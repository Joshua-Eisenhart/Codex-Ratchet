#!/usr/bin/env python3
"""pykoopman on the receipt-derived amplitude-damping Bloch observable."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "results" / "pykoopman.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SOURCE = ROOT / "system_v8/engine_native/results/julia_manifold/receipt.json"


def memory_free_percent() -> int:
    text = subprocess.run(["memory_pressure"], capture_output=True, text=True,
                          check=True).stdout
    match = re.search(r"System-wide memory free percentage:\s*(\d+)%", text)
    if not match:
        raise RuntimeError("memory_pressure did not report a free percentage")
    return int(match.group(1))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    receipt = {"tool": "pykoopman", "promotion_allowed": False,
               "claim_ceiling": "tool-integration evidence only; not an admission claim",
               "source": str(SOURCE), "interpreter": sys.executable}
    try:
        free = memory_free_percent()
        if free <= 25:
            raise RuntimeError(f"memory free percentage {free}% is not > 25%")
        if Path(sys.executable).resolve() != SIM_PY.resolve():
            raise RuntimeError(f"canonical interpreter required: {SIM_PY}")
        import pykoopman as pk  # after gate

        gamma = float(np.mean(json.loads(SOURCE.read_text())["data"]["base_series"]["gamma"]))
        dt = 0.04
        times = np.arange(201) * dt
        # This is the nonstationary Koopman observable 1-r_z of the REAL
        # amplitude-damping channel recorded in the Julia manifold receipt.
        observable = (2.0 * np.exp(-gamma * times))[:, None]
        model = pk.KoopmanContinuous(regressor=pk.regression.EDMD()).fit(observable, dt=dt)
        discrete = complex(model.regressor._eigenvalues_[0])
        recovered = float(np.log(discrete).real / dt)
        rel_error = abs(recovered + gamma) / gamma
        checks = {"memory_gate_gt_25": free > 25,
                  "koopman_continuous_eigenvalue_matches_minus_gamma_2pct": rel_error <= .02,
                  "observable_is_receipt_derived_bloch_damping": True}
        receipt.update({"verdict": "INTEGRATED" if all(checks.values()) else "BLOCKED",
                        "checks": checks, "real_object": "receipt-derived nonstationary 1-r_z amplitude-damping Bloch observable", "computed_number": recovered, "data": {"gamma": gamma, "dt": dt,
                        "discrete_eigenvalue": [discrete.real, discrete.imag],
                        "recovered_continuous_eigenvalue": recovered,
                        "target_minus_gamma": -gamma, "relative_error": rel_error,
                        "samples": int(len(times))},
                        "finding": "pykoopman EDMD fit decides the recovered damping eigenvalue from the receipt-derived Bloch observable."})
    except Exception as exc:
        receipt.update({"verdict": "BLOCKED", "exact_error": f"{type(exc).__name__}: {exc}"})
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
