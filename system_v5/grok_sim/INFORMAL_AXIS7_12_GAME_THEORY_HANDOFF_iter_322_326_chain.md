# INFORMAL Axis 7-12 / game-theory handoff — iter_322 through iter_326

Date: 2026-05-25
Author: Claude (informal sidequest thread)
Lane: `system_v5/grok_sim/` only. Not formal-lane evidence.
Driving prompt: `system_v5/grok_sim/INFORMAL_AXIS7_12_GAME_THEORY_AUDIT_AND_PROMPT_20260525.md`

All five iters carry: `claim_ceiling = side_quest_only`, `promotion_allowed = false`, `evidence_allowed = false`, `evidence_allowed_for_formal = false`, `formal_reproduction_target = false`, `blocked_formal_consumers = ["manifold", "axis", "flux", "Axis0", "bridge", "physics", "canon"]`. No writes outside `system_v5/grok_sim/`. A7-A12 are named exclusively as `A7_shadow..A12_shadow` and never as axes.

Boundary-guard baseline at session start: 80 violations across 60 unique paths (captured to `/tmp/grok_sim_guard_baseline_paths.txt`).
Boundary-guard delta after all five new iters: **0 new violation paths**.

---

## 1. What ran

| Iter | Mode | Subject | strict_pass | Wall time |
|---|---|---|:---:|---:|
| iter_322 | baseline | 4-player 2-action classical game, four IGT quadrants, z3+cvc5 search | True | ~0.23 s |
| iter_323 | forward_exploration | QIT-FEP payoff lift: classical-diagonal vs quantum-product vs GHZ | True | ~0.05 s |
| iter_324 | forward_exploration | IGT Axis6 order witness Ne/Ti and Si/Fe + T/F MI drop | True | ~0.04 s |
| iter_325 | forward_exploration | A7_shadow..A12_shadow on 4-engine 32-event graph | True | ~0.03 s |
| iter_326 | reverse_derivation | dependency gaps, killed hypotheses, formal targets | True | ~0.00 s |

Five iters, five strict-pass. Each iter is between 220-510 lines of Python. Total wall time under 0.5 s.

---

## 2. What worked

**iter_322 classical baseline.** 4-player 2-action game with four IGT quadrant payoff tables. WinWin shows classical Pareto inefficiency at uniform-mixed strategies. LoseLose admits 12 pure-strategy local-loss/global-gain transitions in the sacrifice game design. z3 and cvc5 independently confirm sat on a 32-integer payoff witness in [-3, 3]; they agree. Sequential best-response from uniform-init collapses to N01 = 0 in this game class — recorded as a real classical-baseline finding, not smuggled. The iter's audit gates include this honestly as "sequential_order_n01_collapses_at_uniform_init_baseline_finding".

**iter_323 QIT-FEP lift.** Three carriers: classical-diagonal, quantum-product-coherent, GHZ-entangled. Classical-diagonal and quantum-product payoffs agree at the marginal level (within 1e-9), confirming the lift preserves classical content. GHZ total correlation = 4·log(2) ≈ 2.7726 in all four quadrants while product total correlation = 0; the entanglement readout is real. GHZ payoff differs from product payoff (audit gate passed).

**iter_324 IGT Axis6 order witness.** Ne/Ti pair noncommutes at all four test states with probe-norm witness up to ~5e-2. Si/Fe collapses by basis alignment at every test state — recorded honestly as a real structural finding (Phi_Si and U_Fe both diagonal in the z-eigenbasis per doc 07 construction, so [Phi_Si, U_Fe] = 0 analytically). Order-erased and commuting-only controls collapse to <1e-12 exact. T/F strategy contrast at Ne topology: F-route (rotation) preserves coherence at every test state; T-route (dephasing) does not. Bell-pair partner MI drop: T-route drops MI by 0.61 nats; F-route drops by ~0 nats.

**iter_325 collective shadow map.** 4-engine × 4-time-step × 2-macro-stage event graph (32 events). Three shadows computed concretely (A7 pairwise sign-covariance ranges [-0.75, 0.75]; A8 rustworkx min-cut value = 0.75 with partition counts [1, 3]; A11 within-family covariance gap |F| − |T| = 0.25). Three shadows specified with explicit dependency gaps (A9 private/public split, A10 schedule-order N01, A12 policy/evidence channel order). GUDHI persistent homology over the payoff filtration returns 8 features. XGI coalition 3-subsets and TopoNetX simplicial complex both load-bearing.

**iter_326 reverse derivation.** Reads iter_322..iter_325 result JSONs and emits 6 patterns, 2 killed hypotheses, 3 open hypotheses, 6 priority-ordered dependency gaps, and 4 narrow formal-lane reproduction targets — each with explicit fails_if conditions.

---

## 3. What failed (honestly)

- **iter_322 sequential N01 = 0 at uniform init.** Best-response dynamics converge identically under forward and reverse player orderings because each player's BR depends only on others' marginals. Recorded as baseline finding, not smuggled. Forward target: noisy/epsilon BR, non-uniform init, or extensive-form sequential games.
- **iter_324 Si/Fe collapses by basis alignment.** Phi_Si (z-diagonal H_C + z-eigenstate projectors) and U_Fe (z-axis rotation) share the z-eigenbasis. [Phi_Si, U_Fe] = 0 analytically. The chart distinction between FeSi and SiFe in doc 06 is Axis3 placement only, not Axis6 noncommutation. This kills one specific hypothesis (see Section 4).
- **iter_325 A9/A10/A12 spec-only.** These three shadows have finite maps and dependency gaps recorded but their characteristic observables are not computed in this iter. Acknowledged in `failed_predictions`.

---

## 4. Killed hypotheses

1. **"FeSi differs from SiFe at the Axis6 channel level under the doc-07 Phi_Si and U_Fe construction"** — falsified by iter_324. The doc 07 construction explicitly chose H_C and the projectors to commute (invariant-subspace terrain); combined with z-axis Fe rotation, the entire Si/Fe pair lives in one eigenbasis and the Axis6 order witness is identically zero. The surviving reading is: the chart distinction is Axis3 placement, not Axis6 noncommutation. Future iters that want Si/Fe Axis6 content need to perturb H_C off the z-axis.
2. **"Sequential best-response order matters at uniform-init mixed strategy"** — falsified by iter_322. Best-response from uniform converges identically under any player update order. Forward targets: noisy/epsilon BR, non-uniform init, or extensive-form games.

---

## 5. Open hypotheses

1. **Local-loss/global-gain transitions are common across sacrifice-game families.** Evidence: iter_322 LoseLose has 12 such transitions. Counter: only one sacrifice game tested. Next test: vary sacrifice game family (threshold-public-goods, dictator-with-cost) and check witness count.
2. **QIT-FEP lift adds collective signal beyond classical at the payoff level.** Evidence: iter_323 GHZ TC = 4log2. Counter: GHZ payoff difference vs product may be marginal-driven, not coherence-driven. Next test: add a classical-product-with-matched-marginal control to iter_323.
3. **A9/A10/A12 collective shadows have computable observables on a PEPS3D-anchored population state.** Evidence: iter_325 specs and finite maps. Counter: not computed. Next test: 2-engine population on small PEPS lattice with all three shadows computed.

---

## 6. Dependency gaps (priority order)

1. **G1** — No PEPS3D carrier anchor for population state. Blocks P2/P3/P5 admissibility and G6. Concrete step: lift iter_320-style 64-cell schedule to 2 engines on 2×2×2 PEPS lattice with bond-link channels between engines. One iter, ~500 lines.
2. **G2** — No CPTP-equivalent Axis6 order witness. Blocks P3 admissibility. Express M_NeTi and M_TiNe as superoperators; verify the difference is a non-zero CPTP-distance. Small addendum to iter_324.
3. **G3** — iter_323 GHZ vs product payoff may be marginal-driven. Add classical-product-with-matched-marginal control. One short iter.
4. **G4** — iter_325 A9/A10/A12 are spec-only. Build private/public broadcast channel, population schedule lift, and policy/evidence channel pair. One iter per shadow.
5. **G5** — Local axes A1..A6 not stably defined locally. iter_312..iter_321 showed L/R structural ratio is seed-region-dependent. Formal-lane work, not in grok_sim scope.
6. **G6** — No terrain Lindblad lift to multi-engine state. Build Kraus representation of X_terrain and lift to single-site channel on a 2-engine product state. Integrate with iter_320 bond-link channels. One iter.

---

## 7. Formal-lane reproduction targets (narrow + reproducible)

Each target includes a reproduction recipe, expected outcome, and a `fails_if` negative condition. None of these are formal-lane support; they are sidequest reproduction prompts only.

| Target | Scope | Expected outcome | Fails if |
|---|---|---|---|
| T1 — z3+cvc5 local-loss/global-gain payoff witness | classical only | sat with small-coefficient witness in [-3,3] | unsat from either solver |
| T2 — Bell-pair T-route MI drop vs F-route preservation | 2 qubits | T drops MI ~0.6 nats, F drops ~0 | F-route also collapses MI |
| T3 — Ne/Ti Axis6 witness with order-erased + commuting-only controls | single qubit density | Delta_A6 ~ 5e-2; controls <1e-12 | Delta_A6 collapses |
| T4 — A8 min-cut on coalition-signed interaction graph | classical 4-engine population | nontrivial cut with numeric value; current toy gives value 0.75 and partition counts [1, 3] | rustworkx API change, missing numeric cut, or degenerate cut |

---

## 8. Tool usage summary

| Tool | Use across iter_322-326 |
|---|---|
| torch | load-bearing in iter_323 and iter_324; supportive in iter_322 and iter_325; not relevant in iter_326 |
| z3 | load-bearing in iter_322 (finite payoff search) |
| cvc5 | load-bearing in iter_322 (independent cross-check; agreement with z3 confirmed) |
| sympy | not relevant at any iter; could be load-bearing later for symbolic Delta_A6 |
| Clifford / geomstats / e3nn | not relevant at any iter |
| rustworkx | load-bearing in iter_325 (interaction graph; min-cut value 0.75) |
| XGI | load-bearing in iter_325 (coalition 3-subset hyperedges built) |
| TopoNetX | load-bearing in iter_325 (simplicial complex for private/public surface) |
| GUDHI | load-bearing in iter_325 (persistent homology over payoff filtration; 8 features) |
| PyG | available_but_not_used; rustworkx covered the graph readout cheaply |

Per the prompt's max-tool-usage rule, every tool that wasn't load-bearing in a given iter is marked `not_relevant_this_iter` with a one-line reason or `deferred_to_iter_X` for the iter where it might become load-bearing.

---

## 9. Boundary-guard status

| Stage | Total violations | Unique paths | Delta from baseline |
|---|---:|---:|---:|
| Session start | 80 | 60 | 0 |
| After iter_322 (first attempt) | 81 | 61 | +1 (introduced by a stale overclaim phrase in claim_ceiling_text) |
| After iter_322 (repaired) | 80 | 60 | 0 |
| After iter_323 | 80 | 60 | 0 |
| After iter_324 | 80 | 60 | 0 |
| After iter_325 | 80 | 60 | 0 |
| After iter_326 | 80 | 60 | 0 |

The one transient violation came from a stale overclaim phrase inside my own claim_ceiling_text that was within the guard's `DANGEROUS_TEXT_PATTERNS` list even with the negation. Rephrased to "sidequest-local; not a basis for any formal-lane claim" and the guard delta returned to zero.

---

## 10. Files written this session (iter_322-326 only)

```
system_v5/grok_sim/iters/iter_322_claude_classical_game_baseline.py
system_v5/grok_sim/iters/iter_323_claude_qit_fep_payoff_lift.py
system_v5/grok_sim/iters/iter_324_claude_igt_axis6_order_witness.py
system_v5/grok_sim/iters/iter_325_claude_collective_shadow_map.py
system_v5/grok_sim/iters/iter_326_claude_reverse_derivation_report.py

system_v5/grok_sim/results/iter_322_claude_classical_game_baseline_results.json
system_v5/grok_sim/results/iter_323_claude_qit_fep_payoff_lift_results.json
system_v5/grok_sim/results/iter_324_claude_igt_axis6_order_witness_results.json
system_v5/grok_sim/results/iter_325_claude_collective_shadow_map_results.json
system_v5/grok_sim/results/iter_326_claude_reverse_derivation_report_results.json

system_v5/grok_sim/INFORMAL_AXIS7_12_GAME_THEORY_HANDOFF_iter_322_326_chain.md  (this file)
```

No writes to `system_v5/ops/formal_scouts/`, `system_v5/docs/`, `system_v5/evidence/`, or any formal classifier/index. All five result JSONs carry sidequest-local classification and full schema (sim_id, claim_ceiling, mode, F01, N01, finite_map, domain, codomain_or_output, carrier, spinor/density/peps3d/quaternion status, controls, negative_conditions, tool_manifest, tool_integration_depth, observables, pass_fail, failed_predictions, dependency_gaps, blocked_formal_consumers, schema_version).
