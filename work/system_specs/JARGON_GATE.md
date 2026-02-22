# Jargon Gate (quarantine until admitted)

Status: NONCANON | Updated: 2026-02-18  
Purpose: Prevent accidental “meaning inflation” by forcing dangerous words to stay quarantined until admitted through the term pipeline (B) or stripped into fuel (A2).

## Canon-gated (Thread B derived-only families)

Source: `core_docs/BOOTPACK_THREAD_B_v3.9.13.md` (derived-only families + derived-only term guard)

Families (exact family names; see bootpack for full member lists):

- `FAMILY_EQUALITY`
- `FAMILY_CARTESIAN`
- `FAMILY_TIME_CAUSAL`
- `FAMILY_NUMBER`
- `FAMILY_SET_FUNCTION`
- `FAMILY_COMPLEX_QUAT`

Rule shape (boot-enforced):

- Derived-only scanning applies only to lines inside `EXPORT_BLOCK CONTENT`.
- Whole-segment matches are detected (segments split on `_` and non-alphanumeric).
- Matches inside TERM/LABEL/FORMULA def-field quoting contexts are ignored.
- Remaining matches are rejected as `DERIVED_ONLY_PRIMITIVE_USE`, and also require `TERM_REGISTRY[t].STATE == CANONICAL_ALLOWED` (else `DERIVED_ONLY_NOT_PERMITTED`).

Also note:

- `DERIVED_ONLY_TERMS` includes more than the families above (e.g., optimization words like `optimize/maximize/minimize/utility`, plus “keyword smuggling” minimal variants).

## A2 quarantine vectors (high-entropy hazards)

Source: `work/rebaseline/A2_FUEL_EXTRACT_x_grok_chat_TOE.md`

These are not canon rules; they are operational hazards:

- Teleology/deity language (“god”, “destiny”, “ends of time”)
- Time-first narratives (“future causes present”)
- FTL signaling claims (must separate from non-signaling correlations)
- Speculative psych/aliens/DMT transmissions (overlay-only)

## Practical boundary mapping

- If a term is canon-gated: keep it out of B-facing artifacts unless admitted.
- If a phrase is A2-hazard: keep it in A2 fuel extracts only, and rewrite to operator/observable candidates before any proposal attempt.
