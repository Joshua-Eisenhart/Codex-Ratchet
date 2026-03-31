"""
qit_nonclassical_guards.py

Bounded z3 guard layer for QIT/nonclassical proof work.

The goal is not theorem proving. The goal is to fail closed on the most
common classical drifts called out in
`core_docs/v4 upgrades/lev_nonclassical_runtime_design_audited.md`:

- state treated as a flat point
- primitive equality admitted without probes
- updates treated as commutative by default
- separable/cartesian bridge admitted while claiming nonclassical coupling
- bounded local improvement replaced with unbounded global optimization
"""
from __future__ import annotations

from dataclasses import dataclass, field
import numpy as np

try:
    import z3
    HAS_Z3 = True
except ImportError:  # pragma: no cover
    HAS_Z3 = False


@dataclass
class NonclassicalGuardInput:
    nonclassical_state_claim: bool = True
    flat_state_model: bool = False
    primitive_equality: bool = False
    probe_relative_equivalence: bool = True
    update_order_matters: bool = True
    assumes_commutative_update: bool = False
    entangling_bridge_claim: bool = True
    cartesian_product_bridge: bool = False
    bounded_local_improvement: bool = True
    unbounded_global_optimization: bool = False


@dataclass
class GuardCheckResult:
    passed: bool
    violations: list[str] = field(default_factory=list)
    checked_count: int = 0


def bridge_guard_input(
    rho_ab: np.ndarray,
    rho_L: np.ndarray,
    rho_R: np.ndarray,
    *,
    tol: float = 1e-8,
    entangling_bridge_claim: bool = True,
) -> NonclassicalGuardInput:
    """Build a guard input from an actual bipartite bridge state."""
    rho_ab = np.asarray(rho_ab, dtype=complex)
    rho_L = np.asarray(rho_L, dtype=complex)
    rho_R = np.asarray(rho_R, dtype=complex)
    separable = np.kron(rho_L, rho_R)
    cartesian = bool(np.linalg.norm(rho_ab - separable, ord="fro") <= tol)
    return NonclassicalGuardInput(
        entangling_bridge_claim=entangling_bridge_claim,
        cartesian_product_bridge=cartesian,
    )


def check_nonclassical_guards(inp: NonclassicalGuardInput) -> GuardCheckResult:
    violations: list[str] = []

    if HAS_Z3:
        s = z3.Solver()
        nonclassical_state_claim = z3.Bool("nonclassical_state_claim")
        flat_state_model = z3.Bool("flat_state_model")
        primitive_equality = z3.Bool("primitive_equality")
        probe_relative_equivalence = z3.Bool("probe_relative_equivalence")
        update_order_matters = z3.Bool("update_order_matters")
        assumes_commutative_update = z3.Bool("assumes_commutative_update")
        entangling_bridge_claim = z3.Bool("entangling_bridge_claim")
        cartesian_product_bridge = z3.Bool("cartesian_product_bridge")
        bounded_local_improvement = z3.Bool("bounded_local_improvement")
        unbounded_global_optimization = z3.Bool("unbounded_global_optimization")

        assignments = {
            nonclassical_state_claim: inp.nonclassical_state_claim,
            flat_state_model: inp.flat_state_model,
            primitive_equality: inp.primitive_equality,
            probe_relative_equivalence: inp.probe_relative_equivalence,
            update_order_matters: inp.update_order_matters,
            assumes_commutative_update: inp.assumes_commutative_update,
            entangling_bridge_claim: inp.entangling_bridge_claim,
            cartesian_product_bridge: inp.cartesian_product_bridge,
            bounded_local_improvement: inp.bounded_local_improvement,
            unbounded_global_optimization: inp.unbounded_global_optimization,
        }
        for sym, val in assignments.items():
            s.add(sym == val)

        checks = [
            ("flat_state_drift", z3.Implies(nonclassical_state_claim, z3.Not(flat_state_model))),
            ("primitive_equality_drift", z3.Implies(nonclassical_state_claim, z3.Not(primitive_equality))),
            ("probe_relative_equivalence_required", z3.Implies(nonclassical_state_claim, probe_relative_equivalence)),
            ("commutative_update_drift", z3.Implies(update_order_matters, z3.Not(assumes_commutative_update))),
            ("cartesian_bridge_leak", z3.Implies(entangling_bridge_claim, z3.Not(cartesian_product_bridge))),
            ("unbounded_optimization_drift", z3.Implies(bounded_local_improvement, z3.Not(unbounded_global_optimization))),
        ]

        for name, expr in checks:
            local = z3.Solver()
            local.add(s.assertions())
            local.add(z3.Not(expr))
            if local.check() == z3.sat:
                violations.append(name)
    else:  # pragma: no cover
        if inp.nonclassical_state_claim and inp.flat_state_model:
            violations.append("flat_state_drift")
        if inp.nonclassical_state_claim and inp.primitive_equality:
            violations.append("primitive_equality_drift")
        if inp.nonclassical_state_claim and not inp.probe_relative_equivalence:
            violations.append("probe_relative_equivalence_required")
        if inp.update_order_matters and inp.assumes_commutative_update:
            violations.append("commutative_update_drift")
        if inp.entangling_bridge_claim and inp.cartesian_product_bridge:
            violations.append("cartesian_bridge_leak")
        if inp.bounded_local_improvement and inp.unbounded_global_optimization:
            violations.append("unbounded_optimization_drift")

    return GuardCheckResult(
        passed=len(violations) == 0,
        violations=violations,
        checked_count=6,
    )


def _selftest() -> int:
    passed = 0

    baseline = check_nonclassical_guards(NonclassicalGuardInput())
    assert baseline.passed, baseline.violations
    passed += 1

    flat = check_nonclassical_guards(NonclassicalGuardInput(flat_state_model=True))
    assert not flat.passed and "flat_state_drift" in flat.violations
    passed += 1

    primitive = check_nonclassical_guards(NonclassicalGuardInput(primitive_equality=True))
    assert not primitive.passed and "primitive_equality_drift" in primitive.violations
    passed += 1

    commutative = check_nonclassical_guards(NonclassicalGuardInput(assumes_commutative_update=True))
    assert not commutative.passed and "commutative_update_drift" in commutative.violations
    passed += 1

    cartesian = check_nonclassical_guards(NonclassicalGuardInput(cartesian_product_bridge=True))
    assert not cartesian.passed and "cartesian_bridge_leak" in cartesian.violations
    passed += 1

    optimization = check_nonclassical_guards(NonclassicalGuardInput(unbounded_global_optimization=True))
    assert not optimization.passed and "unbounded_optimization_drift" in optimization.violations
    passed += 1

    rho0 = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=complex)
    rho1 = np.array([[0.0, 0.0], [0.0, 1.0]], dtype=complex)
    sep = np.kron(rho0, rho1)
    sep_guard = check_nonclassical_guards(bridge_guard_input(sep, rho0, rho1))
    assert not sep_guard.passed and "cartesian_bridge_leak" in sep_guard.violations
    passed += 1

    psi_minus = np.array([0.0, 1.0, -1.0, 0.0], dtype=complex) / np.sqrt(2.0)
    bell = np.outer(psi_minus, psi_minus.conj())
    bell_guard = check_nonclassical_guards(bridge_guard_input(bell, rho0, rho1))
    assert bell_guard.passed, bell_guard.violations
    passed += 1

    return passed


if __name__ == "__main__":
    total_passed = _selftest()
    print(f"PASS: qit_nonclassical_guards self-test ({total_passed} checks, z3_available={HAS_Z3})")
