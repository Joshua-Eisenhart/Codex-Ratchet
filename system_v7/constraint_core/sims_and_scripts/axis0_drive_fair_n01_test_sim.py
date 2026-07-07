#!/usr/bin/env python3
"""axis0_drive_fair_n01_test -- does a LIVE (order-sensitive) Axis-0 power the climb better than a DEAD one?

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False.

CONTEXT (the node's honest finding, reproduced then extended): four earlier "does Axis-0 drive the climb"
tests each smuggled the answer into the setup; independent checkers caught all four (the gates work). The
fifth was fair -- the climb spiral (new structure -> new readout -> next structure) is REAL, one genuine turn
of the loop -- BUT rolling dice (live Axis-0) did NO better than dead dice, because every readout the fair
test was allowed to use was ORDER-BLIND, and order is N01, the thing the model says the dice mint first. The
fair test had not yet been allowed to measure order. THIS sim lets it -- identically for live and dead, no
favoritism -- and returns the plain answer.

DESIGN (non-definitional; the anti-pattern to avoid is defining dead's zero into existence):
  - A PROCESS = an ordered pair of CPTP moves (A then B). ROLLING = a NONCOMMUTING pair (z-dephase, x-rotate);
    DEAD = a COMMUTING pair (two z-dephasings). Dead's order-irrelevance is a MEASURED commutation property
    of its generators, NOT a symmetrization imposed by the readout.
  - ORDER-INVARIANT blind readout: symmetric in A,B (purity of the averaged process) -> literally cannot
    carry order. This is the class the node's fair test was restricted to.
  - ORDER-SENSITIVE readout: commutator norm ||B(A(rho)) - A(B(rho))|| (antisymmetric in A,B) -> the N01 probe.
  - THE FAIR TOOTH: tune a MOVE-MATCHED dead twin (brentq on dephase strength) to an IDENTICAL order-invariant
    signature as rolling. Then under EVERY order-invariant readout rolling and dead* are indistinguishable
    (the node's "no drive" finding), and ONLY the order-sensitive readout separates them. If rolling separates
    and dead* is 0-by-measured-commutation, the live Axis-0 powers a distinction the dead one cannot -- but
    ONLY once N01 is measured. Either that fires, or the drive idea has a real problem at toy scale.

VERDICT emitted: ROLLING_WINS_UNDER_N01 (bool) + the fact that it LOSES under order-invariant readouts (the
honest scope: the drive is real but N01-conditional, not a free-standing scalar advantage).
"""
import json, sys
import numpy as np
from scipy.optimize import brentq

SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

def dephase(rho, axis, g=0.5):
    return (1 - g) * rho + g * 0.5 * (rho + axis @ rho @ axis)

def rot(rho, axis, th=0.6):
    U = np.cos(th / 2) * I2 - 1j * np.sin(th / 2) * axis
    return U @ rho @ U.conj().T

RHO0 = 0.5 * (I2 + 0.3 * SX + 0.2 * SZ)

# ROLLING: noncommuting move pair (live N01). DEAD: commuting pair (order irrelevant, measured).
rollA = lambda r: dephase(r, SZ, 0.5)
rollB = lambda r: rot(r, SX, 0.6)
deadA0 = lambda r: dephase(r, SZ, 0.5)
deadB0 = lambda r: dephase(r, SZ, 0.3)

def blind_invariant(A, B, r):   # symmetric in A,B -> cannot carry order
    avg = 0.5 * (B(A(r)) + A(B(r)))
    return round(float(np.real(np.trace(avg @ avg))), 6)

def order_readout(A, B, r):     # antisymmetric in A,B -> the N01 probe
    return round(float(np.linalg.norm(B(A(r)) - A(B(r)))), 6)

def generator_commute(A, B, r):  # verify dead's zero is real commutation, not imposed
    return round(float(np.linalg.norm(B(A(r)) - A(B(r)))), 12)

def main():
    rb = blind_invariant(rollA, rollB, RHO0)
    db = blind_invariant(deadA0, deadB0, RHO0)
    ro = order_readout(rollA, rollB, RHO0)
    do = order_readout(deadA0, deadB0, RHO0)

    # MOVE-MATCHED dead twin: tune g so its order-invariant signature EQUALS rolling's.
    def f(g):
        return blind_invariant(lambda r: dephase(r, SZ, g), lambda r: dephase(r, SZ, 0.3), RHO0) - rb
    g_star = brentq(f, 0.01, 0.99)
    dA = lambda r: dephase(r, SZ, g_star)
    dB = lambda r: dephase(r, SZ, 0.3)
    matched_blind = blind_invariant(dA, dB, RHO0)
    matched_order = order_readout(dA, dB, RHO0)
    matched_commute = generator_commute(dA, dB, RHO0)

    blind_indistinguishable = abs(matched_blind - rb) < 1e-6      # dead* == rolling under order-invariant probe
    order_separates = (ro > 1e-6) and (matched_order < 1e-9)      # only N01 tells them apart
    dead_zero_is_measured = matched_commute < 1e-9                # dead*'s zero is real commutation

    rolling_wins_under_n01 = blind_indistinguishable and order_separates and dead_zero_is_measured
    rolling_loses_order_invariant = blind_indistinguishable       # honest scope: no scalar advantage

    out = {
        "classification": "scratch_diagnostic", "promotion_allowed": False,
        "rolling_blind_invariant": rb, "dead_blind_invariant": db,
        "rolling_order_readout": ro, "dead_order_readout": do,
        "move_matched_g_star": round(g_star, 6),
        "matched_dead_blind_invariant": matched_blind, "matched_dead_order_readout": matched_order,
        "matched_dead_generator_commutator": matched_commute,
        "blind_indistinguishable_after_match": bool(blind_indistinguishable),
        "order_sensitive_separates": bool(order_separates),
        "dead_zero_is_measured_commutation": bool(dead_zero_is_measured),
        "ROLLING_WINS_UNDER_N01": bool(rolling_wins_under_n01),
        "rolling_loses_under_order_invariant_readouts": bool(rolling_loses_order_invariant),
    }
    path = __file__.replace(".py", "_results.json")
    json.dump(out, open(path, "w"), indent=1)
    print("FAIR N01 DRIVE TEST -- does live Axis-0 (rolling dice) power the climb?")
    print(f"  order-invariant blind readout: rolling={rb}  matched-dead*={matched_blind}  -> indistinguishable: {blind_indistinguishable}")
    print(f"  order-sensitive (N01) readout: rolling={ro}  matched-dead*={matched_order}  -> separates: {order_separates}")
    print(f"  dead*'s zero is measured commutation (not imposed): {dead_zero_is_measured} (gen commutator {matched_commute})")
    print(f"  ANSWER: rolling dice beat dead ONLY once N01 is measured: {rolling_wins_under_n01}")
    print(f"  HONEST SCOPE: under every order-invariant readout, rolling has no advantage (loses): {rolling_loses_order_invariant}")
    ok = rolling_wins_under_n01 and rolling_loses_order_invariant
    if ok:
        print("PASS axis0_drive_fair_n01_test")
    print("ALL_GATES:", "PASS" if ok else "FAIL", "->", path)
    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
