# SOURCE_DEPENDENCY_MAP__v1
Status: PROPOSED / NONCANONICAL / A2-MID SOURCE DEPENDENCY MAP
Batch: `BATCH_A2MID_constraints_entropy_chain_fences__v1`
Extraction mode: `TERM_CONFLICT_REDUCTION_PASS`
Date: 2026-03-09

## Primary parent batch
- `BATCH_refinedfuel_constraints_entropy_term_conflict__v1`

## Comparison anchors used for narrowing
- `BATCH_A2MID_CONTRADICTION_entropic_qit_math_drift__v1`
- `BATCH_A2MID_CONTRADICTION_entropy_scalar_worldview__v1`
- `BATCH_refinedfuel_entropy_contract_math_class__v1`
- `BATCH_refinedfuel_path_contract_math_class__v1`
- `BATCH_refinedfuel_engine_contract_engine_pattern__v1`
- `BATCH_refinedfuel_topology_contract_math_class__v1`
- `BATCH_refinedfuel_geometry_admissibility_math_class__v1`

## Parent artifacts read
- `MANIFEST.json`
- `SOURCE_MAP__v1.md`
- `CLUSTER_MAP__v1.md`
- `TENSION_MAP__v1.md`
- `A2_3_DISTILLATES__v1.md`
- `A2_2_CANDIDATE_SUMMARIES__v1.md`

## Dependency notes
- this pass operates from the stronger single-source `TERM_CONFLICT_PASS` parent rather than the older `SOURCE_MAP_PASS` parent used by the broader warm-cluster contradiction packet
- the broader contradiction packet remains valid comparison context, but this pass narrows only the internal chain of the `Constraints. Entropy` precursor
- direct contract-side batches were used so the reduction could stay source-specific at each step of the chain:
  - scalar law
  - path law
  - engine pressure
  - topology forcing
  - bundle and Hopf pressure
- no fresh raw-source reread was needed because the parent batch already isolates the relevant chain sections and their fail-closed comparison seams

## Candidate-to-parent dependency map
- `RC1_PROBE_RELATIVE_IDENTITY_GOVERNANCE_ONLY_PACKET`
  - parent dependencies:
    - `SOURCE_MAP__v1.md:Segment A`
    - `CLUSTER_MAP__v1.md:2`
    - `TENSION_MAP__v1.md:7`
  - comparison anchor:
    - `BATCH_A2MID_CONTRADICTION_entropic_qit_math_drift__v1:RC1`
- `RC2_NONLITERAL_SCALAR_TRANSLATION_WITHOUT_MASTER_I_SCALAR`
  - parent dependencies:
    - `SOURCE_MAP__v1.md:Segment B`
    - `CLUSTER_MAP__v1.md:3`
    - `TENSION_MAP__v1.md:2`
  - comparison anchors:
    - `BATCH_A2MID_CONTRADICTION_entropy_scalar_worldview__v1:RC4`
    - `BATCH_A2MID_CONTRADICTION_entropy_scalar_worldview__v1:RC5`
    - `BATCH_refinedfuel_entropy_contract_math_class__v1:A2_3_DISTILLATES__v1`
- `RC3_PATH_COST_AND_SURVIVOR_LANGUAGE_STAYS_NONADMISSIVE`
  - parent dependencies:
    - `SOURCE_MAP__v1.md:Segment C`
    - `CLUSTER_MAP__v1.md:4`
    - `TENSION_MAP__v1.md:3`
  - comparison anchors:
    - `BATCH_A2MID_CONTRADICTION_entropy_scalar_worldview__v1:RC3`
    - `BATCH_refinedfuel_path_contract_math_class__v1:A2_3_DISTILLATES__v1`
- `RC4_RECURRENCE_STAYS_NONENGINE_STRUCTURE`
  - parent dependencies:
    - `SOURCE_MAP__v1.md:Segment E`
    - `CLUSTER_MAP__v1.md:5`
    - `TENSION_MAP__v1.md:4`
  - comparison anchors:
    - `BATCH_A2MID_CONTRADICTION_entropic_qit_math_drift__v1:RC4`
    - `BATCH_refinedfuel_engine_contract_engine_pattern__v1:A2_3_DISTILLATES__v1`
- `RC5_COMPATIBILITY_NEIGHBORHOODS_STAY_RELATIONAL_NOT_FORCED_TOPOLOGY`
  - parent dependencies:
    - `SOURCE_MAP__v1.md:Segment F`
    - `CLUSTER_MAP__v1.md:6`
    - `TENSION_MAP__v1.md:5`
  - comparison anchor:
    - `BATCH_refinedfuel_topology_contract_math_class__v1:A2_3_DISTILLATES__v1`
- `RC6_BUNDLE_HOPF_PRESSURE_STAYS_DERIVED_GEOMETRY_LINEAGE_ONLY`
  - parent dependencies:
    - `SOURCE_MAP__v1.md:Segment F`
    - `CLUSTER_MAP__v1.md:7`
    - `TENSION_MAP__v1.md:6`
  - comparison anchors:
    - `BATCH_A2MID_CONTRADICTION_entropic_qit_math_drift__v1:CP7`
    - `BATCH_refinedfuel_geometry_admissibility_math_class__v1:A2_3_DISTILLATES__v1`

## Quarantine dependency map
- `Q1_EQUIVALENCE_PREORDER_CATEGORY_AS_ALREADY_EARNED_KERNEL_OBJECT`
  - `SOURCE_MAP__v1.md:Segment A`
  - `CLUSTER_MAP__v1.md:2`
- `Q2_GLOBAL_I_SCALAR_AND_PATH_ENTROPY_AS_CLOCK_SELECTION_LAW`
  - `SOURCE_MAP__v1.md:Segment B`
  - `CLUSTER_MAP__v1.md:3`
  - `TENSION_MAP__v1.md:2`
- `Q3_PATH_COST_SURVIVORSHIP_AS_ADMISSIBILITY_OR_REALIZABILITY_LAW`
  - `SOURCE_MAP__v1.md:Segment C`
  - `CLUSTER_MAP__v1.md:4`
  - `TENSION_MAP__v1.md:3`
- `Q4_STABLE_RECURRENCE_AS_ENGINE_INEVITABILITY`
  - `SOURCE_MAP__v1.md:Segment E`
  - `CLUSTER_MAP__v1.md:5`
  - `TENSION_MAP__v1.md:4`
- `Q5_COMPATIBILITY_NEIGHBORHOODS_AS_FORCED_TOPOLOGY`
  - `SOURCE_MAP__v1.md:Segment F`
  - `CLUSTER_MAP__v1.md:6`
  - `TENSION_MAP__v1.md:5`
- `Q6_BUNDLE_GLUING_HOPF_AS_UNAVOIDABLE_DERIVATION`
  - `SOURCE_MAP__v1.md:Segment F`
  - `CLUSTER_MAP__v1.md:7`
  - `TENSION_MAP__v1.md:6`
- `Q7_HIDDEN_FORMAL_IMPORTS_AS_IF_THEY_DO_NOT_COUNT_AS_SMUGGLING`
  - `CLUSTER_MAP__v1.md:8`
  - `TENSION_MAP__v1.md:7`

## Raw reread status
- raw source reread needed: `false`
- reason:
  - the parent term-conflict batch already isolates the early equivalence package, scalar law jump, path-selection jump, engine pressure, topology forcing, and bundle/Hopf pressure with enough precision for bounded reduction
