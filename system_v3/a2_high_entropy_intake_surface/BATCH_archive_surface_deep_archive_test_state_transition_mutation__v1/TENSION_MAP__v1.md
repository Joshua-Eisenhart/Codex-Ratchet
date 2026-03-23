# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / BOUNDED INTAKE ARTIFACT
Batch: `BATCH_archive_surface_deep_archive_test_state_transition_mutation__v1`
Date: 2026-03-09

## Tension 1: Final Summary Hash Versus Only Event Endpoint
- source anchors:
  - `summary.json`
  - `state.json.sha256`
  - `events.jsonl`
- bounded contradiction:
  - summary and sidecar bind to `63995c34...`, while the sole executed event ends on `fcb5d2fe...`
- intake handling:
  - preserve summary/state sidecar as the stronger final snapshot while keeping the event-lattice endpoint visibly distinct

## Tension 2: Snapshot Pending Evidence Versus Empty Final `evidence_pending`
- source anchors:
  - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
- bounded contradiction:
  - the Thread-S snapshot lists both retained specs under `EVIDENCE_PENDING`, while final state keeps `evidence_pending` empty
- intake handling:
  - preserve the snapshot/state normalization split as historical residue rather than reconciling it away

## Tension 3: Export/Snapshot `KILL_IF` Lines Versus Empty Final `kill_log`
- source anchors:
  - `000001_A0_TO_B_EXPORT_BATCH_ZIP.zip`
  - `000001_B_TO_A0_STATE_UPDATE_ZIP.zip`
  - `state.json`
  - retained SIM evidence files
- bounded contradiction:
  - export and snapshot preserve `KILL_IF ... NEG_NEG_BOUNDARY` lines for both specs, final state keeps `kill_log` empty, and retained SIM evidence files do not carry explicit kill-signal lines
- intake handling:
  - preserve pre-SIM kill-condition residue without forcing it into final kill bookkeeping

## Tension 4: Zero Packet Parks Versus Two `PARKED` Promotion States
- source anchors:
  - `summary.json`
  - `soak_report.md`
  - `state.json`
- bounded contradiction:
  - summary and soak report zero parked packets, while final state marks both sim promotion outcomes as `PARKED` and keeps two unresolved blockers
- intake handling:
  - preserve the distinction between packet transport cleanliness and semantic promotion closure

## Tension 5: Exact Duplicate ` 2` File Family Versus Single Runtime Branch
- source anchors:
  - all primary run-core files
  - all suffixed ` 2` duplicates
- bounded contradiction:
  - the root keeps two top-level file families, but the suffixed family is byte-identical to the primary one
- intake handling:
  - preserve the duplicate family as packaging residue rather than as evidence of a second branch

## Tension 6: Event Schema, Path Drift, And Empty Directory Shells
- source anchors:
  - `events.jsonl`
  - archive-local `zip_packets/`
  - empty residue directories
- bounded contradiction:
  - executed rows omit explicit `event` keys, use variant counter field names, still point packet paths at `system_v3/runtime/...`, and the root keeps empty suffixed directories that suggest lanes which never retained content
- intake handling:
  - preserve the runtime-emitted event shape, path leakage, and empty directory shells rather than rewriting them into a normalized archive-local form
