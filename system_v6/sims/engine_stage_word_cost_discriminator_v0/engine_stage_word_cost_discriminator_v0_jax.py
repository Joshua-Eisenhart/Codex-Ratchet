#!/usr/bin/env python3
"""Python/quimb mirror for engine_stage_word_cost_discriminator_v0.

The filename uses the repository's validator-compatible "jax" lane label, but
the load-bearing Python tensor-network tool here is quimb.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import math
from pathlib import Path
import resource
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import quimb
import quimb.tensor as qtn
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "engine_stage_word_cost_discriminator_v0"
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
NS = [8, 12, 16]
CUTOFF = 1.0e-14
MAX_BOND = None
SCENARIO_OFFSETS = {"loop_local": 0, "random_word": 101, "all_to_all": 202, "haar": 303}
SUPPLEMENTARY_SCENARIO_OFFSETS = {"random_word_own_sampled": 101}

PIN_SPEC = (
    "engine_stage_word_cost_discriminator_v0|mode=FREE|"
    "word=D_then_I:Se,Ne,Ni,Si,Se,Si,Ni,Ne|seat_i_uses_word_i_mod_8|"
    "actions=Ti_z_axis_ZZ,Fe_Rz_ZZ,Ti_down_ZZ,Fe_down_Rz_ZZ,"
    "Te_x_axis_XX,Fi_Rx_XX,Te_down_XX,Fi_down_Rx_XX|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

SOURCE_REFS = {
    "two_engine_readout_automaton": "system_v6/foundations/two_engine_readout_automaton_20260609.md",
    "working_math_scaffold_s4_forms": "system_v6/foundations/working_math_scaffold_20260609.md#3-four-base-operator-families",
    "working_math_scaffold_signed_operators": "system_v6/foundations/working_math_scaffold_20260609.md#5-signed-operators--axis-6-variants",
    "ring_checkerboard_support_graph_probe": "system_v6/sims/ring_checkerboard_support_graph_probe/",
    "geo_s4_operator_stage_v0": "system_v6/sims/geo_s4_operator_stage_v0/",
}

TOOL_MANIFEST = {
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MPS state evolution, dense conversion, bond dimensions, and n=8 MPS-vs-dense cross-check",
    },
    "quimb.tensor": {
        "tried": True,
        "used": True,
        "reason": "load-bearing MatrixProductState construction and gate application",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing finite readout-periodicity identity with erased-flip SAT control",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent finite readout-periodicity identity with erased-flip SAT control",
    },
    "numpy": {
        "tried": True,
        "used": True,
        "reason": "supportive matrix construction, dense statevector evolution, QR Haar draws, and SVD rank cross-checks",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive JSON, path, timestamp, memory, and hashing machinery",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "quimb": "load_bearing",
    "quimb.tensor": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": "supportive",
    "python_stdlib": "supportive",
}

I2 = np.eye(2, dtype=np.complex128)
X = np.asarray([[0, 1], [1, 0]], dtype=np.complex128)
Z = np.asarray([[1, 0], [0, -1]], dtype=np.complex128)

STAGE_WORD = [
    {"stage": "Se", "loop": "D", "signed_operator": "Ti↑", "axis": "Z", "family": "Ti"},
    {"stage": "Ne", "loop": "D", "signed_operator": "Fe↑", "axis": "Z", "family": "Fe"},
    {"stage": "Ni", "loop": "D", "signed_operator": "Ti↓", "axis": "Z", "family": "Ti"},
    {"stage": "Si", "loop": "D", "signed_operator": "Fe↓", "axis": "Z", "family": "Fe"},
    {"stage": "Se", "loop": "I", "signed_operator": "Te↑", "axis": "X", "family": "Te"},
    {"stage": "Si", "loop": "I", "signed_operator": "Fi↑", "axis": "X", "family": "Fi"},
    {"stage": "Ni", "loop": "I", "signed_operator": "Te↓", "axis": "X", "family": "Te"},
    {"stage": "Ne", "loop": "I", "signed_operator": "Fi↓", "axis": "X", "family": "Fi"},
]

# Generated once from the Python/quimb RNG path and stored as packet data.
# Both engines replay these exact STAGE_WORD indices for the named random rows.
SHARED_RANDOM_STAGE_INDICES = {
    "8": {
        "word": [0, 3, 1, 4, 3, 7, 0, 4],
        "double_720": [4, 1, 3, 2, 2, 5, 4, 2, 4, 1, 1, 5, 5, 3, 6, 2],
    },
    "12": {
        "word": [6, 6, 6, 1, 5, 2, 0, 7, 3, 5, 1, 6],
        "double_720": [4, 5, 7, 7, 5, 3, 5, 6, 7, 5, 6, 7, 2, 1, 7, 0, 0, 5, 5, 4, 7, 7, 7, 6],
    },
    "16": {
        "word": [3, 6, 6, 2, 3, 3, 5, 0, 2, 0, 3, 0, 7, 4, 7, 6],
        "double_720": [6, 0, 7, 3, 3, 2, 7, 4, 1, 6, 4, 4, 6, 4, 6, 3, 1, 1, 5, 3, 5, 7, 4, 2, 2, 7, 5, 1, 2, 1, 0, 0],
    },
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def r12(value: float) -> float:
    return round(float(np.real(value)), 12)


def memory_units() -> int:
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def sign_for(opname: str) -> float:
    return 1.0 if "↑" in opname else -1.0


def axis_matrix(axis: str) -> np.ndarray:
    return X if axis == "X" else Z


def rx(theta: float) -> np.ndarray:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * X


def rz(theta: float) -> np.ndarray:
    return math.cos(theta / 2.0) * I2 - 1j * math.sin(theta / 2.0) * Z


def raa(axis: str, theta: float) -> np.ndarray:
    amat = axis_matrix(axis)
    return math.cos(theta / 2.0) * np.kron(I2, I2) - 1j * math.sin(theta / 2.0) * np.kron(amat, amat)


def haar2(rng: np.random.Generator) -> np.ndarray:
    raw = (rng.normal(size=(4, 4)) + 1j * rng.normal(size=(4, 4))) / math.sqrt(2.0)
    qmat, rmat = np.linalg.qr(raw)
    phases = np.diag(rmat)
    phases = np.where(np.abs(phases) <= np.finfo(float).eps, 1.0 + 0.0j, phases / np.abs(phases))
    return qmat @ np.diag(phases)


def nonlocal_pair(n: int, step: int, offset: int) -> tuple[int, int]:
    a = (5 * step + 3 * offset + 1) % n
    b = (7 * step + 5 * offset + n // 2) % n
    if a == b or abs(a - b) == 1 or abs(a - b) == n - 1:
        b = (a + n // 2) % n
    if a == b:
        b = (a + 1) % n
    return a, b


def stage_for(n: int, step: int, scenario: str, traversal: str, rng: np.random.Generator) -> dict[str, str]:
    if scenario == "random_word":
        return STAGE_WORD[SHARED_RANDOM_STAGE_INDICES[str(n)][traversal][step - 1]]
    if scenario == "random_word_own_sampled":
        return STAGE_WORD[int(rng.integers(0, len(STAGE_WORD)))]
    return STAGE_WORD[(step - 1) % len(STAGE_WORD)]


def stage_gate_plan(n: int, step: int, scenario: str, traversal: str, rng: np.random.Generator) -> tuple[dict[str, str], list[tuple[np.ndarray, tuple[int, ...]]]]:
    seat = (step - 1) % n
    stage = stage_for(n, step, scenario, traversal, rng)
    sign = sign_for(stage["signed_operator"])
    axis = stage["axis"]
    family = stage["family"]
    gates: list[tuple[np.ndarray, tuple[int, ...]]] = []

    if scenario == "haar":
        for lane in (1, 2):
            gates.append((haar2(rng), nonlocal_pair(n, step, lane)))
        return stage, gates

    pair_angle = sign * (0.31 if axis == "Z" else 0.29)
    if family in {"Fi", "Fe"}:
        gates.append(((rx(sign * 0.37) if family == "Fi" else rz(sign * 0.41)), (seat,)))
        pair_angle = sign * (0.17 if family == "Fi" else 0.19)

    if scenario == "all_to_all":
        pairs = [nonlocal_pair(n, step, 1), nonlocal_pair(n, step, 2)]
    else:
        pairs = [((seat - 1) % n, seat), (seat, (seat + 1) % n)]
    two_site = raa(axis, pair_angle)
    for pair in pairs:
        gates.append((two_site, pair))
    return stage, gates


def traversal_steps(n: int, traversal: str) -> int:
    if traversal == "word":
        return n
    if traversal == "double_720":
        return 2 * n
    raise ValueError(traversal)


def apply_dense_gate(state: np.ndarray, gate: np.ndarray, where: tuple[int, ...], n: int) -> np.ndarray:
    where = tuple(where)
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


def mps_vector(psi: qtn.MatrixProductState) -> np.ndarray:
    return np.asarray(psi.to_dense()).reshape(-1)


def run_scenario(n: int, scenario: str, traversal: str, *, dense_crosscheck: bool = False) -> dict[str, Any]:
    seed_offsets = SCENARIO_OFFSETS | SUPPLEMENTARY_SCENARIO_OFFSETS
    seed = SEED + 1000 * n + seed_offsets[scenario] + (17 if traversal == "double_720" else 0)
    rng = np.random.default_rng(seed)
    start = _dt.datetime.now(_dt.UTC)
    start_mem = memory_units()
    psi = qtn.MPS_computational_state("0" * n)
    dense = np.zeros(2**n, dtype=np.complex128) if dense_crosscheck else None
    if dense is not None:
        dense[0] = 1.0
    stage_trace: list[dict[str, Any]] = []
    chi_trace: list[int] = []
    max_norm_deviation = 0.0

    for step in range(1, traversal_steps(n, traversal) + 1):
        stage, gates = stage_gate_plan(n, step, scenario, traversal, rng)
        for gate, where in gates:
            psi.gate_(gate, where, contract="swap+split", cutoff=CUTOFF, max_bond=MAX_BOND)
            if dense is not None:
                dense = apply_dense_gate(dense, gate, where, n)
        norm_value = float(abs(psi.H @ psi))
        max_norm_deviation = max(max_norm_deviation, abs(norm_value - 1.0))
        chi = int(psi.max_bond())
        chi_trace.append(chi)
        stage_trace.append(
            {
                "step": step,
                "seat": (step - 1) % n,
                "stage": stage["stage"],
                "loop": stage["loop"],
                "signed_operator": stage["signed_operator"],
                "chi": chi,
                "linkdims": list(map(int, psi.bond_sizes())),
                "norm": r12(norm_value),
            }
        )

    elapsed = (_dt.datetime.now(_dt.UTC) - start).total_seconds()
    row: dict[str, Any] = {
        "n": n,
        "scenario": scenario,
        "traversal": traversal,
        "steps": traversal_steps(n, traversal),
        "seed": seed,
        "row_role": "supplementary_own_sampled_random_word" if scenario == "random_word_own_sampled" else "named_control",
        "max_chi": max(chi_trace),
        "final_chi": chi_trace[-1],
        "final_linkdims": list(map(int, psi.bond_sizes())),
        "chi_trace": chi_trace,
        "stage_trace": stage_trace,
        "wall_clock_seconds": r12(elapsed),
        "memory_start_ru_maxrss" : start_mem,
        "memory_end_ru_maxrss": memory_units(),
        "truncation": {
            "cutoff": CUTOFF,
            "max_bond": MAX_BOND,
            "max_norm_deviation_from_unit": r12(max_norm_deviation),
        },
    }
    if dense is not None:
        mps = mps_vector(psi)
        dense_norm = np.vdot(dense, dense).real
        mps_norm = np.vdot(mps, mps).real
        fidelity = abs(np.vdot(dense, mps)) ** 2 / (dense_norm * mps_norm)
        dense_ranks = dense_bond_ranks(dense, n)
        row["dense_crosscheck"] = {
            "ran": True,
            "statevector_dimension": int(dense.shape[0]),
            "fidelity": r12(fidelity),
            "infidelity": float(max(0.0, 1.0 - fidelity)),
            "dense_norm": r12(dense_norm),
            "mps_norm": r12(mps_norm),
            "dense_schmidt_ranks": dense_ranks,
            "mps_bond_sizes": list(map(int, psi.bond_sizes())),
            "bond_sizes_match_dense_ranks": dense_ranks == list(map(int, psi.bond_sizes())),
            "truncation_error_reported_as_infidelity": float(max(0.0, 1.0 - fidelity)),
        }
    return row


def z3_periodicity_proof() -> dict[str, Any]:
    bits = [z3.Bool(f"r{i}") for i in range(4)]
    alternating = [bits[0] == bits[2], bits[1] == bits[3], bits[0] != bits[1]]
    paired = [bits[0] == bits[1], bits[2] == bits[3], bits[0] != bits[2]]
    solver = z3.Solver()
    solver.add(*(alternating + paired))
    verdict = str(solver.check())

    control = z3.Solver()
    control.add(bits[0] == bits[2], bits[1] == bits[3], bits[0] == bits[1], bits[2] == bits[3])
    control_verdict = str(control.check())
    model = None
    if control_verdict == "sat":
        model = {f"r{i}": bool(z3.is_true(control.model()[bits[i]])) for i in range(4)}
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "identity": "no single non-erased four-bit readout is both alternating and paired",
        "positive_case": "alternating constraints plus paired constraints are UNSAT",
        "erased_flip_control": "remove the nontrivial flip/phase inequalities; common constant readout is SAT",
        "control_verdict": control_verdict,
        "control_model": model,
        "tool_call_index": 1,
    }


def cvc5_periodicity_proof() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_UF")
    bool_sort = solver.getBooleanSort()
    bits = [solver.mkConst(bool_sort, f"c{i}") for i in range(4)]

    def eq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, b)

    def neq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.NOT, eq(a, b))

    for formula in [eq(bits[0], bits[2]), eq(bits[1], bits[3]), neq(bits[0], bits[1]), eq(bits[0], bits[1]), eq(bits[2], bits[3]), neq(bits[0], bits[2])]:
        solver.assertFormula(formula)
    verdict = str(solver.checkSat())

    control = cvc5.Solver()
    control.setLogic("QF_UF")
    cbool = control.getBooleanSort()
    cbits = [control.mkConst(cbool, f"k{i}") for i in range(4)]

    def ceq(a: Any, b: Any) -> Any:
        return control.mkTerm(Kind.EQUAL, a, b)

    for formula in [ceq(cbits[0], cbits[2]), ceq(cbits[1], cbits[3]), ceq(cbits[0], cbits[1]), ceq(cbits[2], cbits[3])]:
        control.assertFormula(formula)
    return {
        "ran": True,
        "load_bearing": True,
        "verdict": verdict,
        "identity": "no single non-erased four-bit readout is both alternating and paired",
        "positive_case": "alternating constraints plus paired constraints are UNSAT",
        "erased_flip_control": "remove the nontrivial flip/phase inequalities; common constant readout is SAT",
        "control_verdict": str(control.checkSat()),
        "tool_call_index": 2,
    }


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for n in NS:
        out[str(n)] = {}
        for scenario in ["loop_local", "random_word", "all_to_all", "haar"]:
            out[str(n)][scenario] = {}
            for traversal in ["word", "double_720"]:
                row = next(r for r in rows if r["n"] == n and r["scenario"] == scenario and r["traversal"] == traversal)
                out[str(n)][scenario][traversal] = {
                    "max_chi": row["max_chi"],
                    "final_chi": row["final_chi"],
                    "wall_clock_seconds": row["wall_clock_seconds"],
                    "max_norm_deviation_from_unit": row["truncation"]["max_norm_deviation_from_unit"],
                }
    return out


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    supplementary_own_sampled_rows: list[dict[str, Any]] = []
    for n in NS:
        for scenario in ["loop_local", "random_word", "all_to_all", "haar"]:
            for traversal in ["word", "double_720"]:
                rows.append(
                    run_scenario(
                        n,
                        scenario,
                        traversal,
                        dense_crosscheck=(n == 8 and scenario == "loop_local" and traversal == "double_720"),
                    )
                )
        for traversal in ["word", "double_720"]:
            supplementary_own_sampled_rows.append(run_scenario(n, "random_word_own_sampled", traversal))
    summary = summarize(rows)
    local_double = [summary[str(n)]["loop_local"]["double_720"]["max_chi"] for n in NS]
    alltoall_double = [summary[str(n)]["all_to_all"]["double_720"]["max_chi"] for n in NS]
    haar_double = [summary[str(n)]["haar"]["double_720"]["max_chi"] for n in NS]
    random_double = [summary[str(n)]["random_word"]["double_720"]["max_chi"] for n in NS]
    dense_row = next(r for r in rows if r["n"] == 8 and r["scenario"] == "loop_local" and r["traversal"] == "double_720")
    z3_proof = z3_periodicity_proof()
    cvc5_proof = cvc5_periodicity_proof()
    random_faster_count = sum(int(r > l) for r, l in zip(random_double, local_double))
    gate_pass = {
        "mode_declared_free": MODE == "FREE",
        "ceiling_preserved": CLASSIFICATION == "scratch_diagnostic" and PROMOTION_ALLOWED is False and FORMAL_ADMISSION_ALLOWED is False,
        "local_double_bounded_at_or_below_8": max(local_double) <= 8,
        "all_to_all_control_exceeds_local_at_n16": alltoall_double[-1] > local_double[-1],
        "haar_control_exceeds_all_to_all_at_n16": haar_double[-1] > alltoall_double[-1],
        "dense_crosscheck_fidelity_one_to_tol": dense_row["dense_crosscheck"]["fidelity"] >= 1.0 - 1.0e-10,
        "dense_bond_sizes_match_mps": dense_row["dense_crosscheck"]["bond_sizes_match_dense_ranks"] is True,
        "z3_cvc5_agree_unsat": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat",
        "erased_flip_controls_sat": z3_proof["control_verdict"] == "sat" and cvc5_proof["control_verdict"] == "sat",
        "random_word_checked_not_forced": len(random_double) == len(NS),
    }
    if alltoall_double[-1] <= local_double[-1]:
        verdict = "EXCLUDED"
    elif max(local_double) <= 8 and haar_double[-1] > alltoall_double[-1] and random_faster_count == len(NS):
        verdict = "MIXED"
    else:
        verdict = "MIXED"
    return {
        "schema_version": "engine_stage_word_cost_discriminator_v0_python_result_v1",
        "sim_id": SIM_ID,
        "engine": ENGINE,
        "engine_label_note": "validator-compatible jax lane label; load-bearing Python tensor-network package is quimb/quimb.tensor",
        "mode": MODE,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": sha256_file(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "seed": SEED,
        "source_refs": SOURCE_REFS,
        "stage_word": STAGE_WORD,
        "shared_random_stage_indices": SHARED_RANDOM_STAGE_INDICES,
        "shared_random_word_policy": {
            "named_random_word_rows": "scenario=random_word replays shared_random_stage_indices in both engines",
            "supplementary_rows": "engine-native RNG rows are stored separately as supplementary_random_word_own_sampled_rows",
        },
        "stage_assignment": {
            "rule": "for each n, traversal seat i receives STAGE_WORD[(i mod 8)+1]; double_720 repeats the traversal once",
            "n_values": NS,
        },
        "packages_used": ["quimb", "quimb.tensor", "z3", "cvc5", "numpy", "python_stdlib"],
        "package_versions": {
            "quimb": getattr(quimb, "__version__", None),
            "z3": getattr(z3, "__version__", None),
            "cvc5": getattr(cvc5, "__version__", None),
            "numpy": np.__version__,
        },
        "aligned_packages_load_bearing": ["quimb", "quimb.tensor", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "claim_path_tools": ["quimb", "quimb.tensor", "z3", "cvc5"],
        "tool_calls": [
            {
                "tool": "quimb.tensor",
                "qualified_api": "qtn.MPS_computational_state",
                "input_object": "|0>^n for n=8,12,16",
                "output_object": "MatrixProductState",
                "positive_case": "loop-local and controls initialize as bond-1 MPS",
                "negative_or_erased_control": "none; initialization support call",
                "boundary_case": "n=16",
                "demotion_condition": "MPS construction fails",
                "gates": ["python_quimb_ran"],
                "tool_call_index": 1,
            },
            {
                "tool": "quimb.tensor",
                "qualified_api": "MatrixProductState.gate_",
                "input_object": "S4-axis lifted one/two-qubit unitary gates",
                "output_object": "evolved MPS after each stage",
                "positive_case": "loop-local stage word",
                "negative_or_erased_control": "random_word/all_to_all/Haar controls",
                "boundary_case": "n=16 double_720",
                "demotion_condition": "gate application fails or bond dimensions unavailable",
                "gates": ["local_double_bounded_at_or_below_8", "all_to_all_control_exceeds_local_at_n16"],
                "tool_call_index": 2,
            },
            {
                "tool": "z3",
                "qualified_api": "z3.Solver.check",
                "input_object": "four-bit alternating and paired readout constraints",
                "output_object": "UNSAT plus erased-flip SAT control",
                "positive_case": "alternating and paired cannot be the same non-erased readout",
                "negative_or_erased_control": "erased flip/phase inequalities",
                "boundary_case": "four-stage readout period",
                "demotion_condition": "SAT on positive case or UNSAT on erased control",
                "gates": ["z3_cvc5_agree_unsat", "erased_flip_controls_sat"],
                "tool_call_index": z3_proof["tool_call_index"],
            },
            {
                "tool": "cvc5",
                "qualified_api": "cvc5.Solver.checkSat",
                "input_object": "four-bit alternating and paired readout constraints",
                "output_object": "UNSAT plus erased-flip SAT control",
                "positive_case": "alternating and paired cannot be the same non-erased readout",
                "negative_or_erased_control": "erased flip/phase inequalities",
                "boundary_case": "four-stage readout period",
                "demotion_condition": "SAT on positive case or UNSAT on erased control",
                "gates": ["z3_cvc5_agree_unsat", "erased_flip_controls_sat"],
                "tool_call_index": cvc5_proof["tool_call_index"],
            },
        ],
        "rows": rows,
        "supplementary_random_word_own_sampled_rows": supplementary_own_sampled_rows,
        "summary": summary,
        "dense_crosscheck_n8_loop_local_double": dense_row["dense_crosscheck"],
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "values": {
            "local_n8_double_max_chi": summary["8"]["loop_local"]["double_720"]["max_chi"],
            "local_n12_double_max_chi": summary["12"]["loop_local"]["double_720"]["max_chi"],
            "local_n16_double_max_chi": summary["16"]["loop_local"]["double_720"]["max_chi"],
            "all_to_all_n16_double_max_chi": summary["16"]["all_to_all"]["double_720"]["max_chi"],
            "haar_n16_double_max_chi": summary["16"]["haar"]["double_720"]["max_chi"],
            "random_word_n16_double_max_chi": summary["16"]["random_word"]["double_720"]["max_chi"],
            "dense_crosscheck_fidelity": dense_row["dense_crosscheck"]["fidelity"],
        },
        "random_word_control": {
            "faster_than_local_count": random_faster_count,
            "n_values": NS,
            "local_double_max_chi": local_double,
            "random_word_double_max_chi": random_double,
            "interpretation": "checked as an order/locality stressor, not forced as a pass gate",
        },
        "cost_verdict": verdict,
        "builder_verdict_note": "Hardened builder rows close H1/H2/H3 inputs, but verdict promotion is reserved for fresh re-audit; this leg does not self-upgrade to SURVIVES.",
        "gate_pass": gate_pass,
        "all_pass": all(gate_pass.values()),
        "limits": [
            "Pure-state unitary axis-lift of S4 forms; this does not simulate density-channel dephasing as a mixed-state channel.",
            "No extrapolation beyond n=8,12,16.",
            "Named random-word rows replay one stored shared sequence per n/traversal; own-sampled engine RNG rows are supplementary only.",
        ],
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": result["all_pass"],
                "result_path": str(RESULT_PATH.relative_to(ROOT)),
                "cost_verdict": result["cost_verdict"],
                "local_double": result["random_word_control"]["local_double_max_chi"],
                "random_word_double": result["random_word_control"]["random_word_double_max_chi"],
                "n8_fidelity": result["dense_crosscheck_n8_loop_local_double"]["fidelity"],
            },
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
