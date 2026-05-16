#!/usr/bin/env python3
"""Classical baseline sim: partial_trace_operator lego.

Lane B classical baseline (numpy-only). NOT canonical.
Captures: classical 'partial trace' as marginalization of a joint pmf:
  p_A(a) = sum_b p_AB(a,b).
Innately missing: quantum partial trace on density matrix (off-diagonal
coherences are averaged in; reduced state can be mixed even when joint is
pure — the entanglement signature). Classical marginal cannot represent
the purity-entropy inversion.
"""
import json, os
import numpy as np

NAME = "partial_trace_classical"
classification = "classical_baseline"
CLAIM_CEILING = "classical baseline for probability marginalization only; no density-matrix partial-trace, coherence, or nonclassical claim"
divergence_log = (
    "Cannot express pure-joint -> mixed-marginal (entanglement signature); "
    "no off-diagonal coherence tracing, only diagonal marginalization; "
    "blind to subsystem purity inversion used in entanglement entropy."
)

TOOL_MANIFEST = {
    "numpy": {"tried": True, "used": True, "reason": "sum over axis"},
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline"},
}
TOOL_INTEGRATION_DEPTH = {"numpy": "supportive"}

def marginal_A(pab): return np.asarray(pab).sum(axis=1)
def marginal_B(pab): return np.asarray(pab).sum(axis=0)

def run_positive_tests():
    pab = np.array([[0.1, 0.2],[0.3, 0.4]])
    return {
        "marginal_A_sum_1": abs(marginal_A(pab).sum() - 1.0) < 1e-12,
        "marginal_B_sum_1": abs(marginal_B(pab).sum() - 1.0) < 1e-12,
        "product_factorizes": np.allclose(np.outer(marginal_A(np.outer([0.5,0.5],[0.3,0.7])),
                                                     marginal_B(np.outer([0.5,0.5],[0.3,0.7]))),
                                           np.outer([0.5,0.5],[0.3,0.7]), atol=1e-10),
    }

def run_negative_tests():
    # Pure joint in classical sense (delta) has pure marginals (no entanglement signature)
    delta = np.zeros((2,2)); delta[0,0] = 1.0
    mA = marginal_A(delta)
    return {
        "classical_pure_joint_yields_pure_marginal": abs(np.max(mA) - 1.0) < 1e-12,
    }

def run_boundary_tests():
    # linearity
    p1 = np.array([[0.3,0.2],[0.1,0.4]]); p2 = np.array([[0.1,0.4],[0.4,0.1]])
    lam = 0.3
    mix = lam*p1 + (1-lam)*p2
    return {
        "linearity": np.allclose(marginal_A(mix), lam*marginal_A(p1) + (1-lam)*marginal_A(p2), atol=1e-12),
    }

if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    all_pass = all(pos.values()) and all(neg.values()) and all(bnd.values())
    results = {
        "schema": "SIM_RESULT_v1",
        "name": NAME,
        "classification": "classical_baseline",
        "promotion_allowed": False,
        "claim_ceiling": CLAIM_CEILING,
        "next_lego_target": "density_matrix_partial_trace_marginal_fixture",
        "promotion_condition": "not promotable; classical probability marginalization baseline only",
        "blocked_until": "paired with density-matrix partial-trace receipts",
        "demotion_condition": "already baseline; demote any use as density-matrix partial trace proof",
        "out_of_scope": [
            "no density-matrix partial trace",
            "no coherence readout",
            "no nonclassical admission",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "all_pass": all_pass,
        "summary": {"all_pass": all_pass},
        "divergence_log": divergence_log,
        "survivor_classes": {
            "survivor_equivalence_classes": [key for key, value in pos.items() if value],
            "survivor_count": sum(1 for value in pos.values() if value),
            "killed_neighbors": [key for key, value in {**neg, **bnd}.items() if value],
            "killed_neighbor_count": sum(1 for value in {**neg, **bnd}.values() if value),
        },
        "rosetta_to_sim_contract": {
            "operation_sequence": [
                "construct finite joint probability table",
                "sum over second coordinate",
                "sum over first coordinate",
                "check product factorization control",
                "check linearity boundary",
            ],
            "carrier_topology": "finite classical joint probability table",
            "observable": ["row marginal", "column marginal", "linearity gap"],
            "pass_fail_predicate": "classical marginals normalize and linearity holds while divergence log marks missing density-matrix behavior",
            "graveyard_companions": ["classical pure-joint pure-marginal control"],
            "baseline_variants": ["two-by-two joint probability table"],
            "alternative_formulations": ["density-matrix partial trace", "tensor index summation"],
            "exact_tool_function_needs": {"numpy": "axis summation and allclose checks"},
            "lego_coupling_target": "classical_probability_marginalization_baseline",
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    out = os.path.join(out_dir, "sim_partial_trace_classical_results.json")
    legacy_out = os.path.join(out_dir, "partial_trace_classical_results.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f: json.dump(results, f, indent=2, default=str)
    with open(legacy_out, "w") as f: json.dump(results, f, indent=2, default=str)
    print(f"all_pass={all_pass} -> {out}")
