from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER_PATH = REPO_ROOT / "scripts" / "integration" / "loop_to_system_runner.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("loop_to_system_runner_under_test", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(spec.name, None)


def test_three_engine_gap_report_names_missing_envelope_fields() -> None:
    runner = _load_runner()
    payload = {
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "pairs": [],
    }

    gaps = runner.three_engine_schema_gap_report(payload)

    assert gaps["schema"] == "not_three_engine_sim_result_v1"
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


def test_build_admission_payload_matches_real_validator_contract(tmp_path: Path) -> None:
    runner = _load_runner()
    sim_path = REPO_ROOT / "system_v7/sims/order_sensitivity_noncommutation_floor_v0/order_sensitivity_scratch_diagnostic.py"
    result_path = tmp_path / "order_sensitivity_scratch_diagnostic_results.json"
    result_path.write_text(json.dumps({"classification": "scratch_diagnostic"}) + "\n", encoding="utf-8")
    artifact_path = tmp_path / "order_sensitivity_scratch_diagnostic_admission_artifact.json"
    artifact_path.write_text(
        json.dumps(
            {
                "kind": "admission_artifact",
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
