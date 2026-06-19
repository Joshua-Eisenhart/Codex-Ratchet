# Fresh Audit: geo_s1_spinor_hopf_free_v0

Audit date: 2026-06-10

VERDICT: GENUINE-WITH-CAVEATS.

The S1 packet is not an R3-style decorative fixture: the Hopf map, density quotient, Gauss linking integral, Haar pushforward check, solver controls, and three-engine envelope are real source-level computations. The core ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

The caveats are load-bearing:

1. The double-cover receipt is endpoint-only; it does not emit intermediate path samples.
2. Several "convergence rows" are flat or machine-epsilon rows, not decreasing ladders.
3. The envelope tripwire for S3-vs-Fubini-Study separation is `false`, even though the source labels and computes the two distances separately.
4. PyTorch records `keystone_identity_max_deviation: 0.0` as a shared scalar without computing G6 in the PyTorch leg; the actual keystone gate is JAX/Julia, so this is a reporting caveat rather than a failed keystone gate.

## Evidence Boundary

Files read:

- `system_v6/sims/geo_s1_spinor_hopf_free_v0/build_card.md`
- `system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_jax.py`
- `system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_julia.jl`
- `system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_pytorch.py`
- `system_v6/sims/geo_s1_spinor_hopf_free_v0/geo_s1_spinor_hopf_free_v0_envelope.py`
- `system_v6/sims/geo_s1_spinor_hopf_free_v0/results/*.json`
- `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md`

I did not rerun the leg or envelope scripts because their `main()` functions write result JSON, and the lane was read-only except this file. I did run read-only validation and source-import recomputations.

Fresh checks:

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/geo_s1_spinor_hopf_free_v0/results/geo_s1_spinor_hopf_free_v0_envelope_results.json
-> {"ok": true, "result_json": "...geo_s1_spinor_hopf_free_v0_envelope_results.json"}
```

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_spinor_hopf_free_v0/results/geo_s1_spinor_hopf_free_v0_envelope_results.json
-> {"ok": true, "result_json": "...geo_s1_spinor_hopf_free_v0_envelope_results.json"}
```

## Hand Recomputations

One Hopf image by hand:

- Chosen chart: `eta=pi/6`, `phi=0.2`, `chi=0.3`.
- Hand formula: `(sin(2eta) cos(2chi), sin(2eta) sin(2chi), cos(2eta)) = [0.7147616091598321, 0.48899472601577965, 0.5000000000000001]`.
- Source `hopf(spinor_from_chart(...))`: `[0.714761609159832, 0.4889947260157796, 0.5000000000000002]`.
- Max absolute difference: `1.1102230246251565e-16`.

One fiber point check:

- Base representative: `psi0=(1/sqrt(2), 1/sqrt(2))`, Hopf image `[0.9999999999999998, 0.0, 0.0]`.
- Fiber point: `exp(i*1.23) psi0`, Hopf image `[0.9999999999999999, -3.1715551276224362e-21, 0.0]`.
- Max absolute fiber-image difference: `1.1102230246251565e-16`.

One linking integrand sample from the source finite-difference rule:

- `n=64`, sample pair `(i=3, j=11)`.
- Numerator: `0.14149327497565373`.
- Denominator: `4.33059154275659`.
- Kernel: `0.03267296709437246`.
- Cell contribution after `dt*dt/(4pi)`: `2.505985190299355e-05`.

One convergence ratio:

- Linking errors: `0.003861839468583539`, `0.0009663589815541718`, `0.00024164590288522358`, `6.041498498032816e-05`.
- Error ratios under resolution doubling: `3.9962783420014745`, `3.999070416737712`, `3.9997676563837`.

One keystone recomputation:

- Same chart point as above.
- Hopf route: `[0.7147616091598321, 0.48899472601577965, 0.4999999999999999]`.
- Density route: `[0.7147616091598321, 0.48899472601577965, 0.5000000000000001]`.
- Max absolute difference: `2.220446049250313e-16`.

## A1. Linking Integral Honesty

Decision: PASS.

Quoted source:

```python
def gauss_linking_integral(curve_a: torch.Tensor, curve_b: torch.Tensor) -> float:
    n = curve_a.shape[0]
    dt = 2.0 * math.pi / n
    da = (torch.roll(curve_a, -1, dims=0) - torch.roll(curve_a, 1, dims=0)) / (2.0 * dt)
    db = (torch.roll(curve_b, -1, dims=0) - torch.roll(curve_b, 1, dims=0)) / (2.0 * dt)
    diff = curve_a[:, None, :] - curve_b[None, :, :]
    cross = torch.cross(da[:, None, :].expand(n, n, 3), db[None, :, :].expand(n, n, 3), dim=2)
    numerator = torch.sum(diff * cross, dim=2)
    denominator = torch.linalg.norm(diff, dim=2) ** 3
    return py_float(torch.sum(numerator / denominator) * dt * dt / (4.0 * math.pi))
```

Cites: `geo_s1_spinor_hopf_free_v0_pytorch.py:170-179`.

The source constructs two full curves, applies central finite-difference tangents, evaluates the double sum over pairwise curve samples, and multiplies by `dt*dt/(4pi)`. The convergence ladder is emitted at `64,128,256,512` samples per fiber (`geo_s1_spinor_hopf_free_v0_pytorch.py:204-216`) and the result JSON records `0.9961381605 -> 0.9990336410 -> 0.9997583541 -> 0.9999395850` (`geo_s1_spinor_hopf_free_v0_pytorch_results.json:33-57`).

Wrong-linking control is honestly labeled:

```python
same_curve = stereographic_to_r3(fiber_curve_s3(p_north, 256))
same_shifted = stereographic_to_r3(fiber_curve_s3(p_north, 256, phase_offset=0.37))
same_control = regularized_same_fiber_control(same_curve, same_shifted)
...
"semantics": "same Hopf base point gives the same fiber; ordinary linking is undefined, so this regularized duplicate-curve computation is a can-fail control and must not equal 1",
```

Cites: `geo_s1_spinor_hopf_free_v0_pytorch.py:218-220`, `geo_s1_spinor_hopf_free_v0_pytorch.py:275-279`; result value `0.0` at `geo_s1_spinor_hopf_free_v0_pytorch_results.json:61-66`.

This is not misrepresented as true self-linking. It is a regularized duplicate-curve can-fail control, and it is labeled as such.

## A2. Keystone 0.0

Decision: PASS WITH REPORTING CAVEAT.

Quoted source:

```python
def hopf(psi: jax.Array) -> jax.Array:
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    z12 = z1 * jnp.conj(z2)
    return jnp.stack(
        [
            2.0 * jnp.real(z12),
            2.0 * jnp.imag(z12),
            jnp.abs(z1) ** 2 - jnp.abs(z2) ** 2,
        ],
        axis=-1,
    )

def density(psi: jax.Array) -> jax.Array:
    return psi[..., :, None] * jnp.conj(psi[..., None, :])

def bloch_from_density(rho: jax.Array) -> jax.Array:
    return jnp.real(jnp.einsum("...ab,iba->...i", rho, BLOCH_BASIS))
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:135-168`.

JAX computes the Hopf route and the density/Bloch route separately:

```python
h = hopf(psi)
rho = density(psi)
bloch = bloch_from_density(rho)
...
"bloch_equals_hopf_max_deviation": as_float(jnp.max(jnp.abs(bloch - h))),
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:354-392`.

Julia does the same two-path check:

```julia
function hopf(psi::Vector{ComplexF64})
    z1, z2 = psi[1], psi[2]
    z12 = z1 * conj(z2)
    Float64[
        2.0 * real(z12),
        2.0 * imag(z12),
        abs2(z1) - abs2(z2),
    ]
end

function density(psi::Vector{ComplexF64})
    psi * psi'
end

function bloch_from_density(rho::Matrix{ComplexF64})
    Float64[real(tr(rho * basis)) for basis in BLOCH_BASIS]
end
```

Cites: `geo_s1_spinor_hopf_free_v0_julia.jl:88-103`; the comparison is at `geo_s1_spinor_hopf_free_v0_julia.jl:226-230`.

The exact Julia `0.0` is not evidence of computing the same expression twice; it is a density-matrix route compared to a quadratic Hopf route on deterministic chart samples. The JAX dense route reports `5.551115123125783e-16` (`geo_s1_spinor_hopf_free_v0_jax_results.json:431-446`), matching ordinary float roundoff.

Caveat: PyTorch hardcodes a keystone scalar:

```python
"keystone_identity_max_deviation": 0.0,
```

Cite: `geo_s1_spinor_hopf_free_v0_pytorch.py:332-336`.

That PyTorch scalar is not used as the envelope keystone gate, and PyTorch is not recorded as a G6 receipt. It should be removed or labeled `not_scoped` in a cleanup pass.

## A3. Double-Cover Path

Decision: FAIL AS REQUESTED.

Quoted source:

```python
rot2 = unitary_from_axis_angle(jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64), 2.0 * math.pi) @ base_psi
rot4 = unitary_from_axis_angle(jnp.asarray([0.0, 0.0, 1.0], dtype=jnp.float64), 4.0 * math.pi) @ base_psi
double_cover = {
    "rotation_axis": [0.0, 0.0, 1.0],
    "psi_2pi_plus_initial_norm": as_float(jnp.linalg.norm(rot2 + base_psi)),
    "psi_2pi_minus_initial_norm": as_float(jnp.linalg.norm(rot2 - base_psi)),
    "rho_2pi_return_deviation": as_float(jnp.max(jnp.abs(density(rot2) - rho0_single))),
    "psi_4pi_minus_initial_norm": as_float(jnp.linalg.norm(rot4 - base_psi)),
}
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:430-440`.

Julia is also endpoint-only:

```julia
rot2 = unitary_from_axis_angle([0.0, 0.0, 1.0], 2.0 * pi) * base_psi
rot4 = unitary_from_axis_angle([0.0, 0.0, 1.0], 4.0 * pi) * base_psi
double_cover = Dict{String,Any}(
    "psi_2pi_plus_initial_norm" => norm(rot2 .+ base_psi),
    "rho_2pi_return_deviation" => maximum(abs.(density(rot2) .- rho0)),
    "psi_4pi_minus_initial_norm" => norm(rot4 .- base_psi),
)
```

Cites: `geo_s1_spinor_hopf_free_v0_julia.jl:212-220`.

The endpoint values are correct (`psi_2pi_plus_initial_norm ~= 1.7e-16`, `psi_4pi_minus_initial_norm ~= 1.8e-16` at `geo_s1_spinor_hopf_free_v0_envelope_results.json:73-84`), but the requested audit criterion was stronger: intermediate samples emitted along a continuous path. They are not emitted. My recomputed intermediate samples show the path exists mathematically, but that is not a packet receipt.

Required fix: emit a `double_cover_path_rows` receipt with sampled angles from `0` to `4pi`, spinor distance to `psi0`, spinor distance to `-psi0`, and density deviation.

## A4. Haar Honesty

Decision: PASS WITH LIMITED UNIFORMITY RECEIPT.

Quoted source:

```python
def normalized_complex_gaussian(n: int, seed: int) -> jax.Array:
    key = jax.random.PRNGKey(seed)
    raw = jax.random.normal(key, (n, 2, 2), dtype=jnp.float64)
    psi = raw[:, :, 0] + 1j * raw[:, :, 1]
    return psi / jnp.linalg.norm(psi, axis=1, keepdims=True)
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:128-132`.

The pushforward uniformity check is genuinely computed:

```python
def uniformity_receipt(points: jax.Array, bins: int = 20) -> dict[str, Any]:
    z = points[:, 2]
    azimuth = jnp.arctan2(points[:, 1], points[:, 0])
    z_counts = jnp.histogram(z, bins=bins, range=(-1.0, 1.0))[0]
    azimuth_counts = jnp.histogram(azimuth, bins=bins, range=(-math.pi, math.pi))[0]
    expected = points.shape[0] / bins
    z_chi_square = jnp.sum((z_counts - expected) ** 2 / expected)
    azimuth_chi_square = jnp.sum((azimuth_counts - expected) ** 2 / expected)
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:298-305`; pass threshold and labels at `geo_s1_spinor_hopf_free_v0_jax.py:306-313`.

Clustered control is real:

```python
clustered_eta = 0.08 * jax.random.uniform(jax.random.PRNGKey(55), (10_000,), dtype=jnp.float64)
clustered_phi = 2.0 * math.pi * jax.random.uniform(jax.random.PRNGKey(56), (10_000,), dtype=jnp.float64)
clustered_chi = 2.0 * math.pi * jax.random.uniform(jax.random.PRNGKey(57), (10_000,), dtype=jnp.float64)
non_haar_uniformity = uniformity_receipt(hopf(spinor_from_chart(clustered_eta, clustered_phi, clustered_chi)))
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:446-449`.

The receipt reports Haar pushforward pass at `N=100000` with `z` chi-square `15.8796`, azimuth chi-square `13.6076`, and clustered control failure with `z` chi-square `190000.0` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:130-145`, `geo_s1_spinor_hopf_free_v0_envelope_results.json:94-109`).

Caveat: the uniformity check is a pair of marginal histograms (`z`, azimuth), not a joint 2D independence test. That is enough to show a real computed receipt and catch the provided clustered control, but it is not a full distributional proof.

## A5. Convergence Rows

Decision: PARTIAL FAIL.

Quoted source:

```python
convergence_rows: dict[str, list[dict[str, Any]]] = {
    "G1_spinor_norm": [],
    "G2_s3_volume": [],
    "G4_hopf_unit_sphere_uniformity": [],
    "G6_density_quotient": [],
    "G7_s2_area_and_commuting_square": [],
}
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:347-352`.

Real decreasing ladders exist for S3 volume, S2 area, and Gauss linking:

- S3 volume error decreases `8.117e-6 -> 8.117e-8 -> 8.117e-10` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:788-809`).
- S2 area error decreases `5.167e-6 -> 5.167e-8 -> 5.167e-10` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:890-911`).
- Gauss linking error decreases `3.861e-3 -> 9.663e-4 -> 2.416e-4 -> 6.041e-5` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:963-987`).

But the build card required every invariant to have a resolution ladder with decreasing error. Several rows are flat or drift upward at machine epsilon:

- G1 spinor norm is flat: `6.661338147750939e-16` at all three N values (`geo_s1_spinor_hopf_free_v0_envelope_results.json:774-787`).
- G4 Hopf unit-sphere deviation rises: `8.881e-16 -> 1.332e-15 -> 1.554e-15` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:811-872`).
- G6 Bloch/Hopf deviation is flat then rises: `4.440e-16 -> 4.440e-16 -> 5.551e-16` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:873-889`).
- PyTorch G7 commuting-square max deviation rises: `6.261e-16 -> 6.777e-16 -> 7.850e-16` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:989-1001`).

This does not make the core identities fake; it means those rows are residual rows, not convergence ladders. The audit criterion explicitly says flat/diverging rows are findings, so this check cannot pass cleanly.

## A6. Distance Conflation Tripwire

Decision: SOURCE PASS, ENVELOPE CAVEAT.

Quoted source:

```python
complex_inner = jnp.sum(jnp.conj(geodesic_a) * geodesic_b, axis=1)
real_inner = jnp.real(complex_inner)
s3_distance = jnp.arccos(jnp.clip(real_inner, -1.0, 1.0))
fs_distance = jnp.arccos(jnp.clip(jnp.abs(complex_inner), 0.0, 1.0))
phase_alpha = 0.7
phase_s3 = jnp.arccos(jnp.real(jnp.vdot(psi_max[0], jnp.exp(1j * phase_alpha) * psi_max[0])))
phase_fs = jnp.arccos(jnp.abs(jnp.vdot(psi_max[0], jnp.exp(1j * phase_alpha) * psi_max[0])))
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:412-420`.

The source labels both distances correctly:

```python
"s3_distance_label": "arccos(Re <psi1,psi2>) using R4 real inner product",
"fubini_study_distance_label": "arccos(|<psi1,psi2>|) on the base quotient",
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:539-540`.

The result also records separated values for a phase-shift tripwire: S3 distance `0.7`, FS distance `1.4901161193847656e-08` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:40-45`).

Caveat: because the code requires `phase_fs <= TOL` with `TOL=1e-8`, the envelope records `s3_vs_fubini_study_distance_separated: false` (`geo_s1_spinor_hopf_free_v0_envelope_results.json:1302-1307`). This is a threshold/reporting failure, not source-level conflation. The fix is to clamp the phase FS value more robustly or use a looser tripwire tolerance for the known zero.

## A7. Standard: SMT, Isolation, Cross-Leg Independence, NumPy Leakage, Ceiling

Decision: PASS WITH MINOR CAVEATS.

Raw-value SMT is not the R3 derived-boolean failure mode. The proof functions bind integer-scaled raw computed values:

```python
def z3_exists_outside_scaled(values: list[int], target: int, tol: int) -> str:
    solver = z3.Solver()
    terms = [z3.Or(z3.IntVal(v) > target + tol, z3.IntVal(v) < target - tol) for v in values]
    solver.add(z3.Or(terms) if terms else z3.BoolVal(False))
    return str(solver.check())
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:269-273`; cvc5 mirror at `geo_s1_spinor_hopf_free_v0_jax.py:276-295`.

The bound values are computed from raw residuals:

```python
sphere_scaled = [int(round(float(v) * scale)) for v in jax.device_get(hopf_norm_sq_max[:4096])]
sphere_scrambled = [int(round(float(v) * scale)) for v in jax.device_get(jnp.sum(scrambled_hopf(psi_max[:4096]) ** 2, axis=1))]
commute_scaled = [int(round(float(v) * scale)) for v in jax.device_get(commuting_deviations)]
wrong_commute_scaled = [int(round(float(v) * scale)) for v in jax.device_get(wrong_commuting_deviations)]
```

Cites: `geo_s1_spinor_hopf_free_v0_jax.py:501-505`.

The controls flip: P1 and P2 are `unsat`, while scrambled Hopf and wrong rotation controls are `sat` (`geo_s1_spinor_hopf_free_v0_jax_results.json:485-520`).

Fixture isolation: no R3-style family-keyed fixture matrix was found. The geometric objects are computed directly from spinors, densities, SU(2) actions, and curve samples. The envelope reads engine result JSONs, but the engine legs record `reads_peer_result=false` and the envelope records independent engine lanes (`geo_s1_spinor_hopf_free_v0_envelope.py:66-83`, `geo_s1_spinor_hopf_free_v0_envelope.py:200-204`).

NumPy leakage: source search found no `np.asarray`, `.numpy()`, CSV, pickle, or hidden host-copy bridge on the claim path. `jax.numpy` is declared supportive, while `jax`, `z3`, and `cvc5` are load-bearing (`geo_s1_spinor_hopf_free_v0_jax.py:48-76`). The envelope records forbidden exchange as absent/no tensor exchange (`geo_s1_spinor_hopf_free_v0_envelope.py:218-224`).

Ceiling is correct:

```python
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
```

Cites: `geo_s1_spinor_hopf_free_v0_envelope.py:23-25`; payload restates this at `geo_s1_spinor_hopf_free_v0_envelope.py:189-191`.

Caveats:

- P2 binds four maximum commuting-square deviations, not every sampled pointwise deviation. This is raw-value SMT, but it is a max-residual proof fixture, not a formal continuous proof.
- PyTorch's `torch.func` role is real for the batched commuting-square check (`geo_s1_spinor_hopf_free_v0_pytorch.py:229-258`), but PyTorch does not independently cover every G item. The envelope admits this: only G5 and G7 have PyTorch receipts (`geo_s1_spinor_hopf_free_v0_envelope_results.json:124-134`).

## Named Gaps

1. Add emitted double-cover path rows. Current packet only records endpoint checks.
2. Separate "exact residual rows" from true convergence ladders. Do not call flat machine-epsilon rows decreasing convergence.
3. Fix the S3/FS tripwire threshold so the envelope does not report `s3_vs_fubini_study_distance_separated=false` when the source did separate them.
4. Remove or relabel PyTorch's hardcoded `keystone_identity_max_deviation: 0.0`; PyTorch is not a G6 lane here.
5. Upgrade the Haar uniformity receipt from marginal `z`/azimuth chi-square checks to a joint or rotation-invariant statistic if this is later used beyond scratch diagnostic status.
6. If P2 is used later as proof-like evidence, bind more pointwise commuting-square residuals or an exact finite fixture, not only four max residuals.

## Final Ceiling

Strongest honest status: executable three-engine S1 geometry scratch diagnostic; strict source-backed validator passes; Hopf/linking/density quotient core is genuine; no formal admission, no manifold/axis/physics claim, no bridge claim, no Bloch-ball or torus content.

Do not cite this packet as canonical or formally admitted. It is genuine foundation evidence with the caveats above.

## Post-Hardening Re-Audit Addendum — 2026-06-10

Scope: focused read-only re-audit of the prior §Named Gaps after hardening. I did not rebuild or harden this packet; I inspected source/result state and reran the validators.

Validator reruns:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_spinor_hopf_free_v0/results/geo_s1_spinor_hopf_free_v0_envelope_results.json` returned `{"ok": true}`.
- Extra strict check also returned `{"ok": true}` with `--require-pytorch --strict-source-backed`.

Named-gap closure check:

1. Double-cover path rows are now emitted. JAX and Julia each expose 9 `double_cover_path_rows` with continuous overlap sequences from initial return through sign flip and 4π return.
2. Exact algebra rows are separated from convergence ladders. `G6_density_quotient` is under `exact_by_algebra_rows` for JAX/Julia, and PyTorch `G7_commuting_square` rows are exact algebra rows; no flat G6 residual row is labeled as a convergence ladder row.
3. The S3/FS tripwire is fixed. The source records `s3_distance: 0.7`, `fubini_study_distance: 1.4901161193847656e-08`, threshold `1e-07`, and `conflation_detectable: true`; the envelope now reports `s3_vs_fubini_study_distance_separated: true`.
4. The PyTorch hardcoded density-keystone row is removed/relabelled. PyTorch shared scalars now carry `keystone_identity_status: not_scoped_pytorch_not_G6_lane`; the PyTorch result states `pytorch_role: fiber-linking Gauss integral and torch-native S2 commuting-square check; not a G6 density-keystone lane`.
5. Haar receipt is upgraded but still scratch-only. JAX keeps marginal z/azimuth chi-square and adds `rotation_invariant_second_moment_eigenvalues` with max deviation `0.0022780269749310134`; the note still says stronger joint tests are required beyond scratch.
6. P2 limitation note is present. The P2 proof note says the binding covers four max residuals and proof-like use requires pointwise binding over the full sampled action.

Byte-stable fields checked:

- JAX keystone `5.551115123125783e-16`; Julia keystone `0.0`.
- PyTorch Gauss linking `0.9999395850150197`.
- JAX S3 volume final abs error `8.117417849007325e-10`; JAX S2 area final abs error `5.167724026478027e-10`.
- Julia commuting square `4.996003610813204e-16`; JAX commuting square `1.0429598422709816e-15`; PyTorch commuting square `7.850462293418876e-16`.
- Solver verdicts remain `P1_hopf_unit_sphere=unsat`, `P1_scrambled_control=sat`, `P2_commuting_square=unsat`, `P2_wrong_rotation_control=sat` for both z3 and cvc5; Julia Z3 remains `unsat`.

Current ceiling: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No canonical, formal-admission, manifold/axis/physics, bridge, Bloch-ball, torus, or replacement claim is admitted. Prior §Named Gaps are historically preserved above, but no stale open-gap surface remains for the six named hardening items checked here.

Final line: sustained.

## 2026-06-10 Toolset-Coverage Addendum

Manifolds.jl is now load-bearing for the Julia S3/S2 metric side of this packet. The Julia leg imports `Manifolds` in the strict carrier project and gates `G2_s3_metric_volume` plus `G7_s2_base` through `Manifolds.distance`, `Manifolds.shortest_geodesic`, `Manifolds.log`/`exp`, and `Manifolds.manifold_volume` on `Sphere(3)` and `Sphere(2)`.

Hand midpoint metric/area rows are preserved as mirror convergence rows only. Claim ceilings and scalar pins stay at `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

Fresh checks: `sim_manifolds_capability.py` wrote `manifolds_capability_results.json` with `summary.all_pass=true`; the Julia leg and envelope reran with `ok:true`; `validate_three_engine_sim_result.py --strict-source-backed` returned `ok:true`; the per-file load-bearing capability gate returned no violations for `Manifolds` and `Z3`.
