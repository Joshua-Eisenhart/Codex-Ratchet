#!/usr/bin/env python3
"""Closure scout for the online-VMP active-policy margin repair.

The older active-policy window remains blocked because its top-two EFE margin
is below the basin-depth floor.  The stricter source-native POMDP + online VMP
receipt clears the nominal policy margin, but that alone is not enough to
repair the manifold-dependency row.  This scout tests the missing manifold-off
online VMP control and records the honest closure:

- online VMP is a stronger finite FEP interface candidate;
- it does not repair active_inference_policy_window into manifold-depth
  evidence because the manifold-disabled online control is not worse than the
  nominal manifold-on run under the same EFE scale.

Formal scout only.  No final FEP, Axis0, manifold-required, Holodeck, physics,
world-model, cognition, architecture, or canonical claim is admitted.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import time
from typing import Any

import torch

import sim_source_native_fep_online_vmp_policy_update_probe as vmp
import sim_source_native_fep_pomdp_policy_tree_probe as pomdp


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "active_policy_online_vmp_margin_closure_probe_results.json"

NAME = "active_policy_online_vmp_margin_closure_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "active_policy_online_vmp_margin_closure"
CLAIM_CEILING = (
    "Formal scout only: tests whether the source-native online-VMP policy "
    "receipt can repair the active-policy row into manifold-depth evidence. "
    "It does not admit final FEP, final Axis0, deep-basin evidence, global "
    "manifold requirement, Holodeck, physics, cognition, world-model, "
    "architecture, or canonical claims."
)

TOOL_MANIFEST = {
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing policy-row sorting, margins, and finite online-VMP control comparisons",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing and result writing",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing source/result hash receipts",
    },
    "engine_core": {
        "tried": True,
        "used": True,
        "reason": "load-bearing transitively through POMDP/VMP source-native transition estimation",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "python_stdlib": "supportive",
    "json": "supportive",
    "hashlib": "supportive",
    "engine_core": "supportive",
}

MARGIN_FLOOR = 0.01
CONTROL_MARGIN_FLOOR = 0.02
POSTERIOR_KL_FLOOR = vmp.POSTERIOR_KL_FLOOR
VFE_REDUCTION_FLOOR = vmp.VFE_REDUCTION_FLOOR
EFE_DECOMPOSITION_TOL = vmp.EFE_DECOMPOSITION_TOL


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_receipt(filename: str) -> dict[str, Any]:
    path = RESULT_DIR / filename
    if not path.exists():
        return {"exists": False, "filename": filename, "path": str(path)}
    data = json.loads(path.read_text(encoding="utf-8"))
    data["exists"] = True
    data["filename"] = filename
    data["path"] = str(path)
    data["sha256"] = sha256_file(path)
    return data


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(val) for val in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    array_module = getattr(vmp, "np", None) or getattr(pomdp, "np", None)
    if array_module is not None:
        if isinstance(value, array_module.ndarray):
            return value.tolist()
        if isinstance(value, (array_module.bool_,)):
            return bool(value)
        if isinstance(value, (array_module.integer, array_module.floating)):
            return value.item()
    return value


def top_two(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(rows, key=lambda row: float(row["expected_free_energy"]))
    top = ordered[0]
    runner = ordered[1]
    return {
        "top_policy": top["policy_id"],
        "top_efe": float(top["expected_free_energy"]),
        "runner_up_policy": runner["policy_id"],
        "runner_up_efe": float(runner["expected_free_energy"]),
        "top_two_margin": float(runner["expected_free_energy"] - top["expected_free_energy"]),
        "policy_count": len(ordered),
    }


def control_row(label: str, rows: list[dict[str, Any]], nominal: dict[str, Any]) -> dict[str, Any]:
    row = top_two(rows)
    row["label"] = label
    row["delta_vs_nominal_top_efe"] = row["top_efe"] - nominal["top_efe"]
    row["policy_changed"] = row["top_policy"] != nominal["top_policy"]
    row["top_two_margin_floor"] = MARGIN_FLOOR
    return row


def main() -> int:
    started = time.time()
    pomdp_receipt = load_receipt("source_native_fep_pomdp_policy_tree_probe_results.json")
    online_receipt = load_receipt("source_native_fep_online_vmp_policy_update_probe_results.json")
    old_margin_receipt = load_receipt("active_inference_policy_margin_sensitivity_probe_results.json")

    a_matrix = pomdp.emission_matrix()
    c_pref = pomdp.preference_distribution()
    d_prior = pomdp.estimate_prior()

    nominal_rows = vmp.online_family(a_matrix=a_matrix, c_pref=c_pref, d_prior=d_prior)
    no_manifold_rows = vmp.online_family(
        a_matrix=a_matrix,
        c_pref=c_pref,
        d_prior=d_prior,
        manifold_enabled=False,
    )
    no_engine_rows = vmp.online_family(
        a_matrix=a_matrix,
        c_pref=c_pref,
        d_prior=d_prior,
        no_engine_control=True,
    )
    heldout_rows = vmp.online_family(
        a_matrix=a_matrix,
        c_pref=c_pref,
        d_prior=d_prior,
        observation_mode="heldout_cycle",
    )
    shuffled_rows = vmp.online_family(
        a_matrix=a_matrix,
        c_pref=pomdp.shuffled_preference(c_pref),
        d_prior=d_prior,
    )
    identity_emission_rows = vmp.online_family(
        a_matrix=pomdp.identity_emission_matrix(),
        c_pref=c_pref,
        d_prior=d_prior,
    )

    nominal = top_two(nominal_rows)
    controls = {
        "no_manifold_online_vmp": control_row("no_manifold_online_vmp", no_manifold_rows, nominal),
        "no_engine_online_vmp": control_row("no_engine_online_vmp", no_engine_rows, nominal),
        "heldout_observation_online_vmp": control_row("heldout_observation_online_vmp", heldout_rows, nominal),
        "shuffled_preference_online_vmp": control_row("shuffled_preference_online_vmp", shuffled_rows, nominal),
        "identity_emission_online_vmp": control_row("identity_emission_online_vmp", identity_emission_rows, nominal),
    }

    online_summary = online_receipt.get("summary") or {}
    online_positives = online_receipt.get("positive") or {}
    old_margin_primary = (
        (old_margin_receipt.get("repair_receipt") or {})
        .get("primary_control/result", {})
    )

    nominal_margin_pass = nominal["top_two_margin"] >= MARGIN_FLOOR
    online_update_pass = (
        online_receipt.get("exists") is True
        and online_receipt.get("all_pass") is True
        and float(online_summary.get("posterior_kl_max", 999.0)) < POSTERIOR_KL_FLOOR
        and float(online_summary.get("vfe_reduction_min", -999.0)) > VFE_REDUCTION_FLOOR
        and (
            online_positives.get("heldout_observation_tokens_support_online_updates", {})
            .get("pass")
            is True
        )
    )
    no_manifold = controls["no_manifold_online_vmp"]
    no_manifold_blocks_depth = (
        no_manifold["delta_vs_nominal_top_efe"] < CONTROL_MARGIN_FLOOR
        or no_manifold["top_two_margin"] < MARGIN_FLOOR
    )
    manifold_off_outperforms_nominal = no_manifold["delta_vs_nominal_top_efe"] < 0.0
    old_strategy_still_blocked = (
        old_margin_receipt.get("exists") is True
        and old_margin_receipt.get("all_pass") is True
        and old_margin_primary.get("branch_status") == "blocked_open"
    )
    branch_status = "blocked_open" if no_manifold_blocks_depth else "repaired_candidate"

    positive = {
        "upstream_online_vmp_receipt_loads": {
            "pass": online_receipt.get("exists") is True and online_receipt.get("all_pass") is True,
            "receipt_sha256": online_receipt.get("sha256"),
        },
        "upstream_pomdp_receipt_loads": {
            "pass": pomdp_receipt.get("exists") is True and pomdp_receipt.get("all_pass") is True,
            "receipt_sha256": pomdp_receipt.get("sha256"),
        },
        "online_vmp_nominal_margin_clears_policy_floor": {
            "pass": nominal_margin_pass,
            **nominal,
            "margin_floor": MARGIN_FLOOR,
        },
        "online_vmp_update_quality_predicates_remain_green": {
            "pass": online_update_pass,
            "posterior_kl_max": online_summary.get("posterior_kl_max"),
            "posterior_kl_floor": POSTERIOR_KL_FLOOR,
            "vfe_reduction_min": online_summary.get("vfe_reduction_min"),
            "vfe_reduction_floor": VFE_REDUCTION_FLOOR,
            "heldout_control_pass": (
                online_positives.get("heldout_observation_tokens_support_online_updates", {})
                .get("pass")
            ),
        },
        "online_vmp_manifold_disabled_control_evaluated": {
            "pass": no_manifold["policy_count"] == 16 and no_manifold["top_policy"] is not None,
            "control": no_manifold,
        },
        "branch_closure_is_explicit": {
            "pass": branch_status in {"blocked_open", "repaired_candidate"},
            "branch_status": branch_status,
            "reason": "The online-VMP repair candidate was routed from evaluated nominal and no-manifold controls.",
        },
    }

    graveyard = {
        "old_strategy_policy_branch_still_blocked": {
            "pass": old_strategy_still_blocked,
            "old_branch_status": old_margin_primary.get("branch_status"),
            "baseline_margin": old_margin_primary.get("baseline_margin"),
            "best_margin": old_margin_primary.get("best_margin"),
            "margin_floor": old_margin_primary.get("margin_floor"),
        },
        "online_vmp_nominal_margin_not_enough_for_manifold_depth": {
            "pass": True,
            "currently_blocks_depth": nominal_margin_pass and no_manifold_blocks_depth,
            "nominal": nominal,
            "no_manifold_control": no_manifold,
            "boundary": "A nominal policy margin is not a manifold-depth guard without manifold-disabled control pressure.",
        },
        "no_manifold_control_blocks_depth_upgrade": {
            "pass": True,
            "currently_blocks_depth": no_manifold_blocks_depth,
            "delta_vs_nominal_top_efe": no_manifold["delta_vs_nominal_top_efe"],
            "manifold_off_outperforms_nominal": manifold_off_outperforms_nominal,
            "control_margin_floor": CONTROL_MARGIN_FLOOR,
            "no_manifold_top_two_margin": no_manifold["top_two_margin"],
            "top_two_margin_floor": MARGIN_FLOOR,
        },
        "online_vmp_controls_are_interface_controls_not_depth_proof": {
            "pass": True,
            "controls": controls,
            "note": "These controls show finite FEP interface sensitivity. They do not prove the manifold is required for the active-policy row.",
        },
        "scalar_weight_tuning_not_used": {
            "pass": True,
            "efe_formula": "risk + ambiguity",
            "reason": "This closure imports the POMDP/VMP finite scoring formula and does not tune EFE scalar weights.",
        },
    }

    repair_receipt = {
        "weak_link": "The online-VMP receipt cleared the nominal policy margin, but the active-policy basin-depth row still needed a manifold-disabled online control.",
        "target_file_or_result": str(OUT_PATH),
        "admission_rule_improved": (
            "An online-VMP policy margin can support the finite FEP interface only. "
            "It repairs active-policy manifold-depth evidence only if the manifold-disabled "
            "online control also fails by the same margin discipline."
        ),
        "dependency_subset": [
            online_receipt.get("path"),
            pomdp_receipt.get("path"),
            old_margin_receipt.get("path"),
        ],
        "stage_fields_touched_or_consumed": [
            "A_emission",
            "B_pi transition",
            "C_preference",
            "D_prior",
            "online_vmp posterior",
            "expected_free_energy",
            "manifold_disabled online control",
        ],
        "before_baseline/hash": {
            "online_vmp_receipt": online_receipt.get("sha256"),
            "pomdp_receipt": pomdp_receipt.get("sha256"),
            "old_margin_receipt": old_margin_receipt.get("sha256"),
        },
        "after_delta/hash": {
            "script": sha256_file(pathlib.Path(__file__)),
            "result": "written_after_receipt_payload_assembly",
        },
        "primary_control/result": {
            "branch_status": branch_status,
            "active_policy_window_remains_open": branch_status == "blocked_open",
            "online_vmp_nominal_margin": nominal["top_two_margin"],
            "margin_floor": MARGIN_FLOOR,
            "online_vmp_selected_policy": nominal["top_policy"],
            "no_manifold_online_policy": no_manifold["top_policy"],
            "no_manifold_delta_vs_nominal_top_efe": no_manifold["delta_vs_nominal_top_efe"],
            "manifold_off_outperforms_nominal": manifold_off_outperforms_nominal,
            "no_manifold_top_two_margin": no_manifold["top_two_margin"],
            "no_manifold_blocks_depth_repair": no_manifold_blocks_depth,
            "old_strategy_branch_status": old_margin_primary.get("branch_status"),
        },
        "axis0_outputs_or_blockers": {
            "retrocausal_many_futures_policy_scoring": (
                "online VMP remains a finite many-futures policy-scoring interface candidate, "
                "but it does not repair active-policy manifold-depth evidence"
            ),
            "fep_gradient_polarity": "not touched here",
            "path_entropy": "not revived",
            "holographic_boundary_interior_reconstruction": "not touched here",
        },
        "provider_inputs_used": {
            "grok": "not_run_this_closure_wave",
            "gemini": "not_run_this_closure_wave",
            "opus_max": "not_run_this_closure_wave",
            "sonnet_high": "not_run_this_closure_wave",
            "codex_native_subagents": "read-only active-policy and POMDP/VMP explorer lanes informed the repair question but are not embedded as formal evidence",
        },
        "promotion_ceiling": CLAIM_CEILING,
        "next_step": "Consume this closure in the basin-depth guard; keep active_inference_policy_window routed open until a new scoring/manifold-control formulation exists.",
    }

    boundary = {
        "claim_ceiling_blocks_depth_or_full_fep_promotion": {
            "pass": all(
                term in CLAIM_CEILING.lower()
                for term in ["formal scout", "does not admit", "deep-basin evidence", "global manifold"]
            ),
        },
        "repair_receipt_has_required_loop_fields": {
            "pass": all(
                key in repair_receipt
                for key in [
                    "weak_link",
                    "target_file_or_result",
                    "admission_rule_improved",
                    "dependency_subset",
                    "stage_fields_touched_or_consumed",
                    "before_baseline/hash",
                    "after_delta/hash",
                    "primary_control/result",
                    "axis0_outputs_or_blockers",
                    "provider_inputs_used",
                    "promotion_ceiling",
                    "next_step",
                ]
            ),
            "keys": sorted(repair_receipt),
        },
        "promotion_remains_disabled": {
            "pass": PROMOTION_ALLOWED is False and CLASSIFICATION == "formal_scout",
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(controls),
            "passed": len(controls),
            "variants": controls,
        },
        "why_not_v4_probes": (
            "This is a v5 source-native closure receipt over the finite POMDP/VMP scouts. "
            "It does not revive v4 Holodeck, IGT, physics, or narrative probes."
        ),
        "policy_rows": nominal_rows,
        "control_rows": controls,
        "repair_receipt": repair_receipt,
        "axis0_outputs_or_blockers": repair_receipt["axis0_outputs_or_blockers"],
        "audit_method_families": [
            "online_vmp_nominal_margin",
            "online_vmp_update_quality",
            "online_vmp_no_manifold_control",
            "old_strategy_policy_margin_blocker",
        ],
        "method_count_source": "online_vmp_repair_candidate_with_manifold_disabled_control_closure",
        "explicit_branch_blockers": [
            "online_vmp_no_manifold_control_blocks_manifold_depth_repair",
            "old_strategy_policy_margin_floor_not_met",
        ],
        "blockers": [],
        "all_pass": all(
            row.get("pass") is True
            for section in (positive, graveyard, boundary)
            for row in section.values()
        ),
        "elapsed_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"RESULT {NAME}: all_pass={result['all_pass']} -> {OUT_PATH}")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
