from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.run_context_strategy import run_wave


def _layout(tmp_path: Path) -> Path:
    root = tmp_path / "box"
    prompts = root / "prompts"
    outputs = root / "outputs"
    prompts.mkdir(parents=True)
    outputs.mkdir()
    (prompts / "owner.md").write_text(
        "> Failure is its own full wave.\n"
        "> falsification is deductive.\n"
        "> induction keeps an antichain.\n",
        encoding="utf-8",
    )
    (outputs / "receipt.json").write_text(
        json.dumps(
            {
                "operation": "finite_time_first_seed_validation.v1",
                "status": "PASS",
                "reason": "REFUSE_ORDER_GAP_COLLAPSED",
            }
        ),
        encoding="utf-8",
    )
    return root


def test_ready_snapshot_keeps_corpora_apart(tmp_path: Path) -> None:
    root = _layout(tmp_path)
    dest = tmp_path / "out" / "receipt.json"
    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=dest,
    )
    assert receipt["status"] == "CONTEXT_SNAPSHOT_READY"
    assert receipt["admission_disposition"] == "demote_RUNTIME_ONLY"
    assert receipt["mmm_read_proved"] is False
    user = json.loads(Path(receipt["user_mmm_draft"]).read_text(encoding="utf-8"))
    project = json.loads(Path(receipt["project_mmm_draft"]).read_text(encoding="utf-8"))
    assert user["source"] == "user_prompts_only"
    assert project["source"] == "project_outputs_only"
    assert "Failure is its own full wave." in user["distinctions"]
    assert "finite_time_first_seed_validation.v1" in project["tokens"]
    assert "REFUSE_ORDER_GAP_COLLAPSED" in project["tokens"]


def test_merge_and_admit_refuse(tmp_path: Path) -> None:
    root = _layout(tmp_path)
    merged = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "merge.json",
        merge=True,
    )
    assert merged["status"] == "REFUSE"
    assert merged["reason"] == "REFUSE_MERGED_CORPORA"
    admitted = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "admit.json",
        admit=True,
    )
    assert admitted["status"] == "REFUSE"
    assert admitted["reason"] == "REFUSE_DRAFT_AS_LAW"


def test_pasted_material_stays_out_of_user_mmm(tmp_path: Path) -> None:
    root = _layout(tmp_path)
    (root / "prompts" / "owner.md").write_text(
        "## 1.  2026-08-08 00:18:06  — pasted material, not typed\n"
        "> Agreed, and the fix is a runner that doesn't need a turn between steps.\n"
        "\n"
        "## 2.  2026-08-08 03:48:31\n"
        "> Failure is its own full wave.\n",
        encoding="utf-8",
    )
    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "attr.json",
    )
    assert receipt["status"] == "CONTEXT_SNAPSHOT_READY"
    assert receipt["speaker_filter"] == "owner_typed"
    assert receipt["owner_pasted_quote_count"] == 1
    assert receipt["owner_typed_quote_count"] == 1
    user = json.loads(Path(receipt["user_mmm_draft"]).read_text(encoding="utf-8"))
    assert "Failure is its own full wave." in user["distinctions"]
    assert "Agreed, and the fix is a runner that doesn't need a turn between steps." not in user["distinctions"]


def test_overlap_holds(tmp_path: Path) -> None:
    root = _layout(tmp_path)
    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts"), Path("outputs")],
        output_paths=[Path("outputs")],
        out=tmp_path / "overlap.json",
    )
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_CORPUS_OVERLAP"


def _write_event(
    path: Path,
    *,
    event_type: str,
    text: str,
    event_id: str,
    source_kind: str,
    role: str | None = None,
) -> None:
    source = {"kind": source_kind, "locator": f"fixture://{event_id}"}
    if role is not None:
        source["role"] = role
    row = {
        "event": {
            "event_id": event_id,
            "event_type": event_type,
            "material": {
                "text": text,
                "sha256": __import__("hashlib").sha256(text.encode()).hexdigest(),
            },
            "source": source,
        },
        "source_line_sha256": event_id * 8,
        "source_sequence": int(event_id.rsplit("-", 1)[-1]),
    }
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row) + "\n")


def test_jsonl_partitions_owner_and_project_with_custody_refs(tmp_path: Path) -> None:
    root = tmp_path / "box"
    prompts = root / "prompts"
    outputs = root / "outputs"
    prompts.mkdir(parents=True)
    outputs.mkdir()
    events = prompts / "context.jsonl"
    _write_event(
        events,
        event_type="OWNER_PROMPT",
        text="Keep the prompt and project corpora separate.",
        event_id="owner-1",
        source_kind="codex_rollout_message",
        role="user",
    )
    _write_event(
        events,
        event_type="OWNER_PROMPT",
        text="<recommended_plugins>\nplatform supplied material\n",
        event_id="pseudo-2",
        source_kind="codex_rollout_message",
        role="user",
    )
    _write_event(
        events,
        event_type="OWNER_PROMPT",
        text="# AGENTS.md instructions\nplatform supplied instructions\n",
        event_id="pseudo-3",
        source_kind="codex_rollout_message",
        role="user",
    )
    _write_event(
        events,
        event_type="ASSISTANT_OBSERVATION",
        text="The route is constraintbox.repo-consolidation.v1 and remains HOLD_TEST.",
        event_id="project-4",
        source_kind="codex_rollout_message",
        role="assistant",
    )
    _write_event(
        events,
        event_type="OWNER_DIRECTIVE_IMPORTED",
        text="Imported owner material remains context, not typed voice.",
        event_id="imported-5",
        source_kind="local_file",
    )
    (outputs / "receipt.json").write_text(
        '{"operation":"constraintbox.context-strategy-receipt.v1"}', encoding="utf-8"
    )

    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "jsonl.json",
    )

    assert receipt["status"] == "CONTEXT_SNAPSHOT_READY"
    assert receipt["owner_material_count"] == 1
    assert receipt["project_material_count"] == 3
    assert receipt["pseudo_owner_excluded_count"] == 2
    assert receipt["selection"]["owner"]["method"] == "unique_content_evenly_spaced_source_order"
    assert "constraintbox.repo-consolidation.v1" in json.loads(
        Path(receipt["project_mmm_draft"]).read_text(encoding="utf-8")
    )["tokens"]
    user = json.loads(Path(receipt["user_mmm_draft"]).read_text(encoding="utf-8"))
    assert user["distinction_sources"][0]["event_id"] == "owner-1"
    assert user["distinction_sources"][0]["material_sha256"]
    assert "must_not_lose" not in user
    assert "must_not_lose" not in receipt


def test_jsonl_empty_owner_extraction_holds(tmp_path: Path) -> None:
    root = tmp_path / "box"
    prompts = root / "prompts"
    outputs = root / "outputs"
    prompts.mkdir(parents=True)
    outputs.mkdir()
    _write_event(
        prompts / "context.jsonl",
        event_type="ASSISTANT_OBSERVATION",
        text="constraintbox.project-event.v1",
        event_id="project-1",
        source_kind="codex_rollout_message",
        role="assistant",
    )
    (outputs / "receipt.json").write_text(
        '{"operation":"constraintbox.project-event.v1"}', encoding="utf-8"
    )
    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "empty-owner.json",
    )
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_OWNER_EXTRACTION_EMPTY"
    assert receipt["empty_extractions"] == ["owner"]


def test_jsonl_empty_project_extraction_holds(tmp_path: Path) -> None:
    root = tmp_path / "box"
    prompts = root / "prompts"
    outputs = root / "outputs"
    prompts.mkdir(parents=True)
    outputs.mkdir()
    _write_event(
        prompts / "context.jsonl",
        event_type="OWNER_PROMPT",
        text="Keep exact owner material.",
        event_id="owner-1",
        source_kind="owner_verbatim",
    )
    (outputs / "plain.txt").write_text("No schema or reason code here.", encoding="utf-8")
    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "empty-project.json",
    )
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_PROJECT_EXTRACTION_EMPTY"
    assert receipt["empty_extractions"] == ["project"]


def test_jsonl_material_digest_tamper_holds(tmp_path: Path) -> None:
    root = tmp_path / "box"
    prompts = root / "prompts"
    outputs = root / "outputs"
    prompts.mkdir(parents=True)
    outputs.mkdir()
    path = prompts / "context.jsonl"
    _write_event(
        path,
        event_type="OWNER_PROMPT",
        text="Keep the exact owner bytes.",
        event_id="owner-1",
        source_kind="owner_verbatim",
    )
    raw = path.read_text(encoding="utf-8")
    path.write_text(raw.replace('"sha256": "', '"sha256": "' + "0" * 64, 1), encoding="utf-8")
    (outputs / "receipt.json").write_text(
        '{"operation":"constraintbox.project-event.v1"}', encoding="utf-8"
    )
    receipt = run_wave(
        root=root,
        prompt_paths=[Path("prompts")],
        output_paths=[Path("outputs")],
        out=tmp_path / "tamper.json",
    )
    assert receipt["status"] == "HOLD"
    assert receipt["reason"] == "HOLD_JSONL_PARSE"
    assert "sha256" in receipt["error"]
