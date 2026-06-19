#!/usr/bin/env python3
"""Torsion-aware adjudicating consumer for fiber_augmented_cover_v2_1."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import sympy as sp
from sympy.matrices.normalforms import smith_normal_form


SIM_ID = "topology_parity_guard_v3"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FIBER_V2_1_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v2_1"
FIBER_V2_1_RESULT_PATH = FIBER_V2_1_DIR / "results" / "fiber_augmented_cover_v2_1_results.json"
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_consumer_guard_only_no_new_construction"
SOURCE_AUDIT_COMMIT = "eb96d0e87"
GUARD_V2_AUDIT_COMMIT = "2137ae3e8"

COMPLEX_ORDER = [
    "v2_1_shifted_degree_one_mod3",
    "zero_shift_product_control",
    "wrong_gluing_generator_not_threaded_control",
    "old_v2_regression_coboundary_control",
]
EXPECTED_CHAIN_HASHES = {
    "v2_1_shifted_degree_one_mod3": "6afe8ea8f778ae9f470354a641a8989e40868df5efa8c9792fcdd2eb25c3c75a",
    "zero_shift_product_control": "5315bd250363ab44ed209f9102f9f00f8a7aad72105fdb95452d9b1a5ae5bd76",
    "wrong_gluing_generator_not_threaded_control": "856ae6b070b7227dfff272c7e587f08d63cf06563d0a8394084baef782f64b8d",
    "old_v2_regression_coboundary_control": "151c47084f246e24665e80728a6c5492fdbe7feaecd96cbcdb6e94242b68d0d5",
}
EXPECTED_PROFILES = {
    "lens_l31": {"betti": [1, 0, 0, 1], "torsion": {"H0": [], "H1": [3], "H2": [], "H3": []}},
    "s3": {"betti": [1, 0, 0, 1], "torsion": {"H0": [], "H1": [], "H2": [], "H3": []}},
    "product_s2xs1": {"betti": [1, 1, 1, 1], "torsion": {"H0": [], "H1": [], "H2": [], "H3": []}},
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact integer rank and Smith normal form torsion computations",
    },
    "python_stdlib_json_hashlib_subprocess": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JSON consumption, stable boundary-only hashing, source locks, and result serialization",
    },
    "fiber_augmented_cover_v2_1_results_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing hash-pinned source for the four emitted complexes; no builder homology is cited",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a idempotency-from-birth builder/audit boundary",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "python_stdlib_json_hashlib_subprocess": "load_bearing",
    "fiber_augmented_cover_v2_1_results_json": "load_bearing",
    "builder_audit_boundary": "load_bearing",
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sparse_to_matrix(matrix: dict[str, Any]) -> sp.Matrix:
    rows, cols = matrix["shape"]
    out = sp.zeros(int(rows), int(cols))
    for entry in matrix["entries"]:
        out[int(entry["row"]), int(entry["col"])] = int(entry["value"])
    return out


def recompute_sparse_hash(matrix: dict[str, Any]) -> str:
    return stable_sha256({"shape": matrix["shape"], "entries": matrix["entries"]})


def rank(matrix: sp.Matrix) -> int:
    if matrix.rows == 0 or matrix.cols == 0:
        return 0
    return int(matrix.rank())


def smith_invariants(matrix: sp.Matrix) -> list[int]:
    if matrix.rows == 0 or matrix.cols == 0:
        return []
    normal = smith_normal_form(matrix, domain=sp.ZZ)
    return [
        abs(int(normal[i, i]))
        for i in range(min(normal.rows, normal.cols))
        if int(normal[i, i]) != 0
    ]


def sparse_matrix(rows: int, cols: int, value: int) -> dict[str, Any]:
    entries = [] if value == 0 else [{"row": 0, "col": 0, "value": int(value)}]
    return {
        "shape": [rows, cols],
        "entries": entries,
        "sha256": stable_sha256({"shape": [rows, cols], "entries": entries}),
    }


def one_cell_complex(coefficient: int) -> dict[str, Any]:
    return {
        "cell_counts": {"C0": 1, "C1": 1, "C2": 1, "C3": 1},
        "boundary_matrices": {
            "d1": sparse_matrix(1, 1, 0),
            "d2": sparse_matrix(1, 1, coefficient),
            "d3": sparse_matrix(1, 1, 0),
        },
    }


def boundary_matrices_only_payload(complex_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        name: {
            "shape": complex_payload["boundary_matrices"][name]["shape"],
            "entries": complex_payload["boundary_matrices"][name]["entries"],
        }
        for name in sorted(complex_payload["boundary_matrices"])
    }


def boundary_matrix_only_hash(complex_payload: dict[str, Any]) -> str:
    return stable_sha256(boundary_matrices_only_payload(complex_payload))


def homology_result(label: str, complex_payload: dict[str, Any], source_chain_sha256: str | None = None) -> dict[str, Any]:
    dims = [int(complex_payload["cell_counts"][f"C{i}"]) for i in range(4)]
    boundaries = {
        int(name[1:]): sparse_to_matrix(matrix)
        for name, matrix in complex_payload["boundary_matrices"].items()
    }
    ranks: dict[str, int] = {}
    smith: dict[str, list[int]] = {}
    d_squared_zero = True
    d_squared_errors: list[str] = []

    for degree in range(1, 4):
        matrix = boundaries.get(degree, sp.zeros(dims[degree - 1], dims[degree]))
        ranks[f"d{degree}"] = rank(matrix)
        smith[f"d{degree}"] = smith_invariants(matrix)

    for degree in range(2, 4):
        left = boundaries.get(degree - 1, sp.zeros(dims[degree - 2], dims[degree - 1]))
        right = boundaries.get(degree, sp.zeros(dims[degree - 1], dims[degree]))
        product = left * right
        if product != sp.zeros(product.rows, product.cols):
            d_squared_zero = False
            d_squared_errors.append(f"d{degree - 1}_d{degree}_nonzero")

    betti: list[int] = []
    torsion: dict[str, list[int]] = {}
    for degree in range(4):
        down = ranks.get(f"d{degree}", 0)
        up = ranks.get(f"d{degree + 1}", 0)
        betti.append(int(dims[degree] - down - up))
        torsion[f"H{degree}"] = [value for value in smith.get(f"d{degree + 1}", []) if value > 1]

    chain_euler = sum(((-1) ** degree) * dims[degree] for degree in range(4))
    betti_euler = sum(((-1) ** degree) * betti[degree] for degree in range(4))
    result = {
        "label": label,
        "source_chain_sha256": source_chain_sha256,
        "chain_dims_c0_to_c3": dims,
        "boundary_ranks": ranks,
        "smith_invariants": smith,
        "homology": {
            "betti_b0_b1_b2_b3": betti,
            "torsion": torsion,
            "torsion_description": describe_torsion(torsion),
        },
        "d_squared_zero": d_squared_zero,
        "d_squared_errors": d_squared_errors,
        "euler_cross_check": {
            "chain_euler_characteristic": chain_euler,
            "betti_euler_characteristic": betti_euler,
            "passed": chain_euler == betti_euler,
        },
        "boundary_matrix_only_hash": boundary_matrix_only_hash(complex_payload),
        "source_boundary_hashes": {
            name: matrix["sha256"]
            for name, matrix in complex_payload["boundary_matrices"].items()
        },
    }
    return result


def describe_torsion(torsion: dict[str, list[int]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for group, factors in torsion.items():
        out[group] = "free" if not factors else " x ".join(f"Z/{factor}" for factor in factors)
    return out


def run_reference_gate() -> dict[str, Any]:
    explicit_s3 = homology_result("explicit_s3", one_cell_complex(1))
    explicit_product = homology_result("explicit_s2xs1", one_cell_complex(0))
    explicit_lens = homology_result("explicit_lens_space_l31", one_cell_complex(3))
    passed = (
        explicit_s3["homology"]["betti_b0_b1_b2_b3"] == EXPECTED_PROFILES["s3"]["betti"]
        and explicit_s3["homology"]["torsion"] == EXPECTED_PROFILES["s3"]["torsion"]
        and explicit_product["homology"]["betti_b0_b1_b2_b3"] == EXPECTED_PROFILES["product_s2xs1"]["betti"]
        and explicit_product["homology"]["torsion"] == EXPECTED_PROFILES["product_s2xs1"]["torsion"]
        and explicit_lens["homology"]["betti_b0_b1_b2_b3"] == EXPECTED_PROFILES["lens_l31"]["betti"]
        and explicit_lens["homology"]["torsion"] == EXPECTED_PROFILES["lens_l31"]["torsion"]
        and explicit_s3["d_squared_zero"]
        and explicit_product["d_squared_zero"]
        and explicit_lens["d_squared_zero"]
    )
    return {
        "gate_rule": "cover rows are inadmissible unless explicit S3, S2xS1, and L(3,1) references recover through the same SNF machinery",
        "explicit_s3": explicit_s3,
        "explicit_s2xs1": explicit_product,
        "explicit_lens_space_l31": explicit_lens,
        "reference_gate_passed": passed,
    }


def run_controls() -> dict[str, Any]:
    trap = homology_result("degree_2_torsion_trap", one_cell_complex(2))
    trap["pass"] = (
        trap["homology"]["betti_b0_b1_b2_b3"] == [1, 0, 0, 1]
        and trap["homology"]["torsion"]["H1"] == [2]
        and trap["d_squared_zero"]
    )
    return {"degree_2_torsion_trap": trap}


def load_v2_1_payload() -> dict[str, Any]:
    return load_json(FIBER_V2_1_RESULT_PATH)


def verify_and_load_complexes(v2_1: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    errors: list[str] = []
    family = v2_1.get("complex_family", {})
    complexes = family.get("complexes", {})
    loaded: dict[str, Any] = {}

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(v2_1.get("betti_computed") is False, "builder packet must not compute Betti")
    require(v2_1.get("homology_computed") is False, "builder packet must not compute homology")
    require(v2_1.get("consumer_boundary", {}).get("intended_consumer") == SIM_ID, "builder intended consumer mismatch")
    require(family.get("complex_order") == COMPLEX_ORDER, "complex order mismatch")

    for complex_id in COMPLEX_ORDER:
        row = complexes.get(complex_id)
        require(isinstance(row, dict), f"missing complex: {complex_id}")
        if not isinstance(row, dict):
            continue
        require(row.get("chain_sha256") == EXPECTED_CHAIN_HASHES[complex_id], f"{complex_id} chain hash mismatch")
        require(row.get("betti_computed") is False, f"{complex_id} builder Betti boundary failed")
        require(row.get("homology_computed") is False, f"{complex_id} builder homology boundary failed")
        require(row.get("chain_checks", {}).get("d_squared_zero") is True, f"{complex_id} d^2 source check failed")
        for boundary_name, matrix in row.get("boundary_matrices", {}).items():
            require(recompute_sparse_hash(matrix) == matrix.get("sha256"), f"{complex_id} {boundary_name} boundary hash mismatch")
        loaded[complex_id] = row

    source = {
        "fiber_augmented_cover_v2_1_result": source_lock(
            FIBER_V2_1_RESULT_PATH,
            "eb96d0e87_four_hash_pinned_complexes_source",
            SOURCE_AUDIT_COMMIT,
        ),
        "fiber_augmented_cover_v2_1_audit": source_lock(
            FIBER_V2_1_DIR / "audit_verdict.md",
            "eb96d0e87_audit_caveat_and_boundary_matrix_separability_requirement",
            SOURCE_AUDIT_COMMIT,
        ),
        "guard_v2_audit": source_lock(
            ROOT / "system_v6/sims/topology_parity_guard_v2/audit_verdict.md",
            "2137ae3e8_guard_v2_arc_and_torsion_preregistration",
            GUARD_V2_AUDIT_COMMIT,
        ),
        "axis_work_order": source_lock(
            ROOT / "system_v6/receipts/axis_work_order_20260612.md",
            "two_reading_section_adjudicated_here",
        ),
        "audit_standards_codex": source_lock(
            ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
            "G.2a_from_birth_and_standards_codex",
        ),
        "builder_betti_computed": v2_1.get("betti_computed"),
        "builder_homology_computed": v2_1.get("homology_computed"),
        "expected_chain_hashes": EXPECTED_CHAIN_HASHES,
        "hash_verification_errors": errors,
        "hash_verification_passed": not errors,
    }
    if errors:
        raise RuntimeError("STOP: v2.1 complex hash/source verification failed: " + "; ".join(errors))
    return loaded, source


def math_content_separability(complexes: dict[str, Any]) -> dict[str, Any]:
    by_complex = {complex_id: boundary_matrix_only_hash(complexes[complex_id]) for complex_id in COMPLEX_ORDER}
    classes: dict[str, list[str]] = {}
    for complex_id, digest in by_complex.items():
        classes.setdefault(digest, []).append(complex_id)
    control_ids = COMPLEX_ORDER[1:]
    control_hashes = {by_complex[complex_id] for complex_id in control_ids}
    shifted_hash = by_complex["v2_1_shifted_degree_one_mod3"]
    passed = len(classes) == 2 and len(control_hashes) == 1 and shifted_hash not in control_hashes
    return {
        "hash_rule": "sha256 over boundary matrices only: d1/d2/d3 shapes and entries; no metadata, witness rows, or labels",
        "by_complex": by_complex,
        "classes": classes,
        "boundary_matrix_only_distinct_hash_count": len(classes),
        "expected_distinct_pure_complexes": 2,
        "control_complexes_mutually_isomorphic_expected": len(control_hashes) == 1,
        "control_isomorphism_reason": "the three controls have identical boundary matrices after metadata stripping",
        "shifted_separated_from_controls": shifted_hash not in control_hashes,
        "passed": passed,
    }


def expected_row(complex_id: str) -> dict[str, Any]:
    if complex_id == "v2_1_shifted_degree_one_mod3":
        return {
            "expected_profile": "lens_space_L31",
            "expected_betti_b0_b1_b2_b3": [1, 0, 0, 1],
            "expected_torsion": {"H0": [], "H1": [3], "H2": [], "H3": []},
        }
    return {
        "expected_profile": "product_S2xS1_unthreaded_control",
        "expected_betti_b0_b1_b2_b3": [1, 1, 1, 1],
        "expected_torsion": {"H0": [], "H1": [], "H2": [], "H3": []},
    }


def profile_matches(result: dict[str, Any], expected: dict[str, Any]) -> bool:
    return (
        result["homology"]["betti_b0_b1_b2_b3"] == expected["expected_betti_b0_b1_b2_b3"]
        and result["homology"]["torsion"] == expected["expected_torsion"]
        and result["d_squared_zero"] is True
        and result["euler_cross_check"]["passed"] is True
    )


def adjudicate(results: dict[str, Any], reference_gate: dict[str, Any], source_lock_row: dict[str, Any]) -> dict[str, Any]:
    if not reference_gate["reference_gate_passed"]:
        return {
            "winner": "MACHINERY_INSUFFICIENT",
            "status": "INSUFFICIENT",
            "finding_kind": "machinery_insufficient",
            "reason": "reference gate failed before cover rows",
        }
    if not source_lock_row["hash_verification_passed"]:
        return {
            "winner": "SOURCE_HASH_MISMATCH",
            "status": "INSUFFICIENT",
            "finding_kind": "source_hash_mismatch",
            "hash_errors": source_lock_row["hash_verification_errors"],
        }

    shifted = results["v2_1_shifted_degree_one_mod3"]
    shifted_betti = shifted["homology"]["betti_b0_b1_b2_b3"]
    shifted_torsion = shifted["homology"]["torsion"]
    controls_product = all(profile_matches(results[complex_id], expected_row(complex_id)) for complex_id in COMPLEX_ORDER[1:])
    if shifted_betti == [1, 0, 0, 1] and shifted_torsion["H1"] == [3] and controls_product:
        return {
            "winner": "READING_A_REPAIRED_WINS",
            "status": "EARNED",
            "finding_kind": "shifted_lens_space_profile_with_H1_Z3",
            "certificate_status": "FINITE_SECOND_CERTIFICATE_EARNED_BY_TORSION_GUARD_DATA",
            "plain_result": "the shifted repaired complex computes the L(3,1) homology profile while all unthreaded controls compute the product profile",
            "formal_admission_allowed": False,
        }
    if shifted_betti == [1, 1, 1, 1] and all(not values for values in shifted_torsion.values()):
        return {
            "winner": "READING_B_WINS",
            "status": "FAILED",
            "finding_kind": "shifted_product_profile_no_torsion",
            "certificate_status": "NO_FINITE_SECOND_CERTIFICATE",
            "plain_result": "even the generator re-pin loses structure in this encoding; cover labels must re-issue",
        }
    return {
        "winner": "UNEXPECTED_PROFILE",
        "status": "REPORT_STRAIGHT",
        "finding_kind": "unexpected_shifted_or_control_profile",
        "shifted_betti": shifted_betti,
        "shifted_torsion": shifted_torsion,
        "controls_product": controls_product,
    }


def build_topology_parity_guard_v3_object() -> dict[str, Any]:
    v2_1 = load_v2_1_payload()
    complexes, source_lock_row = verify_and_load_complexes(v2_1)
    reference_gate = run_reference_gate()
    controls = run_controls()
    separability = math_content_separability(complexes)
    complex_results: dict[str, Any] = {}
    expectation_results: dict[str, Any] = {}
    for complex_id in COMPLEX_ORDER:
        row = homology_result(complex_id, complexes[complex_id], complexes[complex_id]["chain_sha256"])
        expected = expected_row(complex_id)
        row["pre_registered_expectation"] = expected
        row["expectation_passed"] = profile_matches(row, expected)
        complex_results[complex_id] = row
        expectation_results[complex_id] = row["expectation_passed"]

    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    adjudication = adjudicate(complex_results, reference_gate, source_lock_row)
    all_pass = bool(
        source_lock_row["hash_verification_passed"]
        and reference_gate["reference_gate_passed"]
        and controls["degree_2_torsion_trap"]["pass"]
        and separability["passed"]
        and all(expectation_results.values())
        and adjudication["winner"] == "READING_A_REPAIRED_WINS"
        and boundary_ok
    )
    return {
        "schema": f"{SIM_ID}.object.v1",
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "preregistration_order": "build_card_written_before_v3_computation_then_reference_gate_then_hash_pinned_v2_1_complexes_then_adjudication",
        "expected_profiles_preregistered_from_math": {
            "shifted_repair": expected_row("v2_1_shifted_degree_one_mod3"),
            "controls": {complex_id: expected_row(complex_id) for complex_id in COMPLEX_ORDER[1:]},
            "adjudication_rule": {
                "shifted_lens_profile": "READING_A_REPAIRED_WINS",
                "shifted_product_profile": "READING_B_WINS",
                "anything_else": "UNEXPECTED_PROFILE",
            },
        },
        "source_complex_lock": source_lock_row,
        "reference_gate": reference_gate,
        "math_content_separability": separability,
        "complexes": complex_results,
        "controls": controls,
        "expectation_results": expectation_results,
        "adjudication": adjudication,
        "allowed_claims": [
            "scratch-diagnostic consumer homology of four hash-pinned fiber_augmented_cover_v2_1 complexes",
            "torsion-aware integer homology computation from explicit boundary matrices",
            "boundary-matrix-only math-content separability check",
            "pre-registered two-reading adjudication at consumer-guard ceiling",
        ],
        "disallowed_claims": [
            "new construction",
            "target Betti fitting",
            "formal admission",
            "canonical by process",
            "work-order update",
            "topology admission beyond this consumer guard",
            "bridge claim",
            "physics/manifold claim",
            "axis closure",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": {
            "g2a_boundary_from_birth": boundary_ok,
            "boundary_helper_path": rel(SIM_DIR / "topology_parity_guard_v3_boundary.py"),
            "shared_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
            "file_disjoint_packet": True,
            "no_git_add_or_commit_required": True,
            "no_new_cells_introduced": True,
            "consumer_only": True,
            "hash_mismatch_stop_rule": True,
            "math_content_separability_added": separability["passed"],
        },
        "all_pass": all_pass,
        "result_summary": {
            "reference_gate_passed": reference_gate["reference_gate_passed"],
            "hash_verification_passed": source_lock_row["hash_verification_passed"],
            "boundary_matrix_only_distinct_hash_count": separability["boundary_matrix_only_distinct_hash_count"],
            "shifted_betti": complex_results["v2_1_shifted_degree_one_mod3"]["homology"]["betti_b0_b1_b2_b3"],
            "shifted_torsion": complex_results["v2_1_shifted_degree_one_mod3"]["homology"]["torsion"],
            "adjudication_winner": adjudication["winner"],
            "certificate_status": adjudication.get("certificate_status"),
            "claim_ceiling": CLAIM_CEILING,
            "all_pass": all_pass,
        },
    }


def write_result() -> dict[str, Any]:
    payload = build_topology_parity_guard_v3_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope_result() -> dict[str, Any]:
    payload = build_topology_parity_guard_v3_object()
    envelope = {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "result_path": rel(RESULT_PATH),
        "all_pass": payload["all_pass"],
        "result_summary": payload["result_summary"],
        "source_complex_lock": payload["source_complex_lock"],
        "reference_gate": payload["reference_gate"],
        "math_content_separability": payload["math_content_separability"],
        "adjudication": payload["adjudication"],
        "complex_homology_summary": {
            complex_id: {
                "betti": payload["complexes"][complex_id]["homology"]["betti_b0_b1_b2_b3"],
                "torsion": payload["complexes"][complex_id]["homology"]["torsion"],
                "boundary_matrix_only_hash": payload["complexes"][complex_id]["boundary_matrix_only_hash"],
            }
            for complex_id in COMPLEX_ORDER
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": payload["builder_gates"],
    }
    write_json(ENVELOPE_RESULT_PATH, envelope)
    return envelope
