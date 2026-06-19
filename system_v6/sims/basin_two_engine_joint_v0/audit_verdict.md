# Fresh Audit Verdict - basin_two_engine_joint_v0

Auditor: codex2 cross-backend audit.
Scope: read-only audit of codex1 builder packet, except this verdict file.
Standard: calibrated audit bar, basin contract `000f48e71`, amended pre-registration `0bed51ac2`, and the k=5 order-echo lesson.

## Bottom Line

VERDICT: BY_CONSTRUCTION for the registered 64-subsubbasin claim.

The packet genuinely computes the coarser finite transition rows:

- `both`: one terminal closed communicating class of size 64.
- `synchronous`: eight terminal closed communicating classes of size 8.
- `l_only`: eight terminal closed communicating classes of size 8.
- `r_only`: eight terminal closed communicating classes of size 8.

Those middle `8/8` rows are real multi-state SCCs with absent-exit proofs. The decisive failure is the last step: the claimed 64 subsubbasins are all singleton intersections of the L-only and R-only partitions on a 64-state carrier. Under every actual generator row, every singleton has an outgoing transition. The packet does not supply a subsubbasin-level transition system whose terminal closed classes are those 64 singletons. If the generating set is `both`, the dynamics merges everything into one 64-state SCC; if the generating set is empty, the singleton partition is vacuous state identity.

Count adjudication: 64 is observed as an artifact-level count, not earned as a basin count.

Product adjudication: the owner-stated `2 engines x 2 loops x 4 stages x 4 substages` product is not computed. The packet realizes only `8 x 8` joint stage coordinates, and even that is realized as singleton state identity after intersecting row/column cycle partitions. Product structure is therefore not confirmed; at most the pre-registration gets count-only partial evidence.

Ceiling: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`. No bridge, axis, admitted basin, or canonical product claim is earned.

## Commands And Checks Run

- Read build card, common source, JAX/PyTorch/Julia legs, envelope builder, local validator, result JSON, amended pre-registration, basin contract, and prior generating-set audit.
- Recomputed graph rows in-memory from `basin_two_engine_joint_v0_common.py` with `PYTHONDONTWRITEBYTECODE=1` and the Makefile sim-stack Python.
- Recomputed singleton escape under `l_only`, `r_only`, `synchronous`, and `both`.
- Re-ran the decode audit against actual component ids instead of accepting the packet's hardcoded decode result.
- Ran generic validator twice:
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --require-source-backed system_v6/sims/basin_two_engine_joint_v0/results/basin_two_engine_joint_v0_envelope_results.json`
  - `scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed system_v6/sims/basin_two_engine_joint_v0/results/basin_two_engine_joint_v0_envelope_results.json`
- Scanned for forbidden wording: `fixture|toy|mock|dummy`.
- Checked git state: packet directory remains untracked; no `git add` or `git commit` was run.

Both generic validator commands returned `{"ok": true, "result_json": "system_v6/sims/basin_two_engine_joint_v0/results/basin_two_engine_joint_v0_envelope_results.json"}`. This is a validator pass for the packet's declared gates, not an acceptance of the amended pre-registration standard.

## Source Anchors

- The amended registration says the primary product is specifically `64 = 2 engines x 2 loops x 4 stages x 4 substages`, and that 64 without the product structure is only partial confirmation: `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:11-21`.
- The registration also names the falsifier: 64 appearing only through an order-echo or label artifact fails the claim: `system_v6/receipts/owner_prediction_64_subsubbasins_20260611.md:34-36`.
- The basin contract requires finite `S`, explicit `R_C`, terminal/closed classes, may/must semantics, trapping or absent-exit evidence, and recomputation of invariant cores rather than name-only intersection: `system_v6/receipts/attractor_basin_criterion_20260611.md:175-190` and `system_v6/receipts/attractor_basin_criterion_20260611.md:220-232`.
- The build card itself asks for subsubbasins as intersection refinement of marginal restricted partitions, but still requires may/must, absent-exit proofs, and Morse ordering at every level: `system_v6/sims/basin_two_engine_joint_v0/build_card.md:27-33`.
- The source builds actual graph rows with deltas `(1,1)`, `(1,0)`, `(0,1)`, and their union: `system_v6/sims/basin_two_engine_joint_v0/basin_two_engine_joint_v0_common.py:151-188`.
- The source computes SCCs, terminal closure, absent exits, may/must rows, and Morse rows for graph rows: `system_v6/sims/basin_two_engine_joint_v0/basin_two_engine_joint_v0_common.py:191-321`.
- The source computes the 64 subsubbasin layer by grouping `(l_comp[cid], r_comp[cid])`, not by constructing a new transition graph: `system_v6/sims/basin_two_engine_joint_v0/basin_two_engine_joint_v0_common.py:324-364`.
- The source adjudicates the factorization as `8x8_joint_stage_configuration` and explicitly says no independent four-substage quotient is computed: `system_v6/sims/basin_two_engine_joint_v0/basin_two_engine_joint_v0_common.py:618-633`.

## R1 - Triviality / Singleton Layer

Result: FAIL for the 64 subsubbasin claim. PASS for the coarser middle SCC rows.

Fresh recomputation of the actual transition rows:

```text
row           generators                 state_count  edge_count  SCCs  terminal classes  terminal sizes
both          L_only,R_only,sync_LR       64           192         1     1                 [64]
synchronous   sync_LR                     64           64          8     8                 [8,8,8,8,8,8,8,8]
l_only        L_only                      64           64          8     8                 [8,8,8,8,8,8,8,8]
r_only        R_only                      64           64          8     8                 [8,8,8,8,8,8,8,8]
l_then_r      L_then_R                    64           64          8     8                 [8,8,8,8,8,8,8,8]
r_then_l      R_then_L                    64           64          8     8                 [8,8,8,8,8,8,8,8]
```

The middle level is not singleton-by-construction. `synchronous`, `l_only`, and `r_only` are genuine cycle dynamics. Each has eight SCCs of size 8, all terminal under its own restricted generator, with absent-exit proofs of `checked_edge_count=8`, `outgoing_edge_count=0`, `no_exit=true` for every terminal class.

The 64 layer is different. The source defines it as:

```text
intersection refinement of L-only and R-only restricted terminal partitions,
with synchronous orbit class retained only as a consistency component
```

The resulting 64 classes have class-size multiset `[1] * 64`; the first classes are `[0]`, `[8]`, `[16]`, `[24]`, `[32]`, and so on. That is exactly the singleton identity partition of the 8-by-8 state grid.

Transition check at the singleton layer:

```text
actual row     singleton classes with at least one outgoing edge
l_only         64 / 64
r_only         64 / 64
synchronous    64 / 64
both           64 / 64
```

Sample from cell `0`:

```text
l_only:       0 -> 8
r_only:       0 -> 1
synchronous:  0 -> 9
both:         0 -> 8, 0 -> 1, 0 -> 9
```

Therefore the 64 singleton classes are not terminal closed communicating classes under any actual packet transition row. They have no absent-exit proof as subsubbasins. The only way to make them closed is to use no generator, which is a vacuous discrete partition, not a basin result.

Adjudication against R1:

- The chain `1 -> 8/8 -> 64` exists as set refinement.
- The chain is not fully dynamical. The `1` and `8/8` levels are SCC partitions under explicit dynamics; the `64` level is an intersection of two incompatible marginal SCC partitions.
- Coarser dynamics genuinely merges states: `both` is one SCC of size 64.
- The 64 refinement is not a terminal or trapping layer under the joint dynamics. It is state identity recovered by crossing row and column cycle labels.

## R2 - Product Structure

Result: owner-stated product NOT CONFIRMED. Packet realizes only `8 x 8` stage-coordinate structure.

The amended registration's primary candidate is:

```text
2 engines x 2 loops x 4 stages x 4 substages
```

The packet's own adjudication says:

```text
realized_factorization = 8x8_joint_stage_configuration
16x4 status = not_realized_by_primary_partition
64_matrix status = cardinality_compatible_not_structure_identified
```

It does not compute four factor sets of sizes `2`, `2`, `4`, and `4`. It does not provide quotient/projection maps from the class set onto those four factors. It does not provide product reconstruction from those four projections. It does not identify a separate substage factor.

The realized factorization is:

```text
L-only terminal class x R-only terminal class = 8 x 8
```

Because the 64 classes are singleton intersections, this is equivalent to the original `L_stage_8 x R_stage_8` carrier. It is not the owner-stated `2 x 2 x 4 x 4` product lattice.

Adjudication against R2:

- Count 64: observed.
- Owner product: not computed.
- Product reconstruction exact for `2 x 2 x 4 x 4`: absent.
- Realized factorization: `8 x 8_joint_stage_configuration`, with singleton identity caveat.
- Registration status: partial/count-only evidence, not product confirmation.

## Q3 - Signature / Label-Free / Order-Blind

Result: FAIL as packet-delivered. The source-level decode test is hardcoded, and a fresh decode recovers slot coordinates from component ids.

The packet's `decode_test()` simply returns:

```text
passed = true
stage_label_recovered = false
stage_order_recovered = false
```

It does not attempt a decoder. It does not consume the emitted signature rows. It does not test whether deterministic component ids recover slots.

Fresh decode audit:

```text
slot_recovery_from_component_ids = true
```

Examples:

```text
cell 0:  actual (l_slot=0, r_slot=0), signature (l=0, r=0, sync=0), recovered (0,0)
cell 1:  actual (l_slot=0, r_slot=1), signature (l=1, r=0, sync=1), recovered (0,1)
cell 8:  actual (l_slot=1, r_slot=0), signature (l=0, r=1, sync=7), recovered (1,0)
cell 9:  actual (l_slot=1, r_slot=1), signature (l=1, r=1, sync=0), recovered (1,1)
cell 63: actual (l_slot=7, r_slot=7), signature (l=7, r=7, sync=0), recovered (7,7)
```

Because the payload also includes `l_word` and `r_word`, recovered slots recover the stage order and stage labels in the emitted artifact. That is the k=5 order-echo risk in this packet.

Label permutation control:

The source does not recompute graph partitions under a permuted label action. It maps each `(l_slot, r_slot)` through two bijections and counts unique pairs:

```text
l -> (3*l + 1) mod 8
r -> (5*r + 2) mod 8
permuted_subsubbasin_count = len(unique permuted pairs) = 64
```

That is a bijection-cardinality check, not a genuine graph or signature-control rerun. It does not test whether order information disappears from the emitted signature.

Adjudication against Q3:

- No forbidden component key names are present in the narrow `signature` dict.
- The emitted component ids still recover stage slots under deterministic SCC sorting.
- Stage labels/order are recoverable from recovered slots plus the packet's own `l_word`/`r_word`.
- Label permutation invariant count is real as arithmetic but not meaningful as a label-free basin control.

## Q4 - Marginals / Chirality / Interleaving / N01

Result: PARTIAL.

The packet's L-only and R-only marginal rows compute eight terminal classes each:

```text
l_only: terminal_count=8, terminal_sizes=[8,8,8,8,8,8,8,8]
r_only: terminal_count=8, terminal_sizes=[8,8,8,8,8,8,8,8]
```

Those are valid cycle partitions of the 8-by-8 stage-word carrier. They are not the same object as the committed `ba1bfc4d1` chirality subset sweep. The committed sweep reported:

```text
G3L: state_count=33, scc_count=8, terminal_class_count=3, terminal_class_sizes=[1,1,6]
G3R: state_count=33, scc_count=8, terminal_class_count=3, terminal_class_sizes=[1,1,6]
```

So the packet's `8` marginal counts are not a direct consistency match to the committed chirality splits. The only safe comparison is weaker: both families show L/R-restricted structure, but on different carriers and with different terminal counts.

Interleaving semantics are pinned as separate rows:

```text
synchronous: advance L and R together
asynchronous: L-only or R-only as separate generator-labelled moves
both: union of synchronous and asynchronous moves
```

N01 row:

```text
state_partition_moves = false
trace_order_moves = true
state_result = independent stage advances commute on the finite state pair
trace_result = emitted generator trace distinguishes L-then-R from R-then-L even when endpoint state agrees
```

This is an honest negative state-level N01 result, not a noncommuting state partition. The trace-order row is weaker than a basin-structure order gap because it does not move the endpoint partition.

## Q5 - Contract / Envelope / Tooling / Controls

Result: mixed.

Passes:

- Classification and ceilings are correct: `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.
- Generic helper-backed envelope validates in both source-backed and strict-source-backed modes.
- Parent lineage includes the pre-registration, basin contract, parent transition graph envelope, two-engine readout automaton, Matrix64 envelope, mirror-law audit, and build card.
- JAX/Python leg uses `networkx`, `sympy`, `z3`, `cvc5`; PyTorch leg uses `torch.func`, `torch_geometric`, `sympy`, `z3`, `cvc5`; Julia leg uses real `Graphs` and `Z3`.
- Engine counts agree: Julia, JAX, and PyTorch each report subsubbasin count 64 and terminal counts `{both:1, synchronous:8, l_only:8, r_only:8}`.
- SMT erased flips fire: z3/cvc5/Julia Z3 all report real identity `unsat` and erased marginal flip `sat`.
- Capability receipt counts and tool-call counts are present: JAX 3/3, Julia 2/2, PyTorch 3/3.
- No `fixture`, `toy`, `mock`, or `dummy` wording was found under the packet path.
- Seed ledger records deterministic/no-randomness state.

Failures or caveats:

- Q5-C1: the local validator encodes the contested singleton criterion as a pass condition. It explicitly requires `subsubbasin_count == 64` and `class_size_multiset == [1] * 64`; it never asks whether those singletons are terminal under a subsubbasin transition relation.
- Q5-C2: may/must rows and absent-exit proofs exist for graph rows only. They do not exist for the 64 singleton subsubbasin layer.
- Q5-C3: root-off has weak teeth here. It changes the carrier from 64 to 81 states and gets one SCC either way. This proves the carrier size changed, not that the root constraint controls the claimed basin structure.
- Q5-C4: similarity contrast fires for readout-label clusters, but it is unrelated to the decisive singleton-product failure.
- Q5-C5: the packet directory is worktree-only and untracked at audit time. This audit covers the current filesystem artifact, not a committed durable packet.
- Q5-C6: envelope `child_agent_receipts` are self-reported agent ids without independent receipt paths in the result. They were not used as evidence for this verdict.

## Q6 - Verdict Against The Registration

Registration terms:

```text
64 = 2 engines x 2 loops x 4 stages x 4 substages
```

Adjudication:

- Count: observed as 64 singleton classes on a 64-state carrier.
- Basin count: not earned. The singleton classes are not terminal closed classes under `l_only`, `r_only`, `synchronous`, or `both`; every singleton has an outgoing transition.
- Product structure: not confirmed. The packet realizes `8 x 8_joint_stage_configuration`, not the registered `2 x 2 x 4 x 4` product.
- Which factorization is realized: `8 x 8`, specifically `L-only terminal class x R-only terminal class`, equivalent to row/column coordinates of the original state grid.
- 64-matrix candidate: only cardinality-compatible; no source-backed basin-transition equivalence relation connects Matrix64 rows to these classes.
- 16 x 4 candidate: not realized by the primary partition.
- Falsifier status: the "64 via artifact" falsifier survives. This is a 64-count artifact from intersecting two marginal cycle partitions, with order/slot recovery present in emitted component ids.

Final status:

```text
count_result = partial_count_only_observed
product_result = not_confirmed
registered_product = not_realized
realized_factorization = 8x8_joint_stage_configuration_with_singleton_identity_caveat
verdict = BY_CONSTRUCTION for the 64 subsubbasin claim
coarser_rows = GENUINE-WITH-CAVEATS at scratch_diagnostic ceiling
```

## Named Caveats

C1 - Singleton identity partition.
The 64 classes equal `|S|` and are all singletons. Under every actual transition row, all 64 singleton classes have outgoing edges. They are not terminal closed communicating classes.

C2 - Intersection is not a new dynamical operation.
The step from `8/8` to `64` is an intersection of L-only and R-only terminal partitions. The packet does not construct a restricted/conditioned `R_C` whose SCCs are the 64 classes.

C3 - Owner product absent.
No computed projections realize factor sets of sizes `2`, `2`, `4`, and `4`; no reconstruction check proves the registered product.

C4 - Decode control is asserted, not tested.
Fresh audit shows deterministic component ids recover `(l_slot, r_slot)`; with `l_word`/`r_word`, stage order and labels are recoverable from the packet artifact.

C5 - Label permutation control is cardinality-only.
It counts unique permuted coordinate pairs. It does not rerun the graph partition or prove order-blind signature invariance.

C6 - Marginal comparison to `ba1bfc4d1` is not direct.
The committed chirality sweep's `G3L/G3R` terminal count is 3 on the 33-cell carrier; this packet's L/R marginal count is 8 on the 8-by-8 stage-word carrier.

C7 - N01 is trace-only here.
The packet records `state_partition_moves=false`; only trace order differs. That is not a state-level noncommutation basin split.

C8 - Worktree-only packet.
The packet is untracked at audit time. It is auditable as current worktree evidence only.

## Ceiling Restated

This packet may be cited for:

- a real finite `both/synchronous/l_only/r_only` graph computation on the 64-state joint stage carrier;
- coarser middle-level cycle partitions of size `8 x 8`;
- cross-engine agreement that the packet's implemented arithmetic returns 64;
- a negative audit lesson: count 64 can appear as singleton identity without earning the registered product basin.

This packet must not be cited for:

- confirmed 64 subsubbasins under the basin contract;
- the owner-stated `2 x 2 x 4 x 4` product structure;
- an order-blind or label-free earned signature;
- Matrix64 correspondence;
- canonical, admitted, or promoted basin/product evidence.

No `git add` or `git commit` was run.
