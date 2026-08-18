"""
Tests for the Z3 hello world verification script.
"""
from src.z3_hello_world import run_z3_hello_world, run_z3_unsat_demo


def test_z3_reachable_path():
    """Z3 should return SAT when a valid path exists."""
    assert run_z3_hello_world() is True


def test_z3_unreachable_path():
    """Z3 should return UNSAT when no valid path exists."""
    assert run_z3_unsat_demo() is True
