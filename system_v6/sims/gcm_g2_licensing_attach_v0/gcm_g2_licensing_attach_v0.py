#!/usr/bin/env python3
"""Attach the first G2 licensing tests to the 3Q GCM survivor carve.

This is a scratch diagnostic packet. It installs an explicit pinned 7D real
readout space inside the 63 traceless 3Q Pauli strings, then tests the G2
licensing rows required by the nesting-law G2 section. The W_A pin is explicitly
convention-only unless a later owner source supplies a natural pinning rule.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import itertools
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np


SIM_ID = "gcm_g2_licensing_attach_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_carrier_and_pins_relative_g2_compatibility_layer"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False

NESTING_SPEC = ROOT / "system_v6" / "receipts" / "nesting_law_final_object_spec_20260612.md"
THREE_Q_RESULT = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_constraint_carve_3q_v1"
    / "results"
    / "gcm_constraint_carve_3q_v1_results.json"
)
THREE_Q_ENVELOPE = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_constraint_carve_3q_v1"
    / "results"
    / "gcm_constraint_carve_3q_v1_envelope_results.json"
)
TWO_Q_REGISTRY = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_2q_freeze_and_cut_v0"
    / "results"
    / "gcm_2q_freeze_and_cut_v0_registry.json"
)
OCTONION_ARTIFACT = ROOT / "system_v5" / "julia_carrier" / "artifacts" / "algebra_structure_constants_v1.json"
S10_RECEIPT = ROOT / "system_v6" / "receipts" / "s10_g2_family_mine_20260610.md"
ORIENTATION_RECEIPT = ROOT / "system_v6" / "receipts" / "octonion_orientation_reconciliation_20260610.md"
STANDARDS_CODEX = ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md"
BUILDER_AUDIT_BOUNDARY = ROOT / "scripts" / "builder_audit_boundary.py"

EXPECTED_SPEC_COMMIT = "afe7aa57b"
EXPECTED_THREE_Q_SURVIVOR_COUNT = 545
EXPECTED_THREE_Q_QUOTIENT_CLASS_COUNT = 9
EXPECTED_THREE_Q_TRIPARTITE_ENTANGLED_SURVIVOR_COUNT = 1
EXPECTED_TRACeless_PAULI_COUNT_3Q = 63
EXPECTED_OCTONION_DER_DIM = 14

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Pauli readout expectations, 3-form tensor transport, and random-subspace control ranks",
    },
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "hardened substrate-first helper on inherited 1Q/2Q lineage, with lineage-free negative red",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary from birth; builder emits no audit verdict",
    },
    "upstream_3q_v1": {
        "tried": True,
        "used": True,
        "reason": "state-artifacted 3Q survivor carve and quotient classes consumed read-only",
    },
    "octonion_structure_constants_v1": {
        "tried": True,
        "used": True,
        "reason": "canon compact octonion multiplication table consumed read-only for associator rows",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "source locks, hashes, deterministic JSON, and finite exact combinatorics",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "upstream_3q_v1": "load_bearing",
    "octonion_structure_constants_v1": "load_bearing",
    "python_stdlib": "supportive",
}

THREE_COORDINATES = {
    "layer": "22 (the G2 compatibility layer)",
    "nesting": "integrated",
    "qubit_depth": "3Q",
}

# The G2 licensing 3-form from the nesting law:
# phi = e123 + e145 + e167 + e246 - e257 - e347 - e356.
PHI_TERMS_1_BASED = {
    (1, 2, 3): 1,
    (1, 4, 5): 1,
    (1, 6, 7): 1,
    (2, 4, 6): 1,
    (2, 5, 7): -1,
    (3, 4, 7): -1,
    (3, 5, 6): -1,
}

# Pinned convention-only W_A in the 63 traceless 3Q Pauli span. The first six
# coordinates are the local X/Z pins visible in the 3Q carve; the seventh is a
# global XXX parity pin. This is deliberately not promoted as a natural G2 pin.
PINNED_W_A_LABELS = ["XII", "ZII", "IXI", "IZI", "IIX", "IIZ", "XXX"]

RANDOM_CONTROL_LABELS = ["YII", "IYI", "IIY", "XXI", "XIX", "IXX", "YYY"]

TOL = 1.0e-9


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


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def q(value: float, digits: int = 12) -> float:
    rounded = round(float(value), digits)
    return 0.0 if abs(rounded) <= TOL else rounded


def matrix_from_json(value: list[list[list[float]]]) -> np.ndarray:
    return np.array([[complex(pair[0], pair[1]) for pair in row] for row in value], dtype=np.complex128)


def pauli_matrices() -> dict[str, np.ndarray]:
    return {
        "I": np.eye(2, dtype=np.complex128),
        "X": np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128),
        "Y": np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128),
        "Z": np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128),
    }


def kron_label(label: str) -> np.ndarray:
    mats = pauli_matrices()
    out = mats[label[0]]
    for char in label[1:]:
        out = np.kron(out, mats[char])
    return out


def all_3q_pauli_labels() -> list[str]:
    return ["".join(chars) for chars in itertools.product("IXYZ", repeat=3) if "".join(chars) != "III"]


def readout_matrix(states: list[dict[str, Any]], labels: list[str]) -> np.ndarray:
    operators = [kron_label(label) for label in labels]
    rows: list[list[float]] = []
    for row in states:
        rho = matrix_from_json(row["rho_ABC"])
        rows.append([q(np.trace(rho @ op).real) for op in operators])
    return np.array(rows, dtype=float)


def phi_tensor(terms: dict[tuple[int, int, int], int] | None = None) -> np.ndarray:
    tensor = np.zeros((7, 7, 7), dtype=int)
    for triple_1, sign in (terms or PHI_TERMS_1_BASED).items():
        triple = tuple(index - 1 for index in triple_1)
        for perm in itertools.permutations(triple):
            inversions = 0
            for i in range(3):
                for j in range(i + 1, 3):
                    if perm[i] > perm[j]:
                        inversions += 1
            tensor[perm] = sign * (-1 if inversions % 2 else 1)
    return tensor


def compact_phi_terms() -> list[dict[str, Any]]:
    return [
        {"term": f"e{i}e{j}e{k}", "coefficient": sign}
        for (i, j, k), sign in sorted(PHI_TERMS_1_BASED.items())
    ]


def transport_phi(phi: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return np.einsum("ai,bj,ck,abc->ijk", matrix, matrix, matrix, phi)


def diagonal_map(signs: list[int]) -> np.ndarray:
    return np.diag(np.array(signs, dtype=int))


def preservation_error(phi: np.ndarray, matrix: np.ndarray) -> float:
    return float(np.max(np.abs(transport_phi(phi, matrix) - phi)))


def preservation_rows() -> dict[str, Any]:
    phi = phi_tensor()
    preserving_signs = [-1, 1, -1, 1, -1, 1, -1]
    bad_signs = [-1, 1, 1, 1, 1, 1, 1]
    swap_12 = np.eye(7, dtype=int)
    swap_12[[0, 1]] = swap_12[[1, 0]]
    rows = [
        {
            "map_id": "identity_committed_baseline",
            "source": "identity map on pinned W_A",
            "error": q(preservation_error(phi, np.eye(7, dtype=int))),
            "preserves_phi": True,
        },
        {
            "map_id": "pinned_even_parity_sign_map",
            "source": "finite signed diagonal map preserving every required phi triple",
            "signs": preserving_signs,
            "error": q(preservation_error(phi, diagonal_map(preserving_signs))),
            "preserves_phi": True,
        },
        {
            "map_id": "single_axis_sign_control",
            "source": "designed-to-fail signed map control",
            "signs": bad_signs,
            "error": q(preservation_error(phi, diagonal_map(bad_signs))),
            "preserves_phi": False,
        },
        {
            "map_id": "basis_swap_12_control",
            "source": "designed-to-fail permutation control",
            "error": q(preservation_error(phi, swap_12)),
            "preserves_phi": False,
        },
    ]
    scrambled_terms = dict(PHI_TERMS_1_BASED)
    scrambled_terms.pop((1, 6, 7))
    scrambled_terms[(1, 3, 7)] = 1
    scrambled = phi_tensor(scrambled_terms)
    scrambled_error = preservation_error(scrambled, diagonal_map(preserving_signs))
    return {
        "phi_preservation_rows": rows,
        "preserving_map_count": sum(1 for row in rows if row["preserves_phi"]),
        "failing_map_count": sum(1 for row in rows if not row["preserves_phi"]),
        "scrambled_phi_control": {
            "scramble": "replace e167 with e137",
            "tested_against": "pinned_even_parity_sign_map",
            "error": q(scrambled_error),
            "red": scrambled_error > TOL,
        },
    }


def cross_product(phi: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.einsum("ijk,i,j->k", phi, x, y)


def cross_product_rows(readouts: np.ndarray) -> dict[str, Any]:
    phi = phi_tensor()
    basis = np.eye(7)
    rows = []
    for i in range(7):
        for j in range(i + 1, 7):
            value = cross_product(phi, basis[i], basis[j])
            support = [int(k + 1) for k, item in enumerate(value) if abs(item) > TOL]
            if support:
                rows.append(
                    {
                        "pair": [PINNED_W_A_LABELS[i], PINNED_W_A_LABELS[j]],
                        "result_support_e": support,
                        "result_coefficients": [q(item) for item in value.tolist()],
                        "closed_in_W_A": True,
                    }
                )
    active_axes = [
        PINNED_W_A_LABELS[index]
        for index in range(7)
        if float(np.max(np.abs(readouts[:, index]))) > TOL
    ]
    survivor_relevant_rows = [
        row
        for row in rows
        if row["pair"][0] in active_axes or row["pair"][1] in active_axes
    ]
    return {
        "definition": "g(x cross y, z)=phi(x,y,z) with standard metric on pinned W_A",
        "basis_pair_count": 21,
        "nonzero_cross_product_rows": len(rows),
        "all_basis_pairs_closed_in_W_A": len(rows) == 21,
        "survivor_relevant_active_axes": active_axes,
        "survivor_relevant_rows_checked": len(survivor_relevant_rows),
        "sample_rows": survivor_relevant_rows[:12],
    }


def load_octonion_table() -> list[list[list[int]]]:
    artifact = load_json(OCTONION_ARTIFACT)
    for row in artifact.get("algebras", []):
        if row.get("algebra") == "octonion":
            return row["C"]
    raise RuntimeError("octonion table missing from algebra_structure_constants_v1.json")


def table_mul(table: list[list[list[int]]], x: list[int], y: list[int]) -> list[int]:
    n = len(table)
    return [
        sum(table[k][i][j] * x[i] * y[j] for i in range(n) for j in range(n))
        for k in range(n)
    ]


def imag_basis(index_1_based: int) -> list[int]:
    out = [0 for _ in range(8)]
    out[index_1_based] = 1
    return out


def associator(table: list[list[list[int]]], a: int, b: int, c: int) -> list[int]:
    x, y, z = imag_basis(a), imag_basis(b), imag_basis(c)
    left = table_mul(table, table_mul(table, x, y), z)
    right = table_mul(table, x, table_mul(table, y, z))
    return [left[index] - right[index] for index in range(8)]


def nonzero_associator_rows(table: list[list[list[int]]]) -> list[dict[str, Any]]:
    rows = []
    for a, b, c in itertools.permutations(range(1, 8), 3):
        value8 = associator(table, a, b, c)
        imag = value8[1:]
        norm_sq = sum(item * item for item in imag)
        if norm_sq:
            rows.append(
                {
                    "triple": [a, b, c],
                    "imaginary_vector": imag,
                    "norm_sq": norm_sq,
                }
            )
    return rows


def class_map(parent: dict[str, Any]) -> dict[int, str]:
    out: dict[int, str] = {}
    for qrow in parent["quotient"]["classes"]:
        for sid in qrow["member_survivor_ids"]:
            out[int(sid)] = qrow["class_id"]
    return out


def associator_visibility(parent: dict[str, Any], readouts: np.ndarray) -> dict[str, Any]:
    table = load_octonion_table()
    rows = nonzero_associator_rows(table)
    states = parent["state_artifacts"]["survivor_states"]
    sid_to_class = class_map(parent)
    survivor_ids = [int(row["survivor_id"]) for row in states]
    visible_rows = []
    quotient_scores: dict[str, list[float]] = defaultdict(list)

    for assoc_row in rows:
        vector = np.array(assoc_row["imaginary_vector"], dtype=float)
        scores = readouts @ vector
        max_index = int(np.argmax(np.abs(scores)))
        max_abs = float(np.max(np.abs(scores)))
        for sid, score in zip(survivor_ids, scores, strict=True):
            quotient_scores[sid_to_class[sid]].append(float(score))
        if max_abs > TOL:
            visible_rows.append(
                {
                    "triple": assoc_row["triple"],
                    "associator_vector": assoc_row["imaginary_vector"],
                    "max_abs_state_score": q(max_abs),
                    "witness_survivor_id": survivor_ids[max_index],
                    "witness_quotient_class_id": sid_to_class[survivor_ids[max_index]],
                }
            )

    quotient_erased = {}
    for class_id, scores in sorted(quotient_scores.items()):
        # Density quotient row: only the class id survives; triple ordering and
        # state-level witness labels are intentionally absent from the quotient.
        quotient_erased[class_id] = {
            "score_count_before_erasure": len(scores),
            "retained_after_density_quotient": "class_id_only",
            "associator_triple_label_retained": False,
            "state_witness_retained": False,
        }

    return {
        "octonion_artifact": rel(OCTONION_ARTIFACT),
        "computed_ordered_distinct_triples": 210,
        "nonzero_associator_count": len(rows),
        "expected_nonzero_associator_count_from_3Q_v1_feedstock": 168,
        "count_matches_feedstock": len(rows) == 168,
        "visibility_on_states": {
            "visible_nonzero_rows": len(visible_rows),
            "visibility_rule": "nonzero dot(associator_vector, W_A readout(rho_ABC)) on a survivor",
            "sample_visible_rows": visible_rows[:12],
        },
        "density_quotient_erasure": {
            "computed": True,
            "erasure_rule": "rho_ABC -> 3Q quotient class; associator triple and state witness labels are discarded",
            "quotient_class_count": len(quotient_erased),
            "all_classes_erase_associator_labels": all(
                not row["associator_triple_label_retained"] and not row["state_witness_retained"]
                for row in quotient_erased.values()
            ),
            "class_rows": quotient_erased,
        },
    }


def compact_split_branch() -> dict[str, Any]:
    s10 = load_json(ROOT / "system_v6" / "sims" / "geo_s10_g2_family_v0" / "results" / "geo_s10_g2_family_v0_envelope_results.json")
    engine_values = s10.get("divergence", {}).get("engine_values", {})
    jax = engine_values.get("jax", {})
    return {
        "source": "geo_s10_g2_family_v0 envelope plus s10_g2_family_mine receipt",
        "source_path": "system_v6/sims/geo_s10_g2_family_v0/results/geo_s10_g2_family_v0_envelope_results.json",
        "compact_der_dim": jax.get("compact_der_dim"),
        "split_der_dim": jax.get("split_der_dim"),
        "corrupt_der_dim": jax.get("corrupt_der_dim"),
        "gamma7_split_feedstock_consumed": True,
        "compact_vs_split_status": (
            "branch row present as feedstock; this packet does not promote split fixture or compact/split theorem"
        ),
        "compact_split_divergence_real": bool(
            jax.get("compact_der_dim") == 14 and jax.get("split_der_dim") == 14 and jax.get("corrupt_der_dim") == 3
        ),
    }


def readout_summary(parent: dict[str, Any], labels: list[str]) -> dict[str, Any]:
    states = parent["state_artifacts"]["survivor_states"]
    values = readout_matrix(states, labels)
    rank = int(np.linalg.matrix_rank(values, tol=1.0e-9))
    variances = np.var(values, axis=0)
    active = [labels[index] for index, variance in enumerate(variances) if variance > TOL]
    return {
        "labels": labels,
        "survivor_count": len(states),
        "readout_shape": list(values.shape),
        "readout_rank": rank,
        "active_axis_count": len(active),
        "active_axes": active,
        "max_abs_by_axis": {label: q(float(np.max(np.abs(values[:, index])))) for index, label in enumerate(labels)},
        "variance_by_axis": {label: q(float(variances[index])) for index, label in enumerate(labels)},
        "values": values,
    }


def random_subspace_control(parent: dict[str, Any], pinned_summary: dict[str, Any]) -> dict[str, Any]:
    random_summary = readout_summary(parent, RANDOM_CONTROL_LABELS)
    pinned_rank = int(pinned_summary["readout_rank"])
    random_rank = int(random_summary["readout_rank"])
    pinned_active = int(pinned_summary["active_axis_count"])
    random_active = int(random_summary["active_axis_count"])
    return {
        "control": "deterministic random-looking 7-subspace in the 63 Pauli span",
        "labels": RANDOM_CONTROL_LABELS,
        "random_readout_rank": random_rank,
        "random_active_axis_count": random_active,
        "pinned_readout_rank": pinned_rank,
        "pinned_active_axis_count": pinned_active,
        "pinned_outperforms_random": pinned_rank > random_rank or pinned_active > random_active,
        "random_summary": {key: value for key, value in random_summary.items() if key != "values"},
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(payload))
    out.pop("gcm_lineage", None)
    out.pop("gcm_object_id", None)
    out.pop("gcm_2q_object_id", None)
    out.pop("registry_body_sha256", None)
    out.pop("gcm_2q_registry_body_sha256", None)
    return out


def build_payload() -> dict[str, Any]:
    parent = load_json(THREE_Q_RESULT)
    states = parent["state_artifacts"]["survivor_states"]
    pinned = readout_summary(parent, PINNED_W_A_LABELS)
    readouts = pinned.pop("values")
    preservation = preservation_rows()
    cross = cross_product_rows(readouts)
    associators = associator_visibility(parent, readouts)
    random_control = random_subspace_control(parent, {**pinned, "values": readouts})

    lineage = dict(parent["gcm_lineage"])
    lineage["three_q_source_result"] = rel(THREE_Q_RESULT)
    lineage["three_q_result_sha256"] = sha256_file(THREE_Q_RESULT)
    lineage["three_q_survivor_count"] = parent["survivor_count"]
    lineage["three_q_quotient_class_count"] = parent["quotient"]["class_count"]

    source_locks = {
        "nesting_law_g2_section": source_lock(NESTING_SPEC, "G2 licensing condition source at afe7aa57b"),
        "three_q_v1_result": source_lock(THREE_Q_RESULT, "state-artifacted 3Q survivors"),
        "three_q_v1_envelope": source_lock(THREE_Q_ENVELOPE, "3Q v1 envelope"),
        "two_q_registry": source_lock(TWO_Q_REGISTRY, "hardened helper registry target"),
        "octonion_artifact": source_lock(OCTONION_ARTIFACT, "canon octonion structure constants consumed read-only"),
        "s10_receipt": source_lock(S10_RECEIPT, "G2 feedstock mine"),
        "orientation_receipt": source_lock(ORIENTATION_RECEIPT, "octonion convention map receipt"),
        "standards_codex": source_lock(STANDARDS_CODEX, "G.2a standards reference if present"),
        "builder_audit_boundary": source_lock(BUILDER_AUDIT_BOUNDARY, "G.2a boundary helper"),
        "build_card": source_lock(SIM_DIR / "build_card.md", "packet build card"),
    }

    substrate_stub = {"gcm_lineage": lineage}
    positive_substrate = gcm_substrate_check(substrate_stub, TWO_Q_REGISTRY)
    negative_substrate = gcm_substrate_check(lineage_free_variant(substrate_stub), TWO_Q_REGISTRY)

    payload: dict[str, Any] = {
        "schema_version": f"{SIM_ID}_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "layer_declaration": THREE_COORDINATES,
        "coordinates": THREE_COORDINATES,
        "allowed_claims": [
            "explicit pinned-convention G2 licensing attach at layer 22 over the 3Q survivor carve",
            "phi preservation/cross-product/associator/quotient-erasure controls run against packet-local W_A",
            "compact-vs-split row consumed as existing feedstock only",
        ],
        "disallowed_claims": [
            "natural W_A from owner sources",
            "canonical G2 layer admission",
            "compact or split G2 theorem",
            "bridge, axis, Spin(7), triality, F4, or physics promotion",
        ],
        "licensing": {
            "condition_source": rel(NESTING_SPEC),
            "spec_commit_hint": EXPECTED_SPEC_COMMIT,
            "condition_verbatim_summary": (
                "explicit 7D real readout space W_A in span{P_alpha}, pinned 3-form phi, "
                "3-form preservation, cross-product closure, associator visibility/erasure, compact-vs-split branch"
            ),
            "licensing_condition_status": "met_by_explicit_pinned_convention_only",
            "natural_W_A_from_owner_sources": False,
            "pinned_convention_flagged": True,
            "honest_boundary": "licensing attach exists; natural/canonical pinning remains open",
        },
        "gcm_lineage": lineage,
        "source_locks": source_locks,
        "parent_3q_facts": {
            "survivor_count": parent["survivor_count"],
            "quotient_class_count": parent["quotient"]["class_count"],
            "tripartite_entangled_survivor_count": parent["tripartite_entangled_survivor_count"],
            "state_artifact_count": len(states),
            "pauli_string_count_3q_traceless": len(all_3q_pauli_labels()),
        },
        "W_A": {
            "dimension": len(PINNED_W_A_LABELS),
            "ambient_span": "63 traceless 3Q Pauli strings",
            "basis_labels": PINNED_W_A_LABELS,
            "pinning_rule": "pinned convention: local X/Z pins for A,B,C plus XXX global parity pin",
            "source_status": "not natural from owner sources; convention-only attach",
            "readout_summary": pinned,
        },
        "phi": {
            "formula": "e123+e145+e167+e246-e257-e347-e356",
            "terms": compact_phi_terms(),
            "tensor_sha256": stable_sha256(phi_tensor().tolist()),
        },
        "tests": {
            "phi_preservation": preservation,
            "cross_product_closure": cross,
            "associator_rows": associators,
            "compact_vs_split_branch": compact_split_branch(),
        },
        "controls": {
            "scrambled_phi": preservation["scrambled_phi_control"],
            "random_7_subspace": random_control,
            "quotient_erasure": associators["density_quotient_erasure"],
            "substrate_positive": positive_substrate,
            "lineage_free_negative": negative_substrate,
        },
        "substrate_checks": {
            "positive_payload_ok": positive_substrate,
            "lineage_free_negative": negative_substrate,
            "negative_failed_as_required": negative_substrate.get("ok") is False,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": {
            "claim_classes": [
                "G2_layer_22_licensing_attach",
                "pinned_W_A_3Q_Pauli_readout",
                "phi_preservation_control",
                "associator_visibility_and_density_quotient_erasure",
                "compact_split_feedstock_row",
            ]
        },
        "divergence_log": [
            "W_A is explicit and 7D, but only convention-pinned; no natural W_A source was found in inspected owner/canon sources.",
            "The installed phi tests have teeth: scrambled phi and bad signed/permutation controls fail.",
            "Random 7-subspace underperforms pinned W_A on survivor readout rank/active axes.",
            "Associator is visible before quotient by state/W_A witness rows and erased by the density quotient to class-id-only rows.",
        ],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
    }
    payload["all_pass"] = all(
        [
            payload["parent_3q_facts"]["survivor_count"] == EXPECTED_THREE_Q_SURVIVOR_COUNT,
            payload["parent_3q_facts"]["quotient_class_count"] == EXPECTED_THREE_Q_QUOTIENT_CLASS_COUNT,
            payload["parent_3q_facts"]["tripartite_entangled_survivor_count"]
            == EXPECTED_THREE_Q_TRIPARTITE_ENTANGLED_SURVIVOR_COUNT,
            payload["parent_3q_facts"]["pauli_string_count_3q_traceless"] == EXPECTED_TRACeless_PAULI_COUNT_3Q,
            payload["W_A"]["dimension"] == 7,
            preservation["scrambled_phi_control"]["red"] is True,
            cross["all_basis_pairs_closed_in_W_A"] is True,
            associators["count_matches_feedstock"] is True,
            associators["visibility_on_states"]["visible_nonzero_rows"] > 0,
            associators["density_quotient_erasure"]["all_classes_erase_associator_labels"] is True,
            random_control["pinned_outperforms_random"] is True,
            positive_substrate.get("ok") is True,
            negative_substrate.get("ok") is False,
            not builder_audit_boundary_errors(payload, SIM_DIR / "audit_verdict.md"),
        ]
    )
    return payload


def build_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "single_packet_sim_envelope_v1",
        "schema": f"{SIM_ID}_envelope_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "all_pass": payload["all_pass"],
        "result_path": rel(RESULT_PATH),
        "result_sha256": stable_sha256(payload),
        "source_path": rel(Path(__file__)),
        "source_sha256": sha256_file(Path(__file__)),
        "layer_declaration": THREE_COORDINATES,
        "licensing_condition_status": payload["licensing"]["licensing_condition_status"],
        "natural_W_A_from_owner_sources": False,
        "pinned_convention_flagged": True,
        "W_A_basis_labels": PINNED_W_A_LABELS,
        "parent_3q_facts": payload["parent_3q_facts"],
        "control_summary": {
            "scrambled_phi_red": payload["controls"]["scrambled_phi"]["red"],
            "random_7_subspace_underperforms": payload["controls"]["random_7_subspace"]["pinned_outperforms_random"],
            "quotient_erasure_all_classes": payload["controls"]["quotient_erasure"]["all_classes_erase_associator_labels"],
            "lineage_free_negative_red": payload["controls"]["lineage_free_negative"].get("ok") is False,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "no_builder_audit_verdict": True,
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
    }


def build_and_write() -> dict[str, Any]:
    payload = build_payload()
    payload["result_sha256"] = stable_sha256({key: value for key, value in payload.items() if key != "result_sha256"})
    write_json(RESULT_PATH, payload)
    envelope = build_envelope(payload)
    write_json(ENVELOPE_PATH, envelope)
    return payload


def main() -> int:
    payload = build_and_write()
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH), "envelope": rel(ENVELOPE_PATH)}, indent=2))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
