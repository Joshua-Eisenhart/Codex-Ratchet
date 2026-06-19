#!/usr/bin/env python3
"""Build standard three-engine envelope for ECD.01."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import ecd01_order_programmable_computer_v0_common as common

import sys

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


SOURCE_PATH = Path(__file__).resolve()
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_comparison(julia: dict[str, Any], jax: dict[str, Any], pytorch: dict[str, Any]) -> dict[str, Any]:
    engine_values = {
        "julia": julia["channel_hash_classes"],
        "jax": jax["channel_hash_classes"],
        "pytorch": pytorch["channel_hash_classes"],
    }
    max_divergence = 0
    rows = {}
    for word in common.REGISTERED_ORDER_WORDS:
        values = {engine: classes[word] for engine, classes in engine_values.items()}
        match = len(set(values.values())) == 1
        if not match:
            max_divergence += 1
        rows[word] = {"hashes": values, "match": match}
    return {
        "julia_authoritative": True,
        "engine_values": engine_values,
        "comparison": rows,
        "max_divergence": max_divergence,
        "verdict": "aligned" if max_divergence == 0 else "diverged",
    }


def build_result() -> dict[str, Any]:
    obj = common.build_order_programmability_object()
    julia = load_json(common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json")
    jax = load_json(common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json")
    pytorch = load_json(common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json")
    divergence = lane_comparison(julia, jax, pytorch)
    all_pass = obj["all_pass"] and julia["all_pass"] and jax["all_pass"] and pytorch["all_pass"] and divergence["max_divergence"] == 0
    lanes = {
        "julia": {
            "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_julia.jl"),
            "result_path": common.rel(common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"),
            "all_pass": julia["all_pass"],
            "packages_used": julia["packages_used"],
            "aligned_packages_load_bearing": julia["aligned_packages_load_bearing"],
            "package_observables": julia["package_observables"],
            "tool_calls": ["Graphs.SimpleDiGraph", "Graphs.add_edge!", "Z3.Solver", "Z3.check"],
            "observables": julia["observables"],
        },
        "jax": {
            "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_jax.py"),
            "result_path": common.rel(common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"),
            "all_pass": jax["all_pass"],
            "packages_used": jax["packages_used"],
            "aligned_packages_load_bearing": jax["aligned_packages_load_bearing"],
            "package_observables": jax["package_observables"],
            "tool_calls": ["nx.Graph", "sp.symbols", "z3.Solver.check", "cvc5.Solver.checkSat"],
            "observables": jax["observables"],
        },
        "pytorch": {
            "source_path": common.rel(common.SIM_DIR / f"{common.SIM_ID}_pytorch.py"),
            "result_path": common.rel(common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"),
            "all_pass": pytorch["all_pass"],
            "packages_used": pytorch["packages_used"],
            "aligned_packages_load_bearing": pytorch["aligned_packages_load_bearing"],
            "package_observables": pytorch["package_observables"],
            "tool_calls": ["torch.func.vmap", "sp.symbols", "z3.Solver.check", "cvc5.Solver.checkSat"],
            "observables": pytorch["observables"],
        },
    }
    envelope = build_envelope(
        sim_id=common.SIM_ID,
        lanes=lanes,
        mode=common.ENGINE_MODE,
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func"],
        crossover_proofs=obj["crossover_proofs"],
        divergence=divergence,
        classification=common.CLASSIFICATION,
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "ecd_registry": "7c3f4b48d:system_v6/receipts/engine_capability_differentiators_20260612.md",
            "axis4_fixture": "99c4f84b3:system_v6/sims/discrete_axis4_composition_v0",
            "szilard_ledger": "system_v6/sims/carnot_szilard_landauer_ledger_v1",
        },
        stability_pairs=[
            ("channel_hash_classes", common.stable_sha256(obj["channel_hash_classes"])),
            ("channel_distinguishability_matrix", common.stable_sha256(obj["channel_distinguishability_matrix"])),
            ("capability_metric", common.stable_sha256(obj["capability_metric"])),
        ],
        extra_fields={
            **obj,
            "source_path": common.rel(SOURCE_PATH),
            "result_path": common.rel(RESULT_PATH),
            "all_pass": all_pass,
            "validator_expected_commands": [
                f"PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{common.SIM_ID}/{common.SIM_ID}_jax.py",
                f"JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project={common.ROOT}/system_v5/julia_carrier system_v6/sims/{common.SIM_ID}/{common.SIM_ID}_julia.jl",
                f"PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{common.SIM_ID}/{common.SIM_ID}_pytorch.py",
                f"PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{common.SIM_ID}/{common.SIM_ID}_envelope.py",
                f"PYTHONDONTWRITEBYTECODE=1 /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 system_v6/sims/{common.SIM_ID}/validate_{common.SIM_ID}.py",
            ],
        },
    )
    envelope["all_pass"] = all_pass
    return envelope


def main() -> int:
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"result_path": common.rel(RESULT_PATH), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
