# Forge-Z3 Agent Rules

> These rules are automatically loaded by Antigravity when working in this repository.

## Project Identity
- **Name:** Forge-Z3: A Neuro-Symbolic Cyber Range Compiler
- **Student:** Jampani Komal (B.Tech 7th Sem, RRU)
- **Guide:** Dr. Ravi Sheth

## Mandatory Reading Before Any Work
1. Read `context/03_Agent_Onboarding.md` for strict operating rules.
2. Read `context/02_Technical_Architecture_and_Decisions.md` for the 3-layer architecture.
3. Read `devlog/DEVLOG.md` to understand what has been built so far.

## Architecture (Do Not Violate)
The pipeline is: `Natural Language → LLM (JSON) → Datalog → Z3 CEGIS Loop → IaC Output`
- The Z3 verification layer is the core academic contribution. Never bypass it.
- The CVE knowledge base is intentionally bounded to ~15 CVEs (State Explosion Problem).
- LLM integration uses an external API (Gemini/Groq), NOT local Ollama, due to hardware constraints on some dev machines.

## Code Standards
- Python 3.10+
- Type hints on all functions
- Pydantic v2 for all data schemas
- Unit tests for every module in `tests/`
- Commits must be descriptive and atomic

## User Preferences
- No frontends or dashboards until the backend is 100% complete.
- No pampering. Be direct and harsh about technical trade-offs.
- This is NOT a mockup. Every component must produce real, verifiable output.
