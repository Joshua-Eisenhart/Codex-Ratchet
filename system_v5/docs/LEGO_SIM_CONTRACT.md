# LEGO Sim Contract

Status: working contract
Last verified: 2026-05-01
Purpose: define what every small sim (lego sim) must declare, use, emit, and satisfy before it can count as a real building block in the pre-Axis ladder

This contract exists because the system should be built from small sims as legos.
That only works if each small sim is explicit enough, rich enough, and honest enough to be composed upward later.

---

## 1. Core rule

A small sim is not automatically a valid lego.

A sim counts as a real lego only if it:
- declares its role
- declares its tier
- uses its required tools
- emits its required artifacts
- includes its required negatives
- states its promotion status
- can be consumed by higher sims without smuggling hidden assumptions

If these are missing, the sim is `diagnostic_only`.

---

## 2. Minimal fields every lego sim must declare

Every lego sim must declare at least the following fields.

### Identity
- `sim_id`
- `name`
- `version`
- `tier`

### Purpose and scope
- `purpose`
- `scientific_question`
- `sim_execution_kind`
  - one of:
    - `classical`
    - `nonclassical`
    - `bridge`
- `sim_class`
  - examples:
    - `constraint_probe`
    - `carrier_probe`
    - `geometry_probe`
    - `transport_search`
    - `chiral_search`
    - `negative_probe`
    - `placement_probe`

### Constraint and structure context
- `root_constraints_in_force`
- `finite_map`
- `domain`
- `codomain_or_output`
- `carrier_layer`
- `geometry_layer`
- `carrier_realization`
- `peps3d_embedding`
- `spinor_state`
- `quaternion_action`
- `dependency_receipts`
- `downstream_blocks`
- `bridge_layer`
- `cut_layer`
- `law_or_candidate_tested`
- `branch_status_before_run`
- `allowed_claims`
- `promotion_blockers`

### Tooling
- `required_tools`
- `actual_tools_used`
- `proof_surfaces_used`
- `graph_surfaces_used`
- `topology_surfaces_used`
- result key: `tool_manifest`
- result key: `tool_integration_depth`
- result key: `classification`
- classical-baseline result key when applicable: `divergence_log`

Allowed `classification` values:
- `classical_baseline`: baseline/control evidence only.
- `canonical`: admitted local sim evidence, still limited by its stated claim ceiling.
- `tool_lego_fit_probe`: pre-admission tool-lego fit evidence only. This category
  must keep `promotion_allowed: false` or an equivalent claim ceiling in its
  result summary and cannot be cited as canonical, bridge, QIT, GStack, axis, or
  nonclassical admission without a later admitted receipt.

`sim_execution_kind` controls runner admission:
- `classical` sims are baselines/controls and may use graph/proof tools only as baseline or comparison surfaces.
- `nonclassical` sims require the claim-relevant nonclassical stack: PyTorch/PyG for tensor or graph dynamics, Clifford for geometric product/spinor/rotor claims, and z3/cvc5 for structural proof or UNSAT claims.
- `nonclassical` manifold sims additionally require torch-native spinor or spinor-derived density state, quaternionic map/invariant when quaternion language is used, PEPS3D site/bond/face/cell embedding from the first admitted finite carrier/probe step, and explicit NumPy/dense-state/Cartesian adapter blocks.
- `bridge` sims connect a named classical-side baseline to a named nonclassical tool plan and remain gated until bridge work is explicitly opened.

### Inputs
- `required_inputs`
- `data_or_artifact_dependencies`

### Negatives
- `required_negatives`
- `negatives_run`
- `kill_conditions`

### Outputs
- `required_artifacts`
- `artifacts_emitted`
- `witness_trace_id`
- `result_summary`

### Evaluation
- `pass_rule`
- `fail_rule`
- `promotion_status`
- `eligible_consumers`
- `blocked_consumers`

---

## 3. Required field meanings

### `tier`
Which pre-Axis tier the sim belongs to.
Examples:
- 0 root constraints
- 1 finite carrier
- 2 geometry
- 3 transport
- 4 differential/chirality
- 5 negatives
- 6 placement/pre-entropy
- 7 axis-entry

### `carrier_layer`
Which carrier level the sim is actually operating on.
This must not be hidden.
Examples:
- `S3`
- `nested_hopf_tori`
- `clifford_restricted_layer`
- `left_right_weyl`
- or explicit composite/nested layer description

### `finite_map`
The exact finite map, transition, quotient, or invariant under test.
This field must not contain only a label such as `manifold`, `layer`,
`quaternion shell`, `terrain`, `flux`, or `Axis0`.

### `domain`
The finite input object. For nonclassical manifold work, this must include the
active finite probes/effects/operators/paths and the PEPS3D carrier anchors used
by the claim.

### `codomain_or_output`
The finite output object, quotient, invariant, or blocked readout produced by
the map.

### `carrier_realization`
The concrete computation substrate. Nonclassical manifold claims must name
torch tensors and the spinor/quaternion/PEPS3D realization. Scalar rows, dense
full-state closure, NumPy bridges, and label-only tensors must be fenced as
controls/adapters, not admitted carriers.

### `peps3d_embedding`
How the object is anchored in finite PEPS3D sites, bonds, faces, or cells.
For 64-substage work, this must show each substage as a local cell/tensor/channel
action or an explicit projection from a richer PEPS3D cell carrier to the
16-stage placement quotient.

### `spinor_state`
The torch-native spinor or spinor-derived density object. Missing spinor state
blocks nonclassical manifold admission.

### `quaternion_action`
The explicit quaternionic map/invariant and its control. If quaternion language
is not used, this should be `not_applicable`. If quaternion language is used
without a map/invariant, the sim is `diagnostic_only` or `broken`.

### `dependency_receipts`
The lower receipt paths required by this sim. Empty dependency receipts are only
allowed for true root/finite-carrier probes.

### `downstream_blocks`
Consumers that must not cite this sim. For foundation/manifold work, default
blocks include flux, Xi, Phi0, Axis0, bridge, basin, and physics unless the sim
explicitly earns a narrower consumer.

### `geometry_layer`
Which geometry surface is being directly tested.
This is distinct from broad carrier names when needed.

### `bridge_layer`
What bridge family, bridge object, or bridge status is involved.
Examples:
- `none`
- `Xi_hist`
- `Xi_ref`
- `shell_bridge_family_open`
- `bridge_not_applicable_at_this_tier`

### `cut_layer`
What cut family or cut status is involved.
Examples:
- `none`
- `history_window_cut`
- `shell_interior_boundary_cut`
- `generic_A|B_only`
- `cut_not_applicable_at_this_tier`

### `law_or_candidate_tested`
The exact law, candidate family, or structural claim under test.
No vague descriptions.

### `allowed_claims`
What this sim is allowed to support if it passes.
Examples:
- local geometry witness only
- bridge discriminator only
- control-only negative
- executable bridge support
- doctrine-facing support but not closure

### `promotion_blockers`
What still blocks this sim from stronger promotion.
Examples:
- missing negatives
- missing bridge layer
- cut not fixed
- graph writeback absent
- proof pressure absent
- pointwise only, not doctrine-closing

### `promotion_status`
Must be one of:
- `admitted`
- `keep_but_open`
- `audit_further`
- `diagnostic_only`
- `broken`

These are internal sim-role / promotion states. They are not the public repo truth labels.
For controller closeout and repo reporting, use only:
- `exists`
- `runs`
- `passes local rerun`
- `canonical by process`

A sim can be internally `keep_but_open` while the file itself only has the public status `runs` or `passes local rerun`. Do not collapse those two vocabularies.

### `eligible_consumers`
Higher-level sims or packets that are allowed to use this sim as input.

### `blocked_consumers`
Higher-level sims or packets that are not allowed to treat this sim as supporting evidence.

---

## 4. Tool declaration rules

### 4.1 Required tools must be explicit
If a sim requires tools from the contract stack, they must be listed.

Examples:
- `z3`
- `cvc5`
- `sympy`
- `hypothesis`
- `pytest`
- `networkx`
- `PyG`
- `TopoNetX`
- `clifford`
- `pyquaternion`
- `gudhi`

### 4.2 Required tools must actually be used
A tool listed as required must appear in the real execution path.
If the tool is listed but not used, the sim is `diagnostic_only`.

### 4.3 Underpowered tool use blocks promotion
If the tier requires proof/graph/topology richness and those surfaces are absent, the sim cannot promote.

---

## 5. Negative-suite rules

### 5.1 Every real lego sim needs explicit negatives when the tier requires them
Examples of required negative families:
- flattened carrier
- reduced geometry
- no chirality
- loop-law swap
- commutative collapse
- fake transport activity
- fake chiral law
- counterfeit history

### 5.2 Negatives must be named
The contract must say which negatives are required and which were actually run.

### 5.3 Negative results must be artifacted
Not just reported in prose.
They must appear in emitted artifacts and witness traces.

### 5.4 No negatives means no promotion
If the sim is supposed to support lower-tier admission and lacks negatives, it is not a valid lego.

---

## 6. Artifact rules

Every lego sim must emit enough artifacts to be auditable.

Minimum artifact classes:
- result artifact
- witness trace
- tool-usage evidence
- classification summary

Possible artifact examples:
- JSON result packet
- graph artifact
- witness/event log
- validator result
- negative result packet
- topology-pressure artifact

If required artifacts are missing, the sim is under-specified.

---

## 7. Witness trace rules

Every nontrivial lego sim should have a witness trace or event trace.

The trace should support:
- what inputs were used
- what transforms were applied
- what negatives were run
- what branch or candidate status changed
- what final classification was produced

A trace is especially important when the sim supports:
- promotion
- branch narrowing
- kill classification
- higher-level composition

---

## 8. Composition rules

### 8.1 A lego sim must be composable
A higher sim should be able to consume a lego sim without guessing hidden assumptions.

### 8.2 No hidden dependencies
If a lego sim silently depends on:
- unresolved branches
- missing geometry layers
- absent rich tooling
- prose-only assumptions
then it is not safely composable.

### 8.3 Explicit consumer rules
The contract must state:
- who may consume this sim
- who may not
- whether the sim supports executable bridge use, doctrine-facing cut use, control-only use, or discriminator-only use

### 8.4 No packet-score smuggling
A higher-level packet may not use a lower sim just because a broad packet score is green.
The lower sim’s real role and status must be explicit.

### 8.5 No fake winner collapse
If executable winners, doctrine-facing winners, and pointwise discriminators differ, the contract must keep them distinct.
No higher consumer may collapse them into one fake closure object.

---

## 9. Promotion rules

### 9.1 A lego sim starts as `diagnostic_only`
A sim should be considered `diagnostic_only` by default until it earns a stronger internal promotion state.

### 9.2 Promotion requires:
- required fields declared
- required tools actually used
- required negatives run
- required artifacts emitted
- witness trace present
- no hidden geometry/carrier flattening
- no blocked downstream use

### 9.3 Reasons for `keep_but_open`
Use `keep_but_open` when:
- the sim is real and useful
- a branch survives
- closure is not yet justified
- the output should be kept for later composition

### 9.4 Reasons for `audit_further`
Use `audit_further` when:
- the sim may be useful
- but fields/tools/negatives/artifacts are incomplete or unclear

### 9.5 Reasons for `diagnostic_only`
Use `diagnostic_only` when:
- the sim is underpowered
- flattened
- missing rich tooling required by the tier
- missing negatives
- missing artifacts
- useful only as a local probe

### 9.6 Reasons for `broken`
Use `broken` when:
- the execution path is invalid
- required writeback/proof path failed
- the sim false-greens
- the outputs are untrustworthy

---

## 10. Tier-specific tightening

## Tier 0–1 legos
Must be explicit about:
- root constraints
- admissibility
- finite witness structure
- domain/codomain finite map
- PEPS3D carrier admission if the lego is nonclassical manifold work

## Tier 2 legos
Must be explicit about:
- carrier ladder
- geometry richness
- reduced-geometry negatives
- torch-native spinor state
- nested Hopf torus index/projection when Hopf language is used
- quaternion map/invariant and controls when quaternion language is used
- PEPS3D site/bond/face/cell anchor

## Tier 3 legos
Must be explicit about:
- candidate-law family
- proof/synthesis pressure
- transport negatives
- noncommuting/order-sensitive witness on the finite carrier
- blocked downstream consumers

## Tier 4 legos
Must be explicit about:
- chirality richness
- differential candidate family
- no-single-law or fake-law kills
- graph/tensor support if required
- sheet/terrain/substage labels translated into explicit finite maps before
  they are used as computation-layer objects

## Tier 5 legos
Must be explicit kill surfaces.

## Tier 6 legos
Must be explicit about placement and downstream relation.
Placement means a finite carrier cell/tensor/channel action, not only a token
row. A stage/substage schedule without PEPS3D-carried local state/action
evidence is scaffold-only.

## Tier 7 legos
Should generally be blocked unless lower tiers justify them.
Flux, Xi, Phi0, Axis0, basin, bridge, and physics consumers remain blocked
unless the lower dependency receipts are cited and current.

---

## 11. Standard template

A lego sim should be representable in a structure like:

```yaml
sim_id: ...
name: ...
version: ...
tier: ...
purpose: ...
scientific_question: ...
sim_execution_kind: classical | nonclassical | bridge
sim_class: ...
root_constraints_in_force: [...]
finite_map: ...
domain: ...
codomain_or_output: ...
carrier_layer: ...
geometry_layer: ...
carrier_realization: ...
peps3d_embedding: ...
spinor_state: ...
quaternion_action: ...
dependency_receipts: [...]
downstream_blocks: [...]
law_or_candidate_tested: ...
branch_status_before_run: ...
required_tools: [...]
actual_tools_used: [...]
proof_surfaces_used: [...]
graph_surfaces_used: [...]
topology_surfaces_used: [...]
required_inputs: [...]
data_or_artifact_dependencies: [...]
required_negatives: [...]
negatives_run: [...]
kill_conditions: [...]
required_artifacts: [...]
artifacts_emitted: [...]
witness_trace_id: ...
result_summary: ...
pass_rule: ...
fail_rule: ...
promotion_status: ...
eligible_consumers: [...]
blocked_consumers: [...]
```

---

## 12. What this contract prevents

This contract is designed to stop:
- toy-flat sims being used as real evidence
- graphless/scalar-only “rich geometry” claims
- proofless candidate-law claims
- packet-score smuggling
- hidden unresolved branch assumptions
- premature Axis-entry support
- narrative-only classification

---

## 13. Relation to the broader plan

This contract is the operational bridge between:
- the QIT engine proto ratchet plan
- the nonclassical tool plan
- the bounded Hermes ingestion protocol

It makes “small sims as legos” concrete enough to implement.

---

## 14. Current best summary

A real lego sim is a small sim that:
- has explicit tier and role
- uses the required tools
- runs the required negatives
- emits the required artifacts
- carries a witness trace
- has a clear promotion status
- can be safely composed upward

If it cannot do those things, it is not a real lego yet.
