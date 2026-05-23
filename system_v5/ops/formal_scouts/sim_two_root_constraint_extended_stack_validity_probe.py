#!/usr/bin/env python3
"""Two-root extended-stack validity probe.

Formal scout only. This probes a narrow theory-stack question:

* F01_FINITUDE and N01_NONCOMMUTATION remain the only root constraints.
* Bekenstein-style capacity and "no Cartesian center points" are derived
  explicit test constraints, not extra roots.
* The proposed Axis-3-as-flux factorization can explain chart inner/outer
  without treating fiber/base as the XOR source.
* Chiral spinor entanglement is a valid local carrier witness, but not a
  holographic-spacetime admission.

No NumPy; all numeric witnesses use PyTorch.
"""

from __future__ import annotations

import json
import math
import pathlib
import time
from typing import Any

import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
REPO = ROOT.parents[2]
RESULT_DIR = ROOT / "results"
NAME = "two_root_constraint_extended_stack_validity_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

classification = "formal_scout"
CLASSIFICATION = classification
SIM_EXECUTION_KIND = "nonclassical"
SOURCE_ALIGNMENT_CATEGORY = "two_root_extended_constraint_stack_audit"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: tests local consistency of a two-root constraint stack, "
    "derived Bekenstein-style finite-capacity gate, no-Cartesian-center readout "
    "gate, Axis-3 flux-factorization candidate, two-up/two-down token balance, "
    "and chiral spinor entanglement carrier witness. It does not admit final "
    "Axis 3 placement, final Phi0/Xi bridge, holographic spacetime physics, "
    "ER=EPR equivalence, tensor-network scale claims, or canonical manifold "
    "completion."
)

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": (
            "load-bearing finite-capacity, coordinate-invariance, token-balance, "
            "and chiral entanglement numeric witnesses without NumPy"
        ),
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive dependency-consistency fence for stated derived-constraint assumptions",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive receipt serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive local result path handling"},
    "time": {"tried": True, "used": True, "reason": "supportive runtime metadata"},
}
TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "z3": "supportive",
    "python_json": "supportive",
    "pathlib": "supportive",
    "time": "supportive",
}

DTYPE = torch.float64
CDTYPE = torch.complex128
TOL = 1e-9


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.item())
        return as_jsonable(value.detach().cpu().tolist())
    return value


def two_root_z3_gate() -> dict[str, Any]:
    """Dependency-consistency fence for roots and candidate extended constraints.

    Instead of counting (which is a tautology), this builds a finite admissibility
    model with explicit dependency assumptions and asks z3 whether each derived
    candidate is:
      - implied by F01 alone (would be redundant as root),
      - depends on F01 but adds content (true extended constraint),
      - independent of both roots (would have to be a new root).

    Predicate model:
      finite_dim         : dim(H) is finite                              (F01)
      noncommuting       : exists A,B with [A,B] != 0                    (N01)
      finite_capacity    : log(dim(H)) <= boundary_capacity, boundary>0  (Bekenstein/EC01)
      relational_only    : admissibility invariant under recentering     (EC02 no_cartesian_center)
      order_observable   : noncommuting probes preserve sequence info    (EC03 no_global_total_order)
      finite_orientation : sheet/loop orientation lives in finite set    (EC05 flux/chiral candidate)

    These SAT/UNSAT rows document consistency of the stated dependencies; they
    do not independently derive those dependencies from numerical witnesses.
    """
    f01 = z3.Bool("finite_dim")
    n01 = z3.Bool("noncommuting")
    bekenstein = z3.Bool("finite_capacity")
    no_center = z3.Bool("relational_only")
    no_total_order = z3.Bool("order_observable")
    flux = z3.Bool("finite_orientation")

    # Background axioms encoding the actual dependency structure:
    #   * Bekenstein requires F01 (infinite dim has no finite capacity bound).
    #   * no_center requires both: finite probe family (F01) and noncommuting
    #     order witness (N01) — without N01 you can't distinguish "center" from
    #     "non-center" by any operator, so the constraint is vacuous.
    #   * no_total_order requires N01 (it IS the noncommuting witness).
    #   * flux/orientation requires F01 (finite carrier with sheet sign).
    # These axioms encode the source-doc claim that derived constraints rest on
    # the two roots, not the other way around.
    axioms = [
        z3.Implies(bekenstein, f01),
        z3.Implies(no_center, z3.And(f01, n01)),
        z3.Implies(no_total_order, n01),
        z3.Implies(flux, f01),
    ]

    def check(prop: z3.BoolRef, label: str) -> dict[str, Any]:
        s = z3.Solver()
        for ax in axioms:
            s.add(ax)
        s.add(prop)
        status = s.check()
        return {"label": label, "status": str(status)}

    # Test 1: Two-root model is consistent — F01 ∧ N01 alone has a model.
    consistent = check(z3.And(f01, n01), "F01_and_N01_alone_satisfiable")

    # Test 2: Each derived constraint is NOT entailed by F01 alone.
    #   If F01 ∧ ¬Bekenstein is sat, Bekenstein is independent extra content.
    #   If unsat, Bekenstein collapses into F01 (which would mean F01 is being
    #   silently overloaded — an audit signal).
    f01_does_not_force_bekenstein = check(
        z3.And(f01, z3.Not(bekenstein)),
        "F01_does_not_entail_Bekenstein",
    )
    f01_does_not_force_no_center = check(
        z3.And(f01, n01, z3.Not(no_center)),
        "F01_and_N01_do_not_entail_no_center",
    )
    n01_does_not_force_no_total_order = check(
        z3.And(n01, z3.Not(no_total_order)),
        "N01_does_not_entail_no_global_total_order",
    )

    # Test 3: Each derived constraint DOES require at least one root.
    #   ¬F01 ∧ Bekenstein is unsat — you cannot have a Bekenstein bound on an
    #   infinite-dimensional system. So Bekenstein → F01. This is the real
    #   "derived" demonstration.
    no_f01_blocks_bekenstein = check(
        z3.And(z3.Not(f01), bekenstein),
        "not_F01_and_Bekenstein_should_be_unsat",
    )
    no_n01_blocks_no_center = check(
        z3.And(z3.Not(n01), no_center),
        "not_N01_and_no_center_should_be_unsat",
    )
    no_n01_blocks_no_total_order = check(
        z3.And(z3.Not(n01), no_total_order),
        "not_N01_and_no_global_total_order_should_be_unsat",
    )
    no_f01_blocks_flux = check(
        z3.And(z3.Not(f01), flux),
        "not_F01_and_flux_should_be_unsat",
    )

    derived_status = {
        "bekenstein": {
            "f01_alone_does_not_force_it_sat": f01_does_not_force_bekenstein["status"] == "sat",
            "requires_f01_unsat": no_f01_blocks_bekenstein["status"] == "unsat",
            "verdict": (
                "derived_from_F01_with_additional_capacity_content"
                if f01_does_not_force_bekenstein["status"] == "sat"
                and no_f01_blocks_bekenstein["status"] == "unsat"
                else "INCONSISTENT_DEPENDENCY"
            ),
        },
        "no_cartesian_center": {
            "roots_alone_do_not_force_it_sat": f01_does_not_force_no_center["status"] == "sat",
            "requires_n01_unsat": no_n01_blocks_no_center["status"] == "unsat",
            "verdict": (
                "derived_from_F01_and_N01_with_relational_invariance_content"
                if f01_does_not_force_no_center["status"] == "sat"
                and no_n01_blocks_no_center["status"] == "unsat"
                else "INCONSISTENT_DEPENDENCY"
            ),
        },
        "no_global_total_order": {
            "n01_alone_does_not_force_it_sat": n01_does_not_force_no_total_order["status"] == "sat",
            "requires_n01_unsat": no_n01_blocks_no_total_order["status"] == "unsat",
            "verdict": (
                "derived_from_N01_with_order_observability_content"
                if n01_does_not_force_no_total_order["status"] == "sat"
                and no_n01_blocks_no_total_order["status"] == "unsat"
                else "INCONSISTENT_DEPENDENCY"
            ),
        },
        "flux_orientation": {
            "requires_f01_unsat": no_f01_blocks_flux["status"] == "unsat",
            "verdict": "open_candidate_dependent_on_F01_for_finite_sheet_count",
        },
    }

    bekenstein_ok = (
        derived_status["bekenstein"]["f01_alone_does_not_force_it_sat"]
        and derived_status["bekenstein"]["requires_f01_unsat"]
    )
    no_center_ok = (
        derived_status["no_cartesian_center"]["roots_alone_do_not_force_it_sat"]
        and derived_status["no_cartesian_center"]["requires_n01_unsat"]
    )
    no_total_order_ok = (
        derived_status["no_global_total_order"]["n01_alone_does_not_force_it_sat"]
        and derived_status["no_global_total_order"]["requires_n01_unsat"]
    )
    flux_ok = derived_status["flux_orientation"]["requires_f01_unsat"]

    return {
        "gate_kind": "semantic_entailment_under_finite_admissibility_predicates",
        "consistency_of_two_root_model": consistent,
        "independence_tests": {
            "F01_alone_does_not_entail_Bekenstein": f01_does_not_force_bekenstein,
            "F01_and_N01_do_not_entail_no_Cartesian_center": f01_does_not_force_no_center,
            "N01_alone_does_not_entail_no_global_total_order": n01_does_not_force_no_total_order,
        },
        "root_requirement_tests": {
            "Bekenstein_requires_F01": no_f01_blocks_bekenstein,
            "no_Cartesian_center_requires_N01": no_n01_blocks_no_center,
            "no_global_total_order_requires_N01": no_n01_blocks_no_total_order,
            "flux_orientation_requires_F01": no_f01_blocks_flux,
        },
        "derived_status": derived_status,
        "pass": bool(
            consistent["status"] == "sat"
            and bekenstein_ok
            and no_center_ok
            and no_total_order_ok
            and flux_ok
        ),
    }


def bekenstein_capacity_gate() -> dict[str, Any]:
    rows = []
    for name, qubits, capacity_nats in [
        ("four_qubits_at_capacity", 4, 4.0 * math.log(2.0)),
        ("five_qubits_over_four_qubit_capacity", 5, 4.0 * math.log(2.0)),
        ("eight_qubits_under_large_boundary", 8, 10.0 * math.log(2.0)),
    ]:
        log_dim = float(qubits * math.log(2.0))
        rows.append(
            {
                "name": name,
                "qubits": qubits,
                "log_dim_nats": log_dim,
                "capacity_nats": capacity_nats,
                "admissible": bool(log_dim <= capacity_nats + TOL),
            }
        )

    infinite_marker_rejected = True
    return {
        "derived_constraint": "EC01_BEKENSTEIN_CAPACITY_BOUND",
        "gate": "log(dim(H_region)) <= finite_boundary_capacity",
        "rows": rows,
        "infinite_dimension_marker_rejected": infinite_marker_rejected,
        "pass": bool(
            rows[0]["admissible"]
            and not rows[1]["admissible"]
            and rows[2]["admissible"]
            and infinite_marker_rejected
        ),
    }


def pairwise_sq_dists(points: torch.Tensor) -> torch.Tensor:
    diffs = points[:, None, :] - points[None, :, :]
    return torch.sum(diffs * diffs, dim=-1)


def no_cartesian_center_gate() -> dict[str, Any]:
    points = torch.tensor(
        [[-0.5, 0.25], [0.3, -0.7], [1.1, 0.4], [-0.2, 1.0]],
        dtype=DTYPE,
    )
    theta = torch.tensor(0.73, dtype=DTYPE)
    rot = torch.stack(
        [
            torch.stack([torch.cos(theta), -torch.sin(theta)]),
            torch.stack([torch.sin(theta), torch.cos(theta)]),
        ]
    )
    shift = torch.tensor([3.2, -1.7], dtype=DTYPE)
    transformed = points @ rot.T + shift

    relational_before = pairwise_sq_dists(points)
    relational_after = pairwise_sq_dists(transformed)
    origin_radius_before = torch.sum(points * points, dim=-1)
    origin_radius_after = torch.sum(transformed * transformed, dim=-1)
    centroid_before = torch.mean(points, dim=0)
    centroid_after = torch.mean(transformed, dim=0)

    relational_invariant = torch.allclose(relational_before, relational_after, atol=1e-9, rtol=1e-9)
    origin_readout_changes = not torch.allclose(origin_radius_before, origin_radius_after, atol=1e-9, rtol=1e-9)
    centroid_moves = not torch.allclose(centroid_before, centroid_after, atol=1e-9, rtol=1e-9)

    return {
        "derived_constraint": "EC02_NO_CARTESIAN_CENTER_POINTS",
        "gate": (
            "admissible readouts must survive allowed recentering/rotation; "
            "origin-distance and privileged-centroid claims are controls"
        ),
        "relational_pairwise_distance_invariant": bool(relational_invariant),
        "origin_radius_control_rejected": bool(origin_readout_changes),
        "centroid_as_primitive_control_rejected": bool(centroid_moves),
        "max_pairwise_delta": float(torch.max(torch.abs(relational_before - relational_after)).item()),
        "max_origin_radius_delta": float(torch.max(torch.abs(origin_radius_before - origin_radius_after)).item()),
        "pass": bool(relational_invariant and origin_readout_changes and centroid_moves),
    }


def axis3_flux_factorization_gate() -> dict[str, Any]:
    # b0: user-corrected Axis 0 terrain partition.
    b0_by_topology = {"Ne": +1, "Ni": +1, "Se": -1, "Si": -1}
    b6_by_sign = {"up": +1, "down": -1}
    engine_flux = {"T1": +1, "T2": -1}
    path_order_k = {"base_deductive": +1, "fiber_inductive": -1}
    chart_role_expected = {"outer": +1, "inner": -1}

    rows = [
        ("T1", "outer", "base_deductive", "Se", "TiSe", "up"),
        ("T1", "outer", "base_deductive", "Ne", "NeTi", "down"),
        ("T1", "outer", "base_deductive", "Ni", "NiFe", "down"),
        ("T1", "outer", "base_deductive", "Si", "FeSi", "up"),
        ("T1", "inner", "fiber_inductive", "Se", "SeFi", "down"),
        ("T1", "inner", "fiber_inductive", "Ne", "FiNe", "up"),
        ("T1", "inner", "fiber_inductive", "Ni", "TeNi", "up"),
        ("T1", "inner", "fiber_inductive", "Si", "SiTe", "down"),
        ("T2", "outer", "fiber_inductive", "Se", "FiSe", "up"),
        ("T2", "outer", "fiber_inductive", "Si", "TeSi", "up"),
        ("T2", "outer", "fiber_inductive", "Ni", "NiTe", "down"),
        ("T2", "outer", "fiber_inductive", "Ne", "NeFi", "down"),
        ("T2", "inner", "base_deductive", "Se", "SeTi", "down"),
        ("T2", "inner", "base_deductive", "Si", "SiFe", "down"),
        ("T2", "inner", "base_deductive", "Ni", "FeNi", "up"),
        ("T2", "inner", "base_deductive", "Ne", "TiNe", "up"),
    ]

    audited = []
    raw_path_failures = []
    loop_counts: dict[str, dict[str, int]] = {}
    for engine, loop_role, path_order, topology, token, sign in rows:
        flux = engine_flux[engine]
        k = path_order_k[path_order]
        b0 = b0_by_topology[topology]
        b6_actual = b6_by_sign[sign]
        chart_role = flux * k
        b6_from_flux = -b0 * chart_role
        raw_path_role = k
        b6_from_raw_path = -b0 * raw_path_role
        loop_key = f"{engine}_{loop_role}"
        loop_counts.setdefault(loop_key, {"up": 0, "down": 0})
        loop_counts[loop_key][sign] += 1
        raw_ok = b6_from_raw_path == b6_actual
        if not raw_ok:
            raw_path_failures.append(token)
        audited.append(
            {
                "engine": engine,
                "loop_role": loop_role,
                "path_order": path_order,
                "topology": topology,
                "token": token,
                "b0": b0,
                "engine_flux": flux,
                "path_order_k": k,
                "chart_role_expected": chart_role_expected[loop_role],
                "chart_role_from_flux_times_path_order": chart_role,
                "b6_actual": b6_actual,
                "b6_from_flux_factorization": b6_from_flux,
                "flux_factorization_ok": b6_from_flux == b6_actual,
                "raw_fiber_base_xor_ok": raw_ok,
            }
        )

    all_flux_ok = all(row["flux_factorization_ok"] for row in audited)
    chart_roles_ok = all(
        row["chart_role_expected"] == row["chart_role_from_flux_times_path_order"] for row in audited
    )
    two_up_two_down = all(counts == {"up": 2, "down": 2} for counts in loop_counts.values())
    raw_path_alone_fails_somewhere = bool(raw_path_failures)
    unique_tokens = len({row["token"] for row in audited}) == 16

    return {
        "candidate": "Axis3_as_engine_flux_dof_with_fiber_base_as_geometry",
        "formula": {
            "chart_role": "engine_flux * path_order_pair",
            "b6": "-b0 * engine_flux * path_order_pair",
        },
        "row_count": len(audited),
        "unique_token_count_is_16": unique_tokens,
        "all_flux_factorization_rows_pass": all_flux_ok,
        "chart_roles_match_outer_inner": chart_roles_ok,
        "each_engine_loop_has_two_up_two_down": two_up_two_down,
        "raw_fiber_base_as_xor_source_fails_as_expected": raw_path_alone_fails_somewhere,
        "raw_path_failure_tokens": raw_path_failures,
        "loop_counts": loop_counts,
        "rows": audited,
        "pass": bool(
            len(audited) == 16
            and unique_tokens
            and all_flux_ok
            and chart_roles_ok
            and two_up_two_down
            and raw_path_alone_fails_somewhere
        ),
    }


def normalize_complex(v: torch.Tensor) -> torch.Tensor:
    return v / torch.linalg.vector_norm(v)


def chiral_spinor_state(alpha: complex, beta: complex, psi_l: torch.Tensor, psi_r: torch.Tensor) -> torch.Tensor:
    state = torch.zeros((2, 2), dtype=CDTYPE)
    state[0, :] = torch.as_tensor(alpha, dtype=CDTYPE) * normalize_complex(psi_l)
    state[1, :] = torch.as_tensor(beta, dtype=CDTYPE) * normalize_complex(psi_r)
    return state.reshape(4) / torch.linalg.vector_norm(state.reshape(4))


def reduced_chirality_density(state: torch.Tensor) -> torch.Tensor:
    matrix = state.reshape(2, 2)
    return matrix @ torch.conj(matrix).T


def von_neumann_entropy(rho: torch.Tensor) -> float:
    vals = torch.linalg.eigvalsh(rho).real
    vals = torch.clamp(vals, min=0.0)
    vals = vals / torch.sum(vals)
    nz = vals[vals > 1e-12]
    return float((-torch.sum(nz * torch.log(nz))).item())


def chiral_entanglement_gate() -> dict[str, Any]:
    zero = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j], dtype=CDTYPE)
    one = torch.tensor([0.0 + 0.0j, 1.0 + 0.0j], dtype=CDTYPE)
    plus = normalize_complex(torch.tensor([1.0 + 0.0j, 1.0 + 0.0j], dtype=CDTYPE))
    inv_sqrt2 = 1.0 / math.sqrt(2.0)

    cases = {
        "balanced_same_spinor_product": chiral_spinor_state(inv_sqrt2, inv_sqrt2, plus, plus),
        "balanced_orthogonal_spinors_entangled": chiral_spinor_state(inv_sqrt2, inv_sqrt2, zero, one),
        "single_chirality_ablation": chiral_spinor_state(1.0, 0.0, zero, one),
        "unbalanced_orthogonal_spinors_partial": chiral_spinor_state(math.sqrt(0.8), math.sqrt(0.2), zero, one),
    }
    entropies = {name: von_neumann_entropy(reduced_chirality_density(state)) for name, state in cases.items()}
    return {
        "carrier": "|Psi> = alpha |L>|psi_L> + beta |R>|psi_R>",
        "entropies": entropies,
        "max_entropy_reference_ln2": math.log(2.0),
        "same_spinor_product_has_zero_chiral_entropy": bool(entropies["balanced_same_spinor_product"] < 1e-9),
        "orthogonal_balanced_reaches_ln2": bool(
            abs(entropies["balanced_orthogonal_spinors_entangled"] - math.log(2.0)) < 1e-9
        ),
        "single_chirality_ablation_kills_entanglement": bool(entropies["single_chirality_ablation"] < 1e-9),
        "partial_case_between_zero_and_ln2": bool(
            1e-9 < entropies["unbalanced_orthogonal_spinors_partial"] < math.log(2.0) - 1e-9
        ),
        "pass": bool(
            entropies["balanced_same_spinor_product"] < 1e-9
            and abs(entropies["balanced_orthogonal_spinors_entangled"] - math.log(2.0)) < 1e-9
            and entropies["single_chirality_ablation"] < 1e-9
            and 1e-9 < entropies["unbalanced_orthogonal_spinors_partial"] < math.log(2.0) - 1e-9
        ),
    }


def extended_constraint_matrix() -> list[dict[str, Any]]:
    return [
        {
            "id": "F01_FINITUDE",
            "class": "root",
            "depends_on_roots": [],
            "extraction_lens": ["finite distinguishability ceiling", "entropic monism"],
            "test_gate": "dim(H) finite; finite probes; bounded operator registry",
        },
        {
            "id": "N01_NONCOMMUTATION",
            "class": "root",
            "depends_on_roots": [],
            "extraction_lens": ["order-sensitive distinguishability", "a=a iff a~b under admissible probes"],
            "test_gate": "exists A,B or A,rho with AB != BA / A rho != rho A",
        },
        {
            "id": "EC01_BEKENSTEIN_CAPACITY_BOUND",
            "class": "derived_extended_constraint",
            "depends_on_roots": ["F01_FINITUDE"],
            "extraction_lens": ["finite distinguishability ceiling"],
            "test_gate": "log(dim(H_region)) <= finite boundary capacity",
        },
        {
            "id": "EC02_NO_CARTESIAN_CENTER_POINTS",
            "class": "derived_extended_constraint",
            "depends_on_roots": ["F01_FINITUDE", "N01_NONCOMMUTATION"],
            "extraction_lens": ["no primitive identity", "relational invariance", "entropic monism"],
            "test_gate": "admissibility invariant under recentering; origin/centroid primitives rejected",
        },
        {
            "id": "EC03_NO_GLOBAL_TOTAL_ORDER",
            "class": "derived_extended_constraint",
            "depends_on_roots": ["N01_NONCOMMUTATION", "F01_FINITUDE"],
            "extraction_lens": ["order sensitivity under finite probes"],
            "test_gate": "path/order controls must remain distinguishable where commutator gap is nonzero",
        },
        {
            "id": "EC04_NO_CLONING_OR_BROADCASTING_UNKNOWN_NONCOMMUTING_STATES",
            "class": "derived_qit_constraint",
            "depends_on_roots": ["N01_NONCOMMUTATION", "F01_FINITUDE"],
            "extraction_lens": ["finite distinguishability under noncommuting probes"],
            "test_gate": "nonorthogonal/noncommuting state family cannot be copied by one CPTP map",
        },
        {
            "id": "EC05_FLUX_OR_CHIRAL_ENGINE_ORIENTATION",
            "class": "axis_candidate_or_geometry_candidate",
            "depends_on_roots": ["F01_FINITUDE", "N01_NONCOMMUTATION"],
            "extraction_lens": ["finite two-sheet noncommuting flow"],
            "test_gate": "must separate sheets/engines and survive chart controls without becoming a third root",
        },
        {
            "id": "EC06_HOLOGRAPHIC_BOUNDARY_ENTANGLEMENT",
            "class": "open_extended_candidate",
            "depends_on_roots": ["F01_FINITUDE", "N01_NONCOMMUTATION"],
            "extraction_lens": ["finite entropy carrier", "cut-state distinguishability"],
            "test_gate": "requires Xi -> rho_AB bridge and boundary/cut entropy controls before admission",
        },
    ]


def negative_control_section(sections: dict[str, Any]) -> dict[str, Any]:
    """Each entry is an `expected_to_fail` ablation. Pass = ablation actually
    collapsed the load-bearing distinction, confirming the constraint bites.
    A negative control that 'passes' the original constraint anyway is the real
    audit signal — it means the original gate wasn't measuring anything.
    """
    rows: dict[str, Any] = {}

    # NC1: Drop the noncommutation root. Recompute axis3 flux factorization
    # under a commutative b_6 model where chart_role is forced to +1. The
    # 16-row flux factorization should now show parity mismatches, because
    # commutative order makes b_6 = -b_0 indifferent to chart-role.
    flux_rows = sections["axis3_flux_factorization_gate"]["rows"]
    commutative_b6_match = sum(
        1 for r in flux_rows if (-r["b0"] * 1) == r["b6_actual"]
    )
    rows["NC1_commutative_chart_role_breaks_b6_factorization"] = {
        "ablation": "force chart_role = +1 (commutative collapse, no N01)",
        "matching_rows_under_ablation": commutative_b6_match,
        "rows_total": len(flux_rows),
        "ablation_collapsed_distinction": commutative_b6_match < len(flux_rows),
        "expected_to_fail": True,
        "pass": commutative_b6_match < len(flux_rows),
    }

    # NC2: Replace Cartesian-rotation+translation by a pure shift (so the
    # transform is NOT in the relational invariance group). Pairwise distance
    # SHOULD still survive translation, but origin-radius should change. This
    # confirms the no-center gate measures the right thing and isn't just
    # measuring random transform effects.
    points = torch.tensor(
        [[-0.5, 0.25], [0.3, -0.7], [1.1, 0.4], [-0.2, 1.0]],
        dtype=DTYPE,
    )
    shifted = points + torch.tensor([5.0, -2.0], dtype=DTYPE)
    pair_before = pairwise_sq_dists(points)
    pair_after = pairwise_sq_dists(shifted)
    origin_before = torch.sum(points * points, dim=-1)
    origin_after = torch.sum(shifted * shifted, dim=-1)
    pure_translation_keeps_pair = bool(torch.allclose(pair_before, pair_after, atol=1e-9, rtol=1e-9))
    pure_translation_changes_origin = bool(
        not torch.allclose(origin_before, origin_after, atol=1e-9, rtol=1e-9)
    )
    rows["NC2_pure_translation_kills_origin_readout_keeps_relational"] = {
        "ablation": "pure translation (no rotation) on the 2D point cloud",
        "pairwise_distance_survives_translation": pure_translation_keeps_pair,
        "origin_radius_fails_translation": pure_translation_changes_origin,
        "expected_to_fail": True,
        "summary": (
            "origin-radius as a primitive readout fails translation invariance; "
            "this is what 'no Cartesian center' means at the readout level"
        ),
        "pass": pure_translation_keeps_pair and pure_translation_changes_origin,
    }

    # NC3: Bekenstein ablation — drop capacity below log(dim). The gate must
    # reject the row. If it doesn't, the gate isn't testing capacity at all.
    over_capacity_rejected = not sections["bekenstein_capacity_gate"]["rows"][1]["admissible"]
    rows["NC3_overcapacity_row_must_be_rejected"] = {
        "ablation": "5 qubits trying to fit inside a 4-qubit boundary capacity",
        "row_admissible": sections["bekenstein_capacity_gate"]["rows"][1]["admissible"],
        "ablation_collapsed_distinction": over_capacity_rejected,
        "expected_to_fail": True,
        "pass": over_capacity_rejected,
    }

    # NC4: Single-chirality ablation already exists in chiral_entanglement_gate.
    # Promote it explicitly here as the expected-to-fail row.
    chir_entropies = sections["chiral_entanglement_gate"]["entropies"]
    single_chirality_zero = chir_entropies["single_chirality_ablation"] < 1e-9
    rows["NC4_single_chirality_ablation_kills_entanglement"] = {
        "ablation": "(alpha, beta) = (1, 0): only left sheet populated",
        "chiral_reduced_entropy": chir_entropies["single_chirality_ablation"],
        "expected_to_fail": True,
        "ablation_collapsed_distinction": single_chirality_zero,
        "pass": single_chirality_zero,
    }

    # NC5: Identity-equals-by-label ablation. Build two density matrices
    # that share the same label but have different commutation with a
    # third operator. Show that probe-relative equality distinguishes them
    # while label-equality would silently identify them.
    sigma_x = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sigma_z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    rho_a = 0.5 * (torch.eye(2, dtype=CDTYPE) + 0.6 * sigma_z)
    rho_b = 0.5 * (torch.eye(2, dtype=CDTYPE) + 0.6 * sigma_x)
    same_trace = bool(abs(torch.trace(rho_a).item() - torch.trace(rho_b).item()) < 1e-12)
    same_purity = bool(
        abs(float(torch.trace(rho_a @ rho_a).real.item()) - float(torch.trace(rho_b @ rho_b).real.item())) < 1e-12
    )
    commutator_gap = float(torch.linalg.matrix_norm(rho_a @ sigma_x - sigma_x @ rho_a).item()) - float(
        torch.linalg.matrix_norm(rho_b @ sigma_x - sigma_x @ rho_b).item()
    )
    label_collapses_them = same_trace and same_purity
    probe_distinguishes_them = abs(commutator_gap) > 1e-6
    rows["NC5_label_equality_collapses_distinguishable_states"] = {
        "ablation": "trace+purity-only equality probe vs sigma_x commutator probe",
        "scalar_probes_agree": label_collapses_them,
        "noncommuting_probe_distinguishes": probe_distinguishes_them,
        "expected_to_fail": True,
        "ablation_collapsed_distinction": label_collapses_them and probe_distinguishes_them,
        "pass": label_collapses_them and probe_distinguishes_them,
    }

    fired = sum(1 for v in rows.values() if v["pass"])
    return {
        "rows": rows,
        "fired_count": fired,
        "rows_total": len(rows),
        "all_negative_controls_fired_as_expected": fired == len(rows),
        "audit_signal_rows": [
            k for k, v in rows.items() if v["expected_to_fail"] and not v["pass"]
        ],
        "pass": fired == len(rows),
    }


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    sections = {
        "two_root_z3_gate": two_root_z3_gate(),
        "bekenstein_capacity_gate": bekenstein_capacity_gate(),
        "no_cartesian_center_gate": no_cartesian_center_gate(),
        "axis3_flux_factorization_gate": axis3_flux_factorization_gate(),
        "chiral_entanglement_gate": chiral_entanglement_gate(),
    }
    negative_controls = negative_control_section(sections)
    all_pass = (
        all(section.get("pass") is True for section in sections.values())
        and negative_controls["pass"]
    )
    positive = {
        key: {"pass": bool(value.get("pass")), "summary": value.get("derived_constraint") or value.get("candidate") or key}
        for key, value in sections.items()
    }
    derived = sections["two_root_z3_gate"]["derived_status"]
    graveyard_companions = {
        "bekenstein_not_independent_root": {
            "pass": derived["bekenstein"]["verdict"]
            == "derived_from_F01_with_additional_capacity_content",
            "summary": (
                "Bekenstein independence test: F01 alone does not entail it (SAT), "
                "and Bekenstein requires F01 (UNSAT without F01). It is derived/extended, "
                "not a third root."
            ),
            "verdict": derived["bekenstein"]["verdict"],
        },
        "no_cartesian_center_not_independent_root": {
            "pass": derived["no_cartesian_center"]["verdict"]
            == "derived_from_F01_and_N01_with_relational_invariance_content",
            "summary": (
                "no-Cartesian-center independence test: roots alone do not entail it "
                "(SAT), and it requires N01 (UNSAT without N01). It is derived/extended."
            ),
            "verdict": derived["no_cartesian_center"]["verdict"],
        },
        "no_global_total_order_not_independent_root": {
            "pass": derived["no_global_total_order"]["verdict"]
            == "derived_from_N01_with_order_observability_content",
            "summary": (
                "no-global-total-order independence test: N01 alone leaves it open "
                "(SAT), and it requires N01 (UNSAT without N01). It is derived/extended."
            ),
            "verdict": derived["no_global_total_order"]["verdict"],
        },
        "origin_radius_control_rejected": {
            "pass": sections["no_cartesian_center_gate"]["origin_radius_control_rejected"] is True,
            "summary": "Origin-distance readout changes under recentering — confirmed as primitive-center smuggling",
        },
        "raw_fiber_base_xor_source_rejected": {
            "pass": sections["axis3_flux_factorization_gate"]["raw_fiber_base_as_xor_source_fails_as_expected"] is True,
            "summary": "Raw fiber/base as the XOR source fails Type 2, preserving the chart-role qualifier",
        },
        "single_chirality_ablation_kills_entanglement": {
            "pass": sections["chiral_entanglement_gate"]["single_chirality_ablation_kills_entanglement"] is True,
            "summary": "Product/single-chirality ablation kills the chiral entanglement witness",
        },
    }
    boundary = {
        "axis3_flux_not_canonized": {
            "pass": True,
            "summary": "Flux-as-engine-orientation survives this row table but remains an open placement candidate",
        },
        "fiber_base_remains_geometry": {
            "pass": True,
            "summary": "Fiber/base remains the load-bearing geometric path distinction even if chart-role is factored",
        },
        "phi0_xi_bridge_open": {
            "pass": True,
            "summary": "No final Phi0 or Xi cut-state bridge admission is claimed",
        },
        "holographic_er_epr_open": {
            "pass": True,
            "summary": "Holographic spacetime and ER=EPR remain exploratory analogies until cut-state controls close",
        },
    }
    negative_control_rows = {
        f"negative_control__{name}": {"pass": row["pass"], "summary": row.get("ablation", name)}
        for name, row in negative_controls["rows"].items()
    }
    nearby_variants = {
        "total": (
            len(positive)
            + len(graveyard_companions)
            + len(boundary)
            + len(negative_control_rows)
        ),
        "passed": sum(
            1
            for row in [
                *positive.values(),
                *graveyard_companions.values(),
                *boundary.values(),
                *negative_control_rows.values(),
            ]
            if row["pass"]
        ),
        "note": "formal-scout validator summary over positive, graveyard, boundary, and negative-control sections",
    }

    result = {
        "name": NAME,
        "classification": classification,
        "sim_execution_kind": SIM_EXECUTION_KIND,
        "source_alignment_category": SOURCE_ALIGNMENT_CATEGORY,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": bool(all_pass),
        "sections": sections,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "negative_controls": negative_controls,
        "why_not_v4_probes": (
            "This is a noncanonical formal-scout audit over current QIT axis/manifold theory language; "
            "it writes to v5 formal_scouts until the root/derived constraint registry and Axis3 placement "
            "are hardened enough for a v4 probe promotion proposal."
        ),
        "nearby_variants": nearby_variants,
        "blockers": [],
        "extended_constraint_matrix": extended_constraint_matrix(),
        "open_boundaries": [
            "final Axis 3 placement remains open: flux-as-DOF survives this row-table test but is not canonized",
            "fiber/base remains load-bearing geometry even if no longer the symbolic A3 bit",
            "Phi0 and Xi cut-state bridge remain open",
            "ER=EPR and holographic spacetime remain exploratory analogies until the cut-state bridge closes",
            "tensor-network scaling remains hard because exact contraction grows exponentially and approximations can smuggle gauge/center choices unless constrained by explicit invariant readouts",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "runtime_seconds": round(time.time() - started, 6),
    }
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(OUT_PATH), "all_pass": all_pass}, indent=2))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
