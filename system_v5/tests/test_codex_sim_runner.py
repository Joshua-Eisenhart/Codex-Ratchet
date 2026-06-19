from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "scripts" / "codex_sim_runner.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("codex_sim_runner_under_test", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(spec.name, None)


def test_three_engine_gap_report_names_missing_fields() -> None:
    runner = _load_runner()
    payload = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "pairs": [],
    }

    gaps = runner.three_engine_schema_gap_report(payload)

    assert gaps["schema"] == "not_three_engine_sim_result_v1"
    assert gaps["ok"] is False
    assert gaps["missing_or_invalid"] == [
        "schema_version=three_engine_sim_result_v1",
        "engines.julia",
        "engines.jax",
        "crossover_proofs.z3",
        "crossover_proofs.cvc5",
        "divergence.engine_values.julia",
        "divergence.engine_values.jax",
        "divergence.max_divergence",
        "divergence.julia_authoritative=true",
    ]


def test_three_engine_gap_report_accepts_minimal_valid_envelope() -> None:
    runner = _load_runner()
    payload = {
        "schema_version": "three_engine_sim_result_v1",
        "engines": {
            "julia": {"ran": True},
            "jax": {"ran": True},
        },
        "crossover_proofs": {
            "z3": {"ran": True},
            "cvc5": {"ran": True},
        },
        "divergence": {
            "engine_values": {"julia": 5, "jax": 5},
            "max_divergence": 0.0,
            "julia_authoritative": True,
        },
    }

    gaps = runner.three_engine_schema_gap_report(payload)

    assert gaps == {
        "schema": "three_engine_sim_result_v1",
        "ok": True,
        "missing_or_invalid": [],
    }


def test_build_admission_payload_matches_real_validator_shape(tmp_path: Path) -> None:
    runner = _load_runner()
    sim_path = REPO_ROOT / "system_v7/sims/order_sensitivity_noncommutation_floor_v0/order_sensitivity_scratch_diagnostic.py"
    result_path = tmp_path / "order_sensitivity_scratch_diagnostic_results.json"
    result_path.write_text(json.dumps({"classification": "scratch_diagnostic"}) + "\n", encoding="utf-8")
    artifact_path = tmp_path / "order_sensitivity_scratch_diagnostic_admission_artifact.json"
    artifact_path.write_text(
        json.dumps(
            {
                "kind": "codex_sim_runner_admission_artifact",
                "result_path": str(result_path),
                "result_sha256": runner.sha256(result_path),
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = runner.build_admission_payload(
        repo_root=REPO_ROOT,
        basename="order_sensitivity_scratch_diagnostic",
        sim_path=sim_path,
        result_path=result_path,
        artifact_path=artifact_path,
        stage="micro",
        tool_target="z3",
        claim_ceiling="scratch_diagnostic; no promotion",
    )

    assert payload["schema"] == "wizard_sim_admission_v4_2"
    assert payload["basename"] == "order_sensitivity_scratch_diagnostic"
    assert payload["status"] == "queue_ready"
    assert payload["admitted_by"] == "guard.receipt_audit"
    assert payload["sim_path"] == str(sim_path.relative_to(REPO_ROOT))
    assert payload["controller_read_artifacts"] == [str(artifact_path), str(result_path)]
    assert payload["formal_sim_profile"]["stage"] == "micro"
    assert payload["formal_sim_profile"]["expected_result_path"] == str(result_path)
    assert payload["packet_contract"]["tool_target"] == "z3"
    assert payload["packet_contract"]["promotion_boundary"] == (
        "no promotion beyond scratch_diagnostic without a later admitted packet"
    )


def test_admission_artifact_tolerates_missing_result_path(tmp_path: Path) -> None:
    runner = _load_runner()
    sim_path = tmp_path / "sim.py"
    sim_path.write_text("print('ok')\n", encoding="utf-8")
    missing_result = tmp_path / "missing_results.json"

    payload = runner.admission_artifact_payload(
        basename="missing",
        sim_path=sim_path,
        result_path=missing_result,
        result_payload={},
    )

    assert payload["sim_sha256"] == runner.sha256(sim_path)
    assert payload["result_sha256"] is None
    assert payload["classification"] is None


def test_seat_certify_rejects_stale_preexisting_result(tmp_path: Path) -> None:
    runner = _load_runner()
    sim_path = tmp_path / "no_write.py"
    sim_path.write_text("print('no result write')\n", encoding="utf-8")
    result_path = tmp_path / "no_write_results.json"
    result_path.write_text(json.dumps({"stale": True}) + "\n", encoding="utf-8")

    report = runner.seat_certify(
        python=Path(sys.executable),
        sim_path=sim_path,
        result_path=result_path,
        runs=1,
        timeout=5,
    )

    assert report["all_exited_zero"] is True
    assert report["all_result_exists"] is True
    assert report["all_result_fresh"] is False
    assert report["ok"] is False


def test_purgatory_record_does_not_write_graph_by_default() -> None:
    runner = _load_runner()
    record = runner.purgatory_record(
        basename="candidate",
        result_path=Path("/tmp/candidate_results.json"),
        result_payload={
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "all_pass": True,
        },
        gate_reports={"seat_certify": {"ok": True}},
    )
    graveyard = runner.route_to_graveyard_if_requested(
        repo_root=REPO_ROOT,
        record=record,
        enabled=False,
    )

    assert record["status"] == "resident_purgatory"
    assert record["failure_class"] == "PARKED_NOT_FAILURE"
    assert graveyard["status"] == "not_written"
    assert "shared graph mutation stays controller-serial" in graveyard["reason"]


def test_wizard_v43_missing_packet_blocks_full_wizard_claim() -> None:
    runner = _load_runner()

    report = runner.validate_wizard_v43_object_packet(
        python=Path(sys.executable),
        packet_path=None,
        timeout=1,
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_missing_packet"
    assert report["runtime"] == runner.CURRENT_WIZARD_RUNTIME


def test_swarm_truth_report_requires_manifest_for_model_counts() -> None:
    runner = _load_runner()

    report = runner.swarm_truth_report(
        manifest_path=None,
        required_models=["gemini-tui", "grok-api"],
        required_routes=["decision_council"],
    )

    assert report["ok"] is False
    assert report["status"] == "blocked_missing_manifest"
    assert report["missing_required_models"] == ["gemini-tui", "grok-api"]
    assert report["missing_required_routes"] == ["decision_council"]


def test_swarm_truth_report_accepts_completed_parent_child_receipts(tmp_path: Path) -> None:
    runner = _load_runner()
    gemini_receipt = tmp_path / "gemini.json"
    grok_receipt = tmp_path / "grok.json"
    gemini_receipt.write_text(
        json.dumps(
            {
                "schema": "codex_model_child_receipt_v1",
                "child_id": "c1",
                "runtime": "gemini-tui",
                "model": "gemini-2.5-flash",
                "route": "decision_council",
                "status": "completed",
                "proposal_only": True,
                "content": "proposal-only decision audit",
                "launch_surface": "multi_agent_v1_parent_spawned_child",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    grok_receipt.write_text(
        json.dumps(
            {
                "schema": "codex_model_child_receipt_v1",
                "child_id": "c2",
                "runtime": "grok-api",
                "model": "grok-4.3",
                "route": "followup_audit",
                "status": "completed",
                "proposal_only": True,
                "content": "proposal-only followup audit",
                "launch_surface": "multi_agent_v1_parent_spawned_child",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "swarm.json"
    manifest.write_text(
        json.dumps(
            {
                "schema": "codex_model_swarm_manifest_v1",
                "required_models": ["gemini-tui", "grok-api"],
                "required_routes": ["decision_council", "followup_audit"],
                "parents": [
                    {
                        "parent_id": "p1",
                        "runtime": "codex-native",
                        "route": "decision_council",
                        "status": "completed",
                        "children": [
                            {
                                "child_id": "c1",
                                "runtime": "gemini-tui",
                                "model": "gemini-2.5-flash",
                                "route": "decision_council",
                                "status": "completed",
                                "receipt_path": str(gemini_receipt),
                                "proposal_only": True,
                                "launch_surface": "multi_agent_v1_parent_spawned_child",
                            },
                            {
                                "child_id": "c2",
                                "runtime": "grok-api",
                                "model": "grok-4.3",
                                "route": "followup_audit",
                                "status": "completed",
                                "receipt_path": str(grok_receipt),
                                "proposal_only": True,
                                "launch_surface": "multi_agent_v1_parent_spawned_child",
                            },
                        ],
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = runner.swarm_truth_report(
        manifest_path=manifest,
        required_models=[],
        required_routes=[],
    )

    assert report["ok"] is True
    assert report["status"] == "coverage_passed"
    assert report["hierarchy_complete"] is True
    assert report["completed_parents"] == 1
    assert report["completed_children"] == 2
    assert report["missing_required_models"] == []
    assert report["missing_required_routes"] == []
    assert report["missing_child_receipts"] == []
    assert report["receipt_integrity_errors"] == []
    assert report["non_proposal_children"] == []
    assert report["unusable_child_outputs"] == []


def test_cocoindex_grounding_report_requires_exact_wiki_and_repo_reads(tmp_path: Path) -> None:
    runner = _load_runner()
    wiki_hit = tmp_path / "wiki.md"
    repo_hit = tmp_path / "repo.py"
    wiki_hit.write_text("wiki hit\n", encoding="utf-8")
    repo_hit.write_text("repo hit\n", encoding="utf-8")
    receipt = tmp_path / "cocoindex.json"
    receipt.write_text(
        json.dumps(
            {
                "schema": "codex_cocoindex_grounding_receipt_v1",
                "queries": ["sim runner wizard swarm"],
                "hits": [
                    {
                        "corpus": "wiki",
                        "path": str(wiki_hit),
                        "exact_read": True,
                        "retrieval": "cocoindex_wiki",
                        "lines": [1, 1],
                    },
                    {
                        "corpus": "repo",
                        "path": str(repo_hit),
                        "exact_read": True,
                        "retrieval": "cocoindex_repo",
                        "lines": [1, 1],
                    },
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = runner.cocoindex_grounding_report(
        receipt_path=receipt,
        required_corpora=["wiki", "repo"],
    )

    assert report["ok"] is True
    assert report["status"] == "passed"
    assert report["corpora_with_exact_reads"] == ["repo", "wiki"]


def test_full_wizard_obligation_report_stays_partial_when_swarm_is_missing() -> None:
    runner = _load_runner()

    report = runner.full_wizard_obligation_report(
        wizard_v43={"ok": True},
        deterministic_harness={"ok": True},
        swarm={
            "ok": False,
            "missing_required_models": ["openrouter-fusion"],
            "missing_required_routes": ["failure_council"],
        },
        cocoindex_grounding={"ok": True, "corpora_with_exact_reads": ["wiki", "repo"]},
    )

    assert report["ok"] is False
    assert report["status"] == "partial"
    assert "swarm_model:openrouter-fusion" in report["missing_obligations"]
    assert "swarm_route:failure_council" in report["missing_obligations"]


def test_admission_basename_uses_neutral_sim_id_for_three_engine_envelope() -> None:
    runner = _load_runner()

    basename = runner.admission_basename_from_result(
        {
            "sim_id": "probe_quotient_fingerprint_floor_v1",
            "classification": "scratch_diagnostic",
        },
        "probe_quotient_fingerprint_floor_v1_three_engine",
    )

    assert basename == "probe_quotient_fingerprint_floor_v1"


def test_model_quality_swarm_report_is_advisory_and_boundary_checked(tmp_path: Path) -> None:
    runner = _load_runner()
    report_path = tmp_path / "quality.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "codex_model_quality_swarm_report_v1",
                "proposal_only": True,
                "promotion_allowed": False,
                "formal_admission_allowed": False,
                "model_outputs_are_sim_evidence": False,
                "status": "quality_passed",
                "completed_model_count": 1,
                "accepted_model_count": 1,
                "children": [
                    {
                        "child_id": "fusion_decision",
                        "proposal_only": True,
                        "promotion_allowed": False,
                        "formal_admission_allowed": False,
                        "model_outputs_are_sim_evidence": False,
                        "blocked_consumers": [
                            "sim_admission",
                            "formal_evidence",
                            "canonical_status",
                        ],
                        "extraction": {"extraction_status": "usable_content"},
                        "score": {"accepted": True, "total": 78},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = runner.model_quality_swarm_report(report_path=report_path)

    assert report["ok"] is True
    assert report["status"] == "accepted_advisory"
    assert report["gate_participation"] == "advisory_only_not_sim_gate"
    assert report["usable_outputs"] == ["fusion_decision"]
    assert report["boundary_errors"] == []


def test_model_quality_swarm_report_blocks_promotion_leak(tmp_path: Path) -> None:
    runner = _load_runner()
    report_path = tmp_path / "quality_bad.json"
    report_path.write_text(
        json.dumps(
            {
                "schema": "codex_model_quality_swarm_report_v1",
                "proposal_only": True,
                "promotion_allowed": False,
                "formal_admission_allowed": False,
                "model_outputs_are_sim_evidence": False,
                "children": [
                    {
                        "child_id": "bad_child",
                        "proposal_only": False,
                        "promotion_allowed": True,
                        "formal_admission_allowed": False,
                        "model_outputs_are_sim_evidence": True,
                        "blocked_consumers": [],
                        "extraction": {"extraction_status": "usable_content"},
                        "score": {"accepted": True, "total": 99},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = runner.model_quality_swarm_report(report_path=report_path)

    assert report["ok"] is False
    assert report["status"] == "blocked_or_invalid"
    assert "bad_child:proposal_only_not_true" in report["boundary_errors"]
    assert "bad_child:promotion_allowed_not_false" in report["boundary_errors"]
    assert "bad_child:model_outputs_are_sim_evidence_not_false" in report["boundary_errors"]
