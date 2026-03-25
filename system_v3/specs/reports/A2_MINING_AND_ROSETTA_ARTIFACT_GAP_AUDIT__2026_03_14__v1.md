# A2_MINING_AND_ROSETTA_ARTIFACT_GAP_AUDIT__2026_03_14__v1
Status: NONCANON / AUDIT
Date: 2026-03-14

## Scope

Audit current mining/Rosetta tooling against:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`

Legacy witness:
- `/home/ratchet/Desktop/Codex Ratchet/core_docs/BOOTPACKS/BOOTPACK_THREAD_M_v1.0.md`

Audited files:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/legacy_extract.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_cold_core_strip.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/ingest_a2_distillery_zip.py`

## Findings

### 1. `legacy_extract.py` is a migration scanner, not a mining artifact builder

Current legacy extractor scans old markdown files for keyword/role hits and writes one JSON report.

Witness:
- [legacy_extract.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/legacy_extract.py#L40)
- [legacy_extract.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/legacy_extract.py#L95)
- [legacy_extract.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/legacy_extract.py#L127)

Gap:
- extraction exists
- `FUEL_DIGEST`, `ROSETTA_MAP`, `OVERLAY_SAVE_DOC`, and `EXPORT_CANDIDATE_PACK` do not

### 2. `a1_cold_core_strip.py` strips proposals, but does not emit the missing artifact family

Current cold-core strip logic:
- reads memos
- filters terms
- extracts rescue targets and negative classes

Witness:
- [a1_cold_core_strip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/a1_cold_core_strip.py#L48)
- [a1_cold_core_strip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/a1_cold_core_strip.py#L68)
- [a1_cold_core_strip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/a1_cold_core_strip.py#L210)

Gap:
- cold-core filtering exists
- explicit mined fuel pack / overlay map pack / overlay save pack do not

### 3. `ingest_a2_distillery_zip.py` appends JSONL events, not structured mining/Rosetta packs

Current distillery ingest:
- reads update packets from a ZIP
- appends entries to `memory.jsonl`
- appends rosetta candidates to `a1_brain.jsonl`

Witness:
- [ingest_a2_distillery_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/ingest_a2_distillery_zip.py#L52)
- [ingest_a2_distillery_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/ingest_a2_distillery_zip.py#L67)
- [ingest_a2_distillery_zip.py](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/tools/ingest_a2_distillery_zip.py#L88)

Gap:
- ingest continuity exists
- explicit artifact-pack surfaces do not

### 4. Current artifact discipline is implied, not structurally enforced

The current spec names:
- kernel lane
- overlay lane

but the current tool layer does not yet make it structurally hard to confuse:
- mined digest
- overlay map
- candidate pack

Witness:
- [15_ROSETTA_AND_MINING_ARTIFACTS.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/15_ROSETTA_AND_MINING_ARTIFACTS.md#L18)
- [15_ROSETTA_AND_MINING_ARTIFACTS.md](/home/ratchet/Desktop/Codex%20Ratchet/system_v3/specs/15_ROSETTA_AND_MINING_ARTIFACTS.md#L53)

Gap:
- the boundary is conceptually defined
- the artifact family is underbuilt

## Exact patch targets

1. Add artifact builders:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_fuel_digest.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_rosetta_map.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_overlay_save_doc.py`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/build_export_candidate_pack.py`

2. Extend current tools:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/legacy_extract.py`
  - source extraction feed
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/a1_cold_core_strip.py`
  - kernel-lane emission feed
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/tools/ingest_a2_distillery_zip.py`
  - structured pack emission or routing

3. Add schemas:
- `FUEL_DIGEST_v1.schema.json`
- `ROSETTA_MAP_v1.schema.json`
- `OVERLAY_SAVE_DOC_v1.schema.json`
- `EXPORT_CANDIDATE_PACK_v1.schema.json`
