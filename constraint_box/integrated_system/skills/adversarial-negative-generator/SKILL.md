---
name: adversarial-negative-generator
description: Generate cheap deterministic negative twins so positive-only testing cannot hide paperclip behaviour. Covers reward hacks, shortcut features, metric gaming, reversed objectives, and degenerate completions.
---

# Adversarial negative generator

Positive tests are not a family. A family needs refuse twins.

```text
python3 ~/.codex/skills/adversarial-negative-generator/scripts/generate_negatives.py \
  --target /path/target.json
```

Twins: `reward_hack`, `shortcut`, `metric_gaming`, `reversed_objective`, `degenerate`.
Couples to `cb-counterexample-wave` and Light dualsolve. This skill proposes twins. Code decides.
