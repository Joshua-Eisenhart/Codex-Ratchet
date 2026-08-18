---
name: cb-branch-failure-memory
description: Preserve failed candidates, killed assumptions, counterexamples, parked branches, unresolved discriminators, and exact resurrection conditions. A rejected proposal may return only with a named new bridge or new evidence.
---

# CB branch-failure memory

Append-only. Recency never deletes a killed branch.

```text
python3 $CB_SKILLS_ROOT/cb-branch-failure-memory/scripts/remember.py \
  --memory receipts/branch_failure/memory.jsonl \
  --remember '{"kind":"failed_candidate","id":"pick-winner","why":"vote is not a verifier"}'
```
