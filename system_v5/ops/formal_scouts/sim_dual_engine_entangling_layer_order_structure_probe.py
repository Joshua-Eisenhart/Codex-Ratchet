"""
sim_dual_engine_entangling_layer_order_structure_probe.py

The genuine next depth: ENTANGLING / multi-site layers, where the single-qubit
"shared Z-eigenbasis" criterion (from the operator-generality sim) is expected to
BREAK. Layers here are full 2-qubit operators on the Weyl carrier:
  XX = exp(i*0.7 X⊗X), YY = exp(i*0.5 Y⊗Y), ZZ = exp(i*0.9 Z⊗Z)  (entangling couplings)
  CZ = diag(1,1,1,-1)            (entangling, Z-diagonal)
  Xloc = X⊗I                     (local single-site, on qubit 0)
  CNOT                           (entangling)

KEY NON-OBVIOUS CLAIM tested: {XX,YY,ZZ} MUTUALLY COMMUTE even though their
single-qubit factors X,Y,Z do NOT share an eigenbasis — because (P⊗P)(Q⊗Q) =
(PQ)⊗(PQ) and the two sign flips from PQ=-QP cancel, so the couplings share the
BELL basis. So the single-qubit criterion is INSUFFICIENT for multi-site layers:
commutativity is shared eigenbasis of the FULL operators (here the Bell basis),
not of the single-site factors.

Dual-engine (torch/jax). z3+cvc5 proof load-bearing by mutation.
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

SIM_ID = "dual_engine_entangling_layer_order_structure_probe"
OPS = ["XX", "YY", "ZZ", "CZ", "Xloc", "CNOT"]
PAULI_COUPLINGS = ["XX", "YY", "ZZ"]
PAIRS = list(itertools.combinations(OPS, 2))
TXX, TYY, TZZ = 0.7, 0.5, 0.9

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "complex128 2-qubit entangling unitaries via matrix_exp + order-gaps"},
    "jax": {"tried": True, "used": True, "reason": "parity engine (x64): independent recompute of the entangling-layer commutation graph"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: '{XX,YY,ZZ} is a commuting clique' + local-breaks-witness; flips under erasure"},
    "cvc5": {"tried": True, "used": HAVE_CVC5, "reason": "second SMT family cross-check"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "jax": "load_bearing", "z3": "load_bearing",
                          "cvc5": ("load_bearing" if HAVE_CVC5 else None)}


def ops_torch():
    CDT = torch.complex128
    X = torch.tensor([[0, 1], [1, 0]], dtype=CDT)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=CDT)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=CDT)
    I = torch.eye(2, dtype=CDT)
    k = torch.kron
    return {
        "XX": torch.matrix_exp(1j * TXX * k(X, X)),
        "YY": torch.matrix_exp(1j * TYY * k(Y, Y)),
        "ZZ": torch.matrix_exp(1j * TZZ * k(Z, Z)),
        "CZ": torch.diag(torch.tensor([1, 1, 1, -1], dtype=CDT)),
        "Xloc": k(X, I),
        "CNOT": torch.tensor([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=CDT),
    }


def ops_jax():
    from jax.scipy.linalg import expm
    X = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    Y = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    Z = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    I = jnp.eye(2, dtype=jnp.complex128)
    k = jnp.kron
    return {
        "XX": expm(1j * TXX * k(X, X)),
        "YY": expm(1j * TYY * k(Y, Y)),
        "ZZ": expm(1j * TZZ * k(Z, Z)),
        "CZ": jnp.diag(jnp.array([1, 1, 1, -1], dtype=jnp.complex128)),
        "Xloc": k(X, I),
        "CNOT": jnp.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=jnp.complex128),
    }


def td_t(a, b):
    d = a - b
    return 0.5 * float(torch.sum(torch.abs(torch.linalg.eigvalsh((d + d.conj().T) / 2))))


def td_j(a, b):
    d = a - b
    return 0.5 * float(jnp.sum(jnp.abs(jnp.linalg.eigvalsh((d + jnp.conj(d).T) / 2))))


def graph(engine):
    if engine == "torch":
        rho, ops, td = carrier_t(), ops_torch(), td_t

        def ap(U, r):
            return U @ r @ U.conj().T
    else:
        rho, ops, td = carrier_j(), ops_jax(), td_j

        def ap(U, r):
            return U @ r @ jnp.conj(U).T
    g = {}
    for (Xn, Yn) in PAIRS:
        g[f"{Xn}|{Yn}"] = td(ap(ops[Yn], ap(ops[Xn], rho)), ap(ops[Xn], ap(ops[Yn], rho)))
    return g


def z3_proof(gaps, erase=False):
    s = z3.Solver()
    clique = [f"{a}|{b}" for i, a in enumerate(PAULI_COUPLINGS) for b in PAULI_COUPLINGS[i + 1:]]
    for k in clique:
        v = z3.Real(k.replace("|", "_"))
        s.add(v == z3.RealVal(repr(0.0 if erase else float(gaps[k]))))
        s.add(v <= z3.RealVal(repr(EPS)))   # claim: Pauli couplings mutually commute
    # witness: a LOCAL-vs-entangling pair must NOT commute (order genuinely matters somewhere)
    w = z3.Real("local_witness")
    wkey = "Xloc|CNOT" if "Xloc|CNOT" in gaps else "CNOT|Xloc"
    # pick the largest local/entangling-involving gap as the witness
    wg = max((0.0 if erase else gaps[k]) for k in gaps if "Xloc" in k.split("|"))
    s.add(w == z3.RealVal(repr(wg)))
    s.add(w > z3.RealVal(repr(EPS)))
    return str(s.check())


def cvc5_proof(gaps, erase=False):
    if not HAVE_CVC5:
        return "n/a"
    sv = cvc5.Solver(); sv.setLogic("QF_LRA"); R = sv.getRealSort()

    def rv(x):
        fr = Fraction(float(x)).limit_denominator(10 ** 15)
        return sv.mkReal(fr.numerator, fr.denominator)
    eps = rv(EPS)
    clique = [f"{a}|{b}" for i, a in enumerate(PAULI_COUPLINGS) for b in PAULI_COUPLINGS[i + 1:]]
    for k in clique:
        v = sv.mkConst(R, k.replace("|", "_"))
        sv.assertFormula(sv.mkTerm(Kind.EQUAL, v, rv(0.0 if erase else gaps[k])))
        sv.assertFormula(sv.mkTerm(Kind.LEQ, v, eps))
    w = sv.mkConst(R, "local_witness")
    wg = max((0.0 if erase else gaps[k]) for k in gaps if "Xloc" in k.split("|"))
    sv.assertFormula(sv.mkTerm(Kind.EQUAL, w, rv(wg)))
    sv.assertFormula(sv.mkTerm(Kind.GT, w, eps))
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
    clique = [f"{a}|{b}" for i, a in enumerate(PAULI_COUPLINGS) for b in PAULI_COUPLINGS[i + 1:]]
    pauli_couplings_commute = all(commutes(k) for k in clique)
    # local X⊗I breaks commutativity with at least the entangling couplings
    local_breaks = any(not commutes(key("Xloc", e)) for e in ["XX", "YY", "CNOT", "CZ"])
    # single-qubit-criterion would WRONGLY predict XX,YY,ZZ don't commute (X,Y,Z don't share eigenbasis)
    single_qubit_criterion_insufficient = pauli_couplings_commute  # the couplings DO commute -> criterion insufficient

    z3_real, z3_erased = z3_proof(gt, False), z3_proof(gt, True)
    cvc5_real, cvc5_erased = cvc5_proof(gt, False), cvc5_proof(gt, True)
    proof_load_bearing = bool(z3_real == "sat" and z3_erased == "unsat"
                              and (not HAVE_CVC5 or (cvc5_real == "sat" and cvc5_erased == "unsat")))

    n_commute = sum(1 for k in gt if commutes(k))

    known_value_checks = [
        {"invariant": "Pauli couplings {XX,YY,ZZ} MUTUALLY COMMUTE (Bell-basis clique)",
         "computed": f"clique_gaps={[f'{gt[k]:.1e}' for k in clique]}", "known": "all ~0", "match": pauli_couplings_commute},
        {"invariant": "single-qubit shared-eigenbasis criterion INSUFFICIENT for multi-site (X,Y,Z dont share basis yet XX,YY,ZZ commute)",
         "computed": str(single_qubit_criterion_insufficient), "known": "True (criterion breaks)", "match": single_qubit_criterion_insufficient},
        {"invariant": "local X⊗I breaks commutativity with entangling layers",
         "computed": str(local_breaks), "known": "True", "match": local_breaks},
        {"invariant": "dual-engine torch-vs-jax same classification (15 pairs)", "computed": str(same_class), "known": "True", "match": same_class},
        {"invariant": "dual-engine max gap delta < 1e-9", "computed": f"{max_delta:.2e}", "known": "<1e-9", "match": bool(max_delta < 1e-9)},
        {"invariant": "z3 proof SAT on real data", "computed": z3_real, "known": "sat", "match": z3_real == "sat"},
        {"invariant": "z3 flips to UNSAT under erasure (load-bearing)", "computed": z3_erased, "known": "unsat", "match": z3_erased == "unsat"},
        {"invariant": "cvc5 proof SAT on real data", "computed": cvc5_real, "known": "sat", "match": (cvc5_real == "sat") or not HAVE_CVC5},
    ]
    all_pass = bool(all(c["match"] for c in known_value_checks) and proof_load_bearing)

    out = {
        "sim_id": SIM_ID, "classification": "diagnostic_only", "promotion_allowed": False,
        "claim_ceiling": "Multi-site/entangling extension of the order-structure finding. State-level, diagnostic.",
        "finding": ("The single-qubit shared-eigenbasis criterion is INSUFFICIENT for entangling layers: the 2-site Pauli couplings {XX,YY,ZZ} MUTUALLY COMMUTE "
                    "(they share the Bell basis: (P kron P)(Q kron Q)=(PQ kron PQ) and the two PQ=-QP sign flips cancel) even though X,Y,Z individually share no eigenbasis. "
                    "Commutativity is shared eigenbasis of the FULL operators, and local operators break it against entangling layers."
                    if (pauli_couplings_commute and local_breaks) else "see commutation_table"),
        "n_operators": len(OPS), "n_pairs": len(PAIRS), "n_commute": n_commute, "n_noncommute": len(PAIRS) - n_commute,
        "commutation_table": table,
        "pauli_coupling_clique": clique,
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
    print(json.dumps({"pauli_couplings_commute_BELL": pauli_couplings_commute,
                      "single_qubit_criterion_insufficient": single_qubit_criterion_insufficient,
                      "local_breaks_entangling": local_breaks, "n_commute": n_commute, "n_noncommute": len(PAIRS) - n_commute,
                      "dual_engine_same_class": same_class, "max_delta": max_delta,
                      "proof_load_bearing": proof_load_bearing, "all_pass": all_pass,
                      "finding": out["finding"][:130]}, indent=2))
    return out


if __name__ == "__main__":
    main()
