#!/usr/bin/env python3
"""
Tests for retrocausal_possibility_field_v1 -- positive + negative + boundary.

Focus of v1 (the audited gap): the SHELL ORDERING is now LOAD-BEARING in the
inward multi-shell compression. The discriminating test is the
shell-reassignment control (move a branch to a different shell, union unchanged,
the survivor must MOVE), plus the flat-union negative control that proves the
traversal is what carries it.

Run:  <sim-stack python3> tests/test_retrocausal_possibility_field_v1.py
Exits 0 only if every test passes.
"""

from __future__ import annotations

import json
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SIM_DIR = os.path.dirname(TESTS_DIR)
sys.path.insert(0, SIM_DIR)

import retrocausal_possibility_field_v1 as rpf  # noqa: E402


FAILURES: list[str] = []


def check(name: str, cond: bool) -> None:
    status = "PASS" if cond else "FAIL"
    if not cond:
        FAILURES.append(name)
    print(f"[{status}] {name}")


# =====================================================================
# POSITIVE tests -- the object instantiates with its first-class fields and the
# shell ordering is load-bearing
# =====================================================================

def positive_tests() -> None:
    print("\n=== POSITIVE (object field instantiation + shell ordering) ===")
    result = rpf.build_result()

    for k in rpf.FIRST_CLASS_KEYS:
        check(f"positive: first-class key present -> {k}", k in result)

    fc = result["future_continuations"]
    check("positive: future_continuations is a dict", isinstance(fc, dict))
    check("positive: future_continuations keyed by >=1 shell", len(fc) >= 1)
    check(
        "positive: each shell carries a LIST of >=2 distinct branches",
        all(isinstance(v, list) and len(set(v)) >= 2 for v in fc.values()),
    )

    cw = result["compatibility_weights"]
    check("positive: compatibility_weights over PAIRS (keys 'bi|bj')", all("|" in k for k in cw))
    check("positive: compatibility_weights real-valued", all(isinstance(v, float) for v in cw.values()))
    check("positive: compatibility_weights non-uniform", len(set(round(v, 12) for v in cw.values())) >= 2)

    cm = result["compression_map"]
    check("positive: compression_map direction INWARD", cm["direction"] == "INWARD")
    check("positive: compression_map records a shell traversal order",
          isinstance(cm.get("shell_traversal_order"), list) and len(cm["shell_traversal_order"]) >= 2)
    nonempty = [s for s in cm["traversal_steps"] if s["branches_on_shell"]]
    check("positive: compression_map is a MULTI-STEP traversal (>=2 non-empty shells)", len(nonempty) >= 2)
    check(
        "positive: weights computed before compression",
        cm["weights_computed_before_compression"] is True,
    )

    # the inner step OVERRIDES the outer anchor -> the second step is load-bearing
    # in the canonical instance (not a pass-through). Outer anchor != final.
    outer_anchor = nonempty[0]["selected_anchor"]
    final = cm["present_survivor"]
    check("positive: inner traversal step OVERRIDES outer anchor (multi-step is load-bearing)",
          outer_anchor != final)

    ps = result["present_survivor"]
    check("positive: present_survivor is a single branch id", isinstance(ps, str) and ps in rpf.BRANCH_STATES)
    check(
        "positive: present_survivor derived (final selected anchor of the traversal)",
        ps == cm["present_survivor"] and ps == nonempty[-1]["selected_anchor"],
    )

    rec = result["outward_record"]
    check("positive: outward_record orientation OUTWARD", rec["record_orientation"] == "OUTWARD")
    check("positive: outward_record hash-chain recomputes", rec["append_only_recomputed"] is True)
    check("positive: outward_record reflects per-shell compression steps",
          rec["reflects_per_shell_compression_steps"] is True)
    check("positive: outward_record binds the present survivor", rec["binds_present_survivor"] == ps)
    check("positive: outward_record has one entry per non-empty traversal step",
          len(rec["record_entries"]) == len(cm["traversal_steps"]))

    # THE AUDITED GAP, NOW FIXED: shell-reassignment moves the survivor
    check("positive: shell_reassignment_moves_survivor (the v1 fix)",
          result["shell_reassignment_moves_survivor"] is True)
    ctrl = result["shell_reassignment_control"]
    check("positive: shell-reassignment keeps the union identical", ctrl["union_identical"] is True)
    check("positive: shell-reassignment survivors actually differ",
          ctrl["base_present_survivor"] != ctrl["reassigned_present_survivor"])

    check("positive: all invariants hold", result["all_invariants_hold"] is True)
    check("positive: classification scratch_diagnostic", result["classification"] == "scratch_diagnostic")
    check("positive: promotion_allowed false", result["promotion_allowed"] is False)
    check("positive: formal_admission_allowed false", result["formal_admission_allowed"] is False)


# =====================================================================
# NEGATIVE tests -- each control must BREAK the result / be inert
# =====================================================================

def negative_tests() -> None:
    print("\n=== NEGATIVE (controls) ===")

    # HARD-STOP: identity compression must be detected as a break.
    inst = rpf.build_object_instance()
    inv = rpf.check_invariants(inst)
    check("hard-stop holds (future_continuations != present_survivor)",
          inv["HARD_STOP_future_continuations_ne_present_survivor"] is True)

    # (a) FLAT-UNION COLLAPSE must be INERT under the shell-reassignment:
    # collapsing the traversal to v0's flat union argmax must NOT move the
    # survivor (proving the traversal is what carries the shell-ordering effect).
    flat = rpf.flat_union_negative_control()
    check("negative (a): flat-union collapse is INERT (does NOT move survivor) -> traversal carries it",
          flat["flat_union_control_correctly_inert"] is True)
    check("negative (a): flat-union survivor is identical before/after reassignment",
          flat["base_flat_survivor"] == flat["reassigned_flat_survivor"])

    # (b) scramble future_continuations -> only 1 distinct branch per shell -> break
    scr = rpf.scramble_futures_negative_control()
    check("negative (b): scramble future_continuations breaks", scr["control_breaks"] is True)

    # (c) uniform weights -> build breaks AND the shell effect dies
    uni = rpf.uniform_weights_negative_control()
    check("negative (c): uniform weights break the build", uni["control_breaks"] is True)
    check("negative (c): uniform weights KILL the shell-reassignment effect",
          uni["uniform_correctly_kills_shell_effect"] is True)


# =====================================================================
# TRAP tests -- the v0 traps must STILL pass (no regression)
# =====================================================================

def trap_tests() -> None:
    print("\n=== TRAPS retained from v0 (must still pass) ===")
    t1 = rpf.weight_permutation_trap()
    check("trap #1: weight permutation moves the survivor", t1["weight_permutation_moves_survivor"] is True)
    print(f"     (weight perm: {t1['base_survivor']} -> {t1['permuted_survivor']})")
    t4 = rpf.state_mutation_trap()
    check("trap #4: state mutation moves the survivor", t4["state_mutation_moves_survivor"] is True)
    print(f"     (state mut: {t4['base_survivor']} -> {t4['mutated_survivor']})")


# =====================================================================
# BOUNDARY tests -- thin edges of the field / traversal
# =====================================================================

def boundary_tests() -> None:
    print("\n=== BOUNDARY (thin edges) ===")

    # Boundary: a single inward shell collapses the traversal to its seed step
    # (within-shell mass argmax) -- a genuine degenerate edge. With only one
    # non-empty shell the multi-step invariant fails (this is the structural
    # boundary: the traversal NEEDS >=2 inward shells to carry shell ordering).
    one_shell = {"Sigma_2": ["b0", "b2", "b3"]}
    inst1 = rpf.build_object_instance(future_continuations=one_shell)
    inv1 = rpf.check_invariants(inst1, include_shell_ordering=False)
    check("boundary: single-inward-shell field FAILS multi-step traversal (degenerate edge, expected)",
          inv1["compression_is_multi_step_traversal"] is False)
    check("boundary: single-shell field still yields a derived scalar survivor",
          inst1["present_survivor"] in {"b0", "b2", "b3"})

    # Boundary: a branch identical to the incoming anchor scores 1.0 on the inner
    # shell (anchor persists). Build a config where the anchor reappears on the
    # inner shell; it must survive (self-compat = 1.0 is maximal).
    persist_fc = {"Sigma_2": ["b0", "b4"], "Sigma_1": ["b0", "b5"]}
    inst_p = rpf.build_object_instance(future_continuations=persist_fc)
    cm = inst_p["compression_map"]
    nonempty = [s for s in cm["traversal_steps"] if s["branches_on_shell"]]
    outer_anchor = nonempty[0]["selected_anchor"]
    inner_step = nonempty[1]
    if outer_anchor in inner_step["branches_on_shell"]:
        check("boundary: anchor reappearing on inner shell scores 1.0 (self-compat maximal)",
              abs(inner_step["branch_scores"][outer_anchor] - 1.0) < 1e-12)
        check("boundary: persisting anchor survives the inner shell",
              inner_step["selected_anchor"] == outer_anchor)
    else:
        check("boundary: persist-config outer anchor present on inner shell (setup check)", False)

    # Boundary: deterministic tie-break on the OUTER seed step. Use a symmetric
    # outer pair so within-shell masses tie; the lower id must seed the anchor.
    tie_fc = {"Sigma_2": ["b1", "b2"], "Sigma_1": ["b0", "b3"]}  # b1,b2 symmetric dist 2
    inst_tie = rpf.build_object_instance(future_continuations=tie_fc)
    cm_t = inst_tie["compression_map"]
    seed = [s for s in cm_t["traversal_steps"] if s["branches_on_shell"]][0]
    check("boundary: symmetric outer pair has equal within-shell mass (genuine tie)",
          abs(seed["branch_scores"]["b1"] - seed["branch_scores"]["b2"]) < 1e-12)
    check("boundary: deterministic seed tie-break picks lowest branch id (b1)",
          seed["selected_anchor"] == "b1")

    # Boundary: present_survivor must never be a list/count even at minimal field
    check("boundary: present_survivor is scalar id at minimal multi-shell field",
          isinstance(inst_tie["present_survivor"], str))


def main() -> int:
    positive_tests()
    negative_tests()
    trap_tests()
    boundary_tests()
    print("\n=== SUMMARY ===")
    if FAILURES:
        print(json.dumps({"green": False, "failures": FAILURES}, indent=2))
        return 1
    print(json.dumps({"green": True, "failures": []}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
