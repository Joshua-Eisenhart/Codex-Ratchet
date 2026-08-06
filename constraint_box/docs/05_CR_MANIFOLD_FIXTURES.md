# CR manifold fixtures and test program

This document describes proposed uses of the simulation estate. It is not a
canonical layer ladder.

## Candidate dependency graph

The safest current representation is a directed acyclic graph with branches,
not a single numbered staircase:

```text
finite distinctions -> finite quotient / extension fibres
        |                         |
        v                         v
finite histories --------> density-operator carrier (candidate)
                                  |
                      +-----------+-----------+
                      |                       |
                 pure branch             mixed branch
                      |                       |
                 Hopf branch            purification geometry
                      \                       /
                       +-- subsystem cuts --+
                                |
                        correlation graphs
                                |
                      channels / instruments
                                |
                      classical record branch
                                |
                  compatible whole-state assembly

graded/chiral and exceptional-algebra branches attach conditionally where
their additional operations have a discriminator; they are not silently
inserted into every path.
```

## Alternative orders that must remain testable

| Rival | Question | Bounded discriminator |
|---|---|---|
| set support before density rank | can \(H_0(\mathcal H)\) be defined without a probability carrier? | compare set and operator fixtures without identifying them |
| density carrier before complex amplitudes | do demanded distinctions require complex phases? | real versus complex tomography fixture |
| subsystem cut before Hopf structure | does the cut force Schmidt data before a torus/holonomy description? | compare reconstruction loss and missing observables |
| pure and mixed as parallel branches | does one really extend the other for the active demand? | Uhlmann/Fubini–Study limiting fixture |
| chiral branch before process order | does grading add a witness beyond channel noncommutation? | graded pinching versus sign-flip control |
| exceptional algebra installed late | is non-associativity demanded by a measured associator? | explicit bracketed associator negative and positive fixtures |
| record branch after instruments | can records be defined without an instrument? | measurement-to-record and metadata-stripping fixture |

## Engine work

The two engines, four cyclic traversals, and sixteen stages should be encoded
as finite process maps attached to `PROC`, with their carrier and map types
declared explicitly. Traversals are cycles: their start index may rotate.
A preferred start may be chosen for a scientific-method reading, but that does
not change cyclic order or direction.

Before any stage schedule is treated as load-bearing, the fixture should test:

1. each map is finite and trace preserving where claimed;
2. operator/terrain composition order is explicit;
3. Axis-6 sign/order behavior is represented mathematically, not by a label;
4. unreset handoff across loop boundaries;
5. stage deletion and substitute controls;
6. forward, reverse, and cyclic-rotation schedules;
7. independent runtime parity for the same observable;
8. basin structure, not merely one endpoint;
9. a no-selection contraction control;
10. whole-manifold compatibility after the cycle.

No Jungian, IGT, or thermodynamic analogy belongs inside the formal map name
or formula. Such labels can be carried separately as interpretation metadata.

## Planned fixture sequence

| Phase | Fixture | Minimum tier |
|---|---|---|
| M0 | finite histories, fibres, \(H_0\), history-pair field | S1 |
| M1 | 2×2 density, rank, \(S_0\), \(S_1\), dephasing | S1 + S2 parity |
| M2 | finite constraint graph and relative partition frontier | S1 |
| M3 | one typed channel and flow with mutation controls | S1 + S2 |
| M4 | one four-stage cyclic traversal and rotations | S2 |
| M5 | sixteen-stage dual-engine candidate with deletion witnesses | S2 |
| M6 | PySINDy/PyDMD analysis of retained trajectories | S3 |
| M7 | finite FEP/IGT environment comparator | S3 |
| M8 | CPU/GPU parity and bounded search | S4 |

Each phase creates evidence for the next. None self-promotes a layer.
