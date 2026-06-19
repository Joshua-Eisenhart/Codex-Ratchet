import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SIM_DIR = ROOT / "system_v6" / "sims" / "render_layer_readout_v0"
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def test_render_layer_validator_passes() -> None:
    subprocess.run(
        [PY, str(SIM_DIR / "validate_render_layer_readout_v0.py")],
        cwd=ROOT,
        check=True,
    )
    result = json.loads((SIM_DIR / "results" / "render_layer_readout_v0_validator_results.json").read_text())
    assert result["all_pass"] is True


def test_render_layer_result_stays_bounded() -> None:
    payload = json.loads((SIM_DIR / "results" / "render_layer_readout_v0_envelope_results.json").read_text())
    assert payload["classification"] == "scratch_diagnostic"
    assert payload["promotion_allowed"] is False
    assert payload["formal_admission_allowed"] is False
    assert payload["axis0_boundary"]["boundary_verdict"]["verdict"] == "no_stable_distinction"
    assert "physics admission" in payload["disallowed_claims"]
