# PRO-04: Extended Arithmetic

## Context
CODEX RATCHET ENGINE — QIT framework. Density matrices (ρ) + 4 CPTP operators. The engine derives counting, addition, multiplication, primes from QIT axioms. Missing: division, zero, negation, fractions, order.

## Required Reads
- `system_v4/probes/arithmetic_gravity_sim.py`
- `system_v4/probes/deep_math_foundations_sim.py`

## Build These
1. Division = partial trace (d→d/k, remainder = lost entropy)
2. Zero = I/d (maximally mixed, additive identity: ρ + I/d ≈ ρ)
3. Negation = time-reversal (ρ → ρᵀ), verify: ρ + ρᵀ = 2·Re(ρ)
4. Order = entropy ordering (ρ₁ < ρ₂ ⟺ S(ρ₁) < S(ρ₂))
5. Fractions = reduced density matrices (subsystem = fraction of whole)

## Required Output
Save to `system_v4/probes/`:
- `extended_arithmetic_sim.py`
- `EXTENDED_ARITHMETIC_NOTES.md`
- Run it and include results
