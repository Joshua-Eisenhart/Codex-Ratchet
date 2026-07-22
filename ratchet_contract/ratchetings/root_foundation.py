#!/usr/bin/env python3
"""Root-below-magma probe: the actual root mechanics behind `a = a iff a ~ b`.

Objects (deliberately below magma/algebra -- no operation on S, only probes):

  S       finite carrier set: all 16 tuples (a,b,c,h) in {0,1}^4.
  M       probe family: a list of named functions S -> finite outcome set.
  ~_M     a ~ b iff every probe in M agrees: p(a) == p(b) for all p in M.
  Q=S/~_M the induced quotient: partition of S into ~_M-classes.
  reidentify(S, M, proposal) -- the gate: a proposed partition earns
          "identity" status iff it reproduces Q exactly (no over-merge,
          no over-split). This is the root's only admission mechanism.

The 4th coordinate h is a HIDDEN attribute never read by the "full" active
probe family M3={p_a,p_b,p_c}. It exists so the sim can honestly demonstrate
the completeness objection (NVIDIA panel, qwen3): M3 LOOKS maximal from
inside M3 but is not; adding p_h strictly refines it further. No finite
self-check can certify a probe family is complete.

This probe runs MANY NEGATIVES, each a control that must genuinely FLIP
(catch the adversarial case) or is reported as a real hole -- not smoothed.
See NEGATIVES list in main() for the 6 required families plus 2 discovered
sub-negatives (malformed/overlapping proposals under NEG3).

classification = "tool_lego_fit_probe"; promotion_allowed = False;
ordering_status = "PROPOSED not canon". This settles nothing about magma,
semigroup, or any algebraic layer above -- it is the root layer only:
finite S, probe family M, ~_M, Q, and the reidentify gate.
"""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Any, Callable

classification = "tool_lego_fit_probe"
promotion_allowed = False
ordering_status = "PROPOSED not canon"

TOOL_MANIFEST = {
    "python_stdlib": {"tried": True, "used": True,
                       "reason": "Root mechanics are finite-set combinatorics (16-element carrier, probe tuples, partitions) -- itertools/collections suffice exactly; no numeric approximation involved anywhere."},
    "numpy": {"tried": False, "used": False,
              "reason": "Not needed: no numeric arrays, no floating point, exact finite combinatorics only."},
    "sympy": {"tried": False, "used": False,
              "reason": "Not needed: no algebraic/symbolic expressions at the root layer (magma/semigroup structure is a different, higher lego, deliberately out of scope here)."},
    "z3": {"tried": False, "used": False,
           "reason": "Not run. The prior systemic finding (committed 2026-07-21, magma/vn/anticommutation sims) showed generic single-valued-function SMT encodings are decorative tautologies mislabeled load_bearing. Root-layer claims here (transitivity of tuple equality, partition well-formedness, refinement) are finite and directly enumerable in full -- exhaustive enumeration over |S|=16 is a stronger, non-decorative witness than a generic SMT non-vacuity check would be. Omitting z3 here is an honest scope choice, not a coverage gap."},
    "cvc5": {"tried": False, "used": False, "reason": "Same reasoning as z3 above -- not run."},
    "jax": {"tried": False, "used": False, "reason": "No batched/exhaustive numeric workload; |S|=16 is enumerated directly in pure Python."},
    "julia": {"tried": False, "used": False, "reason": "No numeric linear algebra at this layer; not run."},
}

TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "load_bearing",
    "numpy": None, "sympy": None, "z3": None, "cvc5": None, "jax": None, "julia": None,
}

Elem = tuple[int, int, int, int]
Probe = Callable[[Elem], int]


def build_S() -> list[Elem]:
    return [(a, b, c, h) for a in (0, 1) for b in (0, 1) for c in (0, 1) for h in (0, 1)]


def probes() -> dict[str, Probe]:
    return {
        "p_a": lambda s: s[0],
        "p_b": lambda s: s[1],
        "p_c": lambda s: s[2],
        "p_h": lambda s: s[3],  # hidden: not in any "active" M below unless named
    }


def probe_signature(s: Elem, M: list[str], P: dict[str, Probe]) -> tuple[int, ...]:
    return tuple(P[name](s) for name in M)


def indistinguishable_pairwise(a: Elem, b: Elem, M: list[str], P: dict[str, Probe]) -> bool:
    """a ~ b iff every probe in M agrees -- computed directly as a universal
    quantifier over M, NOT via signature equality. Kept as a second,
    independently-written implementation of ~_M so it can be cross-checked
    against probe_signature equality (a real correctness check on the root
    mechanism itself, not just on its inputs)."""
    return all(P[name](a) == P[name](b) for name in M)


def quotient(S: list[Elem], M: list[str], P: dict[str, Probe]) -> list[frozenset[Elem]]:
    groups: dict[tuple[int, ...], list[Elem]] = {}
    for s in S:
        groups.setdefault(probe_signature(s, M, P), []).append(s)
    return [frozenset(v) for v in groups.values()]


def as_partition_set(classes: list) -> frozenset[frozenset[Elem]]:
    return frozenset(frozenset(c) for c in classes)


def is_valid_partition(S: list[Elem], proposed: list[list[Elem]]) -> tuple[bool, str]:
    """Well-formedness check: every element of S appears in EXACTLY one
    proposed class. Missing element -> incomplete proposal. Element in >1
    class -> overlapping proposal (the tolerance-relation failure mode,
    NEG4, reappearing as a malformed-input case)."""
    seen: dict[Elem, int] = {}
    for ci, cls in enumerate(proposed):
        for s in cls:
            seen[s] = seen.get(s, 0) + 1
    missing = [s for s in S if s not in seen]
    overlapping = [s for s, n in seen.items() if n > 1]
    if missing:
        return False, f"MALFORMED_PROPOSAL: {len(missing)} element(s) missing from every class, e.g. {missing[0]}"
    if overlapping:
        return False, f"MALFORMED_PROPOSAL: {len(overlapping)} element(s) assigned to >1 class, e.g. {overlapping[0]}"
    return True, "well_formed"


def reidentify_naive(S: list[Elem], M: list[str], P: dict[str, Probe],
                      proposed: list[list[Elem]]) -> dict[str, Any]:
    """The gate WITHOUT a well-formedness pre-check -- deliberately naive,
    to test whether skipping validation causes a malformed proposal to be
    silently mislabeled as an ordinary over-split/over-merge rather than
    flagged as structurally invalid input."""
    over_merge = []
    for cls in proposed:
        for a, b in itertools.combinations(cls, 2):
            if not indistinguishable_pairwise(a, b, M, P):
                witness = next(name for name in M if P[name](a) != P[name](b))
                over_merge.append({"pair": [a, b], "witness_probe": witness,
                                    "a_val": P[witness](a), "b_val": P[witness](b)})
    proposed_class_of: dict[Elem, frozenset[Elem]] = {}
    for cls in proposed:
        for s in cls:
            proposed_class_of[s] = frozenset(cls)
    over_split = []
    for a, b in itertools.combinations(S, 2):
        if indistinguishable_pairwise(a, b, M, P):
            if proposed_class_of.get(a) != proposed_class_of.get(b):
                over_split.append({"pair": [a, b]})
    actual = as_partition_set(quotient(S, M, P))
    proposed_set = as_partition_set(proposed)
    earned = (not over_merge) and (not over_split) and (actual == proposed_set)
    return {
        "earned": earned,
        "over_merge_witnesses": over_merge[:5],
        "over_merge_count": len(over_merge),
        "over_split_witnesses": over_split[:5],
        "over_split_count": len(over_split),
        "matches_actual_quotient": actual == proposed_set,
    }


def reidentify_hardened(S: list[Elem], M: list[str], P: dict[str, Probe],
                         proposed: list[list[Elem]]) -> dict[str, Any]:
    """The gate WITH the well-formedness pre-check. Malformed proposals are
    rejected as MALFORMED_PROPOSAL before over-merge/over-split logic runs,
    instead of being silently mis-scored as an over-split."""
    valid, reason = is_valid_partition(S, proposed)
    if not valid:
        return {"earned": False, "rejected_as": "MALFORMED_PROPOSAL", "reason": reason}
    result = reidentify_naive(S, M, P, proposed)
    result["rejected_as"] = None
    return result


def is_transitive(carrier: list, rel: Callable[[Any, Any], bool]) -> tuple[bool, Any]:
    for a, b, c in itertools.product(carrier, repeat=3):
        if rel(a, b) and rel(b, c) and not rel(a, c):
            return False, (a, b, c)
    return True, None


def main() -> None:
    S = build_S()
    P = probes()
    M_empty: list[str] = []
    M1 = ["p_a"]
    M2 = ["p_a", "p_b"]
    M3 = ["p_a", "p_b", "p_c"]           # "active/full" family -- deliberately NOT complete (h hidden)
    M4 = ["p_a", "p_b", "p_c", "p_h"]    # fully faithful: adds the hidden probe

    negatives: list[dict[str, Any]] = []

    # --- sanity: root axiom mechanics themselves (positive controls) -------
    refl = all(indistinguishable_pairwise(s, s, M3, P) for s in S)
    sym = all(indistinguishable_pairwise(a, b, M3, P) == indistinguishable_pairwise(b, a, M3, P)
              for a, b in itertools.combinations(S, 2))
    iff_consistency = all(
        indistinguishable_pairwise(a, b, M2, P) == (probe_signature(a, M2, P) == probe_signature(b, M2, P))
        for a, b in itertools.combinations(S, 2)
    )
    q_empty = quotient(S, M_empty, P)
    vacuous_merge = len(q_empty) == 1 and q_empty[0] == frozenset(S)

    root_sanity = {
        "reflexivity_a_tilde_a_holds_for_all_s_under_M3": refl,
        "symmetry_holds_for_all_pairs_under_M3": sym,
        "iff_pairwise_vs_signature_formulations_agree_under_M2": iff_consistency,
        "vacuous_case_empty_M_merges_everything": vacuous_merge,
        "vacuous_case_note": "With M=[], 'all probes agree' is vacuously true for every pair -- ~_[] merges the whole of S into one class. This is the literal semantics of the universal quantifier in the iff, not a bug; flagged explicitly so it is never silently mistaken for full individuation.",
    }

    # --- NEG1: under-discriminating M -> quotient too coarse, HOLD ---------
    Q1 = quotient(S, M1, P)
    Q3 = quotient(S, M3, P)
    # M3 used ONLY as a test-oracle reference here, never as a production
    # ground truth -- it demonstrates M1 is coarse relative to a stronger
    # (but itself still incomplete, see NEG6b) family.
    q1_is_coarse = any(len({probe_signature(s, M3, P) for s in cls}) > 1 for cls in Q1)
    negatives.append({
        "id": "NEG1_underdiscriminating_M",
        "attack": "Use M1=[p_a] (weak) to compute a quotient, then check whether the mechanism flags it as provisional/coarse rather than presenting it as final identity.",
        "n_classes_M1": len(Q1),
        "coarse_relative_to_M3": q1_is_coarse,
        "flip": bool(q1_is_coarse),
        "verdict": "HOLD: M1's quotient merges elements M3 can separate -- caught, correctly not asserted as final identity." if q1_is_coarse else "SILENT HOLE: M1's quotient was NOT flagged coarse even though a stronger reference exists.",
    })

    # --- NEG2: reidentify over-merges -> INELIGIBLE, must be caught --------
    # Under M2, elements differing in p_a must never be proposed same-class.
    e1, e2 = S[0], S[8]  # (0,0,0,0) vs (1,0,0,0): differ in p_a
    assert e1[0] != e2[0]
    bad_merge_proposal = [c for c in [list(q) for q in Q1]]  # M1's own (coarser) partition,
    # tested AGAINST the finer M2 -- M1's classes merge pairs M2 distinguishes.
    over_merge_check = reidentify_hardened(S, M2, P, bad_merge_proposal)
    caught_over_merge = (not over_merge_check["earned"]) and over_merge_check.get("over_merge_count", 0) > 0
    negatives.append({
        "id": "NEG2_reidentify_over_merges",
        "attack": "Propose M1's (coarser) partition as if it were M2's quotient -- claims identity for pairs M2 actually separates.",
        "gate_result": {"earned": over_merge_check["earned"], "over_merge_count": over_merge_check.get("over_merge_count"),
                         "example_witness": (over_merge_check.get("over_merge_witnesses") or [None])[0]},
        "flip": bool(caught_over_merge),
        "verdict": "INELIGIBLE, correctly caught -- witness probe names the exact separating measurement." if caught_over_merge else "SILENT HOLE: over-merge was not caught.",
    })

    # --- NEG3: reidentify over-splits -> unearned identity, must be caught -
    # Under M2, split S into 4 groups by (a,b) as usual, but then further
    # slice ONE of those groups by c/h -- distinctions M2 cannot see.
    Q2 = quotient(S, M2, P)
    over_split_proposal = []
    for cls in Q2:
        cls_list = list(cls)
        if len(cls_list) > 1:
            over_split_proposal.append([cls_list[0]])
            over_split_proposal.append(cls_list[1:])
        else:
            over_split_proposal.append(cls_list)
    over_split_check = reidentify_hardened(S, M2, P, over_split_proposal)
    caught_over_split = (not over_split_check["earned"]) and over_split_check.get("over_split_count", 0) > 0
    negatives.append({
        "id": "NEG3_reidentify_over_splits",
        "attack": "Split every M2-class into singleton + rest -- distinguishes pairs M2 cannot actually separate.",
        "gate_result": {"earned": over_split_check["earned"], "over_split_count": over_split_check.get("over_split_count")},
        "flip": bool(caught_over_split),
        "verdict": "Unearned identity, correctly caught -- no probe in M2 licenses the split." if caught_over_split else "SILENT HOLE: over-split was not caught.",
    })

    # --- NEG3b/c: malformed proposals (missing / overlapping element) ------
    # Drop exactly ONE straggler element from one class (not a whole class),
    # so its former classmates remain in the proposal -- this is the shape
    # that can actually trigger the naive gate's over-split path.
    missing_proposal = [list(c) for c in Q2]
    missing_proposal[-1] = missing_proposal[-1][1:]
    naive_on_missing = reidentify_naive(S, M2, P, missing_proposal)
    hardened_on_missing = reidentify_hardened(S, M2, P, missing_proposal)
    naive_mislabels_missing = (not naive_on_missing["earned"]) and naive_on_missing.get("rejected_as") is None \
        and naive_on_missing.get("over_split_count", 0) > 0
    hardened_catches_missing = hardened_on_missing.get("rejected_as") == "MALFORMED_PROPOSAL"

    overlap_proposal = [list(c) for c in Q2]
    overlap_proposal[0] = overlap_proposal[0] + [overlap_proposal[1][0]]  # duplicate one element
    naive_on_overlap = reidentify_naive(S, M2, P, overlap_proposal)
    hardened_on_overlap = reidentify_hardened(S, M2, P, overlap_proposal)
    hardened_catches_overlap = hardened_on_overlap.get("rejected_as") == "MALFORMED_PROPOSAL"

    negatives.append({
        "id": "NEG3b_malformed_proposal_missing_element",
        "attack": "Propose a partition that silently drops an element of S from every class (incomplete coverage).",
        "naive_gate_result": {"earned": naive_on_missing["earned"], "labeled_as": "over_split" if naive_mislabels_missing else "other",
                               "over_split_count": naive_on_missing.get("over_split_count")},
        "hardened_gate_result": hardened_on_missing,
        "flip": bool(hardened_catches_missing),
        "finding": "REAL HOLE FOUND, THEN CLOSED: the naive gate (no well-formedness pre-check) does reject the proposal (earned=False) but MISLABELS the failure as an ordinary over-split, not as a malformed/incomplete input -- a misleading diagnostic, not a false admission. The hardened gate adds an explicit well-formedness check and reports MALFORMED_PROPOSAL correctly." if naive_mislabels_missing else "No mislabeling found: the naive gate still correctly returns earned=False for this missing-element case (over_split_count=%d), it just gives no specific reason string. The hardened gate additionally names the defect (MALFORMED_PROPOSAL) instead of leaving the caller to infer it." % naive_on_missing.get("over_split_count", -1),
        "verdict": ("Caught by both gates; the naive gate's mislabeling as an ordinary over-split is reported honestly, not smoothed." if naive_mislabels_missing else "Caught by both gates; the hardened gate additionally names the defect correctly where the naive gate only returns an unlabeled rejection."),
    })
    negatives.append({
        "id": "NEG3c_malformed_proposal_overlapping_element",
        "attack": "Propose a partition that assigns one element of S to two different classes (overlapping blocks).",
        "hardened_gate_result": hardened_on_overlap,
        "flip": bool(hardened_catches_overlap),
        "verdict": "Caught and correctly labeled MALFORMED_PROPOSAL by the hardened gate." if hardened_catches_overlap else "SILENT HOLE: overlapping proposal was not caught.",
    })

    # --- NEG4: tolerance (non-transitive) vs equivalence (transitive) ------
    T = list(range(6))
    def tolerance_rel(x: int, y: int) -> bool:
        return abs(x - y) <= 1
    tol_transitive, tol_witness = is_transitive(T, tolerance_rel)
    # Contrast: naive "blocks" built directly from a non-transitive relation
    # are not well-defined disjoint classes (block(0) != block(1) despite
    # tolerance_rel(0,1) holding).
    block0 = frozenset(x for x in T if tolerance_rel(0, x))
    block1 = frozenset(x for x in T if tolerance_rel(1, x))
    blocks_disagree_despite_related = (tolerance_rel(0, 1) and block0 != block1)

    def probe_rel_M2(a: Elem, b: Elem) -> bool:
        return indistinguishable_pairwise(a, b, M2, P)
    probe_transitive, probe_witness = is_transitive(S, probe_rel_M2)

    caught_tolerance_failure = (not tol_transitive) and blocks_disagree_despite_related
    negatives.append({
        "id": "NEG4_tolerance_vs_equivalence",
        "attack": "Build a reflexive+symmetric but NON-transitive tolerance relation (|x-y|<=1 on {0..5}) and check whether the mechanism can tell its 'blocks' are not a genuine quotient.",
        "tolerance_relation_is_transitive": tol_transitive,
        "tolerance_transitivity_witness_triple": tol_witness,
        "naive_blocks_disagree_for_a_related_pair": blocks_disagree_despite_related,
        "contrast_probe_induced_relation_is_transitive_on_full_S": probe_transitive,
        "probe_transitivity_witness_if_any": probe_witness,
        "flip": bool(caught_tolerance_failure and probe_transitive),
        "verdict": ("Tolerance relation correctly detected as non-transitive (witness triple recorded); its naive 'blocks' are shown NOT to be well-defined disjoint classes. Contrast: ~_M2, built from equality of probe tuples, is transitive on the FULL 16-element S with zero violations found by exhaustive check (not asserted) -- a genuine quotient exists there, and does not exist for the tolerance relation."
                    if (caught_tolerance_failure and probe_transitive) else
                    "SILENT HOLE: tolerance-vs-equivalence distinction was not correctly detected."),
    })

    # --- NEG5: probe-family enlargement refines the quotient one-way -------
    refines = all(any(c2 <= c1 for c1 in Q1) for c2 in Q2)  # every Q2-class subset of some Q1-class
    strictly_finer = len(Q2) > len(Q1)
    # forward (forgetful) map Q2 -> Q1 is well-defined: each Q2 class's
    # elements all land in the SAME Q1 class.
    forward_well_defined = True
    for c2 in Q2:
        parents = {c1 for c1 in Q1 if any(x in c1 for x in c2)}
        if len(parents) != 1:
            forward_well_defined = False
            break
    # backward map Q1 -> Q2: pick one Q1 class and show it corresponds to
    # MORE THAN ONE Q2 class -- so no single-valued reverse function exists
    # (recovering the added distinction from Q1 alone is impossible).
    backward_class = Q1[0]
    children = {c2 for c2 in Q2 if c2 <= backward_class}
    backward_not_well_defined = len(children) > 1

    negatives.append({
        "id": "NEG5_probe_enlargement_refines_oneway",
        "attack": "Add p_b to M1 (-> M2) and check the quotient only ever refines (never coarsens), and that reversing (recovering the finer quotient from the coarser one alone) is impossible.",
        "Q1_class_count": len(Q1), "Q2_class_count": len(Q2),
        "every_Q2_class_subset_of_a_Q1_class": refines,
        "strictly_finer": strictly_finer,
        "forward_forgetful_map_Q2_to_Q1_well_defined": forward_well_defined,
        "backward_map_Q1_to_Q2_well_defined": not backward_not_well_defined,
        "example_Q1_class_with_multiple_Q2_children": len(children),
        "flip": bool(refines and strictly_finer and forward_well_defined and backward_not_well_defined),
        "verdict": "Refinement confirmed one-way: forgetful map Q2->Q1 is well-defined (many-to-one); no well-defined reverse map Q1->Q2 exists (one Q1 class corresponds to multiple Q2 classes) -- the added probe's information cannot be recovered from the coarser quotient alone." if (refines and strictly_finer and forward_well_defined and backward_not_well_defined) else "SILENT HOLE: refinement one-way-ness was not confirmed as expected.",
    })

    # --- NEG6a: NVIDIA/llama -- impoverished-M over-merge (root axiom) -----
    negatives.append({
        "id": "NEG6a_nvidia_llama_impoverished_M_overmerge",
        "attack": "llama's root-axiom negative: a non-injective/impoverished probe family M over-merges genuinely different elements into one class.",
        "same_mechanism_as": "NEG1",
        "flip": bool(q1_is_coarse),
        "verdict": "Same finding as NEG1 -- caught: M1 over-merges relative to a finer reference, correctly flagged coarse/HOLD, not asserted final.",
    })

    # --- NEG6b: NVIDIA/qwen3 -- M-completeness objection -------------------
    m3_not_singletons = any(len(c) > 1 for c in Q3)
    Q4 = quotient(S, M4, P)
    m4_all_singletons = all(len(c) == 1 for c in Q4)
    hidden_probe_refines_M3 = m3_not_singletons and m4_all_singletons and len(Q4) > len(Q3)
    negatives.append({
        "id": "NEG6b_nvidia_qwen3_completeness_objection",
        "attack": "qwen3's root-axiom negative: 'iff' silently assumes M is complete/maximal -- no finite check performed using only the ACTIVE M can certify that. Demonstrate with a hidden probe p_h not in the 'active/full' family M3.",
        "M3_active_family": M3,
        "M3_quotient_has_nonsingleton_classes": m3_not_singletons,
        "M3_class_count": len(Q3),
        "hidden_probe_p_h_not_in_M3": True,
        "M4_full_family_all_singletons": m4_all_singletons,
        "M4_class_count": len(Q4),
        "flip": bool(hidden_probe_refines_M3),
        "verdict": ("Confirmed: M3 (the currently 'active/full' family) is NOT complete -- it merges pairs differing only in the hidden bit h. Adding p_h strictly refines M3's quotient to all-singletons. This is the completeness objection made concrete and computable: from INSIDE M3 there is no signal that M3 is incomplete (its own quotient looks like ordinary, unremarkable classes); completeness can only be refuted by a probe not yet in the family, never proved from within it. Every 'iff' claim in this sim is therefore reported as relative-to-active-M, never as an absolute completeness claim."
                    if hidden_probe_refines_M3 else
                    "SILENT HOLE: the completeness objection was not demonstrated as expected."),
    })

    all_flip = all(bool(n.get("flip")) for n in negatives)
    n_flip = sum(1 for n in negatives if n.get("flip"))

    verdict = "ROOT_MECHANICS_HOLD" if all_flip else "PARTIAL_HOLD_HOLES_FOUND"

    result = {
        "schema_version": "1.0",
        "layer": "root, below magma: finite S, probe family M, ~_M (a~b iff all probes in M agree), quotient Q=S/~_M, reidentify gate.",
        "carrier_S": "16 elements, all (a,b,c,h) in {0,1}^4",
        "probe_families": {"M_empty": M_empty, "M1": M1, "M2": M2, "M3_active": M3, "M4_full_incl_hidden": M4},
        "root_sanity": root_sanity,
        "negatives": negatives,
        "negatives_total": len(negatives),
        "negatives_flipped": n_flip,
        "negatives_silent_holes": len(negatives) - n_flip,
        "silent_hole_ids": [n["id"] for n in negatives if not n.get("flip")],
        "genuinely_enforced_by_root_mechanics": [
            "reflexivity and symmetry of ~_M hold for every probe family tried (structural, by construction of equality)",
            "the pairwise-agreement and signature-equality formulations of ~_M coincide exactly (cross-checked, not assumed)",
            "reidentify correctly rejects proposals that over-merge (claim identity a probe separates)",
            "reidentify correctly rejects proposals that over-split (distinguish what no probe in the active M separates)",
            "well-formedness (every element assigned to exactly one class) must be checked explicitly -- the naive gate without it mislabels a missing-element proposal as an ordinary over-split rather than a malformed input; the hardened gate closes this",
            "a non-transitive tolerance relation is correctly detected and shown NOT to yield a well-defined quotient (its naive blocks disagree for related elements); the probe-induced ~_M is exhaustively confirmed transitive on the full 16-element carrier",
            "enlarging M only ever refines the quotient (forgetful map coarser<-finer is well-defined, many-to-one); the reverse map is confirmed NOT well-defined -- refinement is one-way",
            "no probe family in this sim is ever asserted complete: M3, the richest family in active use, is shown non-complete relative to a hidden probe not yet in M3 -- completeness is a claim that can only be refuted from outside a family, never proved from inside it",
        ],
        "verdict": verdict,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "ordering_status": ordering_status,
        "floor_claims": [{"key": "ratcheting.root_foundation.negatives_flipped", "value": n_flip, "direction": "higher_is_better"}],
        "engines_ran": {"python_stdlib": True, "numpy": False, "sympy": False, "z3": False, "cvc5": False, "jax": False, "julia": False},
        "tool_manifest": TOOL_MANIFEST,
        "notes": [
            "This is the ROOT layer only: a finite set S, a probe family M, the induced ~_M, its quotient, and the reidentify gate. It does NOT build or settle anything about magma_to_semigroup or any higher lego (those are separate, already-committed sims).",
            "Fuel used: NVIDIA panel negatives on the root axiom (llama impoverished-M over-merge; qwen3 M-completeness/global-phase objection) are folded in as NEG6a/NEG6b, each mapped to a concrete, computable, finite carrier rather than left as prose.",
            "Formality deliberately eased per instruction: single plain rerun + one post_receipt_gate.sh pass (honest exit 3 acceptable); full ClaimGate tier0-4 not pushed.",
        ],
    }

    output = Path(__file__).resolve().parent / "results" / "root_foundation.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True, default=list) + "\n", encoding="utf-8")
    print(json.dumps({
        "result": str(output),
        "verdict": verdict,
        "negatives_total": len(negatives),
        "negatives_flipped": n_flip,
        "silent_hole_ids": result["silent_hole_ids"],
    }, indent=2))


if __name__ == "__main__":
    main()
