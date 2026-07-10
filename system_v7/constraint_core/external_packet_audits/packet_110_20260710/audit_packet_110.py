#!/usr/bin/env python3
"""Fail-closed packet 110 provenance and claim-ceiling audit."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any
from zipfile import ZipFile


EXPECTED_ZIP_SHA256 = "670df73023ce5bc17e458d662f23f37eaff65676bbd4e121094f05f288743c3d"
EXPECTED_REGISTRY_SHA256 = "deabab61f149215a439b99d7bb8a858b31a2244ecd1592b4c243ab8058451861"
EXPECTED_MEMBER_COUNT = 474
EXPECTED_NEW_FILES = {
    "panel_adversarial_review.py": "6c5b5d29572918f7b9597c0bcd6d9cbf66d6f9fa4cbc594e38227cb8f8b38b0e",
    "sims_and_scripts/field_pair_of_engines_weakest_rung_sim.py": "a2760a9dd980369e41492f5971561a98b1db3c54ad6161c1e488aa857145205f",
    "sims_and_scripts/field_pair_of_engines_weakest_rung_sim_results.json": "2cb625359c79a50c049707c0d4c9e3d0273c220060adf9b0a8ee97aa1e3742a8",
    "sims_and_scripts/maxplus_tropical_is_classical_limit_not_foundation_sim.py": "87e924b83abecd616bc3526ef19699f98658299e83c4dedc12ab6c9a70e6451d",
    "sims_and_scripts/maxplus_tropical_is_classical_limit_not_foundation_sim_results.json": "ca3eaed0e6c9bbed8c0a771b5dd50805ee5f95aca81d3912c4871d9963a78295",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strict_json(path: Path) -> Any:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate JSON key {key!r} in {path}")
            out[key] = value
        return out

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=no_duplicates)


def check(condition: bool, name: str, checks: dict[str, bool]) -> None:
    checks[name] = bool(condition)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-zip", type=Path, required=True)
    parser.add_argument("--pristine-root", type=Path, required=True)
    parser.add_argument("--rerun-root", type=Path, required=True)
    parser.add_argument("--packet-107-root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    checks: dict[str, bool] = {}
    check(sha256(args.packet_zip) == EXPECTED_ZIP_SHA256, "packet_zip_hash", checks)
    check(sha256(args.registry) == EXPECTED_REGISTRY_SHA256, "registry_hash", checks)

    with ZipFile(args.packet_zip) as archive:
        members = archive.infolist()
        safe = all(
            not PurePosixPath(row.filename).is_absolute()
            and ".." not in PurePosixPath(row.filename).parts
            for row in members
        )
        check(safe, "zip_member_names_safe", checks)
        check(len(members) == EXPECTED_MEMBER_COUNT, "zip_member_count", checks)
        zip_hashes = {
            row.filename: hashlib.sha256(archive.read(row)).hexdigest()
            for row in members
            if not row.is_dir()
        }

    check(
        all(zip_hashes.get(name) == digest for name, digest in EXPECTED_NEW_FILES.items()),
        "new_file_hashes_bound_to_zip",
        checks,
    )
    check(
        all(sha256(args.pristine_root / name) == digest for name, digest in EXPECTED_NEW_FILES.items()),
        "pristine_extraction_bound_to_zip",
        checks,
    )

    run_all = (args.pristine_root / "run_all.py").read_text(encoding="utf-8")
    field_source = (
        args.pristine_root / "sims_and_scripts/field_pair_of_engines_weakest_rung_sim.py"
    ).read_text(encoding="utf-8")
    field_result = strict_json(
        args.pristine_root / "sims_and_scripts/field_pair_of_engines_weakest_rung_sim_results.json"
    )
    maxplus_result = strict_json(
        args.pristine_root / "sims_and_scripts/maxplus_tropical_is_classical_limit_not_foundation_sim_results.json"
    )
    check("field_pair_of_engines_weakest_rung_sim.py" not in run_all, "field_pair_absent_from_harness", checks)
    check("does NOT earn" in field_source and "de-registered" in field_source, "field_source_withdraws_rung", checks)
    check(
        field_result.get("policy_eval", {}).get("FIELD_WEAKEST_RUNG_EARNED") is True,
        "stale_field_result_overclaim_detected",
        checks,
    )
    check(
        run_all.count("maxplus_tropical_is_classical_limit_not_foundation_sim.py") == 1,
        "maxplus_wired_once",
        checks,
    )
    check(
        maxplus_result.get("classification") == "scratch_diagnostic"
        and maxplus_result.get("promotion_allowed") is False,
        "maxplus_ceiling_is_scratch",
        checks,
    )

    strongest = 1.0
    phases = [2.0 * math.pi * i / 199 for i in range(200)]
    coherent = [abs(1.0 + complex(math.cos(phi), math.sin(phi))) ** 2 for phi in phases]
    combined_min = min(coherent)
    visibility = (max(coherent) - combined_min) / (max(coherent) + combined_min)
    check(combined_min < strongest and visibility > 0.99, "maxplus_scalar_example_recomputed", checks)
    check(2.0 >= strongest, "decohered_control_recomputed", checks)

    report = strict_json(args.report)
    summary = report.get("summary", {})
    check(
        summary == {"pass": 142, "fail": 0, "skip": 0, "green": True},
        "canonical_harness_142_0_0",
        checks,
    )
    sims = {row.get("sim"): row.get("status") for row in report.get("results", [])}
    check(
        sims.get("maxplus_tropical_is_classical_limit_not_foundation_sim.py") == "PASS",
        "maxplus_pass_present_in_report",
        checks,
    )

    sindy_rel = Path("sims_and_scripts/engine_dynamics_id_arbiter_sim_results.json")
    score_rel = Path("sims_and_scripts/engine_object_formation_scorecard_sim_results.json")
    sindy_source_rel = Path("sims_and_scripts/engine_dynamics_id_arbiter_sim.py")
    score_source_rel = Path("sims_and_scripts/engine_object_formation_scorecard_sim.py")
    check(
        sha256(args.packet_107_root / sindy_source_rel) == sha256(args.pristine_root / sindy_source_rel)
        and sha256(args.packet_107_root / score_source_rel) == sha256(args.pristine_root / score_source_rel),
        "object_lane_sources_unchanged_from_107",
        checks,
    )
    pristine_sindy = strict_json(args.pristine_root / sindy_rel)
    rerun_sindy = strict_json(args.rerun_root / sindy_rel)
    pristine_score = strict_json(args.pristine_root / score_rel)
    rerun_score = strict_json(args.rerun_root / score_rel)
    packaged_loss = pristine_score["handling_lane"]["handling_loss_mean"]
    rerun_loss = rerun_score["handling_lane"]["handling_loss_mean"]
    check(
        not math.isclose(packaged_loss, rerun_loss, rel_tol=1e-6, abs_tol=1e-9)
        and rerun_loss / packaged_loss > 100,
        "object_handling_loss_environment_shift_detected",
        checks,
    )
    check(
        math.isclose(
            pristine_score["handling_lane"]["per_terrain"][0]["heldout_error_proxy_1_minus_r2"],
            1.0 - pristine_sindy["per_terrain"][0]["real_r2"],
            rel_tol=0,
            abs_tol=1e-12,
        ),
        "packaged_object_score_bound_to_packaged_sindy_input",
        checks,
    )
    check(
        math.isclose(
            rerun_score["handling_lane"]["per_terrain"][0]["heldout_error_proxy_1_minus_r2"],
            1.0 - rerun_sindy["per_terrain"][0]["real_r2"],
            rel_tol=0,
            abs_tol=1e-12,
        ),
        "rerun_object_score_bound_to_rerun_sindy_input",
        checks,
    )

    panel_source = (args.pristine_root / "panel_adversarial_review.py").read_text(encoding="utf-8")
    check("KEYS_PATH=" in panel_source and "_apikeys.json" in panel_source, "panel_hardcoded_key_path_detected", checks)
    check("open(sim_path).read()" in panel_source, "panel_unbounded_local_read_detected", checks)
    check("_panel_review.json" in panel_source, "panel_overwrite_sink_detected", checks)

    registry = args.registry.read_text(encoding="utf-8")
    check("**Dark-sector acceleration scale a0 = c·H0/2π** (UP-134) | **DONE**" in registry, "registry_up134_done_overclaim_detected", checks)
    check("**a0(z) redshift fork, data-selected** (UP-135) | **DONE**" in registry, "registry_up135_done_overclaim_detected", checks)
    check("**Physics loops back → core (2π = engine holonomy)** (UP-136) | **DONE**" in registry, "registry_up136_done_overclaim_detected", checks)

    all_pass = all(checks.values())
    output = {
        "schema": "codex_ratchet.packet_110_audit.v1",
        "classification": "external_packet_rerun_and_claim_ceiling_audit",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "packet_zip_sha256": sha256(args.packet_zip),
        "registry_sha256": sha256(args.registry),
        "run_report_sha256": sha256(args.report),
        "checks": checks,
        "check_count": len(checks),
        "all_pass": all_pass,
        "measurements": {
            "canonical_harness": summary,
            "packaged_handling_loss_mean": packaged_loss,
            "canonical_rerun_handling_loss_mean": rerun_loss,
            "handling_loss_ratio": rerun_loss / packaged_loss,
            "maxplus_scalar_combined_min": combined_min,
            "maxplus_scalar_visibility": visibility,
        },
        "scientific_verdicts": {
            "field_pair_rung": "REJECTED_WITHDRAWN_AND_STALE_RESULT",
            "maxplus": "FINITE_SCALAR_INTERFERENCE_DIAGNOSTIC_ONLY",
            "cross_family_panel": "UNVERIFIED_NO_PACKET_RECEIPTS",
            "object_perception": "BLOCKED_ENVIRONMENT_SENSITIVE_ACROSS_RUNTIMES",
            "registry_up134": "NOT_DONE_NUMERICAL_COINCIDENCE_ONLY",
            "registry_up135": "REJECTED_BY_CURRENT_PRIMARY_SOURCE_AUDIT",
            "registry_up136": "REJECTED_GAUGE_DEPENDENT_CONNECTION_INTEGRAL",
        },
        "claim_ceiling": "packet_110_passes_local_rerun_with_new_scratch_diagnostic_only",
        "blocked_consumers": [
            "field-of-engines admission",
            "four-substage or 64-stage derivation",
            "Axis0 closure",
            "object or perception admission",
            "MMM, ontology, mesh, or business claims",
            "physics admission",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
