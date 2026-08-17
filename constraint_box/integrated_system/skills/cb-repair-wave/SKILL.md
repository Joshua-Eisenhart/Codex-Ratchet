---
name: cb-repair-wave
description: Run an independently callable ConstraintBox repair council against one digest-bound failed target, using bounded candidate mutations, deterministic tests, and exact reruns.
---

# CB Repair Wave

This wave consumes a valid failure-wave receipt and an isolated copy of the exact failed target. It never edits the live target directly.

1. Validate `wave.json`, the failure receipt, target digest, and context-snapshot digest.
2. Use `mmm-preload` for every model-backed member. Load mini voice combinations only; runtime model assignments remain invocation data.
3. Run three independent members: minimal repair, alternative repair, and adversarial verifier.
4. Preserve every proposal. Deterministically select at most one mutation whose write set, score, test, and falsifier are explicit.
5. Apply that mutation only to the isolated candidate. Run its positive and negative tests.
6. Keep the mutation only when the score improves and every hard gate remains green; otherwise discard it without rationalizing.
7. Rerun the exact failure children against the new candidate digest.
8. Emit kept/discarded mutation receipts and the candidate digest. Never promote it to live source.

Missing failure evidence, an expanded write set, cancellation, or an unverifiable test makes the wave `PARTIAL` or `REFUSED`, never a smaller success.
