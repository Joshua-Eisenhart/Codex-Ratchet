# geo_s7_discrete_refinement_v0 build card

Status: builder-lane packet, scratch diagnostic only.

Scope:
- Build genuinely new S7 finite Hopf-torus grid refinement receipts under `system_v6/sims/geo_s7_discrete_refinement_v0/`.
- Cite S1/S2, ring checkerboard, S1 finite lens, and MCT lineage from `system_v6/receipts/s7_build_spec_20260610.md`; do not rebuild those packets.
- Use even `N={2,4,8,16,32,64}` and eta rows `{pi/12, pi/8, pi/6, pi/4, pi/3, 3*pi/8, 5*pi/12}`.
- Preserve the `2:1` cover, `kappa=(a+b) mod 2`, S2 holonomy convention pin, transported-loop holonomy route, round-trip checks, can-fail controls, cross-engine fatality, literal status tokens, and claim ceiling.

Claim ceiling:
- `classification=scratch_diagnostic`
- `promotion_allowed=false`
- `formal_admission_allowed=false`

Required local outputs:
- `geo_s7_discrete_refinement_v0_core.py`
- `geo_s7_discrete_refinement_v0_julia.jl`
- `geo_s7_discrete_refinement_v0_jax.py`
- `geo_s7_discrete_refinement_v0_pytorch.py`
- `geo_s7_discrete_refinement_v0_envelope.py`
- `geo_s7_discrete_refinement_v0_exact_strength_validator.py`
- `results/geo_s7_discrete_refinement_v0_{julia,jax,pytorch,envelope}_results.json`
- `results/convergence_curves/*.csv`

Non-claims:
- No canonical discretization.
- No manifold admission.
- No Axis closure.
- No bridge, physics, or runtime closure.
- No completed constraint-manifold geometry.
