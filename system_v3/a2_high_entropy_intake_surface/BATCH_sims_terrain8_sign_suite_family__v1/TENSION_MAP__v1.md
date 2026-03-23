# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_terrain8_sign_suite_family__v1`
Extraction mode: `SIM_TERRAIN8_SIGN_SUITE_PASS`

## T1) The local terrain suite exists, but repo-top Terrain8 evidence points to a different family
- source markers:
  - `run_terrain8_sign_suite.py:1-137`
  - negative search for `S_SIM_TERRAIN8_SIGN_SUITE` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:54-89`
- tension:
  - the current runner writes local evidence for `S_SIM_TERRAIN8_SIGN_SUITE`
  - the repo-held top-level evidence pack instead admits `S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1`
- preserved read:
  - keep local-writer existence separate from repo-top evidence admission
- possible downstream consequence:
  - this batch should remain proposal-side in provenance strength

## T2) Shared `Terrain8` naming does not imply numerical or contractual continuity
- source markers:
  - `results_terrain8_sign_suite.json:1-20`
  - `results_S_SIM_AXIS12_TOPOLOGY4_TERRAIN8_SUITE_V1.json:1-79`
- tension:
  - local minus `Se` entropy is `0.023571598861606945`
  - top-level `Se_sign-1_{UP,DOWN}` entropies are about `0.39937` to `0.39948`
  - local `Ne` entropy is about `0.6931459`
  - top-level `Ne_sign*_*` entropies are about `0.41221` to `0.41606`
- preserved read:
  - do not collapse the local terrain suite into the Topology4 Terrain8 descendant
- possible downstream consequence:
  - later terrain summaries should keep the simple sign suite and the Topology4 family explicitly separated

## T3) Sign sensitivity is real but uneven across terrains
- source markers:
  - `results_terrain8_sign_suite.json:1-20`
- tension:
  - `Ni` has the largest sign gap:
    - entropy gap `0.001752965040475507`
    - purity gap `0.0017208049418918625`
  - `Si` is the second-largest sign-sensitive terrain
  - `Ne` is effectively sign-invariant
- preserved read:
  - do not summarize the suite as uniformly sign-sensitive or uniformly sign-invariant
- possible downstream consequence:
  - later terrain interpretation should stay terrain-specific rather than sign-averaged

## T4) Terrain ordering is stable even while sign gaps vary
- source markers:
  - `results_terrain8_sign_suite.json:1-20`
- tension:
  - both signs preserve the same ordering:
    - `Se` most ordered / purest
    - `Ne` most mixed / least pure
  - this stable order coexists with the terrain-specific sign gaps above
- preserved read:
  - keep ordering stability and sign sensitivity together rather than flattening to only one of them
- possible downstream consequence:
  - later reads should separate baseline terrain ordering from incremental sign effect

## T5) Raw-order adjacency to `ultra2` does not imply a shared family
- source markers:
  - `run_ultra2_axis0_ab_stage16_axis6.py:280-382`
  - `results_ultra2_axis0_ab_stage16_axis6.json:1-332`
- tension:
  - the current terrain suite is a compact one-family sign sweep
  - `ultra2` is a composite macro surface with:
    - `48` Stage16 keys
    - `16` Axis0 AB keys
    - `8` Axis12 keys
- preserved read:
  - `ultra2` begins the next bounded family
- possible downstream consequence:
  - the next batch should start at `run_ultra2_axis0_ab_stage16_axis6.py`

## T6) Catalog visibility is broader than evidence-pack visibility
- source markers:
  - `SIM_CATALOG_v1.3.md:115`
  - `SIM_CATALOG_v1.3.md:128`
  - negative search for `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6` in `SIM_EVIDENCE_PACK_autogen_v2.txt`
- tension:
  - the catalog lists both `terrain8_sign_suite` and `ultra2_axis0_ab_stage16_axis6`
  - the repo-held evidence pack contains neither local `S_SIM_TERRAIN8_SIGN_SUITE` nor `S_SIM_ULTRA2_AXIS0_AB_STAGE16_AXIS6`
- preserved read:
  - keep catalog admission distinct from evidence-pack admission
- possible downstream consequence:
  - both families stay proposal-side until stronger repo-top evidence appears
