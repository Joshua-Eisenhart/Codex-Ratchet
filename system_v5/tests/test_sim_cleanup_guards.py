from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(module_name, None)


def test_live_queue_controller_ignores_copy_sims(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "live_queue_controller_under_test",
        REPO_ROOT / "system_v4" / "probes" / "live_queue_controller.py",
    )
    probes = tmp_path / "probes"
    probes.mkdir()
    (probes / "sim_alpha.py").write_text("print('alpha')\n", encoding="utf-8")
    (probes / "sim_alpha 2.py").write_text("print('alpha copy')\n", encoding="utf-8")
    (probes / "sim_beta.py").write_text("print('beta')\n", encoding="utf-8")

    monkeypatch.setattr(module, "PROBES", probes)

    names = [path.name for path in module.enumerate_all_sims()]
    assert names == ["sim_alpha.py", "sim_beta.py"]


def test_check_witnesses_accepts_recent_witness_fields(tmp_path, monkeypatch, capsys) -> None:
    module = _load_module(
        "check_witnesses_under_test",
        REPO_ROOT / "scripts" / "check_witnesses.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    probes.mkdir(parents=True)

    witness = probes / "sim_pyg_dynamic_edge_werner.py"
    witness.write_text(
        "TOOL_INTEGRATION_DEPTH = {'pyg': 'load_bearing'}\n",
        encoding="utf-8",
    )
    capability = probes / "sim_pyg_capability.py"
    capability.write_text(
        "\n".join(
            [
                "results = {",
                "    'witness_use_cases': ['system_v4/probes/sim_pyg_dynamic_edge_werner.py'],",
                "}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert '"violation_count": 0' in out


def test_lint_accepts_isolated_capability_probe_for_classical_integration(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "lint_sim_contract_under_test",
        REPO_ROOT / "scripts" / "lint_sim_contract.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)

    capability = probes / "sim_capability_datasketch_isolated.py"
    capability.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical capability baseline."',
                'TOOL_MANIFEST = {"datasketch": {"tried": True, "used": True, "reason": "load-bearing isolated capability probe"}}',
                'TOOL_INTEGRATION_DEPTH = {"datasketch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "sim_capability_datasketch_isolated_results.json").write_text(
        '{"overall_pass": true}\n',
        encoding="utf-8",
    )

    integration = probes / "sim_integration_datasketch_graph.py"
    integration.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'divergence_log = "Classical integration baseline."',
                'TOOL_MANIFEST = {"datasketch": {"tried": True, "used": True, "reason": "load-bearing graph edge construction"}}',
                'TOOL_INTEGRATION_DEPTH = {"datasketch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    violations = module.lint_sim(integration)
    rules = {v["rule"] for v in violations}

    assert "C5_missing_probe" not in rules
    assert "C5_probe_stale" not in rules
    assert "C5_probe_failing" not in rules
    assert "C6_classical_has_load_bearing" not in rules


def test_gate_accepts_isolated_capability_probe_for_load_bearing_tool(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "verify_load_bearing_under_test",
        REPO_ROOT / "scripts" / "verify_load_bearing_has_capability_probe.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)

    capability = probes / "sim_capability_evotorch_isolated.py"
    capability.write_text(
        "\n".join(
            [
                'classification = "classical_baseline"',
                'TOOL_MANIFEST = {"evotorch": {"tried": True, "used": True, "reason": "isolated capability probe"}}',
                'TOOL_INTEGRATION_DEPTH = {"evotorch": "load_bearing"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (results / "sim_capability_evotorch_isolated_results.json").write_text(
        '{"overall_pass": true}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES_DIR", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    assert module.probe_status("evotorch") is None


def test_adaptive_controller_builds_plane_snapshot_from_current_surfaces(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    skill_log = repo / "system_v4" / "a1_state" / "skill_invocation_log.jsonl"
    for lane, count in {
        "lane_A": 2,
        "lane_B": 1,
        "claimed": 3,
        "blocked": 1,
        "done": 4,
    }.items():
        lane_dir = queue_root / lane
        lane_dir.mkdir(parents=True, exist_ok=True)
        for i in range(count):
            (lane_dir / f"{lane}_{i}.json").write_text("{}", encoding="utf-8")

    skill_log.parent.mkdir(parents=True, exist_ok=True)
    skill_log.write_text(
        "\n".join(
            [
                '{"timestamp":"2026-04-15T01:00:00Z","batch_id":"B1","phase":"A1_EXTRACTION","layer_id":"A1_STRIPPED","graph_family":"dependency","selected_skill_id":"a1-brain","execution_runtime":"codex"}',
                '{"timestamp":"2026-04-15T01:05:00Z","batch_id":"B2","phase":"SIM_EVIDENCE","layer_id":"SIM_EVIDENCED","graph_family":"runtime","selected_skill_id":"sim-engine","execution_runtime":"codex"}',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "SKILL_LOG", skill_log)

    state = {
        "ts": "2026-04-15T02:00:00Z",
        "failing": ["sim_fail"],
        "schema_debt": ["sim_schema"],
        "never_run": ["sim_new"],
        "stale": [],
        "passing": ["sim_ok1", "sim_ok2"],
        "released_claims": 5,
    }
    integration = {
        "canonical_passing": 1,
        "total_passing": 2,
        "rosetta_candidate_clusters": 3,
    }

    snapshot = module.build_plane_snapshot(state, integration)

    assert snapshot["control_plane"]["queue"] == {
        "lane_A": 2,
        "lane_B": 1,
        "claimed": 3,
        "blocked": 1,
        "done": 4,
    }
    assert snapshot["control_plane"]["released_claims"] == 5
    assert len(snapshot["control_plane"]["recent_dispatch"]) == 2
    assert snapshot["state_plane"]["triage"] == {
        "failing": 1,
        "schema_debt": 1,
        "never_run": 1,
        "stale": 0,
        "passing": 2,
    }
    assert snapshot["state_plane"]["integration"]["rosetta_candidate_clusters"] == 3


def test_controller_plane_snapshot_dry_mode_prints_snapshot(
    tmp_path, monkeypatch, capsys
) -> None:
    adaptive = _load_module(
        "adaptive_controller_for_plane_script",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    sys.modules["adaptive_controller"] = adaptive
    try:
        module = _load_module(
            "controller_plane_snapshot_under_test",
            REPO_ROOT / "scripts" / "controller_plane_snapshot.py",
        )
    finally:
        sys.modules.pop("adaptive_controller", None)

    monkeypatch.setattr(adaptive, "triage_cycle", lambda dry=True: {
        "ts": "2026-04-15T03:00:00Z",
        "failing": [],
        "schema_debt": [],
        "never_run": [],
        "stale": [],
        "passing": ["sim_ok"],
        "released_claims": 0,
    })
    monkeypatch.setattr(adaptive, "build_integration_summary", lambda state: {
        "canonical_passing": 1,
        "total_passing": 1,
        "rosetta_candidate_clusters": 0,
    })
    monkeypatch.setattr(adaptive, "build_plane_snapshot", lambda state, integration: {
        "ts": state["ts"],
        "control_plane": {"queue": {"lane_A": 0, "lane_B": 0, "claimed": 0, "blocked": 0, "done": 0}},
        "state_plane": {"triage": {"passing": 1}},
    })
    monkeypatch.setattr(sys, "argv", ["controller_plane_snapshot.py", "--dry"])

    rc = module.main()
    out = capsys.readouterr().out

    assert rc == 0
    assert '"control_plane"' in out
