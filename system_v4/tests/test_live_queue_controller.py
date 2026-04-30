from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "system_v4" / "probes" / "live_queue_controller.py"


def load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"missing live queue controller script: {SCRIPT_PATH}")
    spec = importlib.util.spec_from_file_location("live_queue_controller", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        pytest.fail("unable to load live_queue_controller module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_closure_command_returns_dry_run_command_for_step_with_truth_row():
    lqc = load_module()
    step = lqc.Step(
        name="carrier_admission_rerun",
        command=[lqc.PYTHON, str(lqc.PROBES / "sim_density_hopf_geometry.py")],
        result_json="density_hopf_geometry_results.json",
        truth_row="explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
        backlog_row="B4",
        registry_row="hopf_map_s3_to_s2",
    )

    command = lqc.build_closure_command(step)

    assert command == [
        lqc.PYTHON,
        str(lqc.PROBES / "maintenance_closure.py"),
        "--result-json",
        str(lqc.RESULTS / "density_hopf_geometry_results.json"),
        "--truth-row",
        "explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
        "--backlog-row",
        "B4",
        "--registry-row",
        "hopf_map_s3_to_s2",
        "--dry-run",
    ]


def test_build_closure_command_returns_none_when_step_has_no_truth_surface_target():
    lqc = load_module()
    step = lqc.Step(
        name="truth_audit",
        command=[lqc.PYTHON, str(lqc.PROBES / "probe_truth_audit.py")],
    )

    assert lqc.build_closure_command(step) is None


def test_run_batch_closure_invokes_only_targeted_steps_after_green_audits():
    lqc = load_module()
    steps = [
        lqc.Step(
            name="carrier_admission_rerun",
            command=[lqc.PYTHON, str(lqc.PROBES / "sim_density_hopf_geometry.py")],
            result_json="density_hopf_geometry_results.json",
            truth_row="explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
            backlog_row="B4",
            registry_row="hopf_map_s3_to_s2",
        ),
        lqc.Step(
            name="truth_audit",
            command=[lqc.PYTHON, str(lqc.PROBES / "probe_truth_audit.py")],
        ),
        lqc.Step(
            name="controller_alignment",
            command=[lqc.PYTHON, str(lqc.PROBES / "controller_alignment_audit.py")],
        ),
    ]
    commands = []

    def fake_runner(cmd: list[str]) -> int:
        commands.append(cmd)
        return 0

    rc = lqc.run_batch_closure(steps, truth_exit=0, controller_exit=0, runner=fake_runner)

    assert rc == 0
    assert commands == [
        [
            lqc.PYTHON,
            str(lqc.PROBES / "maintenance_closure.py"),
            "--result-json",
            str(lqc.RESULTS / "density_hopf_geometry_results.json"),
            "--truth-row",
            "explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
            "--backlog-row",
            "B4",
            "--registry-row",
            "hopf_map_s3_to_s2",
            "--dry-run",
        ]
    ]


LANES_T01_OPEN = textwrap.dedent("""\
    ## Lane T — Tool sims (isolation)

    | id | tool | owner | status | result_path |
    |---|---|---|---|---|
    | T-01 | z3 |  | open |  |
    | T-02 | cvc5 | | open | |
""")

LANES_NO_OPEN = textwrap.dedent("""\
    ## Lane T — Tool sims (isolation)

    | id | tool | owner | status | result_path |
    |---|---|---|---|---|
    | T-01 | z3 | hermes | in_progress |  |
    | T-02 | cvc5 | hermes | in_progress | |
""")


def test_choose_batch_prefers_live_t_lane_when_audits_are_red(tmp_path):
    lqc = load_module()
    lanes_file = tmp_path / "lanes.md"
    lanes_file.write_text(LANES_T01_OPEN)

    with patch.object(lqc, "audit_green", return_value=(False, False)), \
         patch.object(lqc, "LANES_MD", lanes_file):
        name, steps = lqc.choose_batch(previous=None)

    assert name == "T-01"
    step_names = [s.name for s in steps]
    assert step_names[0] == "z3_capability"
    assert "truth_audit" in step_names
    assert "controller_alignment" in step_names
    assert len(steps) == 3


def test_choose_batch_falls_back_to_batch1_when_no_open_t_row(tmp_path):
    lqc = load_module()
    lanes_file = tmp_path / "lanes.md"
    lanes_file.write_text(LANES_NO_OPEN)

    with patch.object(lqc, "audit_green", return_value=(False, False)), \
         patch.object(lqc, "LANES_MD", lanes_file):
        name, steps = lqc.choose_batch(previous=None)

    assert name == "batch1"
    step_names = [s.name for s in steps]
    assert "truth_audit" in step_names


def test_run_batch_closure_skips_when_audits_are_not_green():
    lqc = load_module()
    steps = [
        lqc.Step(
            name="carrier_admission_rerun",
            command=[lqc.PYTHON, str(lqc.PROBES / "sim_density_hopf_geometry.py")],
            result_json="density_hopf_geometry_results.json",
            truth_row="explicit Hopf-map packet (`hopf_map_s3_to_s2`)",
            backlog_row="B4",
            registry_row="hopf_map_s3_to_s2",
        )
    ]

    called = False

    def fake_runner(cmd: list[str]) -> int:
        nonlocal called
        called = True
        return 0

    rc = lqc.run_batch_closure(steps, truth_exit=1, controller_exit=0, runner=fake_runner)

    assert rc == 0
    assert called is False
