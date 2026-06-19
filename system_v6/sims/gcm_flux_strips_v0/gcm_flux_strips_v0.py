#!/usr/bin/env python3
"""Complete occupied-shell geometric flux strips for the GCM Hopf packet."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from itertools import combinations
from pathlib import Path
from typing import Any


SIM_ID = "gcm_flux_strips_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

REGISTRY_PATH = ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
ATTACH_PATH = ROOT / "system_v6" / "sims" / "gcm_connection_flux_attach_v0" / "results" / "gcm_connection_flux_attach_v0_results.json"
GEOMETRY_PATH = ROOT / "system_v6" / "sims" / "gcm_geometry_attach_v0" / "results" / "gcm_geometry_attach_v0_results.json"
AUDIT_PATH = ROOT / "system_v6" / "sims" / "gcm_connection_flux_attach_v0" / "audit_verdict.md"

EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
SHELL_ORDER = ["0", "pi/8", "pi/4", "3pi/8", "pi/2"]

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from gcm_substrate_check import gcm_substrate_check  # noqa: E402


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


def git_last_commit(path: Path) -> str | None:
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() or None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0.0 else rounded


def eta_value(label: str) -> float:
    return {
        "0": 0.0,
        "pi/8": math.pi / 8.0,
        "pi/4": math.pi / 4.0,
        "3pi/8": 3.0 * math.pi / 8.0,
        "pi/2": math.pi / 2.0,
    }[label]


def holonomy(eta: float) -> float:
    return -2.0 * math.pi * math.cos(2.0 * eta)


def curvature_integral(eta_i: float, eta_j: float) -> float:
    return 2.0 * math.pi * (math.cos(2.0 * eta_j) - math.cos(2.0 * eta_i))


def shell_groups(attach_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = attach_payload["connection_flux_attachment"]["shell_rows"]
    return {row["T_eta_label"]: row for row in rows}


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    variant.pop("gcm_lineage", None)
    variant.pop("gcm_object_id", None)
    variant.pop("registry_body_sha256", None)
    for row in variant.get("complete_strip_table", []):
        row.pop("survivor_ids", None)
        row.pop("quotient_class_ids", None)
        row.pop("candidate_region_ids", None)
    return variant


def build_strip_table(attach_payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups = shell_groups(attach_payload)
    rows: list[dict[str, Any]] = []
    for index, (left_label, right_label) in enumerate(combinations(SHELL_ORDER, 2), start=1):
        left_eta = eta_value(left_label)
        right_eta = eta_value(right_label)
        left_h = holonomy(left_eta)
        right_h = holonomy(right_eta)
        h_delta = right_h - left_h
        int_f = curvature_integral(left_eta, right_eta)
        residual = h_delta + int_f
        left = groups[left_label]
        right = groups[right_label]
        survivor_ids = sorted(set(left["survivor_ids"]) | set(right["survivor_ids"]))
        quotient_class_ids = sorted(set(left["quotient_class_ids"]) | set(right["quotient_class_ids"]))
        candidate_region_ids = sorted(set(left["candidate_region_ids"]) | set(right["candidate_region_ids"]))
        rows.append(
            {
                "strip_index": index,
                "ordered_shell_pair": [left_label, right_label],
                "eta_interval_rad": [q(left_eta), q(right_eta)],
                "boundary_holonomy_difference": q(h_delta),
                "curvature_integral_int_F": q(int_f),
                "stokes_orientation_equation": "boundary_holonomy_difference + curvature_integral_int_F = 0",
                "stokes_residual": q(residual),
                "stokes_verified": abs(residual) <= 1e-12,
                "leakage_adjudication": {
                    "v0_leakage_meaning": "Stokes residual on a geometric Hopf curvature strip, not transport/runtime leakage.",
                    "status": "closed_no_leakage" if abs(residual) <= 1e-12 else "open_residual",
                    "residual_abs": q(abs(residual)),
                },
                "survivor_ids": survivor_ids,
                "quotient_class_ids": quotient_class_ids,
                "candidate_region_ids": candidate_region_ids,
            }
        )
    return rows


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("classification") != "scratch_diagnostic":
        errors.append("classification must be scratch_diagnostic")
    if payload.get("promotion_allowed") is not False or payload.get("formal_admission_allowed") is not False:
        errors.append("promotion/formal admission must be false")
    if payload.get("three_axis_declaration") != {"layers": "10-12", "nesting": "integrated", "qubit_depth": "1Q"}:
        errors.append("three_axis_declaration must be layers 10-12 | integrated | 1Q")
    table = payload.get("complete_strip_table", [])
    if len(table) != 10:
        errors.append(f"expected 10 strip rows, got {len(table)}")
    expected_pairs = [list(pair) for pair in combinations(SHELL_ORDER, 2)]
    if [row.get("ordered_shell_pair") for row in table] != expected_pairs:
        errors.append("strip table does not cover every increasing occupied-shell pair in shell order")
    for row in table:
        if row.get("stokes_verified") is not True:
            errors.append(f"Stokes row failed: {row.get('ordered_shell_pair')}")
        if abs(row.get("stokes_residual", 1.0)) > 1e-12:
            errors.append(f"nonzero Stokes residual: {row.get('ordered_shell_pair')}")
        if row.get("leakage_adjudication", {}).get("status") != "closed_no_leakage":
            errors.append(f"leakage row not closed: {row.get('ordered_shell_pair')}")
    substrate = payload.get("substrate_enforcement", {})
    if substrate.get("positive_payload_ok", {}).get("ok") is not True:
        errors.append("positive substrate check failed")
    if substrate.get("lineage_free_negative", {}).get("ok") is not False:
        errors.append("lineage-free negative did not fail")
    g2 = payload.get("corrected_g2_metadata", {})
    if g2.get("geometry_attach_audit_commit") != "748fca97c" or "in_flight" in json.dumps(g2):
        errors.append("G2 metadata not corrected to landed attach audit commit")
    return errors


def build_payload(write: bool = True) -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    attach_payload = load_json(ATTACH_PATH)
    geometry_payload = load_json(GEOMETRY_PATH)
    strip_table = build_strip_table(attach_payload)
    payload: dict[str, Any] = {
        "schema": "gcm_flux_strips_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": "scratch_diagnostic_layers_10_12_1Q_complete_geometric_flux_strip_table",
        "claim": "Complete geometric Hopf curvature strip table over every increasing occupied-shell pair on the landed attached GCM survivor lineage.",
        "three_axis_declaration": {"layers": "10-12", "nesting": "integrated", "qubit_depth": "1Q"},
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "geometric_flux_only_fence": {
            "runtime_or_qit_flux_claimed": False,
            "statement": "This packet computes geometric Hopf curvature flux only; it is not runtime, QIT, memory, chirality, terrain, axis, or physics flux.",
        },
        "gcm_object_id": registry["gcm_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "gcm_lineage": copy.deepcopy(attach_payload["gcm_lineage"]),
        "source_locks": {
            "registry": {"path": rel(REGISTRY_PATH), "sha256": sha256_file(REGISTRY_PATH), "git_last_commit": git_last_commit(REGISTRY_PATH)},
            "connection_flux_attach_result": {"path": rel(ATTACH_PATH), "sha256": sha256_file(ATTACH_PATH), "git_last_commit": git_last_commit(ATTACH_PATH)},
            "connection_flux_attach_audit": {"path": rel(AUDIT_PATH), "sha256": sha256_file(AUDIT_PATH), "git_last_commit": git_last_commit(AUDIT_PATH)},
            "geometry_attach_result": {"path": rel(GEOMETRY_PATH), "sha256": sha256_file(GEOMETRY_PATH), "git_last_commit": git_last_commit(GEOMETRY_PATH)},
        },
        "upstream_commits": {
            "flux_audit_commit": "5afa1ea53",
            "geometry_attach_audit_commit": "748fca97c",
        },
        "corrected_g2_metadata": {
            "status": "resolved_landed_attach_audit",
            "geometry_attach_audit_commit": "748fca97c",
            "required_caveat": "G1_shell_pattern_is_carved_probe_support_signature",
            "correction": "This packet consumes the landed geometry attach verdict; no in-flight conditionality is carried forward.",
        },
        "formula_pin": {
            "connection_form": "A = d phi + cos(2*eta) d chi",
            "curvature_form": "F = -2*sin(2*eta) d eta wedge d chi",
            "holonomy_lifted_cycle": "h(eta) = -2*pi*cos(2*eta)",
            "stokes_orientation": "h(eta_j)-h(eta_i) + int_[eta_i,eta_j]F = 0",
        },
        "occupied_shells": SHELL_ORDER,
        "complete_strip_table": strip_table,
        "leakage_summary": {
            "row_count": len(strip_table),
            "closed_count": sum(1 for row in strip_table if row["leakage_adjudication"]["status"] == "closed_no_leakage"),
            "open_count": sum(1 for row in strip_table if row["leakage_adjudication"]["status"] != "closed_no_leakage"),
            "max_abs_stokes_residual": q(max(abs(row["stokes_residual"]) for row in strip_table)),
            "adjudication": "the v0 leakage rows are geometric Stokes closure rows; every complete strip is closed at tolerance",
        },
        "substrate_context": {
            "geometry_all_pass": geometry_payload.get("all_pass"),
            "attach_all_pass": attach_payload.get("all_pass"),
            "expected_object_id": EXPECTED_OBJECT_ID,
            "expected_registry_body_sha256": EXPECTED_REGISTRY_BODY_SHA256,
        },
        "TOOL_MANIFEST": {
            "python_stdlib": {"tried": True, "used": True, "reason": "deterministic shell-pair enumeration, Stokes arithmetic, JSON receipts"},
            "gcm_substrate_check": {"tried": True, "used": True, "reason": "positive lineage enforcement and lineage-free negative"},
        },
        "TOOL_INTEGRATION_DEPTH": {
            "python_stdlib": "load_bearing",
            "gcm_substrate_check": "load_bearing",
        },
        "classical_baseline": {
            "baseline": "lineage-free payload and no-Stokes-orientation closure checks",
            "divergence_log": [
                "lineage-free payload fails gcm_substrate_check",
                "every real strip requires the orientation equation h_delta + int_F = 0",
            ],
        },
        "disallowed_claims": [
            "THE manifold",
            "runtime flux",
            "QIT flux",
            "memory flux",
            "chirality flux",
            "terrain admission",
            "axis admission",
            "physics admission",
            "formal admission",
        ],
    }
    positive = gcm_substrate_check(payload, REGISTRY_PATH)
    negative = gcm_substrate_check(lineage_free_variant(payload), REGISTRY_PATH)
    payload["substrate_enforcement"] = {
        "helper": "scripts/gcm_substrate_check.py",
        "positive_payload_ok": positive,
        "lineage_free_negative": negative,
        "negative_failed_as_required": negative.get("ok") is False,
    }
    payload["validation_errors"] = validate_payload(payload)
    payload["all_pass"] = not payload["validation_errors"]
    if write:
        write_json(RESULT_PATH, payload)
        write_json(ENVELOPE_PATH, {"sim_id": SIM_ID, "all_pass": payload["all_pass"], "result_path": rel(RESULT_PATH), "strip_count": len(strip_table), "max_abs_stokes_residual": payload["leakage_summary"]["max_abs_stokes_residual"]})
        write_json(NEGATIVE_PATH, negative)
    return payload


def main() -> None:
    payload = build_payload(write=True)
    print(json.dumps({"sim_id": SIM_ID, "all_pass": payload["all_pass"], "strip_count": len(payload["complete_strip_table"]), "result_path": rel(RESULT_PATH)}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

