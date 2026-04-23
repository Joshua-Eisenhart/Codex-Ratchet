---
title: Venv Migration Status
created: 2026-04-07
updated: 2026-04-08
type: summary
tags: [reference, research, system, tooling, status]
sources:
  - raw/articles/new-docs/VENV_MIGRATION_STATUS.md
framing: current
---

# .venv_spec_graph Migration Status

## Overview
Date: 2026-04-05. Supersedes 4 venv-specific planning docs. As of that migration check, the move was assessed as complete, with the old directory considered deletion-ready pending owner confirmation.

## Migrated Skills
All 5 tier-1/tier-2 runtime skills migrated to /opt/homebrew/bin/python3:
- qit_graph_stack_runtime.py (line 71): migrated
- nested_graph_builder.py (line 93): migrated
- clifford_edge_semantics_audit.py (line 29): migrated
- toponetx_projection_adapter_audit.py (line 27): migrated
- pyg_heterograph_projection_audit.py (line 31): migrated

The 2026-04-05 migration check reported no known runtime blockers.

## Remaining References (non-blocking)
46 files still reference .venv_spec_graph:
- ~12 frozen audit logs (JSON/MD run records)
- ~4 Antigravity prompt batches (historical task docs)
- Various planning/tracking docs and readiness ledgers
- Legacy/read-only docs (core_docs/, system_v5/)
- 1 sim result (formal_geometry_packet_run_results.json)

Two dead-code constants in run_formal_geometry_packet.py:33 and run_root_emergence_packet.py:22. Not runtime blockers.

## Deletion Checklist
Before deleting .venv_spec_graph/ (~1GB):
1. Confirm no shell aliases or .zshrc entries reference it
2. Confirm no launchd plists reference it (heartbeat already fixed)
3. Optionally remove the two dead-code constants
4. Delete the directory
5. Optionally archive the 4 VENV_SPEC_GRAPH planning docs

## Related pages
- [[tooling-status]]
- [[python-repo-skills-inventory-and-cleanup-plan]]
- [[current-tool-status-installed-vs-missing-vs-not-wired]]
