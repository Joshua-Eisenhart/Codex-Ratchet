# CONTRADICTION_PRESERVATION__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING REDUCTION NOTE
Batch: `BATCH_A2MID_sims_axis4_p03_evidence_path__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-08

## CP1) Self-Label Inside Harness vs Real Duplicate Filename
Pole A:
- `axis4_seq_cycle_sim.py` self-labels as `run_axis4_sims.py`

Pole B:
- a separate real file named `run_axis4_sims.py` exists in the same family

Preserved read:
- keep this as filename-identity drift, not as a typo to silently erase

## CP2) Duplicate Harnesses vs One Currently Evidenced Producer
Pole A:
- two near-duplicate harnesses target the same P03 result namespace

Pole B:
- the top-level evidence pack currently binds only one harness hash to the stored P03 outputs

Preserved read:
- preserve one evidenced producer path and one unresolved alternate authoring path

## CP3) Shared Result Targets vs Divergent Sidecar Contracts
Pole A:
- both harnesses write the same `results_<SIM_ID>.json` family

Pole B:
- one emits per-SIM evidence files while the other emits one packed evidence file

Preserved read:
- keep the result namespace shared and the sidecar contract split explicit

## CP4) Generic Axis4 Sequence Story vs Polarity-Specific Asymmetry
Pole A:
- there is pressure to summarize the family as showing generic Axis4 sequence sensitivity

Pole B:
- the current stored results show invariance on `polarity_plus` and variation on `polarity_minus`

Preserved read:
- sequence sensitivity must stay branch-specific in this family

## CP5) Type Switch Exposed vs Type-1-Only Stored Family
Pole A:
- both harnesses expose `axis3_sign` as the type switch

Pole B:
- the stored P03 family is only `axis3_sign = +1`

Preserved read:
- do not treat the current files as evidence for both type branches

## CP6) Coherent Axis4 Family Bundle vs Interrupted Raw Folder Order
Pole A:
- this batch coherently bundles the Axis4 P03 core harness family

Pole B:
- unrelated `mega_*`, `prove_foundation.py`, and early `run_axis0_*` files intervene in raw folder order

Preserved read:
- keep the small-related-docs family-bundle decision explicit rather than pretending folder order was contiguous
