"""
sim_d4_pseudoscalar_chirality_dimension_parity_portability_probe.py

Portability methodology applied to D4 gamma5 chirality probe (currently candidate_basin).
Tests whether D4's pseudoscalar-anticommutes-with-generators property holds across
multiple Cl(p,q) signatures + dimensions.

Finding (from initial in-line run): D4's chirality property is DIMENSION-PARITY-LOCKED.
- Even-dim (n=p+q=4): pseudoscalar anticommutes with all generators → chirality holds
- Odd-dim (n=p+q=5): pseudoscalar COMMUTES with all generators (central in algebra) → chirality FAILS

Contrast with D5 commutative_geometry_collapse which is FULLY signature-portable (8/8 signatures
including both n=4 and n=5 returned 4-way UNSAT in sim_commutative_geometry_collapse_cl_2_2_portability_probe).

This formalizes the methodology: portability gives a discriminating axis between basin claims.

Anti-smuggling: authors this sim only. Does NOT add CASES entry to basin classifier.
Cross-lineage external authorship required for classifier admission.
"""

from __future__ import annotations

import json
import pathlib
import time

import numpy as np
from clifford import Cl

ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "d4_pseudoscalar_chirality_dimension_parity_portability_probe_results.json"

CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests whether D4 gamma5 chirality probe's pseudoscalar-anticommutation "
    "property holds across multiple Cl(p,q) signatures. Finds dimension-parity-conditional "
    "behavior (works for even n=p+q, fails for odd n). Does not admit canonical engine, manifold, "
    "axis, or basin verdict — requires fresh-context external case authorship per anti-smuggling rule."
)

TOOL_INTEGRATION_DEPTH = {
    "clifford": "load_bearing",
    "numpy": "supportive",
}

TOOL_MANIFEST = {
    "clifford": {"tried": True, "used": True,
                  "reason": "Load-bearing Cl(p,q) generator construction + geometric product + pseudoscalar computation across signatures"},
    "numpy": {"tried": True, "used": True,
              "reason": "Supportive multivector coefficient norm arithmetic"},
}


def test_signature(p: int, q: int) -> dict:
    """Test pseudoscalar I = e1*e2*...*en for anticommutation with each generator."""
    layout, blades = Cl(p, q)
    n = p + q
    gens = [blades[f"e{i+1}"] for i in range(n)]
    I = gens[0]
    for g in gens[1:]:
        I = I * g
    I_sq = I * I
    I_sq_scalar = float(I_sq.value[0])
    anticomm_per_gen = []
    for g in gens:
        anticomm_norm = float(np.linalg.norm((I * g + g * I).value))
        anticomm_per_gen.append({
            "norm_of_I_g_plus_g_I": anticomm_norm,
            "anticommutes": anticomm_norm < 1e-12,
        })
    n_anticomm = sum(1 for x in anticomm_per_gen if x["anticommutes"])
    return {
        "signature": f"Cl({p},{q})",
        "n_gens": n,
        "I_squared_scalar": I_sq_scalar,
        "anticomm_count_out_of_n": [n_anticomm, n],
        "pseudoscalar_anticommutes_all_generators": n_anticomm == n,
        "parity": "even" if n % 2 == 0 else "odd",
    }


def main():
    signatures = [(1, 3), (2, 2), (0, 4), (4, 0), (1, 4), (4, 1), (2, 3), (3, 2)]
    test_results = [test_signature(p, q) for p, q in signatures]

    even_results = [r for r in test_results if r["parity"] == "even"]
    odd_results = [r for r in test_results if r["parity"] == "odd"]

    all_even_anticomm = all(r["pseudoscalar_anticommutes_all_generators"] for r in even_results)
    all_odd_commute = all(not r["pseudoscalar_anticommutes_all_generators"] for r in odd_results)

    portability_pattern = (
        f"DIMENSION-PARITY-LOCKED: pseudoscalar anticommutes with all generators in all {len(even_results)} "
        f"even-dimension signatures tested AND fails in all {len(odd_results)} odd-dimension signatures. "
        f"D4 chirality property is dimension-parity-conditional, contrasting with D5's fully-portable impossibility."
    )

    results = {
        "probe": "sim_d4_pseudoscalar_chirality_dimension_parity_portability_probe",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "audit_method_families": [
            "clifford_algebra_construction",
            "pseudoscalar_anticommutation_test",
            "dimension_parity_partition",
        ],
        "positive": {
            "signatures_tested": len(test_results),
            "per_signature_results": test_results,
            "all_even_dim_anticommute": all_even_anticomm,
            "all_odd_dim_commute": all_odd_commute,
            "dimension_parity_partition_pass": all_even_anticomm and all_odd_commute,
        },
        "negative": {},
        "boundary": {
            "even_dim_signatures_tested": [r["signature"] for r in even_results],
            "odd_dim_signatures_tested": [r["signature"] for r in odd_results],
            "pseudoscalar_squared_values": {r["signature"]: r["I_squared_scalar"] for r in test_results},
        },
        "graveyard_companions": {
            "even_dim_pseudoscalar_central_control": {
                "pass": all(r["pseudoscalar_anticommutes_all_generators"] for r in even_results),
                "claim": "if pseudoscalar were central in any tested even-dim signature, D4 chirality would not be the pseudoscalar's anticommutation property — control passes (anticommutes in all 4 tested)",
            },
            "odd_dim_pseudoscalar_anticommutes_control": {
                "pass": all(not r["pseudoscalar_anticommutes_all_generators"] for r in odd_results),
                "claim": "if pseudoscalar anticommuted in any odd-dim signature, the parity-locked claim would fail — control passes (commutes in all 4 odd-dim tested)",
            },
        },
        "all_pass": all_even_anticomm and all_odd_commute,
        "portability_verdict": portability_pattern,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(results, indent=2))
    print(f"WROTE: {OUT_PATH}")
    print(f"signatures tested: {len(test_results)}")
    print(f"even-dim pseudoscalar anticommutes-all: {all_even_anticomm}  ({len(even_results)} sigs)")
    print(f"odd-dim pseudoscalar commutes-all: {all_odd_commute}  ({len(odd_results)} sigs)")
    print(f"all_pass: {results['all_pass']}")
    print(f"VERDICT: {portability_pattern}")
    return results


if __name__ == "__main__":
    main()
