# S7 build spec prep - finite discretization of Hopf tori - 2026-06-10

Status: read-lane spec only, not a build. Deliverable target for a future builder: one bounded S7 packet for genuinely new finite-grid convergence receipts only.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not claim canonical discretization, manifold admission, Axis closure, bridge/physics/runtime closure, or completed constraint-manifold geometry.

## Stage anchor

The canonical geometry program defines S7 as finite discretization: `T_eta^{N,N}` grids with the `2:1` cover handled, checkerboard parity `kappa=a+b mod 2`, and refinement `N=2..64` converging to S1-S2 invariants: area, holonomy, and flux. Convergence curves are mandatory (`system_v6/receipts/geometry_sim_program_canonical_20260610.md:17-23`).

The continuum targets are inherited from S1/S2, not redefined here:

- physical torus area: `Area(T_eta)=2*pi^2*sin(2*eta)`;
- lifted-cycle holonomy: `h(eta)=-2*pi*cos(2*eta)` under the S2 convention pin;
- curvature: `F=-2*sin(2*eta) d eta wedge d chi`;
- strip flux target, named here as `Phi_ij`, is the S2 strip integral between `eta_i` and `eta_j` over the same lifted `chi` interval. It is not the later S6 terrain transition map unless a future packet explicitly imports S6 and says so.

Build mode: FREE finite-discretization/refinement mode over already-earned S1/S2 geometry. S7 does not introduce terrain, operators, ratcheted constraints, or mixed-state lifts.

## Already computed - cite, do not rebuild

1. S2 continuum targets and cover accounting are earned.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:17-19` earns the S2 scratch diagnostic and preserves the ceiling.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:35-63` verifies the holonomy convention map and horizontal transport.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:65-101` verifies curvature, Stokes, Chern, and strip flux.
   - `system_v6/sims/geo_s2_connection_flux_foliation_v0/audit_verdict.md:103-129` verifies torus area, double-cover reason, and exact `N^2/2` grid accounting for even `N`.
   - S7 must import/cite these targets. Do not rebuild S2 symbolic derivations.

2. The program receipt already pins the `N^2/2` rule and parity-preserving cover.
   - `system_v6/receipts/geometry_sim_program_canonical_20260610.md:18` states that the `(phi,chi)` chart double-covers `T_eta` via `(phi,chi)~(phi+pi,chi+pi)`, the naive chart area is twice physical area, and all even-`N` grids have `N^2/2` distinct points.
   - `system_v6/receipts/geometry_sim_program_canonical_20260610.md:23` states the S7 requirement: `T_eta^{N,N}`, handled cover, checkerboard parity, `N=2..64`, and convergence curves.

3. `ring_checkerboard_support_graph_probe` already computes graph/parity/ladder behavior.
   - `system_v6/sims/ring_checkerboard_support_graph_probe/audit_verdict.md:5-9` adjudicates it as genuine-with-caveats and preserves its ceiling.
   - `system_v6/sims/ring_checkerboard_support_graph_probe/audit_verdict.md:74-93` recomputes parity rate and solver flips from emitted edges.
   - `system_v6/sims/ring_checkerboard_support_graph_probe/audit_verdict.md:95-157` verifies orientation and `phi0` are computed, not label-only.
   - It is a support graph/parity/ladder precedent at primary `n=8` with ladder rows through `2,4,8,16,32,64`; it is not an S7 area, holonomy, or flux convergence packet.

4. `geo_s1_finite_phase_lens_v0` is the refinement/limit exemplar.
   - `system_v6/sims/geo_s1_finite_phase_lens_v0/audit_verdict.md:5-12` adjudicates it as a finite-resolution lens-family scratch diagnostic, not a Hopf replacement.
   - `system_v6/sims/geo_s1_finite_phase_lens_v0/audit_verdict.md:35-55` records coherent `N`-ladder recomputation values.
   - `system_v6/sims/geo_s1_finite_phase_lens_v0/audit_verdict.md:136-150` verifies a decreasing refinement proxy, with the caveat that analytic `1/N` is only a proxy unless supplemented by explicit metric computation.
   - S7 should reuse the lesson: refinement curves need measured residuals and controls, not just a named ladder or analytic proxy.

5. The MCT packet already has the three-presentation receipt pattern.
   - `system_v6/sims/mct_dynamic_admissibility_packet_v0/build_card.md:56-60` defines the flat, spherical-shell, and nested-ring/Hopf-torus presentation-consistency target plus disagreement controls.
   - `system_v6/sims/mct_dynamic_admissibility_packet_v0/audit_verdict.md:101-123` says post-hardening row-location tables for all three presentations are present and disagreement controls break expected readouts.
   - S7 should reuse the presentation-receipt shape for finite torus grids. Do not rebuild the MCT packet or import its 384 support as an S7 torus-invariant result.

## Adjudication boundary

Already-computed, admissible as lineage only:

- graph support, checkerboard parity, orientation, `phi0`, and ladder rows from `ring_checkerboard_support_graph_probe`;
- finite-phase quotient/refinement pattern from `geo_s1_finite_phase_lens_v0`;
- three-presentation row-location receipt pattern from `mct_dynamic_admissibility_packet_v0`;
- continuum S2 formulas and exact even-`N` cover count `N^2/2`.

Genuinely new S7 work:

- discrete `T_eta^{N,N}` physical grids for every `N in {2,4,8,16,32,64}` with the `2:1` cover quotient and parity receipts emitted at each `N`;
- discrete area estimates converging to `2*pi^2*sin(2*eta)` with mandatory residual curves over both `N` and `eta`;
- discrete holonomy estimates on the grids converging to `h(eta)=-2*pi*cos(2*eta)`, with the S2 five-part convention pin preserved;
- discrete flux/strip estimates converging to `Phi_ij=int_strip F` and satisfying discrete Stokes against boundary holonomies;
- measured convergence rates compared to expected finite-grid scalings, not merely monotone arrays;
- parity/cover interaction receipts at each `N`, including controls where the cover or parity rule is wrong.

## Genuinely new S7 work

Build only these new receipts.

1. Physical torus grid and cover quotient.
   - For each even `N in {2,4,8,16,32,64}`, construct chart vertices `(a,b)` with `phi=2*pi*a/N`, `chi=2*pi*b/N`.
   - Implement the physical identification `(a,b) ~ (a+N/2 mod N, b+N/2 mod N)`.
   - Emit `chart_point_count=N^2`, `physical_point_count=N^2/2`, quotient-class table, representative policy, and proof that every class has size `2`.
   - Emit `kappa=(a+b) mod 2` per chart point and per physical class. Because the cover shift adds `N` to `a+b`, parity must be class-invariant for every even `N`.
   - Emit adjacency or cell tables only after quotienting, with no duplicate physical cells counted as separate evidence.

2. Three presentation receipts for the same S7 grid.
   - For every `N`, emit row-location tables in at least these presentations:
     - `flat_chart`: `(a,b)` chart coordinates plus quotient representative;
     - `spherical_shell`: embedded `S^3 subset C^2`/`R^4` torus point at fixed `eta`;
     - `nested_ring`: shell/ring index plus phase coordinates using the Hopf-torus vocabulary.
   - Presentations must agree on `physical_point_count`, parity class counts, quotient classes, edge/cell counts, area residual, holonomy residual, and flux residual.
   - Disagreement controls must break the expected rows: erase shell nesting, flatten away cover pairing, or drop one phase coordinate.

3. Discrete area convergence.
   - Compute physical torus area by a genuinely discrete geometric route, preferably embedded chord mesh triangles in `R^4` after quotienting.
   - Target: `A(eta)=2*pi^2*sin(2*eta)`.
   - Emit rows for at least `eta in {pi/12, pi/8, pi/6, pi/4, pi/3, 3*pi/8, 5*pi/12}` and every `N`.
   - Emit `area_estimate`, `area_target`, `abs_error`, `rel_error`, and `rate_between_N_doublings`.
   - If an exact quadrature route is also emitted, label it `exact_by_constant_density` and do not count it as the required convergence curve. The required curve must come from a discrete geometric estimator whose residual can change with `N`.

4. Discrete holonomy convergence.
   - Compute grid holonomy around constant-`eta` loops using a discrete transport route, not by copying the closed form.
   - Acceptable route: Wilson/overlap product or discrete horizontal lift around the sampled loop, with phase unwrapping and the S2 convention pin carried in every row.
   - Target: `h(eta)=-2*pi*cos(2*eta)` for the lifted torus-chart cycle.
   - Emit rows over all `eta` and `N`: `holonomy_estimate`, `target_h`, `lifted_or_mod_2pi`, `base_loop_count`, `abs_error`, `rel_error`, and `rate_between_N_doublings`.
   - Include the Clifford row `eta=pi/4`, where the lifted-cycle target is `0`; the error scale must be absolute, not relative-only.
   - A closed-form edge-sum row may be included as a consistency check, but it does not replace the discrete convergence route if it is exact at every `N`.

5. Discrete flux and `Phi_ij` convergence.
   - Define `Phi_ij` in this packet as the S2 strip flux target between shell pair `(eta_i, eta_j)` over the same lifted `chi` interval:
     `Phi_ij = int_{eta_i}^{eta_j} int_0^{2*pi} -2*sin(2*eta) d eta d chi`.
   - Compute a discrete plaquette/strip sum over the `eta-chi` grid between adjacent or selected shell pairs. The route must use sampled cells/weights, not the closed-form strip value.
   - Emit rows for adjacent shell pairs in the eta list and at least two wider strip pairs.
   - Emit `flux_estimate`, `target_Phi_ij`, `abs_error`, `rel_error`, `rate_between_N_doublings`, and a discrete Stokes row:
     `holonomy_estimate(eta_j)-holonomy_estimate(eta_i) + flux_estimate -> 0`.
   - Keep chart-cover normalization explicit. A naive double-covered chart flux is a negative-control value, not the physical S7 target.

6. Convergence-rate ledger.
   - For area, holonomy, flux, and Stokes residuals, fit/report observed rates over `N=2,4,8,16,32,64`.
   - Compare rates against method-specific expected scalings:
     - embedded chord mesh area: generally `O(N^-2)` on smooth tori;
     - midpoint/trapezoid plaquette flux on smooth periodic rows: `O(N^-2)` or better when the route justifies it;
     - overlap/Wilson or discrete transport phase residual: expected `O(N^-2)` unless the chosen scheme proves a different rate.
   - Exact rows are allowed but must be labeled exact and excluded from rate-fit claims.
   - A curve that is flat because the builder copied continuum formulas is a failure.

7. Parity/cover interaction receipts at each `N`.
   - Emit `parity_class_invariant_under_cover=true` only after checking all quotient pairs.
   - Emit counts for `kappa=0` and `kappa=1` physical classes, and explain any imbalance at `N=2`.
   - Emit cover-compatible adjacency/cell-orientation checks: quotienting must not identify an edge/cell with an inconsistent parity or orientation.
   - Emit SMT or exact integer checks for `2*physical_point_count=N^2` and `kappa(a,b)=kappa(a+N/2,b+N/2)`.
   - Preserve the ring-checkerboard lesson: parity rows are support/discretization evidence only, not Axis-0 closure or settled ring-checkerboard doctrine.

## Proposed packet boundary

Suggested sim id: `geo_s7_finite_torus_grid_convergence_v0`.

Allowed output path for the future build:
`system_v6/sims/geo_s7_finite_torus_grid_convergence_v0/`

Required files for the future build:

- `build_card.md`
- `geo_s7_finite_torus_grid_convergence_v0_julia.jl`
- `geo_s7_finite_torus_grid_convergence_v0_jax.py`
- `geo_s7_finite_torus_grid_convergence_v0_pytorch.py`
- `geo_s7_finite_torus_grid_convergence_v0_envelope.py`
- `geo_s7_finite_torus_grid_convergence_v0_exact_strength_validator.py`
- `results/geo_s7_finite_torus_grid_convergence_v0_{julia,jax,pytorch,envelope}_results.json`
- `results/convergence_curves/*.csv` or equivalent JSON arrays inside the envelope for area, holonomy, flux, and Stokes residual curves
- optional `audit_verdict.md` only after a separate audit lane runs

Do not edit or regenerate S1, S2, ring checkerboard, finite-lens, MCT, S5, S6, Matrix64, source docs, queue state, or the canonical program receipt.

## Positive ledger

The future build passes only if the envelope proves all of these:

1. `P1_prior_reuse_lineage`: imports/cites S1/S2 continuum targets, ring parity precedent, lens refinement precedent, and MCT presentation pattern without rebuilding them.
2. `P2_even_N_cover_quotient`: for every `N`, emits `N^2` chart points, `N^2/2` physical points, size-2 quotient classes, and representative policy.
3. `P3_parity_cover_compatibility`: `kappa` is invariant under the cover shift at every `N`, with counts and exact checks.
4. `P4_three_presentation_row_locations`: flat, spherical-shell, and nested-ring presentations agree on the same physical grid and readouts.
5. `P5_area_curve`: discrete geometric area estimates converge to `2*pi^2*sin(2*eta)` with residual curves and rate rows.
6. `P6_holonomy_curve`: discrete transport/overlap holonomy estimates converge to `h(eta)` under the full S2 convention pin.
7. `P7_flux_curve`: discrete plaquette/strip flux estimates converge to `Phi_ij`.
8. `P8_discrete_stokes`: boundary holonomy differences and discrete flux satisfy Stokes in the refinement limit, with residual curves.
9. `P9_rate_ledger`: observed convergence rates are computed and compared to declared method scalings; exact formula rows are not misreported as convergence.
10. `P10_negative_controls_execute`: all controls are actual mutated computations with observed failing values.
11. `P11_cross_engine_fatality`: Julia/JAX/PyTorch agree on load-bearing rows within declared tolerance; disagreement fails the envelope.
12. `P12_claim_ceiling`: every result carries `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`.

## Negative controls

The future build must include controls that can fail:

1. Naive cover: count `N^2` physical points; `P2` and area normalization must fail by factor `2`.
2. Wrong cover shift: use `(a+N/2,b)` or another noncanonical shift; parity/geometry pairing must fail where applicable.
3. Odd-`N` attempted cover: try `N=3` or `N=5`; route must mark unsupported/blocked, not force `N^2/2`.
4. Label-only parity: compute `kappa` but never check cover-pair invariance; `P3` must fail.
5. Presentation echo: copy row counts into three presentations without row-location tables; `P4` must fail.
6. Dropped shell nesting: collapse all `eta` rows; area/flux/shell presentation controls must fail.
7. Dropped phase coordinate: remove `phi` or `chi`; holonomy, flux, and presentation agreement must fail.
8. Formula-copy area: set `area_estimate=2*pi^2*sin(2*eta)` for every `N` and claim convergence; rate gate must fail unless labeled exact support-only.
9. Formula-copy holonomy: set `holonomy_estimate=h(eta)` directly; discrete-route gate must fail.
10. Formula-copy flux: set `flux_estimate=Phi_ij` directly; plaquette-route gate must fail.
11. Convention mix: compare one-base-loop Berry phase or mod-`2*pi` phase to lifted `h(eta)`; holonomy gate must fail.
12. Naive double-covered flux: integrate over the chart and treat the doubled value as physical; flux normalization must fail.
13. Stokes sign flip: use `+F` or reverse strip orientation without declaring it; discrete Stokes must fail.
14. Endpoint misuse: include `eta=0` or `eta=pi/2` as ordinary torus rows; degeneracy gate must fail.
15. Rate gaming: omit low-`N` failures, fit only two points, or report monotone values without observed rates; `P9` must fail.
16. Cross-engine copy: one engine reads another engine's result instead of computing local rows; independence gate must fail.
17. Ceiling creep: say canonical, admitted, closed, final geometry, Axis, bridge, runtime, or physics; claim-ceiling gate must fail.

## Blind list for audit lane

Keep these as audit expectations. A builder may encode them only as generated results from derivation, not as hand-entered verdicts.

1. For every even `N`, the cover quotient has exactly `N^2/2` physical points and no fixed quotient pairs.
2. `kappa(a,b)=a+b mod 2` is invariant under `(a,b)->(a+N/2,b+N/2)` because the parity shift is `N mod 2=0`.
3. Naive chart area is `4*pi^2*sin(2*eta)`; physical area is half of it.
4. Embedded chord-mesh area should converge toward the physical area and usually with second-order behavior.
5. `eta=pi/4` has area `2*pi^2` and lifted holonomy `0`.
6. `h(eta)` is antisymmetric around `pi/4`: signs flip between `eta` and `pi/2-eta`.
7. Strip flux and holonomy difference should satisfy `h(eta_j)-h(eta_i) = - int_strip F` under the same convention.
8. Flux signs should follow `F=-2*sin(2*eta) d eta wedge d chi`; sign-flipped rows must fail Stokes.
9. A zero or tiny residual at all `N` can be valid only for explicitly exact rows; it is not a convergence curve by itself.
10. The lens packet proves a finite-refinement pattern, not torus area/holonomy/flux convergence.
11. The ring-checkerboard packet proves parity/support behavior, not S7 invariant convergence.
12. The MCT three-presentation receipts prove a row-location pattern, not S7 presentation equivalence.
13. S7 `Phi_ij` is the S2 strip-flux target unless a future S6 packet is explicitly imported; do not mix the names.

## Audit attacks

Audit the future packet against these failure modes:

1. Rebuild drift: the builder regenerates S1/S2/ring/lens/MCT evidence instead of citing it.
2. Cover theater: result states `2:1 cover handled` but counts chart rows as physical rows.
3. Parity decoration: parity exists as a column but no cover/admissibility check depends on it.
4. Three-presentation theater: three IDs are emitted but row-location tables are absent.
5. Continuum copy: area, holonomy, or flux estimates are the target formulas with noise-free exact equality and no discrete route.
6. Curve laundering: arrays over `N` exist, but no residuals, no rate fits, or only exact-formula rows are plotted.
7. Convention collapse: endpoint global phase, Berry phase, accumulated phi, mod phase, and lifted phase are mixed.
8. Flux normalization error: chart-double-covered flux or area is compared to physical target without the cover factor.
9. Stokes source echo: discrete Stokes is asserted from continuum formula rather than computed from the discrete holonomy and flux rows.
10. Endpoint degeneracy: singular tori are included as ordinary convergence points to improve curves.
11. Rate overclaim: observed rates are called `O(N^-2)` without enough points or while signs/oscillations contradict the fit.
12. Engine-role blur: PyTorch mirrors scalar formulas and is described as independent geometry evidence without native tensor/grid work.
13. Solver decoration: SMT binds booleans rather than raw integer cover/parity values.
14. Lower-stage promotion: S7 convergence is used to promote S1/S2 from scratch diagnostic to canonical/admitted status.
15. Name collision: `Phi_ij` is silently switched from S2 strip flux to S6 terrain transition.

## Directive rules binding

1. Build genuinely new S7 finite-grid convergence receipts only.
2. Cite S1/S2 continuum targets, ring parity precedent, lens refinement precedent, and MCT presentation pattern; do not rebuild them.
3. Use only even `N={2,4,8,16,32,64}` for positive cover receipts.
4. Every row must say whether it is chart-level, physical-quotient-level, exact-support, or discrete-convergence evidence.
5. Area, holonomy, flux, and Stokes each need real residual curves over `N`.
6. Exact formula rows are allowed only when labeled exact and excluded from convergence-rate claims.
7. Preserve the S2 convention pin for every holonomy and flux comparison.
8. Keep parity/support evidence separate from continuum invariant convergence.
9. Keep `Phi_ij` as the S2 strip-flux target in this packet unless later S6 evidence is explicitly imported and scoped.
10. Every result must include `classification`, `TOOL_MANIFEST`, `TOOL_INTEGRATION_DEPTH`, source lineage, exactness labels, executed can-fail controls, convergence curves, rate rows, and claim ceiling.
11. If discrete routes disagree with continuum targets or prior receipts, preserve the divergence and mark the packet blocked pending audit. Do not smooth it into agreement.
