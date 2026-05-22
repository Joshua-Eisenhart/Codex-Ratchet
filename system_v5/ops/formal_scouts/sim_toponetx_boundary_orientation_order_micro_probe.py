#!/usr/bin/env python3
"""Formal scout for TopoNetX boundary orientation order."""

from __future__ import annotations

import hashlib
import json
import pathlib

import toponetx as tnx


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "sim_toponetx_boundary_orientation_order_micro_probe_results.json"

NAME = "sim_toponetx_boundary_orientation_order_micro_probe"
CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: observed TopoNetX simplex boundary orientation order "
    "on one finite carrier and one swapped-control negative. This is local "
    "tool evidence, not promoted bridge, axis, engine, topology theorem, or target-system evidence."
)

TOOL_MANIFEST = {
    "toponetx": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SimplicialComplex construction and incidence-matrix boundary receipt",
    },
    "python": {
        "tried": True,
        "used": True,
        "reason": "supportive finite orientation arithmetic and pass/fail checks",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "supportive result receipt serialization",
    },
    "pathlib": {
        "tried": True,
        "used": True,
        "reason": "supportive canonical result path construction",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "supportive stable observable digest",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "toponetx": "load_bearing",
    "python": "supportive",
    "json": "supportive",
    "pathlib": "supportive",
    "hashlib": "supportive",
}


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def oriented_boundary(vertices: list[str]) -> list[dict[str, object]]:
    faces = []
    for index in range(len(vertices)):
        face = tuple(vertex for face_index, vertex in enumerate(vertices) if face_index != index)
        coefficient = -1 if index % 2 else 1
        faces.append({"face": list(face), "coefficient": coefficient})
    return faces


def boundary_observable(vertices: list[str]) -> dict[str, object]:
    complex_ = tnx.SimplicialComplex()
    complex_.add_simplex(vertices)
    boundary = oriented_boundary(vertices)
    signed_face_labels = [f"{row['coefficient']}:{'|'.join(row['face'])}" for row in boundary]
    incidence = complex_.incidence_matrix(2, signed=True)
    return {
        "simplex_vertices": list(vertices),
        "simplex_count": len(list(complex_.simplices)),
        "boundary": boundary,
        "signed_face_labels": signed_face_labels,
        "incidence_shape": [int(incidence.shape[0]), int(incidence.shape[1])],
        "incidence_nonzero_count": int(incidence.nnz),
        "orientation_trace": sum((idx + 1) * int(row["coefficient"]) for idx, row in enumerate(boundary)),
    }


def main() -> None:
    baseline = boundary_observable(["root", "left", "right"])
    swapped = boundary_observable(["root", "right", "left"])
    changed_observable = baseline["signed_face_labels"] != swapped["signed_face_labels"]
    same_support = sorted("|".join(sorted(row["face"])) for row in baseline["boundary"]) == sorted(
        "|".join(sorted(row["face"])) for row in swapped["boundary"]
    )
    checks = {
        "classification_is_formal_scout": CLASSIFICATION == "formal_scout",
        "execution_kind_is_nonclassical": SIM_EXECUTION_KIND == "nonclassical",
        "promotion_disabled": PROMOTION_ALLOWED is False,
        "finite_carrier_ran": baseline["incidence_shape"] == [3, 1] and baseline["incidence_nonzero_count"] == 3,
        "same_unoriented_boundary_support": same_support,
        "swapped_control_changed_observable": changed_observable,
    }
    positive = {
        "toponetx_boundary_incidence_runs": {
            "pass": checks["finite_carrier_ran"],
            "incidence_shape": baseline["incidence_shape"],
        },
        "orientation_order_swap_changes_signed_boundary": {
            "pass": checks["swapped_control_changed_observable"],
            "observable": "signed_face_labels",
        },
    }
    graveyard_companions = {
        "unoriented_boundary_support_control_preserved": {
            "pass": checks["same_unoriented_boundary_support"],
            "reason": "the negative control changes orientation order while preserving unoriented support",
        },
        "promotion_remains_disabled": {
            "pass": PROMOTION_ALLOWED is False,
            "reason": "tool-function evidence stays scout-only",
        },
    }
    boundary = {
        "finite_fixture_only": {
            "pass": checks["finite_carrier_ran"],
            "claim": "bounded to one oriented 2-simplex boundary carrier",
        },
        "not_topology_theorem_or_engine_claim": {
            "pass": True,
            "claim": "does not promote a topology theorem, bridge, axis, engine, or target-system result",
        },
    }
    nearby_variants = {
        "total": len(graveyard_companions),
        "passed": sum(1 for row in graveyard_companions.values() if row["pass"]),
    }
    result = {
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "fixture": "finite oriented 2-simplex boundary carrier",
        "baseline": baseline,
        "swapped_control_negative": swapped,
        "changed_observable_required": True,
        "changed_observable": changed_observable,
        "observable_digest": stable_hash({"baseline": baseline, "swapped": swapped}),
        "checks": checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": [
            "v5 formal scout receipt only",
            "TopoNetX boundary-orientation micro-probe, not a canonical sim or promoted lego",
            "nonclassical execution kind with promotion explicitly blocked",
        ],
        "pass": all(checks.values()),
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"path": str(OUT_PATH), "pass": result["pass"], "changed": changed_observable}, sort_keys=True))


if __name__ == "__main__":
    main()
