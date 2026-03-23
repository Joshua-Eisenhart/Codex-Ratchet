# FULL_PLUS_SEMANTIC_SAVE_ZIP__v1
Status: DRAFT / NONCANON / REPAIR TARGET
Date: 2026-03-14
Owner: `A0` save/restore tooling

## Purpose

This spec restores the old semantic Thread B save bundle as a first-class ZIP carrier.

It exists because the current system still defines:
- `MIN`
- `FULL+`
- `FULL++`

but the live tool surface has drifted toward broad repo/system exports instead of the older semantic restore bundle.

Legacy witness surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/core_docs/a1_refined_Ratchet Fuel/THREAD_S_FULL_SAVE/README.md`

Current normative anchors:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/16_ZIP_SAVE_AND_TAPES_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/08_PIPELINE_AND_STATE_FLOW_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/17_BOOTPACK_THREAD_B_v3.9.13_ENFORCEABLE_CONTRACT_EXTRACT_FOR_IMPLEMENTATION_v1.md`

Normative anchors:
- `RQ-090`
- `RQ-091`
- `RQ-092`
- `RQ-093`
- `RQ-094`
- `RQ-095`

## Core rule

`FULL+` is a semantic restore carrier, not a generic repo image.

It must contain the exact semantic Thread B restore surfaces required to:
- archive
- replay
- inspect
- restore B-facing canon state

without requiring a full workspace export.

## Required `FULL+` ZIP members

Every `FULL+` semantic save ZIP must contain:

1. `THREAD_S_SAVE_SNAPSHOT_v2.txt`
- canonical snapshot container

2. `DUMP_LEDGER_BODIES.txt`
- full survivor ledger bodies
- full park set bodies if non-empty

3. `DUMP_TERMS.txt`
- full term registry enumeration

4. `DUMP_INDEX.txt`
- deterministic index and counts

5. `REPORT_POLICY_STATE.txt`
- policy flags / state switches relevant to restore or replay

6. `PROVENANCE.txt`
- counters / save provenance / generator note

7. `SHA256SUMS.txt`
- integrity hashes for every member

Optional but permitted in `FULL+`:
- one manifest file naming the profile and member hashes
- one restore-audit report

Forbidden in `FULL+`:
- broad unrelated repo/system payloads
- non-restore overlays
- A2 mining notes as required fuel
- Rosetta overlays as required fuel
- arbitrary generated run clutter

## Required semantic coverage

The `FULL+` bundle must preserve these semantic restore surfaces:
- replayable snapshot
- full item bodies
- full term enumeration
- deterministic index/count witness
- policy-state witness
- provenance witness
- integrity witness

If any of the seven required semantic surfaces are missing, the bundle is not `FULL+`.

## `FULL++` extension

`FULL++` is:
- `FULL+`
- plus `CAMPAIGN_TAPE`
- plus optional `EXPORT_TAPE`
- plus optional Rosetta/mining overlays
- plus optional replay/audit aids

`FULL++` may include:
- `CAMPAIGN_TAPE`
- `EXPORT_TAPE`
- `ROSETTA_MAP`
- `OVERLAY_SAVE_DOC`
- mining/output witness packs

`FULL++` is never required by B restore.

## ZIP shape

Suggested internal layout:

- `restore/THREAD_S_SAVE_SNAPSHOT_v2.txt`
- `restore/DUMP_LEDGER_BODIES.txt`
- `restore/DUMP_TERMS.txt`
- `restore/DUMP_INDEX.txt`
- `restore/REPORT_POLICY_STATE.txt`
- `restore/PROVENANCE.txt`
- `restore/SHA256SUMS.txt`
- `meta/FULL_PLUS_SAVE_MANIFEST_v1.json`

For `FULL++`, add:
- `tapes/campaign_tape.000.jsonl`
- `tapes/export_tape.000.jsonl`
- `overlay/...`

The old flat member naming is still valid as a legacy witness shape.

## Manifest

Every semantic save ZIP should contain:

`FULL_PLUS_SAVE_MANIFEST_v1.json`

Minimum fields:
- `schema`
- `save_level`
- `bundle_id`
- `created_utc`
- `boot_id`
- `member_list`
- `member_sha256`

Allowed `save_level` values:
- `MIN`
- `FULL+`
- `FULL++`

## Build law

1. `NO_GUESSING`
- builder must not guess missing restore surfaces

2. `FAIL_CLOSED_ON_MISSING_MEMBER`
- if a required `FULL+` member is missing, do not silently downgrade inside a claimed `FULL+` ZIP

3. `SEMANTIC_OVER_GENERIC`
- a generic repo/system export ZIP is not a substitute for `FULL+`

4. `ASCII_AND_DETERMINISM`
- text payloads must respect current ZIP determinism rules

5. `HASH_WITNESS_REQUIRED`
- the ZIP must include member-level integrity hashes

## Audit law

Every semantic save ZIP should be auditable by a dedicated tool that returns:
- `PASS`
- `FAIL`

Audit checks:
- required members present
- snapshot container valid
- required members hashed
- save-level consistent with members present
- forbidden broad-payload contamination absent

## Relationship to current generic save ZIPs

Generic save/profile ZIPs remain useful for:
- broad archive export
- system image handoff
- debug capture

They do not satisfy `FULL+` unless they explicitly implement this semantic member set.

## Acceptance criteria

This spec is satisfied only when:
- a tool can build a semantic `FULL+` ZIP directly
- a tool can audit that ZIP directly
- `FULL+` and generic repo export are no longer conflated

## Current patch targets

Primary tool to retain as generic exporter:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_save_profile_zip.py`

Primary new tools to add:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/build_full_plus_save_zip.py`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/tools/audit_full_plus_save_zip.py`
