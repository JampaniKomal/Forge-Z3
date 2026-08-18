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
