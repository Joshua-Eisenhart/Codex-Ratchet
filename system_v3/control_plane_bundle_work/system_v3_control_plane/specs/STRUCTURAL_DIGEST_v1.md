# STRUCTURAL_DIGEST v1

Defines deterministic structural comparison for A1 “real wiggle” enforcement.

This is NOT a kernel primitive.
This is a deterministic A0 comparator.

## Purpose

Prevent fake wiggle (ID churn or cosmetic change only) by defining a deterministic structural fingerprint for a proposal object.

## Included vs excluded fields (normative)

Included fields:
- `spec_kind`
- `requires`
- `fields`
- `asserts`
- `operator_id`

Excluded fields:
- `proposal_id`
- `parent_proposal_id`
- `self_audit`

No other fields are excluded unless explicitly added in a future version.

## Normalization (normative)

Given a proposal object:

1) Remove excluded fields.
2) Normalize arrays:
   - `requires` sorted lexicographically (bytewise).
   - `fields` sorted lexicographically by tuple (`name`, `value`).
   - `asserts` sorted lexicographically by tuple (`token_class`, `token`).
3) Serialize using canonical JSON rules defined by `specs/ZIP_PROTOCOL_v2.md`:
   - UTF-8
   - LF newlines
   - sorted keys at every object level
   - stable separators (`,` and `:` only; no spaces)
   - no trailing spaces
   - exactly one trailing LF
4) Compute SHA-256 of the canonical bytes.
5) The resulting lowercase hex64 is the `structural_digest`.

## Structural distinctness rule (normative)

Two proposals are structurally distinct iff:

`structural_digest(A) != structural_digest(B)`.

ID-only differences MUST NOT change `structural_digest`.

## Determinism requirement

Structural digest MUST be identical across independent implementations given identical proposal objects.
