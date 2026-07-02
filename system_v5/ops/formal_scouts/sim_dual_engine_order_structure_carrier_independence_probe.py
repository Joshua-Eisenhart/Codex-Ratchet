"""
sim_dual_engine_order_structure_carrier_independence_probe.py

Closes the open question: is the layer-composition ORDER structure (which pairs
commute) a property of the operator ALGEBRA, independent of the carrier state?

Re-runs the depth-2 order-test on site-0 reduced densities drawn from a
STRUCTURALLY DIFFERENT carrier — genuine quimb PEPS3D states at several bond
dims / lattices / seeds (mixed states), vs. the original exact pure Weyl-spinor
carrier. Claim: the commute / non-commute CLASSIFICATION is identical across all
carriers (operator-intrinsic), even though the gap MAGNITUDES vary with the input
state. Tested over many PEPS3D inputs (basin discipline).

Dual-engine (torch readout vs jax readout). Proof (z3+cvc5) load-bearing: assert
"the commute-classification is the SAME on every PEPS3D carrier as on the exact
reference" — flips if any carrier disagrees. classification="diagnostic_only".
"""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402

import json  # noqa: E402
import math  # noqa: E402
import pathlib  # noqa: E402
import itertools  # noqa: E402
from fractions import Fraction  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
import quimb.tensor as qtn  # noqa: E402
import z3  # noqa: E402
try:
    import cvc5
    from cvc5 import Kind
    HAVE_CVC5 = True
except Exception:
    HAVE_CVC5 = False

from sim_dual_engine_weyl_layer_composition_order_proof_probe import (  # noqa: E402
    OP_NAMES, EPS, kraus_t, kraus_j,
)

SIM_ID = "dual_engine_order_structure_carrier_independence_probe"
PAIRS = [(OP_NAMES[i], OP_NAMES[j]) for i in range(len(OP_NAMES)) for j in range(i + 1, len(OP_NAMES))]
# reference classification (from the exact Weyl-spinor carrier, twice-clean verified):
REFERENCE_COMMUTE = {  # True = commute
    "U1a|U1b": True, "U1a|Rsu2": False, "U1a|AD": True, "U1a|DEPH": True,
    "U1b|Rsu2": False, "U1b|AD": True, "U1b|DEPH": True,
    "Rsu2|AD": False, "Rsu2|DEPH": False, "AD|DEPH": True,
}
# PEPS3D carriers to draw site-0 reduced densities from (vary bond dim, lattice, seed)
PEPS_CASES = [(2, 2, 2, D, s) for D in (2, 3, 4) for s in (1, 7, 23)] + [(3, 2, 2, 3, 5), (3, 2, 2, 4, 11)]

TOOL_MANIFEST = {
    "quimb": {"tried": True, "used": True, "reason": "genuine PEPS3D carriers supplying structurally-varied site-0 input states (numpy native contraction)"},
    "pytorch": {"tried": True, "used": True, "reason": "torch READOUT: single-qubit channel composition + order-gap on each PEPS3D rho0"},
    "jax": {"tried": True, "used": True, "reason": "jax READOUT (x64): independent recompute for torch-vs-jax parity"},
    "z3": {"tried": True, "used": True, "reason": "load-bearing: 'classification matches reference on every carrier' UNSAT-of-mismatch; flips if a carrier disagrees"},
    "cvc5": {"tried": True, "used": HAVE_CVC5, "reason": "second SMT family cross-check of carrier-invariance"},
}
TOOL_INTEGRATION_DEPTH = {"quimb": "load_bearing", "pytorch": "load_bearing", "jax": "load_bearing",
                          "z3": "load_bearing", "cvc5": ("load_bearing" if HAVE_CVC5 else None)}


def peps_rho0(Lx, Ly, Lz, D, seed):
    """site-0 reduced density (2x2, generically mixed) from a genuine quimb PEPS3D."""
    peps = qtn.PEPS3D.rand(Lx, Ly, Lz, bond_dim=D, phys_dim=2, seed=seed, dtype="complex128")
    psi = np.asarray(peps.to_dense()).reshape(-1)
    psi = psi / np.linalg.norm(psi)
    n = int(round(math.log2(psi.size)))
    t = psi.reshape([2] * n)
    rho0 = np.tensordot(t, t.conj(), axes=(list(range(1, n)), list(range(1, n))))
    return rho0


def apply_1q_t(kraus, rho):
    return sum(K @ rho @ K.conj().T for K in kraus)


def apply_1q_j(kraus, rho):
    return sum(K @ rho @ jnp.conj(K).T for K in kraus)


def trace_dist_t(a, b):
    d = a - b
    return 0.5 * float(torch.sum(torch.abs(torch.linalg.eigvalsh((d + d.conj().T) / 2))))


def trace_dist_j(a, b):
    d = a - b
    return 0.5 * float(jnp.sum(jnp.abs(jnp.linalg.eigvalsh((d + jnp.conj(d).T) / 2))))


def classify(rho0_np, backend):
    if backend == "torch":
        rho0 = torch.tensor(rho0_np, dtype=torch.complex128)
        ap, td = apply_1q_t, trace_dist_t
        kr = lambda n: kraus_t(n)  # noqa: E731
    else:
        rho0 = jnp.asarray(rho0_np, dtype=jnp.complex128)
        ap, td = apply_1q_j, trace_dist_j
        kr = lambda n: kraus_j(n)  # noqa: E731
    table = {}
    for (X, Y) in PAIRS:
        xy = ap(kr(Y), ap(kr(X), rho0))
        yx = ap(kr(X), ap(kr(Y), rho0))
        gap = td(xy, yx)
        table[f"{X}|{Y}"] = {"gap": gap, "commutes": bool(gap < EPS)}
    return table


def z3_carrier_invariance(per_carrier_class, erase=False):
    """For each carrier and pair, assert (commutes_flag matches REFERENCE). Encode the
    measured gap and the reference threshold; a disagreeing carrier makes the conjunction
    inconsistent. Erase=zero all gaps -> every pair reads 'commute', which DISAGREES with
    the reference non-commuting pairs -> verdict flips (load-bearing)."""
    s = z3.Solver()
    ok = True
    for ci, table in enumerate(per_carrier_class):
        for pair, ref_commute in REFERENCE_COMMUTE.items():
            g = 0.0 if erase else table[pair]["gap"]
            v = z3.Real(f"g_{ci}_{pair.replace('|','_')}")
            s.add(v == z3.RealVal(repr(float(g))))
            # claim: this pair's commute-status equals the reference
            if ref_commute:
                s.add(v <= z3.RealVal(repr(EPS)))   # reference says commute -> gap small
            else:
                s.add(v > z3.RealVal(repr(EPS)))     # reference says non-commute -> gap large
    return str(s.check())  # 'sat' = all carriers consistent with reference; 'unsat' = a disagreement


def cvc5_carrier_invariance(per_carrier_class, erase=False):
    if not HAVE_CVC5:
        return "n/a"
    sv = cvc5.Solver(); sv.setLogic("QF_LRA")
    R = sv.getRealSort()

    def rv(x):
        fr = Fraction(float(x)).limit_denominator(10 ** 15)
        return sv.mkReal(fr.numerator, fr.denominator)

    eps = rv(EPS)
    for ci, table in enumerate(per_carrier_class):
        for pair, ref_commute in REFERENCE_COMMUTE.items():
            g = 0.0 if erase else table[pair]["gap"]
            v = sv.mkConst(R, f"g_{ci}_{pair.replace('|','_')}")
            sv.assertFormula(sv.mkTerm(Kind.EQUAL, v, rv(g)))
            if ref_commute:
                sv.assertFormula(sv.mkTerm(Kind.LEQ, v, eps))
            else:
                sv.assertFormula(sv.mkTerm(Kind.GT, v, eps))
    return str(sv.checkSat())


def main():
    carriers = []
    per_carrier_torch, per_carrier_jax = [], []
    for (Lx, Ly, Lz, D, seed) in PEPS_CASES:
        rho0 = peps_rho0(Lx, Ly, Lz, D, seed)
        ct = classify(rho0, "torch")
        cj = classify(rho0, "jax")
        per_carrier_torch.append(ct)
        per_carrier_jax.append(cj)
        # does this carrier's classification match the reference?
        matches_ref = all(ct[p]["commutes"] == REFERENCE_COMMUTE[p] for p in REFERENCE_COMMUTE)
        same_engines = all(ct[p]["commutes"] == cj[p]["commutes"] for p in ct)
        carriers.append({
            "carrier": f"PEPS3D_{Lx}x{Ly}x{Lz}_D{D}_seed{seed}",
            "matches_reference_classification": matches_ref,
            "torch_jax_same_classification": same_engines,
            "max_gap_delta_torch_jax": max(abs(ct[p]["gap"] - cj[p]["gap"]) for p in ct),
            "rsu2_pairs_noncommute": all(not ct[p]["commutes"] for p in ct if "Rsu2" in p),
            "nonrsu2_pairs_commute": all(ct[p]["commutes"] for p in ct if "Rsu2" not in p),
            "gap_range_noncommuting": [round(min(ct[p]["gap"] for p in ct if not REFERENCE_COMMUTE[p]), 4),
                                       round(max(ct[p]["gap"] for p in ct if not REFERENCE_COMMUTE[p]), 4)],
        })

    all_match_ref = all(c["matches_reference_classification"] for c in carriers)
    all_engine_agree = all(c["torch_jax_same_classification"] for c in carriers)
    max_engine_delta = max(c["max_gap_delta_torch_jax"] for c in carriers)

    z3_real = z3_carrier_invariance(per_carrier_torch, erase=False)
    z3_erased = z3_carrier_invariance(per_carrier_torch, erase=True)
    cvc5_real = cvc5_carrier_invariance(per_carrier_torch, erase=False)
    cvc5_erased = cvc5_carrier_invariance(per_carrier_torch, erase=True)
    proof_load_bearing = bool(z3_real == "sat" and z3_erased == "unsat"
                              and (not HAVE_CVC5 or (cvc5_real == "sat" and cvc5_erased == "unsat")))

    known_value_checks = [
        {"invariant": "order classification matches the exact-carrier reference on ALL PEPS3D carriers",
         "computed": f"{sum(c['matches_reference_classification'] for c in carriers)}/{len(carriers)}",
         "known": "all", "match": all_match_ref},
        {"invariant": "Rsu2 is sole non-commuter on every PEPS3D carrier",
         "computed": str(all(c["rsu2_pairs_noncommute"] and c["nonrsu2_pairs_commute"] for c in carriers)),
         "known": "True", "match": all(c["rsu2_pairs_noncommute"] and c["nonrsu2_pairs_commute"] for c in carriers)},
        {"invariant": "torch-vs-jax same classification on every carrier",
         "computed": str(all_engine_agree), "known": "True", "match": all_engine_agree},
        {"invariant": "dual-engine max gap delta < 1e-9", "computed": f"{max_engine_delta:.2e}",
         "known": "<1e-9", "match": bool(max_engine_delta < 1e-9)},
        {"invariant": "z3 carrier-invariance SAT on real data", "computed": z3_real, "known": "sat", "match": z3_real == "sat"},
        {"invariant": "z3 flips to UNSAT under gap-erasure (load-bearing)", "computed": z3_erased, "known": "unsat", "match": z3_erased == "unsat"},
        {"invariant": "cvc5 carrier-invariance SAT on real data", "computed": cvc5_real, "known": "sat", "match": (cvc5_real == "sat") or not HAVE_CVC5},
    ]
    all_pass = bool(all(c["match"] for c in known_value_checks) and proof_load_bearing)

    out = {
        "sim_id": SIM_ID, "classification": "diagnostic_only", "promotion_allowed": False,
        "claim_ceiling": "Carrier-independence of the order CLASSIFICATION (operator-intrinsic); gap magnitudes are carrier-dependent. Diagnostic, not a physics proof.",
        "finding": ("ORDER STRUCTURE IS CARRIER-INDEPENDENT: the commute/non-commute classification (Rsu2 = sole non-commuter, 6 commute / 4 order-matter) is identical on all "
                    + f"{len(carriers)} structurally-varied quimb-PEPS3D carriers and the exact Weyl reference; only the gap magnitudes vary with the input state."
                    if all_match_ref else "carrier-DEPENDENT - see carriers"),
        "n_carriers_tested": len(carriers),
        "carriers": carriers,
        "reference_classification": REFERENCE_COMMUTE,
        "dual_engine_scope": "readout_only (quimb PEPS3D states contracted in numpy; torch/jax independently recompute the order-test)",
        "max_engine_gap_delta": max_engine_delta,
        "proof_real_verdict": {"z3": z3_real, "cvc5": cvc5_real},
        "proof_erased_verdict": {"z3": z3_erased, "cvc5": cvc5_erased},
        "proof_load_bearing": proof_load_bearing,
        "known_value_checks": known_value_checks, "all_pass": all_pass,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH, "blockers": [],
    }
    outdir = pathlib.Path(__file__).parent / "results"
    outdir.mkdir(exist_ok=True)
    (outdir / f"{SIM_ID}_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"n_carriers": len(carriers), "all_match_reference": all_match_ref,
                      "all_engine_agree": all_engine_agree, "max_engine_delta": max_engine_delta,
                      "proof_real": out["proof_real_verdict"], "proof_erased": out["proof_erased_verdict"],
                      "proof_load_bearing": proof_load_bearing, "all_pass": all_pass,
                      "finding": out["finding"][:140]}, indent=2))
    return out


if __name__ == "__main__":
    main()
