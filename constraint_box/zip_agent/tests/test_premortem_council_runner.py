from __future__ import annotations

from pathlib import Path

import pytest

from constraintbox_zip_agent.premortem_council_runner import write_request


def test_premortem_provider_request_holds_without_declared_controller(tmp_path: Path) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"premortem prompt\n")
    out = tmp_path / "out"
    out.mkdir()
    runner = tmp_path / "runner"
    runner.write_text("fixture runner\n")

    with pytest.raises(RuntimeError, match="HOLD_PROVIDER_CONTROLLER_MISSING"):
        write_request(
            {
                "kind": "grok",
                "model": "fixture-model",
                "runner_path": str(runner),
            },
            "request-1",
            prompt,
            tmp_path,
            out,
            tmp_path / "missing-controller",
        )


def test_premortem_request_uses_explicit_controller_and_no_host_defaults(tmp_path: Path) -> None:
    controller = tmp_path / "controller"
    package = controller / "constraintbox"
    package.mkdir(parents=True)
    source = Path(__file__).resolve().parents[2] / "src" / "constraintbox" / "mmm_load_gate.py"
    (package / "mmm_load_gate.py").write_bytes(source.read_bytes())
    (tmp_path / "mmm").mkdir()
    packs = tmp_path / "mmm" / "packs"
    packs.mkdir()
    (packs / "nominalist.md").write_text("nominalist\n", encoding="utf-8")
    (packs / "smt.md").write_text("smt\n", encoding="utf-8")
    prompt = tmp_path / "prompt.md"
    prompt.write_bytes(b"premortem prompt\n")
    out = tmp_path / "out"
    out.mkdir()
    runner = tmp_path / "runner"
    runner.write_text("fixture runner\n")

    request, _, _ = write_request(
        {
            "kind": "grok",
            "model": "fixture-model",
            "runner_path": str(runner),
        },
        "request-2",
        prompt,
        tmp_path,
        out,
        controller,
    )
    import json

    value = json.loads(request.read_bytes())
    assert value["schema"] == "constraintbox.grok-cli-request.v1"
    assert value["tools"] == ""
    assert "controller_src" not in value
    assert "runner_path" in value
