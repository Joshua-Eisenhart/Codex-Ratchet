# RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_REVIEW__2026_03_11__v1

Status: DRAFT / NONCANON / A2 AUDIT OUTPUT
Date: 2026-03-11
Role: bounded review of the dominant `system_v3/runs` concentration family

## 1) Scope

- audited only the `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE*` family under:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/runs`
- goal:
  - determine whether the run-folder bloat still has a meaningful next internal action
  - avoid path-breaking archive moves where run-anchor / witness surfaces still depend on exact run paths

## 2) Current concentration

- current family count: `62`
- largest visible entries:
  - `15.4M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0015`
  - `14.4M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0016`
  - `12.0M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_0006`
  - `9.0M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_0048`
  - `9.0M` `RUN_GRAVEYARD_VALIDITY_ENTROPY_BRIDGE_CLUSTER_RESCUE_BROAD_CONT_ROTATE_0001`

Operational read:
- this is the main remaining local size concentration inside `system_v3/runs`
- the family is not one bad directory; it is a broad repeated cluster with many medium-size runs

## 3) Structural pattern

Representative top entries share the same heavy structure:
- `a1_inbox`
- `a1_packet_inbox_surface`
- `a1_sandbox`
- `append_only_event_log_surface`
- `append_only_tape_surface`
- `b_reports`
- `deterministic_compile_and_kernel_report_surface`
- `deterministic_outbound_export_block_cache_surface`
- `reports`
- `sim`
- `tapes`
- `state.json`
- `summary.json`

Read:
- these are full evidence-bearing run surfaces, not trivial scratch dirs
- they look more like repeated heavyweight runtime instances than obviously disposable temp folders

## 4) Anchor dependency check

Live repo evidence still points at exact family members through:
- `run_anchor_surface/*`
- `RUN_REGENERATION_WITNESS__*`
- archive-surface/source-map packets in:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_archive_surface_heat_dumps_root_family_split__v1`

Important result:
- multiple run-anchor and witness surfaces still rely on exact run paths from this family
- direct archive/quarantine mutation is therefore not justified in this pass

## 5) Decision

Decision: `HOLD_UNTIL_RUN_ANCHOR_REMAP`

Meaning:
- this family is a real remaining cleanup target
- but the next safe step is not filesystem mutation
- the next safe step is a narrower remap/audit of which exact members are still required by active anchor/witness surfaces

## 6) Exact next internal run-folder go-on

If an internal run-folder go-on is wanted, it should be:

`RUN_ANCHOR_DEPENDENCY_REMAP__ENTROPY_BRIDGE_CLUSTER`

Bounded task:
- enumerate exact family members still referenced by active `run_anchor_surface/` and active intake/archive packets
- separate:
  - `anchor-live`
  - `archive-only`
  - `unreferenced`
- do not move any run in that pass

## 7) Stop rule

- stop after producing one exact remap list
- do not archive or delete within that same pass
