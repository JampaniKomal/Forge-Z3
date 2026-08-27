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

    def synthesize(self, user_prompt: str, target_node_id: int | None = None) -> Topology:
        """
        Attempts to generate and verify a topology.
        Loops until Z3 returns SAT, or max_iterations is reached.
        If target_node_id is None, auto-detects the highest non-attacker node ID.
        """
        previous_failures = []
        
        # --- TIER 1: Prompt Upgrade ---
        with console.status("[magenta]Tier 1: Upgrading User Prompt...[/magenta]"):
            upgraded_prompt = self.generator.upgrade_prompt(user_prompt)
            
        console.print("\n[bold magenta]=== TIER 1: ARCHITECTURAL PLAN ===[/bold magenta]")
        console.print(f"[magenta]{upgraded_prompt}[/magenta]")
        console.print("[bold magenta]=====================================[/bold magenta]\n")

        for iteration in range(1, self.max_iterations + 1):
            console.print(f"\n[bold cyan]CEGIS Iteration {iteration}/{self.max_iterations}[/bold cyan]")

            try:
                # Step 1: SYNTHESIS (Neural - Tier 2)
                with console.status("[yellow]LLM generating topology (Tier 2)...[/yellow]"):
                    topology = self.generator.generate_topology(upgraded_prompt, previous_failures)
                console.print("  [green][OK] LLM generated a schema-compliant topology.[/green]")

                # Auto-detect target node if not specified
                effective_target = target_node_id
                if effective_target is None:
                    non_attacker_ids = [n.node_id for n in topology.nodes if n.node_id != 0]
                    if not non_attacker_ids:
                        raise ValueError("Topology has no non-attacker nodes to target.")
                    effective_target = max(non_attacker_ids)
                    console.print(f"  [dim]Auto-detected target: Node {effective_target}[/dim]")

                # Step 2: VERIFICATION (Symbolic)
                with console.status("[blue]Z3 verifying attack path physics...[/blue]"):
                    engine = Z3Engine(topology)
                    is_sat = engine.verify_attack_path(effective_target)

                if is_sat:
                    console.print("  [bold green][OK] Z3 VERIFIED (SAT): The attack path is mathematically valid![/bold green]")
                    return topology
                else:
                    # Generate specific failure diagnostics
                    diagnostics = engine.diagnose_failure(effective_target)
                    diagnostic_str = "\n".join(f"  • {d}" for d in diagnostics)

                    console.print("  [bold red][FAIL] Z3 FAILED (UNSAT): The attack path is broken.[/bold red]")
                    console.print(f"  [yellow]Diagnostics:[/yellow]")
                    for d in diagnostics:
                        console.print(f"    [yellow]• {d}[/yellow]")
                    console.print(f"\n--- RAW JSON TOPOLOGY ---\n{topology.model_dump_json(indent=2)}\n-------------------------\n")

                    # Send specific feedback to the LLM (not generic)
                    failure_msg = (
                        f"Your previous topology FAILED Z3 verification.\n"
                        f"Failed topology JSON:\n{topology.model_dump_json(indent=2)}\n\n"
                        f"Specific failure reasons:\n{diagnostic_str}\n\n"
                        f"Fix these exact issues in your next attempt."
                    )
                    previous_failures.append(failure_msg)

            except Exception as e:
                console.print(f"  [bold red][FAIL] LLM Generation Error:[/bold red] {str(e)}")
                previous_failures.append(str(e))

        raise RuntimeError("CEGIS loop exhausted max iterations without finding a valid topology.")
