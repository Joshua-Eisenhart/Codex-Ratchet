# A1 Historical Branch/Wiggle Extract (v1)
Status: DRAFT / NONCANON (extract only; authority remains owner draft surfaces)
Date: 2026-03-15

## Purpose
Provide one compact historical-draft read for the older A1 branch/wiggle model without making readers reconstruct it from the mixed owner docs.

This file is an extract only.
It does not own any `RQ-*` requirements.

## Authority Sources
Historical owner draft surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/05_A1_STRATEGY_AND_REPAIR_SPEC.md`

Live/runtime-control contrast surfaces:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`

## Interpretation Rule
- Use this extract when you need the older A1 branch/wiggle doctrine as doctrine history.
- Do not use this extract as the live runtime/control operator or packet source of truth.
- For the current live A1 packet/profile path, use:
  - `/home/ratchet/Desktop/Codex Ratchet/system_v3/specs/77_A1_LIVE_PACKET_PROFILE_EXTRACT__v1.md`

## Historical A1 Branch/Wiggle Model

### A1 branch exploration
The historical draft model centers on:
- explicit branch states
- explicit lineage fields
- separate novelty and viability scores
- explicit graveyard-targeted alternatives
- deterministic branch ranking
- deterministic stall handling and rebalance

### Historical branch states
The preserved draft branch lifecycle uses:
- `OPEN`
- `ACTIVE`
- `PARKED`
- `RETIRED`
- `RESURRECTABLE`

### Historical branch object ideas
The draft branch object includes concepts like:
- `branch_id`
- `parent_branch_id`
- `seed_hash`
- `prompt_hash`
- `operator_history[]`
- `feedback_refs[]`
- `novelty_score`
- `viability_score`
- `combined_rank_key`

### Historical compile-ready candidate shape
The historical wiggle draft still assumes compile-ready candidate objects with:
- `item_class`
- `id`
- `kind`
- `requires`
- `def_fields`
- `asserts`

That part overlaps with later/livelier A1 packet shape, but the surrounding branch/quota model is historical draft doctrine here.

## Historical Operator/Quota Model

### Historical operator set from `18`
The older wiggle draft preserves this operator vocabulary:
- `OP_MUTATE_LEXEME`
- `OP_SPLIT_COMPOUND`
- `OP_COMPOSE_COMPOUND`
- `OP_REORDER_DEPENDENCIES`
- `OP_ALT_FOR_FAILURE_MODE`
- `OP_GRAVEYARD_RESCUE`
- `OP_NEG_SIM_EXPAND`
- `OP_PROBE_BALANCE`

### Historical operator quota table from `18`
- `OP_MUTATE_LEXEME`: `0.18`
- `OP_SPLIT_COMPOUND`: `0.14`
- `OP_COMPOSE_COMPOUND`: `0.14`
- `OP_REORDER_DEPENDENCIES`: `0.12`
- `OP_ALT_FOR_FAILURE_MODE`: `0.16`
- `OP_GRAVEYARD_RESCUE`: `0.12`
- `OP_NEG_SIM_EXPAND`: `0.08`
- `OP_PROBE_BALANCE`: `0.06`

### Historical scheduler language from `05`
The mixed strategy/repair draft also preserves an older scheduler summary:
- `q_mutate_local = 0.35`
- `q_repair_from_reject = 0.30`
- `q_alt_generation = 0.20`
- `q_dependency_reorder = 0.10`
- `q_exploratory_novel = 0.05`

### Historical repair vocabulary from `05`
The older repair-loop draft vocabulary includes:
- `OP_REORDER_DEPS`
- `OP_SPLIT_COMPOUND`
- `OP_REBIND`
- `OP_ALT_REWRITE`
- `OP_SIM_EXPAND`
- `OP_PROBE_REBALANCE`

## Historical Branch/Wiggle Behaviors

### Historical novelty floor
The draft branch model preserves a novelty-floor idea:
- reject branch if novelty score `< 0.15`
- unless the branch addresses an unseen failure mode

### Historical stall / rebalance law
The historical wiggle draft preserves:
- stall detection after repeated no-improvement patterns
- deterministic quota rebalancing before retirement
- rebalance bias toward:
  - `OP_ALT_FOR_FAILURE_MODE`
  - `OP_GRAVEYARD_RESCUE`

### Historical graveyard / repair emphasis
The historical branch model explicitly emphasizes:
- at least one graveyard-seeking alternative per primary cluster
- repair generation consuming raw B tags and SIM failure classes
- expected failure modes attached to alternatives and negative-sim plans

## What this historical extract is good for
- understanding the older A1 branch/wiggle design intent
- comparing the old branch-model doctrine to the current control-plane/runtime path
- preserving historical reasoning about novelty, quotas, rebalance, graveyard pressure, and rescue

## What it is not good for
- choosing current live `operator_id` values
- defining the current transported A1 packet/profile shape
- defining the current runtime/control operator law

## Practical read split
If the question is:
- “what is the live A1 packet/profile/runtime-control path?” -> use `77`
- “what did the older branch/wiggle doctrine intend?” -> use this extract

If there is conflict:
1. lower-loop earned/runtime reality wins
2. live control-plane packet/operator sources win for current runtime law
3. this extract remains historical draft doctrine only
