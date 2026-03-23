# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_history_scan_strip_v11_to_reuse_v2__v1`
Extraction mode: `SIM_HISTORY_STRIP_PASS`

## T1) Current `v11` runner vs stored `v11` result surface
- source markers:
  - `run_history_invariant_gradient_scan_v11.py:1-41`
  - `results_history_invariant_gradient_scan_v11.json:1-35`
- tension:
  - the current runner prints one evidence triple and no JSON
  - the stored result is a seven-depth sweep with embedded `CODE_HASH_SHA256 = 80d43b6d...`
- preserved read:
  - do not collapse the current file and stored result into one clean producer path
- possible downstream consequence:
  - later provenance claims should treat `v11` as a live mismatch surface

## T2) One contiguous executable family vs only one stored result surface
- source markers:
  - raw-folder-order history strip in `simpy`
  - `results_history_invariant_gradient_scan_v11.json`
- tension:
  - the scripts form one contiguous family from `v11` through reuse `v2`
  - only `v11` has a repo-held paired result surface
- preserved read:
  - keep script-family membership separate from stored-result admission
- possible downstream consequence:
  - later summaries should not overstate result coverage across the full strip

## T3) `v13` is a wrapper but includes itself in its own launch list
- source markers:
  - `run_history_variant_order_preserved_v13.py:1-19`
- tension:
  - `v13` is not a direct sim implementation
  - its `SCRIPTS` list includes `run_history_variant_order_preserved_v13.py` itself
- preserved read:
  - execution semantics are recursive / unsafe if run as written
- possible downstream consequence:
  - treat `v13` as a control-surface artifact, not as clean evidencing machinery

## T4) `v13b` preserves the history theme but drifts from the small evidence-printer contract
- source markers:
  - `run_history_variant_order_preserved_v13b.py:1-43`
- tension:
  - `v13b` appears to be the heavier preserved-order runtime implementation
  - it does not emit `EVIDENCE_SIGNAL` and prints `H_LEN` every step
- preserved read:
  - preserve the contract drift instead of smoothing `v13b` into the same evidence style as `v11` / `v12`
- possible downstream consequence:
  - later executable audits should distinguish contract-light console traces from evidence-pack-ready outputs

## T5) Catalog admission exists, but top-level evidence-pack admission does not
- source markers:
  - `SIM_CATALOG_v1.3.md:104`
  - `SIM_CATALOG_v1.3.md:155`
  - search across `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog recognizes `history_invariant_gradient_scan_v11` and stages the history scans as a family
  - the repo-held top-level evidence pack contains no block for any SIM_ID in this strip
- preserved read:
  - keep catalog presence distinct from top-level evidence-pack admission
- possible downstream consequence:
  - this family should stay proposal-side in provenance strength

## T6) Theory-facing history questions vs executable heterogeneity
- source markers:
  - script strip membership in this batch
- tension:
  - theory-facing concern is coherent:
    - history invariance
    - order preservation
    - truncation
    - reuse
  - executable-facing realization is heterogeneous:
    - tiny placeholder scripts
    - recursive wrapper
    - heavier console runtimes
    - one lone durable JSON result
- preserved read:
  - do not pretend one uniform runtime contract exists across the strip
- possible downstream consequence:
  - later distillates should separate question-family coherence from implementation-family inconsistency

## T7) The stored `v11` result implies a depth law that the current runner no longer expresses
- source markers:
  - `results_history_invariant_gradient_scan_v11.json:1-35`
  - `run_history_invariant_gradient_scan_v11.py:1-41`
- tension:
  - stored `mi_mean` decays from `0.18764924632487293` at depth `1` to `0.0021472392647626896` at depth `64`
  - the current runner exposes only one draw-derived triple and no depth sweep
- preserved read:
  - the result surface carries a stronger theory-facing claim than the present script implementation
- possible downstream consequence:
  - later consumers should avoid using the current runner as if it transparently reproduces the stored decay curve
