---
name: reversibility-option-value-gate
description: Prefer bounded reversible probes. Escalate irreversible actions only after evidence receipts. Use before delete, push, promote, or any one-way keep.
---

# Reversibility and option-value gate

```text
python3 ~/.codex/skills/reversibility-option-value-gate/scripts/check_reversibility.py \
  --action '{"irreversible":true,"evidence_receipt":null}'
```

Irreversible without an evidence receipt is REFUSE_IRREVERSIBLE.
