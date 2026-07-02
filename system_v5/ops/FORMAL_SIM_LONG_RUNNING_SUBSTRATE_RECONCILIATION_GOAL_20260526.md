# Formal Sim Long-Running Substrate Reconciliation Goal - 2026-05-26

This is the full Codex TUI goal. Use it before any full layer/G-structure
matrix execution. The compact launcher in
`FORMAL_SIM_SUBSTRATE_BOOTSTRAP_GOAL_20260526.md` should point here.

## Copy-Paste Launcher

```text
You are in /Users/joshuaeisenhart/Desktop/Codex Ratchet.

Run the long-running formal substrate reconciliation goal in system_v5/ops/FORMAL_SIM_LONG_RUNNING_SUBSTRATE_RECONCILIATION_GOAL_20260526.md.

Do not summarize it and stop. Execute it. Use Wizard v4.2 Max Assembly with high parallelism where possible; if Wizard blocks, continue the maximum honest subset and label route truth. The job is not finished when one row passes, one row blocks, or downstream remains blocked. Continue row-by-row until the substrate reconciliation program reaches a terminal state or write a continuation_required artifact with the exact next row.
```

## Why This Goal Exists

The previous formal lane kept grinding on narrow Phase 2 carrier rows and
stopping after local success. That did not solve the real issue. The real issue
is substrate truth:

- `system_v5/legos/` contains real torch/tool lego artifacts.
- `system_v5/docs/MIGRATION_REGISTRY.md` still says 28/28 migration families are
  `NOT_STARTED`.
- `system_v5/docs/TOOL_LEGO_INTEGRATION_MATRIX.md` has empty or weak tool cells.
- A full manifold/layer/G-structure matrix cannot be the controlling launch
  surface until these mismatches are reconciled, repaired, or explicitly
  blocked.

The work is therefore not "build the final manifold." The work is "make the
legos real enough, receipt-bound enough, and ledger-reconciled enough that the
layer matrix can later be populated honestly."

This is a long-running goal. It should not end at substrate reconciliation if
the substrate rows become usable. It should continue into the next tranche that
the evidence unlocks.

## Authority And Read Gate

Before planning, claims, edits, or status reports, read:

1. `AGENTS.md`
2. `CODEX.md`
3. `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
4. `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
5. `system_v5/docs/LEGO_SIM_CONTRACT.md`
6. `system_v5/docs/MIGRATION_REGISTRY.md`
7. `system_v5/docs/TOOL_LEGO_INTEGRATION_MATRIX.md`
8. `system_v5/docs/FORMAL_SCOUT_READINESS_INDEX.md`
9. `system_v5/legos/README.md`
10. every `system_v5/legos/results/*.json`
11. `system_v5/ops/FORMAL_SIM_LAYER_VARIANT_CONSTRAINT_ALIGNMENT_SPEC_20260526.md`

If this read gate is incomplete, say the run is partial and do not make broad
repo, manifold, layer, flux, Axis0, or formal-lane claims.

## Non-Negotiable Corrections

1. The substrate is not empty. Existing `system_v5/legos/` artifacts must be
   reconciled before rebuilding them from scratch.
2. The substrate is not admitted. Existing artifacts default to
   `blocked_pending_admission` until strict checks pass.
3. A reconciliation artifact is preflight, not completion.
4. A passing row is progress, not completion.
5. A blocked row is an expected row result, not a reason to stop the whole goal.
6. Downstream consumers remaining blocked is expected and is not a stop reason.
7. Full matrix adoption, stacking order, terrain/operator composition, flux,
   Xi/Phi0, Axis0, physics, or final manifold claims are forbidden from this
   goal.
8. Wizard improves execution. It does not replace sim/proof/tool work.

## Route And Parallelism

Run Wizard v4.2 Max Assembly if available. Use high parallelism:

- Codex-native parents for independent source/result slices.
- External model/tool children only where they can produce bounded receipts.
- Separate worker lanes for result audit, source audit, rerun/validator,
  ablation analysis, registry delta, and tool-matrix delta.
- Keep Git/index mutation and shared ledger edits serial in the controller.

If full Wizard blocks, do not fake it. Record `PARTIAL` or `BLOCKED`, then keep
working through the maximum honest subset. A blocked Wizard is not a blocked
substrate program.

## Full Tooling Requirement

Every row must decide tool relevance explicitly. The row should not merely name
or import tools. A tool is load-bearing only when removing it collapses,
weakens, or makes unprovable the exact finite map or invariant under test.

Required tool inventory:

| Tool | Required role |
| --- | --- |
| PyTorch/autograd | Claim-bearing complex tensors, density matrices, spinors, channels, PEPS3D local tensors, entropy spectra, differentiable parameter sweeps. |
| PyG | Graph-carried tensor/message passing, local PEPS3D cell adjacency, schedule graph operations. Must not be a decorative wrapper over a simple loop. |
| z3 | Finite constraint satisfiability, impossibility, distinctness, and control blockers. |
| cvc5 | Independent SMT cross-check for z3-style structural claims, or explicit blocker if not applicable. |
| SymPy | Exact small symbolic identities, spectra, commutators, entropy formulas, and closed-form blockers. |
| Clifford / geometric algebra | Spinor, rotor, chirality, Clifford module, Weyl, quaternion-adjacent action claims. |
| geomstats | Metric, geodesic, shell, or manifold-statistics checks where a real finite metric object exists. |
| e3nn | Equivariant tensor checks where O(3)/SO(3)/SU(2)/E(3)-style symmetry is the claim. |
| rustworkx | Finite graph paths, cuts, order witnesses, graph isomorphism controls, dependency routing. |
| XGI | Hypergraph and multi-way interaction structure, including cell or coalition supports. |
| TopoNetX | Simplicial/cell incidence and boundary maps for V/E/F/C carrier structure. |
| GUDHI | Persistent homology and finite filtration readouts. |
| opt_einsum | Tensor contraction support where contraction path affects feasibility or result. |

For each tool, record one of:

- `load_bearing` with `ablation_outcome_delta`;
- `supportive` with reason;
- `not_applicable_with_reason`;
- `blocked_missing_tool_or_api`.

Major geometry rows should use at least two load-bearing tools from different
mathematical categories, or explain why that is not yet possible.

## Root Axioms, Derived Constraints, And Admission Gates

Do not call implementation gates "extended constraints." The actual root pair
and derived constraint pressure are:

Root pair:

- `F01_FINITUDE`: finite encodings, bounded distinguishability, no completed
  infinities, decidable admissibility.
- `N01_NONCOMMUTATION`: order-sensitive composition, no swap-by-default,
  sequence belongs to the object.

Nominalist axiom, from `CLAUDE.md` as reference doctrine:

- `a = a iff a ~_M b`: identity/equality is probe-relative
  indistinguishability under an active finite probe family `M`; primitive
  equality is not admitted.

Derived/extended constraint pressure:

- no primitive identity;
- no primitive equality;
- no primitive center point;
- no primitive coordinate grid;
- no primitive metric;
- no primitive time;
- no primitive causality;
- no primitive global objecthood;
- no free algebraic closure;
- no unrestricted real continuum;
- Bekenstein-style finite capacity:
  `log(dim H_region) <= boundary_capacity(region)`;
- no global total order;
- flux/chiral orientation is only an open derived candidate dependent on lower
  finite sheet/path/loop/cut receipts, not a primitive.

Every row must align to the root pair and respect the derived pressure above,
or be explicitly marked classical/control/adapter:

F01 finite:

- finite carrier set;
- finite probe/effect set;
- finite operator/path set;
- explicit finite domain and codomain/output;
- finite scale ladder, with 8 qubits/sites as floor and 16/32/64 as stress
  rungs where feasible;
- no dense-state or infinite-continuum closure as claim-bearing evidence.

N01 noncommutation/order:

- nonzero order gap, commutator gap, channel-order gap, history-effect gap, or
  path-order gap;
- order-erased and commuting controls collapse;
- label-only, scalar-only, Bloch-only, and non-informational controls fail or
  remain blocked.

Admission and implementation gates, not extended constraints:

- `EC_density`: Hermitian, PSD, trace-one; spinor-derived density distinguished
  from arbitrary density.
- `EC_CPTP`: channel Kraus/Choi/CPTP checks or blocked as non-CPTP control.
- `EC_PEPS3D`: explicit finite K=(V,E,F,C) with site/edge/face/cell anchors.
- `EC_chirality`: L/R or Weyl chirality explicit; swapped/no-chirality controls.
- `EC_quaternion`: explicit quaternion/Clifford action or invariant when used.
- `EC_entropy`: QIT entropy readouts, not diagonal Shannon as claim-bearing.
- `EC_tool`: PyTorch plus non-vacuous non-PyTorch load-bearing ablation.
- `EC_scale`: 8 floor; 16/32/64 stress or resource blocker.
- `EC_controls`: product, max-mixed, order-erased, boundary-shuffled,
  scalar-label, dense-closure, Bloch-only controls where meaningful.
- `EC_boundary`: blocked consumers named for stacking, bridge, flux, Xi/Phi0,
  Axis0, Holodeck/FEP, physics, and final manifold.

## PEPS3D Requirement

PEPS3D is not a late garnish. For nonclassical manifold or layer rows, the
carrier must be finite and PEPS3D-anchored as early as the row allows.

Minimum PEPS3D row data:

- finite K=(V,E,F,C);
- site, edge, face, and cell support counts;
- local tensor shape and bond dimension;
- boundary/interior distinction;
- local contraction or environment signature;
- explicit no-dense-closure flag;
- anchor-erased, edge/face/cell-erased, topology-shuffled, scalar-label, and
  dense-environment controls;
- scale ladder: 2x2x2 / 8 sites as floor, then 16/32/64 sites where feasible;
- bond ladder where feasible: 2, 3, 4 or resource-blocked.

Rows that cannot yet be PEPS3D-anchored must say why and must remain substrate
or adapter rows, not manifold rows.

## Entropy-As-Geometry Harness

Entropy must run across every row where a density, spinor-derived density,
cut, communication path, chirality split, or PEPS3D boundary exists. Entropy is
not a scalar decoration; it is geometric only when tied to a support/cut/path.

Required entropy families where applicable:

- von Neumann entropy;
- Renyi-2 entropy;
- mutual information;
- conditional entropy;
- relative entropy;
- coherent information;
- negativity/log-negativity for bipartite quantum cuts;
- path/history entropy for order-sensitive channels.

Required supports/cuts where applicable:

- site, edge, face, cell;
- bulk/boundary;
- L/R chirality sheets and chirality-swapped controls;
- engine/private/public cuts where communication exists;
- forward, reverse, shuffled, and order-erased paths.

If entropy appears geometric, the receipt must state the support that made it
geometric. A scalar entropy number without support, cut, probe, or comparator is
not geometry.

## Long-Running Tranche Ladder

The TUI should keep moving through this ladder. A blocked row does not block
unrelated independent rows.

### Tranche A: Existing Lego Reconciliation

Audit every existing `system_v5/legos/results/*.json`. Default each to
`blocked_pending_admission`. Rerun, validate, classify, and propose exact
registry/tool-matrix deltas.

### Tranche B: Missing Substrate Builds

Build or block missing rows found in Tranche A, especially density gaps,
CNOT/two-qubit entangling gate, depolarizing/CPTP, chiral overlap,
spinor-to-density, Cl3/Cl6 density bridge, spectral triple wiring, and weak or
decorative tool-matrix cells.

### Tranche C: 28-Family Migration Sweep

Continue until every `MIGRATION_REGISTRY.md` family is no longer a stale
`NOT_STARTED` claim. Each family becomes one of:

- `admit_candidate`;
- `repair_required`;
- `missing_build`;
- `blocked_on_gate`;
- `not_applicable_with_reason`.

No family can be silently left out.

### Tranche D: Tool-Matrix Repair

Work the high-value empty or weak columns/rows in
`TOOL_LEGO_INTEGRATION_MATRIX.md`, especially cvc5 coverage, SpectralTriple,
Gerbe, AssocBundle, and any PyG/TopoNetX decorative cells. Each repair is one
tool/function/lego-target triple.

### Tranche E: Layer/G-Structure Bootstrap

Only after substrate rows are terminal, use
`FORMAL_SIM_LAYER_VARIANT_CONSTRAINT_ALIGNMENT_SPEC_20260526.md` as a tracker.
Run scale-8 bootstrap probes for candidate geometry families and G-structures,
including killed and blocked candidates. Do not prove stacking yet.

### Tranche F: Variant And Scale Expansion

For earned layer rows, expand variants and scale rungs:

- 8/16/32/64 qubits or sites;
- PEPS3D bond ladder where meaningful;
- entropy spinor network cuts;
- tool ablation receipts;
- controls and negatives.

### Tranche G: Stacking Candidate Preparation

Only after enough layer legos are real, write candidate stacking tests. This is
still preparation, not final stacking canon. Stacking remains locked until its
own prompt and receipts.

## Required Artifacts

Write these under `system_v5/ops/formal_scouts/`:

1. `substrate_bootstrap_reconciliation_20260526.json`
2. `substrate_bootstrap_premortem_loop_20260526.json`
3. `substrate_bootstrap_registry_delta_proposal_20260526.json`
4. `substrate_bootstrap_tool_matrix_delta_proposal_20260526.json`
5. `substrate_bootstrap_continuation_required_20260526.json` only if the run
   must pause before terminal completion.
6. For later tranches, write analogous `*_reconciliation`, `*_delta_proposal`,
   `*_premortem_loop`, and `*_continuation_required` artifacts rather than
   overwriting the substrate files.

Do not edit `MIGRATION_REGISTRY.md` or `TOOL_LEGO_INTEGRATION_MATRIX.md` unless
the exact row delta is evidence-bound and the repo rules permit the edit. If in
doubt, write the delta proposal JSON instead.

## Reconciliation Schema

For every existing lego result and every genuinely missing substrate row, record:

- `row_id`
- `source_path`
- `result_path`
- `registry_family`
- `tool_matrix_family`
- `current_registry_status`
- `current_tool_matrix_status`
- `default_status: blocked_pending_admission`
- `final_row_status`: one of `admit_candidate`, `repair_required`,
  `missing_build`, `blocked_on_gate`
- `fresh_rerun_command`
- `fresh_rerun_status`
- `validator_command`
- `validator_status`
- `classification`
- `finite_map`
- `domain`
- `codomain_or_output`
- `F01_status`
- `N01_status`
- `torch_carrier_status`
- `spinor_or_density_status`
- `peps3d_anchor_status`
- `tool_manifest_status`
- `tool_integration_depth_status`
- `ablation_outcome_delta`
- `scale_status`
- `entropy_status`
- `controls_status`
- `blocked_consumers`
- `exact_registry_delta_or_blocker`
- `exact_tool_matrix_delta_or_blocker`
- `next_admissible_row_or_patch`

## Admission Checks

An existing lego can become `admit_candidate` only if all of these hold:

1. Fresh local rerun succeeds.
2. Validator succeeds or the missing validator is named as a blocker.
3. Result has valid `classification`, tool manifest, and tool depth fields.
4. PyTorch is claim-bearing where the claim is nonclassical.
5. NumPy or `.numpy()` is not claim-bearing for nonclassical claims.
6. At least one non-PyTorch tool is load-bearing when the claim requires it.
7. `ablation_outcome_delta` is non-vacuous: stubbing/removing the tool causes
   the exact claim to fail, weaken above noise, or become unprovable.
8. Entropy is computed when a density object exists: at minimum von Neumann
   entropy; MI/coherent information when bipartite.
9. Scale reaches at least 8 qubits/sites where meaningful, or the row is
   marked `debug_only` / `resource_blocked` and not admitted.
10. Positive, negative, boundary, product/max-mixed, label-erased, order-erased,
    Bloch-only, and dense-closure controls are present where meaningful.
11. `blocked_consumers` prevents matrix stacking, bridge, terrain, flux,
    Xi/Phi0, Axis0, basin, Holodeck/FEP, physics, and final-manifold claims.

If any item fails, the row is not admitted. It becomes `repair_required` or
`blocked_on_gate` with the next patch named.

## Work Order

Start with all existing `system_v5/legos/results/*.json`, not with new theory.

Priority tranche:

1. L0b `complex_hilbert_density_carrier`: density matrix torch baseline.
2. L2c `weyl_chirality_orientation_cover`: chiral overlap or spinor-to-density
   bridge. Existing Weyl chirality legos may help, but they do not automatically
   satisfy chiral-overlap density bridging.
3. L1 `peps3d_closure`: 2x2x2 PEPS3D carrier anchor with PyG or graph/topology
   tool load-bearing.

Then continue to genuinely missing or weak substrate rows discovered by
reconciliation, especially:

- CNOT or equivalent two-qubit entangling gate.
- Depolarizing/CPTP channel.
- Chiral overlap.
- Cl3/Cl6 spinor-to-density bridge.
- Spectral triple z3/SymPy/PyTorch wiring.
- Any empty or decorative tool-matrix row needed by the above.

## Premortem Fix Loop

Before each row:

1. Name three ways this row can fake progress.
2. Patch the row plan to prevent those failures.
3. Only then run, repair, or build.

After each row:

1. Audit the receipt against those three failure modes.
2. If the row fails, repair once immediately when the repair is local.
3. If still failed, write `blocked_on_gate` or `repair_required`.
4. Continue to the next independent row.

Do not stop after a good reconciliation, a green row, a blocked row, or a
validator that says downstream consumers remain blocked. Those are normal row
states.

## Terminal State

The goal is terminal only when all of these are true:

1. Every existing lego result has a row in the reconciliation JSON.
2. Every T1 priority row is terminal.
3. Every genuinely missing substrate row discovered by reconciliation is either
   built, repaired, or blocked with evidence.
4. Registry delta proposals are exact and evidence-bound.
5. Tool-matrix delta proposals are exact and evidence-bound.
6. The final report names the next row if any remains.

Allowed pause reasons:

- repo safety failure;
- dependency missing for all remaining rows;
- real context/runtime exhaustion.

If pausing, write `substrate_bootstrap_continuation_required_20260526.json`
with exact next row, current terminal rows, pending rows, blockers, commands run,
and what to do first on resume.

## Bad Closeouts

These are failures:

- "Reconciliation complete" with no next row selected.
- "One row passed" as a final answer.
- "Downstream remains blocked, so I stopped."
- "Wizard blocked, so I stopped."
- "Matrix can now proceed" without terminal substrate rows.
- Tool used/imported but no ablation outcome.
- Registry or matrix prose without row/key old/new deltas.
- Any manifold, stacking, bridge, flux, Axis0, or physics claim from this goal.

## Final Report Shape

Report concisely:

1. Wizard route truth: FULL/PARTIAL/BLOCKED and why.
2. Reconciliation artifact path.
3. Per-row counts by terminal status.
4. Rows admitted as candidates, with result paths and exact delta proposals.
5. Rows repaired or built, with result paths and validators.
6. Rows blocked, with blocker and next admissible patch.
7. Whether continuation is required and exact next row.

Do not output a log dump. Say what advanced, what remains, and what the next row
is.
