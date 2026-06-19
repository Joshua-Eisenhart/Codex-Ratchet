# S3 build spec - density/observable geometry stage (2026-06-10)

PROVENANCE: read-lane preparation from `system_v6/receipts/geometry_sim_program_canonical_20260610.md`, committed `bloch_root_admissibility_discriminator_v0`, committed `geo_s1_exact_closure_v0`, and committed `geo_s1_*qubit*` packets. This is a build spec only. No S3 build, result JSON, source packet, queue mutation, or promotion is implied.

Ceiling for the future S3 packet: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## A. Adjudication against committed packets

Canonical S3 is density/observable geometry. Some committed packets already compute S3-adjacent facts, but they are not a dense one-qubit S3 free-mode packet.

| S3 item | Status | Existing evidence / boundary |
| --- | --- | --- |
| Pure-state density quotient `psi -> rho -> Bloch_pinned(rho)` | already-computed | `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json` computes `rho = psi * psi^dagger`, the pinned Pauli basis, and `Bloch_pinned(rho) = (x,y,z)` with explicit `sigma_y` convention. |
| Phase erasure under `rho = psi psi^dagger` | already-computed | `system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json` and `system_v6/sims/geo_s1_two_qubit_boundary_exact_v0/results/geo_s1_two_qubit_boundary_exact_v0_jax_results.json` compute phase-erasure identities. |
| F01 finite quotient refinement toward `S^2` | already-computed | `system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` T1 computes finite quotient cardinalities and a measured Hausdorff refinement ladder, with a non-refining control. |
| N01 ball-vs-simplex reconstruction | already-computed | `system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json` T2 computes commuting `sigma_z` probes as affine dimension `1` and full Pauli probes as affine dimension `3` solid Bloch ball. |
| Dense Bloch ball fields: eigenvalues, purity, entropy over all `||r|| <= 1` | genuinely-new | Existing packets compute pure boundary quotient, finite reconstruction dimension, and multi-qubit selected reductions. No committed packet emits the full one-qubit field table/formulas over the ball. |
| Expectation fields `Tr(O rho) = a0 + a.r` and plane level sets for arbitrary Hermitian one-qubit `O` | genuinely-new | `geo_s1_exact_closure_v0` computes Pauli component traces for the pinned basis, but not arbitrary observable fields or plane-level-set receipts over `B^3`. |
| Born fields `p_+/- = (1 +/- n.r)/2` | genuinely-new | `bloch_root_admissibility_discriminator_v0` uses binned spin directions for quotient reconstruction, but does not emit the exact Born probability field with normalization, bounds, and boundary controls. |
| Measurement updates | genuinely-new | The committed S1/qubit packets do not build projective selective/nonselective one-qubit update maps as S3 density geometry. |
| Probe-equivalence quotient as computed map | genuinely-new, reusing prior evidence | `bloch_root_admissibility_discriminator_v0` proves finite quotient refinement and ball-vs-simplex dimensions. S3 still needs the explicit map `Q_N(r)` and equivalence kernel rows for named probe families. |
| Trace distance and fidelity fields | genuinely-new | No committed packet emits trace-distance or fidelity formulas over two arbitrary Bloch vectors with convention pins and mixed-state controls. |
| CPTP contraction receipts | genuinely-new, S3-limited | No committed packet emits pairwise trace-distance/fidelity contraction checks for named one-qubit CPTP maps. Keep this to contraction; do not claim channel ellipsoid geometry here. |
| Channel ellipsoids `r -> M r + c` as image geometry | out-of-scope for this S3 spec | Canonical program puts ellipsoid images in S4 operators. Do not build this in the S3 packet except for minimal affine-map metadata needed to test contraction. |
| Fixed points and basins | out-of-scope for this S3 spec | Canonical program puts fixed points/basins in S5 terrain generators. Do not build this in the S3 packet. |
| Multi-qubit density dimensions and named entropy controls | already-computed but not S3 substitute | `system_v6/sims/geo_s1_two_qubit_boundary_exact_v0/`, `geo_s1_three_qubit_floor_exact_v0/`, `geo_s1_four_qubit_support_exact_v0/`, and `geo_s1_five_qubit_safety_margin_exact_v0/` compute `D(C^(2^n))` dimensions, phase quotients, and selected named-state density/entropy rows. They do not replace the one-qubit dense S3 field packet. |

The bounded build below therefore includes only the genuinely-new S3 items.

## B. Positive S3 packet spec

### B0. Scope and objects

Build one bounded S3 free-mode packet, provisionally named `geo_s3_density_observable_geometry_v0`, for one-qubit density/observable geometry over the pinned S1 Bloch convention:

- `rho(r) = (I + r_x sigma_x + r_y (-sigma_y_standard) + r_z sigma_z) / 2`;
- Bloch domain `B^3 = {r in R^3 : ||r|| <= 1}`;
- arbitrary Hermitian one-qubit observable `O = a0 I + a_x sigma_x + a_y (-sigma_y_standard) + a_z sigma_z`;
- projective measurement directions `n in S^2`;
- finite probe families `N = {n_i}`;
- trace distance and fidelity between `rho(r)` and `rho(s)`;
- named CPTP contraction checks for dephasing, depolarizing, and amplitude damping only as contraction receipts.

Do not build S4 channel ellipsoid image classification or S5 fixed-point/basin classification in this packet.

### B1. Mandatory convention PIN

Every receipt that mentions `rho`, `Bloch`, `sigma_y`, expectation, Born probability, measurement update, trace distance, fidelity, or CPTP contraction must include one structured `convention_pin` object with:

1. `sigma_y_standard = [[0,-i],[i,0]]`.
2. `bloch_basis = (sigma_x, -sigma_y_standard, sigma_z)`.
3. `component_rule = r_i = Tr(rho * basis_i)`.
4. `rho_rule = rho(r) = (I + r.basis) / 2`.
5. `hopf_lineage = geo_s1_exact_closure_v0 pinned identity`.
6. `trace_distance_convention = D(rho,sigma) = 1/2 ||rho-sigma||_1`.
7. `fidelity_convention = squared Uhlmann qubit fidelity F = 1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)))`, with `root_fidelity = sqrt(F)` if emitted.

Any use of the standard `sigma_y` sign must be either converted through the pin or marked as a negative control.

### B2. Positive receipt families

The future packet must emit these positive receipts.

| ID | Claim | Required route | Target strength |
| --- | --- | --- | --- |
| S3.F01 | One-qubit finite presentation | emit `hilbert_dim=2`, `operator_basis_count=4`, `mixed_density_real_dim=3`, finite Pauli basis, finite variables/constraints for symbolic fields | `exact_integer_combinatorial` plus `symbolic_identity` |
| S3.N01 | Root noncommutation in S3 | emit O1-O6 with commuting control, general noncommuting witness, noncommuting-not-anticommuting witness, Clifford anticommuting witness, measurement order-gap row, and capacity row kept separate | `symbolic_identity` / `exact_integer_combinatorial` |
| S3.T01 | Bracketing boundary | matrix associator `(AB)C-A(BC)=0`; schedule/channel associator marked `open_with_reason` unless a named nonlinear/adaptive measurement schedule is explicitly scoped | `symbolic_identity` / `open_with_reason` |
| S3.A | Bloch ball field | derive eigenvalues `(1 +/- ||r||)/2`, positivity iff `||r||<=1`, determinant `(1-||r||^2)/4`, purity `(1+||r||^2)/2`, entropy `H2((1+||r||)/2)` | `symbolic_identity` / `closed_form_integral` where integrated |
| S3.B | Observable plane fields | derive `Tr(O rho(r)) = a0 + a.r`; emit plane normal/offset for `Tr(O rho)=c`; include pinned-y sign compatibility | `symbolic_identity` |
| S3.C | Born fields | derive `p_+/- = (1 +/- n.r)/2`, normalization, range on `B^3`, boundary certainty at `r=+/- n` | `symbolic_identity` |
| S3.D | Measurement updates | compute selective update `r -> +/- n` with probabilities `p_+/-`; compute nonselective update `r -> (n.r)n`; emit idempotence and purity/entropy effects | `symbolic_identity` plus selected exact rows |
| S3.E | Probe-equivalence quotient map | for named probe families, compute `Q_N(r) = (n_i.r)_i` or probability vector, rank, kernel, equivalence class parameterization, and reconstructed quotient dimension | `symbolic_identity` / `finite_exhaustive_enumeration` for finite families |
| S3.F | Trace distance and fidelity | derive `D = ||r-s||_2/2`; derive squared Uhlmann fidelity formula; include pure, center, antipodal, and mixed-interior controls | `symbolic_identity` |
| S3.G | CPTP contraction | for named one-qubit CPTP maps, prove/compute `D(Phi(r),Phi(s)) <= D(r,s)` and fidelity monotonicity under the pinned fidelity convention; no ellipsoid/basin claim | `symbolic_identity` where diagonal/simple channels allow proof, `rigorous_interval_bound` for bounded sweeps |

### B3. F01 details

The packet must include:

```text
F01_finitude_receipt:
  hilbert_dim = 2
  computational_basis_count = 2
  operator_basis_count = 4
  pure_sphere = S^3 subset C^2
  phase_quotient = CP^1 = S^2
  mixed_density_real_dim = 3
  active_probe_family_count = finite / named for each probe family
  quotient_or_relation_table = finite where claimed
  finite_enumeration_bounds = named
  proof_objects = finite Pauli basis + finite variables r_x,r_y,r_z,a0,a,n + finite polynomial identities
```

Do not cite finite arrays alone as F01. Symbolic all-state identities are allowed only because the carrier, variables, constraints, and generators are finitely presented.

### B4. N01 details

The packet must include:

- O1 commuting control: `A=Z`, `B=f(Z)` or another distinct commuting pair, order gap `0`.
- O2 general noncommuting witness: `A=X`, `B=Z`, `AB != BA`.
- O3 noncommuting-but-not-anticommuting witness: `A=X`, `B=X+Z`, `AB != BA` and `AB+BA != 0`.
- O4 Clifford witness: `X` and `Z` anticommute, with `XZ+ZX=0`.
- O5 measurement order gap: sequential projective measurements along nonparallel axes produce different conditioned or nonselective output statistics; commuting/same-axis control has gap `0`.
- O6 capacity row: pairwise anticommuting capacity belongs to Clifford capacity, not root-order pressure.

Anticommutation must not be used as the definition of N01.

### B5. T01 details

The packet must include the associative matrix-algebra control:

```text
T01_bracketing_receipt:
  matrix_associator_control: (AB)C - A(BC) = 0 in M_2(C)
  schedule_or_channel_associator_test: open_with_reason unless a named adaptive/nonlinear measurement schedule is scoped
  explicit_statement: algebra-level nonassociativity is not present in one-qubit matrix multiplication
  boundary: true algebra-level nonassociativity belongs to later octonion/nonassociative extension lanes
```

If a measurement schedule row is added, it must distinguish sequence/order effects from algebra-level associator claims.

### B6. Engine and receipt expectations

The build should follow the current S1/S2 packet discipline:

- Julia canon route for symbolic Pauli/density/trace identities where practical.
- JAX/SymPy route for independent symbolic checks, exact formulas, and dense bounded sweeps.
- PyTorch route for an honest S3-native lane, such as tensor-native projective updates, batched contraction checks, or finite probe-map rank checks; otherwise mark PyTorch supportive/not-scoped honestly.
- envelope result validated with `--require-pytorch --strict-source-backed`.
- `TOOL_MANIFEST` non-empty for each used tool, with non-empty reasons.
- `TOOL_INTEGRATION_DEPTH` honest (`load_bearing`, `supportive`, or `None`).
- every claim row carries a literal allowed strength token.
- no formal, canonical, bridge, axis, physics, S4 ellipsoid, or S5 basin claim.

Literal allowed strength tokens:

```text
symbolic_identity
closed_form_integral
exact_integer_combinatorial
rigorous_interval_bound
measure_theorem
finite_exhaustive_enumeration
representation_theorem_with_constructive_receipt
statistical_redundant_by_exact_route
diagnostic_float_nonclaim
open_with_reason
```

Forbidden for claim-bearing rows:

```text
bare_float_tolerance
sample_only
max_deviation_only
abs_error_only
visual agreement
validator-green only
```

## C. Negative-model specs

### C1. Outside-ball negative

Construct `r_bad` with `||r_bad|| > 1` and route it through the same `rho(r)` adapter.

Expected selectivity:

- fail positivity/eigenvalue/Born-range receipts;
- fail entropy domain if the formula is forced beyond the domain;
- preserve affine expectation formula syntax as a non-state algebraic expression;
- must not fail pinned Pauli basis construction.

### C2. Wrong `sigma_y` pin negative

Construct the S3 fields with standard `sigma_y` where the S1 lineage requires `-sigma_y_standard`.

Expected selectivity:

- fail y-component compatibility with `geo_s1_exact_closure_v0` lineage;
- fail observable expectation rows involving y;
- preserve x/z rows;
- must not be silently accepted by changing the convention pin.

### C3. Commuting-probe simplex misclassified as ball

Use only a commuting `Z` probe family and attempt to reconstruct a 3D ball.

Expected selectivity:

- fail `rank=3` / full-ball quotient rows;
- pass interval/simplex quotient rows with dimension `1`;
- preserve Born formula for the `Z` direction;
- connect directly to the `bloch_root_admissibility_discriminator_v0` T2 lesson.

### C4. Nonlinear expectation echo negative

Use a fake observable field such as `a0 + a.r + epsilon ||r||^2` while labeling it `Tr(O rho)`.

Expected selectivity:

- fail linearity and plane-level-set receipts;
- fail trace derivation from the actual `O` matrix;
- may pass at the origin or for accidental shells only as marked accidental controls;
- must not be accepted through sample-only plane fitting.

### C5. Bad measurement update negative

Use an unnormalized or wrong-axis post-measurement update.

Expected selectivity:

- fail selective-update target `r -> +/- n`;
- fail probability conservation or idempotence;
- preserve Born probability formula if probabilities are separately computed correctly;
- distinguish wrong update from wrong probability.

### C6. Non-CPTP expansive map negative

Use a map such as `r -> lambda r` with `lambda > 1` on an interior domain where outputs remain comparable, or another explicit non-CPTP affine map.

Expected selectivity:

- fail CPTP certification;
- fail trace-distance contraction on a named pair;
- preserve trace-distance formula itself;
- must not be used as an ellipsoid/basin claim.

### C7. Wrong mixed-state fidelity formula negative

Use pure-state overlap or `1/2(1+r.s)` as if it were mixed-state fidelity.

Expected selectivity:

- pass selected pure-boundary cases where the formula coincides;
- fail mixed-interior controls requiring the square-root determinant term;
- preserve trace-distance rows;
- emit the convention conflict explicitly.

## D. Alternative-model specs

### D1. Fidelity convention alternative

Emit both squared Uhlmann fidelity and root fidelity only if the convention pin names them separately. The squared convention is the claim path; root fidelity is an auxiliary conversion row.

Acceptance target: conversions agree by squaring/square-rooting, but no row may compare a root-fidelity value against a squared-fidelity target.

### D2. Probe-family alternatives

Use named finite probe families:

- `Z_only`: quotient dimension `1`;
- `X_Z`: quotient dimension `2`;
- `X_Y_Z`: quotient dimension `3`;
- redundant probes, such as duplicate `Z`, must not raise rank;
- refined spherical probe families may support F01-style refinement but not replace the exact three-Pauli reconstruction.

Acceptance target: each family emits `Q_N`, rank, kernel, equivalence relation, and quotient dimension.

### D3. Simple CPTP families

For S3 contraction only, use simple named channels:

- dephasing: shrink transverse components;
- depolarizing: uniform shrink;
- amplitude damping: affine shift plus shrink.

Acceptance target: contraction rows pass, but image ellipsoid classification, fixed points, and basins are explicitly deferred to S4/S5.

## E. Blind-lane derivation list

The build should assign independent blind derivations before integration:

1. Derive `rho(r) = (I+r.basis)/2` under the pinned basis and compute eigenvalues, determinant, purity, and entropy domain.
2. Derive positivity iff `||r|| <= 1` without reading a result JSON fixture.
3. Derive `Tr((a0 I+a.basis) rho(r)) = a0+a.r` from matrix multiplication.
4. Derive Born probabilities for projectors `(I +/- n.basis)/2`.
5. Derive selective and nonselective projective update maps from projectors and trace normalization.
6. Derive the finite probe quotient map `Q_N`, rank, kernel, and equivalence classes for each named probe family.
7. Derive trace distance from eigenvalues of `rho(r)-rho(s)`.
8. Derive qubit mixed-state fidelity with the determinant square-root term and separate root-vs-squared convention.
9. Derive contraction for each named CPTP family from the actual affine map or Kraus route.
10. Derive F01/N01/T01 receipts with exact controls and separate root noncommutation from Clifford capacity.
11. Derive negative-model selectivity matrices for outside-ball, wrong-y-pin, commuting-only, nonlinear-expectation, bad-update, non-CPTP-expansive, and wrong-fidelity negatives.
12. Derive audit-ready source scans for stale S4/S5 language so ellipsoid/basin claims do not leak into S3.

No blind lane may hardcode final receipt values as fixtures. Each lane must expose intermediate matrices, variables, and raw values so a fresh audit can recompute the claim.

## F. Audit attack list

The S3 audit should attack all prior S1/S2 H/E-pattern failures and carry forward the hardening lessons:

1. Convention PIN missing: reject any density, expectation, Born, update, distance, fidelity, or contraction row without the pinned `sigma_y` and metric/fidelity conventions.
2. Derived-vs-predeclared: reject rows that echo `rho`, eigenvalues, purity, entropy, expectation, or update formulas without deriving them from matrices/projectors.
3. Sign absorption: check that y-sign changes are explicit and cannot be hidden by relabeling the basis.
4. Computed signs/factors: require wrong-sign, wrong-factor, and missing-square-root controls for expectation, Born, fidelity, and update formulas.
5. Fixture isolation: reject disjoint fixtures where each observable only reads its own field; shared `rho(r)` must feed expectations, Born probabilities, updates, and distance rows.
6. Label echo: reject probe-rank or quotient-dimension rows that are keyed from family labels instead of computed from probe vectors.
7. Weak shuffle: shuffled/duplicate probe controls must actually recompute rank/kernel and not only reorder labels.
8. Tautological controls: reject `x-x`, `pass=True`, or post-erasure zeros that cannot fail.
9. Derived-boolean SMT: z3/cvc5 sidecars must bind raw matrix entries, ranks, scaled residuals, or integer counts, not already-assigned verdict booleans.
10. Synthetic PyTorch: PyTorch must perform a real tensor-native S3 route or be demoted; no decorative autograd/Jacobian claim.
11. Numerical authenticity: dense sweeps may be diagnostics, but claim rows must be symbolic, exact, interval, theorem, or finite-enumeration where promised.
12. Genuine interval/bound route: any interval row must propagate interval inputs through the relevant formula, not float-tail box a closed-form result.
13. Exact-by-algebra labeling: exact symbolic identities must be labeled exact-by-algebra, not convergence.
14. No hardcoded receipts: search source for final constants and formulas bypassing derivation, especially eigenvalues, entropy values, fidelity terms, and contraction pass flags.
15. Negative selectivity: each negative model must fail only its predicted receipt family and preserve unrelated positive controls.
16. Common adapter for negatives: route negatives and positives through a shared receipt interface where feasible.
17. Root-order boundary: N01 must include noncommuting-not-anticommuting O3 and must not define root pressure as anticommutation.
18. T01 honesty: matrix associativity must be a zero control; sequence/order effects must not be renamed algebra-level nonassociativity.
19. Fidelity convention audit: root and squared fidelity must not be mixed in comparisons.
20. CPTP boundary audit: contraction checks must not launder S4 ellipsoid or S5 fixed-point/basin claims.
21. Source-backed tools: enforce strict source-backed validation; load-bearing tool claims must gate a receipt and name function/API surfaces.
22. Stale surface scan: audit build cards, envelopes, result tables, and verdict text for old narrowed labels, S4/S5 leakage, or overstrong status language.
23. Ceiling audit: reject any formal-admission, canonical, bridge, axis, physics, ellipsoid-image, fixed-point, basin, or manifold-promotion language.
24. No receipt laundering: schema/validator green is not enough; every load-bearing row must survive direct recomputation from emitted source/result artifacts.
