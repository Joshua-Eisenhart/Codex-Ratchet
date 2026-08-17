---
name: stakeholder-externality-mapper
description: Name who benefits and who pays. Prevents paperclip optimization by omission. Use when a keep helps one visible score and dumps cost onto maintainers, future users, or the evidence base.
---

# Stakeholder / externality mapper

Required lists: `beneficiaries`, `bearers`, `absent`.

```text
python3 ~/.codex/skills/stakeholder-externality-mapper/scripts/map_externalities.py \
  --map /path/map.json
```

If `absent` is empty, HOLD. If a bearer is the evidence base or a future user and no mitigation is named, REFUSE_OMISSION.
