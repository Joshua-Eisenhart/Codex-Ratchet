# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION
Batch: `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## CP1) One bundle emits ten descendants vs split current provenance
- side A:
  - `run_sim_suite_v1.py` emits all ten descendants in one executable surface
- side B:
  - repo-top evidence attribution splits current producer identity across multiple hashes
- preserved handling:
  - keep emission and current provenance separate
  - do not flatten the two into one uniform producer story

## CP2) Clean aligned subset vs migrated subset
- side A:
  - Axis3 / Axis5 / Axis6 remain aligned to the current bundle hash
- side B:
  - Axis12 / Axis4 / Axis0 / Stage16 / Negctrl have migrated to other current provenance anchors
- preserved handling:
  - keep the aligned subset visible
  - keep it from swallowing the migrated subset

## CP3) Bundle emission vs dedicated-runner producer paths
- side A:
  - the bundle emits Axis12, Axis4, and Axis0 descendants directly
- side B:
  - current repo-top evidence attributes those descendants to dedicated runner hashes
- preserved handling:
  - keep bundle emission visible
  - keep dedicated current provenance visible

## CP4) Stage16 version drift vs payload identity
- side A:
  - Stage16 appears under `V4` and `V5`
- side B:
  - the stored result payloads are byte-identical
- preserved handling:
  - keep version drift
  - keep payload identity

## CP5) Negctrl version continuity vs successor-bundle provenance crossover
- side A:
  - Negctrl preserves the same zero metrics across `V2` and `V3`
- side B:
  - current provenance crosses into the successor-bundle hash while versions and trials drift
- preserved handling:
  - keep metric continuity separate from version and producer continuity

## CP6) Raw adjacency vs bundle boundary
- side A:
  - `sim_suite_v2` follows `sim_suite_v1` in raw order and shares partial provenance overlap
- side B:
  - it emits a different bounded descendant set and remains a separate family
- preserved handling:
  - keep overlap visible
  - keep the bundle boundary intact
