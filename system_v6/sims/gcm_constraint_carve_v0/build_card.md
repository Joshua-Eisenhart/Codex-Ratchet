# gcm_constraint_carve_v0 Build Card

## Boundary

- Packet: `gcm_constraint_carve_v0`.
- Location: `system_v6/sims/gcm_constraint_carve_v0/`.
- Scope: `scratch_diagnostic`.
- Ceiling: first computed-carve candidate only, carrier-and-pins-relative, not THE manifold.
- Git: NO git add/commit.
- Boundary helper: `scripts/builder_audit_boundary.py`.
- G.2a idempotency-from-birth: builders may not write or rely on a builder-authored `audit_verdict.md`; the envelope carries `no_builder_audit_verdict` and `no_builder_audit_verdict_envelope_gate`.

## Authority Read First

1. `system_v6/receipts/gcm_reanchor_requirement_20260612.md` at `393c5147a`: the manifold is carved, not drawn; the standing tooth is "where is the constraint set and what did it carve?"
2. `system_v6/receipts/validity_audit_lane_c_doctrine_20260612.md` at `53ae02357`: `M(C) = {x : x admissible under C}`, `S/~_M` as quotient identity, `a=a iff a~b`, and the build order.
3. `/Users/joshuaeisenhart/wiki/concepts/constraint-manifold-architecture.md`: a finite admissibility process must pin `C`, compute survivors, and quotient only after survival is known.
4. `system_v6/foundations/root_axioms_v0_1_DRAFT.md`: finitude, distinguishability, persistence/history, and the root identity pressure.
5. `system_v6/foundations/two_engine_readout_automaton_20260609.md` at `dd9ec4999`: first `M(C,t)` update hook.
6. `system_v6/foundations/working_math_scaffold_20260609.md`, `/Users/joshuaeisenhart/wiki/projects/codex-ratchet/qit-axes-terrain-operator-fold-2026-06-09.md`, and `/Users/joshuaeisenhart/wiki/concepts/terrain-laws-and-loop-geometry.md`: terrain/operator signatures are scaffold inputs only until computed off survivors.
7. `system_v6/receipts/audit_standards_codex_v1.md`: G7 pin rule and G.2a boundary.

## Candidate Space

Finite state/configuration carrier:

```text
S = {(x,y,z) in {-1,-1/2,0,1/2,1}^3}
```

The density subcarrier is the 33-cell Bloch-ball grid cut by `x^2 + y^2 + z^2 <= 1`, source-locked to the Family A 33-cell dynamic chart estate (`manifold_dynamic_chart_v0`, committed as `eb51339c0`) and kept as a quotient/readout carrier, not as foundation admission.

## Pinned Constraint Family C

Each constraint is executable and source-cited in `gcm_constraint_carve_v0_common.py`.

- `C1_finite_density_carrier`: keep only the finite density-state subcarrier. Source: root axioms finitude plus constraint-manifold architecture.
- `C2_probe_distinguishability_xz`: pinned probe family `M={sigma_x,sigma_z}` must distinguish the candidate from the zero active-probe class. Source: root distinguishability pressure and quotient identity.
- `C3_persistence_n01_order_gap`: `D_z after R_x` and `R_x after D_z` must leave different active-probe signatures, so update history is not erased. Source: N01/history cannot be erased plus order-gap scaffold.
- `C4_G7_operator_residency_pin`: composition legality rejects simultaneous dissipative/circulation active residency; zero active-probe boundary is left to `C2`. Source: G7 operator residency and terrain placement constraints.

## Computed Product

The packet computes:

- `M(C)`: survivors under all constraints, with every exclusion attributed in a kill ledger.
- `~_M`: probe-relative indistinguishability on survivors under `M={sigma_x,sigma_z}`.
- `S/~_M`: quotient classes with stability under one committed update.
- Existence probes: stable, independent, chart-recoverable, and negative-controlled.
- Carved organization: survivor adjacency, quotient adjacency, components, and terrain-signature readout off the survivor structure.
- Terrain question: whether the carved structure matches dissipative-legal vs circulation-legal signatures, or honestly misses the atlas.
- Controls: empty-C, over-constrained C, per-constraint erasure, and probe-family scramble.
- `M(C,t)` hook: one committed update `C -> C'` with recomputed survivors and quotient classes.

## Validation Commands

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_v0/gcm_constraint_carve_v0_common.py
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_v0/gcm_constraint_carve_v0_jax.py
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_v0/gcm_constraint_carve_v0_pytorch.py
```

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/gcm_constraint_carve_v0/gcm_constraint_carve_v0_julia.jl
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_v0/write_envelope_spec.py
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/gcm_constraint_carve_v0/gcm_constraint_carve_v0_envelope_spec.json > system_v6/sims/gcm_constraint_carve_v0/results/gcm_constraint_carve_v0_envelope_results.json
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/gcm_constraint_carve_v0/validate_gcm_constraint_carve_v0.py
```

```text
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/gcm_constraint_carve_v0/tests
```
