# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1`
Extraction mode: `SIM_ULTRA2_MACRO_BUNDLE_PASS`

## T1) The local ultra2 macro family exists, but the repo-held top-level evidence pack omits it
- source markers:
  - `run_ultra2_axis0_ab_stage16_axis6.py:1-382`
  - negative search for `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_CATALOG_v1.3.md:115`
- tension:
  - the current runner writes local evidence for `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6`
  - the catalog lists the family
  - the repo-held top-level evidence pack contains no matching block
- preserved read:
  - keep local-writer existence distinct from repo-top evidence admission
- possible downstream consequence:
  - the batch should stay proposal-side in provenance strength

## T2) One macro result joins three different subfamilies into one surface
- source markers:
  - `run_ultra2_axis0_ab_stage16_axis6.py:280-382`
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- tension:
  - the stored result mixes:
    - `stage16`
    - `axis0_ab`
    - `axis12`
  - those branches have different scales, semantics, and expected downstream use
- preserved read:
  - do not flatten the macro bundle into one single-behavior sim
- possible downstream consequence:
  - later summaries should preserve branch identity inside the macro family

## T3) The stored `seqs` field is not exhaustive for the Axis12 branch
- source markers:
  - `run_ultra2_axis0_ab_stage16_axis6.py:280-382`
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- tension:
  - the stored `seqs` field lists only `SEQ01` and `SEQ02`
  - the stored `axis12` counts also include `SEQ03` and `SEQ04`
  - those extra sequences come from inline literals in the runner, not from the stored `seqs` object
- preserved read:
  - do not treat `seqs` as a complete declaration of sequence participation
- possible downstream consequence:
  - later sequence analysis must preserve that the Axis12 portion has hidden sequence scope beyond the stored `seqs` field

## T4) Stage16 and Axis0 AB branches live on different effect scales inside the same macro result
- source markers:
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- tension:
  - the strongest Stage16 absolute effect is about `0.0030557656357999563`
  - the strongest Axis0 AB absolute effect is about `0.0007394962681647188`
  - both scales are bundled without separate file boundaries
- preserved read:
  - do not speak about one uniform ultra2 effect scale
- possible downstream consequence:
  - later interpretation should stay branch-specific rather than bundle-averaged

## T5) The strongest Stage16 cells are Se-focused, not evenly distributed across the lattice
- source markers:
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- tension:
  - the top Stage16 entries are:
    - `T1_outer_1_Se_UP_MIX_A`
    - `T1_inner_1_Se_DOWN_MIX_B`
    - `T2_inner_1_Se_DOWN_MIX_B`
    - `T2_outer_1_Se_UP_MIX_A`
- preserved read:
  - keep the Stage16 branch Se-centered rather than implying an even macro-wide spread
- possible downstream consequence:
  - later Stage16 reads should preserve the Se concentration even inside the ultra bundle

## T6) Raw-order-adjacent `ultra4` is a fuller stack, not the same bounded family
- source markers:
  - `run_ultra4_full_stack.py:280-412`
  - `results_ultra4_full_stack.json:1-906`
- tension:
  - `ultra4` adds:
    - berry flux
    - `SEQ03`
    - `SEQ04`
  - `ultra4` expands `axis0_ab` from `16` keys to `128`
  - both families are catalog-visible but omitted from the current top-level evidence pack
- preserved read:
  - `ultra4` begins the next bounded family
- possible downstream consequence:
  - the next batch should start at `run_ultra4_full_stack.py`
