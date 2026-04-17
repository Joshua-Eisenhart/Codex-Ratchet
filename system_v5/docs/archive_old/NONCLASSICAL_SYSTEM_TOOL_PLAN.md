# Nonclassical System Tool Plan

Status: formal working plan
Scope: tools to install and use for the nonclassical pre-Axis simulation system
Purpose: define the actual tool stack for the system, with named jobs, instead of relying on old scattered research notes

## 1. Governing rule

Only add or keep a tool if it has a named job in the pre-Axis sim pipeline.

This system is not allowed to drift into:
- toy sims
- narrative proofs
- scalar-only reductions of rich geometry
- classical smoothing by LLM habits
- using whatever tool is easiest instead of what the tier requires

A tool is justified only if it supports one or more of:
- admissibility checking
- candidate-law synthesis/refinement
- exact symbolic pressure
- topology-pressure on the geometry ratchet
- rich tensor/chirality/entanglement simulation
- graph-native state/writeback
- negative-suite generation
- witness/provenance discipline
- promotion/embargo enforcement

## 2. Core architectural split

### 2.1 Owner stack
These are the auditable core tools that define the canonical system surface.

- `pydantic`
  - typed schemas for sim contracts, graph nodes/edges, witness payloads, result packets
- `jsonschema`
  - artifact validation and anti-drift enforcement
- `networkx`
  - canonical in-memory graph structure
- `GraphML`
  - stable graph interchange and inspection format
- `witness recorder` / append-only witness trace
  - record positive, negative, and counterexample traces with provenance
- `pytest`
  - executable gates per tier
- `hypothesis`
  - property-based pressure on invariants and negatives
- `z3`
  - hard admissibility, impossibility, and embargo checks

These are the minimum serious stack for fail-closed pre-Axis work.

### 2.2 Augmentation stack
These are richness/sidecar tools that extend the owner stack without replacing it.

- `torch`
  - tensor substrate
- `PyTorch Geometric (PyG)`
  - tensorized heterograph projections and richer relation handling
- `TopoNetX`
  - higher-order topology, cells, boundaries, loop/hole structure
- `clifford`
  - noncommutative / graded / orientation-aware algebra
- `pyquaternion`
  - spinor/quaternion transformations between S3 / Hopf / Weyl-style geometry
- `kingdon`
  - bridge between geometric algebra and tensor backends when needed
- `hypernetx` / `xgi`
  - higher-arity relational structure if pairwise/cell-complex forms become insufficient

### 2.3 Fresh proof/geometry additions
These fill real gaps not covered by the older stack.

- `cvc5`
  - second solver and SyGuS-style synthesis/refinement
- `sympy`
  - exact symbolic pressure on lower-tier identities and branch-sensitive algebra
- `gudhi`
  - topology-pressure on the geometry ratchet itself
- `ripser.py`
  - lighter persistent homology/TDA sidecar when GUDHI is too heavy
- `egglog`
  - rewrite/equivalence pressure when symbolic branch normalization risks becoming hand-wavy

## 3. Tool categories and named jobs

## 3.1 Admissibility / embargo / impossibility

### `z3`
Named jobs:
- `admissibility_gate`
- `embargo_enforcer`
- `impossibility_checker`

Use for:
- proving a branch is blocked
- proving promotion conditions are not satisfied
- proving a candidate violates root constraints
- mechanical tier-7 embargo

### `cvc5`
Named jobs:
- `second_solver_oracle`
- `candidate_law_synthesizer`
- `synthesis_refiner`

Use for:
- SyGuS-style synthesis of transport/chiral/placement candidates
- cross-checking z3 results on hard constraints
- refining candidate-law families instead of handwritten loop-only searching

Rule:
- use `cvc5` where branch search/refinement is part of the tier, not just pass/fail admission

## 3.2 Exact symbolic pressure

### `sympy`
Named jobs:
- `exact_identity_pressure`
- `branch_sensitive_algebra_checker`
- `assumption_explicitifier`

Use for:
- lower-tier geometric/algebraic identities
- exact simplification under assumptions
- detecting when numeric witness pressure is too weak
- explicit statement of conditions under which an identity holds

Rule:
- if a tier depends on exact identity structure, numeric-only support is insufficient

## 3.3 Topology-pressure on the geometry ratchet

### `gudhi`
Named jobs:
- `geometry_ratchet_topology_pressure`
- `persistence_under_constraint_narrowing`
- `nested_carrier_feature_survival`

Use for:
- measuring which topological features survive as constraints narrow admissible geometry
- testing whether broader-carrier features collapse under lower admitted structure
- persistent homology over nested carrier filtrations

### `ripser.py`
Named jobs:
- `fast_persistence_probe`

Use for:
- quick smaller persistent homology experiments when full GUDHI workflows are too heavy

Rule:
- geometry-ratchet claims should eventually have topology-pressure, not just graph decoration

## 3.4 Graph-native state and writeback

### `networkx`
Named jobs:
- `canonical_system_graph`
- `state_graph`
- `dependency_graph`
- `witness_graph`

Use for:
- canonical owner graph structure
- state/writeback representation
- dependency and lineage representation

### `PyG`
Named jobs:
- `tensorized_heterograph_projection`
- `typed_relation_graph`
- `rich_edge_state_projection`

Use for:
- tensor-rich graph structure
- heterograph node/edge typing
- richer graph state than scalar summaries

### `TopoNetX`
Named jobs:
- `higher_order_topology_projection`
- `cell_complex_projection`
- `loop_boundary_structure`

Use for:
- non-pairwise topology
- cell/boundary/loop structure that plain graphs cannot express well

### `clifford`
Named jobs:
- `noncommutative_edge_semantics`
- `orientation_algebra_surface`

Use for:
- orientation-aware and graded algebra on geometry/graph structures
- preserving nonclassical algebra rather than flattening to scalar graph labels

### `pyquaternion`
Named jobs:
- `spinor_quaternion_transform_layer`

Use for:
- S3/Hopf/Weyl transform handling
- quaternion/spinor layer where plain graph or matrix code is too thin

### `kingdon`
Named jobs:
- `ga_tensor_bridge`

Use for:
- coupling GA structure into tensor pipelines when needed later

## 3.5 Negative pressure and branch exploration

### `hypothesis`
Named jobs:
- `property_pressure`
- `adversarial_negative_generator`

Use for:
- adversarial cases
- invariant pressure
- branch attacks
- negative suite expansion

### `structured_fuzzer.py`
Named jobs:
- `structured_negative_generator`

Use for:
- targeted adversarial generation beyond generic property testing

### `differential_tester.py`
Named jobs:
- `branch_comparator`
- `live_vs_ablated_diff`

Use for:
- comparing live branch vs flattened branch
- comparing chirality-preserved vs no-chirality
- comparing same-carrier vs ablated variants

### `model_checker.py`
Named jobs:
- `promotion_path_checker`
- `embargo_state_machine_checker`

Use for:
- tier progression logic
- promotion blockers
- branch-transition legality

### `z3_cegis_refiner.py`
Named jobs:
- `cegis_refiner`

Use for:
- counterexample-guided candidate law refinement
- transport/chiral/placement law searching

### `egglog`
Named jobs:
- `rewrite_equivalence_pressure`
- `branch_canonicalizer`

Use for:
- preventing prose-based normalization of symbolic branches
- rewrite/equivalence saturation under explicit laws

## 3.6 Witness and artifact discipline

### `pydantic`
Named jobs:
- `sim_contract_schema`
- `graph_payload_schema`
- `witness_payload_schema`

### `jsonschema`
Named jobs:
- `artifact_validator`
- `promotion_artifact_gate`

### `witness recorder`
Named jobs:
- `append_only_witness_spine`
- `step_trace_host`
- `counterexample_trace_host`

Rule:
- if a tier requires a tool, the resulting artifact must exist and validate
- missing artifact means no promotion

## 4. Tier-by-tier required tool gates

## Tier 0 — Root constraints
Required:
- `z3`
- `pytest`
- `pydantic`
- `jsonschema`
- witness trace

Optional but useful:
- `cvc5` for cross-checking or synthesis of admissibility fragments
- `sympy` when exact symbolic identities are involved

Pass standard:
- root constraints are machine-enforced, not narrated

## Tier 1 — Finite carrier
Required:
- `z3`
- `pytest`
- `hypothesis`
- `sympy` when exact carrier identities matter
- witness trace

Optional:
- `networkx` if carrier relations are already graph-encoded

Pass standard:
- admissible carrier family shown under root constraints
- negatives included for disallowed carriers

## Tier 2 — Geometry
Required:
- `z3`
- `sympy`
- `pytest`
- `hypothesis`
- witness trace
- `networkx`

Required for full-geometry claims:
- `PyG`
- `TopoNetX`
- `clifford`
- `pyquaternion`
- `gudhi`

Pass standard:
- no reduced geometry can support a full-geometry claim
- if geometry richness is dropped, result becomes `diagnostic_only`

## Tier 3 — Transport
Required:
- `z3`
- `cvc5`
- `z3_cegis_refiner`
- `hypothesis`
- `differential_tester`
- `structured_fuzzer`
- witness trace
- `networkx`

Optional:
- `sympy`
- `egglog`

Pass standard:
- exact-loop law survivor must be found under synthesis/refinement and negatives
- handwritten candidate loops alone are insufficient

## Tier 4 — Differential / chirality / flux
Required:
- `z3`
- `cvc5`
- `z3_cegis_refiner`
- `sympy`
- `hypothesis`
- `differential_tester`
- witness trace
- `PyG`
- `clifford`
- `pyquaternion`
- `TopoNetX`

Strongly recommended:
- `gudhi`
- `egglog`

Pass standard:
- no single chiral law may be admitted without proof pressure, negatives, and rich geometry/tensor/chirality substrate

## Tier 5 — Negatives
Required:
- `hypothesis`
- `structured_fuzzer`
- `differential_tester`
- `pytest`
- witness trace
- `networkx`

Pass standard:
- no promotion without kill tests
- negatives must be explicit and artifacted

## Tier 6 — Placement / pre-entropy
Required:
- `z3`
- `cvc5`
- `sympy`
- `networkx`
- witness trace
- `jsonschema`
- `pydantic`

Required when placement depends on full geometry:
- `PyG`
- `TopoNetX`
- `clifford`
- `pyquaternion`
- `gudhi`

Pass standard:
- placement cannot be treated as prose-only packet structure
- placement law must remain downstream of admitted lower geometry
- bridge family, cut family, and kernel family must remain distinguished where the tier depends on their relation

## Tier 7 — Axis-entry
Required for any unembargo attempt:
- all lower required tiers satisfied
- `z3` embargo checks
- `pytest` promotion gates
- witness trace

Rule:
- no Axis-entry before transport / differential / placement closure
- if middle tiers are open, Axis-entry is blocked mechanically

## 5. Immediate install/use priorities

## Priority 1 — Must be active in the real pipeline
- `z3`
- `hypothesis`
- `pytest`
- `networkx`
- `pydantic`
- `jsonschema`
- `torch`
- `PyG`
- `TopoNetX`
- `clifford`
- `pyquaternion`
- witness recorder

## Priority 2 — Fresh additions with real current jobs
- `cvc5`
- `sympy`
- `gudhi`

## Priority 3 — Good second-wave additions
- `ripser.py`
- `egglog`
- `kingdon`
- `hypernetx`
- `xgi`

## Priority 4 — Later / only when justified
- `Lean + mathlib`
- additional theorem provers beyond explicit need
- alternate graph backends unless current stack proves insufficient

## 6. What not to do

Do not:
- install tools just because they are interesting
- count numeric-only witnesses as enough where exact symbolic pressure is required
- count graph labels as enough where tensor/chirality richness is required
- count a green validator as enough if the required tools were not actually used
- use Lean/Coq-style systems as first-line engine for this repo
- let package existence substitute for integration

## 7. Immediate next build targets

### Target A — transport law search
Wire in:
- `z3`
- `cvc5`
- `z3_cegis_refiner`
- `hypothesis`
- `differential_tester`
- `structured_fuzzer`
- witness trace

### Target B — chiral law search
Wire in:
- `z3`
- `cvc5`
- `z3_cegis_refiner`
- `sympy`
- `hypothesis`
- `differential_tester`
- witness trace
- `PyG`
- `clifford`
- `pyquaternion`

### Target C — geometry ratchet pressure
Wire in:
- `sympy`
- `TopoNetX`
- `PyG`
- `clifford`
- `pyquaternion`
- `gudhi`
- `networkx`
- witness trace

### Target D — graph-native writeback honesty
Wire in:
- `networkx`
- `PyG`
- `TopoNetX`
- `clifford`
- `pydantic`
- `jsonschema`
- witness trace

## 8. Promotion rule

If a sim flattens the carrier ladder, drops tensor/chirality richness, skips proof pressure, or lacks negative structure, it is `diagnostic_only` and cannot support Axis work.

If a tier requires a tool and the tool is not actually used in the execution path and artifacts, the result is `diagnostic_only`.

## 9. Bottom line

The real system stack is not just:
- z3
- PyG
- clifford
- TopoNetX

It is:
- owner stack for contracts, artifacts, and fail-closed promotion
- proof stack for admissibility and synthesis/refinement
- geometry stack for full nested carrier richness
- topology-pressure stack for constraint narrowing
- negative/branch stack for anti-narrative pressure

The strongest fresh additions now are:
- `cvc5`
- `sympy`
- `gudhi`

And the key rule remains:
- no tool without a named job
- no promotion without required tool use
