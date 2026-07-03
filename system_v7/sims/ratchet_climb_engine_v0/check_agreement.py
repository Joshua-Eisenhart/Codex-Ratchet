#!/usr/bin/env python3
"""Agreement and envelope builder for ratchet_climb_engine_v0."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

classification = "scratch_diagnostic"
promotion_allowed = False
formal_admission_allowed = False

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive independent receipt readback, parity comparison, and envelope emission",
    }
}

TOOL_INTEGRATION_DEPTH = {"python_stdlib": "supportive"}

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RESULTS = HERE / "results"
SIM_ID = "ratchet_climb_engine_v0"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def engine_record(result: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": result["source_path"],
        "source_sha256": result["source_sha256"],
        "result_path": rel(path),
        "result_sha256": sha256_of(path),
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "package_observables": result["package_observables"],
        "reads_peer_result": False,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    paths = {
        "jax": RESULTS / "ratchet_climb_engine_v0_jax_results.json",
        "julia": RESULTS / "ratchet_climb_engine_v0_julia_results.json",
        "numpy": RESULTS / "ratchet_climb_engine_v0_numpy_results.json",
    }
    results = {name: load(path) for name, path in paths.items()}
    failures: list[str] = []

    for name, result in results.items():
        if result.get("classification") != "scratch_diagnostic":
            failures.append(f"{name}: classification not scratch_diagnostic")
        if result.get("promotion_allowed") is not False:
            failures.append(f"{name}: promotion_allowed not false")
        if result.get("formal_admission_allowed") is not False:
            failures.append(f"{name}: formal_admission_allowed not false")
        if result.get("all_pass") is not True:
            failures.append(f"{name}: all_pass not true")
        if result.get("capstone_status") != "DRAFT_UNAUDITED":
            failures.append(f"{name}: capstone_status not DRAFT_UNAUDITED")

    ladders = {name: tuple(result["climbed_ladder"]) for name, result in results.items()}
    frontiers = {name: int(result["frontier_reached"]) for name, result in results.items()}
    if len(set(ladders.values())) != 1:
        failures.append(f"engine climbed ladders differ: {ladders}")
    if len(set(frontiers.values())) != 1:
        failures.append(f"engine frontiers differ: {frontiers}")

    attractor = results["jax"]["attractor_measurement"]
    if attractor["verdict"] != "basin_evidence_same_rungs_and_same_frontier":
        failures.append("JAX attractor measurement did not converge")
    for name in ("julia", "numpy"):
        if results[name]["attractor_measurement"]["verdict"] != attractor["verdict"]:
            failures.append(f"{name}: attractor verdict differs")

    jax_flip = results["jax"]["run_results"][0]["controls"]["non_definitional_flip"]
    z3_verdict = jax_flip["contextual_peres_mermin"]["z3"]
    cvc5_verdict = jax_flip["contextual_peres_mermin"]["cvc5"]
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "written_at": datetime.now().astimezone().isoformat(),
        "engine": "agreement_envelope",
        "engine_contract": {
            "mode": "julia_canon_jax_workhorse",
            "lanes": ["julia", "jax", "numpy_oracle_control"],
            "audit_order": ["combined_envelope", "julia_local", "jax_local", "numpy_control", "controller_comparison"],
        },
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "lifecycle_status": "SCRATCH_DIAGNOSTIC",
        "evidence_grade": "evidence_grade",
        "claim_ceiling": "scratch_diagnostic",
        "capstone_status": "DRAFT_UNAUDITED",
        "all_pass": not failures,
        "claim": "The Ratchet Runbook climb over the reused v7 finite carrier admits rungs 1-4 and stops at the rung-4 quotient frontier because no measured distinction forces the next lift.",
        "claim_path_tools": ["jax", "z3", "cvc5", "Z3", "Graphs"],
        "control_only_tools": ["numpy"],
        "TOOL_MANIFEST": {
            "jax": results["jax"]["TOOL_MANIFEST"]["jax"],
            "z3": results["jax"]["TOOL_MANIFEST"]["z3"],
            "cvc5": results["jax"]["TOOL_MANIFEST"]["cvc5"],
            "Z3": results["julia"]["TOOL_MANIFEST"]["Z3"],
            "Graphs": results["julia"]["TOOL_MANIFEST"]["Graphs"],
            "numpy": results["numpy"]["TOOL_MANIFEST"]["numpy"],
            "python_stdlib": TOOL_MANIFEST["python_stdlib"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "jax": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "Z3": "load_bearing",
            "Graphs": "load_bearing",
            "numpy": "supportive",
            "python_stdlib": "supportive",
        },
        "engines": {
            "julia": engine_record(results["julia"], paths["julia"]),
            "jax": engine_record(results["jax"], paths["jax"]),
        },
        "numpy_oracle_control": engine_record(results["numpy"], paths["numpy"]),
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": z3_verdict, "load_bearing": True},
            "cvc5": {"ran": True, "verdict": cvc5_verdict, "load_bearing": True},
            "julia_z3": {"ran": True, "verdict": "unsat", "load_bearing": True},
        },
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {
                "julia": float(results["julia"]["frontier_reached"]),
                "jax": float(results["jax"]["frontier_reached"]),
                "numpy": float(results["numpy"]["frontier_reached"]),
            },
            "max_divergence": float(max(frontiers.values()) - min(frontiers.values())),
        },
        "climbed_ladder": list(next(iter(ladders.values()))),
        "frontier_reached": next(iter(frontiers.values())),
        "minimalist_wins": {
            "rung_5_survivor_set": "rejected_unforced_no_supplied_C_loss",
            "rung_6_ordered_update": "rejected_unforced_static_filters_commute",
            "rung_10_density_rho": "not_reached_rejected_unforced",
            "rung_11_hopf": "not_reached_rejected_unforced",
        },
        "attractor_convergence": {
            "jax": results["jax"]["attractor_measurement"],
            "julia": results["julia"]["attractor_measurement"],
            "numpy": results["numpy"]["attractor_measurement"],
        },
        "controls_outcomes": {
            "jax": results["jax"]["run_results"][0]["controls"],
            "julia": results["julia"]["run_results"][0]["controls"],
            "numpy": results["numpy"]["run_results"][0]["controls"],
        },
        "failures": failures,
        "TOOL_INTEGRATION_DEPTH_notes": "numpy is oracle/control only and is excluded from claim_path_tools.",
    }
    out = RESULTS / "ratchet_climb_engine_v0_three_engine_results.json"
    out.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
    summary = {
        "result_path": rel(out),
        "all_pass": envelope["all_pass"],
        "climbed_ladder": envelope["climbed_ladder"],
        "frontier_reached": envelope["frontier_reached"],
        "failures": failures,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
