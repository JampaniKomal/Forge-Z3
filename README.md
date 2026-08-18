<div align="center">
  <h1>Forge-Z3: Neuro-Symbolic Cyber Range Compiler</h1>
  <p><b>Bridging Large Language Models with Formal Mathematical Verification</b></p>
</div>

## Overview
Forge-Z3 is a state-of-the-art Infrastructure Compiler that uses **Neuro-Symbolic AI** to automatically generate, verify, and deploy vulnerable cyber ranges (networks) for defensive training and red-teaming.

Instead of relying purely on the probabilistic output of LLMs (which frequently hallucinate physically impossible network topologies), Forge-Z3 utilizes **Counterexample-Guided Inductive Synthesis (CEGIS)**. 

1. **Neural Generation:** An LLM generates a JSON topology based on natural language.
2. **Symbolic Verification:** Microsoft's Z3 SMT Solver mathematically proves whether the attack path is physically possible using Datalog.
3. **Self-Healing Loop:** If Z3 detects a hallucination (`UNSAT`), it automatically extracts the failure reason and prompts the LLM to self-correct.
4. **Compilation:** Once mathematically proven, the engine compiles the network into a bootable `Vagrantfile` and Ansible Playbooks.

*Built by Jampani Komal at Rashtriya Raksha University (RRU) in collaboration with Antigravity AI.*

---

## 🖥️ The UI (Visual Dashboard)
Forge-Z3 operates primarily as a **CLI Compiler** with rich terminal output. 

However, upon successful compilation, it automatically generates a **3D Interactive Visual Dashboard**. 
You will find this file at `build/topology.html`. Opening it in any web browser provides a fully interactive 3D map of the generated network, allowing you to visually inspect nodes, IP addresses, vulnerabilities, and exact attack paths.

---

## 🚀 How to Run (All Supported Models)
Forge-Z3 uses the `litellm` framework, making it completely model-agnostic. You can hot-swap the AI engine depending on your hardware and API limits.

### 1. Google Gemini (Default - Free Tier)
The most reliable free option. Ensure you have your `GEMINI_API_KEY` set in your `.env` file.
```bash
python -m src.main "Build me a 3-node network where I pivot through a WebServer to hack a Database." --model gemini/gemini-flash-latest
```

### 2. Groq (Blazing Fast Llama-3)
The absolute fastest generation speed. Ensure your `GROQ_API_KEY` is set in `.env`.
```bash
python -m src.main "Build me a 3-node network..." --model groq/llama-3.3-70b-versatile
```
*(Note: Check the Groq console for the latest active model string, as they deprecate models frequently).*

### 3. Local Ollama (100% Offline & Free)
Run the engine entirely on your local hardware without any internet connection. Make sure the Ollama app is running in your system tray.
```bash
python -m src.main "Build me a 3-node network..." --model ollama/llama3
```

### 4. Remote Ollama (SSH Tunnel / Wi-Fi Bypass)
If you want to run the compiler on a lightweight laptop while offloading the heavy LLM generation to a friend's powerful GPU over the internet:
1. Have your friend run: `ssh -R 80:localhost:11434 nokey@localhost.run`
2. Copy the `.lhr.life` URL it generates.
3. Place the URL in your `.env` file: `OLLAMA_API_BASE="https://<URL>.lhr.life"`
4. Run your command!
```bash
python -m src.main "Build me a 3-node network..." --model ollama/qwen2.5:7b
```

---

## 🛠️ Project Architecture
```text
Forge-Z3/
├── .agents/          # Antigravity AI rules
├── context/          # Documentation & Academic context
├── src/
│   ├── knowledge_base/   # CVE rules (Log4Shell, ProFTPd, MySQL, etc.)
│   ├── generator/        # Neural perception (LiteLLM + Pydantic JSON enforcement)
│   ├── z3_engine/        # Symbolic Verification (Z3 Fixedpoint) & Datalog Translator
│   ├── compiler/         # Verified Topology → Vagrant/Ansible IaC output
│   └── visualization/    # Pyvis 3D HTML Engine
├── tests/            # Pytest test suite
└── build/            # Output directory for Vagrantfile, Ansible, & topology.html
```

## Setup Instructions
```bash
# Clone the repository
git clone https://github.com/yourusername/Forge-Z3.git

# Create virtual environment
python -m venv venv
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Run the tests
pytest tests/
```
