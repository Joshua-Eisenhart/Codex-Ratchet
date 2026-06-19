# Fresh Audit Verdict: geo_s7_discrete_refinement_v0

Scope: fresh read-only audit of `system_v6/sims/geo_s7_discrete_refinement_v0/` against `/tmp/s7_blind_expected_20260610.md` and `system_v6/receipts/s7_build_spec_20260610.md`. The only write in this lane is this `audit_verdict.md`.

Audit mode: source/result inspection plus independent recomputation. I did not run builder scripts because they write result JSON/CSV artifacts.

Commands/checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_exact_strength_validator.py
ok: true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json
ok: true
```

Validator status is schema/process evidence only. It is not enough for the exact blind/catalog bar.

## Binding Sources

S7 spec binding:
- Continuum targets and S2 boundary: `system_v6/receipts/s7_build_spec_20260610.md:11-18`.
- New S7 work requirements: `system_v6/receipts/s7_build_spec_20260610.md:59-66`.
- Cover/parity requirements: `system_v6/receipts/s7_build_spec_20260610.md:72-77`, `system_v6/receipts/s7_build_spec_20260610.md:120-125`.
- Holonomy route requirement: `system_v6/receipts/s7_build_spec_20260610.md:94-100`.
- Flux/Stokes requirements: `system_v6/receipts/s7_build_spec_20260610.md:102-109`.
- Rate and exact-row requirements: `system_v6/receipts/s7_build_spec_20260610.md:111-118`.
- Negative controls and cross-engine fatality: `system_v6/receipts/s7_build_spec_20260610.md:161-185`.
- Pattern attack list including PyTorch blur and SMT decoration: `system_v6/receipts/s7_build_spec_20260610.md:207-223`.
- Directive rules and ceiling surface: `system_v6/receipts/s7_build_spec_20260610.md:225-237`.

Blind ledger binding:
- Continuum targets: `/tmp/s7_blind_expected_20260610.md:21-41`.
- Cover/parity exact table: `/tmp/s7_blind_expected_20260610.md:43-78`.
- Estimator definitions and expected orders: `/tmp/s7_blind_expected_20260610.md:80-150`.
- Expected area table: `/tmp/s7_blind_expected_20260610.md:152-164`.
- Expected Wilson/overlap holonomy table: `/tmp/s7_blind_expected_20260610.md:166-178`.
- Expected midpoint and left flux tables: `/tmp/s7_blind_expected_20260610.md:180-193`.
- Required tripwires: `/tmp/s7_blind_expected_20260610.md:195-227`.

Pattern catalog binding:
- H1-H7: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md:81-205`.
- E1-E6: `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md:332-415`.
- S4-v2 conditions: `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:326-400`.
- S5-v2 conditions: `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:326-446`.
- S6-v2 conditions: `system_v6/sims/geo_s6_stacked_flows_hopf_v0/audit_verdict.md:197-305`.

## R1 - Cover Division, Odd N, Parity

Status: PASS for quotient point counts and parity preservation; GAP for the exact area/flux cover-factor tripwire as emitted.

Quoted source:

```python
def quotient_partner(n: int, a: int, b: int) -> tuple[int, int]:
    shift = n // 2
    return ((a + shift) % n, (b + shift) % n)
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:244-252`.

The emitted cover rows match the blind quotient table:

```text
N=2: chart=4, physical=2, factor=2.0, kappa={'0': 1, '1': 1}, preserved=true
N=4: chart=16, physical=8, factor=2.0, kappa={'0': 4, '1': 4}, preserved=true
N=8: chart=64, physical=32, factor=2.0, kappa={'0': 16, '1': 16}, preserved=true
N=16: chart=256, physical=128, factor=2.0, kappa={'0': 64, '1': 64}, preserved=true
N=32: chart=1024, physical=512, factor=2.0, kappa={'0': 256, '1': 256}, preserved=true
N=64: chart=4096, physical=2048, factor=2.0, kappa={'0': 1024, '1': 1024}, preserved=true
```

This matches `/tmp/s7_blind_expected_20260610.md:69-78`.

Odd N behavior is correctly blocked in the negative control:

```json
"odd_N_attempted_cover": {
  "attempted_N": [3, 5],
  "status": "blocked_unsupported_odd_N_cover",
  "forced_N_squared_over_2": false,
  "gate_pass": false
}
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:709-715`, blind rule `/tmp/s7_blind_expected_20260610.md:205-207`.

Gap R1.a: the packet does not emit the exact area/flux cover-factor tripwire cleanly. The source records:

```python
"area_normalization_ratio": (2.0 * area_good) / area_target
```

Cite: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:693-701`.

The emitted value is `1.9983883430101332`, not exact `2`, because it compares doubled discrete area to the continuum target instead of chart estimator over physical estimator. Independent recomputation shows the exact factor exists for the discrete area at `N=4, eta=pi/4`:

```text
physical area = 13.856406460551014
chart area = 27.712812921102028
chart/physical = 2.0
```

The exact factor is true but not emitted in the required tripwire form for area/flux normalization. The point-count cover passes; the normalization control is weaker than the blind tripwire.

## R2 - Convergence Orders And Continuum Targets

Status: PARTIAL. Area and midpoint flux values match the blind estimator rows. Holonomy does not match the blind Wilson/overlap table because the packet uses a different central-secant transport estimator. Rate reporting is present, but the rate gate is too weak and can pass misattribution.

Quoted source for area route:

```python
areas = [cell_area(eta, n, a, b) for a, b in reps]
total = sum(areas)
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:332-354`.

Hand recompute minimum, discrete area at `N=4, eta=pi/4`:

```text
Delta = pi/2
cell_area_chart = 1.7320508075688767
physical cells = N^2/2 = 8
A_4(pi/4) = 13.856406460551014
target = 19.739208802178716
abs_error = 5.882802341627702
```

Emitted row: `13.856406460551018`, matching the blind table `/tmp/s7_blind_expected_20260610.md:161`.

One convergence ratio:

```text
area pi/4 abs_error N=32 = 0.06424401097633492
area pi/4 abs_error N=64 = 0.015906416920234534
ratio = 4.038873826739081
rate = log2(ratio) = 2.013953077365321
```

This supports the expected second-order behavior on the high-N tail.

But the full emitted area fit includes low-N oscillatory rows and still labels every fit under `expected: O(N^-2)`. Examples:

```text
3*pi/8 observed_rate = 1.3741519282964618
5*pi/12 observed_rate = 1.2081132072144314
3*pi/8 local rate N=4->8 = -0.5377967502087814
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json:31-76`, source gate `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:813-833`.

This is not fatal for the numeric curve because the blind table itself has low-N nonmonotonicity for high eta rows, but it is a gate weakness: `P9_rate_ledger` is unconditional:

```python
"P9_rate_ledger": {
    "pass": True,
```

Cite: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:889-894`.

Quoted source for holonomy route:

```python
deriv = ((plus[0] - minus[0]) / (2.0 * delta), (plus[1] - minus[1]) / (2.0 * delta))
a_chi = (-1j * inner(psi, deriv)).real
forward = -sum(a * delta for a in a_values)
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:357-387`.

This is a genuine sampled discrete transport/connection estimator, not direct closed-form substitution. However it is not the blind Wilson/overlap estimator from `/tmp/s7_blind_expected_20260610.md:106-124`, so the blind table does not match. Independent diff for `eta=pi/6`:

```text
N=8:  emitted central-sec = -2.8284271247461907; blind Wilson = -3.7091808720064487; diff = +0.880753747260258
N=16: emitted central-sec = -3.0614674589207196; blind Wilson = -3.2675131348499042; diff = +0.20604567592918466
N=32: emitted central-sec = -3.121445152258055;  blind Wilson = -3.172166129935116;  diff = +0.05072097767706074
N=64: emitted central-sec = -3.1365484905459375; blind Wilson = -3.1491808177966436; diff = +0.012632327250706066
```

Hand recompute minimum, one discrete holonomy step at `eta=pi/6, N=8, k=0`:

```text
A_chi = 0.45015815807855314
step = -A_chi * Delta = -0.35355339059327384
8 * step = -2.8284271247461907
target h(pi/6) = -3.141592653589794
```

The central-secant route converges toward the S2 value, but the packet does not say it deviates from the blind Wilson table. This is a named blind-diff gap, not evidence of formula-copy failure.

Flux route:

```python
eta_mid = eta_i + (i + 0.5) * deta
row_value = -2.0 * math.sin(2.0 * eta_mid) * deta * dchi
total += n * row_value
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:390-411`.

For `pi/6->pi/4`, the emitted midpoint row matches the blind table `/tmp/s7_blind_expected_20260610.md:188`:

```text
N=64 flux = -3.1416014150557023
target = -3.141592653589793
abs_error = 8.761465909223887e-06
N=32->64 error ratio = 4.000023426550932
rate = 2.0000084493174715
```

Gap R2.a: the blind ledger's second wider strip `pi/6->5pi/12` is absent. The packet uses `pi/8->3*pi/8` instead:

```text
flux_pair pi/6->5pi/12 row_count = 0
flux_pair pi/8->3*pi/8 row_count = 6
```

Cites: packet row label `system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json:1705`, blind expected wider row `/tmp/s7_blind_expected_20260610.md:193`.

## R3 - Discrete Holonomy Lineage And Route

Status: PARTIAL PASS. The core holonomy path is a genuine sampled central-secant transport route and the lineage is cited. It does not match the blind Wilson/overlap estimator, and its round-trip gates are too tautological to carry much audit weight.

The S7 spec allows "Wilson/overlap product or discrete horizontal lift" (`system_v6/receipts/s7_build_spec_20260610.md:94-100`). The packet chose central-secant spinor connection and marks closed-form edge sum as support-only:

```python
"transport_route": "central-secant transported-loop connection from sampled spinors",
"closed_form_edge_sum_label": "not_used_for_estimate",
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:379-386`.

Lineage citations are present in the core source and envelope:

```python
"s2_continuum_targets": [
    "system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:17-19",
    ...
]
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:99-124`, envelope `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_envelope.py:293-300`.

Gap R3.a: the round-trip gate is weak. In the core, reverse is constructed by negating the same sampled values:

```python
reverse = -sum((-a) * delta for a in reversed(a_values))
round_trip_residual = forward + reverse
```

Cite: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:368-384`.

In the JAX and PyTorch native checks, round trip is literally self-subtraction:

```python
round_trip_residuals = estimates - estimates
round_trip = estimates - estimates
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_jax.py:96-108`, `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_pytorch.py:83-95`.

This repeats the H4-style risk: a can-fail gate is recorded, but the decisive pass condition is structurally unable to fail for many wrong estimators.

## R4 - Standard Gates, Tools, Engines, Ceiling

Status: PARTIAL. Literal ceiling tokens and validators pass. Cross-engine/process claims are stronger than the evidence.

Ceiling is preserved:

```text
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
```

Cites: envelope `system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json:30`, `system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json:1-30`; build card `system_v6/sims/geo_s7_discrete_refinement_v0/build_card.md:13-18`.

Cross-engine fatality is wired as an envelope gate:

```python
"jax_pytorch_curve_hashes_match_payload": jax_py_hash_match,
"julia_native_summary_matches_payload": julia_compare["pass"],
...
gates["cross_engine_fatality"] = all(value is True for key, value in gates.items() if key != "cross_engine_fatality")
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_envelope.py:224-244`.

Gap R4.a: JAX/PyTorch curve agreement is mostly shared-core agreement, not independent engine recomputation of every curve. Both engine results are built from `base_engine_result()`, which imports the full shared Python payload:

```python
payload = build_s7_payload()
...
"area_curve": payload["area_curve"],
"holonomy_curve": payload["holonomy_curve"],
"flux_stokes_curve": payload["flux_stokes_curve"],
```

Cite: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:957-993`.

The PyTorch native check is narrower than the role label `pytorch_graph_network_sim_builder` implies. It runs `torch.func.vmap` on a holonomy probe at `N=64`; it does not independently recompute the area and flux curves in native torch:

```python
result = base_engine_result(
    "pytorch",
    "pytorch_graph_network_sim_builder",
...
"gates": ["P6_holonomy_curve", "P11_cross_engine_fatality"],
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_pytorch.py:172-201`. This is exactly the S7 attack-surface risk `Engine-role blur` in `system_v6/receipts/s7_build_spec_20260610.md:220`.

Gap R4.b: SMT is honest only at a narrow aggregate level. The solvers bind `N=64`, `physical_point_count=2048`, and `kappa_mismatch_count=0`:

```python
"bound_raw_values": {"N": n_value, "physical_point_count": physical_value, "kappa_mismatch_count": mismatch_value},
"asserted_precomputed_boolean": False,
```

Cites: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_jax.py:112-143`, `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_pytorch.py:98-128`, Julia `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_julia.jl:188-226`.

This is better than a literal boolean, but it is still a derived aggregate, not an all-N, all-pair solver proof of `kappa(a,b)=kappa(a+N/2,b+N/2)`. The exact enumerated parity rows cover the all-N evidence; the SMT claim should be scoped to the `N=64` aggregate contradiction.

Gap R4.c: negative controls are not uniformly executed mutations through the same gate. Several are records such as "transport_route_present=false" or "row_location_tables_present=false", not reruns. Example:

```python
"formula_copy_holonomy": {
    "executed": True,
    "mutation": "set holonomy_estimate=h(eta) directly",
    "transport_route_present": False,
    "P6_gate_pass": False,
}
```

Cite: `system_v6/sims/geo_s7_discrete_refinement_v0/geo_s7_discrete_refinement_v0_core.py:749-760`. This is weaker than the S4/S5/S6-v2 executed-mutation standard in `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:342-355`, `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:412-430`, and `system_v6/sims/geo_s6_stacked_flows_hopf_v0/audit_verdict.md:251-277`.

## Pattern Catalog Adjudication

H1-H7: no H2-style label echo or H7 axis-boundary collapse was found in the core S7 arithmetic. However H4/H5/H6-style risks survive: round-trip and some mutation gates are structurally weak, SMT binds a derived aggregate, and PyTorch's role label overstates native coverage. Binding source: `system_v6/sims/axis_independence_discriminators_036/audit_verdict.md:140-191`.

E1-E6: sign and convention pinning are present, and the packet keeps exact support rows excluded from convergence claims. The blind Wilson/overlap mismatch means the holonomy table is not closed against the blind estimator; it is a different discrete estimator. Binding source: `system_v6/sims/geo_s1_exact_closure_v0/audit_verdict.md:332-415`.

S4/S5/S6-v2: literal tokens and source-backed validators pass, but executed mutation and round-trip strength fall short of the repaired S4/S5/S6 examples. Binding sources: `system_v6/sims/geo_s4_operator_stage_v0/audit_verdict.md:342-355`, `system_v6/sims/geo_s5_terrain_flows_v0/audit_verdict.md:361-430`, `system_v6/sims/geo_s6_stacked_flows_hopf_v0/audit_verdict.md:251-277`.

## Named Gaps

G1. The exact 2:1 cover factor is true for point counts and independently true for the discrete area estimator, but the emitted negative-control field reports `1.9983883430101332` because it compares to the continuum target. This fails the blind exact-factor tripwire as emitted.

G2. Holonomy uses a central-secant transport estimator. It is genuine discrete transport, but it does not match the blind Wilson/overlap table. The packet should either emit Wilson/overlap rows or explicitly diff and justify the estimator change.

G3. The blind wider flux row `pi/6->5pi/12` is missing; the packet substitutes `pi/8->3*pi/8`.

G4. `P9_rate_ledger` passes unconditionally and does not fail or caveat low-N/nonmonotone rate fits that are far from second order.

G5. Round-trip gates are tautological in JAX/PyTorch and weak in the core route.

G6. Negative controls are not uniformly actual mutation reruns through the same gate.

G7. SMT proof is an `N=64` aggregate contradiction, not a full all-N/all-pair solver proof.

G8. PyTorch native evidence is a `torch.func.vmap` holonomy probe at `N=64`; it is not full independent native PyTorch coverage for area, flux, Stokes, or graph/network geometry.

## Verdict

VERDICT: REJECT AS CLAIMED for the exact blind/catalog audit bar.

Accepted below that bar:
- Useful scratch-diagnostic S7 finite-grid packet.
- Correct even-N quotient point counts and parity preservation.
- Area chord-mesh rows match the blind area table.
- Midpoint flux rows match the blind midpoint table for emitted strips.
- Central-secant holonomy is a genuine sampled discrete estimator converging toward the S2 target.
- Local validators pass.

Rejected as claimed:
- Exact blind holonomy table match.
- Full blind convergence-table coverage because `pi/6->5pi/12` is absent.
- Exact emitted 2:1 area/flux cover-factor tripwire.
- Strong executed-mutation/round-trip/cross-engine/PyTorch/SMT claims.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No canonical discretization, manifold admission, Axis closure, bridge/physics/runtime closure, or completed constraint-manifold geometry is earned.

## 2026-06-10 v2 Fresh Re-Audit: Three v1 Fail Conditions

Scope: fresh read-only re-audit of the v2 result JSON against the three v1 fail conditions and `/tmp/s7_blind_expected_20260610.md`. Only this section was appended.

Important byte-stability caveat: the directory `system_v6/sims/geo_s7_discrete_refinement_v0/` is untracked in git, so there is no repository baseline for a full byte-for-byte v1/v2 diff. I checked untouched values against the existing v1 audit text where exact values were named; those sampled values are stable.

### V1 - Discrete-vs-discrete cover ratio exactly 2

Status: PASS.

Recomputed from emitted v2 sums at `N=64`:

```text
area naive chart grid sum / cover-corrected grid sum
= 39.44660477051696 / 19.72330238525848
= 2.0

flux naive chart grid sum / cover-corrected grid sum
= -6.283202830111405 / -3.1416014150557023
= 2.0
```

The emitted exact integer ratio also records `numerator=4096`, `denominator=2048`, `reduced=2/1` for both area and flux. This closes the prior v1 failure where the emitted row compared doubled discrete area to the continuum target and produced `1.9983883430101332` instead of the discrete-vs-discrete cover ratio.

### V2 - Wilson/overlap holonomy rows and estimator diff

Status: PASS.

The v2 result emits Wilson/overlap rows as the primary holonomy estimator:

```text
primary_estimator = wilson_overlap_product
blind_table_comparison_estimator = wilson_overlap_product
Wilson/overlap row count = 42 = 7 eta shells * 6 N values
```

Independent recomputation used:

```text
h_N(eta) = -N * atan2(cos(2*eta) * sin(2*pi/N), cos(2*pi/N))
```

All 42 emitted Wilson/overlap values matched the blind formula to `1e-12`.

Sample rows:

```text
eta=pi/6, N=8:
emitted Wilson = -3.7091808720064487
blind recompute = -3.7091808720064487
central-secant comparison = -2.8284271247461907
emitted estimator diff = 0.880753747260258

eta=pi/6, N=64:
emitted Wilson = -3.1491808177966436
blind recompute = -3.1491808177966436
central-secant comparison = -3.1365484905459375
emitted estimator diff = 0.012632327250706066
```

Estimator diff honesty check: for all Wilson rows with a central-secant comparison, `estimator_abs_diff == abs(wilson_overlap_product - central_secant_estimate)` to `1e-12`. This closes the v1 failure where only the central-secant estimator was emitted and the blind Wilson table did not match.

### V3 - `pi/6 -> 5pi/12` flux row

Status: PASS.

The v2 result emits all six `pi/6->5pi/12` midpoint flux rows.

Independent recomputation used:

```text
Phi_mid_N = 2*pi * sum_{m=0}^{N-1} [-2*sin(2*(eta_i + (m+1/2)*delta_eta))*delta_eta]
eta_i = pi/6
eta_j = 5*pi/12
delta_eta = (eta_j - eta_i)/N
```

All six emitted rows matched the recomputed midpoint formula to `1e-12`.

Sample rows:

```text
N=2:
emitted flux = -8.807626093104854
target Phi = -8.582990746292447
abs_error = 0.22463534681240738

N=64:
emitted flux = -8.58320618058713
target Phi = -8.582990746292447
abs_error = 0.000215434294682737
```

This closes the v1 failure where the wider blind strip was missing.

### Untouched-value stability spot check

Full byte-stability is not provable from git because this sim directory is untracked. Spot checks against exact values printed in the existing v1 audit text are stable:

```text
area pi/4 N=4 = 13.856406460551018
area pi/4 N=64 = 19.72330238525848
flux pi/6->pi/4 N=64 = -3.1416014150557023
central-secant holonomy pi/6 N=8 = -2.8284271247461907
```

### Final line

EARNED

## 2026-06-10 S7 Tooling Remediation Note

Status: PASS as a remediated scratch diagnostic. Claim ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

Route table:

| Route | Proof surface | Output-only artifacts | Status |
|---|---|---|---|
| Quotient grid tables | Z3/cvc5/Z3.jl exact integer cover/parity checks plus emitted quotient tables | none | pass |
| Topology mesh certificate | TopoNetX `SimplicialComplex` incidence plus GUDHI `SimplexTree` Betti readout on the same quotient triangulation; only `N={8,16,32,64}` carry the mesh-complex certificate | `N=2` and `N=4` degenerate refinement controls | pass |
| Interval/error certificates | Julia `IntervalArithmetic` in `@codex-ratchet-tensorkit-v1.12`, from interval-valued eta/N inputs through area, Wilson holonomy, midpoint flux, and Stokes residual bounds | `results/convergence_curves/*.csv` | pass |
| Claim ceiling | Literal source/result ceiling fields | none | pass |

Byte-stability: compared the fresh envelope against `HEAD` for the claim string, classification, promotion/formal-admission ceilings, `pin_sha256`, `convention_pin`, `summary.N_values`, `summary.eta_count`, `summary.strip_pair_count`, and existing `curve_hashes` for parity cover, presentations, negative controls, area, holonomy, and flux/Stokes. All compared values were byte-stable.

Fresh rerun and validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 geo_s7_discrete_refinement_v0_jax.py -> ok:true
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 geo_s7_discrete_refinement_v0_pytorch.py -> ok:true
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier geo_s7_discrete_refinement_v0_julia.jl -> ok:true
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=@codex-ratchet-tensorkit-v1.12 geo_s7_discrete_refinement_v0_interval.jl -> ok:true
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 geo_s7_discrete_refinement_v0_envelope.py -> ok:true
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch .../geo_s7_discrete_refinement_v0_envelope_results.json -> ok:true
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed .../geo_s7_discrete_refinement_v0_envelope_results.json -> ok:true
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed .../geo_s7_discrete_refinement_v0_envelope_results.json -> ok:true
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 geo_s7_discrete_refinement_v0_exact_strength_validator.py -> ok:true
```

Capability gate: `verify_load_bearing_has_capability_probe.py --sim geo_s7_discrete_refinement_v0_jax.py` returned no violations for `z3`, `cvc5`, `toponetx`, and `gudhi`; the PyTorch source gate returned no violations for `z3` and `cvc5`. The interval route cites the existing Julia capability receipt `system_v6/probes/julia/results/intervalarithmetic_capability_results.json` and is explicitly scoped to the optional interval project, not strict-carrier evidence.

## 2026-06-10 Cross-Engine Fatality Remediation Note

Status: PASS with unchanged claim ceiling. The envelope now emits `cross_engine_fatality_receipt`, an independent fatal-signature comparison over proof signatures, curve hashes, negative controls, transported-loop estimates, Julia cover rows, and no-peer-read state. The previous conjunction-style fatal gate was replaced by this signature comparison; byte-stable result values and strict validator outcome remain green.

Fresh check:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json -> ok:true
```
