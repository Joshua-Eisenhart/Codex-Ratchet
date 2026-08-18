from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "run_light_jax_wave_bridge.py"
SPEC = importlib.util.spec_from_file_location("run_light_jax_wave_bridge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)


def _children() -> dict:
    return {
        "light_jax_negative": {"status": "PASS"},
        "jax_runtime": {"status": "PROBED"},
        "seed": {"disposition": "ADMIT", "returncode": 0},
        "etf_exact": {"status": "PASS", "returncode": 0},
        "etf_dual": {"status": "PASS", "returncode": 0},
        "maintenance": {"status": "READY", "returncode": 0},
        "context": {"status": "CONTEXT_SNAPSHOT_READY", "returncode": 0},
        "exploration": {"status": "ANTICHAIN_OPEN", "returncode": 0},
        "dualsolve": {"status": "BOUNDED_SAT", "returncode": 0},
    }


def test_all_children_pass_without_promoting_jax_or_wave() -> None:
    status, reasons = bridge.settle(_children())
    assert status == "PASS"
    assert reasons == []


def test_boundary_or_wave_failure_holds() -> None:
    children = _children()
    children["light_jax_negative"] = {"status": "REFUSE_JAX_IN_LIGHT"}
    children["exploration"] = {"status": "HOLD", "returncode": 0}
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert reasons == ["REFUSE_JAX_IN_LIGHT", "HOLD_EXPLORATION_WAVE"]


def test_nonzero_child_returncode_holds_even_with_pass_like_status() -> None:
    children = _children()
    children["etf_exact"] = {"status": "PASS", "returncode": 1}
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert "HOLD_ETF_EXACT_RETURNCODE" in reasons


def test_missing_returncode_field_is_treated_as_a_hold() -> None:
    children = _children()
    del children["dualsolve"]["returncode"]
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert "HOLD_DUALSOLVE_RETURNCODE" in reasons


def test_declared_interpreter_path_is_not_resolved(tmp_path: Path) -> None:
    alias = tmp_path / "python-alias"
    alias.symlink_to(Path(sys.executable))
    declared = bridge.declared_interpreter(alias)
    assert declared == alias.absolute()
    assert declared != alias.resolve()


def test_bridge_output_must_stay_below_product_root(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    box.mkdir()
    inside = bridge.confined_output_dir(box, box / "integrated_system" / "runs" / "one")
    assert inside == (box / "integrated_system" / "runs" / "one").resolve()
    outside = tmp_path / "outside"
    try:
        bridge.confined_output_dir(box, outside)
    except ValueError as exc:
        assert str(exc) == "REFUSE_BRIDGE_OUTPUT_OUTSIDE_PRODUCT"
    else:
        raise AssertionError("bridge must refuse an output path outside the product")


def test_source_checkout_uses_light_first_selected_overlay(tmp_path: Path) -> None:
    box = tmp_path / "constraint_box"
    light_package = box / "light_runtime" / "src" / "constraintbox"
    root_package = box / "src" / "constraintbox"
    light_package.mkdir(parents=True)
    root_package.mkdir(parents=True)
    (light_package / "__init__.py").write_text("LIGHT = True\n", encoding="utf-8")
    (root_package / "distinguishability.py").write_text(
        "ROOT_SELECTED = True\n", encoding="utf-8"
    )
    output = box / "integrated_system" / "runs" / "overlay"
    output.mkdir(parents=True)
    overlay = bridge.selected_controller_overlay(box, output)
    assert overlay == output / ".controller_src"
    assert (overlay / "constraintbox" / "__init__.py").read_text(encoding="utf-8") == "LIGHT = True\n"
    assert (overlay / "constraintbox" / "distinguishability.py").is_file()


def test_replay_projection_ignores_capture_time_but_not_decision() -> None:
    children = _children()
    children["seed"].update(
        {"source_sha256": "a" * 64, "support_counts": [2, 4], "delta_K": [1.0]}
    )
    children["etf_exact"]["result_sha256"] = "b" * 64
    children["etf_dual"].update(
        {"result_sha256": "c" * 64, "jax": {"output_sha256": "d" * 64}}
    )
    children["maintenance"].update(
        {"captured_at": "first", "source_digest": "e" * 64, "context_digest": "f" * 64}
    )
    children["context"].update({"captured_at": "first"})
    children["exploration"].update({"captured_at": "first"})
    first = bridge.replay_projection(
        children, target_sha256="1" * 64, source_bindings={"source": "2" * 64}
    )
    children["maintenance"]["captured_at"] = "second"
    children["context"]["captured_at"] = "second"
    children["exploration"]["captured_at"] = "second"
    second = bridge.replay_projection(
        children, target_sha256="1" * 64, source_bindings={"source": "2" * 64}
    )
    assert first == second
    children["exploration"]["status"] = "HOLD"
    changed = bridge.replay_projection(
        children, target_sha256="1" * 64, source_bindings={"source": "2" * 64}
    )
    assert changed != first


def _context_layout(tmp_path: Path) -> tuple[Path, Path, Path]:
    box = tmp_path / "constraint_box"
    current = box / "integrated_system" / "context" / "current"
    full = box / "integrated_system" / "context" / "full"
    skills = box / "integrated_system" / "skills"
    current.mkdir(parents=True)
    full.mkdir(parents=True)
    (skills / "cb-context-strategy-wave" / "scripts").mkdir(parents=True)
    (current / "OWNER_OBJECT.md").write_text("> Keep the object bound.\n", encoding="utf-8")
    corpus = {
        "event": {
            "event_type": "OWNER_PROMPT",
            "material": {"text": "Keep the full corpus bound."},
            "source": {"kind": "owner_verbatim", "role": "user"},
        }
    }
    (full / "prompt_plan_progress_corpus.jsonl").write_text(
        json.dumps(corpus) + "\n", encoding="utf-8"
    )
    runner = skills / "cb-context-strategy-wave" / "scripts" / "run_context_strategy.py"
    runner.write_text("# runner fixture\n", encoding="utf-8")
    return box, skills, full / "prompt_plan_progress_corpus.jsonl"


def test_context_runner_command_passes_current_and_full_prompt_paths(
    tmp_path: Path,
) -> None:
    box, skills, _ = _context_layout(tmp_path)
    command = bridge.context_runner_command(
        light_python=Path("/light/python"),
        context_runner=skills / "cb-context-strategy-wave" / "scripts" / "run_context_strategy.py",
        box_root=box,
        output_dir=box / "runs" / "one" / "observations",
        context_path=box / "runs" / "one" / "context_strategy.json",
    )
    prompt_args = [
        command[index + 1]
        for index, value in enumerate(command[:-1])
        if value == "--prompt-path"
    ]
    assert prompt_args == [
        str(bridge.CONTEXT_CURRENT_REL),
        str(bridge.FULL_PROMPT_CORPUS_REL),
    ]


def test_context_input_bindings_cover_full_corpus_and_runner(tmp_path: Path) -> None:
    box, skills, corpus = _context_layout(tmp_path)
    bindings = bridge.context_input_bindings(box, skills)
    assert bindings["full_prompt_corpus_path"] == str(bridge.FULL_PROMPT_CORPUS_REL)
    assert bindings["full_prompt_corpus_sha256"] == bridge.sha256_path(corpus)
    assert bindings["context_strategy_runner_sha256"]
    assert bindings["context_current_sha256"]


def test_context_input_currentness_detects_corpus_mutation(tmp_path: Path) -> None:
    box, skills, corpus = _context_layout(tmp_path)
    before = bridge.context_input_bindings(box, skills)
    corpus.write_text(corpus.read_text(encoding="utf-8") + "mutation\n", encoding="utf-8")
    after = bridge.context_input_bindings(box, skills)
    currentness = bridge.context_input_currentness(before, after)
    assert currentness["status"] == "STALE"
    assert currentness["changed_keys"] == ["full_prompt_corpus_sha256"]


def test_bind_context_result_accepts_bound_full_corpus(tmp_path: Path) -> None:
    box, skills, _ = _context_layout(tmp_path)
    bindings = bridge.context_input_bindings(box, skills)
    body = {
        "status": "CONTEXT_SNAPSHOT_READY",
        "jsonl_index": [
            {
                "path": bindings["full_prompt_corpus_path"],
                "sha256": bindings["full_prompt_corpus_sha256"],
            }
        ],
    }
    bound = bridge.bind_context_result(body, before=bindings, after=bindings)
    assert bound["status"] == "CONTEXT_SNAPSHOT_READY"
    assert bound["input_currentness"]["status"] == "CURRENT"
    assert bound["full_prompt_corpus_sha256"] == bindings["full_prompt_corpus_sha256"]


def test_bind_context_result_holds_missing_or_stale_corpus_binding(tmp_path: Path) -> None:
    box, skills, _ = _context_layout(tmp_path)
    bindings = bridge.context_input_bindings(box, skills)
    missing = bridge.bind_context_result(
        {"status": "CONTEXT_SNAPSHOT_READY", "jsonl_index": []},
        before=bindings,
        after=bindings,
    )
    assert missing["status"] == "HOLD_CONTEXT_CORPUS_UNBOUND"
    stale = bridge.bind_context_result(
        {
            "status": "CONTEXT_SNAPSHOT_READY",
            "jsonl_index": [
                {
                    "path": bindings["full_prompt_corpus_path"],
                    "sha256": "0" * 64,
                }
            ],
        },
        before=bindings,
        after=bindings,
    )
    assert stale["status"] == "HOLD_CONTEXT_CORPUS_STALE"


def test_context_input_missing_and_unsafe_paths_refuse(tmp_path: Path) -> None:
    box, skills, corpus = _context_layout(tmp_path)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_FULL_PROMPT_CORPUS_MISSING"):
        corpus.unlink()
        bridge.context_input_bindings(box, skills)
    corpus.write_text("{}\n", encoding="utf-8")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_UNSAFE_OUTSIDE_PRODUCT"):
        bridge.confined_input_path(box, outside, label="UNSAFE")
    linked = box / "integrated_system" / "context" / "current" / "outside.md"
    linked.symlink_to(outside)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_CONTEXT_CURRENT_OUTSIDE_PRODUCT"):
        bridge.context_input_bindings(box, skills)


def _make_context_snapshot(tmp_path: Path, name: str = "one") -> tuple[dict, Path, Path, Path]:
    box, skills, corpus = _context_layout(tmp_path / name)
    output = box / "integrated_system" / "runs" / name
    snapshot = bridge.create_context_snapshot(
        box_root=box,
        skills_root=skills,
        output_dir=output,
    )
    return snapshot, box, skills, corpus


def test_context_snapshot_manifest_binds_every_file(tmp_path: Path) -> None:
    snapshot, _, _, _ = _make_context_snapshot(tmp_path)
    manifest = snapshot["manifest"]
    assert manifest["schema"] == bridge.CONTEXT_SNAPSHOT_SCHEMA
    assert manifest["claim_ceiling"] == bridge.CONTEXT_SNAPSHOT_CLAIM
    assert manifest["captured_at"]
    assert len(manifest["files"]) == 3
    for entry in manifest["files"]:
        copied = snapshot["root"] / entry["relative_path"]
        assert copied.is_file()
        assert entry["byte_length"] == copied.stat().st_size
        assert entry["sha256"] == bridge.sha256_path(copied)
    core = {
        "schema": manifest["schema"],
        "files": manifest["files"],
        "source_at_capture": manifest["source_at_capture"],
    }
    assert snapshot["snapshot_digest"] == bridge.sha256_bytes(
        bridge.canonical_json_bytes(core)
    )
    assert snapshot["path"] == "context_snapshot"


def test_context_snapshot_digest_is_content_only(tmp_path: Path) -> None:
    first, _, _, _ = _make_context_snapshot(tmp_path, "first")
    second, _, _, _ = _make_context_snapshot(tmp_path, "second")
    assert first["snapshot_digest"] == second["snapshot_digest"]
    assert first["captured_at"] != second["captured_at"]
    assert first["manifest_sha256"] != second["manifest_sha256"]


def test_context_snapshot_runner_command_uses_snapshot_root(tmp_path: Path) -> None:
    snapshot, box, _, _ = _make_context_snapshot(tmp_path)
    runner = snapshot["root"] / snapshot["runner_relative_path"]
    command = bridge.context_runner_command(
        light_python=Path("/light/python"),
        context_runner=runner,
        box_root=snapshot["root"],
        output_dir=box / "integrated_system" / "runs" / "one" / "observations",
        context_path=box / "integrated_system" / "runs" / "one" / "context.json",
    )
    assert command[command.index("--root") + 1] == str(snapshot["root"])
    assert str(runner).startswith(str(snapshot["root"]))
    prompt_args = [
        command[index + 1]
        for index, value in enumerate(command[:-1])
        if value == "--prompt-path"
    ]
    assert prompt_args == [
        str(bridge.CONTEXT_CURRENT_REL),
        str(bridge.FULL_PROMPT_CORPUS_REL),
    ]


def test_context_snapshot_refuses_full_corpus_symlink(tmp_path: Path) -> None:
    box, skills, corpus = _context_layout(tmp_path)
    target = box / "integrated_system" / "context" / "full" / "inside.jsonl"
    target.write_text("{}\n", encoding="utf-8")
    corpus.unlink()
    corpus.symlink_to(target)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_SNAPSHOT_FULL_PROMPT_CORPUS_SYMLINK"):
        bridge.create_context_snapshot(
            box_root=box,
            skills_root=skills,
            output_dir=box / "integrated_system" / "runs" / "symlink",
        )


def test_context_snapshot_refuses_current_symlink(tmp_path: Path) -> None:
    box, skills, _ = _context_layout(tmp_path)
    current = box / "integrated_system" / "context" / "current"
    target = box / "integrated_system" / "context" / "OWNER_OBJECT.md"
    target.write_text("> externalized\n", encoding="utf-8")
    (current / "link.md").symlink_to(target)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_SNAPSHOT_CONTEXT_CURRENT_SYMLINK"):
        bridge.create_context_snapshot(
            box_root=box,
            skills_root=skills,
            output_dir=box / "integrated_system" / "runs" / "symlink",
        )


def test_context_snapshot_refuses_nonregular_current_entry(tmp_path: Path) -> None:
    box, skills, _ = _context_layout(tmp_path)
    fifo = box / "integrated_system" / "context" / "current" / "pipe.md"
    os.mkfifo(fifo)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_SNAPSHOT_CONTEXT_CURRENT_NONREGULAR"):
        bridge.create_context_snapshot(
            box_root=box,
            skills_root=skills,
            output_dir=box / "integrated_system" / "runs" / "fifo",
        )


def test_context_snapshot_refuses_existing_destination(tmp_path: Path) -> None:
    box, skills, _ = _context_layout(tmp_path)
    output = box / "integrated_system" / "runs" / "existing"
    (output / "context_snapshot").mkdir(parents=True)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_CONTEXT_SNAPSHOT_EXISTS"):
        bridge.create_context_snapshot(box_root=box, skills_root=skills, output_dir=output)


def test_context_snapshot_refuses_missing_source(tmp_path: Path) -> None:
    box, skills, corpus = _context_layout(tmp_path)
    corpus.unlink()
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_SNAPSHOT_FULL_PROMPT_CORPUS_MISSING"):
        bridge.create_context_snapshot(
            box_root=box,
            skills_root=skills,
            output_dir=box / "integrated_system" / "runs" / "missing",
        )


def test_context_snapshot_refuses_output_escape(tmp_path: Path) -> None:
    box, skills, _ = _context_layout(tmp_path)
    with pytest.raises(ValueError, match="REFUSE_BRIDGE_OUTPUT_OUTSIDE_PRODUCT"):
        bridge.create_context_snapshot(
            box_root=box,
            skills_root=skills,
            output_dir=tmp_path / "outside",
        )


def test_snapshot_source_currentness_is_current_at_capture(tmp_path: Path) -> None:
    snapshot, box, skills, _ = _make_context_snapshot(tmp_path)
    after = bridge.context_input_bindings(box, skills)
    currentness = bridge.snapshot_source_currentness(snapshot, after=after)
    assert currentness["status"] == "CURRENT"
    assert currentness["basis"] == "SNAPSHOT_AT_CAPTURE"
    assert currentness["changed_keys"] == []


def test_snapshot_late_source_swap_marks_stale_without_changing_snapshot(
    tmp_path: Path,
) -> None:
    snapshot, box, skills, corpus = _make_context_snapshot(tmp_path)
    snapshot_copy = (
        snapshot["root"] / bridge.FULL_PROMPT_CORPUS_REL
    ).read_bytes()
    corpus.write_text(corpus.read_text(encoding="utf-8") + "late swap\n", encoding="utf-8")
    currentness = bridge.snapshot_source_currentness(
        snapshot,
        after=bridge.context_input_bindings(box, skills),
    )
    assert currentness["status"] == "STALE_AFTER_CAPTURE"
    assert currentness["changed_keys"] == ["full_prompt_corpus_sha256"]
    assert (snapshot["root"] / bridge.FULL_PROMPT_CORPUS_REL).read_bytes() == snapshot_copy


def test_snapshot_bound_context_stays_valid_but_settlement_holds_late_drift(
    tmp_path: Path,
) -> None:
    snapshot, box, skills, corpus = _make_context_snapshot(tmp_path)
    corpus.write_text(corpus.read_text(encoding="utf-8") + "late swap\n", encoding="utf-8")
    currentness = bridge.snapshot_source_currentness(
        snapshot,
        after=bridge.context_input_bindings(box, skills),
    )
    expected_sha = snapshot["source_at_capture"]["full_prompt_corpus_sha256"]
    bound = bridge.bind_snapshot_context_result(
        {
            "status": "CONTEXT_SNAPSHOT_READY",
            "returncode": 0,
            "jsonl_index": [
                {
                    "path": bridge.FULL_PROMPT_CORPUS_REL.as_posix(),
                    "sha256": expected_sha,
                }
            ],
        },
        snapshot=snapshot,
        source_currentness=currentness,
    )
    assert bound["snapshot_valid"] is True
    assert bound["status"] == "CONTEXT_SNAPSHOT_READY"
    assert bound["input_currentness"]["status"] == "STALE_AFTER_CAPTURE"
    children = _children()
    children["context"] = bound
    status, reasons = bridge.settle(children)
    assert status == "HOLD"
    assert "HOLD_CONTEXT_INPUT_CURRENTNESS" in reasons
