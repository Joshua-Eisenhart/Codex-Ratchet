# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_root_policy_lineage__v1`
Extraction mode: `ARCHIVE_LINEAGE_PASS`
Batch scope: first archive-root policy and generated-metadata family in top-level folder order
Date: 2026-03-09

## 1) Batch Selection
- selected sources:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/A1_ROSETTA_v1.json`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/A2_BRAIN_v1.json`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/README__ARCHIVE_POLICY_v1.md`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/DOC_INDEX.md`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/SYSTEM_PROCESS_AUDIT.md`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/MIGRATION_LOG__20260224_070730Z.txt`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/CLEANUP_BOOKKEEPING__20260224T204957Z.txt`
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/CLEANUP_BOOKKEEPING__20260224T205138Z.json`
- reason for bounded family batch:
  - these are the first high-signal archive-root docs in folder order before the first `BATCH_01_OF_10...zip` package
  - together they define archive role, migration lineage, cleanup/demotion behavior, generated retained-memory mirrors, and a process-status snapshot
  - this keeps the first batch at archive-root scope and avoids prematurely descending into ZIP contents, heat dumps, or deep milestone run families
- deferred next bounded batch in folder order:
  - `/home/ratchet/Desktop/Codex_Ratchet__archive/BATCH_01_OF_10__A2_LAYER1_5__OUTPUT__CORE_CONSTRAINT_LADDER_AXIS_FOUNDATION__v1_1.zip`

## 2) Source Membership
### Source 1
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/README__ARCHIVE_POLICY_v1.md`
- sha256: `f4db49cb259d9c532a40e3f88c1477502fdfc93153ece6810a9634fd32e98370`
- size bytes: `690`
- line count: `22`
- source class: archive-root policy plaque

### Source 2
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/MIGRATION_LOG__20260224_070730Z.txt`
- sha256: `9fcb66c21d72fb8a3bd2c73fd401f1438c75d9cf7abe01c45ba6b393a09bb6f3`
- size bytes: `2961`
- line count: `24`
- source class: archive migration and demotion move log

### Source 3
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/CLEANUP_BOOKKEEPING__20260224T204957Z.txt`
- sha256: `fe4a323e292f40eccecd767c9605c319f2f955b7015e864b1f238ba2ca9be972`
- size bytes: `32057`
- line count: `227`
- source class: cleanup residue and duplicate-dir deletion log

### Source 4
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/CLEANUP_BOOKKEEPING__20260224T205138Z.json`
- sha256: `1c8b135cf878ae09f3892f85a9987453f1d6ac9c55326b869f6303021d341869`
- size bytes: `3034`
- line count: `64`
- source class: cleanup summary and byte-delta record

### Source 5
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/SYSTEM_PROCESS_AUDIT.md`
- sha256: `d0fe77c8837a70d239ed4a8c2d2d79b0f1b6c790611b84579eda18f330d0e01b`
- size bytes: `6873`
- line count: `109`
- source class: archived process maturity snapshot

### Source 6
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/DOC_INDEX.md`
- sha256: `c6d73c46317f1a76383fca540bbe5118b5b268f2461ad13abd2ffa8dce9303c8`
- size bytes: `3458975`
- line count: `35577`
- source class: generated processed-doc lookup index

### Source 7
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/A2_BRAIN_v1.json`
- sha256: `6f8f640c5786ac79a8c18d174ddf31cf479cecba85a6444e7ed09f3c6e434ba9`
- size bytes: `10299066`
- line count: `58831`
- source class: generated archive-held A2 content mirror

### Source 8
- path: `/home/ratchet/Desktop/Codex_Ratchet__archive/A1_ROSETTA_v1.json`
- sha256: `19e06505f820cb8bf11dc7a6bbab64f09e8fb1fd8d5a2869a7bf84d444af392f`
- size bytes: `2952669`
- line count: `115097`
- source class: generated archive-held A1 candidate-mapping mirror

## 3) Structural Map Of The Sources
### Segment A: archive-root role and tier semantics
- source anchors:
  - source 1: whole file
  - source 2: move targets
- source role:
  - defines the archive as retention-only and shows the first concrete move set that instantiated that policy
- strong markers:
  - archive root is outside active runtime surfaces by design
  - tier names are `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`, `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`, and `LEGACY_REFERENCE__READ_ONLY`
  - no live runtime writes or canonical replay should depend on this tree

### Segment B: demotion and cleanup lineage
- source anchors:
  - source 2: whole file
  - source 3: `deleted_archive_duplicate_dirs` and pre/post counts
  - source 4: `before`, `after`, `deleted`, and `planned`
- source role:
  - records how active-path material was moved into archive tiers and later thinned for duplicate or cache residue
- strong markers:
  - whole directories and ZIP saves were moved into archive tiers on `2026-02-24`
  - cleanup later removed `__pycache__`, `.DS_Store`, and zero-byte duplicate directories while reporting byte deltas
  - the archive therefore preserves both demotion history and post-demotion residue management

### Segment C: generated archive mirror layer
- source anchors:
  - source 6: whole file
  - source 7: metadata plus entry population
  - source 8: metadata plus entry population
- source role:
  - exposes a generated lookup and mirror layer sitting at the archive root above the retained raw families
- strong markers:
  - `A2_BRAIN_v1.json` and `A1_ROSETTA_v1.json` each contain `6536` entries
  - both files share the exact same concept-id set
  - `A2_BRAIN_v1.json` spans `2460` unique `source_documents`
  - `A1_ROSETTA_v1.json` explicitly labels its mappings as candidate extraction notes, not assertions
  - `DOC_INDEX.md` is generated from processed documents found in the workspace and extracted archives, so it is broad lookup coverage rather than archive-root law

### Segment D: process maturity snapshot
- source anchors:
  - source 5: component status table and evidence hits
- source role:
  - preserves a time-bounded process audit inside the archive root
- strong markers:
  - `A0_COMPILER`, `B_CONSTRAINT_KERNEL`, `SIM_EVIDENCE_LAYER`, and `GRAVEYARD_PROTOCOL` are marked `PASS`
  - `A2_DISTILLERY`, `A1_ROSETTA`, and `APPEND_RATCHET_LEDGER` are marked `INCOMPLETE`
  - the archive root therefore retains a partial upgrade-state snapshot rather than a fully settled doctrine set

### Segment E: observed archive-root tier inventory
- source anchors:
  - archive-root directory inventory observed during batch selection
- source role:
  - shows current mass distribution across archive tiers without reading deep contents yet
- strong markers:
  - `CACHE__HIGH_ENTROPY__RECENT__PURGEABLE`: `11` files / `1` directory
  - `DEEP_ARCHIVE__LOW_ENTROPY__MILESTONES_ONLY`: `7805` files / `183` directories
  - `HEAT_DUMPS`: `68806` files / `2164` directories
  - `LEGACY_REFERENCE__READ_ONLY`: `227` files / `21` directories
  - `ops_logs`: `1` file / `0` directories

## 4) Source-Class Read
- best classification:
  - archive-root retention policy plus demotion lineage plus generated historical lookup mirrors
- useful as:
  - entry-point map for how the external archive is structured
  - lineage evidence for demotion-before-delete behavior
  - quarantine map for archive-held brain and rosetta mirrors that look active but are not current control memory
- not best classified as:
  - current active A2 law
  - current runtime replay source
  - a curated final doctrine layer
- possible downstream consequence:
  - later archive passes should split by tier and artifact class:
    - first ZIP family packages
    - deep-archive milestone runs
    - heat-dump demotion batches
    - legacy read-only references
