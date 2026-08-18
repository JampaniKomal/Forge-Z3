"""
Schema definitions for the Network Topology.
This represents the output from the LLM (in JSON mode) and serves as the
input to the Z3 Mathematical Engine.
"""

from typing import List
from pydantic import BaseModel, Field

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
    nodes: List[Node]
    edges: List[Edge]
    vulnerabilities: List[VulnerabilityInstance]
