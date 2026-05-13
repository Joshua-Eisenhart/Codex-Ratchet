#!/usr/bin/env python3
"""
Szilard distinguishability admission-floor fence
================================================
Classification: tool_lego_fit_probe

This sim is a bounded one-bit numeric/z3 fence. It maps a classical
Szilard-Landauer bookkeeping tuple into declared admission-floor variables
and checks only that the stated arithmetic constraints are internally
consistent. It does not admit a bridge, engine, QIT, GStack, axis, or
nonclassical claim.

Nominalist framing (required by project doctrine):
  - Distinguishability is not "fuel"; it is the probe-relative admission
    condition for a bit of record to persist on the memory carrier.
  - Measurement is not "information acquisition"; it is the admission gate
    that couples the memory shell to the system shell on exactly those
    probe-relative distinctions that survive.
  - Landauer erasure is not "a cost we pay"; it is the F01 floor below
    which an erase-step is inadmissible (a non-existent operation on the
    constraint manifold, not an expensive one).

The bridge is operationalized with a small set of identifications:
  - D  : one-bit distinguishability admitted by measurement (nats)
  - G  : admission-gate coupling strength  (open = 1, closed = 0)
  - E  : erasure step's record-removal magnitude (nats)
  - F01: floor below which erasure-without-record is inadmissible
           (encoded as F01 = T * D, the Landauer floor in this row)
  - dF : system free-energy gain extractable from the admitted record

Load-bearing fence (z3):
  The pass gate requires z3 to certify that the forbidden region
    "a record was admitted (D > 0, G = 1) AND the record was
     subsequently erased without paying the floor (E < F01)"
  is UNSAT under the declared admission-floor axioms.

Counterpart numeric check: the measured row from the Szilard-Landauer
cycle is re-derived here (one-bit ideal case) and passed into the z3
solver so the fence is anchored to the same numeric tuple as the
classical one-bit row.
"""

import json
import pathlib

import numpy as np

classification = "tool_lego_fit_probe"
DEMOTE_REASON = (
    "No promotion from this receipt: it is a one-bit numeric/z3 "
    "admission-floor consistency fence only."
)


LN2 = float(np.log(2.0))
EPS = 1e-10

CLASSIFICATION = classification
CLASSIFICATION_NOTE = (
    "Tool-lego fit probe: maps classical one-bit Szilard-Landauer "
    "bookkeeping (mutual information / free-energy / erasure cost) onto "
    "declared distinguishability/admission-floor variables and checks the "
    "local z3 constraints. This is not bridge, QIT, GStack, axis, runtime-"
    "engine, or nonclassical admission evidence."
)

LEGO_IDS = [
    "quantum_thermodynamics",
    "channel_cptp_map",
    "constraint_admissibility",
    "f01_floor",
]

PRIMARY_LEGO_IDS = [
    "constraint_admissibility",
]

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": "2-qubit bookkeeping row uses numpy; no gradient surface needed for the bridge"},
    "pyg":       {"tried": False, "used": False, "reason": "no graph carrier in this bridge row"},
    "z3":        {"tried": True, "used": True, "reason": (
        "Encodes the declared one-bit admission-floor constraints "
        "(F01 = T*D, dF<=E, admission-gated floor), rejects the declared "
        "forbidden region (admitted AND Ev < F01), and checks a no-admission "
        "independence row."
    )},
    "cvc5":      {"tried": False, "used": False, "reason": "z3 already covers the Real-arithmetic admission encoding"},
    "sympy":     {"tried": False, "used": False, "reason": "closed-form one-bit values are numeric-exact; no symbolic step needed"},
    "clifford":  {"tried": False, "used": False, "reason": "no geometric-algebra carrier in this bridge row"},
    "geomstats": {"tried": False, "used": False, "reason": "no manifold carrier in this bridge row"},
    "e3nn":      {"tried": False, "used": False, "reason": "no equivariant representation in this bridge row"},
    "rustworkx": {"tried": False, "used": False, "reason": "no graph carrier"},
    "xgi":       {"tried": False, "used": False, "reason": "no hypergraph carrier"},
    "toponetx":  {"tried": False, "used": False, "reason": "no cell complex carrier"},
    "gudhi":     {"tried": False, "used": False, "reason": "no persistence computation"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": "load_bearing",
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


# ---------------------------------------------------------------------------
# Numeric anchor: one-bit Szilard measurement row (re-derived minimally here)
# ---------------------------------------------------------------------------

def one_bit_szilard_anchor(temperature: float = 1.0) -> dict:
    """Re-derive the ideal one-bit Szilard measurement numbers so this sim
    does not depend on importing the companion cycle sim. Values match the
    classical row: I = dF = E = T * ln2."""
    KET0 = np.array([[1.0], [0.0]], dtype=complex)
    PROJ0 = KET0 @ KET0.conj().T
    rho_s = 0.5 * np.eye(2, dtype=complex)
    rho_m = PROJ0
    rho_init = np.kron(rho_s, rho_m)
    cnot = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0],
                     [0, 0, 0, 1],
                     [0, 0, 1, 0]], dtype=complex)
    rho_measured = cnot @ rho_init @ cnot.conj().T

    def entropy(rho):
        evals = np.linalg.eigvalsh((rho + rho.conj().T) / 2)
        evals = evals[evals > 1e-15]
        return float(-np.sum(evals * np.log(evals))) if len(evals) else 0.0

    def ptrace_mem(rho_sm):
        r = rho_sm.reshape(2, 2, 2, 2)
        return np.trace(r, axis1=1, axis2=3)

    def ptrace_sys(rho_sm):
        r = rho_sm.reshape(2, 2, 2, 2)
        return np.trace(r, axis1=0, axis2=2)

    S_s = entropy(ptrace_mem(rho_measured))
    S_m = entropy(ptrace_sys(rho_measured))
    S_sm = entropy(rho_measured)
    D = S_s + S_m - S_sm  # mutual information = distinguishability bit
    # In the idealized one-bit row, dF = T*D and E = T*D.
    dF = temperature * D
    E = temperature * D
    return {
        "temperature": temperature,
        "D_nats": D,
        "dF": dF,
        "E": E,
        "expected_ln2": LN2,
    }


# ---------------------------------------------------------------------------
# z3 bridge proof (load-bearing)
# ---------------------------------------------------------------------------

def z3_admission_bridge_proof(D_nats: float, dF: float, E: float,
                               temperature: float) -> dict:
    """Load-bearing z3 check for the one-bit admission-floor fence.

    Real variables:
      D   : distinguishability admitted by measurement (nats)
      G   : admission-gate (0 = closed, 1 = open); encoded as Real in [0,1]
      F01 : floor = T * D  (Landauer floor in this local arithmetic row)
      dF  : system free-energy gain
      E   : erasure cost / record-removal magnitude
      T   : reservoir temperature

    Declared fence axioms:
      A1  (measurement-as-admission): a record is admitted iff G = 1 AND D > 0
      A2  (F01 floor):                F01 = T * D
      A3  (demon inequality):         dF <= E
      A4  (admission monotonicity):   if G = 1 AND D > 0 then E >= F01

    Positive: the measured tuple (D, dF, E, T) + axioms is SAT with G=1.
    Negative (primary, load-bearing):
      "record admitted AND erasure strictly below floor" is UNSAT under
      the declared axioms.
    Counterfactual:
      "record admitted AND erasure completely free (E = 0)" is UNSAT,
      proving the floor is load-bearing (not vacuous at zero).
    Independence check (must be SAT):
      "no record admitted (G = 0)" -> erasure cost is unconstrained, so
      E = 0 is SAT. This confirms the forbidden region is gated by
      admission, not global.
    """
    import z3

    TOL = 1e-9
    SLACK = 10 * TOL

    D   = z3.Real("D")
    G   = z3.Real("G")
    F01 = z3.Real("F01")
    dFv = z3.Real("dFv")
    Ev  = z3.Real("Ev")
    T   = z3.Real("T")

    measured = z3.And(
        D >= D_nats - TOL,  D <= D_nats + TOL,
        T >= temperature - TOL, T <= temperature + TOL,
        dFv >= dF - TOL,    dFv <= dF + TOL,
        Ev >= E - TOL,      Ev <= E + TOL,
    )
    axioms = z3.And(
        F01 == T * D,
        dFv <= Ev,
        G >= 0, G <= 1,
    )
    admitted = z3.And(G == 1, D > 0)
    floor_rule = z3.Implies(admitted, Ev >= F01)

    # Positive
    s_pos = z3.Solver()
    s_pos.add(measured, axioms, floor_rule, G == 1)
    pos_res = s_pos.check()
    pos_sat = pos_res == z3.sat

    # Negative (load-bearing): admitted AND Ev < F01 - SLACK is UNSAT
    s_neg = z3.Solver()
    s_neg.add(measured, axioms, floor_rule, admitted)
    s_neg.add(Ev < F01 - SLACK)
    neg_res = s_neg.check()
    neg_unsat = neg_res == z3.unsat

    # Counterfactual: admitted AND Ev = 0 (free erasure) is UNSAT, with a
    # nontrivial one-bit admission (D >= ln2 - TOL). Do NOT anchor to the
    # measured Ev here -- this is the hypothetical.
    D2   = z3.Real("D2")
    Ev2  = z3.Real("Ev2")
    T2   = z3.Real("T2")
    F012 = z3.Real("F012")
    G2   = z3.Real("G2")
    s_cf = z3.Solver()
    s_cf.add(
        T2 >= temperature - TOL, T2 <= temperature + TOL,
        D2 >= LN2 - TOL,
        F012 == T2 * D2,
        G2 == 1,
        Ev2 >= -TOL, Ev2 <= TOL,        # erasure essentially free
        z3.Implies(z3.And(G2 == 1, D2 > 0), Ev2 >= F012),
    )
    cf_res = s_cf.check()
    cf_unsat = cf_res == z3.unsat

    # Independence: no record admitted (G = 0) -> E = 0 is SAT, proving the
    # forbidden region is specifically gated by admission.
    D3   = z3.Real("D3")
    Ev3  = z3.Real("Ev3")
    T3   = z3.Real("T3")
    F013 = z3.Real("F013")
    G3   = z3.Real("G3")
    s_ind = z3.Solver()
    s_ind.add(
        T3 >= temperature - TOL, T3 <= temperature + TOL,
        D3 >= -TOL, D3 <= TOL,           # D = 0
        F013 == T3 * D3,
        G3 == 0,
        Ev3 >= -TOL, Ev3 <= TOL,
        z3.Implies(z3.And(G3 == 1, D3 > 0), Ev3 >= F013),
    )
    ind_res = s_ind.check()
    ind_sat = ind_res == z3.sat

    return {
        "positive_sat":                       pos_sat,
        "positive_result":                    str(pos_res),
        "negative_admission_floor_unsat":     neg_unsat,
        "negative_result":                    str(neg_res),
        "counterfactual_free_erasure_unsat":  cf_unsat,
        "counterfactual_result":              str(cf_res),
        "independence_no_admission_sat":      ind_sat,
        "independence_result":                str(ind_res),
        "pass": bool(pos_sat and neg_unsat and cf_unsat and ind_sat),
        "note": (
            "z3 is load-bearing for this local fence: the declared forbidden "
            "region (admitted AND Ev < F01) is UNSAT under the stated "
            "admission-floor axioms. The independence SAT row gates the "
            "forbidden region to the admission branch, preventing a vacuous "
            "global constraint."
        ),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    temperature = 1.0
    anchor = one_bit_szilard_anchor(temperature=temperature)
    D = anchor["D_nats"]
    dF = anchor["dF"]
    E = anchor["E"]

    # --- Positive tests (numeric anchor) ---------------------------------
    positive = {
        "measurement_admits_exactly_one_bit_of_distinguishability": {
            "D_nats": D,
            "expected_ln2": LN2,
            "pass": abs(D - LN2) < 1e-9,
        },
        "f01_floor_equals_T_times_D_in_the_one_bit_row": {
            "F01": temperature * D,
            "T_times_D": temperature * D,
            "expected_T_ln2": temperature * LN2,
            "pass": abs((temperature * D) - (temperature * LN2)) < 1e-12,
        },
        "demon_inequality_holds_as_equality_in_ideal_one_bit_row": {
            "dF": dF,
            "E": E,
            "pass": abs(dF - E) < 1e-9,
        },
    }

    # --- z3 load-bearing proof -------------------------------------------
    proof = z3_admission_bridge_proof(
        D_nats=D, dF=dF, E=E, temperature=temperature,
    )

    negative = {
        "free_erasure_of_admitted_record_is_inadmissible_unsat": {
            "admission_floor_unsat":       proof["negative_admission_floor_unsat"],
            "counterfactual_free_erasure": proof["counterfactual_free_erasure_unsat"],
            "pass": bool(
                proof["negative_admission_floor_unsat"]
                and proof["counterfactual_free_erasure_unsat"]
            ),
        },
        "admission_independence_is_not_vacuous": {
            "no_admission_sat": proof["independence_no_admission_sat"],
            "pass": bool(proof["independence_no_admission_sat"]),
        },
    }

    boundary = {
        "bridge_anchored_numerically_to_one_bit_szilard_row": {
            "D_nats": D, "dF": dF, "E": E,
            "pass": (
                abs(D - LN2) < 1e-9
                and abs(dF - LN2) < 1e-9
                and abs(E - LN2) < 1e-9
            ),
        },
        "z3_proof_block_reports_pass": {
            "pass": proof["pass"],
        },
    }

    all_pass = (
        all(v["pass"] for v in positive.values())
        and all(v["pass"] for v in negative.values())
        and all(v["pass"] for v in boundary.values())
    )

    results = {
        "name": "szilard_distinguishability_admission_bridge",
        "classification": CLASSIFICATION,
        "all_pass": all_pass,
        "promotion_allowed": False,
        "demote_reason": DEMOTE_REASON,
        "claim_ceiling": (
            "one-bit numeric/z3 admission-floor consistency fence only; no "
            "bridge, QIT, GStack, axis, nonclassical, runtime-engine, or "
            "cycle admission"
        ),
        "next_lego_target": "one-bit measurement/erasure calibration support only",
        "promotion_condition": (
            "No promotion from this receipt; downstream cycle or bridge work "
            "requires exact dynamics, coupling/coexistence receipts, physical "
            "graveyards, and independent admission."
        ),
        "demotion_condition": (
            "Demote if the z3 independence row fails, if the one-bit numeric "
            "anchor diverges from ln2, or if this receipt is used as bridge, "
            "QIT, GStack, axis, runtime-engine, or nonclassical evidence."
        ),
        "blocked_until": (
            "blocked from bridge, QIT, GStack, axis, nonclassical, runtime-"
            "engine, or cycle claims until separate exact receipts close "
            "those gates"
        ),
        "out_of_scope": [
            "No runtime cycle dynamics.",
            "No physical bridge admission.",
            "No QIT, GStack, axis, nonclassical, runtime-engine, reservoir, or universal-demon claim.",
        ],
        "operation_sequence": [
            "construct maximally mixed one-bit system and pure memory state",
            "apply CNOT measurement fixture",
            "compute mutual information distinguishability D",
            "set one-bit ideal dF and E equal to T*D",
            "z3-check admitted measured tuple satisfiability",
            "z3-reject admitted erasure below F01 and free-erasure counterfactual",
            "z3-check no-admission independence row is SAT",
        ],
        "carrier_topology": (
            "finite two-qubit density-matrix fixture plus scalar z3 real-"
            "arithmetic admission-floor variables"
        ),
        "observable": (
            "mutual information in nats, free-energy/erasure scalar equality, "
            "and z3 SAT/UNSAT verdicts"
        ),
        "pass_fail_predicate": (
            "D equals ln2, dF and E equal T*D, admitted below-floor erasure is "
            "UNSAT, free-erasure counterfactual is UNSAT, and no-admission "
            "independence row is SAT"
        ),
        "graveyards": [
            "admitted erasure below F01",
            "admitted free erasure",
            "no-admission zero-erasure independence row",
        ],
        "graveyard_companions": [
            "admitted erasure below F01",
            "admitted free erasure",
            "no-admission zero-erasure independence row",
        ],
        "baselines": [
            "numpy two-qubit one-bit measurement fixture",
            "Landauer one-bit T*ln2 scalar anchor",
            "z3 real-arithmetic admission-floor fence",
        ],
        "alternative_formulations": [
            "explicit branch/ensemble Szilard cycle",
            "Petz-style reverse measurement candidate",
            "finite-temperature Lindblad erasure calibration",
        ],
        "exact_tool_function_needs": {
            "numpy": ["kron", "eye", "array", "linalg.eigvalsh", "trace", "log"],
            "z3": ["Real", "And", "Implies", "Solver"],
        },
        "lego_or_coupling_target": "one-bit measurement/erasure calibration support",
        "classification_note": CLASSIFICATION_NOTE,
        "lego_ids": LEGO_IDS,
        "primary_lego_ids": PRIMARY_LEGO_IDS,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "negative": negative,
        "boundary": boundary,
        "z3_bridge_proof": proof,
        "anchor": anchor,
        "summary": {
            "all_pass": all_pass,
            "temperature": temperature,
            "D_nats": D,
            "dF": dF,
            "E": E,
            "promotion_allowed": False,
            "scope_note": (
                "One-bit admission-floor fence only: maps Szilard quantities "
                "to declared admission-gate variables on a two-qubit fixture. "
                "No bridge, QIT, GStack, axis, nonclassical, engine-runtime, "
                "reservoir, or universal-demon claim."
            ),
        },
    }

    out_path = (
        pathlib.Path(__file__).resolve().parent
        / "a2_state"
        / "sim_results"
        / "szilard_distinguishability_admission_bridge_results.json"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"Results written to {out_path}")
    print(f"ALL PASS: {all_pass}")


if __name__ == "__main__":
    main()
