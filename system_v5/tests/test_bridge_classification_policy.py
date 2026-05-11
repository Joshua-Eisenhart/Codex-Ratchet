from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT / "system_v5/ops/bridge_classification_policy.md"


def test_bridge_policy_names_admission_boundary() -> None:
    text = POLICY.read_text()

    assert "`bridge` is a runner admission class" in text
    assert "not a scientific promotion" in text
    assert "not admissible as axis, QIT, GStack, bridge-claim, or assembly evidence" in text
    assert "v4.2 Wizard admission artifact" in text
