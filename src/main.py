"""
Forge-Z3: The Neural-Symbolic Cyber Range Compiler
Main CLI Entrypoint
"""

import argparse

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.generator.cegis import CEGISLoop

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()
console = Console()

def main():
    parser = argparse.ArgumentParser(description="Forge-Z3: AI-Driven Cyber Range Compiler")
    parser.add_argument("prompt", type=str, help="The natural language description of the attack path you want.")
    parser.add_argument("--model", type=str, default="gemini/gemini-2.5-pro", help="The LiteLLM model string to use.")
    parser.add_argument("--target", type=int, default=2, help="The Node ID of the final target (default: 2).")

    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold cyan]Forge-Z3 Compiler[/bold cyan]\n"
        "[italic]Neural Generation + Symbolic Verification[/italic]",
        border_style="bright_blue"
    ))
    console.print(f"[bold]Target Model:[/bold] {args.model}")
    console.print(f"[bold]Prompt:[/bold] {args.prompt}\n")

    try:
        loop = CEGISLoop(model_name=args.model)
        valid_topology = loop.synthesize(args.prompt, target_node_id=args.target)

        console.print("\n[bold green]Compilation Successful![/bold green]")

        # Phase 4: IaC Compilation
        from src.compiler.generator import IaCCompiler
        compiler = IaCCompiler(build_dir="build")
        compiler.compile(valid_topology)

        console.print(Panel(
            valid_topology.model_dump_json(indent=2),
            title="Verified JSON Topology",
            border_style="green"
        ))

        # Phase 5: Visualization
        from src.visualization.graph import TopologyVisualizer
        visualizer = TopologyVisualizer(build_dir="build")
        html_path = visualizer.generate_html(valid_topology)

        console.print("[bold yellow]Infrastructure Code Generated in ./build/[/bold yellow]")
        console.print("- Vagrantfile")
        console.print("- site.yml")
        console.print("- inventory.ini")
        console.print(f"- [bold cyan]Interactive Graph:[/bold cyan] {html_path}")

    except Exception as e:
        console.print(f"\n[bold red]Compilation Failed:[/bold red] {str(e)}")

if __name__ == "__main__":
    main()
