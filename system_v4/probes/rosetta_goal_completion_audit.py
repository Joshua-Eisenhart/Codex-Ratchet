#!/usr/bin/env python3
"""Completion audit for the Rosetta repair-and-sim scaling goal.

This controller surface summarizes existing receipts. It does not promote any
sim, stage files, commit, or run new scientific work.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent.parent
RESULTS_DIR = SCRIPT_DIR / "a2_state" / "sim_results"
OUT_JSON = RESULTS_DIR / "rosetta_goal_completion_audit_results.json"
OUT_MD = RESULTS_DIR / "rosetta_goal_completion_audit.md"


PATHS = {
    "probe_truth": RESULTS_DIR / "probe_truth_audit_results.json",
    "controller_alignment": RESULTS_DIR / "controller_alignment_audit_results.json",
    "migration_contract": RESULTS_DIR / "migration_contract_audit_results.json",
    "lego_tool_reporting": RESULTS_DIR / "lego_tool_reporting_audit_results.json",
    "repo_hygiene": RESULTS_DIR / "repo_hygiene_audit_results.json",
    "system_hygiene": RESULTS_DIR / "system_hygiene_supervisor_results.json",
    "lane_catalog": RESULTS_DIR / "source_dirty_lane_catalog.json",
    "lane_catalog_md": RESULTS_DIR / "source_dirty_lane_catalog.md",
    "parallel_review_md": RESULTS_DIR / "source_dirty_parallel_review.md",
    "prime_sidecar": RESULTS_DIR / "prime_qit_sidecar_probe_results.json",
    "prime_sidecar_graveyard": RESULTS_DIR / "prime_qit_sidecar_graveyard_results.json",
    "prime_rosetta_fit": RESULTS_DIR / "prime_rosetta_sidecar_fit_results.json",
    "iching_rosetta": RESULTS_DIR / "six_bit_gray_code_single_flip_cycle_invariant_results.json",
    "visualizer_audit": RESULTS_DIR / "visualizer_engine_lab_receipt_audit_results.json",
    "inventory": PROJECT_DIR / "system_v5" / "evidence" / "sim_inventory_index.json",
    "inventory_unlinked_audit": RESULTS_DIR / "inventory_unlinked_result_audit_results.json",
    "z3_capability": RESULTS_DIR / "z3_capability_results.json",
    "cvc5_capability": RESULTS_DIR / "cvc5_capability_results.json",
    "clifford_capability": RESULTS_DIR / "clifford_capability_results.json",
    "rosetta_lego_registry": RESULTS_DIR / "rosetta_lego_registry_results.json",
    "rosetta_coupled_array": RESULTS_DIR / "rosetta_lego_coupled_array_results.json",
    "rosetta_coupled_array_graveyard": RESULTS_DIR / "rosetta_lego_coupled_array_graveyard_results.json",
}


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
    return payload if isinstance(payload, dict) else None


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_DIR))


def status(ok: bool, evidence: list[str], blocker: str | None = None) -> dict[str, Any]:
    return {
        "status": "met" if ok else "blocked",
        "evidence": evidence,
        "blocker": blocker,
    }


def summary_all_pass(payload: dict[str, Any] | None) -> bool:
    summary = (payload or {}).get("summary", {})
    if isinstance(summary, dict) and summary.get("all_pass") is True:
        return True
    return bool((payload or {}).get("all_pass") is True)


def no_finder_duplicate_admissions(inventory: dict[str, Any] | None) -> bool:
    admitted = (inventory or {}).get("admitted_stems", [])
    return isinstance(admitted, list) and all(" 2" not in str(stem) for stem in admitted)


def source_dirty_packet_coverage(lane_count: int) -> dict[str, Any]:
    manifest_paths = sorted(RESULTS_DIR.glob("source_dirty_lane_manifest__*.json"))
    packet_paths = sorted(RESULTS_DIR.glob("source_dirty_checkpoint_packet__*.json"))
    stage_plan_paths = sorted(RESULTS_DIR.glob("source_dirty_stage_plan__*.json"))
    packets = [read_json(path) for path in packet_paths]
    stage_plans = [read_json(path) for path in stage_plan_paths]
    ready_packets = [
        payload for payload in packets
        if payload and payload.get("ready_for_checkpoint") is True and payload.get("group_id")
    ]
    manifest_group_ids = {
        str(payload.get("selected_group_id"))
        for payload in (read_json(path) for path in manifest_paths)
        if payload and payload.get("selected_group_id")
    }
    packet_group_ids = {
        str(payload.get("group_id"))
        for payload in packets
        if payload and payload.get("group_id")
    }
    stage_plan_group_ids = {
        str(payload.get("group_id"))
        for payload in stage_plans
        if payload and payload.get("group_id")
    }
    ready_stage_plans = [
        payload for payload in stage_plans
        if payload
        and payload.get("group_id")
        and (payload.get("summary") or {}).get("ready_for_staging") is True
    ]
    group_sets_match = manifest_group_ids == packet_group_ids == stage_plan_group_ids
    enough_for_catalog = (
        lane_count > 0
        and len(manifest_paths) >= lane_count
        and len(packet_paths) >= lane_count
        and len(stage_plan_paths) >= lane_count
    )
    return {
        "manifest_count": len(manifest_paths),
        "packet_count": len(packet_paths),
        "stage_plan_count": len(stage_plan_paths),
        "ready_packet_count": len(ready_packets),
        "ready_stage_plan_count": len(ready_stage_plans),
        "manifest_group_ids": sorted(manifest_group_ids),
        "packet_group_ids": sorted(packet_group_ids),
        "stage_plan_group_ids": sorted(stage_plan_group_ids),
        "group_sets_match": group_sets_match,
        "enough_for_catalog": enough_for_catalog,
        "all_ready": (
            enough_for_catalog
            and group_sets_match
            and len(ready_packets) >= lane_count
            and len(ready_stage_plans) >= lane_count
        ),
        "manifest_paths": [rel(path) for path in manifest_paths],
        "packet_paths": [rel(path) for path in packet_paths],
        "stage_plan_paths": [rel(path) for path in stage_plan_paths],
    }


def prompt_item(
    requirement: str,
    ok: bool,
    evidence: list[str],
    command_or_check: str,
    blocker: str | None = None,
) -> dict[str, Any]:
    return {
        "requirement": requirement,
        "status": "met" if ok else "blocked",
        "evidence": evidence,
        "command_or_check": command_or_check,
        "blocker": blocker,
    }


def build_report() -> dict[str, Any]:
    payloads = {name: read_json(path) for name, path in PATHS.items()}
    truth = (payloads["probe_truth"] or {}).get("summary", {})
    controller = (payloads["controller_alignment"] or {}).get("summary", {})
    migration = (payloads["migration_contract"] or {}).get("summary", {})
    lego = (payloads["lego_tool_reporting"] or {}).get("summary", {})
    repo = (payloads["repo_hygiene"] or {}).get("summary", {})
    hygiene = (payloads["system_hygiene"] or {}).get("summary", {})
    catalog = (payloads["lane_catalog"] or {}).get("summary", {})
    prime = (payloads["prime_sidecar"] or {}).get("summary", {})
    prime_graveyard = (payloads["prime_sidecar_graveyard"] or {}).get("summary", {})
    prime_fit = (payloads["prime_rosetta_fit"] or {}).get("summary", {})
    iching = (payloads["iching_rosetta"] or {}).get("summary", {})
    visualizer = (payloads["visualizer_audit"] or {}).get("summary", {})
    inventory = (payloads["inventory"] or {}).get("summary", {})
    inventory_unlinked = (payloads["inventory_unlinked_audit"] or {}).get("summary", {})
    z3_ok = summary_all_pass(payloads["z3_capability"])
    cvc5_ok = summary_all_pass(payloads["cvc5_capability"])
    clifford_ok = summary_all_pass(payloads["clifford_capability"])
    registry_ok = summary_all_pass(payloads["rosetta_lego_registry"])
    coupled_array_ok = summary_all_pass(payloads["rosetta_coupled_array"])
    graveyard_ok = summary_all_pass(payloads["rosetta_coupled_array_graveyard"])

    tracking_green = (
        truth.get("ok") is True
        and bool(controller.get("code_process_green"))
        and bool(controller.get("controller_contract_current"))
        and migration.get("ok") is True
        and lego.get("ok") is True
        and inventory.get("admission_repair_count") == 0
        and inventory_unlinked.get("all_pass") is True
        and no_finder_duplicate_admissions(payloads["inventory"])
    )
    repo_green = hygiene.get("repo_hygiene_green") is True and hygiene.get("overall_green") is True
    catalog_ready = (
        catalog.get("lane_count", 0) > 0
        and catalog.get("lane_count") == catalog.get("ready_for_checkpoint_review_count")
        and catalog.get("missing_companion_count") == 0
    )
    packet_coverage = source_dirty_packet_coverage(int(catalog.get("lane_count") or 0))
    cleanup_packetized = catalog_ready and packet_coverage["all_ready"]
    prime_bounded = (
        prime.get("all_pass") is True
        and prime.get("claim_ceiling") == "sidecar_probe_candidate_prior_only"
        and prime.get("recommendation") == "retool"
    )
    prime_graveyard_bounded = (
        prime_graveyard.get("all_pass") is True
        and prime_graveyard.get("claim_ceiling") == "sidecar_graveyard_control_only"
        and prime_graveyard.get("recommendation") == "retool"
    )
    prime_fit_bounded = (
        prime_fit.get("all_pass") is True
        and prime_fit.get("claim_ceiling") == "sidecar_fit_diagnostic_only"
        and prime_fit.get("recommendation") == "retool"
        and prime_fit.get("all_fits_diagnostic_only") is True
    )

    checklist = {
        "tracking_and_admission_truth": status(
            tracking_green,
            [
                rel(PATHS["probe_truth"]),
                rel(PATHS["controller_alignment"]),
                rel(PATHS["migration_contract"]),
                rel(PATHS["lego_tool_reporting"]),
                rel(PATHS["inventory"]),
                rel(PATHS["inventory_unlinked_audit"]),
            ],
            None if tracking_green else "one or more truth/controller/migration/tool-reporting audits are not green",
        ),
        "capability_admission_result_links": status(
            z3_ok and cvc5_ok and clifford_ok,
            [
                rel(PATHS["z3_capability"]),
                rel(PATHS["cvc5_capability"]),
                rel(PATHS["clifford_capability"]),
            ],
            None
            if z3_ok and cvc5_ok and clifford_ok
            else "one or more admitted capability rows lacks a passing linked result receipt",
        ),
        "rosetta_registry_and_coupling_receipts": status(
            registry_ok and coupled_array_ok and graveyard_ok,
            [
                rel(PATHS["rosetta_lego_registry"]),
                rel(PATHS["rosetta_coupled_array"]),
                rel(PATHS["rosetta_coupled_array_graveyard"]),
            ],
            None
            if registry_ok and coupled_array_ok and graveyard_ok
            else "registry, coupled-array, or graveyard receipt is missing/failing",
        ),
        "bounded_rosetta_and_iching_receipts": status(
            iching.get("all_pass") is True,
            [rel(PATHS["iching_rosetta"])],
            None if iching.get("all_pass") is True else "I Ching/Rosetta receipt is missing or not all_pass",
        ),
        "bounded_prime_sidecar": status(
            prime_bounded and prime_graveyard_bounded and prime_fit_bounded,
            [rel(PATHS["prime_sidecar"]), rel(PATHS["prime_sidecar_graveyard"]), rel(PATHS["prime_rosetta_fit"])],
            None if prime_bounded and prime_graveyard_bounded and prime_fit_bounded else "prime sidecar, graveyard, or Rosetta fit is missing, failing, or over-promoted",
        ),
        "visualizer_receipt_audit": status(
            visualizer.get("all_pass") is True and visualizer.get("qit_or_axis_promotion_allowed") is False,
            [rel(PATHS["visualizer_audit"])],
            None
            if visualizer.get("all_pass") is True and visualizer.get("qit_or_axis_promotion_allowed") is False
            else "visualizer audit is missing/failing or allows over-promotion",
        ),
        "source_dirty_review_catalog": status(
            catalog_ready,
            [rel(PATHS["lane_catalog"]), rel(PATHS["lane_catalog_md"]), rel(PATHS["parallel_review_md"])],
            None if catalog_ready else "source-dirty catalog is missing, incomplete, or has missing companions",
        ),
        "source_dirty_lane_packets": status(
            cleanup_packetized,
            packet_coverage["manifest_paths"] + packet_coverage["packet_paths"] + packet_coverage["stage_plan_paths"],
            None
            if cleanup_packetized
            else "source-dirty lane manifests/packets/stage plans do not cover every cleanup catalog lane",
        ),
        "repo_cleanup_gate": status(
            repo_green,
            [rel(PATHS["system_hygiene"]), rel(PATHS["repo_hygiene"])],
            None
            if repo_green
            else "repo hygiene remains red until manual lanes are checkpointed, archived/quarantined, or reverted",
        ),
    }

    prompt_to_artifact_checklist = [
        prompt_item(
            "Fix honest tracking blockers: duplicate * 2 admissions and admitted rows without linked result evidence.",
            tracking_green,
            [rel(PATHS["inventory"])],
            "inspect inventory summary: admission_repair_count == 0 and no admitted stem contains ' 2'",
            None if tracking_green else "tracking/admission inventory still reports a blocker",
        ),
        prompt_item(
            "Repair or clearly mark z3/cvc5/Clifford capability admissions.",
            z3_ok and cvc5_ok and clifford_ok,
            [rel(PATHS["z3_capability"]), rel(PATHS["cvc5_capability"]), rel(PATHS["clifford_capability"])],
            "read capability result summaries and require all_pass true",
            None if z3_ok and cvc5_ok and clifford_ok else "capability receipt missing or failing",
        ),
        prompt_item(
            "Continue bounded Rosetta lego scaling after tracking is honest.",
            registry_ok and coupled_array_ok,
            [rel(PATHS["rosetta_lego_registry"]), rel(PATHS["rosetta_coupled_array"])],
            "read Rosetta registry and coupled-array receipts and require all_pass true",
            None if registry_ok and coupled_array_ok else "bounded Rosetta registry/coupling receipt missing or failing",
        ),
        prompt_item(
            "Advance order/graveyard variants around the coupled sim.",
            graveyard_ok,
            [rel(PATHS["rosetta_coupled_array_graveyard"])],
            "read negative battery receipt and require all_pass true",
            None if graveyard_ok else "graveyard receipt missing or failing",
        ),
        prompt_item(
            "Advance I Ching-64 lego sim/tracking.",
            iching.get("all_pass") is True,
            [rel(PATHS["iching_rosetta"])],
            "read I Ching-64 Rosetta receipt and require all_pass true",
            None if iching.get("all_pass") is True else "I Ching receipt missing or failing",
        ),
        prompt_item(
            "Run bounded prime/Riemann sidecar without prestige claims.",
            prime_bounded and prime_graveyard_bounded and prime_fit_bounded,
            [rel(PATHS["prime_sidecar"]), rel(PATHS["prime_sidecar_graveyard"]), rel(PATHS["prime_rosetta_fit"])],
            "read prime sidecar, graveyard, and Rosetta-fit summaries: all_pass true, recommendation retool, claim_ceiling sidecar/control/diagnostic only",
            None if prime_bounded and prime_graveyard_bounded and prime_fit_bounded else "prime sidecar/graveyard/fit missing, failing, or over-promoted",
        ),
        prompt_item(
            "Keep visualizer/result tracking inspectable.",
            visualizer.get("all_pass") is True and visualizer.get("qit_or_axis_promotion_allowed") is False,
            [rel(PATHS["visualizer_audit"])],
            "read visualizer receipt audit and require all_pass true with promotion disallowed",
            None
            if visualizer.get("all_pass") is True and visualizer.get("qit_or_axis_promotion_allowed") is False
            else "visualizer receipt audit missing/failing or over-promoting",
        ),
        prompt_item(
            "Packetize cleanup lanes without staging or committing.",
            cleanup_packetized,
            packet_coverage["manifest_paths"] + packet_coverage["packet_paths"] + packet_coverage["stage_plan_paths"],
            "require lane-specific source_dirty_lane_manifest__*.json, source_dirty_checkpoint_packet__*.json, and source_dirty_stage_plan__*.json coverage for every catalog lane, with packets/stage plans ready",
            None
            if cleanup_packetized
            else "cleanup lane manifests/packets/stage plans are missing, incomplete, or not ready",
        ),
        prompt_item(
            "Do not claim goal complete while cleanup gate is red.",
            repo_green,
            [rel(PATHS["system_hygiene"]), rel(PATHS["repo_hygiene"])],
            "read hygiene supervisor: repo_hygiene_green and overall_green must both be true",
            None if repo_green else "repo cleanup gate remains red",
        ),
    ]

    all_complete = all(item["status"] == "met" for item in checklist.values())
    blockers = [
        {"requirement": key, "blocker": item["blocker"]}
        for key, item in checklist.items()
        if item["status"] != "met"
    ]
    report = {
        "generated_at": datetime.now(UTC).isoformat(),
        "objective": "Codex Ratchet repair-and-sim scaling pass",
        "all_complete": all_complete,
        "completion_status": "complete" if all_complete else "blocked",
        "checklist": checklist,
        "prompt_to_artifact_checklist": prompt_to_artifact_checklist,
        "blockers": blockers,
        "project_status": {
            "truth_green": hygiene.get("truth_green"),
            "controller_green": hygiene.get("controller_green"),
            "migration_green": hygiene.get("migration_green"),
            "lego_tool_reporting_green": hygiene.get("lego_tool_reporting_green"),
            "repo_hygiene_green": hygiene.get("repo_hygiene_green"),
            "overall_green": hygiene.get("overall_green"),
            "source_dirty_count": repo.get("source_dirty_count"),
            "generated_dirty_count": repo.get("generated_dirty_count"),
            "dirty_worktree_count": repo.get("dirty_worktree_count"),
            "lane_count": catalog.get("lane_count"),
            "stage_path_count": catalog.get("stage_path_count"),
            "missing_companion_count": catalog.get("missing_companion_count"),
            "lane_manifest_count": packet_coverage["manifest_count"],
            "lane_packet_count": packet_coverage["packet_count"],
            "lane_stage_plan_count": packet_coverage["stage_plan_count"],
            "ready_lane_packet_count": packet_coverage["ready_packet_count"],
            "ready_lane_stage_plan_count": packet_coverage["ready_stage_plan_count"],
            "lane_packet_groups_match": packet_coverage["group_sets_match"],
            "admitted_count": inventory.get("admitted_count"),
            "admission_repair_count": inventory.get("admission_repair_count"),
            "unlinked_result_json_count": inventory.get("unlinked_result_json_count"),
        },
        "claim_boundaries": {
            "qit_gstack_axis_nonclassical_admission": "not_claimed",
            "riemann_pnt_prime_prediction": "not_claimed",
            "prime_sidecar_ceiling": prime.get("claim_ceiling"),
        },
    }
    return report


def write_markdown(report: dict[str, Any]) -> None:
    lines = [
        "# Rosetta Goal Completion Audit",
        "",
        f"Status: **{report['completion_status']}**",
        "",
        "## Checklist",
    ]
    for key, item in report["checklist"].items():
        lines.append(f"- `{key}`: {item['status']}")
        if item.get("blocker"):
            lines.append(f"  - blocker: {item['blocker']}")
    lines.extend(
        [
            "",
            "## Prompt To Artifact Checklist",
        ]
    )
    for item in report["prompt_to_artifact_checklist"]:
        lines.append(f"- {item['status']}: {item['requirement']}")
        lines.append(f"  - check: {item['command_or_check']}")
        if item.get("blocker"):
            lines.append(f"  - blocker: {item['blocker']}")
    lines.extend(
        [
            "",
            "## Project Status",
            f"- truth/controller/migration/tool reporting: {report['project_status']['truth_green']}/"
            f"{report['project_status']['controller_green']}/"
            f"{report['project_status']['migration_green']}/"
            f"{report['project_status']['lego_tool_reporting_green']}",
            f"- repo hygiene green: {report['project_status']['repo_hygiene_green']}",
            f"- overall green: {report['project_status']['overall_green']}",
            f"- dirty worktree/source/generated: {report['project_status']['dirty_worktree_count']}/"
            f"{report['project_status']['source_dirty_count']}/"
            f"{report['project_status']['generated_dirty_count']}",
            f"- cleanup catalog lanes/stage paths/missing companions: {report['project_status']['lane_count']}/"
            f"{report['project_status']['stage_path_count']}/"
            f"{report['project_status']['missing_companion_count']}",
            f"- cleanup lane manifests/packets/stage plans/ready packets/ready stage plans/groups match: {report['project_status']['lane_manifest_count']}/"
            f"{report['project_status']['lane_packet_count']}/"
            f"{report['project_status']['lane_stage_plan_count']}/"
            f"{report['project_status']['ready_lane_packet_count']}/"
            f"{report['project_status']['ready_lane_stage_plan_count']}/"
            f"{report['project_status']['lane_packet_groups_match']}",
            f"- admitted/admission repair/unlinked results: {report['project_status']['admitted_count']}/"
            f"{report['project_status']['admission_repair_count']}/"
            f"{report['project_status']['unlinked_result_json_count']}",
            "",
            "## Claim Boundaries",
            "- QIT/GStack/axis/nonclassical admission: not claimed",
            "- RH/PNT/prime prediction: not claimed",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report)
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print(f"completion_status={report['completion_status']}")
    print(f"blocker_count={len(report['blockers'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
