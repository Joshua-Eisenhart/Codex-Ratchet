# Expanded Quarantine Inventory Summary - 2026-05-23

Status: cleanup steering summary. This is not scientific evidence.

Machine-readable inventory:

`system_v5/ops/EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json`

## Stable Snapshot Boundary

This inventory was generated after stopping the live Claude Code process and
the standalone Codex CLI process that were rooted in this repo. No staging,
restore, deletion, or sim rerun was performed.

## Current Counts

| Surface | Count |
|---|---:|
| tracked dirty files | 1 |
| untracked scoped files under `system_v5/docs`, `system_v5/ops`, `system_v5/evidence` | 87 |
| untracked formal-scout source files | 0 |
| recent untracked/ignored formal-scout result JSONs after `2026-05-23 04:57` | 0 |
| files newer than `2026-05-23 08:45` under scoped dirs | 96 |
| files newer than `2026-05-23 20:00` under scoped dirs | 28 |
| untracked `system_levels_20260523` files | 18 |
| untracked `clean_rebuild_20260523` files | 17 |
| untracked `constraint_audit_20260523` files | 41 |
| untracked external-audit files | 0 |
| untracked legacy high-entropy intake chunks | 0 |

## Immediate Classification

### Cleanup Already Performed

11 tracked canonical files were restored to `HEAD` after writer processes were
stopped. This removed contaminated tracked edits from readiness/index docs,
evidence JSONs, formal-scout README/classifiers, and the tracked result JSON.

The untracked formal-scout source/result quarantine slice was archived and
removed from the working tree:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-formal-scout-quarantine/formal_scout_quarantine_20260523.tar.gz
```

Archive path list:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-formal-scout-quarantine/formal_scout_quarantine_paths.txt
```

The legacy high-entropy intake chunk archive was also archived and removed:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-legacy-high-entropy-intake/legacy_high_entropy_intake_20260523.tar.gz
```

Archive path list:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-legacy-high-entropy-intake/legacy_high_entropy_intake_paths.txt
```

The untracked external-audit packet slice was archived and removed:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-external-audit-packets/external_audit_packets_20260523.tar.gz
```

Archive path list:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-external-audit-packets/external_audit_untracked_paths.txt
```

The top-level generated ops docs/JSON bucket was archived and removed:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-top-level-generated-ops/top_level_generated_ops_20260523.tar.gz
```

Archive path list:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-top-level-generated-ops/top_level_generated_ops_paths.txt
```

Local `.DS_Store` and `__pycache__` noise under remaining quarantine folders was
also archived outside the repo and removed:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-quarantine-local-noise/
```

The system-level documentation pack now has its receipt anchors quarantined:
machine-readable current-anchor arrays are empty until clean independent reruns
rebuild the cited receipts.

Constraint-audit external transcripts and prompt drafts were archived and
removed, leaving only the core docs, registries, validator, scripts, and local
process-result JSONs:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-constraint-audit-advisory-transcripts/constraint_audit_advisory_transcripts_20260523.tar.gz
```

The only tracked dirty file intentionally left is:

```text
system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md
```

It contains the cross-lane independence rule patch and remains pending review.

### High-Risk Formal Contamination

These were removed from the working tree after archive. They must not be
restored into formal evidence without independent rerun:

- 42 untracked formal-scout `sim_*.py` files;
- 95 untracked/ignored recent formal-scout result JSONs after the first
  contamination cutoff.

### Advisory / Archive-Only Until Reviewed

These may contain useful ideas but are not evidence:

- `system_v5/ops/clean_rebuild_20260523/`;
- `system_v5/ops/constraint_audit_20260523/` core process-control packet;
- `system_v5/docs/system_levels_20260523/`;

The external-audit packets are now archive-only unless manually restored for
inspection.
The top-level synthesis/alignment docs are also archive-only unless manually
restored for inspection.
The system-level docs are reviewable as non-evidence documentation only; their
prior receipt anchors are rerun targets, not live evidence.

### Recovery Docs

These are process-control artifacts, not sim evidence:

- `system_v5/ops/CROSS_LANE_SIM_INDEPENDENCE_RESET_20260523.md`;
- `system_v5/ops/FORMAL_GROK_BOUNDARY_DAMAGE_AUDIT_20260523.md`;
- `system_v5/ops/FORMAL_GROK_BOUNDARY_QUARANTINE_MANIFEST_20260523.json`;
- `system_v5/ops/CLAUDE_SELF_VIOLATION_INVENTORY_20260523.md`;
- `system_v5/ops/FORMAL_GROK_SIM_REDO_PLAN_20260523.md`;
- `system_v5/ops/LIVE_CLAUDE_PROCESS_STOP_AND_EXPANDED_QUARANTINE_20260523.md`;
- this summary and the full inventory JSON.

## Cleanup Rule

No generated path should be kept because it "looks useful." Each path needs one
of these explicit statuses before any commit:

- `discard`;
- `archive_only`;
- `advisory_only`;
- `manual_doc_review`;
- `independent_formal_rerun_candidate`;
- `independent_grok_sim_rerun_candidate`;
- `recovery_control_artifact`.

Until that classification exists, the safe global status is quarantine.

## Next Non-Destructive Step

Create a path-classification table from the JSON inventory with one row per
top-level surface first, not one row per file. Recommended first buckets:

1. recovery-control docs;
2. second-wave clean-rebuild / constraint-audit surfaces;
3. system-level docs;
4. recovery-rule patch review.
