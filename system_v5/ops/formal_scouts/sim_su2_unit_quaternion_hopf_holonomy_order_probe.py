#!/usr/bin/env python3
"""SU2 unit-quaternion action before Hopf holonomy order probe.

Formal-scout only. This composes existing v4 callable legos for exact SU2
unit-quaternion vector action and Hopf connection loop integrals, then checks
whether transport-before-holonomy keeps an order readout that nearby variants
collapse or invert.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import time
import traceback
from typing import Any

import sympy as sp


sys.dont_write_bytecode = True

ROOT = pathlib.Path(__file__).resolve().parents[3]
PROBES = ROOT / "system_v4" / "probes"
RESULT_DIR = pathlib.Path(__file__).resolve().parent / "results"
OUT_PATH = RESULT_DIR / "su2_unit_quaternion_hopf_holonomy_order_probe_results.json"

NAME = "su2_unit_quaternion_hopf_holonomy_order_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal-scout SU2 unit-quaternion and Hopf holonomy order probe only. "
    "It may guide later tower variants, but it does not admit a canonical "
    "manifold, physical flux, chirality, bridge, cycle, or target-system claim."
)

LEGO_PATHS = {
    "su2_unit_quaternion_action": PROBES / "sim_su2_unit_quaternion_vector_action_survivor_classes.py",
    "hopf_connection_loop_integral": PROBES / "sim_hopf_connection_one_form_loop_integral_survivor_classes.py",
}

TOOL_MANIFEST = {
    "importlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing imports from existing v4 callable legos",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact quaternion products and squared gaps",
    },
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "used through imported Hopf connection loop-integral callable",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "used through imported Hopf connection loop-integral callable",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "used through imported SU2 and Hopf boundary callables",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "importlib": "load_bearing",
    "sympy": "load_bearing",
    "pytorch": "supportive",
    "numpy": "supportive",
    "z3": "supportive",
}


def load_module(label: str, path: pathlib.Path) -> tuple[Any | None, dict[str, Any]]:
    if not path.exists():
        return None, {"status": "NOT_YET_TESTED", "path": str(path), "lego_load_error": "missing path"}
    parent = str(path.parent)
    if parent not in sys.path:
        sys.path.insert(0, parent)
    try:
        spec = importlib.util.spec_from_file_location(f"_formal_scout_{label}", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("spec loader missing")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, {"status": "SURVIVED", "path": str(path)}
    except Exception as exc:
        return None, {
            "status": "KILLED",
            "path": str(path),
            "lego_load_error": f"{type(exc).__name__}: {str(exc)[:240]}",
            "traceback": traceback.format_exc()[:600],
        }


def exact_su2_order_gap(su2_module: Any) -> dict[str, Any]:
    half = sp.sqrt(2) / 2
    qz = (half, sp.Integer(0), sp.Integer(0), half)
    qx = (half, half, sp.Integer(0), sp.Integer(0))
    vx = (sp.Integer(1), sp.Integer(0), sp.Integer(0))
    forward = su2_module.vector_action(su2_module.qmul(qx, qz), vx)
    reverse = su2_module.vector_action(su2_module.qmul(qz, qx), vx)
    gap = su2_module.squared_gap(forward, reverse)
    return {
        "first_product_image": [str(part) for part in forward],
        "second_product_image": [str(part) for part in reverse],
        "squared_gap": str(gap),
        "pass": int(gap) > 0,
    }


def holonomy_rows(hopf_module: Any) -> dict[str, Any]:
    fiber = hopf_module.fiber_loop_row()
    base = hopf_module.base_lift_loop_row()
    reverse = hopf_module.reversed_orientation_control()
    zero = hopf_module.zero_winding_control()
    hidden = hopf_module.hidden_connection_coordinate_control()
    return {
        "fiber_loop": fiber,
        "base_lift_loop": base,
        "reversed_orientation": reverse,
        "zero_winding": zero,
        "hidden_coordinate": hidden,
        "pass": fiber["passed"] and base["passed"] and reverse["passed"] and zero["passed"] and hidden["passed"],
    }


def ordered_tower(order_gap: dict[str, Any], holonomy: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "index": 0,
            "name": "finite_unit_quaternion_carrier",
            "parent_layer_index": None,
            "finite_witness": 2,
        },
        {
            "index": 1,
            "name": "unit_quaternion_vector_action",
            "parent_layer_index": 0,
            "order_gap": order_gap["squared_gap"],
            "finite_witness": 3,
        },
        {
            "index": 2,
            "name": "hopf_connection_loop_integral",
            "parent_layer_index": 1,
            "fiber_connection_integral": holonomy["fiber_loop"]["connection_integral"],
            "base_lift_connection_integral": holonomy["base_lift_loop"]["connection_integral"],
            "finite_witness": 5,
        },
    ]


def parent_links_pass(layers: list[dict[str, Any]]) -> bool:
    return (
        layers[0]["parent_layer_index"] is None
        and all(layers[idx]["parent_layer_index"] == idx - 1 for idx in range(1, len(layers)))
    )


def nearby_variants(order_gap: dict[str, Any], holonomy: dict[str, Any]) -> dict[str, Any]:
    variants = {
        "transport_order_visible": bool(order_gap["pass"]),
        "fiber_and_base_holonomy_visible": bool(holonomy["fiber_loop"]["passed"] and holonomy["base_lift_loop"]["passed"]),
        "reversed_orientation_inverts_readout": bool(holonomy["reversed_orientation"]["passed"]),
        "zero_winding_collapses_holonomy": bool(holonomy["zero_winding"]["passed"]),
        "hidden_coordinate_loses_connection_detail": bool(holonomy["hidden_coordinate"]["passed"]),
    }
    passed = sum(1 for value in variants.values() if value)
    return {"variants": variants, "total": len(variants), "passed": passed}


def main() -> dict[str, Any]:
    started = time.time()
    su2_module, su2_load = load_module("su2_unit_quaternion_action", LEGO_PATHS["su2_unit_quaternion_action"])
    hopf_module, hopf_load = load_module("hopf_connection_loop_integral", LEGO_PATHS["hopf_connection_loop_integral"])
    blockers = []
    if su2_module is None:
        blockers.append(su2_load)
    if hopf_module is None:
        blockers.append(hopf_load)

    positive: dict[str, Any] = {}
    graveyards: dict[str, Any] = {}
    boundary: dict[str, Any] = {}
    nearby: dict[str, Any] = {"total": 0, "passed": 0, "variants": {}}
    exact_callable_paths = {key: str(path) for key, path in LEGO_PATHS.items()}

    if not blockers:
        order_gap = exact_su2_order_gap(su2_module)
        holonomy = holonomy_rows(hopf_module)
        layers = ordered_tower(order_gap, holonomy)
        bad_layers = [dict(layer) for layer in layers]
        bad_layers[2]["parent_layer_index"] = None
        nonunit_norm = su2_module.qnorm2((sp.Integer(2), sp.Integer(0), sp.Integer(0), sp.Integer(0)))
        positive = {
            "v4_callable_legos_loaded": {
                "pass": su2_load["status"] == "SURVIVED" and hopf_load["status"] == "SURVIVED",
                "loads": {"su2": su2_load, "hopf": hopf_load},
            },
            "unit_quaternion_transport_order_has_nonzero_gap": order_gap,
            "hopf_connection_loop_integrals_survive": holonomy,
            "nested_parent_links_survive": {"pass": parent_links_pass(layers), "layers": layers},
        }
        graveyards = {
            "commuting_or_hidden_transport_would_collapse_order_readout": {
                "pass": order_gap["pass"],
                "observed_gap": order_gap["squared_gap"],
                "reason": "the actual imported SU2 products are noncommuting; a zero gap would kill this order readout",
            },
            "nonunit_quaternion_rejected": {
                "pass": nonunit_norm != 1,
                "nonunit_norm_square": str(nonunit_norm),
            },
            "zero_winding_collapses_connection_integral": {
                "pass": holonomy["zero_winding"]["passed"],
                "control": holonomy["zero_winding"],
            },
            "reversed_orientation_inverts_connection_integral": {
                "pass": holonomy["reversed_orientation"]["passed"],
                "control": holonomy["reversed_orientation"],
            },
            "missing_parent_link_fails_nested_order": {
                "pass": not parent_links_pass(bad_layers),
                "layers": bad_layers,
            },
        }
        boundary = {
            "su2_z3_unit_action_boundary": {
                "pass": su2_module.boundary_predicates(True, True, 1)["passed"],
                "raw": su2_module.boundary_predicates(True, True, 1),
            },
            "hopf_z3_orientation_boundary": hopf_module.z3_orientation_boundary(),
        }
        nearby = nearby_variants(order_gap, holonomy)

    all_pass = (
        not blockers
        and all(bool(row.get("pass")) for row in positive.values())
        and all(bool(row.get("pass")) for row in graveyards.values())
        and all(bool(row.get("pass") or row.get("passed")) for row in boundary.values())
        and nearby.get("passed") == nearby.get("total")
    )
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "observable": [
            "exact SU2 vector-action composition-order gap",
            "Hopf connection loop integral",
            "orientation reversal sign",
            "zero-winding collapse",
            "nested parent-link validity",
        ],
        "predicate": "imported SU2 transport order has a nonzero exact gap and imported Hopf connection loops survive while nearby controls collapse or invert",
        "boundary": boundary,
        "positive": positive,
        "graveyard_companions": graveyards,
        "nearby_variants": nearby,
        "blockers": blockers,
        "why_not_v4_probes": (
            "This is a new tower/order composition over existing v4 callable legos. "
            "It belongs in v5 formal-scout space because it is proposal-level and "
            "does not promote the v4 reference corpus."
        ),
        "exact_callable_paths": exact_callable_paths,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "summary": {
            "all_pass": bool(all_pass),
            "promotion_allowed": PROMOTION_ALLOWED,
            "elapsed_seconds": round(time.time() - started, 6),
            "next_step": "Compare against spinor/Clifford insertion and topology-cycle Hopf projection order variants.",
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()["summary"], indent=2, sort_keys=True))
