# Fresh audit verdict: geo_union_rule_k_leaves_v0

Auditor: codex2 cross-backend audit
Date: 2026-06-11
Scope: read-only audit of codex1 packet, except this `audit_verdict.md`
Calibration: `system_v6/receipts/audit_bar_calibration_20260610.md`
Parent: committed `geo_nested_disintegration_v0`

## Verdict

`GENUINE-WITH-CAVEATS`.

The finite distinct k-leaf union rule is genuinely derived by band-limit mass ratios, not merely copied from the k=2 pattern. The k=2 reduction reproduces the committed parent row byte-exact under stable JSON, the k=3/k=4 shell weights recompute exactly, the k=3 bracketing row agrees at the measure level when group mass is carried, and the degenerate/mortality controls fire in the right direction.

Ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`.

## Named caveats

- `CAVEAT_LOAD_BEARING_ALIGNMENT_METADATA`: the result maps mark `sympy` and `Symbolics` as load-bearing in `TOOL_INTEGRATION_DEPTH`, but per-engine `aligned_packages_load_bearing` lists only solver packages (`z3`, `cvc5`, `Z3`). The tool-call receipts are present and one-to-one, so this is metadata alignment debt, not a mathematical failure.
- `CAVEAT_PYTHON_SIDECAR_LABELED_JAX`: the envelope uses the standard validator lane name `jax`, but explicitly states that this lane is a Python SymPy/z3/cvc5 sidecar and that no JAX array claim is made. Do not cite this as a real JAX leg.
- `CAVEAT_DISTINCT_NONBOUNDARY_LEAVES`: the unfenced rule applies to finite distinct nonboundary fixed-eta Hopf leaves after duplicate collapse. Boundary leaves and non-leaf/transverse conditioning remain fenced.

## Q1 - k-leaf rule derived

Pass.

Quoted source:

- `geo_union_rule_k_leaves_v0_common.py` pins `leaf_density=rho(eta)=sin(2*eta)` and `finite_k_distinct_union_rule=...sin(2eta_i)/sum_j sin(2eta_j)...`.
- `geo_union_rule_k_leaves_v0_python.py` records: `int_{eta_i-eps}^{eta_i+eps} sin(2*eta) d_eta = sin(2*eta_i)*sin(2*eps)` and `sin(2*eps) cancels across every finite distinct leaf`.
- `geo_union_rule_k_leaves_v0_julia.jl` mirrors the formula as `rho_i/sum_j rho_j, with rho_i=sin(2eta_i)`.

Recomputation:

- Centered band mass for leaf `eta_i`: integral of `sin(2 eta)` over `[eta_i-eps, eta_i+eps]` is `sin(2*eta_i)*sin(2*eps)`.
- The common factor cancels across finite distinct leaves, giving `w_i = sin(2 eta_i) / sum_j sin(2 eta_j)`.
- The packet-local validator passed.

k=2 parent reduction:

- Computed row hash: `e731c4790eef9d9fa5625ca7f10adb7d6a2f5e6ef63fc95931853abab047088e`.
- Parent row hash: `e731c4790eef9d9fa5625ca7f10adb7d6a2f5e6ef63fc95931853abab047088e`.
- Stable JSON byte-exact check: pass.

## Q2 - k=3/k=4 exact shell weights

Pass.

Hand recomputation for committed shells:

- Shell densities for `(pi/12, pi/6, pi/4, pi/3)` are `(1/2, sqrt(3)/2, 1, sqrt(3)/2)`.
- k=3 weights for `(pi/12, pi/6, pi/4)` are:
  - `pi/12`: `1/2 - sqrt(3)/6`
  - `pi/6`: `-1/2 + sqrt(3)/2`
  - `pi/4`: `1 - sqrt(3)/3`
- k=4 weights for `(pi/12, pi/6, pi/4, pi/3)` are:
  - `pi/12`: `-1 + 2*sqrt(3)/3`
  - `pi/6`: `2 - sqrt(3)`
  - `pi/4`: `-2 + 4*sqrt(3)/3`
  - `pi/3`: `2 - sqrt(3)`

The equal-density pair is handled correctly: `pi/6` and `pi/3` both have density `sqrt(3)/2` and equal weight `2 - sqrt(3)`.

## Q3 - bracketing row

Pass. Finding: agreement, not a bracketing sensitivity, at the measure level when group mass is summed.

Packet source computes all three routes:

- Direct 3-leaf weights.
- `((1 union 2) union 3)` with group mass `rho12=rho1+rho2`.
- `(1 union (2 union 3))` with group mass `rho23=rho2+rho3`.

Recomputed defects:

- `left_minus_direct = [0, 0, 0]`
- `right_minus_direct = [0, 0, 0]`
- direct, left, and right `cos(2 eta)` values agree and simplify to `-1/2 + sqrt(3)/2`.

No smoothing found: the packet states the condition honestly as agreement only when the iterated union carries summed group mass. It also names the failure mode: a gap would require erasing group mass or double-counting sets.

## Q4 - degenerate rows

Pass.

Repeated leaf:

- Input row: `["pi/6", "pi/6", "pi/4"]`.
- Packet collapses repeated eta before weighting because the union is a set.
- Naive duplicate-list weights are noncanonical and produce defect `9/4 - 5*sqrt(3)/4`.
- Collapsed unique weights match the parent two-leaf row: `pi/6 -> -3 + 2*sqrt(3)`, `pi/4 -> 4 - 2*sqrt(3)`.

Vanishing boundary leaf:

- Input row: `["0", "pi/6", "pi/4"]`.
- Recomputed boundary weights: `0`, `-3 + 2*sqrt(3)`, `4 - 2*sqrt(3)`.
- The eta `0` leaf has zero union weight.

Equal weights control:

- Equal k=3 value: `1/6 + sqrt(3)/6`.
- Correct k=3 value: `-1/2 + sqrt(3)/2`.
- Equal-minus-correct defect: `2/3 - sqrt(3)/3`, nonzero.
- z3, cvc5, and Julia Z3 all mark equal weights as failing.

## Q5 - mortality boundary

Pass, scoped a.e. rather than pointwise.

Quoted source:

- `finite_k_naive_conditioning_denominator`: `0 for every finite k because finite union of fixed-eta leaves has S3 measure zero`.
- `definable_again_boundary`: `continuum_all_eta_in_[0,pi/2]; union of all shells equals S3 a.e.`
- `mode4_to_free_boundary`: finite-k rule converges only as a weighted eta integral, not naive finite-union conditioning.

Recomputed integrals:

- `integral sin(2 eta) d eta` over `[0, pi/2]` = `1`.
- `integral cos(2 eta) sin(2 eta) d eta` = `0`.
- `integral cos(2 eta)^2 sin(2 eta) d eta` = `1/3`.

This supports the full-measure continuum boundary as recovery of the unconditioned/FREE eta distribution a.e.; it does not make any finite k union a positive-measure conditioning event.

## Q6 - standard checks

Pass with caveats `CAVEAT_LOAD_BEARING_ALIGNMENT_METADATA` and `CAVEAT_PYTHON_SIDECAR_LABELED_JAX`.

Fresh commands run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_union_rule_k_leaves_v0/geo_union_rule_k_leaves_v0_exact_strength_validator.py
```

Result: `ok=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_union_rule_k_leaves_v0/results/geo_union_rule_k_leaves_v0_envelope_results.json
```

Result: `ok=true`.

Independent recomputation checks:

- z3 positive negated identity: `unsat`.
- z3 erased middle weight formula: `sat`.
- z3 equal-weights identity: `unsat`.
- cvc5 positive negated identity: `unsat`.
- Julia active project: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`.
- Julia Symbolics normalization defect: `0`.
- Julia Z3 positive negated identity: `unsat`.

Parent lineage:

- All file hashes resolve against current files.
- JSON-pointer hashes for parent pin and parent R3 row resolve when pointer-aware stable JSON hashing is used.
- Parent `geo_nested_disintegration_v0` is committed at `b79036b1f`.

Other standard checks:

- Honest mode: `julia_symbolics_plus_python_sympy_smt_diagnostic`.
- Real Julia leg: yes, `Symbolics` + `Z3.jl` under `system_v5/julia_carrier`.
- Capability receipts: Python `sympy 1.14.0`, `z3 4.16.0`, `cvc5 1.3.3`; Julia `Symbolics 7.26.0`, `Z3 1.0.4`.
- Seeds recorded: `2026061102` for Python and Julia; Riemann midpoint Ns `[4, 8, 16, 32, 64]`.
- One-to-one claim tool calls: validator passes; aggregate tools are `sympy`, `z3`, `cvc5`, `Symbolics`, `Z3`.
- Fixture wording: no live fixture/mock/dummy wording found in packet source; `asserted_precomputed_boolean=false` is present on solver rows.
- Ceilings preserved: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Q7 - closure / unfencing

This does unfence finite k-leaf union conditioning for multi-shell ratchet cards under the following conditions:

- finite k, including the committed exact k=3 and k=4 shell rows;
- distinct fixed-eta Hopf leaves, with repeated leaves collapsed as sets before weighting;
- eta leaves are nonboundary;
- bracketing carries summed group mass;
- the cited use stays at the finite weighted-disintegration level and carries the parent `geo_nested_disintegration_v0` lineage hashes;
- the consumer keeps the same ceiling: `scratch_diagnostic`, no formal admission, no bridge/axis/manifold/physics promotion.

What stays fenced:

- transverse intersections and non-leaf conditioning;
- boundary leaves such as `eta=0` and `eta=pi/2`;
- naive finite-k positive-measure conditioning or finite-k FREE replacement;
- arbitrary measurable-function measure theory beyond the declared symbolic/diagnostic rows;
- bridge, axis-level, manifold-completion, physics, or canonical-admission claims.

Final ceiling: `scratch_diagnostic`; finite multi-shell stack cards may cite the k-leaf union rule only inside the conditions above.
