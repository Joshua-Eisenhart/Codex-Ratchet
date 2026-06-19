# Build Card: manifold_dynamic_chart_v0

## Boundary

- Packet: `system_v6/sims/manifold_dynamic_chart_v0/`
- Object: Family A 33-cell dynamic density-state chart.
- Claim ceiling: `scratch_diagnostic_dynamic_chart_v0_first_measurement_attempt_only`.
- Classification: `scratch_diagnostic`.
- Row classification: `dynamic_chart_v0_first_measurement_attempt`.
- Promotion allowed: `false`.
- Formal admission allowed: `false`.
- NO git add/commit.
- NO Axis-0 admission, bridge admission, physics claim, final manifold claim, or final substrate choice.
- The final substrate remains OWNER-CHOICE across chart, spinor-network surface, and QCA/local-update readings.

## Authority

- Upgrade design: `system_v6/receipts/dynamic_manifold_upgrade_design_20260612.md` at `4fc7c2f3b`.
- Owner correction: `system_v6/receipts/owner_correction_axis0_not_built_20260612.md` at `0313d47bc`.
- Dynamics parent: `system_v6/sims/engines_run_with_axes_v0/` at `de243459e`.
- Standards codex: `system_v6/receipts/audit_standards_codex_v1.md`.
- G.2a idempotency-from-birth binds: validator delegates `audit_verdict.md` boundary checks to `scripts/builder_audit_boundary.py` from the first build.

## Object

This packet makes the design's v0 rung real at chart scale:

- per-cell density states `rho_c(t)` on the committed Family A 33-cell carrier;
- committed four-stroke generator schedule reused from `engines_run_with_axes_v0`;
- `S_vN(rho_c(t))` computed from density eigenvalues at each time;
- directed entropy gradients over committed adjacency;
- entropy-level shells recomputed at each `t`, with shell-boundary motion recorded;
- `j/k` future multiplicity rows from committed one-step continuations;
- perturb -> watch -> classify response rows over a pinned window;
- old static `phi` sign tested only as a falsifiable equilibrium-shadow bridge row.

The old static polynomial is never an entropy source.

## Controls

- identity dynamics: frozen trajectories must refuse/degenerate;
- scrambled adjacency: edge mapping changes the dynamic signature;
- dropped-half perturbation family: smaller kick family is measured separately;
- over-boundary perturbation: refused as a boundary-control row, not injected as a synthetic entropy state;
- no identity leak: classifier feature fields exclude `cell_id`, `state_id`, `start_cell`, and `current_cell`.

## Three-Engine Scope

- Julia: rebuild finite transition graph and trajectory signature with `Graphs`.
- JAX/Python: cross-check graph/trajectory counts with `networkx` and exact count guards with `sympy`.
- PyTorch: load-bearing density-state and vN entropy path with `torch.func`/`torch.linalg.eigvalsh`; exact count guards with `sympy`.
- Envelope is built with `scripts/build_three_engine_envelope.py`.

## Validator Commands

```bash
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_dynamic_chart_v0/manifold_dynamic_chart_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v0/manifold_dynamic_chart_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v0/manifold_dynamic_chart_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_dynamic_chart_v0/manifold_dynamic_chart_v0_envelope_spec.json > system_v6/sims/manifold_dynamic_chart_v0/results/manifold_dynamic_chart_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_dynamic_chart_v0/validate_manifold_dynamic_chart_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_dynamic_chart_v0/results/manifold_dynamic_chart_v0_envelope_results.json
PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q -p no:cacheprovider system_v6/sims/manifold_dynamic_chart_v0/tests
```

## Status

Implementation target:

- `rho_c(t)` density rows for `T>1`;
- state-derived local vN entropy and gradients;
- moving dynamic entropy-shell rows;
- `j/k` future rows;
- perturb bite and identity-refusal witness gates;
- falsifiable old-`phi` bridge row;
- all-three envelope, validator, tests, and builder self-assessment;
- no git add/commit.
