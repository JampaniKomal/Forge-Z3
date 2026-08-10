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
   A natural language prompt (e.g., *"Build a 3-machine network demonstrating lateral movement via CVE-2021-44228"*) is parsed by a local LLM (Llama 3.1 8B). Using constrained decoding, the LLM generates a strictly formatted JSON network topology.
2. **Symbolic Reasoning Layer (The Verifier):** 
   The JSON topology is translated into Datalog predicates. The Z3 SMT (Satisfiability Modulo Theories) solver evaluates this logic against a hardcoded knowledge base of CVE mechanics and network rules (inspired by the MulVAL attack graph generator). 
3. **The CEGIS Loop (Self-Healing):**
   If Z3 determines the attack path is logically impossible (UNSAT), it extracts the exact point of failure (`unsat_core`) and sends a corrective prompt back to the LLM. This Counterexample-Guided Inductive Synthesis (CEGIS) loop forces the AI to self-correct until the network is mathematically proven to be vulnerable.
4. **Infrastructure Compiler (The Deployer):**
   Once verified, the engine compiles the logic into an executable XML/YAML file that can be consumed by deployment frameworks (like SecGen or Vagrant) to boot the physical Virtual Machines.

## 3. Academic & Practical Justification
- **Scalability & Anti-Plagiarism:** Automated, randomized instantiation allows instructors to generate 50 unique but mathematically equivalent labs for 50 students, neutralizing plagiarism.
- **State-of-the-Art Integration:** Combining AI with Formal Methods (Neuro-Symbolic AI) is currently one of the most heavily researched areas in computer science, moving away from purely heuristic AI toward deterministic safety.

## 4. Key References & Literature Review

This project builds upon recent state-of-the-art research in automated security modeling and formal verification:

1. **Automated Vulnerability Modeling:**
   - *Ou, X., Boyer, W. F., & McQueen, M. A. (2006). "A scalable approach to attack graph generation." (MulVAL)* 
     - **Application:** Forge-Z3 adapts MulVAL’s Datalog approach to define the logical preconditions of vulnerabilities.
2. **Neuro-Symbolic Verification (2025-2026):**
   - *"ProofNet++: A Neuro-Symbolic System for Formal Proof Verification with Self-Correction" (arXiv:2505.13840)*
     - **Application:** Demonstrates the efficacy of using LLMs in a loop with formal provers to iteratively correct logical errors.
   - *"FormalJudge: A Neuro-Symbolic Paradigm for Agentic Oversight" (arXiv:2602.05432)*
     - **Application:** Validates the use of Z3 SMT solvers to provide deterministic proofs over AI-generated outputs, preventing hallucinations in security contexts.
3. **Infrastructure Automation:**
   - *SecGen: Security Scenario Generator (GitHub/SecGen)*
     - **Application:** Forge-Z3 acts as the intelligent front-end compiler, passing verified topologies to SecGen for physical VM provisioning.

## 5. Minimum Viable Product (MVP)
By the end of the semester, the core MVP will demonstrate the end-to-end CEGIS loop: parsing a natural language prompt, triggering an intentional Z3 `UNSAT` failure, auto-repairing the topology, and outputting the verified infrastructure code.
