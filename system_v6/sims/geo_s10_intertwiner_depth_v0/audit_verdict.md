# Fresh Audit Verdict: geo_s10_intertwiner_depth_v0

Auditor: codex2 cross-backend audit.
Write boundary observed: this file only. I did not git add or commit anything.

Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`. I applied the calibrated rule set: route genuineness, can-fail controls, capability receipts, erasure honesty, scratch ceilings, and fresh-context audit stay binding; two-CAS end-to-end proof is preferred, not mandatory, when one genuine derivation has independent solver or cross-engine binding.

Parent fences audited:

- `geo_s10_g2_family_v0` at `77a4f5d19`: prior caveat `G3-triality-scope` said the parent earned D4 diagram/character-node triality only, not explicit intertwiners.
- `ratchet_g2_family_v0` at `b5649217c`: prior caveat left the null row nonreductive/deferred and explicitly did not earn a full null-stabilizer Levi decomposition.

## Verdict

VERDICT: `GENUINE-WITH-CAVEATS`.

The packet earns the explicit-intertwiner upgrade for the S10/G2 triality fence. It constructs the three eight-dimensional D4 rows (`8v`, `8c`, `8s`) and exact 8x8 maps for the S3 outer action; my recomputation of `A*rho(x) - rho'(x)*A` on two generators per map returned zero residuals for all six maps, and the order-3 direct-sum action cubed to scalar `1`.

The packet also earns a computed split-null stabilizer decomposition at the nilradical plus Levi-quotient level: stabilizer dimension `8`, nilradical dimension `5`, quotient dimension `3`, quotient derived dimension `3`, center dimension `0`, indefinite nonzero Killing form, and exact bookkeeping `8 = 5 + 3`. It does not earn the stronger phrase "explicit closed Levi factor inside the stabilizer"; see caveat `G1`.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`; `stage_movement_allowed=false`. This closes the two named parent fences only at the local citation level below; it does not promote either parent packet, classify all triality intertwiners, classify all null-line parabolics, or admit bridge/axis/physics claims.

## Caveats

`G1-Levi-quotient-not-explicit-factor`: The packet claims and validates `Levi_quotient`, not an embedded closed Levi subalgebra. I recomputed the selected complement indices `[0, 3, 4]`; their brackets had `4` failures for exact closure inside the complement, but `0` failures after adjoining/modding out the 5D radical. Parent citations may say "computed nilradical plus sl2_R-type Levi quotient"; they may not say "explicit closed Levi factor" unless a later packet supplies and checks that embedding.

`G2-Nemo-project-deps`: The Nemo sidecar receipt records `--project=system_v6/optional/nemo_hecke` and the GF(2) math row reruns under that project. However `Project.toml` lists `Nemo` and `Hecke` only, while the sidecar source also imports `JSON3`; a strict load-path run hiding the global environment failed at `using JSON3`. This is a reproducibility/package-declaration caveat, not a math-row failure, because the live read-only Nemo/Hecke recompute under the project returned the claimed S3 row.

`G3-engine-label`: The envelope uses lanes `["julia", "jax"]`, but the `jax` lane is explicitly `python_sympy_exact`, not a JAX backend computation. This is honest in `engine_contract.lane_aliases`, so it is a naming ceiling rather than a defect.

`G4-route-topology`: I did not spawn Codex-native subagents because the current tool policy permits subagent spawning only on explicit user request for delegation. This audit is therefore a single-controller fresh audit with local recomputation, not a full Max Assembly worker topology receipt.

## Q1 Intertwiners

Source quotes:

- `geo_s10_intertwiner_depth_v0.py:236-254` constructs the Chevalley `e`, `f`, and `h` matrices for each 8D representation from the D4 weights.
- `geo_s10_intertwiner_depth_v0.py:294-303` constructs each outer-action matrix as an explicit 8x8 permutation matrix by Dynkin-label transport.
- `geo_s10_intertwiner_depth_v0.py:314-327` checks the actual intertwiner property by computing `matrix * src_matrix - dst_matrix * matrix` for each generator.
- `geo_s10_intertwiner_depth_v0.py:403-405` states the honest fence: "one exact Chevalley-basis realization" and "not a classification of all possible intertwiners".

Independent recomputation:

```text
cycle 8v->8c: e1 residual rank 0, f2 residual rank 0, rank(A)=8, det=1
cycle 8c->8s: e1 residual rank 0, f2 residual rank 0, rank(A)=8, det=-1
cycle 8s->8v: e1 residual rank 0, f2 residual rank 0, rank(A)=8, det=-1
transposition 8v->8v: e1 residual rank 0, f2 residual rank 0, rank(A)=8, det=-1
transposition 8c->8s: e1 residual rank 0, f2 residual rank 0, rank(A)=8, det=1
transposition 8s->8c: e1 residual rank 0, f2 residual rank 0, rank(A)=8, det=1
order-3 direct-sum matrix cubed: scalar 1, residual rank 0, nonzero residual entries 0
```

Adjudication: Q1 passes. The parent `G3-triality-scope` fence is closed from diagram-level to explicit Chevalley-basis intertwiner-level for this one realization.

## Q2 Null Levi

Source quotes:

- `geo_s10_intertwiner_depth_v0.py:478-492` builds the derivation linear system from the multiplication table.
- `geo_s10_intertwiner_depth_v0.py:541-562` computes the null-stabilizer as the nullspace of the action constraint matrix.
- `geo_s10_intertwiner_depth_v0.py:725-752` computes structure constants, radical/nilradical diagnostics, and the `Levi_quotient`.
- `geo_s10_intertwiner_depth_v0.py:802-841` builds the compact and split controls, null vector, dimension bookkeeping, and sign-flip closure control.

Independent recomputation:

```text
split derivation nullity: 14
split null vector norm: 0
null-stabilizer constraint rank: 6
null-stabilizer dimension: 8
stabilizer closure under commutator: true
radical dimension: 5
nilradical dimension: 5
nilradical lower central dimensions: [5, 3, 2, 0]
nilradical derived-series dimensions: [5, 3, 0]
Levi quotient dimension: 3
Levi quotient derived dimension: 3
Levi quotient center dimension: 0
Levi quotient Killing rank/signature: rank 3, positive 2, negative 1, zero 0
bookkeeping: 8 = 5 + 3, identity true
selected complement exact closure failures: 4
selected complement closure modulo radical failures: 0
```

Adjudication: Q2 passes for nilradical plus Levi-quotient decomposition and fails for any stronger embedded-factor wording. The ratchet parent fence moves from "null deferred" to "null stabilizer decomposed as computed nilradical plus sl2_R-type Levi quotient", not to "explicit Levi factor embedded and closed".

## Q3 Controls

Source quotes:

- `geo_s10_intertwiner_depth_v0.py:400-425` constructs the wrong-identity intertwiner control.
- `geo_s10_intertwiner_depth_v0.py:755-783` mutates one stabilizer-basis entry and checks closure under commutators.
- `geo_s10_intertwiner_depth_v0.py:834-839` records the compact positive stabilizer control.

Recomputed controls:

```text
wrong identity 8v->8c under 3-cycle: residual entries 50, max abs residual 2, passes false, control fired true
sign-flipped null-stabilizer basis: bad bracket count 18, closure false, control fired true
compact unit stabilizer: stabilizer dim 8, radical dim 0, nilradical dim 0, Killing rank 8, nilradical_zero true
```

Adjudication: Q3 passes. Both designed-fail controls fire, and the compact positive control prevents copying the split nilradical story onto compact `su(3)`.

## Q4 Shape And Validator

Source quotes:

- `geo_s10_intertwiner_depth_v0.py:1068-1100` builds the shape-only `{subtree, hash}` rows for the Python exact algebra, Julia/Nemo S3 row, and divergence values.
- `geo_s10_intertwiner_depth_v0.py:1133-1145` declares the honest mode, lane aliases, PyTorch omission, runner boundary, and Julia project.
- `validate_geo_s10_intertwiner_depth_v0.py:50-58` validates schema, mode, scratch ceiling, all-pass, and that the builder did not emit an audit verdict.
- `validate_geo_s10_intertwiner_depth_v0.py:112-147` validates the null decomposition and z3/cvc5 erased-flip rows.

Read-only validator run: I imported the validator, redirected `VALIDATOR_RESULT` to `/tmp/geo_s10_intertwiner_depth_v0_validator_results.audit_tmp.json`, and called `main(...)` before creating this file. It returned:

```json
{"errors":[],"mode":"SYMBOLIC_LIGHT_LOCAL_INTERTWINER_DEPTH","ok":true,"result_json":"system_v6/sims/geo_s10_intertwiner_depth_v0/results/geo_s10_intertwiner_depth_v0_envelope_results.json","validator":"system_v6/sims/geo_s10_intertwiner_depth_v0/validate_geo_s10_intertwiner_depth_v0.py"}
```

Fresh no-write rebuild matched the stored shape hashes:

```text
jax subtree math_payload.triality_intertwiners + math_payload.split_null_Levi: c801873b8567da4dc2db9a68cfcd4b853c7223a6437414befcc316b0f1ebac7c
julia subtree nemo_hecke.outer_s3_row: ec1fb12eb3cb1b93fe7d25e022af6007cff14ed334f77aa657af9707e253db17
divergence subtree divergence.engine_values: 7bb405bd0fba4327041ffe6d96241f28ead3181b42d58b83f14523564b2798d9
stored all_pass: true
rebuilt all_pass: true
```

Nemo sidecar:

- Existing receipt records active project `/Users/joshuaeisenhart/Codex-Ratchet/system_v6/optional/nemo_hecke/Project.toml`, Julia `1.12.6`, `gl2_2_order=6`, `cycle_order=3`, `transposition_order=2`, and S3 relation true.
- Live read-only command `/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v6/optional/nemo_hecke -e 'using Nemo, Hecke; ...'` returned active project equal to that Project.toml, `gl2_2_order=6`, `singular_count=10`, `cycle_order_3=true`, `transposition_order_2=true`, `s3_relation=true`, `hecke_loaded=true`.
- Strict load-path smoke with `JULIA_LOAD_PATH=@:@stdlib` failed at `using JSON3` because `JSON3` is not in `system_v6/optional/nemo_hecke/Project.toml`; see `G2`.

Adjudication: Q4 passes with caveat `G2`. The shape repair is proven only by subtree hashes, not byte identity of the whole envelope. The mode and omissions are honest.

## Q5 Standard Metadata

Parent lineage passes: the envelope records `geo_s10_g2_family_v0` committed commit `77a4f5d19f1f110e59053bd581b45319c8d7569a` and `ratchet_g2_family_v0` committed commit `b5649217cc5b1becfc3b45bb906c4670bd7d3248`, both matching the requested prefixes.

z3/cvc5 dimension-bookkeeping identity passes:

```text
z3 real dimensions: unsat
z3 erased Levi binding: sat
cvc5 real dimensions: unsat
cvc5 erased Levi binding: sat
erased flips detected: true for both
```

Tool-call and capability checks pass with caveats already named:

- Top-level `tool_calls` are one-to-one: `sympy`, `z3`, `cvc5`, `Nemo`.
- `TOOL_MANIFEST` and `TOOL_INTEGRATION_DEPTH` exist and assign load-bearing depth to `sympy`, `z3`, `cvc5`, and `Nemo`; `Hecke`, `json`, `hashlib`, and `subprocess` are supportive.
- Capability receipts record Python `3.13.6`, SymPy `1.14.0`, z3 `4.15.2`, cvc5 `1.3.3`, Julia `1.12.6`, and Nemo sidecar project metadata.
- Seed is `geo_s10_intertwiner_depth_v0_seed_20260611`.
- `rg -n 'fix''ture' system_v6/sims/geo_s10_intertwiner_depth_v0` returned no hits before this verdict file was written.
- Disallowed claims are explicitly listed: no formal admission, no classification of all intertwiners, no retroactive parent promotion, no null-line parabolic classification beyond the computed null-vector stabilizer, and no bridge/axis/physics claim.

Adjudication: Q5 passes with `G2` and `G3` metadata ceilings.

## Q6 Parent Fence Closure

`geo_s10_g2_family_v0` future citation language may upgrade from:

```text
D4 diagram/character-node automorphism order only, not explicit intertwiners
```

to:

```text
one explicit Chevalley-basis D4 triality realization with 8v/8c/8s 8x8 intertwiners, verified by generator-level A*rho(x)=rho'(x)*A residuals and order-3 scalar-cubed check; still not a classification of all possible intertwiners
```

`ratchet_g2_family_v0` future citation language may upgrade from:

```text
null row deferred/nonreductive; no full null-stabilizer Levi classification
```

to:

```text
split null-vector stabilizer computed as dimension 8 with 5D nilradical and 3D sl2_R-type Levi quotient, exact dimension bookkeeping 8=5+3, compact positive control nilradical zero; explicit closed Levi factor not yet supplied
```

Do not cite the new packet as parent promotion, formal admission, canonical theorem, full null-line parabolic classification, or bridge/axis/physics evidence.

## Commands And Checks

- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... import builder; recompute intertwiners/null-stabilizer/proofs ... PY` returned the Q1-Q3 recomputation rows above.
- `PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... import validator with VALIDATOR_RESULT redirected to /tmp; rebuild_result no-write ... PY` returned validator `ok:true`, no errors, subtree hashes matching stored envelope, and rebuilt `all_pass:true`.
- `/opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v6/optional/nemo_hecke -e 'using Nemo, Hecke; ...'` returned the Q4 Nemo/Hecke row.
- `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v6/optional/nemo_hecke -e 'using Nemo, Hecke, JSON3; ...'` failed with `Package JSON3 not found in current path`, producing caveat `G2`.
- `rg -n 'fix''ture' system_v6/sims/geo_s10_intertwiner_depth_v0` returned no hits before this verdict file was written.
- `git status --short` before writing this verdict showed `?? system_v6/sims/geo_s10_intertwiner_depth_v0/` and unrelated `?? system_v6/receipts/old_estate_mine_20260611.md`; I did not stage or commit anything.
