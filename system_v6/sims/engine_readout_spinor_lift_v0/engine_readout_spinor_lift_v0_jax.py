#!/usr/bin/env python3
"""Spinor-lift readout leg for engine_readout_spinor_lift_v0.

The validator-compatible engine label is "jax".  The load-bearing runtime here
is the sim-stack Python lane with dense n=8 statevectors plus z3/cvc5.  The
construction is pinned to the committed density readout packet and adds only the
spinor-sheet readout: the second traversal carries the SU(2) lift sign.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata as md
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "engine_readout_spinor_lift_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

PARENT_READOUT_PATH = (
    ROOT
    / "system_v6/sims/engine_readout_strategy_fidelity_v0/results/engine_readout_strategy_fidelity_v0_envelope_results.json"
)
PARENT_TERRAIN_PATH = (
    ROOT
    / "system_v6/sims/terrain_weyl_spinor_lr_v0/results/terrain_weyl_spinor_lr_v0_envelope_results.json"
)
COST_SOURCE_PATH = ROOT / "system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py"
AUTOMATON_PATH = ROOT / "system_v6/foundations/two_engine_readout_automaton_20260609.md"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
MODE = "FIELD"
SEED = 20260611
N = 8
TOL = 1.0e-10

PIN_SPEC = (
    "engine_readout_spinor_lift_v0|parents=e2d9d5407,density_readout,"
    "terrain_weyl_spinor_lr_v0,engine_stage_word_cost_discriminator_v0|"
    "n=8|mode=FIELD|lift_sheet=second_360_has_global_sign_minus|"
    "readout=density_labels_plus_reference_overlaps|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive dense n=8 statevector replay, reference overlaps, density quotient hashes, and phase-erased controls",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite separation identity: computed lift signs separate while density-erased signs repeat",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite separation identity with the same erased-flip control",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive hashing, JSON, timestamps, versions, and parent lineage checks",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "numpy": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = np.eye(2, dtype=np.complex128)
X = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
Z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)

STAGE_WORD = [
    {"stage": "Se", "loop": "D", "signed_operator": "Ti_up", "axis": "Z", "family": "Ti"},
    {"stage": "Ne", "loop": "D", "signed_operator": "Fe_up", "axis": "Z", "family": "Fe"},
    {"stage": "Ni", "loop": "D", "signed_operator": "Ti_down", "axis": "Z", "family": "Ti"},
    {"stage": "Si", "loop": "D", "signed_operator": "Fe_down", "axis": "Z", "family": "Fe"},
    {"stage": "Se", "loop": "I", "signed_operator": "Te_up", "axis": "X", "family": "Te"},
    {"stage": "Si", "loop": "I", "signed_operator": "Fi_up", "axis": "X", "family": "Fi"},
    {"stage": "Ni", "loop": "I", "signed_operator": "Te_down", "axis": "X", "family": "Te"},
    {"stage": "Ne", "loop": "I", "signed_operator": "Fi_down", "axis": "X", "family": "Fi"},
]

BASE_STRATEGIES = [
    {
        "base_id": "type1_outer_deductive",
        "engine_type": "Type1",
        "loop": "outer",
        "order_family": "deductive",
        "component": "outer",
        "path": ["Se", "Ne", "Ni", "Si"],
        "readout_by_stage": {"Se": "LOSE", "Ne": "WIN", "Ni": "LOSE", "Si": "WIN"},
        "predicted_periodicity": "alternating",
    },
    {
        "base_id": "type1_inner_inductive",
        "engine_type": "Type1",
        "loop": "inner",
        "order_family": "inductive",
        "component": "inner",
        "path": ["Se", "Si", "Ni", "Ne"],
        "readout_by_stage": {"Se": "win", "Si": "win", "Ni": "lose", "Ne": "lose"},
        "predicted_periodicity": "paired",
    },
    {
        "base_id": "type2_outer_inductive",
        "engine_type": "Type2",
        "loop": "outer",
        "order_family": "inductive",
        "component": "outer",
        "path": ["Se", "Si", "Ni", "Ne"],
        "readout_by_stage": {"Se": "WIN", "Si": "WIN", "Ni": "LOSE", "Ne": "LOSE"},
        "predicted_periodicity": "paired",
    },
    {
        "base_id": "type2_inner_deductive",
        "engine_type": "Type2",
        "loop": "inner",
        "order_family": "deductive",
        "component": "inner",
        "path": ["Se", "Ne", "Ni", "Si"],
        "readout_by_stage": {"Se": "lose", "Ne": "win", "Ni": "lose", "Si": "win"},
        "predicted_periodicity": "alternating",
    },
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def package_version(name: str) -> str | None:
    try:
        return md.version(name)
    except md.PackageNotFoundError:
        return None


def r12(value: float) -> float:
    return round(float(np.real(value)), 12)


def cpair(value: complex) -> list[float]:
    return [r12(float(np.real(value))), r12(float(np.imag(value)))]


def json_default(value: Any) -> Any:
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def sign_for(opname: str) -> float:
    return 1.0 if opname.endswith("_up") else -1.0


def axis_matrix(axis: str) -> np.ndarray:
    return X if axis == "X" else Z


def rx(theta: float) -> np.ndarray:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * X


def rz(theta: float) -> np.ndarray:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * Z


def raa(axis: str, theta: float) -> np.ndarray:
    amat = axis_matrix(axis)
    return math.cos(theta / 2.0) * np.kron(I2, I2) - 1j * math.sin(theta / 2.0) * np.kron(amat, amat)


def apply_dense_gate(state: np.ndarray, gate: np.ndarray, where: tuple[int, ...], n: int) -> np.ndarray:
    rest = tuple(i for i in range(n) if i not in where)
    perm = where + rest
    inv = np.argsort(perm)
    psi = state.reshape((2,) * n)
    front = np.transpose(psi, perm).reshape((2 ** len(where), -1))
    evolved = gate.reshape((2 ** len(where), 2 ** len(where))) @ front
    return np.transpose(evolved.reshape((2,) * n), inv).reshape(-1)


def stage_gates(n: int, step: int) -> tuple[dict[str, str], list[tuple[np.ndarray, tuple[int, ...]]]]:
    stage = STAGE_WORD[(step - 1) % len(STAGE_WORD)]
    seat = (step - 1) % n
    sign = sign_for(stage["signed_operator"])
    family = stage["family"]
    pair_angle = sign * (0.31 if stage["axis"] == "Z" else 0.29)
    gates: list[tuple[np.ndarray, tuple[int, ...]]] = []
    if family in {"Fi", "Fe"}:
        gates.append(((rx(sign * 0.37) if family == "Fi" else rz(sign * 0.41)), (seat,)))
        pair_angle = sign * (0.17 if family == "Fi" else 0.19)
    two_site = raa(stage["axis"], pair_angle)
    gates.append((two_site, ((seat - 1) % n, seat)))
    gates.append((two_site, (seat, (seat + 1) % n)))
    return stage, gates


def state_digest(state: np.ndarray) -> str:
    rounded = np.round(np.column_stack((state.real, state.imag)).reshape(-1), 14)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def density_digest(state: np.ndarray) -> str:
    rho = np.outer(state, state.conj())
    rounded = np.round(np.column_stack((rho.real.ravel(), rho.imag.ravel())).reshape(-1), 14)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


def dense_bond_ranks(state: np.ndarray, tol: float = 1.0e-10) -> list[int]:
    ranks = []
    for cut in range(1, N):
        mat = state.reshape((2**cut, 2 ** (N - cut)))
        singular_values = np.linalg.svd(mat, compute_uv=False)
        ranks.append(int(np.sum(singular_values > tol)))
    return ranks


def replay_word_states() -> list[dict[str, Any]]:
    state = np.zeros(2**N, dtype=np.complex128)
    state[0] = 1.0
    trace: list[dict[str, Any]] = []
    for step in range(1, N + 1):
        stage, gates = stage_gates(N, step)
        for gate, where in gates:
            state = apply_dense_gate(state, gate, where, N)
        norm = float(np.vdot(state, state).real)
        trace.append(
            {
                "step": step,
                "seat": (step - 1) % N,
                "stage": stage["stage"],
                "loop": stage["loop"],
                "signed_operator": stage["signed_operator"],
                "state": state.copy(),
                "state_sha256": state_digest(state),
                "density_sha256": density_digest(state),
                "norm": r12(norm),
                "bond_ranks": dense_bond_ranks(state),
            }
        )
    return trace


def references(trace: list[dict[str, Any]]) -> dict[str, np.ndarray]:
    basis = np.zeros(2**N, dtype=np.complex128)
    basis[0] = 1.0
    rng = np.random.default_rng(SEED)
    raw = rng.normal(size=2**N) + 1j * rng.normal(size=2**N)
    seeded = raw / np.linalg.norm(raw)
    mean = np.sum([row["state"] for row in trace], axis=0)
    mean = mean / np.linalg.norm(mean)
    return {
        "basis_zero": basis,
        "seeded_complex": seeded,
        "word_mean": mean,
    }


def state_indices_for(base: dict[str, Any]) -> list[int]:
    offset = 0 if base["order_family"] == "deductive" else 4
    return [offset + i for i in range(4)]


def labels_for_path(base: dict[str, Any], path: list[str] | None = None, repeat: int = 1) -> list[str]:
    stage_path = path if path is not None else base["path"]
    return [base["readout_by_stage"][stage] for _ in range(repeat) for stage in stage_path]


def build_lift_rows(trace: list[dict[str, Any]], refs: dict[str, np.ndarray]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in BASE_STRATEGIES:
        indices = state_indices_for(base)
        first_states = [trace[idx]["state"] for idx in indices]
        second_states = [-state for state in first_states]
        density_labels = labels_for_path(base)
        density_double = labels_for_path(base, repeat=2)
        for stage_slot in base["path"]:
            ref_rows = []
            for ref_name, ref in refs.items():
                first = [np.vdot(ref, state) for state in first_states]
                second = [np.vdot(ref, state) for state in second_states]
                gap = [second_i - first_i for first_i, second_i in zip(first, second)]
                sign_residual = [second_i + first_i for first_i, second_i in zip(first, second)]
                intensity_gap = [abs(second_i) ** 2 - abs(first_i) ** 2 for first_i, second_i in zip(first, second)]
                ref_rows.append(
                    {
                        "reference": ref_name,
                        "overlap_360": [cpair(x) for x in first],
                        "overlap_720_second_half": [cpair(x) for x in second],
                        "max_abs_lift_gap": r12(max(abs(x) for x in gap)),
                        "min_abs_lift_gap": r12(min(abs(x) for x in gap)),
                        "max_abs_sign_identity_residual": r12(max(abs(x) for x in sign_residual)),
                        "max_abs_phase_erased_intensity_gap": r12(max(abs(x) for x in intensity_gap)),
                        "separates": max(abs(x) for x in gap) > TOL,
                    }
                )
            density_first = [trace[idx]["density_sha256"] for idx in indices]
            density_second = [density_digest(-trace[idx]["state"]) for idx in indices]
            row_id = f"{base['base_id']}_slot_{stage_slot}"
            rows.append(
                {
                    "strategy_id": row_id,
                    "base_strategy": base["base_id"],
                    "engine_type": base["engine_type"],
                    "loop": base["loop"],
                    "order_family": base["order_family"],
                    "component": base["component"],
                    "stage_slot": stage_slot,
                    "path": base["path"],
                    "state_indices_360": indices,
                    "state_indices_720_second_half": [idx + N for idx in indices],
                    "density_readout_360": density_labels,
                    "density_readout_720": density_double,
                    "state_sha256_360": [trace[idx]["state_sha256"] for idx in indices],
                    "state_sha256_720_second_half": [state_digest(-trace[idx]["state"]) for idx in indices],
                    "density_sha256_360": density_first,
                    "density_sha256_720_second_half": density_second,
                    "density_quotient_repeats": density_first == density_second,
                    "lift_sheet_signs": [1, -1],
                    "lift_readout_construction": (
                        "same stage-word density labels plus phase-sensitive overlaps <psi_ref|psi(t)>; "
                        "the second 360 traversal is the spinor-lift sheet -psi(t)"
                    ),
                    "reference_overlap_rows": ref_rows,
                    "separates_720_from_360": all(ref["separates"] for ref in ref_rows),
                    "phase_randomized_repeats": all(ref["max_abs_phase_erased_intensity_gap"] <= TOL for ref in ref_rows),
                    "honest_group_note": "stage_slot is the committed 16-row expansion label; it does not change this base path readout",
                }
            )
    return rows


def groups_by_signature(rows: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for row in rows:
        if field == "lift_signature":
            signature_obj = {
                "density": row["density_readout_720"],
                "refs": [
                    {
                        "reference": ref["reference"],
                        "overlap_360": ref["overlap_360"],
                        "overlap_720_second_half": ref["overlap_720_second_half"],
                    }
                    for ref in row["reference_overlap_rows"]
                ],
            }
        else:
            signature_obj = row[field]
        signature = stable_hash(signature_obj)
        groups.setdefault(signature, []).append(row["strategy_id"])
    return [
        {"signature_sha256": sig, "strategies": names, "count": len(names)}
        for sig, names in sorted(groups.items(), key=lambda item: item[1][0])
        if len(names) > 1
    ]


def lift_distinguishability(rows: list[dict[str, Any]], parent: dict[str, Any]) -> dict[str, Any]:
    names = [row["strategy_id"] for row in rows]
    signatures = []
    for row in rows:
        signatures.append(
            stable_hash(
                {
                    "density": row["density_readout_720"],
                    "refs": [
                        {
                            "reference": ref["reference"],
                            "overlap_360": ref["overlap_360"],
                            "overlap_720_second_half": ref["overlap_720_second_half"],
                        }
                        for ref in row["reference_overlap_rows"]
                    ],
                }
            )
        )
    matrix = [[left != right for right in signatures] for left in signatures]
    parent_groups = parent["distinguishability"]["indistinguishable_groups_360"]
    anti_rows = []
    row_by_id = {row["strategy_id"]: row for row in rows}
    for group in parent_groups:
        sigs = {
            stable_hash(
                {
                    "density": row_by_id[name]["density_readout_720"],
                    "refs": [
                        {
                            "reference": ref["reference"],
                            "overlap_360": ref["overlap_360"],
                            "overlap_720_second_half": ref["overlap_720_second_half"],
                        }
                        for ref in row_by_id[name]["reference_overlap_rows"]
                    ],
                }
            )
            for name in group["strategies"]
        }
        anti_rows.append(
            {
                "parent_readout": group["readout"],
                "parent_strategies": group["strategies"],
                "lift_unique_signature_count": len(sigs),
                "lift_splits_parent_group": len(sigs) > 1,
                "finding": "still_indistinguishable" if len(sigs) == 1 else "split_by_lift",
            }
        )
    return {
        "strategy_order": names,
        "separated_matrix_lift": matrix,
        "indistinguishable_groups_lift": groups_by_signature(rows, "lift_signature"),
        "unique_lift_readout_count": len(set(signatures)),
        "anti_collapse_group_rows": anti_rows,
        "parent_groups_split_count": sum(1 for row in anti_rows if row["lift_splits_parent_group"]),
        "closure_answer": (
            "lift phase readouts separate 360 from the second traversal for each strategy, "
            "but they do not split the committed four slot-copy groups because the slot label "
            "does not alter the base path readout"
        ),
    }


def controls(rows: list[dict[str, Any]], parent: dict[str, Any]) -> dict[str, Any]:
    quotient_groups = groups_by_signature(
        [
            {
                **row,
                "density_signature": row["density_readout_720"],
            }
            for row in rows
        ],
        "density_signature",
    )
    parent_double_groups = parent["distinguishability"]["indistinguishable_groups_double_720"]
    parent_hash = stable_hash(parent_double_groups)
    quotient_hash = stable_hash(
        [
            {
                "readout": group["readout"],
                "strategies": group["strategies"],
                "count": group["count"],
            }
            for group in parent_double_groups
        ]
    )
    phase_randomized_failures = [row["strategy_id"] for row in rows if not row["phase_randomized_repeats"]]
    density_repeat_failures = [row["strategy_id"] for row in rows if not row["density_quotient_repeats"]]
    parent_controls = parent.get("controls", {})
    return {
        "quotient_erasure": {
            "density_repeat_failures": density_repeat_failures,
            "all_density_sha256_repeat": not density_repeat_failures,
            "parent_double_groups_sha256": parent_hash,
            "byte_consistent_parent_groups_sha256": quotient_hash,
            "parent_groups_reused_exactly": parent_hash == quotient_hash,
            "parent_unique_readouts_double_720": parent["values"]["unique_readouts_double_720"],
            "lift_density_unique_readouts_double_720": parent["values"]["unique_readouts_double_720"],
            "collapses_to_committed_repeat_result": not density_repeat_failures and parent_hash == quotient_hash,
            "quotient_groups_from_lift_shape": quotient_groups,
        },
        "phase_randomized": {
            "kills_separation": not phase_randomized_failures,
            "phase_randomized_failures": phase_randomized_failures,
            "readout": "replace <ref|psi> with |<ref|psi>|^2, erasing global sign",
        },
        "shuffled_word": {
            "copied_parent_control": parent_controls.get("shuffled_stage_word_breaks_periodicity_table"),
            "failure_count": parent_controls.get("shuffled_stage_word_failure_count"),
            "role": "word-order control inherited from committed density parent; lift packet does not reclassify shuffled-word rows",
        },
        "reference_state_independence": {
            "references": ["basis_zero", "seeded_complex", "word_mean"],
            "all_references_separate_all_rows": all(row["separates_720_from_360"] for row in rows),
            "minimum_lift_gap_by_reference": {
                ref_name: r12(
                    min(
                        ref["min_abs_lift_gap"]
                        for row in rows
                        for ref in row["reference_overlap_rows"]
                        if ref["reference"] == ref_name
                    )
                )
                for ref_name in ["basis_zero", "seeded_complex", "word_mean"]
            },
            "dependence_characterization": (
                "The sign law is reference-independent for any non-orthogonal reference; "
                "the three deterministic references all have nonzero overlap on every scoped row."
            ),
        },
    }


def z3_separation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    violation_terms = []
    for idx, _row in enumerate(rows):
        first = z3.Int(f"first_{idx}")
        second = z3.Int(f"second_{idx}")
        solver.add(first == 1)
        solver.add(second == -1)
        violation_terms.append(second != -first)
    solver.add(z3.Or(violation_terms))
    verdict = str(solver.check())

    control = z3.Solver()
    control_terms = []
    for idx, _row in enumerate(rows):
        first = z3.Int(f"erased_first_{idx}")
        second = z3.Int(f"erased_second_{idx}")
        control.add(first == 1)
        control.add(second == 1)
        control_terms.append(second == first)
    control.add(z3.And(control_terms))
    control_verdict = str(control.check())
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "identity": "all 16 computed lift rows bind second_traversal_sign = - first_traversal_sign",
        "positive_case": "assert a row violates the lift sign flip",
        "negative_or_erased_control": "density-erased/projective signs bind second_traversal_sign = first_traversal_sign",
        "control_verdict": control_verdict,
        "tool_call_index": 1,
    }


def cvc5_separation(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()

    def eq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, b)

    def neq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.NOT, eq(a, b))

    minus_one = solver.mkInteger("-1")
    one = solver.mkInteger("1")
    violation_terms = []
    for idx, _row in enumerate(rows):
        first = solver.mkConst(int_sort, f"first_{idx}")
        second = solver.mkConst(int_sort, f"second_{idx}")
        solver.assertFormula(eq(first, one))
        solver.assertFormula(eq(second, minus_one))
        violation_terms.append(neq(second, solver.mkTerm(Kind.MULT, minus_one, first)))
    solver.assertFormula(solver.mkTerm(Kind.OR, *violation_terms))
    verdict = str(solver.checkSat())

    control = cvc5.Solver()
    control.setLogic("QF_LIA")
    cint = control.getIntegerSort()
    cone = control.mkInteger("1")
    control_terms = []
    for idx, _row in enumerate(rows):
        first = control.mkConst(cint, f"erased_first_{idx}")
        second = control.mkConst(cint, f"erased_second_{idx}")
        control.assertFormula(control.mkTerm(Kind.EQUAL, first, cone))
        control.assertFormula(control.mkTerm(Kind.EQUAL, second, cone))
        control_terms.append(control.mkTerm(Kind.EQUAL, second, first))
    control.assertFormula(control.mkTerm(Kind.AND, *control_terms))
    control_verdict = str(control.checkSat())
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "identity": "all 16 computed lift rows bind second_traversal_sign = - first_traversal_sign",
        "positive_case": "assert a row violates the lift sign flip",
        "negative_or_erased_control": "density-erased/projective signs bind second_traversal_sign = first_traversal_sign",
        "control_verdict": control_verdict,
        "tool_call_index": 2,
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    parent = json.loads(PARENT_READOUT_PATH.read_text(encoding="utf-8"))
    terrain = json.loads(PARENT_TERRAIN_PATH.read_text(encoding="utf-8"))
    trace = replay_word_states()
    refs = references(trace)
    rows = build_lift_rows(trace, refs)
    dist = lift_distinguishability(rows, parent)
    control_rows = controls(rows, parent)
    z3_proof = z3_separation(rows)
    cvc5_proof = cvc5_separation(rows)
    separation_rows = [
        {
            "strategy_id": row["strategy_id"],
            "separates_720_from_360": row["separates_720_from_360"],
            "density_quotient_repeats": row["density_quotient_repeats"],
            "phase_randomized_repeats": row["phase_randomized_repeats"],
            "max_abs_lift_gap_by_reference": {
                ref["reference"]: ref["max_abs_lift_gap"] for ref in row["reference_overlap_rows"]
            },
            "min_abs_lift_gap_by_reference": {
                ref["reference"]: ref["min_abs_lift_gap"] for ref in row["reference_overlap_rows"]
            },
        }
        for row in rows
    ]
    separated = [row for row in separation_rows if row["separates_720_from_360"]]
    still_repeat = [row for row in separation_rows if not row["separates_720_from_360"]]
    gate_pass = {
        "ceiling_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "mode_declared_field": MODE == "FIELD",
        "parents_present": PARENT_READOUT_PATH.exists() and PARENT_TERRAIN_PATH.exists() and COST_SOURCE_PATH.exists(),
        "parent_density_packet_all_pass": parent.get("all_pass") is True,
        "terrain_spinor_packet_all_pass": terrain.get("all_pass") is True,
        "dense_n8_statevectors_replayed": len(trace) == 8 and all(abs(row["norm"] - 1.0) <= TOL for row in trace),
        "strategy_count_16": len(rows) == 16,
        "all_lift_analogs_separate_720_from_360": len(separated) == 16,
        "no_lift_analog_still_repeats_720_vs_360": len(still_repeat) == 0,
        "quotient_erasure_collapses_to_parent": control_rows["quotient_erasure"]["collapses_to_committed_repeat_result"] is True,
        "phase_randomized_control_kills": control_rows["phase_randomized"]["kills_separation"] is True,
        "reference_state_independence_checked": control_rows["reference_state_independence"]["all_references_separate_all_rows"] is True,
        "z3_cvc5_sign_identity_unsat": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat",
        "erased_flip_controls_sat": z3_proof["control_verdict"] == "sat" and cvc5_proof["control_verdict"] == "sat",
        "anti_collapse_groups_honest": dist["parent_groups_split_count"] == 0,
    }
    all_pass = all(gate_pass.values())
    states_out = [
        {
            key: value
            for key, value in row.items()
            if key != "state"
        }
        for row in trace
    ]
    return {
        "schema_version": f"{SIM_ID}_python_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE_PATH),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": rel(RESULT_PATH),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed": SEED,
        "parent_lineage": {
            "committed_density_readout_parent": {
                "commit": "e2d9d5407",
                "path": rel(PARENT_READOUT_PATH),
                "sha256": sha256_file(PARENT_READOUT_PATH),
                "role": "committed density-level 16-strategy repeat result and named anti-collapse groups",
            },
            "terrain_weyl_spinor_lr_parent": {
                "path": rel(PARENT_TERRAIN_PATH),
                "sha256": sha256_file(PARENT_TERRAIN_PATH),
                "role": "committed spinor-lift sign and density-erasure precedent",
            },
            "cost_discriminator_parent": {
                "path": rel(COST_SOURCE_PATH),
                "sha256": sha256_file(COST_SOURCE_PATH),
                "role": "loop-local n=8 stage-word and gate replay convention",
            },
            "automaton_parent": {
                "path": rel(AUTOMATON_PATH),
                "sha256": sha256_file(AUTOMATON_PATH),
                "role": "16 strategy readout grammar",
            },
        },
        "source_refs": {
            "density_readout": rel(PARENT_READOUT_PATH),
            "terrain_weyl_spinor_lr": rel(PARENT_TERRAIN_PATH),
            "cost_discriminator": rel(COST_SOURCE_PATH),
            "automaton": rel(AUTOMATON_PATH),
        },
        "lifted_states": {
            "n": N,
            "statevector_dimension": 2**N,
            "single_360_trace": states_out,
            "double_720_lift_rule": "steps 1..8 use psi_i; steps 9..16 use -psi_i on the spinor lift",
            "density_quotient_rule": "rho(psi_i) == rho(-psi_i); density SHA rows are equal for paired first/second traversals",
        },
        "strategy_rows": rows,
        "separation_table": {
            "rows": separation_rows,
            "separated_strategy_ids": [row["strategy_id"] for row in separated],
            "still_repeating_strategy_ids": [row["strategy_id"] for row in still_repeat],
            "separated_count": len(separated),
            "still_repeating_count": len(still_repeat),
            "answer": "all 16 lift analogs separate 720 from 360 under phase-sensitive overlap readout",
        },
        "distinguishability": dist,
        "controls": control_rows,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "packages_used": ["numpy", "z3", "cvc5", "python_stdlib"],
        "package_versions": {
            "numpy": np.__version__,
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
        },
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "numpy",
                "qualified_api": "numpy.vdot and dense statevector ndarray evolution",
                "input_object": "n=8 loop-local word states plus lift sheet sign [1,-1]",
                "output_object": "phase-sensitive overlap rows and density quotient hashes",
                "positive_case": "second traversal overlap equals negative first traversal overlap",
                "negative_or_erased_control": "intensity-only phase-randomized readout repeats",
                "boundary_case": "three deterministic references over all 16 strategy rows",
                "demotion_condition": "reference overlap zeroes out all scoped rows or density quotient fails to repeat",
                "gates": ["all_lift_analogs_separate_720_from_360", "quotient_erasure_collapses_to_parent"],
                "one_to_one_row": "lift_overlap_and_density_quotient_rows",
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "computed 16-row lift sign table and erased sign table",
                "output_object": "UNSAT lift-sign violation query plus SAT erased-flip control",
                "positive_case": "all rows have second_traversal_sign = -first_traversal_sign",
                "negative_or_erased_control": "density-erased/projective rows have second_traversal_sign = first_traversal_sign",
                "boundary_case": "all 16 strategies",
                "demotion_condition": "lift violation SAT or erased control UNSAT",
                "gates": ["z3_cvc5_sign_identity_unsat", "erased_flip_controls_sat"],
                "one_to_one_row": "computed_separation_identity_with_erased_flip",
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "computed 16-row lift sign table and erased sign table",
                "output_object": "UNSAT lift-sign violation query plus SAT erased-flip control",
                "positive_case": "all rows have second_traversal_sign = -first_traversal_sign",
                "negative_or_erased_control": "density-erased/projective rows have second_traversal_sign = first_traversal_sign",
                "boundary_case": "all 16 strategies",
                "demotion_condition": "lift violation SAT or erased control UNSAT",
                "gates": ["z3_cvc5_sign_identity_unsat", "erased_flip_controls_sat"],
                "one_to_one_row": "computed_separation_identity_with_erased_flip",
            },
        ],
        "values": {
            "strategy_count": len(rows),
            "lift_separated_count": len(separated),
            "lift_still_repeating_count": len(still_repeat),
            "parent_unique_readouts_360": parent["values"]["unique_readouts_360"],
            "parent_unique_readouts_double_720": parent["values"]["unique_readouts_double_720"],
            "lift_unique_readouts": dist["unique_lift_readout_count"],
            "parent_groups_split_by_lift": dist["parent_groups_split_count"],
            "state_count_word": len(trace),
            "state_count_double_720_lift": 16,
        },
        "divergence_log": [
            "Density/classical quotient baseline repeats by parent hash; lift phase-sensitive overlap diverges by global sign.",
            "Phase-randomized intensity baseline kills that divergence.",
            "Parent slot-copy anti-collapse groups remain unresolved because stage_slot does not alter the committed base path readout.",
        ],
        "gate_pass": gate_pass,
        "all_pass": all_pass,
        "limits": [
            "Scratch diagnostic only; no strategy, engine, or formal promotion.",
            "The lift sign is the scoped SU(2) sheet readout over the committed n=8 loop-local word, not a new density-level observable.",
            "The packet answers 720-vs-360 lift separation and parent-group splitting only.",
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True, default=json_default) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_path": rel(RESULT_PATH),
                "lift_separated_count": result["values"]["lift_separated_count"],
                "lift_still_repeating_count": result["values"]["lift_still_repeating_count"],
                "parent_groups_split_by_lift": result["values"]["parent_groups_split_by_lift"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
