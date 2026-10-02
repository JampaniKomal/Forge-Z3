<div align="center">
  <h1>Forge-Z3: Neuro-Symbolic Cyber Range Compiler</h1>
  <p><b>Bridging Large Language Models with Formal Mathematical Verification</b></p>
</div>

## Overview
Forge-Z3 is a state-of-the-art Infrastructure Compiler that utilizes **Neuro-Symbolic AI** to automatically generate, verify, and deploy vulnerable cyber ranges for defensive training and red-teaming exercises.

Instead of relying purely on the probabilistic output of Large Language Models (which frequently hallucinate physically impossible network topologies), Forge-Z3 utilizes **Counterexample-Guided Inductive Synthesis (CEGIS)**:

1. **Neural Generation:** Uses LiteLLM (Gemini, Groq, Ollama) and constrained decoding (Pydantic) to generate a JSON network graph based on a natural language prompt.
2. **Symbolic Translation:** The JSON graph is compiled into formal Datalog predicates.
3. **Self-Healing Loop:** If Z3 detects a structural hallucination (`UNSAT`), it automatically extracts the failure reason and prompts the LLM to self-correct.
4. **Compilation:** Once mathematically proven, the engine compiles the network into a `Vagrantfile` and matching Ansible playbook. Note: this generates the deployment *skeleton* with correct role names and networking — most CVE roles are currently placeholder stubs rather than real vulnerable-service provisioning; see Known Limitations below.

*Built by Jampani Komal at Rashtriya Raksha University (RRU).*

---

## Example Prompts & Testing
For a curated list of Easy, Medium, and Hard prompts to test the Z3 engine, see the [Example Prompts Guide](docs/PROMPTS.md).

---

## Deep Dive & Academic References
For a complete technical breakdown of the compiler's Datalog layers and CEGIS feedback loop, read the [Architecture Deep Dive](docs/ARCHITECTURE.md).

For a complete breakdown of every file and folder in this repository, see the [Repository Map](docs/REPOSITORY_MAP.md).

This project adapts state-of-the-art research in automated security modeling and neuro-symbolic verification:
1. **Automated Vulnerability Modeling:** Adapts the Datalog approach from *"A scalable approach to attack graph generation (MulVAL)"* (Ou, Boyer, McQueen).
2. **Neuro-Symbolic Agentic Oversight:** Inspired by *"FormalJudge: A Neuro-Symbolic Paradigm for Agentic Oversight"* (ICML 2026), replacing standard LLM evaluation with deterministic Dafny/Z3 verification.
3. **Formal Proof Verification:** Implements self-correction paradigms analogous to *"ProofNet++: A Neuro-Symbolic System for Formal Proof Verification"*.

---

## Visualization Dashboard
Forge-Z3 operates primarily as a CLI Compiler with rich terminal output. 

Upon successful compilation, it automatically generates a 3D Interactive Visual Dashboard located at `build/topology.html`. Opening this file in any modern web browser provides a fully interactive 3D map of the generated network, allowing for visual inspection of nodes, IP addresses, vulnerabilities, and exact attack paths.

---

## Execution Modes
Forge-Z3 uses the `litellm` framework, making it completely model-agnostic. The AI engine can be hot-swapped depending on local hardware availability and API limits.

### 1. Google Gemini (Default - Free Tier)
The most reliable cloud-based option. Ensure the `GEMINI_API_KEY` environment variable is set in the `.env` file.
```bash
python -m src.main "Build me a 3-node network where I pivot through a WebServer to hack a Database." --model gemini/gemini-flash-latest
```

### 2. Groq (High-Speed Inference)
Provides the fastest generation speed utilizing Meta's Llama 3 models. Ensure the `GROQ_API_KEY` is set in the `.env` file.
```bash
python -m src.main "Build me a 3-node network..." --model groq/llama-3.3-70b-versatile
```

### 3. Local Ollama (Offline Execution)
Run the engine entirely on local hardware without an internet connection. Ensure the Ollama daemon is running.
```bash
python -m src.main "Build me a 3-node network..." --model ollama/llama3
```

---

## Tested Configurations & Known Limitations

This section is updated from actual runs, not aspirations.

**What is verified to work end-to-end today:**
- The full pipeline (Tier 1 plan -> Tier 2 JSON -> Z3 verification -> CEGIS
  self-correction on failure -> Vagrantfile/Ansible/topology.html generation)
  has been run live against a local Ollama model (`qwen2.5-coder:3b`) and
  succeeded on the second CEGIS iteration: the first attempt used the wrong
  port for CVE-2021-44228, Z3 caught it and told the model exactly what was
  wrong, and the model corrected it on retry.
- The 22-test unit suite (`pytest tests/`) passes, including the Z3 SAT/UNSAT
  logic, BitVec-sort sizing/soundness, failure diagnostics, the CEGIS loop
  (mocked LLM), the compiler, and the visualizer.
- `ruff` and `bandit` both report zero issues; `pip-audit` reports no known
  vulnerabilities in the pinned dependencies. CI runs ruff + pytest on
  Python 3.10, 3.11 and 3.12.

**Correctness fix (latest pass):**
- The Z3 node/CVE BitVec sorts were a fixed width (4-bit nodes), which silently
  wrapped any `node_id >= 16` — node 16 aliased to the attacker at node 0, so a
  query about an unreachable high-id node could collapse onto the attacker's own
  ROOT fact and wrongly return SAT. The sort widths are now derived from the
  topology, the topology schema rejects negative IDs and out-of-range ports, and
  both cases are covered by regression tests (`tests/test_z3_engine_scaling.py`).

**What is known to be inconsistent:**
- Local model reliability varies by model and prompt, not just parameter
  count. A documented session with `ollama/llama3:8b` failed all 5 CEGIS
  iterations on a 3-node scenario (it kept losing track of port/CVE/privilege
  constraints simultaneously — see `docs/IMPLEMENTATION_LOG.md` section 6-7),
  while a smaller `qwen2.5-coder:3b` model succeeded on a simpler 2-node
  scenario on the second attempt. Treat cloud models (Gemini, Groq) as the
  reliable path today; local models are genuinely hit-or-miss until the
  planned Tier 3 deterministic auto-repair layer (see `ROADMAP.md`) exists to
  take mechanical constraint-matching off the LLM's plate.

**What is not yet real, stated plainly:**
- The generated Ansible roles are almost all placeholder stubs. Only
  `ansible/roles/cve_2021_44228/` exists, and its task is a `debug` message,
  not a real Log4j deployment. The remaining 11 CVEs in the knowledge base
  have no role directory at all yet — a topology using them would generate a
  `site.yml` that references a role Ansible cannot find.
- `vagrant up` against the generated output has not been run in this
  environment (no VirtualBox/Vagrant installed here). The Vagrantfile and
  Ansible inventory have been checked for valid syntax and correct
  hostnames/IPs/role-name references, but actually booting the VMs is
  untested.
- The `docs/PROMPTS.md` example prompts are not all individually verified
  against a live model run; treat them as example inputs to try, not as a
  guarantee of a specific outcome.

---

## Project Architecture
```text
Forge-Z3/
├── src/
│   ├── knowledge_base/   # CVE rules (Log4Shell, ProFTPd, MySQL, etc.)
│   ├── generator/        # Neural perception (LiteLLM + Pydantic JSON enforcement)
│   ├── z3_engine/        # Symbolic Verification (Z3 Fixedpoint) & Datalog Translator
│   ├── compiler/         # Verified Topology → Vagrant/Ansible IaC output
│   └── visualization/    # Pyvis 3D HTML Engine
├── tests/                # Pytest test suite
└── build/                # Output directory for Vagrantfile, Ansible, & topology.html
```

## Setup Instructions
```bash
# Clone the repository
git clone https://github.com/JampaniKomal/Forge-Z3.git

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Execute test suite
pytest tests/
```
