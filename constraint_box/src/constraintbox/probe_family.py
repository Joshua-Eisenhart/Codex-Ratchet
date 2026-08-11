"""Finite probe-family evaluation for deterministic gates.

This module records partitions, local boundary tests, and independent-decider
agreement.  It deliberately does not infer a universal property from a
sample: ``boundary_mapped`` is earned only when every observed refusal reason
has a flipped boundary pair and the declared deciders agree on every probe.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

ADMITTED = "admitted"
REASON_CODES = frozenset({ADMITTED})


class ProbeFamilyError(ValueError):
    """The family is malformed or violates the finite schema."""


@dataclass(frozen=True)
class Probe:
    probe_id: str
    input_ref: Any
    expected: str


@dataclass(frozen=True)
class BoundaryPair:
    probe_a: str
    probe_b: str
    differing_field: str
    expected_flip: bool = True


@dataclass(frozen=True)
class Decider:
    decider_id: str
    tool: str
    how_it_decides: str


@dataclass(frozen=True)
class ProbeFamily:
    gate_id: str
    probes: tuple[Probe, ...]
    boundary_pairs: tuple[BoundaryPair, ...]
    deciders: tuple[Decider, ...]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProbeFamily":
        if set(raw) != {"gate_id", "probes", "boundary_pairs", "deciders"}:
            raise ProbeFamilyError("probe family keys mismatch")
        gate_id = raw["gate_id"]
        if not isinstance(gate_id, str) or not gate_id:
            raise ProbeFamilyError("gate_id must be non-empty")
        probes = tuple(Probe(**item) for item in raw["probes"])
        ids = [p.probe_id for p in probes]
        if not ids or len(set(ids)) != len(ids):
            raise ProbeFamilyError("probe ids must be non-empty and unique")
        for probe in probes:
            if not isinstance(probe.expected, str) or not probe.expected:
                raise ProbeFamilyError("probe expected must be a reason code")
        pairs = tuple(BoundaryPair(**item) for item in raw["boundary_pairs"])
        if any(p.probe_a not in ids or p.probe_b not in ids for p in pairs):
            raise ProbeFamilyError("boundary pair references unknown probe")
        deciders = tuple(Decider(**item) for item in raw["deciders"])
        if len(deciders) < 2 or len({d.decider_id for d in deciders}) != len(deciders):
            raise ProbeFamilyError("at least two distinct deciders are required")
        return cls(gate_id, probes, pairs, deciders)

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "probes": [p.__dict__ for p in self.probes],
            "boundary_pairs": [p.__dict__ for p in self.boundary_pairs],
            "deciders": [d.__dict__ for d in self.deciders],
        }


def _paths(a: Any, b: Any, prefix: str = "") -> list[str]:
    if isinstance(a, dict) and isinstance(b, dict):
        keys = sorted(set(a) | set(b))
        out: list[str] = []
        for key in keys:
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in a or key not in b:
                out.append(path)
            else:
                out.extend(_paths(a[key], b[key], path))
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for index, (left, right) in enumerate(zip(a, b)):
            out.extend(_paths(left, right, f"{prefix}[{index}]"))
        return out
    return [] if a == b else [prefix or "$"]


def evaluate_probe_family(
    family: ProbeFamily,
    deciders: Mapping[str, Callable[[Any], str]],
) -> dict[str, Any]:
    """Evaluate one finite family; disagreement is retained, never swallowed."""
    missing = [d.decider_id for d in family.deciders if d.decider_id not in deciders]
    if missing:
        raise ProbeFamilyError(f"missing deciders: {missing}")
    verdicts: dict[str, dict[str, str]] = {}
    for probe in family.probes:
        verdicts[probe.probe_id] = {
            d.decider_id: deciders[d.decider_id](probe.input_ref)
            for d in family.deciders
        }
    primary = family.deciders[0].decider_id
    expected_mismatches = [
        {"probe_id": probe.probe_id, "expected": probe.expected,
         "actual": verdicts[probe.probe_id][primary]}
        for probe in family.probes
        if probe.expected != verdicts[probe.probe_id][primary]
    ]
    partition: dict[str, Any] = {"admitted": [], "refused": {}}
    for probe in family.probes:
        verdict = verdicts[probe.probe_id][primary]
        if verdict == ADMITTED:
            partition["admitted"].append(probe.probe_id)
        else:
            partition["refused"].setdefault(verdict, []).append(probe.probe_id)
    quotient = []
    for verdict, members in [(ADMITTED, partition["admitted"]), *sorted(partition["refused"].items())]:
        if members:
            quotient.append({"verdict": verdict, "probes": members})
    boundary = []
    for pair in family.boundary_pairs:
        a, b = next(p for p in family.probes if p.probe_id == pair.probe_a), next(
            p for p in family.probes if p.probe_id == pair.probe_b
        )
        fields = _paths(a.input_ref, b.input_ref)
        va, vb = verdicts[a.probe_id][primary], verdicts[b.probe_id][primary]
        flipped = va != vb
        boundary.append({**pair.__dict__, "actual_differing_fields": fields,
                         "single_field": len(fields) == 1,
                         "flipped": flipped, "side_a": va, "side_b": vb,
                         "passes": flipped == pair.expected_flip and fields == [pair.differing_field]})
    disagreements = []
    agreement = []
    for probe in family.probes:
        row = {"probe_id": probe.probe_id, "deciders": verdicts[probe.probe_id]}
        row["agree"] = len(set(verdicts[probe.probe_id].values())) == 1
        agreement.append(row)
        if not row["agree"]:
            disagreements.append(row)
    reasons = sorted(set(partition["refused"]))
    covered_reasons = sorted({r for r in reasons if any(
        p["passes"] and p["side_a"] == ADMITTED and p["side_b"] == r or
        p["passes"] and p["side_b"] == ADMITTED and p["side_a"] == r
        for p in boundary)})
    non_constant = bool(partition["admitted"]) and bool(partition["refused"])
    boundary_mapped = (non_constant and set(covered_reasons) == set(reasons)
                       and all(p["passes"] for p in boundary)
                       and not disagreements and not expected_mismatches)
    return {"gate_id": family.gate_id, "partition": partition, "quotient": quotient,
            "boundary": boundary, "agreement": agreement,
            "disagreements": disagreements, "expected_mismatches": expected_mismatches,
            "coverage": {
                "probes": len(family.probes), "admitted": len(partition["admitted"]),
                "refused": sum(map(len, partition["refused"].values())),
                "reason_codes_exercised": len(reasons),
                "boundary_pairs": len(boundary), "deciders": len(family.deciders)},
            "non_constant": non_constant, "boundary_mapped": boundary_mapped,
            "unmapped_reason_codes": sorted(set(reasons) - set(covered_reasons))}
