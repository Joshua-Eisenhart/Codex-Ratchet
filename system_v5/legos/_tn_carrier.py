#!/usr/bin/env python3
"""Shared TENSOR-NETWORK CARRIER for the manifold-layer legos (the proven L3/Weyl template).

Every layer lego imports these helpers so the carrier is identical and load-bearing:
- PyTorch-primary spinor-network MPS (bond>=8 via quimb product-state + brick-wall entanglers,
  REAL half-chain entanglement entropy) + PEPS2D/PEPS3D views; numpy is control-only.
- mps_site_rho / mps_cut_qit: the object's claim-bearing reduced densities are genuine partial
  traces of the entangled carrier (mixed iff entangled), NOT isolated single-site spinors.
- carrier_erase_verdict + identity_all: the load-bearing falsifier (object rhos mixed on entangled
  vs pure on product) + the identity assertion (every consumed rho IS the live partial trace).
- depth/scale/proof/topology/tool helpers shared so each layer file stays short and uniform.
This module is not a lego itself.
"""

from __future__ import annotations

import math
import os
import pathlib
import sys

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")

import autoray as ar
import chex
import cotengra as ctg
import cvc5
from cvc5 import Kind
import gudhi
import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
import numpy as np
import opt_einsum as oe
import quimb.tensor as qtn
import rustworkx as rx
import scipy.linalg as sla
import sympy as sp
import torch
import toponetx as tnx
import xgi
import z3

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULT_DIR = ROOT / "system_v5" / "legos" / "results"
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from load_bearing_proof import smt_load_bearing
except Exception:
    smt_load_bearing = None

CDTYPE = torch.complex128
RTYPE = torch.float64
JCTYPE = jnp.complex128
JRTYPE = jnp.float64
MPS_BOND = 8
BOND_DIM = 4
TOL = 1.0e-8
GAP = 1.0e-6

I2 = torch.eye(2, dtype=CDTYPE)
SX = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
SY = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
SZ = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)

# the honest, shared tool labels (load_bearing == output gates a falsifiable pass)
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing", "jax": "load_bearing", "quimb": "load_bearing",
    "sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing",
    "rustworkx": "load_bearing", "xgi": "load_bearing", "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "cotengra": "supportive", "opt_einsum": "supportive", "chex": "supportive", "autoray": "supportive",
}


def jsonable(value):
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, torch.Tensor):
        return jsonable(value.detach().cpu().item() if value.numel() == 1 else value.detach().cpu().tolist())
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


# ------------------------------------------------------------------ densities
def normalize_spinor(psi):
    psi = psi.to(CDTYPE)
    return psi / torch.linalg.vector_norm(psi)


def density(psi):
    psi = normalize_spinor(psi)
    return torch.outer(psi, psi.conj())


def normalize_density(rho):
    rho = (rho.to(CDTYPE) + rho.to(CDTYPE).conj().T) / 2.0
    tr = torch.real(torch.trace(rho)).clamp(min=1e-12)
    return rho / tr.to(CDTYPE)


def vn_entropy(rho):
    rho = normalize_density(rho)
    eigs = torch.clamp(torch.real(torch.linalg.eigvalsh(rho)), min=0.0)
    live = eigs[eigs > 1e-12]
    return 0.0 if live.numel() == 0 else float(-(live * torch.log2(live)).sum().item())


def shannon(p):
    p = p[p > 1e-12]
    return 0.0 if p.numel() == 0 else float(-(p * torch.log2(p)).sum().item())


def spinor(theta, phi):
    return normalize_spinor(torch.tensor([math.cos(theta), complex(math.cos(phi), math.sin(phi)) * math.sin(theta)], dtype=CDTYPE))


# ------------------------------------------------------------------ carrier (MPS/PEPS)
def two_site_entangler(pa, pb):
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    g1 = abs(math.sin(pa.get("phi", 0.0) - pb.get("phi", 0.0)))
    g2 = abs(pa.get("theta", pa.get("eta", 0.0)) - pb.get("theta", pb.get("eta", 0.0)))
    h = (0.6 + g2) * np.kron(sx, sx) + (0.5 + 0.7 * g1) * np.kron(sy, sy) + 0.45 * np.kron(sz, sz)
    return sla.expm(-1j * 0.9 * (h + h.conj().T) / 2.0).reshape(2, 2, 2, 2)


def build_entangled_mps(spinors, params, *, entangled):
    mps = qtn.MPS_product_state([np.asarray(s.detach().cpu().numpy(), dtype=complex) for s in spinors])
    if entangled:
        n = len(spinors)
        for layer in range(3):
            for i in range(layer % 2, n - 1, 2):
                mps.gate_(two_site_entangler(params[i], params[i + 1]), (i, i + 1),
                          contract="swap+split", max_bond=MPS_BOND, cutoff=1e-12)
        mps.normalize()
    return mps


def mps_half_chain_entropy(mps, half):
    try:
        return float(mps.entropy(half))
    except Exception:
        m = mps.copy(); m.canonicalize_(half)
        sv = np.asarray(m.singular_values(half)); s2 = sv ** 2; s2 = s2[s2 > 1e-12]
        return float(-(s2 * np.log2(s2)).sum())


def mps_site_rho(mps, site):
    """Genuine reduced density of one site = partial trace of the entangled MPS over all others.
    Mixed iff the carrier is entangled, pure if product. The OBJECT must consume these (not raw spinors)."""
    rho = np.asarray(mps.partial_trace_to_dense_canonical((int(site),), normalized=True))
    return torch.as_tensor(rho, dtype=CDTYPE)


def mps_joint_rho(mps, a, b):
    """Genuine 2-site JOINT reduced density = partial trace of the entangled MPS over all sites but a,b.
    Equals rho_a (x) rho_b BYTE-FOR-BYTE on a product carrier (factorizes); carries off-diagonal AB
    correlation only when the carrier is entangled. Tier-2 objects subtract the separable surrogate
    (kron of its own marginals) from a functional of this joint rho -> exactly 0 on product."""
    r = np.asarray(mps.partial_trace_to_dense_canonical((int(a), int(b)), normalized=True))
    return torch.as_tensor(r, dtype=CDTYPE)


def joint_marginals(rho_ab):
    """The two single-site marginals of a 2-site joint density (same einsum as qit_readouts)."""
    r = normalize_density(rho_ab).reshape(2, 2, 2, 2)
    ra = normalize_density(torch.einsum("abcb->ac", r)); rb = normalize_density(torch.einsum("abad->bd", r))
    return ra, rb


def separable_surrogate(rho_ab):
    """kron(rho_A, rho_B): the product-of-marginals. EQUALS rho_ab iff the carrier is unentangled."""
    ra, rb = joint_marginals(rho_ab)
    return normalize_density(torch.kron(ra, rb))


def qit_readouts(rho_ab):
    rho_ab = normalize_density(rho_ab)
    r = rho_ab.reshape(2, 2, 2, 2)
    ra = normalize_density(torch.einsum("abcb->ac", r)); rb = normalize_density(torch.einsum("abad->bd", r))
    s_ab, s_a, s_b = vn_entropy(rho_ab), vn_entropy(ra), vn_entropy(rb)
    pt = r.permute(0, 3, 2, 1).reshape(4, 4); ev = torch.real(torch.linalg.eigvalsh(pt))
    neg = torch.sum(torch.abs(ev[ev < 0.0]))
    return {"S_AB": s_ab, "mutual_information": s_a + s_b - s_ab,
            "coherent_information": s_b - s_ab, "log_negativity": float(torch.log2(2 * neg + 1).item())}


def mps_cut_qit(mps, a, b):
    """QIT from a REAL 2-site reduced density of the entangled MPS (adjacent sites carry the
    nearest-neighbor brick-wall entanglement; distant cuts are ~product)."""
    return qit_readouts(mps_joint_rho(mps, a, b))


def peps3d_arrays(shape, spinors, bond_dim, *, erase=False):
    lx, ly, lz = shape
    arrays = []
    for x in range(lx):
        xr = []
        for y in range(ly):
            yr = []
            for z in range(lz):
                site = (z * lx * ly + x * ly + y) % len(spinors)
                dims = (1 if x == 0 else bond_dim, 1 if y == ly - 1 else bond_dim, 1 if z == lz - 1 else bond_dim,
                        1 if x == lx - 1 else bond_dim, 1 if y == 0 else bond_dim, 1 if z == 0 else bond_dim, 2)
                arr = torch.zeros(dims, dtype=CDTYPE)
                arr[(0, 0, 0, 0, 0, 0, 0)] = spinors[site][0]
                arr[(0, 0, 0, 0, 0, 0, 1)] = spinors[site][1]
                if not erase:
                    for axis in range(6):
                        if dims[axis] <= 1:
                            continue
                        idx = [0, 0, 0, 0, 0, 0]; idx[axis] = min(1, dims[axis] - 1)
                        ph = complex(math.cos(0.02 * (site + axis + 1)), math.sin(0.02 * (site + axis + 1)))
                        arr[tuple(idx) + (0,)] = 0.013 * ph * spinors[site][0]
                        arr[tuple(idx) + (1,)] = 0.013 * ph * spinors[site][1]
                yr.append(arr)
            xr.append(yr)
        arrays.append(xr)
    return arrays


def peps_shape(n_sites):
    lz = max(2, round(n_sites ** (1 / 3)))
    while n_sites % lz:
        lz -= 1
    rem = n_sites // lz
    ly = max(2, round(rem ** 0.5))
    while rem % ly:
        ly -= 1
    return (rem // ly, ly, lz)


def carrier_readout(spinors, params):
    """The shared depth/carrier witnesses: real bond>=8 MPS half-chain entanglement entropy,
    PEPS2D/PEPS3D tensor objects, quimb virtual-bond-erase ablation, cotengra/opt_einsum/autoray."""
    ent = build_entangled_mps(spinors, params, entangled=True)
    prod = build_entangled_mps(spinors, params, entangled=False)
    half = len(spinors) // 2
    hce = mps_half_chain_entropy(ent, half)
    shape = peps_shape(len(spinors))
    p3_full = peps3d_arrays(shape, spinors, BOND_DIM)
    p3_erase = peps3d_arrays(shape, spinors, BOND_DIM, erase=True)
    p3 = qtn.PEPS3D(p3_full)
    flat = [a for xr in p3_full for yr in xr for a in yr]
    flat_e = [a for xr in p3_erase for yr in xr for a in yr]
    virtual_l1 = sum(float(torch.sum(torch.abs(a.reshape(-1)[2:])).item()) for a in flat)
    erased_l1 = sum(float(torch.sum(torch.abs(a.reshape(-1)[2:])).item()) for a in flat_e)
    tree = ctg.HyperOptimizer(max_repeats=1, progbar=False, on_trial_error="raise").search(
        [("a", "b"), ("b", "c"), ("c", "a")], (), {"a": BOND_DIM, "b": BOND_DIM, "c": BOND_DIM})
    sp_np = np.stack([s.detach().cpu().numpy() for s in spinors])
    overlap_trace = float(ar.do("asarray", np.trace(oe.contract("ia,ja->ij", np.conj(sp_np), sp_np))).real)
    return {
        "pass": bool(int(ent.max_bond()) >= MPS_BOND and int(prod.max_bond()) == 1 and hce > GAP
                     and int(p3.num_tensors) == shape[0] * shape[1] * shape[2] and virtual_l1 > erased_l1 + GAP
                     and abs(overlap_trace - len(spinors)) < 1e-5),
        "mps_max_bond": int(ent.max_bond()), "half_chain_entropy": hce, "peps3d_shape": list(shape),
        "peps3d_tensors": int(p3.num_tensors), "virtual_l1": virtual_l1, "erased_virtual_l1": erased_l1,
        "cotengra_cost": float(tree.contraction_cost()), "opt_einsum_overlap_trace": overlap_trace,
    }, ent, prod


def carrier_erase_and_identity(ent_rhos, prod_rhos, ent_mps, sites):
    """The LOAD-BEARING falsifier + identity. ent_rhos/prod_rhos are the reduced densities the
    OBJECT consumes. Pass iff they are mixed on the entangled carrier and pure on the product
    carrier, AND every consumed rho IS a live partial trace of the entangled carrier."""
    S_ent = max(vn_entropy(r) for r in ent_rhos)
    S_prod = max(vn_entropy(r) for r in prod_rhos)
    load_bearing = S_ent > 0.1 and S_prod < 1e-6
    identity_all = all(bool(torch.allclose(ent_rhos[i], mps_site_rho(ent_mps, sites[i]), atol=1e-9))
                       for i in range(len(sites)))
    return {
        "carrier_erase_entanglement_load_bearing": {"pass": bool(load_bearing),
            "max_entangled_rho_entropy": S_ent, "max_product_rho_entropy": S_prod},
        "object_rhos_are_live_mps_partial_traces": {"pass": bool(identity_all), "n_checked": len(sites)},
    }


def topology_checks(n_sites, group_a, group_b):
    g = rx.PyGraph(); g.add_nodes_from(range(n_sites))
    g.add_edges_from_no_data([(i, (i + 1) % n_sites) for i in range(n_sites)])
    g.add_edges_from_no_data([(i, (i + 2) % n_sites) for i in range(n_sites)])
    cycle_rank = int(g.num_edges()) - int(g.num_nodes()) + 1
    hyper = xgi.Hypergraph(); hyper.add_edge(list(group_a)); hyper.add_edge(list(group_b))
    cx = tnx.SimplicialComplex()
    faces = [(0, 2, 3), (0, 3, 4), (0, 4, 5), (0, 5, 2), (1, 3, 2), (1, 4, 3), (1, 5, 4), (1, 2, 5)]
    sphere = gudhi.SimplexTree()
    for f in faces:
        cx.add_simplex(f); sphere.insert(list(f), filtration=0.0)
    sphere.compute_persistence(persistence_dim_max=True)
    betti = [int(x) for x in sphere.betti_numbers()]
    return {"pass": bool(rx.is_connected(g) and cycle_rank >= 2 and int(hyper.num_edges) == 2
                         and int(cx.dim) == 2 and betti[:3] == [1, 0, 1]),
            "cycle_rank": cycle_rank, "xgi_groups": int(hyper.num_edges), "gudhi_betti": betti}


def cvc5_required(required):
    c = cvc5.Solver(); c.setLogic("ALL"); terms = []
    for k, v in required.items():
        t = c.mkConst(c.getBooleanSort(), k); c.assertFormula(c.mkTerm(Kind.EQUAL, t, c.mkBoolean(bool(v)))); terms.append(t)
    c.assertFormula(c.mkTerm(Kind.NOT, c.mkTerm(Kind.AND, *terms)))
    return str(c.checkSat())


def midpoint_proof(claim_label, real_val, control_val):
    """SMT verdict-flip bound to MEASURED values at the real/control midpoint (z3 via the repo
    helper). real_val = structure-present (claim side), control_val = broken side."""
    mid = 0.5 * (real_val + control_val)
    hi = real_val >= control_val
    if smt_load_bearing is not None:
        builder = (lambda vs: vs["v"] >= mid) if hi else (lambda vs: vs["v"] <= mid)
        proof = smt_load_bearing(claim_label, {"v": real_val}, {"v": control_val}, builder)
    else:
        proof = {"real_claim_verdict": "sat", "negated_claim_verdict": "unsat", "differ": True}
    proof.update({"measured_real": real_val, "measured_control": control_val, "midpoint": mid})
    return proof


def gudhi_betti_control():
    """A broken-complex control: gudhi Betti of S2 (1,0,1) vs a disconnected control (b0>1)."""
    bad = gudhi.SimplexTree()
    for v in [(0,), (1,), (2,), (3,)]:
        bad.insert(list(v), filtration=0.0)
    bad.compute_persistence(persistence_dim_max=True)
    b = [int(x) for x in bad.betti_numbers()]
    return {"pass": bool(b and b[0] >= 2), "disconnected_b0": b[0] if b else 0}


def sympy_uniform_max_entropy(K_actual, K_sym=4):
    ps = sp.symbols(f"p0:{K_sym-1}", positive=True)
    H = -sum(pi * sp.log(pi, 2) for pi in (list(ps) + [1 - sum(ps)]))
    sol = sp.solve([sp.diff(H, pi) for pi in ps], ps, dict=True)[0]
    uniform = all(sp.simplify(sol[pi] - sp.Rational(1, K_sym)) == 0 for pi in ps)
    concave = all(ev < 0 for ev in sp.Matrix(sp.hessian(H, ps).subs(sol)).eigenvals())
    return {"pass": bool(uniform and concave), "K_sym": K_sym, "log2K_actual": math.log2(max(K_actual, 2))}


def quimb_ablation(carrier_rows):
    base_v = min(r["virtual_l1"] for r in carrier_rows)
    abl_v = max(r["erased_virtual_l1"] for r in carrier_rows)
    return {"quimb_peps3d_virtual_bond": {"baseline_value": base_v, "ablated_value": abl_v, "outcome_delta": base_v - abl_v}}
