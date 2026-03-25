# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / SIM-ONLY CLUSTER MAP
Batch: `BATCH_sims_history_scan_strip_v11_to_reuse_v2__v1`
Extraction mode: `SIM_HISTORY_STRIP_PASS`

## Cluster A
- cluster label:
  - invariant baseline pair
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_invariant_gradient_scan_v11.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_history_invariant_gradient_scan_v11.json`
- family role:
  - the only script-plus-result pair in the strip
- executable-facing read:
  - current runner is a minimal evidence printer
- stored-result-facing read:
  - result JSON is a seven-depth sweep with its own embedded code hash
- tension anchor:
  - current runner shape does not match the stored result payload

## Cluster B
- cluster label:
  - variant and order-perturbation runners
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_gradient_scan_v12.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_preserved_v13.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_preserved_v13b.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_scrambled_v14.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_variant_order_truncated_v15.py`
- family role:
  - introduces shuffled, preserved, scrambled, and truncated history variants
- executable-facing read:
  - mixed family of placeholder evidence printers, wrappers, and direct runtime scripts
- theory-facing read:
  - tests whether order preservation itself carries signal
- tension anchor:
  - `v13` is wrapper-recursive and `v13b` weakens the evidence contract

## Cluster C
- cluster label:
  - order-critical and self-operator comparison runners
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_order_critical_scan_v16.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_pair_order_coupling_scan_v17.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_self_operator_scan_v18.py`
- family role:
  - comparative middle strip for order criticality, pair coupling, and self-operator reuse
- executable-facing read:
  - direct runtime comparisons with no stored result surfaces found
- theory-facing read:
  - the batch pivots from single-scan placeholders into relational history probes
- tension anchor:
  - runtime semantics grow stronger while evidence admission stays absent

## Cluster D
- cluster label:
  - history-reuse tail
- members:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_reuse_probe_v1.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_history_reuse_truncation_v2.py`
- family role:
  - closes the strip by making reuse, record form, and truncation the direct variables
- executable-facing read:
  - still script-only in repo-held storage
- theory-facing read:
  - the family sharpens the difference between stored record history and operator-style reuse
- tension anchor:
  - reuse is central to the executable story but not to any top-level evidenced result block

## Cross-Cluster Read
- the strip is one executable family, not one uniformly evidenced family
- stored-result admission is highly asymmetric:
  - one result JSON for Cluster A
  - no stored result surfaces for Clusters B, C, or D
- theory-facing versus executable-facing split:
  - theory-facing:
    - history invariance
    - order dependence
    - reuse sensitivity
  - executable-facing:
    - placeholder evidence printer
    - recursive wrapper
    - runtime consoles
    - only one durable JSON result surface
