# Technical Architecture and Decisions

## Overview
This document records the core architectural decisions, trade-offs, and design patterns chosen for Forge-Z3. It explains the 3-layer neuro-symbolic pipeline.

## The 3-Layer Pipeline

### 1. Neural Perception Layer (The "Compiler")
- **Role:** Takes a natural language prompt and translates it into a structured network topology.
- **Technology:** Local LLM (Llama 3.1 8B via Ollama).
- **Key Decision:** We cannot trust raw text generation. We must use **constrained decoding** (JSON mode or Outlines) and validate the output against strict Pydantic schemas. The AI is used *only* for structural generation, not for determining logical correctness.

### 2. Symbolic Reasoning Layer (The "Verifier" & CEGIS Loop)
- **Role:** Mathematically proves that the AI's generated topology is exploitable based on known CVE mechanics.
- **Technology:** Datalog (for intermediate representation) and **z3.Fixedpoint (Spacer)** (Microsoft's SMT solver).
- **The CEGIS Loop (Counterexample-Guided Inductive Synthesis):** If Z3 finds the attack path is impossible (e.g., a firewall blocks the needed port), it generates an `unsat_core`. This failure logic is fed back to the LLM to force it to repair the topology.
- **Key Decision:** We explicitly bounded the knowledge base to ~15 hardcoded CVEs. This mitigates the **State Explosion Problem** (where the SMT solver times out trying to calculate millions of paths). The CVE physics (Pre-Privileges, Post-Privileges, network vectors) must be flawless for the math to work.

### 3. Infrastructure Compiler (The "Deployer")
- **Role:** Translates the mathematically verified logic into bootable Infrastructure-as-Code (IaC).
- **Technology:** SecGen XML (via Vagrant/VirtualBox) as the primary target. Docker Compose as a fallback.
- **Key Decision:** We are not building VMs from scratch. We are compiling configuration files that instruct existing deployers (like SecGen) to assemble pre-existing vulnerable modules.

## Major Trade-offs & Alternatives Explored
1. **Docker vs. Vagrant:** Vagrant (SecGen) provides high-fidelity OS isolation (kernel exploits work), but is very slow. Docker is fast but less realistic. We plan to target SecGen XML first, but keep Docker Compose in mind as a lightweight MVP alternative if local hardware struggles.
2. **z3.Fixedpoint vs. Boolean SAT:** z3.Fixedpoint natively understands Datalog, saving us translation effort. However, if it performs poorly on finite network topologies, we have documented a fallback strategy to flatten the Datalog rules into standard Boolean SAT formulas.
3. **Manual vs. Automated CVE Extraction:** We rejected automated NLP extraction of CVEs because it introduces logical noise. The Z3 solver requires perfect "physics", meaning the CVE interaction rules must be hand-crafted into the system.
