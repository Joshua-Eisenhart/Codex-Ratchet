#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — Attractors.jl basins of attraction vs sympy exact roots.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: capability demonstration only — shows DynamicalSystems.jl +
Attractors.jl map basins of attraction (Newton-fractal for z^3 - 1 as a 2D
DeterministicIteratedMap, AttractorsViaRecurrences over a 101x101 IC grid on
[-1.5,1.5]^2), a classical-dynamics capability absent from the estate.
Cross-checked against the exact roots of z^3 - 1 from sympy. No manifold,
axis, or bridge claim. Parks by definition.

Checks:
  1. AttractorsViaRecurrences discovers exactly 3 attractors for the z^3 - 1
     Newton map (no root list supplied to the mapper).
  2. Each discovered attractor sits within 1e-8 of one exact sympy root of
     z^3 - 1, and all 3 roots are covered (unique matching).
  3. Each basin fraction lies in (0.2, 0.5) and the fractions sum to ~1
     (> 0.99 labeled).
  4. NEGATIVE CONTROL: z^1 - 1 through the SAME machinery — the 3-attractor
     property genuinely fails: exactly 1 attractor, at the single sympy root
     z = 1, with basin fraction ~1.

Exit 0 = probe completed (results recorded either way); 1 = infra failure.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

import sympy

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
MATCH_TOL = 1e-8


def exact_roots(power):
    """Exact roots of z^power - 1 from sympy, as python complex."""
    z = sympy.symbols("z")
    rs = sympy.roots(z**power - 1, z)
    return [complex(r.evalf(30)) for r in rs.keys() for _ in range(rs[r])]


def match_attractors(att_points, roots):
    """Nearest-root match for each attractor; distances + covered-root indices."""
    matches = {}
    covered = set()
    for label, (re, im) in sorted(att_points.items()):
        a = complex(re, im)
        dists = [abs(a - r) for r in roots]
        i = min(range(len(roots)), key=lambda k: dists[k])
        covered.add(i)
        matches[label] = {"attractor": [re, im],
                          "nearest_root": [roots[i].real, roots[i].imag],
                          "distance": dists[i]}
    max_dist = max((m["distance"] for m in matches.values()), default=float("inf"))
    return matches, max_dist, covered


def main():
    t0 = time.perf_counter()
    julia_bin = shutil.which("julia")
    if not julia_bin:
        print("[FATAL] no julia on PATH", file=sys.stderr)
        return 1

    # 1. Julia leg: DynamicalSystems + Attractors basin mapping (both cases).
    proc = subprocess.run(
        [julia_bin, f"--project={REPO}/system_v5/julia_carrier",
         str(HERE / "attractors_basins_probe.jl")],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        print(f"[FATAL] julia leg exit {proc.returncode}: {proc.stderr[-500:]}", file=sys.stderr)
        return 1
    jl = json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])
    t_julia = time.perf_counter() - t0

    # 2. sympy exact cross-check: roots of z^3 - 1 and z^1 - 1.
    roots3 = exact_roots(3)
    roots1 = exact_roots(1)

    p3 = jl["cases"]["p3"]
    matches3, max_d3, covered3 = match_attractors(p3["attractor_points"], roots3)
    fracs3 = list(p3["basin_fractions"].values())
    p1 = jl["cases"]["p1"]
    matches1, max_d1, covered1 = match_attractors(p1["attractor_points"], roots1)
    fracs1 = list(p1["basin_fractions"].values())

    checks = {
        "p3_attractor_count": {
            "found": p3["n_attractors"], "expected": 3,
            "pass": p3["n_attractors"] == 3,
        },
        "p3_attractors_match_sympy_roots": {
            "matches": matches3, "max_distance": max_d3,
            "roots_covered": len(covered3), "tolerance": MATCH_TOL,
            "pass": max_d3 < MATCH_TOL and len(covered3) == 3,
        },
        "p3_basin_fractions": {
            "fractions": p3["basin_fractions"], "sum": sum(fracs3),
            "unlabeled_fraction": p3["unlabeled_fraction"],
            "each_in_open_02_05": all(0.2 < f < 0.5 for f in fracs3),
            "pass": (len(fracs3) == 3 and all(0.2 < f < 0.5 for f in fracs3)
                     and sum(fracs3) > 0.99),
        },
        "p1_negative_control": {
            "found": p1["n_attractors"], "expected": 1,
            "matches": matches1, "max_distance": max_d1,
            "basin_fraction_sum": sum(fracs1),
            "pass": (p1["n_attractors"] == 1 and max_d1 < MATCH_TOL
                     and len(covered1) == 1 and sum(fracs1) > 0.99),
        },
    }
    all_pass = all(c["pass"] for c in checks.values())

    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "capability demonstration only — Attractors.jl/DynamicalSystems.jl "
                         "basin mapping cross-checked by sympy exact roots; no manifold/axis/"
                         "bridge claim; parks by definition",
        "engines_used": {
            "julia": [jl["engine"], "separate process, --project=system_v5/julia_carrier"],
            "sympy": ["roots (exact algebraic roots of z^p - 1)"],
        },
        "load_bearing": "AttractorsViaRecurrences discovers attractors and labels the "
                        "101x101 IC grid — basin-of-attraction capability nothing else "
                        "in the estate provides",
        "negative_control": "z^1 - 1 (single root) through the same machinery: "
                            "3-attractor property genuinely fails, exactly 1 found",
        "grid": {"ic_grid": "101x101 on [-1.5,1.5]^2", "recurrence_grid": "301x301"},
        "checks": checks,
        "all_checks_pass": all_pass,
        "seconds_julia_leg": round(t_julia, 3),
        "seconds": round(time.perf_counter() - t0, 3),
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    with open(out / "attractors_basins_probe.json", "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] attractors probe COMPLETED — checks {'ALL HOLD' if all_pass else 'FAIL (recorded)'}; "
          f"receipt: {out / 'attractors_basins_probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
