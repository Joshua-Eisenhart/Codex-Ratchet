# Type2 Weyl Inversion Status Note

Generated: 2026-04-04
Source files cited:
- `system_v4/probes/a2_state/sim_results/operator_basis_search_results.json` (geometry_crosscheck block)
- `system_v4/probes/a2_state/sim_results/lower_tier_operator_basis_search_results.json`

---

## Type1: MATCH

Type1 engine operator assignment matches the probe canonical exactly.

| Layer | Engine assigns | Probe canonical | Match |
|-------|---------------|-----------------|-------|
| Fiber | Fi, Te | Fi, Te | true |
| Base  | Fe, Ti | Fe, Ti | true |

`geometry_crosscheck.per_engine_type.type1.fully_matches = true`

## Type2: INVERTED (open)

Type2 engine operator assignment is the fiber/base inversion of the probe canonical.

| Layer | Engine assigns | Probe canonical | Match |
|-------|---------------|-----------------|-------|
| Fiber | Fe, Ti | Fi, Te | false |
| Base  | Fi, Te | Fe, Ti | false |

`geometry_crosscheck.per_engine_type.type2.fully_matches = false`

The probe canonical scope field states explicitly:
> "Type-2 has inverted fiber/base grammar (z-family on fiber, x-family on base)"

## What this means

- All B3.1-B3.4 tests and SymPy proofs pass against the canonical (Type1-aligned) basis.
- The lower-tier search (`lower_tier_operator_basis_search_results.json`) confirms the noncommuting basis split survives local search, but this was also run against the Type1-aligned canonical.
- No dedicated sim or fix addresses the Type2 inversion.
- The Type2 inversion is **documented and open**, not resolved.

## What this does NOT claim

- This note does NOT claim the Type2 inversion is a bug or a feature. It is an observed structural fact that has not been adjudicated.
- This note does NOT claim B3.x results transfer to Type2 without additional proof work.
- This note does NOT propose a fix.
