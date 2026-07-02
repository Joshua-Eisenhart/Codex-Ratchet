# Formal Sim Layer Lego Build Goal - 2026-05-26

Status: architecture/reference spec. Do not use this as the immediate launch
prompt while substrate admission is unreconciled.

Use the substrate bootstrap prompt first:

```text
system_v5/ops/FORMAL_SIM_SUBSTRATE_BOOTSTRAP_GOAL_20260526.md
```

Rationale: the full layer/G-structure matrix is architecturally useful, but it
overreaches as a controller surface until torch density/channel/gate and
spinor-to-density bridge legos are admitted or explicitly blocked in the live
registries. After those prerequisites exist, this file can become the tracker
for variants of the earned legos.

## Copy-Paste Prompt

```text
You are in /Users/joshuaeisenhart/Desktop/Codex Ratchet.

Goal: build the full candidate geometry/G-structure lego inventory before stacking/order. Do not grind one Phase2 map. Do not stack. Make things to stack first.

Read: AGENTS.md, CODEX.md, the three process docs, SIM_FULL_WIZARD_PARALLEL_RUNBOOK.md, current Phase2 matrix/transition/blocker/receipts, and system_v5/ops/FORMAL_SIM_LAYER_VARIANT_CONSTRAINT_ALIGNMENT_SPEC_20260526.md.

Run Wizard v4.2 Max Assembly with high parallelism. Use Codex parents plus model/tool children where available. Count only completed receipts. Reroute stalls. No FULL without real receipts.

Build/update manifold_layer_lego_matrix_20260526.json with schema_version=layer_lego_v1 and no field aliases. Active unit = layer_id x variant_id x scale_rung x tool_receipt.

Doctrine: layer/shell legos are simultaneous constraint surfaces, not a ladder. Stacking order is later. PEPS3D is carrier from the first nonclassical carrier step. Labels are invalid without finite maps.

Inventory rows must include possible geometries too: finite response quotient, Hilbert/density carrier, PEPS3D, MPS/MERA/boundary-MPS, spinor sphere, Hopf bundle/tori, Weyl chirality cover, Clifford module, quaternionic action, frame/G-structure reductions O/SO/U/SU/Sp/Spin/SpinC/Pin plus finite G2/Spin7 candidates, symplectic/contact/Poisson/Dirac/Berry, finite spectral triple, terrain placement, operator substage cells, entropy cuts, tensor communication, gluing/groupoid/equivariant/dynamic candidates.

Each row: sim_id, tier, geometry_family, g_structure_family, finite_map, domain, codomain_or_output, F01_alignment, N01_alignment, peps3d_embedding, spinor_state, quaternion_action, entropy_matrix, scale_rungs, required/actual tools, tool_manifest/depth, tool_ablations, controls, negatives, artifacts, witness_trace_id, promotion_status, public_status_label, runner_state, blocker_reason, receipt_path, blocked_consumers.

Entropy spinor network on every meaningful row, not only entropy row: S(rho), Renyi2, MI, conditional, coherent, relative, negativity/log-negativity, path entropy across site/edge/face/cell/sheet/boundary/path/history cuts. Diagonal Shannon is control-only unless basis/probe and comparator are explicit.

Terrain rows: run Se/Ne/Ni/Si and label/random controls across unitary, CPTP/Kraus, Lindblad, projector, metric-distortion, curvature, site/edge/face/cell/boundary support, terrain/operator orders, basis variants, and entropy cuts.

Controls: product, max-mixed, matched-marginal, label/order-erased, chirality-swapped/no-chirality, boundary-shuffled, Bloch-only, scalar-PEPS, dense-state/env closure.

Scale/tool gate: full PyTorch tensors for claim numerics; no NumPy/.numpy/dense closure except controls. <8 qubits/sites debug only. Run/queue 8 floor and 16/32/64 stress ladder; resource-block failed rungs. Row cannot pass on toy scale or torch-only decoration. At least one relevant non-PyTorch tool load-bearing with ablation: claim_fails, claim_weakens, or map_unprovable. Try relevant PyG, Clifford, z3, cvc5, SymPy, geomstats/e3nn, rustworkx/XGI/TopoNetX/GUDHI.

Execution loop:
1 Build/audit matrix first.
2 T1: one bootstrap probe per geometry/variant axis at scale 8 with controls. If zero runner receipts exist, run one bounded bootstrap probe per geometry family; then strict gates resume.
3 T2: one stress rung >=16 or resource blocker.
4 T3: non-PyTorch load-bearing ablation.
5 T4: entropy spinor network coverage.
6 Run independent rows in parallel; result writes serial.
7 Continue until rows are passed, killed, blocked, resource_blocked, queued, or running with receipt. File creation alone is not started work.

Final report: matrix path, rows changed, probes run/queued, entropy findings, tool ablations, blockers, next probe. Forbidden: stacking/order claims, final manifold admission, Axis0/flux/physics claims, same-map Phase2 grinding, FULL Wizard without receipts.
```

## Local Test Checklist

- Copy block stays under 4000 characters.
- Builds all independent layer legos before stacking/order proof.
- Makes entropy a required invariant suite, not an assumed layer promotion.
- Preserves Gate0 and no-scout-while-red boundary.
- Requires per-row finite maps, controls, tools, receipts/blockers.
