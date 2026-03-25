# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_negsagb_stress_family__v1`
Extraction mode: `SIM_AXIS0_NEGSAGB_STRESS_PASS`
Batch scope: standalone residual axis0 negativity-stress sweep family centered on `run_axis0_negsagb_stress.py` and `results_axis0_negsagb_stress.json`, with top-level visibility, mutual-info baseline comparison, and residual continuity held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
- reason for bounded family:
  - the prior mutual-info batch deferred this pair as the next clean residual runner/result unit
  - one runner emits one paired result surface with one local SIM_ID
  - the current file is the first residual axis0 pair whose main contract is an explicit search over parameter space rather than one stored baseline or one branch pair
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mutual_info.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mutual_info_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_sagb_entangle_seed.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - sha256: `43500c562680ce7b5f80516d3187f6525161ed0088d302fe7f44a9eb241883df`
  - size bytes: `11182`
  - line count: `316`
  - source role: axis0 negativity-stress sweep runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
  - sha256: `43e447a611618da0081acb9e8df6faf7f78010b5e4a14febc3b99acd37b6cdea`
  - size bytes: `11155`
  - line count: `380`
  - source role: compact best-plus-sample stress result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_negsagb_stress.py`
- anchors:
  - `run_axis0_negsagb_stress.py:1-316`
- source role:
  - one axis0 search runner comparing:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
  - fixed knobs:
    - seed `0`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - trials `512`
  - sweep knobs:
    - axis3 sign `+1`, `-1`
    - cycles `8`, `16`, `32`, `64`
    - gamma `0.02`, `0.05`, `0.08`, `0.12`
    - p `0.02`, `0.05`, `0.08`
    - q `0.02`, `0.05`, `0.10`
    - entangler `CNOT`, `CZ`
    - entangle reps `1`, `2`, `4`
    - entangle position `BEFORE`, `AFTER`
  - total stored search width:
    - `3456` records
  - local objective:
    - maximize mean branch negativity fraction
      - `score = 0.5 * (SEQ01.neg_SAgB_frac + SEQ02.neg_SAgB_frac)`
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_NEGSAGB_STRESS`

### Result structure: `results_axis0_negsagb_stress.json`
- top-level shape:
  - fixed knobs
  - one `best` record
  - `records_count = 3456`
  - `records_sample` containing only the first `10` records
- strongest stored read:
  - `best.score = 0.0`
  - best record parameters:
    - axis3 sign `1`
    - cycles `8`
    - gamma `0.02`
    - p `0.02`
    - q `0.02`
    - entangler `CNOT`
    - entangle reps `1`
    - entangle position `BEFORE`
  - best-record branch metrics:
    - `SEQ01.neg_SAgB_frac = 0.0`
    - `SEQ02.neg_SAgB_frac = 0.0`
    - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
    - `delta_MI_mean_SEQ02_minus_SEQ01 = -0.00030116171275254566`
    - `delta_SAgB_mean_SEQ02_minus_SEQ01 = 0.0003039874049425295`
- bounded implication:
  - the full stored sweep fails to produce any positivity in its own negativity objective
  - the result surface preserves best plus sample, not the entire search table

### Search-failure and storage-compression split
- bounded read:
  - early stop condition exists:
    - break if `best.score >= 0.05`
  - stored `records_count = 3456` matches the full sweep width, so no early stop was triggered
  - the output still compresses the full sweep into:
    - one `best` record
    - `10` sampled records
- sample-level extrema preserved:
  - sample absolute max `delta_MI_mean_SEQ02_minus_SEQ01`:
    - `0.0003737679379132719`
    - `CZ`, reps `1`, `AFTER`, cycles `8`, params `{gamma: 0.02, p: 0.02, q: 0.02}`
  - sample absolute max `delta_SAgB_mean_SEQ02_minus_SEQ01`:
    - `-0.00037998941985362134`
    - same sample setting

### Boundary to the mutual-info baseline
- comparison anchors:
  - `run_axis0_mutual_info.py:1-141`
  - `results_axis0_mutual_info.json:1-15`
  - `BATCH_sims_axis0_mutual_info_family__v1/MANIFEST.json`
- bounded comparison read:
  - the smaller mutual-info baseline stores:
    - `neg_SAgB_frac = 0.001953125`
    - `SAgB_min = -0.002114071978150056`
  - the larger stress sweep stores:
    - `best.score = 0.0`
    - no negativity in its best record
  - the larger search family therefore does not dominate the smaller baseline on the stored negativity objective

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:48`
  - negative search for `axis0_negsagb_stress`, `S_SIM_AXIS0_NEGSAGB_STRESS`, `S_AXIS0_NEGSAGB_SWEEP_V1`, and `AX0_NEGSAGB_FAIL` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists the negativity-stress family
  - the repo-held top-level evidence pack contains no current block for the local SIM_ID
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mutual_info.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mutual_info_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:48`
  - `BATCH_sims_axis0_mutual_info_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior mutual-info batch set this pair as next in queue
  - the current family is the first stored axis0 search surface that clearly fails its intended negativity objective
  - the smaller baseline remains the correct anchor for that failure

## 5) Source-Class Read
- Best classification:
  - standalone axis0 negativity-search family with one compressed best-plus-sample result surface
- Not best classified as:
  - a successful negativity-producing family
  - a full retained search log
  - repo-top evidenced surface
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner performs a full parameter sweep over `3456` search records
  - theory-facing:
    - the stored search failure matters more than any tiny branch delta in the best record
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission is absent
    - the stored output compresses the search to `best` plus `records_sample`
- possible downstream consequence:
  - later residual intake should treat this family as a failed negativity-search surface and let `run_axis0_sagb_entangle_seed.py` begin the next bounded pair
