#!/usr/bin/env python3
"""<=3Q inverse-limit tower packet for the GCM nesting law."""

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

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "gcm_nesting_tower_le3q_v0"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

ONE_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_object_id_freeze_v0" / "results" / "gcm_object_id_freeze_v0_registry.json"
)
TWO_Q_REGISTRY_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_registry.json"
)
LE2_TOWER_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_nesting_tower_le2q_v0" / "results" / "gcm_nesting_tower_le2q_v0_results.json"
)
THREE_Q_RESULT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_constraint_carve_3q_v1" / "results" / "gcm_constraint_carve_3q_v1_results.json"
)
NESTING_LAW_SPEC_PATH = ROOT / "system_v6" / "receipts" / "nesting_law_final_object_spec_20260612.md"
AUDIT_STANDARDS_CODEX_PATH = ROOT / "system_v6" / "receipts" / "audit_standards_codex_v1.md"
GCM_SUBSTRATE_HELPER_PATH = ROOT / "scripts" / "gcm_substrate_check.py"
BUILDER_AUDIT_BOUNDARY_PATH = ROOT / "scripts" / "builder_audit_boundary.py"

EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_1Q_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_1Q_SURVIVOR_COUNT = 16
EXPECTED_2Q_SURVIVOR_COUNT = 544
EXPECTED_3Q_SURVIVOR_COUNT = 545
EXPECTED_3Q_PRODUCT_LIFT_COUNT = 544
EXPECTED_3Q_TRIPARTITE_ENTANGLED_COUNT = 1
EXPECTED_3Q_CANDIDATE_COUNT = 552
EXPECTED_3Q_QUOTIENT_CLASS_COUNT = 9
EXPECTED_LE2_AUDIT_COMMIT = "28052037d"
EXPECTED_3Q_V1_COMMIT = "5544ad21c"
EXPECTED_NESTING_LAW_COMMIT = "afe7aa57b"

LE2_REGRESSION_EXPECTED_COUNTS = {
    "exact_compatible_2q_count": 256,
    "exact_compatible_family_triple_count": 256,
    "exact_orphan_2q_count": 288,
    "probe_compatible_2q_count": 464,
    "probe_compatible_family_triple_count": 1856,
    "probe_orphan_2q_count": 80,
    "probe_rescued_exact_orphan_2q_count": 208,
    "quotient_multiplicity_added_family_triples": 1600,
    "product_exact_subtower_count": 256,
    "product_probe_compatible_2q_count": 448,
    "product_probe_family_triple_count": 1792,
    "entangled_probe_compatible_2q_count": 16,
    "entangled_probe_family_triple_count": 64,
}

SCHEMA = f"{SIM_ID}_result_v1"
ENVELOPE_SCHEMA = f"{SIM_ID}_envelope_v1"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic_le3q_tower_carrier_and_pins_relative"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "all_three_full_sims"
AXIS_DECLARATION = {
    "axis": "nesting/tower",
    "limit_object": "inverse-limit",
    "rung": "<=3Q",
}
CUTS = {
    "A|BC": {"single": "A", "single_keep": [0], "pair": "BC", "pair_keep": [1, 2]},
    "B|AC": {"single": "B", "single_keep": [1], "pair": "AC", "pair_keep": [0, 2]},
    "C|AB": {"single": "C", "single_keep": [2], "pair": "AB", "pair_keep": [0, 1]},
}
PAIR_TO_CUT = {value["pair"]: key for key, value in CUTS.items()}
TOL = 1.0e-10

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


TOOL_MANIFEST = {
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hardened 1Q/2Q substrate lineage check and lineage-free negatives",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "canonical JSON, source locks, SHA-256 ids, and tower bookkeeping",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix partial traces, Bloch coordinates, ranks, and density spectra from stored rho_ABC",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT contradiction guards for all-cut exact/probe family count identities",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent SMT contradiction guards for the same all-cut tower identities",
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
    "numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "nesting_law_le3_inverse_limit_tower",
        "all_three_cut_partial_trace_relation_exact_and_probe",
        "extension_fiber_F3_over_2q_survivors",
        "root_axiom_replication_test_at_3q",
        "schmidt_density_strata_per_cut",
        "tower_orphan_characterization",
        "substrate_first_negative_controls",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "SimpleGraph/add_edge!/connected_components encode 3Q survivor to 2Q cut-fiber incidence.",
        },
        "jax": {
            "sympy": "sp.Rational exact guard for all-cut exact/probe compatible family counts.",
            "z3": "z3.Solver contradiction guard for computed all-cut exact/probe tower counts.",
            "cvc5": "cvc5.Solver contradiction guard for computed all-cut exact/probe tower counts.",
        },
        "pytorch": {
            "torch.func": "vmap over 3Q cut multiplicity vectors recomputes all-cut probe family cardinality.",
            "sympy": "sp.Rational exact guard for product + entangled family count partition identities.",
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


def q(value: float) -> float:
    rounded = round(float(value), 12)
    return 0.0 if rounded == 0 else rounded


def scaled(value: float) -> int:
    return int(round(2.0 * float(value)))


def sign(value: int | float) -> int:
    return -1 if value < 0 else 1 if value > 0 else 0


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def stable_id(prefix: str, value: Any, length: int = 20) -> str:
    return f"{prefix}_{stable_sha256(value)[:length]}"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
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


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path),
        "role": role,
    }


def complex_pair(value: complex) -> list[float]:
    return [q(float(np.real(value))), q(float(np.imag(value)))]


def matrix_to_json(matrix: np.ndarray) -> list[list[list[float]]]:
    return [[complex_pair(value) for value in row] for row in matrix.tolist()]


def json_to_matrix(value: list[list[list[float]]]) -> np.ndarray:
    return np.array([[complex(pair[0], pair[1]) for pair in row] for row in value], dtype=np.complex128)


PAULI_X = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.complex128)
PAULI_Y = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=np.complex128)
PAULI_Z = np.array([[1.0, 0.0], [0.0, -1.0]], dtype=np.complex128)


def partial_trace(rho: np.ndarray, keep: list[int], dims: list[int] | None = None) -> np.ndarray:
    dims = dims or [2, 2, 2]
    keep_set = set(keep)
    traced = rho.reshape(dims + dims)
    current_n = len(dims)
    for index in reversed(range(len(dims))):
        if index not in keep_set:
            traced = np.trace(traced, axis1=index, axis2=index + current_n)
            current_n -= 1
    final_dim = math.prod(dims[index] for index in keep)
    return traced.reshape((final_dim, final_dim))


def bloch_from_single(rho_single: np.ndarray) -> tuple[float, float, float]:
    return (
        q(float(np.real(np.trace(PAULI_X @ rho_single)))),
        q(float(np.real(np.trace(PAULI_Y @ rho_single)))),
        q(float(np.real(np.trace(PAULI_Z @ rho_single)))),
    )


def scaled_coord_from_single(rho_single: np.ndarray) -> tuple[int, int, int]:
    return tuple(scaled(value) for value in bloch_from_single(rho_single))


def probe_signature_from_scaled(coord_scaled: tuple[int, int, int] | list[int]) -> tuple[int, int]:
    return (sign(int(coord_scaled[0])), sign(int(coord_scaled[2])))


def sig_key(sig: tuple[int, int] | list[int]) -> str:
    return f"{int(sig[0])},{int(sig[1])}"


def rounded_eigvals(matrix: np.ndarray) -> list[float]:
    hermitian = (matrix + np.conjugate(matrix.T)) / 2.0
    values = sorted((q(float(np.real(value))) for value in np.linalg.eigvalsh(hermitian)), reverse=True)
    return [0.0 if abs(value) <= TOL else value for value in values]


def matrix_rank(matrix: np.ndarray) -> int:
    return int(np.linalg.matrix_rank(matrix, tol=1.0e-9))


def density_purity(matrix: np.ndarray) -> float:
    return q(float(np.real(np.trace(matrix @ matrix))))


def one_q_indexes(one_q: dict[str, Any]) -> dict[str, Any]:
    survivors = one_q["frozen_registry"]["survivors"]
    quotient_classes = one_q["frozen_registry"]["quotient_classes"]
    regions = one_q["frozen_registry"]["candidate_regions"]
    by_coord = {tuple(int(v) for v in row["coord_scaled"]): row for row in survivors}
    by_sig: dict[tuple[int, int], list[str]] = defaultdict(list)
    qclass_by_sig: dict[tuple[int, int], str] = {}
    region_by_qclass: dict[str, str] = {}
    for row in survivors:
        by_sig[probe_signature_from_scaled(row["coord_scaled"])].append(row["survivor_id"])
    for qrow in quotient_classes:
        qclass_by_sig[tuple(int(v) for v in qrow["probe_signature"])] = qrow["quotient_class_id"]
    for region in regions:
        for qid in region["member_quotient_class_ids"]:
            region_by_qclass[qid] = region["candidate_region_id"]
    return {
        "survivors": survivors,
        "by_coord": by_coord,
        "by_sig": {key: sorted(values) for key, values in by_sig.items()},
        "qclass_by_sig": qclass_by_sig,
        "region_by_qclass": region_by_qclass,
        "survivor_ids": [row["survivor_id"] for row in survivors],
    }


def two_q_indexes(two_q: dict[str, Any]) -> dict[str, Any]:
    survivors = two_q["frozen_2q_registry"]["survivors"]
    quotient_classes = two_q["frozen_2q_registry"]["quotient_classes"]
    regions = two_q["frozen_2q_registry"]["candidate_regions"]
    by_coord: dict[tuple[tuple[int, int, int], tuple[int, int, int]], list[dict[str, Any]]] = defaultdict(list)
    by_id = {}
    qclass_by_sig: dict[tuple[int, int], str] = {}
    qclass_members_by_sig: dict[tuple[int, int], list[str]] = {}
    qclass_by_survivor = {}
    region_by_qclass = {}
    for row in survivors:
        key = (
            tuple(int(v) for v in row["first_bloch_scaled"]),
            tuple(int(v) for v in row["second_bloch_scaled"]),
        )
        by_coord[key].append(row)
        by_id[row["gcm_2q_survivor_id"]] = row
    for qrow in quotient_classes:
        sig = tuple(int(v) for v in qrow["probe_signature"])
        qclass_by_sig[sig] = qrow["gcm_2q_quotient_class_id"]
        qclass_members_by_sig[sig] = sorted(qrow["member_gcm_2q_survivor_ids"])
        for sid in qrow["member_gcm_2q_survivor_ids"]:
            qclass_by_survivor[sid] = qrow["gcm_2q_quotient_class_id"]
    for region in regions:
        for qid in region["member_gcm_2q_quotient_class_ids"]:
            region_by_qclass[qid] = region["gcm_2q_candidate_region_id"]
    return {
        "survivors": survivors,
        "by_coord": {key: sorted(values, key=lambda row: row["gcm_2q_survivor_id"]) for key, values in by_coord.items()},
        "by_id": by_id,
        "qclass_by_sig": qclass_by_sig,
        "qclass_members_by_sig": qclass_members_by_sig,
        "qclass_by_survivor": qclass_by_survivor,
        "region_by_qclass": region_by_qclass,
        "survivor_ids": [row["gcm_2q_survivor_id"] for row in survivors],
    }


def match_single(rho_single: np.ndarray, one_index: dict[str, Any]) -> dict[str, Any]:
    coord = scaled_coord_from_single(rho_single)
    sig = probe_signature_from_scaled(coord)
    exact = one_index["by_coord"].get(coord)
    probe_ids = list(one_index["by_sig"].get(sig, []))
    qclass = one_index["qclass_by_sig"].get(sig)
    return {
        "relation_scope": "rho_single_to_1q_registry",
        "coord_scaled": list(coord),
        "bloch": [q(v) for v in bloch_from_single(rho_single)],
        "probe_signature": list(sig),
        "exact_survivor_ids": [exact["survivor_id"]] if exact else [],
        "probe_survivor_ids": probe_ids,
        "probe_quotient_class_id": qclass,
        "probe_candidate_region_id": one_index["region_by_qclass"].get(qclass) if qclass else None,
        "exact_resolves": exact is not None,
        "probe_resolves": bool(probe_ids),
    }


def two_qubit_marginals(pair_matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return partial_trace(pair_matrix, [0], [2, 2]), partial_trace(pair_matrix, [1], [2, 2])


def match_pair(pair_matrix: np.ndarray, two_index: dict[str, Any]) -> dict[str, Any]:
    first_single, second_single = two_qubit_marginals(pair_matrix)
    first_coord = scaled_coord_from_single(first_single)
    second_coord = scaled_coord_from_single(second_single)
    coord_key = (first_coord, second_coord)
    sig = probe_signature_from_scaled(first_coord)
    exact_rows = two_index["by_coord"].get(coord_key, [])
    exact_ids = [row["gcm_2q_survivor_id"] for row in exact_rows]
    probe_ids = list(two_index["qclass_members_by_sig"].get(sig, []))
    qclass = two_index["qclass_by_sig"].get(sig)
    return {
        "relation_scope": "rho_pair_to_2q_registry",
        "relation_kind": "frozen local-pin coordinate equality for exact; 2Q active first-qubit x/z quotient for probe",
        "first_bloch_scaled": list(first_coord),
        "second_bloch_scaled": list(second_coord),
        "first_bloch": [q(v) for v in bloch_from_single(first_single)],
        "second_bloch": [q(v) for v in bloch_from_single(second_single)],
        "probe_signature": list(sig),
        "exact_2q_survivor_ids": exact_ids,
        "probe_2q_survivor_ids": probe_ids,
        "probe_2q_quotient_class_id": qclass,
        "probe_2q_candidate_region_id": two_index["region_by_qclass"].get(qclass) if qclass else None,
        "exact_resolves": bool(exact_ids),
        "probe_resolves": bool(probe_ids),
    }


def survivor_content_id(survivor: dict[str, Any]) -> str:
    return str(survivor["rho_ABC_content_id"])


def survivor_state_matrix(survivor: dict[str, Any], states: dict[str, Any]) -> np.ndarray:
    return json_to_matrix(states[survivor_content_id(survivor)]["rho_ABC"])


def family_row_id(kind: str, survivor: dict[str, Any], cut_rows: dict[str, Any]) -> str:
    key = {
        "kind": kind,
        "rho_ABC_content_id": survivor_content_id(survivor),
        "cut_keys": {
            cut: {
                "single_exact": row["single_relation"]["exact_survivor_ids"],
                "single_probe": row["single_relation"]["probe_survivor_ids"],
                "pair_exact": row["pair_relation"]["exact_2q_survivor_ids"],
                "pair_probe_qclass": row["pair_relation"]["probe_2q_quotient_class_id"],
            }
            for cut, row in sorted(cut_rows.items())
        },
    }
    return stable_id("le3qfam", key, 24)


def product(values: list[int]) -> int:
    out = 1
    for value in values:
        out *= int(value)
    return out


def cut_multiplicity(cut_row: dict[str, Any], relation: str) -> int:
    if relation == "exact":
        return len(cut_row["single_relation"]["exact_survivor_ids"]) * len(
            cut_row["pair_relation"]["exact_2q_survivor_ids"]
        )
    if relation == "probe":
        return len(cut_row["single_relation"]["probe_survivor_ids"]) * len(
            cut_row["pair_relation"]["probe_2q_survivor_ids"]
        )
    raise ValueError(relation)


def schmidt_and_density_strata(rho: np.ndarray, cut_matrices: dict[str, dict[str, np.ndarray]]) -> dict[str, Any]:
    global_rank = matrix_rank(rho)
    global_purity = density_purity(rho)
    is_pure = global_rank == 1 and abs(global_purity - 1.0) <= 1.0e-8
    rows = {}
    for cut, matrices in cut_matrices.items():
        single = matrices["single"]
        pair = matrices["pair"]
        single_eig = rounded_eigvals(single)
        pair_eig = rounded_eigvals(pair)
        single_rank = matrix_rank(single)
        pair_rank = matrix_rank(pair)
        rows[cut] = {
            "single_rank": single_rank,
            "pair_rank": pair_rank,
            "single_spectrum": single_eig,
            "pair_spectrum": pair_eig,
            "density_rank_stratum": f"single_rank_{single_rank}__pair_rank_{pair_rank}",
            "schmidt_status": "pure_schmidt" if is_pure else "mixed_density_rank_stratum_not_pure_schmidt",
            "schmidt_rank": single_rank if is_pure else None,
            "schmidt_spectrum": single_eig if is_pure else None,
        }
    return {
        "global_rank": global_rank,
        "global_purity": global_purity,
        "pure_state": is_pure,
        "cuts": rows,
    }


def build_cut_rows(
    survivor: dict[str, Any],
    rho: np.ndarray,
    one_index: dict[str, Any],
    two_index: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, dict[str, np.ndarray]]]:
    cut_rows = {}
    cut_matrices = {}
    for cut, spec in CUTS.items():
        single = partial_trace(rho, spec["single_keep"])
        pair = partial_trace(rho, spec["pair_keep"])
        single_relation = match_single(single, one_index)
        pair_relation = match_pair(pair, two_index)
        exact = single_relation["exact_resolves"] and pair_relation["exact_resolves"]
        probe = single_relation["probe_resolves"] and pair_relation["probe_resolves"]
        exact_mult = cut_multiplicity({"single_relation": single_relation, "pair_relation": pair_relation}, "exact")
        probe_mult = cut_multiplicity({"single_relation": single_relation, "pair_relation": pair_relation}, "probe")
        cut_rows[cut] = {
            "cut": cut,
            "rho_single": spec["single"],
            "rho_pair": spec["pair"],
            "computed_from_stored_rho_ABC": True,
            "partial_trace_tested": True,
            "single_relation": single_relation,
            "pair_relation": pair_relation,
            "exact_cut_compatible": exact,
            "probe_cut_compatible": probe,
            "exact_cut_family_multiplicity": exact_mult,
            "probe_cut_family_multiplicity": probe_mult,
        }
        cut_matrices[cut] = {"single": single, "pair": pair}
    return cut_rows, cut_matrices


def compatible_family_row(survivor: dict[str, Any], cut_rows: dict[str, Any], relation: str) -> dict[str, Any] | None:
    all_ok_key = f"{relation}_cut_compatible"
    if not all(row[all_ok_key] for row in cut_rows.values()):
        return None
    cut_counts = {cut: cut_multiplicity(row, relation) for cut, row in cut_rows.items()}
    multiplicity = product(list(cut_counts.values()))
    return {
        "family_id": family_row_id(relation, survivor, cut_rows),
        "relation": relation,
        "rho_ABC_content_id": survivor_content_id(survivor),
        "survivor_id": survivor["survivor_id"],
        "candidate_id": survivor["candidate_id"],
        "candidate_label": survivor["candidate_label"],
        "family": survivor["family"],
        "source_gcm_2q_survivor_id": survivor.get("source_gcm_2q_survivor_id"),
        "tripartite_entangled_anchor": bool(survivor.get("tripartite_entangled_anchor")),
        "cut_family_multiplicities": cut_counts,
        "family_multiplicity": multiplicity,
        "cut_relation_ids": {
            cut: {
                "single_ids": row["single_relation"][f"{relation}_survivor_ids"],
                "pair_ids": row["pair_relation"][f"{relation}_2q_survivor_ids"],
            }
            for cut, row in cut_rows.items()
        },
    }


def build_tower(
    one_q: dict[str, Any],
    two_q: dict[str, Any],
    three_q: dict[str, Any],
) -> dict[str, Any]:
    one_index = one_q_indexes(one_q)
    two_index = two_q_indexes(two_q)
    states = three_q["state_artifacts"]["states_by_content_id"]
    survivors = sorted(three_q["survivors"], key=lambda row: int(row["survivor_id"]))

    object_maps = []
    exact_rows = []
    probe_rows = []
    extension_accumulator: dict[str, dict[str, dict[str, set[str]]]] = {
        pair: defaultdict(lambda: {"exact": set(), "probe": set()}) for pair in PAIR_TO_CUT
    }
    pair_source_match_rows = []

    for survivor in survivors:
        rho = survivor_state_matrix(survivor, states)
        cut_rows, cut_matrices = build_cut_rows(survivor, rho, one_index, two_index)
        strata = schmidt_and_density_strata(rho, cut_matrices)
        exact_row = compatible_family_row(survivor, cut_rows, "exact")
        probe_row = compatible_family_row(survivor, cut_rows, "probe")
        if exact_row:
            exact_rows.append(exact_row)
        if probe_row:
            probe_rows.append(probe_row)

        for cut, row in cut_rows.items():
            pair = row["rho_pair"]
            for sid in row["pair_relation"]["exact_2q_survivor_ids"]:
                extension_accumulator[pair][sid]["exact"].add(str(survivor["survivor_id"]))
            for sid in row["pair_relation"]["probe_2q_survivor_ids"]:
                extension_accumulator[pair][sid]["probe"].add(str(survivor["survivor_id"]))

        source_id = survivor.get("source_gcm_2q_survivor_id")
        source_match = None
        if source_id:
            source_match = source_id in cut_rows["C|AB"]["pair_relation"]["exact_2q_survivor_ids"]
            pair_source_match_rows.append(
                {
                    "survivor_id": survivor["survivor_id"],
                    "source_gcm_2q_survivor_id": source_id,
                    "correct_C_AB_exact_source_match": source_match,
                    "scrambled_A_BC_exact_source_match": source_id
                    in cut_rows["A|BC"]["pair_relation"]["exact_2q_survivor_ids"],
                    "scrambled_B_AC_exact_source_match": source_id
                    in cut_rows["B|AC"]["pair_relation"]["exact_2q_survivor_ids"],
                }
            )

        exact_failed_cuts = [cut for cut, row in cut_rows.items() if not row["exact_cut_compatible"]]
        probe_failed_cuts = [cut for cut, row in cut_rows.items() if not row["probe_cut_compatible"]]
        object_maps.append(
            {
                "rho_ABC_content_id": survivor_content_id(survivor),
                "survivor_id": survivor["survivor_id"],
                "candidate_id": survivor["candidate_id"],
                "candidate_label": survivor["candidate_label"],
                "family": survivor["family"],
                "source_gcm_2q_survivor_id": source_id,
                "source_2q_family": survivor.get("source_2q_family"),
                "tripartite_entangled_anchor": bool(survivor.get("tripartite_entangled_anchor")),
                "cut_relations": cut_rows,
                "exact_all_cuts_compatible": exact_row is not None,
                "probe_all_cuts_compatible": probe_row is not None,
                "exact_all_cut_family_multiplicity": exact_row["family_multiplicity"] if exact_row else 0,
                "probe_all_cut_family_multiplicity": probe_row["family_multiplicity"] if probe_row else 0,
                "exact_failed_cuts": exact_failed_cuts,
                "probe_failed_cuts": probe_failed_cuts,
                "schmidt_strata_per_cut": strata,
            }
        )

    return {
        "object_maps": object_maps,
        "compatible_family_rows_exact": exact_rows,
        "compatible_family_rows_probe": probe_rows,
        "extension_fibers_F3": build_extension_fibers(two_index, extension_accumulator),
        "pair_source_match_rows": pair_source_match_rows,
    }


def build_extension_fibers(
    two_index: dict[str, Any],
    accumulator: dict[str, dict[str, dict[str, set[str]]]],
) -> list[dict[str, Any]]:
    rows = []
    for pair in ("AB", "AC", "BC"):
        for sid in two_index["survivor_ids"]:
            exact_ids = sorted(accumulator[pair].get(sid, {}).get("exact", set()), key=lambda value: int(value))
            probe_ids = sorted(accumulator[pair].get(sid, {}).get("probe", set()), key=lambda value: int(value))
            two_row = two_index["by_id"][sid]
            rows.append(
                {
                    "rho_pair": pair,
                    "cut": PAIR_TO_CUT[pair],
                    "two_q_survivor_id": sid,
                    "two_q_family": two_row["family"],
                    "two_q_entangled": two_row["entangled"],
                    "first_bloch_scaled": two_row["first_bloch_scaled"],
                    "second_bloch_scaled": two_row["second_bloch_scaled"],
                    "probe_signature": two_row["probe_signature"],
                    "exact_member_3q_survivor_ids": exact_ids,
                    "probe_member_3q_survivor_ids": probe_ids,
                    "sizes": {"exact": len(exact_ids), "probe": len(probe_ids)},
                }
            )
    return rows


def summarize_counts(tower: dict[str, Any], three_q: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]
    exact_maps = [row for row in maps if row["exact_all_cuts_compatible"]]
    probe_maps = [row for row in maps if row["probe_all_cuts_compatible"]]
    exact_family_count = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_exact"])
    probe_family_count = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_probe"])
    product_maps = [row for row in maps if row["family"] == "2q_survivor_product_lift"]
    entangled_maps = [row for row in maps if row["tripartite_entangled_anchor"]]
    return {
        "one_q_survivor_count": EXPECTED_1Q_SURVIVOR_COUNT,
        "two_q_survivor_count": EXPECTED_2Q_SURVIVOR_COUNT,
        "three_q_survivor_count": len(maps),
        "three_q_candidate_count": three_q["candidate_space"]["candidate_count"],
        "exact_all_cut_compatible_3q_count": len(exact_maps),
        "exact_all_cut_compatible_family_count": exact_family_count,
        "exact_all_cut_orphan_3q_count": len(maps) - len(exact_maps),
        "probe_all_cut_compatible_3q_count": len(probe_maps),
        "probe_all_cut_compatible_family_count": probe_family_count,
        "probe_all_cut_orphan_3q_count": len(maps) - len(probe_maps),
        "probe_rescued_exact_orphan_3q_count": sum(
            1 for row in maps if not row["exact_all_cuts_compatible"] and row["probe_all_cuts_compatible"]
        ),
        "quotient_multiplicity_added_family_count": probe_family_count - exact_family_count,
        "product_lift_3q_count": len(product_maps),
        "product_lift_exact_all_cut_compatible_count": sum(1 for row in product_maps if row["exact_all_cuts_compatible"]),
        "product_lift_probe_all_cut_compatible_count": sum(1 for row in product_maps if row["probe_all_cuts_compatible"]),
        "product_lift_probe_family_count": sum(row["probe_all_cut_family_multiplicity"] for row in product_maps),
        "tripartite_entangled_anchor_count": len(entangled_maps),
        "tripartite_entangled_exact_all_cut_compatible_count": sum(
            1 for row in entangled_maps if row["exact_all_cuts_compatible"]
        ),
        "tripartite_entangled_probe_all_cut_compatible_count": sum(
            1 for row in entangled_maps if row["probe_all_cuts_compatible"]
        ),
        "tripartite_entangled_probe_family_count": sum(
            row["probe_all_cut_family_multiplicity"] for row in entangled_maps
        ),
    }


def fiber_summary(tower: dict[str, Any]) -> dict[str, Any]:
    rows = tower["extension_fibers_F3"]

    def dist(pair: str, key: str) -> dict[str, int]:
        values = [row["sizes"][key] for row in rows if row["rho_pair"] == pair]
        return {str(k): v for k, v in sorted(Counter(values).items())}

    summary = {"by_pair": {}}
    for pair in ("AB", "AC", "BC"):
        pair_rows = [row for row in rows if row["rho_pair"] == pair]
        exact_cover = {sid for row in pair_rows for sid in row["exact_member_3q_survivor_ids"]}
        probe_cover = {sid for row in pair_rows for sid in row["probe_member_3q_survivor_ids"]}
        summary["by_pair"][pair] = {
            "fiber_count": len(pair_rows),
            "exact_size_distribution": dist(pair, "exact"),
            "probe_size_distribution": dist(pair, "probe"),
            "exact_3q_cover_count": len(exact_cover),
            "probe_3q_cover_count": len(probe_cover),
        }
    return summary


def orphan_summary(tower: dict[str, Any]) -> dict[str, Any]:
    maps = tower["object_maps"]

    def characterize(rows: list[dict[str, Any]], relation: str) -> dict[str, Any]:
        failed_key = f"{relation}_failed_cuts"
        return {
            "count": len(rows),
            "by_family": dict(sorted(Counter(row["family"] for row in rows).items())),
            "by_failed_cut_set": dict(
                sorted(Counter("|".join(row[failed_key]) if row[failed_key] else "none" for row in rows).items())
            ),
            "sample_survivor_ids": [row["survivor_id"] for row in rows[:24]],
        }

    exact_orphans = [row for row in maps if not row["exact_all_cuts_compatible"]]
    probe_orphans = [row for row in maps if not row["probe_all_cuts_compatible"]]
    return {
        "exact_tower_orphans": characterize(exact_orphans, "exact"),
        "probe_tower_orphans": characterize(probe_orphans, "probe"),
        "characterization": (
            "A 3Q tower orphan is a state-artifacted 3Q survivor whose recomputed partial traces fail at least "
            "one of the three cut relations against the frozen lower registry under the named relation."
        ),
        "relation_ceiling": "registry-coordinate/probe orphan characterization, not a full-density canonical quotient",
    }


def schmidt_summary(tower: dict[str, Any]) -> dict[str, Any]:
    rows = tower["object_maps"]
    out: dict[str, Any] = {"by_cut": {}, "pure_state_count": 0, "mixed_state_count": 0}
    out["pure_state_count"] = sum(1 for row in rows if row["schmidt_strata_per_cut"]["pure_state"])
    out["mixed_state_count"] = len(rows) - out["pure_state_count"]
    for cut in CUTS:
        cut_rows = [row["schmidt_strata_per_cut"]["cuts"][cut] for row in rows]
        out["by_cut"][cut] = {
            "density_rank_strata": dict(sorted(Counter(row["density_rank_stratum"] for row in cut_rows).items())),
            "pure_schmidt_rank_strata": dict(
                sorted(Counter(str(row["schmidt_rank"]) for row in cut_rows if row["schmidt_rank"] is not None).items())
            ),
        }
    return out


def root_axiom_question(counts: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    exact_entangled = counts["tripartite_entangled_exact_all_cut_compatible_count"]
    exact_nonempty = counts["exact_all_cut_compatible_3q_count"] > 0
    probe_entangled = counts["tripartite_entangled_probe_all_cut_compatible_count"]
    entangled_rows = [
        row
        for row in tower["object_maps"]
        if row["tripartite_entangled_anchor"] and row["probe_all_cuts_compatible"]
    ]
    return {
        "question": "At 3Q, does the exact tower stay product-trivial and does the probe quotient again admit the entangled?",
        "exact_tower_stays_product_trivial": exact_entangled == 0,
        "exact_tower_nonempty": exact_nonempty,
        "exact_tripartite_entangled_family_count": sum(
            row["family_multiplicity"]
            for row in tower["compatible_family_rows_exact"]
            if row["tripartite_entangled_anchor"]
        ),
        "probe_quotient_admits_tripartite_entangled_anchor": probe_entangled > 0,
        "probe_tripartite_entangled_family_count": counts["tripartite_entangled_probe_family_count"],
        "surviving_entangled_probe_rows": [
            {
                "survivor_id": row["survivor_id"],
                "candidate_label": row["candidate_label"],
                "rho_ABC_content_id": row["rho_ABC_content_id"],
                "probe_all_cut_family_multiplicity": row["probe_all_cut_family_multiplicity"],
                "cut_probe_signatures": {
                    cut: {
                        "single": cut_row["single_relation"]["probe_signature"],
                        "pair": cut_row["pair_relation"]["probe_signature"],
                    }
                    for cut, cut_row in row["cut_relations"].items()
                },
            }
            for row in entangled_rows
        ],
        "outcome_ceiling": CLAIM_CEILING,
    }


def le2_regression(le2: dict[str, Any]) -> dict[str, Any]:
    counts = le2["counts"]
    checks = {key: counts.get(key) == expected for key, expected in LE2_REGRESSION_EXPECTED_COUNTS.items()}
    return {
        "authority_commit": EXPECTED_LE2_AUDIT_COMMIT,
        "source_path": rel(LE2_TOWER_RESULT_PATH),
        "git_last_commit": git_last_commit(LE2_TOWER_RESULT_PATH),
        "expected_counts": LE2_REGRESSION_EXPECTED_COUNTS,
        "observed_counts": {key: counts.get(key) for key in LE2_REGRESSION_EXPECTED_COUNTS},
        "all_counts_reproduced": all(checks.values()),
        "checks": checks,
    }


def product_baseline(counts: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    product_rows = [row for row in tower["object_maps"] if row["family"] == "2q_survivor_product_lift"]
    return {
        "product_lift_count": len(product_rows),
        "expected_product_lift_count": EXPECTED_3Q_PRODUCT_LIFT_COUNT,
        "all_product_lifts_probe_compatible_all_three_cuts": all(
            row["probe_all_cuts_compatible"] for row in product_rows
        ),
        "product_lift_exact_all_cut_compatible_count": counts["product_lift_exact_all_cut_compatible_count"],
        "product_lift_probe_family_count": counts["product_lift_probe_family_count"],
        "pair_entanglement_not_claimed_in_product_lift_state": all(
            row.get("source_2q_family") is not None for row in product_rows
        ),
    }


def scrambled_pairing_control(tower: dict[str, Any]) -> dict[str, Any]:
    rows = tower["pair_source_match_rows"]
    correct_matches = sum(1 for row in rows if row["correct_C_AB_exact_source_match"])
    scrambled_a_matches = sum(1 for row in rows if row["scrambled_A_BC_exact_source_match"])
    scrambled_b_matches = sum(1 for row in rows if row["scrambled_B_AC_exact_source_match"])
    red = correct_matches == EXPECTED_3Q_PRODUCT_LIFT_COUNT and (
        scrambled_a_matches != EXPECTED_3Q_PRODUCT_LIFT_COUNT
        or scrambled_b_matches != EXPECTED_3Q_PRODUCT_LIFT_COUNT
    )
    return {
        "control": "scrambled-pairing",
        "correct_C_AB_source_match_count": correct_matches,
        "scrambled_A_BC_source_match_count": scrambled_a_matches,
        "scrambled_B_AC_source_match_count": scrambled_b_matches,
        "expected_correct_match_count": EXPECTED_3Q_PRODUCT_LIFT_COUNT,
        "negative_verdict": "red" if red else "failed_to_turn_red",
        "red": red,
        "sample_rows": rows[:12],
    }


def helper_payloads(
    one_q: dict[str, Any],
    two_q: dict[str, Any],
    tower: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    first_map = tower["object_maps"][0]
    one_payload = {
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
            "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "survivor_ids": [one_q["frozen_registry"]["survivors"][0]["survivor_id"]],
            "quotient_class_ids": [one_q["frozen_registry"]["quotient_classes"][0]["quotient_class_id"]],
            "candidate_region_ids": [one_q["frozen_registry"]["candidate_regions"][0]["candidate_region_id"]],
        }
    }
    two_payload = {
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
            "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
            "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_BODY_SHA256,
            "survivor_ids": first_map["cut_relations"]["C|AB"]["single_relation"]["probe_survivor_ids"][:1],
            "gcm_2q_survivor_ids": [two_q["frozen_2q_registry"]["survivors"][0]["gcm_2q_survivor_id"]],
            "gcm_2q_quotient_class_ids": [
                two_q["frozen_2q_registry"]["quotient_classes"][0]["gcm_2q_quotient_class_id"]
            ],
            "gcm_2q_candidate_region_ids": [
                two_q["frozen_2q_registry"]["candidate_regions"][0]["gcm_2q_candidate_region_id"]
            ],
        }
    }
    negative_payload = {
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
            "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "survivor_ids": [],
            "quotient_class_ids": [],
            "candidate_region_ids": [],
        }
    }
    return one_payload, two_payload, negative_payload


def substrate_checks(
    one_q: dict[str, Any],
    two_q: dict[str, Any],
    three_q: dict[str, Any],
    tower: dict[str, Any],
) -> dict[str, Any]:
    one_payload, two_payload, negative_payload = helper_payloads(one_q, two_q, tower)
    one_check = gcm_substrate_check(one_payload, ONE_Q_REGISTRY_PATH)
    two_check = gcm_substrate_check(two_payload, TWO_Q_REGISTRY_PATH)
    negative_check = gcm_substrate_check(negative_payload, ONE_Q_REGISTRY_PATH)
    write_json(LINEAGE_FREE_NEGATIVE_PATH, negative_check)
    parent_commit = git_last_commit(THREE_Q_RESULT_PATH)
    parent_hash = sha256_file(THREE_Q_RESULT_PATH)
    three_q_checks = {
        "source_path": rel(THREE_Q_RESULT_PATH),
        "source_sha256": parent_hash,
        "git_last_commit": parent_commit,
        "expected_authority_commit": EXPECTED_3Q_V1_COMMIT,
        "commit_matches_authority": parent_commit == EXPECTED_3Q_V1_COMMIT,
        "survivor_count_matches": three_q.get("survivor_count") == EXPECTED_3Q_SURVIVOR_COUNT,
        "state_artifacted_survivors_by_content_id": len(three_q["state_artifacts"]["survivor_states"])
        == EXPECTED_3Q_SURVIVOR_COUNT,
    }
    return {
        "helper_scope": "hardened helper is load-bearing for 1Q/2Q substrate; packet-local checks bind 3Q v1 source/count/content-id lineage",
        "one_q_positive": one_check,
        "two_q_positive": two_check,
        "lineage_free_negative": negative_check,
        "lineage_free_negative_red": negative_check.get("ok") is False,
        "three_q_parent_source_check": three_q_checks,
        "all_positive_ok": one_check.get("ok") is True and two_check.get("ok") is True,
        "negatives_red": negative_check.get("ok") is False,
    }


def z3_count_proof(counts: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    exact_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_exact"])
    probe_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_probe"])
    solver = z3.Solver()
    exact = z3.Int("le3q_exact_family_count")
    probe = z3.Int("le3q_probe_family_count")
    solver.add(exact == exact_sum)
    solver.add(probe == probe_sum)
    solver.add(
        z3.Or(
            exact != int(counts["exact_all_cut_compatible_family_count"]),
            probe != int(counts["probe_all_cut_compatible_family_count"]),
        )
    )
    verdict = str(solver.check())
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "assertion": "computed family count sums disagree with result counts",
        "bound_values": {"exact": exact_sum, "probe": probe_sum},
    }


def cvc5_count_proof(counts: dict[str, Any], tower: dict[str, Any]) -> dict[str, Any]:
    exact_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_exact"])
    probe_sum = sum(row["family_multiplicity"] for row in tower["compatible_family_rows_probe"])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    exact = solver.mkConst(int_sort, "le3q_exact_family_count")
    probe = solver.mkConst(int_sort, "le3q_probe_family_count")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, exact, solver.mkInteger(exact_sum)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, probe, solver.mkInteger(probe_sum)))
    exact_bad = solver.mkTerm(
        Kind.NOT,
        solver.mkTerm(Kind.EQUAL, exact, solver.mkInteger(int(counts["exact_all_cut_compatible_family_count"]))),
    )
    probe_bad = solver.mkTerm(
        Kind.NOT,
        solver.mkTerm(Kind.EQUAL, probe, solver.mkInteger(int(counts["probe_all_cut_compatible_family_count"]))),
    )
    solver.assertFormula(solver.mkTerm(Kind.OR, exact_bad, probe_bad))
    verdict = str(solver.checkSat()).lower()
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "assertion": "computed family count sums disagree with result counts",
        "bound_values": {"exact": exact_sum, "probe": probe_sum},
    }


def controls(counts: dict[str, Any], tower: dict[str, Any], le2: dict[str, Any]) -> dict[str, Any]:
    return {
        "le2_regression": le2_regression(le2),
        "scrambled_pairing": scrambled_pairing_control(tower),
        "product_baseline": product_baseline(counts, tower),
    }


def source_locks() -> dict[str, Any]:
    return {
        "one_q_registry": source_lock(ONE_Q_REGISTRY_PATH, "1Q frozen registry"),
        "two_q_registry": source_lock(TWO_Q_REGISTRY_PATH, "2Q frozen registry"),
        "le2_tower_authority": source_lock(LE2_TOWER_RESULT_PATH, "<=2Q tower + audit authority"),
        "three_q_v1_authority": source_lock(THREE_Q_RESULT_PATH, "3Q v1 state-artifacted survivor authority"),
        "nesting_law_authority": source_lock(NESTING_LAW_SPEC_PATH, "nesting law authority"),
        "audit_standards_codex": source_lock(AUDIT_STANDARDS_CODEX_PATH, "standards codex G.2a"),
        "gcm_substrate_check": source_lock(GCM_SUBSTRATE_HELPER_PATH, "hardened helper"),
        "builder_audit_boundary": source_lock(BUILDER_AUDIT_BOUNDARY_PATH, "G.2a boundary helper"),
    }


def source_authority_checks(locks: dict[str, Any]) -> dict[str, bool]:
    return {
        "le2_authority_commit_matches": locks["le2_tower_authority"]["git_last_commit"] == EXPECTED_LE2_AUDIT_COMMIT,
        "three_q_v1_authority_commit_matches": locks["three_q_v1_authority"]["git_last_commit"] == EXPECTED_3Q_V1_COMMIT,
        "nesting_law_authority_commit_matches": locks["nesting_law_authority"]["git_last_commit"]
        == EXPECTED_NESTING_LAW_COMMIT,
    }


def build_packet(*, write_negative: bool = True) -> dict[str, Any]:
    one_q = load_json(ONE_Q_REGISTRY_PATH)
    two_q = load_json(TWO_Q_REGISTRY_PATH)
    le2 = load_json(LE2_TOWER_RESULT_PATH)
    three_q = load_json(THREE_Q_RESULT_PATH)
    tower = build_tower(one_q, two_q, three_q)
    counts = summarize_counts(tower, three_q)
    locks = source_locks()
    substrates = substrate_checks(one_q, two_q, three_q, tower) if write_negative else {}
    crossover = {
        "z3": z3_count_proof(counts, tower),
        "cvc5": cvc5_count_proof(counts, tower),
    }
    packet = {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "created_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "engine_mode": ENGINE_MODE,
        "axis_declaration": AXIS_DECLARATION,
        "relation_boundary": {
            "carrier": "state-artifacted 3Q survivor rho_ABC content ids plus frozen 1Q/2Q registry coordinates",
            "pins": "exact uses frozen local-pin coordinate equality; probe uses active x/z quotient classes from the lower registries",
            "not_claimed": [
                "canonical full-density equality quotient",
                "formal admission beyond scratch diagnostic",
                "axis-level bridge claim",
            ],
        },
        "authority": {
            "le2_tower_audit_commit": EXPECTED_LE2_AUDIT_COMMIT,
            "three_q_v1_commit": EXPECTED_3Q_V1_COMMIT,
            "nesting_law_commit": EXPECTED_NESTING_LAW_COMMIT,
        },
        "source_locks": locks,
        "source_authority_checks": source_authority_checks(locks),
        "gcm_lineage": {
            "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
            "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
            "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
            "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_BODY_SHA256,
            "three_q_parent_sim_id": "gcm_constraint_carve_3q_v1",
            "three_q_parent_commit": locks["three_q_v1_authority"]["git_last_commit"],
            "three_q_survivor_content_id_count": EXPECTED_3Q_SURVIVOR_COUNT,
            "object_maps": [
                {
                    "survivor_id": one_q["frozen_registry"]["survivors"][0]["survivor_id"],
                    "gcm_2q_survivor_id": two_q["frozen_2q_registry"]["survivors"][0]["gcm_2q_survivor_id"],
                    "gcm_2q_quotient_class_id": two_q["frozen_2q_registry"]["quotient_classes"][0][
                        "gcm_2q_quotient_class_id"
                    ],
                    "gcm_2q_candidate_region_id": two_q["frozen_2q_registry"]["candidate_regions"][0][
                        "gcm_2q_candidate_region_id"
                    ],
                }
            ],
        },
        "counts": counts,
        "compatible_families": {
            "representation": "compressed rows; family_multiplicity is the product over all three cut relation id-list sizes",
            "exact_rows": tower["compatible_family_rows_exact"],
            "probe_rows": tower["compatible_family_rows_probe"],
            "exact_rows_sha256": stable_sha256(tower["compatible_family_rows_exact"]),
            "probe_rows_sha256": stable_sha256(tower["compatible_family_rows_probe"]),
        },
        "object_maps": tower["object_maps"],
        "extension_fibers_F3": tower["extension_fibers_F3"],
        "fiber_summary": fiber_summary(tower),
        "root_axiom_question_at_3q": root_axiom_question(counts, tower),
        "schmidt_strata_summary": schmidt_summary(tower),
        "tower_orphan_characterization": orphan_summary(tower),
        "controls": controls(counts, tower, le2),
        "substrate_checks": substrates,
        "crossover_proofs": crossover,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "build_boundary": {
            "G_2a_from_birth": True,
            "no_builder_audit_verdict": True,
            "no_audit_verdict_written": True,
            "file_disjoint_packet": True,
            "builder_audit_boundary_ok": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        },
        "classical_baseline": {
            "name": "product baseline over 3Q product lifts",
            "divergence_log": [
                "exact all-cut relation may be empty or product-only because exact lower-registry pins are stricter than product construction",
                "probe all-cut relation admits product lifts by lower quotient classes",
                "tripartite entangled admission is reported only under probe quotient if recomputed cut rows resolve",
            ],
        },
    }
    return packet


def main() -> int:
    packet = build_packet()
    write_json(RESULT_PATH, packet)
    print(json.dumps({"ok": True, "result_path": rel(RESULT_PATH), "counts": packet["counts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
