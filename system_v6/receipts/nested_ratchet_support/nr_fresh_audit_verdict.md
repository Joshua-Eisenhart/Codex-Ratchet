# Fresh audit verdict: foundation_nested_hopf_weyl_signed_cut_ratchet

Audit target:

- `system_v5/julia_carrier/foundation_nested_hopf_weyl_signed_cut_ratchet_julia.jl`
- `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_jax.py`
- `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_pytorch.py`
- `system_v5/ops/formal_scouts/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope.py`
- result JSONs under `system_v5/julia_carrier/results/` and `system_v5/ops/formal_scouts/results/`

## Bottom line

Final classification: **GENUINE-WITH-CAVEATS**.

The separable-control equality flagged by the overseer is **GOOD**, not a copy-paste/vacuous-control bug. The source constructs the carrier as the pure Schmidt-form state
`|psi_r> = cos(theta_r)|00> + sin(theta_r)|11>`, and constructs the separable control as the product of the carrier marginals:
`diag(cos(theta_r)^2, sin(theta_r)^2)_L kron diag(cos(theta_r)^2, sin(theta_r)^2)_R`.

For a pure carrier, `S(AB)=0`, `S(B)=H(cos^2 theta, sin^2 theta)`, so `S(A|B)=-H` and `I_c=+H`. For the marginal-matched product control, `S(AB)=2H`, `S(B)=H`, so `S(A|B)=+H`. The identical magnitudes are mathematically forced.

Single most important caveat: the SMT proof is a real in-solver matrix-entry noncommutation check for the bounded 2x2 filter matrices, but it is not a full symbolic proof over the normalized density-channel/superoperator action. The numerical order gaps do use the density-channel action on `rho_probe`; the solver certificate is narrower.

## Recomputed rung values

Independent recomputation with natural logs, using `theta_r = 0.70*(r-1)/2`:

| rung | theta | p=cos(theta)^2 | H_ln | H_log2 | carrier S(A|B) | sep S(A|B) | carrier Ic |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| 2 | 0.35 | 0.8824210936422442 | 0.36207321415030524 | 0.5223612304933730 | -0.36207321415030524 | +0.36207321415030524 | +0.36207321415030524 |
| 3 | 0.70 | 0.5849835714501206 | 0.67863240236859246 | 0.9790596014837319 | -0.67863240236859246 | +0.67863240236859246 | +0.67863240236859246 |

These match the three legs to floating tolerance. The expected-values file uses log2; the build pins natural log, so the comparison is by multiplying/dividing by `ln(2)`.

## Nine failure-mode checks

1. **PASS - Pin-spec drift across legs.**
   The Julia, JAX, PyTorch, and envelope pin SHA is identical: `3133dd3db5ee9d7bc424b1f96dd6e487e6b0e0534e4a3860c6cbbf4f9f6adb81`. `reads_peer_result=false` in all three legs. The pin spec includes `eta_1 > eta_2 > eta_3`, the rho family, Weyl-L/R cut, natural-log entropy, filter/channel definition, separable control, and probe sets.

2. **PASS - Incommensurable `max_divergence`.**
   The envelope compares same-named `shared_scalars` only. It exposes 18 observable rows, no missing keys by engine, and `max_divergence=4.440892098500626e-16` on `order_gap_r1_r2`.

3. **CONCERN - Wrong marginal/sign for `S(A|B)`.**
   Source is correct: JAX/PyTorch compute `entropy_vn(rho) - entropy_vn(partial_trace_left_to_b(rho))`, and Julia computes `entropy_matrix(rho) - entropy_b(rho)` with `ptrace(op, [1])` leaving Weyl-R. The result JSONs do not expose separate `S_AB` and `S_B` fields, so result-only recomputation of this failure mode is not possible without reading source/recomputing.

4. **PASS - Entropy readout is carrier-dependent.**
   Carrier values are `[0, -0.36207321415030524, -0.6786324023685923/5]`; separable values are `[0, +0.36207321415030524, +0.6786324023685925/6]`. They differ in sign, only the carrier crosses negative, and PyTorch reports finite nonzero crossing gradient `-0.6492296109233585`.

5. **PASS - Probe families are real and used.**
   `M_1=[Z_L Z_R]`, `M_2=[Z_L Z_R, X_L X_R]`, `M_3=[Z_L Z_R, X_L X_R, Z_L, Z_R, Y_L Y_R]` are strict nested operator lists. Source computes expectation vectors from these operators and class counts from those vectors. Quotient counts are `[1, 3, 3]`: non-flat and nondecreasing, with saturation at `M_3`.

6. **PASS - Order gap is not bare-unitary plumbing.**
   Source applies normalized density filters to the same `rho_probe=rho_2`:
   `left = apply_filter(apply_filter(rho_probe, second), first)`,
   `right = apply_filter(apply_filter(rho_probe, first), second)`,
   then takes trace norm of `left-right`. Reported carrier gaps are about `[2.0, 1.109633178975764]`; commuting-control gaps are machine zero.

7. **CONCERN - SMT is real but narrower than a full-channel proof.**
   Z3/cvc5 bind the entries of the rung-2 adjacent 2x2 matrices, construct `AB` and `BA` in solver, and get `unsat` when forcing commutation; commuting controls return `sat`. This is not a precomputed boolean/scalar wrapper. Caveat: the bound entry count is `8` because it binds two 2x2 filter matrices, not a 4x4 or superoperator channel encoding.

8. **PASS - Load-bearing labels/capability probes.**
   `verify_load_bearing_has_capability_probe.py` passes for JAX, PyTorch, and envelope sources. JAX load-bearing tools are `z3` and `cvc5`; PyTorch load-bearing tool is `pytorch`; envelope has no load-bearing tools. No `numpy`, `scipy`, or `mpmath` appears in `claim_path_tools`.

9. **PASS - Contract and source-backed envelope gate.**
   Both validators passed:
   `validate_three_engine_sim_result.py --require-pytorch` and
   `validate_three_engine_sim_result.py --require-pytorch --require-source-backed`.
   Python syntax compile via `compile()` also passed for the JAX, PyTorch, and envelope sources. Envelope status is `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, `all_pass=true`.

## Required-number conditions

1. **PASS - Same object/pin.**
   All three legs use identical pin spec and hash; all peer-read flags are false.

2. **PASS - Carrier signed cut.**
   `S(A|B)_1=0`, `S(A|B)_2=-0.36207321415030524`, `S(A|B)_3≈-0.6786324023685924`; negative crossing starts at rung 2.

3. **PASS - Separable control.**
   `S(A|B)_sep=[0, +0.36207321415030524, +0.6786324023685925/6]`, nonnegative every rung.

4. **PASS - Carrier dependence.**
   Carrier and separable arrays differ by sign at rungs 2 and 3; PyTorch crossing gradient is finite and nonzero: `-0.6492296109233585`.

5. **PASS - Probe nesting/readout.**
   Strict operator inclusion is real; class count readout is `[1,3,3]`, non-flat and nondecreasing. Caveat: the final refinement saturates in class count.

6. **PASS - Order sensitivity.**
   Adjacent carrier channel gaps are positive in all engines; commuting-control gaps are near zero (`~1e-16`).

7. **PASS - Rung-1 boundary.**
   Boundary rung count 1 has `S(A|B)=0`, no negative crossing, and no adjacent order gap obligation.

8. **PASS - Cross-engine agreement.**
   Julia/JAX/PyTorch agree per named observable within `4.45e-16`; the envelope includes row-wise shared-observable comparisons, not just a scalar.

## Commands/checks run

- Located target files with `rg --files` and `find`.
- Inspected checklist and expected-values files under `/tmp/found/`.
- Inspected source paths for pin spec, rho/separable construction, entropy formula, probe family use, order-gap path, SMT binding, and PyTorch jacrev.
- Parsed result JSONs with `jq`.
- Recomputed rung entropy values independently with a small Python calculation.
- Ran:
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope_results.json`
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v5/ops/formal_scouts/results/foundation_nested_hopf_weyl_signed_cut_ratchet_envelope_results.json`
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim ...jax.py`
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim ...pytorch.py`
  - `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim ...envelope.py`
  - read-only syntax compile via Python `compile()` for the three Python sources.

No repo files were written by this audit. The repository was already dirty before the verdict write.
