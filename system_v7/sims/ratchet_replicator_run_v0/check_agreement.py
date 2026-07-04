#!/usr/bin/env python3
"""Agreement envelope for ratchet_replicator_run_v0."""

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
SIM_ID = "ratchet_replicator_run_v0"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path) -> str:
    return path.resolve().relative_to(REPO).as_posix()


def timeline_counts(result: dict[str, Any], mode: str) -> list[int]:
    return [int(row["distinguishable_history_class_count"]) for row in result["runs"][mode]["timeline"]]


def motif_counts(result: dict[str, Any], mode: str) -> dict[str, int]:
    return {str(k): int(v) for k, v in result["runs"][mode]["motif_counts"].items()}


def engine_record(result: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": result["source_path"],
        "source_sha256": result["source_sha256"],
        "result_path": rel(path),
        "result_sha256": sha256_of(path),
        "packages_used": result["packages_used"],
        "aligned_packages_load_bearing": result["aligned_packages_load_bearing"],
        "classification": result["classification"],
        "promotion_allowed": result["promotion_allowed"],
        "formal_admission_allowed": result["formal_admission_allowed"],
        "reads_peer_result": False,
    }


def main() -> int:
    RESULTS.mkdir(exist_ok=True)
    paths = {
        "jax": RESULTS / f"{SIM_ID}_jax_results.json",
        "julia": RESULTS / f"{SIM_ID}_julia_results.json",
        "numpy": RESULTS / f"{SIM_ID}_numpy_results.json",
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

    for mode in ("commuting", "noncommuting"):
        histories = {name: timeline_counts(result, mode) for name, result in results.items()}
        if len({tuple(v) for v in histories.values()}) != 1:
            failures.append(f"{mode}: history-class timelines differ")
        motifs = {name: motif_counts(result, mode) for name, result in results.items()}
        if len({json.dumps(v, sort_keys=True) for v in motifs.values()}) != 1:
            failures.append(f"{mode}: motif counts differ")
        halts = {name: result["runs"][mode]["halted_at_step"] for name, result in results.items()}
        if len({json.dumps(v, sort_keys=True) for v in halts.values()}) != 1:
            failures.append(f"{mode}: halt steps differ {halts}")

    rep_verdicts = {name: result["replicator_verdict"]["verdict"] for name, result in results.items()}
    if len(set(rep_verdicts.values())) != 1:
        failures.append(f"replicator verdicts differ: {rep_verdicts}")

    jax = results["jax"]
    noncommuting_history_values = {
        name: float(result["frontier_result"]["noncommuting"]["final_history_class_count"])
        for name, result in results.items()
    }
    envelope = {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "written_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
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
        "claim_ceiling": "scratch_diagnostic",
        "capstone_status": "DRAFT_UNAUDITED",
        "all_pass": not failures,
        "claim": "Scratch diagnostic only: old headline saturation, replicator, and equivalence verdicts were by-construction; repaired output reports parameter sweeps, copy-step-only replicator detection, and adversarial closure-demand fixtures.",
        "claim_path_tools": ["python_stdlib", "z3", "cvc5", "Graphs", "Julia Base"],
        "control_only_tools": ["numpy", "jax"],
        "TOOL_MANIFEST": {
            "python_stdlib": jax["TOOL_MANIFEST"]["python_stdlib"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "Graphs": results["julia"]["TOOL_MANIFEST"]["Graphs"],
            "Julia Base": results["julia"]["TOOL_MANIFEST"]["Julia Base"],
            "numpy": results["numpy"]["TOOL_MANIFEST"]["numpy"],
            "jax": results["jax"]["TOOL_MANIFEST"]["jax"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "python_stdlib": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "Graphs": "load_bearing",
            "Julia Base": "load_bearing",
            "numpy": "supportive",
            "jax": "supportive",
        },
        "engines": {
            "julia": engine_record(results["julia"], paths["julia"]),
            "jax": engine_record(results["jax"], paths["jax"]),
        },
        "numpy_oracle_control": engine_record(results["numpy"], paths["numpy"]),
        "saturation_theorem_check": jax["saturation_theorem_check"],
        "equivalence_property_lifts": jax["equivalence_property_lifts"],
        "replicator_verdict": jax["replicator_verdict"],
        "replicator_scan_by_branch": jax["replicator_scan_by_branch"],
        "possibility_field_ledger_summary": {
            mode: {
                "steps": len(jax["runs"][mode]["possibility_field_ledger"]),
                "final": jax["runs"][mode]["possibility_field_ledger"][-1],
            }
            for mode in ("commuting", "noncommuting")
        },
        "frontier_result": jax["frontier_result"],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": noncommuting_history_values,
            "max_divergence": float(max(noncommuting_history_values.values()) - min(noncommuting_history_values.values())),
        },
        "crossover_proofs": {
            "z3": {"ran": True, "verdict": jax["crossover_proofs"]["z3"]["forbidden_reflexive"], "load_bearing": True},
            "cvc5": {"ran": True, "verdict": jax["crossover_proofs"]["cvc5"]["forbidden_reflexive"], "load_bearing": True},
        },
        "parity": {
            "history_class_counts": "PASS" if not any("history-class" in f for f in failures) else "FAIL",
            "motif_counts": "PASS" if not any("motif counts" in f for f in failures) else "FAIL",
            "halt_steps": "PASS" if not any("halt steps" in f for f in failures) else "FAIL",
            "replicator_verdict": "PASS" if not any("replicator verdicts" in f for f in failures) else "FAIL",
        },
        "failures": failures,
    }
    out = RESULTS / f"{SIM_ID}_three_engine_results.json"
    out.write_text(json.dumps(envelope, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"result_path": rel(out), "all_pass": envelope["all_pass"], "failures": failures}, indent=2, sort_keys=True))
    return 0 if envelope["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
