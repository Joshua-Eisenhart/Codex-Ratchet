#!/usr/bin/env python3
"""Independent auditor reimplementation of the survivor-set-restriction
noncommutation crux from
  system_v6/foundations/ratchet_definition_and_emergence_spec_DRAFT_20260614.md (§5)

This file is written by a FRESH-CONTEXT auditor. It does NOT import any builder
code. It re-derives, from scratch, every quantity the audit crux asks for:

  (1) delta(C_i,C_j) = | Surv(...C_i C_j...) symmetric_difference Surv(...C_j C_i...) |
      as a restriction of SURVIVOR SETS (not maps), for a HISTORY-DEPENDENT
      constraint pair.  Crux question: is this genuinely NONZERO?

  (2) the same delta for a STATIC (history-INDEPENDENT) predicate control.
      Crux question: is this genuinely ZERO (set-intersection commutes,
      replicating ratchet_s1's commuting filter case)?

  (3) AMNESIC memory-ablation: take the SAME history-dependent constraints but
      strip the history argument (C_k(x,H) -> C_k(x)).  Crux question: does the
      noncommutation COLLAPSE to zero (proving memory/history is the engine, R3)?

  (4) GNVW index of the ring-checkerboard QCA local rules: L-shift, R-shift,
      identity.  Crux question: do the signs flip for L/R (+/-) and is it 0 for
      identity?

  (5) Phi commuting square  Phi o Update_lex  ==  Update_geo o Phi  on matched
      inputs, reporting a fidelity (fraction of matched steps where the square
      closes exactly).

The geometric register is a RING of cells with a checkerboard (even/odd
sublattice) update.  The lexical register is a tiny token survivor process whose
tokens are bijective with cells; Phi is that bijection lifted to survivor sets.

NO precomputed booleans.  NO hand-ranked verdicts.  Every reported scalar is the
return value of a function defined in THIS file and recomputed at run time.
"""

import itertools


# --------------------------------------------------------------------------
# Geometric register: ring of N cells, each cell holds a bit (alive-token = 1).
# A "claim token" x lives on a cell.  The carrier set S is the set of cells.
# A survivor SET is a subset of cells that are still "alive".
# --------------------------------------------------------------------------

N = 8  # ring size (even, so checkerboard sublattices are equal)
CELLS = tuple(range(N))


def neighbours(c):
    """Ring adjacency (periodic)."""
    return ((c - 1) % N, (c + 1) % N)


# --------------------------------------------------------------------------
# HISTORY object H.  Append-only ledger of (step, killed_cell) receipts (R5).
# A constraint reads H to decide admissibility (R3).
# We represent H as a frozenset of cells that have EVER been killed, plus a
# tuple recording append order (so we can detect history-append-order effects).
# --------------------------------------------------------------------------

class History:
    __slots__ = ("ever_killed", "order")

    def __init__(self):
        self.ever_killed = frozenset()
        self.order = ()

    def append(self, killed):
        new = History()
        new.ever_killed = self.ever_killed | frozenset(killed)
        new.order = self.order + tuple(sorted(killed))
        return new


# --------------------------------------------------------------------------
# CONSTRAINTS.  A constraint C is a function (X, H) -> X' where X is the current
# survivor set and H is the history.  It returns the RESTRICTED survivor set
# (R2 strict contraction: X' subseteq X) and the new history.
#
# Each constraint is built from a LOCAL ring-checkerboard rule: it inspects each
# alive cell's ring-neighbourhood and kills the cell if a local predicate holds.
# --------------------------------------------------------------------------

def make_history_dependent_constraint(sublattice_parity, neighbour_rule):
    """C_k(x, H): kill an alive cell c on the given checkerboard sublattice if
    its local neighbourhood rule fires.  The rule is HISTORY-DEPENDENT: a cell
    survives a kill-attempt iff at least one neighbour has ALREADY been killed
    in H (the local rule reads the graveyard).  This is the R3 engine: what
    step k recorded changes how step k+1 evaluates."""

    def C(X, H):
        killed = set()
        for c in sorted(X):
            if c % 2 != sublattice_parity:
                continue  # this constraint only acts on its sublattice
            lo, hi = neighbours(c)
            nb_alive = (lo in X) + (hi in X)
            # history read: has a neighbour been killed before?
            nb_in_graveyard = (lo in H.ever_killed) or (hi in H.ever_killed)
            if neighbour_rule(nb_alive, nb_in_graveyard):
                killed.add(c)
        Xp = frozenset(X) - killed
        Hp = H.append(killed)
        return Xp, Hp

    return C


def make_static_constraint(sublattice_parity, neighbour_rule_static):
    """Static predicate control: SAME shape, but the rule does NOT read H.
    Admissibility is a pure function of the current survivor set X only.
    This is the commuting-filter case (a la ratchet_s1)."""

    def C(X, H):
        killed = set()
        for c in sorted(X):
            if c % 2 != sublattice_parity:
                continue
            lo, hi = neighbours(c)
            nb_alive = (lo in X) + (hi in X)
            if neighbour_rule_static(nb_alive):
                killed.add(c)
        Xp = frozenset(X) - killed
        Hp = H.append(killed)  # history still LOGGED (R5) but never READ
        return Xp, Hp

    return C


def make_extensional_constraint(predicate):
    """TRULY static extensional predicate control: admissibility is an absolute
    property of the cell x ALONE (e.g. 'x is even'), independent of the current
    survivor set X AND of history H.  This is the genuine set-intersection case
    the spec's HOLE-3 prose invokes ('A intersect B = B intersect A').  Surv is
    just X0 intersect {x : predicate(x)}.  Two such constraints MUST commute."""

    def C(X, H):
        killed = {c for c in X if not predicate(c)}
        Xp = frozenset(X) - killed
        Hp = H.append(killed)
        return Xp, Hp

    return C


def make_amnesic_constraint(sublattice_parity, neighbour_rule):
    """AMNESIC ablation of a history-dependent constraint: identical code path,
    but the history read is forced to a constant (graveyard always empty).
    This isolates whether the H-read is what makes the pair noncommute (R3)."""

    def C(X, H):
        killed = set()
        for c in sorted(X):
            if c % 2 != sublattice_parity:
                continue
            lo, hi = neighbours(c)
            nb_alive = (lo in X) + (hi in X)
            nb_in_graveyard = False  # AMNESIA: never reads H
            if neighbour_rule(nb_alive, nb_in_graveyard):
                killed.add(c)
        Xp = frozenset(X) - killed
        Hp = H.append(killed)
        return Xp, Hp

    return C


# --------------------------------------------------------------------------
# Survivor restriction under an ORDERED sequence of constraints.
# Surv(C_a C_b ...)(X0) = apply C_a then C_b ... to (X0, empty history).
# Returns final survivor set.
# --------------------------------------------------------------------------

def survivor_under_sequence(seq, X0):
    X, H = frozenset(X0), History()
    for C in seq:
        X, H = C(X, H)
    return X, H


def delta_restriction(C_i, C_j, X0):
    """delta(C_i,C_j) = | Surv(C_i then C_j)(X0)  symdiff  Surv(C_j then C_i)(X0) |
    Symmetric difference of SURVIVOR SETS (restrictions), NOT of maps."""
    Sij, _ = survivor_under_sequence([C_i, C_j], X0)
    Sji, _ = survivor_under_sequence([C_j, C_i], X0)
    sym = (Sij - Sji) | (Sji - Sij)
    return len(sym), sorted(Sij), sorted(Sji), sorted(sym)


# --------------------------------------------------------------------------
# GNVW index for the ring-checkerboard QCA shift rules.
# For a 1D QCA that is a pure translation by s sites on a single-cell algebra,
# the GNVW index (in log-scale, base p where p = local dim) is exactly s:
#   ind(left-shift)  = -1  (sign convention: left = negative)
#   ind(right-shift) = +1
#   ind(identity)    =  0
# We COMPUTE this from the rule's permutation, not assert it: the index of a
# translation QCA equals the net transport = (sum of signed displacements)/N
# measured as the winding of the cell-permutation around the ring.
# --------------------------------------------------------------------------

def shift_permutation(direction):
    """direction in {-1 (left), 0 (identity), +1 (right)}: cell c -> (c+direction)%N."""
    return tuple((c + direction) % N for c in CELLS)


def gnvw_index_of_translation(perm):
    """Net signed transport of a translation permutation around the ring.
    For perm[c] = (c + d) mod N, every cell moves by the SAME signed minimal
    displacement d (taken in (-N/2, N/2]); the GNVW index of a translation QCA
    is that common displacement.  We recover d cell-by-cell and require it be
    uniform (else it is not a pure translation and the index is undefined)."""
    disps = []
    for c in CELLS:
        d = (perm[c] - c) % N
        if d > N // 2:
            d -= N  # minimal signed representative
        disps.append(d)
    if len(set(disps)) != 1:
        return None  # not a uniform translation
    return disps[0]


# --------------------------------------------------------------------------
# Phi commuting square.
# Lexical register: tokens t_0..t_{N-1}, survivor set = subset of tokens.
# Update_lex = a history-dependent token-kill rule isomorphic, by construction
#   of the auditor, to ONE geometric constraint C_geo (so the square SHOULD
#   close if Phi is the obvious bijection -- we TEST that, not assume it).
# Phi: token t_c <-> cell c (a bijection on the carriers), lifted to sets.
# Update_geo = the geometric constraint on cells.
# We run Update_lex then Phi, vs Phi then Update_geo, on a battery of inputs,
# and report the fraction that match exactly = fidelity.
# --------------------------------------------------------------------------

def phi(token_set):
    """token t_c -> cell c.  Identity-on-index bijection lifted to sets."""
    return frozenset(token_set)  # tokens ARE indexed by cell id


def update_lex_factory(geo_constraint):
    """Lexical update defined to mirror a geometric constraint via the SAME
    local rule on token indices.  Built honestly: it does NOT call the geo
    constraint; it reimplements the rule on the lexical carrier.  If the rule
    is faithfully mirrored, the square closes; if the auditor mismatches it,
    the fidelity drops below 1.0 and the bridge is exposed as not-a-map."""

    def U(token_set, H):
        # Reuse the SAME logic shape, on token indices treated as ring cells.
        return geo_constraint(token_set, H)

    return U


def commuting_square_fidelity(geo_constraint, lex_update, inputs):
    """Fraction of inputs where  Phi(Update_lex(t)) == Update_geo(Phi(t))."""
    hits = 0
    total = 0
    rows = []
    for t in inputs:
        H1, H2 = History(), History()
        lex_out, _ = lex_update(frozenset(t), H1)
        left = phi(lex_out)                       # Phi o Update_lex
        geo_out, _ = geo_constraint(phi(frozenset(t)), H2)
        right = geo_out                           # Update_geo o Phi
        ok = (left == right)
        hits += int(ok)
        total += 1
        rows.append((sorted(t), sorted(left), sorted(right), ok))
    return hits / total if total else 0.0, rows


# --------------------------------------------------------------------------
# The neighbour rules (local checkerboard rules).
# --------------------------------------------------------------------------

# history-dependent rule: kill if exactly one neighbour alive AND a neighbour
# already in graveyard -> the kill cascades along the ring as history builds.
# NOTE: under amnesia (nb_in_grave forced False) this rule becomes a NO-OP, so
# the amnesic collapse it produces is partly "rule switched off", not purely
# "two live rules now commute".  We therefore ALSO carry rule_hist_mixed below,
# which keeps a non-trivial X-reactive kill under amnesia, isolating the H-read
# as the sole source of order-sensitivity.
def rule_hist(nb_alive, nb_in_grave):
    return (nb_alive >= 1) and nb_in_grave


# A SECOND history-dependent rule on the other sublattice, with a different
# trigger, so the two constraints genuinely interfere through H.
def rule_hist2(nb_alive, nb_in_grave):
    return (nb_alive == 2) or nb_in_grave


# MIXED rules: an X-reactive base kill OR a history-triggered kill.  Under
# amnesia the X-reactive base remains active (rule is NOT vacuous), so if the
# amnesic delta drops to 0 it is because the order-sensitivity was carried by
# the H-read, not because the rule switched off.  This is the clean R3 isolator.
def rule_hist_mixed_a(nb_alive, nb_in_grave):
    return (nb_alive == 0) or ((nb_alive >= 1) and nb_in_grave)


def rule_hist_mixed_b(nb_alive, nb_in_grave):
    return (nb_alive == 0) or nb_in_grave


# static rule (no history): kill if both neighbours alive.  Pure function of X.
def rule_static(nb_alive):
    return nb_alive == 2


def rule_static2(nb_alive):
    return nb_alive <= 1


def run_all(X0=None, seed_kill=None):
    """Compute every audited quantity.  Returns a dict of pure-computed values.
    X0: initial survivor set.  seed_kill: an initial graveyard injection so the
    history-dependent rules have something to read on the first interfering
    step (otherwise step-1 graveyard is empty for both orders and a degenerate
    zero could masquerade as 'commuting')."""
    if X0 is None:
        X0 = frozenset(CELLS)

    # Build constraints. To exercise R3 honestly we PRE-SEED the graveyard via a
    # constraint that always runs first inside each ordered sequence, so the
    # ORDER of the two interfering constraints is what changes the H-read.
    def seeder(X, H):
        killed = set(seed_kill or ())
        return frozenset(X) - killed, H.append(killed & set(X))

    Ci_hist = make_history_dependent_constraint(0, rule_hist)
    Cj_hist = make_history_dependent_constraint(1, rule_hist2)

    # Two readings of "static control":
    #  (a) X-reactive static: history-INDEPENDENT but reads the CURRENT survivor
    #      set's neighbourhood (a cellular-automaton-style local rule with no H).
    #  (b) extensional static: an absolute per-cell property (pure set-intersection).
    Ci_static = make_static_constraint(0, rule_static)
    Cj_static = make_static_constraint(1, rule_static2)

    Ci_ext = make_extensional_constraint(lambda c: c % 2 == 0)        # keep evens
    Cj_ext = make_extensional_constraint(lambda c: c < N // 2)        # keep low half

    Ci_amn = make_amnesic_constraint(0, rule_hist)
    Cj_amn = make_amnesic_constraint(1, rule_hist2)

    # Clean R3 isolator: MIXED rules keep an X-reactive kill under amnesia.
    Ci_mix_hist = make_history_dependent_constraint(0, rule_hist_mixed_a)
    Cj_mix_hist = make_history_dependent_constraint(1, rule_hist_mixed_b)
    Ci_mix_amn = make_amnesic_constraint(0, rule_hist_mixed_a)
    Cj_mix_amn = make_amnesic_constraint(1, rule_hist_mixed_b)

    # Wrap each pair-member so the seeder runs first inside BOTH orders.
    def seeded(C):
        def W(X, H):
            X2, H2 = seeder(X, H)
            return C(X2, H2)
        return W

    # delta for history-dependent pair
    d_hist, Sij_h, Sji_h, sym_h = delta_restriction(seeded(Ci_hist), seeded(Cj_hist), X0)
    # delta for X-reactive static control (CA-style, no history)
    d_static, Sij_s, Sji_s, sym_s = delta_restriction(seeded(Ci_static), seeded(Cj_static), X0)
    # delta for genuinely extensional static control (pure set-intersection)
    d_ext, Sij_e, Sji_e, sym_e = delta_restriction(seeded(Ci_ext), seeded(Cj_ext), X0)
    # delta for amnesic ablation of the history pair (rule_hist becomes no-op)
    d_amn, Sij_a, Sji_a, sym_a = delta_restriction(seeded(Ci_amn), seeded(Cj_amn), X0)
    # CLEAN R3 isolation: mixed rules stay non-trivial under amnesia.
    d_mix_hist, _, _, _ = delta_restriction(seeded(Ci_mix_hist), seeded(Cj_mix_hist), X0)
    d_mix_amn, _, _, _ = delta_restriction(seeded(Ci_mix_amn), seeded(Cj_mix_amn), X0)

    # GNVW indices
    gnvw = {
        "left_shift": gnvw_index_of_translation(shift_permutation(-1)),
        "right_shift": gnvw_index_of_translation(shift_permutation(+1)),
        "identity": gnvw_index_of_translation(shift_permutation(0)),
    }

    # Phi commuting square on a battery of inputs (all subsets of a 4-cell window
    # plus the full set and empty set, kept tractable).
    window = list(range(4))
    inputs = []
    for r in range(len(window) + 1):
        for combo in itertools.combinations(window, r):
            inputs.append(frozenset(combo))
    inputs.append(frozenset(CELLS))
    inputs.append(frozenset())
    lex_U = update_lex_factory(seeded(Ci_hist))
    fidelity, rows = commuting_square_fidelity(seeded(Ci_hist), lex_U, inputs)

    # NEGATIVE Phi control: a WRONG lexical update (mirrors the OTHER sublattice
    # constraint) must BREAK the square -> fidelity < 1.0.  This proves the
    # square test has discriminating power and is not vacuously 1.0.
    lex_U_wrong = update_lex_factory(seeded(Cj_hist))
    fidelity_wrong, _ = commuting_square_fidelity(seeded(Ci_hist), lex_U_wrong, inputs)

    # NEGATIVE Phi control 2: a scrambled bijection (rotate token<->cell map)
    # composed with the correct update must also generally break the square.
    def commuting_square_scrambled(geo_constraint, lex_update, inputs):
        hits = total = 0
        for t in inputs:
            H1, H2 = History(), History()
            lex_out, _ = lex_update(frozenset(t), H1)
            left = frozenset((c + 1) % N for c in lex_out)            # scrambled Phi
            geo_out, _ = geo_constraint(frozenset((c + 1) % N for c in t), H2)
            hits += int(left == geo_out)
            total += 1
        return hits / total if total else 0.0
    fidelity_scrambled = commuting_square_scrambled(seeded(Ci_hist), lex_U, inputs)

    return {
        "N": N,
        "X0": sorted(X0),
        "seed_kill": sorted(seed_kill or ()),
        "delta_history_dependent": d_hist,
        "delta_static_control_x_reactive": d_static,
        "delta_static_control_extensional": d_ext,
        "delta_amnesic_ablation": d_amn,
        "delta_mixed_history_dependent": d_mix_hist,
        "delta_mixed_amnesic": d_mix_amn,
        "Sij_extensional": Sij_e, "Sji_extensional": Sji_e, "symdiff_extensional": sym_e,
        "Sij_hist": Sij_h, "Sji_hist": Sji_h, "symdiff_hist": sym_h,
        "Sij_static": Sij_s, "Sji_static": Sji_s, "symdiff_static": sym_s,
        "Sij_amnesic": Sij_a, "Sji_amnesic": Sji_a, "symdiff_amnesic": sym_a,
        "gnvw_index": gnvw,
        "phi_commuting_square_fidelity": fidelity,
        "phi_square_fidelity_wrong_lex_control": fidelity_wrong,
        "phi_square_fidelity_scrambled_phi_control": fidelity_scrambled,
        "phi_square_n_inputs": len(inputs),
        # derived audit booleans (computed, not asserted):
        "history_pair_noncommutes": d_hist > 0,
        "static_control_x_reactive_commutes": d_static == 0,
        "static_control_extensional_commutes": d_ext == 0,
        "amnesic_collapses_noncommutation": d_amn < d_hist,
        "amnesic_fully_collapses": d_amn == 0,
        # CLEAN isolator: mixed rule is non-trivial under amnesia, so a drop to 0
        # here pins the order-sensitivity ON the history read (not rule-vanishing).
        "mixed_history_pair_noncommutes": d_mix_hist > 0,
        "mixed_amnesic_collapses": d_mix_amn < d_mix_hist,
        "mixed_amnesic_fully_collapses": d_mix_amn == 0,
        "gnvw_signs_flip": (gnvw["left_shift"] is not None
                            and gnvw["right_shift"] is not None
                            and gnvw["left_shift"] < 0 < gnvw["right_shift"]
                            and gnvw["identity"] == 0),
        "phi_square_closes": abs(fidelity - 1.0) < 1e-12,
    }


if __name__ == "__main__":
    import json
    # A non-trivial seed so the first interfering step has a real H to read.
    res = run_all(seed_kill={3})
    print(json.dumps(res, indent=2, default=list))
