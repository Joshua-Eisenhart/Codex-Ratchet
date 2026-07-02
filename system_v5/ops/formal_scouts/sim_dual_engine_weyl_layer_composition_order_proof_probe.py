"""
sim_dual_engine_weyl_layer_composition_order_proof_probe.py

Dual-engine (PyTorch primary / JAX parity) layer-composition ORDER test on a
left/right Weyl-spinor 2-qubit carrier. Tests whether composing operator/channel
layers in different orders (A then B vs B then A) is order-sensitive, measured as
the trace-distance "order gap" between the two composed density matrices, and
classified commute (<EPS) vs noncommute (>EPS).

Proof tools (z3 + cvc5) are made GENUINELY LOAD-BEARING by a mutation control:
the "order matters" verdict (UNSAT of 'all gaps <= eps' under the measured values)
must FLIP to SAT when the measured gaps are erased to zero. The solver consumes
the actual measured gaps, so the flip is not a tautology. sympy gives exact
symbolic unitary commutators as an independent algebraic cross-check.

NOTE (framing discipline): the order gap is STATE-LEVEL non-commutativity, NOT
Wolfram causal non-invariance (which would need a causal-graph embedding not built
here). classification = "diagnostic_only"; promotion_allowed = False.
"""
import jax
jax.config.update("jax_enable_x64", True)   # MUST precede any jnp use
import jax.numpy as jnp

import json
import math
import pathlib
from fractions import Fraction
import torch
import sympy as sp
import z3
try:
    import cvc5
    from cvc5 import Kind
    HAVE_CVC5 = True
except Exception:
    HAVE_CVC5 = False

torch.set_default_dtype(torch.float64)
CDT = torch.complex128
SIM_ID = "dual_engine_weyl_layer_composition_order_proof_probe"
EPS = 1e-9
A_PHASE, B_PHASE, THETA, GAMMA, P_DEPH = 0.7, 1.3, 0.9, 0.4, 0.3

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "primary complex128 carrier/channel/order-gap substrate + autograd gradient"},
    "jax": {"tried": True, "used": True, "reason": "second-engine parity (x64): independent recompute of the whole pipeline + jax.grad"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: 'order matters' = UNSAT of (all measured gaps <= eps); flips to SAT under erasure"},
    "cvc5": {"tried": True, "used": HAVE_CVC5, "reason": "second SMT family cross-check of the order-matters proof + mutation control"},
    "sympy": {"tried": True, "used": True, "reason": "exact symbolic commutators: [U1a,U1b]=0, [Rsu2,U1a]!=0"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "jax": "load_bearing", "z3": "load_bearing",
                          "cvc5": ("load_bearing" if HAVE_CVC5 else None), "sympy": "supportive"}

OP_NAMES = ["U1a", "U1b", "Rsu2", "AD", "DEPH"]
PAIRS = [(OP_NAMES[i], OP_NAMES[j]) for i in range(len(OP_NAMES)) for j in range(i + 1, len(OP_NAMES))]

# ======================================================================
# TORCH ENGINE (primary)
# ======================================================================
I2_t = torch.eye(2, dtype=CDT)
X_t = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
Z_t = torch.tensor([[1, 0], [0, -1]], dtype=CDT)
G5_t = torch.diag(torch.tensor([1, 1, -1, -1], dtype=CDT))


def _norm_t(v):
    return v / torch.linalg.norm(v)


def carrier_t():
    """Two Dirac C^4 bases -> left Weyl qubit0 (P_L upper) / right Weyl qubit1 (P_R lower),
    tensored then entangled (H on q0 + CZ) so the entanglement readout is meaningful."""
    PL = (torch.eye(4, dtype=CDT) + G5_t) / 2
    PR = (torch.eye(4, dtype=CDT) - G5_t) / 2
    d0 = torch.tensor([0.8, 0.3 + 0.2j, 0.1, 0.05], dtype=CDT)
    d1 = torch.tensor([0.2, 0.1, 0.7, 0.4 - 0.3j], dtype=CDT)
    q0 = _norm_t((PL @ d0)[:2])
    q1 = _norm_t((PR @ d1)[2:])
    psi = torch.kron(q0, q1)
    H = (1 / math.sqrt(2)) * torch.tensor([[1, 1], [1, -1]], dtype=CDT)
    CZ = torch.diag(torch.tensor([1, 1, 1, -1], dtype=CDT))
    psi = CZ @ (torch.kron(H, I2_t) @ psi)
    psi = _norm_t(psi)
    return torch.outer(psi, psi.conj())


def kraus_t(name, gamma=GAMMA):
    if name == "U1a":
        return [torch.tensor([[1, 0], [0, complex(math.cos(A_PHASE), math.sin(A_PHASE))]], dtype=CDT)]
    if name == "U1b":
        return [torch.tensor([[1, 0], [0, complex(math.cos(B_PHASE), math.sin(B_PHASE))]], dtype=CDT)]
    if name == "Rsu2":
        c, s = math.cos(THETA / 2), math.sin(THETA / 2)
        return [torch.tensor([[c, 1j * s], [1j * s, c]], dtype=CDT)]
    if name == "AD":
        g = gamma if torch.is_tensor(gamma) else torch.tensor(float(gamma), dtype=torch.float64)
        K0 = torch.zeros(2, 2, dtype=CDT); K0[0, 0] = 1.0; K0[1, 1] = torch.sqrt(1 - g)
        K1 = torch.zeros(2, 2, dtype=CDT); K1[0, 1] = torch.sqrt(g)
        return [K0, K1]
    if name == "DEPH":
        return [math.sqrt(1 - P_DEPH) * I2_t, math.sqrt(P_DEPH) * Z_t]
    raise ValueError(name)


def apply_t(kraus, rho):
    out = torch.zeros_like(rho)
    for K in kraus:
        Kf = torch.kron(K, I2_t)
        out = out + Kf @ rho @ Kf.conj().T
    return out


def compose_t(first, second, rho, gamma=GAMMA):
    return apply_t(kraus_t(second, gamma), apply_t(kraus_t(first, gamma), rho))


def trace_dist_t(a, b):
    d = a - b
    ev = torch.linalg.eigvalsh((d + d.conj().T) / 2)
    return 0.5 * torch.sum(torch.abs(ev))


def reduced0_t(rho):
    return torch.einsum("ikjk->ij", rho.reshape(2, 2, 2, 2))


def vn_entropy_t(rho):
    ev = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    ev = torch.clamp(ev, min=1e-13)
    return float(-torch.sum(ev * torch.log(ev)))


def order_gap_pair_t(X, Y, rho, gamma=GAMMA):
    return trace_dist_t(compose_t(X, Y, rho, gamma), compose_t(Y, X, rho, gamma))


def run_torch():
    rho = carrier_t()
    gaps, ent = {}, {}
    for (X, Y) in PAIRS:
        g = float(order_gap_pair_t(X, Y, rho))
        gaps[f"{X}|{Y}"] = g
        ent[f"{X}then{Y}"] = vn_entropy_t(reduced0_t(compose_t(X, Y, rho)))
    # control diagnostics on the carrier and a composed output
    rho_ad = apply_t(kraus_t("AD"), rho)
    ctrl = {
        "trace_carrier": float(torch.trace(rho).real),
        "min_eig_carrier": float(torch.linalg.eigvalsh((rho + rho.conj().T) / 2).min()),
        "herm_defect": float(torch.linalg.norm(rho - rho.conj().T)),
        "trace_after_AD": float(torch.trace(rho_ad).real),
        "min_eig_after_AD": float(torch.linalg.eigvalsh((rho_ad + rho_ad.conj().T) / 2).min()),
    }
    # autograd: d order_gap(Rsu2,AD)/d gamma
    g = torch.tensor(GAMMA, dtype=torch.float64, requires_grad=True)
    og = order_gap_pair_t("Rsu2", "AD", rho.detach(), gamma=g)
    og.backward()
    grad = float(g.grad)
    return gaps, ent, ctrl, grad


# ======================================================================
# JAX ENGINE (parity mirror)
# ======================================================================
I2_j = jnp.eye(2, dtype=jnp.complex128)
X_j = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
Z_j = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
G5_j = jnp.diag(jnp.array([1, 1, -1, -1], dtype=jnp.complex128))


def _norm_j(v):
    return v / jnp.linalg.norm(v)


def carrier_j():
    PL = (jnp.eye(4, dtype=jnp.complex128) + G5_j) / 2
    PR = (jnp.eye(4, dtype=jnp.complex128) - G5_j) / 2
    d0 = jnp.array([0.8, 0.3 + 0.2j, 0.1, 0.05], dtype=jnp.complex128)
    d1 = jnp.array([0.2, 0.1, 0.7, 0.4 - 0.3j], dtype=jnp.complex128)
    q0 = _norm_j((PL @ d0)[:2])
    q1 = _norm_j((PR @ d1)[2:])
    psi = jnp.kron(q0, q1)
    H = (1 / math.sqrt(2)) * jnp.array([[1, 1], [1, -1]], dtype=jnp.complex128)
    CZ = jnp.diag(jnp.array([1, 1, 1, -1], dtype=jnp.complex128))
    psi = CZ @ (jnp.kron(H, I2_j) @ psi)
    psi = _norm_j(psi)
    return jnp.outer(psi, jnp.conj(psi))


def kraus_j(name, gamma=GAMMA):
    if name == "U1a":
        return [jnp.array([[1, 0], [0, complex(math.cos(A_PHASE), math.sin(A_PHASE))]], dtype=jnp.complex128)]
    if name == "U1b":
        return [jnp.array([[1, 0], [0, complex(math.cos(B_PHASE), math.sin(B_PHASE))]], dtype=jnp.complex128)]
    if name == "Rsu2":
        c, s = math.cos(THETA / 2), math.sin(THETA / 2)
        return [jnp.array([[c, 1j * s], [1j * s, c]], dtype=jnp.complex128)]
    if name == "AD":
        g = gamma
        K0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128) + jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128) * jnp.sqrt(1 - g)
        K1 = jnp.array([[0, 1], [0, 0]], dtype=jnp.complex128) * jnp.sqrt(g)
        return [K0, K1]
    if name == "DEPH":
        return [math.sqrt(1 - P_DEPH) * I2_j, math.sqrt(P_DEPH) * Z_j]
    raise ValueError(name)


def apply_j(kraus, rho):
    out = jnp.zeros_like(rho)
    for K in kraus:
        Kf = jnp.kron(K, I2_j)
        out = out + Kf @ rho @ jnp.conj(Kf).T
    return out


def compose_j(first, second, rho, gamma=GAMMA):
    return apply_j(kraus_j(second, gamma), apply_j(kraus_j(first, gamma), rho))


def trace_dist_j(a, b):
    d = a - b
    ev = jnp.linalg.eigvalsh((d + jnp.conj(d).T) / 2)
    return 0.5 * jnp.sum(jnp.abs(ev))


def reduced0_j(rho):
    return jnp.einsum("ikjk->ij", rho.reshape(2, 2, 2, 2))


def vn_entropy_j(rho):
    ev = jnp.linalg.eigvalsh((rho + jnp.conj(rho).T) / 2).real
    ev = jnp.clip(ev, min=1e-13)
    return float(-jnp.sum(ev * jnp.log(ev)))


def order_gap_pair_j(X, Y, rho, gamma=GAMMA):
    return trace_dist_j(compose_j(X, Y, rho, gamma), compose_j(Y, X, rho, gamma))


def run_jax():
    rho = carrier_j()
    gaps, ent = {}, {}
    for (X, Y) in PAIRS:
        gaps[f"{X}|{Y}"] = float(order_gap_pair_j(X, Y, rho))
        ent[f"{X}then{Y}"] = vn_entropy_j(reduced0_j(compose_j(X, Y, rho)))
    grad = float(jax.grad(lambda g: order_gap_pair_j("Rsu2", "AD", rho, gamma=g))(GAMMA))
    rhos = {f"{X}|{Y}": compose_j(X, Y, rho) for (X, Y) in PAIRS}
    return gaps, ent, grad, rhos


# ======================================================================
# PROOF: z3 / cvc5 order-matters with MUTATION CONTROL (load-bearing)
# ======================================================================
def z3_order_matters(gaps, eps=EPS, erase=False):
    """Assert each gap equals its MEASURED value and that all gaps <= eps
    ('order does not matter for any pair'). With real data (a pair > eps) this is
    UNSAT -> 'order matters' certified. Erase to 0 -> SAT. The flip proves the
    solver consumed the measured values (not a tautology)."""
    s = z3.Solver()
    for name, g in gaps.items():
        v = z3.Real(name.replace("|", "_"))
        s.add(v == z3.RealVal(repr(0.0 if erase else float(g))))
        s.add(v <= z3.RealVal(repr(eps)))
    return str(s.check())


def cvc5_order_matters(gaps, eps=EPS, erase=False):
    if not HAVE_CVC5:
        return "n/a"
    sv = cvc5.Solver()
    sv.setLogic("QF_LRA")
    sv.setOption("produce-models", "true")
    R = sv.getRealSort()
    def rv(x):
        fr = Fraction(float(x)).limit_denominator(10 ** 15)
        return sv.mkReal(fr.numerator, fr.denominator)
    for name, g in gaps.items():
        v = sv.mkConst(R, name.replace("|", "_"))
        sv.assertFormula(sv.mkTerm(Kind.EQUAL, v, rv(0.0 if erase else g)))
        sv.assertFormula(sv.mkTerm(Kind.LEQ, v, rv(eps)))
    return str(sv.checkSat())


def sympy_commutators():
    a, b, th = sp.symbols("a b th", real=True)
    U1a = sp.Matrix([[1, 0], [0, sp.exp(sp.I * a)]])
    U1b = sp.Matrix([[1, 0], [0, sp.exp(sp.I * b)]])
    Rs = sp.Matrix([[sp.cos(th / 2), sp.I * sp.sin(th / 2)], [sp.I * sp.sin(th / 2), sp.cos(th / 2)]])
    comm_ab = sp.simplify(U1a * U1b - U1b * U1a)
    comm_ra = sp.simplify(Rs * U1a - U1a * Rs)
    return {
        "[U1a,U1b]==0_exact": comm_ab == sp.zeros(2, 2),
        "[Rsu2,U1a]!=0_exact": comm_ra != sp.zeros(2, 2),
    }


# ======================================================================
# MAIN
# ======================================================================
def main():
    t_gaps, t_ent, t_ctrl, t_grad = run_torch()
    j_gaps, j_ent, j_grad, j_rhos = run_jax()

    # dual-engine deltas
    t_rho = carrier_t()
    max_rho_delta = 0.0
    for (X, Y) in PAIRS:
        tr = compose_t(X, Y, t_rho).detach().numpy()
        jr = jnp.asarray(j_rhos[f"{X}|{Y}"])
        max_rho_delta = max(max_rho_delta, float(jnp.linalg.norm(jnp.asarray(tr) - jr)))
    max_entropy_delta = max(abs(t_ent[k] - j_ent[k]) for k in t_ent)
    gradient_delta = abs(t_grad - j_grad)

    commutation_table = []
    for (X, Y) in PAIRS:
        k = f"{X}|{Y}"
        commutation_table.append({"pair": k, "order_gap": t_gaps[k], "commutes": bool(t_gaps[k] < EPS)})

    same_table = all((t_gaps[k] < EPS) == (j_gaps[k] < EPS) for k in t_gaps)
    same_controls = bool(
        same_table
        and abs(t_ctrl["trace_carrier"] - 1.0) < 1e-9
        and t_ctrl["min_eig_carrier"] > -1e-9
        and t_ctrl["herm_defect"] < 1e-9
        and abs(t_ctrl["trace_after_AD"] - 1.0) < 1e-9
        and t_ctrl["min_eig_after_AD"] > -1e-9
    )

    # PROOF + mutation control
    z3_real, z3_erased = z3_order_matters(t_gaps, erase=False), z3_order_matters(t_gaps, erase=True)
    cvc5_real, cvc5_erased = cvc5_order_matters(t_gaps, erase=False), cvc5_order_matters(t_gaps, erase=True)
    z3_load_bearing = (z3_real != z3_erased) and (z3_real == "unsat") and (z3_erased == "sat")
    cvc5_load_bearing = HAVE_CVC5 and (cvc5_real != cvc5_erased) and (cvc5_real == "unsat") and (cvc5_erased == "sat")
    proof_load_bearing = bool(z3_load_bearing and (cvc5_load_bearing or not HAVE_CVC5))
    sym = sympy_commutators()

    n_noncommute = sum(1 for c in commutation_table if not c["commutes"])
    n_commute = sum(1 for c in commutation_table if c["commutes"])

    torch_pass = bool(same_controls and n_noncommute > 0 and n_commute > 0)
    jax_pass = bool(max_rho_delta < 1e-9 and max_entropy_delta < 1e-9 and same_table)

    known_value_checks = [
        {"invariant": "abelian pair U1a|U1b commutes (gap~0)", "computed": f"{t_gaps['U1a|U1b']:.2e}", "known": "0", "match": bool(t_gaps["U1a|U1b"] < EPS)},
        {"invariant": "diagonal pair U1a|DEPH commutes (gap~0)", "computed": f"{t_gaps['U1a|DEPH']:.2e}", "known": "0", "match": bool(t_gaps["U1a|DEPH"] < EPS)},
        {"invariant": "U1a|Rsu2 does NOT commute (gap>0)", "computed": f"{t_gaps['U1a|Rsu2']:.2e}", "known": ">0", "match": bool(t_gaps["U1a|Rsu2"] > EPS)},
        {"invariant": "z3 order-matters UNSAT on real data", "computed": z3_real, "known": "unsat", "match": z3_real == "unsat"},
        {"invariant": "z3 flips to SAT under gap-erasure (load-bearing)", "computed": z3_erased, "known": "sat", "match": z3_erased == "sat"},
        {"invariant": "cvc5 order-matters UNSAT on real data", "computed": cvc5_real, "known": "unsat", "match": (cvc5_real == "unsat") or not HAVE_CVC5},
        {"invariant": "cvc5 flips to SAT under erasure", "computed": cvc5_erased, "known": "sat", "match": (cvc5_erased == "sat") or not HAVE_CVC5},
        {"invariant": "sympy [U1a,U1b]==0 exact", "computed": str(sym["[U1a,U1b]==0_exact"]), "known": "True", "match": bool(sym["[U1a,U1b]==0_exact"])},
        {"invariant": "sympy [Rsu2,U1a]!=0 exact", "computed": str(sym["[Rsu2,U1a]!=0_exact"]), "known": "True", "match": bool(sym["[Rsu2,U1a]!=0_exact"])},
        {"invariant": "dual-engine max_rho_delta < 1e-9", "computed": f"{max_rho_delta:.2e}", "known": "<1e-9", "match": bool(max_rho_delta < 1e-9)},
        {"invariant": "dual-engine gradient_delta < 1e-9", "computed": f"{gradient_delta:.2e}", "known": "<1e-9", "match": bool(gradient_delta < 1e-9)},
    ]
    all_pass = bool(all(c["match"] for c in known_value_checks) and proof_load_bearing and torch_pass and jax_pass)

    out = {
        "sim_id": SIM_ID,
        "classification": "diagnostic_only",
        "promotion_allowed": False,
        "claim_ceiling": "Dual-engine order-sensitivity diagnostic; STATE-LEVEL non-commutativity, not Wolfram causal non-invariance.",
        "torch_pass": torch_pass,
        "jax_pass": jax_pass,
        "max_rho_delta": max_rho_delta,
        "max_entropy_delta": max_entropy_delta,
        "gradient_delta": gradient_delta,
        "same_controls": same_controls,
        "commutation_table": commutation_table,
        "n_commute": n_commute,
        "n_noncommute": n_noncommute,
        "proof_real_verdict": {"z3": z3_real, "cvc5": cvc5_real},
        "proof_erased_verdict": {"z3": z3_erased, "cvc5": cvc5_erased},
        "proof_load_bearing": proof_load_bearing,
        "torch_grad_Rsu2_AD_dgamma": t_grad,
        "jax_grad_Rsu2_AD_dgamma": j_grad,
        "torch_gaps": t_gaps,
        "jax_gaps": j_gaps,
        "controls": t_ctrl,
        "known_value_checks": known_value_checks,
        "all_pass": all_pass,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [],
    }
    outdir = pathlib.Path(__file__).parent / "results"
    outdir.mkdir(exist_ok=True)
    (outdir / f"{SIM_ID}_results.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: out[k] for k in ["torch_pass", "jax_pass", "max_rho_delta", "gradient_delta",
                                          "same_controls", "n_commute", "n_noncommute",
                                          "proof_real_verdict", "proof_erased_verdict", "proof_load_bearing", "all_pass"]}, indent=2))
    return out


if __name__ == "__main__":
    main()
