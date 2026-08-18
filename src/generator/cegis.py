"""
Counter-Example Guided Inductive Synthesis (CEGIS) Loop.

This is the core execution loop that pits the Neural Generator (LLM) against
the Symbolic Verifier (Z3). It forces the LLM to self-correct until it writes
a mathematically sound attack path.
"""

from rich.console import Console

from src.generator.llm_client import LLMGenerator
from src.z3_engine.engine import Z3Engine
from src.z3_engine.schema import Topology

console = Console()

class CEGISLoop:
    def __init__(self, model_name: str = "gemini/gemini-2.5-pro", max_iterations: int = 5):
        self.generator = LLMGenerator(model_name)
        self.max_iterations = max_iterations

    def synthesize(self, user_prompt: str, target_node_id: int) -> Topology:
        """
        Attempts to generate and verify a topology.
        Loops until Z3 returns SAT, or max_iterations is reached.
        """
        previous_failures = []

        for iteration in range(1, self.max_iterations + 1):
            console.print(f"\n[bold cyan]CEGIS Iteration {iteration}/{self.max_iterations}[/bold cyan]")

            try:
                # 1. SYNTHESIS (Neural)
                with console.status("[yellow]LLM generating topology...[/yellow]"):
                    topology = self.generator.generate_topology(user_prompt, previous_failures)
                console.print("  [green][OK] LLM generated a schema-compliant topology.[/green]")

                # 2. VERIFICATION (Symbolic)
                with console.status("[blue]Z3 verifying attack path physics...[/blue]"):
                    engine = Z3Engine(topology)
                    is_sat = engine.verify_attack_path(target_node_id)

                if is_sat:
                    console.print("  [bold green][OK] Z3 VERIFIED (SAT): The attack path is mathematically valid![/bold green]")
                    return topology
                else:
                    console.print("  [bold red][FAIL] Z3 FAILED (UNSAT): The attack path is broken.[/bold red]")
                    failure_msg = (
                        "Z3 SMT Solver returned UNSAT. The attacker cannot reach the target "
                        "or lacks required privileges to execute the CVEs. Please double-check "
                        "your NetworkEdges and pre_privileges."
                    )
                    previous_failures.append(failure_msg)

            except Exception as e:
                console.print(f"  [bold red][FAIL] LLM Generation Error:[/bold red] {str(e)}")
                previous_failures.append(str(e))

        raise RuntimeError("CEGIS loop exhausted max iterations without finding a valid topology.")
