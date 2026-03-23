# REFINEDFUEL_REVISIT_ROUTING_PASS__2026_03_11__v1

Status: DRAFT / NONCANON / A2 CONTROL NOTE
Date: 2026-03-11
Role: bounded family-routing pass over the live `BATCH_refinedfuel*` intake family

## Scope

This pass does **not** globally reprocess all refined-fuel batches.

It only does one bounded controller task:
- split the current `BATCH_refinedfuel*` family into:
  - `RUN_NOW`
  - `HOLD`
  - `ARCHIVE_SIDE_ONLY`

Routing basis:
- live family count: `72` refined-fuel batch dirs
- current intake mix is dominated by already-reduced reusable math-class / overlay-governance packets plus a smaller revisit-required contradiction cluster
- the current controller shortlist still points first to the `Constraints. Entropy` sibling pair

## Controller read

The refined-fuel family is not one backlog class.

It is already internally split into three different classes:
- active contradiction/revisit parents that still need controller-directed re-entry
- already-reduced reusable fences that should not be reopened just because they remain live in intake
- archive/save/manifests and support packets that are useful as reference lineage but are not the next live refinement target

So the correct next move is selective routing, not “process all refinedfuel.”

## RUN_NOW

These are the highest-value live refined-fuel parents for the next bounded internal A2 revisit lane:

1. `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`
   - status in index: `REVISIT_REQUIRED`
   - still the strongest contradiction-routing parent for precursor-pressure / scalar overreach / engine-topology drift

2. `BATCH_refinedfuel_constraints_term_conflict__v1`
   - status in index: `REVISIT_REQUIRED`
   - still the strongest governance-residue companion parent for the same stitched foundation cluster

3. `BATCH_refinedfuel_constraints_entropy_source_map__v1`
   - active support parent for contradiction tracing and source remap continuity
   - should travel with the sibling pair rather than be reopened alone

4. `BATCH_refinedfuel_constraints_source_map__v1`
   - active support parent for contradiction tracing and source remap continuity
   - should travel with the sibling pair rather than be reopened alone

5. `BATCH_refinedfuel_physics_fuel_digest_term_conflict__v1`
   - status in index: `A2_3_REUSABLE`
   - not a first-pass doctrine packet, but still the best next refined-fuel quarantine/translation boundary follow-on once the constraints pair is stabilized
   - route: second-wave `RUN_NOW`, not first-wave mandatory

## HOLD

These stay live but should **not** be reopened now.

Reason:
- they already have strong reusable fence value
- many already have A2-mid/controller-facing descendants
- reopening them now would mostly create duplicate or low-yield work

Families/classes to hold:

1. math-class admissibility / contract packets
   - examples:
     - `BATCH_refinedfuel_geometry_admissibility_math_class__v1`
     - `BATCH_refinedfuel_metric_admissibility_math_class__v1`
     - `BATCH_refinedfuel_obstruction_admissibility_math_class__v1`
     - `BATCH_refinedfuel_orthogonality_admissibility_math_class__v1`
     - `BATCH_refinedfuel_path_contract_math_class__v1`
     - `BATCH_refinedfuel_refinement_contract_math_class__v1`
     - `BATCH_refinedfuel_transport_contract_math_class__v1`
   - reason: already reusable fence stock, not priority revisit targets

2. overlay-governance / removable-rosetta packets
   - examples:
     - `BATCH_refinedfuel_game_theory_rosetta_personality_analogy__v1`
     - `BATCH_refinedfuel_physics_rosetta_personality_analogy__v1`
   - reason: useful overlay fences, but not the best next live revisit work

3. already-reduced nonsims closure/controller packets
   - examples:
     - `BATCH_refinedfuel_nonsims_residual_inventory_closure_audit__v1`
     - `BATCH_A2MID_refinedfuel_nonsims_residual_inventory_controller_fences__v1`
     - the broader `BATCH_A2MID_refinedfuel_nonsims_*` descendant cluster already recorded in queue surfaces
   - reason: closure/routing support is real, but fresh same-root reprocessing would be duplicate

4. contradiction descendants already reduced into A2-mid packets
   - example:
     - `BATCH_A2MID_CONTRADICTION_entropic_qit_math_drift__v1`
   - reason: already a bounded contradiction reprocess surface; use as anchor, do not reopen as a fresh parent lane

## ARCHIVE_SIDE_ONLY

These are still useful as lineage/reference, but they are not next live refinement targets.

1. `BATCH_refinedfuel_archive_manifest_source_map__v1`
   - archive-classification / readiness ledger
   - archive-local reference value is high
   - not a live revisit priority

2. `BATCH_refinedfuel_thread_s_full_save_family__v1`
   - save-kit / replay-family lineage packet
   - strong archive/replay reference value
   - not a live refined-fuel revisit target

## Exact next pass unlocked by this routing

The next bounded internal refined-fuel pass should be:

`CONSTRAINTS_REVISIT_PASS__PAIR_PLUS_SOURCE_MAPS`

Required inputs:
- `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`
- `BATCH_refinedfuel_constraints_term_conflict__v1`
- `BATCH_refinedfuel_constraints_entropy_source_map__v1`
- `BATCH_refinedfuel_constraints_source_map__v1`
- existing child anchors:
  - `BATCH_A2MID_constraints_entropy_chain_fences__v1`
  - `BATCH_A2MID_constraints_foundation_governance_fences__v1`

Optional immediate follow-on after that:
- `BATCH_refinedfuel_physics_fuel_digest_term_conflict__v1`

## Stop rule

This routing pass stops here.

It does not:
- archive refined-fuel files
- reopen held packets
- mutate archive-side packets
- start the pair revisit itself

Its only job is to set the exact family routing.
