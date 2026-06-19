#!/usr/bin/env python3
"""Envelope for geo_s10_g2_family_v0."""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
from pathlib import Path
from typing import Any

from geo_s10_g2_family_v0_common import (
    CLASSIFICATION,
    FORMAL_ADMISSION_ALLOWED,
    G2_DISCRIMINATOR_PATH,
    NEMO_RECEIPT_PATH,
    PROMOTION_ALLOWED,
    READS_PEER_RESULT,
    RESULT_DIR,
    ROOT,
    SIM_ID,
    file_sha256,
    write_json,
)


SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_envelope.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
JULIA_RESULT = RESULT_DIR / f"{SIM_ID}_julia_results.json"
JAX_RESULT = RESULT_DIR / f"{SIM_ID}_jax_results.json"
PYTORCH_RESULT = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
NEMO_RESULT = RESULT_DIR / f"{SIM_ID}_nemo_hecke_results.json"


TOOL_MANIFEST = {
    "json": {"tried": True, "used": True, "reason": "supportive envelope assembly from packet-local lane receipts"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive source/result hash checks"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive deterministic path binding"},
}
TOOL_INTEGRATION_DEPTH = {"json": "supportive", "hashlib": "supportive", "pathlib": "supportive"}
classification = "scratch_diagnostic"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def engine_record(payload: dict[str, Any], result_path: Path) -> dict[str, Any]:
    return {
        "ran": payload["all_pass"] is True,
        "source_path": payload["source_path"],
        "source_sha256": payload["source_sha256"],
        "result_path": str(result_path.relative_to(ROOT)),
        "reads_peer_result": payload["reads_peer_result"],
        "packages_used": payload["packages_used"],
        "aligned_packages_load_bearing": payload["aligned_packages_load_bearing"],
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "tool_manifest": payload["TOOL_MANIFEST"],
        "tool_integration_depth": payload["TOOL_INTEGRATION_DEPTH"],
        "tool_calls": payload["tool_calls"],
        "claim_path_tools": payload["claim_path_tools"],
        "shared_scalars": payload.get("shared_scalars", {}),
        "capability_receipts": payload.get("capability_receipts", {}),
    }


def aggregate_tool_calls(lanes: dict[str, dict[str, Any]], nemo: dict[str, Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for lane_name, payload in lanes.items():
        for call in payload.get("tool_calls", []):
            calls.append({"source": f"engine:{lane_name}", **call})
    for call in nemo.get("tool_calls", []):
        calls.append({"source": "sidecar:nemo_hecke", **call})
    return calls


def divergence(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    values = {engine: payload["shared_scalars"] for engine, payload in payloads.items()}
    common = sorted(set.intersection(*(set(v) for v in values.values())))
    rows = []
    max_divergence = 0
    for key in common:
        row_values = {engine: values[engine][key] for engine in values}
        exact = len(set(json.dumps(v, sort_keys=True) for v in row_values.values())) == 1
        rows.append({"key": key, "values": row_values, "exact_match": exact})
        if not exact:
            max_divergence = 1
    return {
        "julia_authoritative": True,
        "engine_values": values,
        "common_keys_checked": common,
        "max_divergence": max_divergence,
        "comparison": {"rows": rows, "exact_match": max_divergence == 0},
        "meaning": "exact comparison over scalars common to Julia carrier, JAX-labeled, and PyTorch-labeled lanes",
    }


def compare_nemo(nemo_payload: dict[str, Any]) -> dict[str, Any]:
    committed = load_json(NEMO_RECEIPT_PATH)
    committed_probe = committed["probes"][0]["probe_result"]
    current = nemo_payload["probe_result"]
    keys = [
        "sl2_7_order",
        "psl2_7_order",
        "borel_stabilizer_order_in_psl",
        "unipotent_order_in_psl",
        "subgroup_chain_orders",
    ]
    rows = {key: {"current": current[key], "committed": committed_probe[key], "match": current[key] == committed_probe[key]} for key in keys}
    return {
        "committed_receipt": str(NEMO_RECEIPT_PATH.relative_to(ROOT)),
        "committed_classification": committed["classification"],
        "committed_promotion_allowed": committed["promotion_allowed"],
        "rows": rows,
        "all_match": all(row["match"] for row in rows.values()),
        "ceiling_preserved": nemo_payload["classification"] == "tool_lego_fit_probe" and nemo_payload["promotion_allowed"] is False,
    }


def predecessor_anchor() -> dict[str, Any]:
    payload = load_json(G2_DISCRIMINATOR_PATH)
    dims = payload["derivation_dimensions"]["julia"]
    return {
        "path": str(G2_DISCRIMINATOR_PATH.relative_to(ROOT)),
        "classification": payload["classification"],
        "promotion_allowed": payload["promotion_allowed"],
        "formal_admission_allowed": payload["formal_admission_allowed"],
        "forced_vs_installed_verdict": payload["decision"]["forced_vs_installed_verdict"],
        "derivation_anchor": {
            "H": dims["H"]["nullity_dim_der"],
            "M2R": dims["M2R"]["nullity_dim_der"],
            "O": dims["O"]["nullity_dim_der"],
            "O_corrupted": dims["O_corrupted"]["nullity_dim_der"],
        },
        "used_as": "predecessor context only; current packet recomputes requested rows",
    }


def build_result() -> dict[str, Any]:
    lanes = {
        "julia": load_json(JULIA_RESULT),
        "jax": load_json(JAX_RESULT),
        "pytorch": load_json(PYTORCH_RESULT),
    }
    nemo = load_json(NEMO_RESULT)
    math_payload = lanes["jax"]["math_payload"]
    div = divergence(lanes)
    nemo_compare = compare_nemo(nemo)
    smt = math_payload["smt"]
    row_survival = math_payload["row_survival_map_no_crowned_winner"]
    controls = math_payload["controls"]
    gate_pass = {
        "lanes_all_pass": all(lane["all_pass"] is True for lane in lanes.values()),
        "nemo_hecke_pass": nemo["all_pass"] is True,
        "classification_ceiling": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        "no_peer_result_reads": all(lane["reads_peer_result"] is False for lane in lanes.values()),
        "divergence_zero_on_common_scalars": div["max_divergence"] == 0,
        "row_survival_all_true": all(row_survival.values()),
        "fabrication_controls_all_true": all(controls.values()),
        "nemo_matches_committed_fit_probe": nemo_compare["all_match"] and nemo_compare["ceiling_preserved"],
        "no_crowned_winner": True,
    }
    claim_tools = sorted({tool for lane in lanes.values() for tool in lane["claim_path_tools"]} | set(nemo["claim_path_tools"]))
    aggregated_tool_calls = aggregate_tool_calls(lanes, nemo)
    return {
        "schema_version": "three_engine_sim_result_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": "scratch_diagnostic S10 G2-family map; no crowned winner; promotion_allowed=false; formal_admission_allowed=false",
        "claim": "Family map of compact G2, split G_2(2), tensor-square blocks, Spin chain/triality scoped to D4 diagram/character-node automorphism order, not explicit intertwiners, finite Fano/PSL structures, stabilizer choices, and bounded nesting rows.",
        "allowed_claims": [
            "which requested G2-family structures survive the packet-local algebra and finite tests",
            "compact and split derivation dimensions computed from explicit tables",
            "finite Fano/PSL rows are sanity rows only",
            "controls catch echo, compact/split collapse, finite substitution, orientation-label theater, and stabilizer copy-paste",
        ],
        "disallowed_claims": [
            "formal admission",
            "canonical family theorem",
            "compact/split real-form proof from PSL(2,7) alone",
            "crowned winner among family members",
            "bridge, axis, physics, or manifold promotion",
            "explicit triality intertwiners; triality row is D4 diagram/character-node automorphism order, not explicit intertwiners",
        ],
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "reads_peer_result": READS_PEER_RESULT,
        "engine_contract": {
            "mode": "julia_canon_plus_jax_diagnostic",
            "lanes": ["julia", "jax"],
            "audit_order": ["combined_envelope", "julia_carrier", "jax_labeled_python", "pytorch_labeled_python", "nemo_hecke_sidecar", "packet_validator"],
            "declared_mode": "scratch_diagnostic_family_map",
            "mode_rationale": "Decisive rows are Julia-carrier plus shared exact Python/SymPy with the Nemo sidecar; JAX is the declared diagnostic Python/SymPy/solver lane; PyTorch was rerun as a supportive wrapper only and is not required for declared-mode validation.",
            "supportive_lanes": {
                "pytorch": "supportive wrapper rerun; no graph/network/autograd claim path and not required by declared mode",
                "nemo_hecke": "Nemo finite-field sidecar for PSL sanity row; Hecke import remains supportive only",
            },
            "omitted_requirements": {
                "pytorch_required_validator": "dropped because PyTorch is supportive-only for this packet",
                "explicit_triality_intertwiners": "not built; triality row is fenced to D4 diagram/character-node automorphism order, not explicit intertwiners",
            },
            "reads_peer_result": False,
        },
        "canon_runtime": {
            "semantic_owner": "python_sympy_exact_algebra_with_julia_carrier_anchor",
            "julia_project": "system_v5/julia_carrier",
            "nemo_hecke_project": "system_v6/optional/nemo_hecke",
            "proof_tag": "s10_g2_family_exact_table_derivation_and_finite_orientation_map",
            "consumer_policy": "scratch diagnostic; no promotion",
        },
        "foreign_runtime_manifest": {
            "julia": lanes["julia"]["runtime"],
            "jax": lanes["jax"]["runtime"],
            "pytorch": lanes["pytorch"]["runtime"],
            "nemo_hecke": nemo["runtime"],
            "tensor_exchange": "none",
            "forbidden_exchange": [".numpy", "np.asarray", "csv", "pickle", "hidden_host_copy"],
        },
        "source_inputs": lanes["jax"]["source_inputs"],
        "predecessor_anchor": predecessor_anchor(),
        "nemo_hecke": {"current": nemo, "committed_compare": nemo_compare},
        "engines": {
            "julia": engine_record(lanes["julia"], JULIA_RESULT),
            "jax": engine_record(lanes["jax"], JAX_RESULT),
            "pytorch": engine_record(lanes["pytorch"], PYTORCH_RESULT),
        },
        "math_payload": math_payload,
        "row_survival_map_no_crowned_winner": row_survival,
        "gate_pass": gate_pass,
        "all_pass": all(gate_pass.values()),
        "claim_path_tools": claim_tools,
        "control_only_tools": [],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": aggregated_tool_calls,
        "tool_call_aggregation": {
            "source": "lane-local function-level receipts plus Nemo sidecar",
            "count": len(aggregated_tool_calls),
            "claim_path_tools_one_to_one_boundary": sorted({call["tool"] for call in aggregated_tool_calls if call.get("tool") in claim_tools}) == claim_tools,
        },
        "triality_scope_fence": "D4 diagram/character-node automorphism order, not explicit intertwiners",
        "crossover_proofs": {
            "z3": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["z3"]["real"]["status"],
                "negative_control_verdict": smt["z3"]["erased"]["status"],
                "erase_flip": smt["z3"]["flip"],
            },
            "cvc5": {
                "ran": True,
                "load_bearing": True,
                "verdict": smt["cvc5"]["real"]["status"],
                "negative_control_verdict": smt["cvc5"]["erased"]["status"],
                "erase_flip": smt["cvc5"]["flip"],
            },
            "julia_z3": lanes["julia"]["crossover_proofs"]["julia_z3"],
        },
        "divergence": div,
    }


def main() -> int:
    result = build_result()
    write_json(RESULT_PATH, result)
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_json": str(RESULT_PATH.relative_to(ROOT)),
                "compact_der_dim": result["math_payload"]["algebra"]["compact_g2_aut_o"]["derivation"]["nullity_dim_der"],
                "split_der_dim": result["math_payload"]["algebra"]["split_g2_2_aut_o_split"]["derivation"]["nullity_dim_der"],
                "orientation_family_count": result["math_payload"]["finite_structures"]["fano_orientation_family"]["orientation_family_count"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
