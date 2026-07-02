# Nested Hopf Tori Deep Sim Goal - 2026-05-30

## Purpose

Build one genuinely deep standalone geometry sim for `nested_hopf_tori`.

This is not a manifold admission goal. It is not G-structure selection. It does
not unlock stacking, flux, Xi/Phi0, Axis0, FEP/Holodeck, physics/gravity, or
final manifold claims.

## Starting Evidence

Current evidence says:

- The 24-target JAX geometry wave has real target-specific invariants.
- It is still shallow because it uses a shared finite sample/graph/Optax
  carrier pattern.
- `nested_hopf_tori` needs a geometry-specific carrier, dynamics, controls,
  tool integration, and parity pass before it can be called a proper deep sim.

Read before implementation:

- `AGENTS.md`
- `CODEX.md`
- `system_v5/docs/ENFORCEMENT_AND_PROCESS_RULES.md`
- `system_v5/docs/LLM_CONTROLLER_CONTRACT.md`
- `system_v5/docs/LEGO_SIM_CONTRACT.md`
- `system_v5/ops/formal_scouts/JAX_GEOMETRY_REALITY_AUDIT_20260530.md`
- `system_v5/ops/formal_scouts/ACTUAL_DEEP_SIM_EXECUTION_MATRIX_20260530.md`
- `system_v5/ops/formal_scouts/jax_native_geometry_engine.py`
- existing `nested_hopf_tori` source/result files.

## Required Finite Map

The sim must define an explicit finite map:

```text
M_nested_hopf_tori:
  (finite shells R, leaves L_r, Hopf spinors psi_{r,l,s},
   fiber phases theta, base coordinates b, admissible leaf paths P,
   carrier network N, controls C)
  ->
  (transported spinor-network states, fiber/base cut states,
   leaf-to-leaf transport readouts, QIT cut readouts,
   invariant residuals, failed controls, blocked consumers)
```

Minimum structure:

- shell index `r`
- leaf index `l`
- site index `s`
- Hopf fiber phase
- Hopf base projection
- finite path/order family
- spinor-network carrier over the leaves
- explicit inward/outward or leaf-to-leaf transport direction where used

## Required Carrier

Do not use only normalized finite samples plus graph edges.

The carrier must include:

- complex spinor states;
- a real network over the spinors;
- MPS plus PEPS2D and PEPS3D or a documented equivalent;
- bond dimension stress separate from site-count stress;
- product/no-entanglement control;
- dense-closure control fenced as non-claim-bearing.

Minimum stress axes:

- site counts: at least `8, 16, 32, 64`; attempt higher only if resources allow;
- bond dimensions: at least `2, 4`; attempt `5+` only if contraction remains honest;
- shell/leaf count variation independent of site count;
- path/order variation independent of shell count.

## Required Dynamics

The sim must include geometry-specific dynamics, not only the shared JAX
compatibility optimizer.

Required dynamics candidates:

- fiber phase transport along a Hopf fiber;
- base projection stability under fiber motion;
- leaf-to-leaf transport across nested torus leaves;
- noncommuting order comparison for two admissible transport actions;
- control dynamics where fiber/base or leaf order is scrambled.

## Required QIT / Entanglement Readouts

Entropy is not the geometry object. It is a readout carried by the network.

Required readouts where meaningful:

- von Neumann entropy on reduced cut states;
- mutual information across leaf/fiber/base cuts;
- conditional entropy;
- coherent information where the channel/cut direction is well-defined;
- logarithmic negativity or another entanglement witness;
- readout deltas under product/no-entanglement control.

## Required Tools

Use tools because they change or certify the result, not because they are listed.

Minimum expected roles:

- `jax` / `jax.numpy`: x64 primary or mirror for geometry-specific dynamics.
- `torch`: parity or blocked reason; if parity runs, report max delta.
- `quimb`, `cotengra`, `autoray`: network construction/contraction or explicit
  blocked reason if not available.
- `sympy`: exact Hopf/torus formula checks.
- `z3`: finite exclusion/minimality/order-control check.
- `cvc5`: cross-check one z3 structural claim or record a specific blocker.
- `rustworkx` / `networkx`: path/order graph checks.
- `xgi`: higher-order leaf/shell incidence if used.
- `TopoNetX` / `GUDHI`: topology checks only if a topology claim is made.
- `jaxtyping` / `chex`: shape/type controls for JAX surfaces.

## Required Controls

The sim must fail or weaken when these are removed:

- label-only geometry;
- target invariant erased;
- fiber/base relation scrambled;
- shell/leaf order scrambled;
- product/no-entanglement carrier;
- dense closure substituted as claim path;
- generic shared optimizer used without geometry-specific dynamics;
- scalar entropy made primary.

Each control should report an observed delta, not only a status string.

## Output Requirements

Write one new source and one new result receipt:

```text
system_v5/ops/formal_scouts/sim_nested_hopf_tori_full_deep_network_probe.py
system_v5/ops/formal_scouts/results/nested_hopf_tori_full_deep_network_probe_results.json
```

The result must include:

- `classification`
- `finite_map`
- `domain`
- `codomain_or_output`
- `carrier_realization`
- `peps3d_embedding`
- `spinor_state`
- `tool_manifest`
- `tool_integration_depth`
- `result_summary`
- `controls`
- `ablation_outcome_delta`
- `blocked_consumers`
- exact resource frontier reached.

## Validation

Run:

```text
PYTHON system_v5/ops/formal_scouts/sim_nested_hopf_tori_full_deep_network_probe.py
PYTHON scripts/lint_sim_contract.py system_v5/ops/formal_scouts/sim_nested_hopf_tori_full_deep_network_probe.py
PYTHON system_v5/ops/formal_scouts/validate_formal_scout_results.py --fresh-rerun system_v5/ops/formal_scouts/results/nested_hopf_tori_full_deep_network_probe_results.json
make layer-completion-claim-gate CLAIM_FILE=system_v5/ops/formal_scouts/NESTED_HOPF_TORI_DEEP_SIM_GOAL_20260530.md
git diff --check
```

## Completion Boundary

Allowed claim if everything passes:

```text
One bounded standalone nested_hopf_tori deep-network scout passed local rerun.
It is stronger than the earlier JAX finite-sample scout.
It does not admit the manifold, select the G-structure, open stacking, or unlock
Axis0/FEP/flux/physics.
```

Blocked claim:

```text
nested_hopf_tori is fully proven
all G-structures are done
the layer stack is ready
Axis0/FEP/flux/physics is unlocked
```
