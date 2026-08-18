---
name: cb-strategy-discriminator-wave
description: Compare a digest-bound candidate stage order with the current cumulative-wave profile order and return a non-authoritative changed or held frontier.
---

# CB strategy-discriminator wave

This directory is an inactive `NEW_CANDIDATE`.  The runner is a deterministic
parent over three distinct operations of the approved
`cb-strategy-discriminator-cell` leaf:

1. `bind_survivors` binds the candidate-order and live-profile-order readings;
2. `name_exact_disagreement` names the first exact array disagreement; and
3. `design_finite_observable` designs the finite array/prefix comparison.

The leaf's internal operation remains
`cb-strategy-discriminator-cell.v1`.  Each parent operation has its own
`child_operation_id` and receipt.  The parent verifies both identities and
never treats the leaf's finite-probe selection as an order decision.

## Input and run

`scripts/run_wave.py` accepts one strict
`constraintbox.strategy-discriminator-wave-input.v1` packet.  The packet binds
the target bytes and digest, candidate order and digest, expected live order
and digest, profile, current configuration path and digest, retained
cumulative receipt, exact retained run id and digest, context epoch and
digest, branch frontier and digest, the caller's expected source-set digest,
and exactly one input wrapper for each of the three parent operations.
The current `CUMULATIVE_WAVE_SEQUENCE.json` bytes are read and hashed at run
time; a profile-order mismatch against the packet is a refusal, not an
inferred repair.  The packet cannot choose the authority artifact: immutable
bindings in `wave.json` pin the durable retained cumulative receipt, current
epoch pointer/epoch, run ID, receipt/epoch hashes, and frontier IDs.  A
candidate-contained copy is used only when the durable live path is absent in
an isolated fixture root.  The frontier entries are fixed in the order
`candidate_order`, `live_scheduler_order` and carry the corresponding order
digests.  Live epoch currentness is checked through the contained epoch sealer;
fixture epochs use exact pinned pointer/epoch bytes and canonical self-hashes.

```text
python3 constraint_box/integrated_system/skills/cb-strategy-discriminator-wave/scripts/run_wave.py \
  --packet /path/to/strategy-discriminator.packet.json \
  --root /path/to/worktree \
  --out /path/to/receipt.json
```

The command writes only an explicitly requested receipt.  `--verify` checks a
receipt against the packet and the current source/config bindings;
`replay_receipt` performs the same read-only exact rerun.

## Result boundary

For a valid packet the terminal disposition is exactly one of:

- `MATCH_OBSERVED` — the candidate and live profile arrays are identical;
- `HOLD_ORDER_MISMATCH` — exact arrays, digests, first difference, common
  prefix, and prefix-lock evidence are retained without changing either
  array.

The result is a branch-frontier projection only.  It contains no winner,
reorder, activation, or promotion operation.  Definition/admission controls,
source/config/receipt custody, child-set custody, path confinement,
cancellation, tamper checks, and replay are deterministic.  `selection_count`
or any other count from a retained receipt is explicitly outside order
admission.  The retained cumulative receipt is independently self-hash
checked, profile/run/status checked, and required to show prefix 3 locked at
`cb-premortem-wave` with no later stage executed.  Negative controls invoke
the real parent validators and approved leaf with mutated inputs, verify their
refusal receipts, and retain each control digest.  Every child boundary and
the prewrite boundary re-attest target, config, retained receipt, epoch,
frontier, parent sources, and leaf sources; a refusal retains the completed
child prefix.

`route_truth=NOT_FULL` and `route_truth_label=NOT_FULL/model_free` are fixed.
Provider dispatch and MMM preload are not applicable, not proved, and never
called by this candidate.

## Claim ceiling

Digest-bound comparison of one supplied candidate stage list against one live
profile order, with a non-authoritative frontier receipt only.  This does not
measure a strategy, select a winner, reorder stages, execute a scheduler,
activate a wave, prove provider/MMM delivery, or promote any result.
