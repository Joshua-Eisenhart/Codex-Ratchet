#!/usr/bin/env python3
"""qutip-jax backend solve of the real amplitude-damping referee channel."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "results" / "qutip_jax.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SOURCE = ROOT / "system_v8/deep_integration/results/qit_referee/receipt.json"


def memory_free_percent() -> int:
    s = subprocess.run(["memory_pressure"], capture_output=True, text=True, check=True).stdout
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", s)
    if not m: raise RuntimeError("memory_pressure did not report a free percentage")
    return int(m.group(1))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {"tool": "qutip-jax", "promotion_allowed": False,
              "claim_ceiling": "tool-integration evidence only; not an admission claim",
              "source": str(SOURCE), "interpreter": sys.executable}
    try:
        free = memory_free_percent()
        if free <= 25: raise RuntimeError(f"memory free percentage {free}% is not > 25%")
        if Path(sys.executable).resolve() != SIM_PY.resolve(): raise RuntimeError(f"canonical interpreter required: {SIM_PY}")
        import qutip as qt
        import qutip_jax
        qutip_jax.set_as_default()
        gamma, t_final = .5, 12.
        rho0 = .5 * (qt.qeye(2) + .5 * qt.sigmax() + .3 * qt.sigmay() - .4 * qt.sigmaz())
        solved = qt.mesolve(0.0 * qt.sigmaz(), rho0, np.linspace(0., t_final, 31),
                            [np.sqrt(gamma) * qt.destroy(2)])
        final = solved.states[-1].full()
        pop = float(np.real(final[1, 1]))
        known = float(.7 * np.exp(-gamma * t_final))
        err = abs(pop - known)
        trace_error = float(abs(np.trace(final) - 1.0))
        receipt = json.loads(SOURCE.read_text())
        checks = {"memory_gate_gt_25": free > 25, "qutip_jax_backend_selected": qt.settings.core["default_dtype"] == "jax",
                  "qutip_jax_gksl_matches_known_referee_channel_1e-8": err < 1e-8,
                  "trace_preserved_1e-9": trace_error < 1e-9,
                  "referee_receipt_loaded": receipt["checks"]["qutip_lawA_series_matches_julia_lt_1e-6"]}
        result.update({"verdict": "INTEGRATED" if all(checks.values()) else "BLOCKED", "checks": checks, "real_object": "QIT-referee amplitude-damping manifold channel", "computed_number": err,
                       "data": {"gamma": gamma, "t_final": t_final, "excited_population_qutip_jax": pop,
                       "known_qutip_referee_family_population": known, "abs_error": err, "trace_error": trace_error},
                       "finding": "The qutip-jax Diffrax backend, not ordinary qutip, evolves the receipt-family channel and decides the agreement gate."})
    except Exception as exc:
        result.update({"verdict": "BLOCKED", "exact_error": f"{type(exc).__name__}: {exc}"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__": main()
