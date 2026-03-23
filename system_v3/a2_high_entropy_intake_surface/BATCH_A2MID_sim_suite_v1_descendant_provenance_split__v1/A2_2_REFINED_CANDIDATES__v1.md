# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / A2-2 REFINED CANDIDATES
Batch: `BATCH_A2MID_sim_suite_v1_descendant_provenance_split__v1`
Extraction mode: `CONTRADICTION_REPROCESS_PASS`
Date: 2026-03-09

## Candidate RC1) `SIM_SUITE_V1_TEN_DESCENDANT_BUNDLE_EMISSION_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_sim_suite_v1.py` is best kept as:
  - one genuine multisim bundle
  - one executable surface that emits ten stored descendants
  - one local multi-block evidence surface
  - not just a catalog pointer or a loose descendant cluster

Why this survives reduction:
- it is the parent batch's clearest bundle-identity claim
- later sims lineage work needs this bundle-emission fact before sorting current provenance splits

Source lineage:
- parent cluster `A`
- parent distillate `D1`
- parent candidates:
  - `C1`
  - `C2`

Preserved limits:
- this batch does not treat bundle emission as identical to current repo-top producer attribution
- it preserves executable-bundle identity only

## Candidate RC2) `ALL_TEN_DESCENDANTS_EVIDENCED_WITH_SPLIT_CURRENT_PROVENANCE_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the parent batch's strongest top-level provenance packet is:
  - all ten emitted descendants are represented in the repo-held top-level evidence pack
  - current code attribution is split across multiple hashes rather than remaining on one bundle hash

Why this survives reduction:
- it is the cleanest compression of the parent batch's central contradiction
- it keeps full evidence coverage and split current provenance visible together

Source lineage:
- parent distillate `D2`
- parent tension `T1`
- comparison anchor:
  - `BATCH_A2MID_sims_evidence_boundary__v1:RC2`

Preserved limits:
- this batch does not collapse evidence coverage into one current producer path
- it preserves coverage and attribution separately

## Candidate RC3) `ALIGNED_FOUR_VERSUS_MIGRATED_SIX_DESCENDANT_SPLIT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- descendant continuity in this bundle should be graded by subset:
  - Axis3, Axis5 FGA, Axis5 FSA, and Axis6 remain aligned to the current `run_sim_suite_v1.py` hash
  - Axis12 seq constraints, Axis12 channel realization, Axis4 all-bidir, Axis0 traj corr V4, Stage16 V4, and Negctrl V2 have migrated to other current provenance anchors

Why this survives reduction:
- it is the parent batch's cleanest anti-flattening provenance rule
- later lineage work needs the aligned-four subset without overextending it to the whole bundle

Source lineage:
- parent clusters:
  - `B`
  - `C`
- parent distillates:
  - `D3`
  - `D4`
- parent tensions:
  - `T2`
  - `T3`
  - `T4`
  - `T5`

Preserved limits:
- this batch does not deny bundle emission for the migrated six
- it preserves only that current repo-top provenance has split descendant-specifically

## Candidate RC4) `STAGE16_V4_PAYLOAD_IDENTITY_WITH_VERSION_AND_PROVENANCE_DRIFT_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the Stage16 branch preserves one sharp residue packet:
  - `sim_suite_v1` emits `S_SIM_STAGE16_SUB4_AXIS6_UNIFORM_V4`
  - repo-top evidence attributes current provenance to the leading-space mega-script hash
  - stored `V4` and `V5` result payloads are byte-identical despite versioned renaming

Why this survives reduction:
- it is the parent batch's clearest version-label versus payload-identity warning
- later Stage16 summaries need a compact rule for not assuming version labels imply payload change

Source lineage:
- parent cluster `C`
- parent tension `T6`
- comparison anchor:
  - `BATCH_A2MID_oprole8_harness_descendant_seam__v1:RC5`

Preserved limits:
- this batch does not erase Stage16 lineage drift
- it preserves payload identity and provenance drift together

## Candidate RC5) `NEGCTRL_V2_SUCCESSOR_HASH_CROSSOVER_WITH_METRIC_CONTINUITY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- the Negctrl branch preserves a separate crossover packet:
  - `sim_suite_v1` emits Negctrl `V2`
  - repo-top evidence attributes `V2` to the current `run_sim_suite_v2_full_axes.py` hash
  - the current successor bundle emits `V3`, not `V2`
  - `V2` and `V3` preserve the same zero metrics while trials drift from `256` to `512`

Why this survives reduction:
- it is the parent batch's clearest cross-bundle continuity-versus-version packet
- later Negctrl lineage work needs a compact rule for not collapsing metric continuity into clean producer or version continuity

Source lineage:
- parent clusters:
  - `C`
  - `D`
- parent tension `T7`
- comparison anchor:
  - `BATCH_A2MID_oprole8_harness_descendant_seam__v1:RC5`

Preserved limits:
- this batch does not deny Negctrl continuity pressure
- it preserves only that metric continuity, version continuity, and producer continuity are not the same thing here

## Candidate RC6) `SIM_SUITE_V2_SUCCESSOR_BUNDLE_BOUNDARY_RULE`
Status:
- `A2_2_CANDIDATE`

Reduced candidate:
- `run_sim_suite_v2_full_axes.py` should stay comparison-only for this batch because:
  - it emits a different bounded descendant set
  - it already carries partial provenance crossover with `sim_suite_v1`
  - raw adjacency and hash overlap are not enough to erase the bundle boundary

Why this survives reduction:
- it is the parent batch's clearest anti-merge boundary
- keeping the successor bundle separate preserves a clean next-step family instead of creating one giant omnibus bundle

Source lineage:
- parent cluster `D`
- parent distillate `D6`
- parent candidates:
  - `C5`
  - `C6`
- parent tension `T8`

Preserved limits:
- this batch does not deny successor overlap
- it preserves overlap without merging the two bundles

## Quarantined Residue Q1) `TEN_EMITTED_DESCENDANTS_AS_ONE_UNIFORM_CURRENT_BUNDLE_PRODUCER_PATH`
Status:
- `QUARANTINED`

Preserved residue:
- one bundle emitter
- all ten descendants
- all treated as if current repo-top evidence still pointed to one uniform bundle hash

Why it stays quarantined:
- the parent batch explicitly preserves split current provenance across multiple hashes
- flattening the bundle this way would erase the main contradiction in the source

Source lineage:
- parent distillate `D2`
- parent tension `T1`

## Quarantined Residue Q2) `ALIGNED_FOUR_SUBSET_AS_BUNDLE_WIDE_PROVENANCE_RULE`
Status:
- `QUARANTINED`

Preserved residue:
- the clean Axis3 / Axis5 / Axis6 subset
- all treated as if its clean continuity generalized to the whole bundle

Why it stays quarantined:
- the parent batch explicitly preserves a larger migrated subset with other current provenance anchors
- the aligned subset is real but not bundle-global

Source lineage:
- parent cluster `B`
- parent distillate `D3`
- parent tension `T2`

## Quarantined Residue Q3) `DEDICATED_OR_SUCCESSOR_PROVENANCE_AS_ERASURE_OF_BUNDLE_EMISSION`
Status:
- `QUARANTINED`

Preserved residue:
- descendants currently evidenced under dedicated-runner or successor hashes
- all treated as if `sim_suite_v1` no longer emitted them

Why it stays quarantined:
- the parent batch explicitly preserves direct emission by the bundle even where current top-level provenance has migrated
- migrated provenance is weaker than emission erasure

Source lineage:
- parent cluster `C`
- parent distillate `D4`
- parent tensions:
  - `T3`
  - `T4`
  - `T5`

## Quarantined Residue Q4) `STAGE16_VERSION_LABELS_AS_PAYLOAD_CHANGE`
Status:
- `QUARANTINED`

Preserved residue:
- `V4` and `V5` labels in the Stage16 branch
- all treated as if the version change itself proved payload change

Why it stays quarantined:
- the parent batch explicitly preserves byte identity across the two stored result files
- version labels alone are too weak to settle payload drift

Source lineage:
- parent tension `T6`

## Quarantined Residue Q5) `NEGCTRL_V2_TO_V3_AS_CLEAN_RENAME_AND_PRODUCER_CONTINUITY`
Status:
- `QUARANTINED`

Preserved residue:
- Negctrl `V2`
- Negctrl `V3`
- all treated as if the branch followed one clean rename and producer-continuity path

Why it stays quarantined:
- the parent batch explicitly preserves metric continuity alongside trial drift, version drift, and cross-bundle provenance crossover
- a clean rename story overstates the record

Source lineage:
- parent tension `T7`

## Quarantined Residue Q6) `SIM_SUITE_V1_AND_V2_AS_ONE_BOUNDED_BUNDLE`
Status:
- `QUARANTINED`

Preserved residue:
- raw-order adjacency
- partial hash overlap
- all treated as if `sim_suite_v1` and `sim_suite_v2` belonged in one bounded family

Why it stays quarantined:
- the parent batch explicitly preserves a separate successor bundle boundary
- merging them here would destroy the bounded batch discipline

Source lineage:
- parent cluster `D`
- parent distillate `D6`
- parent tension `T8`
