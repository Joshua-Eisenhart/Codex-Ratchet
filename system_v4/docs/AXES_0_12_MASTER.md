# AXES 0-12 MASTER SPECIFICATION

DATE_UTC: 2026-03-25T13:57:47Z

## Overview
This document specifies the master definitions for all 13 axes (Axes 0-12) of the Ratchet Graph structure. Axes 0-6 represent the canon definitions, while Axes 7-12 are non-canon extensions derived from commutator products of the base generators.

## Core Properties
*   **Natural build order:** 0 → 6 → 5 → 3 → 4 → 1 → 2
*   **Trigrams:** 
    *   `{6, 5, 3}` = Diversifier (30 basins)
    *   `{4, 1, 2}` = Compressor (1 basin)
*   **Lie Closure:** 6 generators → 75-dimensional algebra
*   **Non-commutativity Ranking:** A3 is the master non-commutator
*   **Proof Hygiene:** Non-triviality gates are strictly MANDATORY for all validations

---

## Part 1: CANON DEFINITIONS (Axes 0-6)
*(Referenced from AXES_MASTER_SPEC_v0.2.md)*

### Axis-0: Two-Class Slice
*   **Codomain:** `V₀ = {A0-CLASS-1, A0-CLASS-2}`
*   **Rule:** A two-class partition of the constraint manifold (M) computed from admissible operators.

### Axis-6: Precedence / Composition Sidedness
*   **Codomain:** `V₆ = {UP, DOWN}`
*   **Rule:** Selects which composition order is used when composing admissible operators/channels. (Do not conflate with Axis-4).

### Axis-5: Texture / Generator Algebra
*   **Codomain:** `V₅ = {Line (Partition), Wave (Mixing)}`
*   **Rule:** Partitions the mathematical calculus toolhead into integration (Wave/FeFi) vs differentiation (Line/TeTi) boundaries.

### Axis-3: Type Selection 
*   **Codomain:** `A₃ ∈ {0, 1}`
*   **Rule:** Top-level fork for operator family (e.g., Identity-preservation vs. Phase/Inversion logic). Type-1 vs Type-2 mappings are Engine overlay specifications. The highest non-commutativity ranking (master non-commutator).

### Axis-4: Operator Family / Thermodynamic Optimization
*   **Codomain:** `V₄ = {DEDUCTIVE (FeTi), INDUCTIVE (TeFi)}`
*   **Rule:** Defines the thermodynamic optimization objective and sequence operator constraint. (Deductive: S → 0; Inductive: ΔW → max).

### Axis-1 & Axis-2: Topology4 (The Base Regimes)
*   **Rule:** Axis-1 and Axis-2 are slices whose product defines **Topology4** (four base regimes). Edges/adjacency between bases are derived structure.

---

## Part 2: NON-CANON EXTENSIONS (Axes 7-12)
*(Constructed from commutator products)*

**Note on Dimensional Shifting:** Axis assignments shift with the representation dimension. Variables mapped at dimension `d=4` may map differently in `d=8` and `d=16` variants due to the shifting representation space of the 75-dimensional exterior algebra.

### Axis-7
*   **Construction:** `A7 = [A1, A3]`
*   **Description:** Derived from the commutator of Topology4 partial slice (A1) and the master non-commutator (A3).

### Axis-8
*   **Construction:** `A8 = [A1, A6]` or `[A4, A6]`
*   **Description:** Derived from the commutator of base topology/optimization drive and the composition sidedness (A6).

### Axis-9
*   **Construction:** `A9 = [A3, A6]`
*   **Description:** Commutator product of the top-level type fork (A3) and precedence structure (A6).

### Axis-10
*   **Construction:** `A10 = [A4, A6]` or `[A1, A4]`
*   **Description:** Product interacting thermodynamic optimization (A4) with composition order (A6) or spatial topography (A1).

### Axis-11
*   **Construction:** `A11 = [A2, A6]` or `[A1, A2]`
*   **Description:** Cross-commutator of the topologies or precedence relationships, effectively yielding boundary crossing operators.

### Axis-12
*   **Construction:** `A12 = [A1, A5]` or `[A4, A5]`
*   **Description:** Product of topology/thermodynamics with the texture algebra (A5), differentiating continuous flow vs discrete jumps.
