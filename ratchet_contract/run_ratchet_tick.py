#!/usr/bin/env python3
"""Run the bounded two-tick frontier/MSS advancement contract.

This file copies (rather than imports) ``BridgeCandidateAsPackage`` and the
``build_deck`` pattern from ``fuel_sims/practice_run.py``.  Importing that
module would import its QIT carrier, which is intentionally outside this
stdlib-only classical/countermodel/ablation run.
"""
from __future__ import annotations

import itertools
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional, Sequence

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
FUEL_SIMS = HERE / "fuel_sims"
BRIDGE = HERE / "bridge_validation"
for path in (HERE, FUEL_SIMS, BRIDGE):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from contract import CandidatePackage, Carrier, ControlCase, ControlSet, NestInterface
from gates import (IDENTITY_GATE, adequacy, buildability_gate, evolvability_gate,
                   extension_gate, persistence_gate, probe_validity_gate)
from mss import frontier, pairwise_mss
from bridge_interface import Action, CandidateBridgeInterface, Outcome, history_point, hp_json, replay


def fail(step: str, error: Exception | str) -> None:
    print(f"run_ratchet_tick: {step} failed: {error}", file=sys.stderr)
    raise RuntimeError(f"{step}: {error}")


def _words_upto(alphabet: Sequence[Action], horizon: int) -> tuple[tuple[Action, ...], ...]:
    words = [()]
    for width in range(1, horizon + 1):
        words.extend(tuple(word) for word in itertools.product(alphabet, repeat=width))
    return tuple(words)


class BridgeCandidateAsPackage(CandidatePackage):
    """Verbatim behavioural adapter from practice_run, minus QIT imports."""
    def __init__(self, bridge_candidate: CandidateBridgeInterface, X: Sequence[tuple], *, horizon: int,
                 action_alphabet: Optional[Sequence[Action]] = None, name: Optional[str] = None):
        self._bridge = bridge_candidate
        self._X = tuple(X)
        self._horizon = horizon
        self._alphabet = tuple(action_alphabet or bridge_candidate.action_alphabet())
        self._words = _words_upto(self._alphabet, horizon)
        self._name = name or f"{bridge_candidate.name}__as_package_h{horizon}"
        self._memo: dict = {}

    @property
    def name(self) -> str: return self._name

    @property
    def carrier(self) -> Carrier:
        return Carrier(f"bridge-candidate adapter over {self._bridge.name}, horizon={self._horizon}",
                       tuple(("advance", (action,)) for action in self._alphabet))

    def states(self): return self._X
    def probes(self): return tuple(("peek", word) for word in self._words)

    def _trace(self, x: tuple, word: tuple[Action, ...]) -> tuple[Outcome, ...]:
        root, prefix = x
        state = replay(self._bridge, root, prefix, memo=self._memo)
        trace = []
        for action in word:
            state, outcome = self._bridge.step_C(state, action, None)
            trace.append(outcome)
        return tuple(trace)

    def apply(self, op, state):
        kind, word = op
        if kind == "peek": return self._trace(state, word)
        if kind == "advance":
            root, prefix = state
            return (root, prefix + word)
        raise ValueError(f"unknown op kind {kind!r}")

    def reidentify(self, record, current_state) -> bool:
        return all(self._trace(record, word) == self._trace(current_state, word) for word in self._words)

    def persist(self, state, *, perturbation=None, delay=0, partial_access=None, relabeled=False):
        root, prefix = state
        extra = ["delay_short"] * (delay or 0)
        if perturbation: extra.append("perturb_small_rx0")
        if partial_access: extra.append("restrict_trace_out_qubit1")
        if relabeled: extra.append("renest_swap01")
        return (root, prefix + tuple(extra))

    def evolve(self, new_constraint):
        name = new_constraint if new_constraint in ("trace_preserving", "require_purity") else "require_purity"
        token = ("extend_under_constraint", name)
        return BridgeCandidateAsPackage(self._bridge, tuple((root, prefix + (token,)) for root, prefix in self._X),
                                        horizon=self._horizon, action_alphabet=self._alphabet,
                                        name=f"{self._name}__evolved_{name}")

    def nest_interface(self): return NestInterface()
    def declared_primitives(self):
        # CandidateBridgeInterface does not require this optional declaration;
        # the lookup replay inherits its public trace behaviour but declares no
        # additional raw primitive when it omits the hook.
        hook = getattr(self._bridge, "declared_primitives", None)
        return tuple(hook()) if hook is not None else ()
    def controls(self):
        roots_seen = {root for root, _ in self._X}
        positive = ()
        if "root_00" in roots_seen and "root_bell" in roots_seen:
            positive = (ControlCase("root_00_vs_root_bell", history_point("root_00"), history_point("root_bell"), True),)
        negative = (ControlCase("trace_preserving_is_a_genuine_noop", history_point("root_00"),
                                history_point("root_00", (("extend_under_constraint", "trace_preserving"),)), False),)
        return ControlSet(positive=positive, negative=negative)


def build_deck():
    hp = history_point
    named = {
        "root_00": hp("root_00"), "root_bell": hp("root_bell"),
        "root_plus0": hp("root_plus0"), "root_mixed": hp("root_mixed"),
        "root_00_reprepared_bell": hp("root_00", ("prepare_bell",)),
        "root_plus0_couple_inner_outer": hp("root_plus0", ("couple_inner_outer",)),
        "root_plus0_couple_neighbor_neighbor": hp("root_plus0", ("couple_neighbor_neighbor",)),
        "root_plus0_order_H0_then_CNOT01": hp("root_plus0", (("ordered_compose", ("H0", "CNOT01")),)),
        "root_plus0_order_CNOT01_then_H0": hp("root_plus0", (("ordered_compose", ("CNOT01", "H0")),)),
        "root_00_delay_long": hp("root_00", ("delay_long",)),
        "root_bell_delay_long": hp("root_bell", ("delay_long",)),
    }
    demands = (
        (named["root_00"], named["root_bell"]),
        (named["root_00"], named["root_00_reprepared_bell"]),
        (named["root_plus0_order_H0_then_CNOT01"], named["root_plus0_order_CNOT01_then_H0"]),
        (named["root_plus0_couple_inner_outer"], named["root_plus0_couple_neighbor_neighbor"]),
    )
    return named, tuple(named.values()), demands


def point_json(point: tuple) -> dict: return hp_json(point)
def pair_json(pair: tuple[tuple, tuple]) -> list[dict]: return [point_json(pair[0]), point_json(pair[1])]


def run_kernel(candidates, X, D) -> dict:
    packages = [BridgeCandidateAsPackage(candidate, X, horizon=1, name=f"{candidate.name}_pkg") for candidate in candidates]
    gates = {}
    for package in packages:
        # probe_validity's D is an operation family, so it deliberately uses probes(), not state-pair demands.
        gates[package.name] = {
            "buildability_gate": buildability_gate(package).to_json(),
            "probe_validity_gate": probe_validity_gate(package).to_json(),
            "IDENTITY_GATE": IDENTITY_GATE(package, X).to_json(),
            "persistence_gate": persistence_gate(package, X, D).to_json(),
            "evolvability_gate": evolvability_gate(package, X, D).to_json(),
            "extension_gate": extension_gate(package, X, D).to_json(),
            "adequacy": adequacy(package, X, D).to_json(),
        }
    pairwise = [pairwise_mss(a, b, X, D).to_json() for a, b in itertools.combinations(packages, 2)]
    result = frontier(packages, X, D)
    return {"x_size": len(X), "d_size": len(D), "demand_pairs": [pair_json(pair) for pair in D],
            "gate_verdicts": gates, "pairwise_mss_base_no_thickening": pairwise,
            "frontier": result}


def frontier_signature(kernel: dict) -> dict:
    fr = kernel["frontier"]
    return {"survivors": sorted(fr["survivors"]), "antichain": sorted(fr["antichain"]),
            "purgatory": sorted((item["candidate"], item["failed_at"], json.dumps(item["reason"], sort_keys=True))
                               for item in fr["purgatory"])}


def frontier_diff(before: dict, after: dict) -> list[dict]:
    left, right = frontier_signature(before), frontier_signature(after)
    out = []
    for field in ("survivors", "antichain", "purgatory"):
        if left[field] != right[field]: out.append({"field": field, "tick0": left[field], "tick1": right[field]})
    return out


def joint_is_nonproduct(table: dict[str, int]) -> bool:
    total = sum(table.values())
    a = {"0": table["00"] + table["01"], "1": table["10"] + table["11"]}
    b = {"0": table["00"] + table["10"], "1": table["01"] + table["11"]}
    return any(table[token] * total != a[token[0]] * b[token[1]] for token in ("00", "01", "10", "11"))


def d2_thickening() -> tuple[list[dict], tuple[tuple, ...], tuple[tuple, ...]]:
    path = HERE / "demand_batteries" / "results" / "d2_battery_classical.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    edges = raw.get("edges")
    if not isinstance(edges, list) or len(edges) != 6: fail("D2 load", "expected an edges list of length 6")
    cuts = [edge for edge in edges if str(edge.get("name", "")).startswith("cut_change_ab")]
    if len(cuts) != 4: fail("D2 dedup", "expected four cut_change_ab edges")
    # The four cut_change_ab.. edges are byte-identical readings; one substantive cut witness avoids count inflation.
    canonical = json.dumps({"table_a": cuts[0].get("table_a"), "table_b": cuts[0].get("table_b")}, sort_keys=True, separators=(",", ":"))
    if any(json.dumps({"table_a": edge.get("table_a"), "table_b": edge.get("table_b")}, sort_keys=True, separators=(",", ":")) != canonical for edge in cuts[1:]):
        fail("D2 dedup", "cut_change_ab tables are not literally equal across all four edges")
    joints = [edge for edge in edges if str(edge.get("name", "")).startswith("joint_vs_marginal_")]
    if len(joints) != 2: fail("D2 load", "expected two joint_vs_marginal edges")
    for edge in joints:
        if not edge.get("differs") or not joint_is_nonproduct(edge["table_a"]):
            fail("D2 joint translation", f"edge is not a genuinely non-product witness: {edge.get('name')}")
    cut_pair = (history_point("root_00"), history_point("root_00", ("perturb_small_rx0",)))
    # Product tables are not carrier states.  The auditable proxy compares the joint-reading address to its native
    # trace-restriction address, whose intended observable role is removal of the joint correlation.
    bell0_pair = (history_point("root_bell"), history_point("root_bell", ("restrict_trace_out_qubit1",)))
    # The lookup carrier is deliberately bounded to one-address actions, so
    # cut1 uses its one-action Bell address against an already-present product
    # preparation instead of manufacturing a two-action product-table state.
    bell1_pair = (history_point("root_bell", ("perturb_small_rx0",)), history_point("root_00"))
    translated = [
        {"name": cuts[0]["name"], "source_edges_deduplicated": [edge["name"] for edge in cuts],
         "translation_choice": "cut-0 versus native cut-1 history address", "demand_pair": pair_json(cut_pair)},
        {"name": joints[0]["name"], "translation_choice": "joint root_bell/cut0 address versus native correlation-removing restrict_trace_out_qubit1 proxy address; not a synthetic product state", "demand_pair": pair_json(bell0_pair)},
        {"name": joints[1]["name"], "translation_choice": "one-action root_bell/cut1 joint address versus existing root_00 product-preparation proxy; the D2 product table is not manufactured as a HistoryPoint", "demand_pair": pair_json(bell1_pair)},
    ]
    return translated, (cut_pair, bell0_pair, bell1_pair), tuple({point for pair in (cut_pair, bell0_pair, bell1_pair) for point in pair})


def invoke_floor(d_size: int, purgatory_count: int) -> dict:
    results = HERE / "results"; results.mkdir(parents=True, exist_ok=True)
    receipt = results / "ratchet_tick_floor_receipt.json"
    receipt.write_text(json.dumps({"floor_claims": [{"key": "ratchet_tick.demand_count", "value": d_size, "direction": "higher_is_better"}, {"key": "ratchet_tick.purgatory_count", "value": purgatory_count, "direction": "lower_is_better"}]}, indent=2) + "\n", encoding="utf-8")
    store = results / "ratchet_tick_floors.json"
    command = [sys.executable, str(REPO_ROOT / "claimgate_plugin" / "ratchet_floor.py"), "admit", str(receipt), "--store", str(store)]
    try:
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        parsed: Any
        try: parsed = json.loads(completed.stdout)
        except json.JSONDecodeError: parsed = completed.stdout
        return {"invoked": True, "result_path": str(store), "stdout_or_result": parsed,
                "error": None if completed.returncode in (0, 1) else (completed.stderr or f"exit {completed.returncode}"),
                "exit_code": completed.returncode}
    except Exception as exc:
        return {"invoked": True, "result_path": str(store), "stdout_or_result": None, "error": repr(exc)}


def main() -> int:
    try:
        try:
            from candidate_classical_exec import ClassicalRelationalExecCandidate
        except Exception as exc: fail("import ClassicalRelationalExecCandidate", exc)
        try:
            from candidate_countermodel_exec import CountermodelLookupReplayExecCandidate
        except Exception as exc: fail("import CountermodelLookupReplayExecCandidate", exc)
        try:
            from candidate_ablation_exec import AblationFlattenedExecCandidate
        except Exception as exc: fail("import AblationFlattenedExecCandidate", exc)
        candidates = [ClassicalRelationalExecCandidate(), CountermodelLookupReplayExecCandidate(), AblationFlattenedExecCandidate()]
        _named, X0, D0 = build_deck()
        tick0 = run_kernel(candidates, X0, D0)
        translated, d2_pairs, d2_points = d2_thickening()
        X1, D1 = tuple(dict.fromkeys((*X0, *d2_points))), tuple(dict.fromkeys((*D0, *d2_pairs)))
        if not (len(D1) > len(D0) and set(D0).issubset(D1)): fail("D1 monotonicity", "D1 did not strictly extend D0")
        tick1 = run_kernel(candidates, X1, D1)
        # Three fresh, one-action root_mixed pairs are outside the four declared D2 witnesses.
        # Keeping prefixes at one action also respects the countermodel's explicitly bounded replay table.
        junk_pairs = (
            (history_point("root_mixed", ("prepare_00",)), history_point("root_mixed", ("prepare_bell",))),
            (history_point("root_mixed", ("prepare_plus0",)), history_point("root_mixed", ("restrict_trace_out_qubit1",))),
            (history_point("root_mixed", (("ordered_compose", ("H0", "CNOT01")),)), history_point("root_mixed", ("perturb_small_rx0",))),
        )
        Xjunk = tuple(dict.fromkeys((*X0, *(point for pair in junk_pairs for point in pair))))
        Djunk = tuple(dict.fromkeys((*D0, *junk_pairs)))
        junk_run = run_kernel(candidates, Xjunk, Djunk)
        control_diff = frontier_diff(tick0, junk_run)
        anti = "PASS" if not control_diff else "FAILED"
        moved_diff = frontier_diff(tick0, tick1)
        attribution = []
        for difference in moved_diff:
            trials = []
            reverting = []
            for index, pair in enumerate(d2_pairs):
                trial = run_kernel(candidates, X1, tuple(item for item in D1 if item != pair))
                trial_diff = frontier_diff(tick0, trial)
                trials.append({"removed_edge": translated[index]["name"], "frontier_diff_from_tick0": trial_diff})
                if not trial_diff: reverting.append(translated[index]["name"])
            attribution.append({"difference": difference, "responsible_edges": reverting,
                                "attribution": "unambiguous" if len(reverting) == 1 else "ambiguous attribution",
                                "single_pair_removal_reruns": trials})
        moved = bool(moved_diff)
        ambiguous = any(item["attribution"] == "ambiguous attribution" for item in attribution)
        old_purgatory_names = {item["candidate"] for item in tick0["frontier"]["purgatory"]}
        new_live_names = set(tick1["frontier"]["survivors"]) | set(tick1["frontier"]["antichain"])
        named_resurrection = old_purgatory_names & new_live_names
        attributed_edges = {edge for item in attribution for edge in item["responsible_edges"]}
        no_resurrection = not named_resurrection or (not ambiguous and bool(attributed_edges))
        if anti == "FAILED": verdict = "CONTROL_FAILED"
        elif not moved: verdict = "STALLED"
        elif not ambiguous: verdict = "RATCHETED"
        else: verdict = "STALLED"
        floor = invoke_floor(len(D1), len(tick1["frontier"]["purgatory"]))
        output = {"schema_version": "ratchet-tick/0.1", "classification": "tool_lego_fit_probe", "promotion_allowed": False,
                  "tick0": tick0, "tick1": tick1, "junk_run": junk_run, "translated_d2_edges": translated,
                  "frontier_moved": moved, "movement_attribution": attribution, "d_monotone": True,
                  "no_unearned_resurrection": no_resurrection, "anti_stall_control": anti,
                  "anti_stall_control_diff": None if anti == "PASS" else {"differences": control_diff}, "verdict": verdict,
                  "floor_seal": floor}
        results = HERE / "results"; results.mkdir(parents=True, exist_ok=True)
        (results / "ratchet_tick.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    except Exception as exc:
        print(f"run_ratchet_tick: hard failure: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
