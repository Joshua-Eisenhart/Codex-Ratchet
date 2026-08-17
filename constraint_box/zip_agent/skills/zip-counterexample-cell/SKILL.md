---
name: zip-counterexample-cell
description: Use when independently attacking a ZIP_JOB with bounded path, custody, operation, and output mutations.
---

# ZIP Counterexample Cell

1. Bind one target ZIP SHA-256.
2. Generate six replayable mutants: changed input bytes, undeclared member,
   duplicate member, traversal path, unknown operation, and required output that
   no task produces.
3. Validate each mutant through the same public packet validator.
4. Require the exact reason code assigned to that mutation.
5. Emit only `output/counterexample.json` inside a child return ZIP.

Validation: no mutant is accepted and all observed reasons equal expected
reasons. A new acceptance or changed reason is REVISE.

This cell is deterministic. Mini-MMM preload is required only for a future
language-model mutation proposer. Claim ceiling: six finite counterexamples only.
