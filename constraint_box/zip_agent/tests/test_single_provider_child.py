from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path

import pytest

import constraintbox_zip_agent.md_agent_roster as roster_module
from constraintbox_zip_agent.protocol import ZipJobRefusal, deterministic_zip
from constraintbox_zip_agent.runtime import execute_packet
from constraintbox_zip_agent.single_provider_child import (
    BUILD_SCHEMA,
    MARKER,
    SingleProviderChildBuild,
    build_single_provider_child_packet,
    load_build_request,
    validate_single_provider_child_return,
)


FIXTURE = r'''
import hashlib
import json
from pathlib import Path

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

tool = json.loads(Path("output/tool_evidence.json").read_text())["canonical_sha256"]
lines = [
    "CB_SINGLE_PROVIDER_CHILD_RESULT_V1",
    "status: OBSERVATION",
    "evidence: fixture worker wrote one declared file",
    "limits: fixture provider only",
    "next: validate nested return",
    "skill-token: " + digest("SKILLS/task.md"),
]
for path in sorted(Path("MMMS").glob("*.md")):
    lines.append("mmm-token: " + digest(path))
lines.append(tool)
Path("output").mkdir(exist_ok=True)
Path("output/worker.md").write_text("\n".join(lines) + "\n")
'''


def _source_files(tmp_path: Path) -> dict[str, Path]:
    paths = {
        "owner": tmp_path / "owner.md",
        "agent": tmp_path / "agent.md",
        "skill": tmp_path / "skill.md",
        "mmm_a": tmp_path / "mmm_a.md",
        "mmm_b": tmp_path / "mmm_b.md",
    }
    for key, path in paths.items():
        path.write_text(f"{key} exact bytes\n", encoding="utf-8")
    return paths


def _request(tmp_path: Path) -> SingleProviderChildBuild:
    paths = _source_files(tmp_path)
    return SingleProviderChildBuild.model_validate(
        {
            "schema": BUILD_SCHEMA,
            "parent_job_id": "single-provider-proof",
            "run_id": "single-provider-proof-run",
            "wave_id": "single-provider-proof-wave",
            "round": 1,
            "seed": 8162026,
            "timeout_seconds": 30,
            "max_attempts": 1,
            "owner_prompt_path": str(paths["owner"]),
            "agent_instruction_path": str(paths["agent"]),
            "skill_path": str(paths["skill"]),
            "mmm_paths": [str(paths["mmm_a"]), str(paths["mmm_b"])],
            "route": {"provider": "fixture-subprocess", "fixture_script": FIXTURE},
            "required_fragments": [],
            "forbidden_fragments": ["promotion_allowed: true"],
        }
    )


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}


def test_build_is_deterministic_and_model_route_is_run_data(tmp_path: Path) -> None:
    request = _request(tmp_path)
    first = build_single_provider_child_packet(request)
    second = build_single_provider_child_packet(request)
    assert first.packet_bytes == second.packet_bytes
    assert first.packet_sha256 == hashlib.sha256(first.packet_bytes).hexdigest()
    entries = _entries(first.packet_bytes)
    assert "children/md-agent-roster.zip" in entries
    child = _entries(entries["children/md-agent-roster.zip"])
    roster = json.loads(child["inputs/roster.json"])
    assert roster["parent_id"] == "single-provider-proof"
    assert roster["wave_id"] == "single-provider-proof-wave"
    assert roster["depth"] == 1
    assert roster["agents"][0]["provider"] == "fixture-subprocess"
    assert roster["agents"][0]["mmm_paths"] == ["MMMS/00.md", "MMMS/01.md"]


def test_fixture_child_executes_and_both_returns_verify(tmp_path: Path) -> None:
    built = build_single_provider_child_packet(_request(tmp_path))
    result = execute_packet(built.packet_bytes)
    verified = validate_single_provider_child_return(
        built.packet_bytes, result.return_zip_bytes
    )
    text = verified.worker_output.decode("utf-8")
    assert MARKER in text
    assert verified.summary["provider"] == "fixture-subprocess"
    assert verified.summary["model_binding_confirmed"] is False
    assert verified.summary["accepted_attempt"] == 1
    assert verified.roster_receipt["accepted_agent_ids"] == ["worker"]


def test_provider_evidence_receives_post_binding_prompt_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_argv = roster_module._argv
    captured: dict[str, bytes] = {}

    def binding_argv(*args, **kwargs):
        prompt_path = args[2]
        result = original_argv(*args, **kwargs)
        prompt_path.write_bytes(b"BOUND-MMM-HEADER\n" + prompt_path.read_bytes())
        return result

    def capture_evidence(**kwargs):
        captured["prompt"] = kwargs["prompt"]
        return {
            "provider_request_id": None,
            "model_observed": ["fixture-observed"],
            "model_binding_confirmed": False,
            "identity_source": "fixture",
            "composed_prompt_sha256": hashlib.sha256(kwargs["prompt"]).hexdigest(),
            "provider_source_receipt_sha256": None,
            "provider_source_receipt": None,
        }

    monkeypatch.setattr(roster_module, "_argv", binding_argv)
    monkeypatch.setattr(roster_module, "_provider_evidence", capture_evidence)
    built = build_single_provider_child_packet(_request(tmp_path))
    execute_packet(built.packet_bytes)
    assert captured["prompt"].startswith(b"BOUND-MMM-HEADER\n")


def test_extra_contract_field_is_refused(tmp_path: Path) -> None:
    request = _request(tmp_path)
    raw = request.model_dump(mode="json", by_alias=True)
    raw["invented_authority"] = True
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps(raw), encoding="utf-8")
    with pytest.raises(ZipJobRefusal, match="REFUSE_SINGLE_PROVIDER_BUILD"):
        load_build_request(contract)


def test_tampered_child_packet_is_refused_without_parent_return(tmp_path: Path) -> None:
    built = build_single_provider_child_packet(_request(tmp_path))
    entries = _entries(built.packet_bytes)
    child = bytearray(entries["children/md-agent-roster.zip"])
    child[-1] ^= 1
    entries["children/md-agent-roster.zip"] = bytes(child)
    tampered = deterministic_zip(entries)
    with pytest.raises(ZipJobRefusal):
        execute_packet(tampered)


def test_worker_output_tamper_breaks_nested_return_verification(tmp_path: Path) -> None:
    built = build_single_provider_child_packet(_request(tmp_path))
    result = execute_packet(built.packet_bytes)
    parent_entries = _entries(result.return_zip_bytes)
    child_entries = _entries(parent_entries["output/child.return.zip"])
    child_entries["output/worker.md"] += b"tamper\n"
    parent_entries["output/child.return.zip"] = deterministic_zip(child_entries)
    tampered_parent_return = deterministic_zip(parent_entries)
    with pytest.raises(ZipJobRefusal):
        validate_single_provider_child_return(built.packet_bytes, tampered_parent_return)
