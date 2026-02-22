
# PROMOTION_BINDING v1

This specification defines deterministic binding rules for promotion readiness using:
- negative SIM outcomes
- graveyard density
- tightening rules

It does not redesign the architecture; it defines measurable gates.

## 1. Definitions

- **Candidate cluster**: a set of related proposals targeting the same spec_kind/term family (A0-defined grouping).
- **Promotion state**: a deterministic label computed from artifacts.
  Promotion state labels are defined in `specs/ENUM_REGISTRY_v1.md` under `promotion_state (A0 deterministic labels)`.

  At minimum:
  - `NOT_READY`
  - `READY_FOR_TIGHTEN`
  - `READY_FOR_CANON`
  (Exact labels may be aligned with existing runtime; this doc defines gates, not storage.)

## 2. Inputs required
Deterministically derived by A0 from:
- SIM_EVIDENCE blocks (counts, kill signals, evidence signals)
- graveyard summaries (density by spec_kind)
- current state hash / snapshot
- strategy/operator traces

## 3. Gates (deterministic)

## Threshold source
Constants used in promotion gates MUST be explicitly defined in A0 runtime configuration.

Required constants:
- `MIN_NEG_FAILS`
- `T_graveyard`
- `W_neg`
- `W_grave`

If undefined, promotion state MUST default to `NOT_READY`.

These constants are integer-based deterministic gates, not probabilistic thresholds.

### Gate G1: Negative SIM coverage
A candidate cluster is NOT eligible for promotion unless:
- `negative_sim_count >= MIN_NEG_FAILS` for the cluster, AND
- `kill_signal_count == 0` for the cluster

### Gate G2: Stress-family coverage (counts-based)
If the system defines stress families, then for eligibility:
- Every required stress family must have at least one SIM attempt recorded for the cluster.

(Required stress families are A0-configured constants; no optimization.)

### Gate G3: Graveyard pressure
If graveyard density for the cluster’s spec_kind exceeds a deterministic threshold `T_graveyard` (integer), then:
- promotion state MUST remain `NOT_READY` until either:
  - the graveyard density decreases below threshold, OR
  - a tightening proposal is accepted that changes the cluster structure.

### Gate G4: Operator diversity
A cluster is NOT eligible for promotion unless:
- at least 2 distinct operator_ids have been used across attempts in the cluster,
- and at least one attempt used an operator other than `OP_MUTATE_LEXEME`.

Purpose: prevent id-churn promotion.

## 4. Promotion outputs
Promotion state transitions MUST NOT modify canonical constraint state directly.
Promotion decisions do not directly mutate canon.
They must result in:
- deterministic state labels stored by A0 (or via B-defined mechanism), and/or
- a requirement for A1 to produce an EXPORT proposal in the next cycle.

## 5. Failure signatures
- Promotion stuck at `NOT_READY` with `kill_signal_count > 0` indicates SIM binding is working (correctly blocks promotion).
- Promotion stuck at `NOT_READY` with `negative_sim_count == 0` indicates missing negative SIM instrumentation.
- Promotion oscillation indicates non-deterministic gating; must be treated as a bug.
