---
name: specification-boundary
description: Separate authorized objective, non-objectives, forbidden actions, irreversible actions, and claims the system is not licensed to make. Use to stop scope creep and claim-ceiling inflation.
---

# Specification boundary / claim ceiling

Couples to `evidence-sufficiency`. This skill names the fence. That skill checks worn vs legal ceiling.

```text
python3 $CB_SKILLS_ROOT/specification-boundary/scripts/check_boundary.py \
  --spec /path/spec.json
```

Required keys: `objective`, `non_objectives`, `forbidden`, `irreversible`, `unlicensed_claims`.
A proposed action that matches forbidden or unlicensed refuses.
