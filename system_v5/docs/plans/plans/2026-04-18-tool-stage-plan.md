# 2026-04-18 Tool Stage Plan

Status: SAVED TOOL-STAGE PLAN

Use this file when:
- the controller needs the actual tool/base-stage plan without softening it into unrelated higher-stage claims
- the repo has many tool capability / integration probes but the live planning surfaces still present an older, smaller Tier A story
- a worker or planner needs to know which tool-stage packets are still honest now

Do not use this file as a truth-label surface. Keep `sim_truth_audit.md` for truth labels and `queue_tier_a.txt` for live queued Tier A execution.

## Hard Guardrail

The tool stage sits inside the larger build loop:

1. tool sims stay active
2. tool-integration sims stay active
3. lego rows stay active one by one
4. bounded coupling exploration may exist elsewhere in the loop, but tool-stage work must not be reframed as broad higher-stage progress
5. bridge / axis / engine work still remains later and gated

Tool-stage progress does not authorize lego skipping.
Tool-stage progress does not authorize broad coupling promotion.

## Current Truth

- the repo contains far more tool-stage surface than the old Tier A plan implies
- current filesystem scan shows:
  - `34` capability-style probes
  - `47` integration-style probes
- only a bounded subset should be treated as current-stage tool packets
- many `sim_integration_*` files are already too bridgey, too stack-shaped, or too late to serve as the clean tool stage
- fresh 2026-04-18 executions now verify:
  - capability anchors: `sim_rustworkx_capability.py`, `sim_geomstats_capability.py`, `sim_xgi_capability.py`, `sim_e3nn_capability.py`
  - clean follow-on canonical integrations: `sim_integration_hypothesis_z3_property_guard.py`, `sim_integration_optuna_sympy_invariant_search.py`, `sim_integration_datasketch_pyg_lsh_graph.py`, `sim_integration_ribs_z3_constraint_archive.py`
  - real coverage-lego anchors:
    - `sim_gtower_reduction_obstruction_z3.py`
    - `sim_toponetx_hopf_crosscheck.py`
    - `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py`
    - `sim_foundation_hopf_torus_geomstats_clifford.py`
  - further tool-bearing or tool-adjacent local executions now verify:
    - `sim_e3nn_hopf_spinor_equivariance.py`
    - `sim_toponetx_state_class_binding.py`
    - `sim_integration_gudhi_gtower_filtration.py`
    - `sim_lego_constraint_admissibility_fence_z3.py`
    - `sim_torch_channel_taxonomy.py`
  - fresh local normalization reruns now verify:
    - `sim_graph_shell_geometry.py`
    - `sim_reduced_state_object.py`
    - `sim_negativity_measure.py`
    - `sim_concurrence_measure.py`
    - `sim_local_operator_action.py`
    - `sim_persistence_geometry.py`
    - `sim_foundation_shell_graph_topology.py`

## Tool-Stage Principles

1. a tool should be simed on a real bounded lego whenever possible, not only in a sterile demo
2. the goal is not “every tool in one sim”; the goal is a small coverage-lego set that exercises the tool estate honestly
3. one tool-integration sim should prove actual interop, not parallel tool usage
4. tool-stage packets stay below lego coupling claims even when they use real legos
5. graph / topology / manifold / solver / symbolic tools should earn their own load-bearing rows on real objects
6. extension tools are allowed, but only if they stay bounded and honest

## Coverage-Lego Rule

Tool-stage planning should now prefer a small set of real local legos that together cover many tools well.

The question is not:
- “did we author one isolated file per tool?”

The better question is:
- “do we have a good set of real bounded legos that honestly exercise the tool families and their integrations?”

It is not required to find one sim that integrates all tools.
It is required to find a good set of legos that covers the tools well.

## Current Best Coverage-Lego Set

These are the best current real local families for covering many tools without widening into coupling work:

1. Hopf / same-carrier geometry family
- best for: `pytorch`, `clifford`, `geomstats`, `e3nn`, `gudhi`, `toponetx`, and some `pyg`
- representative surfaces:
  - `sim_density_hopf_geometry.py`
  - `sim_foundation_hopf_torus_geomstats_clifford.py`
  - `sim_e3nn_hopf_spinor_equivariance.py`
  - `sim_toponetx_hopf_crosscheck.py`
  - `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py`

2. Weyl local / nested-shell family
- best for: `rustworkx`, `z3`, `clifford`, `geomstats`
- representative surfaces:
  - `sim_weyl_nested_shell.py`
  - `sim_weyl_geometry_graph_proof_alignment.py`

3. G-tower local obstruction / filtration family
- best for: `z3`, `rustworkx`, `gudhi`, `toponetx`
- representative surfaces:
  - `sim_gtower_reduction_obstruction_z3.py`
  - `sim_integration_gudhi_gtower_filtration.py`
  - `sim_integration_toponetx_gtower_chain_complex.py` as reference only until thinned

4. Constraint / distinguishability proof-search family
- best for: `z3`, `cvc5`, `sympy`, `hypothesis`, `optuna`, `ribs`
- representative surfaces:
  - `sim_integration_hypothesis_z3_property_guard.py`
  - `sim_integration_optuna_sympy_invariant_search.py`
  - `sim_integration_ribs_z3_constraint_archive.py`

5. Graph / cell-complex local family
- best for: `pyg`, `datasketch`, `networkx`, `rustworkx`, `xgi`, `toponetx`
- representative surfaces:
  - `sim_integration_datasketch_pyg_lsh_graph.py`
  - `sim_integration_networkx_rustworkx_crosscheck.py`
  - `sim_toponetx_state_class_binding.py`

## Tool Buckets

### 1. Core tool-capability gate

These are the clearest first-class stage-1 tools:
- z3
- cvc5
- sympy
- torch / pytorch
- PyG
- TopoNetX
- clifford

These already have the clearest direct `tool_capability_*` or equivalent probes.

### 2. Extension capability normalization

These tools already have capability probes or clear capability-style files, but the live Tier A story under-represents them:
- GUDHI
- Pennylane
- NetworkX
- Cirq
- QuTiP
- torch_ga
- rustworkx
- geomstats
- XGI
- e3nn

These should be treated as second-wave tool-stage work, still below lego work.

### 3. Clean second-wave tool integrations

These are bounded enough to stay in the tool stage:
- `sim_integration_networkx_rustworkx_crosscheck.py`
- `sim_integration_geomstats_constraint_manifold.py`
- `sim_integration_gudhi_gtower_filtration.py` when kept local to one bounded filtration object

Borderline / quarantine unless rewritten thinner:
- `sim_integration_toponetx_gtower_chain_complex.py`
  - executed 2026-04-18 as a `classical_baseline` reference packet
  - currently too tower-order / shortcut-law shaped to serve as the clean default Tier A next move

### 4. Not clean tool-stage packets

Do not treat these as current tool-stage defaults even if their names say `integration`:
- bridge stacks
- multi-shell coexistence stacks
- spectral-triple / axis / bridge composites
- quantum-open / mega-stack / entropy-stack surfaces that already import late structure

## Actual Tool Plan

### Phase T1. Normalize the core gate

- keep the core 7 tool-capability rows explicit
- keep the core 6 tool-integration rows explicit
- maintain the rule that these are foundational, not side work

### Phase T2. Normalize the real extension tool estate

Bounded capability reruns / audits for:
- rustworkx
- geomstats
- XGI
- e3nn
- GUDHI
- Pennylane
- NetworkX
- Cirq
- QuTiP
- torch_ga

Goal:
- make the repo’s real tool-stage coverage visible without pretending every extension tool is equally deep

### Phase T3. Run bounded second-wave integrations

Priority order:
1. networkx + rustworkx crosscheck
2. geomstats constraint manifold
3. GUDHI G-tower filtration when kept local to one bounded filtration object
4. revisit TopoNetX G-tower only after it is thinned back below tower-order semantics

### Phase T3b. Use real coverage legos on purpose

After the clean second-wave integrations:
- choose bounded real legos that cover underused tools well
- prefer Hopf, Weyl, G-tower obstruction, constraint/distinguishability, and graph/cell-complex locals
- do not widen into coupling just because a coverage-lego uses many tools
- use these coverage legos to decide which isolated capability probes are still worth doing and which are now redundant

Rule:
- these are still tool-stage packets
- they must not be reframed as lego coupling or bridge preparation

### Phase T4. Tool-stage maintenance

- keep `TOOL_CAPABILITY_AND_INTEGRATION_LEDGER.md` current
- keep `tool_integration_maintenance_matrix.md` current
- keep `TIER_A.md` aligned with the real tool-stage estate rather than the older seven-tool story alone

## Immediate Bounded Batch

Queue these as the next honest Tier A second-wave batch:

### Capability packets
- `sim_rustworkx_capability`
- `sim_geomstats_capability`
- `sim_xgi_capability`
- `sim_e3nn_capability`

### Integration packets
- `sim_integration_networkx_rustworkx_crosscheck`
- `sim_integration_geomstats_constraint_manifold`
- hold `sim_integration_toponetx_gtower_chain_complex` as executed reference material only until it is thinned below tower-order / shortcut-law semantics

### Coverage-lego follow-ons
- `sim_gtower_reduction_obstruction_z3.py`
- `sim_toponetx_hopf_crosscheck.py`
- `sim_gudhi_deep_s3_hopf_torus_persistent_homology.py`
- `sim_foundation_hopf_torus_geomstats_clifford.py`

## Explicit Non-Moves

- do not treat bridge-shaped `sim_integration_*` files as tool-stage defaults
- do not move from tool stage to lego stage because “enough tools look good”
- do not move from tool integrations to broad higher-stage claims
- do not let late-stage composites hide inside the tool-stage backlog

## Bottom Line

The tool stage is bigger than the old plan says, but the rule is still simple:

1. keep tool sims active
2. keep tool integrations active
3. use them to support honest lego completion inside the larger loop
4. do not let tool-stage success masquerade as broad higher-stage permission

The main need now is not more vague tool talk.
It is a cleaner, stricter operator-facing tool-stage plan plus bounded Tier A packets that stay honestly below lego work.
