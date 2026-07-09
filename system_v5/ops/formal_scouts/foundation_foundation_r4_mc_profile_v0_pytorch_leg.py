#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import math
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_r4_mc_profile_v0_pytorch_leg"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r4_mc_profile_v0_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r4_mc_profile_v0_pytorch_leg_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
# REPAIR NOTE (R4 reopen): this probe family (Bloch-diagonal qubit boundary)
# has zero derivation link to R3's admitted octonion/Cl(6) carrier. No
# non-fabricated R3 derivation exists, so this object is reclassified to R2
# rather than asserting a fake R3 dependency.
rung_reclassified_from_r4_to_r2 = True
rung_reclassification_reason = (
    "Probe family (generic qubit Bloch boundary) has zero derivation link to "
    "R3's admitted octonion/Cl(6) carrier; no non-fabricated R3 derivation "
    "exists, so this object is demoted to R2 (admissible-operations layer on "
    "M(C)) rather than asserting a fake R3 dependency."
)
DTYPE = torch.float64


def as_float(value: torch.Tensor | float) -> float:
    return float(value.detach().cpu().item()) if isinstance(value, torch.Tensor) else float(value)


def rho_from_equal_bloch(t: torch.Tensor) -> torch.Tensor:
    one = torch.ones((), dtype=DTYPE)
    two = torch.tensor(2.0, dtype=DTYPE)
    a = (one + t) / two
    d = (one - t) / two
    re = t / two
    im = -t / two
    zero = torch.zeros((), dtype=DTYPE)
    return torch.stack(
        [
            torch.stack([torch.complex(a, zero), torch.complex(re, im)]),
            torch.stack([torch.complex(re, -im), torch.complex(d, zero)]),
        ]
    )


def probe_probs(rho: torch.Tensor) -> torch.Tensor:
    p_z0 = rho[0, 0].real
    p_xplus = ((rho[0, 0] + rho[1, 1] + rho[0, 1] + rho[1, 0]) / 2.0).real
    p_yplus = ((rho[0, 0] + rho[1, 1]) / 2.0 + (rho[1, 0].imag - rho[0, 1].imag) / 2.0).real
    return torch.stack([p_z0, p_xplus, p_yplus])


def psd_det_margin(t: torch.Tensor) -> torch.Tensor:
    rho = rho_from_equal_bloch(t)
    a = rho[0, 0].real
    d = rho[1, 1].real
    re = rho[0, 1].real
    im = rho[0, 1].imag
    return a * d - re * re - im * im


def probe_upper_margin(t: torch.Tensor) -> torch.Tensor:
    rho = rho_from_equal_bloch(t)
    return (torch.tensor(7.0 / 8.0, dtype=DTYPE) - probe_probs(rho)).min()


def row(t_value: float) -> dict[str, Any]:
    t = torch.tensor(t_value, dtype=DTYPE)
    rho = rho_from_equal_bloch(t)
    evals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    probs = probe_probs(rho)
    return {
        "t": t_value,
        "psd_det_margin": as_float(psd_det_margin(t)),
        "d_psd_det_margin_dt": as_float(jacrev(psd_det_margin)(t)),
        "probe_upper_margin": as_float(probe_upper_margin(t)),
        "eigenvalues": [as_float(v) for v in evals],
        "probe_probabilities": [as_float(v) for v in probs],
    }


def build_result() -> dict[str, Any]:
    boundary = 1.0 / math.sqrt(3.0)
    rows = [row(boundary - 0.01), row(boundary), row(boundary + 0.01), row(0.75)]
    derivative_expected = -math.sqrt(3.0) / 2.0
    boundary_row = rows[1]
    crossing_ok = rows[0]["psd_det_margin"] > 0.0 and abs(boundary_row["psd_det_margin"]) <= 1.0e-12 and rows[2]["psd_det_margin"] < 0.0
    gradient_ok = abs(boundary_row["d_psd_det_margin_dt"] - derivative_expected) <= 1.0e-12
    probe_bounds_still_open_at_boundary = boundary_row["probe_upper_margin"] > 0.0
    control_non_psd_at_0p75 = rows[3]["psd_det_margin"] < 0.0 and abs(rows[3]["probe_upper_margin"]) <= 1.0e-12
    all_pass = crossing_ok and gradient_ok and probe_bounds_still_open_at_boundary and control_non_psd_at_0p75 and reads_peer_result is False
    return {
        "object_id": OBJECT_ID,
        "engine": "pytorch",
        "backend": "pytorch_torch_func_mc_boundary_sensitivity",
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "rung_reclassified_from_r4_to_r2": rung_reclassified_from_r4_to_r2,
        "rung_reclassification_reason": rung_reclassification_reason,
        "ran": True,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "python_executable": sys.executable,
        "dtype": "torch.float64",
        "M_probe_family": ["P_z0=|0><0|", "P_xplus=|+><+|", "P_yplus=|i+><i+|"],
        "differentiable_family": "rho(t) has Bloch vector (t,t,t); probes stay under 7/8 at the PSD boundary t=1/sqrt(3)",
        "boundary_parameter": boundary,
        "rows": rows,
        "genuine_independent_check": True,
        "independence_note": "PyTorch does not mirror the quotient count or SMT proof; torch.func.jacrev computes the local PSD determinant sensitivity for the M(C) boundary family.",
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "load-bearing float64 complex Hermitian family and PSD/probe margin evaluation"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev derivative of the PSD determinant margin at the M(C) boundary"},
        },
        "TOOL_INTEGRATION_DEPTH": {"torch": "load_bearing", "torch.func": "load_bearing"},
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "SCOUT_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"boundary_t={result['boundary_parameter']} "
        f"boundary_margin={result['rows'][1]['psd_det_margin']} "
        f"jacrev={result['rows'][1]['d_psd_det_margin_dt']} "
        f"reads_peer_result={result['reads_peer_result']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
