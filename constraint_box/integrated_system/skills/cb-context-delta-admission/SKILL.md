---
name: cb-context-delta-admission
description: Admit new context only after classifying it as observation, inference, proposal, contradiction, rejection, owner amendment, or earned state. A recent summary cannot outrank an older primary source.
---

# CB context delta admission

```text
python3 $CB_SKILLS_ROOT/cb-context-delta-admission/scripts/admit_delta.py \
  --delta '{"class":"proposal","text":"...","outranks_primary":true}'
```

`proposal` and `inference` are never earned state. `owner_amendment` needs an amendment receipt.
