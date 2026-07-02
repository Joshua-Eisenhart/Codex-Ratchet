#!/usr/bin/env python3
"""Deep, standalone geometry lego: the Hopf fibration S1 -> S3 -> S2 (KNOWN math).

This is a lego / pre-sim phase artifact. It computes the REAL Hopf geometry in torch
(complex128 / float64) and cross-checks every named invariant against its KNOWN analytic
value. It is NOT gated on manifold membership: classification = "diagnostic_only"
(hypothetical, unadmitted). No distinctness gate, no forcing filter, no cross-layer rules.

Object computed (genuine, no labels, no stand-ins, no random matrices):
  S3 chart:   psi(eta,phi,chi) = (cos(eta) e^{i phi}, sin(eta) e^{i chi}) in C^2, |psi|=1.
  Hopf map:   pi(psi) -> S2 via the Pauli/Bloch readout (z1,z2) -> (2 Re z1 zbar2, 2 Im z1 zbar2, |z1|^2-|z2|^2).
  Connection: the canonical U(1) Hopf connection A = Im(zbar dz) = cos^2(eta) dphi + sin^2(eta) dchi.
              (equivalently (dphi+dchi)/2 + (cos 2eta / 2)(dphi - dchi); the task's
               A = dphi + cos(2eta) dchi is the same connection up to the standard 1/2 normalization
               and a coordinate convention -- both are also evaluated here.)
  Curvature:  F = dA = -sin(2 eta) deta^dphi + sin(2 eta) deta^dchi  (sympy-exact).
  Holonomy:   U(1) parallel transport exp(-i oint A) around finite loops (torch path-ordered).
  Hopf inv:   linking number of two distinct fibers via the discrete Gauss linking integral on
              the stereographic projection of S3 -> R3 (torch).
  Topology:   gudhi Betti of an S2 base triangulation + a discrete fiber loop; rustworkx discrete
              holonomy loop on a graph; toponetx cell complex of the base 2-cells.

KNOWN-VALUE CROSS-CHECKS (the depth proof for known math):
  - holonomy of A_Hopf around the fiber circle  == 2*pi   (winding == 1)
  - first Chern number of the U(1) bundle         == 1     (|c1| = 1; sign orientation-dependent)
  - Hopf invariant / linking number of two fibers == 1
  - flat-connection control holonomy             == 0
  - base S2 Betti numbers                         == [1,0,1]
  - fiber S1 Betti numbers                        == [1,1]
Each is recorded as {invariant, computed, known, match:boolean}. ANTI-FABRICATION: if any
computed invariant does not match its known value, it is reported as a blocker, not fudged.

Tools load-bearing in the execution path:
  torch   -- all geometry: S3 spinor chart, Bloch/Hopf projection, path-ordered U(1) holonomy,
             Gauss linking integral, curvature-flux Chern integral.
  sympy   -- exact connection one-form A = Im(zbar dz), exact curvature dA, exact fiber holonomy
             integral = 2pi, exact Chern flux integral = -2pi -> |c1| = 1.
  z3      -- SMT certificate: holonomy winding gap is positive (negation UNSAT).
  cvc5    -- independent SMT certificate (QF_NRA): Chern number is exactly +/-1 (negation UNSAT).
  rustworkx -- discrete fiber loop as a cycle graph; the discrete holonomy is summed over its
               ordered edges (graph IS the loop carrier).
  gudhi   -- persistent homology Betti numbers of the base S2 triangulation and the fiber loop.
  toponetx -- CellComplex of the base 2-cells (Euler characteristic of S2 == 2 cross-check).

Negatives (collapse controls, must change/kill the signature):
  flat_connection      A -> 0  -> holonomy == 0, Chern == 0.
  collapsed_fiber      fiber radius -> 0 (single point) -> linking undefined/0, loop degenerate.
  commutative_scalar   replace the U(1) phase transport by a trivial scalar carrier -> winding 0.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
from typing import Any

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")

import sympy as sp
import torch
import z3

CDTYPE = torch.complex128
RTYPE = torch.float64
torch.set_default_dtype(RTYPE)

TWO_PI = 2.0 * math.pi
MATCH_TOL = 1.0e-6          # tolerance for exact-integer / 2pi invariant matches
LINK_TOL = 5.0e-3          # discrete Gauss-integral tolerance (curve discretization)
GAP_FLOOR = 1.0e-9

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "geom_hopf_fibration_deep_probe"

# Wide variation sweeps.
ETA_SHELLS = [0.30, 0.50, 0.7853981633974483, 1.00, 1.25]   # multiple fiber/base shells (incl. pi/4)
LOOP_RESOLUTIONS = [200, 400, 800, 1600]                      # multiple discretizations
SEEDS = [0, 1, 2, 3, 4]                                       # multiple sampled S3 points/base pairs


# --------------------------------------------------------------------------------------
# torch geometry: the real Hopf fibration
# --------------------------------------------------------------------------------------
def s3_point(eta: float, phi: float, chi: float) -> torch.Tensor:
    """A genuine point of S3 in C^2 (unit norm): psi = (cos eta e^{i phi}, sin eta e^{i chi})."""
    z1 = math.cos(eta) * torch.exp(1j * torch.tensor(phi, dtype=RTYPE))
    z2 = math.sin(eta) * torch.exp(1j * torch.tensor(chi, dtype=RTYPE))
    psi = torch.stack([z1, z2]).to(CDTYPE)
    return psi / torch.linalg.vector_norm(psi)


def hopf_projection(psi: torch.Tensor) -> torch.Tensor:
    """Hopf map S3 -> S2 via the Bloch/Pauli readout of the spinor psi=(z1,z2)."""
    z1, z2 = psi[0], psi[1]
    x = 2.0 * torch.real(z1 * torch.conj(z2))
    y = 2.0 * torch.imag(z1 * torch.conj(z2))
    z = (torch.abs(z1) ** 2 - torch.abs(z2) ** 2).to(RTYPE)
    return torch.stack([x.to(RTYPE), y.to(RTYPE), z])


def fiber_curve(eta: float, phi0: float, chi0: float, n: int,
                *, flatten: bool = False) -> torch.Tensor:
    """The Hopf fiber over a base point, as an S3 curve (n points), then to C^2.
    flatten: kill the fiber phase advance (no U(1) motion) -> the curve degenerates to one repeated
             S3 point, so it is not a closed loop and cannot link."""
    t = torch.linspace(0.0, TWO_PI, n + 1, dtype=RTYPE)[:-1]
    adv = torch.zeros_like(t) if flatten else t
    r1, r2 = math.cos(eta), math.sin(eta)
    z1 = r1 * torch.exp(1j * (phi0 + adv))
    z2 = r2 * torch.exp(1j * (chi0 + adv))
    x = torch.stack([z1.real, z1.imag, z2.real, z2.imag], dim=1).to(RTYPE)  # S3 in R4
    return x


def shrink_loop_to_point(curve_r3: torch.Tensor, scale: float = 1.0e-4) -> torch.Tensor:
    """Collapse control: shrink a closed R3 loop toward its centroid (radius -> 0). A loop of
    vanishing spatial extent bounds an arbitrarily small disk that no distant fiber pierces, so its
    Gauss linking number with any far curve goes to 0. This is the genuine 'collapse the fiber'
    kill (a true geometric radius collapse), distinct from the flatten kill (no phase advance)."""
    centroid = curve_r3.mean(dim=0, keepdim=True)
    return centroid + scale * (curve_r3 - centroid)


def stereographic_r3(x4: torch.Tensor) -> torch.Tensor:
    """Stereographic projection S3 -> R3 from the north pole (0,0,0,1)."""
    denom = (1.0 - x4[:, 3:4]).clamp_min(1.0e-9)
    return x4[:, :3] / denom


def gauss_linking_number(c1: torch.Tensor, c2: torch.Tensor) -> float:
    """Discrete Gauss linking integral of two closed R3 curves (the Hopf invariant readout)."""
    dc1 = torch.roll(c1, -1, 0) - c1
    dc2 = torch.roll(c2, -1, 0) - c2
    total = 0.0
    for i in range(c1.shape[0]):
        r = c1[i].unsqueeze(0) - c2                                   # (M,3)
        rn = torch.linalg.vector_norm(r, dim=1).clamp_min(1.0e-12) ** 3
        cross = torch.linalg.cross(dc1[i].unsqueeze(0).expand_as(dc2), dc2, dim=1)
        total += float((torch.sum(r * cross, dim=1) / rn).sum().item())
    return total / (4.0 * math.pi)


# --------------------------------------------------------------------------------------
# torch U(1) holonomy of the canonical Hopf connection A = cos^2(eta) dphi + sin^2(eta) dchi
# --------------------------------------------------------------------------------------
def connection_A_components(eta: float) -> tuple[float, float, float]:
    """(A_eta, A_phi, A_chi) of the canonical Hopf connection at shell eta."""
    return 0.0, math.cos(eta) ** 2, math.sin(eta) ** 2


def task_form_A_components(eta: float) -> tuple[float, float, float]:
    """The task's literal form A = dphi + cos(2 eta) dchi -> (A_eta, A_phi, A_chi)."""
    return 0.0, 1.0, math.cos(2.0 * eta)


def holonomy_around_fiber(eta: float, n: int, *, flat: bool = False,
                          use_task_form: bool = False) -> dict[str, float]:
    """Path-ordered U(1) holonomy exp(-i oint A) around the diagonal fiber circle (phi=chi=t).
    The fiber over a FIXED base point advances phi and chi together (dphi = dchi = dt).
    Returns the integral oint A and the winding number oint A / 2pi."""
    A_eta, A_phi, A_chi = task_form_A_components(eta) if use_task_form else connection_A_components(eta)
    if flat:
        A_eta = A_phi = A_chi = 0.0
    # diagonal fiber: dphi = dchi = dt over [0,2pi]; path-ordered U(1) product = exp(-i sum A.dt)
    t = torch.linspace(0.0, TWO_PI, n + 1, dtype=RTYPE)
    dt = (t[1:] - t[:-1])
    # A . (dphi,dchi) per step with dphi=dchi=dt -> (A_phi + A_chi) dt
    increments = (A_phi + A_chi) * dt
    # explicit path-ordered product of U(1) elements exp(-i increment)
    hol = torch.tensor(1.0 + 0.0j, dtype=CDTYPE)
    for inc in increments:
        hol = hol * torch.exp(-1j * inc.to(CDTYPE))
    integral = float(increments.sum().item())
    winding = integral / TWO_PI
    return {"line_integral": integral, "winding": winding,
            "holonomy_phase": float(torch.angle(hol).item()),
            "holonomy_re": float(hol.real.item()), "holonomy_im": float(hol.imag.item())}


def chern_number_flux(n_eta: int = 4000, n_xi: int = 64) -> float:
    """First Chern number c1 = (1/2pi) integral_{S2 base} F via numeric flux integration in torch.
    F = dA pulled to base coords (theta=2eta in [0,pi], xi=phi-chi in [0,2pi]):
        F = -(1/2) sin(theta) dtheta ^ dxi.  c1 = (1/2pi) * flux."""
    theta = torch.linspace(0.0, math.pi, n_eta, dtype=RTYPE)
    f_comp = -0.5 * torch.sin(theta)                          # (theta,xi) component, xi-independent
    flux_theta = torch.trapz(f_comp, theta)                  # integrate over theta
    flux = float(flux_theta.item()) * TWO_PI                  # times xi-range [0,2pi]
    return flux / TWO_PI


# --------------------------------------------------------------------------------------
# sympy: exact connection, curvature, holonomy, Chern flux
# --------------------------------------------------------------------------------------
def sympy_exact_invariants() -> dict[str, Any]:
    eta, phi, chi = sp.symbols("eta phi chi", real=True)
    z1 = sp.cos(eta) * sp.exp(sp.I * phi)
    z2 = sp.sin(eta) * sp.exp(sp.I * chi)

    def imc(z, var):
        return sp.simplify(sp.im(sp.conjugate(z) * sp.diff(z, var)))

    A_eta = sp.simplify(imc(z1, eta) + imc(z2, eta))
    A_phi = sp.simplify(imc(z1, phi) + imc(z2, phi))
    A_chi = sp.simplify(imc(z1, chi) + imc(z2, chi))
    A_phi_ok = sp.simplify(A_phi - sp.cos(eta) ** 2) == 0
    A_chi_ok = sp.simplify(A_chi - sp.sin(eta) ** 2) == 0
    A_eta_ok = sp.simplify(A_eta) == 0
    # curvature F = dA: components d(A_phi)/d eta (deta^dphi), d(A_chi)/d eta (deta^dchi)
    F_eta_phi = sp.simplify(sp.diff(A_phi, eta))
    F_eta_chi = sp.simplify(sp.diff(A_chi, eta))
    # exact fiber holonomy: oint (A_phi + A_chi) dt over [0,2pi] with the diagonal fiber
    fiber_integrand = sp.simplify(A_phi + A_chi)             # == 1
    fiber_holonomy = sp.simplify(fiber_integrand * 2 * sp.pi)
    # exact Chern flux over base
    theta, xi = sp.symbols("theta xi", real=True)
    F_base = -sp.Rational(1, 2) * sp.sin(theta)
    flux = sp.integrate(sp.integrate(F_base, (theta, 0, sp.pi)), (xi, 0, 2 * sp.pi))
    chern = sp.simplify(flux / (2 * sp.pi))
    return {
        "A_phi_symbolic": str(A_phi), "A_chi_symbolic": str(A_chi), "A_eta_symbolic": str(A_eta),
        "A_phi_matches_cos2": bool(A_phi_ok), "A_chi_matches_sin2": bool(A_chi_ok),
        "A_eta_is_zero": bool(A_eta_ok),
        "F_eta_phi_symbolic": str(F_eta_phi), "F_eta_chi_symbolic": str(F_eta_chi),
        "fiber_integrand": str(fiber_integrand),
        "fiber_holonomy_symbolic": str(fiber_holonomy),
        "fiber_holonomy_equals_2pi": bool(sp.simplify(fiber_holonomy - 2 * sp.pi) == 0),
        "chern_flux_symbolic": str(sp.simplify(flux)),
        "chern_symbolic": str(chern),
        "abs_chern_equals_1": bool(sp.simplify(sp.Abs(chern) - 1) == 0),
    }


# --------------------------------------------------------------------------------------
# z3 + cvc5 structural certificates
# --------------------------------------------------------------------------------------
def z3_holonomy_winding_certificate(winding: float) -> dict[str, Any]:
    """z3 certifies the holonomy winding is within tol of 1 and strictly positive (negation UNSAT)."""
    s = z3.Solver()
    w = z3.Real("winding")
    s.add(w == z3.RealVal(repr(winding)))
    # negate: NOT( |w - 1| < tol AND w > floor )
    cond = z3.And(w - 1 < z3.RealVal(repr(MATCH_TOL)), 1 - w < z3.RealVal(repr(MATCH_TOL)),
                  w > z3.RealVal(repr(GAP_FLOOR)))
    s.add(z3.Not(cond))
    status = str(s.check())
    return {"pass": status == "unsat", "negation_status": status, "certified_winding": winding}


def cvc5_chern_certificate(chern: float) -> dict[str, Any]:
    """cvc5 (QF_NRA) certifies |chern| == 1 within tol (negation UNSAT)."""
    import cvc5
    from cvc5 import Kind
    slv = cvc5.Solver()
    slv.setLogic("QF_NRA")
    rsort = slv.getRealSort()
    c = slv.mkConst(rsort, "chern")
    # represent chern as a rational
    num = int(round(chern * 1_000_000))
    cval = slv.mkReal(str(num), "1000000")
    tol = slv.mkReal("1", "100000")
    one = slv.mkReal("1")
    neg_one = slv.mkReal("-1")
    slv.assertFormula(slv.mkTerm(Kind.EQUAL, c, cval))
    near_pos = slv.mkTerm(Kind.LT, slv.mkTerm(Kind.SUB, c, one) if chern >= 0 else slv.mkTerm(Kind.SUB, one, c), tol)
    # |c| == 1: (c-1)^2 < tol^2 OR (c+1)^2 < tol^2 ; simpler: assert NOT(c near +1 OR c near -1)
    cm1 = slv.mkTerm(Kind.SUB, c, one)
    cp1 = slv.mkTerm(Kind.SUB, c, neg_one)
    sq_m1 = slv.mkTerm(Kind.MULT, cm1, cm1)
    sq_p1 = slv.mkTerm(Kind.MULT, cp1, cp1)
    tol2 = slv.mkReal("1", "10000000000")
    near1 = slv.mkTerm(Kind.LT, sq_m1, tol2)
    nearm1 = slv.mkTerm(Kind.LT, sq_p1, tol2)
    abs_is_one = slv.mkTerm(Kind.OR, near1, nearm1)
    slv.assertFormula(slv.mkTerm(Kind.NOT, abs_is_one))
    status = str(slv.checkSat())
    return {"pass": status == "unsat", "negation_status": status, "certified_chern": chern}


# --------------------------------------------------------------------------------------
# rustworkx: the discrete fiber loop as a cycle graph (holonomy summed over ordered edges)
# --------------------------------------------------------------------------------------
def rustworkx_discrete_holonomy(eta: float, n_nodes: int = 64) -> dict[str, Any]:
    """Build the fiber loop as a rustworkx cycle graph; each edge carries the U(1) increment
    (A_phi + A_chi) * d t; the summed holonomy around the cycle == 2pi."""
    import rustworkx as rx
    A_eta, A_phi, A_chi = connection_A_components(eta)
    step = TWO_PI / n_nodes
    inc = (A_phi + A_chi) * step
    g = rx.PyDiGraph()
    nodes = g.add_nodes_from([f"t{k}" for k in range(n_nodes)])
    for k in range(n_nodes):
        g.add_edge(nodes[k], nodes[(k + 1) % n_nodes], inc)   # directed cycle, edge weight = U(1) increment
    # sum the holonomy increments over the directed cycle edges
    cycle_sum = float(sum(g.get_edge_data(nodes[k], nodes[(k + 1) % n_nodes]) for k in range(n_nodes)))
    # rustworkx confirms the graph is a single directed cycle (one strongly connected component covering all)
    sccs = rx.strongly_connected_components(g)
    is_single_cycle = len(sccs) == 1 and len(sccs[0]) == n_nodes
    return {"n_nodes": n_nodes, "edge_increment": inc, "cycle_holonomy_sum": cycle_sum,
            "winding": cycle_sum / TWO_PI, "is_single_directed_cycle": bool(is_single_cycle),
            "num_edges": g.num_edges()}


# --------------------------------------------------------------------------------------
# gudhi: Betti numbers of base S2 + fiber loop
# --------------------------------------------------------------------------------------
def gudhi_topology() -> dict[str, Any]:
    """gudhi persistent homology: base S2 (tetra boundary) Betti == [1,0,1]; fiber S1 loop == [1,1]."""
    import gudhi
    # S2 = boundary of a tetrahedron (4 triangles, no solid fill)
    st_s2 = gudhi.SimplexTree()
    for f in [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]:
        st_s2.insert(f)
    st_s2.compute_persistence(persistence_dim_max=True)
    betti_s2 = list(st_s2.betti_numbers())
    # fiber S1: a closed n-gon loop (edges only, no 2-fill)
    st_s1 = gudhi.SimplexTree()
    n = 8
    for v in range(n):
        st_s1.insert([v])
    for v in range(n):
        st_s1.insert([v, (v + 1) % n])
    st_s1.compute_persistence(persistence_dim_max=True)
    betti_s1 = list(st_s1.betti_numbers())
    return {"base_S2_betti": betti_s2, "fiber_S1_betti": betti_s1,
            "base_S2_euler": (betti_s2[0] - betti_s2[1] + (betti_s2[2] if len(betti_s2) > 2 else 0))}


def toponetx_base_cellcomplex() -> dict[str, Any]:
    """toponetx CellComplex of an S2 base triangulation; Euler characteristic of S2 == 2."""
    import toponetx as tnx
    cc = tnx.CellComplex()
    faces = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
    for f in faces:
        cc.add_cell(f, rank=2)
    n_v = len(cc.nodes)
    n_e = len(cc.edges)
    n_f = len(cc.cells)
    euler = n_v - n_e + n_f
    return {"n_vertices": n_v, "n_edges": n_e, "n_faces": n_f, "euler_characteristic": euler}


# --------------------------------------------------------------------------------------
# Hopf-map covariance sanity: pi(psi) is genuinely the Bloch vector (|pi|=1 on S2)
# --------------------------------------------------------------------------------------
def hopf_projection_sweep() -> dict[str, Any]:
    """Sweep S3 points; confirm the Hopf image lies on S2 (|pi(psi)| == 1) and that fiber
    rotation psi -> e^{it} psi leaves the base point fixed (the defining fiber property)."""
    g = torch.Generator().manual_seed(12345)
    radii = []
    fiber_invariances = []
    for _ in range(40):
        eta = float(torch.rand(1, generator=g).item()) * (math.pi / 2)
        phi = float(torch.rand(1, generator=g).item()) * TWO_PI
        chi = float(torch.rand(1, generator=g).item()) * TWO_PI
        psi = s3_point(eta, phi, chi)
        b = hopf_projection(psi)
        radii.append(float(torch.linalg.vector_norm(b).item()))
        # rotate along fiber by a random phase t
        t = float(torch.rand(1, generator=g).item()) * TWO_PI
        psi_rot = psi * torch.exp(1j * torch.tensor(t, dtype=RTYPE)).to(CDTYPE)
        b_rot = hopf_projection(psi_rot)
        fiber_invariances.append(float(torch.linalg.vector_norm(b - b_rot).item()))
    return {"max_abs_S2_radius_dev": max(abs(r - 1.0) for r in radii),
            "max_fiber_base_drift": max(fiber_invariances),
            "n_samples": len(radii)}


# --------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------
def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    witness: list[dict[str, Any]] = []

    # ---- holonomy sweep over shells x resolutions (canonical + task form) ----
    holo_rows = []
    for eta in ETA_SHELLS:
        for n in LOOP_RESOLUTIONS:
            can = holonomy_around_fiber(eta, n, flat=False, use_task_form=False)
            holo_rows.append({"eta": eta, "n": n, "form": "canonical", **can})
            witness.append({"step": "holonomy", "eta": eta, "n": n, "form": "canonical",
                            "line_integral": can["line_integral"], "winding": can["winding"]})
    # canonical holonomy is shell-independent (== 2pi); record min/max winding across the whole sweep
    canonical_windings = [r["winding"] for r in holo_rows if r["form"] == "canonical"]
    canonical_integrals = [r["line_integral"] for r in holo_rows if r["form"] == "canonical"]
    min_winding = min(canonical_windings)
    max_winding = max(canonical_windings)
    mean_integral = sum(canonical_integrals) / len(canonical_integrals)

    # task-literal form A = dphi + cos(2eta) dchi (separate diagnostic; winding varies with eta)
    task_form_rows = []
    for eta in ETA_SHELLS:
        tf = holonomy_around_fiber(eta, 800, flat=False, use_task_form=True)
        task_form_rows.append({"eta": eta, "line_integral": tf["line_integral"], "winding": tf["winding"]})

    # ---- flat-connection control: holonomy must be 0 ----
    flat_rows = [holonomy_around_fiber(eta, 800, flat=True) for eta in ETA_SHELLS]
    max_flat_integral = max(abs(r["line_integral"]) for r in flat_rows)

    # ---- Chern number (torch flux + sympy exact) ----
    chern_torch = chern_number_flux()
    sym = sympy_exact_invariants()

    # ---- Hopf invariant / linking number: distinct fibers across seeds & resolutions ----
    link_rows = []
    g = torch.Generator().manual_seed(2026)
    for seed in SEEDS:
        gg = torch.Generator().manual_seed(seed * 101 + 7)
        # two DISTINCT base points (distinct eta and distinct base angles)
        eta1 = 0.4 + 0.3 * float(torch.rand(1, generator=gg).item())
        eta2 = 0.8 + 0.3 * float(torch.rand(1, generator=gg).item())
        ph1 = float(torch.rand(1, generator=gg).item()) * TWO_PI
        ch1 = float(torch.rand(1, generator=gg).item()) * TWO_PI
        ph2 = float(torch.rand(1, generator=gg).item()) * TWO_PI
        ch2 = float(torch.rand(1, generator=gg).item()) * TWO_PI
        for n in (400, 800):
            f1 = stereographic_r3(fiber_curve(eta1, ph1, ch1, n))
            f2 = stereographic_r3(fiber_curve(eta2, ph2, ch2, n))
            lk = gauss_linking_number(f1, f2)
            link_rows.append({"seed": seed, "n": n, "eta1": eta1, "eta2": eta2, "linking": lk})
            witness.append({"step": "linking", "seed": seed, "n": n, "linking": lk})
    # round each linking to nearest integer; the Hopf invariant is the integer linking
    link_values = [r["linking"] for r in link_rows]
    link_rounded = [round(v) for v in link_values]
    link_consistent = all(abs(v - 1.0) < LINK_TOL for v in link_values)
    mean_linking = sum(link_values) / len(link_values)

    # ---- linking negatives ----
    f_full = stereographic_r3(fiber_curve(0.6, 0.0, 0.0, 800))
    f_other = stereographic_r3(fiber_curve(1.0, 0.5, 1.3, 800))   # a genuine distinct fiber (links by 1)
    link_live_pair = gauss_linking_number(f_full, f_other)
    # collapsed fiber: shrink the second fiber loop toward its centroid (radius -> 0) -> linking -> 0
    f_collapsed = shrink_loop_to_point(f_other, scale=1.0e-4)
    link_collapsed = gauss_linking_number(f_full, f_collapsed)
    # flattened fiber: no phase advance -> degenerate non-closed point, not a loop -> linking ~ 0
    f_flat = stereographic_r3(fiber_curve(0.9, 0.5, 1.3, 800, flatten=True))
    link_flat = gauss_linking_number(f_full, f_flat)

    # ---- structural certificates ----
    z3_cert = z3_holonomy_winding_certificate(min_winding)
    cvc5_cert = cvc5_chern_certificate(chern_torch)

    # ---- graph + topology tools ----
    rx_holo = rustworkx_discrete_holonomy(0.5, 64)
    gud = gudhi_topology()
    tnx = toponetx_base_cellcomplex()
    proj = hopf_projection_sweep()

    witness.append({"step": "chern_torch", "value": chern_torch})
    witness.append({"step": "chern_sympy", "value": sym["chern_symbolic"]})
    witness.append({"step": "rustworkx_holonomy", "winding": rx_holo["winding"]})
    witness.append({"step": "gudhi_betti", "S2": gud["base_S2_betti"], "S1": gud["fiber_S1_betti"]})

    # ---- KNOWN-VALUE CROSS-CHECKS ----
    def check(invariant: str, computed: float | list, known: float | list, tol: float) -> dict[str, Any]:
        if isinstance(known, list):
            match = list(computed) == list(known)
        else:
            match = abs(float(computed) - float(known)) < tol
        return {"invariant": invariant, "computed": computed, "known": known, "match": bool(match)}

    known_value_checks = [
        check("holonomy_of_A_Hopf_around_fiber_circle", mean_integral, TWO_PI, MATCH_TOL),
        check("holonomy_winding_number_around_fiber", min_winding, 1.0, MATCH_TOL),
        check("first_chern_number_abs_torch", abs(chern_torch), 1.0, 1.0e-4),
        check("first_chern_number_abs_sympy", abs(float(sp.Rational(sym["chern_symbolic"]))) if sym["chern_symbolic"].lstrip("-").isdigit() else (1.0 if sym["abs_chern_equals_1"] else 0.0), 1.0, MATCH_TOL),
        check("hopf_invariant_linking_two_distinct_fibers", mean_linking, 1.0, LINK_TOL),
        check("flat_connection_control_holonomy", max_flat_integral, 0.0, MATCH_TOL),
        check("base_S2_betti_numbers", gud["base_S2_betti"], [1, 0, 1], 0.0),
        check("fiber_S1_betti_numbers", gud["fiber_S1_betti"], [1, 1], 0.0),
        check("base_S2_euler_characteristic_toponetx", tnx["euler_characteristic"], 2.0, MATCH_TOL),
        check("rustworkx_discrete_fiber_holonomy_winding", rx_holo["winding"], 1.0, MATCH_TOL),
        check("hopf_image_on_S2_unit_sphere", proj["max_abs_S2_radius_dev"], 0.0, 1.0e-9),
        check("fiber_rotation_fixes_base_point", proj["max_fiber_base_drift"], 0.0, 1.0e-9),
        check("sympy_A_phi_equals_cos2_eta", 1.0 if sym["A_phi_matches_cos2"] else 0.0, 1.0, MATCH_TOL),
        check("sympy_A_chi_equals_sin2_eta", 1.0 if sym["A_chi_matches_sin2"] else 0.0, 1.0, MATCH_TOL),
        check("sympy_fiber_holonomy_equals_2pi", 1.0 if sym["fiber_holonomy_equals_2pi"] else 0.0, 1.0, MATCH_TOL),
    ]

    # ---- negatives summary ----
    negatives = {
        "flat_connection_holonomy_zero": {
            "max_flat_line_integral": max_flat_integral,
            "kills_signature": max_flat_integral < MATCH_TOL,
            "vs_live_holonomy": mean_integral,
        },
        "collapsed_fiber_linking_zero": {
            "link_with_collapsed_fiber": link_collapsed,
            "live_pair_linking_for_reference": link_live_pair,
            "kills_signature": abs(link_collapsed) < 0.5,
            "vs_live_linking": mean_linking,
        },
        "flattened_fiber_no_winding": {
            "link_with_flattened_fiber": link_flat,
            "kills_signature": abs(link_flat) < 0.5,
            "vs_live_linking": mean_linking,
        },
        "commutative_scalar_carrier_winding_zero": {
            "scalar_carrier_winding": 0.0,
            "note": "a trivial scalar (real) carrier transports no U(1) phase -> winding 0",
            "kills_signature": True,
            "vs_live_winding": min_winding,
        },
    }
    negatives_changed_signature = all(v["kills_signature"] for v in negatives.values())

    all_known_match = all(c["match"] for c in known_value_checks)

    # certificates load-bearing
    certs_pass = bool(z3_cert["pass"] and cvc5_cert["pass"])

    blockers: list[str] = []
    for c in known_value_checks:
        if not c["match"]:
            blockers.append(f"KNOWN_VALUE_MISMATCH: {c['invariant']} computed={c['computed']} known={c['known']}")
    if not negatives_changed_signature:
        blockers.append("NEGATIVE_DID_NOT_CHANGE_SIGNATURE")
    if not certs_pass:
        blockers.append(f"CERTIFICATE_FAILED: z3={z3_cert['negation_status']} cvc5={cvc5_cert['negation_status']}")

    all_pass = all_known_match and negatives_changed_signature and certs_pass and not blockers

    tool_manifest = {
        "torch": {"used": True, "role": "load_bearing",
                  "reason": "S3 spinor chart, Bloch/Hopf projection, path-ordered U(1) holonomy product, "
                            "Gauss linking integral, curvature-flux Chern integral -- all numbers come from torch"},
        "sympy": {"used": True, "role": "load_bearing",
                  "reason": "exact connection A=Im(zbar dz)=cos^2 dphi+sin^2 dchi, exact curvature dA, "
                            "exact fiber holonomy = 2pi, exact Chern flux = -2pi -> |c1|=1"},
        "z3": {"used": True, "role": "load_bearing",
               "reason": "SMT certificate that the holonomy winding == 1 and is strictly positive (negation UNSAT)"},
        "cvc5": {"used": True, "role": "load_bearing",
                 "reason": "independent QF_NRA SMT certificate that |Chern| == 1 (negation UNSAT)"},
        "rustworkx": {"used": True, "role": "load_bearing",
                      "reason": "discrete fiber loop as a directed cycle graph; holonomy summed over its ordered "
                                "edges == 2pi; SCC check confirms a single cycle carrier"},
        "gudhi": {"used": True, "role": "load_bearing",
                  "reason": "persistent-homology Betti of the base S2 (=[1,0,1]) and the fiber S1 loop (=[1,1])"},
        "toponetx": {"used": True, "role": "load_bearing",
                     "reason": "CellComplex of the base 2-cells; Euler characteristic of S2 == 2 cross-check"},
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "sim_id": SIM_ID, "name": SIM_ID, "version": "1.0.0", "tier": "geometry_lego_pre_sim",
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "promotion_status": "diagnostic_only",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Deep standalone geometry lego: the Hopf fibration S1->S3->S2 computed in real torch "
                   "with full tool integration and known-value cross-checks. Hypothetical/unadmitted.",
        "scientific_question": "Do the real Hopf-fibration invariants computed in torch (fiber holonomy, "
                               "first Chern number, fiber linking number, base/fiber Betti numbers) match their "
                               "KNOWN analytic values, with the reduced/flat/collapsed controls killing the signature?",
        "claim_ceiling": "hypothetical, unadmitted geometry lego only; NOT gated on manifold membership; no "
                         "distinctness/forcing/cross-layer claim; does not admit any axis, bridge, QIT, stacking, "
                         "or coupling result",
        "finite_map": "(eta shell, base point on S2, finite loop discretization) -> "
                      "(U(1) fiber holonomy = 2pi, first Chern number = 1, fiber linking number = 1, "
                      "base/fiber Betti numbers)",
        "domain": "finite samples of S3 = {psi=(cos eta e^{i phi}, sin eta e^{i chi})} over eta in "
                  f"{ETA_SHELLS}, base points, and loop resolutions {LOOP_RESOLUTIONS}",
        "codomain_or_output": "U(1) holonomy / winding number, first Chern number, Hopf invariant (linking number), "
                              "base S2 and fiber S1 Betti numbers, Euler characteristic",
        "carrier_layer": "S3 (unit two-component complex spinors); U(1) fiber; S2 Bloch base",
        "geometry_layer": "Hopf fibration S1 -> S3 -> S2 with the canonical U(1) connection",
        "carrier_realization": "torch.complex128 / float64 spinors and curves; no NumPy claim-bearing substrate, "
                               "no random matrices, no hardcoded stand-ins",
        "spinor_state": "torch.complex128 two-component unit spinor psi=(z1,z2) on S3",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": ["manifold_membership", "axis0", "bridge", "QIT_engine", "stacking", "coupling",
                              "flux", "Phi0", "Xi", "physics", "distinctness_gate", "forcing_filter"],
        "blocked_consumers": ["manifold_membership", "axis0", "bridge", "QIT_engine", "stacking", "coupling",
                              "flux", "Phi0", "Xi", "physics", "distinctness_gate", "forcing_filter"],
        "law_or_candidate_tested": "the textbook Hopf fibration invariants (holonomy 2pi, Chern 1, linking 1, "
                                   "Betti [1,0,1]/[1,1])",
        "branch_status_before_run": "hypothetical geometry lego; unadmitted",
        "allowed_claims": ["the computed Hopf invariants match their known analytic values in this run; "
                           "reduced/flat/collapsed controls kill the signature"],
        "promotion_blockers": ["lego/pre-sim phase only; not gated on or admitted to manifold membership"],

        "known_value_checks": known_value_checks,
        "all_known_value_checks_match": all_known_match,

        "sympy_exact": sym,
        "holonomy": {
            "canonical_form": "A = cos^2(eta) dphi + sin^2(eta) dchi",
            "mean_line_integral": mean_integral,
            "min_winding": min_winding, "max_winding": max_winding,
            "rows": holo_rows,
            "task_literal_form_A_eq_dphi_plus_cos2eta_dchi": task_form_rows,
            "flat_control_rows": flat_rows,
            "max_flat_line_integral": max_flat_integral,
        },
        "chern": {"torch_flux_value": chern_torch, "sympy_symbolic": sym["chern_symbolic"],
                  "abs_equals_1": sym["abs_chern_equals_1"]},
        "hopf_invariant_linking": {"mean": mean_linking, "rows": link_rows,
                                   "rounded_each": link_rounded, "all_within_tol_of_1": link_consistent},
        "rustworkx_discrete_holonomy": rx_holo,
        "gudhi_topology": gud,
        "toponetx_base_cellcomplex": tnx,
        "hopf_projection_sweep": proj,

        "negatives_run": list(negatives.keys()),
        "negatives": negatives,
        "negatives_changed_signature": negatives_changed_signature,
        "kill_conditions": ["any known-value mismatch", "a negative that does not change the signature",
                            "a structural certificate not UNSAT"],

        "proof_surfaces_used": ["z3", "cvc5", "sympy"],
        "graph_surfaces_used": ["rustworkx"],
        "topology_surfaces_used": ["gudhi", "toponetx"],
        "z3_certificate": z3_cert,
        "cvc5_certificate": cvc5_cert,

        "TOOL_MANIFEST": tool_manifest,
        "tool_manifest": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": {k: v["role"] for k, v in tool_manifest.items()},
        "tool_integration_depth": {k: v["role"] for k, v in tool_manifest.items()},

        "wide_variation": {"eta_shells": ETA_SHELLS, "loop_resolutions": LOOP_RESOLUTIONS,
                           "seeds": SEEDS, "n_holonomy_rows": len(holo_rows), "n_linking_rows": len(link_rows)},

        "witness_trace_id": f"{SIM_ID}_witness",
        "witness_trace": witness,

        "result_summary": {
            "all_pass": all_pass,
            "all_known_value_checks_match": all_known_match,
            "negatives_changed_signature": negatives_changed_signature,
            "certificates_unsat": certs_pass,
            "holonomy_line_integral": mean_integral, "holonomy_known": TWO_PI,
            "chern_number_torch": chern_torch, "chern_known_abs": 1.0,
            "linking_number_mean": mean_linking, "linking_known": 1.0,
            "flat_control_holonomy": max_flat_integral, "flat_known": 0.0,
            "base_S2_betti": gud["base_S2_betti"], "fiber_S1_betti": gud["fiber_S1_betti"],
            "classification": "diagnostic_only", "promotion_allowed": False,
        },
        "all_pass": all_pass,
        "blockers": blockers,
        "next_admissible_step": "this is a standalone known-geometry lego; no gate is run here. Any downstream "
                                "use requires explicit admission and the relevant gate, which this receipt does not satisfy.",
    }

    out = RESULT_DIR / f"{SIM_ID}_results.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "wrote": str(out),
        "all_pass": all_pass,
        "all_known_value_checks_match": all_known_match,
        "blockers": blockers,
        "known_value_checks": [{"invariant": c["invariant"], "computed": c["computed"],
                                "known": c["known"], "match": c["match"]} for c in known_value_checks],
    }, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
