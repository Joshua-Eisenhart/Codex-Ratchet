#!/usr/bin/env python3
"""Build the standard result envelope for axis0_amendment_light_sweep_v1."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


SIM_ID = "axis0_amendment_light_sweep_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"

sys.path.insert(0, str(ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()).hexdigest()


def lane_comparison(jax: dict[str, Any], julia: dict[str, Any]) -> dict[str, Any]:
    jax_hashes = jax["computed_vector_hashes"]
    julia_hashes = julia["computed_vector_hashes"]
    rows = {}
    max_divergence = 0
    for candidate in sorted(set(jax_hashes) | set(julia_hashes)):
        same = jax_hashes.get(candidate) == julia_hashes.get(candidate)
        rows[candidate] = {
            "jax_sha256": jax_hashes.get(candidate),
            "julia_sha256": julia_hashes.get(candidate),
            "match": same,
        }
        if not same:
            max_divergence += 1
    return {
        "julia_authoritative": True,
        "comparison": rows,
        "engine_values": {
            "jax": jax_hashes,
            "julia": julia_hashes,
        },
        "max_divergence": max_divergence,
        "verdict": "aligned" if max_divergence == 0 else "diverged",
    }


def build_result() -> dict[str, Any]:
    jax = load_json(JAX_RESULT)
    julia = load_json(JULIA_RESULT)
    divergence = lane_comparison(jax, julia)
    all_pass = bool(jax["all_pass"] and julia["all_pass"] and divergence["max_divergence"] == 0)
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "all_pass": all_pass,
        "envelope_built_with_helper": True,
        "build_helper_path": "scripts/build_three_engine_envelope.py",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim": jax["claim"],
        "allowed_claims": jax["allowed_claims"],
        "disallowed_claims": jax["disallowed_claims"],
        "authority_binding": jax["authority_binding"],
        "carrier_binding": jax["carrier_binding"],
        "candidate_verdict_table": jax["candidate_verdict_table"],
        "per_candidate_verdicts": jax["per_candidate_verdicts"],
        "alias_pair_table": jax["alias_pair_table"],
        "control_verdicts": jax["control_verdicts"],
        "prior_light_regression_verdicts": jax["prior_light_regression_verdicts"],
        "v0_regression_rows": jax["v0_regression_rows"],
        "fork_row": jax["fork_row"],
        "queued_heavy": jax["queued_heavy"],
        "counts": jax["counts"],
        "computed_vector_hashes": jax["computed_vector_hashes"],
        "lane_comparison": divergence,
        "build_gates": {
            **jax["build_gates"],
            "julia_mirror_all_pass": julia["all_pass"],
            "lane_vector_hashes_match": divergence["max_divergence"] == 0,
            "pythorch_omission_honest_for_light_pass": True,
        },
        "TOOL_INTENT_MATRIX": {
            **jax["TOOL_INTENT_MATRIX"],
            "julia": {
                "Graphs": "independent finite directed graph mirror",
                "LinearAlgebra": "independent vN entropy/trace-norm mirror",
            },
            "pytorch": "omitted: light rerun required Julia exact mirror minimum; no tensor/autograd claim path is made",
        },
        "tool_intent": jax["TOOL_INTENT_MATRIX"],
        "TOOL_MANIFEST": {**jax["TOOL_MANIFEST"], **julia["TOOL_MANIFEST"]},
        "TOOL_INTEGRATION_DEPTH": {**jax["TOOL_INTEGRATION_DEPTH"], **julia["TOOL_INTEGRATION_DEPTH"]},
        "validator_expected_commands": [
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis0_amendment_light_sweep_v1/axis0_amendment_light_sweep_v1_jax.py",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/axis0_amendment_light_sweep_v1/axis0_amendment_light_sweep_v1_julia.jl",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis0_amendment_light_sweep_v1/axis0_amendment_light_sweep_v1_envelope.py",
            "PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/axis0_amendment_light_sweep_v1/validate_axis0_amendment_light_sweep_v1.py",
        ],
    }
    lanes = {
        "julia": {
            "source_path": rel(SIM_DIR / f"{SIM_ID}_julia.jl"),
            "result_path": rel(JULIA_RESULT),
            "all_pass": julia["all_pass"],
            "packages_used": julia["packages_used"],
            "aligned_packages_load_bearing": julia["aligned_packages_load_bearing"],
            "package_observables": julia["package_observables"],
            "tool_calls": ["Graphs.SimpleDiGraph", "strongly_connected_components", "LinearAlgebra.norm"],
            "observables": julia["build_gates"],
        },
        "jax": {
            "source_path": rel(SIM_DIR / f"{SIM_ID}_jax.py"),
            "result_path": rel(JAX_RESULT),
            "all_pass": jax["all_pass"],
            "packages_used": jax["packages_used"],
            "aligned_packages_load_bearing": jax["aligned_packages_load_bearing"],
            "package_observables": jax["package_observables"],
            "tool_calls": ["networkx.DiGraph", "z3.Solver.check", "cvc5.Solver.checkSat"],
            "observables": jax["build_gates"],
        },
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes=lanes,
        expected_lanes=("julia", "jax", "pytorch"),
        omitted_lanes={"pytorch": "omitted for Supplement-pinned light pass; Julia exact mirror added as the required non-Python lane, and no tensor/autograd claim path is made"},
        mode="supplement_pinned_axis0_light_sweep_with_julia_exact_mirror",
        claim_path_tools=["Graphs", "networkx", "sympy", "z3", "cvc5", "build_three_engine_envelope"],
        crossover_proofs=jax["crossover_proofs"],
        divergence=divergence,
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "amendment_supplement_1": "34596316d:system_v6/receipts/axis0_registry_amendment_1_20260612.md",
            "v0_audit_verdict": "system_v6/sims/axis0_amendment_light_sweep_v0/audit_verdict.md",
            "committed_carrier": "system_v6/sims/discrete_axis0_field_v0/results/discrete_axis0_field_v0_envelope_results.json",
        },
        stability_pairs=[
            ("candidate_vector_hashes", stable_hash(jax["computed_vector_hashes"])),
            ("fork_row", stable_hash(jax["fork_row"])),
            ("v0_regression_rows", stable_hash(jax["v0_regression_rows"])),
        ],
        extra_fields=extra_fields,
    )
    envelope["all_pass"] = all_pass
    return envelope


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": rel(RESULT_PATH), "all_pass": result["all_pass"], "max_divergence": result["divergence"]["max_divergence"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
