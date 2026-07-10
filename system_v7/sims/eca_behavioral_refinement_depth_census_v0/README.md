# ECA Behavioral Refinement Depth Census V0

This scratch-diagnostic packet asks a narrow foundation question before another
learned object-engine attempt: how many *strict* partition refinements are
actually required by the finite ECA carrier?

For periodic binary rings of sizes 6, 7, and 8, the primary census covers all
32,640 unordered distinct pairs of elementary cellular-automaton rules. The
initial probe is the ordered pair

```text
(Hamming weight, periodic domain-wall count)
```

and refinement is

```text
P_(d+1)(x) = canon(P_d(x), P_d(T_a(x)), P_d(T_b(x))).
```

`strict_refinement_depth` is the number of rounds in which the partition
changes. `first_equality_round` is one greater. The two fields are kept
separate because V1's JAX and Julia lanes used different meanings for the word
"depth," which made a depth-one benchmark look deeper than it was.

## Engine Contract

- Julia independently constructs the exact full-state ledger.
- JAX x64 independently exhausts the same full-state universe in compiled
  batches.
- A controller must compare every pair record, transition hash, partition hash,
  and trajectory before the census can close.
- PyTorch has no role in the census because there is nothing to learn here.

Neither engine may read the other's result. Matching aggregate depth
histograms is insufficient: V1 already demonstrated that equal partition hashes
can conceal a left/right transition-convention disagreement.

## Exploratory Boundary

An uncommitted JAX scout selected the carrier range and reported maximum strict
depths 3, 4, and 6 for rings 6, 7, and 8. Those values are hypotheses until the
independent ledgers and controller agree. Any later benchmark using the deepest
fixtures must disclose that the depth census exposed them; it cannot call them
an untouched hidden test set.

## Ceiling

A green census can establish only an exact finite, probe-relative depth map on
this ECA family. It cannot establish learned perception, a universal attractor,
QIT engine personalities, four substages, the 64-stage schedule, MMMs, ontology
formation, physics, life, or consciousness.
