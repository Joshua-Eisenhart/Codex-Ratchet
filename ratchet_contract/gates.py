#!/usr/bin/env python3
"""
gates.py -- deterministic gate operators (CODE, never LLM judgment).

Style match: system_v7/constraint_core/ratchet/ratchet_engine.py's partition
kernel (`_normalise_partition`, `_partition_coarser`, `compute_frontier_cache`)
and fuel_gate/fuel_adequacy_gate.py's exit-code/receipt discipline (every
check runs every time; every failing check is reported, not just the first;
reasons are a JSON dict, never prose a human has to parse).

THE PARTITION KERNEL (normalise_partition / induced_partition / partition_coarser
/ partition_digest / collapsed_demand_edges) is a direct, deliberate port of
ratchet_engine.py's own math onto CandidatePackage objects. MSS is partition
coarseness, full stop -- there is exactly one judge in this file and in
mss.py, and every gate below either (a) is an ELIGIBILITY control on whether
a candidate's partition may be trusted at all (IDENTITY_GATE), or (b)
ENLARGES the demand set D that the SAME kernel evaluates (persistence_gate,
evolvability_gate, extension_gate emit demand-thickened survivorship checks,
they do not compute independent scores).

Six gates, each returns a GateResult with verdict in {PASS, FAIL, HOLD,
UNRESOLVED} and a reasons dict:
  buildability_gate     -- does the candidate instantiate/run its own probes
                            on its own states without error?               (UNCHANGED per owner correction)
  probe_validity_gate   -- does D separate the candidate's own positive
                            controls, AND does D avoid falsely separating
                            the candidate's own negative controls?          (positive-control check UNCHANGED
                                                                              per owner correction; negative-control
                                                                              check ADDED per audit finding F1)
  IDENTITY_GATE         -- THE NOMINALIST CORE: does reidentify() exactly
                            reproduce the probe-induced partition (a=a iff
                            a~b)? Gates ELIGIBILITY for every downstream
                            partition-coarseness comparison.
  persistence_gate       -- DEMAND GENERATOR: do D's distinctions survive
                            being pushed through persist() (delay/
                            perturbation/relabeling/partial-access)?
  evolvability_gate      -- DEMAND GENERATOR: do D's distinctions survive
                            being pushed through evolve(new_constraint)?
  extension_gate         -- DEMAND GENERATOR (whole-nest): does a declared
                            nest_interface recompute_digest match a fresh
                            recompute of the induced partition?
  adequacy               -- combines all six into one verdict.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Sequence

from contract import CandidatePackage, State


class Verdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    HOLD = "HOLD"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class GateResult:
    gate: str
    candidate: str
    verdict: Verdict
    reasons: dict

    def to_json(self) -> dict:
        return {
            "gate": self.gate,
            "candidate": self.candidate,
            "verdict": self.verdict.value,
            "reasons": self.reasons,
        }


def _result(gate: str, candidate: CandidatePackage, verdict: Verdict, reasons: dict) -> GateResult:
    return GateResult(gate=gate, candidate=candidate.name, verdict=verdict, reasons=reasons)


# ===========================================================================
# THE PARTITION KERNEL -- ported from ratchet_engine.py, generalized from
# "candidate assignment over generated rows" to "CandidatePackage.reidentify
# over an externally supplied observation surface X."
# ===========================================================================
def normalise_partition(labels: Sequence[Any]) -> tuple[int, ...]:
    """Exact port of ratchet_engine.py's `_normalise_partition`: canonical
    block-label encoding, first-seen-gets-lowest-label."""
    seen: dict[Any, int] = {}
    out: list[int] = []
    for v in labels:
        if v not in seen:
            seen[v] = len(seen)
        out.append(seen[v])
    return tuple(out)


def induced_partition(candidate: CandidatePackage, X: Sequence[State]) -> tuple[int, ...]:
    """pi_C : X -> Q_pi. Union-find over candidate.reidentify(x,y) checked
    BOTH directions, across every pair of X. This is "the candidate's
    presentation as a probe-relative quotient S/~_M"
    (HOW_THE_ENGINES_RUN_THE_RATCHET.md Part A.2), generalized from
    ratchet_engine.py's `_candidate_assignment` (which reads a parameter
    proposal's assignment keys) to reading a CandidatePackage's own
    reidentify oracle directly.

    Meaningful only for identity-honest candidates -- callers that skip
    IDENTITY_GATE first are trusting an uncontrolled partition. mss.py
    always runs IDENTITY_GATE before calling this."""
    n = len(X)
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(n):
        for j in range(i + 1, n):
            if candidate.reidentify(X[i], X[j]) and candidate.reidentify(X[j], X[i]):
                union(i, j)

    return normalise_partition([find(i) for i in range(n)])


def partition_coarser(left: Sequence[int], right: Sequence[int]) -> bool:
    """Exact port of ratchet_engine.py's `_partition_coarser`: whether
    `left` is a quotient/coarsening of `right` (every block of `right`
    lies inside a single block of `left`)."""
    mapping: dict[int, int] = {}
    for right_label, left_label in zip(right, left, strict=True):
        previous = mapping.setdefault(right_label, left_label)
        if previous != left_label:
            return False
    return True


def partition_digest(partition: Sequence[int]) -> str:
    raw = json.dumps(list(partition), separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def collapsed_demand_edges(
    partition: Sequence[int], index: dict[State, int], D: Sequence[tuple[State, State]]
) -> list[tuple[State, State]]:
    """L_D(pi), itemized: which demanded pairs (x,y) in D got merged into
    the same block of `partition`. Mirrors ratchet_engine.py's
    `collapsed_demand_edges` count, but returns the offending pairs
    (never just a count) so reasons dicts stay non-empty and inspectable."""
    collapsed = []
    for (a, b) in D:
        if partition[index[a]] == partition[index[b]]:
            collapsed.append((a, b))
    return collapsed


def collapsed_demand_edge_buckets(
    partition: Sequence[int],
    index: dict[State, int],
    D: Sequence[tuple[State, State]],
    *,
    base_partition: Optional[Sequence[int]] = None,
    base_index: Optional[dict[State, int]] = None,
    base_pairs: Optional[Sequence[tuple[State, State]]] = None,
) -> dict[str, list[tuple[State, State]]]:
    """Classify collapsed demanded edges by whether continuation caused loss.

    With no base partition, retain the historical undifferentiated result.
    ``base_pairs`` maps continuation edges back to their original X pair; it
    is needed when continuation changes the state values (persistence).
    """
    collapsed = collapsed_demand_edges(partition, index, D)
    buckets = {"collapsed_edges": collapsed}
    if base_partition is None or base_index is None:
        return buckets
    if base_pairs is None:
        base_pairs = D
    already = []
    newly = []
    collapsed_positions = {
        position for position, edge in enumerate(D)
        if partition[index[edge[0]]] == partition[index[edge[1]]]
    }
    for position, edge in enumerate(D):
        if position not in collapsed_positions:
            continue
        try:
            original = base_pairs[position]
            a, b = original
            if base_partition[base_index[a]] == base_partition[base_index[b]]:
                already.append(edge)
            else:
                newly.append(edge)
        except (ValueError, KeyError, IndexError):
            newly.append(edge)
    buckets["already_collapsed_at_base"] = already
    buckets["newly_collapsed_by_continuation"] = newly
    return buckets


def reidentify_internal_contradictions(
    candidate: CandidatePackage, X: Sequence[State]
) -> list[tuple[State, State]]:
    """Return same-final-block pairs directly denied by reidentify()."""
    partition = induced_partition(candidate, X)
    contradictions = []
    for i, a in enumerate(X):
        for j in range(i + 1, len(X)):
            b = X[j]
            if partition[i] == partition[j] and not (
                candidate.reidentify(a, b) and candidate.reidentify(b, a)
            ):
                contradictions.append((a, b))
    return contradictions


# ===========================================================================
# buildability_gate -- UNCHANGED per owner correction.
# ===========================================================================
def buildability_gate(candidate: CandidatePackage) -> GateResult:
    """Instantiates + runs its own probes on its own states without error?"""
    try:
        states = list(candidate.states())
    except Exception as e:  # noqa: BLE001 -- deliberately broad, we report and continue
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "states()", "error": repr(e)})
    if not states:
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "states()", "error": "empty state population"})

    try:
        probes = list(candidate.probes())
    except Exception as e:
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "probes()", "error": repr(e)})
    if not probes:
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "probes()", "error": "empty probe family"})

    apply_errors = []
    for p in probes:
        for s in states:
            try:
                candidate.apply(p, s)
            except Exception as e:
                apply_errors.append({"probe": repr(p), "state": repr(s), "error": repr(e)})
    if apply_errors:
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "apply(probe,state)", "errors": apply_errors})

    try:
        allowed_ops = list(candidate.carrier.allowed_ops)
    except Exception as e:
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "carrier.allowed_ops", "error": repr(e)})

    seq_errors = []
    if allowed_ops:
        for bracketing in ("left", "right"):
            try:
                candidate.apply_sequence(allowed_ops, states[0], bracketing=bracketing)
            except Exception as e:
                seq_errors.append({"bracketing": bracketing, "error": repr(e)})
    if seq_errors:
        return _result("buildability_gate", candidate, Verdict.FAIL,
                        {"stage": "apply_sequence", "errors": seq_errors})

    return _result("buildability_gate", candidate, Verdict.PASS, {
        "state_count": len(states), "probe_count": len(probes), "allowed_op_count": len(allowed_ops),
    })


# ===========================================================================
# probe_validity_gate -- positive-control check UNCHANGED per owner
# correction; negative-control check ADDED 2026-07-20 (audit finding F1:
# ControlSet.negative / expected_distinguishable=False were declared and
# populated by toys but had zero consumers in gates.py/mss.py -- dead
# scaffolding behind an over-promising docstring). Both checks now share
# one gate because both are about whether D itself has the right shape:
# separates what it must (positive), and does not separate what it must
# not (negative) -- a real leakage-fence control, not decorative.
# ===========================================================================
def probe_validity_gate(
    candidate: CandidatePackage,
    D: Optional[Sequence[Any]] = None,
    positive_controls: Optional[Sequence[Any]] = None,
    negative_controls: Optional[Sequence[Any]] = None,
) -> GateResult:
    """Does D SEPARATE the known positive controls, and does D AVOID
    falsely separating the known negative controls?

    Positive: if D fails to separate a declared positive control (the
    base_campaign restricting_outer_changes_inner:false pattern) -> HOLD
    "probe family has not demonstrated discrimination power". NOT a tie.

    Negative: if D DOES separate a declared negative control (an
    ablation/alias pair the candidate says must not be told apart) -> FAIL
    "D leaks a distinction the candidate declares must not exist" -- this
    is a leakage-fence violation (RATCHET_SPEC.md section 8), not
    insufficient evidence, so it is FAIL rather than HOLD, and it takes
    priority over a co-occurring positive-control HOLD (a definitive
    over-reach is reported, not masked by "not yet proven enough").
    """
    if D is None:
        D = list(candidate.probes())
    if positive_controls is None:
        positive_controls = candidate.controls().positive
    if negative_controls is None:
        negative_controls = candidate.controls().negative

    if not positive_controls and not negative_controls:
        return _result("probe_validity_gate", candidate, Verdict.UNRESOLVED,
                        {"reason": "no positive or negative controls declared -- cannot test discrimination power"})

    unseparated = []
    for cc in positive_controls:
        try:
            obs_a = [candidate.apply(p, cc.state_a) for p in D]
            obs_b = [candidate.apply(p, cc.state_b) for p in D]
        except Exception as e:
            return _result("probe_validity_gate", candidate, Verdict.FAIL,
                            {"reason": f"D raised while probing positive control {cc.label!r}: {e!r}"})
        if obs_a == obs_b:
            unseparated.append({
                "control": cc.label, "state_a": repr(cc.state_a), "state_b": repr(cc.state_b),
                "D": [repr(p) for p in D],
            })

    leaked = []
    for cc in negative_controls:
        try:
            obs_a = [candidate.apply(p, cc.state_a) for p in D]
            obs_b = [candidate.apply(p, cc.state_b) for p in D]
        except Exception as e:
            return _result("probe_validity_gate", candidate, Verdict.FAIL,
                            {"reason": f"D raised while probing negative control {cc.label!r}: {e!r}"})
        if obs_a != obs_b:
            leaked.append({
                "control": cc.label, "state_a": repr(cc.state_a), "state_b": repr(cc.state_b),
                "D": [repr(p) for p in D], "obs_a": repr(obs_a), "obs_b": repr(obs_b),
            })

    if leaked:
        return _result("probe_validity_gate", candidate, Verdict.FAIL, {
            "reason": ("D falsely separates a declared negative control (alias/ablation pair) -- "
                       "D leaks a distinction the candidate declares must not exist"),
            "leaked_negative_controls": leaked,
            "also_unseparated_positive_controls": unseparated,
        })

    if unseparated:
        return _result("probe_validity_gate", candidate, Verdict.HOLD, {
            "reason": "probe family has not demonstrated discrimination power",
            "unseparated_positive_controls": unseparated,
        })

    return _result("probe_validity_gate", candidate, Verdict.PASS, {
        "D": [repr(p) for p in D],
        "separated_positive_controls": [cc.label for cc in positive_controls],
        "checked_negative_controls": [cc.label for cc in negative_controls],
    })


# ===========================================================================
# IDENTITY_GATE -- THE NOMINALIST CORE. Executable form of a=a iff a~b.
# ELIGIBILITY control: a candidate whose partition fails this is INELIGIBLE
# for the coarseness comparison in mss.py (its partition is not honest).
# ===========================================================================
def IDENTITY_GATE(candidate: CandidatePackage, X: Optional[Sequence[State]] = None) -> GateResult:
    if X is None:
        X = list(candidate.states())
    if len(X) < 2:
        return _result("IDENTITY_GATE", candidate, Verdict.UNRESOLVED,
                        {"reason": "fewer than two states in X -- nothing to test"})

    try:
        probes = list(candidate.probes())
        fingerprints = [tuple(candidate.apply(p, x) for p in probes) for x in X]
    except Exception as e:
        return _result("IDENTITY_GATE", candidate, Verdict.FAIL,
                        {"stage": "probe fingerprint", "error": repr(e)})
    pi_probes = normalise_partition(fingerprints)

    try:
        pi_reidentify = induced_partition(candidate, X)
    except Exception as e:
        return _result("IDENTITY_GATE", candidate, Verdict.FAIL,
                        {"stage": "reidentify", "error": repr(e)})

    declared = candidate.declared_primitives()
    declared_flag = bool(set(declared) & {"identity", "equality"})

    equal = pi_probes == pi_reidentify
    contradictions = reidentify_internal_contradictions(candidate, X)
    # reidentify STRICTLY FINER than the probe partition == unearned distinction:
    reidentify_finer = (not equal) and partition_coarser(pi_probes, pi_reidentify)
    # reidentify STRICTLY COARSER than the probe partition == under-discriminating:
    reidentify_coarser = (not equal) and partition_coarser(pi_reidentify, pi_probes)

    base = {
        "declared_primitives": list(declared),
        "pi_probes": list(pi_probes),
        "pi_reidentify": list(pi_reidentify),
        "pi_probes_cells": len(set(pi_probes)),
        "pi_reidentify_cells": len(set(pi_reidentify)),
    }
    if contradictions:
        base["reidentify_internal_contradictions"] = [[repr(a), repr(b)] for a, b in contradictions]

    if equal and not declared_flag:
        if contradictions:
            base["reason"] = (
                "reidentify's transitive closure produced a partition block containing a pair "
                "reidentify itself denies -- reidentify is not an honest equivalence relation, "
                "even though the resulting partition happens to match the probe fingerprint partition"
            )
            return _result("IDENTITY_GATE", candidate, Verdict.FAIL, base)
        base["reason"] = (
            "reidentify agrees exactly with the probe-induced partition over X; "
            "a=a iff a~b holds under the current probe family"
        )
        return _result("IDENTITY_GATE", candidate, Verdict.PASS, base)

    if reidentify_finer or declared_flag:
        base["reason"] = (
            "reidentify distinguishes states no probe in the family separates, "
            "and/or the candidate declares raw identity/equality as an installed "
            "primitive -- unearned identity"
        )
        return _result("IDENTITY_GATE", candidate, Verdict.FAIL, base)

    if reidentify_coarser:
        base["reason"] = (
            "reidentify merges states the current probe family still separates -- "
            "new probe required, or reidentify is under-discriminating relative to "
            "observed evidence"
        )
        return _result("IDENTITY_GATE", candidate, Verdict.HOLD, base)

    base["reason"] = "reidentify and the probe-induced partition are incomparable (neither refines the other)"
    return _result("IDENTITY_GATE", candidate, Verdict.HOLD, base)


# ===========================================================================
# persistence_gate -- DEMAND GENERATOR. Pushes D through persist() and
# checks survivorship via the SAME partition kernel. Not a self-reported
# score: viability is derived mechanically from reidentify, never trusted
# from the candidate's own say-so.
# ===========================================================================
def persistence_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    perturbation: Any = "default_probe_perturbation",
    delay: int = 1,
    partial_access: Any = None,
    relabeled: bool = False,
) -> GateResult:
    try:
        continuation = {
            x: candidate.persist(x, perturbation=perturbation, delay=delay,
                                  partial_access=partial_access, relabeled=relabeled)
            for x in X
        }
    except Exception as e:
        return _result("persistence_gate", candidate, Verdict.FAIL,
                        {"stage": "persist()", "error": repr(e)})

    D_persistence = [(continuation[a], continuation[b]) for (a, b) in D]
    X_layer = list({*continuation.values()})
    if len(X_layer) < 2:
        return _result("persistence_gate", candidate, Verdict.UNRESOLVED,
                        {"reason": "fewer than two distinct continuation states -- nothing to test"})

    try:
        pi_layer = induced_partition(candidate, X_layer)
    except Exception as e:
        return _result("persistence_gate", candidate, Verdict.FAIL,
                        {"stage": "induced_partition(persisted)", "error": repr(e)})

    index = {x: i for i, x in enumerate(X_layer)}
    collapsed = collapsed_demand_edges(pi_layer, index, D_persistence)

    if collapsed:
        base_partition = induced_partition(candidate, X)
        buckets = collapsed_demand_edge_buckets(
            pi_layer, index, D_persistence, base_partition=base_partition,
            base_index={x: i for i, x in enumerate(X)}, base_pairs=D,
        )
        return _result("persistence_gate", candidate, Verdict.FAIL, {
            "reason": (
                "distinctions demanded by D do not survive the declared continuation "
                "(delay/perturbation/relabeling/partial-access)"
            ),
            "perturbation": repr(perturbation), "delay": delay,
            "partial_access": repr(partial_access), "relabeled": relabeled,
            "collapsed_persistence_demand_edges": [[repr(a), repr(b)] for (a, b) in collapsed],
            "D_persistence_size": len(D_persistence),
            "already_collapsed_at_base_edges": [[repr(a), repr(b)] for a, b in buckets["already_collapsed_at_base"]],
            "newly_collapsed_by_continuation_edges": [[repr(a), repr(b)] for a, b in buckets["newly_collapsed_by_continuation"]],
        })
    return _result("persistence_gate", candidate, Verdict.PASS, {
        "perturbation": repr(perturbation), "delay": delay,
        "D_persistence_size": len(D_persistence), "collapsed": 0,
    })


# ===========================================================================
# evolvability_gate -- DEMAND GENERATOR. Pushes D through evolve() and
# checks survivorship via the SAME partition kernel, plus a no-new-primitive
# check.
# ===========================================================================
def evolvability_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    new_constraint: Any = "probe_generic_extension",
) -> GateResult:
    try:
        extended = candidate.evolve(new_constraint)
    except Exception as e:
        return _result("evolvability_gate", candidate, Verdict.FAIL,
                        {"stage": "evolve()", "error": repr(e)})

    if extended is None:
        return _result("evolvability_gate", candidate, Verdict.FAIL, {
            "reason": (
                "evolve() returned None -- no admissible extension for the new "
                "constraint; every demanded distinction is treated as failed under "
                "this layer"
            ),
            "new_constraint": repr(new_constraint), "D_size": len(D),
        })
    if not isinstance(extended, CandidatePackage):
        return _result("evolvability_gate", candidate, Verdict.FAIL,
                        {"reason": "evolve() did not return a CandidatePackage", "got": repr(type(extended))})

    try:
        pi_extended = induced_partition(extended, X)
    except Exception as e:
        return _result("evolvability_gate", candidate, Verdict.FAIL,
                        {"stage": "induced_partition(extended)", "error": repr(e)})

    index = {x: i for i, x in enumerate(X)}
    collapsed = collapsed_demand_edges(pi_extended, index, D)
    if collapsed:
        base_partition = induced_partition(candidate, X)
        buckets = collapsed_demand_edge_buckets(
            pi_extended, index, D, base_partition=base_partition, base_index=index,
        )
        return _result("evolvability_gate", candidate, Verdict.FAIL, {
            "reason": "the evolved extension destroys a previously-live demanded distinction",
            "new_constraint": repr(new_constraint),
            "collapsed_evolvability_demand_edges": [[repr(a), repr(b)] for (a, b) in collapsed],
            "already_collapsed_at_base_edges": [[repr(a), repr(b)] for a, b in buckets["already_collapsed_at_base"]],
            "newly_collapsed_by_continuation_edges": [[repr(a), repr(b)] for a, b in buckets["newly_collapsed_by_continuation"]],
        })

    new_primitives = set(extended.declared_primitives()) - set(candidate.declared_primitives())
    if new_primitives:
        return _result("evolvability_gate", candidate, Verdict.FAIL, {
            "reason": "evolve() smuggled in a new declared primitive not present before -- ad hoc primitive",
            "new_primitives": sorted(new_primitives),
        })

    return _result("evolvability_gate", candidate, Verdict.PASS, {
        "new_constraint": repr(new_constraint), "D_size": len(D), "collapsed": 0,
    })


# ===========================================================================
# extension_gate -- DEMAND GENERATOR (whole-nest). Does the declared
# nest_interface recompute_digest match a fresh recompute of the induced
# partition?
# ===========================================================================
def extension_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
) -> GateResult:
    try:
        ni = candidate.nest_interface()
    except Exception as e:
        return _result("extension_gate", candidate, Verdict.FAIL,
                        {"stage": "nest_interface()", "error": repr(e)})

    if ni.inner is None and ni.outer is None and not ni.neighbors:
        return _result("extension_gate", candidate, Verdict.HOLD, {
            "reason": "no nest interface declared -- shell-local candidate, whole-nest recompute not applicable",
        })

    declared_digest = ni.inner.get("recompute_digest") if ni.inner is not None else None
    if declared_digest is None:
        return _result("extension_gate", candidate, Verdict.HOLD, {
            "reason": "nest interface declared but no recompute_digest present to check",
        })

    try:
        pi_fresh = induced_partition(candidate, X)
    except Exception as e:
        return _result("extension_gate", candidate, Verdict.FAIL,
                        {"stage": "induced_partition(fresh)", "error": repr(e)})
    fresh_digest = partition_digest(pi_fresh)

    if declared_digest != fresh_digest:
        return _result("extension_gate", candidate, Verdict.FAIL, {
            "reason": (
                "declared inner/nest recompute digest does not match a fresh recompute -- "
                "local result does NOT survive whole-nest recompute"
            ),
            "declared_digest": declared_digest, "fresh_digest": fresh_digest,
        })

    return _result("extension_gate", candidate, Verdict.PASS, {
        "reason": "declared nest recompute digest matches a fresh recompute of the induced partition",
        "digest": fresh_digest,
    })


# ===========================================================================
# order_honesty_gate -- OPERATIONAL, PAIRWISE order honesty over the finite
# carrier.allowed_ops surface. apply_sequence(..., bracketing="right") is
# used only for what the contract actually defines it to do: reverse order.
# This is not an associativity or bracket-honesty test.
# ===========================================================================
def order_honesty_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
) -> GateResult:
    """Never merge two observably noncommuting two-operation words.

    This finite gate is deliberately narrower than a deformation-word
    ledger: it checks every pair of advertised operations on every state in
    X. Probe fingerprints establish noncommutation; the partition kernel
    decides whether reidentify silently merges the two results.
    """
    try:
        ops = list(dict.fromkeys(candidate.carrier.allowed_ops))
        probes = list(candidate.probes())
    except Exception as e:
        return _result("order_honesty_gate", candidate, Verdict.FAIL, {
            "stage": "load operational surface", "error": repr(e),
        })
    if len(ops) < 2:
        return _result("order_honesty_gate", candidate, Verdict.UNRESOLVED, {
            "reason": "fewer than two allowed operations -- no order pair to test",
            "allowed_ops": [repr(op) for op in ops],
        })
    if not probes:
        return _result("order_honesty_gate", candidate, Verdict.UNRESOLVED, {
            "reason": "empty probe family -- operation-order results are not observable",
        })
    if not X:
        return _result("order_honesty_gate", candidate, Verdict.UNRESOLVED, {
            "reason": "empty X -- no state on which to test operation order",
        })

    silently_merged = []
    checked_words = 0
    observably_noncommuting = 0
    for i, op_a in enumerate(ops):
        for op_b in ops[i + 1:]:
            for state in X:
                try:
                    result_ab = candidate.apply_sequence((op_a, op_b), state, bracketing="left")
                    result_ba = candidate.apply_sequence((op_a, op_b), state, bracketing="right")
                    fingerprint_ab = tuple(candidate.apply(probe, result_ab) for probe in probes)
                    fingerprint_ba = tuple(candidate.apply(probe, result_ba) for probe in probes)
                    pi_results = induced_partition(candidate, (result_ab, result_ba))
                except Exception as e:
                    return _result("order_honesty_gate", candidate, Verdict.FAIL, {
                        "stage": "execute order pair",
                        "state": repr(state),
                        "order_ab": [repr(op_a), repr(op_b)],
                        "order_ba": [repr(op_b), repr(op_a)],
                        "error": repr(e),
                    })
                checked_words += 1
                pi_probes = normalise_partition((fingerprint_ab, fingerprint_ba))
                if pi_probes[0] != pi_probes[1]:
                    observably_noncommuting += 1
                if pi_probes[0] != pi_probes[1] and pi_results[0] == pi_results[1]:
                    silently_merged.append({
                        "state": repr(state),
                        "order_ab": [repr(op_a), repr(op_b)],
                        "order_ba": [repr(op_b), repr(op_a)],
                        "result_ab": repr(result_ab),
                        "result_ba": repr(result_ba),
                        "fingerprint_ab": repr(fingerprint_ab),
                        "fingerprint_ba": repr(fingerprint_ba),
                    })

    if silently_merged:
        return _result("order_honesty_gate", candidate, Verdict.FAIL, {
            "silently_merged_noncommuting_orders": silently_merged,
            "checked_order_words": checked_words,
            "observably_noncommuting_words": observably_noncommuting,
            "D_size": len(D),
        })
    return _result("order_honesty_gate", candidate, Verdict.PASS, {
        "checked_order_words": checked_words,
        "observably_noncommuting_words": observably_noncommuting,
        "silently_merged_noncommuting_orders": [],
        "D_size": len(D),
    })


# ===========================================================================
# distinction_adequacy_gate -- standalone demanded-distinction check. This
# exposes the distinction term separately without changing adequacy(), and
# uses the SAME induced partition / collapsed-demand-edge kernel as MSS.
# ===========================================================================
def distinction_adequacy_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
) -> GateResult:
    """Does the candidate's induced partition preserve every pair in D?"""
    if not D:
        return _result("distinction_adequacy_gate", candidate, Verdict.UNRESOLVED, {
            "reason": "empty D -- no demanded distinction to test",
        })
    index = {state: i for i, state in enumerate(X)}
    missing_edges = [
        (a, b) for a, b in D if a not in index or b not in index
    ]
    if missing_edges:
        return _result("distinction_adequacy_gate", candidate, Verdict.FAIL, {
            "demand_edges_outside_X": [[repr(a), repr(b)] for a, b in missing_edges],
        })
    try:
        partition = induced_partition(candidate, X)
        collapsed = collapsed_demand_edges(partition, index, D)
    except Exception as e:
        return _result("distinction_adequacy_gate", candidate, Verdict.FAIL, {
            "stage": "induced_partition/collapsed_demand_edges", "error": repr(e),
            "D": [[repr(a), repr(b)] for a, b in D],
        })
    if collapsed:
        return _result("distinction_adequacy_gate", candidate, Verdict.FAIL, {
            "collapsed_distinction_demand_edges": [
                [repr(a), repr(b)] for a, b in collapsed
            ],
            "partition": list(partition),
        })
    return _result("distinction_adequacy_gate", candidate, Verdict.PASS, {
        "D_size": len(D), "collapsed": 0, "partition": list(partition),
    })


# ===========================================================================
# operational_reidentification_gate -- wraps the existing finite
# reidentify_internal_contradictions helper as a standalone gate. It catches
# pairs joined by reidentify's closure that reidentify itself directly denies.
# ===========================================================================
def operational_reidentification_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
) -> GateResult:
    """Is reidentify internally consistent on its induced finite blocks?"""
    if len(X) < 2:
        return _result("operational_reidentification_gate", candidate, Verdict.UNRESOLVED, {
            "reason": "fewer than two states in X -- nothing to reidentify",
        })
    try:
        contradictions = reidentify_internal_contradictions(candidate, X)
    except Exception as e:
        return _result("operational_reidentification_gate", candidate, Verdict.FAIL, {
            "stage": "reidentify_internal_contradictions", "error": repr(e),
        })
    if contradictions:
        return _result("operational_reidentification_gate", candidate, Verdict.FAIL, {
            "reidentify_internal_contradictions": [
                [repr(a), repr(b)] for a, b in contradictions
            ],
            "D_size": len(D),
        })
    return _result("operational_reidentification_gate", candidate, Verdict.PASS, {
        "checked_state_count": len(X),
        "reidentify_internal_contradictions": [],
        "D_size": len(D),
    })


# ===========================================================================
# gauge_rejection_gate -- CONTRACT-BOUNDED relabeling gauge check. The v0
# contract exposes persist(relabeled=True), but no coordinate-change or
# conjugation API; this gate therefore certifies only the declared relabeling
# continuation and makes no broader gauge claim.
# ===========================================================================
def gauge_rejection_gate(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    perturbation: Any = None,
    delay: int = 0,
    partial_access: Any = None,
) -> GateResult:
    """A declared relabeling must not refine or coarsen the partition."""
    if len(X) < 2:
        return _result("gauge_rejection_gate", candidate, Verdict.UNRESOLVED, {
            "reason": "fewer than two states in X -- no relation to compare under relabeling",
        })
    try:
        base_partition = induced_partition(candidate, X)
        relabeled_states = [
            candidate.persist(
                state,
                perturbation=perturbation,
                delay=delay,
                partial_access=partial_access,
                relabeled=True,
            )
            for state in X
        ]
        relabeled_partition = induced_partition(candidate, relabeled_states)
        relabeled_preimages: dict[int, dict[int, list[int]]] = {}
        for position, (base_block, relabeled_block) in enumerate(
            zip(base_partition, relabeled_partition, strict=True)
        ):
            relabeled_preimages.setdefault(relabeled_block, {}).setdefault(
                base_block, []
            ).append(position)
        collisions = [
            {
                "relabeled_states": [
                    repr(relabeled_states[position])
                    for positions in base_blocks.values()
                    for position in positions
                ],
                "original_states": [
                    repr(X[position])
                    for positions in base_blocks.values()
                    for position in positions
                ],
                "original_partition_blocks": list(base_blocks),
                "relabeled_partition_block": relabeled_block,
            }
            for relabeled_block, base_blocks in relabeled_preimages.items()
            if len(base_blocks) > 1
        ]
        if collisions:
            return _result("gauge_rejection_gate", candidate, Verdict.HOLD, {
                "reason": (
                    "persist(relabeled=True) is not injective on the distinct "
                    "operational states of X, so the declared continuation is "
                    "not a relabeling"
                ),
                "colliding_relabelings": collisions,
                "relabeled_distinct_state_count": len(set(relabeled_partition)),
                "original_distinct_state_count": len(set(base_partition)),
                "D_size": len(D),
            })
    except Exception as e:
        return _result("gauge_rejection_gate", candidate, Verdict.FAIL, {
            "stage": "persist(relabeled=True)/induced_partition", "error": repr(e),
        })

    changed_relations = []
    for i, a in enumerate(X):
        for j in range(i + 1, len(X)):
            base_same = base_partition[i] == base_partition[j]
            relabeled_same = relabeled_partition[i] == relabeled_partition[j]
            if base_same != relabeled_same:
                changed_relations.append({
                    "original_pair": [repr(a), repr(X[j])],
                    "relabeled_pair": [
                        repr(relabeled_states[i]), repr(relabeled_states[j])
                    ],
                    "base_same_block": base_same,
                    "relabeled_same_block": relabeled_same,
                })
    if changed_relations:
        return _result("gauge_rejection_gate", candidate, Verdict.FAIL, {
            "relabeling_changed_partition_relations": changed_relations,
            "base_partition": list(base_partition),
            "relabeled_partition": list(relabeled_partition),
            "D_size": len(D),
        })
    return _result("gauge_rejection_gate", candidate, Verdict.PASS, {
        "checked_state_count": len(X),
        "base_partition": list(base_partition),
        "relabeled_partition": list(relabeled_partition),
        "changed_relations": 0,
        "D_size": len(D),
    })


# These named gates are intentionally absent, not unresolved gate stubs.
# Bracket honesty needs an associativity/bracketing surface beyond the contract's
# order-reversal-only apply_sequence API. Unique work needs deletion-with-refit,
# which in turn needs a settlement engine that this repository does not have.
ABSENT_GATES = {
    "bracket_honesty": (
        "not implemented: the contract has no genuine associativity/bracketing surface"
    ),
    "unique_work": (
        "not implemented: deletion-with-refit requires an unavailable settlement engine"
    ),
}


# ===========================================================================
# adequacy -- combines all six into one verdict.
# adequacy = Distinguish(IDENTITY_GATE) AND Persist(persistence_gate) AND
#            Evolve(evolvability_gate) AND Compose(buildability_gate) AND
#            Extend(extension_gate) AND PassControls(probe_validity_gate)
# ===========================================================================
def adequacy(
    candidate: CandidatePackage,
    X: Sequence[State],
    D: Sequence[tuple[State, State]],
    *,
    probe_D: Optional[Sequence[Any]] = None,
    positive_controls: Optional[Sequence[Any]] = None,
    negative_controls: Optional[Sequence[Any]] = None,
    perturbation: Any = "default_probe_perturbation",
    delay: int = 1,
    partial_access: Any = None,
    relabeled: bool = False,
    new_constraint: Any = "probe_generic_extension",
) -> GateResult:
    compose = buildability_gate(candidate)
    pass_controls = probe_validity_gate(candidate, D=probe_D, positive_controls=positive_controls,
                                         negative_controls=negative_controls)
    distinguish = IDENTITY_GATE(candidate, X)
    persist = persistence_gate(candidate, X, D, perturbation=perturbation, delay=delay,
                                partial_access=partial_access, relabeled=relabeled)
    evolve = evolvability_gate(candidate, X, D, new_constraint=new_constraint)
    extend = extension_gate(candidate, X, D)

    terms = {
        "Compose": compose, "PassControls": pass_controls, "Distinguish": distinguish,
        "Persist": persist, "Evolve": evolve, "Extend": extend,
    }
    verdicts = {k: v.verdict for k, v in terms.items()}

    if all(v == Verdict.PASS for v in verdicts.values()):
        overall = Verdict.PASS
    elif any(v == Verdict.FAIL for v in verdicts.values()):
        overall = Verdict.FAIL
    elif any(v == Verdict.HOLD for v in verdicts.values()):
        overall = Verdict.HOLD
    else:
        overall = Verdict.UNRESOLVED

    return _result("adequacy", candidate, overall, {
        "terms": {k: v.to_json() for k, v in terms.items()},
        "verdicts": {k: v.value for k, v in verdicts.items()},
    })
