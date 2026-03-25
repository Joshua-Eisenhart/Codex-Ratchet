# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_work_surface_stage3_pro_send_packaging__v1`
Extraction mode: `OUTBOUND_HANDOFF_PACKAGING_PASS`
Batch scope: inbox micro-coordination plaque plus Stage-3 Pro send-pack manifest/send-order/checksum trio
Date: 2026-03-09

## 1) Folder-Order Selection
- primary outbound packaging family:
  - `/home/ratchet/Desktop/Codex Ratchet/work/INBOX/README.md`
  - `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__MANIFEST__STAGE3_PRO_RUN__v1_1.json`
  - `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__SEND_ORDER__STAGE3_PRO_RUN__v1_1.md`
  - `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__SHA256__STAGE3_PRO_RUN__v1_1.txt`
- bundling reason:
  - the inbox plaque defines the smallest allowed coordination sidechannel for cross-operator exchange
  - the Stage-3 trio defines the formal machine-facing handoff contract for a ten-batch outbound Pro run
  - together they show one spillover packaging stack:
    - minimal human note lane
    - explicit batch inventory
    - exact send-order contract
    - checksum closure
- deferred wrapped members in this folder:
  - the Stage-3 directory also contains ten child input-job zips referenced by the manifest/send-order/checksum trio
  - those child zips are preserved as deferred wrapped members rather than direct sources in this batch
- deferred next docs in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/work/PRO_SEND_PACK__A2_LAYER1_5__STAGE3_BATCHES_10__v1_1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`

## 2) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/INBOX/README.md`
  - sha256: `128d03acc22a5fc87495b755f41c7763757d5b37b0ec2174e1a5f6facfe03aa2`
  - size bytes: `243`
  - line count: `11`
  - readable status in this batch: coordination plaque
  - source-class note:
    - establishes a tiny, explicit, dated note lane for Codex/Minimax exchange and says the directory is maintenance-owned by `lean_promote_and_prune.py`
- source 2:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__MANIFEST__STAGE3_PRO_RUN__v1_1.json`
  - sha256: `6e271ad8f4f45767ad045a0a4044d5b7c4ec78a9506a50e9e2650a04354eea9d`
  - size bytes: `6970`
  - line count: `155`
  - readable status in this batch: batch-set inventory contract
  - source-class note:
    - declares a ten-job Stage-3 set with subjects, job dirs, zip names, and payload refs for each outbound unit
- source 3:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__SEND_ORDER__STAGE3_PRO_RUN__v1_1.md`
  - sha256: `e0b3707ebcc946c9a27af10196b397b6945ffde9b719142504978c73c7dc7c5f`
  - size bytes: `2069`
  - line count: `56`
  - readable status in this batch: execution-order and return-contract plaque
  - source-class note:
    - constrains dispatch to one zip per fresh thread, one exact instruction string, and an output-only return format
- source 4:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__SHA256__STAGE3_PRO_RUN__v1_1.txt`
  - sha256: `c1dae421aaee311a44593350f7b39286ba7fc384e4496d9354c5487291dcf950`
  - size bytes: `1501`
  - line count: `10`
  - readable status in this batch: filename-binding and integrity ledger
  - source-class note:
    - closes the transport set with hashes for the ten child zips and exposes naming drift against the other two control files

## 3) Structural Map
### Segment A: inbox micro-coordination boundary
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/INBOX/README.md`
- key markers:
  - small coordination notes only
  - explicit and dated naming
  - Codex/Minimax exchange
  - maintenance delegated to `system_v3/tools/lean_promote_and_prune.py`
- strongest read:
  - the spillover workspace keeps a deliberately tiny human note lane even when adjacent transport packets are large and formal

### Segment B: batch-set inventory and payload decomposition
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__MANIFEST__STAGE3_PRO_RUN__v1_1.json`
- key markers:
  - `BATCH_SET_MANIFEST_v1`
  - `batch_count: 10`
  - per-batch subject names
  - per-batch `job_dir`, `zip_name`, `payload_file_count`, and `payload_refs`
- strongest read:
  - the outbound run is not one vague archive; it is an explicitly sharded ten-job program with preserved payload provenance inside the wrapper manifest

### Segment C: single-attachment thread discipline
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/BATCH_SET__A2_LAYER1_5__SEND_ORDER__STAGE3_PRO_RUN__v1_1.md`
- key markers:
  - exactly one batch zip per fresh thread
  - exact send text
  - returned zip should contain only `output/`
  - ordered batch list with payload counts
- strongest read:
  - the process optimizes for repeatable serial dispatch and strict result hygiene rather than rich conversational handling

### Segment D: checksum closure and filename drift
- sources:
  - send-order plaque
  - checksum ledger
  - actual child zip filenames in the Stage-3 directory
- key markers:
  - checksum entries use the real double-underscore filenames before `__v1_1.zip`
  - manifest/send-order entries use triple underscores before `___v1_1.zip`
  - the actual directory contents match the checksum ledger, not the manifest/send-order spelling
- strongest read:
  - the packaging family is disciplined enough to preserve hashes, but still carries a concrete control-file naming inconsistency

## 4) Structural Quality Notes
- this batch is useful because it captures one coherent outbound packaging method:
  - keep human coordination tiny
  - serialize multi-job dispatch
  - constrain the operator message
  - require output-only returns
  - bind files by checksum
- the family is not current law:
  - every source sits under `work/`
  - the send contract is spillover packaging residue, not active ZIP protocol authority
  - the ten child zips are referenced but not promoted to direct-source truth here
- important contradiction preserved:
  - the control packet presents itself as exact and operational
  - the filename layer still drifts between manifest/send-order and checksum/actual files

## 5) Source-Class Read
- best classification:
  - outbound Pro handoff residue
  - process archaeology for serialized single-attachment packaging
- not best classified as:
  - active transport law
  - proof that the handoff set was executed successfully
  - payload-level semantic extraction of the ten jobs themselves
- likely trust placement under current A2 rules:
  - useful for transport-pattern archaeology, checksum discipline, and migration-debt capture
  - not sufficient to outrank active `system_v3` protocol surfaces
