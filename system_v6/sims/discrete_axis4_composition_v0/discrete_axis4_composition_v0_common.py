#!/usr/bin/env python3
"""Shared builder for the Family-A Axis-4 composition readout candidate."""

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
import numpy as np
from scipy.linalg import expm
import sympy as sp
import z3


SIM_ID = "discrete_axis4_composition_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "axis_readout_candidate_only"
ENGINE_MODE = "three_engine_axis4_composition_candidate_on_family_a_33_cell_carrier"
EXPECTED_STATE_COUNT = 33
EXPECTED_EDGE_COUNT = 198
EPS = 1.0e-10
TAU_R = 1.0
TAU_C = 1.0
SMALL_U = 1.0e-3
SMALL_E = 1.0e-3
LAMBDA_DZ = 0.7
S4_PIN_SHA256 = "0d7ae0b81d7a92ba490818bb37afe2204cb905fdc43d4d58f35387e64fb72566"
PRIMARY_R = "R_x"
PRIMARY_C = "D_z"

AXIS0_DIR = ROOT / "system_v6" / "sims" / "discrete_axis0_field_v0"
AXIS6_DIR = ROOT / "system_v6" / "sims" / "discrete_axis6_precedence_v0"
SCRIPTS_DIR = ROOT / "scripts"
for import_dir in (AXIS0_DIR, AXIS6_DIR, SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import discrete_axis0_field_v0_common as axis0_common  # noqa: E402
import discrete_axis6_precedence_v0_common as axis6_common  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


PARENT_COMMITS = {
    "axis_work_order": "f6112e407",
    "panel7_q3": "1f8ddb9e1",
    "carnot_szilard_basin_cycle_v0": "ffe6e1c38",
    "discrete_axis0_field_v0": "5d330b427",
    "discrete_axis6_precedence_v0": "b6fafc67f",
    "geo_s6_stacked_flows_hopf_v0": "7dc512454",
    "dual_stack_carnot_szilard_hopf_weyl_probe": "9dad43b2b",
}
PARENT_PATHS = {
    "axis_work_order": ROOT / "system_v6/receipts/axis_work_order_20260612.md",
    "panel7_build_card": ROOT / "system_v6/sims/carnot_szilard_basin_cycle_v0/build_card.md",
    "panel7_envelope": ROOT
    / "system_v6/sims/carnot_szilard_basin_cycle_v0/results/carnot_szilard_basin_cycle_v0_envelope_results.json",
    "geo_s4_envelope": ROOT / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "axis0_envelope": ROOT / "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
    "axis6_envelope": ROOT
    / "system_v6/sims/discrete_axis6_precedence_v0/results/discrete_axis6_precedence_v0_envelope_results.json",
    "geo_s6_loop_prior": ROOT
    / "system_v6/sims/geo_s6_stacked_flows_hopf_v0/results/geo_s6_stacked_flows_hopf_v0_envelope_results.json",
    "dual_stack_prior": ROOT
    / "system_v6/sims/dual_stack_carnot_szilard_hopf_weyl_probe/results/dual_stack_carnot_szilard_hopf_weyl_probe_envelope_results.json",
    "axis6_contender_registry": ROOT / "system_v6/receipts/axis6_contender_probe_registry_20260612.md",
    "coupling_law_mine": ROOT / "system_v6/receipts/coupling_law_mining_raw_20260611.json",
}

TOOL_INTENT = {
    "claim_classes": [
        "finite_axis4_composition_readout_candidate",
        "pinned_Rx_Dz_order_gap",
        "panel7_small_stroke_2ue_commutator_control",
        "carrier_honest_axis0_axis4_and_axis6_axis4_discriminators",
        "computed_negative_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "rebuild the 33-cell carrier graph and count Axis-4 sign stability over generator edges",
            "Z3": "bind computed Axis-4 counts and commuting-control counts, then prove the negated identity unsat with erased flips sat",
        },
        "jax": {
            "networkx": "build the directed 33-cell graph and verify carrier adjacency metadata for the Axis-4 sign table",
            "sympy": "compute exact symbolic R_x/D_z generator commutator rows and the 2ue[A,B] panel form",
            "z3": "bind computed Axis-4 counts in SMT and prove nonzero identity cannot be erased",
            "cvc5": "independent SMT binding of the same computed Axis-4 counts with erased flips",
        },
        "pytorch": {
            "torch.func": "vectorized Axis-4 sign recomputation over the 33 Family-A Bloch vectors",
            "torch_geometric": "Data edge_index carrier for the committed 198 directed generator edges",
            "sympy": "exact symbolic D_z/R_x commutator source probe",
            "z3": "bind computed Axis-4 counts in SMT and prove nonzero identity cannot be erased",
            "cvc5": "independent SMT binding of the same computed Axis-4 counts with erased flips",
        },
    },
}
TOOL_MANIFEST = {
    "Graphs": {"tried": True, "used": True, "reason": "Julia finite carrier graph and Axis-4 stability counts"},
    "Z3": {"tried": True, "used": True, "reason": "Julia SMT computed-value identity and erased flip"},
    "networkx": {"tried": True, "used": True, "reason": "JAX-slot finite directed graph carrier and adjacency metadata"},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vectorized Axis-4 sign recomputation"},
    "torch_geometric": {"tried": True, "used": True, "reason": "PyTorch directed edge_index carrier"},
    "sympy": {"tried": True, "used": True, "reason": "exact symbolic generator commutator and panel-form rows"},
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
    return float(sp.N(sp.sympify(str(value), locals={"sqrt": sp.sqrt, "pi": sp.pi}), 40))


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


def round_matrix(matrix: np.ndarray, digits: int = 15) -> list[list[float]]:
    return [round_vec(row, digits) for row in matrix]


def sign_scalar(value: float) -> int:
    return 1 if value > EPS else -1 if value < -EPS else 0


def polarity_from_delta(delta: np.ndarray) -> int:
    if float(np.linalg.norm(delta, ord=2)) <= EPS:
        return 0
    for idx in (1, 2, 0):
        value = float(delta[idx])
        if abs(value) > EPS:
            return sign_scalar(value)
    return 0


def polarity_label(value: int) -> str:
    return {
        1: "deductive_positive_D_minus_I",
        -1: "inductive_positive_I_minus_D",
        0: "neutral_commuting_or_zero_gap",
    }[value]


def complex_obj(real: float, imag: float = 0.0) -> dict[str, float]:
    return {"re": round_float(real), "im": round_float(imag)}


def density_matrix_from_bloch(r: np.ndarray) -> list[list[dict[str, float]]]:
    x, y, z_coord = [float(value) for value in r]
    return [
        [complex_obj((1.0 + z_coord) / 2.0), complex_obj(x / 2.0, -y / 2.0)],
        [complex_obj(x / 2.0, y / 2.0), complex_obj((1.0 - z_coord) / 2.0)],
    ]


def first_independence_witness(rows: list[dict[str, Any]], key_name: str, target_name: str) -> dict[str, Any]:
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


def add_combo_key(rows: list[dict[str, Any]], key_name: str, fields: list[str]) -> list[dict[str, Any]]:
    combo_rows = []
    for row in rows:
        combo = dict(row)
        combo[key_name] = "|".join(f"{field}={row.get(field)}" for field in fields)
        combo_rows.append(combo)
    return combo_rows


def source_import_audit() -> dict[str, Any]:
    return {
        "authority_and_context": {
            "axis_work_order": source_lock(
                PARENT_PATHS["axis_work_order"],
                "work_order_axis4_row",
                PARENT_COMMITS["axis_work_order"],
            ),
            "panel7_build_card": source_lock(
                PARENT_PATHS["panel7_build_card"],
                "panel7_q3_leading_order_pin",
                PARENT_COMMITS["panel7_q3"],
            ),
            "coupling_law_mine": source_lock(PARENT_PATHS["coupling_law_mine"], "Phi_D_Phi_I_owner_formula_context"),
            "axis6_contender_registry": source_lock(
                PARENT_PATHS["axis6_contender_registry"],
                "axis4_axis6_never_merge_boundary_context",
            ),
        },
        "parent_hash_pins": {
            "geo_s4_envelope": source_lock(PARENT_PATHS["geo_s4_envelope"], "committed_Rx_Dz_generator_pin"),
            "axis0_envelope": source_lock(
                PARENT_PATHS["axis0_envelope"],
                "committed_axis0_family_a_carrier_and_response_rows",
                PARENT_COMMITS["discrete_axis0_field_v0"],
            ),
            "axis6_envelope": source_lock(
                PARENT_PATHS["axis6_envelope"],
                "committed_axis6_same_carrier_discriminator_parent",
                PARENT_COMMITS["discrete_axis6_precedence_v0"],
            ),
            "geo_s6_loop_prior": source_lock(
                PARENT_PATHS["geo_s6_loop_prior"],
                "committed_axis4_style_prior_art_trajectories_differ_commuting_collapses",
                PARENT_COMMITS["geo_s6_stacked_flows_hopf_v0"],
            ),
            "dual_stack_prior": source_lock(
                PARENT_PATHS["dual_stack_prior"],
                "committed_DI_gap_prior_art_context_only",
                PARENT_COMMITS["dual_stack_carnot_szilard_hopf_weyl_probe"],
            ),
            "panel7_envelope": source_lock(
                PARENT_PATHS["panel7_envelope"],
                "panel7_small_stroke_2ue_commutator_anchor",
                PARENT_COMMITS["carnot_szilard_basin_cycle_v0"],
            ),
        },
        "anti_conflation_rule": "Axis-4 here is R_x/D_z composition order over Family A; Axis-6 is imported only as a same-carrier discriminator parent.",
        "raw_parent_classification_imported": False,
    }


@lru_cache(maxsize=1)
def pinning_payload() -> dict[str, Any]:
    s4 = load_json(PARENT_PATHS["geo_s4_envelope"])
    r_row = s4["affine_channel_table"][PRIMARY_R]
    c_row = s4["affine_channel_table"][PRIMARY_C]
    committed_r = parse_matrix(r_row["pinned"]["M"])
    committed_c = parse_matrix(c_row["pinned"]["M"])
    zero = np.zeros(3, dtype=float)
    l_r = np.asarray(
        [
            [0.0, 0.0, 0.0],
            [0.0, 0.0, -math.pi / 2.0],
            [0.0, math.pi / 2.0, 0.0],
        ],
        dtype=float,
    )
    l_c = np.diag([math.log(LAMBDA_DZ), math.log(LAMBDA_DZ), 0.0])
    phi_r = expm(TAU_R * l_r)
    phi_c = expm(TAU_C * l_c)
    return {
        "source": {
            "path": rel(PARENT_PATHS["geo_s4_envelope"]),
            "sha256": sha256_file(PARENT_PATHS["geo_s4_envelope"]),
            "pin_sha256": s4.get("pin_sha256"),
        },
        "R": {
            "id": f"S4:{PRIMARY_R}",
            "name": PRIMARY_R,
            "tau": TAU_R,
            "symbolic": r_row["symbolic"],
            "committed_pinned": r_row["pinned"],
            "L": l_r,
            "M": phi_r,
            "c": zero,
            "max_abs_delta_vs_committed": float(np.max(np.abs(phi_r - committed_r))),
        },
        "C": {
            "id": f"S4:{PRIMARY_C}",
            "name": PRIMARY_C,
            "tau": TAU_C,
            "lambda": LAMBDA_DZ,
            "symbolic": c_row["symbolic"],
            "committed_pinned": c_row["pinned"],
            "L": l_c,
            "M": phi_c,
            "c": parse_vector(c_row["pinned"]["c"]),
            "max_abs_delta_vs_committed": float(np.max(np.abs(phi_c - committed_c))),
        },
    }


def json_pinning(pins: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": pins["source"],
        "R": {
            "id": pins["R"]["id"],
            "name": pins["R"]["name"],
            "tau": pins["R"]["tau"],
            "symbolic": pins["R"]["symbolic"],
            "committed_pinned": pins["R"]["committed_pinned"],
            "L": round_matrix(pins["R"]["L"]),
            "M": round_matrix(pins["R"]["M"]),
            "c": round_vec(pins["R"]["c"]),
            "max_abs_delta_vs_committed": round_float(pins["R"]["max_abs_delta_vs_committed"]),
        },
        "C": {
            "id": pins["C"]["id"],
            "name": pins["C"]["name"],
            "tau": pins["C"]["tau"],
            "lambda": pins["C"]["lambda"],
            "symbolic": pins["C"]["symbolic"],
            "committed_pinned": pins["C"]["committed_pinned"],
            "L": round_matrix(pins["C"]["L"]),
            "M": round_matrix(pins["C"]["M"]),
            "c": round_vec(pins["C"]["c"]),
            "max_abs_delta_vs_committed": round_float(pins["C"]["max_abs_delta_vs_committed"]),
        },
        "finite_exponential_semantics": (
            "L_R is the real pi/2 x-rotation generator whose tau_R=1 exponential is committed R_x; "
            "L_C is diag(log(7/10), log(7/10), 0) whose tau_C=1 exponential is committed D_z."
        ),
    }


def composition_row(cell: dict[str, Any], pins: dict[str, Any]) -> dict[str, Any]:
    r = np.asarray(cell["coord"], dtype=float)
    r_map = pins["R"]["M"]
    c_map = pins["C"]["M"]
    phi_d = r_map @ (c_map @ r)
    phi_i = c_map @ (r_map @ r)
    delta = phi_d - phi_i
    w4 = float(np.linalg.norm(delta, ord=2))
    sign = polarity_from_delta(delta)
    return {
        "cell_id": int(cell["cell_id"]),
        "coord": cell["coord"],
        "coord_scaled": cell["coord_scaled"],
        "Phi_D_expression": "exp(tau_R L_R)(exp(tau_C L_C)(rho_cell))",
        "Phi_I_expression": "exp(tau_C L_C)(exp(tau_R L_R)(rho_cell))",
        "Phi_D_bloch": round_vec(phi_d),
        "Phi_I_bloch": round_vec(phi_i),
        "Phi_D_density": density_matrix_from_bloch(phi_d),
        "Phi_I_density": density_matrix_from_bloch(phi_i),
        "Delta_D_minus_I_bloch": round_vec(delta),
        "W4_trace_norm": round_float(w4),
        "axis4_sign": sign,
        "axis4_label": polarity_label(sign),
        "functional": "sign(first_nonzero(Delta_y, Delta_z, Delta_x)); neutral iff ||Delta r||_2 <= EPS",
    }


def composition_table(carrier: dict[str, Any], pins: dict[str, Any]) -> list[dict[str, Any]]:
    return [composition_row(cell, pins) for cell in carrier["cells"]]


def composition_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["axis4_sign"] for row in rows)
    return {
        "positive": counts[1],
        "negative": counts[-1],
        "neutral": counts[0],
        "nonneutral": counts[1] + counts[-1],
        "total": len(rows),
        "by_label": dict(Counter(row["axis4_label"] for row in rows)),
    }


def one_step_stability(carrier: dict[str, Any], signs_by_cell: dict[int, int]) -> dict[str, Any]:
    rows = []
    by_generator: dict[str, dict[str, int]] = defaultdict(lambda: {"stable": 0, "changed": 0})
    for edge in carrier["edges"]:
        src = int(edge["src"])
        dst = int(edge["dst"])
        same = signs_by_cell[src] == signs_by_cell[dst]
        by_generator[edge["generator"]]["stable" if same else "changed"] += 1
        rows.append(
            {
                "edge_id": int(edge["edge_id"]),
                "src": src,
                "dst": dst,
                "generator": edge["generator"],
                "src_axis4_sign": signs_by_cell[src],
                "dst_axis4_sign": signs_by_cell[dst],
                "survives_update": same,
            }
        )
    stable = sum(row["survives_update"] for row in rows)
    return {
        "scope": "one_step_edges_on_committed_family_a_carrier",
        "edge_count": len(rows),
        "stable_edges": stable,
        "changed_edges": len(rows) - stable,
        "stable_fraction": stable / len(rows) if rows else 0.0,
        "changed_fraction": (len(rows) - stable) / len(rows) if rows else 0.0,
        "by_generator": dict(sorted(by_generator.items())),
        "neither_trivial_nor_frozen": stable > 0 and len(rows) - stable > 0,
        "sample_rows": rows[:64],
    }


def joined_axis_rows(
    axis0_rows: list[dict[str, Any]],
    axis6_rows: list[dict[str, Any]],
    axis4_rows: list[dict[str, Any]],
    carrier: dict[str, Any],
) -> list[dict[str, Any]]:
    by_axis6 = {row["cell_id"]: row for row in axis6_rows}
    by_axis4 = {row["cell_id"]: row for row in axis4_rows}
    successor_counts = carrier["successor_count_by_cell"]
    joined = []
    for row in axis0_rows:
        cell_id = int(row["cell_id"])
        b6 = by_axis6[cell_id]
        a4 = by_axis4[cell_id]
        joined.append(
            {
                **row,
                "successor_count": successor_counts[cell_id],
                "b6_sign": b6["b6_sign"],
                "b6_label": b6["b6_label"],
                "axis4_sign": a4["axis4_sign"],
                "axis4_label": a4["axis4_label"],
                "W4_trace_norm": a4["W4_trace_norm"],
                "axis4_nonzero": a4["axis4_sign"] != 0,
            }
        )
    return joined


def independence_matrix(
    axis0_rows: list[dict[str, Any]],
    axis6_rows: list[dict[str, Any]],
    axis4_rows: list[dict[str, Any]],
    carrier: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    joined = joined_axis_rows(axis0_rows, axis6_rows, axis4_rows, carrier)
    rows = []
    for row_id, predictor, target in [
        ("axis4_not_recoverable_from_axis0_response", "axis0_polarity_sign", "axis4_sign"),
        ("axis0_response_not_recoverable_from_axis4", "axis4_sign", "axis0_polarity_sign"),
        ("axis4_not_recoverable_from_axis6_precedence", "b6_sign", "axis4_sign"),
        ("axis6_precedence_not_recoverable_from_axis4", "axis4_sign", "b6_sign"),
    ]:
        acc, ambiguous = majority_accuracy(joined, predictor, target)
        rows.append(
            {
                "row_id": row_id,
                "predictor": predictor,
                "target": target,
                "majority_accuracy": acc,
                "ambiguous_keys": ambiguous,
                "witness_pair": first_independence_witness(joined, predictor, target),
                "pass": acc < 1.0,
                "carrier_honest": True,
                "no_identity_leak_rule": "cell identity, coordinates, and direct target readout fingerprints are excluded from the pass/fail predictor.",
            }
        )

    identity_fields = ["cell_id", "coord_scaled", "axis4_sign", "W4_trace_norm"]
    identity_keyed = add_combo_key(joined, "identity_predictor_key", identity_fields)
    identity_acc, identity_amb = majority_accuracy(identity_keyed, "identity_predictor_key", "axis4_sign")
    frozen_candidates = []
    for name, fields in {
        "axis0_readout_only": ["axis0_polarity_sign"],
        "axis6_readout_only": ["b6_sign"],
        "axis0_axis6_readout_pair": ["axis0_polarity_sign", "b6_sign"],
        "low_dimensional_tags_only": ["kappa", "nesting", "conditioned_shell_member"],
    }.items():
        keyed = add_combo_key(joined, "predictor_key", fields)
        acc, ambiguous = majority_accuracy(keyed, "predictor_key", "axis4_sign")
        frozen_candidates.append(
            {
                "predictor_id": name,
                "fields": fields,
                "majority_accuracy": acc,
                "ambiguous_key_count": len(ambiguous),
            }
        )
    best_non_identity = max(frozen_candidates, key=lambda row: row["majority_accuracy"])
    rows.append(
        {
            "row_id": "best_predictor_full_0_4_6_feature_report",
            "full_feature_report_included": True,
            "identity_inclusive_fields": identity_fields,
            "identity_inclusive_majority_accuracy": identity_acc,
            "identity_inclusive_ambiguous_key_count": len(identity_amb),
            "identity_leak_detected": identity_acc == 1.0,
            "identity_leak_exclusion_rule": (
                "The pass rows use readout-only or low-dimensional tag predictors. "
                "Cell id, coordinates, W4, and direct Axis-4 fingerprints are reported as leaks and excluded."
            ),
            "identity_leak_excluded_candidate_rows": frozen_candidates,
            "identity_leak_excluded_best_predictor": best_non_identity["predictor_id"],
            "identity_leak_excluded_best_accuracy": best_non_identity["majority_accuracy"],
            "pass": best_non_identity["majority_accuracy"] < 1.0 and identity_acc == 1.0,
            "status": "carrier_honest_readout_only_with_identity_leak_caveat",
        }
    )
    return rows, {"joined_rows": joined, "best_non_identity": best_non_identity, "identity_inclusive_accuracy": identity_acc}


def commuting_control(carrier: dict[str, Any], pins: dict[str, Any]) -> dict[str, Any]:
    l_r = pins["R"]["L"]
    r_map = expm(l_r)
    c_commuting = expm(0.5 * l_r)
    rows = []
    for cell in carrier["cells"]:
        r = np.asarray(cell["coord"], dtype=float)
        left = r_map @ (c_commuting @ r)
        right = c_commuting @ (r_map @ r)
        delta = left - right
        rows.append({"cell_id": int(cell["cell_id"]), "W4": float(np.linalg.norm(delta)), "sign": polarity_from_delta(delta)})
    neutral_count = sum(row["sign"] == 0 for row in rows)
    return {
        "fired": True,
        "pair": "exp(L_R) with exp(0.5 L_R), same x-rotation generator family",
        "all_cells_neutral": neutral_count == EXPECTED_STATE_COUNT,
        "neutral_count": neutral_count,
        "max_W4": round_float(max(row["W4"] for row in rows)),
        "falsifier_reachability": "A commuting generator pair reaches the all-neutral outcome under the same functional.",
    }


def leading_order_control(pins: dict[str, Any]) -> dict[str, Any]:
    a = pins["R"]["L"]
    b = pins["C"]["L"]
    u_map = np.eye(3) + SMALL_U * a
    e_map = np.eye(3) + SMALL_E * b
    d_map = u_map @ e_map @ u_map @ e_map
    i_map = e_map @ u_map @ e_map @ u_map
    gap = d_map - i_map
    leading = 2.0 * SMALL_U * SMALL_E * (a @ b - b @ a)
    gap_norm = float(np.linalg.norm(gap))
    leading_norm = float(np.linalg.norm(leading))
    residual_norm = float(np.linalg.norm(gap - leading))
    relative_error = residual_norm / leading_norm if leading_norm else math.inf
    return {
        "fired": relative_error < 5.0e-4,
        "panel_form": "D=UEUE, I=EUEU, leading order D-I = 2ue[A,B]",
        "u": SMALL_U,
        "e": SMALL_E,
        "A": "L_R",
        "B": "L_C",
        "gap_matrix": round_matrix(gap, 18),
        "leading_order_2ue_commutator": round_matrix(leading, 18),
        "gap_norm": round_float(gap_norm, 18),
        "leading_norm": round_float(leading_norm, 18),
        "residual_norm": round_float(residual_norm, 18),
        "relative_error": relative_error,
        "threshold": 5.0e-4,
        "pass": relative_error < 5.0e-4,
    }


def shuffled_order_control(carrier: dict[str, Any], pins: dict[str, Any], axis4_rows: list[dict[str, Any]]) -> dict[str, Any]:
    r_map = pins["R"]["M"]
    c_map = pins["C"]["M"]
    primary_by_cell = {row["cell_id"]: row["axis4_sign"] for row in axis4_rows}
    shuffled = []
    for cell in carrier["cells"]:
        r = np.asarray(cell["coord"], dtype=float)
        left = r_map @ (c_map @ (c_map @ (r_map @ r)))
        right = c_map @ (r_map @ (r_map @ (c_map @ r)))
        delta = left - right
        shuffled.append({"cell_id": int(cell["cell_id"]), "sign": polarity_from_delta(delta), "W4": float(np.linalg.norm(delta))})
    match_count = sum(row["sign"] == primary_by_cell[row["cell_id"]] for row in shuffled)
    return {
        "fired": match_count < EXPECTED_STATE_COUNT,
        "primary_order": "R C versus C R",
        "shuffled_order": "R C C R versus C R R C",
        "match_count": match_count,
        "changed_count": EXPECTED_STATE_COUNT - match_count,
        "primary_signature_sha256": stable_sha256(
            [{"cell_id": row["cell_id"], "axis4_sign": row["axis4_sign"]} for row in axis4_rows]
        ),
        "shuffled_signature_sha256": stable_sha256([{"cell_id": row["cell_id"], "sign": row["sign"]} for row in shuffled]),
        "pass": match_count < EXPECTED_STATE_COUNT,
    }


def compute_controls(
    carrier: dict[str, Any],
    pins: dict[str, Any],
    axis4_rows: list[dict[str, Any]],
    independence_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {row["row_id"]: row for row in independence_rows}
    axis6_to_axis4 = by_id["axis4_not_recoverable_from_axis6_precedence"]
    controls = {
        "commuting_pair_all_neutral": commuting_control(carrier, pins),
        "panel7_leading_order_2ue_commutator": leading_order_control(pins),
        "shuffled_order_not_primary": shuffled_order_control(carrier, pins, axis4_rows),
        "axis4_vs_axis6_discriminator": {
            "fired": axis6_to_axis4["pass"] is True,
            "same_cells": EXPECTED_STATE_COUNT,
            "axis6_parent": "discrete_axis6_precedence_v0",
            "axis6_commit": PARENT_COMMITS["discrete_axis6_precedence_v0"],
            "axis6_predicts_axis4_majority_accuracy": axis6_to_axis4["majority_accuracy"],
            "witness_pair": axis6_to_axis4["witness_pair"],
            "pass": axis6_to_axis4["pass"] is True,
            "why": "Axis-6 b6_sign on the same cells does not perfectly recover the Axis-4 composition sign.",
        },
    }
    return controls


def _z3_axis4_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = z3.Solver()
    positive = z3.Int("axis4_positive_erased" if erased else "axis4_positive")
    negative = z3.Int("axis4_negative_erased" if erased else "axis4_negative")
    neutral = z3.Int("axis4_neutral_erased" if erased else "axis4_neutral")
    total = z3.Int("axis4_total_erased" if erased else "axis4_total")
    commuting = z3.Int("axis4_commuting_neutral_erased" if erased else "axis4_commuting_neutral")
    leading = z3.Int("axis4_leading_order_pass_erased" if erased else "axis4_leading_order_pass")
    shuffled = z3.Int("axis4_shuffled_changed_erased" if erased else "axis4_shuffled_changed")
    axis6_not_predict = z3.Int("axis6_not_predict_axis4_erased" if erased else "axis6_not_predict_axis4")
    bind = dict(values)
    if erased:
        bind.update(
            {
                "positive": 0,
                "negative": 0,
                "commuting_neutral_count": 0,
                "leading_order_pass": 0,
                "shuffled_changed_count": 0,
                "axis6_not_predict_axis4": 0,
            }
        )
    solver.add(positive == bind["positive"])
    solver.add(negative == bind["negative"])
    solver.add(neutral == bind["neutral"])
    solver.add(total == bind["total"])
    solver.add(commuting == bind["commuting_neutral_count"])
    solver.add(leading == bind["leading_order_pass"])
    solver.add(shuffled == bind["shuffled_changed_count"])
    solver.add(axis6_not_predict == bind["axis6_not_predict_axis4"])
    solver.add(
        z3.Or(
            positive == 0,
            negative == 0,
            positive + negative + neutral != total,
            commuting != total,
            leading != 1,
            shuffled == 0,
            axis6_not_predict != 1,
        )
    )
    return str(solver.check()).lower()


def _cvc5_axis4_identity(values: dict[str, int], *, erased: bool = False) -> str:
    solver = cvc5.Solver()
    int_sort = solver.getIntegerSort()
    terms = {
        key: solver.mkConst(int_sort, f"axis4_{key}_cvc5{'_erased' if erased else ''}")
        for key in [
            "positive",
            "negative",
            "neutral",
            "total",
            "commuting_neutral_count",
            "leading_order_pass",
            "shuffled_changed_count",
            "axis6_not_predict_axis4",
        ]
    }
    bind = dict(values)
    if erased:
        bind.update(
            {
                "positive": 0,
                "negative": 0,
                "commuting_neutral_count": 0,
                "leading_order_pass": 0,
                "shuffled_changed_count": 0,
                "axis6_not_predict_axis4": 0,
            }
        )
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
            solver.mkTerm(Kind.DISTINCT, terms["commuting_neutral_count"], terms["total"]),
            solver.mkTerm(Kind.DISTINCT, terms["leading_order_pass"], solver.mkInteger(1)),
            solver.mkTerm(Kind.EQUAL, terms["shuffled_changed_count"], solver.mkInteger(0)),
            solver.mkTerm(Kind.DISTINCT, terms["axis6_not_predict_axis4"], solver.mkInteger(1)),
        )
    )
    return str(solver.checkSat()).lower()


def smt_rows(counts: dict[str, Any], controls: dict[str, Any]) -> dict[str, Any]:
    values = {
        "positive": int(counts["positive"]),
        "negative": int(counts["negative"]),
        "neutral": int(counts["neutral"]),
        "total": int(counts["total"]),
        "commuting_neutral_count": int(controls["commuting_pair_all_neutral"]["neutral_count"]),
        "leading_order_pass": 1 if controls["panel7_leading_order_2ue_commutator"]["pass"] else 0,
        "shuffled_changed_count": int(controls["shuffled_order_not_primary"]["changed_count"]),
        "axis6_not_predict_axis4": 1 if controls["axis4_vs_axis6_discriminator"]["pass"] else 0,
    }
    base = {
        "ran": True,
        "load_bearing": True,
        "asserted_precomputed_boolean": False,
        "bound_values": values,
        "identity": "positive>0 and negative>0 and total accounted and commuting all-neutral and panel leading-order pass and shuffled differs and axis6 does not predict axis4",
        "erased_flip_bindings": {
            "positive": 0,
            "negative": 0,
            "commuting_neutral_count": 0,
            "leading_order_pass": 0,
            "shuffled_changed_count": 0,
            "axis6_not_predict_axis4": 0,
        },
    }
    return {
        "z3": {
            **base,
            "tool": "z3",
            "verdict": _z3_axis4_identity(values),
            "erased_flip_verdict": _z3_axis4_identity(values, erased=True),
        },
        "cvc5": {
            **base,
            "tool": "cvc5",
            "verdict": _cvc5_axis4_identity(values),
            "erased_flip_verdict": _cvc5_axis4_identity(values, erased=True),
        },
    }


def contender_registry() -> list[dict[str, Any]]:
    return [
        {
            "contender_id": "trace_norm_D_minus_I_first_nonzero_yzx_sign",
            "status": "run_primary_candidate",
            "readout": "sign(first_nonzero(Delta_y, Delta_z, Delta_x)) with W4 trace-norm neutral gate",
            "demotion_condition": "demote if commuting control is not all-neutral, if panel leading order fails, or if same-carrier Axis-6 predicts it perfectly",
        },
        {
            "contender_id": "W4_magnitude_only",
            "status": "staged_not_run",
            "readout": "magnitude bucket of ||Phi_D-Phi_I||_1",
            "teeth": "must beat neutral and identity-leak controls without hiding polarity",
        },
        {
            "contender_id": "z_projection_sign_only",
            "status": "staged_not_run",
            "readout": "sign of z component of Delta_D_minus_I",
            "teeth": "must not collapse to an Axis-6 weighted-z precedence proxy",
        },
    ]


@lru_cache(maxsize=1)
def build_axis4_object() -> dict[str, Any]:
    carrier = axis0_common.rebuild_committed_carrier()
    axis0_object = axis0_common.build_axis0_object()
    axis6_object = axis6_common.build_axis6_object()
    axis0_rows = axis0_object["readout_table"]
    axis6_rows = axis6_object["precedence_table"]
    pins = pinning_payload()
    rows = composition_table(carrier, pins)
    counts = composition_counts(rows)
    signs = {row["cell_id"]: row["axis4_sign"] for row in rows}
    stability = one_step_stability(carrier, signs)
    independence, independence_aux = independence_matrix(axis0_rows, axis6_rows, rows, carrier)
    controls = compute_controls(carrier, pins, rows, independence)
    smt = smt_rows(counts, controls)
    control_pass = (
        controls["commuting_pair_all_neutral"]["all_cells_neutral"] is True
        and controls["panel7_leading_order_2ue_commutator"]["pass"] is True
        and controls["shuffled_order_not_primary"]["pass"] is True
        and controls["axis4_vs_axis6_discriminator"]["pass"] is True
    )
    independence_pass = all(row.get("pass") is True for row in independence)
    smt_pass = all(row["verdict"] == "unsat" and row["erased_flip_verdict"] == "sat" for row in smt.values())
    pin_pass = (
        pins["source"]["pin_sha256"] == S4_PIN_SHA256
        and pins["R"]["max_abs_delta_vs_committed"] <= 1.0e-12
        and pins["C"]["max_abs_delta_vs_committed"] <= 1.0e-12
    )
    all_pass = (
        carrier["state_count"] == EXPECTED_STATE_COUNT
        and carrier["edge_count"] == EXPECTED_EDGE_COUNT
        and axis0_object["carrier"]["state_object_id"] == carrier["state_object_id"]
        and axis6_object["carrier"]["state_object_id"] == carrier["state_object_id"]
        and pin_pass
        and counts["positive"] > 0
        and counts["negative"] > 0
        and counts["neutral"] > 0
        and stability["neither_trivial_nor_frozen"]
        and control_pass
        and independence_pass
        and smt_pass
    )
    state_object_id = f"{SIM_ID}:{stable_sha256({'carrier': carrier['state_object_id'], 'pinning': json_pinning(pins), 'axis4': rows})}"
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
        "axis4_functional": {
            "declared_before_classification": True,
            "Phi_D": "exp(tau_R L_R) after exp(tau_C L_C)",
            "Phi_I": "exp(tau_C L_C) after exp(tau_R L_R)",
            "difference": "Phi_D - Phi_I",
            "witness": "W4 = ||Phi_D(rho)-Phi_I(rho)||_1 = ||Delta Bloch||_2 for qubit density differences",
            "sign_functional": "first nonzero sign of (Delta_y, Delta_z, Delta_x)",
            "neutral_rule": "neutral iff W4 <= EPS",
            "eps": EPS,
        },
        "axis4_readout_table": rows,
        "axis4_counts": counts,
        "stability_under_committed_dynamics": stability,
        "axis0_alignment": {
            "axis0_state_object_id": axis0_object["state_object_id"],
            "axis0_source_path": rel(PARENT_PATHS["axis0_envelope"]),
            "axis0_source_sha256": sha256_file(PARENT_PATHS["axis0_envelope"]),
            "same_carrier": axis0_object["carrier"]["state_object_id"] == carrier["state_object_id"],
        },
        "axis6_alignment": {
            "axis6_state_object_id": axis6_object["state_object_id"],
            "axis6_source_path": rel(PARENT_PATHS["axis6_envelope"]),
            "axis6_source_sha256": sha256_file(PARENT_PATHS["axis6_envelope"]),
            "same_carrier": axis6_object["carrier"]["state_object_id"] == carrier["state_object_id"],
            "axis6_readout_parent_commit": PARENT_COMMITS["discrete_axis6_precedence_v0"],
        },
        "carrier_honest_independence_matrix": independence,
        "independence_auxiliary": {
            "best_non_identity": independence_aux["best_non_identity"],
            "identity_inclusive_accuracy": independence_aux["identity_inclusive_accuracy"],
        },
        "axis4_contender_registry_staged_rows": contender_registry(),
        "controls": controls,
        "falsifier_branches": {
            "reachable": True,
            "branches": sorted(controls),
            "required_to_fire": sorted(controls),
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
            "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
            "packet_audit_verdict_absent": not (SIM_DIR / "audit_verdict.md").exists(),
        },
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "no_builder_audit_verdict_envelope_gate": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "claim_sections": {
            "positive": [
                "one finite Axis-4 composition readout candidate over the committed Family A 33-cell carrier",
                "pinned S4 R_x/D_z generators with tau_R=tau_C=1 before classification",
                "carrier-honest 0/4 and 6/4 rows reported with identity-leak caveat",
                "panel-7 leading-order 2ue[A,B] control computed separately from the finite two-factor readout",
            ],
            "negative": [
                "no Axis-4 admission",
                "no Axis-6 claim",
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
            "finite Axis-4 composition readout candidate computed on Family A 33-cell carrier",
            "pinned R_x/D_z order-gap table emitted",
            "commuting, leading-order, shuffled-order, and 4-vs-6 controls computed",
            "readout-only 0/4 and 6/4 same-carrier non-recovery rows computed with identity-leak caveat",
        ],
        "disallowed_claims": [
            "axis admission",
            "Axis-6 precedence claim",
            "bridge admission",
            "physics",
            "manifold promotion",
            "canonical Axis-4 readout",
        ],
        "blocked_consumers": [
            "axis_level_admission",
            "bridge_or_cut_inference",
            "physics_interpretation",
            "scientific_lego_coupling",
        ],
        "validator_expected_commands": validator_expected_commands(),
    }


def validator_expected_commands() -> list[str]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/discrete_axis4_composition_v0/discrete_axis4_composition_v0_julia.jl",
        f"{py} system_v6/sims/discrete_axis4_composition_v0/discrete_axis4_composition_v0_jax.py",
        f"{py} system_v6/sims/discrete_axis4_composition_v0/discrete_axis4_composition_v0_pytorch.py",
        f"{py} system_v6/sims/discrete_axis4_composition_v0/write_envelope_spec.py",
        f"{py} scripts/build_three_engine_envelope.py system_v6/sims/discrete_axis4_composition_v0/discrete_axis4_composition_v0_envelope_spec.json > system_v6/sims/discrete_axis4_composition_v0/results/discrete_axis4_composition_v0_envelope_results.json",
        f"{py} system_v6/sims/discrete_axis4_composition_v0/validate_discrete_axis4_composition_v0.py",
        f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/discrete_axis4_composition_v0/results/discrete_axis4_composition_v0_envelope_results.json",
        f"{py} -m pytest -q system_v6/sims/discrete_axis4_composition_v0/tests",
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
    obj = build_axis4_object()
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
                "receipt_id": f"{engine}_{package}_axis4_composition_candidate",
                "tool": package,
                "computed_what": package_observables[package],
                "status": "used",
            }
            for package in aligned_packages_load_bearing
        ],
        "tool_calls": [
            {
                "receipt_id": f"{engine}_{package}_axis4_composition_candidate",
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
            "positive": obj["axis4_counts"]["positive"],
            "negative": obj["axis4_counts"]["negative"],
            "neutral": obj["axis4_counts"]["neutral"],
            "nonneutral": obj["axis4_counts"]["nonneutral"],
            "stable_edge_count": obj["stability_under_committed_dynamics"]["stable_edges"],
            "changed_edge_count": obj["stability_under_committed_dynamics"]["changed_edges"],
            "leading_order_relative_error": obj["controls"]["panel7_leading_order_2ue_commutator"]["relative_error"],
            "axis6_predicts_axis4_majority_accuracy": obj["controls"]["axis4_vs_axis6_discriminator"][
                "axis6_predicts_axis4_majority_accuracy"
            ],
            "readout_signature_sha256": stable_sha256(
                {
                    "axis4_counts": obj["axis4_counts"],
                    "axis4_table": [
                        {"cell_id": row["cell_id"], "axis4_sign": row["axis4_sign"], "W4": row["W4_trace_norm"]}
                        for row in obj["axis4_readout_table"]
                    ],
                    "leading_order": obj["controls"]["panel7_leading_order_2ue_commutator"],
                }
            ),
        },
        "crossover_proofs": obj["crossover_proofs"],
        "state_object_id": obj["state_object_id"],
        "all_pass": all_pass,
    }
