# Audit Verdict - geo_bracketing_smt_lifted_v0

Date: 2026-06-10

Calibration used: `system_v6/receipts/audit_bar_calibration_20260610.md`. The binding bar keeps finite receipts, route genuineness, erasure honesty, can-fail controls, and scratch ceilings; it allows one genuine derivation plus independent solver/cross-engine binding where the split is honest.

## Verdict

**GENUINE-WITH-CAVEATS**.

This packet genuinely closes the standing **G5 bracketing SMT gap for committed n=3 only**, at scratch-diagnostic scope. It does not close n=4, n=5, stage closure, formal admission, canonical proof, bridge/axis admission, or ladder scaling.

Ceiling restated: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

## Source And Lineage Checked

- G5 being targeted is real: the n=3 audit says `G5. Bracketing SMT gap: bracketing/order rows are computed numerically/symbolically on the shared carrier, but no z3/cvc5 raw-object bracketing proof is present` at `system_v6/sims/stage_lifted_spinor_shell_n3_v0/audit_verdict.md:230`.
- Committed n=3 inputs are tracked and clean in this checkout. `git log -1` for the n=3 JAX/Julia result exports is commit `3a53d16afc715eea7e1e6e38dae10149cc5793ed` from `2026-06-10 14:29:59 -0700`.
- Consumed n=3 export hashes:
  - `system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_jax_results.json`: `18dc57bd1f9f404daaa857e2e4d6cf5761b4cd49e4f410f00dd66a9e8935c273`
  - `system_v6/sims/stage_lifted_spinor_shell_n3_v0/results/stage_lifted_spinor_shell_n3_v0_julia_results.json`: `c07e3e7f38f088cb899209e3a1baf6ff0399fba5a778d6a2bf4c2d2abc686a46`
- Caveat: `system_v6/sims/geo_bracketing_smt_lifted_v0/` itself is currently untracked in this checkout. That does not falsify the computation, but it blocks any wording stronger than "packet present in worktree" for this new audit target.

## Q1 Raw-Value Derivation

**Pass.** The proof derives from finite raw values loaded out of committed n=3 exports, not from a precomputed boolean and not from a hardcoded literal spectrum.

Quoted source:

```python
support = n3_jax["rows"]["P2_support_object"]
order_row = n3_jax["rows"]["P7_bracketing_boundary"]
edges_by_id = {edge["edge_id"]: edge for edge in edges}
left_path = ["e01", "e12"]
right_path = ["e12", "e01"]
left_outputs = [compose_path(edges_by_id, left_path, state, n_sites) for state in inputs]
right_outputs = [compose_path(edges_by_id, right_path, state, n_sites) for state in inputs]
left_counts = count_vector(left_outputs, dim)
right_counts = count_vector(right_outputs, dim)
diff_sq_counts = sum((a - b) ** 2 for a, b in zip(left_counts, right_counts))
```

Cite: `system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py:112-130`.

The z3 encoding binds those computed vectors before asserting equality:

```python
for var, value in zip(left, raw["left_counts"]):
    solver.add(var == value)
for var, value in zip(right, raw["right_counts"]):
    solver.add(var == value)
solver.add(z3.And([left[i] == right[i] for i in range(raw["dim"])]))
positive_verdict = solver.check()
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:160-169`.

The cvc5 encoding mirrors the same finite values:

```python
for var, value in zip(left, raw["left_counts"]):
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
for var, value in zip(right, raw["right_counts"]):
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, solver.mkInteger(value)))
equalities = [solver.mkTerm(Kind.EQUAL, left[i], right[i]) for i in range(raw["dim"])]
solver.assertFormula(solver.mkTerm(Kind.AND, *equalities))
positive_result = solver.checkSat()
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:214-221`.

Hand recomputation from `rows.P2_support_object.edges/sites`:

```text
inputs = [4, 2, 1]
left path = ["e01", "e12"], outputs = [7, 3, 1]
right path = ["e12", "e01"], outputs = [6, 3, 1]
left_counts  = [0, 1, 0, 1, 0, 0, 0, 1]
right_counts = [0, 1, 0, 1, 0, 0, 1, 0]
diff_sq_counts = 2
lifted_gap_sq = 2/3
lifted_gap_decimal = 0.816496580927726
exported P7 lifted_path_grouping_gap = 0.816496580928
```

The recomputed decimal matches the committed n=3 `rows.P7_bracketing_boundary.lifted_path_grouping_gap` within rounding.

## Q2 Erasure Flip Genuine

**Pass with a named caveat.** The erased-side flip is computed from erased objects, not toggled by a flag. The erased object is the density-quotient path-order erasure represented by total single-excitation mass.

Quoted source:

```python
left_density_token = z3.Int("erased_left_density_single_excitation_mass")
right_density_token = z3.Int("erased_right_density_single_excitation_mass")
erased.add(left_density_token == sum(raw["left_counts"]))
erased.add(right_density_token == sum(raw["right_counts"]))
erased.add(left_density_token == right_density_token)
erased_verdict = erased.check()
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:171-177`.

cvc5 mirrors the same erased values at `geo_bracketing_smt_lifted_v0_jax.py:223-231`. Julia Z3 mirrors the erased token computation at `geo_bracketing_smt_lifted_v0_julia.jl:158-164`.

Hand recomputation:

```text
erased_left_sum = sum(left_counts) = 3
erased_right_sum = sum(right_counts) = 3
erased_gap_sq = 0
```

Named caveat: this is a minimal quotient-erasure witness over the bracketing count vectors. It does not re-import the full B1 density table from the n=3 packet; it recomputes the order-erasing quotient token from the same raw path counts. That is enough for the scoped G5 flip, not a broader density-quotient theorem.

## Q3 Dual Solver

**Pass.** z3 and cvc5 each run positive/lifted and erased forms separately and agree.

Stored packet results:

```text
z3 positive = unsat
cvc5 positive = unsat
z3 erased = sat
cvc5 erased = sat
```

Fresh throwaway recomputation returned the same:

```text
z3:  positive=unsat, erased=sat, unit_nonzero_boundary=unsat
cvc5: positive=unsat, erased=sat, unit_nonzero_boundary=unsat
```

Envelope gate quotes the required agreement at `geo_bracketing_smt_lifted_v0_envelope.py:108-110`.

## Q4 Anti-Associativity Unit-Kill Control

**Pass with a named caveat.** The designed-fail row is encoded and can fail; it is not prose-only. The encoding is the unit-reduced consequence of `(a*e)*e = -a*(e*e)`, namely `a = -a` with `a != 0`, which is unsatisfiable over integers.

z3 source:

```python
boundary = z3.Solver()
a = z3.Int("a")
boundary.add(a == -a)
boundary.add(a != 0)
boundary_verdict = boundary.check()
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:179-183`.

cvc5 source:

```python
a = boundary.mkConst(b_int, "a")
boundary.assertFormula(boundary.mkTerm(Kind.EQUAL, a, boundary.mkTerm(Kind.NEG, a)))
boundary.assertFormula(boundary.mkTerm(Kind.NOT, boundary.mkTerm(Kind.EQUAL, a, boundary.mkInteger(0))))
boundary_verdict = cvc5_status(boundary.checkSat())
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:233-239`.

Sympy exact control also forces `a=0` at `geo_bracketing_smt_lifted_v0_jax.py:252-268`.

Named caveat: no explicit unit element `e` or binary multiplication table is modeled in SMT. The row is a valid unit-reduced scalar control, not a full algebra presentation control.

## Q5 Lineage And Honesty

**Pass with caveat.**

- Reads committed n=3 result exports read-only and cites their hashes. The loader reads only `N3_JAX_RESULT` and `N3_JULIA_RESULT`, then extracts `rows.P2_support_object` and `rows.P7_bracketing_boundary` (`geo_bracketing_smt_lifted_v0_jax.py:112-116`; Julia mirror at `geo_bracketing_smt_lifted_v0_julia.jl:95-99`).
- Static search found no reads of `stage_lifted_spinor_shell_n4_v0` or `stage_lifted_spinor_shell_n5_v0` in packet source other than the `n4_not_read` self-check string. Result JSONs contain no `stage_lifted_spinor_shell_n4_v0` or `stage_lifted_spinor_shell_n5_v0` path.
- Mode is honest: envelope declares lanes `["julia", "jax"]`, PyTorch `not_scoped`, and no tensor exchange (`geo_bracketing_smt_lifted_v0_envelope.py:150-175`).
- Capability receipts are present: z3/cvc5/sympy are `load_bearing`; Julia Z3 is `load_bearing` (`geo_bracketing_smt_lifted_v0_jax.py:51-64`; `geo_bracketing_smt_lifted_v0_julia.jl:42-50`).
- Controls can fail: lifted equality is UNSAT while erased equality is SAT; nonzero unit-reduced anti-associativity is UNSAT.
- Ceilings are explicit and enforced in the envelope gate: `classification`, `promotion_allowed`, and `formal_admission_allowed` are checked at `geo_bracketing_smt_lifted_v0_envelope.py:101-106`. Allowed claims are n=3-only; disallowed claims include `n=4 result`, `formal admission`, and `canonical proof beyond scratch diagnostic` at `geo_bracketing_smt_lifted_v0_envelope.py:130-142`.

Validator:

```text
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}
```

Named caveat: the packet directory is untracked in this checkout, so the packet artifact is not yet committed even though the consumed n=3 exports are committed.

## Q6 Closure Answer

For **n=3**, yes: this packet genuinely closes G5 at scratch-diagnostic scope. The closure is narrow: the committed n=3 lifted support edges produce non-equal bracketing count vectors, z3 and cvc5 derive UNSAT for equality from those finite values, and the erased quotient token flips to SAT.

For **n=4**, this n=3 proof is not structurally sufficient by itself. n=4 closure would need the same raw-object proof rerun on committed n=4 exports, with n=4 source hashes, n=4 path/support fields, recomputed n=4 lifted and erased values, and z3/cvc5 positive-erased-boundary results. The n=3 packet can be a proof template, not n=4 evidence.

## Named Caveats

1. `packet_untracked`: `geo_bracketing_smt_lifted_v0/` is present but untracked in the current worktree.
2. `minimal_erasure_witness`: erased flip is computed as path-order mass erasure over the bracketing count vectors, not by reusing the full B1 density table.
3. `unit_reduced_control`: the anti-associativity control encodes `a=-a, a!=0`; it does not encode an explicit unit element or multiplication table.
4. `n3_only`: no n=4/n=5 result is read or closed.

## Final Classification

`GENUINE-WITH-CAVEATS`.

Accept only as: `G5 scratch diagnostic closed for n=3 raw-object bracketing SMT`.

Reject as: stage closure, n=4 closure, n=5 closure, ladder-scaling evidence, formal admission, canonical proof beyond scratch diagnostic, PyTorch graph/autograd evidence, or bridge/axis admission.

## Builder Extension Addendum - n=4 Rows

Date: 2026-06-10

The fresh verdict above still stands as the audited verdict. The rows below are **builder-extension rows pending re-audit**. Ceiling is unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; reject as stage closure, audited n=4 closure, n=5 closure, ladder scaling, formal admission, canonical proof, PyTorch graph/autograd evidence, or bridge/axis admission.

What changed:

- Reran the same raw-object bracketing proof on committed `stage_lifted_spinor_shell_n4_v0` exports, read-only.
- Kept existing n=3 rows as exact-class rows and added clearly named `n4_*` rows in the JAX, Julia, and envelope results.
- Did not touch `stage_lifted_spinor_shell_n4_v0` source/results, `stage_lifted_spinor_shell_n5_v0`, or other active lanes.

n=4 lineage imports:

- `system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json`: `8ba4faf424e6f5a4a68d0220f3b3b658cc860ab643c7f3387ef8ea169282da3f`
- `system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_julia_results.json`: `d79fff73f5e7462abb6433bea05ecf574a084db198a9a2e5677da4fd32e1e3cd`
- Imported support field: `rows.P2_support_object`.
- Imported boundary field: `rows.P7_bracketing_boundary`.
- Path convention cited from committed source field: `system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py:order_and_bracketing_rows.path_gap`; Julia mirror source field: `system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_julia.jl:order_and_bracketing_rows.path_gap`.

n=4 recomputed rows:

```text
left path  = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
left_counts  = [0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,1]
right_counts = [0,1,0,1,0,0,1,0,0,0,0,0,1,0,0,0]
lifted_gap_squared = 1/1
lifted_gap_decimal = 1.0
exported P7 lifted_path_grouping_gap = 1.0
erased_gap_squared = 0
```

Solver polarity:

```text
n4 z3 positive = unsat
n4 cvc5 positive = unsat
n4 z3 erased = sat
n4 cvc5 erased = sat
n4 z3 unit boundary = unsat
n4 cvc5 unit boundary = unsat
n4 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

Fresh reruns and gates:

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py
=> ok:true

JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_julia.jl
=> ok:true

MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_envelope.py
=> ok:true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}
```

Capability receipts:

```text
verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_jax.py
=> z3 ok; cvc5 ok; sympy ok; violations=[]

verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_julia.jl
=> Z3 ok; violations=[]
```

## Focused Re-Audit Addendum - n=4 Extension Rows

Date: 2026-06-10

Scope: only the builder-extension `n4_*` rows above. The original n=3 verdict remains **GENUINE-WITH-CAVEATS** and was not re-litigated.

### 1. Committed n=4 Export Lineage

**Pass.** The n=4 rows consume the committed `stage_lifted_spinor_shell_n4_v0` exports, with source hashes and fields carried into the JAX and envelope results.

Quoted source:

```python
"n4": {
    "n": 4,
    "jax_result": N4_JAX_RESULT,
    "julia_result": N4_JULIA_RESULT,
    "left_path": ["e01", "e12", "e23"],
    "right_path": ["e23", "e12", "e01"],
    "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py:order_and_bracketing_rows.path_gap",
    "support_field": "rows.P2_support_object",
    "boundary_field": "rows.P7_bracketing_boundary",
}
```

Cite: `system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py:62-70`.

```python
support = source_jax["rows"]["P2_support_object"]
order_row = source_jax["rows"]["P7_bracketing_boundary"]
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:136-141`.

The stage n=4 source computes the cited path gap from actual n=4 CNOT paths:

```python
u01 = cnot(0, 1)
u12 = cnot(1, 2)
u23 = cnot(2, 3)
w = w_jax()
path_gap = jnp.linalg.norm(u23 @ u12 @ u01 @ w - u01 @ u12 @ u23 @ w)
```

Cite: `system_v6/sims/stage_lifted_spinor_shell_n4_v0/stage_lifted_spinor_shell_n4_v0_jax.py:784-788`.

Quoted result fields:

```text
n4_jax_result = system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json
n4_jax_sha256 = 8ba4faf424e6f5a4a68d0220f3b3b658cc860ab643c7f3387ef8ea169282da3f
n4_julia_result = system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_julia_results.json
n4_julia_sha256 = d79fff73f5e7462abb6433bea05ecf574a084db198a9a2e5677da4fd32e1e3cd
n4_support_field = rows.P2_support_object
n4_boundary_field = rows.P7_bracketing_boundary
```

Recomputed hash check:

```text
shasum -a 256 system_v6/sims/stage_lifted_spinor_shell_n4_v0/results/stage_lifted_spinor_shell_n4_v0_jax_results.json
=> 8ba4faf424e6f5a4a68d0220f3b3b658cc860ab643c7f3387ef8ea169282da3f
```

The n=4 stage exports are clean relative to the worktree, and their last touching commit is `30d21022e39f7a54a05f09da98bd843bb4489449` on `2026-06-10 15:11:11 -0700`.

### 2. n=4 SMT Sentences Derive From n=4 Raw Values

**Pass.** The solver sentences bind `raw["left_counts"]` and `raw["right_counts"]`, and for n=4 those raw vectors are 16-slot vectors derived from the n=4 support object. They are not n=3 structures relabeled.

Quoted source:

```python
left = [z3.Int(f"lifted_left_count_{i}") for i in range(raw["dim"])]
right = [z3.Int(f"lifted_right_count_{i}") for i in range(raw["dim"])]
for var, value in zip(left, raw["left_counts"]):
    solver.add(var == value)
for var, value in zip(right, raw["right_counts"]):
    solver.add(var == value)
solver.add(z3.And([left[i] == right[i] for i in range(raw["dim"])]))
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:206-215`.

cvc5 mirrors the same raw-value binding at `geo_bracketing_smt_lifted_v0_jax.py:254-267`.

Encoding diff recomputation:

```text
n3 SMT sexpr sha256 = bfe934550f5e278c4e74c04a2a45a0558c2ce3f3c92dc107e3a11687ffcf9596, line_count = 40, equality slots = 0..7
n4 SMT sexpr sha256 = 46e885124eb3a9c9919410903a77981e621e6e8b1e466cbe86d60acc09806125, line_count = 80, equality slots = 0..15
n3 paths = e01->e12 versus e12->e01; dim = 8
n4 paths = e01->e12->e23 versus e23->e12->e01; dim = 16
```

Raw value diff:

```text
n3 left_outputs/right_outputs = [7, 3, 1] / [6, 3, 1]
n4 left_outputs/right_outputs = [15, 7, 3, 1] / [12, 6, 3, 1]
n3 left_counts/right_counts = [0,1,0,1,0,0,0,1] / [0,1,0,1,0,0,1,0]
n4 left_counts/right_counts = [0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,1] / [0,1,0,1,0,0,1,0,0,0,0,0,1,0,0,0]
```

### 3. Hand Recompute: n=4 Count Vector And Erased Side

**Pass.** From `rows.P2_support_object.edges`:

```text
edges used:
e01 q0->q1
e12 q1->q2
e23 q2->q3
one-excitation inputs = [8, 4, 2, 1]
left path e01,e12,e23 outputs = [15, 7, 3, 1]
right path e23,e12,e01 outputs = [12, 6, 3, 1]
left_counts = [0,1,0,1,0,0,0,1,0,0,0,0,0,0,0,1]
right_counts = [0,1,0,1,0,0,1,0,0,0,0,0,1,0,0,0]
diff_sq_counts = 4
normalized lifted gap squared = 4/4 = 1
lifted_gap_decimal = 1.0
exported rows.P7_bracketing_boundary.lifted_path_grouping_gap = 1.0
```

Erased-side recomputation:

```text
sum(left_counts) = 4
sum(right_counts) = 4
erased_gap_squared = 0.0
```

This matches `n4_values.erased_gap_squared = 0.0` and `n4_values.exported_gap_matches_recomputed = true` in the JAX result.

### 4. Solver Results And Erased Flip

**Pass.** Positive, erased, and boundary results are present for both load-bearing solvers; the erased flip is computed from count-vector mass, not toggled by label.

Quoted source:

```python
erased.add(left_density_token == sum(raw["left_counts"]))
erased.add(right_density_token == sum(raw["right_counts"]))
erased.add(left_density_token == right_density_token)
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:217-223`.

cvc5 mirrors the erased-token computation at `geo_bracketing_smt_lifted_v0_jax.py:269-277`.

Quoted n=4 result values:

```text
n4 z3 positive verdict = unsat
n4 cvc5 positive verdict = unsat
n4 z3 erased_control_verdict = sat
n4 cvc5 erased_control_verdict = sat
n4 z3 unit_killed_nonzero_verdict = unsat
n4 cvc5 unit_killed_nonzero_verdict = unsat
n4 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

The envelope gate also requires these exact polarities:

```python
"n4_positive_z3_cvc5_agree_unsat": n4_z3_proof["verdict"] == "unsat" and n4_cvc5_proof["verdict"] == "unsat",
"n4_erased_control_flips_sat": n4_z3_proof["erased_control_verdict"] == "sat" and n4_cvc5_proof["erased_control_verdict"] == "sat",
"n4_unit_killed_nonzero_unsat": n4_z3_proof["unit_killed_nonzero_verdict"] == "unsat" and n4_cvc5_proof["unit_killed_nonzero_verdict"] == "unsat",
```

Cite: `geo_bracketing_smt_lifted_v0_envelope.py:148-150`.

Fresh read-only recomputation by importing the JAX diagnostic module, without writing result files, returned:

```text
n4 z3 = unsat / sat / unsat
n4 cvc5 = unsat / sat / unsat
```

### 5. n=3 Exact Rows Byte-Stable Against HEAD

**Pass.** Current n=3 exact rows were compared as canonical JSON subtrees against `git show HEAD:<path>` and match byte-for-byte after sorted compact serialization.

Compared fields:

```text
geo_bracketing_smt_lifted_v0_jax_results.json:
source_refs MATCH
raw_object MATCH
positive MATCH
negative MATCH
boundary MATCH
sympy_exact_crosscheck MATCH
crossover_proofs MATCH
values MATCH

geo_bracketing_smt_lifted_v0_julia_results.json:
source_refs MATCH
raw_object MATCH
positive MATCH
negative MATCH
boundary MATCH
crossover_proofs MATCH
values MATCH

geo_bracketing_smt_lifted_v0_envelope_results.json:
positive MATCH
negative MATCH
boundary MATCH
raw_object MATCH
crossover_proofs MATCH
divergence MATCH
```

### Re-Audit Conclusion

n=4 G5 closure EARNED for the narrow raw-object bracketing SMT extension rows because committed n=4 exports are hash-bound, n=4 solver encodings are 16-slot raw-value derivations rather than relabeled n=3 rows, hand recomputation matches the exported gap and erased value, both z3/cvc5 positive-erased-boundary polarities are present with Julia Z3 mirror, and n=3 exact rows stayed byte-stable; ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, not stage closure, not n=5, not ladder scaling, not formal admission, not canonical proof, not PyTorch graph/autograd evidence, and not bridge/axis admission.

## Builder Extension Addendum - n=5 Rows

Date: 2026-06-10

The audited n=3 verdict and the focused n=4 re-audit verdict above still stand. The rows below are **builder-extension rows pending re-audit**. Ceiling is unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; reject as stage closure, audited n=5 closure, ladder scaling, formal admission, canonical proof, PyTorch graph/autograd evidence, bridge evidence, or axis admission.

What changed:

- Reran the same raw-object bracketing proof on committed `stage_lifted_spinor_shell_n5_v0` exports, read-only and hash-bound.
- Kept existing n=3 and n=4 exact-class rows byte-stable against `HEAD` by canonical JSON subtree comparison.
- Added clearly named `n5_*` rows in the JAX, Julia, and envelope results.
- Did not touch `stage_lifted_spinor_shell_n6_v0`.

n=5 lineage imports:

- `system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_jax_results.json`: `f1f7aaeb2fd4376b5878ac71082891ccdaaf9535a498496b8793923968c8cbcb`
- `system_v6/sims/stage_lifted_spinor_shell_n5_v0/results/stage_lifted_spinor_shell_n5_v0_julia_results.json`: `d1d9500f8e4cf5b646b81adfd11c9d6a3fcccea0bbbca67cdad27c103a573450`
- Imported support field: `rows.P2_support_object`.
- Imported boundary field: `rows.P7_bracketing_boundary`.
- Path convention cited from committed source field: `system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_jax.py:order_and_bracketing_rows.path_gap`; Julia mirror source field: `system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_julia.jl:order_and_bracketing_rows.path_gap`.

n=5 recomputed rows:

```text
left path  = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
input_support_basis = [16, 8, 4, 2, 1]
left_outputs  = [30, 14, 6, 2, 1]
right_outputs = [24, 12, 6, 2, 1]
left_counts  = [0,1,1,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0]
right_counts = [0,1,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]
lifted_gap_squared = 4/5
lifted_gap_decimal = 0.8944271909999159
exported P7 lifted_path_grouping_gap = 0.894427191
erased_gap_squared = 0
```

Solver polarity:

```text
n5 z3 positive = unsat
n5 cvc5 positive = unsat
n5 z3 erased = sat
n5 cvc5 erased = sat
n5 z3 unit boundary = unsat
n5 cvc5 unit boundary = unsat
n5 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

Fresh reruns and gates:

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py
=> ok:true

JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_julia.jl
=> ok:true

MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_envelope.py
=> ok:true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}
```

Capability receipts:

```text
verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_jax.py
=> z3 ok; cvc5 ok; sympy ok; violations=[]

verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_julia.jl
=> Z3 ok; violations=[]
```

Existing-row stability check:

```text
n3 exact subtrees: JAX source_refs/raw_object/positive/negative/boundary/sympy/crossover_proofs/values MATCH HEAD; Julia source_refs/raw_object/positive/negative/boundary/crossover_proofs/values MATCH HEAD; envelope positive/negative/boundary/raw_object/crossover_proofs/divergence MATCH HEAD.
n4 exact subtrees: JAX n4_source_refs/n4_raw_object/n4_positive/n4_negative/n4_boundary/n4_sympy/n4_crossover_proofs/n4_values MATCH HEAD; Julia n4_source_refs/n4_raw_object/n4_positive/n4_negative/n4_boundary/n4_crossover_proofs/n4_values MATCH HEAD; envelope n4_positive/n4_negative/n4_boundary/n4_raw_object/n4_crossover_proofs/n4_divergence MATCH HEAD.
```

Builder-extension conclusion: n=5 extension rows are present, source-backed to committed n=5 exports, and the erased side flips honestly (`sat`) while lifted equality remains `unsat`. These are pending re-audit rows only; the packet ceiling and all prior audited verdict boundaries remain unchanged.

## Focused Re-Audit Addendum - n=5 Extension Rows

Date: 2026-06-10

Scope: only the new `n5_*` extension rows. The audited n=3 verdict and the earned n=4 re-audit verdict above still stand.

### 1. Committed n=5 Export Lineage

**Pass.** The n=5 rows consume the committed `stage_lifted_spinor_shell_n5_v0` JAX and Julia exports, with hashes carried into both engine results and recomputed directly.

Quoted source:

```python
N5_JAX_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n5_v0" / "results" / "stage_lifted_spinor_shell_n5_v0_jax_results.json"
N5_JULIA_RESULT = ROOT / "system_v6" / "sims" / "stage_lifted_spinor_shell_n5_v0" / "results" / "stage_lifted_spinor_shell_n5_v0_julia_results.json"
```

Cite: `system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py:31-32`.

```python
"n5": {
    "n": 5,
    "jax_result": N5_JAX_RESULT,
    "julia_result": N5_JULIA_RESULT,
    "left_path": ["e01", "e12", "e23"],
    "right_path": ["e23", "e12", "e01"],
    "path_lineage": "system_v6/sims/stage_lifted_spinor_shell_n5_v0/stage_lifted_spinor_shell_n5_v0_jax.py:order_and_bracketing_rows.path_gap",
    "support_field": "rows.P2_support_object",
    "boundary_field": "rows.P7_bracketing_boundary",
}
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:74-83`.

Recomputed hash check:

```text
shasum -a 256 stage_lifted_spinor_shell_n5_v0_jax_results.json
=> f1f7aaeb2fd4376b5878ac71082891ccdaaf9535a498496b8793923968c8cbcb

shasum -a 256 stage_lifted_spinor_shell_n5_v0_julia_results.json
=> d1d9500f8e4cf5b646b81adfd11c9d6a3fcccea0bbbca67cdad27c103a573450
```

The last commit touching the n=5 stage exports is `4047dc73b86b5193ab68b698640d6f648f7d6cc9` (`2026-06-10 15:41:32 -0700`), whose subject still marks G5 open at n=5 before this extension.

### 2. n=5 SMT Encodings Scale With The Object

**Pass.** The proof loads `rows.P2_support_object` and `rows.P7_bracketing_boundary`, derives `n_sites = len(sites)`, then sets `dim = 2**n_sites`. For n=5 this creates a 32-slot count-vector encoding, not a relabeled n=3 or n=4 encoding.

Quoted source:

```python
support = source_jax["rows"]["P2_support_object"]
order_row = source_jax["rows"]["P7_bracketing_boundary"]
sites = support["sites"]
n_sites = len(sites)
dim = 2**n_sites
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:152-156`.

```python
left = [z3.Int(f"lifted_left_count_{i}") for i in range(raw["dim"])]
right = [z3.Int(f"lifted_right_count_{i}") for i in range(raw["dim"])]
for var, value in zip(left, raw["left_counts"]):
    solver.add(var == value)
for var, value in zip(right, raw["right_counts"]):
    solver.add(var == value)
solver.add(z3.And([left[i] == right[i] for i in range(raw["dim"])]))
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:218-227`. cvc5 mirrors the same `raw["dim"]` and raw-count binding at `geo_bracketing_smt_lifted_v0_jax.py:266-278`; Julia Z3 mirrors it at `geo_bracketing_smt_lifted_v0_julia.jl:203-212`.

Encoding diff recomputation:

```text
n3 dim=8, equality slots 0..7, assertion lines=17, sexpr sha256=054d00877d7aa29563403b438b933f254ad5af1a1f426eeffca7644d609ad392
n4 dim=16, equality slots 0..15, assertion lines=33, sexpr sha256=1738e575a908875743167236c10e2a7273e48d408733c3c50b1559f0c2ab0334
n5 dim=32, equality slots 0..31, assertion lines=65, sexpr sha256=1e819f4181854c5c446737f2e7bb33522c0dd73f4003f888af27457f08aceb16
```

The committed n=5 stage source computes the cited path gap on the five-qubit `C^32` carrier:

```python
u01 = cnot(0, 1)
u12 = cnot(1, 2)
u23 = cnot(2, 3)
w = w_jax()
path_gap = jnp.linalg.norm(u23 @ u12 @ u01 @ w - u01 @ u12 @ u23 @ w)
```

Cite: `stage_lifted_spinor_shell_n5_v0_jax.py:754-758`.

Julia mirror:

```julia
path_gap = norm(cnot(2, 3) * cnot(1, 2) * cnot(0, 1) * dense_state("W") - cnot(0, 1) * cnot(1, 2) * cnot(2, 3) * dense_state("W"))
```

Cite: `stage_lifted_spinor_shell_n5_v0_julia.jl:588`.

### 3. Hand Recompute: n=5 Count Vector And Erased Side

**Pass.** Independent recomputation from the n=5 `rows.P2_support_object.edges` and one-excitation basis gives:

```text
n = 5
dim = 32
input_support_basis = [16, 8, 4, 2, 1]
left path = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
left_outputs = [30, 14, 6, 2, 1]
right_outputs = [24, 12, 6, 2, 1]
left_counts = [0,1,1,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0]
right_counts = [0,1,1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0]
diff_sq_counts = 4
normalized_gap_sq = 4/5
lifted_gap_decimal = 0.8944271909999159
exported rows.P7_bracketing_boundary.lifted_path_grouping_gap = 0.894427191
erased_left_sum = 5
erased_right_sum = 5
erased_gap_sq = 0
```

This matches `n5_values.exported_gap_matches_recomputed = true`, `lifted_gap_squared_num = 4`, `lifted_gap_squared_den = 5`, and `erased_gap_squared = 0.0` in both JAX and Julia results.

### 4. Solver Polarities And Julia Z3 Mirror

**Pass.** Both load-bearing Python-side solvers have the positive, erased, and boundary polarities, and Julia Z3 mirrors them.

Quoted erased source:

```python
erased.add(left_density_token == sum(raw["left_counts"]))
erased.add(right_density_token == sum(raw["right_counts"]))
erased.add(left_density_token == right_density_token)
```

Cite: `geo_bracketing_smt_lifted_v0_jax.py:232-235`. cvc5 mirrors this at `geo_bracketing_smt_lifted_v0_jax.py:281-289`; Julia Z3 mirrors it at `geo_bracketing_smt_lifted_v0_julia.jl:214-220`.

Quoted n=5 result values:

```text
n5 z3 positive = unsat
n5 cvc5 positive = unsat
n5 z3 erased = sat
n5 cvc5 erased = sat
n5 z3 unit boundary = unsat
n5 cvc5 unit boundary = unsat
n5 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

Envelope gate values are true for `n5_positive_z3_cvc5_agree_unsat`, `n5_erased_control_flips_sat`, `n5_unit_killed_nonzero_unsat`, `n5_julia_z3_mirror_positive_unsat`, `n5_julia_z3_mirror_erased_flip`, `n5_julia_z3_mirror_unit_boundary`, `n5_sympy_exact_crosscheck`, `n5_divergence_ok`, and `n5_read_only_imports_present`.

### 5. n=3/n=4 Exact Rows Byte-Stable Against HEAD

**Pass.** Current exact subtrees were compared against `git show HEAD:<path>` by sorted compact JSON serialization.

```text
n3 JAX: source_refs/raw_object/positive/negative/boundary/sympy_exact_crosscheck/crossover_proofs/values MATCH
n3 Julia: source_refs/raw_object/positive/negative/boundary/crossover_proofs/values MATCH
n3 envelope: positive/negative/boundary/raw_object/crossover_proofs/divergence MATCH

n4 JAX: n4_source_refs/n4_raw_object/n4_positive/n4_negative/n4_boundary/n4_sympy_exact_crosscheck/n4_crossover_proofs/n4_values MATCH
n4 Julia: n4_source_refs/n4_raw_object/n4_positive/n4_negative/n4_boundary/n4_crossover_proofs/n4_values MATCH
n4 envelope: n4_positive/n4_negative/n4_boundary/n4_raw_object/n4_crossover_proofs/n4_divergence MATCH
overall = true
```

### Re-Audit Conclusion

n=5 G5 closure EARNED for the narrow extension rows because the rows are hash-bound to committed n=5 exports, the solver encodings scale to the 32-slot n=5 object, independent recomputation matches the n=5 count vectors and erased value, z3/cvc5/Julia Z3 polarities are present, and n=3/n=4 exact rows stayed byte-stable; ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, not stage closure, not ladder scaling, not formal admission, not canonical proof, not PyTorch graph/autograd evidence, and not bridge/axis admission.

## Builder Extension Addendum - n=6 and n=7 Rows

Date: 2026-06-10

The audited n=3 verdict and focused n=4/n5 re-audit addenda above still stand. The rows below are **builder-extension rows pending re-audit**. Ceiling is unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; reject as stage closure, audited n=6 closure, audited n=7 closure, ladder scaling, formal admission, canonical proof, PyTorch graph/autograd evidence, bridge evidence, axis admission, or any n=8 result.

What changed:

- Reran the same raw-object bracketing proof on committed `stage_lifted_spinor_shell_n6_v0` and `stage_lifted_spinor_shell_n7_v0` exports, read-only and hash-bound.
- Kept existing n=3, n=4, and n=5 exact-class rows byte-stable against `HEAD` by canonical JSON subtree comparison.
- Added clearly named `n6_*` and `n7_*` rows in the JAX, Julia, and envelope results.
- Did not read or touch the `stage_lifted_spinor_shell_n8_v0` lane.

n=6 lineage imports:

- `system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_jax_results.json`: `881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571`
- `system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_julia_results.json`: `b90f0b5202a4105691580619739bd2ce016a1c0982bcb6b7f2f4275816bce92e`
- Imported support field: `rows.P2_support_object`.
- Imported boundary field: `rows.P7_bracketing_boundary`.
- Path convention cited from committed source field: `system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_jax.py:order_and_bracketing_rows.path_gap`; Julia mirror source field: `system_v6/sims/stage_lifted_spinor_shell_n6_v0/stage_lifted_spinor_shell_n6_v0_julia.jl:order_and_bracketing_rows.path_gap`.

n=6 recomputed rows:

```text
left path  = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
input_support_basis = [32, 16, 8, 4, 2, 1]
left_outputs  = [60, 28, 12, 4, 2, 1]
right_outputs = [48, 24, 12, 4, 2, 1]
left_counts  = [0,1,1,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0]
right_counts = [0,1,1,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
diff_sq_counts = 4
lifted_gap_squared = 2/3
lifted_gap_decimal = 0.816496580927726
exported P7 lifted_path_grouping_gap = 0.816496580928
erased_gap_squared = 0
```

n=6 solver polarity:

```text
n6 z3 positive = unsat
n6 cvc5 positive = unsat
n6 z3 erased = sat
n6 cvc5 erased = sat
n6 z3 unit boundary = unsat
n6 cvc5 unit boundary = unsat
n6 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

n=7 lineage imports:

- `system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_jax_results.json`: `1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc`
- `system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_julia_results.json`: `c40e85436b39426d4979f36cfb5f9cb2868d715a4754e9a0c1a2554b9a03d551`
- Imported support field: `rows.P2_support_object`.
- Imported boundary field: `rows.P7_bracketing_boundary`.
- Path convention cited from committed source field: `system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_jax.py:order_and_bracketing_rows.path_gap`; Julia mirror source field: `system_v6/sims/stage_lifted_spinor_shell_n7_v0/stage_lifted_spinor_shell_n7_v0_julia.jl:order_and_bracketing_rows.path_gap`.

n=7 recomputed rows:

```text
left path  = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
input_support_basis = [64, 32, 16, 8, 4, 2, 1]
left_outputs  = [120, 56, 24, 8, 4, 2, 1]
right_outputs = [96, 48, 24, 8, 4, 2, 1]
left_counts/right_counts are 128-slot vectors in the result JSON; they differ at rung-scaled support slots, not by relabeling n=3/n=4/n=5 rows.
diff_sq_counts = 4
lifted_gap_squared = 4/7
lifted_gap_decimal = 0.7559289460184545
exported P7 lifted_path_grouping_gap = 0.755928946018
erased_gap_squared = 0
```

n=7 solver polarity:

```text
n7 z3 positive = unsat
n7 cvc5 positive = unsat
n7 z3 erased = sat
n7 cvc5 erased = sat
n7 z3 unit boundary = unsat
n7 cvc5 unit boundary = unsat
n7 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

Fresh reruns and gates:

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py
=> ok:true

JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_julia.jl
=> ok:true

MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_envelope.py
=> ok:true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}
```

Capability receipts:

```text
verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_jax.py
=> z3 ok; cvc5 ok; sympy ok; violations=[]

verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_julia.jl
=> Z3 ok; violations=[]
```

Existing-row stability check:

```text
n3 exact subtrees: JAX source_refs/raw_object/positive/negative/boundary/sympy/crossover_proofs/values MATCH HEAD; Julia source_refs/raw_object/positive/negative/boundary/crossover_proofs/values MATCH HEAD; envelope positive/negative/boundary/raw_object/crossover_proofs/divergence MATCH HEAD.
n4 exact subtrees: JAX n4_source_refs/n4_raw_object/n4_positive/n4_negative/n4_boundary/n4_sympy/n4_crossover_proofs/n4_values MATCH HEAD; Julia n4_source_refs/n4_raw_object/n4_positive/n4_negative/n4_boundary/n4_crossover_proofs/n4_values MATCH HEAD; envelope n4_positive/n4_negative/n4_boundary/n4_raw_object/n4_crossover_proofs/n4_divergence MATCH HEAD.
n5 exact subtrees: JAX n5_source_refs/n5_raw_object/n5_positive/n5_negative/n5_boundary/n5_sympy/n5_crossover_proofs/n5_values MATCH HEAD; Julia n5_source_refs/n5_raw_object/n5_positive/n5_negative/n5_boundary/n5_crossover_proofs/n5_values MATCH HEAD; envelope n5_positive/n5_negative/n5_boundary/n5_raw_object/n5_crossover_proofs/n5_divergence MATCH HEAD.
```

Builder-extension conclusion: n=6 and n=7 extension rows are present, source-backed to committed n=6/n=7 exports, and the erased sides flip honestly (`sat`) while lifted equality remains `unsat`. These are pending re-audit rows only; the packet ceiling and all prior audited verdict boundaries remain unchanged.

## Focused Re-Audit Addendum - n=6 and n=7 Extension Rows

Date: 2026-06-10

Scope: read-only re-audit of the new `n6_*` and `n7_*` rows only, except appending this addendum. All prior verdicts above stand.

Quoted source anchors:

- `geo_bracketing_smt_lifted_v0_jax.py:33-36` binds the imported committed stage exports: `N6_JAX_RESULT`, `N6_JULIA_RESULT`, `N7_JAX_RESULT`, and `N7_JULIA_RESULT`.
- `geo_bracketing_smt_lifted_v0_jax.py:88-107` defines the n6/n7 source specs with `left_path: ["e01", "e12", "e23"]`, `right_path: ["e23", "e12", "e01"]`, `support_field: rows.P2_support_object`, and `boundary_field: rows.P7_bracketing_boundary`.
- `geo_bracketing_smt_lifted_v0_jax.py:179-191` computes `dim = 2**n_sites`, CNOT path outputs, count vectors, `diff_sq_counts`, and `normalized_gap_sq` from the imported support object.
- `geo_bracketing_smt_lifted_v0_jax.py:242-279` binds every count slot into z3, checks lifted equality as `unsat`, erased density-token equality as `sat`, and unit boundary as `unsat`; `geo_bracketing_smt_lifted_v0_jax.py:290-330` mirrors the same raw bindings in cvc5.
- `geo_bracketing_smt_lifted_v0_julia.jl:227-260` mirrors the same lifted/erased/boundary checks in Julia Z3; `geo_bracketing_smt_lifted_v0_julia.jl:319-329` stores n6/n7 positive, erased, boundary, and crossover rows.
- Committed stage source quotes: n6 `stage_lifted_spinor_shell_n6_v0_jax.py:770` computes `path_gap = jnp.linalg.norm(u23 @ u12 @ u01 @ w - u01 @ u12 @ u23 @ w)` and `:777` exports `lifted_path_grouping_gap`; n7 mirrors this at `stage_lifted_spinor_shell_n7_v0_jax.py:773` and `:780`.

Recomputed hash binding against committed stage exports:

```text
git show HEAD:system_v6/sims/stage_lifted_spinor_shell_n6_v0/results/stage_lifted_spinor_shell_n6_v0_jax_results.json | sha256
=> 881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571
current n6 row_ref => 881e1b9b1255cd408e08094aa679790417706937e81a619fe1b283dc17d54571

git show HEAD:system_v6/sims/stage_lifted_spinor_shell_n7_v0/results/stage_lifted_spinor_shell_n7_v0_jax_results.json | sha256
=> 1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc
current n7 row_ref => 1a24dbf38f4f7cc366de261767bd74f43a8ef7fdd59acc5897f037e660b988fc
```

Encoding growth check:

```text
n3 dim=8   inputs=[4,2,1]              left_nz=[1,3,7]             right_nz=[1,3,6]
n4 dim=16  inputs=[8,4,2,1]            left_nz=[1,3,7,15]          right_nz=[1,3,6,12]
n5 dim=32  inputs=[16,8,4,2,1]         left_nz=[1,2,6,14,30]       right_nz=[1,2,6,12,24]
n6 dim=64  inputs=[32,16,8,4,2,1]      left_nz=[1,2,4,12,28,60]    right_nz=[1,2,4,12,24,48]
n7 dim=128 inputs=[64,32,16,8,4,2,1]   left_nz=[1,2,4,8,24,56,120] right_nz=[1,2,4,8,24,48,96]
```

This is structural growth, not relabeling: the current n6/n7 rows have 64-slot and 128-slot count vectors, new one-excitation basis supports, and rung-scaled differing slots.

Independent hand recomputation from committed stage exports:

```text
n6 left path  e01 -> e12 -> e23
n6 right path e23 -> e12 -> e01
n6 inputs=[32,16,8,4,2,1]
n6 left_outputs=[60,28,12,4,2,1]
n6 right_outputs=[48,24,12,4,2,1]
n6 diff_sq_counts=4
n6 lifted_gap_squared=2/3
n6 exported_gap=0.816496580928
n6 erased value=sum(left_counts)-sum(right_counts)=0

n7 left path  e01 -> e12 -> e23
n7 right path e23 -> e12 -> e01
n7 inputs=[64,32,16,8,4,2,1]
n7 left_outputs=[120,56,24,8,4,2,1]
n7 right_outputs=[96,48,24,8,4,2,1]
n7 diff_sq_counts=4
n7 lifted_gap_squared=4/7
n7 exported_gap=0.755928946018
n7 erased value=sum(left_counts)-sum(right_counts)=0
```

Solver polarity check:

```text
n6 JAX z3/cvc5: positive=unsat/unsat erased=sat/sat boundary=unsat/unsat
n6 Julia Z3 mirror: positive/erased/boundary=unsat/sat/unsat
n7 JAX z3/cvc5: positive=unsat/unsat erased=sat/sat boundary=unsat/unsat
n7 Julia Z3 mirror: positive/erased/boundary=unsat/sat/unsat
```

Exact-row stability against `HEAD`:

```text
JAX n3/n4/n5 exact source_refs/raw_object/positive/negative/boundary/sympy/crossover/values subtrees: MATCH HEAD
Julia n3/n4/n5 exact source_refs/raw_object/positive/negative/boundary/crossover/values subtrees: MATCH HEAD
Envelope n3/n4/n5 exact positive/negative/boundary/raw_object/crossover/divergence subtrees: MATCH HEAD
```

Fresh read-only checks:

```text
validate_three_engine_sim_result.py --require-source-backed geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}

verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_jax.py
=> z3 ok; cvc5 ok; sympy ok; violations=[]

verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_julia.jl
=> Z3 ok; violations=[]
```

n6/n7 G5 closure EARNED for the narrow raw-object bracketing SMT extension rows; full G5 status is now EARNED for n3, n4, n5, n6, and n7 only under this packet's row scope; ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, not stage closure, not ladder scaling beyond checked rows, not formal admission, not canonical proof, not PyTorch graph/autograd evidence, not bridge/axis admission, and not any n8 claim.

## Builder Extension Addendum - n=8 Rows

Date: 2026-06-10

The audited n=3 verdict and focused n=4/n5/n6/n7 addenda above still stand. The rows below are **builder-extension rows pending fresh re-audit**. Ceiling is unchanged: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`; reject as stage closure, ladder scaling beyond checked rows, formal admission, canonical proof, PyTorch graph/autograd evidence, bridge evidence, or axis admission.

What changed:

- Reran the same raw-object bracketing proof on committed `stage_lifted_spinor_shell_n8_v0` exports, read-only and hash-bound.
- Kept existing n=3, n=4, n=5, n=6, and n=7 row-bearing exact subtrees byte-stable against `HEAD` by canonical JSON subtree comparison.
- Added clearly named `n8_*` rows in the JAX, Julia, and envelope results.
- Did not stage or commit anything.

n=8 lineage imports:

- `system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_jax_results.json`: `f7ded95c7fb77973cfb93d8ee329d43e4ec70ffa21c0966b03f3b4cec2fe4c1d`
- `system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_julia_results.json`: `21eb99a69a80f581f0f2587f5541591e6e0fda7cec99a317ac04f5a2e666680b`
- Imported support field: `rows.P2_support_object`.
- Imported boundary field: `rows.P7_bracketing_boundary`.
- Path convention cited from committed source fields: `stage_lifted_spinor_shell_n8_v0_jax.py:order_and_bracketing_rows.path_gap` and `stage_lifted_spinor_shell_n8_v0_julia.jl:order_and_bracketing_rows.path_gap`.
- Last commit touching the n=8 stage exports: `08037882ee4f580c239a2080e0bcb36212b19208` (`2026-06-10 17:10:10 -0700`).

n=8 recomputed rows:

```text
left path  = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
dim = 256
input_support_basis = [128,64,32,16,8,4,2,1]
left_outputs  = [240,112,48,16,8,4,2,1]
right_outputs = [192,96,48,16,8,4,2,1]
left_nz_slots  = [1,2,4,8,16,48,112,240]
right_nz_slots = [1,2,4,8,16,48,96,192]
diff_sq_counts = 4
lifted_gap_squared = 1/2
lifted_gap_decimal = 0.7071067811865476
exported P7 lifted_path_grouping_gap = 0.707106781187
erased_gap_squared = 0
```

The n=8 encoding scales structurally from n=7: `dim=256` versus `dim=128`, with a new eight-element one-excitation support and 256-slot count vectors. This is not a relabeled n=7 row.

Solver polarity:

```text
n8 z3 positive = unsat
n8 cvc5 positive = unsat
n8 z3 erased = sat
n8 cvc5 erased = sat
n8 z3 unit boundary = unsat
n8 cvc5 unit boundary = unsat
n8 Julia Z3 positive/erased/boundary = unsat/sat/unsat
```

Fresh reruns and gates:

```text
MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_jax.py
=> ok:true

julia --project=system_v5/julia_carrier system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_julia.jl
=> ok:true

MPLCONFIGDIR=/tmp/codex-mpl NUMBA_CACHE_DIR=/tmp/codex-numba /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/geo_bracketing_smt_lifted_v0/geo_bracketing_smt_lifted_v0_envelope.py
=> ok:true

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}

/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/geo_bracketing_smt_lifted_v0/results/geo_bracketing_smt_lifted_v0_envelope_results.json
=> {"ok": true}
```

Capability receipts:

```text
verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_jax.py
=> z3 ok; cvc5 ok; sympy ok; violations=[]

verify_load_bearing_has_capability_probe.py --sim geo_bracketing_smt_lifted_v0_julia.jl
=> Z3 ok; violations=[]
```

Existing-row stability check:

```text
JAX n3/n4/n5/n6/n7 row-bearing exact subtrees: MATCH HEAD
Julia n3/n4/n5/n6/n7 row-bearing exact subtrees: MATCH HEAD
Envelope n3/n4/n5/n6/n7 row-bearing exact subtrees: MATCH HEAD
```

Builder-extension conclusion: n=8 extension rows are present, source-backed to committed n=8 exports, structurally scaled to `dim=256`, and the erased side flips honestly (`sat`) while lifted equality remains `unsat`. These are pending re-audit rows only; the packet ceiling and all prior audited verdict boundaries remain unchanged.

## Focused Re-Audit Addendum - n=8 Rows

Date: 2026-06-11.
Scope: read-only re-audit of the new n8 rows only. All prior verdicts and addenda above stand.

Hash/source binding checked:

- Recomputed `HEAD` sha256 for `system_v6/sims/stage_lifted_spinor_shell_n8_v0/results/stage_lifted_spinor_shell_n8_v0_jax_results.json`: `f7ded95c7fb77973cfb93d8ee329d43e4ec70ffa21c0966b03f3b4cec2fe4c1d`, matching `n8_raw_object.source_results.n8_jax_sha256`.
- Stored n8 Julia export hash: `21eb99a69a80f581f0f2587f5541591e6e0fda7cec99a317ac04f5a2e666680b`.
- `validate_three_engine_sim_result.py --strict-source-backed ...geo_bracketing_smt_lifted_v0_envelope_results.json` returned `{"ok": true}` with exit 0.

Encoding growth checked:

```text
n7 dim=128
n8 dim=256
n8 input_support_basis=[128,64,32,16,8,4,2,1]
```

The n8 row uses an eight-element one-excitation basis and 256-slot count vectors. That is structural growth from the n7 encoding, not a relabeled n7 row.

Hand recomputation from the committed n8 support object:

```text
left path  = e01 -> e12 -> e23
right path = e23 -> e12 -> e01
left_outputs  = [240,112,48,16,8,4,2,1]
right_outputs = [192,96,48,16,8,4,2,1]
left_nz_slots  = [1,2,4,8,16,48,112,240]
right_nz_slots = [1,2,4,8,16,48,96,192]
diff_sq_counts = 4
lifted_gap_squared = 1/2
erased equality value = sat
```

Solver polarity checked:

```text
n8 JAX z3/cvc5 lifted positive = unsat/unsat
n8 JAX z3/cvc5 erased = sat/sat
n8 JAX z3/cvc5 unit boundary = unsat/unsat
n8 Julia Z3 lifted/erased/boundary = unsat/sat/unsat
```

Byte-stability checked:

```text
JAX n3/n4/n5/n6/n7 exact row-bearing subtrees: MATCH_HEAD
Julia n3/n4/n5/n6/n7 exact row-bearing subtrees: MATCH_HEAD
Envelope n3/n4/n5/n6/n7 exact row-bearing subtrees: MATCH_HEAD
```

Conclusion: n8 extension rows EARNED; full G5 status across n3..n8 is EARNED only for this packet's raw-object bracketing SMT row scope; ceiling remains `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`, not stage closure, not formal admission, not canonical proof, not PyTorch graph/autograd evidence, not bridge/axis admission, and not any unverified rung consequence.
