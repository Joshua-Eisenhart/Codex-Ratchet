from __future__ import annotations

import io
import importlib.util
import json
import zipfile
from pathlib import Path

import pytest

from constraintbox_zip_agent.cli import main
from constraintbox_zip_agent.failure_wave import (
    _manifest,
    _task,
    build_demo_packet,
    build_failure_wave_packet,
)
from constraintbox_zip_agent.protocol import MANIFEST_PATH, ZipJobRefusal, build_packet, validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {info.filename: archive.read(info) for info in archive.infolist() if not info.is_dir()}


def test_failure_wave_is_three_child_zips_plus_compile() -> None:
    wave = build_failure_wave_packet(build_demo_packet())
    entries = _entries(wave)
    assert sorted(path for path in entries if path.startswith("children/")) == [
        "children/authority-collapse.zip",
        "children/counterexample.zip",
        "children/structure.zip",
    ]
    result = execute_packet(wave)
    validate_return_zip(result.return_zip_bytes)
    returned = _entries(result.return_zip_bytes)
    report = json.loads(returned["output/failure_wave.json"])
    assert report["verdict"] == "PASS"
    assert report["members_complete"] is True
    assert set(report["member_status"]) == {"structure", "counterexample", "authority-collapse"}


def test_child_return_zips_are_retained_as_parent_outputs() -> None:
    result = execute_packet(build_failure_wave_packet(build_demo_packet()))
    returned = _entries(result.return_zip_bytes)
    child_returns = sorted(path for path in returned if path.endswith(".return.zip"))
    assert len(child_returns) == 3
    for path in child_returns:
        validate_return_zip(returned[path])


def test_existing_target_return_is_verified_without_target_reexecution() -> None:
    target = build_demo_packet()
    target_return = execute_packet(target).return_zip_bytes
    result = execute_packet(
        build_failure_wave_packet(target, target_return=target_return)
    )
    returned = _entries(result.return_zip_bytes)
    authority_return = _entries(returned["output/authority-collapse.return.zip"])
    report = json.loads(authority_return["output/authority-collapse.json"])
    assert report["mode"] == "verify_existing_return_without_execution"
    assert report["existing_return_consumed"] is True
    assert report["checks"] == {
        "input_identity_bound": True,
        "return_integrity_bound": True,
        "runtime_source_current": True,
        "unknown_operation_refused": True,
    }


def test_existing_target_return_with_wrong_input_is_refused() -> None:
    target = build_demo_packet()
    other = build_demo_packet()[:-1] + b"x"
    with pytest.raises(ZipJobRefusal):
        execute_packet(
            build_failure_wave_packet(
                target,
                target_return=other,
            )
        )


def test_model_bearing_target_without_return_is_refused() -> None:
    from constraintbox_zip_agent.md_agent_roster import build_md_agent_roster_packet

    target = build_md_agent_roster_packet(
        roster={
            "schema": "constraintbox.md-agent-roster.v1",
            "run_id": "wave-guard",
            "seed": 1,
            "required_marker": "X",
            "max_attempts": 1,
            "timeout_seconds": 5,
            "max_workers": 1,
            "shared_paths": ["input/OBJECT.md", "REFERENCES/mmm/voice.md"],
            "agents": [
                {
                    "agent_id": "one",
                    "agent_path": "AGENTS/one.md",
                    "output_path": "output/one.md",
                    "provider": "fixture-subprocess",
                    "model_requested": "fixture-model",
                    "fixture_script": "raise SystemExit(1)",
                    "mmm_paths": ["REFERENCES/mmm/voice.md"],
                    "skill_paths": ["SKILLS/write-finding.md"],
                    "context_paths": ["input/OBJECT.md"],
                    "required_fragments": ["finding:"],
                    "max_output_bytes": 4096,
                }
            ],
        },
        files={
            "AGENTS/one.md": b"role: one\n",
            "input/OBJECT.md": b"x\n",
            "REFERENCES/mmm/voice.md": b"v\n",
            "SKILLS/write-finding.md": b"s\n",
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(build_failure_wave_packet(target))
    assert caught.value.reason_code == "REFUSE_FAILURE_WAVE_REEXECUTES_MODELS"


def test_root_depth_limit_is_enforced() -> None:
    wave = build_failure_wave_packet(build_demo_packet())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(wave, _root_depth_limit=0)
    assert caught.value.reason_code == "REFUSE_CHILD_DEPTH_LIMIT"


def test_nested_child_cannot_expand_its_own_depth_ceiling() -> None:
    grandchild = build_demo_packet()
    child_task = "tasks/00_child.task.json"
    child = build_packet(
        _manifest(
            job_id="zero-depth-child",
            task_paths=[child_task],
            outputs=["output/grandchild.return.zip"],
            operations=["run_child_zip_v1"],
            child_ids=["zip-agent-demo"],
            depth=0,
        ),
        {
            "00_RUN_ME_FIRST.md": b"child",
            "children/grandchild.zip": grandchild,
            child_task: _task(
                task_id="run-grandchild",
                sequence=0,
                operation="run_child_zip_v1",
                inputs=["children/grandchild.zip"],
                outputs=["output/grandchild.return.zip"],
            ),
        },
    )
    outer_task = "tasks/00_outer.task.json"
    outer = build_packet(
        _manifest(
            job_id="outer-parent",
            task_paths=[outer_task],
            outputs=["output/child.return.zip"],
            operations=["run_child_zip_v1"],
            child_ids=["zero-depth-child"],
            depth=4,
        ),
        {
            "00_RUN_ME_FIRST.md": b"outer",
            "children/child.zip": child,
            outer_task: _task(
                task_id="run-child",
                sequence=0,
                operation="run_child_zip_v1",
                inputs=["children/child.zip"],
                outputs=["output/child.return.zip"],
            ),
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(outer)
    assert caught.value.reason_code == "REFUSE_CHILD_DEPTH_LIMIT"


def test_failure_wave_replays_byte_identically() -> None:
    wave = build_failure_wave_packet(build_demo_packet())
    assert execute_packet(wave).return_zip_bytes == execute_packet(wave).return_zip_bytes


def test_failure_wave_definition_and_child_skills_validate() -> None:
    root = Path(__file__).resolve().parents[1]
    script = root / "skills" / "zip-failure-wave" / "scripts" / "validate_wave.py"
    spec = importlib.util.spec_from_file_location("zip_wave_validator", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate(root / "skills" / "zip-failure-wave" / "wave.json") == []


def test_unused_child_authority_is_refused() -> None:
    wave = build_failure_wave_packet(build_demo_packet())
    entries = _entries(wave)
    manifest = json.loads(entries.pop(MANIFEST_PATH))
    manifest.pop("file_sha256_registry")
    manifest["allowed_child_job_ids"].append("unused-child")
    changed = build_packet(manifest, entries)
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(changed)
    assert caught.value.reason_code == "REFUSE_CHILD_DECLARATION_MISMATCH"


def test_wave_packet_and_return_path_cannot_alias(tmp_path: Path, capsys) -> None:
    target = tmp_path / "target.zip"
    shared = tmp_path / "shared.zip"
    target.write_bytes(build_demo_packet())
    rc = main(
        [
            "failure-wave",
            "--target",
            str(target),
            "--wave-packet",
            str(shared),
            "--return-zip",
            str(shared),
        ]
    )
    assert rc == 2
    assert not shared.exists()
    assert json.loads(capsys.readouterr().out)["disposition"] == "REFUSE_OUTPUT_ALIAS"
