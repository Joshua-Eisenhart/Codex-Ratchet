#!/usr/bin/env python3
"""
bridge_self_tests.py -- tests of the BRIDGE ITSELF (BRIDGE_VALIDATION).

Three self-tests, distinct from controls.py's 9 candidate-level controls:

  (a) action-deck permutation + relabeling invariance -- permuting/renaming
      deck tokens must not change what a candidate reports for the
      semantically-same history (direct outcome-content check; see
      controls.py's module docstring for why this must NOT be checked via
      partition-digest comparison alone).
  (b) outcome-encoding change invariance -- renaming the OUTCOME token
      vocabulary (not the action vocabulary) must not change the induced
      PARTITION (grouping), because both bridges only ever compare Outcome
      values by structural equality, never by pattern-matching a specific
      token string.
  (c) HIDDEN LOOKUP-TABLE control -- a candidate that hides a hand-authored
      answer table behind step_C, keyed by the raw literal action-token
      strings rather than by any genuine order/continuation-sensitive rule,
      must be CAUGHT (by the relabeling-invariance mechanism from (a), by a
      biased/thin-deck-style ablation, or by both) -- the opaque-state
      interface does NOT make step_C's behaviour neutral by itself; a
      smuggled authored answer is still a raw-label dependency the same
      controls that catch C2's illicit candidate are built to catch.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PARENT = Path(__file__).resolve().parent.parent
if str(_PARENT) not in sys.path:
    sys.path.insert(0, str(_PARENT))

from bridge_interface import (  # noqa: E402
    BridgeCheckResult,
    CandidateBridgeInterface,
    Outcome,
    history_point,
    replay,
)
from bridge_action_predictive import induce_action_predictive_partition  # noqa: E402
from bridge_smt_relational import induce_smt_relational_partition  # noqa: E402

from controls import (  # noqa: E402
    C1_IntCounterCandidate,
    C2_HonestBookkeeping,
    C2_IllicitRawLabel,
    _relabeling_check,
)


# ===========================================================================
# (a) action-deck permutation + relabeling invariance
# ===========================================================================
def _partition_relabeling_check(build_candidate, base_tokens: tuple, relabeled_tokens: tuple, horizon: int = 1) -> dict:
    """Complementary PARTITION-level view of the same relabeling used by
    controls.py's C2 (direct outcome-content check). Included to make the
    methodological point explicit and CHECKED, not just asserted: partition
    equality is invariant under relabeling for the HONEST candidate too,
    but (see result) is NOT by itself sufficient to catch the illicit
    candidate's bug, because a consistent content swap preserves grouping
    structure."""
    shapes = ((), ("up",), ("down",), ("up", "up"), ("down", "down"), ("up", "down"), ("down", "up"))

    def realize(tokens, shape):
        up, down = tokens
        return tuple(up if s == "up" else down for s in shape)

    cand_base = build_candidate(base_tokens)
    cand_relabeled = build_candidate(relabeled_tokens)
    X_base = tuple(history_point("r0", realize(base_tokens, s)) for s in shapes)
    X_relabeled = tuple(history_point("r0", realize(relabeled_tokens, s)) for s in shapes)
    alphabet_base = base_tokens + ("read_outcome",)
    alphabet_relabeled = relabeled_tokens + ("read_outcome",)

    pi_base = induce_action_predictive_partition(cand_base, X_base, horizon=horizon, action_alphabet=alphabet_base)
    pi_relabeled = induce_action_predictive_partition(
        cand_relabeled, X_relabeled, horizon=horizon, action_alphabet=alphabet_relabeled
    )
    return {
        "pi_base": list(pi_base), "pi_relabeled": list(pi_relabeled),
        "partition_grouping_invariant": pi_base == pi_relabeled,
    }


def run_relabeling_invariance_self_test() -> BridgeCheckResult:
    honest_content = _relabeling_check(
        lambda toks: C2_HonestBookkeeping({toks[0]: "up", toks[1]: "down"}),
        ("tokA", "tokB"), ("zzz", "yyy"),
    )
    illicit_content = _relabeling_check(
        lambda toks: C2_IllicitRawLabel(toks),
        ("tokA", "tokB"), ("zzz_up", "aaa_down"),
    )
    honest_partition = _partition_relabeling_check(
        lambda toks: C2_HonestBookkeeping({toks[0]: "up", toks[1]: "down"}),
        ("tokA", "tokB"), ("zzz", "yyy"),
    )
    illicit_partition = _partition_relabeling_check(
        lambda toks: C2_IllicitRawLabel(toks),
        ("tokA", "tokB"), ("zzz_up", "aaa_down"),
    )

    honest_content_invariant = honest_content["relabeling_invariant"] is True
    illicit_content_invariant = illicit_content["relabeling_invariant"] is True  # expected False

    # The methodological point (module docstring in controls.py), CHECKED
    # here rather than only asserted: does the illicit candidate's bug
    # survive a partition-only comparison even though the direct-content
    # check catches it? Report whatever actually happens.
    partition_only_would_miss_the_bug = (
        (not illicit_content_invariant) and illicit_partition["partition_grouping_invariant"]
    )

    fired = honest_content_invariant and (not illicit_content_invariant)

    return BridgeCheckResult(
        check="self_test_action_relabeling_invariance",
        label=f"honest_content_invariant={honest_content_invariant};illicit_content_invariant={illicit_content_invariant}",
        expected_label="honest_content_invariant=True;illicit_content_invariant=False",
        fired_as_expected=fired,
        reasons={
            "direct_outcome_content_check": {
                "honest": honest_content, "illicit": illicit_content,
            },
            "partition_grouping_check_supplementary": {
                "honest": honest_partition, "illicit": illicit_partition,
            },
            "methodological_finding": {
                "claim": "partition-digest comparison alone can miss a relabeling bug that direct "
                         "outcome-content comparison catches, because a consistent content swap "
                         "preserves grouping structure",
                "observed_on_illicit_candidate": partition_only_would_miss_the_bug,
                "note": ("this is checked, not assumed -- if observed_on_illicit_candidate is False here, "
                         "the illicit candidate's specific bug happened to also break grouping on this deck, "
                         "which is a fine outcome but does not by itself establish the general claim; the "
                         "direct-content check remains the check controls.py C2 and this self-test rely on"),
            },
        },
    )


# ===========================================================================
# (b) outcome-encoding change invariance
# ===========================================================================
class _OutcomeRelabeledCandidate(CandidateBridgeInterface):
    """Wraps an inner candidate; every returned Outcome token is renamed
    through a fixed bijection. Actions and states are untouched -- only the
    OUTCOME vocabulary changes. Both bridges only ever compare Outcome
    values by structural (==) equality, never by pattern-matching a
    specific token string, so the induced PARTITION should be unaffected."""

    def __init__(self, inner: CandidateBridgeInterface, token_map: dict):
        self._inner = inner
        self._map = dict(token_map)
        self.name = f"{inner.name}__outcome_relabeled"

    def action_alphabet(self):
        return self._inner.action_alphabet()

    def action_category(self, action):
        return self._inner.action_category(action)

    def initial_state(self, root):
        return self._inner.initial_state(root)

    def step_C(self, state, action, nest_context=None):
        next_state, outcome = self._inner.step_C(state, action, nest_context)
        renamed = Outcome(tuple((self._map[tok], mult) for tok, mult in outcome.entries))
        return next_state, renamed


def run_outcome_encoding_invariance_self_test() -> BridgeCheckResult:
    inner = C1_IntCounterCandidate()
    token_map = {"ack": "K", "even": "E", "odd": "O"}
    recoded = _OutcomeRelabeledCandidate(inner, token_map)

    horizon = 2
    X = tuple(
        history_point("r0", p)
        for p in [(), ("perturb",), ("perturb", "perturb"), ("perturb", "perturb", "perturb")]
    )
    alphabet = ("perturb", "read_outcome", "bracket_compose_probe", "couple_inner_outer_probe")

    pi_inner_ap = induce_action_predictive_partition(inner, X, horizon=horizon, action_alphabet=alphabet)
    pi_recoded_ap = induce_action_predictive_partition(recoded, X, horizon=horizon, action_alphabet=alphabet)
    smt_inner = induce_smt_relational_partition(inner, X, horizon=horizon, action_alphabet=alphabet)
    smt_recoded = induce_smt_relational_partition(recoded, X, horizon=horizon, action_alphabet=alphabet)

    ap_invariant = pi_inner_ap == pi_recoded_ap
    smt_invariant = smt_inner.partition == smt_recoded.partition
    fired = ap_invariant and smt_invariant

    return BridgeCheckResult(
        check="self_test_outcome_encoding_invariance",
        label=f"action_predictive_invariant={ap_invariant};smt_relational_invariant={smt_invariant}",
        expected_label="action_predictive_invariant=True;smt_relational_invariant=True",
        fired_as_expected=fired,
        reasons={
            "inner_candidate": inner.name, "token_map": token_map,
            "pi_inner_action_predictive": list(pi_inner_ap), "pi_recoded_action_predictive": list(pi_recoded_ap),
            "pi_inner_smt_relational": list(smt_inner.partition), "pi_recoded_smt_relational": list(smt_recoded.partition),
            "smt_inner_solver_agreement": smt_inner.all_agree, "smt_recoded_solver_agreement": smt_recoded.all_agree,
        },
    )


# ===========================================================================
# (c) HIDDEN LOOKUP-TABLE control
# ===========================================================================
class _HiddenLookupTableCandidate(CandidateBridgeInterface):
    """Smuggles a hand-authored answer table keyed by the LITERAL prefix
    tuple of raw action-token strings, instead of computing outcomes from
    any genuine order/continuation-sensitive rule. On any prefix NOT in its
    table it falls back to a constant default. This candidate exists to
    prove the campaign CATCHES this pattern -- it does not model a real
    carrier and is not one of the 9 numbered controls."""

    name = "hidden_lookup_table_cheat"

    _TABLE = {
        (): Outcome.deterministic("base"),
        ("tokA",): Outcome.deterministic("hand_authored_1"),
        ("tokA", "tokB"): Outcome.deterministic("hand_authored_2"),
        ("tokB", "tokA"): Outcome.deterministic("hand_authored_2"),  # authored to LOOK order-insensitive here
    }
    _DEFAULT = Outcome.deterministic("default_fallback")

    def action_alphabet(self):
        return ("tokA", "tokB", "read_outcome")

    def action_category(self, action):
        return "read_outcome"

    def initial_state(self, root):
        return ()  # opaque state IS the literal prefix so far -- the smuggled identity

    def step_C(self, state, action, nest_context=None):
        if action == "read_outcome":
            return state, self._TABLE.get(state, self._DEFAULT)
        return state + (action,), Outcome.deterministic("ack")


class _RelabeledHiddenLookupTableCandidate(_HiddenLookupTableCandidate):
    """SAME step_C (inherited, unmodified) -- only the offered deck tokens
    change. Because step_C's table lookup is keyed on whatever raw token
    string was actually passed in, this alone is enough to make the cheat
    visible under relabeling."""

    name = "hidden_lookup_table_cheat__relabeled"

    def action_alphabet(self):
        return ("zzz", "yyy", "read_outcome")


def run_hidden_lookup_table_self_test() -> BridgeCheckResult:
    base = _HiddenLookupTableCandidate()
    relabeled = _RelabeledHiddenLookupTableCandidate()
    relabel_map = {"tokA": "zzz", "tokB": "yyy"}
    shapes = [(), ("tokA",), ("tokA", "tokB"), ("tokB", "tokA")]

    probe_base = {}
    probe_relabeled = {}
    for shape in shapes:
        state_b = replay(base, "r0", shape)
        _s, o_b = base.step_C(state_b, "read_outcome", None)
        probe_base[shape] = repr(o_b)

        relabeled_prefix = tuple(relabel_map[t] for t in shape)
        state_r = replay(relabeled, "r0", relabeled_prefix)
        _s, o_r = relabeled.step_C(state_r, "read_outcome", None)
        probe_relabeled[relabeled_prefix] = repr(o_r)

    mismatches = []
    for shape in shapes:
        relabeled_prefix = tuple(relabel_map[t] for t in shape)
        if probe_base[shape] != probe_relabeled[relabeled_prefix]:
            mismatches.append({
                "shape": list(shape), "base_outcome": probe_base[shape],
                "relabeled_prefix": list(relabeled_prefix), "relabeled_outcome": probe_relabeled[relabeled_prefix],
            })
    caught_by_relabeling_invariance = len(mismatches) > 0

    # Secondary signature: an action combination the table was never
    # authored for (a novel word), revealing the fallback -- the same
    # ablation/biased-deck reasoning C8 uses, applied to a novel action
    # combination the smuggled table does not cover.
    novel_state = replay(base, "r0", ("tokA", "tokA"))
    _s, o_novel = base.step_C(novel_state, "read_outcome", None)
    caught_by_novel_word_fallback = repr(o_novel) == repr(_HiddenLookupTableCandidate._DEFAULT)

    fired = caught_by_relabeling_invariance or caught_by_novel_word_fallback

    return BridgeCheckResult(
        check="self_test_hidden_lookup_table_catch",
        label=(
            f"caught_by_relabeling_invariance={caught_by_relabeling_invariance};"
            f"caught_by_novel_word_fallback={caught_by_novel_word_fallback}"
        ),
        expected_label="caught_by_at_least_one=True",
        fired_as_expected=fired,
        reasons={
            "candidate": base.name,
            "probe_base": {repr(k): v for k, v in probe_base.items()},
            "probe_relabeled": {repr(k): v for k, v in probe_relabeled.items()},
            "mismatches_under_relabeling": mismatches,
            "novel_word_probed": ["tokA", "tokA"], "novel_word_outcome": repr(o_novel),
            "caught_by_relabeling_invariance": caught_by_relabeling_invariance,
            "caught_by_novel_word_fallback": caught_by_novel_word_fallback,
            "note": ("the opaque-state interface does not make step_C's behaviour neutral by itself -- "
                     "a raw-label-keyed lookup table is caught the same way C2's illicit candidate is "
                     "caught: relabeling the deck exposes that the table's keys did not travel with the "
                     "renaming, because they were never derived from a declared semantic map"),
        },
    )


def run_all_self_tests() -> dict:
    return {
        "self_test_action_relabeling_invariance": run_relabeling_invariance_self_test(),
        "self_test_outcome_encoding_invariance": run_outcome_encoding_invariance_self_test(),
        "self_test_hidden_lookup_table_catch": run_hidden_lookup_table_self_test(),
    }
