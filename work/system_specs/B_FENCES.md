# B Fences (from BOOTPACK_THREAD_B_v3.9.13 only)

Status: NONCANON | Updated: 2026-02-18  
Source of truth for this file: `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`

## Message acceptance fence (MSG-001)

User message must be exactly one of:

- COMMAND_MESSAGE: one or more lines starting with `REQUEST`
- Note: boot text requires `REQUEST` followed by a space.
- ARTIFACT_MESSAGE: exactly one container:
  - EXPORT_BLOCK vN
  - THREAD_S_SAVE_SNAPSHOT v2
  - SIM_EVIDENCE_PACK (one or more SIM_EVIDENCE v1 blocks back-to-back)

Else: reject with tag `MULTI_ARTIFACT_OR_PROSE`.

## Rejection tag fence (BR-000A)

Only the following rejection tags are permitted (anything else is forbidden and triggers `SCHEMA_FAIL`):

- MULTI_ARTIFACT_OR_PROSE
- COMMENT_BAN
- SNAPSHOT_NONVERBATIM
- UNDEFINED_TERM_USE
- DERIVED_ONLY_PRIMITIVE_USE
- DERIVED_ONLY_NOT_PERMITTED
- UNQUOTED_EQUAL
- SCHEMA_FAIL
- FORWARD_DEPEND
- NEAR_REDUNDANT
- PROBE_PRESSURE
- UNUSED_PROBE
- SHADOW_ATTEMPT
- KERNEL_ERROR
- GLYPH_NOT_PERMITTED

## Derived-only fence (summary)

There is a derived-only term set and families; primitive use is rejected unless admitted via the term pipeline.
Pointers inside bootpack:

- `STATE DERIVED_ONLY_TERMS`
- `STATE DERIVED_ONLY_FAMILIES`
- `RULE BR-0D1 DERIVED_ONLY_SCAN`
- `RULE BR-0D2 DERIVED_ONLY_PERMISSION`

## Undefined-term + lexeme fences (summary)

Two distinct concepts:

- Compound term component admission (LEX-001) for TERM_DEF compounds.
- Content undefined-term fence (BR-0U1) for tokens in EXPORT_BLOCK content outside TERM/LABEL/FORMULA contexts.

Pointers inside bootpack:

- `STATE L0_LEXEME_SET`
- `RULE LEX-001 COMPOUND_TERM_COMPONENTS_DEFINED`
- `RULE BR-0U1 UNDEFINED_TERM_FENCE`

## Formula-specific fences (summary)

Formulas are carriers only; glyphs and tokens are gated.
Pointers inside bootpack:

- `RULE BR-0F1 FORMULA_TOKEN_FENCE`
- `RULE BR-0F2 FORMULA_DERIVED_ONLY_SCAN`
- `RULE BR-0F3 EQUALS_SIGN_GUARD`
- `RULE BR-0F4 FORMULA_ASCII_ONLY`
- `RULE BR-0F5 FORMULA_GLYPH_FENCE`
- `RULE BR-0F6 FORMULA_UNKNOWN_GLYPH_REJECT`
