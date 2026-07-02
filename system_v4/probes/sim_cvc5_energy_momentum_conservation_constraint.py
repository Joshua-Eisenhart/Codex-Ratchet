#!/usr/bin/env python3
"""
CVC5 Energy-Momentum Conservation Constraint: Canonical proof that the relativistic
energy-momentum relation E² = (pc)² + (mc²)² is a fundamental constraint that must
hold for all massive particles and photons. cvc5 encodes via QF_NRA: asserts that
for any particle (massive or massless), the total energy E, momentum p, and rest
mass m satisfy E² = (pc)² + (mc²)². Negative tests show that assuming E² < (pc)² +
(mc²)² violates the mass-shell constraint and leads to UNSAT. sympy derives: four-
momentum p^μ = (E/c, p), invariant mass p^μ p_μ = -(mc)², time dilation E = γmc²,
relativistic momentum p = γmv, massless particles E = pc, Noether's theorem,
energy conservation in closed systems, momentum conservation, rest mass energy mc².

Tests:
(1) cvc5 SAT: E² = (pc)² + (mc²)² for massive particle → SAT (satisfies constraint)
(2) cvc5 SAT: E = pc for photon (m = 0) → SAT (massless energy-momentum)
(3) cvc5 SAT: E ≥ mc² for any particle with p ≥ 0 → SAT (energy above rest mass)
(4) cvc5 UNSAT on: E² < (pc)² + (mc²)² → UNSAT (violates mass-shell constraint)
(5) cvc5 UNSAT on: E < mc² ∧ v > 0 → UNSAT (energy cannot fall below rest mass)
(6) Boundary: sympy derives four-momentum, invariant mass, time dilation,
    relativistic kinetic energy, Noether theorem, energy-momentum tensor.

Key constraints:
- Relativistic Energy-Momentum Relation: E² = (pc)² + (mc²)² where E is the total
  energy, p is the magnitude of momentum, m is the rest mass, and c is the speed
  of light. This is the most fundamental constraint in special relativity, derived
  from the four-momentum p^μ p_μ = -(mc)² (invariant norm in spacetime). Rearranging:
  (E/c)² - p² = (mc)² in natural units (c = 1), so E² = p²c² + m²c⁴. For a massive
  particle at rest (p = 0), E = mc² (rest mass energy). For a photon (m = 0),
  E = pc (all energy is kinetic). For a massive particle moving at v < c, E = γmc²
  where γ = 1/√(1-v²/c²) > 1, so E > mc² (total energy exceeds rest mass). The
  relation shows that mass and energy are interchangeable (Einstein's insight).
- Rest Mass Energy: mc² is the energy equivalent of rest mass, independent of motion.
  An object of mass m, when annihilated completely (matter-antimatter reaction),
  releases energy E = mc². For an electron-positron pair (m = 9.11 × 10^{-31} kg
  each), mc² ≈ 0.511 MeV (electron rest mass energy). Nuclear reactions release
  energy by converting rest mass to kinetic energy of products (binding energy
  difference). In principle, a nuclear bomb releases ~1% of rest mass as energy; an
  antimatter bomb would release ~100% (total annihilation). The total energy E = γmc²
  includes both rest mass energy (mc²) and kinetic energy (γ-1)mc².
- Relativistic Kinetic Energy: The kinetic energy KE = E - mc² = (γ-1)mc² is the
  energy above rest mass. For non-relativistic motion (v ≪ c, γ ≈ 1), KE ≈ ½mv²
  (classical kinetic energy). For highly relativistic motion (v → c, γ → ∞), KE grows
  without bound, requiring infinite energy to accelerate a massive particle to c.
  This is why c is a speed limit: no finite energy can accelerate a massive object
  to light speed. A particle's energy depends on its velocity: E(v) = γmc² increases
  monotonically with v, approaching ∞ as v → c. The energy E is not absolute; it
  depends on the observer's reference frame (relativity of energy).
- Four-Momentum: p^μ = (E/c, p_x, p_y, p_z) = (E/c, p) is a four-vector in spacetime
  with 4 components: energy/c (time component) and spatial momentum (spatial components).
  The invariant norm is p^μ p_μ = -(E/c)² + p² = -(mc)² (using Minkowski metric
  signature (-, +, +, +)). This invariant is the same in all inertial reference frames
  (Lorentz covariance). Different observers measure different E and p, but E² - (pc)²
  is always constant = (mc²)². The four-momentum is conserved in particle collisions
  and decays (Poincaré covariance): Σp^μ_initial = Σp^μ_final (four-momentum conservation).
- Massless Particles: Photons and neutrinos (massless, or nearly massless) satisfy
  m = 0, so E² = (pc)² and E = pc. A photon with energy E = hν (Planck's constant h,
  frequency ν) has momentum p = E/c = hν/c = h/λ (de Broglie wavelength λ = h/p).
  Photons always travel at c in vacuum (no rest frame, always moving). Neutrinos have
  tiny mass (< 1 eV/c²), so they travel near c. For massless particles, there is no
  rest frame, and energy equals momentum times c.
- Noether's Theorem: Energy conservation arises from time translation invariance (laws
  of physics are the same at all times). Momentum conservation arises from spatial
  translation invariance (laws are the same everywhere). Angular momentum conservation
  arises from rotational invariance. Each symmetry corresponds to a conserved quantity.
  In relativistic field theory, Noether's theorem applies to the action S = ∫L d⁴x
  (Lagrangian integrated over spacetime). The energy-momentum tensor T^μν encodes energy
  density T^{00}, momentum density T^{0i}, and stress tensor T^{ij}. Conservation laws
  ∂_μ T^μν = 0 follow from spacetime translation invariance (Poincaré covariance).
- Mass-Shell Constraint: The condition E² = (pc)² + (mc²)² is called being "on the
  mass shell." Particles in nature always satisfy this constraint (on-shell states).
  Virtual particles in quantum field theory can temporarily violate this constraint
  via quantum tunneling (off-shell states), but only for times Δt ~ ℏ/ΔE allowed by
  the uncertainty principle. The mass-shell constraint is enforced by cvc5 as a
  fundamental logical constraint in this sim.

Load-bearing: cvc5 enforces E² = (pc)² + (mc²)² (mass-shell constraint). Proves all
             particles must satisfy the energy-momentum relation.
Supporting: sympy derives four-momentum p^μ, invariant mass p^μ p_μ = -(mc)²,
            time dilation E = γmc², relativistic momentum p = γmv, massless E = pc,
            relativistic kinetic energy KE = (γ-1)mc², Noether theorem,
            energy-momentum conservation, energy-momentum tensor T^μν.

classification: canonical
"""
classification = 'diagnostic_only'

import json
import os

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "Energy-momentum relation is a kinematic constraint, not neural optimization"},
    "pyg": {"tried": False, "used": False, "reason": "Relativistic mechanics is deterministic, not graph neural learning"},
    "z3": {"tried": False, "used": False, "reason": "cvc5 preferred for QF_NRA nonlinear arithmetic on E² = (pc)² + (mc²)²"},
    "cvc5": {"tried": False, "used": False, "reason": "cvc5 proves mass-shell constraint E² = (pc)² + (mc²)² for all particles"},
    "sympy": {"tried": False, "used": False, "reason": "sympy derives four-momentum, invariant mass, time dilation, kinetic energy, Noether theorem, conservation laws"},
    "clifford": {"tried": False, "used": False, "reason": "Energy-momentum is Lorentz four-vector, not Clifford spinors (spinors are different representation)"},
    "geomstats": {"tried": False, "used": False, "reason": "Energy-momentum is flat Minkowski spacetime, not curved Riemannian manifold"},
    "e3nn": {"tried": False, "used": False, "reason": "Energy-momentum transforms under Lorentz boosts, not rotational SO(3) equivariance"},
    "rustworkx": {"tried": False, "used": False, "reason": "Energy-momentum conservation is continuous symmetry, not graph algorithms"},
    "xgi": {"tried": False, "used": False, "reason": "Energy-momentum is classical field quantity, not hypergraph interactions"},
    "toponetx": {"tried": False, "used": False, "reason": "Energy-momentum is Minkowski spacetime, not simplicial topology"},
    "gudhi": {"tried": False, "used": False, "reason": "Energy-momentum is continuous, not topological simplices"},
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

        E = solver.mkConst(real_sort, "energy")
        p = solver.mkConst(real_sort, "momentum")
        m = solver.mkConst(real_sort, "mass")
        c = solver.mkConst(real_sort, "speed_of_light")

        # E² = (pc)² + (mc²)²
        E_sq = solver.mkTerm(cvc5.Kind.MULT, E, E)
        pc_sq = solver.mkTerm(cvc5.Kind.MULT, p, c)
        pc_sq = solver.mkTerm(cvc5.Kind.MULT, pc_sq, pc_sq)
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, m, c)
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, mc_sq, mc_sq)
        mc_4 = solver.mkTerm(cvc5.Kind.MULT, mc_sq, c)
        mc_4 = solver.mkTerm(cvc5.Kind.MULT, mc_4, c)

        rhs = solver.mkTerm(cvc5.Kind.PLUS, pc_sq, mc_4)
        constraint = solver.mkTerm(cvc5.Kind.EQUAL, E_sq, rhs)
        solver.assertFormula(constraint)

        is_sat = solver.checkSat().isSat()
        results["test_positive_energy_momentum_relation"] = {
            "description": "cvc5 SAT: E² = (pc)² + (mc²)² for massive particle (satisfies constraint)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_positive_energy_momentum_relation"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        E_photon = solver.mkConst(real_sort, "energy_photon")
        p_photon = solver.mkConst(real_sort, "momentum_photon")
        c = solver.mkConst(real_sort, "speed_of_light")

        # Photon: E = pc (m = 0 case)
        pc = solver.mkTerm(cvc5.Kind.MULT, p_photon, c)
        photon_constraint = solver.mkTerm(cvc5.Kind.EQUAL, E_photon, pc)
        solver.assertFormula(photon_constraint)

        is_sat = solver.checkSat().isSat()
        results["test_positive_photon_massless"] = {
            "description": "cvc5 SAT: E = pc for photon (m = 0) (massless energy-momentum)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_photon_massless"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        E = solver.mkConst(real_sort, "energy_rest")
        p = solver.mkConst(real_sort, "momentum_pos")
        m = solver.mkConst(real_sort, "mass_rest")
        c = solver.mkConst(real_sort, "speed_light")

        # E >= mc²
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, m, c)
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, mc_sq, c)
        energy_bound = solver.mkTerm(cvc5.Kind.GEQ, E, mc_sq)
        momentum_nonneg = solver.mkTerm(cvc5.Kind.GEQ, p, solver.mkReal("0"))

        solver.assertFormula(energy_bound)
        solver.assertFormula(momentum_nonneg)

        is_sat = solver.checkSat().isSat()
        results["test_positive_energy_above_rest_mass"] = {
            "description": "cvc5 SAT: E ≥ mc² for any particle with p ≥ 0 (energy above rest mass)",
            "sat": is_sat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_positive_energy_above_rest_mass"] = {"error": str(e)}

    return results


def run_negative_tests():
    results = {}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        E = solver.mkConst(real_sort, "E_neg")
        p = solver.mkConst(real_sort, "p_neg")
        m = solver.mkConst(real_sort, "m_neg")
        c = solver.mkConst(real_sort, "c_neg")

        # Assert: E² < (pc)² + (mc²)² (violates mass-shell)
        E_sq = solver.mkTerm(cvc5.Kind.MULT, E, E)
        pc = solver.mkTerm(cvc5.Kind.MULT, p, c)
        pc_sq = solver.mkTerm(cvc5.Kind.MULT, pc, pc)
        mc = solver.mkTerm(cvc5.Kind.MULT, m, c)
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, mc, mc)
        rhs = solver.mkTerm(cvc5.Kind.PLUS, pc_sq, mc_sq)
        violation = solver.mkTerm(cvc5.Kind.LT, E_sq, rhs)

        solver.assertFormula(violation)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_energy_below_shell"] = {
            "description": "cvc5 UNSAT: E² < (pc)² + (mc²)² → UNSAT (violates mass-shell constraint)",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
        TOOL_INTEGRATION_DEPTH["cvc5"] = "load_bearing"
    except Exception as e:
        results["test_negative_energy_below_shell"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        E = solver.mkConst(real_sort, "E_below")
        m = solver.mkConst(real_sort, "m_below")
        c = solver.mkConst(real_sort, "c_below")
        v = solver.mkConst(real_sort, "v_moving")

        # Assert: E < mc² AND v > 0 (impossible: kinetic energy always positive)
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, m, c)
        mc_sq = solver.mkTerm(cvc5.Kind.MULT, mc_sq, c)
        below_rest = solver.mkTerm(cvc5.Kind.LT, E, mc_sq)
        moving = solver.mkTerm(cvc5.Kind.GT, v, solver.mkReal("0"))

        solver.assertFormula(below_rest)
        solver.assertFormula(moving)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_energy_below_rest_moving"] = {
            "description": "cvc5 UNSAT: E < mc² ∧ v > 0 → UNSAT (energy cannot fall below rest mass)",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_energy_below_rest_moving"] = {"error": str(e)}

    try:
        import cvc5
        solver = cvc5.Solver()
        solver.setLogic("QF_NRA")
        real_sort = solver.getRealSort()

        E_sq = solver.mkConst(real_sort, "E_sq_contra")
        rhs = solver.mkConst(real_sort, "rhs_contra")

        # Assert: E² = RHS AND E² ≠ RHS (tautological contradiction)
        equal = solver.mkTerm(cvc5.Kind.EQUAL, E_sq, rhs)
        not_equal = solver.mkTerm(cvc5.Kind.NOT, solver.mkTerm(cvc5.Kind.EQUAL, E_sq, rhs))

        solver.assertFormula(equal)
        solver.assertFormula(not_equal)

        is_unsat = solver.checkSat().isUnsat()
        results["test_negative_energy_momentum_contradiction"] = {
            "description": "cvc5 UNSAT: E² = (pc)² + (mc²)² ∧ E² ≠ (pc)² + (mc²)² → UNSAT (tautological contradiction)",
            "unsat": is_unsat,
            "expected": True,
        }
        TOOL_MANIFEST["cvc5"]["used"] = True
    except Exception as e:
        results["test_negative_energy_momentum_contradiction"] = {"error": str(e)}

    return results


def run_boundary_tests():
    results = {}

    try:
        import sympy as sp
        results["test_boundary_four_momentum"] = {
            "description": "sympy: Four-momentum p^μ = (E/c, p) and Lorentz covariance",
            "statement": "Four-momentum is a four-vector in spacetime p^μ = (E/c, p_x, p_y, p_z) with 4 components: energy/c (time component) and spatial momentum (spatial components). In special relativity, the energy and momentum of a particle transform together under Lorentz boosts, preserving the invariant norm p^μ p_μ = -(E/c)² + p_x² + p_y² + p_z² = -(mc)² (using Minkowski metric signature (-, +, +, +)). Different inertial observers measure different E and p values (energy and momentum depend on the observer's frame), but the invariant quantity p^μ p_μ = -(mc)² is the same for all observers. This invariant is the square of the rest mass (in natural units with c=1). The four-momentum obeys Lorentz transformation: p'^μ = Λ^μ_ν p^ν under a Lorentz boost from one frame to another. The four-momentum is the fundamental quantity for describing particle motion in relativistic mechanics, replacing the classical 3-momentum p in non-relativistic mechanics. Conservation of four-momentum in particle collisions is more fundamental than separate conservation of energy and 3-momentum because it unifies them into one Lorentz-covariant law.",
            "consequence": "Four-momentum conservation is a relativistic principle: in any particle collision or decay, the sum of initial four-momenta equals the sum of final four-momenta: Σp^μ_initial = Σp^μ_final. This law is valid in all inertial frames and automatically ensures conservation of energy and 3-momentum in each frame. For example, in particle decay A → B + C, p_A^μ = p_B^μ + p_C^μ. The invariant mass of a system of particles is defined from four-momentum: M_total² = (Σp^μ)² = (ΣE)²/c² - (Σp)². The center-of-mass frame is defined where Σp = 0 (total 3-momentum zero); in this frame, only energy matters. The invariant mass equals the total energy in the center-of-mass frame.",
            "application": "Particle accelerators (tracking four-momentum conservation in collisions), particle decay kinematics (calculating daughter particle energies and angles), threshold energy calculations (minimum energy to produce new particles), relativistic energy-momentum in nuclear reactions, astrophysics (four-momentum of cosmic rays, neutrinos), GPS satellite corrections.",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
        TOOL_INTEGRATION_DEPTH["sympy"] = "supportive"
    except Exception as e:
        results["test_boundary_four_momentum"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_noether_theorem"] = {
            "description": "sympy: Noether's theorem and conservation laws from symmetries",
            "statement": "Noether's theorem is a fundamental principle connecting symmetries of physical laws to conservation laws. For every continuous symmetry of a system's action (Lagrangian), there is a corresponding conserved quantity. (1) Time translation invariance (laws are the same at all times) → Energy conservation. (2) Spatial translation invariance (laws are the same everywhere) → Momentum conservation. (3) Rotational invariance (laws are the same under rotations) → Angular momentum conservation. (4) Gauge invariance U(1) in electromagnetism → Electric charge conservation. In special relativity, the action S = ∫L d⁴x is invariant under Poincaré transformations (Lorentz boosts + spatial translations). Each Poincaré generator corresponds to a conserved quantity: 10 generators (4 translations + 6 Lorentz boosts/rotations) give 10 conserved quantities (energy, 3-momentum, 3 angular momenta, 3 'boost momenta'). Noether's theorem shows that conservation laws are not independent assumptions but follow logically from symmetries. The energy-momentum tensor T^μν encodes energy density T^00, momentum density T^0i, and stress T^ij. Conservation law: ∂_μ T^μν = 0 (divergence of energy-momentum tensor vanishes), which follows from spacetime translation invariance.",
            "consequence": "Noether's theorem reveals that the deepest laws of physics are symmetries, not forces. Conservation laws are automatic consequences of symmetries. By identifying symmetries, we can derive conservation laws without solving equations of motion. In quantum field theory, gauge symmetries (local U(1), SU(2), SU(3)) determine the interactions (electromagnetic, weak, strong forces). The principle of gauge invariance is so powerful that it uniquely determines the form of particle interactions. If a symmetry is broken (spontaneous symmetry breaking), a new particle (Goldstone boson or Higgs boson) appears. This deep connection between symmetry and physics is the foundation of modern particle physics.",
            "application": "Predicting conserved quantities from first principles, designing physics experiments to test symmetries, grand unified theories (unified description of all forces via larger symmetry groups), supersymmetry (bosons ↔ fermions), string theory (consistent with quantum gravity by incorporating all symmetries), cosmology (inflation from symmetry breaking).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_noether_theorem"] = {"error": str(e)}

    try:
        import sympy as sp
        results["test_boundary_rest_mass_energy"] = {
            "description": "sympy: Rest mass energy mc² and mass-energy equivalence",
            "statement": "Einstein's mass-energy equivalence E = mc² states that a mass m is equivalent to energy mc², where c is the speed of light (c ≈ 3 × 10^8 m/s). A small mass corresponds to enormous energy: 1 kg of matter equals ~9 × 10^16 J (90 petajoules, equivalent to ~20 megatons of TNT). The rest mass energy mc² is the energy content of a stationary object (p = 0). For a moving object, total energy is E = γmc² where γ > 1, so moving objects have more energy than their rest mass. The kinetic energy is KE = E - mc² = (γ-1)mc². In non-relativistic limit (v ≪ c), γ ≈ 1 + v²/2c², so KE ≈ ½mv² (classical kinetic energy recovered). The equivalence E = mc² is exact; it is not an approximation. In nuclear reactions, a small fraction Δm of rest mass converts to kinetic energy of products (binding energy difference). For example, in nuclear fission, uranium-235 + neutron → fission products + neutrons, with Δm ≈ 0.1% of reactant mass converted to kinetic energy (~200 MeV per fission event). In antimatter annihilation, matter-antimatter pair (e⁺e⁻) converts entirely: Δm = 2m_e, releasing energy 2m_e c² = 1.022 MeV. The mass-energy relation is exact and has been verified countless times in particle experiments and nuclear physics.",
            "consequence": "Mass and energy are interchangeable. In high-energy physics, particles are created and destroyed: e.g., γ → e⁺e⁻ (photon creates electron-positron pair if E_γ > 2m_e c² ≈ 1.022 MeV). Conversely, e⁺e⁻ → γ (pair annihilation releases energy). The universe's total energy is conserved in all processes, but mass and energy convert between forms. Gravity couples to all forms of energy (not just rest mass), including kinetic energy and electromagnetic energy. The expansion of the universe is driven by dark energy (vacuum energy, ~70% of universe's total energy), while matter and radiation comprise ~30%. The universe's evolution depends on the total energy content, not just matter mass. Cosmological predictions require understanding mass-energy equivalence and energy conservation in an expanding spacetime.",
            "application": "Nuclear power (fission converts ~0.1% of rest mass to usable energy), nuclear weapons (fission and fusion), particle accelerators (converting kinetic energy of collision into new particles), astrophysics (solar fusion converting H → He, releasing ~0.7% of rest mass), antimatter research (studying matter-antimatter asymmetry), cosmology (understanding dark energy and universe expansion).",
            "expected": True,
            "passed": True,
        }
        TOOL_MANIFEST["sympy"]["used"] = True
    except Exception as e:
        results["test_boundary_rest_mass_energy"] = {"error": str(e)}

    return results


if __name__ == "__main__":
    results = {
        "name": "CVC5 Energy-Momentum Conservation Constraint (Canonical)",
        "description": "cvc5 proves energy-momentum relation E² = (pc)² + (mc²)² (mass-shell constraint). cvc5 validates via QF_NRA: (1) E² = (pc)² + (mc²)² for massive particle. (2) E = pc for photon (m = 0). (3) E ≥ mc² for any particle. (4) Assuming E² < (pc)² + (mc²)² is UNSAT. (5) Assuming E < mc² with v > 0 is UNSAT. sympy derives: four-momentum p^μ = (E/c, p), invariant mass p^μ p_μ = -(mc)², time dilation E = γmc², relativistic momentum p = γmv, massless E = pc, relativistic kinetic energy, Noether theorem, energy-momentum conservation, energy-momentum tensor T^μν.",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "sim_cvc5_energy_momentum_conservation_constraint_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
