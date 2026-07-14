import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = (
    ROOT
    / "system_v5/codex_skills/codex-ratchet-tool-status-auditor/scripts/validate_skills_used.py"
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_receipt(tmp_path: Path, *, executable: bool = True) -> tuple[dict, dict[str, Path]]:
    skill_root = tmp_path / "skills" / "example-skill"
    scripts = skill_root / "scripts"
    scripts.mkdir(parents=True)
    skill_file = skill_root / "SKILL.md"
    script_file = scripts / "check.py"
    artifact = tmp_path / "results" / "check.json"
    artifact.parent.mkdir()
    skill_file.write_text("---\nname: example-skill\n---\n", encoding="utf-8")
    script_file.write_text("print('checked')\n", encoding="utf-8")
    artifact.write_text('{"all_pass": true}\n', encoding="utf-8")

    command = {
        "id": "validate-example",
        "argv": [sys.executable, str(script_file)],
        "exit_code": 0,
        "output_artifacts": [{"path": str(artifact), "sha256": sha256_file(artifact)}],
    }
    skills_used = [
        {
            "path": str(skill_file),
            "sha256": sha256_file(skill_file),
            "role": "guidance",
            "affected_commands": ["validate-example"],
        }
    ]
    if executable:
        skills_used.append(
            {
                "path": str(script_file),
                "sha256": sha256_file(script_file),
                "role": "executable_validator",
                "affected_commands": ["validate-example"],
            }
        )
    return (
        {
            "schema": "codex-ratchet-skills-used-v1",
            "receipt_id": "example-receipt",
            "commands": [command],
            "skills_used": skills_used,
        },
        {"skill": skill_file, "script": script_file, "artifact": artifact},
    )


def run_validator(tmp_path: Path, payload: dict) -> subprocess.CompletedProcess[str]:
    receipt = tmp_path / "receipt.json"
    receipt.write_text(json.dumps(payload), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(receipt), "--repo-root", str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_blocked(tmp_path: Path, payload: dict, expected: str) -> None:
    result = run_validator(tmp_path, payload)
    assert result.returncode == 1, result.stdout + result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["all_pass"] is False
    assert verdict["max_skill_provenance_level"] == "BLOCKED"
    assert any(expected in error for error in verdict["errors"]), verdict


def test_guidance_only_receipt_is_hash_bound_and_capped_at_l2(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path, executable=False)

    result = run_validator(tmp_path, payload)

    assert result.returncode == 0, result.stdout + result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["all_pass"] is True
    assert verdict["counts"]["guidance"] == 1
    assert verdict["max_skill_provenance_level"] == "L2"
    assert "no executable" in verdict["claim_ceiling"]


def test_executable_receipt_is_only_l3_eligible_without_external_runner(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)

    result = run_validator(tmp_path, payload)

    assert result.returncode == 0, result.stdout + result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["all_pass"] is True
    assert verdict["counts"]["executable_validator"] == 1
    assert verdict["max_skill_provenance_level"] == "L2"
    assert verdict["l3_eligible"] is True
    assert verdict["external_runner_receipt_required"] is True
    assert "self-reported" in verdict["claim_ceiling"]


def test_self_reported_exit_and_artifact_realignment_cannot_forge_l3(tmp_path: Path) -> None:
    payload, paths = build_receipt(tmp_path)
    paths["script"].write_text("raise SystemExit(9)\n", encoding="utf-8")
    paths["artifact"].write_text('{"forged": "green"}\n', encoding="utf-8")
    payload["skills_used"][1]["sha256"] = sha256_file(paths["script"])
    payload["commands"][0]["exit_code"] = 0
    payload["commands"][0]["output_artifacts"][0]["sha256"] = sha256_file(paths["artifact"])

    result = run_validator(tmp_path, payload)

    assert result.returncode == 0, result.stdout + result.stderr
    verdict = json.loads(result.stdout)
    assert verdict["all_pass"] is True
    assert verdict["max_skill_provenance_level"] == "L2"
    assert verdict["l3_eligible"] is True
    assert verdict["external_runner_receipt_required"] is True


def test_rejects_extra_skill_entry_key(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    payload["skills_used"][0]["self_reported_pass"] = True

    assert_blocked(tmp_path, payload, "keys must be exact")


def test_rejects_stale_skill_hash(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    payload["skills_used"][0]["sha256"] = "0" * 64

    assert_blocked(tmp_path, payload, "does not match current bytes")


def test_rejects_path_escape_without_allow_root(tmp_path: Path) -> None:
    payload, paths = build_receipt(tmp_path)
    outside = tmp_path.parent / f"{tmp_path.name}-outside-SKILL.md"
    outside.write_text("outside\n", encoding="utf-8")
    payload["skills_used"][0]["path"] = str(outside)
    payload["skills_used"][0]["sha256"] = sha256_file(outside)

    try:
        assert_blocked(tmp_path, payload, "escapes the allowed roots")
    finally:
        outside.unlink()
    assert paths["skill"].is_file()


def test_rejects_guidance_disguised_as_executable_file(tmp_path: Path) -> None:
    payload, paths = build_receipt(tmp_path, executable=False)
    payload["skills_used"][0]["path"] = str(paths["script"])
    payload["skills_used"][0]["sha256"] = sha256_file(paths["script"])

    assert_blocked(tmp_path, payload, "must point to SKILL.md")


def test_rejects_executable_without_matching_guidance_entry(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    payload["skills_used"] = [payload["skills_used"][1]]

    assert_blocked(tmp_path, payload, "requires a matching guidance entry")


def test_rejects_decorative_executable_path_mention(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    payload["commands"][0]["argv"] = [sys.executable, "different_script.py"]

    assert_blocked(tmp_path, payload, "does not invoke the exact executable path")


def test_rejects_nonzero_affected_command(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    payload["commands"][0]["exit_code"] = 2

    assert_blocked(tmp_path, payload, "references nonzero command")


def test_rejects_executable_without_hash_bound_output(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    payload["commands"][0]["output_artifacts"] = []

    assert_blocked(tmp_path, payload, "has no hash-bound output artifact")


def test_rejects_unknown_or_duplicate_command_references(tmp_path: Path) -> None:
    payload, _ = build_receipt(tmp_path)
    unknown = deepcopy(payload)
    unknown["skills_used"][1]["affected_commands"] = ["missing"]
    duplicate = deepcopy(payload)
    duplicate["skills_used"][1]["affected_commands"] = ["validate-example", "validate-example"]

    assert_blocked(tmp_path, unknown, "references unknown command")
    assert_blocked(tmp_path, duplicate, "must not contain duplicates")
