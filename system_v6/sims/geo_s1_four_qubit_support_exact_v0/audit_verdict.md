# Fresh Audit Verdict: geo_s1_four_qubit_support_exact_v0

Audit date: 2026-06-10
Audit mode: read-only except this `audit_verdict.md`
Inputs: this sim folder sources/results, `build_card.md`, `directive_addendum.md`, `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md`, prior H1-H7 catalog from `axis_independence_discriminators_036/audit_verdict.md`, and prior E1-E6 catalog from `geo_s1_exact_closure_v0/audit_verdict.md`.

## Verdict

VERDICT: NARROWED.

The 4Q packet earns the core scratch diagnostic computations: F01/N01/T01 are present and computed; `C16`, `S31`, `CP15`, mixed dimension `255`, `Cl8 ~= M16(C)`, `gamma9` split `8+8`, and max family `9` are source-backed; GHZ4/product/Bell-pair/cluster controls are exact; and triality is correctly kept as pressure/open rather than full triality. The narrowing is label-contract drift: the packet uses a local hyphenated strength-label dialect such as `representation-theorem`, while the binding directive's strength list uses tokens like `representation_theorem_with_constructive_receipt`.

Ceiling restated: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No final carrier, final `M(C)`, QIT-engine, S2/S3 runtime, physics, bridge, or full Spin(8) triality automorphism admission is earned.

## Fresh Commands

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/geo_s1_four_qubit_support_exact_v0/results/geo_s1_four_qubit_support_exact_v0_envelope_results.json
-> {"ok": true, ...}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/geo_s1_four_qubit_support_exact_v0/results/geo_s1_four_qubit_support_exact_v0_envelope_results.json
-> {"ok": true, ...}
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_s1_four_qubit_support_exact_v0/geo_s1_four_qubit_support_exact_v0_exact_strength_validator.py system_v6/sims/geo_s1_four_qubit_support_exact_v0/results/geo_s1_four_qubit_support_exact_v0_envelope_results.json
-> {"ok": true, "errors": [], ...}
```

JSON float scan: all four result JSON files contain `0` JSON float values.

## Per-Check Adjudication

### 1. F01/N01/T01

Verdict: PASS.

Quoted source:

- F01 computes `n = 4`, `hilbert_dim = 2**n`, `operator_basis_count = 4**n`, `pure_sphere = "S^31 subset C^16"`, `phase_quotient = "CP^15"`, and `mixed_density_real_dim = 4**n - 1` (`geo_s1_four_qubit_support_exact_v0_jax.py:203-231`).
- N01 computes O3 with `A = XIII`, `B = XIII + ZIII`, then requires both `AB_minus_BA_nonzero` and `AB_plus_BA_nonzero` (`geo_s1_four_qubit_support_exact_v0_jax.py:268-328`).
- O6 explicitly separates root order from capacity: `root_order_row = "noncommutation"` and `separate_capacity_row = "Z4 max anticommuting family = 9"` (`geo_s1_four_qubit_support_exact_v0_jax.py:322-326`).
- T01 checks all ordered triples of the eight Cl8 gamma generators, records `failures = 0`, marks channels/schedules `not_scoped`, and states matrix-level nonassociativity is not present (`geo_s1_four_qubit_support_exact_v0_jax.py:479-508`).

Recomputation:

```text
4Q F01:
hilbert_dim = 16
computational_basis_count = 16
operator_basis_count = 256
pure sphere = S^31 subset C^16
phase quotient = CP^15
mixed density real dimension = 255

O3 with A=XIII, B=(X+Z)III:
AB-BA nonzero = true, 16 nonzero entries
AB+BA nonzero = true, 16 nonzero entries

One Clifford pair:
gamma_1 = XIII, gamma_2 = YIII
gamma_1 gamma_2 + gamma_2 gamma_1 = 0 exactly
```

Adjudication: O3 is genuine and root-vs-Clifford separation is preserved. T01 is honest: matrix associativity is controlled, while schedule/channel associativity is not claimed.

### 2. Max-Family 9

Verdict: PASS for math; NARROWED for label token.

Quoted source:

- Z3 constructs Cl8 with gamma labels `XIII`, `YIII`, `ZXII`, `ZYII`, `ZZXI`, `ZZYI`, `ZZZX`, `ZZZY`; it checks all 64 anticommutators, generated dimension `256`, `gamma9^2=I`, trace `0`, and split `8+8` (`geo_s1_four_qubit_support_exact_v0_jax.py:607-653`).
- Z4 constructs `gammas + [gamma9]`, checks pairwise anticommutation, runs a finite extension scan, and proves the m=10 bound impossible by z3/cvc5 (`geo_s1_four_qubit_support_exact_v0_jax.py:666-699`).
- The theorem text says pairwise anticommuting Hermitian-unitaries in `M_16(C)` imply a `Cl_m(C)` representation, so `2^floor(m/2) <= 16` and `m <= 9` (`geo_s1_four_qubit_support_exact_v0_jax.py:684-690`).

Recomputation:

```text
m = 9: 2^floor(9/2) = 16 <= 16, admissible.
m = 10: 2^floor(10/2) = 32 > 16, blocked.
```

Adjudication: the theorem-plus-constructive route is the right route, and the constructed family is exact. The named gap is that the result labels the row `representation-theorem`, not the directive token `representation_theorem_with_constructive_receipt` (`geo_s1_four_qubit_support_exact_v0_jax.py:690`, `:698`; classification table at `:758-780`).

### 3. 4Q-Specific Rows

Verdict: PASS.

Quoted source:

- Carrier quotient keeps `S31/S1 = CP15`, `D(C16)` dimension `255`, and `Cl8_Spin8_representation_pressure` separate from the pure quotient; `CP15_equals_Spin8_triality` is `False` (`geo_s1_four_qubit_support_exact_v0_jax.py:511-530`).
- GHZ4, product, Bell-pair product, and linear cluster state are constructed as exact named states (`geo_s1_four_qubit_support_exact_v0_jax.py:561-604`).
- Cluster state signs are computed from the linear graph CZ pattern, and stabilizers `XZII`, `ZXZI`, `IZXZ`, `IIZX` are applied with exact zero deltas (`geo_s1_four_qubit_support_exact_v0_jax.py:533-558`).
- Triality pressure computes `gamma_i gamma9 + gamma9 gamma_i = 0` for all eight relations, records `8v/8s/8c` dimensions, and states full triality automorphism is not claimed (`geo_s1_four_qubit_support_exact_v0_jax.py:702-740`).

Recomputation:

```text
GHZ4 one-qubit reduction = diag(1/2, 1/2), entropy = log(2).
Product |0000> reductions have entropy 0.
Bell_AB tensor Bell_CD has AB entropy 0 and AC entropy log(4).
```

Adjudication: Spin(8)/triality pressure is computed as a pinned relation and left open for the missing automorphism. GHZ4/cluster/product/Bell-pair controls are exact. The build card asked for "biseparable controls"; the Bell-pair product is the biseparable/control row used here.

### 4. Strength, Forbidden Rows, Tools, Ceilings

Verdict: PASS for no float tolerance and ceiling; NARROWED for strength-label dialect.

Quoted source:

- The directive's allowed strength tokens include `representation_theorem_with_constructive_receipt` and forbid `bare_float_tolerance`, `sample_only`, `max_deviation_only`, `abs_error_only`, visual agreement, and validator-green-only (`directive_addendum.md:382-408`).
- The packet classification table has no bare-float rows, but uses `exact-integer`, `representation-theorem`, `finite-exhaustive`, `negative-control`, and `open-with-reason` (`geo_s1_four_qubit_support_exact_v0_jax.py:758-780`).
- The custom validator accepts the local labels and checks all source hashes, `reads_peer_result=false`, F01/N01/T01, entanglement, Cl8, max family, triality, and no bare float rows (`geo_s1_four_qubit_support_exact_v0_exact_strength_validator.py:30-93`).
- PyTorch is honest as exact integer tensor and cluster stabilizer mirror, and the envelope keeps `.numpy`, `np.asarray`, CSV, pickle, and hidden host-copy bridges forbidden (`geo_s1_four_qubit_support_exact_v0_envelope.py:244-297`).

Pattern-catalog audit:

- H1-H7 fixture/echo/control/derived-boolean/synthetic-boundary patterns: no matching fixture-isolation or label-template pattern found. The packet recomputes shared matrix objects and exact state controls rather than disjoint field fixtures.
- E1-E6 exactness patterns: sign pin is explicit enough for gamma conventions, two solver routes exist in the Python lane with Julia/PyTorch split roles, signs are computed for gamma products, no float-boxed interval row is present, and the classification table exposes the local label dialect.

Named gaps:

1. Strength labels do not literally match the binding directive token names. This narrows the packet even though the math row is honest.
2. Full Spin(8) triality is not implemented. This is not a failure because the packet marks `triality_pressure_open` with the missing condition.
3. Schedule/channel associator is not scoped. This is acceptable for this carrier/support packet and must not be cited as a channel-bracketing result.

## Final Verdict

VERDICT: NARROWED.

Use the packet as a 4Q support scratch diagnostic for exact `C16/S31/CP15/D(C16)`, Cl8, `gamma9` split `8+8`, max family `9`, exact named controls, and Spin(8)/triality pressure only. Do not cite it as matching the directive's exact strength-token vocabulary until the hyphenated local labels are normalized to the current underscore strength list.

2026-06-10 re-audit note: Gap 1 was closed by mechanical relabeling only: every claim strength-classification value in the source-generated `strength_label` and `achieved_strength` fields now uses the literal directive token names from `/tmp/claude_s1_qubit_ladder_corrected_message_20260610.md` section 5, while honest open/not-scoped markers for gaps 2-3 remain untouched. Fresh JAX, Julia, PyTorch, and envelope reruns all returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --require-source-backed`, `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed`, and the packet-local exact-strength validator all returned `ok:true`; a fresh token scan found no old strength-classification values and no non-directive strength tokens in the result JSONs. The packet directory is currently untracked, so there is no Git baseline for a literal old/new byte diff, but the source edit is limited to classification-token literals and regenerated claim values checked against the audit-critical values remain unchanged: `C16/S31/CP15/D(C16)=255`, O3 noncommuting-not-anticommuting witness, T01 `not_scoped`, Cl8 dimension `256`, gamma9 split `8+8`, max family `9`, and promotion/formal-admission ceilings.
NARROWED -> EARNED if tokens match and values byte-stable.

## 2026-06-10 Tooling Remediation Steps 5-6

Step 5: Clifford claims now route through Julia `CliffordAlgebras` as load-bearing for Cl8. The Julia receipt constructs `CliffordAlgebra(8,0)` and records package dimension `256` plus generator-square evidence; the hand Jordan-Wigner gamma table is retained as a mirror.

Step 6: the attempted 10-member extension scan now routes through an exact `rustworkx.PyGraph` candidate-to-family graph in both JAX and PyTorch. The old finite Pauli-label scan is retained as mirror evidence.

Byte-stability pins: max family `9`, gamma9 split `8+8`, Cl8 algebra dimension `256`, `C16/S31/CP15/D(C16)=255`, and open triality/channel boundaries remained unchanged.

Fresh checks: JAX, Julia, PyTorch, and envelope reruns returned `ok:true`; `validate_three_engine_sim_result.py --require-pytorch --strict-source-backed` and `geo_s1_four_qubit_support_exact_v0_exact_strength_validator.py` returned `ok:true`; relevant capability gates for `rustworkx`, `sympy`, `torch`, and `CliffordAlgebras` returned passing receipts.
