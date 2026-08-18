# Forge-Z3: A Neuro-Symbolic Cyber Range Compiler
*Presentation Pitch Document for Dr. Ravi Sheth*

## Introduction
"Good morning, Dr. Sheth. Today I am presenting **Forge-Z3**, a Neuro-Symbolic compiler that completely automates the creation of physical cyber ranges."

### The Problem
- **Manual Cyber Range Creation is Slow:** Setting up vulnerable topologies (VMs, Ansible scripts, networking) takes days of manual DevOps work.
- **LLM Hallucinations:** Generative AI is great at designing networks, but it hallucinates. If you ask an LLM to design an attack path, it routinely generates broken topologies where the attacker physically cannot reach the target, or CVE prerequisites are mathematically impossible. You cannot pipe LLM output directly into Terraform without things breaking.

### The Solution
Forge-Z3 solves this by pairing a Neural Network (Generative AI) with a Symbolic Math solver (Z3 Theorem Prover). 
It generates mathematically proven infrastructure code.

---

## The 3-Layer Architecture

### Layer 1: Neural Generation (The LLM)
- The user provides a natural language prompt: *"Build a 3-node network where I pivot through a WebServer to get root on a Database."*
- We use a strict JSON-schema prompt to force the LLM to output a `Topology` object containing Nodes, Edges, and assigned Vulnerabilities.

### Layer 2: Symbolic Verification (The Z3 Engine)
- We built a mathematical model of "cyber physics" using Datalog and the Z3 SMT Solver.
- We programmed Z3 to understand that `Exploitation Requires Network Reachability AND Pre-Privileges`.
- **The CEGIS Loop (Counter-Example Guided Inductive Synthesis):** When the LLM hallucinates a broken topology, Z3 detects the failure (returns `UNSAT`). The system extracts the failure reason, feeds it back to the LLM, and forces it to regenerate. It loops until Z3 mathematically proves the attack path works (`SAT`).

### Layer 3: Infrastructure Actuation (The Compiler)
- Once Z3 verifies the attack path, the JSON is passed to our IaC Compiler.
- The compiler translates the topology into:
  1. A **Vagrantfile** to orchestrate the virtual machines.
  2. An **Ansible Playbook** mapping the CVEs to configuration roles.
  3. A **PyVis 3D HTML Map** to visually explore the range interactively in a web browser.

---

## Conclusion
"With Forge-Z3, we have successfully neutralized AI hallucination in infrastructure generation. By wrapping an LLM in a mathematical theorem prover, we guarantee that the cyber ranges generated are 100% executable and mathematically sound before a single VM is ever booted."
