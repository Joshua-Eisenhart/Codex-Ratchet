#!/usr/bin/env python3
"""sim_holodeck_reality_reconstruction_probe.

Thesis: reality is probe-relative. Given multiple observer projections
{pi_i} that together span the carrier, we can reconstruct a carrier
vector up to null-space. We check: (a) redundant projections recover
the original; (b) insufficient projections leave residual; (c) the
reconstruction is a candidate, not a theorem -- we mark the residual.
"""
import numpy as np
import sys, os
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _holodeck_common import build_manifest, write_results, summary_ok

TOOL_MANIFEST = build_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
TOOL_INTEGRATION_DEPTH["numpy"] = "load_bearing"
TOOL_MANIFEST["numpy"]["used"] = True
TOOL_MANIFEST["numpy"]["reason"] = "least-squares reconstruction"


def reconstruct(projectors, measurements):
    A = np.vstack(projectors)
    b = np.concatenate(measurements)
    x, *_ = np.linalg.lstsq(A, b, rcond=None)
    return x


def run_positive_tests():
    r = {}
    v_true = np.array([1.0, -2.0, 3.0, 0.5])
    P1 = np.eye(4)[:2]        # observes coords 0,1
    P2 = np.eye(4)[2:]        # observes coords 2,3
    m1 = P1 @ v_true
    m2 = P2 @ v_true
    v_rec = reconstruct([P1, P2], [m1, m2])
    r["full_reconstruction"] = np.allclose(v_rec, v_true, atol=1e-9)
    # overdetermined still works
    P3 = np.array([[1.0, 1.0, 0.0, 0.0]])
    m3 = P3 @ v_true
    v_rec2 = reconstruct([P1, P2, P3], [m1, m2, m3])
    r["overdetermined_ok"] = np.allclose(v_rec2, v_true, atol=1e-9)
    return r


def run_negative_tests():
    r = {}
    # Insufficient projections: claim perfect recovery (should be False)
    v_true = np.array([1.0, -2.0, 3.0, 0.5])
    P1 = np.eye(4)[:2]
    m1 = P1 @ v_true
    v_rec = reconstruct([P1], [m1])
    r["partial_claims_full"] = np.allclose(v_rec, v_true, atol=1e-6)
    return r


def run_boundary_tests():
    r = {}
    # zero vector reconstructs to zero
    P = np.eye(4)
    v_rec = reconstruct([P], [np.zeros(4)])
    r["zero_recon"] = np.allclose(v_rec, 0)
    # degenerate (rank-deficient) projection still returns *a* candidate
    P_deg = np.array([[1.0, 0, 0, 0], [1.0, 0, 0, 0]])
    v_rec = reconstruct([P_deg], [np.array([1.0, 1.0])])
    r["degenerate_returns_candidate"] = v_rec is not None and np.isfinite(v_rec).all()
    return r


if __name__ == "__main__":
    results = {
        "name": "sim_holodeck_reality_reconstruction_probe",
        "classification": "classical_baseline",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }
    results["pass"] = summary_ok(results)
    path = write_results("sim_holodeck_reality_reconstruction_probe", results)
    print(f"pass={results['pass']} -> {path}")
    sys.exit(0 if results["pass"] else 1)
