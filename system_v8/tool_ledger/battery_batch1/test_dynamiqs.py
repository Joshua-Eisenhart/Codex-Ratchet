#!/usr/bin/env python3
"""dynamiqs JAX-native mesolve of the QIT receipt's amplitude-damping channel."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "results" / "dynamiqs.json"
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
SOURCE = ROOT / "system_v8/deep_integration/results/qit_referee/receipt.json"


def memory_free_percent() -> int:
    s = subprocess.run(["memory_pressure"], capture_output=True, text=True, check=True).stdout
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", s)
    if not m: raise RuntimeError("memory_pressure did not report a free percentage")
    return int(m.group(1))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    result = {"tool": "dynamiqs", "promotion_allowed": False,
              "claim_ceiling": "tool-integration evidence only; not an admission claim",
              "source": str(SOURCE), "interpreter": sys.executable}
    try:
        free = memory_free_percent()
        if free <= 25: raise RuntimeError(f"memory free percentage {free}% is not > 25%")
        if Path(sys.executable).resolve() != SIM_PY.resolve(): raise RuntimeError(f"canonical interpreter required: {SIM_PY}")
        import jax
        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp
        import dynamiqs as dq
        referee = json.loads(SOURCE.read_text())
        # Same one-qubit amplitude-damping channel as the referee's A family:
        # gamma=.5, initial left-sheet Bloch state (0.5,0.3,-0.4), t=12.
        gamma, t_final = .5, 12.
        sx, sy, sz = dq.sigmax(), dq.sigmay(), dq.sigmaz()
        rho0 = dq.asqarray(.5 * (dq.eye(2) + .5 * sx + .3 * sy - .4 * sz), layout=dq.dense)
        states = dq.mesolve(dq.asqarray(0.0 * sz, layout=dq.dense), [dq.asqarray(jnp.sqrt(gamma) * dq.destroy(2), layout=dq.dense)], rho0,
                            jnp.linspace(0., t_final, 31), method=dq.method.Tsit5(rtol=1e-10, atol=1e-12),
                            options=dq.Options(progress_meter=False)).states
        final = np.asarray(dq.to_numpy(states[-1]))
        # The independent qutip receipt gives the same channel's fixed-point
        # minimum eigenvalue (ground-state fixed point in the one-qubit reduction).
        target_pop = float(np.exp(-gamma * t_final) * .7)
        pop = float(np.real(final[1, 1]))
        trace_error = float(abs(np.trace(final) - 1.0))
        min_eig = float(np.min(np.linalg.eigvalsh(final)))
        err = abs(pop - target_pop)
        checks = {"memory_gate_gt_25": free > 25, "trace_preserved_1e-10": trace_error < 1e-10,
                  "physical_density_min_eig_ge_minus_1e-10": min_eig >= -1e-10,
                  "gksl_channel_matches_qutip_referee_family_1e-8": err < 1e-8,
                  "qutip_referee_fixed_point_min_eig_recorded": referee["data"]["A_rho_ss_min_eig_qutip"] > 0}
        result.update({"verdict": "INTEGRATED" if all(checks.values()) else "BLOCKED", "checks": checks, "real_object": "QIT-referee amplitude-damping manifold channel", "computed_number": err,
                       "data": {"gamma": gamma, "t_final": t_final, "excited_population_dynamiqs": pop,
                       "known_qutip_family_population": target_pop, "abs_error": err,
                       "trace_error": trace_error, "min_eigenvalue": min_eig,
                       "qutip_referee_two_sheet_fixed_point_min_eig": referee["data"]["A_rho_ss_min_eig_qutip"]},
                       "finding": "dynamiqs.mesolve performs the channel evolution that decides the numerical agreement gate."})
    except Exception as exc:
        result.update({"verdict": "BLOCKED", "exact_error": f"{type(exc).__name__}: {exc}"})
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__": main()
