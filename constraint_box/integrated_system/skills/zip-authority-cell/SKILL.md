---
name: zip-authority-cell
description: Use when independently checking that a ZIP_JOB cannot invent an operation and that its return remains input-bound and replayable.
---

# ZIP Authority-Collapse Cell

1. Bind one target ZIP SHA-256.
2. Replace its first task operation with an unimplemented operation while
   keeping packet hashes internally coherent.
3. Require `REFUSE_OPERATION_NOT_IMPLEMENTED` from the runtime registry.
4. Execute the valid target twice and require byte-identical return ZIPs.
5. Require both returns to bind the original target digest.
6. Emit only `output/authority-collapse.json` in a child return ZIP.

Validation: all three checks pass and the child return retains the report.

This cell is deterministic. Mini-MMM preload is required only if a future
language-model authority adversary is added. Claim ceiling: registry/input/replay boundary only.
