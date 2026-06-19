# Fresh Audit Verdict: ratchet_g2_family_v0

Auditor: codex2 cross-backend audit.
Write boundary observed: this file only. I did not git add or commit anything.

Blind sheet: `/tmp/g2_ratchet_blind_expectations.md`.
Calibration bar: `system_v6/receipts/audit_bar_calibration_20260610.md`.

## Verdict

VERDICT: GENUINE-WITH-CAVEATS.

The packet earns the bounded algebraic ratchet claim over the committed G2-family carrier: compact `Der(O)` recomputes to dimension 14, the compact chosen-unit stabilizer solves to dimension 8 with coset 6, compact branch ranks are projection-derived for `7`, `14`, and `27`, the split family forks by computed causal type, and the compact stabilize/branch order check has zero gap.

Ceiling: `scratch_diagnostic`; `promotion_allowed=false`; `formal_admission_allowed=false`. This does not earn a crowned compact/split form, a preferred hybrid crowned form, a canonical G2 theorem, nesting-over-shells of G2 data, bridge/axis claims, physics claims, or a full null-stabilizer Levi decomposition.

## Source Quotes

- Derivation equations are built from the multiplication table, not table prose: `derivation_matrix(table)` loops over `i,j,k` and returns `sp.Matrix(rows)` in `system_v6/sims/ratchet_g2_family_v0/ratchet_g2_family_v0.py:273-287`.
- Derivation dimension is rank/nullity: `"nullity_dim_der": n * n - rank` at `ratchet_g2_family_v0.py:294-310`.
- Stabilizer is a solve-space: `action = sp.Matrix(rows)`, `rank = int(action.rank())`, and `kernel = action.nullspace()` at `ratchet_g2_family_v0.py:362-370`.
- Branch projectors are computed from the fixed line and left multiplication: `p_plus = (pc - I * jmat) / 2` and `p_minus = (pc + I * jmat) / 2` at `ratchet_g2_family_v0.py:408-414`.
- Branch rows use projector/action ranks: `p3_action_rank = int((p3 * action).rank())` and tensor-block ranks at `ratchet_g2_family_v0.py:482-518`.
- Split labels are conditioned by computed norm and left-multiplication relation, with the null row explicitly not promoted: see `ratchet_g2_family_v0.py:562-604`.
- SMT controls bind the computed dimension sum, then erase it for the flip: `solver.add(combo == ...)` and `solver.add(combo != 29)` at `ratchet_g2_family_v0.py:685-724`.

## Recomputations

I used read-only imports with `PYTHONDONTWRITEBYTECODE=1`; I did not run packet entrypoints that rewrite result JSONs.

- Compact derivation: recomputed rank/nullity `50/14` from the derivation matrix.
- Compact stabilizer of the chosen imaginary unit: recomputed constraint rank `6`, stabilizer dimension `8`, coset/orbit dimension `6`, closure under commutator true.
- Branch `7`: recomputed projector ranks `fixed_line=1`, `orthogonal_complement=6`, `complex_3=3`, `complex_3bar=3`, dimension sum `7`.
- Branch `14`: recomputed stabilizer rank `8`, projected ranks `3` and `3bar` both `3`, dimension sum `14`.
- Branch `27`: recomputed raw symmetric projector ranks `1x1=1`, `1x3=3`, `1x3bar=3`, `sym2_3=6`, `sym2_3bar=6`, `3x3bar_raw=9` with trace present; trace-free block sum `27`.
- Split fork: recomputed `u.u=+1` for `spacelike_positive_e1`, `u.u=-1` for `timelike_negative_e4`, and `u.u=0` for `null_e1_plus_e4`; all three stabilizer solve-spaces have dimension `8`.
- Split labels: positive row reports `su(2,1) / su(1,2)` with `J^2=-I` residual rank `0`; negative row reports `sl(3,R)` with `J^2=+I` residual rank `0`; null row reports nonreductive/null, relation residual rank `1`, and does not promote a full Levi classification.
- Path specificity: recomputed branch-then-stabilize constraint rank `6`, stabilizer dimension `8`, span equality true, rank gap `0`; compact pipelines agree.
- Controls: wrong non-imaginary unit is rejected and would otherwise alias to the imaginary part; sign-flipped table breaks `Der=14` to nullity `3`; permuted projector changes the valid `7` sum to `8`; nothing-excluded leaves derivation basis hash byte-exact and dimension `14`.
- SMT: recomputed `z3=unsat`, erased `z3=sat`; recomputed `cvc5=unsat`, erased `cvc5=sat`.
- Julia leg: existing receipt uses project `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`; live Julia smoke with `Z3` under that project returned `unsat`.

## Blind-Sheet Diff

Q1 passed. The packet recomputes `Der(O)=14` by nullity, computes the chosen-unit stabilizer solve-space as dimension `8`, and reports narrowing `14 -> 8`.

Q2 passed. The branch-table echo risk is materially addressed: at least one load-bearing projector/action rank exists for each requested branch, and my recomputation matched the envelope. I did not find a branch dimension that appears only as copied representation-table prose.

Q3 passed with caveat G1. The split row dimensions and causal classes are computed. The packet agrees with the blind sheet on positive/spacelike `su(2,1) / su(1,2)`, negative/timelike `sl(3,R)`, and null as nonreductive/deferred. It does not collapse split rows to compact `SU(3)`.

Q4 passed. Compact stabilize-then-branch and branch-then-stabilize agree with order gap `0`.

Q5 passed. The wrong-unit, sign-flipped, permuted-projector, nothing-excluded, z3, cvc5, and Julia Z3 controls all fire in the intended direction.

Q6 passed with caveat G2. Schema mode is `RATCHETED`; parent lineage includes the committed `geo_s10_g2_family_v0` commit `77a4f5d19f1f110e59053bd581b45319c8d7569a`, tree `d2de46273a77e9952148ea2b73c5e03f53e620c0`, and recomputed envelope sha256 `5a4dc0281e0f07121b0ffd5b184362c4d2fcd7a861d038388840c765d82c2e35`; tool calls are one-to-one `sympy`, `z3`, `cvc5`, `Z3`; validators pass; no fixture wording was found; disallowed crowned/physics/bridge claims are present only as explicit not-earned/disallowed claims.

Q7 passed. Earned: algebraic ratchet on the G2-family carrier, namely stabilizer narrowing plus computed branchings plus split causal fork. Not earned: no crowned form, no preferred hybrid crowned form, no nesting-over-shells of G2 data, no bridge/axis, no physics/SM claim, no full null-stabilizer classification.

## Caveats

G1 - Split real-form label ceiling. The packet computes split stabilizer dimensions by solve-space and computes causal norm plus left-multiplication square relations. The labels `su(2,1) / su(1,2)` and `sl(3,R)` are justified by those computed discriminators, but this is not an independent Cartan/Killing-form real-form classification proof. The null row is honestly kept at dimension/nilpotent evidence only.

G2 - Engine naming ceiling. The envelope uses lanes `julia` and `jax`, but its `jax` lane is a Python exact algebra/SMT lane, not a JAX array/backend computation. The packet states this in the engine record and the claim does not require a JAX-specific operation, so this is not a failure; do not cite it as a true JAX backend result.

## Commands And Checks

- `env PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... mod.build_math(); mod.solver_proofs(...) ... PY` returned the recomputed rows above and matched envelope engine values.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-source-backed system_v6/sims/ratchet_g2_family_v0/results/ratchet_g2_family_v0_envelope_results.json` returned `ok:true`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --strict-source-backed system_v6/sims/ratchet_g2_family_v0/results/ratchet_g2_family_v0_envelope_results.json` returned `ok:true`.
- Read-only import of `validate_ratchet_g2_family_v0.py` and direct `validate(payload)` returned `ok:true` with no errors.
- `git log -n 1 --format=%H -- system_v6/sims/geo_s10_g2_family_v0` returned `77a4f5d19f1f110e59053bd581b45319c8d7569a`.
- `git show HEAD:system_v6/sims/geo_s10_g2_family_v0/results/geo_s10_g2_family_v0_envelope_results.json | shasum -a 256` returned `5a4dc0281e0f07121b0ffd5b184362c4d2fcd7a861d038388840c765d82c2e35`.
- `JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier -e 'using JSON3, Z3; ...'` returned project `/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml`, Julia `1.12.6`, and `z3_status=unsat`.

