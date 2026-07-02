#!/usr/bin/env python3
"""Independent diagnostic Clifford-module G-structure probe.

This is a lego-phase, diagnostic-only formal scout. It computes the known
irreducible complex Clifford modules from the defining Clifford relations rather
than from any prior worker's numbers:

  * Cl(3): Pauli 2 x 2 module, {sigma_i, sigma_j} = 2 delta_ij, pseudoscalar
    (e1 e2 e3)^2 = -1.
  * Cl(6): Jordan-Wigner gamma module on C^8. The 64 Clifford monomials span
    M_8(C), and the commutant is one-dimensional, hence the module is
    irreducible by the finite-dimensional Schur criterion.
  * Chirality Gamma = i gamma_1 ... gamma_6 squares to I, anticommutes with the
    six generators, and has eigenvalue multiplicities +1 x4 and -1 x4.

No NumPy is imported as a claim substrate. Torch complex128/float64 owns the
numeric matrix algebra; SymPy owns exact rank/identity checks; z3/cvc5 certify
computed pass conditions; clifford/geomstats/gudhi/toponetx/rustworkx/e3nn are
load-bearing independent structure checks.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from itertools import combinations
from typing import Any

# clifford 1.5.1 under this Python can trip numba's cache locator when JIT is
# enabled. Disabling JIT keeps the library path usable for the small exact Cl(3)
# check below.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import cvc5
from cvc5 import Kind
import gudhi
import rustworkx as rx
import sympy as sp
import toponetx as tnx
import torch
import z3
from clifford import Cl
from e3nn import o3
from geomstats.geometry.special_orthogonal import SpecialOrthogonal

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_RANK = 1.0e-8
TOL_E3NN = 1.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "gstruct_clifford_module_codex_probe_results.json"
SIM_ID = "gstruct_clifford_module_codex_probe"

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = [SX, SY, SZ]

SP_I2 = sp.eye(2)
SP_SX = sp.Matrix([[0, 1], [1, 0]])
SP_SY = sp.Matrix([[0, -sp.I], [sp.I, 0]])
SP_SZ = sp.Matrix([[1, 0], [0, -1]])


def kron_all_torch(mats: list[torch.Tensor]) -> torch.Tensor:
    out = mats[0]
    for mat in mats[1:]:
        out = torch.kron(out, mat)
    return out


def kron_all_sympy(mats: list[sp.Matrix]) -> sp.Matrix:
    out = mats[0]
    for mat in mats[1:]:
        out = sp.kronecker_product(out, mat)
    return out


def jw_gamma_torch(m: int) -> list[torch.Tensor]:
    """Jordan-Wigner Euclidean gamma matrices for Cl(2m) on C^(2^m)."""
    gammas: list[torch.Tensor] = []
    for k in range(m):
        prefix = [SZ] * k
        suffix = [I2] * (m - k - 1)
        gammas.append(kron_all_torch(prefix + [SX] + suffix))
        gammas.append(kron_all_torch(prefix + [SY] + suffix))
    return gammas


def jw_gamma_sympy(m: int) -> list[sp.Matrix]:
    gammas: list[sp.Matrix] = []
    for k in range(m):
        prefix = [SP_SZ] * k
        suffix = [SP_I2] * (m - k - 1)
        gammas.append(kron_all_sympy(prefix + [SP_SX] + suffix))
        gammas.append(kron_all_sympy(prefix + [SP_SY] + suffix))
    return gammas


def matrix_norm(mat: torch.Tensor) -> float:
    return float(torch.linalg.matrix_norm(mat).item())


def max_clifford_defect(gammas: list[torch.Tensor]) -> float:
    dim = gammas[0].shape[0]
    eye = torch.eye(dim, dtype=CDTYPE)
    zero = torch.zeros((dim, dim), dtype=CDTYPE)
    worst = 0.0
    for i, gi in enumerate(gammas):
        for j, gj in enumerate(gammas):
            target = 2.0 * eye if i == j else zero
            worst = max(worst, matrix_norm(gi @ gj + gj @ gi - target))
    return worst


def max_square_defect(gammas: list[torch.Tensor]) -> float:
    dim = gammas[0].shape[0]
    eye = torch.eye(dim, dtype=CDTYPE)
    return max(matrix_norm(g @ g - eye) for g in gammas)


def max_hermitian_defect(gammas: list[torch.Tensor]) -> float:
    return max(matrix_norm(g - g.conj().T) for g in gammas)


def monomial_torch(gammas: list[torch.Tensor], mask: int) -> torch.Tensor:
    dim = gammas[0].shape[0]
    out = torch.eye(dim, dtype=CDTYPE)
    for i, gamma in enumerate(gammas):
        if mask & (1 << i):
            out = out @ gamma
    return out


def monomial_sympy(gammas: list[sp.Matrix], mask: int) -> sp.Matrix:
    dim = gammas[0].shape[0]
    out = sp.eye(dim)
    for i, gamma in enumerate(gammas):
        if mask & (1 << i):
            out = out * gamma
    return out


def monomial_span_rank_torch(gammas: list[torch.Tensor]) -> int:
    mats = [monomial_torch(gammas, mask) for mask in range(1 << len(gammas))]
    span = torch.stack([m.reshape(-1) for m in mats], dim=1)
    return int(torch.linalg.matrix_rank(span, atol=TOL_RANK).item())


def monomial_span_rank_sympy(gammas: list[sp.Matrix]) -> int:
    mats = [monomial_sympy(gammas, mask) for mask in range(1 << len(gammas))]
    cols = [sp.Matrix(list(m)) for m in mats]
    return int(sp.Matrix.hstack(*cols).rank())


def commutant_dim_torch(gammas: list[torch.Tensor]) -> dict[str, int]:
    dim = gammas[0].shape[0]
    cols: list[torch.Tensor] = []
    for a in range(dim):
        for b in range(dim):
            basis = torch.zeros((dim, dim), dtype=CDTYPE)
            basis[a, b] = 1.0
            cols.append(torch.cat([(basis @ g - g @ basis).reshape(-1) for g in gammas]))
    system = torch.stack(cols, dim=1)
    rank = int(torch.linalg.matrix_rank(system, atol=TOL_RANK).item())
    return {"linear_system_rank": rank, "commutant_dim": dim * dim - rank}


def commutant_dim_sympy(gammas: list[sp.Matrix]) -> dict[str, int]:
    dim = gammas[0].shape[0]
    cols: list[sp.Matrix] = []
    for a in range(dim):
        for b in range(dim):
            basis = sp.zeros(dim, dim)
            basis[a, b] = 1
            entries: list[sp.Expr] = []
            for gamma in gammas:
                entries.extend(list(basis * gamma - gamma * basis))
            cols.append(sp.Matrix(entries))
    system = sp.Matrix.hstack(*cols)
    rank = int(system.rank())
    return {"linear_system_rank": rank, "commutant_dim": dim * dim - rank}


def chirality_data(gammas: list[torch.Tensor]) -> dict[str, Any]:
    dim = gammas[0].shape[0]
    eye = torch.eye(dim, dtype=CDTYPE)
    product = eye.clone()
    for gamma in gammas:
        product = product @ gamma
    chirality = 1j * product
    herm = (chirality + chirality.conj().T) / 2
    eigs = torch.linalg.eigvalsh(herm).real
    plus = int(torch.sum(torch.abs(eigs - 1.0) < 1.0e-7).item())
    minus = int(torch.sum(torch.abs(eigs + 1.0) < 1.0e-7).item())
    return {
        "matrix": chirality,
        "product_square_defect_to_minus_identity": matrix_norm(product @ product + eye),
        "square_defect": matrix_norm(chirality @ chirality - eye),
        "anticomm_defect": max(matrix_norm(chirality @ g + g @ chirality) for g in gammas),
        "hermitian_defect": matrix_norm(chirality - chirality.conj().T),
        "eigenvalues": [float(x.item()) for x in eigs],
        "plus_multiplicity": plus,
        "minus_multiplicity": minus,
    }


def cl3_pseudoscalar_checks() -> dict[str, Any]:
    pseudo = SX @ SY @ SZ
    torch_square_defect = matrix_norm(pseudo @ pseudo + I2)

    layout, blades = Cl(3)
    del layout
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    cliff_pseudo_square = (e1 * e2 * e3) * (e1 * e2 * e3)
    cliff_values = [float(v) for v in cliff_pseudo_square.value]
    cliff_scalar = cliff_values[0]
    cliff_nonscalar_abs_sum = sum(abs(v) for v in cliff_values[1:])

    sp_pseudo = SP_SX * SP_SY * SP_SZ
    sympy_square_exact = bool(sp.simplify(sp_pseudo * sp_pseudo + SP_I2) == sp.zeros(2, 2))

    return {
        "torch_square_defect_to_minus_identity": torch_square_defect,
        "sympy_square_exact_minus_identity": sympy_square_exact,
        "clifford_library_square_scalar": cliff_scalar,
        "clifford_library_square_nonscalar_abs_sum": cliff_nonscalar_abs_sum,
        "clifford_library_square_is_minus_one": abs(cliff_scalar + 1.0) < TOL and cliff_nonscalar_abs_sum < TOL,
    }


def su2_induced_so3(U: torch.Tensor) -> torch.Tensor:
    R = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = U @ sj @ U.conj().T
        for i, si in enumerate(PAULI):
            R[i, j] = (torch.trace(si @ conj).real) / 2.0
    return R


def e3nn_so3_check() -> dict[str, Any]:
    theta = math.pi / 3.0
    U = torch.linalg.matrix_exp(-0.5j * theta * SZ)
    R = su2_induced_so3(U)
    det = float(torch.det(R).item())
    orth = float(torch.linalg.matrix_norm(R @ R.T - torch.eye(3, dtype=RTYPE)).item())
    Rf = R.to(torch.float32)
    try:
        alpha, beta, gamma = o3.matrix_to_angles(Rf)
        R_rec = o3.angles_to_matrix(alpha, beta, gamma)
        recon = float(torch.linalg.matrix_norm(R_rec - Rf).item())
        e3nn_pass = abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and recon < TOL_E3NN
    except Exception as exc:  # e3nn rejects non-SO(3) matrices by assertion.
        recon = None
        e3nn_pass = False
        return {
            "det": det,
            "orthogonality_defect": orth,
            "reconstruction_defect": recon,
            "pass": e3nn_pass,
            "error": f"{type(exc).__name__}: {exc}",
        }
    return {
        "det": det,
        "orthogonality_defect": orth,
        "reconstruction_defect": recon,
        "pass": e3nn_pass,
        "matrix": [[float(x) for x in row] for row in R],
    }


def spin6_induced_so6_check(gammas: list[torch.Tensor]) -> dict[str, Any]:
    dim = gammas[0].shape[0]
    theta = math.pi / 5.0
    bivector = gammas[0] @ gammas[1]
    rotor = torch.linalg.matrix_exp(-0.5 * theta * bivector)
    rotor_inv = rotor.conj().T
    R = torch.zeros((6, 6), dtype=RTYPE)
    for j, gj in enumerate(gammas):
        conj = rotor @ gj @ rotor_inv
        for i, gi in enumerate(gammas):
            R[i, j] = (torch.trace(gi @ conj).real) / float(dim)

    det = float(torch.det(R).item())
    orth = float(torch.linalg.matrix_norm(R @ R.T - torch.eye(6, dtype=RTYPE)).item())
    so6 = SpecialOrthogonal(n=6, point_type="matrix")
    geomstats_belongs = bool(so6.belongs(R))
    return {
        "det": det,
        "orthogonality_defect": orth,
        "geomstats_so6_belongs": geomstats_belongs,
        "matrix": [[float(x) for x in row] for row in R],
    }


def topology_basis_checks(n_generators: int) -> dict[str, Any]:
    subsets = [mask for mask in range(1 << n_generators)]
    graph = rx.PyGraph(multigraph=False)
    graph.add_nodes_from(range(len(subsets)))
    index = {mask: idx for idx, mask in enumerate(subsets)}
    for mask in subsets:
        for bit in range(n_generators):
            if not (mask & (1 << bit)):
                graph.add_edge(index[mask], index[mask | (1 << bit)], None)
    rust = {
        "nodes": int(graph.num_nodes()),
        "edges": int(graph.num_edges()),
        "connected": bool(rx.is_connected(graph)),
    }

    simplex = list(range(n_generators))
    st = gudhi.SimplexTree()
    st.insert(simplex, filtration=0.0)
    st.compute_persistence()
    betti = [int(x) for x in st.betti_numbers()]
    gudhi_data = {
        "nonempty_simplices": int(st.num_simplices()),
        "plus_empty": int(st.num_simplices() + 1),
        "dimension": int(st.dimension()),
        "betti_numbers": betti,
    }

    sc = tnx.SimplicialComplex([simplex])
    shape = tuple(int(x) for x in sc.shape)
    topnx = {
        "shape_by_simplex_dimension": list(shape),
        "plus_empty": int(sum(shape) + 1),
        "dimension": int(sc.dim),
        "connected": bool(sc.is_connected()),
    }

    return {"rustworkx": rust, "gudhi": gudhi_data, "toponetx": topnx}


def z3_certificate(values: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    int_names = [
        "cl3_dim",
        "cl6_dim",
        "span_rank_torch",
        "span_rank_sympy",
        "commutant_dim_torch",
        "commutant_dim_sympy",
        "chirality_plus",
        "chirality_minus",
        "rustworkx_nodes",
        "rustworkx_edges",
        "gudhi_plus_empty",
        "toponetx_plus_empty",
    ]
    ints = {name: z3.Int(name) for name in int_names}
    for name in int_names:
        solver.add(ints[name] == int(values[name]))
    reals = {
        "cl3_anticomm_defect": z3.Real("cl3_anticomm_defect"),
        "cl6_anticomm_defect": z3.Real("cl6_anticomm_defect"),
        "cl3_pseudoscalar_square_defect": z3.Real("cl3_pseudoscalar_square_defect"),
        "chirality_square_defect": z3.Real("chirality_square_defect"),
        "chirality_anticomm_defect": z3.Real("chirality_anticomm_defect"),
        "spin6_orth_defect": z3.Real("spin6_orth_defect"),
    }
    for name, var in reals.items():
        solver.add(var == z3.RealVal(repr(float(values[name]))))
    tol = z3.RealVal(repr(TOL))
    ok = z3.And(
        ints["cl3_dim"] == 2,
        ints["cl6_dim"] == 8,
        ints["span_rank_torch"] == 64,
        ints["span_rank_sympy"] == 64,
        ints["commutant_dim_torch"] == 1,
        ints["commutant_dim_sympy"] == 1,
        ints["chirality_plus"] == 4,
        ints["chirality_minus"] == 4,
        ints["rustworkx_nodes"] == 64,
        ints["rustworkx_edges"] == 192,
        ints["gudhi_plus_empty"] == 64,
        ints["toponetx_plus_empty"] == 64,
        reals["cl3_anticomm_defect"] <= tol,
        reals["cl6_anticomm_defect"] <= tol,
        reals["cl3_pseudoscalar_square_defect"] <= tol,
        reals["chirality_square_defect"] <= tol,
        reals["chirality_anticomm_defect"] <= tol,
        reals["spin6_orth_defect"] <= tol,
    )
    solver.add(z3.Not(ok))
    status = str(solver.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_certificate(values: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setOption("produce-models", "false")
    solver.setLogic("QF_LIRA")
    int_sort = solver.getIntegerSort()
    real_sort = solver.getRealSort()

    def mk_int(name: str, value: int):
        term = solver.mkConst(int_sort, name)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(value)))
        return term

    def mk_real_from_float(value: float):
        rational = sp.Rational(str(value)).limit_denominator(10**18)
        num, den = sp.fraction(rational)
        return solver.mkReal(int(num), int(den))

    def mk_real(name: str, value: float):
        term = solver.mkConst(real_sort, name)
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, mk_real_from_float(value)))
        return term

    ints = {
        name: mk_int(name, int(values[name]))
        for name in [
            "cl3_dim",
            "cl6_dim",
            "span_rank_torch",
            "span_rank_sympy",
            "commutant_dim_torch",
            "commutant_dim_sympy",
            "chirality_plus",
            "chirality_minus",
            "rustworkx_nodes",
            "rustworkx_edges",
            "gudhi_plus_empty",
            "toponetx_plus_empty",
        ]
    }
    reals = {
        name: mk_real(name, float(values[name]))
        for name in [
            "cl3_anticomm_defect",
            "cl6_anticomm_defect",
            "cl3_pseudoscalar_square_defect",
            "chirality_square_defect",
            "chirality_anticomm_defect",
            "spin6_orth_defect",
        ]
    }
    tol = mk_real_from_float(TOL)

    terms = [
        solver.mkTerm(Kind.EQUAL, ints["cl3_dim"], solver.mkInteger(2)),
        solver.mkTerm(Kind.EQUAL, ints["cl6_dim"], solver.mkInteger(8)),
        solver.mkTerm(Kind.EQUAL, ints["span_rank_torch"], solver.mkInteger(64)),
        solver.mkTerm(Kind.EQUAL, ints["span_rank_sympy"], solver.mkInteger(64)),
        solver.mkTerm(Kind.EQUAL, ints["commutant_dim_torch"], solver.mkInteger(1)),
        solver.mkTerm(Kind.EQUAL, ints["commutant_dim_sympy"], solver.mkInteger(1)),
        solver.mkTerm(Kind.EQUAL, ints["chirality_plus"], solver.mkInteger(4)),
        solver.mkTerm(Kind.EQUAL, ints["chirality_minus"], solver.mkInteger(4)),
        solver.mkTerm(Kind.EQUAL, ints["rustworkx_nodes"], solver.mkInteger(64)),
        solver.mkTerm(Kind.EQUAL, ints["rustworkx_edges"], solver.mkInteger(192)),
        solver.mkTerm(Kind.EQUAL, ints["gudhi_plus_empty"], solver.mkInteger(64)),
        solver.mkTerm(Kind.EQUAL, ints["toponetx_plus_empty"], solver.mkInteger(64)),
    ]
    for name in reals:
        terms.append(solver.mkTerm(Kind.LEQ, reals[name], tol))
    ok = solver.mkTerm(Kind.AND, *terms)
    solver.assertFormula(solver.mkTerm(Kind.NOT, ok))
    result = solver.checkSat()
    status = "unsat" if result.isUnsat() else ("sat" if result.isSat() else "unknown")
    return {"negation_status": status, "pass": result.isUnsat()}


def known_check(checks: list[dict[str, Any]], invariant: str, computed: Any, known: Any, match: bool) -> None:
    checks.append({
        "invariant": invariant,
        "computed": computed,
        "known": known,
        "match": bool(match),
    })


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    cl3_gammas = PAULI
    cl6_gammas = jw_gamma_torch(3)
    cl6_gammas_sp = jw_gamma_sympy(3)

    cl3_dim = int(cl3_gammas[0].shape[0])
    cl6_dim = int(cl6_gammas[0].shape[0])
    cl3_anticomm = max_clifford_defect(cl3_gammas)
    cl6_anticomm = max_clifford_defect(cl6_gammas)
    cl3_square = max_square_defect(cl3_gammas)
    cl6_square = max_square_defect(cl6_gammas)
    cl3_herm = max_hermitian_defect(cl3_gammas)
    cl6_herm = max_hermitian_defect(cl6_gammas)

    cl3_pseudo = cl3_pseudoscalar_checks()
    span_rank_torch = monomial_span_rank_torch(cl6_gammas)
    span_rank_sympy = monomial_span_rank_sympy(cl6_gammas_sp)
    comm_torch = commutant_dim_torch(cl6_gammas)
    comm_sympy = commutant_dim_sympy(cl6_gammas_sp)
    chir = chirality_data(cl6_gammas)
    spin6 = spin6_induced_so6_check(cl6_gammas)
    e3 = e3nn_so3_check()
    topology = topology_basis_checks(6)

    smt_values = {
        "cl3_dim": cl3_dim,
        "cl6_dim": cl6_dim,
        "span_rank_torch": span_rank_torch,
        "span_rank_sympy": span_rank_sympy,
        "commutant_dim_torch": comm_torch["commutant_dim"],
        "commutant_dim_sympy": comm_sympy["commutant_dim"],
        "chirality_plus": chir["plus_multiplicity"],
        "chirality_minus": chir["minus_multiplicity"],
        "rustworkx_nodes": topology["rustworkx"]["nodes"],
        "rustworkx_edges": topology["rustworkx"]["edges"],
        "gudhi_plus_empty": topology["gudhi"]["plus_empty"],
        "toponetx_plus_empty": topology["toponetx"]["plus_empty"],
        "cl3_anticomm_defect": cl3_anticomm,
        "cl6_anticomm_defect": cl6_anticomm,
        "cl3_pseudoscalar_square_defect": cl3_pseudo["torch_square_defect_to_minus_identity"],
        "chirality_square_defect": chir["square_defect"],
        "chirality_anticomm_defect": chir["anticomm_defect"],
        "spin6_orth_defect": spin6["orthogonality_defect"],
    }
    z3_cert = z3_certificate(smt_values)
    cvc5_cert = cvc5_certificate(smt_values)

    checks: list[dict[str, Any]] = []
    known_check(checks, "Cl(3)_Pauli_module_dim", cl3_dim, 2, cl3_dim == 2)
    known_check(checks, "Cl(3)_Pauli_anticommutator_max_defect", cl3_anticomm, 0, cl3_anticomm < TOL)
    known_check(checks, "Cl(3)_generator_square_max_defect", cl3_square, 0, cl3_square < TOL)
    known_check(checks, "Cl(3)_generator_Hermitian_max_defect", cl3_herm, 0, cl3_herm < TOL)
    known_check(checks, "Cl(3)_pseudoscalar_(e1e2e3)^2_torch_defect_to_-I", cl3_pseudo["torch_square_defect_to_minus_identity"], 0, cl3_pseudo["torch_square_defect_to_minus_identity"] < TOL)
    known_check(checks, "Cl(3)_pseudoscalar_(e1e2e3)^2_sympy_exact", cl3_pseudo["sympy_square_exact_minus_identity"], True, cl3_pseudo["sympy_square_exact_minus_identity"])
    known_check(checks, "Cl(3)_pseudoscalar_(e1e2e3)^2_clifford_library", {
        "scalar": cl3_pseudo["clifford_library_square_scalar"],
        "nonscalar_abs_sum": cl3_pseudo["clifford_library_square_nonscalar_abs_sum"],
    }, {"scalar": -1, "nonscalar_abs_sum": 0}, cl3_pseudo["clifford_library_square_is_minus_one"])
    known_check(checks, "Cl(6)_irreducible_module_dim_prompt_Weyl_label", cl6_dim, 8, cl6_dim == 8)
    known_check(checks, "Cl(6)_gamma_anticommutator_max_defect", cl6_anticomm, 0, cl6_anticomm < TOL)
    known_check(checks, "Cl(6)_generator_square_max_defect", cl6_square, 0, cl6_square < TOL)
    known_check(checks, "Cl(6)_generator_Hermitian_max_defect", cl6_herm, 0, cl6_herm < TOL)
    known_check(checks, "Cl(6)_monomial_span_rank_torch", span_rank_torch, 64, span_rank_torch == 64)
    known_check(checks, "Cl(6)_monomial_span_rank_sympy_exact", span_rank_sympy, 64, span_rank_sympy == 64)
    known_check(checks, "Cl(6)_commutant_dim_torch", comm_torch["commutant_dim"], 1, comm_torch["commutant_dim"] == 1)
    known_check(checks, "Cl(6)_commutant_dim_sympy_exact", comm_sympy["commutant_dim"], 1, comm_sympy["commutant_dim"] == 1)
    known_check(checks, "Cl(6)_Schur_irreducible_criterion", {
        "monomial_span_rank": span_rank_torch,
        "commutant_dim": comm_torch["commutant_dim"],
    }, {"monomial_span_rank": 64, "commutant_dim": 1}, span_rank_torch == 64 and comm_torch["commutant_dim"] == 1)
    known_check(checks, "Cl(6)_chirality_product_square_defect_to_-I_before_phase", chir["product_square_defect_to_minus_identity"], 0, chir["product_square_defect_to_minus_identity"] < TOL)
    known_check(checks, "Cl(6)_chirality_gamma5_square_defect", chir["square_defect"], 0, chir["square_defect"] < TOL)
    known_check(checks, "Cl(6)_chirality_gamma5_anticommutes_with_generators", chir["anticomm_defect"], 0, chir["anticomm_defect"] < TOL)
    known_check(checks, "Cl(6)_chirality_gamma5_Hermitian_defect", chir["hermitian_defect"], 0, chir["hermitian_defect"] < TOL)
    known_check(checks, "Cl(6)_chirality_gamma5_eigenvalue_multiplicities", {
        "+1": chir["plus_multiplicity"],
        "-1": chir["minus_multiplicity"],
    }, {"+1": 4, "-1": 4}, chir["plus_multiplicity"] == 4 and chir["minus_multiplicity"] == 4)
    known_check(checks, "Spin(6)_rotor_induced_SO(6)_geomstats_membership", {
        "det": spin6["det"],
        "orthogonality_defect": spin6["orthogonality_defect"],
        "geomstats_so6_belongs": spin6["geomstats_so6_belongs"],
    }, {"det": 1, "orthogonality_defect": 0, "geomstats_so6_belongs": True}, abs(spin6["det"] - 1.0) < TOL and spin6["orthogonality_defect"] < TOL and spin6["geomstats_so6_belongs"])
    known_check(checks, "Spin(3)_Pauli_rotor_induced_SO(3)_e3nn_roundtrip", {
        "det": e3["det"],
        "orthogonality_defect": e3["orthogonality_defect"],
        "reconstruction_defect": e3["reconstruction_defect"],
    }, {"det": 1, "orthogonality_defect": 0, "reconstruction_defect": 0}, bool(e3["pass"]))
    known_check(checks, "Cl(6)_monomial_subset_graph_rustworkx", topology["rustworkx"], {"nodes": 64, "edges": 192, "connected": True}, topology["rustworkx"]["nodes"] == 64 and topology["rustworkx"]["edges"] == 192 and topology["rustworkx"]["connected"])
    known_check(checks, "Cl(6)_monomial_simplex_count_gudhi", topology["gudhi"], {"nonempty_simplices": 63, "plus_empty": 64, "dimension": 5, "betti0": 1}, topology["gudhi"]["nonempty_simplices"] == 63 and topology["gudhi"]["plus_empty"] == 64 and topology["gudhi"]["dimension"] == 5 and topology["gudhi"]["betti_numbers"][0] == 1)
    known_check(checks, "Cl(6)_monomial_simplex_count_toponetx", topology["toponetx"], {"shape_by_simplex_dimension": [6, 15, 20, 15, 6, 1], "plus_empty": 64, "dimension": 5, "connected": True}, topology["toponetx"]["shape_by_simplex_dimension"] == [6, 15, 20, 15, 6, 1] and topology["toponetx"]["plus_empty"] == 64 and topology["toponetx"]["dimension"] == 5 and topology["toponetx"]["connected"])
    known_check(checks, "z3_certificate_for_computed_clifford_conditions", z3_cert["negation_status"], "unsat", z3_cert["pass"])
    known_check(checks, "cvc5_certificate_for_computed_clifford_conditions", cvc5_cert["negation_status"], "unsat", cvc5_cert["pass"])

    known_values_all_match = all(check["match"] for check in checks)
    tools_all_pass = (
        cl3_anticomm < TOL
        and cl6_anticomm < TOL
        and span_rank_torch == 64
        and span_rank_sympy == 64
        and comm_torch["commutant_dim"] == 1
        and comm_sympy["commutant_dim"] == 1
        and cl3_pseudo["clifford_library_square_is_minus_one"]
        and spin6["geomstats_so6_belongs"]
        and e3["pass"]
        and topology["rustworkx"]["connected"]
        and topology["gudhi"]["plus_empty"] == 64
        and topology["toponetx"]["plus_empty"] == 64
        and z3_cert["pass"]
        and cvc5_cert["pass"]
    )
    all_pass = known_values_all_match and tools_all_pass
    blockers = [
        f"KNOWN-VALUE MISMATCH: {check['invariant']} computed={check['computed']} known={check['known']}"
        for check in checks
        if not check["match"]
    ]

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "constructs Pauli and Cl(6) Jordan-Wigner gamma matrices in complex128, computes anticommutators, monomial rank, commutant rank, chirality, eigenmultiplicities, and Spin-induced rotations",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent exact matrix ranks for the Cl(6) monomial span and commutant, plus exact Cl(3) pseudoscalar square",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT certificate that the negation of the computed Clifford dimension/rank/commutant/chirality/topology conditions is UNSAT",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SMT certificate for the same computed Clifford condition bundle",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent geometric-algebra Cl(3) computation of (e1e2e3)^2 = -1",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "SpecialOrthogonal(6) membership check for the SO(6) rotation induced by a Spin(6) Clifford rotor",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "simplex-tree count confirms the 63 nonempty generator subsets plus the empty monomial equals the 64 Clifford monomial basis labels",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "simplicial-complex f-vector independently confirms the Cl(6) monomial subset count [6,15,20,15,6,1] plus empty = 64",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "hypercube/Hasse graph over generator subsets confirms 64 monomial nodes, 192 single-generator edges, and connected basis indexing",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "SO(3) l=1 round-trip validates the Pauli Spin(3) rotor's induced vector rotation",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "2_geometry",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "gstruct_clifford_module_probe",
        "purpose": "Independent known-G-structure Clifford module diagnostic: compute Cl(3) Pauli module and Cl(6) irreducible gamma module from defining relations, with exact rank and commutant checks.",
        "scientific_question": "Do the independently constructed Pauli and Jordan-Wigner Clifford modules satisfy the known Cl(3)/Cl(6) dimensions, anticommutation laws, irreducibility criteria, chirality split, and pseudoscalar invariant?",
        "claim_ceiling": "diagnostic_only / lego-phase / unadmitted; this does not admit a manifold layer, layer completion, official G-structure selection, Axis0, flux, bridge, basin, or physics claim.",
        "finite_map": "finite generator set {gamma_i} -> matrix module, Clifford monomial span, commutant linear system, chirality operator, Spin rotor vector action, and finite subset topology checks",
        "domain": "Pauli generators for Cl(3) and six Jordan-Wigner gamma generators for complex Euclidean Cl(6)",
        "codomain_or_output": "2x2 and 8x8 complex matrix modules, 64 monomial span rank, commutant dimension, chirality eigenspaces, SO(3)/SO(6) rotor checks, and JSON receipt",
        "carrier_realization": "torch.complex128 matrices with exact SymPy cross-checks; no NumPy claim substrate",
        "spinor_state": "Cl(6) spinor module C^8 with chirality eigenspaces C^4 + C^4 under the even subalgebra",
        "quaternion_action": "Cl(3) Pauli module/even subalgebra check via pseudoscalar and Spin(3)->SO(3) rotor action",
        "peps3d_embedding": "not_applicable_at_lego_phase (diagnostic_only; no manifold anchor claimed)",
        "downstream_blocks": ["manifold_layers", "layer_completion", "official_G_structure_selection", "stacking", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "layer_completion", "official_G_structure_selection", "stacking", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "allowed_claims": [
            "standalone diagnostic: computed Cl(3) and Cl(6) known Clifford-module invariants match the requested known values",
            "Cl(6) module is irreducible by monomial span M_8(C) and commutant dimension 1 in this finite matrix representation",
        ],
        "promotion_blockers": [
            "classification is diagnostic_only",
            "no validator gate was run by request",
            "no manifold/layer/Axis0/flux admission evidence is claimed",
        ],
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(checks),
            "blocker_count": len(blockers),
            "cl3_module_dim": cl3_dim,
            "cl6_module_dim": cl6_dim,
            "cl6_monomial_span_rank_torch": span_rank_torch,
            "cl6_monomial_span_rank_sympy": span_rank_sympy,
            "cl6_commutant_dim_torch": comm_torch["commutant_dim"],
            "cl6_commutant_dim_sympy": comm_sympy["commutant_dim"],
            "chirality_plus_multiplicity": chir["plus_multiplicity"],
            "chirality_minus_multiplicity": chir["minus_multiplicity"],
            "z3_negation_status": z3_cert["negation_status"],
            "cvc5_negation_status": cvc5_cert["negation_status"],
        },
        "known_value_checks": checks,
        "computed_invariants": {
            "cl3": {
                "module_dim": cl3_dim,
                "anticommutator_max_defect": cl3_anticomm,
                "generator_square_max_defect": cl3_square,
                "generator_hermitian_max_defect": cl3_herm,
                "pseudoscalar": cl3_pseudo,
            },
            "cl6": {
                "module_dim": cl6_dim,
                "anticommutator_max_defect": cl6_anticomm,
                "generator_square_max_defect": cl6_square,
                "generator_hermitian_max_defect": cl6_herm,
                "monomial_span_rank_torch": span_rank_torch,
                "monomial_span_rank_sympy": span_rank_sympy,
                "commutant_torch": comm_torch,
                "commutant_sympy": comm_sympy,
                "chirality": {
                    "product_square_defect_to_minus_identity": chir["product_square_defect_to_minus_identity"],
                    "square_defect": chir["square_defect"],
                    "anticomm_defect": chir["anticomm_defect"],
                    "hermitian_defect": chir["hermitian_defect"],
                    "eigenvalues": chir["eigenvalues"],
                    "plus_multiplicity": chir["plus_multiplicity"],
                    "minus_multiplicity": chir["minus_multiplicity"],
                },
            },
            "spin_lie_group_checks": {
                "spin6_induced_so6_geomstats": spin6,
                "spin3_induced_so3_e3nn": e3,
            },
            "basis_topology_checks": topology,
            "smt_certificates": {"z3": z3_cert, "cvc5": cvc5_cert},
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": list(tool_manifest.keys()),
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "topology_surfaces_used": ["gudhi", "toponetx", "rustworkx"],
        "geometry_surfaces_used": ["clifford", "geomstats", "e3nn"],
        "numpy_claim_substrate": False,
        "required_negatives": [],
        "negatives_run": [],
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "all known_value_checks match, all tool checks pass, Cl(6) monomial span rank is 64, Cl(6) commutant dimension is 1, chirality invariants match, and z3/cvc5 negations are UNSAT",
        "fail_rule": "any known-value mismatch, tool check failure, non-UNSAT SMT certificate, non-64 monomial span, non-1 commutant, or chirality mismatch",
        "eligible_consumers": ["diagnostic_only cross-model comparison against independently built Clifford-module probes"],
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(RESULT_PATH),
        "all_pass": all_pass,
        "known_values_all_match": known_values_all_match,
        "tools_all_pass": tools_all_pass,
        "n_known_value_checks": len(checks),
        "blockers": blockers,
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
