#!/usr/bin/env python3
"""PyDMD on three physical observables of a receipt-derived GKSL channel."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "results" / "pydmd.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SOURCE = ROOT / "system_v8/engine_native/results/julia_manifold/receipt.json"


def memory_free_percent() -> int:
    text = subprocess.run(["memory_pressure"], capture_output=True, text=True, check=True).stdout
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", text)
    if not m: raise RuntimeError("memory_pressure did not report a free percentage")
    return int(m.group(1))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {"tool": "PyDMD", "promotion_allowed": False,
              "claim_ceiling": "tool-integration evidence only; not an admission claim",
              "source": str(SOURCE), "interpreter": sys.executable}
    try:
        free = memory_free_percent()
        if free <= 25: raise RuntimeError(f"memory free percentage {free}% is not > 25%")
        if Path(sys.executable).resolve() != SIM_PY.resolve(): raise RuntimeError(f"canonical interpreter required: {SIM_PY}")
        from pydmd import DMD
        gamma = float(np.mean(json.loads(SOURCE.read_text())["data"]["base_series"]["gamma"]))
        dt, times = .04, np.arange(201) * .04
        # rho0_L has x=.5,y=.3,z=-.4 in the QIT referee.  Retain its
        # omega=1.3 Z-Hamiltonian: population decays at gamma and the two
        # coherences rotate while decaying at gamma/2, producing three real,
        # linearly independent physical observables.
        omega = 1.3
        decay = np.exp(-gamma * times / 2)
        multiobservable = np.vstack((.7 * np.exp(-gamma * times),
                                      decay * (.5 * np.cos(omega * times) - .3 * np.sin(omega * times)),
                                      decay * (.3 * np.cos(omega * times) + .5 * np.sin(omega * times))))
        fit = DMD(svd_rank=3, exact=True).fit(multiobservable)
        recovered = np.log(fit.eigs) / dt
        expected = np.array([-gamma, -gamma / 2 - 1j * omega, -gamma / 2 + 1j * omega])
        recovered = recovered[np.argsort(recovered.imag)]
        expected = expected[np.argsort(expected.imag)]
        max_error = float(np.max(np.abs(recovered - expected)))
        reconstruction = float(np.max(np.abs(fit.reconstructed_data.real - multiobservable)))
        checks = {"memory_gate_gt_25": free > 25,
                  "three_gksl_observable_eigenvalues_match_known_law_2pct": max_error / gamma <= .02,
                  "reconstruction_max_abs_lt_1e-10": reconstruction < 1e-10}
        result.update({"verdict": "INTEGRATED" if all(checks.values()) else "BLOCKED", "checks": checks, "real_object": "three observables of the QIT-referee amplitude-damping initial state", "computed_number": max_error,
                       "data": {"gamma": gamma, "dt": dt, "observables": ["excited_population", "bloch_x", "bloch_y"],
                       "omega": omega, "continuous_eigenvalues": [[float(x.real), float(x.imag)] for x in recovered], "expected": [[float(x.real), float(x.imag)] for x in expected],
                       "max_abs_error": max_error, "reconstruction_max_abs": reconstruction},
                       "finding": "PyDMD modes/eigenvalues are load-bearing for the three-observable amplitude-damping law comparison."})
    except Exception as exc:
        result.update({"verdict": "BLOCKED", "exact_error": f"{type(exc).__name__}: {exc}"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__": main()
