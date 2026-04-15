from __future__ import annotations

import importlib.util
import json
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
    assert payload["plan_bucket"] == "core_ladder"
    assert payload["plan_stage"] == "late_info"
    assert payload["priority"] == "high"


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
