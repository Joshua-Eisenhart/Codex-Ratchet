# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_negsagb_stress_family__v1`
Extraction mode: `SIM_AXIS0_NEGSAGB_STRESS_PASS`

## T1) The full sweep executes all `3456` configurations and still stores `best.score = 0.0`
- source markers:
  - `run_axis0_negsagb_stress.py:188-247`
  - `results_axis0_negsagb_stress.json:1-380`
- tension:
  - the runner defines a full search over `3456` configurations
  - the early stop threshold is `best.score >= 0.05`
  - the stored result still has:
    - `records_count = 3456`
    - `best.score = 0.0`
- preserved read:
  - keep full-search exhaustion distinct from search success
- possible downstream consequence:
  - later summaries should treat this family as a failed negativity search, not as an incomplete sweep

## T2) The larger search family underperforms the smaller mutual-info baseline on stored negativity
- source markers:
  - `results_axis0_negsagb_stress.json:1-380`
  - `results_axis0_mutual_info.json:1-15`
- tension:
  - the current stress sweep stores zero negativity in its best record
  - the smaller mutual-info baseline stores:
    - `neg_SAgB_frac = 0.001953125`
    - `SAgB_min = -0.002114071978150056`
- preserved read:
  - search breadth does not automatically dominate baseline evidence quality
- possible downstream consequence:
  - later backlog work should keep the smaller baseline alive as a stronger stored negativity anchor

## T3) The result surface preserves only `best` plus a `10`-record sample, not the full search table
- source markers:
  - `run_axis0_negsagb_stress.py:252-315`
  - `results_axis0_negsagb_stress.json:1-380`
- tension:
  - the runner executes `3456` records
  - the stored output keeps:
    - one `best` record
    - `records_sample = records[:10]`
- preserved read:
  - compact result storage is not the same as full search trace retention
- possible downstream consequence:
  - later interpretation should stay within the preserved `best` and sample windows

## T4) The best record is defined by the negativity objective, but its residual branch deltas are tiny and mixed-sign
- source markers:
  - `results_axis0_negsagb_stress.json:1-380`
- tension:
  - best record deltas remain small:
    - `delta_MI_mean_SEQ02_minus_SEQ01 = -0.00030116171275254566`
    - `delta_SAgB_mean_SEQ02_minus_SEQ01 = 0.0003039874049425295`
    - `delta_negfrac_SEQ02_minus_SEQ01 = 0.0`
  - even the sample-level absolute maxima stay under `0.00038`
- preserved read:
  - do not over-read tiny branch deltas as compensating for the zero negativity score
- possible downstream consequence:
  - later summaries should foreground search failure over incidental micro-deltas

## T5) The family is catalog-visible and locally evidenced, but the repo-held top-level evidence pack omits it
- source markers:
  - `SIM_CATALOG_v1.3.md:48`
  - negative search for `axis0_negsagb_stress`, `S_SIM_AXIS0_NEGSAGB_STRESS`, `S_AXIS0_NEGSAGB_SWEEP_V1`, and `AX0_NEGSAGB_FAIL` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog lists the family
  - the runner emits a local evidence block
  - the repo-held top-level pack omits the local SIM_ID
- preserved read:
  - keep catalog presence, local evidence, and repo-top admission distinct
- possible downstream consequence:
  - later sims summaries should not mistake local evidence emission for top-level admission

## T6) This family advances the residual paired-family campaign, but the remaining residual classes stay separate
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `BATCH_sims_axis0_mutual_info_family__v1/MANIFEST.json`
- tension:
  - the paired-family campaign is advancing cleanly
  - result-only, runner-only, diagnostic, and hygiene residual classes remain outside this campaign
- preserved read:
  - keep paired-family intake separate from the other residual classes
- possible downstream consequence:
  - future work should continue pair-by-pair at `run_axis0_sagb_entangle_seed.py`
