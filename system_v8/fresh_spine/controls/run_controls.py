#!/usr/bin/env python3
"""Re-execute the whole negative-control lane and write the measured matrix.

Every row is derived from a process this script started: argv, exit code,
stdout byte count, stdout sha256, and the per-key contract movement against the
matching baseline. Nothing is hand-entered. No ran / verdict / load_bearing
field is written.

    python3 run_controls.py            # writes out/control_matrix_v0.json
"""

import hashlib
import json
import pathlib
import subprocess
import time

FS = pathlib.Path("/Users/joshuaeisenhart/Codex-Ratchet/system_v8/fresh_spine")
C = FS / "controls"
OUT = C / "out"
OUT.mkdir(parents=True, exist_ok=True)
PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"

CONTRACT_KEYS = [
    "f0_diag_a0", "f0_diag_a1", "f0_diag_a2", "f0_coh_a0", "f0_coh_a1", "f0_coh_a2",
    "f1_fibre_sizes", "f1_kappa", "f1_q2_fibre_sizes",
    "f2_checker_edges", "f2_ring_edges", "f2_checker_cycles", "f2_ring_cycles",
    "f2_n1_ring_cycles_after_cut", "f2_n2_degree_changed", "f2_n3_edge_counts_differ",
    "f3_seam_satisfied_edges", "f3_seam_total_edges", "f3_r1_quotient_vertices",
    "f3_r2_violating_edges", "f3_r2_blocked",
]

# row = (control, lane, argv, cwd, env_overlay, baseline_row_or_None, what_it_severs)
ROWS = [
    ("baseline", "jax", [PY, str(FS / "jax_lane.py")], FS, {}, None, "nothing"),
    ("baseline", "pytorch", [PY, str(FS / "pytorch_lane.py")], FS, {}, None, "nothing"),
    ("baseline", "julia", [JULIA, str(FS / "julia_lane.jl")], FS, {}, None, "nothing"),
    ("baseline", "analytic_control", [PY, str(FS / "ground_truth_v0.py")], FS, {}, None, "nothing"),

    ("C1_dependency_kill", "jax", [PY, str(FS / "jax_lane.py")], FS,
     {"PYTHONPATH": str(C / "shims" / "nojax")}, ("baseline", "jax"), "import jax"),
    ("C1_dependency_kill", "pytorch", [PY, str(FS / "pytorch_lane.py")], FS,
     {"PYTHONPATH": str(C / "shims" / "notorch")}, ("baseline", "pytorch"), "import torch"),
    ("C1_dependency_kill", "julia", [JULIA, str(FS / "julia_lane.jl")], FS,
     {"JULIA_LOAD_PATH": "@stdlib"}, ("baseline", "julia"), "Graphs.jl / JSON.jl load path"),

    ("C2a_rank_kernel", "jax", [PY, str(C / "mutants" / "c2a_rank_jax_lane.py")], C / "mutants", {},
     ("baseline", "jax"), "the matrix_rank call behind f0_*_a2"),
    ("C2a_rank_kernel", "pytorch", [PY, str(C / "mutants" / "c2a_rank_pytorch_lane.py")], C / "mutants", {},
     ("baseline", "pytorch"), "the Bareiss elimination behind f0_*_a2"),
    ("C2a_rank_kernel", "julia", [JULIA, str(C / "mutants" / "c2a_rank_julia_lane.jl")], C / "mutants", {},
     ("baseline", "julia"), "the exact_rank row echelon behind f0_*_a2"),

    ("C2b_adjacency_build", "jax", [PY, str(C / "mutants" / "c2b_adj_jax_lane.py")], C / "mutants", {},
     ("baseline", "jax"), "the symmetric adjacency scatter behind f2_*"),
    ("C2b_adjacency_build", "pytorch", [PY, str(C / "mutants" / "c2b_adj_pytorch_lane.py")], C / "mutants", {},
     ("baseline", "pytorch"), "the symmetric adjacency scatter behind f2_*"),
    ("C2b_adjacency_build", "julia", [JULIA, str(C / "mutants" / "c2b_adj_julia_lane.jl")], C / "mutants", {},
     ("baseline", "julia"), "the Graphs.add_edge! head vertex behind f2_*"),

    ("C3_wrong_carrier_gate", "pytorch", [PY, str(C / "c3_n3" / "pytorch_lane.py")], C / "c3_n3", {},
     ("baseline", "pytorch"), "the 4-cube fixture, lane unmodified"),
    ("C3_wrong_carrier_gate", "julia", [JULIA, str(C / "c3_n3" / "julia_lane.jl")], C / "c3_n3", {},
     ("baseline", "julia"), "the 4-cube fixture, lane unmodified"),
    ("C3_wrong_carrier", "jax", [PY, str(C / "c3_n3" / "jax_lane.py")], C / "c3_n3", {},
     ("baseline", "jax"), "the 4-cube carrier (3-cube substituted)"),
    ("C3_wrong_carrier", "pytorch", [PY, str(C / "c3_n3" / "pytorch_lane_shaok.py")], C / "c3_n3", {},
     ("baseline", "pytorch"), "the 4-cube carrier (3-cube substituted)"),
    ("C3_wrong_carrier", "julia", [JULIA, str(C / "c3_n3" / "julia_lane_n3.jl")], C / "c3_n3", {},
     ("baseline", "julia"), "the 4-cube carrier (3-cube substituted)"),
    ("C3_wrong_carrier", "analytic_control", [PY, str(C / "c3_n3" / "ground_truth_v0.py")], C / "c3_n3", {},
     ("baseline", "analytic_control"), "the 4-cube carrier (3-cube substituted)"),

    ("C4a_wrong_order_inconsistent", "jax", [PY, str(C / "c4a_inconsistent" / "jax_lane.py")], C / "c4a_inconsistent", {},
     ("baseline", "jax"), "Gray-code RING order; declared order left as Gray"),
    ("C4a_wrong_order_inconsistent", "pytorch", [PY, str(C / "c4a_inconsistent" / "pytorch_lane_shaok.py")], C / "c4a_inconsistent", {},
     ("baseline", "pytorch"), "Gray-code RING order; declared order left as Gray"),
    ("C4a_wrong_order_inconsistent", "julia", [JULIA, str(C / "c4a_inconsistent" / "julia_lane.jl")], C / "c4a_inconsistent", {},
     ("baseline", "julia"), "Gray-code RING order; declared order left as Gray"),
    ("C4a_wrong_order_inconsistent", "analytic_control", [PY, str(C / "c4a_inconsistent" / "ground_truth_v0.py")], C / "c4a_inconsistent", {},
     ("baseline", "analytic_control"), "Gray-code RING order; declared order left as Gray"),
    ("C4b_wrong_order_consistent", "jax", [PY, str(C / "c4b_consistent" / "jax_lane.py")], C / "c4b_consistent", {},
     ("baseline", "jax"), "Gray-code RING order; declared order re-declared to match"),
    ("C4b_wrong_order_consistent", "pytorch", [PY, str(C / "c4b_consistent" / "pytorch_lane_shaok.py")], C / "c4b_consistent", {},
     ("baseline", "pytorch"), "Gray-code RING order; declared order re-declared to match"),
    ("C4b_wrong_order_consistent", "julia", [JULIA, str(C / "c4b_consistent" / "julia_lane.jl")], C / "c4b_consistent", {},
     ("baseline", "julia"), "Gray-code RING order; declared order re-declared to match"),
    ("C4b_wrong_order_consistent", "analytic_control", [PY, str(C / "c4b_consistent" / "ground_truth_v0.py")], C / "c4b_consistent", {},
     ("baseline", "analytic_control"), "Gray-code RING order; declared order re-declared to match"),

    ("C6_numpy_poison", "jax", [PY, str(FS / "jax_lane.py")], FS,
     {"PYTHONPATH": str(C / "shims" / "nonumpy")}, ("baseline", "jax"), "import numpy"),
    ("C6_numpy_poison", "pytorch", [PY, str(FS / "pytorch_lane.py")], FS,
     {"PYTHONPATH": str(C / "shims" / "nonumpy")}, ("baseline", "pytorch"), "import numpy"),
    ("C6_numpy_poison", "analytic_control", [PY, str(FS / "ground_truth_v0.py")], FS,
     {"PYTHONPATH": str(C / "shims" / "nonumpy")}, ("baseline", "analytic_control"), "import numpy"),
]


def contract_of(text, lane):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return None
    if lane == "analytic_control":
        # ground_truth_v0.py prints its contract as an indented JSON block first
        try:
            start = text.index("{")
            end = text.index("}\n", start) + 1
            return {k: json.loads(text[start:end]).get(k) for k in CONTRACT_KEYS}
        except Exception:
            return None
    try:
        obj = json.loads(lines[-1])
    except Exception:
        return None
    return {k: obj.get(k) for k in CONTRACT_KEYS}


def moved(base, now):
    if base is None or now is None:
        return None
    return [{"key": k, "before": base.get(k), "after": now.get(k)}
            for k in CONTRACT_KEYS if base.get(k) != now.get(k)]


def main():
    import os
    results = {}
    for control, lane, argv, cwd, envx, baseline, severs in ROWS:
        env = dict(os.environ)
        env.update(envx)
        t0 = time.time()
        p = subprocess.Popen(argv, cwd=str(cwd), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env=env)
        pid = p.pid
        so, se = p.communicate()
        rec = {
            "control": control,
            "lane": lane,
            "what_it_severs": severs,
            "argv": argv,
            "cwd": str(cwd),
            "env_overlay": envx,
            "launched_pid": pid,
            "exit_code": p.returncode,
            "elapsed_s": round(time.time() - t0, 3),
            "stdout_bytes": len(so),
            "stdout_sha256": hashlib.sha256(so).hexdigest(),
            "stderr_tail": se.decode("utf-8", "replace").strip().splitlines()[-1:],
        }
        text = so.decode("utf-8", "replace")
        c = contract_of(text, lane) if p.returncode == 0 else None
        rec["contract_captured"] = c is not None
        results[control + "|" + lane] = (rec, c, baseline)
        print("%-32s %-16s exit=%-3d %7dB %6.2fs" %
              (control, lane, p.returncode, len(so), rec["elapsed_s"]))

    matrix = []
    for key, (rec, c, baseline) in results.items():
        if baseline is not None:
            bkey = baseline[0] + "|" + baseline[1]
            brec, bc, _ = results[bkey]
            rec["baseline_row"] = bkey
            rec["baseline_exit_code"] = brec["exit_code"]
            rec["baseline_stdout_bytes"] = brec["stdout_bytes"]
            m = moved(bc, c)
            rec["n_contract_keys"] = len(CONTRACT_KEYS)
            rec["n_contract_keys_moved"] = None if m is None else len(m)
            rec["contract_movement"] = m
            rec["exit_code_moved"] = rec["exit_code"] != brec["exit_code"]
            rec["discriminated"] = bool(
                rec["exit_code_moved"] or (m is not None and len(m) > 0))
        matrix.append(rec)

    out = OUT / "control_matrix_v0.json"
    out.write_text(json.dumps({
        "receipt": "fresh_spine negative-control matrix",
        "rule": "every row derived from a process this script started; exit codes read from the OS",
        "python": PY, "julia": JULIA,
        "rows": matrix,
    }, indent=2, sort_keys=True) + "\n")
    print("\nwrote", out)


if __name__ == "__main__":
    main()
