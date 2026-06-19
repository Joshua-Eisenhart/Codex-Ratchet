# Fresh Audit: geo_s1_vector_vs_spinor_v0

Audit date: 2026-06-10

VERDICT: GENUINE DISCRIMINATION, NOT VECTOR EXCLUSION.

The packet genuinely builds an SO(3) vector leg and an SU(2) spinor leg, computes the 2pi/4pi split, computes the U/-U double-cover collapse, and keeps the ceiling at `scratch_diagnostic`. It answers "why spinors and not plain vectors" for pre-quotient sign/holonomy/fiber construction claims: the spinor route carries data the vector route has already quotiented away.

It does not earn a blanket "SO(3) vectors excluded" claim. The packet itself says vector/Bloch observables survive after quotient, and the density quotient row collapses the sign exactly as intended. It also does not emit a formal `N01` or `order_gap` field; the hand recompute below gives a like-for-like boolean closure-order gap, but that is not a named packet receipt.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No canonical/admitted/formal status is earned.

## Evidence Boundary

Sources read:

- `system_v6/receipts/audit_bar_calibration_20260610.md`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/geo_s1_vector_vs_spinor_v0_julia.jl`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/geo_s1_vector_vs_spinor_v0_jax.py`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/geo_s1_vector_vs_spinor_v0_pytorch.py`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/geo_s1_vector_vs_spinor_v0_envelope.py`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_julia_results.json`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_jax_results.json`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_pytorch_results.json`
- `system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_envelope_results.json`

Fresh commands/checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_envelope_results.json` returned `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_envelope_results.json` returned `ok:true`.
- Standalone hand recompute of one 2pi/4pi pair and one like-for-like closure-order gap returned the values in the recompute table below.
- I did not rerun `*_julia.jl`, `*_jax.py`, `*_pytorch.py`, or the envelope entrypoint because their `main()` functions write result JSONs and this audit was read-only except this verdict file.
- `git status --short -- system_v6/sims/geo_s1_vector_vs_spinor_v0 system_v6/receipts/audit_bar_calibration_20260610.md` reports `?? system_v6/sims/geo_s1_vector_vs_spinor_v0/` in this checkout.

The calibrated bar was applied from `audit_bar_calibration_20260610.md`: keep F01/N01 pins, route genuineness, can-fail controls, erasure honesty, scratch ceilings, and fresh-context audits; do not require over-strict two-CAS end-to-end when one derivation plus independent solver/cross-engine binding is present. Cites: `system_v6/receipts/audit_bar_calibration_20260610.md:5-11`.

## Manual Recompute Packet

Hand recompute from the declared definitions `U(theta)=diag(exp(-i theta/2), exp(i theta/2))` and `R(theta)=Rz(theta)`:

| Check | Recomputed value |
|---|---:|
| `||Rz(2pi) - I3||_F` | `3.463824224941973e-16` |
| `||Rz(4pi) - I3||_F` | `6.927648449883946e-16` |
| `||U(2pi) - I2||_F` | `2.8284271247461903` |
| `||U(2pi) - (-I2)||_F` | `1.7319121124709866e-16` |
| `||U(4pi) - I2||_F` | `3.463824224941973e-16` |
| Like-for-like boolean closure-order gap at 2pi | `1` |

The closure-order gap above uses the same probe family and same functional on both routes: `1[route closes to identity at 2pi under its own representation]`, then `vector_minus_spinor`. Vector closes at 2pi and spinor does not, so the gap is `1 - 0 = 1`. This avoids comparing raw 3x3 SO(3) and 2x2 SU(2) Frobenius norms as if they were one scale.

## Q1. SO(3) Leg Genuineness

Decision: PASSES.

Quoted source:

```julia
function so3_z(theta::Float64)
    c = cos(theta)
    s = sin(theta)
    return [c -s 0.0; s c 0.0; 0.0 0.0 1.0]
end
```

Cites: explicit Julia rotation matrix at `geo_s1_vector_vs_spinor_v0_julia.jl:64-68`; Julia SO(3) manifold object and distance calls at `geo_s1_vector_vs_spinor_v0_julia.jl:115-139`.

The vector leg is not merely a renamed spinor leg. Julia uses `Manifolds.Rotations(3)` and computes distances from genuine 3x3 rotation matrices. PyTorch independently defines `so3_z(...)`, instantiates `SpecialOrthogonal(n=3, point_type="matrix")`, and computes `so3.metric.dist(identity, r2/r4)`. Cites: `geo_s1_vector_vs_spinor_v0_pytorch.py:75-86` and `geo_s1_vector_vs_spinor_v0_pytorch.py:112-120`.

## Q2. Discriminating Rows And 2pi/4pi Holonomy

Decision: PASSES.

Quoted source:

```python
so3_distances = jax.vmap(lambda t: jnp.linalg.norm(so3_z(t) - i3))(angles)
su2_identity_distances = jax.vmap(lambda t: jnp.linalg.norm(su2_z(t) - i2))(angles)
su2_minus_identity_distances = jax.vmap(lambda t: jnp.linalg.norm(su2_z(t) + i2))(angles)
```

Cites: `geo_s1_vector_vs_spinor_v0_jax.py:138-160`.

The result rows match the hand recompute. JAX records `so3_distance_at_2pi=3.463824224941973e-16`, `su2_identity_distance_at_2pi=2.8284271247461903`, `su2_minus_identity_distance_at_2pi=1.7319121124709866e-16`, and `su2_identity_distance_at_4pi=3.463824224941973e-16`. Cite: `geo_s1_vector_vs_spinor_v0_jax_results.json:100-112`.

Julia records the same route facts and also records the concrete matrices: `R_2pi` is identity up to roundoff, `U_2pi` is `-I` up to roundoff, and `U_4pi` is `I` up to roundoff. Cites: `geo_s1_vector_vs_spinor_v0_julia_results.json:83-171`.

The double-cover/negative-conjugation row is also computed, not prose. JAX symbolically computes `R_ij = 1/2 Tr(sigma_i U sigma_j U^dagger)` and records `R_from_U_minus_R_from_minus_U` as all zero entries. Cites: source at `geo_s1_vector_vs_spinor_v0_jax.py:90-122`; result at `geo_s1_vector_vs_spinor_v0_jax_results.json:128-179`.

## Q3. N01 Order-Gap Like-For-Like

Decision: PARTIAL / NAMED GAP.

The packet does not emit a formal `N01`, `order_gap`, `n01_order_gap`, `gap_functional`, or equivalent named receipt. A repo search inside this packet found no such field. The envelope's `divergence.engine_values` are all `0.0`, but those are explicitly density-quotient sign distances, not vector-vs-spinor N01 order gaps. Cites: envelope divergence at `geo_s1_vector_vs_spinor_v0_envelope_results.json:156-164`; engine scalar rows at `geo_s1_vector_vs_spinor_v0_envelope_results.json:202-208`, `geo_s1_vector_vs_spinor_v0_envelope_results.json:269-275`, and `geo_s1_vector_vs_spinor_v0_envelope_results.json:327-330`.

The hand recompute gives a valid like-for-like closure-order gap at 2pi: use the boolean functional `closes_to_identity_at_2pi` on each route under its own representation. SO(3) gives `true`, SU(2) gives `false`, so `vector_minus_spinor = 1`.

That supports discrimination, but it should be added as an explicit packet receipt before anyone cites this as an N01-order-gap result. Do not cite raw `||R-I3||` versus `||U-I2||` as a numeric order gap; those live in different representation dimensions and are not one normalized scale.

## Q4. Verdict Direction

Decision: DISTINGUISHED / SPINOR REQUIRED FOR PRE-QUOTIENT CLAIMS; VECTORS NOT EXCLUDED.

The envelope language is mostly honest. It says the routes are "competing S1 carriers," says spinor is required for sign/phase, 4pi return, holonomy sign, Hopf S1 fiber/linking, and keystone construction, and says the vector route survives as SO(3)/Bloch observable data after quotient. Cites: claim at `geo_s1_vector_vs_spinor_v0_envelope_results.json:38`; fact classification at `geo_s1_vector_vs_spinor_v0_envelope_results.json:50-64`; summary at `geo_s1_vector_vs_spinor_v0_envelope_results.json:466`.

The decisive row is the density quotient: the packet computes that `psi` and `-psi` are distinct before quotient but `rho=psi psi^dagger` is equal afterward. Julia records spinor norm difference `2.0` and density norm difference `0.0`; JAX records symbolic density difference all zeros. Cites: `geo_s1_vector_vs_spinor_v0_julia_results.json:173-224` and `geo_s1_vector_vs_spinor_v0_jax_results.json:113-127`.

Therefore any future receipt language saying "SO(3) vector model excluded" is too strong unless it is scoped to excluded for the pre-quotient sign/holonomy/fiber construction claim. The honest language is: the SO(3) vector route is admissible-but-coarser as a quotient/base observable route, and it is discriminated from, not a replacement for, the SU(2) spinor route where the lost sign/fiber data is claim-bearing.

## Q5. Standard Checks

Decision: PASSES WITH THE Q3 GAP.

Mode is declared as `all_three_full_sims`, with lanes `julia`, `jax`, and `pytorch`. The envelope records `classification=scratch_diagnostic`, `promotion_allowed=false`, and `formal_admission_allowed=false`. Cites: `geo_s1_vector_vs_spinor_v0_envelope_results.json:49` and `geo_s1_vector_vs_spinor_v0_envelope_results.json:165-179`.

Controls can fail and flip. JAX and Julia both set a corrupted `su2_2pi_not_closed=false` control; nominal `not_accepted` is `unsat`, corrupted `not_accepted` is `sat`. Cites: `geo_s1_vector_vs_spinor_v0_jax_results.json:68-94`; `geo_s1_vector_vs_spinor_v0_julia_results.json:64-77`; envelope controls at `geo_s1_vector_vs_spinor_v0_envelope_results.json:117-153`.

Tooling is load-bearing on the claim path. Julia uses `Manifolds`, `QuantumOptics`, and `Z3`; JAX uses `sympy`, `z3`, and `cvc5`; PyTorch uses `geomstats`, `e3nn`, and `sympy`. Cites: `geo_s1_vector_vs_spinor_v0_envelope_results.json:39-48`, `geo_s1_vector_vs_spinor_v0_envelope_results.json:180-245`, `geo_s1_vector_vs_spinor_v0_envelope_results.json:246-330`; PyTorch half-integer irrep rejection control at `geo_s1_vector_vs_spinor_v0_pytorch_results.json:63-85`.

Seeds are not applicable for this deterministic symbolic/closed-form route; there is no random sampler in the claim path. The source/result pins are present via `pin_spec` and `pin_sha256` in all legs. Cite: Julia pin at `geo_s1_vector_vs_spinor_v0_julia_results.json:61-63`; JAX pin at `geo_s1_vector_vs_spinor_v0_jax_results.json:65-67`; PyTorch pin at `geo_s1_vector_vs_spinor_v0_pytorch_results.json:57-60`.

## Named Gaps

1. `GAP-N01-ORDER-RECEIPT`: no formal `N01`/`order_gap` receipt exists in the packet. Add an explicit gap functional and value before citing this as an N01-order-gap result.
2. `GAP-RAW-SCALE-MISMATCH-RISK`: raw SO(3) 3x3 and SU(2) 2x2 norm distances are useful closure diagnostics but should not be presented as one scalar order-gap scale. Use a normalized/boolean closure functional or another pinned common functional.
3. `GAP-EXCLUSION-LANGUAGE`: any "vector excluded" phrasing must be narrowed. The computed result supports "vector excluded for sign/holonomy/fiber construction claims," not "vector route excluded as quotient/base observable."

## Final Boundary

Keep: three-engine scratch diagnostic; real SO(3) vector leg; real SU(2) spinor leg; computed 2pi/4pi split; computed U/-U double-cover collapse; density quotient erasure honesty; load-bearing solver controls; strict source-backed validator pass.

Audit further: add a named N01/order-gap receipt with a pinned common functional; re-audit any future prose that uses "excluded."

Demote: blanket vector-exclusion claims; canonical/admitted/formal claims; any claim that density/Bloch observables themselves require carrying the pre-quotient spinor sign after quotient.

Broken/blocked: none for the stated spinor-vs-vector discriminator under `scratch_diagnostic`; the N01 order-gap receipt is missing as a citation surface.

Next build: add `order_gap_receipt = {"functional": "...", "vector_value": ..., "spinor_value": ..., "gap": ...}` to all three legs and the envelope, using a like-for-like functional rather than raw mixed-dimension norm magnitudes.

## builder-hardening

Builder hardening on 2026-06-10 closes `GAP-N01-ORDER-RECEIPT` for the Julia canon leg and JAX mirror by adding `n01_closure_order_gap=1` from the normalized boolean closure functional: SO(3) `Rz(2pi)` closes to identity, SU(2) `U(2pi)` does not, and both close at `4pi`. The regenerated envelope surfaces this under `envelope_facts.n01_closure_order_gap`, explicitly excludes raw `||R-I3||` versus `||U-I2||` as a cross-dimension numeric gap, and narrows vector language to "excluded for pre-quotient sign/holonomy/fiber construction claims; admissible but coarser after quotient."

Fresh reruns completed for Julia, JAX, PyTorch, and envelope from entrypoints. Required validator returned `ok:true` for `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_vector_vs_spinor_v0/results/geo_s1_vector_vs_spinor_v0_envelope_results.json`. Ceiling unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
