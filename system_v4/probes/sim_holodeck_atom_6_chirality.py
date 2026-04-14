#!/usr/bin/env python3
"""
Holodeck atom 6 / 7 -- CHIRALITY.

Lego scope: a holodeck scene with oriented structure admits a chirality
bit (L vs R). We realize chirality via Cl(3) pseudoscalar i = e1 e2 e3:
its square is -1, and reflecting one axis flips its sign. Tests:
  - i^2 = -1
  - axis reflection flips i
  - two reflections restore i (Z/2 action)
clifford library is load-bearing.
"""

import json, os

TOOL_MANIFEST = {k: {"tried": False, "used": False, "reason": ""} for k in [
    "pytorch","pyg","z3","cvc5","sympy","clifford","geomstats","e3nn",
    "rustworkx","xgi","toponetx","gudhi"]}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

# --- backfill empty TOOL_MANIFEST reasons (cleanup) ---
def _backfill_reasons(tm):
    for _k,_v in tm.items():
        if not _v.get('reason'):
            if _v.get('used'):
                _v['reason'] = 'used without explicit reason string'
            elif _v.get('tried'):
                _v['reason'] = 'imported but not exercised in this sim'
            else:
                _v['reason'] = 'not used in this sim scope'
    return tm


try:
    from clifford import Cl
    TOOL_MANIFEST["clifford"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["clifford"]["reason"] = "not installed"
try:
    import torch
    TOOL_MANIFEST["pytorch"]["tried"] = True
except ImportError:
    TOOL_MANIFEST["pytorch"]["reason"] = "not installed"
for n in ("pyg","z3","cvc5","sympy","geomstats","e3nn",
          "rustworkx","xgi","toponetx","gudhi"):
    TOOL_MANIFEST[n]["reason"] = "not needed for Cl(3) pseudoscalar"


def setup():
    layout, blades = Cl(3)
    e1, e2, e3 = blades["e1"], blades["e2"], blades["e3"]
    I = e1 * e2 * e3
    return layout, e1, e2, e3, I


def run_positive_tests():
    results = {}
    _, e1, e2, e3, I = setup()
    sq = I * I
    results["i_squared_is_neg1"] = {"val": str(sq), "pass": float(sq[0]) == -1.0}
    # A pseudoscalar anticommutes with a vector reflection:
    # reflect along e1: v -> -e1 v e1; applied to I:
    reflected = -e1 * I * e1
    # e1 I e1 = e1 (e1 e2 e3) e1 = (e2 e3) e1 = -e1 e2 e3 = -I  => -(-I) = I?
    # Actually: under single reflection along e1, pseudoscalar flips sign.
    # Check by reconstructing pseudoscalar of reflected frame:
    e1p, e2p, e3p = -e1, e2, e3
    Ip = e1p * e2p * e3p
    results["single_refl_flips"] = {
        "I_sign": float(I[7]) if len(I.value) > 7 else float((I*I)[0]),
        "Ip_sign_opposite": float((I + Ip)[0]) == 0 and (I - Ip) != 0,
        "pass": Ip == -I,
    }
    return results


def run_negative_tests():
    results = {}
    _, e1, e2, e3, I = setup()
    # Claim "i is scalar" must be false
    scalar_part = float(I[0])
    results["i_not_scalar"] = {"scalar": scalar_part, "pass": scalar_part == 0.0}
    # Claim "i^2 = +1" must be false
    sq = I * I
    results["i_sq_not_plus1"] = {"val": float(sq[0]), "pass": float(sq[0]) != 1.0}
    return results


def run_boundary_tests():
    results = {}
    _, e1, e2, e3, I = setup()
    # Double reflection restores chirality
    e1p, e2p, e3p = -e1, -e2, e3
    Ipp = e1p * e2p * e3p
    results["double_refl_restores"] = {"pass": Ipp == I}
    # Commute check: I commutes with vectors in Cl(3)? (I is central in Cl(3))
    comm = (I*e1 - e1*I)
    zero = (I - I)  # zero multivector reference
    results["I_central"] = {"pass": comm == zero}
    return results


if __name__ == "__main__":
    TOOL_MANIFEST["clifford"]["used"] = True
    TOOL_MANIFEST["clifford"]["reason"] = "Cl(3) pseudoscalar algebra load-bearing for chirality"
    TOOL_INTEGRATION_DEPTH["clifford"] = "load_bearing"

    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    def allpass(d): return all(v.get("pass", False) for v in d.values())
    all_pass = allpass(pos) and allpass(neg) and allpass(bnd)
    results = {
        "name": "holodeck_atom_6_chirality",
        "tool_manifest": _backfill_reasons(TOOL_MANIFEST),
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "canonical", "all_pass": all_pass,
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "holodeck_atom_6_chirality_results.json")
    with open(out_path, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"[atom6 chirality] all_pass={all_pass} -> {out_path}")
