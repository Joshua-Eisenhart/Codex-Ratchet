# SIM_CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
Extraction mode: `SIM_BATCH_BUNDLE_PASS`

## Cluster S1: Embedded multi-sim bundle membership
- source anchors:
  - `run_batch_v3.py:214-324`
  - `run_batch_v3.py:326-401`
  - `run_batch_v3.py:435-500`
  - `results_batch_v3.json:1-222`
- cluster members:
  - `S_SIM_AXIS12_CHANNEL_REALIZATION_V3`
  - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V3`
  - `S_SIM_AXIS0_TRAJ_CORR_SUITE_V3`
  - `S_SIM_NEGCTRL_AXIS6_COMMUTE_V1`
- compressed read:
  - `batch_v3` is one runner bundling four different sims with different internal schemas into one aggregate container
- possible downstream consequence:
  - later intake should treat this source as a precursor bundle, not as one uniform sim family

## Cluster S2: Per-subpayload evidence hash contract
- source anchors:
  - `run_batch_v3.py:416-433`
  - `run_batch_v3.py:487-498`
  - `results_batch_v3.json:1-222`
- cluster members:
  - aggregate file hash `d58eb25c...`
  - subpayload hashes `43e11d9d...`, `855d4daa...`, `e5569eed...`, `0524d2f1...`
  - one packed evidence file
- compressed read:
  - the bundle's evidence contract is keyed to each embedded payload rather than to the aggregate JSON file that actually stores them together
- possible downstream consequence:
  - provenance checks against `results_batch_v3.json` must separate container hash from embedded output hashes

## Cluster S3: Descendant decomposition across later standalone surfaces
- source anchors:
  - `SIM_CATALOG_v1.3.md:39-54`
  - `SIM_CATALOG_v1.3.md:102-108`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:2-40`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-414`
- cluster members:
  - Axis12 V4
  - Axis0 V4
  - Axis0 V5
  - Stage16 V4
  - Stage16 V5
  - Negctrl Axis6 V2
  - Negctrl Axis6 V3
- compressed read:
  - the current repo foregrounds decomposed later descendants of the bundle rather than the bundle's own V3/V1 SIM_IDs
- possible downstream consequence:
  - `batch_v3` is best used as a lineage surface for descendant drift, not as the present authoritative result surface for any one branch

## Cluster S4: Schema drift inside descendant families
- source anchors:
  - `results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json:1-595`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json:1-28`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json:1-32`
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json:1-50`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json:1-5`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json:1-5`
- cluster members:
  - parameter grid
  - single-sequence collapse
  - two-sequence delta surface
  - stage-indexed uniform surface
  - negctrl trial-count revision
- compressed read:
  - each descendant family refactors the bundle differently; there is no one simple one-to-one export from `batch_v3` into the current repo's standalone shapes
- possible downstream consequence:
  - later sims interpretation should avoid overstating exact equivalence between bundle payloads and later standalone files

## Cluster S5: Stage16 duplicate descendant output
- source anchors:
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json:1-50`
  - `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json:1-50`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`
- cluster members:
  - `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4`
  - `S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5`
  - shared result hash `955244986b65a4a45227f50737471c41ebf97d1462cabdd3d5b4a8467cbf7c8e`
- compressed read:
  - the repo carries two differently named Stage16 descendants with byte-identical stored outputs
- possible downstream consequence:
  - later Stage16 provenance work must preserve duplicate descendant naming rather than silently collapsing one label

## Cluster S6: Adjacent engine32 separation
- source anchors:
  - `run_engine32_axis0_axis6_attack.py:2-5`
  - `run_engine32_axis0_axis6_attack.py:168-238`
  - `results_engine32_axis0_axis6_attack.json:1-689`
  - `SIM_CATALOG_v1.3.md:54`
  - `SIM_CATALOG_v1.3.md:102`
- cluster members:
  - `batch_v3`
  - `engine32_axis0_axis6_attack`
  - `OTHER`
  - `MESO: Axis0`
- compressed read:
  - the adjacent `engine32` surface shares some axis vocabulary with one branch of the bundle but is structurally a separate direct suite, not another embedded precursor block
- possible downstream consequence:
  - the next raw-order batch should process `engine32` independently
