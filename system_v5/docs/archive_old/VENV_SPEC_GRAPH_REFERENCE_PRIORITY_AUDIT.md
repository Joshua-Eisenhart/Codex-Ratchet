# .venv_spec_graph Reference Priority Audit

Date: 2026-04-03
Produced by: Claude Code (terminal C handoff)
Canonical interpreter assumed: `/opt/homebrew/bin/python3`

---

## Purpose

Classify all known `.venv_spec_graph` references into priority tiers so follow-up migration handoffs can be bounded safely. This is an audit, not a migration pass. No references have been patched.

---

## Tier 1 — Execution-Critical Now

These files contain live interpreter path construction that is actually used at runtime to spawn subprocesses. Migration here unblocks real execution under the canonical interpreter.

| File | Line | Nature |
|---|---|---|
| `system_v4/probes/run_formal_geometry_packet.py` | 33 | `SPEC_GRAPH_PYTHON = ROOT.parent.parent / ".venv_spec_graph" / "bin" / "python3"` — path is used to spawn subprocess |
| `system_v4/probes/run_root_emergence_packet.py` | 22 | Same pattern — `SPEC_GRAPH_PYTHON` is the live launch path for root emergence packet |
| `system_v4/skills/qit_graph_stack_runtime.py` | 71 | `PREFERRED_INTERPRETER = REPO_ROOT / ".venv_spec_graph" / "bin" / "python"` — central runtime skill, absolute path construction |

**Why tier 1:** These construct `Path` objects that get passed to `subprocess`/`Popen` or equivalent. If `.venv_spec_graph` does not exist, these fail at runtime, not just at the comment/doc level. The formal geometry packet and root emergence packet are on the pre-Axis sim ladder.

**Do not patch yet.** Migration requires verifying that the target packages (`cvc5` or equivalent) are available under the canonical interpreter first, or that the call sites can be safely redirected to `sys.executable` / `shutil.which("python3")`.

---

## Tier 2 — Execution-Related, Lower Priority

These files reference `.venv_spec_graph` in ways that affect execution (run instructions, PREFERRED_INTERPRETER strings, exclusion filters) but are either: advisory comments, lower-tier audit skills not on the immediate sim ladder, or correct-behavior exclusion filters.

| File | Line(s) | Nature |
|---|---|---|
| `system_v4/probes/sim_nonclassical_guard_probe.py` | 1–2 | `# REQUIRES:` and `# Run as:` comments — not executable, but misleads anyone following the run instruction |
| `system_v4/probes/sim_edge_state_writeback.py` | 1–2 | Same pattern — already known to emit real failures; run instruction is stale |
| `system_v4/probes/sim_geometry_truth.py` | 1–2 | Same pattern — advisory only |
| `system_v4/probes/sim_axis_7_12_audit.py` | 43 | Embedded in a `print()` string — informational, not execution path |
| `system_v4/skills/nested_graph_builder.py` | 93 | `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"` — active skill, relative path string (not Path object) |
| `system_v4/skills/clifford_edge_semantics_audit.py` | 29 | `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"` — same pattern |
| `system_v4/skills/toponetx_projection_adapter_audit.py` | 27 | `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"` — same pattern |
| `system_v4/skills/pyg_heterograph_projection_audit.py` | 31 | `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"` — same pattern |
| `system_v4/skills/graph_intake/multi_repo_ingestor.py` | 110 | Exclusion filter — correctly ignores `.venv_spec_graph` during ingestion; **this reference is correct and should not be changed** |

**Do not patch yet.** The four `PREFERRED_INTERPRETER` skills can be batched as one follow-up once the canonical interpreter is confirmed stable for their package requirements. The run-instruction comments can be updated at the same time as tier 1 migrations, since they document the same entry points.

---

## Tier 3 — Historical / Reporting Only

These files record past runs, audit states, or thread context under the old environment. They are frozen snapshots; updating them would corrupt the historical record without improving execution.

| File | Nature |
|---|---|
| `system_v4/probes/a2_state/sim_results/formal_geometry_packet_run_results.json` | Run result artifact — records what python was used in a past run |
| `system_v4/a2_state/antigravity_prompt_batches/safe_pack/task_2_sim_audit.md` | Prompt/task doc |
| `system_v4/a2_state/antigravity_prompt_batches/safe_pack/task2_results.md` | Past run result narrative |
| `system_v4/a2_state/antigravity_prompt_batches/safe_pack/task_1_provenance.md` | Prompt doc |
| `system_v4/a2_state/audit_logs/PACKAGE_INVENTORY__v1.md` | Package inventory for the old `.venv_spec_graph` environment |
| `system_v4/a2_state/audit_logs/THREAD_PROMPT_BANK__v1.md` | Multiple `Activate .venv_spec_graph` prompt templates — historical prompt bank |
| `system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.json` | Past stack status snapshot |
| `system_v4/a2_state/audit_logs/QIT_GRAPH_STACK_STATUS__CURRENT__v1.md` | Companion markdown |
| `system_v4/a2_state/audit_logs/PHASE1_TOOL_ADOPTION_FIRST_EXPERIMENTS__v1.json` | Phase 1 experiment log |
| `system_v4/a2_state/audit_logs/PHASE1_TOOL_ADOPTION_AUDIT_REPORT__v1.md` | Phase 1 audit report |
| `system_v4/a2_state/audit_logs/PHASE1_PHASE2_COMBINED_AUDIT__v1.json` | Combined phase audit |
| `system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_PACKET__CURRENT__v1.json` | Audit packet |
| `system_v4/a2_state/audit_logs/CLIFFORD_EDGE_SEMANTICS_AUDIT__CURRENT__v1.json` | Audit result |
| `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_PACKET__CURRENT__v1.json` | Audit packet |
| `system_v4/a2_state/audit_logs/TOPONETX_PROJECTION_ADAPTER_AUDIT__CURRENT__v1.json` | Audit result |
| `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_AUDIT__CURRENT__v1.json` | Audit result |
| `system_v4/a2_state/audit_logs/PYG_HETEROGRAPH_PROJECTION_PACKET__CURRENT__v1.json` | Audit packet |
| `system_v4/a2_state/audit_logs/EGGLOG_V13_WORKING_EXAMPLES__v1.md` | Example doc noting venv context |
| `system_v4/a2_state/audit_logs/MUTMUT_RESULTS__nested_graph_builder__v1.md` | Mutation test results |
| `system_v4/a2_state/audit_logs/CROSS_SOLVER_VERIFICATION_REPORT__v1.md` | Solver verification report |
| `system_v4/a2_state/audit_logs/DVC_SETUP_REPORT__v1.md` | DVC setup report |
| `system_v4/a2_state/graphs/full_stack_ingestion_manifest.json` | Manifest noting `.venv_spec_graph` as excluded dir — correct behavior |

**These should not be patched.** They are provenance records. The `preferred_interpreter` fields in JSON packets are artifact metadata, not live configuration.

---

## Tier 4 — Safe to Defer Indefinitely

The `full_stack_ingestion_manifest.json` exclusion entry and the `multi_repo_ingestor.py` exclusion filter both correctly exclude `.venv_spec_graph` from graph ingestion. These are working correctly and must remain as-is even after the venv is eventually removed (the exclusion filter is defensive code for any hidden venv, not specifically tied to this one still existing).

---

## Ranked Top Follow-Up Set for Future Handoffs

Ordered by: highest execution impact × lowest migration risk

1. **`run_formal_geometry_packet.py:33`** — Tier 1 — migrate `SPEC_GRAPH_PYTHON` to canonical interpreter after confirming package requirements for the formal geometry packet are met under Homebrew Python
2. **`run_root_emergence_packet.py:22`** — Tier 1 — same migration; batch with item 1
3. **`qit_graph_stack_runtime.py:71`** — Tier 1 — central runtime; migrate `PREFERRED_INTERPRETER` after confirming its downstream package requirements
4. **`nested_graph_builder.py:93` + `clifford_edge_semantics_audit.py:29` + `toponetx_projection_adapter_audit.py:27` + `pyg_heterograph_projection_audit.py:31`** — Tier 2 batch — four skills with the same `PREFERRED_INTERPRETER` pattern; migrate as a group after tier 1 is confirmed stable
5. **Run-instruction comments in probes** (`sim_nonclassical_guard_probe.py`, `sim_edge_state_writeback.py`, `sim_geometry_truth.py`, `sim_axis_7_12_audit.py`) — Tier 2 — update to reflect canonical interpreter after tier 1 migrations land

---

## What Must Not Be Patched Yet

- All tier 3 audit logs and result docs — they are historical provenance
- `multi_repo_ingestor.py:110` exclusion filter — it is correct
- `full_stack_ingestion_manifest.json` exclusion entry — it is correct
- Any tier 1 or tier 2 file **before** package availability under the canonical interpreter is confirmed for the specific packages each file's runtime depends on (particularly `cvc5`, which is still missing under Homebrew Python)

---

## Confidence Bound

This audit is bounded to the reference list already embedded in `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`. A broader grep across the full repo may surface additional references not captured here, particularly in `system_v3`, `system_v5`, or `core_docs`. Those surfaces were not ingested per the stop rule.
