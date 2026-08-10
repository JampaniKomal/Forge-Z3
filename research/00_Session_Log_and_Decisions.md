# Brainstorming Log — Session Summary (August 10, 2026)

This file captures the full context of every discussion and decision made so far. If this project is revisited in a new chat, start here.

---

## The Student
- **Name:** Jampani Komal
- **Enrollment:** 230031101611054
- **University:** Rashtriya Raksha University (RRU)
- **Program:** B.Tech CSE (Cybersecurity)
- **Semester:** 7th (ODD 2026)
- **Project Type:** Minor Project (G7A40MIP) — 7 Credits, 14 hrs/week practical

## The Guide
- **Professor:** Dr. Ravi Sheth
- **Role:** Senior Assistant Professor, SITAICS
- **Research Interests:** VAPT, Machine Learning, Cyber Forensics, Darknet Investigation
- **Also Teaching:** Machine Learning course this very semester to Komal

## Key Decisions Made
1. **GRC is OUT.** The official guide list shows GRC domain, but that was filled for Richa Ma'am. Ravi Sir rejected GRC and wants a different direction.
2. **Cyber Abhyaas name is OUT.** Komal never liked the name. Will be renamed.
3. **Full Cyber Range Infrastructure is OUT.** Too risky for one student — DevOps burnout risk (hypervisors, networking bugs, Proxmox).
4. **The 3-Layer architecture is partially in.** The *concept* of Compiler → Topology → Deployer is valid, but we are NOT building the deployer in this semester. We are building only the "Brain" — the Neuro-Symbolic compiler engine that generates the blueprint.

## The Chosen Direction (Pending Final Confirmation)
**Project: A Neuro-Symbolic Infrastructure Compiler for Automated Cyber Range Generation**

### In Plain English:
A Python engine that takes a plain English prompt ("Build me a 3-machine network with a Log4j vulnerability and a lateral movement attack path") and outputs a mathematically proven, ready-to-deploy Infrastructure-as-Code blueprint (SecGen XML or Terraform).

### The 3-Stage Pipeline:
1. **Neural Layer (LLM):** Translates natural language → JSON topology + attack graph draft.
2. **Symbolic Layer (Z3 SMT Solver):** Validates the JSON mathematically. Proves the attack path is actually feasible. Catches LLM hallucinations. If broken, feeds the error back to the LLM to auto-correct (Self-Healing Loop).
3. **Compiler Layer (Code Generator):** Translates the verified JSON → SecGen XML / Terraform HCL files.

### Why It's Original (Confirmed):
- No open-source tool combines LLM + Z3 + IaC generation for cyber ranges.
- The closest academic work is VSDL (which uses SMT but no LLM) and GARAGE (which uses LLM but no formal verification). We bridge both.
- This is publishable research, not just a student project.

### Why It Impresses Ravi Sir:
- Hits his ML expertise directly (LLM layer, neuro-symbolic AI).
- Hits his VAPT expertise (the output is attack graph blueprints).
- No other student in RRU history will have submitted something this technically advanced.

## Still To Decide
- Final project name (dropping "Cyber Abhyaas")
- Whether to use a local LLM (Llama/Mistral) or an API (Gemini/OpenAI)
- Whether the PoC output targets SecGen XML or Terraform
- Scope of the CVE knowledge base for the PoC (start with 5-10 well-known CVEs)
