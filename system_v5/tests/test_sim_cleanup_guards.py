from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
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
    assert snapshot["state_plane"]["program"]["never_run_families"] == {"new": 1}
    assert snapshot["state_plane"]["program"]["passing_families"] == {"ok1": 1, "ok2": 1}
    assert snapshot["state_plane"]["program"]["never_run_buckets"] == {"exploratory": 1}
    assert snapshot["state_plane"]["program"]["passing_buckets"] == {"exploratory": 2}
    assert snapshot["state_plane"]["program"]["never_run_stages"] == {"early_core": 1}
    assert snapshot["state_plane"]["program"]["passing_stages"] == {"early_core": 2}
    assert snapshot["state_plane"]["program"]["queue_families"]["lane_A"] == {"other": 2}


def test_adaptive_controller_rescues_misrouted_blocked_classical_baseline(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_rescue_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)
    lane_b.mkdir(parents=True)

    sim = probes / "sim_cl3_composition.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    blocked_item = blocked / "dead.json.123.host.w1"
    blocked_item.write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    rescued = module.rescue_misrouted_blocked()

    queued = list(lane_b.glob("*.json"))
    resolved = list((blocked / "resolved").glob("*.json*"))
    assert rescued == 1
    assert len(queued) == 1
    assert len(resolved) == 1
    queued_payload = json.loads(queued[0].read_text(encoding="utf-8"))
    assert queued_payload["sim_path"] == str(sim)
    resolved_payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert resolved_payload["rescued_lane"] == "lane_B"
    assert resolved_payload["rescued_priority"] == "normal"
    assert blocked_item.exists() is False


def test_adaptive_controller_resolves_blacklisted_blocked_items(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_blacklisted_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)

    sim = probes / "sim_timing_benchmark.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    blocked_item = blocked / "meta.json"
    blocked_item.write_text(
        '{"lane":"lane_B","sim_path":"%s","blocked_reason":"blacklisted_meta_sim"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    rescued = module.rescue_misrouted_blocked()

    resolved = list((blocked / "resolved").glob("*.json*"))
    assert rescued == 1
    assert len(resolved) == 1
    payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert payload["resolution"] == "blacklisted_meta_sim"
    assert blocked_item.exists() is False


def test_adaptive_controller_triage_skips_enqueue_for_active_blocked_sim(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_blocked_skip_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)

    sim = probes / "sim_clifford_holo_dirac_pairwise_coupling.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    (blocked / "gate.json.1.host.w1").write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied","blocked_at":1}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "gate_allows_sim", lambda path: False)

    state = module.triage_cycle(dry=False)

    assert "sim_clifford_holo_dirac_pairwise_coupling" in state["never_run"]
    assert state["enqueued"]["never_run"] == 0
    assert list((queue_root / "lane_A").glob("*.json")) == []


def test_adaptive_controller_dedupes_blocked_entries_and_queue_overlaps(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_blocked_dedupe_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    lane_a = queue_root / "lane_A"
    probes.mkdir(parents=True)
    blocked.mkdir(parents=True)
    lane_a.mkdir(parents=True)

    sim = probes / "sim_alpha.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    abs_sim = str(sim.resolve())
    (blocked / "dup1.json.1.host.w1").write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied","blocked_at":1}\n' % abs_sim,
        encoding="utf-8",
    )
    (blocked / "dup2.json.2.host.w2").write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied","blocked_at":2}\n' % abs_sim,
        encoding="utf-8",
    )
    (lane_a / "queued.json").write_text(
        '{"lane":"lane_A","sim_path":"%s","priority":"high"}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    active_blocked = list(blocked.glob("*.json.*"))
    resolved = list((blocked / "resolved").glob("*.json*"))
    assert removed == 2
    assert len(active_blocked) == 1
    assert len(resolved) == 1
    assert list(lane_a.glob("*.json")) == []
    payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert payload["resolution"] == "deduped_duplicate_block"


def test_adaptive_controller_rescues_gate_ready_blocked_canonical(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_gate_ready_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    blocked = queue_root / "blocked"
    lane_a = queue_root / "lane_A"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    blocked.mkdir(parents=True)
    lane_a.mkdir(parents=True)

    sim = probes / "sim_clifford_holo_dirac_pairwise_coupling.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    blocked_item = blocked / "gate.json.123.host.w1"
    blocked_item.write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)
    monkeypatch.setattr(module, "gate_allows_sim", lambda path: True)

    rescued = module.rescue_misrouted_blocked()

    queued = list(lane_a.glob("*.json"))
    resolved = list((blocked / "resolved").glob("*.json*"))
    assert rescued == 1
    assert len(queued) == 1
    assert len(resolved) == 1
    payload = json.loads(resolved[0].read_text(encoding="utf-8"))
    assert payload["rescued_lane"] == "lane_A"
    assert payload["resolution"] == "requeued_lane_A"
    assert blocked_item.exists() is False


def test_adaptive_controller_dry_mode_skips_queue_mutation(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "adaptive_controller_dry_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    queue_root = probes / "a2_state" / "queue"
    probes.mkdir(parents=True)
    results.mkdir(parents=True)
    for lane in ("claimed", "blocked"):
        (queue_root / lane).mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_alpha.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    claim = queue_root / "claimed" / "dead.json.123.host.w1"
    claim.write_text(
        '{"lane":"lane_A","sim_path":"%s"}\n' % sim,
        encoding="utf-8",
    )
    blocked = queue_root / "blocked" / "gate.json.123.host.w1"
    blocked.write_text(
        '{"lane":"lane_A","sim_path":"%s","blocked_reason":"gate_denied"}\n' % sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS", results)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    state = module.triage_cycle(dry=True)

    assert state["released_claims"] == 0
    assert state["rescued_misrouted_blocked"] == 0
    assert claim.exists()
    assert blocked.exists()


def test_adaptive_controller_is_queued_matches_relative_and_absolute_paths(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_is_queued_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    (queue_root / "lane_B").mkdir(parents=True, exist_ok=True)

    sim_rel = "system_v4/probes/sim_alpha.py"
    sim_abs = str((repo / sim_rel).resolve())
    (queue_root / "lane_B" / "item.json").write_text(
        '{"sim_path":"%s","lane":"lane_B"}\n' % sim_rel,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    assert module.is_queued(sim_abs) is True


def test_adaptive_controller_enqueue_is_idempotent(tmp_path, monkeypatch) -> None:
    module = _load_module(
        "adaptive_controller_enqueue_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True, exist_ok=True)
    lane_b.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_weyl_chirality_bipartite.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    module.enqueue(sim, "lane_B", "normal")
    module.enqueue(sim, "lane_B", "normal")

    queued = list(lane_b.glob("*.json"))
    assert len(queued) == 1
    payload = json.loads(queued[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == str(sim.resolve())
    assert payload["plan_stage"] == "late_info"


def test_adaptive_controller_dedupes_queue_entries_and_normalizes_paths(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_dedupe_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_a = queue_root / "lane_A"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True, exist_ok=True)
    lane_a.mkdir(parents=True, exist_ok=True)
    lane_b.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_weyl_chirality_bipartite.py"
    sim.write_text('classification = "classical_baseline"\n', encoding="utf-8")
    abs_sim = str(sim.resolve())
    rel_sim = "system_v4/probes/sim_weyl_chirality_bipartite.py"
    (lane_b / "a.json").write_text(
        '{"sim_path":"%s","lane":"lane_B","priority":"high"}\n' % rel_sim,
        encoding="utf-8",
    )
    (lane_b / "b.json").write_text(
        '{"sim_path":"%s","lane":"lane_B","priority":"normal"}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    remaining = list(lane_b.glob("*.json"))
    assert removed == 1
    assert len(remaining) == 1
    payload = json.loads(remaining[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == abs_sim
    assert remaining[0].name == module.queue_item_path("lane_B", abs_sim).name
    assert payload["plan_bucket"] == "core_ladder"
    assert payload["plan_stage"] == "late_info"
    assert payload["priority"] == "high"


def test_adaptive_controller_normalizes_legacy_queue_filename_without_duplicate(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_queue_normalize_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_b = queue_root / "lane_B"
    probes.mkdir(parents=True, exist_ok=True)
    lane_b.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_shannon_entropy.py"
    sim.write_text("print('ok')\n", encoding="utf-8")
    abs_sim = str(sim.resolve())
    legacy = lane_b / "legacy.json"
    legacy.write_text(
        '{"sim_path":"%s","lane":"lane_B","priority":"normal"}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    remaining = list(lane_b.glob("*.json"))
    assert removed == 0
    assert len(remaining) == 1
    assert remaining[0].name == module.queue_item_path("lane_B", abs_sim).name
    payload = json.loads(remaining[0].read_text(encoding="utf-8"))
    assert payload["sim_path"] == abs_sim
    assert payload["plan_stage"] == "late_info"


def test_adaptive_controller_removes_queue_entries_for_claimed_sims(
    tmp_path, monkeypatch
) -> None:
    module = _load_module(
        "adaptive_controller_claim_overlap_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )
    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    queue_root = probes / "a2_state" / "queue"
    lane_a = queue_root / "lane_A"
    claimed = queue_root / "claimed"
    probes.mkdir(parents=True, exist_ok=True)
    lane_a.mkdir(parents=True, exist_ok=True)
    claimed.mkdir(parents=True, exist_ok=True)

    sim = probes / "sim_gerbe_admissibility_dixmier_douady.py"
    sim.write_text('classification = "canonical"\n', encoding="utf-8")
    abs_sim = str(sim.resolve())
    (lane_a / "legacy.json").write_text(
        '{"sim_path":"%s","lane":"lane_A","priority":"high"}\n' % abs_sim,
        encoding="utf-8",
    )
    (claimed / "claimed.json.123.host.laneA_w1").write_text(
        '{"sim_path":"%s","lane":"lane_A","claimed_at":1}\n' % abs_sim,
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "ROOT", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "QUEUE", queue_root)

    removed = module.dedupe_queue_entries()

    assert removed == 1
    assert list(lane_a.glob("*.json")) == []


def test_adaptive_controller_accepts_all_pass_and_summary_all_passed() -> None:
    module = _load_module(
        "adaptive_controller_pass_schema_under_test",
        REPO_ROOT / "scripts" / "adaptive_controller.py",
    )

    assert module.is_passing({"all_pass": True}) is True
    assert module.is_passing({"all_pass": False}) is False
    assert module.is_passing({"ALL_PASS": True}) is True
    assert module.is_passing({"ALL_PASS": False}) is False
    assert module.is_passing({"summary": {"all_passed": True}}) is True
    assert module.is_passing({"summary": {"all_pass": False}}) is False
    assert module.is_passing({"summary": {"all_checks_pass": True}}) is True
    assert module.is_passing({
        "summary": {
            "all_checks_pass": True,
            "key_findings": {"one": True, "two": True},
        }
    }) is True
    assert module.is_passing({
        "positive": {"torch": {"status": "ok"}},
        "negative": {"z3": {"status": "ok"}},
    }) is True
    assert module.is_legacy_schema({"timestamp": "x", "all_pass": True}) is False
    assert module.is_legacy_schema({"timestamp": "x", "ALL_PASS": True}) is False


def test_perpetual_runner_declares_pidfile_singleton() -> None:
    text = (REPO_ROOT / "scripts" / "perpetual_runner.sh").read_text(encoding="utf-8")

    assert 'PERPETUAL_PIDFILE="/tmp/codex_ratchet_perpetual_runner.pid"' in text
    assert "acquire_perpetual_pidfile()" in text
    assert "existing perpetual pidfile is alive; exiting duplicate" in text


def test_system_surface_audit_infers_legacy_pass_shapes() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    assert module._pass_state({"all_pass": True}) == "pass"
    assert module._pass_state({"ALL_PASS": True}) == "pass"
    assert module._pass_state({"summary": {"all_passed": True}}) == "pass"
    assert module._pass_state({"summary": {"all_checks_pass": True}}) == "pass"
    assert module._pass_state({
        "summary": {"all_checks_pass": True, "key_findings": {"alpha": True, "beta": True}},
    }) == "pass"
    assert module._pass_state({
        "positive": {"torch": {"status": "ok"}},
        "negative": {"z3": {"status": "ok"}},
        "boundary": {"sympy": {"status": "passed"}},
    }) == "pass"
    assert module._pass_state({
        "evidence_ledger": [{"status": "PASS"}],
        "results": {"check_a": True},
    }) == "pass_inferred"
    assert module._pass_state({
        "positive": {"foo": {"passed": True}},
        "negative": {"bar": {"pass": True}},
        "boundary": {"baz": {"ok": True}},
    }) == "pass_inferred"
    assert module._pass_state({"summary": {"positive": "42/42", "boundary": "5/5"}}) == "pass_inferred"


def test_system_surface_audit_pidfile_uses_ps_fallback_on_permission_error(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_pid_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    pidfile = tmp_path / "runner.pid"
    pidfile.write_text("123\n", encoding="utf-8")

    def fake_kill(pid: int, sig: int) -> None:
        raise PermissionError

    monkeypatch.setattr(module.os, "kill", fake_kill)
    monkeypatch.setattr(module, "_process_command", lambda pid: "bash scripts/perpetual_runner.sh")

    status = module._pidfile_status("perpetual_runner", pidfile)

    assert status["alive"] is True
    assert status["alive_state"] == "ps_visible_permission_limited"
    assert status["command"] == "bash scripts/perpetual_runner.sh"


def test_system_surface_audit_reports_fail_and_unknown_families(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_result_surface_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    root = probes / "a2_state" / "sim_results"
    root.mkdir(parents=True, exist_ok=True)

    (root / "sim_szilard_alpha_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )
    (root / "sim_szilard_beta_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )
    (root / "sim_weyl_gamma_results.json").write_text(
        '{"summary": {"all_checks_pass": true}}\n',
        encoding="utf-8",
    )
    (root / "sim_axis_delta_results.json").write_text(
        '{"summary": {"note": "unknown legacy shape"}}\n',
        encoding="utf-8",
    )
    (probes / "sim_szilard_alpha.py").write_text("print('alpha')\n", encoding="utf-8")
    (probes / "weyl_beta.py").write_text("print('beta')\n", encoding="utf-8")
    (root / "weyl_beta_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULT_ROOTS", [root])

    report = module.result_surface()["system_v4/probes/a2_state/sim_results"]

    assert report["status"]["fail"] == 3
    assert report["status"]["pass"] == 1
    assert report["status"]["unknown"] == 1
    assert report["fail_families"] == {"szilard": 2, "weyl": 1}
    assert report["fail_modes"] == {"summary_gate_false": 3}
    assert report["fail_source_states"] == {"source_clean_source_newer": 1, "source_missing": 1, "source_clean_result_newer": 1}
    assert report["fail_actions"] == {"missing_source_repair": 1, "rerun_candidate": 1, "noncanonical_source_repair": 1}
    assert report["unknown_families"] == {"axis": 1}


def test_system_surface_audit_classifies_fail_modes() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_fail_modes_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    assert module._result_fail_mode({"error": "ImportError", "overall_pass": False}) == "explicit_error"
    assert module._result_fail_mode({"summary": {"tests_failed": 2}, "overall_pass": False}) == "tests_failed"
    assert module._result_fail_mode({"summary": {"passed": 2, "total": 3}, "overall_pass": False}) == "partial_pass"
    assert module._result_fail_mode({"summary": {"all_pass": False}, "overall_pass": False}) == "summary_gate_false"
    assert module._result_fail_mode({"all_pass": False}) == "top_level_gate_false"
    assert module._result_fail_mode({"positive": {"foo": {"pass": False}}, "overall_pass": False}) == "section_check_failed"


def test_system_surface_audit_queue_freshness_detects_recent_activity(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_freshness_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue_dir = tmp_path / "queue"
    queue_dir.mkdir()
    item = queue_dir / "item.json"
    item.write_text("{}", encoding="utf-8")

    freshness = module._queue_dir_freshness(queue_dir)

    assert freshness["newest_file"] == "item.json"
    assert freshness["newest_age_sec"] is not None
    assert freshness["active_within_60s"] is True
    assert freshness["active_within_300s"] is True


def test_system_surface_audit_git_layer_classifies_probe_sources() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_git_layer_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    assert module._git_layer("system_v4/probes/sim_mera_weyl_pairwise_coupling.py") == "probe_sources"
    assert (
        module._git_layer("system_v4/probes/sim_mera_weyl_pairwise_coupling_results.json")
        == "misplaced_probe_results"
    )


def test_system_surface_audit_result_surface_reports_untracked_probe_sources(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_untracked_sources_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    root = probes / "a2_state" / "sim_results"
    root.mkdir(parents=True, exist_ok=True)
    (root / "sim_mera_weyl_pairwise_coupling_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )
    (probes / "sim_mera_weyl_pairwise_coupling.py").write_text(
        "print('probe')\n",
        encoding="utf-8",
    )
    newer = time.time() + 5
    os.utime(root / "sim_mera_weyl_pairwise_coupling_results.json", (newer, newer))

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULT_ROOTS", [root])
    monkeypatch.setattr(
        module,
        "_git_status_entries",
        lambda: [{"status": "??", "path": "system_v4/probes/sim_mera_weyl_pairwise_coupling.py"}],
    )

    report = module.result_surface()["system_v4/probes/a2_state/sim_results"]

    assert report["dirty_source_results"] == 1
    assert report["untracked_source_results"] == 1
    assert report["samples"]["untracked_source_results"] == ["sim_mera_weyl_pairwise_coupling_results.json"]
    assert report["fail_source_states"] == {"source_untracked_result_newer": 1}
    assert report["fail_details"] == [{
        "result": "sim_mera_weyl_pairwise_coupling_results.json",
        "source": "system_v4/probes/sim_mera_weyl_pairwise_coupling.py",
        "fail_mode": "summary_gate_false",
        "source_state": "source_untracked_result_newer",
        "action": "source_drift_review",
    }]


def test_system_surface_audit_tool_integration_flags_missing_torch_headers(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_tool_integration_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    (probes / "sim_torch_missing_headers.py").write_text(
        "\n".join(
            [
                "import torch",
                "",
                "classification = 'canonical'",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_torch_declared_headers.py").write_text(
        "\n".join(
            [
                "import torch",
                "TOOL_MANIFEST = {'pytorch': {'tried': True, 'used': True, 'reason': 'declared'}}",
                "TOOL_INTEGRATION_DEPTH = {'pytorch': 'load_bearing'}",
            ]
        ) + "\n",
        encoding="utf-8",
    )
    (probes / "sim_pytorch_capability.py").write_text(
        "TOOL_INTEGRATION_DEPTH = {'pytorch': 'load_bearing'}\n",
        encoding="utf-8",
    )
    (results / "pytorch_capability_results.json").write_text(
        '{"summary": {"all_pass": true}}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)

    report = module.tool_integration_surface()

    assert report["audited_sims_with_tool_imports"] == 2
    assert report["missing_manifest_by_tool"] == {"pytorch": 1}
    assert report["missing_depth_by_tool"] == {"pytorch": 1}
    assert report["samples"] == [{
        "sim": "sim_torch_missing_headers.py",
        "imported_tools": ["pytorch"],
        "missing_manifest_tools": ["pytorch"],
        "missing_depth_tools": ["pytorch"],
    }]
    assert report["per_tool"]["pytorch"]["status"] == "passing"
    assert report["per_tool"]["pytorch"]["imported_in_sims"] == 2
    assert report["per_tool"]["pytorch"]["load_bearing_witnesses"] == 1
    assert report["per_tool"]["pytorch"]["missing_manifest"] == 1
    assert report["per_tool"]["pytorch"]["missing_depth"] == 1


def test_system_surface_audit_tool_integration_reports_failing_capability_probe(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_tool_probe_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    repo = tmp_path / "repo"
    probes = repo / "system_v4" / "probes"
    results = probes / "a2_state" / "sim_results"
    probes.mkdir(parents=True, exist_ok=True)
    results.mkdir(parents=True, exist_ok=True)
    (probes / "sim_capability_cma_isolated.py").write_text(
        "TOOL_INTEGRATION_DEPTH = {'cma': 'load_bearing'}\n",
        encoding="utf-8",
    )
    (results / "sim_capability_cma_isolated_results.json").write_text(
        '{"summary": {"all_pass": false}}\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(module, "REPO", repo)
    monkeypatch.setattr(module, "PROBES", probes)
    monkeypatch.setattr(module, "RESULTS_DIR", results)

    report = module.tool_integration_surface()

    assert report["per_tool"]["cma"]["status"] == "probe_failing"
    assert report["per_tool"]["cma"]["probe_files"] == [
        "system_v4/probes/sim_capability_cma_isolated.py"
    ]


def test_system_surface_audit_runner_health_reports_draining() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_health_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    health = module._runner_health(
        {"lane_A": 1, "lane_B": 2, "claimed": 3, "done": 10},
        {
            "lane_A": {"active_within_60s": False},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": True},
            "done": {"active_within_60s": True},
        },
    )

    assert health["status"] == "draining"


def test_system_surface_audit_runner_health_reports_long_claims() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_health_long_claims_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    health = module._runner_health(
        {"lane_A": 0, "lane_B": 5, "claimed": 2, "done": 10},
        {
            "lane_A": {"active_within_60s": False},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": True},
            "done": {"active_within_60s": True},
        },
        {"over_900s": 1},
    )

    assert health["status"] == "draining_with_long_claims"


def test_system_surface_audit_runner_warnings_report_long_claims() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_warnings_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    warnings = module._runner_warnings(
        {"lane_A": 1, "lane_B": 2, "claimed": 1, "done": 10},
        {
            "lane_A": {"active_within_60s": False},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": True},
            "done": {"active_within_60s": True},
        },
        {"over_300s": 1, "over_900s": 0},
    )

    assert warnings == ["1 claim(s) over 300s"]


def test_system_surface_audit_runner_warnings_report_blocked_duplicates() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_runner_blocked_warnings_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    warnings = module._runner_warnings(
        {"lane_A": 1, "lane_B": 2, "claimed": 0, "done": 10},
        {
            "lane_A": {"active_within_60s": True},
            "lane_B": {"active_within_60s": True},
            "claimed": {"active_within_60s": False},
            "done": {"active_within_60s": True},
        },
        {"over_300s": 0, "over_900s": 0},
        {"active_count": 9, "unique_sims": 3, "duplicate_entries": 6},
    )

    assert warnings == ["9 blocked entry(s) across 3 unique sim(s)"]


def test_system_surface_audit_blocked_surface_reports_reasons_and_duplicates(
    tmp_path, monkeypatch
) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_blocked_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue_root = tmp_path / "queue"
    blocked = queue_root / "blocked"
    resolved = blocked / "resolved"
    blocked.mkdir(parents=True, exist_ok=True)
    resolved.mkdir(parents=True, exist_ok=True)
    for name in ("a.json.1.host.w1", "a.json.2.host.w2"):
        (blocked / name).write_text(
            json.dumps(
                {
                    "sim_path": "/tmp/sim_alpha.py",
                    "lane": "lane_A",
                    "blocked_reason": "gate_denied",
                }
            ),
            encoding="utf-8",
        )
    (blocked / "b.json.1.host.w1").write_text(
        json.dumps(
            {
                "sim_path": "/tmp/sim_beta.py",
                "lane": "lane_B",
                "blocked_reason": "blacklisted_meta_sim",
            }
        ),
        encoding="utf-8",
    )
    (resolved / "old.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(module.adaptive_controller, "QUEUE", queue_root)

    report = module._blocked_surface()

    assert report["active_count"] == 3
    assert report["resolved_count"] == 1
    assert report["reasons"] == {"gate_denied": 2, "blacklisted_meta_sim": 1}
    assert report["unique_sims"] == 2
    assert report["duplicate_entries"] == 1
    assert report["duplicate_sims"] == {"sim_alpha.py": 2}


def test_system_surface_audit_claimed_age_surface_uses_claimed_at(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_claimed_age_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    claimed = tmp_path / "claimed"
    claimed.mkdir()
    (claimed / "sample.json.1.host.laneB_w1").write_text(
        json.dumps({"sim_path": "/tmp/sim_alpha.py", "claimed_at": time.time() - 1200}),
        encoding="utf-8",
    )

    report = module._claimed_age_surface(claimed)

    assert report["count"] == 1
    assert report["over_900s"] == 1
    assert report["samples"][0]["sim"] == "sim_alpha.py"


def test_system_surface_audit_maintenance_queue_groups_actions() -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "system_surface_audit_maintenance_queue_under_test",
            REPO_ROOT / "scripts" / "system_surface_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue = module.maintenance_queue_surface(
        {
            "layers": {
                "owner_vault": 3,
                "probe_results": 4,
                "runner_logs": 1,
                "misplaced_probe_results": 2,
            },
            "cleanup_posture": {
                "owner_vault": "BLOCKED_REQUIRES_PREP",
                "probe_results": "KEEP_ACTIVE",
                "runner_logs": "KEEP_ACTIVE",
                "misplaced_probe_results": "REPAIR_TO_CANONICAL_ROOT",
            },
        },
        {
            "health": {"status": "draining"},
            "warnings": ["1 claim(s) over 300s"],
            "claimed_age": {"over_300s": 1},
            "blocked": {
                "active_count": 5,
                "reasons": {"gate_denied": 5},
                "unique_sims": 2,
                "duplicate_entries": 3,
                "samples": [{"sim": "sim_alpha.py", "reason": "gate_denied"}],
            },
        },
        {
            "system_v4/probes/a2_state/sim_results": {
                "fail_actions": {"rerun_candidate": 2, "missing_source_repair": 1},
                "fail_details": [
                    {"result": "a.json", "action": "rerun_candidate"},
                    {"result": "b.json", "action": "missing_source_repair"},
                ],
                "dirty_source_results": 1,
                "untracked_source_results": 0,
            }
        },
    )

    assert queue["git"]["blocked_entries"] == 3
    assert queue["git"]["repair_entries"] == 2
    assert queue["git"]["active_churn_entries"] == 5
    assert queue["runner"]["warnings"] == ["1 claim(s) over 300s"]
    assert queue["runner"]["blocked"]["duplicate_entries"] == 3
    assert queue["results"]["fail_actions"] == {"rerun_candidate": 2, "missing_source_repair": 1}
    assert queue["results"]["fail_action_samples"]["rerun_candidate"] == [{"result": "a.json", "action": "rerun_candidate"}]


def test_sim_program_audit_skips_invalid_queue_candidates(tmp_path) -> None:
    scripts_dir = str(REPO_ROOT / "scripts")
    sys.path.insert(0, scripts_dir)
    try:
        module = _load_module(
            "sim_program_audit_invalid_queue_under_test",
            REPO_ROOT / "scripts" / "sim_program_audit.py",
        )
    finally:
        if sys.path and sys.path[0] == scripts_dir:
            sys.path.pop(0)

    queue_root = tmp_path / "queue"
    lane_b = queue_root / "lane_B"
    lane_b.mkdir(parents=True, exist_ok=True)
    (lane_b / "bad.json").write_text('{"plan_bucket":"exploratory"}\n', encoding="utf-8")
    (lane_b / "good.json").write_text(
        '{"sim_path":"system_v4/probes/sim_good_alpha.py","plan_bucket":"core_ladder","priority":"high"}\n',
        encoding="utf-8",
    )

    module.QUEUE = queue_root

    assert module.queue_invalid_entry_summary() == {"lane_A": 0, "lane_B": 1}
    assert module.next_queue_candidates("lane_B", limit=5) == [{
        "sim": "sim_good_alpha.py",
        "priority": "high",
        "plan_bucket": "core_ladder",
        "plan_stage": "early_core",
    }]


def test_queue_claim_prefers_high_priority_items(tmp_path) -> None:
    module = _load_module(
        "queue_claim_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    low = lane / "b.json"
    low.write_text(
        '{"sim_path":"sim_low.py","lane":"lane_B","priority":"low"}\n',
        encoding="utf-8",
    )
    high = lane / "a.json"
    high.write_text(
        '{"sim_path":"sim_high.py","lane":"lane_B","priority":"high"}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_high.py"


def test_queue_claim_inferrs_priority_for_legacy_items(tmp_path) -> None:
    module = _load_module(
        "queue_claim_legacy_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    exploratory = lane / "b.json"
    exploratory.write_text(
        '{"sim_path":"sim_leviathan_control_surface.py","lane":"lane_B"}\n',
        encoding="utf-8",
    )
    core = lane / "a.json"
    core.write_text(
        '{"sim_path":"sim_weyl_chirality_bipartite.py","lane":"lane_B"}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_weyl_chirality_bipartite.py"


def test_queue_claim_prefers_core_ladder_when_priority_ties(tmp_path) -> None:
    module = _load_module(
        "queue_claim_bucket_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    exploratory = lane / "a.json"
    exploratory.write_text(
        '{"sim_path":"sim_leviathan_control_surface.py","lane":"lane_B","priority":"normal","enqueued_at":1}\n',
        encoding="utf-8",
    )
    core = lane / "b.json"
    core.write_text(
        '{"sim_path":"sim_weyl_chirality_bipartite.py","lane":"lane_B","priority":"normal","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_weyl_chirality_bipartite.py"


def test_queue_claim_promotes_stale_priority_to_bucket_default(tmp_path) -> None:
    module = _load_module(
        "queue_claim_priority_upgrade_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    stale_core = lane / "a.json"
    stale_core.write_text(
        '{"sim_path":"sim_qit_szilard_record_translation_lane.py","lane":"lane_B","priority":"normal","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    exploratory = lane / "b.json"
    exploratory.write_text(
        '{"sim_path":"sim_leviathan_control_surface.py","lane":"lane_B","priority":"normal","plan_bucket":"exploratory","enqueued_at":0}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_qit_szilard_record_translation_lane.py"


def test_queue_claim_demotes_axis_stage_within_core_ladder(tmp_path) -> None:
    module = _load_module(
        "queue_claim_stage_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    axis = lane / "a.json"
    axis.write_text(
        '{"sim_path":"sim_axis0_kernel_phi0.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_z3_negative_quasiprob_exclusion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_z3_negative_quasiprob_exclusion.py"


def test_queue_claim_demotes_late_info_stage_within_core_ladder(tmp_path) -> None:
    module = _load_module(
        "queue_claim_late_info_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    late_info = lane / "a.json"
    late_info.write_text(
        '{"sim_path":"sim_qit_carnot_finite_time_companion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_z3_negative_quasiprob_exclusion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_z3_negative_quasiprob_exclusion.py"


def test_queue_claim_classifies_coherent_info_as_late_info(tmp_path) -> None:
    module = _load_module(
        "queue_claim_coherent_info_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    late_info = lane / "a.json"
    late_info.write_text(
        '{"sim_path":"sim_lego_coherent_info_advanced.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_z3_negative_quasiprob_exclusion.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_z3_negative_quasiprob_exclusion.py"


def test_queue_claim_classifies_entanglement_as_late_info(tmp_path) -> None:
    module = _load_module(
        "queue_claim_entanglement_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    late_info = lane / "a.json"
    late_info.write_text(
        '{"sim_path":"sim_lego_entanglement_distillation.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":1}\n',
        encoding="utf-8",
    )
    early = lane / "b.json"
    early.write_text(
        '{"sim_path":"sim_geom_cp1_u1_projective.py","lane":"lane_B","priority":"high","plan_bucket":"core_ladder","enqueued_at":2}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_geom_cp1_u1_projective.py"


def test_autonomous_reseed_loop_uses_deterministic_stage_aware_enqueue() -> None:
    text = (REPO_ROOT / "scripts" / "autonomous_reseed_loop.sh").read_text(encoding="utf-8")
    assert "plan_stage_for_sim()" in text
    assert "hashlib.sha1" in text
    assert '"plan_stage": stage' in text
    assert "secrets.token_hex" not in text


def test_queue_claim_prefers_older_items_when_rank_ties(tmp_path) -> None:
    module = _load_module(
        "queue_claim_fifo_under_test",
        REPO_ROOT / "scripts" / "queue_claim.py",
    )
    repo = tmp_path / "repo"
    queue_root = repo / "system_v4" / "probes" / "a2_state" / "queue"
    lane = queue_root / "lane_B"
    lane.mkdir(parents=True, exist_ok=True)
    (queue_root / "claimed").mkdir(parents=True, exist_ok=True)

    module.QUEUE_ROOT = queue_root
    newer = lane / "a.json"
    newer.write_text(
        '{"sim_path":"sim_probe_object.py","lane":"lane_B","priority":"normal","enqueued_at":20}\n',
        encoding="utf-8",
    )
    older = lane / "z.json"
    older.write_text(
        '{"sim_path":"sim_characteristic_representation.py","lane":"lane_B","priority":"normal","enqueued_at":10}\n',
        encoding="utf-8",
    )

    claimed = module.claim("lane_B", "w1")

    assert claimed is not None
    payload = json.loads(claimed.read_text(encoding="utf-8"))
    assert payload["sim_path"] == "sim_characteristic_representation.py"


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
