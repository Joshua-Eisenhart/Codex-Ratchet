# finite_probe_behavioral_object_engine_v1

Preregistered scratch-diagnostic benchmark for learned probe-relative object
equivalence on held-out elementary-cellular-automaton action families.

## Primary Object

The object is an exact behavioral equivalence class, not a neural label. Two
finite ring states are equivalent only when the frozen probes cannot
distinguish them after any admitted action history through stable partition
refinement. The neural lane predicts this relation; it cannot define or certify
it.

## What V1 Repairs

V0 trained on one representative from every cyclic orbit and tested only on
rotated presentations of those same objects. V1 instead freezes all 88 ECA
reflection/conjugacy symmetry orbits, assigns complete orbits to train,
validation, or test, and prohibits any rule or symmetry-relative rule from
crossing the split.

Fourteen primary test rule pairs are unseen action families. Two additional
test pairs have exact stable-partition hashes excluded from both train and
validation. These are structural-holdout probes, not enough by themselves for
a general-perception claim.

## Engine Roles

- Julia independently constructs exact transitions, stable partitions,
  quotient receipts, and graph controls.
- JAX x64 independently exhausts the frozen fixtures and computes exact
  baselines and mutation controls.
- PyTorch/PyG learns a shared six-step refinement update on 4096-node ordered
  state-pair graphs. It sees probe equality and action-successor edges, never
  exact class IDs or history fingerprints.
- The controller reconstructs the split and object independently, recomputes
  metrics from raw predictions, attacks the receipts, and owns the ceiling.

No engine may read another engine's result.

## T9 Correction

The old engine-removal gate was circular: assigned work disappeared when its
assigned runtime was deleted. That demonstrates orchestration dependency, not
unique intelligence.

V1 replaces it with counterfactual evidence contribution and adaptive
replaceability. Runtime deletion must allow remaining runtimes to reimplement
the role under frozen interfaces and resource bounds. T9 reports a vector:

```text
role_contribution
runtime_replaceability
resource_advantage
diversity_gain
claim_ceiling
```

Absolute runtime-language uniqueness is not an admissible result for this
finite computable battery.

## Frozen Boundary

The object card and specification were validated and hashed before builder
source existed. A failed metric cannot be repaired by lowering thresholds or
reusing the exposed test split. Such a change requires a new sim version.

## Ceiling

Even a complete green run can support only bounded behavioral-equivalence
prediction on the frozen ECA suite. It cannot earn the sixteen-by-four QIT
schedule, four substages, unique engine personalities, general perception,
MMMs, ontology admission, a cross-domain attractor, Axis0, physics, life, or
consciousness.
