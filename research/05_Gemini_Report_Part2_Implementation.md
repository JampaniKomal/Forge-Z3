# Gemini Deep Research Report — Part 2
## Neuro-Symbolic Infrastructure Compilation: Architectural Implementation
### Source: Gemini Deep Research | Date: August 10, 2026

---

## 1. SecGen XML Schema — The Exact Output Target

### Root Structure
```xml
<?xml version="1.0"?>
<scenario xmlns="http://www.github/cliffe/SecGen/scenario" 
          xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
          xsi:schemaLocation="http://www.github/cliffe/SecGen/scenario">
    
    <!-- Shared network definition (reused across systems) -->
    <network type="private_network" name="intranet" subnet="172.28.128.0/24"/>
    
    <!-- Machine 1: Public-facing web server with Log4j -->
    <system>
        <base module_path="bases/linux/debian/buster"/>
        <network type="private_network" name="intranet"/>
        <network type="public_network" name="internet"/>
        <vulnerability cve="CVE-2021-44228"/>
        <service name="apache"/>
    </system>
    
    <!-- Machine 2: Internal server requiring lateral movement -->
    <system>
        <base module_path="bases/linux/debian/buster"/>
        <network type="private_network" name="intranet"/>
        <vulnerability cve="CVE-2021-3156"/>
        <datastore name="flag1">
            <generator type="random_string"/>
        </datastore>
    </system>
</scenario>
```

### Key XML Elements
| Element | Description | Required for Compiler |
|---|---|---|
| `<scenario>` | Root element with namespace defs | Always |
| `<system>` | One VM per block | One per topology node |
| `<base module_path="...">` | OS template (Debian, Windows, etc.) | Maps from node's OS field |
| `<network type="..." name="...">` | Virtual network interface | Maps from topology edges/subnets |
| `<vulnerability cve="...">` | CVE injection | Maps from Z3-verified exploit |
| `<service name="...">` | Background services | Maps from node service requirements |
| `<datastore>` + `<generator>` | CTF flags | Optional for demo polish |

### Python Invocation
```python
import subprocess
result = subprocess.run(
    ["ruby", "secgen.rb", "--scenario", "compiled_scenario.xml", "run"],
    cwd="/path/to/SecGen"
)
```

---

## 2. CVE Precondition Knowledge Base — The Minimal Schema

### Why CAPEC/MITRE ATT&CK Are NOT Enough
CAPEC prerequisites are human-readable ("The target must be running a web server that does not sanitize input") — NOT Boolean-typed for Z3. They require NLP to parse, reintroducing the hallucination problem. Use MulVAL Datalog rules instead.

### The 8 CVE Attributes Required for Z3 Encoding
| Attribute | Z3 Type | Description |
|---|---|---|
| Vulnerability ID | String | CVE ID. Used in unsat core reporting + SecGen XML |
| Target OS | Enum/Bool | Linux/Windows. Prevents cross-OS exploit attempts |
| Target Service | String | SSH, HTTP, SMB. Matches `networkService` predicate |
| Network Protocol | Enum (TCP/UDP) | For firewall rule evaluation |
| Target Port | Int | Static for known services (80, 443, 22, 445) |
| Precondition Privilege | Enum | NONE (unauthenticated), USER (local), ROOT |
| Postcondition Privilege | Enum | USER, ROOT, SYSTEM. Maps to `execCode` |
| Access Vector | Enum | NETWORK, LOCAL, ADJACENT, PHYSICAL |

### The MulVAL Interaction Rule Model (Reuse This!)
MulVAL's `interaction_rules.P` defines exploit logic in Datalog:
```prolog
% Remote code execution rule
execCode(Host, Perm) :-
    vulExists(Host, VulID, Software, remoteExploit, privEscalation),
    networkService(Host, Software, Protocol, Port, Perm),
    netAccess(Host, Protocol, Port).

% Lateral movement rule (credential reuse)
execCode(Host, Perm) :-
    principalCompromised(Victim),
    hasAccount(Victim, Host, Perm).
```
**We do NOT need to invent a new vulnerability ontology. We adopt MulVAL's interaction rules directly.**

### Recommended CVE Knowledge Base (10-15 CVEs for PoC)
| Category | CVE Examples | Quantity |
|---|---|---|
| Remote Code Execution | Log4Shell (CVE-2021-44228), EternalBlue (CVE-2017-0144) | 3 |
| Web App Vulnerabilities | SQLi, SSRF, XSS leading to auth bypass | 3 |
| Local Privilege Escalation | PwnKit (CVE-2021-4034), Baron Samedit (CVE-2021-3156) | 3 |
| Misconfigurations | Anonymous FTP, Default SSH credentials | 3 (no CVE needed) |

---

## 3. Datalog as Intermediate Representation (IR)

### The z3.Fixedpoint API (Critical Discovery!)
Z3 has a **native Datalog engine** called **Spacer/µZ** accessible via the `z3.Fixedpoint` class. We do NOT need to manually parse Datalog and translate to Z3 constraints. We can feed Datalog rules DIRECTLY into Z3:

```python
from z3 import *

fp = Fixedpoint()
fp.set(engine='datalog')

# Declare relations (Datalog predicates)
Node   = Function('Node',   StringSort(), BoolSort())
Edge   = Function('Edge',   StringSort(), StringSort(), BoolSort())
Vuln   = Function('VulnExists', StringSort(), StringSort(), IntSort(), BoolSort())
Fw     = Function('FirewallRule', StringSort(), StringSort(), IntSort(), BoolSort())
Access = Function('AttackerAccess', StringSort(), StringSort(), BoolSort())

# Register rules (network physics)
n1, n2, n3 = Consts('n1 n2 n3', StringSort())
port = Int('port')

# If edge exists AND firewall allows → network access is possible
fp.rule(Access(n2, 'network'), [Edge(n1, n2), Fw(n1, n2, port)])

# Add facts from LLM-generated JSON
fp.fact(Edge('Attacker', 'WebServer'))
fp.fact(VulnExists('WebServer', 'CVE-2021-44228', 8080))
fp.fact(FirewallRule('Attacker', 'WebServer', 8080))

# Query: Can attacker reach WebServer?
result = fp.query(Access('WebServer', 'network'))
# sat = reachable, unsat = not reachable (hallucination!)
```

### Minimal Datalog Vocabulary for 5-Node PoC
| Predicate | Arity | Role |
|---|---|---|
| `Node(n)` | 1 | Declares machine n |
| `Edge(n1, n2)` | 2 | Network link between nodes |
| `Service(n, port, proto)` | 3 | Service running on node |
| `VulnExists(n, cve, port)` | 3 | CVE present on node |
| `FirewallRule(n1, n2, port)` | 3 | Allow/deny traffic |
| `AttackerAccess(n, priv)` | 2 | Attacker's privilege on node |

### The SyNET Approach (Validated Academic Precedent)
SyNET framework reduces network synthesis to: "find inputs to a Datalog program that satisfy constraints via SMT solvers." Key SyNET fact syntax:
```
+SetNode("R1")          → Node("R1")
+SetLink("R1_I1","R2_I1") → Edge("R1","R2")
```
We mirror this approach. LLM generates simple `Node` and `Edge` facts. Complex reasoning (firewall traversal, CVE chaining) is handled by Datalog rules compiled into Z3 — not the LLM.

---

## 4. Local LLM vs. API — The Definitive Answer

### The Verdict: Local + Constrained Decoding (vLLM/Outlines)
| Stack | JSON Guarantee | Logic Quality | Air-Gap | Latency |
|---|---|---|---|---|
| OpenAI/Gemini API | Medium (prompt-based) | Very High | ❌ None | High (network) |
| Local Llama 3.1 8B (raw) | Low (drift-prone) | Moderate | ✅ Absolute | Low |
| **Local + vLLM/Outlines** | **✅ Absolute (logit masking)** | **Moderate** | **✅ Absolute** | **Low** |

### Constrained Decoding — How It Works
`Outlines` / `vLLM guided decoding` operates at the **token logits level**. During inference, it masks out any token that would violate the supplied JSON schema — **before** the token is sampled. The model physically cannot generate invalid JSON.

```python
import outlines
model = outlines.models.transformers("meta-llama/Meta-Llama-3.1-8B-Instruct")

schema = '{"type": "object", "properties": {"nodes": {"type": "array"}, "edges": {"type": "array"}}}'
generator = outlines.generate.json(model, schema)
topology = generator("Create a 3-node network with Log4j on the web server")
# topology is GUARANTEED to be valid JSON matching the schema
```

### Hybrid CEGIS Loop Architecture
- **CEGIS iterations (fast, frequent):** Local Llama 3.1 8B + vLLM/Outlines
- **Stuck fallback (after 5 failed iterations):** Bundle context → single API call to Gemini/GPT-4o → repair → return to local

### Hardware Requirement
- Llama 3.1 8B @ 4-bit quantization = ~4.5GB RAM
- Mistral 7B @ 8-bit = ~7GB RAM
- **16GB laptop is sufficient.** Leaves room for Z3, FastAPI backend, and OS.

---

## 5. Realistic Semester Scope — What "Outstanding" Looks Like

### Knowledge Base: 12 CVEs across 4 Categories (see section 2)

### Topology: 5 Nodes
```
[Attacker] → [Firewall/Router] → [DMZ Web Server (RCE)]
                                       ↓ (lateral movement)
                              [Internal App Server]
                                       ↓ (privilege escalation)
                              [Secure Database (flag)]
```

### Demo Interface: Dual-Interface Approach
1. **Backend CLI (Core):**
   Color-coded pipeline stages:
   - `[LLM]` → generating topology
   - `[DATALOG]` → translating to predicates
   - `[Z3]` → verifying attack path
   - `[UNSAT]` → extracting core + healing
   - `[COMPILE]` → writing SecGen XML
   - `[SUCCESS]` → scenario ready

2. **Streamlit/Jupyter Dashboard (Visual):**
   - NetworkX / Pyvis graph visualization
   - Attack path highlighted in RED
   - Compromised nodes turn RED, secure nodes GREEN
   - CEGIS iteration counter visible

### The "Wow" Demo Moment for Ravi Sir
1. Komal types: *"Build me a 5-machine network teaching lateral movement via Log4j"*
2. LLM generates topology (with a deliberate firewall misconfiguration)
3. CLI shows: `[Z3 UNSAT] FirewallRule missing: Attacker→WebServer:8080`
4. LLM auto-repairs
5. CLI shows: `[Z3 SAT] Attack path verified. 3 nodes compromised.`
6. `compiled_scenario.xml` is written
7. `ruby secgen.rb run` provisions the VMs
8. Ravi Sir watches the Kali machine actually exploit the Log4j box in real-time
