# Migration Handoff Spec (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Purpose
Define deterministic migration from v2/legacy spec surfaces into the v3 owner-model pack.

## Sources
- Legacy draft pack:
  - `/home/ratchet/Desktop/Codex Ratchet/system_spec_pack_v2/`
- Legacy work specs:
  - `/home/ratchet/Desktop/Codex Ratchet/work/system_specs/`
- New owner pack:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/`

## Migration Phases
1. Inventory
- list every v2/legacy doc and assign class:
  - `KEEP_REFERENCE`
  - `MERGED_INTO_V3`
  - `ARCHIVE_ONLY`

2. Mapping
- map each v2 normative statement to an owner requirement id (`RQ-*`) in v3.
- unresolved statements -> `UNKNOWN` backlog.

3. Freeze
- freeze v2 docs as reference snapshots (read-only, no in-place edits).

4. Promote
- v3 becomes active spec baseline only after conformance gates pass.

5. Archive Routing
- legacy docs remain addressable by pointer map (no deletion).

## Required Artifacts
- `migration_inventory.json`
- `migration_mapping.json`
- `migration_unknowns.json`
- `migration_promotion_report.json`

## Promotion Blockers
- any orphan requirement
- unresolved owner collision
- unresolved root constraint conflict
- unresolved bootpack-sync critical drift
