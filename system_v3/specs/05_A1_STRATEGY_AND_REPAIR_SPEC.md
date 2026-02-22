# A1 Strategy and Repair Specification
Status: DRAFT / NONCANON
Date: 2026-02-20
Owner: `RQ-040..RQ-049`

## Role
A1 is nondeterministic exploration and repair.
It proposes strategy objects; it does not emit B containers.

Execution-depth companion:
- `/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v3/specs/18_A1_WIGGLE_EXECUTION_CONTRACT.md`

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
This schema is the minimal stable interface A0 expects. Extra keys may exist above the boundary, but A0 may drop/ignore them.

Top-level required keys:
- `schema: A1_STRATEGY_v1`
- `budget`
- `policy`
- `targets`
- `alternatives`
- `sims`

### Kernel-Lane Item Object (inside `targets[]` and `alternatives[]`)
Each candidate is represented as a structured object that A0 can deterministically compile into bootpack grammar lines.

Minimum fields:
- `item_class`: `AXIOM_HYP|PROBE_HYP|SPEC_HYP`
- `id`: `<ID>`
- `kind`: for:
  - `AXIOM_HYP`: `axiom_kind`
  - `PROBE_HYP`: `probe_kind`
  - `SPEC_HYP`: `spec_kind`
- `requires[]`: list of dependency IDs (may be empty)
- `asserts[]`: list of assertion objects (may be empty)
- `def_fields[]`: list of DEF_FIELD objects (may be empty)

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

## Wiggle Model (`RQ-042`)
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

## Branch Scheduler (`RQ-046`)
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

## Novelty Floor (`RQ-047`)
Each new branch is compared against active branches.
Novelty score uses deterministic token/structure distance.

Default rule:
- reject branch if novelty score `< 0.15`
- unless branch addresses unseen failure mode id

## Repair Loop (`RQ-043`)
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

## Branch Lifecycle (`RQ-048`)
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

## Stall Behavior
If branch pool stalls:
- increase unresolved-frontier bias
- increase failure-mode-coverage bias
- enforce strict duplicate suppression
