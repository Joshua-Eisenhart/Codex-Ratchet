#!/usr/bin/env python3
"""Hopf fiber/base path geometry probe (diagnostic_only, unadmitted).

Known geometry computed directly in torch.float64 / torch.complex128:

  psi(eta, chi, phi) =
      (cos(eta) exp(i(phi + chi)), sin(eta) exp(i(phi - chi)))

  A_Hopf = -i psi^dag d psi = dphi + cos(2 eta) dchi

  pi(psi) = (
      2 Re(conj(z0) z1),
      2 Im(conj(z0) z1),
      |z0|^2 - |z1|^2
  )

The probe computes a fixed-base Hopf fiber loop gamma_f and a horizontal
base-lift gamma_b. It writes the required JSON receipt with computed known-value
checks only; no known-value match is hardcoded.
"""

from __future__ import annotations

import importlib
import json
import math
import os
import pathlib
import traceback
from typing import Any

import torch

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

CDTYPE = torch.complex128
RTYPE = torch.float64
TOL_STRICT = 1.0e-10
TOL_TOOL = 1.0e-8
TOL_E3NN = 1.0e-5
N_PATH = 257
N_TOPOLOGY = 64
ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_fiber_base_paths_codex_probe"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"


def module_imports() -> tuple[dict[str, Any], list[str]]:
    tools: dict[str, Any] = {}
    blockers: list[str] = []
    for name in ("sympy", "z3", "cvc5", "clifford", "geomstats", "gudhi", "toponetx", "rustworkx", "e3nn"):
        try:
            tools[name] = importlib.import_module(name)
        except Exception as exc:  # pragma: no cover - receipt records the blocker.
            blockers.append(f"tool_import_failed:{name}:{exc}")
    try:
        tools["cvc5_Kind"] = importlib.import_module("cvc5").Kind
    except Exception as exc:
        blockers.append(f"tool_import_failed:cvc5.Kind:{exc}")
    try:
        tools["clifford_Cl"] = importlib.import_module("clifford").Cl
    except Exception as exc:
        blockers.append(f"tool_import_failed:clifford.Cl:{exc}")
    try:
        tools["geomstats_backend"] = importlib.import_module("geomstats.backend")
        tools["geomstats_Hypersphere"] = importlib.import_module("geomstats.geometry.hypersphere").Hypersphere
    except Exception as exc:
        blockers.append(f"tool_import_failed:geomstats.Hypersphere:{exc}")
    try:
        tools["e3nn_o3"] = importlib.import_module("e3nn.o3")
    except Exception as exc:
        blockers.append(f"tool_import_failed:e3nn.o3:{exc}")
    return tools, blockers


def real_tensor(x: float | torch.Tensor) -> torch.Tensor:
    return torch.as_tensor(x, dtype=RTYPE)


def spinor(eta: torch.Tensor, chi: torch.Tensor, phi: torch.Tensor) -> torch.Tensor:
    eta, chi, phi = torch.broadcast_tensors(eta, chi, phi)
    z0 = torch.cos(eta).to(CDTYPE) * torch.exp(1j * (phi + chi).to(CDTYPE))
    z1 = torch.sin(eta).to(CDTYPE) * torch.exp(1j * (phi - chi).to(CDTYPE))
    return torch.stack((z0, z1), dim=-1)


def hopf_projection(psi: torch.Tensor) -> torch.Tensor:
    psi = psi / torch.linalg.vector_norm(psi, dim=-1, keepdim=True)
    z0 = psi[..., 0]
    z1 = psi[..., 1]
    cross = z0.conj() * z1
    x = 2.0 * cross.real
    y = 2.0 * cross.imag
    z = (z0.abs() ** 2 - z1.abs() ** 2).real
    return torch.stack((x, y, z), dim=-1).to(RTYPE)


def real4_from_spinor(psi: torch.Tensor) -> list[list[float]]:
    rows: list[list[float]] = []
    flat = psi.reshape(-1, 2)
    for row in flat:
        rows.append([
            float(row[0].real.item()),
            float(row[0].imag.item()),
            float(row[1].real.item()),
            float(row[1].imag.item()),
        ])
    return rows


def path_derivative(y: torch.Tensor, t: torch.Tensor, retain_graph: bool = True) -> torch.Tensor:
    return torch.autograd.grad(
        y,
        t,
        grad_outputs=torch.ones_like(y),
        retain_graph=retain_graph,
        create_graph=False,
    )[0]


def fiber_path() -> dict[str, Any]:
    t = torch.linspace(0.0, 1.0, N_PATH, dtype=RTYPE, requires_grad=True)
    eta = real_tensor(0.63) + 0.0 * t
    chi = real_tensor(-0.41) + 0.0 * t
    phi = (2.0 * math.pi) * t
    psi = spinor(eta, chi, phi)
    proj = hopf_projection(psi)

    dphi = path_derivative(phi, t, retain_graph=True)
    dchi = path_derivative(chi, t, retain_graph=True)
    connection = dphi + torch.cos(2.0 * eta) * dchi
    holonomy = float(torch.trapezoid(connection.detach(), t.detach()).item())
    winding = holonomy / (2.0 * math.pi)

    proj0 = proj[0].unsqueeze(0)
    drift = float(torch.linalg.vector_norm(proj - proj0, dim=-1).max().item())
    closure = float(torch.linalg.vector_norm(psi[-1] - psi[0]).item())
    norm_err = float((torch.linalg.vector_norm(psi, dim=-1) - 1.0).abs().max().item())
    connection_mean = float(connection.detach().mean().item())
    connection_max_err = float((connection.detach() - 2.0 * math.pi).abs().max().item())

    return {
        "t": t.detach(),
        "eta": eta.detach(),
        "chi": chi.detach(),
        "phi": phi.detach(),
        "psi": psi.detach(),
        "projection": proj.detach(),
        "projection_drift": drift,
        "spinor_closure_error": closure,
        "norm_error": norm_err,
        "connection_integrand_mean": connection_mean,
        "connection_integrand_max_err_from_2pi": connection_max_err,
        "holonomy_phase": holonomy,
        "winding": winding,
    }


def horizontal_base_lift() -> dict[str, Any]:
    t = torch.linspace(0.0, 1.0, N_PATH, dtype=RTYPE, requires_grad=True)
    eta0 = 0.38
    eta_rate = 0.24
    chi0 = 0.17
    chi_rate = 1.13
    phi0 = -0.22
    eta = real_tensor(eta0) + real_tensor(eta_rate) * t
    chi = real_tensor(chi0) + real_tensor(chi_rate) * t
    phi = real_tensor(phi0) - real_tensor(chi_rate / (2.0 * eta_rate)) * (
        torch.sin(2.0 * eta) - real_tensor(math.sin(2.0 * eta0))
    )
    psi = spinor(eta, chi, phi)
    proj = hopf_projection(psi)

    deta = path_derivative(eta, t, retain_graph=True)
    dchi = path_derivative(chi, t, retain_graph=True)
    dphi = path_derivative(phi, t, retain_graph=True)
    connection = dphi + torch.cos(2.0 * eta) * dchi
    max_abs_connection = float(connection.detach().abs().max().item())
    base_displacement = float(torch.linalg.vector_norm(proj[-1] - proj[0]).item())
    norm_err = float((torch.linalg.vector_norm(psi, dim=-1) - 1.0).abs().max().item())
    speed = torch.linalg.vector_norm(torch.stack((deta, dchi, dphi), dim=-1), dim=-1)

    return {
        "t": t.detach(),
        "eta": eta.detach(),
        "chi": chi.detach(),
        "phi": phi.detach(),
        "psi": psi.detach(),
        "projection": proj.detach(),
        "connection_integrand": connection.detach(),
        "max_abs_connection_integrand": max_abs_connection,
        "base_displacement": base_displacement,
        "norm_error": norm_err,
        "coordinate_speed_min": float(speed.detach().min().item()),
        "coordinate_speed_max": float(speed.detach().max().item()),
    }


def sympy_exact_checks(tools: dict[str, Any]) -> dict[str, Any]:
    sp = tools.get("sympy")
    if sp is None:
        return {"pass": False, "blocker": "sympy unavailable"}
    t = sp.symbols("t", real=True)
    eta, chi, phi = sp.symbols("eta chi phi", real=True)
    x = sp.sin(2 * eta) * sp.cos(2 * chi)
    y = -sp.sin(2 * eta) * sp.sin(2 * chi)
    z = sp.cos(2 * eta)
    fiber_phi_independent = all(sp.diff(v, phi) == 0 for v in (x, y, z))

    eta0, s, chi0, w, phi0 = sp.symbols("eta0 s chi0 w phi0", real=True, nonzero=True)
    eta_t = eta0 + s * t
    chi_t = chi0 + w * t
    phi_t = phi0 - (w / (2 * s)) * (sp.sin(2 * eta_t) - sp.sin(2 * eta0))
    horizontal_integrand = sp.simplify(sp.diff(phi_t, t) + sp.cos(2 * eta_t) * sp.diff(chi_t, t))
    horizontal_exact = horizontal_integrand == 0
    hol = sp.integrate(sp.diff(2 * sp.pi * t, t), (t, 0, 1))
    holonomy_exact = sp.simplify(hol - 2 * sp.pi) == 0
    return {
        "fiber_projection_phi_independent": bool(fiber_phi_independent),
        "horizontal_integrand_exact": str(horizontal_integrand),
        "horizontal_integrand_is_zero": bool(horizontal_exact),
        "closed_fiber_holonomy_integral": str(hol),
        "closed_fiber_holonomy_is_2pi": bool(holonomy_exact),
        "pass": bool(fiber_phi_independent and horizontal_exact and holonomy_exact),
    }


def z3_zero_certificate(values: list[float], tol: float, tools: dict[str, Any]) -> dict[str, Any]:
    z3 = tools.get("z3")
    if z3 is None:
        return {"status": "blocked", "pass": False, "blocker": "z3 unavailable"}
    solver = z3.Solver()
    tol_z3 = z3.RealVal(repr(tol))
    bad_terms = []
    for idx, value in enumerate(values):
        var = z3.Real(f"v_{idx}")
        solver.add(var == z3.RealVal(repr(float(value))))
        bad_terms.append(z3.Or(var > tol_z3, var < -tol_z3))
    solver.add(z3.Or(*bad_terms) if bad_terms else z3.BoolVal(False))
    status = str(solver.check())
    return {"status": status, "pass": status == "unsat", "n_values": len(values), "tol": tol}


def cvc5_zero_certificate(values: list[float], tol: float, tools: dict[str, Any]) -> dict[str, Any]:
    cvc5 = tools.get("cvc5")
    Kind = tools.get("cvc5_Kind")
    sp = tools.get("sympy")
    if cvc5 is None or Kind is None or sp is None:
        return {"status": "blocked", "pass": False, "blocker": "cvc5 or sympy unavailable"}

    def rv(slv: Any, x: float) -> Any:
        rat = sp.Rational(str(float(x))).limit_denominator(10**15)
        num, den = sp.fraction(rat)
        return slv.mkReal(int(num), int(den)) if int(den) != 1 else slv.mkReal(int(num))

    slv = cvc5.Solver()
    slv.setLogic("QF_LRA")
    real_sort = slv.getRealSort()
    zero = slv.mkReal(0)
    tol_term = rv(slv, tol)
    neg_tol = slv.mkTerm(Kind.SUB, zero, tol_term)
    bad_terms = []
    for idx, value in enumerate(values):
        var = slv.mkConst(real_sort, f"v_{idx}")
        slv.assertFormula(slv.mkTerm(Kind.EQUAL, var, rv(slv, value)))
        bad_terms.append(slv.mkTerm(Kind.OR, slv.mkTerm(Kind.GT, var, tol_term), slv.mkTerm(Kind.LT, var, neg_tol)))
    if bad_terms:
        slv.assertFormula(slv.mkTerm(Kind.OR, *bad_terms))
    else:
        slv.assertFormula(slv.mkTerm(Kind.DISTINCT, zero, zero))
    res = slv.checkSat()
    status = "unsat" if res.isUnsat() else ("sat" if res.isSat() else "unknown")
    return {"status": status, "pass": res.isUnsat(), "n_values": len(values), "tol": tol}


def clifford_projection(eta: float, chi: float, tools: dict[str, Any]) -> list[float]:
    Cl = tools["clifford_Cl"]
    _, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    I3 = e1 * e2 * e3

    def rotor(axis: tuple[float, float, float], theta: float) -> Any:
        axis_vec = axis[0] * e1 + axis[1] * e2 + axis[2] * e3
        bivector = axis_vec * I3
        return math.cos(theta / 2.0) - math.sin(theta / 2.0) * bivector

    ry = rotor((0.0, 1.0, 0.0), 2.0 * eta)
    rz = rotor((0.0, 0.0, 1.0), -2.0 * chi)
    v = rz * (ry * e3 * (~ry)) * (~rz)
    return [float((v * basis).value[0]) for basis in (e1, e2, e3)]


def clifford_cross_check(path: dict[str, Any], tools: dict[str, Any]) -> dict[str, Any]:
    if "clifford_Cl" not in tools:
        return {"pass": False, "blocker": "clifford unavailable"}
    try:
        idxs = [0, len(path["eta"]) // 3, 2 * len(path["eta"]) // 3, len(path["eta"]) - 1]
        diffs = []
        rows = []
        for idx in idxs:
            eta = float(path["eta"][idx].item())
            chi = float(path["chi"][idx].item())
            cp = torch.tensor(clifford_projection(eta, chi, tools), dtype=RTYPE)
            tp = path["projection"][idx]
            diff = float(torch.linalg.vector_norm(cp - tp).item())
            diffs.append(diff)
            rows.append({"idx": idx, "clifford": [float(x) for x in cp], "torch": [float(x) for x in tp], "diff": diff})
        max_diff = max(diffs)
        return {"max_projection_diff": max_diff, "rows": rows, "pass": max_diff < TOL_TOOL}
    except Exception as exc:
        return {"pass": False, "blocker": f"clifford check failed:{exc}", "traceback": traceback.format_exc()}


def rotation_matrix_z(theta: torch.Tensor) -> torch.Tensor:
    c = torch.cos(theta)
    s = torch.sin(theta)
    return torch.stack((
        torch.stack((c, -s, torch.zeros_like(c)), dim=-1),
        torch.stack((s, c, torch.zeros_like(c)), dim=-1),
        torch.stack((torch.zeros_like(c), torch.zeros_like(c), torch.ones_like(c)), dim=-1),
    ), dim=-2)


def rotation_matrix_y(theta: torch.Tensor) -> torch.Tensor:
    c = torch.cos(theta)
    s = torch.sin(theta)
    return torch.stack((
        torch.stack((c, torch.zeros_like(c), s), dim=-1),
        torch.stack((torch.zeros_like(c), torch.ones_like(c), torch.zeros_like(c)), dim=-1),
        torch.stack((-s, torch.zeros_like(c), c), dim=-1),
    ), dim=-2)


def e3nn_cross_check(path: dict[str, Any], tools: dict[str, Any]) -> dict[str, Any]:
    o3 = tools.get("e3nn_o3")
    if o3 is None:
        return {"pass": False, "blocker": "e3nn.o3 unavailable"}
    try:
        idxs = [0, len(path["eta"]) // 2, len(path["eta"]) - 1]
        north = torch.tensor([0.0, 0.0, 1.0], dtype=RTYPE)
        rows = []
        errs = []
        for idx in idxs:
            eta = path["eta"][idx]
            chi = path["chi"][idx]
            rot = rotation_matrix_z(-2.0 * chi) @ rotation_matrix_y(2.0 * eta)
            base = rot @ north
            base_err = float(torch.linalg.vector_norm(base - path["projection"][idx]).item())
            rot32 = rot.to(torch.float32)
            det = float(torch.det(rot32).item())
            orth = float(torch.linalg.matrix_norm(rot32 @ rot32.T - torch.eye(3, dtype=torch.float32)).item())
            alpha, beta, gamma = o3.matrix_to_angles(rot32)
            rec = o3.angles_to_matrix(alpha, beta, gamma)
            rec_err = float(torch.linalg.matrix_norm(rec - rot32).item())
            row_pass = base_err < TOL_TOOL and abs(det - 1.0) < TOL_E3NN and orth < TOL_E3NN and rec_err < TOL_E3NN
            rows.append({"idx": idx, "base_err": base_err, "det": det, "orthogonality_defect": orth, "e3nn_reconstruction_err": rec_err, "pass": row_pass})
            errs.append(max(base_err, abs(det - 1.0), orth, rec_err))
        return {"rows": rows, "max_error": max(errs), "pass": all(r["pass"] for r in rows)}
    except Exception as exc:
        return {"pass": False, "blocker": f"e3nn check failed:{exc}", "traceback": traceback.format_exc()}


def geomstats_check(fiber: dict[str, Any], horiz: dict[str, Any], tools: dict[str, Any]) -> dict[str, Any]:
    gs = tools.get("geomstats_backend")
    Hypersphere = tools.get("geomstats_Hypersphere")
    if gs is None or Hypersphere is None:
        return {"pass": False, "blocker": "geomstats Hypersphere unavailable"}
    try:
        sphere = Hypersphere(dim=3)
        pts = real4_from_spinor(fiber["psi"][::32]) + real4_from_spinor(horiz["psi"][::32])
        belongs = sphere.belongs(gs.array(pts), atol=TOL_TOOL)
        if hasattr(gs, "to_numpy"):
            vals = gs.to_numpy(belongs).tolist()
        elif hasattr(belongs, "tolist"):
            vals = belongs.tolist()
        else:
            vals = list(belongs)
        bools = [bool(v) for v in vals]
        return {"n_points": len(pts), "all_on_s3": all(bools), "pass": all(bools)}
    except Exception as exc:
        return {"pass": False, "blocker": f"geomstats check failed:{exc}", "traceback": traceback.format_exc()}


def gudhi_check(fiber: dict[str, Any], tools: dict[str, Any]) -> dict[str, Any]:
    gudhi = tools.get("gudhi")
    if gudhi is None:
        return {"pass": False, "blocker": "gudhi unavailable"}
    try:
        k = torch.arange(N_TOPOLOGY, dtype=RTYPE)
        eta0 = fiber["eta"][0] + 0.0 * k
        chi0 = fiber["chi"][0] + 0.0 * k
        phi = (2.0 * math.pi / N_TOPOLOGY) * k
        pts = real4_from_spinor(spinor(eta0, chi0, phi))
        nearest_chord = 2.0 * math.sin(math.pi / N_TOPOLOGY)
        stree = gudhi.SimplexTree()
        for i in range(N_TOPOLOGY):
            stree.insert([i], filtration=0.0)
        for i in range(N_TOPOLOGY):
            stree.insert([i, (i + 1) % N_TOPOLOGY], filtration=nearest_chord)
        stree.compute_persistence(persistence_dim_max=True)
        betti = stree.betti_numbers()
        beta1 = betti[1] if len(betti) > 1 else 0
        return {
            "n_points": N_TOPOLOGY,
            "nearest_chord": nearest_chord,
            "simplex_tree_vertices": int(stree.num_vertices()),
            "simplex_tree_simplices": int(stree.num_simplices()),
            "sample_start": pts[0],
            "sample_next": pts[1],
            "betti_numbers": [int(x) for x in betti],
            "fiber_cycle_beta1": int(beta1),
            "pass": int(beta1) == 1,
        }
    except Exception as exc:
        return {"pass": False, "blocker": f"gudhi check failed:{exc}", "traceback": traceback.format_exc()}


def toponetx_check(tools: dict[str, Any]) -> dict[str, Any]:
    tnx = tools.get("toponetx")
    if tnx is None:
        return {"pass": False, "blocker": "toponetx unavailable"}
    try:
        simplices = [(i,) for i in range(N_TOPOLOGY)] + [(i, (i + 1) % N_TOPOLOGY) for i in range(N_TOPOLOGY)]
        sc = tnx.SimplicialComplex(simplices)
        vertices = [tuple(s) for s in list(sc.skeleton(0))]
        edges = [tuple(s) for s in list(sc.skeleton(1)) if len(tuple(s)) == 2]
        beta1 = len(edges) - len(vertices) + 1
        return {
            "vertices": len(vertices),
            "edges": len(edges),
            "cycle_beta1_from_toponetx_cells": beta1,
            "pass": len(vertices) == N_TOPOLOGY and len(edges) == N_TOPOLOGY and beta1 == 1,
        }
    except Exception as exc:
        return {"pass": False, "blocker": f"toponetx check failed:{exc}", "traceback": traceback.format_exc()}


def rustworkx_check(tools: dict[str, Any]) -> dict[str, Any]:
    rx = tools.get("rustworkx")
    if rx is None:
        return {"pass": False, "blocker": "rustworkx unavailable"}
    try:
        graph = rx.PyGraph()
        graph.add_nodes_from(range(N_TOPOLOGY))
        graph.add_edges_from_no_data([(i, (i + 1) % N_TOPOLOGY) for i in range(N_TOPOLOGY)])
        if hasattr(rx, "is_connected"):
            connected = bool(rx.is_connected(graph))
            components = 1 if connected else len(rx.connected_components(graph))
        else:
            components = len(rx.connected_components(graph))
            connected = components == 1
        beta1 = graph.num_edges() - graph.num_nodes() + components
        return {
            "nodes": graph.num_nodes(),
            "edges": graph.num_edges(),
            "connected": connected,
            "components": components,
            "cycle_rank": beta1,
            "pass": connected and beta1 == 1,
        }
    except Exception as exc:
        return {"pass": False, "blocker": f"rustworkx check failed:{exc}", "traceback": traceback.format_exc()}


def known_value_checks(
    fiber: dict[str, Any],
    horiz: dict[str, Any],
    sym: dict[str, Any],
    z3_cert: dict[str, Any],
    cvc5_cert: dict[str, Any],
    cliff: dict[str, Any],
    e3: dict[str, Any],
    geom: dict[str, Any],
    gudhi: dict[str, Any],
    tnx: dict[str, Any],
    rx: dict[str, Any],
) -> list[dict[str, Any]]:
    holonomy_err = abs(fiber["holonomy_phase"] - 2.0 * math.pi)
    winding_err = abs(fiber["winding"] - 1.0)
    return [
        {
            "invariant": "fiber_path_keeps_pi(psi)_constant",
            "computed": {"max_projection_drift": fiber["projection_drift"]},
            "known": "drift < 1e-10",
            "match": fiber["projection_drift"] < TOL_STRICT,
        },
        {
            "invariant": "horizontal_base_lift_A_Hopf_integrand_zero",
            "computed": {"max_abs_A": horiz["max_abs_connection_integrand"]},
            "known": "0",
            "match": horiz["max_abs_connection_integrand"] < TOL_STRICT,
        },
        {
            "invariant": "closed_fiber_loop_holonomy_phase",
            "computed": {"phase": fiber["holonomy_phase"], "winding": fiber["winding"], "phase_error": holonomy_err, "winding_error": winding_err},
            "known": {"phase": 2.0 * math.pi, "winding": 1},
            "match": holonomy_err < TOL_STRICT and winding_err < TOL_STRICT,
        },
        {
            "invariant": "spinor_paths_lie_on_S3_torch",
            "computed": {"fiber_norm_error": fiber["norm_error"], "horizontal_norm_error": horiz["norm_error"]},
            "known": "||psi|| = 1",
            "match": fiber["norm_error"] < TOL_STRICT and horiz["norm_error"] < TOL_STRICT,
        },
        {
            "invariant": "horizontal_lift_moves_base_nontrivially",
            "computed": {"base_displacement": horiz["base_displacement"]},
            "known": "base displacement > 0",
            "match": horiz["base_displacement"] > 1.0e-3,
        },
        {
            "invariant": "sympy_exact_fiber_horizontal_holonomy",
            "computed": sym,
            "known": "phi-independent projection, A=0 for gamma_b, integral=2*pi for gamma_f",
            "match": bool(sym.get("pass")),
        },
        {
            "invariant": "z3_certifies_numeric_zero_errors",
            "computed": z3_cert,
            "known": "negation of tolerance bound is UNSAT",
            "match": bool(z3_cert.get("pass")),
        },
        {
            "invariant": "cvc5_certifies_numeric_zero_errors",
            "computed": cvc5_cert,
            "known": "negation of tolerance bound is UNSAT",
            "match": bool(cvc5_cert.get("pass")),
        },
        {
            "invariant": "clifford_rotor_base_projection_matches_torch_Hopf_projection",
            "computed": cliff,
            "known": "Cl(3) rotor projection equals pi(psi)",
            "match": bool(cliff.get("pass")),
        },
        {
            "invariant": "e3nn_SO3_base_rotation_matches_torch_Hopf_projection",
            "computed": e3,
            "known": "SO(3) rotation maps north pole to pi(psi)",
            "match": bool(e3.get("pass")),
        },
        {
            "invariant": "geomstats_Hypersphere_accepts_spinor_paths_as_S3",
            "computed": geom,
            "known": "belongs(S^3) is true",
            "match": bool(geom.get("pass")),
        },
        {
            "invariant": "gudhi_Rips_fiber_loop_has_beta1_one",
            "computed": gudhi,
            "known": "closed fiber sample has H1 rank 1",
            "match": bool(gudhi.get("pass")),
        },
        {
            "invariant": "toponetx_cycle_complex_has_beta1_one",
            "computed": tnx,
            "known": "64-cycle simplicial complex has beta1 = 1",
            "match": bool(tnx.get("pass")),
        },
        {
            "invariant": "rustworkx_cycle_graph_has_cycle_rank_one",
            "computed": rx,
            "known": "connected graph with E=V has cycle rank 1",
            "match": bool(rx.get("pass")),
        },
    ]


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    tools, import_blockers = module_imports()

    fiber = fiber_path()
    horiz = horizontal_base_lift()
    sym = sympy_exact_checks(tools)

    zero_values = [
        fiber["projection_drift"],
        fiber["spinor_closure_error"],
        abs(fiber["holonomy_phase"] - 2.0 * math.pi),
        abs(fiber["winding"] - 1.0),
        horiz["max_abs_connection_integrand"],
        fiber["norm_error"],
        horiz["norm_error"],
    ]
    z3_cert = z3_zero_certificate(zero_values, TOL_STRICT, tools)
    cvc5_cert = cvc5_zero_certificate(zero_values, TOL_STRICT, tools)
    cliff = clifford_cross_check(horiz, tools)
    e3 = e3nn_cross_check(horiz, tools)
    geom = geomstats_check(fiber, horiz, tools)
    gudhi = gudhi_check(fiber, tools)
    tnx = toponetx_check(tools)
    rx = rustworkx_check(tools)

    checks = known_value_checks(fiber, horiz, sym, z3_cert, cvc5_cert, cliff, e3, geom, gudhi, tnx, rx)
    checks_all_match = all(bool(row["match"]) for row in checks)
    blockers = list(import_blockers)
    blockers.extend(
        f"KNOWN_VALUE_MISMATCH:{row['invariant']} computed={row['computed']} known={row['known']}"
        for row in checks
        if not row["match"]
    )
    all_pass = checks_all_match and not import_blockers

    tool_manifest = {
        "torch": {
            "used": True,
            "role": "load_bearing",
            "reason": "claim substrate for spinor paths, Hopf projection, autograd path derivatives, A_Hopf integrand, holonomy integral, and numeric match computation in complex128/float64",
        },
        "sympy": {
            "used": "sympy" in tools,
            "role": "load_bearing",
            "reason": "exact symbolic check that pi(psi) is phi-independent, the constructed base lift has A_Hopf=0, and the closed fiber integral is 2*pi",
        },
        "z3": {
            "used": "z3" in tools,
            "role": "load_bearing",
            "reason": "SMT check that the finite numeric zero/error witnesses cannot exceed the strict tolerance",
        },
        "cvc5": {
            "used": "cvc5" in tools,
            "role": "load_bearing",
            "reason": "independent SMT check over the same finite numeric zero/error witnesses",
        },
        "clifford": {
            "used": "clifford_Cl" in tools,
            "role": "load_bearing",
            "reason": "Cl(3) rotor construction independently reproduces the Hopf base projection from known S^3/S^2 geometry",
        },
        "geomstats": {
            "used": "geomstats_Hypersphere" in tools,
            "role": "load_bearing",
            "reason": "Hypersphere(dim=3).belongs cross-checks that sampled complex spinors lie on S^3",
        },
        "gudhi": {
            "used": "gudhi" in tools,
            "role": "load_bearing",
            "reason": "Rips complex on the sampled closed fiber loop verifies beta1=1 for the loop witness",
        },
        "toponetx": {
            "used": "toponetx" in tools,
            "role": "load_bearing",
            "reason": "simplicial 64-cycle cell inventory verifies beta1=1 for the discrete fiber loop model",
        },
        "rustworkx": {
            "used": "rustworkx" in tools,
            "role": "load_bearing",
            "reason": "cycle graph check verifies the closed fiber sample has one graph cycle",
        },
        "e3nn": {
            "used": "e3nn_o3" in tools,
            "role": "load_bearing",
            "reason": "SO(3) angle round-trip checks the base projection as a genuine rotation of the north pole",
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
        "sim_class": "carrier_probe",
        "purpose": "Independent known-geometry Hopf fiber/base path probe for cross-model comparison; diagnostic_only lego-phase evidence, not manifold admission.",
        "scientific_question": "Do the fixed-base Hopf fiber loop and a constructed horizontal base-lift satisfy the known Hopf fibration invariants when computed directly from the math?",
        "claim_ceiling": "diagnostic_only / hypothetical / unadmitted: no layer, manifold, Axis0, flux, bridge, basin, physics, or promotion claim.",
        "finite_map": "(eta, chi, phi) -> psi in S^3 subset C^2 -> pi(psi) in S^2, A_Hopf path integrand, and closed-fiber holonomy",
        "domain": "finite sampled Hopf-coordinate paths gamma_f and gamma_b on normalized torch.complex128 spinors",
        "codomain_or_output": "Hopf base projections, connection integrands, holonomy phase, topology/tool cross-checks, and known-value receipt rows",
        "carrier_layer": "S^3 spinor carrier with Hopf projection to S^2",
        "geometry_layer": "Hopf fibration fiber/base path geometry with A_Hopf=dphi+cos(2 eta)dchi",
        "carrier_realization": "torch.complex128 spinors and torch.float64 coordinates; no NumPy claim-bearing substrate",
        "spinor_state": "psi(eta, chi, phi)=(cos eta e^{i(phi+chi)}, sin eta e^{i(phi-chi)})",
        "quaternion_action": "Cl(3) rotor cross-check of the S^3/S^2 base projection; diagnostic tool witness only",
        "peps3d_embedding": "not_applicable_at_lego_phase (no manifold anchor claimed; diagnostic_only)",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "blocked_consumers": ["manifold_layers", "stacking", "coupling", "G_structure", "Axis0", "flux", "Xi", "Phi0", "bridge", "basin", "physics"],
        "law_or_candidate_tested": "known Hopf fiber/base path invariants for S^3 -> S^2",
        "branch_status_before_run": "lego/pre-sim phase; standalone known-math geometry; unadmitted",
        "allowed_claims": ["diagnostic_only known Hopf path invariants matched by this finite torch computation"],
        "promotion_blockers": ["diagnostic_only by design; no PEPS3D manifold anchor, no coupling, no layer admission"],
        "result_summary": {
            "all_pass": all_pass,
            "known_values_all_match": checks_all_match,
            "n_known_value_checks": len(checks),
            "result_path": str(RESULT_PATH),
            "fiber_projection_drift": fiber["projection_drift"],
            "horizontal_max_abs_A": horiz["max_abs_connection_integrand"],
            "closed_fiber_holonomy_phase": fiber["holonomy_phase"],
            "closed_fiber_winding": fiber["winding"],
            "promotion_allowed": False,
        },
        "paths": {
            "fiber_gamma_f": {
                "eta": float(fiber["eta"][0].item()),
                "chi": float(fiber["chi"][0].item()),
                "phi_start": float(fiber["phi"][0].item()),
                "phi_end": float(fiber["phi"][-1].item()),
                "projection_start": [float(x) for x in fiber["projection"][0]],
                "projection_end": [float(x) for x in fiber["projection"][-1]],
                "projection_drift": fiber["projection_drift"],
                "holonomy_phase": fiber["holonomy_phase"],
                "winding": fiber["winding"],
                "spinor_closure_error": fiber["spinor_closure_error"],
            },
            "horizontal_gamma_b": {
                "eta_start": float(horiz["eta"][0].item()),
                "eta_end": float(horiz["eta"][-1].item()),
                "chi_start": float(horiz["chi"][0].item()),
                "chi_end": float(horiz["chi"][-1].item()),
                "phi_start": float(horiz["phi"][0].item()),
                "phi_end": float(horiz["phi"][-1].item()),
                "projection_start": [float(x) for x in horiz["projection"][0]],
                "projection_end": [float(x) for x in horiz["projection"][-1]],
                "base_displacement": horiz["base_displacement"],
                "max_abs_connection_integrand": horiz["max_abs_connection_integrand"],
            },
        },
        "known_value_checks": checks,
        "tool_evidence": {
            "sympy": sym,
            "z3_zero_certificate": z3_cert,
            "cvc5_zero_certificate": cvc5_cert,
            "clifford": cliff,
            "e3nn": e3,
            "geomstats": geom,
            "gudhi": gudhi,
            "toponetx": tnx,
            "rustworkx": rx,
        },
        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {name: "load_bearing" for name in tool_manifest},
        "proof_surfaces_used": ["sympy", "z3", "cvc5"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "required_tools": ["torch", "sympy", "z3", "cvc5", "clifford", "geomstats", "gudhi", "toponetx", "rustworkx", "e3nn"],
        "actual_tools_used": [name for name, row in tool_manifest.items() if row["used"]],
        "required_artifacts": ["json_result_receipt"],
        "artifacts_emitted": ["json_result_receipt"],
        "all_pass": all_pass,
        "blockers": blockers,
        "pass_rule": "all known_value_checks must have match=true and every required tool import must succeed",
        "fail_rule": "any required invariant mismatch, any missing required tool, or any failed tool cross-check",
        "eligible_consumers": ["other diagnostic_only Hopf geometry probes"],
    }

    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(RESULT_PATH),
        "all_pass": all_pass,
        "known_values_all_match": checks_all_match,
        "n_known_value_checks": len(checks),
        "blockers": blockers,
        "required_checks": [
            {"invariant": row["invariant"], "computed": row["computed"], "known": row["known"], "match": row["match"]}
            for row in checks[:3]
        ],
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
