#!/usr/bin/env python3
"""Validate cross-packet convention pins for the v6 geometry estate.

This is a receipt-bound guard, not a promotion gate.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "system_v6" / "receipts" / "estate_convention_ledger_20260610.md"
OCTONION_RECEIPT = ROOT / "system_v6" / "receipts" / "octonion_orientation_reconciliation_20260610.md"
CANON_ARTIFACT_RECEIPT = ROOT / "system_v6" / "receipts" / "canon_algebra_artifact_v1_results_20260610.json"

RESULTS = {
    "geo_s1_exact": ROOT / "system_v6/sims/geo_s1_exact_closure_v0/results/geo_s1_exact_closure_v0_envelope_results.json",
    "geo_s2": ROOT / "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json",
    "geo_s3": ROOT / "system_v6/sims/geo_s3_density_observable_v0/results/geo_s3_density_observable_v0_envelope_results.json",
    "geo_s4": ROOT / "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "geo_s5": ROOT / "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "geo_s7": ROOT / "system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json",
    "mct_dynamic": ROOT / "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json",
    "bloch_root": ROOT / "system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json",
    "mct_weld": ROOT / "system_v6/sims/mct_nonassoc_weld_packet_v0/results/mct_nonassoc_weld_packet_v0_envelope_results.json",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_text(value: Any) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def check_source_hash(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    source = payload.get("source_path")
    expected = payload.get("source_sha256")
    if not source or not expected:
        return {"pass": False, "reason": "missing source_path/source_sha256"}
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = ROOT / source_path
    if not source_path.exists():
        return {"pass": False, "reason": f"source missing: {source}"}
    actual = sha256_file(source_path)
    return {"pass": actual == expected, "path": str(source_path.relative_to(ROOT)), "sha256": actual}


def build_ledger() -> tuple[bool, list[dict[str, Any]], dict[str, Any]]:
    payloads = {name: load_json(path) for name, path in RESULTS.items()}
    texts = {name: flatten_text(payload) for name, payload in payloads.items()}
    source_hashes = {name: check_source_hash(RESULTS[name], payload) for name, payload in payloads.items()}

    checks: list[dict[str, Any]] = []
    def add(name: str, passed: bool, evidence: Any, failure: str) -> None:
        checks.append({"name": name, "pass": bool(passed), "evidence": evidence, "failure": None if passed else failure})

    add(
        "bloch_basis_mapped",
        "-sigma_y_standard" in texts["geo_s1_exact"]
        and "-sigma_y_standard" in texts["geo_s3"]
        and "source_locked_standard_bloch" in texts["geo_s4"]
        and "source_locked_standard_bloch" in texts["geo_s5"]
        and ("J" in texts["geo_s4"] or "diag(1,-1,1)" in texts["geo_s4"])
        and ("J" in texts["geo_s5"] or "diag(1,-1,1)" in texts["geo_s5"]),
        {
            "s1_s3_basis": "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)",
            "s4_s5_expected": "source_locked_standard_bloch plus J conversion into pinned basis",
        },
        "Bloch basis or standard-to-pinned J conversion is not explicit across S1/S3/S4/S5.",
    )
    add(
        "holonomy_sense_mapped",
        "-2*pi*cos(2*eta)" in texts["geo_s7"]
        and "h(eta_j)-h(eta_i)+Phi_ij" in texts["geo_s7"]
        and ("Berry" in texts["geo_s2"] or "berry" in texts["geo_s2"])
        and ("endpoint" in texts["geo_s2"] or "global spinor phase" in texts["geo_s2"]),
        {
            "target": "h(eta)=-2*pi*cos(2*eta)",
            "stokes": "h(eta_j)-h(eta_i)+Phi_ij=0",
            "distinction": "accumulated phi is separated from endpoint/Berry phase",
        },
        "Holonomy target/sense or endpoint/Berry distinction is unmapped.",
    )
    add(
        "entropy_base_mapped",
        ("natural_log" in texts["geo_s3"] or "nats" in texts["geo_s3"])
        and ("nats" in texts["mct_dynamic"] or "natural" in texts["mct_dynamic"]),
        {"primary": "nats/natural log", "auxiliary": "bits/log2 only if labelled"},
        "Entropy base is not pinned to nats/natural log across S3 and MCT dynamic.",
    )
    add(
        "rotation_handedness_mapped",
        ("R_x" in texts["geo_s4"] or "R_x" in texts["geo_s5"])
        and ("R_z" in texts["geo_s4"] or "R_z" in texts["geo_s5"])
        and "source_locked_standard_bloch" in (texts["geo_s4"] + texts["geo_s5"])
        and ("H_L" in texts["geo_s5"] or "+H0" in texts["geo_s5"])
        and ("H_R" in texts["geo_s5"] or "-H0" in texts["geo_s5"]),
        {"s4": "R_x/R_z source-locked standard basis", "s5": "H_L=+H0 and H_R=-H0"},
        "Rotation handedness is not explicit across S4/S5.",
    )
    bloch_orientation = payloads["bloch_root"].get("zero_divisor_convention_translation", {}).get("blind_sheet_own_convention", {})
    weld_lift = payloads["mct_weld"].get("carrier_provenance", {}).get("committed_basis_lift", {})
    add(
        "octonion_orientation_reconciled_without_reuse",
        OCTONION_RECEIPT.exists()
        and bloch_orientation.get("octonion_permutation_old_to_new") == [0, 3, 2, 1, 6, 7, 4, 5]
        and bloch_orientation.get("octonion_signs_old_to_new") == [1, -1, 1, 1, -1, -1, 1, -1]
        and weld_lift.get("perm") == [0, 1, 2, 3, 4, 7, 6, 5]
        and weld_lift.get("signs") == [1, 1, 1, 1, 1, -1, 1, -1],
        {
            "receipt": str(OCTONION_RECEIPT.relative_to(ROOT)),
            "bloch_old_to_new": bloch_orientation.get("octonion_permutation_old_to_new"),
            "weld_basis_lift": weld_lift,
            "status": "distinct maps documented; no cross-packet reuse claim promoted",
        },
        "Octonion orientation maps are missing or reused without a reconciliation receipt.",
    )
    add(
        "canon_receipt_path_live",
        CANON_ARTIFACT_RECEIPT.exists(),
        {"path": str(CANON_ARTIFACT_RECEIPT.relative_to(ROOT))},
        "Canon algebra artifact receipt path is absent.",
    )
    add(
        "source_hashes_current",
        all(row["pass"] for row in source_hashes.values()),
        source_hashes,
        "One or more result source_path/source_sha256 pairs does not match current source bytes.",
    )
    return all(row["pass"] for row in checks), checks, source_hashes


def write_receipt(ok: bool, checks: list[dict[str, Any]]) -> None:
    lines = [
        "# Estate Convention Ledger 2026-06-10",
        "",
        f"Generated: {dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        "",
        f"Outcome: {'PASS' if ok else 'FAIL'}",
        "",
        "Scope: committed/current result files for S1/S2/S3/S4/S5/S7, MCT dynamic, Bloch root, and MCT nonassoc weld. This ledger is a convention guard only; it promotes no claim.",
        "",
        "| Check | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for check in checks:
        evidence = json.dumps(check["evidence"], sort_keys=True)
        status = "PASS" if check["pass"] else f"FAIL: {check['failure']}"
        lines.append(f"| `{check['name']}` | {status} | `{evidence}` |")
    lines.append("")
    RECEIPT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write-receipt", action="store_true")
    args = parser.parse_args()
    ok, checks, _ = build_ledger()
    if not args.no_write_receipt:
        write_receipt(ok, checks)
    print(json.dumps({"ok": ok, "receipt": str(RECEIPT.relative_to(ROOT)), "checks": checks}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
