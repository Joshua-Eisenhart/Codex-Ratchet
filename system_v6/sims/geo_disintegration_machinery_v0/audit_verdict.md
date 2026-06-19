# Audit verdict: geo_disintegration_machinery_v0

Audit date: 2026-06-10

Scope: read-only audit of `system_v6/sims/geo_disintegration_machinery_v0/`, except this verdict file. I did not build this packet. I did not git add or commit anything.

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md` keeps convention pins, can-fail controls, capability-probe gates, route genuineness, erasure honesty, and scratch ceilings; it relaxes over-strict byte/two-CAS/vocabulary requirements where the math is otherwise checked.

Advisory pre-registration context: `system_v6/receipts/cross_model_anchor_recompute_panel2_20260610.md` q6 says both external blind models reached the anchor targets `sin(2eta)` and `2*pi^2` before this packet reported. I treat that as advisory convergence only; the verdict below is based on packet source, packet receipts, and fresh recomputation.

## Sources checked

- `geo_disintegration_machinery_v0_common.py`: convention pin says `volume_form_double_chart=(1/2)*sin(2*eta)`, `physical_torus_area=2*pi^2*sin(2*eta)`, `s3_volume=2*pi^2`, `normalized_eta_marginal=sin(2*eta)`, `conditional_chart_density=1/(4*pi^2)`, double cover `(phi, chi) ~ (phi + pi, chi + pi)`, and finite grid rule `N^2/2` physical quotient classes.
- `geo_disintegration_machinery_v0_jax.py`: SymPy computes the chart density, S3 volume, eta marginal, conditional density, conditional average, global integral, disintegrated integral, and all control rows. z3/cvc5 compute the finite recovery identity and erased controls.
- `geo_disintegration_machinery_v0_julia.jl`: Symbolics computes an independent transformed-marginal recovery row under `x=cos(2*eta)` and Z3.jl computes the same finite recovery identity.
- `geo_disintegration_machinery_v0_envelope.py`: combines Julia and JAX results, checks ceilings, no peer reads, source hashes, all gates, and the declared scope boundary.
- `geo_disintegration_machinery_v0_exact_strength_validator.py`: read-only validator passed before this verdict file was created.

Fresh validator result:

```text
{"ok": true, "errors": [], "result_json": "system_v6/sims/geo_disintegration_machinery_v0/results/geo_disintegration_machinery_v0_envelope_results.json"}
```

## Q1: Exact disintegration property

Verdict: PASS, with convention caveat `CAVEAT_QDENSITY` below.

Quoted packet source/receipt:

- Source computes `physical_chart_volume_density = sin(2*eta) / 2`, integrates it over `eta, phi, chi`, forms `normalized_chart_density`, then integrates over `phi, chi` to get `eta_marginal`.
- Receipt row `R1_eta_marginal_area_law` records `volume_density_on_double_chart=(1/2)*sin(2*eta)`, `torus_layer_area_from_chart=2*pi**2*sin(2*eta)`, `normalized_eta_marginal=sin(2*eta)`, `conditional_chart_density=1/(4*pi**2)`, `conditional_total_mass=1`, and `s3_volume=2*pi**2`.
- Receipt row `R2_symbolic_disintegration_recovery` records test function `a + b*cos(2*eta) + c*sin(2*eta)**2 + d*cos(phi) + e*sin(chi) + f*cos(chi + phi)`, conditional average `a + b*cos(2*eta) + c*sin(2*eta)**2`, global integral `a + 2*c/3`, disintegrated integral `a + 2*c/3`, and defect `0`.
- Julia receipt `J1_symbolics_recovery_identity` independently records `x=cos(2*eta), sin(2*eta)d_eta=-dx/2`, uniform density `1/2` on `[-1,1]`, global integral `a + c / 3`, disintegrated integral `a + c / 3`, and defect `0`.

Fresh recomputation:

```text
integral_0_to_pi/2 sin(2*eta) d_eta = [-cos(2*eta)/2]_0^(pi/2) = 1
packet dV convention = (1/2)*sin(2*eta) d_eta d_phi d_chi
V = (1/2) * (2*pi) * (2*pi) * 1 = 2*pi^2 = 19.739208802178716
eta marginal = integral_phi_chi [(1/2)*sin(2*eta) / (2*pi^2)] = sin(2*eta)
conditional chart density = 1/(4*pi^2), so integral over [0,2*pi]^2 = 1
global integral = a + 2*c/3
disintegrated integral = a + 2*c/3
defect = 0
```

The committed-value anchor `19.7392088022` is hit within `2.12843076496938e-11`.

## Q2: Conditionals on measure-zero leaves and 2:1 cover

Verdict: PASS, with `CAVEAT_QDENSITY`.

Quoted packet source/receipt:

- Convention pin: `double_cover=(phi, chi) ~ (phi + pi, chi + pi)`.
- Convention pin: `conditional_chart_density=1/(4*pi^2) d_phi d_chi`.
- Convention pin: `finite_grid_rule=even N chart has N^2 points and N^2/2 physical quotient classes`.
- JAX diagnostic rows compute `chart_points=N^2`, `physical_points=N^2/2`, `physical_class_weight=2/chart`, and `double_cover_honored=true` for `N=4,8,16,64`.
- Solver rows use `N=8`, `physical_class_count=32`, `target_recovered_scaled=30`, and include a double-cover erasure control.

Load-bearing effect of the cover:

```text
N=8 chart points = 64
physical quotient classes = N^2/2 = 32
target = 1*5 + 2*7 + 1*11 = 30
without the cover factor, doubled_total = 60
double_cover_control_defect = 60 - 30 = 30
```

So the 2:1 factor is not decorative. Missing it would double the finite recovery mass and, in the continuous chart convention, would turn the quotient-counted area/volume into the raw double-chart count.

## Q3: Controls

Verdict: PASS.

Control (a), naive conditioning on a null leaf fails:

- Receipt `C1_naive_singleton_conditioning_fails` records constraint set `T_eta at eta=pi/4`, denominator mass `0`, numerator mass `0`, naive quotient `nan`, and failure text `P(A and T_eta)/P(T_eta) is 0/0`.
- Fresh recomputation: singleton mass is `0`, singleton quotient is `nan`.

Control (b), positive eta-band where naive equals disintegrated:

- Receipt `C2_positive_eta_band_agrees` uses band `[pi/6, pi/3]`, denominator mass `1/2`, naive value `35/12`, disintegrated value `35/12`, defect `0`.
- Fresh recomputation: band denominator `1/2`, band value `35/12`, defect `0`.

Control (c), wrong flat eta marginal fails:

- Receipt `C3_wrong_flat_marginal_fails` uses observable `sin(2*eta)**2`, correct recovery `2/3`, flat marginal `2/pi`, wrong flat recovery `1/2`, computed nonzero defect `-1/6`.
- Julia receipt `J3_wrong_flat_marginal_defect` independently records `correct_recovery=2/3`, `flat_marginal_recovery=1/2`, defect `-1//6`.
- Fresh recomputation: `1/2 - 2/3 = -1/6`.

Control (d), a.e.-honesty row:

- Receipt `C4_null_set_disintegration_scope` records modified eta `pi/4`, pointwise conditional difference for `cos_phi` equal to `1`, singleton eta mass `0`, global integrated defect `0`, and the scope statement that conditional measures are determined only eta-a.e.
- Fresh recomputation: changing one eta leaf contributes `0 * 1 = 0` to global recovery.

## Q4: Solver rows

Verdict: PASS as finite-discretization checks, not as the continuous proof.

Quoted packet source/receipt:

- z3/cvc5/J3 rows state the claim as a finite eta-layer recovery identity from bound integer layer weights, class count, and layer values.
- All three solver rows record raw values `N=8`, weights `[1,2,1]`, values `[5,7,11]`, physical class count `32`, target `30`.
- All three record positive verdict `unsat`, flat-erasure verdict `unsat`, double-cover-erasure verdict `unsat`, `flat_control_defect=-7`, `double_cover_control_defect=30`, and `asserted_precomputed_boolean=false`.

Fresh recomputation:

```text
target = 1*5 + 2*7 + 1*11 = 30
class_count = 8^2/2 = 32
valid identity negation: sum_i weight_i*(class_count*value_i) != target*class_count -> unsat
flat erasure total = 1*5 + 1*7 + 1*11 = 23; forced to target 30 -> unsat; defect -7
double-cover erasure total = 2*30 = 60; forced to target 30 -> unsat; defect 30
```

z3 and cvc5 both returned `unsat` on the positive negated identity in the fresh recomputation.

## Q5: Standard packet checks

Verdict: PASS with ceiling preserved.

- Mode declaration honest: envelope mode is `RATCHETED_prerequisite_disintegration_rule`, stage is `mode4_prerequisite`, and engine contract is `julia_canon_plus_jax_diagnostic`.
- Classification honest: envelope, JAX, and Julia all record `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.
- Hash/value-bound anchors: all three result files share pin SHA `cfb0fce2ae4ca9691261638ce66afa222b7f7b57d6c0698a69b40733f498464d`; source hashes are current; `2*pi^2=19.739208802178716`, matching committed value `19.7392088022` within `2.12843076496938e-11`.
- Capability receipts present: JAX row records SymPy `1.14.0`, JAX `0.10.1`, x64 enabled, z3 `4.16.0`, cvc5 `1.3.3`; Julia row records active project `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`, `Symbolics.Num`, and Z3 verdict `unsat`.
- One-to-one claim-path tooling: claim path tools are `Symbolics`, `Z3`, `sympy`, `z3`, and `cvc5`, and each has a corresponding tool call. JAX has an additional supportive diagnostic tool call for x64 area and finite grid rows.
- No banned fixture wording: `rg -ni "fixture" system_v6/sims/geo_disintegration_machinery_v0` returned no hits.
- Seeds pinned: `python_jax=2026061004`, `julia=2026061004`, finite grid `N=8`, finite eta layers `pi/12`, `pi/4`, `5*pi/12`.
- Scope statement honest: summary enables mode-4 cards to cite the disintegration rule for fixed-eta Hopf torus leaves despite `mu(T_eta)=0`; it explicitly does not enable a ratchet sim, manifold claim, axis claim, bridge claim, physics claim, or canonical admission.
- PyTorch omission honest: packet declares no graph/network/autograd claim path, so PyTorch would be decorative for this prerequisite.

## Q6: Closure for mode-4 prerequisite

Verdict: PASS for the Hopf fixed-eta leaf case.

The packet genuinely meets the mode-4 conditioning prerequisite for the specific Hopf foliation case:

```text
S3 = union_eta T_eta
eta in [0, pi/2]
eta marginal = sin(2*eta) d_eta
conditional on T_eta = normalized flat chart measure in (phi, chi), with 2:1 quotient honored
global round S3 measure recovered by integrating conditionals against eta marginal
```

This enables later mode-4 cards to cite the conditioning rule for fixed-eta Hopf tori. It does not run a ratchet sim and does not prove a manifold, axis, bridge, or physics claim.

Additional cases nested-ratchet conditioning still needs:

- Iterated disintegration: condition first on an outer eta shell and then on a subleaf/fiber inside that shell, with both marginals and conditionals pinned.
- Nested quotient compatibility: prove that quotient factors compose correctly when two or more covers or identifications are stacked.
- Conditioning on intersections of leaves: handle cases where two constraint foliations intersect transversely, nontransversely, or singularly.
- Null-set transfer across layers: prove that modifying conditionals on a null set at one layer remains null after the next projection or pullback.
- Fubini/Tonelli/order checks: verify that nested integration order is legal and that order changes do not silently change a sequence claim.
- Boundary/singular leaves: separately treat endpoints such as eta `0` and `pi/2`, where the torus degenerates.

## Named caveats

- `CAVEAT_QDENSITY`: the packet's `(1/2)*sin(2*eta)` over the `(phi,chi)` double chart is quotient-normalized to count the physical S3 measure once. The raw metric pullback before dividing the 2:1 cover would carry the extra factor. Consumers must not mix raw double-chart and quotient-counted conventions.
- `CAVEAT_TEST_FAMILY`: the SymPy identity is exact for the declared symbolic Fourier/polynomial test family, and Julia Symbolics independently checks a transformed polynomial shell-average family. This is enough for this packet's prerequisite target, but it is not a full measure-theory proof for arbitrary measurable functions.
- `CAVEAT_SOLVER_FINITE`: z3/cvc5/Z3.jl rows are finite scaled recovery and erasure checks. They support route genuineness and cover/marginal controls; they are not the continuous disintegration proof.
- `CAVEAT_WORKTREE_STATE`: at audit time, `git status --short -- system_v6/sims/geo_disintegration_machinery_v0` showed the packet directory as untracked. This verdict audits the working-tree packet contents, not a committed object.
- `CAVEAT_NESTED_SCOPE`: multi-layer/nested-ratchet conditioning remains unproved by this packet and needs the additional cases listed in Q6.

## Verdict

PASS: `geo_disintegration_machinery_v0` meets the mode-4 conditioning prerequisite for conditioning round S3 measure on fixed-eta Hopf torus leaves `T_eta` with the packet's quotient-normalized chart convention.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. The packet may be cited for the fixed-eta Hopf disintegration rule only. It does not authorize a ratchet sim, manifold claim, axis claim, bridge claim, physics claim, canonical admission, or nested/multi-layer disintegration claim.
