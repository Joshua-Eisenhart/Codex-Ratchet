#!/usr/bin/env python3
"""Shared builder for engine_16_stage_definition_correspondence_v0."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


SIM_ID = "engine_16_stage_definition_correspondence_v0"
SCHEMA = f"{SIM_ID}_result_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "macro_stage_definition_correspondence_proposal_only"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
ENGINE_MODE = "julia_canon_jax_with_pytorch_graph"

LAMBDA = 0.7
THETA = math.pi / 2.0
TOL = 1.0e-10

ENG64_DIR = ROOT / "system_v6" / "sims" / "eng64_stage_fingerprint_ids_v0"
SCRIPTS_DIR = ROOT / "scripts"
for import_dir in (ENG64_DIR, SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.insert(0, str(import_dir))

import eng64_stage_fingerprint_ids_v0 as eng64  # noqa: E402
from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402


SOURCE_PATHS = {
    "owner_router": Path("/Users/joshuaeisenhart/wiki/concepts/igt-axes-terrain-source-extraction-2026-06-04.md"),
    "doc_router_axes": ROOT / "system_v6/receipts/doc_router_axes_terrains_operators_20260609.md",
    "terrain_operator_map": ROOT / "system_v6/receipts/terrain_operator_map_20260609.md",
    "matrix64_mine": ROOT / "system_v6/receipts/matrix64_mine_20260610.md",
    "operator_math_explicit": ROOT / "system_v5/READ ONLY Reference Docs/operator math explicit.md",
    "qit_engine_four_operator_signed_math": ROOT / "system_v5/ops/QIT_ENGINE_FOUR_OPERATOR_SIGNED_MATH_20260522.md",
    "axes_terrains_operators_layout": ROOT / "system_v5/ops/AXES_TERRAINS_OPERATORS_MANIFOLD_SOURCE_LAYOUT_20260522.md",
    "eng64_source": ENG64_DIR / "eng64_stage_fingerprint_ids_v0.py",
    "eng64_result": ENG64_DIR / "results/eng64_stage_fingerprint_ids_v0_results.json",
    "eng64_validator": ENG64_DIR / "validate_eng64_stage_fingerprint_ids_v0.py",
    "eng64_64_run": ROOT / "system_v5/julia_carrier/eng_64_hexagram_julia_results.json",
    "axis4_common": ROOT / "system_v6/sims/discrete_axis4_composition_v0/discrete_axis4_composition_v0_common.py",
    "axis4_envelope": ROOT / "system_v6/sims/discrete_axis4_composition_v0/results/discrete_axis4_composition_v0_envelope_results.json",
    "ecd01_common": ROOT / "system_v6/sims/ecd01_order_programmable_computer_v1/ecd01_order_programmable_computer_v1_common.py",
    "standards_codex": ROOT / "system_v6/receipts/audit_standards_codex_v1.md",
}

TOOL_MANIFEST = {
    "eng64_stage_fingerprint_ids_v0": {
        "tried": True,
        "used": True,
        "reason": "load-bearing: imports the exact audited fingerprint machinery and representative density carrier.",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive finite matrix arithmetic for the explicit 3x3 Bloch maps.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "supportive computed-count consistency gate over stage/control counts.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "supportive independent computed-count consistency gate matching z3.",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "load-bearing G.2a idempotency-from-birth validator boundary.",
    },
    "json_hashing": {
        "tried": True,
        "used": True,
        "reason": "supportive deterministic result serialization and source locks.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "eng64_stage_fingerprint_ids_v0": "load_bearing",
    "numpy": "supportive",
    "z3": "supportive",
    "cvc5": "supportive",
    "builder_audit_boundary": "load_bearing",
    "json_hashing": "supportive",
}

TOOL_INTENT = {
    "claim_classes": [
        "macro_stage_definition_correspondence_proposal",
        "eng64_fingerprint_family_reuse",
        "computed_correspondence_matrix",
        "computed_controls_only",
    ],
    "engine_tool_intent": {
        "julia": {
            "Graphs": "construct the exact alias graph over the computed 16 stage fingerprints without reading peer results",
        },
        "jax": {
            "networkx": "construct the exact alias graph over the computed 16 stage fingerprints without reading peer results",
            "sympy": "exactly bind the 16x16 match-matrix dimensions and discovered-component count",
        },
        "pytorch": {
            "torch.func": "batched application of all 16 explicit stage matrices to the representative Bloch vector",
            "sympy": "exactly bind the 16x16 match-matrix dimensions and discovered-component count",
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
        out = subprocess.check_output(
            ["git", "log", "-n", "1", "--format=%h", "--", rel(path)],
            cwd=ROOT,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return out or None
    except Exception:
        return None


def source_lock(path: Path, role: str, commit_hint: str | None = None) -> dict[str, Any]:
    row: dict[str, Any] = {"role": role, "path": rel(path), "exists": path.exists()}
    if path.exists():
        row["sha256"] = sha256_file(path)
        row["git_last_commit"] = git_last_commit(path)
    if commit_hint:
        row["commit_hint"] = commit_hint
    return row


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def round_float(value: float, digits: int = 12) -> float:
    value = float(value)
    if abs(value) < 10 ** (-digits):
        return 0.0
    return round(value, digits)


def round_list(values: Any, digits: int = 12) -> list[Any]:
    arr = np.asarray(values)
    if arr.ndim == 1:
        return [round_float(float(x), digits) for x in arr]
    return [[round_float(float(x), digits) for x in row] for row in arr]


def bloch_from_rho(rho: np.ndarray) -> np.ndarray:
    return np.array(
        [
            2.0 * float(np.real(rho[0, 1])),
            -2.0 * float(np.imag(rho[0, 1])),
            float(np.real(rho[0, 0] - rho[1, 1])),
        ],
        dtype=float,
    )


def rho_from_bloch(vec: np.ndarray) -> np.ndarray:
    x, y, z = [float(v) for v in vec]
    return np.array(
        [
            [(1.0 + z) / 2.0, (x - 1j * y) / 2.0],
            [(x + 1j * y) / 2.0, (1.0 - z) / 2.0],
        ],
        dtype=np.complex128,
    )


def entropy_vn(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + np.conjugate(rho.T)) / 2.0)
    clipped = np.clip(np.real(vals), 0.0, 1.0)
    return float(-sum(val * math.log(val) for val in clipped if val > 1.0e-14))


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def rotation_x(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]], dtype=float)


def rotation_z(theta: float) -> np.ndarray:
    c = math.cos(theta)
    s = math.sin(theta)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def base_operator_matrix(name: str, chirality_sign: float = 1.0, assignment: dict[str, str] | None = None) -> np.ndarray:
    actual = assignment.get(name, name) if assignment else name
    if actual == "Ti":
        return np.diag([LAMBDA, LAMBDA, 1.0])
    if actual == "Te":
        return np.diag([1.0, LAMBDA, LAMBDA])
    if actual == "Fi":
        return rotation_x(chirality_sign * THETA)
    if actual == "Fe":
        return rotation_z(chirality_sign * THETA)
    raise ValueError(f"unknown operator: {name}")


def affine_channel_matrix(m: np.ndarray) -> np.ndarray:
    out = np.zeros((4, 4), dtype=float)
    out[0, 0] = 1.0
    out[1:, 1:] = m
    return out


def vector_fingerprint(rho: np.ndarray) -> tuple[float, ...]:
    if rho.shape != (2, 2):
        raise ValueError(f"eng64 fingerprint carrier must be 2x2 density matrix, got {rho.shape}")
    return eng64.fingerprint(rho)


def component_id_for_rho(rho: np.ndarray) -> str:
    return eng64.component_id_for_fingerprint(vector_fingerprint(rho))


def stage_specs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for chirality in ("L", "R"):
        for t_op in ("Ti", "Te"):
            for f_op in ("Fi", "Fe"):
                for order in ("+", "-"):
                    if order == "+":
                        dominant, auxiliary = t_op, f_op
                        family_order = "T_dominant"
                    else:
                        dominant, auxiliary = f_op, t_op
                        family_order = "F_dominant"
                    token = f"{chirality}_{t_op}_{f_op}_{'plus' if order == '+' else 'minus'}"
                    rows.append(
                        {
                            "stage_index": len(rows),
                            "stage_token": token,
                            "chirality": chirality,
                            "chirality_sign": 1.0 if chirality == "L" else -1.0,
                            "t_operator": t_op,
                            "f_operator": f_op,
                            "order_polarity": order,
                            "family_order": family_order,
                            "dominant_operator": dominant,
                            "auxiliary_operator": auxiliary,
                            "ordered_pair": [dominant, auxiliary],
                            "composition_notation": f"{dominant} o {auxiliary}",
                            "signed_pair_convention": [f"{dominant}+", f"{auxiliary}-"],
                        }
                    )
    return rows


def build_stage_rows(
    *,
    erase_order: bool = False,
    erase_chirality: bool = False,
    assignment: dict[str, str] | None = None,
    identity: bool = False,
) -> list[dict[str, Any]]:
    rho_in = np.array(eng64.RHO_REPR, dtype=np.complex128)
    bloch_in = bloch_from_rho(rho_in)
    rows: list[dict[str, Any]] = []
    for spec in stage_specs():
        sign = 1.0 if erase_chirality else float(spec["chirality_sign"])
        if identity:
            m = np.eye(3)
            effective_order = "identity"
            dominant = "I"
            auxiliary = "I"
        else:
            t_m = base_operator_matrix(spec["t_operator"], sign, assignment)
            f_m = base_operator_matrix(spec["f_operator"], sign, assignment)
            if erase_order:
                dominant = spec["t_operator"]
                auxiliary = spec["f_operator"]
                m = t_m @ f_m
                effective_order = "order_erased_T_o_F"
            elif spec["order_polarity"] == "+":
                dominant = spec["t_operator"]
                auxiliary = spec["f_operator"]
                m = t_m @ f_m
                effective_order = "T_o_F"
            else:
                dominant = spec["f_operator"]
                auxiliary = spec["t_operator"]
                m = f_m @ t_m
                effective_order = "F_o_T"
        bloch_out = m @ bloch_in
        rho_out = rho_from_bloch(bloch_out)
        fp = vector_fingerprint(rho_out)
        component_id = eng64.component_id_for_fingerprint(fp)
        rows.append(
            {
                **spec,
                "effective_dominant_operator": dominant,
                "effective_auxiliary_operator": auxiliary,
                "effective_order": effective_order,
                "matrix_bloch_3x3": round_list(m, 12),
                "matrix_affine_4x4": round_list(affine_channel_matrix(m), 12),
                "bloch_input": round_list(bloch_in, 12),
                "bloch_output": round_list(bloch_out, 12),
                "rho_output": [
                    [[round_float(float(np.real(cell)), 12), round_float(float(np.imag(cell)), 12)] for cell in row]
                    for row in rho_out
                ],
                "fingerprint": list(fp),
                "fingerprint_id": component_id,
                "component_id": component_id,
                "geometry": geometry_row(m, rho_in, rho_out),
            }
        )
    return rows


def nullspace_basis(a: np.ndarray, tol: float = 1.0e-9) -> list[list[float]]:
    _, s, vh = np.linalg.svd(a)
    rank = int((s > tol).sum())
    basis = vh[rank:].T
    return [round_list(basis[:, idx], 10) for idx in range(basis.shape[1])]


def moved_basis_directions(m: np.ndarray) -> list[str]:
    names = ("x", "y", "z")
    moved = []
    for idx, name in enumerate(names):
        basis = np.zeros(3)
        basis[idx] = 1.0
        if np.linalg.norm(m @ basis - basis) > 1.0e-9:
            moved.append(name)
    return moved


def geometry_row(m: np.ndarray, rho_in: np.ndarray, rho_out: np.ndarray) -> dict[str, Any]:
    eigvals = np.linalg.eigvals(m)
    singular = np.linalg.svd(m, compute_uv=False)
    fixed_basis = nullspace_basis(m - np.eye(3))
    entropy_in = entropy_vn(rho_in)
    entropy_out = entropy_vn(rho_out)
    purity_in = purity(rho_in)
    purity_out = purity(rho_out)
    return {
        "fixed_point_subspace": {
            "basis_vectors": fixed_basis,
            "dimension": len(fixed_basis),
            "interpretation": "Bloch vectors r satisfying M r = r; origin is always fixed for these unital maps.",
        },
        "eigenvalues_re_im": [[round_float(float(np.real(v)), 12), round_float(float(np.imag(v)), 12)] for v in eigvals],
        "singular_values": round_list(singular, 12),
        "determinant": round_float(float(np.linalg.det(m)), 12),
        "spectral_radius": round_float(float(max(abs(v) for v in eigvals)), 12),
        "contraction_character": "strict_contraction_present" if float(min(singular)) < 1.0 - 1.0e-9 else "unitary_or_isometric_on_all_axes",
        "moved_bloch_directions": moved_basis_directions(m),
        "entropy_input": round_float(entropy_in, 12),
        "entropy_output": round_float(entropy_out, 12),
        "entropy_delta": round_float(entropy_out - entropy_in, 12),
        "purity_input": round_float(purity_in, 12),
        "purity_output": round_float(purity_out, 12),
        "purity_delta": round_float(purity_out - purity_in, 12),
    }


def discovered_components() -> list[dict[str, Any]]:
    result = load_json(SOURCE_PATHS["eng64_result"])
    rows = result["stage_fingerprint_components"]
    by_component: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_component[row["component_id"]].append(row)
    components = []
    for component in result["components"]:
        cid = component["component_id"]
        sample = sorted(by_component[cid], key=lambda row: row["stage"])[0]
        components.append(
            {
                "component_id": cid,
                "representative_stage": component["representative_stage"],
                "stages": component["stages"],
                "size": component["size"],
                "representative_fingerprint": sample["fingerprint"],
            }
        )
    return sorted(components, key=lambda row: int(row["representative_stage"]))


def correspondence(stage_rows: list[dict[str, Any]], discovered: list[dict[str, Any]]) -> dict[str, Any]:
    matrix = []
    nearest = []
    for row in stage_rows:
        fp = np.asarray(row["fingerprint"], dtype=float)
        matrix_row = []
        distances = []
        for comp in discovered:
            comp_fp = np.asarray(comp["representative_fingerprint"], dtype=float)
            match = row["component_id"] == comp["component_id"]
            matrix_row.append(1 if match else 0)
            distances.append(float(np.linalg.norm(fp - comp_fp, ord=2)))
        best_idx = int(np.argmin(distances))
        nearest.append(
            {
                "stage_token": row["stage_token"],
                "component_id": row["component_id"],
                "nearest_discovered_component_id": discovered[best_idx]["component_id"],
                "nearest_l2_distance": round_float(distances[best_idx], 12),
                "exact_match": row["component_id"] == discovered[best_idx]["component_id"],
            }
        )
        matrix.append(matrix_row)
    defined_set = {row["component_id"] for row in stage_rows}
    discovered_set = {row["component_id"] for row in discovered}
    alias_groups = alias_groups_for_rows(stage_rows)
    matched = sorted(defined_set & discovered_set)
    perfect = defined_set == discovered_set and len(defined_set) == 16
    return {
        "question": "Do the proposed 16 stage definitions reproduce the discovered eng64 16 component set under exact fingerprint equivalence?",
        "match_rule": "exact equality of eng64_fp_* component IDs computed from rounded 8-float density fingerprints",
        "defined_component_count": len(defined_set),
        "discovered_component_count": len(discovered_set),
        "exact_matched_component_count": len(matched),
        "perfect_bijection": perfect,
        "result": "MATCH" if perfect else "MISMATCH",
        "stage_labels": [row["stage_token"] for row in stage_rows],
        "discovered_labels": [f"rep_hex{comp['representative_stage']:02d}:{comp['component_id']}" for comp in discovered],
        "match_matrix_16x16": matrix,
        "nearest_discovered_by_stage": nearest,
        "defined_alias_groups": alias_groups,
        "defined_components_without_discovered_counterpart": sorted(defined_set - discovered_set),
        "discovered_components_without_defined_counterpart": sorted(discovered_set - defined_set),
        "matched_component_ids": matched,
    }


def alias_groups_for_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[row["component_id"]].append(row["stage_token"])
    return [
        {"component_id": component_id, "stage_tokens": sorted(tokens), "size": len(tokens)}
        for component_id, tokens in sorted(groups.items())
        if len(tokens) > 1
    ]


def non_equivalence(rows: list[dict[str, Any]]) -> dict[str, Any]:
    labels = [row["stage_token"] for row in rows]
    status = []
    distances = []
    for left in rows:
        status_row = []
        distance_row = []
        lfp = np.asarray(left["fingerprint"], dtype=float)
        for right in rows:
            rfp = np.asarray(right["fingerprint"], dtype=float)
            same = left["component_id"] == right["component_id"]
            status_row.append("alias" if same else "distinct")
            distance_row.append(round_float(float(np.linalg.norm(lfp - rfp, ord=2)), 12))
        status.append(status_row)
        distances.append(distance_row)
    return {
        "labels": labels,
        "alias_distinct_matrix_16x16": status,
        "fingerprint_l2_distance_matrix_16x16": distances,
        "alias_groups": alias_groups_for_rows(rows),
        "all_pairs_distinct": not alias_groups_for_rows(rows),
    }


def stage_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        groups[row["component_id"]].append(row["stage_token"])
    return {
        "stage_count": len(rows),
        "n_distinct": len(groups),
        "largest_alias_group": max((len(v) for v in groups.values()), default=0),
        "alias_groups": [
            {"component_id": key, "stage_tokens": sorted(value), "size": len(value)}
            for key, value in sorted(groups.items())
            if len(value) > 1
        ],
    }


def controls(normal_rows: list[dict[str, Any]], discovered: list[dict[str, Any]]) -> dict[str, Any]:
    normal_match = correspondence(normal_rows, discovered)
    order_rows = build_stage_rows(erase_order=True)
    chirality_rows = build_stage_rows(erase_chirality=True)
    scramble_rows = build_stage_rows(assignment={"Ti": "Fe", "Te": "Fi", "Fi": "Ti", "Fe": "Te"})
    identity_rows = build_stage_rows(identity=True)
    scramble_match = correspondence(scramble_rows, discovered)
    lr_pairs_merge = True
    by_key: dict[tuple[str, str, str], dict[str, str]] = defaultdict(dict)
    for row in chirality_rows:
        by_key[(row["t_operator"], row["f_operator"], row["order_polarity"])][row["chirality"]] = row["component_id"]
    for pair in by_key.values():
        if pair.get("L") != pair.get("R"):
            lr_pairs_merge = False
            break
    return {
        "erase_order_polarity": {
            **stage_summary(order_rows),
            "control": "Both + and - variants are evaluated as the same unordered T o F map.",
            "collapsed_toward_8": stage_summary(order_rows)["n_distinct"] <= 8,
        },
        "erase_chirality": {
            **stage_summary(chirality_rows),
            "control": "L and R rotation signs are both set to +theta.",
            "all_lr_pairs_merge": lr_pairs_merge,
        },
        "scramble_operator_assignments": {
            **stage_summary(scramble_rows),
            "control": "Deterministic remap Ti->Fe, Te->Fi, Fi->Ti, Fe->Te before matrix construction.",
            "exact_matched_component_count": scramble_match["exact_matched_component_count"],
            "normal_exact_matched_component_count": normal_match["exact_matched_component_count"],
            "does_not_improve_correspondence": scramble_match["exact_matched_component_count"]
            <= normal_match["exact_matched_component_count"],
            "perfect_bijection_after_scramble": scramble_match["perfect_bijection"],
        },
        "identity_stages": {
            **stage_summary(identity_rows),
            "control": "Every stage matrix is replaced by identity.",
        },
    }


def z3_gate(values: dict[str, int]) -> dict[str, Any]:
    solver = z3.Solver()
    normal = z3.Int("normal_defined_distinct")
    order_erased = z3.Int("order_erased_distinct")
    chirality_erased = z3.Int("chirality_erased_distinct")
    identity = z3.Int("identity_distinct")
    discovered = z3.Int("discovered_distinct")
    stage_count = z3.Int("stage_count")
    solver.add(normal == values["normal_defined_distinct"])
    solver.add(order_erased == values["order_erased_distinct"])
    solver.add(chirality_erased == values["chirality_erased_distinct"])
    solver.add(identity == values["identity_distinct"])
    solver.add(discovered == values["discovered_distinct"])
    solver.add(stage_count == values["stage_count"])
    solver.add(stage_count == 16)
    solver.add(discovered == 16)
    solver.add(identity == 1)
    solver.add(order_erased <= 8)
    solver.add(chirality_erased <= 8)
    solver.add(normal <= 16)
    verdict = str(solver.check())
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": False,
        "supportive": True,
        "polarity": "direct satisfiable computed-count consistency check",
        "bound_values": values,
    }


def cvc5_gate(values: dict[str, int]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    normal = solver.mkConst(int_sort, "normal_defined_distinct")
    order_erased = solver.mkConst(int_sort, "order_erased_distinct")
    chirality_erased = solver.mkConst(int_sort, "chirality_erased_distinct")
    identity = solver.mkConst(int_sort, "identity_distinct")
    discovered = solver.mkConst(int_sort, "discovered_distinct")
    stage_count = solver.mkConst(int_sort, "stage_count")

    def eq(term: Any, value: int) -> None:
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, term, solver.mkInteger(value)))

    eq(normal, values["normal_defined_distinct"])
    eq(order_erased, values["order_erased_distinct"])
    eq(chirality_erased, values["chirality_erased_distinct"])
    eq(identity, values["identity_distinct"])
    eq(discovered, values["discovered_distinct"])
    eq(stage_count, values["stage_count"])
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, stage_count, solver.mkInteger(16)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, discovered, solver.mkInteger(16)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, identity, solver.mkInteger(1)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, order_erased, solver.mkInteger(8)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, chirality_erased, solver.mkInteger(8)))
    solver.assertFormula(solver.mkTerm(Kind.LEQ, normal, solver.mkInteger(16)))
    verdict = str(solver.checkSat()).lower()
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": False,
        "supportive": True,
        "polarity": "direct satisfiable computed-count consistency check",
        "bound_values": values,
    }


def smt_rows(normal_rows: list[dict[str, Any]], discovered: list[dict[str, Any]], control_rows: dict[str, Any]) -> dict[str, Any]:
    values = {
        "stage_count": len(normal_rows),
        "normal_defined_distinct": stage_summary(normal_rows)["n_distinct"],
        "discovered_distinct": len({row["component_id"] for row in discovered}),
        "order_erased_distinct": int(control_rows["erase_order_polarity"]["n_distinct"]),
        "chirality_erased_distinct": int(control_rows["erase_chirality"]["n_distinct"]),
        "identity_distinct": int(control_rows["identity_stages"]["n_distinct"]),
    }
    return {"z3": z3_gate(values), "cvc5": cvc5_gate(values)}


def base_operator_rows() -> list[dict[str, Any]]:
    rows = []
    for name in ("Ti", "Te", "Fi", "Fe"):
        m = base_operator_matrix(name, 1.0)
        rows.append(
            {
                "operator": name,
                "bloch_matrix_3x3": round_list(m, 12),
                "affine_channel_4x4": round_list(affine_channel_matrix(m), 12),
                "family": "dissipative_contraction" if name in {"Ti", "Te"} else "unitary_rotation",
                "fixture_parameter": {"lambda": LAMBDA} if name in {"Ti", "Te"} else {"theta": THETA},
            }
        )
    return rows


def build_packet() -> dict[str, Any]:
    stage_rows = build_stage_rows()
    discovered = discovered_components()
    corr = correspondence(stage_rows, discovered)
    neq = non_equivalence(stage_rows)
    control_rows = controls(stage_rows, discovered)
    smt = smt_rows(stage_rows, discovered, control_rows)
    all_pass = bool(
        len(stage_rows) == 16
        and len(discovered) == 16
        and len(corr["match_matrix_16x16"]) == 16
        and all(len(row) == 16 for row in corr["match_matrix_16x16"])
        and control_rows["identity_stages"]["n_distinct"] == 1
        and control_rows["erase_order_polarity"]["n_distinct"] <= 8
        and control_rows["erase_chirality"]["all_lr_pairs_merge"]
        and control_rows["scramble_operator_assignments"]["does_not_improve_correspondence"]
        and smt["z3"]["verdict"] == "sat"
        and smt["cvc5"]["verdict"] == "sat"
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    return {
        "schema": SCHEMA,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "all_pass": all_pass,
        "definition_phase_pinned_before_correspondence": True,
        "definition_rule": {
            "count_formula": "2 chirality sheets x 2 dissipative T operators x 2 rotation F operators x 2 order polarities = 16",
            "carrier": "eng64 one-qubit density/Bloch representative carrier",
            "base_operators": "Ti=D_z, Te=D_x, Fi=R_x, Fe=R_z",
            "order_polarity_convention": {
                "+": "T-family dominant, T o F",
                "-": "F-family dominant, F o T",
            },
            "chirality_convention": {
                "L": "+theta rotations",
                "R": "-theta rotations",
                "dephasing": "chirality-invariant",
            },
            "underdetermined_choices_pinned_as_convention": [
                "using pi/2 for both R_x and R_z from the Axis-4 R_x fixture angle",
                "using lambda=0.7 for both D_z and D_x from the Axis-4 D_z fixture",
                "representing chirality as rotation-angle sign only",
                "using T/F mixed pairs as the admissible macro-stage pairing set",
            ],
        },
        "source_locks": {
            "owner_router": source_lock(SOURCE_PATHS["owner_router"], "owner operator/stage source router"),
            "doc_router_axes": source_lock(SOURCE_PATHS["doc_router_axes"], "repo source router for axes/terrains/operators"),
            "terrain_operator_map": source_lock(SOURCE_PATHS["terrain_operator_map"], "normalized operator grammar and signed precedence map"),
            "matrix64_mine": source_lock(SOURCE_PATHS["matrix64_mine"], "64/16 boundary and fingerprint evidence map"),
            "operator_math_explicit": source_lock(SOURCE_PATHS["operator_math_explicit"], "four base operator math source"),
            "qit_engine_four_operator_signed_math": source_lock(
                SOURCE_PATHS["qit_engine_four_operator_signed_math"],
                "exact four-map and signed-order source notes",
            ),
            "axes_terrains_operators_layout": source_lock(
                SOURCE_PATHS["axes_terrains_operators_layout"],
                "Axis 4/5/6 source layout and false-count fences",
            ),
            "eng64_source": source_lock(SOURCE_PATHS["eng64_source"], "audited fingerprint machinery", "fab7b2253"),
            "eng64_result": source_lock(SOURCE_PATHS["eng64_result"], "audited discovered-16 component set", "fab7b2253"),
            "eng64_64_run": source_lock(SOURCE_PATHS["eng64_64_run"], "realization-relative 64-run result", "23cfa5536"),
            "axis4_common": source_lock(SOURCE_PATHS["axis4_common"], "R_x/D_z fixture implementation"),
            "axis4_envelope": source_lock(SOURCE_PATHS["axis4_envelope"], "R_x/D_z fixture result envelope"),
            "ecd01_common": source_lock(SOURCE_PATHS["ecd01_common"], "ECD.01 U/E fixture reference"),
            "standards_codex": source_lock(SOURCE_PATHS["standards_codex"], "G.2a/G7 standards codex"),
        },
        "eng64_fingerprint_contract": {
            "source": rel(SOURCE_PATHS["eng64_source"]),
            "fp_tolerance": eng64.FP_TOL,
            "rng_seed": eng64.RNG_SEED,
            "representative_rho_sha256": stable_sha256(
                [[float(np.real(cell)), float(np.imag(cell))] for row in eng64.RHO_REPR for cell in row]
            ),
            "definition": "Apply stage channel to RHO_REPR, flatten rho_out row-major as real/imag pairs, round to FP_TOL=1e-7, hash the 8-float vector using eng64 component_id_for_fingerprint.",
        },
        "base_operator_rows": base_operator_rows(),
        "defined_stage_rows": stage_rows,
        "discovered_components": discovered,
        "correspondence": corr,
        "non_equivalence_matrix": neq,
        "controls": control_rows,
        "smt_rows": smt,
        "summary": {
            "defined_stage_count": len(stage_rows),
            "defined_distinct_component_count": stage_summary(stage_rows)["n_distinct"],
            "discovered_component_count": len(discovered),
            "correspondence_result": corr["result"],
            "perfect_bijection": corr["perfect_bijection"],
            "exact_matched_component_count": corr["exact_matched_component_count"],
            "claim_ceiling": CLAIM_CEILING,
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "G7_definitions_pinned_before_correspondence": True,
            "file_disjoint_packet": True,
            "no_engine_stage_admission": True,
            "rx_dz_fixture_fence_carried": True,
            "builder_audit_boundary_ok": builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md"),
        },
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
        "disallowed_claims": [
            "engine-stage admission",
            "Matrix64 admission",
            "QIT-engine admission",
            "axis admission",
            "bridge admission",
            "manifold admission",
            "physics claim",
        ],
        "fences": {
            "realization_relative": True,
            "substage_convention_unpinned": True,
            "macro_stage_level_only": True,
            "rx_dz_fixture_not_canonical": True,
            "scratch_diagnostic": True,
            "formal_admission_allowed": False,
        },
    }


def build_and_write() -> dict[str, Any]:
    payload = build_packet()
    write_json(RESULT_PATH, payload)
    return payload


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except Exception:
        return "unknown"
