---
name: cb-failure-wave
description: Use when running the nested ConstraintBox failure council as an independent skill that orders and loops the premortem, counterexample, and authority-collapse wave skills.
---

# CB Failure Wave

This is a skill of wave skills. It does not replace or inline its children.

1. Validate this `wave.json` and all three child manifests.
2. Bind one target digest for the round.
3. Use `mmm-preload` for the root wave agent. Do not load a main MMM.
4. Run `cb-premortem-wave`, `cb-counterexample-wave`, and `cb-authority-collapse-wave` independently. Each child must produce its own complete or partial receipt.
5. Exchange anonymized child findings only after all three divergent runs terminate.
6. Preserve contradictions, select only authorized finite repairs, and rerun all three child wave skills against the repaired target.
7. Repeat through the main loop cap.
8. Compile the parent receipt from child receipts and deterministic evidence. Never infer missing execution from prose.

The parent is `PARTIAL` if any required child is missing or receipt-invalid. Cancellation remains cancellation. Reaching the cap retains unresolved failures. A completed failure wave may conclude that the target failed.

Runtime assignments are supplied by the invocation contract and recorded in call receipts; they are not embedded here.
