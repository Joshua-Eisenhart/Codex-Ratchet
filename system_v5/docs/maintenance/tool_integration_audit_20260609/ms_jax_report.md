# JAX TOOL-INTEGRATION audit: foundation_spinor_network_full_stack_layer_jax

Scope:
- Source: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_jax.py`
- Result: `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/ops/formal_scouts/results/foundation_spinor_network_full_stack_layer_jax_results.json`
- Repo writes: none. This report is the only written artifact.

Checks run:
- Canonical runtime doctor: `ok=True install_state=stable_observed`; no missing expected modules or active installers.
- API smoke check in `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3`: JAX x64 true; `dynamiqs` QArray exposes `.to_jax`; `diffrax.Tsit5`, `quimb.MPS_computational_state`, `cotengra.HyperOptimizer`, `e3nn_jax.Irreps`, `z3`, and `cvc5` callable.
- Static sim contract lint on the source: `checked=1`, `violation_total=0`.
- Three-engine envelope validator intentionally not applicable to this single-leg result: it fails on `schema_version must be three_engine_sim_result_v1`, not on JAX tool use.
- Provenance note: the audited source path is currently untracked by git (`?? system_v5/ops/formal_scouts/foundation_spinor_network_full_stack_layer_jax.py`).

Bottom line:
- The JAX leg is not a fake import-only script. Every named tool is called through a real package API.
- Actual load-bearing status is mixed. `jax/vmap`, `diffrax`, `z3`, and `cvc5` are genuinely load-bearing for the current pass/fail path. `dynamiqs`, `quimb+cotengra`, and `e3nn_jax` are real calls but too weak or disconnected to deserve unqualified `load_bearing` under the current `all_pass` gate.
- The safest ceiling remains exactly the result ceiling: `scratch_diagnostic finite same-carrier spinor-network JAX integration leg only; no canon/admission/bridge/physics/Axis0/manifold claim`.

## Per-tool verdicts

### dynamiqs

Verdict: real API call, not load-bearing under the current gate.

Evidence:
- Source calls `dq.asqarray`, `dq.mesolve`, and `res.states.to_jax()[-1]` in `qit_readout()`.
- The specific footgun from the JAX skill is handled for states: `.to_jax()` is called before the result state is passed to `jnp` entropy code.
- `res.expects` is already a JAX `ArrayImpl` in the current runtime, so the direct `jnp.real(res.expects[0, -1])` path is API-correct.

Why it is not load-bearing:
- `dynamiqs_final_entropy` and `dynamiqs_z0_expectation_final` are emitted as readouts, but neither participates in `quotient["drop_probe_strictly_coarsens"]`, `controls`, or `all_pass`.
- The quotient predicate uses `qit["coherent_information"] != qit["erased_coherent_information"]`, and those values are computed from direct JAX density matrices, not from `dynamiqs`.
- Removing `dynamiqs` while retaining the direct density/coherent-information code would leave the present `all_pass` logic intact.

Footguns:
- The Lindblad operator is a low-information dephasing fixture; the reported final expectation is `0.0`, so the boundary readout is not discriminating.
- No trace/PSD/Hermitian gate is applied specifically to `dynamiqs` final state.
- `TOOL_INTEGRATION_DEPTH["dynamiqs"] = "load_bearing"` conflicts with `aligned_packages_load_bearing`, which omits `dynamiqs`.

Recommendation:
- Demote `dynamiqs` to `supportive` unless a future patch makes `dynamiqs_final_entropy`, final trace/PSD, or a structured-vs-erased `dynamiqs` control part of `all_pass`.

### diffrax

Verdict: genuine load-bearing, with a basin-boundary footgun.

Evidence:
- `diffrax_basin_flow()` calls `diffrax.ODETerm`, `diffrax.Tsit5`, and `diffrax.diffeqsolve` inside `jax.vmap` over the 16 finite seeds.
- `dynamics_readout()` separately uses `diffrax.diffeqsolve` for a Lindblad-style master equation, and `all_pass` requires `abs(dynamics["final_trace"] - 1.0) <= TOL`.
- The result records `dynamics.final_trace = 1.0` and `diffrax_basin_flow.attractor_count = 2`.

Why it is load-bearing:
- At least the `dynamics.final_trace` path is directly in `all_pass`.
- The basin-flow readout is a real ODE integration path, not a static label.

Footguns:
- `diffrax_basin_flow.terminal_projection_min_abs` is `0.0`, which means at least one terminal seed lies exactly on the sign projection boundary. That weakens the "two terminal signs" statement.
- The basin-flow path is reported in `tool_calls`, but its own output is not directly in `all_pass`; only the separate `dynamics.final_trace` check is.
- No solution stats, solver result code, or per-seed boundary list is recorded.

Recommendation:
- Keep `diffrax` load-bearing, but split the role: `diffrax_master_trace_gate` is load-bearing now; `diffrax_basin_flow` is diagnostic until `terminal_projection_min_abs > threshold` or boundary seeds are explicitly classified.

### quimb+cotengra

Verdict: real API call, currently decorative/thin rather than load-bearing.

Evidence:
- Source calls `qtn.MPS_computational_state("0111")`, creates `ctg.HyperOptimizer(max_repeats=1)`, contracts `mps.H & mps`, and records norm/tensor count.
- Result records `contraction_norm = 1.0` and `tensor_count = 4`.

Why it is not load-bearing:
- The MPS bitstring is hard-coded, not derived in code from `TARGET` or from the quotient object.
- Contracting the norm of a computational-basis MPS is expected to produce `1.0`; this is a weak fixture, not a falsifying tensor-network claim.
- The negative control is prose only: `"erased signs would change bitstring fixture"`. There is no executed erased/wrong-sign tensor contraction.
- No tensor readout participates in `all_pass`.

Footguns:
- `cotengra` is technically invoked, but with a trivial four-tensor norm and `max_repeats=1`; that is optimizer presence, not meaningful contraction-order pressure.
- The tool_call says "four-node bitstring from spinor signs", but the source currently hard-codes `"0111"`.

Recommendation:
- Demote `quimb` and `cotengra` to `supportive` unless the script derives the tensor network from the carrier/sign object, runs positive/negative/boundary contractions, records contraction path/cost metadata, and makes a tensor-network predicate part of `all_pass`.

### e3nn_jax

Verdict: real API call, currently decorative/thin rather than load-bearing.

Evidence:
- Source calls `e3nn.matrix_z`, `e3nn.Irreps("1x1o")`, and `irreps.D_from_matrix(rotation)`.
- Result records `so3_equivariance_residual = 4.1540741810552243e-16`.

Why it is not load-bearing:
- The vector checked is hard-coded as `[1.0, -1.0, 0.5]`, not the actual `hopf(spinor)` readout.
- The residual is not used in `all_pass`.
- The negative control is prose only: `"non-rotated control would not test equivariance"`.

Footguns:
- `Irreps("1x1o")` for a vector representation is API-correct, but this only proves the representation matrix matches the ordinary rotation matrix on a test vector.
- The tool_call claims the input is "Hopf/Bloch vector image"; the source does not use `geometry["hopf_s2"]` or `hopf(spinor)` in the e3nn check.

Recommendation:
- Demote `e3nn_jax` to `supportive` unless the equivariance check is wired to the actual Hopf/Bloch readout, includes a wrong-irrep or non-equivariant control, and gates `all_pass` on the residual/control flip.

### jax / jax.vmap

Verdict: genuine load-bearing.

Evidence:
- `config.update("jax_enable_x64", True)` runs before `jax.numpy` import and before module-level `TARGET`.
- `jax.vmap` is used for graph message passing and finite basin updates. `jnp.einsum`, x64 arrays, vectorized finite states, and JAX device reads are in the claim path.
- `network["cycle_rank"]`, `network["noncommutative_message_gap"]`, and finite basin counts feed the quotient predicate and controls used by `all_pass`.

Why it is load-bearing:
- Removing JAX/vmap/einsum would break the graph message and basin gates used in `quotient["drop_probe_strictly_coarsens"]` and controls.
- JAX is more than array support here; it is the vectorized finite-workhorse path.

Footguns:
- The table is generated locally by JAX Cayley-Dickson doubling. It is not loaded from a Julia canonical artifact with `table_version`, `bracket_convention`, and `proof_tag`, so it cannot support a canon-table consumer claim.
- `py_float()` applies `jnp.real`, which can silently drop imaginary parts if a complex-valued check accidentally enters a real metric.
- The finite update maps `q == 0` to `TARGET`, producing a tie rule that should be recorded explicitly because it affects basin counts.

Recommendation:
- Keep `jax` load-bearing and `jax.numpy` supportive. Add result fields recording `jax_enable_x64`, key dtypes, tie-rule policy, and whether the algebra table is local diagnostic vs imported canonical artifact.

### z3

Verdict: genuine load-bearing, API shape correct.

Evidence:
- The source constructs Z3 variables for basis vectors, constrains selected coordinates in solver, expands products coefficient-by-coefficient into Z3 expressions, and asks equality/escape queries with `solver.check()`.
- The result records the expected split: octonion assoc-zero `unsat`, quaternion assoc-zero control `sat`, real basin escape `unsat`, erased basin escape `sat`.
- The combined `z3_cvc5_derive_flip` control participates in `all_pass`.

Why it is load-bearing:
- The solver verdicts are directly required by a control gate.
- This is derive-in-solver enough for a fixed finite witness: it does not merely feed a precomputed scalar norm into Z3.

Footguns:
- Coefficients are produced by JAX floats and cast with `int(jax.device_get(...))`; there is no guard that every coefficient is exactly integral within tolerance before solver handoff.
- No model is recorded for SAT controls and no query fingerprint/sexpr is recorded.
- The solver proves fixed-witness equality/escape status, not general algebraic associativity or basin structure.

Recommendation:
- Keep `z3` load-bearing. Add an integer-coefficient guard, per-query fingerprint, SAT model snippets for controls, and explicit wording that the proof scope is fixed finite witness/query.

### cvc5

Verdict: genuine load-bearing, API shape correct.

Evidence:
- Source constructs a cvc5 `Solver`, sets `QF_LIA`, creates integer constants, expands product expressions in cvc5 terms, and calls `checkSat()`.
- The result agrees with Z3 on all four SMT checks.
- The combined `z3_cvc5_derive_flip` control participates in `all_pass`.

Why it is load-bearing:
- It independently certifies the same fixed finite witness/control split as Z3.
- The all-pass gate requires cvc5 and Z3 to agree on the expected SAT/UNSAT pattern.

Footguns:
- Same coefficient-cast issue as Z3: JAX float table entries are converted to ints without an exactness guard.
- `cvc5_and()` and `cvc5_or()` assume non-empty term lists. The current calls are non-empty, but the helper is unsafe as a general skill pattern.
- No SAT model, query fingerprint, or proof/unsat-core metadata is recorded.

Recommendation:
- Keep `cvc5` load-bearing. Add exact coefficient validation, non-empty helper guards or explicit true/false identities, query fingerprints, and SAT control model capture.

## Result consistency issues

- `TOOL_INTEGRATION_DEPTH` marks `dynamiqs`, `quimb`, `cotengra`, and `e3nn_jax` as `load_bearing`, but current `all_pass` does not depend on their outputs.
- `aligned_packages_load_bearing` omits `dynamiqs` while `TOOL_INTEGRATION_DEPTH` marks it load-bearing. This is internally inconsistent.
- `tool_calls` are useful, but they do not record whether each tool_call changes `all_pass`, controls, or quotient predicates. That allows real-but-decorative calls to look load-bearing.

Recommended source/result patch direction:
- Add per-tool fields: `role_verdict`, `all_pass_dependency`, `control_dependency`, `quotient_dependency`, and `executed_negative_control`.
- Require every `TOOL_INTEGRATION_DEPTH == "load_bearing"` tool to have at least one true dependency among `all_pass_dependency`, `control_dependency`, or `quotient_dependency`.
- Make `aligned_packages_load_bearing` agree with the subset of load-bearing rich packages, or add a `not_aligned_but_load_bearing_reason` field for packages outside the validator aligned set.

## Concrete jax-sim SKILL patch recommendations

Patch target: `/Users/joshuaeisenhart/.codex-second/skills/jax-sim/SKILL.md`

1. Add a load-bearing decision rule after Step 3:

```md
Load-bearing means the package output changes, constrains, certifies, or falsifies the bounded claim through `all_pass`, a named control, or a quotient/admission predicate. A real API call that only emits an auxiliary readout is supportive, not load-bearing. A prose-only negative control does not make a tool load-bearing.
```

2. Add a per-tool receipt requirement to Step 4:

```json
"tool_calls": [
  {
    "tool": "diffrax",
    "api_surface": "diffrax.diffeqsolve",
    "role_verdict": "load_bearing",
    "all_pass_dependency": true,
    "control_dependency": "final_trace_gate",
    "quotient_dependency": null,
    "executed_negative_control": true,
    "demotion_condition": "solver output removed without changing all_pass"
  }
]
```

3. Add a `dynamiqs` guard under API footguns:

```md
`dynamiqs` states are `QArray`/`DenseQArray`; call `.to_jax()` before `jnp` operations. Expectations may already be JAX arrays in the current runtime, but use a small helper that calls `.to_jax()` when available and otherwise returns the value unchanged. A `dynamiqs` call is load-bearing only when its state, expectation, entropy, trace, PSD, or control flip participates in `all_pass` or a named control.
```

4. Add a `diffrax` boundary rule:

```md
For basin-flow claims, record solver status/stats when available, per-seed terminal projections, and a nonzero boundary margin. If `terminal_projection_min_abs == 0`, classify the basin-flow readout as boundary-diagnostic unless the tie rule is explicitly part of the claim and separately checked.
```

5. Add a tensor-network demotion rule:

```md
`quimb`/`cotengra` are not load-bearing for a hard-coded normalized MPS norm alone. Load-bearing tensor-network use must derive tensors from the claim object, execute positive/negative/boundary contractions, record contraction path/cost metadata, and feed a predicate into `all_pass` or a named control.
```

6. Add an `e3nn_jax` demotion rule:

```md
`e3nn_jax` is not load-bearing for a hard-coded vector representation smoke test. It becomes load-bearing only when the representation acts on the actual geometric readout, has a wrong-irrep/non-equivariant control, and the residual/control split gates the claim.
```

7. Add an SMT derive-in-solver checklist:

```md
For Z3/cvc5 claims, validate exact integer/rational coefficients before solver handoff, build the target expression inside the solver rather than passing only a precomputed scalar, record query fingerprints, record SAT models for controls when practical, and state the finite witness/query scope. Z3 and cvc5 should be independently constructed, not one solver's result copied into the other.
```

8. Add an x64 receipt rule:

```md
Record `jax.config.jax_enable_x64` and key result dtypes in the JSON receipt. If x64 is false for numeric comparison lanes, classify as diagnostic only.
```

9. Add result consistency validation:

```md
Every tool marked `TOOL_INTEGRATION_DEPTH[tool] == "load_bearing"` must either appear in `aligned_packages_load_bearing` or carry an explicit `not_aligned_but_load_bearing_reason`. `aligned_packages_load_bearing` must not include tools whose outputs do not affect `all_pass`, controls, or quotient/admission predicates.
```

Net classification after audit:
- `jax/vmap`: load-bearing.
- `diffrax`: load-bearing, with basin boundary caveat.
- `z3`: load-bearing.
- `cvc5`: load-bearing.
- `dynamiqs`: supportive until wired into a gate.
- `quimb+cotengra`: supportive/decorative until tensor output is derived, controlled, and gated.
- `e3nn_jax`: supportive/decorative until actual Hopf/Bloch equivariance is controlled and gated.
