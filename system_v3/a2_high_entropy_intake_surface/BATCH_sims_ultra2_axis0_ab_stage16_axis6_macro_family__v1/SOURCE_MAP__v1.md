# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_ultra2_axis0_ab_stage16_axis6_macro_family__v1`
Extraction mode: `SIM_ULTRA2_MACRO_BUNDLE_PASS`
Batch scope: macro composite bundle centered on `run_ultra2_axis0_ab_stage16_axis6.py` and `results_ultra2_axis0_ab_stage16_axis6.json`, with `ultra4` held comparison-only as the next full-stack expansion family
Date: 2026-03-09

## 1) Batch Selection
- starting file in raw simpy folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
- selected sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
- reason for bounded family:
  - `run_ultra2_axis0_ab_stage16_axis6.py` is the next unprocessed raw-folder-order source
  - it has one direct paired result surface with the same basename
  - it is a true macro composite runner that merges:
    - `stage16`
    - `axis0_ab`
    - `axis12`
  - the adjacent `run_ultra4_full_stack.py` is a larger full-stack expansion with additional berry-flux and sequence coverage, so it begins the next bounded family rather than joining this batch
- comparison-only anchors read:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
- deferred next raw-folder-order source:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`

## 2) Source Membership
- Runner:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra2_axis0_ab_stage16_axis6.py`
  - sha256: `d24af2380331058e9e38128a72b61fcafbdc168bbbf4f73a60ad982893dca334`
  - size bytes: `14413`
  - line count: `382`
  - source role: macro composite runner
- Result surface:
  - path: `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra2_axis0_ab_stage16_axis6.json`
  - sha256: `6b829c908932fa9e87be92a94fa256a76edafb5d572a02a2943c07f435fd76f5`
  - size bytes: `7560`
  - line count: `332`
  - source role: macro composite result surface

## 3) Structural Map Of The Family
### Ultra2 macro runner: `run_ultra2_axis0_ab_stage16_axis6.py`
- anchors:
  - `run_ultra2_axis0_ab_stage16_axis6.py:1-382`
  - `run_ultra2_axis0_ab_stage16_axis6.py:280-382`
- source role:
  - one macro runner that stores three subfamilies in one result surface:
    - `stage16` mixed-axis6 deltas
    - `axis0_ab` sequence-delta deltas
    - `axis12` adjacency counts
  - writes one local SIM_ID:
    - `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6`
  - current result shape:
    - `stage16` keys: `48`
    - `axis0_ab` keys: `16`
    - `axis12` keys: `8`

### Stage16 component
- source markers:
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- bounded read:
  - the strongest Stage16 absolute effect is tied between:
    - `T1_outer_1_Se_UP_MIX_A`
    - `T1_inner_1_Se_DOWN_MIX_B`
  - both reach:
    - `abs(dS) = 0.0030557656357999563`
  - the next strongest cells remain Se-focused:
    - `T2_inner_1_Se_DOWN_MIX_B`
    - `T2_outer_1_Se_UP_MIX_A`
- preserved read:
  - this macro Stage16 branch stays small and Se-concentrated inside the composite bundle

### Axis0 AB component
- source markers:
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- bounded read:
  - the strongest Axis0 AB setting is:
    - `T1_FWD_CNOT_R1`
  - its deltas are:
    - `dMI = -0.0007394962681647188`
    - `dSAgB = 0.0006057979105169031`
    - `dNegFrac = -0.0005408653846153966`
  - all stored Axis0 AB entries are deltas only, not mixed absolute/delta records

### Axis12 internal seam
- source markers:
  - `run_ultra2_axis0_ab_stage16_axis6.py:280-382`
  - `results_ultra2_axis0_ab_stage16_axis6.json`
- bounded read:
  - the stored `seqs` field lists only:
    - `SEQ01`
    - `SEQ02`
  - the stored `axis12` counts also include:
    - `SEQ03_NESI = 1`
    - `SEQ03_SENI = 1`
    - `SEQ04_NESI = 1`
    - `SEQ04_SENI = 1`
  - those extra counts come from inline literal sequences in the runner rather than from the stored `seqs` field
- preserved read:
  - do not treat the `seqs` field as exhaustive for the Axis12 portion of this macro result

### Boundary to `ultra4_full_stack`
- comparison anchors:
  - `run_ultra4_full_stack.py:280-412`
  - `results_ultra4_full_stack.json:1-906`
- bounded comparison read:
  - `ultra4` expands the macro contract rather than continuing this exact surface
  - `ultra4` adds:
    - `berry_flux_plus`
    - `berry_flux_minus`
    - `SEQ03`
    - `SEQ04`
  - `ultra4` stores:
    - `axis0_ab` keys: `128`
    - `stage16` keys: `48`
    - `axis12` keys: `8`
  - both `ultra2` and `ultra4` are catalog-visible but absent from the repo-held top-level evidence pack

## 4) Comparison Anchors
- comparison sources:
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_CATALOG_v1.3.md`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simpy/run_ultra4_full_stack.py`
  - `/home/ratchet/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/sims/simson/results_ultra4_full_stack.json`
- relevant anchors:
  - `SIM_CATALOG_v1.3.md:115`
  - `SIM_CATALOG_v1.3.md:131`
  - `SIM_CATALOG_v1.3.md:147-148`
- bounded comparison read:
  - the catalog lists both `ultra2_axis0_ab_stage16_axis6` and `ultra4_full_stack`
  - the repo-held top-level evidence pack contains neither `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6` nor `S_SIM_ULTRA4_FULL_STACK`
  - the next raw-order handoff is therefore a family boundary inside the same macro lane, not a single merged bundle

## 5) Source-Class Read
- Best classification:
  - standalone macro composite family with one runner and one result that bundles three sim subfamilies into one proposal-side surface
- Not best classified as:
  - a repo-top evidenced macro surface
  - the same bounded family as `run_ultra4_full_stack.py`
  - a single theory-only family
- Theory-facing vs executable-facing split:
  - executable-facing:
    - one macro runner emits three different result classes into one JSON surface
  - theory-facing:
    - one proposal-side compression of Stage16, Axis0 AB, and Axis12 behavior
  - evidence-facing:
    - local SIM_ID exists only in the writer contract
    - current repo-top evidence omits the entire macro family
- possible downstream consequence:
  - later sims interpretation should treat `ultra2` as a bounded macro bundle and let `ultra4` stand as the next broader full-stack family
