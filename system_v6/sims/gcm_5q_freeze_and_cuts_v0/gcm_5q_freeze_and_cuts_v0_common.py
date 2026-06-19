#!/usr/bin/env python3
"""5Q GCM registry freeze plus lean bipartition cut-state attachments."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "gcm_5q_freeze_and_cuts_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
REGISTRY_PATH = RESULT_DIR / f"{SIM_ID}_registry.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

FIVE_Q_CARVE_DIR = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_5q_v0"
FIVE_Q_CARVE_RESULT = FIVE_Q_CARVE_DIR / "results" / "gcm_constraint_carve_5q_v0_results.json"
FIVE_Q_CARVE_VALIDATOR = FIVE_Q_CARVE_DIR / "results" / "gcm_constraint_carve_5q_v0_validator_results.json"
FOUR_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_4q_freeze_and_cuts_v0" / "results" / "gcm_4q_freeze_and_cuts_v0_registry.json"
)
FOUR_Q_FREEZE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_4q_freeze_and_cuts_v0" / "results" / "gcm_4q_freeze_and_cuts_v0_results.json"
)
THREE_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_3q_freeze_and_cuts_v0" / "results" / "gcm_3q_freeze_and_cuts_v0_registry.json"
)
TWO_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_registry.json"
)
ONE_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
SIM_TEMPLATE = ROOT / "system_v4" / "probes" / "SIM_TEMPLATE.py"

CARVE_MODULE_DIR = FIVE_Q_CARVE_DIR
if str(CARVE_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(CARVE_MODULE_DIR))
import gcm_constraint_carve_5q_v0_common as carve_common  # noqa: E402

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_1Q_REGISTRY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_OBJECT_ID = "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
EXPECTED_3Q_REGISTRY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
EXPECTED_4Q_OBJECT_ID = "gcm4qobj_64fa5326aa89eae836e75e6c71fc8cdc"
EXPECTED_4Q_REGISTRY_SHA256 = "bf92c850a2880e26011080c900879cf729f8394ffc2e5d00bf1f70ed786020de"
EXPECTED_5Q_CANDIDATE_COUNT = 556
EXPECTED_5Q_SURVIVOR_COUNT = 547
EXPECTED_5Q_KILLED_COUNT = 9
EXPECTED_5Q_CLASS_COUNT = 9
EXPECTED_5Q_REGION_COUNT = 9
EXPECTED_5Q_PRODUCT_LIFT_COUNT = 546
EXPECTED_5Q_ENTANGLED_SURVIVOR_COUNT = 1
MAX_FILE_BYTES = 50 * 1024 * 1024
TOL = 1.0e-10

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_5q_freeze_cut_attachment_surface_carrier_pins_relative"
SCHEMA = f"{SIM_ID}_result_v1"
REGISTRY_SCHEMA = f"{SIM_ID}_registry_v1"

CUTS = carve_common.CUTS
SAMPLE_LABELS = [
    "GHZ5",
    "W5",
    "cluster_linear_5",
    "locally_rotated_generalized_GHZ5_anchor",
    "4q_lift_0",
    "4q_lift_544",
    "invalid_trace_anchor",
    "order_only_no_probe_anchor",
]

TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing drift-immune 1Q/2Q/3Q/4Q lineage consumption check for the 5Q freeze packet",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "content-addressed registry IDs, JSON serialization, SHA256 source locks, and file-size guards",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 5Q partial traces, reduced-state spectra, entropy rows, and sample matrix recomputation",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary check from birth",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "not used; this freeze packet adds no new solver proof, so z3 would be decorative",
    },
    "cvc5": {
        "tried": False,
        "used": False,
        "reason": "not used; this freeze packet adds no new solver proof, so cvc5 would be decorative",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "python_stdlib": "load_bearing",
    "numpy": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "z3": None,
    "cvc5": None,
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def q(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if abs(rounded) <= TOL else rounded


def matrix_to_json(matrix: np.ndarray) -> list[list[list[float]]]:
    return carve_common.matrix_to_json(matrix)


def json_to_matrix(value: list[list[Any]]) -> np.ndarray:
    return carve_common.json_to_matrix(value)


def entropy_nats(matrix: np.ndarray) -> float:
    eigs = np.linalg.eigvalsh((matrix + np.conjugate(matrix.T)) / 2.0)
    return carve_common.entropy_nats_from_eigs(eigs)


def matrix_rank(matrix: np.ndarray) -> int:
    eigs = np.linalg.eigvalsh((matrix + np.conjugate(matrix.T)) / 2.0)
    return int(np.sum(np.real(eigs) > TOL))


def reduced_pair(rho: np.ndarray, cut_name: str) -> tuple[np.ndarray, np.ndarray]:
    spec = CUTS[cut_name]
    return carve_common.partial_trace(rho, spec["left"]), carve_common.partial_trace(rho, spec["right"])


def reduced_hash_row(rho: np.ndarray, cut_name: str) -> dict[str, Any]:
    left, right = reduced_pair(rho, cut_name)
    left_json = matrix_to_json(left)
    right_json = matrix_to_json(right)
    s_left = entropy_nats(left)
    s_right = entropy_nats(right)
    s_full = entropy_nats(rho)
    return {
        "cut": cut_name,
        "left_qubits": CUTS[cut_name]["left"],
        "right_qubits": CUTS[cut_name]["right"],
        "rho_left_shape": [int(left.shape[0]), int(left.shape[1])],
        "rho_right_shape": [int(right.shape[0]), int(right.shape[1])],
        "rho_left_hash": stable_sha256(left_json),
        "rho_right_hash": stable_sha256(right_json),
        "rho_left_id": stable_id("rho5qL", {"cut": cut_name, "matrix": left_json}),
        "rho_right_id": stable_id("rho5qR", {"cut": cut_name, "matrix": right_json}),
        "rho_left_rank": matrix_rank(left),
        "rho_right_rank": matrix_rank(right),
        "entropy_values": {
            "S_rho_left": s_left,
            "S_rho_right": s_right,
            "S_rho_ABCDE": s_full,
            "conditional_S_left_given_right": q(s_full - s_right),
            "conditional_S_right_given_left": q(s_full - s_left),
            "mutual_I_left_right": q(s_left + s_right - s_full),
            "coherent_I_c_left_to_right": q(s_right - s_full),
            "coherent_I_c_right_to_left": q(s_left - s_full),
        },
    }


def sample_cut_row(rho: np.ndarray, cut_name: str) -> dict[str, Any]:
    row = reduced_hash_row(rho, cut_name)
    left, right = reduced_pair(rho, cut_name)
    row["rho_left"] = matrix_to_json(left)
    row["rho_right"] = matrix_to_json(right)
    row["sample_full_reduced_matrices_stored"] = True
    return row


def state_by_content(carve: dict[str, Any], content_id: str) -> np.ndarray:
    return json_to_matrix(carve["state_artifacts"]["states_by_content_id"][content_id]["rho_ABCDE"])


def clean_survivor_for_registry(row: dict[str, Any], gcm_5q_object_id: str) -> dict[str, Any]:
    payload = {
        "gcm_5q_object_id": gcm_5q_object_id,
        "raw_5q_survivor_id": row["survivor_id"],
        "candidate_id": row["candidate_id"],
        "candidate_label": row["candidate_label"],
        "family": row["family"],
        "rho_ABCDE_content_id": row["rho_ABCDE_content_id"],
        "source_4q_survivor_id": row.get("source_4q_survivor_id"),
    }
    out = {
        "gcm_5q_survivor_id": stable_id("gcm5qsurv", payload),
        "raw_5q_survivor_id": row["survivor_id"],
        "candidate_id": row["candidate_id"],
        "candidate_label": row["candidate_label"],
        "family": row["family"],
        "rho_ABCDE_content_id": row["rho_ABCDE_content_id"],
        "source_4q_survivor_id": row.get("source_4q_survivor_id"),
        "source_4q_candidate_id": row.get("source_4q_candidate_id"),
        "source_4q_family": row.get("source_4q_family"),
        "source_rho_ABCD_content_id": row.get("source_rho_ABCD_content_id"),
        "five_partite_entangled_anchor": bool(row.get("five_partite_entangled_anchor")),
        "content_sha256": stable_sha256(payload),
    }
    return out


def build_5q_registry(carve: dict[str, Any], four_q_registry: dict[str, Any]) -> dict[str, Any]:
    pinned = {
        "base_gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "gcm_4q_object_id": EXPECTED_4Q_OBJECT_ID,
        "gcm_4q_registry_body_sha256": EXPECTED_4Q_REGISTRY_SHA256,
        "five_q_carve_result_sha256": sha256_file(FIVE_Q_CARVE_RESULT),
        "survivor_count": carve["survivor_count"],
        "quotient_class_count": carve["quotient"]["class_count"],
        "survivor_family_counts": carve["survivor_family_counts"],
        "cut_lattice": list(CUTS),
        "lean_cut_state_policy": "hash_per_survivor_cut_plus_sample_full_reduced_matrices",
    }
    gcm_5q_object_id = stable_id("gcm5qobj", pinned, length=32)
    survivor_rows = [clean_survivor_for_registry(row, gcm_5q_object_id) for row in carve["survivors"]]
    by_raw = {row["raw_5q_survivor_id"]: row["gcm_5q_survivor_id"] for row in survivor_rows}

    class_rows = []
    for qrow in carve["quotient"]["classes"]:
        member_ids = [by_raw[int(raw_sid)] for raw_sid in qrow["member_survivor_ids"]]
        payload = {
            "gcm_5q_object_id": gcm_5q_object_id,
            "raw_class_id": qrow["class_id"],
            "probe_signature": qrow["probe_signature"],
            "member_gcm_5q_survivor_ids": member_ids,
        }
        class_rows.append(
            {
                "gcm_5q_quotient_class_id": stable_id("gcm5qqcls", payload),
                "raw_class_id": qrow["class_id"],
                "probe_signature": qrow["probe_signature"],
                "member_gcm_5q_survivor_ids": member_ids,
                "member_raw_5q_survivor_ids": qrow["member_survivor_ids"],
                "member_count": qrow["member_count"],
                "family_counts": qrow["family_counts"],
                "five_partite_entangled_anchor_count": qrow["five_partite_entangled_anchor_count"],
                "content_sha256": stable_sha256(payload),
            }
        )

    region_rows = []
    for qrow, class_row in zip(carve["quotient"]["classes"], class_rows, strict=True):
        payload = {
            "gcm_5q_object_id": gcm_5q_object_id,
            "raw_region_id": qrow["class_id"],
            "member_gcm_5q_quotient_class_ids": [class_row["gcm_5q_quotient_class_id"]],
            "cut_lattice": list(CUTS),
            "region_scope": "class_local_5q_lean_cut_state_attachment_region",
        }
        region_rows.append(
            {
                "gcm_5q_candidate_region_id": stable_id("gcm5qcreg", payload),
                "raw_region_id": qrow["class_id"],
                "region_scope": "class_local_5q_lean_cut_state_attachment_region",
                "member_gcm_5q_quotient_class_ids": [class_row["gcm_5q_quotient_class_id"]],
                "member_raw_class_ids": [qrow["class_id"]],
                "can_affect_survival": False,
                "content_sha256": stable_sha256(payload),
            }
        )

    registry = {
        "schema": REGISTRY_SCHEMA,
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "gcm_4q_object_id": EXPECTED_4Q_OBJECT_ID,
        "gcm_4q_registry_body_sha256": EXPECTED_4Q_REGISTRY_SHA256,
        "gcm_5q_object_id": gcm_5q_object_id,
        "gcm_5q_object_id_rule": "sha256 over 1Q/2Q/3Q/4Q object identities, pinned 5Q carve result, 5Q survivor/class counts, survivor family counts, 15-cut lattice, and lean cut-state policy",
        "pinned_spec_sha256": stable_sha256(pinned),
        "frozen_registry": four_q_registry["frozen_registry"],
        "frozen_2q_registry": four_q_registry["frozen_2q_registry"],
        "frozen_3q_registry": four_q_registry["frozen_3q_registry"],
        "frozen_4q_registry": four_q_registry["frozen_4q_registry"],
        "frozen_5q_registry": {
            "survivors": survivor_rows,
            "quotient_classes": class_rows,
            "candidate_regions": region_rows,
        },
        "counts": {
            "candidate_count": carve["candidate_space"]["candidate_count"],
            "survivor_count": len(survivor_rows),
            "killed_count": len(carve["killed_rows"]),
            "quotient_class_count": len(class_rows),
            "candidate_region_count": len(region_rows),
            "product_lift_survivor_count": sum(1 for row in survivor_rows if row["family"] == "4q_survivor_product_lift"),
            "five_partite_entangled_survivor_count": sum(1 for row in survivor_rows if row["five_partite_entangled_anchor"]),
        },
        "source_locks": {
            "five_q_carve_result": source_lock(FIVE_Q_CARVE_RESULT, "state-artifacted 547 survivor 5Q carve source"),
            "five_q_carve_validator": source_lock(FIVE_Q_CARVE_VALIDATOR, "5Q carve validator receipt"),
            "four_q_freeze_registry": source_lock(FOUR_Q_FREEZE_REGISTRY, "4Q freeze registry lineage source"),
            "four_q_freeze_result": source_lock(FOUR_Q_FREEZE_RESULT, "4Q freeze result source"),
            "sim_template": source_lock(SIM_TEMPLATE, "new-sim template reference"),
        },
    }
    body = dict(registry)
    registry["registry_body_sha256"] = stable_sha256(body)
    return registry


def registry_maps(registry: dict[str, Any]) -> dict[str, dict[Any, str]]:
    return {
        "gcm5q_by_raw": {
            row["raw_5q_survivor_id"]: row["gcm_5q_survivor_id"]
            for row in registry["frozen_5q_registry"]["survivors"]
        },
        "gcm5q_class_by_raw": {
            row["raw_class_id"]: row["gcm_5q_quotient_class_id"]
            for row in registry["frozen_5q_registry"]["quotient_classes"]
        },
        "gcm5q_region_by_raw_class": {
            row["member_raw_class_ids"][0]: row["gcm_5q_candidate_region_id"]
            for row in registry["frozen_5q_registry"]["candidate_regions"]
        },
    }


def raw_class_for_survivor(carve: dict[str, Any]) -> dict[int, str]:
    out = {}
    for qrow in carve["quotient"]["classes"]:
        for raw_sid in qrow["member_survivor_ids"]:
            out[int(raw_sid)] = qrow["class_id"]
    return out


def four_q_by_raw(four_q_registry: dict[str, Any]) -> dict[int, dict[str, Any]]:
    return {
        int(row["raw_4q_survivor_id"]): row
        for row in four_q_registry["frozen_4q_registry"]["survivors"]
    }


def first_nested_id(registry: dict[str, Any], section: str, field: str) -> str:
    bucket = "survivors" if field.endswith("survivor_id") else "quotient_classes"
    if field.endswith("candidate_region_id"):
        bucket = "candidate_regions"
    for row in registry.get(section, {}).get(bucket, []):
        value = row.get(field)
        if isinstance(value, str):
            return value
    raise KeyError(f"{section}.{field}")


def helper_lineage(four_q_registry: dict[str, Any], object_maps: list[dict[str, Any]]) -> dict[str, Any]:
    one_q_survivor = first_nested_id(four_q_registry, "frozen_registry", "survivor_id")
    one_q_class = first_nested_id(four_q_registry, "frozen_registry", "quotient_class_id")
    one_q_region = first_nested_id(four_q_registry, "frozen_registry", "candidate_region_id")
    two_q_survivor = first_nested_id(four_q_registry, "frozen_2q_registry", "gcm_2q_survivor_id")
    two_q_class = first_nested_id(four_q_registry, "frozen_2q_registry", "gcm_2q_quotient_class_id")
    two_q_region = first_nested_id(four_q_registry, "frozen_2q_registry", "gcm_2q_candidate_region_id")
    three_q_survivor = first_nested_id(four_q_registry, "frozen_3q_registry", "gcm_3q_survivor_id")
    three_q_class = first_nested_id(four_q_registry, "frozen_3q_registry", "gcm_3q_quotient_class_id")
    three_q_region = first_nested_id(four_q_registry, "frozen_3q_registry", "gcm_3q_candidate_region_id")
    return {
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_4q_object_id": EXPECTED_4Q_OBJECT_ID,
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "one_q_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "gcm_4q_registry_body_sha256": EXPECTED_4Q_REGISTRY_SHA256,
        "survivor_ids": [one_q_survivor],
        "quotient_class_ids": [one_q_class],
        "candidate_region_ids": [one_q_region],
        "gcm_2q_survivor_ids": [two_q_survivor],
        "gcm_2q_quotient_class_ids": [two_q_class],
        "gcm_2q_candidate_region_ids": [two_q_region],
        "gcm_3q_survivor_ids": [three_q_survivor],
        "gcm_3q_quotient_class_ids": [three_q_class],
        "gcm_3q_candidate_region_ids": [three_q_region],
        "gcm_4q_survivor_ids": [row["gcm_4q_survivor_id"] for row in object_maps if row.get("gcm_4q_survivor_id")],
        "gcm_4q_quotient_class_ids": [
            row["gcm_4q_quotient_class_id"]
            for row in four_q_registry["frozen_4q_registry"]["quotient_classes"]
        ],
        "gcm_4q_candidate_region_ids": [
            row["gcm_4q_candidate_region_id"]
            for row in four_q_registry["frozen_4q_registry"]["candidate_regions"]
        ],
        "object_maps": object_maps,
    }


def cross_rung_lineage(
    carve: dict[str, Any],
    registry: dict[str, Any],
    four_q_registry: dict[str, Any],
) -> dict[str, Any]:
    maps = registry_maps(registry)
    class_by_raw = raw_class_for_survivor(carve)
    four_by_raw = four_q_by_raw(four_q_registry)
    object_maps = []
    product_rows = []
    for row in carve["survivors"]:
        raw_sid = int(row["survivor_id"])
        raw_class = class_by_raw[raw_sid]
        map_row = {
            "gcm_5q_object_id": registry["gcm_5q_object_id"],
            "gcm_5q_survivor_id": maps["gcm5q_by_raw"][raw_sid],
            "raw_5q_survivor_id": raw_sid,
            "candidate_id": row["candidate_id"],
            "candidate_label": row["candidate_label"],
            "family": row["family"],
            "gcm_5q_quotient_class_id": maps["gcm5q_class_by_raw"][raw_class],
            "gcm_5q_candidate_region_id": maps["gcm5q_region_by_raw_class"][raw_class],
            "rho_ABCDE_content_id": row["rho_ABCDE_content_id"],
            "five_partite_entangled_anchor": bool(row.get("five_partite_entangled_anchor")),
        }
        if row["family"] == "4q_survivor_product_lift":
            source_raw = int(row["source_4q_survivor_id"])
            four_row = four_by_raw[source_raw]
            map_row.update(
                {
                    "gcm_4q_survivor_id": four_row["gcm_4q_survivor_id"],
                    "raw_4q_survivor_id": source_raw,
                    "projection": "Tr_E(rho_ABCDE) -> source 4Q rho_ABCD",
                }
            )
            product_rows.append(
                {
                    "gcm_4q_survivor_id": four_row["gcm_4q_survivor_id"],
                    "raw_4q_survivor_id": source_raw,
                    "gcm_5q_survivor_id": maps["gcm5q_by_raw"][raw_sid],
                    "raw_5q_survivor_id": raw_sid,
                    "candidate_id": row["candidate_id"],
                }
            )
        else:
            map_row.update(
                {
                    "gcm_4q_survivor_id": None,
                    "raw_4q_survivor_id": None,
                    "projection": "5Q-only entangled anchor has no 4Q registry source row",
                }
            )
        object_maps.append(map_row)
    return {
        "row_id": "cross_rung_4q_5q_product_embedding_and_projection",
        "base_gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "gcm_4q_object_id": EXPECTED_4Q_OBJECT_ID,
        "gcm_4q_registry_body_sha256": EXPECTED_4Q_REGISTRY_SHA256,
        "gcm_5q_object_id": registry["gcm_5q_object_id"],
        "gcm_5q_registry_body_sha256": registry["registry_body_sha256"],
        "gcm_4q_survivor_ids": [row["gcm_4q_survivor_id"] for row in product_rows],
        "gcm_5q_survivor_ids": [row["gcm_5q_survivor_id"] for row in object_maps],
        "gcm_5q_quotient_class_ids": [
            row["gcm_5q_quotient_class_id"] for row in registry["frozen_5q_registry"]["quotient_classes"]
        ],
        "gcm_5q_candidate_region_ids": [
            row["gcm_5q_candidate_region_id"] for row in registry["frozen_5q_registry"]["candidate_regions"]
        ],
        "object_maps": object_maps,
        "four_q_to_5q_product_embedding": {
            "input_4q_survivor_count": EXPECTED_5Q_PRODUCT_LIFT_COUNT,
            "lifted_5q_survivor_count": len(product_rows),
            "all_4q_survivors_have_one_5q_lift": len(product_rows) == EXPECTED_5Q_PRODUCT_LIFT_COUNT,
            "construction": "rho_ABCD survivor tensor |0><0|_E from gcm_constraint_carve_5q_v0",
        },
    }


def sample_candidates(carve: dict[str, Any]) -> list[dict[str, Any]]:
    rows = {row["candidate_label"]: row for row in carve["survivors"] + carve["killed_rows"]}
    samples = []
    for label in SAMPLE_LABELS:
        row = rows[label]
        samples.append(
            {
                "candidate_label": label,
                "candidate_id": row["candidate_id"],
                "raw_5q_survivor_id": row.get("survivor_id"),
                "survives": label in {item["candidate_label"] for item in carve["survivors"]},
                "family": row["family"],
                "rho_ABCDE_content_id": row["rho_ABCDE_content_id"],
                "failed_constraints": row.get("all_failed_constraints", []),
            }
        )
    return samples


def survivor_cut_hash_rows(carve: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    maps = registry_maps(registry)
    class_by_raw = raw_class_for_survivor(carve)
    rows = []
    for survivor in carve["survivors"]:
        raw_sid = int(survivor["survivor_id"])
        rho = state_by_content(carve, survivor["rho_ABCDE_content_id"])
        raw_class = class_by_raw[raw_sid]
        cuts = {cut_name: reduced_hash_row(rho, cut_name) for cut_name in CUTS}
        rows.append(
            {
                "gcm_5q_survivor_id": maps["gcm5q_by_raw"][raw_sid],
                "raw_5q_survivor_id": raw_sid,
                "candidate_id": survivor["candidate_id"],
                "candidate_label": survivor["candidate_label"],
                "family": survivor["family"],
                "rho_ABCDE_content_id": survivor["rho_ABCDE_content_id"],
                "gcm_5q_quotient_class_id": maps["gcm5q_class_by_raw"][raw_class],
                "gcm_5q_candidate_region_id": maps["gcm5q_region_by_raw_class"][raw_class],
                "source_4q_survivor_id": survivor.get("source_4q_survivor_id"),
                "five_partite_entangled_anchor": bool(survivor.get("five_partite_entangled_anchor")),
                "cut_state_available": True,
                "full_reduced_matrices_stored": False,
                "cuts": cuts,
            }
        )
    return rows


def sample_cut_matrix_pairs(carve: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for sample in sample_candidates(carve):
        rho = state_by_content(carve, sample["rho_ABCDE_content_id"])
        rows.append(
            {
                **sample,
                "cut_state_available": True,
                "sample_full_reduced_matrices_stored": True,
                "cuts": {cut_name: sample_cut_row(rho, cut_name) for cut_name in CUTS},
            }
        )
    return rows


def class_cut_hash_rows(registry: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_class[row["gcm_5q_quotient_class_id"]].append(row)
    raw_by_qid = {
        row["gcm_5q_quotient_class_id"]: row
        for row in registry["frozen_5q_registry"]["quotient_classes"]
    }
    out = []
    for qid in sorted(by_class, key=lambda item: raw_by_qid[item]["raw_class_id"]):
        members = by_class[qid]
        cut_stats = {}
        for cut_name in CUTS:
            cut_stats[cut_name] = {}
            for metric in members[0]["cuts"][cut_name]["entropy_values"]:
                values = [float(row["cuts"][cut_name]["entropy_values"][metric]) for row in members]
                cut_stats[cut_name][metric] = {
                    "min": q(min(values)),
                    "max": q(max(values)),
                    "mean": q(sum(values) / len(values)),
                    "unique_count": len({q(value) for value in values}),
                }
        out.append(
            {
                "gcm_5q_quotient_class_id": qid,
                "raw_class_id": raw_by_qid[qid]["raw_class_id"],
                "member_count": len(members),
                "member_gcm_5q_survivor_ids": [row["gcm_5q_survivor_id"] for row in members],
                "five_partite_entangled_anchor_count": sum(1 for row in members if row["five_partite_entangled_anchor"]),
                "cut_metric_stats": cut_stats,
            }
        )
    return out


def helper_payload_from_lineage(four_q_registry: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    product_maps = [
        row
        for row in lineage["object_maps"]
        if row.get("gcm_4q_survivor_id") is not None
    ]
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "gcm_lineage": helper_lineage(four_q_registry, product_maps),
    }


def check_with_registry(payload: dict[str, Any], registry: dict[str, Any], committed_path: Path) -> dict[str, Any]:
    if committed_path.exists():
        try:
            if load_json(committed_path) == registry:
                return gcm_substrate_check(payload, committed_path)
        except Exception:
            pass
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "registry.json"
        write_json(path, registry)
        result = gcm_substrate_check(payload, path)
        result["registry_path"] = f"temporary_registry:{stable_sha256(registry)[:16]}"
        return result


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    lineage = variant.setdefault("gcm_lineage", {})
    for key in (
        "survivor_ids",
        "quotient_class_ids",
        "candidate_region_ids",
        "gcm_2q_survivor_ids",
        "gcm_2q_quotient_class_ids",
        "gcm_2q_candidate_region_ids",
        "gcm_3q_survivor_ids",
        "gcm_3q_quotient_class_ids",
        "gcm_3q_candidate_region_ids",
        "gcm_4q_survivor_ids",
        "gcm_4q_quotient_class_ids",
        "gcm_4q_candidate_region_ids",
        "object_maps",
    ):
        lineage[key] = []
    return variant


def stale_lineage_variant(payload: dict[str, Any], key: str) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    lineage = variant.setdefault("gcm_lineage", {})
    lineage[key] = "0" * 64
    return variant


def substrate_control_matrix(helper_payload: dict[str, Any]) -> dict[str, Any]:
    four_q_registry = load_json(FOUR_Q_FREEZE_REGISTRY)
    positives = {"4Q": check_with_registry(helper_payload, four_q_registry, FOUR_Q_FREEZE_REGISTRY)}
    negatives = {
        "4Q": {
            "lineage_free": check_with_registry(lineage_free_variant(helper_payload), four_q_registry, FOUR_Q_FREEZE_REGISTRY),
            "stale_4q_lineage": check_with_registry(
                stale_lineage_variant(helper_payload, "gcm_4q_registry_body_sha256"),
                four_q_registry,
                FOUR_Q_FREEZE_REGISTRY,
            ),
        }
    }
    return {"substrate_positive": positives, "substrate_negatives": negatives}


def sample_recompute_report(carve: dict[str, Any], sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    mismatches = []
    checked = 0
    for sample in sample_rows:
        rho = state_by_content(carve, sample["rho_ABCDE_content_id"])
        for cut_name, stored in sample["cuts"].items():
            recomputed = sample_cut_row(rho, cut_name)
            checked += 1
            for key in ("rho_left_hash", "rho_right_hash", "rho_left", "rho_right"):
                if recomputed[key] != stored[key]:
                    mismatches.append({"candidate_label": sample["candidate_label"], "cut": cut_name, "key": key})
    return {
        "checked_sample_cut_pairs": checked,
        "sample_recompute_pass": not mismatches,
        "mismatches": mismatches,
    }


def mutation_sensitivity(carve: dict[str, Any], sample_rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = copy.deepcopy(sample_rows[0])
    cut_name = next(iter(CUTS))
    first["cuts"][cut_name]["rho_left"][0][0][0] = q(first["cuts"][cut_name]["rho_left"][0][0][0] + 0.125)
    rho = state_by_content(carve, first["rho_ABCDE_content_id"])
    recomputed = sample_cut_row(rho, cut_name)
    mutated_hash = stable_sha256(first["cuts"][cut_name]["rho_left"])
    return {
        "control": "sample reduced matrix mutation must flip hash comparison",
        "candidate_label": first["candidate_label"],
        "cut": cut_name,
        "expected_rho_left_hash": recomputed["rho_left_hash"],
        "mutated_rho_left_hash": mutated_hash,
        "mutation_detected": mutated_hash != recomputed["rho_left_hash"],
    }


def file_size_guard() -> dict[str, Any]:
    rows = []
    for path in sorted(SIM_DIR.rglob("*")):
        if path.is_file():
            size = path.stat().st_size
            rows.append({"path": rel(path), "bytes": size, "under_50mb": size < MAX_FILE_BYTES})
    return {
        "max_file_bytes": MAX_FILE_BYTES,
        "all_files_under_50mb": all(row["under_50mb"] for row in rows),
        "files": rows,
        "largest_file": max(rows, key=lambda row: row["bytes"]) if rows else None,
    }


def all_pass_substrate_controls(controls: dict[str, Any]) -> bool:
    positives = controls["substrate_positive"]
    negatives = controls["substrate_negatives"]
    return all(row.get("ok") is True for row in positives.values()) and all(
        item.get("ok") is False and bool(item.get("error_codes")) for rung in negatives.values() for item in rung.values()
    )


def build_packet(*, write: bool = True) -> dict[str, Any]:
    carve = load_json(FIVE_Q_CARVE_RESULT)
    four_q_registry = load_json(FOUR_Q_FREEZE_REGISTRY)
    registry = build_5q_registry(carve, four_q_registry)
    if write:
        write_json(REGISTRY_PATH, registry)

    lineage = cross_rung_lineage(carve, registry, four_q_registry)
    helper_payload = helper_payload_from_lineage(four_q_registry, lineage)
    substrate_controls = substrate_control_matrix(helper_payload)
    hash_rows = survivor_cut_hash_rows(carve, registry)
    sample_rows = sample_cut_matrix_pairs(carve)
    class_rows = class_cut_hash_rows(registry, hash_rows)
    recompute = sample_recompute_report(carve, sample_rows)
    mutation = mutation_sensitivity(carve, sample_rows)
    no_audit = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")

    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "declared_surface": "5Q freeze/registry + lean cut-state map | carve-attached | Cl(10)/C^32 density carrier",
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "cut_state_available": True,
        "cut_state_available_semantics": "recomputable cut-state map via per-survivor/cut reduced-state hashes plus capped sample full reduced matrices; not a full all-survivor matrix blob",
        "lean_storage_policy": {
            "full_all_survivor_cut_matrices_stored": False,
            "survivor_cut_hash_rows_stored": True,
            "sample_full_reduced_matrices_stored": True,
            "sample_candidate_labels": SAMPLE_LABELS,
            "honest_limit": "Only sample full reduced matrices are stored and recomputed here; all other full reduced matrices must be recomputed from the pinned 5Q carve state source.",
        },
        "cut_state_available_evidence": {
            "survivor_count": len(hash_rows),
            "cut_count": len(CUTS),
            "hash_pair_count": len(hash_rows) * len(CUTS),
            "sample_candidate_count": len(sample_rows),
            "sample_cut_pair_count": len(sample_rows) * len(CUTS),
            "matrix_fields_full_population": [],
            "matrix_fields_sample": ["rho_left", "rho_right"],
        },
        "coordinates": {
            "layers": "5Q freeze/registry plus all unordered bipartition cut-state hash attachments",
            "qubit_depth": "5Q",
            "carrier": "Cl(10) / C^32 density carrier from gcm_constraint_carve_5q_v0",
        },
        "cut_lattice": {
            "count": len(CUTS),
            "bipartitions": list(CUTS),
            "tensor_order": "computational basis |01234> with index = 16*q0 + 8*q1 + 4*q2 + 2*q3 + q4",
            "stored_reductions": "hashes for all survivor/cut rho_left/rho_right; full matrices for sample only",
        },
        "gcm_5q_object_id": registry["gcm_5q_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "registry_path": rel(REGISTRY_PATH),
        "gcm_lineage": helper_payload["gcm_lineage"],
        "cross_rung_lineage": lineage,
        "counts": {
            "candidate_count": carve["candidate_space"]["candidate_count"],
            "five_q_survivor_count": len(hash_rows),
            "five_q_killed_count": len(carve["killed_rows"]),
            "five_q_class_count": len(class_rows),
            "five_q_candidate_region_count": len(registry["frozen_5q_registry"]["candidate_regions"]),
            "product_lift_survivor_count": registry["counts"]["product_lift_survivor_count"],
            "five_partite_entangled_survivor_count": registry["counts"]["five_partite_entangled_survivor_count"],
        },
        "frozen_5q_registry": registry["frozen_5q_registry"],
        "cut_tables": {
            "survivor_cut_hash_rows": hash_rows,
            "class_cut_hash_rows": class_rows,
            "sample_cut_matrix_pairs": sample_rows,
        },
        "controls": {
            **substrate_controls,
            "sample_recompute": recompute,
            "mutation_sensitivity": mutation,
            "boundary_size_guard": {"required_max_file_bytes": MAX_FILE_BYTES},
            "positive_counts": {
                "survivor_count_ok": len(hash_rows) == EXPECTED_5Q_SURVIVOR_COUNT,
                "class_count_ok": len(class_rows) == EXPECTED_5Q_CLASS_COUNT,
                "region_count_ok": len(registry["frozen_5q_registry"]["candidate_regions"]) == EXPECTED_5Q_REGION_COUNT,
                "cut_count_ok": len(CUTS) == 15,
            },
        },
        "source_locks": {
            "five_q_carve_result": source_lock(FIVE_Q_CARVE_RESULT, "state-artifacted 547 survivor 5Q carve source"),
            "five_q_carve_validator": source_lock(FIVE_Q_CARVE_VALIDATOR, "5Q carve validator receipt"),
            "four_q_freeze_registry": source_lock(FOUR_Q_FREEZE_REGISTRY, "4Q freeze registry lineage source"),
            "four_q_freeze_result": source_lock(FOUR_Q_FREEZE_RESULT, "4Q freeze result source"),
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "1Q frozen substrate registry"),
            "two_q_freeze_registry": source_lock(TWO_Q_FREEZE_REGISTRY, "2Q frozen substrate registry"),
            "three_q_freeze_registry": source_lock(THREE_Q_FREEZE_REGISTRY, "3Q frozen substrate registry"),
            "sim_template": source_lock(SIM_TEMPLATE, "SIM_TEMPLATE.py reference"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "G_2a_idempotency_from_birth": no_audit,
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": no_audit,
            "no_builder_audit_verdict_envelope_gate": no_audit,
        },
        "allowed_claims": [
            "5Q registry freeze over pinned carve survivor/class/region source",
            "5Q lean recomputable cut-state attachment surface",
            "hash-level reduced-state availability for all 547 survivors across 15 cuts",
            "sample full reduced matrix recomputation for GHZ5/W5/cluster plus survivor/control rows",
            "carrier/pins-relative prerequisite for the <=5Q tower",
        ],
        "blocked_consumers": [
            "formal_admission",
            "canonical_manifold_claim",
            "axis_or_bridge_claim",
            "physics_claim",
            "full_all_survivor_reduced_matrix_blob_claim",
            "SLOCC_or_five_party_entanglement_classification_claim",
        ],
        "file_size_guard": None,
    }
    payload["all_pass"] = not validate_payload(payload, require_file_size=False)
    payload["result_sha256"] = stable_sha256({key: value for key, value in payload.items() if key != "generated_at"})
    if write:
        write_json(RESULT_PATH, payload)
        write_json(LINEAGE_FREE_NEGATIVE_PATH, lineage_free_variant(helper_payload))
        payload["file_size_guard"] = file_size_guard()
        payload["all_pass"] = not validate_payload(payload, require_file_size=True)
        payload["result_sha256"] = stable_sha256({key: value for key, value in payload.items() if key != "generated_at"})
        write_json(RESULT_PATH, payload)
    return payload


def validate_payload(payload: dict[str, Any], *, require_file_size: bool = True) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != CLASSIFICATION:
        errors.append("classification mismatch")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission fences must be false")
    if payload.get("cut_state_available") is not True:
        errors.append("cut_state_available must be true")
    if payload.get("lean_storage_policy", {}).get("full_all_survivor_cut_matrices_stored") is not False:
        errors.append("full all-survivor cut matrices must not be stored")
    counts = payload.get("counts", {})
    if counts.get("candidate_count") != EXPECTED_5Q_CANDIDATE_COUNT:
        errors.append("candidate count mismatch")
    if counts.get("five_q_survivor_count") != EXPECTED_5Q_SURVIVOR_COUNT:
        errors.append("5Q survivor count mismatch")
    if counts.get("five_q_killed_count") != EXPECTED_5Q_KILLED_COUNT:
        errors.append("5Q killed count mismatch")
    if counts.get("five_q_class_count") != EXPECTED_5Q_CLASS_COUNT:
        errors.append("5Q class count mismatch")
    if counts.get("five_q_candidate_region_count") != EXPECTED_5Q_REGION_COUNT:
        errors.append("5Q region count mismatch")
    if counts.get("product_lift_survivor_count") != EXPECTED_5Q_PRODUCT_LIFT_COUNT:
        errors.append("5Q product-lift survivor count mismatch")
    if counts.get("five_partite_entangled_survivor_count") != EXPECTED_5Q_ENTANGLED_SURVIVOR_COUNT:
        errors.append("5Q entangled survivor count mismatch")
    evidence = payload.get("cut_state_available_evidence", {})
    if evidence.get("hash_pair_count") != EXPECTED_5Q_SURVIVOR_COUNT * 15:
        errors.append("hash-pair count mismatch")
    if evidence.get("sample_candidate_count") != len(SAMPLE_LABELS):
        errors.append("sample candidate count mismatch")
    if evidence.get("sample_cut_pair_count") != len(SAMPLE_LABELS) * 15:
        errors.append("sample cut-pair count mismatch")
    cut_rows = payload.get("cut_tables", {}).get("survivor_cut_hash_rows", [])
    if len(cut_rows) != EXPECTED_5Q_SURVIVOR_COUNT:
        errors.append("survivor cut hash row count mismatch")
    for row in cut_rows[:3] + cut_rows[-3:]:
        if row.get("full_reduced_matrices_stored") is not False:
            errors.append(f"full matrices leaked into hash row {row.get('raw_5q_survivor_id')}")
        if set(row.get("cuts", {})) != set(CUTS):
            errors.append(f"missing cuts in hash row {row.get('raw_5q_survivor_id')}")
    sample_rows = payload.get("cut_tables", {}).get("sample_cut_matrix_pairs", [])
    if [row.get("candidate_label") for row in sample_rows] != SAMPLE_LABELS:
        errors.append("sample labels mismatch")
    for row in sample_rows:
        if row.get("sample_full_reduced_matrices_stored") is not True:
            errors.append(f"sample full matrices missing for {row.get('candidate_label')}")
        if set(row.get("cuts", {})) != set(CUTS):
            errors.append(f"sample missing cuts for {row.get('candidate_label')}")
        for cut in row.get("cuts", {}).values():
            if "rho_left" not in cut or "rho_right" not in cut:
                errors.append(f"sample reduced matrices missing for {row.get('candidate_label')}")
                break
    controls = payload.get("controls", {})
    if not all_pass_substrate_controls(
        {
            "substrate_positive": controls.get("substrate_positive", {}),
            "substrate_negatives": controls.get("substrate_negatives", {}),
        }
    ):
        errors.append("substrate controls failed")
    if controls.get("sample_recompute", {}).get("sample_recompute_pass") is not True:
        errors.append("sample recompute failed")
    if controls.get("mutation_sensitivity", {}).get("mutation_detected") is not True:
        errors.append("mutation sensitivity did not flip")
    positives = controls.get("positive_counts", {})
    if not all(positives.values()):
        errors.append("positive count controls failed")
    if payload.get("TOOL_MANIFEST") != TOOL_MANIFEST:
        errors.append("TOOL_MANIFEST mismatch")
    if payload.get("TOOL_INTEGRATION_DEPTH") != TOOL_INTEGRATION_DEPTH:
        errors.append("TOOL_INTEGRATION_DEPTH mismatch")
    if not any(depth == "load_bearing" for tool, depth in TOOL_INTEGRATION_DEPTH.items() if tool != "numpy"):
        errors.append("missing non-numeric load-bearing tool depth")
    if require_file_size:
        guard = payload.get("file_size_guard", {})
        if guard.get("all_files_under_50mb") is not True:
            errors.append("file-size guard failed")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    return errors


def main() -> int:
    payload = build_packet(write=True)
    print(
        json.dumps(
            {
                "ok": payload["all_pass"],
                "result": rel(RESULT_PATH),
                "registry": rel(REGISTRY_PATH),
                "gcm_5q_object_id": payload["gcm_5q_object_id"],
                "registry_body_sha256": payload["registry_body_sha256"],
                "cut_count": payload["cut_state_available_evidence"]["cut_count"],
                "hash_pair_count": payload["cut_state_available_evidence"]["hash_pair_count"],
                "sample_cut_pair_count": payload["cut_state_available_evidence"]["sample_cut_pair_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
