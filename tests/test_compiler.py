import os
import shutil

import pytest

from src.compiler.generator import IaCCompiler
from src.z3_engine.schema import Edge, Node, Topology, VulnerabilityInstance


@pytest.fixture
def temp_build_dir(tmpdir):
    build_dir = os.path.join(str(tmpdir), "build")
    yield build_dir
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)

def test_compiler_generates_files(temp_build_dir):
    topology = Topology(
        nodes=[
            Node(node_id=0, name="Attacker"),
            Node(node_id=1, name="Web Server"),
            Node(node_id=2, name="Database")
        ],
        edges=[
            Edge(source_id=0, target_id=1, port=80),
            Edge(source_id=1, target_id=2, port=3306)
        ],
        vulnerabilities=[
            VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228"),
            VulnerabilityInstance(node_id=2, cve_id="CVE-2016-5195")
        ]
    )

    compiler = IaCCompiler(build_dir=temp_build_dir)
    compiler.compile(topology)

    # Assert files exist
    assert os.path.exists(os.path.join(temp_build_dir, "Vagrantfile"))
    assert os.path.exists(os.path.join(temp_build_dir, "inventory.ini"))
    assert os.path.exists(os.path.join(temp_build_dir, "site.yml"))

    # Assert Vagrantfile contents
    with open(os.path.join(temp_build_dir, "Vagrantfile")) as f:
        vagrant_code = f.read()
        assert "config.vm.define 'web_server'" in vagrant_code
        assert "config.vm.define 'database'" in vagrant_code
        assert "Attacker" not in vagrant_code  # Node 0 is skipped

    # Assert Ansible playbook contents
    with open(os.path.join(temp_build_dir, "site.yml")) as f:
        site_code = f.read()
        assert "hosts: web_server" in site_code
        assert "cve_2021_44228" in site_code
        assert "hosts: database" in site_code
        assert "cve_2016_5195" in site_code
