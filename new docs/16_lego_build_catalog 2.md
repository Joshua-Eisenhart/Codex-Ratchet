# Lego Build Catalog

Status: working execution ledger  
Date: 2026-04-08

## Purpose

This doc is the current working catalog of the lego families the system needs.

It is not a theory essay.
It is not a raw sim dump.
It is not a bridge/Phi0/Axis plan.

It exists to answer:
- which pure-math or boundary-lego families must exist
- which are already covered by a decent lego probe
- which still need deeper lego work
- which tool surfaces should be load-bearing for each lego
- which pairwise successor each lego should feed next

This is the bounded catalog extracted from the current execution docs and machine artifacts.
It should widen later, but this is the working build set now.

## Authority Order

Use these surfaces in this order:

1. Machine artifacts
- `system_v4/probes/a2_state/sim_results/lego_stack_audit_results.json`
- `system_v4/probes/a2_state/sim_results/lego_coupling_candidates.json`
- `system_v4/probes/a2_state/sim_results/lego_batch_queue.json`
- `system_v4/probes/a2_state/sim_results/controller_alignment_audit_results.json`

2. Core execution docs
- `new docs/07_model_math_geometry_sim_plan.md`
- `new docs/08_aligned_sim_backlog_and_build_order.md`
- `new docs/LEGO_SIM_CONTRACT.md`
- `new docs/FALSIFICATION_SIM_DESIGNS.md`
- `new docs/ENFORCEMENT_AND_PROCESS_RULES.md`

3. Everything else
- useful only if it does not conflict with the surfaces above

## Build Rules

- A lego is local or tightly bounded. It is not a bridge, bakeoff, packet, audit, integrated pipeline, or axis-entry surface.
- Root-killed or rejected sims are useful. Keep them as evidence surfaces.
- A lego does not promote because it exists. It promotes only if the result is clear, scoped, and tool-honest.
- A tool only counts if it is load-bearing or clearly supportive in the real execution path.
- Pairwise and coexistence work come after the lego is real.
- Assembly does not consume a lego just because the lego passed once.

## Status Labels

- `covered`: there is at least one good current lego probe
- `partial`: the family exists, but the current lego set is still thin or mixed
- `needs_deeper_lego_work`: current candidates exist but are not yet strong enough
- `ready_for_pairwise`: there is already a usable successor for the family
- `blocked_from_assembly`: useful family, but not allowed to feed assembly yet

## Core Lego Families

| Lego ID | Layer | What It Is | Current Status | Current Best Probes | Tool Focus | Next Safe Successor |
| --- | --- | --- | --- | --- | --- | --- |
| `constraint_probe_admissibility` | L0-L1 | probe admissibility, fence pressure, root-constraint boundary | `needs_deeper_lego_work` | `sim_bc1_fence_investigation.py` | `z3`, later `cvc5` | `sim_constraint_shells_binding_crosscheck.py` |
| `carrier_admission_density_matrix` | L1 | carrier admission, positivity, trace, density-matrix representability | `partial` | `sim_density_hopf_geometry.py` | `pytorch`, `sympy` | `sim_operator_geometry_compatibility.py` |
| `geometry_crosschecks_same_carrier` | L2 | same-carrier geometry comparisons: Hopf, Berry, QFI, metric structure | `covered` | `sim_foundation_hopf_torus_geomstats_clifford.py`, `sim_berry_qfi_shell_paths.py` | `geomstats`, `clifford`, `sympy` | `sim_compound_operator_geometry.py` |
| `graph_cell_complex_geometry` | L2 | graph, hypergraph, cell-complex, persistence views on the same carrier | `covered` | `sim_xgi_family_hypergraph.py`, `sim_foundation_shell_graph_topology.py`, `sim_foundation_equivariant_graph_backprop.py` | `xgi`, `toponetx`, `gudhi`, `pyg` | `sim_xgi_indirect_pathway.py`, `sim_toponetx_state_class_binding.py`, `sim_pyg_dynamic_edge_werner.py` |
| `operator_family_admission` | L3 | Pauli/Clifford/channel/operator family behavior before assembly | `needs_deeper_lego_work` | no clean default probe yet | `clifford`, `sympy`, `z3` | `sim_operator_geometry_compatibility.py` |
| `bipartite_structure_local` | L4 | partial trace, concurrence, negativity, local bipartite witnesses | `covered` | `sim_gudhi_bipartite_entangled.py`, `sim_gudhi_concurrence_filtration.py` | `gudhi`, `pyg`, `sympy` | `sim_lego_entropy_bipartite_cut.py`, `sim_pyg_dynamic_edge_werner.py` |
| `entropy_family_crosschecks` | L5 | local entropy-family comparison before any bridge or axis promotion | `needs_deeper_lego_work` | no clean default probe yet | `sympy`, `pytorch` | none yet; stay local first |
| `gauge_group_falsifier` | boundary lego | operator/symmetry kill surface from falsification doc | `covered` | `sim_geom_cp1_u1_projective.py`, `sim_geom_su2_so3_quaternions.py` | `sympy`, geometry stack | `blocked_from_assembly` |
| `quantum_metric_nonuniqueness` | boundary lego | compare quantum metric choices without smuggling one geometry as primitive | `covered` | `sim_geomstats_shell_metrics.py`, `sim_lego_weyl_wigner_phase_space.py` | `geomstats`, `sympy` | `blocked_from_assembly` |

## Families That Are Not Lego

These are real and useful, but they are not lego-family entries for this catalog:

| Family | Why It Is Not Lego |
| --- | --- |
| `dependency_dag_and_collapse` | coupling / collapse-analysis surface |
| `viability_vs_attractor_falsifier` | coupling-stage dynamics comparison |
| `axis_entry_after_admission` | explicitly later than the lego stack |
| bridge / cut / kernel / Phi0 files | late-object or seam surfaces |
| bakeoffs / audits / packets / validations | controller or comparison surfaces, not foundational math objects |

## Tool Integration Targets

Current shallow tools from the machine audit:
- `pyg`
- `cvc5`
- `e3nn`
- `toponetx`

What that means here:

- `pyg` should deepen through graph/cell-complex and bipartite local legos first.
- `cvc5` should deepen through constraint/probe admissibility legos first.
- `e3nn` should deepen through geometry/operator legos first.
- `toponetx` should deepen through graph/cell-complex geometry legos first.

## Current Queue-First Batch

Current top ready tasks from `lego_batch_queue.json`:

1. `graph_cell_complex_geometry -> sim_pyg_dynamic_edge_werner.py`
2. `bipartite_structure_local -> sim_pyg_dynamic_edge_werner.py`
3. `bipartite_structure_local -> sim_lego_entropy_bipartite_cut.py`
4. `graph_cell_complex_geometry -> sim_xgi_indirect_pathway.py`
5. `graph_cell_complex_geometry -> sim_toponetx_state_class_binding.py`
6. `geometry_crosschecks_same_carrier -> sim_compound_operator_geometry.py`

These are middle-ladder tasks.
They are safer than more bridge or assembly expansion.

## Stop Rules

- Do not feed assembly from a family marked `needs_deeper_lego_work`.
- Do not treat `supporting` successors as closure-grade.
- Do not use bridge, cut, kernel, Phi0, or axis files to stand in for missing lego work.
- Do not discard root-killed/rejected lego candidates; keep them as evidence surfaces.

## Commands

- `make lego-audit`
- `make lego-coupling`
- `make lego-queue`

Bot read-only views:
- `lego`
- `pairs`
- `queue`
- `sims`

## Bottom Line

The current program should be:

1. finish the lego families above
2. deepen tool integration per lego
3. run pairwise successors
4. only then widen into coexistence, topology reruns, and assembly
