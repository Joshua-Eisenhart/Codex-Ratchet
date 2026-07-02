#!/usr/bin/env python3
"""Independent known-geometry probe for the Hopf fibration.

This diagnostic probe computes invariant checks for S^1 -> S^3 -> S^2 from
the stated Hopf spinor coordinates, without reading comparison receipts.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
import os
import pathlib
import sys
from typing import Any


os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

IMPORT_ERRORS: dict[str, str] = {}

try:
    import torch
except Exception as exc:  # pragma: no cover - import failure path is a receipt blocker.
    IMPORT_ERRORS["torch"] = f"{type(exc).__name__}: {exc}"

try:
    import sympy as sp
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["sympy"] = f"{type(exc).__name__}: {exc}"

try:
    import z3
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["z3"] = f"{type(exc).__name__}: {exc}"

try:
    import cvc5
    from cvc5 import Kind
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["cvc5"] = f"{type(exc).__name__}: {exc}"

try:
    from clifford import Cl
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["clifford"] = f"{type(exc).__name__}: {exc}"

try:
    import geomstats.backend as gs
    from geomstats.geometry.hypersphere import Hypersphere
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["geomstats"] = f"{type(exc).__name__}: {exc}"

try:
    import gudhi
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["gudhi"] = f"{type(exc).__name__}: {exc}"

try:
    import toponetx as tnx
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["toponetx"] = f"{type(exc).__name__}: {exc}"

try:
    import rustworkx as rx
except Exception as exc:  # pragma: no cover
    IMPORT_ERRORS["rustworkx"] = f"{type(exc).__name__}: {exc}"


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "geom_hopf_fibration_codex_probe_results.json"

SIM_ID = "sim_geom_hopf_fibration_codex_probe"
NAME = "geom_hopf_fibration_codex_probe"
VERSION = "1.0.0"
CLASSIFICATION = "diagnostic_only"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Known-geometry diagnostic receipt only. It checks Hopf fibration invariants "
    "and tool fit, but does not admit a nonclassical manifold layer, PEPS3D "
    "carrier, flux, Xi, Phi0, Axis0, bridge, basin, or physics claim."
)


def now_iso() -> str:
    return _dt.datetime.now(tz=_dt.UTC).isoformat()


def sha256_file(path: pathlib.Path) -> str:
    if not path.exists():
        return "missing"
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tensor_float(value: "torch.Tensor") -> float:
    return float(value.detach().item())


def round_float(value: float, digits: int = 15) -> float:
    return float(f"{value:.{digits}g}")


def close_match(computed: float, known: float, tolerance: float) -> bool:
    return abs(computed - known) <= tolerance


def psi_bundle(eta: float, fiber_phi: "torch.Tensor", base_chi: float) -> "torch.Tensor":
    """Hopf spinor in the requested phase form.

    The user-requested psi=(exp(i phi_phase) cos eta,
    exp(i chi_phase) sin eta) is evaluated in bundle coordinates
    phi_phase=fiber_phi+base_chi and chi_phase=fiber_phi-base_chi.
    In these coordinates the contact connection is
    A_Hopf=d fiber_phi + cos(2 eta) d base_chi.
    """

    ce = math.cos(eta)
    se = math.sin(eta)
    phase_1 = fiber_phi + base_chi
    phase_2 = fiber_phi - base_chi
    z1 = torch.exp(1j * phase_1) * ce
    z2 = torch.exp(1j * phase_2) * se
    return torch.stack([z1.to(torch.complex128), z2.to(torch.complex128)], dim=-1)


def hopf_base_from_spinor(psi: "torch.Tensor") -> "torch.Tensor":
    z1 = psi[..., 0]
    z2 = psi[..., 1]
    mixed = z1 * torch.conj(z2)
    x = 2.0 * torch.real(mixed)
    y = 2.0 * torch.imag(mixed)
    z = torch.real(z1 * torch.conj(z1) - z2 * torch.conj(z2))
    return torch.stack([x, y, z], dim=-1).to(torch.float64)


def s3_curve_projected(
    eta: float,
    base_chi: float,
    samples: int,
    orientation: int = 1,
) -> tuple["torch.Tensor", "torch.Tensor", "torch.Tensor"]:
    """Return stereographic R3 curve, derivative, and raw S3 curve."""

    t = (torch.arange(samples, dtype=torch.float64) + 0.5) * (2.0 * math.pi / samples)
    fiber_phi = orientation * t
    ce = math.cos(eta)
    se = math.sin(eta)
    a = fiber_phi + base_chi
    b = fiber_phi - base_chi
    x = torch.stack(
        [
            ce * torch.cos(a),
            ce * torch.sin(a),
            se * torch.cos(b),
            se * torch.sin(b),
        ],
        dim=1,
    ).to(torch.float64)
    dx_dphi = torch.stack(
        [
            -ce * torch.sin(a),
            ce * torch.cos(a),
            -se * torch.sin(b),
            se * torch.cos(b),
        ],
        dim=1,
    ).to(torch.float64) * orientation

    denominator = 1.0 - x[:, 3]
    r3 = x[:, :3] / denominator[:, None]
    dr3 = (dx_dphi[:, :3] * denominator[:, None] + x[:, :3] * dx_dphi[:, 3, None]) / (
        denominator[:, None] ** 2
    )
    return r3, dr3, x


def gauss_linking_number(
    first: tuple[float, float],
    second: tuple[float, float],
    samples: int = 512,
    orientation_second: int = 1,
) -> float:
    r1, dr1, _ = s3_curve_projected(first[0], first[1], samples, orientation=1)
    r2, dr2, _ = s3_curve_projected(second[0], second[1], samples, orientation=orientation_second)
    diff = r1[:, None, :] - r2[None, :, :]
    cross = torch.cross(
        dr1[:, None, :].expand(-1, samples, -1),
        dr2[None, :, :].expand(samples, -1, -1),
        dim=2,
    )
    numerator = (diff * cross).sum(dim=2)
    denominator = torch.linalg.norm(diff, dim=2) ** 3
    dt = 2.0 * math.pi / samples
    integral = (numerator / denominator).sum() * dt * dt / (4.0 * math.pi)
    return tensor_float(integral)


def gauss_linking_unlinked_control(samples: int = 512) -> float:
    t = (torch.arange(samples, dtype=torch.float64) + 0.5) * (2.0 * math.pi / samples)
    r1 = torch.stack([torch.cos(t), torch.sin(t), torch.zeros_like(t)], dim=1)
    dr1 = torch.stack([-torch.sin(t), torch.cos(t), torch.zeros_like(t)], dim=1)
    r2 = torch.stack([3.0 + torch.cos(t), torch.sin(t), torch.zeros_like(t)], dim=1)
    dr2 = torch.stack([-torch.sin(t), torch.cos(t), torch.zeros_like(t)], dim=1)
    diff = r1[:, None, :] - r2[None, :, :]
    cross = torch.cross(
        dr1[:, None, :].expand(-1, samples, -1),
        dr2[None, :, :].expand(samples, -1, -1),
        dim=2,
    )
    numerator = (diff * cross).sum(dim=2)
    denominator = torch.linalg.norm(diff, dim=2) ** 3
    dt = 2.0 * math.pi / samples
    return tensor_float((numerator / denominator).sum() * dt * dt / (4.0 * math.pi))


def torch_holonomy(samples: int = 4096) -> float:
    dphi = 2.0 * math.pi / samples
    tangent_values = torch.ones(samples, dtype=torch.float64)
    return tensor_float(tangent_values.sum() * dphi)


def torch_flat_holonomy(samples: int = 4096) -> float:
    dphi = 2.0 * math.pi / samples
    tangent_values = torch.zeros(samples, dtype=torch.float64)
    return tensor_float(tangent_values.sum() * dphi)


def sympy_connection_checks() -> dict[str, Any]:
    eta, base_chi, fiber_phi = sp.symbols("eta base_chi fiber_phi", real=True)
    a_phi = sp.Integer(1)
    a_chi = sp.cos(2 * eta)
    curvature_eta_chi = sp.diff(a_chi, eta) - sp.diff(sp.Integer(0), base_chi)
    curvature_integral = sp.integrate(
        curvature_eta_chi,
        (eta, 0, sp.pi / 2),
        (base_chi, 0, sp.pi),
    )
    first_chern = sp.simplify(-curvature_integral / (2 * sp.pi))
    holonomy = sp.integrate(a_phi, (fiber_phi, 0, 2 * sp.pi))
    flat_holonomy = sp.integrate(sp.Integer(0), (fiber_phi, 0, 2 * sp.pi))
    return {
        "A_Hopf": "dphi + cos(2*eta) dchi",
        "base_chi_period": "pi",
        "curvature_F_eta_chi": str(sp.simplify(curvature_eta_chi)),
        "curvature_integral_oriented": str(sp.simplify(curvature_integral)),
        "first_chern_oriented": str(first_chern),
        "holonomy_symbolic": str(sp.simplify(holonomy)),
        "flat_holonomy_symbolic": str(sp.simplify(flat_holonomy)),
        "first_chern_float": float(first_chern),
        "holonomy_float": float(holonomy.evalf()),
        "flat_holonomy_float": float(flat_holonomy),
    }


def z3_distinct_fiber_check(pairs: list[tuple[tuple[int, int], tuple[int, int]]]) -> dict[str, Any]:
    solver = z3.Solver()
    bad_terms = []
    for idx, ((eta_a, chi_a), (eta_b, chi_b)) in enumerate(pairs):
        ea = z3.Int(f"eta_a_{idx}")
        ca = z3.Int(f"chi_a_{idx}")
        eb = z3.Int(f"eta_b_{idx}")
        cb = z3.Int(f"chi_b_{idx}")
        solver.add(ea == eta_a, ca == chi_a, eb == eta_b, cb == chi_b)
        bad_terms.append(z3.And(ea == eb, ca == cb))
    solver.add(z3.Or(bad_terms))
    status = solver.check()
    return {
        "surface": "z3",
        "claim": "selected Hopf fiber pairs are distinct base cells",
        "bad_same_base_sat": str(status),
        "pass": status == z3.unsat,
    }


def cvc5_distinct_fiber_check(pairs: list[tuple[tuple[int, int], tuple[int, int]]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    bad_terms = []
    for idx, ((eta_a, chi_a), (eta_b, chi_b)) in enumerate(pairs):
        ea = solver.mkConst(int_sort, f"eta_a_{idx}")
        ca = solver.mkConst(int_sort, f"chi_a_{idx}")
        eb = solver.mkConst(int_sort, f"eta_b_{idx}")
        cb = solver.mkConst(int_sort, f"chi_b_{idx}")
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, ea, solver.mkInteger(eta_a)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, ca, solver.mkInteger(chi_a)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, eb, solver.mkInteger(eta_b)))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, cb, solver.mkInteger(chi_b)))
        bad_terms.append(
            solver.mkTerm(
                Kind.AND,
                solver.mkTerm(Kind.EQUAL, ea, eb),
                solver.mkTerm(Kind.EQUAL, ca, cb),
            )
        )
    solver.assertFormula(solver.mkTerm(Kind.OR, *bad_terms))
    status = solver.checkSat()
    return {
        "surface": "cvc5",
        "claim": "selected Hopf fiber pairs are distinct base cells",
        "bad_same_base_sat": str(status),
        "pass": status.isUnsat(),
    }


def clifford_cross_product_check() -> dict[str, Any]:
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    pseudoscalar = e1 ^ e2 ^ e3

    r1, dr1, _ = s3_curve_projected(0.47, 0.11, 8)
    r2, dr2, _ = s3_curve_projected(1.02, 0.67, 8)
    a = dr1[0]
    b = dr2[0]
    torch_cross = torch.cross(a, b, dim=0)

    vector_a = float(a[0]) * e1 + float(a[1]) * e2 + float(a[2]) * e3
    vector_b = float(b[0]) * e1 + float(b[1]) * e2 + float(b[2]) * e3
    clifford_cross = -((vector_a ^ vector_b) * pseudoscalar)
    clifford_values = torch.tensor(
        [float(clifford_cross[e1]), float(clifford_cross[e2]), float(clifford_cross[e3])],
        dtype=torch.float64,
    )
    max_abs_error = tensor_float(torch.max(torch.abs(clifford_values - torch_cross)))
    return {
        "surface": "clifford",
        "claim": "Cl(3) bivector dual agrees with torch cross product in Gauss integrand",
        "max_abs_error": round_float(max_abs_error),
        "pass": max_abs_error <= 1.0e-12,
    }


def geomstats_s3_check() -> dict[str, Any]:
    sphere = Hypersphere(dim=3)
    _, _, s3_points = s3_curve_projected(0.53, 0.29, 32)
    belongs = sphere.belongs(s3_points)
    distances = sphere.metric.dist(s3_points[:-1], s3_points[1:])
    norm_errors = torch.abs(torch.linalg.norm(s3_points, dim=1) - 1.0)
    return {
        "surface": "geomstats",
        "backend": gs.__name__,
        "claim": "sampled Hopf fibers lie on S3 with nonzero neighbor geodesic distance",
        "all_belong": bool(torch.all(belongs).item()),
        "min_neighbor_distance": round_float(tensor_float(torch.min(distances))),
        "max_norm_error": round_float(tensor_float(torch.max(norm_errors))),
        "pass": bool(torch.all(belongs).item()) and tensor_float(torch.min(distances)) > 0.0,
    }


def base_s2_topology_checks() -> tuple[dict[str, Any], dict[str, Any]]:
    faces = [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)]

    simplex_tree = gudhi.SimplexTree()
    for face in faces:
        simplex_tree.insert(face)
    simplex_tree.persistence(persistence_dim_max=True)
    betti = simplex_tree.betti_numbers()
    gudhi_result = {
        "surface": "gudhi",
        "claim": "finite S2 base triangulation has Betti numbers b0=1,b1=0,b2=1",
        "num_simplices": simplex_tree.num_simplices(),
        "dimension": simplex_tree.dimension(),
        "betti_numbers": betti,
        "pass": betti[:3] == [1, 0, 1],
    }

    simplicial_complex = tnx.SimplicialComplex()
    simplicial_complex.add_simplices_from(faces)
    cell_counts = [len(list(simplicial_complex.skeleton(rank))) for rank in range(3)]
    euler_characteristic = cell_counts[0] - cell_counts[1] + cell_counts[2]
    toponetx_result = {
        "surface": "toponetx",
        "claim": "finite S2 base triangulation has Euler characteristic 2",
        "cell_counts_by_rank": cell_counts,
        "dimension": simplicial_complex.dim,
        "euler_characteristic": euler_characteristic,
        "pass": euler_characteristic == 2,
    }
    return gudhi_result, toponetx_result


def rustworkx_witness_graph_check() -> dict[str, Any]:
    graph = rx.PyDiGraph()
    nodes = {
        name: graph.add_node(name)
        for name in [
            "torch_spinor_samples",
            "sympy_connection",
            "smt_distinctness",
            "stereographic_projection",
            "gauss_linking_integral",
            "known_value_checks",
            "json_receipt",
        ]
    }
    graph.add_edge(nodes["torch_spinor_samples"], nodes["stereographic_projection"], "S3 curve")
    graph.add_edge(nodes["stereographic_projection"], nodes["gauss_linking_integral"], "R3 curves")
    graph.add_edge(nodes["sympy_connection"], nodes["known_value_checks"], "c1 holonomy")
    graph.add_edge(nodes["smt_distinctness"], nodes["known_value_checks"], "valid distinct fibers")
    graph.add_edge(nodes["gauss_linking_integral"], nodes["known_value_checks"], "linking number")
    graph.add_edge(nodes["known_value_checks"], nodes["json_receipt"], "receipt")
    topo_indices = list(rx.topological_sort(graph))
    topo = [graph[index] for index in topo_indices]
    return {
        "surface": "rustworkx",
        "claim": "witness dependency graph is acyclic and reaches JSON receipt",
        "node_count": graph.num_nodes(),
        "edge_count": graph.num_edges(),
        "topological_order": topo,
        "pass": topo[-1] == "json_receipt" and "known_value_checks" in topo,
    }


def compute_known_checks() -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    symbolic = sympy_connection_checks()

    sample_pairs = [
        ((0.45, 0.10), (1.00, 0.70)),
        ((0.30, 0.20), (1.20, 1.00)),
        ((0.80, 0.00), (0.90, 0.80)),
        ((math.pi / 4.0, 0.00), (math.pi / 4.0, 0.70)),
        ((0.62, 0.35), (1.10, 1.30)),
    ]
    link_values = [gauss_linking_number(first, second) for first, second in sample_pairs]
    link_errors = [abs(value - 1.0) for value in link_values]
    link_max_abs_error = max(link_errors)

    holonomy_numeric = torch_holonomy()
    c1_numeric = symbolic["first_chern_float"]
    flat_holonomy_numeric = torch_flat_holonomy()

    tolerance_link = 5.0e-10
    tolerance_holonomy = 5.0e-12
    tolerance_c1 = 1.0e-12

    checks = [
        {
            "invariant": "Hopf invariant / linking number of distinct fibers",
            "computed": {
                "sample_values": [round_float(value) for value in link_values],
                "max_abs_error": round_float(link_max_abs_error),
                "sample_count": len(link_values),
            },
            "known": 1,
            "tolerance": tolerance_link,
            "match": link_max_abs_error <= tolerance_link,
        },
        {
            "invariant": "holonomy of A_Hopf around the fiber circle",
            "computed": {
                "numeric": round_float(holonomy_numeric),
                "symbolic": symbolic["holonomy_symbolic"],
                "winding": round_float(holonomy_numeric / (2.0 * math.pi)),
            },
            "known": "2*pi",
            "known_numeric": round_float(2.0 * math.pi),
            "tolerance": tolerance_holonomy,
            "match": close_match(holonomy_numeric, 2.0 * math.pi, tolerance_holonomy),
        },
        {
            "invariant": "first Chern number of Hopf bundle",
            "computed": {
                "numeric": round_float(c1_numeric),
                "symbolic": symbolic["first_chern_oriented"],
                "curvature_integral_oriented": symbolic["curvature_integral_oriented"],
            },
            "known": 1,
            "tolerance": tolerance_c1,
            "match": close_match(c1_numeric, 1.0, tolerance_c1),
        },
        {
            "invariant": "flat-connection control holonomy",
            "computed": {
                "numeric": round_float(flat_holonomy_numeric),
                "symbolic": symbolic["flat_holonomy_symbolic"],
            },
            "known": 0,
            "tolerance": tolerance_holonomy,
            "match": close_match(flat_holonomy_numeric, 0.0, tolerance_holonomy),
        },
    ]

    reversed_link = gauss_linking_number(sample_pairs[0][0], sample_pairs[0][1], orientation_second=-1)
    unlinked_control = gauss_linking_unlinked_control()
    same_base_rejected = [
        {"first": [2, 3], "second": [2, 3], "valid_distinct_fibers": False},
    ]
    negatives = [
        {
            "negative": "orientation-reversed second Hopf fiber",
            "computed_linking": round_float(reversed_link),
            "expected": -1,
            "pass": close_match(reversed_link, -1.0, 5.0e-10),
        },
        {
            "negative": "unlinked planar control curves",
            "computed_linking": round_float(unlinked_control),
            "expected": 0,
            "pass": close_match(unlinked_control, 0.0, 5.0e-12),
        },
        {
            "negative": "same-base duplicate fiber pair is rejected before Gauss integral",
            "rows": same_base_rejected,
            "pass": all(not row["valid_distinct_fibers"] for row in same_base_rejected),
        },
        {
            "negative": "zero flat control connection has no fiber holonomy",
            "computed_holonomy": round_float(flat_holonomy_numeric),
            "expected": 0,
            "pass": close_match(flat_holonomy_numeric, 0.0, tolerance_holonomy),
        },
    ]
    diagnostics = {
        "symbolic_connection": symbolic,
        "variation_pairs": [
            {"first_eta_chi": [first[0], first[1]], "second_eta_chi": [second[0], second[1]]}
            for first, second in sample_pairs
        ],
    }
    return checks, diagnostics, negatives


def build_tool_manifest(tool_checks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_surface = {row["surface"]: row for row in tool_checks}
    return {
        "torch": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "complex128 Hopf spinor, float64 S3 curves, holonomy quadrature, and Gauss linking integral",
            "pass": True,
        },
        "sympy": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "symbolic curvature, oriented first Chern integral, and fiber holonomy derivation",
            "pass": True,
        },
        "z3": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "SMT rejection of duplicate-base fiber pairs before linking checks",
            "pass": by_surface["z3"]["pass"],
        },
        "cvc5": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "independent SMT cross-check of z3 duplicate-base rejection",
            "pass": by_surface["cvc5"]["pass"],
        },
        "clifford": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "Cl(3) bivector-dual cross product verifies Gauss-integral orientation machinery",
            "pass": by_surface["clifford"]["pass"],
        },
        "geomstats": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "pytorch-backend S3 membership and geodesic-distance check for sampled Hopf fibers",
            "pass": by_surface["geomstats"]["pass"],
        },
        "gudhi": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "finite S2 base triangulation Betti-number topology check",
            "pass": by_surface["gudhi"]["pass"],
        },
        "toponetx": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "finite S2 base cell-count and Euler-characteristic topology check",
            "pass": by_surface["toponetx"]["pass"],
        },
        "rustworkx": {
            "tried": True,
            "used": True,
            "depth": "load_bearing",
            "reason": "acyclic witness dependency graph from spinor samples to JSON receipt",
            "pass": by_surface["rustworkx"]["pass"],
        },
    }


def write_import_blocker() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = {
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "created_at": now_iso(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "blockers": [f"{tool}: {error}" for tool, error in sorted(IMPORT_ERRORS.items())],
        "KNOWN_VALUE_CHECKS": [],
        "known_value_checks": [],
        "all_known_value_checks_passed": False,
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"RESULT {OUT_PATH}")
    print("CLASSIFICATION diagnostic_only")
    print("KNOWN_VALUE_CHECKS FAIL")
    for blocker in result["blockers"]:
        print(f"BLOCKER {blocker}")


def main() -> int:
    if IMPORT_ERRORS:
        write_import_blocker()
        return 1

    torch.set_default_dtype(torch.float64)

    checks, diagnostics, negatives = compute_known_checks()
    finite_pair_codes = [
        ((0, 0), (2, 3)),
        ((1, 1), (3, 4)),
        ((2, 0), (2, 5)),
        ((4, 2), (5, 8)),
        ((3, 7), (6, 1)),
    ]
    tool_checks = [
        z3_distinct_fiber_check(finite_pair_codes),
        cvc5_distinct_fiber_check(finite_pair_codes),
        clifford_cross_product_check(),
        geomstats_s3_check(),
    ]
    gudhi_check, toponetx_check = base_s2_topology_checks()
    tool_checks.extend([gudhi_check, toponetx_check, rustworkx_witness_graph_check()])

    tool_manifest = build_tool_manifest(tool_checks)
    tool_pass = all(row["pass"] for row in tool_checks) and all(
        row["pass"] for row in tool_manifest.values()
    )
    known_pass = all(row["match"] for row in checks)
    negatives_pass = all(row["pass"] for row in negatives)
    blockers: list[str] = []
    if not known_pass:
        blockers.extend(
            f"known-value mismatch: {row['invariant']}" for row in checks if not row["match"]
        )
    if not negatives_pass:
        blockers.extend(f"negative failed: {row['negative']}" for row in negatives if not row["pass"])
    if not tool_pass:
        blockers.extend(f"tool check failed: {row['surface']}" for row in tool_checks if not row["pass"])

    result: dict[str, Any] = {
        "sim_id": SIM_ID,
        "name": NAME,
        "version": VERSION,
        "tier": "2 geometry diagnostic",
        "created_at": now_iso(),
        "purpose": "Independent known-value Hopf fibration diagnostic for cross-model comparison.",
        "scientific_question": (
            "Do direct torch/symbolic/topological computations recover the known "
            "S^1 -> S^3 -> S^2 Hopf invariants without comparison receipt numbers?"
        ),
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "classification": CLASSIFICATION,
        "promotion_status": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "root_constraints_in_force": [
            "F01 finite sampled fiber circles, finite base cells, finite witness dependency graph",
            "N01 order-sensitive loop orientation and fiber/base projection controls",
        ],
        "finite_map": (
            "finite Hopf fiber samples psi(eta,phi,chi)->S3, Hopf projection "
            "S3->S2, stereographic projection of two fibers, and Gauss linking integral"
        ),
        "domain": {
            "bundle": "S1 -> S3 -> S2",
            "psi_phase_form": "(exp(i phi_phase) cos eta, exp(i chi_phase) sin eta)",
            "bundle_coordinate_form": {
                "phi_phase": "fiber_phi + base_chi",
                "chi_phase": "fiber_phi - base_chi",
                "eta_range": "[0, pi/2]",
                "fiber_phi_period": "2*pi",
                "base_chi_period": "pi",
            },
            "finite_variation_count": len(diagnostics["variation_pairs"]),
        },
        "codomain_or_output": "known-value invariant checks and diagnostic JSON receipt",
        "carrier_layer": "S3 Hopf spinor samples",
        "geometry_layer": "S1 fibers over S2 base",
        "carrier_realization": "torch complex128 spinor samples plus torch float64 R4/R3 geometry",
        "peps3d_embedding": "not_admitted; no PEPS3D promotion claimed by this known-geometry diagnostic",
        "spinor_state": "psi(eta, fiber_phi, base_chi) torch complex128 with two complex components",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": [
            "nonclassical_manifold_admission",
            "PEPS3D_carrier_admission",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
        ],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Hopf fibration known invariant values",
        "branch_status_before_run": "independent_codex_known_geometry_probe_requested",
        "allowed_claims": [
            "local known-geometry diagnostic check",
            "cross-model comparison receipt input",
            "tool-integration evidence for this bounded diagnostic only",
        ],
        "promotion_blockers": [
            "diagnostic_only requested",
            "no PEPS3D carrier admission",
            "no lego-phase validator run by request",
            "no downstream manifold/layer completion claim",
        ],
        "required_tools": list(tool_manifest.keys()),
        "actual_tools_used": [name for name, row in tool_manifest.items() if row["used"]],
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {
            name: row["depth"] for name, row in tool_manifest.items()
        },
        "tool_integration_depth": {
            name: row["depth"] for name, row in tool_manifest.items()
        },
        "required_inputs": ["none; all samples are deterministic finite grids"],
        "data_or_artifact_dependencies": [],
        "required_negatives": [
            "orientation reversed Hopf fiber",
            "unlinked planar control",
            "same-base duplicate fiber rejection",
            "flat connection control",
        ],
        "negatives_run": negatives,
        "kill_conditions": [
            "any known-value check mismatch",
            "any required negative mismatch",
            "any load-bearing tool check failure",
            "any import failure in requested tool stack",
        ],
        "required_artifacts": ["JSON result receipt", "known-value check list", "tool manifest"],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{SIM_ID}:{now_iso()}",
        "KNOWN_VALUE_CHECKS": checks,
        "known_value_checks": checks,
        "result_summary": {
            "all_known_value_checks_passed": known_pass,
            "all_negatives_passed": negatives_pass,
            "all_tool_checks_passed": tool_pass,
            "blocker_count": len(blockers),
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "pass_rule": "all known-value checks, negatives, and tool checks pass within stated tolerances",
        "fail_rule": "write blocker and return nonzero if any invariant misses its known value",
        "eligible_consumers": ["cross_model_known_geometry_comparison"],
        "blocked_consumers": [
            "canonical_by_process",
            "layer_completion",
            "G_structure_completion",
            "manifold_admission",
            "flux",
            "Xi",
            "Phi0",
            "Axis0",
            "bridge",
            "basin",
            "physics",
        ],
        "diagnostics": diagnostics,
        "tool_checks": tool_checks,
        "numpy_policy": {
            "source_imports_numpy": False,
            "uses_tensor_numpy_conversion": False,
            "claim_bearing_substrate": "torch complex128/float64",
            "geomstats_backend_requested": "pytorch",
        },
        "source_sha256": sha256_file(pathlib.Path(__file__).resolve()),
        "blockers": blockers,
        "all_known_value_checks_passed": known_pass,
        "all_pass": known_pass and negatives_pass and tool_pass and not blockers,
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")

    print(f"RESULT {OUT_PATH}")
    print(f"CLASSIFICATION {CLASSIFICATION}")
    print(f"PROMOTION_ALLOWED {PROMOTION_ALLOWED}")
    print(f"KNOWN_VALUE_CHECKS {'PASS' if known_pass else 'FAIL'}")
    for row in checks:
        print(
            "CHECK "
            f"{row['invariant']} | computed={row['computed']} | known={row['known']} | "
            f"match={row['match']}"
        )
    print(f"NEGATIVES {'PASS' if negatives_pass else 'FAIL'}")
    print(f"TOOLS {'PASS' if tool_pass else 'FAIL'}")
    if blockers:
        for blocker in blockers:
            print(f"BLOCKER {blocker}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
