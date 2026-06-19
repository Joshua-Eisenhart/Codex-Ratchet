# Build Card - manifold_family_c_integrated_v0

## Scope

Close exactly the `weld_feedstock_inventory_20260611.md` gap:

> No committed packet provides a Family C integrated super-sim; the unified-run mechanism is available as a mechanism template, not a completed C integration.

This packet builds one integrated Family C state object at `scratch_diagnostic` ceiling. It does not address A+B weld relation, cross-family weld controls, or the flux-carrying L/R asymmetric engine object.

## Pinned Controller Decisions

- LIVE rungs: `n=3` and `n=4` through `terrain_spinor_flux_nest_n3_v0` (`1b36e4a3c`) and `terrain_spinor_flux_nest_n4_v0` (`c36a80f6b`).
- Exact floor anchor: `geo_s1_three_qubit_floor_exact_v0` (`6ed5e961e`) as the C^8 floor.
- Boundary/stress context only: `geo_s1_scaling_stress_678q_exact_v0` (`b27d22317`) for n=6/7/8. It is cited but not run as a live C behavior rung.
- Shell support is consumed through the terrain packets, not raw `stage_lifted_*` rows.
- The unified-run mechanism is instantiated on this packet's own Family C state object, with per-row lineage, step-dependent/invariant classification, and consistency matrix.

## Carried Boundaries

- G3: no committed bare-current parent-row comparison; this packet carries the terrain packets' recomputed zero-terrain network boundary.
- G4: carrier reconstructed, not copied; committed site spinors and carrier hashes are consumed through the terrain packets.
- No n=5 behavior continuation.
- No behavior-class-growth claim beyond the committed n3/n4 saturation signal.

## Artifacts

- `manifold_family_c_integrated_v0_common.py`
- `manifold_family_c_integrated_v0_julia.jl`
- `manifold_family_c_integrated_v0_jax.py`
- `manifold_family_c_integrated_v0_pytorch.py`
- `write_envelope_spec.py`
- `validate_manifold_family_c_integrated_v0.py`
- `tests/test_manifold_family_c_integrated_v0.py`
- `builder_self_assessment.md`
- generated results under `results/`

## Required Commands

```bash
/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_julia.jl
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/write_envelope_spec.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_family_c_integrated_v0/manifold_family_c_integrated_v0_envelope_spec.json > system_v6/sims/manifold_family_c_integrated_v0/results/manifold_family_c_integrated_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_family_c_integrated_v0/validate_manifold_family_c_integrated_v0.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_family_c_integrated_v0/results/manifold_family_c_integrated_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/manifold_family_c_integrated_v0/tests
```

## Ceiling

Highest allowed claim: `scratch_diagnostic`, Family C integration evidence only.

Not allowed: weld/manifold/axis/bridge admission, formal admission, promotion, A+B weld relation, cross-family weld controls, flux-carrying L/R asymmetric engine object, n=5 behavior continuation, or behavior-class growth beyond committed n3/n4 saturation.
