import pytest
from src.z3_engine.schema import Topology, Node, Edge, VulnerabilityInstance
from src.z3_engine.engine import Z3Engine

def test_successful_attack_path():
    """
    Test a valid, multi-stage attack path.
    Attacker (0) -> WebServer (1) -> Database (2)
    WebServer has Log4Shell (Network -> Root)
    Database has WEAK_SSH_CREDS (Network -> User) and Dirty COW (User -> Root)
    """
    topology = Topology(
        nodes=[
            Node(node_id=0, name="Attacker"),
            Node(node_id=1, name="WebServer"),
            Node(node_id=2, name="Database")
        ],
        edges=[
            Edge(source_id=0, target_id=1, port=8080), # Attacker can reach WebServer on 8080
            Edge(source_id=1, target_id=2, port=22)    # WebServer can reach Database on 22
        ],
        vulnerabilities=[
            VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228"), # Log4Shell on 8080
            VulnerabilityInstance(node_id=2, cve_id="WEAK_SSH_CREDS"), # Weak SSH on 22
            VulnerabilityInstance(node_id=2, cve_id="CVE-2016-5195")   # Dirty COW (local esc)
        ]
    )
    
    engine = Z3Engine(topology)
    
    # Should be SAT (Attacker can get root on DB)
    assert engine.verify_attack_path(target_node_id=2) is True


def test_failed_attack_path_missing_edge():
    """
    Test an attack path that fails physically.
    Attacker cannot reach the Database because there is no edge from WebServer.
    """
    topology = Topology(
        nodes=[
            Node(node_id=0, name="Attacker"),
            Node(node_id=1, name="WebServer"),
            Node(node_id=2, name="Database")
        ],
        edges=[
            Edge(source_id=0, target_id=1, port=8080),
            # MISSING EDGE: WebServer to Database
        ],
        vulnerabilities=[
            VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228"),
            VulnerabilityInstance(node_id=2, cve_id="WEAK_SSH_CREDS"),
            VulnerabilityInstance(node_id=2, cve_id="CVE-2016-5195")
        ]
    )
    
    engine = Z3Engine(topology)
    
    # Should be UNSAT (Attacker is stuck at WebServer)
    assert engine.verify_attack_path(target_node_id=2) is False


def test_failed_attack_path_missing_privilege():
    """
    Test an attack path that fails logically.
    Attacker reaches Database via SSH, gets USER, but Database lacks a local root exploit.
    """
    topology = Topology(
        nodes=[
            Node(node_id=0, name="Attacker"),
            Node(node_id=1, name="WebServer"),
            Node(node_id=2, name="Database")
        ],
        edges=[
            Edge(source_id=0, target_id=1, port=8080),
            Edge(source_id=1, target_id=2, port=22)
        ],
        vulnerabilities=[
            VulnerabilityInstance(node_id=1, cve_id="CVE-2021-44228"),
            VulnerabilityInstance(node_id=2, cve_id="WEAK_SSH_CREDS"),
            # MISSING LOCAL ESCALATION: Attacker gets USER via SSH, but cannot get ROOT
        ]
    )
    
    engine = Z3Engine(topology)
    
    # Should be UNSAT (Attacker only gets USER, not ROOT)
    assert engine.verify_attack_path(target_node_id=2) is False
