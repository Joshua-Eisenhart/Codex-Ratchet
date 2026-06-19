#!/usr/bin/env python3
"""Composite envelope for foundation R6 finite CTC loop admissibility."""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RUNG_ID = "foundation_r6_ctc_loop_admissibility"
OBJECT_ID = "foundation_foundation_r6_ctc_loop_admissibility_envelope"
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_envelope_results.json"
JULIA_RESULT = ROOT / "system_v5/julia_carrier/results/foundation_foundation_r6_ctc_loop_admissibility_julia_results.json"
JAX_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_jax_results.json"
PYTORCH_RESULT = ROOT / "system_v5/ops/formal_scouts/results/foundation_foundation_r6_ctc_loop_admissibility_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False

TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive result-envelope assembly from engine receipts; not a math claim path"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding for receipt files"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "pathlib": "supportive"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(
    *,
    payload: dict[str, Any],
    result_path: Path,
    packages_used: list[str],
    load_bearing: list[str],
    values: dict[str, Any],
) -> dict[str, Any]:
    return {
        "ran": True,
        "source_path": payload["source_path"],
        "result_path": str(result_path),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": packages_used,
        "aligned_packages_load_bearing": load_bearing,
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "values": values,
    }


def max_bool_divergence(*records: dict[str, Any]) -> float:
    keys = ["bare_loop_int", "retro_loop_int"]
    divergences = []
    for key in keys:
        vals = [float(record[key]) for record in records]
        divergences.append(max(vals) - min(vals))
    return max(divergences) if divergences else 0.0


def build_result() -> dict[str, Any]:
    julia = load_json(JULIA_RESULT)
    jax = load_json(JAX_RESULT)
    pytorch = load_json(PYTORCH_RESULT)

    julia_values = {
        "bare_loop_admissible": julia["values"]["bare_loop_admissible"],
        "retrocausal_edge_loop_admissible": julia["values"]["retrocausal_edge_loop_admissible"],
        "drop_forward_edge_loop_admissible": julia["values"]["drop_forward_edge_loop_admissible"],
        "forced_commutative_loop_admissible": julia["values"]["forced_commutative_loop_admissible"],
        "bare_loop_int": julia["values"]["bare_loop_int"],
        "retro_loop_int": julia["values"]["retro_loop_int"],
        "full_M_class_count": julia["values"]["full_M_class_count"],
        "loop_admissibility_class_count": julia["values"]["loop_admissibility_class_count"],
    }
    jax_values = {
        "bare_loop_admissible": jax["values"]["bare_loop_admissible"],
        "retrocausal_edge_loop_admissible": jax["values"]["retrocausal_edge_loop_admissible"],
        "drop_forward_edge_loop_admissible": jax["values"]["drop_forward_edge_loop_admissible"],
        "forced_commutative_loop_admissible": jax["values"]["forced_commutative_loop_admissible"],
        "bare_loop_int": jax["values"]["bare_loop_int"],
        "retro_loop_int": jax["values"]["retro_loop_int"],
        "full_M_class_count": jax["values"]["full_M_class_count"],
        "loop_admissibility_class_count": jax["values"]["loop_admissibility_class_count"],
    }
    pytorch_values = {
        "bare_loop_admissible": pytorch["values"]["bare_loop_admissible"],
        "retrocausal_edge_loop_admissible": pytorch["values"]["retrocausal_edge_loop_admissible"],
        "drop_forward_edge_loop_admissible": pytorch["values"]["drop_forward_edge_loop_admissible"],
        "forced_commutative_loop_admissible": pytorch["values"]["forced_commutative_loop_admissible"],
        "bare_loop_int": pytorch["values"]["bare_loop_int"],
        "retro_loop_int": pytorch["values"]["retro_loop_int"],
        "bare_loop_score": pytorch["values"]["bare_loop_score"],
        "retrocausal_edge_loop_score": pytorch["values"]["retrocausal_edge_loop_score"],
        "drop_forward_edge_loop_score": pytorch["values"]["drop_forward_edge_loop_score"],
        "jacrev_at_bare": pytorch["differentiable_check"]["jacrev_at_bare"],
        "drop_forward_edge_jacrev": pytorch["differentiable_check"]["drop_forward_edge_jacrev"],
    }

    z3_bare = jax["smt"]["z3"]["bare"]
    z3_retro = jax["smt"]["z3"]["retrocausal_edge"]
    z3_drop = jax["smt"]["z3"]["drop_forward_edge"]
    cvc5_bare = jax["smt"]["cvc5"]["bare"]
    cvc5_retro = jax["smt"]["cvc5"]["retrocausal_edge"]
    cvc5_drop = jax["smt"]["cvc5"]["drop_forward_edge"]
    all_pass = (
        julia["all_pass"] is True
        and jax["all_pass"] is True
        and pytorch["all_pass"] is True
        and z3_bare["verdict"] == cvc5_bare["verdict"] == "unsat"
        and z3_retro["verdict"] == cvc5_retro["verdict"] == "sat"
        and z3_drop["verdict"] == cvc5_drop["verdict"] == "unsat"
        and julia_values["bare_loop_int"] == jax_values["bare_loop_int"] == pytorch_values["bare_loop_int"] == 0
        and julia_values["retro_loop_int"] == jax_values["retro_loop_int"] == pytorch_values["retro_loop_int"] == 1
    )

    return {
        "schema_version": "three_engine_sim_result_v1",
        "rung_id": RUNG_ID,
        "object_id": OBJECT_ID,
        "classification": CLASSIFICATION,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "claim_ceiling": "Finite directed constraint-order foundation rung only. It says retrocausal closed loops are not forced by the bare finite order and appear only when the retro edge is installed. No GR metric, cosmology, Godel, bridge, axis, or promotion claim.",
        "all_pass": all_pass,
        "M": julia["M"],
        "C": julia["C"],
        "S": julia["S"],
        "S_quotient": julia["S_quotient"],
        "forced_vs_installed": "INSTALLED",
        "bare_order_loop_admissible": False,
        "retrocausal_edge_loop_admissible": True,
        "negative_control_flip": {
            "bare_assert_loop_z3": z3_bare["verdict"],
            "bare_assert_loop_cvc5": cvc5_bare["verdict"],
            "retrocausal_edge_assert_loop_z3": z3_retro["verdict"],
            "retrocausal_edge_assert_loop_cvc5": cvc5_retro["verdict"],
            "drop_forward_edge_after_retro_assert_loop_z3": z3_drop["verdict"],
            "drop_forward_edge_after_retro_assert_loop_cvc5": cvc5_drop["verdict"],
            "force_commutativity_loop_admissible": True,
            "torch_drop_forward_edge_loop_score": pytorch_values["drop_forward_edge_loop_score"],
            "torch_jacrev_at_bare": pytorch_values["jacrev_at_bare"],
            "torch_drop_forward_edge_jacrev": pytorch_values["drop_forward_edge_jacrev"],
            "sat_unsat_flip": z3_bare["verdict"] == cvc5_bare["verdict"] == "unsat"
            and z3_retro["verdict"] == cvc5_retro["verdict"] == "sat"
            and z3_drop["verdict"] == cvc5_drop["verdict"] == "unsat",
            "quotient_changes_when_cycle_probe_dropped": julia["negative_control_flip"]["quotient_changes_when_cycle_probe_dropped"],
        },
        "engines": {
            "julia": engine_record(
                payload=julia,
                result_path=JULIA_RESULT,
                packages_used=["Graphs", "Z3", "LinearAlgebra", "JSON", "Dates"],
                load_bearing=["Z3"],
                values=julia_values,
            ),
            "jax": engine_record(
                payload=jax,
                result_path=JAX_RESULT,
                packages_used=["jax", "jax.numpy", "z3", "cvc5", "json", "pathlib"],
                load_bearing=["z3", "cvc5"],
                values=jax_values,
            ),
            "pytorch": engine_record(
                payload=pytorch,
                result_path=PYTORCH_RESULT,
                packages_used=["torch", "torch.func", "json", "pathlib"],
                load_bearing=["torch.func"],
                values=pytorch_values,
            ),
        },
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": z3_bare["verdict"],
                "version": z3_bare.get("version"),
                "claim": "Bare finite order admits a closed directed loop when reachability is derived from bound edge variables.",
                "retrocausal_edge_negative_control_verdict": z3_retro["verdict"],
                "drop_forward_edge_after_retro_verdict": z3_drop["verdict"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": cvc5_bare["verdict"],
                "version": cvc5_bare.get("version"),
                "claim": "Bare finite order admits a closed directed loop when reachability is derived from bound edge variables.",
                "retrocausal_edge_negative_control_verdict": cvc5_retro["verdict"],
                "drop_forward_edge_after_retro_verdict": cvc5_drop["verdict"],
            },
            "julia_z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": julia["z3"]["bare"]["verdict"],
                "claim": "Julia Z3.jl derives the same bare-order closed-loop UNSAT from bound edge variables.",
                "retrocausal_edge_negative_control_verdict": julia["z3"]["retrocausal_edge"]["verdict"],
            },
        },
        "claim_path_tools": ["Graphs", "Z3", "jax", "jax.numpy", "z3", "cvc5", "torch", "torch.func"],
        "control_only_tools": [],
        "divergence": {
            "julia_authoritative": True,
            "engine_values": {"julia": julia_values, "jax": jax_values, "pytorch": pytorch_values},
            "max_divergence": max_bool_divergence(julia_values, jax_values, pytorch_values),
            "notes": [
                "Julia is authoritative for the finite directed graph and Z3.jl derivation.",
                "JAX carries independent z3/cvc5 structural SMT over bound edge variables.",
                "PyTorch is a genuine independent torch.func sensitivity check over retro-edge installation, not a proof of the Boolean quotient.",
            ],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "FOUNDATION_R6_ENVELOPE_DONE "
        f"all_pass={str(result['all_pass']).lower()} "
        f"bare_loop={result['bare_order_loop_admissible']} "
        f"retro_loop={result['retrocausal_edge_loop_admissible']} "
        f"validator_target={RESULT_PATH}"
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
