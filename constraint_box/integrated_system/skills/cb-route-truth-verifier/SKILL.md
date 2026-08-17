---
name: cb-route-truth-verifier
description: Compare declared routes with observed receipts. Detect fake FULL, missing children, substituted models, mixed-run receipts, missing MMM loads, parent-reported-only children, and stale output paths.
---

# CB route-truth verifier

FULL is illegal unless every declared child has a bound receipt. Parent-reported children are not FULL.
