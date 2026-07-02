#!/usr/bin/env python3
"""Independent S^3 spinor/unit-quaternion geometry probe.

Diagnostic-only lego-phase probe. Core claim-bearing computations use
torch.complex128/float64. Library outputs are read only as independent tool
checks.

Finite map:
  psi = (z0,z1) in C^2, ||psi|| = 1
    -> x = (Re z0, Im z0, Re z1, Im z1) in S^3 subset R^4
    -> q = Re z0 + Im z0 i + Re z1 j + Im z1 k, ||q|| = 1
    -> SO(3) rotation induced by the unit quaternion.
"""

from __future__ import annotations

import itertools
import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover - receipt path records blocker
    sp = None
    SYMPY_IMPORT_ERROR = repr(exc)
else:
    SYMPY_IMPORT_ERROR = None

try:
    import z3
except Exception as exc:  # pragma: no cover
    z3 = None
    Z3_IMPORT_ERROR = repr(exc)
else:
    Z3_IMPORT_ERROR = None

try:
    import cvc5
    from cvc5 import Kind
except Exception as exc:  # pragma: no cover
    cvc5 = None
    Kind = None
    CVC5_IMPORT_ERROR = repr(exc)
else:
    CVC5_IMPORT_ERROR = None

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover
    Cl = None
    CLIFFORD_IMPORT_ERROR = repr(exc)
else:
    CLIFFORD_IMPORT_ERROR = None

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere
except Exception as exc:  # pragma: no cover
    gs = None
    Hypersphere = None
    GEOMSTATS_IMPORT_ERROR = repr(exc)
else:
    GEOMSTATS_IMPORT_ERROR = None

try:
    import gudhi
except Exception as exc:  # pragma: no cover
    gudhi = None
    GUDHI_IMPORT_ERROR = repr(exc)
else:
    GUDHI_IMPORT_ERROR = None

try:
    import toponetx as tnx
except Exception as exc:  # pragma: no cover
    tnx = None
    TOPONETX_IMPORT_ERROR = repr(exc)
else:
    TOPONETX_IMPORT_ERROR = None

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover
    rx = None
    RUSTWORKX_IMPORT_ERROR = repr(exc)
else:
    RUSTWORKX_IMPORT_ERROR = None

try:
    from e3nn import o3
except Exception as exc:  # pragma: no cover
    o3 = None
    E3NN_IMPORT_ERROR = repr(exc)
else:
    E3NN_IMPORT_ERROR = None


CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-9
TOL_DISTANCE = 1.0e-7
TOL_GEOMSTATS = 1.0e-7
TOL_E3NN = 1.0e-5
TOL_SMT = 1.0e-9
SAMPLE_SIZES = [8, 16, 32, 64]
SEEDS = [11, 23, 37]
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_s3_spinor_codex_probe"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"


def normalize_spinor(psi: torch.Tensor) -> torch.Tensor:
    return psi.to(CDTYPE) / torch.linalg.vector_norm(psi.to(CDTYPE))


def spinor_to_r4(psi: torch.Tensor) -> torch.Tensor:
    psi = normalize_spinor(psi)
    return torch.stack((psi[0].real, psi[0].imag, psi[1].real, psi[1].imag)).to(RTYPE)


def spinor_to_quaternion(psi: torch.Tensor) -> torch.Tensor:
    return spinor_to_r4(psi)


def s3_distance_torch(x: torch.Tensor, y: torch.Tensor) -> float:
    x = x.to(RTYPE) / torch.linalg.vector_norm(x.to(RTYPE))
    y = y.to(RTYPE) / torch.linalg.vector_norm(y.to(RTYPE))
    dot = torch.clamp(torch.dot(x, y), -1.0, 1.0)
    return float(torch.arccos(dot).item())


def sample_spinors(n_states: int, seed: int) -> list[torch.Tensor]:
    gen = torch.Generator().manual_seed(seed)
    out = []
    for _ in range(n_states):
        re = torch.randn(2, generator=gen, dtype=RTYPE)
        im = torch.randn(2, generator=gen, dtype=RTYPE)
        out.append(normalize_spinor(re + 1j * im))
    return out


def quaternion_to_so3(q: torch.Tensor) -> torch.Tensor:
    q = q.to(RTYPE) / torch.linalg.vector_norm(q.to(RTYPE))
    w, x, y, z = q
    return torch.stack((
        torch.stack((1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y))),
        torch.stack((2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x))),
        torch.stack((2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y))),
    )).to(RTYPE)


def torch_geodesic_autograd_evidence() -> dict[str, Any]:
    x = torch.tensor([1.0, 0.0, 0.0, 0.0], dtype=RTYPE)
    v = torch.tensor([0.0, 1.0, 0.0, 0.0], dtype=RTYPE)
    t = torch.tensor(0.413, dtype=RTYPE, requires_grad=True)
    gamma = torch.cos(t) * x + torch.sin(t) * v
    deriv = []
    for k in range(4):
        deriv.append(torch.autograd.grad(gamma[k], t, retain_graph=True)[0])
    velocity = torch.stack(deriv)
    norm_gamma = float(torch.linalg.vector_norm(gamma).item())
    speed = float(torch.linalg.vector_norm(velocity).item())
    radial_dot = float(torch.dot(gamma.detach(), velocity.detach()).item())
    return {
        "path": "gamma(t)=cos(t)x+sin(t)v with x perp v in R4",
        "sample_t": float(t.detach().item()),
        "norm_gamma": norm_gamma,
        "speed": speed,
        "radial_dot": radial_dot,
        "pass": abs(norm_gamma - 1.0) < TOL and abs(speed - 1.0) < TOL and abs(radial_dot) < TOL,
    }


def sympy_s3_exact_evidence() -> dict[str, Any]:
    if sp is None:
        return {"pass": False, "blocker": f"sympy import failed: {SYMPY_IMPORT_ERROR}"}
    chi, theta, phi = sp.symbols("chi theta phi", real=True)
    coords = [
        sp.cos(chi),
        sp.sin(chi) * sp.cos(theta),
        sp.sin(chi) * sp.sin(theta) * sp.cos(phi),
        sp.sin(chi) * sp.sin(theta) * sp.sin(phi),
    ]
    norm_sq = sp.simplify(sum(c * c for c in coords))
    antipodal_dot = sp.simplify(sum(c * (-c) for c in coords))
    return {
        "s3_parameterization_norm_squared": str(norm_sq),
        "antipodal_dot_for_unit_point": str(antipodal_dot),
        "norm_exact": bool(sp.simplify(norm_sq - 1) == 0),
        "antipodal_dot_exact": bool(sp.simplify(antipodal_dot + 1) == 0),
        "pass": bool(sp.simplify(norm_sq - 1) == 0 and sp.simplify(antipodal_dot + 1) == 0),
    }


def z3_unit_norm_certificate(coords: torch.Tensor) -> dict[str, Any]:
    if z3 is None:
        return {"pass": False, "negation_status": "not_run", "blocker": f"z3 import failed: {Z3_IMPORT_ERROR}"}
    vals = [float(x) for x in coords.to(RTYPE)]
    solver = z3.Solver()
    xs = [z3.Real(f"x{k}") for k in range(4)]
    tol = z3.RealVal(repr(TOL_SMT))
    for var, val in zip(xs, vals):
        solver.add(var == z3.RealVal(repr(val)))
    norm_sq = sum(var * var for var in xs)
    close = z3.And(norm_sq - 1 <= tol, norm_sq - 1 >= -tol)
    solver.add(z3.Not(close))
    status = str(solver.check())
    return {
        "negation_status": status,
        "norm_squared": sum(v * v for v in vals),
        "pass": status == "unsat",
    }


def cvc5_unit_norm_certificate(coords: torch.Tensor) -> dict[str, Any]:
    if cvc5 is None or Kind is None or sp is None:
        return {
            "pass": False,
            "negation_status": "not_run",
            "blocker": f"cvc5/sympy import failed: cvc5={CVC5_IMPORT_ERROR} sympy={SYMPY_IMPORT_ERROR}",
        }
    vals = [float(x) for x in coords.to(RTYPE)]
    slv = cvc5.Solver()
    slv.setOption("produce-models", "false")
    slv.setLogic("QF_NRA")
    real_sort = slv.getRealSort()

    def rv(x: float):
        frac = sp.Rational(x).limit_denominator(10**12)
        num, den = sp.fraction(frac)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    def add_terms(terms):
        acc = terms[0]
        for term in terms[1:]:
            acc = slv.mkTerm(Kind.ADD, acc, term)
        return acc

    xs = [slv.mkConst(real_sort, f"cx{k}") for k in range(4)]
    for var, val in zip(xs, vals):
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, var, rv(val)))
    norm_sq = add_terms([slv.mkTerm(Kind.MULT, var, var) for var in xs])
    diff = slv.mkTerm(Kind.SUB, norm_sq, slv.mkReal(1))
    tol = rv(TOL_SMT)
    zero = slv.mkReal(0)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol)
    close = slv.mkTerm(Kind.AND, slv.mkTerm(Kind.LEQ, diff, tol), slv.mkTerm(Kind.GEQ, diff, neg_tol))
    slv.assertFormula(slv.mkTerm(Kind.NOT, close))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"negation_status": status, "norm_squared": sum(v * v for v in vals), "pass": res.isUnsat()}


def clifford_quaternion_norm(q: torch.Tensor) -> dict[str, Any]:
    if Cl is None:
        return {"pass": False, "blocker": f"clifford import failed: {CLIFFORD_IMPORT_ERROR}"}
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    w, x, y, z = [float(v) for v in q.to(RTYPE)]
    qi = w + x * (e2 * e3) + y * (e3 * e1) + z * (e1 * e2)
    norm_sq = float((qi * (~qi)).value[0])
    return {
        "basis": "Cl(3) even basis {1,e23,e31,e12}",
        "computed_reverse_norm_squared": norm_sq,
        "pass": abs(norm_sq - 1.0) < TOL,
    }


def geomstats_hypersphere_evidence(x: torch.Tensor) -> dict[str, Any]:
    if gs is None or Hypersphere is None:
        return {"pass": False, "blocker": f"geomstats import failed: {GEOMSTATS_IMPORT_ERROR}"}
    sphere = Hypersphere(dim=3)
    point = gs.array([float(v) for v in x.to(RTYPE)])
    antipode = gs.array([float(-v) for v in x.to(RTYPE)])
    dist_antipodal = sphere.metric.dist(point, antipode)
    dist_self = sphere.metric.dist(point, point)
    belongs = sphere.belongs(point, atol=TOL_GEOMSTATS)
    return {
        "model": "geomstats.geometry.hypersphere.Hypersphere(dim=3)",
        "antipodal_distance": float(dist_antipodal),
        "self_distance": float(dist_self),
        "belongs": bool(belongs),
        "pass": abs(float(dist_antipodal) - math.pi) < TOL_GEOMSTATS
        and abs(float(dist_self)) < TOL_GEOMSTATS
        and bool(belongs),
    }


def gudhi_boundary_s3_evidence() -> dict[str, Any]:
    if gudhi is None:
        return {"pass": False, "blocker": f"gudhi import failed: {GUDHI_IMPORT_ERROR}"}
    st = gudhi.SimplexTree()
    vertices = range(5)
    for size in range(1, 5):
        for simplex in itertools.combinations(vertices, size):
            st.insert(simplex, filtration=0.0)
    st.persistence(persistence_dim_max=True)
    betti = list(st.betti_numbers())
    expected = [1, 0, 0, 1]
    return {
        "complex": "boundary of 4-simplex, a finite triangulation of S^3",
        "num_simplices": st.num_simplices(),
        "dimension": st.dimension(),
        "betti_numbers": betti,
        "expected_betti_prefix": expected,
        "pass": st.dimension() == 3 and betti[:4] == expected,
    }


def toponetx_boundary_s3_evidence() -> dict[str, Any]:
    if tnx is None:
        return {"pass": False, "blocker": f"toponetx import failed: {TOPONETX_IMPORT_ERROR}"}
    facets = [list(simplex) for simplex in itertools.combinations(range(5), 4)]
    sc = tnx.SimplicialComplex(facets)
    shape = list(sc.shape)
    dim = int(sc.dim)
    expected_shape = [5, 10, 10, 5]
    return {
        "complex": "TopoNetX boundary of 4-simplex",
        "shape": shape,
        "dimension": dim,
        "expected_shape": expected_shape,
        "pass": dim == 3 and shape == expected_shape,
    }


def rustworkx_boundary_graph_evidence() -> dict[str, Any]:
    if rx is None:
        return {"pass": False, "blocker": f"rustworkx import failed: {RUSTWORKX_IMPORT_ERROR}"}
    graph = rx.PyGraph()
    graph.add_nodes_from(range(5))
    for i, j in itertools.combinations(range(5), 2):
        graph.add_edge(i, j, None)
    degrees = [int(graph.degree(i)) for i in range(5)]
    connected = bool(rx.is_connected(graph))
    return {
        "graph": "1-skeleton of boundary of 4-simplex (K5)",
        "num_nodes": graph.num_nodes(),
        "num_edges": graph.num_edges(),
        "degrees": degrees,
        "connected": connected,
        "pass": connected and graph.num_nodes() == 5 and graph.num_edges() == 10 and degrees == [4, 4, 4, 4, 4],
    }


def e3nn_quaternion_so3_evidence(q: torch.Tensor) -> dict[str, Any]:
    if o3 is None:
        return {"pass": False, "blocker": f"e3nn import failed: {E3NN_IMPORT_ERROR}"}
    r = quaternion_to_so3(q)
    det = float(torch.det(r).item())
    orth = float(torch.linalg.matrix_norm(r @ r.T - torch.eye(3, dtype=RTYPE)).item())
    if abs(det - 1.0) >= TOL_E3NN or orth >= TOL_E3NN:
        return {
            "det": det,
            "orthogonality_defect": orth,
            "e3nn_reconstruction_err": None,
            "pass": False,
        }
    rf = r.to(torch.float32)
    a, b, c = o3.matrix_to_angles(rf)
    r_rec = o3.angles_to_matrix(a, b, c)
    recon = float(torch.linalg.matrix_norm(r_rec - rf).item())
    return {
        "det": det,
        "orthogonality_defect": orth,
        "e3nn_reconstruction_err": recon,
        "pass": abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and recon < TOL_E3NN,
    }


def sample_blocks() -> tuple[list[dict[str, Any]], list[torch.Tensor]]:
    blocks = []
    all_psis: list[torch.Tensor] = []
    for n_states, seed in itertools.product(SAMPLE_SIZES, SEEDS):
        psis = sample_spinors(n_states, seed)
        all_psis.extend(psis)
        r4s = [spinor_to_r4(psi) for psi in psis]
        qs = [spinor_to_quaternion(psi) for psi in psis]
        spinor_norm_errs = [abs(float(torch.linalg.vector_norm(psi).item()) - 1.0) for psi in psis]
        r4_norm_errs = [abs(float(torch.linalg.vector_norm(x).item()) - 1.0) for x in r4s]
        quat_norm_errs = [abs(float(torch.linalg.vector_norm(q).item()) - 1.0) for q in qs]
        antipodal_errs = [abs(s3_distance_torch(x, -x) - math.pi) for x in r4s]
        self_distances = [s3_distance_torch(x, x) for x in r4s]
        blocks.append({
            "n_states": n_states,
            "seed": seed,
            "max_spinor_norm_err": max(spinor_norm_errs),
            "max_r4_norm_err": max(r4_norm_errs),
            "max_quaternion_norm_err": max(quat_norm_errs),
            "max_antipodal_distance_err": max(antipodal_errs),
            "max_self_distance": max(abs(v) for v in self_distances),
        })
    return blocks, all_psis


def known_value_checks(
    blocks: list[dict[str, Any]],
    representative: torch.Tensor,
    geomstats_ev: dict[str, Any],
    clifford_ev: dict[str, Any],
    autograd_ev: dict[str, Any],
    sympy_ev: dict[str, Any],
    gudhi_ev: dict[str, Any],
    toponetx_ev: dict[str, Any],
    rustworkx_ev: dict[str, Any],
    e3nn_ev: dict[str, Any],
) -> list[dict[str, Any]]:
    max_antipodal_err = max(b["max_antipodal_distance_err"] for b in blocks)
    max_self_dist = max(b["max_self_distance"] for b in blocks)
    max_spinor_norm_err = max(b["max_spinor_norm_err"] for b in blocks)
    max_r4_norm_err = max(b["max_r4_norm_err"] for b in blocks)
    max_quaternion_norm_err = max(b["max_quaternion_norm_err"] for b in blocks)
    x = spinor_to_r4(representative)
    q = spinor_to_quaternion(representative)
    rep_antipodal = s3_distance_torch(x, -x)
    rep_self = s3_distance_torch(x, x)
    rep_spinor_norm = float(torch.linalg.vector_norm(representative).item())
    rep_q_norm = float(torch.linalg.vector_norm(q).item())
    return [
        {
            "invariant": "antipodal_geodesic_distance(psi,-psi)",
            "computed": rep_antipodal,
            "known": math.pi,
            "match": abs(rep_antipodal - math.pi) < TOL_DISTANCE and max_antipodal_err < TOL_DISTANCE,
        },
        {
            "invariant": "distance(psi,psi)",
            "computed": rep_self,
            "known": 0.0,
            "match": abs(rep_self) < TOL_DISTANCE and max_self_dist < TOL_DISTANCE,
        },
        {
            "invariant": "||psi||==1 all samples",
            "computed": {
                "representative": rep_spinor_norm,
                "max_spinor_norm_err": max_spinor_norm_err,
                "max_r4_norm_err": max_r4_norm_err,
            },
            "known": 1.0,
            "match": max_spinor_norm_err < TOL and max_r4_norm_err < TOL,
        },
        {
            "invariant": "unit quaternion ||q||==1",
            "computed": {"representative": rep_q_norm, "max_quaternion_norm_err": max_quaternion_norm_err},
            "known": 1.0,
            "match": max_quaternion_norm_err < TOL,
        },
        {
            "invariant": "geomstats Hypersphere(dim=3) antipodal/self distances",
            "computed": {
                "antipodal_distance": geomstats_ev.get("antipodal_distance"),
                "self_distance": geomstats_ev.get("self_distance"),
                "belongs": geomstats_ev.get("belongs"),
            },
            "known": {"antipodal_distance": math.pi, "self_distance": 0.0, "belongs": True},
            "match": bool(geomstats_ev.get("pass")),
        },
        {
            "invariant": "clifford Cl(3) even-quaternion reverse norm",
            "computed": clifford_ev.get("computed_reverse_norm_squared"),
            "known": 1.0,
            "match": bool(clifford_ev.get("pass")),
        },
        {
            "invariant": "torch autograd S^3 geodesic unit speed",
            "computed": {
                "norm_gamma": autograd_ev["norm_gamma"],
                "speed": autograd_ev["speed"],
                "radial_dot": autograd_ev["radial_dot"],
            },
            "known": {"norm_gamma": 1.0, "speed": 1.0, "radial_dot": 0.0},
            "match": bool(autograd_ev["pass"]),
        },
        {
            "invariant": "sympy exact S^3 parameterization norm",
            "computed": sympy_ev.get("s3_parameterization_norm_squared"),
            "known": "1",
            "match": bool(sympy_ev.get("pass")),
        },
        {
            "invariant": "GUDHI boundary-of-4-simplex homology of S^3",
            "computed": gudhi_ev.get("betti_numbers"),
            "known": [1, 0, 0, 1],
            "match": bool(gudhi_ev.get("pass")),
        },
        {
            "invariant": "TopoNetX boundary-of-4-simplex f-vector",
            "computed": toponetx_ev.get("shape"),
            "known": [5, 10, 10, 5],
            "match": bool(toponetx_ev.get("pass")),
        },
        {
            "invariant": "rustworkx K5 one-skeleton of 4-simplex boundary",
            "computed": {
                "num_nodes": rustworkx_ev.get("num_nodes"),
                "num_edges": rustworkx_ev.get("num_edges"),
                "degrees": rustworkx_ev.get("degrees"),
                "connected": rustworkx_ev.get("connected"),
            },
            "known": {"num_nodes": 5, "num_edges": 10, "degrees": [4, 4, 4, 4, 4], "connected": True},
            "match": bool(rustworkx_ev.get("pass")),
        },
        {
            "invariant": "e3nn certifies unit-quaternion induced SO(3)",
            "computed": {
                "det": e3nn_ev.get("det"),
                "orthogonality_defect": e3nn_ev.get("orthogonality_defect"),
                "e3nn_reconstruction_err": e3nn_ev.get("e3nn_reconstruction_err"),
            },
            "known": {"det": 1.0, "orthogonal": True, "reconstructs": True},
            "match": bool(e3nn_ev.get("pass")),
        },
    ]


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    blocks, psis = sample_blocks()
    representative = normalize_spinor(torch.tensor([0.5 + 0.5j, -0.25 + 0.6614378277661477j], dtype=CDTYPE))
    x = spinor_to_r4(representative)
    q = spinor_to_quaternion(representative)

    autograd_ev = torch_geodesic_autograd_evidence()
    sympy_ev = sympy_s3_exact_evidence()
    z3_ev = z3_unit_norm_certificate(x)
    cvc5_ev = cvc5_unit_norm_certificate(x)
    clifford_ev = clifford_quaternion_norm(q)
    geomstats_ev = geomstats_hypersphere_evidence(x)
    gudhi_ev = gudhi_boundary_s3_evidence()
    toponetx_ev = toponetx_boundary_s3_evidence()
    rustworkx_ev = rustworkx_boundary_graph_evidence()
    e3nn_ev = e3nn_quaternion_so3_evidence(q)

    kvc = known_value_checks(
        blocks,
        representative,
        geomstats_ev,
        clifford_ev,
        autograd_ev,
        sympy_ev,
        gudhi_ev,
        toponetx_ev,
        rustworkx_ev,
        e3nn_ev,
    )
    known_values_all_match = all(row["match"] for row in kvc)
    tools_all_pass = all([
        autograd_ev["pass"],
        sympy_ev.get("pass", False),
        z3_ev.get("pass", False),
        cvc5_ev.get("pass", False),
        clifford_ev.get("pass", False),
        geomstats_ev.get("pass", False),
        gudhi_ev.get("pass", False),
        toponetx_ev.get("pass", False),
        rustworkx_ev.get("pass", False),
        e3nn_ev.get("pass", False),
    ])
    all_pass = known_values_all_match and tools_all_pass

    blockers: list[str] = []
    for name, ev in {
        "sympy": sympy_ev,
        "z3": z3_ev,
        "cvc5": cvc5_ev,
        "clifford": clifford_ev,
        "geomstats": geomstats_ev,
        "gudhi": gudhi_ev,
        "toponetx": toponetx_ev,
        "rustworkx": rustworkx_ev,
        "e3nn": e3nn_ev,
    }.items():
        if not ev.get("pass", False):
            blockers.append(f"{name} tool check failed: {ev}")
    blockers.extend([
        f"KNOWN-VALUE MISMATCH: {row['invariant']} computed={row['computed']} known={row['known']}"
        for row in kvc
        if not row["match"]
    ])

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "core C^2 spinor normalization, S^3 R4 embedding, geodesic distances, quaternion norms, quaternion->SO(3), and autograd geodesic speed are computed in torch.complex128/float64",
        },
        "sympy": {
            "used": True,
            "role": "load_bearing",
            "reason": "exact symbolic S^3 parameterization norm and antipodal dot checks must pass",
        },
        "z3": {
            "used": True,
            "role": "load_bearing",
            "reason": "SMT negation of unit R4 norm within tolerance must be UNSAT for the representative spinor carrier",
        },
        "cvc5": {
            "used": True,
            "role": "load_bearing",
            "reason": "independent SMT negation of the same unit R4 norm certificate must be UNSAT",
        },
        "clifford": {
            "used": True,
            "role": "load_bearing",
            "reason": "Cl(3) even-subalgebra unit-quaternion reverse norm must compute to 1",
        },
        "geomstats": {
            "used": True,
            "role": "load_bearing",
            "reason": "Hypersphere(dim=3) independently computes antipodal/self geodesic distances and point membership",
        },
        "gudhi": {
            "used": True,
            "role": "load_bearing",
            "reason": "boundary of the 4-simplex must have S^3 homology betti prefix [1,0,0,1]",
        },
        "toponetx": {
            "used": True,
            "role": "load_bearing",
            "reason": "finite boundary-of-4-simplex simplicial complex must expose f-vector [5,10,10,5]",
        },
        "rustworkx": {
            "used": True,
            "role": "load_bearing",
            "reason": "the 1-skeleton of that finite S^3 triangulation must be connected K5 with degree 4 at each vertex",
        },
        "e3nn": {
            "used": True,
            "role": "load_bearing",
            "reason": "quaternion-induced SO(3) matrix must survive e3nn l=1 angle reconstruction",
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
        "sim_class": "known_geometry_probe",
        "purpose": "Independent S^3 spinor/unit-quaternion known-geometry probe for cross-model comparison; diagnostic_only lego phase.",
        "scientific_question": "Does the finite torch C^2 spinor carrier reproduce the known S^3/unit-quaternion geometry and the required exact values?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted; no manifold layer, stacking, coupling, Axis0, flux, Xi, Phi0, bridge, basin, gravity, or physics claim.",
        "finite_map": "(normalized psi in C^2) -> (R4 point on S^3, unit quaternion q, geodesic distances, finite S^3 triangulation checks, quaternion-induced SO(3))",
        "domain": "normalized two-component complex spinors psi in C^2, sampled in torch.complex128",
        "codomain_or_output": "S^3 embedded in R4, unit quaternions, Hypersphere(3) distances, finite boundary-of-4-simplex topology, SO(3) matrices",
        "carrier_layer": "S^3 spinor carrier: {psi in C^2 : ||psi||=1}",
        "geometry_layer": "S^3 unit sphere in R4 with unit-quaternion identification",
        "carrier_realization": "torch.complex128 spinors and torch.float64 R4/quaternion carriers; no NumPy claim-bearing substrate",
        "spinor_state": "torch.complex128 two-component spinors psi",
        "quaternion_action": "psi=(a+bi,c+di) maps to q=(a,b,c,d); unit q induces SO(3) via the standard quaternion rotation formula",
        "peps3d_embedding": "not_applicable_at_lego_phase (diagnostic_only known-geometry probe)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "known S^3 spinor/unit-quaternion geometry values",
        "branch_status_before_run": "lego/pre-sim phase; standalone known geometry; unadmitted",
        "allowed_claims": ["standalone diagnostic known-math S^3 spinor/unit-quaternion geometry witness"],
        "promotion_blockers": ["diagnostic_only by design; no manifold membership, cross-layer evidence, or coupling"],
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": known_values_all_match,
            "tools_all_pass": tools_all_pass,
            "n_known_value_checks": len(kvc),
            "n_sampled_states": len(psis),
            "sample_sizes": SAMPLE_SIZES,
            "seeds": SEEDS,
            "result_path": str(RESULT_PATH),
            "promotion_allowed": False,
        },
        "known_value_checks": kvc,
        "representative": {
            "spinor": [[float(representative[0].real), float(representative[0].imag)], [float(representative[1].real), float(representative[1].imag)]],
            "r4": [float(v) for v in x],
            "quaternion_wxyz": [float(v) for v in q],
        },
        "variation_blocks": blocks,
        "tool_evidence": {
            "torch_autograd": autograd_ev,
            "sympy": sympy_ev,
            "z3": z3_ev,
            "cvc5": cvc5_ev,
            "clifford": clifford_ev,
            "geomstats": geomstats_ev,
            "gudhi": gudhi_ev,
            "toponetx": toponetx_ev,
            "rustworkx": rustworkx_ev,
            "e3nn": e3nn_ev,
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": list(tool_manifest.keys()),
        "required_artifacts": ["json_result_receipt"],
        "artifacts_emitted": ["json_result_receipt"],
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "all required known_value_checks match and every load-bearing tool evidence block passes",
        "fail_rule": "any known-value mismatch, import failure, SMT non-UNSAT result, topology mismatch, or SO(3) reconstruction failure",
        "eligible_consumers": ["other diagnostic_only known-geometry comparison probes"],
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(RESULT_PATH),
        "all_pass": all_pass,
        "known_values_all_match": known_values_all_match,
        "tools_all_pass": tools_all_pass,
        "n_known_value_checks": len(kvc),
        "blockers": blockers,
        "known_value_checks": kvc,
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
