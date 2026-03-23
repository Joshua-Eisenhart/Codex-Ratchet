# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_axis0_mi_discrim_branches_family__v1`
Extraction mode: `SIM_AXIS0_MI_DISCRIM_BRANCHES_PASS`

## T1) The runner emits one explicit local SIM_ID evidence block, but the repo-held top-level evidence pack omits it
- source markers:
  - `run_axis0_mi_discrim_branches.py:197-223`
  - negative search for `axis0_mi_discrim_branches` and `S_SIM_AXIS0_MI_DISCRIM_BRANCHES` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_CATALOG_v1.3.md:45`
- tension:
  - the runner writes one local evidence block for `S_SIM_AXIS0_MI_DISCRIM_BRANCHES`
  - the catalog lists the family
  - the repo-held evidence pack still contains no matching block
- preserved read:
  - keep local evidence emission distinct from repo-top admission
- possible downstream consequence:
  - later sims summaries should treat this family as source-real but not top-level evidenced

## T2) The file is named as an MI discriminator, but the stored MI layer is effectively machine-zero
- source markers:
  - `results_axis0_mi_discrim_branches.json:1-48`
- tension:
  - `metrics_SEQ01.MI_mean = -2.190088388420719e-17`
  - `metrics_SEQ02.MI_mean = -1.9949319973733282e-17`
  - `delta_MI_mean_SEQ02_minus_SEQ01 = 1.951563910473908e-18`
  - `delta_SAgB_mean_SEQ02_minus_SEQ01 = -0.002669220066020328`
- preserved read:
  - keep the naming pressure separate from the stored metric reality
- possible downstream consequence:
  - later interpretation should not describe this non-AB surface as a successful MI split without qualification

## T3) The non-AB branch family and the adjacent `_ab` sibling look adjacent by name, but their executable contracts differ materially
- source markers:
  - `run_axis0_mi_discrim_branches.py:116-139`
  - `run_axis0_mi_discrim_branches_ab.py:131-154`
  - `results_axis0_mi_discrim_branches_ab.json:1-49`
- tension:
  - the current runner uses only A-local unitary and A-local terrain maps
  - the `_ab` sibling adds `rho = apply_unitary_AB(rho, CNOT)`
  - the sibling then produces nonzero MI means around `0.005` and `delta_MI_mean_SEQ02_minus_SEQ01 = 0.0007381966930415842`
- preserved read:
  - keep the current family separate from the sibling AB-coupled family
- possible downstream consequence:
  - the next batch should begin at `run_axis0_mi_discrim_branches_ab.py`

## T4) The current branch difference is present in `SAgB`, but negativity never appears
- source markers:
  - `results_axis0_mi_discrim_branches.json:1-48`
- tension:
  - `delta_SAgB_mean_SEQ02_minus_SEQ01 = -0.002669220066020328`
  - both branches keep `neg_SAgB_frac = 0.0`
- preserved read:
  - the current family has branch sensitivity without any stored negative conditional-entropy event
- possible downstream consequence:
  - later backlog work should not confuse zero negativity fraction with total metric invariance

## T5) The result surface is extremely compact, and that compactness can hide how little the MI layer actually moves
- source markers:
  - `results_axis0_mi_discrim_branches.json:1-48`
  - `run_axis0_mi_discrim_branches.py:176-223`
- tension:
  - the family stores only branch-level summary statistics
  - the compact writer still foregrounds MI deltas even when the stored MI layer is effectively zero
- preserved read:
  - keep compact evidence formatting distinct from substantive signal strength
- possible downstream consequence:
  - later summaries should call out the machine-scale MI values rather than echoing the family name uncritically

## T6) This family is the second resolved residual pair, but result-only, runner-only, and hygiene residue remain outside the paired-family campaign
- source markers:
  - `BATCH_sims_residual_inventory_closure_audit__v1/MANIFEST.json`
  - `BATCH_sims_axis0_historyop_rec_suite_v1_family__v1/MANIFEST.json`
- tension:
  - the paired-family campaign is advancing
  - the closure audit still preserves separate residual classes that have not entered this campaign
- preserved read:
  - keep paired-family intake separate from orphan results, runner-only surfaces, and hygiene residue
- possible downstream consequence:
  - future work should continue pair-by-pair without collapsing residual classes
