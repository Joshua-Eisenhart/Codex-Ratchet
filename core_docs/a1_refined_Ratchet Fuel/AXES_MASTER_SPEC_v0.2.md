# AXES_MASTER_SPEC_v0.2

DATE_UTC: 2026-02-02T00:00:00Z
AUTHORITY: CANON (axis semantics + nonconflation rules)

REFERENCE
- See: CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC_v1.0.md

GLOBAL LOCKS (HARD)
- Geometry is the constraint manifold and exists before Axes 0–6.
- Axes 0–6 are functions/slices on the constraint manifold; they are not primitives.
- Axis-3 is ONLY the engine-family split (Type-1 vs Type-2).

## 0) Notation

- Constraint manifold: **M** (shorthand for **M(C)**).
- Axis-i: **Aᵢ : M → Vᵢ** (a classification/slice).
- Axis indices (0–6) are bookkeeping labels for slices; they are not carriers.

## 1) Axis-0 (two-class slice)

- Codomain: **V₀ = {A0-CLASS-1, A0-CLASS-2}**
- Rule: Axis-0 is a two-class partition of **M** computed from admissible probes/operators.
- Candidate computations live in: AXIS0_SPEC_OPTIONS_v0.* (noncanon option sheets).

## 2) Axis-6 (precedence / composition sidedness)

- Codomain: **V₆ = {UP, DOWN}**
- Rule: Axis-6 selects which composition order is used when composing admissible operators/channels.
- Axis-6 is the sidedness/precedence slice; do not conflate with Axis-4.

## 3) Axis-5 (generator regime split)

- Codomain: **V₅ = {GEN-CLASS-1, GEN-CLASS-2}**
- Rule: Axis-5 partitions generator/operator families into two regimes (names remain placeholder in CANON).
- Evidence hooks: existing Axis-5 sims/scripts (noncanon), without importing Axis-3 semantics.

## 4) Axis-3 (engine-family split)

- Codomain: **V₃ = {Type-1, Type-2}**
- Rule: Axis-3 selects the engine-family template (Type-1 vs Type-2).
- Axis-3 is not a chirality/handedness/spinor/Berry/flux tag.

## 5) Axis-4 (variance-order math class split)

- Codomain: **V₄ = {DEDUCTIVE, INDUCTIVE}**
- Rule: Axis-4 is the two-class split in operator update math class (variance-order).
- Loop-order experiments (SEQ01–SEQ04, FWD/REV) are probes of Axis-4; they are not the definition.

## 6) Axis-1 × Axis-2 (Topology4)

- Axis-1 and Axis-2 are slices whose product defines **Topology4** (four base regimes).
- The axis product is the base-class split itself.
- Graph edges / adjacency between bases are derived structure, not Axis-1/2.

## 7) Guardrails (nonconflation)

- Axis-4 ≠ Axis-6 (math class vs composition sidedness).
- Axis-1×Axis-2 base regimes ≠ edges/adjacency structures.
- Axis-3 is only the engine-family split; do not bind it to any legacy substrate.

## 8) Ratchet ingestion order (roadmap only)

- Candidate build order: **0 → 6 → 5 → 3 → 4 → (1×2)**
- This is a build order for admissions/evidence; it is not a precedence claim about geometry.
