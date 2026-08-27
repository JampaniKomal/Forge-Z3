# Forge-Z3: Full Codebase Audit, Live Run Analysis & Fix Plan

*Written by Antigravity AI on 2026-08-27 after a full line-by-line audit of every file in the repository.*
*This document captures: what the code does, what was run, exactly why it failed, and what must change to fix it.*

---

## 1. Complete Codebase Understanding

### 1.1 What Forge-Z3 Is

Forge-Z3 is a **Neuro-Symbolic Infrastructure Compiler**. It accepts a natural language description of a hacking scenario (e.g., *"Build a 3-node network where I pivot through a WebServer to hack a Database"*) and automatically:

1. Uses an LLM to generate a structured network topology (Nodes, Edges, Vulnerabilities).
2. Uses the **Z3 SMT Solver** (Microsoft Research) to mathematically prove whether the attack path is physically and logically possible.
3. If the LLM hallucinates an impossible topology, the system self-corrects in a loop (CEGIS).
4. Once verified, compiles the topology into real Infrastructure-as-Code: a `Vagrantfile` and Ansible playbooks.
5. Renders an interactive 3D HTML network graph.

The core innovation is the **CEGIS (Counterexample-Guided Inductive Synthesis)** loop — pitting a probabilistic neural network against a deterministic theorem prover.

---

### 1.2 Complete File-By-File Breakdown

#### Root Files

| File | Purpose |
|------|---------|
| `README.md` | Main documentation, usage, execution modes |
| `requirements.txt` | Python deps: z3-solver, pydantic, litellm, rich, pyvis, pytest, bandit, ruff |
| `pyproject.toml` | Build config, Ruff linting rules, pytest config (pythonpath=["."] to avoid __init__.py) |
| `.env.example` | Template for API keys (GEMINI_API_KEY, GROQ_API_KEY) |
| `.gitignore` | Ignores venv/, build/, .env (confirmed: .env IS properly ignored) |
| `ROADMAP.md` | 428-line, 8-phase action plan generated from a prior codebase audit |
| `CONTRIBUTING.md` | Contributor guidelines |
| `CODE_OF_CONDUCT.md` | Community standards |
| `SECURITY.md` | Security vulnerability disclosure policy |
| `LICENSE` | MIT License |

---

#### `src/main.py` — CLI Entry Point

- Uses `argparse` to accept:
  - `prompt` (positional): natural language scenario description
  - `--model`: LiteLLM model string, **defaults to `"gemini/gemini-flash-latest"`**
  - `--target`: target node ID, **defaults to `2`** ← **BUG: breaks all 2-node networks**
- Calls `CEGISLoop.synthesize()` → `IaCCompiler.compile()` → `TopologyVisualizer.generate_html()`
- Uses `rich` library for pretty terminal output

---

#### `src/generator/llm_client.py` — LLM Neural Layer

- **`LLMGenerator.__init__`**: Stores the model name, generates `Topology.model_json_schema()`, and builds `self.cve_db` (list of CVE IDs from the knowledge base).
- **`LLMGenerator.upgrade_prompt(basic_prompt)`** (Tier 1):
  - Sends a system prompt telling the LLM to act as a "Cyber Range Architect."
  - The system prompt includes the list of available CVE IDs so Tier 1 can reference valid ones.
  - Returns a plain-text explicit mapping (Nodes, Edges, Vulnerabilities) — NOT JSON yet.
- **`LLMGenerator.generate_topology(user_prompt, previous_failures)`** (Tier 2):
  - Takes the upgraded Tier 1 output and converts it to strict JSON.
  - **BUG: The Tier 2 system prompt does NOT include the list of valid CVE IDs.** The LLM can hallucinate fake CVE strings.
  - Uses `response_format={"type": "json_object"}` to force JSON mode.
  - Strips markdown code fences if the LLM hallucinates them despite instructions.
  - Validates against the `Topology` Pydantic model.
  - **BUG: `import os` on line 95 is dead code inside `generate_topology()`. Not used anywhere.**
  - When `previous_failures` exist, appends a correction prompt — but only sends the error string, NOT the failed JSON topology itself.

---

#### `src/generator/cegis.py` — CEGIS Self-Healing Loop

- **`CEGISLoop.__init__`**: Creates an `LLMGenerator` and stores `max_iterations` (default: 5).
- **`CEGISLoop.synthesize(user_prompt, target_node_id)`**:
  1. Runs Tier 1: `upgrade_prompt()` — generates architectural plan.
  2. For up to `max_iterations`:
     - Runs Tier 2: `generate_topology()` — generates JSON.
     - Creates `Z3Engine` and calls `verify_attack_path(target_node_id)`.
     - If `SAT` → returns the topology. ✅
     - If `UNSAT` → **appends a GENERIC error string** to `previous_failures`. ❌
  3. If all iterations exhausted → raises `RuntimeError`.
- **BUG (Comment numbering):** Lines 41 and 46 both say `# 2.` (should be Step 1 and Step 2).
- **BUG (Auto-target):** `target_node_id` is always passed from CLI default of `2`. A 2-node network only has node IDs 0 and 1 — querying node 2 always returns UNSAT.
- **BUG (CEGIS feedback quality):** The `failure_msg` sent to the LLM is always the exact same generic string. The LLM receives zero specific information about what was wrong.
- **BUG (No topology in feedback):** The LLM doesn't receive its own previous failed JSON, so it's "flying blind" on retry.

---

#### `src/z3_engine/schema.py` — Topology Data Models

Defines the Pydantic models the LLM must output:
- **`Node`**: `node_id: int`, `name: str`. *Node 0 must always be the Attacker* (by convention, not enforced).
- **`Edge`**: `source_id: int`, `target_id: int`, `port: int`. No validation that source/target IDs exist in the nodes list.
- **`VulnerabilityInstance`**: `node_id: int`, `cve_id: str`. No validation that `cve_id` is in the knowledge base.
- **`Topology`**: `nodes: list[Node]`, `edges: list[Edge]`, `vulnerabilities: list[VulnerabilityInstance]`. No cross-field validators at all.

---

#### `src/z3_engine/engine.py` — Z3 Mathematical Verification Core

This is the intellectual heart of the project. It uses Z3's `Fixedpoint` (Datalog) engine.

**Sorts (data types in Z3):**
- `NodeSort`: 4-bit BitVec → up to 16 nodes
- `PrivSort`: 3-bit BitVec → up to 8 privilege levels
- `PortSort`: 16-bit BitVec → up to 65535 ports
- `CveSort`: 8-bit BitVec → up to 256 CVEs

**Relations (Datalog predicates):**
- `NetworkEdge(node1, node2, port)` → is there a network connection?
- `RunsCVE(node, cve_int)` → does this node run this vulnerability?
- `Reaches(node1, node2, port)` → can node1 reach node2 on this port?
- `State(node, privilege)` → what privilege level does the attacker have on this node?

**The 3 Datalog Rules (`_build_rules`):**

1. **Reachability**: `Reaches(n1, n2, port) :- State(n1, ROOT/USER), NetworkEdge(n1, n2, port)`
   - You can only move to another node if you have USER or ROOT on the source AND a physical edge exists.

2. **CVE Exploitation** (generated dynamically from the CVE database):
   - **RCE-type**: `State(n2, post_priv) :- Reaches(n1, n2, target_port), RunsCVE(n2, cve)`
     - If you can reach node n2 on the right port AND n2 runs the CVE, you gain privilege.
   - **Local Escalation-type**: `State(n2, post_priv) :- State(n2, pre_priv), RunsCVE(n2, cve)`
     - If you already have some privilege on n2 AND it runs a local exploit, you escalate.

3. **Privilege Inheritance**: `State(n1, USER) :- State(n1, ROOT)`
   - Having ROOT implies having USER. (For the Reachability rule to work both ways.)

**`_assert_facts`**: Injects the topology into Z3:
- Attacker (Node 0) starts with `State(0, ROOT)`.
- Asserts all `NetworkEdge` facts from `topology.edges`.
- Asserts all `RunsCVE` facts from `topology.vulnerabilities` — **silently skips unknown CVE IDs** (no error raised).

**`verify_attack_path(target_node_id)`**: Queries `State(target_node_id, ROOT)`. Returns `True` if SAT, `False` if UNSAT.

---

#### `src/knowledge_base/schema.py` — CVE Data Models

- **`PrivilegeLevel`** (Enum): `NONE`, `NETWORK_ACCESS`, `USER`, `ROOT`
- **`ExploitType`** (Enum): `RCE`, `PRIVILEGE_ESCALATION`, `INFO_DISCLOSURE`, `AUTHENTICATION_BYPASS`
- **`CVEDefinition`**: `cve_id`, `description`, `software_target`, `port` (0-65535), `exploit_type`, `pre_privilege`, `post_privilege`
  - Validator: `pre_privilege` cannot be `ROOT`.
  - Validator: RCE/PrivEsc must actually escalate (`pre != post`).
- **`KnowledgeBase`**: `list[CVEDefinition]` with uniqueness check on CVE IDs.

---

#### `src/knowledge_base/physics.py` — Knowledge Base Loader

- `load_knowledge_base()`: Loads and Pydantic-validates `cve_database.json`.
- `get_cve_map()`: Returns `dict[cve_id → CVEDefinition]` for easy lookup.

---

#### `src/knowledge_base/cve_database.json` — The 12 Known CVEs

| CVE ID | Description | Port | Pre → Post |
|--------|-------------|------|------------|
| CVE-2021-44228 | Log4Shell (Apache Tomcat) | 8080 | NETWORK_ACCESS → ROOT |
| CVE-2017-5638 | Apache Struts 2 RCE | 8080 | NETWORK_ACCESS → USER |
| CVE-2019-19781 | Citrix ADC RCE | 443 | NETWORK_ACCESS → ROOT |
| CVE-2021-26855 | ProxyLogon (Exchange) | 443 | NETWORK_ACCESS → ROOT |
| CVE-2021-3156 | Baron Samedit (sudo) | 0 | USER → ROOT |
| CVE-2021-4034 | PwnKit (polkit) | 0 | USER → ROOT |
| CVE-2016-5195 | Dirty COW (Linux kernel) | 0 | USER → ROOT |
| CVE-2017-0144 | EternalBlue (SMBv1) | 445 | NETWORK_ACCESS → ROOT |
| CVE-2020-1472 | ZeroLogon (Netlogon) | 135 | NETWORK_ACCESS → ROOT |
| CVE-2014-0160 | Heartbleed (OpenSSL) | 443 | NETWORK_ACCESS → USER |
| CVE-2019-0708 | BlueKeep (RDP) | 3389 | NETWORK_ACCESS → ROOT |
| WEAK_SSH_CREDS | SSH brute force | 22 | NETWORK_ACCESS → USER |

---

#### `src/compiler/generator.py` — IaC Compiler

Generates 3 files in the `build/` directory:

- **`Vagrantfile`**: Multi-machine Vagrant config using `ubuntu/focal64`. IP assignment is `192.168.56.{100 + node_id}`. Node 0 (Attacker) is skipped.
- **`inventory.ini`**: Ansible inventory grouping each node by its name (e.g., `[web_server]`).
- **`site.yml`**: Ansible playbook. Maps CVEs to Ansible roles by name: `CVE-2021-44228` → role `cve_2021_44228`. **BUG (Roadmap D4):** The only existing Ansible role is named `log4shell`, not `cve_2021_44228`. This mismatch means `ansible-playbook site.yml` would fail with "role not found."

---

#### `src/visualization/graph.py` — Interactive Graph Renderer

Uses `pyvis` to generate `build/topology.html`:
- **Attacker node (0)**: Neon red (`#ff003c`), dot shape, glow shadow.
- **Target nodes**: Neon cyan (`#00f0ff`), hexagon shape if has CVEs, dot otherwise.
- **Edges**: Shows port number as label and tooltip.
- **Physics**: Barnes-Hut gravity simulation for organic layout.
- Dark cyberpunk theme (`bgcolor="#050510"`).

---

#### `src/z3_hello_world.py` — Phase 0 Verification Script

A standalone Z3 sanity-check script (not part of the main pipeline). Tests:
1. Simple `Attacker→WebServer→Database` reachability (should be SAT).
2. Same network without the WebServer→Database edge (should be UNSAT).
Uses simpler `Edge/Reachable` predicates without privilege levels. Lives in `src/` but belongs in `examples/` (Roadmap E3).

---

#### `tests/` — Pytest Suite (6 files)

| File | What it tests |
|------|--------------|
| `test_z3_hello_world.py` | The Phase 0 sanity check script runs correctly |
| `test_z3_engine.py` | 3 tests: valid multi-hop SAT, missing edge UNSAT, missing privilege UNSAT |
| `test_knowledge_base.py` | CVE database loads (12 CVEs), Pydantic validators reject invalid CVEs |
| `test_cegis.py` | CEGIS returns topology on SAT (mocked LLM), raises RuntimeError when exhausted |
| `test_compiler.py` | Generated files exist and contain correct Vagrant/Ansible content |
| `test_visualizer.py` | HTML file is generated and contains node/CVE text |

---

#### `ansible/roles/log4shell/tasks/main.yml` — The Only Ansible Role

A stub placeholder. Just prints a debug message. Not functional for real provisioning.

---

#### `lib/` — Vendored JavaScript

Contains PyVis's bundled frontend libraries: `vis-9.1.2/`, `tom-select/`, `bindings/`. These are auto-generated by PyVis when it writes the HTML file. Should be in `.gitignore`.

---

## 2. Live Run Analysis — What Happened and Exactly Why

### 2.1 Command Run
```bash
.\venv\Scripts\python -m src.main "Build me a 3-node network where I pivot through an external WebServer to hack an internal Database." --model ollama/llama3:8b
```

### 2.2 What the LLM Generated (all 5 iterations, same result)

```json
{
  "nodes": [
    {"node_id": 0, "name": "Attacker"},
    {"node_id": 1, "name": "External WebServer"},
    {"node_id": 2, "name": "Internal Database"}
  ],
  "edges": [
    {"source_id": 0, "target_id": 1, "port": 80},
    {"source_id": 1, "target_id": 2, "port": 22}
  ],
  "vulnerabilities": [
    {"node_id": 1, "cve_id": "WEAK_SSH_CREDS"}
  ]
}
```

### 2.3 Why Z3 Returned UNSAT — Step-by-Step Trace

**Facts asserted into Z3:**
```
State(0, ROOT)                     ← Attacker always starts with ROOT
NetworkEdge(0→1, port=80)          ← Attacker to WebServer
NetworkEdge(1→2, port=22)          ← WebServer to Database
RunsCVE(1, WEAK_SSH_CREDS_INT)     ← WebServer runs WEAK_SSH_CREDS
```

**Reachability check — Attacker to WebServer:**
```
State(0, ROOT) ✅ + NetworkEdge(0→1, 80) ✅ → Reaches(0, 1, port=80) ✅
```

**Exploitation check — Can Attacker compromise WebServer?**
`WEAK_SSH_CREDS` requires `port=22` (from cve_database.json).
The Datalog rule fires only if `Reaches(0, 1, port=22)` exists.
We only have `Reaches(0, 1, port=80)`. **Port mismatch. Rule does not fire.**
```
State(1, USER) ← NEVER DERIVED  ❌
```

**Pivot check — Can WebServer reach Database?**
Reachability rule requires `State(1, ROOT) or State(1, USER)`.
Since Node 1 was never compromised: **`Reaches(1, 2, 22)` never fires.** ❌

**Final query:**
```
State(2, ROOT) ← NEVER DERIVED → Z3 returns UNSAT ❌
```

### 2.4 Root Cause of the Failure

The LLM placed `WEAK_SSH_CREDS` (requires port 22) on the WebServer (Node 1), but the Attacker connects to the WebServer on **port 80**. The port mismatch means the CVE can never be triggered.

A correct topology would have been:
```json
{
  "edges": [
    {"source_id": 0, "target_id": 1, "port": 8080},  ← match Log4Shell's port
    {"source_id": 1, "target_id": 2, "port": 22}
  ],
  "vulnerabilities": [
    {"node_id": 1, "cve_id": "CVE-2021-44228"},       ← Log4Shell on WebServer (port 8080)
    {"node_id": 2, "cve_id": "WEAK_SSH_CREDS"},       ← SSH on Database (port 22)
    {"node_id": 2, "cve_id": "CVE-2016-5195"}         ← DirtyCOW to get ROOT on Database
  ]
}
```

### 2.5 Why the CEGIS Loop Couldn't Self-Correct

On each failed iteration, the LLM was sent this message:
> *"Z3 SMT Solver returned UNSAT. The attacker cannot reach the target or lacks required privileges to execute the CVEs. Please double-check your NetworkEdges and pre_privileges."*

This message is **generic, non-specific, and unhelpful.** The LLM:
- Did not know its port was wrong (80 vs. 22).
- Did not receive its own previous JSON to reference and fix.
- Had no whitelist of valid CVE IDs in Tier 2, so it couldn't match CVEs to ports.
- Kept generating the same broken topology 5 times.

---

## 3. Complete Fix Plan (Confirmed Against Every File)

### Phase A — Critical Bug Fixes

#### A1. Auto-Detect Target Node
**File:** `src/main.py` (line 22) and `src/generator/cegis.py` (line 22)

**Change `main.py`:**
```python
# BEFORE:
parser.add_argument("--target", type=int, default=2, ...)
# AFTER:
parser.add_argument("--target", type=int, default=None, ...)
```

**Change `cegis.py` inside the loop, after topology is generated:**
```python
if target_node_id is None:
    target_node_id = max(n.node_id for n in topology.nodes if n.node_id != 0)
```

---

#### A2. Restore CVE Whitelist to Tier 2 Prompt
**File:** `src/generator/llm_client.py` (lines 27-51)

Add the CVE ID list back into the Tier 2 `system_prompt`:
```python
self.system_prompt = f"""
You are a strict JSON formatter...

VALID CVE IDs — you may ONLY use these exact strings:
{json.dumps(self.cve_db, indent=2)}

CRITICAL RULES:
1. ONLY use CVE IDs from the list above. Any other CVE ID will be silently ignored.
2. Each CVE has a required port — the edge connecting to that node MUST use that port.
...
"""
```

This is critical because Tier 1 already sees the CVE list, but Tier 2 (the JSON formatter) was missing it.

---

#### A3. Remove Dead `import os`
**File:** `src/generator/llm_client.py` (line 95)

Delete the `import os` line inside `generate_topology()`. It serves no purpose.

---

#### A4. Fix Comment Numbering in CEGIS
**File:** `src/generator/cegis.py` (lines 41 and 46)

```python
# BEFORE:
# 2. SYNTHESIS (Neural - Tier 2)
...
# 2. VERIFICATION (Symbolic)

# AFTER:
# Step 1: SYNTHESIS (Neural - Tier 2)
...
# Step 2: VERIFICATION (Symbolic)
```

---

### Phase B — Making the CEGIS Loop Real

#### B1. Generate Specific Failure Diagnostics
**Add new method `_diagnose_failure(topology, target_node_id)` to `src/z3_engine/engine.py`:**

This method analyses the failed topology WITHOUT needing Z3 and produces targeted error messages:

1. **No edge to target:** Check if any edge has `target_id == target_node_id`. If not: *"No edge connects to Node {target_id}. Add an edge from a compromised node."*
2. **Port mismatch:** For each vulnerability on a node, check if any incoming edge uses the CVE's required port. If not: *"CVE-2021-44228 requires port 8080, but the edge to Node 1 uses port 80."*
3. **Missing privilege chain:** If a node only has CVEs that give USER (not ROOT), check if there's also a local PrivEsc CVE. If not: *"Node 2 only reaches USER via WEAK_SSH_CREDS. Add a local privilege escalation CVE (e.g., CVE-2021-3156)."*
4. **Unreachable intermediate node:** In multi-hop chains, check if intermediate nodes have both incoming and outgoing edges.

---

#### B2. Include Failed Topology JSON in Feedback
**File:** `src/generator/cegis.py` (lines 57-62)

```python
# BEFORE:
failure_msg = (
    "Z3 SMT Solver returned UNSAT. The attacker cannot reach the target "
    "or lacks required privileges..."
)

# AFTER:
diagnostic = engine.diagnose_failure(topology, target_node_id)
failure_msg = (
    f"Your previous topology FAILED Z3 verification:\n"
    f"{topology.model_dump_json(indent=2)}\n\n"
    f"Specific failure reason: {diagnostic}\n"
    f"Fix these exact issues in your next attempt."
)
```

---

### Phase C — Code Quality (Lower Priority, Next Session)

- **C1:** Add empty `__init__.py` to all 6 `src/` packages.
- **C2:** Add Pydantic validation to reject unknown CVE IDs before Z3 silently skips them.
- **C3:** Add `model_validator` to `Topology` for referential integrity (edge source/target must exist as node IDs).
- **C4:** Add `model_validator` to ensure Node 0 always exists in the topology.

---

## 4. Expected Behavior After Fixes

With Phase A+B implemented, re-running the same prompt should look like:

```
=== TIER 1: ARCHITECTURAL PLAN ===
[LLM outputs correct mapping with valid CVE IDs]

CEGIS Iteration 1/5
  [OK] LLM generated a schema-compliant topology.
  [FAIL] Z3 FAILED (UNSAT): The attack path is broken.
  Specific failure: CVE-2021-44228 requires port 8080, but the edge to
  Node 1 uses port 80. Change the edge port from 80 to 8080.

CEGIS Iteration 2/5
  [OK] LLM generated a schema-compliant topology.
  [OK] Z3 VERIFIED (SAT): The attack path is mathematically valid!

Compilation Successful!
```

---

## 5. Files NOT Changed (Out of Scope for Current Fix)

- `src/z3_engine/schema.py` — validators planned for Phase C
- `src/knowledge_base/*` — no changes needed
- `src/compiler/generator.py` — Ansible role name mismatch is Phase D
- `src/visualization/graph.py` — working correctly
- `ansible/roles/*` — Phase D (real role implementations)
- `tests/*` — Phase F (new tests to be added after B1 implementation)
- `lib/` — Phase E (repo cleanup)

---

*End of Audit Document. Next action: implement Phase A and Phase B fixes.*
