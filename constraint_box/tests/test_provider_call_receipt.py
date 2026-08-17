from __future__ import annotations

from typing import Any

from constraintbox.provider_call_receipt import (
    VERIFIED_REASON,
    build_provider_call_envelope,
    provider_call_validation_reasons,
    provider_call_verdict,
)

H = "a" * 64
B = "b" * 64
C = "c" * 64
D = "d" * 64
E = "e" * 64


def _envelope(**overrides):
    base: dict[str, Any] = dict(
        run_id="run-1",
        agent_id="AGENTS/paraphraser.md",
        parent_id=None,
        wave_id="prompt-handshake",
        round_index=0,
        depth=0,
        preload_receipt_sha256=H,
        provider="codex-cli",
        route="luna",
        model_requested="gpt-5.6-luna",
        model_observed="gpt-5.6-luna",
        prompt_sha256=B,
        request_sha256=C,
        response_sha256=D,
        terminal_state="OBSERVED",
        source_receipt_schema="constraintbox.codex-cli-receipt.v1",
        source_receipt_sha256=E,
        budget={"max_calls": 1, "max_seconds": 600},
        usage={"cost_usd": None},
    )
    base.update(overrides)
    return build_provider_call_envelope(**base)


def test_provider_call_envelope_can_earn_mmm_call_verified() -> None:
    env = _envelope()
    verdict = provider_call_verdict(env)
    assert verdict["verdict"] == "VERIFIED"
    assert verdict["reason_code"] == VERIFIED_REASON
    assert env["promotion_allowed"] is False
    assert env["claim_ceiling"].startswith("one normalized provider call")


def test_missing_preload_receipt_blocks_mmm_call_verified() -> None:
    env = _envelope(preload_receipt_sha256="")
    reasons = provider_call_validation_reasons(env)
    assert "INVALID_PRELOAD_RECEIPT_SHA256" in reasons
    assert provider_call_verdict(env)["verdict"] == "HOLD"


def test_tampered_envelope_hash_blocks_verification() -> None:
    env = _envelope()
    env["model_observed"] = "gpt-5.6-sol"
    reasons = provider_call_validation_reasons(env)
    assert "PROVIDER_CALL_HASH_MISMATCH" in reasons
