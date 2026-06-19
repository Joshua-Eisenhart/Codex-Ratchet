#!/usr/bin/env python3
"""Packet-local builder validator for geo_union_rule_k_leaves_v0."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_union_rule_k_leaves_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_PATH = SIM_DIR / "results" / f"{SIM_ID}_envelope_results.json"

sys.path.insert(0, str(ROOT))
from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    envelope = load(RESULT_PATH)
    receipts = envelope["receipts"]
    controls = envelope["controls"]
    proofs = envelope["crossover_proofs"]
    summary = envelope["summary"]["anchor_values"]

    require(envelope["schema_version"] == "three_engine_sim_result_v1", "schema drift")
    require(envelope["all_pass"] is True, "envelope all_pass false")
    require(envelope["classification"] == "scratch_diagnostic", "classification drift")
    require(envelope["promotion_allowed"] is False, "promotion_allowed drift")
    require(envelope["formal_admission_allowed"] is False, "formal_admission_allowed drift")
    require(envelope["builder_scope_boundary"]["no_audit_verdict_written"] is True, "audit verdict boundary missing")
    for error in builder_audit_boundary_errors(envelope, SIM_DIR / "audit_verdict.md"):
        require(False, error)

    require(envelope["engine_contract"]["mode"] == "julia_symbolics_plus_python_sympy_smt_diagnostic", "engine mode drift")
    require(envelope["engine_contract"]["lanes"] == ["julia", "jax"], "standard validator lane shape drift")
    require("Python SymPy/z3/cvc5 sidecar" in envelope["engine_contract"]["lane_note"], "python sidecar lane note missing")
    require(envelope["engines"]["julia"]["reads_peer_result"] is False, "Julia peer-result read drift")
    require(envelope["engines"]["jax"]["reads_peer_result"] is False, "Python peer-result read drift")
    require(envelope["engines"]["julia"]["source_hash_current"] is True, "Julia source hash stale")
    require(envelope["engines"]["jax"]["source_hash_current"] is True, "Python source hash stale")

    k1 = receipts["K1_general_k_leaf_band_limit_rule"]
    require(k1["pass"] is True, "general k-leaf rule failed")
    require(k1["k_leaf_weight_formula"] == "w_i = sin(2*eta_i) / sum_j sin(2*eta_j)", "weight formula drift")
    require(k1["normalization_defect_k3_symbolic"] == "0", "normalization defect drift")
    require(k1["grouping_left_defects_symbolic"] == ["0", "0", "0"], "left grouping defects drift")
    require(k1["grouping_right_defects_symbolic"] == ["0", "0", "0"], "right grouping defects drift")

    k2 = receipts["K2_parent_two_leaf_byte_exact_reduction"]
    require(k2["pass"] is True, "k=2 parent reduction failed")
    require(k2["byte_exact_under_stable_json"] is True, "k=2 parent row not byte-exact")
    require(k2["computed_row_sha256"] == k2["parent_row_sha256"], "k=2 row hash mismatch")
    require(k2["computed_row"]["union_weight_eta1_ratio_form"] == "sqrt(3)/(sqrt(3)+2)", "parent eta1 ratio drift")
    require(k2["computed_row"]["union_weight_eta2_ratio_form"] == "2/(sqrt(3)+2)", "parent eta2 ratio drift")

    k3k4 = receipts["K3_concrete_k3_k4_committed_shell_weights"]
    require(k3k4["pass"] is True, "k3/k4 exact row failed")
    require(k3k4["k3_shells"] == ["pi/12", "pi/6", "pi/4"], "k3 shell set drift")
    require(k3k4["k4_shells"] == ["pi/12", "pi/6", "pi/4", "pi/3"], "k4 shell set drift")
    require(k3k4["k3_weight_sum_defect"] == "0", "k3 weight sum defect drift")
    require(k3k4["k4_weight_sum_defect"] == "0", "k4 weight sum defect drift")
    require(k3k4["k3_weights"][2]["eta"] == "pi/4", "k3 pi/4 row missing")
    require(summary["k_leaf_rule"] == "w_i=sin(2*eta_i)/sum_j sin(2*eta_j)", "summary rule drift")

    assoc = receipts["K4_associativity_order_row_k3"]
    require(assoc["pass"] is True, "associativity row failed")
    require(assoc["agreement_or_gap"] == "agreement_when_iterated_union_carries_summed_group_mass", "associativity finding drift")
    require(assoc["left_minus_direct_defects"] == ["0", "0", "0"], "left route defect drift")
    require(assoc["right_minus_direct_defects"] == ["0", "0", "0"], "right route defect drift")

    control = receipts["K5_degenerate_boundary_and_equal_weight_controls"]
    require(control["pass"] is True, "control row failed")
    require(control["repeated_leaf_status"].startswith("collapse repeated eta"), "repeated leaf collapse missing")
    require(control["duplicate_double_count_cos_2eta_defect"] != "0", "duplicate control did not fail")
    require(control["boundary_weights"][0] == {"eta": "0", "weight": "0"}, "boundary zero leaf did not vanish")
    require(control["equal_weights_control_defect_equal_minus_correct"] != "0", "equal weight control did not fail")
    require(controls["equal_weights"]["defect"] == control["equal_weights_control_defect_equal_minus_correct"], "equal control summary mismatch")

    mortality = receipts["K6_mortality_boundary_free_measure"]
    require(mortality["pass"] is True, "mortality boundary failed")
    require(mortality["finite_k_naive_conditioning_denominator"].startswith("0 for every finite k"), "finite-k denominator boundary drift")
    require(mortality["definable_again_k"] == "no_finite_k", "finite k incorrectly made definable")
    require("continuum_all_eta" in mortality["definable_again_boundary"], "continuum boundary missing")
    require(mortality["all_shell_constant_recovery"] == "1", "FREE constant recovery drift")
    require(mortality["all_shell_cos_2eta_unconditioned"] == "0", "FREE cos recovery drift")
    require(mortality["all_shell_cos2_2eta_unconditioned"] == "1/3", "FREE cos2 recovery drift")

    for key in ["z3", "cvc5", "julia_z3"]:
        row = proofs[key]
        require(row["ran"] is True, f"{key} did not run")
        require(row["verdict"] == "unsat", f"{key} positive verdict drift")
        require(row["erase_flip_unsat_to_sat"] is True, f"{key} erased flip missing")
        require(row["asserted_precomputed_boolean"] is False, f"{key} precomputed boolean risk")
        require(row["equal_weights_fail"] is True, f"{key} equal-weight negative missing")
        require(row["boundary_pass"] is True, f"{key} boundary case missing")

    claim_tools = set(envelope["claim_path_tools"])
    receipt_tools = {call["tool"] for call in envelope["tool_calls"] if call.get("tool") in claim_tools}
    require(receipt_tools == claim_tools, "claim_path_tools not one-to-one with aggregate tool_calls")
    require(envelope["build_gates"]["one_to_one_claim_tool_calls"] is True, "one-to-one gate false")
    require(envelope["result_hashes"]["computed_k2_row_sha256"] == envelope["result_hashes"]["parent_r3_row_sha256"], "result hash k2 mismatch")

    print(json.dumps({"ok": True, "result_json": str(RESULT_PATH.relative_to(ROOT)), "mode": envelope["engine_contract"]["mode"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
