# S2 build spec - connection/flux/foliation stage (2026-06-10)

PROVENANCE: read-lane preparation from `system_v6/receipts/geometry_sim_program_canonical_20260610.md`, `system_v6/receipts/nesting_law_audited_20260610.md`, and the committed S1 packet audit verdicts. This is a build spec only. No S2 build, result JSON, source packet, queue mutation, or promotion is implied.

Ceiling for the future S2 packet: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## A. Positive S2 packet spec

### A0. Scope and objects

Build one bounded S2 packet for the free connection/flux/foliation layer over the S1 Hopf geometry:

- normalized spinors in `C^2`, parameterized by `(eta, phi, chi)` with `0 <= eta <= pi/2`;
- Hopf base coordinates `theta = 2 eta`, `base_angle = 2 chi`;
- Hopf connection `A = -i psi^dagger d psi = d phi + cos(2 eta) d chi`;
- curvature `F = dA = -2 sin(2 eta) d eta wedge d chi`;
- horizontal transport on constant-eta loops;
- Stokes strip consistency between two shells;
- first Chern receipt with sign/orientation and cover conventions pinned;
- Hopf tori `T_eta` with radii `cos eta` and `sin eta`;
- nested shell family `{T_eta_k}` and the Clifford torus `eta = pi/4`;
- finite torus grids with the `(phi, chi) ~ (phi + pi, chi + pi)` double-cover identification.

The packet must name the nesting arrow types from the audited nesting law:

- `S^3 subset C^2`: subset/submanifold;
- `S^3 -> S^2`: principal bundle/fibration plus quotient;
- `SU(2) -> SO(3)`: covering-space / group-quotient;
- `S^3 = union_eta T_eta`: foliation;
- `T_eta^{N,N} -> T_eta`: refinement/limit;
- lens variants: covering/group quotient, not a replacement for the Hopf quotient.

### A1. Mandatory convention PIN

Every holonomy, Berry, flux, Stokes, Chern, and torus-grid receipt must include one structured `convention_pin` object with all five fields:

1. `holonomy_quantity`: distinguish `accumulated_phi`, `endpoint_global_spinor_phase`, and Berry phase.
2. `berry_formula`: state whether the route reports `-Omega/2 = -pi(1 - cos(2 eta))` for one base loop, or the lifted/twice-traversed value.
3. `phase_domain`: state `mod_2pi` or `lifted_real`.
4. `base_loop_count`: state whether `chi: 0 -> pi` is used for one base loop or `chi: 0 -> 2pi` is used for the torus-chart cycle that traverses the base twice because `base_angle = 2 chi`.
5. `orientation_and_c1_sign`: state the sign convention that makes the displayed `F` integrate to `-4pi` over the double-covered chart and yields the reported `c1 = 1`.

The canonical S2 target for horizontal transport is:

```text
h(eta) = -2 pi cos(2 eta)
```

This target means `accumulated_phi` for the lifted torus-chart cycle `chi: 0 -> 2pi`. If a receipt reports one base loop instead, it must explicitly report the half-cycle value and not compare it to the lifted-cycle target.

### A2. Positive receipt families

The future packet must emit these positive receipts.

| ID | Claim | Required route | Target strength |
| --- | --- | --- | --- |
| S2.A | Connection derivation | derive `A = -i psi^dagger d psi` from the spinor parameterization; do not predeclare and echo it | symbolic |
| S2.F | Curvature derivation | compute `dA` and emit `F = -2 sin(2 eta) d eta wedge d chi`; include a wrong-sign control | symbolic |
| S2.H1 | Numerical horizontal transport | integrate `A(gamma_dot)=0` around the constant-eta lifted cycle and emit convergence to `h(eta) = -2 pi cos(2 eta)` | closed-form target plus numerical convergence |
| S2.H2 | Closed-form horizontal transport | solve `d phi / d chi = -cos(2 eta)` and evaluate over the pinned loop interval | closed-form |
| S2.H3 | Berry route | compute the Berry phase by solid angle with the five-convention pin; reconcile modulo/lifted and one-loop/two-loop reporting with H1/H2 | closed-form |
| S2.S | Stokes strip | for multiple exact eta pairs, verify `h(eta_j) - h(eta_i) = - int_strip F` under the same lifted-cycle convention | symbolic plus numerical spot checks |
| S2.C | Chern receipt | emit total chart integral `int F = -4 pi`, the physical/base-loop normalization, and `c1 = 1` with the orientation convention pinned | symbolic/closed-form |
| S2.T | Torus area | derive restricted metric determinant on `T_eta`, emit chart area `4 pi^2 sin(2 eta)`, physical area `2 pi^2 sin(2 eta)`, and the double-cover reason | symbolic/closed-form |
| S2.G | Grid cover accounting | for even `N`, emit `N^2 / 2` distinct physical grid points under parity-preserving identification | exact integer |
| S2.N | Nested shells | emit monotone shell rows for chosen eta values, including area, flux strip deltas, and adjacency metadata; exclude endpoint singular shells unless separately marked degenerate | closed-form plus exact integer labels |
| S2.K | Clifford torus | special row for `eta = pi/4`, radii equal, physical area `2 pi^2`, and holonomy `0` for the lifted-cycle convention | closed-form |

### A3. Horizontal transport details

The numerical route must be a real horizontal ODE route:

```text
A(gamma_dot) = dphi/dt + cos(2 eta) dchi/dt = 0
```

For constant `eta` and `chi(t)` traversing the pinned interval, the integrator computes `phi(t)` from the ODE and compares the endpoint delta against the closed-form target. It must not compute the closed form first and label it numerical transport.

Required numerical rows:

- at least five non-degenerate eta values, including `eta = pi/4`;
- at least four step sizes or solver tolerances per eta;
- convergence rows must genuinely shrink toward the closed-form residual, not flat machine-epsilon algebra rows mislabeled as convergence;
- endpoint singular shells `eta = 0` and `eta = pi/2` may appear only as boundary diagnostics, not as ordinary torus rows.

### A4. Stokes and Chern details

For any `eta_i < eta_j`:

```text
int_strip F = int_{eta_i}^{eta_j} int_{chi interval} -2 sin(2 eta) d eta d chi
h(eta_j) - h(eta_i) = - int_strip F
```

The `chi interval` must match the holonomy convention in the same receipt. The packet must include exact symbolic rows for representative pairs and independent numeric quadrature rows as diagnostics. Numeric quadrature is supportive, not the claim path.

The Chern receipt must not hide the cover/sign issue. It must state:

- displayed chart integral over `eta in [0, pi/2]`, `chi in [0, 2pi]`: `int F = -4 pi`;
- base loop/physical normalization under `base_angle = 2 chi`;
- the orientation choice under which the packet reports `c1 = 1`.

### A5. Torus area and double-cover details

At fixed `eta`, the induced metric in `(phi, chi)` coordinates has determinant `sin^2(2 eta)`, so the naive chart integral over `[0, 2pi)^2` gives:

```text
chart_area(T_eta) = 4 pi^2 sin(2 eta)
```

But the chart double-covers the physical torus by `(phi, chi) ~ (phi + pi, chi + pi)`, so the physical area target is:

```text
area(T_eta) = 2 pi^2 sin(2 eta)
```

Every finite-grid receipt must account for this same double cover:

```text
physical_points(N) = N^2 / 2
```

for even `N`, using parity-preserving identification. Naive `N^2` grids belong only in negative controls.

### A6. Engine and receipt expectations

The build should keep the S1 discipline:

- Julia canon route for symbolic/closed-form derivations where practical;
- JAX/SymPy route for independent symbolic and dense numerical checks;
- PyTorch route for a genuinely tensor/native numerical horizontal-transport or grid-check lane, with an honest role label;
- envelope result validated with `--require-pytorch --strict-source-backed`;
- `TOOL_MANIFEST` non-empty for each used tool, with non-empty reasons;
- `TOOL_INTEGRATION_DEPTH` set honestly (`load_bearing`, `supportive`, or `None`);
- every claim row carries `exact_strength` or equivalent per-row strength;
- no formal, canonical, axis, bridge, or promotion claim.

## B. Negative-model specs

### B1. Wrong connection negative

Construct a negative packet/model using at least one wrong connection, such as:

- sign-flipped connection `A_wrong = d phi - cos(2 eta) d chi`;
- missing-fiber connection `A_wrong = d phi`;
- factor-wrong connection `A_wrong = d phi + 2 cos(2 eta) d chi`.

Expected selectivity:

- fail S2.A/S2.F derivation or connection-match receipts;
- fail horizontal holonomy target except at accidental eta values;
- fail Stokes consistency against the canonical `F`;
- may still pass basic torus area receipts if the torus metric path is independent;
- must not fail everything.

### B2. Broken Stokes negative

Construct a model where `A` and `F` are not a derivative pair, for example canonical `A` paired with `F_wrong = +2 sin(2 eta) d eta wedge d chi` or a missing factor.

Expected selectivity:

- pass closed-form horizontal transport from `A`;
- fail `F = dA`;
- fail strip Stokes with the predicted sign/factor;
- fail Chern normalization in the corresponding sign/factor row;
- preserve torus area/grid receipts.

### B3. Naive-cover grid negative

Construct a grid model that treats `(phi, chi)` as a one-to-one chart on `T_eta`.

Expected selectivity:

- pass local metric determinant before quotienting;
- emit naive area `4 pi^2 sin(2 eta)` and naive point count `N^2`;
- fail physical torus area by exact factor `2`;
- fail `N^2/2` distinct-point receipt;
- fail parity-preserving identification checks;
- preserve holonomy/Stokes rows if those rows do not depend on grid cardinality.

## C. Alternative-model specs

### C1. Gauge/section alternatives

Add alternative gauge/section lanes that change local potentials but preserve invariant content:

- local section/gauge transform `A' = A + d lambda`;
- north/south base-section Berry potentials if used, with overlap transition receipt;
- endpoint spinor phase vs accumulated `phi` route, pinned as different reported quantities;
- one-base-loop Berry phase route versus lifted torus-chart cycle route.

Acceptance target: alternatives may differ in local potential, lifted endpoint phase, or modulo representative, but must preserve curvature, Stokes consistency, Chern number, and gauge-invariant holonomy class under the convention pin.

### C2. Lens-tower connection analogue

Use the S1 finite phase/lens family only as an alternative-family analogue:

- quotient by finite phase subgroup `Z_N` and identify the arrow type as covering/group quotient;
- emit connection/holonomy residue rows compatible with the finite quotient;
- preserve the ceiling that this is F01 finite-resolution alternative evidence, not a Hopf replacement;
- compare volume/cover accounting against the S1 lens audit lesson: exact formula plus any Monte Carlo route must be labeled separately;
- require Hausdorff/refinement or residue-convergence rows if the lane claims a limit relation.

The lens analogue must not be used to weaken the S2 Hopf connection target.

## D. Blind-lane derivation list

The build should assign independent blind derivations before integration:

1. Derive the Hopf connection `A` from `-i psi^dagger d psi` using the pinned spinor convention.
2. Derive `F = dA` and the total chart integral without reading any future builder constants.
3. Derive the horizontal ODE and closed-form `h(eta)` under both one-base-loop and lifted-cycle conventions.
4. Implement numerical horizontal transport from the ODE only, then compare to the closed form after the solve.
5. Derive the Berry solid-angle route and reconcile it through the five-convention pin.
6. Derive Stokes strip consistency from `h(eta_j) - h(eta_i)` and `int_strip F`.
7. Derive the Chern receipt, including the sign/orientation and chart-cover normalization.
8. Derive the fixed-eta torus metric, determinant, chart area, physical area, and Clifford row.
9. Derive the grid double-cover identification and exact `N^2/2` point count for even `N`.
10. Derive negative-model selectivity matrices for wrong connection, broken Stokes, and naive cover.
11. Derive gauge/section alternatives and prove invariant preservation.
12. Derive the lens-tower analogue as a separate alternative-family lane with its own ceiling.

No blind lane may hardcode the final receipt values as fixtures. Each lane must expose enough intermediate quantities for a fresh audit to recompute the claim.

## E. Audit attack list

The S2 audit should attack all prior S1 H/E-pattern failures and carry forward the hardening lessons:

1. Convention PIN missing: reject any holonomy/Berry/Stokes/Chern row that does not state accumulated phi vs endpoint phase, Berry formula, mod/lifted phase, base loop count, and orientation/sign.
2. Derived-vs-predeclared: reject component echoes where `A`, `F`, torus area, or grid count is prefilled rather than derived from source objects.
3. Sign absorption: check that sign choices are explicit, not hidden by using a flipped basis or route-local convention.
4. Computed signs/factors: require wrong-sign and wrong-factor controls for `F`, Stokes, Chern, and double-cover area.
5. Numerical transport authenticity: reject numerical rows that are just closed-form values re-emitted through a loop.
6. Genuine convergence: distinguish shrinking numerical convergence from exact-by-algebra residual rows and machine-epsilon flats.
7. Exact-by-algebra labeling: exact symbolic identities must be labeled exact-by-algebra, not convergence.
8. Interval/bound honesty: if any bound/interval route is added, it must propagate interval inputs through the claim path, not float-tailed boxing.
9. No hardcoded receipts: search source for receipt constants that bypass computation, especially holonomy values, crossing/sign analogues, areas, and point counts.
10. Source-backed tools: enforce strict source-backed validation; tool claims must be load-bearing only where the source proves they are.
11. PyTorch role honesty: PyTorch must do a real S2-native lane or be marked supportive/not-scoped for the claim, not listed as load-bearing by metadata alone.
12. Negative selectivity: each negative model must fail only its predicted receipt family and preserve unrelated positive controls.
13. Common adapter for negatives: avoid fixture-only negative constants; route negatives and positives through a shared receipt interface where feasible.
14. Raw-value solver binding: SMT/CAS sidecars must bind computed raw values or symbolic expressions, not already-assigned verdict booleans.
15. Stokes independence: verify `F=dA`, horizontal transport, and Stokes consistency as separate checks; do not let one derived formula imply all three.
16. Cover accounting: attack every torus/grid/area row for hidden factor-of-two errors from `(phi, chi)` double cover or `base_angle = 2 chi`.
17. Lens-family boundary: keep lens-tower evidence as alternative F01 evidence only; reject any wording that replaces the Hopf quotient or promotes the model.
18. Stale surface scan: audit build cards, envelopes, result tables, and verdict text for old narrowed or overstrong labels after hardening.
19. Ceiling audit: reject any formal-admission, canonical, bridge, axis, physics, or manifold-promotion language.
20. No receipt laundering: schema/validator green is not enough; every load-bearing row must survive direct recomputation from the emitted source/result artifacts.
