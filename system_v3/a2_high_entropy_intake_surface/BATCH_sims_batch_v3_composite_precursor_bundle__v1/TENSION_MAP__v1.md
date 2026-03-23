# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_sims_batch_v3_composite_precursor_bundle__v1`
Extraction mode: `SIM_BATCH_BUNDLE_PASS`

## T1) `batch_v3` is cataloged as `OTHER` but bundles multiple meso-family branches
- source markers:
  - `SIM_CATALOG_v1.3.md:39-54`
  - `SIM_CATALOG_v1.3.md:102-108`
  - `run_batch_v3.py:435-500`
- tension:
  - the catalog lists `batch_v3` under `OTHER`
  - the bundle internally carries Axis12, Axis0, Stage16, and Axis6-negctrl descendants that later appear in meso/Stage16 catalog groupings
- preserved read:
  - keep `batch_v3` as a classification seam between bundle packaging and later decomposed family placement
- possible downstream consequence:
  - later catalog-based summaries should not flatten bundle location into subject-matter location

## T2) Aggregate result container vs per-payload evidence hashing
- source markers:
  - `run_batch_v3.py:416-433`
  - `run_batch_v3.py:487-498`
  - `results_batch_v3.json:1-222`
- tension:
  - the runner writes one aggregate `results_batch_v3.json`
  - evidence hashes are computed from each embedded payload instead of the aggregate container
- preserved read:
  - keep container-level and payload-level provenance distinct
- possible downstream consequence:
  - later audits must not mistake the aggregate file hash for the evidence-cited output hashes

## T3) The current top-level evidence pack omits the bundle's own V3/V1 SIM_IDs
- source markers:
  - `run_batch_v3.py:441-480`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:2-40`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-414`
- tension:
  - `run_batch_v3.py` emits V3/V1 SIM_IDs for four embedded payloads
  - the current top-level evidence pack instead records later standalone descendants and does not surface those bundle-local V3/V1 IDs
- preserved read:
  - preserve the repo's shift from composite bundle to decomposed descendant evidence
- possible downstream consequence:
  - later sims intake should treat `batch_v3` as historical precursor evidence, not as current top-level evidence-pack authority

## T4) Descendant families drift in different directions rather than one direction
- source markers:
  - `results_S_SIM_AXIS12_CHANNEL_REALIZATION_V4.json:1-595`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V4.json:1-28`
  - `results_S_SIM_AXIS0_TRAJ_CORR_SUITE_V5.json:1-32`
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json:1-50`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json:1-5`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json:1-5`
- tension:
  - Axis12 becomes a parameter grid
  - Axis0 becomes later collapsed or delta-oriented standalone surfaces
  - Stage16 is extracted into uniform-only descendants
  - Negctrl is reduced to minimal mean-only surfaces with a later trial-count change
- preserved read:
  - keep descendant drift as plural and uneven rather than implying one simple upgrade path
- possible downstream consequence:
  - later lineage claims should stay family-specific

## T5) Stage16 descendant duplication vs naming drift
- source markers:
  - `results_S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4.json:1-50`
  - `results_S_SIM_STAGE16_SUB4_UNIFORM_AXIS6_V5.json:1-50`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:336-414`
- tension:
  - V4 and V5 have different names and SIM_IDs
  - their stored result files are byte-identical and share the same output hash
- preserved read:
  - keep the duplicate descendant labels visible rather than normalizing them to one canonical name
- possible downstream consequence:
  - later Stage16 summary layers should record the duplicate-label residue explicitly

## T6) Negctrl descendant revision changes trials but not mean metrics
- source markers:
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V2.json:1-5`
  - `results_S_SIM_NEGCTRL_AXIS6_COMMUTE_V3.json:1-5`
  - `SIM_EVIDENCE_PACK_autogen_v2.txt:318-332`
- tension:
  - V2 and V3 both report `comm_norm_mean=0` and `delta_trace_mean=0`
  - V2 stores `trials=256` while V3 stores `trials=512`
  - the evidence pack also records a zeroed code hash for V3
- preserved read:
  - keep the negctrl branch as a versioning seam rather than assuming the two stored surfaces are interchangeable
- possible downstream consequence:
  - later negative-control confidence claims should mention the trial-count and provenance drift

## T7) Adjacent `engine32` shares axis vocabulary but not family structure
- source markers:
  - `run_batch_v3.py:435-500`
  - `run_engine32_axis0_axis6_attack.py:168-238`
  - `SIM_CATALOG_v1.3.md:54`
  - `SIM_CATALOG_v1.3.md:102`
- tension:
  - `batch_v3` contains one Axis0-related embedded payload and one Axis6 negctrl payload
  - `engine32` is a direct Axis0/Axis6 attack suite with `32` keyed result cells and one single SIM_ID
- preserved read:
  - do not merge adjacency-plus-shared-terms into one batch family
- possible downstream consequence:
  - the next raw-order batch should start at `engine32` and treat it as separate executable-facing intake
