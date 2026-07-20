#!/usr/bin/env python3
"""Kingdon float64 recomputation of the Julia CliffordAlgebras gamma5 receipt."""
import json, re, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "system_v8/tool_ledger/battery_batch1/results/kingdon.json"
JULIA = ROOT / "system_v8/engine_estate/results/julia/receipt.json"

def gate():
    text = subprocess.run(["memory_pressure"], capture_output=True, text=True, check=True).stdout
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", text)
    if not m or int(m.group(1)) <= 25:
        raise RuntimeError("memory gate failed: " + (m.group(1) if m else "unparsed"))
    return int(m.group(1))

def main():
    result = {"tool": "kingdon", "promotion_allowed": False, "real_object": str(JULIA),
              "generated_at": datetime.now(timezone.utc).isoformat(), "verdict": "BLOCKED"}
    try:
        free = gate()
        source = json.loads(JULIA.read_text())
        assert source["sections"]["cliffordalgebras_gamma5_L10"]["status"] == "PASS"
        from kingdon import Algebra
        alg = Algebra(p=4)
        e = [alg.blades[f"e{i}"] for i in range(1, 5)]
        gamma5 = e[0] * e[1] * e[2] * e[3]
        scalar_one = alg.blades.e
        def maxcoeff(mv):
            return max((abs(float(x)) for x in mv.asfullmv().values()), default=0.0)
        anti = max(maxcoeff(gamma5 * v + v * gamma5) for v in e)
        bivectors = [e[i] * e[j] for i in range(4) for j in range(i + 1, 4)]
        commute = max(maxcoeff(gamma5 * b - b * gamma5) for b in bivectors)
        square = maxcoeff(gamma5 * gamma5 - scalar_one)
        result.update({"verdict": "INTEGRATED", "memory_free_percent": free,
                       "computed_number": {"gamma5_square_residual_float64": square,
                                           "max_generator_anticommutator_residual_float64": anti,
                                           "max_bivector_commutator_residual_float64": commute},
                       "agreement_gate": bool(max(square, anti, commute) < 1e-12),
                       "reason": "Kingdon geometric products independently recompute all three true checks of the real CliffordAlgebras.jl gamma5 L10 receipt."})
    except Exception as exc:
        result["exact_error"] = f"{type(exc).__name__}: {exc}"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True))

if __name__ == "__main__": main()
