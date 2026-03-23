# CLUSTER_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_systemv3_active_a2state_live_state_index_packet__v1`
Extraction mode: `ACTIVE_A2_LIVE_STATE_AND_INGEST_INDEX_PASS`
Date: 2026-03-09

## Cluster A: `LIVE_STATE_CONTROL_REGISTRIES`
- source members:
  - `a1_brain.jsonl`
  - `autosave_seq.txt`
  - `campaign_status/CAMPAIGN_STATUS__20260224T225042Z.json`
  - `constraint_surface.json`
  - `fuel_queue.json`
  - `rosetta.json`
- reusable payload:
  - A1 event memory
  - autosave counter
  - compact campaign snapshot
  - blocked-concept summary
  - extracted fuel queue
  - active jargon-to-B mapping store
- possible downstream consequence:
  - later A2-mid work can explain what the system believes its current active registries are without needing to reread every append log

## Cluster B: `INGEST_INDEX_AND_CLASSIFICATION_PACKET`
- source members:
  - `core_docs_ingest_index_v1.json`
  - `core_docs_ingest_index_v1.sha256`
  - `doc_index.json`
  - `ingest/index_v1.json`
  - `ingest/index_v1.sha256`
- reusable payload:
  - corpus inventory
  - integrity sidecars
  - layer/status classification
  - quarantine marking
  - extra-path exposure outside the smaller ingest set
- possible downstream consequence:
  - strong feedstock for later active-source inventory and index-reconciliation work

## Cluster C: `DOC_CARD_AND_ROLE_ABSTRACTION_PACKET`
- source members:
  - `ingest/system_map_v1.md`
  - `ingest/doc_cards/*.md`
- reusable payload:
  - curated role map
  - purpose/fence/container/card abstraction
  - mixed-role assignment over a smaller curated subset
- possible downstream consequence:
  - later A2/A1 reduction can treat this cluster as a doc-abstraction overlay rather than as a direct owner-model truth layer

## Cluster D: `MEMORY_CHAIN_AND_SHARD_PACKET`
- source members:
  - `memory.jsonl`
  - `memory_shards/index_v1.json`
  - `memory_shards/index_v1.sha256`
  - `memory_shards/memory_shard_000001.jsonl`
- reusable payload:
  - shard continuity
  - append-log chronology
  - autosave cadence
  - base memory categories
- possible downstream consequence:
  - later maintenance or ingestion work can distinguish long-lived semantic memory from repetitive autosave/state churn

## Cross-Cluster Couplings
- Cluster A stores the compact registries the system uses to summarize itself.
- Cluster B stores the corpus inventory and classification surfaces those registries implicitly depend on.
- Cluster C sits above Cluster B as a curated doc-abstraction overlay with its own id/path scheme.
- Cluster D provides the chronological continuity that explains how Cluster A changes over time.
