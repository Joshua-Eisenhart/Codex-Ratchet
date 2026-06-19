# Fresh audit verdict: basin_information_fusion_v1

Bottom line: `GENUINE-WITH-CAVEATS`.

`basin_information_fusion_v1` earns the v0 FAIL/HOLD gate for the scratch-diagnostic joint basin-information-flow object. It is not just v0 accounting with new labels: the packet constructs stepwise `R_C` orbit entropy trajectories, a packet-local G1 merge syndrome table, record recoverability regimes, terminal-class restricted throughput rows with absent-exit proofs, and basin-conditioned may/must flow rows under a declared probe family.

It does not earn a clean full-strength all-three independent backend claim. The JAX and PyTorch legs both build the full object through the shared Python common module; PyTorch-specific `torch.func`/`torch_geometric` and JAX-local `networkx` surfaces are source-backed but mostly probe/receipt surfaces rather than independent carriers of the full joint object. Julia independently checks only the G1 record-count slice. Ceiling remains `scratch_diagnostic`, `promotion_allowed=false`, `formal_admission_allowed=false`.

No staging occurred and no commit was run. During closure after this verdict was first written, a shell quoting mistake invoked `git add` with no path; Git returned "Nothing specified, nothing added," and `git status --short` still showed the packet untracked.

## Verdict

`VERDICT: GENUINE-WITH-CAVEATS`.

The v0 joint-object hold is now `EARNED` at scratch-diagnostic strength:

- `v0` was real partition-information accounting but held for missing per-class/orbit/record/basin-conditioned information-flow objects.
- `v1` supplies those missing object rows over the committed 33-cell substrate and G0-G5 generator rows.
- The decisive object is earned by the Python/JAX-common computation plus independent auditor recomputation from the parent sweep graph, not by the all-three envelope language alone.

Accepted citation:

`basin_information_fusion_v1` is a scratch-diagnostic joint basin-information-flow object over the committed finite 33-cell Bloch substrate and G0-G5 generator rows. It computes typed stepwise counting-entropy trajectories along actual generator-labelled `R_C` orbits, packet-local G1 chart-relative merge record retention, exact finite support throughput for terminal-class restricted channels, and basin-conditioned may/must flow under the declared one-step successor/reachable-size probe family.

Forbidden citation:

Do not cite it as invariant continuum basin geometry, formal admission, a canonical basin theorem, universal information scalar, bridge/axis/physics result, Z4 radiated-record construction, Shannon/Holevo channel capacity result, or a fully independent all-three-backend construction of the full joint object.

## Checks run

Read-only checks only; I did not run packet entrypoints that rewrite result JSON.

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 - <<'PY'
# imported validate_basin_information_fusion_v1.validate(payload), no validator-result rewrite
# result: {"ok": true, "errors": [], "mode": "imported_validator_no_write"}
PY
```

```bash
/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/basin_information_fusion_v1/results/basin_information_fusion_v1_envelope_results.json
# result: {"ok": true, "result_json": "system_v6/sims/basin_information_fusion_v1/results/basin_information_fusion_v1_envelope_results.json"}
```

Independent recomputation used `basin_generating_set_sweep_v0_common.build_sweep(...)` and compared against the v1 envelope without importing v1 helpers for the decisive rows.

## Adjudication

### 1. Entropy production along actual `R_C` orbits

PASS.

The orbit rows are per-step trajectories, not endpoint deltas relabeled. Each row has a generator schedule, step index, occupied cell count, occupied communicating-class count, typed counting entropy, and `after_minus_before`.

Independent recomputation of the full `G2` trajectory from the parent sweep graph matched the stored v1 envelope step-for-step:

- schedule: `Ne_Spiral_R`, `Ne_Vortex_L`, `Ni_Pit_L`, `Ni_Source_R`, `Se_Cannon_R`, `Se_Funnel_L`, `Si_Citadel_R`, `Si_Hill_L`, `D_x`, `D_z`, `R_x`, `R_z`;
- steps: `13`;
- all compared fields matched: generator applied, occupied cell count, occupied class count, cell/class deltas, and cell histogram hashes;
- first row: 33 occupied cells, 2 communicating classes, `log(33)` cell entropy;
- last row: 16 occupied cells, 2 communicating classes, `log(16)` cell entropy.

This satisfies the order-separate check: the sequence was recomputed in the declared generator order, and the shuffled-order control changes the production trajectory.

### 2. Record retention at the G1 merge

PASS with scope caveat `G1`.

The packet constructs a 33-row syndrome table with `start_cell`, `G1_chart_relative_class_id`, `post_merge_terminal_readout`, `constructed_full_syndrome_record`, `partial_record_control`, and `erased_record_control`. The record values are computed as readout label counts over that table.

Independent recomputation from the stored syndrome table:

- full record: 3 labels, `log(3) = 1.0986122886681098`, defect `0.0`;
- post-merge terminal readout only: 1 label, retained `0.0`, defect `log(3)`;
- erased record: 1 label, retained `0.0`, defect `log(3)`;
- partial record: 2 labels, retained `log(2) = 0.6931471805599453`, defect `0.4054651081081645`.

The scope limitation is honest: `caveat_q1_repaired_here_for_g1_merge_only` says this constructs the G1 merge syndrome object and does not construct a Z4 radiated-record object.

### 3. Per-class throughput

PASS with semantics caveat `G2`.

The packet emits 17 terminal-class throughput rows covering G0, G1, G2, G3L, G3R, G4, and G5. Rows carry absent-exit proofs and exact finite support counts.

Independent recomputation of a nontrivial G1 terminal class matched:

- terminal class: `G1_terminal_class_1`;
- input cells: `18`;
- restricted edge count: `72`;
- output support count: `18`;
- output throughput: `log(18) = 2.8903717578961645`;
- absent-exit proof: `no_exit=true`;
- chart label present: `G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE`.

The exactness label is honest for finite support-count throughput. It is not a Shannon capacity, Holevo capacity, or optimized channel capacity claim.

### 4. Basin-conditioned flow

PASS.

The packet declares the probe family as one-step successor communicating-class signatures plus reachable-set-size readout. It applies the probe family to must-basin versus may-only cells and reports either separation or an empty may-only side.

Stored row summary:

- total basin-conditioned rows: `17`;
- distinguishable nonempty rows: `7`;
- indistinguishable nonempty rows: `0`;
- no may-only side: `10`.

Example separated row: `G0_terminal_class_1_basin_conditioned_flow` has must count `1`, may-only count `32`, must probe signature count `1`, may-only probe signature count `3`, and `distinguishable_under_declared_probes=true`.

Example honest non-comparison row: `G1_terminal_class_0_basin_conditioned_flow` has may-only count `0` and is labeled `no_may_only_cells`, not forced into a fake indistinguishability claim.

### 5. Controls

PASS.

The controls are not byte-identical decorations:

- erased-record control flips retained record to `0.0` and defect to `log(3)`;
- partial-record control flips to an intermediate `log(2)` retained record and nonzero defect;
- shuffled-order control changes the production trajectory and final cell histogram;
- similarity-only control fails basin-conditioned rows under THE GUARD.

The shuffled-order control is especially important: original `Ni_Pit_L -> R_x` and shuffled `R_x -> Ni_Pit_L` both end at 25 occupied cells, but their stepwise trajectories differ. That is a real order test, not an endpoint-only decoration.

### 6. Chart relativity

PASS.

Every exposed G1-citing object subtree I scanned carries `G1_CHART_RELATIVE_ORIGINAL_33_CELL_FINITE_STRUCTURE`. The packet-local validator also enforces this for the orbit and record surfaces. My broader scan over `entropy_production_along_orbits`, `record_retention_at_g1_merge`, `per_class_throughput`, `basin_conditioned_flow`, `controls`, and `claim_sections` found `0` missing chart-label paths.

Future citations must keep the exact sense: G1 is finite chart-relative original-33-cell structure, persistent under declared 2x/3x containment refinements and changed by the pinned non-axis rotated chart. It is not invariant geometry.

### 7. Standard, SMT, validators, backend agreement

PASS for schema and validators; CAVEATED for backend independence and tool load-bearing strength.

Accepted:

- schema is `three_engine_sim_result_v1`;
- mode is `all_three_full_sims`;
- ceilings are exact: `scratch_diagnostic`, no promotion, no formal admission;
- envelope is built through `scripts/build_three_engine_envelope.py`;
- packet-local validator import returned `ok:true`;
- strict source-backed validator with `--require-pytorch --strict-source-backed --require-tool-intent` returned `ok:true`;
- z3/cvc5/Julia Z3 all bind computed syndrome/readout counts with UNSAT identity and SAT erased flip;
- no schema fork found.

Backend agreement scope:

- JAX and PyTorch full joint-object signatures are byte-identical because both call `build_joint_object(...)` from the shared Python common module with different matrix-exponential functions.
- Julia does not emit orbit trajectories, per-class throughput, or basin-conditioned flow; it independently constructs/checks the G1 record-count slice.
- `divergence.max_divergence = 0.0` is for computed G1 syndrome class count only, not full-object independent recomputation.

Tool honesty caveat:

- The strict source-backed validator passes, and the source contains the named APIs.
- But `networkx`, `torch.func`, and `torch_geometric` are not all load-bearing carriers for the full joint object in the strong sense implied by the envelope. `networkx`/`torch_geometric` appear mainly in source-backing probes or parent/common paths; PyTorch does not independently implement the full graph/orbit/throughput/flow object in native torch/PyG form.

This does not kill the joint object. It demotes the all-three/tool-strength reading.

## Named caveats

`G1_RECORD_SCOPE_G1_MERGE_ONLY`: The packet closes the v0 record-retention hold for the G1 merge syndrome object only. It does not construct a Z4 radiated-record object.

`G2_FINITE_SUPPORT_THROUGHPUT_NOT_CAPACITY`: Per-class throughput is exact finite support-count throughput on a pinned ensemble/readout. Do not cite it as Shannon capacity, Holevo capacity, optimized channel capacity, or general information capacity.

`G3_BACKEND_INDEPENDENCE_SCOPE`: The full joint object is shared-Python-common across JAX/PyTorch, while Julia independently checks only the G1 record-count slice. `max_divergence=0.0` is real for the declared metric but not proof of full-object independent recomputation.

`G4_TOOL_LOAD_BEARING_SCOPE`: Source-backed tool intent is validator-green, but some load-bearing package claims are stronger than the code path. Treat `torch.func`, `torch_geometric`, and local `networkx` as supportive/source-backed surfaces unless a later packet makes them carry the committed R_C graph object directly.

`G5_SMT_COUNT_BINDING_NOT_RAW_TABLE_FORMALIZATION`: SMT binds computed syndrome/readout label counts and the erased flip. It does not ingest or formalize the raw syndrome table, orbit trajectories, or per-class channels.

`G6_CHART_RELATIVE_ALWAYS`: Every G1 citation must carry the chart-relative original-33-cell label. This packet currently does; future summaries must not shorten it into invariant G1 basin geometry.

`G7_WORKTREE_PACKET`: At audit time the entire `system_v6/sims/basin_information_fusion_v1/` packet is untracked worktree state. That is fine for this requested audit, but future citation after commit should cite the committed hash, not this transient filesystem state.

## Future-citation rule

Allowed:

`basin_information_fusion_v1` closes the `basin_information_fusion_v0` FAIL/HOLD gate at scratch-diagnostic strength by constructing the finite joint basin-information-flow object v0 lacked: actual stepwise `R_C` orbit entropy trajectories, packet-local G1 merge record retention, terminal-class restricted finite support throughput, and basin-conditioned may/must flow over the committed 33-cell substrate.

Required suffix:

Ceiling remains `scratch_diagnostic`; G1 is chart-relative original-33-cell structure; record closure is G1-merge-only; throughput is finite support-count throughput; SMT is count-level; the all-three envelope is validator-green but full-object independence is limited by the shared Python common builder and Julia's record-slice-only check.

Forbidden:

Do not use this as a formal basin theorem, invariant continuum geometry, full native PyTorch/PyG graph construction, full independent Julia/JAX/PyTorch recomputation, Z4 radiated-record object, channel-capacity theorem, axis/bridge/physics claim, or promotion beyond scratch diagnostic.

## Super-sim v0 implication

For `system_v6/receipts/program_plan_factory_20260611.md`, this packet is now usable as the decisive prerequisite for the Family A super-sim v0 build, with the caveats above carried into the super-sim card.

Super-sim v0 may consume:

- stepwise orbit entropy trajectories over the 33-cell G0-G5 generator rows;
- the G1 chart-relative merge record table and full/partial/erased regimes;
- exact finite support-count terminal-class throughput rows;
- basin-conditioned may/must flow rows and THE GUARD control.

Super-sim v0 must not consume:

- invariant G1 geometry;
- Z4 record-object closure from this packet;
- full backend-independence language;
- Shannon/Holevo capacity language;
- promoted/canonical status.
