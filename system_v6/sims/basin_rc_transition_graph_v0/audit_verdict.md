# Audit Verdict - basin_rc_transition_graph_v0

Auditor: codex1 cross-backend audit
Date: 2026-06-11
Scope: read-only audit of codex2 builder packet, with this verdict file as the only repo write.

## Verdict

VERDICT: PARTIAL PASS / HOLD STRONG BASIN WORDING.

The packet passes as an explicit finite `R_C` transition graph over the full 33-cell admitted Bloch grid, and it earns the term `terminal/closed communicating class` for the singleton origin class. It also closes the pilot's three carried caveats at the mechanical level: G1 `R_C` explicit, G4 seven controls firing, and G5 a real Julia Graphs/Z3 leg instead of a slot-only label.

It does not fully earn the stronger `B(A)` / unitary-basin wording as written. The emitted `basin_map` uses existential reachability ("can reach the terminal closed class"), while the basin contract defines `B(A)` by omega-limit containment. On the recomputed graph, all 33 cells can reach the terminal singleton, but only the terminal singleton is guaranteed/sure under all successor choices; the 32-cell nonterminal SCC is strongly connected, metastable, and leaky, so internal cycles remain available indefinitely. The honest ceiling is:

`scratch_diagnostic`: first explicit finite transition partition with one closed terminal class, one leaky/metastable 32-cell communicating class, and a reachability-to-terminal map; not a formal admitted basin theorem and not a strict omega-basin partition.

## Quoted Source Anchors

- Build card: "`This yields 33 cells.`" `system_v6/sims/basin_rc_transition_graph_v0/build_card.md:28-32`
- Build card: "`Base R_C uses six declared generators`" `system_v6/sims/basin_rc_transition_graph_v0/build_card.md:34-40`
- Contract: "`B(A) = {x: omega_{R_C}(x) subset A}`" `system_v6/receipts/attractor_basin_criterion_20260611.md:304-305`
- Contract: "`terminal/closed communicating class`" is earned by a closed finite `R_C` class with no outgoing transition. `system_v6/receipts/attractor_basin_criterion_20260611.md:310-315`
- Contract guard: "`Similarity, clustering, repeated motifs, or provider/model agreement is not convergence.`" `system_v6/receipts/attractor_basin_criterion_20260611.md:323-327`

## Recomputations

Scratch recompute artifact: `/tmp/basin_rc_transition_graph_v0_audit_recompute.json`

Method: independently read the committed `geo_s5_terrain_flows_v0` and `geo_s4_operator_stage_v0` result rows, used `scipy.linalg.expm` for terrain `h=0.5`, rebuilt the finite grid, nearest-cell quantization, generator-labelled edges, SCCs, reachability, controls, and solver no-exit checks. No repo result JSON was rewritten.

Fresh command checks:

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json`
  - result: `{"ok": true}`
- scratch graph recompute:
  - full `S` count: 33
  - conditioned-shell flagged count: 4
  - generator count: 6
  - edge count: 198
  - recomputed edge triples match emitted edge triples: true
  - partition signature: `state_count=33`, `scc_count=2`, `class_sizes=[1,32]`, `terminal_sizes=[1]`, `boundary_count=3`
  - terminal class: class `1`, cell `[16]`, coord `[0,0,0]`
  - terminal edges checked: 6, one per generator; all return to cell `16`
  - z3 no-exit: real `unsat`, erased flip `sat`
  - cvc5 no-exit: real `unsat`, erased flip `sat`

## Per-Check Adjudication

### Q1 - Finite Objects

Status: PASS with coarse-grid caveat.

The full state object is not the four conditioned-shell cells. Full `S` is the 33-cell admitted grid. The four cells are flags for the conditioned shell: cells `3, 9, 25, 31`, all in the nonterminal 32-cell SCC. This prevents the packet from being vacuous in the "4-cell shell only" sense.

Named caveat `CAVEAT-COARSE-33`: the discretization is very sparse. It has enough teeth to produce a nontrivial SCC partition and controls, but not enough to support refined sub-basin claims.

`Adm_C` is explicit as `x^2+y^2+z^2 <= 1` over the grid. The generating set is pinned to four S5 terrain rows at `h=1/2` plus `D_z` and `R_x` from S4.

### Q2 - Partition

Status: PASS for SCC/terminal partition; FAIL/HOLD for strict `B(A)` wording.

Independent SCC recompute returns two communicating classes:

- class `0`: size 32, internal fraction `0.9895833333333334`, escape fraction `0.010416666666666666`, metastable true, leaky true.
- class `1`: size 1, terminal closed true, no exits.

The absent-exit proof covers every generator on terminal cell `16`:

- `Se_Funnel_L -> 16`
- `Ni_Pit_L -> 16`
- `Ni_Source_R -> 16`
- `Ne_Spiral_R -> 16`
- `D_z -> 16`
- `R_x -> 16`

The emitted separatrix/boundary cells `[15,16,17]` reproduce. The two nonterminal exits are:

- `15 --Ni_Source_R--> 16`
- `17 --Ni_Pit_L--> 16`

The emitted reachability basin has all 33 cells, but this is existential reachability. A strict all-successors/omega-containment basin recomputes to only `[16]`. This is the main caveat.

Named caveat `CAVEAT-BASIN-MAP-EXISTENTIAL`: `basin_map.B_A_definition` must be weakened or split into `can_reach_terminal=33` versus `omega/sure_basin=1`.

### Q3 - Trapping and Lyapunov

Status: PASS with direction caveat.

For terminal `A={16}`, recomputation gives `R_C(A) subset A = true`; six terminal outgoing generator edges were checked and zero exits were found.

The emitted monotone observable has zero edge violations. However, the packet's observable is exclusion count `|S|-|Reach(x)|`, which is monotone non-decreasing toward the terminal class. The decreasing form is reachable-set size `|Reach(x)|`; that also has zero increase violations in the scratch recompute.

Named caveat `CAVEAT-LYAPUNOV-DIRECTION`: say "exclusion non-decreasing" or "reachable-set size non-increasing," not simply "decreasing exclusion."

### Q4 - Seven Controls

Status: PASS.

All seven controls fired in independent recomputation:

- `similarity_only_cluster`: radius clusters are not closed; escaping edge counts inner `10`, mid `20`, outer `18`.
- `shuffled_order`: changed cells for `Ni_Pit_L/R_x` = 19; `Ne_Spiral_R/D_z` = 10; `Se_Funnel_L/R_x` = 0; control fires overall.
- `root_off`: partition changes from 33-state `2` SCCs to 125-state `4` SCCs.
- `F01_only`: partition changes to `27` SCCs.
- `N01_only`: partition changes to `3` SCCs with terminal sizes `[1,14,18]`.
- `quotient_erased`: radius quotient collapses to 5 nodes, so static similarity does not reproduce the finite state object.
- `commutative_collapse`: partition changes to `33` SCCs.

The pilot's blocked controls G4 are closed mechanically.

### Q5 - Escape and Engine-DoF Rows

Status: COMPUTED / WEAK EFFECT.

Generator-addition escape rows were computed:

- `add_D_x`: partition unchanged; terminal class still closed.
- `add_R_z`: partition unchanged; terminal class still closed.

DoF perturbation rows were computed:

- `remove_Ni_Pit_L`: partition signature changes by boundary count.
- `remove_Se_Funnel_L`: unchanged.
- `R_x_to_R_z`: unchanged.

Named caveat `CAVEAT-DOF-LOW-SENSITIVITY`: the DoF/escape surface is present, but most tested perturbations preserve the unitary terminal signature. This supports robustness of the simple partition, not rich engine-DoF basin structure.

### Q6 - Guard and Earn-The-Term

Status: PASS for terminal-class language; HOLD for "unitary basin" language.

The terminal-class language is earned: finite `R_C` graph, closed class, no outgoing allowed transitions, solver no-exit proof with erased flips.

The sub-basin honesty statement is directionally right that there is one terminal closed class and that richer generators/refinements are needed for subbasins. It should not imply that every nonterminal state has omega-limit subset inside the terminal class. The frontier statement is honest if phrased as "no multiple terminal classes at this generating set; one leaky/metastable 32-cell class remains."

### Q7 - Standard Contract Fields

Status: PASS with controller caveat.

Present:

- envelope schema `three_engine_sim_result_v1`
- canonical helper path `scripts/build_three_engine_envelope.py`
- build card persisted as `build_card.md`
- source-backed validator green under strict source-backed check
- real Julia leg present: Graphs + Z3, result path `system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_julia_results.json`
- JAX and PyTorch legs present
- z3/cvc5/Julia Z3 no-exit proofs with erased flips in envelope
- parent lineage includes `4e082f525` pilot and `50f16d82d` basin contract
- capability receipts and one-to-one tool calls present
- no forbidden fixture wording per emitted packet-local validator result
- versions emitted for Julia, Graphs, Z3, Python, JAX, PyTorch, torch-geometric, z3, cvc5, sympy, and networkx
- seed ledger is deterministic: `rng=none`, tie break `cell_id_ascending`
- ceiling fields are correct: `classification=scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`

Named caveat `CAVEAT-JULIA-SCOPE`: G5 is closed as a real Julia Graphs/Z3 core leg. The full seven-control suite is still Python/JAX/PyTorch-envelope-side, not a full Julia mirror of every control.

Named caveat `CAVEAT-WIZARD-THIS-AUDIT`: this audit did not use native Codex subagents because the available spawn-agent tool contract only permits spawning when the user explicitly requests delegation/parallel agent work. This verdict is controller-local plus fresh command recomputation, not a full Max Assembly worker topology.

## Named Caveats

1. `CAVEAT-COARSE-33`: 33-cell grid is honest and nonvacuous, but sparse.
2. `CAVEAT-BASIN-MAP-EXISTENTIAL`: emitted `B(A)` is reachability-to-terminal, not strict omega/sure containment.
3. `CAVEAT-LYAPUNOV-DIRECTION`: exclusion is non-decreasing; reachable-set size is non-increasing.
4. `CAVEAT-DOF-LOW-SENSITIVITY`: most escape/DoF perturbations preserve the simple terminal signature.
5. `CAVEAT-JULIA-SCOPE`: Julia closes core graph/proof G5, not every envelope-side control.
6. `CAVEAT-WIZARD-THIS-AUDIT`: this audit is not a full native-subagent Wizard topology.

## Final Ceiling

Accepted: `passes local rerun` / source-backed scratch diagnostic for the finite graph partition, terminal closed class, absent-exit proof, controls, and three-engine envelope shape.

Rejected above ceiling: formal admission, strict omega-basin partition for all 33 cells, nested/sub-basin claim, rich engine-DoF basin structure, or any "the basin theorem is closed" wording.

No `git add` or `git commit` was run.
