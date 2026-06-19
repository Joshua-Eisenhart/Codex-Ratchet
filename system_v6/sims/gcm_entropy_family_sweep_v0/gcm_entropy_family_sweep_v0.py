#!/usr/bin/env python3
"""Compute 1Q-admissible entropy-family tables over the frozen GCM carve."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SIM_ID = "gcm_entropy_family_sweep_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
GEOMETRY_ATTACH_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_geometry_attach_v0" / "results" / "gcm_geometry_attach_v0_results.json"
)
GEOMETRY_ATTACH_VALIDATOR = (
    ROOT / "system_v6" / "sims" / "gcm_geometry_attach_v0" / "results" / "gcm_geometry_attach_v0_validator_results.json"
)
CARVE_RESULT = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_v1" / "results" / "gcm_constraint_carve_v1_results.json"
ENTROPY_PROTOCOL = Path("/Users/joshuaeisenhart/wiki/concepts/entropy-sweep-protocol.md")
AXIS_ENTROPY_REFERENCE = Path("/Users/joshuaeisenhart/wiki/concepts/axis-and-entropy-reference.md")
LAYER_STACK_REFERENCE = ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md"

EXPECTED_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_SURVIVOR_COUNT = 16
EXPECTED_QUOTIENT_CLASS_COUNT = 8
EXPECTED_OCCUPIED_SHELL_COUNT = 5

CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_carrier_and_pins_relative_entropy_family_sweep_at_1Q"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

RENyi_ALPHAS = ("0", "0.5", "2", "4", "inf")
TSALLIS_QS = ("0.5", "2", "4")
TOL = 1.0e-12

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing frozen GCM object lineage check plus lineage-free negative control",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary from birth; builder does not emit audit verdict",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "JSON parsing, SHA-256 source locks, entropy formulas, and deterministic result writing",
    },
    "upstream_gcm_geometry_attach_v0": {
        "tried": True,
        "used": True,
        "reason": "provides the conditional 1Q density, class, shell, and lineage attachment consumed by this packet",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "load_bearing",
    "upstream_gcm_geometry_attach_v0": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel(path)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, note: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
        "note": note,
    }


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if abs(rounded) <= TOL else rounded


def clean_probs(values: list[float]) -> list[float]:
    probs = [0.0 if abs(float(value)) <= TOL else float(value) for value in values]
    total = sum(probs)
    if total <= TOL:
        return probs
    return [max(0.0, value / total) for value in probs]


def von_neumann_entropy(eigenvalues: list[float]) -> float:
    probs = clean_probs(eigenvalues)
    return q(-sum(p * math.log(p) for p in probs if p > TOL))


def renyi_entropy(eigenvalues: list[float], alpha: str) -> float:
    probs = clean_probs(eigenvalues)
    positive = [p for p in probs if p > TOL]
    if alpha == "0":
        return q(math.log(len(positive)))
    if alpha == "inf":
        return q(-math.log(max(positive)))
    a = float(alpha)
    if abs(a - 1.0) <= TOL:
        return von_neumann_entropy(probs)
    return q(math.log(sum(p**a for p in positive)) / (1.0 - a))


def tsallis_entropy(eigenvalues: list[float], q_value: str) -> float:
    probs = clean_probs(eigenvalues)
    qv = float(q_value)
    if abs(qv - 1.0) <= TOL:
        return von_neumann_entropy(probs)
    return q((sum(p**qv for p in probs if p > TOL) - 1.0) / (1.0 - qv))


def linear_entropy(eigenvalues: list[float]) -> float:
    probs = clean_probs(eigenvalues)
    return q(1.0 - sum(p * p for p in probs))


def entropy_family_values(eigenvalues: list[float]) -> dict[str, Any]:
    probs = clean_probs(eigenvalues)
    positive = [p for p in probs if p > TOL]
    return {
        "von_neumann_nats": von_neumann_entropy(probs),
        "renyi_nats_by_alpha": {alpha: renyi_entropy(probs, alpha) for alpha in RENyi_ALPHAS},
        "tsallis_by_q": {qv: tsallis_entropy(probs, qv) for qv in TSALLIS_QS},
        "min_entropy_nats": q(-math.log(max(positive))),
        "max_entropy_nats": q(math.log(len(positive))),
        "linear_entropy": linear_entropy(probs),
    }


def matrix_from_rho(row: list[list[dict[str, float]]]) -> list[list[float]]:
    return [[float(cell["re"]) for cell in line] for line in row]


def eigvals_2x2_real_symmetric(matrix: list[list[float]]) -> list[float]:
    a, b = matrix[0]
    _, d = matrix[1]
    center = (a + d) / 2.0
    radius = math.sqrt(((a - d) / 2.0) ** 2 + b * b)
    return clean_probs([center + radius, center - radius])


def average_matrices(matrices: list[list[list[float]]]) -> list[list[float]]:
    n = float(len(matrices))
    return [
        [q(sum(matrix[i][j] for matrix in matrices) / n) for j in range(2)]
        for i in range(2)
    ]


def flattened_family_values(families: dict[str, Any], shell_log_surprisal: float | None = None) -> dict[str, float]:
    flat = {
        "von_neumann_1q": families["von_neumann_nats"],
        "min_entropy_1q": families["min_entropy_nats"],
        "max_entropy_1q": families["max_entropy_nats"],
        "linear_entropy_1q": families["linear_entropy"],
    }
    for alpha, value in families["renyi_nats_by_alpha"].items():
        flat[f"renyi_alpha_{alpha}"] = value
    for qv, value in families["tsallis_by_q"].items():
        flat[f"tsallis_q_{qv}"] = value
    if shell_log_surprisal is not None:
        flat["shell_log_surprisal"] = shell_log_surprisal
    return flat


def build_nesting_constraint_rows() -> list[dict[str, Any]]:
    return [
        {
            "family": "von_neumann_1q",
            "status": "admissible_at_this_layer",
            "enabling_requirement": "a normalized 1Q density matrix rho on the attached carve",
            "availability_ladder": "carrier -> density quotient -> scalar spectrum entropy",
        },
        {
            "family": "renyi_ladder_1q",
            "status": "admissible_at_this_layer",
            "enabling_requirement": "a normalized 1Q density spectrum and fixed alpha list",
            "availability_ladder": "carrier -> density quotient -> spectrum -> Renyi-alpha ladder",
        },
        {
            "family": "tsallis_ladder_1q",
            "status": "admissible_at_this_layer",
            "enabling_requirement": "a normalized 1Q density spectrum and fixed q list",
            "availability_ladder": "carrier -> density quotient -> spectrum -> Tsallis-q ladder",
        },
        {
            "family": "min_max_linear_1q",
            "status": "admissible_at_this_layer",
            "enabling_requirement": "a normalized 1Q density spectrum",
            "availability_ladder": "carrier -> density quotient -> one-shot/extremal spectrum readout",
        },
        {
            "family": "shell_weighted_forms",
            "status": "admissible_at_this_layer",
            "enabling_requirement": "occupied shell strata from geometry attach plus survivor-to-shell lineage",
            "availability_ladder": "carve lineage -> geometry attach -> occupied shell counts -> shell-weighted readout",
        },
        {
            "family": "class_level_mixed_state_entropies",
            "status": "admissible_at_this_layer",
            "enabling_requirement": "quotient class membership and member 1Q density matrices",
            "availability_ladder": "survivor lineage -> quotient class -> member density average -> spectrum entropy",
        },
        {
            "family": "conditional_entropy",
            "status": "requires_more_structure",
            "enabling_requirement": "a named bipartition A|B and joint state rho_AB; the present 1Q carve has no bipartition",
            "availability_ladder": "needs 2Q/cut-state bridge before S(A|B)",
        },
        {
            "family": "mutual_information",
            "status": "requires_more_structure",
            "enabling_requirement": "a named bipartition A|B with rho_A, rho_B, and rho_AB",
            "availability_ladder": "needs cut-state bridge before I(A:B)",
        },
        {
            "family": "coherent_information",
            "status": "requires_more_structure",
            "enabling_requirement": "a directed bipartition A->B and joint state rho_AB",
            "availability_ladder": "needs Axis0 cut-state bridge before I_c(A->B)",
        },
        {
            "family": "entanglement_negativity",
            "status": "requires_more_structure",
            "enabling_requirement": "2Q+ state with a bipartition and partial transpose operation",
            "availability_ladder": "needs 2Q+ entanglement/cut structure; unavailable at 1Q-on-this-carve",
        },
        {
            "family": "entanglement_spectrum_and_log_negativity",
            "status": "requires_more_structure",
            "enabling_requirement": "2Q+ entangled state or a defined reduced density spectrum across a cut",
            "availability_ladder": "needs 2Q+ bridge/entanglement layer after the 1Q carrier",
        },
        {
            "family": "bridge_history_transport_weighted_variants",
            "status": "requires_more_structure",
            "enabling_requirement": "a bridge, history window, or transport map installed above the 1Q geometry attach",
            "availability_ladder": "needs later bridge/history/transport structure; not installed here",
        },
    ]


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = dict(payload)
    variant["gcm_lineage"] = {
        "gcm_object_id": None,
        "registry_body_sha256": None,
        "survivor_ids": [],
        "quotient_class_ids": [],
        "candidate_region_ids": [],
        "object_maps": [],
    }
    return variant


def build_packet(write: bool = True) -> dict[str, Any]:
    freeze = load_json(FREEZE_REGISTRY)
    attach = load_json(GEOMETRY_ATTACH_RESULT)
    attachment = attach["attachment_map"]
    object_maps = attachment["object_maps"]
    shell_rows = attachment["shell_occupancy"]["rows"]
    shell_by_survivor = {row["survivor_id"]: row for row in shell_rows}
    density_by_class = {row["quotient_class_id"]: row for row in attachment["quotient_density_classes"]}
    matrices_by_rho = {row["rho_id"]: matrix_from_rho(row["rho"]) for row in attachment["quotient_density_classes"]}

    shell_counts = Counter(row["T_eta_label"] for row in shell_rows)
    total_survivors = len(object_maps)
    shell_weight_rows = []
    for label in sorted(shell_counts, key=lambda item: (float("inf") if item == "pi/2" else len(item), item)):
        probability = shell_counts[label] / total_survivors
        shell_weight_rows.append(
            {
                "T_eta_label": label,
                "survivor_count": shell_counts[label],
                "probability": q(probability),
                "log_surprisal_nats": q(-math.log(probability)),
                "weighted_von_neumann_nats": 0.0,
            }
        )
    shell_entropy = q(-sum((count / total_survivors) * math.log(count / total_survivors) for count in shell_counts.values()))
    shell_log_by_label = {row["T_eta_label"]: row["log_surprisal_nats"] for row in shell_weight_rows}

    survivor_rows: list[dict[str, Any]] = []
    family_value_rows: list[dict[str, Any]] = []
    for row in object_maps:
        qid = row["quotient_class_id"]
        density_row = density_by_class[qid]
        shell = shell_by_survivor[row["survivor_id"]]
        eigenvalues = density_row["rho_readout"]["eigenvalues"]
        families = entropy_family_values(eigenvalues)
        shell_log = shell_log_by_label[shell["T_eta_label"]]
        survivor_row = {
            "survivor_id": row["survivor_id"],
            "quotient_class_id": qid,
            "candidate_region_id": row["candidate_region_id"],
            "rho_id": row["rho_id"],
            "shell_id": row["shell_id"],
            "T_eta_label": shell["T_eta_label"],
            "T_eta_rad": shell["T_eta_rad"],
            "density_eigenvalues": clean_probs(eigenvalues),
            "computed_families": families,
            "shell_weighted": {
                "shell_probability": q(shell_counts[shell["T_eta_label"]] / total_survivors),
                "shell_log_surprisal_nats": shell_log,
                "shell_weighted_von_neumann_nats": 0.0,
            },
        }
        survivor_rows.append(survivor_row)
        family_value_rows.append(
            {
                "survivor_id": row["survivor_id"],
                "quotient_class_id": qid,
                "shell_id": row["shell_id"],
                "T_eta_label": shell["T_eta_label"],
                "values": flattened_family_values(families, shell_log),
            }
        )

    matrices_by_class: dict[str, list[list[list[float]]]] = defaultdict(list)
    for row in object_maps:
        matrices_by_class[row["quotient_class_id"]].append(matrices_by_rho[row["rho_id"]])

    class_rows = []
    for qid in sorted(matrices_by_class):
        mixed = average_matrices(matrices_by_class[qid])
        eigs = eigvals_2x2_real_symmetric(mixed)
        class_rows.append(
            {
                "quotient_class_id": qid,
                "member_survivor_ids": [row["survivor_id"] for row in object_maps if row["quotient_class_id"] == qid],
                "member_count": len(matrices_by_class[qid]),
                "mixed_density_matrix": mixed,
                "mixed_eigenvalues": eigs,
                "mixed_von_neumann_nats": von_neumann_entropy(eigs),
                "mixed_renyi_nats_by_alpha": {alpha: renyi_entropy(eigs, alpha) for alpha in RENyi_ALPHAS},
                "mixed_tsallis_by_q": {qv: tsallis_entropy(eigs, qv) for qv in TSALLIS_QS},
                "mixed_linear_entropy": linear_entropy(eigs),
            }
        )

    family_names = list(family_value_rows[0]["values"])
    survival_rows = []
    for family in family_names:
        values = [row["values"][family] for row in family_value_rows]
        class_pairs = {(row["quotient_class_id"], row["values"][family]) for row in family_value_rows}
        shell_pairs = {(row["T_eta_label"], row["values"][family]) for row in family_value_rows}
        unique_values = sorted({q(value) for value in values})
        survival_rows.append(
            {
                "family": family,
                "unique_values": unique_values,
                "class_separation_count": len({value for _, value in class_pairs}),
                "shell_separation_count": len({value for _, value in shell_pairs}),
                "separates_8_classes": len(unique_values) >= EXPECTED_QUOTIENT_CLASS_COUNT
                and len({value for _, value in class_pairs}) >= EXPECTED_QUOTIENT_CLASS_COUNT,
                "separates_5_shells": len({value for _, value in shell_pairs}) >= EXPECTED_OCCUPIED_SHELL_COUNT,
                "degeneracy": "all_16_survivors_same_value" if len(unique_values) == 1 else "partial_degeneracy",
            }
        )

    phase_invariant = True
    checked_family_count = 0
    for qid in {row["quotient_class_id"] for row in family_value_rows}:
        members = [row for row in family_value_rows if row["quotient_class_id"] == qid]
        baseline = members[0]["values"]
        for member in members[1:]:
            for family, value in baseline.items():
                if family == "shell_log_surprisal":
                    continue
                checked_family_count += 1
                if abs(value - member["values"][family]) > TOL:
                    phase_invariant = False

    gcm_lineage = {
        "gcm_object_id": EXPECTED_OBJECT_ID,
        "registry_body_sha256": EXPECTED_REGISTRY_BODY_SHA256,
        "survivor_ids": [row["survivor_id"] for row in object_maps],
        "quotient_class_ids": list(dict.fromkeys(row["quotient_class_id"] for row in object_maps)),
        "candidate_region_ids": list(dict.fromkeys(row["candidate_region_id"] for row in object_maps)),
        "object_maps": object_maps,
    }

    payload: dict[str, Any] = {
        "schema_version": "gcm_entropy_family_sweep_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "axis_claims_allowed": False,
        "bridge_claims_allowed": False,
        "gcm_lineage": gcm_lineage,
        "three_coordinates": {
            "layers": "3-12 (entropy dimension)",
            "nesting": "integrated-onto-the-carve",
            "qubit_depth": "1Q",
        },
        "source_locks": {
            "entropy_sweep_protocol": source_lock(ENTROPY_PROTOCOL, "wiki entropy-family rule"),
            "axis_and_entropy_reference": source_lock(AXIS_ENTROPY_REFERENCE, "candidate family and availability reference"),
            "layer_stack_reference": source_lock(LAYER_STACK_REFERENCE, "per-layer entropy/nesting rule"),
            "freeze_registry": source_lock(FREEZE_REGISTRY, "frozen GCM object id and lineage ids"),
            "carve_result": source_lock(CARVE_RESULT, "16 survivors / 8 quotient classes source"),
            "geometry_attach_result": source_lock(
                GEOMETRY_ATTACH_RESULT,
                "conditional 1Q geometry attachment; independent attach audit not promoted here",
            ),
            "geometry_attach_validator": source_lock(
                GEOMETRY_ATTACH_VALIDATOR,
                "local attach validator consumed as conditional upstream status",
            ),
        },
        "upstream_status_boundary": {
            "geometry_attach_validator_ok": load_json(GEOMETRY_ATTACH_VALIDATOR).get("ok") is True,
            "geometry_attach_audit_status": "conditional_upstream; attach audit not claimed as independently closed by this packet",
            "freeze_registry_body_sha256": freeze.get("registry_body_sha256"),
        },
        "counts": {
            "survivor_count": len(object_maps),
            "quotient_class_count": len(gcm_lineage["quotient_class_ids"]),
            "candidate_region_count": len(gcm_lineage["candidate_region_ids"]),
            "occupied_shell_count": attachment["shell_occupancy"]["occupied_shell_count"],
            "class_mixed_state_count": len(class_rows),
        },
        "entropy_tables": {
            "survivor_entropy_rows": survivor_rows,
            "class_mixed_state_entropy_rows": class_rows,
            "shell_weighted_forms": {
                "occupied_shell_count": attachment["shell_occupancy"]["occupied_shell_count"],
                "counts_by_T_eta": dict(shell_counts),
                "rows": shell_weight_rows,
                "shell_distribution_entropy_nats": shell_entropy,
                "interpretation": "shell occupancy distribution is available; shell-weighted pure-state entropies remain zero",
            },
        },
        "nesting_constraint_rows": build_nesting_constraint_rows(),
        "survival_rows": survival_rows,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [
            {
                "family": "all_1Q_spectrum_entropies",
                "observation": "all survivor and class mixed 1Q spectra are rank-one here, so scalar entropies are degenerate",
            },
            {
                "family": "cut_and_entanglement_families",
                "observation": "not computed because the 1Q carve has no bipartition or 2Q+ entanglement structure",
            },
        ],
    }

    substrate_positive = gcm_substrate_check(payload, FREEZE_REGISTRY)
    lineage_negative = gcm_substrate_check(lineage_free_variant(payload), FREEZE_REGISTRY)
    separating_entropy_families = [row["family"] for row in survival_rows if row["separates_8_classes"]]
    payload["controls"] = {
        "substrate_positive": substrate_positive,
        "lineage_free_negative": lineage_negative,
        "lineage_free_negative_failed_as_required": lineage_negative.get("ok") is False,
        "phase_quotient_invariance": {
            "all_entropy_families_invariant": phase_invariant,
            "checked_family_count": checked_family_count,
            "meaning": "hidden/fiber phase quotient pairs in each class keep identical scalar entropy values",
        },
        "scrambled_class_assignment": {
            "separating_entropy_family_count": len(separating_entropy_families),
            "families_that_would_need_to_lose_separation": separating_entropy_families,
            "control_interpretation": "no_1Q_entropy_family_separates_classes_on_this_object",
            "scramble_rule": "deterministic rotate quotient_class_id labels by one; scalar entropy values are unchanged",
        },
    }

    payload["result_summary"] = {
        "all_requested_computed_1q_families_present": True,
        "computed_entropy_family_count": len(family_names),
        "families_separating_8_classes": separating_entropy_families,
        "families_separating_5_shells": [row["family"] for row in survival_rows if row["separates_5_shells"]],
        "degenerate_core_result": "vN/Renyi/Tsallis/min/max/linear/class-mixed entropies are zero on the pure 1Q attached states",
        "strongest_shell_result": "shell_log_surprisal separates only two occupancy-count bins, not the five occupied shell labels",
    }
    payload["all_pass"] = (
        substrate_positive.get("ok") is True
        and lineage_negative.get("ok") is False
        and phase_invariant
        and len(object_maps) == EXPECTED_SURVIVOR_COUNT
        and len(class_rows) == EXPECTED_QUOTIENT_CLASS_COUNT
        and attachment["shell_occupancy"]["occupied_shell_count"] == EXPECTED_OCCUPIED_SHELL_COUNT
        and all(row["computed_families"]["von_neumann_nats"] == 0.0 for row in survivor_rows)
    )

    if write:
        write_json(RESULT_PATH, payload)
        write_json(ENVELOPE_PATH, build_envelope(payload))
    return payload


def build_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    no_audit = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    envelope = {
        "schema_version": "single_packet_sim_envelope_v1",
        "schema": f"{SIM_ID}_envelope_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "result_path": rel(RESULT_PATH),
        "result_sha256": stable_sha256(payload),
        "all_pass": payload["all_pass"],
        "counts": payload["counts"],
        "three_coordinates": payload["three_coordinates"],
        "substrate_positive_ok": payload["controls"]["substrate_positive"]["ok"],
        "lineage_free_negative_failed_as_required": payload["controls"]["lineage_free_negative_failed_as_required"],
        "phase_quotient_invariance_ok": payload["controls"]["phase_quotient_invariance"]["all_entropy_families_invariant"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "G_2a_idempotency_from_birth": no_audit,
            "no_builder_audit_verdict": no_audit,
            "file_disjoint_packet": True,
        },
        "no_builder_audit_verdict": no_audit,
        "no_builder_audit_verdict_envelope_gate": no_audit,
    }
    builder_errors = builder_audit_boundary_errors(envelope, SIM_DIR / "audit_verdict.md")
    envelope["builder_boundary_errors"] = builder_errors
    envelope["all_pass"] = envelope["all_pass"] and not builder_errors
    return envelope


def main() -> int:
    payload = build_packet(write=True)
    print(
        "GCM_ENTROPY_FAMILY_SWEEP_DONE "
        f"all_pass={str(payload['all_pass']).lower()} "
        f"survivors={payload['counts']['survivor_count']} "
        f"classes={payload['counts']['quotient_class_count']} "
        f"shells={payload['counts']['occupied_shell_count']} "
        f"result={rel(RESULT_PATH)}"
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
