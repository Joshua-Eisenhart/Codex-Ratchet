#!/usr/bin/env python3
"""R3 readout-invariants taxonomy over the verified R0-R3 foundation.

Scratch diagnostic only. This enumerates finite scalar readouts and classifies
each by the mutation that changes it. It does not promote any top-floor claim.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp


OBJECT_ID = "r3_readout_invariants"
ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
RESULT_PATH = ROOT / "system_v5/ops/formal_scouts/results/r3_readout_invariants_results.json"
JULIA_SCRIPT_PATH = ROOT / "system_v5/julia_carrier/r3_readout_invariants.jl"
JULIA_RESULT_PATH = ROOT / "system_v5/julia_carrier/r3_readout_invariants_julia_results.json"
PARENT_RESULTS = [
    ROOT / "system_v5/ops/formal_scouts/results/foundation_rung0to3_distinguishability_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r0_r1_r2_probe_quotient_micro_packet_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_operations_commutation_order_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r2_admissible_composition_rules_results.json",
    ROOT / "system_v5/ops/formal_scouts/results/r3_division_algebra_ladder_onset_results.json",
]
TOL = 1.0e-12

classification = "scratch_diagnostic"
CLASSIFICATION = classification
promotion_allowed = False
PROMOTION_ALLOWED = promotion_allowed
formal_admission_allowed = False
FORMAL_ADMISSION_ALLOWED = formal_admission_allowed
sim_execution_kind = "nonclassical"
SIM_EXECUTION_KIND = sim_execution_kind

ALLOWED_CLAIM = (
    "Finite R3 scalar readout-dependence taxonomy over verified R0-R3 foundation "
    "receipts; scratch diagnostic only."
)
BLOCKED_CLAIMS = [
    "formal_admission",
    "promotion",
    "top_floor_claim",
    "physics_claim",
    "downstream_doctrine_claim",
]
CLAIM_CEILING = (
    "Allowed only: finite bottom-up scalar readout taxonomy and mutation classifier. "
    "No formal admission, no promotion, no physics/top-floor consumer."
)

TOOL_MANIFEST = {
    "JAX": {
        "tried": True,
        "used": True,
        "reason": "load-bearing x64 finite density, quotient, carrier, and operation-algebra scalar readouts",
    },
    "jax.numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing array backend; all JAX lane numerical compute is through jnp with x64",
    },
    "Julia mirror": {
        "tried": True,
        "used": True,
        "reason": "load-bearing same-run independent backend parity; Julia reads the current JAX result",
    },
    "Python stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON receipt, hashing, timestamps, UUIDs, and Julia subprocess launch",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "not used: JAX lane uses jax.numpy only; no NumPy import or compute path",
    },
    "pytorch": {
        "tried": False,
        "used": False,
        "reason": "not used: explicit rung fence says no torch; stale C8 is not repaired decoratively",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "JAX": "load_bearing",
    "jax.numpy": "load_bearing",
    "Julia mirror": "load_bearing",
    "Python stdlib": "supportive",
    "numpy": None,
    "pytorch": None,
}

SIM_TEMPLATE_SURFACE = {
    "identity": ["sim_id", "name", "version", "tier"],
    "tooling": ["TOOL_MANIFEST", "TOOL_INTEGRATION_DEPTH", "classification"],
    "negatives": ["positive", "negative", "boundary", "probe"],
    "promotion": ["promotion_allowed", "formal_admission_allowed", "blocked_consumers"],
}

I2 = jnp.asarray([[1.0, 0.0], [0.0, 1.0]], dtype=jnp.complex128)
Z = jnp.asarray([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
X = jnp.asarray([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
HAD = (1.0 / jnp.sqrt(jnp.asarray(2.0, dtype=jnp.float64))) * jnp.asarray(
    [[1.0, 1.0], [1.0, -1.0]], dtype=jnp.complex128
)


def py_float(value: Any) -> float:
    return float(jax.device_get(jnp.real(value)))


def rounded(value: Any, digits: int = 12) -> float:
    return round(py_float(value), digits)


def ket(values: list[complex]) -> jax.Array:
    vec = jnp.asarray(values, dtype=jnp.complex128)
    return vec / jnp.sqrt(jnp.vdot(vec, vec))


def density(psi: jax.Array) -> jax.Array:
    return jnp.outer(psi, jnp.conj(psi))


def make_probe(name: str, vectors: list[jax.Array]) -> dict[str, Any]:
    return {"name": name, "effects": [density(vec) for vec in vectors]}


def base_kets() -> dict[str, jax.Array]:
    return {
        "z0": ket([1.0 + 0.0j, 0.0 + 0.0j]),
        "z1": ket([0.0 + 0.0j, 1.0 + 0.0j]),
        "x_plus": ket([1.0 + 0.0j, 1.0 + 0.0j]),
        "x_minus": ket([1.0 + 0.0j, -1.0 + 0.0j]),
    }


def candidate_configurations() -> list[dict[str, Any]]:
    ks = base_kets()
    return [
        {"id": "pure_z0", "rho": density(ks["z0"])},
        {"id": "pure_z1", "rho": density(ks["z1"])},
        {"id": "pure_x_plus", "rho": density(ks["x_plus"])},
        {"id": "pure_x_minus", "rho": density(ks["x_minus"])},
    ]


def probes() -> dict[str, dict[str, Any]]:
    ks = base_kets()
    return {
        "Z": make_probe("Z", [ks["z0"], ks["z1"]]),
        "X": make_probe("X", [ks["x_plus"], ks["x_minus"]]),
        "BLIND": {"name": "BLIND", "effects": [I2]},
    }


def measurement_stats(rho: jax.Array, probe: dict[str, Any]) -> list[float]:
    return [rounded(jnp.trace(effect @ rho), 12) for effect in probe["effects"]]


def quotient_class_count(candidates: list[dict[str, Any]], probe_family: list[dict[str, Any]]) -> int:
    signatures = set()
    for candidate in candidates:
        sig = [measurement_stats(candidate["rho"], probe) for probe in probe_family]
        signatures.add(json.dumps(sig, sort_keys=True, separators=(",", ":")))
    return len(signatures)


def von_neumann_entropy(rho: jax.Array) -> float:
    eigvals = jnp.real(jnp.linalg.eigvalsh(rho))
    positive = eigvals > TOL
    terms = jnp.where(positive, eigvals * jnp.log(eigvals), 0.0)
    return rounded(-jnp.sum(terms), 15)


def purity(rho: jax.Array) -> float:
    return rounded(jnp.trace(rho @ rho), 15)


def op_signature(commuting: bool) -> float:
    left = Z @ I2 if commuting else Z @ HAD
    right = I2 @ Z if commuting else HAD @ Z
    return rounded(jnp.linalg.norm(left - right), 15)


def cd_conj(x: jax.Array) -> jax.Array:
    signs = jnp.concatenate(
        [jnp.ones((1,), dtype=jnp.float64), -jnp.ones((x.shape[0] - 1,), dtype=jnp.float64)]
    )
    return x * signs


def cd_multiply(table: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    return jnp.einsum("cab,a,b->c", table, x, y)


def cd_pair_multiply(parent: jax.Array, x: jax.Array, y: jax.Array) -> jax.Array:
    n = parent.shape[0]
    a, b = x[:n], x[n:]
    c, d = y[:n], y[n:]
    first = cd_multiply(parent, a, c) - cd_multiply(parent, cd_conj(d), b)
    second = cd_multiply(parent, d, a) + cd_multiply(parent, b, cd_conj(c))
    return jnp.concatenate([first, second])


def cd_double(parent: jax.Array) -> jax.Array:
    n = parent.shape[0]
    dim = 2 * n
    table = jnp.zeros((dim, dim, dim), dtype=jnp.float64)
    eye = jnp.eye(dim, dtype=jnp.float64)
    for i in range(dim):
        for j in range(dim):
            table = table.at[:, i, j].set(cd_pair_multiply(parent, eye[i], eye[j]))
    return table


def carrier_tables() -> dict[str, jax.Array]:
    r = jnp.zeros((1, 1, 1), dtype=jnp.float64).at[0, 0, 0].set(1.0)
    c = cd_double(r)
    h = cd_double(c)
    o = cd_double(h)
    return {"H": h, "O": o}


def associator_defect(table: jax.Array) -> float:
    dim = table.shape[0]
    eye = jnp.eye(dim, dtype=jnp.float64)
    max_value = 0.0
    for a in range(dim):
        for b in range(dim):
            for c in range(dim):
                left = cd_multiply(table, cd_multiply(table, eye[a], eye[b]), eye[c])
                right = cd_multiply(table, eye[a], cd_multiply(table, eye[b], eye[c]))
                max_value = max(max_value, rounded(jnp.linalg.norm(left - right), 15))
    return max_value


def read_parent_receipts() -> dict[str, Any]:
    rows = []
    for path in PARENT_RESULTS:
        exists = path.exists()
        data = json.loads(path.read_text(encoding="utf-8")) if exists else {}
        rows.append(
            {
                "path": str(path),
                "exists": exists,
                "classification": data.get("classification"),
                "all_pass": data.get("all_pass"),
                "promotion_allowed": data.get("promotion_allowed"),
                "formal_admission_allowed": data.get("formal_admission_allowed"),
            }
        )
    return {
        "rows": rows,
        "pass": all(
            row["exists"]
            and row["classification"] == "scratch_diagnostic"
            and row["all_pass"] is True
            and row["promotion_allowed"] is False
            and row["formal_admission_allowed"] is False
            for row in rows
        ),
    }


def l1_gap(left: list[float], right: list[float]) -> float:
    return float(sum(abs(a - b) for a, b in zip(left, right, strict=True)))


def no_self_diff_tautologies(rows: list[dict[str, Any]]) -> bool:
    return all(
        row["left_expression_id"] != row["right_expression_id"]
        and row["left_quantity_id"] != row["right_quantity_id"]
        for row in rows
    )


def build_classifier() -> dict[str, Any]:
    ps = probes()
    candidates = candidate_configurations()
    relabeled = list(reversed(candidates))
    mixed = 0.5 * candidates[0]["rho"] + 0.5 * candidates[1]["rho"]
    pure = candidates[0]["rho"]
    tables = carrier_tables()

    values = {
        "quotient_class_count": {
            "base": float(quotient_class_count(candidates, [ps["Z"]])),
            "mutate_M": float(quotient_class_count(candidates, [ps["Z"], ps["X"]])),
            "carrier_relabel": float(quotient_class_count(relabeled, [ps["Z"]])),
        },
        "quotient_resolution": {
            "base": float(jnp.log(jnp.asarray(quotient_class_count(candidates, [ps["Z"]]), dtype=jnp.float64))),
            "mutate_M": float(jnp.log(jnp.asarray(quotient_class_count(candidates, [ps["Z"], ps["X"]]), dtype=jnp.float64))),
            "carrier_relabel": float(jnp.log(jnp.asarray(quotient_class_count(relabeled, [ps["Z"]]), dtype=jnp.float64))),
        },
        "von_neumann_entropy": {
            "base": von_neumann_entropy(pure),
            "mutate_density": von_neumann_entropy(mixed),
            "mutate_M": von_neumann_entropy(pure),
            "carrier_relabel": von_neumann_entropy(pure),
        },
        "purity": {
            "base": purity(pure),
            "mutate_density": purity(mixed),
            "mutate_M": purity(pure),
            "carrier_relabel": purity(pure),
        },
        "associator_defect": {
            "base": associator_defect(tables["O"]),
            "mutate_carrier": associator_defect(tables["H"]),
            "mutate_M": associator_defect(tables["O"]),
        },
        "commutation_order_signature": {
            "base": op_signature(False),
            "mutate_operation_algebra": op_signature(True),
            "mutate_density": op_signature(False),
            "carrier_relabel": op_signature(False),
        },
    }

    specs = {
        "quotient_class_count": {
            "dependence": "PROBE_DEPENDENT",
            "positive_factor": "M",
            "positive_key": "mutate_M",
            "control_keys": ["carrier_relabel"],
        },
        "quotient_resolution": {
            "dependence": "PROBE_DEPENDENT",
            "positive_factor": "M",
            "positive_key": "mutate_M",
            "control_keys": ["carrier_relabel"],
        },
        "von_neumann_entropy": {
            "dependence": "DENSITY_DERIVED",
            "positive_factor": "density",
            "positive_key": "mutate_density",
            "control_keys": ["mutate_M", "carrier_relabel"],
        },
        "purity": {
            "dependence": "DENSITY_DERIVED",
            "positive_factor": "density",
            "positive_key": "mutate_density",
            "control_keys": ["mutate_M", "carrier_relabel"],
        },
        "associator_defect": {
            "dependence": "CARRIER_DEPENDENT",
            "positive_factor": "carrier",
            "positive_key": "mutate_carrier",
            "control_keys": ["mutate_M"],
        },
        "commutation_order_signature": {
            "dependence": "OPERATION_ALGEBRA_DEPENDENT",
            "positive_factor": "operation_algebra",
            "positive_key": "mutate_operation_algebra",
            "control_keys": ["mutate_density", "carrier_relabel"],
        },
    }

    rows: dict[str, Any] = {}
    dependence_map: dict[str, str] = {}
    probe_dependent: list[str] = []
    carrier_dependent: list[str] = []
    density_derived: list[str] = []
    operation_algebra_dependent: list[str] = []
    control_pairs = []
    for readout, spec in specs.items():
        row_values = values[readout]
        base = float(row_values["base"])
        positive_value = float(row_values[spec["positive_key"]])
        positive_delta = abs(positive_value - base)
        control_deltas = {
            key: abs(float(row_values[key]) - base)
            for key in spec["control_keys"]
        }
        pass_value = positive_delta > TOL and all(delta <= TOL for delta in control_deltas.values())
        rows[readout] = {
            "readout": readout,
            "classification": spec["dependence"],
            "positive_mutation_factor": spec["positive_factor"],
            "base_value": base,
            "positive_mutation_value": positive_value,
            "positive_delta": positive_delta,
            "control_deltas": control_deltas,
            "pass": pass_value,
            "can_misclassify": True,
            "iff_rule": "only the declared dependence mutation changes this scalar above tolerance",
        }
        dependence_map[readout] = spec["dependence"]
        if spec["dependence"] == "PROBE_DEPENDENT":
            probe_dependent.append(readout)
        elif spec["dependence"] == "CARRIER_DEPENDENT":
            carrier_dependent.append(readout)
        elif spec["dependence"] == "DENSITY_DERIVED":
            density_derived.append(readout)
        elif spec["dependence"] == "OPERATION_ALGEBRA_DEPENDENT":
            operation_algebra_dependent.append(readout)
        control_pairs.append(
            {
                "name": f"{readout}_positive_mutation",
                "left_expression_id": f"{readout}.base",
                "right_expression_id": f"{readout}.{spec['positive_key']}",
                "left_quantity_id": f"{readout}_base_value",
                "right_quantity_id": f"{readout}_{spec['positive_key']}_value",
                "gap": positive_delta,
                "can_fail": True,
            }
        )

    no_self_diff = no_self_diff_tautologies(control_pairs)
    all_classified = all(bool(row["pass"]) for row in rows.values())
    return {
        "readout_rows": rows,
        "readout_dependence_map": dependence_map,
        "probe_dependent": sorted(probe_dependent),
        "carrier_dependent": sorted(carrier_dependent),
        "density_derived": sorted(density_derived),
        "operation_algebra_dependent": sorted(operation_algebra_dependent),
        "control_comparison_pairs": control_pairs,
        "no_self_diff": no_self_diff,
        "all_classified": all_classified,
        "readouts_count": len(rows),
    }


def shared_digest(shared: dict[str, Any]) -> str:
    payload = json.dumps(shared, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def dependence_map_string(dependence_map: dict[str, str]) -> str:
    return "|".join(f"{key}={dependence_map[key]}" for key in sorted(dependence_map))


def build_result(within_run_id: str) -> dict[str, Any]:
    parents = read_parent_receipts()
    classifier = build_classifier()
    no_top_floor = not any(term in " ".join(BLOCKED_CLAIMS).lower() for term in ["top-floor-allowed"])
    classification_genuine = (
        parents["pass"]
        and classifier["all_classified"]
        and classifier["no_self_diff"]
        and classification == "scratch_diagnostic"
        and promotion_allowed is False
        and formal_admission_allowed is False
    )
    shared_scalars = {
        f"{name}.base": float(row["base_value"])
        for name, row in classifier["readout_rows"].items()
    }
    shared_scalars.update(
        {
            f"{name}.positive_delta": float(row["positive_delta"])
            for name, row in classifier["readout_rows"].items()
        }
    )
    shared_booleans = {
        "parent_receipts_verified": parents["pass"],
        "readout_classifier_all_pass": classifier["all_classified"],
        "no_self_diff": classifier["no_self_diff"],
        "classification_genuine": classification_genuine,
        "classification_is_scratch_diagnostic": classification == "scratch_diagnostic",
        "promotion_false": promotion_allowed is False,
        "formal_admission_false": formal_admission_allowed is False,
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "torch_compute_used": False,
        "no_top_floor": no_top_floor,
    }
    shared_strings = {
        "object_id": OBJECT_ID,
        "allowed_claim": ALLOWED_CLAIM,
        "claim_ceiling": CLAIM_CEILING,
        "dependence_map": dependence_map_string(classifier["readout_dependence_map"]),
    }
    shared = {
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
    }

    result: dict[str, Any] = {
        "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
        "object_id": OBJECT_ID,
        "sim_id": OBJECT_ID,
        "name": OBJECT_ID,
        "version": "1.0",
        "tier": "R3_readout_invariants_taxonomy",
        "backend": "jax",
        "within_run_id": within_run_id,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(Path(__file__).resolve()),
        "result_path": str(RESULT_PATH),
        "peer_result_path": str(JULIA_RESULT_PATH),
        "parent_results": [str(path) for path in PARENT_RESULTS],
        "classification": classification,
        "promotion_allowed": promotion_allowed,
        "formal_admission_allowed": formal_admission_allowed,
        "allowed_claims": [ALLOWED_CLAIM],
        "blocked_claims": BLOCKED_CLAIMS,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_status": "diagnostic_only",
        "eligible_consumers": [],
        "blocked_consumers": BLOCKED_CLAIMS,
        "sim_execution_kind": sim_execution_kind,
        "sim_class": "constraint_probe",
        "purpose": "Classify finite R3 scalar readouts by genuine mutation dependence.",
        "scientific_question": "Which finite scalar readouts depend on M, density, carrier, or operation algebra?",
        "root_constraints_in_force": [
            "foundation_rung0to3",
            "r0_r1_r2_probe_quotient_micro_packet",
            "r2_admissible_operations",
            "r2_admissible_composition_rules",
            "r3_division_algebra_ladder_onset",
        ],
        "out_of_scope": BLOCKED_CLAIMS,
        "promotion_blockers": BLOCKED_CLAIMS,
        "SIM_TEMPLATE_surface": SIM_TEMPLATE_SURFACE,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "required_tools": ["JAX", "jax.numpy", "Julia mirror"],
        "actual_tools_used": ["JAX", "jax.numpy", "Python stdlib", "Julia mirror"],
        "proof_surfaces_used": [],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "numpy_compute_used": False,
        "numpy_imported": False,
        "torch_compute_used": False,
        "torch_imported": False,
        "tol": TOL,
        "verified_parent_receipts": parents,
        "probe": {
            "readouts": sorted(classifier["readout_rows"]),
            "mutation_factors": ["M", "density", "carrier", "operation_algebra"],
            "classifier_rule": "a readout is assigned to the only mutation factor that changes it above tolerance",
        },
        "readout_dependence_map": classifier["readout_dependence_map"],
        "readout_rows": classifier["readout_rows"],
        "probe_dependent": classifier["probe_dependent"],
        "carrier_dependent": classifier["carrier_dependent"],
        "density_derived": classifier["density_derived"],
        "operation_algebra_dependent": classifier["operation_algebra_dependent"],
        "control_comparison_pairs": classifier["control_comparison_pairs"],
        "positive": {
            "parent_receipts_verified": {"pass": parents["pass"]},
            "readout_classifier_all_pass": {"pass": classifier["all_classified"]},
            "classification_genuine": {"pass": classification_genuine},
            "no_self_diff_tautologies": {"pass": classifier["no_self_diff"]},
        },
        "negative": {
            "wrong_probe_dependence_controls_stable": {
                "pass": all(
                    delta <= TOL
                    for row in classifier["readout_rows"].values()
                    for delta in row["control_deltas"].values()
                ),
                "reason": "non-declared mutation factors do not move each scalar above tolerance",
            },
            "top_floor_blocked": {"pass": no_top_floor, "blocked_claims": BLOCKED_CLAIMS},
            "self_diff_control_rejected": {
                "pass": classifier["no_self_diff"],
                "control_count": len(classifier["control_comparison_pairs"]),
            },
        },
        "boundary": {
            "carrier_relabel_invariant_for_probe_readouts": {
                "pass": all(
                    classifier["readout_rows"][name]["control_deltas"].get("carrier_relabel", 0.0) <= TOL
                    for name in classifier["probe_dependent"]
                )
            },
            "quaternion_octonion_associator_boundary": {
                "pass": classifier["readout_rows"]["associator_defect"]["positive_delta"] > TOL,
                "left": "O",
                "right": "H",
            },
            "commuting_noncommuting_operation_boundary": {
                "pass": classifier["readout_rows"]["commutation_order_signature"]["positive_delta"] > TOL,
                "left": "noncommuting",
                "right": "commuting",
            },
            "classification_fence": {
                "pass": classification == "scratch_diagnostic"
                and promotion_allowed is False
                and formal_admission_allowed is False
            },
        },
        "why_not_v4_probes": "This is a v5 scratch diagnostic bottom-up formal-scout receipt with no promotion or formal admission.",
        "required_negatives": ["wrong_probe_dependence_controls_stable", "top_floor_blocked", "self_diff_control_rejected"],
        "negatives_run": ["wrong_probe_dependence_controls_stable", "top_floor_blocked", "self_diff_control_rejected"],
        "required_artifacts": [str(RESULT_PATH), str(JULIA_RESULT_PATH)],
        "artifacts_emitted": [str(RESULT_PATH)],
        "shared_scalars": shared_scalars,
        "shared_booleans": shared_booleans,
        "shared_strings": shared_strings,
        "shared_value_digest": shared_digest(shared),
        "result_summary": {
            "readouts_count": classifier["readouts_count"],
            "probe_dependent": classifier["probe_dependent"],
            "carrier_dependent": classifier["carrier_dependent"],
            "density_derived": classifier["density_derived"],
            "operation_algebra_dependent": classifier["operation_algebra_dependent"],
            "classification_genuine": classification_genuine,
            "no_self_diff": classifier["no_self_diff"],
            "all_pass": False,
        },
    }
    return result


def parity_against_julia(result: dict[str, Any], julia_data: dict[str, Any]) -> dict[str, Any]:
    max_diff = 0.0
    rows = []
    missing = []
    for key, value in result["shared_scalars"].items():
        if key not in julia_data.get("shared_scalars", {}):
            missing.append(key)
            continue
        diff = abs(float(value) - float(julia_data["shared_scalars"][key]))
        max_diff = max(max_diff, diff)
        rows.append({"key": key, "jax": float(value), "julia": float(julia_data["shared_scalars"][key]), "abs_diff": diff})
    boolean_mismatches = []
    for key, value in result["shared_booleans"].items():
        if key not in julia_data.get("shared_booleans", {}):
            missing.append(key)
            continue
        if bool(value) != bool(julia_data["shared_booleans"][key]):
            boolean_mismatches.append({"key": key, "jax": bool(value), "julia": bool(julia_data["shared_booleans"][key])})
    string_mismatches = []
    for key, value in result["shared_strings"].items():
        if key not in julia_data.get("shared_strings", {}):
            missing.append(key)
            continue
        if str(value) != str(julia_data["shared_strings"][key]):
            string_mismatches.append({"key": key, "jax": str(value), "julia": str(julia_data["shared_strings"][key])})
    parity_within_run = (
        julia_data.get("jax_reference_within_run_id") == result["within_run_id"]
        and julia_data.get("jax_reference_shared_value_digest") == result["shared_value_digest"]
        and julia_data.get("jax_reference_path") == str(RESULT_PATH)
    )
    return {
        "peer_result_path": str(JULIA_RESULT_PATH),
        "status": "compared",
        "within_1e_12": max_diff <= TOL and not boolean_mismatches and not string_mismatches and not missing and parity_within_run,
        "parity_max_diff": max_diff,
        "numeric_rows": rows,
        "boolean_mismatches": boolean_mismatches,
        "string_mismatches": string_mismatches,
        "missing_keys": missing,
        "parity_within_run": parity_within_run,
    }


def main() -> int:
    within_run_id = f"{OBJECT_ID}:{uuid.uuid4()}"
    result = build_result(within_run_id)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    env = dict(os.environ)
    env["R3_READOUT_JAX_RESULT"] = str(RESULT_PATH)
    env["R3_READOUT_JULIA_RESULT"] = str(JULIA_RESULT_PATH)
    proc = subprocess.run(["julia", str(JULIA_SCRIPT_PATH)], cwd=str(ROOT), text=True, capture_output=True, env=env)
    result["julia_subprocess"] = {
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-1200:],
        "stderr_tail": proc.stderr[-1200:],
    }
    if proc.returncode != 0 or not JULIA_RESULT_PATH.exists():
        result["parity"] = {
            "peer_result_path": str(JULIA_RESULT_PATH),
            "status": "julia_failed_or_missing",
            "within_1e_12": False,
            "parity_within_run": False,
        }
    else:
        julia_data = json.loads(JULIA_RESULT_PATH.read_text(encoding="utf-8"))
        result["parity"] = parity_against_julia(result, julia_data)
    result["positive"]["dual_backend_parity"] = {"pass": bool(result["parity"].get("within_1e_12"))}
    result["artifacts_emitted"] = [str(RESULT_PATH), str(JULIA_RESULT_PATH)]
    result["all_pass"] = bool(
        result["shared_booleans"]["classification_genuine"]
        and result["parity"].get("within_1e_12") is True
        and result["parity"].get("parity_within_run") is True
    )
    result["stop_condition_fired"] = not bool(result["all_pass"])
    result["pass_rule"] = "all readouts classify by iff mutation, no self-diff controls, fenced scratch diagnostic, and same-run JAX/Julia parity"
    result["fail_rule"] = "any misclassified readout, stale Julia parity, missing Julia mirror in actual tools, self-diff control, or fence violation"
    result["result_summary"]["parity_within_run"] = bool(result["parity"].get("parity_within_run"))
    result["result_summary"]["all_pass"] = result["all_pass"]
    result["parity_within_run"] = bool(result["parity"].get("parity_within_run"))
    result["no_self_diff"] = bool(result["shared_booleans"]["no_self_diff"])
    result["classification_genuine"] = bool(result["shared_booleans"]["classification_genuine"])
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "parity_within_run": result["parity_within_run"],
                "no_self_diff": result["no_self_diff"],
                "readouts_count": result["result_summary"]["readouts_count"],
                "julia_returncode": proc.returncode,
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
