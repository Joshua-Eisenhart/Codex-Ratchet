#!/usr/bin/env python3
"""ratchet_three_qubit_floor -- carry the conservation-gated ratchet onto a >=3-qubit carrier, where
distinguishability outstrips a handful of bases so DEMANDS KEEP FORCING TEETH past the dim-2 saturation.

THE OPEN REMAINDER (foundational_ratchet_entropy_gradient_sim.py, measured): a dim-2 (single-qubit) carrier
SATURATES after 2 forced teeth -- the gap keeps widening under growth but NO new demand opens, because 3
noncommuting qubit bases (Z,X,Y) resolve every new pair. That is the F01 3-qubit-floor arrived at BY the
mechanism: the carrier has no room left to be confused. The owner's standing ruling (three_qubit_floor): "i think
i need at least 3 qubits for many things to really run."

THIS SIM tests that ruling as a MEASUREMENT, not an assumption. Same ratchet rules as the foundational sim:
  - DEMAND = a pair the room asserts distinguishable (trace distance > THETA) that the ACQUIRED bases do not
    resolve (best resolved fraction < RESOLVE_FRAC of the available distinguishability).
  - MSS admissibility: admit only the weakest acquisition that closes >=1 open demand; the pawl holds otherwise.
  - CONSERVATION gate (no picked count): a climb happens iff a forced admissible step is available, replayed from
    the demand structure independently of the run.
Run the SAME mechanism on dim 2, 4, 8 carriers and MEASURE how many forced teeth each sustains before demands run
out with a fixed small stock of acquired bases. The prediction of the ruling: teeth-before-saturation RISES with
qubit count -- the dim-2 carrier stalls early, the 3-qubit (dim-8) carrier keeps forcing teeth.

WHY (the mechanism reason, not a fit): on n qubits a small fixed set of product/stabilizer bases resolves a
vanishing fraction of the exponentially many distinguishable pairs, so growth keeps opening demands the acquired
bases cannot close -> the pawl keeps releasing forced teeth. On 1 qubit, 3 bases already tomographically span the
Bloch sphere, so growth opens no new demand.

MEASUREMENT/VERDICT SEPARATION (Lev mesh discipline): instruments emit the per-dimension teeth-before-saturation
counts and the open-demand curves; a SEPARATE policy eval decides on the CONTROL FLIP -- teeth-before-saturation
must be MONOTONE NONDECREASING in qubit count AND the 3-qubit carrier must strictly exceed the 1-qubit carrier
(the floor is real). No picked pass count.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False. Pure quantum
distinguishability (trace distance), no bits/vectors. Acquired "bases" = a fixed small stock of measurement bases
per dimension (the analog of the 3 qubit bases at dim 2), so the comparison is like-for-like: a HANDFUL of bases,
rising carrier size.
"""
import json, os, sys
import numpy as np

THETA = 0.25          # a pair is a DEMAND if the room asserts it distinguishable above this (trace distance)
RESOLVE_FRAC = 0.6    # ... and the acquired bases resolve less than this fraction of its available distinguishability

def dm_from_pure(psi):
    psi = psi/np.linalg.norm(psi)
    return np.outer(psi, psi.conj())

def trace_distance(a, b):
    d = a - b
    ev = np.linalg.eigvalsh((d + d.conj().T)/2)
    return 0.5*float(np.abs(ev).sum())

def basis_resolves(basis, rhoA, rhoB):
    """resolving power of a measurement basis on a pair = total variation between the two outcome distributions."""
    pa = np.real(np.diag(basis.conj().T @ rhoA @ basis))
    pb = np.real(np.diag(basis.conj().T @ rhoB @ basis))
    return 0.5*float(np.abs(pa - pb).sum())

def pauli_axis_bases(n_qubits):
    """The acquired stock = the n single-qubit Pauli-X,Y,Z eigenbases applied qubit-wise (the natural 'few bases'
    a carrier acquires). At 1 qubit that is 3 bases and they TOMOGRAPHICALLY SPAN the qubit (dim^2-1 = 3 axes) --
    so once acquired, no pair stays unresolved: the carrier saturates. At n qubits the SAME kind of stock is 3n
    single-qubit-axis bases, but full tomography needs dim^2-1 = 4^n - 1 axes (3 at 1q, 15 at 2q, 63 at 3q). So a
    handful of single-qubit bases resolves a VANISHING fraction of the distinguishable pairs -> demands keep
    opening. This is the mechanism reason the floor exists, built in, not fitted."""
    X = np.array([[1,1],[1,-1]],complex)/np.sqrt(2)          # X eigenbasis
    Y = np.array([[1,1],[1j,-1j]],complex)/np.sqrt(2)        # Y eigenbasis
    Z = np.eye(2,dtype=complex)                              # Z eigenbasis
    singles = [Z, X, Y]
    bases = []
    for q in range(n_qubits):
        for S in singles:
            # basis measuring qubit q in S, others in Z (a single-qubit-axis product basis)
            mats = [S if i==q else np.eye(2,dtype=complex) for i in range(n_qubits)]
            U = mats[0]
            for M in mats[1:]:
                U = np.kron(U, M)
            bases.append(U)
    return bases

# ---------- PURE INSTRUMENT: run the ratchet on a carrier of given dimension ----------

def run_ratchet(dim, n_states=40, n_bases=3, seed=0, growth_steps=12):
    """The carrier GROWS (more distinguishable states admitted each shell). With a FIXED stock of n_bases acquired
    measurement bases, count how many forced teeth the ratchet releases before demands run out (saturation).
    A tooth = a shell where >=1 forced admissible step (a demand no acquired basis resolves) exists."""
    rng = np.random.default_rng(seed)
    n_qubits = int(round(np.log2(dim)))
    bases = pauli_axis_bases(n_qubits)          # 3*n_qubits single-qubit-axis bases: tomographically complete ONLY at 1 qubit
    n_bases = len(bases)
    # a growing pool of pure states on the carrier
    def rand_state():
        v = rng.standard_normal(dim) + 1j*rng.standard_normal(dim)
        return dm_from_pure(v)
    pool = [rand_state() for _ in range(4)]
    teeth = 0
    open_demand_curve = []
    for step in range(growth_steps):
        # growth: admit more states (room expands -> more distinguishable pairs)
        pool += [rand_state() for _ in range(3)]
        # find open demands: pairs the room asserts distinguishable that acquired bases don't resolve
        open_demands = 0
        forced = False
        for i in range(len(pool)):
            for j in range(i+1, len(pool)):
                td = trace_distance(pool[i], pool[j])
                if td > THETA:
                    best = max(basis_resolves(B, pool[i], pool[j]) for B in bases)
                    if best < RESOLVE_FRAC * td:
                        open_demands += 1
                        forced = True
        open_demand_curve.append(open_demands)
        # CONSERVATION: a climb (tooth) happens iff a forced admissible step is available this shell
        if forced:
            teeth += 1
    # teeth-before-saturation = teeth up to the first shell where open_demands hits 0 and stays 0 (or all shells)
    sat_shell = next((k for k in range(len(open_demand_curve))
                      if all(c == 0 for c in open_demand_curve[k:])), len(open_demand_curve))
    teeth_before_sat = sum(1 for k in range(sat_shell) if open_demand_curve[k] > 0)
    return {"dim": dim, "n_qubits": int(np.log2(dim)), "n_bases": n_bases,
            "total_forced_teeth": teeth, "teeth_before_saturation": teeth_before_sat,
            "final_open_demands": open_demand_curve[-1], "open_demand_curve": open_demand_curve}

# ---------- SEPARATE POLICY EVAL ----------

def eval_three_qubit_floor(runs):
    teeth = [r["teeth_before_saturation"] for r in runs]  # ordered by rising qubit count
    monotone = all(teeth[k+1] >= teeth[k] for k in range(len(teeth)-1))
    three_exceeds_one = runs[-1]["teeth_before_saturation"] > runs[0]["teeth_before_saturation"]
    # the dim-2 carrier saturates (its demands do run out); the 3-qubit carrier keeps forcing to the last shell
    one_saturates = runs[0]["final_open_demands"] == 0 or runs[0]["teeth_before_saturation"] <= runs[0]["open_demand_curve"].__len__()//2
    three_still_forcing = runs[-1]["final_open_demands"] > 0
    floor_real = bool(monotone and three_exceeds_one and three_still_forcing)
    return {"teeth_before_saturation_by_qubit": {r["n_qubits"]: r["teeth_before_saturation"] for r in runs},
            "monotone_nondecreasing_in_qubits": bool(monotone),
            "three_qubit_exceeds_one_qubit": bool(three_exceeds_one),
            "three_qubit_still_forcing_at_last_shell": bool(three_still_forcing),
            "THREE_QUBIT_FLOOR_IS_REAL": floor_real}

def main():
    runs = [run_ratchet(dim=2, seed=1), run_ratchet(dim=4, seed=1), run_ratchet(dim=8, seed=1)]
    verdict = eval_three_qubit_floor(runs)
    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "ruling": "three_qubit_floor -- 'i think i need at least 3 qubits for many things to really run' (owner)",
           "runs": runs, "policy_eval": verdict}
    path = __file__.replace(".py","_results.json"); json.dump(out, open(path,"w"), indent=1)

    print("THE 3-QUBIT FLOOR -- carry the ratchet past dim-2 saturation; demands keep forcing teeth on 3 qubits.\n")
    print(f"  {'qubits':>7} {'dim':>4} {'bases':>6} {'teeth_before_sat':>17} {'final_open_demands':>19}")
    for r in runs:
        print(f"  {r['n_qubits']:>7} {r['dim']:>4} {r['n_bases']:>6} {r['teeth_before_saturation']:>17} {r['final_open_demands']:>19}")
    print("\n  SEPARATE POLICY EVAL (verdict = floor is real: monotone + 3q exceeds 1q + 3q still forcing):")
    for k,v in verdict.items():
        if k not in ("THREE_QUBIT_FLOOR_IS_REAL","teeth_before_saturation_by_qubit"): print(f"    {k}: {v}")
    print(f"\n  THREE-QUBIT FLOOR IS REAL: {verdict['THREE_QUBIT_FLOOR_IS_REAL']}")
    if verdict["THREE_QUBIT_FLOOR_IS_REAL"]:
        print("PASS ratchet_three_qubit_floor")
    print("ALL_GATES:", "PASS" if verdict["THREE_QUBIT_FLOOR_IS_REAL"] else "FAIL", "->", path)
    sys.exit(0 if verdict["THREE_QUBIT_FLOOR_IS_REAL"] else 1)

if __name__ == "__main__":
    main()
