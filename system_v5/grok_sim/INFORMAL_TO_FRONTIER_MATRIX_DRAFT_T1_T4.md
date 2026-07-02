# INFORMAL → frontier matrix DRAFT for T1-T4

Date: 2026-05-25
Author: Claude (informal sidequest thread)
Lane: `system_v5/grok_sim/` only.

**STATUS: DRAFT / SOURCE SUGGESTION ONLY.** This document is NOT a frontier matrix. It is NOT `system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json`. The formal lane authors the actual frontier matrix; that file lives under `system_v5/ops/formal_scouts/` and is validated by `scripts/validate_bounded_max_exploration.py`.

This file is a sidequest-local pre-translation of the four reproduction targets that iter_326 emitted, re-expressed in the `FRONTIER_ROW_REQUIRED_FIELDS` schema (11 fields per row) so the formal-lane owner can read the raw material in approximately the right shape. Nothing here carries:

- `classification: formal_scout` (informal lane is forbidden from using formal-lane classifications)
- `promotion_allowed: true`
- `evidence_allowed: true`
- a `status` in `{contract_complete, survived}` (sidequest cannot self-stamp those)

If any field below is wrong for the formal-lane schema, the formal lane corrects it. Source-of-truth lives in iter_326's `formal_targets_narrow_and_reproducible` block, not here.

---

## Schema being targeted

Per `scripts/validate_bounded_max_exploration.py`, `FRONTIER_ROW_REQUIRED_FIELDS`:

```
row_id
candidate_family
carrier
probe_or_effect_family
operator_or_path_witness
positive_case
negative_control
boundary_control
status
blocked_consumers
next_in_level_move
```

The four rows below populate each of those 11 fields. The `status` field is left at `draft_source_only` because sidequest-local cannot legitimately claim `contract_complete` or `survived`; the formal lane decides the real status after its own rerun.

---

## Row T1 — z3+cvc5 local-loss/global-gain payoff witness

| Field | Value |
|---|---|
| `row_id` | `T1_classical_payoff_witness_draft` |
| `candidate_family` | finite-integer-payoff local-loss/global-gain witness |
| `carrier` | classical 4-player 2-action joint action space; |S| = 16 |
| `probe_or_effect_family` | 32 integer payoff variables `u_i(a)` ∈ [-3, 3] |
| `operator_or_path_witness` | unilateral action flip `a → a'` where `a_i ≠ a'_i`; delta_payoff_i < 0 ∧ delta_V_others > 0 |
| `positive_case` | iter_322 sat verdict on z3 AND cvc5 independently agreeing on existence of a payoff table in [-3, 3] satisfying the constraint |
| `negative_control` | tighten search to [-1, 1] integer range; expected unsat or trivially-degenerate witnesses |
| `boundary_control` | replace `<` and `>` with `≤` and `≥`; degenerate witness with delta_i = 0 ∧ delta_V = 0 must not be admitted |
| `status` | `draft_source_only` (formal lane decides real status) |
| `blocked_consumers` | manifold, axis, flux, Axis0, bridge, physics, canon, peps3d, frontier_matrix_promotion |
| `next_in_level_move` | encode constraint in formal-lane harness; rerun both solvers; record agreement-on-sat |

iter_322 evidence summary: z3 sat with 8-variable witness `u_0(0000)=-1, u_0(1000)=-2, u_1(0000)=-2, u_1(1000)=-1, u_2(0000)=-2, u_2(1000)=-1, u_3(0000)=-2, u_3(1000)=-1` (delta_i = -1, delta_V_others = +3). cvc5 cross-check also sat. Sidequest-local.

---

## Row T2 — Bell-pair T-route MI drop vs F-route preservation

| Field | Value |
|---|---|
| `row_id` | `T2_bellpair_T_vs_F_MI_drop_draft` |
| `candidate_family` | single-qubit channel applied to one side of a Bell pair; mutual-information drop as strategy-family signature |
| `carrier` | 2-qubit Bell pair `(|00>+|11>)/√2`; 4-dim Hilbert; reduced-q0 and reduced-q1 via partial trace |
| `probe_or_effect_family` | mutual information `I(q0:q1) = S(rho_q0) + S(rho_q1) - S(rho_full)` |
| `operator_or_path_witness` | T-route channel applied to q0 (Hamiltonian step + z-dephasing); F-route channel applied to q0 (Hamiltonian step + y-rotation) |
| `positive_case` | iter_324 observation: T-route MI drop = 0.6109 nats; F-route MI drop = 0.0 |
| `negative_control` | apply identity channel to q0; MI drop must equal 0 within machine epsilon |
| `boundary_control` | replace q0 channel with a channel acting only on q1's ancilla register; MI drop unchanged (channel disjoint from cut) |
| `status` | `draft_source_only` |
| `blocked_consumers` | manifold, axis, flux, Axis0, bridge, physics, canon |
| `next_in_level_move` | formal-lane rerun on torch-native Kraus representation; sweep over multiple Bell-pair seeds to confirm T-vs-F gap is seed-independent |

iter_324 evidence summary: Bell-pair (|00>+|11>)/√2; T-route channel `Pi_Ti ∘ Phi_Ne` on q0 yields reduced-q0 with MI drop 0.6109 nats; F-route `Phi_Ne ∘ U_Fi` on q0 yields MI drop 0.0 nats. Both controls collapse to <1e-12. Sidequest-local.

---

## Row T3 — Ne/Ti Axis6 order witness with controls

| Field | Value |
|---|---|
| `row_id` | `T3_ne_ti_axis6_order_witness_draft` |
| `candidate_family` | Axis6 terrain-first vs operator-first noncommutation on the (Ne, Ti) channel pair |
| `carrier` | single-qubit density `rho ∈ D(C^2)` seeded from spinor formula at four test points |
| `probe_or_effect_family` | 6-effect cube-vertex POVM `{E_a = (1/6)(I + r_a·σ)}` with directions `{±x, ±y, ±z}` |
| `operator_or_path_witness` | `Delta_A6(Ne, Ti; rho) = ‖Pi_Ti(Phi_Ne(rho)) - Phi_Ne(Pi_Ti(rho))‖` |
| `positive_case` | iter_324: probe-norm witness up to 5e-2 across four test states |
| `negative_control` | order-erased control: apply `Pi_Ti ∘ Phi_Ne` twice in both branches; difference < 1e-12 |
| `boundary_control` | commuting-only control: replace `Phi_Ne` and `Pi_Ti` with identity channels; difference < 1e-12 |
| `status` | `draft_source_only` |
| `blocked_consumers` | manifold, axis, flux, Axis0, bridge, physics, canon |
| `next_in_level_move` | formal-lane rerun expressing both channels as CPTP superoperators; verify witness is a property of the superoperator structure (not the specific Kraus-rank-1 representative) |

iter_324 evidence summary: four spinor-seeded test states; max Delta_A6 probe-norm 5.12e-2. Order-erased control 0; commuting-only control 0. Si/Fe pair collapses by basis alignment (recorded honestly as killed hypothesis). Sidequest-local.

---

## Row T4 — A8_shadow min-cut on coalition-signed interaction graph

| Field | Value |
|---|---|
| `row_id` | `T4_a8_min_cut_coalition_signed_graph_draft` |
| `candidate_family` | weighted min-cut on a population-level interaction graph derived from pairwise payoff sign-covariance |
| `carrier` | classical 4-engine event graph with 32 events; pairwise sign-covariance derived from per-event payoffs |
| `probe_or_effect_family` | rustworkx `PyGraph` with 4 nodes (engines), 6 edges (all pairs), edge weights `|sign-cov(i,j)|` |
| `operator_or_path_witness` | Stoer-Wagner min-cut value and partition |
| `positive_case` | iter_325: min-cut value 0.75 with partition node counts [1, 3] |
| `negative_control` | replace edge weights with i.i.d. uniform on [0,1] noise; expected min-cut distribution is order-statistic of uniform, not a 0.75 spike |
| `boundary_control` | constant edge weights = 0.5; min-cut should equal 3 × 0.5 = 1.5 with arbitrary partition |
| `status` | `draft_source_only` |
| `blocked_consumers` | manifold, axis, flux, Axis0, bridge, physics, canon |
| `next_in_level_move` | formal-lane rerun on a larger population (N ≥ 8 engines) to determine whether cut value is structurally significant or small-N artifact |

iter_325 evidence summary: 4-engine population labeled with IGT quadrant assignment and Axis5 family; rustworkx Stoer-Wagner min-cut = 0.75 with partition counts [1, 3] (after iter_325 patch). XGI coalition 3-subsets and GUDHI persistent homology load-bearing on the same population. Sidequest-local.

---

## What the formal lane should do with this

1. Treat each row as a *source candidate*, not a frontier-matrix row.
2. Translate each row into the actual frontier matrix at `system_v5/ops/formal_scouts/phase1_frontier_matrix_20260525.json`. The formal-lane translation must:
   - Decide each row's real `status` (one of `contract_complete`, `survived`, `needs_reissue`, `needs_rerun`, `killed`, `blocked`).
   - Replace `draft_source_only` with the chosen status.
   - Adjust `blocked_consumers` to match the formal-lane closeout schema.
   - Add any required fields the informal lane cannot legitimately provide (e.g., `formal_reproduction_target = true` if the row is admitted).
3. Run `scripts/validate_bounded_max_exploration.py` against the translated matrix.
4. If T1-T4 collectively form less than the minimum frontier-row count for closeout, write a Phase 1 blocker and stop, do not let an informal draft fill the matrix.

---

## What this document is NOT

- NOT a frontier matrix
- NOT a Phase 1 closeout artifact
- NOT formal evidence
- NOT a promotion artifact
- NOT a license for the informal lane to declare any of T1-T4 admitted
- NOT a substitute for the formal-lane rerun

If any reader treats this as the actual frontier matrix, they have misread the file header. The "DRAFT / SOURCE SUGGESTION ONLY" stamp at the top is the binding interpretive instruction.
