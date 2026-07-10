# Results

## Exact Verdict

```text
EXACT_CROSS_RUNTIME_FINITE_ECA_REFINEMENT_DEPTH_CENSUS_N9
```

Julia and JAX independently enumerated all 32,640 unordered distinct ECA rule
pairs on all 512 periodic nine-bit states. The controller compared every
required field in every pair record. No field disagreed.

| Strict depth | Pair count |
|---:|---:|
| 0 | 120 |
| 1 | 1,886 |
| 2 | 7,570 |
| 3 | 15,592 |
| 4 | 5,448 |
| 5 | 1,530 |
| 6 | 318 |
| 7 | 136 |
| 8 | 0 |
| 9 | 24 |
| 10 | 16 |

The maximum strict depth rises from `3,4,6` on carriers N6-N8 to `10` on N9.
This is an observed finite sequence, not a fitted growth law.

The 16 depth-ten pairs occupy four simultaneous reflection/conjugacy pair
orbits with canonical keys `2,60`, `2,102`, `8,153`, and `8,195`.

## Cross-Runtime Closure

The controller requires the exact lexicographic pair universe, preventing a
coordinated duplicate or omission from passing positional comparison. Across
all 32,640 records, Julia and JAX agree on:

- rule identities and order;
- strict depth and first equality round;
- class-count and surviving-ordered-pair trajectories;
- stable class count;
- compact partition and exact transition-pair hashes;
- simultaneous pair-orbit key and hidden batch;
- state-pair labels changed after depth six.

Six field mutations plus a duplicate-pair mutation are detected.

The JAX implementation uses ordered `(current,A-successor,B-successor)`
signatures. A pre-run implementation that sorted the two successor components
was rejected because it changed the object by forgetting which action produced
which future.

## Downstream Learned-V2 Gate

```text
INSUFFICIENT_DEPTH_NOVEL_MASS_FOR_LEARNED_V2
```

The depth-novel family-count gates pass:

- 176 fixtures have strict depth at least seven;
- they occupy 44 simultaneous pair-symmetry orbits;
- hidden batches contain 26 and 18 qualifying orbits.

Under the decisive-subset reading, the changed-mass gates pass. Among state pairs still
equivalent after six strict refinements, at least `2.6937%` per qualifying
fixture and `5.3499%` in aggregate change by stability.

Across the whole ordered-pair carrier, those changes are only `0.1166%`.

The frozen spec does not explicitly bind the MCC scope. On the full carrier,
the exact depth-six baseline achieves macro MCC `0.9709778575`, far above the
preregistered maximum `0.35`; a learner could score extremely well without
learning the late refinements. On the decisive subset, the depth-six baseline
predicts one class everywhere and receives conventional MCC `0`, which passes
the threshold vacuously without discriminating anything.

The controller reports both readings and fails closed on the unresolved metric
scope. The separate learned V2 card is not admitted.

The threshold is not lowered and no PyTorch training is run.

## Leviathan Execution

Lev's `createExec` runtime executed the JAX lane through a frozen local-process
allowlist. Matched `exec.started` and `exec.completed` events share execution ID
`04a9a185-488e-4126-921e-c65cd47b2014`; process exit is zero and the scientific
pair-ledger hash matches the direct run.

The active installed Lev checkout was dirty at
`e9a4ba7717dbc35e478b3db737a4d5b752ba8252`. The Lev receipt is executor
provenance only and does not strengthen the scientific result or establish
clean/current Lev readiness.

## Ceiling

Earned: an exact finite N9 probe-relative behavioral-refinement census and a
measured rejection of this particular depth-novel learning benchmark.

Not earned: learned perception, unique runtime intelligence, engine
personalities, QIT stages, four substages, the 16-by-4-by-2 schedule, an entropy
gradient, MMMs, ontology admission, a universal attractor, Axis0, physics, life,
or consciousness.
