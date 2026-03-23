# A2_2_REFINED_CANDIDATES__v1
Status: PROPOSED / NONCANONICAL / OUTER A2-MID REDUCTION ARTIFACT
Batch: `BATCH_A2MID_active_live_state_index_controller_fences__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Candidate RC1: `ACTIVE_STATE_STORE_CLASS_SEPARATION_RULE`
- candidate read:
  - active `a2_state` should be read as at least four distinct store classes:
    - compact registries and snapshots
    - ingest indices and classification surfaces
    - curated doc-card/system-map abstractions
    - append-log memory plus shard history
  and later reduction should not flatten them into one state surface
- why candidate:
  - this is the cleanest controller-facing reduction of the parent’s overall live-state structure
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `CLUSTER_MAP__v1:Cluster B`
  - `CLUSTER_MAP__v1:Cluster C`
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D1`
  - `A2_3_DISTILLATES__v1:D2`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C1`

## Candidate RC2: `MEMBERSHIP_EQUIVALENT_INGEST_INDICES_ARE_STILL_DISTINCT_ARTIFACTS`
- candidate read:
  - `core_docs_ingest_index_v1.json` and `ingest/index_v1.json` may be membership-equivalent, but because they have separate generation times, hashes, and sidecars they should remain distinct artifacts rather than being silently collapsed
- why candidate:
  - this preserves the parent’s sharpest index-identity contradiction without turning same membership into same object
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D3`
  - `TENSION_MAP__v1:T1`

## Candidate RC3: `DOC_INDEX_IS_BROADER_CLASSIFICATION_NOT_INGEST_COPY`
- candidate read:
  - `doc_index.json` should be preserved as:
    - a broader classification layer
    - including quarantine markers and extra residue paths
    - not just another ingest index copy
- why candidate:
  - this is the cleanest controller-facing reduction of the parent’s broader-scope audit value
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster B`
  - `A2_3_DISTILLATES__v1:D4`
  - `A2_3_DISTILLATES__v1:D11`
  - `TENSION_MAP__v1:T2`
  - `TENSION_MAP__v1:T10`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Candidate RC4: `DOC_CARD_SYSTEM_MAP_OVERLAY_IS_NOT_ID_OR_PATH_COMPATIBLE_INDEX`
- candidate read:
  - the doc-card/system-map packet is a curated role overlay:
    - useful for purpose, fence, and role abstraction
    - not id-compatible with the ingest index
    - not path-accurate enough to replace the current index paths
- why candidate:
  - this compresses the parent’s strongest structural mismatch into one direct controller rule
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster C`
  - `A2_3_DISTILLATES__v1:D5`
  - `A2_3_DISTILLATES__v1:D6`
  - `TENSION_MAP__v1:T3`
  - `TENSION_MAP__v1:T4`
  - `TENSION_MAP__v1:T9`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C2`

## Candidate RC5: `LIVE_REGISTRY_COUNTS_MUST_NOT_COLLAPSE_TO_ONE_PROGRESS_METRIC`
- candidate read:
  - kernel survivors, constraint survivors, rosetta mappings, autosave counters, and queue volumes are different layer metrics and must not be merged into one progress number or one admission score
- why candidate:
  - this is the strongest metric-discipline rule preserved by the parent live registries
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster A`
  - `A2_3_DISTILLATES__v1:D9`
  - `A2_3_DISTILLATES__v1:D10`
  - `TENSION_MAP__v1:T5`
  - `TENSION_MAP__v1:T6`

## Candidate RC6: `MEMORY_CHAIN_SEMANTIC_CORE_OVER_AUTOSAVE_CHURN`
- candidate read:
  - the memory chain should be reduced with explicit separation between:
    - older semantic base shard and current append log continuity
    - meaningful campaign/runtime/A1/ingest events
    - heavy autosave-tick churn
- why candidate:
  - this is the parent’s clearest chronological rule and the cleanest way to keep semantic event signal visible
- parent dependencies:
  - `CLUSTER_MAP__v1:Cluster D`
  - `A2_3_DISTILLATES__v1:D7`
  - `A2_3_DISTILLATES__v1:D8`
  - `TENSION_MAP__v1:T7`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C5`

## Quarantined Q1: `INDEXED_PRESENCE_AS_TRUSTED_ADMISSION`
- quarantine read:
  - do not infer trusted admission from indexed presence alone, because the active `doc_index.json` explicitly retains quarantined high-entropy sources and residue paths
- why quarantined:
  - the parent preserves indexed presence and quarantine classification simultaneously, so presence cannot self-authorize trust
- parent dependencies:
  - `A2_3_DISTILLATES__v1:D11`
  - `TENSION_MAP__v1:T10`
  - `A2_2_CANDIDATE_SUMMARIES__v1:C3`

## Quarantined Q2: `LIVE_UPDATE_LANGUAGE_AS_MUTATION_PERMISSION_IN_THIS_LANE`
- quarantine read:
  - do not treat live registry update wording in `rosetta.json` or `a1_brain.jsonl` as permission to mutate active state from this intake lane
- why quarantined:
  - the parent preserves current state and intended update semantics, but this worker lane remains intake-only and proposal-side
- parent dependencies:
  - `TENSION_MAP__v1:T8`
  - `A2_3_DISTILLATES__v1:D9`
