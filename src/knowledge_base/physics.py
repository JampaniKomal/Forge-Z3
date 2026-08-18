"""
MulVAL-inspired Physics Logic for Z3.

This module provides the theoretical mapping of how Pydantic CVE models
translate into Datalog rules for the Z3 SMT solver.

The 'Physics' of our Cyber Range are governed by state transitions:
State(Node, Privilege)

Basic rules:
1. Attacker starts with State(AttackerNode, ROOT)
2. Network connectivity allows the attacker to reach a target node's port:
   Reaches(Attacker, Target, Port) :- Connected(Attacker, Target), RunsService(Target, Port).
3. Exploitation transitions state based on the CVE pre/post privileges:
   State(Target, ROOT) :- 
        Reaches(Attacker, Target, Port), 
        RunsCVE(Target, Port, "CVE-2021-44228").
"""

import json
import os

from .schema import CVEDefinition, KnowledgeBase

DB_PATH = os.path.join(os.path.dirname(__file__), "cve_database.json")

def load_knowledge_base(path: str = DB_PATH) -> KnowledgeBase:
    """
    Loads and validates the CVE database from JSON into Pydantic models.
    """
    with open(path) as f:
        data = json.load(f)

    # Validates against the strict Pydantic rules
    return KnowledgeBase(**data)

def get_cve_map() -> dict[str, CVEDefinition]:
    """Returns a dictionary mapping CVE IDs to their Pydantic definitions."""
    kb = load_knowledge_base()
    return {cve.cve_id: cve for cve in kb.cves}

