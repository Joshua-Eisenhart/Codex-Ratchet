# B Artifacts + Fences (System Spec Pack v2)
Status: DRAFT / NONCANON
Date: 2026-02-20

## Authority Source
- `core_docs/BOOTPACK_THREAD_B_v3.9.13.md`

## Accepted B-Facing Artifact Containers
- `EXPORT_BLOCK vN`
  - contains: `AXIOM_HYP`, `SPEC_HYP`, `PROBE_HYP`
- `SIM_EVIDENCE v1` (or pack, if allowed)
- `THREAD_S_SAVE_SNAPSHOT v2` (exported state snapshot)

## Core Fence Classes (names are bootpack-defined)
- Schema/grammar fences
  - strict headers + fields
  - no prose mixed with artifacts

- Undefined-term fence
  - disallows unadmitted lower-case lexemes outside scan-exempt quoted contexts

- Lexeme fence (compounds)
  - compounds like `a_b` require components (`a`, `b`) to exist first (or be in L0 lexeme set)

- Derived-only fence
  - certain tokens are forbidden as primitives until admitted through the term pipeline and permitted

- Glyph / formula / equality guards
  - "=" is a protected glyph mapped to term literal `equals_sign`
  - mixed alnum tokens are gated by `digit_sign`

- Probe pressure
  - constrains spec-to-probe ratio per batch (bootpack-defined)

## Output Requirements (audit)
- Every rejection must be recorded with:
  - reason tag
  - offending item id
  - raw lines (verbatim) for replay/mining

