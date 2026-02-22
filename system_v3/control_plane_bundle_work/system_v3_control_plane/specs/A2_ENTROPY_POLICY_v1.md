# A2_ENTROPY_POLICY v1

Purpose: define persistence and purge discipline for high-entropy A2 material.

This document is doctrine-only.
It does NOT modify transport or kernel behavior.

## Policy

- Structured memory may persist.
- Raw transcripts and private reasoning artifacts must not persist.
- High-entropy intermediates must be purged after structured extraction.
- `A2_SAVE` is equivalent to zipping `runtime/` as system image context.

## Scope Constraints

- No new image artifact types are introduced.
- No changes to runtime directory layout are introduced.
- No new serialization formats are introduced.
