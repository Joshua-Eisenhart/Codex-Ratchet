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
