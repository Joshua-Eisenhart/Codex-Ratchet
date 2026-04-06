# Current Tool Status — Operational Classification

Status: companion classification document
Purpose: classify the current tool set by operational status (actively used, installed but not wired, wired but broken, missing but justified, installed but later-only) to reduce planning overhead and clarify what is actually available for the pre-Axis sim ladder.

Companion to: `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`
Canonical interpreter assumed: `/opt/homebrew/bin/python3`
Frame: pre-Axis/QIT sim ladder (Tiers 0–6), per `QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md` and `LEGO_SIM_CONTRACT.md`

---

## Classification Method

Each tool is classified by three questions:
1. Is it importable under the canonical interpreter?
2. Is it actually called in a real, currently-executing code path?
3. Is that execution path functional end-to-end?

"Importable" is not sufficient for "actively used." Tools listed as required in the plan are not "active" unless they appear in a real, passing execution path. See non-goal note in the handoff: "do not claim a tool is active just because it imports."

---

## 1. Actively Used Now

Tools that are importable under the canonical interpreter **and** are in a real, currently-functioning execution path.

| Tool | Evidence | Tier relevance |
|------|----------|----------------|
| `pytest` | Direct test runner, no .venv_spec_graph dependency required; test invocations run under canonical interpreter | Cross-tier: test harness |
| `hypothesis` | Used alongside pytest in property-based test surfaces; runs under canonical interpreter | Cross-tier: negative/property testing |
| `pydantic` | Used in runtime schema and data-model layer in active system; no .venv_spec_graph blocking | Cross-tier: runtime contract |
| `jsonschema` | Used in JSON schema validation in active runtime layer; importable and wired without .venv_spec_graph | Cross-tier: artifact validation |
| `networkx` | Used in `multi_repo_ingestor.py` (graph building); that file's .venv_spec_graph reference is an exclusion filter only, not an interpreter dependency | Tier 1–2: graph structure |

Note: `z3` is installed and importable under canonical interpreter but its current repo wiring runs through `.venv_spec_graph`-gated probes (`sim_nonclassical_guard_probe.py`). The planned standalone guard layer (`qit_nonclassical_guards.py`) does not yet appear as a confirmed running artifact. z3 is classified as **installed but not wired** pending that file's confirmation. Reclassify to "actively used" once the guard layer is confirmed running under canonical interpreter.

---

## 2. Installed but Not Wired

Importable under canonical interpreter, but **not** integrated into any currently-executing real code path. These are available to wire but have not been connected.

| Tool | Evidence | Intended role |
|------|----------|---------------|
| `z3` | Importable; probe scripts gate it behind .venv_spec_graph; planned standalone guard layer (`qit_nonclassical_guards.py`) not yet confirmed as running artifact | Proof pressure — Tier 0+ |
| `sympy` | Importable; status doc §7 lists it as "not used as exact pressure in current sims" | Exact symbolic pressure — Tier 0–2 |
| `gudhi` | Importable; no active sim or skill currently calls it under canonical interpreter | Topology pressure — Tier 2 |

---

## 3. Wired but Broken

Referenced in real repo code (skills/probes), but the execution path is broken because the scripts are hardcoded to `.venv_spec_graph` which is a legacy environment not present or not canonical.

| Tool | Evidence surface | Breakage cause |
|------|-----------------|----------------|
| `torch` | `system_v4/skills/qit_graph_stack_runtime.py:71`, `system_v4/skills/nested_graph_builder.py:93` — both hardcode `.venv_spec_graph/bin/python` | Legacy interpreter lock |
| `torch_geometric` (PyG) | Same files as torch; `pyg_heterograph_projection_audit.py:31` also hardcoded | Legacy interpreter lock |
| `clifford` | `system_v4/skills/clifford_edge_semantics_audit.py:29` hardcodes `.venv_spec_graph/bin/python` | Legacy interpreter lock |
| `pyquaternion` | Pulled in via clifford/PyG geometry path; same scripts | Legacy interpreter lock |
| `toponetx` | `system_v4/skills/toponetx_projection_adapter_audit.py:27` hardcodes `.venv_spec_graph/bin/python` | Legacy interpreter lock |

Note: The writeback path (`sim_edge_state_writeback.py`) is explicitly flagged in `SYSTEM_CONTEXT_HANDOFF__CURRENT.md` §11 as a "real code/workflow problem" — further confirming these are wired but broken, not merely unwired.

All five tools are importable under canonical interpreter. The fix path is: re-point the probe/skill scripts to canonical interpreter (or strip the subprocess dependency entirely where the tool is already available under canonical interpreter).

---

## 4. Missing but Justified

Not importable under canonical interpreter, but required or planned-for by the current sim ladder and formal tool plan.

| Tool | Missing status | Justification source |
|------|---------------|---------------------|
| `cvc5` | `ModuleNotFoundError` under canonical interpreter; present only in `.venv_spec_graph` per audit logs | `QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md` §8.1: required for proof pressure alongside z3 |
| `ripser` | `ModuleNotFoundError` under canonical interpreter | `QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md` §8.3: optional but listed for topology pressure at Tier 2; LEGO_SIM_CONTRACT requires topology surfaces |

Note: `quimb` and `qutip` are also missing under canonical interpreter but are not clearly required at current pre-Axis ladder tiers. They are classified in §5 below.

---

## 5. Installed but Later-Only / Not Yet Justified for Current Ladder

Importable under canonical interpreter, but not required at current pre-Axis Tier 0–2 position, and not yet wired into any planned near-term path.

| Tool | Status | Why later |
|------|--------|-----------|
| `kingdon` | Importable; not wired | Optional GA alternative to `clifford`; only relevant once clifford path is unblocked and chirality (Tier 4) is prioritized |
| `hypernetx` | Importable; not wired | Optional hypergraph surface; listed as optional in QIT plan §8.2; not required until richer relational geometry work at Tier 3–4 |
| `xgi` | Importable; not wired | Same as hypernetx; alternative hypergraph library; optional now |
| `quimb` | Not importable | Quantum sim layer; not in plan's current tool requirements for pre-Axis tiers |
| `qutip` | Not importable | Same as quimb; quantum operator/state layer; not required at current tiers |

---

## Uncertainty Notes

- **z3**: Could be reclassified to "actively used" once `qit_nonclassical_guards.py` is confirmed running under canonical interpreter. Current evidence puts it at "installed but not wired."
- **PyG writeback path**: The evidence that the writeback path "reports real failures" (SYSTEM_CONTEXT_HANDOFF §11) confirms broken status, but the exact failure mode was not re-verified in this read pass.
- **pydantic / jsonschema / networkx "actively used"**: Based on structural evidence (no .venv_spec_graph gate in their key invocation paths). Not validated by running a live execution trace.
- **cvc5 in .venv_spec_graph**: The thread prompt bank (`THREAD_PROMPT_BANK__v1.md`) confirms `cvc5 1.3.3` was installed in .venv_spec_graph. It is missing under canonical interpreter.

---

## Cross-Reference

- `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md` — install/import status baseline; §9 defines the five status types this doc operationalizes
- `QIT_ENGINE_PROTO_RATCHET_AND_SIM_PLAN.md` — §8 defines required tools per scientific need tier
- `LEGO_SIM_CONTRACT.md` — §4 defines tool declaration rules; §4.2: "a tool listed as required must appear in the real execution path"
- `SYSTEM_CONTEXT_HANDOFF__CURRENT.md` — §11 confirms writeback path is broken; §7 confirms .venv_spec_graph is a cleanup target
