"""
Forge-Z3: Z3 Hello World -- Phase 0 Verification Script

This script verifies that the Z3 SMT solver is correctly installed
and can solve a basic network reachability problem using Datalog-style
Fixedpoint reasoning.

The problem modeled here is a simplified version of what Forge-Z3
will do at scale:
  - 3 nodes: Attacker(1), WebServer(2), Database(3)
  - 2 edges: Attacker->WebServer, WebServer->Database
  - Query: Can the Attacker reach the Database?

Expected output: Z3 returns SAT (reachable).

IMPORTANT Z3 Datalog Note:
  - Use z3.Var(index, sort) for BOUND variables in rules (not z3.BitVec).
  - Use z3.BitVecVal(value, bits) for CONCRETE node constants in facts.
  - The Fixedpoint engine requires BitVecSort, not DeclareSort.
"""

import z3


def _create_datalog_engine():
    """Create and configure a Z3 Fixedpoint engine with network predicates.

    Returns:
        Tuple of (fp, Edge, Reachable, NodeSort)
    """
    fp = z3.Fixedpoint()
    fp.set("engine", "datalog")

    # BitVecSort(3) = 3-bit integers, supports up to 8 distinct nodes
    node_sort = z3.BitVecSort(3)

    # Define relations (predicates)
    edge = z3.Function("Edge", node_sort, node_sort, z3.BoolSort())
    reachable = z3.Function("Reachable", node_sort, node_sort, z3.BoolSort())

    fp.register_relation(edge)
    fp.register_relation(reachable)

    # Bound variables for Datalog rules (NOT free constants)
    x = z3.Var(0, node_sort)
    y = z3.Var(1, node_sort)
    z_var = z3.Var(2, node_sort)

    # Rule 1: Direct edge implies reachability
    fp.rule(reachable(x, y), edge(x, y))

    # Rule 2: Transitive closure (if A reaches B, and B->C exists, then A reaches C)
    fp.rule(reachable(x, z_var), [reachable(x, y), edge(y, z_var)])

    return fp, edge, reachable, node_sort


def run_z3_hello_world() -> bool:
    """
    Demonstrates Z3 Fixedpoint (Datalog) solving a simple
    network reachability problem.

    Returns:
        True if Z3 correctly determines the path is reachable (SAT).
    """
    fp, edge, reachable, node_sort = _create_datalog_engine()

    # Concrete node IDs
    attacker = z3.BitVecVal(1, 3)
    webserver = z3.BitVecVal(2, 3)
    database = z3.BitVecVal(3, 3)

    # Add edges: Attacker -> WebServer -> Database
    fp.fact(edge(attacker, webserver))
    fp.fact(edge(webserver, database))

    # Query: Can Attacker reach Database?
    query_result = fp.query(reachable(attacker, database))

    return query_result == z3.sat


def run_z3_unsat_demo() -> bool:
    """
    Demonstrates Z3 correctly identifying an UNREACHABLE path.
    Same network but with NO edge from WebServer to Database.

    Returns:
        True if Z3 correctly determines the path is unreachable (UNSAT).
    """
    fp, edge, reachable, node_sort = _create_datalog_engine()

    attacker = z3.BitVecVal(1, 3)
    webserver = z3.BitVecVal(2, 3)
    database = z3.BitVecVal(3, 3)

    # Only ONE edge: Attacker -> WebServer (no path to Database)
    fp.fact(edge(attacker, webserver))

    query_result = fp.query(reachable(attacker, database))

    return query_result == z3.unsat


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print(Panel.fit(
        "[bold cyan]Forge-Z3 -- Phase 0: Z3 SMT Solver Verification[/bold cyan]",
        border_style="bright_blue"
    ))

    # Test 1: Reachable path
    console.print("\n[bold]Test 1:[/bold] Attacker -> WebServer -> Database")
    sat_result = run_z3_hello_world()
    if sat_result:
        console.print("  [bold green]>> Z3 says: SAT (Attack path is REACHABLE)[/bold green]")
    else:
        console.print("  [bold red]>> Z3 says: UNSAT (UNEXPECTED -- something is wrong)[/bold red]")

    # Test 2: Unreachable path
    console.print("\n[bold]Test 2:[/bold] Attacker -> WebServer  X  Database (no edge)")
    unsat_result = run_z3_unsat_demo()
    if unsat_result:
        console.print("  [bold green]>> Z3 says: UNSAT (Attack path is BLOCKED -- correct!)[/bold green]")
    else:
        console.print("  [bold red]>> Z3 says: SAT (UNEXPECTED -- something is wrong)[/bold red]")

    # Summary
    console.print()
    if sat_result and unsat_result:
        console.print(Panel.fit(
            "[bold green]All tests passed. Z3 is working correctly.[/bold green]\n"
            "The Fixedpoint/Datalog engine can reason about network reachability.",
            title="Phase 0 Complete",
            border_style="green"
        ))
    else:
        console.print(Panel.fit(
            "[bold red]Some tests failed. Check your z3-solver installation.[/bold red]",
            title="Phase 0 FAILED",
            border_style="red"
        ))
