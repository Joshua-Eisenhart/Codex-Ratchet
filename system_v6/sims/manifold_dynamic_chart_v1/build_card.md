# Build Card: manifold_dynamic_chart_v1

## User Card

BUILD CARD - manifold_dynamic_chart_v1 (THE AXIS-0 EXPERIMENT - the v0 audit's contract + codex plan #4)

Repo: `/Users/joshuaeisenhart/Codex-Ratchet`.

Build boundary: everything in `system_v6/sims/manifold_dynamic_chart_v1/` only. NO git add/commit. Card copied here. Use the boundary helper. Standards codex binds; G.2a idempotency-from-birth binds.

Authority read-first:

- v0 + audit at `eb51339c0`: earned protocol machinery, state-derived entropy to `1e-12`, moving shells; did not earn any readout because `32/33` SPREAD was near-constant.
- codex criterion at `4142cecbe`, plan #4: a real distinction equals beats the majority baseline + stable across perturbation families + negative controls fail.
- upgrade design at `4fc7c2f3b`.

Experiment, not formula:

1. Perturbation families: vary kind, strength, and target.
2. Windows: use a pinned ladder longer than v0 `T=4`.
3. Classifiers: at least three pinned classifiers.
4. Separation criterion: a candidate readout EARNS only if it beats the majority baseline, is stable across `>=2` perturbation families, AND the negative controls fail it.
5. Honest outcomes: `separation_found`, `no_separation_anywhere`, or `partial`.
6. v0 regression: the v0 corner must reproduce `32/33`.

Witness gates: dynamics-nontriviality and perturbation-bite per family; refuse dead rows and report them.

Controls: identity dynamics, scrambled adjacency, label-permutation, dropped-half per family, and no identity leak.

Standard contract: three-engine where scoped, envelope, validator, tests, builder self-assessment.

Ceiling: `scratch_diagnostic`, Axis-0 EXPERIMENT v1, no admission either way.

## Pinned Grid

- Perturbation families: `unitary_kicks`, `dephasing_kicks`, `amplitude_kicks`, `generator_biased_kicks`.
- Strength ladder: `weak=1`, `medium=2`, `strong=3`, `very_strong=4` kick steps.
- Targets: `single_cell`, `neighborhood`, `shell_boundary`.
- Windows: `T=[4,8,12,16]`.
- Classifiers: `v0_divergence`, `baseline_growth_rate_sign`, `recovery_return_time`.
- Criterion string is emitted verbatim in source and results.

## Boundary

- Claim ceiling: `scratch_diagnostic_axis0_experiment_v1_no_admission`.
- Classification: `scratch_diagnostic`.
- Promotion allowed: `false`.
- Formal admission allowed: `false`.
- NO Axis-0 admission, bridge admission, physics claim, final manifold claim, or final substrate choice.
- G.2a idempotency-from-birth is implemented through `scripts/builder_audit_boundary.py`; validators must not hard-fail a later legitimate independent `audit_verdict.md`.

## Three-Engine Scope

- Julia: rebuild finite transition graph and trajectory signature with `Graphs`.
- JAX/Python: cross-check graph/sweep counts with `networkx` and exact count guards with `sympy`.
- PyTorch: load-bearing density-state and vN entropy path with `torch.func`/`torch.linalg.eigvalsh`; exact count guards with `sympy`.
- Envelope is built with `scripts/build_three_engine_envelope.py`.

## Validator Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_dynamic_chart_v1/manifold_dynamic_chart_v1_julia.jl
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v1/manifold_dynamic_chart_v1_jax.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v1/manifold_dynamic_chart_v1_pytorch.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v1/write_envelope_spec.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_dynamic_chart_v1/manifold_dynamic_chart_v1_envelope_spec.json > system_v6/sims/manifold_dynamic_chart_v1/results/manifold_dynamic_chart_v1_envelope_results.json
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v1/validate_manifold_dynamic_chart_v1.py
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_dynamic_chart_v1/results/manifold_dynamic_chart_v1_envelope_results.json
```

```bash
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_dynamic_chart_v1/tests
```
