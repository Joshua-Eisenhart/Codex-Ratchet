from __future__ import annotations

from constraintbox_zip_agent.mmm_ab_probe import run_mmm_ab_probe


def test_mmm_ab_probe_observes_delivery_difference_not_cognition() -> None:
    report = run_mmm_ab_probe(seed=461)
    assert report["difference_observed"] is True
    assert report["changed_outputs"] == [
        "output/failure.md",
        "output/repair.md",
        "output/strategy.md",
    ]
    assert report["mmm_read_proved"] is False
    assert report["promotion_allowed"] is False
    assert report["packet_a_sha256"] != report["packet_b_sha256"]
    assert report["mmm_sha256_a"] != report["mmm_sha256_b"]
    assert "not_cognition" in report["claim_ceiling"]


def test_mmm_ab_probe_is_replayable() -> None:
    first = run_mmm_ab_probe(seed=461)
    second = run_mmm_ab_probe(seed=461)
    assert first == second
