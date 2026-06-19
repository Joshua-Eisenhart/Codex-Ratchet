#!/usr/bin/env python3
"""Shared builder for axis_triple_consistency_b6_v0.

The relation is checked after b0, b3, and b6 are computed separately on the
pinned Hopf sample. Violations are part of the result, not validator failures.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
from scipy.linalg import expm
import sympy as sp
import z3


SIM_ID = "axis_triple_consistency_b6_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only + consistency_row_only"
ENGINE_MODE = "all_three_full_sims"
SAMPLE_COUNT = 8
EPS = 1.0e-10
PRIMARY_OPERATOR = "D_z"
PRIMARY_TERRAIN = "Ne_Spiral_R"
TERRAIN_H = "1/2"
S4_PIN_SHA256 = "0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566"
S5_PIN_SHA256 = "ced1d4a8395b66077defbfa44dade651cac9c02ef7ea95cca9918a4019b0634a"
INDEPENDENCE_REMINDER_ROW = (
    "consistency != independence; agreement supports only a consistency row and cannot prove axis independence."
)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


PARENT_COMMITS = {
    "axis_work_order": "f6112e407",
    "panel6": "eba5fdca0",
    "axis0": "5d330b427",
    "axis3": "ce8c77355",
    "axis6": "b6fafc67f",
}
PARENT_PATHS = {
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "panel6": ROOT / "system_v6/receipts/cross_model_anchor_recompute_panel6_20260612.md",
    "working_math_scaffold": ROOT / "system_v6/foundations/working_math_scaffold_20260609.md",
    "symbolic_layer": ROOT / "system_v6/foundations/symbolic_layer_iching_taijitu_20260609.md",
    "axis_deep_math": ROOT / "system_v5/ops/AXES_0_6_DEEP_MATH_DEFINITIONS_20260522.md",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "axis0_common": ROOT / "system_v6/sims/discrete_axis0_field_v0/discrete_axis0_field_v0_common.py",
    "axis3_envelope": ROOT / "system_v6/sims/discrete_axis3_placement_v0/results/discrete_axis3_placement_v0_envelope_results.json",
    "axis3_common": ROOT / "system_v6/sims/discrete_axis3_placement_v0/discrete_axis3_placement_v0_common.py",
    "axis6_envelope": ROOT / "system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
    "axis6_common": ROOT / "system_v6/sims/discrete_axis6_precedence_v0/discrete_axis6_precedence_v0_common.py",
    "geo_s4_envelope": ROOT / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "geo_s5_envelope": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
}

TOOL_INTENT = {
    "claim_classes": [
        "axis0_axis3_axis6_computed_consistency_row",
        "hopf_carrier_axis_readout_candidate_only",
        "computed_panel_point_check",
        "computed_negative_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "build a finite Hopf sample graph whose rows carry independently computed b0, b3, b6 signs",
            "Z3": "bind computed agreement and violation counts with an erased-flip satisfiable control",
        },
        "jax": {
            "jax": "enable x64 and device-get the independently recomputed Hopf table counts",
            "jax.numpy": "vectorize b0, b3, and b6 sign computations over the Hopf sample",
            "jax.scipy.linalg": "compute the Ne flow matrix from the pinned generator by expm",
            "sympy": "exactly check the panel arithmetic signs before numeric JAX evaluation",
            "z3": "bind computed agreement and violation counts with an erased-flip satisfiable control",
            "cvc5": "independently bind the same computed count row and erased flip",
        },
        "pytorch": {
            "torch.func": "torch-native vmap recomputation of the D_z/Ne precedence sign over Hopf rows",
            "torch_geometric": "Data edge_index carrier for the finite sample/control relation graph",
            "sympy": "exactly check the panel arithmetic signs mirrored in the PyTorch lane",
            "z3": "bind computed agreement and violation counts with an erased-flip satisfiable control",
            "cvc5": "independently bind the same computed count row and erased flip",
        },
    },
}
TOOL_MANIFEST = {
    "build_three_engine_envelope": {
        "tried": True,
        "used": True,
        "reason": "load-bearing standard envelope construction; this packet does not hand-roll three_engine_sim_result_v1",
    },
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite Hopf sample graph and row counts"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT computed count identity and erased flip"},
    "jax": {"tried": True, "used": True, "reason": "JAX x64 independent vector recomputation"},
    "jax.numpy": {"tried": True, "used": True, "reason": "JAX finite sign arithmetic over Hopf rows"},
    "jax.scipy.linalg": {"tried": True, "used": True, "reason": "JAX matrix exponential for pinned terrain flow"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized precedence recomputation"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch finite relation graph carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact panel arithmetic rows"},
    "z3": {"tried": True, "used": True, "reason": "Python SMT computed count identity and erased flip"},
    "cvc5": {"tried": True, "used": True, "reason": "independent Python SMT computed count identity and erased flip"},
}
TOOL_INTEGRATION_DEPTH = {
    "build_three_engine_envelope": "load_bearing",
    "Graphs": "load_bearing",
    "Z3": "load_bearing",
    "jax": "load_bearing",
    "jax.numpy": "load_bearing",
    "jax.scipy.linalg": "load_bearing",
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


def sign(value: float) -> int:
    return 1 if value > EPS else -1 if value < -EPS else 0


def round_float(value: float, digits: int = 15) -> float:
    if abs(value) < EPS:
        return 0.0
    return round(float(value), digits)


def round_vec(values: np.ndarray | list[float], digits: int = 15) -> list[float]:
    return [round_float(float(value), digits) for value in values]


def source_import_audit() -> dict[str, Any]:
    return {
        "authority_and_context": {
            "axis_work_order": source_lock(PARENT_PATHS["axis_work_order"], "authority_relation_row", PARENT_COMMITS["axis_work_order"]),
            "panel6": source_lock(PARENT_PATHS["panel6"], "blind_panel_q2_expected_values", PARENT_COMMITS["panel6"]),
            "working_math_scaffold": source_lock(PARENT_PATHS["working_math_scaffold"], "scaffold_axis_definitions"),
            "symbolic_layer": source_lock(PARENT_PATHS["symbolic_layer"], "scaffold_relation_context"),
            "axis_deep_math": source_lock(PARENT_PATHS["axis_deep_math"], "chart_role_convention_context"),
        },
        "parent_hash_pins": {
            "axis0_envelope": source_lock(PARENT_PATHS["axis0_envelope"], "committed_axis0_packet", PARENT_COMMITS["axis0"]),
            "axis0_common": source_lock(PARENT_PATHS["axis0_common"], "committed_axis0_source", PARENT_COMMITS["axis0"]),
            "axis3_envelope": source_lock(PARENT_PATHS["axis3_envelope"], "committed_axis3_packet", PARENT_COMMITS["axis3"]),
            "axis3_common": source_lock(PARENT_PATHS["axis3_common"], "committed_axis3_source", PARENT_COMMITS["axis3"]),
            "axis6_envelope": source_lock(PARENT_PATHS["axis6_envelope"], "committed_axis6_packet", PARENT_COMMITS["axis6"]),
            "axis6_common": source_lock(PARENT_PATHS["axis6_common"], "committed_axis6_source", PARENT_COMMITS["axis6"]),
            "geo_s4_envelope": source_lock(PARENT_PATHS["geo_s4_envelope"], "committed_D_z_operator_pin"),
            "geo_s5_envelope": source_lock(PARENT_PATHS["geo_s5_envelope"], "committed_Ne_flow_pin"),
        },
        "raw_parent_result_rows_imported": False,
        "anti_by_construction_rule": "b0, b3, and b6 are computed from separate formula lanes; the relation row is evaluated after the signs exist and can fail.",
    }


@lru_cache(maxsize=1)
def pinning_payload() -> dict[str, Any]:
    s4 = load_json(PARENT_PATHS["geo_s4_envelope"])
    s5 = load_json(PARENT_PATHS["geo_s5_envelope"])
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
    return {
        "operator": {
            "name": PRIMARY_OPERATOR,
            "source_path": rel(PARENT_PATHS["geo_s4_envelope"]),
            "pin_sha256": s4.get("pin_sha256"),
            "pin_matches_committed_hash": s4.get("pin_sha256") == S4_PIN_SHA256,
            "symbolic": operator_row.get("symbolic"),
            "pinned": operator_row.get("pinned"),
            "M": op_m,
            "c": op_c,
        },
        "terrain": {
            "name": PRIMARY_TERRAIN,
            "h": TERRAIN_H,
            "source_path": rel(PARENT_PATHS["geo_s5_envelope"]),
            "pin_sha256": s5.get("pin_sha256"),
            "pin_matches_committed_hash": s5.get("pin_sha256") == S5_PIN_SHA256,
            "symbolic": terrain_row.get("symbolic"),
            "pinned_generator": terrain_row.get("pinned"),
            "M": flow[:3, :3],
            "c": flow[:3, 3],
        },
    }


def json_pinning(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "operator": {
            key: value
            for key, value in payload["operator"].items()
            if key not in {"M", "c"}
        }
        | {"M": [round_vec(row) for row in payload["operator"]["M"]], "c": round_vec(payload["operator"]["c"])},
        "terrain": {
            key: value
            for key, value in payload["terrain"].items()
            if key not in {"M", "c"}
        }
        | {"M": [round_vec(row) for row in payload["terrain"]["M"]], "c": round_vec(payload["terrain"]["c"])},
    }


def phi_value(index: int) -> float:
    return 2.0 * math.pi * index / SAMPLE_COUNT


def chi_value(index: int) -> float:
    return 2.0 * math.pi * index / SAMPLE_COUNT


def eta_rows() -> list[dict[str, Any]]:
    return [
        {"eta_slot": 0, "eta_label": "pi/8", "eta": math.pi / 8.0},
        {"eta_slot": 1, "eta_label": "pi/4", "eta": math.pi / 4.0},
        {"eta_slot": 2, "eta_label": "3*pi/8", "eta": 3.0 * math.pi / 8.0},
    ]


def axis3_sample_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sheet_index, sheet in enumerate(["L", "R"]):
        for eta in eta_rows():
            for phi_index in [0, 2]:
                for chi_index in [0, 1]:
                    for family in ["gamma_in", "gamma_out"]:
                        placement = "fiber" if family == "gamma_in" else "lifted_base"
                        committed_sign = -1 if family == "gamma_in" else 1
                        primary_b3 = 1 if placement == "fiber" else -1
                        chart_role_sign = chart_role_b3_sign(sheet, placement)
                        carrier_row_id = (((sheet_index * 3 + eta["eta_slot"]) * SAMPLE_COUNT + phi_index) * SAMPLE_COUNT + chi_index)
                        rows.append(
                            {
                                "sample_id": f"{SIM_ID}:{sheet}:eta{eta['eta_slot']}:phi{phi_index}:chi{chi_index}:{family}",
                                "source_axis3_loop_id": f"discrete_axis3_placement_v0:{sheet}:eta{eta['eta_slot']}:phi{phi_index}:chi{chi_index}:{family}",
                                "sheet": sheet,
                                "sheet_index": sheet_index,
                                "eta_slot": eta["eta_slot"],
                                "eta_label": eta["eta_label"],
                                "eta": eta["eta"],
                                "phi_index": phi_index,
                                "chi_index": chi_index,
                                "phi0": phi_value(phi_index),
                                "chi0": chi_value(chi_index),
                                "pinned_family_formula": family,
                                "axis3_geometry_path": placement,
                                "axis3_committed_placement_sign": committed_sign,
                                "axis3_committed_label": "axis3_minus_fiber_placed_gamma_in"
                                if family == "gamma_in"
                                else "axis3_plus_base_placed_gamma_out",
                                "primary_b3_convention": "panel_fiber_plus_base_minus",
                                "b3_sign": primary_b3,
                                "b3_sign_flipped": -primary_b3,
                                "chart_role_b3_sign_context_only": chart_role_sign,
                                "family_b_carrier_row_id": carrier_row_id,
                            }
                        )
    return rows


def chart_role_b3_sign(sheet: str, placement: str) -> int:
    if sheet == "L":
        return -1 if placement == "fiber" else 1
    return 1 if placement == "fiber" else -1


def bloch_vector(chi: float, eta: float) -> np.ndarray:
    return np.asarray(
        [
            math.sin(2.0 * eta) * math.cos(2.0 * chi),
            math.sin(2.0 * eta) * math.sin(2.0 * chi),
            math.cos(2.0 * eta),
        ],
        dtype=float,
    )


def axis0_b0_sign(eta: float) -> int:
    return sign(math.cos(2.0 * eta))


def apply_affine(matrix: np.ndarray, offset: np.ndarray, r: np.ndarray) -> np.ndarray:
    return matrix @ r + offset


def precedence_from_bloch(r: np.ndarray, pinning: dict[str, Any]) -> dict[str, Any]:
    operator = pinning["operator"]
    terrain = pinning["terrain"]
    op_first = apply_affine(terrain["M"], terrain["c"], apply_affine(operator["M"], operator["c"], r))
    terrain_first = apply_affine(operator["M"], operator["c"], apply_affine(terrain["M"], terrain["c"], r))
    delta = op_first - terrain_first
    trace_norm_weight = float(np.linalg.norm(delta, ord=2))
    z_component_difference = float(delta[2])
    weighted_z_difference = trace_norm_weight * z_component_difference
    b6 = sign(weighted_z_difference)
    return {
        "operator_first_expression": "Phi_T(O(rho))",
        "terrain_first_expression": "O(Phi_T(rho))",
        "operator_first_bloch": round_vec(op_first),
        "terrain_first_bloch": round_vec(terrain_first),
        "bloch_difference_operator_first_minus_terrain_first": round_vec(delta),
        "z_component_difference": round_float(z_component_difference),
        "trace_norm_weight": round_float(trace_norm_weight),
        "weighted_z_difference": round_float(weighted_z_difference),
        "b6_sign": b6,
        "b6_label": {1: "operator_first_precedence", -1: "terrain_first_precedence", 0: "neutral"}[b6],
    }


def consistency_row(row: dict[str, Any], pinning: dict[str, Any]) -> dict[str, Any]:
    b0 = axis0_b0_sign(float(row["eta"]))
    b3 = int(row["b3_sign"])
    bloch = bloch_vector(float(row["chi0"]), float(row["eta"]))
    b6 = precedence_from_bloch(bloch, pinning)
    expected = -(b0 * b3)
    flipped_expected = b0 * b3
    return {
        **{key: value for key, value in row.items() if key not in {"eta", "phi0", "chi0"}},
        "eta_float": float(row["eta"]),
        "phi0": float(row["phi0"]),
        "chi0": float(row["chi0"]),
        "bloch_vector": round_vec(bloch),
        "b0_source": "sign(cos 2eta)",
        "b0_sign": b0,
        "b3_source": "panel_fiber_plus_base_minus applied to committed axis3 fiber/base classification",
        "b3_sign": b3,
        "b6_source": "committed D_z analog and Ne_Spiral_R h=1/2 precedence functional on Hopf Bloch state",
        "computed_b6_sign": int(b6["b6_sign"]),
        "expected_b6_negative_b0_b3": int(expected),
        "relation_holds": int(b6["b6_sign"]) == int(expected),
        "flipped_convention_expected_b6_positive_b0_b3": int(flipped_expected),
        "relation_can_fail_here": int(b6["b6_sign"]) != int(expected),
        "anti_by_construction_guard": "b0, b3, and b6 are stored before this relation check; no row reads the expected value while computing b6.",
        **b6,
    }


def build_consistency_table() -> list[dict[str, Any]]:
    pinning = pinning_payload()
    return [consistency_row(row, pinning) for row in axis3_sample_rows()]


def panel_point_rows() -> list[dict[str, Any]]:
    pinning = pinning_payload()
    rows = [
        {
            "panel_point_id": "panel6_q2_eta_pi_over_6_fiber",
            "eta_label": "pi/6",
            "eta": math.pi / 6.0,
            "placement": "fiber",
            "b3_sign": 1,
            "chi0": 0.0,
            "panel_expected_b6": -1,
            "panel_source": "cross_model_anchor_recompute_panel6_20260612.md:11",
        },
        {
            "panel_point_id": "panel6_q2_eta_pi_over_3_base",
            "eta_label": "pi/3",
            "eta": math.pi / 3.0,
            "placement": "base",
            "b3_sign": -1,
            "chi0": 0.0,
            "panel_expected_b6": -1,
            "panel_source": "cross_model_anchor_recompute_panel6_20260612.md:11",
        },
    ]
    out = []
    for row in rows:
        b0 = axis0_b0_sign(float(row["eta"]))
        bloch = bloch_vector(float(row["chi0"]), float(row["eta"]))
        b6 = precedence_from_bloch(bloch, pinning)
        expected = -(b0 * int(row["b3_sign"]))
        out.append(
            {
                **{key: value for key, value in row.items() if key != "eta"},
                "eta_float": float(row["eta"]),
                "bloch_vector": round_vec(bloch),
                "b0_sign": b0,
                "b3_sign": int(row["b3_sign"]),
                "expected_b6_negative_b0_b3": expected,
                "computed_b6_sign": int(b6["b6_sign"]),
                "matches_panel_expected": int(b6["b6_sign"]) == int(row["panel_expected_b6"]),
                "matches_relation_expected": int(b6["b6_sign"]) == expected,
                **b6,
            }
        )
    return out


def consistency_summary(table: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(table)
    agreement = sum(1 for row in table if row["relation_holds"])
    nonneutral = [row for row in table if row["expected_b6_negative_b0_b3"] != 0]
    nonneutral_agreement = sum(1 for row in nonneutral if row["relation_holds"])
    return {
        "sample_total": total,
        "agreement_count": agreement,
        "violation_count": total - agreement,
        "agreement_fraction": agreement / total if total else 0.0,
        "nonneutral_total": len(nonneutral),
        "nonneutral_agreement_count": nonneutral_agreement,
        "nonneutral_violation_count": len(nonneutral) - nonneutral_agreement,
        "nonneutral_agreement_fraction": nonneutral_agreement / len(nonneutral) if nonneutral else 0.0,
        "neutral_expected_count": total - len(nonneutral),
        "claim_language": "computed consistency table; violations are reported verbatim and block theorem/admission language",
    }


def violation_rows(table: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "sample_id": row["sample_id"],
            "sheet": row["sheet"],
            "eta_label": row["eta_label"],
            "phi_index": row["phi_index"],
            "chi_index": row["chi_index"],
            "axis3_geometry_path": row["axis3_geometry_path"],
            "b0_sign": row["b0_sign"],
            "b3_sign": row["b3_sign"],
            "computed_b6_sign": row["computed_b6_sign"],
            "expected_b6_negative_b0_b3": row["expected_b6_negative_b0_b3"],
            "weighted_z_difference": row["weighted_z_difference"],
        }
        for row in table
        if not row["relation_holds"]
    ]


def scrambled_sign(sample_id: str) -> int:
    digest = hashlib.sha256(f"{sample_id}|scrambled-b6-control".encode("utf-8")).digest()
    return 1 if digest[0] % 2 == 0 else -1


def controls(table: list[dict[str, Any]]) -> dict[str, Any]:
    nonzero_expected = [row for row in table if row["expected_b6_negative_b0_b3"] != 0]
    scrambled_rows = []
    for row in table:
        scrambled = scrambled_sign(row["sample_id"])
        expected = row["expected_b6_negative_b0_b3"]
        scrambled_rows.append(
            {
                "sample_id": row["sample_id"],
                "scrambled_b6_sign": scrambled,
                "expected_b6_negative_b0_b3": expected,
                "scrambled_matches_expected": scrambled == expected,
            }
        )
    scrambled_nonneutral = [row for row in scrambled_rows if row["expected_b6_negative_b0_b3"] != 0]
    commuting = [precedence_from_bloch(np.asarray(row["bloch_vector"], dtype=float), {"operator": pinning_payload()["operator"], "terrain": pinning_payload()["operator"]}) for row in table]
    return {
        "convention_flip_control": {
            "description": "flip b3 sign convention; the algebraic target changes from b6=-b0*b3 to b6=+b0*b3 under the original b3 labels",
            "all_flipped_expected_equals_positive_product": all(
                row["flipped_convention_expected_b6_positive_b0_b3"] == row["b0_sign"] * row["b3_sign"]
                for row in table
            ),
            "flipped_relation_agreement_count": sum(
                row["computed_b6_sign"] == row["flipped_convention_expected_b6_positive_b0_b3"] for row in table
            ),
            "flipped_relation_agreement_fraction": sum(
                row["computed_b6_sign"] == row["flipped_convention_expected_b6_positive_b0_b3"] for row in table
            )
            / len(table),
        },
        "scrambled_b6_control": {
            "description": "replace computed b6 with deterministic sha256 noise; agreement should drop to chance-scale rather than certify the relation",
            "agreement_count_all_rows": sum(row["scrambled_matches_expected"] for row in scrambled_rows),
            "agreement_fraction_all_rows": sum(row["scrambled_matches_expected"] for row in scrambled_rows) / len(scrambled_rows),
            "agreement_count_nonzero_expected": sum(row["scrambled_matches_expected"] for row in scrambled_nonneutral),
            "agreement_fraction_nonzero_expected": sum(row["scrambled_matches_expected"] for row in scrambled_nonneutral)
            / len(scrambled_nonneutral),
            "rows": scrambled_rows,
        },
        "commuting_control": {
            "pair": "O=D_z and Phi_T=D_z on the same Hopf Bloch states",
            "all_neutral": all(row["b6_sign"] == 0 for row in commuting),
            "neutral_count": sum(row["b6_sign"] == 0 for row in commuting),
        },
        "relation_can_fail_control": {
            "violation_count": sum(not row["relation_holds"] for row in table),
            "relation_can_fail": any(not row["relation_holds"] for row in table),
            "why_it_matters": "the observed table is not forced to satisfy b6=-b0*b3 by construction",
        },
        "independence_reminder": INDEPENDENCE_REMINDER_ROW,
    }


def _z3_count_row(summary: dict[str, Any], *, erased: bool = False) -> dict[str, Any]:
    solver = z3.Solver()
    total = z3.Int("total_erased" if erased else "total")
    agreement = z3.Int("agreement_erased" if erased else "agreement")
    violation = z3.Int("violation_erased" if erased else "violation")
    panel = z3.Int("panel_pass_erased" if erased else "panel_pass")
    if erased:
        solver.add(total == z3.IntVal(summary["sample_total"]))
        solver.add(agreement == z3.IntVal(summary["sample_total"]))
        solver.add(violation == z3.IntVal(0))
        solver.add(panel == z3.IntVal(2))
    else:
        solver.add(total == z3.IntVal(summary["sample_total"]))
        solver.add(agreement == z3.IntVal(summary["agreement_count"]))
        solver.add(violation == z3.IntVal(summary["violation_count"]))
        solver.add(panel == z3.IntVal(2))
    solver.add(total == agreement)
    solver.add(violation == z3.IntVal(0))
    status = solver.check()
    return {"status": str(status)}


def _cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(int(value))


def _cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def _cvc5_count_row(summary: dict[str, Any], *, erased: bool = False) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    total = solver.mkConst(integer, "total_erased" if erased else "total")
    agreement = solver.mkConst(integer, "agreement_erased" if erased else "agreement")
    violation = solver.mkConst(integer, "violation_erased" if erased else "violation")
    panel = solver.mkConst(integer, "panel_pass_erased" if erased else "panel_pass")
    total_value = summary["sample_total"]
    agreement_value = summary["sample_total"] if erased else summary["agreement_count"]
    violation_value = 0 if erased else summary["violation_count"]
    panel_value = 2
    for var, value in ((total, total_value), (agreement, agreement_value), (violation, violation_value), (panel, panel_value)):
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, var, _cvc5_int(solver, value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, total, agreement))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, violation, _cvc5_int(solver, 0)))
    return {"status": _cvc5_status(solver.checkSat())}


def smt_rows(summary: dict[str, Any]) -> dict[str, Any]:
    z3_real = _z3_count_row(summary, erased=False)
    z3_erased = _z3_count_row(summary, erased=True)
    cvc5_real = _cvc5_count_row(summary, erased=False)
    cvc5_erased = _cvc5_count_row(summary, erased=True)
    base = {
        "ran": True,
        "load_bearing": True,
        "bound_total": summary["sample_total"],
        "bound_agreement_count": summary["agreement_count"],
        "bound_violation_count": summary["violation_count"],
        "bound_panel_pass_count": 2,
        "claim": "with the computed table bound, the stronger no-violation/full-agreement claim is UNSAT; erasing violations makes it SAT",
        "asserted_precomputed_boolean": False,
    }
    return {
        "z3_computed_table": {**base, "solver": "z3", "verdict": z3_real["status"], "erased_flip_verdict": z3_erased["status"]},
        "cvc5_computed_table": {
            **base,
            "solver": "cvc5",
            "verdict": cvc5_real["status"],
            "erased_flip_verdict": cvc5_erased["status"],
        },
    }


def build_axis_triple_object() -> dict[str, Any]:
    table = build_consistency_table()
    summary = consistency_summary(table)
    panel = panel_point_rows()
    ctrl = controls(table)
    rows = smt_rows(summary)
    all_pass = bool(
        len(table) == 48
        and summary["agreement_count"] == 16
        and summary["violation_count"] == 32
        and summary["nonneutral_agreement_count"] == 16
        and all(row["computed_b6_sign"] == -1 and row["matches_panel_expected"] for row in panel)
        and ctrl["convention_flip_control"]["all_flipped_expected_equals_positive_product"]
        and ctrl["scrambled_b6_control"]["agreement_fraction_nonzero_expected"] <= 0.75
        and ctrl["commuting_control"]["all_neutral"]
        and all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in rows.values())
    )
    return {
        "schema": f"{SIM_ID}.axis_triple_object.v1",
        "sim_id": SIM_ID,
        "state_object_id": f"{SIM_ID}:hopf_axis_0_3_6_consistency_table",
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "source_import_audit": source_import_audit(),
        "pinned_pair": json_pinning(pinning_payload()),
        "carrier_decision": {
            "decision": "Hopf carrier hosts all three readouts natively enough for this consistency row.",
            "compromise": "b6 is realized as the committed D_z/Ne precedence functional on Hopf Bloch states. The panel points match, while the wider pinned Hopf sample produces violations; this is the strongest honest shared object here.",
            "carrier": "committed axis3 Hopf loop eta values and placements",
        },
        "consistency_table": table,
        "consistency_summary": summary,
        "violation_rows": violation_rows(table),
        "panel_point_checks": panel,
        "controls": ctrl,
        "smt_rows": rows,
        "independence_reminder_row": INDEPENDENCE_REMINDER_ROW,
        "claim_sections": {
            "positive": [
                "panel q2 arithmetic is reproduced by independent b0, b3, b6 computations at eta=pi/6 fiber and eta=pi/3 base",
                "the full pinned Hopf table is computed and violation rows are explicit",
            ],
            "negative": [
                "the full pinned Hopf sample does not satisfy b6=-b0*b3 universally under the raw D_z/Ne precedence functional",
                "scrambled and convention-flip controls prevent tautology language",
            ],
            "boundary": [
                CLAIM_CEILING,
                INDEPENDENCE_REMINDER_ROW,
            ],
        },
        "allowed_claims": [
            "computed consistency row on the pinned Hopf sample",
            "panel point match under the card convention",
            "violation-bearing axis readout candidate only",
        ],
        "disallowed_claims": [
            "axis independence proof",
            "canonical cross-axis law",
            "Axis-6 admission",
            "physics/manifold theorem",
            "universal relation without naming violations",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTENT_MATRIX": {
            "julia": TOOL_INTENT["engine_tool_intent"]["julia"],
            "jax": TOOL_INTENT["engine_tool_intent"]["jax"],
            "pytorch": TOOL_INTENT["engine_tool_intent"]["pytorch"],
            "build_three_engine_envelope": TOOL_MANIFEST["build_three_engine_envelope"]["reason"],
        },
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        },
        "all_pass": all_pass,
    }


def source_result_base(engine: str, source_path: Path, result_path: Path) -> dict[str, Any]:
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
        "engine_mode": ENGINE_MODE,
    }


def engine_computed_values(obj: dict[str, Any]) -> dict[str, Any]:
    summary = obj["consistency_summary"]
    return {
        "sample_total": summary["sample_total"],
        "agreement_count": summary["agreement_count"],
        "violation_count": summary["violation_count"],
        "nonneutral_total": summary["nonneutral_total"],
        "nonneutral_agreement_count": summary["nonneutral_agreement_count"],
        "panel_pass_count": sum(row["matches_panel_expected"] for row in obj["panel_point_checks"]),
        "consistency_table_sha256": stable_sha256(obj["consistency_table"]),
        "violation_rows_sha256": stable_sha256(obj["violation_rows"]),
    }
