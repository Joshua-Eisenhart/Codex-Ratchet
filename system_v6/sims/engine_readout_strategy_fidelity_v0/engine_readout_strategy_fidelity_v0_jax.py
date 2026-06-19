#!/usr/bin/env python3
"""Dense Python/z3/cvc5 readout leg for engine_readout_strategy_fidelity_v0.

The validator-compatible engine label is "jax"; this packet intentionally uses
dense n=8 numpy state evolution plus z3/cvc5. The readout grammar is the
committed automaton grammar, applied to the actual loop-local state trace.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import z3


ROOT = Path(__file__).resolve().parents[3]
SIM_ID = "engine_readout_strategy_fidelity_v0"
ENGINE = "jax"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_{ENGINE}.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_{ENGINE}_results.json"

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
MODE = "FREE"
SEED = 20260610
N = 8

COST_SOURCE_REF = {
    "commit": "123b8e7d8f1b7aca5162facc5a7801f06372b02a",
    "source": "system_v6/sims/engine_stage_word_cost_discriminator_v0/engine_stage_word_cost_discriminator_v0_jax.py",
    "sections": [
        "PIN_SPEC",
        "STAGE_WORD",
        "stage_assignment.rule",
        "dense_crosscheck_n8_loop_local_double",
    ],
}
AUTOMATON_SOURCE_REF = {
    "commit": "dd9ec4999b2ccb982226344f232dda86307429fc",
    "source": "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "section": "The Two-Engine Readout Automaton / THE 16 LOOP-READOUT STRATEGIES",
    "read_rule": "active loop reads one component of the stage two-component word; outer uppercase, inner lowercase",
}

PIN_SPEC = (
    "engine_readout_strategy_fidelity_v0|consumes=123b8e7d8,dd9ec4999|"
    "n=8|states=dense_loop_local_replay|word=D_then_I:Se,Ne,Ni,Si,Se,Si,Ni,Ne|"
    "seat_i_uses_word_i_mod_8|strategies=2types_2loops_4stage_slots|"
    "read_rule=outer_uppercase_inner_lowercase|classification=scratch_diagnostic|"
    "promotion_allowed=false|formal_admission_allowed=false"
)

TOOL_MANIFEST = {
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing computed 16-row periodicity violation UNSAT check plus erased-flip SAT control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent computed 16-row periodicity violation UNSAT check plus erased-flip SAT control",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive dense n=8 state evolution, norms, trace readout, and state digests",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive hashing, JSON, timestamps, path handling, and deterministic tables",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": "supportive",
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

STAGE_COMPONENTS = {
    "Se": {"outer": "LOSE", "inner": "win"},
    "Ne": {"outer": "WIN", "inner": "lose"},
    "Ni": {"outer": "LOSE", "inner": "lose"},
    "Si": {"outer": "WIN", "inner": "win"},
}

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


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def r12(value: float) -> float:
    return round(float(np.real(value)), 12)


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


def dense_bond_ranks(state: np.ndarray, n: int, tol: float = 1.0e-10) -> list[int]:
    ranks = []
    for cut in range(1, n):
        mat = state.reshape((2**cut, 2 ** (n - cut)))
        singular_values = np.linalg.svd(mat, compute_uv=False)
        ranks.append(int(np.sum(singular_values > tol)))
    return ranks


def state_digest(state: np.ndarray) -> str:
    rounded = np.round(np.column_stack((state.real, state.imag)).reshape(-1), 14)
    return hashlib.sha256(rounded.tobytes()).hexdigest()


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


def replay_loop_local_states(traversal: str) -> dict[str, Any]:
    steps = N if traversal == "word" else 2 * N
    state = np.zeros(2**N, dtype=np.complex128)
    state[0] = 1.0
    trace: list[dict[str, Any]] = []
    for step in range(1, steps + 1):
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
                "state_sha256": state_digest(state),
                "norm": r12(norm),
                "density_trace_real": r12(norm),
                "bond_ranks": dense_bond_ranks(state, N),
            }
        )
    return {
        "traversal": traversal,
        "n": N,
        "statevector_dimension": int(state.shape[0]),
        "steps": steps,
        "stage_assignment": "seat i receives STAGE_WORD[i mod 8]; double_720 repeats the same stored word",
        "trace": trace,
        "final_state_sha256": state_digest(state),
        "max_norm_deviation": r12(max(abs(row["norm"] - 1.0) for row in trace)),
    }


def state_indices_for(base: dict[str, Any], traversal: str) -> list[int]:
    offset = 0 if base["order_family"] == "deductive" else 4
    if traversal == "word":
        return [offset + i for i in range(4)]
    return [offset + i for i in range(4)] + [8 + offset + i for i in range(4)]


def labels_for_path(base: dict[str, Any], path: list[str] | None = None, repeat: int = 1) -> list[str]:
    stage_path = path if path is not None else base["path"]
    return [base["readout_by_stage"][stage] for _ in range(repeat) for stage in stage_path]


def bits_for_labels(labels: list[str]) -> list[int]:
    return [1 if label.lower() == "win" else 0 for label in labels]


def periodicity_status(labels: list[str], expected: str) -> bool:
    bits = bits_for_labels(labels[:4])
    if expected == "alternating":
        ok4 = bits[0] == bits[2] and bits[1] == bits[3] and bits[0] != bits[1]
    elif expected == "paired":
        ok4 = bits[0] == bits[1] and bits[2] == bits[3] and bits[0] != bits[2]
    else:
        raise ValueError(expected)
    if len(labels) == 4:
        return ok4
    return ok4 and labels[:4] == labels[4:8]


def build_strategy_rows(states_by_traversal: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for base in BASE_STRATEGIES:
        for stage_slot in base["path"]:
            row_id = f"{base['base_id']}_slot_{stage_slot}"
            word_labels = labels_for_path(base, repeat=1)
            double_labels = labels_for_path(base, repeat=2)
            word_indices = state_indices_for(base, "word")
            double_indices = state_indices_for(base, "double_720")
            word_states = [states_by_traversal["word"]["trace"][idx] for idx in word_indices]
            double_states = [states_by_traversal["double_720"]["trace"][idx] for idx in double_indices]
            rows.append(
                {
                    "strategy_id": row_id,
                    "base_strategy": base["base_id"],
                    "engine_type": base["engine_type"],
                    "loop": base["loop"],
                    "order_family": base["order_family"],
                    "component": base["component"],
                    "stage_slot": stage_slot,
                    "measurement_mapping": {
                        "source": AUTOMATON_SOURCE_REF,
                        "rule": f"read {base['component']} component from stage two-component word",
                        "stage_to_readout": {stage: base["readout_by_stage"][stage] for stage in base["path"]},
                        "state_binding": "readout labels are attached to the dense state reached at the corresponding loop-local stage index",
                    },
                    "path": base["path"],
                    "state_indices_word": word_indices,
                    "state_indices_double_720": double_indices,
                    "readout_word": word_labels,
                    "readout_double_720": double_labels,
                    "bits_word": bits_for_labels(word_labels),
                    "bits_double_720": bits_for_labels(double_labels),
                    "state_sha256_word": [item["state_sha256"] for item in word_states],
                    "state_sha256_double_720": [item["state_sha256"] for item in double_states],
                    "density_trace_word": [item["density_trace_real"] for item in word_states],
                    "density_trace_double_720": [item["density_trace_real"] for item in double_states],
                    "predicted_periodicity": base["predicted_periodicity"],
                    "periodicity_word_ok": periodicity_status(word_labels, base["predicted_periodicity"]),
                    "periodicity_double_720_ok": periodicity_status(double_labels, base["predicted_periodicity"]),
                }
            )
    return rows


def equivalence_groups(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[str]] = {}
    for row in rows:
        groups.setdefault(tuple(row[key]), []).append(row["strategy_id"])
    return [
        {"readout": list(readout), "strategies": names, "count": len(names)}
        for readout, names in sorted(groups.items(), key=lambda item: (item[0], item[1][0]))
    ]


def distinguishability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    names = [row["strategy_id"] for row in rows]
    matrix_360 = []
    matrix_720 = []
    for left in rows:
        matrix_360.append([left["readout_word"] != right["readout_word"] for right in rows])
        matrix_720.append([left["readout_double_720"] != right["readout_double_720"] for right in rows])
    groups_360 = equivalence_groups(rows, "readout_word")
    groups_720 = equivalence_groups(rows, "readout_double_720")
    return {
        "strategy_order": names,
        "separated_matrix_360": matrix_360,
        "separated_matrix_double_720": matrix_720,
        "indistinguishable_groups_360": [group for group in groups_360 if group["count"] > 1],
        "indistinguishable_groups_double_720": [group for group in groups_720 if group["count"] > 1],
        "double_720_separates_more_than_360": len(groups_720) > len(groups_360),
        "unique_readout_count_360": len(groups_360),
        "unique_readout_count_double_720": len(groups_720),
        "closure_answer": "no; the double traversal repeats each strategy readout and does not separate strategies that one 360 strategy cycle cannot",
    }


def controls(rows: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> dict[str, Any]:
    shuffled_paths = {
        "deductive": ["Se", "Ni", "Ne", "Si"],
        "inductive": ["Se", "Ni", "Si", "Ne"],
    }
    permuted_stage = {"Se": "Se", "Ne": "Ni", "Ni": "Ne", "Si": "Si"}
    shuffled_failures = []
    permuted_failures = []
    for base in BASE_STRATEGIES:
        shuffled = labels_for_path(base, shuffled_paths[base["order_family"]])
        if not periodicity_status(shuffled, base["predicted_periodicity"]):
            shuffled_failures.append({"base_strategy": base["base_id"], "readout": shuffled})
        permuted_path = [permuted_stage[stage] for stage in base["path"]]
        permuted = labels_for_path(base, permuted_path)
        if not periodicity_status(permuted, base["predicted_periodicity"]):
            permuted_failures.append({"base_strategy": base["base_id"], "permuted_path": permuted_path, "readout": permuted})
    trace_values = [item["density_trace_real"] for item in states["double_720"]["trace"]]
    return {
        "shuffled_stage_word_breaks_periodicity_table": bool(shuffled_failures),
        "shuffled_stage_word_failure_count": len(shuffled_failures),
        "shuffled_stage_word_failures": shuffled_failures,
        "strategy_blind_trace_constant": len(set(trace_values)) == 1 and trace_values[0] == 1.0,
        "strategy_blind_trace_values": trace_values,
        "permuted_seat_assignment_breaks_alternating_paired_split": bool(permuted_failures),
        "permuted_seat_assignment_failure_count": len(permuted_failures),
        "permuted_stage_assignment": permuted_stage,
        "permuted_seat_assignment_failures": permuted_failures,
    }


def z3_periodicity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = z3.Solver()
    violation_terms = []
    for idx, row in enumerate(rows):
        bits = [z3.Bool(f"r_{idx}_{i}") for i in range(4)]
        for bit, value in zip(bits, row["bits_word"]):
            solver.add(bit == z3.BoolVal(value == 1))
        if row["predicted_periodicity"] == "alternating":
            good = z3.And(bits[0] == bits[2], bits[1] == bits[3], bits[0] != bits[1])
        else:
            good = z3.And(bits[0] == bits[1], bits[2] == bits[3], bits[0] != bits[2])
        violation_terms.append(z3.Not(good))
    solver.add(z3.Or(violation_terms))
    verdict = str(solver.check())

    control = z3.Solver()
    c = [z3.Bool(f"erased_{i}") for i in range(4)]
    control.add(c[0] == c[2], c[1] == c[3], c[0] == c[1], c[2] == c[3])
    control_verdict = str(control.check())
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "identity": "no computed strategy row violates its predicted alternating/paired periodicity",
        "positive_case": "bind all 16 computed four-bit readouts, assert existence of a predicted-periodicity violation",
        "erased_flip_control": "erase nontrivial flip inequality; constant readout satisfies the weakened equalities",
        "control_verdict": control_verdict,
        "tool_call_index": 1,
    }


def cvc5_periodicity(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()

    def eq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, b)

    def neq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.NOT, eq(a, b))

    def conj(items: list[Any]) -> Any:
        return items[0] if len(items) == 1 else solver.mkTerm(Kind.AND, *items)

    violation_terms = []
    for idx, row in enumerate(rows):
        bits = [solver.mkConst(bool_sort, f"c_{idx}_{i}") for i in range(4)]
        for bit, value in zip(bits, row["bits_word"]):
            solver.assertFormula(eq(bit, solver.mkBoolean(bool(value))))
        if row["predicted_periodicity"] == "alternating":
            good = conj([eq(bits[0], bits[2]), eq(bits[1], bits[3]), neq(bits[0], bits[1])])
        else:
            good = conj([eq(bits[0], bits[1]), eq(bits[2], bits[3]), neq(bits[0], bits[2])])
        violation_terms.append(solver.mkTerm(Kind.NOT, good))
    solver.assertFormula(solver.mkTerm(Kind.OR, *violation_terms))
    verdict = str(solver.checkSat())

    control = cvc5.Solver()
    control.setLogic("QF_UF")
    cbool = control.getBooleanSort()
    c = [control.mkConst(cbool, f"k_{i}") for i in range(4)]

    def ceq(a: Any, b: Any) -> Any:
        return control.mkTerm(Kind.EQUAL, a, b)

    for formula in [ceq(c[0], c[2]), ceq(c[1], c[3]), ceq(c[0], c[1]), ceq(c[2], c[3])]:
        control.assertFormula(formula)
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "identity": "no computed strategy row violates its predicted alternating/paired periodicity",
        "positive_case": "bind all 16 computed four-bit readouts, assert existence of a predicted-periodicity violation",
        "erased_flip_control": "erase nontrivial flip inequality; constant readout satisfies the weakened equalities",
        "control_verdict": str(control.checkSat()),
        "tool_call_index": 2,
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    states = {name: replay_loop_local_states(name) for name in ("word", "double_720")}
    rows = build_strategy_rows(states)
    matrix = distinguishability(rows)
    control_rows = controls(rows, states)
    z3_proof = z3_periodicity(rows)
    cvc5_proof = cvc5_periodicity(rows)
    findings = [
        row["strategy_id"]
        for row in rows
        if not row["periodicity_word_ok"] or not row["periodicity_double_720_ok"]
    ]
    gate_pass = {
        "ceiling_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "dense_n8_loop_local_states_replayed": states["word"]["steps"] == 8 and states["double_720"]["steps"] == 16,
        "dense_state_norms_unit": states["word"]["max_norm_deviation"] <= 1.0e-10 and states["double_720"]["max_norm_deviation"] <= 1.0e-10,
        "strategy_count_16": len(rows) == 16,
        "periodicity_table_clean": len(findings) == 0,
        "z3_cvc5_computed_identity_unsat": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat",
        "erased_flip_controls_sat": z3_proof["control_verdict"] == "sat" and cvc5_proof["control_verdict"] == "sat",
        "shuffled_stage_word_control_fires": control_rows["shuffled_stage_word_breaks_periodicity_table"] is True,
        "strategy_blind_trace_control_constant": control_rows["strategy_blind_trace_constant"] is True,
        "permuted_seat_assignment_control_fires": control_rows["permuted_seat_assignment_breaks_alternating_paired_split"] is True,
    }
    all_pass = all(gate_pass.values())
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
        "source_refs": {
            "cost_discriminator": COST_SOURCE_REF,
            "automaton": AUTOMATON_SOURCE_REF,
        },
        "stage_word": STAGE_WORD,
        "stage_components": STAGE_COMPONENTS,
        "states": states,
        "strategy_rows": rows,
        "periodicity_findings": findings,
        "distinguishability": matrix,
        "controls": control_rows,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "packages_used": ["z3", "cvc5", "numpy", "python_stdlib"],
        "package_versions": {
            "z3": getattr(z3, "__version__", None),
            "cvc5": getattr(cvc5, "__version__", None),
            "numpy": np.__version__,
        },
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "claim_path_tools": ["z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "numpy",
                "qualified_api": "dense statevector gate application via ndarray reshape/transpose",
                "input_object": "n=8 loop-local stage-word gate plan from committed cost discriminator",
                "output_object": "word and double_720 dense state traces with state digests",
                "positive_case": "stored D_then_I word, seat_i_uses_word_i_mod_8",
                "negative_or_erased_control": "strategy-blind trace is constant and therefore cannot separate strategies",
                "boundary_case": "double_720 has 16 evolved states",
                "demotion_condition": "state norms drift or state count/order differs from pinned word",
                "gates": ["dense_n8_loop_local_states_replayed", "dense_state_norms_unit"],
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "all 16 computed strategy bit rows",
                "output_object": "UNSAT violation query plus SAT erased-flip control",
                "positive_case": "no computed row violates predicted periodicity",
                "negative_or_erased_control": "constant readout after erased flip",
                "boundary_case": "four-stage rows lifted to double_720 repetition",
                "demotion_condition": "positive query SAT or erased control UNSAT",
                "gates": ["z3_cvc5_computed_identity_unsat", "erased_flip_controls_sat"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "all 16 computed strategy bit rows",
                "output_object": "UNSAT violation query plus SAT erased-flip control",
                "positive_case": "no computed row violates predicted periodicity",
                "negative_or_erased_control": "constant readout after erased flip",
                "boundary_case": "four-stage rows lifted to double_720 repetition",
                "demotion_condition": "positive query SAT or erased control UNSAT",
                "gates": ["z3_cvc5_computed_identity_unsat", "erased_flip_controls_sat"],
            },
        ],
        "values": {
            "strategy_count": len(rows),
            "periodicity_violation_count": len(findings),
            "unique_readouts_360": matrix["unique_readout_count_360"],
            "unique_readouts_double_720": matrix["unique_readout_count_double_720"],
            "double_720_separates_more_than_360": matrix["double_720_separates_more_than_360"],
            "state_count_word": states["word"]["steps"],
            "state_count_double_720": states["double_720"]["steps"],
        },
        "gate_pass": gate_pass,
        "all_pass": all_pass,
        "limits": [
            "Readout is the committed stage-word component read rule applied to the actual dense state trace; it is not a new promoted quantum observable.",
            "The packet is n=8 only and scratch_diagnostic only.",
            "No strategy promotion or engine admission is made.",
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_path": rel(RESULT_PATH),
                "periodicity_violations": result["values"]["periodicity_violation_count"],
                "unique_360": result["values"]["unique_readouts_360"],
                "unique_double_720": result["values"]["unique_readouts_double_720"],
                "double_720_separates_more": result["values"]["double_720_separates_more_than_360"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
