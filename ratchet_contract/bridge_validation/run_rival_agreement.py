#!/usr/bin/env python3
"""
run_rival_agreement.py -- runs BOTH bridge_word_bfs.py (forward
breadth-first word enumeration) and bridge_action_predictive.py (bounded
backward color-refinement recursion) over the toy candidates/decks
gathered by controls.py's C9 (the C1-C8 cases) plus
ClassicalRelationalExecCandidate (fuel_sims/candidate_classical_exec.py,
pure Python -- does NOT import candidate_spinor_qit_exec.py, whose memory
gate must not trip), and writes
ratchet_contract/bridge_validation/results/rival_agreement.json.

This is a REAL cross-check, not a restatement: bridge_word_bfs.py and
bridge_action_predictive.py derive the SAME target relation
(bridge_interface.py's predictive quotient) via structurally different
paths -- forward word enumeration vs backward recursive signatures --
so agreement across every case is genuine corroboration, and any
disagreement is a real finding, recorded explicitly rather than smoothed
over by picking one bridge's answer.

SCOPE (binding, matches bridge_validation/README.md's own ceiling):
practice/fuel development only. promotion_allowed=false;
formal_admission_allowed=false. Does NOT ratchet the axioms, does NOT
admit any real carrier.

Exit codes: 0 iff every case's rival-agreement check ran to completion and
the JSON was written (divergences, if any, are recorded in the JSON's
`divergences` list rather than causing a failure exit -- a disagreement
between two independently-derived bridges is itself the finding this
script exists to surface, never silently resolved). 1 iff the run itself
could not complete (an exception while building/running a case).
"""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
RESULTS_DIR = THIS_DIR / "results"
RESULTS_PATH = RESULTS_DIR / "rival_agreement.json"

_RATCHET_CONTRACT_DIR = THIS_DIR.parent
_FUEL_SIMS_DIR = _RATCHET_CONTRACT_DIR / "fuel_sims"
for _p in (THIS_DIR, _RATCHET_CONTRACT_DIR, _FUEL_SIMS_DIR):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from bridge_interface import history_point, hp_json  # noqa: E402
from bridge_action_predictive import induce_action_predictive_partition  # noqa: E402
from bridge_word_bfs import induce_word_bfs_partition  # noqa: E402

from controls import (  # noqa: E402
    C1_IntCounterCandidate,
    C1_StringCounterCandidate,
    C2_HonestBookkeeping,
    C3_LastWriteWinsRegister,
    C4_AmnesiacUnderDelay,
    C5_FrozenUnderExtension,
    C6_DeadEndAtRenest,
    C7_ThinDeckCandidate,
    C8_NeighborAwareCandidate,
    C8_NeighborBlindCandidate,
)

# Pure Python; deliberately NOT importing candidate_spinor_qit_exec (its
# memory gate must not trip -- see task scope).
from candidate_classical_exec import ClassicalRelationalExecCandidate, ROOTS  # noqa: E402


def _build_cases() -> list[dict]:
    """One row per (candidate, X, horizon, action_alphabet) combination
    drawn directly from controls.py's C1-C8 (the exact toy cases C9
    aggregates bridge_agreement notes from), plus one row for
    ClassicalRelationalExecCandidate over its 4 declared roots."""
    cases: list[dict] = []

    # -- C1: two internally-different implementations, identical behaviour --
    x1 = tuple(
        history_point("r0", p)
        for p in [(), ("perturb",), ("perturb", "perturb"), ("perturb", "perturb", "perturb"), ("read_outcome",)]
    )
    cases.append({"case": "C1_int_counter", "candidate": C1_IntCounterCandidate(), "X": x1, "horizon": 2, "alphabet": None})
    cases.append({"case": "C1_string_counter", "candidate": C1_StringCounterCandidate(), "X": x1, "horizon": 2, "alphabet": None})

    # -- C2: raw-label relabeling honesty (honest-bookkeeping deck) --
    cand2 = C2_HonestBookkeeping({"tokA": "up", "tokB": "down"})
    x2 = (history_point("r0", ("tokA",)), history_point("r0", ("tokB",)))
    cases.append({"case": "C2_honest_bookkeeping", "candidate": cand2, "X": x2, "horizon": 1,
                  "alphabet": ("tokA", "tokB", "read_outcome")})

    # -- C3: two histories distinguishable only by ORDER --
    cand3 = C3_LastWriteWinsRegister()
    x3 = (
        history_point("r0", (("ordered_compose", ("write_a", "write_b")),)),
        history_point("r0", (("ordered_compose", ("write_b", "write_a")),)),
    )
    cases.append({"case": "C3_last_write_wins_register", "candidate": cand3, "X": x3, "horizon": 1, "alphabet": None})

    # -- C4: persistence under delay (pre/post) --
    cand4 = C4_AmnesiacUnderDelay()
    alpha4 = ("write_a", "write_b", "delay", "read_outcome")
    x4_pre = (history_point("r0", ("write_a",)), history_point("r0", ("write_b",)))
    x4_post = (history_point("r0", ("write_a", "delay")), history_point("r0", ("write_b", "delay")))
    cases.append({"case": "C4_amnesiac_pre_delay", "candidate": cand4, "X": x4_pre, "horizon": 1, "alphabet": alpha4})
    cases.append({"case": "C4_amnesiac_post_delay", "candidate": cand4, "X": x4_post, "horizon": 1, "alphabet": alpha4})

    # -- C5: evolvability under extend_under_constraint (pre/post) --
    cand5 = C5_FrozenUnderExtension()
    ext5 = ("extend_under_constraint", "any_rule")
    alpha5 = ("write_a", "write_b", ext5, "read_outcome")
    x5_pre = (history_point("r0", ("write_a",)), history_point("r0", ("write_b",)))
    x5_post = (history_point("r0", ("write_a", ext5)), history_point("r0", ("write_b", ext5)))
    cases.append({"case": "C5_frozen_pre_extend", "candidate": cand5, "X": x5_pre, "horizon": 1, "alphabet": alpha5})
    cases.append({"case": "C5_frozen_post_extend", "candidate": cand5, "X": x5_post, "horizon": 1, "alphabet": alpha5})

    # -- C6: dead end at renest (pre/post) --
    cand6 = C6_DeadEndAtRenest()
    alpha6 = ("write_a", "write_b", "renest", "read_outcome")
    x6_pre = (history_point("r0", ("write_a",)), history_point("r0", ("write_b",)))
    x6_post = (history_point("r0", ("write_a", "renest")), history_point("r0", ("write_b", "renest")))
    cases.append({"case": "C6_dead_end_pre_renest", "candidate": cand6, "X": x6_pre, "horizon": 1, "alphabet": alpha6})
    cases.append({"case": "C6_dead_end_post_renest", "candidate": cand6, "X": x6_post, "horizon": 1, "alphabet": alpha6})

    # -- C7: deliberately THIN action deck (thin vs rich) --
    cand7 = C7_ThinDeckCandidate()
    x7 = (history_point("r_left", ()), history_point("r_right", ()))
    thin7 = ("probe_thin", "read_outcome")
    rich7 = ("probe_thin", "probe_rich", "read_outcome")
    cases.append({"case": "C7_thin_deck", "candidate": cand7, "X": x7, "horizon": 1, "alphabet": thin7})
    cases.append({"case": "C7_rich_deck", "candidate": cand7, "X": x7, "horizon": 1, "alphabet": rich7})

    # -- C8: deliberately CARRIER-BIASED deck (full vs ablated, both candidates) --
    alpha8 = C8_NeighborAwareCandidate()
    beta8 = C8_NeighborBlindCandidate()
    x8 = (history_point("r_left", ()), history_point("r_right", ()))
    full8 = ("baseline_probe", "couple_neighbor_neighbor", "read_outcome")
    ablated8 = ("baseline_probe", "read_outcome")
    cases.append({"case": "C8_neighbor_aware_full", "candidate": alpha8, "X": x8, "horizon": 1, "alphabet": full8})
    cases.append({"case": "C8_neighbor_aware_ablated", "candidate": alpha8, "X": x8, "horizon": 1, "alphabet": ablated8})
    cases.append({"case": "C8_neighbor_blind_full", "candidate": beta8, "X": x8, "horizon": 1, "alphabet": full8})
    cases.append({"case": "C8_neighbor_blind_ablated", "candidate": beta8, "X": x8, "horizon": 1, "alphabet": ablated8})

    # -- ClassicalRelationalExecCandidate: 18-action deck over its 4 declared
    # roots. horizon=1 matches fuel_sims/practice_run.py's own PRACTICE_HORIZON
    # convention for this exact candidate/deck (tractable; single-action
    # read_outcome_z already separates every root pair at this horizon).
    cand_classical = ClassicalRelationalExecCandidate()
    x_classical = tuple(history_point(root, ()) for root in ROOTS)
    cases.append({"case": "classical_relational_exec", "candidate": cand_classical, "X": x_classical,
                  "horizon": 1, "alphabet": None})

    return cases


def run_rival_agreement() -> dict:
    cases_out = []
    divergences = []

    for spec in _build_cases():
        candidate = spec["candidate"]
        X = spec["X"]
        horizon = spec["horizon"]
        alphabet = spec["alphabet"]

        pi_ap = induce_action_predictive_partition(candidate, X, horizon=horizon, action_alphabet=alphabet)
        pi_bfs = induce_word_bfs_partition(candidate, X, horizon=horizon, action_alphabet=alphabet)
        agree = pi_ap == pi_bfs

        effective_alphabet = tuple(alphabet) if alphabet is not None else tuple(candidate.action_alphabet())

        row = {
            "case": spec["case"],
            "candidate": candidate.name,
            "X": [hp_json(x) for x in X],
            "horizon": horizon,
            "action_alphabet": [repr(a) for a in effective_alphabet],
            "pi_action_predictive": list(pi_ap),
            "pi_word_bfs": list(pi_bfs),
            "agree": agree,
        }
        cases_out.append(row)
        if not agree:
            divergences.append({
                "case": spec["case"],
                "candidate": candidate.name,
                "pi_action_predictive": list(pi_ap),
                "pi_word_bfs": list(pi_bfs),
            })

    all_agree = all(row["agree"] for row in cases_out) if cases_out else False

    return {
        "schema_version": "rival-agreement/0.1",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "purpose": (
            "cross-check induce_word_bfs_partition (bridge_word_bfs.py, forward breadth-first "
            "word enumeration + union-find) against induce_action_predictive_partition "
            "(bridge_action_predictive.py, bounded backward color-refinement recursion) over "
            "controls.py's C1-C8 toy cases (the same cases C9 aggregates) plus "
            "ClassicalRelationalExecCandidate"
        ),
        "scope": (
            "practice/fuel development only -- promotion_allowed=false, "
            "formal_admission_allowed=false; does NOT ratchet the axioms, does NOT admit any "
            "real carrier (see bridge_validation/README.md)"
        ),
        "cases_checked": len(cases_out),
        "all_agree": all_agree,
        "cases": cases_out,
        "divergences": divergences,
        "rule": (
            "bridge_word_bfs.py and bridge_action_predictive.py must induce the SAME partition "
            "on every case, since both decide bridge_interface.py's predictive quotient -- but "
            "via structurally independent derivation paths (forward word enumeration vs backward "
            "recursive signatures), so agreement is a REAL cross-check, not a restatement. Any "
            "disagreement is a genuine finding, recorded in `divergences` rather than silently "
            "resolved by picking one bridge's answer."
        ),
    }


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        result = run_rival_agreement()
    except Exception:
        RESULTS_PATH.write_text(
            json.dumps({
                "schema_version": "rival-agreement/0.1",
                "classification": "tool_lego_fit_probe",
                "promotion_allowed": False,
                "error": "run_rival_agreement raised",
                "traceback": traceback.format_exc(),
            }, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"exit_code": 1, "error": "run_rival_agreement raised -- see results/rival_agreement.json"}))
        return 1

    RESULTS_PATH.write_text(json.dumps(result, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "cases_checked": result["cases_checked"],
        "all_agree": result["all_agree"],
        "divergences_count": len(result["divergences"]),
        "results_path": str(RESULTS_PATH),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
