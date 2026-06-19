# NR Assets Report

Repo: `/Users/joshuaeisenhart/Codex-Ratchet`
Date: 2026-06-09
Scope: read-only repo verification; report-only write to `/tmp/found/nr_assets_report.md`.

## Fresh Runs

| Item | Status | Command | Exit | Key values | Result path |
|---|---|---:|---:|---|---|
| Julia Hopf foliation | PASS | `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier system_v5/julia_carrier/clifford_torus_nested_hopf_foliation.jl` | 0 | `torus_is_constrained_slice=true`; `interior_s3_constraint_max_residual=2.220446049250313e-16`; `torus_metric_det_min=0.08637287570313155`; `foliation_covers_S3=true`; `foliation_volume_residual=3.0239863946235346e-8`; `sample_reconstruction_max_residual=4.611102534756203e-16`; `eta_bin_min_count=5`; `clifford_torus_equal_radius_slice=true`; `clifford_target_radius_residual=2.220446049250313e-16`; `flat_t2_control_pass=true`; `flat_t2_s3_constraint_min_residual=0.9999999999999998`; `parity_status=compared`; `parity_max_diff=1.0658141036401503e-13`; `within_1e-9=true` | `system_v5/julia_carrier/clifford_torus_nested_hopf_foliation_julia_results.json` |
| Julia Weyl sheet pair | PASS | `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=system_v5/julia_carrier system_v5/julia_carrier/weyl_sheet_pair_probe.jl` | 0 | `generic_chi=0.6382081404405828`; `swap_chi=-0.6382081404405828`; `no_chirality_chi=1.1102230246251565e-16`; `parity_symmetric_chi=0.0`; `chirality_load_bearing=true`; `parity_max_diff=1.1102230246251565e-16` | `system_v5/julia_carrier/weyl_sheet_pair_probe_julia_results.json` |
| JAX Hopf foliation | PASS | `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/julia_carrier/jax_clifford_torus_nested_hopf_foliation.py` | 0 | `torus_is_constrained_slice=true`; `interior_s3_constraint_max_residual=4.440892098500626e-16`; `torus_metric_det_min=0.08637287570313155`; `foliation_covers_S3=true`; `foliation_volume_residual=3.023975736482498e-08`; `sample_reconstruction_max_residual=2.9893669801409083e-16`; `eta_bin_min_count=5`; `clifford_torus_equal_radius_slice=true`; `clifford_target_radius_residual=2.220446049250313e-16`; `flat_t2_control_pass=true`; `flat_t2_s3_constraint_min_residual=0.9999999999999996`; `parity_max_diff=1.0658141036401503e-13`; `within_1e-9=true`; `max_diff_key=volume_estimate` | `system_v5/julia_carrier/clifford_torus_nested_hopf_foliation_jax_results.json` |
| JAX Weyl sheet pair | PASS | `/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 system_v5/julia_carrier/jax_weyl_sheet_pair_probe.py` | 0 | `generic_chi=0.6382081404405828`; `swap_chi=-0.6382081404405828`; `no_chirality_chi=2.3498984427972137e-17`; `parity_symmetric_chi=-2.4734191356739254e-17`; `chirality_load_bearing=True`; `parity_max_diff=1.1102230246251565e-16`; `numpy_compute_used=False`; `jax_x64_enabled=True` | `system_v5/julia_carrier/weyl_sheet_pair_probe_jax_results.json` |

## Reuse Inventory

### `system_v5/julia_carrier/clifford_torus_nested_hopf_foliation.jl`

Constants: `OBJECT_ID`, `RESULT_PATH`, `JAX_REFERENCE_PATH`, `TOL`, `STRICT_STOP_TOL`, `COVERAGE_TOL`, `PHASE_COUNT`, `VOLUME_STEPS`, `S3_SAMPLE_COUNT`, `ETA_BINS`.

| Name | Signature | Returns / use |
|---|---|---|
| `torus_point` | `torus_point(eta::Float64, phi::Float64, chi::Float64)` | `(z,w)` in `C^2` with Hopf-torus parameterization. |
| `s3_constraint_residual` | `s3_constraint_residual(z::ComplexF64, w::ComplexF64)` | Scalar `abs(|z|^2+|w|^2-1)`. |
| `phase_grid` | `phase_grid()` | `PHASE_COUNT` phases over `[0,2pi)`. |
| `interior_torus_checks` | `interior_torus_checks()` | Dict of interior Hopf-torus residuals and metric determinant minimum. |
| `volume_check` | `volume_check()` | Dict with quadrature `volume_estimate`, `s3_volume_reference`, `foliation_volume_residual`. |
| `deterministic_s3_sample` | `deterministic_s3_sample(k::Int)` | `(z,w,eta)` deterministic sample on `S3`. |
| `sample_reconstruction_check` | `sample_reconstruction_check()` | Dict of reconstruction residuals and eta coverage bins. |
| `core_circle_checks` | `core_circle_checks()` | Dict for `eta=0,pi/2` core circle residuals. |
| `clifford_torus_check` | `clifford_torus_check()` | Dict for equal-radius Clifford-torus residuals at `eta=pi/4`. |
| `flat_t2_control` | `flat_t2_control()` | Dict rejecting flat `T2` as off-`S3` control. |
| `parity_against_peer` | `parity_against_peer(result::Dict{String,Any}, peer_path::String)` | Dict comparing shared scalars/booleans against peer backend. |
| `build_result` | `build_result()` | Full result Dict, including verdicts, controls, shared scalars, parity, stop condition. |
| `print_summary` | `print_summary(result::Dict{String,Any})` | Prints run summary; returns nothing. |

### `system_v5/julia_carrier/weyl_sheet_pair_probe.jl`

Constants: `OBJECT_ID`, `RESULT_PATH`, `JAX_REFERENCE_PATH`, `TOL`, `STRICT_STOP_TOL`, `I2`, `SX`, `SY`, `SZ`, `N_REF`.

| Name | Signature | Returns / use |
|---|---|---|
| `dm` | `dm(psi::Vector{ComplexF64})` | Density matrix `psi * psi'`. |
| `rho_from_bloch` | `rho_from_bloch(r::Vector{Float64})` | `2x2` density matrix from Bloch vector. |
| `bloch_from_rho` | `bloch_from_rho(rho::Matrix{ComplexF64})` | 3-vector Bloch coordinates. |
| `spinor_from_angles` | `spinor_from_angles(theta::Float64, phi::Float64, fiber_phase::Float64)` | Normalized `C^2` spinor with fiber phase. |
| `spinor_from_bloch` | `spinor_from_bloch(r::Vector{Float64}, fiber_phase::Float64)` | Spinor section over Bloch vector plus fiber phase. |
| `canonical_section` | `canonical_section(r::Vector{Float64})` | Zero-phase spinor section. |
| `fiber_phase` | `fiber_phase(psi::Vector{ComplexF64}, r::Vector{Float64})` | Scalar phase of `psi` against canonical section. |
| `wrap_phase` | `wrap_phase(x::Float64)` | Wrapped phase via `atan(sin(x),cos(x))`. |
| `cross3` | `cross3(a::Vector{Float64}, b::Vector{Float64})` | 3D cross product. |
| `sigma_from_ref` | `sigma_from_ref(n::Vector{Float64})` | Pauli matrix combination `n dot sigma`. |
| `bool_scalar` | `bool_scalar(x::Bool)` | `1.0` or `0.0`. |
| `vec_payload` | `vec_payload(v::Vector{Float64})` | Float list payload. |
| `pair_metrics` | `pair_metrics(label::String, psi_l::Vector{ComplexF64}, psi_r::Vector{ComplexF64})` | Dict for L/R pair: `chi`, trace form, Bloch vectors, residuals, fiber phases, overlap. |
| `parity_block` | `parity_block(result::Dict{String,Any})` | Dict comparing shared scalars against JAX peer. |
| `main` | `main()` | Builds result JSON, prints summary, exits on stop condition. |

### `system_v5/julia_carrier/jax_clifford_torus_nested_hopf_foliation.py`

Constants: `OBJECT_ID`, `BASE_DIR`, `RESULT_PATH`, `JULIA_REFERENCE_PATH`, `TOL`, `STRICT_STOP_TOL`, `COVERAGE_TOL`, `PHASE_COUNT`, `VOLUME_STEPS`, `S3_SAMPLE_COUNT`, `ETA_BINS`.

| Name | Signature | Returns / use |
|---|---|---|
| `py_float` | `py_float(x: Any) -> float` | Host float from JAX value. |
| `torus_point` | `torus_point(eta: float, phi: float, chi: float) -> tuple[jax.Array, jax.Array]` | `(z,w)` Hopf-torus point. |
| `s3_constraint_residual` | `s3_constraint_residual(z: jax.Array, w: jax.Array) -> float` | Scalar `S3` residual. |
| `phase_grid` | `phase_grid() -> list[float]` | Phase grid. |
| `interior_torus_checks` | `interior_torus_checks() -> dict[str, Any]` | Interior torus residuals and metric determinant minimum. |
| `volume_check` | `volume_check() -> dict[str, Any]` | Vectorized quadrature volume check. |
| `deterministic_s3_sample` | `deterministic_s3_sample(k: int) -> tuple[jax.Array, jax.Array, float]` | Deterministic `S3` sample. |
| `sample_reconstruction_check` | `sample_reconstruction_check() -> dict[str, Any]` | Reconstruction and eta-bin coverage dict. |
| `core_circle_checks` | `core_circle_checks() -> dict[str, Any]` | Core-circle residual dict. |
| `clifford_torus_check` | `clifford_torus_check() -> dict[str, Any]` | Equal-radius Clifford-torus residual dict. |
| `flat_t2_control` | `flat_t2_control() -> dict[str, Any]` | Off-`S3` flat torus control dict. |
| `parity_against_peer` | `parity_against_peer(result: dict[str, Any], peer_path: Path) -> dict[str, Any]` | Peer parity comparison dict. |
| `build_result` | `build_result() -> dict[str, Any]` | Full JAX result dict. |
| `print_summary` | `print_summary(result: dict[str, Any]) -> None` | Prints run summary. |
| `main` | `main() -> int` | Writes result JSON and returns process status. |

### `system_v5/julia_carrier/jax_weyl_sheet_pair_probe.py`

Constants: `OBJECT_ID`, `BASE_DIR`, `RESULT_PATH`, `JULIA_REFERENCE_PATH`, `TOL`, `STRICT_STOP_TOL`, `I2`, `SX`, `SY`, `SZ`, `N_REF`.

| Name | Signature | Returns / use |
|---|---|---|
| `py_float` | `py_float(x: Any) -> float` | Host float from JAX value. |
| `py_bool` | `py_bool(x: Any) -> bool` | Host bool from JAX value. |
| `vec_payload` | `vec_payload(v: jax.Array) -> list[float]` | Float list payload. |
| `jax_x64_enabled` | `jax_x64_enabled() -> bool` | Runtime x64 enabled flag. |
| `source_numpy_markers` | `source_numpy_markers() -> dict[str, bool]` | Source-text NumPy marker booleans. |
| `dm` | `dm(psi: jax.Array) -> jax.Array` | Density matrix `outer(psi, conj(psi))`. |
| `rho_from_bloch` | `rho_from_bloch(r: jax.Array) -> jax.Array` | `2x2` density matrix from Bloch vector. |
| `bloch_from_rho` | `bloch_from_rho(rho: jax.Array) -> jax.Array` | 3-vector Bloch coordinates. |
| `spinor_from_angles` | `spinor_from_angles(theta: float, phi: float, fiber_phase: float) -> jax.Array` | `C^2` spinor with fiber phase. |
| `spinor_from_bloch` | `spinor_from_bloch(r: jax.Array, fiber_phase: float) -> jax.Array` | Spinor section over Bloch vector plus fiber phase. |
| `canonical_section` | `canonical_section(r: jax.Array) -> jax.Array` | Zero-phase spinor section. |
| `fiber_phase` | `fiber_phase(psi: jax.Array, r: jax.Array) -> jax.Array` | Scalar phase against canonical section. |
| `wrap_phase` | `wrap_phase(x: jax.Array) -> jax.Array` | Wrapped phase. |
| `sigma_from_ref` | `sigma_from_ref(n: jax.Array) -> jax.Array` | Pauli matrix combination `n dot sigma`. |
| `bool_scalar` | `bool_scalar(value: bool) -> float` | `1.0` or `0.0`. |
| `pair_metrics` | `pair_metrics(label: str, psi_l: jax.Array, psi_r: jax.Array) -> dict[str, Any]` | Dict for L/R pair: `chi`, trace form, Bloch vectors, residuals, fiber phases, overlap. |
| `parity_block` | `parity_block(result: dict[str, Any]) -> dict[str, Any]` | Peer parity comparison dict. |
| `build_result` | `build_result() -> dict[str, Any]` | Full JAX result dict. |
| `main` | `main() -> None` | Writes result JSON, prints summary, exits on stop condition. |

## Capability Receipts

| Capability | Status | Receipt path | Pass field | Key evidence |
|---|---|---|---|---|
| z3 | PASS | `system_v4/probes/a2_state/sim_results/tool_capability_z3_results.json` | `summary.all_pass=true`; `all_pass=true` | `tool_integration_depth.z3=load_bearing`; `classification=canonical`. |
| cvc5 | PASS | `system_v4/probes/a2_state/sim_results/tool_capability_cvc5_results.json` | `summary.all_pass=true`; `all_pass=true` | `tool_integration_depth.cvc5=load_bearing`; positive/negative/boundary all pass. |
| geomstats | PASS | `system_v4/probes/a2_state/sim_results/sim_geomstats_capability_results.json` | `summary.all_pass=true`; `all_pass=true` | `tool_integration_depth.geomstats=load_bearing`; `pass_count=7`; `total_count=7`. |
| sympy | PASS | `system_v4/probes/a2_state/sim_results/tool_capability_sympy_results.json` | `summary.all_pass=true`; `all_pass=true` | `tool_integration_depth.sympy=load_bearing`; `classification=canonical`. |
| clifford | PASS | `system_v4/probes/a2_state/sim_results/tool_capability_clifford_results.json` | `summary.all_pass=true`; `all_pass=true` | `tool_integration_depth.clifford=load_bearing`; `classification=canonical`. |
| e3nn | PASS | `system_v4/probes/a2_state/sim_results/e3nn_capability_results.json` | `summary.all_pass=true`; `all_pass=true` | `tool_integration_depth.e3nn=load_bearing`; `e3nn_version=0.6.0`; `importable=true`. |
| pyg | PASS | `system_v4/probes/a2_state/sim_results/sim_capability_pyg_isolated_results.json` | equivalent `overall_pass=true`; all positive/negative/boundary `pass=true` | `tool_integration_depth.pyg=load_bearing`; `positive.pyg_available.pass=true`; `version=2.7.0`. |

## Final Item Status

| Item | Status |
|---|---|
| 1. Julia Hopf foliation fresh run | PASS |
| 2. Julia Weyl sheet pair fresh run | PASS |
| 3. JAX Hopf foliation and JAX Weyl sheet pair fresh runs | PASS |
| 4. Main reusable functions/constants inventoried for all four files | PASS |
| 5. Capability receipts exist and pass/equivalent pass for z3, cvc5, geomstats, sympy, clifford, e3nn, pyg | PASS |
