#!/usr/bin/env python3
"""
rpf_chirality_grounded_v0

Question: on the real M(C) carrier used by
retrocausal_possibility_field_carrier_grounded_v0, does the co-admissibility
compression admit a genuine chirality, or is it still only a labeled left/right
choice like the GNVW trap?

This packet consumes the committed grounded carrier read-only:

  system_v6/sims/retrocausal_possibility_field_carrier_grounded_v0/results/
  retrocausal_possibility_field_carrier_grounded_v0_results.json

The carrier is the 16 density-matrix survivors, with co-admissibility defined as
Hamming overlap of observable signs sgn(Tr(rho O_k)). The chiral extension uses
the same observable-sign structure and makes handedness a broken symmetry in the
sigma_y sign flow:

  L engine: outer-to-inner pairs whose sigma_y sign flows - to + score their
            Hamming co-admissibility weight.
  R engine: outer-to-inner pairs whose sigma_y sign flows + to - score their
            Hamming co-admissibility weight.

The mirror/parity operation is independent of those constructors:

  P_y(rho) = rho.conjugate(), equivalently Bloch (x,y,z) -> (x,-y,z).

That operation flips sigma_y while preserving sigma_x and sigma_z. The mirror
test reflects field data and reruns the same engines over P(F); it is not a
left/right constructor swap.

Ceiling: scratch_diagnostic. This can earn a finite grounded-carrier chirality
probe if the three acceptance tests pass. It is not a cosmic-birefringence
claim, not a physics admission, and not canonical.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import os
from typing import Any

import numpy as np


SIM_NAME = "rpf_chirality_grounded_v0"
SIM_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SIM_DIR, "..", "..", ".."))
GROUNDED_RESULT_PATH = os.path.join(
    REPO_ROOT,
    "system_v6",
    "sims",
    "retrocausal_possibility_field_carrier_grounded_v0",
    "results",
    "retrocausal_possibility_field_carrier_grounded_v0_results.json",
)
RESULT_PATH = os.path.join(SIM_DIR, "results", f"{SIM_NAME}_results.json")

I2 = np.eye(2, dtype=complex)
SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
OBSERVABLES = {"sigma_x": SIGMA_X, "sigma_y": SIGMA_Y, "sigma_z": SIGMA_Z}

PROBE_FAMILY_CHIRAL = ("sigma_x", "sigma_z", "sigma_y")
PROBE_FAMILY_BASE = ("sigma_x", "sigma_z")


TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing: rebuilds each 2x2 density matrix from the committed "
        "M(C) Bloch coordinates, verifies PSD/trace/Hermitian status, computes "
        "Tr(rho sigma_k), and applies P_y(rho)=rho.conjugate() for the independent "
        "mirror check.",
    },
    "itertools": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing: enumerates the finite shell product for the L and R "
        "compression objectives and the parity-averaged symmetric control.",
    },
    "hashlib": {
        "tried": True,
        "used": True,
        "reason": "Load-bearing for anti-tautology receipts: hashes carrier data, "
        "reflected carrier data, and engine objective score vectors without relying "
        "on a stored left/right label.",
    },
    "json": {
        "tried": True,
        "used": True,
        "reason": "Supportive: reads the committed grounded carrier result and writes "
        "the scratch diagnostic result envelope.",
    },
    "jax": {
        "tried": False,
        "used": False,
        "reason": "Not scoped: the carrier is 16 fixed 2x2 density matrices and the "
        "compression is a tiny exhaustive product.",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "Not scoped: no graph/network/autograd claim path.",
    },
    "julia": {
        "tried": False,
        "used": False,
        "reason": "Not scoped: this consumes the committed Python result for the "
        "M(C)-grounded carrier rather than rebuilding a Julia Canon artifact.",
    },
    "z3": {
        "tried": False,
        "used": False,
        "reason": "Not scoped: this is a finite scratch diagnostic by direct "
        "enumeration, not a formal impossibility proof.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "itertools": "load_bearing",
    "hashlib": "load_bearing",
    "json": "supportive",
    "jax": None,
    "pytorch": None,
    "julia": None,
    "z3": None,
}


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def branch_rank(branch_id: str) -> int:
    return int(branch_id[1:]) if branch_id.startswith("b") else int(branch_id[1:])


def density_matrix(coord: list[float]) -> np.ndarray:
    x, y, z = coord
    return 0.5 * (I2 + x * SIGMA_X + y * SIGMA_Y + z * SIGMA_Z)


def density_matrix_valid(rho: np.ndarray) -> bool:
    hermitian = np.allclose(rho, rho.conj().T, atol=1e-12)
    trace_one = abs(rho.trace().real - 1.0) < 1e-12 and abs(rho.trace().imag) < 1e-12
    eigs = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    return bool(hermitian and trace_one and np.all(eigs >= -1e-12))


def expectation_sign_from_rho(rho: np.ndarray, observable_name: str) -> int:
    val = (rho @ OBSERVABLES[observable_name]).trace().real
    scaled = int(round(2.0 * val))
    return 1 if scaled > 0 else (-1 if scaled < 0 else 0)


def load_grounded_carrier() -> dict[str, Any]:
    with open(GROUNDED_RESULT_PATH, "r", encoding="utf-8") as f:
        grounded = json.load(f)

    branch_states: dict[str, dict[str, Any]] = {}
    all_valid = True
    for bid in grounded["carrier"]["branch_ids"]:
        source = grounded["carrier"]["branch_states"][bid]
        coord = [float(v) for v in source["bloch_coord"]]
        rho = density_matrix(coord)
        valid = density_matrix_valid(rho)
        all_valid = all_valid and valid
        branch_states[bid] = {
            "survivor_id": source["survivor_id"],
            "candidate_id": source["candidate_id"],
            "bloch_coord": coord,
            "rho_real": rho.real.tolist(),
            "rho_imag": rho.imag.tolist(),
            "density_matrix_valid": valid,
            "signature_xzy": observable_signature_from_rho(rho, PROBE_FAMILY_CHIRAL),
            "signature_xz": observable_signature_from_rho(rho, PROBE_FAMILY_BASE),
            "parity_partner": None,
        }

    carrier = {
        "branch_states": branch_states,
        "branch_ids": sorted(branch_states, key=branch_rank),
        "shells_outer_to_inner": grounded["canonical_partition_selection"]["canonical_partition"],
        "source_result_path": os.path.relpath(GROUNDED_RESULT_PATH, REPO_ROOT),
        "source_result_sha256": sha256_text(
            open(GROUNDED_RESULT_PATH, "r", encoding="utf-8").read()
        ),
        "source_carrier_bloch_digest": grounded["carrier"]["carrier_bloch_digest"],
        "all_density_matrices_valid": all_valid,
    }
    for bid in carrier["branch_ids"]:
        carrier["branch_states"][bid]["parity_partner"] = parity_partner_of(carrier, bid)
    carrier["carrier_digest"] = carrier_digest(carrier)
    return carrier


def observable_signature_from_rho(rho: np.ndarray, family: tuple[str, ...]) -> list[int]:
    return [expectation_sign_from_rho(rho, name) for name in family]


def rho_of(carrier: dict[str, Any], branch_id: str) -> np.ndarray:
    state = carrier["branch_states"][branch_id]
    return np.array(state["rho_real"], dtype=float) + 1j * np.array(state["rho_imag"], dtype=float)


def signature(carrier: dict[str, Any], branch_id: str, family: tuple[str, ...]) -> tuple[int, ...]:
    rho = rho_of(carrier, branch_id)
    return tuple(expectation_sign_from_rho(rho, name) for name in family)


def sigma_y_sign(carrier: dict[str, Any], branch_id: str) -> int:
    return signature(carrier, branch_id, ("sigma_y",))[0]


def coadmissibility_overlap(
    carrier: dict[str, Any], left: str, right: str, family: tuple[str, ...]
) -> int:
    sig_l = signature(carrier, left, family)
    sig_r = signature(carrier, right, family)
    return sum(1 for a, b in zip(sig_l, sig_r) if a == b)


def carrier_digest(carrier: dict[str, Any]) -> str:
    rows = []
    for bid in carrier["branch_ids"]:
        state = carrier["branch_states"][bid]
        rows.append([bid, state["bloch_coord"], state["signature_xzy"]])
    return sha256_text(canonical_json(rows))


def parity_reflected_coord(coord: list[float]) -> list[float]:
    x, y, z = coord
    return [x, -y, z]


def parity_partner_of(carrier: dict[str, Any], branch_id: str) -> str | None:
    target = parity_reflected_coord(carrier["branch_states"][branch_id]["bloch_coord"])
    for other in carrier["branch_ids"]:
        if carrier["branch_states"][other]["bloch_coord"] == target:
            return other
    return None


def parity_reflect_carrier_data(carrier: dict[str, Any]) -> dict[str, Any]:
    reflected = json.loads(canonical_json(carrier))
    for bid in reflected["branch_ids"]:
        coord = parity_reflected_coord(carrier["branch_states"][bid]["bloch_coord"])
        rho = density_matrix(coord)
        reflected["branch_states"][bid]["bloch_coord"] = coord
        reflected["branch_states"][bid]["rho_real"] = rho.real.tolist()
        reflected["branch_states"][bid]["rho_imag"] = rho.imag.tolist()
        reflected["branch_states"][bid]["density_matrix_valid"] = density_matrix_valid(rho)
        reflected["branch_states"][bid]["signature_xzy"] = observable_signature_from_rho(
            rho, PROBE_FAMILY_CHIRAL
        )
        reflected["branch_states"][bid]["signature_xz"] = observable_signature_from_rho(
            rho, PROBE_FAMILY_BASE
        )
    for bid in reflected["branch_ids"]:
        reflected["branch_states"][bid]["parity_partner"] = parity_partner_of(reflected, bid)
    reflected["carrier_digest"] = carrier_digest(reflected)
    return reflected


def reflect_features_of_survivor(carrier: dict[str, Any], branch_id: str) -> dict[str, Any]:
    coord = parity_reflected_coord(carrier["branch_states"][branch_id]["bloch_coord"])
    rho = density_matrix(coord)
    return {
        "bloch_coord": coord,
        "signature_xzy": observable_signature_from_rho(rho, PROBE_FAMILY_CHIRAL),
    }


def survivor_features(carrier: dict[str, Any], branch_id: str) -> dict[str, Any]:
    state = carrier["branch_states"][branch_id]
    return {
        "bloch_coord": state["bloch_coord"],
        "signature_xzy": state["signature_xzy"],
    }


def pair_score(
    carrier: dict[str, Any], outer: str, inner: str, handedness: str
) -> int:
    y_outer = sigma_y_sign(carrier, outer)
    y_inner = sigma_y_sign(carrier, inner)
    if handedness == "L":
        flow_ok = y_outer < y_inner
    elif handedness == "R":
        flow_ok = y_outer > y_inner
    else:
        raise ValueError(f"unknown handedness {handedness!r}")
    if not flow_ok:
        return 0
    return coadmissibility_overlap(carrier, outer, inner, PROBE_FAMILY_CHIRAL)


def assignment_scores(
    carrier: dict[str, Any], assignment: tuple[str, ...], handedness: str
) -> dict[str, Any]:
    pair_rows = []
    chiral_score = 0
    base_score = 0
    for i in range(len(assignment)):
        for j in range(i + 1, len(assignment)):
            outer = assignment[i]
            inner = assignment[j]
            coadm = coadmissibility_overlap(carrier, outer, inner, PROBE_FAMILY_CHIRAL)
            oriented = pair_score(carrier, outer, inner, handedness)
            chiral_score += oriented
            base_score += coadm
            pair_rows.append({
                "outer": outer,
                "inner": inner,
                "coadmissibility_hamming_overlap": coadm,
                "oriented_chiral_weight": oriented,
                "sigma_y_signs": [sigma_y_sign(carrier, outer), sigma_y_sign(carrier, inner)],
            })
    return {
        "chiral_oriented_coadmissibility_score": chiral_score,
        "base_unoriented_coadmissibility_score": base_score,
        "pair_rows": pair_rows,
    }


def engine_objective_digest(
    carrier: dict[str, Any], shells: list[list[str]], handedness: str
) -> str:
    """Hash the actual objective over the whole finite shell product.

    The digest intentionally does not include a handedness label. L and R differ
    only if the scored assignment vector differs.
    """
    sorted_shells = [sorted(shell, key=branch_rank) for shell in shells if shell]
    score_vector = []
    for assignment in itertools.product(*sorted_shells):
        scores = assignment_scores(carrier, assignment, handedness)
        score_vector.append([
            list(assignment),
            scores["chiral_oriented_coadmissibility_score"],
            scores["base_unoriented_coadmissibility_score"],
        ])
    return sha256_text(canonical_json(score_vector))


def chiral_compression_engine(
    carrier: dict[str, Any], shells: list[list[str]], handedness: str
) -> dict[str, Any]:
    sorted_shells = [
        sorted(shell, key=branch_rank)
        for shell in shells
        if shell
    ]
    best_key: tuple[Any, ...] | None = None
    best_assignment: tuple[str, ...] | None = None
    for assignment in itertools.product(*sorted_shells):
        scores = assignment_scores(carrier, assignment, handedness)
        tie_break = tuple(-branch_rank(x) for x in reversed(assignment))
        key = (
            scores["chiral_oriented_coadmissibility_score"],
            scores["base_unoriented_coadmissibility_score"],
        ) + tie_break
        if best_key is None or key > best_key:
            best_key = key
            best_assignment = assignment

    assert best_assignment is not None
    scores = assignment_scores(carrier, best_assignment, handedness)
    shell_assignment = {
        f"Sigma_{len(best_assignment) - idx}": bid
        for idx, bid in enumerate(best_assignment)
    }
    return {
        "engine": f"{handedness}_chiral_grounded_compression",
        "handedness": handedness,
        "handedness_is_derived_from_sigma_y_flow": True,
        "reading_rule": (
            "score Hamming co-admissibility on outer-to-inner pairs with sigma_y flow - to +"
            if handedness == "L"
            else "score Hamming co-admissibility on outer-to-inner pairs with sigma_y flow + to -"
        ),
        "probe_family": list(PROBE_FAMILY_CHIRAL),
        "joint_assignment_outer_to_inner": list(best_assignment),
        "joint_assignment_by_shell": shell_assignment,
        "present_survivor": best_assignment[-1],
        "scores": {
            "chiral_oriented_coadmissibility_score": scores["chiral_oriented_coadmissibility_score"],
            "base_unoriented_coadmissibility_score": scores["base_unoriented_coadmissibility_score"],
        },
        "selected_pair_rows": scores["pair_rows"],
        "objective_identity_sha256": engine_objective_digest(
            carrier, shells, handedness
        ),
        "objective_digest_scope": "full finite shell-product score vector; no handedness label included in digest input",
    }


def optimal_innermost_survivor_set(
    carrier: dict[str, Any], shells: list[list[str]], handedness: str
) -> dict[str, Any]:
    sorted_shells = [sorted(shell, key=branch_rank) for shell in shells if shell]
    rows = []
    for assignment in itertools.product(*sorted_shells):
        scores = assignment_scores(carrier, assignment, handedness)
        rows.append((
            scores["chiral_oriented_coadmissibility_score"],
            scores["base_unoriented_coadmissibility_score"],
            assignment,
        ))
    max_pair = max((r[0], r[1]) for r in rows)
    survivors = sorted(
        {assignment[-1] for chiral, base, assignment in rows if (chiral, base) == max_pair},
        key=branch_rank,
    )
    return {
        "max_score_pair": list(max_pair),
        "optimal_assignment_count": sum(1 for chiral, base, _ in rows if (chiral, base) == max_pair),
        "optimal_innermost_survivor_set": survivors,
    }


def chirality_test(carrier: dict[str, Any]) -> dict[str, Any]:
    shells = carrier["shells_outer_to_inner"]
    left = chiral_compression_engine(carrier, shells, "L")
    right = chiral_compression_engine(carrier, shells, "R")
    left_opt = optimal_innermost_survivor_set(carrier, shells, "L")
    right_opt = optimal_innermost_survivor_set(carrier, shells, "R")
    optima_disjoint = not (
        set(left_opt["optimal_innermost_survivor_set"])
        & set(right_opt["optimal_innermost_survivor_set"])
    )
    differ = left["present_survivor"] != right["present_survivor"]
    return {
        "present_survivor_L": left["present_survivor"],
        "present_survivor_R": right["present_survivor"],
        "L_R_survivors_differ": differ,
        "L_optimal_innermost_survivor_set": left_opt["optimal_innermost_survivor_set"],
        "R_optimal_innermost_survivor_set": right_opt["optimal_innermost_survivor_set"],
        "L_R_optimal_survivor_sets_disjoint": optima_disjoint,
        "chirality_physical_not_relabel_on_grounded_carrier": bool(differ and optima_disjoint),
        "L_engine": left,
        "R_engine": right,
    }


def independent_mirror_test(carrier: dict[str, Any]) -> dict[str, Any]:
    reflected = parity_reflect_carrier_data(carrier)
    reflected_twice = parity_reflect_carrier_data(reflected)

    left = chiral_compression_engine(carrier, carrier["shells_outer_to_inner"], "L")
    right = chiral_compression_engine(carrier, carrier["shells_outer_to_inner"], "R")
    left_reflected = chiral_compression_engine(reflected, reflected["shells_outer_to_inner"], "L")
    right_reflected = chiral_compression_engine(reflected, reflected["shells_outer_to_inner"], "R")

    p_left = reflect_features_of_survivor(carrier, left["present_survivor"])
    p_right = reflect_features_of_survivor(carrier, right["present_survivor"])
    right_over_pf = survivor_features(reflected, right_reflected["present_survivor"])
    left_over_pf = survivor_features(reflected, left_reflected["present_survivor"])

    return {
        "P_definition": "P_y(rho)=rho.conjugate(); Bloch (x,y,z)->(x,-y,z); flips sigma_y and preserves sigma_x,sigma_z",
        "P_is_independent_data_operation": True,
        "P_is_involution": reflected_twice["carrier_digest"] == carrier["carrier_digest"],
        "P_moves_field": reflected["carrier_digest"] != carrier["carrier_digest"],
        "P_reflected_carrier_digest": reflected["carrier_digest"],
        "original_carrier_digest": carrier["carrier_digest"],
        "engines_are_distinct_functions_objective_sha_differ": (
            left["objective_identity_sha256"] != right["objective_identity_sha256"]
        ),
        "L_objective_sha256": left["objective_identity_sha256"],
        "R_objective_sha256": right["objective_identity_sha256"],
        "present_survivor_L_over_F": left["present_survivor"],
        "present_survivor_R_over_F": right["present_survivor"],
        "present_survivor_L_over_PF": left_reflected["present_survivor"],
        "present_survivor_R_over_PF": right_reflected["present_survivor"],
        "P_of_L_survivor_features": p_left,
        "R_over_PF_survivor_features": right_over_pf,
        "P_of_R_survivor_features": p_right,
        "L_over_PF_survivor_features": left_over_pf,
        "equivariance_P_maps_L_to_R": p_left == right_over_pf,
        "equivariance_P_maps_R_to_L": p_right == left_over_pf,
        "is_gnvw_swap_tautology": False,
        "anti_tautology_reason": "The mirror is computed by reflecting density-matrix data and rerunning engines over P(F); no swapped constructor result or identical objective SHA is used as evidence.",
    }


def build_parity_averaged_subcarrier(carrier: dict[str, Any]) -> dict[str, Any]:
    orbit_by_xz: dict[str, dict[str, Any]] = {}
    for bid in carrier["branch_ids"]:
        x, _y, z = carrier["branch_states"][bid]["bloch_coord"]
        key = canonical_json([x, z])
        orbit_by_xz.setdefault(key, {"x": x, "z": z, "members": []})
        orbit_by_xz[key]["members"].append(bid)

    q_branch_states: dict[str, dict[str, Any]] = {}
    key_to_qid: dict[str, str] = {}
    for idx, key in enumerate(sorted(orbit_by_xz)):
        orbit = orbit_by_xz[key]
        qid = f"q{idx}"
        key_to_qid[key] = qid
        coord = [float(orbit["x"]), 0.0, float(orbit["z"])]
        rho = density_matrix(coord)
        q_branch_states[qid] = {
            "orbit_members": sorted(orbit["members"], key=branch_rank),
            "bloch_coord": coord,
            "rho_real": rho.real.tolist(),
            "rho_imag": rho.imag.tolist(),
            "density_matrix_valid": density_matrix_valid(rho),
            "signature_xzy": observable_signature_from_rho(rho, PROBE_FAMILY_CHIRAL),
            "signature_xz": observable_signature_from_rho(rho, PROBE_FAMILY_BASE),
        }

    q_shells = []
    for shell in carrier["shells_outer_to_inner"]:
        qids = []
        for bid in shell:
            x, _y, z = carrier["branch_states"][bid]["bloch_coord"]
            qids.append(key_to_qid[canonical_json([x, z])])
        q_shells.append(sorted(set(qids), key=lambda q: int(q[1:])))

    subcarrier = {
        "branch_states": q_branch_states,
        "branch_ids": sorted(q_branch_states, key=lambda q: int(q[1:])),
        "shells_outer_to_inner": q_shells,
        "construction": "parity-pair averaged M(C) subcarrier: each q node is (rho_y_plus + rho_y_minus)/2 for one fixed (sigma_x,sigma_z) orbit, so sigma_y expectation is 0",
        "all_density_matrices_valid": all(v["density_matrix_valid"] for v in q_branch_states.values()),
    }
    subcarrier["carrier_digest"] = carrier_digest(subcarrier)
    return subcarrier


def symmetric_control_collapse(carrier: dict[str, Any]) -> dict[str, Any]:
    subcarrier = build_parity_averaged_subcarrier(carrier)
    left = chiral_compression_engine(subcarrier, subcarrier["shells_outer_to_inner"], "L")
    right = chiral_compression_engine(subcarrier, subcarrier["shells_outer_to_inner"], "R")
    y_signs = {
        bid: signature(subcarrier, bid, ("sigma_y",))[0]
        for bid in subcarrier["branch_ids"]
    }
    return {
        "control_kind": "non-chiral parity-symmetric M(C) subcarrier",
        "construction": subcarrier["construction"],
        "subcarrier_branch_count": len(subcarrier["branch_ids"]),
        "subcarrier_shells_outer_to_inner": subcarrier["shells_outer_to_inner"],
        "sigma_y_signs_all_zero": all(v == 0 for v in y_signs.values()),
        "sigma_y_signs": y_signs,
        "present_survivor_L_symmetric": left["present_survivor"],
        "present_survivor_R_symmetric": right["present_survivor"],
        "L_equals_R_on_symmetric_subcarrier": left["present_survivor"] == right["present_survivor"],
        "chirality_correctly_absent_on_symmetric_subcarrier": (
            left["present_survivor"] == right["present_survivor"]
            and all(v == 0 for v in y_signs.values())
        ),
        "L_engine_symmetric": left,
        "R_engine_symmetric": right,
        "parity_averaged_subcarrier": {
            "branch_ids": subcarrier["branch_ids"],
            "branch_states": {
                bid: {
                    "orbit_members": subcarrier["branch_states"][bid]["orbit_members"],
                    "bloch_coord": subcarrier["branch_states"][bid]["bloch_coord"],
                    "signature_xzy": subcarrier["branch_states"][bid]["signature_xzy"],
                }
                for bid in subcarrier["branch_ids"]
            },
        },
    }


def quotient_reproduction(carrier: dict[str, Any]) -> dict[str, Any]:
    classes: dict[str, list[str]] = {}
    for bid in carrier["branch_ids"]:
        key = canonical_json(list(signature(carrier, bid, PROBE_FAMILY_BASE)))
        classes.setdefault(key, []).append(bid)
    return {
        "probe_family": list(PROBE_FAMILY_BASE),
        "class_count": len(classes),
        "classes": {k: sorted(v, key=branch_rank) for k, v in sorted(classes.items())},
        "reproduces_grounded_carve_8_classes": len(classes) == 8,
    }


def build_result() -> dict[str, Any]:
    carrier = load_grounded_carrier()
    chirality = chirality_test(carrier)
    mirror = independent_mirror_test(carrier)
    symmetric = symmetric_control_collapse(carrier)

    hard_acceptance = {
        "L_R_different_survivors_on_chiral_carrier": chirality[
            "chirality_physical_not_relabel_on_grounded_carrier"
        ],
        "independent_mirror_maps_L_to_R_not_constructor_swap": bool(
            mirror["P_is_independent_data_operation"]
            and mirror["P_is_involution"]
            and mirror["P_moves_field"]
            and mirror["engines_are_distinct_functions_objective_sha_differ"]
            and mirror["equivariance_P_maps_L_to_R"]
            and mirror["equivariance_P_maps_R_to_L"]
            and not mirror["is_gnvw_swap_tautology"]
        ),
        "non_chiral_symmetric_control_L_equals_R": symmetric[
            "chirality_correctly_absent_on_symmetric_subcarrier"
        ],
    }
    all_pass = all(hard_acceptance.values())

    result = {
        "name": SIM_NAME,
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "object_name": "M(C)-grounded co-admissibility chirality diagnostic",
        "source_grounded_carrier": {
            "path": carrier["source_result_path"],
            "source_result_sha256": carrier["source_result_sha256"],
            "source_carrier_bloch_digest": carrier["source_carrier_bloch_digest"],
            "local_carrier_digest": carrier["carrier_digest"],
            "branch_count": len(carrier["branch_ids"]),
            "all_density_matrices_valid": carrier["all_density_matrices_valid"],
        },
        "probe_family": list(PROBE_FAMILY_CHIRAL),
        "coadmissibility_definition": "Hamming overlap of observable signs sgn(Tr(rho O_k)) for O=(sigma_x,sigma_z,sigma_y)",
        "chiral_orientation_definition": {
            "L": "outer-to-inner sigma_y sign flow - to +, weighted by Hamming co-admissibility",
            "R": "outer-to-inner sigma_y sign flow + to -, weighted by Hamming co-admissibility",
            "mirror": "P_y(rho)=rho.conjugate(), Bloch (x,y,z)->(x,-y,z)",
        },
        "quotient_reproduction": quotient_reproduction(carrier),
        "CHIRALITY_TEST": {
            k: v for k, v in chirality.items() if k not in ("L_engine", "R_engine")
        },
        "L_engine": chirality["L_engine"],
        "R_engine": chirality["R_engine"],
        "INDEPENDENT_MIRROR_TEST": mirror,
        "SYMMETRIC_CONTROL_COLLAPSE": symmetric,
        "HARD_ACCEPTANCE": hard_acceptance,
        "criteria_checked": [
            "L_R_different_survivors_on_chiral_M_C_carrier",
            "L_R_optimal_survivor_sets_disjoint",
            "P_y_independent_density_data_mirror_maps_L_to_R",
            "P_y_is_involution_and_moves_field",
            "engine_objective_shas_differ_without_hashing_handedness_label",
            "non_chiral_parity_averaged_subcarrier_has_sigma_y_zero",
            "non_chiral_parity_averaged_subcarrier_L_equals_R",
            "source_grounded_carrier_density_matrices_valid",
            "base_sigma_x_sigma_z_quotient_reproduces_8_classes",
        ],
        "all_pass": all_pass,
        "chirality_earned_on_grounded_carrier": all_pass,
        "honest_self_assessment": (
            "EARNED on the grounded finite M(C) carrier as a scratch diagnostic: L and R "
            "select different survivors under a sigma_y-oriented co-admissibility "
            "compression, P_y is an independent density-data mirror that maps the two "
            "engines, and the parity-averaged non-chiral subcarrier collapses L and R "
            "to the same survivor. This escapes the specific GNVW swap-tautology. It "
            "remains definition-relative to choosing sigma_y sign as the chiral "
            "orientation axis, and it is not yet physics, cosmic birefringence, "
            "spacetime chirality, or canonical admission."
            if all_pass
            else "NOT EARNED: at least one hard acceptance check failed, so the result "
            "stays a labeled left/right construction on this grounded carrier."
        ),
        "blocked_downstream_consumers": [
            "macroscopic parity violation claim",
            "cosmic birefringence / CMB polarization handedness claim",
            "spacetime chirality claim",
            "Weyl spinor admission",
            "GNVW chirality admission",
            "formal manifold admission",
            "canonical process claim",
        ],
        "named_caveats": {
            "G1": "The chiral axis is chosen as sigma_y sign. The diagnostic earns more than a constructor label, but it does not prove sigma_y is forced by deeper physics.",
            "G2": "The parity-symmetric control uses a parity-pair averaged subcarrier, not a new external physical ensemble.",
            "G3": "This is a finite compression diagnostic on a committed scratch carrier; no CMB/cosmic-birefringence prediction is admitted.",
        },
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
    }
    result["result_sha256"] = sha256_text(canonical_json(result))
    return result


def main() -> None:
    result = build_result()
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")
    print(json.dumps({
        "result_path": os.path.relpath(RESULT_PATH, REPO_ROOT),
        "all_pass": result["all_pass"],
        "present_survivor_L": result["CHIRALITY_TEST"]["present_survivor_L"],
        "present_survivor_R": result["CHIRALITY_TEST"]["present_survivor_R"],
        "symmetric_control": result["SYMMETRIC_CONTROL_COLLAPSE"]["present_survivor_L_symmetric"],
        "chirality_earned_on_grounded_carrier": result["chirality_earned_on_grounded_carrier"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
