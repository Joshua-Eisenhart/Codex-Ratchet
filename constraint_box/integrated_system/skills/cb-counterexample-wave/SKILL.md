---
name: cb-counterexample-wave
description: Use when independently running a ConstraintBox counterexample wave over one target using boundary, order-reversal, and ablation cells with deterministic replay.
---

# CB Counterexample Wave

Validate `wave.json` and bind one target digest. Run all `cb-counterexample-cell` children independently, each with a distinct mini-MMM combination. Preserve splits, destroyed regions, holds, and unmapped cases.

Converge only by comparing exact observation records. Propose finite target repairs, then rerun the identical mutations and ablations. Emit one receipt retaining every child, disagreement, repair, and delta. Completion can prove the target failed.
