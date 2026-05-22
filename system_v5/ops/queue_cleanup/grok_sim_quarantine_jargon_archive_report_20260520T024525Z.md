# Grok Sim Quarantine Jargon Archive Report

Generated: `2026-05-20T02:45:25Z`

## Moved Items

| Decision | Source path | Destination path | Reason |
|---|---|---|---|
| `MOVE_TO_ARCHIVE` | `system_v5/grok_sim/loop_runner/proposed_formal_sims/_quarantine_jargon` | `archive/maintenance_quarantine/grok_sim_quarantine_jargon_20260520T024525Z/_quarantine_jargon` | Old generated/quarantined proposal shelf, last modified `2026-05-13T20:44:41-0700`, 31 files, 228K, no active source references found in the `system_v5/grok_sim` or `.gitignore` scan. |

## Verification

- Source path is absent after the move.
- Destination path contains 31 files and is preserved under the ignored archive surface.
- No files were deleted.
- No queue, result, formal-scout, provider, or admission surfaces were moved.

## Blocked Candidates

| Decision | Path | Reason |
|---|---|---|
| `BLOCKED_REQUIRES_PREP` | `system_v5/grok_sim/.DS_Store` | Generated junk candidate, but still inside the 72-hour safety window. |
| `BLOCKED_REQUIRES_PREP` | `system_v5/grok_sim/candidates` | Generated candidate shelf, but inside the 72-hour safety window. |
| `BLOCKED_REQUIRES_PREP` | `system_v5/grok_sim/loops` | Generated loop shelf, but inside the 72-hour safety window. |
| `BLOCKED_REQUIRES_PREP` | `system_v5/grok_sim/loop_runner/receipts` | Generated receipts, inside the 72-hour safety window and referenced by runner docs. |
| `BLOCKED_REQUIRES_PREP` | `system_v5/grok_sim/loop_runner/research_notes` | Generated scout notes, but inside the 72-hour safety window. |
| `BLOCKED_REQUIRES_PREP` | `system_v5/grok_sim/loop_runner/proposed_formal_sims` | Parent shelf is referenced by loop-runner scripts; only the exact `_quarantine_jargon` child was archived. |
| `BLOCKED_REQUIRES_PREP` | `work/tmp` | Mixed work surface with current handoff references. |
| `BLOCKED_REQUIRES_PREP` | `system_v4/probes/results` | Old generated results, but referenced by legacy probe code, docs, and tests. |

## Intentionally Kept

| Decision | Path | Reason |
|---|---|---|
| `KEEP_ACTIVE` | `.gitignore` | Active policy file; not a generated-artifact target. |
| `KEEP_ACTIVE` | `system_v5/grok_sim/iters` | Active side-quest iteration shelf inside the safety window. |
| `KEEP_ACTIVE` | `system_v5/grok_sim/results` | Active side-quest result spillover inside the safety window. |
| `KEEP_ACTIVE` | `system_v5/ops/formal_scouts/provider_receipts` | Active provider receipt estate. |
| `KEEP_ACTIVE` | `system_v5/ops/formal_scouts/results` | Active formal-scout result estate. |
| `KEEP_ACTIVE` | `system_v5/legos/results` | Referenced by current indexes and manifests. |

