---
name: failure-memory-resurrection-checker
description: Bind rejected approaches and why they failed. Refuse a later proposal that resurrects a demoted branch without new evidence. Use when a self-loop, repair, or latest prompt forgets a prior kill.
---

# Failure memory and resurrection checker

Negative results are not cleanup. They are binding.

Store:

- rejected approach id
- why it failed
- severance witness / receipt digest
- demotion cause
- re-entry condition

A later proposal that matches a stored failure without a new evidence digest is `REFUSE_RESURRECTION`.

Couple with `long-horizon-context-curator`. The ledger holds genealogy. This skill holds the graveyard.

```text
python3 ~/.codex/skills/failure-memory-resurrection-checker/scripts/check_resurrection.py \
  --memory receipts/failure_memory/failures.jsonl \
  --proposal '{"approach_id":"pick-winner","text":"..."}'
```

Claim ceiling: resurrection veto only. Not a new verdict on the old failure.
