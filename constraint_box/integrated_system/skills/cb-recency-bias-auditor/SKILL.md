---
name: cb-recency-bias-auditor
description: Compare the current projection with an earlier baseline and with the latest delta removed. If the strategy flips, require a causal explanation tied to new evidence. Use before treating a new summary as the reason a decision changed.
---

# CB recency-bias auditor

```text
python3 $CB_SKILLS_ROOT/cb-recency-bias-auditor/scripts/audit_recency.py \
  --current decision.json --ablated decision.json
```
