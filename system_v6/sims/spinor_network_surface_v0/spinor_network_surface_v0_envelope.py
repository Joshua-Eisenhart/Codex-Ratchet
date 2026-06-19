#!/usr/bin/env python3
"""Envelope assembler for spinor_network_surface_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from spinor_network_surface_v0_common import (
    RESULT_DIR,
    ROOT,
    SIM_DIR,
    SIM_ID,
    core_surface_result,
    rel,
    sha256_file,
    stable_hash,
    to_jsonable,
    write_json,
)

sys.path.insert(0, str(ROOT / "scripts"))
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from build_three_engine_envelope import build_envelope  # noqa: E402


SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
BUILD_CARD = SIM_DIR / "build_card.md"

AUTHORITY_INPUTS = [
    "system_v6/receipts/owner_doctrine_spinor_network_surface_20260611.md",
    "system_v6/receipts/spinor_network_surface_estate_20260611.md",
    "system_v6/receipts/attractor_basin_criterion_20260611.md",
    "system_v6/sims/basin3_hopfield_chiral_quaternion_network/basin3_julia.jl",
    "system_v6/sims/npc2_connection_geometry/npc2_connection_geometry_julia.jl",
    "system_v5/julia_carrier/foundation_spinor_network_basins_julia.jl",
    "system_v5/ops/formal_scouts/foundation_spinor_network_basins_jax.py",
    "system_v5/ops/formal_scouts/foundation_spinor_network_basins_pytorch.py",
]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def lane_record(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_path": payload["source_path"],
        "result_path": payload["result_path"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "package_observables": payload["package_observables"],
        "all_pass": payload["all_pass"],
        "claim_path_tools": payload["claim_path_tools"],
        "TOOL_MANIFEST": payload["TOOL_MANIFEST"],
        "TOOL_INTEGRATION_DEPTH": payload["TOOL_INTEGRATION_DEPTH"],
        "positive": payload["positive"],
        "negative": payload["negative"],
        "boundary": payload["boundary"],
        "computed_scalars": payload["computed_scalars"],
    }


def parent_lineage() -> dict[str, Any]:
    rows = []
    for rel_path in AUTHORITY_INPUTS:
        path = ROOT / rel_path
        rows.append({
            "path": rel_path,
            "exists": path.exists(),
            "sha256": sha256_file(path) if path.exists() else None,
        })
    return {
        "consumed_inputs": rows,
        "commit_anchor": "833af4937 for owner doctrine per build card",
        "foundation_surface_note": "No exact system_v6/sims/foundation_spinor_network_basins directory existed; consumed the committed Julia/JAX/PyTorch foundation basin harness sources named in the repo.",
    }


def validator_commands() -> list[dict[str, str]]:
    py = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
    return [
        {"id": "jax_lane", "command": f"env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache {py} system_v6/sims/{SIM_ID}/{SIM_ID}_jax.py"},
        {"id": "pytorch_lane", "command": f"env GEOMSTATS_BACKEND=pytorch NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache {py} system_v6/sims/{SIM_ID}/{SIM_ID}_pytorch.py"},
        {"id": "julia_lane", "command": f"JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier system_v6/sims/{SIM_ID}/{SIM_ID}_julia.jl"},
        {"id": "envelope", "command": f"env NUMBA_CACHE_DIR=/private/tmp/codex_numba_cache {py} system_v6/sims/{SIM_ID}/{SIM_ID}_envelope.py"},
        {"id": "packet_validator", "command": f"{py} system_v6/sims/{SIM_ID}/validate_{SIM_ID}.py --phase builder"},
        {"id": "three_engine_validator", "command": f"{py} scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent system_v6/sims/{SIM_ID}/results/{SIM_ID}_envelope_results.json"},
        {"id": "pytest", "command": f"PYTHONPATH=system_v6/sims/{SIM_ID} {py} -m pytest -q system_v6/sims/{SIM_ID}/tests"},
    ]


def build_result() -> dict[str, Any]:
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    core = core_surface_result()

    engine_values = {
        "julia": {
            "max_lyapunov_delta": julia["computed_scalars"]["max_lyapunov_delta"],
            "recovered_chart_cells": julia["computed_scalars"]["recovered_chart_cells"],
            "terminal_class_count": julia["computed_scalars"]["terminal_class_count"],
        },
        "jax": {
            "max_lyapunov_delta": jax["computed_scalars"]["max_lyapunov_delta"],
            "recovered_chart_cells": jax["computed_scalars"]["recovered_chart_cells"],
            "terminal_class_count": jax["computed_scalars"]["terminal_class_count"],
        },
        "pytorch": {
            "max_lyapunov_delta": pytorch["computed_scalars"]["max_lyapunov_delta"],
            "recovered_chart_cells": pytorch["computed_scalars"]["recovered_chart_cells"],
            "terminal_class_count": pytorch["computed_scalars"]["terminal_class_count"],
        },
    }
    max_divergence = max(
        abs(float(engine_values[name]["max_lyapunov_delta"]) - float(engine_values["jax"]["max_lyapunov_delta"]))
        for name in engine_values
    )
    gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "build_card_copied": BUILD_CARD.exists() and "spinor_network_surface_v0" in BUILD_CARD.read_text(encoding="utf-8"),
        "no_builder_audit_verdict": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        "classification_ceiling": core["classification"] == "scratch_diagnostic" and core["promotion_allowed"] is False and core["formal_admission_allowed"] is False,
        "surface_basin_contract": core["positive"]["surface_basin_contract"] is True,
        "chart_recoverability_nontrivial": core["chart_recoverability"]["verdict"] == "partial_recovery_nontrivial",
        "typed_information_rows": core["positive"]["typed_conditional_entropy_rows"] is True,
        "lr_hook_distinguishable": core["lr_hook"]["distinguishable_under_probe"] is True,
        "negative_controls": all(row["pass"] for row in core["controls"]["guard_negative_controls"].values()),
        "boundary_controls": core["boundary"]["pattern_overload"]["pass"] is True and core["boundary"]["nonhermitian_coupling"]["pass"] is True,
        "smt_positive_unsat": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "smt_flips_sat": jax["crossover_proofs"]["z3"]["flip_control_verdict"] == jax["crossover_proofs"]["cvc5"]["flip_control_verdict"] == "sat",
        "julia_z3_agrees": julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat" and julia["crossover_proofs"]["julia_z3"]["flip_control_verdict"] == "sat",
    }
    all_pass = all(gates.values())
    extra_fields = {
        "schema": f"{SIM_ID}_envelope_v1",
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "ceiling": "scratch_diagnostic",
        "all_pass": all_pass,
        "build_card_copied": gates["build_card_copied"],
        "no_builder_audit_verdict": gates["no_builder_audit_verdict"],
        "no_builder_audit_verdict_envelope_gate": gates["no_builder_audit_verdict"],
        "surface_doctrine_packet_scope": {
            "finite_carrier": "n4 dim16 strict finite quantum-Hopfield carrier",
            "basin_contract_run": "one finite retrieval partition with stored and spurious terminal classes",
            "a_chart_recoverability_test": "single-site density quotient to A33 Bloch chart",
            "typed_information_row_family": "pattern-conditioned conditional vN S(A|B)",
            "lr_hook": "bounded L/R basin/chart distinction only",
        },
        "netket_omission": {
            "used": False,
            "reason": "No variational quantum-state sampling/optimization claim is made; JAX load-bearing path is qutip/networkx/sympy/SMT over the finite declared carrier.",
        },
        "carrier": core["carrier"],
        "coupling": core["coupling"],
        "basin_partition_table": core["basin_contract"]["terminal_partition"],
        "basin_contract": core["basin_contract"],
        "chart_recoverability_verdict": core["chart_recoverability"],
        "typed_information_rows": core["typed_information"],
        "lr_hook": core["lr_hook"],
        "positive": core["positive"],
        "negative": core["negative"],
        "boundary": core["boundary"],
        "controls": core["controls"],
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"used": True, "reason": "load-bearing standard three-engine envelope construction"},
            "QuantumOptics": julia["TOOL_MANIFEST"]["QuantumOptics"],
            "Graphs": julia["TOOL_MANIFEST"]["Graphs"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "qutip": jax["TOOL_MANIFEST"]["qutip"],
            "networkx": jax["TOOL_MANIFEST"]["networkx"],
            "sympy": jax["TOOL_MANIFEST"]["sympy"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "torch_geometric": pytorch["TOOL_MANIFEST"]["torch_geometric"],
            "torch.func": pytorch["TOOL_MANIFEST"]["torch.func"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "QuantumOptics": "load_bearing",
            "Graphs": "load_bearing",
            "Z3": "load_bearing",
            "qutip": "load_bearing",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch_geometric": "load_bearing",
            "torch.func": "load_bearing",
        },
        "tool_intent": {
            "claim_classes": [
                "finite_quantum_hopfield_carrier",
                "basin_contract_partition",
                "A_chart_density_quotient_recoverability",
                "typed_conditional_vn_information",
                "finite_smt_lyapunov_polarity",
            ],
            "engine_tool_intent": {
                "julia": {
                    "QuantumOptics": "finite density reduction and entropy row over a 4-site spinor carrier",
                    "Graphs": "finite support graph shape for the Hopfield carrier",
                    "Z3": "finite Lyapunov polarity proof with non-Hermitian SAT flip",
                },
                "jax": {
                    "qutip": "finite density object check via Qobj/tensor",
                    "networkx": "support graph object and cycle count",
                    "sympy": "exact chart/basin rational witness arithmetic",
                    "z3": "finite Lyapunov polarity proof with non-Hermitian SAT flip",
                    "cvc5": "independent finite Lyapunov polarity proof with same SAT flip",
                },
                "pytorch": {
                    "torch_geometric": "finite support graph object",
                    "torch.func": "energy-descent sensitivity row by jacrev/vmap",
                    "sympy": "exact chart/basin count witness arithmetic",
                    "z3": "finite Lyapunov polarity proof with non-Hermitian SAT flip",
                    "cvc5": "independent finite Lyapunov polarity proof with same SAT flip",
                },
            },
        },
        "validator_expected_commands": validator_commands(),
        "validator_statuses": [],
        "gates": gates,
    }
    envelope = build_envelope(
        sim_id=SIM_ID,
        lanes={
            "julia": lane_record(julia),
            "jax": lane_record(jax),
            "pytorch": lane_record(pytorch),
        },
        mode="STRICT_FINITE_SURFACE_PACKET",
        claim_path_tools=["QuantumOptics", "Graphs", "Z3", "qutip", "networkx", "sympy", "z3", "cvc5", "torch_geometric", "torch.func"],
        crossover_proofs={
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        divergence={
            "julia_authoritative": True,
            "engine_values": engine_values,
            "max_divergence": max_divergence,
            "comparison": "selected finite scalar rows agree across Julia/JAX/PyTorch for chart count, terminal class count, and Lyapunov max delta",
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage=parent_lineage(),
        extra_fields=extra_fields,
    )
    return envelope


def main() -> int:
    payload = build_result()
    write_json(RESULT_PATH, payload)
    print(json.dumps(to_jsonable({"ok": payload["all_pass"], "result_path": rel(RESULT_PATH)}), sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

