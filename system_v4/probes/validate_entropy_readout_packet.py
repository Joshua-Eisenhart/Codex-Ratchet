#!/usr/bin/env python3
"""
validate_entropy_readout_packet.py
==================================

Mechanical validator for the executable entropy-readout ladder.

This packet sits above the pre-entropy bridge packet and below any later
loop algebra:
  - metric hygiene negatives
  - bridge-family entropy-spectrum separation
  - explicit current bridge-candidate handoff
  - same-family history-to-signed-readout handoff
  - compression / directionality framing
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SIM_RESULTS = ROOT / "a2_state" / "sim_results"
OUTPUT_PATH = SIM_RESULTS / "entropy_readout_packet_validation.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(ok: bool, name: str, detail: dict) -> dict:
    return {"name": name, "pass": bool(ok), "detail": detail}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    battery = load_json(SIM_RESULTS / "entropy_form_negative_battery_results.json")
    spectrum = load_json(SIM_RESULTS / "axis0_full_spectrum_results.json")
    fep = load_json(SIM_RESULTS / "axis0_fep_compression_results.json")
    bridge_search = load_json(SIM_RESULTS / "axis0_bridge_search_results.json")
    mispair = load_json(SIM_RESULTS / "history_mispair_counterfeit_results.json")
    carrier_selection = load_json(SIM_RESULTS / "carrier_selection_packet_validation.json")
    pre_entropy = load_json(SIM_RESULTS / "pre_entropy_packet_validation.json")
    c1_bridge_object = load_json(SIM_RESULTS / "c1_bridge_object_packet_validation.json")

    b = battery["results"]
    rec = battery["recommendation"]
    families = spectrum["families"]
    summary = spectrum["summary"]
    fsum = fep["summary"]
    mean_mi = bridge_search["mean_mi_by_candidate"]
    mean_ic = bridge_search["mean_ic_by_candidate"]
    ranking = bridge_search["ranking"]
    mispair_summary = mispair["summary"]
    pre_entropy_law = pre_entropy["law_summary"]
    signed_bridge_handoff = carrier_selection["signed_bridge_candidate_handoff"]

    local_only = families["L|R_local_only"]
    coupled_control = families["L|R_coupled_control"]
    xi_shell = families["Xi_shell"]
    xi_hist_outer = families["Xi_hist_outer"]
    xi_hist_cycle = families["Xi_hist_cycle"]
    xi_lr_control = families["Xi_LR_control"]

    gates = [
        gate(
            b["spectral_pair_total"] > 1000
            and b["linear_disagreements"] == 0
            and b["renyi2_disagreements"] == 0
            and b["tsallis2_disagreements"] == 0
            and b["purity_disagreements"] == 0
            and b["rel_to_maxmix_affine_err"] < 1e-12
            and b["renyi2_proxy_ok"],
            "E1_qubit_spectral_family_is_order_equivalent",
            {
                "spectral_pair_total": b["spectral_pair_total"],
                "linear_disagreements": b["linear_disagreements"],
                "renyi2_disagreements": b["renyi2_disagreements"],
                "tsallis2_disagreements": b["tsallis2_disagreements"],
                "purity_disagreements": b["purity_disagreements"],
                "rel_to_maxmix_affine_err": b["rel_to_maxmix_affine_err"],
                "renyi2_proxy_ok": b["renyi2_proxy_ok"],
            },
        ),
        gate(
            b["shannon_basis_failures"] >= 24
            and b["shannon_basis_shift_avg"] > 0.1,
            "E2_shannon_diagonal_is_not_geometry_safe",
            {
                "shannon_basis_failures": b["shannon_basis_failures"],
                "shannon_basis_shift_avg": b["shannon_basis_shift_avg"],
                "not_geometry_safe": rec["not_geometry_safe"],
            },
        ),
        gate(
            b["conditional_proxy_max_error"] < 1e-12
            and b["conditional_proxy_max_mutual"] < 1e-12
            and b["fi_vn_delta"] == 0.0
            and b["fi_linear_delta"] == 0.0
            and b["fi_renyi2_delta"] == 0.0
            and b["fi_state_distance"] > 0.1
            and b["fi_z_shift"] > 0.1,
            "E3_product_proxy_and_pure_fi_negatives_hold",
            {
                "conditional_proxy_max_error": b["conditional_proxy_max_error"],
                "conditional_proxy_max_mutual": b["conditional_proxy_max_mutual"],
                "fi_vn_delta": b["fi_vn_delta"],
                "fi_linear_delta": b["fi_linear_delta"],
                "fi_renyi2_delta": b["fi_renyi2_delta"],
                "fi_state_distance": b["fi_state_distance"],
                "fi_z_shift": b["fi_z_shift"],
            },
        ),
        gate(
            set(summary["ranked_keep"]) == {"Xi_shell", "Xi_hist_outer", "Xi_hist_cycle"}
            and set(summary["ranked_kill"]) == {"L|R_local_only", "Xi_LR_control"}
            and set(summary["ranked_control"]) == {"L|R_coupled_control"},
            "E4_bridge_family_ranking_is_separated",
            {
                "ranked_keep": summary["ranked_keep"],
                "ranked_kill": summary["ranked_kill"],
                "ranked_control": summary["ranked_control"],
            },
        ),
        gate(
            local_only["verdict"]["trivial"]
            and xi_lr_control["verdict"]["trivial"]
            and coupled_control["verdict"]["control_only"]
            and local_only["base_metrics"]["I_AB"]["max"] < 1e-12
            and xi_lr_control["base_metrics"]["I_AB"]["max"] < 1e-12,
            "E5_raw_and_lr_controls_stay_entropy_trivial",
            {
                "local_only_I_AB_max": local_only["base_metrics"]["I_AB"]["max"],
                "xi_lr_control_I_AB_max": xi_lr_control["base_metrics"]["I_AB"]["max"],
                "local_only_trivial": local_only["verdict"]["trivial"],
                "xi_lr_control_trivial": xi_lr_control["verdict"]["trivial"],
                "coupled_control_only": coupled_control["verdict"]["control_only"],
            },
        ),
        gate(
            xi_shell["base_metrics"]["I_AB"]["mean"] > 0.25
            and xi_shell["base_metrics"]["I_c_A_to_B"]["mean"] > 0.1
            and xi_shell["base_metrics"]["S_A_given_B"]["mean"] < -0.1
            and xi_shell["verdict"]["eta_sensitive"],
            "E6_shell_bridge_supports_signed_entropy_readout",
            {
                "I_AB_mean": xi_shell["base_metrics"]["I_AB"]["mean"],
                "I_c_mean": xi_shell["base_metrics"]["I_c_A_to_B"]["mean"],
                "S_A_given_B_mean": xi_shell["base_metrics"]["S_A_given_B"]["mean"],
                "eta_sensitive": xi_shell["verdict"]["eta_sensitive"],
            },
        ),
        gate(
            xi_hist_outer["base_metrics"]["I_AB"]["mean"] > 0.001
            and xi_hist_cycle["base_metrics"]["I_AB"]["mean"] > 0.001
            and xi_hist_outer["verdict"]["eta_sensitive"]
            and xi_hist_cycle["verdict"]["eta_sensitive"]
            and not xi_hist_outer["verdict"]["trivial"]
            and not xi_hist_cycle["verdict"]["trivial"],
            "E7_history_bridges_are_nontrivial_and_torus_sensitive",
            {
                "hist_outer_I_AB_mean": xi_hist_outer["base_metrics"]["I_AB"]["mean"],
                "hist_cycle_I_AB_mean": xi_hist_cycle["base_metrics"]["I_AB"]["mean"],
                "hist_outer_eta_sensitive": xi_hist_outer["verdict"]["eta_sensitive"],
                "hist_cycle_eta_sensitive": xi_hist_cycle["verdict"]["eta_sensitive"],
            },
        ),
        gate(
            xi_hist_outer["base_metrics"]["I_AB"]["mean"] > 0.001
            and xi_hist_outer["base_metrics"]["I_c_A_to_B"]["mean"] < -0.1
            and xi_hist_outer["base_metrics"]["S_A_given_B"]["mean"] > 0.1
            and xi_hist_cycle["base_metrics"]["I_AB"]["mean"] > 0.001
            and xi_hist_cycle["base_metrics"]["I_c_A_to_B"]["mean"] < -0.1
            and xi_hist_cycle["base_metrics"]["S_A_given_B"]["mean"] > 0.1
            and xi_lr_control["base_metrics"]["I_AB"]["max"] < 1e-12,
            "E8_history_family_handoff_supports_signed_readout_on_same_objects",
            {
                "hist_outer_I_AB_mean": xi_hist_outer["base_metrics"]["I_AB"]["mean"],
                "hist_outer_I_c_mean": xi_hist_outer["base_metrics"]["I_c_A_to_B"]["mean"],
                "hist_outer_S_A_given_B_mean": xi_hist_outer["base_metrics"]["S_A_given_B"]["mean"],
                "hist_cycle_I_AB_mean": xi_hist_cycle["base_metrics"]["I_AB"]["mean"],
                "hist_cycle_I_c_mean": xi_hist_cycle["base_metrics"]["I_c_A_to_B"]["mean"],
                "hist_cycle_S_A_given_B_mean": xi_hist_cycle["base_metrics"]["S_A_given_B"]["mean"],
                "lr_control_I_AB_max": xi_lr_control["base_metrics"]["I_AB"]["max"],
            },
        ),
        gate(
            fsum["overall"] in {"STRONG COMPRESSION-FROM-FUTURE", "PARTIAL COMPRESSION-FROM-FUTURE"}
            and fsum["compression_verdict"] >= 3
            and fsum["t1_keep"] == fsum["total"]
            and fsum["t3_keep"] >= 4
            and fsum["t4_keep"] >= 4
            and fsum["t2_keep"] >= 2,
            "E9_fep_framing_shows_nonclassical_directionality",
            {
                "overall": fsum["overall"],
                "compression_verdict": fsum["compression_verdict"],
                "total": fsum["total"],
                "t1_keep": fsum["t1_keep"],
                "t2_keep": fsum["t2_keep"],
                "t3_keep": fsum["t3_keep"],
                "t4_keep": fsum["t4_keep"],
            },
        ),
        gate(
            bridge_search["winner"] == "Xi_chiral_entangle"
            and c1_bridge_object["passed_gates"] == c1_bridge_object["total_gates"]
            and c1_bridge_object["score"] == 1.0
            and signed_bridge_handoff["candidate"] == "Xi_chiral_entangle"
            and signed_bridge_handoff["status"] == "provisional_handoff_ready"
            and signed_bridge_handoff["placement_contract"] == "downstream_axis_internal_bridge_candidate_only"
            and signed_bridge_handoff["owner_dependency"] == "must_bind_under_xi_hist_signed_law"
            and signed_bridge_handoff["forbidden_reclassification"] == "not_owner_derived_not_final_owner_xi"
            and signed_bridge_handoff["consumer_status"] == "allowed_for_entropy_readout_not_final_owner_xi"
            and ranking[0] == "Xi_chiral_entangle"
            and mean_mi["Xi_chiral_entangle"] > mean_mi["Xi_chiral_hist_entangle"]
            and mean_mi["Xi_chiral_entangle"] > 0.5,
            "E10_current_bridge_candidate_is_explicit_and_provisional",
            {
                "current_bridge_candidate": bridge_search["winner"],
                "c1_bridge_object_passed_gates": c1_bridge_object["passed_gates"],
                "c1_bridge_object_total_gates": c1_bridge_object["total_gates"],
                "c1_bridge_object_score": c1_bridge_object["score"],
                "signed_bridge_handoff_candidate": signed_bridge_handoff["candidate"],
                "signed_bridge_handoff_status": signed_bridge_handoff["status"],
                "signed_bridge_handoff_placement_contract": signed_bridge_handoff["placement_contract"],
                "signed_bridge_handoff_owner_dependency": signed_bridge_handoff["owner_dependency"],
                "signed_bridge_handoff_forbidden_reclassification": signed_bridge_handoff["forbidden_reclassification"],
                "signed_bridge_handoff_consumer_status": signed_bridge_handoff["consumer_status"],
                "current_bridge_candidate_mean_mi": mean_mi["Xi_chiral_entangle"],
                "current_bridge_candidate_mean_i_c": mean_ic["Xi_chiral_entangle"],
                "runner_up": "Xi_chiral_hist_entangle",
                "runner_up_mean_mi": mean_mi["Xi_chiral_hist_entangle"],
                "runner_up_mean_i_c": mean_ic["Xi_chiral_hist_entangle"],
                "status": "admitted_executable_candidate_not_final_owner_law",
            },
        ),
        gate(
            bridge_search["winner"] == "Xi_chiral_entangle"
            and mispair["bridge_candidate"] == "Xi_chiral_entangle"
            and mispair_summary["mean_counterfeit_I_AB"] > mispair_summary["mean_live_I_AB"]
            and mispair_summary["mean_live_I_c"] > mispair_summary["mean_counterfeit_I_c"]
            and mispair_summary["mean_I_c_gap"] > 0.05
            and mispair_summary["live_beats_counterfeit_on_I_c_count"] >= mispair_summary["counterfeit_beats_live_on_I_AB_count"],
            "E11_xi_chiral_entangle_signed_honesty_beats_mispair_counterfeit",
            {
                "bridge_candidate": mispair["bridge_candidate"],
                "mean_live_I_AB": mispair_summary["mean_live_I_AB"],
                "mean_counterfeit_I_AB": mispair_summary["mean_counterfeit_I_AB"],
                "mean_live_I_c": mispair_summary["mean_live_I_c"],
                "mean_counterfeit_I_c": mispair_summary["mean_counterfeit_I_c"],
                "mean_I_c_gap": mispair_summary["mean_I_c_gap"],
                "counterfeit_beats_live_on_I_AB_count": mispair_summary["counterfeit_beats_live_on_I_AB_count"],
                "live_beats_counterfeit_on_I_c_count": mispair_summary["live_beats_counterfeit_on_I_c_count"],
            },
        ),
        gate(
            pre_entropy_law["strict_bakeoff_owner_object_present"]
            and pre_entropy_law["late_anchor_equivalence"]["placement_8_23_equals_16_31_count"] == pre_entropy_law["total_rows"]
            and pre_entropy_law["late_anchor_equivalence"]["placement_8_23_equals_prefix_8_15_on_ic_count"] == pre_entropy_law["total_rows"]
            and pre_entropy_law["clifford_local_short_width_stress"]["placement_8_23_beats_0_3_on_ic_off_clifford_count"] == 4
            and pre_entropy_law["clifford_local_short_width_stress"]["short_width_0_3_beats_8_23_on_ic_clifford_count"] == 2
            and xi_hist_outer["verdict"]["eta_sensitive"]
            and xi_hist_cycle["verdict"]["eta_sensitive"]
            and xi_hist_outer["base_metrics"]["I_c_A_to_B"]["mean"] < -0.1
            and xi_hist_cycle["base_metrics"]["I_c_A_to_B"]["mean"] < -0.1
            and xi_hist_outer["base_metrics"]["S_A_given_B"]["mean"] > 0.1
            and xi_hist_cycle["base_metrics"]["S_A_given_B"]["mean"] > 0.1,
            "E12_xi_hist_law_summary_binds_pre_entropy_to_readout",
            {
                "law_summary_name": pre_entropy_law["name"],
                "strict_bakeoff_owner_object_present": pre_entropy_law["strict_bakeoff_owner_object_present"],
                "late_anchor_equivalence": pre_entropy_law["late_anchor_equivalence"],
                "clifford_local_short_width_stress": pre_entropy_law["clifford_local_short_width_stress"],
                "hist_outer_I_c_mean": xi_hist_outer["base_metrics"]["I_c_A_to_B"]["mean"],
                "hist_cycle_I_c_mean": xi_hist_cycle["base_metrics"]["I_c_A_to_B"]["mean"],
                "hist_outer_S_A_given_B_mean": xi_hist_outer["base_metrics"]["S_A_given_B"]["mean"],
                "hist_cycle_S_A_given_B_mean": xi_hist_cycle["base_metrics"]["S_A_given_B"]["mean"],
            },
        ),
    ]

    passed = sum(1 for item in gates if item["pass"])
    payload = {
        "name": "entropy_readout_packet_validation",
        "timestamp": datetime.now(UTC).isoformat(),
        "passed_gates": passed,
        "total_gates": len(gates),
        "score": passed / len(gates) if gates else 0.0,
        "gates": gates,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if args.pretty:
        print("=" * 72)
        print("ENTROPY READOUT PACKET VALIDATION")
        print("=" * 72)
        for item in gates:
            status = "PASS" if item["pass"] else "FAIL"
            print(f"{status:>4}  {item['name']}")
        print(f"\npassed_gates: {passed}/{len(gates)}")
        print(f"score: {payload['score']:.6f}")
        print(f"validation_results: {OUTPUT_PATH}")
    else:
        print(json.dumps(payload, indent=2))

    return 0 if passed == len(gates) else 1


if __name__ == "__main__":
    raise SystemExit(main())
