# A1 Strategy Declaration (v1)
Status: DRAFT / NONCANON
Date: 2026-02-20

Purpose: define a **declarative A1 output** that provides “wiggle room” while keeping B safe.

Authority notes:
- This file is a harness/interface spec (A1/A0). It is not a Thread B bootpack.
- B remains the only canon adjudicator.

==================================================
1) Object
==================================================

Object: `A1_STRATEGY_v1`

Representation:
- Authoring format: YAML or JSON is allowed.
- Canonicalization requirement:
  - A0 must parse the strategy and re-serialize it into a deterministic canonical JSON form
  - A0 must hash the canonical form and record that hash in run provenance

==================================================
2) Required Fields (minimum)
==================================================

Top-level keys:

- `schema`: must equal `A1_STRATEGY_v1`
- `meta`:
  - `strategy_id`: string (unique within a run)
  - `created_utc`: ISO-8601 (UTC)
  - `source`: enum: `human` | `llm`
  - `model`: string (if source==llm; else empty allowed)

- `budget`:
  - `max_items`: int (upper bound on compiled B items)
  - `max_sims`: int (upper bound on sims to run this cycle)
  - `max_wall_ms`: int (upper bound on local execution time)
  - `sim_budget_share`:
    - `baseline`: float (0..1)
    - `boundary_sweep`: float (0..1)
    - `perturbation`: float (0..1)
    - `adversarial_neg`: float (0..1)
    - `composition_stress`: float (0..1)
    - total must equal 1.0

- `policy`:
  - `overlay_ban_terms`: list[string]
    - these tokens must not be admitted as canon-facing term literals
    - these tokens must not appear unquoted in any B-facing DEF_FIELD that is scanned
  - `require_alternatives`: bool
  - `require_positive_sim`: bool
  - `require_negative_sim`: bool
  - `require_stress_suite`: bool
  - `min_negative_modes_per_target`: int (>=1 when negative sims are required)

- `targets` (list of target objects; ordered):
  Each target is one of the following kinds:
  - TERM target
  - MATH_DEF target
  - COMPOUND target (term literal with underscores)

==================================================
3) Target Objects
==================================================

3.1 TERM target

Required keys:
- `kind`: `TERM`
- `term`: string (term literal, lower-case + underscores allowed)
- `binds`: string (math anchor id; typically `S_L0_MATH` for early stages)

Optional keys:
- `alternatives`: list[ALT] (plausible wrong variants; see below)
- `evidence`:
  - `positive_sim`: SIM_REF
  - `negative_sims`: list[SIM_REF]
- `notes`: string (non-executable; may contain natural language)

3.2 MATH_DEF target

Required keys:
- `kind`: `MATH_DEF`
- `spec_id`: string (B-facing SPEC_HYP id)
- `objects`: list[string] (lowercase tokens; will be rendered into DEF_FIELD OBJECTS)

Optional keys:
- `alternatives`: list[ALT]
- `evidence`:
  - `positive_sim`: SIM_REF
  - `negative_sims`: list[SIM_REF]
- `notes`: string (non-executable)

3.3 COMPOUND target

Required keys:
- `kind`: `COMPOUND`
- `term`: string (term literal containing `_`)

Optional keys:
- `notes`: string (non-executable)

==================================================
4) Alternative Objects (ALT)
==================================================

ALT is an A1 object used to ensure a real graveyard:
- A0 must compile alternatives into B-grammar candidates that are “nearby” but structurally wrong.
- Alternatives should be designed to fail with informative B tags (derived-only, undefined-term, schema fail, etc.).

ALT keys:
- `suffix`: string (used to derive a unique spec id)
- `mode`: enum `TERM_VARIANT` | `MATH_DEF_VARIANT`
- `payload`: dict (A0-compile-time only; not B-facing directly)
- `expected_failure`: list[string] (B reject/park tags expected; non-binding)

==================================================
5) Sim References (SIM_REF)
==================================================

SIM_REF keys:
- `sim_id`: string (stable id)
- `sim_path`: string (repo-relative path) OR `sim_template`: string
- `evidence_token`: string (the token that SIM_EVIDENCE will provide)
- `family`: enum `BASELINE|BOUNDARY_SWEEP|PERTURBATION|ADVERSARIAL_NEG|COMPOSITION_STRESS`
- `failure_mode_id`: string (required for `ADVERSARIAL_NEG`)
- `expected_outcome`: enum `EXPECT_PASS|NEG_EXPECT_FAIL_TARGET|NEG_EXPECT_REJECT_ALTERNATIVE`

Rules:
- A0 must not emit SIM_SPEC unless a sim exists (path exists or template resolvable).
- If `policy.require_negative_sim == true`, a TERM target without an available negative sim must be downgraded to “trial-only” or skipped (policy decision; never silently admitted as ratcheted).
- If `policy.require_stress_suite == true`, each target class must include all required sim families before being reported as meaningful.

==================================================
6) Deterministic Compilation Contract (A0)
==================================================

A0 must:
- enforce budget ceilings
- enforce overlay bans
- compile targets + alternatives into B-grammar candidates
- compile SIM_SPEC and CANON_PERMIT declarations only when sims/evidence plans exist
- never emit free natural language into B-scanned fields

B remains authoritative on acceptance/rejection.
