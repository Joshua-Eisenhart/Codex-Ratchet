# Fabrication Audit

```yaml
found_fabrication_in_exact_census: false
learned_v2_admission: blocked
accepted_ceiling: exact finite full-state N9 ECA refinement-depth census only
```

## Verified Exact Core

- The frozen spec and object-card hashes match the preregistration receipt.
- Commit `c3d53e6644209f38c33f04dd0aec8cdd4cd44932` contains the frozen packet
  without either builder source.
- Fresh Julia and JAX runs independently cover the exact lexicographic 32,640
  rule-pair universe.
- All twelve required fields agree for every record.
- Maximum strict depth is ten; no result-selected fixture subset defines the
  primary claim.
- Action-swap, carrier symmetry, mutation, pair-duplication, and source-hash
  controls are live.

## Rejected Implementation

An intermediate JAX builder sorted the two action-successor labels inside each
state signature. That would have changed the frozen object by merging states
whose `A` and `B` futures were exchanged. It was interrupted before the accepted
run, replaced by ordered `(current,A-successor,B-successor)` signatures, checked
against V0 fixtures, and the invalid result overwritten.

## Downstream Gate Defect

The frozen V2-admission section names a decisive state-pair subset and an MCC
threshold but does not explicitly bind whether MCC is computed on that subset
or the full fixture.

- Full-fixture depth-six macro MCC is `0.9709778575`, which fails the `<=0.35`
  threshold and shows shallow predictions dominate the complete target.
- Decisive-subset depth-six predictions are constant-positive, producing
  conventional MCC `0`; this passes numerically but carries no discrimination.

The controller reports both. It does not select the favorable interpretation.
Metric-scope ambiguity is itself a blocking gate, so no learned V2 card or
training run is admitted.

This is a preregistration-design defect, not fabrication in the exact N9 census.
It requires a new benchmark version, not an edit to the frozen spec.

## Lev Boundary

Lev emitted matched start/completion events and executed the accepted JAX source
through a frozen local-process allowlist. Raw temporary runtime artifacts were
removed after a bounded durable receipt was extracted. The installed Lev target
was dirty and older than `lev-main`; the receipt proves executor behavior only.

## Rejected Claims

- refinement depth is not an entropy gradient;
- depth ten is not ten QIT stages or substages;
- Julia/JAX parity is not runtime non-substitutability;
- the exact object factory is not a learned perception engine;
- the finite ECA tail is not a universal attractor basin;
- no MMM, ontology, Axis0, physics, life, or consciousness claim moves.
