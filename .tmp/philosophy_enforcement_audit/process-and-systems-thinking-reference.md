---
title: Process And Systems Thinking Reference
created: 2026-04-09
updated: 2026-04-16
type: concept
tags: [reference, formal, harness, language, constraints]
sources:
  - Alfred North Whitehead, Process and Reality (1929)
  - Carlo Rovelli, Relational Quantum Mechanics (1996)
  - W. Ross Ashby, An Introduction to Cybernetics (1956)
  - Saunders Mac Lane, Categories for the Working Mathematician (1998)
  - James Ladyman and Don Ross, Every Thing Must Go (2007)
framing: current
---

# Process and Systems Thinking Reference

This is a support/reference page for translation and routing. It helps stabilize language around process, relation, and systems structure, but it is not itself a provenance source or a proof surface.

Use the process-metaphysics material here as support vocabulary and comparison pressure, not as a front-door primitive ontology. Systems thinking is useful here because it emphasizes structure and interaction over isolated components, but the live system should still route primitive claims through the constraint/distinguishability surfaces rather than through this page alone.

## Core Positions

### Process Philosophy (Whitehead)

**Actual occasions:** In Whitehead's own framework, the fundamental units of reality are "actual occasions of experience" — momentary events of becoming, not enduring substances. What we call "objects" are patterns of repetition across occasions.

**Prehension:** Each occasion "prehends" (grasps, takes account of) other occasions. Relations are primary; relata are abstractions from relations.

**Concrescence:** Each occasion synthesizes its prehensions into a unified "satisfaction." The becoming IS the being — there is no static endpoint.

**Applied to the system:** This is best used as translation/comparison language: states can be compared to momentary snapshots of what survived the current constraint set, operators can be compared to how one state takes account of another, and the constraint cascade can be compared to a synthesis of multiple constraints into a unified admissible set. Do not let that translation quietly replace the system's own tighter support-first and probe-relative doctrine.

### Relational Quantum Mechanics (Rovelli)

**Core claim:** Quantum states are not descriptions of individual systems. They are descriptions of relationships between systems. The state of S relative to O is different from the state of S relative to O'.

**Applied:** A density matrix ρ is not "the state of the system." It is the state of the system relative to the observer/cut/probe that prepared or measured it. Change the cut → change the state.

### Systems Theory (Bertalanffy, Ashby)

**Emergence:** System-level behavior cannot be predicted from component properties alone. The interactions create new structure.

**Requisite variety:** A controller must have at least as many states as the system it controls (Ashby's Law). Applied: the constraint set must be rich enough to distinguish the surviving families.

**Applied to the system:** The 28 families are emergent under the full constraint set — they do not exist under weaker constraint sets. The coupling program tests emergence directly.

### Category Theory as Process Language

**Objects as nodes, morphisms as processes:** In category theory, objects are defined only by their incoming and outgoing morphisms. An object without morphisms is invisible.

**Functors as structure-preserving maps:** A functor between categories preserves the process structure while changing the "stuff." Applied: the PyTorch migration is a functor from numpy-processes to torch-processes.

**Natural transformations as systematic comparisons:** A natural transformation compares two functors. Applied: comparing numpy and PyTorch implementations tests whether the functor preserves structure.

## Anti-Object Patterns

### Pattern 1: Process-First Description

**Object-first:** "A density matrix is a positive semidefinite operator with trace 1."
**Process-first:** "A density matrix is the result of applying a preparation process to a carrier system and then tracing out the environment."

The process-first version names what produced it, not what it "is."

### Pattern 2: Interaction-First Description

**Component-first:** "The system has 28 families with specific properties."
**Interaction-first:** "Under the constraint set {L0, ..., L7}, the interactions between states, operators, and probes produce 28 distinguishable equivalence classes."

The interaction-first version describes the relations that produce the count, not the things being counted.

### Pattern 3: State-As-Frozen-Process

**Static:** "This is a pure state."
**Process-as-frozen:** "This state results from a preparation process that maximized coherence relative to the reference basis. Under dephasing, the process that produced it would produce a different state."

Every state is a frozen process. Change the process → change the state.

## Connection to This System

### The Computational Graph IS the Process

Rule 9 of [[enforcement-and-process-rules]]: the computational graph is the ratchet. This is process metaphysics operationalized. The forward pass is the process of becoming. The backward pass is the process of selection. The graph topology is the process structure.

### Constraint Cascading as Process

The cascade L0-L7 is not a ladder of objects. It is a process of progressive selection. Each level is a process that transforms the admissible set. The result (28 families) is not a discovery of pre-existing objects — it is the output of a specific process.

Support-page fence:
- keep this as a process-first translation aid
- do not read it as permission to import Whitehead, systems theory, or generic process metaphysics as primitive live ontology
- when the question is what the system itself treats as primitive, route back to the constraint/distinguishability and support-first doctrine pages

### Coupling as Interaction

The coupling program (shell-local → pairwise → coexistence → emergence) is explicitly interaction-first. It asks: what happens when processes interact? Not: what properties do objects have?

## Key Results

1. **Whitehead's fallacy of misplaced concreteness:** treating abstractions as if they were concrete entities. The system guards against this by using admissibility language, not existence language.
2. **Ashby's Law of Requisite Variety:** the constraint set must be rich enough to distinguish the target structures. The 28 families are the variety required.
3. **Category theory's Yoneda lemma:** an object is completely determined by its relationships to all other objects. The system's relational-first approach is Yoneda operationalized.

## Related Pages

- [[process-philosophy-and-relational-physics]] — Whitehead, relational QM, structural realism
- [[nominalist-translation-rules]] — Rule 3 (essence → probe-relative)
- [[llm-bias-inversion-rules]] — Inversion 5 (object-first → relation-first)
- [[enforcement-and-process-rules]] — Rule 9 (graph IS the ratchet)
- [[pytorch-ratchet-build-plan]] — the computational claim
- [[shell-local-to-coupled-program]] — coupling as interaction testing
- [[topos-quantum-mechanics-reference]] — context-dependent truth
- [[research-support-bibliography]] — external support cluster

## Sources

- Whitehead. "Process and Reality." Free Press, 1929.
- Rovelli. "Relational Quantum Mechanics." Int. J. Theor. Phys. 35, 1637 (1996).
- Ashby. "An Introduction to Cybernetics." Chapman & Hall, 1956.
- Mac Lane. "Categories for the Working Mathematician." Springer, 2nd ed., 1998.
- Ladyman, Ross. "Every Thing Must Go." Oxford University Press, 2007.
