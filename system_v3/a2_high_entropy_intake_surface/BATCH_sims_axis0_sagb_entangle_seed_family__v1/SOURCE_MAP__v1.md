# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_sagb_entangle_seed_family__v1`
Extraction mode: `SIM_AXIS0_SAGB_ENTANGLE_SEED_PASS`
Batch scope: standalone residual axis0 conditional-entropy entangle-seed family centered on `run_axis0_sagb_entangle_seed.py` and `results_axis0_sagb_entangle_seed.json`, with top-level visibility, negativity-stress continuity, and the next trajectory-correlation pair held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_sagb_entangle_seed.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_sagb_entangle_seed.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_sagb_entangle_seed.json`
- reason for bounded family:
  - the prior negativity-stress batch deferred this pair as the next clean residual runner/result unit
  - one runner emits one paired result surface with one local SIM_ID
  - the current family switches from sweep-search mode to a fixed Bell-seed / weak-noise / repeated-CNOT contract and therefore deserves its own bounded batch
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_negsagb_stress_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_traj_corr_metrics.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_sagb_entangle_seed.py`
  - sha256: `e2b6a23faf45685717d3616a98979c1b7f913c35c1f89726a0ae56f8d130c598`
  - size bytes: `7801`
  - line count: `239`
  - source role: Bell-seed entangle-based `SAgB` probe runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_sagb_entangle_seed.json`
  - sha256: `fc9ddd640da82057ce9ec6eb74bcb5b6b421a71bf6045484f8eac52496cfe649`
  - size bytes: `1045`
  - line count: `50`
  - source role: compact two-branch entangle-seed result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_sagb_entangle_seed.py`
- anchors:
  - `run_axis0_sagb_entangle_seed.py:1-239`
- source role:
  - one axis0 branch family comparing:
    - `SEQ01 = [Se, Ne, Ni, Si]`
    - `SEQ02 = [Se, Si, Ni, Ne]`
  - fixed runtime parameters:
    - seed `0`
    - trials `512`
    - cycles `64`
    - axis3 sign `+1`
    - theta `0.07`
    - n-vector `(0.3, 0.4, 0.866025403784)`
    - terrain params `{gamma: 0.005, p: 0.005, q: 0.005}`
    - entangle reps `2`
  - seed contract:
    - every trial starts from a Bell-state seed with randomized local-unitary scramble
  - update contract:
    - local axis unitary on `A`
    - terrain CPTP map on `A`
    - repeated `CNOT` coupling after every terrain step
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_SAGB_ENTANGLE_SEED`

### Result structure: `results_axis0_sagb_entangle_seed.json`
- top-level shape:
  - one compact result surface with:
    - `metrics_SEQ01`
    - `metrics_SEQ02`
    - `delta_MI_mean_SEQ02_minus_SEQ01`
    - `delta_SAgB_min_SEQ02_minus_SEQ01`
    - `delta_negfrac_SEQ02_minus_SEQ01`
- strongest bounded metrics:
  - `metrics_SEQ01.MI_mean = 0.15475852409818908`
  - `metrics_SEQ02.MI_mean = 0.1547682464204621`
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 9.72232227303138e-06`
  - `metrics_SEQ01.SAgB_min = 0.5233202368566191`
  - `metrics_SEQ02.SAgB_min = 0.5232934814069777`
  - `delta_SAgB_min_SEQ02_minus_SEQ01 = -2.675544964136911e-05`
  - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
  - `metrics_SEQ01.neg_SAgB_frac = 0.0`
  - `metrics_SEQ02.neg_SAgB_frac = 0.0`
- bounded implication:
  - the current family keeps both branches strictly positive in stored `S(A|B)`
  - branch discrimination is tiny but nonzero in both MI mean and `SAgB` minimum

### Near-deterministic trial behavior
- bounded read:
  - per-branch stored ranges are effectively floating-point noise:
    - `metrics_SEQ01.MI_max - MI_min = 2.6645352591003757e-15`
    - `metrics_SEQ02.MI_max - MI_min = 2.6645352591003757e-15`
    - `metrics_SEQ01.SAgB_max - SAgB_min = 2.55351295663786e-15`
    - `metrics_SEQ02.SAgB_max - SAgB_min = 2.4424906541753444e-15`
- bounded implication:
  - despite randomized local scrambles at seed time, the stored branch summaries are effectively deterministic across `512` trials

### Boundary to the prior negativity-stress sweep
- comparison anchors:
  - `run_axis0_negsagb_stress.py:1-316`
  - `results_axis0_negsagb_stress.json:1-380`
  - `BATCH_sims_axis0_negsagb_stress_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior stress family explored `3456` settings and still stored:
    - `best.score = 0.0`
  - the current fixed-seed family also stores:
    - `SEQ01.neg_SAgB_frac = 0.0`
    - `SEQ02.neg_SAgB_frac = 0.0`
  - the current family is not a search failure surface, but a fixed-contract surface whose output remains strictly positive in stored `S(A|B)`

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:49`
  - negative search for `axis0_sagb_entangle_seed` and `S_SIM_AXIS0_SAGB_ENTANGLE_SEED` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists the entangle-seed family
  - the repo-held top-level evidence pack contains no current block for the local SIM_ID
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_negsagb_stress_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:49`
  - `BATCH_sims_axis0_negsagb_stress_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior stress batch set this pair as next in queue
  - the current family narrows from a sweep to one fixed Bell-seed contract
  - the next residual pair should therefore move to the trajectory-correlation metric family rather than merge that distinct contract here

## 5) Source-Class Read
- Best classification:
  - standalone Bell-seed entangle-based conditional-entropy family with one compact local SIM_ID surface
- Not best classified as:
  - a successful negativity-producing family
  - a search sweep
  - repo-top evidenced surface
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner is a fixed contract over Bell seeds, weak noise, and repeated CNOT coupling
  - theory-facing:
    - current output preserves branch-level MI and `SAgB` differences without any stored negativity
    - trial-to-trial variation collapses to floating-point noise
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - repo-top evidence-pack admission is absent
- possible downstream consequence:
  - later residual intake should treat this family as a deterministic-seeming positive-`SAgB` entangle seed surface and let `run_axis0_traj_corr_metrics.py` begin the next bounded pair
