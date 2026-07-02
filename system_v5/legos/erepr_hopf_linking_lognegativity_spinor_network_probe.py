#!/usr/bin/env python3
"""ER=EPR geometry-as-information probe (owner-corrected, 2026-06-01): the Hopf-fibration LINKING of a finite
spinor network read out as A-C LOG-NEGATIVITY -- the genuine quantum entanglement that, in ER=EPR, IS the
Einstein-Rosen bridge / spacetime connection.

Owner doctrine: spacetime IS entropy/information; |00>+|11> (EPR) is how spacetime entangles (ER=EPR,
Maldacena-Susskind). So the EPR/Bell pair is the spacetime-connection UNIT, not a classical artifact. The error
in the earlier attempt was READING the EPR linking with I(A:C|B) (which has a classical analog), and the
over-correction (noncommuting iSWAP gates) broke the construction. The fix keeps the EPR pairs and reads the
linking with LOG-NEGATIVITY.

LOAD-BEARING (pure QIT, no classical analog): LN(A:C) = log2(||rho_AC^{T_C}||_1). Exactly 0 for EVERY separable
state (classical or quantum); >0 only for genuine A-C entanglement (the direct ER=EPR bridge). Verified:
  LINKED (direct A-C EPR) -> LN=1 ; TRIVIAL (A-B-C chain) -> 0 ; PRODUCT -> 0 ; DEPHASED linked -> 0.

ROOT CONSTRAINTS / admissibility:
  F01 finite: finite spinor network, finite regions, finite-dim densities.
  N01 / pure-QIT: the signal is genuine quantum entanglement that DIES under DEPHASING (a commuting/classical
      operation) -- 'tested against commuting/product/gauge negatives' per the owner's admission rule. A classical
      correlation would survive dephasing; this does not, so there is no classical-Markov smuggle.
Candidates KEPT SEPARATE (owner's rule): LN(A:C) [load-bearing], with I(A:C|B) and I3 reported as separate
flagged columns (classical shadow -> not load-bearing). formal_scout, promotion_allowed=false;
primary object = finite retrocausal possibility field.
"""
from __future__ import annotations
import json, math, time
import numpy as np

NAME = "erepr_hopf_linking_lognegativity_spinor_network_probe"
RESULT_DIR = __import__("pathlib").Path(__file__).resolve().parent / "results"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = ("ER=EPR geometry-as-information probe: Hopf LINKING of fiber regions read out as A-C log-negativity "
                 "(the genuine quantum entanglement = ER bridge). Linked (direct EPR) -> LN(A:C)>0; trivial chain "
                 "-> 0; product -> 0; DEPHASED -> 0 (pure-QIT: kills the quantum signal). I(A:C|B)/I3 kept separate, "
                 "not load-bearing. promotion_allowed=false; primary object = finite retrocausal possibility field.")
SCALE_GRID = [
    {"name": "small",  "n_reg": 2, "n_blocks": 1},   # 6 qubits
    {"name": "medium", "n_reg": 2, "n_blocks": 2},   # 12 qubits
]
BLOCKED_CONSUMERS = ["layer_stacking", "flux", "Xi/Phi0", "Axis0", "physics/gravity", "final_manifold", "official_g_structure_selection", "Holodeck/FEP"]
LN_MIN = 0.05
SEP_MAX = 1e-9


def vn(rho):
    ev = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T)); ev = ev[ev > 1e-12]
    return float(-np.sum(ev * np.log2(ev)))


def rdm(psi, keep, n):
    """Reduced density on `keep` from the STATEVECTOR (forms only the 2^|keep| x 2^|keep| matrix). The qubit
    ORDER of `keep` is PRESERVED (not sorted), so callers can pass [A..., C...] and the A|C split is correct."""
    keep = list(keep); tr = [i for i in range(n) if i not in keep]
    t = np.transpose(psi.reshape([2] * n), keep + tr).reshape(2 ** len(keep), 2 ** len(tr))
    return t @ t.conj().T


def rdm_dephased(psi, keep, n):
    """Reduced density of the FULLY-DEPHASED (diagonal/classical) global state, from |psi|^2. Diagonal/classical."""
    p = np.abs(psi) ** 2
    keep = list(keep); tr = [i for i in range(n) if i not in keep]
    t = np.transpose(p.reshape([2] * n), keep + tr).reshape(2 ** len(keep), 2 ** len(tr))
    return np.diag(t.sum(axis=1)).astype(complex)


def log_neg_rdm(rho, dA, dC):
    pt = rho.reshape(dA, dC, dA, dC).transpose(0, 3, 2, 1).reshape(dA * dC, dA * dC)
    ev = np.linalg.eigvalsh(0.5 * (pt + pt.conj().T))
    return float(np.log2(np.sum(np.abs(ev))))


def _S(psi, keep, n, deph):
    if len(keep) >= n:                                  # whole system: avoid forming the full 2^n density
        if deph:
            p = np.abs(psi) ** 2; p = p[p > 1e-12]; return float(-np.sum(p * np.log2(p)))
        return 0.0                                       # pure global state -> S=0
    return vn(rdm_dephased(psi, keep, n) if deph else rdm(psi, keep, n))


def log_neg(psi, A, C, n, deph=False):
    rho = rdm_dephased(psi, A + C, n) if deph else rdm(psi, A + C, n)
    return log_neg_rdm(rho, 2 ** len(A), 2 ** len(C))


def cmi(psi, A, B, C, n, deph=False):
    return _S(psi, A + B, n, deph) + _S(psi, B + C, n, deph) - _S(psi, B, n, deph) - _S(psi, A + B + C, n, deph)


def mutual(psi, X, Y, n, deph=False):
    return _S(psi, X, n, deph) + _S(psi, Y, n, deph) - _S(psi, X + Y, n, deph)


def tripartite(psi, A, B, C, n, deph=False):
    return mutual(psi, A, B, n, deph) + mutual(psi, A, C, n, deph) - mutual(psi, A, B + C, n, deph)


def two_bell(i, j, k, l, n):
    """Two EPR/Bell pairs (i,j) and (k,l): |00>+|11> on each (the ER=EPR spacetime-entanglement units)."""
    v = np.zeros([2] * n, dtype=complex)
    for a in (0, 1):
        for b in (0, 1):
            idx = [0] * n; idx[i] = idx[j] = a; idx[k] = idx[l] = b; v[tuple(idx)] += 1.0
    return (v.reshape(-1)) / 2.0


def regions(n_reg, base=0):
    A = [base + i for i in range(0, n_reg)]; B = [base + i for i in range(n_reg, 2 * n_reg)]
    C = [base + i for i in range(2 * n_reg, 3 * n_reg)]; return A, B, C


def linked_block(n_reg):
    """Hopf-LINKED: bell(A1,C0) directly EPR-links A<->C (the ER bridge bypassing B) + bell(A0,B0)."""
    n = 3 * n_reg; A, B, C = regions(n_reg)
    return two_bell(A[-1], C[0], A[0], B[0], n)


def trivial_block(n_reg):
    """MATCHED trivial: bell(A0,B0) + bell(B1,C0) -- a chain A-B-C, same two EPR pairs, A and C NOT directly linked."""
    n = 3 * n_reg; A, B, C = regions(n_reg)
    return two_bell(A[0], B[0], B[1], C[0], n)


def tensor(states):
    v = states[0]
    for s in states[1:]:
        v = np.kron(v, s)
    return v


def canonical_self_tests():
    """Baked-in: a direct EPR pair has LN=1; a chain (A-B + B-C) has LN(A:C)=0; product has LN=0; dephased EPR has LN=0."""
    n = 6; A, B, C = [0, 1], [2, 3], [4, 5]
    lk = linked_block(2); tv = trivial_block(2); pr = np.eye(64)[0].astype(complex)
    ln_lk = log_neg(lk, A, C, n); ln_tv = log_neg(tv, A, C, n); ln_pr = log_neg(pr, A, C, n)
    ln_dp = log_neg(lk, A, C, n, deph=True)
    return {"LN_linked": ln_lk, "LN_trivial": ln_tv, "LN_product": ln_pr, "LN_dephased": ln_dp,
            "pass": bool(ln_lk > 0.5 and abs(ln_tv) < 1e-9 and abs(ln_pr) < 1e-9 and abs(ln_dp) < 1e-9)}


def scale_row(g):
    nr = g["n_reg"]; nb = g["n_blocks"]; nblock = 3 * nr; n = nblock * nb
    linked = tensor([linked_block(nr)] * nb); trivial = tensor([trivial_block(nr)] * nb)
    prod = np.zeros(2 ** n, complex); prod[0] = 1.0
    A = [b * nblock + i for b in range(nb) for i in range(0, nr)]
    B = [b * nblock + i for b in range(nb) for i in range(nr, 2 * nr)]
    C = [b * nblock + i for b in range(nb) for i in range(2 * nr, 3 * nr)]
    def cols(psi, deph=False):
        return {"LN_AC": log_neg(psi, A, C, n, deph), "I_ACgivenB_classical_shadow": cmi(psi, A, B, C, n, deph), "I3": tripartite(psi, A, B, C, n, deph)}
    link = cols(linked); triv = cols(trivial); prd = cols(prod); deph = cols(linked, deph=True)
    ent_link = sum(vn(rdm(linked, [q], n)) for q in range(n)); ent_triv = sum(vn(rdm(trivial, [q], n)) for q in range(n))
    self_tests = canonical_self_tests()
    linking = link["LN_AC"] > LN_MIN
    geometry_kill = abs(triv["LN_AC"]) < SEP_MAX
    info_kill = abs(prd["LN_AC"]) < SEP_MAX
    dephasing_kills = abs(deph["LN_AC"]) < SEP_MAX
    ent_matched = abs(ent_link - ent_triv) < 1e-6
    row_pass = bool(linking and geometry_kill and info_kill and dephasing_kills and ent_matched and self_tests["pass"])
    return {"pass": row_pass, "scale_name": g["name"], "n_qubits": n, "geometry_scale": {"n_reg": nr, "n_blocks": nb, "n_qubits": n},
            "linked": link, "trivial_matched": triv, "product": prd, "dephased_linked": deph,
            "total_entanglement_linked": ent_link, "total_entanglement_trivial": ent_triv,
            "root_constraints": {"F01_finite": True, "N01_pure_qit_dies_under_dephasing": bool(dephasing_kills)},
            "canonical_self_tests": self_tests,
            "controls": {
                "linking_lognegativity_AC_positive": {"pass": bool(linking), "LN_AC": link["LN_AC"], "note": "direct A-C EPR = the ER bridge = genuine quantum entanglement"},
                "geometry_kill_matched_trivial_chain": {"pass": bool(geometry_kill), "LN_AC": triv["LN_AC"], "note": "A-C correlation routed through B -> A,C separable -> LN=0; same total entanglement, only linking removed"},
                "info_kill_product": {"pass": bool(info_kill), "LN_AC": prd["LN_AC"]},
                "dephasing_commuting_negative_kills_signal": {"pass": bool(dephasing_kills), "LN_AC": deph["LN_AC"], "note": "PURE-QIT: dephasing (classical/commuting) destroys the EPR link -> LN=0; a classical correlation would survive. No classical smuggle."},
                "entanglement_amount_matched": {"pass": bool(ent_matched), "linked": ent_link, "trivial": ent_triv},
                "canonical_state_self_tests": {"pass": bool(self_tests["pass"]), **self_tests},
            }}


def main():
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [scale_row(g) for g in SCALE_GRID]
    min_ln = min(r["linked"]["LN_AC"] for r in rows)
    max_triv = max(abs(r["trivial_matched"]["LN_AC"]) for r in rows)
    max_deph = max(abs(r["dephased_linked"]["LN_AC"]) for r in rows)
    required = {
        "rows_pass": all(r["pass"] for r in rows),
        "linking_lognegativity_pass": min_ln > LN_MIN,
        "geometry_kill_matched_pass": max_triv < SEP_MAX,
        "info_kill_product_pass": all(r["controls"]["info_kill_product"]["pass"] for r in rows),
        "dephasing_pure_qit_pass": max_deph < SEP_MAX,
        "entanglement_matched_pass": all(r["controls"]["entanglement_amount_matched"]["pass"] for r in rows),
        "canonical_self_tests_pass": all(r["controls"]["canonical_state_self_tests"]["pass"] for r in rows),
    }
    all_pass = bool(all(required.values()))
    result = {
        "schema": "LEGO_RESULT_v1", "name": NAME, "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED, "claim_ceiling": CLAIM_CEILING,
        "carrier_role": "object_load_bearing",
        "carrier_role_note": "ER=EPR: the EPR/Bell pair IS the spacetime connection; the Hopf LINKING of fiber regions is read out as A-C log-negativity (genuine quantum entanglement, the ER bridge). Geometry-kill (route through B), info-kill (product), AND dephasing/commuting negative all -> 0. Pure QIT: log-neg=0 for all separable/classical, signal dies under dephasing. I(A:C|B)/I3 kept separate (classical shadow, not load-bearing).",
        "math_object": "A-C log-negativity of three fiber regions of a finite spinor network; nonzero iff the fibers are directly EPR-linked (the ER=EPR bridge); 0 for matched unlinked chain, product, and dephased; I(A:C|B), I3 separate columns",
        "root_constraints": {"F01": "finite spinor network, finite regions, finite-dim densities",
                             "N01_pure_qit": "the signal is genuine quantum entanglement (log-negativity) that DIES under dephasing (a commuting/classical operation); a classical correlation would survive -> no classical-Markov smuggle"},
        "admissibility": "finite-dim, density-matrix-native, basis/gauge-safe, capacity-bounded, tested against matched-trivial + product + DEPHASING(commuting) negatives -- per owner's admission rule; load-bearing measure LN(A:C) has NO classical analog",
        "candidates_kept_separate": ["log_negativity(A:C) [load-bearing]", "I(A:C|B) [classical shadow]", "I3 [classical shadow]"],
        "required": required, "rows": rows, "blocked_consumers": BLOCKED_CONSUMERS,
        "summary": {"all_pass": all_pass, "promotion_allowed": PROMOTION_ALLOWED, "elapsed_seconds": round(time.time() - started, 4),
                    "scale_grid": [{"name": r["scale_name"], **r["geometry_scale"]} for r in rows],
                    "max_n_qubits": max(r["n_qubits"] for r in rows), "carrier_role": "object_load_bearing",
                    "min_linked_LN_AC": min_ln, "max_trivial_LN_AC": max_triv, "max_dephased_LN_AC": max_deph,
                    "canonical_self_tests_pass": all(r["controls"]["canonical_state_self_tests"]["pass"] for r in rows)}}
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, default=float) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True, default=float))
    return result


if __name__ == "__main__":
    res = main()
    raise SystemExit(0 if res["summary"]["all_pass"] else 1)
