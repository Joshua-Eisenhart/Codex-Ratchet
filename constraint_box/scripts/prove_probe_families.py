#!/usr/bin/env python3
"""Run the finite probe-family receipt for five bounded gate surfaces."""
from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

from constraintbox.probe_family import ProbeFamily, evaluate_probe_family

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/probe_families/probe_families_v1.json"
RECEIPT = ROOT / "receipts/probe_family_v1.json"


def _sympy(value: Any) -> str:
    import sympy
    if value["denominator"] == 0:
        return "zero_denominator"
    return "admitted" if sympy.Rational(value["numerator"], value["denominator"]) == sympy.Rational(str(value["expected"])) else "exact_mismatch"


def _fraction(value: Any) -> str:
    if value["denominator"] == 0:
        return "zero_denominator"
    return "admitted" if Fraction(value["numerator"], value["denominator"]) == Fraction(str(value["expected"])) else "exact_mismatch"


def _transition(value: Any) -> str:
    if value["from"] not in value["states"]:
        return "unknown_source"
    if value["from"] == value["to"]:
        return "self_loop"
    return "admitted" if value["to"] in value["states"] else "unknown_target"


def _transition_enum(value: Any) -> str:
    states = set(value["states"])
    if value["from"] not in states:
        return "unknown_source"
    if value["from"] == value["to"]:
        return "self_loop"
    return "admitted" if value["to"] in states else "unknown_target"


def _graph(value: Any) -> str:
    nodes, edges = set(value["nodes"]), [tuple(e) for e in value["edges"]]
    if value["entry"] not in nodes:
        return "entry_missing"
    outgoing = {node: [] for node in nodes}
    for source, target in edges:
        if source in outgoing:
            outgoing[source].append(target)
    visiting, visited = set(), set()
    def cyclic(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(cyclic(target) for source in [node] for target in outgoing[source]):
            return True
        visiting.remove(node); visited.add(node)
        return False
    if any(cyclic(node) for node in nodes):
        return "cycle"
    if any(a not in nodes or b not in nodes for a, b in edges):
        return "unknown_node"
    return "admitted"


def _graph_enum(value: Any) -> str:
    nodes, edges = set(value["nodes"]), [tuple(e) for e in value["edges"]]
    if value["entry"] not in nodes:
        return "entry_missing"
    reachable = {value["entry"]}
    changed = True
    while changed:
        changed = False
        for a, b in edges:
            if a in reachable and b not in reachable:
                reachable.add(b); changed = True
    if any(a not in nodes or b not in nodes for a, b in edges):
        return "unknown_node"
    visiting, visited = set(), set()
    outgoing = {node: [] for node in nodes}
    for source, target in edges:
        outgoing[source].append(target)
    def cyclic(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(cyclic(target) for target in outgoing[node]):
            return True
        visiting.remove(node); visited.add(node)
        return False
    if any(cyclic(node) for node in nodes):
        return "cycle"
    return "admitted" if reachable == nodes else "unreachable"


def _mini(value: Any) -> str:
    nodes, edges = set(value["nodes"]), [tuple(e) for e in value["edges"]]
    if value["entry"] not in nodes:
        return "entry_missing"
    outgoing = {n: [] for n in nodes}
    for a, b in edges:
        outgoing.setdefault(a, []).append(b)
    def reaches_terminal(start: str) -> bool:
        seen = set()
        pending = [start]
        while pending:
            node = pending.pop()
            if node not in nodes:
                return True
            if node in seen:
                continue
            seen.add(node)
            pending.extend(outgoing[node])
        return False
    return "admitted" if all(reaches_terminal(node) for node in nodes) else "dead_end"


def _mini_enum(value: Any) -> str:
    nodes, edges = set(value["nodes"]), [tuple(e) for e in value["edges"]]
    if value["entry"] not in nodes:
        return "entry_missing"
    outgoing = {n: [] for n in nodes}
    for a, b in edges:
        outgoing.setdefault(a, []).append(b)
    def reaches_terminal(start: str) -> bool:
        seen, pending = set(), [start]
        while pending:
            node = pending.pop()
            if node not in nodes:
                return True
            if node in seen:
                continue
            seen.add(node); pending.extend(outgoing[node])
        return False
    return "admitted" if all(reaches_terminal(node) for node in nodes) else "dead_end"


def _chain(value: Any) -> str:
    if not value["head"]:
        return "head_missing"
    previous = "0"
    for row in value["records"]:
        if row["previous"] != previous:
            return "chain_break"
        previous = row["line_hash"]
    return "admitted" if previous == value["head"] else "chain_break"


def _chain_raw(value: Any) -> str:
    # Independent representation of the same finite link relation.
    if value.get("head") == "":
        return "head_missing"
    expected = ["0"]
    expected.extend(row["line_hash"] for row in value["records"][:-1])
    actual = [row["previous"] for row in value["records"]]
    if actual != expected:
        return "chain_break"
    return "admitted" if value["records"][-1]["line_hash"] == value["head"] else "chain_break"


DECIDERS = {
    "cb:sympy-exact-gate": {"sympy": _sympy, "fraction": _fraction},
    "cb:maude-transition-gate": {"maude": _transition, "enumeration": _transition_enum},
    "cb:rustworkx-workflow-gate": {"rustworkx": _graph, "enumeration": _graph_enum},
    "mini_levos:construction-invariant": {"constructor": _mini, "enumeration": _mini_enum},
    "claimgate:chain-gate": {"ledger": _chain, "raw-bytes": _chain_raw},
}


def main() -> int:
    raw = json.loads(FIXTURE.read_text(encoding="utf-8"))
    results = []
    for item in raw["families"]:
        family = ProbeFamily.from_dict(item)
        results.append(evaluate_probe_family(family, DECIDERS[family.gate_id]))
    receipt = {"schema": "constraintbox.probe-family.v1", "fixture": str(FIXTURE.relative_to(ROOT)),
               "claim_ceiling": "finite partition and boundary evidence only; no universal property",
               "gates": results, "summary": {
                   "gates": len(results),
                   "non_constant": sum(r["non_constant"] for r in results),
                   "boundary_mapped": sum(r["boundary_mapped"] for r in results)}}
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
