# Fresh Audit Verdict - geo_lifted_coord_families_v0

Scope: read-only audit of `system_v6/sims/geo_lifted_coord_families_v0/`, except this `audit_verdict.md`. Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`. HEAD during audit: `b02a843ff`.

Important status: the packet directory is untracked in this checkout (`git status --short -- system_v6/sims/geo_lifted_coord_families_v0` reports `?? system_v6/sims/geo_lifted_coord_families_v0/`). The consumed rung result JSONs for n=3/4/5 are tracked by Git.

## Verdict

**PARTIAL PASS, NOT FULL G7-LIFTED CLOSURE under the stated audit questions.**

The core mathematical route is genuine for n=3/4/5: the JAX lane and envelope consume committed lifted rung site exports, hash-bind those source JSONs, build W-site weighted amplitudes from exported `eta_i`, recover equal-eta anchors, carry a B1-consistent phase-erased/weights-survive quotient row, and derive z3/cvc5 product-boundary polarity rows.

I do **not** close G7-LIFTED fully because Q5 and Q6 have material receipt gaps:

- **CAVEAT C1 - missing permutation and flat-family controls:** mutation reruns exist, but I found no packet row or validator requirement for "permute -> permutes" or "flat-family detected".
- **CAVEAT C2 - strict one-to-one tool-call receipt not met:** JAX has 3 manifest tools and 3 tool calls, but Julia has 3 manifest entries and 2 tool calls; PyTorch has 4 manifest entries and 2 tool calls, with `z3/cvc5` grouped.
- **CAVEAT C3 - Julia capability helper gap:** `verify_load_bearing_has_capability_probe.py` on the Julia source returned `error: no_tool_integration_depth`, even though the Julia result JSON contains `TOOL_INTEGRATION_DEPTH`.
- **CAVEAT C4 - packet untracked:** the audited packet itself is not committed in this checkout.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no canonical lifted coordinate family, no stage closure, no n8 result, no formal admission.

## Q1 - Rung Coordinates Genuine

**PASS for the JAX lifted source-binding route.** The constructor consumes actual exported per-site eta values from committed n=3/4/5 JAX rung result JSONs, not synthetic eta vectors.

Source quote and path:

- `geo_lifted_coord_families_v0_common.py:32-38` defines `LIFTED_RESULTS` as the three engine result paths under `stage_lifted_spinor_shell_n{n}_v0/results/...`.
- `geo_lifted_coord_families_v0_common.py:236-253` loads the JSON, reads `payload["rows"]["P2_support_object"]["sites"]`, and records `json_pointer: "/rows/P2_support_object/sites"`.
- `geo_lifted_coord_families_v0_common.py:100-108` passes those `sites` into `site_eta_vector(sites)`, squares the etas, and calls `w_site_weighted_amplitudes_from_eta`.
- `geo_lifted_coord_families_v0_common.py:128-130` labels the source as `rows.P2_support_object.sites[*].eta from committed lifted rung result`.

Commit/hash check:

- `git ls-files --error-unmatch` succeeded for the three JAX source result JSONs.
- `git cat-file -e HEAD:system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json` succeeded.
- Recomputed n=4 JAX source hash: `8ba4faf424e6f5a4a68d0220f3b3b658cc860ab643c7f3387ef8ea169282da3f`, matching the envelope's `lifted_source_exports["4"].result_sha256`.

The exported n=4 eta row in the committed source is:

```text
[0.314159265359, 0.628318530718, 0.942477796077, 1.256637061436]
```

## Q2 - Executable Constructor

**PASS.** The constructor maps per-site eta to a W-site amplitude vector in the Python/JAX shared route, Julia route, and PyTorch route.

Source quote and path:

- Python/JAX shared: `geo_lifted_coord_families_v0_common.py:79-97` squares `eta_vec`, normalizes probabilities, emits W basis states, and emits `amplitudes`.
- Julia: `geo_lifted_coord_families_v0_julia.jl:42-53` computes `weights = eta_vec .^ 2`, `probabilities = weights ./ total`, and `amplitudes = sqrt.(probabilities)`.
- PyTorch: `geo_lifted_coord_families_v0_pytorch.py:53-55` computes `weights = eta_vec.square()` and normalizes by `torch.sum(weights)`.

Hand recomputation from the committed n=4 JAX export:

```text
eta = [0.314159265359, 0.628318530718, 0.942477796077, 1.256637061436]
weights = eta^2 = [0.09869604401090659, 0.39478417604362637, 0.8882643960981592, 1.5791367041745055]
sum(weights) = 2.9608813203271978
p = weights / sum = [1/30, 2/15, 3/10, 8/15]
amplitudes = sqrt(p) = [0.18257418583505536, 0.3651483716701107, 0.5477225575051661, 0.7302967433402214]
```

Single-site entropy for q0:

```text
S(q0) = -(1/30) log(1/30) - (29/30) log(29/30)
      = 0.1461447460085638
```

This matches `geo_lifted_coord_families_v0_jax_results.json` for n=4 q0.

## Q3 - Anchor Recovery

**PASS.** Equal-eta limits recover the committed W_n single-site anchor values.

Source quote and path:

- `geo_lifted_coord_families_v0_common.py:138-150` constructs the equal-eta anchor with `[1.0 for _ in range(n)]`, expects `1/n`, computes `entropy_binary_float(1.0 / n)`, and checks `committed_rung_anchor_recovered`.
- `geo_lifted_coord_families_v0_common.py:183-219` builds the GHZ-W interpolation row and records `phase_erased: True`, `weights_survive: True`, `ghz_anchor_pass`, and `w_anchor_pass`.

Numbers checked:

```text
n=3: H(1/3) = 0.6365141682948128
n=4: H(1/4) = 0.5623351446188083
n=5: H(1/5) = 0.5004024235381879
```

The n=4 committed rung anchor is `W_4_single_site_entropy=0.562335144619`, matching the equal-eta constructor value within displayed precision.

The GHZ-W interpolation quotient row is consistent with committed B1 at this surface: the row says phase is erased on the entropy quotient surface while `sin(eta)^2` and W-site weights survive.

## Q4 - Separability Boundary

**PASS for solver-derived product-boundary polarity per rung.** The semantics are narrow: W-site weighted pure state is product only at a one-hot weight boundary; the committed eta exports are interior non-boundary rows.

Source quote and path:

- `geo_lifted_coord_families_v0_jax.py:44-67` builds z3 rows from actual exported `eta_i^2` weights and checks actual boundary, one-hot positive control, and invalid zero-vector control.
- `geo_lifted_coord_families_v0_jax.py:70-100` mirrors the same boundary rows in cvc5.
- `geo_lifted_coord_families_v0_jax.py:108-119` requires actual rows `unsat`, positive controls `sat`, and invalid-zero controls `unsat` for both solvers.

Solver results:

```text
n=3 z3/cvc5: actual exported eta on product boundary = unsat; one-hot positive control = sat; invalid zero vector = unsat
n=4 z3/cvc5: actual exported eta on product boundary = unsat; one-hot positive control = sat; invalid zero vector = unsat
n=5 z3/cvc5: actual exported eta on product boundary = unsat; one-hot positive control = sat; invalid zero vector = unsat
```

These are can-fail polarity flips, not label-only checks.

## Q5 - Site-Resolved Controls

**PARTIAL / FAILS stated control coverage.**

Passing part: mutation controls are full reruns. `geo_lifted_coord_families_v0_common.py:153-180` mutates exactly one exported eta by factor `1.1`, reruns `w_site_weighted_amplitudes_from_eta`, recomputes entropies, checks the changed eta site, marks `entropy_responds_at_mutated_site`, and sets `gate_passed_after_mutation: False`.

n=4 q0 example:

```text
base p = [0.03333333333333333, 0.13333333333333333, 0.3, 0.5333333333333333]
q0-mutated p = [0.04005296259516717, 0.132406487917908, 0.29791459781529295, 0.529625951671632]
q0 entropy delta = 0.02196768319557091
changed_eta_sites = ["q0"]
gate_passed_after_mutation = false
```

Failing coverage: no source/result row was found for:

- permutation control: `permute -> permutes`;
- flat-family detection;
- can-fail gates for permutation and flat-family rows.

I independently recomputed that a permutation and flat-family check would be executable for n=4:

```text
reverse-eta probabilities = [0.5333333333333333, 0.3, 0.13333333333333333, 0.03333333333333333]
permutation matches reversed base probabilities = true
flat eta probabilities = [0.25, 0.25, 0.25, 0.25]
flat-family detectable = true
```

But those are audit-side recomputations, not packet receipts. They do not close the packet gap.

## Q6 - Standard / Receipts

**MIXED.**

Passes:

- Mode is honest: envelope `mode=QUOTIENTED`; `engine_contract.mode=all_three_full_sims`.
- Ceiling is honest: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Seeds are present: `geo_lifted_coord_families_seed_v0_hash_bound_n3_n4_n5`.
- No peer-result reads: each engine record says `reads_peer_result=false`; the envelope gates `no_peer_result_reads=true`.
- No n8 consumed: `geo_lifted_coord_families_v0_common.py:287` says `no n8 lane read`; `geo_lifted_coord_families_v0_common.py:320` and `geo_lifted_coord_families_v0_envelope.py:85-89` gate absence of `stage_lifted_spinor_shell_n8`; packet validator line 42 requires it.
- Strict validators passed:
  - `geo_lifted_coord_families_v0_exact_strength_validator.py` returned `{"ok": true}`.
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed ...envelope_results.json` returned `{"ok": true}`.
  - JAX and PyTorch capability-probe checks returned no violations.

Gaps:

- Julia source capability-probe helper returned `{"error": "no_tool_integration_depth"}` for `geo_lifted_coord_families_v0_julia.jl`, despite the Julia result JSON carrying `TOOL_INTEGRATION_DEPTH`.
- Strict one-to-one `TOOL_MANIFEST` to `tool_calls` is not satisfied:
  - JAX: manifest 3, tool calls 3.
  - Julia: manifest 3, tool calls 2.
  - PyTorch: manifest 4, tool calls 2.
- I found no fixture wording in the packet, but the absence check is not a packet-local validator row.
- No cross-run parity is claimed as a result; the envelope uses cross-engine divergence for this packet's three lanes, with `max_divergence=2.220446049250313e-16`.

## Q7 - Closure / Extension

Under the exact bar in this prompt, **this does not fully close G7-LIFTED for n=3/4/5**. It closes the mathematical core of the lifted coordinate-family caveat, but leaves closure blocked on missing permutation/flat-family controls and receipt-shape gaps.

What n=6/7/8 would need under the trail-by-one pattern:

1. Committed `stage_lifted_spinor_shell_n6_v0`, `n7`, and `n8` result JSONs with exported `rows.P2_support_object.sites[*].eta`.
2. Extension rows in this packet or successor packets consuming those exact rung exports read-only, with source hashes and Git-tracked source-result checks.
3. Per-rung W-site constructor rows: exported eta -> eta squared weights -> normalized probabilities -> amplitudes -> single-site entropies.
4. Equal-eta anchor rows for W_6, W_7, and W_8:
   - n=6: `H(1/6) = 0.45056120886630463`
   - n=7: `H(1/7) = 0.410116318288409`
   - n=8: `H(1/8) = 0.37677016125643675`
5. z3/cvc5 product-boundary rows for each rung with actual `unsat`, one-hot `sat`, invalid-zero `unsat`.
6. Site-resolved controls that include mutation, permutation, and flat-family detection, with each row able to fail and covered by the packet validator.
7. One-to-one load-bearing tool-call receipts or a documented validator-normalized exception for supportive/grouped tool entries.

## Commands / Checks Run

```text
git status --short -- system_v6/sims/geo_lifted_coord_families_v0 system_v6/receipts/audit_bar_calibration_20260610.md
git rev-parse --short HEAD
git ls-files --error-unmatch system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_jax_results.json system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_jax_results.json
git cat-file -e HEAD:system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json
shasum -a 256 system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_exact_strength_validator.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_jax.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_pytorch.py
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_julia.jl
```

No `git add` or `git commit` was run.

## Builder-Hardening Addendum - 2026-06-11

Status: bounded builder hardening only. The audit verdict above remains **PARTIAL PASS, NOT FULL G7-LIFTED CLOSURE** pending fresh re-audit.

Closed in the builder packet:

- **B1 CONTROLS closed:** each rung n=3/4/5 now carries full-rerun controls for mutate-one-eta, site permutation, and flat-family detection. The permutation control reruns the W-site constructor on a permuted exported eta vector and checks that probabilities and per-site entropies permute accordingly. The flat-family control reruns the constructor on a coordinate-independent eta family and requires detection as uncoupled. Both controls state failure semantics and are enforced by the packet validator.
- **B2 RECEIPT SHAPE closed:** load-bearing `tool_calls` are now strict one-to-one with `TOOL_INTEGRATION_DEPTH == load_bearing` tools in every leg, using the `{tool, qualified_api, input_object, output_object, positive_case, negative_control, boundary_case, demotion_condition, gates}` shape. The packet validator now fails if the one-to-one mapping or strict field shape drifts. The Julia capability-helper parsing gap is closed by a source-level `TOOL_INTEGRATION_DEPTH` constant in `geo_lifted_coord_families_v0_julia.jl`.

Full reruns completed:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_jax.py
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_pytorch.py
exit 0

julia --project=system_v5/julia_carrier system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_julia.jl
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_envelope.py
exit 0
```

Final validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_exact_strength_validator.py
{"errors": [], "ok": true, "result_json": "system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json"}
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json
{"ok": true, "result_json": "system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json"}
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_julia.jl
load_bearing_tools: Symbolics ok, Z3 ok; violations: []
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_jax.py
load_bearing_tools: sympy ok, z3 ok, cvc5 ok; violations: []
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_pytorch.py
load_bearing_tools: torch ok, torch.func ok, z3 ok, cvc5 ok; violations: []
exit 0
```

Exact/control-row stability check:

```text
0ec3ad5120c41bc3f798872c0eab92bc13e18509334099f2af0a8e862c8b611d  before
0ec3ad5120c41bc3f798872c0eab92bc13e18509334099f2af0a8e862c8b611d  after
cmp exit 0
```

No `git add` or `git commit` was run during hardening.

## Focused Re-Audit Addendum - 2026-06-11

Scope: B1+B2 hardening only. I did not re-litigate the accepted core source-binding math for n=3/4/5. Read-only except this addendum; no `git add` or `git commit` was run.

**B1 CLOSED.** The packet now carries per-rung mutation, site-permutation, and flat-family controls, and the packet-local validator requires them. Recomputed n=5 permutation case:

```text
permutation_indices = [4, 3, 2, 1, 0]
base_probabilities = [0.018181818181795456, 0.07272727272718182, 0.16363636363615908, 0.29090909090928285, 0.45454545454558076]
rerun_probabilities = [0.45454545454558076, 0.29090909090928285, 0.16363636363615908, 0.07272727272718182, 0.018181818181795456]
expected_permuted_probabilities = [0.45454545454558076, 0.29090909090928285, 0.16363636363615908, 0.07272727272718182, 0.018181818181795456]
rerun_entropies = [0.6890092384766815, 0.6029636624164108, 0.4456509046044218, 0.26063709953369085, 0.09087612133291084]
expected_permuted_entropies = [0.6890092384766815, 0.6029636624164108, 0.4456509046044218, 0.26063709953369085, 0.09087612133291084]
probability_vector_permuted_accordingly = True
entropy_vector_permuted_accordingly = True
full_rerun_not_json_edit = True
failure_semantics = fails if rerunning the constructor on the permuted exported eta vector does not produce the correspondingly permuted per-site probability and entropy vectors
```

Flat-family detection has real failure semantics:

```text
n=5 flat_probabilities = [0.2, 0.2, 0.2, 0.2, 0.2]
n=5 probability_spread = 0.0
n=5 entropy_spread = 0.0
coordinate_independent_family_detected = True
detected_as_uncoupled = True
failure_semantics = fails if a flat coordinate-independent eta family is not detected as uncoupled, or if rerun probabilities/entropies retain site-coordinate dependence
hypothetical coupled flat probability_spread = 0.04030710172744725
hypothetical coupled flat entropy_spread = 0.0529538708612155
hypothetical detected_as_uncoupled = False
```

The value that flips under coupling is `detected_as_uncoupled` / `coordinate_independent_family_detected`, driven by `probability_spread` or `entropy_spread` becoming nonzero above the `1e-15` gate.

**B2 CLOSED.** Function-level `tool_calls` are one-to-one with load-bearing tools in every leg:

```text
jax: load_bearing=3 ['cvc5', 'sympy', 'z3']; tool_calls=3 ['sympy', 'z3', 'cvc5']; one_to_one=True
julia: load_bearing=2 ['Symbolics', 'Z3']; tool_calls=2 ['Symbolics', 'Z3']; one_to_one=True
pytorch: load_bearing=4 ['cvc5', 'torch', 'torch.func', 'z3']; tool_calls=4 ['torch', 'torch.func', 'z3', 'cvc5']; one_to_one=True
```

Capability helpers were rerun and all exited 0:

```text
verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_jax.py
load_bearing_tools: sympy ok, z3 ok, cvc5 ok; violations: []
EXIT:0

verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_pytorch.py
load_bearing_tools: torch ok, torch.func ok, z3 ok, cvc5 ok; violations: []
EXIT:0

verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_julia.jl
load_bearing_tools: Symbolics ok, Z3 ok; violations: []
EXIT:0
```

Exact/control row stability through hardening is supported by the hardening hash check already in this audit file:

```text
0ec3ad5120c41bc3f798872c0eab92bc13e18509334099f2af0a8e862c8b611d  before
0ec3ad5120c41bc3f798872c0eab92bc13e18509334099f2af0a8e862c8b611d  after
cmp exit 0
```

Fresh validators are green:

```text
geo_lifted_coord_families_v0_exact_strength_validator.py
{"errors": [], "ok": true, "result_json": "system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json"}
EXIT:0

validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json
{"ok": true, "result_json": "system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json"}
EXIT:0
```

What n=6/7/8 still need: committed lifted rung result JSONs with exported `rows.P2_support_object.sites[*].eta`; read-only source-hash binding to those exports; W-site constructor rows; equal-eta anchors; z3/cvc5 product-boundary rows; mutation, permutation, and flat-family controls that can fail and are validator-covered; and one-to-one function-level load-bearing tool-call receipts.

Ceiling remains `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no canonical lifted coordinate family, no stage closure, no n8 result, and no formal admission.

Conclusion: G7-LIFTED closure for n=3/4/5 **EARNED** under the original B1+B2 audit bar.

## Builder-Extension Addendum - 2026-06-11 - n6/n7/n8 trail-by-one

Status: bounded builder extension only. The committed n=3/4/5 EARNED re-audit above stands; this addendum records the extension rows for n=6/7/8 on the same coordinate-parameterized family surface. No trend, scaling, closure, canonical, promotion, or formal-admission claim is made.

Scope changed:

- `geo_lifted_coord_families_v0_common.py` now consumes committed, hash-bound lifted rung exports for n=3/4/5/6/7/8 through `RUNG_NS = (3, 4, 5, 6, 7, 8)`.
- The W-site-weighted constructor remains the same executable per-site eta rule: `w_i=eta_i^2; p_i=w_i/sum_j w_j`.
- The GHZ-W interpolation rows remain on the same entropy quotient surface: phase erased, W-site weights survive.
- The packet validator now requires lifted source, family, control, and solver rows for all rungs n=3 through n=8.
- n3/4/5 row subsets were checked byte-stable by JSON canonical subset hashes after the full reruns:

```text
jax      609ed48717a61d0bd5bd2ae4fe3a2574fb9e39b15c103c5fc3387d7475fa0c85 MATCH
julia    0acf2d31b0093e8a984524837db6bb582c619c9012dc9d0e8263264e6c1d6c45 MATCH
pytorch  9749db97c0c1616168e365d673e2f30644b044501dd400b658a39db8acb6d987 MATCH
envelope c5c3b2813c931c333eaaa0596a21461a18413d0ee729fd2ec85e03c08cfb3c57 MATCH
```

n6/n7/n8 source binding and anchor rows:

```text
n6 source sha256 881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571
n6 sites 6
n6 equal-eta anchor H(1/6) = 0.45056120886630463
n6 z3/cvc5 actual/one-hot/zero = unsat/sat/unsat
n6 permutation, entropy-permutation, flat-family controls = true/true/true

n7 source sha256 1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc
n7 sites 7
n7 equal-eta anchor H(1/7) = 0.41011631828840894
n7 z3/cvc5 actual/one-hot/zero = unsat/sat/unsat
n7 permutation, entropy-permutation, flat-family controls = true/true/true

n8 source sha256 f7ded95c7fb77973cfb93d8ee329d43e4ec70ffa21c0966b03f3b4cec2fe4c1d
n8 sites 8
n8 equal-eta anchor H(1/8) = 0.37677016125643675
n8 z3/cvc5 actual/one-hot/zero = unsat/sat/unsat
n8 permutation, entropy-permutation, flat-family controls = true/true/true
```

Full reruns completed:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_jax.py
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_pytorch.py
exit 0

julia --project=system_v5/julia_carrier system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_julia.jl
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_envelope.py
exit 0
```

Final validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_lifted_coord_families_v0/geo_lifted_coord_families_v0_exact_strength_validator.py
{
  "errors": [],
  "ok": true,
  "result_json": "system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json"
}
exit 0

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json
{
  "ok": true,
  "result_json": "system_v6/sims/geo_lifted_coord_families_v0/results/geo_lifted_coord_families_v0_envelope_results.json"
}
exit 0
```

Capability helpers:

```text
verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_jax.py
load_bearing_tools: sympy ok, z3 ok, cvc5 ok; violations: []
exit 0

verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_pytorch.py
load_bearing_tools: torch ok, torch.func ok, z3 ok, cvc5 ok; violations: []
exit 0

verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_julia.jl
load_bearing_tools: Symbolics ok, Z3 ok; violations: []
exit 0
```

Strict one-to-one load-bearing tool-call receipt status:

```text
jax: load_bearing=['cvc5', 'sympy', 'z3']; tool_calls=['cvc5', 'sympy', 'z3']; one_to_one=True
julia: load_bearing=['Symbolics', 'Z3']; tool_calls=['Symbolics', 'Z3']; one_to_one=True
pytorch: load_bearing=['cvc5', 'torch', 'torch.func', 'z3']; tool_calls=['cvc5', 'torch', 'torch.func', 'z3']; one_to_one=True
```

Combined envelope summary:

```text
all_pass true
rungs ['3', '4', '5', '6', '7', '8']
max_divergence 2.220446049250313e-16
divergence rows 33
```

No `git add` or `git commit` was run during this builder extension.

## Focused Re-Audit Addendum - 2026-06-11 - n6/n7/n8 extension rows

Scope: read-only re-audit of the new n6/n7/n8 rows only. All prior verdicts and addenda above stand.

Hash/source binding checked per rung:

```text
n6 source sha256=881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571
n7 source sha256=1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc
n8 source sha256=f7ded95c7fb77973cfb93d8ee329d43e4ec70ffa21c0966b03f3b4cec2fe4c1d
```

The executable constructor consumes each rung's actual exported per-site etas. One quoted source vector:

```text
n8 eta=[0.174532925199,0.349065850399,0.523598775598,0.698131700798,0.872664625997,1.047197551197,1.221730476396,1.396263401595]
```

Anchor recovery checked by hand:

```text
n6 H(1/6)=0.45056120886630463, stored=0.45056120886630463
n7 H(1/7)=0.41011631828840894, stored=0.41011631828840894
n8 H(1/8)=0.37677016125643675, stored=0.37677016125643675
```

Controls checked as full reruns with failure semantics:

```text
n6 mutate q0: gate_passed_after_mutation=false; entropy_responds_at_mutated_site=true; full_rerun_not_json_edit=true
n6 site permutation: probability_vector_permuted_accordingly=true; entropy_vector_permuted_accordingly=true; full_rerun_not_json_edit=true
n6 flat family: detected_as_uncoupled=true; probability_spread=0.0; entropy_spread=0.0

n7 mutation/permutation/flat controls: present with the same full-rerun gates and pass statuses
n8 mutation/permutation/flat controls: present with the same full-rerun gates and pass statuses
```

Solver-derived separability boundaries checked:

```text
n6 z3 actual/one-hot/zero = unsat/sat/unsat; cvc5 actual/one-hot/zero = unsat/sat/unsat
n7 z3 actual/one-hot/zero = unsat/sat/unsat; cvc5 actual/one-hot/zero = unsat/sat/unsat
n8 z3 actual/one-hot/zero = unsat/sat/unsat; cvc5 actual/one-hot/zero = unsat/sat/unsat
```

n3/n4/n5 byte-stability checked:

```text
JAX n3/n4/n5 row subsets: MATCH_HEAD
Julia n3/n4/n5 row subsets: MATCH_HEAD
PyTorch n3/n4/n5 row subsets: MATCH_HEAD
Envelope n3/n4/n5 row subsets: MATCH_HEAD
```

Strict one-to-one tool-call receipts checked:

```text
jax load_bearing=['cvc5','sympy','z3']; tool_calls=['cvc5','sympy','z3']; one_to_one=true
julia load_bearing=['Symbolics','Z3']; tool_calls=['Symbolics','Z3']; one_to_one=true
pytorch load_bearing=['cvc5','torch','torch.func','z3']; tool_calls=['cvc5','torch','torch.func','z3']; one_to_one=true
```

Fresh validators and capability helpers:

```text
geo_lifted_coord_families_v0_exact_strength_validator.py -> {"errors":[],"ok":true}; EXIT:0
validate_three_engine_sim_result.py --require-pytorch --strict-source-backed ...geo_lifted_coord_families_v0_envelope_results.json -> {"ok":true}; EXIT:0
verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_jax.py -> sympy ok, z3 ok, cvc5 ok, violations=[]; EXIT:0
verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_pytorch.py -> torch ok, torch.func ok, z3 ok, cvc5 ok, violations=[]; EXIT:0
verify_load_bearing_has_capability_probe.py --sim geo_lifted_coord_families_v0_julia.jl -> Symbolics ok, Z3 ok, violations=[]; EXIT:0
```

Conclusion: n6/n7/n8 extension rows EARNED; full G7-LIFTED status across n3..n8 is EARNED only for this packet's lifted coordinate-family row scope; ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, no canonical lifted coordinate family, no stage closure, and no formal admission.
