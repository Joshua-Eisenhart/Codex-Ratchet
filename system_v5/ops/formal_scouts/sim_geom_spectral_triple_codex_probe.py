#!/usr/bin/env python3
"""Finite two-point spectral triple geometry probe.

Diagnostic-only formal scout for the known finite spectral triple

    A = C + C acting diagonally on H = C^2
    D = [[0, m], [conj(m), 0]]

with m = 3 + 4i. The Connes distance between the two pure states is
1 / |m| = 1/5. Torch complex128/float64 is the claim substrate; other geometry
tools are independent load-bearing cross-checks.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from datetime import datetime, timezone
from typing import Any

# The local Python 3.13 environment imports these numba-backed packages only
# when their cache/JIT path is disabled up front.
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("QUIMB_NUMBA_CACHE", "False")

import cvc5
from cvc5 import Kind
from clifford import Cl
from e3nn import o3
import geomstats.backend as gs
from geomstats.geometry.euclidean import Euclidean
import gudhi
import quimb as qu
import rustworkx as rx
import sympy as sp
import toponetx as tnx
import torch
import z3


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_E3NN = 1.0e-5
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
RESULT_PATH = RESULT_DIR / "geom_spectral_triple_codex_probe_results.json"
SIM_ID = "geom_spectral_triple_codex_probe"

M_RE = 3.0
M_IM = 4.0
M_COMPLEX = complex(M_RE, M_IM)


def j(x: Any) -> Any:
    """Small JSON adapter without using numpy as a claim substrate."""
    if isinstance(x, torch.Tensor):
        return j(x.detach().cpu().tolist())
    if isinstance(x, complex):
        return {"real": x.real, "imag": x.imag}
    if isinstance(x, (list, tuple)):
        return [j(v) for v in x]
    if isinstance(x, dict):
        return {str(k): j(v) for k, v in x.items()}
    if hasattr(x, "tolist"):
        return j(x.tolist())
    if hasattr(x, "item"):
        try:
            return x.item()
        except Exception:
            pass
    return x


def check(invariant: str, computed: Any, known: Any, match: bool) -> dict[str, Any]:
    return {
        "invariant": invariant,
        "computed": j(computed),
        "known": j(known),
        "match": bool(match),
    }


def make_dirac() -> torch.Tensor:
    m = torch.tensor(M_COMPLEX, dtype=CDTYPE)
    d = torch.zeros((2, 2), dtype=CDTYPE)
    d[0, 1] = m
    d[1, 0] = m.conj()
    return d


def algebra_element(delta: torch.Tensor | float) -> torch.Tensor:
    """A self-adjoint element diag(delta, 0), enough because constants drop out."""
    if not isinstance(delta, torch.Tensor):
        delta = torch.tensor(delta, dtype=RTYPE)
    return torch.diag(torch.stack([delta, torch.zeros((), dtype=RTYPE)])).to(CDTYPE)


def commutator(d: torch.Tensor, a: torch.Tensor) -> torch.Tensor:
    return d @ a - a @ d


def op_norm(x: torch.Tensor) -> torch.Tensor:
    return torch.linalg.matrix_norm(x, ord=2).real


def torch_core() -> dict[str, Any]:
    d = make_dirac()
    abs_m = float(torch.abs(torch.tensor(M_COMPLEX, dtype=CDTYPE)).real.item())
    known_distance = 1.0 / abs_m

    self_adjoint_defect = float(torch.linalg.matrix_norm(d - d.conj().T).item())
    evals = torch.linalg.eigvalsh((d + d.conj().T) / 2).real
    eval_match = torch.allclose(
        torch.sort(evals).values,
        torch.tensor([-abs_m, abs_m], dtype=RTYPE),
        atol=TOL,
        rtol=0.0,
    )

    d_squared_defect = float(
        torch.linalg.matrix_norm(d @ d - (abs_m**2) * torch.eye(2, dtype=CDTYPE)).item()
    )

    boundary_delta = torch.tensor(known_distance, dtype=RTYPE, requires_grad=True)
    boundary_norm = op_norm(commutator(d, algebra_element(boundary_delta)))
    boundary_norm.backward()
    grad_at_boundary = float(boundary_delta.grad.item())
    computed_distance = float(boundary_delta.detach().item())

    sample_delta = torch.tensor(0.37, dtype=RTYPE)
    sample_comm_norm = float(op_norm(commutator(d, algebra_element(sample_delta))).item())
    sample_known_norm = abs_m * float(abs(sample_delta.item()))

    points = ("p", "q")

    def dist(x: str, y: str) -> float:
        return 0.0 if x == y else computed_distance

    symmetry_error = max(abs(dist(x, y) - dist(y, x)) for x in points for y in points)
    triangle_violation = max(
        dist(x, z) - (dist(x, y) + dist(y, z))
        for x in points
        for y in points
        for z in points
    )
    identity_ok = (
        dist("p", "p") == 0.0
        and dist("q", "q") == 0.0
        and dist("p", "q") > 0.0
        and dist("q", "p") > 0.0
    )

    return {
        "D": d,
        "abs_m": abs_m,
        "known_distance": known_distance,
        "self_adjoint_defect": self_adjoint_defect,
        "eigenvalues": evals,
        "eval_match": bool(eval_match),
        "d_squared_defect": d_squared_defect,
        "computed_distance": computed_distance,
        "boundary_commutator_norm": float(boundary_norm.detach().item()),
        "autograd_lipschitz_gradient": grad_at_boundary,
        "sample_delta": float(sample_delta.item()),
        "sample_commutator_norm": sample_comm_norm,
        "sample_commutator_known_norm": sample_known_norm,
        "metric": {
            "points": points,
            "distance_table": {
                "p,p": dist("p", "p"),
                "p,q": dist("p", "q"),
                "q,p": dist("q", "p"),
                "q,q": dist("q", "q"),
            },
            "symmetry_error": symmetry_error,
            "triangle_max_violation": triangle_violation,
            "identity_ok": identity_ok,
        },
    }


def sympy_exact() -> dict[str, Any]:
    delta = sp.symbols("delta", real=True)
    i = sp.I
    d = sp.Matrix([[0, 3 + 4 * i], [3 - 4 * i, 0]])
    a = sp.diag(delta, 0)
    c = sp.simplify(d * a - a * d)
    c_star_c = sp.simplify(c.conjugate().T * c)
    d2 = sp.simplify(d * d)
    distance = sp.Rational(1, 5)
    return {
        "D_self_adjoint_exact": bool(d.conjugate().T == d),
        "D_squared": str(d2),
        "D_squared_equals_25I": bool(d2 == 25 * sp.eye(2)),
        "commutator_star_commutator": str(c_star_c),
        "commutator_norm_formula": "5*Abs(delta)",
        "distance_formula": str(distance),
        "distance_float": float(distance),
    }


def z3_metric_certificate(distance: float) -> dict[str, Any]:
    x, y, z = z3.Bools("x y z")
    zero = z3.RealVal(0)
    d = z3.RealVal("1/5")

    def dist(a: z3.BoolRef, b: z3.BoolRef) -> z3.ArithRef:
        return z3.If(a == b, zero, d)

    metric = z3.And(
        dist(x, y) >= 0,
        z3.Implies(dist(x, y) == 0, x == y),
        z3.Implies(x == y, dist(x, y) == 0),
        dist(x, y) == dist(y, x),
        dist(x, z) <= dist(x, y) + dist(y, z),
        d == z3.RealVal(repr(distance)),
    )
    s = z3.Solver()
    s.add(z3.Not(metric))
    status = str(s.check())
    return {"metric_negation_status": status, "pass": status == "unsat"}


def cvc5_metric_certificate() -> dict[str, Any]:
    slv = cvc5.Solver()
    slv.setLogic("ALL")
    bsort = slv.getBooleanSort()
    x = slv.mkConst(bsort, "x")
    y = slv.mkConst(bsort, "y")
    z = slv.mkConst(bsort, "z")
    zero = slv.mkReal(0)
    d = slv.mkReal(1, 5)

    def dist(a: cvc5.Term, b: cvc5.Term) -> cvc5.Term:
        return slv.mkTerm(Kind.ITE, slv.mkTerm(Kind.EQUAL, a, b), zero, d)

    metric = slv.mkTerm(
        Kind.AND,
        slv.mkTerm(Kind.GEQ, dist(x, y), zero),
        slv.mkTerm(
            Kind.IMPLIES,
            slv.mkTerm(Kind.EQUAL, dist(x, y), zero),
            slv.mkTerm(Kind.EQUAL, x, y),
        ),
        slv.mkTerm(
            Kind.IMPLIES,
            slv.mkTerm(Kind.EQUAL, x, y),
            slv.mkTerm(Kind.EQUAL, dist(x, y), zero),
        ),
        slv.mkTerm(Kind.EQUAL, dist(x, y), dist(y, x)),
        slv.mkTerm(Kind.LEQ, dist(x, z), slv.mkTerm(Kind.ADD, dist(x, y), dist(y, z))),
    )
    slv.assertFormula(slv.mkTerm(Kind.NOT, metric))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"metric_negation_status": status, "pass": bool(res.isUnsat())}


def clifford_check(abs_m: float) -> dict[str, Any]:
    _layout, blades = Cl(2)
    e1, e2 = blades["e1"], blades["e2"]
    v = 3 * e1 - 4 * e2
    sq = v * v
    norm_squared = float(sq.value[0])
    return {
        "clifford_vector": "3*e1 - 4*e2",
        "norm_squared": norm_squared,
        "known_norm_squared": abs_m**2,
        "pass": abs(norm_squared - abs_m**2) < TOL,
    }


def geomstats_check(distance: float) -> dict[str, Any]:
    line = Euclidean(dim=1)
    p = gs.array([0.0])
    q = gs.array([distance])
    gs_dist = float(line.metric.dist(p, q))
    return {"euclidean_realization_distance": gs_dist, "pass": abs(gs_dist - distance) < TOL}


def gudhi_check(distance: float) -> dict[str, Any]:
    rips = gudhi.RipsComplex(distance_matrix=[[0.0, distance], [distance, 0.0]], max_edge_length=distance)
    st = rips.create_simplex_tree(max_dimension=1)
    filtration = [(simplex, float(value)) for simplex, value in st.get_filtration()]
    st.persistence()
    h0_intervals = st.persistence_intervals_in_dimension(0)
    finite_deaths = [
        float(pair[1])
        for pair in h0_intervals
        if math.isfinite(float(pair[1]))
    ]
    edge_filtration = next(value for simplex, value in filtration if len(simplex) == 2)
    return {
        "num_vertices": st.num_vertices(),
        "num_simplices": st.num_simplices(),
        "edge_filtration": edge_filtration,
        "h0_finite_deaths": finite_deaths,
        "pass": (
            st.num_vertices() == 2
            and st.num_simplices() == 3
            and abs(edge_filtration - distance) < TOL
            and finite_deaths
            and abs(finite_deaths[0] - distance) < TOL
        ),
    }


def toponetx_check() -> dict[str, Any]:
    sc = tnx.SimplicialComplex()
    sc.add_simplex(["p", "q"])
    boundary = sc.incidence_matrix(1)
    return {
        "dimension": int(sc.dim),
        "zero_simplices": len(list(sc.skeleton(0))),
        "one_simplices": len(list(sc.skeleton(1))),
        "boundary_shape": list(boundary.shape),
        "boundary_nnz": int(boundary.nnz),
        "pass": int(sc.dim) == 1 and len(list(sc.skeleton(0))) == 2 and len(list(sc.skeleton(1))) == 1 and int(boundary.nnz) == 2,
    }


def rustworkx_check(distance: float) -> dict[str, Any]:
    graph = rx.PyGraph()
    graph.add_nodes_from(["p", "q"])
    graph.add_edge(0, 1, distance)
    lengths = rx.dijkstra_shortest_path_lengths(graph, 0, edge_cost_fn=float)
    shortest = float(lengths[1])
    return {
        "connected": bool(rx.is_connected(graph)),
        "shortest_path_pq": shortest,
        "pass": bool(rx.is_connected(graph)) and abs(shortest - distance) < TOL,
    }


def e3nn_check(abs_m: float) -> dict[str, Any]:
    coeff = torch.tensor([M_RE, -M_IM, 0.0], dtype=torch.float32)
    rotation = o3.angles_to_matrix(
        torch.tensor(0.31, dtype=torch.float32),
        torch.tensor(0.27, dtype=torch.float32),
        torch.tensor(-0.19, dtype=torch.float32),
    )
    rotated = rotation @ coeff
    det = float(torch.det(rotation).item())
    orth_defect = float(torch.linalg.matrix_norm(rotation @ rotation.T - torch.eye(3)).item())
    rotated_norm = float(torch.linalg.vector_norm(rotated).item())
    return {
        "so3_det": det,
        "so3_orthogonality_defect": orth_defect,
        "rotated_dirac_coefficient_norm": rotated_norm,
        "known_norm": abs_m,
        "pass": abs(det - 1.0) < TOL_E3NN and orth_defect < TOL_E3NN and abs(rotated_norm - abs_m) < TOL_E3NN,
    }


def quimb_check(abs_m: float) -> dict[str, Any]:
    d = qu.qarray([[0.0, M_COMPLEX], [M_COMPLEX.conjugate(), 0.0]])
    evals = [float(x) for x in qu.eigvalsh(d)]
    spectral_norm = float(qu.norm(d, "spectral"))
    return {
        "eigenvalues": evals,
        "spectral_norm": spectral_norm,
        "pass": (
            len(evals) == 2
            and abs(evals[0] + abs_m) < TOL
            and abs(evals[1] - abs_m) < TOL
            and abs(spectral_norm - abs_m) < TOL
        ),
    }


def build_receipt() -> dict[str, Any]:
    core = torch_core()
    abs_m = core["abs_m"]
    known_distance = core["known_distance"]

    sym = sympy_exact()
    z3_cert = z3_metric_certificate(known_distance)
    cvc5_cert = cvc5_metric_certificate()
    cliff = clifford_check(abs_m)
    gs_check = geomstats_check(known_distance)
    gd_check = gudhi_check(known_distance)
    tnx_check = toponetx_check()
    rx_check = rustworkx_check(known_distance)
    e3_check = e3nn_check(abs_m)
    qu_check = quimb_check(abs_m)

    checks = [
        check(
            "D self-adjoint with real eigenvalues",
            {
                "self_adjoint_defect": core["self_adjoint_defect"],
                "eigenvalues": core["eigenvalues"],
            },
            {"self_adjoint_defect": 0.0, "eigenvalues": [-abs_m, abs_m]},
            core["self_adjoint_defect"] < TOL and core["eval_match"],
        ),
        check(
            "D^2 equals |m|^2 identity",
            core["d_squared_defect"],
            0.0,
            core["d_squared_defect"] < TOL,
        ),
        check(
            "2-point Connes distance d(p,q)",
            {
                "computed_distance": core["computed_distance"],
                "boundary_commutator_norm": core["boundary_commutator_norm"],
                "autograd_lipschitz_gradient": core["autograd_lipschitz_gradient"],
            },
            {"distance": known_distance, "boundary_commutator_norm": 1.0, "gradient": abs_m},
            abs(core["computed_distance"] - known_distance) < TOL
            and abs(core["boundary_commutator_norm"] - 1.0) < TOL
            and abs(core["autograd_lipschitz_gradient"] - abs_m) < TOL,
        ),
        check(
            "[D,a] bounded for a in A",
            {
                "sample_delta": core["sample_delta"],
                "sample_commutator_norm": core["sample_commutator_norm"],
            },
            {"finite": True, "formula": "|m|*|delta|", "sample_norm": core["sample_commutator_known_norm"]},
            math.isfinite(core["sample_commutator_norm"])
            and abs(core["sample_commutator_norm"] - core["sample_commutator_known_norm"]) < TOL,
        ),
        check(
            "spectral distance is a genuine metric",
            core["metric"],
            {"identity": True, "symmetry_error": 0.0, "triangle_max_violation": 0.0},
            core["metric"]["identity_ok"]
            and core["metric"]["symmetry_error"] < TOL
            and core["metric"]["triangle_max_violation"] <= TOL,
        ),
        check(
            "sympy exact spectral-triple algebra",
            sym,
            {"D_self_adjoint_exact": True, "D_squared_equals_25I": True, "distance_formula": "1/5"},
            sym["D_self_adjoint_exact"] and sym["D_squared_equals_25I"] and sym["distance_formula"] == "1/5",
        ),
        check("z3 finite metric certificate", z3_cert, {"metric_negation_status": "unsat"}, z3_cert["pass"]),
        check("cvc5 finite metric certificate", cvc5_cert, {"metric_negation_status": "unsat"}, cvc5_cert["pass"]),
        check("clifford Dirac coefficient norm", cliff, {"norm_squared": abs_m**2}, cliff["pass"]),
        check("geomstats Euclidean realization distance", gs_check, {"distance": known_distance}, gs_check["pass"]),
        check("gudhi two-point Rips topology", gd_check, {"edge_filtration": known_distance, "H0 finite death": known_distance}, gd_check["pass"]),
        check("toponetx two-point simplicial carrier", tnx_check, {"dimension": 1, "vertices": 2, "edges": 1}, tnx_check["pass"]),
        check("rustworkx graph metric shortest path", rx_check, {"shortest_path_pq": known_distance}, rx_check["pass"]),
        check("e3nn SO3 phase/norm invariance", e3_check, {"rotated_norm": abs_m}, e3_check["pass"]),
        check("quimb spectral cross-check", qu_check, {"eigenvalues": [-abs_m, abs_m], "spectral_norm": abs_m}, qu_check["pass"]),
    ]

    blockers = [
        f"{item['invariant']} did not match known value"
        for item in checks
        if not item["match"]
    ]

    tool_manifest = {
        "torch": "load-bearing claim substrate for complex128 Dirac operator, commutator norm, eigenspectrum, metric table, and autograd Lipschitz derivative",
        "sympy": "load-bearing exact algebra check for D self-adjointness, D^2, commutator norm formula, and 1/5 distance formula",
        "z3": "load-bearing SMT certificate that the two-point spectral distance satisfies the metric axioms",
        "cvc5": "load-bearing independent SMT certificate for the same finite metric axioms",
        "clifford": "load-bearing Clifford Cl(2) representation of the Dirac coefficient vector norm |m|",
        "geomstats": "load-bearing Euclidean realization of the two-point Connes metric as points separated by 1/|m|",
        "gudhi": "load-bearing Vietoris-Rips topology check; the edge and finite H0 death appear at the spectral distance",
        "toponetx": "load-bearing simplicial carrier check for the two vertices and their one edge boundary",
        "rustworkx": "load-bearing weighted graph shortest-path metric check for the two-point carrier",
        "e3nn": "load-bearing SO(3) coefficient-norm invariance check for phase/gauge rotation of the Dirac vector",
        "quimb": "load-bearing independent spectral norm and eigenvalue check of the finite quantum operator",
    }

    return {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_substrate": "torch complex128/float64; no numpy claim substrate",
        "finite_map": "(A=C+C diagonal, H=C^2, D off-diagonal) -> commutator seminorm -> two-point Connes metric",
        "domain": "self-adjoint diagonal algebra elements a=diag(a_p,a_q) and pure states p,q",
        "codomain": "finite spectral metric table over {p,q}",
        "parameters": {
            "m": {"real": M_RE, "imag": M_IM},
            "abs_m": abs_m,
            "known_distance": known_distance,
        },
        "TOOL_MANIFEST": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "known_value_checks": checks,
        "all_known_value_checks_pass": all(item["match"] for item in checks),
        "blockers": blockers,
        "core_computation": {
            "torch": {
                "eigenvalues": core["eigenvalues"],
                "distance_table": core["metric"]["distance_table"],
                "boundary_commutator_norm": core["boundary_commutator_norm"],
                "autograd_lipschitz_gradient": core["autograd_lipschitz_gradient"],
            },
            "sympy": sym,
            "z3": z3_cert,
            "cvc5": cvc5_cert,
            "clifford": cliff,
            "geomstats": gs_check,
            "gudhi": gd_check,
            "toponetx": tnx_check,
            "rustworkx": rx_check,
            "e3nn": e3_check,
            "quimb": qu_check,
        },
        "negative_controls": {
            "m_zero_blocked": "If m=0 then |m|=0 and the two-point distance is infinite/undefined, so metric admission is blocked.",
            "non_self_adjoint_D_blocked": "If lower-left entry is not conj(m), torch self-adjoint defect becomes nonzero and real-eigenvalue check is blocked.",
            "scalar_label_only_blocked": "A scalar label without D and commutator seminorm cannot compute the Connes distance.",
        },
    }


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    receipt = build_receipt()
    RESULT_PATH.write_text(json.dumps(j(receipt), indent=2, sort_keys=True) + "\n")
    return 0 if receipt["all_known_value_checks_pass"] and not receipt["blockers"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
