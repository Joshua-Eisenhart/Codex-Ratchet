# Attached constraint-stack audit — reconciliation

Input: `AUDIT_INPUT/CONSTRAINT_STACK_AUDIT_AND_REPAIR_20260804.md`

The attached document is a 2,079-line cold-audit history with 11 original
problem entries and 47 addenda. Its latest Addendum 47 is consistent with the
run-pack evidence produced here. In particular, it correctly narrows CBCUR-1:
the federated estate surface already has a top-level receipt and verifies 8/8;
the standalone historical `results/engine_estate_20260805` root is the one
missing that receipt. T2 in this packet independently reproduces that exact
distinction: the simple helper fails the contract, and the contract-aware
adapter reaches 7/8 while refusing to infer missing historical process exits.

## Reconciled against this packet

- The audit's 16/16, 28/28, and 15/15 CB figures match T1.
- Its Julia one-based/zero-based finding matches T5: 55/68 original period
  rows fail, and the corrected comparison yields `all_match=true`.
- Its soft-pinch observations match T4. The finer local sweep narrows the
  shared three-loop boundary to `q* = 0.71728515625 +/- 0.00048828125` and
  observes no `outer_T2` flux in 2,001 samples over q in [0,1].
- Its claim that annealing was the missing CB mechanism is now addressed by
  T6's receipt-store coarsening/refit gate and mutation canary. This is a
  receipt-integrity primitive, not a claim that MSS annealing is complete.
- Its warning not to confuse the heavyweight Julia estate with the narrow
  Julia lane is preserved in the packet's runtime report and tool matrix.

## Still open; not silently promoted by this reconciliation

The audit's upstream/root issues remain separate from the contained packet:

1. P2's container failure inventory/lock work was not rerun here.
2. The original MSTAR v2 CB-ingestion/spec-completeness path is not replaced
   merely by the contained target-surface runner. The target surface is a
   bounded CB adapter with its own source-addressed consumers.
3. Full four-lane MSTAR v2 independence still requires per-lane dependency and
   output schemas plus a blind-room/spec-only rerun; parity alone is not proof.
4. Julia remains a single-host execution in this packet; no second-host Julia
   verification was performed.
5. The audit's upstream documentation/version-authority items are provenance
   claims here, not fresh local gate results.
6. The three known CB gate defects and any live-repo status labels remain
   blocked unless their dedicated gates are run in the active checkout.

The architecture recommendations in Addendum 47 are accepted as design
direction only: an engine-shaped scheduler with a neutral evidence kernel,
typed engine-step packets, shadow mode before authority, per-capability
leases, plan-only CR, and projector-first Holodeck. The contained package has
the typed packet and packet-aware diagnostic consumers, but this packet does
not claim that the full scheduler/lease architecture is canonical.

Claim ceiling for this reconciliation: `exists` for the audit input and
`passes local rerun` for the explicitly linked T1–T6 artifacts. No registry
status, canon, admission, MSS, CR truth, or release status changed.
