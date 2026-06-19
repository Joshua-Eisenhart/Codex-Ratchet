from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "codex_model_quality_swarm.py"


def _load_swarm():
    spec = importlib.util.spec_from_file_location("codex_model_quality_swarm_under_test", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        return module
    finally:
        sys.modules.pop(spec.name, None)


def test_extract_openai_chat_text_preserves_reasoning_only_content_null() -> None:
    swarm = _load_swarm()

    extracted = swarm.extract_openai_chat_text(
        {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "reasoning": "Use the neutral sim_id; do not promote model output.",
                    },
                    "finish_reason": "length",
                }
            ],
            "usage": {"completion_tokens_details": {"reasoning_tokens": 450}},
        }
    )

    assert extracted["output_text"] == "Use the neutral sim_id; do not promote model output."
    assert extracted["content_was_null"] is True
    assert extracted["reasoning_present"] is True
    assert extracted["extraction_status"] == "reasoning_only_content_null"


def test_score_output_rewards_repo_specific_actionable_boundary_work() -> None:
    swarm = _load_swarm()
    output = """
    Patch scripts/codex_sim_runner.py so wizard_sim_admission uses the neutral
    sim_id instead of probe_quotient_fingerprint_floor_v1_three_engine for the
    admission basename. This avoids nonclassical_suitable_load_bearing_tool_missing
    without changing scripts/wizard_sim_admission.py or two_root_constraints.py.
    Add system_v5/tests/test_codex_sim_runner.py coverage, then run python3 -m
    pytest -q system_v5/tests/test_codex_sim_runner.py and python3
    scripts/wizard_sim_admission.py with the refreshed codex_probe_quotient...
    packet. This is proposal-only, not sim evidence, no promotion, and the
    deterministic JAX/Julia/SMT runner remains authoritative. Stop if the fresh
    validator still reports nonclassical_load_bearing_tool_missing_two_root_registry.
    """

    score = swarm.score_output(output)

    assert score["accepted"] is True
    assert score["total"] >= 55
    assert score["components"]["evidence_specificity"] > 0
    assert score["components"]["gate_alignment"] > 0


def test_score_output_rejects_generic_short_text() -> None:
    swarm = _load_swarm()

    score = swarm.score_output("Looks good. I would improve the tests.")

    assert score["accepted"] is False
    assert score["total"] < 55
    assert "too_short" in score["penalties"]


def test_child_receipt_is_proposal_only_and_blocks_evidence_consumers() -> None:
    swarm = _load_swarm()
    route = swarm.DEFAULT_ROUTES[2]

    child = swarm.child_completed(
        route,
        {"choices": []},
        {
            "output_text": "scripts/codex_sim_runner.py should preserve no promotion boundaries.",
            "extraction_source": "content",
            "extraction_status": "usable_content",
            "content_was_null": False,
            "content_empty": False,
            "reasoning_present": False,
        },
        http_status=200,
    )

    assert child["proposal_only"] is True
    assert child["promotion_allowed"] is False
    assert child["formal_admission_allowed"] is False
    assert child["model_outputs_are_sim_evidence"] is False
    assert "sim_admission" in child["blocked_consumers"]
    assert "formal_evidence" in child["blocked_consumers"]


def test_build_report_separates_reasoning_only_from_usable_content() -> None:
    swarm = _load_swarm()
    children = [
        {
            "child_id": "usable",
            "status": "completed",
            "runtime": "openrouter-fusion",
            "model": "openrouter/fusion",
            "route": "decision_council",
            "extraction": {"extraction_status": "usable_content"},
            "score": {"accepted": True, "total": 80},
        },
        {
            "child_id": "reasoning_only",
            "status": "completed",
            "runtime": "top-chinese-models",
            "model": "moonshotai/kimi-k2.7-code",
            "route": "followup_audit",
            "extraction": {"extraction_status": "reasoning_only_content_null"},
            "score": {"accepted": True, "total": 88},
        },
    ]

    report = swarm.build_report(
        prompt="audit prompt",
        prompt_path=None,
        children=children,
        child_paths=["/tmp/usable.json", "/tmp/reasoning.json"],
        run_id="test",
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
    )

    assert report["accepted_model_count"] == 2
    assert report["usable_content_model_count"] == 1
    assert report["reasoning_only_model_count"] == 1
    assert report["usable_model_outputs"] == ["usable"]
    assert report["reasoning_only_outputs"] == ["reasoning_only"]
