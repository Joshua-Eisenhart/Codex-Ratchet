# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / INVENTORY-BOUND CLOSURE AUDIT
Batch: `BATCH_sims_residual_inventory_closure_audit__v1`
Extraction mode: `SIM_RESIDUAL_CLOSURE_AUDIT_PASS`
Batch scope: residual sims-side inventory closure audit after raw-order `simpy` family exhaustion, bounded to filename-level coverage accounting rather than new family extraction
Date: 2026-03-09

## 1) Batch Selection
- starting state:
  - the raw-order `simpy` family campaign is already exhausted at `run_ultra_axis0_ab_axis6_sweep.py`
  - `17` prior `BATCH_sims_*` directories already exist
  - those prior batches admit `76` sims files as direct source members
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- reason for bounded closure batch:
  - no later raw-order `simpy` family remains
  - a residual inventory still exists outside source membership
  - this pass is therefore a coverage audit, not a new executable family batch
- inventory method:
  - filename-level inventory only across:
    - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims`
    - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy`
    - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson`
  - prior sims manifests were checked only to distinguish:
    - direct source membership
    - comparison-anchor-only reuse
    - never-referenced residuals
- deferred next raw-folder-order source:
  - none

## 2) Source Membership
- Catalog anchor:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - sha256: `0875a516fe8ed7d7ca5724b6655d13c5b07eb4b580829e598dce97e833254748`
  - size bytes: `7893`
  - line count: `158`
  - source role: top-level sims inventory spine used to confirm residual families are still catalog-visible
- Evidence-pack anchor:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - sha256: `63b7e2029a9a3f5b06294b301ffcc62dd386077bed0ff4a3b9ef561b9f99140a`
  - size bytes: `30407`
  - line count: `663`
  - source role: repo-held top-level admission surface used to compare residual local families against current evidence visibility

## 3) Structural Map Of Residual Coverage
### Coverage totals
- current coverage read:
  - total sims files present: `120`
  - direct sims source members across prior batches: `76`
  - residual sims-side files not admitted as direct source members: `44`
  - residual by directory:
    - top level: `1`
    - `simpy`: `21`
    - `simson`: `22`

### Residual paired runner/result families: `12`
- paired residual families:
  - `axis0_historyop_rec_suite_v1`
  - `axis0_mi_discrim_branches`
  - `axis0_mi_discrim_branches_ab`
  - `axis0_mutual_info`
  - `axis0_negsagb_stress`
  - `axis0_sagb_entangle_seed`
  - `axis0_traj_corr_metrics`
  - `axis0_traj_corr_suite`
  - `axis12_channel_realization_suite`
  - `axis12_seq_constraints`
  - `axis12_topology4_channelfamily_suite_v2`
  - `axis12_topology4_channelgrid_v1`
- bounded read:
  - these are real executable/result siblings that still exist outside direct source membership
  - raw-order family extraction did not consume them as standalone batches

### Residual paired families already used as comparison anchors elsewhere: `4`
- anchor-only runner list:
  - `run_axis0_traj_corr_suite.py`
  - `run_axis12_channel_realization_suite.py`
  - `run_axis12_seq_constraints.py`
  - `run_axis12_topology4_channelfamily_suite_v2.py`
- bounded read:
  - these four runners were already comparison-read in earlier sims manifests
  - they still never became direct source members themselves
  - their descendant or sibling result surfaces were instead carried by suite-level batches

### Residual runner-only executable surfaces: `2`
- runner-only residuals:
  - `run_axis12_harden_triple_v1.py`
  - `run_axis12_harden_v2_triple.py`
- bounded read:
  - both remain executable-facing residuals with no direct residual result sibling present in the current inventory

### Residual result-only surfaces: `10`
- result-only residuals:
  - `results_axis0_boundary_bookkeep_v1.json`
  - `results_axis0_traj_corr_suite_v2.json`
  - `results_axis12_altchan_v1.json`
  - `results_axis12_altchan_v2.json`
  - `results_axis12_negctrl_label_v2.json`
  - `results_axis12_negctrl_swap_v1.json`
  - `results_axis12_paramsweep_v1.json`
  - `results_axis12_paramsweep_v2.json`
  - `results_ultra3_full_geometry_stage16_axis0.json`
  - `results_ultra_big_ax012346.json`
- bounded read:
  - these surfaces remain in the repo with no matching residual runner in the current closure set
  - they should be treated as orphan or deferred result artifacts until separately re-bounded

### Residual diagnostics, proofs, and hygiene artifacts: `8`
- diagnostic or proof scripts:
  - `mega_sims_failure_detector.py`
  - `mega_sims_run_02.py`
  - `mega_sims_trivial_check.py`
  - `prove_foundation.py`
- cache and noise artifacts:
  - `.DS_Store`
  - `__pycache__/ run_axis0_boundary_bookkeep_sweep_v2.cpython-313.pyc`
  - `__pycache__/ run_axis12_axis0_link_v1.cpython-313.pyc`
  - `__pycache__/ run_mega_axis0_ab_stage16_axis6.cpython-313.pyc`
- bounded read:
  - these files are inside the sims tree but should not be conflated with validated runner/result family coverage

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_sim_suite_v1_descendant_bundle__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_sims_sim_suite_v2_successor_bundle__v1/MANIFEST.json`
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/BATCH_INDEX__v1.md`
- relevant anchors:
  - `BATCH_sims_ultra_axis0_ab_axis6_sweep_family__v1/MANIFEST.json`
  - `BATCH_sims_sim_suite_v1_descendant_bundle__v1/MANIFEST.json:32-40`
  - `BATCH_sims_sim_suite_v2_successor_bundle__v1/MANIFEST.json:31-39`
- bounded comparison read:
  - raw-order exhaustion was already established in the final ultra sweep batch
  - the suite-level batches for V1 and V2 already comparison-read:
    - `run_axis0_traj_corr_suite.py`
    - `run_axis12_channel_realization_suite.py`
    - `run_axis12_seq_constraints.py`
    - `run_axis12_topology4_channelfamily_suite_v2.py`
  - comparison reuse did not promote those runners into direct source membership

## 5) Source-Class Read
- Best classification:
  - residual inventory closure audit over the separate sims source class after raw-order family exhaustion
- Not best classified as:
  - one more executable family batch
  - content-level extraction of all `44` residual files
  - proof that every residual artifact is obsolete or invalid
- Theory-facing vs executable-facing split:
  - executable-facing:
    - `12` paired runner/result families remain outside direct source membership
    - `2` residual runner-only surfaces remain
    - `10` residual result-only surfaces remain
  - theory-facing:
    - the catalog still names many of these surfaces
    - the repo-held evidence pack emphasizes descendant or renamed SIM_IDs instead of local parent families
  - hygiene-facing:
    - `.DS_Store` and committed `__pycache__` files remain inside the sims tree
- possible downstream consequence:
  - if later residual work is requested, it should begin by prioritizing the `12` residual paired runner/result families rather than pretending the sims source class is fully covered
