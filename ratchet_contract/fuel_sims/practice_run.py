#!/usr/bin/env python3
"""
practice_run.py -- PRACTICE run of the FULL ratchet pipeline, end-to-end, on
two executable bridge candidates: the owner's proposed spinor/QIT density-
matrix carrier (candidate_spinor_qit_exec.py, real qutip 2-qubit density
matrices) and a classical finite-relation rival (candidate_classical_exec.py,
plain integer weight-vector + relation, no qutip dependency).

SCOPE (binding): this is PRACTICE + fuel development -- getting the MACHINE
to operate and flow end-to-end, not a scientific or MSS claim about the
owner's manifold. promotion_allowed=false; formal_admission_allowed=false
throughout, matching every file this script imports.

THREE STAGES, run in order, each reported HONESTLY (FLOW or LOCK, with the
exact stage and reason -- never forced green):

  (a) fuel_adequacy_gate.py -- "Principle Zero." Run against the REAL
      candidate pool (system_v8/candidates/, its real manifest). This is a
      POOL-level gate: it governs whether ANY pairwise MSS comparison,
      including this practice pair, may run at all. Read-only against
      system_v8/candidates/ and fuel_gate/; nothing outside fuel_sims/ is
      written.

  (b) bridge_action_predictive.py's induce_action_predictive_partition, run
      DIRECTLY on both CandidateBridgeInterface exec candidates over a
      shared demand deck X_DECK (11 HistoryPoints) at PRACTICE_HORIZON,
      checked against 4 demanded-separation pairs D_PAIRS. Also runs a
      direct diagnostic re-partition after delay_long and after an
      extend_under_constraint(require_purity) attempt, using the SAME bridge
      machinery on shifted decks -- answering "do these distinctions survive
      X" directly, without bending gates.py's own evolvability semantics.

  (c) gates.py / mss.py's coarseness kernel (IDENTITY_GATE, persistence_gate,
      evolvability_gate, frontier, pairwise_mss), run through a
      CandidatePackage ADAPTER (BridgeCandidateAsPackage, defined below) that
      wraps each bridge candidate: State = HistoryPoint (root, prefix);
      probes() = every action-word up to PRACTICE_HORIZON, wrapped as
      ("peek", word); carrier.allowed_ops = single-action words wrapped as
      ("advance", word); reidentify(x,y) = identical apply()-fingerprint over
      probes() -- BY CONSTRUCTION the same equivalence stage (b) computes, so
      IDENTITY_GATE passing is EARNED, not fudged (mirrors
      ratchet_contract/toy_candidates.py's ToyQuotientRespecting discipline,
      the one toy every other gate is designed to let PASS cleanly).

Run under the sim-stack interpreter (qutip 5.2.3 confirmed installed there --
required because candidate_spinor_qit_exec.py imports qutip):
    /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 practice_run.py

Writes ratchet_contract/fuel_sims/results/practice_run.json. Nothing outside
ratchet_contract/fuel_sims/ is written; nothing is committed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

# ---------------------------------------------------------------------------
# sys.path wiring -- this file lives in ratchet_contract/fuel_sims/ and needs
# siblings in fuel_sims/ (the two candidate_*_exec.py files), ratchet_contract/
# (contract.py, gates.py, mss.py), ratchet_contract/bridge_validation/
# (bridge_interface.py, bridge_action_predictive.py), and repo-root/fuel_gate/
# (fuel_adequacy_gate.py). Same manual-insertion pattern every file in this
# repo's contract/bridge stack already uses (see bridge_action_predictive.py).
# ---------------------------------------------------------------------------
_FUEL_SIMS_DIR = Path(__file__).resolve().parent
_RATCHET_CONTRACT_DIR = _FUEL_SIMS_DIR.parent
_REPO_ROOT = _RATCHET_CONTRACT_DIR.parent
_BRIDGE_VALIDATION_DIR = _RATCHET_CONTRACT_DIR / "bridge_validation"
_FUEL_GATE_DIR = _REPO_ROOT / "fuel_gate"

for _p in (_FUEL_SIMS_DIR, _RATCHET_CONTRACT_DIR, _BRIDGE_VALIDATION_DIR, _FUEL_GATE_DIR):
    _sp = str(_p)
    if _sp not in sys.path:
        sys.path.insert(0, _sp)

from contract import CandidatePackage, Carrier, ControlCase, ControlSet, NestInterface  # noqa: E402
from gates import IDENTITY_GATE, persistence_gate, evolvability_gate  # noqa: E402
from mss import frontier as mss_frontier, pairwise_mss  # noqa: E402
from bridge_interface import Action, CandidateBridgeInterface, Outcome, history_point, replay  # noqa: E402
from bridge_action_predictive import induce_action_predictive_partition, separating_witness  # noqa: E402
import fuel_adequacy_gate as fag  # noqa: E402

import candidate_spinor_qit_exec as spinor_mod  # noqa: E402
import candidate_classical_exec as classical_mod  # noqa: E402

RESULTS_PATH = _FUEL_SIMS_DIR / "results" / "practice_run.json"

PRACTICE_HORIZON = 1  # shallow by design (tractability); see report for the thicken-and-rerun step at horizon=2


def log(msg: str) -> None:
    print(f"[practice_run] {msg}", file=sys.stderr, flush=True)


# ===========================================================================
# Stage 0 -- self-check that both exec candidates genuinely answer the SAME
# deck. Not part of the three named stages, but a precondition the report
# must not silently assume.
# ===========================================================================
def check_shared_deck() -> dict:
    same_actions = tuple(spinor_mod.ACTIONS) == tuple(classical_mod.ACTIONS)
    same_shots = spinor_mod.SHOT_BUDGET == classical_mod.SHOT_BUDGET
    same_roots = tuple(spinor_mod.ROOTS) == tuple(classical_mod.ROOTS)
    ok = same_actions and same_shots and same_roots
    receipt = {
        "same_action_deck": same_actions,
        "same_shot_budget": same_shots,
        "same_roots": same_roots,
        "action_count": len(spinor_mod.ACTIONS),
        "shot_budget": spinor_mod.SHOT_BUDGET,
        "roots": list(spinor_mod.ROOTS),
        "ok": ok,
    }
    if not ok:
        raise AssertionError(f"candidates do not answer the same deck -- refusing to proceed: {receipt}")
    log(f"shared-deck self-check OK: {len(spinor_mod.ACTIONS)} actions, {len(spinor_mod.ROOTS)} roots, "
        f"shot_budget={spinor_mod.SHOT_BUDGET}")
    return receipt


# ===========================================================================
# Stage (a) -- fuel_adequacy_gate.py, Principle Zero, run against the REAL
# pool (system_v8/candidates/). Read-only against system_v8/candidates and
# fuel_gate/; nothing outside fuel_sims/ is written by this script.
# ===========================================================================
def run_stage_a() -> dict:
    log("STAGE (a) fuel_adequacy_gate -- Principle Zero, real pool (system_v8/candidates/)")
    pool_dir = fag.REPO_ROOT / "system_v8" / "candidates"
    manifest_path = fag.GATE_DIR / "manifests" / "current_pool_provenance_manifest.json"
    schema_path = fag.GATE_DIR / "candidate_package_schema.json"
    result, error = fag.evaluate(pool_dir, manifest_path, schema_path,
                                  fag.DEFAULT_MIN_DIVERSITY_FLOOR, fag.DEFAULT_FILE_PATTERN)
    if error is not None:
        log(f"STAGE (a) LOCK -- gate itself errored: {error}")
        return {"stage": "a_fuel_adequacy", "flow": False, "lock_reason": "gate_error", "error": error}

    verdict = result["verdict"]
    flow = verdict == "ADEQUATE"
    log(f"STAGE (a) verdict={verdict} "
        f"(pool={pool_dir.name}, candidates={result['raw_candidate_count']}, "
        f"missing_slots={result['missing_slots']})")
    return {
        "stage": "a_fuel_adequacy",
        "pool_dir": str(pool_dir),
        "note": ("pool-level Principle-Zero gate -- this practice pair (spinor_qit, classical_bottomup) "
                 "lives inside this pool; a pool-level HOLD is inherited by every pair drawn from it, "
                 "including this one. Resolving it (adding countermodel/ablation_control candidates) "
                 "is out of scope for this fuel_sims/-scoped practice task."),
        "verdict": verdict,
        "flow": flow,
        "missing_slots": result["missing_slots"],
        "effective_vs_raw": result["effective_vs_raw"],
        "provenance_gaps_count": len(result["checks"]["c_provenance_present"]["provenance_gaps"]),
        "nonexecutable": result["checks"]["d_executable_enough"]["nonexecutable"],
        "checks_pass": {k: v["pass"] for k, v in result["checks"].items()},
        "full_result_written_to": None,  # filled in by main() after writing the sidecar file
    }


# ===========================================================================
# Demand deck -- shared HistoryPoints (X_DECK) and demanded pairs (D_PAIRS),
# used by BOTH stage (b) (directly, on the bridge candidates) and stage (c)
# (via the adapter, on the SAME HistoryPoint tuples).
# ===========================================================================
def build_deck():
    hp = history_point
    X = {
        "root_00": hp("root_00", ()),
        "root_bell": hp("root_bell", ()),
        "root_plus0": hp("root_plus0", ()),
        "root_mixed": hp("root_mixed", ()),
        "root_00_reprepared_bell": hp("root_00", ("prepare_bell",)),
        "root_plus0_couple_inner_outer": hp("root_plus0", ("couple_inner_outer",)),
        "root_plus0_couple_neighbor_neighbor": hp("root_plus0", ("couple_neighbor_neighbor",)),
        "root_plus0_order_H0_then_CNOT01": hp("root_plus0", (("ordered_compose", ("H0", "CNOT01")),)),
        "root_plus0_order_CNOT01_then_H0": hp("root_plus0", (("ordered_compose", ("CNOT01", "H0")),)),
        "root_00_delay_long": hp("root_00", ("delay_long",)),
        "root_bell_delay_long": hp("root_bell", ("delay_long",)),
    }
    X_DECK = tuple(X.values())
    D_PAIRS = (
        (X["root_00"], X["root_bell"]),  # different preparations must separate
        (X["root_00"], X["root_00_reprepared_bell"]),  # re-preparing to bell must look different from staying at 00
        (X["root_plus0_order_H0_then_CNOT01"], X["root_plus0_order_CNOT01_then_H0"]),  # order-sensitivity
        (X["root_plus0_couple_inner_outer"], X["root_plus0_couple_neighbor_neighbor"]),  # the two couplings differ
    )
    return X, X_DECK, D_PAIRS


def _hpj(x) -> str:
    root, prefix = x
    return f"{root}/{list(prefix)}"


# ===========================================================================
# Stage (b) -- bridge_action_predictive.py's induce_action_predictive_partition,
# run directly on both CandidateBridgeInterface candidates.
# ===========================================================================
def run_stage_b(X_named: dict, X_DECK: tuple, D_PAIRS: tuple) -> dict:
    log(f"STAGE (b) bridge_action_predictive -- horizon={PRACTICE_HORIZON}, |X|={len(X_DECK)}, |D|={len(D_PAIRS)}")
    spinor = spinor_mod.SpinorQitExecCandidate()
    classical = classical_mod.ClassicalRelationalExecCandidate()

    out: dict[str, Any] = {"stage": "b_action_predictive_bridge", "horizon": PRACTICE_HORIZON}
    per_candidate = {}
    for label, cand in (("spinor_qit_exec", spinor), ("classical_relational_exec", classical)):
        pi = induce_action_predictive_partition(cand, X_DECK, horizon=PRACTICE_HORIZON)
        index = {x: i for i, x in enumerate(X_DECK)}
        d_status = []
        all_separated = True
        for (a, b) in D_PAIRS:
            separated = pi[index[a]] != pi[index[b]]
            all_separated = all_separated and separated
            witness = None if separated else separating_witness(cand, a, b, horizon=PRACTICE_HORIZON)
            d_status.append({
                "pair": [_hpj(a), _hpj(b)], "separated": separated,
                "witness_if_not_separated": [repr(w) for w in witness] if witness else None,
            })
        per_candidate[label] = {
            "partition": list(pi),
            "cells": len(set(pi)),
            "D_all_separated_at_this_horizon": all_separated,
            "D_status": d_status,
        }
        log(f"  {label}: partition cells={len(set(pi))}, all_D_pairs_separated={all_separated}")
    out["per_candidate"] = per_candidate

    # cross-candidate direct outcome comparison at read_outcome_z on every X point
    # (both candidates share the "00"/"01"/"10"/"11" token vocabulary, so content
    # -- not just partition shape -- is directly comparable).
    cross = {}
    for name, x in X_named.items():
        root, prefix = x
        s_spinor = replay(spinor, root, prefix)
        _s2, o_spinor = spinor.step_C(s_spinor, "read_outcome_z", None)
        s_classical = replay(classical, root, prefix)
        _s2c, o_classical = classical.step_C(s_classical, "read_outcome_z", None)
        cross[name] = {"spinor_read_outcome_z": repr(o_spinor), "classical_read_outcome_z": repr(o_classical)}
    out["cross_candidate_read_outcome_z"] = cross

    # thicken-and-rerun step: if any D pair failed to separate at horizon=1,
    # rerun at horizon=2 for BOTH candidates (cheap -- memoized recursion, not
    # O(n^2)) and report whether thickening flips the result.
    any_hold = any(not per_candidate[c]["D_all_separated_at_this_horizon"] for c in per_candidate)
    out["thickened_rerun"] = None
    if any_hold:
        log("  at least one D pair unseparated at horizon=1 -- thickening to horizon=2 and rerunning")
        thick = {}
        for label, cand in (("spinor_qit_exec", spinor), ("classical_relational_exec", classical)):
            pi2 = induce_action_predictive_partition(cand, X_DECK, horizon=2)
            index = {x: i for i, x in enumerate(X_DECK)}
            d_status2 = [{"pair": [_hpj(a), _hpj(b)], "separated": pi2[index[a]] != pi2[index[b]]}
                         for (a, b) in D_PAIRS]
            thick[label] = {"partition": list(pi2), "cells": len(set(pi2)), "D_status": d_status2}
        out["thickened_rerun"] = {"horizon": 2, "per_candidate": thick}

    # direct diagnostic: does the order-sensitivity distinction (D_PAIRS[2],
    # rooted at root_plus0) survive a further delay_long, for each candidate?
    # Reuses the bridge machinery on a SHIFTED deck rather than routing
    # through gates.py's evolvability_gate (whose collapsed-edges check is
    # evaluated on the UN-shifted X by design -- see the module docstring).
    #
    # NAMED CONFOUND, found and kept rather than quietly re-rooted: this pair
    # is ALREADY unseparated for the classical carrier at the BASE level (see
    # D_status above and thickened_rerun -- true at horizon=1 AND horizon=2),
    # for a specific, checkable reason (verified by hand): from root_plus0 =
    # (2,2,0,0), rewrite H0 ("spread") maps to (1,1,1,1) regardless of
    # whether CNOT01 ("conditional swap", which is a no-op on a symmetric
    # (1,1,1,1) vector) runs before or after it -- a genuine fixed point of
    # THIS rewrite pair at THIS starting state, not a general order-
    # insensitivity claim (root_00 refutes that reading, see the SECOND,
    # root_00-rooted diagnostic immediately below). So "still_separated"
    # reading False for classical here answers "was a distinction ever
    # present to lose" (no) rather than "did delay erase one" -- reported
    # under its own key, not silently corrected, because it is itself a real
    # finding: this carrier's order-sensitivity does not hold uniformly
    # across the tested starting states.
    shifted_delay = {}
    x_h0 = X_named["root_plus0_order_H0_then_CNOT01"]
    x_cnot = X_named["root_plus0_order_CNOT01_then_H0"]
    x_h0_delayed = (x_h0[0], x_h0[1] + ("delay_long",))
    x_cnot_delayed = (x_cnot[0], x_cnot[1] + ("delay_long",))
    for label, cand in (("spinor_qit_exec", spinor), ("classical_relational_exec", classical)):
        pi3 = induce_action_predictive_partition(cand, (x_h0_delayed, x_cnot_delayed), horizon=PRACTICE_HORIZON)
        shifted_delay[label] = {
            "still_separated_after_delay_long": pi3[0] != pi3[1],
            "partition": list(pi3),
        }
    out["order_sensitivity_survives_delay_long__root_plus0__CONFOUNDED_see_note"] = shifted_delay
    log(f"  order-sensitivity (root_plus0, confounded for classical -- see note) survives delay_long: "
        f"{ {k: v['still_separated_after_delay_long'] for k, v in shifted_delay.items()} }")

    # SAME diagnostic, UNCONFOUNDED: rooted at root_00, where BOTH candidates
    # genuinely separate the order pair at the base level (confirmed in
    # D_status-style checks below) -- a clean apples-to-apples "does heavy
    # delay erase order-sensitivity" test.
    root00_order_clean = {}
    x_h0_00 = history_point("root_00", (("ordered_compose", ("H0", "CNOT01")),))
    x_cnot_00 = history_point("root_00", (("ordered_compose", ("CNOT01", "H0")),))
    x_h0_00_delayed = (x_h0_00[0], x_h0_00[1] + ("delay_long",))
    x_cnot_00_delayed = (x_cnot_00[0], x_cnot_00[1] + ("delay_long",))
    for label, cand in (("spinor_qit_exec", spinor), ("classical_relational_exec", classical)):
        pi_base = induce_action_predictive_partition(cand, (x_h0_00, x_cnot_00), horizon=PRACTICE_HORIZON)
        pi_after = induce_action_predictive_partition(cand, (x_h0_00_delayed, x_cnot_00_delayed), horizon=PRACTICE_HORIZON)
        root00_order_clean[label] = {
            "separated_at_base": pi_base[0] != pi_base[1],
            "still_separated_after_delay_long": pi_after[0] != pi_after[1],
        }
    out["order_sensitivity_survives_delay_long__root_00__unconfounded"] = root00_order_clean
    log(f"  order-sensitivity (root_00, unconfounded) base vs after delay_long: {root00_order_clean}")

    # direct diagnostic: isolate WHICH part of persistence_gate's continuation
    # (5x delay_short vs the default perturbation) is responsible for the
    # couple_inner_outer/couple_neighbor_neighbor collapse seen in stage (c)'s
    # persistence_gate(delay=5) call (which composes both by default -- see
    # BridgeCandidateAsPackage.persist()).
    x_cio = X_named["root_plus0_couple_inner_outer"]
    x_cnn = X_named["root_plus0_couple_neighbor_neighbor"]
    couple_isolation = {}
    for cont_label, extra in (
        ("delay_short_x5_only", ("delay_short",) * 5),
        ("perturb_only", ("perturb_small_rx0",)),
        ("delay_short_x5_plus_perturb", ("delay_short",) * 5 + ("perturb_small_rx0",)),
    ):
        per_cand = {}
        for label, cand in (("spinor_qit_exec", spinor), ("classical_relational_exec", classical)):
            xa = (x_cio[0], x_cio[1] + extra)
            xb = (x_cnn[0], x_cnn[1] + extra)
            pi5 = induce_action_predictive_partition(cand, (xa, xb), horizon=PRACTICE_HORIZON)
            per_cand[label] = pi5[0] != pi5[1]
        couple_isolation[cont_label] = per_cand
    out["couple_pair_persistence_isolation"] = couple_isolation
    log(f"  couple-pair persistence isolation (separated? by continuation): {couple_isolation}")

    # direct diagnostic: does extend_under_constraint(require_purity) change
    # whether the two prep-only roots (root_00 vs root_bell) stay separated?
    x_00 = X_named["root_00"]
    x_bell = X_named["root_bell"]
    ext_tok = ("extend_under_constraint", "require_purity")
    x_00_ext = (x_00[0], x_00[1] + (ext_tok,))
    x_bell_ext = (x_bell[0], x_bell[1] + (ext_tok,))
    shifted_evolve = {}
    for label, cand in (("spinor_qit_exec", spinor), ("classical_relational_exec", classical)):
        pi4 = induce_action_predictive_partition(cand, (x_00_ext, x_bell_ext), horizon=PRACTICE_HORIZON)
        shifted_evolve[label] = {"still_separated_after_require_purity_attempt": pi4[0] != pi4[1]}
    out["separation_survives_require_purity_attempt"] = shifted_evolve
    log(f"  separation survives require_purity attempt: "
        f"{ {k: v['still_separated_after_require_purity_attempt'] for k, v in shifted_evolve.items()} }")

    return out


# ===========================================================================
# The CandidatePackage adapter -- wraps a CandidateBridgeInterface candidate
# + a fixed demand deck into contract.py's shape, honestly (reidentify() is
# DEFINED as fingerprint-equality over the SAME word set probes() exposes --
# structurally guaranteed to match pi_probes, not fudged to match).
# ===========================================================================
def _words_upto(alphabet: Sequence[Action], horizon: int) -> tuple[tuple[Action, ...], ...]:
    words: list[tuple[Action, ...]] = [()]
    frontier: list[tuple[Action, ...]] = [()]
    for _ in range(horizon):
        new_frontier = []
        for w in frontier:
            for a in alphabet:
                new_frontier.append(w + (a,))
        words.extend(new_frontier)
        frontier = new_frontier
    return tuple(words)


class BridgeCandidateAsPackage(CandidatePackage):
    """Adapts a step_C-shaped CandidateBridgeInterface candidate into
    contract.py's CandidatePackage so gates.py / mss.py's coarseness kernel
    can run on it. State = HistoryPoint (root, prefix) -- itself a plain
    Hashable tuple, so no separate opaque-state wrapping is needed at this
    layer (the UNDERLYING carrier state, e.g. a qutip Qobj, stays fully
    opaque and is never touched by this adapter or by gates.py/mss.py --
    only replayed via bridge_interface.replay()).

    probes() = every action-word up to `horizon`, wrapped ("peek", word):
    apply() computes the OUTCOME TRACE of tentatively running that word from
    the given HistoryPoint, without committing (a read). carrier.allowed_ops
    = single-action words wrapped ("advance", (action,)): apply() extends
    the HistoryPoint's prefix by one action (a transform, matching
    contract.py's apply() dual-dispatch convention -- see toy_candidates.py).

    reidentify(record, current_state) = "identical outcome trace for every
    word in probes()" -- BY CONSTRUCTION the same relation
    induce_action_predictive_partition computes at the SAME horizon (both
    are "agree on every action word up to length H"), so IDENTITY_GATE's
    pi_probes == pi_reidentify check is EARNED by the definitions matching,
    not coincidence."""

    def __init__(
        self,
        bridge_candidate: CandidateBridgeInterface,
        X: Sequence[tuple],
        *,
        horizon: int,
        action_alphabet: Optional[Sequence[Action]] = None,
        name: Optional[str] = None,
    ):
        self._bridge = bridge_candidate
        self._X = tuple(X)
        self._horizon = horizon
        self._alphabet = tuple(action_alphabet or bridge_candidate.action_alphabet())
        self._words = _words_upto(self._alphabet, horizon)
        self._name = name or f"{bridge_candidate.name}__as_package_h{horizon}"
        self._memo: dict = {}  # bookkeeping cache keyed by (root, prefix) -- see bridge_interface.py's
                                # bookkeeping-vs-illicit-identity rule; never consulted to alter a result,
                                # only to avoid recomputing replay() for a syntactic address seen before.

    @property
    def name(self) -> str:
        return self._name

    @property
    def carrier(self) -> Carrier:
        allowed = tuple(("advance", (a,)) for a in self._alphabet)
        return Carrier(description=f"bridge-candidate adapter over {self._bridge.name}, horizon={self._horizon}",
                        allowed_ops=allowed)

    def states(self):
        return self._X

    def probes(self):
        return tuple(("peek", w) for w in self._words)

    def _trace(self, x: tuple, word: tuple[Action, ...]) -> tuple[Outcome, ...]:
        root, prefix = x
        state = replay(self._bridge, root, prefix, memo=self._memo)
        trace = []
        for a in word:
            state, o = self._bridge.step_C(state, a, None)
            trace.append(o)
        return tuple(trace)

    def apply(self, op, state):
        kind, word = op
        if kind == "peek":
            return self._trace(state, word)
        if kind == "advance":
            root, prefix = state
            return (root, prefix + word)
        raise ValueError(f"unknown op kind {kind!r} (expected 'peek' or 'advance')")

    def reidentify(self, record, current_state) -> bool:
        for word in self._words:
            if self._trace(record, word) != self._trace(current_state, word):
                return False
        return True

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        root, prefix = state
        extra: list[Action] = []
        for _ in range(delay or 0):
            extra.append("delay_short")
        if perturbation:
            extra.append("perturb_small_rx0")
        if partial_access:
            extra.append("restrict_trace_out_qubit1")
        if relabeled:
            extra.append("renest_swap01")
        return (root, prefix + tuple(extra))

    def evolve(self, new_constraint) -> Optional["BridgeCandidateAsPackage"]:
        name = new_constraint if new_constraint in ("trace_preserving", "require_purity") else "require_purity"
        token = ("extend_under_constraint", name)
        new_X = tuple((r, p + (token,)) for (r, p) in self._X)
        return BridgeCandidateAsPackage(self._bridge, new_X, horizon=self._horizon,
                                         action_alphabet=self._alphabet, name=f"{self._name}__evolved_{name}")

    def nest_interface(self) -> NestInterface:
        # Real cross-candidate nesting is explicitly out of scope -- see
        # bridge_interface.py's NestContext docstring. Empty declaration ->
        # extension_gate reads this as HOLD/vacuous, never penalized.
        return NestInterface()

    def declared_primitives(self) -> tuple[str, ...]:
        return tuple(self._bridge.declared_primitives())

    def controls(self) -> ControlSet:
        root, _ = self._X[0]
        roots_seen = {r for r, _ in self._X}
        pos = ()
        if "root_00" in roots_seen and "root_bell" in roots_seen:
            pos = (ControlCase("root_00_vs_root_bell", ("root_00", ()), ("root_bell", ()), True),)
        neg = (ControlCase(
            "trace_preserving_is_a_genuine_noop",
            ("root_00", ()),
            ("root_00", (("extend_under_constraint", "trace_preserving"),)),
            False,
        ),)
        return ControlSet(positive=pos, negative=neg)


# ===========================================================================
# Stage (c) -- gates.py / mss.py's coarseness kernel via the adapter.
# ===========================================================================
def run_stage_c(X_DECK: tuple, D_PAIRS: tuple) -> dict:
    log(f"STAGE (c) gates.py/mss.py coarseness kernel -- horizon={PRACTICE_HORIZON}, |X|={len(X_DECK)}")
    spinor = spinor_mod.SpinorQitExecCandidate()
    classical = classical_mod.ClassicalRelationalExecCandidate()

    spinor_pkg = BridgeCandidateAsPackage(spinor, X_DECK, horizon=PRACTICE_HORIZON, name="spinor_qit_exec_pkg")
    classical_pkg = BridgeCandidateAsPackage(classical, X_DECK, horizon=PRACTICE_HORIZON, name="classical_relational_exec_pkg")

    out: dict[str, Any] = {"stage": "c_gates_mss_kernel", "horizon": PRACTICE_HORIZON}

    identity = {}
    for pkg in (spinor_pkg, classical_pkg):
        idg = IDENTITY_GATE(pkg, X_DECK)
        identity[pkg.name] = idg.to_json()
        log(f"  IDENTITY_GATE({pkg.name}) = {idg.verdict.value} "
            f"(pi_probes_cells={idg.reasons.get('pi_probes_cells')}, "
            f"pi_reidentify_cells={idg.reasons.get('pi_reidentify_cells')})")
    out["identity_gate"] = identity
    both_identity_pass = all(v["verdict"] == "PASS" for v in identity.values())

    # cross-check: stage (b)'s raw bridge partition MUST equal stage (c)'s
    # pi_probes/pi_reidentify at the SAME horizon -- both are defined as the
    # same "agree on every word up to H" relation; a mismatch here would be a
    # bug in this file, not a research finding, and is reported as such.
    cross_check = {}
    for label, cand, pkg in (("spinor_qit_exec", spinor, spinor_pkg),
                              ("classical_relational_exec", classical, classical_pkg)):
        pi_bridge = induce_action_predictive_partition(cand, X_DECK, horizon=PRACTICE_HORIZON)
        pi_pkg_probes = tuple(identity[pkg.name]["reasons"]["pi_probes"])
        pi_pkg_reidentify = tuple(identity[pkg.name]["reasons"]["pi_reidentify"])
        cross_check[label] = {
            "bridge_partition_equals_pkg_pi_probes": list(pi_bridge) == list(pi_pkg_probes),
            "bridge_partition_equals_pkg_pi_reidentify": list(pi_bridge) == list(pi_pkg_reidentify),
        }
    out["stage_b_vs_stage_c_cross_check"] = cross_check
    cross_check_ok = all(v["bridge_partition_equals_pkg_pi_probes"] and v["bridge_partition_equals_pkg_pi_reidentify"]
                          for v in cross_check.values())
    log(f"  stage(b)-vs-stage(c) partition cross-check: {'OK, identical' if cross_check_ok else 'MISMATCH -- bug'}")

    if not both_identity_pass:
        out["frontier"] = None
        out["pairwise_mss"] = None
        out["flow"] = False
        out["lock_stage"] = "IDENTITY_GATE"
        log("  STAGE (c) LOCK at IDENTITY_GATE -- at least one adapter's partition is not probe-honest")
        return out

    index = {x: i for i, x in enumerate(X_DECK)}

    persist_r = {}
    evolve_r = {}
    for pkg in (spinor_pkg, classical_pkg):
        pr = persistence_gate(pkg, X_DECK, D_PAIRS, delay=5)
        persist_r[pkg.name] = pr.to_json()
        er = evolvability_gate(pkg, X_DECK, D_PAIRS, new_constraint="require_purity")
        evolve_r[pkg.name] = er.to_json()
        log(f"  persistence_gate({pkg.name}, delay=5) = {pr.verdict.value}; "
            f"evolvability_gate({pkg.name}, require_purity) = {er.verdict.value}")
    out["persistence_gate_delay5"] = persist_r
    out["evolvability_gate_require_purity"] = evolve_r

    fr = mss_frontier(
        [spinor_pkg, classical_pkg], X_DECK, D_PAIRS,
        thicken_persistence=True, persistence_kwargs={"delay": 5},
        thicken_evolvability=True, new_constraint="require_purity",
        thicken_wholenest=False,
    )
    out["frontier"] = fr
    log(f"  frontier(): survivors={fr['survivors']}, purgatory={[p['candidate'] for p in fr['purgatory']]}, "
        f"antichain={fr['antichain']}")

    pw = pairwise_mss(spinor_pkg, classical_pkg, X_DECK, D_PAIRS)  # base coarseness, no thickening
    out["pairwise_mss_base_no_thickening"] = pw.to_json()
    log(f"  pairwise_mss (base, no thickening) = {pw.verdict.value}")

    out["flow"] = True
    out["lock_stage"] = None
    return out


def main() -> int:
    log("=" * 70)
    log("PRACTICE RUN -- spinor_qit_exec vs classical_relational_exec")
    log("promotion_allowed=false; formal_admission_allowed=false throughout")
    log("=" * 70)

    shared_deck_receipt = check_shared_deck()
    memory_gate_receipt = getattr(spinor_mod, "MEMORY_GATE_RECEIPT", None)

    stage_a = run_stage_a()

    X_named, X_DECK, D_PAIRS = build_deck()
    stage_b = run_stage_b(X_named, X_DECK, D_PAIRS)
    stage_c = run_stage_c(X_DECK, D_PAIRS)

    overall_flow = bool(stage_a.get("flow")) and bool(stage_c.get("flow"))
    # stage (b) never itself "locks" the pipeline (HOLDs at horizon=1 are the
    # expected practice signal to thicken, handled inline) -- it contributes
    # findings, not a pass/fail gate the way (a) and (c) do.

    report = {
        "schema_version": "practice-run/0.1",
        "ceiling": (
            "PRACTICE + fuel development, exercising ratchet_contract's pipeline machinery "
            "(fuel_adequacy_gate.py -> bridge_action_predictive.py -> gates.py/mss.py) end-to-end on two "
            "small, finite, REAL executable carriers. NOT a scientific or MSS claim about the owner's "
            "manifold. promotion_allowed=false; formal_admission_allowed=false."
        ),
        "practice_horizon": PRACTICE_HORIZON,
        "shot_budget": spinor_mod.SHOT_BUDGET,
        "shared_deck_self_check": shared_deck_receipt,
        "memory_gate_receipt": memory_gate_receipt,
        "demand_deck": {
            "X_DECK_size": len(X_DECK),
            "X_DECK": {k: _hpj(v) for k, v in X_named.items()},
            "D_PAIRS": [[_hpj(a), _hpj(b)] for a, b in D_PAIRS],
        },
        "stage_a_fuel_adequacy": stage_a,
        "stage_b_action_predictive_bridge": stage_b,
        "stage_c_gates_mss_kernel": stage_c,
        "overall": {
            "stage_a_flow": stage_a.get("flow"),
            "stage_c_flow": stage_c.get("flow"),
            "stage_c_lock_stage": stage_c.get("lock_stage"),
            "pipeline_flows_end_to_end_including_pool_level_fuel_gate": overall_flow,
            "pipeline_flows_on_the_pair_itself_stage_b_and_c_only": bool(stage_c.get("flow")),
        },
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text(json.dumps(report, indent=2, sort_keys=False, default=str) + "\n", encoding="utf-8")
    log(f"full receipt written to {RESULTS_PATH}")

    log("=" * 70)
    log(f"STAGE (a) fuel_adequacy on the real pool:  {stage_a['verdict']}  (flow={stage_a['flow']})")
    log(f"STAGE (c) gates/mss kernel on the pair:     {'FLOW' if stage_c['flow'] else 'LOCK at ' + str(stage_c['lock_stage'])}")
    log("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
