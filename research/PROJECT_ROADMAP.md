# Project Roadmap: Neuro-Symbolic Cyber Range Compiler
## B.Tech 7th Semester Minor Project | RRU | Guide: Dr. Ravi Sheth
## Status: Pre-Development (Brainstorming Complete) | August 2026

---

## What Is This Project?

### The Objective
A Python engine that takes a plain-English instruction, mathematically proves the requested attack path is valid (not hallucinated), and outputs a bootable vulnerable lab environment automatically.

### Architecture Overview
Building a cyber range lab today takes significant manual effort. Pure LLM generation is unreliable due to hallucinations and logical impossibilities. Our system solves this by integrating:
- **Neural Layer (LLM):** Parses intent into a JSON topology.
- **Formal Verification (Z3 SMT):** Mathematically verifies the attack path is physically possible.
- **Feedback Loop (CEGIS):** If the AI makes a mistake, the solver extracts an unsat core, translates it to a repair prompt, and auto-repairs the topology.
- **Compiler Layer:** Generates deterministic Infrastructure-as-Code (IaC) to boot the VMs/Containers.

### The Academic Framing
This project implements a **Counterexample-Guided Inductive Synthesis (CEGIS)** architecture applied to the domain of automated cyber range generation. It combines Machine Learning, Formal Methods, and Systems Engineering. No existing open-source tool natively combines these three domains for this specific use case.

---

## Why This Project?

| Problem | Our Solution |
|---|---|
| Building cyber ranges takes expert hours | LLM generates topology from one sentence |
| LLMs hallucinate impossible attack paths | Z3 mathematically proves the path is real |
| No feedback when AI makes a mistake | CEGIS loop auto-repairs using unsat cores |
| Static labs become stale, students copy answers | Each generated lab is unique and mathematically validated |
| No open-source tool does end-to-end NLP→IaC with verification | **We build it** |

---

## The Full Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER INPUT                            │
│   "Build a 5-machine network teaching lateral movement      │
│    via Log4j vulnerability"                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           LAYER 1: NEURAL PERCEPTION                        │
│                                                              │
│   Local Llama 3.1 8B (via Ollama)                           │
│   + Constrained Decoding (JSON mode / Outlines)             │
│   + Pydantic Schema Validation                              │
│                                                              │
│   Output: Guaranteed-valid JSON topology                     │
│   {nodes: [...], edges: [...], vulns: [...], firewalls: ...} │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           LAYER 2: DATALOG TRANSLATION                      │
│                                                              │
│   JSON facts → Datalog predicates                           │
│   Node("WebServer"), Edge("Attacker","WebServer"),          │
│   VulnExists("WebServer","CVE-2021-44228",8080),            │
│   FirewallRule("Attacker","WebServer",8080)                 │
│                                                              │
│   Schema errors caught HERE → prompts LLM to fix           │
│   (Prevents Z3 crashes from malformed input)                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│    LAYER 3: SYMBOLIC REASONING — THE CEGIS LOOP            │
│                                                              │
│   Datalog facts + MulVAL interaction rules                  │
│   ──────────────────────────────────────────                │
│   z3.Fixedpoint (Spacer/µZ engine)                          │
│                                                              │
│   Query: "Can AttackerAccess('Database','ROOT') = SAT?"     │
│                                                              │
│   ┌─── SAT ──────────────────────────────────────────────┐  │
│   │  Attack path VERIFIED. Proceed to compiler.          │  │
│   └──────────────────────────────────────────────────────┘  │
│   ┌─── UNSAT ────────────────────────────────────────────┐  │
│   │  Extract unsat_core via assert_and_track             │  │
│   │  Translate to semantic repair prompt                  │  │
│   │  → Back to LLM (max 5 iterations)                    │  │
│   └──────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│           LAYER 4: COMPILER OUTPUT                          │
│                                                              │
│   Verified graph → SecGen XML                               │
│   Python xml.etree.ElementTree writes scenario file         │
│                                                              │
│   subprocess.run(["ruby","secgen.rb","--scenario",          │
│                   "scenario.xml","run"])                     │
│                                                              │
│   Output: Live, bootable, hackable VMs on laptop            │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

| Component | Tool | Why |
|---|---|---|
| **LLM (local)** | Llama 3.1 8B via Ollama | Air-gap friendly, ~4.5GB RAM, free |
| **JSON Enforcement** | Ollama JSON mode / Outlines | Logit-level masking → 100% valid JSON |
| **Schema Validation** | Pydantic v2 | Catches LLM output drift before Z3 |
| **Intermediate Rep.** | Datalog (custom predicates) | Buffer layer, crash-safe |
| **SMT Solver** | Z3 Python API (`z3-solver`) | Industry standard, free, Python-native |
| **Datalog Engine** | `z3.Fixedpoint` (built into Z3) | No extra library needed |
| **CVE Knowledge Base** | Hand-crafted 12-CVE JSON | Grounded, accurate, verifiable |
| **Output Compiler** | Python `xml.etree.ElementTree` | Generates SecGen XML |
| **Range Deployer** | SecGen + Vagrant + VirtualBox | Existing tool, no reinvention |
| **CLI Interface** | Python `Rich` library | Color-coded, professional look |
| **Visualization** | NetworkX + Pyvis | Attack graph overlay |

---

## The 5-Node Demo Topology (Fixed for PoC)

```
External Subnet (10.0.0.0/24)         Internal Subnet (172.16.0.0/24)
                                        
[Attacker: Kali] ──► [Firewall] ──► [Web Server]
   10.0.0.5           10.0.0.1        172.16.0.10
                                      └ CVE-2021-44228 (Log4j)
                                      └ Port 8080 open
                                             │
                                             ▼ (lateral movement)
                                       [App Server]
                                        172.16.0.20
                                        └ CVE-2021-4034 (PwnKit)
                                               │
                                               ▼ (privilege escalation)
                               Isolated Subnet (172.16.1.0/24)
                                       [Database Server]
                                        172.16.1.10
                                        └ FLAG stored here
```

**Z3 must verify:** Attacker can reach Database with ROOT access via this exact 3-step chain.

---

## The 12-CVE Knowledge Base

| # | CVE | Name | Attack Vector | Priv In | Priv Out |
|---|---|---|---|---|---|
| 1 | CVE-2021-44228 | **Log4Shell** | NETWORK | NONE | USER |
| 2 | CVE-2017-0144 | **EternalBlue (MS17-010)** | NETWORK | NONE | SYSTEM |
| 3 | CVE-2014-6271 | **Shellshock** | NETWORK | NONE | USER |
| 4 | CVE-2021-4034 | **PwnKit** | LOCAL | USER | ROOT |
| 5 | CVE-2021-3156 | **Baron Samedit (sudo)** | LOCAL | USER | ROOT |
| 6 | CVE-2019-0708 | **BlueKeep** | NETWORK | NONE | SYSTEM |
| 7 | CVE-2021-34527 | **PrintNightmare** | NETWORK | USER | SYSTEM |
| 8 | CVE-2017-5638 | **Apache Struts RCE** | NETWORK | NONE | USER |
| 9 | MISC-001 | **Default SSH Credentials** | NETWORK | NONE | USER |
| 10 | MISC-002 | **Anonymous FTP Access** | NETWORK | NONE | USER |
| 11 | MISC-003 | **SQLi → Auth Bypass** | NETWORK | NONE | USER |
| 12 | CVE-2020-1472 | **Zerologon** | ADJACENT | NONE | SYSTEM |

---

## Development Roadmap (18 Weeks — Aug to Nov 2026)

### ✅ PHASE 0: Foundations (Week 1–2)
**Goal:** Development environment fully operational

- [ ] Install Ollama + Llama 3.1 8B locally. Verify JSON mode works
- [ ] Install `z3-solver` Python package. Run hello-world Z3 script
- [ ] Install SecGen + Vagrant + VirtualBox. Manually boot one vulnerable VM
- [ ] Create GitHub repo with project structure
- [ ] Create `requirements.txt`

**Deliverable:** Screenshot of Z3 running + SecGen booting a VM manually

---

### 📋 PHASE 1: CVE Knowledge Base (Week 3–4)
**Goal:** The structured heart of the Z3 reasoning layer

- [ ] Design the 8-attribute CVE schema in Pydantic
- [ ] Hand-code all 12 CVEs into `knowledge_base.json`
- [ ] Write MulVAL-inspired interaction rules in Python (not Datalog yet — just dicts)
- [ ] Unit test: Given CVE-2021-44228, assert preconditions and postconditions are correctly structured

**Deliverable:** `knowledge_base.json` with 12 CVEs, unit tests passing

---

### 🤖 PHASE 2: Neural Perception Layer (Week 5–6)
**Goal:** LLM reliably generates Pydantic-validated JSON topology

- [ ] Design the Pydantic schema for topology JSON (nodes, edges, services, vulns, firewalls)
- [ ] Write the LLM prompt template (system prompt + few-shot examples)
- [ ] Enable Ollama JSON mode for constrained output
- [ ] Build the `llm_generator.py` module
- [ ] Test with 10 different natural language prompts. Verify 100% valid JSON output

**Deliverable:** `llm_generator.py` that takes a prompt and returns valid topology JSON 100% of the time

---

### 🔗 PHASE 3: Datalog Translation Layer (Week 7–8)
**Goal:** JSON → Datalog facts safely, with validation

- [ ] Define the Datalog predicate vocabulary (Node, Edge, Service, VulnExists, FirewallRule, AttackerAccess)
- [ ] Write `datalog_translator.py` that converts topology JSON → Datalog fact strings
- [ ] Add validation: reject any JSON field that doesn't map to a known predicate
- [ ] Test: convert 5 different topologies to Datalog, verify correctness

**Deliverable:** `datalog_translator.py` with validation and unit tests

---

### ⚙️ PHASE 4: Z3 CEGIS Reasoning Loop (Week 9–12) ← THE CORE
**Goal:** The self-healing verification loop working end-to-end

- [ ] Write `z3_engine.py` using `z3.Fixedpoint`
- [ ] Register all Datalog predicates as Z3 relations
- [ ] Implement MulVAL-inspired propagation rules (if Edge + Firewall → netAccess; if netAccess + VulnExists → execCode)
- [ ] Add `assert_and_track` for ALL facts (enables unsat core extraction)
- [ ] Write `cegis_loop.py`: runs Z3 → extracts unsat core → builds repair prompt → calls LLM → repeats
- [ ] Implement max iteration cap (5 attempts)
- [ ] Test: deliberately create a broken topology (missing firewall rule), verify UNSAT is detected and repaired automatically

**Deliverable:** End-to-end CEGIS loop working. CLI shows `[Z3 UNSAT] → [REPAIR] → [Z3 SAT]`

---

### 📄 PHASE 5: SecGen XML Compiler (Week 13–14)
**Goal:** Verified topology → deployable SecGen XML

- [ ] Study 3 real SecGen scenario XML files from the official repo
- [ ] Write `xml_compiler.py` using `xml.etree.ElementTree`
- [ ] Map verified Datalog nodes → `<system>` blocks
- [ ] Map verified CVEs → `<vulnerability cve="...">` tags
- [ ] Map verified subnets → `<network>` definitions
- [ ] Add subprocess call to invoke `ruby secgen.rb --scenario out.xml run`
- [ ] Test: Boot the 5-node demo topology end-to-end

**Deliverable:** `xml_compiler.py` that generates valid SecGen XML + VMs actually boot

---

### 🎨 PHASE 6: CLI + Visualization (Week 15–16)
**Goal:** A professional, demo-ready interface

- [ ] Wrap everything in a `main.py` CLI using Python `Rich`
- [ ] Color-coded pipeline stages: `[LLM]`, `[DATALOG]`, `[Z3]`, `[UNSAT]`, `[REPAIR]`, `[COMPILE]`, `[SUCCESS]`
- [ ] Build Streamlit or Jupyter dashboard
- [ ] NetworkX graph that renders the topology and highlights attack path in RED
- [ ] CEGIS iteration counter visible in UI

**Deliverable:** A professional-looking demo that can be screen-recorded for the presentation

---

### 🧪 PHASE 7: Testing & Report (Week 17–18)
**Goal:** Rock-solid execution + written report

- [ ] Test all 12 CVEs in the knowledge base generate valid scenarios
- [ ] Test 10 different natural language prompts end-to-end
- [ ] Test edge cases: impossible topology, conflicting CVEs, no attack path
- [ ] Write the project report (Introduction, Literature Review, Architecture, Implementation, Results)
- [ ] Prepare presentation slides
- [ ] **Final Validation:** Execute the end-to-end pipeline, demonstrating the auto-repair loop live.

**Deliverable:** Complete project + report + presentation

---

## End-to-End Execution Flow

1. User runs: `python main.py --prompt "Build a 5-machine network teaching lateral movement via Log4j"`
2. CLI output `[LLM]` — Generates JSON topology
3. CLI output `[DATALOG]` — JSON translated to predicates
4. CLI output `[Z3 CHECKING]` — Z3 Spacer/SAT engine evaluates rules
5. CLI output `[Z3 UNSAT]` (Red) — Example: Missing firewall rule `Attacker → WebServer:8080`
6. CLI output `[REPAIR]` — Semantic prompt sent back to LLM based on unsat core
7. LLM applies the structural fix
8. CLI output `[Z3 SAT]` (Green) — Attack path verified
9. CLI output `[COMPILE]` — Writing IaC output file
10. CLI output `[DEPLOY]` — Infrastructure spins up
11. Dashboard renders the verified attack path as a directed graph.

**Target execution time from prompt to verified configuration: < 60 seconds.**

---

## Risk Register & Architectural Trade-offs

| Risk/Trade-off | Likelihood | Mitigation / Strategy |
|---|---|---|
| **Vagrant/SecGen VM Overhead** | High | Vagrant is high-fidelity but slow. **Mitigation:** If VM booting is too slow for testing, we will write a secondary compiler targeting **Docker Compose** for rapid, lightweight containerized ranges. |
| **z3.Fixedpoint (Spacer) Limitations** | Medium | Spacer is built for infinite state (Horn clauses). If it struggles with finite network topologies, we will implement a fallback algorithm that flattens the Datalog rules into standard **Boolean SAT** formulas. |
| **Local LLM Latency** | Medium | Iterating a 5-step CEGIS loop on a local 8B model may take several minutes. **Mitigation:** Use heavily quantized models and vLLM for optimized inference speed. |
| **Automated CVE Extraction** | High | Fully automating CVE parsing into Datalog is currently error-prone NLP research. **Mitigation:** We will manually craft a high-quality 12-CVE JSON knowledge base to ensure the formal reasoning layer is perfectly grounded. |
| **Semester time runs out** | Medium | Phase 5 (working compiler) is the minimum viable product. Visualizations are optional polish. |

---

## Minimum Viable Product (MVP)

If time runs short, the following subset proves the core thesis:
- Phase 1: CVE Knowledge Base ✅
- Phase 2: LLM Topology Generation ✅  
- Phase 3: Datalog Translation ✅
- Phase 4: Z3 CEGIS Loop ✅ (This is the core academic contribution)
- Phase 5: Output a valid configuration file (even if auto-deployment is skipped)

The CEGIS loop alone, outputting verified configurations, is academically rigorous for a minor project.

---

## Open Engineering Decisions

1. **Deployment Target:** SecGen (Vagrant) provides realistic VM isolation, but Docker Compose provides speed. We will start with SecGen as planned, but keep Docker Compose as a lightweight alternative.
2. **LLM Inference:** Default is local (Llama 3.1 8B via Ollama). If hardware limits iteration speed, we will support dropping in an OpenAI/Gemini API key.
3. **Project Name:** To be decided (working titles: `NeSy-Range`, `CEGIS-Forge`, `SynapseRange`).
