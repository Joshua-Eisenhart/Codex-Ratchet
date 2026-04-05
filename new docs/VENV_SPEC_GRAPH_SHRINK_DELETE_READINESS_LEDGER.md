# .venv_spec_graph Shrink/Delete Readiness Ledger

Date: 2026-04-04 (refreshed)
Produced by: Claude Code (Terminal D, wave 5) — refreshed by Claude Code (wave 6)
Canonical interpreter: `/opt/homebrew/bin/python3`
Sources: `VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md`, `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md`,
         tier-1/tier-2 migration reviews, `VENV_SPEC_GRAPH_POST_MIGRATION_VALIDATION.md`,
         live grep of all system_v3/v4/v5/core_docs (2026-04-04 refresh)

---

## Purpose

This ledger records where each `.venv_spec_graph` reference stands today and what is
required before the directory itself can be safely deleted. No files are moved or deleted
by this document.

---

## Category 1 — Already Replaced (runtime migration complete)

These references originally pointed to `.venv_spec_graph` but are now pointing to the
canonical interpreter. The directory being absent would not break these.

| File | Line | What changed |
|---|---|---|
| `system_v4/skills/qit_graph_stack_runtime.py` | 71 | `PREFERRED_INTERPRETER = Path("/opt/homebrew/bin/python3")` — confirmed |
| `system_v4/skills/nested_graph_builder.py` | 93 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` — **migrated since last ledger** |
| `system_v4/skills/clifford_edge_semantics_audit.py` | 29 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` — **migrated since last ledger** |
| `system_v4/skills/toponetx_projection_adapter_audit.py` | 27 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` — **migrated since last ledger** |
| `system_v4/skills/pyg_heterograph_projection_audit.py` | 31 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` — **migrated since last ledger** |
| `system_v4/probes/run_formal_geometry_packet.py` | 33, 37–38 | `SPEC_GRAPH_PYTHON` dead-code constant; all steps `require_spec_graph=False`, so never called |
| `system_v4/probes/run_root_emergence_packet.py` | 22, 26–27 | Same dead-code pattern; never called |

**All 5 tier-1/tier-2 skills and 2 launchers: MIGRATED. Zero live runtime blockers.**

---

## Category 2 — Live Dependency Still Blocking Deletion

**CLEARED.** The four tier-2 skills that were previously blocking
(`nested_graph_builder.py`, `clifford_edge_semantics_audit.py`,
`toponetx_projection_adapter_audit.py`, `pyg_heterograph_projection_audit.py`) have all
been migrated to `/opt/homebrew/bin/python3`. Confirmed by grep 2026-04-04.

**No remaining runtime blockers.**

---

## Category 3 — Stale Instruction Only

These references exist in comments, `print()` strings, or dead-code constants. They are
not execution paths. Deleting `.venv_spec_graph` would not cause runtime failures here,
but the instructions would be misleading to anyone reading them.

| File | Location | Nature | Status |
|---|---|---|---|
| `system_v4/probes/run_formal_geometry_packet.py` | Line 33 | `SPEC_GRAPH_PYTHON` dead-code constant (commented as legacy) | Still present |
| `system_v4/probes/run_root_emergence_packet.py` | Line 22 | Same | Still present |
| `system_v4/probes/sim_nonclassical_guard_probe.py` | Lines 1–2 | Was `# REQUIRES:` advisory comment | **CLEANED** — no longer present |
| `system_v4/probes/sim_edge_state_writeback.py` | Lines 1–2 | Was advisory comment | **CLEANED** — no longer present |
| `system_v4/probes/sim_geometry_truth.py` | Lines 1–2 | Was advisory comment | **CLEANED** — no longer present |
| `system_v4/probes/sim_axis_7_12_audit.py` | Line 43 | Was `.venv_spec_graph` in `print()` string | **CLEANED** — no longer present |
| `core_docs/QIT_GRAPH_SIDECAR_POLICY.md` | Line 91 | Policy doc says "check for `.venv_spec_graph/bin/python`" — now stale | **NEW** — discovered this refresh |

**Remaining stale refs: 3 locations** (down from 6).

---

## Category 4 — Historical / Provenance Only

These files recorded past runs, audit states, or prompt context under the old environment.
They must not be patched — they are frozen provenance records. Deleting `.venv_spec_graph`
would not affect these files or their correctness.

| Location | Count | Nature |
|---|---|---|
| `system_v4/a2_state/audit_logs/` | ~12 files | Run results, solver reports — records what was used at time of run |
| `system_v4/a2_state/antigravity_prompt_batches/safe_pack/` | 4 files | Historical task/prompt/result docs |
| `system_v4/probes/a2_state/sim_results/formal_geometry_packet_run_results.json` | 1 file | Records interpreter used in past run |
| `system_v3/a2_state/A2_UPDATE_NOTE__*.md` | 3 files | Historical update notes with past `.venv_spec_graph` commands |
| `core_docs/legacy_docs/SKILL_SOURCE_CORPUS.md` | 1 file | Legacy corpus listing `.venv_spec_graph` as toolchain env |
| `core_docs/legacy_docs/LOCAL_SOURCE_REPO_INVENTORY.md` | 1 file | Legacy inventory entry |
| `core_docs/legacy_docs/REPO_SKILL_INTEGRATION_TRACKER.md` | 1 file | Historical integration note |
| `system_v5/READ ONLY Reference Docs/` (Older Legacy) | 2 files | Frozen reference copies of SKILL_SOURCE_CORPUS.md and system tools doc |

Do not patch any of these.

---

## Category 5 — Safe to Ignore Until Final Delete Pass

These references should remain as-is even after `.venv_spec_graph` is deleted. They are
correct defensive code that excludes the venv from graph ingestion.

| File | Line | Nature |
|---|---|---|
| `system_v4/skills/graph_intake/multi_repo_ingestor.py` | 110 | Exclusion filter — correctly prevents venv from being ingested; must remain |
| `system_v4/a2_state/graphs/full_stack_ingestion_manifest.json` | exclusion entry | Same |
| `.gitignore` | — | Excludes `.venv_spec_graph/` — correct |

---

## Deletion Gate — What Makes `.venv_spec_graph` Safe to Delete

All of the following must be true before the directory is removed:

1. **~~Category 2 cleared~~** ✅ **DONE** — All four tier-2 skills migrated to canonical
   interpreter. Confirmed by grep 2026-04-04.

2. **Tier-1 dead code cleaned** (optional but clean) — `SPEC_GRAPH_PYTHON` constant and
   `choose_python()` still present in both launchers. Not a hard gate — path is never
   called — but removes confusion.

3. **No undiscovered live execution paths** ✅ **DONE** — Full repo-wide grep of
   `system_v3/`, `system_v4/`, `system_v5/`, `core_docs/` completed this refresh. All
   remaining references are provenance records, documentation, or exclusion filters. Zero
   executable `.venv_spec_graph` paths found outside of the dead-code constants.

4. **Hermes sign-off** — Confirm no external script, shell alias, or launchd plist still
   activates `.venv_spec_graph` by path. `heartbeat.sh` and `heartbeat.plist` confirmed
   clean.

**Minimum required for safe deletion: Items 1 and 3 are now satisfied.
Only Item 4 (Hermes confirmation) remains as a procedural gate.**

---

## Summary

| Category | Count of surfaces | Blocks deletion? | Change from prior ledger |
|---|---|---|---|
| Already replaced (runtime migrated) | 7 files | No | +4 (tier-2 batch migrated) |
| Live dependency — blocking | **0 files** | **No** | **Cleared** (was 4) |
| Stale instruction only | 3 locations | No (misleading but not breaking) | -3 cleaned, +1 discovered |
| Historical/provenance | ~25 files | No (must not be patched) | +8 (v3/v5/core_docs now catalogued) |
| Safe to ignore indefinitely | 3 files | No | +1 (.gitignore) |

**No remaining hard blockers. Deletion-ready pending Hermes sign-off (Item 4).**

---

## Confidence Bound

This ledger is grounded in:
- `VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md` (full tiered reference list)
- `VENV_SPEC_GRAPH_POST_MIGRATION_VALIDATION.md` (post-migration confirmation)
- `CURRENT_TOOL_STATUS__INSTALLED_VS_MISSING_VS_NOT_WIRED.md` (package availability)
- Live grep of **all** tier-1/2 files, `system_v3/`, `system_v4/`, `system_v5/`, `core_docs/` (2026-04-04 refresh)
- Tier-1 and tier-2 migration reviews (confirmed all 5 skills migrated)
- `heartbeat.sh` and `heartbeat.plist` confirmed clean

**Full coverage achieved.** The prior "not covered" gap (`system_v3/`, `system_v5/`, `core_docs/`) is now closed.
