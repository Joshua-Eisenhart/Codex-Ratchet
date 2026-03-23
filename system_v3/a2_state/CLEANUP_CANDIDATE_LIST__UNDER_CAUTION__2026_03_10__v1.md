# CLEANUP_CANDIDATE_LIST__UNDER_CAUTION__2026_03_10__v1

Status: DRAFT / NONCANON / A2 AUDIT OUTPUT
Date: 2026-03-10
Role: caution-classified cleanup candidate list produced by the system-shape and bloat audit lane

## 1) Keep

Keep as active or clearly useful:
- `system_v3/specs/`
- `system_v3/a2_state/`
- `system_v3/a1_state/`
- `system_v3/tools/`
- `system_v3/runtime/`
- `system_v3/a2_high_entropy_intake_surface/`
- `system_v3/control_plane_bundle_work/`
- `system_v3/runs/` as a class
- `work/zip_subagents`
- `work/zip_job_templates`
- `work/zip_dropins`
- `work/to_send_to_pro` as an active class, though likely needing bounded rotation/thinning

## 2) Archive

Good bounded archive-prep candidates:
- older heavy `work/audit_tmp` subtrees once not tied to an active pending task
- older `work/out` output trees once reproduced or superseded by owner surfaces
- older `work/to_send_to_pro` artifacts once the active current send sets are identified
- selected legacy run families inside `system_v3/runs/` once representative retention rules are defined

Archive rule:
- archive by bounded class or subtree after lineage check
- do not archive the entire parent class wholesale

## 3) Quarantine

Good quarantine candidates:
- `work/system_v3` mirrored system fragment if it is not an active authoring surface
- stale `work/a1_sandbox` residue not needed for current active runs
- stale coordination/minimax spillover surfaces if no active consumer exists:
  - `work/coordination_sandbox__codex_minimax__noncanonical_delete_safe`
  - `work/minimax_spillover_quarantine`

Quarantine rule:
- move out of active reload intuition first
- do not delete directly from this pass

## 4) Investigate

Needs narrower investigation before any mutation:
- `work/system_v3`
  - large enough to matter
  - ambiguous whether it is active mirror, stale fragment, or mixed
- `_RUNS_REGISTRY.jsonl`
  - large enough to matter
  - likely required, but may need bounded split/rotation rules later
- the `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_*` family in `system_v3/runs/`
  - high concentration class
  - may be valid evidence retention rather than simple bloat
- `work/to_send_to_pro`
  - active as a class
  - likely contains stale send artifacts mixed with active ones

## 5) No-delete-without-followon

This lane does **not** justify deletion.

Any later mutation lane must first choose one of:
- archive-prep for a bounded subtree/class
- quarantine-prep for a bounded ambiguous surface
- narrower investigation of one ambiguous large surface

The strongest next bounded follow-on is:
- investigate `work/system_v3` and `work/to_send_to_pro` first
- then design one bounded archive/quarantine lane for stale staging/send residue
