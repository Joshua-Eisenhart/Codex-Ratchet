# Expanded Quarantine Action Plan - 2026-05-23

Status: proposed cleanup plan. No cleanup action has been executed by this
document.

Machine-readable action manifest:

`system_v5/ops/EXPANDED_QUARANTINE_ACTION_MANIFEST_20260523.json`

## Precondition

Before any cleanup command:

1. Confirm no live Claude Code or standalone Codex writer process is rooted in
   this repo.
2. Do not run formal scouts, validators, readiness index generation, or external
   audits during cleanup.
3. Do not stage mixed buckets together.

## Buckets

| Bucket | Count | Status |
|---|---:|---|
| recovery-control artifacts | 11 | keep for review |
| tracked restore candidates | 0 | restored to HEAD |
| tracked manual review | 1 | manual review |
| untracked formal-scout source files | 0 | archived and removed |
| recent untracked/ignored formal-scout result JSONs | 0 | archived and removed |
| external audit packets | 0 | archived and removed |
| clean-rebuild second wave | 17 | manual review / independent rerun candidate |
| constraint-audit second wave | 41 | manual review / process-control candidate |
| system-level docs | 18 | manual review; receipt anchors quarantined |
| legacy high-entropy intake | 0 | archived and removed |
| top-level generated ops docs | 0 | archived and removed |

## Safe Order

### Step 1 - Stop Writers

Required before every snapshot or cleanup slice. If a writer respawns, stop and
refresh the inventory before continuing.

### Step 2 - Restore / Isolate Dirty Canonical Files

Done for the contaminated tracked canonical files. 11 tracked files were
restored to `HEAD`, covering readiness indexes, evidence JSON, formal-scout
README, formal classifiers, docs map/manifest, and the tracked result JSON.

Remaining tracked dirty file:

```text
system_v5/docs/MULTIMODEL_PROPOSAL_SPLIT.md
```

This is the recovery boundary-rule patch and remains pending review.

### Step 3 - Keep Or Archive Recovery-Control Packet

Review only these process-control artifacts as a packet:

```text
system_v5/ops/CROSS_LANE_SIM_INDEPENDENCE_RESET_20260523.md
system_v5/ops/FORMAL_GROK_BOUNDARY_DAMAGE_AUDIT_20260523.md
system_v5/ops/FORMAL_GROK_BOUNDARY_QUARANTINE_MANIFEST_20260523.json
system_v5/ops/CLAUDE_SELF_VIOLATION_INVENTORY_20260523.md
system_v5/ops/FORMAL_GROK_SIM_REDO_PLAN_20260523.md
system_v5/ops/LIVE_CLAUDE_PROCESS_STOP_AND_EXPANDED_QUARANTINE_20260523.md
system_v5/ops/EXPANDED_QUARANTINE_FULL_INVENTORY_20260523.json
system_v5/ops/EXPANDED_QUARANTINE_INVENTORY_SUMMARY_20260523.md
system_v5/ops/EXPANDED_QUARANTINE_SURFACE_CLASSIFICATION_20260523.md
system_v5/ops/EXPANDED_QUARANTINE_ACTION_MANIFEST_20260523.json
system_v5/ops/EXPANDED_QUARANTINE_ACTION_PLAN_20260523.md
```

These should never be staged with sim source, result estate, or scientific docs.

### Step 4 - Remove Or Archive Generated Untracked Surfaces

Formal-scout generated source/result estate cleanup has started. The contaminated
formal-scout slice was archived and removed from the working tree:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-formal-scout-quarantine/formal_scout_quarantine_20260523.tar.gz
```

External-audit packets were archived and removed here:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-external-audit-packets/external_audit_packets_20260523.tar.gz
```

Archive path list:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-external-audit-packets/external_audit_untracked_paths.txt
```

Top-level generated ops docs/JSON were archived and removed here:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-top-level-generated-ops/top_level_generated_ops_20260523.tar.gz
```

Archive path list:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-top-level-generated-ops/top_level_generated_ops_paths.txt
```

Local `.DS_Store` and `__pycache__` noise under remaining quarantine folders was
archived and removed here:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-quarantine-local-noise/
```

Remaining untracked generated surfaces remain quarantined for manual review:

- clean-rebuild second wave: independent rerun candidate only;
- constraint-audit second wave: process-control candidate only;
- system-level docs: non-evidence docs candidate only, with current receipt
  anchors emptied pending clean independent reruns.

Constraint-audit external transcripts and prompt drafts were archived and
removed here:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-constraint-audit-advisory-transcripts/constraint_audit_advisory_transcripts_20260523.tar.gz
```

The legacy high-entropy chunks were archived and removed here:

```text
/Users/joshuaeisenhart/Desktop/Codex Ratchet Cleanup Archive/20260523-legacy-high-entropy-intake/legacy_high_entropy_intake_20260523.tar.gz
```

### Step 5 - Independent Rerun

Only after cleanup:

- formal lane reruns from formal source/contracts only;
- informal lane reruns under `system_v5/grok_sim/` only;
- neither lane uses the other's result JSONs, indexes, or conclusions as
  evidence.

## Blocked Actions

Do not:

- `git add .`;
- commit all dirty files together;
- rerun readiness/index generation from the current estate;
- call current classifier outputs evidence;
- use cross-lane agreement as validation;
- run more formal science before cleanup.
