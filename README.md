# Forge-Z3: Neuro-Symbolic Cyber Range Compiler

> **Read the `context/` folder for full project history, architecture decisions, and agent operating rules.**

## What is this?
A Python engine that takes a plain-English instruction, uses an LLM to draft a network topology, uses Microsoft's Z3 SMT solver to mathematically prove the attack path is valid, auto-repairs hallucinations via a CEGIS loop, and outputs bootable Infrastructure-as-Code.

## Project Structure
```
Forge-Z3/
├── .agents/          # Antigravity auto-discovery rules
├── context/          # Full project history & agent onboarding docs
├── research/         # Academic papers, pitch docs, deep research
├── src/              # Source code
│   ├── knowledge_base/   # CVE JSON database
│   ├── llm/              # LLM interface (API-based)
│   ├── datalog/          # JSON → Datalog translator
│   ├── z3_engine/        # Z3 SMT solver & CEGIS loop
│   ├── compiler/         # Verified topology → IaC output
│   └── cli/              # Rich CLI interface
├── tests/            # Unit tests
├── devlog/           # Development log (commit-by-commit progress)
└── requirements.txt
```

## Quick Start (Development)
```bash
python -m venv venv
venv\Scripts\activate       # Windows
pip install -r requirements.txt
python -m pytest tests/
```

## Status
See `devlog/DEVLOG.md` for current progress.
