from __future__ import annotations

import importlib.util
import json
import shutil
from pathlib import Path
from typing import Any, Mapping


SYSTEM = Path(__file__).resolve().parents[1]
SCRIPT = SYSTEM / "scripts" / "run_cumulative_waves.py"
SPEC = importlib.util.spec_from_file_location("integrated_cumulative_waves", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
scheduler = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scheduler)


def _fixture(tmp_path: Path) -> Path:
    system = tmp_path / "integrated_system"
    (system / "config").mkdir(parents=True)
    shutil.copy2(
        SYSTEM / "config" / "CUMULATIVE_WAVE_SEQUENCE.json",
        system / "config" / "CUMULATIVE_WAVE_SEQUENCE.json",
    )
    (system / "scripts").mkdir(parents=True)
    (system / "scripts" / "run_wave.py").write_text(
        "# fixture public runner; tests inject the callable\n", encoding="utf-8"
    )
    skills = system / "skills"
    skills.mkdir(parents=True)
    rows: list[dict[str, str]] = []
    for stage_id in (
        "cb-maintenance-wave",
        "cb-context-strategy-wave",
        "cb-exploration-wave",
    ):
        stage_dir = skills / stage_id
        stage_dir.mkdir(parents=True)
        script = stage_dir / "run.py"
        definition = stage_dir / "wave.json"
        script.write_text(f"# {stage_id}\n", encoding="utf-8")
        definition.write_text(json.dumps({"wave_id": stage_id}) + "\n", encoding="utf-8")
        rows.append(
            {
                "wave_id": stage_id,
                "script": f"skills/{stage_id}/run.py",
                "definition": f"skills/{stage_id}/wave.json",
                "script_sha256": scheduler.sha256_path(script),
                "definition_sha256": scheduler.sha256_path(definition),
            }
        )
    (skills / "ACTIVE_WAVES.json").write_text(
        json.dumps({"schema": "constraintbox.active-wave-set.v1", "runnable_cohort": rows}) + "\n",
        encoding="utf-8",
    )
    (system / "runs").mkdir()
    return system


def _runner(
    calls: list[str],
    *,
    unstable: bool = False,
    hold: bool = False,
    cancel_after: int | None = None,
    worktree_drift: bool = False,
):
    def run(
        stage_id: str,
        *,
        system_root: Path,
        output_dir: Path,
        timeout_seconds: float,
        cancel_file: Path | None,
        run_id: str,
        python_executable: Path | None,
    ) -> Mapping[str, Any]:
        calls.append(stage_id)
        if cancel_after is not None and len(calls) >= cancel_after and cancel_file is not None:
            cancel_file.parent.mkdir(parents=True, exist_ok=True)
            cancel_file.write_text("cancel\n", encoding="utf-8")
        child = {
            "status": "ANTICHAIN_OPEN",
            "source_digest": "source-stable",
            "context_digest": "context-stable",
            "seed_digest": "seed-stable",
            "reading_count": 8,
            "family_count": 7,
            "antichain_ids": ["R-layer-order", "R-lr-order-scar"],
            "antichain_digest": "antichain-stable",
            "distinguish_packet_digest": "packet-stable",
            "hidden_third": "R-lr-two-manifolds",
            "winner_selected": False,
            "new_rival_readings": 8,
            "epistemology": {"this_wave": "induction_harvest"},
            "diagnostics": {
                "git": {
                    "available": True,
                    "changed_count": 4,
                    "worktrees": [
                        {
                            "path": "sibling-worktree",
                            "head": "abc123",
                            "branch": "fixture",
                            "status": {"changed_count": 0},
                        }
                    ],
                }
            },
            "candidate_decisions": [{"classification": "KEEP_ACTIVE"}],
            "blockers": [],
            "mutation_performed": False,
            "prompt_corpus_digest": "prompt-stable",
            "output_corpus_digest": "output-stable",
            "project_mmm_draft_digest": "project-stable",
            "user_mmm_draft_digest": "user-stable",
            "owner_source_digest": "owner-source-stable",
            "project_source_digest": "project-source-stable",
            "prompt_file_count": 2,
            "output_file_count": 2,
        }
        if unstable:
            child["source_digest"] = f"source-{len(calls)}"
        if worktree_drift:
            child["diagnostics"]["git"]["worktrees"][0]["status"]["changed_count"] = len(calls)
        if hold:
            return {
                "status": "HOLD",
                "reason_code": "HOLD_FIXTURE",
                "child_status": "HOLD_FIXTURE",
                "child_reason": "fixture",
                "child": child,
                "timestamp": len(calls),
            }
        reason = f"round-{len(calls)}" if unstable else None
        return {
            "status": "PASS",
            "reason_code": None,
            "child_status": "READY" if stage_id == "cb-maintenance-wave" else "CONTEXT_SNAPSHOT_READY",
            "child_reason": reason,
            "child": child,
            "timestamp": len(calls),
        }

    return run


def test_prefix_one_then_prefix_two_order_and_locked_stop(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="ordered",
        child_runner=_runner(calls),
    )

    assert result["status"] == "LOCKED"
    assert result["reason_code"] == "LOCKED_STAGE"
    assert calls == [
        "cb-maintenance-wave",
        "cb-maintenance-wave",
        "cb-maintenance-wave",
        "cb-context-strategy-wave",
        "cb-maintenance-wave",
        "cb-context-strategy-wave",
    ]
    assert [row["status"] for row in result["prefixes"]] == [
        "PASS",
        "PASS",
        "LOCKED",
    ]
    assert result["prefixes"][0]["stabilized"] is True
    assert result["prefixes"][1]["stabilized"] is True
    locked = result["prefixes"][2]
    assert locked["blocked_stage_id"] == "cb-premortem-wave"
    assert locked["stage_records"][0]["status"] == "NOT_RUN"
    assert locked["stage_records"][2]["status"] == "LOCKED"
    assert all(not row["executed"] for row in locked["stage_records"])
    profile = scheduler.load_config(system / "config" / "CUMULATIVE_WAVE_SEQUENCE.json")["profiles"]["light"]
    assert profile["stages"]["cb-exploration-wave"]["mode"] == "ACTIVE"
    assert "cb-exploration-wave" in profile["active_stage_ids"]
    assert profile["stage_order"].index("cb-exploration-wave") > profile["stage_order"].index("cb-premortem-wave")
    assert result["source_binding"]["active_waves"]["cb-exploration-wave"]["valid"] is True
    assert "cb-exploration-wave" not in calls
    assert (system / "runs" / "cumulative" / "ordered" / "receipt.json").is_file()


def test_timestamp_noise_is_not_part_of_semantic_stability(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="timestamp-noise",
        child_runner=_runner(calls),
    )
    first_prefix = result["prefixes"][0]
    assert first_prefix["stable_round"] == 2
    projections = [round_row["stages"][0]["semantic_projection"] for round_row in first_prefix["rounds"]]
    assert projections[0] == projections[1]
    assert all("timestamp" not in projection for projection in projections)


def test_prefix_round_cap_holds_and_does_not_enter_next_prefix(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="cap",
        child_runner=_runner(calls, unstable=True),
    )

    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_PREFIX_ROUND_CAP"
    assert result["prefixes"][-1]["prefix_id"] == "prefix-1"
    assert len(result["prefixes"][0]["rounds"]) == 3
    assert calls == ["cb-maintenance-wave"] * 3


def test_sibling_worktree_drift_prevents_semantic_stability(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="worktree-drift",
        child_runner=_runner(calls, worktree_drift=True),
    )

    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_PREFIX_ROUND_CAP"
    assert calls == ["cb-maintenance-wave"] * 3
    projections = [
        row["stages"][0]["semantic_projection"]
        for row in result["prefixes"][0]["rounds"]
    ]
    assert all("child.diagnostics.git.worktrees" in projection for projection in projections)
    assert len({projection["child.diagnostics.git.worktrees"][0]["status"]["changed_count"] for projection in projections}) == 3


def test_hold_child_stops_without_silent_later_stage(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="hold",
        child_runner=_runner(calls, hold=True),
    )

    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_CHILD_STATUS"
    assert calls == ["cb-maintenance-wave"]
    stage_records = result["prefixes"][0]["rounds"][0]["stages"]
    assert stage_records[0]["status"] == "HOLD"
    assert all(row["status"] == "NOT_RUN" for row in stage_records[1:])
    assert all(row["reason_code"] == "PREFIX_STOPPED_AFTER_FAILURE" for row in stage_records[1:])


def test_cancellation_before_and_during_run_is_receipted(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    cancel = system / "runs" / "cancel.flag"
    cancel.write_text("cancel\n", encoding="utf-8")
    calls: list[str] = []
    before = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="cancel-before",
        cancel_file=cancel,
        child_runner=_runner(calls),
    )
    assert before["status"] == "CANCELLED"
    assert before["reason_code"] == "CANCELLED_BEFORE_RUN"
    assert calls == []

    cancel.unlink()
    during_calls: list[str] = []
    during = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="cancel-during",
        cancel_file=cancel,
        child_runner=_runner(during_calls, cancel_after=1),
    )
    assert during["status"] == "CANCELLED"
    assert during["reason_code"] == "CANCELLED_DURING_PREFIX"
    assert during_calls == ["cb-maintenance-wave"]


def test_output_escape_is_refused_in_contained_fallback(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        output_dir=tmp_path / "outside",
        run_id="escape",
        child_runner=_runner(calls),
    )
    assert result["status"] == "REFUSE"
    assert result["reason_code"] == "OUTPUT_OUTSIDE_PRODUCT"
    assert calls == []
    assert result["output_path"].startswith("runs/cumulative/refused/")


def test_manifest_expected_source_digest_mismatch_holds_before_spawn(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    manifest_path = system / "skills" / "ACTIVE_WAVES.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["runnable_cohort"][0]["script_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="source-mismatch",
        child_runner=_runner(calls),
    )
    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_SOURCE_BINDING_INCOMPLETE"
    assert calls == []
    assert result["source_binding"]["active_waves"]["cb-maintenance-wave"]["reason"] == (
        "HOLD_SCRIPT_DIGEST_MISMATCH"
    )


def test_manifest_scheduler_drift_holds_before_spawn(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    manifest_path = system / "skills" / "ACTIVE_WAVES.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["runnable_cohort"] = [
        row
        for row in manifest["runnable_cohort"]
        if row["wave_id"] != "cb-exploration-wave"
    ]
    manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="manifest-drift",
        child_runner=_runner(calls),
    )

    assert result["status"] == "HOLD"
    assert result["reason_code"] == "HOLD_MANIFEST_SCHEDULER_DRIFT"
    assert calls == []
    alignment = result["source_binding"]["manifest_scheduler_alignment"]
    assert alignment["manifest_only"] == []
    assert alignment["scheduler_only"] == ["cb-exploration-wave"]
    assert alignment["valid"] is False


def test_heavy_profile_is_separate_and_stops_at_same_locked_boundary(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        "heavy",
        system_root=system,
        run_id="heavy",
        child_runner=_runner(calls),
    )
    assert result["runtime"] == "CB_HEAVY"
    assert result["status"] == "LOCKED"
    assert calls[:2] == ["cb-maintenance-wave", "cb-maintenance-wave"]


def test_human_summary_is_compact_and_receipt_derived(tmp_path: Path) -> None:
    system = _fixture(tmp_path)
    calls: list[str] = []
    result = scheduler.run_cumulative_waves(
        system_root=system,
        run_id="summary",
        child_runner=_runner(calls),
    )
    summary = scheduler.compile_human_summary(result)
    assert summary["status"] == "LOCKED"
    assert summary["full_receipt"] == result["output_path"]
    assert summary["execution"]["provider_model_calls"] == 0
    assert summary["execution"]["llm_agents"] == 0
    assert summary["execution"]["model_free_wave_executions"] == len(calls)
    assert [item["status"] for item in summary["prefixes"]] == [
        "PASS",
        "PASS",
        "LOCKED",
    ]
    assert "source_binding" not in summary
