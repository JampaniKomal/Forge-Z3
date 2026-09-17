# Forge-Z3: Complete Perfection Roadmap

*Generated from a full line-by-line audit of the entire codebase on 2026-08-26.*
*Every item here is actionable, specific, and has a clear "done" condition.*

---

## Phase A: Critical Bug Fixes

These are bugs in the existing code that will cause failures or incorrect behavior. Fix these first, before anything else.

---

### A1. Auto-Detect Target Node (Eliminate `--target` Flag)

**The Problem:**
`main.py` line 22 defaults `--target` to `2`. For any 2-node network, this silently points Z3 at a nonexistent node, causing guaranteed UNSAT failure. The user has to manually figure out the correct node ID and pass `--target 1`. This is fragile and error-prone.

**The Fix:**
The system should automatically determine the target. The target is the "deepest" node in the attack path -- the last non-attacker node. Two approaches:

**Option 1 (Simple):** After Tier 2 generates the topology, find the highest `node_id` that is not `0`:
```python
# In cegis.py, after topology is generated:
if target_node_id is None:
    target_node_id = max(n.node_id for n in topology.nodes if n.node_id != 0)
```
Change `main.py` to default `--target` to `None` instead of `2`, and pass `None` into `synthesize()`.

**Option 2 (Better):** Have Tier 1's `upgrade_prompt` also output the target node ID as part of its architectural plan. Then parse it out.

**Done Condition:** Running `python -m src.main "Build a 2-node network..." --model ollama/llama3:8b` (without `--target`) succeeds automatically.

---

### A2. Restore CVE Whitelist to Tier 2 Prompt

**The Problem:**
`llm_client.py` lines 27-51 -- the Tier 2 system prompt no longer tells the LLM which CVE IDs are valid. It was removed during the schema hallucination fix. If the LLM invents a CVE ID (e.g., `CVE-2023-99999`), the Z3 engine silently ignores it at `engine.py` line 127: `if vuln.cve_id in self._cve_id_to_int`, and the topology fails verification with no clear error.

**The Fix:**
Add a simple list of valid CVE IDs back into the Tier 2 prompt. Do NOT use the full Pydantic schema dump (that caused the hallucination). Just a plain list:
```python
self.system_prompt = f"""
You are a strict JSON formatter...

VALID CVE IDs (you may ONLY use these):
{json.dumps(self.cve_db)}

CRITICAL RULES:
1. DO NOT output JSON schema definitions...
...
"""
```

**Done Condition:** If the LLM tries to use a CVE not in the database, the system prompt explicitly prevents it.

---

### A3. Remove Dead Code: Stray `import os`

**The Problem:**
`llm_client.py` line 95 has `import os` inside the `generate_topology` method. It is not used anywhere in that method. It is leftover debug code.

**The Fix:** Delete the line.

**Done Condition:** `import os` no longer appears inside `generate_topology`.

---

### A4. Fix Comment Numbering in CEGIS

**The Problem:**
`cegis.py` lines 41 and 46 both say `# 2.`:
```python
# 2. SYNTHESIS (Neural - Tier 2)
...
# 2. VERIFICATION (Symbolic)
```

**The Fix:** Renumber to `# Step 1` and `# Step 2`.

**Done Condition:** Comments are sequentially numbered.

---

## Phase B: Making the CEGIS Loop Real

The CEGIS loop is the intellectual heart of the project. Right now, the feedback mechanism is a stub. This phase makes it genuine.

---

### B1. Generate Specific Failure Diagnostics

**The Problem:**
`cegis.py` lines 57-61 sends the exact same generic error message on every failed iteration:
```python
failure_msg = (
    "Z3 SMT Solver returned UNSAT. The attacker cannot reach the target "
    "or lacks required privileges..."
)
```

The LLM receives no specific information about *what* went wrong. It cannot meaningfully self-correct.

**The Fix:**
Write a diagnostic function that analyzes the failed topology and produces specific, actionable error messages. This function should check:

1. **Missing edge to target:** Does any edge connect to the target node? If not, say: `"No edge connects to Node {target_id}. Add an edge from a compromised node to Node {target_id} on the correct port."`
2. **Wrong port for CVE:** Does the edge port match the CVE's required port? If not, say: `"CVE-2021-44228 requires port 8080, but the edge to Node 1 uses port 443. Change the edge port to 8080."`
3. **Missing privilege chain:** Does the attack path have a complete privilege escalation chain? If a CVE gives USER but no subsequent CVE escalates to ROOT, say: `"Node {id} only reaches USER privilege. Add a local privilege escalation CVE (e.g., CVE-2021-3156) to escalate to ROOT."`
4. **Unreachable intermediate node:** In multi-hop scenarios, is there a node that the attacker cannot reach? Say: `"Node {id} is unreachable from the attacker. Add an edge from a compromised node to Node {id}."`

**Where to put it:**
Create a new method `_diagnose_failure(topology, target_node_id) -> str` in `cegis.py` or in `z3_engine/engine.py`. Call it when Z3 returns UNSAT.

**Done Condition:** On a failed CEGIS iteration, the terminal prints a specific, targeted error message (not the generic one), and this specific message is sent to the LLM for the next iteration.

---

### B2. Include Failed Topology JSON in Feedback

**The Problem:**
When the CEGIS loop feeds failure messages back to the LLM, it does NOT include the actual topology that failed. The LLM has no memory of what it generated. It is flying blind on retry.

**The Fix:**
In `cegis.py`, when appending to `previous_failures`, include the serialized topology:
```python
failure_msg = (
    f"Your previous topology FAILED Z3 verification:\n"
    f"{topology.model_dump_json(indent=2)}\n\n"
    f"Specific failure: {diagnostic_message}\n"
    f"Fix these issues in your next attempt."
)
```

**Done Condition:** The LLM receives both the failed JSON AND the specific reason for failure.

---

## Phase C: Code Quality and Correctness

These are structural improvements that make the codebase robust and professional.

---

**Update (2026-09-17): Phase C is done.** All four items below were
implemented and verified (16/16 tests pass, including 5 new tests added
specifically for the C2-C4 validators in `tests/test_schema_validation.py`).

### C1. Add `__init__.py` to All Source Packages

**The Problem:**
None of the `src/` subdirectories have `__init__.py` files. Python finds them via the `pythonpath` hack in `pyproject.toml`, but this is non-standard and will break if you ever try to package or distribute the project.

**The Fix:**
Create empty `__init__.py` files in:
- `src/__init__.py`
- `src/generator/__init__.py`
- `src/z3_engine/__init__.py`
- `src/knowledge_base/__init__.py`
- `src/compiler/__init__.py`
- `src/visualization/__init__.py`

**Done Condition:** All 6 files exist. Tests still pass.

---

### C2. Add Pydantic Validation for Unknown CVEs

**The Problem:**
If the LLM outputs a CVE ID that is not in the knowledge base, the Z3 engine silently skips it at `engine.py` line 127:
```python
if vuln.cve_id in self._cve_id_to_int:
```
No error, no warning. The vulnerability just disappears.

**The Fix:**
Add a validation step BEFORE passing the topology to Z3. Either:
1. Add a Pydantic validator to the `VulnerabilityInstance` model that checks against the CVE database.
2. Or add a pre-check in `cegis.py` that raises a clear error: `"LLM used unknown CVE: {cve_id}. Valid CVEs are: {list}"`

**Done Condition:** If the LLM invents a fake CVE, the system raises a clear, descriptive error instead of silently failing.

---

### C3. Validate Node ID Consistency

**The Problem:**
There is no validation that `edge.source_id` and `edge.target_id` actually reference existing `node.node_id` values. If the LLM outputs `{"source_id": 5, "target_id": 9}` but only defines nodes 0 and 1, the system will silently pass schema validation (Pydantic only checks types, not referential integrity) and then fail at Z3.

**The Fix:**
Add a Pydantic `model_validator` to the `Topology` class:
```python
@model_validator(mode="after")
def check_referential_integrity(self):
    node_ids = {n.node_id for n in self.nodes}
    for edge in self.edges:
        if edge.source_id not in node_ids:
            raise ValueError(f"Edge references non-existent source node: {edge.source_id}")
        if edge.target_id not in node_ids:
            raise ValueError(f"Edge references non-existent target node: {edge.target_id}")
    for vuln in self.vulnerabilities:
        if vuln.node_id not in node_ids:
            raise ValueError(f"Vulnerability references non-existent node: {vuln.node_id}")
    return self
```

**Done Condition:** `Topology(nodes=[Node(0, "A")], edges=[Edge(0, 5, 80)], ...)` raises a `ValidationError`.

---

### C4. Validate Node 0 Is Always the Attacker

**The Problem:**
The system assumes Node 0 is the attacker everywhere (Z3 engine, compiler, visualizer), but there is no validation enforcing this. If the LLM outputs a topology where Node 0 is named "Database," everything silently breaks.

**The Fix:**
Add a Pydantic validator to `Topology`:
```python
@model_validator(mode="after")
def check_attacker_node(self):
    if not any(n.node_id == 0 for n in self.nodes):
        raise ValueError("Topology must contain Node 0 (the Attacker)")
    return self
```

**Done Condition:** A topology without Node 0 raises a `ValidationError`.

---

## Phase D: Ansible Roles (Making the Output Real)

The compiler generates Ansible playbook files that reference roles, but most of those roles do not exist. This phase creates real, working roles.

---

### D1. Create `weak_ssh_creds` Role (Easiest)

This is the simplest role to implement because it just configures a user with a weak password.

```yaml
# ansible/roles/weak_ssh_creds/tasks/main.yml
---
- name: Create vulnerable SSH user
  user:
    name: admin
    password: "{{ 'admin' | password_hash('sha512') }}"
    shell: /bin/bash
    state: present

- name: Enable password authentication in SSH
  lineinfile:
    path: /etc/ssh/sshd_config
    regexp: "^PasswordAuthentication"
    line: "PasswordAuthentication yes"
  notify: restart sshd
```

**Done Condition:** Running `ansible-playbook site.yml` with this role creates a user `admin:admin` on the target VM.

---

### D2. Make the Log4Shell Role Real

Replace the stub in `ansible/roles/log4shell/tasks/main.yml` with a role that actually installs a vulnerable Log4j version. There are well-documented Docker images for this (e.g., `christophetd/log4shell-vulnerable-app`).

```yaml
---
- name: Install Docker
  apt:
    name: docker.io
    state: present

- name: Pull vulnerable Log4j container
  docker_image:
    name: ghcr.io/christophetd/log4shell-vulnerable-app
    source: pull

- name: Run vulnerable Log4j on port 8080
  docker_container:
    name: log4shell-target
    image: ghcr.io/christophetd/log4shell-vulnerable-app
    ports:
      - "8080:8080"
    state: started
```

**Done Condition:** After provisioning, `curl http://target:8080` returns a response from a Log4j-vulnerable application.

---

### D3. Create Remaining CVE Roles (Stretch Goal)

For each CVE in `cve_database.json`, create at least a skeleton role. Realistic scope: implement `weak_ssh_creds`, `cve_2021_44228` (log4shell), `cve_2021_3156` (Baron Samedit), and `cve_2021_4034` (PwnKit). These four cover SSH brute-force, RCE, and two local privilege escalations -- enough to demonstrate a full multi-hop attack chain.

---

### D4. Fix Role Name Mismatch — DONE (2026-09-17)

**The Problem:**
The compiler generates role names like `cve_2021_44228` (from `generator.py` line 111), but the actual Ansible role directory is named `log4shell`. These do not match. Ansible will fail with "role not found."

**The Fix:** Rename all Ansible role directories to match the generated names (`cve_2021_44228/` instead of `log4shell/`).

**Done Condition:** The role directory name matches exactly what `site.yml` references.

**Verified:** ran a real end-to-end compilation (`ollama/qwen2.5-coder:3b`, Log4Shell
scenario) and confirmed the generated `site.yml` references `cve_2021_44228`, which
now matches `ansible/roles/cve_2021_44228/`. D1-D3 (real provisioning logic for the
CVE roles) remain not started — the role content is still a placeholder `debug`
message, not a working Log4j deployment.

---

## Phase E: Repository Cleanup — DONE (2026-09-17)

---

### E1. Delete Empty Directories

Remove `context/`, `devlog/`, `research/`. They contain nothing and make the repo look unfinished.

**Status:** these directories did not exist in the repo by the time this was checked — already moot.

---

### E2. Handle the `lib/` Directory

The `lib/` directory contains vendored JavaScript files (`vis-9.1.2/`, `tom-select/`, `bindings/`) that PyVis depends on. Either add `lib/` to `.gitignore` if it is auto-generated, or document it in REPOSITORY_MAP.md.

**Status:** confirmed the committed `lib/` contents were byte-identical to PyVis's own
bundled `templates/lib/` assets — i.e. build output from a previous `write_html()` run
from the repo root, not original project code. Removed from git tracking and added
`lib/` to `.gitignore`.

---

### E3. Move `z3_hello_world.py` Out of `src/`

`z3_hello_world.py` is a Phase 0 verification script. It served its purpose. Move it to `examples/` or `scripts/` so it does not clutter the main source tree.

**Status:** moved to `examples/z3_hello_world.py`, `tests/test_z3_hello_world.py` import
updated to match, and the full test suite re-run to confirm nothing broke.

---

### E4. Ensure `.env` Is Not Committed

Verify that `.env` is in `.gitignore`. Currently there is a `.env` file (541 bytes) in the repo root. If it contains API keys, it should NOT be in version control. `.env.example` (which IS safe to commit) already exists.

---

## Phase F: Test Suite Hardening

---

### F1. Add Test for Unknown CVE Handling — DONE (2026-09-17)

After implementing C2 (unknown CVE validation), add a test that verifies a fake CVE is rejected.

**Status:** `tests/test_schema_validation.py::test_topology_rejects_unknown_cve`.

---

### F2. Add Test for Referential Integrity — DONE (2026-09-17)

After implementing C3, add a test that verifies invalid node references in edges are rejected.

**Status:** `tests/test_schema_validation.py::test_topology_rejects_edge_to_unknown_node` and
`test_topology_rejects_vulnerability_on_unknown_node`.

---

### F3. Add Test for Auto-Target Detection

After implementing A1, add a test that verifies `target_node_id=None` auto-detects the correct target.

**Status:** still not covered by an explicit unit test — auto-detection has only been
verified via live runs (see README's Tested Configurations section), not a pytest case.

---

### F4. Add Test for Specific CEGIS Diagnostics

After implementing B1, add a test that verifies the diagnostic function outputs correct, specific error messages for different failure modes.

**Status:** still not covered by an explicit unit test for `diagnose_failure()` itself,
though the diagnostics were observed working correctly in a live run (a real port
mismatch was caught and reported, and the LLM corrected it on the next iteration).

---

## Phase G: Multi-Hop Validation (Requires Lab PC / New Laptop)

---

### G1. Test 3-Node Pivot Scenario on 8B Model

Run the "Standard Pivot" prompt from PROMPTS.md on the local Ollama instance:
```bash
python -m src.main "Build me a 3-node network where I pivot through an external WebServer to hack an internal Database." --model ollama/llama3:8b
```

This is the true stress test for the 2-Tier Architecture.

---

### G2. Test 4-Node Scenario

Push further with the "Multi-Service Lateral Movement" prompt.

---

### G3. Actually Run `vagrant up`

On the new laptop (with VirtualBox and Vagrant installed), run `vagrant up` on the generated build output. This is the ultimate end-to-end validation.

---

## Phase H: Documentation Polish

---

### H1. Update ARCHITECTURE.md

Update to accurately reflect the 2-Tier Architecture, the specific diagnostic feedback, and the actual data flow.

---

### H2. Update README.md

- Remove the `--target` flag from example commands (after A1).
- Add a section about the 2-Tier Architecture.
- Add a "Tested Configurations" section.
- Clarify the Ansible role status.

---

### H3. Update PROMPTS.md

After multi-hop validation, annotate each prompt with its actual test result.

---

## Execution Order

```
Phase A (Critical Bugs)     -->  Do first. 30 minutes.
Phase C (Code Quality)      -->  Do second. 1 hour.
Phase B (CEGIS Loop)        -->  Do third. 2 hours. Biggest intellectual upgrade.
Phase E (Repo Cleanup)      -->  Do fourth. 15 minutes.
Phase F (Tests)             -->  Do fifth, in parallel with B and C. 1 hour.
Phase D (Ansible Roles)     -->  Do sixth. 2-3 hours for 4 real roles.
Phase G (Multi-Hop)         -->  Do seventh. Requires new laptop or lab PC.
Phase H (Docs)              -->  Do last. 1 hour.
```

**Total estimated effort: ~8-10 hours of focused work.**
