<div align="center">
  <h1>Forge-Z3: Neuro-Symbolic Cyber Range Compiler</h1>
  <p><b>Bridging Large Language Models with Formal Mathematical Verification</b></p>
</div>

## Overview
Forge-Z3 is a state-of-the-art Infrastructure Compiler that utilizes **Neuro-Symbolic AI** to automatically generate, verify, and deploy vulnerable cyber ranges for defensive training and red-teaming exercises.

Instead of relying purely on the probabilistic output of Large Language Models (which frequently hallucinate physically impossible network topologies), Forge-Z3 utilizes **Counterexample-Guided Inductive Synthesis (CEGIS)**:

1. **Neural Generation:** An LLM generates a JSON topology based on a natural language specification.
2. **Symbolic Verification:** Microsoft's Z3 SMT Solver mathematically proves whether the attack path is physically possible using a Datalog engine.
3. **Self-Healing Loop:** If Z3 detects a structural hallucination (`UNSAT`), it automatically extracts the failure reason and prompts the LLM to self-correct.
4. **Compilation:** Once mathematically proven, the engine compiles the network into a bootable `Vagrantfile` and Ansible Playbooks.

*Built by Jampani Komal at Rashtriya Raksha University (RRU).*

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
