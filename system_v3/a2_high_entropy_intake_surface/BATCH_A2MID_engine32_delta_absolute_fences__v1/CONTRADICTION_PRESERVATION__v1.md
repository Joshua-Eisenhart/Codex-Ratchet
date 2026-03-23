# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION
Batch: `BATCH_A2MID_engine32_delta_absolute_fences__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## CP1) Attack label vs proxy implementation
- side A:
  - `Axis0 attack` naming remains visible
- side B:
  - implementation narrows the family to a one-qubit trajectory proxy with no AB coupling
- preserved handling:
  - keep both
  - do not smooth the label into stronger Axis0 evidence than the script supplies

## CP2) Absolute result lattice vs compressed evidence sidecar
- side A:
  - the paired JSON stores absolute stage metrics across all `32` cells
- side B:
  - the script-local evidence block emits only `MIX_R - UNIFORM` deltas
- preserved handling:
  - keep both surfaces distinct
  - do not substitute the sidecar for the full result lattice

## CP3) Strong loop split vs weaker sequence modulation
- side A:
  - sequence order changes magnitude
- side B:
  - loop orientation keeps a stronger sign-stable split across the family
- preserved handling:
  - keep both
  - rank loop orientation above sequence when compressing the family

## CP4) Local visibility vs top-level admission
- side A:
  - the family is catalog-visible and script-local evidence exists
- side B:
  - no direct current top-level evidence-pack block was preserved by the parent batch
- preserved handling:
  - keep visibility and admission as separate provenance layers

## CP5) Raw-order adjacency vs family separation
- side A:
  - `full_axis_suite` follows engine32 in raw order and shares some axis vocabulary
- side B:
  - `full_axis_suite` is a structurally different cross-axis sampler family
- preserved handling:
  - keep adjacency visible
  - keep the family boundary intact
