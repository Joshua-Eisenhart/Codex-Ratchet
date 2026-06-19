# Audit verdict: nesting_consistency_family_v0

Date: 2026-06-10

Verdict: PASS at `scratch_diagnostic` ceiling only. The central GHZ/W/product/cluster, embedding-family, hybrid-order, chirality, arrow-type, and quotient-chain tripwires survive direct source inspection, result inspection, independent recomputation, and the two local validators. No variant is promoted.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; no canonical nesting law, no bridge/axis-level claim, no H/E or S4-S7 promotion.

## Sources checked

- Blind expected values: `/tmp/nesting_blind_expected_20260610.md`, 420 lines, sha in result `d743e8a84feb5c638e42dd03a5f50d848c351f728331c7678950889f41330536`.
- Family directive: `build_card.md` lines 5-12 require variants `first-sites`, `last-sites`, `interleaved-jw-order`, trace variants, hybrid order, quotient-chain, and family comparison; lines 14-19 bind the blind sheet, nesting-law receipt, `scratch_diagnostic`, and no promotion.
- Nesting-law receipt: `system_v6/receipts/nesting_law_audited_20260610.md` lines 15-29 list arrow types and require every sim to name them.
- Geometry program receipt: `system_v6/receipts/geometry_sim_program_canonical_20260610.md` lines 20-23 bind S4-S7 as stage conditions; this packet does not claim those stages as completed.
- Source lines quoted below are from the packet itself.

## Recomputations

Independent recompute used `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`.

1. `Tr_C(GHZ_3)`:

```text
Matrix([[1/2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 1/2]])
offdiag00_11=0 purity=1/2 spectrum={1/2: 2, 0: 2}
```

This is the classical mixture `( |00><00| + |11><11| ) / 2`, not `GHZ_2`. Any "GHZ nests" language would fail. The packet says the GHZ expected form is "classical two-outcome mixture" in source at `nesting_consistency_family_v0_jax.py:214-218`, computes partial trace in `:194-203`, and records `GHZ3_Tr_last_nonzero_spectrum="1/2|1/2"` in `results/nesting_consistency_family_v0_jax_results.json:1397-1405`.

2. `W_4` last-site trace:

```text
W4_weights=3/4 1/4
```

This matches `(n-1)/n` and `1/n`. The packet source encodes the W expected spectrum at `nesting_consistency_family_v0_jax.py:217-218`, and SMT binds raw values `W4_weight_W3_numerator_over_4=3`, `W4_weight_zero_numerator_over_4=1` in `results/nesting_consistency_family_v0_envelope_results.json:316-320`.

3. One embedding image element:

```text
embedding_first_XII_vs_last_ZXI_equal=False
```

For `n=3`, the first-sites row has old labels `XII,YII,ZXI,ZYI`, while last-sites has `ZXI,ZYI,ZZX,ZZY`; the images differ concretely. The source constructs variant sites at `nesting_consistency_family_v0_jax.py:252-256` and records the labels in rows at `:280-324`.

4. One hybrid composite:

```text
hybrid_phase_then_trace_equals_trace_then_phase=True Matrix([[1/2, 0], [0, 1/2]])
```

For the tested global-phase quotient input, trace-then-quotient and quotient-then-trace commute because density is phase invariant before trace. The packet states this derivation at `nesting_consistency_family_v0_jax.py:372-379`. This verdict is value-backed for this global-phase quotient family; it is not a blanket noncommutation theorem.

## Per-check adjudication

### A1 central tripwire

PASS. GHZ does not nest to pure smaller GHZ. The packet rejects pure GHZ nesting in source and SMT:

- GHZ density has off-diagonal terms in the full state at `nesting_consistency_family_v0_jax.py:156-161`, but partial trace kills the reduced `|00><11|` coherence via same traced-bit matching at `:194-203`.
- Result SMT binds `GHZ3_Tr_last_offdiag_scaled_by_2=0` and `GHZ2_pure_target_offdiag_scaled_by_2=1`; forced equality is `unsat`, with can-fail controls present (`results/nesting_consistency_family_v0_envelope_results.json:311-390`).
- W weights are exact `3/4|1/4`; product is the exact positive control (`results/nesting_consistency_family_v0_jax_results.json:1397-1408`).

### A2 family genuineness

PASS with a route caveat. The family directive is complete and no variant is promoted. The packet compares 9 embedding rows, 36 trace rows, 36 hybrid-order rows, and 3 quotient samples; divergence is exact string/scalar equality across engines (`results/nesting_consistency_family_v0_envelope_results.json:470-520`).

The embedding variants are genuinely different computations in the exact Python lanes: first/last/interleaved choose different old-site/new-site sets (`nesting_consistency_family_v0_jax.py:252-256`), and the recomputed `XII != ZXI` witness shows concrete image difference. The family table keeps `promoted_variant=null` and marks GHZ/W/cluster pure nesting as what breaks (`results/nesting_consistency_family_v0_jax_results.json:1372-1391`).

Caveat: the Julia lane is not an independent density-matrix recomputation for F2/F3/F4. It emits formula-derived rows for trace, quotient, and hybrid receipts (`nesting_consistency_family_v0_julia.jl:66-110`, `:181-206`). Julia is still load-bearing for CliffordAlgebras dimensions/generator-square receipts and Z3 raw-value SMT (`:145-173`, `:224-246`, `:306-353`).

### A3 hybrid order

PASS for the scoped global-phase quotient. The packet does not assume an arbitrary quotient/trace law; it scopes the hybrid to `trace_phase_quotient` in the pin (`nesting_consistency_family_v0_jax.py:35-41`) and records `commutator_zero_count=36` with derivation (`nesting_consistency_family_v0_jax.py:372-379`). My recompute on the Bell sample gives equal reduced density matrices. This is a commute verdict from values for the named phase quotient family, not a claim that all quotient/trace composites commute.

### A4 chirality restriction

PASS. The blind expected relation is derived and matched: `Gamma_n = Gamma_(n-1)_image * Z_new`, not literal old chirality. Source computes old/new chirality products at `nesting_consistency_family_v0_jax.py:294-311`, and rows require the `Z_new` relation true while literal equality is false at `:315-321`. Recompute for `n=3` first-sites gave old `ZZI`, new `ZZZ`, `new=old*IIZ true`, `new=old false`.

### A5 arrow types

PASS. The nesting-law receipt names arrow types at `system_v6/receipts/nesting_law_audited_20260610.md:15-29`. The packet uses `tensor`, `algebra extension`, `quotient`, `principal-bundle / fibration`, `subset/submanifold`, and `filtration`; the envelope gate reports these per engine (`results/nesting_consistency_family_v0_envelope_results.json:59-89`).

The quotient-chain commuting square is pointwise, not just prose: each F4 row carries `pi_15 o i_S = i_P o pi_7`, `difference_zero=true`, and the guard that Hopf/projective quotient is not a finite covering (`results/nesting_consistency_family_v0_jax_results.json:1328-1368`).

### A6 tool, route, controls, tokens, ceiling

PASS with caveats.

- Aligned load-bearing tooling is mostly honest. JAX marks `jax` and `jax.numpy` supportive, with SymPy/z3/cvc5 load-bearing (`nesting_consistency_family_v0_jax.py:52-66`, `results/..._jax_results.json:1-46`). PyTorch marks `torch.func`, SymPy, z3, and cvc5 load-bearing, with `torch` supportive (`nesting_consistency_family_v0_pytorch.py:57-95`). Julia marks CliffordAlgebras and Z3 load-bearing (`nesting_consistency_family_v0_julia.jl:28-49`).
- Mirrors are labeled: the JAX claim says "SymPy/SMT with JAX as x64 runtime marker" (`results/..._jax_results.json:66`), and the envelope foreign runtime roles say JAX is "SymPy plus z3/cvc5 exact SMT lane with JAX x64 marker" and PyTorch is "torch.func exact tensor gate plus SymPy/z3/cvc5 lane" (`nesting_consistency_family_v0_envelope.py:215-220`).
- Raw-value SMT for A1 is present and load-bearing, not boolean-only: result fields bind off-diagonal and W numerator integers and show wrong-weight can-fail `sat` (`results/nesting_consistency_family_v0_envelope_results.json:311-390`, `:439-468`).
- Mutation/control coverage exists for the central facts: wrong W numerator can-fail controls are `sat`, pure GHZ forced equality is `unsat`, and no-variant-promoted is checked (`results/nesting_consistency_family_v0_envelope_results.json:300-390`).
- No sampling seeds are required; the packet is exact finite/symbolic and pointwise sample based. Strength tokens are literal and allowed (`results/nesting_consistency_family_v0_jax_results.json:1413-1419`).
- H/E and S4-S7 v2 catalog binding: no H/E or S4-S7 completion claim appears in this packet. The geometry program S4-S7 stage conditions remain source context only (`geometry_sim_program_canonical_20260610.md:20-23`), and the result ceiling blocks promotion.

Named gaps:

1. Julia F2/F3/F4 is partly declarative/formula-emitted, not a full local density/projector recomputation. This does not kill the packet because JAX/PyTorch recompute exact matrices and Julia owns the Clifford/Z3 route, but it prevents any stronger "three fully independent family computations" wording.
2. The hybrid-order result is for global phase quotient/density inputs only. Do not generalize it to arbitrary quotient-then-trace composites.
3. The mutation controls are targeted to the central GHZ/W tripwires and variant promotion, not broad mutation testing of every row.

## Validator evidence

Both commands exited 0 with `{"ok": true}`:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/nesting_consistency_family_v0/nesting_consistency_family_v0_exact_strength_validator.py
```

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/nesting_consistency_family_v0/results/nesting_consistency_family_v0_envelope_results.json
```

## Final classification

VERDICT: PASS as a bounded exact `scratch_diagnostic` family-comparison packet.

Ceiling restated: no variant promoted; no canonical nesting admission; no claim that GHZ nests; no all-quotients commute claim; no H/E, S4-S7, bridge, axis, manifold, or formal-admission promotion.
