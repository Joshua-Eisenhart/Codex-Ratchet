#!/usr/bin/env python3
"""3Q registry freeze plus all bipartition cut attachments for the GCM object."""

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


SIM_ID = "gcm_3q_freeze_and_cuts_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
REGISTRY_PATH = RESULT_DIR / f"{SIM_ID}_registry.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

THREE_Q_CARVE_DIR = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_3q_v1"
THREE_Q_CARVE_RESULT = THREE_Q_CARVE_DIR / "results" / "gcm_constraint_carve_3q_v1_results.json"
THREE_Q_CARVE_VALIDATOR = THREE_Q_CARVE_DIR / "results" / "gcm_constraint_carve_3q_v1_validator_results.json"
TWO_Q_FREEZE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_results.json"
)
TWO_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_registry.json"
)
ONE_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
AUDIT_STANDARDS = ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md"
LAYER_STACK_REFERENCE = ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md"

EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_1Q_REGISTRY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_3Q_SURVIVOR_COUNT = 545
EXPECTED_3Q_CLASS_COUNT = 9
EXPECTED_3Q_PRODUCT_LIFT_COUNT = 544
EXPECTED_3Q_TRIPARTITE_ANCHOR_COUNT = 1
EXPECTED_2Q_SURVIVOR_COUNT = 544

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_3q_attachment_surface_runtime_flux_blocked"
SCHEMA = f"{SIM_ID}_result_v1"
REGISTRY_SCHEMA = f"{SIM_ID}_registry_v1"
TOL = 1.0e-10
CUTS = {
    "A|BC": {"left": [0], "right": [1, 2], "dims": [2, 4]},
    "B|AC": {"left": [1], "right": [0, 2], "dims": [2, 4]},
    "C|AB": {"left": [2], "right": [0, 1], "dims": [2, 4]},
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
        "reason": "load-bearing 1Q/2Q/3Q lineage, identity, stale, and forged-registry checks",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "content-addressed IDs, JSON serialization, source locks, and negative-control temp registries",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 8x8 density matrices, partial traces, partial transpose spectra, entropy, and CKW recomputation",
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
        "gcm_3q_content_derived_registry",
        "cross_rung_2q_3q_lineage_both_directions",
        "all_three_3q_bipartition_cuts",
        "entropy_family_attachment_for_A_B_C_cuts",
        "schmidt_strata_for_tripartite_anchor",
        "ckw_monogamy_from_stored_states",
        "hardened_substrate_helper_3q_rung",
    ],
    "negative_controls": [
        "lineage-free payloads fail at 1Q/2Q/3Q",
        "forged registries fail at 1Q/2Q/3Q",
        "stale lineage hashes fail at 1Q/2Q/3Q",
        "runtime flux remains blocked",
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


def q(value: float, digits: int = 15) -> float:
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


def partial_trace_3q(rho: np.ndarray, keep: list[int]) -> np.ndarray:
    keep_set = set(keep)
    dims = [2, 2, 2]
    shaped = rho.reshape(dims + dims)
    for traced in sorted([idx for idx in range(3) if idx not in keep_set], reverse=True):
        current_n = len(dims)
        shaped = np.trace(shaped, axis1=traced, axis2=traced + current_n)
        dims.pop(traced)
    out_dim = int(np.prod(dims))
    return shaped.reshape(out_dim, out_dim)


def partial_transpose_right(rho: np.ndarray, left_dim: int, right_dim: int) -> np.ndarray:
    return rho.reshape(left_dim, right_dim, left_dim, right_dim).transpose(0, 3, 2, 1).reshape(
        left_dim * right_dim,
        left_dim * right_dim,
    )


def cut_reduced_pair(rho: np.ndarray, cut_name: str) -> tuple[np.ndarray, np.ndarray]:
    spec = CUTS[cut_name]
    return partial_trace_3q(rho, spec["left"]), partial_trace_3q(rho, spec["right"])


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
    left_rank = matrix_rank_from_eigs(eig_left)
    right_rank = matrix_rank_from_eigs(eig_right)
    row = {
        "state_purity": purity,
        "pure_state": pure,
        "schmidt_applicable": pure,
        "left_rank": left_rank,
        "right_rank": right_rank,
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
        row["mixed_state_note"] = "Schmidt decomposition is not asserted for mixed product-lift density rows."
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
        "rho_left_id": stable_id(f"rho{left_label}", left_json),
        "rho_right_id": stable_id(f"rho{right_label}", right_json),
        "rho_left": left_json,
        "rho_right": right_json,
        "spectra": {
            "rho_left": [q(float(value)) for value in np.real(np.linalg.eigvalsh(rho_left))],
            "rho_right": [q(float(value)) for value in np.real(np.linalg.eigvalsh(rho_right))],
            "rho_ABC": [q(float(value)) for value in np.real(np.linalg.eigvalsh(rho))],
            "partial_transpose_right": pt_spectrum,
        },
        "entropy_values": {
            "S_rho_left": s_left,
            "S_rho_right": s_right,
            "S_rho_ABC": s_full,
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
    return {content_id: json_to_matrix(row["rho_ABC"]) for content_id, row in states.items()}


def build_3q_registry(carve: dict[str, Any], two_q_registry: dict[str, Any]) -> dict[str, Any]:
    pinned = {
        "base_gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "three_q_carve_result_sha256": sha256_file(THREE_Q_CARVE_RESULT),
        "survivor_count": carve["survivor_count"],
        "quotient_class_count": carve["quotient"]["class_count"],
        "survivor_family_counts": carve["survivor_family_counts"],
        "cut_lattice": list(CUTS),
    }
    gcm_3q_object_id = stable_id("gcm3qobj", pinned, length=32)
    survivor_rows = []
    for row in carve["survivors"]:
        raw_sid = int(row["survivor_id"])
        payload = {
            "gcm_3q_object_id": gcm_3q_object_id,
            "raw_3q_survivor_id": raw_sid,
            "candidate_id": row["candidate_id"],
            "candidate_label": row["candidate_label"],
            "family": row["family"],
            "rho_ABC_content_id": row["rho_ABC_content_id"],
            "source_gcm_2q_survivor_id": row.get("source_gcm_2q_survivor_id"),
            "tripartite_entangled_anchor": bool(row.get("tripartite_entangled_anchor")),
        }
        survivor_rows.append(
            {
                "gcm_3q_survivor_id": stable_id("gcm3qsurv", payload),
                "raw_3q_survivor_id": raw_sid,
                "candidate_id": row["candidate_id"],
                "candidate_label": row["candidate_label"],
                "family": row["family"],
                "rho_ABC_content_id": row["rho_ABC_content_id"],
                "source_gcm_2q_survivor_id": row.get("source_gcm_2q_survivor_id"),
                "source_2q_survivor_id": row.get("source_2q_survivor_id"),
                "tripartite_entangled_anchor": bool(row.get("tripartite_entangled_anchor")),
                "content_sha256": stable_sha256(payload),
            }
        )
    gcm_by_raw = {row["raw_3q_survivor_id"]: row["gcm_3q_survivor_id"] for row in survivor_rows}

    class_rows = []
    for qrow in carve["quotient"]["classes"]:
        member_ids = [gcm_by_raw[int(raw_sid)] for raw_sid in qrow["member_survivor_ids"]]
        payload = {
            "gcm_3q_object_id": gcm_3q_object_id,
            "raw_class_id": qrow["class_id"],
            "probe_signature": qrow["probe_signature"],
            "member_gcm_3q_survivor_ids": member_ids,
        }
        class_rows.append(
            {
                "gcm_3q_quotient_class_id": stable_id("gcm3qqcls", payload),
                "raw_class_id": qrow["class_id"],
                "probe_signature": qrow["probe_signature"],
                "member_gcm_3q_survivor_ids": member_ids,
                "member_raw_3q_survivor_ids": qrow["member_survivor_ids"],
                "member_count": qrow["member_count"],
                "family_counts": qrow["family_counts"],
                "tripartite_entangled_anchor_count": qrow["tripartite_entangled_anchor_count"],
                "content_sha256": stable_sha256(payload),
            }
        )

    region_rows = []
    for qrow, class_row in zip(carve["quotient"]["classes"], class_rows, strict=True):
        payload = {
            "gcm_3q_object_id": gcm_3q_object_id,
            "raw_region_id": qrow["class_id"],
            "member_gcm_3q_quotient_class_ids": [class_row["gcm_3q_quotient_class_id"]],
            "cut_lattice": list(CUTS),
            "region_scope": "class_local_attachment_region",
        }
        region_rows.append(
            {
                "gcm_3q_candidate_region_id": stable_id("gcm3qcreg", payload),
                "raw_region_id": qrow["class_id"],
                "region_scope": "class_local_attachment_region",
                "member_gcm_3q_quotient_class_ids": [class_row["gcm_3q_quotient_class_id"]],
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
        "gcm_3q_object_id": gcm_3q_object_id,
        "gcm_3q_object_id_rule": "sha256 over 1Q/2Q object identities, committed 3Q carve result hash, 3Q counts, survivor family counts, and the A|BC/B|AC/C|AB cut lattice",
        "pinned_spec_sha256": stable_sha256(pinned),
        "frozen_registry": two_q_registry["frozen_registry"],
        "frozen_2q_registry": two_q_registry["frozen_2q_registry"],
        "frozen_3q_registry": {
            "survivors": survivor_rows,
            "quotient_classes": class_rows,
            "candidate_regions": region_rows,
        },
        "counts": {
            "survivor_count": len(survivor_rows),
            "quotient_class_count": len(class_rows),
            "candidate_region_count": len(region_rows),
            "product_lift_survivor_count": sum(1 for row in survivor_rows if row["family"] == "2q_survivor_product_lift"),
            "tripartite_entangled_survivor_count": sum(1 for row in survivor_rows if row["tripartite_entangled_anchor"]),
        },
        "source_locks": {
            "three_q_carve_result": source_lock(THREE_Q_CARVE_RESULT, "committed 545-survivor 3Q carve v1 source"),
            "three_q_carve_validator": source_lock(THREE_Q_CARVE_VALIDATOR, "3Q carve validator receipt"),
            "two_q_freeze_registry": source_lock(TWO_Q_FREEZE_REGISTRY, "2Q freeze registry source"),
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "1Q freeze registry source"),
            "audit_standards": source_lock(AUDIT_STANDARDS, "G.2a standards"),
        },
    }
    body = dict(registry)
    registry["registry_body_sha256"] = stable_sha256(body)
    return registry


def registry_maps(registry: dict[str, Any]) -> dict[str, dict[Any, str]]:
    return {
        "gcm3q_by_raw": {
            row["raw_3q_survivor_id"]: row["gcm_3q_survivor_id"]
            for row in registry["frozen_3q_registry"]["survivors"]
        },
        "gcm3q_class_by_raw": {
            row["raw_class_id"]: row["gcm_3q_quotient_class_id"]
            for row in registry["frozen_3q_registry"]["quotient_classes"]
        },
        "gcm3q_region_by_raw_class": {
            row["member_raw_class_ids"][0]: row["gcm_3q_candidate_region_id"]
            for row in registry["frozen_3q_registry"]["candidate_regions"]
        },
    }


def raw_class_for_survivor(carve: dict[str, Any]) -> dict[int, str]:
    out = {}
    for qrow in carve["quotient"]["classes"]:
        for raw_sid in qrow["member_survivor_ids"]:
            out[int(raw_sid)] = qrow["class_id"]
    return out


def two_q_rows_by_gcm_id(two_q_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["gcm_2q_survivor_id"]: row
        for row in two_q_payload["entropy_tables"]["survivor_cut_entropy_rows"]
    }


def cross_rung_lineage(
    carve: dict[str, Any],
    two_q_payload: dict[str, Any],
    registry: dict[str, Any],
) -> tuple[dict[str, Any], dict[int, dict[str, float | bool]]]:
    maps = registry_maps(registry)
    class_by_raw = raw_class_for_survivor(carve)
    two_q_by_id = two_q_rows_by_gcm_id(two_q_payload)
    states = source_states(carve)
    object_maps = []
    two_to_three = []
    projection_deltas: dict[int, dict[str, float | bool]] = {}
    for row in carve["survivors"]:
        raw_sid = int(row["survivor_id"])
        raw_class = class_by_raw[raw_sid]
        map_row = {
            "gcm_3q_survivor_id": maps["gcm3q_by_raw"][raw_sid],
            "raw_3q_survivor_id": raw_sid,
            "candidate_id": row["candidate_id"],
            "candidate_label": row["candidate_label"],
            "family": row["family"],
            "gcm_3q_quotient_class_id": maps["gcm3q_class_by_raw"][raw_class],
            "gcm_3q_candidate_region_id": maps["gcm3q_region_by_raw_class"][raw_class],
            "rho_ABC_content_id": row["rho_ABC_content_id"],
            "tripartite_entangled_anchor": bool(row.get("tripartite_entangled_anchor")),
        }
        if row["family"] == "2q_survivor_product_lift":
            gcm_2q_id = row["source_gcm_2q_survivor_id"]
            rho_abc = states[row["rho_ABC_content_id"]]
            rho_ab = partial_trace_3q(rho_abc, [0, 1])
            source_row = two_q_by_id[gcm_2q_id]
            source_rho_ab = json_to_matrix(source_row["rho_AB"])
            source_local_pin_product = np.kron(json_to_matrix(source_row["rho_A"]), json_to_matrix(source_row["rho_B"]))
            full_delta = q(float(np.max(np.abs(rho_ab - source_rho_ab))))
            local_pin_delta = q(float(np.max(np.abs(rho_ab - source_local_pin_product))))
            full_reproduced = full_delta == 0.0
            projection_deltas[raw_sid] = {
                "full_rho_AB_delta": full_delta,
                "local_pin_product_delta": local_pin_delta,
                "full_rho_AB_reproduced": full_reproduced,
                "full_correlation_not_claimed": not full_reproduced,
            }
            map_row.update(
                {
                    "gcm_2q_survivor_id": gcm_2q_id,
                    "source_2q_survivor_id": row["source_2q_survivor_id"],
                    "projection": "Tr_C(rho_ABC) -> source 2Q local-pin product",
                    "local_pin_product_delta": local_pin_delta,
                    "full_rho_AB_delta": full_delta,
                    "full_rho_AB_reproduced": full_reproduced,
                    "full_2q_correlation_not_claimed": not full_reproduced,
                }
            )
            two_to_three.append(
                {
                    "gcm_2q_survivor_id": gcm_2q_id,
                    "source_2q_survivor_id": row["source_2q_survivor_id"],
                    "gcm_3q_survivor_id": maps["gcm3q_by_raw"][raw_sid],
                    "raw_3q_survivor_id": raw_sid,
                    "TrC_reproduces_2q_local_pin_product": local_pin_delta == 0.0,
                    "TrC_reproduces_full_2q_rho_AB": full_reproduced,
                    "full_2q_correlation_not_claimed": not full_reproduced,
                }
            )
        else:
            map_row.update(
                {
                    "gcm_2q_survivor_id": None,
                    "source_2q_survivor_id": None,
                    "projection": "tripartite-only anchor has no 2Q registry source row",
                    "projection_delta": None,
                }
            )
        object_maps.append(map_row)

    counts = Counter(row["gcm_2q_survivor_id"] for row in two_to_three)
    lineage = {
        "row_id": "cross_rung_2q_3q_product_embedding_and_projection",
        "base_gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_object_id": registry["gcm_3q_object_id"],
        "gcm_3q_registry_body_sha256": registry["registry_body_sha256"],
        "gcm_2q_survivor_ids": [row["gcm_2q_survivor_id"] for row in two_to_three],
        "gcm_3q_survivor_ids": [row["gcm_3q_survivor_id"] for row in object_maps],
        "gcm_3q_quotient_class_ids": [
            row["gcm_3q_quotient_class_id"] for row in registry["frozen_3q_registry"]["quotient_classes"]
        ],
        "gcm_3q_candidate_region_ids": [
            row["gcm_3q_candidate_region_id"] for row in registry["frozen_3q_registry"]["candidate_regions"]
        ],
        "object_maps": object_maps,
        "two_q_to_3q_product_embedding": {
            "input_2q_survivor_count": EXPECTED_2Q_SURVIVOR_COUNT,
            "lifted_3q_survivor_count": len(two_to_three),
            "all_2q_survivors_have_one_3q_lift": len(counts) == EXPECTED_2Q_SURVIVOR_COUNT and set(counts.values()) == {1},
            "embedding_rows": two_to_three,
        },
        "three_q_to_2q_projection": {
            "trace": "Tr_C(rho_ABC)",
            "product_lift_checked_count": len(projection_deltas),
            "product_lift_TrC_reproduces_2q_local_pins": all(
                row["local_pin_product_delta"] == 0.0 for row in projection_deltas.values()
            ),
            "max_abs_delta_TrC_vs_2q_local_pin_product": q(
                max((float(row["local_pin_product_delta"]) for row in projection_deltas.values()), default=0.0)
            ),
            "max_abs_delta_TrC_vs_full_2q_rho_AB": q(
                max((float(row["full_rho_AB_delta"]) for row in projection_deltas.values()), default=0.0)
            ),
            "full_rho_AB_reproduced_product_rows": sum(
                1 for row in projection_deltas.values() if row["full_rho_AB_reproduced"]
            ),
            "full_rho_AB_correlation_not_claimed_rows": sum(
                1 for row in projection_deltas.values() if row["full_correlation_not_claimed"]
            ),
            "tripartite_anchor_projection_status": "not_a_2q_registry_embedding",
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
        rho = states[row["rho_ABC_content_id"]]
        cuts = {name: cut_row(name, rho) for name in CUTS}
        rows.append(
            {
                "gcm_3q_survivor_id": maps["gcm3q_by_raw"][raw_sid],
                "raw_3q_survivor_id": raw_sid,
                "candidate_id": row["candidate_id"],
                "candidate_label": row["candidate_label"],
                "family": row["family"],
                "rho_ABC_content_id": row["rho_ABC_content_id"],
                "rho_ABC_id": stable_id("rhoABC3q", row["rho_ABC_content_id"]),
                "gcm_3q_quotient_class_id": maps["gcm3q_class_by_raw"][raw_class],
                "gcm_3q_candidate_region_id": maps["gcm3q_region_by_raw_class"][raw_class],
                "source_gcm_2q_survivor_id": row.get("source_gcm_2q_survivor_id"),
                "tripartite_entangled_anchor": bool(row.get("tripartite_entangled_anchor")),
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
        by_class[row["gcm_3q_quotient_class_id"]].append(row)
    raw_by_qid = {
        row["gcm_3q_quotient_class_id"]: row
        for row in registry["frozen_3q_registry"]["quotient_classes"]
    }
    out = []
    for qid in sorted(by_class, key=lambda item: raw_by_qid[item]["raw_class_id"]):
        members = by_class[qid]
        cut_stats = {}
        for cut_name in CUTS:
            cut_stats[cut_name] = {}
            metric_names = list(members[0]["cuts"][cut_name]["entropy_values"])
            for metric in metric_names:
                cut_stats[cut_name][metric] = stats(
                    [float(row["cuts"][cut_name]["entropy_values"][metric]) for row in members]
                )
        out.append(
            {
                "gcm_3q_quotient_class_id": qid,
                "raw_class_id": raw_by_qid[qid]["raw_class_id"],
                "member_count": len(members),
                "member_gcm_3q_survivor_ids": [row["gcm_3q_survivor_id"] for row in members],
                "tripartite_entangled_anchor_count": sum(1 for row in members if row["tripartite_entangled_anchor"]),
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


def ckw_for_rho(rho: np.ndarray) -> dict[str, Any]:
    rho_a = partial_trace_3q(rho, [0])
    rho_b = partial_trace_3q(rho, [1])
    rho_c = partial_trace_3q(rho, [2])
    rho_ab = partial_trace_3q(rho, [0, 1])
    rho_ac = partial_trace_3q(rho, [0, 2])
    rho_bc = partial_trace_3q(rho, [1, 2])
    tau_ab = q(concurrence_2q(rho_ab) ** 2)
    tau_ac = q(concurrence_2q(rho_ac) ** 2)
    tau_bc = q(concurrence_2q(rho_bc) ** 2)
    rows = {
        "A|BC": {"one_tangle": one_tangle(rho_a), "pairwise_tangles": {"AB": tau_ab, "AC": tau_ac}},
        "B|AC": {"one_tangle": one_tangle(rho_b), "pairwise_tangles": {"AB": tau_ab, "BC": tau_bc}},
        "C|AB": {"one_tangle": one_tangle(rho_c), "pairwise_tangles": {"AC": tau_ac, "BC": tau_bc}},
    }
    for row in rows.values():
        pair_sum = q(sum(row["pairwise_tangles"].values()))
        margin = q(row["one_tangle"] - pair_sum)
        row["pairwise_sum"] = pair_sum
        row["ckw_margin"] = margin
        row["satisfies_ckw"] = margin >= -1.0e-10
    return rows


def monogamy_table(carve: dict[str, Any], cut_rows: list[dict[str, Any]]) -> dict[str, Any]:
    states = source_states(carve)
    by_raw = {row["raw_3q_survivor_id"]: row for row in cut_rows}
    rows = []
    for survivor in carve["survivors"]:
        if not survivor.get("tripartite_entangled_anchor"):
            continue
        raw_sid = int(survivor["survivor_id"])
        rho = states[survivor["rho_ABC_content_id"]]
        rows.append(
            {
                "state_id": survivor["candidate_label"],
                "candidate_id": survivor["candidate_id"],
                "raw_3q_survivor_id": raw_sid,
                "gcm_3q_survivor_id": by_raw[raw_sid]["gcm_3q_survivor_id"],
                "rho_ABC_content_id": survivor["rho_ABC_content_id"],
                "computed_from_stored_rho_ABC": True,
                "party_cuts": ckw_for_rho(rho),
            }
        )
    return {
        "row_id": "ckw_monogamy_full_3q_attachment_surface",
        "extends_2q_open_row": "gcm_2q_freeze_and_cut_v0.monogamy_row.OPEN_REQUIRES_3Q_FOR_CKW",
        "computed_from_stored_rho_ABC": True,
        "entangled_survivor_count_checked": len(rows),
        "all_party_cuts_satisfy_ckw": all(
            cut["satisfies_ckw"] for row in rows for cut in row["party_cuts"].values()
        ),
        "rows": rows,
    }


def lineage_for_helper(registry: dict[str, Any], lineage: dict[str, Any]) -> dict[str, Any]:
    one_q_survivors = registry["frozen_registry"]["survivors"]
    one_q_classes = registry["frozen_registry"]["quotient_classes"]
    one_q_regions = registry["frozen_registry"]["candidate_regions"]
    return {
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_3q_object_id": registry["gcm_3q_object_id"],
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_SHA256,
        "gcm_3q_registry_body_sha256": registry["registry_body_sha256"],
        "survivor_ids": [one_q_survivors[0]["survivor_id"]],
        "quotient_class_ids": [one_q_classes[0]["quotient_class_id"]],
        "candidate_region_ids": [one_q_regions[0]["candidate_region_id"]],
        "gcm_2q_survivor_ids": lineage["gcm_2q_survivor_ids"],
        "gcm_3q_survivor_ids": lineage["gcm_3q_survivor_ids"],
        "gcm_3q_quotient_class_ids": lineage["gcm_3q_quotient_class_ids"],
        "gcm_3q_candidate_region_ids": lineage["gcm_3q_candidate_region_ids"],
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
    elif rung == "2Q":
        lineage["gcm_2q_registry_body_sha256"] = stale
    elif rung == "3Q":
        lineage["gcm_3q_registry_body_sha256"] = stale
    return variant


def forged_registry(registry: dict[str, Any]) -> dict[str, Any]:
    clone = copy.deepcopy(registry)
    clone.setdefault("counts", {})["survivor_count"] = int(clone.get("counts", {}).get("survivor_count", 0)) + 1
    return clone


def substrate_control_matrix(payload: dict[str, Any], registries: dict[str, dict[str, Any]]) -> dict[str, Any]:
    positive = {
        "1Q": check_with_registry(payload, registries["1Q"], ONE_Q_FREEZE_REGISTRY),
        "2Q": check_with_registry(payload, registries["2Q"], TWO_Q_FREEZE_REGISTRY),
        "3Q": check_with_registry(payload, registries["3Q"], REGISTRY_PATH),
    }
    negatives = {}
    for rung, path in (("1Q", ONE_Q_FREEZE_REGISTRY), ("2Q", TWO_Q_FREEZE_REGISTRY), ("3Q", REGISTRY_PATH)):
        registry = registries[rung]
        negatives[rung] = {
            "lineage_free": check_with_registry(lineage_free_variant(payload), registry, path),
            "forged_registry": check_with_registry(payload, forged_registry(registry), path),
            "stale_lineage": check_with_registry(stale_lineage_variant(payload, rung), registry, path),
        }
    return {"substrate_positive": positive, "substrate_negatives": negatives}


def all_pass_substrate_controls(controls: dict[str, Any]) -> bool:
    positives = controls["substrate_positive"]
    negatives = controls["substrate_negatives"]
    return all(row.get("ok") is True for row in positives.values()) and all(
        item.get("ok") is False for rung in negatives.values() for item in rung.values()
    )


def build_packet(write: bool = True) -> dict[str, Any]:
    carve = load_json(THREE_Q_CARVE_RESULT)
    two_q_payload = load_json(TWO_Q_FREEZE_RESULT)
    two_q_registry = load_json(TWO_Q_FREEZE_REGISTRY)
    one_q_registry = load_json(ONE_Q_FREEZE_REGISTRY)
    registry = build_3q_registry(carve, two_q_registry)
    if write:
        write_json(REGISTRY_PATH, registry)

    lineage, projection_deltas = cross_rung_lineage(carve, two_q_payload, registry)
    rows = survivor_cut_rows(carve, registry)
    classes = class_cut_rows(registry, rows)
    anchor_profiles = [row for row in rows if row["tripartite_entangled_anchor"]]
    helper_payload = {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "gcm_lineage": lineage_for_helper(registry, lineage),
    }
    substrate_controls = substrate_control_matrix(
        helper_payload,
        {"1Q": one_q_registry, "2Q": two_q_registry, "3Q": registry},
    )
    ckw = monogamy_table(carve, rows)
    no_audit = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    two_q_regression = {
        "trace": "Tr_C(rho_ABC)",
        "product_lift_checked_count": len(projection_deltas),
        "partial_traces_reproduce": all(row["local_pin_product_delta"] == 0.0 for row in projection_deltas.values()),
        "partial_trace_scope": "2Q local-pin products from stored rho_A and rho_B; full entangled rho_AB is not claimed for the 16 2Q purification rows",
        "max_abs_delta_TrC_vs_2q_local_pin_product": q(
            max((float(row["local_pin_product_delta"]) for row in projection_deltas.values()), default=0.0)
        ),
        "max_abs_delta_TrC_vs_full_2q_rho_AB": q(
            max((float(row["full_rho_AB_delta"]) for row in projection_deltas.values()), default=0.0)
        ),
        "full_rho_AB_reproduced_product_rows": sum(
            1 for row in projection_deltas.values() if row["full_rho_AB_reproduced"]
        ),
        "full_rho_AB_correlation_not_claimed_rows": sum(
            1 for row in projection_deltas.values() if row["full_correlation_not_claimed"]
        ),
    }
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "declared_surface": "freeze/registry + cut layers | carve-attached | 3Q",
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "runtime_flux_blocked": True,
        "coordinates": {
            "layers": "3Q freeze/registry plus all bipartition cut attachments",
            "nesting": "A|BC, B|AC, C|AB cut lattice",
            "qubit_depth": "3Q",
        },
        "cut_lattice": {
            "bipartitions": list(CUTS),
            "tensor_order": "computational basis |ABC> with index = 4*A + 2*B + C",
            "stored_reductions": ["rho_left", "rho_right"],
        },
        "gcm_3q_object_id": registry["gcm_3q_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "registry_path": rel(REGISTRY_PATH),
        "gcm_lineage": helper_payload["gcm_lineage"],
        "counts": {
            "three_q_survivor_count": len(rows),
            "three_q_class_count": len(classes),
            "three_q_candidate_region_count": len(registry["frozen_3q_registry"]["candidate_regions"]),
            "product_lift_survivor_count": registry["counts"]["product_lift_survivor_count"],
            "tripartite_entangled_survivor_count": registry["counts"]["tripartite_entangled_survivor_count"],
        },
        "frozen_3q_registry": registry["frozen_3q_registry"],
        "cross_rung_lineage": lineage,
        "cut_tables": {
            "survivor_cut_rows": rows,
            "class_cut_rows": classes,
        },
        "tripartite_only_anchor_profile": anchor_profiles[0],
        "monogamy_table": ckw,
        "controls": {
            "two_q_regression": two_q_regression,
            **substrate_controls,
            "runtime_flux_blocked": {
                "blocked": True,
                "next_packet": "J_ent/J_cut at 3Q",
                "reason": "this packet freezes the attachment surface only",
            },
        },
        "source_locks": {
            "three_q_carve_result": source_lock(THREE_Q_CARVE_RESULT, "state-artifacted 545 survivor 3Q carve v1"),
            "three_q_carve_validator": source_lock(THREE_Q_CARVE_VALIDATOR, "3Q carve v1 validator"),
            "two_q_freeze_result": source_lock(TWO_Q_FREEZE_RESULT, "2Q freeze and cut packet"),
            "two_q_freeze_registry": source_lock(TWO_Q_FREEZE_REGISTRY, "2Q registry lineage source"),
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "1Q object registry lineage source"),
            "layer_stack_reference": source_lock(LAYER_STACK_REFERENCE, "GCM layer stack reference"),
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
            "3Q registry and cut attachment surface",
            "all three stored bipartition reductions and entropy families",
            "CKW table for stored tripartite entangled survivors",
            "3Q helper lineage hardening checks",
        ],
        "blocked_consumers": [
            "runtime_flux",
            "J_ent",
            "J_cut",
            "formal_admission",
            "canonical_manifold_claim",
            "axis_or_bridge_claim",
        ],
    }
    payload["all_pass"] = (
        len(rows) == EXPECTED_3Q_SURVIVOR_COUNT
        and len(classes) == EXPECTED_3Q_CLASS_COUNT
        and registry["counts"]["product_lift_survivor_count"] == EXPECTED_3Q_PRODUCT_LIFT_COUNT
        and registry["counts"]["tripartite_entangled_survivor_count"] == EXPECTED_3Q_TRIPARTITE_ANCHOR_COUNT
        and len(anchor_profiles) == 1
        and two_q_regression["partial_traces_reproduce"]
        and ckw["computed_from_stored_rho_ABC"]
        and ckw["entangled_survivor_count_checked"] == EXPECTED_3Q_TRIPARTITE_ANCHOR_COUNT
        and ckw["all_party_cuts_satisfy_ckw"]
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
                "gcm_3q_object_id": payload["gcm_3q_object_id"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
