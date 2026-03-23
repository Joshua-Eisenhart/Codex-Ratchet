# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_work_surface_autowiggle_lane_blockage__v1`
Extraction mode: `DIAGNOSTIC_BLOCKAGE_PASS`

## T1) branch/kill/rescue working vs zero canonical ascent
- source markers:
  - `work/AUTOWIGGLE_RESULTS.md`: `18-34`
  - `work/BLOCKAGE_DIAGNOSIS.txt`: `55-69`
  - `work/RATCHET_STATE_EXTRACT.txt`: `233-240`
- tension:
  - the batch says autowiggle is doing real branch/kill/rescue work
  - the same batch says none of that ever becomes canon
- preserved read:
  - live churn is not evidence of ascent

## T2) "all SIMs failing at T1" vs "canonical ladder never emitted"
- source markers:
  - `work/AUTOWIGGLE_RESULTS.md`: `24-47`
  - `work/BLOCKAGE_DIAGNOSIS.txt`: `55-69`
- tension:
  - one surface frames the problem as tier failure
  - the other frames it as missing `MATH_DEF -> TERM_DEF -> CANON_PERMIT` emission
- preserved read:
  - both may be true at different layers; do not collapse them into one simplified root cause

## T3) 46-step run summary vs 35-cycle raw extract
- source markers:
  - `work/AUTOWIGGLE_RESULTS.md`: `5-9`
  - `work/RATCHET_STATE_EXTRACT.txt`: `4-5`
- tension:
  - the summary reports 46 steps
  - the raw extract reports 35 cycles / 35 steps
- preserved read:
  - keep the count mismatch explicit as extract/resummary residue

## T4) parked/rejected counts conflict inside the raw extract
- source markers:
  - `work/RATCHET_STATE_EXTRACT.txt`: `12-13`
  - `work/RATCHET_STATE_EXTRACT.txt`: `565-590`
- tension:
  - early extract says `parked: 440`, `rejected: 0`
  - later extract says `parked terms: 1980`, `rejected: 1980`, and all `5417` promotion statuses are `PARKED`
- preserved read:
  - internal inconsistency is part of the source signal here

## T5) `PROBE_PASS=true` for all items vs no item promoted
- source markers:
  - `work/AUTOWIGGLE_RESULTS.md`: `31-34`
  - `work/RATCHET_STATE_EXTRACT.txt`: `314-315`
  - `work/RATCHET_STATE_EXTRACT.txt`: `587-590`
- tension:
  - every recorded probe pass is true
  - yet every promotion status remains parked and canon count stays zero
- preserved read:
  - probe pass alone is structurally insufficient for ascent

## T6) rescue evidence volume vs unknown rescue efficacy
- source markers:
  - `work/AUTOWIGGLE_RESULTS.md`: `18-20`
  - `work/BLOCKAGE_DIAGNOSIS.txt`: `34-40`
  - `work/RATCHET_STATE_EXTRACT.txt`: `233-240`
- tension:
  - rescue evidence count is high and summary language sounds positive
  - success/failure/mutation details remain unknown in the raw surfaces
- preserved read:
  - rescue throughput must not be mistaken for rescue efficacy

## T7) fail-closed external packaging vs selector re-entry into the live strategy path
- source markers:
  - request README: `1-13`
  - request MANIFEST: `2-15`
  - pack selector prompt: whole file
- tension:
  - the request shell is framed as tightly fail-closed and packaging-only
  - one role is explicitly asked to emit `A1_STRATEGY_v1` for downstream consumption
- preserved read:
  - this pack is both safety wrapper and live strategy injection path

## T8) sandbox-only lawyer memos vs downstream-consumable selector
- source markers:
  - `ROLE_1_STEELMAN` prompt: whole file
  - `ROLE_2_DEVIL` prompt: whole file
  - `ROLE_3_BOUNDARY` prompt: whole file
  - `ROLE_4_PACK_SELECTOR` prompt: whole file
- tension:
  - three lanes are explicitly sandbox-only and not consumed by lower layers
  - the fourth lane is required to output a strict strategy artifact that will be consumed downstream
- preserved read:
  - the pack splits exploratory and actionable outputs rather than treating all lanes uniformly

## T9) full-context-read requirement vs bounded shell-only intake
- source markers:
  - combined prompt: `3-26`
  - request manifest: `2-15`
- tension:
  - the pack requires all context files to be read before role generation
  - this bounded intake pass intentionally processed only the shell and role split, not the full context corpus
- preserved read:
  - keep the shell/context distinction explicit; do not pretend this batch covered the full semantic payload
