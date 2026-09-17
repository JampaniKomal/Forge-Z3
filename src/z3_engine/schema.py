"""
Schema definitions for the Network Topology.
This represents the output from the LLM (in JSON mode) and serves as the
input to the Z3 Mathematical Engine.
"""


from pydantic import BaseModel, Field, model_validator


class Node(BaseModel):
    """A virtual machine in the cyber range."""

    node_id: int = Field(..., description="Unique ID. Node 0 is ALWAYS the Attacker.")
    name: str = Field(..., description="Human-readable name (e.g., 'WebServer')")


class Edge(BaseModel):
    """A network connection between two nodes."""

    source_id: int = Field(..., description="The ID of the node initiating the connection")
    target_id: int = Field(..., description="The ID of the node receiving the connection")
    port: int = Field(..., description="The destination port (e.g., 80, 443, 22)")


class VulnerabilityInstance(BaseModel):
    """A vulnerability installed on a specific node."""

    node_id: int = Field(..., description="The ID of the vulnerable node")
    cve_id: str = Field(..., description="The exact CVE string from the knowledge base")


class Topology(BaseModel):
    """The complete definition of a Cyber Range environment."""

    nodes: list[Node]
    edges: list[Edge]
    vulnerabilities: list[VulnerabilityInstance]

    @model_validator(mode="after")
    def check_attacker_node(self) -> "Topology":
        """Node 0 must always exist and be the attacker (C4)."""
        if not any(n.node_id == 0 for n in self.nodes):
            raise ValueError("Topology must contain Node 0 (the Attacker).")
        return self

    @model_validator(mode="after")
    def check_referential_integrity(self) -> "Topology":
        """Edges and vulnerabilities must only reference node IDs that exist (C3)."""
        node_ids = {n.node_id for n in self.nodes}
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise ValueError(f"Edge references non-existent source node: {edge.source_id}")
            if edge.target_id not in node_ids:
                raise ValueError(f"Edge references non-existent target node: {edge.target_id}")
        for vuln in self.vulnerabilities:
            if vuln.node_id not in node_ids:
                raise ValueError(f"Vulnerability references non-existent node: {vuln.node_id}")
        return self

    @model_validator(mode="after")
    def check_known_cves(self) -> "Topology":
        """Every vulnerability must reference a CVE that exists in the knowledge base (C2)."""
        # Imported lazily to avoid a hard import-time dependency between the
        # schema module and the knowledge base loader (and the file I/O it does).
        from src.knowledge_base.physics import get_cve_map

        valid_cve_ids = set(get_cve_map().keys())
        for vuln in self.vulnerabilities:
            if vuln.cve_id not in valid_cve_ids:
                raise ValueError(
                    f"Unknown CVE ID: {vuln.cve_id!r}. Valid CVE IDs are: "
                    f"{sorted(valid_cve_ids)}"
                )
        return self
