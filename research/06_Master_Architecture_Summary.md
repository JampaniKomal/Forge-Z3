# Master Architecture Summary — All Research Synthesized
## Living Document | Last Updated: August 10, 2026
## Based on: 2x Gemini Deep Research + Independent Verification

---

## The Project in One Sentence
A Python engine that takes a plain-English cyber range request, generates a network topology using a local LLM, formally verifies the attack path using Z3 (CEGIS loop), auto-heals hallucinations, and outputs a ready-to-run SecGen XML file.

---

## The Full Pipeline (Confirmed Architecture)

```
[USER PROMPT]
    "Build a 5-machine network teaching lateral movement via Log4j"
        ↓
[LAYER 1: NEURAL PERCEPTION]
    Local Llama 3.1 8B + vLLM/Outlines (constrained decoding)
    Output: Pydantic-validated JSON topology
        ↓
[LAYER 2: DATALOG TRANSLATION]
    JSON → Datalog facts (Node, Edge, Service, VulnExists, FirewallRule)
    Schema validation catches drift BEFORE Z3
        ↓
[LAYER 3: SYMBOLIC REASONING — CEGIS LOOP]
    Datalog facts + MulVAL interaction rules → z3.Fixedpoint (Spacer/µZ)
    Z3 queries: "Can AttackerAccess('Database', ROOT) be satisfied?"
    
    IF SAT → Attack path verified → proceed to output
    IF UNSAT → extract unsat_core via assert_and_track → 
               build semantic repair prompt → back to LLM
    Max 5 iterations. If still UNSAT: reject, ask user to simplify.
        ↓
[LAYER 4: COMPILER OUTPUT]
    Verified Datalog graph → SecGen XML
    subprocess.run(["ruby", "secgen.rb", "--scenario", "out.xml", "run"])
        ↓
[RESULT]
    Live, hackable VMs on student's laptop
```

---

## Technology Stack (Final Decisions)

| Component | Technology | Rationale |
|---|---|---|
| LLM (local) | Llama 3.1 8B via Ollama | Air-gap friendly, 4.5GB RAM |
| Structured Output | vLLM + Outlines / Ollama JSON mode | Absolute JSON guarantee via logit masking |
| Intermediate Rep. | Datalog (custom facts) | Schema buffer, crash-safe |
| SMT Solver | Z3 Python API (`z3-solver`) | Industry standard, free, Python native |
| Datalog Engine | `z3.Fixedpoint` (Spacer/µZ) | Native Z3, no extra dependency |
| CVE Knowledge Base | Hand-crafted 12-CVE JSON + MulVAL rules | Grounded, accurate preconditions |
| Output Compiler | Python xml.etree.ElementTree | Generates SecGen XML |
| Deployer | SecGen + Vagrant + VirtualBox | Existing tool, no reinvention |
| Visualization | NetworkX + Pyvis or Streamlit | Attack path graph overlay |
| CLI | Python Rich library (color-coded stages) | Professional demo look |

---

## CVE Knowledge Base — The 12 CVEs

| # | CVE | Name | Vector | Pre-Priv | Post-Priv |
|---|---|---|---|---|---|
| 1 | CVE-2021-44228 | Log4Shell | NETWORK | NONE | USER |
| 2 | CVE-2017-0144 | EternalBlue | NETWORK | NONE | SYSTEM |
| 3 | CVE-2014-6271 | Shellshock | NETWORK | NONE | USER |
| 4 | CVE-2021-4034 | PwnKit | LOCAL | USER | ROOT |
| 5 | CVE-2021-3156 | Baron Samedit | LOCAL | USER | ROOT |
| 6 | CVE-2019-0708 | BlueKeep | NETWORK | NONE | SYSTEM |
| 7 | MISC-001 | Default SSH creds | NETWORK | NONE | USER |
| 8 | MISC-002 | Anonymous FTP | NETWORK | NONE | USER |
| 9 | MISC-003 | SQLi → auth bypass | NETWORK | NONE | USER |
| 10 | CVE-2021-34527 | PrintNightmare | NETWORK | USER | SYSTEM |
| 11 | CVE-2020-1472 | Zerologon | ADJACENT | NONE | SYSTEM |
| 12 | CVE-2017-5638 | Apache Struts RCE | NETWORK | NONE | USER |

---

## Demo Topology (5 Nodes — Fixed for PoC)

```
Subnet: 10.0.0.0/24 (external)      Subnet: 172.16.0.0/24 (internal)

[Attacker]  ──────►  [Firewall]  ─────►  [Web Server]
10.0.0.5              10.0.0.1            172.16.0.10
(Kali Linux)          (routing)           (CVE-2021-44228 Log4j)
                                                │
                                                ▼ lateral movement
                                      [App Server]
                                       172.16.0.20
                                       (CVE-2021-4034 PwnKit)
                                                │
                                                ▼ privilege escalation
                                      [Database Server]
                                       172.16.1.10 (isolated subnet)
                                       (flag stored here)
```

---

## What Still Needs Answering (Open Questions for Future Research)

1. **Does SecGen's `<vulnerability cve="...">` actually filter by exact CVE?** 
   Need to verify against real SecGen module metadata. Some modules may only match by module path, not CVE ID directly.

2. **z3.Fixedpoint performance** — Has anyone benchmarked Spacer/µZ on 5-node Datalog topologies? Need to test locally.

3. **Outlines compatibility with Ollama** — Outlines works natively with HuggingFace models. For Ollama, we may need to use Ollama's built-in JSON mode instead (less strict but still workable).

4. **Project Name** — Still not decided. "Cyber Abhyaas" is out. Working title: "NeSy-Range" or "CEGIS-Forge". Final name to be decided with Komal.

5. **Ravi Sir's Approval** — All of this architecture needs to be pitched to Ravi Sir before we write code. If he has specific constraints (no internet, specific hardware available in the lab), those will affect tool choices.
