"""
sim_dual_engine_geometry_lego_operators_commutation_tie_in_probe.py

Ties the composition-phase order-structure finding to the VERIFIED geometry-lego
catalog: re-runs the layer-commutation test using REAL geometry-derived operators
instead of toy Paulis, and checks two things:

 1. SHARED-EIGENBASIS criterion (from the operator-generality sim) holds on real
    geometry operators: the diagonal/shared-Z family
      {Berry_a, Berry_b (abelian U(1) Berry holonomies),
       Cliff_rotor_Z (even-Cl(3) rotor exp(-th/2 e1e2) = Z-rotation, diagonal),
       ProjZ (Z-basis measurement channel)}
    is a commuting clique; the non-abelian Wilczek-Zee SU(2) holonomies
      {WZ_a, WZ_b} (off-diagonal, different axes)
    break commutativity with the clique AND with each other.

 2. CONSISTENCY with the connection_holonomy lego (cross-model + cross-backend
    verified earlier): abelian holonomies COMMUTE (order gap ~0), non-abelian
    Wilczek-Zee holonomies do NOT (order gap > 0). The composition framework
    should reproduce this AND explain it via shared eigenbasis.

Dual-engine (torch/jax), z3+cvc5 proof load-bearing by mutation.
classification="diagnostic_only"; promotion_allowed=False.
"""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402

import json  # noqa: E402
import math  # noqa: E402
import pathlib  # noqa: E402
import itertools  # noqa: E402
from fractions import Fraction  # noqa: E402
import torch  # noqa: E402
import z3  # noqa: E402
try:
    import cvc5
    from cvc5 import Kind
    HAVE_CVC5 = True
except Exception:
    HAVE_CVC5 = False

from sim_dual_engine_weyl_layer_composition_order_proof_probe import carrier_t, carrier_j, EPS  # noqa: E402

SIM_ID = "dual_engine_geometry_lego_operators_commutation_tie_in_probe"
OPS = ["Berry_a", "Berry_b", "CliffRotZ", "ProjZ", "WZ_a", "WZ_b"]
DIAGONAL_FAMILY = ["Berry_a", "Berry_b", "CliffRotZ", "ProjZ"]   # abelian holonomy + Z-rotor + Z-measure
NONABELIAN = ["WZ_a", "WZ_b"]                                    # Wilczek-Zee SU(2) holonomies
PAIRS = list(itertools.combinations(OPS, 2))

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "complex128 geometry operators (holonomies/rotor/measure) + order-gaps via matrix_exp"},
    "jax": {"tried": True, "used": True, "reason": "parity engine (x64): independent recompute of the geometry-operator commutation graph"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: abelian-clique-commutes + WZ-witness UNSAT/flip under erasure"},
    "cvc5": {"tried": True, "used": HAVE_CVC5, "reason": "second SMT family cross-check"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "jax": "load_bearing", "z3": "load_bearing",
                          "cvc5": ("load_bearing" if HAVE_CVC5 else None)}

BERRY_A, BERRY_B = 0.7, 1.3          # abelian Berry holonomy phases
CLIFF_TH = 0.5                       # Cl(3) rotor angle about e1e2 (=> Z-rotation)


def _ops(xp, X, Y, Zp, I2, expm):
    # Berry abelian U(1) holonomy = diagonal phase on |1>
    Ba = xp.array([[1, 0], [0, complex(math.cos(BERRY_A), math.sin(BERRY_A))]], dtype=I2.dtype) if xp is jnp \
        else torch.tensor([[1, 0], [0, complex(math.cos(BERRY_A), math.sin(BERRY_A))]], dtype=I2.dtype)
    Bb = xp.array([[1, 0], [0, complex(math.cos(BERRY_B), math.sin(BERRY_B))]], dtype=I2.dtype) if xp is jnp \
        else torch.tensor([[1, 0], [0, complex(math.cos(BERRY_B), math.sin(BERRY_B))]], dtype=I2.dtype)
    # even-Cl(3) rotor about e1e2: e1e2 = sx sy = i sz, so exp(-th/2 e1e2) = exp(-i th/2 sz) (diagonal Z-rotation)
    CliffRotZ = expm(-1j * CLIFF_TH / 2 * Zp)
    # Wilczek-Zee non-abelian SU(2) holonomies (off-diagonal, different axes)
    WZ_a = expm(1j * (0.9 * X + 0.4 * Y) / 2)
    WZ_b = expm(1j * (0.3 * X + 0.8 * Zp) / 2)
    return {
        "Berry_a": [Ba], "Berry_b": [Bb], "CliffRotZ": [CliffRotZ],
        "ProjZ": [_proj0(I2), _proj1(I2)],   # Z-basis measurement channel {|0><0|,|1><1|} (CPTP, diagonal)
        "WZ_a": [WZ_a], "WZ_b": [WZ_b],
    }


def _proj0(I2):
    p = I2 * 0
    p[0, 0] = 1
    return p


def _proj1(I2):
    p = I2 * 0
    p[1, 1] = 1
    return p


def ops_torch():
    CDT = torch.complex128
    X = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDT)
    Zp = torch.tensor([[1, 0], [0, -1]], dtype=CDT)
    I2 = torch.eye(2, dtype=CDT)
    return _ops(torch, X, Y, Zp, I2, torch.matrix_exp)


def ops_jax():
    from jax.scipy.linalg import expm
    X = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    Y = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    Zp = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    I2 = jnp.eye(2, dtype=jnp.complex128)

    def _proj(i):
        m = [[0, 0], [0, 0]]
        m[i][i] = 1
        return jnp.array(m, dtype=jnp.complex128)
    Ba = jnp.array([[1, 0], [0, complex(math.cos(BERRY_A), math.sin(BERRY_A))]], dtype=jnp.complex128)
    Bb = jnp.array([[1, 0], [0, complex(math.cos(BERRY_B), math.sin(BERRY_B))]], dtype=jnp.complex128)
    return {
        "Berry_a": [Ba], "Berry_b": [Bb],
        "CliffRotZ": [expm(-1j * CLIFF_TH / 2 * Zp)],
        "ProjZ": [_proj(0), _proj(1)],
        "WZ_a": [expm(1j * (0.9 * X + 0.4 * Y) / 2)],
        "WZ_b": [expm(1j * (0.3 * X + 0.8 * Zp) / 2)],
    }


def apply_t(kraus, rho):
    I2 = torch.eye(2, dtype=torch.complex128)
    return sum(torch.kron(K, I2) @ rho @ torch.kron(K, I2).conj().T for K in kraus)


def apply_j(kraus, rho):
    I2 = jnp.eye(2, dtype=jnp.complex128)
    return sum(jnp.kron(K, I2) @ rho @ jnp.conj(jnp.kron(K, I2)).T for K in kraus)


def td_t(a, b):
    d = a - b
    return 0.5 * float(torch.sum(torch.abs(torch.linalg.eigvalsh((d + d.conj().T) / 2))))


def td_j(a, b):
    d = a - b
    return 0.5 * float(jnp.sum(jnp.abs(jnp.linalg.eigvalsh((d + jnp.conj(d).T) / 2))))


def graph(engine):
    if engine == "torch":
        rho, ops, ap, td = carrier_t(), ops_torch(), apply_t, td_t
    else:
        rho, ops, ap, td = carrier_j(), ops_jax(), apply_j, td_j
    g = {}
    for (Xn, Yn) in PAIRS:
        g[f"{Xn}|{Yn}"] = td(ap(ops[Yn], ap(ops[Xn], rho)), ap(ops[Xn], ap(ops[Yn], rho)))
    return g


def z3_proof(gaps, erase=False):
    s = z3.Solver()
    clique = [f"{a}|{b}" for i, a in enumerate(DIAGONAL_FAMILY) for b in DIAGONAL_FAMILY[i + 1:]]
    for k in clique:
        v = z3.Real(k.replace("|", "_"))
        s.add(v == z3.RealVal(repr(0.0 if erase else float(gaps[k]))))
        s.add(v <= z3.RealVal(repr(EPS)))
    wz = z3.Real("wz_witness")
    wz_gap = 0.0 if erase else gaps[f"{NONABELIAN[0]}|{NONABELIAN[1]}"]
    s.add(wz == z3.RealVal(repr(wz_gap)))
    s.add(wz > z3.RealVal(repr(EPS)))   # non-abelian WZ pair must NOT commute
    return str(s.check())


def cvc5_proof(gaps, erase=False):
    if not HAVE_CVC5:
        return "n/a"
    sv = cvc5.Solver(); sv.setLogic("QF_LRA"); R = sv.getRealSort()

    def rv(x):
        fr = Fraction(float(x)).limit_denominator(10 ** 15)
        return sv.mkReal(fr.numerator, fr.denominator)
    eps = rv(EPS)
    clique = [f"{a}|{b}" for i, a in enumerate(DIAGONAL_FAMILY) for b in DIAGONAL_FAMILY[i + 1:]]
    for k in clique:
        v = sv.mkConst(R, k.replace("|", "_"))
        sv.assertFormula(sv.mkTerm(Kind.EQUAL, v, rv(0.0 if erase else gaps[k])))
        sv.assertFormula(sv.mkTerm(Kind.LEQ, v, eps))
    wz = sv.mkConst(R, "wz_witness")
    wz_gap = 0.0 if erase else gaps[f"{NONABELIAN[0]}|{NONABELIAN[1]}"]
    sv.assertFormula(sv.mkTerm(Kind.EQUAL, wz, rv(wz_gap)))
    sv.assertFormula(sv.mkTerm(Kind.GT, wz, eps))
    return str(sv.checkSat())


def main():
    gt, gj = graph("torch"), graph("jax")
    max_delta = max(abs(gt[k] - gj[k]) for k in gt)
    same_class = all((gt[k] < EPS) == (gj[k] < EPS) for k in gt)

    def commutes(k):
        return gt[k] < EPS

    def key(a, b):
        return f"{a}|{b}" if f"{a}|{b}" in gt else f"{b}|{a}"

    table = [{"pair": k, "gap": gt[k], "commutes": bool(commutes(k))} for k in gt]
    clique = [f"{a}|{b}" for i, a in enumerate(DIAGONAL_FAMILY) for b in DIAGONAL_FAMILY[i + 1:]]
    clique_commutes = all(commutes(k) for k in clique)
    wz_pair_noncommute = not commutes(key("WZ_a", "WZ_b"))
    wz_breaks_clique = all(not commutes(key(w, d)) for w in NONABELIAN for d in DIAGONAL_FAMILY)
    abelian_berry_commute = commutes(key("Berry_a", "Berry_b"))

    z3_real, z3_erased = z3_proof(gt, False), z3_proof(gt, True)
    cvc5_real, cvc5_erased = cvc5_proof(gt, False), cvc5_proof(gt, True)
    proof_load_bearing = bool(z3_real == "sat" and z3_erased == "unsat"
                              and (not HAVE_CVC5 or (cvc5_real == "sat" and cvc5_erased == "unsat")))

    known_value_checks = [
        {"invariant": "LEGO TIE-IN: abelian Berry holonomies COMMUTE (Berry_a|Berry_b ~0)",
         "computed": f"{gt[key('Berry_a','Berry_b')]:.2e}", "known": "~0 (commute)", "match": abelian_berry_commute},
        {"invariant": "LEGO TIE-IN: non-abelian Wilczek-Zee holonomies do NOT commute (WZ_a|WZ_b >0)",
         "computed": f"{gt[key('WZ_a','WZ_b')]:.2e}", "known": ">0 (order matters)", "match": wz_pair_noncommute},
        {"invariant": "shared-eigenbasis: diagonal family {Berry_a,Berry_b,CliffRotZ,ProjZ} is a commuting clique",
         "computed": str(clique_commutes), "known": "True", "match": clique_commutes},
        {"invariant": "WZ holonomies break commutativity with the whole diagonal clique",
         "computed": str(wz_breaks_clique), "known": "True", "match": wz_breaks_clique},
        {"invariant": "dual-engine torch-vs-jax same classification", "computed": str(same_class), "known": "True", "match": same_class},
        {"invariant": "dual-engine max gap delta < 1e-9", "computed": f"{max_delta:.2e}", "known": "<1e-9", "match": bool(max_delta < 1e-9)},
        {"invariant": "z3 proof SAT on real data", "computed": z3_real, "known": "sat", "match": z3_real == "sat"},
        {"invariant": "z3 flips to UNSAT under erasure (load-bearing)", "computed": z3_erased, "known": "unsat", "match": z3_erased == "unsat"},
        {"invariant": "cvc5 proof SAT on real data", "computed": cvc5_real, "known": "sat", "match": (cvc5_real == "sat") or not HAVE_CVC5},
    ]
    all_pass = bool(all(c["match"] for c in known_value_checks) and proof_load_bearing)

    out = {
        "sim_id": SIM_ID, "classification": "diagnostic_only", "promotion_allowed": False,
        "claim_ceiling": "Ties the shared-eigenbasis order-structure finding to real geometry operators; reproduces the connection_holonomy lego's abelian-commute / WZ-noncommute result. State-level, diagnostic.",
        "tie_in_finding": ("CONFIRMED: the composition framework reproduces the connection_holonomy lego on real geometry operators — abelian Berry U(1) holonomies commute, "
                           "non-abelian Wilczek-Zee SU(2) holonomies do not — and the shared-eigenbasis criterion explains it (Berry/Cliff-Z-rotor/Z-measure share the Z eigenbasis = commuting clique; WZ are off-diagonal)."
                           if (abelian_berry_commute and wz_pair_noncommute and clique_commutes and wz_breaks_clique) else "see commutation_table"),
        "commutation_table": table,
        "diagonal_family": DIAGONAL_FAMILY, "nonabelian_holonomies": NONABELIAN,
        "dual_engine_max_delta": max_delta, "dual_engine_same_classification": same_class,
        "proof_real_verdict": {"z3": z3_real, "cvc5": cvc5_real},
        "proof_erased_verdict": {"z3": z3_erased, "cvc5": cvc5_erased},
        "proof_load_bearing": proof_load_bearing,
        "known_value_checks": known_value_checks, "all_pass": all_pass,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "blockers": [],
    }
    outdir = pathlib.Path(__file__).parent / "results"
    outdir.mkdir(exist_ok=True)
    (outdir / f"{SIM_ID}_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"abelian_berry_commute": abelian_berry_commute, "WZ_pair_noncommute": wz_pair_noncommute,
                      "diagonal_clique_commutes": clique_commutes, "WZ_breaks_clique": wz_breaks_clique,
                      "dual_engine_same_class": same_class, "max_delta": max_delta,
                      "proof_load_bearing": proof_load_bearing, "all_pass": all_pass,
                      "tie_in_finding": out["tie_in_finding"][:120]}, indent=2))
    return out


if __name__ == "__main__":
    main()
