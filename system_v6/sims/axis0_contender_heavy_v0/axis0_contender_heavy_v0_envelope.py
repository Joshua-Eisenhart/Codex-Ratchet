#!/usr/bin/env python3
"""Controller envelope for axis0_contender_heavy_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import axis0_contender_heavy_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JAX_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"
BUILD_CARD = common.SIM_DIR / "build_card.md"
SELF_ASSESSMENT = common.SIM_DIR / "builder_self_assessment.md"
AUDIT_VERDICT = common.SIM_DIR / "audit_verdict.md"

sys.path.insert(0, str(common.ROOT / "scripts"))
from build_three_engine_envelope import build_envelope  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


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
    return {row["candidate"]: row["final_verdict"] for row in payload.get("final_verdict_table", [])}


def build_result() -> dict[str, Any]:
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    julia = load(JULIA_RESULT)
    registry_blob = git_show(common.REGISTRY_COMMIT, common.REGISTRY_REL)
    doctrine_blob = git_show(common.DOCTRINE_COMMIT, common.DOCTRINE_REL)
    sweep_blob = git_show(common.SWEEP_COMMIT, common.SWEEP_AUDIT_REL)
    maps = {"jax": verdict_map(jax), "pytorch": verdict_map(pytorch), "julia": verdict_map(julia)}
    final_tables_match = jax["final_verdict_table"] == pytorch["final_verdict_table"] == julia["final_verdict_table"]
    no_cosurvivors = all(row["co_survivor"] is False for row in jax["final_verdict_table"])
    expected_sentence = "Axis-0 = the anchor alias class"
    boundary_flags = {
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "packet_audit_verdict_absent": not AUDIT_VERDICT.exists(),
        "file_disjoint_packet": True,
        "builder_surface_no_audit_verdict": True,
    }
    gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "three_engine_final_tables_match": final_tables_match,
        "registry_commit_bound": bool(registry_blob),
        "doctrine_commit_bound": bool(doctrine_blob),
        "sweep_audit_commit_bound": bool(sweep_blob),
        "build_card_copied": BUILD_CARD.exists() and "BUILD CARD" in BUILD_CARD.read_text(encoding="utf-8"),
        "builder_self_assessment_present": SELF_ASSESSMENT.exists() and "Builder status" in SELF_ASSESSMENT.read_text(encoding="utf-8"),
        "classification_ceiling": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [julia, jax, pytorch]
        ),
        "all_heavy_rows_excluded": all(row["final_verdict"].startswith("excluded-by") for row in jax["final_verdict_table"]),
        "no_cosurvivors_minted": no_cosurvivors,
        "family_adjudication_sentence": jax["family_adjudication_sentence"] == expected_sentence,
        "z3_cvc5_agree": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "julia_z3_agrees": julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat",
        "flip_controls_fire": jax["crossover_proofs"]["z3"]["flip_control_verdict"]
        == jax["crossover_proofs"]["cvc5"]["flip_control_verdict"]
        == julia["crossover_proofs"]["julia_z3"]["flip_control_verdict"]
        == "sat",
        "builder_audit_boundary_ok": not builder_audit_boundary_errors(boundary_flags, AUDIT_VERDICT),
    }
    all_pass = all(gates.values())
    tool_intent = {
        "claim_classes": [
            "axis0_contender_heavy_pass",
            "source_backed_33_cell_adapters",
            "row_local_smt_bindings",
            "pytorch_graph_tensor_control",
            "julia_graphs_z3_mirror",
        ],
        "engine_tool_intent": {
            "julia": {
                "Graphs": "SimpleDiGraph/add_edge! builds finite graph support for the mirror control lane",
                "Z3": "Z3.Solver/check binds row-local heavy verdict counts and SAT flip control",
            },
            "jax": {
                "networkx": "networkx.DiGraph carries committed 33-cell edge/stability and light-regression graph rows",
                "sympy": "sp.Rational builds exact finite Lyapunov/field support rows",
                "z3": "z3.Solver binds row-local heavy verdict values with SAT flip control",
                "cvc5": "cvc5.Solver independently binds row-local heavy verdict values with SAT flip control",
            },
            "pytorch": {
                "torch.func": "torch.func.vmap checks tensorized finite row transforms over the computed sign support",
                "torch_geometric": "torch_geometric.data.Data carries finite edge_index graph support for the control lane",
                "sympy": "sp.Rational provides exact rational support token matching the Python exact lane",
                "z3": "z3.Solver binds row-local heavy verdict values with SAT flip control",
                "cvc5": "cvc5.Solver independently binds row-local heavy verdict values with SAT flip control",
            },
        },
    }
    extra_fields = {
        "schema": f"{common.SIM_ID}_envelope_v1",
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "Axis-0 family adjudication heavy pass over exactly CP.3-CP.9 on the committed 33-cell carrier.",
        "allowed_claims": [
            "CP.3-CP.9 33-cell adapter variants were computed inside this packet",
            "each family has exact alias, disagreement, stability, boundary, and source-control rows",
            "no CP.3-CP.9 family passed the heavy rows as a genuine co-survivor",
            expected_sentence,
        ],
        "disallowed_claims": [
            "formal or canonical Axis-0 admission",
            "new candidates outside CP.3-CP.9",
            "THE global Axis-0 readout beyond this 33-cell heavy packet",
            "bridge, physics, or manifold promotion",
        ],
        "registry_binding": {
            "path": common.REGISTRY_REL,
            "commit": common.REGISTRY_COMMIT,
            "commit_blob_sha256": sha256_bytes(registry_blob),
            "working_tree_sha256": common.sha256_file(common.REGISTRY_PATH),
            "candidate_space_bound": [spec.cid for spec in common.HEAVY_SPECS],
        },
        "doctrine_binding": {
            "path": common.DOCTRINE_REL,
            "commit": common.DOCTRINE_COMMIT,
            "commit_blob_sha256": sha256_bytes(doctrine_blob),
        },
        "sweep_audit_binding": {
            "path": common.SWEEP_AUDIT_REL,
            "commit": common.SWEEP_COMMIT,
            "commit_blob_sha256": sha256_bytes(sweep_blob),
            "corrected_vocabulary": "open + queued-heavy before this packet",
        },
        "source_inputs_read": jax.get("source_inputs_read", {}),
        "TOOL_INTENT_MATRIX_decision": {
            "engine_mode": "julia_graphs_z3_mirror_plus_jax_exact_with_pytorch_graph",
            "julia": "Graphs/Z3 mirror of the row-local verdict table; no peer result read",
            "jax": "authoritative exact adapter/teeth computation with networkx/SymPy/z3/cvc5",
            "pytorch": "PyG finite graph and torch.func tensor check plus row-local table mirror; no peer result read",
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
            "deliberate_alias": jax["positive"]["deliberate_alias"],
            "alias_pair_table": jax["alias_pair_table"],
        },
        "negative": {
            "family_verdict_table": jax["final_verdict_table"],
            "light_regression_controls": jax["light_regression_verdicts"],
            "no_structure_controls": jax["control_verdicts"],
        },
        "boundary": {
            **boundary_flags,
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "scope": "CP.3-CP.9 only; committed 33-cell carrier only",
            "family_adjudication_sentence": expected_sentence,
        },
        "candidate_verdict_table": jax["candidate_verdicts"],
        "final_verdict_table": jax["final_verdict_table"],
        "control_verdicts": jax["control_verdicts"],
        "light_regression_verdicts": jax["light_regression_verdicts"],
        "alias_pair_table": jax["alias_pair_table"],
        "family_adjudication_sentence": expected_sentence,
        "counts": jax["counts"],
        "engine_verdict_hashes": {name: common.stable_hash(table) for name, table in maps.items()},
        "build_gates": gates,
        "builder_audit_boundary": boundary_flags,
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (common.SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (common.SIM_ID + '_pytorch.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no --project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier "
            + common.rel(common.SIM_DIR / (common.SIM_ID + "_julia.jl")),
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch --strict-source-backed --require-tool-intent {common.rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / ('validate_' + common.SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q {common.rel(common.SIM_DIR / 'tests')}",
        ],
    }
    return build_envelope(
        sim_id=common.SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax), "pytorch": lane_record(pytorch)},
        mode="julia_graphs_z3_mirror_plus_jax_exact_with_pytorch_graph",
        claim_path_tools=["Graphs", "Z3", "networkx", "sympy", "z3", "cvc5", "torch.func", "torch_geometric"],
        crossover_proofs={
            "z3": jax["crossover_proofs"]["z3"],
            "cvc5": jax["crossover_proofs"]["cvc5"],
            "julia_z3": julia["crossover_proofs"]["julia_z3"],
        },
        divergence={
            "julia_authoritative": True,
            "observable": "final_verdict_table",
            "engine_values": {
                "julia": common.stable_hash(julia["final_verdict_table"]),
                "jax": common.stable_hash(jax["final_verdict_table"]),
                "pytorch": common.stable_hash(pytorch["final_verdict_table"]),
            },
            "max_divergence": 0.0 if final_tables_match else 1.0,
            "final_tables_match": final_tables_match,
        },
        classification="scratch_diagnostic",
        promotion_allowed=False,
        formal_admission_allowed=False,
        parent_lineage={
            "axis0_registry": {"path": common.REGISTRY_REL, "commit": common.REGISTRY_COMMIT},
            "axis0_doctrine": {"path": common.DOCTRINE_REL, "commit": common.DOCTRINE_COMMIT},
            "axis0_light_sweep_audit": {"path": common.SWEEP_AUDIT_REL, "commit": common.SWEEP_COMMIT},
        },
        stability_pairs=[
            {"subtree": "final_verdict_table", "hash": common.stable_hash(jax["final_verdict_table"])},
            {"subtree": "candidate_verdict_table", "hash": common.stable_hash(jax["candidate_verdicts"])},
            {"subtree": "control_verdicts", "hash": common.stable_hash(jax["control_verdicts"])},
        ],
        generated_at=dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        extra_fields=extra_fields,
    )


def main() -> int:
    common.RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    common.write_json(RESULT_PATH, result)
    print(json.dumps({"ok": result["all_pass"], "result_path": common.rel(RESULT_PATH)}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

