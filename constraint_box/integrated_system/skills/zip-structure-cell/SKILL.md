---
name: zip-structure-cell
description: Use when independently checking ZIP_JOB identity, task order, file registry, and required-output structure.
---

# ZIP Structure Cell

1. Bind one target ZIP SHA-256.
2. Validate it twice with strict Pydantic and JSON Schema models.
3. Compare packet digest, parsed task order, exact member registry, and exact
   required-output set across both passes.
4. Emit only `output/structure.json` inside a child return ZIP.

Validation: every check is Boolean true and the child return manifest binds the
same target digest. Missing or malformed evidence is REVISE, never PASS.

This cell is deterministic. Mini-MMM preload is required only if a future
language-model member is added. Claim ceiling: packet structure and replay only.
