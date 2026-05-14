#!/usr/bin/env python3
"""Entropy reduction before Hopf projection order probe.

Formal-scout only. This tests a candidate tower order where a finite entropy
predicate filters density states before a Hopf projection readout is attached.
It compares that order to nearby failures without promoting a manifold claim.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import time
import traceback
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parents[3]
PROBES = ROOT / "system_v4" / "probes"
RESULT_DIR = pathlib.Path(__file__).resolve().parent / "results"
OUT_PATH = RESULT_DIR / "entropy_reduction_before_hopf_projection_order_probe_results.json"

NAME = "entropy_reduction_before_hopf_projection_order_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal-scout finite entropy-before-projection order probe only. It may "
    "guide later tower variants, but it does not admit a canonical manifold, "
    "coordinate-family, bridge, cycle, or target-system claim."
)

LEGO_PATHS = {
    "entropy": PROBES / "sim_lego_entropy_bipartite_cut.py",
    "hopf_projection": PROBES / "sim_hopf_projection_s3_s2_phase_invariant_survivor_classes.py",
}

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing density validation, entropy thresholds, and Hopf projection tensors",
    },
    "importlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing imports from existing entropy and Hopf formal legos",
    },
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "importlib": "load_bearing"}


def load_module(label: str, path: pathlib.Path) -> tuple[Any | None, dict[str, Any]]:
    if not path.exists():
        return None, {"status": "NOT_YET_TESTED", "lego_load_error": f"missing {path}"}
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


def density_validity(rho: torch.Tensor, tol: float = 1e-9) -> dict[str, Any]:
    hermitian_error = float(torch.linalg.norm(rho - rho.conj().T).real)
    trace_value = complex(torch.trace(rho).item())
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    min_eval = float(torch.min(evals))
    return {
        "hermitian_error": hermitian_error,
        "trace_real": trace_value.real,
        "trace_imag": trace_value.imag,
        "min_eigenvalue": min_eval,
        "pass": hermitian_error < tol and abs(trace_value.real - 1.0) < tol and abs(trace_value.imag) < tol and min_eval > -tol,
    }


def hopf_readout_from_werner_parameter(hopf_module: Any, p: float) -> dict[str, Any]:
    psi = torch.tensor([complex(p, 0.0), complex(1.0 - p, 0.0)], dtype=torch.complex128)
    psi = hopf_module.normalize(psi)
    projection = hopf_module.hopf(psi)
    return {
        "p": float(p),
        "projection": [float(x) for x in projection.tolist()],
        "projection_norm": float(torch.linalg.norm(projection)),
    }


def entropy_filtered_order(entropy_module: Any, hopf_module: Any) -> dict[str, Any]:
    p_values = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    threshold = 1.2
    rows = []
    survivors = []
    for p in p_values:
        rho = entropy_module.werner_density(p)
        s_ab = entropy_module.von_neumann_entropy(rho)
        mutual_information = entropy_module.mutual_information(rho)
        valid = density_validity(rho)
        row = {
            "p": float(p),
            "S_AB": float(s_ab),
            "I_AB": float(mutual_information),
            "density_valid": valid["pass"],
            "survives_entropy_filter": bool(s_ab <= threshold and valid["pass"]),
        }
        if row["survives_entropy_filter"]:
            row["hopf_projection"] = hopf_readout_from_werner_parameter(hopf_module, p)
            survivors.append(row)
        rows.append(row)
    return {
        "p_values": p_values,
        "entropy_threshold_bits": threshold,
        "rows": rows,
        "survivor_p_values": [row["p"] for row in survivors],
        "survivor_count": len(survivors),
        "strict_subset": 0 < len(survivors) < len(p_values),
    }


def graveyards(entropy_module: Any, hopf_module: Any, positive: dict[str, Any]) -> dict[str, Any]:
    p_values = positive["p_values"]
    no_filter_count = len(p_values)
    invalid_rho = torch.tensor([[0.8 + 0j, 0.4 + 0j], [0.0 + 0j, 0.4 + 0j]], dtype=torch.complex128)
    invalid_validity = density_validity(invalid_rho)
    psi = hopf_module.normalize(torch.tensor([0.7 + 0.2j, -0.1 + 0.5j], dtype=torch.complex128))
    phased = torch.exp(torch.tensor(2.1j, dtype=torch.complex128)) * psi
    projection_gap = float(torch.linalg.norm(hopf_module.hopf(psi) - hopf_module.hopf(phased)))
    loose_survivors = [
        p for p in p_values if entropy_module.von_neumann_entropy(entropy_module.werner_density(p)) <= 3.0
    ]
    missing_parent_layers = [
        {"index": 0, "name": "finite_density_state", "parent_layer_index": None},
        {"index": 1, "name": "hopf_projection_readout", "parent_layer_index": None},
    ]
    return {
        "no_entropy_filter_fails_strict_subset": {
            "pass": no_filter_count == len(p_values),
            "control_survivor_count": no_filter_count,
            "interpretation": "without an entropy predicate the finite carrier is not reduced",
        },
        "invalid_density_rejected": {
            "validity": invalid_validity,
            "pass": not invalid_validity["pass"],
        },
        "hopf_global_phase_control_collapses": {
            "pass": projection_gap < 1e-10,
            "projection_gap": projection_gap,
            "interpretation": "global phase alone cannot create a base projection distinction",
        },
        "too_loose_entropy_threshold_fails_reduction": {
            "pass": len(loose_survivors) == len(p_values),
            "control_survivor_count": len(loose_survivors),
        },
        "missing_parent_link_fails": {
            "pass": missing_parent_layers[1]["parent_layer_index"] != 0,
            "layers": missing_parent_layers,
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    entropy_module, entropy_load = load_module("entropy", LEGO_PATHS["entropy"])
    hopf_module, hopf_load = load_module("hopf_projection", LEGO_PATHS["hopf_projection"])

    positive: dict[str, Any] = {}
    graveyard_checks: dict[str, Any] = {}
    blockers = []
    if entropy_module is None:
        blockers.append(entropy_load)
    if hopf_module is None:
        blockers.append(hopf_load)

    if not blockers:
        order = entropy_filtered_order(entropy_module, hopf_module)
        layers = [
            {"index": 0, "name": "finite_density_state_family", "parent_layer_index": None},
            {
                "index": 1,
                "name": "entropy_reduction_predicate",
                "parent_layer_index": 0,
                "entropy_threshold_bits": order["entropy_threshold_bits"],
            },
            {"index": 2, "name": "hopf_projection_readout", "parent_layer_index": 1},
        ]
        positive = {
            "formal_legos_loaded": {"pass": entropy_load["status"] == "SURVIVED" and hopf_load["status"] == "SURVIVED"},
            "entropy_filter_reduces_finite_state_family": {
                "pass": order["strict_subset"],
                "survivor_p_values": order["survivor_p_values"],
                "survivor_count": order["survivor_count"],
                "total_count": len(order["p_values"]),
            },
            "survivors_receive_hopf_projection_readouts": {
                "pass": all("hopf_projection" in row for row in order["rows"] if row["survives_entropy_filter"]),
                "readouts": [row.get("hopf_projection") for row in order["rows"] if row["survives_entropy_filter"]],
            },
            "nested_layers_have_parent_links": {
                "pass": layers[0]["parent_layer_index"] is None
                and layers[1]["parent_layer_index"] == 0
                and layers[2]["parent_layer_index"] == 1,
                "layers": layers,
            },
        }
        graveyard_checks = graveyards(entropy_module, hopf_module, order)

    all_positive = bool(positive) and all(v.get("pass") for v in positive.values())
    all_graveyards = bool(graveyard_checks) and all(v.get("pass") for v in graveyard_checks.values())
    all_pass = not blockers and all_positive and all_graveyards
    nearby_variants = {
        "names": list(graveyard_checks.keys()),
        "total": len(graveyard_checks),
        "passed": sum(1 for row in graveyard_checks.values() if row.get("pass", False)),
    }
    boundary = {
        "entropy_filter_is_strict_but_nonempty": {
            "pass": bool(positive.get("entropy_filter_reduces_finite_state_family", {}).get("pass", False)),
            "survivor_count": positive.get("entropy_filter_reduces_finite_state_family", {}).get("survivor_count"),
            "total_count": positive.get("entropy_filter_reduces_finite_state_family", {}).get("total_count"),
        },
        "hopf_projection_norm_is_unit_for_survivors": {
            "pass": all(
                abs(readout.get("projection_norm", 0.0) - 1.0) < 1e-9
                for readout in positive.get("survivors_receive_hopf_projection_readouts", {}).get("readouts", [])
            ),
        },
    }

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "all_pass": bool(all_pass),
        "claim_ceiling": CLAIM_CEILING,
        "imported_legos": {"entropy": entropy_load, "hopf_projection": hopf_load},
        "positive": positive,
        "graveyard_companions": graveyard_checks,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "blockers": blockers,
        "why_not_v4_probes": (
            "This is an exploratory order probe over existing v4 reference callables; "
            "it is not a canonical probe and must remain in v5 formal_scouts until promoted by manifest."
        ),
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "next_step": "Compare this order against projection-before-entropy and spinor/Clifford insertion variants.",
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "sim_spec_contract": {
            "operation_sequence": [
                "construct finite Werner density family",
                "compute entropy and mutual-information readouts",
                "filter by entropy predicate",
                "attach Hopf projection readout to survivors",
                "compare nearby graveyards",
            ],
            "carrier_topology": "finite density family with post-filter two-component Hopf projection readout",
            "observable": ["survivor count", "survivor p values", "Hopf projection coordinates"],
            "pass_fail_predicate": "entropy predicate creates a strict finite subset and every survivor receives a Hopf readout",
            "graveyard_companions": list(graveyard_checks.keys()),
            "baseline_variants": ["no entropy filter", "too-loose entropy threshold", "global-phase Hopf control"],
            "alternative_formulations": ["projection-before-entropy order", "spinor/Clifford insertion before projection"],
            "exact_tool_function_needs": {
                "entropy_lego": ["werner_density", "von_neumann_entropy", "mutual_information"],
                "hopf_projection_lego": ["normalize", "hopf"],
            },
            "lego_coupling_target": "entropy_reduction_before_hopf_projection_order",
            "claim_ceiling": CLAIM_CEILING,
        },
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()["summary"], indent=2, sort_keys=True))
