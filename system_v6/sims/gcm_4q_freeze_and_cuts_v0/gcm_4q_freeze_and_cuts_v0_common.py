#!/usr/bin/env python3
"""4Q registry freeze plus all bipartition cut-state attachments for GCM."""

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


SIM_ID = "gcm_4q_freeze_and_cuts_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
REGISTRY_PATH = RESULT_DIR / f"{SIM_ID}_registry.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

FOUR_Q_CARVE_DIR = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_4q_v0"
FOUR_Q_CARVE_RESULT = FOUR_Q_CARVE_DIR / "results" / "gcm_constraint_carve_4q_v0_results.json"
FOUR_Q_CARVE_VALIDATOR = FOUR_Q_CARVE_DIR / "results" / "gcm_constraint_carve_4q_v0_validator_results.json"
THREE_Q_FREEZE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_3q_freeze_and_cuts_v0" / "results" / "gcm_3q_freeze_and_cuts_v0_results.json"
)
THREE_Q_CARVE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_constraint_carve_3q_v1" / "results" / "gcm_constraint_carve_3q_v1_results.json"
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
AUDIT_STANDARDS = ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md"
TRIBUNAL_ADOPTION = ROOT / "system_v6" / "receipts" / "nesting_plan_tribunal_adopted_20260612.md"

EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_1Q_REGISTRY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_OBJECT_ID = "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
EXPECTED_3Q_REGISTRY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
EXPECTED_4Q_SURVIVOR_COUNT = 546
EXPECTED_4Q_CLASS_COUNT = 9
EXPECTED_4Q_PRODUCT_LIFT_COUNT = 545
EXPECTED_4Q_ENTANGLED_ANCHOR_COUNT = 1
EXPECTED_3Q_SURVIVOR_COUNT = 545

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_4q_attachment_surface_with_cut_states"
SCHEMA = f"{SIM_ID}_result_v1"
REGISTRY_SCHEMA = f"{SIM_ID}_registry_v1"
TOL = 1.0e-10

CUTS = {
    "1|234": {"left": [0], "right": [1, 2, 3], "dims": [2, 8], "source_name": "q0|q123"},
    "2|134": {"left": [1], "right": [0, 2, 3], "dims": [2, 8], "source_name": "q1|q023"},
    "3|124": {"left": [2], "right": [0, 1, 3], "dims": [2, 8], "source_name": "q2|q013"},
    "4|123": {"left": [3], "right": [0, 1, 2], "dims": [2, 8], "source_name": "q3|q012"},
    "12|34": {"left": [0, 1], "right": [2, 3], "dims": [4, 4], "source_name": "q01|q23"},
    "13|24": {"left": [0, 2], "right": [1, 3], "dims": [4, 4], "source_name": "q02|q13"},
    "14|23": {"left": [0, 3], "right": [1, 2], "dims": [4, 4], "source_name": "q03|q12"},
}

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)

TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 1Q/2Q/3Q/4Q lineage, identity, stale, forged-registry, and lineage-free checks",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "content-addressed IDs, JSON serialization, source locks, and negative-control temp registries",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 16x16 density matrices, 4Q partial traces, partial transpose spectra, entropy, and focus-CKW recomputation",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary check from birth",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "python_stdlib": "load_bearing",
    "numpy": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "gcm_4q_content_derived_registry",
        "cross_rung_3q_4q_lineage_both_directions",
        "all_seven_4q_bipartition_cut_states",
        "entropy_family_attachment_for_all_4q_cuts",
        "four_party_focus_ckw_monogamy_from_stored_states",
        "hardened_substrate_helper_4q_rung",
    ],
    "negative_controls": [
        "lineage-free payloads fail at 1Q/2Q/3Q/4Q",
        "forged registries fail at 1Q/2Q/3Q/4Q",
        "stale lineage hashes fail at 1Q/2Q/3Q/4Q",
        "3Q regression remains green",
    ],
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


def complex_pair(value: complex) -> list[float]:
    return [q(float(np.real(value))), q(float(np.imag(value)))]


def matrix_to_json(matrix: np.ndarray) -> list[list[list[float]]]:
    return [[complex_pair(value) for value in row] for row in matrix.tolist()]


def json_cell_to_complex(cell: Any) -> complex:
    if isinstance(cell, dict):
        return complex(float(cell["re"]), float(cell["im"]))
    return complex(float(cell[0]), float(cell[1]))


def json_to_matrix(value: list[list[Any]]) -> np.ndarray:
    return np.array([[json_cell_to_complex(cell) for cell in row] for row in value], dtype=np.complex128)


def entropy_nats_from_eigs(eigenvalues: np.ndarray) -> float:
    vals = np.real(eigenvalues)
    vals = np.where(np.abs(vals) <= TOL, 0.0, vals)
    vals = np.clip(vals, 0.0, 1.0)
    total = float(np.sum(vals))
    if total > TOL:
        vals = vals / total
    return q(float(-np.sum([value * math.log(value) for value in vals if value > TOL])))


def matrix_rank_from_eigs(eigenvalues: np.ndarray) -> int:
    return int(np.sum(np.real(eigenvalues) > TOL))


def partial_trace_4q(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    dims = [2, 2, 2, 2]
    keep_set = set(keep)
    shaped = rho.reshape(dims + dims)
    current_n = len(dims)
    for qubit in reversed(range(4)):
        if qubit not in keep_set:
            shaped = np.trace(shaped, axis1=qubit, axis2=qubit + current_n)
            current_n -= 1
            dims.pop(qubit)
    out_dim = 2 ** len(keep)
    return shaped.reshape(out_dim, out_dim)


def partial_transpose_right(rho: np.ndarray, left_dim: int, right_dim: int) -> np.ndarray:
    return rho.reshape(left_dim, right_dim, left_dim, right_dim).transpose(0, 3, 2, 1).reshape(
        left_dim * right_dim,
        left_dim * right_dim,
    )


def cut_reduced_pair(rho: np.ndarray, cut_name: str) -> tuple[np.ndarray, np.ndarray]:
    spec = CUTS[cut_name]
    return partial_trace_4q(rho, spec["left"]), partial_trace_4q(rho, spec["right"])


def negativity(rho: np.ndarray, cut_name: str) -> tuple[float, list[float]]:
    left_dim, right_dim = CUTS[cut_name]["dims"]
    eigs = np.linalg.eigvalsh(partial_transpose_right(rho, left_dim, right_dim))
    neg = q(float(np.sum([-float(value) for value in eigs if value < -TOL])))
    return neg, [q(float(value)) for value in eigs]


def schmidt_stratum(rho: np.ndarray, rho_left: np.ndarray, rho_right: np.ndarray) -> dict[str, Any]:
    eig_left = np.linalg.eigvalsh(rho_left)
    eig_right = np.linalg.eigvalsh(rho_right)
    purity = q(float(np.real(np.trace(rho @ rho))))
    pure = abs(purity - 1.0) <= 1.0e-9
    row = {
        "state_purity": purity,
        "pure_state": pure,
        "schmidt_applicable": pure,
        "left_rank": matrix_rank_from_eigs(eig_left),
        "right_rank": matrix_rank_from_eigs(eig_right),
        "left_spectrum": [q(float(value)) for value in np.real(eig_left)],
        "right_spectrum": [q(float(value)) for value in np.real(eig_right)],
    }
    if pure:
        coeffs = sorted([q(math.sqrt(max(0.0, float(value)))) for value in np.real(eig_left) if value > TOL], reverse=True)
        row["schmidt_rank"] = len(coeffs)
        row["schmidt_coefficients"] = coeffs
    else:
        row["schmidt_rank"] = None
        row["schmidt_coefficients"] = []
        row["mixed_state_note"] = "Schmidt decomposition is not asserted for mixed 4Q density rows."
    return row


def cut_row(cut_name: str, rho: np.ndarray) -> dict[str, Any]:
    left_label, right_label = cut_name.split("|")
    rho_left, rho_right = cut_reduced_pair(rho, cut_name)
    s_left = entropy_nats_from_eigs(np.linalg.eigvalsh(rho_left))
    s_right = entropy_nats_from_eigs(np.linalg.eigvalsh(rho_right))
    s_full = entropy_nats_from_eigs(np.linalg.eigvalsh(rho))
    neg, pt_spectrum = negativity(rho, cut_name)
    left_json = matrix_to_json(rho_left)
    right_json = matrix_to_json(rho_right)
    return {
        "cut": cut_name,
        "source_cut_name": CUTS[cut_name]["source_name"],
        "rho_left_id": stable_id(f"rho{left_label}", left_json),
        "rho_right_id": stable_id(f"rho{right_label}", right_json),
        "rho_left_shape": [len(left_json), len(left_json[0])],
        "rho_right_shape": [len(right_json), len(right_json[0])],
        "rho_left": left_json,
        "rho_right": right_json,
        "stored_reduced_matrices": True,
        "spectra": {
            "rho_left": [q(float(value)) for value in np.real(np.linalg.eigvalsh(rho_left))],
            "rho_right": [q(float(value)) for value in np.real(np.linalg.eigvalsh(rho_right))],
            "rho_ABCD": [q(float(value)) for value in np.real(np.linalg.eigvalsh(rho))],
            "partial_transpose_right": pt_spectrum,
        },
        "entropy_values": {
            "S_rho_left": s_left,
            "S_rho_right": s_right,
            "S_rho_ABCD": s_full,
            "conditional_S_left_given_right": q(s_full - s_right),
            "conditional_S_right_given_left": q(s_full - s_left),
            "mutual_I_left_right": q(s_left + s_right - s_full),
            "coherent_I_c_left_to_right": q(s_right - s_full),
            "coherent_I_c_right_to_left": q(s_left - s_full),
            "negativity": neg,
            "log_negativity": q(math.log(1.0 + 2.0 * neg)),
        },
        "schmidt_stratum": schmidt_stratum(rho, rho_left, rho_right),
    }


def source_states(carve: dict[str, Any]) -> dict[str, np.ndarray]:
    states = carve["state_artifacts"]["states_by_content_id"]
    return {content_id: json_to_matrix(row["rho_ABCD"]) for content_id, row in states.items()}


def build_4q_registry(carve: dict[str, Any], three_q_registry: dict[str, Any]) -> dict[str, Any]:
    pinned = {
        "base_gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "four_q_carve_result_sha256": sha256_file(FOUR_Q_CARVE_RESULT),
        "survivor_count": carve["survivor_count"],
        "quotient_class_count": carve["quotient"]["class_count"],
        "survivor_family_counts": carve["survivor_family_counts"],
        "cut_lattice": list(CUTS),
    }
    gcm_4q_object_id = stable_id("gcm4qobj", pinned, length=32)
    survivor_rows = []
    for row in carve["survivors"]:
        raw_sid = int(row["survivor_id"])
        payload = {
            "gcm_4q_object_id": gcm_4q_object_id,
            "raw_4q_survivor_id": raw_sid,
            "candidate_id": row["candidate_id"],
            "candidate_label": row["candidate_label"],
            "family": row["family"],
            "rho_ABCD_content_id": row["rho_ABCD_content_id"],
            "source_gcm_3q_survivor_id": row.get("source_gcm_3q_survivor_id"),
            "four_partite_entangled_anchor": bool(row.get("four_partite_entangled_anchor")),
        }
        survivor_rows.append(
            {
                "gcm_4q_survivor_id": stable_id("gcm4qsurv", payload),
                "raw_4q_survivor_id": raw_sid,
                "candidate_id": row["candidate_id"],
                "candidate_label": row["candidate_label"],
                "family": row["family"],
                "rho_ABCD_content_id": row["rho_ABCD_content_id"],
                "source_gcm_3q_survivor_id": row.get("source_gcm_3q_survivor_id"),
                "source_3q_survivor_id": row.get("raw_3q_survivor_id"),
                "four_partite_entangled_anchor": bool(row.get("four_partite_entangled_anchor")),
                "content_sha256": stable_sha256(payload),
            }
        )
    gcm_by_raw = {row["raw_4q_survivor_id"]: row["gcm_4q_survivor_id"] for row in survivor_rows}

    class_rows = []
    for qrow in carve["quotient"]["classes"]:
        member_ids = [gcm_by_raw[int(raw_sid)] for raw_sid in qrow["member_survivor_ids"]]
        payload = {
            "gcm_4q_object_id": gcm_4q_object_id,
            "raw_class_id": qrow["class_id"],
            "probe_signature": qrow["probe_signature"],
            "member_gcm_4q_survivor_ids": member_ids,
        }
        class_rows.append(
            {
                "gcm_4q_quotient_class_id": stable_id("gcm4qqcls", payload),
                "raw_class_id": qrow["class_id"],
                "probe_signature": qrow["probe_signature"],
                "member_gcm_4q_survivor_ids": member_ids,
                "member_raw_4q_survivor_ids": qrow["member_survivor_ids"],
                "member_count": qrow["member_count"],
                "family_counts": qrow["family_counts"],
                "four_partite_entangled_anchor_count": qrow["four_partite_entangled_anchor_count"],
                "content_sha256": stable_sha256(payload),
            }
        )

    region_rows = []
    for qrow, class_row in zip(carve["quotient"]["classes"], class_rows, strict=True):
        payload = {
            "gcm_4q_object_id": gcm_4q_object_id,
            "raw_region_id": qrow["class_id"],
            "member_gcm_4q_quotient_class_ids": [class_row["gcm_4q_quotient_class_id"]],
            "cut_lattice": list(CUTS),
            "region_scope": "class_local_4q_cut_state_attachment_region",
        }
        region_rows.append(
            {
                "gcm_4q_candidate_region_id": stable_id("gcm4qcreg", payload),
                "raw_region_id": qrow["class_id"],
                "region_scope": "class_local_4q_cut_state_attachment_region",
                "member_gcm_4q_quotient_class_ids": [class_row["gcm_4q_quotient_class_id"]],
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
        "gcm_4q_object_id": gcm_4q_object_id,
        "gcm_4q_object_id_rule": "sha256 over 1Q/2Q/3Q object identities, committed 4Q carve result hash, 4Q counts, survivor family counts, and the seven-cut lattice",
        "pinned_spec_sha256": stable_sha256(pinned),
        "frozen_registry": three_q_registry["frozen_registry"],
        "frozen_2q_registry": three_q_registry["frozen_2q_registry"],
        "frozen_3q_registry": three_q_registry["frozen_3q_registry"],
        "frozen_4q_registry": {
            "survivors": survivor_rows,
            "quotient_classes": class_rows,
            "candidate_regions": region_rows,
        },
        "counts": {
            "survivor_count": len(survivor_rows),
            "quotient_class_count": len(class_rows),
            "candidate_region_count": len(region_rows),
            "product_lift_survivor_count": sum(1 for row in survivor_rows if row["family"] == "3q_survivor_product_lift"),
            "four_partite_entangled_survivor_count": sum(1 for row in survivor_rows if row["four_partite_entangled_anchor"]),
        },
        "source_locks": {
            "four_q_carve_result": source_lock(FOUR_Q_CARVE_RESULT, "committed 546-survivor 4Q carve source"),
            "four_q_carve_validator": source_lock(FOUR_Q_CARVE_VALIDATOR, "4Q carve validator receipt"),
            "three_q_carve_result": source_lock(THREE_Q_CARVE_RESULT, "3Q carve state source for Tr_D regression"),
            "three_q_freeze_result": source_lock(THREE_Q_FREEZE_RESULT, "3Q freeze result source"),
            "three_q_freeze_registry": source_lock(THREE_Q_FREEZE_REGISTRY, "3Q freeze registry source"),
            "two_q_freeze_registry": source_lock(TWO_Q_FREEZE_REGISTRY, "2Q freeze registry source"),
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "1Q freeze registry source"),
            "audit_standards": source_lock(AUDIT_STANDARDS, "G.2a standards"),
            "tribunal_adoption": source_lock(TRIBUNAL_ADOPTION, "4Q cut-state caveat authority"),
        },
    }
    body = dict(registry)
    registry["registry_body_sha256"] = stable_sha256(body)
    return registry


def registry_maps(registry: dict[str, Any]) -> dict[str, dict[Any, str]]:
    return {
        "gcm4q_by_raw": {
            row["raw_4q_survivor_id"]: row["gcm_4q_survivor_id"]
            for row in registry["frozen_4q_registry"]["survivors"]
        },
        "gcm4q_class_by_raw": {
            row["raw_class_id"]: row["gcm_4q_quotient_class_id"]
            for row in registry["frozen_4q_registry"]["quotient_classes"]
        },
        "gcm4q_region_by_raw_class": {
            row["member_raw_class_ids"][0]: row["gcm_4q_candidate_region_id"]
            for row in registry["frozen_4q_registry"]["candidate_regions"]
        },
    }


def raw_class_for_survivor(carve: dict[str, Any]) -> dict[int, str]:
    out = {}
    for qrow in carve["quotient"]["classes"]:
        for raw_sid in qrow["member_survivor_ids"]:
            out[int(raw_sid)] = qrow["class_id"]
    return out


def three_q_rows_by_gcm_id(three_q_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["gcm_3q_survivor_id"]: row
        for row in three_q_payload["cut_tables"]["survivor_cut_rows"]
    }


def cross_rung_lineage(
    carve: dict[str, Any],
    three_q_payload: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[dict[str, Any], dict[int, dict[str, float | bool]]]:
    maps = registry_maps(registry)
    class_by_raw = raw_class_for_survivor(carve)
    three_q_by_id = three_q_rows_by_gcm_id(three_q_payload)
    three_q_carve = load_json(THREE_Q_CARVE_RESULT)
    three_q_states = three_q_carve["state_artifacts"]["states_by_content_id"]
    states = source_states(carve)
    object_maps = []
    three_to_four = []
    projection_deltas: dict[int, dict[str, float | bool]] = {}
    for row in carve["survivors"]:
        raw_sid = int(row["survivor_id"])
        raw_class = class_by_raw[raw_sid]
        map_row = {
            "gcm_4q_survivor_id": maps["gcm4q_by_raw"][raw_sid],
            "raw_4q_survivor_id": raw_sid,
            "candidate_id": row["candidate_id"],
            "candidate_label": row["candidate_label"],
            "family": row["family"],
            "gcm_4q_quotient_class_id": maps["gcm4q_class_by_raw"][raw_class],
            "gcm_4q_candidate_region_id": maps["gcm4q_region_by_raw_class"][raw_class],
            "rho_ABCD_content_id": row["rho_ABCD_content_id"],
            "four_partite_entangled_anchor": bool(row.get("four_partite_entangled_anchor")),
        }
        if row["family"] == "3q_survivor_product_lift":
            gcm_3q_id = row["source_gcm_3q_survivor_id"]
            rho_abcd = states[row["rho_ABCD_content_id"]]
            rho_abc = partial_trace_4q(rho_abcd, [0, 1, 2])
            source_row = three_q_by_id[gcm_3q_id]
            source_3q_full = json_to_matrix(three_q_states[source_row["rho_ABC_content_id"]]["rho_ABC"])
            full_delta = q(float(np.max(np.abs(rho_abc - source_3q_full))))
            projection_deltas[raw_sid] = {
                "TrD_vs_3q_rho_delta": full_delta,
                "TrD_reproduces_3q_state": full_delta == 0.0,
            }
            map_row.update(
                {
                    "gcm_3q_survivor_id": gcm_3q_id,
                    "raw_3q_survivor_id": row["raw_3q_survivor_id"],
                    "projection": "Tr_D(rho_ABCD) -> source 3Q rho_ABC",
                    "TrD_vs_3q_rho_delta": full_delta,
                    "TrD_reproduces_3q_state": full_delta == 0.0,
                }
            )
            three_to_four.append(
                {
                    "gcm_3q_survivor_id": gcm_3q_id,
                    "raw_3q_survivor_id": row["raw_3q_survivor_id"],
                    "gcm_4q_survivor_id": maps["gcm4q_by_raw"][raw_sid],
                    "raw_4q_survivor_id": raw_sid,
                    "TrD_reproduces_3q_state": full_delta == 0.0,
                    "TrD_vs_3q_rho_delta": full_delta,
                }
            )
        else:
            map_row.update(
                {
                    "gcm_3q_survivor_id": None,
                    "raw_3q_survivor_id": None,
                    "projection": "4Q-only entangled anchor has no 3Q registry source row",
                    "projection_delta": None,
                }
            )
        object_maps.append(map_row)

    counts = Counter(row["gcm_3q_survivor_id"] for row in three_to_four)
    lineage = {
        "row_id": "cross_rung_3q_4q_product_embedding_and_projection",
        "base_gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "gcm_4q_object_id": registry["gcm_4q_object_id"],
        "gcm_4q_registry_body_sha256": registry["registry_body_sha256"],
        "gcm_3q_survivor_ids": [row["gcm_3q_survivor_id"] for row in three_to_four],
        "gcm_4q_survivor_ids": [row["gcm_4q_survivor_id"] for row in object_maps],
        "gcm_4q_quotient_class_ids": [
            row["gcm_4q_quotient_class_id"] for row in registry["frozen_4q_registry"]["quotient_classes"]
        ],
        "gcm_4q_candidate_region_ids": [
            row["gcm_4q_candidate_region_id"] for row in registry["frozen_4q_registry"]["candidate_regions"]
        ],
        "object_maps": object_maps,
        "three_q_to_4q_product_embedding": {
            "input_3q_survivor_count": EXPECTED_3Q_SURVIVOR_COUNT,
            "lifted_4q_survivor_count": len(three_to_four),
            "all_3q_survivors_have_one_4q_lift": len(counts) == EXPECTED_3Q_SURVIVOR_COUNT and set(counts.values()) == {1},
            "embedding_rows": three_to_four,
        },
        "four_q_to_3q_projection": {
            "trace": "Tr_D(rho_ABCD)",
            "product_lift_checked_count": len(projection_deltas),
            "product_lift_TrD_reproduces_3q_states": all(
                row["TrD_vs_3q_rho_delta"] == 0.0 for row in projection_deltas.values()
            ),
            "max_abs_delta_TrD_vs_3q_rho": q(
                max((float(row["TrD_vs_3q_rho_delta"]) for row in projection_deltas.values()), default=0.0)
            ),
            "four_partite_anchor_projection_status": "not_a_3q_registry_embedding",
        },
    }
    return lineage, projection_deltas


def survivor_cut_rows(carve: dict[str, Any], registry: dict[str, Any]) -> list[dict[str, Any]]:
    maps = registry_maps(registry)
    class_by_raw = raw_class_for_survivor(carve)
    states = source_states(carve)
    rows = []
    for row in carve["survivors"]:
        raw_sid = int(row["survivor_id"])
        raw_class = class_by_raw[raw_sid]
        rho = states[row["rho_ABCD_content_id"]]
        cuts = {name: cut_row(name, rho) for name in CUTS}
        rows.append(
            {
                "gcm_4q_survivor_id": maps["gcm4q_by_raw"][raw_sid],
                "raw_4q_survivor_id": raw_sid,
                "candidate_id": row["candidate_id"],
                "candidate_label": row["candidate_label"],
                "family": row["family"],
                "rho_ABCD_content_id": row["rho_ABCD_content_id"],
                "rho_ABCD_id": stable_id("rhoABCD4q", row["rho_ABCD_content_id"]),
                "gcm_4q_quotient_class_id": maps["gcm4q_class_by_raw"][raw_class],
                "gcm_4q_candidate_region_id": maps["gcm4q_region_by_raw_class"][raw_class],
                "source_gcm_3q_survivor_id": row.get("source_gcm_3q_survivor_id"),
                "raw_3q_survivor_id": row.get("raw_3q_survivor_id"),
                "four_partite_entangled_anchor": bool(row.get("four_partite_entangled_anchor")),
                "cut_state_available": True,
                "cuts": cuts,
            }
        )
    return rows


def stats(values: list[float]) -> dict[str, Any]:
    unique = sorted({q(value) for value in values})
    return {
        "min": q(min(values)),
        "max": q(max(values)),
        "mean": q(sum(values) / len(values)),
        "unique_count": len(unique),
        "unique_values": unique[:32],
        "unique_values_truncated": len(unique) > 32,
    }


def class_cut_rows(registry: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_class[row["gcm_4q_quotient_class_id"]].append(row)
    raw_by_qid = {
        row["gcm_4q_quotient_class_id"]: row
        for row in registry["frozen_4q_registry"]["quotient_classes"]
    }
    out = []
    for qid in sorted(by_class, key=lambda item: raw_by_qid[item]["raw_class_id"]):
        members = by_class[qid]
        cut_stats = {}
        for cut_name in CUTS:
            cut_stats[cut_name] = {}
            for metric in members[0]["cuts"][cut_name]["entropy_values"]:
                cut_stats[cut_name][metric] = stats(
                    [float(row["cuts"][cut_name]["entropy_values"][metric]) for row in members]
                )
        out.append(
            {
                "gcm_4q_quotient_class_id": qid,
                "raw_class_id": raw_by_qid[qid]["raw_class_id"],
                "member_count": len(members),
                "member_gcm_4q_survivor_ids": [row["gcm_4q_survivor_id"] for row in members],
                "four_partite_entangled_anchor_count": sum(1 for row in members if row["four_partite_entangled_anchor"]),
                "cut_metric_stats": cut_stats,
            }
        )
    return out


def concurrence_2q(rho_2q: np.ndarray) -> float:
    yy = np.kron(PAULI_Y, PAULI_Y)
    product = rho_2q @ yy @ np.conjugate(rho_2q) @ yy
    eigvals = np.linalg.eigvals(product)
    roots = sorted((math.sqrt(max(0.0, float(np.real(value)))) for value in eigvals), reverse=True)
    while len(roots) < 4:
        roots.append(0.0)
    return q(max(0.0, roots[0] - roots[1] - roots[2] - roots[3]))


def one_tangle(rho_single: np.ndarray) -> float:
    return q(max(0.0, float(np.real(4.0 * np.linalg.det(rho_single)))))


def focus_ckw_rows(rho: np.ndarray) -> dict[str, Any]:
    pair_cache: dict[tuple[int, int], float] = {}
    for left in range(4):
        for right in range(left + 1, 4):
            pair_cache[(left, right)] = q(concurrence_2q(partial_trace_4q(rho, [left, right])) ** 2)
    rows = {}
    for focus in range(4):
        pairwise = {}
        for other in range(4):
            if other == focus:
                continue
            key = tuple(sorted((focus, other)))
            pairwise[f"q{focus + 1}q{other + 1}"] = pair_cache[key]
        pair_sum = q(sum(pairwise.values()))
        one = one_tangle(partial_trace_4q(rho, [focus]))
        margin = q(one - pair_sum)
        rows[f"q{focus + 1}"] = {
            "one_tangle": one,
            "pairwise_tangles": pairwise,
            "pairwise_sum": pair_sum,
            "ckw_margin": margin,
            "satisfies_focus_ckw": margin >= -1.0e-10,
        }
    return rows


def monogamy_table(carve: dict[str, Any], cut_rows: list[dict[str, Any]]) -> dict[str, Any]:
    states = carve["state_artifacts"]["states_by_content_id"]
    by_raw = {row["raw_4q_survivor_id"]: row for row in cut_rows}
    rows = []
    for survivor in carve["survivors"]:
        state = states[survivor["rho_ABCD_content_id"]]
        if "state_vector" not in state:
            continue
        raw_sid = int(survivor["survivor_id"])
        rho = json_to_matrix(state["rho_ABCD"])
        rows.append(
            {
                "state_id": survivor["candidate_label"],
                "candidate_id": survivor["candidate_id"],
                "raw_4q_survivor_id": raw_sid,
                "gcm_4q_survivor_id": by_raw[raw_sid]["gcm_4q_survivor_id"],
                "rho_ABCD_content_id": survivor["rho_ABCD_content_id"],
                "computed_from_stored_rho_ABCD": True,
                "focus_qubits": focus_ckw_rows(rho),
            }
        )
    return {
        "row_id": "four_party_focus_ckw_monogamy_4q_attachment_surface",
        "generalization": "Osborne-Verstraete N-qubit CKW focus-qubit inequality",
        "narrow_statement": "For stored pure survivor states, C(qi|rest)^2 >= sum_j C(qi,qj)^2 is checked per focus qubit.",
        "computed_from_stored_rho_ABCD": True,
        "residual_4_tangle_claimed": False,
        "pure_survivor_count_checked": len(rows),
        "all_focus_qubits_satisfy_ckw": all(
            focus["satisfies_focus_ckw"] for row in rows for focus in row["focus_qubits"].values()
        ),
        "rows": rows,
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


def lineage_for_helper(registry: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    one_q_survivors = registry["frozen_registry"]["survivors"]
    one_q_classes = registry["frozen_registry"]["quotient_classes"]
    one_q_regions = registry["frozen_registry"]["candidate_regions"]
    two_q_surv = first_nested_id(registry, "frozen_2q_registry", "gcm_2q_survivor_id")
    two_q_cls = first_nested_id(registry, "frozen_2q_registry", "gcm_2q_quotient_class_id")
    two_q_reg = first_nested_id(registry, "frozen_2q_registry", "gcm_2q_candidate_region_id")
    three_q_cls = first_nested_id(registry, "frozen_3q_registry", "gcm_3q_quotient_class_id")
    three_q_reg = first_nested_id(registry, "frozen_3q_registry", "gcm_3q_candidate_region_id")
    return {
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_3q_object_id": EXPECTED_3Q_OBJECT_ID,
        "gcm_4q_object_id": registry["gcm_4q_object_id"],
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "one_q_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_registry_body_sha256": EXPECTED_3Q_REGISTRY_SHA256,
        "gcm_4q_registry_body_sha256": registry["registry_body_sha256"],
        "survivor_ids": [one_q_survivors[0]["survivor_id"]],
        "quotient_class_ids": [one_q_classes[0]["quotient_class_id"]],
        "candidate_region_ids": [one_q_regions[0]["candidate_region_id"]],
        "gcm_2q_survivor_ids": [two_q_surv],
        "gcm_2q_quotient_class_ids": [two_q_cls],
        "gcm_2q_candidate_region_ids": [two_q_reg],
        "gcm_3q_survivor_ids": lineage["gcm_3q_survivor_ids"],
        "gcm_3q_quotient_class_ids": [three_q_cls],
        "gcm_3q_candidate_region_ids": [three_q_reg],
        "gcm_4q_survivor_ids": lineage["gcm_4q_survivor_ids"],
        "gcm_4q_quotient_class_ids": lineage["gcm_4q_quotient_class_ids"],
        "gcm_4q_candidate_region_ids": lineage["gcm_4q_candidate_region_ids"],
        "object_maps": lineage["object_maps"],
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


def stale_lineage_variant(payload: dict[str, Any], rung: str) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    lineage = variant.setdefault("gcm_lineage", {})
    stale = "0" * 64
    if rung == "1Q":
        lineage["registry_body_sha256"] = stale
        lineage["base_registry_body_sha256"] = stale
        lineage["one_q_registry_body_sha256"] = stale
    elif rung == "2Q":
        lineage["gcm_2q_registry_body_sha256"] = stale
    elif rung == "3Q":
        lineage["gcm_3q_registry_body_sha256"] = stale
    elif rung == "4Q":
        lineage["gcm_4q_registry_body_sha256"] = stale
    return variant


def forged_registry(registry: dict[str, Any]) -> dict[str, Any]:
    clone = copy.deepcopy(registry)
    clone.setdefault("counts", {})["survivor_count"] = int(clone.get("counts", {}).get("survivor_count", 0)) + 1
    return clone


def substrate_control_matrix(payload: dict[str, Any], registries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    paths = {
        "1Q": ONE_Q_FREEZE_REGISTRY,
        "2Q": TWO_Q_FREEZE_REGISTRY,
        "3Q": THREE_Q_FREEZE_REGISTRY,
        "4Q": REGISTRY_PATH,
    }
    positive = {rung: check_with_registry(payload, registries[rung], paths[rung]) for rung in ("1Q", "2Q", "3Q", "4Q")}
    negatives = {}
    for rung in ("1Q", "2Q", "3Q", "4Q"):
        registry = registries[rung]
        negatives[rung] = {
            "lineage_free": check_with_registry(lineage_free_variant(payload), registry, paths[rung]),
            "forged_registry": check_with_registry(payload, forged_registry(registry), paths[rung]),
            "stale_lineage": check_with_registry(stale_lineage_variant(payload, rung), registry, paths[rung]),
        }
    return {"substrate_positive": positive, "substrate_negatives": negatives}


def all_pass_substrate_controls(controls: dict[str, Any]) -> bool:
    positives = controls["substrate_positive"]
    negatives = controls["substrate_negatives"]
    return all(row.get("ok") is True for row in positives.values()) and all(
        item.get("ok") is False and bool(item.get("error_codes")) for rung in negatives.values() for item in rung.values()
    )


def build_packet(write: bool = True) -> dict[str, Any]:
    carve = load_json(FOUR_Q_CARVE_RESULT)
    three_q_payload = load_json(THREE_Q_FREEZE_RESULT)
    three_q_registry = load_json(THREE_Q_FREEZE_REGISTRY)
    two_q_registry = load_json(TWO_Q_FREEZE_REGISTRY)
    one_q_registry = load_json(ONE_Q_FREEZE_REGISTRY)
    registry = build_4q_registry(carve, three_q_registry)
    if write:
        write_json(REGISTRY_PATH, registry)

    lineage, projection_deltas = cross_rung_lineage(carve, three_q_payload, registry)
    rows = survivor_cut_rows(carve, registry)
    classes = class_cut_rows(registry, rows)
    anchor_profiles = [row for row in rows if row["four_partite_entangled_anchor"]]
    helper_payload = {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "gcm_lineage": lineage_for_helper(registry, lineage),
    }
    substrate_controls = substrate_control_matrix(
        helper_payload,
        {"1Q": one_q_registry, "2Q": two_q_registry, "3Q": three_q_registry, "4Q": registry},
    )
    monogamy = monogamy_table(carve, rows)
    no_audit = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    three_q_regression = {
        "trace": "Tr_D(rho_ABCD)",
        "product_lift_checked_count": len(projection_deltas),
        "partial_traces_reproduce": all(row["TrD_vs_3q_rho_delta"] == 0.0 for row in projection_deltas.values()),
        "max_abs_delta_TrD_vs_3q_rho": q(
            max((float(row["TrD_vs_3q_rho_delta"]) for row in projection_deltas.values()), default=0.0)
        ),
        "partial_trace_scope": "3Q states from committed gcm_3q_freeze_and_cuts_v0 cut-state rows; 4Q-only anchor has no 3Q registry source",
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "declared_surface": "freeze/registry + cut layers | carve-attached | 4Q",
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "cut_state_available": True,
        "cut_state_available_evidence": {
            "stored_reduced_matrices": True,
            "survivor_count": len(rows),
            "cut_count": len(CUTS),
            "stored_matrix_pair_count": len(rows) * len(CUTS),
            "matrix_fields": ["rho_left", "rho_right"],
            "content_hashed_fields": ["rho_left_id", "rho_right_id"],
        },
        "unblocks_cut_state_citation_for": [
            "<=4Q tower",
            "4Q geometry-delta",
            "4Q flux",
        ],
        "coordinates": {
            "layers": "4Q freeze/registry plus all bipartition cut-state attachments",
            "nesting": "1|234, 2|134, 3|124, 4|123, 12|34, 13|24, 14|23 cut lattice",
            "qubit_depth": "4Q",
        },
        "cut_lattice": {
            "bipartitions": list(CUTS),
            "source_bipartition_names": {name: spec["source_name"] for name, spec in CUTS.items()},
            "tensor_order": "computational basis |1234> with index = 8*q1 + 4*q2 + 2*q3 + q4",
            "stored_reductions": ["rho_left", "rho_right"],
        },
        "gcm_4q_object_id": registry["gcm_4q_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "registry_path": rel(REGISTRY_PATH),
        "gcm_lineage": helper_payload["gcm_lineage"],
        "counts": {
            "four_q_survivor_count": len(rows),
            "four_q_class_count": len(classes),
            "four_q_candidate_region_count": len(registry["frozen_4q_registry"]["candidate_regions"]),
            "product_lift_survivor_count": registry["counts"]["product_lift_survivor_count"],
            "four_partite_entangled_survivor_count": registry["counts"]["four_partite_entangled_survivor_count"],
        },
        "frozen_4q_registry": registry["frozen_4q_registry"],
        "cross_rung_lineage": lineage,
        "cut_tables": {
            "survivor_cut_rows": rows,
            "class_cut_rows": classes,
        },
        "four_partite_anchor_profile": anchor_profiles[0] if anchor_profiles else None,
        "monogamy_table": monogamy,
        "controls": {
            "three_q_regression": three_q_regression,
            **substrate_controls,
            "cut_state_caveat_resolution": {
                "cut_state_available": True,
                "resolved_caveat_from": "gcm_constraint_carve_4q_v0 stored entropy/MI rows without per-cut reduced matrices",
                "resolution": "this packet stores rho_left and rho_right for every survivor and every unordered 4Q bipartition",
            },
        },
        "source_locks": {
            "four_q_carve_result": source_lock(FOUR_Q_CARVE_RESULT, "state-artifacted 546 survivor 4Q carve v0"),
            "four_q_carve_validator": source_lock(FOUR_Q_CARVE_VALIDATOR, "4Q carve v0 validator"),
            "three_q_carve_result": source_lock(THREE_Q_CARVE_RESULT, "3Q state-artifact source for Tr_D regression"),
            "three_q_freeze_result": source_lock(THREE_Q_FREEZE_RESULT, "3Q freeze and cuts packet"),
            "three_q_freeze_registry": source_lock(THREE_Q_FREEZE_REGISTRY, "3Q registry lineage source"),
            "two_q_freeze_registry": source_lock(TWO_Q_FREEZE_REGISTRY, "2Q registry lineage source"),
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "1Q object registry lineage source"),
            "tribunal_adoption": source_lock(TRIBUNAL_ADOPTION, "4Q caveat-resolution authority"),
            "audit_standards": source_lock(AUDIT_STANDARDS, "G.2a standards"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "G_2a_idempotency_from_birth": no_audit,
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": no_audit,
            "no_builder_audit_verdict_envelope_gate": no_audit,
        },
        "allowed_claims": [
            "4Q registry and cut-state attachment surface",
            "all seven stored 4Q bipartition reductions and entropy families",
            "4-party focus-qubit monogamy table from stored rho_ABCD where pure-state computation is applicable",
            "4Q helper lineage hardening checks",
            "<=4Q tower and 4Q geometry-delta may cite 4Q cut states from this attachment surface",
        ],
        "blocked_consumers": [
            "formal_admission",
            "canonical_manifold_claim",
            "axis_or_bridge_claim",
            "physics_claim",
            "SLOCC_GHZ_W_cluster_separator_claim",
            "canonical_G2_or_Spin7_claim",
        ],
    }
    payload["all_pass"] = (
        len(rows) == EXPECTED_4Q_SURVIVOR_COUNT
        and len(classes) == EXPECTED_4Q_CLASS_COUNT
        and registry["counts"]["product_lift_survivor_count"] == EXPECTED_4Q_PRODUCT_LIFT_COUNT
        and registry["counts"]["four_partite_entangled_survivor_count"] == EXPECTED_4Q_ENTANGLED_ANCHOR_COUNT
        and len(anchor_profiles) == 1
        and three_q_regression["partial_traces_reproduce"]
        and monogamy["computed_from_stored_rho_ABCD"]
        and monogamy["all_focus_qubits_satisfy_ckw"]
        and payload["cut_state_available_evidence"]["stored_matrix_pair_count"] == EXPECTED_4Q_SURVIVOR_COUNT * 7
        and all_pass_substrate_controls(substrate_controls)
        and no_audit
    )
    payload["result_sha256"] = stable_sha256({key: value for key, value in payload.items() if key != "generated_at"})
    if write:
        write_json(RESULT_PATH, payload)
        write_json(LINEAGE_FREE_NEGATIVE_PATH, lineage_free_variant(helper_payload))
    return payload


def main() -> int:
    payload = build_packet(write=True)
    print(
        json.dumps(
            {
                "ok": payload["all_pass"],
                "result": rel(RESULT_PATH),
                "registry": rel(REGISTRY_PATH),
                "registry_body_sha256": payload["registry_body_sha256"],
                "gcm_4q_object_id": payload["gcm_4q_object_id"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
