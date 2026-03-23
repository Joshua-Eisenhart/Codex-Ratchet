# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_history_scan_strip_v11_to_reuse_v2__v1`
Extraction mode: `SIM_HISTORY_STRIP_PASS`
Batch scope: contiguous history-scan and history-reuse script strip from `run_history_invariant_gradient_scan_v11.py` through `run_history_reuse_truncation_v2.py`, with only one stored result surface admitted
Date: 2026-03-08

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_invariant_gradient_scan_v11.py`
- selected sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_invariant_gradient_scan_v11.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_order_critical_scan_v16.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_pair_order_coupling_scan_v17.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_reuse_probe_v1.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_reuse_truncation_v2.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_self_operator_scan_v18.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_gradient_scan_v12.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_preserved_v13.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_preserved_v13b.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_scrambled_v14.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_truncated_v15.py`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_history_invariant_gradient_scan_v11.json`
- reason for bounded family:
  - this is the next unprocessed raw-folder-order strip after `run_full_axis_suite.py`
  - the selected scripts form one contiguous history-themed executable family:
    - invariant / variant gradients
    - preserved / scrambled / truncated order
    - order-critical and pair-order probes
    - self-operator and reuse probes
  - only one stored result surface exists inside the repo for this strip:
    - `results_history_invariant_gradient_scan_v11.json`
  - keeping the whole strip together preserves the executable family while keeping result-surface admission separate and partial
- comparison-only anchors read:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_oprole8_left_right_suite.py`

## 2) Source Membership
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_invariant_gradient_scan_v11.py`
  - sha256: `394d5d7df581a643dac55dd48579da63a548485bf604059e225317f7a489f911`
  - size bytes: `1341`
  - line count: `41`
  - source role: invariant baseline gradient placeholder runner
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_gradient_scan_v12.py`
  - sha256: `f20531df894b74355c8dabc84fda386081b7726e95201be442ecc840e0c18bc8`
  - size bytes: `1420`
  - line count: `48`
  - source role: shuffled-history gradient placeholder runner
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_preserved_v13.py`
  - sha256: `df47d90c2f248a12ffae46d238d7daa8ea025b0aabca5dc151be56a05d10e62c`
  - size bytes: `460`
  - line count: `19`
  - source role: wrapper launcher for preserved-order variants
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_preserved_v13b.py`
  - sha256: `7a7b5b1a32c4daf8ad37550e2d83c74f903072add2b8c5f4d2c90c90d33e4768`
  - size bytes: `1011`
  - line count: `43`
  - source role: growth-heavy preserved-order runtime surface
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_scrambled_v14.py`
  - sha256: `99ccabb193d6a53ba99c528ecc62c7b6ee7571fdfea3a621912c53050c2caf1c`
  - size bytes: `683`
  - line count: `25`
  - source role: scrambled-order runtime surface
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_truncated_v15.py`
  - sha256: `499d7f337e6bc02a895655c4125d9bd7a7c1a9028b576b531f474f22bd8f1f6a`
  - size bytes: `670`
  - line count: `26`
  - source role: truncated-order runtime surface
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_order_critical_scan_v16.py`
  - sha256: `92fa64fd023c01bb42f5b7c1161453d59e00b40ca204587c8fb94784b939c8bb`
  - size bytes: `680`
  - line count: `24`
  - source role: depth-indexed order-critical runtime surface
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_pair_order_coupling_scan_v17.py`
  - sha256: `d8c19c2ae0f309af52f628656727d4a06a6fb64b97e90df8e611976aafbc92f1`
  - size bytes: `936`
  - line count: `36`
  - source role: preserved-vs-scrambled pair-order runtime surface
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_self_operator_scan_v18.py`
  - sha256: `42b3da6e46cd7d678c1d9e216d0c1fbf00594d4187add4f1650179668b491468`
  - size bytes: `885`
  - line count: `35`
  - source role: data-only versus prefix-reuse runtime surface
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_reuse_probe_v1.py`
  - sha256: `ab538d44544441dde3892a6986223d977b2042160f74536a467831f1ad2b269e`
  - size bytes: `1375`
  - line count: `52`
  - source role: matrix-record versus operator-reuse probe
- Runner:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_reuse_truncation_v2.py`
  - sha256: `80246cce437e120dd0fa80f592bb1ec652f934d7f519fb3c7e118b56394718e0`
  - size bytes: `1175`
  - line count: `43`
  - source role: reuse plus depth-truncation runtime surface
- Result surface:
  - path: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_history_invariant_gradient_scan_v11.json`
  - sha256: `050f6a79848b07a28fc191db4a5da5cd23681fa814ea71f5fd476c59410ac6a9`
  - size bytes: `953`
  - line count: `35`
  - source role: only stored result surface found for the contiguous history strip

## 3) Structural Map Of The Family
### Baseline pair: `run_history_invariant_gradient_scan_v11.py` + `results_history_invariant_gradient_scan_v11.json`
- anchors:
  - `run_history_invariant_gradient_scan_v11.py:1-41`
  - `results_history_invariant_gradient_scan_v11.json:1-35`
- source role:
  - the current script is a tiny evidence-printer placeholder:
    - one SIM_ID
    - one `mi_mean`
    - one `mi_std`
    - one `gradient_sign`
    - no JSON write path
  - the stored result surface is a depth sweep with seven buckets:
    - depths `1, 2, 4, 8, 16, 32, 64`
    - each depth stores `mi_mean` and `mi_std`
  - stored result metadata preserves a separate producer path:
    - `CODE_HASH_SHA256 = 80d43b6dc7d6799fc13b317aa8bea5762d8bdadd5c6aeeea0568807e89acf918`
    - `OUTPUT_HASH_SHA256 = 2ee65124eec131ee8f5592354b75d1b21617e48a9eb1ee1a8ada55acd00bb36f`
- notable stored values:
  - `depth_1.mi_mean = 0.18764924632487293`
  - `depth_8.mi_mean = 0.06398529766810998`
  - `depth_64.mi_mean = 0.0021472392647626896`
  - the sequence is monotone-decaying across depth

### Variant-order strip: `v12`, `v13`, `v13b`, `v14`, `v15`
- anchors:
  - `run_history_variant_gradient_scan_v12.py:1-48`
  - `run_history_variant_order_preserved_v13.py:1-19`
  - `run_history_variant_order_preserved_v13b.py:1-43`
  - `run_history_variant_order_scrambled_v14.py:1-25`
  - `run_history_variant_order_truncated_v15.py:1-26`
- source role:
  - `v12` mirrors the small `v11` template but switches to a shuffled-history variant and seed `1`
  - `v13` is a wrapper launcher rather than a direct sim surface
  - `v13b` is the first clearly heavier preserved-order runtime surface in the strip
  - `v14` and `v15` isolate scrambled-order and truncated-order cases as direct runtime programs
- structural risks:
  - `v13` includes itself inside `SCRIPTS`, so execution would recurse into itself
  - `v13b` does not emit `EVIDENCE_SIGNAL`
  - `v13b` prints `H_LEN` every step, making it executable-facing but evidence-contract-weak

### Order / coupling / self-operator strip: `v16`, `v17`, `v18`
- anchors:
  - `run_history_order_critical_scan_v16.py:1-24`
  - `run_history_pair_order_coupling_scan_v17.py:1-36`
  - `run_history_self_operator_scan_v18.py:1-35`
- source role:
  - these runners pivot the family from simple gradient placeholders toward runtime comparisons:
    - depth-indexed order criticality
    - preserved-vs-scrambled pair coupling
    - data-only versus prefix-reuse self-operator behavior
- bounded read:
  - no paired result JSONs were found for these later strip members
  - their semantics stay executable-facing and comparative rather than stored-result-facing

### Reuse pair: `run_history_reuse_probe_v1.py` + `run_history_reuse_truncation_v2.py`
- anchors:
  - `run_history_reuse_probe_v1.py:1-52`
  - `run_history_reuse_truncation_v2.py:1-43`
- source role:
  - these close the strip by making reuse itself the direct variable:
    - matrix-record versus operator reuse
    - depth sweep versus reuse truncation
- bounded read:
  - they belong to the same executable family because they preserve the same history/reuse theme and sit contiguously in raw folder order
  - no stored result surfaces were found for either one

## 4) Comparison Anchors
- comparison sources:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:104`
  - `SIM_CATALOG_v1.3.md:155`
- bounded comparison read:
  - the catalog explicitly maps `history_invariant_gradient_scan_v11` to `results_history_invariant_gradient_scan_v11.json`
  - the catalog's suggested order places the history scans later as their own stage family
  - searching the repo-held top-level evidence pack found no block for any SIM_ID in this strip:
    - `S_SIM_HISTORY_INVARIANT_GRADIENT_SCAN_V11`
    - `S_SIM_HISTORY_VARIANT_GRADIENT_SCAN_V12`
    - `S_SIM_HISTORY_VARIANT_ORDER_PRESERVED_V13B`
    - `S_SIM_HISTORY_VARIANT_ORDER_SCRAMBLED_V14`
    - `S_SIM_HISTORY_VARIANT_ORDER_TRUNCATED_V15`
    - `S_SIM_HISTORY_ORDER_CRITICAL_SCAN_V16`
    - `S_SIM_HISTORY_PAIR_ORDER_COUPLING_SCAN_V17`
    - `S_SIM_HISTORY_SELF_OPERATOR_SCAN_V18`
    - `S_SIM_HISTORY_REUSE_PROBE_V1`
    - `S_SIM_HISTORY_REUSE_TRUNCATION_V2`

## 5) Source-Class Read
- Best classification:
  - contiguous executable history-strip family with partial result admission and weak top-level evidence admission
- Not best classified as:
  - one fully evidenced family
  - one single current producer path
  - same source family as the earlier cross-axis sampler batch
- Theory-facing vs executable-facing split:
  - executable-facing:
    - the script strip is dominated by runtime probes, wrappers, and console-print evidence behavior
    - only one repo-held result JSON exists for the strip
  - theory-facing:
    - the family is probing how order, truncation, reuse, and self-operator choices affect history sensitivity
  - evidence-facing:
    - catalog admission exists for `v11`
    - top-level evidence-pack admission is absent across the strip
- possible downstream consequence:
  - later sims interpretation should treat this batch as a partially materialized executable family with preserved provenance gaps, not as a settled evidenced theory cluster
