---
name: cb-goal-amendment-guard
description: Only an explicit owner amendment may alter the object, success condition, or hard constraints. A model-discovered better objective remains a proposal.
---

# Goal amendment guard

This leaf audits a proposed change; it never changes the owner object. The
request must use schema `constraintbox.goal-amendment.v1`, the exact operation
`cb-goal-amendment-guard.v1`, and one canonical non-empty string `target`.
`target_id` and operation aliases are refused. All of
`object_changed`,
`success_condition_changed`, or `hard_constraints_changed` to a boolean.

Changed goals require an externally supplied `owner_amendment_receipt` object
with exact owner/source/target/operation binding and exactly one non-empty
`signature` or digest matching the receipt body, plus an out-of-band expected
SHA supplied via `--owner-receipt-sha256` (or the
`trusted_owner_receipt_sha256` API argument). Optional out-of-band owner/source
value is the canonical SHA-256 of the complete owner-receipt JSON; optional
out-of-band owner/source values are compared exactly. A self-declared `owner`, arbitrary signature, or
`authorized: true` is not proof. A discovered better objective without that
trusted receipt is `PROPOSED`; it is never adopted. Missing change flags
refuse. Unchanged requests remain `UNCHANGED` with
`owner_amendment_bound: false`.

Run from the repository root:

```text
python3 constraint_box/integrated_system/skills/cb-goal-amendment-guard/scripts/guard.py \
  --payload '{"schema":"constraintbox.goal-amendment.v1","operation":"cb-goal-amendment-guard.v1","target":"goal-1","object_changed":false,"success_condition_changed":false,"hard_constraints_changed":false}'
```

Receipts are deterministic and self-digested, audit/proposal-only, and always
carry `promotion_allowed: false`. Identity mismatches, malformed/unproven owner receipts,
authority-shaped requests, malformed JSON, cancellation, and write attempts
fail closed; no owner or goal file is written.
