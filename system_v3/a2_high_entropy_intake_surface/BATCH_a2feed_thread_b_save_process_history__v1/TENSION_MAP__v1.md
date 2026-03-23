# TENSION_MAP__v1
Status: PROPOSED / NONCANONICAL / CONTRADICTION-PRESERVING
Batch: `BATCH_a2feed_thread_b_save_process_history__v1`
Extraction mode: `PROCESS_HISTORY_PASS`

## T1) Fail-closed Thread B grammar vs malformed container residue inside the save
- source markers:
  - source 1: `1-41`
  - source 1: `528-530`
  - source 1: `913-953`
- tension:
  - the embedded bootpack says admissible interaction must be exact command, export, snapshot, or sim-evidence containers
  - the save itself preserves bare `SIM_EVIDENCE`, bare `END SIM_EVIDENCE`, and a malformed `END EXPORT_BLOCK`
- preserved read:
  - the stitched session artifact does not fully obey the kernel grammar it embeds

## T2) `SOLE_SOURCE_OF_TRUTH` rhetoric vs materially distributed continuity
- source markers:
  - source 1: `1-4`
  - source 1: `350-497`
  - source 1: `4653-4891`
  - source 1: `9986-10037`
- tension:
  - the bootpack claims sole-source authority
  - actual continuity is spread across bootpack copies, saved snapshots, reports, export blocks, and evidence blocks
- preserved read:
  - authority is centralized rhetorically, but operational continuity is artifact-distributed

## T3) No-drift kernel aspiration vs long accretive export/evidence session sprawl
- source markers:
  - source 1: `42-79`
  - source 1: `498-10149`
- tension:
  - the kernel insists on narrow replayable context and no drift
  - the save grows into a 10k-line stitched history with repeated re-entry, duplicate seeding, and family sprawl
- preserved read:
  - the file records real process accumulation, not a perfectly closed no-drift trace

## T4) Uppercase command discipline vs lowercase requests and transcript residue
- source markers:
  - source 1: `272-302`
  - source 1: `4299-4307`
  - source 1: `8914-10149`
- tension:
  - the embedded grammar only allows strict `REQUEST ...` command lines
  - the save includes lowercase `request` lines, doubled spacing, stray `ok`, and UI residue text
- preserved read:
  - session-save artifacts can pick up noncanonical operator residue even when the kernel surface is formal

## T5) Zeroed seed counters vs later accumulated state checkpoints
- source markers:
  - source 1: `346-347`
  - source 1: `494-495`
  - source 1: `4649-4650`
  - source 1: `4888-4889`
  - source 1: `10020-10021`
- tension:
  - embedded bootpacks repeatedly reset `ACCEPTED_BATCH_COUNT` and `UNCHANGED_LEDGER_STREAK` to zero
  - actual saved and reported state shows the session has already grown through `36`, `157`, and `246` accepted batches
- preserved read:
  - the save preserves both pristine seed state and later accumulated state without resolving them into one layer

## T6) Repeated save/report requests vs absence of a later emitted closing snapshot
- source markers:
  - source 1: `8429-10149`
  - source 1: `10144-10149`
- tension:
  - the late file repeatedly requests `REPORT_STATE` and `SAVE_SNAPSHOT`
  - the artifact ends without a final closing snapshot after the last request sequence
- preserved read:
  - the save history is incomplete as a final replay artifact even while it is rich as process evidence

## T7) Simulation execution unavailability and input rejection vs evidence-driven activation
- source markers:
  - source 1: `498-953`
  - source 1: `5142-10149`
- tension:
  - early evidence shows rejected inputs and execution-unavailable states
  - the broader file still depends on sim evidence for state advancement, activation, and later invariant packaging
- preserved read:
  - the file preserves both fragile evidence transport and heavy evidence dependence

## T8) Nonsemantic admissibility ledgers vs late history-reuse object packaging
- source markers:
  - source 1: `8914-9311`
  - source 1: `9312-10149`
- tension:
  - the admissibility ledgers insist they admit structure only and introduce no semantics
  - the later history-reuse family rapidly packages record/operator distinctions, invariants, and functional consequences
- preserved read:
  - the late branch tries to stay structural while also moving toward more interpretable reusable object families
