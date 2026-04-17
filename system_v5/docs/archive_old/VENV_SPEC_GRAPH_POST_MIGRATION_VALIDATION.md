# `.venv_spec_graph` Post-Migration Validation

**Date:** 2026-04-04
**Validator:** Claude Code
**Task:** claude-venvsg-post-migration-validation
**Verdict:** ALL RUNTIME BLOCKERS RESOLVED — deletion-ready pending final confirmation

---

## Summary

All tier-1 and tier-2 runtime skills have been migrated to the canonical interpreter (`/opt/homebrew/bin/python3`). Zero `.venv_spec_graph/bin/python` references remain in any active execution path. The venv directory (~1 GB) can be safely deleted once the owner confirms no external shell aliases or launchd plists still reference it.

---

## Migrated (confirmed `/opt/homebrew/bin/python3`)

| File | Line | Evidence |
|------|------|----------|
| `system_v4/skills/qit_graph_stack_runtime.py` | 71 | `PREFERRED_INTERPRETER = Path("/opt/homebrew/bin/python3")` |
| `system_v4/skills/nested_graph_builder.py` | 93 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` |
| `system_v4/skills/clifford_edge_semantics_audit.py` | 29 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` |
| `system_v4/skills/toponetx_projection_adapter_audit.py` | 27 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` |
| `system_v4/skills/pyg_heterograph_projection_audit.py` | 31 | `PREFERRED_INTERPRETER = "/opt/homebrew/bin/python3"` |

**All 5 tier-1 and tier-2 skills: MIGRATED.**

---

## Dead-code constants (not runtime blockers)

| File | Line | Status |
|------|------|--------|
| `system_v4/probes/run_formal_geometry_packet.py` | 33 | Dead constant, commented "legacy; no step requires this now" |
| `system_v4/probes/run_root_emergence_packet.py` | 22 | Dead constant, commented "legacy; no step requires this now" |

These define a `SPEC_GRAPH_PYTHON` variable that is **never used in any execution path**. Not blockers.

---

## Defensive exclusion filters (should remain as-is)

| File | Line | Purpose |
|------|------|---------|
| `system_v4/skills/graph_intake/multi_repo_ingestor.py` | 110 | Excludes `.venv_spec_graph` from ingestion — correct filter |
| `system_v4/a2_state/graphs/full_stack_ingestion_manifest.json` | 22 | Exclusion entry — correct |
| `.gitignore` | — | Excludes `.venv_spec_graph/` — correct |

---

## Historical/provenance records (must NOT be patched)

46 total files reference `.venv_spec_graph`. After removing the categories above, the remainder fall into:

- **Audit logs** (`system_v4/a2_state/audit_logs/`): ~12 frozen JSON/MD run records that captured the interpreter path at execution time
- **Antigravity prompt batches** (`system_v4/a2_state/antigravity_prompt_batches/safe_pack/`): 4 historical task docs
- **Planning/tracking docs** (repo root): `VENV_SPEC_GRAPH_SHRINK_DELETE_READINESS_LEDGER.md`, `VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md`, `VENV_SPEC_GRAPH_TIER2_SKILL_BATCH_READINESS.md`, `CURRENT_TOOL_STATUS__*.md`, etc.
- **Legacy/read-only docs**: `core_docs/`, `READ ONLY Legacy core_docs/`, `system_v5/READ ONLY Reference Docs/`
- **Sim results**: `formal_geometry_packet_run_results.json` (frozen run output)

**None of these are runtime references. All are historical records or documentation.**

---

## Remaining runtime blockers before safe deletion

**None.** All runtime paths now use `/opt/homebrew/bin/python3`.

## Recommended pre-deletion checklist

1. Confirm no external shell aliases, `.zshrc` entries, or launchd plists reference `.venv_spec_graph`
2. Optionally remove the two dead-code constants in the probe launchers (cosmetic, not blocking)
3. Delete `.venv_spec_graph/` directory (~1 GB reclaimed)
4. Optionally archive `VENV_SPEC_GRAPH_*.md` planning docs to a legacy folder
