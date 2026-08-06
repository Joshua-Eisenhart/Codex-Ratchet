#!/usr/bin/env python3
"""Rough finite i,j,k entropic-geometry and Hopfield prototype.

This is an exploratory object, not a proof runner.  It deliberately keeps
Axis 0 as a field of component readouts over finite shell coordinates
``(i, j, k)`` rather than collapsing the object to one entropy scalar.

The prototype combines four small mechanisms:

* a finite fuzzy shell complex over ``i`` and toroidal ``j,k`` coordinates;
* a finite Feynman-like sum over retained ``open``/``bind`` histories;
* a bracket seam produced by explicit intermediate settlement/compression;
* a deterministic Hopfield/QCA update whose recurrent classes provide rough
  attractor and subbasin observations.

Every number is a model readout.  Nothing here is a physical, CR, or formal
admission claim.
"""

from __future__ import annotations

import argparse
import cmath
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


N = 4
SHELLS = 3
PATH_DEPTH = 3
BETA = 0.35
SIGMA = 1.25


def nodes() -> list[tuple[int, int, int]]:
    return [(i, j, k) for i in range(SHELLS) for j in range(N) for k in range(N)]


def torus_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    di = abs(left[0] - right[0])
    dj = min(abs(left[1] - right[1]), N - abs(left[1] - right[1]))
    dk = min(abs(left[2] - right[2]), N - abs(left[2] - right[2]))
    return math.sqrt(di * di + dj * dj + dk * dk)


def fuzzy_shell(node: tuple[int, int, int]) -> dict[tuple[int, int, int], float]:
    raw = {
        other: math.exp(-0.5 * (torus_distance(node, other) / SIGMA) ** 2)
        for other in nodes()
    }
    total = sum(raw.values())
    return {other: value / total for other, value in raw.items()}


def open_step(node: tuple[int, int, int]) -> tuple[int, int, int]:
    i, j, k = node
    return ((i + 1) % SHELLS, (j + 1 + i) % N, (k + i) % N)


def bind_step(node: tuple[int, int, int]) -> tuple[int, int, int]:
    i, j, k = node
    return (i, j, (k + j + 1) % N)


def apply_word(node: tuple[int, int, int], word: str) -> tuple[int, int, int]:
    current = node
    for operation in word:
        current = open_step(current) if operation == "O" else bind_step(current)
    return current


def bracket_left(node: tuple[int, int, int]) -> tuple[int, int, int]:
    """(O B) O with a retained settlement seam after the first pair."""

    current = bind_step(open_step(node))
    i, j, k = current
    return open_step((i, j, k % 2))


def bracket_right(node: tuple[int, int, int]) -> tuple[int, int, int]:
    """O (B O) with a different explicit intermediate compression."""

    current = open_step(bind_step(node))
    i, j, k = current
    return bind_step((i, j % 2, k))


def action_and_phase(node: tuple[int, int, int], word: str, chirality: int) -> tuple[float, float, tuple[int, int, int]]:
    current = node
    action = 0.0
    phase = 0.0
    for depth, operation in enumerate(word, start=1):
        current = open_step(current) if operation == "O" else bind_step(current)
        i, j, k = current
        # The action is a finite seam/boundary cost; the phase is an oriented
        # record.  Neither is asserted to be a physical action or flux.
        action += 1.0 + (0.25 if operation == "B" else 0.0) + 0.05 * i
        phase += chirality * 2.0 * math.pi * (j - k + depth * i) / N
    return action, phase, current


def path_sum(node: tuple[int, int, int], chirality: int) -> dict[str, Any]:
    amplitudes: dict[tuple[int, int, int], complex] = defaultdict(complex)
    histories: list[dict[str, Any]] = []
    for bits in itertools.product("OB", repeat=PATH_DEPTH):
        word = "".join(bits)
        action, phase, endpoint = action_and_phase(node, word, chirality)
        amplitude = cmath.exp(-BETA * action + 1j * phase)
        amplitudes[endpoint] += amplitude
        histories.append(
            {
                "word": word,
                "endpoint": endpoint,
                "action": action,
                "amplitude": {"real": amplitude.real, "imag": amplitude.imag},
            }
        )
    weights = {endpoint: abs(value) ** 2 for endpoint, value in amplitudes.items()}
    partition = sum(weights.values())
    probabilities = [weight / partition for weight in weights.values() if weight > 0.0]
    path_entropy = -sum(value * math.log2(value) for value in probabilities)
    return {
        "endpoint_count": len(amplitudes),
        "path_count": len(histories),
        "path_entropy": path_entropy,
        "partition": partition,
        "amplitude": {
            "real": sum(amplitudes.values()).real,
            "imag": sum(amplitudes.values()).imag,
        },
        "histories": histories,
    }


def hopfield_update(state: tuple[int, ...]) -> tuple[int, ...]:
    size = len(state)
    return tuple(
        1 if state[(index - 1) % size] + state[index] + state[(index + 1) % size] >= 2 else 0
        for index in range(size)
    )


def hopfield_attractor(state: tuple[int, ...], limit: int = 32) -> tuple[tuple[int, ...], ...]:
    seen: list[tuple[int, ...]] = []
    current = state
    for _ in range(limit):
        if current in seen:
            return tuple(seen[seen.index(current) :])
        seen.append(current)
        current = hopfield_update(current)
    return (current,)


def basin_map() -> tuple[dict[str, list[tuple[int, ...]]], dict[str, str]]:
    basins: dict[str, list[tuple[int, ...]]] = defaultdict(list)
    assignments: dict[str, str] = {}
    for state in itertools.product((0, 1), repeat=4):
        cycle = hopfield_attractor(state)
        key = "|".join("".join(map(str, value)) for value in cycle)
        basins[key].append(state)
        assignments["".join(map(str, state))] = key
    return dict(basins), assignments


def component_field() -> tuple[dict[str, Any], dict[str, Any]]:
    basins, assignments = basin_map()
    field: dict[str, Any] = {}
    for node in nodes():
        i, j, k = node
        forward = path_sum(node, +1)
        reverse = path_sum(node, -1)
        ob = apply_word(node, "OB")
        bo = apply_word(node, "BO")
        left = bracket_left(node)
        right = bracket_right(node)
        fuzzy = fuzzy_shell(node)
        bit_state = (i % 2, j % 2, k % 2, (i + j + k) % 2)
        basin = assignments["".join(map(str, bit_state))]
        shell_mass = sum(weight for other, weight in fuzzy.items() if other[0] == i)
        field["%d,%d,%d" % node] = {
            # Axis 0 is a component field over ijk, not this list collapsed to
            # one scalar.  The complex path amplitude is retained explicitly.
            "ijk": [i, j, k],
            "path_entropy": forward["path_entropy"],
            "endpoint_count": forward["endpoint_count"],
            "order_gap": 0.0 if ob == bo else 1.0,
            "bracket_gap": 0.0 if left == right else 1.0,
            "orientation_gap": abs(
                complex(forward["amplitude"]["real"], forward["amplitude"]["imag"])
                - complex(reverse["amplitude"]["real"], reverse["amplitude"]["imag"])
            ),
            "fuzzy_shell_mass": shell_mass,
            "basin": basin,
        }
    return field, {"basins": basins, "assignments": assignments}


def quotient_field(field: dict[str, Any]) -> dict[str, Any]:
    classes: dict[str, list[list[int]]] = defaultdict(list)
    for row in field.values():
        signature = (
            row["ijk"][0] % 2,
            row["endpoint_count"],
            bool(row["order_gap"]),
            bool(row["bracket_gap"]),
            row["basin"],
        )
        classes[json.dumps(signature, separators=(",", ":"))].append(row["ijk"])
    return {
        "raw_node_count": len(field),
        "quotient_class_count": len(classes),
        "classes": dict(classes),
    }


def mss_frontier(features: dict[str, bool]) -> dict[str, Any]:
    required = {"finite", "order_retention", "basin_recurrence"}
    candidates = [
        {"id": "phase_history", "constraints": {"finite", "order_retention", "basin_recurrence"}},
        {"id": "shell_history", "constraints": {"finite", "order_retention", "basin_recurrence"}},
        {"id": "overbuilt_bracket", "constraints": {"finite", "order_retention", "basin_recurrence", "bracket_seam", "fuzzy_shell"}},
    ]
    rows = []
    for candidate in candidates:
        sufficient = all(features[name] for name in candidate["constraints"])
        rows.append(
            {
                "id": candidate["id"],
                "constraints": sorted(candidate["constraints"]),
                "sufficient": sufficient,
                "cost": len(candidate["constraints"]),
            }
        )
    costs = [row["cost"] for row in rows if row["sufficient"]]
    minimum = min(costs) if costs else None
    frontier = [row["id"] for row in rows if row["sufficient"] and row["cost"] == minimum]
    return {"required": sorted(required), "rows": rows, "frontier": frontier}


def run() -> dict[str, Any]:
    field, dynamics = component_field()
    quotient = quotient_field(field)
    basins = dynamics["basins"]
    features = {
        "finite": len(field) == SHELLS * N * N,
        "order_retention": any(row["order_gap"] > 0 and row["orientation_gap"] > 1e-12 for row in field.values()),
        "basin_recurrence": len(basins) >= 2 and max(len(values) for values in basins.values()) > 1,
        "bracket_seam": any(row["bracket_gap"] > 0 for row in field.values()),
        "fuzzy_shell": any(row["fuzzy_shell_mass"] < 0.999 for row in field.values()),
    }
    chirality_gap = sum(row["orientation_gap"] for row in field.values())
    subbasins: dict[str, int] = defaultdict(int)
    for row in field.values():
        subbasins[f"{row['basin']}::shell{row['ijk'][0]}"] += 1
    sample_keys = sorted(field)[:8]
    return {
        "schema": "codex_ratchet.exploratory_prototype.finite_ijk_path_hopfield.v1",
        "classification": "exploratory_prototype",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "sim_ran": True,
        "claim_ceiling": "finite exploratory ijk field, path-sum deformation, and Hopfield/QCA recurrent-class observation only; not proof, CR validation, physical entropy, or final manifold",
        "parameters": {"shells": SHELLS, "ring_size": N, "path_depth": PATH_DEPTH, "beta": BETA, "fuzzy_sigma": SIGMA},
        "axis0_field": {
            "coordinates": "(i,j,k)",
            "components": ["path_entropy", "endpoint_count", "order_gap", "bracket_gap", "orientation_gap", "fuzzy_shell_mass", "basin"],
            "sample": {key: field[key] for key in sample_keys},
            "node_count": len(field),
        },
        "quotient": quotient,
        "deformation": {
            "chirality_plus_minus_gap_sum": chirality_gap,
            "order_sensitive_nodes": sum(row["order_gap"] > 0 for row in field.values()),
            "bracket_sensitive_nodes": sum(row["bracket_gap"] > 0 for row in field.values()),
        },
        "attractors": {
            "basin_count": len(basins),
            "basin_sizes": sorted((len(values) for values in basins.values()), reverse=True),
            "subbasin_count": len(subbasins),
            "subbasins": dict(sorted(subbasins.items())),
        },
        "mss": mss_frontier(features),
        "features": features,
        "exploration_note": "LLM or search may propose additional candidate constraints; this prototype records the finite family and readouts without selecting a physical interpretation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run()
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps({
        "sim_ran": result["sim_ran"],
        "nodes": result["axis0_field"]["node_count"],
        "quotient_classes": result["quotient"]["quotient_class_count"],
        "basins": result["attractors"]["basin_count"],
        "subbasins": result["attractors"]["subbasin_count"],
        "mss_frontier": result["mss"]["frontier"],
        "order_sensitive_nodes": result["deformation"]["order_sensitive_nodes"],
        "bracket_sensitive_nodes": result["deformation"]["bracket_sensitive_nodes"],
        "chirality_gap_sum": result["deformation"]["chirality_plus_minus_gap_sum"],
        "output": str(args.output) if args.output else None,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
