from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "codex_harness_adapter.py"


def load_module():
    spec = importlib.util.spec_from_file_location("codex_harness_adapter", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("unable to load codex_harness_adapter module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def salience_payload(rows: list[dict] | None = None) -> dict:
    return {
        "schema": {
            "fields": ["id", "term", "weight", "row_type", "gloss", "provenance"],
            "variant_semantics": "independent_v2_7_variant",
        },
        "words": rows
        if rows is not None
        else [
            {
                "id": 1,
                "term": "plain",
                "weight": 100,
                "row_type": "aligned",
                "gloss": "fixture salience: plain",
                "provenance": "test_fixture",
            }
        ],
    }


def write_salience(path: Path, rows: list[dict] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, salience_payload(rows))


def make_packet_fixture(tmp_path: Path) -> Path:
    packet = tmp_path / "packet"
    boot = packet / "current"
    boot.mkdir(parents=True)
    for name in [
        "NEW_THREAD_POSITIVE_MMM_BOOT_PROMPT_v2_7.md",
        "SUBAGENT_POSITIVE_MINI_MMM_BOOT_PROMPT_v2_7.md",
        "SUBSUBAGENT_POSITIVE_MINI_MMM_BOOT_PROMPT_v2_7.md",
        "README_BOOT_ORDER_v2_7.md",
    ]:
        (boot / name).write_text("Load only positive salience material.\n", encoding="utf-8")

    boot_rules = packet / "boot_rules" / "json"
    boot_rules.mkdir(parents=True)
    write_json(boot_rules / "MAIN_AGENT_BOOT_RULES_v2_7.json", {"text": "Positive boot scope only."})

    write_salience(packet / "main_mmm" / "compact" / "json" / "MMM_MAIN_COMPACT_v2_7.json")
    write_salience(packet / "mini_mmms" / "compact" / "voices" / "json" / "MMM_VOICE_HUME_COMPACT_v2_7.json")
    (packet / "mini_mmms" / "compact" / "voices" / "md").mkdir(parents=True)
    (packet / "mini_mmms" / "compact" / "voices" / "md" / "MMM_VOICE_HUME_COMPACT_v2_7.md").write_text(
        "- plain :: 100 :: aligned :: test_fixture\n",
        encoding="utf-8",
    )
    return packet


def mini_mmm(path: Path) -> None:
    path.write_text(" ".join(f"word{i}" for i in range(120)), encoding="utf-8")


def receipt(lane: str) -> dict:
    return {
        "lane": lane,
        "checked": "checked source",
        "concluded": "concluded result",
        "open": "open risk",
        "evidence": "evidence path",
    }


def spawned_row(lane: str, mini_path: Path, receipt_path: str) -> dict:
    return {
        "lane": lane,
        "emoji": "",
        "role": "bounded task card",
        "wave": 1,
        "status": "spawned",
        "worker_id": f"worker-{lane}",
        "checked": "checked",
        "concluded": "concluded",
        "open": "open",
        "evidence": "evidence",
        "blocker_or_defer_reason": None,
        "wiki_harness_boot": "loaded",
        "mini_mmm_language_body": str(mini_path),
        "mini_mmm_path": str(mini_path),
        "mini_mmm_scope": "lane_local",
        "task_card": "task after mini MMM",
        "task_card_after_mini_mmm": True,
        "lane_resolution": "row",
        "runtime_registry": "runtime row",
        "worker_receipt": receipt_path,
        "audit": "audit row",
        "final_output_check": "final check",
        "receipt_path": receipt_path,
    }


def live_spawned_row(lane: str, mini_path: Path, receipt_path: str) -> dict:
    row = spawned_row(lane, mini_path, receipt_path)
    row["agent_id"] = f"019-live-{lane.lower().replace(' ', '-')}"
    row["runtime_registry"] = "codex native subagent spawned with route-local mini-MMM"
    return row


def deferred_row(lane: str) -> dict:
    return {
        "lane": lane,
        "emoji": "",
        "role": "child receipt truth",
        "wave": 6,
        "status": "deferred",
        "worker_id": None,
        "checked": "checked",
        "concluded": "deferred",
        "open": "open",
        "evidence": "evidence",
        "blocker_or_defer_reason": "bounded test fixture defers child execution",
    }


def all_d_child_rows() -> list[dict]:
    return [deferred_row(f"Follow-up {index}") for index in range(1, 18)] + [
        deferred_row("All-D self-check"),
        deferred_row("Follow-up Audit/Improve"),
    ]


def validate(tmp_path: Path, rows: list[dict], final_text: str):
    mod = load_module()
    lane_resolution = tmp_path / "lanes.jsonl"
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    final_answer = tmp_path / "final.md"
    final_answer.write_text(final_text, encoding="utf-8")
    write_jsonl(lane_resolution, rows)
    return mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=final_answer,
        allow_controller_local=False,
    )


def finding_codes(report: dict) -> set[str]:
    return {finding["code"] for finding in report["findings"]}


def test_visible_pushback_and_llm_council_require_registry_rows(tmp_path: Path):
    ok, report = validate(
        tmp_path,
        [deferred_row("Audit")],
        "**Main Answer**\nPushback found a weak assumption. LLM Council rejected readiness.\n",
    )

    assert not ok
    assert finding_codes(report) == {"missing_lane_resolution"}
    assert report["visible_lanes"] == ["LLM Council", "Pushback"]


def test_direct_all_d_requires_own_registry_row(tmp_path: Path):
    ok, report = validate(tmp_path, [], "**Main Answer**\nAll-D is blocked until wired.\n")

    assert not ok
    assert any(finding["detail"] == "All-D" for finding in report["findings"])


def test_option_18_aliases_to_all_d_registry_row(tmp_path: Path):
    ok, report = validate(tmp_path, [], "**Main Answer**\nOption 18 is blocked until All-D is wired.\n")

    assert not ok
    assert report["visible_lanes"] == ["All-D"]
    assert any(finding["detail"] == "All-D" for finding in report["findings"])


def test_followup_menu_mentions_do_not_count_as_executed_lanes(tmp_path: Path):
    ok, report = validate(
        tmp_path,
        [],
        "**Main Answer**\nNo visible lane ran.\n\n"
        "**🪄 Follow-up — choose scale**\n"
        "Prompt-local\n"
        "P1. Pushback\n   Outcome: boundary.\n   Use when: scope fails.\n   Stop/gate: boundary named.\n"
        "Context-scale\n"
        "S7. Systems\n   Outcome: loop.\n   Use when: recurrence appears.\n   Stop/gate: loop named.\n"
        "Guard compositions\n"
        "G10. Hygiene Guard\n   Outcome: readable.\n   Use when: output collapses.\n   Stop/gate: readable.\n"
        "All-of-above\n"
        "A16. All-D\n   Outcome: full run.\n   Use when: system changes.\n   Stop/gate: receipts.\n",
    )

    assert ok
    assert report["visible_lanes"] == []


def test_wizard_chat_contract_accepts_plain_text_followup_prework(tmp_path: Path):
    ok, report = validate(
        tmp_path,
        [deferred_row("Audit")],
        "🧙 Wizard 2.8 full: 12 wave slots scaffolded; true 12-wave run not executed; 0 live subagents; quality 91/100; local harness passed\n\n"
        "🧙 Main Answer\n"
        "The current answer is a chat output, not a report.\n\n"
        "🗣️ Voices\n"
        "The voices contribute without turning the body into a menu.\n\n"
        "📊 Quality Audit\n"
        "Quality Audit Score: 91/100 (pass)\n\n"
        "🪄 Follow-up\n"
        "Lane follow-ups\n"
        "L1. Direct\n"
        "   🪄 Follow-up: \"Do one bounded thing.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 90/100.\n"
        "   Audit: passes only with one proof gate.\n"
        "L2. Reframe\n"
        "   🪄 Follow-up: \"Restate the task.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 89/100.\n"
        "   Audit: passes only if the frame sharpens the move.\n"
        "L3. Alternative\n"
        "   🪄 Follow-up: \"Keep one alternate route.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 87/100.\n"
        "   Audit: passes only if assumptions differ.\n"
        "L4. Wildcard\n"
        "   🪄 Follow-up: \"Run one bounded probe.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 80/100.\n"
        "   Audit: passes only if it cannot contaminate the main path.\n"
        "L5. Hygiene\n"
        "   🪄 Follow-up: \"Clean the answer.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 93/100.\n"
        "   Audit: passes only if clarity improves.\n"
        "L6. Security\n"
        "   🪄 Follow-up: \"Check trust boundaries.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 95/100.\n"
        "   Audit: passes only if risky claims are handled.\n"
        "Composition follow-ups\n"
        "C5. Clean closeout\n"
        "   🪄 Follow-up: \"Rewrite as chat.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 91/100.\n"
        "   Audit: passes only if evidence is preserved.\n"
        "C6. Trust check\n"
        "   🪄 Follow-up: \"Test whether the answer is safe to trust.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 96/100.\n"
        "   Audit: passes only if evidence claims are not overstated.\n"
        "C7. Whole-context check\n"
        "   🪄 Follow-up: \"Check project fit.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 91/100.\n"
        "   Audit: passes only if one next action survives.\n"
        "C8. Behavior proof\n"
        "   🪄 Follow-up: \"Compare expected behavior against output.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 96/100.\n"
        "   Audit: passes only if there is a falsifier.\n"
        "C9. Full Wizard pass\n"
        "   🪄 Follow-up: \"Integrate the useful composition work.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 92/100.\n"
        "   Audit: passes only if body and follow-up stay separate.\n",
    )

    assert ok, report["findings"]


def test_wizard_chat_contract_rejects_body_compositions(tmp_path: Path):
    ok, report = validate(
        tmp_path,
        [],
        "🧙 Wizard 2.8 full: quality 91/100; local harness passed\n\n"
        "🧙 Main Answer\n"
        "Body answer.\n\n"
        "🗣️ Voices\n"
        "Voice answer.\n\n"
        "🔗 Compositions\n"
        "C19. All-A belongs in the body.\n\n"
        "📊 Quality Audit\n"
        "Quality Audit Score: 91/100 (pass)\n\n"
        "🪄 Follow-up\n"
        "Lane follow-ups\n"
        "L1. Direct\n"
        "   🪄 Follow-up: \"Do one bounded thing.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 90/100.\n"
        "   Audit: passes only with one proof gate.\n"
        "Composition follow-ups\n"
        "C5. Clean closeout\n"
        "   🪄 Follow-up: \"Rewrite as chat.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 91/100.\n"
        "   Audit: passes only if evidence is preserved.\n"
        "C9. Full Wizard pass\n"
        "   🪄 Follow-up: \"Integrate useful compositions.\"\n"
        "   Pre-run status/score: scouted, not executed as current work; 92/100.\n"
        "   Audit: passes only if boundaries hold.\n",
    )

    assert not ok
    assert {"body_compositions_section", "body_composition_option"} <= finding_codes(report)


def test_wizard_chat_contract_rejects_body_c5_without_compositions_heading(tmp_path: Path):
    ok, report = validate(
        tmp_path,
        [],
        "🧙 Wizard 2.8 full: quality 91/100; local harness passed\n\n"
        "🧙 Main Answer\n"
        "C5. Hygiene composition is being rendered in the body.\n\n"
        "🗣️ Voices\n"
        "Voice answer.\n\n"
        "📊 Quality Audit\n"
        "Quality Audit Score: 91/100 (pass)\n\n"
        "🪄 Follow-up\n"
        "Lane follow-ups\n"
        "L1. Direct\n"
        "   🪄 Follow-up: Do one bounded thing.\n"
        "   Pre-run status/score: scouted, not executed as current work; 90/100.\n"
        "   Audit: passes only with one proof gate.\n"
        "Composition follow-ups\n"
        "C5. Clean closeout\n"
        "   🪄 Follow-up: Rewrite as chat.\n"
        "   Pre-run status/score: scouted, not executed as current work; 91/100.\n"
        "   Audit: passes only if evidence is preserved.\n"
        "C9. Full Wizard pass\n"
        "   🪄 Follow-up: Integrate useful compositions.\n"
        "   Pre-run status/score: scouted, not executed as current work; 92/100.\n"
        "   Audit: passes only if boundaries hold.\n",
    )

    assert not ok
    assert "body_composition_option" in finding_codes(report)


def test_wizard_chat_contract_rejects_missing_fields_per_followup_option(tmp_path: Path):
    ok, report = validate(
        tmp_path,
        [deferred_row("Audit")],
        "🧙 Wizard 2.8 full: quality 91/100; local harness passed\n\n"
        "🧙 Main Answer\n"
        "Body answer.\n\n"
        "🗣️ Voices\n"
        "Voice answer.\n\n"
        "📊 Quality Audit\n"
        "Quality Audit Score: 91/100 (pass)\n\n"
        "🪄 Follow-up\n"
        "Lane follow-ups\n"
        "L1. Direct\n"
        "   🪄 Follow-up: Do one bounded thing.\n"
        "   Pre-run status/score: scouted, not executed as current work; 90/100.\n"
        "   Audit: passes only with one proof gate.\n"
        "L2. Reframe\n"
        "   🪄 Follow-up: Reframe the task.\n"
        "Composition follow-ups\n"
        "C5. Clean closeout\n"
        "   🪄 Follow-up: Rewrite as chat.\n"
        "   Pre-run status/score: scouted, not executed as current work; 91/100.\n"
        "   Audit: passes only if evidence is preserved.\n"
        "C9. Full Wizard pass\n"
        "   🪄 Follow-up: Integrate useful compositions.\n"
        "   Pre-run status/score: scouted, not executed as current work; 92/100.\n"
        "   Audit: passes only if boundaries hold.\n",
    )

    assert not ok
    assert "followup_option_missing_selection_field" in finding_codes(report)


def test_spawned_row_requires_full_spine_fields(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    row = spawned_row("Direct", mini, "direct.json")
    for field in [
        "wiki_harness_boot",
        "task_card",
        "lane_resolution",
        "runtime_registry",
        "worker_receipt",
        "audit",
        "final_output_check",
    ]:
        row.pop(field)

    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir(exist_ok=True)
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )

    assert not ok
    assert "missing_receipt_spine_fields" in finding_codes(report)


def test_completed_row_cannot_claim_not_spawned_runtime(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    row = spawned_row("Direct", mini, "direct.json")
    row["status"] = "completed"
    row["state"] = "completed"
    row["runtime_registry"] = "not spawned; behavior harness normalization only"
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )

    assert not ok
    assert "spawned_state_contradicts_runtime_registry" in finding_codes(report)


def test_local_receipt_state_requires_explicit_allowance(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    row = spawned_row("Direct", mini, "direct.json")
    row["status"] = "local_receipt"
    row["state"] = "local_receipt"
    row["worker_id"] = None
    row["runtime_registry"] = "not spawned; behavior harness normalization only"
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    denied_ok, denied_report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )
    allowed_ok, allowed_report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
        allow_local_receipt=True,
    )

    assert not denied_ok
    assert "local_receipt_not_allowed" in finding_codes(denied_report)
    assert allowed_ok, allowed_report["findings"]


def test_require_live_execution_rejects_local_receipts_even_when_allowed(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    row = spawned_row("Direct", mini, "direct.json")
    row["status"] = "local_receipt"
    row["state"] = "local_receipt"
    row["worker_id"] = None
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
        allow_local_receipt=True,
        require_live_execution=True,
    )

    assert not ok
    assert "live_execution_requires_spawned" in finding_codes(report)


def test_require_live_execution_requires_live_agent_id(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    row = spawned_row("Direct", mini, "direct.json")
    row["runtime_registry"] = "not spawned; behavior harness normalization only"
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
        require_live_execution=True,
    )

    assert not ok
    assert "missing_live_agent_id" in finding_codes(report)
    assert "live_execution_contradicts_runtime_registry" in finding_codes(report)


def test_require_live_execution_accepts_live_spawned_row(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    row = live_spawned_row("Direct", mini, "direct.json")
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
        require_live_execution=True,
    )

    assert ok, report["findings"]


def test_require_live_execution_requires_followup_scout_receipts(tmp_path: Path):
    mod = load_module()
    final_answer = tmp_path / "final.md"
    final_answer.write_text(
        "**Main Answer**\nNo visible route ran.\n\n"
        "**🪄 Follow-up**\n"
        "Prompt-local\n"
        "P1. Direct\n   Outcome: bounded move.\n   Use when: one action is enough.\n   Stop/gate: proof exists.\n"
        "Context-scale\n"
        "S7. Systems\n   Outcome: loop named.\n   Use when: recurrence matters.\n   Stop/gate: loop checked.\n"
        "Guard compositions\n"
        "G10. Hygiene Guard\n   Outcome: cleaner output.\n   Use when: drift appears.\n   Stop/gate: clarity improves.\n"
        "All-of-above\n"
        "A16. All-D\n   Outcome: full route.\n   Use when: many routes matter.\n   Stop/gate: receipts exist.\n"
        "L1. Direct\n"
        "   Pre-run status/score: scouted, not executed as current work; 94/100.\n",
        encoding="utf-8",
    )
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [])
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()

    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=final_answer,
        allow_controller_local=False,
        require_live_execution=True,
    )

    assert not ok
    assert report["followup_scout_claims"] == ["L1"]
    assert "missing_followup_scout_receipt" in finding_codes(report)


def test_receipt_file_must_exist_for_spawned_rows(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    row = spawned_row("Direct", mini, "direct.json")
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )

    assert not ok
    assert "missing_receipt_file" in finding_codes(report)


def test_receipt_json_must_be_valid_object_with_matching_lane(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    row = spawned_row("Direct", mini, "direct.json")
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])
    (receipts_dir / "direct.json").write_text("{broken", encoding="utf-8")

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )
    assert not ok
    assert "invalid_receipt_json" in finding_codes(report)

    write_json(receipts_dir / "direct.json", {"lane": "Direct"})
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )
    assert not ok
    assert "missing_receipt_fields" in finding_codes(report)

    write_json(receipts_dir / "direct.json", receipt("Hume"))
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )
    assert not ok
    assert "receipt_lane_mismatch" in finding_codes(report)


def test_spawned_row_requires_lane_local_mini_mmm(tmp_path: Path):
    mini = tmp_path / "direct.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "direct.json", receipt("Direct"))
    row = spawned_row("Direct", mini, "direct.json")
    row["mini_mmm_scope"] = "main_only"
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )

    assert not ok
    assert "missing_lane_local_mini_mmm" in finding_codes(report)


def test_blocked_or_deferred_rows_require_reason(tmp_path: Path):
    row = {
        "lane": "All-D",
        "emoji": "",
        "role": "full wizard bundle",
        "wave": 0,
        "status": "blocked",
        "worker_id": None,
        "checked": "checked",
        "concluded": "concluded",
        "open": "open",
        "evidence": "evidence",
        "blocker_or_defer_reason": None,
    }
    ok, report = validate(tmp_path, [row], "**Main Answer**\nAll-D is blocked.\n")

    assert not ok
    assert "missing_block_or_defer_reason" in finding_codes(report)


def test_blocked_all_d_requires_child_rows_too(tmp_path: Path):
    row = {
        "lane": "All-D",
        "emoji": "",
        "role": "full wizard bundle",
        "wave": 0,
        "status": "blocked",
        "worker_id": None,
        "checked": "checked",
        "concluded": "blocked",
        "open": "open",
        "evidence": "evidence",
        "blocker_or_defer_reason": "capacity",
    }
    ok, report = validate(tmp_path, [row], "**Main Answer**\nAll-D is blocked.\n")

    assert not ok
    assert "missing_all_d_child_rows" in finding_codes(report)


def test_valid_spawned_all_d_passes(tmp_path: Path):
    mini = tmp_path / "all_d.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "all_d.json", receipt("All-D"))
    row = spawned_row("All-D", mini, "all_d.json")
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row, *all_d_child_rows()])
    final_answer = tmp_path / "final.md"
    final_answer.write_text("**Main Answer**\nAll-D ran with a receipt.\n", encoding="utf-8")

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=final_answer,
        allow_controller_local=False,
    )

    assert ok, report["findings"]
    assert report["visible_lanes"] == ["All-D"]


def test_spawned_all_d_requires_child_rows(tmp_path: Path):
    mini = tmp_path / "all_d.md"
    mini_mmm(mini)
    receipts_dir = tmp_path / "receipts"
    receipts_dir.mkdir()
    write_json(receipts_dir / "all_d.json", receipt("All-D"))
    row = spawned_row("All-D", mini, "all_d.json")
    lane_resolution = tmp_path / "lanes.jsonl"
    write_jsonl(lane_resolution, [row])

    mod = load_module()
    ok, report = mod.validate(
        lane_resolution_path=lane_resolution,
        receipts_dir=receipts_dir,
        final_answer_path=None,
        allow_controller_local=False,
    )

    assert not ok
    assert "missing_all_d_child_rows" in finding_codes(report)


def test_behavior_audit_flags_excluded_agency_terms():
    mod = load_module()

    findings = mod.audit_behavior_text(
        "This produces a smooth story and creates fake certainty.",
        label="main-output",
        source_kind="output",
    )

    assert [finding.code for finding in findings] == ["excluded_agency_terms"]
    assert "produces=1" in findings[0].detail
    assert "creates=1" in findings[0].detail


def test_behavior_audit_flags_hume_jargon_source():
    mod = load_module()

    findings = mod.audit_behavior_text(
        "impression, idea, custom, habit, constant conjunction",
        label="hume-source",
        source_kind="source",
        check_hume_jargon=True,
    )

    assert {finding.code for finding in findings} == {"hume_jargon_terms"}
    assert "constant conjunction=1" in findings[0].detail


def test_behavior_audit_flags_unsupported_status_leakage():
    mod = load_module()

    findings = mod.audit_behavior_text(
        "The lower engine path is back to passing and the Axis 0 control bridge exists.",
        label="contract-output",
        source_kind="output",
    )

    assert {finding.code for finding in findings} == {"unsupported_status_claims"}
    assert "axis 0 control bridge exists" in findings[0].detail


def test_behavior_audit_accepts_clean_hume_target_shape():
    mod = load_module()

    findings = mod.audit_behavior_text(
        "The repair is a candidate. Keep it plain, compare it under use, and only promote parts that preserve receipt truth.",
        label="hume-output",
        source_kind="output",
        check_hume_jargon=True,
    )

    assert findings == []


def test_packet_audit_scans_main_and_hume_surfaces(tmp_path: Path):
    mod = load_module()
    packet = tmp_path / "packet"
    main = packet / "main_mmm" / "full" / "md"
    hume = packet / "mini_mmms" / "full" / "voices" / "md"
    other = packet / "mini_mmms" / "full" / "voices" / "md"
    main.mkdir(parents=True)
    hume.mkdir(parents=True, exist_ok=True)
    other.mkdir(parents=True, exist_ok=True)
    (main / "MMM_MAIN_FULL.md").write_text("receipt truth creates overclaim", encoding="utf-8")
    (hume / "MMM_VOICE_HUME_FULL.md").write_text("plain habit custom", encoding="utf-8")
    (other / "MMM_VOICE_POPPER_FULL.md").write_text("creates ignored outside main/hume", encoding="utf-8")

    ok, report = mod.audit_packet_dir(packet)

    assert not ok
    assert len(report["scanned"]) == 2
    assert {finding["code"] for finding in report["findings"]} == {
        "excluded_agency_terms",
        "hume_jargon_terms",
    }


def test_audit_structure_command_accepts_minimal_v2_7_packet(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)

    exit_code = mod.main(["audit-structure", str(packet)])

    output = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert output["ok"] is True
    assert output["findings"] == []


def test_audit_structure_flags_invalid_json(tmp_path: Path):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)
    broken = packet / "main_mmm" / "compact" / "json" / "BROKEN.json"
    broken.write_text('{"not": "closed"', encoding="utf-8")

    ok, report = mod.audit_structure_dir(packet)

    assert not ok
    assert "invalid_json" in finding_codes(report)


def test_audit_structure_flags_missing_salience_row_fields(tmp_path: Path):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)
    write_salience(
        packet / "mini_mmms" / "compact" / "voices" / "json" / "MMM_VOICE_HUME_COMPACT_v2_7.json",
        [{"id": 1, "term": "plain", "weight": 100}],
    )

    ok, report = mod.audit_structure_dir(packet)

    assert not ok
    assert "missing_salience_row_fields" in finding_codes(report)


def test_audit_structure_accepts_clean_triplet_salience_rows(tmp_path: Path):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)
    write_salience(
        packet / "main_mmm" / "compact" / "json" / "MMM_MAIN_COMPACT_v2_7.json",
        [[1, "abstract", 100], [2, "measured", 95]],
    )

    ok, report = mod.audit_structure_dir(packet)

    assert "invalid_salience_row" not in finding_codes(report)
    assert "missing_salience_row_fields" not in finding_codes(report)


def test_audit_structure_flags_boot_critical_banned_terms(tmp_path: Path):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)
    boot = packet / "current" / "NEW_THREAD_POSITIVE_MMM_BOOT_PROMPT_v2_7.md"
    boot.write_text("Load the contrast reference and Audit surface.\n", encoding="utf-8")

    ok, report = mod.audit_structure_dir(packet)

    assert not ok
    assert "boot_critical_banned_terms" in finding_codes(report)


def test_audit_structure_flags_zero_width_joiner(tmp_path: Path):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)
    target = packet / "current" / "README_BOOT_ORDER_v2_7.md"
    target.write_text("Bad emoji joiner \u200d leak.\n", encoding="utf-8")

    ok, report = mod.audit_structure_dir(packet)

    assert not ok
    assert "zero_width_joiner" in finding_codes(report)


def test_audit_structure_flags_taxonomy_misplacement(tmp_path: Path):
    mod = load_module()
    packet = make_packet_fixture(tmp_path)
    misplaced = packet / "mini_mmms" / "compact" / "voices" / "json" / "MMM_VOICE_AUDIT_COMPACT_v2_7.json"
    write_salience(misplaced)

    ok, report = mod.audit_structure_dir(packet)

    assert not ok
    assert "taxonomy_misplacement" in finding_codes(report)
