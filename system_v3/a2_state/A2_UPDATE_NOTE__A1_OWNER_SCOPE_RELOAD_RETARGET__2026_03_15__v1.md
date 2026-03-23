# A2_UPDATE_NOTE__A1_OWNER_SCOPE_RELOAD_RETARGET__2026_03_15__v1

Status: DRAFT / NONCANON / DERIVED_A2 RESET NOTE
Date: 2026-03-15
Role: preserve the ownership-surface retarget that stops A1 owner docs from being read as uniformly live runtime law just because they own requirement ranges

## Scope

Patched owner surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md`

Related reload-hygiene surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/00_MANIFEST.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`

## Problem

`02_OWNERSHIP_MAP.md` correctly said that:
- `05_A1_STRATEGY_AND_REPAIR_SPEC.md` owns `RQ-040..RQ-049`, `RQ-097..RQ-098`
- `18_A1_WIGGLE_EXECUTION_CONTRACT.md` owns `RQ-100..RQ-108`

But that ownership statement alone could still mislead reloads into treating both files as uniformly live runtime/operator law.

That was still risky after the earlier spec retargets, because ownership and live runtime authority are not the same thing for these mixed draft surfaces.

## What changed

Added `A1 Owner-Scope Note` to:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/02_OWNERSHIP_MAP.md`

It now says:
- `05` still owns its requirement range, but is a mixed draft surface
- `18` still owns its requirement range, but its operator/quota sections are historical draft wiggle doctrine
- the live A1 operator enum/mapping for the current runtime/control path comes from:
  - `ENUM_REGISTRY_v1.md`
  - `A1_REPAIR_OPERATOR_MAPPING_v1.md`
  - `A1_STRATEGY_v1.md`

## Meaning

This is another reload guard, not a new doctrine.

The repo now says the same thing in three places:
- the read spine (`00_MANIFEST.md`)
- the mixed A1 draft spec itself (`05_A1_STRATEGY_AND_REPAIR_SPEC.md`)
- the ownership surface (`02_OWNERSHIP_MAP.md`)

That makes it much harder for a future read pass to accidentally flatten:
- requirement ownership
- mixed draft content
- live runtime/control law

## Verification

Grounded checks:
- `rg -n "A1 Owner-Scope Note|ENUM_REGISTRY_v1|A1_REPAIR_OPERATOR_MAPPING_v1|A1_STRATEGY_v1" system_v3/specs/02_OWNERSHIP_MAP.md`
- `sed -n '1,60p' system_v3/specs/02_OWNERSHIP_MAP.md`

These confirmed:
- the new owner-scope note is present
- the live control-plane operator-law references are present in the ownership surface

No runtime code changed in this step.

## Next seam

The next real structural choice is still the same:
- leave `05` as a mixed owner doc with good reload guards
- or split the live packet/profile material from the historical branch/wiggle material into separate surfaces
