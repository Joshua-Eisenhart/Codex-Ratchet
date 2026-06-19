#!/usr/bin/env python3
"""Controller envelope for axis0_cosurvivor_heavy_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import axis0_cosurvivor_heavy_v0_common as common


SOURCE_PATH = common.SIM_DIR / f"{common.SIM_ID}_envelope.py"
RESULT_PATH = common.RESULT_DIR / f"{common.SIM_ID}_envelope_results.json"
JAX_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_jax_results.json"
PYTORCH_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_pytorch_results.json"
JULIA_RESULT = common.RESULT_DIR / f"{common.SIM_ID}_julia_results.json"
BUILD_CARD = common.SIM_DIR / "build_card.md"
SELF_ASSESSMENT = common.SIM_DIR / "builder_self_assessment.md"

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
        "tool_calls": payload.get("tool_calls", []),
        "boundary": {
            "classification": payload["classification"],
            "promotion_allowed": payload["promotion_allowed"],
            "formal_admission_allowed": payload["formal_admission_allowed"],
        },
    }


def verdict_map(payload: dict[str, Any]) -> dict[str, str]:
    return {row["candidate"]: row["final_verdict"] for row in payload.get("final_verdict_table", [])}


def build_result() -> dict[str, Any]:
    jax = load(JAX_RESULT)
    pytorch = load(PYTORCH_RESULT)
    julia = load(JULIA_RESULT)
    final_tables_match = jax["final_verdict_table"] == pytorch["final_verdict_table"] == julia["final_verdict_table"]
    expected_sentence = "Axis-0 = the anchor alias class"
    no_cosurvivors = all(row["co_survivor"] is False for row in jax["final_verdict_table"])
    gates = {
        "julia_lane_pass": julia["all_pass"] is True,
        "jax_lane_pass": jax["all_pass"] is True,
        "pytorch_lane_pass": pytorch["all_pass"] is True,
        "three_engine_final_tables_match": final_tables_match,
        "supplement_commit_bound": bool(git_show(common.SUPPLEMENT_COMMIT, common.AMENDMENT_REL)),
        "accepted_light_commit_bound": bool(git_show(common.LIGHT_ACCEPTED_COMMIT, common.rel(common.LIGHT_AUDIT))),
        "build_card_copied": BUILD_CARD.exists() and "axis0_cosurvivor_heavy_v0" in BUILD_CARD.read_text(encoding="utf-8"),
        "builder_self_assessment_present": SELF_ASSESSMENT.exists() and "Builder status" in SELF_ASSESSMENT.read_text(encoding="utf-8"),
        "classification_ceiling": all(
            payload["classification"] == "scratch_diagnostic"
            and payload["promotion_allowed"] is False
            and payload["formal_admission_allowed"] is False
            for payload in [julia, jax, pytorch]
        ),
        "all_heavy_rows_have_required_teeth": all(
            "cell_level_disagreement_table" in row
            and "stability_class_comparison" in row
            and "multi_step_stability_extension" in row
            and "distinction_boundary_check" in row
            for row in jax["candidate_verdict_table"]
        ),
        "no_cosurvivors_minted": no_cosurvivors,
        "family_adjudication_sentence": jax["family_adjudication_sentence"] == expected_sentence,
        "z3_cvc5_agree": jax["crossover_proofs"]["z3"]["verdict"] == jax["crossover_proofs"]["cvc5"]["verdict"] == "unsat",
        "julia_z3_agrees": julia["crossover_proofs"]["julia_z3"]["verdict"] == "unsat",
        "flip_controls_fire": jax["crossover_proofs"]["z3"]["flip_control_verdict"]
        == jax["crossover_proofs"]["cvc5"]["flip_control_verdict"]
        == julia["crossover_proofs"]["julia_z3"]["flip_control_verdict"]
        == "sat",
    }
    all_pass = all(gates.values())
    tool_intent = {
        "claim_classes": [
            "axis0_cp11_cp14_heavy_teeth",
            "supplement_pinned_light_cosurvivor_followon",
            "finite_33_cell_generator_stability",
            "multi_step_generator_walk_stability",
            "row_local_smt_bindings",
        ],
        "engine_tool_intent": {
            "julia": {
                "Graphs": "SimpleDiGraph rebuilds the finite committed generator graph for the Julia mirror lane",
                "Z3": "Z3.Solver/check binds CP.11/CP.14 heavy verdict counts and SAT flip control",
            },
            "jax": {
                "networkx": "DiGraph carries committed generator adjacency and multi-step generator-walk profiles",
                "sympy": "Rational support binds finite 33-cell carrier scale and exact anchor controls",
                "z3": "Solver binds CP.11/CP.14 heavy-tooth counts with SAT flip control",
                "cvc5": "independent Solver binds the same heavy-tooth counts with SAT flip control",
            },
            "pytorch": {
                "torch.func": "vmap checks finite tensor transform over the CP.11/CP.14 heavy count support",
                "torch_geometric": "Data edge_index carries a finite graph support probe for the control lane",
                "sympy": "Rational support token matches the finite 33-cell carrier scale",
                "z3": "Solver binds CP.11/CP.14 heavy-tooth counts with SAT flip control",
                "cvc5": "independent Solver binds the same heavy-tooth counts with SAT flip control",
            },
        },
    }
    extra_fields = {
        "schema": f"{common.SIM_ID}_envelope_v1",
        "source_path": common.rel(SOURCE_PATH),
        "source_sha256": common.sha256_file(SOURCE_PATH),
        "result_path": common.rel(RESULT_PATH),
        "all_pass": all_pass,
        "claim": "Axis-0 CP.11/CP.14 heavy teeth and family adjudication on the committed 33-cell carrier.",
        "allowed_claims": jax["allowed_claims"],
        "disallowed_claims": jax["disallowed_claims"],
        "authority_binding": {
            **jax["authority_binding"],
            "accepted_light_commit_blob_sha256": sha256_bytes(git_show(common.LIGHT_ACCEPTED_COMMIT, common.rel(common.LIGHT_AUDIT))),
        },
        "anchor_binding": jax["anchor_binding"],
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
        "candidate_verdict_table": jax["candidate_verdict_table"],
        "final_verdict_table": jax["final_verdict_table"],
        "control_verdicts": jax["control_verdicts"],
        "alias_pair_table": jax["alias_pair_table"],
        "family_adjudication_sentence": jax["family_adjudication_sentence"],
        "fork_adjudication": jax["fork_adjudication"],
        "counts": jax["counts"],
        "engine_verdict_maps": {"jax": verdict_map(jax), "pytorch": verdict_map(pytorch), "julia": verdict_map(julia)},
        "build_gates": gates,
        "validator_expected_commands": [
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (common.SIM_ID + '_jax.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / (common.SIM_ID + '_pytorch.py'))}",
            "JULIA_LOAD_PATH=@:@stdlib /opt/homebrew/bin/julia --startup-file=no "
            f"--project=/Users/joshuaeisenhart/Codex-Ratchet/system_v5/julia_carrier {common.rel(common.SIM_DIR / (common.SIM_ID + '_julia.jl'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(SOURCE_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 scripts/validate_three_engine_sim_result.py --require-pytorch {common.rel(RESULT_PATH)}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 {common.rel(common.SIM_DIR / ('validate_' + common.SIM_ID + '.py'))}",
            f"/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3 -m pytest -q {common.rel(common.SIM_DIR / 'tests')}",
        ],
    }
    return build_envelope(
        sim_id=common.SIM_ID,
        lanes={"julia": lane_record(julia), "jax": lane_record(jax), "pytorch": lane_record(pytorch)},
        mode="julia_graphs_z3_mirror_plus_jax_exact_with_pytorch_graph_control",
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
            "amendment_supplement_1": f"{common.SUPPLEMENT_COMMIT}:{common.AMENDMENT_REL}",
            "accepted_light_packet": f"{common.LIGHT_ACCEPTED_COMMIT}:{common.rel(common.LIGHT_AUDIT)}",
            "committed_carrier": common.rel(common.ANCHOR_ENVELOPE),
            "heavy_format_source": "c27d3dd39:system_v6/sims/axis0_contender_heavy_v0",
        },
        stability_pairs=[
            {"subtree": "final_verdict_table", "hash": common.stable_hash(jax["final_verdict_table"])},
            {"subtree": "candidate_verdict_table", "hash": common.stable_hash(jax["candidate_verdict_table"])},
            {"subtree": "fork_adjudication", "hash": common.stable_hash(jax["fork_adjudication"])},
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
