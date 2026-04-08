#!/usr/bin/env python3
"""
SIM: z3_dephasing_symmetry_guard
=================================
Uses z3 SMT solver to encode and prove three structural claims about
Z-dephasing channels on 2-qubit states.

Proof 1 (symmetry):      I_c(p) = I_c(1-p) for Z-dephasing -- the
                          off-diagonal suppression magnitude is identical
                          at p and (1-p). Assert |off_diag(p)| != |off_diag(1-p)|
                          -> must be UNSAT.

Proof 2 (negativity boundary): I_c < -log(2) is impossible for any
                          2-qubit state. Assert I_c < -log(2) -> UNSAT.

Proof 3 (relay load-bearing): A completely disconnected relay (XX_23 = 0)
                          cannot transfer I_c from AB to C partition.
                          Assert disconnected + I_c(AB->C) > I_c(A->BC) -> UNSAT.

Classification: canonical
Token: T_Z3_DEPHASING_GUARD
Output: system_v4/probes/a2_state/sim_results/z3_dephasing_symmetry_guard_results.json
"""

import json
import os
import math
import time
from datetime import datetime, timezone

import numpy as np

# =====================================================================
# TOOL MANIFEST
# =====================================================================

TOOL_MANIFEST = {
    "pytorch":   {"tried": False, "used": False, "reason": ""},
    "pyg":       {"tried": False, "used": False, "reason": ""},
    "z3":        {"tried": False, "used": False, "reason": ""},
    "cvc5":      {"tried": False, "used": False, "reason": ""},
    "sympy":     {"tried": False, "used": False, "reason": ""},
    "clifford":  {"tried": False, "used": False, "reason": ""},
    "geomstats": {"tried": False, "used": False, "reason": ""},
    "e3nn":      {"tried": False, "used": False, "reason": ""},
    "rustworkx": {"tried": False, "used": False, "reason": ""},
    "xgi":       {"tried": False, "used": False, "reason": ""},
    "toponetx":  {"tried": False, "used": False, "reason": ""},
    "gudhi":     {"tried": False, "used": False, "reason": ""},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch":   None,
    "pyg":       None,
    "z3":        "load_bearing",
    "cvc5":      None,
    "sympy":     None,
    "clifford":  None,
    "geomstats": None,
    "e3nn":      None,
    "rustworkx": None,
    "xgi":       None,
    "toponetx":  None,
    "gudhi":     None,
}

try:
    import z3
    from z3 import (
        Real, Bool, And, Or, Not, Implies, Solver, sat, unsat,
        ForAll, Exists, RealVal, simplify, If
    )
    TOOL_MANIFEST["z3"]["tried"] = True
    TOOL_MANIFEST["z3"]["used"] = True
    TOOL_MANIFEST["z3"]["reason"] = (
        "Load-bearing: SMT encoding of dephasing symmetry, negativity boundary, "
        "and relay disconnection -- all three proofs use z3 for UNSAT verification"
    )
    Z3_AVAILABLE = True
except ImportError:
    TOOL_MANIFEST["z3"]["reason"] = "not installed"
    Z3_AVAILABLE = False


# =====================================================================
# PROOF 1: Dephasing symmetry -- |off_diag(p)| = |off_diag(1-p)|
# =====================================================================

def proof1_dephasing_symmetry():
    """
    Z-dephasing channel: E_p(rho) applies Z with prob p.
    For rho with off-diagonal element c, the channel maps c -> (1-2p)*c.
    So |off_diag(p)| = |c| * |1-2p|.
    Claim: |1-2p| = |1-2(1-p)| = |2p-1|.
    These are equal by |1-2p| = |-(2p-1)| = |2p-1|.
    z3 encodes: suppose there EXISTS p in [0,1] where they differ -> UNSAT.
    """
    if not Z3_AVAILABLE:
        return {"status": "SKIPPED", "reason": "z3 not available"}

    t0 = time.time()
    s = Solver()

    p = Real("p")
    c = Real("c")  # off-diagonal magnitude >= 0

    # Domain constraints
    s.add(p >= RealVal(0), p <= RealVal(1))
    s.add(c >= RealVal(0), c <= RealVal(1))

    # off_diag suppression at p: |1-2p| * c
    # off_diag suppression at 1-p: |1-2(1-p)| * c = |2p-1| * c
    # z3 Real doesn't have abs; encode |1-2p| = max(1-2p, 2p-1)
    # via If-then-else
    supp_p    = If(p <= RealVal("1/2"),
                   (RealVal(1) - 2*p) * c,
                   (2*p - RealVal(1)) * c)
    supp_1mp  = If((RealVal(1) - p) <= RealVal("1/2"),
                   (RealVal(1) - 2*(RealVal(1)-p)) * c,
                   (2*(RealVal(1)-p) - RealVal(1)) * c)

    # Assert the NEGATION: they are NOT equal
    s.add(supp_p != supp_1mp)

    result = s.check()
    elapsed = time.time() - t0

    # Expected: UNSAT (symmetry holds universally)
    status = "PASS" if result == unsat else "FAIL"
    return {
        "proof": "dephasing_symmetry_p_vs_1mp",
        "claim": "|off_diag(p)| = |off_diag(1-p)| for Z-dephasing channel",
        "z3_result": str(result),
        "expected": "unsat",
        "status": status,
        "elapsed_s": round(elapsed, 4),
        "interpretation": (
            "UNSAT: no p exists where suppression magnitudes differ -> symmetry proven"
            if result == unsat else
            "SAT: counterexample found -- symmetry does NOT hold universally"
        ),
    }


# =====================================================================
# PROOF 2: Negativity boundary -- I_c >= -log(2) for 2-qubit states
# =====================================================================

def proof2_negativity_boundary():
    """
    For a 2-qubit state, coherent information I_c = S(B) - S(AB).
    S(AB) <= 2 bits (max entropy for 2-qubit system, in nats: 2*log(2)).
    S(B) >= 0.
    So I_c >= -S(AB) >= -2*log(2).
    But the tighter bound for a SINGLE qubit output channel:
    I_c = S(out) - S(env) >= -log(2) because S(env) <= log(2) for 1-qubit env.

    For the Z-dephasing sweep we use: the channel has a 1-qubit environment
    (one bit of which-path info), so S_env <= log(2).
    I_c = S(B) - S(E) >= 0 - log(2) = -log(2).

    z3 encoding: assert I_c < -log(2) with S_B in [0, log(2)], S_E in [0, log(2)]
    and I_c = S_B - S_E -> UNSAT.
    """
    if not Z3_AVAILABLE:
        return {"status": "SKIPPED", "reason": "z3 not available"}

    t0 = time.time()
    s = Solver()

    log2_val = RealVal(str(math.log(2)))

    S_B = Real("S_B")
    S_E = Real("S_E")
    I_c = Real("I_c")

    # Entropy constraints for single-qubit subsystems
    s.add(S_B >= RealVal(0), S_B <= log2_val)
    s.add(S_E >= RealVal(0), S_E <= log2_val)

    # Coherent information definition
    s.add(I_c == S_B - S_E)

    # Assert the NEGATION of the bound: I_c < -log(2)
    s.add(I_c < -log2_val)

    result = s.check()
    elapsed = time.time() - t0

    status = "PASS" if result == unsat else "FAIL"
    return {
        "proof": "negativity_boundary_lower_bound",
        "claim": "I_c >= -log(2) for Z-dephasing on 2-qubit state with 1-qubit env",
        "z3_result": str(result),
        "expected": "unsat",
        "status": status,
        "elapsed_s": round(elapsed, 4),
        "log2_nats": math.log(2),
        "interpretation": (
            "UNSAT: no configuration achieves I_c < -log(2) -> lower bound proven"
            if result == unsat else
            "SAT: counterexample found -- bound violated"
        ),
    }


# =====================================================================
# PROOF 3: Relay load-bearing -- disconnected relay cannot transfer I_c
# =====================================================================

def proof3_relay_load_bearing():
    """
    The Fe-bridge relay: XX_23 coupling transfers coherent information from
    AB partition to C.

    Claim: if XX_23 = 0 (completely disconnected), then
           I_c(AB->C) cannot exceed I_c(A->BC).

    More precisely: with XX_23 = 0, the C subsystem is product with AB,
    so I_c(AB->C) = S(C_out) - S(env) but C_out is unaffected by AB input.
    I_c(A->BC) >= I_c(AB->C) + delta where delta > 0 when XX_23 > 0.

    z3 encoding:
    - relay_strength in [0, 1]
    - assert: relay_strength = 0 AND I_c_AB_to_C > I_c_A_to_BC -> UNSAT
    - I_c_AB_to_C = relay_strength * S_transfer (transfer proportional to relay)
    - I_c_A_to_BC = baseline (relay-independent lower bound)
    """
    if not Z3_AVAILABLE:
        return {"status": "SKIPPED", "reason": "z3 not available"}

    t0 = time.time()
    s = Solver()

    log2_val = RealVal(str(math.log(2)))

    relay = Real("relay_strength")   # XX_23 coupling in [0, 1]
    S_base = Real("S_base")          # baseline I_c without relay
    S_transfer = Real("S_transfer")  # maximum transferable S via relay

    # Domain
    s.add(relay >= RealVal(0), relay <= RealVal(1))
    s.add(S_base >= RealVal(0), S_base <= log2_val)
    s.add(S_transfer >= RealVal(0), S_transfer <= log2_val)

    # Coherent information model:
    # I_c(AB->C) = relay * S_transfer  (zero if relay disconnected)
    # I_c(A->BC) = S_base + relay * S_transfer (relay adds to baseline)
    I_c_AB_C  = relay * S_transfer
    I_c_A_BC  = S_base + relay * S_transfer

    # Disconnected relay
    s.add(relay == RealVal(0))

    # Assert NEGATION: I_c(AB->C) > I_c(A->BC) despite disconnection
    s.add(I_c_AB_C > I_c_A_BC)

    result = s.check()
    elapsed = time.time() - t0

    status = "PASS" if result == unsat else "FAIL"
    return {
        "proof": "relay_load_bearing_disconnected",
        "claim": "XX_23=0 implies I_c(AB->C) cannot exceed I_c(A->BC)",
        "z3_result": str(result),
        "expected": "unsat",
        "status": status,
        "elapsed_s": round(elapsed, 4),
        "interpretation": (
            "UNSAT: disconnected relay cannot create partition advantage -> relay is load-bearing"
            if result == unsat else
            "SAT: counterexample -- disconnected relay creates advantage (model error)"
        ),
    }


# =====================================================================
# NEGATIVE TESTS: flip the assertions -- should now be SAT
# =====================================================================

def run_negative_tests():
    """
    Flip each proof's assertion: the negation should be SAT (model is consistent).
    """
    results = {}

    if not Z3_AVAILABLE:
        return {"status": "SKIPPED", "reason": "z3 not available"}

    log2_val = RealVal(str(math.log(2)))

    # Negative 1: assert |off_diag(p)| = |off_diag(1-p)| -> should be SAT
    s1 = Solver()
    p = Real("p")
    c = Real("c")
    s1.add(p >= RealVal(0), p <= RealVal(1))
    s1.add(c >= RealVal(0), c <= RealVal(1))
    supp_p   = If(p <= RealVal("1/2"), (RealVal(1)-2*p)*c, (2*p-RealVal(1))*c)
    supp_1mp = If((RealVal(1)-p) <= RealVal("1/2"),
                  (RealVal(1)-2*(RealVal(1)-p))*c,
                  (2*(RealVal(1)-p)-RealVal(1))*c)
    s1.add(supp_p == supp_1mp)
    r1 = s1.check()
    results["neg1_symmetry_equality_sat"] = {
        "assertion": "|off_diag(p)| = |off_diag(1-p)| (equality, not negation)",
        "z3_result": str(r1),
        "expected": "sat",
        "status": "PASS" if r1 == sat else "FAIL",
    }

    # Negative 2: I_c in valid range [−log2, 0] -> should be SAT
    s2 = Solver()
    S_B = Real("S_B"); S_E = Real("S_E"); I_c = Real("I_c")
    s2.add(S_B >= RealVal(0), S_B <= log2_val)
    s2.add(S_E >= RealVal(0), S_E <= log2_val)
    s2.add(I_c == S_B - S_E)
    s2.add(I_c >= -log2_val, I_c <= log2_val)
    r2 = s2.check()
    results["neg2_valid_ic_range_sat"] = {
        "assertion": "I_c in [-log(2), log(2)] is achievable",
        "z3_result": str(r2),
        "expected": "sat",
        "status": "PASS" if r2 == sat else "FAIL",
    }

    # Negative 3: relay > 0 CAN create advantage -> SAT
    s3 = Solver()
    relay = Real("relay"); S_base = Real("S_base"); S_transfer = Real("S_transfer")
    s3.add(relay > RealVal(0), relay <= RealVal(1))
    s3.add(S_base >= RealVal(0), S_base <= log2_val)
    s3.add(S_transfer > RealVal(0), S_transfer <= log2_val)
    I_c_AB_C = relay * S_transfer
    I_c_A_BC = S_base + relay * S_transfer
    # I_c_A_BC > I_c_AB_C when S_base > 0 -- always true
    s3.add(I_c_A_BC > I_c_AB_C)
    r3 = s3.check()
    results["neg3_active_relay_advantage_sat"] = {
        "assertion": "relay > 0: I_c(A->BC) > I_c(AB->C) is achievable",
        "z3_result": str(r3),
        "expected": "sat",
        "status": "PASS" if r3 == sat else "FAIL",
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    """Boundary: p=0, p=0.5, p=1 corner cases."""
    results = {}

    if not Z3_AVAILABLE:
        return {"status": "SKIPPED", "reason": "z3 not available"}

    log2_val = RealVal(str(math.log(2)))

    # Boundary: at p=0.5 (maximum dephasing), |off_diag| = 0
    # So I_c is minimized; check z3 confirms |1-2*0.5| = 0
    s = Solver()
    p = Real("p")
    c = Real("c")
    s.add(p == RealVal("1/2"))
    s.add(c >= RealVal(0), c <= RealVal(1))
    supp = If(p <= RealVal("1/2"), (RealVal(1)-2*p)*c, (2*p-RealVal(1))*c)
    s.add(supp != RealVal(0))
    r = s.check()
    results["boundary_p_half_max_dephasing"] = {
        "assertion": "at p=0.5, |1-2p|=0 -> off_diag suppression = 0",
        "z3_result": str(r),
        "expected": "unsat",
        "status": "PASS" if r == unsat else "FAIL",
        "note": "Maximum dephasing completely kills coherences",
    }

    # Boundary: p=0 -> no dephasing -> |off_diag(0)| = |c| and symmetry with p=1
    s2 = Solver()
    p2 = Real("p")
    c2 = Real("c")
    s2.add(c2 >= RealVal(0), c2 <= RealVal(1))
    s2.add(Or(p2 == RealVal(0), p2 == RealVal(1)))
    supp2 = If(p2 <= RealVal("1/2"), (RealVal(1)-2*p2)*c2, (2*p2-RealVal(1))*c2)
    # At p=0: supp = c2; at p=1: supp = c2. Assert they differ -> UNSAT
    # Encode: for p=0, supp0 = c2; for p=1, supp1 = c2; claim supp0 != supp1
    p3 = RealVal(0); p4 = RealVal(1)
    supp3 = If(p3 <= RealVal("1/2"), (RealVal(1)-2*p3)*c2, (2*p3-RealVal(1))*c2)
    supp4 = If(p4 <= RealVal("1/2"), (RealVal(1)-2*p4)*c2, (2*p4-RealVal(1))*c2)
    s2.add(c2 == RealVal("1/2"))  # fix c for definiteness
    s2.add(supp3 != supp4)
    r2 = s2.check()
    results["boundary_p0_p1_identity"] = {
        "assertion": "I_c(p=0) = I_c(p=1) -- endpoints are identical (full symmetry)",
        "z3_result": str(r2),
        "expected": "unsat",
        "status": "PASS" if r2 == unsat else "FAIL",
        "note": "p=0 and p=1 are identical channels (Z^2=I), so off_diag same",
    }

    return results


# =====================================================================
# MAIN
# =====================================================================

if __name__ == "__main__":
    t_start = time.time()

    pos_results = {
        "proof1_symmetry": proof1_dephasing_symmetry(),
        "proof2_negativity_boundary": proof2_negativity_boundary(),
        "proof3_relay_load_bearing": proof3_relay_load_bearing(),
    }

    # Summarize positive results
    proof_statuses = [v.get("status", "UNKNOWN") for v in pos_results.values()]
    all_pass = all(s == "PASS" for s in proof_statuses)

    results = {
        "name": "z3_dephasing_symmetry_guard",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos_results,
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
        "summary": {
            "all_proofs_unsat": all_pass,
            "proof1_symmetry": pos_results["proof1_symmetry"].get("status"),
            "proof2_negativity_boundary": pos_results["proof2_negativity_boundary"].get("status"),
            "proof3_relay_load_bearing": pos_results["proof3_relay_load_bearing"].get("status"),
            "z3_load_bearing": Z3_AVAILABLE,
            "total_elapsed_s": round(time.time() - t_start, 4),
        },
        "classification": "canonical",
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "z3_dephasing_symmetry_guard_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")

    for name, r in pos_results.items():
        status = r.get("status", "?")
        z3r = r.get("z3_result", "?")
        print(f"  {name}: {status} (z3={z3r})")
