# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION
Batch: `BATCH_A2MID_sim_suite_v2_externalized_provenance__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## CP1) Current successor emission vs absent current successor-hash attribution
- side A:
  - `run_sim_suite_v2_full_axes.py` currently emits seven descendants
- side B:
  - none of the repo-top evidence blocks for those descendants uses the current successor-bundle hash
- preserved handling:
  - keep current emission visible
  - keep current top-level attribution separate

## CP2) Dedicated-runner attribution vs successor-bundle emission
- side A:
  - the successor bundle emits Topology4, Axis4, and Axis0 V5 descendants
- side B:
  - repo-top evidence attributes those descendants to dedicated current runners
- preserved handling:
  - keep successor emission
  - keep dedicated current provenance

## CP3) Operator4 successor emission vs predecessor-bundle evidence
- side A:
  - the successor bundle emits operator4 LR V1
- side B:
  - repo-top evidence still points to the predecessor-bundle hash
- preserved handling:
  - keep overlap explicit
  - do not flatten it into one clean upgrade path

## CP4) Stage16 V5 version drift vs payload identity
- side A:
  - Stage16 appears here as `V5`
- side B:
  - the stored payload remains byte-identical to the `V4` result
- preserved handling:
  - keep version drift
  - keep payload identity

## CP5) Negctrl stability vs malformed or foreign provenance
- side A:
  - Negctrl surfaces are emitted here and keep stable low-information metrics
- side B:
  - one block is evidenced under an all-zero hash and the other under a cross-family leading-space hash
- preserved handling:
  - keep metric stability
  - keep provenance contradiction

## CP6) Raw-order adjacency vs next-family boundary
- side A:
  - `run_stage16_axis6_mix_control.py` follows this bundle in raw order
- side B:
  - the successor bundle already closes cleanly on its own emitted descendant set
- preserved handling:
  - keep adjacency visible
  - keep the next Stage16 family separate
