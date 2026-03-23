# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a2state_live_state_index_packet__v1`
Extraction mode: `ACTIVE_A2_LIVE_STATE_AND_INGEST_INDEX_PASS`
Date: 2026-03-09

## T1) `DUPLICATE_INGEST_INDEX_MEMBERSHIP_VS_DIFFERENT_HASHED_ARTIFACTS`
- tension:
  - `core_docs_ingest_index_v1.json` and `ingest/index_v1.json` both index the same `215` docs
  - the files were generated at different times and hash to different artifact values
- preserve:
  - same membership does not mean one physical index artifact
- main sources:
  - `core_docs_ingest_index_v1.json`
  - `core_docs_ingest_index_v1.sha256`
  - `ingest/index_v1.json`
  - `ingest/index_v1.sha256`

## T2) `DOC_INDEX_BROADER_CLASSIFICATION_VS_SMALLER_INGEST_INDICES`
- tension:
  - `doc_index.json` expands to `222` documents with explicit layer/status fields
  - the ingest indices stay at `215` docs with a narrower inventory schema
- preserve:
  - classification scope and ingest inventory scope are not the same thing
- main sources:
  - `doc_index.json`
  - `core_docs_ingest_index_v1.json`
  - `ingest/index_v1.json`

## T3) `DOC_CARD_SYSTEM_MAP_ID_NAMESPACE_VS_INGEST_INDEX_DOC_ID_NAMESPACE`
- tension:
  - `ingest/system_map_v1.md` and `ingest/doc_cards/*.md` use one `DOC_*` namespace
  - `ingest/index_v1.json` uses a different `doc_id` namespace for the same-looking source families
- preserve:
  - the curated abstraction overlay and the ingest index are related but not id-compatible
- main sources:
  - `ingest/system_map_v1.md`
  - `ingest/doc_cards/*.md`
  - `ingest/index_v1.json`

## T4) `SYSTEM_MAP_PATH_LABELS_VS_CURRENT_INDEX_PATHS`
- tension:
  - `ingest/system_map_v1.md` uses path labels like `core_docs/high entropy doc/...` and `system_spec_pack_v2/...`
  - `ingest/index_v1.json` and `doc_index.json` use different current paths for the indexed corpus
- preserve:
  - the map is a useful abstraction surface
  - it is not a path-accurate mirror of the ingest index
- main sources:
  - `ingest/system_map_v1.md`
  - `ingest/index_v1.json`
  - `doc_index.json`

## T5) `AUTOSAVE_COUNTER_ALIGNMENT_VS_NONCONTEMPORANEOUS_SNAPSHOTS`
- tension:
  - `autosave_seq.txt` and the last `memory.jsonl` autosave tick align at `233`
  - `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json` is an older compact snapshot with different state counts and purpose
- preserve:
  - local autosave consistency does not make every control snapshot contemporaneous
- main sources:
  - `autosave_seq.txt`
  - `memory.jsonl`
  - `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json`

## T6) `SURVIVOR_AND_ADMISSION_COUNTS_ARE_NOT_THE_SAME_METRIC`
- tension:
  - `campaign_status` reports `7` kernel survivors
  - `constraint_surface` reports `43` survivors and `8` graveyard items
  - `rosetta.json` holds `41` mappings
- preserve:
  - these counts refer to different layers of state and cannot be merged into one progress number
- main sources:
  - `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json`
  - `constraint_surface.json`
  - `rosetta.json`

## T7) `SEMANTIC_EVENT_CORE_VS_AUTOSAVE_NOISE_DOMINANCE`
- tension:
  - `memory.jsonl` contains meaningful campaign, runtime, A1, and ingest events
  - the file is numerically dominated by `a2_autosave_tick`
- preserve:
  - autosave churn is operationally real
  - it should not overshadow the smaller semantic event core in later reductions
- main sources:
  - `memory.jsonl`
  - `memory_shards/memory_shard_000001.jsonl`

## T8) `ACTIVE_ROSETTA_STORE_UPDATE_LANGUAGE_VS_INTAKE_ONLY_MUTATION_RULE`
- tension:
  - `rosetta.json` and `a1_brain.jsonl` imply live updating when B admits terms and A1 reports back
  - this worker lane is intake-only and cannot mutate active state surfaces
- preserve:
  - the files are evidence of current state and intended update semantics
  - this batch only compresses them into intake artifacts
- main sources:
  - `rosetta.json`
  - `a1_brain.jsonl`
  - cross-batch anchor: `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/a2_high_entropy_intake_surface/A2_HIGH_ENTROPY_INTAKE_PROCESS__v1.md`

## T9) `DOC_CARD_USEFULNESS_VS_DOC_CARD_NONOWNER_STATUS`
- tension:
  - the doc cards are useful compressed views of purpose, fences, and role
  - many cards mark `NONE_SPECIFIED`, `UNMAPPED`, or mixed multi-role assignments and therefore cannot outrank owner sources
- preserve:
  - cards are high-value abstractions
  - they remain abstraction surfaces rather than owner doctrine
- main sources:
  - `ingest/doc_cards/*.md`
  - `ingest/system_map_v1.md`

## T10) `QUARANTINE_CLASSIFICATION_VS_ACTIVE_INDEX_PRESENCE`
- tension:
  - `doc_index.json` still indexes `16` high-entropy sources under `QUARANTINE_SOURCE`
  - the same file lives inside the active A2 state packet as a current operational index
- preserve:
  - indexed presence does not imply trusted admission
- main source:
  - `doc_index.json`
