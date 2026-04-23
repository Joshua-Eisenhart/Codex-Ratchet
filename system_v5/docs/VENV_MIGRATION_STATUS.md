# .venv_spec_graph Migration Status

Date: 2026-04-05
Supersedes: VENV_SPEC_GRAPH_POST_MIGRATION_VALIDATION.md,
            VENV_SPEC_GRAPH_SHRINK_DELETE_READINESS_LEDGER.md,
            VENV_SPEC_GRAPH_REFERENCE_PRIORITY_AUDIT.md,
            VENV_SPEC_GRAPH_TIER2_SKILL_BATCH_READINESS.md

---

## Status: COMPLETE — Deletion-ready pending owner confirmation

All 5 tier-1/tier-2 runtime skills migrated to `/opt/homebrew/bin/python3`.
Zero live runtime blockers remaining.

### Migrated Skills

| File | Line | Status |
|---|---|---|
| qit_graph_stack_runtime.py | 71 | migrated |
| nested_graph_builder.py | 93 | migrated |
| clifford_edge_semantics_audit.py | 29 | migrated |
| toponetx_projection_adapter_audit.py | 27 | migrated |
| pyg_heterograph_projection_audit.py | 31 | migrated |

### Remaining References (non-blocking)

46 files still reference `.venv_spec_graph`:
- ~12 frozen audit logs (JSON/MD run records)
- ~4 Antigravity prompt batches (historical task docs)
- Various planning/tracking docs and readiness ledgers
- Legacy/read-only docs (core_docs/, system_v5/)
- 1 sim result (formal_geometry_packet_run_results.json)

Two dead-code constants exist in:
- run_formal_geometry_packet.py:33
- run_root_emergence_packet.py:22

These are cosmetic, not runtime blockers.

### Deletion Checklist

Before deleting `.venv_spec_graph/` (~1GB):
1. Confirm no shell aliases or .zshrc entries reference it
2. Confirm no launchd plists reference it (heartbeat already fixed)
3. Optionally remove the two dead-code constants
4. Delete the directory
5. Optionally archive the 4 VENV_SPEC_GRAPH planning docs
