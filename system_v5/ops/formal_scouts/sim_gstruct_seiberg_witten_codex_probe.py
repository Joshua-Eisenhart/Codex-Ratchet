#!/usr/bin/env python3
"""Discrete Seiberg-Witten G-structure / Spin^c diagnostic probe.

This is an independent known-math scout for a U(1)-twisted discrete
Seiberg-Witten structure on a periodic square lattice. It computes the objects
directly from the definitions:

  - 0, 1, 2 cochains on a 2-torus lattice, with d^2 = 0.
  - U(1) gauge potential A, curvature F = dA, and A -> A + df.
  - A gauge-twisted central-difference Dirac operator D_A on C^2 spinors.
  - The quadratic moment map sigma(phi) = phi phi^* - |phi|^2 I / 2.
  - The Cl(3)-even quaternion/su(2) basis used for self-dual Lambda+ labels.

classification = diagnostic_only. This is lego-phase evidence only and writes
the requested JSON receipt path.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/codex_ratchet_numba_cache")

IMPORT_ERRORS: list[dict[str, str]] = []

try:
    import torch
except Exception as exc:  # pragma: no cover - writes a blocker receipt
    IMPORT_ERRORS.append({"tool": "torch", "error": repr(exc)})

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "sympy", "error": repr(exc)})

try:
    import z3
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "z3", "error": repr(exc)})

try:
    import cvc5
    from cvc5 import Kind
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "cvc5", "error": repr(exc)})

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "clifford", "error": repr(exc)})

try:
    import geomstats.backend as gs
    from geomstats.geometry.special_orthogonal import SpecialOrthogonal
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "geomstats", "error": repr(exc)})

try:
    import gudhi
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "gudhi", "error": repr(exc)})

try:
    from toponetx.classes import SimplicialComplex
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "toponetx", "error": repr(exc)})

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "rustworkx", "error": repr(exc)})

try:
    from e3nn import o3
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS.append({"tool": "e3nn", "error": repr(exc)})


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "gstruct_seiberg_witten_codex_probe"
RESULT_PATH = RESULT_DIR / "gstruct_seiberg_witten_codex_probe_results.json"
CDTYPE = torch.complex128 if "torch" in globals() else None
RTYPE = torch.float64 if "torch" in globals() else None
TOL = 1.0e-9
TOL_SO3 = 1.0e-6
N = 4


def write_blocker_receipt(blockers: list[str], extra: dict[str, Any] | None = None) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "all_pass": False,
        "result_summary": {
            "all_pass": False,
            "known_values_all_match": False,
            "tools_all_pass": False,
            "blocker_count": len(blockers),
        },
        "known_value_checks": [],
        "blockers": blockers,
        "TOOL_MANIFEST": {},
        "TOOL_INTEGRATION_DEPTH": {},
    }
    if extra:
        result.update(extra)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if IMPORT_ERRORS:
    missing = [f"required tool import failed: {row['tool']} {row['error']}" for row in IMPORT_ERRORS]
    write_blocker_receipt(missing, {"import_errors": IMPORT_ERRORS})
    print(json.dumps({"wrote": str(RESULT_PATH), "all_pass": False, "blockers": missing}, indent=2))
    raise SystemExit(1)


I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
PAULI = (SX, SY, SZ)


def site_index(x: int, y: int) -> int:
    return (x % N) * N + (y % N)


def deterministic_field() -> torch.Tensor:
    vals = []
    for x in range(N):
        row = []
        for y in range(N):
            row.append(math.sin(0.37 + 0.41 * x - 0.23 * y) + 0.2 * math.cos(0.5 * x * y + 0.19))
        vals.append(row)
    return torch.tensor(vals, dtype=RTYPE)


def deterministic_connection() -> tuple[torch.Tensor, torch.Tensor]:
    ax = torch.zeros((N, N), dtype=RTYPE)
    ay = torch.zeros((N, N), dtype=RTYPE)
    for x in range(N):
        for y in range(N):
            ax[x, y] = 0.17 * math.sin(0.31 + x) + 0.11 * math.cos(0.29 + y)
            ay[x, y] = -0.13 * math.cos(0.21 + y) + 0.07 * math.sin(0.43 + x - y)
    return ax, ay


def d0(f: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    return torch.roll(f, shifts=-1, dims=0) - f, torch.roll(f, shifts=-1, dims=1) - f


def d1(ax: torch.Tensor, ay: torch.Tensor) -> torch.Tensor:
    return (torch.roll(ay, shifts=-1, dims=0) - ay) - (torch.roll(ax, shifts=-1, dims=1) - ax)


def build_covariant_differences(ax: torch.Tensor, ay: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
    sites = N * N
    kx = torch.zeros((sites, sites), dtype=CDTYPE)
    ky = torch.zeros((sites, sites), dtype=CDTYPE)
    ux = torch.exp(1j * ax.to(CDTYPE))
    uy = torch.exp(1j * ay.to(CDTYPE))
    for x in range(N):
        for y in range(N):
            row = site_index(x, y)
            xp = site_index(x + 1, y)
            xm = site_index(x - 1, y)
            yp = site_index(x, y + 1)
            ym = site_index(x, y - 1)
            kx[row, xp] += 0.5 * ux[x, y]
            kx[row, xm] += -0.5 * torch.conj(ux[(x - 1) % N, y])
            ky[row, yp] += 0.5 * uy[x, y]
            ky[row, ym] += -0.5 * torch.conj(uy[x, (y - 1) % N])
    return kx, ky


def build_dirac(ax: torch.Tensor, ay: torch.Tensor) -> dict[str, Any]:
    kx, ky = build_covariant_differences(ax, ay)
    dmat = -1j * (torch.kron(kx, SX) + torch.kron(ky, SY))
    return {
        "D": dmat,
        "Kx": kx,
        "Ky": ky,
        "kx_skew_defect": float(torch.linalg.matrix_norm(kx.conj().T + kx).item()),
        "ky_skew_defect": float(torch.linalg.matrix_norm(ky.conj().T + ky).item()),
    }


def gauge_matrix(f: torch.Tensor) -> torch.Tensor:
    phases = torch.exp(-1j * f.reshape(-1).to(CDTYPE))
    g_site = torch.diag(phases)
    return torch.kron(g_site, I2)


def sigma(phi: torch.Tensor) -> torch.Tensor:
    rho = torch.outer(phi, phi.conj())
    norm_sq = torch.vdot(phi, phi).real
    return rho - 0.5 * norm_sq.to(CDTYPE) * I2


def max_abs_matrix(m: torch.Tensor) -> float:
    return float(torch.max(torch.abs(m)).item())


def seiberg_witten_numeric() -> dict[str, Any]:
    ax, ay = deterministic_connection()
    f = deterministic_field()
    dfx, dfy = d0(f)
    curvature = d1(ax, ay)
    curvature_gauge = d1(ax + dfx, ay + dfy)
    d2 = d1(dfx, dfy)

    ddata = build_dirac(ax, ay)
    dmat = ddata["D"]
    ddata_gauge = build_dirac(ax + dfx, ay + dfy)
    dmat_gauge = ddata_gauge["D"]
    g = gauge_matrix(f)

    self_adjoint_defect = float(torch.linalg.matrix_norm(dmat - dmat.conj().T).item())
    evals = torch.linalg.eigvals(dmat)
    max_imag = float(torch.max(torch.abs(evals.imag)).item())
    eigvalsh_span = [float(torch.min(torch.linalg.eigvalsh(dmat)).item()), float(torch.max(torch.linalg.eigvalsh(dmat)).item())]
    gauge_covariance_defect = float(torch.linalg.matrix_norm(dmat_gauge - g @ dmat @ g.conj().T).item())

    phi = torch.tensor([0.73 + 0.21j, -0.37 + 0.91j], dtype=CDTYPE)
    sig = sigma(phi)
    phase = torch.exp(torch.tensor(1j * 0.733, dtype=CDTYPE))
    lam = torch.tensor(0.41 - 1.27j, dtype=CDTYPE)
    zero = torch.zeros(2, dtype=CDTYPE)
    phase_defect = float(torch.linalg.matrix_norm(sigma(phase * phi) - sig).item())
    scaling_defect = float(torch.linalg.matrix_norm(sigma(lam * phi) - (torch.abs(lam) ** 2).to(CDTYPE) * sig).item())
    zero_sigma_norm = float(torch.linalg.matrix_norm(sigma(zero)).item())

    return {
        "connection": {
            "ax": ax.tolist(),
            "ay": ay.tolist(),
            "gauge_f": f.tolist(),
        },
        "curvature": {
            "F": curvature.tolist(),
            "gauge_invariance_defect": float(torch.linalg.matrix_norm(curvature_gauge - curvature).item()),
            "max_abs_F": float(torch.max(torch.abs(curvature)).item()),
        },
        "d_squared": {
            "max_abs_d1_d0_f": float(torch.max(torch.abs(d2)).item()),
        },
        "dirac": {
            "matrix_size": list(dmat.shape),
            "self_adjoint_defect": self_adjoint_defect,
            "max_eigenvalue_imaginary_part": max_imag,
            "eigvalsh_span": eigvalsh_span,
            "gauge_covariance_defect": gauge_covariance_defect,
            "kx_skew_defect": ddata["kx_skew_defect"],
            "ky_skew_defect": ddata["ky_skew_defect"],
            "gauge_kx_skew_defect": ddata_gauge["kx_skew_defect"],
            "gauge_ky_skew_defect": ddata_gauge["ky_skew_defect"],
        },
        "sigma": {
            "matrix": [[complex(sig[i, j].item()).real if abs(complex(sig[i, j].item()).imag) < TOL else str(complex(sig[i, j].item()))
                        for j in range(2)] for i in range(2)],
            "trace_abs": abs(complex(torch.trace(sig).item())),
            "hermitian_defect": float(torch.linalg.matrix_norm(sig - sig.conj().T).item()),
            "phase_invariance_defect": phase_defect,
            "quadratic_scaling_defect": scaling_defect,
            "zero_spinor_sigma_norm": zero_sigma_norm,
        },
    }


def sympy_exact_checks() -> dict[str, Any]:
    x1, y1, x2, y2, a, b = sp.symbols("x1 y1 x2 y2 a b", real=True)
    z1 = x1 + sp.I * y1
    z2 = x2 + sp.I * y2
    phi = sp.Matrix([z1, z2])
    rho = phi * phi.conjugate().T
    norm_sq = sp.simplify((phi.conjugate().T * phi)[0])
    sig = sp.simplify(rho - norm_sq * sp.eye(2) / 2)
    trace_free = sp.simplify(sp.trace(sig)) == 0
    hermitian = sp.simplify(sig - sig.conjugate().T) == sp.zeros(2, 2)
    lam = a + sp.I * b
    sig_scaled = sp.simplify((lam * phi) * (lam * phi).conjugate().T - ((lam * phi).conjugate().T * (lam * phi))[0] * sp.eye(2) / 2)
    scaling = sp.simplify(sig_scaled - (a**2 + b**2) * sig) == sp.zeros(2, 2)

    f00, f10, f01, f11 = sp.symbols("f00 f10 f01 f11", real=True)
    dfx_00 = f10 - f00
    dfx_01 = f11 - f01
    dfy_00 = f01 - f00
    dfy_10 = f11 - f10
    d2_expr = sp.simplify((dfy_10 - dfy_00) - (dfx_01 - dfx_00))

    return {
        "sigma_trace_free_exact": bool(trace_free),
        "sigma_hermitian_exact": bool(hermitian),
        "sigma_quadratic_scaling_exact": bool(scaling),
        "d_squared_exact_expression": str(d2_expr),
        "d_squared_exact_zero": d2_expr == 0,
    }


def z3_d_squared_certificate() -> dict[str, Any]:
    f00, f10, f01, f11 = z3.Reals("f00 f10 f01 f11")
    dfx_00 = f10 - f00
    dfx_01 = f11 - f01
    dfy_00 = f01 - f00
    dfy_10 = f11 - f10
    d2_expr = (dfy_10 - dfy_00) - (dfx_01 - dfx_00)
    solver = z3.Solver()
    solver.add(d2_expr != 0)
    status = str(solver.check())
    return {"negation_status": status, "pass": status == "unsat"}


def cvc5_d_squared_certificate() -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_LRA")
    real = slv.getRealSort()
    f00 = slv.mkConst(real, "f00")
    f10 = slv.mkConst(real, "f10")
    f01 = slv.mkConst(real, "f01")
    f11 = slv.mkConst(real, "f11")
    zero = slv.mkReal(0)

    def sub(a: Any, b: Any) -> Any:
        return slv.mkTerm(Kind.SUB, a, b)

    dfx_00 = sub(f10, f00)
    dfx_01 = sub(f11, f01)
    dfy_00 = sub(f01, f00)
    dfy_10 = sub(f11, f10)
    d2_expr = sub(sub(dfy_10, dfy_00), sub(dfx_01, dfx_00))
    slv.assertFormula(slv.mkTerm(Kind.NOT, slv.mkTerm(Kind.EQUAL, d2_expr, zero)))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "pass": res.isUnsat()}


def mv_max_abs(mv: Any) -> float:
    return max(abs(float(v)) for v in mv.value.tolist())


def clifford_quaternion_checks() -> dict[str, Any]:
    _layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    qi = e2 * e3
    qj = e3 * e1
    qk = -(e1 * e2)
    ij_minus_k = mv_max_abs(qi * qj - qk)
    squares = max(mv_max_abs(qi * qi + 1), mv_max_abs(qj * qj + 1), mv_max_abs(qk * qk + 1))
    comm = max(
        mv_max_abs(qi * qj - qj * qi - 2 * qk),
        mv_max_abs(qj * qk - qk * qj - 2 * qi),
        mv_max_abs(qk * qi - qi * qk - 2 * qj),
    )
    return {
        "ij_minus_k_defect": ij_minus_k,
        "unit_imaginary_square_defect": squares,
        "su2_commutator_defect": comm,
        "basis_dimension": 3,
        "basis": ["e23", "e31", "-e12"],
    }


def su2_induced_so3(unitary: torch.Tensor) -> torch.Tensor:
    rot = torch.zeros((3, 3), dtype=RTYPE)
    for j, sj in enumerate(PAULI):
        conj = unitary @ sj @ unitary.conj().T
        for i, si in enumerate(PAULI):
            rot[i, j] = (torch.trace(si @ conj).real) / 2
    return rot


def so3_group_checks() -> dict[str, Any]:
    axis = torch.tensor([0.25, -0.5, 0.83], dtype=RTYPE)
    axis = axis / torch.linalg.vector_norm(axis)
    theta = 0.711
    n_dot_sigma = axis[0].to(CDTYPE) * SX + axis[1].to(CDTYPE) * SY + axis[2].to(CDTYPE) * SZ
    unitary = torch.linalg.matrix_exp(-1j * theta / 2 * n_dot_sigma)
    rot = su2_induced_so3(unitary)
    det = float(torch.det(rot).item())
    orth_defect = float(torch.linalg.matrix_norm(rot.T @ rot - torch.eye(3, dtype=RTYPE)).item())

    r_float = rot.to(torch.float32)
    try:
        aa, bb, cc = o3.matrix_to_angles(r_float)
        r_round = o3.angles_to_matrix(aa, bb, cc)
        e3nn_recon = float(torch.linalg.matrix_norm(r_round - r_float).item())
        e3nn_pass = e3nn_recon < TOL_SO3
        e3nn_error = None
    except Exception as exc:
        e3nn_recon = None
        e3nn_pass = False
        e3nn_error = repr(exc)

    try:
        try:
            so3 = SpecialOrthogonal(n=3, point_type="matrix")
        except TypeError:
            so3 = SpecialOrthogonal(n=3)
        point = gs.array(rot.tolist())
        belongs = so3.belongs(point, atol=TOL_SO3)
        geomstats_belongs = bool(belongs.item()) if hasattr(belongs, "item") else bool(belongs)
        geomstats_error = None
    except Exception as exc:
        geomstats_belongs = False
        geomstats_error = repr(exc)

    return {
        "rotation_matrix": [[float(v) for v in row] for row in rot.tolist()],
        "det": det,
        "orthogonality_defect": orth_defect,
        "e3nn_reconstruction_defect": e3nn_recon,
        "e3nn_pass": e3nn_pass,
        "e3nn_error": e3nn_error,
        "geomstats_belongs_so3": geomstats_belongs,
        "geomstats_error": geomstats_error,
    }


def torus_triangulation() -> tuple[list[int], set[tuple[int, int]], list[tuple[int, int, int]]]:
    vertices = list(range(N * N))
    triangles: list[tuple[int, int, int]] = []
    for x in range(N):
        for y in range(N):
            a = site_index(x, y)
            b = site_index(x + 1, y)
            c = site_index(x, y + 1)
            d = site_index(x + 1, y + 1)
            triangles.append(tuple(sorted((a, b, d))))
            triangles.append(tuple(sorted((a, d, c))))
    triangles = sorted(set(triangles))
    edges: set[tuple[int, int]] = set()
    for tri in triangles:
        a, b, c = tri
        edges.add(tuple(sorted((a, b))))
        edges.add(tuple(sorted((b, c))))
        edges.add(tuple(sorted((a, c))))
    return vertices, edges, triangles


def topology_checks() -> dict[str, Any]:
    vertices, edges, triangles = torus_triangulation()
    explicit_chi = len(vertices) - len(edges) + len(triangles)

    st = gudhi.SimplexTree()
    for tri in triangles:
        st.insert(list(tri))
    gudhi_counts = {0: 0, 1: 0, 2: 0}
    for simplex, _filtration in st.get_skeleton(2):
        dim = len(simplex) - 1
        if dim in gudhi_counts:
            gudhi_counts[dim] += 1
    gudhi_chi = gudhi_counts[0] - gudhi_counts[1] + gudhi_counts[2]

    try:
        sc = SimplicialComplex([list(t) for t in triangles])
    except Exception:
        sc = SimplicialComplex()
        for tri in triangles:
            sc.add_simplex(list(tri))
    shape = tuple(int(v) for v in sc.shape[:3])
    toponetx_chi = shape[0] - shape[1] + shape[2]

    graph = rx.PyGraph()
    graph.add_nodes_from(vertices)
    graph.add_edges_from_no_data(sorted(edges))
    components = rx.connected_components(graph)
    n_components = len(components)
    graph_edge_count = graph.num_edges()
    graph_node_count = graph.num_nodes()

    return {
        "explicit_counts": {"vertices": len(vertices), "edges": len(edges), "faces": len(triangles), "euler_char": explicit_chi},
        "gudhi_counts": {"vertices": gudhi_counts[0], "edges": gudhi_counts[1], "faces": gudhi_counts[2], "euler_char": gudhi_chi},
        "toponetx_shape": {"vertices": shape[0], "edges": shape[1], "faces": shape[2], "euler_char": toponetx_chi},
        "rustworkx_1_skeleton": {
            "nodes": graph_node_count,
            "edges": graph_edge_count,
            "connected_components": n_components,
            "connected": n_components == 1,
        },
    }


def add_check(checks: list[dict[str, Any]], invariant: str, computed: Any, known: Any, match: bool) -> None:
    checks.append({
        "invariant": invariant,
        "computed": computed,
        "known": known,
        "match": bool(match),
    })


def build_known_value_checks(
    numeric: dict[str, Any],
    exact: dict[str, Any],
    z3_cert: dict[str, Any],
    cvc5_cert: dict[str, Any],
    quat: dict[str, Any],
    so3: dict[str, Any],
    topo: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    add_check(checks, "twisted_D_self_adjoint", f"{numeric['dirac']['self_adjoint_defect']:.3e}", "0", numeric["dirac"]["self_adjoint_defect"] < TOL)
    add_check(checks, "twisted_D_real_spectrum", f"max |Im(lambda)| = {numeric['dirac']['max_eigenvalue_imaginary_part']:.3e}", "0", numeric["dirac"]["max_eigenvalue_imaginary_part"] < TOL)
    add_check(checks, "twisted_D_gauge_covariant", f"{numeric['dirac']['gauge_covariance_defect']:.3e}", "0", numeric["dirac"]["gauge_covariance_defect"] < TOL)
    add_check(checks, "curvature_F_equals_dA_gauge_invariant", f"{numeric['curvature']['gauge_invariance_defect']:.3e}", "0", numeric["curvature"]["gauge_invariance_defect"] < TOL)
    add_check(checks, "discrete_d_squared_zero_numeric", f"{numeric['d_squared']['max_abs_d1_d0_f']:.3e}", "0", numeric["d_squared"]["max_abs_d1_d0_f"] < TOL)
    add_check(checks, "discrete_d_squared_zero_sympy_exact", exact["d_squared_exact_expression"], "0", bool(exact["d_squared_exact_zero"]))
    add_check(checks, "discrete_d_squared_zero_z3_negation_unsat", z3_cert["negation_status"], "unsat", bool(z3_cert["pass"]))
    add_check(checks, "discrete_d_squared_zero_cvc5_negation_unsat", cvc5_cert["negation_status"], "unsat", bool(cvc5_cert["pass"]))

    add_check(checks, "sigma_trace_free_numeric", f"{numeric['sigma']['trace_abs']:.3e}", "0", numeric["sigma"]["trace_abs"] < TOL)
    add_check(checks, "sigma_trace_free_sympy_exact", exact["sigma_trace_free_exact"], True, bool(exact["sigma_trace_free_exact"]))
    add_check(checks, "sigma_Hermitian_numeric", f"{numeric['sigma']['hermitian_defect']:.3e}", "0", numeric["sigma"]["hermitian_defect"] < TOL)
    add_check(checks, "sigma_Hermitian_sympy_exact", exact["sigma_hermitian_exact"], True, bool(exact["sigma_hermitian_exact"]))
    add_check(checks, "sigma_exp_if_phi_phase_invariant", f"{numeric['sigma']['phase_invariance_defect']:.3e}", "0", numeric["sigma"]["phase_invariance_defect"] < TOL)
    add_check(checks, "sigma_lambda_phi_quadratic_scaling_numeric", f"{numeric['sigma']['quadratic_scaling_defect']:.3e}", "0", numeric["sigma"]["quadratic_scaling_defect"] < TOL)
    add_check(checks, "sigma_lambda_phi_quadratic_scaling_sympy_exact", exact["sigma_quadratic_scaling_exact"], True, bool(exact["sigma_quadratic_scaling_exact"]))
    add_check(checks, "reducible_phi_zero_implies_sigma_zero", f"{numeric['sigma']['zero_spinor_sigma_norm']:.3e}", "0", numeric["sigma"]["zero_spinor_sigma_norm"] < TOL)

    add_check(checks, "quaternion_i_j_equals_k_in_Cl3_even", f"{quat['ij_minus_k_defect']:.3e}", "0", quat["ij_minus_k_defect"] < TOL)
    add_check(checks, "Cl3_even_basis_squares_to_minus_one", f"{quat['unit_imaginary_square_defect']:.3e}", "0", quat["unit_imaginary_square_defect"] < TOL)
    add_check(checks, "Cl3_even_su2_commutator_relations", f"{quat['su2_commutator_defect']:.3e}", "0", quat["su2_commutator_defect"] < TOL)

    add_check(checks, "SU2_adjoint_rotation_det_one", f"{so3['det']:.12f}", "1", abs(so3["det"] - 1.0) < TOL_SO3)
    add_check(checks, "SU2_adjoint_rotation_orthogonal", f"{so3['orthogonality_defect']:.3e}", "0", so3["orthogonality_defect"] < TOL_SO3)
    add_check(checks, "e3nn_certifies_SO3_roundtrip", f"{so3['e3nn_reconstruction_defect']}", "0", bool(so3["e3nn_pass"]))
    add_check(checks, "geomstats_certifies_SO3_membership", so3["geomstats_belongs_so3"], True, bool(so3["geomstats_belongs_so3"]))

    add_check(checks, "lattice_2_torus_Euler_characteristic_explicit", topo["explicit_counts"]["euler_char"], 0, topo["explicit_counts"]["euler_char"] == 0)
    add_check(checks, "lattice_2_torus_Euler_characteristic_gudhi", topo["gudhi_counts"]["euler_char"], 0, topo["gudhi_counts"]["euler_char"] == 0)
    add_check(checks, "lattice_2_torus_Euler_characteristic_toponetx", topo["toponetx_shape"]["euler_char"], 0, topo["toponetx_shape"]["euler_char"] == 0)
    add_check(checks, "rustworkx_torus_1_skeleton_connected", topo["rustworkx_1_skeleton"]["connected"], True, bool(topo["rustworkx_1_skeleton"]["connected"]))
    return checks


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    runtime_errors: list[str] = []
    data: dict[str, Any] = {}
    try:
        numeric = seiberg_witten_numeric()
        exact = sympy_exact_checks()
        z3_cert = z3_d_squared_certificate()
        cvc5_cert = cvc5_d_squared_certificate()
        quat = clifford_quaternion_checks()
        so3 = so3_group_checks()
        topo = topology_checks()
        checks = build_known_value_checks(numeric, exact, z3_cert, cvc5_cert, quat, so3, topo)
        data = {
            "numeric": numeric,
            "sympy_exact": exact,
            "z3_certificate": z3_cert,
            "cvc5_certificate": cvc5_cert,
            "clifford_quaternion": quat,
            "so3_group_checks": so3,
            "topology": topo,
        }
    except Exception as exc:
        runtime_errors.append(f"runtime blocker: {type(exc).__name__}: {exc}")
        checks = []

    known_values_all_match = bool(checks) and all(row["match"] for row in checks)
    blockers = [f"KNOWN-VALUE MISMATCH: {row['invariant']} computed={row['computed']} known={row['known']}" for row in checks if not row["match"]]
    blockers.extend(runtime_errors)
    all_pass = known_values_all_match and not blockers

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "complex128/float64 lattice cochains, U(1) links, twisted Dirac matrix, spectrum, curvature, and moment-map computations are all torch-native.",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact symbolic sigma trace/Hermitian/quadratic-scaling identities and exact d^2 cancellation.",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT counterexample search for d^2 != 0 is UNSAT over real cochain variables.",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SMT counterexample search for d^2 != 0 is UNSAT over real cochain variables.",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "Cl(3) even bivectors compute i*j=k, square to -1, and satisfy su(2) commutators.",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "SpecialOrthogonal(3) membership certifies the SU(2) adjoint rotation as an SO(3) group element.",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "SimplexTree independently counts the triangulated periodic lattice and verifies Euler characteristic 0.",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "SimplicialComplex shape independently verifies the torus cell counts and Euler characteristic 0.",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "1-skeleton graph connectivity and edge/node counts guard the torus topology witness.",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "SO(3) angle round-trip certifies the SU(2) adjoint rotation in the l=1 representation.",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "tier": "2_gstructure_known_math",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "gstructure_probe",
        "g_structure": "seiberg_witten_spin_c_u1_discrete_lattice",
        "purpose": "Independent known-math diagnostic of a discrete U(1)-twisted Seiberg-Witten structure on a 2-torus lattice.",
        "scientific_question": "Do the discrete Spin^c/U(1) Seiberg-Witten carrier invariants match their known mathematical values without copying external model numbers?",
        "claim_ceiling": "diagnostic_only / lego phase / unadmitted: no manifold layer, stacking, Axis0, flux, bridge, basin, or physics claim.",
        "finite_map": "(f, A, phi) on a finite periodic 2-torus lattice -> (d0 f, F=dA, twisted Dirac D_A, sigma(phi), topology and group-structure invariants)",
        "domain": "finite N x N periodic lattice vertices, U(1) link potential A, real gauge phase f, C^2 spinor field phi",
        "codomain_or_output": "curvature 2-cochain F, gauge-transformed connection A+df, Hermitian Dirac matrix D_A, trace-free Hermitian sigma(phi), Cl(3)-even quaternion/su(2) witnesses, torus topology counts",
        "carrier_realization": "torch.complex128 spinors/operators and torch.float64 cochains; no NumPy claim-bearing substrate",
        "negative_or_control_condition": "any known invariant mismatch blocks; the receipt remains diagnostic_only and downstream consumers stay blocked",
        "downstream_blocks": ["manifold_layers", "layer_completion", "G_structure_admission", "stacking", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "layer_completion", "G_structure_admission", "stacking", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "known_value_checks": checks,
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "tools_all_pass": all_pass,
            "n_known_value_checks": len(checks),
            "classification": "diagnostic_only",
            "result_path": str(RESULT_PATH),
        },
        "computed_evidence": data,
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "required_tools": list(tool_manifest),
        "actual_tools_used": list(tool_manifest),
        "required_artifacts": ["json_result_receipt"],
        "artifacts_emitted": ["json_result_receipt"],
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "every known_value_check match boolean is true and no runtime blocker is present",
        "fail_rule": "any mismatched invariant, missing required tool, or runtime/tool API failure blocks the diagnostic",
        "eligible_consumers": ["diagnostic_only cross-model comparison against independent Seiberg-Witten probes"],
    }
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "wrote": str(RESULT_PATH),
        "all_pass": all_pass,
        "known_values_all_match": known_values_all_match,
        "n_known_value_checks": len(checks),
        "blockers": blockers,
        "failed_checks": [row for row in checks if not row["match"]],
    }, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
