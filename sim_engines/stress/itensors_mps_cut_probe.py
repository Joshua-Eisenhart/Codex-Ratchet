#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — ITensors/ITensorMPS entanglement entropy across an MPS cut.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: capability demonstration only — shows ITensors/ITensorMPS does
real tensor-network work (MPS orthogonalization + bond SVD entropy at a cut,
cost ~ chi^3) that dense QuantumOptics matrices do not scale to. No manifold,
axis, or bridge claim. Parks by definition.

Julia leg (itensors_mps_cut_probe.jl, separate process):
  1. 8-site GHZ as MPS: orthogonalize at the middle cut (bond 4|5), SVD the
     bond, S = -sum p log2 p — expected exactly 1 bit; GHZ bond dim must be 2.
  2. NEGATIVE CONTROL through the SAME MPS path: random product state
     — expected 0 bits (entanglement genuinely absent; the property flips).
  3. INDEPENDENT CROSS-CHECK: 4-site GHZ dense via QuantumOptics entropy_vn
     of the half-chain reduced density matrix — expected 1 bit (<1e-9).
Closed-form control: any bipartite cut of GHZ_N carries exactly 1 bit.

Exit 0 = probe completed (agreements recorded either way); 1 = infra failure.
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
TOL = 1e-9
CLOSED_FORM_GHZ_CUT_BITS = 1.0  # Schmidt spectrum of GHZ across any cut: {1/2, 1/2}


def main():
    t0 = time.perf_counter()
    julia_bin = shutil.which("julia")
    if not julia_bin:
        print("[FATAL] no julia on PATH", file=sys.stderr)
        return 1
    proc = subprocess.run(
        [julia_bin, f"--project={REPO}/system_v5/julia_carrier",
         str(HERE / "itensors_mps_cut_probe.jl")],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        print(f"[FATAL] julia leg exit {proc.returncode}: {proc.stderr[-500:]}", file=sys.stderr)
        return 1
    jl = json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])

    ghz_div = abs(jl["ghz8_mps_cut_bits"] - CLOSED_FORM_GHZ_CUT_BITS)
    qo_div = abs(jl["qo_dense_ghz4_half_bits"] - CLOSED_FORM_GHZ_CUT_BITS)
    checks = {
        "ghz8_mps_cut_is_1_bit": {
            "value_bits": jl["ghz8_mps_cut_bits"], "expected": 1.0,
            "div_from_closed_form": ghz_div, "pass": ghz_div < TOL,
        },
        "ghz8_mps_bond_dim_is_2": {
            "value": jl["ghz8_bond_dim"], "expected": 2,
            "pass": jl["ghz8_bond_dim"] == 2,
        },
        "negative_control_product_state_0_bits_same_path": {
            "value_bits": jl["product_mps_cut_bits"], "expected": 0.0,
            "product_bond_dim": jl["product_bond_dim"],
            "pass": abs(jl["product_mps_cut_bits"]) < TOL,
        },
        "quantumoptics_dense_ghz4_cross_check_1_bit": {
            "value_bits": jl["qo_dense_ghz4_half_bits"], "expected": 1.0,
            "div_from_closed_form": qo_div, "pass": qo_div < TOL,
        },
    }
    all_pass = all(c["pass"] for c in checks.values())
    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "capability demonstration only — ITensors/ITensorMPS bond-SVD "
                         "entropy at an MPS cut, cross-checked by QuantumOptics dense + "
                         "closed form; no manifold/axis/bridge claim; parks by definition",
        "engines_used": {
            "julia_itensors": ["siteinds S=1/2", "MPS from dense amplitudes",
                               "orthogonalize", "bond svd", "maxlinkdim"],
            "julia_quantumoptics": ["tensor", "dm", "ptrace", "entropy_vn (dense, dim 16)"],
        },
        "load_bearing": "ITensors/ITensorMPS — the cut entropy is read off the bond SVD "
                        "of the orthogonalized MPS, a tensor-network operation dense "
                        "matrices do not provide",
        "checks": checks,
        "all_checks_pass": all_pass,
        "seconds": round(time.perf_counter() - t0, 3),
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    with open(out / "itensors_mps_cut_probe.json", "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt, indent=1, sort_keys=True))
    print(f"[*] itensors_mps_cut probe COMPLETED — checks "
          f"{'ALL HOLD' if all_pass else 'FAIL (recorded)'}; "
          f"receipt: {out / 'itensors_mps_cut_probe.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
