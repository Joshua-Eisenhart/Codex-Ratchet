# A1 Live Packet/Profile Extract (v1)
Status: DRAFT / NONCANON (extract only; authority remains owner/control-plane sources)
Date: 2026-03-15

## Purpose
Provide one compact reload/reference surface for the current live A1 packet/profile path without forcing readers through the mixed draft structure of:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`

This file is a reference extract only.
It does not own any `RQ-*` requirements.

## Authority Sources
Primary owner/source surfaces:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`

Related historical draft branch-model surface:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`

## Current Interpretation Rule
- Use this extract for the current live A1 packet/profile path.
- Use `05_A1_STRATEGY_AND_REPAIR_SPEC.md` for requirement ownership and the broader Rosetta/repair role framing.
- Treat sections explicitly labeled `Legacy` in `05` and the operator/quota sections in `18` as historical draft doctrine, not as the live runtime/control operator law.

## Live Operator Law
Current live `operator_id` law comes from the control-plane bundle:
- `OP_A1_GENERATED`
- `OP_BIND_SIM`
- `OP_REPAIR_DEF_FIELD`
- `OP_MUTATE_LEXEME`
- `OP_REORDER_DEPENDENCIES`
- `OP_NEG_SIM_EXPAND`
- `OP_INJECT_PROBE`

Interpretation:
- operator enums come from `ENUM_REGISTRY_v1.md`
- bounded repair allowlists come from `A1_REPAIR_OPERATOR_MAPPING_v1.md`
- transported strategy object shape comes from `A1_STRATEGY_v1.md`

## Live A1 Output Surface
A1 outputs one strategy object:
- `A1_STRATEGY_v1`

That strategy is the admissible A1 transport/profile object for the A1 -> A0 path.

## Live Packet/Profile Highlights

### Top-level shape
At the current live packet/profile path, the strategy centers on:
- `schema`
- `strategy_id`
- `inputs`
- `budget`
- `policy`
- `targets`
- `alternatives`
- `sims`
- `self_audit`

### Packet discipline
- extra root keys on the strict local packet path are fail-closed
- richer authoring surfaces must be canonicalized down before packet emission

### Inputs highlights
Common live inputs include:
- `state_hash`
- source/fuel or save hashes as available
- pinned ruleset/megaboot hashes when active

### Policy highlights
Current live profile expects:
- forbidden-field discipline
- overlay-ban discipline where needed
- explicit `require_try_to_fail`

### Candidate object shape
Each candidate in `targets[]` / `alternatives[]` centers on:
- `item_class`
- `id`
- `kind`
- `requires[]`
- `def_fields[]`
- `asserts[]`
- `operator_id`

### Boundary hygiene
- free English must not leak into kernel-lane compile fields
- explanatory or overlay-like material must stay above the compile boundary
- current live packet validator also requires every `SIM_SPEC` candidate to carry at least one probe dependency id beginning with `P`

## Live Summary/Adjacency Surfaces
Some useful A1-facing summaries are currently adjacent to the strict packet root rather than part of the packet root:
- `target_terms`
- `family_terms`
- `admissibility`

Interpretation:
- these are summary/handoff aids
- they are not earned truth
- they should remain outside the strict validated packet root unless/until the packet schema is widened explicitly

## Current Family/Selector Reading
For the active reset direction, family/admissibility reading should prefer:
- explicit bounded A2 -> A1 family slices
- launch packets compiled directly from those family slices where available
- launch bundles prepared directly from those family slices where available
- adjacent admissibility/handoff surfaces
- controller/audit summaries that expose lane/head/negative/sim-family obligations

and should not infer live operator law from the historical branch-model sections of `05` or `18`.

Current helper-policy interpretation:
- the family-slice packet/bundle preparation path now defaults to validation mode `auto`
- `auto` prefers the local spec-object stack when present and otherwise falls back to the hand-written JSON schema path

## What This Extract Does Not Do
- does not replace `05` as requirement owner
- does not replace the control-plane strategy/operator specs
- does not redefine the legacy branch-model doctrine
- does not promote any proposal surface into earned state

## Operational Use
Use this extract when the task needs:
- a compact current A1 packet/profile read
- a safer reload surface for controller/A2/A1 work
- a quick answer to “what is the live A1 strategy object/profile path right now?”

If there is any conflict:
1. control-plane `A1_STRATEGY_v1` / operator-law surfaces win for live packet/operator shape
2. owner docs still win for requirement ownership
3. lower-loop earned/runtime reality still outranks all upper-loop summary surfaces
