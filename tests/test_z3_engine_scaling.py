"""
Tests for BitVec-sort sizing (soundness) and failure diagnostics.

The Z3 engine encodes node and CVE IDs as unsigned BitVecs. The node sort used
to be a fixed 4 bits, which silently wraps any node_id >= 16 (node 16 aliases to
the attacker at node 0), making verification unsound for larger topologies. The
sort width is now derived from the data; these tests lock that in.
"""

import pytest
from pydantic import ValidationError

from src.z3_engine.engine import Z3Engine
from src.z3_engine.schema import Edge, Node, Topology, VulnerabilityInstance


def test_node_sort_width_scales_with_largest_node_id():
    topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=16, name="Far")],
        edges=[],
        vulnerabilities=[],
    )
    engine = Z3Engine(topology)
    # 16 needs 5 bits; a fixed 4-bit sort could not represent it.
    assert engine.node_bits >= 5


def test_high_node_id_isolated_node_is_unsat():
    """
    Regression for the 4-bit wrap bug. Node 16 is isolated (no edges, no CVEs),
    so the attacker cannot possibly gain ROOT on it. With the old fixed 4-bit
    node sort, BitVecVal(16, 4) == 0, so the query collapsed onto the attacker's
    own ROOT fact and wrongly returned SAT. It must be UNSAT.
    """
    topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=16, name="Isolated")],
        edges=[],
        vulnerabilities=[],
    )
    engine = Z3Engine(topology)
    assert engine.verify_attack_path(target_node_id=16) is False


def test_high_node_id_valid_attack_path_is_sat():
    """A genuine attack path to a node with id > 15 still verifies as SAT."""
    topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=20, name="Server")],
        edges=[Edge(source_id=0, target_id=20, port=8080)],
        vulnerabilities=[VulnerabilityInstance(node_id=20, cve_id="CVE-2021-44228")],
    )
    engine = Z3Engine(topology)
    assert engine.verify_attack_path(target_node_id=20) is True


def test_negative_ids_are_rejected_by_the_schema():
    with pytest.raises(ValidationError):
        Node(node_id=-1, name="Bad")
    with pytest.raises(ValidationError):
        Edge(source_id=0, target_id=-2, port=80)


def test_port_out_of_range_is_rejected_by_the_schema():
    with pytest.raises(ValidationError):
        Edge(source_id=0, target_id=1, port=70000)


def test_port_mismatch_is_unsat_and_diagnosed():
    """
    The CVE needs port 8080 but the only edge delivers traffic on port 22, so no
    attack path exists, and the diagnostic should say exactly that.
    """
    topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="Server")],
        edges=[Edge(source_id=0, target_id=1, port=22)],
        vulnerabilities=[VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228")],
    )
    engine = Z3Engine(topology)
    assert engine.verify_attack_path(target_node_id=1) is False
    diagnostics = engine.diagnose_failure(target_node_id=1)
    assert any("Port mismatch" in d and "8080" in d for d in diagnostics)
