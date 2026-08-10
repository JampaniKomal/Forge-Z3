# AI Agent Onboarding & Context

> **WARNING TO ALL FUTURE AI AGENTS / INSTANCES:**
> Read this document completely before suggesting changes, writing code, or advising the user on this repository. 

## 1. The User
- **Name:** Jampani Komal
- **Context:** B.Tech 7th Semester Minor Project at Rashtriya Raksha University (RRU).
- **Guide:** Dr. Ravi Sheth.
- **Mindset:** The user prioritizes robust, hardcore systems engineering over flashy frontends. The user strictly does not want a "mockup", a "prototype", or a "clone". The user wants a deeply technical, mathematically sound backend engine. 

## 2. The Project: Forge-Z3
- **What it is:** A Neuro-Symbolic Cyber Range Compiler.
- **What it does:** It takes a natural language prompt, uses an LLM to generate a JSON network topology, uses the **Z3 SMT solver** to mathematically verify that the attack path works (using a CEGIS auto-repair loop), and then compiles that logic into deployable Infrastructure-as-Code.
- **What it is NOT:** It is NOT a web dashboard. It is NOT a GRC platform. It is NOT just an LLM wrapper. 

## 3. Strict Operating Rules for AI Agents
If you (the AI) are assisting the user in this repository, you must adhere to the following rules:

### A. Do Not Pamper the User
Be direct, objective, and harsh when evaluating technical decisions. If an idea compromises the mathematical rigor of the SMT solver, reject it and explain why.

### B. Respect the 3-Layer Architecture
Do not suggest bypassing the Z3 verification layer. The entire academic value of this project rests on the CEGIS loop (Layer 2). Without it, this is just an LLM wrapper.

### C. No Frontends (Unless Explicitly Requested)
Do not suggest building React dashboards, Streamlit UIs, or web portals unless the core backend engine is 100% complete and tested. The UI is the least important part of this project.

### D. Hardware Awareness
The user is developing this locally. The LLM (Llama 3.1) and the VMs (VirtualBox/Vagrant) will consume significant RAM. Always optimize code for local execution speed and memory efficiency.

### E. References to the "Mockup"
If the user asks if this is a mockup, remind them that the output of this engine is a **real, bootable configuration file** that spins up physical virtual machines. Z3 performs **real mathematical proofs**. There is nothing "fake" about this pipeline.

## 4. Where to Pick Up (Next Actions)
As of August 2026, the project is in the **Pre-Development** phase. The research is complete, the roadmap is set, and the academic pitch is written. 

**DO NOT START WRITING CODE** until the user explicitly states their powerful laptop has arrived and they are ready to begin **Phase 0** (Environment Setup).
