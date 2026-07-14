#!/usr/bin/env python3
"""Adversarial controls for the full-surface campaign validator."""

from __future__ import annotations

import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any, Callable

from validate_full_surface import sha256_file, validate


def set_pointer(payload: Any, pointer: str, value: Any) -> None:
    tokens = pointer.strip("/").split("/") if pointer != "/" else []
    target = payload
    for token in tokens[:-1]:
        token = token.replace("~1", "/").replace("~0", "~")
        target = target[int(token)] if isinstance(target, list) else target[token]
    final = tokens[-1].replace("~1", "/").replace("~0", "~")
    if isinstance(target, list):
        target[int(final)] = value
    else:
        target[final] = value


def recompute(payload: dict[str, Any]) -> None:
    groups = payload["groups"]
    by_id = {row["id"]: row for row in groups}
    for row in payload["set_coverage"]:
        selected = [by_id[group_id] for group_id in row["group_ids"]]
        execution = all(group["execution_completed"] for group in selected)
        values = [
            observation["observed"] == observation["pass_value"]
            for observation in row["observations"]
        ]
        row["status"] = (
            "execution_blocked"
            if not execution
            else "red"
            if any(value is False for value in values)
            else "partial"
            if row["blockers"]
            else "bounded_green"
            if values and all(value is True for value in values)
            else "not_assessed"
        )
    bounded = [
        row["bounded_pass"]
        for row in groups
        if row["bounded_pass"] is not None
    ]
    sets = payload["set_coverage"]
    inventory = payload["blocked_inventory"]
    summary = {
        "group_count": len(groups),
        "command_count": sum(len(row["commands"]) for row in groups),
        "executed_command_count": sum(
            1
            for row in groups
            for command in row["commands"]
            if command["timed_out"] is False and command["exit_code"] is not None
        ),
        "execution_failed_count": sum(
            row["execution_completed"] is not True for row in groups
        ),
        "bounded_pass_count": sum(value is True for value in bounded),
        "bounded_red_count": sum(value is False for value in bounded),
        "bounded_not_assessed_count": sum(
            row["bounded_pass"] is None for row in groups
        ),
        "blocked_inventory_count": len(inventory),
        "set_count": len(sets),
        "set_evidence_complete_count": sum(
            row["status"] in {"bounded_green", "red"} for row in sets
        ),
        "set_bounded_green_count": sum(
            row["status"] == "bounded_green" for row in sets
        ),
        "set_red_count": sum(row["status"] == "red" for row in sets),
        "set_partial_count": sum(row["status"] == "partial" for row in sets),
        "set_execution_blocked_count": sum(
            row["status"] == "execution_blocked" for row in sets
        ),
    }
    payload["summary"] = summary
    payload["runner_all_completed"] = (
        summary["execution_failed_count"] == 0
        and summary["executed_command_count"] == summary["command_count"]
    )
    payload["bounded_observations_all_pass"] = (
        bool(bounded)
        and all(bounded)
        and summary["set_partial_count"] == 0
        and summary["set_execution_blocked_count"] == 0
        and summary["set_red_count"] == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("envelope", type=Path)
    args = parser.parse_args()
    baseline = json.loads(args.envelope.read_text(encoding="utf-8"))
    baseline_errors = validate(baseline, envelope_path=args.envelope)
    results: dict[str, Any] = {
        "baseline_accepts": not baseline_errors,
        "baseline_errors": baseline_errors,
        "negative_controls": {},
    }

    controls: list[tuple[str, Callable[[dict[str, Any]], None]]] = [
        ("promotion_flip", lambda row: row.__setitem__("promotion_allowed", True)),
        ("partial_promotion_flip", lambda row: row.__setitem__("partial_promotion_allowed", True)),
        ("partial_promotion_alias", lambda row: row.__setitem__("partial_promotion_status", "provisional")),
        ("provider_as_evidence", lambda row: row.__setitem__("provider_advisory_is_evidence", True)),
        ("projection_only", lambda row: row.__setitem__("projection_only", True)),
        ("lev_commit_field_substitution", lambda row: row["lev_executor"].__setitem__("git_commit", "ab211e8c83bd323b8eb2f4dabf1d80bb27a5ebcd")),
        ("lev_nonexistent_commit", lambda row: row["lev_executor"].__setitem__("git_commit", "0" * 40)),
        ("lev_executor_tree_hash_mismatch", lambda row: row["lev_executor"].__setitem__("git_tree", "0" * 40)),
        ("lev_suite_source_hash_mismatch", lambda row: row["lev_executor"]["suite_bindings"][0].__setitem__("sha256", "0" * 64)),
        ("replayed_source_commit", lambda row: row["source"].__setitem__("git_commit", "0" * 40)),
        ("source_hash_mismatch", lambda row: row["groups"][0]["sources"][0].__setitem__("sha256", "0" * 64)),
        ("artifact_hash_mismatch", lambda row: row["groups"][0]["artifacts"][0].__setitem__("sha256", "0" * 64)),
        ("evidence_observed_fabrication", lambda row: row["groups"][0]["science_evidence"].__setitem__("observed", "fabricated")),
        ("evidence_pass_value_rewrite", lambda row: row["groups"][0]["science_evidence"].__setitem__("pass_value", row["groups"][0]["science_evidence"]["observed"])),
        ("archive_member_hash_mismatch", lambda row: row["archive"]["members"][0].__setitem__("sha256", "0" * 64)),
        ("required_artifact_erasure", lambda row: row["groups"][0].__setitem__("required_artifact_count", 0)),
        ("set_blocker_erasure", lambda row: row["set_coverage"][4].__setitem__("blockers", [])),
        ("set_lane_observation_fabrication", lambda row: row["set_coverage"][3]["observations"][0].__setitem__("observed", False)),
        ("set_lane_pointer_rewrite", lambda row: row["set_coverage"][3]["observations"][0].__setitem__("json_pointer", "/all_pass")),
        ("unknown_top_level_field", lambda row: row.__setitem__("authority_override", True)),
        ("zero_execution", lambda row: row.__setitem__("groups", [])),
    ]
    for name, mutate in controls:
        candidate = copy.deepcopy(baseline)
        mutate(candidate)
        errors = validate(candidate)
        results["negative_controls"][name] = {
            "rejected": bool(errors),
            "errors": errors[:8],
        }

    advisory = next(
        (row for row in baseline["groups"] if row["kind"] == "provider_advisory_validation"),
        None,
    )
    if advisory is not None:
        candidate = copy.deepcopy(baseline)
        target = next(
            row for row in candidate["groups"] if row["id"] == advisory["id"]
        )
        target["provider_as_evidence"] = True
        provider_errors = validate(candidate)
        results["negative_controls"]["provider_group_alias"] = {
            "rejected": bool(provider_errors),
            "errors": provider_errors[:8],
        }

    def correction_artifact_control(
        name: str,
        mutate: Callable[[dict[str, Any]], None],
    ) -> None:
        candidate = copy.deepcopy(baseline)
        target = next(
            row for row in candidate["groups"]
            if row["id"] == "julia_correction_probes"
        )
        original_path = Path(target["science_evidence"]["artifact_path"])
        with tempfile.TemporaryDirectory(
            prefix=f"{name}-",
            dir=Path(candidate["artifact_root"]),
        ) as temp:
            mutated_path = Path(temp) / original_path.name
            shutil.copy2(original_path, mutated_path)
            receipt = json.loads(mutated_path.read_text(encoding="utf-8"))
            mutate(receipt)
            mutated_path.write_text(
                json.dumps(receipt, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            old_path = target["science_evidence"]["artifact_path"]
            for artifact in target["artifacts"]:
                if artifact["path"] == old_path:
                    artifact["path"] = str(mutated_path.resolve())
                    artifact["sha256"] = sha256_file(mutated_path)
            target["science_evidence"]["artifact_path"] = str(mutated_path.resolve())
            for set_row in candidate["set_coverage"]:
                for observation in set_row["observations"]:
                    if observation["artifact_path"] == old_path:
                        observation["artifact_path"] = str(mutated_path.resolve())
            mutation_errors = validate(candidate)
        results["negative_controls"][name] = {
            "rejected": bool(mutation_errors),
            "errors": mutation_errors[:8],
        }

    correction_artifact_control(
        "correction_observation_fabrication",
        lambda receipt: receipt["checks"]["albert_component_norm"]["observed"].__setitem__(
            "component_norm", -1.0
        ),
    )

    def substitute_correction_project(receipt: dict[str, Any]) -> None:
        project = Path(
            "/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier/Project.toml"
        )
        manifest = project.with_name("Manifest.toml")
        receipt["project"]["project_toml_path"] = str(project)
        receipt["project"]["project_toml_sha256"] = sha256_file(project)
        receipt["project"]["manifest_toml_path"] = str(manifest)
        receipt["project"]["manifest_toml_sha256"] = sha256_file(manifest)
        receipt["runtime"]["active_project"] = str(project)
        receipt["command"][2] = f"--project={project.parent}"

    correction_artifact_control(
        "correction_project_substitution",
        substitute_correction_project,
    )

    def realign_correction_booleans(receipt: dict[str, Any]) -> None:
        check = receipt["checks"]["albert_component_norm"]
        check["observed"]["component_norm"] = 1.0
        check["observed"]["synthetic_component_norm"] = 0.0
        check["observed"]["candidate_error"] = ""
        check["candidate_failure_reproduced"] = True
        check["corrected_pass"] = True
        check["must_fail_control_fired"] = True
        receipt["all_pass"] = True

    correction_artifact_control(
        "correction_boolean_realignment",
        realign_correction_booleans,
    )

    green = next(
        row
        for row in baseline["groups"]
        if row["bounded_pass"] is True
        and row["science_evidence"]["kind"] == "artifact_json"
    )
    demoted = copy.deepcopy(baseline)
    demoted_group = next(row for row in demoted["groups"] if row["id"] == green["id"])
    original_path = Path(demoted_group["science_evidence"]["artifact_path"])
    with tempfile.TemporaryDirectory(
        prefix="honest-demotion-",
        dir=Path(demoted["artifact_root"]),
    ) as temp:
        demoted_path = Path(temp) / original_path.name
        shutil.copy2(original_path, demoted_path)
        artifact_payload = json.loads(demoted_path.read_text(encoding="utf-8"))
        pass_value = demoted_group["science_evidence"]["pass_value"]
        alternate = not pass_value if isinstance(pass_value, bool) else pass_value + 1
        set_pointer(
            artifact_payload,
            demoted_group["science_evidence"]["json_pointer"],
            alternate,
        )
        demoted_path.write_text(
            json.dumps(artifact_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        old_path = demoted_group["science_evidence"]["artifact_path"]
        for artifact in demoted_group["artifacts"]:
            if artifact["path"] == old_path:
                artifact["path"] = str(demoted_path.resolve())
                artifact["sha256"] = sha256_file(demoted_path)
        demoted_group["science_evidence"]["artifact_path"] = str(demoted_path.resolve())
        demoted_group["science_evidence"]["observed"] = alternate
        for set_row in demoted["set_coverage"]:
            for observation in set_row["observations"]:
                if observation["artifact_path"] == old_path:
                    observation["artifact_path"] = str(demoted_path.resolve())
        demoted_group["bounded_pass"] = False
        demoted_group["status"] = "bounded_red"
        recompute(demoted)
        demotion_errors = validate(demoted)
    results["honest_demotion"] = {
        "group": green["id"],
        "accepted": not demotion_errors,
        "errors": demotion_errors,
    }

    all_negative_rejected = all(
        row["rejected"] for row in results["negative_controls"].values()
    )
    results["all_pass"] = (
        results["baseline_accepts"]
        and all_negative_rejected
        and results["honest_demotion"]["accepted"]
    )
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
