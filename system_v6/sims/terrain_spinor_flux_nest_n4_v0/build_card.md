# Build card - terrain_spinor_flux_nest_n4_v0

Status: builder packet, not an audit verdict.

Ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Inputs

- Template lineage: committed `system_v6/sims/terrain_spinor_flux_nest_n3_v0/` at `1b36e4a3c`, including `audit_verdict.md` and `builder_hardening_addendum.md`.
- Carrier: committed `system_v6/sims/stage_lifted_spinor_shell_n4_v0/` at `30d21022e`, C^16 four-qubit support with 4 sites, 5 edges, and 2 faces.
- Seven-parent lineage pattern: `stage_lifted_spinor_shell_n4_v0`, `terrain_spinor_shell_nest_v0`, `geo_s5_terrain_flows_v0`, `ratchet_s2_two_shell_flux_v0`, `geo_disintegration_machinery_v0`, `geo_union_rule_k_leaves_v0`, and `terrain_exact_mirror_finder_v0`.
- N3 anchor: `system_v6/sims/terrain_spinor_flux_nest_n3_v0/results/terrain_spinor_flux_nest_n3_v0_envelope_results.json`.

## Built Artifacts

- `terrain_spinor_flux_nest_n4_v0_common.py`
- `terrain_spinor_flux_nest_n4_v0_jax.py`
- `terrain_spinor_flux_nest_n4_v0_pytorch.py`
- `terrain_spinor_flux_nest_n4_v0_julia.jl`
- `terrain_spinor_flux_nest_n4_v0_envelope.py`
- `validate_terrain_spinor_flux_nest_n4_v0.py`
- `builder_hardening_addendum.md`
- `results/terrain_spinor_flux_nest_n4_v0_jax_results.json`
- `results/terrain_spinor_flux_nest_n4_v0_pytorch_results.json`
- `results/terrain_spinor_flux_nest_n4_v0_julia_results.json`
- `results/terrain_spinor_flux_nest_n4_v0_envelope_results.json`
- `results/terrain_spinor_flux_nest_n4_v0_validator_results.json`

## Builder Facts

- Carrier provenance is rederived from committed n4 per-site `psi_L`/`psi_R` rows. It emits `parent_site_rows_sha256=a4db762169eaa01f17a11c5ad5a76ea24b6f8e4b7faaab3d2eb1324243565eff`, `reconstructed_state_vector_sha256=00f7a6cd956d09d9372ffc356da4d0c3ec76bb13f641596e3108c5a1f8526b76`, and `reconstructed_probabilities_sha256=e18acaf3d5116e2820084b8f6be1bf99aaecbc7bbde9b7b06dfa8563698ef2d0`.
- Terrain edge-couplings run on the committed n4 support graph: `e01`, `e12`, `e23`, `e03`, `e02`; faces `f012`, `f023`.
- In-solver continuity binds scaled edge-current formula rows, derives site divergence from edge variables, and checks the negated balance. z3, cvc5, and Julia-Z3 return real `unsat` and erased target `sat` on target site `q1`.
- Density quotient reproduction is complete at builder scope: the n4 packet rederives the committed stage n4 `P3_density_quotient` row and records a full-row SHA match.
- Collapse controls pass with honest scope: decoupling checks same-schema `z_dot` rows only, zero-terrain recomputes zero couplings/currents/flux/continuity, and no committed bare-current parent row comparison is claimed.
- Saturation comparison row reports changed classes: `carrier_support`, `decoupling_control`, and `density_quotient_control`. Rescale-only rows include terrain edge-couplings, flux continuity, k-leaf conditioning, network observable signatures, and terrain-drop control.

## Fresh Commands

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_jax.py
```

Result: `ok=true`.

```text
env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_pytorch.py
```

Result: `ok=true`.

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_julia.jl
```

Result: `ok=true`.

```text
env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_envelope.py
```

Result: `ok=true`, `max_divergence=0.0`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/terrain_spinor_flux_nest_n4_v0/validate_terrain_spinor_flux_nest_n4_v0.py --phase builder
```

Result: `{"errors": [], "ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/terrain_spinor_flux_nest_n4_v0/results/terrain_spinor_flux_nest_n4_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/terrain_spinor_flux_nest_n4_v0/terrain_spinor_flux_nest_n4_v0_julia.jl
```

Result: no violations for all three source files.

## Scalar Agreement

Envelope divergence metric: `conditioned_total_abs_current`.

- Julia: `0.260547429214`
- JAX: `0.260547429214`
- PyTorch: `0.260547429214`
- max divergence: `0.0`

Primary terrain observables:

- bare `total_abs_current=1.100562920308`
- bare `total_signed_transport_flux=-1.086614377305`
- conditioned `total_abs_current=0.260547429214`
- conditioned `total_signed_transport_flux=-0.246503665249`

## Boundary

This packet is a scratch diagnostic build receipt only. It is not an audit verdict, formal admission, stage closure, bridge/axis admission, physics claim, manifold claim, or actual n=5 result.
