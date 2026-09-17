"""
Tests for Topology's model validators: attacker-node presence, referential
integrity, and unknown-CVE rejection (roadmap Phase C2-C4 / F1-F2).
"""

import pytest
from pydantic import ValidationError

from src.z3_engine.schema import Edge, Node, Topology, VulnerabilityInstance


def test_topology_requires_node_zero():
    """A topology with no Node 0 (the attacker) must be rejected."""
    with pytest.raises(ValidationError, match="Node 0"):
        Topology(
            nodes=[Node(node_id=1, name="WebServer")],
            edges=[],
            vulnerabilities=[],
        )


def test_topology_rejects_edge_to_unknown_node():
    """An edge referencing a node ID that doesn't exist must be rejected."""
    with pytest.raises(ValidationError, match="non-existent target node"):
        Topology(
            nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="WebServer")],
            edges=[Edge(source_id=0, target_id=5, port=80)],
            vulnerabilities=[],
        )


def test_topology_rejects_vulnerability_on_unknown_node():
    """A vulnerability referencing a node ID that doesn't exist must be rejected."""
    with pytest.raises(ValidationError, match="non-existent node"):
        Topology(
            nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="WebServer")],
            edges=[Edge(source_id=0, target_id=1, port=8080)],
            vulnerabilities=[VulnerabilityInstance(node_id=9, cve_id="CVE-2021-44228")],
        )


def test_topology_rejects_unknown_cve():
    """A CVE ID not present in the knowledge base must be rejected."""
    with pytest.raises(ValidationError, match="Unknown CVE ID"):
        Topology(
            nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="WebServer")],
            edges=[Edge(source_id=0, target_id=1, port=8080)],
            vulnerabilities=[VulnerabilityInstance(node_id=1, cve_id="CVE-9999-99999")],
        )


def test_topology_accepts_valid_definition():
    """A well-formed topology with a real CVE ID must be accepted."""
    topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="WebServer")],
        edges=[Edge(source_id=0, target_id=1, port=8080)],
        vulnerabilities=[VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228")],
    )
    assert topology.nodes[0].node_id == 0
