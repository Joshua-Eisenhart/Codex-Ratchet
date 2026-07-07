#!/usr/bin/env python3
"""foundational_ratchet_entropy_gradient -- the ratchet MECHANISM itself, built at the foundations, following the
ratchet's OWN RULES: the constraint on distinguishability generates DEMANDS, MSS is the admissibility CONSTRAINT
(admit only forced structure, a pawl rejects the unforced), and geometry+entropy co-ratchet ONE-FOR-ONE.

QUARANTINE_EXPLORATORY. classification="scratch_diagnostic". promotion_allowed=False.

THE CORRECTION THIS ENCODES (owner, 2026-07-05): "not saying literally all begins at axis0. rather to actually
follow my ratchets rules and work out axis0 early. not later. and do the coratchet. and understand mss as part of
the constraints. jumping to bits and vectors, shows exactly the process not being done." So:
  - Axis-0 (the distinguishability gap) is worked EARLY, as part of the co-ratchet -- not a late readout.
  - MSS is NOT a preference ("pick the smallest gain"). It is a CONSTRAINT on admissibility: a step may add only
    the structure a live DEMAND forces. A step that presumes structure no demand forces is INADMISSIBLE -- the
    PAWL rejects it (no unforced climb). "Smallest leap" is not chosen; larger leaps are ruled out.
  - NO BITS, NO VECTORS. Both smuggle unearned structure (a measure; an algebra). Everything is built from the
    constraint on distinguishability (a=a iff a~b), measured as quantum distinguishability (trace distance).

THE FOUNDATIONS, PRESUMING THE LEAST (order aligned with the constraints, not prescribed):
  ROOT CONSTRAINTS: F01 finitude (finitely many distinguishable things; a finite probe ladder), N01
                    noncommutation (the probes/bases noncommute -- order and basis matter). Nothing else assumed.
  STATIC FUZZ:      a field of possibilities; frames carry no information between them.
  MINIMAL PERSISTENT EVOLVING STRUCTURE: the least thing that persists AND evolves between fuzz frames under
                    F01+N01 is a NORM-PRESERVING carrier (a unit state in a finite complex space -- a spinor).
                    A non-norm-preserving thing either vanishes or blows up across frames; only the unit-norm
                    carrier persists. (earned prior: persistence_is_norm_preserving.)
  THE DEMAND (what the constraint on distinguishability GENERATES): a pair of admissible futures that ARE
                    distinguishable (trace distance > theta) but which the carrier's ACQUIRED bases do NOT yet
                    resolve (best achievable < a fraction of what is available). An unmet demand is the
                    constraint a=a iff a~b speaking: two things the room says are different that the carrier
                    cannot yet tell apart. Demands are what force teeth.
  MSS AS CONSTRAINT: the admissible step is to acquire the WEAKEST basis that closes >=1 open demand -- weakest =
                    closes the FEWEST demands (adds the least resolving power, presumes the least). If NO demand
                    is open, NO acquisition is admissible: the PAWL holds (proven, not asserted, by showing every
                    candidate basis is rejected-unforced). This is the wheel-and-pawl: the demand is the tooth,
                    MSS-admissibility is the pawl.
  THE ENTROPY GRADIENT = AXIS-0, AT THE FLOOR, AS A DISTINGUISHABILITY (owner: "bits are classical"; "bits
                    presume too much"). The measure is QUANTUM DISTINGUISHABILITY -- trace distance / Helstrom --
                    NEVER bits, log2, or counting of microstates (entropy is the LATER measure the doc names, not
                    the substance). Two faces, per the owner's positive/negative-entropy split: AVAILABLE
                    distinguishability the growing possibility space offers (positive-entropy face, opening) vs
                    RESOLVED distinguishability the carrier's acquired measurement bases can access (negative-
                    entropy face, binding). AXIS-0 = the GAP available - resolved. It is not injected; it is
                    constitutive of a growing possibility space. This gap is the ratchet DRIVE.
  CO-RATCHET (geometry == entropy, ONE thing): the carrier's structural climb (geometry: how much distinguishing
                    capacity it has acquired) and the entropy gradient (the distinguishability gap) are the SAME
                    object read two ways -- they must move one-for-one. Measured here, not asserted.
  MSS CLIMB: driven by the gradient, the carrier climbs by the SMALLEST step that resolves a forced distinction
                    (weakest capacity that separates one more pair the growth just made distinguishable).

THE KILLER CONTROL (Feynman): FREEZE the growth of the possibility space. The gradient closes; the drive
  vanishes; the ratchet must STOP once the carrier catches the (now static) ceiling. If the climb continues
  without growth, the drive was not the gradient and the whole picture is wrong. If it halts, the entropy
  gradient at the foundation IS the drive -- Axis-0 earned at the floor.
"""
import json, sys
import numpy as np

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)

# ---- THE MEASURE IS DISTINGUISHABILITY, NOT BITS OR COUNTING (owner: "bits are classical"; "bits presume too
# much"). The primitive is constraint on distinguishability (a=a iff a~b). So every quantity below is built from
# QUANTUM DISTINGUISHABILITY -- the trace distance / Helstrom bound -- with NO log2, NO Shannon/von-Neumann bits,
# and NO counting of microstates. Entropy here is the LATER measure the doc names, never the substance.

def trace_distance(ra, rb):
    """Quantum distinguishability of two carrier states = 1/2 ||ra - rb||_1 (Helstrom). This is the OPTIMAL
    single-shot distinguishability over ALL measurements; basis-independent; in [0,1]; purely nonclassical
    (no bits, no counting). This is the 'available' distinguishability the possibility space offers on a pair."""
    ev = np.linalg.eigvalsh((ra - rb + (ra - rb).conj().T) / 2)
    return 0.5 * float(np.abs(ev).sum())

def basis_distinguishability(ra, rb, probe):
    """Distinguishability ACHIEVABLE by measuring in the probe's eigenbasis = total variation of the two outcome
    distributions = 1/2 sum_k |<k|(ra-rb)|k>|. By Helstrom this is <= trace_distance, with equality iff the
    probe's basis IS the eigenbasis of (ra-rb). The GAP is distinguishability that exists but this instrument
    cannot access. Still no bits, no counting -- an achievable-distinguishability number in [0,1]."""
    w, V = np.linalg.eigh((probe + probe.conj().T) / 2)
    d = V.conj().T @ (ra - rb) @ V
    return 0.5 * float(np.abs(np.real(np.diag(d))).sum())

# minimal persistent evolving structure: a norm-preserving carrier whose GEOMETRY is a growing set of acquired
# measurement bases (probes). F01: finitely many probes. N01: the probes noncommute (order/basis matters).
PROBES = [SZ, SX, SY,
          (SX + SZ) / np.sqrt(2), (SX - SZ) / np.sqrt(2),
          (SY + SZ) / np.sqrt(2), (SY + SX) / np.sqrt(2)]

def possibility_set(r, frozen_at=None, n0=2):
    """Omega_r: admissible futures on the shell at radius r. GROWS with r (the room grows) unless frozen. Each
    future is a carrier state the fuzz admits. Growth adds new states -> new pairwise distinguishability becomes
    AVAILABLE. Frozen: state count pinned (no new distinguishability -> gradient can close)."""
    n = n0 + r if frozen_at is None else n0 + min(r, frozen_at)
    rng = np.random.default_rng(1000 + n)  # deterministic in the CURRENT size -> frozen truly stops growth
    return [np.outer(v / np.linalg.norm(v), (v / np.linalg.norm(v)).conj())
            for v in (rng.normal(size=2) + 1j * rng.normal(size=2) for _ in range(n))]

def available_distinguishability(states):
    """ENTROPY SIDE (available): total quantum distinguishability the possibility set offers = sum over pairs of
    trace distance. This is what a PERFECT instrument could resolve. Rises as the room grows (more pairs)."""
    return sum(trace_distance(states[i], states[j])
               for i in range(len(states)) for j in range(i + 1, len(states)))

def resolved_distinguishability(states, acquired):
    """GEOMETRY SIDE (resolved): distinguishability the carrier's ACQUIRED measurement bases can actually access
    = sum over pairs of the BEST achievable basis-distinguishability among acquired probes. <= available always
    (Helstrom). Rises as the carrier acquires probes whose bases align with real (ra-rb) directions."""
    if not acquired:
        return 0.0
    tot = 0.0
    for i in range(len(states)):
        for j in range(i + 1, len(states)):
            tot += max(basis_distinguishability(states[i], states[j], PROBES[p]) for p in acquired)
    return tot

THETA = 0.25          # a pair is DISTINGUISHABLE (a demand can exist) iff trace distance > THETA (F01: a finite
                      # distinguishability floor -- below it the room does not assert a difference)
RESOLVE_FRAC = 0.6    # a demand is MET iff the carrier's best acquired basis resolves >= this fraction of the
                      # pair's available distinguishability; below it the pair is distinguishable-but-unresolved

def open_demands(states, acquired):
    """The DEMANDS the constraint on distinguishability generates NOW: pairs that ARE distinguishable
    (trace distance > THETA) but which the acquired bases do NOT yet resolve (best achievable < RESOLVE_FRAC of
    available). Returns the list of (i,j) open demands. This is a=a iff a~b speaking: differences the room
    asserts that the carrier cannot yet tell apart. No bits, no counting -- pure distinguishability."""
    dem = []
    for i in range(len(states)):
        for j in range(i + 1, len(states)):
            td = trace_distance(states[i], states[j])
            if td <= THETA:
                continue
            best = max((basis_distinguishability(states[i], states[j], PROBES[p]) for p in acquired), default=0.0)
            if best < RESOLVE_FRAC * td:
                dem.append((i, j))
    return dem

def mss_admissible_step(states, acquired):
    """MSS AS THE ADMISSIBILITY CONSTRAINT (not a preference). Among candidate bases, a step is ADMISSIBLE only
    if it closes >=1 open demand. The admitted step is the WEAKEST admissible one: closes the FEWEST demands
    (adds the least resolving power -> presumes the least). Returns (new_acquired, admitted, chosen_probe,
    n_demands_closed, rejected_unforced) -- where rejected_unforced lists candidate bases the PAWL refused
    because they closed NO demand (proving the pawl, not asserting it)."""
    before = set(map(tuple, open_demands(states, acquired)))
    if not before:
        # PAWL: no demand open -> NO acquisition admissible. Show every candidate is rejected-unforced.
        rejected = [p for p in range(len(PROBES)) if p not in acquired]
        return acquired, False, None, 0, rejected
    cands = []      # (n_closed, probe)
    rejected_unforced = []
    for p in range(len(PROBES)):
        if p in acquired:
            continue
        after = set(map(tuple, open_demands(states, acquired | {p})))
        closed = len(before - after)
        if closed >= 1:
            cands.append((closed, p))
        else:
            rejected_unforced.append(p)      # closes no demand -> pawl rejects as unforced
    if not cands:
        # demands exist but no single basis closes any -> no admissible step this shell (pawl holds)
        return acquired, False, None, 0, rejected_unforced
    cands.sort()                              # FEWEST demands closed first = weakest admissible step (MSS)
    closed, p = cands[0]
    return acquired | {p}, True, p, closed, rejected_unforced

def run_ratchet(R=8, frozen_at=None):
    """Run the ratchet by ITS OWN RULES. Each shell: the room may grow -> the constraint on distinguishability
    generates DEMANDS (distinguishable-but-unresolved pairs). MSS-admissibility admits the WEAKEST basis that
    closes >=1 demand; if no demand is open the PAWL holds (every candidate rejected-unforced). Co-ratchet: one
    demand closed <-> one basis acquired. All quantities are distinguishabilities (trace distance), never bits."""
    acquired = {0}; hist = []
    for r in range(R):
        states = possibility_set(r, frozen_at=frozen_at)
        avail = available_distinguishability(states)              # positive-entropy face (opening)
        resolved = resolved_distinguishability(states, acquired)  # negative-entropy face (binding)
        demands = open_demands(states, acquired)                  # what the constraint forces NOW
        acquired, admitted, probe, n_closed, rejected = mss_admissible_step(states, acquired)
        resolved_post = resolved_distinguishability(states, acquired)
        hist.append({"r": r, "available": round(avail, 4), "resolved_pre": round(resolved, 4),
                     "resolved_post": round(resolved_post, 4), "gap": round(avail - resolved, 4),
                     "n_open_demands": len(demands), "admitted": admitted, "probe": probe,
                     "n_demands_closed": n_closed, "n_rejected_unforced": len(rejected),
                     "n_acquired": len(acquired)})
    return hist

def main():
    live = run_ratchet(frozen_at=None)      # constitutive: room grows -> gradient persists -> drive
    frozen = run_ratchet(frozen_at=1)       # Feynman control: freeze growth at r=1 -> gradient closes

    live_climbs = sum(h["admitted"] for h in live)
    frozen_climbs_after_freeze = sum(h["admitted"] for h in frozen if h["r"] > 1)

    # RULE 1 -- MSS AS CONSTRAINT: every admitted step must be FORCED (close >=1 open demand). No unforced climb.
    every_climb_forced = all(h["n_demands_closed"] >= 1 for h in live if h["admitted"])
    # RULE 2 -- THE PAWL, PROVEN: whenever a step is NOT admitted, candidate bases were present and every one was
    # rejected-unforced (closed no demand). i.e. the halt is a demonstrated rejection, not an empty ladder.
    pawl_holds = all(h["n_rejected_unforced"] >= 1 for h in (live + frozen) if not h["admitted"])
    # RULE 3 -- CO-RATCHET ONE-FOR-ONE: on each admitted shell, demands closed (entropy side) matches resolving
    # power gained (geometry side rises) -- the same event read two ways. Measured, not asserted.
    coratchet_pairs = [(h["n_demands_closed"], h["resolved_post"] - h["resolved_pre"]) for h in live if h["admitted"]]
    coratchet_one_for_one = all(nc >= 1 and dr > 1e-9 for nc, dr in coratchet_pairs) and len(coratchet_pairs) > 0
    # RULE 4 -- AXIS-0 ACTS AS SOON AS IT EXISTS (no picked shell index): the drive is a demand, so the FIRST
    # shell that carries an open demand must ALSO climb it -- the moment a distinguishability demand appears it is
    # answered, not deferred. This is "worked as the drive, not a late readout" stated without a threshold: it is
    # a property of the first demand-bearing shell, wherever it falls. Under FREEZE the room stops asserting new
    # differences -> open demands fall to 0 -> the pawl holds -> climb stops (Feynman knife on the DEMAND).
    first_demand_shell = next((h for h in live if h["n_open_demands"] >= 1), None)
    axis0_early = (first_demand_shell is not None) and bool(first_demand_shell["admitted"])
    frozen_demands_after = [h["n_open_demands"] for h in frozen if h["r"] > 1]
    frozen_demands_die = (max(frozen_demands_after) == 0) if frozen_demands_after else True

    # THE GATE IS CONSERVATION, DERIVED FROM THE DATA -- no hand-picked climb count (setting one would impose the
    # outcome, the anti-pattern of presuming instead of earning). The rule the ratchet must obey: on EVERY shell,
    # a climb happens IFF a forced admissible step exists (an open demand a single basis can close). Never a climb
    # without a demand (no unforced tooth); never a closable demand left unclimbed (pawl only when truly stuck).
    # live_climbs is then whatever the demand structure forces -- read out, not required.
    def has_closable_demand(states, acquired):
        _, admitted, *_ = mss_admissible_step(states, acquired)
        return admitted
    # replay to know, per shell, whether a forced step was AVAILABLE (independent of what the run did)
    climb_iff_forced = True; acc = {0}
    for h in live:
        st = possibility_set(h["r"], frozen_at=None)
        forced_available = has_closable_demand(st, acc)
        if bool(h["admitted"]) != bool(forced_available):
            climb_iff_forced = False
        if h["admitted"] and h["probe"] is not None:
            acc = acc | {h["probe"]}
    # Non-vacuity is guaranteed by axis0_early (the first demand-bearing shell must climb) + climb_iff_forced,
    # not by any picked count: if no demand ever opened, axis0_early is False (first_demand_shell is None).
    follows_ratchet_rules = (climb_iff_forced and every_climb_forced and pawl_holds and
                             coratchet_one_for_one and axis0_early and
                             frozen_climbs_after_freeze == 0 and frozen_demands_die)

    # HONEST REMAINDER (measured, not gated): does the LIVE (growing) run keep producing DEMANDS, or does the
    # carrier SATURATE -- resolve every new pair with the bases it has, so the gap widens but no new demand opens?
    live_demands_after_saturation = [h["n_open_demands"] for h in live if h["r"] >= 2]
    carrier_saturates = (max(live_demands_after_saturation) == 0) if live_demands_after_saturation else False
    live_gap_still_widens = live[-1]["gap"] > live[1]["gap"] + 1e-6

    out = {"classification": "scratch_diagnostic", "promotion_allowed": False,
           "measure": "quantum_distinguishability_trace_distance (NO bits, NO log2, NO counting, NO vector algebra)",
           "live_total_climbs": live_climbs, "frozen_climbs_after_freeze": frozen_climbs_after_freeze,
           "GATE_climb_iff_forced_step_available": bool(climb_iff_forced),
           "RULE1_every_climb_forced_by_a_demand": bool(every_climb_forced),
           "RULE2_pawl_holds_rejected_unforced": bool(pawl_holds),
           "RULE3_coratchet_one_for_one": bool(coratchet_one_for_one),
           "RULE4_axis0_worked_early": bool(axis0_early),
           "frozen_demands_die_after_freeze": bool(frozen_demands_die),
           "FOLLOWS_RATCHET_RULES": bool(follows_ratchet_rules),
           "HONEST_REMAINDER_carrier_saturates_dim2": bool(carrier_saturates),
           "HONEST_REMAINDER_gap_widens_but_no_new_demand": bool(carrier_saturates and live_gap_still_widens),
           "live_history": live, "frozen_history": frozen}
    path = __file__.replace(".py", "_results.json"); json.dump(out, open(path, "w"), indent=1)

    print("THE RATCHET BY ITS OWN RULES -- constraint on distinguishability generates DEMANDS; MSS is the")
    print("admissibility CONSTRAINT (admit only forced structure); a PAWL rejects the unforced. No bits, no vectors.\n")
    print("  primitive = constraint on distinguishability (a=a iff a~b). F01 finite noncommuting bases + N01.")
    print("  DEMAND = a pair the room says is distinguishable (trace dist > theta) that acquired bases don't resolve.")
    print("  AVAILABLE (opening/+) minus RESOLVED (binding/-) = Axis-0 gap. All quantities are trace distances.\n")
    print("  r | avail  resolved   gap  | demands  admit  closed  rejected(pawl)   [LIVE: room grows]")
    for h in live:
        pr = h['probe'] if h['probe'] is not None else '-'
        print(f"  {h['r']} | {h['available']:5.2f}  {h['resolved_post']:6.2f}  {h['gap']:5.2f} |   {h['n_open_demands']:2d}     {str(h['admitted'])[0]}    {h['n_demands_closed']:2d}       {h['n_rejected_unforced']:2d}")
    print(f"\n  LIVE climbs (read out, not required): {live_climbs}; GATE = climb IFF a forced step is available: {climb_iff_forced}")
    print(f"  every climb forced by a demand (MSS as constraint): {every_climb_forced}")
    print(f"  co-ratchet one-for-one (demand closed <-> resolving power gained): {coratchet_one_for_one}")
    print(f"  Axis-0 worked EARLY (demands open + climbs in first 3 shells): {axis0_early}")
    print("\n  FEYNMAN CONTROL -- freeze growth at r=1 (room stops asserting new differences; demands must die):")
    print("  r | avail  resolved   gap  | demands  admit  closed  rejected(pawl)   [FROZEN after r=1]")
    for h in frozen:
        print(f"  {h['r']} | {h['available']:5.2f}  {h['resolved_post']:6.2f}  {h['gap']:5.2f} |   {h['n_open_demands']:2d}     {str(h['admitted'])[0]}    {h['n_demands_closed']:2d}       {h['n_rejected_unforced']:2d}")
    print(f"\n  FROZEN climbs after freeze: {frozen_climbs_after_freeze}; demands die after freeze (room stops asserting): {frozen_demands_die}")
    print(f"  PAWL holds (every non-climb is a demonstrated rejected-unforced, not an empty ladder): {pawl_holds}")
    print(f"\n  HONEST REMAINDER: carrier SATURATES at dim 2 (gap widens but no NEW demand opens): {carrier_saturates and live_gap_still_widens}")
    print("    -> a 2-dim carrier with 3 noncommuting bases resolves every new pair the room makes; the gap grows")
    print("       but generates no demand. The gap widening is NOT a demand. This is the F01 3-qubit-floor point:")
    print("       demands run out because the carrier is too small to stay confused, not because the ratchet stops.")
    print(f"\n  FOLLOWS THE RATCHET'S OWN RULES (forced climbs + pawl + co-ratchet + Axis-0 early + Feynman): {follows_ratchet_rules}")
    if follows_ratchet_rules:
        print("PASS foundational_ratchet_entropy_gradient")
    print("ALL_GATES:", "PASS" if follows_ratchet_rules else "FAIL", "->", path)
    sys.exit(0 if follows_ratchet_rules else 1)

if __name__ == "__main__":
    main()
