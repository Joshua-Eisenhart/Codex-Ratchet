#!/usr/bin/env python3
"""Falsifier for semantic overclaims in the anti-teleological branch scout."""

from __future__ import annotations

import importlib.util
import json
import math
import os
import pathlib
import sys
import time
from typing import Any, Callable

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "layer_operator_name_blindness_falsifier_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"
PARENT_PATH = ROOT / "sim_antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe.py"
PARENT_RESULT = RESULT_DIR / "antiteleology_geometric_constraint_manifold_pytorch_branch_tensor_network_probe_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "anti_teleology_layer_semantics_falsifier"
CLAIM_CEILING = (
    "Formal scout only: falsifies semantic overclaims about the prior anti-teleological "
    "PyTorch branch scout by testing whether its gates survive layer-name scrambling, "
    "operator-family replacement, and single-layer repetition. A green result demotes "
    "the prior scout to a tool/branch harness for this claim; it does not admit a final "
    "manifold, final nesting order, real attractor basin, bridge, axis, or canonical architecture."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing variant layer operators, branch fingerprints, and tensor comparisons",
    },
    "auto_LiRPA": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent branch-energy bound in every operator-family variant",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite falsifier classification: if all controls pass, semantic-layer implementation claim is killed",
    },
    "torch_geometric": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent graph/message-passing gate in every operator-family variant",
    },
    "rustworkx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent DAG/reachability gate in every operator-family variant",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent branch-coupled noncommutative witness in every variant",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent branch-coupled pseudoscalar action in every variant",
    },
    "geomstats": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent branch-derived sphere-distance witness in every variant",
    },
    "e3nn": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent branch-derived tensor-product witness in every variant",
    },
    "xgi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent hypergraph gate in every variant",
    },
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent simplicial-complex gate in every variant",
    },
    "gudhi": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the imported parent persistence gate in every variant",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive parent source/result loading",
    },
    "python_json": {
        "tried": True,
        "used": True,
        "reason": "supportive receipt serialization",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "auto_LiRPA": "load_bearing",
    "z3": "load_bearing",
    "torch_geometric": "load_bearing",
    "rustworkx": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "geomstats": "load_bearing",
    "e3nn": "load_bearing",
    "xgi": "load_bearing",
    "toponetx": "load_bearing",
    "gudhi": "load_bearing",
    "pathlib": "supportive",
    "python_json": "supportive",
}

EXTERNAL_MODULE_MANIFEST = {
    "parent_antiteleology_branch_scout": {
        "tried": True,
        "used": True,
        "reason": "load-bearing import of the current parent scout functions under controlled operator monkeypatches",
        "path": str(PARENT_PATH),
    },
    "le_wm_module": {
        "tried": True,
        "used": True,
        "reason": "load-bearing through the parent scout le-wm SIGReg/ARPredictor branch-pressure gate",
        "path": "/Users/joshuaeisenhart/GitHub/le-wm/module.py",
    },
}
EXTERNAL_MODULE_INTEGRATION_DEPTH = {
    "parent_antiteleology_branch_scout": "load_bearing",
    "le_wm_module": "load_bearing",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if torch.is_tensor(value):
        if value.numel() == 1:
            return float(value.detach().cpu().item())
        return value.detach().cpu().tolist()
    return value


def load_parent_module() -> Any:
    spec = importlib.util.spec_from_file_location("antiteleology_parent_probe", PARENT_PATH)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Cannot load parent scout: {PARENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def seeded_rotation_operator(layer_idx: int, branch_idx: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(93500 + 101 * layer_idx + 1009 * branch_idx)
    raw = torch.randn((8, 8), generator=generator, dtype=torch.float32)
    q, _r = torch.linalg.qr(raw)
    return torch.eye(8, dtype=torch.float32) + 0.019 * q


def repeated_mid_layer_operator(parent: Any) -> Callable[[int, int], torch.Tensor]:
    original_operator = parent.layer_operator

    def _operator(_layer_idx: int, branch_idx: int) -> torch.Tensor:
        return original_operator(6, branch_idx)

    return _operator


def variant_report(parent: Any, label: str, operator_fn: Callable[[int, int], torch.Tensor]) -> dict[str, Any]:
    original_operator = parent.layer_operator
    try:
        parent.layer_operator = operator_fn
        manifold = parent.run_branch_manifold()
        lewm_module = parent.load_lewm_module()
        lewm = parent.lewm_active_pressure(lewm_module, manifold["branch_outputs"])
        lirpa = parent.lirpa_branch_bound(manifold["branch_outputs"], manifold["tensor_signatures"])
        graph = parent.graph_topology_report(manifold["energies"])
        math_geometry = parent.math_geometry_report(manifold["branch_outputs"])
    finally:
        parent.layer_operator = original_operator
    all_gates = {
        "pytorch_branch_tensor_network": bool(manifold["positive"]["pass"]),
        "lewm_branch_pressure": bool(lewm["pass"]),
        "auto_lirpa_bound": bool(lirpa["pass"]),
        "graph_topology": bool(graph["pass"]),
        "math_geometry": bool(math_geometry["pass"]),
    }
    branch_fingerprint = manifold["branch_outputs"].detach().reshape(-1)
    return {
        "label": label,
        "all_gates": all_gates,
        "all_gates_pass": all(all_gates.values()),
        "energy_values": [float(x) for x in manifold["energies"].detach().tolist()],
        "pairwise_branch_distance_min": manifold["positive"]["pairwise_branch_distance_min"],
        "lewm_relative_advantage": lewm["relative_loss_advantage_vs_best_control"],
        "lirpa_mean_bound_width": lirpa["mean_bound_width"],
        "branch_fingerprint_norm": float(torch.linalg.vector_norm(branch_fingerprint).item()),
        "branch_fingerprint": branch_fingerprint,
    }


def label_scramble_report(parent: Any, baseline: dict[str, Any]) -> dict[str, Any]:
    original_layers = parent.LAYERS
    scrambled = [
        original_layers[0],
        original_layers[10],
        original_layers[7],
        original_layers[3],
        original_layers[12],
        original_layers[5],
        original_layers[1],
        original_layers[8],
        original_layers[4],
        original_layers[9],
        original_layers[2],
        original_layers[11],
        original_layers[6],
    ]
    try:
        parent.LAYERS = scrambled
        rerun = variant_report(parent, "label_scramble_same_indices", parent.layer_operator)
    finally:
        parent.LAYERS = original_layers
    max_abs_diff = float(torch.max(torch.abs(rerun["branch_fingerprint"] - baseline["branch_fingerprint"])).item())
    return {
        "label": "label_scramble_same_indices",
        "scrambled_labels": scrambled,
        "all_gates_pass": rerun["all_gates_pass"],
        "max_abs_fingerprint_diff_vs_baseline": max_abs_diff,
        "pass": bool(rerun["all_gates_pass"] and max_abs_diff < 1e-9),
    }


def z3_falsifier(all_controls_pass: bool) -> dict[str, Any]:
    solver = z3.Solver()
    controls_pass = z3.Bool("all_controls_pass")
    semantic_layer_claim_survives = z3.Bool("semantic_layer_claim_survives")
    solver.add(controls_pass == z3.BoolVal(all_controls_pass))
    solver.add(semantic_layer_claim_survives == z3.Not(controls_pass))
    solver.add(semantic_layer_claim_survives)
    status = solver.check()
    return {
        "all_controls_pass": all_controls_pass,
        "semantic_layer_claim_survives_status": str(status),
        "pass": bool(status == z3.unsat if all_controls_pass else status == z3.sat),
    }


def main() -> dict[str, Any]:
    started = time.time()
    parent = load_parent_module()
    if not PARENT_RESULT.exists():
        raise SystemExit(f"Missing parent result: {PARENT_RESULT}")
    parent_result = json.loads(PARENT_RESULT.read_text(encoding="utf-8"))
    baseline = variant_report(parent, "baseline_parent_operator", parent.layer_operator)
    label_scramble = label_scramble_report(parent, baseline)
    seeded_rotation = variant_report(parent, "seeded_rotation_operator_replacement", seeded_rotation_operator)
    repeated_layer = variant_report(parent, "single_repeated_mid_layer_operator", repeated_mid_layer_operator(parent))
    operator_controls = [seeded_rotation, repeated_layer]
    all_operator_controls_pass = all(row["all_gates_pass"] for row in operator_controls)
    all_controls_pass = bool(label_scramble["pass"] and all_operator_controls_pass)
    proof = z3_falsifier(all_controls_pass)

    positive = {
        "parent_receipt_is_green_and_nonpromotional": {
            "parent_result": str(PARENT_RESULT),
            "parent_summary": parent_result.get("summary", {}),
            "pass": parent_result.get("summary", {}).get("all_pass") is True
            and parent_result.get("promotion_allowed") is False,
        },
        "label_scramble_does_not_change_numeric_branch_surface": label_scramble,
        "operator_family_replacement_still_passes_parent_gates": {
            "variant": {k: v for k, v in seeded_rotation.items() if k != "branch_fingerprint"},
            "pass": bool(seeded_rotation["all_gates_pass"]),
        },
        "single_repeated_layer_still_passes_parent_gates": {
            "variant": {k: v for k, v in repeated_layer.items() if k != "branch_fingerprint"},
            "pass": bool(repeated_layer["all_gates_pass"]),
        },
        "z3_classifies_semantic_layer_overclaim_as_killed": proof,
    }
    graveyard_companions = {
        "named_layer_semantics_claim_killed_for_parent_scout": {
            "reason": "Layer labels can be scrambled without changing the numeric branch surface, and non-geometric operator controls still pass the parent gates.",
            "pass": all_controls_pass and proof["pass"],
        },
        "tool_breadth_equals_geometric_depth_control_rejected": {
            "reason": "The same broad tool stack can pass under seeded rotations and repeated-layer controls, so breadth of tools is not depth of semantic geometry.",
            "operator_controls_all_pass": all_operator_controls_pass,
            "pass": all_operator_controls_pass,
        },
        "anti_teleology_count_only_control_rejected": {
            "reason": "Five branch orders remain only branch-count evidence unless a follow-up binds layer names to semantic operators.",
            "branch_count": len(parent.BRANCH_ORDERS),
            "pass": len(parent.BRANCH_ORDERS) >= 5 and all_controls_pass,
        },
    }
    boundary = {
        "formal_scout_nonpromotion": {
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
            "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
        },
        "does_not_demote_tool_branch_harness": {
            "claim": "This falsifies semantic layer-name overclaims only; it does not say the parent scout failed as a PyTorch/tool branch harness.",
            "pass": True,
        },
        "next_admissible_repair": {
            "repair": "replace index-driven layer_operator fixtures with per-layer semantic operators, then rerun this falsifier before stronger manifold wording",
            "pass": True,
        },
    }
    all_pass = (
        all(row["pass"] for row in positive.values())
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "total": len(graveyard_companions),
            "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
        },
        "blockers": [],
        "open_choices": [
            "Author a semantic per-layer operator replacement for hopf_fiber_bundle, connection_holonomy_geometry, chirality_orientation_cover, Clifford module, and tensor_product_coupling_geometry.",
            "Rerun this falsifier after semantic operators exist; semantic claims remain blocked until at least one control fails for the right reason.",
            "Keep the parent anti-teleology scout indexed as a branch/tool integration harness, not as manifold solidity evidence.",
        ],
        "why_not_v4_probes": (
            "This is a v5 formal scout falsifier over a v5 formal-scout receipt and its current "
            "PyTorch/provider-index integration surface; the v4 probe estate does not own this receipt contract."
        ),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "EXTERNAL_MODULE_MANIFEST": EXTERNAL_MODULE_MANIFEST,
        "EXTERNAL_MODULE_INTEGRATION_DEPTH": EXTERNAL_MODULE_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "promotion_allowed": PROMOTION_ALLOWED,
            "semantic_layer_claim_killed": bool(
                graveyard_companions["named_layer_semantics_claim_killed_for_parent_scout"]["pass"]
            ),
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return result


if __name__ == "__main__":
    main()
