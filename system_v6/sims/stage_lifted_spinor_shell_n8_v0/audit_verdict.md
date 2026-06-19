# Audit verdict - stage_lifted_spinor_shell_n8_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/stage_lifted_spinor_shell_n8_v0/`, except this `audit_verdict.md`.

Verdict: **GENUINE-WITH-CAVEATS**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as stage closure, canonical geometry, bridge/axis admission, physics, formal admission, completed constraint manifold, final-rung promotion, or ladder-trend evidence.

## Inputs and standard

Inputs read:

- Sim folder: `system_v6/sims/stage_lifted_spinor_shell_n8_v0/`
- Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
- Templates: committed `stage_lifted_spinor_shell_n6_v0/audit_verdict.md` and `stage_lifted_spinor_shell_n7_v0/audit_verdict.md`
- Advisory panel receipt: `system_v6/receipts/cross_model_anchor_recompute_panel2_20260610.md`
- Carry-forward packets: `geo_network_shell_coordinate_v0/` and `geo_bracketing_smt_lifted_v0/`

Binding calibration: exactness-class stability replaces blanket byte-stability; genuine alternative methods are acceptable when values are right and substitutions are honest; strength tokens are not verdict-bearing; one genuine derivation plus independent solver or cross-engine binding can satisfy the bar.

Fresh read-only checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_envelope_results.json
```

Result: `{"ok": true, "result_json": "system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_envelope_results.json"}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_jax.py
```

Result: no violations; 11 load-bearing tools checked.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_pytorch.py
```

Result: no violations; 8 load-bearing tools checked.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n8_v0/stage_lifted_spinor_shell_n8_v0_julia.jl
```

Result: no violations; 7 load-bearing tools checked.

I did not rerun the sim scripts because they write result JSONs; rerunning them would violate the read-only audit constraint. The fresh audit recomputed the requested anchors and certificates independently from stored source/result data.

## Q1 - lift genuine

Status: **PASS**.

This is a real eight-site support object, not a label join. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:244-262` constructs per-site `eta`, `theta`, `loop_phase`, `z`, `psi_L`, and `psi_R`; the coordinate line is:

```python
"z": r12(math.cos(2.0 * eta)),
```

The support source constructs ring edges, skip edges, and filled faces from the eight sites at `stage_lifted_spinor_shell_n8_v0_jax.py:312-370`. The pass gate at line 370 requires 8 nodes, 16 edges, 6 faces, connectedness, and dimension 2.

Stored coordinate entry, quoted from `rows.P2_support_object.sites[0]`:

```json
{
  "eta": 0.174532925199,
  "hopf_node_id": "hopf_ring_0:q0",
  "loop_phase": 0.174532925199,
  "psi_L": [0.984807753012, 0.0],
  "psi_R": [0.173648177667, -0.0],
  "shell_id": "shell_0",
  "site_id": "q0",
  "theta": 0.0,
  "z": 0.939692620786
}
```

Direct JSON readout: 8 sites, 16 tensor/path edges, and 6 filled faces `f012`, `f123`, `f234`, `f345`, `f456`, `f567`; `rows.P2_support_object.pass=true`.

Shell coordinates are consumed. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:374-428` derives `z_dot=e_z^T(A*r_eta+b)` from committed S5 exported `A,b` and substitutes this packet's per-site `eta` and `theta` into the leakage rows.

## Q2 - exact anchors

Status: **PASS**.

Hand recomputation:

```text
ln(2) = 0.6931471805599453
W8 single-site entropy
  = -(7/8)ln(7/8) - (1/8)ln(1/8)
  = 0.37677016125643675
stored W8 = 0.376770161256
d = 256
256 + 2*C(256,2) = 256 + 65280 = 65536
```

Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:506` pins the W8 formula as `-(7/8)log(7/8)-(1/8)log(1/8)`, and lines 509-524 compare the stored W row against that formula.

GHZ8 all-cut anchor survives under the pinned convention. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:487-499` iterates `mask in range(1, 2**N_QUBITS - 1)` and records each nonempty proper subset as `A`, with complement `B`. This is subset-labeled counting: A and complement are both present as separate rows. Direct JSON count: 254 rows. Direct JSON uniqueness check: all stored `S_A` values are `0.69314718056`.

The committed panel-2 receipt is advisory convergence only, not proof: `cross_model_anchor_recompute_panel2_20260610.md:13` records `254 subset-labeled cuts, all ln2`, and lines 21-23 adjudicate the 254 vs 127 split as convention, not a math disagreement.

Spot recomputation from the GHZ8 reduced-state spectrum:

```text
cut q0|q1234567:     S_A = ln(2) = 0.6931471805599453, stored 0.69314718056
cut q01|q234567:     S_A = ln(2) = 0.6931471805599453, stored 0.69314718056
cut q024|q13567:     S_A = ln(2) = 0.6931471805599453, stored 0.69314718056
cut q0123|q4567:     S_A = ln(2) = 0.6931471805599453, stored 0.69314718056
```

The IC frame is honestly a matrix-unit certificate, not a materialized full Gram rank. Stored row `rows.P3_density_quotient.ic_povm_separation` reports `d=256`, `effect_count=65536`, `expected_d_squared=65536`, `frame_rank=65536`, `materialized_full_gram_rank=false`, and decomposition `256 + 32640 + 32640`. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:528-543` computes the matrix-unit count and states `full 65536x65536 Gram rank not materialized`.

## Q3 - nesting

Status: **PASS**.

GHZ8 trace-one non-nesting is computed, not asserted. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:859-876` states `Tr_one(|GHZ_8><GHZ_8|)` is a rank-2 classical mixture, not pure `|GHZ_7><GHZ_7|`. Fresh recomputation:

```text
Tr_one(GHZ8) spectrum top4 = [0.5, 0.5, 0.0, 0.0]
distance to pure GHZ7 = 0.7071067811865474
stored distance = 0.707106781187
```

W8 trace-one nesting is computed, not asserted. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:879-908` states `Tr_one(|W_8><W_8|)=(7/8)|W_7><W_7|+(1/8)|0000000><0000000|`. Fresh recomputation:

```text
expected weights = [7/8, 1/8] = [0.875, 0.125]
reduced spectrum top4 = [0.875, 0.125, 0.0, 0.0]
distance to expected weighted state = 2.78e-17
stored rounded distance = 0.0
```

Controls flip. Stored W controls fire: separable control distance `1.237436867076`, permuted-weight control distance `1.06066017178`.

## Q4 - Cl(16) certificate

Status: **PASS**.

The constructive family and finite exclusion certificate survive. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:615-677` builds the stored 17-Pauli witness, maps labels to symplectic vectors, checks pairwise anticommutation, and binds raw rank values into z3/cvc5. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:693-729` materializes 16 Jordan-Wigner gamma matrices plus chirality as 256x256 complex matrices and records the chirality split.

Stored 17-Pauli witness:

```text
XIIIIIII, YIIIIIII, ZXIIIIII, ZYIIIIII, ZZXIIIII,
ZZYIIIII, ZZZXIIII, ZZZYIIII, ZZZZXIII, ZZZZYIII,
ZZZZZXII, ZZZZZYII, ZZZZZZXI, ZZZZZZYI,
ZZZZZZZX, ZZZZZZZY, ZZZZZZZZ
```

Fresh recomputation over stored labels:

```text
witness_count = 17
pair_count = 136
all_pairs_anticommute = true
rank(span(witness vectors)) = 16
rank(K_17) = 16
rank(K_18) = 18
ambient rank F_2^16 = 16
```

The exclusion argument is sound: an assumed 18-family of pairwise anticommuting Pauli strings has Gram matrix `K_18` with rank 18 over `F_2`; it cannot embed in the 8-qubit Pauli symplectic space of rank 16. The stored 17-family has `rank(K_17)=16`, so it is admissible and reaches the maximal family size.

The z3/cvc5 rows are raw-rank rows, not derived booleans. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:637-652` binds `gram_rank_K18 == 18`, `ambient_symplectic_rank_8q == 16`, and `gram_rank_K18 <= ambient_rank`; z3 and cvc5 return `unsat`. Stored bound certificate matches: `rank_K_17_over_F2=16`, `rank_K_18_over_F2=18`, `ambient_symplectic_rank_8q=16`, z3 `unsat`, cvc5 `unsat`.

Panel-2 advisory convergence: `cross_model_anchor_recompute_panel2_20260610.md:8` records both external models confirming the rank lemma, and line 17 says both independently confirm the F2 rank lemma. This is cited only as advisory convergence; proof here is the stored witness plus fresh recomputation.

## Q5 - boundary-stress rows

Status: **PASS**.

The Julia `CliffordAlgebras.CliffordAlgebra(16,0)` materialization failure is an honest infeasibility row, not a defect. Source quote: `stage_lifted_spinor_shell_n8_v0_julia.jl:40-43` marks `CliffordAlgebras` as `tried=true`, `used=false`, and says the Cl(16) maximality row uses the explicit Pauli/GF(2) certificate. Source quote: `stage_lifted_spinor_shell_n8_v0_julia.jl:628-633` records `constructed=false`, attempted object `CliffordAlgebra(16,0)`, route `certificate_route_after_boundary_stress`, and the observation that the package-object attempt was terminated after about `7m14s` at roughly `1.3GB` RSS.

The substitution is labeled everywhere I checked:

- Julia `TOOL_MANIFEST.CliffordAlgebras.reason`: supportive import only; package object terminated; certificate route used.
- Julia `TOOL_INTEGRATION_DEPTH.CliffordAlgebras`: `supportive`.
- Julia `rows.P6_order_gaps.CliffordAlgebras`: `constructed=false`, route `certificate_route_after_boundary_stress`.
- JAX/PyTorch Cl(16) rows label maximality as a stored symplectic-rank certificate while materializing the explicit 256x256 gamma/chirality rows.

Wall-clock and memory rows are present for the d=256 computations:

```text
JAX support/density/GHZ/Cl/leakage/nesting:
  0.010978s / 0.009374s / 0.604745s / 1.875390s / 9.109981s / 0.081955s
PyTorch support/density/GHZ/Cl/leakage/nesting:
  0.858376s / 0.269032s / 70.162239s / 0.955930s / 9.473085s / 0.912840s
Julia support/density/GHZ/Cl/leakage/nesting:
  32.863127s / 6.461165s / 4.842109s / 10.779115s / 6.404933s / 0.989594s
```

Each boundary row includes `exact_computation_status="computed_or_certificate_as_labeled"`, and density rows include `d=256`, `materialized_full_gram_rank=false`, and certificate `matrix-unit IC frame rank`.

## Q6 - patterns

Status: **PASS**.

G1 lineage held. The n=8 row records S5/S6 result paths and hashes, S6 taxonomy, emitted classes, and per-site substitutions into exported `A,b`. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:374-428` derives `z_dot=e_z^T(A*r_eta+b)` from committed S5 exported rows.

G2 capability held. The capability-probe validator returned no violations for JAX, PyTorch, and Julia.

G3 full-rerun mutations held. Source quote: `stage_lifted_spinor_shell_n8_v0_jax.py:265-309` defines global-shell-only, no-face, duplicate-eta, and collapsed-shell rerun-under-mutation controls with `gate_passed_after_mutation=false`. Stored top-level controls also fire density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W nesting, separable W, and permuted-weight W controls.

G6 certificates held. The Cl(16) row stores the witness, 136-pair check, `K_17/K_18` ranks, ambient rank, and z3/cvc5 rank-bound checks. Fresh recomputation matched.

G8 one-to-one `tool_calls` held by count:

```text
JAX:     11 load-bearing tools / 11 tool_calls
Julia:    7 load-bearing tools /  7 tool_calls
PyTorch:  8 load-bearing tools /  8 tool_calls
```

G10 exhaustive cuts held. Stored GHZ8 subset-labeled proper-cut count is 254, with a single unique stored `S_A` value `0.69314718056`; fresh spot recomputation matched one single-site cut, one two-site cut, one three-site cut, and one four-site cut.

G11/G13 prose-matches-computed and banned wording held. JAX `toponetx` text says filled faces `f012/f123/f234/f345/f456/f567`, matching the actual six faces; support object prose and computed rows match 8 nodes, 16 edges, 6 faces. Search over the target source/build card found no `fixture`, `parity`, `echo`, `derived-boolean`, or `derived_boolean` wording. The only `trend` hits are disallowed/boundary text.

## Q7 - carry-forward

Status: **OPEN, NOT A DEFECT**.

G4-at-n8: **OPEN**. `geo_network_shell_coordinate_v0` now has rows through n7 in its source/audit surface, but it does not read or compute the n8 packet. The n8 build card says `G4-at-n8 remains open` at `build_card.md:48`, and the n8 envelope explicitly disallows closure of `G4-at-n8` at `stage_lifted_spinor_shell_n8_v0_envelope.py:218-220`.

G5-at-n8: **OPEN**. `geo_bracketing_smt_lifted_v0` explicitly scopes itself through committed n3..n7 exports and records `n=8 not read`; it does not close n8 raw-object bracketing SMT. The n8 build card says `G5-at-n8 remains open` at `build_card.md:49`, and the n8 envelope disallows closure at `stage_lifted_spinor_shell_n8_v0_envelope.py:218-220`.

G7-lifted: **OPEN**. GHZ/W density and entropy rows remain named carrier-state rows with shell-placement receipts, not coordinate-parameterized lifted state families. Source quote: entropy rows label values `density_only_value_with_shell_placement_receipt` at `stage_lifted_spinor_shell_n8_v0_jax.py:483`. The n8 build card says `G7-lifted remains open` at `build_card.md:50`.

## Q8 - standard

Status: **PASS-WITH-OPEN-CARRY-FORWARD**.

Mode is honest. The envelope declares `engine_contract.mode=all_three_full_sims`, lanes `julia`, `jax`, and `pytorch`, and `reads_peer_result=false` at `stage_lifted_spinor_shell_n8_v0_envelope.py:228-233`. Seeds are explicit and identical: `20260610` in JAX, Julia, PyTorch, and envelope.

Can-fail controls exist and fire: shell-label-only, no-face, duplicate-eta, collapsed-shell, density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W weighted nesting, W separable, and W permuted-weight controls.

No verdict-bearing parity, fixture, echo, or derived-boolean route was found in the target source/build card scan. Solver rows bind raw integer tokens for density-erasure and raw rank integers for Cl(16) exclusion. Ceilings are explicit in all legs and the envelope.

No ladder-trend claim is admitted. Source quote: `stage_lifted_spinor_shell_n8_v0_envelope.py:212-219` disallows `ladder trend claim or final-rung promotion`, promotion beyond scratch diagnostic, and closure of G4/G5/G7. Build-card boundary text at `build_card.md:129` rejects trend claims across the ladder.

## Recomputations

Exact anchors:

```text
ln2 = 0.6931471805599453
W8 entropy = 0.37677016125643675
stored W8 = 0.376770161256
GHZ8 stored proper subset-labeled cuts = 254
GHZ8 stored unique S_A = [0.69314718056]
GHZ spot S(q0) = 0.6931471805599453
GHZ spot S(q01) = 0.6931471805599453
GHZ spot S(q024) = 0.6931471805599453
GHZ spot S(q0123) = 0.6931471805599453
IC d/effects/rank/materialized = 256 / 65536 / 65536 / false
IC count formula = 256 + 2*C(256,2) = 65536
```

Nesting:

```text
Tr_one(GHZ8) spectrum top4 = [0.5, 0.5, 0.0, 0.0]
Tr_one(GHZ8) distance to pure GHZ7 = 0.7071067811865474
Tr_one(W8) weights = 7/8 W7 + 1/8 vacuum
Tr_one(W8) spectrum top4 = [0.875, 0.125, 0.0, 0.0]
Tr_one(W8) distance to expected weighted state = 2.78e-17
W controls = separable 1.237436867076, permuted 1.06066017178
```

Cl(16) certificate:

```text
witness_count = 17
pair_count = 136
all_pairs_anticommute = true
rank(span(witness vectors)) = 16
rank(K_17) = 16
rank(K_18) = 18
ambient rank F_2^16 = 16
z3 rank-bound = unsat
cvc5 rank-bound = unsat
chirality split = 128 + 128
max anticommutator norm = 0.0
```

Envelope and tools:

```text
strict source-backed validator = {"ok": true}
capability validators = no violations for JAX, PyTorch, Julia
all_pass = true
max_divergence = 0.0
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
tool_calls one-to-one = JAX 11/11, Julia 7/7, PyTorch 8/8
```

## Named caveats

G4-at-n8. Static network-level shell-coordinate rows remain open for n8. Existing side lanes do not read this uncommitted n8 packet, and the n8 envelope explicitly disallows closing G4-at-n8.

G5-at-n8. Raw-object bracketing SMT remains open for n8. Existing bracketing extension rows cover prior rungs only and explicitly leave n8 unread.

G7-lifted. Lifted coordinate-parameterized GHZ/W state families remain open. n8 places named carrier states on shell support and computes density/entropy/nesting rows, but does not make GHZ/W families coordinate-parameterized.

## Final verdict

**GENUINE-WITH-CAVEATS**.

Accept as:

- a real n=8 lifted spinor-shell scratch diagnostic;
- an eight-site support object with explicit per-site shell coordinates, 16 path edges, 6 filled shell faces, topology receipts, S5/S6 leakage lineage, and fail-capable controls;
- correct GHZ8, W8, IC-frame certificate, nesting-law, mutation-control, capability, one-to-one tool-call, boundary-stress, and three-engine agreement checks at scratch scope;
- a sound Cl(16) Pauli-surface maximality certificate via explicit 17-Pauli witness, 136 anticommuting pairs, `rank(K_17)=16`, `rank(K_18)=18`, z3/cvc5 rank-bound `unsat`, and 256x256 gamma/chirality materialization;
- an honest Julia `CliffordAlgebras.CliffordAlgebra(16,0)` infeasibility/substitution record, not a failed claim.

Reject as:

- closure of G4-at-n8, G5-at-n8, or G7-lifted;
- materialization of the full `65536 x 65536` IC Gram/rank matrix;
- materialized Julia package object for `CliffordAlgebras.CliffordAlgebra(16,0)`;
- stage closure, canonical geometry, bridge/axis admission, formal admission, physics claim, final-rung promotion, or ladder-trend evidence.
