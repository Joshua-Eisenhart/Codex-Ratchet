# Audit verdict - stage_lifted_spinor_shell_n7_v0

Fresh audit date: 2026-06-10.

Scope: read-only audit of `system_v6/sims/stage_lifted_spinor_shell_n7_v0/`, except this `audit_verdict.md`.

Verdict: **GENUINE-WITH-CAVEATS**.

Ceiling remains: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. Do not use this packet as stage closure, canonical geometry, bridge/axis admission, physics, formal admission, completed constraint manifold, or ladder-trend evidence.

## Inputs and standard

Inputs read:

- Sim folder: `system_v6/sims/stage_lifted_spinor_shell_n7_v0/`
- Calibrated bar: `system_v6/receipts/audit_bar_calibration_20260610.md`
- Templates: committed `stage_lifted_spinor_shell_n5_v0/audit_verdict.md` and `stage_lifted_spinor_shell_n6_v0/audit_verdict.md`, including addenda and carried caveats.
- Carry-forward packets: `geo_network_shell_coordinate_v0/` and `geo_bracketing_smt_lifted_v0/`.

Binding calibration: exactness-class stability replaces blanket byte-stability; genuine alternative methods are acceptable when values are right and method substitutions are honest; strength tokens are not verdict-bearing; one genuine derivation plus independent solver or cross-engine binding can satisfy the bar.

Fresh read-only checks run:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_envelope_results.json
```

Result: `{"ok": true, "result_json": "system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_envelope_results.json"}`.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_jax.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_pytorch.py
```

Result: no violations.

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/verify_load_bearing_has_capability_probe.py --sim system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_julia.jl
```

Result: no violations.

I did not rerun the sim scripts because they write result JSONs; rerunning them would violate the read-only audit constraint. The fresh audit recomputed the requested anchors and certificates independently from stored source/result data.

## Q1 - lift genuine

Status: **PASS**.

This is a real seven-site shell-supported construction, not a label join. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:225-240` constructs per-site `eta`, `theta`, `loop_phase`, `z`, `psi_L`, and `psi_R`; the decisive coordinate line is `z = cos(2 eta)`. The support object then constructs ring/skip edges, five filled faces, TopoNetX, GUDHI, rustworkx, XGI, and mutation controls at `stage_lifted_spinor_shell_n7_v0_jax.py:293-351`.

Stored coordinate entry, quoted from `rows.P2_support_object.sites[0]`:

```json
{
  "site_id": "q0",
  "shell_id": "shell_0",
  "hopf_node_id": "hopf_ring_0:q0",
  "eta": 0.196349540849,
  "theta": 0.0,
  "loop_phase": 0.196349540849,
  "z": 0.923879532511,
  "psi_L": [0.980785280403, 0.0],
  "psi_R": [0.195090322016, -0.0]
}
```

Direct readout: 7 sites, 14 tensor/path edges, and 5 filled shell faces `f012`, `f123`, `f234`, `f345`, `f456`; `rows.P2_support_object.pass=true` in JAX, Julia, and PyTorch. Shell coordinates are consumed by S5/S6 lineage and leakage rows: the source substitutes per-site `eta` and `theta` into exported S5 `A,b` and emits `z_dot=e_z^T(A*r_eta+b)` at `stage_lifted_spinor_shell_n7_v0_jax.py:355-380`.

## Q2 - exact anchors

Status: **PASS**.

Hand recomputation:

```text
ln(2) = 0.6931471805599453
W7 single-site entropy
  = -(6/7)ln(6/7) - (1/7)ln(1/7)
  = 0.410116318288409
stored W7 = 0.410116318288
d = 128
128 + 2*C(128,2) = 128 + 2*8128 = 16384
```

The stored W7 value matches to the packet's rounded precision. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:487` pins the exact W7 expression as `-(6/7)log(6/7)-(1/7)log(1/7)`, and `stage_lifted_spinor_shell_n7_v0_jax.py:490-504` compares the stored row against the numeric formula.

GHZ7 all-cut anchor survives. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:467-480` iterates `mask in range(1, 2**N_QUBITS - 1)` and stores every `S_A`, so for n=7 the expected count is `2^7 - 2 = 126`. Direct JSON count: 126 rows. Direct JSON uniqueness check: all stored `S_A` values are `0.69314718056`.

Spot recomputation from a fresh NumPy partial trace:

```text
cut q0|q123456:   S_A = 0.6931471805599454
cut q012|q3456:   S_A = 0.6931471805599454
cut q024|q1356:   S_A = 0.6931471805599454
```

The stored rows include the 3-site cut `q012|q3456` and the non-contiguous 3-site cut `q024|q1356`, both with `S_A=0.69314718056`.

The IC frame is honestly a matrix-unit certificate, not a materialized rank. Stored row `rows.P3_density_quotient.ic_povm_separation` reports `d=128`, `effect_count=16384`, `expected_d_squared=16384`, `frame_rank=16384`, `materialized_full_gram_rank=false`, and decomposition `128 + 8128 + 8128`. Source quote: all three legs say "full 16384x16384 Gram rank not materialized" and set `materialized_full_gram_rank=false` (`stage_lifted_spinor_shell_n7_v0_jax.py:518-522`; `stage_lifted_spinor_shell_n7_v0_julia.jl:403-406`; `stage_lifted_spinor_shell_n7_v0_pytorch.py:553-556`). The build card says the full matrix was not materialized at `build_card.md:32`. I found no contradictory materialized-rank citation.

## Q3 - nesting

Status: **PASS**.

GHZ7 trace-one non-nesting is computed, not asserted. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:839-856` says `Tr_one(|GHZ_7><GHZ_7|)` is a rank-2 classical mixture, not pure `|GHZ_6><GHZ_6|`. Fresh recomputation:

```text
Tr_one(GHZ7) spectrum top4 = [0.5, 0.5, 0.0, 0.0]
distance to pure GHZ6 = 0.7071067811865474
stored distance = 0.707106781187
```

W7 trace-one nesting is computed, not asserted. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:859-888` states `Tr_one(|W_7><W_7|)=(6/7)|W_6><W_6|+(1/7)|000000><000000|`. Fresh recomputation:

```text
expected weights = [6/7, 1/7] = [0.8571428571428571, 0.14285714285714285]
reduced spectrum top4 = [0.8571428571428569, 0.14285714285714282, 7.7e-18, 0.0]
distance to expected weighted state = 3.34e-16
stored rounded distance = 0.0
```

Controls flip. Stored controls fire for GHZ non-nesting, W weighted nesting, W separable, and W permuted-weight. JAX stored distances: separable control `1.212183053463`; permuted-weight control `1.010152544552`.

## Q4 - Cl(14) certificate

Status: **PASS**.

The constructive family and finite exclusion certificate survive. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:596-658` builds the stored 15-Pauli witness, maps labels to symplectic vectors, checks pairwise anticommutation, and binds raw solver rank values; `stage_lifted_spinor_shell_n7_v0_jax.py:674-708` constructs 14 Jordan-Wigner gamma matrices plus chirality on the `C^128` carrier and records chirality split `64+64`.

Stored 15-Pauli witness:

```text
XIIIIII, YIIIIII, ZXIIIII, ZYIIIII, ZZXIIII,
ZZYIIII, ZZZXIII, ZZZYIII, ZZZZXII, ZZZZYII,
ZZZZZXI, ZZZZZYI, ZZZZZZX, ZZZZZZY, ZZZZZZZ
```

Fresh recomputation over stored labels:

```text
witness_count = 15
pair_count = 105
all_pairs_anticommute = true
rank(span(witness vectors)) = 14
rank(K_15) = 14
rank(K_16) = 16
ambient rank F_2^14 = 14
```

The exclusion argument is sound: an assumed 16-family of pairwise anticommuting Pauli strings has Gram matrix `K_16` with rank 16 over `F_2`; it cannot embed in the 7-qubit Pauli symplectic space of rank 14. The stored 15-family has `rank(K_15)=14`, so it is admissible and reaches the maximal family size.

The z3/cvc5 rows are raw-rank rows, not derived booleans. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:618-633` binds `gram_rank_K16 == 16`, `ambient_symplectic_rank_7q == 14`, and `gram_rank_K16 <= ambient_rank`; z3 and cvc5 return `unsat`. Stored bound certificate matches: `rank_K_15_over_F2=14`, `rank_K_16_over_F2=16`, `ambient_symplectic_rank_7q=14`, z3 `unsat`, cvc5 `unsat`. Julia honestly mirrors Python solver rows; PyTorch stores z3/cvc5 `unsat`.

## Q5 - patterns held

Status: **PASS-WITH-CAVEAT G13**.

G1 lineage held. The n=7 row records S5/S6 result paths, hashes, S6 taxonomy, per-site substituted `z_dot_from_exported_A_b`, `purity_derivative_from_exported_A_b`, and `s6_class`. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:355-380` derives `z_dot=e_z^T(A*r_eta+b)` from exported S5 `A,b`.

G2 capability held. The capability-probe validator returned no violations for JAX, PyTorch, and Julia.

G3 full-rerun mutations held. Source quote: `stage_lifted_spinor_shell_n7_v0_jax.py:246-290` defines global-shell-only, no-face, duplicate-eta, and collapsed-shell rerun-under-mutation controls with `gate_passed_after_mutation=false`. Stored top-level controls also fire density-only collapse, wrong shell coordinate, hardcoded-zero leakage, carrier mismatch, matrix-associator overclaim, GHZ nesting, W nesting, separable W, and permuted-weight W controls.

G6 certificates held. The Cl(14) row stores the witness labels, 105-pair check, `K_15/K_16` ranks, ambient rank, and z3/cvc5 rank-bound checks. Fresh recomputation matched.

G8 one-to-one `tool_calls` held by count:

```text
JAX:     11 load-bearing tools / 11 tool_calls
Julia:    8 load-bearing tools /  8 tool_calls
PyTorch:  8 load-bearing tools /  8 tool_calls
```

G10 exhaustive cuts held. Stored GHZ7 proper-cut count is 126, with a single unique stored `S_A` value `0.69314718056`; fresh spot recomputation matched one single-site cut and two 3-site cuts.

G11 prose-matches-computed held for the n=6 defect class. JAX `toponetx` boundary text says `rank-2 filled shell faces f012/f123/f234/f345/f456`; JAX `rustworkx` text says seven support nodes and fourteen support edges; PyTorch `torch_geometric` text says fourteen undirected support edges represented by twenty-eight directed columns. These match the actual n=7 objects: 7 nodes, 14 edges, 5 faces.

## Q6 - carry-forward

G4-at-n7: **OPEN**. `geo_network_shell_coordinate_v0` is a real coordinate packet, but its PIN and tool-call text scope inputs to committed n3/n4/n5. Source quote: `geo_network_shell_coordinate_v0_jax.py:35-38` names inputs `stage_lifted_spinor_shell_n3_v0,n4_v0,n5_v0`; tool-call text at `geo_network_shell_coordinate_v0_jax.py:258-260` says "committed n3/n4/n5 per-site z coordinates plus support graph edges." I found no n=7 coordinate row there. The n=7 build card also says G4-at-n7 remains open at `build_card.md:46`.

G5-at-n7: **OPEN**. `geo_bracketing_smt_lifted_v0` scopes its source packet to n3 plus n4/n5 extension rows and says n6 is not read. Source quote: `geo_bracketing_smt_lifted_v0_jax.py:40-43` says `source_packet` is n3 plus n4/n5 extension rows and `source_scope` is committed n3/n4/n5 exports. The n=7 packet keeps the bracketing row numeric; it does not close raw-object bracketing SMT for n=7. The n=7 build card also says G5-at-n7 remains open at `build_card.md:47`.

G7-lifted: **OPEN**. GHZ/W density and entropy rows remain named carrier-state rows with shell-placement/support receipts, not coordinate-parameterized lifted state families. Source quote: entropy rows still label values `density_only_value_with_shell_placement_receipt` at `stage_lifted_spinor_shell_n7_v0_jax.py:457-465`. The n=7 build card says G7-lifted remains open at `build_card.md:48`.

## Q7 - standard

Status: **PASS-WITH-CAVEATS G12/G13**.

Mode is honest. The envelope declares `engine_contract.mode=all_three_full_sims`, lanes `julia`, `jax`, and `pytorch`, and `reads_peer_result=false`; gate rows require identical seeds, fresh source hashes, no peer-result reads, mutation controls, S5/S6 lineage, solver agreement, and zero divergence at `stage_lifted_spinor_shell_n7_v0_envelope.py:172-194` and `228-233`.

Can-fail controls exist and fire. Mutation controls are stored with failing values; nesting controls have nonzero distances; density-erasure controls have SAT/UNSAT polarity; wrong-shell and hardcoded-zero leakage controls fire.

No verdict-bearing parity/echo/derived-boolean route was found. Solver rows bind raw integer tokens for density-erasure and raw rank integers for Cl(14) exclusion. Seeds are explicit (`20260610`) and identical across legs. Ceilings are explicit in all legs and the envelope. The envelope disallows stage closure, canonical geometry, bridge/axis admission, trend across n=7..8, promotion beyond scratch diagnostic, and closure of G4/G5/G7 at `stage_lifted_spinor_shell_n7_v0_envelope.py:212-219`.

No ladder-trend claim is admitted. Trend-like language appears only in disallowed claims or boundary text.

## Recomputations

Exact anchors:

```text
ln2 = 0.6931471805599453
W7 entropy = 0.410116318288409
stored W7 = 0.410116318288
GHZ7 stored proper-cut count = 126
GHZ7 stored unique S_A = [0.69314718056]
GHZ spot S(q0) = 0.6931471805599454
GHZ spot S(q012) = 0.6931471805599454
GHZ spot S(q024) = 0.6931471805599454
IC d/effects/rank/materialized = 128 / 16384 / 16384 / false
IC count formula = 128 + 2*C(128,2) = 16384
```

Nesting:

```text
Tr_one(GHZ7) spectrum top4 = [0.5, 0.5, 0.0, 0.0]
Tr_one(GHZ7) distance to pure GHZ6 = 0.7071067811865474
Tr_one(W7) weights = 6/7 W6 + 1/7 vacuum
Tr_one(W7) spectrum top4 = [0.8571428571428569, 0.14285714285714282, 7.7e-18, 0.0]
Tr_one(W7) distance to expected weighted state = 3.34e-16
```

Cl(14) certificate:

```text
witness_count = 15
pair_count = 105
all_pairs_anticommute = true
rank(span(witness vectors)) = 14
rank(K_15) = 14
rank(K_16) = 16
ambient rank F_2^14 = 14
z3 rank-bound = unsat
cvc5 rank-bound = unsat
```

Envelope and tool-call checks:

```text
strict source-backed validator = {"ok": true}
capability validators = no violations for JAX, PyTorch, Julia
all_pass = true
max_divergence = 0.0
JAX tool_calls = 11/11 load-bearing
Julia tool_calls = 8/8 load-bearing
PyTorch tool_calls = 8/8 load-bearing
classification = scratch_diagnostic
promotion_allowed = false
formal_admission_allowed = false
```

## Named caveats

G4. Static network-level shell coordinate remains open for n=7. The coordinate packet covers n3/n4/n5 only.

G5. Raw-object bracketing SMT remains open for n=7. The bracketing packet covers n3/n4/n5 only, and this n=7 packet keeps bracketing numeric.

G7. Lifted-rung coordinate-parameterized GHZ/W state families remain open. n=7 places named carrier states on shell support and computes density/entropy/nesting rows, but does not make GHZ/W families coordinate-parameterized.

G12. Worktree-evidence boundary: `git ls-files --error-unmatch system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_envelope_results.json` fails because the whole n=7 lane is untracked at audit time. This verdict covers current worktree artifacts, not committed `HEAD` evidence. This is not a mathematical failure, but it is a durability boundary until the owner serially stages/commits later.

G13. Fixture-wording boundary: two load-bearing package tool-call descriptions use fixture wording (`ITensor site support fixture` and `Cl(7) support fixture`). I did not use those fixture descriptions as decisive proof of Q1 or Q4. Q1 rests on the explicit sites/edges/faces/topology/control rows; Q4 rests on the Pauli witness, GF(2) ranks, and z3/cvc5 raw rank rows. The fixture wording should not be cited as independent mathematical evidence.

## Final verdict

**GENUINE-WITH-CAVEATS**.

Accept as:

- a real n=7 lifted spinor-shell scratch diagnostic in the current worktree;
- a seven-site support object with explicit per-site shell coordinates, 14 path edges, 5 filled shell faces, topology receipts, S5/S6 leakage lineage, and fail-capable controls;
- correct GHZ7, W7, IC matrix-unit certificate, nesting-law, Cl(14), mutation-control, capability, one-to-one tool-call, exhaustive-cut, and three-engine agreement checks at scratch scope;
- a sound Cl(14) Pauli-surface maximality certificate via a 15-Pauli witness plus GF(2) rank exclusion of 16.

Reject as:

- closure of G4-at-n7, G5-at-n7, or G7-lifted;
- committed `HEAD` evidence before this untracked lane is serially staged/committed;
- stage closure, canonical geometry, bridge/axis admission, physics, formal admission, completed constraint manifold, or ladder-trend evidence.
