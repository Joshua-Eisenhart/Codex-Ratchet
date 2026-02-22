# RUNTIME_IMAGE_POLICY v1

Purpose: define runtime memory discipline as a stable system-image contract.

This document is doctrine-only.
It does NOT modify transport or kernel behavior.

## Runtime Image Policy

- `runtime/` is the full system image.
- Only the following persistent directories are allowed:
  - `canonical_ledger/`
  - `snapshots/`
  - `current_state/`
  - `cache/`
- `cache/` is derived-only and deletable.
- Deleting `cache/` must not change `state_hash`.

## Scope Constraints

- No additional persistent directories are allowed.
- No new serialization formats are allowed.
