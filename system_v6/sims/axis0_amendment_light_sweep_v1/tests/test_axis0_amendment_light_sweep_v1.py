from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PYTHON = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
SIM_DIR = ROOT / "system_v6" / "sims" / "axis0_amendment_light_sweep_v1"
VALIDATOR = SIM_DIR / "validate_axis0_amendment_light_sweep_v1.py"
VALIDATOR_RESULT = SIM_DIR / "results" / "axis0_amendment_light_sweep_v1_validator_results.json"


def test_axis0_amendment_light_sweep_v1_validator_passes() -> None:
    subprocess.run([PYTHON, str(VALIDATOR)], cwd=ROOT, check=True)
    payload = json.loads(VALIDATOR_RESULT.read_text(encoding="utf-8"))
    assert payload["all_pass"] is True
    assert payload["gates"]["v0_regression_pin_bite_computed"] is True
    assert payload["gates"]["julia_exact_mirror_aligned"] is True
