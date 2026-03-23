# A1 Strategy and Repair Specification
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-040..RQ-049`

## Role
A1 is nondeterministic exploration and repair.
It proposes strategy objects; it does not emit B containers.

Execution-depth companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`

## Live Operator Law Note
The current live packet/runtime/control path uses the control-plane operator enum and repair mapping:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/ENUM_REGISTRY_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_REPAIR_OPERATOR_MAPPING_v1.md`
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/control_plane_bundle_work/system_v3_control_plane/specs/A1_STRATEGY_v1.md`

So the older repair operator vocabulary later in this draft should be read as legacy/nonactive doctrine, not as the current runtime `operator_id` source of truth.

## Section Status Map
Sections in this file are mixed rather than uniformly current.

Treat these sections as the still-useful live/profile-facing surface:
- `Role`
- `Anti-Classical Leakage`
- `Rosetta Function`
- `Rosetta: Cold-Core Extraction + Reattachment Dictionaries`
- `Mandatory Output`
- `Strategy Container Shape`
- `A1_STRATEGY_v1 Minimal Schema (Implementation-Facing)`
- `Strategy Contents`
- `Canon Boundary`
- `Fix-Intent Schema`

Treat sections explicitly labeled `Legacy` as preserved historical draft branch/wiggle doctrine, not as the live runtime/control path:
- `Legacy Wiggle Model`
- `Legacy Branch Scheduler`
- `Legacy Novelty Floor`
- `Legacy Repair Loop Vocabulary`
- `Legacy Branch Lifecycle`
- `Legacy Stall Behavior`

## Anti-Classical Leakage (`RQ-097`, `RQ-098`)
- `RQ-097` MUST: treat any “classical proof thinking” that bypasses ratcheting as drift and correct it via explicit proposal repair.
- `RQ-098` MUST: default stance is non-conservative batching; convergence is via massive exploration under finitude and noncommutation.

## Rosetta Function
A1 is the Rosetta layer between:
- high-entropy/source language (A2 and human intent)
- canon-safe B grammar targets

A1 responsibilities at this boundary:
- rewrite overlays/jargon into ratchet-safe target terms
- preserve mapping metadata for traceability
- avoid leaking noncanon language into B-scanned fields

## Rosetta: Cold-Core Extraction + Reattachment Dictionaries
The Rosetta function is two-phase:

1) **Cold-core extraction (kernel lane)**:
- start from a model/idea expressed in some source dialect (field jargon, metaphor, narrative)
- strip to explicit math objects/relations only
- rewrite as minimal kernel-safe candidate structures (TERM_DEF / MATH_DEF / SIM_SPEC plans)
- force explicitness by expanding hidden assumptions into named dependencies
- generate close alternatives designed to fail (B fences and/or SIM falsification)

2) **Reattachment dictionaries (overlay lane)**:
- once a kernel term/spec survives (B + SIM evidence), A1 may attach one or more overlay dictionaries
  that map multiple external dialects back onto the same kernel object
- these overlays are annotation only: they do not ratchet and they do not justify canon
- overlays must never leak into B-scanned fields; they remain above the A0 boundary

Analogy: the historical Rosetta Stone enabled translation by presenting the same content in multiple
languages. Here, the “stone” is the kernel term/spec admitted by B, and the “translations” are
field-specific overlay dictionaries (like an airport sign with multiple languages pointing to the same place).

## Mandatory Output (`RQ-040`)
Output format is `A1_STRATEGY_v1` only.

Required sections:
- metadata
- budget
- policy
- targets
- alternatives
- sim/evidence plan

## Strategy Container Shape (YAML-first)
`A1_STRATEGY_v1` is an authoring-time declaration. YAML is preferred for readability.
JSON is allowed. A0 canonicalizes either to deterministic JSON (`RQ-030`).

## A1_STRATEGY_v1 Minimal Schema (Implementation-Facing)
This section describes the current live packet profile validated by the active bootpack A1->A0 path.
For the current local packet path, extra root keys are rejected fail-closed; richer authoring surfaces must be canonicalized into this subset before packet emission.

Top-level required keys:
- `schema: A1_STRATEGY_v1`
- `strategy_id`
- `inputs`
- `budget`
- `policy`
- `targets`
- `alternatives`
- `sims`
- `self_audit`

Required live subfields:
- `inputs`
  - `state_hash`
  - `fuel_slice_hashes[]`
  - `bootpack_rules_hash`
  - `pinned_ruleset_sha256`
  - `pinned_megaboot_sha256`
- `policy`
  - `forbid_fields[]`
  - `overlay_ban_terms[]`
  - `require_try_to_fail`
- `self_audit`
  - `strategy_hash`
  - `compile_lane_digest`
  - `candidate_count`
  - `alternative_count`
  - `operator_ids_used[]`

Authoring-side helper summaries (not current packet root fields):
- `target_terms`
  - compact ordered term list extracted from final `targets[]`
  - intended to make the final selected target family legible without re-parsing `def_fields`
- `family_terms`
  - compact ordered term list derived from `target_terms` plus active role-bearing admissibility buckets
  - intended to make family scope legible for audits, controller logic, and downstream non-compile consumers
  - should prefer heads, companions, passengers, witnesses, and witness-floor terms
  - should not inflate with residue-only terms by default
- `admissibility`
  - compact role-placement summary emitted by A1 when available
  - intended to make landing/admissibility judgment explicit before A0 compilation

Minimal `admissibility` shape:
- `executable_head[]`
- `active_companion_floor[]`
- `late_passengers[]`
- `witness_only_terms[]`
- `residue_terms[]`
- `landing_blockers[]`

Recommended extended `admissibility` shape for active selector output:
- `witness_floor[]`
- `current_readiness_status{}`
- `process_audit{}`
  - `wiggle_minimum_content_ok`
  - `movement_over_throughput_ok`
  - `evidence_gated_promotion_ok`
  - `sim_evidence_boundary_ok`
  - `hash_anchored_sim_evidence_ok`
  - `state_sim_evidence_hash`
  - `warnings[]`

Boundary note:
- `target_terms` and `family_terms` are summary aids, not authoritative compile inputs
- `admissibility` is advisory A1 judgment, not earned truth
- on the live packet path, these helper summaries must stay outside the validated packet root
- they should remain available in adjacent audit/handoff surfaces rather than packet fields rejected by the validator

Operational purpose of the extended fields:
- surface `WIGGLE_MINIMUM_CONTENT_CONTRACT` as a default output check rather than scattered doctrine
- prefer movement over throughput by warning when residue dominates the strategy object
- keep evidence-gated term promotion visible in the emitted role/status map
- make the sims source/evidence boundary visible at the strategy handoff layer
- on the current local selector path, allow hash-anchored sim evidence to be satisfied either by `inputs.evidence_summary_hash` or by a deterministic digest of state-backed `sim_results`

### Kernel-Lane Item Object (inside `targets[]` and `alternatives[]`)
Each candidate is represented as a structured object that A0 can deterministically compile into bootpack grammar lines.

Minimum fields:
- `item_class`: current live packet path requires `SPEC_HYP`
- `id`: `<ID>`
- `kind`: current live packet path allows `MATH_DEF|TERM_DEF|LABEL_DEF|CANON_PERMIT|SIM_SPEC`
- `requires[]`: list of dependency IDs (may be empty)
- `asserts[]`: list of assertion objects (may be empty)
- `def_fields[]`: list of DEF_FIELD objects (may be empty)
- `operator_id`: emitting operator id for traceability

Assertion object:
- `assert_id`: `<ID>` (line-local correlation id)
- `token_class`: one of bootpack TOKEN_CLASS values
- `token`: `<TOKEN>`

DEF_FIELD object:
- `field_id`: `<ID>` (line-local correlation id)
- `name`: `<FIELD_NAME>`
- `value_kind`: `BARE|TERM_QUOTED|LABEL_QUOTED|FORMULA_QUOTED`
- `value`: string

Compilation rule (boundary hygiene):
- Any free English / high-entropy text MUST be placed in `LABEL_QUOTED` or `FORMULA_QUOTED` only.
- `BARE` values must be restricted to kernel-safe tokens (IDs, token-like atoms) to avoid undefined-term and derived-only violations.
- current live packet validator also requires every `SIM_SPEC` candidate to include at least one probe dependency id beginning with `P`

Minimum structural skeleton (illustrative; non-normative keys may be added above the boundary):
```yaml
schema: A1_STRATEGY_v1
meta:
  created_utc: "YYYY-MM-DDTHH:MM:SSZ"
  model_id: "<llm-id>"            # A1 nondeterministic half
  prompt_hash_sha256: "<hex>"     # optional
  response_hash_sha256: "<hex>"   # optional
budget:
  max_items: 200
  max_sims: 200
policy:
  forbid_fields: ["confidence", "probability", "embedding", "hidden_prompt"]
rosetta:
  mappings: []                    # overlay -> kernel-safe target forms
targets: []                       # primary candidates + dependency assumptions
alternatives: []                  # designed-to-fail siblings
sims:
  positive: []
  negative: []
fix_intents: []                   # optional; see RQ-045/RQ-049
admissibility:                    # optional compact landing-role summary
  executable_head: []
  active_companion_floor: []
  late_passengers: []
  witness_only_terms: []
  residue_terms: []
  landing_blockers: []
target_terms: []                  # optional explicit term list from final targets
family_terms: []                  # optional explicit family/role term summary
```

Hard bans (A1 output policy; enforced at A0 preflight):
- no `confidence` / `probability` fields (nominalized-reality meta rule)
- no raw transcripts or free prose blobs intended to reach B

## Strategy Contents (`RQ-041`)
For each target cluster:
- rosetta mapping entries (source term -> target term/spec ids)
- primary candidate(s)
- dependency assumptions
- alternatives designed to fail meaningfully
- positive/negative sim references
- expected failure modes

## Legacy Wiggle Model (`RQ-042`)
This section preserves older branch-exploration draft language.
It is not the live control-plane operator/scheduler source of truth.

Allowed exploration moves:
- lexical mutations
- composition/decomposition mutations
- dependency re-order proposals
- structural variants per same target class
- adversarial alternative generation

Disallowed:
- direct canon writes
- bypassing root constraints
- prose payloads aimed at B parser surface

## Legacy Branch Scheduler (`RQ-046`)
This quota summary is preserved as older draft branch doctrine.
It does not define the current live runtime/control scheduler surface.

A1 maintains branch states:
- `OPEN`
- `ACTIVE`
- `PARKED`
- `RETIRED`
- `RESURRECTABLE`

Per cycle quota table (defaults):
- `q_mutate_local = 0.35`
- `q_repair_from_reject = 0.30`
- `q_alt_generation = 0.20`
- `q_dependency_reorder = 0.10`
- `q_exploratory_novel = 0.05`

Quota sum must be exactly 1.0.

## Legacy Novelty Floor (`RQ-047`)
Each new branch is compared against active branches.
Novelty score uses deterministic token/structure distance.

Default rule:
- reject branch if novelty score `< 0.15`
- unless branch addresses unseen failure mode id

## Legacy Repair Loop Vocabulary (`RQ-043`)
This repair operator list is preserved as older draft terminology.
The live runtime/control path now uses the control-plane operator enum/mapping instead.

Inputs:
- B reject tags
- B park reasons
- SIM fail classes
- evidence pending backlog

Repair operators:
- `OP_REORDER_DEPS`
- `OP_SPLIT_COMPOUND`
- `OP_REBIND`
- `OP_ALT_REWRITE`
- `OP_SIM_EXPAND`
- `OP_PROBE_REBALANCE`

All repaired candidates carry `repair_from` references.

## Legacy Branch Lifecycle (`RQ-048`)
Retire branch when:
- identical failure tag repeats for `N` retries (default `N=3`)
- no novelty increase for `M` cycles (default `M=2`)

Resurrect branch when:
- new dependency became admitted
- new sim evidence changes failure surface
- alternative sibling branch succeeded nearby

## Canon Boundary (`RQ-044`)
A1 cannot modify canonical state directly.
All canon effects occur only through A0->B admission path.

## Fix-Intent Schema (`RQ-045`, `RQ-049`)
A1 may emit fix intents for runtime/spec issues:
- `FIX_INTENT_A0_*`
- `FIX_INTENT_B_*`
- `FIX_INTENT_SIM_*`

Each fix intent must include:
- `target_layer`
- `observed_failure`
- `evidence_refs`
- `proposed_change`
- `risk_class`
- `rollback_shape`

Fix intents are A2/engineering review inputs, not runtime mutations.

## Legacy Stall Behavior
If branch pool stalls:
- increase unresolved-frontier bias
- increase failure-mode-coverage bias
- enforce strict duplicate suppression
