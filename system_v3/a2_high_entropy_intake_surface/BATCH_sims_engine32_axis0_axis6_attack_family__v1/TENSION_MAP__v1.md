# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_engine32_axis0_axis6_attack_family__v1`
Extraction mode: `SIM_ENGINE32_ATTACK_PASS`

## T1) “Axis0 attack” label vs explicit one-qubit proxy simplification
- source markers:
  - `run_engine32_axis0_axis6_attack.py:111-121`
- tension:
  - the file is named `axis0_axis6_attack`
  - the script explicitly says it keeps Axis0 simple as a one-qubit trajectory proxy and uses no AB coupling
- preserved read:
  - keep the label and the simplification side by side; do not silently upgrade the proxy into AB-correlation evidence
- possible downstream consequence:
  - later Axis0 lineage should treat this family as adjacent to, but not equivalent with, AB-coupled families

## T2) Absolute result lattice vs delta-only evidence packet
- source markers:
  - `run_engine32_axis0_axis6_attack.py:219-232`
  - `results_engine32_axis0_axis6_attack.json:1-689`
- tension:
  - the paired result file stores all absolute stage metrics for `32` cells
  - the evidence packet emits only `MIX_R - UNIFORM` deltas
- preserved read:
  - keep full-result structure and evidence compression separate
- possible downstream consequence:
  - provenance summaries should not pretend the evidence block fully describes the stored result surface

## T3) Stable outer/inner sign split vs weaker sequence modulation
- source markers:
  - `results_engine32_axis0_axis6_attack.json:1-689`
  - derived numeric read in this batch
- tension:
  - sequence order modulates magnitude
  - but the larger pattern is loop-stable:
    - outer entropy deltas stay positive
    - inner entropy deltas stay negative
- preserved read:
  - keep sequence variation subordinate to the stronger loop-orientation split
- possible downstream consequence:
  - later summaries should not overstate sequence-order effects at the expense of the loop split

## T4) Catalog visibility vs top-level evidence-pack absence
- source markers:
  - `SIM_CATALOG_v1.3.md:54`
  - top-level evidence-pack search read in this batch
- tension:
  - `engine32_axis0_axis6_attack` is cataloged
  - no direct `S_SIM_ENGINE32_AXIS0_AXIS6_ATTACK` block was found in the current top-level evidence pack
- preserved read:
  - keep catalog presence distinct from top-level evidence-pack admission
- possible downstream consequence:
  - this family should remain source-local in provenance strength until a matching evidence-pack anchor exists

## T5) Local attack family vs adjacent cross-axis sampler
- source markers:
  - `run_engine32_axis0_axis6_attack.py:168-232`
  - `run_full_axis_suite.py:224-253`
- tension:
  - `engine32` is one focused SIM_ID with a single attack lattice
  - the adjacent `full_axis_suite` is a six-block cross-axis sampler with axes 3/4/5/6 and no Axis0 lattice
- preserved read:
  - do not merge raw-order adjacency into one bounded family
- possible downstream consequence:
  - the next batch should process `full_axis_suite` as a separate sampler/precursor family

## T6) Script-local evidence exists, but repo-top-level evidence emphasis has shifted elsewhere
- source markers:
  - `run_engine32_axis0_axis6_attack.py:210-232`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:93-107`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:269-298`
- tension:
  - `engine32` defines and writes a local evidence block
  - the current repo-held top-level evidence pack instead emphasizes other axis families and standalone descendants
- preserved read:
  - keep script-local evidencing and repo-top-level evidence admission separate
- possible downstream consequence:
  - later confidence grading should distinguish “would write evidence” from “is currently top-level evidenced in repo state”
