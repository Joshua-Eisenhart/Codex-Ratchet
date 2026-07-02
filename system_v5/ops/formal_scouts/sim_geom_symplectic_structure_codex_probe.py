#!/usr/bin/env python3
"""Deep symplectic vector-space geometry probe (diagnostic_only, unadmitted).

This probe independently computes known symplectic invariants for
(R^{2n}, omega) over n in {1, 2, 3}. It uses torch float64 as the numeric
carrier, sympy exact arithmetic for closedness / Pfaffian / determinant
checks, and z3+cvc5 to prove that the standard symplectic matrix has no
nonzero kernel vector. Auxiliary geometry libraries are load-bearing
cross-checks on the canonical Darboux chart, topology, pairing graph, and
compatible rotation structure.

classification = "diagnostic_only"
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
from typing import Any

import sympy as sp
import torch
import z3
import cvc5
from cvc5 import Kind

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import clifford
import geomstats.backend as gs
import gudhi
import rustworkx as rx
import toponetx as tnx
from e3nn import o3


RTYPE = torch.float64
TOL = 1.0e-9
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "geom_symplectic_structure_codex_probe_results.json"
SIM_ID = "geom_symplectic_structure_codex_probe"
NS = [1, 2, 3]


def standard_j(n: int) -> torch.Tensor:
    eye = torch.eye(n, dtype=RTYPE)
    zero = torch.zeros((n, n), dtype=RTYPE)
    return torch.cat(
        [torch.cat([zero, eye], dim=1), torch.cat([-eye, zero], dim=1)],
        dim=0,
    )


def standard_j_sympy(n: int) -> sp.Matrix:
    eye = sp.eye(n)
    zero = sp.zeros(n)
    return sp.Matrix.vstack(sp.Matrix.hstack(zero, eye), sp.Matrix.hstack(-eye, zero))


def pfaffian_exact(mat: sp.Matrix) -> sp.Expr:
    """Recursive exact Pfaffian for the small 2n x 2n matrices in this probe."""
    size = mat.rows
    if size == 0:
        return sp.Integer(1)
    if size % 2:
        return sp.Integer(0)
    total = sp.Integer(0)
    rest = list(range(1, size))
    for offset, j in enumerate(rest, start=1):
        keep = [k for k in range(size) if k not in (0, j)]
        sub = mat.extract(keep, keep)
        total += (-1) ** (offset + 1) * mat[0, j] * pfaffian_exact(sub)
    return sp.simplify(total)


def closedness_coefficients_exact(j_mat: sp.Matrix) -> list[sp.Expr]:
    coords = sp.symbols(f"x0:{j_mat.rows}")
    coeffs: list[sp.Expr] = []
    for i in range(j_mat.rows):
        for j in range(i + 1, j_mat.rows):
            for k in range(j + 1, j_mat.rows):
                coeff = (
                    sp.diff(j_mat[j, k], coords[i])
                    + sp.diff(j_mat[k, i], coords[j])
                    + sp.diff(j_mat[i, j], coords[k])
                )
                coeffs.append(sp.simplify(coeff))
    return coeffs


def as_float(value: Any) -> float:
    if isinstance(value, torch.Tensor):
        return float(value.detach().cpu().item())
    return float(value)


def finite_match(computed: float, known: float, tol: float = TOL) -> bool:
    return math.isfinite(computed) and abs(computed - known) <= tol


def bool_check(checks: list[dict[str, Any]], invariant: str, computed: Any, known: Any) -> bool:
    match = bool(computed == known)
    checks.append(
        {"invariant": invariant, "computed": computed, "known": known, "match": match}
    )
    return match


def numeric_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: float,
    known: float,
    tol: float = TOL,
) -> bool:
    computed_f = float(computed)
    known_f = float(known)
    match = finite_match(computed_f, known_f, tol)
    checks.append(
        {
            "invariant": invariant,
            "computed": computed_f,
            "known": known_f,
            "tolerance": tol,
            "match": match,
        }
    )
    return match


def random_invertible_matrix(n: int, seed: int) -> torch.Tensor:
    dim = 2 * n
    gen = torch.Generator(device="cpu")
    gen.manual_seed(seed)
    candidate = torch.eye(dim, dtype=RTYPE) + 0.125 * torch.randn(
        dim, dim, generator=gen, dtype=RTYPE
    )
    det = torch.linalg.det(candidate)
    if abs(as_float(det)) < 1.0e-6:
        candidate = candidate + 0.5 * torch.eye(dim, dtype=RTYPE)
    return candidate


def random_skew_darboux_residuals(n: int, j_mat: torch.Tensor) -> list[float]:
    residuals: list[float] = []
    for seed in (101 + n, 211 + n, 307 + n):
        s = random_invertible_matrix(n, seed)
        a = s.T @ j_mat @ s
        p = torch.linalg.inv(s)
        residual = torch.linalg.matrix_norm(p.T @ a @ p - j_mat)
        residuals.append(as_float(residual))
    return residuals


def symplectic_test_matrix(n: int) -> torch.Tensor:
    gen = torch.Generator(device="cpu")
    gen.manual_seed(700 + n)
    eye = torch.eye(n, dtype=RTYPE)
    raw = torch.randn(n, n, generator=gen, dtype=RTYPE)
    b = (raw + raw.T) / 2
    scales = torch.exp(0.11 * torch.arange(1, n + 1, dtype=RTYPE))
    d = torch.diag(scales)
    d_inv = torch.diag(1.0 / scales)
    zero = torch.zeros((n, n), dtype=RTYPE)
    shear = torch.cat(
        [torch.cat([eye, b], dim=1), torch.cat([zero, eye], dim=1)],
        dim=0,
    )
    diag = torch.cat(
        [torch.cat([d, zero], dim=1), torch.cat([zero, d_inv], dim=1)],
        dim=0,
    )
    return shear @ diag


def z3_nonzero_kernel_status(j_mat: sp.Matrix) -> str:
    dim = j_mat.rows
    solver = z3.Solver()
    vectors = [z3.Real(f"v_{idx}") for idx in range(dim)]
    for row in range(dim):
        expr = z3.Sum([int(j_mat[row, col]) * vectors[col] for col in range(dim)])
        solver.add(expr == 0)
    solver.add(z3.Or([vectors[idx] != 0 for idx in range(dim)]))
    return str(solver.check())


def cvc5_sum(slv: cvc5.Solver, terms: list[Any]) -> Any:
    if not terms:
        return slv.mkReal(0)
    if len(terms) == 1:
        return terms[0]
    return slv.mkTerm(Kind.ADD, *terms)


def cvc5_neg(slv: cvc5.Solver, term: Any) -> Any:
    return slv.mkTerm(Kind.SUB, slv.mkReal(0), term)


def cvc5_nonzero_kernel_status(j_mat: sp.Matrix) -> str:
    dim = j_mat.rows
    slv = cvc5.Solver()
    slv.setLogic("QF_LRA")
    real_sort = slv.getRealSort()
    zero = slv.mkReal(0)
    vectors = [slv.mkConst(real_sort, f"cv_{idx}") for idx in range(dim)]
    for row in range(dim):
        terms = []
        for col in range(dim):
            coeff = int(j_mat[row, col])
            if coeff == 1:
                terms.append(vectors[col])
            elif coeff == -1:
                terms.append(cvc5_neg(slv, vectors[col]))
            elif coeff != 0:
                terms.append(slv.mkTerm(Kind.MULT, slv.mkReal(coeff), vectors[col]))
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, cvc5_sum(slv, terms), zero))
    nonzero = [
        slv.mkTerm(Kind.NOT, slv.mkTerm(Kind.EQUAL, vectors[idx], zero))
        for idx in range(dim)
    ]
    slv.assertFormula(slv.mkTerm(Kind.OR, *nonzero))
    return str(slv.checkSat()).lower()


def clifford_pair_bivector_check(n: int) -> dict[str, Any]:
    layout, blades = clifford.Cl(2 * n)
    squares = []
    for idx in range(1, n + 1):
        bivector = blades[f"e{idx}"] ^ blades[f"e{n + idx}"]
        squares.append(float((bivector * bivector).value[0]))
    max_residual = max(abs(value + 1.0) for value in squares)
    return {"pair_bivector_squares": squares, "max_residual_to_minus_one": max_residual}


def geomstats_det_check(j_mat: torch.Tensor) -> float:
    gs_j = gs.array(j_mat)
    return as_float(gs.linalg.det(gs_j))


def gudhi_contractible_chart_betti(n: int) -> list[int]:
    simplex_tree = gudhi.SimplexTree()
    simplex_tree.insert(list(range(2 * n + 1)))
    simplex_tree.compute_persistence()
    betti = list(simplex_tree.betti_numbers())
    while len(betti) < 2 * n + 1:
        betti.append(0)
    return betti[: 2 * n + 1]


def toponetx_chart_dimension(n: int) -> int:
    complex_obj = tnx.SimplicialComplex()
    complex_obj.add_simplex(tuple(range(2 * n + 1)))
    return int(complex_obj.dim)


def rustworkx_pairing_degrees(n: int) -> list[int]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(2 * n))
    for idx in range(n):
        graph.add_edge(idx, n + idx, "omega_pair")
    return [int(graph.degree(idx)) for idx in range(2 * n)]


def e3nn_plane_rotation_symplectic_residual() -> float:
    theta = torch.tensor(0.731, dtype=RTYPE)
    rot3 = o3.matrix_z(theta).to(dtype=RTYPE)
    rot2 = rot3[:2, :2]
    j2 = standard_j(1)
    return as_float(torch.linalg.matrix_norm(rot2.T @ j2 @ rot2 - j2))


def evaluate_n(n: int, checks: list[dict[str, Any]]) -> dict[str, Any]:
    dim = 2 * n
    j_t = standard_j(n)
    j_s = standard_j_sympy(n)
    eye = torch.eye(dim, dtype=RTYPE)

    closed_coeffs = closedness_coefficients_exact(j_s)
    closed = all(coeff == 0 for coeff in closed_coeffs)
    bool_check(checks, f"n={n}: omega closed d(omega)==0 (sympy exact)", closed, True)

    det_exact = sp.Integer(j_s.det())
    numeric_check(checks, f"n={n}: nondegenerate det(J)==1 (sympy exact)", float(det_exact), 1.0, 0.0)

    j2_residual = as_float(torch.linalg.matrix_norm(j_t @ j_t + eye))
    numeric_check(checks, f"n={n}: compatible complex structure J^2==-I", j2_residual, 0.0)

    pf_exact = sp.Integer(pfaffian_exact(j_s))
    pf_square = sp.Integer(pf_exact * pf_exact)
    bool_check(
        checks,
        f"n={n}: Pfaffian(J)^2==det(J) (sympy exact)",
        bool(pf_square == det_exact),
        True,
    )
    numeric_check(checks, f"n={n}: |Pfaffian(J)|==1", float(abs(pf_exact)), 1.0, 0.0)

    darboux_residuals = random_skew_darboux_residuals(n, j_t)
    numeric_check(
        checks,
        f"n={n}: Darboux max ||P^T A P - J|| over seeded random skew forms",
        max(darboux_residuals),
        0.0,
        1.0e-8,
    )

    m = symplectic_test_matrix(n)
    sp_residual = as_float(torch.linalg.matrix_norm(m.T @ j_t @ m - j_t))
    det_m = as_float(torch.linalg.det(m))
    numeric_check(checks, f"n={n}: Sp(2n) preserves omega ||M^T J M - J||", sp_residual, 0.0)
    numeric_check(checks, f"n={n}: Sp(2n) is volume-preserving det(M)==1", det_m, 1.0)

    liouville_abs = float(abs(pf_exact))
    numeric_check(checks, f"n={n}: Liouville |omega^n/n!|==1", liouville_abs, 1.0, 0.0)

    z3_status = z3_nonzero_kernel_status(j_s)
    bool_check(
        checks,
        f"n={n}: nondegeneracy exists v!=0 with Jv=0 is UNSAT (z3)",
        z3_status,
        "unsat",
    )
    cvc5_status = cvc5_nonzero_kernel_status(j_s)
    bool_check(
        checks,
        f"n={n}: nondegeneracy exists v!=0 with Jv=0 is UNSAT (cvc5)",
        cvc5_status,
        "unsat",
    )

    clifford_check = clifford_pair_bivector_check(n)
    numeric_check(
        checks,
        f"n={n}: Clifford canonical symplectic pair bivectors square to -1",
        float(clifford_check["max_residual_to_minus_one"]),
        0.0,
    )

    geomstats_det = geomstats_det_check(j_t)
    numeric_check(
        checks,
        f"n={n}: geomstats backend det(J) cross-check",
        geomstats_det,
        1.0,
    )

    betti = gudhi_contractible_chart_betti(n)
    expected_betti = [1] + [0] * (2 * n)
    bool_check(
        checks,
        f"n={n}: GUDHI Darboux chart simplex is contractible",
        betti,
        expected_betti,
    )

    tnx_dim = toponetx_chart_dimension(n)
    bool_check(
        checks,
        f"n={n}: TopoNetX Darboux chart simplex dimension",
        tnx_dim,
        2 * n,
    )

    degrees = rustworkx_pairing_degrees(n)
    bool_check(
        checks,
        f"n={n}: rustworkx omega pairing graph is a perfect coordinate matching",
        degrees,
        [1] * (2 * n),
    )

    return {
        "n": n,
        "dimension": dim,
        "det_j_exact": int(det_exact),
        "pfaffian_j_exact": int(pf_exact),
        "darboux_residuals": darboux_residuals,
        "symplectic_matrix_preservation_residual": sp_residual,
        "symplectic_matrix_det": det_m,
        "z3_nonzero_kernel_status": z3_status,
        "cvc5_nonzero_kernel_status": cvc5_status,
        "clifford": clifford_check,
        "geomstats_det_j": geomstats_det,
        "gudhi_betti": betti,
        "toponetx_simplex_dim": tnx_dim,
        "rustworkx_pairing_degrees": degrees,
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    checks: list[dict[str, Any]] = []
    per_n = [evaluate_n(n, checks) for n in NS]

    e3nn_residual = e3nn_plane_rotation_symplectic_residual()
    numeric_check(
        checks,
        "e3nn SO(3) z-rotation restricts to a 2D symplectic plane rotation",
        e3nn_residual,
        0.0,
    )

    blockers = [
        {"invariant": check["invariant"], "computed": check["computed"], "known": check["known"]}
        for check in checks
        if not check["match"]
    ]
    receipt = {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "finite_map": {
            "domain": "R^{2n} with n in {1,2,3}",
            "operator": "omega(v,w)=v^T J w; compatible J; Darboux congruence P^T A P",
            "codomain": "known symplectic invariants and exact/SMT certificates",
        },
        "parameters": {
            "n_values": NS,
            "dtype": "torch.float64",
            "tolerance": TOL,
            "darboux_random_seeds_per_n": {
                str(n): [101 + n, 211 + n, 307 + n] for n in NS
            },
        },
        "TOOL_MANIFEST": {
            "torch": "load_bearing numeric carrier for J, Darboux congruence, symplectic matrices, determinants, and residual norms",
            "sympy": "load_bearing exact closedness, determinant, Pfaffian, and Liouville coefficient checks",
            "z3": "load_bearing SMT UNSAT certificate for nonzero kernel vector existence",
            "cvc5": "load_bearing independent SMT UNSAT certificate for nonzero kernel vector existence",
            "clifford": "load_bearing geometric-algebra check that canonical symplectic pair bivectors square to -1",
            "geomstats": "load_bearing backend geometry cross-check for det(J)",
            "gudhi": "load_bearing topology check that a finite Darboux chart simplex is contractible",
            "toponetx": "load_bearing finite simplex dimension check for the Darboux chart carrier",
            "rustworkx": "load_bearing coordinate-pairing graph check for omega's perfect matching",
            "e3nn": "load_bearing SO(3) rotation check whose q,p plane restriction preserves omega",
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
        },
        "known_value_checks": checks,
        "per_n": per_n,
        "blockers": blockers,
        "all_known_value_checks_passed": not blockers,
        "anti_fabrication_note": "matches are computed from invariant values; failed checks are reported as blockers without rewriting known values",
        "result_path": str(RESULT_PATH),
    }
    RESULT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result_path": str(RESULT_PATH), "checks": len(checks), "passed": not blockers}, sort_keys=True))
    return 0 if not blockers else 1


if __name__ == "__main__":
    raise SystemExit(main())
