# SELECTION_RATIONALE__v1
Status: PROPOSED / NONCANONICAL / A2-MID SELECTION RATIONALE
Batch: `BATCH_A2MID_archive_signal_lane_closure_audit__v1`
Extraction mode: `A2_MID_REFINEMENT_PASS`
Date: 2026-03-09

## Why this audit batch exists
- the deep-archive `RUN_SIGNAL` lane has now been directly re-entered across:
  - raw `0002`
  - raw `0003`
  - raw `0004`
  - raw `0005`
  - `0005_bundle`
- the current task is therefore not another signal-family reduction
- it is a closure-aware residual audit that decides which deep-archive run or test family now has the strongest bounded next-step value

## Why the completed signal children are the right anchors
- they cover the current signal lane from:
  - fail-closed promotion burden
  - negative residue inflation
  - summary versus replay divergence
  - repaired runtime alignment and `SIGNAL_AUDIT` nullability
  - bundle-side controller and packet identity seams
- together they prove the lane is no longer missing a first bounded A2-mid child

## Why the signal lane is not the next best target anymore
- no additional unresolved raw `RUN_SIGNAL` parent remains in the current live ledger after:
  - `0002`
  - `0003`
  - `0004`
  - `0005`
  - `0005_bundle`
- reopening that lane by default would duplicate already stronger local closure coverage

## Why `TEST_A1_PACKET_ZIP` outranks `TEST_A1_PACKET_EMPTY`
- `TEST_A1_PACKET_EMPTY` already has a direct A2-mid child:
  - `BATCH_A2MID_archive_test_packet_empty_handoff_fences__v1`
- `TEST_A1_PACKET_ZIP` remains unchilded while preserving the closely related packet-handoff family
- `TEST_A1_PACKET_ZIP` also carries a denser contradiction packet than the empty sibling:
  - zero-accept summary collapse
  - two-step canonical ledger residue
  - zeroed sequence counters despite a visible packet lattice
  - same-name strategy packet copies with different bytes and different validity

## Why `TEST_A1_PACKET_ZIP` is the next real unresolved family
- it is compact
- it is still unchilded
- it already has a nearby sibling reduction for comparison
- its contradiction packet is local and reusable:
  - summary and soak say zero accepted work while state and events retain accepted history
  - state canonical ledger preserves two steps inside a nominally one-step run
  - `sequence_state.json` zeros lanes that are visibly populated in the run root
  - the same named `000001_A1_TO_A0_STRATEGY_ZIP.zip` splits into incompatible retained copies by location

## Why `TEST_REAL_A1_002` and the state-transition family are not the next best targets
- they still matter, but they are currently less bounded than the packet-zip sibling seam
- `TEST_REAL_A1_002` has a useful sibling child in `REAL_A1_001`, but its replay and hash-layer contradictions are broader than the tighter packet-identity seam in `TEST_A1_PACKET_ZIP`
- the state-transition family remains useful, but it has no direct childed sibling anchor yet and would reopen a broader chain-oriented lane sooner than needed

## Best next existing intake target
- `BATCH_archive_surface_deep_archive_test_a1_packet_zip__v1`
