# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_axis0_mutual_info_family__v1`
Extraction mode: `SIM_AXIS0_MUTUAL_INFO_PASS`
Batch scope: standalone residual axis0 mutual-information baseline family centered on `run_axis0_mutual_info.py` and `results_axis0_mutual_info.json`, with top-level visibility, residual continuity, and the adjacent negativity-stress sweep held comparison-only
Date: 2026-03-09

## 1) Batch Selection
- starting residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mutual_info.json`
- reason for bounded family:
  - the prior AB branch batch deferred this pair as the next clean residual runner/result unit
  - one runner emits one paired result surface with one local SIM_ID
  - the adjacent `run_axis0_negsagb_stress.py` is a large sweep family with a different search-style contract and therefore starts the next bounded family
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mi_discrim_branches_ab_family__v1/MANIFEST.json`
- deferred next residual-priority source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_mutual_info.py`
  - sha256: `6728b3e9b606c5c92a87f68fb3097d5a33a79d5403d8533a0601d3211ead9bf4`
  - size bytes: `4179`
  - line count: `141`
  - source role: axis0 mutual-information baseline runner
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_mutual_info.json`
  - sha256: `d13a11ea5d3b25133c5f48010704e4fbf7e5f470748f1ef8fc5738bc7e5fe56a`
  - size bytes: `406`
  - line count: `15`
  - source role: compact baseline MI result surface

## 3) Structural Map Of The Family
### Runner contract: `run_axis0_mutual_info.py`
- anchors:
  - `run_axis0_mutual_info.py:1-141`
- source role:
  - one direct mutual-information baseline runner over unconstrained Ginibre two-qubit states
  - fixed runtime parameters:
    - seed `0`
    - trials `512`
  - per trial, computes:
    - `SAB`
    - `SA`
    - `SB`
    - `MI`
    - `S(A|B)`
  - emits one local SIM_ID:
    - `S_SIM_AXIS0_MI_TEST`
  - local evidence gate:
    - writes `KILL_SIGNAL S_AXIS0_CAND_MI_V1 CORR AX0MI_FAIL` only if `neg_SAgB_frac == 0.0`

### Result structure: `results_axis0_mutual_info.json`
- top-level shape:
  - one compact `metrics` map
  - no branch split
  - no terrain sequence split
- strongest bounded metrics:
  - `MI_mean = 0.2724236385732822`
  - `MI_min = 0.07228029839730787`
  - `MI_max = 0.5763919004845633`
  - `SAgB_mean = 0.3323080185492987`
  - `SAgB_min = -0.002114071978150056`
  - `SAgB_max = 0.5886320431593128`
  - `neg_SAgB_frac = 0.001953125`
- bounded implication:
  - the current baseline does produce negative conditional entropy, but only barely:
    - `0.001953125 = 1 / 512`
  - because the stored negativity fraction is nonzero, the runner’s local `KILL_SIGNAL` branch would not fire for this stored output

### Boundary to `negsagb_stress`
- comparison anchors:
  - `run_axis0_negsagb_stress.py:1-260`
  - `results_axis0_negsagb_stress.json:1-220`
- bounded comparison read:
  - the adjacent stress family is a large sweep over:
    - axis3 sign
    - cycles
    - gamma / p / q
    - entangler
    - entangle repetitions
    - entangle position
  - the current baseline stores one tiny nonzero negativity fraction:
    - `0.001953125`
  - the stored stress best score is exactly:
    - `0.0`
  - both branch fractions in the best stress record remain:
    - `SEQ01.neg_SAgB_frac = 0.0`
    - `SEQ02.neg_SAgB_frac = 0.0`
  - the next file therefore begins a new search-style family rather than extending this baseline batch

### Top-level visibility relation
- comparison anchors:
  - `SIM_CATALOG_v1.3.md:47`
  - negative search for `axis0_mutual_info`, `S_SIM_AXIS0_MI_TEST`, `S_AXIS0_CAND_MI_V1`, and `AX0MI_FAIL` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- bounded read:
  - the catalog lists the mutual-info result surface
  - the repo-held top-level evidence pack contains no current block for the local SIM_ID or kill token
  - this leaves the family catalog-visible and locally evidenced, but not repo-top admitted

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_axis0_negsagb_stress.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_axis0_negsagb_stress.json`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_axis0_mi_discrim_branches_ab_family__v1/MANIFEST.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:47`
  - `BATCH_sims_axis0_mi_discrim_branches_ab_family__v1/MANIFEST.json`
- bounded comparison read:
  - the prior AB branch batch set this pair as next in queue
  - the current baseline is much smaller and simpler than the adjacent stress sweep
  - the stress family is the right next boundary because it unexpectedly fails to improve on the current baseline’s tiny negativity event

## 5) Source-Class Read
- Best classification:
  - standalone axis0 mutual-information baseline family with one compact local SIM_ID surface
- Not best classified as:
  - repo-top evidenced surface
  - a branch-family continuation
  - a failed mutual-information candidate under the currently stored output
- Theory-facing vs executable-facing split:
  - executable-facing:
    - current runner directly samples Ginibre two-qubit states and computes one-shot entropy relations
  - theory-facing:
    - current output shows positive mean MI with a tiny but nonzero negative conditional-entropy tail
  - evidence-facing:
    - local evidence is explicit in the runner contract
    - the kill path exists but is not triggered by the stored result
    - repo-top evidence-pack admission is absent
- possible downstream consequence:
  - later residual intake should treat this family as a minimal baseline anchor and let `run_axis0_negsagb_stress.py` begin the next bounded search-style pair
