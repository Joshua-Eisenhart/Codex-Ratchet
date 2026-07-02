#!/usr/bin/env python3
# POPPER LANE — DECISIVE FALSIFIER for "geometric linking number k == entanglement (log-negativity)".
#
# Target claim (under attack): on a (1,k)-torus-link carrier, if you ENTANGLE a Bell-pair (CNOT) at every
# geometric CROSSING of the link diagram and measure A-C log-negativity, the log-negativity equals the
# TOPOLOGICAL linking number k.
#
# Skeptical hypothesis (this lane's default): log-negativity on the naive crossings-entangling construction
# tracks the CROSSING COUNT of the chosen diagram, NOT the topological invariant k. The two coincide only on
# the minimal diagram, so the equality is a planted coincidence of one particular diagram, not a topological
# identity.
#
# DECISIVE FALSIFIER (Reidemeister-I): add a kink (R-I) to the diagram. An R-I move adds a crossing to the
# DIAGRAM (the writhe changes) but does NOT change the link's topological linking number k. A GENUINE
# topological identity must be INVARIANT under R-I. A crossing-count artifact is NOT.
#
# Exact fact used (verified numerically below, then applied analytically): the A-C log-negativity of n
# INDEPENDENT Bell pairs (one entangled crossing each) is exactly n. So "LN at entangled crossings" equals
# the number of entangled crossings. Therefore:
#   (a) minimal (1,k) diagram: entangled crossings = k -> LN = k.   <-- the planted coincidence
#   (b) +R-I kink:  entangled crossings = k+1, k+2, ...  while topological k is UNCHANGED -> LN = k+1, k+2 != k.
# => the equality LN==k is BROKEN by an R-I move that leaves k fixed. LN tracks crossing count, not k.
#
# What would SAVE the claim: a construction whose entangling pattern is provably R-I-INVARIANT (entangle on a
# diagram invariant such as the Gauss linking integral / writhe-corrected linking, not raw crossings) AND
# which shows LN CONSTANT under the R-I kink. codex2 must EXHIBIT such a construction to move the verdict off
# 'crossing-count-only'.

import json, os
import numpy as np

# ---------- verify, ONCE and cheaply, the exact fact LN(1 Bell pair) = 1 (so n pairs -> n by additivity) ----
def bell_pair_log_negativity():
    # |Phi+> = (|00> + |11>)/sqrt2 ; rho_AB ; partial transpose on B ; LN = log2(sum|eigs|)
    psi = np.array([1, 0, 0, 1], dtype=float) / np.sqrt(2)          # over qubits (A,B)
    rho = np.outer(psi, psi)                                        # 4x4 = (A,B)(A,B)
    rho = rho.reshape(2, 2, 2, 2)                                   # axes: Aket, Bket, Abra, Bbra
    rho_pt = np.transpose(rho, (0, 3, 2, 1)).reshape(4, 4)         # partial transpose on B (swap Bket<->Bbra)
    ev = np.linalg.eigvalsh(0.5 * (rho_pt + rho_pt.T))
    return float(np.log2(np.sum(np.abs(ev))))

# log-negativity is ADDITIVE over a tensor product of independent entangled pairs:
#   LN(rho1 (x) rho2) = LN(rho1) + LN(rho2).  Each entangled crossing contributes one Bell pair -> +1.
def naive_LN_at_crossings(n_entangled_crossings, ln_per_pair):
    return n_entangled_crossings * ln_per_pair

# ---------- topology side ----------
def linking_number_topological(k):
    # (1,k) torus link: core circle is linked k times. Topological linking number = k, by definition,
    # independent of cosmetic diagram crossings. This is a Reidemeister invariant.
    return k

def diagram_crossings_after_RI(k, n_kinks):
    # minimal (1,k) diagram has k essential crossings; each Reidemeister-I kink adds 1 cosmetic crossing.
    return k + n_kinks

def main():
    LN_PAIR = bell_pair_log_negativity()
    assert abs(LN_PAIR - 1.0) < 1e-9, f"sanity: Bell-pair LN should be 1, got {LN_PAIR}"

    rows = []
    KILLED = False
    for k in [1, 2, 3, 4, 5]:
        n_min = diagram_crossings_after_RI(k, 0)                 # minimal diagram crossings = k
        ln_min = naive_LN_at_crossings(n_min, LN_PAIR)          # naive LN on minimal diagram
        ktop = linking_number_topological(k)

        ri_results = []
        for nk in [1, 2, 3]:
            n_kinked = diagram_crossings_after_RI(k, nk)         # crossings grow with the kink
            ln_kinked = naive_LN_at_crossings(n_kinked, LN_PAIR) # naive LN follows crossings
            ln_eq_k = abs(ln_kinked - ktop) < 1e-9               # does LN still equal topological k?
            ri_results.append({
                "n_kinks": nk,
                "diagram_crossings": n_kinked,
                "topological_k": ktop,                # INVARIANT under R-I
                "naive_LN": round(ln_kinked, 6),      # NOT invariant — grows with crossings
                "LN_equals_k": ln_eq_k,
                "LN_equals_crossing_count": abs(ln_kinked - n_kinked) < 1e-9,
            })
            if not ln_eq_k:
                KILLED = True   # an R-I move that holds k fixed but moves LN -> identity falsified

        rows.append({
            "k": k,
            "minimal_diagram_crossings": n_min,
            "topological_linking_k": ktop,
            "naive_LN_minimal": round(ln_min, 6),
            "minimal_LN_equals_k": abs(ln_min - ktop) < 1e-9,   # coincidence holds ONLY on minimal diagram
            "after_reidemeister_I": ri_results,
        })

    verdict = {
        "lane": "popper",
        "target_claim": "geometric linking number k == entanglement log-negativity, as a TOPOLOGICAL identity",
        "construction_under_attack": "entangle one Bell pair (CNOT) at each geometric crossing of the (1,k) diagram",
        "exact_fact": f"log-negativity of one Bell pair = {LN_PAIR} (verified); additive -> n pairs give LN=n",
        "falsifier": "Reidemeister-I kink: adds a diagram crossing, leaves topological linking number k fixed",
        "predicted_result": "naive LN grows with crossings (LN = k + n_kinks) while k is constant -> LN != k",
        "minimal_coincidence": "LN == k holds ONLY on the minimal diagram, where #crossings happens to equal k",
        "classification": "crossing-count-only (planted coincidence on the minimal diagram)",
        "claim_status": "KILLED" if KILLED else "SURVIVED",
        "what_would_save_it": "exhibit a construction whose entangling pattern is R-I-INVARIANT (entangle on a "
                              "diagram invariant such as the Gauss linking integral / writhe-corrected linking, "
                              "not raw crossings) AND show LN constant under the R-I kink",
        "codex2_kill_signal": "if codex2's crossings-construction shows log-negativity INCREASE under an R-I "
                              "kink while k is held fixed -> identity is KILLED, demoted to crossing-count",
        "codex2_save_signal": "if codex2 exhibits an R-I-invariant entangling rule and LN stays == k across "
                              "kinks AND across distinct diagrams of the same (1,k) link -> survives this lane",
        "rows": rows,
    }
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "popper_reidemeister_kill_control_results.json")
    with open(out, "w") as f:
        json.dump(verdict, f, indent=2)

    print("=== POPPER REIDEMEISTER-I KILL CONTROL ===")
    print(f"Bell-pair log-negativity (verified) = {LN_PAIR}")
    for r in rows:
        print(f"\nk={r['k']}  topological_linking_k={r['topological_linking_k']}  "
              f"minimal_diagram_crossings={r['minimal_diagram_crossings']}  "
              f"naive_LN_minimal={r['naive_LN_minimal']}  (LN==k on minimal: {r['minimal_LN_equals_k']})")
        for ri in r["after_reidemeister_I"]:
            print(f"   +{ri['n_kinks']} R-I kink(s): diagram_crossings={ri['diagram_crossings']}  "
                  f"topological_k={ri['topological_k']}  naive_LN={ri['naive_LN']}  "
                  f"LN==k? {ri['LN_equals_k']}   LN==crossing_count? {ri['LN_equals_crossing_count']}")
    print(f"\nCLAIM STATUS: {verdict['claim_status']}  ({verdict['classification']})")
    print(f"written: {out}")

if __name__ == "__main__":
    main()
