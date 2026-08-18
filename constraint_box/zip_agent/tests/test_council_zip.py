from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

import pytest

from constraintbox_zip_agent.council_zip import (
    MARKER,
    assign_mini_mmm_combos,
    build_council_loop_packet,
    build_council_zip_packet,
    build_named_council_packet,
    build_three_member_council_packet,
    compare_shadow_lanes,
)
from constraintbox_zip_agent.cli import main
from constraintbox_zip_agent.protocol import ZipJobRefusal, sha256_bytes, validate_return_zip
from constraintbox_zip_agent.runtime import execute_packet


def _script(agent_id: str) -> str:
    return (
        "from pathlib import Path\n"
        "import json, hashlib\n"
        "Path('output').mkdir(exist_ok=True)\n"
        "Path('meta').mkdir(exist_ok=True)\n"
        "Path('meta/provider_evidence.json').write_text(\n"
        "    json.dumps({'schema':'constraintbox.fixture-provider-evidence.v1',"
        "'disposition':'OBSERVED','model_observed':'fixture-observed'}) + '\\n',\n"
        "    encoding='utf-8',\n"
        ")\n"
        "token = json.loads(Path('output/tool_evidence.json').read_text(encoding='utf-8'))['canonical_sha256']\n"
        "skill = hashlib.sha256(Path('SKILLS/council.md').read_bytes()).hexdigest()\n"
        "manifest = json.loads(Path('input/council_manifest.json').read_text(encoding='utf-8'))\n"
        "me = next(row for row in manifest['members'] if row['agent_id'] == "
        f"'{agent_id}')\n"
        "mmm_lines = ''.join('mmm-token: ' + digest + '\\n' for digest in me['mmm_sha256'].values())\n"
        f"Path('output/{agent_id}.md').write_text(\n"
        f"    'finding: {MARKER}\\n'"
        f"    'council: {agent_id}\\n'"
        "    'support: observed\\n'"
        "    'falsifier: missing required token\\n'"
        "    'keep_or_discard: keep\\n'"
        "    'live_patch: false\\n'"
        "    'disposition: REQUEST_CONTEXT\\n'"
        "    'tool-token: ' + token + '\\n'"
        "    'skill-token: ' + skill + '\\n'"
        "    + mmm_lines,\n"
        "    encoding='utf-8',\n"
        ")\n"
    )


def _agent(agent_id: str) -> dict:
    return {
        "agent_id": agent_id,
        "agent_path": f"AGENTS/{agent_id}.md",
        "output_path": f"output/{agent_id}.md",
        "provider": "fixture-subprocess",
        "model_requested": "fixture-model",
        "fixture_script": _script(agent_id),
        "required_fragments": [
            f"finding: {MARKER}",
            f"council: {agent_id}",
            "support: observed",
        ],
        "max_output_bytes": 4096,
    }


def _mmm_files() -> dict[str, bytes]:
    return {
        f"MMMS/{voice}.md": f"# {voice} compact mini-MMM fixture\nparticular evidence only\n".encode()
        for voice in (
            "factory",
            "feynman",
            "hume",
            "orwell",
            "popper",
            "pushback",
            "strategy",
            "systems",
            "zhuangzi",
        )
    }


def test_legacy_council_builder_still_requires_three_agents() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        build_council_zip_packet(
            roster={
                "schema": "constraintbox.md-agent-roster.v1",
                "required_marker": MARKER,
                "agents": [{"agent_id": "failure"}],
            },
            files={"AGENTS/failure.md": b"x"},
        )
    assert caught.value.reason_code == "REFUSE_COUNCIL_ZIP_ROSTER"


def test_three_member_council_assigns_distinct_mmm_combos_and_returns() -> None:
    owner = b"Target: packet Python still has host-wide file-read*. Do not promote.\n"
    packet = build_three_member_council_packet(
        owner_prompt=owner,
        seed=461,
        run_id="council-three-fixture",
        agents=[_agent("failure"), _agent("repair"), _agent("strategy")],
        mmm_files=_mmm_files(),
        extra_files={
            "AGENTS/failure.md": b"role: failure\n",
            "AGENTS/repair.md": b"role: repair\n",
            "AGENTS/strategy.md": b"role: strategy\n",
        },
    )
    result = execute_packet(packet)
    validate_return_zip(
        result.return_zip_bytes,
        expected_input_sha256=result.input_packet_sha256,
        input_packet_bytes=packet,
    )
    with zipfile.ZipFile(io.BytesIO(packet)) as archive:
        manifest = json.loads(archive.read("input/council_manifest.json"))
        for path, raw in _mmm_files().items():
            assert archive.read(path) == raw
    combos = [tuple(row["mmm_ids"]) for row in manifest["members"]]
    assert len(set(combos)) == 3
    assert all(len(row["mmm_ids"]) >= 2 for row in manifest["members"])
    assert set(manifest["selection"]["member_voice_counts"]) == {"failure", "repair", "strategy"}
    for row in manifest["members"]:
        for voice in row["mmm_core"]:
            assert f"voice:{voice}:compact" in row["mmm_ids"]
    assert manifest["owner_prompt_sha256"] == sha256_bytes(owner)
    assert manifest["promotion_allowed"] is False
    assert manifest["mmm_read_proved"] is False
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
        bodies = {
            name: archive.read(f"output/{name}.md").decode("utf-8")
            for name in ("failure", "repair", "strategy")
        }
    assert receipt["accepted_agent_ids"] == ["failure", "repair", "strategy"]
    for row in manifest["members"]:
        body = bodies[row["agent_id"]]
        assert f"council: {row['agent_id']}" in body
        assert f"skill-token: {row['skill_sha256']}" in body
        for digest in row["mmm_sha256"].values():
            assert f"mmm-token: {digest}" in body
    compare = compare_shadow_lanes(
        target_sha256=sha256_bytes(owner),
        internal_accepted=receipt["accepted_agent_ids"],
        external_findings=[
            {
                "lane": "external",
                "failure": "host-wide packet-Python file-read*",
                "support": "observed",
                "disposition": "required_hardening",
            },
            {
                "lane": "external",
                "failure": "internal ZIP is not superior because it returned",
                "support": "inferred",
                "disposition": "stop",
            },
        ],
    )
    assert compare["winner"] is None
    assert compare["internal_not_superior"] is True


def test_council_zip_wrong_roster_is_refused() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        build_council_zip_packet(
            roster={
                "schema": "constraintbox.md-agent-roster.v1",
                "required_marker": MARKER,
                "agents": [{"agent_id": "failure"}],
            },
            files={"AGENTS/failure.md": b"x"},
        )
    assert caught.value.reason_code == "REFUSE_COUNCIL_ZIP_ROSTER"


def test_bind_live_agent_fields_holds_missing_runner(tmp_path) -> None:
    from constraintbox_zip_agent.council_zip import bind_live_agent_fields

    with pytest.raises(ZipJobRefusal) as caught:
        bind_live_agent_fields(
            {"provider": "codex-cli", "model_requested": "gpt-5.6-luna"},
            paths={"runner_path": str(tmp_path / "missing-codex")},
        )
    assert caught.value.reason_code == "HOLD_LIVE_RUNNER_UNBOUND"


def test_live_failure_packet_builds_with_explicit_mmm_and_route_fixtures(tmp_path: Path) -> None:
    from constraintbox_zip_agent.live_failure_council import build_live_failure_council_packet

    mmm_root = tmp_path / "mmm"
    mmm_root.mkdir()
    for path, raw in _mmm_files().items():
        voice = path.split("/")[1][:-3]
        (mmm_root / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md").write_bytes(raw)
    box_root = Path(__file__).resolve().parents[2]
    controller_src = box_root / "src"
    if not controller_src.is_dir():
        controller_src = (
            box_root / "integrated_system" / "runtime" / "controller_src"
        )
    live_paths = {
        "codex-cli": {
            "runner_path": str(tmp_path / "codex-runner"),
            "codex_home": str(tmp_path / "codex-home"),
            "controller_src": str(controller_src),
        },
        "grok-cli": {
            "runner_path": str(tmp_path / "grok-runner"),
            "controller_src": str(controller_src),
        },
        "claude-code": {
            "runner_path": str(tmp_path / "claude-runner"),
            "bridge_path": str(tmp_path / "claude-bridge.py"),
            "controller_src": str(controller_src),
        },
    }
    for provider, paths in live_paths.items():
        runner = Path(paths["runner_path"])
        runner.write_text("fixture runner\n")
        if provider == "codex-cli":
            Path(paths["codex_home"]).mkdir()
        if provider == "claude-code":
            Path(paths["bridge_path"]).write_text("fixture bridge\n")

    packet = build_live_failure_council_packet(
        owner_prompt=b"Target: host-wide packet-Python file-read*. Do not promote.\n",
        mmm_root=mmm_root,
        live_paths=live_paths,
        live_routes={
            "likely": ("codex-cli", "fixture-codex"),
            "dangerous": ("grok-cli", "fixture-grok"),
            "assumption": ("claude-code", "fixture-claude"),
        },
    )
    import io, json, zipfile

    with zipfile.ZipFile(io.BytesIO(packet)) as archive:
        manifest = json.loads(archive.read("input/council_manifest.json"))
        names = archive.namelist()
    assert manifest["council_id"] == "failure"
    assert {row["agent_id"] for row in manifest["members"]} == {"likely", "dangerous", "assumption"}
    assert all(name.startswith("MMMS/") and name.endswith(".md") for name in names if name.startswith("MMMS/"))
    providers = {row["provider"] for row in manifest["members"]}
    assert providers == {"codex-cli", "grok-cli", "claude-code"}


def test_live_failure_packet_refuses_missing_run_data() -> None:
    from constraintbox_zip_agent.live_failure_council import build_live_failure_council_packet

    with pytest.raises(ZipJobRefusal) as caught:
        build_live_failure_council_packet(
            owner_prompt=b"target\n",
            mmm_root=None,  # type: ignore[arg-type]
            live_paths=None,  # type: ignore[arg-type]
            live_routes=None,  # type: ignore[arg-type]
        )
    assert caught.value.reason_code == "HOLD_LIVE_RUN_DATA_UNBOUND"


def test_mmm_assignment_is_replayable() -> None:
    first = assign_mini_mmm_combos(seed=461)
    second = assign_mini_mmm_combos(seed=461)
    other = assign_mini_mmm_combos(seed=462)
    assert first == second
    assert first != other
    assert len({tuple(v) for v in first.values()}) == 3


def test_role_fit_combos_vary_by_seed_and_keep_cores() -> None:
    from constraintbox_zip_agent.council_zip import FAILURE_DEEP_MEMBERS, ROLE_CORE_VOICES

    a = assign_mini_mmm_combos(seed=11, members=FAILURE_DEEP_MEMBERS)
    b = assign_mini_mmm_combos(seed=12, members=FAILURE_DEEP_MEMBERS)
    assert a != b
    for member, voices in a.items():
        for core in ROLE_CORE_VOICES[member]:
            assert core in voices
        assert 2 <= len(voices) <= 4


def test_failure_deep_six_member_fixture_returns() -> None:
    from constraintbox_zip_agent.council_zip import FAILURE_DEEP_MEMBERS

    owner = b"Target: host-wide file-read* plus Grok live flake. Do not promote.\n"
    extra = {f"AGENTS/{name}.md": f"role: {name}\n".encode() for name in FAILURE_DEEP_MEMBERS}
    packet = build_named_council_packet(
        council_id="failure-deep",
        owner_prompt=owner,
        seed=77,
        run_id="failure-deep-fixture",
        agents=[_agent(name) for name in FAILURE_DEEP_MEMBERS],
        mmm_files=_mmm_files(),
        extra_files=extra,
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(packet)) as archive:
        manifest = json.loads(archive.read("input/council_manifest.json"))
        roster = json.loads(archive.read("inputs/roster.json"))
    assert manifest["council_id"] == "failure-deep"
    assert roster["max_workers"] == 6
    assert {row["agent_id"] for row in manifest["members"]} == set(FAILURE_DEEP_MEMBERS)
    counts = set(manifest["selection"]["member_voice_counts"].values())
    assert counts <= {2, 3, 4}
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
        bodies = {
            name: archive.read(f"output/{name}.md").decode("utf-8")
            for name in FAILURE_DEEP_MEMBERS
        }
    assert receipt["accepted_agent_ids"] == list(FAILURE_DEEP_MEMBERS)
    for name, body in bodies.items():
        assert "falsifier:" in body
        assert f"council: {name}" in body


def test_three_member_council_refuses_incomplete_mmm_set() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        build_three_member_council_packet(
            owner_prompt=b"x",
            seed=1,
            run_id="missing-mmm",
            agents=[_agent("failure"), _agent("repair"), _agent("strategy")],
            mmm_files={"MMMS/hume.md": b"not the complete set\n"},
            extra_files={
                "AGENTS/failure.md": b"role: failure\n",
                "AGENTS/repair.md": b"role: repair\n",
                "AGENTS/strategy.md": b"role: strategy\n",
            },
        )
    assert caught.value.reason_code == "REFUSE_COUNCIL_ZIP_MMM_SET"


def test_build_council_cli_embeds_supplied_mmm_bytes(tmp_path: Path, capsys) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("owner object\n")
    current_context = tmp_path / "CURRENT.md"
    current_context.write_bytes(b"# Current project context\nexact retained view\n")
    mmm_dir = tmp_path / "mmm"
    mmm_dir.mkdir()
    for voice, raw in ((path.split("/")[1][:-3], data) for path, data in _mmm_files().items()):
        (mmm_dir / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md").write_bytes(raw)
    fixture = "from pathlib import Path\nraise SystemExit(1)\n"
    config = tmp_path / "run.json"
    config.write_text(
        json.dumps(
            {
                "schema": "constraintbox.internal-council-run.v1",
                "run_id": "cli-council",
                "seed": 7,
                "agents": [
                    {
                        "agent_id": name,
                        "provider": "fixture-subprocess",
                        "model_requested": "fixture-model",
                        "fixture_script": fixture,
                        "max_attempts": 1,
                        "timeout_seconds": 5,
                    }
                    for name in ("failure", "repair", "strategy")
                ],
            }
        )
    )
    packet = tmp_path / "council.zip"
    assert main(
        [
            "build-council",
            "--owner-prompt",
            str(prompt),
            "--run-config",
            str(config),
            "--mmm-dir",
            str(mmm_dir),
            "--context-file",
            str(current_context),
            "--out",
            str(packet),
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["disposition"] == "COUNCIL_ZIP_BUILT_LOCAL"
    with zipfile.ZipFile(packet) as archive:
        for path, raw in _mmm_files().items():
            assert archive.read(path) == raw
        context_path = "input/context/000-CURRENT.md"
        assert archive.read(context_path) == current_context.read_bytes()
        manifest = json.loads(archive.read("input/council_manifest.json"))
        roster = json.loads(archive.read("inputs/roster.json"))
    assert all(context_path in row["context_paths"] for row in manifest["members"])
    assert all(context_path in row["context_paths"] for row in roster["agents"])


def test_build_failure_deep_council_cli_supports_six_members(tmp_path: Path, capsys) -> None:
    from constraintbox_zip_agent.council_zip import FAILURE_DEEP_MEMBERS

    prompt = tmp_path / "prompt.md"
    prompt.write_text("owner object\n")
    mmm_dir = tmp_path / "mmm"
    mmm_dir.mkdir()
    for voice, raw in ((path.split("/")[1][:-3], data) for path, data in _mmm_files().items()):
        (mmm_dir / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md").write_bytes(raw)
    config = tmp_path / "failure-deep-run.json"
    config.write_text(
        json.dumps(
            {
                "schema": "constraintbox.internal-council-run.v1",
                "run_id": "cli-failure-deep",
                "seed": 19,
                "agents": [
                    {
                        "agent_id": name,
                        "provider": "fixture-subprocess",
                        "model_requested": "fixture-model",
                        "fixture_script": "raise SystemExit(1)\n",
                        "max_attempts": 1,
                        "timeout_seconds": 5,
                    }
                    for name in FAILURE_DEEP_MEMBERS
                ],
            }
        )
    )
    packet = tmp_path / "failure-deep.zip"
    assert main(
        [
            "build-council",
            "--owner-prompt",
            str(prompt),
            "--run-config",
            str(config),
            "--mmm-dir",
            str(mmm_dir),
            "--council-id",
            "failure-deep",
            "--out",
            str(packet),
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["disposition"] == "COUNCIL_ZIP_BUILT_LOCAL"
    with zipfile.ZipFile(packet) as archive:
        manifest = json.loads(archive.read("input/council_manifest.json"))
        roster = json.loads(archive.read("inputs/roster.json"))
    assert manifest["council_id"] == "failure-deep"
    assert roster["max_workers"] == 6
    assert [row["agent_id"] for row in roster["agents"]] == list(FAILURE_DEEP_MEMBERS)


def test_build_repair_council_validates_and_embeds_failure_return(
    tmp_path: Path, capsys
) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("owner object\n")
    mmm_dir = tmp_path / "mmm"
    mmm_dir.mkdir()
    for voice, raw in ((path.split("/")[1][:-3], data) for path, data in _mmm_files().items()):
        (mmm_dir / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md").write_bytes(raw)

    failure_packet_bytes = build_named_council_packet(
        council_id="failure",
        owner_prompt=prompt.read_bytes(),
        seed=8,
        run_id="failure-prior",
        agents=[_agent("likely"), _agent("dangerous"), _agent("assumption")],
        mmm_files=_mmm_files(),
        extra_files={
            "AGENTS/likely.md": b"role: likely\n",
            "AGENTS/dangerous.md": b"role: dangerous\n",
            "AGENTS/assumption.md": b"role: assumption\n",
        },
    )
    failure_result = execute_packet(failure_packet_bytes)
    failure_packet = tmp_path / "failure.zip"
    failure_return = tmp_path / "failure.return.zip"
    failure_packet.write_bytes(failure_packet_bytes)
    failure_return.write_bytes(failure_result.return_zip_bytes)

    config = tmp_path / "repair-run.json"
    config.write_text(
        json.dumps(
            {
                "schema": "constraintbox.internal-council-run.v1",
                "run_id": "repair-with-prior",
                "seed": 9,
                "agents": [
                    {
                        "agent_id": name,
                        "provider": "fixture-subprocess",
                        "model_requested": "fixture-model",
                        "fixture_script": "raise SystemExit(1)\n",
                        "max_attempts": 1,
                        "timeout_seconds": 5,
                    }
                    for name in ("smallest", "test", "ceiling")
                ],
            }
        )
    )
    repair_packet = tmp_path / "repair.zip"
    assert main(
        [
            "build-council",
            "--owner-prompt",
            str(prompt),
            "--run-config",
            str(config),
            "--mmm-dir",
            str(mmm_dir),
            "--council-id",
            "repair",
            "--failure-packet",
            str(failure_packet),
            "--failure-return",
            str(failure_return),
            "--out",
            str(repair_packet),
        ]
    ) == 0
    assert json.loads(capsys.readouterr().out)["disposition"] == "COUNCIL_ZIP_BUILT_LOCAL"
    failure_digest = sha256_bytes(failure_result.return_zip_bytes)
    with zipfile.ZipFile(repair_packet) as archive:
        manifest = json.loads(archive.read("input/council_manifest.json"))
        roster = json.loads(archive.read("inputs/roster.json"))
        assert manifest["bound_receipts"] == {
            "failure_return_sha256": failure_digest
        }
        assert archive.read("input/prior/failure/return.zip") == failure_result.return_zip_bytes
        assert archive.read("input/prior/failure/packet.zip") == failure_packet_bytes
        assert "input/prior/failure/likely.md" in archive.namelist()
        for agent in roster["agents"]:
            assert "input/prior/failure/packet.zip" in agent["context_paths"]
            assert "input/prior/failure/return.zip" in agent["context_paths"]
            assert "input/prior/failure/likely.md" in agent["context_paths"]
            assert f"prior-return-token: {failure_digest}" in agent["required_fragments"]


def test_build_repair_council_refuses_unbound_prior_pair(
    tmp_path: Path, capsys
) -> None:
    prompt = tmp_path / "prompt.md"
    prompt.write_text("owner object\n")
    mmm_dir = tmp_path / "mmm"
    mmm_dir.mkdir()
    for voice, raw in ((path.split("/")[1][:-3], data) for path, data in _mmm_files().items()):
        (mmm_dir / f"MMM_VOICE_{voice.upper()}_COMPACT_v4_1.md").write_bytes(raw)
    config = tmp_path / "repair-run.json"
    config.write_text(
        json.dumps(
            {
                "schema": "constraintbox.internal-council-run.v1",
                "run_id": "repair-unbound",
                "seed": 10,
                "agents": [
                    {
                        "agent_id": name,
                        "provider": "fixture-subprocess",
                        "model_requested": "fixture-model",
                        "fixture_script": "raise SystemExit(1)\n",
                    }
                    for name in ("smallest", "test", "ceiling")
                ],
            }
        )
    )
    assert main(
        [
            "build-council",
            "--owner-prompt",
            str(prompt),
            "--run-config",
            str(config),
            "--mmm-dir",
            str(mmm_dir),
            "--council-id",
            "repair",
            "--out",
            str(tmp_path / "repair.zip"),
        ]
    ) == 2
    assert json.loads(capsys.readouterr().out)["disposition"] == "REFUSE_COUNCIL_ZIP_RECEIPT"


def test_failure_council_runs_and_shadows_external() -> None:
    owner = b"Target: packet Python still has host-wide file-read*. Do not promote.\n"
    packet = build_named_council_packet(
        council_id="failure",
        owner_prompt=owner,
        seed=461,
        run_id="failure-only",
        agents=[_agent("likely"), _agent("dangerous"), _agent("assumption")],
        mmm_files=_mmm_files(),
        extra_files={
            "AGENTS/likely.md": b"role: likely\n",
            "AGENTS/dangerous.md": b"role: dangerous\n",
            "AGENTS/assumption.md": b"role: assumption\n",
        },
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(packet)) as archive:
        manifest = json.loads(archive.read("input/council_manifest.json"))
    assert manifest["council_id"] == "failure"
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        receipt = json.loads(archive.read("output/roster_receipt.json"))
    assert receipt["accepted_agent_ids"] == ["likely", "dangerous", "assumption"]
    compare = compare_shadow_lanes(
        target_sha256=sha256_bytes(owner),
        internal_accepted=receipt["accepted_agent_ids"],
        external_findings=[
            {"lane": "external", "failure": "host-wide file-read*", "support": "observed", "disposition": "required_hardening"}
        ],
    )
    assert compare["winner"] is None


def test_repair_without_failure_receipt_is_refused() -> None:
    with pytest.raises(ZipJobRefusal) as caught:
        build_named_council_packet(
            council_id="repair",
            owner_prompt=b"x",
            seed=1,
            run_id="repair-unbound",
            agents=[_agent("smallest"), _agent("test"), _agent("ceiling")],
            mmm_files=_mmm_files(),
            extra_files={
                "AGENTS/smallest.md": b"role: smallest\n",
                "AGENTS/test.md": b"role: test\n",
                "AGENTS/ceiling.md": b"role: ceiling\n",
            },
        )
    assert caught.value.reason_code == "REFUSE_COUNCIL_ZIP_RECEIPT"


def test_repair_and_strategy_refuse_digest_only_prior_receipts() -> None:
    owner = b"same target bytes\n"
    with pytest.raises(ZipJobRefusal) as repair_refusal:
        build_named_council_packet(
            council_id="repair",
            owner_prompt=owner,
            seed=2,
            run_id="repair-digest-only",
            agents=[_agent("smallest"), _agent("test"), _agent("ceiling")],
            mmm_files=_mmm_files(),
            extra_files={
                "AGENTS/smallest.md": b"role: smallest\n",
                "AGENTS/test.md": b"role: test\n",
                "AGENTS/ceiling.md": b"role: ceiling\n",
            },
            bound_receipts={"failure_return_sha256": "a" * 64},
        )
    assert repair_refusal.value.reason_code == "REFUSE_COUNCIL_ZIP_RECEIPT"

    with pytest.raises(ZipJobRefusal) as strategy_refusal:
        build_named_council_packet(
            council_id="strategy",
            owner_prompt=owner,
            seed=3,
            run_id="strategy-digest-only",
            agents=[
                _agent("systems_boundary"),
                _agent("object_preservation"),
                _agent("divergent_futures"),
            ],
            mmm_files=_mmm_files(),
            extra_files={
                "AGENTS/systems_boundary.md": b"role: systems\n",
                "AGENTS/object_preservation.md": b"role: object\n",
                "AGENTS/divergent_futures.md": b"role: futures\n",
            },
            bound_receipts={
                "failure_return_sha256": "a" * 64,
                "repair_return_sha256": "b" * 64,
            },
        )
    assert strategy_refusal.value.reason_code == "REFUSE_COUNCIL_ZIP_RECEIPT"


def test_council_loop_compile_requests_missing_children() -> None:
    packet = build_council_loop_packet(
        intent={
            "schema": "constraintbox.council-loop-state.v1",
            "owner_prompt_sha256": "c" * 64,
            "failure_return_sha256": "d" * 64,
        }
    )
    result = execute_packet(packet)
    with zipfile.ZipFile(io.BytesIO(result.return_zip_bytes)) as archive:
        compiled = json.loads(archive.read("output/council_loop.json"))
    assert compiled["disposition"] == "REQUEST_CONTEXT"
    assert compiled["next_slice"] == "repair"
    assert compiled["missing"] == ["repair", "strategy"]
    assert compiled["promotion_allowed"] is False


def test_council_loop_compile_refuses_non_hex_child_digests() -> None:
    packet = build_council_loop_packet(
        intent={
            "schema": "constraintbox.council-loop-state.v1",
            "owner_prompt_sha256": "c" * 64,
            "failure_return_sha256": "x" * 64,
        }
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_COUNCIL_LOOP_SCHEMA"


def test_council_self_promotion_fragment_is_refused() -> None:
    owner = b"Target: self-promotion must not pass the gate.\n"
    bad = _agent("failure")
    promote = (
        _script("failure")
        .replace(
            "    'disposition: REQUEST_CONTEXT\\n'",
            "    'disposition: REQUEST_CONTEXT\\n'"
            "    'promotion_allowed: true\\n'",
        )
    )
    bad["fixture_script"] = promote
    packet = build_three_member_council_packet(
        owner_prompt=owner,
        seed=5,
        run_id="self-promote",
        agents=[bad, _agent("repair"), _agent("strategy")],
        mmm_files=_mmm_files(),
        extra_files={
            "AGENTS/failure.md": b"role: failure\n",
            "AGENTS/repair.md": b"role: repair\n",
            "AGENTS/strategy.md": b"role: strategy\n",
        },
    )
    with pytest.raises(ZipJobRefusal) as caught:
        execute_packet(packet)
    assert caught.value.reason_code == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    assert json.loads(caught.value.detail)["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_FORBIDDEN_FRAGMENT"
