#!/usr/bin/env python3
from __future__ import annotations

import datetime as _dt
import json
import sys
from pathlib import Path
from typing import Any

import torch
from torch.func import jacrev

ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
OBJECT_ID = "foundation_r2_admissibility_mc_pytorch_leg"
SOURCE_PATH = ROOT / "system_v5/ops/formal_scouts/foundation_foundation_r2_admissibility_mc_pytorch_leg.py"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r2_admissibility_mc_pytorch_leg_results.json"

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
reads_peer_result = False
DTYPE = torch.float64


def as_float(x: torch.Tensor | float) -> float:
    return float(x.detach().cpu().item()) if isinstance(x, torch.Tensor) else float(x)


def rho_imag_coherence(t: torch.Tensor) -> torch.Tensor:
    zero = torch.zeros((), dtype=DTYPE)
    half = torch.tensor(0.5, dtype=DTYPE)
    return torch.stack(
        [
            torch.stack([torch.complex(half, zero), torch.complex(zero, t)]),
            torch.stack([torch.complex(zero, -t), torch.complex(half, zero)]),
        ]
    )


def probe_probs(rho: torch.Tensor) -> torch.Tensor:
    p0 = rho[0, 0].real
    p1 = rho[1, 1].real
    pplus = ((rho[0, 0] + rho[1, 1] + rho[0, 1] + rho[1, 0]) / 2.0).real
    return torch.stack([p0, p1, pplus])


def admissibility_margin(t: torch.Tensor) -> torch.Tensor:
    rho = rho_imag_coherence(t)
    eig_min = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real.min()
    probs = probe_probs(rho)
    born_lower = probs.min()
    born_upper = (1.0 - probs).min()
    trace_margin = 1.0 - torch.abs(torch.trace(rho).real - 1.0)
    return torch.minimum(torch.minimum(eig_min, born_lower), torch.minimum(born_upper, trace_margin))


def margin_row(t_value: float) -> dict[str, Any]:
    t = torch.tensor(t_value, dtype=DTYPE)
    rho = rho_imag_coherence(t)
    vals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
    probs = probe_probs(rho)
    return {
        "t": t_value,
        "margin": as_float(admissibility_margin(t)),
        "jacrev_dmargin_dt": as_float(jacrev(admissibility_margin)(t)),
        "eigenvalues": [float(v.detach().cpu().item()) for v in vals],
        "probe_probabilities": [float(v.detach().cpu().item()) for v in probs],
    }


def build_result() -> dict[str, Any]:
    rows = [margin_row(0.49), margin_row(0.5), margin_row(0.51)]
    gradient_ok = abs(rows[0]["jacrev_dmargin_dt"] + 1.0) <= 1.0e-10
    crossing_ok = rows[0]["margin"] > 0.0 and abs(rows[1]["margin"]) <= 1.0e-10 and rows[2]["margin"] < 0.0
    probs_constant = all(max(abs(p - 0.5) for p in row["probe_probabilities"]) <= 1.0e-10 for row in rows)
    all_pass = gradient_ok and crossing_ok and probs_constant and not reads_peer_result
    return {
        "object_id": OBJECT_ID,
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "reads_peer_result": reads_peer_result,
        "ran": True,
        "engine": "pytorch",
        "backend": "pytorch_torch_func_boundary_normal",
        "source_path": str(SOURCE_PATH),
        "result_path": str(RESULT_PATH),
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "python_executable": sys.executable,
        "dtype": "torch.float64",
        "M_probe_family": ["P_z0=|0><0|", "P_z1=|1><1|", "P_xplus=|+><+|"],
        "boundary_family": "rho(t)=[[1/2, i*t],[-i*t, 1/2]]; finite M probes stay at 1/2 while PSD margin crosses at |t|=1/2",
        "rows": rows,
        "genuine_independent_check": True,
        "independence_note": "PyTorch does not re-prove SMT exclusion; it differentiates the PSD/Born admissibility margin and returns the local boundary normal dmargin/dt via torch.func.jacrev.",
        "all_pass": all_pass,
        "TOOL_MANIFEST": {
            "torch": {"tried": True, "used": True, "reason": "load-bearing complex128 Hermitian family, eigvalsh PSD margin, and Born margin computation"},
            "torch.func": {"tried": True, "used": True, "reason": "load-bearing jacrev boundary normal for the admissibility margin"},
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
        f"margin_0p49={result['rows'][0]['margin']} "
        f"margin_0p5={result['rows'][1]['margin']} "
        f"margin_0p51={result['rows'][2]['margin']} "
        f"jacrev={result['rows'][0]['jacrev_dmargin_dt']} "
        f"reads_peer_result={result['reads_peer_result']}"
    )
    return 0 if result["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
