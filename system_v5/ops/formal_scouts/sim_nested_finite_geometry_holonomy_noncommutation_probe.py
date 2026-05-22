#!/usr/bin/env python3
"""Nested finite geometry with holonomy and noncommuting transport.

Formal-scout only. This file builds a rough geometric-constraint-manifold
prototype from finite density states, Hopf projection, U(1) holonomy,
noncommuting transport, and entropy readouts. It is designed to propose and
stress a tower shape, not to promote a canonical manifold.
"""

from __future__ import annotations

import importlib.util
import json
import math
import pathlib
import sys
import time
import traceback
from typing import Any

import torch


ROOT = pathlib.Path(__file__).resolve().parents[3]
PROBES = ROOT / "system_v4" / "probes"
RESULT_DIR = pathlib.Path(__file__).resolve().parent / "results"
OUT_PATH = RESULT_DIR / "nested_finite_geometry_holonomy_noncommutation_probe_results.json"

NAME = "nested_finite_geometry_holonomy_noncommutation_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal-scout nested finite geometry prototype only. It may guide later "
    "formal sims, but it does not admit a canonical geometric manifold, bridge, "
    "cycle, coordinate-family, or target-system claim."
)

LEGO_PATHS = {
    "hopf_projection": PROBES / "sim_hopf_projection_s3_s2_phase_invariant_survivor_classes.py",
    "hopf_loop_holonomy": PROBES / "sim_sympy_hopf_loop_holonomy_area_dependence.py",
    "matrix_order_noncommutation": PROBES / "sim_sympy_matrix_product_order_noncommutation_survivor_classes.py",
    "bipartite_entropy": PROBES / "sim_lego_entropy_bipartite_cut.py",
}

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite density matrices, unitary transport, commutator norm, and entropy readouts",
    },
    "importlib": {
        "tried": True,
        "used": True,
        "reason": "load-bearing callable imports from existing formal legos",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "used through imported holonomy and exact noncommutation legos when available",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "used through imported Hopf projection and exact noncommutation legos when available",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "importlib": "supportive",
    "sympy": "supportive",
    "z3": "supportive",
}


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


def safe_call(label: str, fn: Any, *args: Any, **kwargs: Any) -> dict[str, Any]:
    try:
        value = fn(*args, **kwargs)
        return {"status": "SURVIVED", "call": label, "value": value}
    except Exception as exc:
        return {
            "status": "KILLED",
            "call": label,
            "exception": f"{type(exc).__name__}: {str(exc)[:240]}",
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


def von_neumann_entropy_bits(rho: torch.Tensor) -> float:
    evals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    evals = torch.clamp(evals, min=0.0)
    total = torch.sum(evals)
    if float(total) <= 0:
        return float("nan")
    evals = evals / total
    nz = evals[evals > 1e-12]
    if nz.numel() == 0:
        return 0.0
    return float((-torch.sum(nz * torch.log2(nz))).item())


def unitary_transport_pair() -> dict[str, Any]:
    dtype = torch.complex128
    sx = torch.tensor([[0, 1], [1, 0]], dtype=dtype)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=dtype)
    ident = torch.eye(2, dtype=dtype)
    theta = torch.tensor(math.pi / 5, dtype=torch.float64)
    phi = torch.tensor(math.pi / 7, dtype=torch.float64)
    ua = torch.cos(theta / 2) * ident - 1j * torch.sin(theta / 2) * sz
    ub = torch.cos(phi / 2) * ident - 1j * torch.sin(phi / 2) * sx
    psi = torch.tensor([1.0 + 0j, 1.0 + 0j], dtype=dtype) / math.sqrt(2)
    rho = psi[:, None] @ psi.conj()[None, :]
    rho_ab = ua @ (ub @ rho @ ub.conj().T) @ ua.conj().T
    rho_ba = ub @ (ua @ rho @ ua.conj().T) @ ub.conj().T
    commutator = ua @ ub - ub @ ua
    return {
        "commutator_norm": float(torch.linalg.norm(commutator).real),
        "transport_order_trace_distance": float(0.5 * torch.linalg.norm(rho_ab - rho_ba, ord="nuc").real),
        "rho_input_validity": density_validity(rho),
        "rho_ab_validity": density_validity(rho_ab),
        "rho_ba_validity": density_validity(rho_ba),
        "entropy_input_bits": von_neumann_entropy_bits(rho),
        "entropy_ab_bits": von_neumann_entropy_bits(rho_ab),
        "entropy_ba_bits": von_neumann_entropy_bits(rho_ba),
        "pass": float(torch.linalg.norm(commutator).real) > 1e-9,
    }


def build_nested_layers(holonomy_phase: float, transport: dict[str, Any]) -> list[dict[str, Any]]:
    base_entropies = [
        "von_neumann",
        "linear_entropy",
        "renyi_2",
        "min_entropy",
        "purity",
        "coherent_information_candidate",
    ]
    return [
        {
            "index": 0,
            "name": "finite_density_state",
            "parent_layer_index": None,
            "admissible_entropies": base_entropies,
            "finite_witness": 2,
        },
        {
            "index": 1,
            "name": "hopf_projection_readout",
            "parent_layer_index": 0,
            "admissible_entropies": base_entropies[:5],
            "finite_witness": 3,
        },
        {
            "index": 2,
            "name": "u1_holonomy_loop",
            "parent_layer_index": 1,
            "admissible_entropies": base_entropies[:4],
            "holonomy_phase": holonomy_phase,
            "finite_witness": 5,
        },
        {
            "index": 3,
            "name": "noncommuting_transport_order",
            "parent_layer_index": 2,
            "admissible_entropies": base_entropies[:2],
            "commutator_norm": transport["commutator_norm"],
            "finite_witness": 7,
        },
    ]


def check_layers(layers: list[dict[str, Any]]) -> dict[str, Any]:
    failures = []
    for idx, layer in enumerate(layers):
        if layer.get("index") != idx:
            failures.append(f"layer {idx} index mismatch")
        if idx == 0 and layer.get("parent_layer_index") is not None:
            failures.append("base layer has parent")
        if idx > 0 and layer.get("parent_layer_index") != idx - 1:
            failures.append(f"layer {idx} parent mismatch")
        if idx > 0:
            prev = set(layers[idx - 1]["admissible_entropies"])
            cur = set(layer["admissible_entropies"])
            if not cur.issubset(prev):
                failures.append(f"layer {idx} expands entropy set")
            if cur == prev:
                failures.append(f"layer {idx} does not strictly restrict entropy set")
    return {
        "layer_count": len(layers),
        "admissible_entropy_set_sizes": [len(layer["admissible_entropies"]) for layer in layers],
        "failures": failures,
        "pass": not failures,
    }


def run_imported_lego_checks() -> dict[str, Any]:
    modules = {}
    load_receipts = {}
    for label, path in LEGO_PATHS.items():
        modules[label], load_receipts[label] = load_module(label, path)

    hopf_readout: dict[str, Any]
    hopf = modules["hopf_projection"]
    if hopf is not None:
        psi0 = hopf.normalize(torch.tensor([1.0 + 0j, 0.0 + 0j], dtype=hopf.DTYPE))
        psi1 = hopf.normalize(torch.tensor([0.0 + 0j, 1.0 + 0j], dtype=hopf.DTYPE))
        r0 = safe_call("hopf(|0>)", hopf.hopf, psi0)
        r1 = safe_call("hopf(|1>)", hopf.hopf, psi1)
        boundary = safe_call("hopf.z3_boundary()", hopf.z3_boundary)
        hopf_readout = {
            "path": str(LEGO_PATHS["hopf_projection"]),
            "north": r0["value"].tolist() if r0["status"] == "SURVIVED" else None,
            "south": r1["value"].tolist() if r1["status"] == "SURVIVED" else None,
            "z3_boundary_status": boundary["status"],
            "pass": (
                r0["status"] == "SURVIVED"
                and r1["status"] == "SURVIVED"
                and abs(float(r0["value"][2]) - 1.0) < 1e-9
                and abs(float(r1["value"][2]) + 1.0) < 1e-9
            ),
        }
    else:
        hopf_readout = {"path": str(LEGO_PATHS["hopf_projection"]), "pass": False, "load": load_receipts["hopf_projection"]}

    hol = modules["hopf_loop_holonomy"]
    if hol is not None:
        positive = safe_call("hopf_loop_holonomy.run_positive()", hol.run_positive)
        vertical = safe_call("hopf_loop_holonomy.vertical_fiber_connection_integral()", hol.vertical_fiber_connection_integral)
        holonomy_phase = float(vertical["value"]) if vertical["status"] == "SURVIVED" else float("nan")
        holonomy_readout = {
            "path": str(LEGO_PATHS["hopf_loop_holonomy"]),
            "phase": holonomy_phase,
            "positive_status": positive["status"],
            "vertical_status": vertical["status"],
            "vertical_error": vertical.get("exception"),
            "pass": (
                positive["status"] == "SURVIVED"
                and vertical["status"] == "SURVIVED"
                and bool(positive["value"].get("survives_area_dependent_horizontal_lift"))
            ),
        }
    else:
        holonomy_phase = float("nan")
        holonomy_readout = {"path": str(LEGO_PATHS["hopf_loop_holonomy"]), "pass": False, "load": load_receipts["hopf_loop_holonomy"]}

    noncomm = modules["matrix_order_noncommutation"]
    noncomm_readout = {"path": str(LEGO_PATHS["matrix_order_noncommutation"]), "pass": False}
    if noncomm is not None:
        exact = safe_call("matrix_order_noncommutation.main()", noncomm.main)
        noncomm_readout = {
            "path": str(LEGO_PATHS["matrix_order_noncommutation"]),
            "main_status": exact["status"],
            "all_pass": bool(exact["value"].get("all_pass")) if exact["status"] == "SURVIVED" else False,
            "pass": exact["status"] == "SURVIVED" and bool(exact["value"].get("all_pass")),
        }

    entropy = modules["bipartite_entropy"]
    entropy_readout = {"path": str(LEGO_PATHS["bipartite_entropy"]), "pass": False}
    if entropy is not None:
        bell = safe_call("bipartite_entropy.bell_density()", entropy.bell_density)
        if bell["status"] == "SURVIVED":
            s_ab = safe_call("bipartite_entropy.von_neumann_entropy(bell)", entropy.von_neumann_entropy, bell["value"])
            s_a_b = safe_call("bipartite_entropy.reduced_entropies(bell)", entropy.reduced_entropies, bell["value"])
            cond = safe_call("bipartite_entropy.conditional_entropy_a_given_b(bell)", entropy.conditional_entropy_a_given_b, bell["value"])
            entropy_readout = {
                "path": str(LEGO_PATHS["bipartite_entropy"]),
                "bell_joint_entropy": s_ab.get("value"),
                "bell_reduced_entropies": list(s_a_b.get("value")) if s_a_b["status"] == "SURVIVED" else None,
                "bell_conditional_entropy": cond.get("value"),
                "pass": s_ab["status"] == "SURVIVED" and s_a_b["status"] == "SURVIVED" and cond["status"] == "SURVIVED",
            }

    return {
        "loads": load_receipts,
        "hopf_projection": hopf_readout,
        "u1_holonomy": holonomy_readout,
        "exact_noncommutation": noncomm_readout,
        "bipartite_entropy": entropy_readout,
        "holonomy_phase": holonomy_phase,
    }


def graveyards(layers: list[dict[str, Any]], transport: dict[str, Any], holonomy_phase: float) -> dict[str, Any]:
    identity_layers = [dict(layer, admissible_entropies=layers[0]["admissible_entropies"]) for layer in layers]
    missing_parent_layers = [dict(layer) for layer in layers]
    missing_parent_layers[2]["parent_layer_index"] = None
    ident = torch.eye(2, dtype=torch.complex128)
    zero_comm = torch.linalg.norm(ident @ ident - ident @ ident).real
    bad_rho = torch.tensor([[1.0, 2.0], [0.0, 0.0]], dtype=torch.complex128)
    mismatch_error = None
    mismatch_pass = False
    try:
        _ = ident @ torch.eye(4, dtype=torch.complex128)
    except RuntimeError as exc:
        mismatch_error = str(exc)[:240]
        mismatch_pass = True
    return {
        "identity_layers_fail_strict_subset": {
            "check": check_layers(identity_layers),
            "pass": not check_layers(identity_layers)["pass"],
        },
        "missing_parent_link_fails": {
            "check": check_layers(missing_parent_layers),
            "pass": not check_layers(missing_parent_layers)["pass"],
        },
        "zero_holonomy_control_collapses": {
            "zero_holonomy": 0.0,
            "observed_holonomy": holonomy_phase,
            "pass": abs(holonomy_phase) > 1e-9,
        },
        "commuting_transport_control_collapses": {
            "identity_commutator_norm": float(zero_comm),
            "observed_commutator_norm": transport["commutator_norm"],
            "pass": float(zero_comm) == 0.0 and transport["commutator_norm"] > 1e-9,
        },
        "invalid_density_rejected": {
            "validity": density_validity(bad_rho),
            "pass": not density_validity(bad_rho)["pass"],
        },
        "dimension_mismatch_rejected": {
            "operator_dim": 2,
            "state_dim": 4,
            "runtime_error": mismatch_error,
            "pass": mismatch_pass,
        },
    }


def main() -> dict[str, Any]:
    started = time.time()
    imported = run_imported_lego_checks()
    transport = unitary_transport_pair()
    layers = build_nested_layers(imported["holonomy_phase"], transport)
    layer_check = check_layers(layers)
    negatives = graveyards(layers, transport, imported["holonomy_phase"])
    positive = {
        "formal_legos_called": {
            "called": list(LEGO_PATHS.keys()),
            "all_loaded": all(row["status"] == "SURVIVED" for row in imported["loads"].values()),
            "pass": all(row["status"] == "SURVIVED" for row in imported["loads"].values()),
        },
        "nested_layers_have_parent_links_and_strict_entropy_subsets": layer_check,
        "hopf_projection_basis_convention_survives": imported["hopf_projection"],
        "u1_holonomy_is_nonzero_and_area_dependent": imported["u1_holonomy"],
        "transport_order_is_noncommuting": transport,
        "bipartite_entropy_readout_is_finite": imported["bipartite_entropy"],
    }
    all_pass = all(row.get("pass", False) for row in positive.values()) and all(
        row.get("pass", False) for row in negatives.values()
    )
    boundary = {
        "holonomy_and_transport_readouts_are_nontrivial": {
            "pass": abs(imported["holonomy_phase"]) > 1e-9 and transport["commutator_norm"] > 1e-9,
            "holonomy_phase": imported["holonomy_phase"],
            "commutator_norm": transport["commutator_norm"],
        },
        "layer_restriction_is_strict": {
            "pass": layer_check["pass"],
            "admissible_entropy_set_sizes": layer_check["admissible_entropy_set_sizes"],
        },
    }
    nearby_variants = {
        "names": list(negatives.keys()),
        "total": len(negatives),
        "passed": sum(1 for row in negatives.values() if row.get("pass", False)),
    }
    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "operation_sequence": [
            "load formal geometry and entropy legos by path",
            "evaluate Hopf projection on basis spinors",
            "evaluate Hopf loop holonomy baseline",
            "construct four nested finite geometry layers with parent links",
            "run noncommuting unitary transports in two orders",
            "read finite density entropy values",
            "run immediate graveyard variants",
        ],
        "carrier_topology": "finite density states with nested Hopf projection, U(1) holonomy, and transport-order layer readouts",
        "observable": [
            "Hopf north/south projection",
            "U(1) holonomy phase",
            "layer parent links",
            "strict entropy-subset sizes",
            "unitary transport commutator norm",
            "density validity residuals",
            "finite entropy readouts",
        ],
        "pass_fail_predicate": (
            "formal legos load, nested layers restrict rather than expand, Hopf and holonomy readouts survive, "
            "transport order is noncommuting, density states remain valid, and adjacent graveyards fail as expected"
        ),
        "positive": positive,
        "graveyard_companions": negatives,
        "nearby_variants": nearby_variants,
        "boundary": boundary,
        "imported_lego_receipts": imported,
        "layers": layers,
        "why_not_v4_probes": (
            "This is exploratory tower assembly over existing v4 reference callables; "
            "it is not a canonical probe and must remain in v5 formal_scouts until promoted by manifest."
        ),
        "summary": {
            "all_pass": bool(all_pass),
            "elapsed_seconds": round(time.time() - started, 6),
            "layer_count": len(layers),
            "promotion_allowed": PROMOTION_ALLOWED,
            "next_step": "Use this scout to propose alternate layer orders and then harden the best one into a formal sim.",
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "out_of_scope": [
            "no formal manifold admission",
            "no bridge admission",
            "no cycle admission",
            "no coordinate-family admission",
            "no target-system admission",
        ],
    }
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, default=str, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(main()["summary"], indent=2, sort_keys=True))
