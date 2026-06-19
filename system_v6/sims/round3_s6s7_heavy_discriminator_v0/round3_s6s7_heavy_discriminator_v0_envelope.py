#!/usr/bin/env python3
"""Controller envelope for round3_s6s7_heavy_discriminator_v0."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import round3_s6s7_heavy_discriminator_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JULIA_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"
JAX_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
BUILD_CARD = common.SIM_DIR / "build_card.md"

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_show(ref: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{ref}:{path}"], cwd=common.ROOT)


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
        "role_id": payload["role_id"],
        "claim_path_tools": payload["claim_path_tools"],
        "tool_calls": payload["tool_calls"],
        "positive": payload["positive"],
        "negative": payload["negative"],
        "boundary": payload["boundary"],
    }


def verdict_map(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["verdict"] for row in payload.get("candidate_verdicts", [])}


def final_verdict_table(jax: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in jax["candidate_verdicts"]:
        rows.append(
            {
                "candidate": row["candidate"],
                "registry_expected_teeth_row": row["registry_expected_teeth_row"],
                "N_sweep": [item["N"] for item in row["N_sweep"]],
                "separating_sizes": row["separating_sizes"],
                "final_verdict": row["verdict"],
                "citable_witness": row["citable_witness"],
                "co_survivor": row["co_survivor"],
                "size_relative": row["size_relative"],
            }
        )
    return rows


def build_result() -> dict[str, Any]:
    julia = load(JULIA_RESULT)
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    registry_blob = git_show(common.REGISTRY_COMMIT, common.REGISTRY_REL)
    registry_bound = sha256_bytes(registry_blob) == common.sha256_file(common.REGISTRY_PATH)
    jax_map = verdict_map(jax)
    julia_map = verdict_map(julia)
    pytorch_map = verdict_map(pytorch)
    verdicts_match = jax_map == julia_map == pytorch_map == common.EXPECTED_FINAL_VERDICTS
    z3_result = jax["crossover_proofs"]["z3"]
    cvc5_result = jax["crossover_proofs"]["cvc5"]
    julia_z3 = julia["crossover_proofs"]["julia_z3"]
    certificate = jax["control_rows"]["deliberate_reparameterized_cycle_alias"]
    table = final_verdict_table(jax)
    gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "three_engine_verdicts_match": verdicts_match,
        "expected_five_row_verdicts": jax_map == common.EXPECTED_FINAL_VERDICTS,
        "registry_commit_bound": registry_bound,
        "build_card_copied": BUILD_CARD.exists() and "BUILD CARD" in BUILD_CARD.read_text(encoding="utf-8"),
        "s9_queue_read": common.S9_QUEUE_AUDIT.exists(),
        "s6s7_light_verdict_read": common.S6S7_LIGHT_AUDIT.exists(),
        "s4_heavy_precedent_read": common.S4_HEAVY_AUDIT.exists(),
        "s5_heavy_precedent_read": common.S5_HEAVY_AUDIT.exists(),
        "classification_ceiling": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [julia, jax, pytorch]
        ),
        "explicit_mapping_certificate_present": certificate["edge_by_edge_verified"] is True
        and len(certificate["mapping_anchor_to_reparameterized"]) == 8,
        "all_rows_swept_N_8_16_32": all(row["N_sweep"] == common.N_SWEEP for row in table),
        "z3_cvc5_agree": z3_result["verdict"] == cvc5_result["verdict"] == "unsat",
        "julia_z3_agrees": julia_z3["verdict"] == "unsat",
        "flip_controls_fire": z3_result["flip_control_verdict"] == cvc5_result["flip_control_verdict"] == julia_z3["flip_control_verdict"] == "sat",
        "pytorch_graph_claim_scoped": pytorch["aligned_packages_load_bearing"][:2] == ["torch.func", "torch_geometric"],
        "no_cosurvivors_minted": all(row["co_survivor"] is False for row in table),
        "no_size_relative_labels": all(row["size_relative"] is False for row in table),
    }
    all_pass = all(gates.values())
    tool_intent = {
        "claim_classes": [
            "s6s7_phase2_heavy_local_discriminator",
            "explicit_isomorphism_certificate",
            "graph_cost_sweeps_N_8_16_32",
            "cover_lens_incidence_rows",
            "smt_erased_flip_controls",
        ],
        "engine_tool_intent": {
            "julia": {
                "Graphs": "finite support graph rows and N={8,16,32} reference graph/cost sweep recomputation",
                "Z3": "Julia-side finite witness UNSAT with SAT flip",
            },
            "jax": {
                "networkx": "explicit edge-by-edge isomorphism certificate plus finite graph/cost sweeps over N={8,16,32}",
                "sympy": "exact characteristic-polynomial and invariant support rows",
                "z3": "computed integer heavy-row witness UNSAT with erased flip",
                "cvc5": "independent computed integer heavy-row witness UNSAT with erased flip",
            },
            "pytorch": {
                "torch.func": "torch-side batched graph probe source-backed by vmap",
                "torch_geometric": "Data(edge_index) finite support graph carriers for chord/ladder N-sweeps",
                "z3": "computed excluded-count and max-N guard UNSAT",
                "cvc5": "independent excluded-count and max-N guard UNSAT",
            },
        },
    }
    extra_fields = {
        "schema": f"{common.SIM_ID}_envelope_v1",
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "S6/S7 round-3 phase-2 heavy-local discriminator over exactly the five queued S6/S7 rows.",
        "allowed_claims": [
            "the five queued S6/S7 heavy-local representatives were run in this packet",
            "the deliberate reparameterized cycle alias has an explicit edge-by-edge mapping certificate in the result JSON",
            "each non-anchor row is excluded by its registry-named heavy tooth at every N in {8,16,32}",
            "PyTorch/PyG is honestly scoped to finite graph-carrier N-sweeps, not neural training or promotion",
            "no S6/S7 co-survivor label is minted",
        ],
        "disallowed_claims": [
            "global S6/S7 uniqueness",
            "formal or canonical admission",
            "any non-S6/S7 heavy queue completion",
            "size-independent claims beyond N={8,16,32}",
            "numeric spectrum closeness as alias evidence",
        ],
        "registry_binding": {
            "path": common.REGISTRY_REL,
            "commit": common.REGISTRY_COMMIT,
            "commit_blob_sha256": sha256_bytes(registry_blob),
            "working_tree_sha256": common.sha256_file(common.REGISTRY_PATH),
            "s6s7_heavy_teeth_quoted": common.REGISTRY_S6S7_HEAVY_TEETH_QUOTE,
        },
        "source_inputs_read": {
            "consolidated_heavy_queue": common.rel(common.S9_QUEUE_AUDIT),
            "registry": common.rel(common.REGISTRY_PATH),
            "s6s7_light_verdict": common.rel(common.S6S7_LIGHT_AUDIT),
            "s4_heavy_precedent": common.rel(common.S4_HEAVY_AUDIT),
            "s5_heavy_precedent": common.rel(common.S5_HEAVY_AUDIT),
        },
        "TOOL_INTENT_MATRIX_decision": {
            "engine_mode": "julia_canon_jax_with_pytorch_graph",
            "julia": "Graphs.jl/Z3.jl reference over finite graph/cost and witness rows",
            "jax": "NetworkX/SymPy exact graph lane with JAX vectorized N-sweep support and z3/cvc5 proof binding",
            "pytorch": "included honestly because graph rows have a genuine torch_geometric Data(edge_index) claim path for the N-sweeps",
        },
        "tool_intent": tool_intent,
        "TOOL_MANIFEST": {
            "build_three_engine_envelope": {"used": True, "reason": "load-bearing standard controller envelope construction"},
            "Graphs": julia["TOOL_MANIFEST"]["Graphs"],
            "Z3": julia["TOOL_MANIFEST"]["Z3"],
            "networkx": jax["TOOL_MANIFEST"]["networkx"],
            "sympy": jax["TOOL_MANIFEST"]["sympy"],
            "z3": jax["TOOL_MANIFEST"]["z3"],
            "cvc5": jax["TOOL_MANIFEST"]["cvc5"],
            "torch.func": pytorch["TOOL_MANIFEST"]["torch.func"],
            "torch_geometric": pytorch["TOOL_MANIFEST"]["torch_geometric"],
        },
        "TOOL_INTEGRATION_DEPTH": {
            "build_three_engine_envelope": "load_bearing",
            "Graphs": "load_bearing",
            "Z3": "load_bearing",
            "networkx": "load_bearing",
            "sympy": "load_bearing",
            "z3": "load_bearing",
            "cvc5": "load_bearing",
            "torch.func": "load_bearing",
            "torch_geometric": "load_bearing",
        },
        "positive": {
            "anchor_self": jax["positive"]["anchor_self"],
            "explicit_isomorphism_certificate": certificate,
            "heavy_rows_run": common.REGISTRY_S6S7_HEAVY_TEETH_QUOTE,
        },
        "negative": {
            "candidate_verdict_table": jax["candidate_verdicts"],
            "round2_path_far_control": jax["negative"]["round2_path_far_control"],
            "known_cosurvivors_minted": [],
        },
        "boundary": {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "scope": "S6/S7 only; exactly five queued heavy-local rows",
            "N_sweep": common.N_SWEEP,
            "resource_guard": "N<=32",
            "co_survivor_minting": "No candidate passed every heavy row; no GENUINE CO-SURVIVOR label is minted.",
        },
        "final_verdict_table": table,
        "control_rows": jax["control_rows"],
        "build_gates": gates,
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (common.SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (common.SIM_ID + '_pytorch.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            + common.rel(common.SIM_DIR / (common.SIM_ID + "_julia.jl")),
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch {common.rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed {common.rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {common.rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / ('validate_' + common.SIM_ID + '.py'))}",
        ],
    }
    envelope = build_envelope(
        sim_id=common.SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax), "pytorch": lane_record(pytorch)},
        mode="julia_canon_jax_with_pytorch_graph",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs={"z3": z3_result, "cvc5": cvc5_result, "julia_z3": julia_z3},
        divergence={
            "julia_authoritative": True,
            "observable": "final_verdict_table",
            "engine_values": {
                "julia": common.stable_hash(julia_map),
                "jax": common.stable_hash(jax_map),
                "pytorch": common.stable_hash(pytorch_map),
            },
            "max_divergence": 0.0 if verdicts_match else 1.0,
            "verdicts_match": verdicts_match,
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage=common.common_parent_lineage(),
        stability_pairs=[
            {"subtree": "final_verdict_table", "hash": common.stable_hash(table)},
            {"subtree": "explicit_isomorphism_certificate", "hash": common.stable_hash(certificate)},
        ],
        generated_at=common.now_z(),
        extra_fields=extra_fields,
    )
    envelope["all_pass"] = all_pass
    return envelope


def main() -> int:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "result": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
