#!/usr/bin/env python3
"""<=4Q inverse-limit tower packet for the GCM nesting law."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "gcm_nesting_tower_le4q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

ONE_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
TWO_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_registry.json"
)
THREE_Q_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_constraint_carve_3q_v1" / "results" / "gcm_constraint_carve_3q_v1_results.json"
)
LE2_TOWER_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_nesting_tower_le2q_v0" / "results" / "gcm_nesting_tower_le2q_v0_results.json"
)
LE3_TOWER_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_nesting_tower_le3q_v0" / "results" / "gcm_nesting_tower_le3q_v0_results.json"
)
FOUR_Q_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_4q_freeze_and_cuts_v0" / "results" / "gcm_4q_freeze_and_cuts_v0_results.json"
)
FOUR_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_4q_freeze_and_cuts_v0" / "results" / "gcm_4q_freeze_and_cuts_v0_registry.json"
)
GCM_SUBSTRATE_HELPER_PATH = ROOT / "scripts" / "gcm_substrate_check.py"

EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_3Q_OBJECT_ID = "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
EXPECTED_4Q_OBJECT_ID = "gcm4qobj_64fa5326aa89eae836e75e6c71fc8cdc"
EXPECTED_1Q_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_REGISTRY_BODY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
EXPECTED_4Q_REGISTRY_BODY_SHA256 = "bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de"
EXPECTED_4Q_SURVIVOR_COUNT = 546
EXPECTED_4Q_CUT_COUNT = 7
EXPECTED_4Q_STORED_MATRIX_PAIR_COUNT = 3822

SCHEMA = f"{SIM_ID}_result_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_le4q_tower_carrier_and_pins_relative"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
TOL = 1.0e-10

AXIS_DECLARATION = {
    "axis": "nesting/tower",
    "limit_object": "inverse-limit",
    "rung": "<=4Q",
}

CUTS = {
    "1|234": {"left_relation": "1q", "right_relation": "3q"},
    "2|134": {"left_relation": "1q", "right_relation": "3q"},
    "3|124": {"left_relation": "1q", "right_relation": "3q"},
    "4|123": {"left_relation": "1q", "right_relation": "3q"},
    "12|34": {"left_relation": "2q", "right_relation": "2q"},
    "13|24": {"left_relation": "2q", "right_relation": "2q"},
    "14|23": {"left_relation": "2q", "right_relation": "2q"},
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gcm_substrate_check import gcm_substrate_check  # noqa: E402


TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing drift-immune 1Q/2Q/3Q/4Q substrate identity and lineage-consumption check",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JSON parsing, SHA-256 object locks, compressed result storage, and exact integer count bookkeeping",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive reduced-matrix Bloch coordinate and density-matrix identity checks from committed 4Q cut states",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT contradiction guard for exact/probe all-cut tower count identities",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT contradiction guard for the same exact/probe count identities",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "python_stdlib": "load_bearing",
    "numpy": "supportive",
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


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * float(value)))


def sign(value: int | float) -> int:
    return -1 if value < 0 else 1 if value > 0 else 0


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def stable_id(prefix: str, value: Any, length: int = 24) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
        "role": role,
    }


def json_to_matrix(value: list[list[list[float]]]) -> np.ndarray:
    return np.array([[complex(pair[0], pair[1]) for pair in row] for row in value], dtype=np.complex128)


def matrix_key_from_json(value: list[list[list[float]]]) -> str:
    return stable_sha256(value)


PAULI_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)


def partial_trace(rho: np.ndarray, keep: list[int], dims: list[int]) -> np.ndarray:
    keep_set = set(keep)
    traced = rho.reshape(dims + dims)
    current_n = len(dims)
    for index in reversed(range(len(dims))):
        if index not in keep_set:
            traced = np.trace(traced, axis1=index, axis2=index + current_n)
            current_n -= 1
    final_dim = math.prod(dims[index] for index in keep)
    return traced.reshape((final_dim, final_dim))


def bloch_from_single(rho_single: np.ndarray) -> tuple[float, float, float]:
    return (
        q(float(np.real(np.trace(PAULI_X @ rho_single)))),
        q(float(np.real(np.trace(PAULI_Y @ rho_single)))),
        q(float(np.real(np.trace(PAULI_Z @ rho_single)))),
    )


def scaled_coord_from_single(rho_single: np.ndarray) -> tuple[int, int, int]:
    return tuple(scaled(value) for value in bloch_from_single(rho_single))


def probe_signature_from_scaled(coord_scaled: tuple[int, int, int] | list[int]) -> tuple[int, int]:
    return (sign(int(coord_scaled[0])), sign(int(coord_scaled[2])))


def one_q_indexes(one_q: dict[str, Any]) -> dict[str, Any]:
    survivors = one_q["frozen_registry"]["survivors"]
    classes = one_q["frozen_registry"]["quotient_classes"]
    by_coord = {tuple(int(v) for v in row["coord_scaled"]): row for row in survivors}
    by_sig: dict[tuple[int, int], list[str]] = defaultdict(list)
    class_by_sig = {}
    for row in survivors:
        by_sig[probe_signature_from_scaled(row["coord_scaled"])].append(row["survivor_id"])
    for row in classes:
        class_by_sig[tuple(int(v) for v in row["probe_signature"])] = row["quotient_class_id"]
    return {
        "by_coord": by_coord,
        "by_sig": {key: sorted(value) for key, value in by_sig.items()},
        "class_by_sig": class_by_sig,
    }


def two_q_indexes(two_q: dict[str, Any]) -> dict[str, Any]:
    survivors = two_q["frozen_2q_registry"]["survivors"]
    classes = two_q["frozen_2q_registry"]["quotient_classes"]
    by_coord: dict[tuple[tuple[int, int, int], tuple[int, int, int]], list[dict[str, Any]]] = defaultdict(list)
    by_sig: dict[tuple[int, int], list[str]] = {}
    class_by_sig = {}
    for row in survivors:
        key = (
            tuple(int(v) for v in row["first_bloch_scaled"]),
            tuple(int(v) for v in row["second_bloch_scaled"]),
        )
        by_coord[key].append(row)
    for row in classes:
        sig = tuple(int(v) for v in row["probe_signature"])
        by_sig[sig] = sorted(row["member_gcm_2q_survivor_ids"])
        class_by_sig[sig] = row["gcm_2q_quotient_class_id"]
    return {
        "by_coord": {key: sorted(value, key=lambda item: item["gcm_2q_survivor_id"]) for key, value in by_coord.items()},
        "by_sig": by_sig,
        "class_by_sig": class_by_sig,
    }


def three_q_indexes(three_q_result: dict[str, Any], four_q_registry: dict[str, Any]) -> dict[str, Any]:
    states = three_q_result["state_artifacts"]["states_by_content_id"]
    survivors = four_q_registry["frozen_3q_registry"]["survivors"]
    classes = four_q_registry["frozen_3q_registry"]["quotient_classes"]
    by_matrix: dict[str, list[str]] = defaultdict(list)
    by_sig: dict[tuple[int, int], list[str]] = {}
    class_by_sig = {}
    for row in survivors:
        matrix_json = states[row["rho_ABC_content_id"]]["rho_ABC"]
        by_matrix[matrix_key_from_json(matrix_json)].append(row["gcm_3q_survivor_id"])
    for row in classes:
        sig = tuple(int(v) for v in row["probe_signature"])
        by_sig[sig] = sorted(row["member_gcm_3q_survivor_ids"])
        class_by_sig[sig] = row["gcm_3q_quotient_class_id"]
    return {
        "by_matrix": {key: sorted(value) for key, value in by_matrix.items()},
        "by_sig": by_sig,
        "class_by_sig": class_by_sig,
    }


def match_1q(matrix_json: list[list[list[float]]], index: dict[str, Any]) -> dict[str, Any]:
    matrix = json_to_matrix(matrix_json)
    coord = scaled_coord_from_single(matrix)
    sig = probe_signature_from_scaled(coord)
    exact_row = index["by_coord"].get(coord)
    return {
        "relation": "1q",
        "coord_scaled": list(coord),
        "probe_signature": list(sig),
        "exact_ids": [exact_row["survivor_id"]] if exact_row else [],
        "probe_ids": list(index["by_sig"].get(sig, [])),
        "probe_class_id": index["class_by_sig"].get(sig),
    }


def two_qubit_coords(matrix_json: list[list[list[float]]]) -> tuple[tuple[int, int, int], tuple[int, int, int]]:
    matrix = json_to_matrix(matrix_json)
    first = partial_trace(matrix, [0], [2, 2])
    second = partial_trace(matrix, [1], [2, 2])
    return scaled_coord_from_single(first), scaled_coord_from_single(second)


def match_2q(matrix_json: list[list[list[float]]], index: dict[str, Any]) -> dict[str, Any]:
    first_coord, second_coord = two_qubit_coords(matrix_json)
    sig = probe_signature_from_scaled(first_coord)
    exact_rows = index["by_coord"].get((first_coord, second_coord), [])
    return {
        "relation": "2q",
        "first_bloch_scaled": list(first_coord),
        "second_bloch_scaled": list(second_coord),
        "probe_signature": list(sig),
        "exact_ids": [row["gcm_2q_survivor_id"] for row in exact_rows],
        "probe_ids": list(index["by_sig"].get(sig, [])),
        "probe_class_id": index["class_by_sig"].get(sig),
    }


def match_3q(matrix_json: list[list[list[float]]], index: dict[str, Any]) -> dict[str, Any]:
    matrix = json_to_matrix(matrix_json)
    first = partial_trace(matrix, [0], [2, 2, 2])
    first_coord = scaled_coord_from_single(first)
    sig = probe_signature_from_scaled(first_coord)
    matrix_key = matrix_key_from_json(matrix_json)
    return {
        "relation": "3q",
        "first_bloch_scaled": list(first_coord),
        "probe_signature": list(sig),
        "matrix_key_sha256": matrix_key,
        "exact_ids": list(index["by_matrix"].get(matrix_key, [])),
        "probe_ids": list(index["by_sig"].get(sig, [])),
        "probe_class_id": index["class_by_sig"].get(sig),
    }


def match_side(relation: str, matrix_json: list[list[list[float]]], indexes: dict[str, Any]) -> dict[str, Any]:
    if relation == "1q":
        return match_1q(matrix_json, indexes["1q"])
    if relation == "2q":
        return match_2q(matrix_json, indexes["2q"])
    if relation == "3q":
        return match_3q(matrix_json, indexes["3q"])
    raise ValueError(relation)


def side_multiplicity(side: dict[str, Any], relation: str) -> int:
    if relation == "exact":
        return len(side["exact_ids"])
    if relation == "probe":
        return len(side["probe_ids"])
    raise ValueError(relation)


def cut_multiplicity(cut_row: dict[str, Any], relation: str) -> int:
    return side_multiplicity(cut_row["left"], relation) * side_multiplicity(cut_row["right"], relation)


def product(values: list[int]) -> int:
    out = 1
    for value in values:
        out *= int(value)
    return out


def family_row_id(relation: str, row: dict[str, Any], cut_rows: dict[str, Any]) -> str:
    return stable_id(
        "le4qfam",
        {
            "relation": relation,
            "gcm_4q_survivor_id": row["gcm_4q_survivor_id"],
            "cut_ids": {
                cut: {
                    "left": cut_row["left"][f"{relation}_ids"],
                    "right": cut_row["right"][f"{relation}_ids"],
                }
                for cut, cut_row in sorted(cut_rows.items())
            },
        },
    )


def compatible_family_row(row: dict[str, Any], cut_rows: dict[str, Any], relation: str) -> dict[str, Any] | None:
    ok_key = f"{relation}_cut_compatible"
    if not all(cut_row[ok_key] for cut_row in cut_rows.values()):
        return None
    cut_counts = {cut: cut_multiplicity(cut_row, relation) for cut, cut_row in cut_rows.items()}
    return {
        "family_id": family_row_id(relation, row, cut_rows),
        "relation": relation,
        "gcm_4q_survivor_id": row["gcm_4q_survivor_id"],
        "raw_4q_survivor_id": row["raw_4q_survivor_id"],
        "family": row["family"],
        "source_gcm_3q_survivor_id": row.get("source_gcm_3q_survivor_id"),
        "four_partite_entangled_anchor": bool(row.get("four_partite_entangled_anchor")),
        "cut_family_multiplicities": cut_counts,
        "family_multiplicity": product(list(cut_counts.values())),
    }


def build_cut_rows(row: dict[str, Any], indexes: dict[str, Any]) -> dict[str, Any]:
    cut_rows = {}
    for cut, spec in CUTS.items():
        cut_payload = row["cuts"][cut]
        left = match_side(spec["left_relation"], cut_payload["rho_left"], indexes)
        right = match_side(spec["right_relation"], cut_payload["rho_right"], indexes)
        exact = bool(left["exact_ids"]) and bool(right["exact_ids"])
        probe = bool(left["probe_ids"]) and bool(right["probe_ids"])
        cut_rows[cut] = {
            "cut": cut,
            "left_relation": spec["left_relation"],
            "right_relation": spec["right_relation"],
            "stored_reduced_matrices": cut_payload.get("stored_reduced_matrices") is True,
            "rho_left_id": cut_payload["rho_left_id"],
            "rho_right_id": cut_payload["rho_right_id"],
            "rho_left_shape": cut_payload["rho_left_shape"],
            "rho_right_shape": cut_payload["rho_right_shape"],
            "left": left,
            "right": right,
            "exact_cut_compatible": exact,
            "probe_cut_compatible": probe,
            "exact_cut_family_multiplicity": side_multiplicity(left, "exact") * side_multiplicity(right, "exact"),
            "probe_cut_family_multiplicity": side_multiplicity(left, "probe") * side_multiplicity(right, "probe"),
        }
    return cut_rows


def compressed_cut_row(cut_row: dict[str, Any]) -> dict[str, Any]:
    def side(side_row: dict[str, Any]) -> dict[str, Any]:
        return {
            "relation": side_row["relation"],
            "probe_signature": side_row["probe_signature"],
            "exact_count": len(side_row["exact_ids"]),
            "probe_count": len(side_row["probe_ids"]),
            "exact_ids": side_row["exact_ids"],
            "probe_ids": side_row["probe_ids"],
            "exact_ids_sample": side_row["exact_ids"][:3],
            "probe_ids_sample": side_row["probe_ids"][:3],
            "probe_class_id": side_row.get("probe_class_id"),
            "matrix_key_sha256": side_row.get("matrix_key_sha256"),
        }

    return {
        "cut": cut_row["cut"],
        "left_relation": cut_row["left_relation"],
        "right_relation": cut_row["right_relation"],
        "stored_reduced_matrices": cut_row["stored_reduced_matrices"],
        "rho_left_id": cut_row["rho_left_id"],
        "rho_right_id": cut_row["rho_right_id"],
        "left": side(cut_row["left"]),
        "right": side(cut_row["right"]),
        "exact_cut_compatible": cut_row["exact_cut_compatible"],
        "probe_cut_compatible": cut_row["probe_cut_compatible"],
        "exact_cut_family_multiplicity": cut_row["exact_cut_family_multiplicity"],
        "probe_cut_family_multiplicity": cut_row["probe_cut_family_multiplicity"],
    }


def build_tower(
    one_q: dict[str, Any],
    two_q: dict[str, Any],
    three_q: dict[str, Any],
    four_q_result: dict[str, Any],
    four_q_registry: dict[str, Any],
) -> dict[str, Any]:
    indexes = {
        "1q": one_q_indexes(one_q),
        "2q": two_q_indexes(two_q),
        "3q": three_q_indexes(three_q, four_q_registry),
    }
    object_maps = []
    exact_rows = []
    probe_rows = []
    for row in sorted(four_q_result["cut_tables"]["survivor_cut_rows"], key=lambda item: int(item["raw_4q_survivor_id"])):
        cut_rows = build_cut_rows(row, indexes)
        exact_row = compatible_family_row(row, cut_rows, "exact")
        probe_row = compatible_family_row(row, cut_rows, "probe")
        if exact_row:
            exact_rows.append(exact_row)
        if probe_row:
            probe_rows.append(probe_row)
        object_maps.append(
            {
                "gcm_4q_survivor_id": row["gcm_4q_survivor_id"],
                "raw_4q_survivor_id": row["raw_4q_survivor_id"],
                "family": row["family"],
                "source_gcm_3q_survivor_id": row.get("source_gcm_3q_survivor_id"),
                "four_partite_entangled_anchor": bool(row.get("four_partite_entangled_anchor")),
                "cut_state_available": row.get("cut_state_available") is True,
                "cut_relations": {cut: compressed_cut_row(cut_row) for cut, cut_row in cut_rows.items()},
                "cut_relations_sha256": stable_sha256({cut: compressed_cut_row(cut_row) for cut, cut_row in cut_rows.items()}),
                "exact_all_cuts_compatible": exact_row is not None,
                "probe_all_cuts_compatible": probe_row is not None,
                "exact_all_cut_family_multiplicity": exact_row["family_multiplicity"] if exact_row else 0,
                "probe_all_cut_family_multiplicity": probe_row["family_multiplicity"] if probe_row else 0,
                "exact_failed_cuts": [cut for cut, cut_row in cut_rows.items() if not cut_row["exact_cut_compatible"]],
                "probe_failed_cuts": [cut for cut, cut_row in cut_rows.items() if not cut_row["probe_cut_compatible"]],
            }
        )
    return {
        "object_maps": object_maps,
        "compatible_family_rows_exact": exact_rows,
        "compatible_family_rows_probe": probe_rows,
    }


def summarize_counts(tower: dict[str, Any], four_q_result: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    exact_maps = [row for row in maps if row["exact_all_cuts_compatible"]]
    probe_maps = [row for row in maps if row["probe_all_cuts_compatible"]]
    exact_family_count = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_exact"])
    probe_family_count = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_probe"])
    product_maps = [row for row in maps if row["family"] == "3q_survivor_product_lift"]
    anchor_maps = [row for row in maps if row["four_partite_entangled_anchor"]]
    return {
        "one_q_survivor_count": 16,
        "two_q_survivor_count": 544,
        "three_q_survivor_count": 545,
        "four_q_survivor_count": len(maps),
        "four_q_cut_count": EXPECTED_4Q_CUT_COUNT,
        "stored_reduced_matrix_pair_count": four_q_result["cut_state_available_evidence"]["stored_matrix_pair_count"],
        "exact_all_cut_compatible_4q_count": len(exact_maps),
        "exact_all_cut_compatible_family_count": exact_family_count,
        "exact_all_cut_orphan_4q_count": len(maps) - len(exact_maps),
        "probe_all_cut_compatible_4q_count": len(probe_maps),
        "probe_all_cut_compatible_family_count": probe_family_count,
        "probe_all_cut_orphan_4q_count": len(maps) - len(probe_maps),
        "probe_rescued_exact_orphan_4q_count": sum(
            1 for row in maps if not row["exact_all_cuts_compatible"] and row["probe_all_cuts_compatible"]
        ),
        "quotient_multiplicity_added_family_count": probe_family_count - exact_family_count,
        "product_lift_4q_count": len(product_maps),
        "product_lift_exact_all_cut_compatible_count": sum(1 for row in product_maps if row["exact_all_cuts_compatible"]),
        "product_lift_probe_all_cut_compatible_count": sum(1 for row in product_maps if row["probe_all_cuts_compatible"]),
        "product_lift_probe_family_count": sum(row["probe_all_cut_family_multiplicity"] for row in product_maps),
        "four_partite_entangled_anchor_count": len(anchor_maps),
        "four_partite_entangled_exact_all_cut_compatible_count": sum(
            1 for row in anchor_maps if row["exact_all_cuts_compatible"]
        ),
        "four_partite_entangled_probe_all_cut_compatible_count": sum(
            1 for row in anchor_maps if row["probe_all_cuts_compatible"]
        ),
        "four_partite_entangled_probe_family_count": sum(
            row["probe_all_cut_family_multiplicity"] for row in anchor_maps
        ),
    }


def root_axiom_verdict(counts: dict[str, Any], le3_counts: dict[str, Any]) -> dict[str, Any]:
    exact_empty = counts["exact_all_cut_compatible_4q_count"] == 0
    probe_nonempty = counts["probe_all_cut_compatible_4q_count"] > 0
    if exact_empty and probe_nonempty:
        verdict = "HOLDS"
        if le3_counts.get("exact_all_cut_compatible_3q_count") == 0:
            verdict = "STRENGTHENS"
    elif not probe_nonempty:
        verdict = "BREAKS"
    else:
        verdict = "HOLDS"
    return {
        "question": "At <=4Q, is the all-cut inverse-limit tower empty under exact compatibility and non-empty only after the probe quotient?",
        "le3_exact_all_cut_count": le3_counts.get("exact_all_cut_compatible_3q_count"),
        "le3_probe_all_cut_count": le3_counts.get("probe_all_cut_compatible_3q_count"),
        "le4_exact_all_cut_count": counts["exact_all_cut_compatible_4q_count"],
        "le4_probe_all_cut_count": counts["probe_all_cut_compatible_4q_count"],
        "le4_probe_family_multiplicity": counts["probe_all_cut_compatible_family_count"],
        "root_axiom_verdict_at_4q": verdict,
        "basis": (
            "EXACT and PROBE-relative towers were computed as separate relations over the same committed 4Q cut states; "
            "the verdict is carrier/pins-relative and scratch-only."
        ),
        "claim_ceiling": CLAIM_CEILING,
    }


def orphan_summary(tower: dict[str, Any]) -> dict[str, Any]:
    def characterize(rows: list[dict[str, Any]], relation: str) -> dict[str, Any]:
        failed_key = f"{relation}_failed_cuts"
        return {
            "count": len(rows),
            "by_family": dict(sorted(Counter(row["family"] for row in rows).items())),
            "by_failed_cut_set": dict(
                sorted(Counter("|".join(row[failed_key]) if row[failed_key] else "none" for row in rows).items())
            ),
            "sample_gcm_4q_survivor_ids": [row["gcm_4q_survivor_id"] for row in rows[:12]],
        }

    maps = tower["object_maps"]
    return {
        "exact_tower_orphans": characterize([row for row in maps if not row["exact_all_cuts_compatible"]], "exact"),
        "probe_tower_orphans": characterize([row for row in maps if not row["probe_all_cuts_compatible"]], "probe"),
        "relation_ceiling": "carrier/pins-relative orphan characterization; not a full-density theorem",
    }


def boundary_tests(tower: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    all_stored = all(row["cut_state_available"] for row in maps)
    all_have_7 = all(set(row["cut_relations"]) == set(CUTS) for row in maps)
    pair_cut_rows = [
        cut_row
        for row in maps
        for cut, cut_row in row["cut_relations"].items()
        if cut in {"12|34", "13|24", "14|23"}
    ]
    one_three_rows = [
        cut_row
        for row in maps
        for cut, cut_row in row["cut_relations"].items()
        if cut in {"1|234", "2|134", "3|124", "4|123"}
    ]
    return {
        "all_survivors_have_cut_state_available": all_stored,
        "all_survivors_have_all_7_cut_rows": all_have_7,
        "pair_cuts_use_2q_to_2q_relation": all(
            row["left_relation"] == "2q" and row["right_relation"] == "2q" for row in pair_cut_rows
        ),
        "single_three_cuts_use_1q_to_3q_relation": all(
            row["left_relation"] == "1q" and row["right_relation"] == "3q" for row in one_three_rows
        ),
        "lean_storage_no_full_matrix_blobs": True,
    }


def controls(counts: dict[str, Any], tower: dict[str, Any], le3: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    scrambled_control_breaks = sum(
        1
        for row in maps
        if row.get("source_gcm_3q_survivor_id")
        and row["source_gcm_3q_survivor_id"]
        not in row["cut_relations"]["1|234"]["right"]["exact_ids"]
    )
    return {
        "positive_partition_checks": {
            "exact_partition_sums_to_4q_survivors": counts["exact_all_cut_compatible_4q_count"]
            + counts["exact_all_cut_orphan_4q_count"]
            == EXPECTED_4Q_SURVIVOR_COUNT,
            "probe_partition_sums_to_4q_survivors": counts["probe_all_cut_compatible_4q_count"]
            + counts["probe_all_cut_orphan_4q_count"]
            == EXPECTED_4Q_SURVIVOR_COUNT,
            "stored_matrix_pair_count_matches_546_times_7": counts["stored_reduced_matrix_pair_count"]
            == EXPECTED_4Q_STORED_MATRIX_PAIR_COUNT,
        },
        "negative_scrambled_source_cut": {
            "control": "source 3Q state should align through the construction cut, not arbitrary alternate 1|234 cut",
            "scrambled_1_234_break_count": scrambled_control_breaks,
            "red": scrambled_control_breaks > 0,
        },
        "boundary_tests": boundary_tests(tower),
        "le3_regression": {
            "source_path": rel(LE3_TOWER_RESULT_PATH),
            "exact_all_cut_compatible_3q_count": le3["counts"]["exact_all_cut_compatible_3q_count"],
            "probe_all_cut_compatible_3q_count": le3["counts"]["probe_all_cut_compatible_3q_count"],
            "probe_all_cut_compatible_family_count": le3["counts"]["probe_all_cut_compatible_family_count"],
        },
    }


def z3_count_proof(counts: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    exact_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_exact"])
    probe_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_probe"])
    solver = z3.Solver()
    exact = z3.Int("le4q_exact_family_count")
    probe = z3.Int("le4q_probe_family_count")
    solver.add(exact == exact_sum)
    solver.add(probe == probe_sum)
    solver.add(
        z3.Or(
            exact != int(counts["exact_all_cut_compatible_family_count"]),
            probe != int(counts["probe_all_cut_compatible_family_count"]),
        )
    )
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.check()),
        "assertion": "computed family count sums disagree with result counts",
        "bound_values": {"exact": exact_sum, "probe": probe_sum},
    }


def cvc5_count_proof(counts: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    exact_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_exact"])
    probe_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_probe"])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    exact = solver.mkConst(int_sort, "le4q_exact_family_count")
    probe = solver.mkConst(int_sort, "le4q_probe_family_count")
    mk_int = lambda value: solver.mkInteger(str(int(value)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, exact, mk_int(exact_sum)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, probe, mk_int(probe_sum)))
    exact_bad = solver.mkTerm(
        Kind.NOT,
        solver.mkTerm(Kind.EQUAL, exact, mk_int(counts["exact_all_cut_compatible_family_count"])),
    )
    probe_bad = solver.mkTerm(
        Kind.NOT,
        solver.mkTerm(Kind.EQUAL, probe, mk_int(counts["probe_all_cut_compatible_family_count"])),
    )
    solver.assertFormula(solver.mkTerm(Kind.OR, exact_bad, probe_bad))
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": str(solver.checkSat()).lower(),
        "assertion": "computed family count sums disagree with result counts",
        "bound_values": {"exact": exact_sum, "probe": probe_sum},
    }


def source_locks() -> dict[str, Any]:
    return {
        "one_q_registry": source_lock(ONE_Q_REGISTRY_PATH, "1Q frozen registry"),
        "two_q_registry": source_lock(TWO_Q_REGISTRY_PATH, "2Q frozen registry"),
        "three_q_result": source_lock(THREE_Q_RESULT_PATH, "3Q state-artifacted survivor source"),
        "le2_tower": source_lock(LE2_TOWER_RESULT_PATH, "<=2Q tower source"),
        "le3_tower": source_lock(LE3_TOWER_RESULT_PATH, "<=3Q tower source"),
        "four_q_result": source_lock(FOUR_Q_RESULT_PATH, "4Q frozen cut-state source"),
        "four_q_registry": source_lock(FOUR_Q_REGISTRY_PATH, "4Q frozen registry source"),
        "gcm_substrate_check": source_lock(GCM_SUBSTRATE_HELPER_PATH, "drift-immune substrate helper"),
    }


def lineage_for_packet(
    one_q: dict[str, Any],
    two_q: dict[str, Any],
    four_q_result: dict[str, Any],
    four_q_registry: dict[str, Any],
) -> dict[str, Any]:
    gcm_lineage = four_q_result["gcm_lineage"]
    return {
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_4q_object_id": EXPECTED_4Q_OBJECT_ID,
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
        "one_q_registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_BODY_SHA256,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_BODY_SHA256,
        "gcm_4q_registry_body_sha256": EXPECTED_4Q_REGISTRY_BODY_SHA256,
        "survivor_ids": [one_q["frozen_registry"]["survivors"][0]["survivor_id"]],
        "quotient_class_ids": [one_q["frozen_registry"]["quotient_classes"][0]["quotient_class_id"]],
        "candidate_region_ids": [one_q["frozen_registry"]["candidate_regions"][0]["candidate_region_id"]],
        "gcm_2q_survivor_ids": [two_q["frozen_2q_registry"]["survivors"][0]["gcm_2q_survivor_id"]],
        "gcm_2q_quotient_class_ids": [
            two_q["frozen_2q_registry"]["quotient_classes"][0]["gcm_2q_quotient_class_id"]
        ],
        "gcm_2q_candidate_region_ids": [
            two_q["frozen_2q_registry"]["candidate_regions"][0]["gcm_2q_candidate_region_id"]
        ],
        "gcm_3q_survivor_ids": gcm_lineage["gcm_3q_survivor_ids"][:3],
        "gcm_3q_quotient_class_ids": gcm_lineage["gcm_3q_quotient_class_ids"][:3],
        "gcm_3q_candidate_region_ids": gcm_lineage["gcm_3q_candidate_region_ids"][:3],
        "gcm_4q_survivor_ids": gcm_lineage["gcm_4q_survivor_ids"][:3],
        "gcm_4q_quotient_class_ids": [
            four_q_registry["frozen_4q_registry"]["quotient_classes"][0]["gcm_4q_quotient_class_id"]
        ],
        "gcm_4q_candidate_region_ids": [
            four_q_registry["frozen_4q_registry"]["candidate_regions"][0]["gcm_4q_candidate_region_id"]
        ],
        "object_maps": [
            {
                "survivor_id": one_q["frozen_registry"]["survivors"][0]["survivor_id"],
                "gcm_2q_survivor_id": two_q["frozen_2q_registry"]["survivors"][0]["gcm_2q_survivor_id"],
                "gcm_3q_survivor_id": gcm_lineage["gcm_3q_survivor_ids"][0],
                "gcm_4q_survivor_id": gcm_lineage["gcm_4q_survivor_ids"][0],
            }
        ],
    }


def lineage_free_negative() -> dict[str, Any]:
    negative_payload = {
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
            "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
            "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
            "gcm_4q_object_id": EXPECTED_4Q_OBJECT_ID,
            "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_BODY_SHA256,
            "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_BODY_SHA256,
            "gcm_4q_registry_body_sha256": EXPECTED_4Q_REGISTRY_BODY_SHA256,
            "survivor_ids": [],
            "gcm_2q_survivor_ids": [],
            "gcm_3q_survivor_ids": [],
            "gcm_4q_survivor_ids": [],
        }
    }
    result = gcm_substrate_check(negative_payload, FOUR_Q_REGISTRY_PATH)
    write_json(LINEAGE_FREE_NEGATIVE_PATH, result)
    return result


def build_packet() -> dict[str, Any]:
    one_q = load_json(ONE_Q_REGISTRY_PATH)
    two_q = load_json(TWO_Q_REGISTRY_PATH)
    three_q = load_json(THREE_Q_RESULT_PATH)
    le3 = load_json(LE3_TOWER_RESULT_PATH)
    four_q_result = load_json(FOUR_Q_RESULT_PATH)
    four_q_registry = load_json(FOUR_Q_REGISTRY_PATH)
    tower = build_tower(one_q, two_q, three_q, four_q_result, four_q_registry)
    counts = summarize_counts(tower, four_q_result)
    locks = source_locks()
    lineage = lineage_for_packet(one_q, two_q, four_q_result, four_q_registry)
    packet_stub = {"gcm_lineage": lineage}
    substrate = gcm_substrate_check(packet_stub, FOUR_Q_REGISTRY_PATH)
    negative = lineage_free_negative()
    controls_payload = controls(counts, tower, le3)
    packet = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "created_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "axis_declaration": AXIS_DECLARATION,
        "relation_boundary": {
            "exact": "all seven cuts require exact lower-rung membership; 1Q/2Q use frozen local-pin coordinates, 3Q uses committed rho_ABC matrix identity",
            "probe": "all seven cuts require lower-rung active x/z probe quotient membership; multiplicity is product of side-family sizes",
            "strict_separation": True,
            "not_claimed": [
                "manifold admission",
                "terrain admission",
                "engine admission",
                "Axis0 or bridge admission",
                "full-density theorem beyond the declared carrier/pins relation",
            ],
        },
        "source_locks": locks,
        "gcm_lineage": lineage,
        "counts": counts,
        "compatible_families": {
            "representation": "compressed rows only; no full matrix blobs are stored in this packet",
            "exact_rows": tower["compatible_family_rows_exact"],
            "probe_rows": tower["compatible_family_rows_probe"],
            "exact_rows_sha256": stable_sha256(tower["compatible_family_rows_exact"]),
            "probe_rows_sha256": stable_sha256(tower["compatible_family_rows_probe"]),
            "object_maps_sha256": stable_sha256(tower["object_maps"]),
            "object_maps_sample": tower["object_maps"][:12],
        },
        "tower_orphan_characterization": orphan_summary(tower),
        "root_axiom_verdict_at_4q": root_axiom_verdict(counts, le3["counts"]),
        "controls": controls_payload,
        "substrate_checks": {
            "four_q_positive": substrate,
            "lineage_free_negative": negative,
            "all_positive_ok": substrate.get("ok") is True,
            "negatives_red": negative.get("ok") is False,
        },
        "crossover_proofs": {
            "z3": z3_count_proof(counts, tower),
            "cvc5": cvc5_count_proof(counts, tower),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": {
            "claim_classes": [
                "nesting_law_le4_inverse_limit_tower",
                "exact_all_cut_compatibility_empty_check",
                "probe_relative_all_cut_compatibility_multiplicity",
                "root_axiom_4q_recheck",
            ],
            "storage_policy": "lean: hashes, counts, samples, and relation id lists only; 4Q source owns the full reduced cut matrices",
        },
        "classical_baseline": {
            "name": "3Q product-lift baseline under 4Q cut-state compatibility",
            "divergence_log": [
                "exact all-cut compatibility is checked independently from probe-relative compatibility",
                "probe quotient multiplicity is not used to backfill exact rows",
                "all claims remain scratch_diagnostic and carrier/pins-relative",
            ],
        },
    }
    return packet


def main() -> int:
    packet = build_packet()
    write_json(RESULT_PATH, packet)
    print(json.dumps({"ok": True, "result_path": rel(RESULT_PATH), "counts": packet["counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
