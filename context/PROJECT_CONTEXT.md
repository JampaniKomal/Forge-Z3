# PROJECT CONTEXT & HANDOFF
*This document contains the complete context of the Forge-Z3 project for seamless AI handoffs.*

## 1. Identity & Goals
- **User:** Jampani Komal, 7th-semester student at RRU (Rashtriya Raksha University).
- **Professor:** Dr. Ravi Sheth.
- **Project Goal:** Build a genuinely useful, open-source, neuro-symbolic cyber range compiler. No mockups, no clones. Strictly follow secure coding standards.

## 2. Hardware Constraints
- **Environment:** Intel i3 processor, 20GB RAM, Windows. 
- **Impact:** We cannot run heavy local LLMs, and we shouldn't boot heavy Vagrant VMs locally during dev. We rely on API-based LLMs (Gemini/Groq) and we *generate* IaC code instead of executing it.

## 3. Technology Stack
- **Core:** Python 3.12, `pytest`
- **Neural Layer:** `litellm` (LLM abstraction for Gemini/Groq/OpenAI), `pydantic` (JSON structured schema).
- **Symbolic Layer:** `z3-solver` (Microsoft's SMT solver using the Fixedpoint/Datalog engine).
- **Visualization:** `networkx`, `pyvis`
- **DevOps Output:** Vagrant, Ansible
- **Quality Assurance:** `bandit` (security), `ruff` (linting).

## 4. The 3-Layer Architecture
1. **Knowledge Base / Schema (`src/knowledge_base/`):** Defines the "physics" of the cyber range. It restricts the universe to 12 carefully selected CVEs (e.g., Log4Shell, Dirty COW) mapped in `cve_database.json`.
2. **The Z3 Engine (`src/z3_engine/`):** The mathematical core. It translates the CVEs and JSON Topology into Datalog rules. It proves whether an attacker (Node 0) can reach the target node and acquire ROOT privileges.
3. **The Generator & Compiler (`src/generator/`, `src/compiler/`):** The LLM hallucination mitigator. It uses a CEGIS (Counter-Example Guided Inductive Synthesis) loop to force the LLM to generate Topologies until Z3 returns `SAT`. Then, the compiler outputs a `Vagrantfile`, `site.yml`, and `topology.html` into the `build/` directory.

## 5. File Structure
- `src/`: Application source code.
  - `knowledge_base/`: Pydantic models and CVE JSON rules.
  - `z3_engine/`: The Z3 Fixedpoint solver logic.
  - `generator/`: The LLM client and CEGIS loop.
  - `compiler/`: Translates topology into Vagrant/Ansible code.
  - `visualization/`: PyVis 3D HTML mapping.
  - `main.py`: The Rich CLI entrypoint.
- `tests/`: 100% coverage unit tests.
- `ansible/`: Scaffolded roles for deploying CVEs.
- `devlog/`: Chronological log of all phases.

## 6. Current State
As of the current timestamp, **Phase 1 through Phase 5 are 100% complete and tested.**
The system is fully operational. Running `python src/main.py "prompt"` will successfully loop between LiteLLM and Z3 until a valid topology is generated, at which point it outputs the physical infrastructure code into the `build/` folder.
