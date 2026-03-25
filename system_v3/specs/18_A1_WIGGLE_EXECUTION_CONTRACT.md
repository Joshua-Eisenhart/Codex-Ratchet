# A1 Wiggle Execution Contract
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-100..RQ-108`

## Scope
This document defines how A1 performs high-entropy exploration while staying compile-safe for A0 and enforceable by B.

## Live Operator Law Note
This document remains a draft/noncanon branch-model surface.

Its operator/quota model is not the active runtime/control-plane operator law.

For the live operator enum and repair/operator mapping, use:
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
- `/home/ratchet/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`

Interpretation rule:
- read the operator/quota sections below as historical draft wiggle doctrine
- do not use them as the live source of truth for current runtime `operator_id` values

## Normative Clauses
- `RQ-100` MUST: A1 executes branch exploration using a fixed operator-quota table whose quotas sum to exactly `1.0` each cycle.
- `RQ-101` MUST: each branch record stores immutable lineage fields `branch_id`, `parent_branch_id`, `seed_hash`, `prompt_hash`, `operator_history[]`, and `feedback_refs[]`.
- `RQ-102` MUST: branch ranking computes `novelty_score` and `viability_score` as separate scalar fields; combined ordering uses a deterministic comparator.
- `RQ-103` MUST: each target cluster emits at least one explicit graveyard-seeking alternative (`alt_intent = TRY_TO_FAIL`) before cycle close.
- `RQ-104` MUST: repair generation consumes raw B tag classes and SIM failure classes directly (`reject_tags[]`, `park_tags[]`, `sim_failure_classes[]`) without prose translation.
- `RQ-105` MUST: every A1 kernel-lane candidate is emitted in compile-ready object form with required keys `item_class`, `id`, `kind`, `requires`, `def_fields`, `asserts`.
- `RQ-106` MUST: kernel-lane values are token-safe only; explanatory language is restricted to overlay-lane fields and cannot cross into compile lanes.
- `RQ-107` MUST: stall handling runs deterministic quota rebalancing before branch retirement and logs the rebalance vector.
- `RQ-108` MUST: every alternative and negative-sim plan includes explicit `expected_failure_modes[]` identifiers.

## Branch Object Schema (A1 Internal)
Required top-level fields:
- `branch_id` (string; unique in run)
- `state` (`OPEN|ACTIVE|PARKED|RETIRED|RESURRECTABLE`)
- `lineage` (object)
- `scores` (object)
- `targets[]` (list of compile-ready candidate objects)
- `alternatives[]` (list of compile-ready candidate objects)
- `negative_sim_plans[]` (list)
- `feedback_inputs` (object)

`lineage` required keys:
- `parent_branch_id` (string or `NONE`)
- `seed_hash` (sha256 hex)
- `prompt_hash` (sha256 hex)
- `operator_history[]` (ordered list of operator IDs)
- `feedback_refs[]` (ordered list of event IDs)

`scores` required keys:
- `novelty_score` (float in `[0,1]`)
- `viability_score` (float in `[0,1]`)
- `combined_rank_key` (deterministic sortable tuple encoded as string)

## Compile-Ready Candidate Object Schema
Required keys:
- `item_class`: `AXIOM_HYP|PROBE_HYP|SPEC_HYP`
- `id`: `<ID>`
- `kind`: `<KIND>`
- `requires[]`: list of IDs (may be empty)
- `def_fields[]`: list of DEF_FIELD objects (may be empty)
- `asserts[]`: list of ASSERT objects (may be empty)

`def_fields[]` object:
- `field_id` (string)
- `name` (string)
- `value_kind`: `BARE|TERM_QUOTED|LABEL_QUOTED|FORMULA_QUOTED`
- `value` (string)

`asserts[]` object:
- `assert_id` (string)
- `token_class` (bootpack token class)
- `token` (string)

## Legacy Operator Set (Historical Draft IDs)
Allowed operator IDs:
- `OP_MUTATE_LEXEME`
- `OP_SPLIT_COMPOUND`
- `OP_COMPOSE_COMPOUND`
- `OP_REORDER_DEPENDENCIES`
- `OP_ALT_FOR_FAILURE_MODE`
- `OP_GRAVEYARD_RESCUE`
- `OP_NEG_SIM_EXPAND`
- `OP_PROBE_BALANCE`

Unknown operator ID is invalid and must be dropped with logged reason `UNKNOWN_OPERATOR`.

This set is preserved as part of the older wiggle branch/quota model.
It does not redefine the live control-plane operator enum.

## Legacy Operator Quota Table (Historical Draft)
Cycle-default quota table:
- `OP_MUTATE_LEXEME`: `0.18`
- `OP_SPLIT_COMPOUND`: `0.14`
- `OP_COMPOSE_COMPOUND`: `0.14`
- `OP_REORDER_DEPENDENCIES`: `0.12`
- `OP_ALT_FOR_FAILURE_MODE`: `0.16`
- `OP_GRAVEYARD_RESCUE`: `0.12`
- `OP_NEG_SIM_EXPAND`: `0.08`
- `OP_PROBE_BALANCE`: `0.06`

Quota sum check:
- sum must equal exactly `1.0` under decimal normalization to 4 places.

## Ranking Comparator (Deterministic)
Sort key order:
1. `viability_score` descending
2. `novelty_score` descending
3. unresolved dependency count ascending
4. `branch_id` lexical ascending

Tie behavior is deterministic and stable.

## Legacy Stall Detection and Rebalance (Historical Draft)
Stall condition:
- no newly accepted survivors linked to branch family for `N=3` cycles, or
- repeated same reject tag set for `N=3` cycles.

Rebalance action:
- transfer `+0.05` quota from highest-nonproductive operator bucket to `OP_ALT_FOR_FAILURE_MODE`
- transfer `+0.03` quota from highest-nonproductive operator bucket to `OP_GRAVEYARD_RESCUE`
- keep exact-sum normalization to `1.0`

Retirement condition:
- rebalance applied twice with no improvement, then state -> `RETIRED`.

## A1 Output Packet Contract
A1 produces one `A1_STRATEGY_v1` packet containing:
- `cycle_id`
- `branch_selection_report`
- `candidate_objects[]`
- `alternative_objects[]`
- `negative_sim_plans[]`
- `expected_failure_modes[]`
- `quota_table_used`
- `rebalance_events[]`

This packet is the only input consumed by A0 for compilation.

## Acceptance Criteria (Spec-Level)
Minimum acceptance checks for this contract:
1. branch packet missing any `RQ-105` candidate key -> preflight fail.
2. missing `expected_failure_modes[]` on alternative -> preflight fail.
3. quota sum not `1.0` -> cycle invalidated.
4. kernel-lane free English detected in `BARE` value -> preflight fail.
5. repeated stall with no rebalance event -> contract violation.
