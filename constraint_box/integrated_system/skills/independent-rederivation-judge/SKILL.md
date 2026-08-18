---
name: independent-rederivation-judge
description: Require different tools or implementations to reproduce a key check. Agreement by several LLMs never counts as verification. Use before treating dualsolve, tests, or a loop keep as reproduced.
---

# Independent re-derivation judge

Allowed independent deciders in Light: `z3`, `cvc5`, `enumeration`, and a fresh pytest replay.

```text
python3 $CB_SKILLS_ROOT/independent-rederivation-judge/scripts/judge_rederivation.py \
  --receipt /path/receipt.json
```

If `verifiers` is only model names, REFUSE_LAUNDERED_CONSENSUS.
If fewer than two distinct tool families agreed, HOLD_NOT_REPLAYED.
Couples to `distinguishability-smt` and dualsolve.
