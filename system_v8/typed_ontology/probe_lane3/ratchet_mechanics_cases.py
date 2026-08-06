#!/usr/bin/env python3
"""
ratchet_mechanics_cases.py -- PROBE LANE 3. Finite discrimination cases run
against the repo's live ratchet operator (ratchet_contract/mss.py:
pairwise_mss / frontier), the same operator system_v8/ratchet_bridge/
run_bridge.py imports.

This file MEASURES. It declares no verdict of its own. Every `*_verdict`
field below is read off a value returned by executed ratchet code
(MssResult.verdict.value, GateResult.verdict.value) or off a membership test
on a dict frontier() returned. Nothing here writes a literal verdict.

Six cases from the owner-diagram rules for the Ratchet (it compares COMPLETE
COMPATIBLE TOWERS; it receives only WITNESSED traces; if demand or probes do
not DISCRIMINATE the rivals it returns HOLD or plural survivors):

  T1  non-discriminating probes  (three sub-cases: a/b/c)
  T2  genuine coarsening
  T3  incomparable partitions
  T4  flat comparison, no nesting anywhere
  T5  unwitnessed continuation (total identity loss vs identity preserved)
  T6  demanded-pair handling, both conventions (a: must-separate merged,
      b: must-NOT-separate split)

classification: tool_lego_fit_probe   promotion_allowed: false
"""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from typing import Optional, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "ratchet_contract"))

from contract import (  # noqa: E402
    CandidatePackage,
    Carrier,
    ControlCase,
    ControlSet,
    NestInterface,
    State,
)
from gates import (  # noqa: E402
    IDENTITY_GATE,
    buildability_gate,
    evolvability_gate,
    extension_gate,
    induced_partition,
    persistence_gate,
    probe_validity_gate,
)
from mss import MssVerdict, frontier, pairwise_mss  # noqa: E402

# ---------------------------------------------------------------------------
# Observation surfaces. States are (raw_id, value, hidden). Externally
# supplied and shared, per the RATCHET_SPEC convention the toys follow.
# ---------------------------------------------------------------------------
X: tuple[State, ...] = (
    (0, "red", 0),
    (1, "blue", 1),
    (2, "red", 2),
    (3, "green", 3),
    (4, "yellow", 4),
)
D: tuple[tuple[State, State], ...] = (((0, "red", 0), (1, "blue", 1)),)

X6: tuple[State, ...] = (
    (0, "red", 0),
    (1, "blue", 1),
    (2, "green", 0),
    (3, "green", 1),
    (4, "yellow", 0),
)
D6: tuple[tuple[State, State], ...] = (((0, "red", 0), (1, "blue", 1)),)

_WARM = {"red", "yellow"}

# Readout ops. EVERY Tower instance implements EVERY op identically -- the
# only thing that varies between instances is which ops are DECLARED in
# probes(), plus the reidentify key. That separation is what T1c measures.
READOUTS = {
    "read_value": lambda raw, val, hid: val,
    "read_category": lambda raw, val, hid: "warm" if val in _WARM else "cool",
    "read_group_rg": lambda raw, val, hid: ("rg" if val in ("red", "green") else val),
    "read_group_gy": lambda raw, val, hid: ("gy" if val in ("green", "yellow") else val),
    "read_constant": lambda raw, val, hid: "K",
}


class Tower(CandidatePackage):
    """One flat single-layer candidate. No nesting is expressible here
    because the contract has no depth field to express it with -- see T4."""

    def __init__(
        self,
        label: str,
        *,
        declared_probes: Sequence[str],
        reid_ops: Sequence[str],
        hidden_rule: str = "identity",
        off_surface: str = "mirror",
        persist_mode: str = "identity",
        on_surface: Sequence[State] = X,
        primitives: Sequence[str] = (),
        controls_set: Optional[ControlSet] = None,
        evolvable: bool = True,
    ):
        self._label = label
        self._declared_probes = tuple(declared_probes)
        self._reid_ops = tuple(reid_ops)
        self._hidden_rule = hidden_rule
        self._off_surface = off_surface
        self._persist_mode = persist_mode
        self._on_surface = frozenset(on_surface)
        self._primitives = tuple(primitives)
        self._controls = controls_set if controls_set is not None else ControlSet()
        self._evolvable = evolvable

    @property
    def name(self) -> str:
        return self._label

    @property
    def carrier(self) -> Carrier:
        return Carrier(description=f"(raw_id,value,hidden) triples; {self._label}", allowed_ops=("noop",))

    def states(self):
        return tuple(sorted(self._on_surface))

    def probes(self):
        return self._declared_probes

    def apply(self, op, state):
        raw, val, hid = state[0], state[1], state[2]
        if op in READOUTS:
            return READOUTS[op](raw, val, hid)
        if op == "read_hidden":
            return (hid + 1) if self._hidden_rule == "identity" else (hid * 2 + 100)
        if op == "noop":
            return state
        raise ValueError(f"unknown op {op!r}")

    def _key(self, state) -> tuple:
        return tuple(self.apply(op, state) for op in self._reid_ops)

    def reidentify(self, record, current_state):
        if self._off_surface == "shatter":
            if record not in self._on_surface or current_state not in self._on_surface:
                # Total identity loss off the declared surface: nothing is the
                # same entity as anything. No trace links t to t+1.
                return False
        return self._key(record) == self._key(current_state)

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        if self._persist_mode == "timestamp":
            return (state[0], state[1], state[2], "t+1")
        return (state[0], state[1], state[2])

    def evolve(self, new_constraint):
        if not self._evolvable:
            return None
        return Tower(
            self._label + "_ext",
            declared_probes=self._declared_probes,
            reid_ops=self._reid_ops,
            hidden_rule=self._hidden_rule,
            off_surface=self._off_surface,
            persist_mode=self._persist_mode,
            on_surface=tuple(sorted(self._on_surface)),
            primitives=self._primitives,
            controls_set=self._controls,
            evolvable=self._evolvable,
        )

    def nest_interface(self):
        return NestInterface()  # no nest claim -- see T4

    def declared_primitives(self):
        return self._primitives

    def controls(self):
        return self._controls


def _p(candidate, surface) -> list[int]:
    return list(induced_partition(candidate, surface))


# ===========================================================================
CASES: dict[str, dict] = {}


def case_T1a():
    """Two towers differing ONLY in a coordinate no declared probe reads.

    Both declare probes=(read_value,), both reidentify on read_value. They
    differ only in what read_hidden returns -- an op neither declares and
    neither reidentifies on."""
    a = Tower("T1a_hidden_rule_A", declared_probes=("read_value",), reid_ops=("read_value",),
              hidden_rule="identity")
    b = Tower("T1a_hidden_rule_B", declared_probes=("read_value",), reid_ops=("read_value",),
              hidden_rule="doubled")
    hidden_differs = [
        {"state": list(x), "A_read_hidden": a.apply("read_hidden", x), "B_read_hidden": b.apply("read_hidden", x)}
        for x in X
    ]
    declared_reads_hidden = ("read_hidden" in a.probes()) or ("read_hidden" in b.probes())
    r = pairwise_mss(a, b, X, D)
    fr = frontier([a, b], X, D)
    return {
        "construction": "identical declared probes and identical reidentify key; differ only in read_hidden, undeclared by both",
        "any_declared_probe_reads_hidden": declared_reads_hidden,
        "hidden_coordinate_differs_on_every_state": all(h["A_read_hidden"] != h["B_read_hidden"] for h in hidden_differs),
        "hidden_readings": hidden_differs,
        "pi_A": _p(a, X), "pi_B": _p(b, X),
        "measured_verdict": r.verdict.value,
        "measured_reason": r.reasons.get("reason"),
        "frontier_survivors": fr["survivors"],
        "frontier_branch_count": len(fr["branches"]),
        "frontier_branch_members": [b_["members"] for b_ in fr["branches"]],
        "frontier_antichain": fr["antichain"],
        "frontier_dominated": fr["dominated"],
    }


def case_T1b():
    """One tower's reidentify reads the unprobed coordinate. This is the
    defect IDENTITY_GATE is built to catch."""
    a = Tower("T1b_reid_reads_hidden", declared_probes=("read_value",),
              reid_ops=("read_value", "read_hidden"))
    b = Tower("T1b_reid_probe_honest", declared_probes=("read_value",), reid_ops=("read_value",))
    ida = IDENTITY_GATE(a, X)
    r = pairwise_mss(a, b, X, D)
    return {
        "construction": "A.reidentify keys on read_hidden, which A does not declare as a probe",
        "identity_gate_A_verdict": ida.verdict.value,
        "identity_gate_A_reason": ida.reasons.get("reason"),
        "measured_verdict": r.verdict.value,
        "measured_stage": r.reasons.get("stage"),
    }


def case_T1c():
    """The probe family is CANDIDATE-SUPPLIED. Two towers with byte-identical
    apply() over every op, differing only in which ops they DECLARE in
    probes() and the matching reidentify granularity. Then the same pair
    re-measured with the union probe family declared instead."""
    coarse = Tower("T1c_declares_only_category", declared_probes=("read_category",),
                   reid_ops=("read_category",))
    fine = Tower("T1c_declares_value", declared_probes=("read_value",), reid_ops=("read_value",))

    every_op = tuple(READOUTS) + ("read_hidden", "noop")
    checks = 0
    disagreements = []
    for op in every_op:
        for x in X:
            checks += 1
            if coarse.apply(op, x) != fine.apply(op, x):
                disagreements.append({"op": op, "state": list(x)})

    r_self = pairwise_mss(coarse, fine, X, D)

    coarse_union = Tower("T1c_same_reid_union_probes",
                         declared_probes=("read_category", "read_value"),
                         reid_ops=("read_category",))
    fine_union = Tower("T1c_fine_union_probes",
                       declared_probes=("read_category", "read_value"),
                       reid_ops=("read_value",))
    id_self = IDENTITY_GATE(coarse, X)
    id_union = IDENTITY_GATE(coarse_union, X)
    r_union = pairwise_mss(coarse_union, fine_union, X, D)

    return {
        "construction": "identical apply() on every op; only probes() declaration and reidentify granularity differ",
        "apply_agreement_checks": checks,
        "apply_disagreements": disagreements,
        "reidentify_key_coarse": list(coarse._reid_ops),
        "reidentify_key_fine": list(fine._reid_ops),
        "self_declared_identity_gate_coarse_verdict": id_self.verdict.value,
        "self_declared_measured_verdict": r_self.verdict.value,
        "self_declared_measured_reason": r_self.reasons.get("reason"),
        "union_probe_identity_gate_coarse_verdict": id_union.verdict.value,
        "union_probe_identity_gate_coarse_reason": id_union.reasons.get("reason"),
        "union_probe_measured_verdict": r_union.verdict.value,
        "union_probe_measured_stage": r_union.reasons.get("stage"),
        "same_reidentify_two_verdicts": r_self.verdict.value != r_union.verdict.value,
    }


def case_T1d():
    """The maximal non-discriminating demand: D is EMPTY. Nothing is demanded,
    so no demand can discriminate the rivals. Owner rule says HOLD or plural
    survivors."""
    coarse = Tower("T1d_coarse", declared_probes=("read_category",), reid_ops=("read_category",))
    fine = Tower("T1d_fine", declared_probes=("read_value",), reid_ops=("read_value",))
    r_empty = pairwise_mss(coarse, fine, X, ())
    fr_empty = frontier([coarse, fine], X, ())
    r_thick = pairwise_mss(coarse, fine, X, (), thicken_persistence=True,
                           thicken_evolvability=True, thicken_wholenest=True)
    return {
        "construction": "D = () -- no demanded distinction at all",
        "demand_size": 0,
        "measured_verdict_empty_demand": r_empty.verdict.value,
        "measured_reason_empty_demand": r_empty.reasons.get("reason"),
        "measured_verdict_empty_demand_all_layers": r_thick.verdict.value,
        "frontier_antichain": fr_empty["antichain"],
        "frontier_dominated": fr_empty["dominated"],
        "frontier_purgatory": [p["candidate"] for p in fr_empty["purgatory"]],
    }


def case_T1e():
    """A caller-supplied demand naming states that are not on the observation
    surface -- an unwitnessed demand with no referent in X."""
    coarse = Tower("T1e_coarse", declared_probes=("read_category",), reid_ops=("read_category",))
    fine = Tower("T1e_fine", declared_probes=("read_value",), reid_ops=("read_value",))
    D_ghost = (((99, "ghost", 99), (98, "phantom", 98)),)
    out = {"construction": "D names two states absent from X"}
    try:
        r = pairwise_mss(coarse, fine, X, D_ghost)
        out["measured_verdict"] = r.verdict.value
        out["measured_stage"] = r.reasons.get("stage")
        out["raised"] = False
    except Exception as e:
        out["raised"] = True
        out["exception_type"] = type(e).__name__
        out["exception_repr"] = repr(e)[:200]
        out["carries_reasons_dict"] = False
    return out


def case_T2():
    """Genuine coarsening: B strictly coarser than A, every demanded pair in
    D still SEPARATED by both (repo convention: D = must-separate)."""
    fine = Tower("T2_fine_value", declared_probes=("read_value",), reid_ops=("read_value",))
    coarse = Tower("T2_coarse_category", declared_probes=("read_category",), reid_ops=("read_category",))
    pi_f, pi_c = _p(fine, X), _p(coarse, X)
    idx = {x: i for i, x in enumerate(X)}
    d_sep_fine = all(pi_f[idx[x]] != pi_f[idx[y]] for x, y in D)
    d_sep_coarse = all(pi_c[idx[x]] != pi_c[idx[y]] for x, y in D)
    r = pairwise_mss(fine, coarse, X, D)
    fr = frontier([fine, coarse], X, D)
    return {
        "construction": "A=exact-value granularity, B=warm/cool granularity; B strictly coarser",
        "pi_A_fine": pi_f, "pi_B_coarse": pi_c,
        "cells_A": len(set(pi_f)), "cells_B": len(set(pi_c)),
        "every_demanded_pair_separated_by_A": d_sep_fine,
        "every_demanded_pair_separated_by_B": d_sep_coarse,
        "measured_verdict": r.verdict.value,
        "measured_reason": r.reasons.get("reason"),
        "frontier_antichain": fr["antichain"],
        "frontier_dominated": fr["dominated"],
    }


def case_T3():
    """Two partitions, neither a coarsening of the other, both preserving D."""
    a = Tower("T3_group_red_green", declared_probes=("read_group_rg",), reid_ops=("read_group_rg",))
    b = Tower("T3_group_green_yellow", declared_probes=("read_group_gy",), reid_ops=("read_group_gy",))
    pi_a, pi_b = _p(a, X), _p(b, X)
    r = pairwise_mss(a, b, X, D)
    fr = frontier([a, b], X, D)
    return {
        "construction": "A merges {red,green}, B merges {green,yellow}; neither refines the other",
        "pi_A": pi_a, "pi_B": pi_b,
        "measured_verdict": r.verdict.value,
        "measured_reason": r.reasons.get("reason"),
        "frontier_antichain": fr["antichain"],
        "frontier_dominated": fr["dominated"],
        "antichain_size": len(fr["antichain"]),
    }


def case_T4():
    """Flat comparison. Neither tower declares any nest interface, so neither
    is a chain. Owner rule: the comparison unit is a NESTED CHAIN, so a flat
    single-layer comparison is an invalid comparison unit. Does the operator
    refuse it -- including when the whole-nest layer is explicitly requested?"""
    a = Tower("T4_flat_coarse", declared_probes=("read_category",), reid_ops=("read_category",))
    b = Tower("T4_flat_fine", declared_probes=("read_value",), reid_ops=("read_value",))
    ni_a, ni_b = a.nest_interface(), b.nest_interface()
    a_is_flat = ni_a.inner is None and ni_a.outer is None and not ni_a.neighbors
    b_is_flat = ni_b.inner is None and ni_b.outer is None and not ni_b.neighbors
    ext_a = extension_gate(a, X, D)

    r_base = pairwise_mss(a, b, X, D)
    r_nest_requested = pairwise_mss(a, b, X, D, thicken_wholenest=True)
    r_all_layers = pairwise_mss(a, b, X, D, thicken_persistence=True,
                                thicken_evolvability=True, thicken_wholenest=True)

    # Is there any depth / chain-length argument anywhere on the call surface?
    import inspect
    import mss as mss_mod
    sig_pairwise = list(inspect.signature(mss_mod.pairwise_mss).parameters)
    sig_frontier = list(inspect.signature(mss_mod.frontier).parameters)
    depth_words = ("depth", "chain", "rung", "layers", "tower", "nest_depth")
    depth_params = [p for p in sig_pairwise + sig_frontier if any(w in p for w in depth_words)]

    return {
        "construction": "both towers return NestInterface() -- no inner, no outer, no neighbours",
        "A_declares_no_nest": a_is_flat, "B_declares_no_nest": b_is_flat,
        "extension_gate_A_verdict": ext_a.verdict.value,
        "extension_gate_A_reason": ext_a.reasons.get("reason"),
        "measured_verdict_base": r_base.verdict.value,
        "measured_verdict_wholenest_requested": r_nest_requested.verdict.value,
        "measured_verdict_all_layers_requested": r_all_layers.verdict.value,
        "measured_reason_all_layers": r_all_layers.reasons.get("reason"),
        "pairwise_mss_parameters": sig_pairwise,
        "frontier_parameters": sig_frontier,
        "depth_or_chain_parameters_found": depth_params,
    }


def case_T5():
    """Unwitnessed continuation. Two towers identical on the surface X and
    identical in persist() -- they differ ONLY in whether any trace links a
    state at t to a state at t+1. `mirror` carries identity through the
    continuation; `shatter` denies that anything at t+1 is the same entity as
    anything else, i.e. supplies no witness at all."""
    mirror = Tower("T5_mirror_identity_carried", declared_probes=("read_category",),
                   reid_ops=("read_category",), off_surface="mirror", persist_mode="timestamp")
    shatter = Tower("T5_shatter_no_witness", declared_probes=("read_category",),
                    reid_ops=("read_category",), off_surface="shatter", persist_mode="timestamp")

    same_on_X = _p(mirror, X) == _p(shatter, X)
    id_m, id_s = IDENTITY_GATE(mirror, X), IDENTITY_GATE(shatter, X)
    persisted = [mirror.persist(x) for x in X]
    same_persist = persisted == [shatter.persist(x) for x in X]

    p_m = persistence_gate(mirror, X, D)
    p_s = persistence_gate(shatter, X, D)
    pi_layer_mirror = _p(mirror, persisted)
    pi_layer_shatter = _p(shatter, persisted)

    ev_s = evolvability_gate(shatter, X, D)
    ext_s = extension_gate(shatter, X, D)
    bld_s = buildability_gate(shatter)

    fine_honest = Tower("T5_fine_honest_rival", declared_probes=("read_value",),
                        reid_ops=("read_value",), off_surface="mirror", persist_mode="timestamp")
    fr = frontier([shatter, fine_honest], X, D, thicken_persistence=True,
                  thicken_evolvability=True, thicken_wholenest=True)

    return {
        "construction": "identical on X and identical persist(); differ only in whether any trace links t to t+1",
        "identical_partition_on_X": same_on_X,
        "identical_persist_outputs": same_persist,
        "identity_gate_mirror_verdict": id_m.verdict.value,
        "identity_gate_shatter_verdict": id_s.verdict.value,
        "pi_continuation_mirror": pi_layer_mirror,
        "pi_continuation_shatter": pi_layer_shatter,
        "continuation_cells_mirror": len(set(pi_layer_mirror)),
        "continuation_cells_shatter": len(set(pi_layer_shatter)),
        "persistence_gate_mirror_verdict": p_m.verdict.value,
        "persistence_gate_shatter_verdict": p_s.verdict.value,
        "persistence_gate_discriminated": p_m.verdict.value != p_s.verdict.value,
        "shatter_evolvability_verdict": ev_s.verdict.value,
        "shatter_extension_verdict": ext_s.verdict.value,
        "shatter_buildability_verdict": bld_s.verdict.value,
        "fully_thickened_frontier_antichain": fr["antichain"],
        "fully_thickened_frontier_purgatory": [p["candidate"] for p in fr["purgatory"]],
        "fully_thickened_frontier_dominated": fr["dominated"],
    }


def case_T5b():
    """Sharper form of T5: the shatterer against its OWN identity-carrying
    twin -- same declared probes, same reidentify key on X, same persist().
    The only difference is whether any trace links t to t+1."""
    mirror = Tower("T5b_mirror_twin", declared_probes=("read_category",), reid_ops=("read_category",),
                   off_surface="mirror", persist_mode="timestamp")
    shatter = Tower("T5b_shatter_twin", declared_probes=("read_category",), reid_ops=("read_category",),
                    off_surface="shatter", persist_mode="timestamp")
    r = pairwise_mss(mirror, shatter, X, D, thicken_persistence=True,
                     thicken_evolvability=True, thicken_wholenest=True)
    fr = frontier([mirror, shatter], X, D, thicken_persistence=True,
                  thicken_evolvability=True, thicken_wholenest=True)
    return {
        "construction": "identity-carrying twin vs identity-destroying twin; identical everywhere else",
        "measured_verdict": r.verdict.value,
        "measured_reason": r.reasons.get("reason"),
        "frontier_branch_count": len(fr["branches"]),
        "frontier_branch_members": [b_["members"] for b_ in fr["branches"]],
        "frontier_branch_digests": [b_["partition_digest"][:16] for b_ in fr["branches"]],
        "frontier_antichain": fr["antichain"],
        "frontier_purgatory": [p["candidate"] for p in fr["purgatory"]],
        "twins_re_merged_into_one_branch": len(fr["branches"]) == 1,
    }


def case_T6a():
    """Repo convention: D is a set of must-SEPARATE pairs; L_D > 0 means a
    demanded pair got MERGED. Such a candidate must be excluded."""
    collapser = Tower("T6a_merges_demanded_pair", declared_probes=("read_constant",),
                      reid_ops=("read_constant",))
    honest = Tower("T6a_separates_demanded_pair", declared_probes=("read_category",),
                   reid_ops=("read_category",))
    pi_c = _p(collapser, X)
    idx = {x: i for i, x in enumerate(X)}
    l_d = sum(1 for x, y in D if pi_c[idx[x]] == pi_c[idx[y]])
    r = pairwise_mss(collapser, honest, X, D)
    fr = frontier([collapser, honest], X, D)
    return {
        "construction": "collapser reidentifies on a constant probe, merging the demanded red/blue pair",
        "pi_collapser": pi_c,
        "L_D_collapser": l_d,
        "measured_verdict": r.verdict.value,
        "measured_stage": r.reasons.get("stage"),
        "frontier_survivors": fr["survivors"],
        "frontier_antichain": fr["antichain"],
        "frontier_purgatory": [{"candidate": p["candidate"], "failed_at": p["failed_at"]} for p in fr["purgatory"]],
        "collapser_excluded_from_antichain": "T6a_merges_demanded_pair" not in fr["antichain"],
    }


def case_T6b():
    """Task convention: a pair DEMANDED-MERGED (declared must-NOT-be-told-
    apart) that the candidate SPLITS. In this repo that demand is expressed
    as ControlSet.negative and enforced by probe_validity_gate. Is the
    splitter excluded from the frontier?"""
    neg = ControlSet(
        positive=(ControlCase("red_vs_blue", (0, "red", 0), (1, "blue", 1), True),),
        negative=(ControlCase("green_alias_must_not_split", (2, "green", 0), (3, "green", 1), False),),
    )
    splitter = Tower("T6b_splits_demanded_merge", declared_probes=("read_hidden",),
                     reid_ops=("read_hidden",), on_surface=X6, controls_set=neg)
    partner = Tower("T6b_incomparable_partner", declared_probes=("read_value",),
                    reid_ops=("read_value",), on_surface=X6, controls_set=neg)

    pi_s, pi_p = _p(splitter, X6), _p(partner, X6)
    idx = {x: i for i, x in enumerate(X6)}
    a_, b_ = (2, "green", 0), (3, "green", 1)
    splitter_splits_the_alias = pi_s[idx[a_]] != pi_s[idx[b_]]

    pv_s = probe_validity_gate(splitter)
    pv_p = probe_validity_gate(partner)
    id_s = IDENTITY_GATE(splitter, X6)

    r = pairwise_mss(splitter, partner, X6, D6)
    fr = frontier([splitter, partner], X6, D6)

    import inspect
    import mss as mss_mod
    mss_src = inspect.getsource(mss_mod)
    return {
        "construction": "splitter declares a negative control (green alias must not be told apart) and its declared probe read_hidden separates it",
        "pi_splitter": pi_s, "pi_partner": pi_p,
        "splitter_splits_the_demanded_merge": splitter_splits_the_alias,
        "probe_validity_gate_splitter_verdict": pv_s.verdict.value,
        "probe_validity_gate_splitter_reason": pv_s.reasons.get("reason"),
        "probe_validity_gate_partner_verdict": pv_p.verdict.value,
        "identity_gate_splitter_verdict": id_s.verdict.value,
        "measured_verdict": r.verdict.value,
        "measured_reason": r.reasons.get("reason"),
        "frontier_survivors": fr["survivors"],
        "frontier_antichain": fr["antichain"],
        "frontier_purgatory": [{"candidate": p["candidate"], "failed_at": p["failed_at"]} for p in fr["purgatory"]],
        "splitter_on_antichain": "T6b_splits_demanded_merge" in fr["antichain"],
        "mss_module_calls_probe_validity_gate": "probe_validity_gate" in mss_src,
        "mss_module_calls_buildability_gate": "buildability_gate" in mss_src,
    }


CASE_FNS = {
    "T1a_non_discriminating_unread_coordinate": case_T1a,
    "T1b_reidentify_reads_unprobed_coordinate": case_T1b,
    "T1c_candidate_supplied_probe_family": case_T1c,
    "T1d_empty_demand_set": case_T1d,
    "T1e_demand_off_surface": case_T1e,
    "T2_genuine_coarsening": case_T2,
    "T3_incomparable": case_T3,
    "T4_flat_comparison": case_T4,
    "T5_unwitnessed_continuation": case_T5,
    "T5b_witness_twins": case_T5b,
    "T6a_merges_must_separate_pair": case_T6a,
    "T6b_splits_must_merge_pair": case_T6b,
}


def main() -> int:
    results: dict[str, dict] = {}
    crashes: dict[str, str] = {}
    for key, fn in CASE_FNS.items():
        try:
            results[key] = fn()
        except Exception:
            crashes[key] = traceback.format_exc()

    verdict_tokens = sorted(v.value for v in MssVerdict)
    t1a = results.get("T1a_non_discriminating_unread_coordinate", {}).get("measured_verdict")
    t2 = results.get("T2_genuine_coarsening", {}).get("measured_verdict")

    out = {
        "probe": "ratchet_mechanics_cases",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "target_operator": str(REPO / "ratchet_contract" / "mss.py"),
        "target_functions": ["pairwise_mss", "frontier"],
        "declared_verdict_tokens": verdict_tokens,
        "observation_surface_X": [list(x) for x in X],
        "demand_set_D": [[list(a), list(b)] for a, b in D],
        "observation_surface_X6": [list(x) for x in X6],
        "T1_and_T2_same_verdict": (t1a is not None and t1a == t2),
        "cases": results,
        "crashes": crashes,
    }
    dest = HERE / "results" / "ratchet_mechanics_cases.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, sort_keys=False))
    print(json.dumps(out, indent=2, sort_keys=False))
    print(f"\nreceipt: {dest}", file=sys.stderr)
    return 1 if crashes else 0


if __name__ == "__main__":
    raise SystemExit(main())
