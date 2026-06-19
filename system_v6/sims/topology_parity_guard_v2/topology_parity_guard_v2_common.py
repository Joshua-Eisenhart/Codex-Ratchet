#!/usr/bin/env python3
"""Consumer homology guard for the committed fiber_augmented_cover_v2 complexes."""

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


SIM_ID = "topology_parity_guard_v2"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"

FIBER_V2_DIR = ROOT / "system_v6" / "sims" / "fiber_augmented_cover_v2"
FIBER_V2_RESULT_PATH = FIBER_V2_DIR / "results" / "fiber_augmented_cover_v2_results.json"
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
CLAIM_CEILING = "scratch_diagnostic_consumer_guard_only_no_new_construction"
BUILDER_COMMIT = "cc2f61b2a"
GUARD_V1_REJECT_COMMIT = "0207fecaf"

EXPECTED_BASE_CHAIN_SHA256 = "9d6655a51782305f80409cce0bd42a57329fb14ea19b05c32b95ec36016b883c"
EXPECTED_TOTAL_CHAIN_SHA256 = "38e57e928d722046eb0b734ff76d7a636c05e0f292ca59f97a3a3e0588d12a5c"
EXPECTED_BASE_BOUNDARY_HASHES = {
    "d1": "e36e2c77badce28030044b39b8128643928c0f38bf5a9c3f515b31c70536399a",
    "d2": "9d0c2669c4172ded9aa64e3c88dfe54669e1bc1bfbd0d2e193489b9a75a9827b",
}
EXPECTED_TOTAL_BOUNDARY_HASHES = {
    "d1": "305b45cb0c7048f794f892531b1244814e4ee650c339670108ca4ca9c13cb1bf",
    "d2": "6c593b1002dc256b78cd59767b4bc5fc91137a82a87b210b186cc3a11e7dcfef",
    "d3": "ed1dc588e4c3a6a80ed674439bbddd9933d6683f5831c1d55d32438bcd67aac7",
}

EXPECTED_PROFILES = {
    "s3_like": [1, 0, 0, 1],
    "s2xs1_product": [1, 1, 1, 1],
}

TOOL_MANIFEST = {
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact integer rank and Smith normal form homology computations",
    },
    "python_stdlib_json_hashlib_subprocess": {
        "tried": True,
        "used": True,
        "reason": "load-bearing result consumption, stable hash recomputation, and commit/path source locks",
    },
    "fiber_augmented_cover_v2_results_json": {
        "tried": True,
        "used": True,
        "reason": "load-bearing committed source of the pinned cellular boundary matrices; no Betti is cited from the builder",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a builder/audit boundary check",
    },
    "toponetx": {
        "tried": False,
        "used": False,
        "reason": "not relevant for the load-bearing claim because the committed input is already explicit integer cellular boundary matrices",
    },
    "gudhi": {
        "tried": False,
        "used": False,
        "reason": "not relevant for torsion-aware cellular homology; GUDHI Betti-only persistence would underpower the torsion claim surface",
    },
}
TOOL_INTEGRATION_DEPTH = {
    "sympy": "load_bearing",
    "python_stdlib_json_hashlib_subprocess": "load_bearing",
    "fiber_augmented_cover_v2_results_json": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "toponetx": None,
    "gudhi": None,
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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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


def matrix_payload(matrix: sp.Matrix) -> dict[str, Any]:
    entries: list[dict[str, int]] = []
    for row in range(matrix.rows):
        for col in range(matrix.cols):
            value = int(matrix[row, col])
            if value:
                entries.append({"row": row, "col": col, "value": value})
    return {"shape": [matrix.rows, matrix.cols], "entries": entries}


def homology_result(label: str, dims: list[int], boundaries: dict[int, sp.Matrix], source_hashes: dict[str, str] | None = None) -> dict[str, Any]:
    max_dim = len(dims) - 1
    ranks: dict[str, int] = {}
    smith: dict[str, list[int]] = {}
    torsion: dict[str, list[int]] = {}
    d_squared_zero = True
    d_squared_errors: list[str] = []

    for degree in range(1, max_dim + 1):
        mat = boundaries.get(degree, sp.zeros(dims[degree - 1], dims[degree]))
        ranks[f"d{degree}"] = rank(mat)
        smith[f"d{degree}"] = smith_invariants(mat)

    for degree in range(2, max_dim + 1):
        left = boundaries.get(degree - 1, sp.zeros(dims[degree - 2], dims[degree - 1]))
        right = boundaries.get(degree, sp.zeros(dims[degree - 1], dims[degree]))
        product = left * right
        if product != sp.zeros(product.rows, product.cols):
            d_squared_zero = False
            d_squared_errors.append(f"d{degree - 1}_d{degree}_nonzero")

    betti: list[int] = []
    for degree in range(max_dim + 1):
        down = ranks.get(f"d{degree}", 0)
        up = ranks.get(f"d{degree + 1}", 0)
        betti.append(int(dims[degree] - down - up))
        torsion[f"H{degree}"] = [value for value in smith.get(f"d{degree + 1}", []) if value > 1]

    return {
        "label": label,
        "chain_dims_c0_to_cmax": dims,
        "boundary_ranks": ranks,
        "smith_invariants": smith,
        "homology": {
            "betti_b0_b1_b2_b3": (betti + [0, 0, 0, 0])[:4],
            "torsion": {f"H{i}": torsion.get(f"H{i}", []) for i in range(4)},
            "torsion_description": describe_torsion({f"H{i}": torsion.get(f"H{i}", []) for i in range(4)}),
        },
        "d_squared_zero": d_squared_zero,
        "d_squared_errors": d_squared_errors,
        "source_boundary_hashes": source_hashes or {},
    }


def describe_torsion(torsion: dict[str, list[int]]) -> dict[str, str]:
    out: dict[str, str] = {}
    for group, factors in torsion.items():
        out[group] = "free" if not factors else " x ".join(f"Z/{factor}" for factor in factors)
    return out


def reduced_euler_reference(label: str, degree: int) -> dict[str, Any]:
    d1 = sp.zeros(1, 1)
    d2 = sp.Matrix([[degree]])
    d3 = sp.zeros(1, 1)
    result = homology_result(label, [1, 1, 1, 1], {1: d1, 2: d2, 3: d3})
    result["metadata"] = {
        "cell_rule": "independent reduced Euler-class reference complex",
        "degree": degree,
        "source": "pre_registered_reference_gate_not_cover_data",
    }
    return result


def run_reference_gate() -> dict[str, Any]:
    s3_like = reduced_euler_reference("explicit_s3_like", 1)
    product = reduced_euler_reference("explicit_s2xs1", 0)
    passed = (
        s3_like["homology"]["betti_b0_b1_b2_b3"] == EXPECTED_PROFILES["s3_like"]
        and product["homology"]["betti_b0_b1_b2_b3"] == EXPECTED_PROFILES["s2xs1_product"]
        and all(not values for values in s3_like["homology"]["torsion"].values())
        and all(not values for values in product["homology"]["torsion"].values())
        and s3_like["d_squared_zero"]
        and product["d_squared_zero"]
    )
    return {
        "gate_rule": "cover rows are skipped unless independent explicit S3-like and S2xS1 reference complexes recover the carried profiles first",
        "expected_profiles": EXPECTED_PROFILES,
        "explicit_s3_like": s3_like,
        "explicit_s2xs1": product,
        "reference_gate_passed": passed,
    }


def run_controls() -> dict[str, Any]:
    torsion_trap = reduced_euler_reference("degree_2_torsion_trap", 2)
    torsion_trap["pass"] = (
        torsion_trap["homology"]["betti_b0_b1_b2_b3"] == EXPECTED_PROFILES["s3_like"]
        and torsion_trap["homology"]["torsion"]["H1"] == [2]
    )
    return {
        "torsion_trap_degree_2": torsion_trap,
        "wrong_gluing_control": {
            "status": "INSUFFICIENT",
            "gap": "v2_committed_wrong_gluing_chain_complex_not_emitted",
            "reason": "the consumer can report the gap but must not introduce a fresh wrong-gluing cell complex",
        },
    }


def load_v2_payload() -> dict[str, Any]:
    return load_json(FIBER_V2_RESULT_PATH)


def source_lock(path: Path, role: str) -> dict[str, Any]:
    row: dict[str, Any] = {"path": rel(path), "role": role, "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    return row


def verify_pinned_complexes(v2: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    base = v2["cellular_base"]
    total = v2["total_space_cellular_structure"]

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    require(v2.get("betti_computed") is False, "builder packet must not have computed Betti")
    require("betti" not in v2, "builder packet must not emit top-level Betti")
    require(v2.get("consumer_boundary", {}).get("builder_consumer_separation") is True, "builder/consumer separation missing")
    require(base.get("chain_sha256") == EXPECTED_BASE_CHAIN_SHA256, "base chain hash mismatch")
    require(total.get("chain_sha256") == EXPECTED_TOTAL_CHAIN_SHA256, "total chain hash mismatch")
    require(base.get("cell_counts") == {"C0": 33, "C1": 92, "C2": 61}, "base counts mismatch")
    require(total.get("cell_counts") == {"C0": 99, "C1": 375, "C2": 459, "C3": 183}, "total counts mismatch")
    require(base.get("euler_characteristic") == 2, "base chi mismatch")
    require(total.get("euler_characteristic") == 0, "total chi mismatch")
    require(base.get("chain_checks", {}).get("d_squared_zero") is True, "base d^2 mismatch")
    require(total.get("chain_checks", {}).get("d_squared_zero") is True, "total d^2 mismatch")

    observed_base_hashes = {name: matrix["sha256"] for name, matrix in base["boundary_matrices"].items()}
    observed_total_hashes = {name: matrix["sha256"] for name, matrix in total["boundary_matrices"].items()}
    require(observed_base_hashes == EXPECTED_BASE_BOUNDARY_HASHES, "base boundary hash field mismatch")
    require(observed_total_hashes == EXPECTED_TOTAL_BOUNDARY_HASHES, "total boundary hash field mismatch")

    for name, matrix in base["boundary_matrices"].items():
        require(recompute_sparse_hash(matrix) == matrix["sha256"], f"base {name} sparse hash recompute mismatch")
    for name, matrix in total["boundary_matrices"].items():
        require(recompute_sparse_hash(matrix) == matrix["sha256"], f"total {name} sparse hash recompute mismatch")

    lock = {
        "builder_result_commit": BUILDER_COMMIT,
        "guard_v1_reject_commit": GUARD_V1_REJECT_COMMIT,
        "builder_result": source_lock(FIBER_V2_RESULT_PATH, "committed_chain_complex_source"),
        "builder_audit": source_lock(FIBER_V2_DIR / "audit_verdict.md", "genuine_audit_consumer_rule"),
        "builder_betti_computed": v2.get("betti_computed"),
        "consumer_boundary": v2.get("consumer_boundary"),
        "base": {
            "cell_counts": base["cell_counts"],
            "euler_characteristic": base["euler_characteristic"],
            "chain_sha256": base["chain_sha256"],
            "boundary_hashes": observed_base_hashes,
            "chain_checks": base["chain_checks"],
        },
        "total": {
            "cell_counts": total["cell_counts"],
            "euler_characteristic": total["euler_characteristic"],
            "chain_sha256": total["chain_sha256"],
            "boundary_hashes": observed_total_hashes,
            "chain_checks": total["chain_checks"],
        },
        "hash_verification_errors": errors,
        "hash_verification_passed": not errors,
    }
    return lock, errors


def committed_complex_result(label: str, complex_payload: dict[str, Any]) -> dict[str, Any]:
    dims = [int(complex_payload["cell_counts"][f"C{i}"]) for i in range(len(complex_payload["cell_counts"]))]
    boundaries = {
        int(name[1:]): sparse_to_matrix(matrix)
        for name, matrix in complex_payload["boundary_matrices"].items()
    }
    hashes = {name: matrix["sha256"] for name, matrix in complex_payload["boundary_matrices"].items()}
    return homology_result(label, dims, boundaries, hashes)


def adjudicate(total: dict[str, Any], reference_gate: dict[str, Any], source_lock_row: dict[str, Any]) -> dict[str, Any]:
    computed = total["homology"]["betti_b0_b1_b2_b3"]
    if not reference_gate["reference_gate_passed"]:
        return {
            "status": "INSUFFICIENT",
            "finding_kind": "machinery_insufficient",
            "reason": "reference gate failed; cover rows are not admissible",
        }
    if not source_lock_row["hash_verification_passed"]:
        return {
            "status": "INSUFFICIENT",
            "finding_kind": "source_hash_mismatch",
            "reason": "committed v2 hashes did not match the consumer pins",
            "hash_errors": source_lock_row["hash_verification_errors"],
        }
    if computed == EXPECTED_PROFILES["s3_like"] and all(not values for values in total["homology"]["torsion"].values()):
        return {
            "status": "EARNED",
            "finding_kind": "second_independent_certificate",
            "computed_total_betti": computed,
            "computed_total_torsion": total["homology"]["torsion"],
            "expected_s3_like_betti": EXPECTED_PROFILES["s3_like"],
        }
    return {
        "status": "FAILED",
        "finding_kind": "computed_mismatch_against_cover_construction",
        "computed_total_betti": computed,
        "computed_total_torsion": total["homology"]["torsion"],
        "expected_s3_like_betti": EXPECTED_PROFILES["s3_like"],
        "expected_product_betti": EXPECTED_PROFILES["s2xs1_product"],
        "plain_result": "the committed v2 total-space complex computes as product-profile homology, not S3-like homology",
    }


def build_topology_parity_guard_v2_object() -> dict[str, Any]:
    v2 = load_v2_payload()
    reference_gate = run_reference_gate()
    controls = run_controls()
    source_lock_row, hash_errors = verify_pinned_complexes(v2)
    base_result = committed_complex_result("committed_v2_base", v2["cellular_base"])
    total_result = committed_complex_result("committed_v2_total_space", v2["total_space_cellular_structure"])
    zero_shift = {
        "status": "INSUFFICIENT",
        "gap": "v2_committed_zero_shift_chain_complex_not_emitted",
        "committed_control_available": "controls.zero_shift_v2_cover_regression",
        "available_committed_facts": {
            "cover_sha256": v2["controls"]["zero_shift_v2_cover_regression"]["cover_sha256"],
            "directed_winding": v2["controls"]["zero_shift_v2_cover_regression"]["bundle_witness"]["directed_winding"],
            "law_table_refused": v2["controls"]["zero_shift_v2_cover_regression"]["law_table_refused"],
        },
    }
    parity = adjudicate(total_result, reference_gate, source_lock_row)
    boundary_ok = builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    all_pass = bool(reference_gate["reference_gate_passed"] and not hash_errors and controls["torsion_trap_degree_2"]["pass"] and boundary_ok)
    return {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "generated_at": now_z(),
        "preregistration_order": "reference_gate_then_committed_hash_pinned_complexes_then_parity_adjudication",
        "expected_profiles_preregistered_from_math": {
            "s3_like_total_space": EXPECTED_PROFILES["s3_like"],
            "zero_shift_product_s2xs1": EXPECTED_PROFILES["s2xs1_product"],
            "source": "carried unchanged from topology parity v0/v1 profiles",
        },
        "source_complex_lock": source_lock_row,
        "reference_gate": reference_gate,
        "complexes": {
            "committed_v2_base": base_result,
            "committed_v2_total_space": total_result,
            "zero_shift_product_cover": zero_shift,
        },
        "controls": controls,
        "parity_adjudication": parity,
        "allowed_claims": [
            "scratch-diagnostic consumer homology of committed fiber_augmented_cover_v2 chain complexes",
            "torsion-aware integer homology computation from pinned boundary matrices",
            "parity adjudication against carried pre-registered profiles",
        ],
        "disallowed_claims": [
            "new construction",
            "new cell introduction",
            "formal admission",
            "canonical by process",
            "axis closure",
            "bridge claim",
            "physics/manifold claim",
            "audit replacement",
            "builder Betti citation",
        ],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": {
            "g2a_boundary_from_birth": boundary_ok,
            "boundary_helper_path": rel(SIM_DIR / "topology_parity_guard_v2_boundary.py"),
            "shared_boundary_helper": rel(SCRIPTS_DIR / "builder_audit_boundary.py"),
            "no_git_add_or_commit_required": True,
            "no_new_cells_introduced": True,
            "consumer_only": True,
        },
        "all_pass": all_pass,
        "result_summary": {
            "reference_gate_passed": reference_gate["reference_gate_passed"],
            "hash_verification_passed": source_lock_row["hash_verification_passed"],
            "computed_total_betti": total_result["homology"]["betti_b0_b1_b2_b3"],
            "computed_total_torsion": total_result["homology"]["torsion"],
            "parity_status": parity["status"],
            "claim_ceiling": CLAIM_CEILING,
        },
    }


def write_result() -> dict[str, Any]:
    payload = build_topology_parity_guard_v2_object()
    write_json(RESULT_PATH, payload)
    return payload


def write_envelope_result() -> dict[str, Any]:
    payload = build_topology_parity_guard_v2_object()
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
        "parity_adjudication": payload["parity_adjudication"],
        "boundary_matrix_hashes": {
            "base": payload["source_complex_lock"]["base"]["boundary_hashes"],
            "total": payload["source_complex_lock"]["total"]["boundary_hashes"],
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "builder_gates": payload["builder_gates"],
    }
    write_json(ENVELOPE_RESULT_PATH, envelope)
    return envelope
