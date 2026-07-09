#!/usr/bin/env python3
"""Shared finite carrier for qit_full_type1_type2_64_live_v1.

This packet is a scratch diagnostic. It uses the atlas schedule as a finite
object carrier and tests whether ordered engine streams form recoverable
objects under erasure controls. It does not admit Axis0, FEP, physics,
manifold, or real-world perception claims.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any


SIM_ID = "qit_full_type1_type2_64_live_v1"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v7" / "sims" / SIM_ID
RESULTS = SIM_DIR / "results"
ATLAS_SOURCE = ROOT / "system_v4" / "docs" / "ENGINE_64_SCHEDULE_ATLAS.md"

CLAIM_CEILING = (
    "64-row Type-1/Type-2 atlas schedule-runtime object-formation scout only; "
    "not manifold, bridge, Axis0, FEP, hexagram, cognition, or physics admission."
)

TOPOLOGY_IDS = {"Se": 0, "Ne": 1, "Ni": 2, "Si": 3}
OPERATOR_IDS = {"Ti": 0, "Te": 1, "Fi": 2, "Fe": 3}
RESULT_POLARITY = {"WIN": 1, "win": 1, "LOSE": -1, "lose": -1}
RESULT_CASE = {"WIN": 1, "LOSE": 1, "win": -1, "lose": -1}
LOOP_IDS = {"outer": 0, "inner": 1}
ENGINE_IDS = {"Type-1": 0, "Type-2": 1}
PRECEDENCE_IDS = {"operator_first": 1, "terrain_first": -1}

SUBSTAGES = [
    {
        "substage_index": 0,
        "substage_name": "candidate",
        "science_role": "candidate/projection intake",
        "observation_fields": ["topology"],
    },
    {
        "substage_index": 1,
        "substage_name": "measurement",
        "science_role": "measurement/result polarity",
        "observation_fields": ["topology", "result_polarity"],
    },
    {
        "substage_index": 2,
        "substage_name": "gate",
        "science_role": "operator/preference gate",
        "observation_fields": ["topology", "result_polarity", "operator_family"],
    },
    {
        "substage_index": 3,
        "substage_name": "receipt",
        "science_role": "ordered receipt and object-card bind",
        "observation_fields": ["topology", "igt_result", "signed_operator", "precedence", "loop", "engine_type"],
    },
]

MACRO_ROWS = [
    # Type-1 outer / deductive
    {
        "object_id": "T1_outer_deductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "outer",
        "topology": "Se",
        "terrain_id": "Se-in",
        "token": "TiSe",
        "igt_result": "LOSE",
        "signed_operator": "Ti^",
        "precedence": "operator_first",
        "loop_family": "deductive",
    },
    {
        "object_id": "T1_outer_deductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "outer",
        "topology": "Ne",
        "terrain_id": "Ne-in",
        "token": "NeTi",
        "igt_result": "WIN",
        "signed_operator": "Ti_v",
        "precedence": "terrain_first",
        "loop_family": "deductive",
    },
    {
        "object_id": "T1_outer_deductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "outer",
        "topology": "Ni",
        "terrain_id": "Ni-in",
        "token": "NiFe",
        "igt_result": "LOSE",
        "signed_operator": "Fe_v",
        "precedence": "terrain_first",
        "loop_family": "deductive",
    },
    {
        "object_id": "T1_outer_deductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "outer",
        "topology": "Si",
        "terrain_id": "Si-in",
        "token": "FeSi",
        "igt_result": "WIN",
        "signed_operator": "Fe^",
        "precedence": "operator_first",
        "loop_family": "deductive",
    },
    # Type-1 inner / inductive
    {
        "object_id": "T1_inner_inductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "inner",
        "topology": "Se",
        "terrain_id": "Se-in",
        "token": "SeFi",
        "igt_result": "win",
        "signed_operator": "Fi_v",
        "precedence": "terrain_first",
        "loop_family": "inductive",
    },
    {
        "object_id": "T1_inner_inductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "inner",
        "topology": "Si",
        "terrain_id": "Si-in",
        "token": "SiTe",
        "igt_result": "win",
        "signed_operator": "Te_v",
        "precedence": "terrain_first",
        "loop_family": "inductive",
    },
    {
        "object_id": "T1_inner_inductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "inner",
        "topology": "Ni",
        "terrain_id": "Ni-in",
        "token": "TeNi",
        "igt_result": "lose",
        "signed_operator": "Te^",
        "precedence": "operator_first",
        "loop_family": "inductive",
    },
    {
        "object_id": "T1_inner_inductive",
        "engine_type": "Type-1",
        "sheet": "T1_IN",
        "flux": "IN",
        "loop": "inner",
        "topology": "Ne",
        "terrain_id": "Ne-in",
        "token": "FiNe",
        "igt_result": "lose",
        "signed_operator": "Fi^",
        "precedence": "operator_first",
        "loop_family": "inductive",
    },
    # Type-2 outer / inductive
    {
        "object_id": "T2_outer_inductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "outer",
        "topology": "Se",
        "terrain_id": "Se-out",
        "token": "FiSe",
        "igt_result": "WIN",
        "signed_operator": "Fi^",
        "precedence": "operator_first",
        "loop_family": "inductive",
    },
    {
        "object_id": "T2_outer_inductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "outer",
        "topology": "Si",
        "terrain_id": "Si-out",
        "token": "TeSi",
        "igt_result": "WIN",
        "signed_operator": "Te^",
        "precedence": "operator_first",
        "loop_family": "inductive",
    },
    {
        "object_id": "T2_outer_inductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "outer",
        "topology": "Ni",
        "terrain_id": "Ni-out",
        "token": "NiTe",
        "igt_result": "LOSE",
        "signed_operator": "Te_v",
        "precedence": "terrain_first",
        "loop_family": "inductive",
    },
    {
        "object_id": "T2_outer_inductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "outer",
        "topology": "Ne",
        "terrain_id": "Ne-out",
        "token": "NeFi",
        "igt_result": "LOSE",
        "signed_operator": "Fi_v",
        "precedence": "terrain_first",
        "loop_family": "inductive",
    },
    # Type-2 inner / deductive
    {
        "object_id": "T2_inner_deductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "inner",
        "topology": "Se",
        "terrain_id": "Se-out",
        "token": "SeTi",
        "igt_result": "lose",
        "signed_operator": "Ti_v",
        "precedence": "terrain_first",
        "loop_family": "deductive",
    },
    {
        "object_id": "T2_inner_deductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "inner",
        "topology": "Ne",
        "terrain_id": "Ne-out",
        "token": "TiNe",
        "igt_result": "win",
        "signed_operator": "Ti^",
        "precedence": "operator_first",
        "loop_family": "deductive",
    },
    {
        "object_id": "T2_inner_deductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "inner",
        "topology": "Ni",
        "terrain_id": "Ni-out",
        "token": "FeNi",
        "igt_result": "lose",
        "signed_operator": "Fe^",
        "precedence": "operator_first",
        "loop_family": "deductive",
    },
    {
        "object_id": "T2_inner_deductive",
        "engine_type": "Type-2",
        "sheet": "T2_OUT",
        "flux": "OUT",
        "loop": "inner",
        "topology": "Si",
        "terrain_id": "Si-out",
        "token": "SiFe",
        "igt_result": "win",
        "signed_operator": "Fe_v",
        "precedence": "terrain_first",
        "loop_family": "deductive",
    },
]

STAGE_INTELLIGENCE = {
    "Se": "expansion/perception intake",
    "Ne": "branching hypothesis search",
    "Ni": "compression/invariant pull",
    "Si": "retention/memory lock",
}

OPERATOR_INTELLIGENCE = {
    "Ti": "formal internal discriminator",
    "Te": "external controller and receipt gate",
    "Fi": "local coherence and value constraint",
    "Fe": "mesh alignment and shared-readout pressure",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return sha256_bytes(stable_json(value).encode("utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def operator_family(row: dict[str, Any]) -> str:
    return str(row["signed_operator"])[:2]


def object_ids() -> list[str]:
    return list(dict.fromkeys(row["object_id"] for row in MACRO_ROWS))


def macro_rows_by_object() -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {object_id: [] for object_id in object_ids()}
    for row in MACRO_ROWS:
        out[row["object_id"]].append(row)
    return out


def build_schedule() -> list[dict[str, Any]]:
    schedule: list[dict[str, Any]] = []
    macro_index = 0
    slot_index = 0
    for row in MACRO_ROWS:
        for substage in SUBSTAGES:
            schedule.append(
                {
                    **row,
                    "macro_index": macro_index,
                    "substage_index": substage["substage_index"],
                    "substage_name": substage["substage_name"],
                    "science_role": substage["science_role"],
                    "slot_index": slot_index,
                    "slot_id": f"{row['object_id']}:{macro_index % 4}:s{substage['substage_index']}",
                    "chart_locked": substage["substage_index"] == 0,
                    "claim_ceiling": CLAIM_CEILING,
                    "operator_family": operator_family(row),
                    "stage_intelligence": STAGE_INTELLIGENCE[row["topology"]],
                    "operator_intelligence": OPERATOR_INTELLIGENCE[operator_family(row)],
                }
            )
            slot_index += 1
        macro_index += 1
    return schedule


def slots_by_object(schedule: list[dict[str, Any]] | None = None) -> dict[str, list[dict[str, Any]]]:
    rows = schedule or build_schedule()
    out: dict[str, list[dict[str, Any]]] = {object_id: [] for object_id in object_ids()}
    for slot in rows:
        out[slot["object_id"]].append(slot)
    return out


def field_value(slot: dict[str, Any], field: str) -> Any:
    if field == "result_polarity":
        return RESULT_POLARITY[slot["igt_result"]]
    if field == "result_case":
        return RESULT_CASE[slot["igt_result"]]
    return slot[field]


def observation_signature(slot: dict[str, Any], fields: list[str] | None = None) -> tuple[Any, ...]:
    if fields is None:
        fields = SUBSTAGES[int(slot["substage_index"])]["observation_fields"]
    return tuple(field_value(slot, field) for field in fields)


def object_sequence_signature(object_id: str, mode: str = "ordered_full") -> tuple[Any, ...]:
    rows = slots_by_object()[object_id]
    if mode == "ordered_full":
        return tuple(observation_signature(row) for row in rows)
    if mode == "bag_topology":
        return tuple(sorted(row["topology"] for row in rows))
    if mode == "collapsed_sheet_loop":
        return tuple((row["topology"], RESULT_POLARITY[row["igt_result"]]) for row in rows)
    if mode == "first_static":
        return tuple(observation_signature(rows[0]))
    if mode == "operator_bag":
        return tuple(sorted(row["operator_family"] for row in rows))
    raise ValueError(f"unknown signature mode: {mode}")


def entropy_bits(probabilities: list[float]) -> float:
    total = sum(probabilities)
    if total <= 0:
        return 0.0
    out = 0.0
    for p in probabilities:
        q = p / total
        if q > 0:
            out -= q * math.log(q, 2)
    return out


def softmax(logits: list[float]) -> list[float]:
    high = max(logits)
    values = [math.exp(x - high) for x in logits]
    total = sum(values)
    return [x / total for x in values]


def bayes_trace(true_object_id: str) -> dict[str, Any]:
    candidates = object_ids()
    candidate_rows = slots_by_object()
    true_rows = candidate_rows[true_object_id]
    logits = [0.0 for _ in candidates]
    trace = []
    for idx, true_slot in enumerate(true_rows):
        obs = observation_signature(true_slot)
        fields = SUBSTAGES[int(true_slot["substage_index"])]["observation_fields"]
        for cand_idx, cand in enumerate(candidates):
            expected = observation_signature(candidate_rows[cand][idx], fields)
            if expected == obs:
                logits[cand_idx] += 1.4 + 0.2 * len(fields)
            else:
                logits[cand_idx] -= 1.1 * len(fields)
        probs = softmax(logits)
        trace.append(
            {
                "prefix_slot": idx,
                "substage": true_slot["substage_name"],
                "observation": list(obs),
                "posterior": {cand: round(probs[i], 12) for i, cand in enumerate(candidates)},
                "entropy_bits": round(entropy_bits(probs), 12),
                "argmax": candidates[max(range(len(probs)), key=lambda i: probs[i])],
            }
        )
    final = trace[-1]
    entropies = [row["entropy_bits"] for row in trace]
    return {
        "object_id": true_object_id,
        "start_entropy_bits": round(math.log(len(candidates), 2), 12),
        "final_entropy_bits": final["entropy_bits"],
        "entropy_drop_bits": round(math.log(len(candidates), 2) - final["entropy_bits"], 12),
        "monotone_nonincreasing": all(entropies[i + 1] <= entropies[i] + 1e-12 for i in range(len(entropies) - 1)),
        "predicted_object_id": final["argmax"],
        "correct": final["argmax"] == true_object_id,
        "trace": trace,
    }


def control_accuracy(mode: str) -> dict[str, Any]:
    signatures = {object_id: object_sequence_signature(object_id, mode) for object_id in object_ids()}
    buckets: dict[str, list[str]] = {}
    for object_id, signature in signatures.items():
        buckets.setdefault(stable_sha256(signature), []).append(object_id)
    bucket_sizes = [len(v) for v in buckets.values()]
    # A deterministic blind chooser earns 1 / bucket size for each object in a
    # collapsed bucket. This measures how much object identity survives the
    # named projection, not a learned classifier.
    expected_accuracy = sum(1.0 / len(v) for v in buckets.values() for _ in v) / len(signatures)
    return {
        "mode": mode,
        "unique_signature_count": len(buckets),
        "bucket_sizes": sorted(bucket_sizes, reverse=True),
        "expected_accuracy": round(expected_accuracy, 12),
        "passed_as_negative_control": expected_accuracy < 0.999999,
        "signatures_sha256": stable_sha256(signatures),
    }


def loop_edge_family(topologies: list[str]) -> list[dict[str, str]]:
    edge_map = {
        frozenset(("Se", "Si")): "Ax0",
        frozenset(("Ne", "Ni")): "Ax0",
        frozenset(("Se", "Ne")): "Ax2",
        frozenset(("Si", "Ni")): "Ax2",
    }
    edges = []
    for left, right in zip(topologies, topologies[1:] + topologies[:1], strict=True):
        edges.append({"from": left, "to": right, "edge_family": edge_map[frozenset((left, right))]})
    return edges


def axis0_boundary_closure() -> dict[str, Any]:
    out = {}
    for object_id, rows in macro_rows_by_object().items():
        topologies = [row["topology"] for row in rows]
        edges = loop_edge_family(topologies)
        out[object_id] = {
            "topology_order": topologies,
            "closure_edges": edges,
            "closed_loop": len(edges) == 4 and edges[-1]["to"] == topologies[0],
            "axis0_claim_ceiling": "atlas edge-walk boundary closure only; not Axis0 admission",
        }
    return out


def stage_personality_map() -> list[dict[str, Any]]:
    rows = []
    for idx, row in enumerate(MACRO_ROWS):
        rows.append(
            {
                "macro_index": idx,
                "object_id": row["object_id"],
                "engine_type": row["engine_type"],
                "loop": row["loop"],
                "terrain_id": row["terrain_id"],
                "token": row["token"],
                "signed_operator": row["signed_operator"],
                "stage_intelligence": STAGE_INTELLIGENCE[row["topology"]],
                "operator_intelligence": OPERATOR_INTELLIGENCE[operator_family(row)],
                "unique_stage_personality": (
                    f"{row['engine_type']} {row['loop']} {row['terrain_id']} {row['token']} "
                    f"as {STAGE_INTELLIGENCE[row['topology']]} + {OPERATOR_INTELLIGENCE[operator_family(row)]}"
                ),
            }
        )
    return rows


def numeric_feature_matrix(mode: str = "ordered_full") -> tuple[list[str], list[list[float]]]:
    rows = []
    labels = []
    for object_id, slots in slots_by_object().items():
        labels.append(object_id)
        values: list[float] = []
        if mode == "bag_topology":
            counts = Counter(slot["topology"] for slot in slots)
            values = [float(counts[key]) for key in ("Se", "Ne", "Ni", "Si")]
        else:
            for slot in slots:
                if mode == "collapsed_sheet_loop":
                    values.extend([TOPOLOGY_IDS[slot["topology"]], RESULT_POLARITY[slot["igt_result"]]])
                elif mode == "ordered_full":
                    values.extend(
                        [
                            TOPOLOGY_IDS[slot["topology"]],
                            OPERATOR_IDS[slot["operator_family"]],
                            RESULT_POLARITY[slot["igt_result"]],
                            RESULT_CASE[slot["igt_result"]],
                            PRECEDENCE_IDS[slot["precedence"]],
                            LOOP_IDS[slot["loop"]],
                            ENGINE_IDS[slot["engine_type"]],
                            float(slot["substage_index"]),
                        ]
                    )
                else:
                    raise ValueError(mode)
        rows.append(values)
    return labels, rows


def object_cards() -> list[dict[str, Any]]:
    cards = []
    for object_id in object_ids():
        ordered = object_sequence_signature(object_id, "ordered_full")
        controls = {
            mode: stable_sha256(object_sequence_signature(object_id, mode))
            for mode in ("bag_topology", "collapsed_sheet_loop", "first_static", "operator_bag")
        }
        cards.append(
            {
                "schema": f"cr.{SIM_ID}.object_card.v1",
                "object_id": object_id,
                "root_object": "ordered atlas loop object",
                "survivor_hash": stable_sha256(ordered),
                "anti_hashes": controls,
                "projection_rows": [
                    {
                        "name": mode,
                        "preserves": "some finite projection of the loop object",
                        "erases": "ordered full object identity" if mode != "ordered_full" else "none for this finite scout",
                        "status": "SCRATCH_DIAGNOSTIC",
                    }
                    for mode in ("bag_topology", "collapsed_sheet_loop", "first_static", "operator_bag")
                ],
            }
        )
    return cards


def schedule_summary(schedule: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rows = schedule or build_schedule()
    coordinates = {
        (
            row["engine_type"],
            row["loop"],
            row["macro_index"],
            row["substage_index"],
        )
        for row in rows
    }
    return {
        "slot_count": len(rows),
        "macro_stage_count": len({row["macro_index"] for row in rows}),
        "substage_count_per_macro": 4,
        "type1_slots": sum(1 for row in rows if row["engine_type"] == "Type-1"),
        "type2_slots": sum(1 for row in rows if row["engine_type"] == "Type-2"),
        "chart_locked_slots": sum(1 for row in rows if row["chart_locked"]),
        "runtime_probe_slots": sum(1 for row in rows if not row["chart_locked"]),
        "unique_coordinate_count": len(coordinates),
        "schedule_sha256": stable_sha256(rows),
    }


def build_core_measurement() -> dict[str, Any]:
    schedule = build_schedule()
    traces = {object_id: bayes_trace(object_id) for object_id in object_ids()}
    controls = {
        mode: control_accuracy(mode)
        for mode in ("bag_topology", "collapsed_sheet_loop", "first_static", "operator_bag")
    }
    ordered_accuracy = sum(1 for row in traces.values() if row["correct"]) / len(traces)
    entropy_drops = [row["entropy_drop_bits"] for row in traces.values()]
    type1_ids = [object_id for object_id in object_ids() if object_id.startswith("T1")]
    type2_ids = [object_id for object_id in object_ids() if object_id.startswith("T2")]
    return {
        "schedule_summary": schedule_summary(schedule),
        "ordered_object_formation": {
            "object_count": len(object_ids()),
            "ordered_accuracy": round(ordered_accuracy, 12),
            "mean_entropy_drop_bits": round(sum(entropy_drops) / len(entropy_drops), 12),
            "min_entropy_drop_bits": round(min(entropy_drops), 12),
            "all_entropy_gradients_monotone": all(row["monotone_nonincreasing"] for row in traces.values()),
            "traces": traces,
        },
        "negative_controls": controls,
        "axis0_boundary_check": axis0_boundary_closure(),
        "type1_type2_comparison": {
            "type1_object_ids": type1_ids,
            "type2_object_ids": type2_ids,
            "type1_mean_entropy_drop_bits": round(
                sum(traces[object_id]["entropy_drop_bits"] for object_id in type1_ids) / len(type1_ids), 12
            ),
            "type2_mean_entropy_drop_bits": round(
                sum(traces[object_id]["entropy_drop_bits"] for object_id in type2_ids) / len(type2_ids), 12
            ),
            "type1_method": "outer deductive + inner inductive, model-to-measure then measure-to-model",
            "type2_method": "outer inductive + inner deductive, measure-to-model then model-to-measure",
            "same_method_family": "bidirectional finite science loop",
            "different_ordering": True,
        },
        "object_cards": object_cards(),
        "stage_intelligence_personality": stage_personality_map(),
    }


def source_lock(path: Path, role: str) -> dict[str, Any]:
    out: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        out["sha256"] = sha256_file(path)
    return out
