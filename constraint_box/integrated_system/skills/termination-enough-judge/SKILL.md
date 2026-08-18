---
name: termination-enough-judge
description: Stop infinite paperclip loops. Defines diminishing-return thresholds, budget ceilings, stopping criteria, and a human handoff trigger. Use after a keep, or when a loop asks to continue by default.
---

# Termination / enough judge

Enough is a gate, not a mood.

Stop when any of these hold:

- score delta is 0
- two consecutive keeps add no new protected measure
- round cap
- Goodhart/paperclip/drift refuse
- human handoff trigger is set

```text
python3 $CB_SKILLS_ROOT/termination-enough-judge/scripts/judge_enough.py \
  --state /path/loop_state.json
```
