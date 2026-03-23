# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis12_harden_v2_result_orphan_triplet__v1`
Extraction mode: `SIM_AXIS12_HARDEN_V2_RESULT_ORPHAN_PASS`
Batch scope: residual result-only axis12 harden `v2` triplet centered on `results_axis12_paramsweep_v2.json`, `results_axis12_altchan_v2.json`, and `results_axis12_negctrl_label_v2.json`, with the runner-only harden strip and the `v1` triplet preserved comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v2.json`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v2.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_altchan_v2.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_negctrl_label_v2.json`
- reason for bounded family:
  - the prior `v1` orphan batch explicitly deferred the `v2` triplet next
  - all three surfaces are declared by one successor runner contract:
    - `run_axis12_harden_v2_triple.py`
  - the three surfaces belong together as the second result-only half of the harden strip
  - `v2` should stay separate from `v1` because the stored schema changes and the third surface is no longer combinatorial
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_v2_triple.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- deferred next residual-priority source:
  - the next remaining result-only orphan beginning with:
    - `results_axis0_boundary_bookkeep_v1.json`

## 2) Source Membership
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_paramsweep_v2.json`
  - sha256: `b9b72a01a12d0b2a230fd6996026d247bedfd7f332d5e653e31fcf3a9a724f72`
  - size bytes: `1344`
  - line count: `75`
  - source role: compressed dynamic `v2` base-channel paramsweep surface
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_altchan_v2.json`
  - sha256: `c6b8194d29eaab38b30cf3d6aa5821b05a7d879f62909306d34efbbc63b5552c`
  - size bytes: `1196`
  - line count: `75`
  - source role: compressed dynamic `v2` alternate-channel realization surface
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis12_negctrl_label_v2.json`
  - sha256: `d15262a79fd4f114f86e14394fac249526ff4f77532b28d68c65d1b870ca0990`
  - size bytes: `1350`
  - line count: `75`
  - source role: compressed dynamic `v2` relabeled-channel negative-control surface

## 3) Structural Map Of The Family
### Result structure: `results_axis12_paramsweep_v2.json`
- anchors:
  - `results_axis12_paramsweep_v2.json:1-75`
  - `run_axis12_harden_v2_triple.py:171-181`
- source role:
  - compressed dynamic base-channel surface with:
    - `6` rows
    - axis3 signs `+1` and `-1`
    - `3` parameter points
    - `disc` summaries only
    - no `by_seq` layer
- strongest bounded reads:
  - the `seni` partition remains robust and positive on all six rows
  - strongest stored partition gap:
    - `dS = 0.002552123876453427`
    - `dP = -0.002452870920967354`
    - at `sign = +1`, `gamma = 0.12`, `p = 0.08`, `q = 0.1`
  - sign `+1` stays stronger on average than sign `-1`:
    - mean `dS` sign `+1` = `0.0013776134754462193`
    - mean `dS` sign `-1` = `0.0006795066665520692`
- bounded implication:
  - despite schema compression, the `v2` base-channel surface preserves the same high-parameter discriminative structure as the `v1` surface

### Result structure: `results_axis12_altchan_v2.json`
- anchors:
  - `results_axis12_altchan_v2.json:1-75`
  - `run_axis12_harden_v2_triple.py:183-193`
- source role:
  - compressed dynamic alternate-channel surface with the same six-row lattice
- strongest bounded reads:
  - the alternate-channel surface remains effectively collapsed to zero separation
  - all medium and high parameter rows store exact zeros:
    - `dS = 0.0`
    - `dP = 0.0`
  - only the weakest parameter point retains nonzero values, and they are tiny:
    - max absolute `dS = 7.83910577561997e-08`
  - the residual sign is the opposite of the `v1` weak-row sign:
    - `v1` weak-row `dS` values were tiny positive
    - `v2` weak-row `dS` values are tiny negative
- bounded implication:
  - the alternate-channel surface still kills the axis12 signal, and the remaining weak-row residual is sign-fragile noise rather than stable structure

### Result structure: `results_axis12_negctrl_label_v2.json`
- anchors:
  - `results_axis12_negctrl_label_v2.json:1-75`
  - `run_axis12_harden_v2_triple.py:195-205`
- source role:
  - compressed dynamic relabeled-channel negative-control surface with the same six-row lattice
- strongest bounded reads:
  - this is not a combinatorial control like `v1`
  - `dS` is negative on `5` of `6` rows
  - strongest absolute response:
    - `dS = -0.0007217115914999184`
    - `dP = 0.0006831974907078875`
    - at `sign = +1`, `gamma = 0.12`, `p = 0.08`, `q = 0.1`
  - one weak-row exception remains positive:
    - `sign = +1`, `gamma = 0.02`, `p = 0.02`, `q = 0.02`
    - `dS = 0.0001253657222393123`
- bounded implication:
  - the `v2` negative-control surface is a real dynamic rerun that partially inverts the base-channel pattern rather than simply renaming flags

### Cross-surface relation inside the triplet
- comparison anchors:
  - `run_axis12_harden_v2_triple.py:171-249`
- bounded read:
  - unlike `v1`, all three current surfaces share the same compressed `rows` plus `disc` schema
  - the price of that schema alignment is loss of `by_seq` detail
  - the three stored behaviors now separate cleanly by discriminator polarity:
    - `paramsweep_v2` keeps positive `dS`
    - `altchan_v2` collapses near zero
    - `negctrl_label_v2` is mostly negative
- bounded implication:
  - the `v2` triplet is more storage-homogeneous than `v1`, but less transparent about which sequences drive the stored differences

### `v1` vs `v2` seam
- comparison anchors:
  - `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
  - `run_axis12_harden_v2_triple.py:171-249`
- bounded read:
  - `paramsweep_v2` and `paramsweep_v1` are nearly identical at medium and high parameter points, but the weakest parameter rows drift materially upward in `v2`
  - `altchan_v2` and `altchan_v1` are identical zeros at medium and high parameter points, while the weak-row residual flips sign at tiny magnitude
  - the third surface changes class entirely:
    - `v1` third surface is combinatorial swapped flags only
    - `v2` third surface is a dynamic relabeled-channel rerun
- bounded implication:
  - the `v1` to `v2` transition is partly a numerical tightening pass and partly a real control-contract rewrite

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:61,63,66`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the top-level catalog lists all three filenames:
    - `results_axis12_altchan_v2.json`
    - `results_axis12_negctrl_label_v2.json`
    - `results_axis12_paramsweep_v2.json`
  - the catalog does not list their local SIM_ID strings
  - the repo-held top-level evidence pack omits both the filenames and the SIM_IDs
- bounded implication:
  - the `v2` triplet is catalog-visible by filename alias only and remains wholly unadmitted at the top-level evidence-pack layer

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis12_harden_v2_triple.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `BATCH_sims_axis12_harden_v1_result_orphan_triplet__v1/MANIFEST.json`
  - `BATCH_sims_axis12_harden_runner_strip__v1/MANIFEST.json`
  - `run_axis12_harden_v2_triple.py:171-249`
  - `SIM_CATALOG_v1.3.md:61,63,66`
- bounded comparison read:
  - the runner-only batch established the producer-side contract
  - the `v1` batch preserved the fuller, mixed-schema predecessor triplet
  - the current batch preserves the compressed successor triplet without broadening source membership back to the runner

## 5) Source-Class Read
- Best classification:
  - residual result-only `v2` harden successor triplet linked to the runner-only harden strip and preserved separately from the `v1` triplet
- Not best classified as:
  - a clean paired family
  - a mixed dynamic/combinatorial family
  - a top-level admitted sims family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - all three `v2` surfaces store only six-row discriminator summaries
    - base-channel separation survives
    - alternate-channel separation collapses
    - relabeled negative control becomes a dynamic rerun with mostly opposite-sign `dS`
  - theory-facing:
    - the storage compression removes sequence-level interpretability
    - the control rewrite changes what the third surface can say about the axis12 partition
  - evidence-facing:
    - the triplet is directly linked to the runner-only harden batch
    - top-level visibility is filename-only in the catalog and absent in the evidence pack
- possible downstream consequence:
  - the next residual pass should leave the harden strip and process the next remaining result-only orphan family beginning with `results_axis0_boundary_bookkeep_v1.json`
