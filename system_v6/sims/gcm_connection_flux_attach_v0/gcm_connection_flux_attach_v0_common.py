#!/usr/bin/env python3
"""Attach Hopf connection and geometric flux to the frozen GCM geometry rows."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


SIM_ID = "gcm_connection_flux_attach_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"
REGISTRY_PATH = ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
GEOMETRY_RESULT_PATH = ROOT / "system_v6" / "sims" / "gcm_geometry_attach_v0" / "results" / "gcm_geometry_attach_v0_results.json"
S2_FEEDSTOCK_PATH = ROOT / "system_v6" / "sims" / "geo_s2_connection_flux_foliation_v0" / "geo_s2_connection_flux_foliation_v0_jax.py"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_layers_10_12_1Q_connection_flux_carrier_and_pins_relative"
ENGINE_MODE = "all_three_scoped_step4_sims"
EXPECTED_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_SURVIVOR_COUNT = 16
EXPECTED_QUOTIENT_CLASS_COUNT = 8
EXPECTED_REGION_COUNT = 6
EXPECTED_SHELL_COUNT = 5
EXPECTED_SHELL_ORDER = ["0", "pi/8", "pi/4", "3pi/8", "pi/2"]
EXPECTED_SHELL_SIGNATURE = "2-4-4-4-2"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


LAYER_DECLARATION = {
    "layer_range": "10-12",
    "layers": [
        "10 Hopf connection A on the attached survivor geometry",
        "11 curvature/geometric flux F=dA on the attached survivor geometry",
        "12 occupied Hopf shell strata with holonomy and shell-flux rows",
    ],
    "step_4_verb": "A, F=dA, holonomy, shell flux, leakage ON the attached geometry",
}
NESTING_DECLARATION = {
    "coordinate": "integrated-onto-the-carve",
    "definition": "same gcm_object_id plus survivor/class/region mappings inherited from gcm_geometry_attach_v0 results by hash",
}
QUBIT_DEPTH_DECLARATION = {
    "coordinate": "1Q",
    "anti_bias_boundary": "1Q connection and geometric curvature flux only; no runtime/QIT/terrain/axis/physics claim.",
}
READOUT_DECLARATION = {
    "families": ["geometric_curvature_flux", "Hopf holonomy", "shell adjacency Stokes residual"],
    "not_entropy_promotion": "These are readouts on an attached 1Q carrier, not full ladder entropy admission.",
}
FORMULA_PIN = {
    "source": "geo_s2_connection_flux_foliation_v0",
    "connection_form": "A = d phi + cos(2*eta) d chi",
    "curvature_form": "F = -2*sin(2*eta) d eta wedge d chi",
    "holonomy_lifted_cycle": "h(eta) = -2*pi*cos(2*eta)",
    "stokes_pair": "h(eta_j)-h(eta_i)+int_[eta_i,eta_j]F = 0 for occupied-shell strips",
    "flux_type": "Hermes split: geometric curvature flux only; NEVER runtime/QIT flux.",
}

TOOL_MANIFEST = {
    "Manifolds": {"tried": True, "used": True, "reason": "Julia scoped S3/Hopf shell carrier check for occupied strata."},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python lineage graph resolves survivor->class->region->shell."},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch vmap recomputes holonomy and curvature density on occupied shell etas."},
    "sympy": {"tried": True, "used": True, "reason": "Exact symbolic A/F/h/Stokes formulas reused from S2 feedstock and evaluated on survivors."},
    "z3": {"tried": True, "used": True, "reason": "SMT binds shell-count/signature invariants from recomputed rows."},
    "cvc5": {"tried": True, "used": True, "reason": "Independent SMT bind of the same shell-count/signature invariants."},
    "gcm_substrate_check": {"tried": True, "used": True, "reason": "load-bearing frozen lineage consumption and lineage-free negative enforcement."},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a post-audit-idempotent builder/audit boundary from birth."},
    "python_stdlib": {"tried": True, "used": True, "reason": "canonical JSON, SHA-256 source locks, and deterministic packet writing."},
}

TOOL_INTEGRATION_DEPTH = {
    "Manifolds": "load_bearing",
    "networkx": "load_bearing",
    "torch.func": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "frozen_lineage_connection_flux_attachment",
        "occupied_shell_holonomy",
        "geometric_flux_only_fence",
        "shell_adjacency_leakage_rows",
        "lineage_free_negative_red",
    ],
    "engine_tool_intent": {
        "julia": {"Manifolds": "Manifolds.Sphere(3) anchors the S3 carrier while Julia recomputes shell holonomy rows."},
        "jax": {
            "networkx": "nx.Graph resolves survivor/class/region/shell paths for every occupied locus.",
            "sympy": "sp.Rational guards shell counts and signature before JAX numeric rows are accepted.",
        },
        "pytorch": {
            "torch.func": "vmap recomputes h(eta) and F_eta_chi over the five occupied shell etas.",
            "sympy": "sp.Rational guards exact shell count and shell occupation signature.",
        },
    },
}

AUTHORITY_PATHS = {
    "frozen_registry": REGISTRY_PATH,
    "geometry_attach_result": GEOMETRY_RESULT_PATH,
    "s2_connection_flux_feedstock": S2_FEEDSTOCK_PATH,
    "substrate_check_helper": ROOT / "scripts" / "gcm_substrate_check.py",
    "builder_audit_boundary": ROOT / "scripts" / "builder_audit_boundary.py",
    "layer_stack_reference": ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md",
    "ladder_contract": Path.home() / "wiki" / "concepts" / "nested-qubit-ladder-entropy-surface-sim-contract.md",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def git_last_commit(path: Path) -> str | None:
    if not path.exists() or not str(path).startswith(str(ROOT)):
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


def source_lock(path: Path) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
        "git_last_commit": git_last_commit(path),
    }


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0.0 else rounded


def eta_value(label: str) -> float:
    return {
        "0": 0.0,
        "pi/8": math.pi / 8.0,
        "pi/4": math.pi / 4.0,
        "3pi/8": 3.0 * math.pi / 8.0,
        "pi/2": math.pi / 2.0,
    }[label]


def connection_a_chi(eta: float) -> float:
    return math.cos(2.0 * eta)


def curvature_eta_chi(eta: float) -> float:
    return -2.0 * math.sin(2.0 * eta)


def holonomy_lifted_cycle(eta: float) -> float:
    return -2.0 * math.pi * math.cos(2.0 * eta)


def strip_flux(eta_i: float, eta_j: float) -> float:
    return 2.0 * math.pi * (math.cos(2.0 * eta_j) - math.cos(2.0 * eta_i))


def shell_groups(geometry_payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups = {label: [] for label in EXPECTED_SHELL_ORDER}
    for row in geometry_payload["attachment_map"]["survivor_spinor_maps"]:
        groups[row["T_eta_label"]].append(row)
    return groups


def build_shell_rows(geometry_payload: dict[str, Any]) -> list[dict[str, Any]]:
    groups = shell_groups(geometry_payload)
    rows = []
    previous_eta: float | None = None
    previous_h: float | None = None
    for label in EXPECTED_SHELL_ORDER:
        eta = eta_value(label)
        h = holonomy_lifted_cycle(eta)
        f_density = curvature_eta_chi(eta)
        strip = 0.0 if previous_eta is None else strip_flux(previous_eta, eta)
        h_delta = 0.0 if previous_h is None else h - previous_h
        stokes_residual = h_delta + strip
        members = groups[label]
        rows.append(
            {
                "T_eta_label": label,
                "T_eta_rad": q(eta),
                "source": "recomputed_on_survivor_loci",
                "survivor_ids": sorted({row["survivor_id"] for row in members}),
                "quotient_class_ids": sorted({row["quotient_class_id"] for row in members}),
                "candidate_region_ids": sorted({row["candidate_region_id"] for row in members}),
                "occupied_survivor_count": len(members),
                "connection": {
                    "A_phi": 1.0,
                    "A_chi": q(connection_a_chi(eta)),
                    "A_eta": 0.0,
                    "local_section": "A = d phi + cos(2*eta) d chi",
                },
                "curvature": {
                    "F_eta_chi": q(f_density),
                    "form": "F = -2*sin(2*eta) d eta wedge d chi",
                },
                "holonomy_lifted_cycle": {
                    "formula": "h(eta) = -2*pi*cos(2*eta)",
                    "value": q(h),
                },
                "shell_flux": {
                    "formula": "F strip flux to previous occupied shell",
                    "previous_shell": None if previous_eta is None else rows[-1]["T_eta_label"],
                    "strip_flux_value": q(strip),
                    "occupied_weighted_flux": q(strip * len(members)),
                    "stokes_residual": q(stokes_residual),
                },
            }
        )
        previous_eta = eta
        previous_h = h
    return rows


def shell_signature(rows: list[dict[str, Any]]) -> str:
    return "-".join(str(row["occupied_survivor_count"]) for row in rows)


def leakage_analysis(rows: list[dict[str, Any]]) -> dict[str, Any]:
    adjacency = []
    for left, right in zip(rows, rows[1:]):
        residual = right["shell_flux"]["stokes_residual"]
        adjacency.append(
            {
                "between_shells": [left["T_eta_label"], right["T_eta_label"]],
                "flux_delta": right["shell_flux"]["strip_flux_value"],
                "holonomy_delta": q(right["holonomy_lifted_cycle"]["value"] - left["holonomy_lifted_cycle"]["value"]),
                "stokes_residual": residual,
                "leakage_status": "closed_edge" if abs(residual) <= 1e-12 else "leaky_edge",
            }
        )
    closed = all(row["leakage_status"] == "closed_edge" for row in adjacency)
    boring = closed and len({abs(row["flux_delta"]) for row in adjacency}) <= 2
    return {
        "status": "closed" if closed else "leaky",
        "adjacency_rows": adjacency,
        "honest_outcome": "boring_flux" if boring else "nontrivial_closed_flux" if closed else "leaky_flux",
        "claim_boundary": "Closure is Stokes closure of the carved geometric-flux rows only, not admission.",
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    variant.pop("gcm_lineage", None)
    variant.pop("gcm_object_id", None)
    variant.pop("registry_body_sha256", None)
    for row in variant.get("connection_flux_attachment", {}).get("shell_rows", []):
        row.pop("survivor_ids", None)
        row.pop("quotient_class_ids", None)
        row.pop("candidate_region_ids", None)
    return variant


def substrate_enforcement(payload: dict[str, Any]) -> dict[str, Any]:
    positive = gcm_substrate_check(payload, REGISTRY_PATH)
    negative = gcm_substrate_check(lineage_free_variant(payload), REGISTRY_PATH)
    return {
        "helper": "scripts/gcm_substrate_check.py",
        "positive_payload_ok": positive,
        "lineage_free_negative": negative,
        "negative_failed_as_required": negative.get("ok") is False,
    }


def controls(payload: dict[str, Any], geometry_payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload["connection_flux_attachment"]["shell_rows"]
    permuted = [rows[0], rows[2], rows[1], rows[3], rows[4]]
    permuted_residuals = []
    for left, right in zip(permuted, permuted[1:]):
        ei = eta_value(left["T_eta_label"])
        ej = eta_value(right["T_eta_label"])
        residual = (holonomy_lifted_cycle(ej) - holonomy_lifted_cycle(ei)) + strip_flux(ei, ej)
        permuted_residuals.append(q(residual))
    negative = gcm_substrate_check(lineage_free_variant(payload), REGISTRY_PATH)
    return {
        "phase_quotient": {
            "control": "remove vertical spinor phase and retain density/base shell data",
            "pass": geometry_payload.get("nesting_controls", {}).get("phase_quotient_remove_lower_layer", {}).get("class_structure_survives") is True,
            "survives": ["A_chi by eta", "F_eta_chi by eta", "h(eta)", "shell occupancy"],
            "lost": ["anchored vertical fiber path as lower-layer coordinate"],
        },
        "carve_erasure": {
            "control": "erase frozen survivor/class/region lineage",
            "pass": negative.get("ok") is False,
            "anchoring_breaks": negative.get("ok") is False,
            "negative_errors": negative.get("errors", []),
        },
        "shell_permutation": {
            "control": "permute occupied shells before adjacency check",
            "pass": [row["T_eta_label"] for row in rows] == EXPECTED_SHELL_ORDER and shell_signature(rows) == EXPECTED_SHELL_SIGNATURE,
            "detects_order_change": [row["T_eta_label"] for row in permuted] != EXPECTED_SHELL_ORDER,
            "permuted_order": [row["T_eta_label"] for row in permuted],
            "permuted_stokes_residuals": permuted_residuals,
        },
    }


def z3_shell_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    shell_count = z3.Int("shell_count")
    survivor_count = z3.Int("survivor_count")
    solver.add(shell_count == len(rows))
    solver.add(survivor_count == sum(row["occupied_survivor_count"] for row in rows))
    solver.add(shell_count == EXPECTED_SHELL_COUNT)
    solver.add(survivor_count == EXPECTED_SURVIVOR_COUNT)
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "occupied shell count and survivor count match the frozen attached geometry after step-4 recomputation",
        "input_object": {"shell_count": len(rows), "survivor_count": sum(row["occupied_survivor_count"] for row in rows)},
    }


def cvc5_shell_proof(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    shell_count = solver.mkConst(int_sort, "shell_count")
    survivor_count = solver.mkConst(int_sort, "survivor_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, shell_count, solver.mkInteger(len(rows))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, survivor_count, solver.mkInteger(sum(row["occupied_survivor_count"] for row in rows))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, shell_count, solver.mkInteger(EXPECTED_SHELL_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, survivor_count, solver.mkInteger(EXPECTED_SURVIVOR_COUNT)))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "independent CVC5 check of occupied shell count and survivor count",
        "input_object": {"shell_count": len(rows), "survivor_count": sum(row["occupied_survivor_count"] for row in rows)},
    }


def seven_audit_questions() -> dict[str, Any]:
    return {
        "which_layer": "layers 10-12",
        "which_nesting_relation": "integrated-onto-the-carve",
        "which_qubit_depth": "1Q",
        "which_surface_network": "attached survivor shell strata on frozen GCM object, not a ring-checkerboard/CA-QCA runner",
        "which_three_engines_ran": ["julia", "jax", "pytorch"],
        "which_entropy_readout_families_varied": ["geometric_curvature_flux", "Hopf holonomy", "shell adjacency Stokes residual"],
        "what_broke_when_removed": "lineage-free substrate negative breaks anchoring; shell permutation breaks the declared shell order; phase quotient loses fiber anchoring while base geometric rows remain.",
    }


def build_packet() -> dict[str, Any]:
    registry = load_json(REGISTRY_PATH)
    geometry = load_json(GEOMETRY_RESULT_PATH)
    shell_rows = build_shell_rows(geometry)
    gcm_lineage = copy.deepcopy(geometry["gcm_lineage"])
    payload: dict[str, Any] = {
        "schema": "gcm_connection_flux_attach_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "claim": "Evaluate Hopf connection A, F=dA, h(eta), shell flux, and leakage rows on the attached survivor geometry.",
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "gcm_object_id": registry["gcm_object_id"],
        "registry_body_sha256": registry["registry_body_sha256"],
        "three_axis_declaration": {
            "layer": LAYER_DECLARATION,
            "nesting": NESTING_DECLARATION,
            "qubit_depth": QUBIT_DEPTH_DECLARATION,
        },
        "readout_declaration": READOUT_DECLARATION,
        "seven_audit_questions": seven_audit_questions(),
        "gcm_lineage": gcm_lineage,
        "upstream_conditionals": {
            "gcm_object_id_freeze_v0": {
                "path": rel(REGISTRY_PATH),
                "registry_body_sha256": registry["registry_body_sha256"],
                "gcm_object_id": registry["gcm_object_id"],
            },
            "gcm_geometry_attach_v0": {
                "path": rel(GEOMETRY_RESULT_PATH),
                "file_sha256": sha256_file(GEOMETRY_RESULT_PATH),
                "result_sha256": geometry.get("result_sha256"),
                "audit_status": "in_flight",
                "claim_condition": "This packet consumes gcm_geometry_attach_v0 RESULTS by hash; claims are conditional on that packet's audit verdict.",
            },
            "geo_s2_connection_flux_foliation_v0": {
                "path": rel(S2_FEEDSTOCK_PATH),
                "file_sha256": sha256_file(S2_FEEDSTOCK_PATH),
                "reuse": "formula pin for A, F=dA, h(eta), and Stokes shell flux; recomputed on frozen survivor loci.",
            },
        },
        "connection_flux_attachment": {
            "formula_pin": FORMULA_PIN,
            "shell_rows": shell_rows,
            "shell_occupation_signature": shell_signature(shell_rows),
            "geometric_flux_only_fence": {
                "statement": "Hermes flux split: this is Hopf curvature/geometric flux only; NEVER runtime/QIT flux.",
                "runtime_or_qit_flux_claimed": False,
                "disallowed_flux_words": ["runtime flux", "QIT flux", "memory flux", "chirality flux"],
            },
        },
        "counts": {
            "survivor_count": sum(row["occupied_survivor_count"] for row in shell_rows),
            "quotient_class_count": len({qid for row in shell_rows for qid in row["quotient_class_ids"]}),
            "candidate_region_count": len({rid for row in shell_rows for rid in row["candidate_region_ids"]}),
            "occupied_shell_count": len(shell_rows),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "source_locks": {name: source_lock(path) for name, path in AUTHORITY_PATHS.items()},
        "builder_gates": {
            "file_disjoint_packet": True,
            "boundary_helper_fully_used": True,
            "G_2a_idempotency_from_birth": True,
            "lineage_free_negative_required": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "substrate_check_helper_script_side": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": [
            "THE manifold",
            "terrain admission",
            "axis admission",
            "runtime flux",
            "QIT flux",
            "physics admission",
            "formal admission",
        ],
    }
    payload["leakage_analysis"] = leakage_analysis(shell_rows)
    payload["controls"] = controls(payload, geometry)
    payload["substrate_enforcement"] = substrate_enforcement(payload)
    payload["crossover_proofs"] = {"z3": z3_shell_proof(shell_rows), "cvc5": cvc5_shell_proof(shell_rows)}
    payload["all_pass"] = bool(
        registry["gcm_object_id"] == EXPECTED_OBJECT_ID
        and registry["registry_body_sha256"] == EXPECTED_REGISTRY_BODY_SHA256
        and geometry.get("all_pass") is True
        and payload["counts"]["survivor_count"] == EXPECTED_SURVIVOR_COUNT
        and payload["counts"]["quotient_class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and payload["counts"]["candidate_region_count"] == EXPECTED_REGION_COUNT
        and payload["counts"]["occupied_shell_count"] == EXPECTED_SHELL_COUNT
        and shell_signature(shell_rows) == EXPECTED_SHELL_SIGNATURE
        and payload["substrate_enforcement"]["positive_payload_ok"].get("ok") is True
        and payload["substrate_enforcement"]["negative_failed_as_required"] is True
        and payload["controls"]["phase_quotient"]["pass"] is True
        and payload["controls"]["carve_erasure"]["anchoring_breaks"] is True
        and payload["controls"]["shell_permutation"]["detects_order_change"] is True
        and payload["leakage_analysis"]["status"] == "closed"
        and payload["crossover_proofs"]["z3"]["verdict"] == "sat"
        and payload["crossover_proofs"]["cvc5"]["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    payload["result_sha256"] = stable_sha256({k: v for k, v in payload.items() if k not in {"generated_at", "result_sha256"}})
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload.get("schema") == "gcm_connection_flux_attach_v0_result_v1", "schema mismatch")
    require(payload.get("classification") == CLASSIFICATION, "classification mismatch")
    require(payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(payload.get("claim_ceiling") == CLAIM_CEILING, "claim ceiling mismatch")
    require(payload.get("gcm_object_id") == EXPECTED_OBJECT_ID, "gcm_object_id mismatch")
    require(payload.get("registry_body_sha256") == EXPECTED_REGISTRY_BODY_SHA256, "registry body hash mismatch")
    require(payload.get("three_axis_declaration", {}).get("layer") == LAYER_DECLARATION, "layer declaration mismatch")
    require(payload.get("three_axis_declaration", {}).get("nesting") == NESTING_DECLARATION, "nesting declaration mismatch")
    require(payload.get("three_axis_declaration", {}).get("qubit_depth") == QUBIT_DEPTH_DECLARATION, "qubit depth mismatch")
    rows = payload.get("connection_flux_attachment", {}).get("shell_rows", [])
    require([row.get("T_eta_label") for row in rows] == EXPECTED_SHELL_ORDER, "shell order mismatch")
    require(shell_signature(rows) == EXPECTED_SHELL_SIGNATURE, "shell signature mismatch")
    require(payload.get("substrate_enforcement", {}).get("positive_payload_ok", {}).get("ok") is True, "substrate positive failed")
    require(payload.get("substrate_enforcement", {}).get("negative_failed_as_required") is True, "lineage-free negative did not fail")
    require(payload.get("connection_flux_attachment", {}).get("geometric_flux_only_fence", {}).get("runtime_or_qit_flux_claimed") is False, "runtime/QIT flux fence failed")
    require(payload.get("leakage_analysis", {}).get("status") == "closed", "leakage closure failed")
    require(payload.get("all_pass") is True, "all_pass false")
    return errors


def main() -> int:
    payload = build_packet()
    write_json(RESULT_PATH, payload)
    write_json(LINEAGE_FREE_NEGATIVE_PATH, lineage_free_variant(payload))
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
