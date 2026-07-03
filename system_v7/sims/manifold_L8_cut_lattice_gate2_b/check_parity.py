#!/usr/bin/env python3
"""Compare the Gate 2 Builder B numpy and Julia legs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


SIM_ID = "manifold_L8_cut_lattice_gate2_b"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
NUMPY = RESULTS / f"{SIM_ID}_numpy_results.json"
JULIA = RESULTS / f"{SIM_ID}_julia_results.json"
OUT = RESULTS / f"{SIM_ID}_parity_results.json"
TOL = 1e-9

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False
TOOL_MANIFEST = {
    "json": {
        "used": True,
        "reason": "load-bearing comparison of independently generated numpy and Julia Gate 2 receipts",
    }
}
TOOL_INTEGRATION_DEPTH = {"json": "load_bearing"}


def load(path: Path):
    return json.loads(path.read_text())


def by_label_cut(rows):
    return {(r["label"], tuple(r["cut"]), r.get("side", "left")): r for r in rows}


def main() -> None:
    n = load(NUMPY)
    j = load(JULIA)
    failures = []

    scalar_paths = [
        ("cut_formula.enumerated_count", n["cut_formula"]["enumerated_count"], j["cut_formula"]["enumerated_count"]),
        ("enumeration.state_count", n["enumeration"]["state_count"], j["enumeration"]["state_count"]),
        ("enumeration.cut_count", n["enumeration"]["cut_count"], j["enumeration"]["cut_count"]),
        ("enumeration.state_cut_pair_count", n["enumeration"]["state_cut_pair_count"], j["enumeration"]["state_cut_pair_count"]),
        ("enumeration.per_cut_side_marginal_records", n["enumeration"]["per_cut_side_marginal_records"], j["enumeration"]["per_cut_side_marginal_records"]),
        ("enumeration.extension_compatibility_checks", n["enumeration"]["extension_compatibility_checks"], j["enumeration"]["extension_compatibility_checks"]),
        ("summary.controls_passed", n["summary"]["controls_passed"], j["summary"]["controls_passed"]),
        ("summary.controls_total", n["summary"]["controls_total"], j["summary"]["controls_total"]),
    ]
    for name, a, b in scalar_paths:
        if a != b:
            failures.append({"path": name, "numpy": a, "julia": b})

    bool_paths = [
        ("summary.all_pass", n["summary"]["all_pass"], j["summary"]["all_pass"]),
        ("cut_formula.assertion_pass", n["cut_formula"]["assertion_pass"], j["cut_formula"]["assertion_pass"]),
        ("epoch_reprojection.fresh_recompute_compare_pass", n["epoch_reprojection"]["fresh_recompute_compare_pass"], j["epoch_reprojection"]["fresh_recompute_compare_pass"]),
    ]
    for name, a, b in bool_paths:
        if bool(a) != bool(b):
            failures.append({"path": name, "numpy": a, "julia": b})

    nrows = by_label_cut(n["per_state_cut_marginals"])
    jrows = by_label_cut(j["per_state_cut_marginals"])
    if set(nrows) != set(jrows):
        failures.append({"path": "per_state_cut_marginals.keys", "numpy_only": len(set(nrows) - set(jrows)), "julia_only": len(set(jrows) - set(nrows))})
    max_delta = 0.0
    compared = 0
    for key in sorted(set(nrows) & set(jrows)):
        nr = nrows[key]
        jr = jrows[key]
        for field in ("marginal_trace", "marginal_entropy_bits", "parent_negativity"):
            delta = abs(float(nr[field]) - float(jr[field]))
            max_delta = max(max_delta, delta)
            compared += 1
            if delta > TOL:
                failures.append({"path": f"{key}.{field}", "numpy": nr[field], "julia": jr[field], "delta": delta})
        if int(nr["marginal_rank"]) != int(jr["marginal_rank"]):
            failures.append({"path": f"{key}.marginal_rank", "numpy": nr["marginal_rank"], "julia": jr["marginal_rank"]})
        if nr.get("side_subset") != jr.get("side_subset"):
            failures.append({"path": f"{key}.side_subset", "numpy": nr.get("side_subset"), "julia": jr.get("side_subset")})

    n_subsets = n["subset_quotient_summaries"]
    j_subsets = j["subset_quotient_summaries"]
    if set(n_subsets) != set(j_subsets):
        failures.append({"path": "subset_quotient_summaries.keys", "numpy_only": len(set(n_subsets) - set(j_subsets)), "julia_only": len(set(j_subsets) - set(n_subsets))})
    for subset in sorted(set(n_subsets) & set(j_subsets)):
        nr = n_subsets[subset]
        jr = j_subsets[subset]
        for field in ("quotient_basis", "quotient_class_count", "class_sizes"):
            if nr[field] != jr[field]:
                failures.append({"path": f"subset_quotient_summaries.{subset}.{field}", "numpy": nr[field], "julia": jr[field]})
        ndiag = nr["diagnostic_matrix_hash_object"]
        jdiag = jr["diagnostic_matrix_hash_object"]
        for field in ("basis", "class_count", "class_sizes"):
            if ndiag[field] != jdiag[field]:
                failures.append({"path": f"subset_quotient_summaries.{subset}.diagnostic_matrix_hash_object.{field}", "numpy": ndiag[field], "julia": jdiag[field]})

    n_controls = n["negative_controls"]
    j_controls = j["negative_controls"]
    for name in sorted(set(n_controls) | set(j_controls)):
        if bool(n_controls[name]["pass"]) != bool(j_controls[name]["pass"]):
            failures.append({"path": f"negative_controls.{name}.pass", "numpy": n_controls[name]["pass"], "julia": j_controls[name]["pass"]})

    result = {
        "schema": "codex_ratchet.manifold_L8_cut_lattice_gate2_b.parity_result.v1",
        "sim_id": SIM_ID,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "inputs": [str(NUMPY), str(JULIA)],
        "tolerance": TOL,
        "all_pass": not failures,
        "max_abs_delta": max_delta,
        "numeric_fields_compared": compared,
        "failure_count": len(failures),
        "failures": failures[:50],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"WROTE {OUT}")
    print(json.dumps({k: result[k] for k in ("all_pass", "max_abs_delta", "numeric_fields_compared", "failure_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
