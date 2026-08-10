# B.Tech 7th Semester Minor Project Proposal

**Project Title:** Forge-Z3: A Neuro-Symbolic Cyber Range Compiler
**Student:** Jampani Komal
**Guide:** Dr. Ravi Sheth
**Institution:** Rashtriya Raksha University (RRU)

---

## 1. Project Overview
Building customized, high-fidelity cyber ranges for defensive training and red-team exercises is a notoriously resource-intensive task. Currently, generating a vulnerable network topology requires significant manual orchestration. 

While Large Language Models (LLMs) can generate text-based network topologies rapidly, they suffer from inherent probabilistic limitations (hallucinations). An LLM may propose an attack path that is structurally or physically impossible (e.g., placing an exploitable service behind a misconfigured firewall). 

**Forge-Z3** solves this by implementing a **Neuro-Symbolic Architecture**. It bridges the generative flexibility of an LLM with the deterministic mathematical guarantees of a Formal Theorem Prover (Microsoft's Z3). The output is a mathematically verified, bootable infrastructure-as-code (IaC) configuration.

## 2. Core Architecture: The "Compiler" Pipeline
The project functions as an Infrastructure Compiler operating in three distinct layers:

1. **Neural Perception Layer (The Generator):** 
   A natural language prompt (e.g., *"Build a 3-machine network demonstrating lateral movement via CVE-2021-44228 — DMZ web server → internal app server → database"*) is parsed by a local LLM (Llama 3.1 8B). Using constrained decoding, the LLM generates a strictly formatted JSON network topology.
2. **Symbolic Reasoning Layer (The Verifier & Self-Healing Loop):** 
   The JSON topology is translated into Datalog predicates. Z3's Datalog/Fixedpoint engine (PDR/Spacer) evaluates this logic against a hardcoded knowledge base of CVE mechanics and network rules (inspired by the MulVAL attack graph generator). 
   - *The CEGIS Loop:* If Z3 determines the attack path is logically impossible (UNSAT), it extracts the exact point of failure (`unsat_core`) and sends a corrective prompt back to the LLM. This Counterexample-Guided Inductive Synthesis (CEGIS) loop forces the AI to self-correct until the network is mathematically proven to be vulnerable.
3. **Infrastructure Deployment Layer (The Deployer):**
   Once verified, the engine compiles the logic into an executable XML/YAML file that can be consumed by deployment frameworks (like SecGen or Vagrant) to boot the physical Virtual Machines.

## 3. Academic & Practical Justification
- **Cyber Abhyaas Ecosystem:** This project feeds directly into the broader vision of the Cyber Abhyaas platform, providing future cohorts and instructors with mathematically verifiable, automated cyber range generation.
- **Scalability & Anti-Plagiarism:** Automated, randomized instantiation allows instructors to generate 50 unique but mathematically equivalent labs for 50 students, neutralizing plagiarism.
- **State-of-the-Art Integration:** Combining AI with Formal Methods (Neuro-Symbolic AI) is currently one of the most heavily researched areas in computer science, moving away from purely heuristic AI toward deterministic safety.

## 4. Key References & Literature Review

This project builds upon recent state-of-the-art research in automated security modeling and formal verification:

1. **Automated Vulnerability Modeling:**
   - *Ou, X., Boyer, W. F., & McQueen, M. A. (2006). ["A scalable approach to attack graph generation." (MulVAL)](https://dl.acm.org/doi/10.1145/1102120.1102124)* 
     - **Application:** Forge-Z3 adapts MulVAL’s Datalog approach to define the logical preconditions of vulnerabilities.
2. **Neuro-Symbolic Verification (Analogous Architectures):**
   - *["ProofNet++: A Neuro-Symbolic System for Formal Proof Verification with Self-Correction"](https://arxiv.org/abs/2505.24230)*
     - **Context:** Explores LLM+Lean/HOL Light theorem proving on math benchmarks.
     - **Application:** Validates the LLM+formal-verifier+self-correction loop pattern in theorem proving. Forge-Z3 represents a novel application of this pattern to bridge the gap in network/CVE modeling.
   - *["FormalJudge: A Neuro-Symbolic Paradigm for Agentic Oversight"](https://arxiv.org/abs/2602.11136)* **(ICML 2026)**
     - **Context:** Introduces the "Formal-of-Thought" architecture: LLMs act as specification compilers decomposing intent into atomic constraints, verified deterministically by Dafny+Z3 (achieving 16.6% performance improvement over LLM-as-Judge baselines).
     - **Application:** Forge-Z3 directly adapts this paradigm — the LLM decomposes a natural language network description into verifiable Datalog predicates, which are then evaluated deterministically by Z3's Fixedpoint engine.
3. **Infrastructure Automation:**
   - *[SecGen: Security Scenario Generator](https://github.com/SecGen/SecGen)*
     - **Application:** Forge-Z3 acts as the intelligent front-end compiler, passing verified topologies to SecGen for physical VM provisioning.

## 5. Objectives & Expected Outcomes
- **Objectives:** 
  - Develop a local neuro-symbolic pipeline capable of generating verified attack graphs from natural language.
  - Implement a CEGIS loop using Z3's PDR/Spacer engine to autonomously correct LLM structural hallucinations.
  - Output deployable infrastructure-as-code for a target environment.
- **Expected Outcomes (Evaluation Criteria):** The system must successfully auto-resolve at least 5/5 deliberately injected UNSAT cases (e.g., a firewall blocking the Log4Shell JNDI egress path) without human intervention, producing a Z3-verified vulnerable topology.

## 6. Tools & Tech Stack
- **AI/LLM:** Llama 3.1 8B (via Ollama/llama.cpp for local, constrained JSON decoding).
- **Formal Verification:** Python, Z3 SMT Solver (Z3py) with Datalog/Fixedpoint engine (PDR/Spacer).
- **Deployment (Stretch):** SecGen, Vagrant, or Terraform.

## 7. Project Scope & Minimum Viable Product (MVP)
Given the complexity of a neuro-symbolic pipeline, the semester's MVP is strictly scoped:
- **Knowledge Base:** Hardcode a small, closed knowledge base of 5–8 specific CVEs (rather than generalized coverage).
- **Topology:** Focus entirely on verifying 1 specific topology class (e.g., a 3-node lateral movement scenario) for the final demo.
- **Stretch Goal:** While compiling logic to XML/YAML is core, full end-to-end physical provisioning via SecGen/Vagrant is a stretch goal depending on time constraints.

## 8. Feasibility & Risk Management
- **Primary Risk:** Relying on a smaller local 8B model to perform reliable constrained JSON generation *and* effectively steer itself via CEGIS feedback may prove challenging. Small models can struggle to generalize from formal `unsat_core` feedback.
- **Fallback Plan:** If the local 8B model fails to converge reliably, the fallback is to integrate a larger, hosted model (e.g., OpenAI/Anthropic APIs) to guarantee the reasoning capabilities required for the demo, swapping back to local optimization post-MVP.

## 9. Proposed Timeline
- **Phase 1 (Weeks 1-3):** Datalog rule translation for 5-8 CVEs and manual Z3 verification.
- **Phase 2 (Weeks 4-6):** LLM integration with constrained JSON decoding for the 3-node topology.
- **Phase 3 (Weeks 7-10):** Implementation of the CEGIS feedback loop and `unsat_core` parsing.
- **Phase 4 (Weeks 11-14):** System evaluation, IaC generation, and final documentation.
