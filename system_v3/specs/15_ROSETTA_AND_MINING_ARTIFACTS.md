# Rosetta + Mining Artifacts (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Companion repair target:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/75_A2_MINING_AND_ROSETTA_ARTIFACT_PACKS__v1.md`

## Purpose
Make the “A2 miner / A1 rosetta” core function explicit as concrete artifact shapes, with hard boundary rules.

## Authority Sources
- Megaboot topology + boundary:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md:14`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md:22`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md:121`
- Megaboot rosetta formats:
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md:155`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md:178`
  - `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a2 hand assembled docs/uploads/MEGABOOT_RATCHET_SUITE_v7.4.9-PROJECTS 2.md:198`

## Core Boundary Rule
- Kernel lane artifacts are B-safe and may be compiled into `EXPORT_BLOCK`.
- Overlay lane artifacts are noncanon and must not leak into B-scanned fields.

## A2 Mining (intended)
A2 mining produces structured fuel from:
- high-entropy docs
- old threads/transcripts
- run artifacts + failures

Mining outputs are not canon and do not justify canon.

## A1 Rosetta (intended)
A1 rosetta:
- rewrites overlay/jargon into kernel-safe candidate terms/spec ids
- preserves mapping metadata for traceability
- emits only strategy objects (compiled by A0), not B containers

## A1 Rosetta: Two-Phase Contract
Rosetta is explicitly two-phase:

1) **Cold-core extraction (kernel lane)**:
- strip a source-field model/idea down to explicit math objects/relations
- express candidates in the kernel vocabulary (terms must be ratcheted; no smuggled primitives)
- emit candidates + dependencies + alternatives + sim plans inside `A1_STRATEGY_v1`

2) **Reattachment dictionaries (overlay lane)**:
- after kernel admission + evidence, attach field-specific dictionaries back onto the admitted kernel ids
- multiple overlay dictionaries may map different dialects onto the same kernel term/spec
- overlays are for human readability and cross-field alignment; they never justify canon

Analogy: the Rosetta Stone enabled Egyptian translation by aligning multiple inscriptions of the same content.
Here, the admitted kernel object is the “stone”, and each overlay dictionary is another “language line”
pointing at the same kernel referent (like an airport sign with multiple languages saying the same thing).

## Artifact Shapes (noncanon)
These are companion artifacts for audit/replay; they are not B input unless compiled into `EXPORT_BLOCK`.

The current companion repair spec sharpens these shapes into executable recovery targets rather than leaving them as light suggested forms.

### ROSETTA_MAP v1
- overlay mapping anchored to kernel ids/terms
- cannot justify canon; annotation only

### ROSETTA_DICTIONARY_SET v1 (overlay; suggested)
Purpose: carry multiple “dialect → kernel” dictionaries without leaking into B.

Suggested fields:
- `dictionary_id` (e.g., `DIALECT_PHYSICS_QIT`, `DIALECT_PERSONALITY_IGT`)
- `entries[]` where each entry includes:
  - `source_term` (overlay token)
  - `kernel_term` (ratcheted term literal) OR `kernel_spec_id` (admitted spec id)
  - `notes` (overlay-only)

### FUEL_DIGEST v1
- structured extracts from sources with kernel suggestions + rosetta suggestions

### EXPORT_CANDIDATE_PACK v1
- sanitized B-safe draft candidates, plus notes kept outside Thread B

## v3 Mapping
- A2 mining artifacts live as noncanon under A2 surfaces (`RQ-070..RQ-078`).
- A1 rosetta mappings are carried inside `A1_STRATEGY_v1` as structured mapping entries (`RQ-040..RQ-049`).
- A0 compiles kernel-lane candidates into `EXPORT_BLOCK` only (`RQ-030..RQ-039`).
