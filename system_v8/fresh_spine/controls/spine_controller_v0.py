#!/usr/bin/env python3
"""fresh_spine controller. It LAUNCHES its lanes; it does not read their leftovers.

The one rule this file exists to hold: a controller that reads a stored result
file and reports that an engine ran has measured nothing. So every per-lane
record below is derived from a process THIS process started:

    argv, cwd, pid, exit_code, elapsed_s, stdout_bytes, stdout_sha256

No field named ran, verdict or load_bearing is written anywhere. `exit_code` is
the integer the OS handed back. `agreement_with_analytic_control` is a
comparison of two contracts this run captured.

The analytic control (ground_truth_v0.py) is launched the same way. Its written
JSON is only accepted if its mtime is later than the moment this controller
started it, so a leftover file from an earlier run cannot stand in for it.

STALE-ARTIFACT CHECK (--claimed FILE)
    FILE is a JSON object {lane_name: contract} that someone claims is this
    run's output. The controller launches the lanes regardless, then compares
    the claim against what it measured. Divergence is reported per lane and
    makes the exit code non-zero. The claim is never a substitute for launching.

Usage:
    spine_controller_v0.py [--claimed FILE] [--out FILE]
"""

import argparse
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

FS = pathlib.Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v8/fresh_spine")
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"

CONTRACT_KEYS = [
    "f0_diag_a0", "f0_diag_a1", "f0_diag_a2",
    "f0_coh_a0", "f0_coh_a1", "f0_coh_a2",
    "f1_fibre_sizes", "f1_kappa", "f1_q2_fibre_sizes",
    "f2_checker_edges", "f2_ring_edges",
    "f2_checker_cycles", "f2_ring_cycles",
    "f2_n1_ring_cycles_after_cut",
    "f2_n2_degree_changed", "f2_n3_edge_counts_differ",
    "f3_seam_satisfied_edges", "f3_seam_total_edges",
    "f3_r1_quotient_vertices", "f3_r2_violating_edges", "f3_r2_blocked",
]

LANES = [
    ("jax", [PY, str(FS / "jax_lane.py")]),
    ("pytorch", [PY, str(FS / "pytorch_lane.py")]),
    ("julia", [JULIA, str(FS / "julia_lane.jl")]),
]

# A1 for COHERENT is log2(80); the three lanes land on adjacent float64 values.
# Integer contract keys are compared exactly. Only these float keys carry a
# tolerance, and the tolerance is stated rather than hidden in a helper.
FLOAT_KEYS = {"f0_diag_a0", "f0_diag_a1", "f0_coh_a0", "f0_coh_a1", "f1_kappa"}
FLOAT_TOL = 1e-12


def launch(argv, cwd):
    """Start a process, wait, and return only what the OS and the pipe reported."""
    t0 = time.time()
    proc = subprocess.Popen(argv, cwd=cwd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    pid = proc.pid
    out, err = proc.communicate()
    return {
        "argv": argv,
        "cwd": str(cwd),
        "launched_pid": pid,
        "exit_code": proc.returncode,
        "elapsed_s": round(time.time() - t0, 3),
        "stdout_bytes": len(out),
        "stdout_sha256": hashlib.sha256(out).hexdigest(),
        "stderr_tail": err.decode("utf-8", "replace")[-400:],
        "_stdout": out.decode("utf-8", "replace"),
    }


def last_json_line(text):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except Exception:
        return None


def contract_of(text):
    obj = last_json_line(text)
    if obj is None:
        return None
    return {k: obj.get(k) for k in CONTRACT_KEYS}


def compare(a, b):
    """Per-key comparison of two captured contracts. Returns the divergences."""
    if a is None or b is None:
        return [{"key": "*", "reason": "one side has no parsable contract"}]
    diffs = []
    for k in CONTRACT_KEYS:
        x, y = a.get(k), b.get(k)
        if k in FLOAT_KEYS:
            xs = x if isinstance(x, list) else [x]
            ys = y if isinstance(y, list) else [y]
            if len(xs) != len(ys):
                diffs.append({"key": k, "left": x, "right": y,
                              "reason": "different length"})
                continue
            for u, v in zip(xs, ys):
                if u is None or v is None:
                    if u != v:
                        diffs.append({"key": k, "left": x, "right": y,
                                      "reason": "None on one side only"})
                        break
                elif abs(float(u) - float(v)) > FLOAT_TOL:
                    diffs.append({"key": k, "left": x, "right": y,
                                  "reason": "outside stated tolerance %g" % FLOAT_TOL})
                    break
        elif x != y:
            diffs.append({"key": k, "left": x, "right": y, "reason": "exact mismatch"})
    return diffs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--claimed", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    report = {
        "controller": "fresh_spine/controls/spine_controller_v0.py",
        "rule": "every per-lane record below was derived from a process this controller started",
        "controller_pid": os.getpid(),
        "started_unix": time.time(),
        "lanes": {},
        "analytic_control": {},
        "cross_lane": {},
        "claim_check": None,
    }

    # ---- analytic control, launched, and its output file freshness measured ----
    gt_json = FS / "ground_truth_v0.json"
    t_before = time.time()
    gt_run = launch([PY, str(FS / "ground_truth_v0.py")], FS)
    gt_text = gt_run.pop("_stdout")
    gt_mtime = gt_json.stat().st_mtime if gt_json.exists() else None
    gt_contract = None
    if gt_run["exit_code"] == 0 and gt_mtime is not None and gt_mtime >= t_before:
        gt_contract = {k: json.loads(gt_json.read_text())["contract"].get(k)
                       for k in CONTRACT_KEYS}
    gt_run["output_file"] = str(gt_json)
    gt_run["output_file_mtime_after_launch"] = (
        gt_mtime is not None and gt_mtime >= t_before)
    gt_run["contract_accepted"] = gt_contract is not None
    gt_run["stdout_head"] = gt_text[:80]
    report["analytic_control"] = gt_run

    # ---- engine lanes, each launched ----
    measured = {}
    for name, argv in LANES:
        rec = launch(argv, FS)
        text = rec.pop("_stdout")
        c = contract_of(text) if rec["exit_code"] == 0 else None
        rec["contract_captured"] = c is not None
        rec["contract"] = c
        measured[name] = c
        if c is not None and gt_contract is not None:
            d = compare(c, gt_contract)
            rec["divergences_from_analytic_control"] = d
            rec["agreement_with_analytic_control"] = (len(d) == 0)
        else:
            rec["agreement_with_analytic_control"] = None
        report["lanes"][name] = rec

    names = [n for n, _ in LANES]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            d = compare(measured[a], measured[b])
            report["cross_lane"]["%s_vs_%s" % (a, b)] = {
                "n_divergences": len(d), "divergences": d}

    # ---- stale-artifact check ----
    ok = all(r["exit_code"] == 0 for r in report["lanes"].values())
    ok = ok and gt_contract is not None
    ok = ok and all(r["agreement_with_analytic_control"] for r in report["lanes"].values())

    if args.claimed:
        claimed = json.loads(pathlib.Path(args.claimed).read_text())
        per = {}
        for name in names:
            if name not in claimed:
                per[name] = {"claim_present": False}
                continue
            d = compare(claimed[name], measured[name])
            per[name] = {
                "claim_present": True,
                "n_divergences_from_measurement": len(d),
                "claim_survived_measurement": len(d) == 0,
                "divergences": d[:6],
            }
        report["claim_check"] = {
            "claimed_file": args.claimed,
            "claimed_file_sha256": hashlib.sha256(
                pathlib.Path(args.claimed).read_bytes()).hexdigest(),
            "note": "the lanes were launched regardless; the claim was compared, never trusted",
            "per_lane": per,
            "all_claims_survived": all(
                v.get("claim_survived_measurement") for v in per.values()),
        }
        ok = ok and report["claim_check"]["all_claims_survived"]

    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n")
    print(text)

    # exit code is the controller's own summary; it is derived, not written
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main())
