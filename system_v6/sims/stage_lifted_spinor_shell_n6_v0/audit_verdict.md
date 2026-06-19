# Audit verdict - stage_lifted_spinor_shell_n6_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/stage_lifted_spinor_shell_n6_v0/`, except this `audit_verdict.md`.

Verdict: **GENUINE-WITH-CAVEATS**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as stage closure, canonical geometry, bridge/axis admission, physics, formal admission, completed constraint manifold, or ladder-trend evidence.

## Inputs and standard

Inputs read:

- Sim folder: `system_v6/sims/stage_lifted_spinor_shell_n6_v0/`
- Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
- Templates: committed `stage_lifted_spinor_shell_n4_v0/audit_verdict.md` and `stage_lifted_spinor_shell_n5_v0/audit_verdict.md`.
- Carry-forward packets: `geo_network_shell_coordinate_v0/` and `geo_bracketing_smt_lifted_v0/`.

Binding calibration: exactness-class stability replaces blanket byte-stability; genuine alternative methods are acceptable when values are right and method substitutions are honest; strength tokens are not verdict-bearing; one genuine derivation plus independent solver or cross-engine binding can satisfy the bar.

Fresh read-only checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_envelope_results.json
```

Result: `{"ok": true}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_julia.jl
```

Result: no violations.

I did not rerun the sim scripts because the build card says they write result JSONs; that would violate the read-only audit constraint.

## Q1 - lift genuine

Status: **PASS**.

This is a real six-site shell-supported construction, not a label join. Shell coordinates enter directly in source: `support_sites()` assigns each site `eta`, `theta`, `loop_phase`, `z=cos(2 eta)`, `psi_L`, and `psi_R` at `stage_lifted_spinor_shell_n6_v0_jax.py:225-243`.

The support object then constructs actual nodes, 12 tensor/path edges, 4 filled shell faces, TopoNetX/GUDHI/rustworkx/XGI receipts, and fail-capable support mutations at `stage_lifted_spinor_shell_n6_v0_jax.py:293-349`. Stored JAX values agree: `support_node_count=6`, `support_edge_count=12`, `support_face_count=4`.

Shell coordinates are consumed, not just printed. The S5/S6 lineage row substitutes each site's `eta` and `theta` into exported S5 `A,b`, emits `z_dot_from_exported_A_b`, `purity_derivative_from_exported_A_b`, and `s6_class`, and records the method as `derive z_dot=e_z^T(A*r_eta+b)` at `stage_lifted_spinor_shell_n6_v0_jax.py:353-405`. The leakage row records `shell_coordinate: z=cos(2 eta)` and the wrong-coordinate control `sin(2 eta)` at `stage_lifted_spinor_shell_n6_v0_jax.py:764-807`.

## Q2 - exact anchors

Status: **PASS-WITH-CAVEAT G10**.

Hand recomputation:

```text
ln(2) = 0.693147180559945
W6 single-site entropy
  = -(5/6)ln(5/6) - (1/6)ln(1/6)
  = 0.450561208866305
d = 64, d^2 = 4096
```

Direct recomputation over all 62 nonempty proper GHZ6 subsystems gave `min=max=0.6931471805599454`, so the mathematical all-bipartition GHZ6 anchor is correct. Stored JAX reports `GHZ_6_ln2_all_bipartitions=true`, `W_6_single_site_entropy=0.450561208866`, and `W_6_expected=0.450561208866`.

The source computes entropy with `qutip.ptrace/qutip.entropy_vn` at `stage_lifted_spinor_shell_n6_v0_jax.py:433-485`. Caveat G10 below: the source enumerates all six single-site cuts and three selected two-site cuts, not all 62 proper cuts. The all-bipartition statement is accepted because GHZ symmetry plus the fresh recomputation covers all proper cuts, not because the stored row exhaustively enumerates them.

The IC frame is a certificate, not a materialized `4096 x 4096` rank. The source says `rank_method = exact certified Hermitian matrix-unit IC frame rank; full 4096x4096 Gram rank not materialized`, stores `materialized_full_gram_rank=false`, and counts `d` diagonal projectors plus real-symmetric and imaginary-antisymmetric off-diagonal pairs at `stage_lifted_spinor_shell_n6_v0_jax.py:488-503`.

Hard adjudication of the IC certificate:

- Stored raw data: `d=64`, `diagonal_projectors=64`, `real_symmetric_pairs=2016`, `imaginary_antisymmetric_pairs=2016`, `effect_count=4096`, `frame_rank=4096`, `materialized_full_gram_rank=false`.
- Logic: diagonal matrix units plus symmetric and antisymmetric off-diagonal Hermitian matrix units form a real basis for Hermitian `64 x 64` matrices. Count is `64 + 2 * C(64,2) = 4096 = d^2`.
- Fresh small-piece verification: materializing the same Hermitian unit construction at `d=4` gives 16 effects and real vector-space rank 16.
- Positivity check: for epsilon `0.05`, `(I + eps H)/(d^2)` is positive for diagonal units and for symmetric/antisymmetric two-site units because the latter have eigenvalues in `{-1,0,1}`, giving minimum eigenvalue `(1 - 0.05)/4096 > 0`.

Therefore the IC row is sound as a stored exact certificate. It is not materialization of the full Gram/rank matrix, and the packet labels it honestly everywhere I found.

## Q3 - nesting

Status: **PASS**.

GHZ6 non-nesting is computed at `stage_lifted_spinor_shell_n6_v0_jax.py:814-831`. Fresh recomputation:

```text
Tr_one(GHZ6) spectrum = [0.5, 0.5, 0.0, 0.0]
distance to pure GHZ5 = 0.707106781187
```

W6 nesting is computed at `stage_lifted_spinor_shell_n6_v0_jax.py:834-863`. Fresh recomputation:

```text
Tr_one(W6) = (5/6)|W5><W5| + (1/6)|00000><00000|
spectrum = [0.833333333333, 0.166666666667, 0.0, 0.0]
distance to expected weighted state = 0.0
```

Controls flip. Stored controls fire for GHZ non-nesting, W6 weighted nesting, W6 separable control, and W6 permuted-weight control. Stored control distances are `1.178511301978` for separable W and `0.942809041582` for permuted weights.

## Q4 - Cl(12) certificate

Status: **PASS**.

The Cl(12) construction is real and the maximality substitution is honestly labeled as a certificate. The source builds the witness labels and pairwise symplectic test at `stage_lifted_spinor_shell_n6_v0_jax.py:575-633`, then builds 12 Jordan-Wigner gamma matrices plus chirality on `C^64`, checks squares, anticommutators, and chirality split at `stage_lifted_spinor_shell_n6_v0_jax.py:649-684`.

Stored 13-Pauli witness:

```text
XIIIII, YIIIII, ZXIIII, ZYIIII, ZZXIII, ZZYIII, ZZZXII,
ZZZYII, ZZZZXI, ZZZZYI, ZZZZZX, ZZZZZY, ZZZZZZ
```

Fresh recomputation mapped the stored labels to symplectic vectors in `F_2^12` and checked all 78 pairs:

```text
witness_count = 13
pair_count = 78
all_pairs_anticommute = true
rank(span(witness vectors)) = 12
rank(K_13) = 12
rank(K_14) = 14
ambient rank F_2^12 = 12
```

The exclusion argument is sound: for an `m`-family of pairwise anticommuting Paulis, the Gram matrix `K_m` has zero diagonal and one off-diagonal over `F_2`. Its rank is `m-1` for odd `m` and `m` for even `m`. Thus `K_13` has rank 12 and is admissible in the 6-qubit symplectic space, while `K_14` has rank 14 and cannot embed in ambient rank 12.

The z3/cvc5 rows are derived from raw rank integers, not asserted booleans: source binds `gram_rank_K14 == 14`, `ambient_symplectic_rank_6q == 12`, and `gram_rank_K14 <= ambient_rank`, producing `unsat` in z3/cvc5 at `stage_lifted_spinor_shell_n6_v0_jax.py:593-608`. PyTorch mirrors the same row; Julia marks the solver result as mirrored by Python legs. Stored bound certificate agrees: `rank_K_13_over_F2=12`, `rank_K_14_over_F2=14`, `ambient_symplectic_rank_6q=12`, z3/cvc5 `unsat`.

This is a certificate over the finite Pauli symplectic model, not a materialized exhaustive clique search over 4095 vertices. The visible fields I found label it as `exact_pauli_symplectic_rank_maximality_certificate` or `symplectic-rank certificate`, so the n=5 G9 wording defect is not repeated.

## Q5 - patterns held

Status: **PASS-WITH-CAVEAT G11**.

G1 lineage held. The n=6 JAX result records `s5_result_path`, `s5_result_sha256`, `s5_pin_sha256`, `s6_result_path`, `s6_result_sha256`, S6 taxonomy, emitted classes, and per-site `s5_A`, `s5_b`, `z_dot_from_exported_A_b`, `purity_derivative_from_exported_A_b`, and `s6_class`. Source path and fields are at `stage_lifted_spinor_shell_n6_v0_jax.py:353-405`.

G2 capability receipts held. The capability-probe validators returned no violations for JAX, PyTorch, and Julia.

G3 full-rerun mutation controls held. Support mutations are full-rerun-style controls with failing values and `gate_passed_after_mutation=false` for global-shell-only, no-face, duplicate-eta, and collapsed-shell at `stage_lifted_spinor_shell_n6_v0_jax.py:246-290`. Envelope gate also requires `mutation_controls_rerun_with_failing_values=true` at `stage_lifted_spinor_shell_n6_v0_envelope.py:186-188`.

G6 stored certificates held. The Cl(12) maximality substitution stores the witness, pair count, all-pairs flag, `K_13`/`K_14` ranks, ambient rank, and z3/cvc5 rank-bound results. Fresh recomputation matched.

G8 one-to-one `tool_calls` held by count and identity:

```text
JAX:     11 tool_calls / 11 load-bearing tools, missing=[], extra=[]
Julia:    8 tool_calls /  8 load-bearing tools, missing=[], extra=[]
PyTorch:  8 tool_calls /  8 load-bearing tools, missing=[], extra=[]
```

Caveat G11: two JAX `tool_calls` prose fields have stale boundary text. `stage_lifted_spinor_shell_n6_v0_jax.py:716` names boundary faces `f012/f234/f024`, but the actual n=6 faces are `f012`, `f234`, `f045`, and `f135`. `stage_lifted_spinor_shell_n6_v0_jax.py:718` says "six support nodes and seven path edges", but the computed support has 12 edges. This does not falsify the support object or one-to-one count, but those tool-call descriptions should not be cited as exact n=6 support facts until corrected.

## Q6 - carry-forward

G4: **OPEN for n=6**. The `geo_network_shell_coordinate_v0` re-audit addendum earns n=5 coordinate rows, and it explicitly says the allowed rows cover `n3/n4/n5` only at `geo_network_shell_coordinate_v0/audit_verdict.md:240-282`. I found no n=6 coordinate row in that packet and no named static network-level coordinate family row inside this n=6 rung. The n=6 build card also says G4 remains open at `build_card.md:44`.

G5-at-n6: **OPEN**. The `geo_bracketing_smt_lifted_v0` audit earns n=4 closure only and explicitly says not n=5 at `geo_bracketing_smt_lifted_v0/audit_verdict.md:499-501`; packet source/result scope says committed n=3 and n=4 exports with n=5 not read. I found no n=6 raw-object bracketing SMT proof. The n=6 envelope itself says raw-object bracketing SMT remains the separate packet at `stage_lifted_spinor_shell_n6_v0_envelope.py:239`, and the build card says G5-at-n6 remains open at `build_card.md:45`.

G7-lifted: **OPEN**. GHZ/W density and entropy rows remain named carrier-state rows with shell-placement receipts, not coordinate-parameterized lifted state families. The entropy source labels the rows `density_only_value_with_shell_placement_receipt` at `stage_lifted_spinor_shell_n6_v0_jax.py:458-466`, and the build card says G7-lifted remains open at `build_card.md:46`.

## Q7 - standard

Status: **PASS-WITH-CAVEATS**.

Mode is honest. The envelope declares `engine_contract.mode=all_three_full_sims`, lanes `julia`, `jax`, and `pytorch`, and `reads_peer_result=false` at `stage_lifted_spinor_shell_n6_v0_envelope.py:226-230`. Seeds are declared identical, no peer-result reads are gated, and source hashes are fresh at `stage_lifted_spinor_shell_n6_v0_envelope.py:172-195`.

Controls can fail and do fail: global-shell-only, no-face, duplicate-eta, collapsed-shell, density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W weighted nesting, W separable, and W permuted-weight controls all fire in stored rows.

SMT is not derived-boolean-only. Density-erasure z3/cvc5 rows bind raw integer density and shell ids at `stage_lifted_spinor_shell_n6_v0_jax.py:884-957`; rank-bound z3/cvc5 rows bind raw rank integers as described in Q4.

Seeds, ceilings, and claim fences are explicit. The envelope allows only scratch n=6 existence, three-engine agreement on named finite scalar rows, and control-firing claims; it disallows stage closure, canonical geometry, bridge/axis admission, trend across n=6..8, and promotion beyond scratch diagnostic at `stage_lifted_spinor_shell_n6_v0_envelope.py:202-218`.

No ladder-trend claim is admitted. The only trend-like language I found is in disallowed claims or in carry-forward bookkeeping.

## Recomputations

Exact anchors:

```text
GHZ6 all proper subsets checked = 62
GHZ6 min entropy = 0.6931471805599454
GHZ6 max entropy = 0.6931471805599454
ln2 = 0.6931471805599453
W6 single-site entropy = 0.4505612088663045
W6 formula = 0.45056120886630463
IC d/effects/rank/materialized = 64 / 4096 / 4096 / false
IC small d=4 materialized rank = 16 / 16
```

Nesting:

```text
GHZ trace-one spectrum = [0.5, 0.5, 0.0, 0.0]
GHZ distance to pure GHZ5 = 0.707106781187
W trace-one spectrum = [0.833333333333, 0.166666666667, 0.0, 0.0]
W distance to expected weighted state = 0.0
```

Cl(12) certificate:

```text
witness_count = 13
pair_count = 78
all_pairs_anticommute = true
rank(span(witness vectors)) = 12
rank(K_13) = 12
rank(K_14) = 14
ambient rank F_2^12 = 12
z3 rank-bound = unsat
cvc5 rank-bound = unsat
```

Envelope and tools:

```text
envelope all_pass = true
max_divergence = 0.0
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
tool_calls one-to-one = JAX 11/11, Julia 8/8, PyTorch 8/8
```

## Named caveats

G4. Static network-level shell coordinate remains open for n=6. The separate G4 packet has earned n3/n4/n5 rows, but no n=6 row is present here or there.

G5. Raw-object bracketing SMT remains open for n=6. The current bracketing packet covers n3/n4; this n=6 packet keeps bracketing numeric/symbolic and points to the separate packet.

G7. Lifted-rung coordinate-parameterized GHZ/W state families remain open. n=6 places named carrier states on shell support and computes density/entropy/nesting rows, but does not make GHZ/W families coordinate-parameterized.

G10. GHZ6 all-bipartition label is theorem-backed and fresh-recomputed, but the stored source enumerates representative cuts rather than all 62 proper cuts. Cite the all-bipartition anchor as audit-recomputed/theorem-backed, not as stored exhaustive enumeration.

G11. JAX `tool_calls` prose has stale n=6 support descriptions for two rows: one boundary lists stale faces, and one input says seven path edges while the support object has 12. The computed support and G8 count still pass.

## Final verdict

**GENUINE-WITH-CAVEATS**.

Accept as:

- a real n=6 lifted spinor-shell scratch diagnostic;
- a six-site support object with explicit per-site shell coordinates, 12 path edges, 4 filled shell faces, topology receipts, S5/S6 leakage lineage, and fail-capable controls;
- correct GHZ6, W6, IC-frame certificate, nesting-law, mutation-control, capability, one-to-one tool-call, and three-engine agreement checks at scratch scope;
- a sound Cl(12) Pauli-surface maximality substitution via symplectic-rank certificate, with stored witness and fresh rank recomputation.

Reject as:

- closure of G4, G5-at-n6, or G7-lifted;
- materialization of the full `4096 x 4096` IC Gram/rank matrix;
- exhaustive max-clique materialization over 4095 Pauli vertices;
- stage closure, canonical geometry, bridge/axis admission, formal admission, physics, or ladder-trend evidence.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Builder hardening addendum - 2026-06-10

Scope: one bounded hardening pass for G10 and G11 only. The fresh verdict above still stands: `GENUINE-WITH-CAVEATS` at `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

G10 is now closed for this packet. JAX, Julia, and PyTorch store `GHZ_6_all_proper_bipartitions` under `P5_entropy`, with all 62 nonempty proper cuts represented and `S_A = 0.69314718056` for every row. The existing representative entropy rows are still retained under `P5_entropy.rows` for continuity.

G11 is now closed for this packet. The JAX `tool_calls` prose now names the actual boundary faces `f012/f234/f045/f135`, and the rustworkx support prose now says the support has 12 edges rather than seven path edges.

Fresh full reruns completed:

```text
JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'include("system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_julia.jl"); println("julia_parse_ok")'
```

Result: `stage_lifted_spinor_shell_n6_v0_julia_DONE all_pass=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_jax.py
```

Result: `stage_lifted_spinor_shell_n6_v0_jax_DONE all_pass=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_pytorch.py
```

Result: `stage_lifted_spinor_shell_n6_v0_pytorch_DONE all_pass=true`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_envelope.py
```

Result: `stage_lifted_spinor_shell_n6_v0_ENVELOPE_DONE all_pass=true max_divergence=0.0`.

Strict validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_envelope_results.json
```

Result:

```json
{
  "ok": true,
  "result_json": "system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_envelope_results.json"
}
```

Still open exactly as audited: G4-at-n6, G5-at-n6, and G7-lifted. This addendum does not promote stage closure, canonical geometry, bridge/axis admission, trend evidence, formal admission, or physics claims.
