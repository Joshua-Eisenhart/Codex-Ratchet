# A2_UPDATE_NOTE__CARNOT_PACKET_SECOND_SOURCE_FILL__2026_03_12__v1

Status: PROPOSED / NONCANONICAL / A2 UPDATE NOTE
Date: 2026-03-12
Role: bounded A2 controller note for the second real source-bearing fill of `carnot_primary`

## AUDIT_SCOPE
- corrected external boot workspace:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/work/zip_dropins/ZIP_JOB__EXTERNAL_RESEARCH_RETOOL_REFINERY__ENTROPY_CARNOT_SZILARD_ENGINE_FAMILIES__CHATUI_DROPIN__v3`
- target packet:
  - `sources/external/carnot_primary/`
- prior hold surface:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_state/EXTERNAL_BOOT_READINESS_AUDIT__ENTROPY_CARNOT_SZILARD__2026_03_12__v1.md`

## FINDINGS
- `carnot_primary` now has a minimal two-file source-bearing floor:
  - cycle skeleton / maximum-effect condition
  - reversibility / efficiency dependence on temperature limits
- this materially improves the first-priority packet beyond single-extract fragility
- the lane still remains held because:
  - Carnot is still partial, not comprehensive
  - `maxwell_demon_primary` remains stub-only
  - `fep_active_inference_primary` remains stub-only

## A2_UPDATE_NOTE
- preserve the narrowed blocker:
  - the first priority wave is no longer blocked by an empty Carnot packet
  - it is now blocked by:
    - remaining Carnot depth gaps
    - no first source-bearing Maxwell packet
    - no first source-bearing FEP packet
- preserve the next exact move:
  - shift the next bounded fill to `maxwell_demon_primary`

## OFF_PROCESS_FLAGS
- off-process if a later controller note:
  - treats two Carnot files as enough to claim full first-wave readiness
  - skips Maxwell and FEP because Carnot now looks respectable

## SAFE_TO_CONTINUE
- yes, for one bounded first-source fill on `maxwell_demon_primary`
- no, for external launch yet
- no, for fresh `A1`
