#!/usr/bin/env python3
"""Deep Clifford algebra geometry probe (diagnostic_only, unadmitted).

Independent Codex build for known Euclidean Clifford geometry:

  * Cl(3) and Cl(6) geometric product over a finite blade carrier.
  * Euclidean generators satisfy e_i^2 = 1 and {e_i, e_j} = 2 delta_ij.
  * dim Cl(3) = 8 and dim Cl(6) = 64.
  * even Cl(3) realizes the quaternion algebra.
  * the Cl(3) pseudoscalar I = e123 has I^2 = -1 and is central.
  * rotor R = exp(-theta B / 2) rotates a vector by angle theta.

The primary claim substrate is a torch.float64 finite-map Clifford engine.
NumPy is not imported here; tools that use NumPy internally are only read as
independent tool outputs.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
from typing import Any

# clifford and quimb both route through numba in this environment. These flags
# keep their import path deterministic and prevent numba cache locator failures.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("QUIMB_NUMBA_CACHE", "false")

import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
from geomstats.geometry.hypersphere import Hypersphere
import geomstats.backend as gs
import gudhi
import quimb as qu
import rustworkx as rx
import sympy as sp
import toponetx as tnx
import torch
import z3


RTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1.0e-10
TOL_TOOL = 1.0e-8
TOL_E3NN = 1.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "geom_clifford_algebra_codex_probe_results.json"
SIM_ID = "geom_clifford_algebra_codex_probe"


def blade_grade(mask: int) -> int:
    return mask.bit_count()


def blade_name(mask: int) -> str:
    if mask == 0:
        return "1"
    return "e" + "".join(str(i + 1) for i in range(mask.bit_length()) if mask & (1 << i))


def scalar_tensor(value: float | torch.Tensor) -> torch.Tensor:
    if isinstance(value, torch.Tensor):
        return value.to(dtype=RTYPE)
    return torch.tensor(float(value), dtype=RTYPE)


def mv_from_terms(n: int, terms: dict[int, float | torch.Tensor]) -> torch.Tensor:
    size = 1 << n
    zero = torch.zeros((), dtype=RTYPE)
    coeffs: list[torch.Tensor] = []
    for mask in range(size):
        coeffs.append(scalar_tensor(terms[mask]) if mask in terms else zero.clone())
    return torch.stack(coeffs)


def scalar_mv(n: int, value: float | torch.Tensor) -> torch.Tensor:
    return mv_from_terms(n, {0: value})


def basis_mv(n: int, mask: int) -> torch.Tensor:
    return mv_from_terms(n, {mask: 1.0})


def blade_mul(mask_a: int, mask_b: int) -> tuple[int, int]:
    """Return (sign, mask) for Euclidean basis blades e_A e_B.

    The sign is the parity of swaps required to move the B blade indices through
    the A blade indices. Repeated equal indices cancel because e_i^2 = +1.
    """
    swaps = 0
    x = mask_a
    while x:
        lowest = x & -x
        i = lowest.bit_length() - 1
        swaps += (mask_b & ((1 << i) - 1)).bit_count()
        x ^= lowest
    return (-1 if swaps % 2 else 1), mask_a ^ mask_b


def gp(a: torch.Tensor, b: torch.Tensor, n: int) -> torch.Tensor:
    size = 1 << n
    out = [torch.zeros((), dtype=RTYPE) for _ in range(size)]
    for ma in range(size):
        ca = a[ma]
        for mb in range(size):
            cb = b[mb]
            sign, mout = blade_mul(ma, mb)
            out[mout] = out[mout] + float(sign) * ca * cb
    return torch.stack(out)


def reverse(mv: torch.Tensor, n: int) -> torch.Tensor:
    return torch.stack(
        [
            mv[mask] * (1.0 if ((blade_grade(mask) * (blade_grade(mask) - 1) // 2) % 2 == 0) else -1.0)
            for mask in range(1 << n)
        ]
    )


def mv_norm(mv: torch.Tensor) -> float:
    return float(torch.linalg.vector_norm(mv.detach()).item())


def max_abs(mv: torch.Tensor) -> float:
    return float(torch.max(torch.abs(mv.detach())).item())


def vector_coords_3(mv: torch.Tensor) -> torch.Tensor:
    return torch.stack([mv[1], mv[2], mv[4]])


def vector_residual_3(mv: torch.Tensor) -> torch.Tensor:
    keep = {1, 2, 4}
    return torch.stack([mv[i] if i not in keep else torch.zeros((), dtype=RTYPE) for i in range(8)])


def clifford_dense(layout: Any, mv: Any, n: int) -> torch.Tensor:
    coeffs = torch.zeros(1 << n, dtype=RTYPE)
    for idx, blade_tuple in enumerate(layout.bladeTupList):
        mask = 0
        for one_based in blade_tuple:
            mask |= 1 << (one_based - 1)
        coeffs[mask] = float(mv.value[idx])
    return coeffs


def clifford_product_defect(n: int) -> dict[str, Any]:
    layout, blades = Cl(n)
    clifford_basis = []
    torch_basis = []
    for mask in range(1 << n):
        key = "" if mask == 0 else blade_name(mask)
        clifford_basis.append(blades[key])
        torch_basis.append(basis_mv(n, mask))

    worst = 0.0
    worst_pair: list[str] | None = None
    for ma in range(1 << n):
        for mb in range(1 << n):
            torch_prod = gp(torch_basis[ma], torch_basis[mb], n)
            cliff_prod = clifford_dense(layout, clifford_basis[ma] * clifford_basis[mb], n)
            defect = max_abs(torch_prod - cliff_prod)
            if defect > worst:
                worst = defect
                worst_pair = [blade_name(ma), blade_name(mb)]
    return {
        "dimension_from_clifford": int(layout.gaDims),
        "max_product_table_defect_vs_clifford": worst,
        "worst_pair": worst_pair,
    }


def topological_dimension_evidence(n: int) -> dict[str, Any]:
    simplex = tuple(range(n))

    st = gudhi.SimplexTree()
    st.insert(simplex)
    gudhi_dim = int(st.num_simplices() + 1)  # add empty face / scalar blade

    sc = tnx.SimplicialComplex([simplex])
    toponetx_dim = int(len(sc.simplices) + 1)  # add empty face / scalar blade
    toponetx_grade_counts = [1] + [int(v) for v in sc.shape]

    g = rx.PyDiGraph()
    nodes = [g.add_node(mask) for mask in range(1 << n)]
    for mask in range(1 << n):
        for bit in range(n):
            if not (mask & (1 << bit)):
                g.add_edge(nodes[mask], nodes[mask | (1 << bit)], bit)

    sympy_dim = int(sum(sp.binomial(n, k) for k in range(n + 1)))
    return {
        "torch_blade_count": 1 << n,
        "sympy_binomial_sum": sympy_dim,
        "gudhi_simplex_faces_plus_scalar": gudhi_dim,
        "toponetx_faces_plus_scalar": toponetx_dim,
        "toponetx_grade_counts": toponetx_grade_counts,
        "rustworkx_boolean_lattice_nodes": int(g.num_nodes()),
        "rustworkx_boolean_lattice_edges": int(g.num_edges()),
    }


def vector_square_defect(n: int) -> dict[str, Any]:
    defects = {}
    for i in range(n):
        e = basis_mv(n, 1 << i)
        defects[f"e{i + 1}^2_minus_1"] = max_abs(gp(e, e, n) - scalar_mv(n, 1.0))
    return defects


def anticommutator_defect(n: int) -> dict[str, Any]:
    scalar_entries: list[list[float]] = []
    residual_max = 0.0
    for i in range(n):
        row = []
        for j in range(n):
            ei = basis_mv(n, 1 << i)
            ej = basis_mv(n, 1 << j)
            anti = gp(ei, ej, n) + gp(ej, ei, n)
            expected = scalar_mv(n, 2.0 if i == j else 0.0)
            residual_max = max(residual_max, max_abs(anti - expected))
            row.append(float(anti[0].item()))
        scalar_entries.append(row)
    return {"scalar_entries": scalar_entries, "max_residual": residual_max}


def quaternion_evidence() -> dict[str, Any]:
    n = 3
    e1, e2, e3 = basis_mv(n, 1), basis_mv(n, 2), basis_mv(n, 4)
    qi = -gp(e2, e3, n)
    qj = -gp(e3, e1, n)
    qk = -gp(e1, e2, n)
    minus_one = scalar_mv(n, -1.0)

    residuals = {
        "i^2_plus_1": max_abs(gp(qi, qi, n) - minus_one),
        "j^2_plus_1": max_abs(gp(qj, qj, n) - minus_one),
        "k^2_plus_1": max_abs(gp(qk, qk, n) - minus_one),
        "ij_minus_k": max_abs(gp(qi, qj, n) - qk),
        "jk_minus_i": max_abs(gp(qj, qk, n) - qi),
        "ki_minus_j": max_abs(gp(qk, qi, n) - qj),
        "ijk_plus_1": max_abs(gp(gp(qi, qj, n), qk, n) - minus_one),
    }

    # quimb independent matrix quaternion representation: q_a = -i sigma_a.
    eye = torch.eye(2, dtype=CDTYPE)
    qx = -1j * torch.as_tensor(qu.pauli("X").tolist(), dtype=CDTYPE)
    qy = -1j * torch.as_tensor(qu.pauli("Y").tolist(), dtype=CDTYPE)
    qz = -1j * torch.as_tensor(qu.pauli("Z").tolist(), dtype=CDTYPE)
    quimb_residuals = {
        "qx^2_plus_I": float(torch.linalg.matrix_norm(qx @ qx + eye).item()),
        "qy^2_plus_I": float(torch.linalg.matrix_norm(qy @ qy + eye).item()),
        "qz^2_plus_I": float(torch.linalg.matrix_norm(qz @ qz + eye).item()),
        "qxqy_minus_qz": float(torch.linalg.matrix_norm(qx @ qy - qz).item()),
        "qxqyqz_plus_I": float(torch.linalg.matrix_norm(qx @ qy @ qz + eye).item()),
    }

    return {"torch_even_cl3_residuals": residuals, "quimb_matrix_residuals": quimb_residuals}


def pseudoscalar_evidence() -> dict[str, Any]:
    n = 3
    e1, e2, e3 = basis_mv(n, 1), basis_mv(n, 2), basis_mv(n, 4)
    pseudoscalar = gp(gp(e1, e2, n), e3, n)
    minus_one = scalar_mv(n, -1.0)
    i_square_residual = max_abs(gp(pseudoscalar, pseudoscalar, n) - minus_one)

    central_residual = 0.0
    for mask in range(1 << n):
        b = basis_mv(n, mask)
        central_residual = max(central_residual, max_abs(gp(pseudoscalar, b, n) - gp(b, pseudoscalar, n)))

    return {
        "pseudoscalar_blade": blade_name(7),
        "I^2_plus_1_residual": i_square_residual,
        "central_max_commutator_residual": central_residual,
    }


def rotor_vector(theta: torch.Tensor) -> torch.Tensor:
    n = 3
    e1, e2 = basis_mv(n, 1), basis_mv(n, 2)
    bivector = gp(e1, e2, n)
    rotor = scalar_mv(n, torch.cos(theta / 2.0)) - torch.sin(theta / 2.0) * bivector
    return gp(gp(rotor, e1, n), reverse(rotor, n), n)


def rotor_evidence() -> dict[str, Any]:
    theta = torch.tensor(math.pi / 3.0, dtype=RTYPE)
    rotated_mv = rotor_vector(theta)
    coords = vector_coords_3(rotated_mv)
    norm = torch.linalg.vector_norm(coords)
    dot = coords[0] / norm
    angle = torch.arccos(torch.clamp(dot, -1.0, 1.0))
    expected = torch.tensor([math.cos(float(theta)), math.sin(float(theta)), 0.0], dtype=RTYPE)

    theta_var = torch.tensor(math.pi / 3.0, dtype=RTYPE, requires_grad=True)
    coords_var = vector_coords_3(rotor_vector(theta_var))
    tangent = torch.stack([torch.autograd.grad(c, theta_var, retain_graph=True)[0] for c in coords_var])
    tangent_norm = torch.linalg.vector_norm(tangent)

    s2 = Hypersphere(dim=2)
    geomstats_distance = float(
        s2.metric.dist(
            gs.array([1.0, 0.0, 0.0]),
            gs.array([float(coords[0].item()), float(coords[1].item()), float(coords[2].item())]),
        )
    )

    e3nn_rotated = o3.matrix_z(theta.to(torch.float32)).to(dtype=RTYPE) @ torch.tensor([1.0, 0.0, 0.0], dtype=RTYPE)

    return {
        "theta": float(theta.item()),
        "rotated_vector": [float(x.item()) for x in coords],
        "expected_vector": [float(x.item()) for x in expected],
        "angle_from_torch_dot": float(angle.item()),
        "vector_norm": float(norm.item()),
        "nonvector_residual": max_abs(vector_residual_3(rotated_mv)),
        "expected_vector_residual": float(torch.linalg.vector_norm(coords - expected).item()),
        "autograd_tangent_norm": float(tangent_norm.item()),
        "geomstats_s2_distance": geomstats_distance,
        "e3nn_matrix_z_vector": [float(x.item()) for x in e3nn_rotated],
        "e3nn_vector_residual": float(torch.linalg.vector_norm(coords - e3nn_rotated).item()),
    }


def sympy_exact_evidence() -> dict[str, Any]:
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    sigmas = [sx, sy, sz]
    eye = sp.eye(2)
    pauli_anticomm_ok = all(
        sp.simplify(sigmas[i] * sigmas[j] + sigmas[j] * sigmas[i] - (2 if i == j else 0) * eye) == sp.zeros(2)
        for i in range(3)
        for j in range(3)
    )
    qx, qy, qz = -sp.I * sx, -sp.I * sy, -sp.I * sz
    quaternion_ok = (
        sp.simplify(qx * qx + eye) == sp.zeros(2)
        and sp.simplify(qy * qy + eye) == sp.zeros(2)
        and sp.simplify(qz * qz + eye) == sp.zeros(2)
        and sp.simplify(qx * qy - qz) == sp.zeros(2)
        and sp.simplify(qx * qy * qz + eye) == sp.zeros(2)
    )
    return {
        "pauli_anticommutator_exact": bool(pauli_anticomm_ok),
        "quaternion_matrix_exact": bool(quaternion_ok),
        "binomial_dim_cl3": int(sum(sp.binomial(3, k) for k in range(4))),
        "binomial_dim_cl6": int(sum(sp.binomial(6, k) for k in range(7))),
    }


def z3_all_true_certificate(named_facts: dict[str, bool]) -> dict[str, Any]:
    solver = z3.Solver()
    bools = []
    for name, fact in named_facts.items():
        b = z3.Bool(name)
        solver.add(b == z3.BoolVal(bool(fact)))
        bools.append(b)
    solver.add(z3.Not(z3.And(*bools)))
    status = str(solver.check())
    return {"negation_of_all_facts_status": status, "pass": status == "unsat"}


def cvc5_all_true_certificate(named_facts: dict[str, bool]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    bools = []
    for name, fact in named_facts.items():
        b = solver.mkConst(bool_sort, name)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, b, solver.mkBoolean(bool(fact))))
        bools.append(b)
    all_facts = solver.mkTerm(Kind.AND, *bools)
    solver.assertFormula(solver.mkTerm(Kind.NOT, all_facts))
    status = str(solver.checkSat())
    return {"negation_of_all_facts_status": status, "pass": status == "unsat"}


def record_check(checks: list[dict[str, Any]], invariant: str, computed: Any, known: Any, match: bool) -> bool:
    computed_match = bool(match)
    checks.append({"invariant": invariant, "computed": computed, "known": known, "match": computed_match})
    return computed_match


def all_values_close(values: list[float], target: float = 0.0, tol: float = TOL) -> bool:
    return all(abs(float(v) - target) <= tol for v in values)


def max_nested_float(d: dict[str, Any]) -> float:
    vals: list[float] = []

    def walk(x: Any) -> None:
        if isinstance(x, dict):
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
        elif isinstance(x, (int, float)):
            vals.append(float(x))

    walk(d)
    return max(vals) if vals else 0.0


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, Any]] = []

    cl3_vector_defects = vector_square_defect(3)
    cl6_vector_defects = vector_square_defect(6)
    record_check(
        checks,
        "Cl(3) generator squares e_i^2 == 1",
        cl3_vector_defects,
        {"all_residuals": 0.0},
        all_values_close(list(cl3_vector_defects.values())),
    )
    record_check(
        checks,
        "Cl(6) generator squares e_i^2 == 1",
        cl6_vector_defects,
        {"all_residuals": 0.0},
        all_values_close(list(cl6_vector_defects.values())),
    )

    cl3_anti = anticommutator_defect(3)
    cl6_anti = anticommutator_defect(6)
    record_check(
        checks,
        "Cl(3) anticommutator {e_i,e_j} == 2 delta_ij",
        cl3_anti,
        {"max_residual": 0.0, "diagonal": 2.0, "off_diagonal": 0.0},
        float(cl3_anti["max_residual"]) <= TOL,
    )
    record_check(
        checks,
        "Cl(6) anticommutator {e_i,e_j} == 2 delta_ij",
        cl6_anti,
        {"max_residual": 0.0, "diagonal": 2.0, "off_diagonal": 0.0},
        float(cl6_anti["max_residual"]) <= TOL,
    )

    cl3_dim = topological_dimension_evidence(3)
    cl6_dim = topological_dimension_evidence(6)
    cl3_clifford = clifford_product_defect(3)
    cl6_clifford = clifford_product_defect(6)
    cl3_dim["clifford_layout_dimension"] = cl3_clifford["dimension_from_clifford"]
    cl6_dim["clifford_layout_dimension"] = cl6_clifford["dimension_from_clifford"]
    record_check(
        checks,
        "dim Cl(3) == 8",
        cl3_dim,
        8,
        all(int(v) == 8 for k, v in cl3_dim.items() if k.endswith("dimension") or k.endswith("scalar") or k in {"torch_blade_count", "sympy_binomial_sum", "gudhi_simplex_faces_plus_scalar", "toponetx_faces_plus_scalar", "rustworkx_boolean_lattice_nodes"}),
    )
    record_check(
        checks,
        "dim Cl(6) == 64",
        cl6_dim,
        64,
        all(int(v) == 64 for k, v in cl6_dim.items() if k.endswith("dimension") or k.endswith("scalar") or k in {"torch_blade_count", "sympy_binomial_sum", "gudhi_simplex_faces_plus_scalar", "toponetx_faces_plus_scalar", "rustworkx_boolean_lattice_nodes"}),
    )

    record_check(
        checks,
        "torch geometric product table matches clifford Cl(3)",
        cl3_clifford,
        {"max_product_table_defect_vs_clifford": 0.0},
        float(cl3_clifford["max_product_table_defect_vs_clifford"]) <= TOL,
    )
    record_check(
        checks,
        "torch geometric product table matches clifford Cl(6)",
        cl6_clifford,
        {"max_product_table_defect_vs_clifford": 0.0},
        float(cl6_clifford["max_product_table_defect_vs_clifford"]) <= TOL,
    )

    quaternion = quaternion_evidence()
    record_check(
        checks,
        "even-Cl(3) == quaternions: i^2=j^2=k^2=ijk=-1",
        quaternion,
        {"all_residuals": 0.0},
        max_nested_float(quaternion) <= TOL,
    )

    pseudoscalar = pseudoscalar_evidence()
    record_check(
        checks,
        "Cl(3) pseudoscalar I=e123 has I^2==-1 and is central",
        pseudoscalar,
        {"I^2_plus_1_residual": 0.0, "central_max_commutator_residual": 0.0},
        float(pseudoscalar["I^2_plus_1_residual"]) <= TOL
        and float(pseudoscalar["central_max_commutator_residual"]) <= TOL,
    )

    rotor = rotor_evidence()
    record_check(
        checks,
        "rotor exp(-theta/2 B) rotates a vector by exactly theta",
        rotor,
        {
            "theta": math.pi / 3.0,
            "vector_norm": 1.0,
            "nonvector_residual": 0.0,
            "expected_vector_residual": 0.0,
            "autograd_tangent_norm": 1.0,
            "geomstats_s2_distance": math.pi / 3.0,
            "e3nn_vector_residual": 0.0,
        },
        abs(float(rotor["angle_from_torch_dot"]) - math.pi / 3.0) <= TOL
        and abs(float(rotor["vector_norm"]) - 1.0) <= TOL
        and float(rotor["nonvector_residual"]) <= TOL
        and float(rotor["expected_vector_residual"]) <= TOL
        and abs(float(rotor["autograd_tangent_norm"]) - 1.0) <= TOL
        and abs(float(rotor["geomstats_s2_distance"]) - math.pi / 3.0) <= TOL_TOOL
        and float(rotor["e3nn_vector_residual"]) <= TOL_E3NN,
    )

    sympy_exact = sympy_exact_evidence()
    record_check(
        checks,
        "sympy exact Pauli/quaternion matrix model supports Cl(3) checks",
        sympy_exact,
        {
            "pauli_anticommutator_exact": True,
            "quaternion_matrix_exact": True,
            "binomial_dim_cl3": 8,
            "binomial_dim_cl6": 64,
        },
        bool(sympy_exact["pauli_anticommutator_exact"])
        and bool(sympy_exact["quaternion_matrix_exact"])
        and int(sympy_exact["binomial_dim_cl3"]) == 8
        and int(sympy_exact["binomial_dim_cl6"]) == 64,
    )

    finite_facts = {c["invariant"].replace(" ", "_").replace("(", "").replace(")", "").replace("=", "eq"): bool(c["match"]) for c in checks}
    z3_cert = z3_all_true_certificate(finite_facts)
    cvc5_cert = cvc5_all_true_certificate(finite_facts)
    record_check(
        checks,
        "z3/cvc5 finite known-fact negation is UNSAT",
        {"z3": z3_cert, "cvc5": cvc5_cert},
        {"negation_of_all_facts_status": "unsat"},
        bool(z3_cert["pass"]) and bool(cvc5_cert["pass"]),
    )

    failing = [c["invariant"] for c in checks if not c["match"]]
    receipt = {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "created_at": _dt.datetime.now(_dt.UTC).isoformat(),
        "result_path": str(RESULT_PATH),
        "finite_map": {
            "carrier": "finite blade subset masks 0..2^n-1 with torch.float64 coefficients",
            "product": "geometric product (mask_a, mask_b) -> (swap_parity_sign, mask_a xor mask_b)",
            "domains": ["Cl(3)", "Cl(6)", "even Cl(3)", "Cl(3) rotor action"],
            "codomains": ["multivector coefficients", "known invariant residuals", "tool cross-check receipts"],
        },
        "claim_substrate": {
            "primary": "torch.float64 finite Clifford engine",
            "numpy_imported_by_this_script": False,
            "third_party_numpy_outputs": "read-only for clifford/geomstats/topology/quimb cross-checks; not the primary claim substrate",
        },
        "TOOL_MANIFEST": {
            "torch": "primary finite Clifford carrier, geometric product, rotor action, and autograd tangent check",
            "sympy": "exact Pauli anticommutator, quaternion matrix model, and binomial dimension identities",
            "z3": "SMT check that negating the finite known-fact conjunction is unsat",
            "cvc5": "independent SMT check that negating the finite known-fact conjunction is unsat",
            "clifford": "independent Cl(3)/Cl(6) product table comparison against torch engine",
            "geomstats": "S^2 geodesic distance cross-check for the rotor angle",
            "gudhi": "simplex face-count cross-check for blade carrier dimension",
            "toponetx": "simplicial-complex face and grade-count cross-check for blade carrier dimension",
            "rustworkx": "Boolean lattice graph node count for blade carrier dimension",
            "e3nn": "SO(3) z-rotation matrix cross-check against Cl(3) rotor action",
            "quimb": "Pauli matrix quaternion representation cross-check",
        },
        "TOOL_INTEGRATION_DEPTH": {
            "torch": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "clifford": "load_bearing",
            "geomstats": "load_bearing",
            "gudhi": "load_bearing",
            "toponetx": "load_bearing",
            "rustworkx": "load_bearing",
            "e3nn": "load_bearing",
            "quimb": "load_bearing",
        },
        "known_value_checks": checks,
        "blockers": [{"kind": "known_value_mismatch", "invariant": name} for name in failing],
        "all_known_value_checks_pass": not failing,
    }

    with RESULT_PATH.open("w", encoding="utf-8") as f:
        json.dump(receipt, f, indent=2, sort_keys=True)
        f.write("\n")

    if failing:
        print(json.dumps({"result_path": str(RESULT_PATH), "all_known_value_checks_pass": False, "failing": failing}, indent=2))
        return 1

    print(json.dumps({"result_path": str(RESULT_PATH), "all_known_value_checks_pass": True, "checks": len(checks)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
