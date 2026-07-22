#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — QuantumClifford stabilizer-state enumeration.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: capability demonstration only — shows QuantumClifford.jl does
group-theoretic stabilizer-tableau work (comm, canonicalize!, phase tracking)
that QuantumOptics/jnp lack, cross-checked against the exact sympy count
formula. No manifold, axis, or bridge claim. Parks by definition.

Checks:
  1. exhaustive 2-qubit stabilizer-state enumeration (Julia leg: every
     commuting, GF(2)-independent signed Pauli pair, canonicalized via
     QuantumClifford.canonicalize!) — unique canonical tableau count vs the
     exact formula 2^n * prod_{k=1..n}(2^k + 1) = 4*3*5 = 60 (sympy integers)
  2. sample of 10 canonical states re-verified inside QuantumClifford:
     generators commute, real phases, full GF(2) rank, canonical fixed point
  3. NEGATIVE CONTROL: same enumeration path at n=1 gives 6 (formula 2*3),
     not 60 — the count genuinely moves with n
  4. NEGATIVE CONTROL: an anticommuting pair (+XX, +ZI) is excluded by the
     same comm predicate — admissibility genuinely fails for it

Exit 0 = probe completed (agreements recorded either way); 1 = infra failure.
"""
import json
import shutil
import subprocess
import sys
import time
from functools import reduce
from pathlib import Path

import sympy

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent


def exact_count(n: int) -> int:
    """Exact stabilizer-state count 2^n * prod_{k=1..n}(2^k + 1), sympy integers."""
    two = sympy.Integer(2)
    return int(two**n * reduce(lambda a, k: a * (two**k + 1),
                               range(1, n + 1), sympy.Integer(1)))


def main():
    t0 = time.perf_counter()
    julia_bin = shutil.which("julia")
    if not julia_bin:
        print("[FATAL] no julia on PATH", file=sys.stderr)
        return 1
    proc = subprocess.run(
        [julia_bin, f"--project={REPO}/system_v5/julia_carrier",
         str(HERE / "quantumclifford_orbit_probe.jl")],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        print(f"[FATAL] julia leg exit {proc.returncode}: {proc.stderr[-500:]}",
              file=sys.stderr)
        return 1
    jl = json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])

    n2_expected = exact_count(2)   # 60
    n1_expected = exact_count(1)   # 6
    n2_count = jl["n2"]["unique_count"]
    n1_count = jl["n1"]["unique_count"]
    sample = jl["n2"]["sample_verified"]
    anti = jl["anticommuting_pair_control"]

    checks = {
        "two_qubit_enumeration": {
            "unique_canonical_tableaux": n2_count,
            "sympy_formula_count": n2_expected,
            "pairs_considered": jl["n2"]["pairs_considered"],
            "rejected_anticommuting": jl["n2"]["rejected_anticommuting"],
            "rejected_dependent_pattern": jl["n2"]["rejected_dependent_pattern"],
            "method": "exhaustive signed-Pauli-pair enumeration + canonicalize!, "
                      "not sampling",
            "pass": n2_count == n2_expected,
        },
        "sample_verification": {
            "n_sampled": len(sample),
            "all_valid": bool(jl["n2"]["sample_all_valid"]),
            "criteria": ["rows_commute", "phases_real", "independent_full_rank",
                         "canonical_fixed_point"],
            "weights_seen": sorted({w for d in sample for w in d["weights"]}),
            "pass": len(sample) == 10 and bool(jl["n2"]["sample_all_valid"]),
        },
        "negative_control_one_qubit": {
            "unique_canonical_tableaux": n1_count,
            "sympy_formula_count": n1_expected,
            "differs_from_60": n1_count != n2_expected,
            "pass": n1_count == n1_expected and n1_count != n2_expected,
        },
        "negative_control_anticommuting_pair": {
            "pair": anti["pair"],
            "comm": anti["comm"],
            "excluded_by_same_predicate": bool(anti["excluded"]),
            "pass": bool(anti["excluded"]),
        },
    }
    all_pass = all(c["pass"] for c in checks.values())

    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "capability demonstration only — QuantumClifford "
                         "stabilizer-tableau enumeration exercise; no manifold/"
                         "axis/bridge claim; parks by definition",
        "engines_used": {
            "julia_quantumclifford": jl["quantumclifford_ops"],
            "sympy": ["Integer-exact count formula 2^n * prod(2^k+1)"],
        },
        "checks": checks,
        "all_checks_pass": all_pass,
        "julia_seconds": jl["julia_seconds"],
        "seconds": round(time.perf_counter() - t0, 3),
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    receipt_path = out / "quantumclifford_orbit_probe.json"
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] quantumclifford probe COMPLETED — checks "
          f"{'ALL HOLD' if all_pass else 'FAIL (recorded)'}; receipt: {receipt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
