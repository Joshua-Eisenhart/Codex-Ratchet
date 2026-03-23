# A2_3_SIM_DISTILLATES__v1
Status: PROPOSED / NONCANONICAL / SOURCE-BOUND DISTILLATE
Batch: `BATCH_sims_history_scan_strip_v11_to_reuse_v2__v1`
Extraction mode: `SIM_HISTORY_STRIP_PASS`

## Distillate D1
- strongest source-bound read:
  - this batch is best understood as one contiguous executable history-strip family with partial durable result storage, not as one uniformly evidenced sim family
- supporting anchors:
  - raw-folder-order strip membership
  - sole paired result surface `results_history_invariant_gradient_scan_v11.json`

## Distillate D2
- strongest source-bound read:
  - the `v11` baseline is currently split across two incompatible surfaces:
    - a minimal live runner
    - a richer stored depth-sweep result produced by a different code hash
- supporting anchors:
  - `run_history_invariant_gradient_scan_v11.py`
  - `results_history_invariant_gradient_scan_v11.json`

## Distillate D3
- strongest source-bound read:
  - the core theory-facing axis of the strip is stable even though implementations differ:
    - history invariance
    - order dependence
    - truncation sensitivity
    - reuse sensitivity
- supporting anchors:
  - `v12` through `v18`
  - `run_history_reuse_probe_v1.py`
  - `run_history_reuse_truncation_v2.py`

## Distillate D4
- evidence assumptions extracted:
  - catalog listing is weaker than top-level evidence-pack admission
  - local script prints are weaker than stored JSON result surfaces
  - current code hash equality should not be assumed when a result JSON embeds a conflicting producer hash
- supporting anchors:
  - `SIM_CATALOG_v1.3.md:104`
  - `results_history_invariant_gradient_scan_v11.json:1-35`
  - negative search across `SIM_EVIDENCE_PACK_autogen_v2.txt`

## Distillate D5
- runtime expectations extracted:
  - `v11` and `v12` look like lightweight evidence printers
  - `v13` is a wrapper and would recurse into itself if executed as written
  - `v13b` through reuse `v2` are more direct runtime surfaces and console-heavy
  - no durable result files were found for the later members of the strip
- supporting anchors:
  - source membership and structural map in this batch

## Distillate D6
- failure modes extracted:
  - treating the current `v11` runner as the exact producer of the stored depth curve
  - treating the whole strip as fully evidenced because one result file exists
  - ignoring the wrapper recursion and `EVIDENCE_SIGNAL` drift inside the middle of the strip
- supporting anchors:
  - tension items `T1` through `T5`
