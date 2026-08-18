---
name: invariant-constitution-checker
description: Check a proposed action against frozen non-negotiables. Local instructions cannot silently overrule them. Changing one requires an explicit amendment receipt. Use before a keep, commit, or promotion.
---

# Invariant and constitution checker

Upstream freeze: `constitution.json` in this skill directory.

```text
python3 $CB_SKILLS_ROOT/invariant-constitution-checker/scripts/check_constitution.py \
  --action '{"text":"git rebase the loop","promotion_allowed":false}'
```

Couple with `long-horizon-context-curator`. An amendment is a ledger `change_of_mind` plus an amendment receipt, never a quieter prompt.

Claim ceiling: constitution veto only.
