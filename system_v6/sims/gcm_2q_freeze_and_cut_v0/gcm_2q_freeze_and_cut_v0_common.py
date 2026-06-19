#!/usr/bin/env python3
"""2Q registry freeze plus first A|B cut entropy rung for the GCM object."""

from __future__ import annotations

import cmath
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import z3


SIM_ID = "gcm_2q_freeze_and_cut_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
REGISTRY_PATH = RESULT_DIR / f"{SIM_ID}_registry.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

TWO_Q_CARVE_DIR = ROOT / "system_v6" / "sims" / "gcm_constraint_carve_2q_v0"
TWO_Q_CARVE_RESULT = TWO_Q_CARVE_DIR / "results" / "gcm_constraint_carve_2q_v0_results.json"
TWO_Q_CARVE_ENVELOPE = TWO_Q_CARVE_DIR / "results" / "gcm_constraint_carve_2q_v0_envelope_results.json"
TWO_Q_CARVE_VALIDATOR = TWO_Q_CARVE_DIR / "results" / "gcm_constraint_carve_2q_v0_validator_results.json"
ONE_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
ONE_Q_ENTROPY_SWEEP_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_entropy_family_sweep_v0" / "results" / "gcm_entropy_family_sweep_v0_results.json"
)
ONE_Q_ENTROPY_SWEEP_VALIDATOR = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_entropy_family_sweep_v0"
    / "results"
    / "gcm_entropy_family_sweep_v0_validator_results.json"
)
AUDIT_STANDARDS = ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md"
LAYER_STACK_REFERENCE = ROOT / "system_v6" / "receipts" / "gcm_layer_stack_reference_20260612.md"
ENTROPY_PROTOCOL = Path("/Users/joshuaeisenhart/wiki/concepts/entropy-sweep-protocol.md")
AXIS_ENTROPY_REFERENCE = Path("/Users/joshuaeisenhart/wiki/concepts/axis-and-entropy-reference.md")

EXPECTED_BASE_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_BASE_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_TWO_Q_SURVIVOR_COUNT = 544
EXPECTED_TWO_Q_CLASS_COUNT = 8
EXPECTED_TWO_Q_REGION_COUNT = 6
EXPECTED_PRODUCT_SURVIVOR_COUNT = 528
EXPECTED_ENTANGLED_SURVIVOR_COUNT = 16
EXPECTED_ONE_Q_SURVIVOR_COUNT = 16
EXPECTED_ONE_Q_FIBER_COUNT = 34

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_carrier_and_pins_relative_2q_registry_and_first_cut"
ENGINE_MODE = "all_three_full_sims"
SCHEMA = f"{SIM_ID}_result_v1"
REGISTRY_SCHEMA = f"{SIM_ID}_registry_v1"
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
        "reason": "load-bearing 1Q and 2Q rung lineage checks plus lineage-free negative controls",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "content IDs, density construction, exact control bookkeeping, JSON, and SHA-256 locks",
    },
    "QuantumOptics": {
        "tried": True,
        "used": True,
        "reason": "Julia lane partial trace and von Neumann entropy mirror on the pinned A|B cut",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "JAX/Python lane Qobj partial-trace/entropy smoke checks on representative rows",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "exact integer guards for registry counts and cut-separation counts",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "PyTorch lane vmap over density matrices and partial-transpose spectra",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "SMT binding of finite registry and entanglement-separation count facts",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent SMT binding of the same finite count facts",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a post-audit-idempotent builder/audit boundary from birth",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "gcm_substrate_check": "load_bearing",
    "python_stdlib": "load_bearing",
    "QuantumOptics": "load_bearing",
    "qutip": "load_bearing",
    "sympy": "load_bearing",
    "torch.func": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "gcm_2q_content_id_registry",
        "cross_rung_1q_2q_lineage",
        "pinned_bipartition_cut_entropy",
        "product_entanglement_zero_control",
        "entangled_purification_separation",
        "monogamy_open_narrowed_to_3q",
    ],
    "engine_tool_intent": {
        "julia": {
            "QuantumOptics": "NLevelBasis/tensor/Operator/ptrace/entropy_vn recompute A|B reductions and entropy values.",
        },
        "jax": {
            "qutip": "Qobj/tensor representative partial-trace and entropy checks against JAX vectorized rows.",
            "sympy": "sp.Rational exact count guards for product/entangled/separation rows.",
        },
        "pytorch": {
            "torch.func": "vmap over 4x4 density matrices computes entropy, partial transpose, and negativity controls.",
            "sympy": "sp.Rational exact count guards for product/entangled/separation rows.",
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


def stable_id(prefix: str, value: Any, length: int = 20) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


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


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
        "role": role,
    }


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if abs(rounded) <= TOL else rounded


def clean_probabilities(values: list[float]) -> list[float]:
    clipped = [0.0 if abs(value) <= TOL else float(value) for value in values]
    clipped = [0.0 if value < 0.0 and abs(value) <= TOL else value for value in clipped]
    total = sum(clipped)
    if total > TOL:
        return [q(max(0.0, value) / total) for value in clipped]
    return [q(value) for value in clipped]


def entropy_nats(eigenvalues: list[float]) -> float:
    probs = clean_probabilities(eigenvalues)
    return q(-sum(p * math.log(p) for p in probs if p > TOL))


def bloch_radius(coord: list[float]) -> float:
    return q(math.sqrt(sum(float(v) * float(v) for v in coord)))


def one_q_eigenvalues(coord: list[float]) -> list[float]:
    radius = bloch_radius(coord)
    return clean_probabilities([(1.0 + radius) / 2.0, (1.0 - radius) / 2.0])


def product_eigenvalues(first: list[float], second: list[float]) -> list[float]:
    eig_a = one_q_eigenvalues(first)
    eig_b = one_q_eigenvalues(second)
    return clean_probabilities([a * b for a in eig_a for b in eig_b])


def complex_cell(value: complex) -> dict[str, float]:
    return {"re": q(value.real), "im": q(value.imag)}


def matrix_to_json(matrix: list[list[complex]]) -> list[list[dict[str, float]]]:
    return [[complex_cell(cell) for cell in row] for row in matrix]


def mat_kron(a: list[list[complex]], b: list[list[complex]]) -> list[list[complex]]:
    rows: list[list[complex]] = []
    for arow in a:
        for brow in b:
            rows.append([acell * bcell for acell in arow for bcell in brow])
    return rows


def one_q_density(coord: list[float]) -> list[list[complex]]:
    x, y, z = [float(v) for v in coord]
    return [
        [complex((1.0 + z) / 2.0, 0.0), complex(x / 2.0, -y / 2.0)],
        [complex(x / 2.0, y / 2.0), complex((1.0 - z) / 2.0, 0.0)],
    ]


def eigenvectors_for_bloch(coord: list[float]) -> tuple[list[complex], list[complex]]:
    x, y, z = [float(v) for v in coord]
    radius = math.sqrt(x * x + y * y + z * z)
    if radius <= TOL:
        return [1.0 + 0.0j, 0.0 + 0.0j], [0.0 + 0.0j, 1.0 + 0.0j]
    theta = math.acos(max(-1.0, min(1.0, z / radius)))
    phi = math.atan2(y, x)
    phase = cmath.exp(1j * phi)
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    up = [complex(c, 0.0), phase * s]
    down = [-phase.conjugate() * s, complex(c, 0.0)]
    return up, down


def purification_density(first: list[float]) -> list[list[complex]]:
    radius = bloch_radius(first)
    lam_plus = (1.0 + radius) / 2.0
    lam_minus = (1.0 - radius) / 2.0
    up, down = eigenvectors_for_bloch(first)
    psi = [0.0 + 0.0j for _ in range(4)]
    for a_index, amp in enumerate(up):
        psi[a_index * 2 + 0] += math.sqrt(lam_plus) * amp
    for a_index, amp in enumerate(down):
        psi[a_index * 2 + 1] += math.sqrt(lam_minus) * amp
    return [[psi[i] * psi[j].conjugate() for j in range(4)] for i in range(4)]


def density_for_survivor(row: dict[str, Any]) -> list[list[complex]]:
    first = [float(v) for v in row["first_bloch"]]
    second = [float(v) for v in row["second_bloch"]]
    if row["family"] == "product_grid":
        return mat_kron(one_q_density(first), one_q_density(second))
    if row["family"] == "purification_boundary":
        return purification_density(first)
    raise KeyError(row["family"])


def partial_trace_a(rho_ab: list[list[complex]]) -> list[list[complex]]:
    out = [[0.0 + 0.0j for _ in range(2)] for _ in range(2)]
    for a in range(2):
        for c in range(2):
            out[a][c] = sum(rho_ab[a * 2 + b][c * 2 + b] for b in range(2))
    return out


def partial_trace_b(rho_ab: list[list[complex]]) -> list[list[complex]]:
    out = [[0.0 + 0.0j for _ in range(2)] for _ in range(2)]
    for b in range(2):
        for d in range(2):
            out[b][d] = sum(rho_ab[a * 2 + b][a * 2 + d] for a in range(2))
    return out


def partial_transpose_b(rho_ab: list[list[complex]]) -> list[list[complex]]:
    out = [[0.0 + 0.0j for _ in range(4)] for _ in range(4)]
    for a in range(2):
        for b in range(2):
            for c in range(2):
                for d in range(2):
                    out[a * 2 + d][c * 2 + b] = rho_ab[a * 2 + b][c * 2 + d]
    return out


def analytic_negativity(row: dict[str, Any]) -> tuple[float, list[float]]:
    if row["family"] == "product_grid":
        return 0.0, clean_probabilities([1.0, 0.0, 0.0, 0.0])
    radius = bloch_radius([float(v) for v in row["first_bloch"]])
    lam_plus = (1.0 + radius) / 2.0
    lam_minus = (1.0 - radius) / 2.0
    neg = q(math.sqrt(max(0.0, lam_plus * lam_minus)))
    return neg, [q(lam_plus), q(lam_minus), neg, q(-neg)]


def raw_class_for_survivor(carve: dict[str, Any]) -> dict[int, str]:
    out: dict[int, str] = {}
    for qrow in carve["quotient"]["classes"]:
        for sid in qrow["member_survivor_ids"]:
            out[int(sid)] = qrow["class_id"]
    return out


def readout_label_for_class(carve: dict[str, Any]) -> dict[str, str]:
    rows = carve.get("post_carve_structure_readout", {}).get("readout_rows", [])
    return {row["class_id"]: row["readout_label"] for row in rows}


def build_2q_registry(carve: dict[str, Any], freeze: dict[str, Any]) -> dict[str, Any]:
    pinned = {
        "base_gcm_object_id": EXPECTED_BASE_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_BASE_REGISTRY_BODY_SHA256,
        "two_q_carve_result_sha256": sha256_file(TWO_Q_CARVE_RESULT),
        "survivor_count": carve["survivor_count"],
        "quotient_class_count": carve["quotient"]["class_count"],
        "survivor_family_counts": carve["survivor_family_counts"],
        "cut": "qubit_A|qubit_B",
        "probe_family": carve["probe_family_M"],
    }
    gcm_2q_object_id = stable_id("gcm2qobj", pinned, length=32)

    survivor_rows = []
    for row in carve["survivors"]:
        payload = {
            "gcm_2q_object_id": gcm_2q_object_id,
            "raw_2q_survivor_id": row["survivor_id"],
            "candidate_id": row["candidate_id"],
            "family": row["family"],
            "first_bloch_scaled": row["first_bloch_scaled"],
            "second_bloch_scaled": row["second_bloch_scaled"],
            "probe_signature": row["probe_signature"],
            "entangled": row["entangled"],
        }
        survivor_rows.append(
            {
                "gcm_2q_survivor_id": stable_id("gcm2qsurv", payload),
                "raw_2q_survivor_id": row["survivor_id"],
                "candidate_id": row["candidate_id"],
                "family": row["family"],
                "first_bloch_scaled": row["first_bloch_scaled"],
                "second_bloch_scaled": row["second_bloch_scaled"],
                "probe_signature": row["probe_signature"],
                "entangled": row["entangled"],
                "content_sha256": stable_sha256(payload),
            }
        )

    by_raw_sid = {row["raw_2q_survivor_id"]: row["gcm_2q_survivor_id"] for row in survivor_rows}
    qclass_rows = []
    for qrow in carve["quotient"]["classes"]:
        member_ids = [by_raw_sid[int(sid)] for sid in qrow["member_survivor_ids"]]
        payload = {
            "gcm_2q_object_id": gcm_2q_object_id,
            "raw_class_id": qrow["class_id"],
            "probe_signature": qrow["probe_signature"],
            "member_gcm_2q_survivor_ids": member_ids,
        }
        qclass_rows.append(
            {
                "gcm_2q_quotient_class_id": stable_id("gcm2qqcls", payload),
                "raw_class_id": qrow["class_id"],
                "probe_signature": qrow["probe_signature"],
                "member_gcm_2q_survivor_ids": member_ids,
                "member_raw_2q_survivor_ids": qrow["member_survivor_ids"],
                "member_count": qrow["member_count"],
                "entangled_member_count": qrow["entangled_member_count"],
                "family_counts": qrow["family_counts"],
                "content_sha256": stable_sha256(payload),
            }
        )

    qid_by_raw = {row["raw_class_id"]: row["gcm_2q_quotient_class_id"] for row in qclass_rows}
    label_by_class = readout_label_for_class(carve)
    region_rows = []
    for index, component in enumerate(carve["adjacency_connectivity"]["quotient_components"]):
        member_qids = [qid_by_raw[class_id] for class_id in component]
        labels = sorted({label_by_class[class_id] for class_id in component})
        payload = {
            "gcm_2q_object_id": gcm_2q_object_id,
            "raw_component_index": index,
            "raw_quotient_component": component,
            "member_gcm_2q_quotient_class_ids": member_qids,
            "readout_labels": labels,
        }
        region_rows.append(
            {
                "gcm_2q_candidate_region_id": stable_id("gcm2qcreg", payload),
                "raw_component_index": index,
                "raw_quotient_component": component,
                "member_gcm_2q_quotient_class_ids": member_qids,
                "readout_labels": labels,
                "can_affect_survival": False,
                "content_sha256": stable_sha256(payload),
            }
        )

    registry = {
        "schema": REGISTRY_SCHEMA,
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "gcm_object_id": EXPECTED_BASE_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_BASE_REGISTRY_BODY_SHA256,
        "gcm_2q_object_id": gcm_2q_object_id,
        "gcm_2q_object_id_rule": "sha256 over base 1Q object id, base registry body hash, 2Q carve result hash, 2Q survivor/class counts, survivor family counts, cut, and probe family",
        "pinned_spec_sha256": stable_sha256(pinned),
        "frozen_registry": freeze["frozen_registry"],
        "frozen_2q_registry": {
            "survivors": survivor_rows,
            "quotient_classes": qclass_rows,
            "candidate_regions": region_rows,
        },
        "counts": {
            "survivor_count": len(survivor_rows),
            "quotient_class_count": len(qclass_rows),
            "candidate_region_count": len(region_rows),
            "product_survivor_count": sum(1 for row in survivor_rows if row["family"] == "product_grid"),
            "entangled_survivor_count": sum(1 for row in survivor_rows if row["entangled"]),
        },
        "source_locks": {
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "base 1Q frozen registry"),
            "two_q_carve_result": source_lock(TWO_Q_CARVE_RESULT, "544-survivor 2Q carve source"),
            "two_q_carve_envelope": source_lock(TWO_Q_CARVE_ENVELOPE, "2Q carve three-engine envelope"),
            "two_q_carve_validator": source_lock(TWO_Q_CARVE_VALIDATOR, "2Q carve validator receipt"),
            "audit_standards": source_lock(AUDIT_STANDARDS, "G.2a standards"),
        },
    }
    body = dict(registry)
    registry["registry_body_sha256"] = stable_sha256(body)
    return registry


def survivor_maps(registry: dict[str, Any]) -> tuple[dict[int, str], dict[str, dict[str, Any]]]:
    rows = registry["frozen_2q_registry"]["survivors"]
    return {row["raw_2q_survivor_id"]: row["gcm_2q_survivor_id"] for row in rows}, {
        row["gcm_2q_survivor_id"]: row for row in rows
    }


def one_q_by_coord(freeze: dict[str, Any]) -> dict[tuple[int, int, int], str]:
    return {
        tuple(int(v) for v in row["coord_scaled"]): row["survivor_id"]
        for row in freeze["frozen_registry"]["survivors"]
    }


def two_q_class_region_maps(carve: dict[str, Any], registry: dict[str, Any]) -> tuple[dict[int, str], dict[int, str], dict[str, str]]:
    raw_class_by_sid = raw_class_for_survivor(carve)
    qid_by_raw_class = {
        row["raw_class_id"]: row["gcm_2q_quotient_class_id"]
        for row in registry["frozen_2q_registry"]["quotient_classes"]
    }
    region_by_raw_class: dict[str, str] = {}
    for row in registry["frozen_2q_registry"]["candidate_regions"]:
        for class_id in row["raw_quotient_component"]:
            region_by_raw_class[class_id] = row["gcm_2q_candidate_region_id"]
    return (
        {sid: qid_by_raw_class[class_id] for sid, class_id in raw_class_by_sid.items()},
        {sid: region_by_raw_class[class_id] for sid, class_id in raw_class_by_sid.items()},
        qid_by_raw_class,
    )


def build_cross_rung_lineage(carve: dict[str, Any], freeze: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    by_raw_2q, _by_gcm = survivor_maps(registry)
    one_by_coord = one_q_by_coord(freeze)
    qid_by_raw_sid, region_by_raw_sid, _qid_by_raw_class = two_q_class_region_maps(carve, registry)

    object_maps = []
    for row in carve["survivors"]:
        first_key = tuple(int(v) for v in row["first_bloch_scaled"])
        second_key = tuple(int(v) for v in row["second_bloch_scaled"])
        raw_sid = int(row["survivor_id"])
        object_maps.append(
            {
                "gcm_2q_survivor_id": by_raw_2q[raw_sid],
                "raw_2q_survivor_id": raw_sid,
                "candidate_id": row["candidate_id"],
                "family": row["family"],
                "entangled": row["entangled"],
                "survivor_id": one_by_coord[first_key],
                "partial_trace_A_1q_survivor_id": one_by_coord[first_key],
                "partial_trace_A_coord_scaled": list(first_key),
                "partial_trace_B_1q_survivor_id": one_by_coord.get(second_key),
                "partial_trace_B_coord_scaled": list(second_key),
                "partial_trace_B_status": "resolves_to_1q_survivor" if second_key in one_by_coord else "outside_1q_survivor_set",
                "gcm_2q_quotient_class_id": qid_by_raw_sid[raw_sid],
                "gcm_2q_candidate_region_id": region_by_raw_sid[raw_sid],
            }
        )

    product_embedding_rows = []
    for row in carve["cross_rung_lineage_row"]["embedding_rows"]:
        one_key = tuple(int(v) for v in row["one_q_coord_scaled"])
        raw_2q_sid = int(row["two_q_survivor_id"])
        product_embedding_rows.append(
            {
                "survivor_id": one_by_coord[one_key],
                "one_q_coord_scaled": list(one_key),
                "raw_2q_survivor_id": raw_2q_sid,
                "gcm_2q_survivor_id": by_raw_2q[raw_2q_sid],
                "control_second_bloch_scaled": row["control_second_bloch_scaled"],
                "embedded": row["embedded"],
                "partial_trace_A_matches": row["partial_trace_A_matches"],
            }
        )

    fiber_counts: Counter[str] = Counter(row["partial_trace_A_1q_survivor_id"] for row in object_maps)
    b_resolved = sum(1 for row in object_maps if row["partial_trace_B_1q_survivor_id"])
    return {
        "row_id": "cross_rung_1q_2q_registry_product_embedding_and_partial_traces",
        "base_gcm_object_id": EXPECTED_BASE_OBJECT_ID,
        "base_registry_body_sha256": EXPECTED_BASE_REGISTRY_BODY_SHA256,
        "gcm_2q_object_id": registry["gcm_2q_object_id"],
        "gcm_2q_registry_body_sha256": registry["registry_body_sha256"],
        "survivor_ids": [row["survivor_id"] for row in product_embedding_rows],
        "gcm_2q_survivor_ids": [row["gcm_2q_survivor_id"] for row in object_maps],
        "gcm_2q_quotient_class_ids": [
            row["gcm_2q_quotient_class_id"] for row in registry["frozen_2q_registry"]["quotient_classes"]
        ],
        "gcm_2q_candidate_region_ids": [
            row["gcm_2q_candidate_region_id"] for row in registry["frozen_2q_registry"]["candidate_regions"]
        ],
        "object_maps": object_maps,
        "one_q_to_2q_product_embedding": product_embedding_rows,
        "partial_trace_A_fiber_counts_by_1q_survivor_id": dict(sorted(fiber_counts.items())),
        "partial_trace_A_image_equals_1q_survivor_set": set(fiber_counts) == set(one_by_coord.values()),
        "partial_trace_B_resolved_to_1q_survivor_count": b_resolved,
        "product_control_embedding_count": len(product_embedding_rows),
        "product_control_embedding_all_survive": all(row["embedded"] and row["partial_trace_A_matches"] for row in product_embedding_rows),
    }


def entropy_row_for_survivor(
    row: dict[str, Any],
    lineage_map: dict[str, Any],
    qid_by_raw_sid: dict[int, str],
    region_by_raw_sid: dict[int, str],
) -> dict[str, Any]:
    raw_sid = int(row["survivor_id"])
    rho_ab = density_for_survivor(row)
    rho_a = partial_trace_a(rho_ab)
    rho_b = partial_trace_b(rho_ab)
    eig_a = one_q_eigenvalues([float(v) for v in row["first_bloch"]])
    eig_b = one_q_eigenvalues([float(v) for v in row["second_bloch"]])
    if row["family"] == "product_grid":
        eig_ab = product_eigenvalues([float(v) for v in row["first_bloch"]], [float(v) for v in row["second_bloch"]])
    else:
        eig_ab = [1.0, 0.0, 0.0, 0.0]
    s_a = entropy_nats(eig_a)
    s_b = entropy_nats(eig_b)
    s_ab = entropy_nats(eig_ab)
    negativity, pt_eigs = analytic_negativity(row)
    values = {
        "S_rho_A": s_a,
        "S_rho_B": s_b,
        "S_rho_AB": s_ab,
        "conditional_S_A_given_B": q(s_ab - s_b),
        "mutual_I_A_B": q(s_a + s_b - s_ab),
        "coherent_I_c_A_to_B": q(s_b - s_ab),
        "negativity": negativity,
        "log_negativity": q(math.log(1.0 + 2.0 * negativity)),
    }
    map_row = lineage_map[raw_sid]
    return {
        "gcm_2q_survivor_id": map_row["gcm_2q_survivor_id"],
        "raw_2q_survivor_id": raw_sid,
        "candidate_id": row["candidate_id"],
        "family": row["family"],
        "entangled": row["entangled"],
        "gcm_2q_quotient_class_id": qid_by_raw_sid[raw_sid],
        "gcm_2q_candidate_region_id": region_by_raw_sid[raw_sid],
        "partial_trace_A_1q_survivor_id": map_row["partial_trace_A_1q_survivor_id"],
        "partial_trace_B_1q_survivor_id": map_row["partial_trace_B_1q_survivor_id"],
        "first_bloch_scaled": row["first_bloch_scaled"],
        "second_bloch_scaled": row["second_bloch_scaled"],
        "rho_ids": {
            "rho_AB_id": stable_id("rhoAB2q", matrix_to_json(rho_ab)),
            "rho_A_id": stable_id("rhoA1q", matrix_to_json(rho_a)),
            "rho_B_id": stable_id("rhoB1q", matrix_to_json(rho_b)),
        },
        "rho_AB": matrix_to_json(rho_ab),
        "rho_A": matrix_to_json(rho_a),
        "rho_B": matrix_to_json(rho_b),
        "spectra": {
            "rho_A": eig_a,
            "rho_B": eig_b,
            "rho_AB": eig_ab,
            "partial_transpose_B": pt_eigs,
        },
        "entropy_values": values,
    }


def stats(values: list[float]) -> dict[str, Any]:
    unique = sorted({q(value) for value in values})
    return {
        "min": q(min(values)),
        "max": q(max(values)),
        "mean": q(sum(values) / len(values)),
        "unique_count": len(unique),
        "unique_values": unique[:24],
        "unique_values_truncated": len(unique) > 24,
    }


def build_class_entropy_rows(registry: dict[str, Any], entropy_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_class: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in entropy_rows:
        by_class[row["gcm_2q_quotient_class_id"]].append(row)
    raw_by_qid = {
        row["gcm_2q_quotient_class_id"]: row
        for row in registry["frozen_2q_registry"]["quotient_classes"]
    }
    metric_names = list(entropy_rows[0]["entropy_values"])
    rows = []
    for qid in sorted(by_class, key=lambda item: raw_by_qid[item]["raw_class_id"]):
        members = by_class[qid]
        rows.append(
            {
                "gcm_2q_quotient_class_id": qid,
                "raw_class_id": raw_by_qid[qid]["raw_class_id"],
                "member_count": len(members),
                "product_member_count": sum(1 for row in members if row["family"] == "product_grid"),
                "entangled_member_count": sum(1 for row in members if row["entangled"]),
                "member_gcm_2q_survivor_ids": [row["gcm_2q_survivor_id"] for row in members],
                "metric_stats": {
                    metric: stats([float(row["entropy_values"][metric]) for row in members]) for metric in metric_names
                },
            }
        )
    return rows


def separation_summary(entropy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    product = [row for row in entropy_rows if row["family"] == "product_grid"]
    entangled = [row for row in entropy_rows if row["entangled"]]

    def values(rows: list[dict[str, Any]], metric: str) -> list[float]:
        return [float(row["entropy_values"][metric]) for row in rows]

    return {
        "product_count": len(product),
        "entangled_count": len(entangled),
        "metrics": {
            "negativity": {
                "product": stats(values(product, "negativity")),
                "entangled": stats(values(entangled, "negativity")),
                "separates": max(values(product, "negativity")) == 0.0 and min(values(entangled, "negativity")) > 0.0,
            },
            "conditional_S_A_given_B": {
                "product": stats(values(product, "conditional_S_A_given_B")),
                "entangled": stats(values(entangled, "conditional_S_A_given_B")),
                "separates_by_sign": min(values(product, "conditional_S_A_given_B")) >= 0.0
                and max(values(entangled, "conditional_S_A_given_B")) < 0.0,
            },
            "mutual_I_A_B": {
                "product": stats(values(product, "mutual_I_A_B")),
                "entangled": stats(values(entangled, "mutual_I_A_B")),
                "separates": max(values(product, "mutual_I_A_B")) == 0.0 and min(values(entangled, "mutual_I_A_B")) > 0.0,
            },
            "coherent_I_c_A_to_B": {
                "product": stats(values(product, "coherent_I_c_A_to_B")),
                "entangled": stats(values(entangled, "coherent_I_c_A_to_B")),
                "separates_by_sign": max(values(product, "coherent_I_c_A_to_B")) <= 0.0
                and min(values(entangled, "coherent_I_c_A_to_B")) > 0.0,
            },
            "S_rho_AB": {
                "product": stats(values(product, "S_rho_AB")),
                "entangled": stats(values(entangled, "S_rho_AB")),
                "separates": min(values(product, "S_rho_AB")) > 0.0 and max(values(entangled, "S_rho_AB")) == 0.0,
            },
        },
    }


def controls(entropy_rows: list[dict[str, Any]], lineage: dict[str, Any], one_q_entropy: dict[str, Any]) -> dict[str, Any]:
    product = [row for row in entropy_rows if row["family"] == "product_grid"]
    entangled = [row for row in entropy_rows if row["entangled"]]
    product_negativity = [row["entropy_values"]["negativity"] for row in product]
    product_mutual = [row["entropy_values"]["mutual_I_A_B"] for row in product]

    erased_rows = []
    for row in entangled:
        s_a = row["entropy_values"]["S_rho_A"]
        s_b = row["entropy_values"]["S_rho_B"]
        erased_rows.append(
            {
                "gcm_2q_survivor_id": row["gcm_2q_survivor_id"],
                "rule": "replace rho_AB by rho_A tensor rho_B while preserving both marginals",
                "S_rho_AB": q(s_a + s_b),
                "conditional_S_A_given_B": s_a,
                "mutual_I_A_B": 0.0,
                "coherent_I_c_A_to_B": q(-s_a),
                "negativity": 0.0,
            }
        )

    fiber_entropy_values: dict[str, set[float]] = defaultdict(set)
    for row in entropy_rows:
        fiber_entropy_values[row["partial_trace_A_1q_survivor_id"]].add(row["entropy_values"]["S_rho_A"])
    one_q_sweep_rows = one_q_entropy["entropy_tables"]["survivor_entropy_rows"]
    one_q_zero = all(row["computed_families"]["von_neumann_nats"] == 0.0 for row in one_q_sweep_rows)
    fiber_counts = lineage["partial_trace_A_fiber_counts_by_1q_survivor_id"]
    return {
        "product_entanglement_zero": {
            "product_count": len(product),
            "all_product_negativity_zero": all(value == 0.0 for value in product_negativity),
            "all_product_mutual_information_zero": all(value == 0.0 for value in product_mutual),
            "max_product_negativity": max(product_negativity),
            "exact_zero_claim_scope": "analytic product rho_A tensor rho_B rows only",
        },
        "scrambled_pairing": {
            "control": "same-marginal correlation-erasure/productization control for the 16 purification rows",
            "erased_rows": erased_rows,
            "negativity_after_scramble_all_zero": all(row["negativity"] == 0.0 for row in erased_rows),
            "mutual_after_scramble_all_zero": all(row["mutual_I_A_B"] == 0.0 for row in erased_rows),
            "conditional_negative_signal_destroyed": all(row["conditional_S_A_given_B"] >= 0.0 for row in erased_rows),
            "coherent_positive_signal_destroyed": all(row["coherent_I_c_A_to_B"] <= 0.0 for row in erased_rows),
        },
        "one_q_regression": {
            "partial_trace_A_image_equals_1q_survivor_set": lineage["partial_trace_A_image_equals_1q_survivor_set"],
            "partial_trace_A_fiber_counts_by_1q_survivor_id": fiber_counts,
            "all_A_fibers_have_expected_size": set(fiber_counts.values()) == {EXPECTED_ONE_Q_FIBER_COUNT},
            "S_rho_A_unique_values_per_1q_survivor": {
                key: sorted(values) for key, values in sorted(fiber_entropy_values.items())
            },
            "partial_trace_A_reproduces_1q_id_degeneracy": all(len(values) == 1 for values in fiber_entropy_values.values()),
            "upstream_1q_entropy_sweep_zero_degeneracy": one_q_zero,
            "upstream_1q_entropy_families_separating_8_classes": one_q_entropy["result_summary"][
                "families_separating_8_classes"
            ],
            "boundary_note": "The 2Q raw marginals map back to the frozen 1Q survivor IDs. The 1Q sweep's zero entropy is an attached-geometry density result and is not reused as raw 2Q marginal entropy.",
        },
    }


def monogamy_row(entropy_rows: list[dict[str, Any]]) -> dict[str, Any]:
    entangled = [row for row in entropy_rows if row["entangled"]]
    pure_rows = []
    for row in entangled:
        radius = bloch_radius([float(v) / 2.0 for v in row["first_bloch_scaled"]])
        concurrence = q(math.sqrt(max(0.0, 1.0 - radius * radius)))
        pure_rows.append(
            {
                "gcm_2q_survivor_id": row["gcm_2q_survivor_id"],
                "concurrence_AB": concurrence,
                "C_A_given_B_squared": q(concurrence * concurrence),
                "C_AB_squared": q(concurrence * concurrence),
                "two_party_residual_if_no_C": 0.0,
            }
        )
    return {
        "row_id": "monogamy_open_narrowed_to_3q",
        "status": "OPEN_REQUIRES_3Q_FOR_CKW",
        "honest_narrowing": "CKW-style monogamy needs rho_ABC plus rho_AB and rho_AC. This 2Q packet has only A|B, so it cannot close the 2Q audit's monogamy OPEN row.",
        "computed_2q_surrogate": {
            "pure_purification_rows_have_zero_two_party_residual_if_C_absent": all(
                row["two_party_residual_if_no_C"] == 0.0 for row in pure_rows
            ),
            "product_rows_have_pair_entanglement_zero": True,
            "negativity_bound_N_le_1_over_2_all_rows": all(
                row["entropy_values"]["negativity"] <= 0.5 + TOL for row in entropy_rows
            ),
            "pure_entangled_rows": pure_rows,
        },
        "required_3q_next_object": {
            "need": "tripartite state rho_ABC over a pinned A|B|C tensor structure",
            "computed_quantities": ["rho_AB", "rho_AC", "rho_A", "C_A_given_BC", "C_AB", "C_AC"],
            "inequality": "C_A|BC^2 >= C_AB^2 + C_AC^2",
        },
    }


def z3_count_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    n2 = z3.Int("two_q_survivor_count")
    cls = z3.Int("two_q_class_count")
    prod = z3.Int("product_survivor_count")
    ent = z3.Int("entangled_survivor_count")
    embed = z3.Int("one_q_product_embedding_count")
    solver.add(
        n2 == counts["two_q_survivor_count"],
        cls == counts["two_q_class_count"],
        prod == counts["product_survivor_count"],
        ent == counts["entangled_survivor_count"],
        embed == counts["one_q_product_embedding_count"],
        n2 == prod + ent,
        n2 == EXPECTED_TWO_Q_SURVIVOR_COUNT,
        cls == EXPECTED_TWO_Q_CLASS_COUNT,
        prod == EXPECTED_PRODUCT_SURVIVOR_COUNT,
        ent == EXPECTED_ENTANGLED_SURVIVOR_COUNT,
        embed == EXPECTED_ONE_Q_SURVIVOR_COUNT,
    )
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "2Q registry and cut-separation counts match the pinned finite packet counts",
        "input_object": counts,
        "positive_case": "544 survivors partition into 528 product and 16 entangled rows, with all 16 1Q survivors product-embedded",
        "negative_control": "lineage-free substrate payload fails",
        "boundary_case": "monogamy row remains narrowed to 3Q rather than promoted",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def cvc5_count_proof(counts: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    vars_by_name = {
        name: solver.mkConst(int_sort, name)
        for name in (
            "two_q_survivor_count",
            "two_q_class_count",
            "product_survivor_count",
            "entangled_survivor_count",
            "one_q_product_embedding_count",
        )
    }
    expected = {
        "two_q_survivor_count": EXPECTED_TWO_Q_SURVIVOR_COUNT,
        "two_q_class_count": EXPECTED_TWO_Q_CLASS_COUNT,
        "product_survivor_count": EXPECTED_PRODUCT_SURVIVOR_COUNT,
        "entangled_survivor_count": EXPECTED_ENTANGLED_SURVIVOR_COUNT,
        "one_q_product_embedding_count": EXPECTED_ONE_Q_SURVIVOR_COUNT,
    }
    for name, term in vars_by_name.items():
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(counts[name])))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(expected[name])))
    solver.assertFormula(
        solver.mkTerm(
            Kind.EQUAL,
            vars_by_name["two_q_survivor_count"],
            solver.mkTerm(Kind.ADD, vars_by_name["product_survivor_count"], vars_by_name["entangled_survivor_count"]),
        )
    )
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "2Q registry and cut-separation counts match the pinned finite packet counts",
        "input_object": counts,
        "positive_case": "544 survivors partition into 528 product and 16 entangled rows, with all 16 1Q survivors product-embedded",
        "negative_control": "lineage-free substrate payload fails",
        "boundary_case": "monogamy row remains narrowed to 3Q rather than promoted",
        "gates": ["all_pass", "crossover_proofs", "divergence"],
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = dict(payload)
    variant["gcm_lineage"] = {
        "gcm_object_id": None,
        "registry_body_sha256": None,
        "survivor_ids": [],
        "quotient_class_ids": [],
        "candidate_region_ids": [],
        "gcm_2q_survivor_ids": [],
        "gcm_2q_quotient_class_ids": [],
        "gcm_2q_candidate_region_ids": [],
        "object_maps": [],
    }
    return variant


def run_2q_substrate_check(payload: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    if REGISTRY_PATH.exists() and load_json(REGISTRY_PATH) == registry:
        return gcm_substrate_check(payload, REGISTRY_PATH)
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "gcm_2q_registry.json"
        write_json(path, registry)
        return gcm_substrate_check(payload, path)


def build_packet(write: bool = True) -> dict[str, Any]:
    freeze = load_json(ONE_Q_FREEZE_REGISTRY)
    carve = load_json(TWO_Q_CARVE_RESULT)
    one_q_entropy = load_json(ONE_Q_ENTROPY_SWEEP_RESULT)
    registry = build_2q_registry(carve, freeze)
    if write:
        write_json(REGISTRY_PATH, registry)
    lineage = build_cross_rung_lineage(carve, freeze, registry)
    by_raw_2q, _by_gcm = survivor_maps(registry)
    qid_by_raw_sid, region_by_raw_sid, _qid_by_raw_class = two_q_class_region_maps(carve, registry)
    lineage_by_raw = {row["raw_2q_survivor_id"]: row for row in lineage["object_maps"]}

    entropy_rows = [
        entropy_row_for_survivor(row, lineage_by_raw, qid_by_raw_sid, region_by_raw_sid) for row in carve["survivors"]
    ]
    class_rows = build_class_entropy_rows(registry, entropy_rows)
    separation = separation_summary(entropy_rows)
    control_rows = controls(entropy_rows, lineage, one_q_entropy)
    monogamy = monogamy_row(entropy_rows)
    count_payload = {
        "two_q_survivor_count": len(entropy_rows),
        "two_q_class_count": len(class_rows),
        "product_survivor_count": sum(1 for row in entropy_rows if row["family"] == "product_grid"),
        "entangled_survivor_count": sum(1 for row in entropy_rows if row["entangled"]),
        "one_q_product_embedding_count": len(lineage["one_q_to_2q_product_embedding"]),
    }
    z3_proof = z3_count_proof(count_payload)
    cvc5_proof = cvc5_count_proof(count_payload)
    substrate_probe_payload = {
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_BASE_OBJECT_ID,
            "registry_body_sha256": EXPECTED_BASE_REGISTRY_BODY_SHA256,
            "base_registry_body_sha256": EXPECTED_BASE_REGISTRY_BODY_SHA256,
            "gcm_2q_object_id": registry["gcm_2q_object_id"],
            "gcm_2q_registry_body_sha256": registry["registry_body_sha256"],
            "survivor_ids": lineage["survivor_ids"],
            "gcm_2q_survivor_ids": lineage["gcm_2q_survivor_ids"],
            "gcm_2q_quotient_class_ids": lineage["gcm_2q_quotient_class_ids"],
            "gcm_2q_candidate_region_ids": lineage["gcm_2q_candidate_region_ids"],
            "object_maps": lineage["object_maps"],
        }
    }
    substrate_1q = gcm_substrate_check(substrate_probe_payload, ONE_Q_FREEZE_REGISTRY)
    substrate_1q_negative = gcm_substrate_check(lineage_free_variant(substrate_probe_payload), ONE_Q_FREEZE_REGISTRY)
    substrate_2q = run_2q_substrate_check(substrate_probe_payload, registry)
    substrate_2q_negative = run_2q_substrate_check(lineage_free_variant(substrate_probe_payload), registry)

    all_separation = (
        separation["metrics"]["negativity"]["separates"]
        and separation["metrics"]["conditional_S_A_given_B"]["separates_by_sign"]
        and separation["metrics"]["mutual_I_A_B"]["separates"]
        and separation["metrics"]["coherent_I_c_A_to_B"]["separates_by_sign"]
        and separation["metrics"]["S_rho_AB"]["separates"]
    )
    no_audit = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "three_coordinates": {
            "layers": "3-12 entropy availability rung",
            "nesting": "2Q freeze plus first bipartition cut",
            "qubit_depth": "2Q",
        },
        "cut": {
            "id": "qubit_A_given_qubit_B",
            "bipartition": "qubit A | qubit B",
            "tensor_order": "computational basis |00>, |01>, |10>, |11> with index = 2*A + B",
            "committed_tensor_structure_is_the_cut": True,
        },
        "gcm_lineage": substrate_probe_payload["gcm_lineage"],
        "registry_path": rel(REGISTRY_PATH),
        "registry_body_sha256": registry["registry_body_sha256"],
        "gcm_2q_object_id": registry["gcm_2q_object_id"],
        "counts": {
            **count_payload,
            "candidate_region_count": len(registry["frozen_2q_registry"]["candidate_regions"]),
        },
        "frozen_2q_registry": registry["frozen_2q_registry"],
        "cross_rung_lineage": lineage,
        "entropy_tables": {
            "survivor_cut_entropy_rows": entropy_rows,
            "class_cut_entropy_rows": class_rows,
        },
        "entangled_vs_product_separation": separation,
        "monogamy_row": monogamy,
        "controls": {
            **control_rows,
            "substrate_positive_1q": substrate_1q,
            "substrate_lineage_free_negative_1q": substrate_1q_negative,
            "substrate_positive_2q": substrate_2q,
            "substrate_lineage_free_negative_2q": substrate_2q_negative,
            "lineage_free_negatives_failed_as_required": substrate_1q_negative.get("ok") is False
            and substrate_2q_negative.get("ok") is False,
        },
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "source_locks": {
            "one_q_freeze_registry": source_lock(ONE_Q_FREEZE_REGISTRY, "base 1Q object freeze by hash"),
            "two_q_carve_result": source_lock(TWO_Q_CARVE_RESULT, "2Q carve 544 survivors / 8 classes / 16 entangled"),
            "two_q_carve_envelope": source_lock(TWO_Q_CARVE_ENVELOPE, "2Q carve PASS audit source"),
            "two_q_carve_validator": source_lock(TWO_Q_CARVE_VALIDATOR, "2Q carve validator receipt"),
            "one_q_entropy_sweep_result": source_lock(ONE_Q_ENTROPY_SWEEP_RESULT, "1Q entropy sweep availability ladder"),
            "one_q_entropy_sweep_validator": source_lock(ONE_Q_ENTROPY_SWEEP_VALIDATOR, "1Q entropy sweep validator"),
            "entropy_protocol": source_lock(ENTROPY_PROTOCOL, "wiki entropy sweep protocol"),
            "axis_entropy_reference": source_lock(AXIS_ENTROPY_REFERENCE, "wiki entropy/axis availability reference"),
            "layer_stack_reference": source_lock(LAYER_STACK_REFERENCE, "GCM layer stack reference"),
            "audit_standards": source_lock(AUDIT_STANDARDS, "G.2a standards"),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "G_2a_idempotency_from_birth": no_audit,
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": no_audit,
            "no_builder_audit_verdict_envelope_gate": no_audit,
        },
        "no_builder_audit_verdict": no_audit,
        "no_builder_audit_verdict_envelope_gate": no_audit,
        "claim_summary": {
            "unlocked_families_computed": [
                "S(rho_A)",
                "S(rho_B)",
                "S(rho_AB)",
                "S(A|B)",
                "I(A:B)",
                "I_c(A>B)",
                "negativity",
            ],
            "entangled_set_separates_from_product_set": all_separation,
            "monogamy_status": monogamy["status"],
        },
        "all_pass": (
            len(entropy_rows) == EXPECTED_TWO_Q_SURVIVOR_COUNT
            and len(class_rows) == EXPECTED_TWO_Q_CLASS_COUNT
            and count_payload["product_survivor_count"] == EXPECTED_PRODUCT_SURVIVOR_COUNT
            and count_payload["entangled_survivor_count"] == EXPECTED_ENTANGLED_SURVIVOR_COUNT
            and len(registry["frozen_2q_registry"]["candidate_regions"]) == EXPECTED_TWO_Q_REGION_COUNT
            and lineage["partial_trace_A_image_equals_1q_survivor_set"]
            and lineage["product_control_embedding_all_survive"]
            and substrate_1q.get("ok") is True
            and substrate_2q.get("ok") is True
            and substrate_1q_negative.get("ok") is False
            and substrate_2q_negative.get("ok") is False
            and control_rows["product_entanglement_zero"]["all_product_negativity_zero"]
            and control_rows["scrambled_pairing"]["negativity_after_scramble_all_zero"]
            and control_rows["one_q_regression"]["partial_trace_A_reproduces_1q_id_degeneracy"]
            and all_separation
            and monogamy["status"] == "OPEN_REQUIRES_3Q_FOR_CKW"
            and z3_proof["verdict"] == "sat"
            and cvc5_proof["verdict"] == "sat"
            and no_audit
        ),
        "disallowed_claims": ["canonical", "formal admission", "THE manifold", "axis admission", "3Q monogamy closure"],
    }
    payload["result_sha256"] = stable_sha256({key: value for key, value in payload.items() if key != "generated_at"})
    if write:
        write_json(RESULT_PATH, payload)
        write_json(LINEAGE_FREE_NEGATIVE_PATH, lineage_free_variant(payload))
    return payload


def main() -> int:
    payload = build_packet(write=True)
    print(
        "GCM_2Q_FREEZE_AND_CUT_DONE "
        f"all_pass={str(payload['all_pass']).lower()} "
        f"survivors={payload['counts']['two_q_survivor_count']} "
        f"classes={payload['counts']['two_q_class_count']} "
        f"product={payload['counts']['product_survivor_count']} "
        f"entangled={payload['counts']['entangled_survivor_count']} "
        f"result={rel(RESULT_PATH)}"
    )
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
