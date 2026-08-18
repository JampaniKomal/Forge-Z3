
import pytest

from src.generator.cegis import CEGISLoop
from src.z3_engine.schema import Edge, Node, Topology, VulnerabilityInstance


def test_cegis_loop_success(mocker):
    """
    Test that the CEGIS loop correctly breaks and returns the topology
    when Z3 says SAT on the first try.
    """
    # Create a mock valid topology
    valid_topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="Target")],
        edges=[Edge(source_id=0, target_id=1, port=8080)],
        vulnerabilities=[VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228")]
    )

    # Mock the LLM to return the valid topology
    mocker.patch("src.generator.cegis.LLMGenerator.generate_topology", return_value=valid_topology)

    loop = CEGISLoop(model_name="mock-model")
    result = loop.synthesize("test prompt", target_node_id=1)

    assert result == valid_topology

def test_cegis_loop_max_iterations(mocker):
    """
    Test that the CEGIS loop exhaust its iterations if the LLM 
    keeps generating invalid/UNSAT topologies.
    """
    # Create an invalid topology (missing the edge)
    invalid_topology = Topology(
        nodes=[Node(node_id=0, name="Attacker"), Node(node_id=1, name="Target")],
        edges=[],  # MISSING EDGE -> UNSAT
        vulnerabilities=[VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228")]
    )

    mocker.patch("src.generator.cegis.LLMGenerator.generate_topology", return_value=invalid_topology)

    loop = CEGISLoop(model_name="mock-model", max_iterations=2)

    with pytest.raises(RuntimeError, match="CEGIS loop exhausted max iterations"):
        loop.synthesize("test prompt", target_node_id=1)
