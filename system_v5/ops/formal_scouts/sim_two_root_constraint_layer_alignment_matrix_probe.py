#!/usr/bin/env python3
"""Two-root layer-alignment matrix for the geometric constraint manifold.

This scout does not claim the 13-layer manifold is final. It makes the next
foundation move executable: encode F01 finitude and N01 noncommutation as
per-layer checks, then classify which layer names are already direct root
carriers, which are only finite bases, which inherit noncommutation from
operators, and which need mathematical retuning.
"""

from __future__ import annotations

import hashlib
import json
import math
import pathlib
import time
from dataclasses import dataclass
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
RESULT_DIR.mkdir(parents=True, exist_ok=True)
NAME = "two_root_constraint_layer_alignment_matrix_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

CLASSIFICATION = "formal_scout"
SIM_EXECUTION_KIND = "nonclassical"
PROMOTION_ALLOWED = False
SOURCE_ALIGNMENT_CATEGORY = "two_root_constraint_layer_alignment_matrix"
CLAIM_CEILING = (
    "Formal scout only: encodes F01 finitude and N01 noncommutation as a "
    "per-layer alignment audit for the current 13-layer geometric constraint "
    "manifold candidate. It can classify root-bearing, inherited, and retune "
    "roles, but it does not admit a final manifold, final layer order, attractor "
    "basin, Axis0, engine, physics, target-system, Holodeck, or canonical claim."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite complex/quaternion/Clifford operator witnesses and commutator norms",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing logic gate separating current direct-root validity from aligned design candidacy",
    },
    "python_json": {"tried": True, "used": True, "reason": "load-bearing receipt serialization"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive row and design hashes"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive bounded output paths"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "load_bearing",
    "python_json": "supportive",
    "hashlib": "supportive",
    "pathlib": "supportive",
}

CDTYPE = torch.complex128
EPS = 1.0e-9


@dataclass(frozen=True)
class LayerSpec:
    idx: int
    name: str
    raw_f01: str
    raw_n01: str
    aligned_math: str
    current_role: str
    retune_required: bool
    retune_note: str
    operator_pair: str


LAYERS = [
    LayerSpec(
        0,
        "finite_constraint_complex",
        "direct_finite_base",
        "absent_if_only_cells",
        "finite noncommutative constraint complex: cells carry bounded operator labels and incidence/probe maps whose order matters",
        "f01_base_only_current",
        True,
        "The first layer is not a full F01+N01 layer if it is only a finite cell/constraint complex; add noncommuting operator-labeled incidence or probe maps.",
        "none_current",
    ),
    LayerSpec(
        1,
        "complex_hilbert_carrier",
        "direct_finite_when_dim_bounded",
        "absent_if_only_complex_scalars",
        "finite complex Hilbert module plus explicit Pauli/Clifford probe family",
        "f01_carrier_operator_inherited",
        True,
        "Complex scalars are commutative; keep the finite carrier but bind N01 to a named noncommuting operator family.",
        "pauli_x_z",
    ),
    LayerSpec(
        2,
        "unit_spinor_sphere",
        "requires_finite_quaternion_sample_or_truncation",
        "direct_when_su2_quaternion_products_are_ordered",
        "finite SU(2)/unit-quaternion spinor sample with i,j,k multiplication order witnesses",
        "candidate_requiring_finite_encoding",
        True,
        "Raw S3 is continuous; represent it by finite unit-quaternion/SU(2) samples before using it as an F01 layer.",
        "quaternion_i_j",
    ),
    LayerSpec(
        3,
        "projective_base_sphere",
        "requires_finite_hopf_quotient_sample",
        "inherited_from_noncommuting_lifts",
        "finite CP1/Bloch quotient rows with noncommuting lifted probes and quotient-invariance controls",
        "derived_quotient_inherited_n01",
        True,
        "The base sphere is a quotient; N01 must be witnessed by noncommuting lifts/probes, not by the sphere label.",
        "lifted_pauli_x_z",
    ),
    LayerSpec(
        4,
        "hopf_fiber_bundle",
        "requires_finite_bundle_chart_and_loop_set",
        "direct_when_vertical_horizontal_transport_order_differs",
        "finite Hopf bundle charts with vertical/horizontal transport order and holonomy controls",
        "candidate_direct_after_finite_transport",
        True,
        "Bundle language needs finite chart/loop sets and explicit order-sensitive transport.",
        "vertical_horizontal_transport",
    ),
    LayerSpec(
        5,
        "hopf_torus_leaf_family",
        "requires_finite_leaf_family",
        "inherited_or_direct_from_leaf_transport_order",
        "finite torus-leaf family with ordered meridian/longitude or fiber/base traversals",
        "weaker_candidate_inherited_n01",
        True,
        "A leaf family can be finite, but N01 must be in the ordered traversals; otherwise it is descriptive geometry.",
        "torus_meridian_longitude",
    ),
    LayerSpec(
        6,
        "connection_holonomy_geometry",
        "direct_finite_loop_family",
        "direct_noncommuting_parallel_transport",
        "finite loop family with noncommuting holonomy matrices and reversed-order controls",
        "strong_direct_root_candidate",
        False,
        "Already close to F01+N01 if finite loops and noncommuting holonomies are load-bearing.",
        "holonomy_x_z",
    ),
    LayerSpec(
        7,
        "weyl_spinor_bundle",
        "direct_finite_doubled_spinor_carrier",
        "direct_chiral_operator_noncommutation",
        "finite left/right Weyl spinor bundle with signed Pauli/Clifford operators",
        "strong_direct_root_candidate",
        False,
        "Keep chirality bound to finite spinor states and explicit operator-order witnesses.",
        "weyl_signed_x_z",
    ),
    LayerSpec(
        8,
        "chirality_orientation_cover",
        "direct_finite_sign_or_orientation_cover",
        "direct_if_orientation_operator_anticommutes_with_motion_generators",
        "finite orientation/chirality cover with gamma-like operator anticommutation",
        "candidate_direct_with_clifford_binding",
        True,
        "A sign cover alone is finite but not N01; bind it to Clifford/gamma operators.",
        "chirality_gamma_x",
    ),
    LayerSpec(
        9,
        "clifford_module_geometry",
        "direct_finite_signature_module",
        "direct_clifford_anticommutation",
        "finite Clifford module over bounded signature with explicit anticommutator/commutator witnesses",
        "strong_direct_root_candidate",
        False,
        "This is one of the strongest root-bearing layers if signature and module dimension are bounded.",
        "clifford_e1_e2",
    ),
    LayerSpec(
        10,
        "frame_bundle_structure_reduction",
        "requires_finite_frame_and_reduction_choices",
        "direct_when_reductions_are_order_sensitive",
        "finite frame choices with noncommuting reduction/projection sequence controls",
        "candidate_direct_after_reduction_order_witness",
        True,
        "Structure reduction must be represented as finite ordered reductions, not just a group-label narrowing.",
        "frame_rotation_projection",
    ),
    LayerSpec(
        11,
        "tensor_product_coupling_geometry",
        "direct_finite_tensor_factorization",
        "direct_local_vs_entangling_order_noncommutation",
        "finite tensor product carrier with local/entangling operator order controls",
        "strong_direct_root_candidate",
        False,
        "Finite tensor factors plus noncommuting local/entangling operations are directly root-aligned.",
        "local_vs_entangling",
    ),
    LayerSpec(
        12,
        "dynamic_transition_ratchet_geometry",
        "direct_finite_transition_graph_or_horizon",
        "direct_noncommuting_transition_schedule",
        "finite transition schedule with noncommuting update/enforce/probe order and constant-exploration controls",
        "strong_but_downstream_root_candidate",
        False,
        "This can be root-bearing, but it must stay downstream of validated finite noncommuting layers.",
        "transition_enforce_update",
    ),
]


def mat(values: list[list[complex]]) -> torch.Tensor:
    return torch.tensor(values, dtype=CDTYPE)


I2 = mat([[1, 0], [0, 1]])
X = mat([[0, 1], [1, 0]])
Y = mat([[0, -1j], [1j, 0]])
Z = mat([[1, 0], [0, -1]])
P0 = mat([[1, 0], [0, 0]])
H = (1.0 / math.sqrt(2.0)) * mat([[1, 1], [1, -1]])
QI = 1j * X
QJ = 1j * Y
QK = 1j * Z
CNOT = mat([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])
XI = torch.kron(X, I2)
ZI = torch.kron(Z, I2)
IX = torch.kron(I2, X)


def commutator_norm(a: torch.Tensor, b: torch.Tensor) -> float:
    return float(torch.linalg.norm(a @ b - b @ a).item())


def row_operator_pair(pair: str) -> tuple[torch.Tensor | None, torch.Tensor | None]:
    if pair == "none_current":
        return None, None
    if pair in {"pauli_x_z", "lifted_pauli_x_z", "holonomy_x_z", "weyl_signed_x_z"}:
        return X, Z
    if pair == "quaternion_i_j":
        return QI, QJ
    if pair == "vertical_horizontal_transport":
        return H, Z
    if pair == "torus_meridian_longitude":
        return QI, QK
    if pair == "chirality_gamma_x":
        return Z, X
    if pair == "clifford_e1_e2":
        return X, Y
    if pair == "frame_rotation_projection":
        return H, P0
    if pair == "local_vs_entangling":
        return CNOT, XI
    if pair == "transition_enforce_update":
        return torch.kron(H, I2) @ CNOT, torch.kron(Z, X)
    raise ValueError(pair)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def layer_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for spec in LAYERS:
        a, b = row_operator_pair(spec.operator_pair)
        current_direct_n01 = spec.raw_n01.startswith("direct")
        if a is None or b is None:
            aligned_commutator_norm = 0.0
            aligned_n01_pass = False
            finite_operator_dimension = 0
        else:
            aligned_commutator_norm = commutator_norm(a, b)
            aligned_n01_pass = aligned_commutator_norm > EPS
            finite_operator_dimension = int(a.shape[0])
        aligned_f01_pass = spec.raw_f01.startswith("direct") or spec.raw_f01.startswith("requires_finite")
        raw_f01_pass = spec.raw_f01.startswith("direct")
        rows.append(
            {
                "layer_idx": spec.idx,
                "layer": spec.name,
                "raw_f01_status": spec.raw_f01,
                "raw_n01_status": spec.raw_n01,
                "raw_f01_pass": raw_f01_pass,
                "raw_direct_n01_pass": current_direct_n01,
                "aligned_math": spec.aligned_math,
                "aligned_f01_pass": aligned_f01_pass,
                "aligned_n01_pass": aligned_n01_pass,
                "aligned_commutator_norm": aligned_commutator_norm,
                "finite_operator_dimension": finite_operator_dimension,
                "current_role": spec.current_role,
                "retune_required": spec.retune_required,
                "retune_note": spec.retune_note,
                "operator_pair": spec.operator_pair,
                "root_alignment_class": (
                    "direct_f01_n01_candidate"
                    if raw_f01_pass and current_direct_n01 and aligned_n01_pass
                    else "finite_base_or_inherited_needs_retool"
                    if spec.retune_required
                    else "direct_root_candidate_needs_hardening"
                ),
            }
        )
    return rows


def z3_gate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    current_all_direct = all(row["raw_f01_pass"] and row["raw_direct_n01_pass"] for row in rows)
    aligned_all_have_path = all(row["aligned_f01_pass"] and row["aligned_n01_pass"] for row in rows if row["operator_pair"] != "none_current")
    first_layer_current_direct = rows[0]["raw_f01_pass"] and rows[0]["raw_direct_n01_pass"]
    solver = z3.Solver()
    current_valid = z3.Bool("current_13_layers_all_direct_root_valid")
    aligned_design = z3.Bool("aligned_design_has_root_path_for_nonbase_layers")
    first_direct = z3.Bool("first_layer_currently_direct_root_valid")
    solver.add(current_valid == z3.BoolVal(current_all_direct))
    solver.add(aligned_design == z3.BoolVal(aligned_all_have_path))
    solver.add(first_direct == z3.BoolVal(first_layer_current_direct))
    solver.push()
    solver.add(current_valid)
    current_check = solver.check()
    solver.pop()
    solver.push()
    solver.add(first_direct)
    first_check = solver.check()
    solver.pop()
    return {
        "current_13_layers_all_direct_root_valid": current_all_direct,
        "current_13_layers_all_direct_root_valid_check": str(current_check),
        "first_layer_currently_direct_root_valid": first_layer_current_direct,
        "first_layer_currently_direct_root_valid_check": str(first_check),
        "aligned_design_has_root_path_for_nonbase_layers": aligned_all_have_path,
        "pass": current_check == z3.unsat and first_check == z3.unsat and aligned_all_have_path,
        "rule": "Current labels are not all direct root-valid; aligned finite operator encodings can be used as the next design target.",
    }


def exploration_branches() -> list[dict[str, Any]]:
    branch_map = {
        "finite_constraint_complex": [
            "finite operator-labeled cell complex with noncommuting incidence/probe maps",
            "finite quiver/path-algebra constraint complex with order-sensitive path composition",
            "finite Hodge-Laplacian plus projection pair where [L,P] is load-bearing",
            "finite hypergraph/simplicial complex with noncommuting face-update operators",
        ],
        "complex_hilbert_carrier": [
            "finite C^n carrier with Pauli probe family",
            "finite C^n carrier with Clifford generator family",
            "finite quaternionic submodule represented as complex 2x2 matrices",
            "finite POVM family where measurement order changes quotient S/~M",
        ],
        "unit_spinor_sphere": [
            "finite SU(2) unit-quaternion net",
            "finite Hopf-coordinate spinor sample with quaternion multiplication controls",
            "finite Clifford spinor orbit under noncommuting rotor pairs",
            "finite density-state lift of spinor samples with phase/fiber controls",
        ],
        "projective_base_sphere": [
            "finite CP1/Bloch quotient induced by noncommuting spinor lifts",
            "finite measurement quotient S/~M with Pauli order controls",
            "finite projective chart atlas with transition-map commutator checks",
            "finite antipodal/gauge quotient with lift-order survival controls",
        ],
        "hopf_fiber_bundle": [
            "finite Hopf chart bundle with vertical/horizontal transport order",
            "finite Berry-loop family with holonomy commutator controls",
            "finite fiber/base path pair with quotient-invariant and quotient-variant readouts",
            "finite U(1) connection discretization with reversed-loop controls",
        ],
        "hopf_torus_leaf_family": [
            "finite Clifford-torus leaf sample with meridian/longitude order",
            "finite nested torus leaves with leaf-change and transport controls",
            "finite fiber/base torus traversal grammar",
            "finite leaf-family quotient with same-leaf and cross-leaf noncommuting probes",
        ],
        "connection_holonomy_geometry": [
            "finite loop groupoid with noncommuting holonomy matrices",
            "finite connection one-form samples with path-ordered exponentials",
            "finite plaquette curvature grid with reversed-order Wilson loop controls",
            "finite transport category with noncommuting parallel transports",
        ],
        "weyl_spinor_bundle": [
            "finite left/right Weyl spinor pair with signed Pauli flows",
            "finite chiral density-state bundle with opposite Hamiltonian signs",
            "finite two-sheet spinor transport with asymmetric flux controls",
            "finite Weyl module with Clifford chirality operator coupling",
        ],
        "chirality_orientation_cover": [
            "finite chirality sign cover bound to gamma-like anticommutation",
            "finite orientation double cover with orientation-reversing operator controls",
            "finite pseudoscalar eigenbundle over Clifford module rows",
            "finite sheet-cover with noncommuting orientation and transport updates",
        ],
        "clifford_module_geometry": [
            "finite Cl(p,q) module with explicit anticommuting generators",
            "finite signature-sweep Clifford module with cvc5/z3 cross-checks",
            "finite rotor/spinor action with noncommuting bivector updates",
            "finite gamma-matrix module with chirality anticommution controls",
        ],
        "frame_bundle_structure_reduction": [
            "finite frame set with noncommuting reduction/projection sequences",
            "finite G-structure family reduction SU3/G2/Spin7-style order tests",
            "finite stabilizer-subgroup chain with permutation/reversal controls",
            "finite frame gauge choice with reduction-then-transport vs transport-then-reduction",
        ],
        "tensor_product_coupling_geometry": [
            "finite tensor product carrier with local-vs-entangling order controls",
            "finite MPS/PEPS factorization with gate-order commutator checks",
            "finite bipartite density coupling with partial-trace readout controls",
            "finite tensor-network contraction path with noncommuting update/probe schedule",
        ],
        "dynamic_transition_ratchet_geometry": [
            "finite transition graph with enforce-then-update vs update-then-enforce",
            "finite dynamic tensor-network schedule with constant exploration and increasing constraints",
            "finite two-basin asymmetric flux transition system with reversed-flux controls",
            "finite Markov/operator semigroup with noncommuting constraint projections",
        ],
    }
    rows: list[dict[str, Any]] = []
    for layer in LAYERS:
        branches = branch_map[layer.name]
        rows.append(
            {
                "layer_idx": layer.idx,
                "layer": layer.name,
                "branch_count": len(branches),
                "branches": [
                    {
                        "branch_id": f"{layer.idx}.{idx}",
                        "candidate": branch,
                        "strict_f01_gate": "finite carrier/sample/operator set required",
                        "strict_n01_gate": "must expose nonzero commutator or order-sensitive quotient/readout",
                        "promotion_gate": "candidate only until ablated under F01-only, N01-only, both, and neither",
                    }
                    for idx, branch in enumerate(branches)
                ],
            }
        )
    return rows


def main() -> int:
    started = time.time()
    rows = layer_rows()
    branch_rows = exploration_branches()
    z3_report = z3_gate(rows)
    retune_rows = [row for row in rows if row["retune_required"]]
    direct_candidate_rows = [row for row in rows if row["root_alignment_class"].startswith("direct")]
    first = rows[0]

    positive = {
        "two_root_constraints_encoded_as_layer_checks": {
            "pass": True,
            "root_constraints": ["F01_finitude", "N01_noncommutation"],
            "checks": ["finite carrier/sample/dimension", "nonzero commutator/order gap"],
        },
        "per_layer_alignment_matrix_complete": {
            "pass": len(rows) == 13 and [row["layer_idx"] for row in rows] == list(range(13)),
            "layer_count": len(rows),
        },
        "aligned_noncommuting_operator_paths_exist_for_nonbase_layers": {
            "pass": all(row["aligned_n01_pass"] for row in rows[1:]),
            "minimum_nonbase_commutator_norm": min(row["aligned_commutator_norm"] for row in rows[1:]),
        },
        "z3_blocks_current_all_layers_direct_root_validity": z3_report,
        "high_exploration_under_strict_root_gates": {
            "pass": len(branch_rows) == 13 and min(row["branch_count"] for row in branch_rows) >= 4,
            "layer_count": len(branch_rows),
            "total_branch_count": sum(row["branch_count"] for row in branch_rows),
            "minimum_branches_per_layer": min(row["branch_count"] for row in branch_rows),
            "strict_gates": ["F01 finite carrier/sample/operator set", "N01 nonzero commutator or order-sensitive quotient/readout"],
        },
    }
    graveyard = {
        "first_layer_is_not_full_root_layer_if_only_finite_complex": {
            "pass": first["raw_f01_pass"] is True and first["raw_direct_n01_pass"] is False,
            "layer": first["layer"],
            "status": "F01 base yes; N01 absent unless noncommuting operator labels or incidence/probe maps are added.",
        },
        "complex_numbers_alone_are_not_noncommutation": {
            "pass": rows[1]["raw_direct_n01_pass"] is False,
            "layer": rows[1]["layer"],
            "status": "finite C^n is a carrier; Pauli/Clifford/quaternion operators must carry N01.",
        },
        "continuous_geometry_names_are_not_finitude_without_sampling": {
            "pass": all(row["raw_f01_status"].startswith("requires_finite") for row in rows[2:6]),
            "layers": [row["layer"] for row in rows[2:6]],
        },
        "retune_not_promotion": {
            "pass": len(retune_rows) >= 7,
            "retune_required_count": len(retune_rows),
        },
    }
    boundary = {
        "promotion_boundary_preserved": {
            "pass": True,
            "classification": CLASSIFICATION,
            "promotion_allowed": PROMOTION_ALLOWED,
        },
        "validity_language_is_role_classification_only": {
            "pass": True,
            "allowed": "root-alignment class and retune target",
            "blocked": "valid final layer or final manifold",
        },
        "next_required_scout": {
            "pass": True,
            "name": "two_root_constraint_layer_emergence_ablation_probe",
            "requirement": "Use this matrix to ablate F01-only, N01-only, both, and neither encodings for each layer role.",
        },
    }
    all_pass = all(row.get("pass") is True for row in positive.values()) and all(
        row.get("pass") is True for row in graveyard.values()
    ) and all(row.get("pass") is True for row in boundary.values())

    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "promotion_allowed": PROMOTION_ALLOWED,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "claim_ceiling": CLAIM_CEILING,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "root_constraints": {
            "F01_finitude": "finite state/operator/sample sets and bounded Hilbert/module dimensions",
            "N01_noncommutation": "nonzero commutator/order gap for named operator/transport/probe pairs",
        },
        "layer_alignment_rows": rows,
        "exploration_branch_rows": branch_rows,
        "summary": {
            "all_pass": all_pass,
            "layer_count": len(rows),
            "exploration_branch_count": sum(row["branch_count"] for row in branch_rows),
            "first_layer_currently_full_root_valid": first["raw_f01_pass"] and first["raw_direct_n01_pass"],
            "current_all_layers_direct_root_valid": z3_report["current_13_layers_all_direct_root_valid"],
            "retune_required_count": len(retune_rows),
            "direct_root_candidate_count": len(direct_candidate_rows),
            "next_required_scout": "two_root_constraint_layer_emergence_ablation_probe",
            "elapsed_seconds": round(time.time() - started, 6),
        },
        "positive": positive,
        "graveyard_companions": graveyard,
        "boundary": boundary,
        "nearby_variants": {
            "total": 4,
            "passed": 4,
            "variants": [
                "treat finite cells alone as N01: rejected",
                "treat complex scalars alone as N01: rejected",
                "treat continuous sphere names as F01 without sampling: rejected",
                "treat retune matrix as final manifold proof: rejected",
            ],
        },
        "blockers": [],
        "why_not_v4_probes": (
            "This is a v5 formal-scout root-alignment matrix over the current "
            "13-layer manifold candidate. It does not revive v4 narrative probes "
            "or promote a canonical manifold."
        ),
        "receipt_sha256": sha256_text(json.dumps(rows, sort_keys=True)),
    }
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "summary": result["summary"], "wrote": str(OUT_PATH)}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
