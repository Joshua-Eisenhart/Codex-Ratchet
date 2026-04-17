# Differential Geometry / Fiber Bundles Reference

Date: 2026-04-05
Status: Reference — exact-term support for geometry buildup, transport, and spinorial structure

---

## Core idea

This reference supports the system’s geometry chain with established differential-geometry terms.

The system’s best exact support comes from:
- manifold
- submanifold
- tangent bundle
- fiber bundle
- principal bundle
- associated bundle
- connection
- spin structure
- spinor bundle / spinor
- Hopf fibration

These are standard mathematical objects. They can support the system’s geometry language without turning the system into a metaphor.

---

## Exact fit terms

### Manifold
- A space locally modeled on R^n.
- Good fit for the admissible state space or a constrained geometry carrier.

### Submanifold
- A manifold sitting inside another manifold.
- Good fit for constraint surfaces or regular admissible loci.

### Tangent bundle
- The collection of all tangent spaces over a manifold.
- Good fit for local directions, infinitesimal deformations, and allowed motions.

### Fiber bundle
- A space that locally looks like base × fiber.
- Good fit for layered geometry where one structure lives over another.

### Principal bundle
- A bundle with a group action on the fibers.
- Good fit for symmetry and gauge-like structure.

### Associated bundle
- A bundle built from a principal bundle and a representation.
- Good fit for carrying fields such as vectors, tensors, or spinors.

### Connection
- A rule for comparing fibers at nearby points.
- Good fit for transport, propagation, and compatibility along a surface.

### Spin structure
- A lift of an orthonormal frame bundle to Spin(n) when the obstruction vanishes.
- Required if the system wants spinors as global geometric objects.

### Spinor / spinor bundle
- Spinors are sections of a spinor bundle.
- Good fit for chiral or fermionic language when the dimension and topology permit it.

### Hopf fibration
- The canonical fibration S^1 -> S^3 -> S^2.
- Good fit as a concrete example of nontrivial bundle structure.

---

## How to map into system language

Useful translations:
- geometry buildup -> induced geometry / constrained geometry / bundle construction
- carrier layer -> manifold or base space
- transport rule -> connection
- symmetry data -> principal bundle
- field data -> associated bundle
- spin carrier -> spin manifold / spin bundle context
- bridge -> bundle map / transport rule / connection-induced correspondence
- cut family -> family of submanifolds or partitions, if explicitly defined

---

## Mismatch notes

- “Geometry buildup” is not a standard term.
  - Use induced geometry, geometric reduction, or bundle construction.
- “Bridge Xi” is not a standard term.
  - It needs a definition: bundle map, transport operator, or channel-like correspondence.
- “psi_L / psi_R” is only standard in a chiral setting.
  - In 3D, a left/right Weyl split is generally not the right language.
- “candidate geometry” needs a precise meaning.
  - Use candidate manifold, candidate metric, or candidate bundle structure.

---

## Best exact fit summary

If the system wants a clean external geometry spine, use:
1. manifold / submanifold
2. tangent bundle
3. fiber bundle / principal bundle
4. connection
5. spin structure / spinor bundle
6. Hopf fibration as the canonical example

This is the cleanest exact support for the system’s geometry chain.
