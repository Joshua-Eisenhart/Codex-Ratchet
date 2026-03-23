# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1`
Extraction mode: `SIM_AXIS0_HISTORYOP_REC_SUITE_PASS`
Batch scope: standalone residual axis0 history-operator reconstruction family centered on `run_axis0_historyop_rec_suite_v1.py` and `results_axis0_historyop_rec_suite_v1.json`, with top-level catalog/evidence and residual-closure continuity held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_historyop_rec_suite_v1.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_historyop_rec_suite_v1.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_historyop_rec_suite_v1.json`
- reason for bounded family:
  - the closure audit marked this as the first clean residual runner/result pair
  - one runner emits one paired result surface containing four internal reconstruction cases
  - no repo-held top-level evidence-pack block currently admits those four local SIM_IDs
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mi_discrim_branches.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_historyop_rec_suite_v1.py`
  - sha256: `919db9d0ee0528a31ee4a5d8bdfa3e2bed93b4ba5449bbdd77d50f7778ce90d6`
  - size bytes: `12316`
  - line count: `369`
  - source role: axis0 history-operator reconstruction suite runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_historyop_rec_suite_v1.json`
  - sha256: `dbbbe790cde1ac3461396ad39f192845188e744f4d406f03a41d5e9689186b9e`
  - size bytes: `73934`
  - line count: `2411`
  - source role: four-case reconstruction result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_historyop_rec_suite_v1.py`
- anchors:
  - `run_axis0_historyop_rec_suite_v1.py:1-369`
- source role:
  - one axis0 family runner that sweeps:
    - `4` reconstruction modes:
      - `REC_ID`
      - `REC_MARG`
      - `REC_MIX`
      - `REC_SCR`
    - `2` init modes:
      - `GINIBRE`
      - `BELL`
    - `2` axis3 signs:
      - `+1`
      - `-1`
    - `4` terrain sequences:
      - `SEQ01`
      - `SEQ02`
      - `SEQ03`
      - `SEQ04`
  - fixed runtime parameters:
    - seed `0`
    - trials `256`
    - cycles `16`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - terrain params `{gamma: 0.02, p: 0.02, q: 0.02}`
    - entangle reps `1`
  - emits one results file and one local `sim_evidence_pack.txt`
  - writes four local SIM_IDs:
    - `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`
    - `S_SIM_AXIS0_HISTORYOP_REC_MARG_V1`
    - `S_SIM_AXIS0_HISTORYOP_REC_MIX_V1`
    - `S_SIM_AXIS0_HISTORYOP_REC_SCR_V1`

### Result structure: `results_axis0_historyop_rec_suite_v1.json`
- top-level shape:
  - one `cases` map with `4` case entries
  - each case contains:
    - `4` run keys:
      - `BELL_s+1`
      - `BELL_s-1`
      - `GINIBRE_s+1`
      - `GINIBRE_s-1`
    - `4` stored sequences per run
    - one `DELTA_SEQ02_SEQ01` discriminator per run
- strongest bounded metrics:
  - largest `dMI_traj_mean_SEQ02_minus_SEQ01`:
    - `0.008794687193699025`
    - case `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`
    - run `BELL_s+1`
  - largest `ERR_traj` mean:
    - `0.5245462662009697`
    - case `S_SIM_AXIS0_HISTORYOP_REC_SCR_V1`
    - run `BELL_s-1`
    - sequence `SEQ03`
  - largest `dERR_traj_mean_SEQ02_minus_SEQ01`:
    - `0.009416131379654302`
    - case `S_SIM_AXIS0_HISTORYOP_REC_SCR_V1`
    - run `BELL_s+1`
  - strongest stored `MI_traj` mean:
    - `0.1923399902814273`
    - case `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`
    - run `BELL_s-1`
    - sequence `SEQ03`
  - lowest stored `SAgB_end` mean:
    - `0.6197164568830165`
    - case `S_SIM_AXIS0_HISTORYOP_REC_ID_V1`
    - run `BELL_s-1`
    - sequence `SEQ03`

### Reconstruction-mode split
- bounded read:
  - average `ERR_traj` mean by rec mode:
    - `REC_ID = 0.0`
    - `REC_MARG = 0.20640436952859126`
    - `REC_MIX = 0.3310559568545458`
    - `REC_SCR = 0.42241966974449235`
  - average `MI_traj` mean is unchanged across all four rec modes:
    - `0.12588103091253527`
  - `NEG_SAgB_end_frac` never rises above `0.0`
- bounded implication:
  - reconstruction choice strongly affects reconstruction error
  - the stored trajectory mutual-information summaries remain invariant under that same rec-mode split

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:44,135`
  - negative search for `axis0_historyop_rec_suite_v1` and `S_SIM_AXIS0_HISTORYOP_REC_*` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists both:
    - `axis0_historyop_rec_suite_v1` result file
    - `run_axis0_historyop_rec_suite_v1.py`
  - the repo-held top-level evidence pack contains no matching block for any of the four local SIM_IDs
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:44,135`
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
- bounded comparison read:
  - the closure audit identified this family as the first clean residual runner/result pair
  - the catalog confirms it is not stray filesystem noise
  - the evidence pack confirms current repo-top omission

## 5) Source-Class Read
- Best classification:
  - standalone residual axis0 reconstruction family with four local SIM_ID cases under one runner/result pair
- Not best classified as:
  - repo-top evidenced family
  - one of the later descendant axis0 suite surfaces
  - hygiene residue or orphan result output
- Theory-facing vs executable-facing split:
  - executable-facing:
    - runner simulates local history, terrain noise, one CNOT entangler, and four reconstruction policies
  - theory-facing:
    - the family isolates what changes when reconstruction fidelity is degraded while keeping trajectory MI summaries fixed
  - evidence-facing:
    - local evidence is explicit inside the runner contract
    - top-level evidence-pack admission is absent
- possible downstream consequence:
  - later residual intake can treat this as the first resolved paired-family unit inside the closure backlog and then move to `run_axis0_mi_discrim_branches.py`
