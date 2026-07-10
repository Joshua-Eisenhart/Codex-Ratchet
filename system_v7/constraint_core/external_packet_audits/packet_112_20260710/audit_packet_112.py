#!/usr/bin/env python3
"""Independent packet-112 delta, harness, and QFI/BKM robustness audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import zipfile
from pathlib import Path

import numpy as np
from scipy.linalg import logm, sqrtm


EXPECTED_ZIP_SHA256 = "9fc8a6f16af8c5d25c7be5ac9276fb79f7c3f693276733ce3fa381fad820dabd"
EXPECTED_MEMBER_COUNT = 484
EXPECTED_NEW_FILES = {
    "bundle_manifest.json",
    "docs/BUNDLE_GUIDE.md",
    "docs/MATH_INVENTORY.md",
    "docs/TOOLS_AND_REPOS.md",
    "docs/UP_REGISTRY.md",
    "docs/WITHDRAWN_AND_FAILED.md",
    "generate_bundle_docs.py",
    "sims_and_scripts/hott_braid_topology_placed_vs_forced_spinor_sim.py",
    "sims_and_scripts/qfi_fubini_study_placed_vs_forced_bkm_sim.py",
    "sims_and_scripts/qfi_fubini_study_placed_vs_forced_bkm_sim_results.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def files_with_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256(path)
        for path in root.rglob("*")
        if path.is_file()
    }


def g_sld(rho: np.ndarray, tangent: np.ndarray) -> float:
    values, vectors = np.linalg.eigh(rho)
    rotated = vectors.conj().T @ tangent @ vectors
    return float(sum(
        2.0 * abs(rotated[i, j]) ** 2 / (values[i] + values[j])
        for i in range(len(values))
        for j in range(len(values))
    ).real)


def g_bkm(rho: np.ndarray, tangent: np.ndarray) -> float:
    values, vectors = np.linalg.eigh(rho)
    rotated = vectors.conj().T @ tangent @ vectors
    total = 0.0
    for i in range(len(values)):
        for j in range(len(values)):
            if abs(values[i] - values[j]) < 1e-12:
                kernel = 1.0 / values[i]
            else:
                kernel = (math.log(values[i]) - math.log(values[j])) / (values[i] - values[j])
            total += abs(rotated[i, j]) ** 2 * kernel
    return float(total.real)


def relative_entropy(sigma: np.ndarray, rho: np.ndarray) -> float:
    return float(np.trace(sigma @ (logm(sigma) - logm(rho))).real)


def fidelity(rho: np.ndarray, sigma: np.ndarray) -> float:
    root = sqrtm(rho)
    middle = sqrtm(root @ sigma @ root)
    return float(np.trace(middle).real ** 2)


def centered_hessian(function, h: float) -> float:
    return float((function(h) - 2.0 * function(0.0) + function(-h)) / h**2)


def metric_sweep() -> dict:
    sx = np.array([[0, 1], [1, 0]], dtype=complex)
    sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
    sz = np.array([[1, 0], [0, -1]], dtype=complex)
    identity = np.eye(2, dtype=complex)
    rows = []
    for radius in (0.2, 0.5, 0.8):
        for state_axis, tangent_axis in ((sx, sy), (sy, sz), (sz, sx)):
            rho = 0.5 * (identity + radius * state_axis)
            tangent = 0.5 * tangent_axis
            sld = g_sld(rho, tangent)
            bkm = g_bkm(rho, tangent)
            re_errors = []
            bures_errors = []
            for h in (1e-2, 3e-3, 1e-3, 3e-4):
                re_h = centered_hessian(lambda t: relative_entropy(rho + t * tangent, rho), h)
                bures_h = centered_hessian(
                    lambda t: 2.0 * (1.0 - math.sqrt(max(fidelity(rho, rho + t * tangent), 0.0))),
                    h,
                )
                re_errors.append(abs(re_h - bkm))
                bures_errors.append(abs(bures_h - sld / 2.0))
            rows.append({
                "radius": radius,
                "commutator_norm": float(np.linalg.norm(rho @ tangent - tangent @ rho)),
                "g_sld": sld,
                "g_bkm": bkm,
                "metric_difference": abs(sld - bkm),
                "best_relative_entropy_hessian_error": min(re_errors),
                "best_bures_hessian_error": min(bures_errors),
            })

    commuting_rows = []
    for radius in (0.2, 0.5, 0.8):
        rho = 0.5 * (identity + radius * sz)
        tangent = 0.5 * sz
        commuting_rows.append({
            "radius": radius,
            "sld_bkm_difference": abs(g_sld(rho, tangent) - g_bkm(rho, tangent)),
        })

    return {
        "noncommuting_rows": rows,
        "commuting_rows": commuting_rows,
        "all_noncommuting_differences_positive": all(row["metric_difference"] > 1e-4 for row in rows),
        "all_relative_entropy_hessian_checks": all(row["best_relative_entropy_hessian_error"] < 1e-5 for row in rows),
        "all_bures_hessian_checks": all(row["best_bures_hessian_error"] < 1e-4 for row in rows),
        "all_commuting_checks": all(row["sld_bkm_difference"] < 1e-12 for row in commuting_rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-zip", type=Path, required=True)
    parser.add_argument("--pristine-root", type=Path, required=True)
    parser.add_argument("--rerun-root", type=Path, required=True)
    parser.add_argument("--packet-110-root", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with zipfile.ZipFile(args.packet_zip) as archive:
        names = archive.namelist()
        safe_names = all(not name.startswith("/") and ".." not in Path(name).parts for name in names)
        integrity_ok = archive.testzip() is None

    hashes_110 = files_with_hashes(args.packet_110_root)
    hashes_112 = files_with_hashes(args.pristine_root)
    added = set(hashes_112) - set(hashes_110)
    changed = {name for name in set(hashes_112) & set(hashes_110) if hashes_112[name] != hashes_110[name]}

    report = load_json(args.report)
    qfi_source = args.pristine_root / "sims_and_scripts/qfi_fubini_study_placed_vs_forced_bkm_sim.py"
    qfi_result = args.rerun_root / "sims_and_scripts/qfi_fubini_study_placed_vs_forced_bkm_sim_results.json"
    qfi_data = load_json(qfi_result)
    braid_text = (args.pristine_root / "sims_and_scripts/hott_braid_topology_placed_vs_forced_spinor_sim.py").read_text(encoding="utf-8")
    runner_text = (args.pristine_root / "run_all.py").read_text(encoding="utf-8")
    generator_text = (args.pristine_root / "generate_bundle_docs.py").read_text(encoding="utf-8")
    guide_text = (args.pristine_root / "docs/BUNDLE_GUIDE.md").read_text(encoding="utf-8")
    registry_text = (args.pristine_root / "docs/UP_REGISTRY.md").read_text(encoding="utf-8")
    sweep = metric_sweep()

    report_summary = report.get("summary", {})
    report_counts = {
        "pass": int(report_summary.get("pass", -1)),
        "fail": int(report_summary.get("fail", -1)),
        "skip": int(report_summary.get("skip", -1)),
    }
    checks = {
        "packet_zip_hash": sha256(args.packet_zip) == EXPECTED_ZIP_SHA256,
        "zip_member_count": len(names) == EXPECTED_MEMBER_COUNT,
        "zip_member_names_safe": safe_names,
        "zip_integrity": integrity_ok,
        "delta_added_files_exact": added == EXPECTED_NEW_FILES,
        "delta_changed_files_exact": changed == {"CHANGELOG_HARDENING.md", "MODEL_LAYER_LEDGER.md", "run_all.py"},
        "canonical_harness_143_0_0": report_counts == {"pass": 143, "fail": 0, "skip": 0},
        "qfi_registered_once": runner_text.count("qfi_fubini_study_placed_vs_forced_bkm_sim.py") == 1,
        "braid_not_registered": "hott_braid_topology_placed_vs_forced_spinor_sim.py\"" not in runner_text,
        "qfi_result_is_scratch": qfi_data.get("classification") == "scratch_diagnostic" and qfi_data.get("promotion_allowed") is False,
        "qfi_result_has_no_source_hash_receipt": "source_sha256" not in qfi_data,
        "metric_noncommuting_sweep": sweep["all_noncommuting_differences_positive"],
        "relative_entropy_hessian_sweep": sweep["all_relative_entropy_hessian_checks"],
        "bures_hessian_sweep": sweep["all_bures_hessian_checks"],
        "commuting_consistency_sweep": sweep["all_commuting_checks"],
        "braid_scalar_control_detected": "a1*a2-a2*a1" in braid_text,
        "braid_cp1_assertion_detected": "cp1_simply_connected=True" in braid_text,
        "docs_generator_hardcoded_foundation_claims": "complex spinor (qubit)" in generator_text and "FORCED" in generator_text,
        "guide_republishes_forced_claims": "Pawl forced by the data-processing inequality" in guide_text,
        "registry_republishes_rejected_up130": bool(re.search(r"UP-130.*DERIVED", registry_text)),
        "registry_republishes_rejected_up134_136": all(token in registry_text for token in ("UP-134", "UP-135", "UP-136")),
    }

    output = {
        "schema": "codex_ratchet.packet_112_audit.v1",
        "classification": "external_packet_rerun_and_claim_ceiling_audit",
        "packet_zip_sha256": sha256(args.packet_zip),
        "source_hashes": {
            "qfi_source": sha256(qfi_source),
            "qfi_rerun_result": sha256(qfi_result),
            "canonical_report": sha256(args.report),
        },
        "checks": checks,
        "check_count": len(checks),
        "all_pass": all(checks.values()),
        "canonical_harness": report_counts,
        "metric_sweep": sweep,
        "scientific_verdicts": {
            "qfi_bkm": "ROBUST_FINITE_METRIC_FAMILY_WITNESS_ONLY",
            "hott_braid": "WITHDRAWN_SCAFFOLD_CONTROL_IS_BY_CONSTRUCTION",
            "generated_docs": "NONCANON_LEDGER_PROJECTION_WITH_REJECTED_CLAIMS",
            "packet": "LOCAL_RERUN_ONLY_NO_FOUNDATION_MOVEMENT",
        },
        "claim_ceiling": "packet_112_passes_local_rerun_with_robust_finite_qfi_bkm_diagnostic_only",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "blocked_consumers": [
            "BKM or Umegaki uniqueness",
            "four-substage or 64-stage derivation",
            "Axis0, perception, objects, MMMs, ontologies, mesh, business, or physics admission",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
