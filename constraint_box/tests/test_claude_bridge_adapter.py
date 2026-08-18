from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from constraintbox.claude_bridge_adapter import ClaudeBridgeAdapterError, REQUEST_SCHEMA, run
from constraintbox.mmm_load_gate import MmmLoadError

from test_mmm_load_gate import mmm_bind


def _bridge(path: Path) -> Path:
    path.write_text(
        """from __future__ import annotations
import argparse
import json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('--model'); p.add_argument('--prompt-file'); p.add_argument('--budget')
p.add_argument('--timeout-sec'); p.add_argument('--tools'); p.add_argument('--cwd')
p.add_argument('--out-dir'); p.add_argument('--name'); p.add_argument('--effort')
a = p.parse_args()
out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
output = out / 'output.json'; receipt = out / 'receipt.json'
output.write_text(json.dumps({'ok': True}))
receipt.write_text(json.dumps({'model': 'claude-sonnet-5'}))
print(json.dumps({'parsed': {'models': ['claude-sonnet-5'], 'total_cost_usd': 0.01}, 'output_path': str(output), 'receipt_path': str(receipt)}))
""",
        encoding="utf-8",
    )
    return path


def _request(
    tmp_path: Path,
    *,
    tools: str = "",
    hierarchy: bool = False,
    bind_mmm: bool = True,
    model_observed_allowlist: list[str] | None = ["claude-sonnet-5"],
) -> Path:
    prompt = tmp_path / "prompt.md"
    path = tmp_path / "request.json"
    request = {
                "schema": REQUEST_SCHEMA,
                "request_id": "claude-adapter-test",
                "bridge_path": str(_bridge(tmp_path / "bridge.py")),
                "model": "sonnet",
                "effort": "high",
                "budget_usd": 0.1,
                "timeout_seconds": 30,
                "prompt_path": str(prompt),
                "cwd": str(tmp_path),
                "out_dir": str(tmp_path / "out"),
                "tools": tools,
            }
    if bind_mmm:
        request.update(mmm_bind(prompt, extra="bounded prompt"))
    else:
        prompt.write_text("bounded prompt", encoding="utf-8")
    if hierarchy:
        request.update(
            {
                "hierarchy_bound": True,
                "parent_id": "child-council",
                "wave_id": "wave-1",
                "round": 1,
                "depth": 2,
            }
        )
    if model_observed_allowlist is not None:
        request["model_observed_allowlist"] = model_observed_allowlist
    path.write_text(
        json.dumps(request, sort_keys=True),
        encoding="utf-8",
    )
    return path


def test_write_tools_are_explicit_request_data(tmp_path: Path) -> None:
    receipt = run(_request(tmp_path, tools="Read,Write,Edit"))
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["model_binding_confirmed"] is True
    assert receipt["models_observed"] == ["claude-sonnet-5"]
    assert receipt["model_identity_match_kind"] == "declared_alias"
    assert receipt["alias_resolution_source"] == "invocation.model_observed_allowlist"
    assert receipt["model_observed_values"] == ["claude-sonnet-5"]
    assert receipt["model_observed_allowlist"] == ["claude-sonnet-5"]
    assert receipt["tools_requested"] == "Read,Write,Edit"
    tool_index = receipt["argv"].index("--tools")
    assert receipt["argv"][tool_index + 1] == "Read,Write,Edit"


def test_zip_leaf_hierarchy_is_accepted_and_bound(tmp_path: Path) -> None:
    receipt = run(_request(tmp_path, tools="Read,Write,Edit", hierarchy=True))
    assert {key: receipt[key] for key in ("hierarchy_bound", "parent_id", "wave_id", "round", "depth")} == {
        "hierarchy_bound": True,
        "parent_id": "child-council",
        "wave_id": "wave-1",
        "round": 1,
        "depth": 2,
    }


def test_unbounded_tool_string_is_refused(tmp_path: Path) -> None:
    request = _request(tmp_path)
    body = json.loads(request.read_text(encoding="utf-8"))
    body["tools"] = "Bash,WebSearch"
    request.write_text(json.dumps(body), encoding="utf-8")
    with pytest.raises(ClaudeBridgeAdapterError, match="tools is invalid"):
        run(request)


def test_output_outside_declared_directory_is_hold(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    outside = tmp_path / "outside.md"
    outside.write_text("do not ingest\n", encoding="utf-8")
    stdout = json.dumps(
        {
            "parsed": {"models": ["claude-sonnet-5"]},
            "output_path": str(outside),
            "receipt_path": str(outside),
        }
    ).encode()
    monkeypatch.setattr(
        "constraintbox.claude_bridge_adapter.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=b""),
    )
    receipt = run(request)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CLAUDE_OUTPUT_UNCONTAINED"
    assert receipt["nested_output_sha256"] is None


def test_unbound_model_is_hold(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    output = out_dir / "result.md"
    output.write_text("bounded result\n", encoding="utf-8")
    stdout = json.dumps(
        {"parsed": {"models": ["claude-haiku-4-5"]}, "output_path": str(output)}
    ).encode()
    monkeypatch.setattr(
        "constraintbox.claude_bridge_adapter.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=b""),
    )
    receipt = run(request)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CLAUDE_MODEL_BINDING"
    assert receipt["model_binding_confirmed"] is False


def test_alias_without_allowlist_is_hold(monkeypatch, tmp_path: Path) -> None:
    request = _request(tmp_path, model_observed_allowlist=None)
    out_dir = tmp_path / "out"
    out_dir.mkdir(exist_ok=True)
    output = out_dir / "result.md"
    output.write_text("bounded result\n", encoding="utf-8")
    stdout = json.dumps(
        {"parsed": {"models": ["claude-sonnet-5"]}, "output_path": str(output)}
    ).encode()
    monkeypatch.setattr(
        "constraintbox.claude_bridge_adapter.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=stdout, stderr=b""),
    )
    receipt = run(request)
    assert receipt["disposition"] == "HOLD"
    assert receipt["reason_code"] == "HOLD_CLAUDE_MODEL_BINDING"
    assert receipt["model_identity_match_kind"] == "unverified"


def test_exact_requested_model_does_not_need_allowlist(tmp_path: Path) -> None:
    request = _request(tmp_path, model_observed_allowlist=None)
    body = json.loads(request.read_text(encoding="utf-8"))
    body["model"] = "claude-sonnet-5"
    request.write_text(json.dumps(body), encoding="utf-8")
    receipt = run(request)
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["model_identity_match_kind"] == "exact"
    assert receipt["alias_resolution_source"] is None


@pytest.mark.parametrize(
    "allowlist",
    [[], ["claude-sonnet-5", "claude-sonnet-5"], ["not safe"], [{"model": "x"}]],
)
def test_model_observed_allowlist_is_strictly_validated(
    tmp_path: Path, allowlist: object
) -> None:
    request = _request(tmp_path, model_observed_allowlist=allowlist)  # type: ignore[arg-type]
    with pytest.raises(ClaudeBridgeAdapterError, match="model_observed_allowlist is invalid"):
        run(request)


def test_missing_mmm_refuses_before_spawn(tmp_path: Path, monkeypatch) -> None:
    spawned = {"called": False}

    def _boom(*_args, **_kwargs):
        spawned["called"] = True
        raise AssertionError("LLM spawn must not run without confirmed MMM load")

    monkeypatch.setattr("constraintbox.claude_bridge_adapter.subprocess.run", _boom)
    with pytest.raises(MmmLoadError) as caught:
        run(_request(tmp_path, bind_mmm=False))
    assert caught.value.reason_code == "REFUSE_MMM_LOAD_MISSING"
    assert spawned["called"] is False


def test_confirmed_mmm_is_bound_on_observed_receipt(tmp_path: Path) -> None:
    receipt = run(_request(tmp_path))
    assert receipt["disposition"] == "OBSERVED"
    assert receipt["mmm_load_confirmed"] is True
    assert receipt["mmm_packs"] == ["nominalist", "smt"]
    assert receipt["mmm_sha256"]
