#!/usr/bin/env python3
"""
controls.py -- the 9 SYNTHETIC CONTROLS for BRIDGE_VALIDATION.

Each control is a small candidate/deck built to isolate exactly ONE bridge
property (matching toy_candidates.py's single-axis-isolation discipline).
Each MUST fire its expected verdict -- self-verifying, like
run_contract_selfcheck.py's discrimination matrix. Where a control does not
fire as expected, run_bridge_validation.py reports that as a real finding
rather than forcing it.

  C1  two internally-different implementations, identical behaviour -> MERGE
  C2  raw-label relabeling that changes a semantic outcome -> FAIL identity-
      honesty; the SAME check on honest bookkeeping -> PASS (the contrast
      that proves the check catches illicit identity, not raw-label usage
      per se)
  C3  two histories distinguishable only by ORDER -> SEPARATE
  C4  a candidate that loses its record under delay -> FAIL persistence
  C5  a frozen candidate (extend_under_constraint always rejected) -> FAIL
      evolvability
  C6  a candidate that works locally but cannot complete renest -> DEAD_END
  C7  a deliberately THIN action deck -> HOLD, never a false tie
  C8  a deliberately CARRIER-BIASED deck -> DETECTED via ablation
  C9  action-predictive and SMT-relational bridges AGREE on every exact toy
      case gathered from C1-C8; any disagreement -> HOLD

IMPORTANT METHODOLOGICAL NOTE (found while designing C2, kept here because
it governs several controls' design): checking whether two bridge-INDUCED
PARTITIONS match is the WRONG tool for relabeling-honesty. Partition
coarseness/equality is invariant under ANY bijective relabeling of block
content by construction -- that is the entire point of a quotient -- so a
candidate that applies a CONSISTENT global relabeling bug (for example,
swapping every "pos" outcome for "neg" under a renamed action deck) can
still induce a partition with the identical GROUPING structure, silently
passing a partition-only check. The controls below that test relabeling/
encoding honesty (C2, and bridge_self_tests.py's hidden-lookup-table self-
test) therefore compare raw OUTCOME CONTENT against the FIXED, un-relabeled
Outcome vocabulary -- never partition digests -- for the property that
actually matters. Controls that ask whether two DIFFERENT HISTORIES are
told apart (C3, C4, C5, C7, C8) correctly use partition/grouping
comparisons, since that is what they are actually claiming about.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from contract import ControlCase  # noqa: E402 -- reused, not reimplemented

from bridge_interface import (  # noqa: E402
    BridgeCheckResult,
    CandidateBridgeInterface,
    MANIFOLD_ACTION_CATEGORIES,
    Outcome,
    history_point,
    hp_json,
    step_outcome,
)
from bridge_action_predictive import induce_action_predictive_partition, separating_witness  # noqa: E402
from bridge_smt_relational import induce_smt_relational_partition  # noqa: E402


def _bridge_agreement_note(pi_ap: tuple, smt_result) -> dict:
    """Supplementary cross-check attached to (almost) every control's
    reasons dict -- material for C9's aggregate concordance check, not
    itself the thing that decides most controls' own fired_as_expected."""
    return {
        "agree": pi_ap == smt_result.partition,
        "pi_action_predictive": list(pi_ap),
        "pi_smt_relational": list(smt_result.partition),
        "smt_internal_solver_agreement": smt_result.all_agree,
        "smt_disagreement_count": len(smt_result.disagreements),
    }


# ===========================================================================
# C1 -- two internally-different implementations, identical behaviour -> MERGE
# ===========================================================================
class C1_IntCounterCandidate(CandidateBridgeInterface):
    """Opaque state = a plain int counter. Internal representation: int.
    Two harmless constant-outcome actions (bracket_compose_probe,
    couple_inner_outer_probe) are included purely for MANIFOLD_ACTION_
    CATEGORIES coverage -- not load-bearing for this control's own verdict,
    identical on both C1 variants below."""

    name = "C1_int_counter"

    def action_alphabet(self):
        return ("perturb", "read_outcome", "bracket_compose_probe", "couple_inner_outer_probe")

    def action_category(self, action):
        return {
            "perturb": "perturb", "read_outcome": "read_outcome",
            "bracket_compose_probe": "bracket_compose", "couple_inner_outer_probe": "couple_inner_outer",
        }[action]

    def initial_state(self, root):
        return 0

    def step_C(self, state, action, nest_context=None):
        if action == "perturb":
            return state + 1, Outcome.deterministic("ack")
        if action == "read_outcome":
            parity = "even" if state % 2 == 0 else "odd"
            return state, Outcome.deterministic(parity)
        if action in ("bracket_compose_probe", "couple_inner_outer_probe"):
            return state, Outcome.deterministic("ack")
        raise ValueError(f"unknown action {action!r}")


class C1_StringCounterCandidate(CandidateBridgeInterface):
    """Opaque state = a string encoding of the SAME counter ('n3', ...).
    Different internal representation (str, not int); IDENTICAL externally
    observable behaviour to C1_IntCounterCandidate. This is what 'two
    internally-different implementations' means under an opaque-state
    contract: the representation difference is invisible to the bridge by
    construction; the point is confirming the bridge reports MERGE for a
    genuine behavioural tie, not FAIL."""

    name = "C1_string_counter"

    def action_alphabet(self):
        return ("perturb", "read_outcome", "bracket_compose_probe", "couple_inner_outer_probe")

    def action_category(self, action):
        return {
            "perturb": "perturb", "read_outcome": "read_outcome",
            "bracket_compose_probe": "bracket_compose", "couple_inner_outer_probe": "couple_inner_outer",
        }[action]

    def initial_state(self, root):
        return "n0"

    def step_C(self, state, action, nest_context=None):
        n = int(state[1:])
        if action == "perturb":
            return f"n{n + 1}", Outcome.deterministic("ack")
        if action == "read_outcome":
            parity = "even" if n % 2 == 0 else "odd"
            return state, Outcome.deterministic(parity)
        if action in ("bracket_compose_probe", "couple_inner_outer_probe"):
            return state, Outcome.deterministic("ack")
        raise ValueError(f"unknown action {action!r}")


def run_C1() -> BridgeCheckResult:
    a = C1_IntCounterCandidate()
    b = C1_StringCounterCandidate()
    horizon = 2
    X = tuple(
        history_point("r0", p)
        for p in [(), ("perturb",), ("perturb", "perturb"), ("perturb", "perturb", "perturb"), ("read_outcome",)]
    )
    pi_a_ap = induce_action_predictive_partition(a, X, horizon=horizon)
    pi_b_ap = induce_action_predictive_partition(b, X, horizon=horizon)
    smt_a = induce_smt_relational_partition(a, X, horizon=horizon)
    smt_b = induce_smt_relational_partition(b, X, horizon=horizon)

    ap_merge = pi_a_ap == pi_b_ap
    smt_merge = smt_a.partition == smt_b.partition
    fired = ap_merge and smt_merge

    note_a = _bridge_agreement_note(pi_a_ap, smt_a)
    note_b = _bridge_agreement_note(pi_b_ap, smt_b)

    return BridgeCheckResult(
        check="C1", label=("MERGE" if fired else "NO_MERGE"), expected_label="MERGE",
        fired_as_expected=fired,
        reasons={
            "candidates": [a.name, b.name], "X": [hp_json(x) for x in X], "horizon": horizon,
            "pi_action_predictive_A": list(pi_a_ap), "pi_action_predictive_B": list(pi_b_ap),
            "pi_smt_relational_A": list(smt_a.partition), "pi_smt_relational_B": list(smt_b.partition),
            "action_predictive_merge": ap_merge, "smt_relational_merge": smt_merge,
            "bridge_agreement": {"A": note_a, "B": note_b, "agree": note_a["agree"] and note_b["agree"]},
        },
    )


# ===========================================================================
# C2 -- raw-label relabeling that changes a semantic outcome -> FAIL
# identity-honesty; the SAME check on honest bookkeeping -> PASS.
# ===========================================================================
class C2_HonestBookkeeping(CandidateBridgeInterface):
    """Raw-label dict lookup used ONLY as bookkeeping: `_semantic` maps
    each action token to its MEANING ('up'/'down'), and behaviour is driven
    by the meaning, never by the raw token spelling. Rebuilding this
    candidate with a relabeled token->meaning dict (same meanings, new
    token spellings) reproduces byte-identical behaviour under the
    correspondingly relabeled deck -- honest bookkeeping, not illicit
    identity."""

    def __init__(self, semantic_map: dict, name: str = "C2_honest_bookkeeping"):
        self._semantic = dict(semantic_map)
        self.name = name

    def action_alphabet(self):
        return tuple(self._semantic.keys()) + ("read_outcome",)

    def action_category(self, action):
        return "perturb" if action in self._semantic else "read_outcome"

    def initial_state(self, root):
        return 0

    def step_C(self, state, action, nest_context=None):
        if action == "read_outcome":
            sign = "pos" if state > 0 else ("neg" if state < 0 else "zero")
            return state, Outcome.deterministic(sign)
        meaning = self._semantic[action]  # raw-label dict lookup -- BOOKKEEPING
        delta = 1 if meaning == "up" else -1
        return state + delta, Outcome.deterministic("ack")


class C2_IllicitRawLabel(CandidateBridgeInterface):
    """Behaviour is driven by which of the candidate's two tokens sorts
    FIRST (a raw-label property of the token STRINGS themselves), not by
    any declared up/down meaning. Relabeling the same two semantic slots to
    token strings that sort in a different relative order flips behaviour:
    illicit identity, not bookkeeping."""

    def __init__(self, tokens: tuple, name: str = "C2_illicit_raw_label"):
        self._tokens = tuple(tokens)  # (up_slot_token, down_slot_token)
        self.name = name

    def action_alphabet(self):
        return self._tokens + ("read_outcome",)

    def action_category(self, action):
        return "perturb" if action in self._tokens else "read_outcome"

    def initial_state(self, root):
        return 0

    def step_C(self, state, action, nest_context=None):
        if action == "read_outcome":
            sign = "pos" if state > 0 else ("neg" if state < 0 else "zero")
            return state, Outcome.deterministic(sign)
        first, _second = sorted(self._tokens)  # ILLICIT: raw sort order, not declared meaning
        delta = 1 if action == first else -1
        return state + delta, Outcome.deterministic("ack")


def _relabeling_probe(build_candidate, tokens: tuple, shapes: Sequence[tuple]) -> dict:
    """build_candidate(tokens) -> a fresh candidate using tokens=(up,down)
    as its two perturb-slot tokens. For each shape (a tuple of 'up'/'down'
    meta-symbols), realize it against `tokens`, replay from a fresh
    instance, apply one more 'read_outcome', and record the resulting
    Outcome repr keyed by the SHAPE (not the realized prefix) so runs under
    different token spellings are directly comparable row-for-row."""
    candidate = build_candidate(tokens)
    up, down = tokens
    memo: dict = {}
    out = {}
    for shape in shapes:
        prefix = tuple(up if s == "up" else down for s in shape)
        out[shape] = repr(step_outcome(candidate, "r0", prefix, "read_outcome", memo=memo))
    return out


def _relabeling_check(build_candidate, base_tokens: tuple, relabeled_tokens: tuple) -> dict:
    shapes = ((), ("up",), ("down",), ("up", "up"), ("down", "down"), ("up", "down"), ("down", "up"))
    probe_base = _relabeling_probe(build_candidate, base_tokens, shapes)
    probe_relabeled = _relabeling_probe(build_candidate, relabeled_tokens, shapes)
    invariant = probe_base == probe_relabeled
    mismatches = [
        {"shape": list(s), "base_outcome": probe_base[s], "relabeled_outcome": probe_relabeled[s]}
        for s in shapes if probe_base[s] != probe_relabeled[s]
    ]
    return {
        "base_tokens": list(base_tokens), "relabeled_tokens": list(relabeled_tokens),
        "probe_base": {repr(k): v for k, v in probe_base.items()},
        "probe_relabeled": {repr(k): v for k, v in probe_relabeled.items()},
        "relabeling_invariant": invariant, "mismatches": mismatches,
    }


def run_C2() -> BridgeCheckResult:
    honest = _relabeling_check(
        lambda toks: C2_HonestBookkeeping({toks[0]: "up", toks[1]: "down"}),
        ("tokA", "tokB"), ("zzz", "yyy"),
    )
    illicit = _relabeling_check(
        lambda toks: C2_IllicitRawLabel(toks),
        ("tokA", "tokB"), ("zzz_up", "aaa_down"),
    )
    honest_pass = honest["relabeling_invariant"] is True
    illicit_fail = illicit["relabeling_invariant"] is False
    fired = honest_pass and illicit_fail

    cand = C2_HonestBookkeeping({"tokA": "up", "tokB": "down"})
    X = (history_point("r0", ("tokA",)), history_point("r0", ("tokB",)))
    alphabet = ("tokA", "tokB", "read_outcome")
    pi_ap = induce_action_predictive_partition(cand, X, horizon=1, action_alphabet=alphabet)
    smt_res = induce_smt_relational_partition(cand, X, horizon=1, action_alphabet=alphabet)

    return BridgeCheckResult(
        check="C2",
        label=f"honest_relabeling_invariant={honest_pass};illicit_relabeling_invariant={not illicit_fail}",
        expected_label="honest_relabeling_invariant=True;illicit_relabeling_invariant=False",
        fired_as_expected=fired,
        reasons={
            "honest_bookkeeping_case": honest, "illicit_raw_label_case": illicit,
            "bridge_agreement": _bridge_agreement_note(pi_ap, smt_res),
        },
    )


# ===========================================================================
# C3 -- two histories distinguishable only by ORDER -> SEPARATE
# ===========================================================================
class C3_LastWriteWinsRegister(CandidateBridgeInterface):
    """Opaque state = the current register value. `ordered_compose`
    actions carry an explicit ORDERED pair of writes and apply them via
    last-write-wins semantics -- order is load-bearing. `read_outcome`
    reports the current value."""

    name = "C3_last_write_wins_register"

    def action_alphabet(self):
        return (
            ("ordered_compose", ("write_a", "write_b")),
            ("ordered_compose", ("write_b", "write_a")),
            "read_outcome",
        )

    def action_category(self, action):
        return "read_outcome" if action == "read_outcome" else "ordered_compose"

    def initial_state(self, root):
        return "empty"

    def step_C(self, state, action, nest_context=None):
        if action == "read_outcome":
            return state, Outcome.deterministic(state)
        _kind, order = action
        value = state
        for write in order:
            value = "a" if write == "write_a" else "b"
        return value, Outcome.deterministic("composed")


def run_C3() -> BridgeCheckResult:
    candidate = C3_LastWriteWinsRegister()
    horizon = 1
    x = history_point("r0", (("ordered_compose", ("write_a", "write_b")),))
    y = history_point("r0", (("ordered_compose", ("write_b", "write_a")),))
    X = (x, y)

    pi_ap = induce_action_predictive_partition(candidate, X, horizon=horizon)
    smt_res = induce_smt_relational_partition(candidate, X, horizon=horizon)
    witness = separating_witness(candidate, x, y, horizon=horizon)

    separate_ap = pi_ap[0] != pi_ap[1]
    separate_smt = smt_res.partition[0] != smt_res.partition[1]
    fired = separate_ap and separate_smt and witness is not None

    return BridgeCheckResult(
        check="C3", label=("SEPARATE" if fired else "NOT_SEPARATE"), expected_label="SEPARATE",
        fired_as_expected=fired,
        reasons={
            "candidate": candidate.name, "x": hp_json(x), "y": hp_json(y), "horizon": horizon,
            "pi_action_predictive": list(pi_ap), "pi_smt_relational": list(smt_res.partition),
            "separating_witness": [repr(a) for a in witness] if witness else None,
            "bridge_agreement": _bridge_agreement_note(pi_ap, smt_res),
        },
    )


# ===========================================================================
# C4 -- a candidate that loses its record under delay -> FAIL persistence
# ===========================================================================
class C4_AmnesiacUnderDelay(CandidateBridgeInterface):
    """`write_a`/`write_b` set value. `delay` (category
    delay_retain_history) sets a marker that WIPES value to a constant
    'forgotten' token on every subsequent read. `read_outcome` reports the
    current value, or 'forgotten' once a delay has been seen."""

    name = "C4_amnesiac_under_delay"

    def action_alphabet(self):
        return ("write_a", "write_b", "delay", "read_outcome")

    def action_category(self, action):
        return {
            "write_a": "prepare_restrict", "write_b": "prepare_restrict",
            "delay": "delay_retain_history", "read_outcome": "read_outcome",
        }[action]

    def initial_state(self, root):
        return ("empty", False)

    def step_C(self, state, action, nest_context=None):
        value, forgotten = state
        if action == "write_a":
            return ("a", forgotten), Outcome.deterministic("ack")
        if action == "write_b":
            return ("b", forgotten), Outcome.deterministic("ack")
        if action == "delay":
            return (value, True), Outcome.deterministic("ack")
        reported = "forgotten" if forgotten else value
        return state, Outcome.deterministic(reported)


def run_C4() -> BridgeCheckResult:
    candidate = C4_AmnesiacUnderDelay()
    horizon = 1
    alphabet = ("write_a", "write_b", "delay", "read_outcome")

    X_pre = (history_point("r0", ("write_a",)), history_point("r0", ("write_b",)))
    pi_pre_ap = induce_action_predictive_partition(candidate, X_pre, horizon=horizon, action_alphabet=alphabet)
    separate_pre = pi_pre_ap[0] != pi_pre_ap[1]

    X_post = (history_point("r0", ("write_a", "delay")), history_point("r0", ("write_b", "delay")))
    pi_post_ap = induce_action_predictive_partition(candidate, X_post, horizon=horizon, action_alphabet=alphabet)
    smt_post = induce_smt_relational_partition(candidate, X_post, horizon=horizon, action_alphabet=alphabet)
    collapse_post_ap = pi_post_ap[0] == pi_post_ap[1]
    collapse_post_smt = smt_post.partition[0] == smt_post.partition[1]

    fired = separate_pre and collapse_post_ap and collapse_post_smt

    return BridgeCheckResult(
        check="C4", label=("FAIL_PERSISTENCE" if fired else "PERSISTS"), expected_label="FAIL_PERSISTENCE",
        fired_as_expected=fired,
        reasons={
            "candidate": candidate.name, "horizon": horizon,
            "pre_delay_separate_action_predictive": separate_pre,
            "post_delay_collapse_action_predictive": collapse_post_ap,
            "post_delay_collapse_smt_relational": collapse_post_smt,
            "pi_pre": list(pi_pre_ap), "pi_post_action_predictive": list(pi_post_ap),
            "pi_post_smt_relational": list(smt_post.partition),
            "bridge_agreement": _bridge_agreement_note(pi_post_ap, smt_post),
        },
    )


# ===========================================================================
# C5 -- a frozen candidate (extend_under_constraint always rejected) ->
# FAIL evolvability
# ===========================================================================
class C5_FrozenUnderExtension(CandidateBridgeInterface):
    """Like C4's register, but adds `extend_under_constraint`: uniformly
    REJECTS every constraint and, once attempted, collapses all future
    reads to a constant 'frozen' token -- evolve()->None from the original
    contract, translated into the corrected step_C interface: no
    admissible extension, and the attempt is visible/inspectable, never
    silently ignored."""

    name = "C5_frozen_under_extension"

    def action_alphabet(self):
        return ("write_a", "write_b", ("extend_under_constraint", "any_rule"), "read_outcome")

    def action_category(self, action):
        if action == "read_outcome":
            return "read_outcome"
        if isinstance(action, tuple) and action[0] == "extend_under_constraint":
            return "extend_under_constraint"
        return "prepare_restrict"

    def initial_state(self, root):
        return ("empty", False)

    def step_C(self, state, action, nest_context=None):
        value, frozen = state
        if action == "write_a":
            return ("a", frozen), Outcome.deterministic("ack")
        if action == "write_b":
            return ("b", frozen), Outcome.deterministic("ack")
        if isinstance(action, tuple) and action[0] == "extend_under_constraint":
            return (value, True), Outcome.deterministic("rejected")
        reported = "frozen" if frozen else value
        return state, Outcome.deterministic(reported)


def run_C5() -> BridgeCheckResult:
    candidate = C5_FrozenUnderExtension()
    horizon = 1
    ext = ("extend_under_constraint", "any_rule")
    alphabet = ("write_a", "write_b", ext, "read_outcome")

    X_pre = (history_point("r0", ("write_a",)), history_point("r0", ("write_b",)))
    pi_pre_ap = induce_action_predictive_partition(candidate, X_pre, horizon=horizon, action_alphabet=alphabet)
    separate_pre = pi_pre_ap[0] != pi_pre_ap[1]

    X_post = (history_point("r0", ("write_a", ext)), history_point("r0", ("write_b", ext)))
    pi_post_ap = induce_action_predictive_partition(candidate, X_post, horizon=horizon, action_alphabet=alphabet)
    smt_post = induce_smt_relational_partition(candidate, X_post, horizon=horizon, action_alphabet=alphabet)
    collapse_post = pi_post_ap[0] == pi_post_ap[1]

    memo: dict = {}
    rejections = {
        "write_a_branch": repr(step_outcome(candidate, "r0", ("write_a",), ext, memo=memo)),
        "write_b_branch": repr(step_outcome(candidate, "r0", ("write_b",), ext, memo=memo)),
    }
    both_rejected = all(v == repr(Outcome.deterministic("rejected")) for v in rejections.values())

    fired = separate_pre and collapse_post and both_rejected

    return BridgeCheckResult(
        check="C5", label=("FAIL_EVOLVABILITY" if fired else "EVOLVES"), expected_label="FAIL_EVOLVABILITY",
        fired_as_expected=fired,
        reasons={
            "candidate": candidate.name, "horizon": horizon,
            "pre_extend_separate": separate_pre, "post_extend_collapse": collapse_post,
            "both_branches_rejected": both_rejected, "rejection_outcomes": rejections,
            "pi_pre": list(pi_pre_ap), "pi_post_action_predictive": list(pi_post_ap),
            "pi_post_smt_relational": list(smt_post.partition),
            "bridge_agreement": _bridge_agreement_note(pi_post_ap, smt_post),
        },
    )


# ===========================================================================
# C6 -- a candidate that works locally but cannot complete renest ->
# DEAD_END / Purgatory
# ===========================================================================
class C6_DeadEndAtRenest(CandidateBridgeInterface):
    """Works locally (write/read distinguish fine) but `renest` is an
    ABSORBING dead end: once taken, EVERY further action (including
    read_outcome) reports the constant sentinel 'DEAD_END', regardless of
    prior history -- a genuine dead end, not silently equivalent to a
    still-live outcome."""

    name = "C6_dead_end_at_renest"

    def action_alphabet(self):
        return ("write_a", "write_b", "renest", "read_outcome")

    def action_category(self, action):
        return {
            "write_a": "prepare_restrict", "write_b": "prepare_restrict",
            "renest": "renest", "read_outcome": "read_outcome",
        }[action]

    def initial_state(self, root):
        return ("empty", False)

    def step_C(self, state, action, nest_context=None):
        value, dead = state
        if dead:
            return state, Outcome.deterministic("DEAD_END")
        if action == "write_a":
            return ("a", False), Outcome.deterministic("ack")
        if action == "write_b":
            return ("b", False), Outcome.deterministic("ack")
        if action == "renest":
            return (value, True), Outcome.deterministic("DEAD_END")
        return state, Outcome.deterministic(value)


def run_C6() -> BridgeCheckResult:
    candidate = C6_DeadEndAtRenest()
    horizon = 1
    alphabet = ("write_a", "write_b", "renest", "read_outcome")

    X_pre = (history_point("r0", ("write_a",)), history_point("r0", ("write_b",)))
    pi_pre_ap = induce_action_predictive_partition(candidate, X_pre, horizon=horizon, action_alphabet=alphabet)
    separate_pre = pi_pre_ap[0] != pi_pre_ap[1]

    X_post = (history_point("r0", ("write_a", "renest")), history_point("r0", ("write_b", "renest")))
    pi_post_ap = induce_action_predictive_partition(candidate, X_post, horizon=horizon, action_alphabet=alphabet)
    smt_post = induce_smt_relational_partition(candidate, X_post, horizon=horizon, action_alphabet=alphabet)
    collapse_post = pi_post_ap[0] == pi_post_ap[1]

    memo: dict = {}
    sink_outcomes = {
        a: repr(step_outcome(candidate, "r0", ("write_a", "renest"), a, memo=memo)) for a in alphabet
    }
    is_sink = all(v == repr(Outcome.deterministic("DEAD_END")) for v in sink_outcomes.values())

    fired = separate_pre and collapse_post and is_sink
    label = "DEAD_END" if (collapse_post and is_sink) else ("SEPARATE" if not collapse_post else "AMBIGUOUS")

    return BridgeCheckResult(
        check="C6", label=label, expected_label="DEAD_END",
        fired_as_expected=fired,
        reasons={
            "candidate": candidate.name, "horizon": horizon,
            "pre_renest_separate": separate_pre, "post_renest_collapse": collapse_post,
            "post_renest_sink_property": is_sink, "sink_outcomes_by_action": sink_outcomes,
            "pi_pre": list(pi_pre_ap), "pi_post_action_predictive": list(pi_post_ap),
            "pi_post_smt_relational": list(smt_post.partition),
            "bridge_agreement": _bridge_agreement_note(pi_post_ap, smt_post),
        },
    )


# ===========================================================================
# C7 -- a deliberately THIN action deck -> HOLD, never a false tie
# ===========================================================================
class C7_ThinDeckCandidate(CandidateBridgeInterface):
    """Two roots (r_left, r_right) are genuinely different -- separable by
    'probe_rich', invisible to a deck restricted to 'probe_thin'/
    'read_outcome' (both report a constant regardless of root)."""

    name = "C7_thin_deck_candidate"

    def action_alphabet(self):
        return ("probe_thin", "probe_rich", "read_outcome")

    def action_category(self, action):
        return "read_outcome"

    def initial_state(self, root):
        return root

    def step_C(self, state, action, nest_context=None):
        if action == "probe_rich":
            return state, Outcome.deterministic(f"rich_signature:{state}")
        return state, Outcome.deterministic("const")


def run_C7() -> BridgeCheckResult:
    candidate = C7_ThinDeckCandidate()
    control = ControlCase(
        label="r_left_vs_r_right_needs_probe_rich",
        state_a=history_point("r_left", ()), state_b=history_point("r_right", ()),
        expected_distinguishable=True,
    )
    X = (control.state_a, control.state_b)
    thin_alphabet = ("probe_thin", "read_outcome")
    rich_alphabet = ("probe_thin", "probe_rich", "read_outcome")
    horizon = 1

    pi_thin_ap = induce_action_predictive_partition(candidate, X, horizon=horizon, action_alphabet=thin_alphabet)
    pi_rich_ap = induce_action_predictive_partition(candidate, X, horizon=horizon, action_alphabet=rich_alphabet)
    smt_thin = induce_smt_relational_partition(candidate, X, horizon=horizon, action_alphabet=thin_alphabet)

    rich_separates = pi_rich_ap[0] != pi_rich_ap[1]
    thin_separates_ap = pi_thin_ap[0] != pi_thin_ap[1]
    thin_separates_smt = smt_thin.partition[0] != smt_thin.partition[1]

    hold = rich_separates and (not thin_separates_ap) and (not thin_separates_smt)
    label = "HOLD_THIN_ACTION_DECK" if hold else ("MERGE" if not rich_separates else "SEPARATE")
    fired = hold

    return BridgeCheckResult(
        check="C7", label=label, expected_label="HOLD_THIN_ACTION_DECK",
        fired_as_expected=fired,
        reasons={
            "candidate": candidate.name, "positive_control": control.label,
            "rich_deck_separates_control": rich_separates,
            "thin_deck_separates_control_action_predictive": thin_separates_ap,
            "thin_deck_separates_control_smt_relational": thin_separates_smt,
            "pi_thin_action_predictive": list(pi_thin_ap), "pi_rich_action_predictive": list(pi_rich_ap),
            "pi_thin_smt_relational": list(smt_thin.partition),
            "rule": ("mirrors gates.py probe_validity_gate: the rich deck must genuinely separate the "
                     "declared positive control (the claim is live) AND the deck under test must fail to "
                     "separate the SAME control -> HOLD_THIN_ACTION_DECK, never MERGE (a false tie)"),
            "bridge_agreement": _bridge_agreement_note(pi_thin_ap, smt_thin),
        },
    )


# ===========================================================================
# C8 -- a deliberately CARRIER-BIASED deck -> DETECTED via ablation
# ===========================================================================
class C8_NeighborAwareCandidate(CandidateBridgeInterface):
    """Meaningfully answers 'couple_neighbor_neighbor' -- its Outcome
    genuinely depends on state (root). On every other action it reports a
    constant."""

    name = "C8_neighbor_aware"

    def action_alphabet(self):
        return ("baseline_probe", "couple_neighbor_neighbor", "read_outcome")

    def action_category(self, action):
        return "couple_neighbor_neighbor" if action == "couple_neighbor_neighbor" else "read_outcome"

    def initial_state(self, root):
        return root

    def step_C(self, state, action, nest_context=None):
        if action == "couple_neighbor_neighbor":
            return state, Outcome.deterministic(f"neighbor_signature:{state}")
        return state, Outcome.deterministic("const")


class C8_NeighborBlindCandidate(CandidateBridgeInterface):
    """Cannot meaningfully answer 'couple_neighbor_neighbor' -- reports the
    SAME refusal token ('NOT_APPLICABLE') regardless of state. Honest
    refusal, not a silent default that could be confused with a genuine
    answer."""

    name = "C8_neighbor_blind"

    def action_alphabet(self):
        return ("baseline_probe", "couple_neighbor_neighbor", "read_outcome")

    def action_category(self, action):
        return "couple_neighbor_neighbor" if action == "couple_neighbor_neighbor" else "read_outcome"

    def initial_state(self, root):
        return root

    def step_C(self, state, action, nest_context=None):
        if action == "couple_neighbor_neighbor":
            return state, Outcome.deterministic("NOT_APPLICABLE")
        return state, Outcome.deterministic("const")


def run_C8() -> BridgeCheckResult:
    alpha = C8_NeighborAwareCandidate()
    beta = C8_NeighborBlindCandidate()
    pair = (history_point("r_left", ()), history_point("r_right", ()))
    full_alphabet = ("baseline_probe", "couple_neighbor_neighbor", "read_outcome")
    ablated_alphabet = ("baseline_probe", "read_outcome")
    horizon = 1

    def separates(candidate, alphabet):
        pi = induce_action_predictive_partition(candidate, pair, horizon=horizon, action_alphabet=alphabet)
        return (pi[0] != pi[1]), pi

    alpha_full, pi_alpha_full = separates(alpha, full_alphabet)
    alpha_ablated, pi_alpha_ablated = separates(alpha, ablated_alphabet)
    beta_full, pi_beta_full = separates(beta, full_alphabet)
    beta_ablated, pi_beta_ablated = separates(beta, ablated_alphabet)

    smt_alpha_full = induce_smt_relational_partition(alpha, pair, horizon=horizon, action_alphabet=full_alphabet)

    bias_detected = alpha_full and (not alpha_ablated) and (not beta_full) and (not beta_ablated)
    label = "DECK_BIAS_DETECTED" if bias_detected else "DECK_BIAS_HELD"
    fired = bias_detected

    return BridgeCheckResult(
        check="C8", label=label, expected_label="DECK_BIAS_DETECTED",
        fired_as_expected=fired,
        reasons={
            "candidates": [alpha.name, beta.name],
            "ablation": {
                "alpha_separates_full_deck": alpha_full, "alpha_separates_ablated_deck": alpha_ablated,
                "beta_separates_full_deck": beta_full, "beta_separates_ablated_deck": beta_ablated,
            },
            "rule": ("design_smt_relational.md section 8 / design_action_predictive_quotient.md section 7.5: "
                     "remove the suspect action family and re-check each candidate's own discrimination power. "
                     "alpha's separation depending ENTIRELY on couple_neighbor_neighbor, while beta cannot use "
                     "it either way, is the mechanical signature of a carrier-biased deck."),
            "pi_alpha_full": list(pi_alpha_full), "pi_alpha_ablated": list(pi_alpha_ablated),
            "pi_beta_full": list(pi_beta_full), "pi_beta_ablated": list(pi_beta_ablated),
            "bridge_agreement": _bridge_agreement_note(pi_alpha_full, smt_alpha_full),
        },
    )


# ===========================================================================
# C9 -- action-predictive and SMT-relational bridges AGREE on every exact
# toy case gathered from C1-C8; any disagreement -> HOLD (semantic
# concordance).
# ===========================================================================
def run_C9(control_results: dict) -> BridgeCheckResult:
    disagreements = []
    checked = []
    for cid, res in control_results.items():
        note = res.reasons.get("bridge_agreement")
        if note is None:
            continue
        checked.append(cid)
        if note.get("agree") is False:
            disagreements.append({"control": cid, "detail": note})

    fired = len(disagreements) == 0 and len(checked) > 0
    label = "AGREE" if fired else "HOLD_SEMANTIC_CONCORDANCE"

    return BridgeCheckResult(
        check="C9", label=label, expected_label="AGREE",
        fired_as_expected=fired,
        reasons={
            "controls_checked": checked, "controls_checked_count": len(checked),
            "disagreements": disagreements,
            "rule": ("action-predictive and SMT-relational bridges must agree on every exact toy case "
                     "gathered from C1-C8; any single disagreement demotes bridge concordance to HOLD, "
                     "never silently resolved by picking one bridge's answer"),
        },
    )


def run_all_controls() -> dict:
    results = {}
    results["C1"] = run_C1()
    results["C2"] = run_C2()
    results["C3"] = run_C3()
    results["C4"] = run_C4()
    results["C5"] = run_C5()
    results["C6"] = run_C6()
    results["C7"] = run_C7()
    results["C8"] = run_C8()
    results["C9"] = run_C9(results)
    return results


# ---------------------------------------------------------------------------
# Action-category coverage report -- honest accounting of which of the 10
# MANIFOLD_ACTION_CATEGORIES the campaign's own decks actually exercise.
# ---------------------------------------------------------------------------
_REPRESENTATIVE_CANDIDATES = (
    C1_IntCounterCandidate(),
    C2_HonestBookkeeping({"tokA": "up", "tokB": "down"}),
    C3_LastWriteWinsRegister(),
    C4_AmnesiacUnderDelay(),
    C5_FrozenUnderExtension(),
    C6_DeadEndAtRenest(),
    C7_ThinDeckCandidate(),
    C8_NeighborAwareCandidate(),
    C8_NeighborBlindCandidate(),
)


def action_category_coverage() -> dict:
    covered = set()
    by_candidate = {}
    for cand in _REPRESENTATIVE_CANDIDATES:
        cats = sorted({cand.action_category(a) for a in cand.action_alphabet()})
        by_candidate[cand.name] = cats
        covered.update(cats)
    missing = sorted(set(MANIFOLD_ACTION_CATEGORIES) - covered)
    return {
        "by_candidate": by_candidate,
        "covered_categories": sorted(covered),
        "missing_categories": missing,
        "all_categories_covered": len(missing) == 0,
    }
