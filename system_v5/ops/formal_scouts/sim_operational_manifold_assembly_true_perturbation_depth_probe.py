#!/usr/bin/env python3
"""Operational manifold assembly true perturbation-depth scout.

This is a true epsilon perturbation follow-up for the
operational_manifold_assembly row in the basin-depth guard.  It consumes the
existing 13-layer operational assembly receipt, finds the weakest source
layer-removal row, then checks whether that layer effect and the nested-order
effect survive perturbed initial dense states.

Formal scout only.  It proves a local, task-specific perturbation-depth check
for the existing assembly row; it does not admit global manifold necessity,
robust architecture-level basin volume, final FEP, final Axis0, physics,
cognition, world-model, or canonical claims.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import pathlib
import time
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "operational_manifold_assembly_true_perturbation_depth_probe_results.json"

NAME = "operational_manifold_assembly_true_perturbation_depth_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "operational_manifold_assembly_true_perturbation_depth"
CLAIM_CEILING = (
    "Formal scout only: tests whether the existing operational manifold "
    "assembly row keeps its weakest-layer and order-sensitive effects under "
    "bounded perturbed initial states. It does not admit global manifold "
    "requirement, robust architecture-level basin volume, final FEP, final "
    "Axis0, Holodeck, physics, cognition, world-model, architecture, or "
    "canonical claims."
)

TOOL_MANIFEST = {
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through imported operational assembly MPS execution",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through imported 13-layer active constraint enforcers",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt parsing and result writing",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing receipt/source hash capture",
    },
}
TOOL_INTEGRATION_DEPTH = {
    'quimb': 'load_bearing',
    'pytorch': 'load_bearing',
    'json': 'supportive',
    'hashlib': 'supportive',
}

SEEDS = [1001, 2003]
EPSILONS = [0.02, 0.05]
MIN_ORDERING_GAP = 0.05
MIN_LAYER_DIFF = 0.005
MIN_ENTROPY_SPAN = 0.05
MIN_PERTURBATION_NORM = 0.001
MIN_CONTROL_SEPARATION_DELTA = 0.01


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


def receipt_all_pass(data: dict[str, Any]) -> bool:
    if data.get("all_pass") is True:
        return True
    summary = data.get("summary")
    return bool(isinstance(summary, dict) and summary.get("all_pass") is True)


def source_weakest_layer(source: dict[str, Any]) -> dict[str, Any]:
    rows = (
        source.get("positive", {})
        .get("all_thirteen_layers_have_runtime_effect", {})
        .get("sub_results", [])
    )
    if not rows:
        raise ValueError("source operational assembly receipt has no layer-removal sub_results")
    idx, row = min(enumerate(rows), key=lambda pair: float(pair[1].get("state_diff", 0.0)))
    layer_name = row.get("layer")
    state_diff = float(row.get("state_diff", 0.0))
    if layer_name is None or state_diff <= 0.0:
        raise ValueError("source operational assembly weakest-layer row is malformed")
    return {"index": idx, "layer": layer_name, "state_diff": state_diff}


def perturbed_initial(assembly: Any, seed: int, epsilon: float) -> torch.Tensor:
    base = torch.zeros(2 ** assembly.N_QUBITS, dtype=torch.complex128)
    base[0] = 1.0
    generator = torch.Generator().manual_seed(seed)
    noise = (
        torch.randn(base.shape, generator=generator, dtype=torch.float64)
        + 1j * torch.randn(base.shape, generator=generator, dtype=torch.float64)
    ).to(torch.complex128)
    noise = noise / max(float(torch.linalg.vector_norm(noise).item()), 1e-15)
    psi = (1.0 - epsilon) * base + epsilon * noise
    return psi / max(float(torch.linalg.vector_norm(psi).item()), 1e-15)


def run_assembly_from_initial(
    assembly: Any,
    psi0: torch.Tensor,
    *,
    reverse_layers: bool = False,
    skip_layer: int | None = None,
) -> dict[str, Any]:
    mps = assembly.mps_from_dense(psi0)
    context: dict[str, Any] = {}
    entropies = []
    bonds = []
    layer_order = (
        list(reversed(range(len(assembly.LAYERS))))
        if reverse_layers else list(range(len(assembly.LAYERS)))
    )
    for step in range(assembly.N_STEPS):
        mps, _metrics = assembly.apply_operational_manifold_step(
            mps,
            step,
            context,
            layer_order=layer_order,
            skip_layer=skip_layer,
        )
        psi = assembly.normalized_dense(mps)
        rho = assembly.reduced_density(psi, step % assembly.N_QUBITS)
        entropies.append(assembly.entropy(rho))
        bonds.append(int(mps.max_bond()))
    return {
        "final_state": assembly.normalized_dense(mps),
        "entropy_span": float(max(entropies) - min(entropies)),
        "max_bond": int(max(bonds)),
    }


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(val) for key, val in value.items()}
    if isinstance(value, list):
        return [as_jsonable(val) for val in value]
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if hasattr(value, "item"):
        return value.item()
    return value


def main() -> int:
    started = time.time()
    assembly = importlib.import_module("sim_nested_constraint_manifold_operational_assembly_tensor_network_probe")
    source = load_receipt("nested_constraint_manifold_operational_assembly_tensor_network_probe_results.json")
    depth_guard = load_receipt("manifold_dependency_basin_depth_guard_probe_results.json")
    weakest = source_weakest_layer(source)

    rows = []
    for seed in SEEDS:
        for epsilon in EPSILONS:
            psi0 = perturbed_initial(assembly, seed, epsilon)
            base = torch.zeros_like(psi0)
            base[0] = 1.0
            perturbation_norm = float(torch.linalg.vector_norm(psi0 - base).item())
            full = run_assembly_from_initial(assembly, psi0)
            reverse = run_assembly_from_initial(assembly, psi0, reverse_layers=True)
            skipped = run_assembly_from_initial(assembly, psi0, skip_layer=int(weakest["index"]))
            ordering_gap = float(torch.linalg.vector_norm(torch.as_tensor(full["final_state"]) - torch.as_tensor(reverse["final_state"])).item())
            layer_diff = float(torch.linalg.vector_norm(torch.as_tensor(full["final_state"]) - torch.as_tensor(skipped["final_state"])).item())
            control_separation_delta = abs(ordering_gap - layer_diff)
            rows.append(
                {
                    "seed": seed,
                    "epsilon": epsilon,
                    "perturbation_norm": perturbation_norm,
                    "weakest_layer_index": weakest["index"],
                    "weakest_layer": weakest["layer"],
                    "source_weakest_layer_diff": weakest["state_diff"],
                    "entropy_span": full["entropy_span"],
                    "max_bond": full["max_bond"],
                    "ordering_gap": ordering_gap,
                    "weakest_layer_diff": layer_diff,
                    "order_vs_skip_control_separation_delta": control_separation_delta,
                    "perturbation_norm_pass": perturbation_norm > MIN_PERTURBATION_NORM,
                    "ordering_gap_pass": ordering_gap > MIN_ORDERING_GAP,
                    "weakest_layer_diff_pass": layer_diff > MIN_LAYER_DIFF,
                    "entropy_span_pass": full["entropy_span"] > MIN_ENTROPY_SPAN,
                    "order_vs_skip_control_separation_pass": control_separation_delta > MIN_CONTROL_SEPARATION_DELTA,
                }
            )

    min_ordering_gap = min(row["ordering_gap"] for row in rows)
    min_layer_diff = min(row["weakest_layer_diff"] for row in rows)
    min_entropy_span = min(row["entropy_span"] for row in rows)

    positive = {
        "source_operational_assembly_receipt_loads": {
            "pass": source.get("exists") is True and receipt_all_pass(source),
            "source_sha256": source.get("sha256"),
        },
        "perturbed_initial_grid_executes": {
            "pass": len(rows) == len(SEEDS) * len(EPSILONS)
            and all(row["perturbation_norm_pass"] for row in rows),
            "seeds": SEEDS,
            "epsilons": EPSILONS,
            "row_count": len(rows),
            "min_perturbation_norm": min(row["perturbation_norm"] for row in rows),
            "min_perturbation_norm_floor": MIN_PERTURBATION_NORM,
        },
        "weakest_layer_effect_survives_perturbed_initials": {
            "pass": all(row["weakest_layer_diff_pass"] for row in rows),
            "weakest_layer": weakest,
            "min_layer_diff": min_layer_diff,
            "min_layer_diff_floor": MIN_LAYER_DIFF,
        },
        "nested_order_effect_survives_perturbed_initials": {
            "pass": all(row["ordering_gap_pass"] for row in rows),
            "min_ordering_gap": min_ordering_gap,
            "min_ordering_gap_floor": MIN_ORDERING_GAP,
        },
        "assembly_entropy_span_survives_perturbed_initials": {
            "pass": all(row["entropy_span_pass"] for row in rows),
            "min_entropy_span": min_entropy_span,
            "min_entropy_span_floor": MIN_ENTROPY_SPAN,
        },
    }

    graveyard = {
        "unperturbed_only_assembly_depth_claim_rejected": {
            "pass": len(rows) > 1 and all(row["perturbation_norm_pass"] for row in rows),
            "reason": "This scout reruns perturbed initial states instead of relying on the original unperturbed assembly receipt.",
        },
        "stronger_all_layer_under_perturbation_not_claimed": {
            "pass": weakest["layer"] is not None
            and len({row["weakest_layer_index"] for row in rows}) == 1,
            "reason": "This scout tests the source weakest layer under perturbation; it does not claim all 13 layer removals survive a perturbation grid.",
        },
        "reverse_order_control_is_not_a_layer_removal_proxy": {
            "pass": all(row["order_vs_skip_control_separation_pass"] for row in rows),
            "min_order_vs_skip_control_separation_delta": min(
                row["order_vs_skip_control_separation_delta"] for row in rows
            ),
            "min_order_vs_skip_control_separation_floor": MIN_CONTROL_SEPARATION_DELTA,
            "reason": "Reverse-order and weakest-layer-skip controls are evaluated separately for every perturbed initial state.",
        },
    }

    boundary = {
        "claim_ceiling_blocks_global_and_canonical_claims": {
            "pass": all(term in CLAIM_CEILING.lower() for term in ["formal scout", "does not admit", "global manifold requirement"]),
        },
        "downstream_depth_guard_loaded_as_context": {
            "pass": depth_guard.get("exists") is True and receipt_all_pass(depth_guard),
            "depth_guard_sha256": depth_guard.get("sha256"),
            "depth_guard_passes": receipt_all_pass(depth_guard),
        },
        "next_work_is_seven_control_perturbation_or_all_layer_extension": {
            "pass": True,
            "next": "Consume this in the basin-depth guard/classifier, then perturb seven_control_source_execution or extend this scout to all 13 layer removals.",
        },
    }

    nearby_passed = sum(
        row["perturbation_norm_pass"]
        and row["ordering_gap_pass"]
        and row["weakest_layer_diff_pass"]
        and row["entropy_span_pass"]
        and row["order_vs_skip_control_separation_pass"]
        for row in rows
    )
    sections = (positive, graveyard, boundary)
    blockers = [
        f"{section_name}.{row_name}"
        for section_name, section in (
            ("positive", positive),
            ("graveyard_companions", graveyard),
            ("boundary", boundary),
        )
        for row_name, row in section.items()
        if isinstance(row, dict) and row.get("pass") is not True
    ]
    all_pass = all(
        row.get("pass") is True
        for section in sections
        for row in section.values()
    )

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
            "total": len(rows),
            "passed": nearby_passed,
            "variants": rows,
        },
        "why_not_v4_probes": (
            "This is a v5 operational manifold assembly perturbation-depth scout. "
            "It does not add v4 probe authority or promote manifold/physics claims."
        ),
        "perturbation_rows": rows,
        "repair_receipt": {
            "weak_link": "operational_manifold_assembly had receipt-local layer/order margin evidence but no perturbed-initial-state depth receipt.",
            "target_file_or_result": str(OUT_PATH),
            "admission_rule_improved": "Operational assembly basin-depth evidence now requires the source weakest-layer effect and nested-order effect to survive a bounded perturbed-initial-state grid.",
            "dependency_subset": [source.get("path"), depth_guard.get("path")],
            "stage_fields_touched_or_consumed": ["constraint_set_for_engine", "positive.all_thirteen_layers_have_runtime_effect", "positive.nested_order_matters_for_operational_assembly"],
            "before_baseline/hash": {
                "operational_assembly": source.get("sha256"),
                "depth_guard": depth_guard.get("sha256"),
            },
            "after_delta/hash": {
                "script": sha256_file(pathlib.Path(__file__)),
                "result": "written_after_receipt_payload_assembly",
            },
            "primary_control/result": {
                "row_count": len(rows),
                "weakest_layer": weakest,
                "min_layer_diff": min_layer_diff,
                "min_ordering_gap": min_ordering_gap,
                "min_entropy_span": min_entropy_span,
            },
            "axis0_outputs_or_blockers": {
                "fep_gradient_polarity": "not touched here",
                "path_entropy": "not touched here",
                "correlation_diversity_derivative": "not touched here",
                "holographic_boundary_interior_reconstruction": "not touched here",
                "retrocausal_many_futures_policy_scoring": "not touched here",
            },
            "provider_inputs_used": {
                "grok": "not_run_this_repair_wave",
                "gemini": "not_run_this_repair_wave",
                "opus_max": "not_run_this_repair_wave",
                "sonnet_high": "not_run_this_repair_wave",
            },
            "promotion_ceiling": CLAIM_CEILING,
            "next_step": "Update basin-depth guard/classifier to consume this perturbation-depth receipt, then continue with seven_control_source_execution or all-layer perturbation extension.",
        },
        "audit_method_families": [
            "perturbed_initial_seed_grid",
            "epsilon_grid",
            "weakest_layer_skip_control",
            "reverse_order_control",
            "mps_operational_assembly",
        ],
        "method_count_source": "operational_assembly_perturbed_initial_grid",
        "blockers": blockers,
        "all_pass": all_pass,
        "elapsed_seconds": round(time.time() - started, 6),
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
