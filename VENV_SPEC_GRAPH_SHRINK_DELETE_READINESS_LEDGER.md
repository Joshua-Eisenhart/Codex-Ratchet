# .venv_spec_graph Shrink/Delete Readiness Ledger

Date: 2026-04-04
Produced by: Claude Code (Terminal D, wave 5)
Canonical interpreter: `/opt/homebrew/bin/python3`
Sources: `VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md`, `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`,
         tier-1 migration reviews (claude-tier1-interpreter-migration-packets, claude-tier1-packet-launcher-review-or-finish)

---

## Purpose

This ledger records where each `.venv_spec_graph` reference stands today and what is
required before the directory itself can be safely deleted. No files are moved or deleted
by this document.

---

## Category 1 — Already Replaced

These references originally pointed to `.venv_spec_graph` but are now pointing to the
canonical interpreter or are dead code with no live execution path. The directory being
absent would not break these.

| File | Line | What changed |
|---|---|---|
| `system_v4/skills/qit_graph_stack_runtime.py` | 71 | `PREFERRED_INTERPRETER` now set to `Path("/opt/homebrew/bin/python3")` — explicit comment confirms packages confirmed available; no `.venv_spec_graph` reference remains |
| `system_v4/probes/run_formal_geometry_packet.py` | 33, 37–38 | `SPEC_GRAPH_PYTHON` still constructed as a `Path` object but annotated `# legacy; no step requires this now`; all steps have `require_spec_graph=False`, so `choose_python()` never returns the spec-graph path; dead code |
| `system_v4/probes/run_root_emergence_packet.py` | 22, 26–27 | Same dead-code pattern; all steps migrated to `require_spec_graph=False` |

**Safe to delete `.venv_spec_graph` given only these?** Not yet — see Category 2.

---

## Category 2 — Live Dependency Still Blocking Deletion

These files still contain `PREFERRED_INTERPRETER = ".venv_spec_graph/bin/python"` as a
string that is used at runtime to construct a path and spawn a subprocess. If
`.venv_spec_graph` is deleted, these will fail silently (path construction succeeds but
the interpreter binary will not exist).

| File | Line | Runtime use | Packages needed | Available under canonical? |
|---|---|---|---|---|
| `system_v4/skills/nested_graph_builder.py` | 93 | `root / PREFERRED_INTERPRETER` → subprocess spawn | `clifford`, `kingdon` | **Yes** (both confirmed in tool status doc) |
| `system_v4/skills/clifford_edge_semantics_audit.py` | 29, 100 | Same pattern | `clifford` | **Yes** |
| `system_v4/skills/toponetx_projection_adapter_audit.py` | 27 | Same pattern | `toponetx` | **Yes** |
| `system_v4/skills/pyg_heterograph_projection_audit.py` | 31 | Same pattern | `torch_geometric` | **Yes** |

**Migration readiness:** All four have their required packages available under
`/opt/homebrew/bin/python3`. No `cvc5`/`quimb`/`qutip`/`ripser` dependency.
These are the only remaining hard blockers for deletion.
Wave-5 handoff `claude__venvsg_tier2_skill_batch_audit.md` is the designated next step.

---

## Category 3 — Stale Instruction Only

These references exist in comments, `print()` strings, or dead-code constants. They are
not execution paths. Deleting `.venv_spec_graph` would not cause runtime failures here,
but the instructions would be misleading to anyone reading them.

| File | Location | Nature |
|---|---|---|
| `system_v4/probes/run_formal_geometry_packet.py` | Line 33 | `SPEC_GRAPH_PYTHON` dead-code constant (commented as legacy) |
| `system_v4/probes/run_root_emergence_packet.py` | Line 22 | Same |
| `system_v4/probes/sim_nonclassical_guard_probe.py` | Lines 1–2 | `# REQUIRES:` / `# Run as:` advisory comments pointing to `.venv_spec_graph` |
| `system_v4/probes/sim_edge_state_writeback.py` | Lines 1–2 | Same pattern |
| `system_v4/probes/sim_geometry_truth.py` | Lines 1–2 | Same pattern |
| `system_v4/probes/sim_axis_7_12_audit.py` | Line 43 | `.venv_spec_graph` inside a `print()` string — informational only |

Wave-5 handoff `claude__venvsg_stale_run_instruction_cleanup.md` covers these.

---

## Category 4 — Historical / Provenance Only

These files recorded past runs, audit states, or prompt context under the old environment.
They must not be patched — they are frozen provenance records. Deleting `.venv_spec_graph`
would not affect these files or their correctness.

| Location | Count | Nature |
|---|---|---|
| `system_v4/a2_state/audit_logs/` | ~12 files | Run results, solver reports, phase audit logs — references record what was used at time of run |
| `system_v4/a2_state/antigravity_prompt_batches/safe_pack/` | 4 files | Task/prompt/result docs — historical thread context |
| `system_v4/probes/a2_state/sim_results/formal_geometry_packet_run_results.json` | 1 file | Records the interpreter used in a past formal geometry packet run |

Do not patch any of these.

---

## Category 5 — Safe to Ignore Until Final Delete Pass

These references should remain as-is even after `.venv_spec_graph` is deleted. They are
correct defensive code that excludes the venv from graph ingestion — the exclusion should
stay regardless of whether the directory exists.

| File | Line | Nature |
|---|---|---|
| `system_v4/skills/graph_intake/multi_repo_ingestor.py` | 110 | Exclusion filter — correctly prevents venv from being ingested; must remain |
| `system_v4/a2_state/graphs/full_stack_ingestion_manifest.json` | exclusion entry | Same — correct behavior |

---

## Deletion Gate — What Makes `.venv_spec_graph` Safe to Delete

All of the following must be true before the directory is removed:

1. **Category 2 cleared** — The four tier-2 skills (`nested_graph_builder.py`,
   `clifford_edge_semantics_audit.py`, `toponetx_projection_adapter_audit.py`,
   `pyg_heterograph_projection_audit.py`) must have `PREFERRED_INTERPRETER` migrated to
   the canonical interpreter. Their packages are already available; this is a bounded text
   patch, not a dependency acquisition problem.

2. **Tier-1 dead code cleaned** (optional but clean) — `SPEC_GRAPH_PYTHON` constant and
   `choose_python()` removed from both launchers. Not a hard gate — deletion is safe even
   with these present since the path is never called — but removes confusion.

3. **No undiscovered live execution paths** — A final repo-wide grep for
   `.venv_spec_graph` paths in executable context (not comments, not JSON values) should
   return zero results outside of the exclusion filters. The current audit did not fully
   cover `system_v3`, `system_v5`, or `core_docs`.

4. **Hermes sign-off** — Confirm no external script, shell alias, or launchd plist still
   activates `.venv_spec_graph` by path.

**Minimum required for safe deletion:** Item 1 only. Items 2–4 are confirmatory.

---

## Summary

| Category | Count of surfaces | Blocks deletion? |
|---|---|---|
| Already replaced | 3 files | No |
| Live dependency — blocking | 4 files | **Yes** |
| Stale instruction only | 6 locations | No (misleading but not breaking) |
| Historical/provenance | ~17 files | No (must not be patched) |
| Safe to ignore indefinitely | 2 files | No |

**Single remaining hard blocker:** Tier-2 skill batch migration (wave-5
`claude__venvsg_tier2_skill_batch_audit.md` → `claude__venvsg_tier1_runtime_migration.md`
covers this).

---

## Confidence Bound

This ledger is grounded in:
- `VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md` (full tiered reference list)
- `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md` (package availability)
- Live grep of tier 1/2 files (confirmed current state 2026-04-04)
- Tier-1 migration reviews (confirm launchers migrated)

Not covered: `system_v3/`, `system_v5/`, `core_docs/` — a final pre-deletion grep is
recommended to rule out undiscovered live paths in those areas.
