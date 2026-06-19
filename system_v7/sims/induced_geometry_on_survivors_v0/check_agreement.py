#!/usr/bin/env python3
"""Two-leg agreement check for induced_geometry_on_survivors_v0.

The checker reads only the exact and JAX result JSON files. It does not
recompute the graph. Exit 0 iff both independently produced legs agree on the
quotient relation, recomputed survivor geometry, stale-control failure, and
state/data perturbation flip.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SIM_ID = "induced_geometry_on_survivors_v0"
HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
OUT = RESULTS / f"{SIM_ID}_agreement_results.json"
LEGS = {
    "exact": RESULTS / f"{SIM_ID}_exact_results.json",
    "jax": RESULTS / f"{SIM_ID}_jax_results.json",
}


def metric_projection(metric: dict[str, object]) -> dict[str, object]:
    return {
        "survivor_count": metric["survivor_count"],
        "vertices": metric["vertices"],
        "nearest_distance": metric["nearest_distance"],
        "edge_count": metric["edge_count"],
        "degree_sequence": metric["degree_sequence"],
        "degree_by_vertex": metric["degree_by_vertex"],
        "component_count": metric["component_count"],
        "diameter": metric["diameter"],
        "connected": metric["connected"],
    }


def main() -> int:
    failures: list[str] = []
    legs: dict[str, dict[str, object]] = {}
    for name, path in LEGS.items():
        if not path.exists():
            failures.append(f"{name}: missing result {path.name}")
            continue
        legs[name] = json.loads(path.read_text())

    for name, obj in legs.items():
        if obj.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification is {obj.get('classification')}")
        if obj.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed is not false")
        if obj.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: formal_admission_allowed is not false")
        if obj.get("reads_peer_result") is not False:
            failures.append(f"{name}: reads_peer_result is not false")
        if obj.get("all_tests_pass") is not True:
            failures.append(f"{name}: all_tests_pass is not true")
        if obj.get("all_controls_pass") is not True:
            failures.append(f"{name}: all_controls_pass is not true")

    if len(legs) == 2:
        styles = {name: obj.get("computation_style") for name, obj in legs.items()}
        if len(set(styles.values())) != len(styles):
            failures.append(f"computation styles are not distinct: {styles}")

        if legs["exact"].get("quotient_relation") != legs["jax"].get("quotient_relation"):
            failures.append("quotient_relation differs across legs")
        if legs["exact"].get("quotient_summary") != legs["jax"].get("quotient_summary"):
            failures.append("quotient_summary differs across legs")

        for seq_name in ("primary_sequence",):
            exact_steps = legs["exact"][seq_name]
            jax_steps = legs["jax"][seq_name]
            if len(exact_steps) != len(jax_steps):
                failures.append(f"{seq_name}: step count differs")
                continue
            for i, (ex_step, jx_step) in enumerate(zip(exact_steps, jax_steps)):
                if ex_step["constraint"] != jx_step["constraint"]:
                    failures.append(f"{seq_name} step {i}: constraint differs")
                for mode in ("recomputed_geometry", "stale_geometry"):
                    ex_metric = metric_projection(ex_step[mode])
                    jx_metric = metric_projection(jx_step[mode])
                    if ex_metric != jx_metric:
                        failures.append(f"{seq_name} step {i} {mode}: metrics differ")

        ex_final = legs["exact"]["perturbed_sequence"]["steps"][-1]["recomputed_geometry"]
        jx_final = legs["jax"]["perturbed_sequence"]["steps"][-1]["recomputed_geometry"]
        if metric_projection(ex_final) != metric_projection(jx_final):
            failures.append("perturbed final recomputed geometry differs across legs")

        if legs["exact"].get("tests") != legs["jax"].get("tests"):
            failures.append("tests differ across legs")
        if legs["exact"].get("controls") != legs["jax"].get("controls"):
            failures.append("controls differ across legs")

    agreement_ok = not failures and len(legs) == 2
    if len(legs) < 2:
        failures.append(f"only {len(legs)}/2 legs present")
        agreement_ok = False

    agreed = legs.get("exact", {})
    primary = agreed.get("primary_sequence", [])
    result = {
        "schema": "codex_ratchet.agreement_result.v1",
        "sim_id": SIM_ID,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "agreement_ok": agreement_ok,
        "engines_present": sorted(legs),
        "n_engines": len(legs),
        "failures": failures,
        "agreed_primary_step_metrics": [
            {
                "constraint": step["constraint"],
                "recomputed": metric_projection(step["recomputed_geometry"]),
                "stale": metric_projection(step["stale_geometry"]),
            }
            for step in primary
        ],
        "load_bearing_discriminators": {
            "recomputed_geometry_changes_across_constraints": bool(agreed.get("tests", {}).get("recomputed_geometry_changes_across_constraints")),
            "stale_geometry_detectably_wrong": bool(agreed.get("controls", {}).get("stale_geometry_detectably_wrong")),
            "state_data_perturbation_flips_final_geometry": bool(agreed.get("controls", {}).get("state_data_perturbation_flips_final_geometry")),
            "C1_recomputed_not_stale": bool(agreed.get("controls", {}).get("stale_wrong_on_same_C1_survivor_set")),
        },
        "honest_scope": {
            "earns": "two-leg agreement that induced Hamming nearest-neighbor geometry must be recomputed on each survivor set; stale edge restriction is wrong on the same C1 survivor data; a real C3 state predicate perturbation flips final graph metrics.",
            "does_not_earn": "smooth manifold, formal admission, bridge/axis claim, physics, or any promotion beyond scratch_diagnostic.",
        },
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "agreement_ok": agreement_ok,
        "n_engines": len(legs),
        "engines": sorted(legs),
        "failures": failures,
    }, indent=2))
    if failures:
        print(f"\nAGREEMENT CHECK FAILED ({len(failures)} issue(s))", file=sys.stderr)
        return 1
    print("\nAGREEMENT CHECK OK: exact and jax legs agree on recomputed survivor geometry and stale-control failure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
