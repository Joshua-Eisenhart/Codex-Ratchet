# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION PRESERVATION
Batch: `BATCH_A2MID_reentry_gap_selection_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Preserved contradiction set

### 1) Local pair closure vs broader unresolved queue still open
- preserved poles:
  - the immediate refined-fuel re-entry pair is now directly child-closed
  - the broader unresolved queue still contains multiple older parents with no direct children
- reduction handling:
  - local closure preserved in `RC1`
  - broader unresolved queue remains explicit in `RC5` and `Q4`

### 2) Queue text continuity vs ledger-state authority
- preserved poles:
  - prior queue text provides continuity of thread intent
  - current ledger state is the stronger authority once new child batches land
- reduction handling:
  - queue continuity is preserved only as context for why this audit was needed
  - ledger authority is preserved in `RC2`
  - stale queue overread remains in `Q2`

### 3) Existing Thread B child context vs unresolved a2feed Thread B parent
- preserved poles:
  - there is already a useful Thread B A2-mid child in the intake surface
  - the a2feed Thread B parent still has no direct child and therefore remains unresolved
- reduction handling:
  - additive sibling value preserved in `RC4`
  - false closure overread left in `Q3`

### 4) Giant unresolved parents remain real vs bounded next-step yield favors compact engine pattern
- preserved poles:
  - large unresolved source-map and archive-package parents are still real future work
  - the next bounded step should still favor the compact unresolved Thread B engine-pattern parent
- reduction handling:
  - compact next-step priority preserved in `RC3` and `RC5`
  - size-first or age-first reentry overread left in `Q4`

### 5) Audit packet usefulness vs control-memory nonpromotion
- preserved poles:
  - this audit packet is useful for lane selection and queue cleanup
  - it is still only an intake-surface artifact and not an active A2 control update
- reduction handling:
  - bounded selection value preserved across `RC1` through `RC5`
  - control-surface overread left in `Q5`
