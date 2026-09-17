"""
The Core Z3 Mathematical Engine.

This takes a Network Topology and the CVE Knowledge Base, translates them into
Datalog rules, and formally verifies if an attack path exists.
"""

import z3

from src.knowledge_base.physics import get_cve_map
from src.knowledge_base.schema import PrivilegeLevel
from src.z3_engine.schema import Topology

# Map privileges to integers for Z3 BitVec
PRIVILEGE_MAP = {
    PrivilegeLevel.NONE: 0,
    PrivilegeLevel.NETWORK_ACCESS: 1,
    PrivilegeLevel.USER: 2,
    PrivilegeLevel.ROOT: 3
}

class Z3Engine:
    def __init__(self, topology: Topology):
        self.topology = topology
        self.cve_map = get_cve_map()

        self.fp = z3.Fixedpoint()
        self.fp.set("engine", "datalog")

        # Sorts (Types)
        self.NodeSort = z3.BitVecSort(4)  # 4 bits = up to 16 nodes
        self.PrivSort = z3.BitVecSort(3)  # 3 bits = up to 8 privilege levels
        self.PortSort = z3.BitVecSort(16) # 16 bits = up to 65535 ports
        self.CveSort = z3.BitVecSort(8)   # 8 bits = up to 256 CVEs

        # Predicates (Relations)
        self.NetworkEdge = z3.Function(
            "NetworkEdge", self.NodeSort, self.NodeSort,
            self.PortSort, z3.BoolSort(),
        )
        self.RunsCVE = z3.Function(
            "RunsCVE", self.NodeSort, self.CveSort, z3.BoolSort(),
        )
        self.Reaches = z3.Function(
            "Reaches", self.NodeSort, self.NodeSort,
            self.PortSort, z3.BoolSort(),
        )
        self.State = z3.Function("State", self.NodeSort, self.PrivSort, z3.BoolSort())

        self.fp.register_relation(self.NetworkEdge)
        self.fp.register_relation(self.RunsCVE)
        self.fp.register_relation(self.Reaches)
        self.fp.register_relation(self.State)

        # Internal mapping of CVE string IDs to integers
        self._cve_id_to_int = {cve_id: i+1 for i, cve_id in enumerate(self.cve_map.keys())}

    def _build_rules(self):
        """Translate the physics of hacking into Datalog rules."""
        n1 = z3.Var(0, self.NodeSort)
        n2 = z3.Var(1, self.NodeSort)
        port = z3.Var(2, self.PortSort)

        # Rule 1: Reachability
        # Attacker can reach Node 2 if they have USER or ROOT
        # on Node 1, and there is a physical edge.
        val_root = z3.BitVecVal(PRIVILEGE_MAP[PrivilegeLevel.ROOT], 3)
        val_user = z3.BitVecVal(PRIVILEGE_MAP[PrivilegeLevel.USER], 3)

        self.fp.rule(
            self.Reaches(n1, n2, port),
            [self.State(n1, val_root), self.NetworkEdge(n1, n2, port)],
        )
        self.fp.rule(
            self.Reaches(n1, n2, port),
            [self.State(n1, val_user), self.NetworkEdge(n1, n2, port)],
        )

        # Rule 2: CVE Exploitation
        # Dynamically generate rules based on the CVE database.
        for cve_id, cve_def in self.cve_map.items():
            cve_int = self._cve_id_to_int[cve_id]
            pre_val = PRIVILEGE_MAP[cve_def.pre_privilege]
            post_val = PRIVILEGE_MAP[cve_def.post_privilege]
            target_port = cve_def.port

            if cve_def.pre_privilege == PrivilegeLevel.NETWORK_ACCESS:
                # RCE: Reaches(n1, n2, port) + RunsCVE(n2) -> State(n2, post)
                self.fp.rule(
                    self.State(n2, z3.BitVecVal(post_val, 3)),
                    [
                        self.Reaches(n1, n2, z3.BitVecVal(target_port, 16)),
                        self.RunsCVE(n2, z3.BitVecVal(cve_int, 8))
                    ]
                )
            else:
                # Local Esc: State(n2, pre) + RunsCVE(n2) -> State(n2, post)
                self.fp.rule(
                    self.State(n2, z3.BitVecVal(post_val, 3)),
                    [
                        self.State(n2, z3.BitVecVal(pre_val, 3)),
                        self.RunsCVE(n2, z3.BitVecVal(cve_int, 8))
                    ]
                )

        # Rule 3: Privilege Inheritance
        # Having ROOT implies having USER.
        self.fp.rule(self.State(n1, val_user), [self.State(n1, val_root)])

    def _assert_facts(self):
        """Assert the physical reality of the topology."""
        # The attacker is always Node 0 with ROOT on their own machine
        attacker_node = z3.BitVecVal(0, 4)
        root_priv = z3.BitVecVal(PRIVILEGE_MAP[PrivilegeLevel.ROOT], 3)
        self.fp.fact(self.State(attacker_node, root_priv))

        # Edges
        for edge in self.topology.edges:
            self.fp.fact(self.NetworkEdge(
                z3.BitVecVal(edge.source_id, 4),
                z3.BitVecVal(edge.target_id, 4),
                z3.BitVecVal(edge.port, 16)
            ))

        # Vulnerabilities
        for vuln in self.topology.vulnerabilities:
            if vuln.cve_id in self._cve_id_to_int:
                cve_int = self._cve_id_to_int[vuln.cve_id]
                self.fp.fact(self.RunsCVE(
                    z3.BitVecVal(vuln.node_id, 4),
                    z3.BitVecVal(cve_int, 8)
                ))

    def verify_attack_path(self, target_node_id: int) -> bool:
        """
        Runs the CEGIS/Datalog proof.
        Returns True if the attacker can achieve ROOT on the target_node_id.
        """
        self._build_rules()
        self._assert_facts()

        q = self.fp.query(self.State(
            z3.BitVecVal(target_node_id, 4),
            z3.BitVecVal(PRIVILEGE_MAP[PrivilegeLevel.ROOT], 3)
        ))

        return q == z3.sat

    def diagnose_failure(self, target_node_id: int) -> list[str]:
        """
        Analyse a failed topology WITHOUT Z3 and produce specific, actionable
        error messages explaining exactly why the attack path is broken.

        Returns a list of diagnostic strings.
        """
        diagnostics = []
        topology = self.topology

        # Build helper lookups
        node_ids = {n.node_id for n in topology.nodes}
        # incoming_edges[node_id] = list of (source_id, port)
        incoming_edges: dict[int, list[tuple[int, int]]] = {nid: [] for nid in node_ids}
        # outgoing_edges[node_id] = list of (target_id, port)
        outgoing_edges: dict[int, list[tuple[int, int]]] = {nid: [] for nid in node_ids}
        for edge in topology.edges:
            if edge.target_id in incoming_edges:
                incoming_edges[edge.target_id].append((edge.source_id, edge.port))
            if edge.source_id in outgoing_edges:
                outgoing_edges[edge.source_id].append((edge.target_id, edge.port))

        # vulns_on_node[node_id] = list of cve_id strings
        vulns_on_node: dict[int, list[str]] = {nid: [] for nid in node_ids}
        for vuln in topology.vulnerabilities:
            if vuln.node_id in vulns_on_node:
                vulns_on_node[vuln.node_id].append(vuln.cve_id)

        # --- Check 1: Target node exists ---
        if target_node_id not in node_ids:
            diagnostics.append(
                f"Target node {target_node_id} does not exist in the topology. "
                f"Available node IDs: {sorted(node_ids)}."
            )
            return diagnostics

        # --- Check 2: No edge connects to the target ---
        if not incoming_edges[target_node_id]:
            diagnostics.append(
                f"No edge connects TO Node {target_node_id}. "
                f"Add an edge from a compromised node to Node {target_node_id}."
            )

        # --- Check 3: Port mismatch between edges and CVEs ---
        for node_id in node_ids:
            if node_id == 0:
                continue  # Attacker node — no CVEs to check
            for cve_id in vulns_on_node[node_id]:
                if cve_id not in self.cve_map:
                    diagnostics.append(
                        f"Node {node_id} references unknown CVE '{cve_id}'. "
                        f"It will be silently ignored. Use a valid CVE ID from the knowledge base."
                    )
                    continue

                cve_def = self.cve_map[cve_id]

                # Only check port for network-based exploits (not local PrivEsc)
                if cve_def.pre_privilege == PrivilegeLevel.NETWORK_ACCESS:
                    required_port = cve_def.port
                    incoming_ports = [port for _, port in incoming_edges[node_id]]

                    if required_port not in incoming_ports:
                        if incoming_ports:
                            diagnostics.append(
                                f"Port mismatch on Node {node_id}: {cve_id} requires port "
                                f"{required_port}, but incoming edges use port(s) "
                                f"{incoming_ports}. Change the edge port to {required_port}."
                            )
                        else:
                            diagnostics.append(
                                f"Node {node_id} has {cve_id} (requires port {required_port}), "
                                f"but no incoming edges exist to deliver network traffic."
                            )

        # --- Check 4: Missing privilege chain to ROOT ---
        for node_id in node_ids:
            if node_id == 0:
                continue
            cve_ids_on_node = vulns_on_node[node_id]
            if not cve_ids_on_node:
                continue

            # What's the highest privilege achievable on this node?
            max_post = PrivilegeLevel.NONE
            has_local_privesc = False

            for cve_id in cve_ids_on_node:
                if cve_id not in self.cve_map:
                    continue
                cve_def = self.cve_map[cve_id]
                # Track if there's a local escalation CVE
                if cve_def.pre_privilege == PrivilegeLevel.USER:
                    has_local_privesc = True
                if cve_def.post_privilege == PrivilegeLevel.ROOT:
                    max_post = PrivilegeLevel.ROOT
                elif (
                    cve_def.post_privilege == PrivilegeLevel.USER
                    and max_post != PrivilegeLevel.ROOT
                ):
                    max_post = PrivilegeLevel.USER

            # If the node is the target and max achievable is only USER, warn
            is_target_capped_at_user = (
                node_id == target_node_id
                and max_post == PrivilegeLevel.USER
                and not has_local_privesc
            )
            if is_target_capped_at_user:
                diagnostics.append(
                    f"Node {node_id} (target) can only reach USER privilege via its CVEs "
                    f"({cve_ids_on_node}), but ROOT is required. Add a local privilege "
                    f"escalation CVE (e.g., CVE-2021-3156, CVE-2021-4034, or CVE-2016-5195)."
                )

        # --- Check 5: Unreachable intermediate nodes ---
        # For multi-hop: intermediate nodes need both incoming AND outgoing edges
        for node_id in node_ids:
            if node_id == 0 or node_id == target_node_id:
                continue
            has_incoming = bool(incoming_edges[node_id])
            has_outgoing = bool(outgoing_edges[node_id])

            if has_incoming and not has_outgoing:
                diagnostics.append(
                    f"Node {node_id} is a dead-end: it has incoming edges but no outgoing "
                    f"edges. If it's an intermediate hop, add an edge from Node {node_id} "
                    f"to the next node in the attack chain."
                )
            elif not has_incoming and has_outgoing and node_id != 0:
                diagnostics.append(
                    f"Node {node_id} has outgoing edges but no incoming edges. "
                    f"The attacker cannot reach it."
                )

        # --- Check 6: No vulnerabilities at all on a node that needs them ---
        for node_id in node_ids:
            if node_id == 0:
                continue
            if incoming_edges[node_id] and not vulns_on_node[node_id]:
                diagnostics.append(
                    f"Node {node_id} has incoming edges but no vulnerabilities assigned. "
                    f"Without a CVE, the attacker cannot compromise this node even if "
                    f"they can reach it."
                )

        if not diagnostics:
            diagnostics.append(
                "No obvious structural issue detected. The attack chain may have "
                "a subtle logical gap in privilege transitions."
            )

        return diagnostics

