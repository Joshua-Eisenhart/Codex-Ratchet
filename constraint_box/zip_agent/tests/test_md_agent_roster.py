from __future__ import annotations

import io
import json
import zipfile

import pytest

from constraintbox_zip_agent.md_agent_roster import (
    _provider_env,
    _provider_evidence,
    build_md_agent_roster_packet,
)
from constraintbox_zip_agent.protocol import ZipJobRefusal, sha256_bytes, validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet

MARKER = "ZIP_MD_AGENT_LIVE"


def _script(body: str) -> str:
    return (
        "from pathlib import Path\n"
        "import json, os, hashlib\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/provider_evidence.json').write_text(\n"
        "    json.dumps({'schema':'constraintbox.fixture-provider-evidence.v1',"
        "'disposition':'OBSERVED','model_observed':'fixture-observed'}) + '\\n',\n"
        "    encoding='utf-8',\n"
        ")\n"
        "token = json.loads(Path('output/tool_evidence.json').read_text(encoding='utf-8'))['canonical_sha256']\n"
        + body
        + "\n"
    )


def _roster(*agents: dict) -> dict:
    return {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": "md-roster-unit",
        "seed": 42042,
        "required_marker": MARKER,
        "max_attempts": 2,
        "timeout_seconds": 30,
        "max_workers": 8,
        "shared_paths": ["input/OBJECT.md", "REFERENCES/mmm/voice.md"],
        "agents": list(agents),
    }


def _files() -> dict[str, bytes]:
    return {
        "AGENTS/one.md": b"role: one\noutput: output/one.md\nWrite the marker.\n",
        "AGENTS/two.md": b"role: two\noutput: output/two.md\nWrite the marker.\n",
        "input/OBJECT.md": b"Write the declared output file.\n",
        "REFERENCES/mmm/voice.md": b"plain particulars only\n",
        "SKILLS/write-finding.md": b"write only the declared markdown output\n",
    }


def _agent(agent_id: str, script: str, model: str = "fixture-model") -> dict:
    return {
        "agent_id": agent_id,
        "agent_path": f"AGENTS/{agent_id}.md",
        "output_path": f"output/{agent_id}.md",
        "provider": "fixture-subprocess",
        "model_requested": model,
        "fixture_script": _script(script),
        "mmm_paths": ["REFERENCES/mmm/voice.md"],
        "skill_paths": ["SKILLS/write-finding.md"],
        "context_paths": ["input/OBJECT.md"],
        "required_fragments": ["finding:"],
        "max_output_bytes": 4096,
    }


def _packet(*scripts: str) -> bytes:
    ids = ("one", "two")
    agents = [_agent(agent_id, script) for agent_id, script in zip(ids, scripts, strict=True)]
    return build_md_agent_roster_packet(roster=_roster(*agents), files=_files())


def _hierarchy_roster(*agents: dict, **binding: object) -> dict:
    roster = _roster(*agents)
    roster.update(
        {
            "parent_id": "parent-run",
            "wave_id": "wave-7",
            "round": 3,
            "depth": 2,
            **binding,
        }
    )
    return roster


def _receipt_for(roster: dict) -> dict:
    packet = build_md_agent_roster_packet(roster=roster, files=_files())
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        return json.loads(archive.read("output/roster_receipt.json"))


def _ok(agent_id: str) -> str:
    return (
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        f"Path('output/{agent_id}.md').write_text("
        f"'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')"
    )


def test_two_md_agents_write_declared_files() -> None:
    packet = _packet(_ok("one"), _ok("two"))
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        one = archive.read("output/one.md").decode("utf-8")
        two = archive.read("output/two.md").decode("utf-8")
        assert one.startswith("finding: ZIP_MD_AGENT_LIVE")
        assert two.startswith("finding: ZIP_MD_AGENT_LIVE")
        assert "tool-token:" in one and "tool-token:" in two
        receipt = archive.read("output/roster_receipt.json")
    assert b'"accepted_agent_ids":["one","two"]' in receipt.replace(b" ", b"")
    assert result.return_zip_bytes == execute_packet(packet).return_zip_bytes
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        surface = json.loads(archive.read("output/roster_receipt.json"))
        assert archive.read("output/tool_evidence.json")
        assert all(row["model_observed"] == "fixture-observed" for row in surface["agents"])
        assert all(row["identity_source"] == "fixture" for row in surface["agents"])
        assert all(row["tool_evidence_sha256"] for row in surface["agents"])
        assert surface["hierarchy_bound"] is False


def test_hierarchy_bound_depth_two_receipt_binds_every_row() -> None:
    receipt = _receipt_for(_hierarchy_roster(_agent("one", _ok("one"))))

    assert receipt["hierarchy_bound"] is True
    assert receipt["parent_id"] == "parent-run"
    assert receipt["wave_id"] == "wave-7"
    assert receipt["round"] == 3
    assert receipt["depth"] == 2
    for agent in receipt["agents"]:
        assert agent["hierarchy_bound"] is True
        assert agent["parent_id"] == receipt["parent_id"]
        assert agent["wave_id"] == receipt["wave_id"]
        assert agent["round"] == receipt["round"]
        assert agent["depth"] == receipt["depth"]
        for attempt in agent["attempts"]:
            assert attempt["hierarchy_bound"] is True
            assert attempt["parent_id"] == receipt["parent_id"]
            assert attempt["wave_id"] == receipt["wave_id"]
            assert attempt["round"] == receipt["round"]
            assert attempt["depth"] == receipt["depth"]


@pytest.mark.parametrize(
    "binding",
    [
        {"parent_id": "parent-run", "wave_id": "wave-7", "round": 3},
        {"parent_id": None, "wave_id": "wave-7", "round": 3, "depth": 2},
        {"parent_id": "parent-run", "wave_id": "wave-7", "round": -1, "depth": 2},
        {"parent_id": "parent-run", "wave_id": "wave-7", "round": 3, "depth": 9},
    ],
)
def test_hierarchy_binding_missing_or_invalid_fields_is_refused(binding: dict[str, object]) -> None:
    roster = _roster(_agent("one", _ok("one")))
    roster.update(binding)
    with pytest.raises(ZipJobRefusal) as caught:
        build_md_agent_roster_packet(roster=roster, files=_files())
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_SCHEMA"


def test_hierarchy_parent_and_depth_change_provider_request_identity() -> None:
    parent = _receipt_for(_hierarchy_roster(_agent("one", _ok("one")), parent_id="parent-a"))
    other_parent = _receipt_for(
        _hierarchy_roster(_agent("one", _ok("one")), parent_id="parent-b")
    )
    other_depth = _receipt_for(
        _hierarchy_roster(_agent("one", _ok("one")), depth=3)
    )

    parent_request_id = parent["agents"][0]["attempts"][0]["provider_request_id"]
    assert parent_request_id != other_parent["agents"][0]["attempts"][0]["provider_request_id"]
    assert parent_request_id != other_depth["agents"][0]["attempts"][0]["provider_request_id"]


def test_failed_first_attempt_retries_then_accepts() -> None:
    retry = (
        "if os.environ.get('CB_ZIP_ATTEMPT') == '1':\n"
        "    raise SystemExit(1)\n"
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')"
    )
    packet = _packet(retry, _ok("two"))
    result = execute_packet(packet)
    validate_return_zip(result.return_zip_bytes, expected_input_sha256=result.input_packet_sha256)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        import json

        receipt = json.loads(archive.read("output/roster_receipt.json"))
    assert receipt["agents"][0]["attempts"][0]["output_present"] is False
    assert receipt["agents"][0]["attempts"][1]["marker_present"] is True


def test_missing_output_after_retries_is_refused() -> None:
    packet = _packet("pass", _ok("two"))
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["return_zip_emitted"] is False
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_MISSING_OUTPUT"
    assert len(refusal["exhausted_agents"][0]["attempts"]) == 2


def test_wrong_marker_is_refused() -> None:
    packet = _packet(
        "Path('output/one.md').write_text('finding: nope\\n', encoding='utf-8')",
        _ok("two"),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_MARKER_MISSING"


def test_missing_required_format_retries_then_refuses() -> None:
    packet = _packet(
        "Path('output/one.md').write_text('ZIP_MD_AGENT_LIVE\\n', encoding='utf-8')",
        _ok("two"),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_FORMAT_MISSING"
    attempt = refusal["exhausted_agents"][0]["attempts"][0]
    assert attempt["missing_fragments"]
    assert attempt["output_preview"] == "ZIP_MD_AGENT_LIVE\n"


def test_controller_prompt_lists_every_required_fragment() -> None:
    from constraintbox_zip_agent.md_agent_roster import _prompt

    prompt = _prompt(
        "AGENTS/one.md",
        "output/one.md",
        MARKER,
        mmm_paths=["REFERENCES/mmm/voice.md"],
        skill_paths=["SKILLS/write-finding.md"],
        context_paths=["input/OBJECT.md"],
        required_fragments=["evidence:", "limit:"],
        forbidden_fragments=[],
        attempt=1,
        attempt_seed="abc",
        prior_refusal=None,
    )
    assert "- evidence:" in prompt
    assert "- limit:" in prompt


def test_128_stateless_fixture_agents_are_gated_and_replay_identically() -> None:
    count = 128
    agents = []
    files = {
        "input/OBJECT.md": b"Write the declared output file.\n",
        "REFERENCES/mmm/voice.md": b"plain particulars only\n",
        "SKILLS/write-finding.md": b"write only the declared markdown output\n",
    }
    for index in range(count):
        agent_id = f"agent-{index:03d}"
        output_path = f"output/{agent_id}.md"
        files[f"AGENTS/{agent_id}.md"] = (
            f"role: {agent_id}\noutput: {output_path}\nWrite the marker.\n".encode()
        )
        agents.append(
            {
                "agent_id": agent_id,
                "agent_path": f"AGENTS/{agent_id}.md",
                "output_path": output_path,
                "provider": "fixture-subprocess",
                "model_requested": "fixture-model",
                "fixture_script": _script(
                    (
                        "if os.environ.get('CB_ZIP_ATTEMPT') == '1':\n"
                        f"    Path('{output_path}').write_text('finding: wrong {agent_id}\\n', encoding='utf-8')\n"
                        "else:\n"
                        f"    Path('{output_path}').write_text('finding: {MARKER} {agent_id}\\ntool-token: ' + token + '\\nskill-token: ' + hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest() + '\\n', encoding='utf-8')"
                    )
                    if index == count - 1
                    else f"Path('{output_path}').write_text('finding: {MARKER} {agent_id}\\ntool-token: ' + token + '\\nskill-token: ' + hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest() + '\\n', encoding='utf-8')"
                ),
                "mmm_paths": ["REFERENCES/mmm/voice.md"],
                "skill_paths": ["SKILLS/write-finding.md"],
                "context_paths": ["input/OBJECT.md"],
                "required_fragments": ["finding:", agent_id],
                "max_output_bytes": 4096,
            }
        )
    roster = {
        "schema": "constraintbox.md-agent-roster.v1",
        "run_id": "md-roster-128",
        "seed": 128042,
        "required_marker": MARKER,
        "max_attempts": 2,
        "timeout_seconds": 30,
        "max_workers": 16,
        "shared_paths": [],
        "agents": agents,
    }
    packet = build_md_agent_roster_packet(roster=roster, files=files)
    first = execute_packet(packet)
    second = execute_packet(packet)
    assert first.return_zip_bytes == second.return_zip_bytes
    with zipfile.ZipFile(io.BytesIO(first.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
        assert len(receipt["accepted_agent_ids"]) == count
        assert len(receipt["agents"]) == count
        assert all(row["attempts"][0]["refusal_reason"] is None for row in receipt["agents"][:-1])
        assert receipt["agents"][-1]["attempts"][0]["refusal_reason"] == "REFUSE_MD_AGENT_MARKER_MISSING"
        assert receipt["agents"][-1]["accepted_attempt"] == 2
        assert all(len(row["delivered_file_sha256"]) == 5 for row in receipt["agents"])


def test_required_agent_exhaustion_rejects_parent_with_structured_attempt_evidence() -> None:
    agents = [
        _agent("one", _ok("one")),
        _agent("two", "pass"),
    ]
    packet = build_md_agent_roster_packet(roster=_roster(*agents), files=_files())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["accepted_agent_ids"] == ["one"]
    assert refusal["return_zip_emitted"] is False
    assert [row["agent_id"] for row in refusal["exhausted_agents"]] == ["two"]
    assert len(refusal["exhausted_agents"][0]["attempts"]) == 2


def test_agent_file_digest_is_bound_into_the_packet() -> None:
    packet = _packet(_ok("one"), _ok("two"))
    files = _files()
    assert sha256_bytes(files["AGENTS/one.md"])
    result = execute_packet(packet)
    assert result.input_packet_sha256 == sha256_bytes(packet)


def test_adapter_receipt_binds_request_model_prompt_and_source_bytes(tmp_path) -> None:
    prompt = b"exact composed prompt\n"
    source = {
        "schema": "constraintbox.codex-cli-receipt.v1",
        "request_id": "zip-request-1",
        "model_requested": "gpt-5.6-luna",
        "model_observed": "gpt-5.6-luna",
        "model_binding_confirmed": True,
        "prompt_sha256": sha256_bytes(prompt),
        "disposition": "OBSERVED",
    }
    receipt_path = tmp_path / "provider.json"
    receipt_path.write_text(json.dumps(source), encoding="utf-8")
    evidence = _provider_evidence(
        provider="codex-cli",
        evidence_path=receipt_path,
        request_id="zip-request-1",
        model_requested="gpt-5.6-luna",
        prompt=prompt,
    )
    assert evidence["model_observed"] == ["gpt-5.6-luna"]
    assert evidence["model_binding_confirmed"] is True
    assert evidence["provider_source_receipt_sha256"] == sha256_bytes(receipt_path.read_bytes())
    assert evidence["provider_source_receipt"] == source


@pytest.mark.parametrize("field,value", [
    ("request_id", "wrong"),
    ("model_binding_confirmed", False),
    ("prompt_sha256", "0" * 64),
])
def test_adapter_receipt_mismatch_is_refused(tmp_path, field: str, value: object) -> None:
    prompt = b"exact composed prompt\n"
    source = {
        "schema": "constraintbox.grok-cli-receipt.v1",
        "request_id": "zip-request-2",
        "model_requested": "grok-4.6",
        "models_observed_in_output": ["grok-4.6-build"],
        "model_binding_confirmed": True,
        "prompt_sha256": sha256_bytes(prompt),
        "disposition": "OBSERVED",
    }
    source[field] = value
    receipt_path = tmp_path / "provider.json"
    receipt_path.write_text(json.dumps(source), encoding="utf-8")
    with pytest.raises(ZipJobRefusal) as caught:
        _provider_evidence(
            provider="grok-cli",
            evidence_path=receipt_path,
            request_id="zip-request-2",
            model_requested="grok-4.6",
            prompt=prompt,
        )
    assert caught.value.reason_code == "REFUSE_MD_AGENT_PROVIDER_EVIDENCE"


def test_tool_pretask_output_is_delivered_and_bound_to_each_worker() -> None:
    files = _files()
    files["inputs/tool_payload.json"] = b'{"z":1,"a":[3,2,1]}'
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", _ok("one")), _agent("two", _ok("two"))),
        files=files,
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        evidence = archive.read("output/tool_evidence.json")
        receipt = json.loads(archive.read("output/roster_receipt.json"))
    digest = sha256_bytes(evidence)
    assert all(
        row["delivered_file_sha256"]["output/tool_evidence.json"] == digest
        for row in receipt["agents"]
    )
    assert receipt["host_hooks_used"] is False
    assert receipt["mmm_read_proved"] is False
    assert receipt["skill_executed"] is False
    assert receipt["llm_invoked_tool"] is False
    assert "not_host_hook" in receipt["claim_ceiling"]
    assert result.return_zip_bytes == execute_packet(packet).return_zip_bytes


def test_missing_tool_token_is_refused_even_when_file_and_marker_exist() -> None:
    one = _agent(
        "one",
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\n', encoding='utf-8')",
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(one, _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_TOOL_TOKEN_MISSING"
    assert refusal["host_hooks_used"] is False


def test_wrong_run_tool_token_is_refused() -> None:
    one = _agent(
        "one",
        "Path('output/one.md').write_text("
        "'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + ('0' * 64) + '\\n', encoding='utf-8')",
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(one, _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_TOOL_TOKEN_MISSING"


def test_live_provider_env_does_not_copy_host_secrets(monkeypatch) -> None:
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "should-not-pass")
    monkeypatch.setenv("GH_TOKEN", "should-not-pass")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "should-not-pass")
    monkeypatch.setenv("OPENAI_API_KEY", "codex-ok")
    env = _provider_env("codex-cli")
    assert "AWS_SECRET_ACCESS_KEY" not in env
    assert "GH_TOKEN" not in env
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert env["OPENAI_API_KEY"] == "codex-ok"
    assert "CODEX_HOME" not in env
    grok_env = _provider_env("grok-cli")
    assert "OPENAI_API_KEY" not in grok_env
    assert "AWS_SECRET_ACCESS_KEY" not in grok_env
    monkeypatch.setenv("XAI_API_KEY", "should-not-pass")
    monkeypatch.setenv("GROK_API_KEY", "should-not-pass")
    grok_env = _provider_env("grok-cli")
    assert "XAI_API_KEY" not in grok_env
    assert "GROK_API_KEY" not in grok_env


def test_worker_tool_request_requires_later_attempt_to_consume_result() -> None:
    asked = (
        "payload = {'asked': True, 'n': 7}\n"
        "if os.environ['CB_ZIP_ATTEMPT'] == '1':\n"
        "    Path('output/tool_request.json').write_text(\n"
        "        json.dumps({'schema': 'constraintbox.md-agent-tool-request.v1',"
        " 'script_path': 'TOOLS/make_token.py', 'payload': payload}),\n"
        "        encoding='utf-8',\n"
        "    )\n"
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text("
        "'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", asked), _agent("two", _ok("two"))),
        files=_files(),
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
        one = archive.read("output/one.md").decode("utf-8")
    assert receipt["llm_invoked_tool"] is False
    assert receipt["tool_request_observed"] is True
    assert receipt["cb_tool_executed"] is True
    assert receipt["tool_result_consumed_on_later_attempt"] is True
    assert receipt["agents"][0]["accepted_attempt"] == 2
    assert receipt["agents"][0]["attempts"][0]["refusal_reason"] == "HOLD_MD_AGENT_TOOL_APPLIED_NEED_REWRITE"
    assert receipt["agents"][0]["llm_invoked_tool"] is False
    assert receipt["agents"][0]["cb_tool_executed"] is True
    assert receipt["agents"][0]["tool_result_consumed_on_later_attempt"] is True
    assert receipt["agents"][1]["llm_invoked_tool"] is False
    assert "tool-token:" in one


def test_worker_cannot_precompute_tool_result_and_accept_same_attempt() -> None:
    asked = (
        "payload = {'asked': True, 'n': 7}\n"
        "Path('output/tool_request.json').write_text(\n"
        "    json.dumps({'schema': 'constraintbox.md-agent-tool-request.v1',"
        " 'script_path': 'TOOLS/make_token.py', 'payload': payload}), encoding='utf-8')\n"
        "canonical = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True)\n"
        "predicted = hashlib.sha256(canonical.encode('utf-8')).hexdigest()\n"
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text("
        "'finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + predicted + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
    )
    roster = _roster(_agent("one", asked), _agent("two", _ok("two")))
    roster["max_attempts"] = 1
    packet = build_md_agent_roster_packet(roster=roster, files=_files())
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    refusal = json.loads(caught.value.detail)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "HOLD_MD_AGENT_TOOL_APPLIED_NEED_REWRITE"


def test_worker_tool_request_missing_script_is_refused() -> None:
    bad = (
        "Path('output/tool_request.json').write_text(\n"
        "    json.dumps({'schema': 'constraintbox.md-agent-tool-request.v1',"
        " 'script_path': 'TOOLS/missing.py', 'payload': {'x': 1}}),\n"
        "    encoding='utf-8',\n"
        ")\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", bad), _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    refusal = json.loads(caught.value.detail)
    assert refusal["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_TOOL_REQUEST"


def test_missing_skill_token_is_refused() -> None:
    one = _agent(
        "one",
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\n', encoding='utf-8')",
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(one, _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_SKILL_TOKEN_MISSING"


def test_extra_undeclared_workspace_file_is_refused() -> None:
    extra = (
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/sneak.md').write_text('nope\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", extra), _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_EXTRA_OUTPUT"


def test_extra_undeclared_output_is_refused() -> None:
    extra = (
        "skill = hashlib.sha256(Path('SKILLS/write-finding.md').read_bytes()).hexdigest()\n"
        "Path('output/one.md').write_text('finding: ZIP_MD_AGENT_LIVE\\ntool-token: ' + token + '\\nskill-token: ' + skill + '\\n', encoding='utf-8')\n"
        "Path('output/sneak.md').write_text('nope\\n', encoding='utf-8')\n"
    )
    packet = build_md_agent_roster_packet(
        roster=_roster(_agent("one", extra), _agent("two", _ok("two"))),
        files=_files(),
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_EXTRA_OUTPUT"


def test_host_hook_requirement_holds_live_provider(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CB_REQUIRE_HOST_HOOK", "1")
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "codex-cli", "model_requested": "gpt-5.6-luna"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_HOST_HOOK_REQUIRED"


def test_unmanaged_live_launch_holds_without_process_box_nonce(tmp_path) -> None:
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "grok-cli", "model_requested": "grok-4.6"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_HOST_HOOK_REQUIRED"


def test_forged_dispatch_nonce_without_file_is_held(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CB_DISPATCH_NONCE", "forged")
    monkeypatch.delenv("CB_DISPATCH_NONCE_FILE", raising=False)
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "grok-cli", "model_requested": "grok-4.6"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_DISPATCH_NONCE_UNBOUND"


def test_dispatch_nonce_mismatch_is_held(monkeypatch, tmp_path) -> None:
    nonce = tmp_path / "dispatch.nonce"
    nonce.write_text("box-nonce\n", encoding="utf-8")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "forged")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {"provider": "grok-cli", "model_requested": "grok-4.6"},
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_DISPATCH_NONCE_MISMATCH"


def test_codex_home_unbound_is_held(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("CODEX_HOME", raising=False)
    nonce = tmp_path / "dispatch.nonce"
    nonce.write_text("test-nonce\n", encoding="utf-8")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "test-nonce")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {
                "provider": "codex-cli",
                "model_requested": "gpt-5.6-luna",
                "runner_path": "/usr/local/bin/codex",
            },
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "HOLD_CODEX_HOME_UNBOUND"


def test_live_provider_without_runner_is_held(monkeypatch, tmp_path) -> None:
    nonce = tmp_path / "dispatch.nonce"
    nonce.write_text("test-nonce\n", encoding="utf-8")
    monkeypatch.setenv("CB_DISPATCH_NONCE", "test-nonce")
    monkeypatch.setenv("CB_DISPATCH_NONCE_FILE", str(nonce))
    from constraintbox_zip_agent.md_agent_roster import _argv

    with pytest.raises(ZipJobRefusal) as caught:
        _argv(
            {
                "provider": "grok-cli",
                "model_requested": "grok-4.6",
            },
            tmp_path,
            tmp_path / "prompt.md",
            request_id="x",
            timeout_seconds=5,
        )
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_SCHEMA"
