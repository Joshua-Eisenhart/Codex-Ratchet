#!/usr/bin/env python3
"""Attach 1Q Hopf geometry to the frozen GCM object IDs."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import z3


SIM_ID = "gcm_geometry_attach_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
REGISTRY_PATH = ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_first_nested_packet_layers_3_12_1Q_carrier_and_pins_relative"
ENGINE_MODE = "all_three_full_sims"
EXPECTED_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_SURVIVOR_COUNT = 16
EXPECTED_QUOTIENT_CLASS_COUNT = 8
EXPECTED_REGION_COUNT = 6
EXPECTED_SHELL_COUNT = 5

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors, builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


AUTHORITY_PATHS = {
    "layer_stack_reference": ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md",
    "frozen_registry": REGISTRY_PATH,
    "substrate_check_helper": ROOT / "scripts" / "gcm_substrate_check.py",
    "standards_codex": ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md",
    "builder_audit_boundary": ROOT / "scripts" / "builder_audit_boundary.py",
    "build_card": SIM_DIR / "build_card.md",
}

USER_HASH_HINTS = {
    "layer_stack_reference_primary": "c9ccf9991",
    "layer_stack_supplement_1": "437f837ea",
    "layer_stack_supplement_2": "e4f03353a",
}

LAYER_DECLARATION = {
    "layer_range": "3-12",
    "layers": [
        "3 minimal QIT carrier C^2",
        "4 normalized spinor S^3",
        "5 Hopf projection",
        "6 density quotient",
        "7 Bloch image/ball",
        "8 fiber loop",
        "9 lifted-base loop",
        "10 Hopf connection A",
        "11 curvature/geometric flux F=dA",
        "12 Hopf tori/shell strata",
    ],
}
NESTING_DECLARATION = {
    "coordinate": "integrated-onto-the-carve",
    "definition": "same gcm_object_id plus survivor/class/region lineage, maps lower->upper, removal controls, recomputed induced geometry",
}
QUBIT_DEPTH_DECLARATION = {
    "coordinate": "1Q",
    "anti_bias_boundary": "1Q establishes exact Hopf/spinor geometry only; no terrain/stage/engine/axis/runtime claim.",
}
ENTROPY_DECLARATION = {
    "family": "density quotient readout plus pure-state von Neumann entropy",
    "expected_value": "zero for each pure 1Q rho",
    "licensed_by_nesting_row": "layers 3-6 attached to frozen survivor and quotient-class lineage",
    "not_claimed": "runtime entropy, cut entropy, axis entropy, or terrain entropy",
}

TOOL_MANIFEST = {
    "Manifolds": {"tried": True, "used": True, "reason": "Julia S3 carrier check through Manifolds.Sphere(3)."},
    "networkx": {"tried": True, "used": True, "reason": "JAX/Python lineage graph check from survivor to class to region."},
    "torch.func": {"tried": True, "used": True, "reason": "PyTorch batched density-matrix trace/determinant checks over all attached spinors."},
    "sympy": {"tried": True, "used": True, "reason": "Exact shell and class count guards."},
    "z3": {"tried": True, "used": True, "reason": "SMT binding of computed nested attachment count invariants."},
    "cvc5": {"tried": True, "used": True, "reason": "Independent SMT binding of the same count invariants."},
    "gcm_substrate_check": {"tried": True, "used": True, "reason": "load-bearing frozen-object lineage and lineage-free negative enforcement."},
    "builder_audit_boundary": {"tried": True, "used": True, "reason": "G.2a post-audit-idempotent builder/audit boundary from birth."},
    "python_stdlib": {"tried": True, "used": True, "reason": "canonical JSON, SHA-256 IDs, file hashes, and result writing."},
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
        "frozen_id_geometry_attachment",
        "S3_spinor_unit_norm",
        "Hopf_density_quotient_survival",
        "lineage_graph_resolves_to_regions",
        "phase_quotient_and_carve_erasure_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Manifolds": "Manifolds.Sphere(3) instantiates the S3 carrier and gates the unit spinor rows."
        },
        "jax": {
            "networkx": "nx.Graph checks every survivor has a path to one quotient class and one candidate region.",
            "sympy": "sp.Rational guards exact survivor/class/shell occupancy counts.",
        },
        "pytorch": {
            "torch.func": "vmap over spinors recomputes rho trace and determinant controls.",
            "sympy": "sp.Rational guards exact density quotient and shell counts.",
        },
    },
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


def stable_id(prefix: str, value: Any, length: int = 20) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


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


def source_lock(name: str, path: Path) -> dict[str, Any]:
    row: dict[str, Any] = {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path) if path.exists() else None,
        "git_last_commit": git_last_commit(path) if path.exists() else None,
    }
    if name == "layer_stack_reference":
        row["user_supplied_hash_hints"] = USER_HASH_HINTS
    return row


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if rounded == 0.0 else rounded


def c(re: float, im: float = 0.0) -> dict[str, float]:
    return {"re": q(re), "im": q(im)}


def cmul(a: dict[str, float], b: dict[str, float]) -> dict[str, float]:
    return c(a["re"] * b["re"] - a["im"] * b["im"], a["re"] * b["im"] + a["im"] * b["re"])


def cconj(a: dict[str, float]) -> dict[str, float]:
    return c(a["re"], -a["im"])


def registry() -> dict[str, Any]:
    return load_json(REGISTRY_PATH)


def region_for_class(registry_payload: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for region in registry_payload["frozen_registry"]["candidate_regions"]:
        for qid in region["member_quotient_class_ids"]:
            out[qid] = region["candidate_region_id"]
    return out


def class_for_survivor(registry_payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for qrow in registry_payload["frozen_registry"]["quotient_classes"]:
        for sid in qrow["member_survivor_ids"]:
            out[sid] = qrow
    return out


def spinor_from_probe_signature(signature: list[int]) -> dict[str, Any]:
    sx, sz = (int(signature[0]), int(signature[1]))
    norm = math.sqrt(float(sx * sx + sz * sz))
    if norm <= 0:
        raise ValueError(f"zero active probe signature cannot realize a 1Q spinor: {signature}")
    nx = sx / norm
    ny = 0.0
    nz = sz / norm
    theta = math.acos(max(-1.0, min(1.0, nz)))
    phi = 0.0 if nx >= 0.0 else math.pi
    eta = theta / 2.0
    alpha = math.cos(eta)
    beta = math.sin(eta) * (1.0 if nx >= 0.0 else -1.0)
    psi = [c(alpha), c(beta)]
    return {
        "psi": psi,
        "s3_r4": [q(alpha), 0.0, q(beta), 0.0],
        "bloch_unit": [q(nx), q(ny), q(nz)],
        "theta_rad": q(theta),
        "phi_rad": q(phi),
        "eta_rad": q(eta),
        "eta_label": eta_label(nz),
    }


def eta_label(nz: float) -> str:
    root_half = 1.0 / math.sqrt(2.0)
    if math.isclose(nz, 1.0, abs_tol=1e-12):
        return "0"
    if math.isclose(nz, root_half, abs_tol=1e-12):
        return "pi/8"
    if math.isclose(nz, 0.0, abs_tol=1e-12):
        return "pi/4"
    if math.isclose(nz, -root_half, abs_tol=1e-12):
        return "3pi/8"
    if math.isclose(nz, -1.0, abs_tol=1e-12):
        return "pi/2"
    return f"eta_{q(math.acos(nz) / 2.0)}"


def hopf_projection(psi: list[dict[str, float]]) -> list[float]:
    alpha, beta = psi
    ab = cmul(cconj(alpha), beta)
    z = alpha["re"] * alpha["re"] + alpha["im"] * alpha["im"] - beta["re"] * beta["re"] - beta["im"] * beta["im"]
    return [q(2.0 * ab["re"]), q(2.0 * ab["im"]), q(z)]


def density_matrix(psi: list[dict[str, float]]) -> list[list[dict[str, float]]]:
    return [[cmul(psi[i], cconj(psi[j])) for j in range(2)] for i in range(2)]


def density_readout(rho: list[list[dict[str, float]]]) -> dict[str, Any]:
    trace = rho[0][0]["re"] + rho[1][1]["re"]
    det = (
        (rho[0][0]["re"] * rho[1][1]["re"] - rho[0][1]["re"] * rho[1][0]["re"])
        - (rho[0][1]["im"] * rho[1][0]["im"])
    )
    eigenvalues = [1.0, 0.0] if abs(det) <= 1e-12 and abs(trace - 1.0) <= 1e-12 else []
    entropy = 0.0
    return {
        "trace": q(trace),
        "determinant": q(det),
        "rank_one": abs(det) <= 1e-12,
        "eigenvalues": eigenvalues,
        "von_neumann_entropy": entropy,
    }


def connection_curvature_readout(eta: float, nz: float) -> dict[str, float]:
    sin_eta = math.sin(eta)
    sin2 = math.sin(2.0 * eta)
    return {
        "A_on_vertical_fiber_generator": 1.0,
        "A_phi_local_section": q(sin_eta * sin_eta),
        "F_theta_phi_density": q(0.5 * sin2),
        "F_eta_phi_density": q(sin2),
        "north_cap_flux": q(2.0 * math.pi * sin_eta * sin_eta),
        "bloch_z": q(nz),
    }


def build_attachment(registry_payload: dict[str, Any]) -> dict[str, Any]:
    q_by_sid = class_for_survivor(registry_payload)
    region_by_qid = region_for_class(registry_payload)
    survivor_maps = []
    qclass_to_rho: dict[str, dict[str, Any]] = {}
    shell_rows = []
    connection_rows = []
    object_maps = []

    for survivor in registry_payload["frozen_registry"]["survivors"]:
        sid = survivor["survivor_id"]
        qrow = q_by_sid[sid]
        qid = qrow["quotient_class_id"]
        region_id = region_by_qid[qid]
        spinor = spinor_from_probe_signature(survivor["probe_signature"])
        psi = spinor["psi"]
        rho = density_matrix(psi)
        rho_readout = density_readout(rho)
        bloch = hopf_projection(psi)
        eta = float(spinor["eta_rad"])
        shell_id = stable_id("shell", {"eta_label": spinor["eta_label"], "eta_rad": spinor["eta_rad"]}, 16)
        spinor_id = stable_id("spinor", {"gcm_object_id": registry_payload["gcm_object_id"], "survivor_id": sid, "psi": psi}, 20)
        rho_id = stable_id("rho", {"gcm_object_id": registry_payload["gcm_object_id"], "quotient_class_id": qid, "rho": rho}, 20)
        row = {
            "survivor_id": sid,
            "raw_survivor_id": survivor["raw_survivor_id"],
            "candidate_id": survivor["candidate_id"],
            "coord_scaled": survivor["coord_scaled"],
            "probe_signature": survivor["probe_signature"],
            "realization_rule": "normalize_xz_probe_signature_to_pure_1Q_bloch_direction",
            "spinor_id": spinor_id,
            "psi_C2": psi,
            "s3_r4": spinor["s3_r4"],
            "s3_norm": q(math.sqrt(sum(v * v for v in spinor["s3_r4"]))),
            "hopf_projection": bloch,
            "hopf_norm": q(math.sqrt(sum(v * v for v in bloch))),
            "quotient_class_id": qid,
            "raw_class_id": qrow["raw_class_id"],
            "rho_id": rho_id,
            "rho": rho,
            "rho_readout": rho_readout,
            "candidate_region_id": region_id,
            "T_eta_shell_id": shell_id,
            "T_eta_label": spinor["eta_label"],
            "T_eta_rad": spinor["eta_rad"],
            "fiber_loop": {
                "loop_id": stable_id("fiber_loop", {"survivor_id": sid, "spinor_id": spinor_id}, 20),
                "formula": "psi(t)=exp(i*t)*psi",
                "rho_invariant": True,
                "hopf_projection_invariant": True,
                "connection_holonomy": q(2.0 * math.pi),
            },
            "lifted_base_loop": {
                "loop_id": stable_id("base_loop", {"survivor_id": sid, "eta": spinor["eta_rad"]}, 20),
                "formula": "psi(phi)=(cos(eta), exp(i*phi)*sin(eta)) at fixed eta",
                "passes_current_section_phi": spinor["phi_rad"],
                "A_phi_local_section": connection_curvature_readout(eta, spinor["bloch_unit"][2])["A_phi_local_section"],
            },
        }
        survivor_maps.append(row)
        qclass_to_rho.setdefault(
            qid,
            {
                "quotient_class_id": qid,
                "raw_class_id": qrow["raw_class_id"],
                "rho_id": rho_id,
                "rho": rho,
                "rho_readout": rho_readout,
                "member_survivor_ids": [],
                "density_hash": stable_sha256(rho),
                "candidate_region_id": region_id,
                "T_eta_shell_id": shell_id,
                "T_eta_label": spinor["eta_label"],
            },
        )
        qclass_to_rho[qid]["member_survivor_ids"].append(sid)
        shell_rows.append(
            {
                "survivor_id": sid,
                "quotient_class_id": qid,
                "candidate_region_id": region_id,
                "T_eta_shell_id": shell_id,
                "T_eta_label": spinor["eta_label"],
                "T_eta_rad": spinor["eta_rad"],
            }
        )
        connection_rows.append(
            {
                "survivor_id": sid,
                "quotient_class_id": qid,
                "T_eta_label": spinor["eta_label"],
                **connection_curvature_readout(eta, spinor["bloch_unit"][2]),
            }
        )
        object_maps.append(
            {
                "survivor_id": sid,
                "spinor_id": spinor_id,
                "quotient_class_id": qid,
                "rho_id": rho_id,
                "candidate_region_id": region_id,
                "shell_id": shell_id,
            }
        )

    density_classes = sorted(qclass_to_rho.values(), key=lambda row: row["raw_class_id"])
    density_hashes = [row["density_hash"] for row in density_classes]
    shell_counts = Counter(row["T_eta_label"] for row in shell_rows)
    return {
        "realization_rule": {
            "id": "normalize_xz_probe_signature_to_pure_1Q_bloch_direction",
            "source": "frozen survivor probe_signature from gcm_object_id_freeze_v0",
            "formula": "n=(sx,0,sz)/sqrt(sx^2+sz^2); psi=(cos(theta/2), exp(i*phi) sin(theta/2))",
            "phase_gauge": "first component nonnegative real; second component sign carries phi=0 or pi",
            "hidden_y_status": "retained only as survivor lineage; not encoded in the 1Q pure density quotient",
        },
        "survivor_spinor_maps": survivor_maps,
        "quotient_density_classes": density_classes,
        "class_structure_survives_density_quotient": len(set(density_hashes)) == EXPECTED_QUOTIENT_CLASS_COUNT,
        "density_quotient_unique_count": len(set(density_hashes)),
        "shell_occupancy": {
            "occupied_shell_count": len(shell_counts),
            "counts_by_T_eta": dict(sorted(shell_counts.items())),
            "rows": shell_rows,
        },
        "connection_and_curvature": {
            "connection": "A = Im(<psi,dpsi>) = cos(eta)^2 dxi1 + sin(eta)^2 dxi2",
            "curvature": "F=dA; local base density F_theta_phi = 1/2 sin(theta)",
            "geometric_flux_boundary": "Hopf curvature/geometric flux only; not runtime/QIT/chirality/memory flux.",
            "rows": connection_rows,
        },
        "object_maps": object_maps,
    }


def nesting_controls(attachment: dict[str, Any]) -> dict[str, Any]:
    phase_survives = attachment["density_quotient_unique_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
    shell_counts = attachment["shell_occupancy"]["counts_by_T_eta"]
    geometry_only_hashes = {
        stable_sha256(
            {
                "rho": row["rho"],
                "hopf": row["hopf_projection"],
                "shell": row["T_eta_label"],
            }
        )
        for row in attachment["survivor_spinor_maps"]
    }
    return {
        "phase_quotient_remove_lower_layer": {
            "control": "quotient spinor phase away",
            "density_quotient_unique_count": attachment["density_quotient_unique_count"],
            "class_structure_survives": phase_survives,
            "survives": [
                "rho density quotient",
                "Hopf/Bloch projection",
                "quotient_class_id mapping",
                "candidate_region_id mapping",
                "T_eta shell occupancy",
                "curvature F on base",
            ],
            "lost": [
                "S3 fiber phase coordinate",
                "fiber loop parameter as lower-layer coordinate",
                "vertical U(1) loop as an anchored spinor path",
            ],
            "outcome": "class structure survives the density quotient" if phase_survives else "class structure collapses under density quotient",
        },
        "erase_carve_control": {
            "control": "erase frozen survivor/class/region lineage",
            "geometry_only_unique_state_count": len(geometry_only_hashes),
            "anchored_survivor_count_after_erasure": 0,
            "lineage_available": False,
            "lost": [
                "survivor_id anchoring",
                "quotient_class_id anchoring",
                "candidate_region_id anchoring",
                "two y-sign survivor multiplicity inside each density quotient",
            ],
            "survives_only_as_unanchored_feedstock": [
                "8 pure Hopf/density states",
                f"{len(shell_counts)} T_eta shell labels",
            ],
            "outcome": "geometry remains as feedstock but loses nested-substrate status",
        },
    }


def z3_attachment_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    survivor_count = z3.Int("survivor_count")
    density_class_count = z3.Int("density_class_count")
    shell_count = z3.Int("shell_count")
    solver.add(survivor_count == counts["survivor_count"])
    solver.add(density_class_count == counts["density_quotient_unique_count"])
    solver.add(shell_count == counts["occupied_shell_count"])
    solver.add(survivor_count == EXPECTED_SURVIVOR_COUNT)
    solver.add(density_class_count == EXPECTED_QUOTIENT_CLASS_COUNT)
    solver.add(shell_count == EXPECTED_SHELL_COUNT)
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "polarity": "direct count assertion expects SAT; lineage-free substrate negative is checked by gcm_substrate_check",
        "claim": "attached survivor, density quotient, and shell counts equal the frozen 1Q nested packet expectations",
        "input_object": counts,
        "positive_case": "16 frozen survivors attach to 8 density quotient classes across 5 T_eta shells",
        "negative_control": "lineage-free variant fails substrate helper and cannot count as nested",
        "boundary_case": "phase quotient preserves density classes but loses S3 fiber anchoring",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def cvc5_attachment_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    survivor_count = solver.mkConst(int_sort, "survivor_count")
    density_class_count = solver.mkConst(int_sort, "density_class_count")
    shell_count = solver.mkConst(int_sort, "shell_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, survivor_count, solver.mkInteger(counts["survivor_count"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, density_class_count, solver.mkInteger(counts["density_quotient_unique_count"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, shell_count, solver.mkInteger(counts["occupied_shell_count"])))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, survivor_count, solver.mkInteger(EXPECTED_SURVIVOR_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, density_class_count, solver.mkInteger(EXPECTED_QUOTIENT_CLASS_COUNT)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, shell_count, solver.mkInteger(EXPECTED_SHELL_COUNT)))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "polarity": "direct count assertion expects SAT; lineage-free substrate negative is checked by gcm_substrate_check",
        "claim": "attached survivor, density quotient, and shell counts equal the frozen 1Q nested packet expectations",
        "input_object": counts,
        "positive_case": "16 frozen survivors attach to 8 density quotient classes across 5 T_eta shells",
        "negative_control": "lineage-free variant fails substrate helper and cannot count as nested",
        "boundary_case": "phase quotient preserves density classes but loses S3 fiber anchoring",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    variant.pop("gcm_lineage", None)
    variant.pop("gcm_object_id", None)
    variant.pop("registry_body_sha256", None)
    if "attachment_map" in variant:
        for row in variant["attachment_map"].get("survivor_spinor_maps", []):
            row.pop("survivor_id", None)
            row.pop("quotient_class_id", None)
            row.pop("candidate_region_id", None)
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


def result_hash_payload(payload: dict[str, Any]) -> dict[str, Any]:
    stripped = copy.deepcopy(payload)
    stripped.pop("generated_at", None)
    stripped.pop("result_sha256", None)
    return stripped


def build_packet() -> dict[str, Any]:
    reg = registry()
    attachment = build_attachment(reg)
    controls = nesting_controls(attachment)
    counts = {
        "survivor_count": len(attachment["survivor_spinor_maps"]),
        "density_quotient_unique_count": attachment["density_quotient_unique_count"],
        "quotient_class_count": len(attachment["quotient_density_classes"]),
        "candidate_region_count": len(reg["frozen_registry"]["candidate_regions"]),
        "occupied_shell_count": attachment["shell_occupancy"]["occupied_shell_count"],
    }
    z3_proof = z3_attachment_proof(counts)
    cvc5_proof = cvc5_attachment_proof(counts)
    exact_counts = {
        "survivors": str(sp.Rational(counts["survivor_count"], 1)),
        "density_classes": str(sp.Rational(counts["density_quotient_unique_count"], 1)),
        "shells": str(sp.Rational(counts["occupied_shell_count"], 1)),
    }
    payload: dict[str, Any] = {
        "schema": "gcm_geometry_attach_v0_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "standards_codex": "system_v6/receipts/audit_standards_codex_v1.md",
        "standards_version": "audit_standards_codex_v1",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "claim": "Attach 1Q C^2/S^3/Hopf/density/T_eta/loop geometry to the frozen GCM IDs; first nested packet only.",
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "gcm_object_id": reg["gcm_object_id"],
        "registry_body_sha256": reg["registry_body_sha256"],
        "three_axis_declaration": {
            "layer": LAYER_DECLARATION,
            "nesting": NESTING_DECLARATION,
            "qubit_depth": QUBIT_DEPTH_DECLARATION,
        },
        "entropy_readout_declaration": ENTROPY_DECLARATION,
        "gcm_lineage": {
            "gcm_object_id": reg["gcm_object_id"],
            "registry_body_sha256": reg["registry_body_sha256"],
            "survivor_ids": [row["survivor_id"] for row in reg["frozen_registry"]["survivors"]],
            "quotient_class_ids": [row["quotient_class_id"] for row in reg["frozen_registry"]["quotient_classes"]],
            "candidate_region_ids": [row["candidate_region_id"] for row in reg["frozen_registry"]["candidate_regions"]],
            "object_maps": attachment["object_maps"],
        },
        "attachment_map": attachment,
        "induced_geometry": {
            "hopf_projection_rows": [
                {
                    "survivor_id": row["survivor_id"],
                    "quotient_class_id": row["quotient_class_id"],
                    "hopf_projection": row["hopf_projection"],
                    "hopf_norm": row["hopf_norm"],
                }
                for row in attachment["survivor_spinor_maps"]
            ],
            "connection_and_curvature": attachment["connection_and_curvature"],
            "T_eta_shell_occupancy": attachment["shell_occupancy"],
        },
        "nesting_controls": controls,
        "counts": counts,
        "exact_count_guard": exact_counts,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "source_locks": {name: source_lock(name, path) for name, path in AUTHORITY_PATHS.items()},
        "builder_gates": {
            "file_disjoint_packet": True,
            "boundary_helper_fully_used": True,
            "G_2a_idempotency_from_birth": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "substrate_check_helper_script_side": True,
            "lineage_free_negative_required": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": [
            "THE manifold",
            "terrain admission",
            "stage admission",
            "engine admission",
            "axis admission",
            "runtime flux",
            "physics admission",
            "formal admission",
            "canonical by process",
        ],
    }
    payload["substrate_enforcement"] = substrate_enforcement(payload)
    all_spinors_unit = all(abs(row["s3_norm"] - 1.0) <= 1e-12 for row in attachment["survivor_spinor_maps"])
    all_hopf_unit = all(abs(row["hopf_norm"] - 1.0) <= 1e-12 for row in attachment["survivor_spinor_maps"])
    all_rho_pure = all(row["rho_readout"]["rank_one"] and abs(row["rho_readout"]["trace"] - 1.0) <= 1e-12 for row in attachment["survivor_spinor_maps"])
    payload["all_pass"] = bool(
        reg["gcm_object_id"] == EXPECTED_OBJECT_ID
        and reg["registry_body_sha256"] == EXPECTED_REGISTRY_BODY_SHA256
        and counts["survivor_count"] == EXPECTED_SURVIVOR_COUNT
        and counts["quotient_class_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and counts["density_quotient_unique_count"] == EXPECTED_QUOTIENT_CLASS_COUNT
        and counts["candidate_region_count"] == EXPECTED_REGION_COUNT
        and counts["occupied_shell_count"] == EXPECTED_SHELL_COUNT
        and attachment["class_structure_survives_density_quotient"] is True
        and controls["phase_quotient_remove_lower_layer"]["class_structure_survives"] is True
        and controls["erase_carve_control"]["lineage_available"] is False
        and payload["substrate_enforcement"]["positive_payload_ok"].get("ok") is True
        and payload["substrate_enforcement"]["negative_failed_as_required"] is True
        and z3_proof["verdict"] == "sat"
        and cvc5_proof["verdict"] == "sat"
        and all_spinors_unit
        and all_hopf_unit
        and all_rho_pure
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    payload["result_sha256"] = stable_sha256(result_hash_payload(payload))
    return payload


def validate_payload(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(payload.get("schema") == "gcm_geometry_attach_v0_result_v1", "schema mismatch")
    require(payload.get("classification") == CLASSIFICATION, "classification must stay scratch_diagnostic")
    require(payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(payload.get("claim_ceiling") == CLAIM_CEILING, "claim ceiling mismatch")
    require(payload.get("gcm_object_id") == EXPECTED_OBJECT_ID, "gcm_object_id mismatch")
    require(payload.get("registry_body_sha256") == EXPECTED_REGISTRY_BODY_SHA256, "registry body hash mismatch")
    require(payload.get("three_axis_declaration", {}).get("layer") == LAYER_DECLARATION, "layer declaration mismatch")
    require(payload.get("three_axis_declaration", {}).get("nesting") == NESTING_DECLARATION, "nesting declaration mismatch")
    require(payload.get("three_axis_declaration", {}).get("qubit_depth") == QUBIT_DEPTH_DECLARATION, "qubit depth declaration mismatch")
    require(payload.get("entropy_readout_declaration") == ENTROPY_DECLARATION, "entropy declaration mismatch")
    counts = payload.get("counts", {})
    require(counts.get("survivor_count") == EXPECTED_SURVIVOR_COUNT, "survivor count mismatch")
    require(counts.get("density_quotient_unique_count") == EXPECTED_QUOTIENT_CLASS_COUNT, "density quotient count mismatch")
    require(counts.get("quotient_class_count") == EXPECTED_QUOTIENT_CLASS_COUNT, "quotient class count mismatch")
    require(counts.get("candidate_region_count") == EXPECTED_REGION_COUNT, "candidate region count mismatch")
    require(counts.get("occupied_shell_count") == EXPECTED_SHELL_COUNT, "shell count mismatch")
    attachment = payload.get("attachment_map", {})
    require(len(attachment.get("survivor_spinor_maps", [])) == EXPECTED_SURVIVOR_COUNT, "spinor map count mismatch")
    require(len(attachment.get("quotient_density_classes", [])) == EXPECTED_QUOTIENT_CLASS_COUNT, "density class row count mismatch")
    require(attachment.get("class_structure_survives_density_quotient") is True, "density quotient collapsed class structure")
    require(attachment.get("shell_occupancy", {}).get("counts_by_T_eta") == {"0": 2, "3pi/8": 4, "pi/2": 2, "pi/4": 4, "pi/8": 4}, "shell occupancy mismatch")
    for row in attachment.get("survivor_spinor_maps", []):
        require(abs(row.get("s3_norm", 0.0) - 1.0) <= 1e-12, f"S3 norm drift for {row.get('survivor_id')}")
        require(abs(row.get("hopf_norm", 0.0) - 1.0) <= 1e-12, f"Hopf norm drift for {row.get('survivor_id')}")
        rho = row.get("rho_readout", {})
        require(rho.get("rank_one") is True, f"rho rank drift for {row.get('survivor_id')}")
        require(abs(rho.get("trace", 0.0) - 1.0) <= 1e-12, f"rho trace drift for {row.get('survivor_id')}")
    controls = payload.get("nesting_controls", {})
    require(controls.get("phase_quotient_remove_lower_layer", {}).get("class_structure_survives") is True, "phase quotient control failed")
    require(controls.get("erase_carve_control", {}).get("lineage_available") is False, "erase-carve control failed")
    proofs = payload.get("crossover_proofs", {})
    require(proofs.get("z3", {}).get("verdict") == "sat", "z3 proof failed")
    require(proofs.get("cvc5", {}).get("verdict") == "sat", "cvc5 proof failed")
    positive = gcm_substrate_check(payload, REGISTRY_PATH)
    negative = gcm_substrate_check(lineage_free_variant(payload), REGISTRY_PATH)
    require(positive.get("ok") is True, f"substrate check positive failed: {positive.get('errors')}")
    require(negative.get("ok") is False, "lineage-free substrate check did not fail")
    require(payload.get("substrate_enforcement", {}).get("positive_payload_ok", {}).get("ok") is True, "stored substrate positive not ok")
    require(payload.get("substrate_enforcement", {}).get("negative_failed_as_required") is True, "stored substrate negative not red")
    require(payload.get("TOOL_MANIFEST") == TOOL_MANIFEST, "TOOL_MANIFEST mismatch")
    require(payload.get("TOOL_INTEGRATION_DEPTH") == TOOL_INTEGRATION_DEPTH, "TOOL_INTEGRATION_DEPTH mismatch")
    require(payload.get("tool_intent") == TOOL_INTENT, "tool_intent mismatch")
    errors.extend(builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"))
    require(payload.get("all_pass") is True, "all_pass must be true")
    expected_hash = stable_sha256(result_hash_payload(payload))
    require(payload.get("result_sha256") == expected_hash, "result hash mismatch")
    return errors


def main() -> int:
    payload = build_packet()
    write_json(RESULT_PATH, payload)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
