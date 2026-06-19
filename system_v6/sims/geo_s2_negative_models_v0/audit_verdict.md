# Fresh Audit Verdict: geo_s2_negative_models_v0

Date: 2026-06-10

Mode: read-only audit except this file. I did not rebuild the packet entrypoints because they rewrite result JSON timestamps; validation and recomputation below read existing sources/results only.

Inputs checked:

- Sim folder: `system_v6/sims/geo_s2_negative_models_v0/`
- Blind sheet: `/tmp/s2_blind_expected_20260610.md`
- Build spec: `system_v6/receipts/s2_build_spec_20260610.md`
- Canonical program receipt: `system_v6/receipts/geometry_sim_program_canonical_20260610.md`
- Pattern catalog: H1-H7 from `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`; E1-E6 from `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md`

## Verdict

VERDICT: EARNED.

Ceiling: this earns only a negative-model selectivity scratch diagnostic at `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `negative_model=true`. It supports wrong-connection, broken-Stokes, and naive-cover failure selectivity for S2 receipt families. It supports no positive S2 claim and no formal/canonical/bridge/axis/physics claim.

## Validator Command

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s2_negative_models_v0/results/geo_s2_negative_models_v0_envelope_results.json
```

Result: `{"ok": true, "result_json": "system_v6/sims/geo_s2_negative_models_v0/results/geo_s2_negative_models_v0_envelope_results.json"}`

## Common Adapter And Positive Control

Status: PASS.

Quoted source:

```python
COMMON_RECEIPT_KEYS = (
    "S2.A_connection_match",
    "S2.F_curvature_derivative_pair",
    "S2.H_horizontal_holonomy",
    "S2.S_stokes_strip",
    "S2.C_chern_normalization",
    "S2.T_local_metric_det",
    "S2.T_physical_area",
    "S2.G_grid_count",
    "S2.G_parity_identification",
)
```

Cites: `geo_s2_negative_models_v0_common.py:37-47`.

The adapter enforces those keys and marks the same interface as the positive control (`geo_s2_negative_models_v0_common.py:126-151`). The JAX, Julia, and PyTorch legs all build a `positive_s2_canonical_connection_quotiented_grid` model through the same common receipt shape (`geo_s2_negative_models_v0_jax.py:192-257`; PyTorch `:134-148`; Julia `:158-172`). The envelope gate `positive_control_passes_shared_adapter` is true for all three engines (`geo_s2_negative_models_v0_envelope.py:154-162`).

## N1. Wrong Connection Negative

Status: PASS.

Quoted source:

```python
def wrong_a_chi(eta: float) -> float:
    return -math.cos(2.0 * eta)

def wrong_connection_holonomy(eta: float) -> float:
    return horizontal_holonomy_from_a_chi(wrong_a_chi(eta))
```

Cites: `geo_s2_negative_models_v0_common.py:78-95`.

Predicted failures from the blind sheet for sign-flipped `A_wrong=dphi-cos(2eta)dchi`: connection match, canonical curvature match, horizontal holonomy except `eta=pi/4`, Stokes against canonical `F`, and Chern sign. Torus metric, physical area, grid count, and parity identification should pass.

Observed selectivity matches. The JAX matrix predicts and observes exactly:

```text
negative_1_wrong_connection_sign_flipped:
connection_match, curvature_derivative_pair, horizontal_holonomy_target, stokes_consistency, chern_normalization
```

Cites: `geo_s2_negative_models_v0_jax.py:531-558`; envelope gate `common_adapter_selectivity=true` at `geo_s2_negative_models_v0_envelope.py:146-153`.

Hand recompute, one failure magnitude:

```text
eta = pi/6
h_wrong = +2*pi*cos(pi/3) = +pi
h_canonical = -2*pi*cos(pi/3) = -pi
residual = 2*pi = 6.283185307179588
receipt residual = 6.283185307179588
```

The blind Chern residual is `+8*pi = 25.132741228718345`, and the receipt records `fail_magnitude = 8*pi` (`geo_s2_negative_models_v0_jax.py:319-323`).

## N2. Broken Stokes Negative

Status: PASS.

Quoted source:

```python
def wrong_sign_strip_integral(eta_i: float, eta_j: float) -> float:
    return -canonical_strip_integral(eta_i, eta_j)
```

Cites: `geo_s2_negative_models_v0_common.py:102-107`.

The broken-Stokes model preserves canonical `A` and holonomy while pairing it with sign-flipped `F`. Source receipts mark `S2.A_connection_match` and `S2.H_horizontal_holonomy` as pass, while `S2.F_curvature_derivative_pair`, `S2.S_stokes_strip`, and `S2.C_chern_normalization` fail (`geo_s2_negative_models_v0_jax.py:358-430`).

Hand recompute, Stokes magnitude:

```text
eta_i = pi/8, eta_j = pi/3, L = 2*pi
c_i = cos(pi/4) = 0.7071067811865476
c_j = cos(2*pi/3) = -0.5
blind broken-Stokes residual = 2*L*(c_i - c_j)
                              = 4*pi*(1.2071067811865475)
                              = 15.168951183496318
receipt residual = 15.168951183496318
```

Chern residual again matches the blind prediction `+8*pi`; unrelated torus/grid receipts pass.

## N3. Naive-Cover Grid Negative

Status: PASS.

Quoted source:

```python
naive_points = n * n
physical_points = n * n // 2
```

Cites: `geo_s2_negative_models_v0_jax.py:437-438`; same model in PyTorch `:206-222` and Julia `:232-248`.

The naive-cover model preserves connection, curvature, holonomy, Stokes, Chern, and local determinant. It fails physical torus area, grid distinct count, and parity-preserving identification exactly as predicted (`geo_s2_negative_models_v0_jax.py:433-515`).

Hand recompute, cover failure:

```text
eta = pi/5, N = 64
naive_area = 4*pi^2*sin(2*pi/5) = 37.54620631564544
physical_area = 2*pi^2*sin(2*pi/5) = 18.77310315782272
area residual = 18.77310315782272
naive_points = 4096
physical_points = 2048
point residual = 2048
factor error = 2
```

The result records `overcount_factor=2.0`, `fail_magnitude=2048` for grid count, and `fail_magnitude=18.77310315782272` for physical area.

## Raw-Value Proofs And Cross-Engine Agreement

Status: PASS.

Quoted source:

```python
wrong_residual = scaled(wrong_conn["S2.H_horizontal_holonomy"]["measured"]["rows"][1]["residual"])
broken_residual = scaled(broken_stokes["S2.S_stokes_strip"]["measured"]["rows"][0]["residual_against_wrong_F"])
naive_points = int(naive_cover["S2.G_grid_count"]["measured"]["naive_claimed_points"])
physical_points = int(naive_cover["S2.G_grid_count"]["measured"]["physical_points"])
```

Cites: `geo_s2_negative_models_v0_jax.py:565-571`.

Z3 and CVC5 bind measured scaled residuals/integers, then flip against positive-control zero residuals (`geo_s2_negative_models_v0_jax.py:572-623`). The envelope gate `raw_value_proofs_flip` is true (`geo_s2_negative_models_v0_envelope.py:108-121`, `:163-167`).

Cross-engine scalar agreement is exact for the main wrong-connection magnitude: `max_divergence=0.0` in the envelope divergence row. Julia and PyTorch recompute their own negative receipts and source hashes are current in the strict source-backed validator.

## H/E Pattern Catalog

H1-H7: no blocking H-pattern found. The negative models are intentionally isolated bad models, but they are run through a shared receipt adapter with a positive control in the same shape, not through unrelated fixture-only fields. There is no label echo, no weak shuffle, no `x-x` tautological erasure control, no derived-boolean SMT, no synthetic torch diagonal claim, and no Axis-4/6 boundary assertion.

E1-E6: no blocking E-pattern found for this negative suite. The sign/convention pin is present at the suite level; the proof split is honest; signs/factors are measured against blind predictions; no interval or Haar claim is made; strength labels are local to a negative scratch diagnostic and do not promote the result.

## Named Gaps

No blocking gap found for the requested N1 audit. Residual limits are ceiling limits, not open gaps: the suite is a negative selectivity packet only, and its exact-strength token dialect is local to the negative-model receipts rather than the positive packet's literal token whitelist.

