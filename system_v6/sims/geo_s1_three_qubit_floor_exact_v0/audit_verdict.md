# Fresh Audit Verdict: geo_s1_three_qubit_floor_exact_v0

Scope: read-only audit of `system_v6/sims/geo_s1_three_qubit_floor_exact_v0/`, except this verdict file.

Inputs checked:

- `build_card.md`
- `geo_s1_three_qubit_floor_exact_v0_julia.jl`
- `geo_s1_three_qubit_floor_exact_v0_jax.py`
- `geo_s1_three_qubit_floor_exact_v0_pytorch.py`
- `geo_s1_three_qubit_floor_exact_v0_envelope.py`
- all four result JSON files under `results/`
- blind sheet: `/tmp/s1_3q_blind_expected_20260610.md`

Fresh commands run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json
```

Result: `{"ok": true}`.

## T1. Genuinely Symbolic

Verdict: FAIL for the full two-CAS exactness claim; PASS only for the sympy leg and the narrower Julia phase/gamma receipts.

Source quotes:

- Build card requires: `CAS-exact (two independent CAS: Symbolics.jl + sympy), no float.` (`build_card.md:9`)
- Julia advertises: `"cas" => "Symbolics.jl plus exact Rational state contractions"` (`geo_s1_three_qubit_floor_exact_v0_julia.jl:149`)
- Julia hard-codes GHZ/W/product reduced density matrices and entropy strings in `reduced_density_receipts()` (`geo_s1_three_qubit_floor_exact_v0_julia.jl:123-154`), e.g. `"rho_A" => density_matrix_strings([[2//3, 0//1], [0//1, 1//3]])` and `"entropy_A" => "ln(3) - (2//3)*ln(2)"`.
- Julia only puts `Y1`, `Y2`, `Y4`, `Y6`, and `Y7` into receipts; there is no Julia `Y3` tau receipt (`geo_s1_three_qubit_floor_exact_v0_julia.jl:258-269`).
- Sympy actually constructs states and contracts partial traces: `states = {"GHZ": state_vector(...), "W": state_vector(...), ...}` and `rhos = {label: reduced_density(psi, keep) ...}` (`geo_s1_three_qubit_floor_exact_v0_jax.py:146-164`).

Adjudication: the sympy leg is a real exact CAS derivation for densities/entropies/tau. The Julia leg uses Symbolics for phase erasure (`geo_s1_three_qubit_floor_exact_v0_julia.jl:157-169`) and exact integer matrices for Cl(6), but its named-state entropy receipt is prefilled exact rationals/strings, and tau is absent. This is not "two independent CAS exact arithmetic end-to-end" for Y2/Y3.

Float/tolerance audit: no `isclose`, tolerance, NumPy, or float comparison appears on the claim path. The sympy leg uses `sp.N(item)` only as an eigenvalue sort key (`geo_s1_three_qubit_floor_exact_v0_jax.py:163`), not as the equality check; still, it is a non-exact ordering helper inside an exact receipt and should be removed in a future exactness-clean pass.

## T2. Tau Route

Verdict: PASS for the used route; cross-route check agrees.

Source quotes:

- Builder route: `"method": "Coffman-Kundu-Wootters 3-tangle via Cayley hyperdeterminant"` (`results/geo_s1_three_qubit_floor_exact_v0_jax_results.json:248-253`).
- Source implements the Cayley hyperdeterminant monomials in `hyperdeterminant()` (`geo_s1_three_qubit_floor_exact_v0_jax.py:183-195`) and computes `tau_three()` as `4 * hyperdeterminant(coeffs)` (`geo_s1_three_qubit_floor_exact_v0_jax.py:198-202`).
- Blind sheet expected hyperdeterminant intermediates: GHZ `d1 = 1/4, d2 = 0, d3 = 0`; W `d1 = 0, d2 = 0, d3 = 0` (`/tmp/s1_3q_blind_expected_20260610.md`).

Spot check: for GHZ, only `a000` and `a111` are nonzero, so `d1 = (1/2)(1/2) = 1/4`, `d2 = 0`, `d3 = 0`, and `tau = 1`. For W, all hyperdeterminant monomials contain at least one zero coefficient, so `d1 = d2 = d3 = 0`, `tau = 0`.

Cross-route recomputation not used by builder: CKW concurrence route for W gives `rho_A = diag(2/3, 1/3)`, `det(rho_A)=2/9`, `C_A(BC)^2=8/9`, `C_AB^2=4/9`, `C_AC^2=4/9`, hence `tau(W)=8/9-4/9-4/9=0`.

Named gap: the result JSON reports tau values but not `d1/d2/d3` intermediates. The source is enough to audit the route, but the receipt is thinner than the blind sheet's route-level derivation.

## T3. Cl(6) Exact-Integer

Verdict: PASS.

Source quotes:

- Julia matrix type is exact Gaussian integer: `Matrix{Complex{Int}}` (`geo_s1_three_qubit_floor_exact_v0_julia.jl:64-71`).
- Julia checks all ordered pairs: `for i in 1:6, j in 1:6` and compares the anticommutator delta to exact integer targets (`geo_s1_three_qubit_floor_exact_v0_julia.jl:184-189`).
- Sympy builds exact Pauli matrices (`geo_s1_three_qubit_floor_exact_v0_jax.py:222-242`), computes all anticommutation deltas (`geo_s1_three_qubit_floor_exact_v0_jax.py:294-301`), and computes the span rank exactly with `sp.Matrix.hstack(*vectors).rank()` (`geo_s1_three_qubit_floor_exact_v0_jax.py:304-312`).
- PyTorch uses exact integer-pair tensors: `torch.tensor(real, dtype=torch.int64)` and stores `[real, imag]` pairs (`geo_s1_three_qubit_floor_exact_v0_pytorch.py:61-64`).
- PyTorch all-pair anticommutation loop is exact integer tensor arithmetic (`geo_s1_three_qubit_floor_exact_v0_pytorch.py:138-148`).
- Corrupted gamma control fires in PyTorch with `delta_nonzero_entries` and `all_36_pairs_pass_after_corruption: false` (`geo_s1_three_qubit_floor_exact_v0_pytorch.py:199-203`; result at `results/geo_s1_three_qubit_floor_exact_v0_pytorch_results.json:99-104`).

Hand recomputation: for the Jordan-Wigner convention, `gamma_1 = XII` and `gamma_2 = YII`. Since `X` and `Y` anticommute on one site and the other sites are identities, `{gamma_1,gamma_2}=0` exactly.

The rank-64 span is source-backed in the sympy leg. The Julia and PyTorch legs verify anticommutators/splits but do not independently compute the 64-dimensional span.

## T4. Counts 3/5/7

Verdict: PASS for constructive count, with a maximality caveat.

Source quotes:

- The sympy source constructs `family = gammas + [ch]` and returns `count = len(family)` (`geo_s1_three_qubit_floor_exact_v0_jax.py:409-424`).
- It checks exact anticommutation of that family: `"anticommutation_exact": z3_any_nonzero(anticommutation_deltas(family)) == "unsat"` (`geo_s1_three_qubit_floor_exact_v0_jax.py:420-424`).
- It then requires `[row["count"] for row in counts] == [3, 5, 7]` and exact anticommutation for all rows (`geo_s1_three_qubit_floor_exact_v0_jax.py:431-436`).
- The Julia leg, by contrast, only records `Dict("one_qubit" => 3, "two_qubits" => 5, "three_qubits" => 7)` and says the counts follow the `2n+1` bound (`geo_s1_three_qubit_floor_exact_v0_julia.jl:225-232`).

Fresh exhaustive search over non-identity Pauli strings found:

```text
n=1 max_count=3 family=['X', 'Y', 'Z']
n=2 max_count=5 family=['IX', 'IY', 'XZ', 'YZ', 'ZZ']
n=3 max_count=7 family=['IIX', 'IIY', 'IXZ', 'IYZ', 'XZZ', 'YZZ', 'ZZZ']
```

Adjudication: the packet's accepted JAX/sympy count path is constructive, not a bare `2n+1` assertion. However, the packet itself does not run an exhaustive maximality search; maximality is supported by the formula-bound field plus this audit's independent exhaustive clique search.

## T5. Honest Boundary (Y5)

Verdict: PASS for non-conflating matrix associativity vs algebra-extension nonassociativity; limited to sampled matrix triples.

Source quotes:

- Source statement: `"nonassociativity CANNOT live in the matrix representation; it requires algebra-extension nesting such as an octonion table"` (`geo_s1_three_qubit_floor_exact_v0_jax.py:390-395`).
- Source pinned definition: `"grouping means operation-application order on named sites, with final comparison after the canonical flattening C^2... -> C^8"` (`geo_s1_three_qubit_floor_exact_v0_jax.py:396-405`).
- Result says `sampled_triples: 512`, `failures: 0`, and repeats the no-matrix-nonassociativity statement (`results/geo_s1_three_qubit_floor_exact_v0_jax_results.json:287-302`).
- Result grouping receipt says `flattened_action_equal: true`, `exact_delta_zero: true`, and `nested_labels_differ: true` (`results/geo_s1_three_qubit_floor_exact_v0_jax_results.json:313-329`).

Adjudication: the packet does not claim algebra-level nonassociativity at the 3-qubit matrix floor. It correctly keeps nonassociativity outside the matrix representation and uses the grouping receipt only as a site/grouping label distinction after flattening. Caveat: the code checks 512 sampled triples from 8 Pauli strings, not all 64 non-identity three-qubit Pauli strings.

## T6. Non-Conflation

Verdict: PASS.

Source quotes:

- Build card fence: `DO NOT conflate the two S^15 structures: the 3-qubit global-phase quotient is S^15 -> CP^7 ...; the octonionic fibration S^15 -> S^8 is a DIFFERENT decomposition` (`build_card.md:5`).
- JAX result records `global_phase_density_quotient: "S^15 -> CP^7 via psi psi^dagger"` and `octonionic_structure_used_in_quotient_computations: false` (`results/geo_s1_three_qubit_floor_exact_v0_jax_results.json:68-75`).
- Envelope non-conflation gate requires `present`, `merged is False`, and `octonionic_structure_used_in_quotient_computations is False` (`geo_s1_three_qubit_floor_exact_v0_envelope.py:157-163`).

Adjudication: the quotient computation uses the density/global-phase route and does not use octonionic structure. The S^15 -> CP^7 vs S^15 -> S^8 fence is explicit in source and result.

## T7. Standard Checks

Verdict: PASS for validator/source-backed shape and can-fail controls; boundary noted for P2 proof granularity and PyTorch role.

Source quotes:

- P1 anticommutation proof/control in result: `z3_assert_some_bad: "unsat"`, `cvc5_assert_some_bad: "unsat"`, corrupted controls `sat` (`results/geo_s1_three_qubit_floor_exact_v0_jax_results.json:84-91`).
- P2 tau proof/control in result: tau wrong assertion `unsat`, GHZ/W swapped controls `sat` (`results/geo_s1_three_qubit_floor_exact_v0_jax_results.json:92-99`).
- P2 SMT uses exact integer tau values after exact sympy evaluation: `tau_ghz = int(y3["tau"]["GHZ"])`, `tau_w = int(y3["tau"]["W"])` (`geo_s1_three_qubit_floor_exact_v0_jax.py:483-489`).
- PyTorch role is exact integer anticommutation only: `role": "exact integer tensor route for anticommutation table"` in the envelope manifest (`geo_s1_three_qubit_floor_exact_v0_envelope.py:198-203`).
- NumPy boundary is explicit as forbidden exchange: `".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"` (`geo_s1_three_qubit_floor_exact_v0_envelope.py:198-204`).
- Ceiling is explicit: `classification: scratch_diagnostic`, `promotion_allowed: false`, `formal_admission_allowed: false` in the envelope (`geo_s1_three_qubit_floor_exact_v0_envelope.py:166-180`, `254-259`).

Adjudication: validator passes with `--require-pytorch` and `--strict-source-backed`. Controls can fail. PyTorch is honest: it is not used for entropy/tau, only exact Gaussian-integer tensor anticommutation. P2 is exact raw-value SMT over exact tau outputs, not a solver-level symbolic polynomial identity over tau's coefficient formula.

## Hand Recomputation Log

1. Partial trace for W over `BC`, keeping `A`:

```text
rho_A[0,0] = |psi_001|^2 + |psi_010|^2 = 1/3 + 1/3 = 2/3
rho_A[1,1] = |psi_100|^2 = 1/3
rho_A[0,1] = rho_A[1,0] = 0
rho_A(W) = [[2/3, 0], [0, 1/3]]
```

2. Tau(W) by CKW route not used by the builder:

```text
det(rho_A) = 2/9
C_A(BC)^2 = 8/9
C_AB^2 = 4/9
C_AC^2 = 4/9
tau(W) = 8/9 - 4/9 - 4/9 = 0
```

3. One anticommutator pair:

```text
gamma_1 = XII
gamma_2 = YII
X Y + Y X = 0
therefore {gamma_1, gamma_2} = 0 exactly
```

4. Count search:

```text
n=1 max_count=3 family=['X', 'Y', 'Z']
n=2 max_count=5 family=['IX', 'IY', 'XZ', 'YZ', 'ZZ']
n=3 max_count=7 family=['IIX', 'IIY', 'IXZ', 'IYZ', 'XZZ', 'YZZ', 'ZZZ']
```

## Named Gaps

1. The full "two independent CAS end-to-end" exactness claim is too strong. Sympy performs the exact named-state derivations; Julia records exact named-state constants and does not include a tau receipt.

2. The result receipt does not emit hyperdeterminant intermediates `d1/d2/d3`; the route is source-auditable but the receipt is thinner than the blind derivation.

3. The packet constructs and verifies anticommuting families for 1/2/3 qubits, but does not itself run an exhaustive maximality search. This audit's independent exhaustive Pauli-string clique search confirms 3/5/7.

4. Y5 associativity is exact for the sampled 512 triples in the packet. The honest mathematical boundary is preserved, but the receipt is sampled rather than exhaustive over all three-qubit Pauli strings.

5. P2 SMT is exact over already-evaluated tau integers. It is not a solver-level symbolic polynomial identity proof over the coefficient formula.

## Verdict

VERDICT: PARTIAL PASS / EXACTNESS CLAIM NARROWED.

The packet's core values survive fresh audit: `log(2)`, `log(3) - 2*log(2)/3`, `tau(GHZ)=1`, `tau(W)=0`, `rank=64`, Weyl splits `2+2` and `4+4`, counts `3/5/7`, exact Cl(6) anticommutation, can-fail controls, PyTorch honest role, NumPy boundary, and non-conflation of `S^15 -> CP^7` from `S^15 -> S^8`.

The packet does not satisfy the strongest wording of T1. Do not cite it as two independent CAS exact arithmetic end-to-end for all entropy/tau claims. Cite it as: sympy exact CAS for named-state entropy/tau and Cl(6) rank; Julia exact Symbolics phase receipt plus exact Gaussian-integer Cl(6)/Z3 receipt; PyTorch exact integer tensor anticommutation receipt.

Ceiling remains: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No promotion. The floor provides three slots and an exact associative matrix representation; nonassociativity requires the algebra extension and is not claimed here.

## Addendum 2026-06-10: Post-Hardening Focused Re-Audit

Scope: read-only re-audit after hardening, except this append-only addendum. I did not rerun the sim entrypoints because they write result JSON timestamps; recomputation below used fresh read-only snippets/imports plus validators.

Fresh validators:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_three_qubit_floor_exact_v0/results/geo_s1_three_qubit_floor_exact_v0_envelope_results.json
```

Result: `{"ok": true}`.

Runtime preflight: `scripts/codex_runtime_env_doctor.py` returned `ok=True install_state=stable_observed`; Python was `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`, Julia was `/opt/homebrew/bin/julia`, and no repo-local env pollution, missing expected modules, or active installers were observed.

Source/result binding: fresh SHA-256 checks matched the envelope source hashes for Julia `72c2e02a6b9e1ed0d3614e453659b8fa9096b1774e89e8a54e7fa02c7802cd53`, JAX `37b1aff314fbe5f4c4ca41bf3e2bd79dccdaea45557db340e43f66937688abaa`, PyTorch `ac9f3e3fd4fb7718999030f994673852bb62e406e4de520c9a456939f6ec90a0`, and envelope `847d9f17b5dc1d2a47ff423fcdab8768ee1c9af5f77f469b829114fbf4638bad`.

Gap 1, two-CAS / Julia exact Y2-Y3: CLOSED for the post-hardening claim path. Julia now computes Y2 by exact rational squared-amplitude partial traces, then diagonal 2x2 eigenvalues, then closed-form entropy strings (`geo_s1_three_qubit_floor_exact_v0_julia.jl:127-199`; result lines `1367-1452`). Julia now computes Y3 by exact rational Cayley hyperdeterminant components and tau (`geo_s1_three_qubit_floor_exact_v0_julia.jl:206-265`; result lines `1495-1545`). The source path still declares expected labels for the named states, but the reduced densities/eigenvalues/tau are no longer prefilled receipt constants. Spot recomputation from the Julia algorithm gave `W rho_A = [2//3 0; 0 1//3]`, eigenvalues `[1//3, 2//3]`, `GHZ d1=1//4,d2=0//1,d3=0//1,tau=1//1`, and `W d1=0//1,d2=0//1,d3=0//1,tau=0//1`.

Gap 2, d1/d2/d3 intermediates: CLOSED. JAX/sympy receipts now emit blind-expected intermediates `GHZ d1=1/4,d2=0,d3=0,tau=1` and `W d1=0,d2=0,d3=0,tau=0` (`geo_s1_three_qubit_floor_exact_v0_jax.py:183-229`; result lines `469-483`). Julia receipts independently emit `GHZ d1=1//4,d2=0//1,d3=0//1,tau=1//1` and `W d1=0//1,d2=0//1,d3=0//1,tau=0//1` (result lines `1500-1518`).

Gap 3, exhaustive anticommuting-clique search: CLOSED. The JAX/sympy source builds all non-identity Pauli-string vertices, all candidate pair checks, and a branch-and-bound clique search over that full graph (`geo_s1_three_qubit_floor_exact_v0_jax.py:457-506`). The source requires exhaustive maxima `[3,5,7]` in `y6_chirality()` (`geo_s1_three_qubit_floor_exact_v0_jax.py:509-525`). Fresh import recomputation returned candidate vertices/pair checks `3/3`, `15/105`, `63/1953`, recursive nodes `4/35/3793`, and max clique sizes `3/5/7`; the envelope stores the same values (result lines `422-467`).

Gap 4, associativity sweep label: CLOSED. The builder chose exhaustive, not sampled+theorem. The JAX/sympy source enumerates all `4^3 = 64` three-qubit Pauli labels, precomputes `64^2 = 4096` pair products, then checks all `64^3 = 262144` ordered triples (`geo_s1_three_qubit_floor_exact_v0_jax.py:380-424`). Fresh import recomputation returned `mode=exhaustive_ordered_pauli_string_triples`, `ordered_triples=262144`, `failures=0`, `first_failure=null`; the envelope stores the same in the build-gate details (`geo_s1_three_qubit_floor_exact_v0_envelope.py:128-131`, `geo_s1_three_qubit_floor_exact_v0_envelope.py:145`). The original build card still says "ALL sampled triples" (`build_card.md:12`), but the current source/result label is exhaustive and truthful.

Gap 5, byte-stability: CLOSED. Fresh receipts and recomputation agree on `log(2)`, `log(3) - 2*log(2)/3`, tau `1/0/0`, rank `64`, splits `2+2` and `4+4`, counts `3/5/7`, and solver/control verdicts. Envelope cites: exact entropy and d/tau/rank/splits at result lines `420-515`; solver verdicts at lines `910-935`; Julia Z3 verdict/control at lines `1573-1576`.

Gap 6, validators: CLOSED. All three validator levels passed locally: plain, `--require-pytorch`, and `--require-pytorch --strict-source-backed`.

Gap 7, stale narrowed-claim surface: CLOSED for the active envelope/result claim, with one historical-surface caveat. The active envelope claim is now: exact symbolic, closed-form, SMT, and exact-integer treatment at the 3-qubit floor, with the split roles made explicit in `foreign_runtime_manifest`: Julia canon exact Symbolics/Z3 receipt, JAX second CAS and z3/cvc5 sidecar, PyTorch exact integer tensor anticommutation route (result lines `841-855` and `1878-1899`). The old narrowed audit remains above by design, and `build_card.md` still contains original task wording about `Symbolics.jl + sympy` and sampled triples (`build_card.md:9`, `build_card.md:12`); this addendum supersedes those historical audit/build-card readings without rewriting them.

Final verdict: exactness claim EARNED as stated in the current envelope/result surface. Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; no formal admission or promotion is implied.

## 2026-06-10 Tooling Remediation Steps 5-6

Step 5: Clifford claims now route through Julia `CliffordAlgebras` as load-bearing for Cl6. The Julia receipt constructs `CliffordAlgebra(6,0)` and records package dimension `64` plus generator-square evidence; the hand Jordan-Wigner gamma table is retained as a mirror.

Step 6: max-anticommuting-family counts now route through an exact `rustworkx.PyGraph` anticommutation graph in the JAX lane. The branch-and-bound search is graph-backed, and the legacy label recursion is marked as mirror evidence. The PyTorch lane also has a source-backed SymPy exact scalar sidecar so strict source-backed validation no longer depends on a baseline-only PyTorch package claim.

Byte-stability pins: max-family ladder `3/5/7`, gamma7 split `4+4`, Cl6 algebra dimension `64`, tau values, and exact entropy pins remained unchanged.

Fresh checks: JAX, Julia, PyTorch, and envelope reruns returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` returned `ok:true`; relevant capability gates for `rustworkx`, `sympy`, `torch`, and `CliffordAlgebras` returned passing receipts.
