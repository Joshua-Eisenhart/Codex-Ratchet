# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION PRESERVATION
Batch: `BATCH_A2MID_archive_progress_bundle_v2_patch_resume_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction CP1) Clean continuation vs dirty retained state
- preserved contradiction:
  - README, summary, and soak surfaces present a clean continuation
  - state still retains parked terms, reject history, and kill signals
- anti-smoothing rule:
  - do not normalize stored state into "fully clean"

## Preserved contradiction CP2) README packet claim vs embedded event proof
- preserved contradiction:
  - README names packets `000010 + 000011` as the latest clean continuation
  - embedded event rows reference strategy packets only through `000009`
- anti-smoothing rule:
  - do not let operator notes outrank embedded event proof

## Preserved contradiction CP3) Strong hash residue vs missing evidence bodies and broader context
- preserved contradiction:
  - README, summary, state, and sidecar agree on the final hash
  - evidence bodies and broader run-control context are still absent
- anti-smoothing rule:
  - do not convert strong state residue into full closure

## Preserved contradiction CP4) Repaired resume control vs partial self-sufficiency
- preserved contradiction:
  - v2 restores run-local state and sequence maxima handling
  - the bundle still omits heavier control surfaces and sim evidence
- anti-smoothing rule:
  - do not treat repair value as full self-sufficiency

## Preserved contradiction CP5) Stable blocker-like summary counts vs indirect state encoding
- preserved contradiction:
  - summary reports `unresolved_promotion_blocker_count 7`
  - the clearest matching state residue is indirect through the seven-entry `kill_log`
- anti-smoothing rule:
  - do not promote summary blocker counts into clean state-law fields

## Preserved contradiction CP6) V2 child complete vs broader bundle sibling still unread
- preserved contradiction:
  - this child now narrows the v2 export
  - the broader `RUN_FOUNDATION_BATCH_0001_bundle` sibling still belongs to the next bounded step
- anti-smoothing rule:
  - do not treat this child as if it already read the next bundle sibling
