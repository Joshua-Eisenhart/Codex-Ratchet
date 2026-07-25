#!/usr/bin/env python3
"""Extract the 21 output-contract keys from a lane's stdout, and diff two extracts.

Usage:
    contract_extract.py extract <lane_stdout_file>
    contract_extract.py diff <baseline_json> <mutated_json>

The lane contract is the LAST line of stdout. Julia's last line carries the
contract keys plus a lane_detail block; only the contract keys are compared.
Nothing here computes a fixture answer -- it only reads what a lane printed.
"""

import json
import sys

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


def extract(path):
    lines = [ln for ln in open(path).read().splitlines() if ln.strip()]
    if not lines:
        return None
    obj = json.loads(lines[-1])
    return {k: obj.get(k) for k in CONTRACT_KEYS}


def main():
    mode = sys.argv[1]
    if mode == "extract":
        got = extract(sys.argv[2])
        print(json.dumps(got, sort_keys=True, indent=2))
    elif mode == "diff":
        a = json.load(open(sys.argv[2]))
        b = json.load(open(sys.argv[3]))
        moved = []
        for k in CONTRACT_KEYS:
            if a.get(k) != b.get(k):
                moved.append({"key": k, "before": a.get(k), "after": b.get(k)})
        print(json.dumps({"n_keys": len(CONTRACT_KEYS),
                          "n_moved": len(moved),
                          "moved": moved}, sort_keys=True, indent=2))
    else:
        raise SystemExit("unknown mode " + mode)


if __name__ == "__main__":
    main()
