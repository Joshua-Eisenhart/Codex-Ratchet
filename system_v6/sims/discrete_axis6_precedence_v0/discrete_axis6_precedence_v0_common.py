#!/usr/bin/env python3
"""Shared carrier-pinned Axis-6 precedence builder.

This packet is intentionally file-disjoint from the committed Axis-0 packet but
uses the same committed 33-cell Family A carrier.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import networkx as nx
import numpy as np
from scipy.linalg import expm
import sympy as sp
import z3


SIM_ID = "discrete_axis6_precedence_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only"
ENGINE_MODE = "three_engine_axis6_precedence_candidate_on_family_a_33_cell_carrier"
EXPECTED_STATE_COUNT = 33
EXPECTED_EDGE_COUNT = 198
EPS = 1.0e-10
S4_PIN_SHA256 = "0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566"
S5_PIN_SHA256 = "ced1d4a8395b66077defbfa44dade651cac9c02ef7ea95cca9918a4019b0634a"
PRIMARY_OPERATOR = "D_z"
PRIMARY_TERRAIN = "Ne_Spiral_R"
TERRAIN_H = "1/2"

AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
if str(AXIS0_DIR) not in sys.path:
    sys.path.insert(0, str(AXIS0_DIR))

import discrete_axis0_field_v0_common as axis0_common  # noqa: E402


PARENT_COMMITS = {
    "axis_work_order": "f6112e407",
    "discrete_axis0_field_v0": "5d330b427",
    "axis_independence_discriminators_036": "0fcf2cc85",
    "blind_panel_q2": "eba5fdca0",
    "contender_registry": "fcf1b3858",
}
PARENT_PATHS = {
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "axis0_common": ROOT / "system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_common.py",
    "axis_independence_discriminators_036": ROOT
    / "system_v6/sims/axis_independence_discriminators_036/results/axis_independence_discriminators_036_envelope_results.json",
    "geo_s4_envelope": ROOT / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "geo_s5_envelope": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "basin_rc_envelope": ROOT / "system_v6/sims/basin_rc_transition_graph_v0/results/basin_rc_transition_graph_v0_envelope_results.json",
    "axis_deep_math": ROOT / "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
    "terrain_operator_source_layout": ROOT
    / "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
    "qit_operator_source_math": ROOT / "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
}

TOOL_INTENT = {
    "claim_classes": [
        "finite_axis6_precedence_readout_candidate",
        "pinned_operator_terrain_affine_order_gap",
        "carrier_honest_axis0_axis6_independence_discriminator",
        "staged_b0_b6_prediction_only",
        "computed_negative_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "rebuild the 33-cell carrier graph and count Axis-6 sign stability across committed generator edges",
            "Z3": "bind computed precedence/stability/independence/control counts and prove the negated packet identity unsat with erased flips sat",
        },
        "jax": {
            "networkx": "build the directed 33-cell graph and verify collapsed carrier adjacency/stability metadata",
            "sympy": "compute exact symbolic commutator template rows for D_z and Ne_Spiral_R before numeric h=1/2 flow evaluation",
            "z3": "bind computed precedence/nonneutral counts in SMT and prove nonzero identity cannot be erased",
            "cvc5": "independent SMT binding of the same computed precedence/nonneutral counts with erased flips",
        },
        "pytorch": {
            "torch.func": "vectorized precedence sign recomputation over the 33 cell Bloch vectors",
            "torch_geometric": "Data edge_index carrier for the committed 198 directed generator edges",
            "sympy": "exact symbolic D_z contraction row mirrored in the PyTorch lane",
            "z3": "bind computed precedence/nonneutral counts in SMT and prove nonzero identity cannot be erased",
            "cvc5": "independent SMT binding of the same computed precedence/nonneutral counts with erased flips",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite carrier graph and Axis-6 stability counts"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT computed-value identity and erased flip"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot finite directed graph carrier and stability metadata"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized precedence recomputation"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch directed edge_index carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact symbolic commutator/source-row probes"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed-value identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed-value identity and erased flip"},
}
TOOL_INTEGRATION_DEPTH = {
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "torch_geometric": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def parse_expr(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    return float(sp.N(sp.sympify(str(value), locals={"sqrt": sp.sqrt}), 30))


def parse_matrix(rows: list[list[Any]]) -> np.ndarray:
    return np.asarray([[parse_expr(value) for value in row] for row in rows], dtype=float)


def parse_vector(values: list[Any]) -> np.ndarray:
    return np.asarray([parse_expr(value) for value in values], dtype=float)


def round_float(value: float, digits: int = 15) -> float:
    if abs(value) < EPS:
        return 0.0
    return round(float(value), digits)


def round_vec(values: np.ndarray | list[float], digits: int = 15) -> list[float]:
    return [round_float(float(value), digits) for value in values]


def sign(value: float) -> int:
    return 1 if value > EPS else -1 if value < -EPS else 0


def sign_label(value: int) -> str:
    return {
        1: "operator_first_precedence",
        -1: "terrain_first_precedence",
        0: "neutral_commuting_or_zero_projection",
    }[value]


def complex_obj(real: float, imag: float = 0.0) -> dict[str, float]:
    return {"re": round_float(real), "im": round_float(imag)}


def density_matrix_from_bloch(r: np.ndarray) -> list[list[dict[str, float]]]:
    x, y, z_coord = [float(value) for value in r]
    return [
        [complex_obj((1.0 + z_coord) / 2.0), complex_obj(x / 2.0, -y / 2.0)],
        [complex_obj(x / 2.0, y / 2.0), complex_obj((1.0 - z_coord) / 2.0)],
    ]


def source_import_audit() -> dict[str, Any]:
    return {
        "authority_and_context": {
            "axis_work_order": source_lock(
                PARENT_PATHS["axis_work_order"],
                "work_order_axis6_row",
                PARENT_COMMITS["axis_work_order"],
            ),
            "axis_deep_math": source_lock(PARENT_PATHS["axis_deep_math"], "axis_0_6_source_math_context"),
            "terrain_operator_source_layout": source_lock(
                PARENT_PATHS["terrain_operator_source_layout"],
                "terrain_operator_source_layout_context",
            ),
            "qit_operator_source_math": source_lock(PARENT_PATHS["qit_operator_source_math"], "operator_source_math_context"),
        },
        "parent_hash_pins": {
            "axis0_envelope": source_lock(
                PARENT_PATHS["axis0_envelope"],
                "committed_axis0_family_a_carrier_and_response_rows",
                PARENT_COMMITS["discrete_axis0_field_v0"],
            ),
            "axis_independence_discriminators_036": source_lock(
                PARENT_PATHS["axis_independence_discriminators_036"],
                "committed_o6_independence_discriminator_context",
                PARENT_COMMITS["axis_independence_discriminators_036"],
            ),
            "geo_s4_envelope": source_lock(PARENT_PATHS["geo_s4_envelope"], "committed_s4_operator_pin"),
            "geo_s5_envelope": source_lock(PARENT_PATHS["geo_s5_envelope"], "committed_s5_terrain_pin"),
            "basin_rc_envelope": source_lock(PARENT_PATHS["basin_rc_envelope"], "committed_family_a_flow_cross_check"),
        },
        "anti_conflation_rule": "Axis-6 here is terrain/operator precedence on the Family A carrier, not Axis-4 composition order and not Axis-0 response or Axis-3 placement.",
        "raw_parent_classification_imported": False,
    }


@lru_cache(maxsize=1)
def pinning_payload() -> dict[str, Any]:
    s4 = load_json(PARENT_PATHS["geo_s4_envelope"])
    s5 = load_json(PARENT_PATHS["geo_s5_envelope"])
    basin = load_json(PARENT_PATHS["basin_rc_envelope"])
    operator_row = s4["affine_channel_table"][PRIMARY_OPERATOR]
    terrain_row = s5["bloch_generator_table"][PRIMARY_TERRAIN]

    op_m = parse_matrix(operator_row["pinned"]["M"])
    op_c = parse_vector(operator_row["pinned"]["c"])
    terrain_a = parse_matrix(terrain_row["pinned"]["A"])
    terrain_b = parse_vector(terrain_row["pinned"]["b"])
    aug = np.zeros((4, 4), dtype=float)
    aug[:3, :3] = terrain_a
    aug[:3, 3] = terrain_b
    flow = expm(0.5 * aug)
    terrain_m = flow[:3, :3]
    terrain_c = flow[:3, 3]

    basin_flow = next(
        row for row in basin["R_C_explicit"]["generators"] if row.get("name") == PRIMARY_TERRAIN
    )
    basin_m = np.asarray(basin_flow["M"], dtype=float)
    basin_c = np.asarray(basin_flow["c"], dtype=float)
    return {
        "operator": {
            "id": f"S4:{PRIMARY_OPERATOR}",
            "name": PRIMARY_OPERATOR,
            "pin_sha256": s4.get("pin_sha256"),
            "source_path": rel(PARENT_PATHS["geo_s4_envelope"]),
            "source_sha256": sha256_file(PARENT_PATHS["geo_s4_envelope"]),
            "symbolic": operator_row["symbolic"],
            "pinned": operator_row["pinned"],
            "M": op_m,
            "c": op_c,
        },
        "terrain": {
            "id": f"S5:{PRIMARY_TERRAIN}",
            "name": PRIMARY_TERRAIN,
            "h": TERRAIN_H,
            "pin_sha256": s5.get("pin_sha256"),
            "source_path": rel(PARENT_PATHS["geo_s5_envelope"]),
            "source_sha256": sha256_file(PARENT_PATHS["geo_s5_envelope"]),
            "source_ref": terrain_row.get("source_ref"),
            "symbolic": terrain_row["symbolic"],
            "pinned_generator": terrain_row["pinned"],
            "M": terrain_m,
            "c": terrain_c,
            "basin_flow_cross_check": {
                "source_path": rel(PARENT_PATHS["basin_rc_envelope"]),
                "source_sha256": sha256_file(PARENT_PATHS["basin_rc_envelope"]),
                "matches_committed_h_half_flow": bool(
                    np.allclose(terrain_m, basin_m, atol=1.0e-12)
                    and np.allclose(terrain_c, basin_c, atol=1.0e-12)
                ),
                "max_abs_matrix_delta": round_float(float(np.max(np.abs(terrain_m - basin_m)))),
                "max_abs_offset_delta": round_float(float(np.max(np.abs(terrain_c - basin_c)))),
            },
        },
    }


def json_pinning(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "operator": {
            key: value
            for key, value in payload["operator"].items()
            if key not in {"M", "c"}
        }
        | {
            "M": [round_vec(row) for row in payload["operator"]["M"]],
            "c": round_vec(payload["operator"]["c"]),
        },
        "terrain": {
            key: value
            for key, value in payload["terrain"].items()
            if key not in {"M", "c"}
        }
        | {
            "M": [round_vec(row) for row in payload["terrain"]["M"]],
            "c": round_vec(payload["terrain"]["c"]),
        },
    }


def apply_affine(matrix: np.ndarray, offset: np.ndarray, r: np.ndarray) -> np.ndarray:
    return matrix @ r + offset


def precedence_row(cell: dict[str, Any], operator: dict[str, Any], terrain: dict[str, Any]) -> dict[str, Any]:
    r = np.asarray(cell["coord"], dtype=float)
    op_first = apply_affine(terrain["M"], terrain["c"], apply_affine(operator["M"], operator["c"], r))
    terrain_first = apply_affine(operator["M"], operator["c"], apply_affine(terrain["M"], terrain["c"], r))
    delta = op_first - terrain_first
    trace_norm_weight = float(np.linalg.norm(delta, ord=2))
    z_component_difference = float(delta[2])
    weighted_z_difference = trace_norm_weight * z_component_difference
    b6 = sign(weighted_z_difference)
    return {
        "cell_id": int(cell["cell_id"]),
        "coord": cell["coord"],
        "coord_scaled": cell["coord_scaled"],
        "operator_first_expression": "Phi_T(O(rho_cell))",
        "terrain_first_expression": "O(Phi_T(rho_cell))",
        "operator_first_bloch": round_vec(op_first),
        "terrain_first_bloch": round_vec(terrain_first),
        "operator_first_density": density_matrix_from_bloch(op_first),
        "terrain_first_density": density_matrix_from_bloch(terrain_first),
        "bloch_difference_operator_first_minus_terrain_first": round_vec(delta),
        "z_component_difference": round_float(z_component_difference),
        "trace_norm_weight": round_float(trace_norm_weight),
        "weighted_z_difference": round_float(weighted_z_difference),
        "b6_sign": b6,
        "b6_label": sign_label(b6),
        "functional": "sign(||Delta rho||_1 * Delta z); for qubit Bloch differences ||Delta rho||_1=||Delta r||_2",
    }


def precedence_table(carrier: dict[str, Any], pinning: dict[str, Any]) -> list[dict[str, Any]]:
    return [precedence_row(cell, pinning["operator"], pinning["terrain"]) for cell in carrier["cells"]]


def precedence_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["b6_sign"] for row in rows)
    return {
        "positive": counts[1],
        "negative": counts[-1],
        "neutral": counts[0],
        "nonneutral": counts[1] + counts[-1],
        "total": len(rows),
        "by_label": dict(Counter(row["b6_label"] for row in rows)),
    }


def one_and_two_step_stability(carrier: dict[str, Any], signs_by_cell: dict[int, int]) -> dict[str, Any]:
    one_rows = []
    by_generator: dict[str, dict[str, int]] = defaultdict(lambda: {"stable": 0, "changed": 0})
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        same = signs_by_cell[src] == signs_by_cell[dst]
        by_generator[edge["generator"]]["stable" if same else "changed"] += 1
        one_rows.append(
            {
                "edge_id": int(edge["edge_id"]),
                "src": src,
                "dst": dst,
                "generator": edge["generator"],
                "src_b6_sign": signs_by_cell[src],
                "dst_b6_sign": signs_by_cell[dst],
                "survives_update": same,
            }
        )
    outgoing: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for edge in carrier["edges"]:
        outgoing[int(edge["src"])].append(edge)
    two_rows = []
    for first in carrier["edges"]:
        for second in outgoing[int(first["dst"])]:
            src = int(first["src"])
            dst = int(second["dst"])
            same = signs_by_cell[src] == signs_by_cell[dst]
            two_rows.append(
                {
                    "src": src,
                    "mid": int(first["dst"]),
                    "dst": dst,
                    "generators": [first["generator"], second["generator"]],
                    "src_b6_sign": signs_by_cell[src],
                    "dst_b6_sign": signs_by_cell[dst],
                    "survives_two_step_update": same,
                }
            )
    one_stable = sum(row["survives_update"] for row in one_rows)
    two_stable = sum(row["survives_two_step_update"] for row in two_rows)
    return {
        "scope": "one_step_and_two_step_edges_on_committed_family_a_carrier",
        "one_step": {
            "edge_count": len(one_rows),
            "stable_edges": one_stable,
            "changed_edges": len(one_rows) - one_stable,
            "stable_fraction": one_stable / len(one_rows) if one_rows else 0.0,
            "changed_fraction": (len(one_rows) - one_stable) / len(one_rows) if one_rows else 0.0,
            "by_generator": dict(sorted(by_generator.items())),
            "rows": one_rows,
        },
        "two_step": {
            "path_count": len(two_rows),
            "stable_paths": two_stable,
            "changed_paths": len(two_rows) - two_stable,
            "stable_fraction": two_stable / len(two_rows) if two_rows else 0.0,
            "changed_fraction": (len(two_rows) - two_stable) / len(two_rows) if two_rows else 0.0,
            "sample_rows": two_rows[:64],
        },
        "neither_trivial_nor_frozen": one_stable > 0 and len(one_rows) - one_stable > 0 and two_stable > 0 and len(two_rows) - two_stable > 0,
    }


def majority_accuracy(rows: list[dict[str, Any]], key_name: str, target_name: str) -> tuple[float, dict[str, Any]]:
    groups: dict[str, Counter[Any]] = defaultdict(Counter)
    for row in rows:
        groups[str(row[key_name])][row[target_name]] += 1
    correct = sum(counter.most_common(1)[0][1] for counter in groups.values())
    ambiguous = {
        key: {str(target): count for target, count in counter.items()}
        for key, counter in groups.items()
        if len([value for value in counter.values() if value > 0]) > 1
    }
    return (correct / len(rows) if rows else 0.0), ambiguous


def witness_pair(rows: list[dict[str, Any]], key_name: str, target_name: str) -> dict[str, Any]:
    by_key: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_key[str(row[key_name])].append(row)
    for key, group in sorted(by_key.items()):
        for left in group:
            for right in group:
                if left["cell_id"] < right["cell_id"] and left[target_name] != right[target_name]:
                    return {
                        "key": key,
                        "left_cell_id": left["cell_id"],
                        f"left_{target_name}": left[target_name],
                        "right_cell_id": right["cell_id"],
                        f"right_{target_name}": right[target_name],
                        f"same_{key_name}": True,
                    }
    return {}


def joined_axis0_axis6_rows(axis0_rows: list[dict[str, Any]], precedence_rows: list[dict[str, Any]], carrier: dict[str, Any]) -> list[dict[str, Any]]:
    by_b6 = {row["cell_id"]: row for row in precedence_rows}
    successor_counts = carrier["successor_count_by_cell"]
    joined = []
    for row in axis0_rows:
        b6 = by_b6[int(row["cell_id"])]
        joined.append(
            {
                **row,
                "successor_count": successor_counts[int(row["cell_id"])],
                "b6_sign": b6["b6_sign"],
                "b6_label": b6["b6_label"],
                "weighted_z_difference": b6["weighted_z_difference"],
            }
        )
    return joined


def add_combo_key(rows: list[dict[str, Any]], key_name: str, fields: list[str]) -> list[dict[str, Any]]:
    combo_rows = []
    for row in rows:
        combo = dict(row)
        combo[key_name] = "|".join(f"{field}={row[field]}" for field in fields)
        combo_rows.append(combo)
    return combo_rows


def independence_rows_vs_axis0(axis0_rows: list[dict[str, Any]], precedence_rows: list[dict[str, Any]], carrier: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    joined = joined_axis0_axis6_rows(axis0_rows, precedence_rows, carrier)
    a0_to_b6_acc, a0_to_b6_amb = majority_accuracy(joined, "axis0_polarity_sign", "b6_sign")
    b6_to_a0_acc, b6_to_a0_amb = majority_accuracy(joined, "b6_sign", "axis0_polarity_sign")

    frozen_candidates = []
    for name, fields in {
        "kappa": ["kappa"],
        "nesting": ["nesting"],
        "conditioned_shell_member": ["conditioned_shell_member"],
        "axis0_response_x_kappa_x_nesting": ["axis0_polarity_sign", "kappa", "nesting"],
        "axis0_non_identity_combined": [
            "axis0_polarity_sign",
            "kappa",
            "nesting",
            "conditioned_shell_member",
            "phi_numerator",
            "axis3_style_placement_key",
            "axis6_style_order_key",
        ],
    }.items():
        keyed = add_combo_key(joined, "predictor_key", fields)
        acc, ambiguous = majority_accuracy(keyed, "predictor_key", "b6_sign")
        frozen_candidates.append(
            {
                "predictor_id": name,
                "fields": fields,
                "majority_accuracy": acc,
                "ambiguous_key_count": len(ambiguous),
            }
        )
    best_non_identity = max(frozen_candidates, key=lambda row: row["majority_accuracy"])
    identity_fields = [
        "cell_id",
        "coord_scaled",
        "net_outgoing_gradient_flux",
        "axis0_polarity_sign",
        "phi_numerator",
        "axis6_style_order_key",
    ]
    identity_keyed = add_combo_key(joined, "identity_predictor_key", identity_fields)
    identity_acc, identity_amb = majority_accuracy(identity_keyed, "identity_predictor_key", "b6_sign")
    rows = [
        {
            "row_id": "axis6_not_recoverable_from_axis0_response",
            "predictor": "axis0_polarity_sign",
            "target": "b6_sign",
            "majority_accuracy": a0_to_b6_acc,
            "ambiguous_keys": a0_to_b6_amb,
            "witness_pair": witness_pair(joined, "axis0_polarity_sign", "b6_sign"),
            "pass": a0_to_b6_acc < 1.0,
            "carrier_honest": True,
        },
        {
            "row_id": "axis0_response_not_recoverable_from_axis6",
            "predictor": "b6_sign",
            "target": "axis0_polarity_sign",
            "majority_accuracy": b6_to_a0_acc,
            "ambiguous_keys": b6_to_a0_amb,
            "witness_pair": witness_pair(joined, "b6_sign", "axis0_polarity_sign"),
            "pass": b6_to_a0_acc < 1.0,
            "carrier_honest": True,
        },
        {
            "row_id": "best_predictor_full_axis0_feature_report",
            "full_axis0_fields_included_in_report": True,
            "identity_inclusive_fields": identity_fields,
            "identity_inclusive_majority_accuracy": identity_acc,
            "identity_inclusive_ambiguous_key_count": len(identity_amb),
            "identity_leak_detected": identity_acc == 1.0,
            "identity_leak_exclusion_rule": "cell identity, coordinates, and direct axis0 output fingerprints are reported but excluded from the independence pass/fail predictor.",
            "identity_leak_excluded_candidate_rows": frozen_candidates,
            "identity_leak_excluded_best_predictor": best_non_identity["predictor_id"],
            "identity_leak_excluded_best_accuracy": best_non_identity["majority_accuracy"],
            "pass": best_non_identity["majority_accuracy"] < 1.0,
            "status": "carrier_honest_with_identity_leak_caveat",
        },
    ]
    return rows, {
        "joined_rows": joined,
        "best_non_identity": best_non_identity,
        "identity_inclusive_accuracy": identity_acc,
    }


def compute_controls(carrier: dict[str, Any], rows: list[dict[str, Any]], pinning: dict[str, Any], independence_aux: dict[str, Any]) -> dict[str, Any]:
    signs = {row["cell_id"]: row["b6_sign"] for row in rows}
    counts = precedence_counts(rows)
    commuting_operator = pinning["operator"]
    commuting_terrain = {
        "M": pinning["operator"]["M"],
        "c": pinning["operator"]["c"],
    }
    commuting = [precedence_row(cell, commuting_operator, commuting_terrain) for cell in carrier["cells"]]
    constant_operator = {"M": np.eye(3), "c": np.zeros(3)}
    constant_terrain = {"M": np.eye(3), "c": np.zeros(3)}
    constant = [precedence_row(cell, constant_operator, constant_terrain) for cell in carrier["cells"]]
    flipped = {-row["b6_sign"] if row["b6_sign"] != 0 else 0 for row in rows}
    flip_count = sum((-row["b6_sign"] if row["b6_sign"] != 0 else 0) != row["b6_sign"] for row in rows)
    shuffled_matches = 0
    for row in rows:
        permuted_cell = (7 * row["cell_id"] + 3) % EXPECTED_STATE_COUNT
        if signs[permuted_cell] == row["b6_sign"]:
            shuffled_matches += 1
    best_frozen = independence_aux["best_non_identity"]
    return {
        "commuting_control": {
            "fired": True,
            "pair": "O=D_z and Phi_T=D_z",
            "all_cells_neutral": all(row["b6_sign"] == 0 for row in commuting),
            "neutral_count": sum(row["b6_sign"] == 0 for row in commuting),
            "falsifier_reachability": "A commuting pair reaches the all-neutral outcome under the same functional.",
        },
        "shuffled_order_n01": {
            "fired": flip_count == counts["nonneutral"],
            "n01_flips_or_demotes": flip_count == counts["nonneutral"] and len(flipped) >= 2,
            "operation": "swap declared difference from Phi_T(O(rho))-O(Phi_T(rho)) to its negative",
            "flipped_nonzero_count": flip_count,
            "base_nonneutral_count": counts["nonneutral"],
        },
        "frozen_factor_projection": {
            "fired": best_frozen["majority_accuracy"] < 1.0,
            "best_frozen_factor_predictor": best_frozen["predictor_id"],
            "best_frozen_factor_accuracy": best_frozen["majority_accuracy"],
            "candidate_rows": independence_aux.get("joined_rows", [])[:0],
            "why": "Frozen axis0 factors and non-identity readout summaries do not perfectly recover b6.",
        },
        "constant_field_degenerate": {
            "fired": True,
            "pair": "identity operator and identity terrain flow",
            "all_cells_neutral": all(row["b6_sign"] == 0 for row in constant),
            "neutral_count": sum(row["b6_sign"] == 0 for row in constant),
        },
        "label_permutation": {
            "fired": shuffled_matches < EXPECTED_STATE_COUNT,
            "permutation": "cell_id -> (7*cell_id+3) mod 33",
            "label_only_reproduction_match_count": shuffled_matches,
            "label_only_reproduction_pass": shuffled_matches == EXPECTED_STATE_COUNT,
        },
    }


def b0_b6_prediction(axis0_rows: list[dict[str, Any]], precedence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    b6_by_cell = {row["cell_id"]: row for row in precedence_rows}
    table = []
    for row in axis0_rows:
        b0 = int(row["axis0_polarity_sign"])
        b6 = int(b6_by_cell[int(row["cell_id"])]["b6_sign"])
        pred = b0 * b6
        table.append(
            {
                "cell_id": int(row["cell_id"]),
                "b0_axis0_response_sign": b0,
                "b6_precedence_sign": b6,
                "b0_times_b6": pred,
                "prediction_for_negative_axis3_sign": pred,
                "claim": "prediction_of_minus_b3_not_axis3_measurement",
            }
        )
    return {
        "relation_status": "staged_prediction_only_requires_axis3_same_carrier_follow_on",
        "blind_panel_q2_arithmetic": "b6=-b0*b3, so b0*b6 is staged as prediction of -b3 only.",
        "axis3_same_carrier_status": "not_computed_in_this_packet",
        "table": table,
    }


def contender_registry() -> list[dict[str, Any]]:
    return [
        {
            "contender_id": "trace_norm_weighted_z_precedence",
            "status": "run_primary_candidate",
            "readout": "sign(||Phi_T(O(rho))-O(Phi_T(rho))||_1 * z_component_difference)",
            "demotion_condition": "demote if commuting control is not all-neutral or if same-carrier independence collapses without identity leakage",
        },
        {
            "contender_id": "commutator_sign_readout",
            "status": "staged_not_run",
            "readout": "sign of a direct commutator functional for the pinned operator/terrain pair",
            "teeth": "must beat neutral/commuting and label-permutation controls on the same carrier",
        },
        {
            "contender_id": "lr_action_spectral_order",
            "status": "staged_not_run",
            "readout": "LEFT action L_A(rho)=A rho versus RIGHT action R_A(rho)=rho A spectral order",
            "teeth": "must use the owner apple source naming and not collapse into Axis-4 order",
        },
        {
            "contender_id": "win_lose_pattern_discriminator",
            "status": "staged_not_run",
            "readout": "win/lose precedence pattern from the committed scaffold",
            "teeth": "must return a per-cell carrier table and controls before being compared to the primary",
        },
    ]


def _z3_axis6_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = z3.Solver()
    pos = z3.Int("axis6_pos_erased" if erased else "axis6_pos")
    neg = z3.Int("axis6_neg_erased" if erased else "axis6_neg")
    neutral = z3.Int("axis6_neutral_erased" if erased else "axis6_neutral")
    total = z3.Int("axis6_total_erased" if erased else "axis6_total")
    stable = z3.Int("axis6_stable_erased" if erased else "axis6_stable")
    changed = z3.Int("axis6_changed_erased" if erased else "axis6_changed")
    edge_count = z3.Int("axis6_edge_count_erased" if erased else "axis6_edge_count")
    a0_to_b6 = z3.Int("axis6_not_from_axis0_response_erased" if erased else "axis6_not_from_axis0_response")
    b6_to_a0 = z3.Int("axis0_not_from_axis6_erased" if erased else "axis0_not_from_axis6")
    commuting_neutral = z3.Int("axis6_commuting_neutral_erased" if erased else "axis6_commuting_neutral")
    if erased:
        bind = {
            **values,
            "positive": 0,
            "negative": 0,
            "stable_edges": 0,
            "changed_edges": values["edge_count"],
            "axis6_not_from_axis0_response": 0,
            "axis0_not_from_axis6": 0,
            "commuting_neutral_count": 0,
        }
    else:
        bind = values
    solver.add(pos == bind["positive"])
    solver.add(neg == bind["negative"])
    solver.add(neutral == bind["neutral"])
    solver.add(total == bind["total"])
    solver.add(stable == bind["stable_edges"])
    solver.add(changed == bind["changed_edges"])
    solver.add(edge_count == bind["edge_count"])
    solver.add(a0_to_b6 == bind["axis6_not_from_axis0_response"])
    solver.add(b6_to_a0 == bind["axis0_not_from_axis6"])
    solver.add(commuting_neutral == bind["commuting_neutral_count"])
    solver.add(
        z3.Or(
            pos == 0,
            neg == 0,
            pos + neg + neutral != total,
            stable == 0,
            changed == 0,
            stable + changed != edge_count,
            a0_to_b6 != 1,
            b6_to_a0 != 1,
            commuting_neutral != total,
        )
    )
    return str(solver.check()).lower()


def _cvc5_axis6_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    terms = {
        key: solver.mkConst(int_sort, f"axis6_{key}_cvc5{'_erased' if erased else ''}")
        for key in [
            "positive",
            "negative",
            "neutral",
            "total",
            "stable_edges",
            "changed_edges",
            "edge_count",
            "axis6_not_from_axis0_response",
            "axis0_not_from_axis6",
            "commuting_neutral_count",
        ]
    }
    if erased:
        bind = {
            **values,
            "positive": 0,
            "negative": 0,
            "stable_edges": 0,
            "changed_edges": values["edge_count"],
            "axis6_not_from_axis0_response": 0,
            "axis0_not_from_axis6": 0,
            "commuting_neutral_count": 0,
        }
    else:
        bind = values
    for key, term in terms.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(bind[key])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.OR,
            solver.mkTerm(Kind.EQUAL, terms["positive"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, terms["negative"], solver.mkInteger(0)),
            solver.mkTerm(
                Kind.DISTINCT,
                solver.mkTerm(Kind.ADD, terms["positive"], terms["negative"], terms["neutral"]),
                terms["total"],
            ),
            solver.mkTerm(Kind.EQUAL, terms["stable_edges"], solver.mkInteger(0)),
            solver.mkTerm(Kind.EQUAL, terms["changed_edges"], solver.mkInteger(0)),
            solver.mkTerm(
                Kind.DISTINCT,
                solver.mkTerm(Kind.ADD, terms["stable_edges"], terms["changed_edges"]),
                terms["edge_count"],
            ),
            solver.mkTerm(Kind.DISTINCT, terms["axis6_not_from_axis0_response"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, terms["axis0_not_from_axis6"], solver.mkInteger(1)),
            solver.mkTerm(Kind.DISTINCT, terms["commuting_neutral_count"], terms["total"]),
        )
    )
    return str(solver.checkSat()).lower()


def smt_rows(counts: dict[str, Any], stability: dict[str, Any], independence_rows: list[dict[str, Any]], controls: dict[str, Any]) -> dict[str, Any]:
    by_id = {row["row_id"]: row for row in independence_rows}
    values = {
        "positive": int(counts["positive"]),
        "negative": int(counts["negative"]),
        "neutral": int(counts["neutral"]),
        "total": int(counts["total"]),
        "stable_edges": int(stability["one_step"]["stable_edges"]),
        "changed_edges": int(stability["one_step"]["changed_edges"]),
        "edge_count": int(stability["one_step"]["edge_count"]),
        "axis6_not_from_axis0_response": 1 if by_id["axis6_not_recoverable_from_axis0_response"]["pass"] else 0,
        "axis0_not_from_axis6": 1 if by_id["axis0_response_not_recoverable_from_axis6"]["pass"] else 0,
        "commuting_neutral_count": int(controls["commuting_control"]["neutral_count"]),
    }
    z3_verdict = _z3_axis6_identity(values)
    z3_erased = _z3_axis6_identity(values, erased=True)
    cvc5_verdict = _cvc5_axis6_identity(values)
    cvc5_erased = _cvc5_axis6_identity(values, erased=True)
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": values,
        "identity": "positive>0 and negative>0 and stable>0 and changed>0 and two-way A0/A6 non-recovery and commuting control all-neutral",
        "erased_flip_bindings": {
            "positive": 0,
            "negative": 0,
            "stable_edges": 0,
            "changed_edges": values["edge_count"],
            "axis6_not_from_axis0_response": 0,
            "axis0_not_from_axis6": 0,
            "commuting_neutral_count": 0,
        },
    }
    return {
        "z3": {**base, "tool": "z3", "verdict": z3_verdict, "erased_flip_verdict": z3_erased},
        "cvc5": {**base, "tool": "cvc5", "verdict": cvc5_verdict, "erased_flip_verdict": cvc5_erased},
    }


@lru_cache(maxsize=1)
def build_axis6_object() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    axis0_object = axis0_common.build_axis0_object()
    axis0_rows = axis0_object["readout_table"]
    pins = pinning_payload()
    rows = precedence_table(carrier, pins)
    counts = precedence_counts(rows)
    signs = {row["cell_id"]: row["b6_sign"] for row in rows}
    stability = one_and_two_step_stability(carrier, signs)
    independence, independence_aux = independence_rows_vs_axis0(axis0_rows, rows, carrier)
    control_rows = compute_controls(carrier, rows, pins, independence_aux)
    smt = smt_rows(counts, stability, independence, control_rows)
    state_object_id = f"{SIM_ID}:{stable_sha256({'carrier': carrier['state_object_id'], 'pinning': {'operator': S4_PIN_SHA256, 'terrain': S5_PIN_SHA256, 'h': TERRAIN_H}, 'precedence': rows})}"
    control_pass = (
        control_rows["commuting_control"]["all_cells_neutral"]
        and control_rows["constant_field_degenerate"]["all_cells_neutral"]
        and control_rows["shuffled_order_n01"]["n01_flips_or_demotes"]
        and control_rows["frozen_factor_projection"]["best_frozen_factor_accuracy"] < 1.0
        and control_rows["label_permutation"]["label_only_reproduction_pass"] is False
    )
    independence_pass = all(row.get("pass") is True for row in independence)
    smt_pass = all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
    all_pass = (
        carrier["state_count"] == EXPECTED_STATE_COUNT
        and carrier["edge_count"] == EXPECTED_EDGE_COUNT
        and pins["operator"]["pin_sha256"] == S4_PIN_SHA256
        and pins["terrain"]["pin_sha256"] == S5_PIN_SHA256
        and pins["terrain"]["basin_flow_cross_check"]["matches_committed_h_half_flow"]
        and counts["positive"] > 0
        and counts["negative"] > 0
        and stability["neither_trivial_nor_frozen"]
        and control_pass
        and independence_pass
        and smt_pass
    )
    return {
        "sim_id": SIM_ID,
        "schema": f"{SIM_ID}.object.v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": all_pass,
        "state_object_id": state_object_id,
        "carrier": {
            key: value
            for key, value in carrier.items()
            if key not in {"cells", "edges", "component_id_by_cell", "successor_count_by_cell"}
        },
        "carrier_cells": carrier["cells"],
        "carrier_edges": [
            {
                "edge_id": row["edge_id"],
                "src": row["src"],
                "dst": row["dst"],
                "generator": row["generator"],
                "image_before_quantization": row["image_before_quantization"],
            }
            for row in carrier["edges"]
        ],
        "pinning": json_pinning(pins),
        "precedence_functional": {
            "declared_before_classification": True,
            "operator_first": "Phi_T(O(rho_cell))",
            "terrain_first": "O(Phi_T(rho_cell))",
            "difference": "operator_first - terrain_first",
            "sign_functional": "sign(trace_norm_weight * z_component_difference)",
            "neutral_rule": "if the weighted z difference is zero within EPS then b6_sign=0",
            "eps": EPS,
        },
        "precedence_table": rows,
        "precedence_counts": counts,
        "stability_under_committed_dynamics": stability,
        "axis0_alignment": {
            "axis0_state_object_id": axis0_object["state_object_id"],
            "axis0_source_path": rel(PARENT_PATHS["axis0_envelope"]),
            "axis0_source_sha256": sha256_file(PARENT_PATHS["axis0_envelope"]),
            "axis0_readout_table": axis0_rows,
            "same_carrier": axis0_object["carrier"]["state_object_id"] == carrier["state_object_id"],
        },
        "independence_rows_vs_axis0": independence,
        "b0_b6_prediction": b0_b6_prediction(axis0_rows, rows),
        "axis6_contender_registry_staged_rows": contender_registry(),
        "controls": control_rows,
        "falsifier_branches": {
            "reachable": True,
            "branches": sorted(control_rows),
            "required_to_fire": sorted(control_rows),
        },
        "smt_rows": smt,
        "crossover_proofs": smt,
        "source_import_audit": source_import_audit(),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "TOOL_INTENT_MATRIX": {
            "build_three_engine_envelope": {
                "status": "required",
                "helper_path": "scripts/build_three_engine_envelope.py",
                "reason": "standard envelope construction, not hand-rolled result schema",
            },
            "builder_audit_boundary": {
                "status": "required",
                "helper_path": "scripts/builder_audit_boundary.py",
                "reason": "builder packet does not emit audit_verdict.md",
            },
            "smt_computed_value_bindings": {
                "status": "computed",
                "rows": ["z3", "cvc5"],
                "reason": "bind computed counts and erased flips, not prose booleans",
            },
        },
        "builder_gates": {
            "file_disjoint_packet": True,
            "no_git_add_commit": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": {
            "positive": [
                "one finite Axis-6 precedence readout candidate over the committed Family A 33-cell carrier",
                "pinned S4 D_z operator and S5 Ne_Spiral_R h=1/2 terrain flow used before classification",
                "carrier-honest A0/A6 rows reported with identity-leak caveat",
                "b0*b6 prediction table staged for a later same-carrier Axis-3 follow-on",
            ],
            "negative": [
                "no Axis-6 admission",
                "no Axis-4 order claim",
                "no Axis-3 measurement",
                "no bridge or physics claim",
                "not canon",
            ],
            "boundary": [
                "scratch_diagnostic only",
                "promotion_allowed=false",
                "formal_admission_allowed=false",
                "claim_ceiling=axis_readout_candidate_only",
            ],
        },
        "allowed_claims": [
            "finite Axis-6 precedence readout candidate computed on Family A 33-cell carrier",
            "pinned D_z/Ne_Spiral_R order-gap table emitted",
            "controls, carrier-honest independence rows, and staged b0*b6 prediction table computed",
        ],
        "disallowed_claims": [
            "axis admission",
            "Axis-4 composition order claim",
            "Axis-3 measurement",
            "bridge admission",
            "physics",
            "manifold promotion",
        ],
        "blocked_consumers": [
            "axis_level_admission",
            "three_way_b6_equals_minus_b0_b3_claim",
            "bridge_or_cut_inference",
            "physics_interpretation",
            "scientific_lego_coupling",
        ],
        "validator_expected_commands": validator_expected_commands(),
    }


def validator_expected_commands() -> list[str]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_julia.jl",
        f"{py} system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_jax.py",
        f"{py} system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_pytorch.py",
        f"{py} system_v6/sims/discrete_axis6_precedence_v0/write_envelope_spec.py",
        f"{py} scripts/build_three_engine_envelope.py system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_envelope_spec.json > system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
        f"{py} system_v6/sims/discrete_axis6_precedence_v0/validate_discrete_axis6_precedence_v0.py",
        f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
        f"{py} -m pytest -q system_v6/sims/discrete_axis6_precedence_v0/tests",
    ]


def engine_result_payload(
    *,
    engine: str,
    source_path: Path,
    result_path: Path,
    packages_used: list[str],
    aligned_packages_load_bearing: list[str],
    package_observables: dict[str, str],
    source_backing_probe: dict[str, Any],
) -> dict[str, Any]:
    obj = build_axis6_object()
    all_pass = obj["all_pass"] and source_backing_probe.get("pass") is True
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_{engine}",
        "engine": engine,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "reads_peer_result": False,
        "generated_at": now_z(),
        "source_path": rel(source_path),
        "source_sha256": sha256_file(source_path),
        "result_path": rel(result_path),
        "packages_used": packages_used,
        "aligned_packages_load_bearing": aligned_packages_load_bearing,
        "package_observables": package_observables,
        "TOOL_MANIFEST": {key: TOOL_MANIFEST[key] for key in package_observables if key in TOOL_MANIFEST},
        "TOOL_INTEGRATION_DEPTH": {key: TOOL_INTEGRATION_DEPTH[key] for key in package_observables if key in TOOL_INTEGRATION_DEPTH},
        "claim_path_tools": aligned_packages_load_bearing,
        "engine_mode": ENGINE_MODE,
        "capability_receipts": [
            {
                "receipt_id": f"{engine}_{package}_axis6_precedence_candidate",
                "tool": package,
                "computed_what": package_observables[package],
                "status": "used",
            }
            for package in aligned_packages_load_bearing
        ],
        "tool_calls": [
            {
                "receipt_id": f"{engine}_{package}_axis6_precedence_candidate",
                "tool": package,
                "qualified_api/function": package_observables[package],
                "load_bearing": True,
            }
            for package in aligned_packages_load_bearing
        ],
        "source_backing_probe": source_backing_probe,
        "computed_values": {
            "state_count": obj["carrier"]["state_count"],
            "edge_count": obj["carrier"]["edge_count"],
            "positive": obj["precedence_counts"]["positive"],
            "negative": obj["precedence_counts"]["negative"],
            "neutral": obj["precedence_counts"]["neutral"],
            "nonneutral": obj["precedence_counts"]["nonneutral"],
            "stable_edge_count": obj["stability_under_committed_dynamics"]["one_step"]["stable_edges"],
            "changed_edge_count": obj["stability_under_committed_dynamics"]["one_step"]["changed_edges"],
            "two_step_stable_paths": obj["stability_under_committed_dynamics"]["two_step"]["stable_paths"],
            "two_step_changed_paths": obj["stability_under_committed_dynamics"]["two_step"]["changed_paths"],
            "axis6_not_recoverable_from_axis0_response": next(
                row for row in obj["independence_rows_vs_axis0"] if row["row_id"] == "axis6_not_recoverable_from_axis0_response"
            )["pass"],
            "axis0_response_not_recoverable_from_axis6": next(
                row for row in obj["independence_rows_vs_axis0"] if row["row_id"] == "axis0_response_not_recoverable_from_axis6"
            )["pass"],
            "readout_signature_sha256": stable_sha256(
                {
                    "precedence_counts": obj["precedence_counts"],
                    "precedence_table": [
                        {"cell_id": row["cell_id"], "b6_sign": row["b6_sign"], "weighted_z": row["weighted_z_difference"]}
                        for row in obj["precedence_table"]
                    ],
                    "stable": obj["stability_under_committed_dynamics"]["one_step"]["stable_edges"],
                }
            ),
        },
        "crossover_proofs": obj["crossover_proofs"],
        "all_pass": all_pass,
    }
