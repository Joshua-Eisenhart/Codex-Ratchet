# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_batch01_core_constraint_ladder_axis_foundation__v1`
Extraction mode: `ARCHIVE_LAYERED_EXTRACTION_PACKAGE_PASS`
Batch scope: first archived packaged layered-extraction output zip in archive-root folder order
Date: 2026-03-09

## 1) Batch Selection
- selected source:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/BATCH_01_OF_10__A2_LAYER1_5__OUTPUT__CORE_CONSTRAINT_LADDER_AXIS_FOUNDATION__v1_1.zip`
- reason for bounded single-package batch:
  - this is the next archive-root item in folder order after the archive-root policy/lineage batch
  - the package is compact (`39305` bytes) and self-contained at the output layer
  - it is a historical derived extraction artifact, so it is safer to process one zip at a time rather than flattening multiple archive packages together
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/BATCH_02_OF_10__A2_LAYER1_5__OUTPUT__AXES_APPLE_NOTES_IGT_MAPPING__v1_1.zip`

## 2) Source Membership
### Primary container
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/BATCH_01_OF_10__A2_LAYER1_5__OUTPUT__CORE_CONSTRAINT_LADDER_AXIS_FOUNDATION__v1_1.zip`
- sha256: `762167c8a904ab4536a1841dfa2f795a241cffbe8188ac5e314284c39044b312`
- size bytes: `39305`
- container member count: `30`
- source class: archived derived A2 layered-extraction output package

### Embedded members read directly for this batch
- member:
  - path: `output/PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__file_fence_and_retry_rules__primary_view__v1.0.md`
  - sha256: `0c6ea43cc82d861855d567a6dad021e1ed8b77b181eaeb3b429f639fbc4749a9`
  - size bytes: `1292`
  - line count: `34`
- member:
  - path: `output/DOCUMENT_NORMALIZATION_AND_SHARD_REPORT__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__deterministic_prep_and_shard_map__primary_view__v1.0.md`
  - sha256: `1f1860e3b423ffa658bb11264b27c1aae93cbb7a851cb967114c357cab81fafb`
  - size bytes: `3654`
  - line count: `65`
- member:
  - path: `output/DOCUMENT_META_MANIFEST__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__topic_inventory_and_output_registry__primary_view__v1.0.md`
  - sha256: `bac8e892947515b355c6fe7f4b09e7c093e8698bac8588ec70f707f5fa7c8191`
  - size bytes: `15081`
  - line count: `192`
- member:
  - path: `output/DOCUMENT_GENERAL_SUMMARY__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__high_level_map_without_smoothing__primary_view__v1.0.md`
  - sha256: `e2193e87e428bccafcd74089707058a9c6773c8b02a18db73361cdfc5df60930`
  - size bytes: `3235`
  - line count: `41`
- member:
  - path: `output/DOCUMENT_TOPIC_INDEX__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__explicit_topic_map__primary_view__v1.0.md`
  - sha256: `ef9cc7a5cf4eb784650fd20236d957f93f4937342f46686f4ae19da0a06bd729`
  - size bytes: `1903`
  - line count: `24`
- member:
  - path: `output/QUALITY_GATE_REPORT__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__completeness_and_no_smoothing_validation__primary_view__v1.0.md`
  - sha256: `02e3646799774138f5b12918bf35a6b557d4436aa3c66426b174fdfd2ee4d6e3`
  - size bytes: `2002`
  - line count: `30`
- member:
  - path: `output/A2_BRAIN_UPDATE_PACKET__persistent_structural_laws_and_invariants_for_future_extractions__primary_view__v1.0.md`
  - sha256: `559059a2f6bac7c9c61112670bf8cbc4da14650d1cb174f2ff832ad0b4de7365`
  - size bytes: `4427`
  - line count: `39`
- member:
  - path: `output/A1_BRAIN_ROSETTA_UPDATE_PACKET__engine_rosetta_patterns_ready_for_a1_sandbox_use__primary_view__v1.0.md`
  - sha256: `49e9ac596513d48d2dc560bd8d1877c5b3e977e31d2ab1095179c914a3838a74`
  - size bytes: `3112`
  - line count: `30`

## 3) Package-Declared Source Corpus
- declared input document count: `8`
- declared source root inside package reporting:
  - `input/payload/*.md`
- declared input members:
  - `input/payload/AXES_MASTER_SPEC_v0.2.md`
  - `input/payload/AXIS_FOUNDATION_COMPANION_v1.4.md`
  - `input/payload/AXIS_FUNCTION_ADMISSIBILITY_v1.md`
  - `input/payload/AXIS_SET_ADMISSIBILITY_v1.md`
  - `input/payload/Base constraints ledger v1.md`
  - `input/payload/CONSTRAINT_MANIFOLD_DERIVATION_v1.md`
  - `input/payload/Constraints.md`
  - `input/payload/REFINEMENT_CONTRACT_v1.1.md`
- declared sharding:
  - `10` shard paths listed in the normalization report
- important archive fact:
  - the zip stores only `output/` files
  - the declared `input/payload/` docs and `shards/` files are referenced by locators/reporting but are not embedded in the archive package

## 4) Structural Map Of The Package
### Segment A: result-only output contract
- source anchors:
  - embedded member: portable output contract
  - embedded member: meta manifest
- source role:
  - defines the package as a pass/fail validated ZIP attachment carrying complete `output/` files only
- strong markers:
  - preferred return mode is `ZIP_ATTACHMENT`
  - fail-closed rejection rules are explicit
  - validation verdict is `PASS`
  - output registry lists `30` files

### Segment B: historical extraction methodology shape
- source anchors:
  - embedded member: normalization and shard report
  - embedded member: topic index
  - embedded member: quality gate
- source role:
  - records the extraction method that produced this historical package
- strong markers:
  - normalization to UTF-8 / LF / trimmed trailing spaces
  - `10` declared shards over the `8` input docs
  - `3` topics
  - required layered topic packets for each topic
  - contradictions preserved and interpretations separated from extraction

### Segment C: foundational law packet
- source anchors:
  - embedded member: A2 brain update packet
- source role:
  - promotes a compact set of law-like extraction locks
- strong markers:
  - finite encoding
  - no commutation by default
  - no primitive identity
  - no substitution by default
  - no probability primitives
  - no optimization primitives
  - axes as nonprimitive slices
  - kernel/overlay separation

### Segment D: thematic topic family
- source anchors:
  - embedded member: topic index
  - embedded member: document general summary
  - topic summaries and contradiction maps
- source role:
  - compresses the package into three historical topic families
- strong markers:
  - `engine_mapping_societal_structure_resilience`
  - `governance_science_method_bidirectional_loops`
  - `mirrors_avatar_feedback_human_machine_alignment`

### Segment E: retained contradiction set
- source anchors:
  - embedded member: document general summary
  - topic contradiction maps
- source role:
  - preserves the package’s main explicit contradiction families
- strong markers:
  - `CONTRA_EM01_AXIS3_SEMANTICS_COLLISION`
  - `CONTRA_EM02_GEOMETRY_PHASE_STATEMENTS`
  - `CONTRA_GOV01_ORDERING_PRESSURE_VS_NO_GLOBAL_RANK`
  - `CONTRA_GOV02_VARIANCE_ORDER_LANGUAGE_VS_NO_TOTAL_ORDER`
  - `CONTRA_MIR01_KERNEL_LABEL_FREE_VS_OVERLAY_LABEL_NEED`
  - `CONTRA_MIR02_IGT_DISCOVERY_PRECEDENCE_VS_MATH_FIRST_FOUNDATION`

### Segment F: rosetta overlay layer
- source anchors:
  - embedded member: A1 brain rosetta update packet
- source role:
  - retains historical Type-1 / Type-2 IGT engine mapping tables and A1-ready term definitions
- strong markers:
  - overlay language remains removable and verification-bound
  - Thread-B remains label-free
  - IGT is checksum/discovery language, not kernel law

## 5) Source-Class Read
- best classification:
  - archived derived extraction package over low-entropy foundation docs
- useful as:
  - historical witness of an older A2 layered-extraction method
  - compact contradiction packet for axis/geometry/IGT/order tensions
  - evidence that archive retention includes result-only extraction ZIPs, not just raw docs and run dumps
- not best classified as:
  - current active A2 law
  - embedded raw source corpus
  - standalone authority over present axis semantics
- possible downstream consequence:
  - later archive passes can compare this package’s contradiction set and overlay handling against current active A2 fences without treating the package as current truth
