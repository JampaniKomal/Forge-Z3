import os
import shutil
import pytest
from src.z3_engine.schema import Topology, Node, Edge, VulnerabilityInstance
from src.visualization.graph import TopologyVisualizer

@pytest.fixture
def temp_build_dir(tmpdir):
    build_dir = os.path.join(str(tmpdir), "build")
    yield build_dir
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

def test_visualizer_generates_html(temp_build_dir):
    topology = Topology(
        nodes=[
            Node(node_id=0, name="Attacker"),
            Node(node_id=1, name="Web Server"),
        ],
        edges=[
            Edge(source_id=0, target_id=1, port=80),
        ],
        vulnerabilities=[
            VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228"),
        ]
    )
    
    visualizer = TopologyVisualizer(build_dir=temp_build_dir)
    html_path = visualizer.generate_html(topology, filename="test_topo.html")
    
    assert os.path.exists(html_path)
    
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()
        assert "Web Server" in content
        assert "Attacker" in content
        # Check if the CVE metadata made it in
        assert "CVE-2021-44228" in content
