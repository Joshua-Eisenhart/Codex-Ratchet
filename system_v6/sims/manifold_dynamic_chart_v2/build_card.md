# Build Card: manifold_dynamic_chart_v2

## User Card

BUILD CARD - manifold_dynamic_chart_v2 (the STABILITY-axis attack; the v1 audit's named continuation)

Repo: `/Users/joshuaeisenhart/Codex-Ratchet`.

Build boundary: everything in `system_v6/sims/manifold_dynamic_chart_v2/` only. NO git add/commit. Card copied here. Use the boundary helper. Standards codex binds; G.2a idempotency-from-birth binds.

Object: Axis-0 EXPERIMENT v2 stability-axis attack.

Authority read-first:

- v1 + audit at `1231dbbd9`: accepted partial. `amplitude_kicks/weak/shell_boundary/T=12/recovery_return_time` separates but fails cross-family stability; transitivity answer is 33 singleton orbits, so nothing is symmetry-forbidden; v2 target is the STABILITY AXIS.
- panel 10 at `3ff556c10`: purity kicks, relaxation-scale windows, and shell-weighted TV functional are directionally confirmed methods.
- Criterion unchanged: beats majority + stable across `>=2` families + negative controls fail.

## v2 Design

1. Anchor on the v1 partial corner: `shell_boundary`, `T>=12`, `recovery_return_time`. Compute per-family classification vectors at `(weak, shell_boundary, T=12, recovery_return_time)` for every v1 family and report the disagreement cells as data.
2. Test pinned stability refinements:
   - family-robust classifiers over common sign structure, with an agreement-threshold ladder;
   - shell-weighted TV functional `sum_r r*||Delta rho_r(T)||_1` as a new classifier;
   - relaxation-calibrated windows computed from the unperturbed generator-family slowest relaxation scale before the sweep;
   - purity kicks proper through projective resets.
3. Apply the unchanged criterion. Either a stable separation or another bounded partial is the result.
4. Reproduce the v1 anchor corner and v0 regression corner.
   - v0 regression expected corner: `32/33` SPREAD.

## Boundary

- Classification: `scratch_diagnostic`.
- Claim ceiling: `scratch_diagnostic_axis0_experiment_v2_no_admission`.
- Boundary phrase: no admission.
- Promotion allowed: `false`.
- Formal admission allowed: `false`.
- NO Axis-0 admission, bridge admission, physics claim, final manifold claim, or final substrate choice.
- G.2a idempotency-from-birth is implemented through `scripts/builder_audit_boundary.py`; builder output must not include an `audit_verdict.md`.

## Three-Engine Scope

- Julia: rebuild finite transition graph and trajectory signature with `Graphs`.
- JAX/Python: cross-check graph/sweep counts with `networkx` and exact count guards with `sympy`.
- PyTorch: load-bearing density-state, vN entropy, projective purity reset, shell-weighted TV, and relaxation-window path with `torch`/`torch.func`/`torch.linalg`.
- Envelope is built with `scripts/build_three_engine_envelope.py`.

## Validator Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_pytorch.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/write_envelope_spec.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_dynamic_chart_v2/manifold_dynamic_chart_v2_envelope_spec.json > system_v6/sims/manifold_dynamic_chart_v2/results/manifold_dynamic_chart_v2_envelope_results.json
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v2/validate_manifold_dynamic_chart_v2.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_dynamic_chart_v2/results/manifold_dynamic_chart_v2_envelope_results.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_dynamic_chart_v2/tests
```
