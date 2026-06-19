# Fresh Audit Verdict: geo_s1_scaling_stress_678q_exact_v0

Date: 2026-06-10

Mode: read-only audit except this file.

Inputs checked:

- Sim folder: `system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/`
- Corrected instruction packet: `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md`
- Local directive copy: `directive_addendum.md`
- Pattern catalog: H1-H7 from `axis_independence_discriminators_036/audit_verdict.md`; E1-E6 from `geo_s1_exact_closure_v0/audit_verdict.md`

## Verdict

VERDICT: EARNED, with the narrow ceiling below.

Ceiling: this earns the scaling-regime exact scratch-diagnostic claim for the 6Q/7Q/8Q overbuild ladder only. It supports exact F01/N01/T01 carrier receipts, constructive maximal anticommuting families of sizes 13/15/17, exact chirality splits, exact no-new-minimum fences, and no dense-enumeration smuggling. It does not establish new minimum qubit counts, channel/schedule associator claims, arbitrary dense-state enumeration coverage, bridge/axis promotion, or canonical scientific-lego coupling.

## Commands And Recomputations

Validator commands:

```text
python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_envelope_results.json
```

Result:

```text
{"ok": true, "result_json": "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_envelope_results.json"}
```

```text
python3 system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/geo_s1_scaling_stress_678q_exact_v0_exact_strength_validator.py
```

Result:

```text
{"ok": true, "errors": [], "result_json": "system_v6/sims/geo_s1_scaling_stress_678q_exact_v0/results/geo_s1_scaling_stress_678q_exact_v0_envelope_results.json"}
```

Independent exact recomputation:

| n | Hilbert dim | mixed-density real dim | gamma count | chirality raw product | chirality split | max family | next-family min dim |
|---|---:|---:|---:|---|---:|---:|---:|
| 6 | 64 | 4095 | 12 | `(i^2, ZZZZZZ)` adjusted to phase 0 | 32+32 | 13 | 128 |
| 7 | 128 | 16383 | 14 | `(i^3, ZZZZZZZ)` adjusted to phase 0 | 64+64 | 15 | 256 |
| 8 | 256 | 65535 | 16 | `(i^0, ZZZZZZZZ)` adjusted to phase 0 | 128+128 | 17 | 512 |

N01/O3 n=8 recomputation:

```text
A = XIIIIIII
B = XIIIIIII + ZIIIIIII
AB terms = I + i^3 YIIIIIII
BA terms = I + i^1 YIIIIIII
commutator nonzero: true
anticommutator has 2I: true
```

n=8 spot anticommutator pair recomputation:

```text
pair = ZZZZZZZX, ZZZZZZZZ
products = i^3 IIIIIIIY and i^1 IIIIIIIY
anticommutator = 0
```

Source-hash and envelope checks recomputed:

```text
jax hash match: true
julia hash match: true
pytorch hash match: true
pin count: 1
classification: scratch_diagnostic
promotion_allowed: false
formal_proof: false
all_pass: true
max_divergence: 0
```

Float scan:

```text
envelope float_count 18, non_runtime_float_count 0
jax float_count 7, non_runtime_float_count 0
julia float_count 7, non_runtime_float_count 0
pytorch float_count 7, non_runtime_float_count 0
```

## Per-Check Findings

### 1. F01/N01/T01 Per Rung, O3, And Dimensions

Finding: PASS.

Quoted source:

- `build_card.md` states the target dimensions: "6Q carrier S^127 / CP^63 / density dim 4095; 7Q carrier S^255 / CP^127 / density dim 16383; 8Q carrier S^511 / CP^255 / density dim 65535."
- `geo_s1_scaling_stress_678q_exact_v0_jax.py` pins the same values in `PIN`: carriers `C64/C128/C256`, spheres `S^127/S^255/S^511`, projective spaces `CP^63/CP^127/CP^255`, and mixed-density dimensions `4095/16383/65535`.
- The exact validator requires per-rung receipt names: `F01`, `N01`, and `T01`.
- JAX W1 computes F01 exact counts, N01 O1-O6, and T01 algebraic associator controls; PyTorch and Julia mirror the exact label arithmetic.

Recomputation:

- `2^6 = 64`, so pure-state sphere `S^(2*64-1) = S^127`, projective space `CP^(64-1) = CP^63`, and mixed-density real dimension `64^2 - 1 = 4095`.
- `2^7 = 128`, so `S^255`, `CP^127`, and `128^2 - 1 = 16383`.
- `2^8 = 256`, so `S^511`, `CP^255`, and `256^2 - 1 = 65535`.
- O3 is genuine at n=8: `A = XIIIIIII`; `B = XIIIIIII + ZIIIIIII`; `AB != BA`, while the anticommutator has the exact identity term `2I`. This is not merely an anticommute or commute witness.

Named gap: T01 schedule/channel associator is explicitly `not_scoped`; only the algebraic carrier spot checks are earned.

### 2. Max-Family 13/15/17, Theorem Bound, Constructive Families

Finding: PASS with honest strength token.

Quoted source:

- `build_card.md` claims "Construct exact max anticommuting Pauli-family sizes 13, 15, 17."
- `geo_s1_scaling_stress_678q_exact_v0_jax.py` defines `representation_bound_receipt`, with theorem statement: "A complex representation of Cl_m requires complex dimension at least 2^(floor(m/2))."
- JAX W3 constructs `gamma_labels(n) + [chirality_label(n)]`, checks all exact pairwise anticommutators, and records `representation_theorem_with_constructive_receipt`.
- The exact strength validator rejects W3 if the strength is not exactly `representation_theorem_with_constructive_receipt`.

Recomputation:

- For n=6, the constructed family has `2n+1 = 13` labels on dimension `2^6 = 64`; the next family size 14 would require minimum complex dimension `2^(14//2) = 128`, exceeding 64.
- For n=7, size 15 fits dimension 128; size 16 would require 256, exceeding 128.
- For n=8, size 17 fits dimension 256; size 18 would require 512, exceeding 256.
- Exact pairwise construction check returned zero failures for all three rungs.
- n=8 spot recomputation of `ZZZZZZZX` with `ZZZZZZZZ` produced products `i^3 IIIIIIIY` and `i^1 IIIIIIIY`, so the anticommutator cancels exactly.

Label honesty: because exhaustive dense enumeration of all possible matrix families is infeasible and intentionally not attempted, the earned token is `representation_theorem_with_constructive_receipt`, not finite dense exhaustive enumeration.

### 3. No Dense Enumeration Smuggled; Resource Rows

Finding: PASS.

Quoted source:

- The corrected instruction says: "Do not brute-force arbitrary full dense-state enumeration in 6Q-8Q."
- JAX states: "No arbitrary dense-state enumeration is used."
- JAX F01 records `arbitrary_dense_state_enumeration: "not_used"`.
- JAX W4 resource rows list dense arbitrary-state enumeration and dense operator clique enumeration as not run, while full nonidentity Pauli-string scans are run.
- PyTorch uses exact integer tensor Pauli scans over `torch.arange(1, 4**n)`.
- Julia uses exact Pauli-label arithmetic and finite Pauli extension scans.
- Envelope forbids `.numpy`, `np.asarray`, CSV, pickle, and hidden host-copy exchange.

Recomputation:

- Source inspection found finite Pauli-string, stabilizer, sparse label, and theorem routes.
- I found no `.numpy()` or `np.asarray` claim path.
- Float values in result JSONs appear only in runtime/resource rows; no non-runtime claim float was found.

Resource status: resource rows are correctly labeled `diagnostic_float_nonclaim`.

### 4. Chirality Splits Computed Via Constructed gamma_(2n+1)

Finding: PASS.

Quoted source:

- JAX `chirality_label(n)` multiplies all constructed gamma labels, then applies the `(-i)^n` phase adjustment and checks the expected all-Z Pauli label.
- JAX W2 iterates computational basis labels and counts chirality signs.
- PyTorch and Julia implement the same exact Pauli-label product route.

Recomputation:

- n=6: raw gamma product `(i^2, ZZZZZZ)` adjusted by `(-i)^6` gives phase 0 and exact label `ZZZZZZ`; parity split is `32+32`.
- n=7: raw product `(i^3, ZZZZZZZ)` adjusted by `(-i)^7` gives phase 0 and exact label `ZZZZZZZ`; parity split is `64+64`.
- n=8: raw product `(i^0, ZZZZZZZZ)` adjusted by `(-i)^8` gives phase 0 and exact label `ZZZZZZZZ`; parity split is `128+128`.

This is computed from the constructed gamma family, not asserted as a separate table.

### 5. No New Minimum Claims; 8Q Overbuild Ceiling

Finding: PASS.

Quoted source:

- `build_card.md` states: "This is not a new minimum-qubit claim. 6Q-8Q are scaling/stress/boundary rungs; 8Q is the finite overbuild ceiling."
- The corrected instruction says: "6Q-8Q are not minimum rungs. They are scaling/stress/boundary rungs."
- JAX W6 names "no_new_minimum_boundary" and rejects controls such as "because 8Q works, the 3Q minimum floor moved."
- The envelope `must_not_claim` list includes no new 6Q/7Q/8Q minimum, no replacement of lower exact closures, no bridge/axis promotion, and no canonical scientific-lego promotion.

Search result:

- Occurrences of "minimum" and promotion language are fences, negative controls, or must-not-claim entries.
- I found no promoted claim that 6Q, 7Q, or 8Q establishes a new minimum.

### 6. Exactness Standard: Tokens, Signs, Controls, SMT, Pins, CAS Split, PyTorch, Ceilings

Finding: PASS with named caveats.

Quoted source:

- The corrected instruction lists allowed strength tokens and says every rung needs exact pins, controls, raw-object SMT/proof checks where scoped, validator, and no-promotion ceiling.
- JAX/PyTorch/JJ source files define the allowed tokens and forbidden labels. The exact validator rejects forbidden labels and checks literal tokens.
- The validator checks schema, `all_pass`, scratch classification, `promotion_allowed == false`, `formal_proof == false`, gates, source hashes, per-rung receipts, W1-W7 tables, resource rows, O3, and ceiling fields.
- Envelope records exact shared pins, three engine legs, source hashes, crossover proof routes, and `all_pass`.

Recomputation:

- Strength tables used literal allowed tokens; no forbidden token was found in claim rows.
- Chirality signs and anticommutator signs were recomputed from Pauli multiplication, not trusted from labels.
- Can-fail controls exist in W5/W6: corrupted gamma set, erased chirality, and false minimum/promotion claims are rejected.
- Z3/cvc5 rows exist for representation bounds and boundary controls per rung.
- Pin hash is shared across JAX, PyTorch, and Julia.
- Source hashes in the envelope match the current source files.

CAS/tool-role finding:

- The sim is honest about tool roles. JAX and PyTorch rely on exact Pauli arithmetic plus SymPy/Z3/cvc5 style checks; Julia uses exact Pauli arithmetic with `Symbolics`/`Z3`, while `CliffordAlgebras` is supportive rather than the sole load-bearing proof path.
- PyTorch is an exact integer tensor mirror for the finite Pauli-string route, not an autograd or floating scientific arbitrator.

Named caveats:

- This is not a two-CAS independent derivation of a new symbolic formula; it is a three-engine exact-arithmetic and theorem-bound cross-check with an honest split of tool roles.
- T01 channel/schedule associator claims remain out of scope.

## Pattern Catalog Audit

H1 fixture isolation: not present as a blocking pattern. The same exact Pauli/Jordan-Wigner construction feeds F01/N01/T01/W2/W3/W4 rather than a disconnected fixture-only table.

H2 label echo: not present as a blocking pattern. Key values were recomputed from labels: density dimensions, chirality phase/sign split, O3 witness behavior, max-family anticommutators, and representation-bound exclusions.

H3 weak shuffle: not present as a blocking pattern. The finite Pauli extension scan and corrupted controls are stronger than a label shuffle.

H4 tautological erasure controls: not present as a blocking pattern. Erased chirality and corrupted gamma controls are expected to fail exact checks, and the validator enforces the failure status.

H5 derived-boolean SMT: not promoted beyond scope. Some SMT checks bind integer summaries, but the claim path also includes exact constructive families, exact pairwise anticommutator checks, and the representation theorem. The SMT rows are not the sole evidence.

H6 synthetic `torch.func`: not present. PyTorch is used as exact integer tensor arithmetic over Pauli labels; no synthetic autograd claim is made.

H7 axis-boundary asserted: not present. The packet repeatedly fences against bridge, axis, canonical, and minimum promotion.

E1 sign pin: passed. The Pauli multiplication convention and chirality phase adjustment are pinned and recomputed.

E2 two-CAS density derivation: passed under honest split. The packet does not falsely claim two independent CAS derivations for a new density formula; it uses exact closed-form counting, cross-engine pins, and source-hash-checked mirrors.

E3 linking signs: passed. Chirality and anticommutator signs are computed by exact Pauli multiplication.

E4 interval/theorem route: passed for this scope. The max-family exclusion uses a representation theorem with exact constructive receipt, not a float interval claim.

E5 Haar/statistical route: not applicable and not smuggled. Statistical rows are absent from the claim path; resource/runtime floats are diagnostic nonclaims.

E6 classification exactness: passed. Claim rows use allowed literal strength tokens; runtime floats do not carry classification claims.

## Named Gaps

1. T01 channel/schedule associator remains explicitly not scoped.
2. No arbitrary dense-state or dense-operator clique enumeration was run; this is correct for the instruction, but it fixes the ceiling at constructive/theorem evidence.
3. Julia `CliffordAlgebras` is supportive, not the sole load-bearing exact proof route.
4. PyTorch is an exact integer tensor mirror, not an autograd/scientific-model authority.
5. The sim folder is currently packet-local evidence in the working tree; this audit does not assert committed or canonical repository state.

## Final Adjudication

VERDICT: EARNED.

Restated ceiling: exact scratch-diagnostic scaling-regime evidence for 6Q/7Q/8Q overbuild stress only. The earned strength is `representation_theorem_with_constructive_receipt` for the max-family rows, supported by exact arithmetic and cross-engine source-hash-checked mirrors. It does not promote a new minimum, bridge, axis-level result, canonical result, channel/schedule associator result, dense-enumeration result, or scientific-lego coupling.

## 2026-06-10 Tooling Remediation Steps 5-6

Step 5: Clifford claims now route through Julia `CliffordAlgebras` as load-bearing by a checked capability artifact plus bounded package receipts. The refreshed `cliffordalgebras_capability_results.json` includes a passing `scaling_cl12_cl14_cl16_artifact` case: Cl12 and Cl14 dimensions are package-constructed, while Cl16 is a checked canon formula artifact with `representation_theorem_with_constructive_receipt` strength. A fresh carrier-project attempt to materialize `CliffordAlgebra(16,0)` produced no successful output within about 3m19s and was killed; no Cl16 materialization claim is made. The Pauli-label gamma/chirality tables are retained as mirrors.

Step 6: the 6Q/7Q/8Q extension scans now route through exact `rustworkx.PyGraph` candidate-to-family graphs in JAX and PyTorch. JAX vectorized and PyTorch tensor scans are retained as mirrors; no `torch_geometric` route is claimed.

Byte-stability pins: max-family ladder `13/15/17`, chirality splits `32+32/64+64/128+128`, algebra dimensions `4096/16384/65536`, Hilbert dimensions `64/128/256`, and density dimensions `4095/16383/65535` remained unchanged.

Fresh checks: JAX, Julia, PyTorch, and envelope reruns returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` and `geo_s1_scaling_stress_678q_exact_v0_exact_strength_validator.py` returned `ok:true`; relevant capability gates for `rustworkx`, `sympy`, `z3`, `cvc5`, and `CliffordAlgebras` returned passing receipts.

## 2026-06-10 Toolset-Coverage Addendum

QuantumClifford.jl is now load-bearing for the Julia stabilizer subfamily route. The Julia leg uses `QuantumClifford.PauliOperator`, `QuantumClifford.Stabilizer`, `QuantumClifford.stab_to_gf2`, and `QuantumClifford.comm` for the 6Q/7Q/8Q stabilizer rows and the applicable Cl16 PauliOperator/stabilizer-formalism check. The broader Cl(12/14/16) max-family capacity remains a representation-theorem row, not a stabilizer-syntax promotion.

kingdon is now load-bearing for the PyTorch-side Clifford algebra route. The PyTorch leg uses `kingdon.Algebra(12,0,0)`, `Algebra(14,0,0)`, and `Algebra(16,0,0)` multivectors for basis-vector anticommutators and chirality pseudoscalar squares. The torch integer Pauli extension scans remain mirror/resource rows for the finite scan, not the Clifford algebra carrier.

Fresh checks: `sim_quantumclifford_capability.py`, `sim_kingdon_capability.py`, and `sim_cliffordalgebras_capability.py` have passing capability receipts; Julia, PyTorch, and envelope reruns returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` and `geo_s1_scaling_stress_678q_exact_v0_exact_strength_validator.py` returned `ok:true`; per-file load-bearing gates returned no violations for `CliffordAlgebras`, `QuantumClifford`, `Symbolics`, `Z3`, `kingdon`, `sympy`, `cvc5`, and `rustworkx`.
