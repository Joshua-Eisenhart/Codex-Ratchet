# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis4_p03_core_harness_family__v1`
Extraction mode: `SIM_AXIS4_CORE_PASS`

## T1) Filename identity drift inside the first harness
- source markers:
  - `axis4_seq_cycle_sim.py:2-3`
  - `run_axis4_sims.py:2-3`
- tension:
  - `axis4_seq_cycle_sim.py` self-labels as `run_axis4_sims.py`
  - there is also a separate real file named `run_axis4_sims.py`
- preserved read:
  - keep this as source-level identity confusion, not a typo to silently normalize away
- possible downstream consequence:
  - any later producer-path judgment must preserve this duplicate naming residue

## T2) Duplicate harnesses vs one evidenced producer
- source markers:
  - harness hashes in this batch
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:111-183`
- tension:
  - two near-duplicate harnesses target the same P03 result namespace
  - the current repo-held evidence pack references only the `axis4_seq_cycle_sim.py` hash `b741c60d...`
  - no current evidence-pack anchor was found for the alternate `run_axis4_sims.py` hash `1fac087c...`
- preserved read:
  - the family currently has one evidenced producer path and one unresolved duplicate authoring path
- possible downstream consequence:
  - do not assume the duplicate harness is dead or authoritative without a later source-bound audit

## T3) Output-contract mismatch
- source markers:
  - `axis4_seq_cycle_sim.py:247-263`
  - `run_axis4_sims.py:215-229`
- tension:
  - one harness writes one evidence file per SIM_ID
  - the other writes one packed `sim_evidence_pack.txt`
  - both write the same `results_<SIM_ID>.json` names
- preserved read:
  - keep both output contracts visible; do not collapse them into one implied standard
- possible downstream consequence:
  - later sidecar reconciliation should treat per-file and packed evidence contracts separately

## T4) Sequence sensitivity is polarity-asymmetric
- source markers:
  - `results_S_SIM_AXIS4_SEQ01_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ02_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ03_P03.json:9-24`
  - `results_S_SIM_AXIS4_SEQ04_P03.json:9-24`
- tension:
  - `polarity_plus` purity and entropy means are identical across all four sequences
  - `polarity_minus` purity and entropy means vary by sequence order
- preserved read:
  - keep this as a real asymmetry in the current result family rather than speaking about “Axis4 sequence effects” generically
- possible downstream consequence:
  - later summaries should state which polarity actually carries the sequence distinction

## T5) Type-1 evidence present, Type-2 only mentioned
- source markers:
  - `axis4_seq_cycle_sim.py:228`
  - `run_axis4_sims.py:200`
  - `results_S_SIM_AXIS4_SEQ01_P03.json:2`
- tension:
  - both harnesses expose `axis3_sign` as the Type-1 / Type-2 switch
  - the current P03 result family is stored only for `axis3_sign = +1`
- preserved read:
  - do not treat the current P03 family as evidence for both type branches
- possible downstream consequence:
  - later Axis4 type-specific batches should keep sign-family coverage explicit

## T6) Family bundling vs raw folder order
- source markers:
  - raw `simpy/` listing around `axis4_seq_cycle_sim.py`
- tension:
  - unrelated `mega_*`, `prove_foundation.py`, and early `run_axis0_*` files intervene in raw folder order
  - this batch nevertheless bundles the nearest coherent Axis4 core family instead of flattening unrelated sources into one package
- preserved read:
  - keep the family-bundle decision explicit as a bounded intake choice, not as proof that the intervening files are irrelevant
- possible downstream consequence:
  - later batches should still return to the deferred raw-folder-order surfaces or state why they stay deferred
