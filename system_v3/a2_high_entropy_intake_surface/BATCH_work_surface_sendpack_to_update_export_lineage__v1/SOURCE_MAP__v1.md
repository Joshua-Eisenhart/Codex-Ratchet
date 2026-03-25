# SOURCE_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_work_surface_sendpack_to_update_export_lineage__v1`
Extraction mode: `PACKAGED_EXPORT_LINEAGE_PASS`
Batch scope: wrapped Stage-3 send pack plus first `work/out` return, delta, update-pack, and checksum sidecar family
Date: 2026-03-09

## 1) Folder-Order Selection
- primary export-lineage family:
  - `/home/ratchet/Desktop/Codex Ratchet/work/PRO_SEND_PACK__A2_LAYER1_5__STAGE3_BATCHES_10__v1_1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip.sha256`
- bundling reason:
  - together these files show one spillover export arc:
    - a ten-job Stage-3 handoff set repackaged as one wrapper zip
    - an outputs-only return artifact
    - a deliberately tiny missing-doc delta pack
    - a broad system update pack
  - the paired `.sha256` sidecars show a second integrity convention:
    - detached digest only
    - no filename binding inside the sidecar itself
- deferred near-neighbor revision family:
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v2.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v2.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v3.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v3.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v4.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v4.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v2.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v2.zip.sha256`
- deferred next docs in folder order:
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v2.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v2.zip.sha256`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v3.zip`
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v3.zip.sha256`

## 2) Source Membership
- source 1:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/PRO_SEND_PACK__A2_LAYER1_5__STAGE3_BATCHES_10__v1_1.zip`
  - sha256: `13ec9c7f081b71ee6d04f7bf8e7fcca141ae85e6d74d0c8613c9e32a88eefc49`
  - size bytes: `1754443`
  - entry count: `14`
  - readable status in this batch: wrapper archive
  - source-class note:
    - wraps the previously separated Stage-3 directory as one transferable shell containing the ten child job zips plus the three Stage-3 control files
- source 2:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip`
  - sha256: `bbd84126f93e5eb648c697cbbe92f634c85cdde44fe430813cf16403b5e5e0eb`
  - size bytes: `1327933`
  - entry count: `5`
  - readable status in this batch: outputs-only return pack
  - source-class note:
    - an intentionally narrow output artifact preserving filtered A2 brain material, counts, doc index, and a non-authoritative audit
- source 3:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip.sha256`
  - sha256: `17e580cf34c27600719fa7c23636601c81ed2ce4b824d14aaedc42bd3c4e4811`
  - size bytes: `65`
  - line count: `1`
  - readable status in this batch: detached checksum sidecar
  - source-class note:
    - preserves only the archive digest, with no filename on the line
- source 4:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip`
  - sha256: `20f4983c0d80db5709df3682b9cd759b89cde9fa2fafe00befab8220fa94b88a`
  - size bytes: `32504`
  - entry count: `24`
  - readable status in this batch: small missing-doc delta pack
  - source-class note:
    - explicitly limited to the missing canon-lock bridge docs, Playwright claw, and operator notes needed to update an external Pro thread without sending full trees
- source 5:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip.sha256`
  - sha256: `007d1e20752a777e0ac71aa28394240ae695b28caabaa47b6a58fd6639aa5837`
  - size bytes: `65`
  - line count: `1`
  - readable status in this batch: detached checksum sidecar
  - source-class note:
    - same digest-only sidecar convention as the Stage V1 outputs pack
- source 6:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`
  - sha256: `30a4fe1116dd9421c3e6ef23269cd98762f519f17d9060b834c1a3cc9d1f826f`
  - size bytes: `7477771`
  - entry count: `649`
  - readable status in this batch: broad update pack
  - source-class note:
    - re-expands the export surface into bundles, examples, core docs, and `system_v3` state, with an internal manifest declaring `648` copied files
- source 7:
  - path: `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip.sha256`
  - sha256: `93e822986f1a34802ec2aa94cbe38e62a9be3855aa02c0f157fbf1ac8f6516ad`
  - size bytes: `65`
  - line count: `1`
  - readable status in this batch: detached checksum sidecar
  - source-class note:
    - confirms the same pathless sidecar checksum style even for the largest export in the family

## 3) Structural Map
### Segment A: one-file wrapper around the Stage-3 serialized handoff set
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/PRO_SEND_PACK__A2_LAYER1_5__STAGE3_BATCHES_10__v1_1.zip`
- key markers:
  - `14` archive entries total
  - one embedded `TO_SEND_TO_PRO__A2_LAYER1_5__STAGE3__v1_1/` directory
  - ten child job zips
  - embedded Stage-3 manifest, send-order, and checksum files
- strongest read:
  - the earlier multi-file Stage-3 send set is compressed into a single transport object, but the inner handoff logic is still the same serial child-job program

### Segment B: outputs-only return artifact
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_CONTEXT__STAGE_V1_OUTPUTS__v1.zip`
- key markers:
  - embedded README says the pack is from a prior `SYSTEM_BOOTSTRAP_STAGE_v1` style pass
  - explicitly outputs-only
  - no `system_v3` or `core_docs`
  - excludes `A1_ROSETTA_v1.json` on purpose
- strongest read:
  - this pack models lean return hygiene by shipping only distilled outputs and explicitly omitting system trees and a low-value rosetta artifact

### Segment C: drift-prevention delta pack
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_DELTA__CANON_LOCK_PLUS_CLAW__v1.zip`
- key markers:
  - embedded README says the zip is intentionally small
  - only missing docs/scripts not already in the Pro thread
  - includes canon-lock runtime bridge docs
  - includes Playwright claw and MiniMax/Codex handoff notes
  - excludes full `system_v3`, full `core_docs`, runs, and large corpora
- strongest read:
  - this export is optimized for minimizing drift while adding only the bridge surfaces needed to make external WebUI execution usable

### Segment D: repair overlay read-first remains unchanged across export tiers
- sources:
  - embedded `CANON_LOCK/00_READ_FIRST.md` in the delta pack
  - embedded `CANON_LOCK/00_READ_FIRST.md` in the update pack
- key markers:
  - `REPAIR/ALIGNMENT overlay`
  - does not replace `SYSTEM/` contents
  - A2/A1/A0/B/SIM/Graveyard role split
  - fail-closed bootstrap framing
- strongest read:
  - the export family changes size drastically, but the top-level repair overlay narrative stays stable

### Segment E: broad system update pack
- source:
  - `/home/ratchet/Desktop/Codex Ratchet/work/out/PRO_THREAD_UPDATE_PACK__SYSTEM_V3_PLUS_CANON_LOCK_PLUS_CLAW__v1.zip`
- key markers:
  - embedded manifest declares `648` copied files
  - bundled bootstrap zip and its `.sha256`
  - example distillery output zip
  - `SYSTEM/core_docs/Archive.zip`
  - large `SYSTEM/system_v3/*` subtree including `a2_state/doc_index.json`
  - mojibake-style filename residue appears inside bundled high-entropy doc paths
- strongest read:
  - the export line swings back from minimal delta to a near-full environment pack, carrying both useful completeness and obvious migration residue

### Segment F: detached checksum sidecars
- sources:
  - the three `.sha256` files in `work/out/`
- key markers:
  - each file is one line
  - each line contains only the digest
  - no filename is recorded inside the sidecar
- strongest read:
  - integrity is preserved, but filename binding is pushed out to surrounding path context rather than carried by the checksum file itself

## 4) Structural Quality Notes
- this batch is useful because it captures an export progression rather than one isolated packet:
  - wrapped send pack
  - lean return
  - tiny delta
  - broad update pack
- the family is not current law:
  - every artifact lives under `work/`
  - the wrapper and exported packs are spillover transport residues, not active `system_v3` bundle doctrine
  - embedded readmes describe intended use, not proof of successful downstream installation
- important migration debt preserved:
  - checksum sidecars lose filename self-description
  - the broad update pack re-bloats after the small-delta discipline
  - bundled path names show encoding damage in at least some imported high-entropy files

## 5) Source-Class Read
- best classification:
  - export-packaging lineage residue
  - external-thread handoff and return archaeology
- not best classified as:
  - active transport law
  - proof that the exported updates were applied
  - direct source admission of every bundled payload file
- likely trust placement under current A2 rules:
  - useful for migration-debt mapping, export-scope comparison, and checksum-convention comparison
  - not sufficient to outrank active protocol surfaces or active repo-state evidence
