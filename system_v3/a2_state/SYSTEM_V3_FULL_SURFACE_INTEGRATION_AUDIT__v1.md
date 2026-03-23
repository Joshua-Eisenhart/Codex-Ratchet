# SYSTEM_V3_FULL_SURFACE_INTEGRATION_AUDIT__v1

Status: WORKING / NONCANONICAL / SOURCE-GUIDED
Purpose: classify the full `system_v3/` tree into active, alias, prototype/reference, generated, and cleanup surfaces so the system can be lean, integrated, and self-aware without bloating itself.

## 1. Core rule

`system_v3/` should not try to flatten every file into one standing truth surface.

Lean integration means:
- every active contract surface is known and linked
- every prototype/reference surface is indexed and consciously treated as reference
- every generated/run surface is treated as runtime evidence, not standing doctrine
- every alias is understood as an alias, not a second system
- junk is removed or clearly marked

## 2. Active root surfaces that must be integrated

These are active and should be part of the system's self-understanding:

- `system_v3/00_CANONICAL_ENTRYPOINTS_v1.md`
- `system_v3/01_OPERATIONS_RUNBOOK_v1.md`
- `system_v3/02_SAFE_DELETE_SURFACE_v1.md`
- `system_v3/03_EXPLICIT_NAME_ALIAS_SURFACE_v1.md`
- `system_v3/WORKSPACE_LAYOUT_v1.md`
- `system_v3/specs/`
- `system_v3/a2_state/`
- `system_v3/a1_state/`
- `system_v3/tools/`
- `system_v3/runtime/`
- `system_v3/control_plane_bundle_work/`
- `system_v3/conformance/`
- `system_v3/public_facing_docs/`

These are the surfaces that define what the system currently is, how it runs, how it is explained, and how it is audited.

## 3. Alias surfaces

These are not extra systems. They are compatibility aliases:

- `system_v3/a2_noncanonical_derived_index_cache_surface -> a2_derived_indices_noncanonical`
- `system_v3/a2_persistent_context_and_memory_surface -> a2_state`
- `system_v3/conformance_and_fixture_validation_surface -> conformance`
- `system_v3/control_plane_bundle_authoring_workspace_surface -> control_plane_bundle_work`
- `system_v3/deterministic_campaign_run_surface -> runs`
- `system_v3/deterministic_operational_tooling_surface -> tools`
- `system_v3/deterministic_runtime_execution_surface -> runtime`
- `system_v3/noncanonical_draft_specification_surface -> specs`
- `system_v3/public_facing_documentation_surface -> public_facing_docs`

Lean rule:
- keep them only as migration/compatibility aids
- never count them as separate surfaces
- never describe them as extra architecture

## 4. Active but under-integrated surfaces

These exist and matter, but were not fully centralized in the earlier understanding pass:

### `system_v3/control_plane_bundle_work/`
- already contains major ZIP-subagent engineering
- should be treated as active control-plane authoring/reference
- not junk
- must be cross-linked into current understanding

### `system_v3/a2_derived_indices_noncanonical/`
- derived helper layer
- regenerable
- useful for memory/search/debug
- should not be treated as authority
- needs conscious integration as "derived only"

### `system_v3/conformance/`
- small but important
- fixture packs and expected outcomes
- should be recognized as part of determinism/self-check infrastructure

### `system_v3/public_facing_docs/`
- explanatory only
- useful for outer-facing clarity
- must not outrank active runtime/spec surfaces

## 5. Generated/runtime surfaces

### `system_v3/runs/`
- this is not one doc surface
- it is runtime evidence and replay state
- must be indexed, sampled, and audited
- should not be ingested wholesale into standing understanding docs

Lean rule:
- integrate the run system, not every run file
- keep representative runs and current-state surfaces
- do not confuse run volume with system understanding

## 6. Prototype/reference history that should remain reference

Inside `system_v3/`, the main active reference/prototype zone is:
- `system_v3/control_plane_bundle_work/`

It should be treated as:
- active authoring workspace
- reference/prototype input for current system integration
- not automatically equal to enforced runtime

## 7. Current junk / sprawl risks

### Real junk
- `.DS_Store`

### Potential sprawl risks
- many backup JSONs under `system_v3/a2_derived_indices_noncanonical/`
- excessive run copies under `system_v3/runs/`
- duplicate descriptive surfaces if alias names are treated as separate systems

These are not all junk, but they are the main places where lean discipline can fail.

## 8. What "every doc integrated and used" should mean

For `system_v3/`, the correct interpretation is:

- every active surface is known
- every active surface has a role
- every active surface has a boundary
- every non-authoritative surface is marked as such
- every prototype/reference surface is consciously mapped
- every generated surface is treated as evidence/runtime, not standing doctrine

It should NOT mean:
- every run file becomes standing context
- every backup file becomes required reading
- every alias becomes a new system
- every prototype file gets promoted into the main self-description

## 9. Lean integration decision table

### Keep and integrate
- root active docs
- `specs/`
- `a2_state/`
- `a1_state/`
- `tools/`
- `runtime/`
- `control_plane_bundle_work/`
- `conformance/`
- `public_facing_docs/`

### Keep as derived/support only
- `a2_derived_indices_noncanonical/`

### Keep as runtime evidence only
- `runs/`

### Keep as aliases only
- all long explicit alias symlinks

### Clean opportunistically
- `.DS_Store`
- unnecessary stale run copies if safe-delete policy allows

## 10. Immediate next integration task

The next lean integration step is:

1. make `system_v3` self-aware of the active root surfaces
2. explicitly map `control_plane_bundle_work` into the active system map
3. explicitly mark `a2_derived_indices_noncanonical` as derived-only
4. explicitly treat `runs/` as runtime evidence, not standing doctrine
5. stop treating aliases as separate systems

## 11. Bottom line

`system_v3/` is not mostly junk.

It is:
- partly active
- partly alias/migration
- partly derived
- partly runtime evidence
- partly control-plane authoring

The real problem is not raw folder size.
The real problem is lack of a single explicit classification surface.

This audit is that surface.
