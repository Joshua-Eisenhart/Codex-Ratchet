# Fresh Audit Verdict - basin_generating_set_sweep_v0

Auditor: codex2 cross-backend audit.
Scope: read-only audit of codex1 builder packet, except this verdict file.
Verdict vocabulary: calibrated bar plus basin contract may/must semantics.

## Bottom Line

VERDICT: GENUINE-WITH-CAVEATS.

The packet earns the first finite 33-cell-grid sub-basin structure at scratch scope: `G1`, `G3L`, `G3R`, and `G5` split into multiple terminal closed communicating classes; `G2` re-merges to the one-terminal-class baseline; `G4` shrinks to the conditioned-shell carrier and remains single-terminal. The splits are label-free SCC/terminal-class facts on the finite transition graph, not label-count echoes.

It does not earn refined sub-basin geometry, invariant-circle/cell geometry beyond the fixed 33-cell grid, or the successor two-engine product. The decisive missing check is a grid-refinement or rotated-grid control for the `G1` rotation classes.

## Source Quotes

- Build card source: status is "builder packet only" and ceiling is `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false` (`build_card.md:3-4`).
- Parent source: `basin_rc_transition_graph_v0` at `631f1c3db` supplies the "33-cell carrier, generator-labelled graph machinery, and may/must basin semantics"; basin contract `000f48e71` supplies extended basin vocabulary (`build_card.md:15-18`).
- Sweep rows: `G1` is rotations only (`R_x`, `R_z`, `Ne_Spiral_R`, `Ne_Vortex_L`); `G3L/G3R` are chirality subsets; `G5` is the word `Ni_Pit_L` then `R_x` as a single move (`build_card.md:24-31`).
- Deliverables required partition fate, terminal counts, may/must sizes, controls, `G5` commutative-collapse contrast, z3/cvc5 erased flips, real Julia Graphs/Z3, lineage, receipts, and helper envelope (`build_card.md:35-47`).
- Earn-the-term rule: "A second terminal closed class in any other row earns the first computed sub-basin structure only for that row and only at this scratch ceiling" (`build_card.md:51-53`).

## Commands Run

- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY' ... PY`
  - Fresh in-memory recomputation from packet source and parent inputs, using `scipy.linalg.expm`, `networkx`, z3, and cvc5.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/basin_generating_set_sweep_v0/results/basin_generating_set_sweep_v0_envelope_results.json`
  - Returned `{"ok": true, ...}`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/basin_generating_set_sweep_v0/results/basin_generating_set_sweep_v0_envelope_results.json`
  - Returned `{"ok": true, ...}`.
- `git ls-files --error-unmatch ...`
  - Parent basin result and basin contract are tracked; this packet's envelope is not tracked.
- `git log -n 1 --format='%H %s' -- ...`
  - Parent basin result commit is `631f1c3db2d56a24f24a6bbd3b92ad6428860771`.
  - Basin contract commit is `000f48e716d28fa84984e6aad6cb35c115745616`.

No `git add` or `git commit` was run.

## Q1 - G0 Anchor

PASS.

Fresh recomputation of `G0` matched the committed parent partition and transition graph byte hash:

```text
parent partition_signature = {state_count:33, scc_count:2, terminal_sizes:[1], class_sizes:[1,32], boundary_count:3}
recomputed partition_signature = same
parent transition_graph_sha256 = bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0
recomputed transition_graph_sha256 = bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0
```

The stored row also says `baseline_anchor_byte_exact=true`, `terminal_class_count=1`, `may_basin_sizes=[33]`, and `must_basin_sizes=[1]`. This preserves the parent may/must split rather than flattening it.

## Q2 - G1 Split

PASS for finite 33-cell terminal classes. CAVEAT C1 blocks geometric refinement language.

Fresh SCC recomputation from the source graph builder matched the stored summary:

```text
G1 state_count=33
G1 scc_count=3
G1 terminal_class_count=3
G1 terminal_class_sizes=[1,14,18]
G1 may_basin_sizes=[1,14,18]
G1 must_basin_sizes=[1,14,18]
G1 fate=SPLITS
```

Terminal cells:

```text
class 0 size 14: [0,1,3,7,9,10,14,18,22,23,25,29,31,32]
class 1 size 18: [2,4,5,6,8,11,12,13,15,17,19,20,21,24,26,27,28,30]
class 2 size 1: [16]
```

Absent-exit proof was recomputed per generator. For each terminal class, every edge under `R_x`, `R_z`, `Ne_Spiral_R`, and `Ne_Vortex_L` stayed inside its class:

```text
class size 14: R_x 14/0 exits, R_z 14/0, Ne_Spiral_R 14/0, Ne_Vortex_L 14/0
class size 18: R_x 18/0 exits, R_z 18/0, Ne_Spiral_R 18/0, Ne_Vortex_L 18/0
class size 1:  R_x 1/0 exits,  R_z 1/0,  Ne_Spiral_R 1/0,  Ne_Vortex_L 1/0
```

Earn-the-term discipline is held in the source and result rows: `earns_sub_basin_term` is true only when `terminal_class_count > 1` (`common.py:317`), and the packet's stated sub-basin answer names only `G1`, `G3L`, `G3R`, and `G5` as split rows (`common.py:510-512`).

CAVEAT C1 - no refinement/rotated-grid control. I found no packet artifact mentioning grid refinement, rotated-grid control, or axis-alignment testing. The three `G1` terminal classes are real finite SCCs on the fixed 33-cell carrier. They are not yet earned as refined invariant circles/cells rather than possible artifacts of the 33-cell grid.

## Q3 - Chirality Splits

PASS, with precise interpretation.

Fresh recomputation of `G3L` and `G3R` matched stored rows:

```text
G3L: state_count=33, scc_count=8, terminal_class_count=3, terminal_class_sizes=[1,1,6]
G3R: state_count=33, scc_count=8, terminal_class_count=3, terminal_class_sizes=[1,1,6]
```

They do not give the same terminal cell sets:

```text
G3L terminal cells = [[1], [2,4,5,11,12,15], [16]]
G3R terminal cells = [[16], [17,20,21,27,28,30], [31]]
same_terminal_cell_sets = false
```

They do give the same aggregate partition signature:

```text
state_count=33, scc_count=8, terminal_sizes=[1,1,6],
class_sizes=[1,1,1,6,6,6,6,6], boundary_count=22
```

Adjudication: L-only and R-only give the same count/size signature but different terminal cells. The mirror-law family-locality is basin-visible as a location split, not as a count split.

## Q4 - G2, G5, G4

PASS for the finite graph rows, with CAVEAT C2 on `G5` contrast wording and CAVEAT C3 on `G4` controls.

`G2` re-merges:

```text
G2 state_count=33
G2 scc_count=2
G2 terminal_class_count=1
G2 terminal_class_sizes=[1]
G2 may_basin_sizes=[33]
G2 must_basin_sizes=[1]
G2 fate=survives
```

`G5` composite split:

```text
G5 state_count=33
G5 scc_count=31
G5 terminal_class_count=5
G5 terminal_class_sizes=[1,1,1,1,3]
G5 terminal_cells=[[0],[5],[16],[27,28,30],[32]]
G5 may_basin_sizes=[1,1,9,9,13]
G5 must_basin_sizes=[1,1,9,9,13]
G5 fate=SPLITS
```

`G4` conditioned fate:

```text
G4 state_count=4
G4 scc_count=3
G4 terminal_class_count=1
G4 terminal_class_sizes=[2]
G4 terminal_cells=[[3,9]]
G4 may_basin_sizes=[4]
G4 must_basin_sizes=[2]
G4 fate=shrinks
```

The contract vocabulary is respected: may is existential reachability (`can_reach_terminal`), must is universal/sure containment (`sure_basin_omega_containment`). The source emits both sizes per row (`common.py:300-311`).

CAVEAT C2 - `G5` reversed-word contrast is not a partition split. The recomputed `G5` commutative-control row shows `diagonal_partition_changed=true` and `reversed_transition_hash_changed=true`, but `reversed_partition_changed=false`. The diagonal commutative-collapse contrast fires at the partition level; the reversed word changes the transition hash but keeps the same partition signature.

CAVEAT C3 - `G4` per-set controls do not fire. Fresh recomputation gives `G4 similarity_fired=false` and `G4 root_off_fired=false`. The packet-local validator checks only control presence for all rows, not that these two controls fire for `G4`. This does not falsify the conditioned fate row; it does falsify the stronger "controls per set each fire" reading.

## Q5 - Controls

PARTIAL PASS.

Fresh recomputation:

```text
G0:  similarity fired=true, root_off fired=true
G1:  similarity fired=true, root_off fired=true
G2:  similarity fired=true, root_off fired=true
G3L: similarity fired=true, root_off fired=true
G3R: similarity fired=true, root_off fired=true
G4:  similarity fired=false, root_off fired=false
G5:  similarity fired=true, root_off fired=true
```

`G5` commutative-collapse contrast:

```text
computed=true
word=[Ni_Pit_L, R_x]
reversed_word=[R_x, Ni_Pit_L]
reversed_partition_changed=false
reversed_transition_hash_changed=true
diagonal_partition_changed=true
```

Label permutation: I found no packet-emitted label-permutation control. As an audit-only check, I deterministically reversed cell labels and recomputed SCC/terminal counts from the graph edges. Counts and terminal-size multisets stayed invariant for `G0`, `G1`, `G2`, `G3L`, `G3R`, `G4`, and `G5`. This supports label-free partition counts, but it is not a packet-delivered control.

## Q6 - Standard/Envelope

PASS with caveats C4 and C5.

The generic helper-backed envelope validates:

```text
--require-pytorch --require-source-backed: ok true
--require-pytorch --strict-source-backed: ok true
```

The envelope records:

```text
schema_version=three_engine_sim_result_v1
engine_contract.lanes=[jax,julia,pytorch]
classification=scratch_diagnostic
promotion_allowed=false
formal_admission_allowed=false
seed_ledger={rng:none, deterministic_tie_break:cell_id_ascending}
```

Cross-engine agreement is exact at the sweep-signature level:

```text
jax    febc5d9e0a281d18f6656b445eef84b9085dd0bb48b45994b09303dd58850bde
julia  febc5d9e0a281d18f6656b445eef84b9085dd0bb48b45994b09303dd58850bde
pytorch febc5d9e0a281d18f6656b445eef84b9085dd0bb48b45994b09303dd58850bde
```

SMT recomputation:

```text
z3 identity = unsat
z3 erased_flip = sat
cvc5 identity = unsat
cvc5 erased_flip = sat
Julia Z3 stored identity = unsat
Julia Z3 stored erased_flip = sat
```

Real Julia leg: envelope records `packages_used=["Graphs","Z3","LinearAlgebra","JSON","Dates","SHA"]`; tool calls include `Graphs.SimpleDiGraph/Graphs.add_edge!/Graphs.strongly_connected_components` and `Z3.Solver/Z3.IntVar/Z3.add/Z3.check`.

The closeout wording scan found no disallowed placeholder labels in this audit verdict.

CAVEAT C4 - packet artifacts are worktree-only. `git ls-files --error-unmatch` fails for this packet's envelope because the packet directory is untracked. This audit covers current worktree artifacts, not committed durable evidence.

CAVEAT C5 - raw graph objects are not persisted in result JSON. The common builder constructs `graphs` (`common.py:483-504`), but the JAX result persists `summarize_sweep(sweep)`, `partition_fate_table`, controls, and proofs rather than full `transition_edges` / `communicating_classes` graph objects (`jax.py:121-125`). I recomputed raw graphs in-memory from source and parent inputs; I could not audit raw emitted graph artifacts because none are persisted.

## Q7 - Closure

Earned:

- `G0` byte-exact anchor to committed parent `631f1c3db`.
- `G1` first finite terminal-class split on the fixed 33-cell grid: three terminal closed communicating classes with absent exits for every rotation generator checked.
- `G3L/G3R` chirality splits: same count/size signature, different terminal cell sets.
- `G2` re-merge to the one-terminal-class baseline.
- `G5` composite split into five terminal classes.
- `G4` conditioned-shell shrink to four states with one terminal class.
- z3/cvc5/Julia Z3 terminal-count identity checks with erased flip.
- Three-engine envelope and source-backed validation at scratch scope.

Not earned:

- refined sub-basin geometry;
- invariant-circle/invariant-cell language beyond the fixed 33-cell graph;
- grid-refinement or rotated-grid robustness;
- a packet-emitted label-permutation control;
- "all controls fire for every set" because `G4` controls do not fire;
- the successor two-engine product;
- canonical/admitted/formal basin theorem status.

## Named Caveats

- C1 `G1_GRID_REFINEMENT_MISSING`: no grid-refinement or rotated-grid control; fixed 33-cell SCC split only.
- C2 `G5_REVERSED_WORD_PARTITION_UNCHANGED`: diagonal commutative collapse changes partition; reversed word changes hash but not partition signature.
- C3 `G4_CONTROLS_NOT_FIRED`: `G4` similarity/root-off controls are present but false.
- C4 `WORKTREE_ONLY_PACKET`: packet is untracked; verdict covers current worktree artifacts.
- C5 `RAW_GRAPH_ARTIFACTS_NOT_PERSISTED`: raw graphs were recomputed in-memory, not audited from durable emitted graph JSON.
- C6 `LABEL_PERMUTATION_NOT_PACKET_EMITTED`: audit-only relabel check passes; packet did not deliver this control.

## Final Verdict

GENUINE-WITH-CAVEATS.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. The accepted claim is: on the fixed 33-cell basin graph, changing the active generating set produces the first finite terminal-class sub-basin structure, including contraction-removal splits (`G1`), chirality-local terminal-cell splits (`G3L/G3R`), a full-set re-merge (`G2`), a conditioned shrink (`G4`), and a composite split (`G5`). No refined geometry, no grid-stable invariant-circle claim, no two-engine product, and no formal/canonical basin theorem is admitted.
