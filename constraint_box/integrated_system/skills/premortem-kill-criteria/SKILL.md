---
name: premortem-kill-criteria
description: Require explicit failure modes, observable tripwires, and stop or demote conditions before work starts. Prevents optimizing a plan after its assumptions have failed. Couples to cb-premortem-wave.
---

# Premortem and kill criteria

Do not start a loop without tripwires.

Required fields: `failure_modes`, `tripwires`, `stop_or_demote`.

```text
python3 $CB_SKILLS_ROOT/premortem-kill-criteria/scripts/check_kill_criteria.py \
  --plan /path/plan.json
```

A missing tripwire is HOLD. A tripwire that has already fired is REFUSE_DEAD_PLAN.
Couples to `cb-premortem-wave`. This skill is the gate; that wave is the council.
