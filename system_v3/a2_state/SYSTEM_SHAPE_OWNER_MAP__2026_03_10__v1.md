# SYSTEM_SHAPE_OWNER_MAP__2026_03_10__v1

Status: DRAFT / NONCANON / A2 AUDIT OUTPUT
Date: 2026-03-10
Role: bounded owner map for the system-shape and bloat audit lane

## 1) Active owner surfaces

These remain the primary owner path and should not be treated as generic cleanup:
- `system_v3/specs/`
- `system_v3/a2_state/`
- `system_v3/a1_state/`
- `system_v3/tools/`
- `system_v3/runtime/`
- `system_v3/runs/` as runtime evidence owner, not doctrine owner
- `system_v3/a2_high_entropy_intake_surface/`
- `system_v3/control_plane_bundle_work/`
- `system_v3/conformance/`
- `system_v3/public_facing_docs/`

## 2) Alias / migration scaffolding

These should remain aliases only and must not be counted as separate systems:
- `system_v3/a2_noncanonical_derived_index_cache_surface`
- `system_v3/a2_persistent_context_and_memory_surface`
- `system_v3/conformance_and_fixture_validation_surface`
- `system_v3/control_plane_bundle_authoring_workspace_surface`
- `system_v3/deterministic_campaign_run_surface`
- `system_v3/deterministic_operational_tooling_surface`
- `system_v3/deterministic_runtime_execution_surface`
- `system_v3/noncanonical_draft_specification_surface`
- `system_v3/public_facing_documentation_surface`

## 3) Derived / support only

These are useful but should not outrank active owners:
- `system_v3/a2_derived_indices_noncanonical/`
- packet sinks, noncanonical indices, generated caches

## 4) Runtime evidence only

These must be understood as evidence/replay surfaces rather than standing doctrine:
- `system_v3/runs/`
- run registries, packets, tapes, and state sidecars under runs

Operational consequence:
- integrate the run system shape
- do not ingest run volume wholesale into standing A2 understanding

## 5) `work/` classification

`work/` is mixed spillover, not one cleanup class.

### Active / still in use
- `work/zip_subagents`
- `work/zip_job_templates`
- `work/zip_dropins`
- `work/to_send_to_pro`
- `work/curated_zips` as delivery/reference, not owner law
- `work/audit_tmp` as temporary staging, not standing truth

### Likely prototype / spillover / investigate-first
- `work/system_v3`
- `work/out`
- `work/a1_sandbox`
- `work/extracts`
- `work/coordination_sandbox__codex_minimax__noncanonical_delete_safe`
- `work/minimax_spillover_quarantine`

### Small legacy/reference pockets
- `work/CORE`
- `work/INBOX`
- `work/SIM`
- `work/a1_brain_persistent__v1`
- `work/a1_transient_cold_core`
- `work/cache_backup`
- `work/golden_tests`

## 6) Owner-map conclusions

- The system is not uniformly bloated.
- The active owner path is still concentrated in `system_v3/`.
- `runs/` is the main evidence-heavy local surface.
- `work/` is the main mixed spillover surface and needs selective classification, not blanket thinning.
- Alias surfaces remain a comprehension risk more than a size risk.
