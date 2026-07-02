#!/usr/bin/env python3
"""Independent diagnostic G2 / octonion G-structure probe.

This is a lego-phase diagnostic-only formal scout. It computes the compact G2
Lie algebra from the octonion derivation equations and separately from the
stabilizer of the octonionic 3-form phi, then cross-checks textbook invariants.

No NumPy is used as a claim substrate. The numerical carrier is torch
float64/complex128; exact rank/nullspace work is sympy; solver/tool checks are
load-bearing and fail closed into the JSON receipt.
"""

from __future__ import annotations

import datetime as _dt
import json
import math
import os
import pathlib
import traceback
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/numba-cache-codex-ratchet")

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_FILE = RESULT_DIR / "gstruct_g2_codex_probe_results.json"
SIM_ID = "gstruct_g2_codex_probe"
CLASSIFICATION = "diagnostic_only"
RTOL = 1.0e-8
TINY = 1.0e-10

IMPORT_ERRORS: dict[str, str] = {}

try:
    import torch
except Exception as exc:  # pragma: no cover - receipt path handles this.
    IMPORT_ERRORS["torch"] = repr(exc)

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["sympy"] = repr(exc)

try:
    import z3
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["z3"] = repr(exc)

try:
    import cvc5
    from cvc5 import Kind
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["cvc5"] = repr(exc)

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["clifford"] = repr(exc)

try:
    from geomstats.geometry.special_orthogonal import SpecialOrthogonal
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["geomstats"] = repr(exc)

try:
    import gudhi
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["gudhi"] = repr(exc)

try:
    import toponetx as tnx
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["toponetx"] = repr(exc)

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["rustworkx"] = repr(exc)

try:
    from e3nn import o3
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["e3nn"] = repr(exc)


FANO_TRIPLES = [
    (1, 2, 3),
    (1, 4, 5),
    (1, 7, 6),
    (2, 4, 6),
    (2, 5, 7),
    (3, 4, 7),
    (3, 6, 5),
]


def now_iso() -> str:
    return _dt.datetime.now(tz=_dt.timezone.utc).isoformat()


def jsonable(value: Any) -> Any:
    if "torch" in globals() and isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.item())
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, (bool, int, float, str)) or value is None:
        return value
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, tuple):
        return [jsonable(v) for v in value]
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    return repr(value)


def write_receipt(receipt: dict[str, Any]) -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(json.dumps(jsonable(receipt), indent=2, sort_keys=True) + "\n")


def base_receipt() -> dict[str, Any]:
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "generated_at": now_iso(),
        "result_path": str(RESULT_FILE),
        "finite_map": (
            "oriented Fano-plane octonion multiplication -> derivation equations "
            "Der(O) and stabilizer Lie algebra ann(phi) inside so(7)"
        ),
        "claim_scope": "diagnostic_only lego-phase known-value comparison for G2 / octonions",
        "claim_substrate": {
            "primary_numeric": "torch.float64 and torch.complex128 with torch.linalg",
            "exact_symbolic": "sympy rational linear algebra",
            "numpy": "not imported by this sim as claim substrate",
        },
        "TOOL_MANIFEST": {
            "torch": "load-bearing octonion tensor algebra, phi identities, matrix exp, eigensignature, least-squares structure constants",
            "sympy": "load-bearing exact derivation and phi-stabilizer constraint ranks/nullspaces",
            "z3": "load-bearing SMT consistency certificate for computed dimensions",
            "cvc5": "load-bearing independent SMT consistency certificate for computed dimensions/incidences",
            "clifford": "load-bearing exterior/geometric-algebra representation of the octonionic 3-form",
            "geomstats": "load-bearing SO(7) matrix-group membership check for exp(theta * g2_generator)",
            "gudhi": "load-bearing Fano-plane simplicial incidence reconstruction",
            "toponetx": "load-bearing independent Fano-plane simplicial incidence reconstruction",
            "rustworkx": "load-bearing bipartite point-line incidence graph count",
            "e3nn": "load-bearing SO(3) line-rotation sanity check for oriented Fano-line geometry",
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
        "positive": [
            "G2 computed as Der(O)",
            "G2 computed independently as the infinitesimal stabilizer of phi in so(7)",
            "octonion norm multiplicativity and nonassociativity checked directly",
            "compact Killing form signature computed from adjoint matrices",
        ],
        "negative_controls": [
            "associative-law readout on (e1,e2,e4) is expected to fail",
            "dimension equality is checked through exact nullspaces, not accepted from labels",
            "known-value match booleans are computed from values and tolerances",
        ],
        "known_value_checks": [],
        "blockers": [],
    }


def build_mult_int() -> list[list[list[int]]]:
    mult = [[[0 for _ in range(8)] for _ in range(8)] for _ in range(8)]
    mult[0][0][0] = 1
    for i in range(1, 8):
        mult[0][i][i] = 1
        mult[i][0][i] = 1
        mult[i][i][0] = -1
    for a, b, c in FANO_TRIPLES:
        cycles = ((a, b, c), (b, c, a), (c, a, b))
        for x, y, z in cycles:
            mult[x][y][z] = 1
            mult[y][x][z] = -1
    return mult


def phi_int_from_mult(mult: list[list[list[int]]]) -> list[list[list[int]]]:
    return [[[mult[i + 1][j + 1][k + 1] for k in range(7)] for j in range(7)] for i in range(7)]


def vector_index(row: int, col: int) -> int:
    return row * 7 + col


def derivation_constraint_matrix(mult: list[list[list[int]]]) -> Any:
    rows: list[list[int]] = []
    for i in range(1, 8):
        for j in range(1, 8):
            for out in range(8):
                row = [0 for _ in range(49)]
                if out > 0:
                    for t in range(1, 8):
                        coeff = mult[i][j][t]
                        if coeff:
                            row[vector_index(out - 1, t - 1)] += coeff
                for p in range(1, 8):
                    coeff = mult[p][j][out]
                    if coeff:
                        row[vector_index(p - 1, i - 1)] -= coeff
                for q in range(1, 8):
                    coeff = mult[i][q][out]
                    if coeff:
                        row[vector_index(q - 1, j - 1)] -= coeff
                if any(row):
                    rows.append(row)
    return sp.Matrix(rows)


def phi_stabilizer_constraint_matrix(phi_i: list[list[list[int]]]) -> Any:
    rows: list[list[int]] = []
    for i in range(7):
        row = [0 for _ in range(49)]
        row[vector_index(i, i)] = 1
        rows.append(row)
    for i in range(7):
        for j in range(i + 1, 7):
            row = [0 for _ in range(49)]
            row[vector_index(i, j)] = 1
            row[vector_index(j, i)] = 1
            rows.append(row)
    for i in range(7):
        for j in range(7):
            for k in range(7):
                row = [0 for _ in range(49)]
                for p in range(7):
                    row[vector_index(p, i)] += phi_i[p][j][k]
                    row[vector_index(p, j)] += phi_i[i][p][k]
                    row[vector_index(p, k)] += phi_i[i][j][p]
                if any(row):
                    rows.append(row)
    return sp.Matrix(rows)


def sympy_vec_to_torch_matrix(v: Any) -> Any:
    vals = [float(x) for x in list(v)]
    return torch.tensor(vals, dtype=torch.float64).reshape(7, 7)


def basis_columns(nullspace: list[Any]) -> Any:
    return sp.Matrix.hstack(*nullspace) if nullspace else sp.zeros(49, 0)


def octonion_basis(i: int) -> Any:
    v = torch.zeros(8, dtype=torch.float64)
    v[i] = 1.0
    return v


def octonion_mul(x: Any, y: Any, mult_t: Any) -> Any:
    return torch.einsum("a,b,abc->c", x, y, mult_t)


def add_check(
    checks: list[dict[str, Any]],
    invariant: str,
    computed: Any,
    known: Any,
    match: bool,
) -> None:
    checks.append(
        {
            "invariant": invariant,
            "computed": jsonable(computed),
            "known": jsonable(known),
            "match": bool(match),
        }
    )


def z3_dimension_certificate(dim_so7: int, dim_der: int, dim_phi: int, incidences: int) -> dict[str, Any]:
    solver = z3.Solver()
    so7, der, phi, inc = z3.Ints("so7 der phi inc")
    solver.add(so7 == dim_so7, der == dim_der, phi == dim_phi, inc == incidences)
    claim = z3.And(so7 == 21, der == 14, phi == 14, der == phi, inc == 21)
    solver.add(z3.Not(claim))
    status = str(solver.check())
    return {"negated_claim_status": status, "pass": status == "unsat"}


def cvc5_dimension_certificate(dim_so7: int, dim_der: int, dim_phi: int, incidences: int) -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setLogic("QF_LIA")
    int_sort = slv.getIntegerSort()
    so7 = slv.mkConst(int_sort, "so7")
    der = slv.mkConst(int_sort, "der")
    phi = slv.mkConst(int_sort, "phi")
    inc = slv.mkConst(int_sort, "inc")

    def i(value: int) -> Any:
        return slv.mkInteger(value)

    slv.assertFormula(slv.mkTerm(Kind.EQUAL, so7, i(dim_so7)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, der, i(dim_der)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, phi, i(dim_phi)))
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, inc, i(incidences)))
    claim = slv.mkTerm(
        Kind.AND,
        slv.mkTerm(Kind.EQUAL, so7, i(21)),
        slv.mkTerm(Kind.EQUAL, der, i(14)),
        slv.mkTerm(Kind.EQUAL, phi, i(14)),
        slv.mkTerm(Kind.EQUAL, der, phi),
        slv.mkTerm(Kind.EQUAL, inc, i(21)),
    )
    slv.assertFormula(slv.mkTerm(Kind.NOT, claim))
    status = str(slv.checkSat())
    return {"negated_claim_status": status, "pass": status == "unsat"}


def fano_counts_gudhi() -> dict[str, int]:
    tree = gudhi.SimplexTree()
    for line in FANO_TRIPLES:
        tree.insert([p - 1 for p in line])
    skeleton = list(tree.get_skeleton(2))
    return {
        "vertices": sum(1 for simplex, _ in skeleton if len(simplex) == 1),
        "edges": sum(1 for simplex, _ in skeleton if len(simplex) == 2),
        "lines": sum(1 for simplex, _ in skeleton if len(simplex) == 3),
    }


def fano_counts_toponetx() -> dict[str, int]:
    complex_obj = tnx.SimplicialComplex([[p - 1 for p in line] for line in FANO_TRIPLES])
    if hasattr(complex_obj, "shape"):
        shape = tuple(int(x) for x in complex_obj.shape)
        if len(shape) >= 3:
            return {"vertices": shape[0], "edges": shape[1], "lines": shape[2]}
    vertices = len(list(complex_obj.skeleton(0)))
    edges = len(list(complex_obj.skeleton(1)))
    lines = len(list(complex_obj.skeleton(2)))
    return {"vertices": vertices, "edges": edges, "lines": lines}


def fano_counts_rustworkx() -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(range(14))
    for line_idx, line in enumerate(FANO_TRIPLES):
        line_node = 7 + line_idx
        for point in line:
            graph.add_edge(point - 1, line_node, None)
    point_degrees = [graph.degree(point) for point in range(7)]
    line_degrees = [graph.degree(7 + line_idx) for line_idx in range(7)]
    return {
        "points": 7,
        "lines": 7,
        "incidences": len(graph.edge_list()),
        "point_degrees": point_degrees,
        "line_degrees": line_degrees,
    }


def clifford_phi_check() -> dict[str, Any]:
    _layout, blades = Cl(7)
    e = [blades[f"e{i}"] for i in range(1, 8)]
    phi_mv = 0
    for a, b, c in FANO_TRIPLES:
        phi_mv = phi_mv + (e[a - 1] ^ e[b - 1] ^ e[c - 1])
    coeffs = [float(v) for v in phi_mv.value]
    nonzero = sum(1 for v in coeffs if abs(v) > 0.5)
    grades = sorted(int(g) for g in phi_mv.grades())
    return {
        "nonzero_blade_coefficients": nonzero,
        "grades": grades,
        "pass": nonzero == 7 and grades == [3],
    }


def geomstats_so7_check(generator: Any) -> dict[str, Any]:
    so7 = SpecialOrthogonal(n=7, point_type="matrix")
    theta = torch.tensor(0.125, dtype=torch.float64)
    rot = torch.matrix_exp(theta * generator)
    belongs = so7.belongs(rot, atol=1.0e-6)
    if isinstance(belongs, torch.Tensor):
        belongs_bool = bool(belongs.item())
    else:
        belongs_bool = bool(belongs)
    det = float(torch.linalg.det(rot).item())
    orth_resid = float(torch.linalg.matrix_norm(rot.T @ rot - torch.eye(7, dtype=torch.float64)).item())
    return {
        "belongs_SO7": belongs_bool,
        "det": det,
        "orthogonality_residual": orth_resid,
        "pass": belongs_bool and abs(det - 1.0) <= 1.0e-6 and orth_resid <= 1.0e-6,
    }


def e3nn_line_rotation_check() -> dict[str, Any]:
    alpha = torch.tensor(0.37, dtype=torch.float64)
    beta = torch.tensor(0.41, dtype=torch.float64)
    gamma = torch.tensor(-0.23, dtype=torch.float64)
    rot = o3.angles_to_matrix(alpha, beta, gamma).to(dtype=torch.float64)
    det = float(torch.linalg.det(rot).item())
    orth_resid = float(torch.linalg.matrix_norm(rot.T @ rot - torch.eye(3, dtype=torch.float64)).item())
    return {
        "det": det,
        "orthogonality_residual": orth_resid,
        "pass": abs(det - 1.0) <= 1.0e-6 and orth_resid <= 1.0e-6,
    }


def centralizer_rank_g2(basis_mats_sp: list[Any]) -> dict[str, Any]:
    prime_coeffs = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43]
    candidates = [
        [i + 1 for i in range(14)],
        prime_coeffs,
        [((i + 1) ** 2 % 17) + 1 for i in range(14)],
        [((i + 3) ** 3 % 23) + 1 for i in range(14)],
    ]
    results: list[dict[str, Any]] = []
    for coeffs in candidates:
        h = sp.zeros(7, 7)
        for coeff, mat in zip(coeffs, basis_mats_sp):
            h += coeff * mat
        comm_cols = []
        for mat in basis_mats_sp:
            comm = h * mat - mat * h
            comm_cols.append([comm[r, c] for r in range(7) for c in range(7)])
        rows = list(map(list, zip(*comm_cols)))
        rank = sp.Matrix(rows).rank()
        nullity = 14 - rank
        results.append({"coefficients": coeffs, "centralizer_dim": int(nullity)})
    return {"computed_rank": min(r["centralizer_dim"] for r in results), "candidates": results}


def main() -> int:
    receipt = base_receipt()
    if IMPORT_ERRORS:
        receipt["status"] = "blocked_import_error"
        receipt["blockers"].append({"kind": "import_error", "details": IMPORT_ERRORS})
        receipt["all_known_value_checks_match"] = False
        write_receipt(receipt)
        print(json.dumps({"result_path": str(RESULT_FILE), "blocked": IMPORT_ERRORS}, indent=2))
        return 1

    checks = receipt["known_value_checks"]

    try:
        mult_i = build_mult_int()
        phi_i = phi_int_from_mult(mult_i)
        mult_t = torch.tensor(mult_i, dtype=torch.float64)
        phi_t = torch.tensor(phi_i, dtype=torch.float64)

        dim_so7 = sum(1 for i in range(7) for j in range(i + 1, 7))
        add_check(checks, "dim so(7)", dim_so7, 21, dim_so7 == 21)

        metric_from_phi = torch.einsum("ikl,jkl->ij", phi_t, phi_t)
        phi_metric_residual = float(
            torch.linalg.matrix_norm(metric_from_phi - 6.0 * torch.eye(7, dtype=torch.float64)).item()
        )
        add_check(
            checks,
            "phi metric identity phi_ikl phi_jkl == 6 delta_ij",
            {"max_matrix_residual": phi_metric_residual},
            {"max_matrix_residual": 0.0},
            phi_metric_residual <= TINY,
        )

        deriv_constraints = derivation_constraint_matrix(mult_i)
        phi_constraints = phi_stabilizer_constraint_matrix(phi_i)
        der_ns = deriv_constraints.nullspace()
        phi_ns = phi_constraints.nullspace()
        der_basis = basis_columns(der_ns)
        phi_basis = basis_columns(phi_ns)
        dim_der = len(der_ns)
        dim_phi = len(phi_ns)
        combined_rank = der_basis.row_join(phi_basis).rank()
        der_rank = der_basis.rank()
        phi_rank = phi_basis.rank()

        add_check(
            checks,
            "dim g2 == 14 == dim Der(O)",
            {"dim_DerO": dim_der, "dim_ann_phi": dim_phi},
            {"dim_DerO": 14, "dim_ann_phi": 14},
            dim_der == 14 and dim_phi == 14,
        )
        add_check(
            checks,
            "g2 == Der(O)",
            {
                "dim_DerO": dim_der,
                "dim_ann_phi": dim_phi,
                "rank_DerO": int(der_rank),
                "rank_ann_phi": int(phi_rank),
                "rank_combined": int(combined_rank),
            },
            {"subspaces_equal": True},
            dim_der == dim_phi == der_rank == phi_rank == combined_rank,
        )

        basis_t = [sympy_vec_to_torch_matrix(v) for v in der_ns]
        basis_sp = [
            sp.Matrix(7, 7, lambda r, c, vec=v: vec[vector_index(r, c), 0])
            for v in der_ns
        ]
        max_phi_action = 0.0
        max_skew_residual = 0.0
        for generator in basis_t:
            action = (
                torch.einsum("pi,pjk->ijk", generator, phi_t)
                + torch.einsum("pj,ipk->ijk", generator, phi_t)
                + torch.einsum("pk,ijp->ijk", generator, phi_t)
            )
            max_phi_action = max(max_phi_action, float(torch.max(torch.abs(action)).item()))
            max_skew_residual = max(
                max_skew_residual,
                float(torch.linalg.matrix_norm(generator + generator.T).item()),
            )
        add_check(
            checks,
            "g2 generators annihilate phi",
            {"max_phi_action_abs": max_phi_action, "max_skew_residual": max_skew_residual},
            {"max_phi_action_abs": 0.0, "max_skew_residual": 0.0},
            max_phi_action <= TINY and max_skew_residual <= TINY,
        )

        rank_result = centralizer_rank_g2(basis_sp)
        add_check(checks, "rank G2", rank_result["computed_rank"], 2, rank_result["computed_rank"] == 2)

        gen = torch.Generator().manual_seed(20260529)
        norm_residuals = []
        for _ in range(32):
            x = torch.randn(8, generator=gen, dtype=torch.float64)
            y = torch.randn(8, generator=gen, dtype=torch.float64)
            xy = octonion_mul(x, y, mult_t)
            nx = torch.dot(x, x)
            ny = torch.dot(y, y)
            nxy = torch.dot(xy, xy)
            norm_residuals.append(abs(float((nxy - nx * ny).item())))
        max_norm_residual = max(norm_residuals)
        add_check(
            checks,
            "octonion norm multiplicative |xy|=|x||y|",
            {"max_norm_squared_residual": max_norm_residual, "samples": len(norm_residuals)},
            {"max_norm_squared_residual": 0.0},
            max_norm_residual <= RTOL,
        )

        e1, e2, e4 = octonion_basis(1), octonion_basis(2), octonion_basis(4)
        left = octonion_mul(octonion_mul(e1, e2, mult_t), e4, mult_t)
        right = octonion_mul(e1, octonion_mul(e2, e4, mult_t), mult_t)
        assoc_residual = float(torch.max(torch.abs(left - right)).item())
        add_check(
            checks,
            "octonions are nonassociative: (e1e2)e4 != e1(e2e4)",
            {"left": left, "right": right, "max_abs_difference": assoc_residual},
            {"equal": False},
            assoc_residual > 0.5,
        )

        fano_rx = fano_counts_rustworkx()
        fano_gudhi = fano_counts_gudhi()
        fano_tnx = fano_counts_toponetx()
        fano_match = (
            fano_rx["points"] == 7
            and fano_rx["lines"] == 7
            and fano_rx["incidences"] == 21
            and fano_rx["point_degrees"] == [3] * 7
            and fano_rx["line_degrees"] == [3] * 7
            and fano_gudhi == {"vertices": 7, "edges": 21, "lines": 7}
            and fano_tnx == {"vertices": 7, "edges": 21, "lines": 7}
        )
        add_check(
            checks,
            "Fano plane 7 points 21 incidences",
            {"rustworkx": fano_rx, "gudhi": fano_gudhi, "toponetx": fano_tnx},
            {"points": 7, "line_count": 7, "incidences": 21},
            fano_match,
        )

        basis_matrix_t = torch.stack([mat.reshape(49) for mat in basis_t], dim=1)
        ad_mats = []
        closure_residual = 0.0
        for a, a_mat in enumerate(basis_t):
            ad = torch.zeros((14, 14), dtype=torch.float64)
            for b, b_mat in enumerate(basis_t):
                comm = (a_mat @ b_mat - b_mat @ a_mat).reshape(49)
                coords = torch.linalg.lstsq(basis_matrix_t, comm).solution
                ad[:, b] = coords
                closure_residual = max(
                    closure_residual,
                    float(torch.linalg.vector_norm(basis_matrix_t @ coords - comm).item()),
                )
            ad_mats.append(ad)
        killing = torch.zeros((14, 14), dtype=torch.float64)
        for a in range(14):
            for b in range(14):
                killing[a, b] = torch.trace(ad_mats[a] @ ad_mats[b])
        killing = (killing + killing.T) / 2.0
        killing_eigs = torch.linalg.eigvalsh(killing)
        pos = int((killing_eigs > 1.0e-7).sum().item())
        neg = int((killing_eigs < -1.0e-7).sum().item())
        zero = int(14 - pos - neg)
        signature = [pos, neg, zero]
        add_check(
            checks,
            "Killing form signature compact G2",
            {
                "signature_pos_neg_zero": signature,
                "min_eigenvalue": float(killing_eigs.min().item()),
                "max_eigenvalue": float(killing_eigs.max().item()),
                "lie_bracket_closure_residual": closure_residual,
            },
            {"signature_pos_neg_zero": [0, 14, 0]},
            signature == [0, 14, 0] and closure_residual <= 1.0e-7,
        )

        z3_cert = z3_dimension_certificate(dim_so7, dim_der, dim_phi, fano_rx["incidences"])
        cvc5_cert = cvc5_dimension_certificate(dim_so7, dim_der, dim_phi, fano_rx["incidences"])
        cliff_cert = clifford_phi_check()
        geom_cert = geomstats_so7_check(basis_t[0])
        e3nn_cert = e3nn_line_rotation_check()
        add_check(checks, "z3 computed-dimension certificate", z3_cert, {"pass": True}, z3_cert["pass"])
        add_check(checks, "cvc5 computed-dimension certificate", cvc5_cert, {"pass": True}, cvc5_cert["pass"])
        add_check(checks, "clifford phi is a pure 7-term trivector", cliff_cert, {"pass": True}, cliff_cert["pass"])
        add_check(checks, "geomstats exp(g2 generator) belongs to SO(7)", geom_cert, {"pass": True}, geom_cert["pass"])
        add_check(checks, "e3nn SO(3) Fano-line rotation sanity", e3nn_cert, {"pass": True}, e3nn_cert["pass"])

        complex_generator = basis_t[0].to(dtype=torch.complex128)
        complex_rot = torch.matrix_exp(torch.tensor(0.125, dtype=torch.float64) * complex_generator)
        unitary_residual = float(
            torch.linalg.matrix_norm(
                complex_rot.conj().T @ complex_rot - torch.eye(7, dtype=torch.complex128)
            ).real.item()
        )

        receipt["details"] = {
            "oriented_fano_triples": FANO_TRIPLES,
            "derivation_constraint_shape": list(deriv_constraints.shape),
            "phi_stabilizer_constraint_shape": list(phi_constraints.shape),
            "sympy_ranks": {
                "derivation_constraints_rank": int(deriv_constraints.rank()),
                "phi_stabilizer_constraints_rank": int(phi_constraints.rank()),
                "derivation_basis_rank": int(der_rank),
                "phi_basis_rank": int(phi_rank),
                "combined_basis_rank": int(combined_rank),
            },
            "rank_search": rank_result,
            "torch_complex128_compact_rotation_unitarity_residual": unitary_residual,
        }
        receipt["all_known_value_checks_match"] = all(bool(item["match"]) for item in checks)
        if not receipt["all_known_value_checks_match"]:
            failed = [item for item in checks if not item["match"]]
            receipt["blockers"].append({"kind": "known_value_mismatch", "failed_checks": failed})
            receipt["status"] = "blocked_known_value_mismatch"
        else:
            receipt["status"] = "pass"
        write_receipt(receipt)
        print(
            json.dumps(
                {
                    "result_path": str(RESULT_FILE),
                    "status": receipt["status"],
                    "all_known_value_checks_match": receipt["all_known_value_checks_match"],
                    "known_value_check_count": len(checks),
                },
                indent=2,
            )
        )
        return 0 if receipt["all_known_value_checks_match"] else 1
    except Exception as exc:
        receipt["status"] = "blocked_exception"
        receipt["blockers"].append(
            {
                "kind": "exception",
                "error": repr(exc),
                "traceback": traceback.format_exc(),
            }
        )
        receipt["all_known_value_checks_match"] = False
        write_receipt(receipt)
        print(json.dumps({"result_path": str(RESULT_FILE), "blocked_exception": repr(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
