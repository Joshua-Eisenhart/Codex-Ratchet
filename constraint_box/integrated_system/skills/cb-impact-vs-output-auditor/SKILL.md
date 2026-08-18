---
name: cb-impact-vs-output-auditor
description: Distinguish producing an artifact, passing a local metric, and changing the intended external condition.
---

# Impact versus output auditor

This leaf audits a claim against the evidence named in one JSON request. The
schema is `constraintbox.impact-vs-output.v1`; the exact operation is
`cb-impact-vs-output-auditor.v1` and `target` must be one
canonical non-empty string. `target_id` and operation aliases are refused.
`claim` and every evidence item must be non-empty members of the exact enum
`artifact`, `metric`, `external_condition`; evidence must be non-empty and
unique.

Claiming `external_condition` without corresponding external evidence is
`REFUSE_OUTPUT_AS_IMPACT`; an artifact or metric is not world impact. Evidence
must exactly match the claimed class; cross-class evidence promotion refuses.
The receipt is proposal/audit-only and cannot promote a claim or change an
external condition.

Run from the repository root:

```text
python3 constraint_box/integrated_system/skills/cb-impact-vs-output-auditor/scripts/classify.py \
  --payload '{"schema":"constraintbox.impact-vs-output.v1","operation":"cb-impact-vs-output-auditor.v1","target":"claim-1","claim":"external_condition","evidence":["artifact","metric"]}'
```

Every result echoes target and operation identity, self-binds its digest, sets
`promotion_allowed` false, and reports `writes_performed` false.
Malformed/authority-shaped requests, identity mismatches, cancellation, and
tampered receipts fail closed.
