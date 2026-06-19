# Audit verdict - stage_lifted_spinor_shell_n5_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/stage_lifted_spinor_shell_n5_v0/`, except this `audit_verdict.md`.

Verdict: **GENUINE-WITH-CAVEATS**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as stage closure, canonical geometry, bridge/axis admission, physics, formal admission, completed constraint manifold, or ladder-trend evidence.

## Inputs and standard

Inputs read:

- Sim folder: `system_v6/sims/stage_lifted_spinor_shell_n5_v0/`
- Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
- Templates: committed `stage_lifted_spinor_shell_n3_v0/audit_verdict.md` and `stage_lifted_spinor_shell_n4_v0/audit_verdict.md`, including addenda.
- Carry-forward packets: `geo_bracketing_smt_lifted_v0/` and the uncommitted `geo_network_shell_coordinate_v0/` lane.

Binding calibration: exactness-class stability replaces blanket byte-stability; genuine alternative methods are acceptable when values are right and method substitutions are honest; strength tokens are not verdict-bearing; one genuine derivation plus independent solver or cross-engine binding can satisfy the bar.

Fresh checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_julia.jl
```

Result: no violations.

Direct recomputation script, read-only, recomputed exact anchors, nesting facts, the stored Pauli witness, GF(2) ranks for `K_11` and `K_12`, and envelope gates.

## Q1 - lift genuine

Status: **PASS**.

This is a real five-site shell-supported construction, not a label join. The support rows define per-site shell coordinates from five distinct etas: `eta`, `theta`, `loop_phase`, `z=cos(2 eta)`, `psi_L`, and `psi_R` enter at `stage_lifted_spinor_shell_n5_v0_jax.py:225-240`. The support object then constructs 5 nodes, 7 tensor/path edges, and 3 filled shell faces in TopoNetX/GUDHI/rustworkx/XGI at `stage_lifted_spinor_shell_n5_v0_jax.py:293-348`.

Shell coordinates are also consumed in lifted lineage and leakage rows, not just printed. The S5/S6 row substitutes each site's `eta` and `theta` into exported S5 `A,b`, emitting `z_dot_from_exported_A_b`, `purity_derivative_from_exported_A_b`, and `s6_class` at `stage_lifted_spinor_shell_n5_v0_jax.py:352-405`. The leakage row computes `z=cos(2 eta)`, finite-time leakage, aggregate leakage, wrong-shell controls, and hardcoded-zero controls at `stage_lifted_spinor_shell_n5_v0_jax.py:773-820`.

The builder card independently states the intended built support: "5 nodes, 7 tensor/path edges, and 3 filled shell faces" at `build_card.md:30`. The JSON agrees: direct audit read `support_node_count=5`, `support_edge_count=7`, `support_face_count=3`.

## Q2 - exact anchors

Status: **PASS**.

Hand recomputation:

```text
ln(2) = 0.693147180559945
W5 single-site entropy
  = -(4/5)ln(4/5) - (1/5)ln(1/5)
  = 0.500402423538188
d = 32, d^2 = 1024
```

The packet computes entropy using `qutip.ptrace/qutip.entropy_vn` over GHZ/W/product/cluster carrier states at `stage_lifted_spinor_shell_n5_v0_jax.py:432-482`. Stored anchors report `W_5_single_site_entropy=0.500402423538` and `W_5_expected=0.500402423538`; the recomputation matches to the packet's rounded precision.

For GHZ5, every proper bipartition reduced side has spectrum `{1/2, 1/2}` at the Schmidt boundary, so `S(A)=ln(2)`. The packet gates this as `GHZ_5_ln2_all_bipartitions=true`.

The IC frame is computed, not a dimension label: the source constructs 32 diagonal effects plus symmetric/antisymmetric off-diagonal effects and computes matrix rank at `stage_lifted_spinor_shell_n5_v0_jax.py:486-513`. Direct audit read `d=32`, `effect_count=1024`, `expected_d_squared=1024`, and `frame_rank=1024`.

## Q3 - nesting

Status: **PASS**.

GHZ5 non-nesting is computed at `stage_lifted_spinor_shell_n5_v0_jax.py:824-841`: tracing one qubit gives a rank-2 classical mixture, not pure GHZ4. Direct recomputation/readout: spectrum `[0.5, 0.5, 0.0, 0.0]`, distance to pure GHZ4 `0.707106781187`.

W5 nesting is computed at `stage_lifted_spinor_shell_n5_v0_jax.py:844-873`: `Tr_one(|W_5><W_5|)=0.8 |W_4><W_4| + 0.2 |0000><0000|`. Direct recomputation/readout: weights `W4=0.8`, `vacuum=0.2`, spectrum `[0.8, 0.2, 0.0, 0.0]`, distance to expected weighted state `0.0`.

Controls flip. The separable W control fires with distance `1.131370849898`; the permuted-weight control fires with distance `0.848528137424`. Support mutations are rerun-style controls with `gate_passed_after_mutation=false` and failing values for global-shell-only, no-face, duplicate-eta, and collapsed-shell mutations at `stage_lifted_spinor_shell_n5_v0_jax.py:246-290`.

## Q4 - symplectic-rank certificate for Cl(10)

Status: **PASS-WITH-CAVEAT**.

The constructive family is real. The source builds 10 Jordan-Wigner gamma matrices plus chirality on the `C^32` carrier, checks squares, pairwise anticommutators, chirality split, and the maximality receipt at `stage_lifted_spinor_shell_n5_v0_jax.py:659-694`. Julia and PyTorch mirror the same structure at `stage_lifted_spinor_shell_n5_v0_julia.jl:497-539` and `stage_lifted_spinor_shell_n5_v0_pytorch.py:537-572`.

Q4a: the stored 11-Pauli witness is pairwise anticommuting. Stored witness:

```text
XIIII, YIIII, ZXIII, ZYIII, ZZXII, ZZYII, ZZZXI, ZZZYI, ZZZZX, ZZZZY, ZZZZZ
```

Direct recomputation mapped each label to `(x,z) in F_2^10` and checked the symplectic product for all 55 pairs. Result: `witness_count=11`, `pair_count=55`, `all_pairs=true`. The stored certificate also records `witness_all_pairs_anticommute=true` and `witness_pair_count=55`.

Q4b: the exclusion argument is sound. For `m` pairwise-anticommuting nonidentity Paulis modulo phase, their symplectic vectors have Gram matrix `K_m` with zero diagonal and one off-diagonal. Over `F_2`, `rank(K_m)=m` for even `m` and `m-1` for odd `m`. Direct recomputation gave:

```text
rank(K_11) = 10
rank(K_12) = 12
ambient 5Q symplectic rank = 10
```

Therefore an assumed 12-family would require 12 independent rank inside an ambient `F_2^10` symplectic space, impossible. This is a derivation from the finite Pauli symplectic model, not a sampled search.

Q4c: the z3/cvc5 rows bind raw rank values, not derived booleans. JAX binds `gram_rank_K12 == 12`, `ambient_symplectic_rank_5q == 10`, and `gram_rank_K12 <= ambient_rank`, producing `unsat` in z3 and cvc5 at `stage_lifted_spinor_shell_n5_v0_jax.py:604-619`. PyTorch mirrors the same raw integer rank-bound solver rows at `stage_lifted_spinor_shell_n5_v0_pytorch.py:471-486`. Julia records the same theorem witness and points to the Python solver mirrors at `stage_lifted_spinor_shell_n5_v0_julia.jl:487-493`.

Q4d: the substitution is mostly but not perfectly honestly labeled. The build card explicitly says direct 1023-vertex branch-and-bound was infeasible and that the packet stores "an exact finite symplectic-rank certificate" at `build_card.md:35-36`. The stored `method` fields in all three legs also label the method as a symplectic-rank certificate. However, the JAX `Cl10_anchor.certificate` string says "Stored exact max-clique search over all 1023 nonidentity n=5 Pauli strings" at `stage_lifted_spinor_shell_n5_v0_jax.py:688`. That one citation is false to the disclosed method and remains caveat G9 below. The mathematical certificate survives; the citation wording does not.

## Q5 - G1-G3, G6-pattern, G8-pattern

Status: **PASS-WITH-CAVEAT G9**.

G1 held. The S5/S6 lineage row records S5 path/hash/pin, S6 path/hash, taxonomy, and per-site derived fields. Direct JSON check found `s5_result_path=system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json`, `s6_result_path=system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json`, non-empty hashes, `pass=true`, and emitted classes `cross_shell`, `leave_foliation`, and `projected_shell_preserve_but_Hopf_leave`.

G2 held. Capability-probe validators returned no violations for JAX, PyTorch, and Julia. Declared load-bearing tools are capability-backed at the validator level.

G3 held. Full-rerun-style mutation controls are present for shell-only, no-face, duplicate-eta, and collapsed-shell mutations with failing values and `gate_passed_after_mutation=false`; all top-level controls fired.

G6-pattern held mathematically for n=5. The previous n=4 G6 was a maximality artifact gap. Here the packet stores a symplectic-rank certificate with witness, pair count, ranks, ambient rank, and solver rows. It is not an exhaustive clique search, but the certificate is a sound replacement for excluding 12 anticommuting Paulis on the 5Q Pauli surface.

G8-pattern held. Direct JSON check found one `tool_calls` entry per declared load-bearing package in every leg: JAX `11/11`, Julia `8/8`, PyTorch `8/8`, with no missing or extra load-bearing tool-call records.

## Q6 - carry-forward

G4: **OPEN for n=5**. The separate `geo_network_shell_coordinate_v0` lane exists in the worktree and defines named static network-level shell coordinates, but `git ls-files` returned no tracked files for that lane. It is not committed evidence. The n=5 builder card also says "G4 remains open" at `build_card.md:43`. Therefore n=5 does not close G4.

G5: **OPEN for n=5**. The committed `geo_bracketing_smt_lifted_v0/audit_verdict.md` closes G5 for committed n=3 only and has n=4 extension rows pending/re-audit language. This n=5 packet keeps bracketing numeric/symbolic and explicitly says raw-object bracketing SMT remains the separate packet at `stage_lifted_spinor_shell_n5_v0_envelope.py:239`. The n=5 builder card also says "G5 remains open" at `build_card.md:44`. I found no n=5 raw-object bracketing SMT proof.

G7: **OPEN for n=5**. GHZ/W density and entropy rows remain named carrier-state rows with shell-placement/support receipts, not coordinate-parameterized state families. The n=5 builder card says "G7 remains open" at `build_card.md:45`, and the entropy source labels density rows as `density_only_value_with_shell_placement_receipt` at `stage_lifted_spinor_shell_n5_v0_jax.py:463`.

## Q7 - standard

Status: **PASS-WITH-CAVEATS**.

Mode is honest: the envelope declares `engine_contract.mode=all_three_full_sims`, with Julia, JAX, and PyTorch lanes at `stage_lifted_spinor_shell_n5_v0_envelope.py:226-230`. Seeds are declared identical (`20260610`) and no leg reads peer results. The envelope gates source hashes, required rows, acceptance, negative controls, mutation controls, S5/S6 lineage, solver agreement, and zero divergence at `stage_lifted_spinor_shell_n5_v0_envelope.py:172-194`.

Controls can fail and do fail under mutations: support mutations, density-only erasure, wrong shell coordinate, hardcoded-zero leakage, GHZ nesting, W separable, and W permuted-weight controls all fire. The density SMT is not a derived-boolean wrapper: z3/cvc5 bind raw density and shell integer values at `stage_lifted_spinor_shell_n5_v0_jax.py:894-978`. The symplectic rank-bound SMT binds raw rank integers as described in Q4.

No cross-run parity claim is needed for this verdict. Fixture isolation is acceptable at scratch scope because source hashes are fresh, result hashes are recorded, no peer-result reads are gated, and the direct audit recomputed the exact anchor and certificate rows. The remaining standard caveat is G9: one JAX citation string overclaims the certificate as a max-clique search.

## Recomputations

Exact anchor recomputation:

```text
ln2 = 0.693147180559945
W5 entropy = 0.500402423538188
stored W5 = 0.500402423538
IC d/effects/rank = 32 / 1024 / 1024
```

Nesting recomputation:

```text
GHZ trace-one spectrum = [0.5, 0.5, 0.0, 0.0]
GHZ distance to pure GHZ4 = 0.707106781187
W trace-one weights = 0.8 W4 + 0.2 vacuum
W trace-one spectrum = [0.8, 0.2, 0.0, 0.0]
W distance to expected weighted state = 0.0
```

Symplectic certificate recomputation:

```text
witness_count = 11
pair_count = 55
all_pairs_anticommute = true
rank(span(witness vectors)) = 10
rank(K_11) = 10
rank(K_12) = 12
ambient rank F_2^10 = 10
z3 rank-bound = unsat
cvc5 rank-bound = unsat
```

Envelope recomputation/readout:

```text
all_pass = true
gate_false = []
max_divergence = 0.0
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
```

## Named caveats

G4. Static network-level shell coordinate remains open for n=5. A separate `geo_network_shell_coordinate_v0` lane exists in the worktree, but it is untracked and not committed evidence; n=5 itself does not close this.

G5. Raw-object bracketing SMT remains open for n=5. The committed bracketing packet closes n=3 only; n=5 has numeric/symbolic bracketing and points to the separate packet for raw-object SMT.

G7. Lifted-rung coordinate-parameterized GHZ/W state families remain open. n=5 places named carrier states on shell support and computes their density/entropy/nesting rows, but does not make GHZ/W families coordinate-parameterized.

G9. Certificate-labeling caveat: the Cl(10) substitution is mathematically sound as a symplectic-rank certificate, but one JAX citation string says "Stored exact max-clique search" even though the disclosed method is not a 1023-vertex exhaustive clique search.

## Final verdict

**GENUINE-WITH-CAVEATS**.

Accept as:

- a real n=5 lifted spinor-shell scratch diagnostic;
- a five-site support object with explicit per-site shell coordinates, path edges, filled shell faces, topology receipts, S5/S6 leakage lineage, and fail-capable controls;
- correct GHZ5, W5, IC-POVM, nesting-law, mutation-control, capability, one-to-one tool-call, and three-engine agreement checks at scratch scope;
- a sound Cl(10) Pauli-surface maximality substitution via symplectic-rank certificate, with direct witness and rank recomputation.

Reject as:

- closure of G4, G5, or G7;
- a 1023-vertex exhaustive max-clique search;
- canonical geometry, stage closure, bridge/axis admission, formal admission, physics, or ladder-trend evidence.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
