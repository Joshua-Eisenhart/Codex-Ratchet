# AGM-10 Phase 5B Stability Read Return

## Stable
- **Bridge Convergence:** The cross-temporal chiral retro-weighted bridge is a mathematical attractor. MI stabilizes within 2-3 engine cycles across all tested tori.
- **Inner/Outer Regime:** High mutual information (~1.82) is extremely robust on standard manifold configurations with near-zero drift after initial settling.
- **Engine Invariance:** Results are consistent across Engine Type 1 and Type 2, verifying the core geometric operators.

## Not stable
- **Clifford Variance:** The Clifford torus exhibits 6x higher variance (Std ~0.25) under random initialization compared to inner/outer tori.
- **Initial Decay:** All configurations show a minor MI drop (~2-5%) between Cycle 1 and Cycle 2 before reaching the fixed-point attractor.
- **Sensitivity:** Bridge "Ic" values for Clifford remain negative or near-zero, indicating that while MI is stable, the information complement is not yet firmly earned in that sector.

## What stability does not prove
- **Doctrine Truth:** Convergence proves the internal consistency of the retrocausal construction but not its alignment with external point-reference Ground Truth.
- **Uniqueness:** The variance in Clifford suggests the search space may contain multiple local attractors rather than a single global maximum.
- **Physicality:** Stability validates the mathematical "stiffness" of the formula but does not verify the underlying entropic assumptions.

## Best next use of this result
- **Phase 5C Pivot:** Stress-test these stable attractors against high-L6 drift to identify the breaking point of the "earned" bridge.
- **Clifford Fencing:** Formalize the Clifford results as a "low-coherence boundary case" in the AXIS0_CLIFFORD_ANOMALY_NOTE.md rather than a failure of the bridge itself.
- **Baseline Lock:** Use the converged MI values (~1.82) as the definitive "earned" benchmark for the Axis 0 construction.
