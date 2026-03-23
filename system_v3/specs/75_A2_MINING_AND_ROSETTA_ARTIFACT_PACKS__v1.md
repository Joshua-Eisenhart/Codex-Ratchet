# A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1
Status: DRAFT / NONCANON / REPAIR TARGET
Date: 2026-03-14
Owner: `A2` mining / `A1` Rosetta artifact recovery

## Purpose

This spec sharpens the missing artifact family that old `Thread M` carried and current `A2`/`A1` only partially preserves.

It exists because the current system already has the right architecture:
- `A2` as noncanon mining/understanding
- `A1` as proposal/cold-core distillation

but weaker explicit artifact packs for:
- mined fuel digests
- kernel-anchor overlay maps
- rebootable overlay saves
- export candidate packs

Legacy witness surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/BOOTPACKS/BOOTPACK_THREAD_M_v1.0.md`

Current normative anchors:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/15_ROSETTA_AND_MINING_ARTIFACTS.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/04_A0_COMPILER_SPEC.md`

## Core boundary rule

Kernel lane and overlay lane must remain explicitly separate.

Kernel lane:
- B-safe
- cold-core
- anchor-bound
- A0-compilable

Overlay lane:
- noncanon
- explanatory
- cross-domain
- removable without changing kernel meaning

## Required artifact packs

### 1. `FUEL_DIGEST v1`

Purpose:
- structured mined extracts from high-entropy or legacy sources

Minimum fields:
- `digest_id`
- `source_list`
- `extracted_claims[]`
- `kernel_candidate_suggestions[]`
- `overlay_mapping_suggestions[]`
- `source_pointers`

### 2. `ROSETTA_MAP v1`

Purpose:
- explicit overlay-to-kernel mapping surface

Minimum fields:
- `map_id`
- `entries[]`

Each entry must include:
- `source_term`
- `kernel_anchor`
- `anchor_type` (`TERM` or `SPEC_ID`)
- `status` (`BOUND` or `UNKNOWN`)
- `kernel_candidate` if `UNKNOWN`
- `source_pointers`

### 3. `OVERLAY_SAVE_DOC v1`

Purpose:
- rebootable noncanon overlay package for mining/Rosetta continuity

Minimum contents:
- one or more `FUEL_DIGEST`
- one or more `ROSETTA_MAP`
- provenance
- integrity hashes

### 4. `EXPORT_CANDIDATE_PACK v1`

Purpose:
- sanitized kernel-lane draft candidate pack that is safe for later A0 compilation

Minimum fields:
- `pack_id`
- `candidate_items[]`
- `required_dependencies[]`
- `negative_pressure[]`
- `source_pointers`

Forbidden contents:
- direct B commit claims
- freeform overlay jargon in B-scanned fields

## Hard rules

1. `NO_CANON_WRITES`
- these artifacts never justify canon by themselves

2. `KERNEL_ANCHOR_REQUIRED`
- overlay entries must bind to a kernel anchor or explicitly mark `UNKNOWN`

3. `NO_KERNEL_OVERLAY_CONFUSION`
- overlay labels may not stand in for admitted kernel ids/terms

4. `DETERMINISTIC_ORDER`
- artifact entries must sort deterministically by stable ids

5. `SOURCE_POINTER_REQUIRED`
- each extracted or mapped unit must carry a source pointer

## Current mapping

Expected current homes:
- `A2` mining artifacts live under noncanon `A2` surfaces
- `A1` cold-core stripping consumes mining outputs and emits proposal-safe structures
- `A0` compiles only kernel-lane candidate content into `EXPORT_BLOCK`

## Tooling targets

Current likely base tools:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/legacy_extract.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/a1_cold_core_strip.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/ingest_a2_distillery_zip.py`

Likely new tools:
- `build_fuel_digest.py`
- `build_rosetta_map.py`
- `build_overlay_save_doc.py`
- `build_export_candidate_pack.py`

## Acceptance criteria

This spec is satisfied only when:
- `A2` mining outputs have explicit artifact packs
- kernel-lane and overlay-lane outputs are impossible to confuse structurally
- `A1` and `A0` can consume the recovered artifact family without treating it as canon
