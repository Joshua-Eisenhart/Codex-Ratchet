---
name: counterfactual-impact-evaluator
description: Ask whether the actual object improved under a held-out measure, not whether the agent's internal score or artifact improved. Prevents task-completed theater.
---

# Counterfactual impact evaluator

Internal score is not the world.

Held-out CB measures: seed still ADMIT, control packet still BOUNDED_SAT, valid_v1 did not fall, promotion_allowed still false.

```text
python3 ~/.codex/skills/counterfactual-impact-evaluator/scripts/evaluate_impact.py \
  --before score.json --after score.json
```

If the proxy rose and a held-out measure fell, REFUSE_THEATER.
