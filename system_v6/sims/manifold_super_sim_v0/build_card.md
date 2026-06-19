# BUILD CARD - manifold_super_sim_v0 (the first integrated constraint-manifold run, Family A)

You are codex1 (builder, xhigh). Repo: /Users/joshuaeisenhart/Codex-Ratchet. Build EVERYTHING inside the new dir system_v6/sims/manifold_super_sim_v0/ (file-disjoint). NO git add/commit. Copy this card into the packet as build_card.md.

## What this is
The first integration test of the constraint manifold as ONE running object - per the committed preassembly map in system_v6/receipts/program_plan_factory_20260611.md (READ IT FIRST, especially the weld anchors, the citation discipline, and the Family A/B split). NOT a script that juxtaposes old JSONs: every layer recomputes against one shared finite object, and the anti-cherry-picking core is that raw transition graphs are persisted nowhere - you MUST rebuild them from pinned sources.

## Read (the consume set - read each packet's audit_verdict.md for its BINDING caveats)
geo_s5_terrain_flows_v0 + geo_s4_operator_stage_v0 (the pinned A,b / M,c sources BY HASH), basin_rc_transition_graph_v0, basin_generating_set_sweep_v0, basin_grid_refinement_control_v0, manifold_information_throughput_v0 (+ z4_syndrome_record_v0, its record-side co-citation), basin_information_fusion_v1 (the joint-object pattern you re-instantiate), manifold_unified_run_v0 (the integration MECHANISM: single state_object_id, persisted sha-verified trajectory artifact, per-step recomputation classification step-dependent vs carried, typed consistency matrix), manifold_entropy_ledger_v0 (typed entropy: NO cross-type sums without an explicit convention).

## The shared object
The 33-cell admitted Bloch grid (5-point axis grid, Adm_C = x^2+y^2+z^2 <= 1) with the pinned S4/S5 generators rebuilt from the geo_s4/geo_s5 exact matrices (consume by hash; recompute exp(hA) at h=1/2 yourself). ONE state_object_id; ONE persisted, sha-verified run trajectory.

## The layers (each recomputed against the shared object, each with a row that CHANGES when its input changes - a layer without such a row is decorative and the packet must FAIL itself)
L1 BASIN: per-generator-set (G0-G5) transition graphs rebuilt from pinned generators; SCC partition, terminal classes w/ absent-exit proofs, may/must split.
L2 CHART: the 2x and 3x refinements + the pinned non-axis rotated chart as LIVE in-run controls (density persistence + the 3->2 rotated merge recomputed, not cited).
L3 INFORMATION: the pinned six-state ensemble evolved under the SAME generator words; Holevo/killed rows for the active channels; the committed 8-stage word curve.
L4 FUSION: stepwise typed entropy trajectories along actual R_C orbits; the G1 merge record (constructed syndrome table, recoverable bits computed); terminal-class-restricted throughput; basin-conditioned may/must flow. (Re-instantiate the fusion_v1 computation on the integrated run - consume its pattern, recompute its rows.)
L5 LEDGER: the typed consistency matrix across all rows (every entropy/information row carries its type tag; any cross-type account states its convention).

## WELD ANCHORS (recompute and match EXACTLY; each is a can-fail control - any mismatch = the run FAILS with the mismatch reported, never patched)
- G0 transition_graph_sha256 must match the committed bd0cd3b5... (read the exact value from the rc-graph envelope)
- G1 partition [1,14,18] with may=must
- rotated-chart merge 3->2 (and 2x/3x persistence at 3)
- D_z six-state Holevo 0.411341122022618 and killed 0.28180605853732726
- stage-word curve endpoint 0.0932927444282512
- fusion regimes: G1-merge record erased->0 / partial->ln2; conservation-row co-citation w/ the z4 packet's state-plus-record convention
- every SMT row: negated identity UNSAT + erased/perturbed SAT flip (computed values, never literals)

## KILL CONTROLS (the super-sim's own honesty tests; all must fire)
- STALE-IMPORT control: perturb one pinned generator entry by epsilon -> the dependent anchors MUST mismatch (proves rows are recomputed, not imported). Restore and rerun clean.
- DECORATIVE-LAYER detector: for each layer, the named input perturbation whose effect must appear in that layer's rows.
- order-shuffled (N01): permute a generator word -> trajectory rows change.
- root-off / similarity-only: a clustering without dynamics must fail L1's partition gates (THE GUARD).
- quotient-erased: drop the probe quotient -> the may/must distinction must degrade as computed.

## Citation discipline (binding, from the plan receipt): all basin classes CHART-RELATIVE (forbidden: invariant/frame-independent sub-basins); basin-map citations name may vs must; typed entropy everywhere; record-side language co-cites z4_syndrome_record_v0; NO joint-engine/two-engine rows in v0 (that object is gated on the convention sweep); no axis/bridge/physics claims.

## Engineering contract
Three engines (Julia reference w/ real aligned packages + package_observables - Graphs.jl for the graph rebuilds at minimum; JAX workhorse; PyTorch first-class on the graph machinery), TOOL_INTENT_MATRIX in build_card.md, envelope ONLY via scripts/build_three_engine_envelope.py, validate --require-pytorch --strict-source-backed --require-tool-intent ok:true, classification scratch_diagnostic, promotion_allowed=false, formal_admission_allowed=false, positive+negative+boundary sections. The run must also FAIL HONESTLY: if any anchor mismatches or any layer is decorative, all_pass=false with the named failure - do not soften gates to go green. End by listing every validator command + ok status.

## TOOL_INTENT_MATRIX

| engine | tool | role | load-bearing gate | positive case | negative/erased control | boundary case | demotion condition |
|---|---|---|---|---|---|---|---|
| julia | Graphs | Rebuild finite directed graphs from the shared 33-cell object and generator labels. | L1 BASIN partition, terminal classes, absent-exit proofs. | G0 hash and G1 [1,14,18] partition match recomputation. | root-off/similarity-only guard fails basin language. | G4 conditioned carrier is tracked as a narrowed chart, not the shared object. | Demote if graph rows are imported from parent JSON instead of rebuilt from pinned generators. |
| julia | Z3 | Solver mirror for computed count/fate identity rows. | SMT rows require UNSAT identity and SAT erased flip. | Computed anchors equal expected constants in solver variables. | Erased/perturbed expected value flips SAT. | Single-terminal and multi-terminal rows both encoded. | Demote if solver asserts literal booleans instead of binding computed values. |
| jax | jax/jax.numpy | Workhorse finite-array reconstruction of shared cells, affine generator action, and trajectory summaries. | State object id, trajectory artifact, L1-L5 recomputation hashes. | Same object id and anchors as envelope. | stale-generator epsilon perturbation changes dependent anchors. | x64 enabled; NumPy/SciPy support is control/helper only, not claim-path tool. | Demote if JAX reads peer result JSON or skips recomputation. |
| jax | networkx | Workhorse graph/SCC rebuilds and orbit traversals. | L1 graph partitions, L4 orbit trajectories and basin-conditioned flow. | G0/G1/G2/G5 rows match expected recomputed signatures. | order-shuffled trajectory differs. | Raw transition edges are not persisted in the super-sim envelope. | Demote if raw parent graph JSON is copied. |
| jax | sympy | Exact typed entropy and symbolic count labels. | L3 information rows and L5 typed consistency matrix. | D_z Holevo/killed and stage endpoint match exact natural-log conventions. | wrong-type/cross-type sum flagged unless convention present. | Typed rows may coexist only with explicit product convention. | Demote if entropy types are summed silently. |
| jax | z3/cvc5 | Crossover SMT over measured finite values. | Negated identity UNSAT + erased/perturbed SAT flip. | All computed anchor identities hold. | Erased or perturbed values flip SAT. | Coefficient/count level only; no formal admission. | Demote if computed values are not bound in solver variables. |
| pytorch | torch | Tensor mirror of shared cells/generator action and finite row summaries. | PyTorch lane agreement and graph machinery surface. | Tensor-derived anchor vector matches common recompute. | stale-generator epsilon changes tensor-derived hash. | PyTorch is first-class support, not Julia semantic arbiter. | Demote if torch only reports imported scalar constants. |
| pytorch | torch_geometric | Graph machinery carrier for finite transition edge_index/terminal summaries. | PyTorch graph row in all-three envelope. | edge_index-derived SCC/checksum agrees with common summary. | similarity-only/root-off guard does not satisfy basin gates. | Raw edge lists stay lane-local and are summarized by hashes/counts. | Demote if PyG is imported but not used in a gate. |
| pytorch | torch.func | Batched generator-word/orbit checks. | Order-shuffled and stale-generator controls. | Original vs shuffled word trajectories differ. | Shuffled N01 trajectory changes. | Function batching is finite diagnostic only. | Demote if batched outputs are unused in controls. |
| pytorch | sympy/z3/cvc5 | Torch-derived count proof checks. | SMT flip and typed exact labels. | Torch-derived counts bind to UNSAT identity. | Erased/perturbed values flip SAT. | Count-level proof only. | Demote if literals replace derived torch counts. |

## Round 1 hardening note - G1/G2 only

Scope: fixed audit caveats `G1_SOURCE_HASH_LOCKS_ARE_WRONG_SURFACE` and `G2_G1_CHART_LABELS_DROPPED_IN_REDUCED_ROWS`; no G3-G7 work was attempted.

Changes:
- `source_locks()` now locks only actual consumed inputs from `PARENT_RESULTS`, so `parent_hash_pins`, `stability_pairs`, and the S4/S5 portion of `state_object_id` bind consumed result JSON/receipt paths instead of parent `audit_verdict.md` files.
- Parent audit verdict hashes are still retained, but only under separate citation-context keys: `parent_lineage.audit_verdict_citation_context` and `source_import_audit.audit_verdict_citation_context_hashes`.
- Reduced L4 G1 rows in `terminal_class_restricted_throughput` and `basin_conditioned_may_must_flow` now carry `chart_relative_label` and `chart_relative_note`.

Fresh rerun and validation statuses:
- `julia system_v6/sims/manifold_super_sim_v0/manifold_super_sim_v0_julia.jl` -> ok:true.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v0/manifold_super_sim_v0_jax.py` -> ok:true.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v0/manifold_super_sim_v0_pytorch.py` -> ok:true.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v0/write_envelope_spec.py` -> ok:true.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/build_three_engine_envelope.py system_v6/sims/manifold_super_sim_v0/manifold_super_sim_v0_envelope_spec.json > system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json` -> exit 0.
- Anchor check -> G0 `bd0cd3b551bbb3f323eb596695da8d91429f010780c1c137af4a253bd73438f0`, G1 `[1, 14, 18]`, rotated chart `2`, D_z Holevo `0.411341122022618`, stage endpoint `0.0932927444282512`.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/manifold_super_sim_v0/validate_manifold_super_sim_v0.py` -> ok:true, errors:[].
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/manifold_super_sim_v0/results/manifold_super_sim_v0_envelope_results.json` -> ok:true.
- `/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q system_v6/sims/manifold_super_sim_v0/tests` -> 6 passed, 11 subtests passed.
