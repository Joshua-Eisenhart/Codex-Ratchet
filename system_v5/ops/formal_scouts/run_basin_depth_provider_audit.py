#!/usr/bin/env python3
"""Run bounded Grok/Gemini audits for the basin-depth guard repair.

Provider output is proposal/audit only.  The written receipt deliberately uses
the provider proposal schema and cannot promote a formal-scout result.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import time
import urllib.error
import urllib.request
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parent
OUT_DIR = ROOT / "provider_receipts"

PROMPT = """Read-only audit for Codex Ratchet formal scouts.

Current repaired files:
- system_v5/ops/formal_scouts/sim_manifold_dependency_basin_depth_guard_probe.py
- system_v5/ops/formal_scouts/results/manifold_dependency_basin_depth_guard_probe_results.json
- system_v5/ops/formal_scouts/sim_operational_manifold_assembly_true_perturbation_depth_probe.py
- system_v5/ops/formal_scouts/results/operational_manifold_assembly_true_perturbation_depth_probe_results.json
- system_v5/ops/formal_scouts/sim_seven_control_source_execution_true_perturbation_depth_probe.py
- system_v5/ops/formal_scouts/results/seven_control_source_execution_true_perturbation_depth_probe_results.json
- system_v5/ops/formal_scouts/sim_active_policy_online_vmp_margin_closure_probe.py
- system_v5/ops/formal_scouts/results/active_policy_online_vmp_margin_closure_probe_results.json
- system_v5/ops/formal_scouts/sim_attractor_basin_success_criteria_receipt_classifier_probe.py
- system_v5/ops/formal_scouts/results/attractor_basin_success_criteria_receipt_classifier_probe_results.json
- system_v5/ops/formal_scouts/sim_stage_record_downstream_carrier_consumption_closure_probe.py
- system_v5/ops/formal_scouts/results/stage_record_downstream_carrier_consumption_closure_probe_results.json
- system_v5/ops/formal_scouts/sim_source_native_multicarrier_subdense_environment_contraction_probe.py
- system_v5/ops/formal_scouts/results/source_native_multicarrier_subdense_environment_contraction_probe_results.json
- system_v5/ops/formal_scouts/sim_axis0_plural_candidate_multicarrier_drive_controls_probe.py
- system_v5/ops/formal_scouts/results/axis0_plural_candidate_multicarrier_drive_controls_probe_results.json
- system_v5/ops/formal_scouts/sim_axis0_fep_gradient_stage_local_adapter_closure_probe.py
- system_v5/ops/formal_scouts/results/axis0_fep_gradient_stage_local_adapter_closure_probe_results.json
- system_v5/ops/formal_scouts/sim_path_entropy_schedule_confound_falsifier_probe.py
- system_v5/ops/formal_scouts/results/path_entropy_schedule_confound_falsifier_probe_results.json
- system_v5/ops/formal_scouts/sim_path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe.py
- system_v5/ops/formal_scouts/results/path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe_results.json
- system_v5/ops/formal_scouts/sim_axis0_path_entropy_branch_closure_probe.py
- system_v5/ops/formal_scouts/results/axis0_path_entropy_branch_closure_probe_results.json
- system_v5/ops/formal_scouts/sim_axis0_holographic_boundary_branch_closure_probe.py
- system_v5/ops/formal_scouts/results/axis0_holographic_boundary_branch_closure_probe_results.json
- system_v5/ops/formal_scouts/sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py
- system_v5/ops/formal_scouts/results/mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json
- system_v5/ops/formal_scouts/sim_integrated_constraint_manifold_suite_fresh_rerun_probe.py
- system_v5/ops/formal_scouts/results/integrated_constraint_manifold_suite_fresh_rerun_probe_results.json

Indexed local receipt facts; do not treat this provider prompt as fresh validation:
- basin-depth guard all_pass=True
- active_inference_policy_window routes open_basin_boundary because nominal top-two EFE margin is 0.0017228540 < floor 0.01
- source-native online VMP clears its nominal policy margin at 0.0217303875 >= floor 0.01
- online VMP does NOT repair active_policy into manifold-depth evidence: no-manifold online VMP control has top score 4.0290859867 versus nominal 4.0317442770 and top-two margin 0.0097097121 < floor 0.01
- online-VMP closure validation is now route-validity based: all_pass means the branch was routed from evaluated controls, not that the blocked conclusion itself is hardcoded as the pass criterion
- guard-pass rows are science_method_stage_record_fields, operational_manifold_assembly, seven_control_source_execution
- operational_manifold_assembly now consumes a bounded perturbed-initial-state receipt: 2 seeds x 2 epsilons, min ordering gap 0.2673063017, min weakest-layer diff 0.0102316214, min entropy span 0.0936725730
- seven_control_source_execution now consumes a bounded perturbed-stage-entry receipt: 2 seeds x 3 epsilons x 7 controls = 42 rows, min dynamic gap 1.8402485123, min full-signature gap 4.8359605651
- attractor classifier labels the guard receipt candidate_basin, not deep_basin
- attractor classifier labels operational_manifold_assembly_true_perturbation_depth as candidate_basin, not deep_basin
- attractor classifier labels seven_control_source_execution_true_perturbation_depth as candidate_basin, not deep_basin
- attractor classifier labels active_policy_online_vmp_margin_closure as anti_basin for the claim that online-VMP nominal margin repairs active-policy manifold-depth evidence
- stage-record scout no longer carries the stale missing source_native_multicarrier_common_boundary_observable_bridge_probe_results.json as a live consumed receipt
- stage_record_downstream_carrier_consumption_closure all_pass=True and verifies current subdense MPS/PEPS/PEPS3D rows consume 128 stage records and 128 unique model-after hashes per carrier
- source_native_multicarrier_subdense_environment_contraction all_pass=True and is intentionally pre-guard: it consumes raw macro Axis0 router candidates as a multicarrier control surface, records pre_guard_axis0_boundary, guard_receipt_consumed=false, and post_guard_admission_claim_allowed=false
- axis0_plural_candidate_multicarrier_drive_controls all_pass=True and remains the downstream guard that consumes the subdense receipt, classifies raw Axis0 candidates, admits fep_gradient_polarity/correlation_diversity_derivative/retrocausal_many_futures_policy_scoring, and blocks path_entropy/HBI
- stage-record scout no longer reports fep_gradient_polarity as blocked_stage_local_adapter_missing; it delegates to macro_sim_axis0_plural_stage_candidate_router with axis0_fep_gradient_stage_local_adapter_closure as guard
- axis0_fep_gradient_stage_local_adapter_closure all_pass=True, independently recomputes fep_gradient_polarity from EngineCore EFE rows, matches the router vector, separates no-manifold and shuffled-order controls, rejects a same-multiset/sign-count broken-adjacency proxy, and verifies downstream plural Axis0 carrier controls consume/admit the candidate while retaining the scalar-weighted-actuator blocker
- path_entropy remains finite at the macro router but is blocked downstream: axis0 guard admits fep_gradient_polarity, correlation_diversity_derivative, and retrocausal_many_futures_policy_scoring; it blocks path_entropy and holographic_boundary_interior_reconstruction
- path_entropy_schedule_confound_falsifier all_pass=True: same ordered-token schedule gives path_entropy_delta_same_schedule=0.0 while FEP-gradient, Bloch-path, and observation-distribution witnesses move; decyclicized same-inventory order revives candidate status only as a surrogate sensitivity control
- path_entropy_proxy_vs_deeper_invariant_pair_falsifier all_pass=True with discrimination score 1.000: path_entropy is a rolling-window categorical proxy, deeper invariant is only candidate_admissible_for_further_pair_tests_on_engine_schedules_in_v2_only, and downstream_promotion_allowed=false
- axis0_path_entropy_branch_closure all_pass=True: path_entropy status is blocked_diagnostic_only_schedule_confound_proxy, no post-guard adapter activates axis0_path_entropy, and only pre-guard raw diagnostic surfaces list path_entropy
- source-native boundary/interior reconstruction remains a green diagnostic receipt, not a promoted holographic dictionary: strict best-KL selection gap is 0.006982623941363303 < old floor 0.01, engine label accuracy is 0.5 < old floor 0.75, terrain accuracy is 0.21875 < old floor 0.35, and stage accuracy is 0.125
- axis0_holographic_boundary_branch_closure all_pass=True: holographic_boundary_interior_reconstruction status is blocked_diagnostic_only_boundary_interior_reconstruction_proxy, the Axis0 guard blocks axis0_holographic_boundary_interior_reconstruction, no post-guard adapter activates the HBI feature, and only pre-guard/source/router/guard diagnostic surfaces list it
- mps_local_boundary_path_fep_scaling_8_16_32 all_pass=True: no dense state handoff is used; 8/16/32-qubit MPS local-boundary transport consumes repaired science-method stage fields and the post-guard plural Axis0 bundle
- the MPS active bundle contains only fep_gradient_polarity, correlation_diversity_derivative, and retrocausal_many_futures_policy_scoring
- MPS recomputes path entropy only as a local diagnostic readout (path_axis0_path_entropy_delta); path_entropy and holographic_boundary_interior_reconstruction have active_bundle_included=false and are excluded from geometry
- MPS path_axis0_path_entropy_delta is not used in signature, pass, or z3 thresholds; the result records load_bearing_for_signature_or_pass=false and local_path_entropy_readout_not_load_bearing
- the embedded upstream router receipt may still name all five candidates, but the MPS scout records raw_router_receipt_boundary and consumes only the post-guard active bundle listed in candidate_names
- dependency order is now explicit and non-cyclic: macro Axis0 router -> subdense raw multicarrier surface -> Axis0 plural-candidate guard -> MPS post-guard consumer. Subdense must not read the guard receipt; MPS must read the guard receipt.
- integrated suite all_pass=True when run directly; the generic validate_formal_scout_results --fresh-rerun wrapper times out at 120s for the full integrated suite, while direct integrated rerun completed

Audit question:
Does this repair correctly preserve the attractor-basin criterion by adding local operational-assembly and seven-control perturbation-depth evidence, preventing both a knife-edge active-inference policy and a nominal-only online-VMP margin from becoming manifold-depth evidence, closing the stale stage-record-to-carrier bridge reference, keeping subdense environment contraction as a raw pre-guard multicarrier control surface, closing the stale fep_gradient_polarity blocker with a finite stage-local Axis0 closure guard, closing path_entropy as a blocked diagnostic/proxy branch, closing holographic_boundary_interior_reconstruction as a blocked diagnostic branch rather than an admitted Axis0 feature or holographic dictionary, and repairing the MPS 8/16/32 scaling scout so only post-guard Axis0 candidates drive geometry? Identify blockers, overclaims, stale assumptions, receipt-cycle risks, and the smallest next receipt-bearing falsifier. Keep claims proposal-only; cite the paths above."""


def provider_receipt(
    *,
    provider: str,
    status: str,
    proposal_text: str = "",
    blocked_reason: str = "",
    model: str = "",
    raw_response: Any = None,
) -> dict[str, Any]:
    return {
        "schema": "PROVIDER_PROPOSAL_RECEIPT_v1",
        "provider": provider,
        "route": "basin_depth_guard_repair_audit",
        "status": status,
        "classification": "provider_audit",
        "promotion_allowed": False,
        "evidence_allowed": False,
        "claim_ceiling": (
            "Provider audit/proposal only. It may suggest blockers or next probes, "
            "but local formal-scout receipts and validators remain authority."
        ),
        "repo_grounding": {
            "targets": [
                "system_v5/ops/formal_scouts/sim_manifold_dependency_basin_depth_guard_probe.py",
                "system_v5/ops/formal_scouts/results/manifold_dependency_basin_depth_guard_probe_results.json",
                "system_v5/ops/formal_scouts/sim_operational_manifold_assembly_true_perturbation_depth_probe.py",
                "system_v5/ops/formal_scouts/results/operational_manifold_assembly_true_perturbation_depth_probe_results.json",
                "system_v5/ops/formal_scouts/sim_seven_control_source_execution_true_perturbation_depth_probe.py",
                "system_v5/ops/formal_scouts/results/seven_control_source_execution_true_perturbation_depth_probe_results.json",
                "system_v5/ops/formal_scouts/sim_active_policy_online_vmp_margin_closure_probe.py",
                "system_v5/ops/formal_scouts/results/active_policy_online_vmp_margin_closure_probe_results.json",
                "system_v5/ops/formal_scouts/sim_attractor_basin_success_criteria_receipt_classifier_probe.py",
                "system_v5/ops/formal_scouts/results/attractor_basin_success_criteria_receipt_classifier_probe_results.json",
                "system_v5/ops/formal_scouts/sim_stage_record_downstream_carrier_consumption_closure_probe.py",
                "system_v5/ops/formal_scouts/results/stage_record_downstream_carrier_consumption_closure_probe_results.json",
                "system_v5/ops/formal_scouts/sim_source_native_multicarrier_subdense_environment_contraction_probe.py",
                "system_v5/ops/formal_scouts/results/source_native_multicarrier_subdense_environment_contraction_probe_results.json",
                "system_v5/ops/formal_scouts/sim_axis0_plural_candidate_multicarrier_drive_controls_probe.py",
                "system_v5/ops/formal_scouts/results/axis0_plural_candidate_multicarrier_drive_controls_probe_results.json",
                "system_v5/ops/formal_scouts/sim_axis0_fep_gradient_stage_local_adapter_closure_probe.py",
                "system_v5/ops/formal_scouts/results/axis0_fep_gradient_stage_local_adapter_closure_probe_results.json",
                "system_v5/ops/formal_scouts/sim_path_entropy_schedule_confound_falsifier_probe.py",
                "system_v5/ops/formal_scouts/results/path_entropy_schedule_confound_falsifier_probe_results.json",
                "system_v5/ops/formal_scouts/sim_path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe.py",
                "system_v5/ops/formal_scouts/results/path_entropy_proxy_vs_deeper_invariant_pair_falsifier_probe_results.json",
                "system_v5/ops/formal_scouts/sim_axis0_path_entropy_branch_closure_probe.py",
                "system_v5/ops/formal_scouts/results/axis0_path_entropy_branch_closure_probe_results.json",
                "system_v5/ops/formal_scouts/sim_axis0_holographic_boundary_branch_closure_probe.py",
                "system_v5/ops/formal_scouts/results/axis0_holographic_boundary_branch_closure_probe_results.json",
                "system_v5/ops/formal_scouts/sim_mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe.py",
                "system_v5/ops/formal_scouts/results/mps_local_boundary_path_fep_scaling_8_16_32_engine_transport_probe_results.json",
                "system_v5/ops/formal_scouts/sim_integrated_constraint_manifold_suite_fresh_rerun_probe.py",
                "system_v5/ops/formal_scouts/results/integrated_constraint_manifold_suite_fresh_rerun_probe_results.json",
            ],
            "local_facts_embedded_in_prompt": True,
        },
        "model": model,
        "proposal_text": proposal_text,
        "blocked_reason": blocked_reason,
        "raw_response": raw_response,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: float) -> Any:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def run_grok(timeout: float) -> dict[str, Any]:
    key = os.environ.get("XAI_API_KEY")
    model = "grok-4.3"
    if not key:
        return provider_receipt(provider="grok", status="blocked", blocked_reason="XAI_API_KEY not set", model=model)
    try:
        raw = post_json(
            "https://api.x.ai/v1/chat/completions",
            {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            {
                "model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "temperature": 0,
            },
            timeout,
        )
        text = raw["choices"][0]["message"]["content"]
        return provider_receipt(provider="grok", status="completed", proposal_text=text, model=model, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="grok", status="blocked", blocked_reason=repr(exc), model=model)


def run_gemini(timeout: float) -> dict[str, Any]:
    key = os.environ.get("GEMINI_API_KEY")
    model = os.environ.get("WIZARD_GEMINI_MODEL", "gemini-3.5-flash").strip() or "gemini-3.5-flash"
    if not key:
        return provider_receipt(provider="gemini", status="blocked", blocked_reason="GEMINI_API_KEY not set", model=model)
    try:
        raw = post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            {"Content-Type": "application/json", "x-goog-api-key": key},
            {
                "contents": [{"parts": [{"text": PROMPT}]}],
                "generationConfig": {"temperature": 0, "thinkingConfig": {"thinkingBudget": 0}},
            },
            timeout,
        )
        parts = raw["candidates"][0]["content"]["parts"]
        text = "\n".join(str(part.get("text", "")) for part in parts).strip()
        return provider_receipt(provider="gemini", status="completed", proposal_text=text, model=model, raw_response=raw)
    except (KeyError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return provider_receipt(provider="gemini", status="blocked", blocked_reason=repr(exc), model=model)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--provider", choices=["grok", "gemini"], required=True)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--stamp", default=time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()))
    args = parser.parse_args()

    receipt = run_grok(args.timeout) if args.provider == "grok" else run_gemini(args.timeout)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"{args.stamp}_{args.provider}_basin_depth_guard_repair_audit.json"
    out_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(out_path), "status": receipt["status"], "provider": args.provider}, sort_keys=True))
    return 0 if receipt["status"] in {"completed", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
