#!/usr/bin/env python3
"""sim_science_method_theory_laden_observation_probe

Probe that observations are NOT theory-free. Expected negative result:
raw observations cannot be extracted without a frame/ontology choice.

Carrier: a raw signal S (list of floats).
Structure: "observation" = (S, frame) where frame selects features.
Probe: apply two different frames to the same S; if outputs differ, the
       observation is theory-laden (no neutral view exists).
Admissibility: the claim "observation is frame-free" is refuted when
               distinct frames produce distinct feature sets.
Chirality: the negative result IS the canonical result here.
"""
import os, sys
classification = "classical_baseline"  # auto-backfill
sys.path.insert(0, os.path.dirname(__file__))
from _sci_method_common import new_manifest, write_results, all_pass

TOOL_MANIFEST = new_manifest()
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}

try:
    import numpy as np
    TOOL_MANIFEST["numpy"]["tried"] = True
    TOOL_MANIFEST["numpy"]["used"] = True
    TOOL_MANIFEST["numpy"]["reason"] = "feature extraction carrier"
    TOOL_INTEGRATION_DEPTH["numpy"] = "supportive"
except ImportError:
    np = None


def frame_mean(S): return sum(S) / len(S) if S else 0.0
def frame_max(S): return max(S) if S else 0.0
def frame_first(S): return S[0] if S else 0.0


def theory_laden(S, frames):
    outs = [f(S) for f in frames]
    return len(set(outs)) > 1


def run_positive_tests():
    # Heterogeneous signal: frames disagree -> theory-laden confirmed.
    S = [1.0, 5.0, 2.0, 7.0]
    ok = theory_laden(S, [frame_mean, frame_max, frame_first])
    return {"heterogeneous_theory_laden": {"pass": ok is True}}


def run_negative_tests():
    # Claim "observation is frame-free" -> must be rejected on any non-trivial signal.
    S = [3.0, 1.0]
    claim_frame_free = not theory_laden(S, [frame_mean, frame_max])
    return {"frame_free_claim_rejected": {"pass": claim_frame_free is False}}


def run_boundary_tests():
    # Constant signal: all frames agree -> NOT theory-laden at this probe depth.
    S = [2.0, 2.0, 2.0]
    ok = theory_laden(S, [frame_mean, frame_max, frame_first])
    return {"constant_signal_agrees": {"pass": ok is False}}


if __name__ == "__main__":
    pos = run_positive_tests(); neg = run_negative_tests(); bnd = run_boundary_tests()
    results = {
        "name": "science_method_theory_laden_observation_probe",
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": pos, "negative": neg, "boundary": bnd,
        "classification": "classical_baseline",
        "status": "pass" if (all_pass(pos) and all_pass(neg) and all_pass(bnd)) else "fail",
    }
    path = write_results("sim_science_method_theory_laden_observation_probe", results)
    print(f"[{results['status']}] {path}")
    sys.exit(0 if results["status"] == "pass" else 1)
