# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_batch02_axes_apple_notes_igt_mapping__v1`
Extraction mode: `ARCHIVE_LAYERED_EXTRACTION_PACKAGE_PASS`
Batch scope: second archived packaged layered-extraction output zip in archive-root folder order
Date: 2026-03-09

## 1) Batch Selection
- selected source:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/BATCH_02_OF_10__A2_LAYER1_5__OUTPUT__AXES_APPLE_NOTES_IGT_MAPPING__v1_1.zip`
- reason for bounded single-package batch:
  - this is the next archive-root item in folder order after the batch-01 package
  - it is still self-contained at the output layer, but it fronts much higher-entropy source material than batch 01
  - processing it alone preserves its specific apple-notes / thread-save / axis-0 tensions without flattening them into the rest of the archive
- deferred next bounded batch in folder order:
  - `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/BATCH_03_OF_10__A2_LAYER1_5__OUTPUT__PHYSICS_GROK_HOLODECK_CLUSTER__v1_1.zip`

## 2) Source Membership
### Primary container
- path: `/Users/joshuaeisenhart/Desktop/Codex_Ratchet__archive/BATCH_02_OF_10__A2_LAYER1_5__OUTPUT__AXES_APPLE_NOTES_IGT_MAPPING__v1_1.zip`
- sha256: `3623d08b24f91f9de25f745db3b0b6bbf05d10667f1f8d5e3e1e63ddeb36ce59`
- size bytes: `41403`
- container member count: `30`
- source class: archived derived A2 layered-extraction output package

### Embedded members read directly for this batch
- member:
  - path: `output/PORTABLE_OUTPUT_CONTRACT_AND_FAIL_CLOSED_VALIDATION__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__file_fence_and_retry_rules__primary_view__v1.0.md`
  - sha256: `bc5ad67867c38cf9d87fc8cf9890bbb665019439db54fe2984f4a99da37894d6`
  - size bytes: `1743`
  - line count: `45`
- member:
  - path: `output/DOCUMENT_NORMALIZATION_AND_SHARD_REPORT__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__deterministic_prep_and_shard_map__primary_view__v1.0.md`
  - sha256: `665efdf529504adc167e37f354270e21e2ae41dc6bbff0a70f388139604df018`
  - size bytes: `7985`
  - line count: `129`
- member:
  - path: `output/DOCUMENT_META_MANIFEST__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__topic_inventory_and_output_registry__primary_view__v1.0.md`
  - sha256: `6b8194bad05fc6380fb3ed89a09862a1f1a2e8b3e82c8b591bb78963c6687e89`
  - size bytes: `15394`
  - line count: `171`
- member:
  - path: `output/DOCUMENT_GENERAL_SUMMARY__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__high_level_map_without_smoothing__primary_view__v1.0.md`
  - sha256: `50a27d8626b9271d1398cce61334a9224e877554d1fe56c8ad26ab539f41be5d`
  - size bytes: `3404`
  - line count: `48`
- member:
  - path: `output/DOCUMENT_TOPIC_INDEX__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__explicit_topic_map__primary_view__v1.0.md`
  - sha256: `b8ed16f9ae3ab20f8d6686ed5ed3e93162f1e2534a5107b45f80af1d8f286f7f`
  - size bytes: `2490`
  - line count: `34`
- member:
  - path: `output/QUALITY_GATE_REPORT__A2_DOC_LAYERED_MULTI_TOPIC_FULL_EXTRACTION__source_scope__completeness_and_no_smoothing_validation__primary_view__v1.0.md`
  - sha256: `c21cccd41b1eb1b873c97e033f6a133058ae0827d93df3c78f85716817236d33`
  - size bytes: `2044`
  - line count: `38`
- member:
  - path: `output/A2_BRAIN_UPDATE_PACKET__persistent_structural_laws_and_invariants_for_future_extractions__primary_view__v1.0.md`
  - sha256: `0626481fad507f06d3db960e47076603a910806b661b46750f797b7a041742f6`
  - size bytes: `3779`
  - line count: `41`
- member:
  - path: `output/A1_BRAIN_ROSETTA_UPDATE_PACKET__engine_rosetta_patterns_ready_for_a1_sandbox_use__primary_view__v1.0.md`
  - sha256: `f58f32f9646f34e5b521bb94963e0858a5385f3a3f2ea284a0316f5fb8f589c9`
  - size bytes: `3533`
  - line count: `54`

## 3) Package-Declared Source Corpus
- declared input document count: `5`
- declared source root inside package reporting:
  - `input/payload/*`
- declared input members:
  - `input/payload/axes math. apple notes dump.txt`
  - `input/payload/apple notes save. pre axex notes.txt`
  - `input/payload/A0 new thread save before sim run.md`
  - `input/payload/AXIS0_SPEC_OPTIONS_v0.3.md`
  - `input/payload/AXIS0_PHYSICS_BRIDGE_v0.1.md`
- declared corpus scale:
  - `axes math. apple notes dump.txt`: `385011` bytes / `17701` lines
  - `apple notes save. pre axex notes.txt`: `93828` bytes / `1798` lines
  - `A0 new thread save before sim run.md`: `446897` bytes / `14807` lines
  - `AXIS0_SPEC_OPTIONS_v0.3.md`: `5584` bytes / `160` lines
  - `AXIS0_PHYSICS_BRIDGE_v0.1.md`: `4158` bytes / `109` lines
- declared sharding:
  - `24` shard paths listed in the normalization report
- important archive fact:
  - the zip stores only `output/` files
  - the declared `input/payload/` docs and `shards/` files are referenced by locators/reporting but are not embedded in the archive package

## 4) Structural Map Of The Package
### Segment A: result-only output contract
- source anchors:
  - embedded member: portable output contract
  - embedded member: quality gate
- source role:
  - defines this archive item as a fail-closed validated output ZIP, not a chat transcript or raw source bundle
- strong markers:
  - preferred return mode is `ZIP_ATTACHMENT`
  - fail-closed rejection rules are all marked `YES`
  - validation verdict is `PASS`
  - `30` output files are present

### Segment B: high-entropy declared input family
- source anchors:
  - embedded member: normalization report
  - embedded member: topic index
- source role:
  - shows that this package distilled very large apple-notes and thread-save material plus Axis-0 spec surfaces
- strong markers:
  - `24` declared shards
  - source family mixes notes, thread save, and lower-entropy Axis-0 spec/bridge docs
  - topic locators are concentrated in the apple-notes and thread-save sources

### Segment C: locked rosetta and invariant layer
- source anchors:
  - embedded member: A2 brain update packet
  - embedded member: A1 brain rosetta update packet
  - embedded member: quality gate
- source role:
  - preserves a strong lock-oriented engine/IGT extraction packet
- strong markers:
  - Major/Outer = CAPS, Minor/Inner = lowercase
  - Axis-3 rank only, not ordering
  - balanced engine payoff counts
  - terrain set lock
  - IGT label order is `T then F`
  - QIT realization sign lock
  - Type-1 / Type-2 mirror relation
  - Axis-0 as allostatic vs homeostatic correlation polarity

### Segment D: governance and societal projection layer
- source anchors:
  - embedded member: document general summary
  - engine and governance topic summaries
  - contradiction maps
- source role:
  - projects engine/axis/IGT language into societal resilience and governance/scientific-method loops
- strong markers:
  - engine-to-society mapping
  - bidirectional scientific method as governance loop
  - agent arrays and holodeck/tricorder world-model building
  - resilience/adaptation/evolutionary fitness framing

### Segment E: mirror, oracle, and alignment layer
- source anchors:
  - mirror topic summary
  - document general summary
- source role:
  - reframes alignment as both socio-cultural manifold reflection and formal world-model robustness
- strong markers:
  - AI as mimetic manifold
  - humans as oracle
  - alignment via diversity preservation
  - oracle-guided survivorship filtering
  - allostasis vs homeostasis under perturbation

### Segment F: retained contradiction set
- source anchors:
  - document general summary
  - all three topic contradiction maps
- source role:
  - preserves the package’s main unresolved worldview and anti-drift tensions
- strong markers:
  - diversity vs leviathan box centralization
  - best-win optimization vs future-options framing
  - Axis-4 vs Major/Minor naming conflict
  - induction/data-first vs prediction-first
  - teleology vs no-teleology boot quarantine
  - socio-cultural alignment vs formal robustness definition split
  - allostatic vs homeostatic polarity under-specified conditions

## 5) Source-Class Read
- best classification:
  - archived derived extraction package over high-entropy apple-notes / thread-save material with some lower-entropy Axis-0 support docs
- useful as:
  - historical witness of how apple-notes / IGT / governance / alignment material was compressed into a locked extraction packet
  - contradiction packet for manifold diversity, teleology, governance centralization, and alignment-definition splits
  - lineage source for explicit IGT mapping locks and Axis-0 polarity framing
- not best classified as:
  - current active A2 law
  - embedded raw source corpus
  - settled authority on governance or alignment doctrine
- possible downstream consequence:
  - later archive passes can mine this package for historical contradiction lineage and mapping-lock ancestry while requiring stronger current-source corroboration before any selective promotion
