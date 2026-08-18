# Forge-Z3: Deep Dive Architecture

## The Core Problem
Generating custom, high-fidelity cyber ranges for defensive training and red-team exercises is a highly manual, resource-intensive task. While Generative AI (LLMs) can rapidly design text-based network topologies, they suffer from inherent probabilistic limitations—commonly known as hallucinations. 

If an LLM is asked to build an attack path, it will frequently generate a topology that is structurally or physically impossible (e.g., placing an exploitable service behind a misconfigured firewall, or assuming lateral movement without prior exploitation). You cannot pipe raw LLM output into deployment engines like Terraform or Vagrant without continuous failures.

## The Neuro-Symbolic Solution
Forge-Z3 solves this by implementing a **Neuro-Symbolic Architecture**. It bridges the generative flexibility of an LLM with the deterministic mathematical guarantees of a Formal Theorem Prover (Microsoft's Z3). The output is a mathematically verified, bootable infrastructure-as-code (IaC) configuration.

### Layer 1: Neural Perception (The Generator)
The system receives a natural language prompt (e.g., *"Build a 3-machine network demonstrating lateral movement via CVE-2021-44228"*).
- Using **LiteLLM**, the engine queries the model (Google Gemini, Groq Llama 3, or local Ollama).
- Using **Pydantic**, the engine forces the LLM to use constrained decoding, ensuring the output is a strictly formatted JSON network topology containing Nodes, Edges, and Vulnerabilities.

### Layer 2: Symbolic Verification (The Z3 Engine)
The JSON topology is translated into Datalog predicates. Z3's Datalog/Fixedpoint engine (PDR/Spacer) evaluates this logic against a hardcoded knowledge base of CVE mechanics and cyber-physical network rules (inspired by the MulVAL attack graph generator).

- **The CEGIS Loop (Counterexample-Guided Inductive Synthesis):** 
If Z3 determines the attack path is logically impossible (`UNSAT`), it extracts the exact point of failure (`unsat_core`). This mathematical failure reason is injected into a corrective prompt and sent back to the LLM. This feedback loop forces the AI to self-correct its hallucinations iteratively until the network is mathematically proven to be vulnerable (`SAT`).

### Layer 3: Infrastructure Deployment (The Compiler)
Once verified by the math engine, the JSON topology is passed to the IaC Compiler.
- The compiler translates the proven topology into an executable `Vagrantfile`.
- It generates an Ansible `inventory.ini` and `site.yml` mapping the CVEs to specific configuration roles to automatically provision the vulnerable services upon boot.
- It triggers a Python PyVis engine to render an interactive 3D HTML map of the network for the user.

## Conclusion
By wrapping a probabilistic neural network inside a deterministic mathematical theorem prover, Forge-Z3 guarantees that the cyber ranges it generates are 100% executable and mathematically sound before a single Virtual Machine is ever booted.
