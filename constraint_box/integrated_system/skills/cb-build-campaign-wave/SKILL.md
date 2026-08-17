---
name: cb-build-campaign-wave
description: Loop the independent ConstraintBox failure, repair, and strategy waves as a receipt-bound campaign while preserving project context and contradictions.
---

# CB Build Campaign Wave

This is a skill of wave skills. It does not inline or replace its children.

1. Invoke `cb-maintenance-wave` as the first and independent step. Bind one live-source digest and one append-only context snapshot, and require a self-validating `READY` maintenance receipt with `mutation_performed: false` and `writes_allowed: false`.
2. Run `cb-context-wave` to seal an epoch and project distinct per-lane packets. This prepares Decision. It is not a truth council.
3. Run `cb-strategy-framing-wave` before Decision or implementation.
4. Run `cb-failure-wave` and `cb-objective-integrity-wave` as Failure attacks.
5. If failures are finite and repairable, run `cb-repair-wave`; otherwise retain the failed candidate and stop.
6. Run `cb-strategy-checkpoint-wave` after repair. Continue only on `CONTINUE_CANDIDATE`.
7. Compile the human surface with `cb-output-compiler`. Missing evidence stays visible.
8. `cb-wave-watchdog` monitors the spine. It has no content vote.

The old combined `cb-strategy-wave` remains in the library. This campaign no longer calls it.

No council may fill in a missing child, reinterpret cancellation as success, or write directly to live source. A human or a separately authorized deterministic promotion gate remains required.
