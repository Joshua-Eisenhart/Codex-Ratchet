from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
import zipfile
from pathlib import Path

import pytest

ZIP_SRC = Path(__file__).resolve().parents[4] / "zip_agent" / "src"
sys.path.insert(0, str(ZIP_SRC))
import constraintbox_zip_agent.md_agent_roster as roster_module
SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_premortem_zip_wave.py"
SPEC = importlib.util.spec_from_file_location("premortem_zip_wave_candidate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
runner = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runner
SPEC.loader.exec_module(runner)


def _fixture_script(*, member_id: str, mode: str = "valid") -> str:
    # The fixture models a live adapter's response artifact.  It deliberately
    # never creates output/<member>.md; the roster must materialize that file.
    return f'''
import hashlib
import json
import os
from pathlib import Path

if {mode!r} == "missing":
    raise SystemExit(0)
if {mode!r} == "retry" and os.environ.get("CB_ZIP_ATTEMPT") == "1":
    Path("meta/claude-output").mkdir(parents=True, exist_ok=True)
    Path("meta/claude-output/provider_response.txt").write_text("not-json\\n", encoding="utf-8")
    raise SystemExit(0)
target = hashlib.sha256(Path("input/target.bin").read_bytes()).hexdigest()
lens = json.loads(Path("input/lens_manifest.json").read_text(encoding="utf-8"))
me = next(row for row in lens["members"] if row["member_id"] == {member_id!r})
tool = json.loads(Path("output/tool_evidence.json").read_text(encoding="utf-8"))["canonical_sha256"]
skill_digest = hashlib.sha256(Path("SKILLS/cb-premortem-cell/SKILL.md").read_bytes()).hexdigest()
skill_echo = "skill_bytes_delivered_echo:path=SKILLS/cb-premortem-cell/SKILL.md;sha256=" + skill_digest
mmm_echoes = [
    "mmm_bytes_delivered_echo:voice=" + voice + ";path=MMMS/" + voice + ".md;sha256=" + digest
    for voice, digest in me["mmm_sha256"].items()
]
tool_echo = "tool_bytes_delivered_echo:path=output/tool_evidence.json;canonical_sha256=" + tool
evidence = [
    "provider response fixture observed",
    skill_echo,
    tool_echo,
]
evidence.extend(mmm_echoes)
if {mode!r} == "unlabeled":
    evidence[1] = skill_digest
elif {mode!r} == "wrong-voice":
    evidence[3] = evidence[3].replace("voice=", "voice=wrong-")
elif {mode!r} == "wrong-path":
    evidence[1] = evidence[1].replace("SKILLS/cb-premortem-cell/SKILL.md", "SKILLS/other.md")
elif {mode!r} == "wrong-digest":
    evidence[1] = skill_echo[:-64] + ("0" * 64)
elif {mode!r} == "duplicate":
    evidence.append(skill_echo)
elif {mode!r} == "extra-label":
    evidence.append("skill_bytes_delivered_echo:path=SKILLS/extra.md;sha256=" + skill_digest)
value = {{
    "schema": "constraintbox.premortem-cell-result.v1",
    "lens": lens["lens"],
    "target_sha256": target,
    "failure_mechanisms": ["declared provider response may be absent"],
    "evidence": evidence,
    "limits": ["fixture route only"],
    "falsifier": "delete the declared provider response and require refusal",
    "warning": "a missing provider response must not become a prose success",
    "finite_repair": "retain the response channel and rerun the same packet",
    "rerun_operation": "run_child_zip_v1:{member_id}",
    "claim_ceiling": "advisory premortem observation only; no authority or promotion",
}}
if {mode!r} == "digest-other-field":
    value["warning"] = skill_echo
Path("meta/claude-output").mkdir(parents=True, exist_ok=True)
envelope = {{
    "is_error": False,
    "subtype": "success",
    "terminal_reason": "completed",
    "result": (
        json.dumps(value, sort_keys=True).replace(
            '"limits": ["fixture route only"]',
            '"limits": [NaN]',
        ) + "\\n"
        if {mode!r} == "invalid-json" and os.environ.get("CB_ZIP_ATTEMPT") == "1"
        else json.dumps(value, sort_keys=True) + "\\n"
    ),
}}
Path("meta/claude-output/provider_response.txt").write_text(json.dumps(envelope, sort_keys=True), encoding="utf-8")
'''


@pytest.fixture(autouse=True)
def _fake_live_provider_response(monkeypatch: pytest.MonkeyPatch) -> None:
    """Run a model-free live-shaped adapter through provider_response mode."""

    def fake_argv(agent, work, prompt_path, *, request_id, timeout_seconds, output_delivery, hierarchy=None):
        del prompt_path, request_id, timeout_seconds, output_delivery, hierarchy
        evidence_path = work / "meta" / "provider_receipt.json"
        script = agent["fixture_script"]
        env = {
            "PATH": str(Path(sys.executable).resolve().parent),
            "HOME": str(work / "home"),
            "TMPDIR": str(work / "tmp"),
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        (work / "home").mkdir(exist_ok=True)
        (work / "tmp").mkdir(exist_ok=True)
        return [sys.executable, "-c", script], env, evidence_path

    def fake_evidence(
        *, provider, evidence_path, request_id, model_requested, prompt,
        model_observed_allowlist=None,
    ):
        del provider
        response_path = evidence_path.parent / "claude-output" / "provider_response.txt"
        if not response_path.is_file():
            raise roster_module.ZipJobRefusal(
                "REFUSE_MD_AGENT_PROVIDER_RESPONSE_MISSING",
                str(response_path),
            )
        response_raw = response_path.read_bytes()
        return {
            "provider_request_id": request_id,
            "model_observed": ["fixture-observed"],
            "model_observed_values": ["fixture-observed"],
            "model_observed_allowlist": model_observed_allowlist,
            # Deliberately forge the legacy boolean without a match kind; the
            # parent validator must still refuse a required binding.
            "model_binding_confirmed": True,
            "model_identity_match_kind": "unverified",
            "model_match_kind": "unverified",
            "alias_resolution_source": None,
            "identity_source": "fixture-provider-response",
            "composed_prompt_sha256": hashlib.sha256(prompt).hexdigest(),
            "provider_source_receipt_sha256": "a" * 64,
            "provider_source_receipt": {
                "nested_output_path": str(response_path),
                "nested_output_sha256": hashlib.sha256(response_raw).hexdigest(),
                "model_requested": model_requested,
            },
        }

    monkeypatch.setattr(roster_module, "_argv", fake_argv)
    monkeypatch.setattr(roster_module, "_provider_evidence", fake_evidence)


def _config(*, mode: str = "valid", require_binding: bool = False, member_count: int = 2) -> dict:
    members: dict[str, list[dict]] = {}
    for lens in runner.LENSES:
        rows = []
        for index in range(member_count):
            member_id = f"{lens[:3]}-{index}"
            rows.append(
                {
                    "member_id": member_id,
                    "provider": "claude-code",
                    "model_requested": f"fixture-{lens}-{index}",
                    "output_delivery": "provider_response",
                    "require_model_binding": require_binding,
                    "fixture_script": _fixture_script(member_id=member_id, mode=mode),
                    "runner_path": sys.executable,
                    "bridge_path": __file__,
                }
            )
        members[lens] = rows
    return {
        "schema": runner.CONFIG_SCHEMA,
        "parent_job_id": "premortem-fixture-parent",
        "run_id": "premortem-fixture-run",
        "wave_id": "premortem-fixture-wave",
        "round": 0,
        "seed": 420461,
        "max_rounds": 2,
        "max_attempts": 2,
        "timeout_seconds": 30,
        "members": members,
    }


def _inputs() -> tuple[bytes, bytes, dict[str, bytes]]:
    target = b"CB target bytes remain immutable.\n"
    skill = b"# contained cb-premortem-cell\nreturn strict JSON only\n"
    mmms = {
        "popper": b"# Popper compact\nfalsifier and finite test\n",
        "pushback": b"# Pushback compact\nboundary and hold\n",
        "zhuangzi": b"# Zhuangzi compact\nplural readings without collapse\n",
        "hume": b"# Hume compact\nparticular evidence only\n",
    }
    return target, skill, mmms


def _entries(data: bytes) -> dict[str, bytes]:
    with zipfile.ZipFile(io.BytesIO(data), "r") as archive:
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}


def _rewrite_return_manifest(entries: dict[str, bytes]) -> bytes:
    manifest = json.loads(entries["RETURN_MANIFEST.json"])
    for path, data in list(entries.items()):
        if not path.startswith("receipts/"):
            continue
        receipt = json.loads(data)
        output_sha256 = receipt.get("output_sha256")
        if isinstance(output_sha256, dict):
            receipt["output_sha256"] = {
                output_path: hashlib.sha256(entries[output_path]).hexdigest()
                if output_path in entries
                else digest
                for output_path, digest in output_sha256.items()
            }
            entries[path] = runner.canonical_json_bytes(receipt)
    manifest["file_sha256_registry"] = {
        path: hashlib.sha256(data).hexdigest()
        for path, data in entries.items()
        if path != "RETURN_MANIFEST.json"
    }
    entries["RETURN_MANIFEST.json"] = runner.canonical_json_bytes(manifest)
    return runner.deterministic_zip(entries)


def _tamper_lens_roster(
    packet_bytes: bytes,
    return_bytes: bytes,
    *,
    lens: str,
    mutate,
) -> bytes:
    root = _entries(return_bytes)
    child_path = f"output/{lens}.return.zip"
    child = _entries(root[child_path])
    roster = json.loads(child["output/roster_receipt.json"])
    mutate(roster)
    child["output/roster_receipt.json"] = runner.canonical_json_bytes(roster)
    root[child_path] = _rewrite_return_manifest(child)
    return _rewrite_return_manifest(root)


def _packet() -> tuple[object, dict, bytes, bytes, dict[str, bytes]]:
    target, skill, mmms = _inputs()
    config = _config()
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    return packet, config, target, skill, mmms


def test_build_has_three_real_zip_children_and_explicit_provider_response() -> None:
    packet, config, target, _skill, _mmms = _packet()
    root = _entries(packet.packet_bytes)
    wave = json.loads(root["inputs/wave_manifest.json"])
    assert set(wave["lenses"][0]) >= {"lens", "packet_sha256", "target_sha256"}
    assert wave["target_sha256"] == hashlib.sha256(target).hexdigest()
    assert wave["output_delivery"] == "provider_response"
    assert set(root) >= {
        "ZIP_JOB_MANIFEST.json",
        "inputs/target.bin",
        "inputs/wave_manifest.json",
        "children/likely_failure.zip",
        "children/dangerous_failure.zip",
        "children/hidden_assumption.zip",
    }
    combos = packet.mmm_combos
    assert len(combos) == 6
    assert all(2 <= len(combo) <= 4 for combo in combos.values())
    assert len(set(combos.values())) == len(combos)
    assert config["members"]["likely_failure"][0]["output_delivery"] == "provider_response"


def test_fixture_wave_executes_through_nested_zip_and_preserves_disagreement() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, result.return_zip_bytes
    )
    assert receipt["disposition"] == "PREMORTEM_ZIP_WAVE_COMPLETED"
    assert receipt["semantic_vote"] is None
    assert receipt["authority_disposition"] is None
    assert receipt["promotion_allowed"] is False
    assert receipt["compiled"]["preserved_without_collapse"] is True
    assert len(receipt["lens_receipts"]) == 3
    assert all(len(row["member_records"]) == 2 for row in receipt["lens_receipts"])


def test_replay_is_independently_bound_and_preserves_output_digests() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    first = runner.execute_packet(packet.packet_bytes)
    second = runner.execute_packet(packet.packet_bytes)
    left = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, first.return_zip_bytes
    )
    right = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, second.return_zip_bytes
    )
    assert left["target_sha256"] == right["target_sha256"]
    assert [
        [hashlib.sha256(runner.canonical_json_bytes(member)).hexdigest() for member in lens["member_records"]]
        for lens in left["lens_receipts"]
    ] == [
        [hashlib.sha256(runner.canonical_json_bytes(member)).hexdigest() for member in lens["member_records"]]
        for lens in right["lens_receipts"]
    ]


def test_provider_response_retry_receipt_is_bound() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="retry")
    packet = runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(packet.packet_bytes, result.return_zip_bytes)
    # The lens receipt retains accepted member records; the nested roster
    # remains independently available in the child return for full attempt
    # inspection.  A successful second attempt is therefore not flattened.
    assert receipt["lens_receipts"][0]["accepted_member_ids"] == ["lik-0", "lik-1"]


def test_invalid_strict_json_member_retries_at_member_gate() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="invalid-json")
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, result.return_zip_bytes
    )
    assert receipt["disposition"] == "PREMORTEM_ZIP_WAVE_COMPLETED"

    root = _entries(result.return_zip_bytes)
    child = _entries(root["output/likely_failure.return.zip"])
    roster = json.loads(child["output/roster_receipt.json"])
    first = roster["agents"][0]
    assert first["output_format"] == "strict_json_object"
    assert first["accepted_attempt"] == 2
    assert first["attempts"][0]["json_valid"] is False
    assert first["attempts"][0]["refusal_reason"] == "REFUSE_MD_AGENT_OUTPUT_JSON"
    assert first["attempts"][1]["json_valid"] is True


def test_invalid_strict_json_exhaustion_refuses_whole_child_wave() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="invalid-json")
    config["max_attempts"] = 1
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    with pytest.raises(Exception) as caught:
        runner.execute_packet(packet.packet_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    detail = json.loads(caught.value.detail)
    assert detail["exhausted_agents"][0]["terminal_refusal"] == "REFUSE_MD_AGENT_OUTPUT_JSON"


@pytest.mark.parametrize(
    "mode,terminal",
    [
        ("unlabeled", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
        ("wrong-voice", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
        ("wrong-path", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
        ("wrong-digest", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
        ("duplicate", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
        ("extra-label", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
        ("digest-other-field", "REFUSE_MD_AGENT_SKILL_ECHO_MISSING"),
    ],
)
def test_delivery_echo_negative_controls_refuse_at_member_gate(
    mode: str, terminal: str
) -> None:
    target, skill, mmms = _inputs()
    config = _config(mode=mode)
    config["max_attempts"] = 1
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    with pytest.raises(Exception) as caught:
        runner.execute_packet(packet.packet_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"
    detail = json.loads(caught.value.detail)
    assert detail["exhausted_agents"][0]["terminal_refusal"] == terminal


def test_target_is_repeated_exactly_for_each_lens_and_member() -> None:
    packet, _config_value, target, _skill, _mmms = _packet()
    root = _entries(packet.packet_bytes)
    for lens in runner.LENSES:
        child = _entries(root[f"children/{lens}.zip"])
        assert child["input/target.bin"] == target
        manifest = json.loads(child["input/lens_manifest.json"])
        assert manifest["target_sha256"] == hashlib.sha256(target).hexdigest()
        roster = json.loads(child["inputs/roster.json"])
        assert all("input/target.bin" in row["context_paths"] for row in roster["agents"])


def test_missing_lens_member_is_refused() -> None:
    target, skill, mmms = _inputs()
    config = _config(member_count=1)
    with pytest.raises(Exception) as caught:
        runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_MEMBER_COUNT"


def test_wrong_output_delivery_is_refused_before_build() -> None:
    target, skill, mmms = _inputs()
    config = _config()
    config["members"]["likely_failure"][0]["output_delivery"] = "worker_file"
    with pytest.raises(Exception) as caught:
        runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_OUTPUT_DELIVERY"


def test_model_binding_mismatch_is_refused_after_provider_return() -> None:
    target, skill, mmms = _inputs()
    config = _config(require_binding=True)
    packet = runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    result = runner.execute_packet(packet.packet_bytes)
    with pytest.raises(Exception) as caught:
        runner.validate_premortem_zip_wave_return(packet.packet_bytes, result.return_zip_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_MODEL_BINDING"


def test_retry_exhaustion_is_a_refusal_and_emits_no_wave_return() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="missing")
    packet = runner.build_premortem_zip_wave_packet(config=config, target=target, skill=skill, mmm_sources=mmms)
    with pytest.raises(Exception) as caught:
        runner.execute_packet(packet.packet_bytes)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_MD_AGENT_ROSTER_EXHAUSTED"


def test_cancellation_does_not_build_or_call_children() -> None:
    target, skill, mmms = _inputs()
    receipt = runner.run_premortem_zip_wave(config=_config(), target=target, skill=skill, mmm_sources=mmms, cancel=True)
    assert receipt["disposition"] == "CANCELLED"
    assert receipt["stop_reason"] == "cancelled"
    assert receipt["rounds"] == []


def test_repair_callback_gets_temp_workspace_and_never_live_target(tmp_path: Path) -> None:
    target, skill, mmms = _inputs()
    original = bytes(target)
    seen: list[Path] = []

    def repair(receipt: dict, work: Path) -> bytes | None:
        seen.append(work)
        assert (work / "target.bin").read_bytes() == original
        assert (work / "receipt.json").is_file()
        return None

    result = runner.run_premortem_zip_wave(
        config=_config(), target=target, skill=skill, mmm_sources=mmms,
        repair_workspace=tmp_path, repair_callback=repair,
    )
    assert result["stop_reason"] == "no_material_delta"
    assert seen and all(path.parent == tmp_path for path in seen)
    assert target == original


def test_tampered_return_is_refused() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    result = runner.execute_packet(packet.packet_bytes)
    root = _entries(result.return_zip_bytes)
    child_entries = _entries(root["output/likely_failure.return.zip"])
    child_entries["output/lik-0.md"] += b"tamper\n"
    root["output/likely_failure.return.zip"] = runner.deterministic_zip(child_entries)
    tampered = runner.deterministic_zip(root)
    with pytest.raises(Exception) as caught:
        runner.validate_premortem_zip_wave_return(packet.packet_bytes, tampered)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_RETURN_DIGEST_MISMATCH"


@pytest.mark.parametrize(
    "mutate,expected_missing,expected_extra",
    [
        (lambda roster: roster.update({"roster_extra": "x"}), [], ["roster_extra"]),
        (lambda roster: roster.pop("host_hooks_used"), ["host_hooks_used"], []),
    ],
)
def test_parent_rejects_recomputed_roster_shape_with_bounded_delta(
    mutate, expected_missing: list[str], expected_extra: list[str]
) -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    result = runner.execute_packet(packet.packet_bytes)
    tampered = _tamper_lens_roster(
        packet.packet_bytes,
        result.return_zip_bytes,
        lens="likely_failure",
        mutate=mutate,
    )
    with pytest.raises(Exception) as caught:
        runner.validate_premortem_zip_wave_return(packet.packet_bytes, tampered)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_ROSTER_SCHEMA"
    detail = json.loads(caught.value.detail)
    assert detail["lens"] == "likely_failure"
    assert detail["child_job_id"] == "premortem-fixture-parent-likely_failure"
    assert detail["expected_output_paths"] == [
        "output/lik-0.md",
        "output/lik-1.md",
    ]
    assert detail["missing_fields"] == expected_missing
    assert detail["extra_fields"] == expected_extra
    assert "output_preview" not in caught.value.detail


def test_parent_rejects_roster_refusal_shape_swap_with_identity() -> None:
    packet, _config_value, _target, _skill, _mmms = _packet()
    result = runner.execute_packet(packet.packet_bytes)
    tampered = _tamper_lens_roster(
        packet.packet_bytes,
        result.return_zip_bytes,
        lens="likely_failure",
        mutate=lambda roster: roster.update(
            {"schema": "constraintbox.md-agent-roster-refusal.v1"}
        ),
    )
    with pytest.raises(Exception) as caught:
        runner.validate_premortem_zip_wave_return(packet.packet_bytes, tampered)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_ROSTER_SCHEMA"
    detail = json.loads(caught.value.detail)
    assert detail["reason"] == "schema"
    assert detail["observed_schema"] == "constraintbox.md-agent-roster-refusal.v1"
    assert detail["lens"] == "likely_failure"


def test_refusal_wrapper_redacts_provider_preview_and_keeps_field_delta() -> None:
    raw = {
        "schema": "constraintbox.md-agent-roster-refusal.v1",
        "run_id": "fixture-run",
        "max_attempts": 1,
        "accepted_agent_ids": [],
        "refusal_reason_summary": {"REFUSE_MD_AGENT_OUTPUT_SCHEMA": 1},
        "exhausted_agents": [
            {
                "agent_id": "lik-0",
                "output_path": "output/lik-0.md",
                "terminal_refusal": "REFUSE_MD_AGENT_OUTPUT_SCHEMA",
                "attempts": [
                    {
                        "attempt": 1,
                        "provider_request_id": "request-1",
                        "output_sha256": "a" * 64,
                        "refusal_reason": "REFUSE_MD_AGENT_OUTPUT_SCHEMA",
                        "cell_missing_fields": ["warning"],
                        "cell_extra_fields": ["provider_extra"],
                        "output_preview": "provider prose must not survive",
                    }
                ],
            }
        ],
    }
    detail = runner._bounded_refusal_detail(
        "REFUSE_MD_AGENT_ROSTER_EXHAUSTED",
        json.dumps(raw),
        config=_config(),
    )
    parsed = json.loads(detail)
    assert parsed["exhausted_agents"][0]["output_path"] == "output/lik-0.md"
    assert parsed["exhausted_agents"][0]["attempts"][0]["cell_missing_fields"] == ["warning"]
    assert parsed["exhausted_agents"][0]["attempts"][0]["cell_extra_fields"] == ["provider_extra"]
    assert "output_preview" not in detail
    assert "provider prose" not in detail


def test_malformed_cell_json_is_refused_by_cell_validator() -> None:
    with pytest.raises(Exception) as caught:
        runner._cell_fields({"schema": runner.CELL_SCHEMA}, lens="likely_failure", target_digest="a" * 64)
    assert getattr(caught.value, "reason_code", "") == "REFUSE_PREMORTEM_OUTPUT_SCHEMA"


def test_cell_field_set_refusal_reports_sorted_identity_and_delta() -> None:
    value = {key: "x" for key in runner.PREMORTEM_CELL_FIELDS}
    value.pop("warning")
    value["provider_extra"] = "ignored"
    with pytest.raises(Exception) as caught:
        runner._cell_fields(
            value,
            lens="hidden_assumption",
            target_digest="a" * 64,
            member_id="hid-0",
            output_path="output/hid-0.md",
        )
    detail = json.loads(caught.value.detail)
    assert detail["lens"] == "hidden_assumption"
    assert detail["member_id"] == "hid-0"
    assert detail["output_path"] == "output/hid-0.md"
    assert detail["missing_fields"] == ["warning"]
    assert detail["extra_fields"] == ["provider_extra"]


def test_config_max_attempts_is_bound_in_wave_lens_and_roster_manifests() -> None:
    target, skill, mmms = _inputs()
    config = _config()
    config["max_attempts"] = 1
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    root = _entries(packet.packet_bytes)
    wave = json.loads(root["inputs/wave_manifest.json"])

    assert wave["max_attempts"] == 1
    for lens in runner.LENSES:
        assert wave["lenses"][runner.LENSES.index(lens)]["max_attempts"] == 1
        child = _entries(root[f"children/{lens}.zip"])
        assert json.loads(child["input/lens_manifest.json"])["max_attempts"] == 1
        assert json.loads(child["inputs/roster.json"])["max_attempts"] == 1


def test_parent_lens_and_compiled_receipts_preserve_retry_summaries() -> None:
    target, skill, mmms = _inputs()
    config = _config(mode="invalid-json")
    packet = runner.build_premortem_zip_wave_packet(
        config=config, target=target, skill=skill, mmm_sources=mmms
    )
    result = runner.execute_packet(packet.packet_bytes)
    receipt = runner.validate_premortem_zip_wave_return(
        packet.packet_bytes, result.return_zip_bytes
    )

    assert receipt["max_attempts"] == config["max_attempts"]
    assert len(receipt["attempt_summaries"]) == 6
    assert len(receipt["compiled"]["attempt_summaries"]) == 6
    assert all(
        lens["max_attempts"] == config["max_attempts"]
        for lens in receipt["lens_receipts"]
    )
    assert receipt["compiled"]["max_attempts"] == config["max_attempts"]
    assert receipt["compiled"]["refusal_reason_summary"] == {
        "REFUSE_MD_AGENT_OUTPUT_JSON": 6,
    }
    assert receipt["mmm_read_proved"] is False
    assert receipt["skill_read_proved"] is False
    assert receipt["skill_executed"] is False
    assert receipt["skill_echo_proved"] is True
    assert receipt["mmm_echo_proved"] is True
    assert receipt["tool_echo_proved"] is True
    assert receipt["accepted_attempt_count"] == 6
    assert receipt["accepted_attempts_consumed"] == 12
    assert receipt["refusal_reason_summary"] == {
        "REFUSE_MD_AGENT_OUTPUT_JSON": 6,
    }
    for lens in receipt["lens_receipts"]:
        assert len(lens["attempt_summaries"]) == 2
        assert all(
            summary["accepted_attempt_count"] == 2
            and summary["refusal_reason_summary"] == {"REFUSE_MD_AGENT_OUTPUT_JSON": 1}
            for summary in lens["attempt_summaries"]
        )
        assert lens["mmm_read_proved"] is False
        assert lens["skill_bytes_delivered"] is True
        assert lens["skill_read_proved"] is False
        assert lens["skill_executed"] is False
        assert lens["skill_echo_proved"] is True
        assert lens["mmm_echo_proved"] is True
        assert lens["tool_echo_proved"] is True


def test_absent_repair_callback_has_distinct_stop_reason() -> None:
    target, skill, mmms = _inputs()
    result = runner.run_premortem_zip_wave(
        config=_config(), target=target, skill=skill, mmm_sources=mmms
    )

    assert result["stop_reason"] == "repair_callback_absent"
    assert result["mmm_read_proved"] is False
    assert result["skill_read_proved"] is False
    assert result["skill_executed"] is False
    assert result["skill_echo_proved"] is True
    assert result["mmm_echo_proved"] is True
    assert result["tool_echo_proved"] is True
    assert result["accepted_attempt_count"] == 6
    assert result["accepted_attempts_consumed"] == 6
    assert result["refusal_reason_summary"] == {}
