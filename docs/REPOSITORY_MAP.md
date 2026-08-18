# Forge-Z3 Repository Map

This document provides a comprehensive, file-by-file explanation of the Forge-Z3 compiler repository.

## Root Directory
- `README.md`: The primary documentation and entry point for the project.
- `requirements.txt`: Lists all Python dependencies required to run the engine (e.g., `z3-solver`, `litellm`, `pydantic`).
- `pyproject.toml`: The configuration file for Python tooling, ensuring tests run smoothly.
- `CODE_OF_CONDUCT.md`: Industry-standard community rules for open-source contributors.
- `.env.example`: A template showing users where to put their API keys (Gemini, Groq).

---

## `/src` (Core Engine)
This is where the entire compiler pipeline lives.

### `src/main.py`
The CLI entry point. This script takes the user's terminal arguments (the prompt and the `--model` flag) and orchestrates the pipeline: Generator -> Verifier -> Compiler.

### `src/generator/` (The AI Layer)
- `llm_client.py`: The universal API wrapper using `litellm`. This allows the engine to route requests to Google Gemini, Groq (Llama 3), Hugging Face, or local Ollama instances seamlessly.
- `cegis.py`: The Counterexample-Guided Inductive Synthesis loop. This script catches `UNSAT` errors from the Z3 engine and forces the LLM to rewrite the JSON topology until it is mathematically proven.
- `schema.py`: Defines the strict `Pydantic` JSON schemas (Nodes, Edges, Vulnerabilities) that the LLM is forced to output.

### `src/z3_engine/` (The Math Layer)
- `verifier.py`: The core mathematical engine. It takes the LLM's JSON and translates it into Datalog predicates. It then asks the Z3 SMT Solver if the attack path is logically possible based on the physics of the network.

### `src/knowledge_base/` (The Rules Engine)
- `physics.py`: Contains the hardcoded Datalog rules of networking and CVEs. For example, it tells Z3 that "to exploit Log4Shell, the attacker must have network reachability to port 8080."

### `src/compiler/` (The Infrastructure Layer)
- `generator.py`: Once Z3 approves the JSON, this script translates the graph into raw infrastructure-as-code (Vagrant and Ansible).

### `src/visualization/` (The UI Layer)
- `graph.py`: Uses `pyvis` to consume the verified JSON and generate an interactive 3D HTML dashboard.

---

## `/ansible` (The Physical Provisioning)
This directory contains the actual DevOps configuration scripts.
- `roles/`: Contains Ansible roles for specific vulnerabilities (e.g., `log4shell`, `proftpd`). 
- **What it does:** When the compiler generates a `Vagrantfile`, Vagrant uses these Ansible scripts to physically install the vulnerable software onto the Virtual Machines, making the cyber range actually functional for red-team exercises.

---

## `/tests` (Quality Assurance)
Contains the automated `pytest` suite. Every time code is pushed, these tests run to ensure the Z3 math engine and LLM parsers are mathematically flawless.
