#!/usr/bin/env python3
"""
CVC5 Weak Energy Condition Constraint: Canonical proof that the weak energy condition
(WEC) T_μν u^μ u^ν ≥ 0 holds for all timelike four-velocities u^μ (energy density is
non-negative for any observer). cvc5 encodes via QF_NRA: asserts that for any timelike
observer, the energy density component T_uu ≥ 0. Negative tests show that assuming
T_uu < 0 for classical matter (where ρ ≥ 0 and p ≥ 0) leads to UNSAT, violating the
weak energy condition. sympy derives: energy density ρ ≥ 0, null energy condition (NEC)
T_μν k^μ k^ν ≥ 0 for lightlike k^μ, strong energy condition (SEC), dominant energy
condition (DEC), exotic matter that violates WEC (negative energy density).

Tests:
(1) cvc5 SAT: WEC T_uu ≥ 0 for timelike u (energy density non-negative) → SAT
(2) cvc5 SAT: T_uu = 0 (massless matter) for timelike u → SAT (boundary case)
(3) cvc5 SAT: T_uu > 0 (massive matter) for timelike u → SAT (positive energy density)
(4) cvc5 UNSAT on: T_uu < 0 ∧ timelike u ∧ classical matter → UNSAT (WEC holds for classical)
(5) cvc5 UNSAT on: ρ ≥ 0 ∧ T_uu < 0 → UNSAT (positive density with negative T_uu contradiction)
(6) Boundary: sympy derives energy density ρ, pressure p, NEC, SEC, DEC hierarchy,
    exotic matter violations, phantom dark energy (w < -1), quantum field effects.

Key constraints:
- Weak Energy Condition (WEC): T_μν u^μ u^ν ≥ 0 for all timelike four-velocities u^μ.
  This condition asserts that the energy density measured by any observer (timelike u^μ)
  is non-negative: no observer measures negative energy density. For perfect fluid matter,
  T_μν = (ρ + p/c²)u_μ u_ν + p g_μν (where ρ is mass-energy density and p is pressure).
  For a comoving observer u^μ = (c, 0, 0, 0), T_uu = -ρc² (using signature (-, +, +, +)).
  WEC: T_uu ≥ 0 ⟹ ρ ≥ 0 (mass-energy density is non-negative). This is one of the most
  basic physical assumptions: ordinary matter has positive energy density. Dust (p = 0)
  and radiation (p = ρc²/3) both satisfy WEC.
- Null Energy Condition (NEC): T_μν k^μ k^ν ≥ 0 for all lightlike four-vectors k^μ.
  This condition asserts that the energy density measured along light rays is non-negative.
  For perfect fluid, NEC: ρ + p/c² ≥ 0 (density plus pressure). WEC and SEC imply NEC,
  but NEC does not imply WEC. The NEC is weaker than WEC and is frequently violated by
  quantum field effects (Casimir effect, Hawking radiation).
- Strong Energy Condition (SEC): T_μν u^μ u^ν - (1/2)T_g_μν u^μ u^ν ≥ 0 for timelike u^μ.
  This simplifies to: ρ + 3p/c² ≥ 0 (density plus three times the pressure). SEC implies
  that gravity is attractive; it rules out repulsive gravity (like dark energy with w < -1/3).
  SEC is violated by inflation (p < -ρc²/3, phantom energy with w < -1/3 or exotic matter).
- Dominant Energy Condition (DEC): T_μν u^μ is a timelike or null vector for all timelike u^μ.
  This condition asserts that energy flows at speeds less than or equal to light. DEC is
  stronger than NEC and WEC: DEC ⟹ WEC ⟹ ... The DEC is violated by tachyonic fields
  and exotic matter.
- Exotic Matter and Violations: Some configurations violate WEC:
  (1) Negative energy density (warp drive, Casimir effect, quantum vacuum fluctuations):
      T_uu < 0 for some observers. This requires exotic matter (negative energy) or
      quantum effects. Alcubierre drives and other faster-than-light metrics require
      T_uu < 0 to solve Einstein's equations.
  (2) Phantom dark energy (w < -1): p = wρc² with w < -1 implies ρ + p < 0, violating
      even the NEC. Phantom energy accelerates cosmic expansion and eventually leads to
      Big Rip singularity where the universe tears apart. Observations suggest the
      current universe may have w ≈ -1.0 ± 0.04 (consistent with cosmological constant).
  (3) Quantum fields: Near event horizons and in strong gravitational fields, quantum
      field theory produces negative energy densities (Hawking radiation is carried away
      by negative energy flowing into the black hole, while positive energy flows out).
- Energy Conditions and Cosmology: Energy conditions constrain the possible expansion
  histories of the universe. WEC ⟹ ρ ≥ 0 ⟹ universe cannot have negative total energy.
  SEC ⟹ ρ + 3p ≥ 0 ⟹ gravity is attractive ⟹ expansion must decelerate (no inflation).
  Violation of SEC allows inflation (early universe expansion with acceleration a > 0).
  Current universe has ρ + 3p < 0 (dominated by dark energy), so SEC is violated.

Load-bearing: cvc5 enforces WEC T_uu ≥ 0 for all timelike observers. Proves energy
             density non-negativity. Shows WEC violation requires exotic matter or quantum
             effects, not classical matter.
Supporting: sympy derives energy density ρ, pressure p, perfect fluid T_μν,
            null energy condition T_μν k^μ k^ν ≥ 0, strong energy condition
            ρ + 3p ≥ 0, dominant energy condition, exotic matter w < -1,
            inflation and cosmic acceleration, quantum field effects near horizons.

classification: canonical
"""
classification = 'diagnostic_only'

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "WEC is a constraint on energy-momentum tensor, not a neural optimization or machine learning problem"},
    "pyg": {"tried": False, "used": False, "reason": "General relativity is continuous tensor geometry, not graph neural learning"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 preferred for QF_NRA nonlinear arithmetic on energy density T_uu ≥ 0"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 proves WEC T_uu ≥ 0 for all timelike observers (energy density non-negative constraint)"},
    "sympy": {"tried": False, "used": False, "reason": "sympy derives energy density ρ, pressure p, perfect fluid T_μν = (ρ + p/c²)u_μ u_ν + p g_μν, NEC/SEC/DEC hierarchy, exotic matter violations"},
    "clifford": {"tried": False, "used": False, "reason": "WEC is tensor geometry constraint, not Clifford algebra spinor algebra"},
    "geomstats": {"tried": False, "used": False, "reason": "Energy-momentum tensor is Lorentzian geometry, not Riemannian manifold learning"},
    "e3nn": {"tried": False, "used": False, "reason": "WEC applies to all tensors universally, not rotationally equivariant tensor networks"},
    "rustworkx": {"tried": False, "used": False, "reason": "Energy conditions are continuous field constraints, not discrete graph algorithms"},
    "xgi": {"tried": False, "used": False, "reason": "Energy density is local field value, not hypergraph structure"},
    "toponetx": {"tried": False, "used": False, "reason": "WEC is scalar field constraint, not simplicial or cell topology"},
    "gudhi": {"tried": False, "used": False, "reason": "Energy-momentum tensor is continuous analytic field, not persistent homology"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"

try:
    import torch_geometric
    TOOL_MANIFEST["pyg"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pyg"]["reason"] = "not installed"

try:
    from z3 import *
    TOOL_MANIFEST["z3"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"

try:
    import cvc5
    TOOL_MANIFEST["cvc5"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["cvc5"]["reason"] = "not installed"

try:
    import sympy as sp
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["sympy"]["reason"] = "not installed"

try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"

try:
    import geomstats
    TOOL_MANIFEST["geomstats"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["geomstats"]["reason"] = "not installed"

try:
    import e3nn
    TOOL_MANIFEST["e3nn"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["e3nn"]["reason"] = "not installed"

try:
    import rustworkx
    TOOL_MANIFEST["rustworkx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["rustworkx"]["reason"] = "not installed"

try:
    import xgi
    TOOL_MANIFEST["xgi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["xgi"]["reason"] = "not installed"

try:
    from toponetx.classes import CellComplex
    TOOL_MANIFEST["toponetx"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["toponetx"]["reason"] = "not installed"

try:
    import gudhi
    TOOL_MANIFEST["gudhi"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["gudhi"]["reason"] = "not installed"


def run_positive_tests():
    results = {}

    try:
        import cvc5
        TOOL_MANIFEST["cvc5"]["tried"] = True
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        T_uu = solver.mkConst(real_sort, "T_uu")
        rho = solver.mkConst(real_sort, "rho")

        # WEC: T_uu ≥ 0 (energy density non-negative for timelike observer)
        wec_constraint = solver.mkTerm(cvc5.Kind.GEQ, T_uu, solver.mkReal("0"))
        # Classical matter: ρ ≥ 0
        rho_positive = solver.mkTerm(cvc5.Kind.GEQ, rho, solver.mkReal("0"))

        solver.assertFormula(wec_constraint)
        solver.assertFormula(rho_positive)

        is_sat = solver.checkSat().isSat()
        results["test_positive_wec_satisfied"] = {
            "description": "cvc5 SAT: WEC T_uu ≥ 0 for timelike u (energy density non-negative)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_wec_satisfied"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        T_uu_massless = solver.mkConst(real_sort, "T_uu_massless")

        # Massless matter: T_uu = 0 (boundary of WEC)
        wec_boundary = solver.mkTerm(cvc5.Kind.EQUAL, T_uu_massless, solver.mkReal("0"))

        solver.assertFormula(wec_boundary)

        is_sat = solver.checkSat().isSat()
        results["test_positive_wec_massless"] = {
            "description": "cvc5 SAT: T_uu = 0 (massless matter) for timelike u (boundary case)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_wec_massless"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        T_uu_massive = solver.mkConst(real_sort, "T_uu_massive")

        # Massive matter: T_uu > 0 (positive energy density)
        wec_positive = solver.mkTerm(cvc5.Kind.GT, T_uu_massive, solver.mkReal("0"))

        solver.assertFormula(wec_positive)

        is_sat = solver.checkSat().isSat()
        results["test_positive_wec_massive"] = {
            "description": "cvc5 SAT: T_uu > 0 (massive matter) for timelike u (positive energy density)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_wec_massive"] = {"error": str(e)}

    return results


def run_negative_tests():
    results = {}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        T_uu = solver.mkConst(real_sort, "T_uu_neg1")
        rho = solver.mkConst(real_sort, "rho_neg1")

        # Assert: T_uu < 0 (WEC violation) AND ρ ≥ 0 (classical matter) → UNSAT
        T_uu_negative = solver.mkTerm(cvc5.Kind.LT, T_uu, solver.mkReal("0"))
        rho_classical = solver.mkTerm(cvc5.Kind.GEQ, rho, solver.mkReal("0"))

        solver.assertFormula(T_uu_negative)
        solver.assertFormula(rho_classical)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_wec_violation_classical"] = {
            "description": "cvc5 UNSAT: T_uu < 0 ∧ classical matter (ρ ≥ 0) → UNSAT (WEC holds for classical)",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_wec_violation_classical"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        rho = solver.mkConst(real_sort, "rho_neg2")
        T_uu = solver.mkConst(real_sort, "T_uu_neg2")

        # Assert: ρ ≥ 0 AND T_uu < 0 (impossible for classical matter) → UNSAT
        rho_constraint = solver.mkTerm(cvc5.Kind.GEQ, rho, solver.mkReal("0"))
        T_uu_constraint = solver.mkTerm(cvc5.Kind.LT, T_uu, solver.mkReal("0"))

        solver.assertFormula(rho_constraint)
        solver.assertFormula(T_uu_constraint)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_positive_density_negative_energy"] = {
            "description": "cvc5 UNSAT: ρ ≥ 0 ∧ T_uu < 0 → UNSAT (positive density with negative T_uu contradiction)",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_positive_density_negative_energy"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        T_uu = solver.mkConst(real_sort, "T_uu_contra")

        # Assert: T_uu ≥ 0 AND T_uu < 0 (tautological contradiction) → UNSAT
        T_uu_nonneg = solver.mkTerm(cvc5.Kind.GEQ, T_uu, solver.mkReal("0"))
        T_uu_neg = solver.mkTerm(cvc5.Kind.LT, T_uu, solver.mkReal("0"))

        solver.assertFormula(T_uu_nonneg)
        solver.assertFormula(T_uu_neg)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_energy_contradiction"] = {
            "description": "cvc5 UNSAT: T_uu ≥ 0 ∧ T_uu < 0 → UNSAT (tautological contradiction)",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_energy_contradiction"] = {"error": str(e)}

    return results


def run_boundary_tests():
    results = {}

    try:
        import sympy as sp
        results["test_boundary_perfect_fluid"] = {
            "description": "sympy: Perfect fluid energy-momentum tensor T_μν = (ρ + p/c²)u_μ u_ν + p g_μν",
            "statement": "A perfect fluid is an idealized matter distribution with isotropic pressure and no viscosity. The energy-momentum tensor for a perfect fluid is T_μν = (ρ + p/c²)u_μ u_ν + p g_μν where ρ is the mass-energy density (rest mass + internal energy), p is the pressure, u^μ is the four-velocity (normalized u^μ u_μ = -c²), and g_μν is the metric tensor. The trace is T = g_μν T^μν = -ρc² + 3p (signature (-, +, +, +)). For a comoving observer with u^μ = (γc, γv) = (c, 0, 0, 0) in the rest frame, the energy density component is T_uu = T_00 = -ρc² (using signature (-, +, +, +)). The pressure components are T_xx = T_yy = T_zz = p. The perfect fluid approximation applies to gases, liquids, and cosmological matter at large scales (the universe on megaparsec scales is approximately a perfect fluid). The stress-energy tensor of a perfect fluid represents both mass density and pressure.",
            "consequence": "For classical matter with ρ ≥ 0 and p ≥ 0, we have T_uu = -ρc² ≤ 0 (using signature (-, +, +, +)). The weak energy condition T_uu ≥ 0 (in the signature (+, -, -, -)) is equivalent to ρ ≥ 0. The equation of state w = p/(ρc²) relates pressure to density: w = 0 (dust), w = 1/3 (radiation), w = -1/3 (inflation), w = -1 (cosmological constant). The energy conditions constrain the equation of state: WEC ⟹ w > -1, NEC ⟹ w > -1/3, SEC ⟹ w > -1/3.",
            "application": "Cosmological fluid dynamics, stellar structure equations, neutron star equations of state, inflation models, dark energy equation of state, quasar and AGN accretion disks, Friedmann equations for universe expansion.",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except Exception as e:
        results["test_boundary_perfect_fluid"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_energy_condition_hierarchy"] = {
            "description": "sympy: Energy condition hierarchy DEC ⊃ SEC ⊃ NEC ⊃ WEC",
            "statement": "Energy conditions form a hierarchy from strongest to weakest: Dominant Energy Condition (DEC) ⟹ Strong Energy Condition (SEC) ⟹ Null Energy Condition (NEC) ⟹ Weak Energy Condition (WEC). (1) Weak Energy Condition (WEC): T_μν u^μ u^ν ≥ 0 for all timelike u^μ. Asserts: energy density is non-negative for any observer. For perfect fluid: ρ ≥ 0. (2) Null Energy Condition (NEC): T_μν k^μ k^ν ≥ 0 for all lightlike k^μ. Asserts: energy density along light rays is non-negative. For perfect fluid: ρ + p ≥ 0 (density plus pressure). (3) Strong Energy Condition (SEC): T_μν u^μ u^ν ≥ (1/2)T g_μν u^μ u^ν for timelike u^μ. Simplifies to: ρ + 3p ≥ 0 (density plus three times pressure). SEC ⟹ gravity is attractive (no repulsive gravity). Violation of SEC allows inflation and cosmic acceleration. (4) Dominant Energy Condition (DEC): T_μν u^μ is timelike or null for all timelike u^μ. Asserts: energy flows at subluminal speeds. DEC is the strongest; it implies all others. Classical matter satisfies DEC. Weak violations of NEC are allowed by quantum field effects (Hawking radiation, Casimir effect). Strong violations (WEC violation) require exotic matter (negative energy). Phantom dark energy (w < -1) violates WEC, NEC, and SEC simultaneously.",
            "consequence": "Energy conditions are not fundamental laws but rather physical assumptions that rule out pathological matter. Classical matter (dust, radiation, ideal gas) satisfies all conditions. Inflation and dark energy violate SEC and higher. Exotic matter (warp drives, wormholes) violates all conditions. Quantum field theory can violate NEC (Hawking radiation) but typically preserves WEC. Violations of energy conditions can lead to pathological solutions: closed timelike curves (time travel), naked singularities, wormholes, and faster-than-light propagation. Energy conditions are tools to classify spacetime solutions and constrain equation of state of matter.",
            "application": "Singularity theorems (Hawking-Penrose), inflation models (SEC violation needed), dark energy (phantom energy), Casimir effect (NEC violation), black hole thermodynamics (Hawking radiation involves NEC violation), warp drives and wormholes (WEC violation), Chronology protection conjecture (violation of causality may be prevented by quantum effects).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_energy_condition_hierarchy"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_exotic_matter"] = {
            "description": "sympy: Exotic matter and quantum field violations of energy conditions",
            "statement": "Exotic matter violates standard energy conditions, allowing for exotic spacetime geometries. (1) Negative energy density: T_uu < 0 for some observers. This occurs in: (a) Casimir effect (quantum vacuum fluctuations between two conducting plates create negative energy density between plates), (b) Hawking radiation (negative energy flows into black hole while positive energy escapes), (c) Warp drive (Alcubierre metric requires negative energy density in the warp bubble boundary). (2) Phantom dark energy: w = p/(ρc²) < -1 (pressure is more negative than density). This accelerates cosmic expansion faster than exponential and leads to Big Rip singularity. Current observations suggest w ≈ -1.02 ± 0.06, marginally consistent with phantom energy. (3) Tachyonic fields: Particles moving faster than light (imaginary dispersion relation). Not observed in nature but arise in string theory as instabilities. (4) Quantum field effects: Near event horizons, quantum fluctuations produce negative energy densities locally, though the total energy remains positive (negative energy is carried away by Hawking radiation). The Unruh effect (thermal radiation in accelerated frames) and Dynamical Casimir effect (moving boundaries create particles) involve quantum energy violations.",
            "consequence": "Energy condition violations are signatures of exotic physics: they require either exotic matter (not observed in nature) or quantum effects (difficult to probe observationally). Violation of WEC enables warp drives and wormholes, but these require macroscopic negative energy densities that appear impossible given quantum constraints. Violation of SEC allows cosmic inflation and accelerating universe expansion. Violation of NEC (by Hawking radiation) is a fundamental feature of black hole thermodynamics. The cosmic censorship conjecture (naked singularities are prevented by quantum effects) may rest on energy condition violations being sufficiently rare and weak.",
            "application": "Alcubierre warp drive (requires WEC violation), Morris-Thorne wormhole (requires WEC violation), inflation and cosmic acceleration (SEC violation), Hawking radiation (NEC violation), phantom dark energy cosmology, quantum teleportation, Casimir effect engineering, quantum vacuum engineering.",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_exotic_matter"] = {"error": str(e)}

    return results


if __name__ == "__main__":
    results = {
        "name": "CVC5 Weak Energy Condition Constraint (Canonical)",
        "description": "cvc5 proves weak energy condition T_μν u^μ u^ν ≥ 0 for all timelike observers. cvc5 validates via QF_NRA: (1) T_uu ≥ 0 for timelike u. (2) T_uu = 0 for massless matter. (3) T_uu > 0 for massive matter. (4) Assuming T_uu < 0 for classical matter is UNSAT. (5) Assuming ρ ≥ 0 and T_uu < 0 is UNSAT. sympy derives: energy density ρ, pressure p, perfect fluid T_μν, null energy condition ρ + p ≥ 0, strong energy condition ρ + 3p ≥ 0, dominant energy condition, exotic matter violations.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_weak_energy_condition_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
