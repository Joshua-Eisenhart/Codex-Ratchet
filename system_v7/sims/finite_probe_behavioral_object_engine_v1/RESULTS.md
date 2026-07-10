# Results

## Exact Core

The preregistration validator reconstructs 88 ECA reflection/conjugacy orbits
and verifies the frozen fixture counts:

```text
train:                    64
validation:               16
test primary:             14
test structural holdout:   2
```

Julia and JAX independently reconstruct all 96 exact stable behavioral
partitions. Every quotient is congruent. The maximum observed stable depth is
three in the JAX closure receipt, corresponding to at most two strict changes
before its explicit convergence check.

The controller found and repaired a real cross-runtime defect before accepting
parity: Julia had reversed the left/right ECA neighborhood convention. The
partition classes happened to remain equal while induced quotient transitions
differed. Exact parity now includes transition maps, not only partition hashes.

## Learned Proxy

The three-seed PyG ensemble is perfect on the fourteen held-out-rule fixtures
and the two structural-holdout fixtures:

```text
ensemble MCC:              1.0
balanced accuracy:         1.0
positive recall:           1.0
false-positive rate:       0.0
partition ARI:             1.0
partition normalized VI:  ~0.0
```

This does not pass the preregistered learning battery:

```text
individual-seed MCC:       [0.0, 0.0, 0.9366614989322403]
shuffled-label MCC:        0.9627052748084781
optimizer-erased MCC:      0.8311452924819083
```

The architecture starts from probe equality and routes exact paired successors
through the same recurrence used by the object definition. All fixtures are
depth-short. The perfect ensemble is therefore an architecture-installed
finite refinement readout with learned calibration, not earned learned
perception.

## T9

The deletion-only T9 formulation is withdrawn. Runtime names are not unique
intelligences. The replacement vector remains unearned:

```text
role_contribution:       measured only in assigned roles
runtime_replaceability:  unearned
resource_advantage:      unearned
diversity_gain:          unearned
claim_ceiling:           no runtime non-substitutability
```

## Validation

The independent controller passes artifact validation and rejects four
in-memory coherent corruptions:

- symmetry leakage;
- source-hash substitution;
- raw-metric rewriting;
- red-ceiling removal.

Final state:

```text
artifact_validation_all_pass: true
all_scientific_gates_pass:    false
accepted_claim_label:         EXACT_CROSS_RUNTIME_CORE_WITH_LEARNING_GATES_RED
```

No QIT schedule, four-substage, unique-personality, general-perception, MMM,
ontology, Axis0, physics, life, or consciousness claim is supported.
