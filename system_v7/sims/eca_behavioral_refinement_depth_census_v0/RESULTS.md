# Results

## Verdict

`EXACT_CROSS_RUNTIME_FINITE_ECA_REFINEMENT_DEPTH_CENSUS_N6_TO_N8`

Julia and JAX independently enumerated all 32,640 unordered distinct ECA rule
pairs on each of the three full-state periodic carriers. The controller compared
97,920 pair records field by field. There were zero disagreements in rule order,
strict depth, first equality round, class-count trajectory, surviving ordered
state-pair trajectory, stable class count, compact partition hash, or exact
transition-pair hash.

| Ring | States | Depth 0 | Depth 1 | Depth 2 | Depth 3 | Depth 4 | Depth 5 | Depth 6 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 6 | 64 | 120 | 26,898 | 5,518 | 104 | 0 | 0 | 0 |
| 7 | 128 | 120 | 21,642 | 9,342 | 1,496 | 40 | 0 | 0 |
| 8 | 256 | 120 | 2,328 | 21,172 | 8,348 | 592 | 76 | 4 |

The four deepest size-8 witnesses are `(19,35)`, `(19,49)`, `(55,59)`, and
`(55,115)`. Each requires six strict refinements before the first unchanged
round.

## Audit Event

The first full-ledger comparison was red despite matching histograms. Three
serialization differences affected every fixture:

- JAX retained the duplicate first-equality observation in its trajectories;
  Julia recorded strict-change observations only.
- JAX hashed minimum-representative labels; Julia hashed compact first-seen
  labels.
- The engines used different transition-pair delimiters.

The source contract was repaired and both engines rerun. This matters because
V1 previously showed that matching partition summaries can conceal a transition
orientation disagreement.

## Controls

- Both engine receipts are internally green and declare no peer-result reads.
- Exact transition-pair hashes agree on all 97,920 fixtures.
- Exact compact partition hashes agree on all 97,920 fixtures.
- The controller detects injected depth, trajectory, partition-hash, and
  transition-hash corruptions.
- The Python sim-contract linter reports zero violations for the JAX and
  controller lanes.

## Meaning

The finite carrier contains a real hierarchy of probe-relative identity depth;
it is not uniformly a one-round construction. Increasing the carrier from 64 to
256 states exposes progressively deeper refinement tails under the same probe
and action family.

This is an exact finite census, not evidence that a neural engine discovered the
recurrence. The census also exposed every deepest fixture, so those witnesses
cannot later be described as a hidden or untouched benchmark.

## Ceiling

Earned: exact finite ECA refinement-depth structure on rings 6 through 8 under
the frozen Hamming-weight/domain-wall probe.

Not earned: learned perception, causal learning, runtime non-substitutability,
unique engine personality, four substages, the 16-by-4-by-2 schedule, QIT
promotion, MMMs, ontology admission, a universal attractor, physics, life, or
consciousness.
