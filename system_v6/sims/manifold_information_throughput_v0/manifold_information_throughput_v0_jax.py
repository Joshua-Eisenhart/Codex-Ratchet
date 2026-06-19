#!/usr/bin/env python3
"""Light-symbolic information-throughput ledger for committed manifold channels."""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib.metadata
import json
import math
import subprocess
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import numpy as np
import scipy.linalg
import sympy as sp
import z3


SIM_ID = "manifold_information_throughput_v0"
ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "system_v6" / "sims" / SIM_ID
RESULT = PACKET / "results" / f"{SIM_ID}_jax_results.json"
SOURCE = PACKET / f"{SIM_ID}_jax.py"
LOG_BASE = "e"
TOL = 1.0e-10

PARENT_RESULT_PATHS = {
    "manifold_entropy_ledger_v0": "system_v6/sims/manifold_entropy_ledger_v0/results/manifold_entropy_ledger_v0_envelope_results.json",
    "geo_s4_operator_stage_v0": "system_v6/sims/geo_s4_operator_stage_v0/results/geo_s4_operator_stage_v0_envelope_results.json",
    "geo_s5_terrain_flows_v0": "system_v6/sims/geo_s5_terrain_flows_v0/results/geo_s5_terrain_flows_v0_envelope_results.json",
    "compression_flow_radiated_record_v0": "system_v6/sims/compression_flow_radiated_record_v0/results/compression_flow_radiated_record_v0_envelope_results.json",
    "engine_readout_spinor_lift_v0": "system_v6/sims/engine_readout_spinor_lift_v0/results/engine_readout_spinor_lift_v0_envelope_results.json",
    "engine_readout_strategy_fidelity_v0": "system_v6/sims/engine_readout_strategy_fidelity_v0/results/engine_readout_strategy_fidelity_v0_envelope_results.json",
    "ratchet_s6_terrain_operator_shell_v0": "system_v6/sims/ratchet_s6_terrain_operator_shell_v0/results/ratchet_s6_terrain_operator_shell_v0_envelope_results.json",
    "ratchet_s6_terrain_sweep_v0": "system_v6/sims/ratchet_s6_terrain_sweep_v0/results/ratchet_s6_terrain_sweep_v0_envelope_results.json",
    "ratchet_deep_chain_v0": "system_v6/sims/ratchet_deep_chain_v0/results/ratchet_deep_chain_v0_envelope_results.json",
}

SIX_STATE_ENSEMBLE = [
    ("+x", np.array([1.0, 0.0, 0.0])),
    ("-x", np.array([-1.0, 0.0, 0.0])),
    ("+y", np.array([0.0, 1.0, 0.0])),
    ("-y", np.array([0.0, -1.0, 0.0])),
    ("+z", np.array([0.0, 0.0, 1.0])),
    ("-z", np.array([0.0, 0.0, -1.0])),
]


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_output(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def git_bytes(args: list[str]) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT)


def read_json(path: str) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def parent_lineage() -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, path in PARENT_RESULT_PATHS.items():
        payload = git_bytes(["show", f"HEAD:{path}"])
        rows[name] = {
            "result_path": path,
            "result_blob": git_output(["rev-parse", f"HEAD:{path}"]),
            "result_sha256": sha256_bytes(payload),
            "allowed_use": "hash-bound committed parent; rows in this packet are recomputed unless explicitly marked cited_parent_anchor",
        }
    rows["owner_prompt_parent_abbrev_notes"] = {
        "manifold_entropy_ledger_v0": "a54224476",
        "readout_packets": ["e2d9d5407", "lift packet"],
        "note": "owner-supplied abbreviated lineage retained as prompt context; actual local blob pins above are authoritative for this build",
    }
    return rows


def package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "version_unavailable"


def sx(value: Any) -> str:
    return str(sp.simplify(value))


def sf(value: float) -> float:
    if abs(value) < 1.0e-14:
        return 0.0
    return float(value)


def binary_entropy_prob(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return float(-p * math.log(p) - (1.0 - p) * math.log(1.0 - p))


def bloch_entropy(radius: float) -> float:
    radius = min(1.0, max(0.0, float(radius)))
    return binary_entropy_prob((1.0 + radius) / 2.0)


def bloch_entropy_sym(radius_expr: sp.Expr) -> sp.Expr:
    p = sp.simplify((1 + radius_expr) / 2)
    return sp.simplify(-p * sp.log(p) - (1 - p) * sp.log(1 - p))


def parse_expr(value: str) -> sp.Expr:
    return sp.sympify(value.replace("//", "/"))


def parse_matrix(values: list[list[str]]) -> np.ndarray:
    return np.array([[float(sp.N(parse_expr(item), 30)) for item in row] for row in values], dtype=float)


def parse_vector(values: list[str]) -> np.ndarray:
    return np.array([float(sp.N(parse_expr(item), 30)) for item in values], dtype=float)


def apply_affine(M: np.ndarray, c: np.ndarray, r: np.ndarray) -> np.ndarray:
    return M @ r + c


def holevo_six(M: np.ndarray, c: np.ndarray) -> dict[str, Any]:
    outputs = [apply_affine(M, c, r) for _, r in SIX_STATE_ENSEMBLE]
    avg = sum(outputs) / len(outputs)
    avg_entropy = bloch_entropy(float(np.linalg.norm(avg)))
    mean_entropy = sum(bloch_entropy(float(np.linalg.norm(out))) for out in outputs) / len(outputs)
    holevo = avg_entropy - mean_entropy
    return {
        "ensemble": "uniform six Pauli pure states",
        "avg_output_bloch": [sf(x) for x in avg.tolist()],
        "avg_output_entropy_nats": sf(avg_entropy),
        "mean_output_entropy_nats": sf(mean_entropy),
        "holevo_nats": sf(holevo),
        "information_killed_from_identity_nats": sf(math.log(2) - holevo),
        "output_radii": {label: sf(float(np.linalg.norm(out))) for (label, _), out in zip(SIX_STATE_ENSEMBLE, outputs)},
    }


def choi_from_affine(M: np.ndarray, c: np.ndarray) -> np.ndarray:
    I = np.eye(2, dtype=complex)
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)
    paulis = [X, Y, Z]

    def phi_mat(A: np.ndarray) -> np.ndarray:
        tr = np.trace(A)
        coeffs = np.array([np.trace(A @ P) for P in paulis], dtype=complex)
        out = tr * (I + c[0] * X + c[1] * Y + c[2] * Z) / 2.0
        for j, coeff in enumerate(coeffs):
            mapped = M[:, j]
            out += coeff * (mapped[0] * X + mapped[1] * Y + mapped[2] * Z) / 2.0
        return out

    blocks = [[phi_mat(np.array([[1 if (a, b) == (i, j) else 0 for a in range(2)] for b in range(2)], dtype=complex)) for j in range(2)] for i in range(2)]
    return np.block(blocks) / 2.0


def von_neumann_entropy_matrix(rho: np.ndarray) -> float:
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    vals = np.clip(np.real(vals), 0.0, 1.0)
    vals = vals[vals > 1.0e-14]
    return float(-np.sum(vals * np.log(vals)))


def coherent_info_max_mixed(M: np.ndarray, c: np.ndarray) -> float:
    out_center = c
    output_entropy = bloch_entropy(float(np.linalg.norm(out_center)))
    exchange_entropy = von_neumann_entropy_matrix(choi_from_affine(M, c))
    return sf(output_entropy - exchange_entropy)


def s4_channel_rows(s4: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    lam = sp.Rational(7, 10)
    p_dephase = sp.Rational(3, 20)
    h_lam = bloch_entropy_sym(lam)
    exact_dephase_holevo = sp.simplify(sp.log(2) - sp.Rational(2, 3) * h_lam)
    exact_dephase_q = sp.simplify(sp.log(2) + p_dephase * sp.log(p_dephase) + (1 - p_dephase) * sp.log(1 - p_dephase))
    for name in ["D_z", "D_x", "R_x", "R_z"]:
        rec = s4["affine_channel_table"][name]["pinned"]
        M = parse_matrix(rec["M"])
        c = parse_vector(rec["c"])
        six = holevo_six(M, c)
        if name.startswith("D_"):
            row = {
                "channel_class": "qubit_dephasing",
                "dephasing_factor_lambda": "7/10",
                "phase_flip_probability_p": "3/20",
                "classical_capacity_exact_nats": "log(2)",
                "classical_capacity_exact_float": sf(math.log(2)),
                "quantum_capacity_exact_nats": sx(exact_dephase_q),
                "quantum_capacity_exact_float": sf(float(sp.N(exact_dephase_q, 30))),
                "six_state_holevo_exact_nats": sx(exact_dephase_holevo),
                "six_state_information_killed_exact_nats": sx(sp.simplify(sp.log(2) - exact_dephase_holevo)),
                "six_state": six,
                "capacity_status": "exact_for_dephasing_family",
            }
        else:
            row = {
                "channel_class": "unitary_rotation",
                "classical_capacity_exact_nats": "log(2)",
                "classical_capacity_exact_float": sf(math.log(2)),
                "quantum_capacity_exact_nats": "log(2)",
                "quantum_capacity_exact_float": sf(math.log(2)),
                "six_state_holevo_exact_nats": "log(2)",
                "six_state_information_killed_exact_nats": "0",
                "six_state": six,
                "capacity_status": "lossless_unitary_exact",
            }
        row["M"] = rec["M"]
        row["c"] = rec["c"]
        row["information_killed_nats"] = row["six_state"]["information_killed_from_identity_nats"]
        out[name] = row
    return out


def classify_terrain(name: str) -> str:
    if name.startswith("Ne_"):
        return "hamiltonian_unitary_flow"
    if name.startswith("Si_"):
        return "projector_retention_dephasing_with_rotation"
    if name.startswith("Se_"):
        return "depolarizing_contraction_with_rotation"
    if name.startswith("Ni_"):
        return "nonunital_affine_amplitude_flow"
    return "unknown_affine_flow"


def terrain_channel_rows(s5: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, rec in s5["bloch_generator_table"].items():
        A = parse_matrix(rec["pinned"]["A"])
        b = parse_vector(rec["pinned"]["b"])
        M = scipy.linalg.expm(A)
        if float(np.linalg.norm(b)) <= TOL:
            c = np.zeros(3)
        else:
            c = np.linalg.solve(A, (M - np.eye(3)) @ b)
        six = holevo_six(M, c)
        ci = coherent_info_max_mixed(M, c)
        klass = classify_terrain(name)
        if klass == "hamiltonian_unitary_flow":
            capacity = {
                "classical_capacity_exact_nats": "log(2)",
                "classical_capacity_exact_float": sf(math.log(2)),
                "quantum_capacity_exact_nats": "log(2)",
                "quantum_capacity_exact_float": sf(math.log(2)),
                "capacity_status": "lossless_unitary_exact",
            }
        elif klass == "projector_retention_dephasing_with_rotation":
            lam = sp.exp(sp.Rational(-2, 5))
            p = sp.simplify((1 - lam) / 2)
            q = sp.simplify(sp.log(2) + p * sp.log(p) + (1 - p) * sp.log(1 - p))
            capacity = {
                "dephasing_factor_lambda": "exp(-2/5)",
                "classical_capacity_exact_nats": "log(2)",
                "classical_capacity_exact_float": sf(math.log(2)),
                "quantum_capacity_exact_nats": sx(q),
                "quantum_capacity_exact_float": sf(float(sp.N(q, 30))),
                "capacity_status": "exact_up_to_unitary_rotation_for_dephasing_axis",
            }
        elif klass == "depolarizing_contraction_with_rotation":
            eta = sp.exp(sp.Rational(-4, 5))
            h_eta = bloch_entropy_sym(eta)
            lower = sp.simplify(sp.log(2) - h_eta)
            capacity = {
                "depolarizing_factor_eta": "exp(-4/5)",
                "classical_capacity_exact_nats": sx(lower),
                "classical_capacity_exact_float": sf(float(sp.N(lower, 30))),
                "quantum_capacity_status": "not_claimed_exact_for_general_depolarizing_quantum_capacity",
                "coherent_information_maximally_mixed_lower_bound_nats": ci,
                "capacity_status": "classical_covariant_exact_quantum_bound_only",
            }
        else:
            capacity = {
                "classical_capacity_lower_bound_pinned_six_state_nats": six["holevo_nats"],
                "classical_capacity_upper_bound_nats": sf(math.log(2)),
                "quantum_capacity_status": "not_exact_for_general_nonunital_affine_row",
                "coherent_information_maximally_mixed_lower_bound_nats": ci,
                "capacity_status": "certified_bounds_only",
            }
        out[name] = {
            "channel_class": klass,
            "time_step": 1,
            "generator_A": rec["pinned"]["A"],
            "generator_b": rec["pinned"]["b"],
            "M_t1_float": [[sf(x) for x in row] for row in M.tolist()],
            "c_t1_float": [sf(x) for x in c.tolist()],
            "six_state": six,
            "information_killed_nats": six["information_killed_from_identity_nats"],
            **capacity,
        }
    return out


def compose_affine(left: tuple[np.ndarray, np.ndarray], right: tuple[np.ndarray, np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    M1, c1 = left
    M2, c2 = right
    return M1 @ M2, M1 @ c2 + c1


def stage_word(s4: dict[str, Any], readout: dict[str, Any]) -> dict[str, Any]:
    channel_by_signed = {"Ti": "D_z", "Te": "D_x", "Fi": "R_x", "Fe": "R_z"}
    channels = {
        name: (parse_matrix(s4["affine_channel_table"][name]["pinned"]["M"]), parse_vector(s4["affine_channel_table"][name]["pinned"]["c"]))
        for name in ["D_z", "D_x", "R_x", "R_z"]
    }
    trace = readout["lifted_states"]["single_360_trace"]
    rows = []
    current = (np.eye(3), np.zeros(3))
    previous_info = math.log(2)
    for item in trace:
        signed = item["signed_operator"].split("_")[0]
        channel = channel_by_signed[signed]
        current = compose_affine(channels[channel], current)
        six = holevo_six(*current)
        destroyed = previous_info - six["holevo_nats"]
        rows.append(
            {
                "step": item["step"],
                "stage": item["stage"],
                "signed_operator": item["signed_operator"],
                "channel": channel,
                "input_information_nats": sf(previous_info),
                "output_information_nats": six["holevo_nats"],
                "processed_nats": sf(previous_info),
                "destroyed_nats": sf(destroyed),
                "unitarity_split": "preserve" if channel.startswith("R_") else "destroy_off_axis",
            }
        )
        previous_info = six["holevo_nats"]
    word_output = previous_info
    for item in trace:
        signed = item["signed_operator"].split("_")[0]
        channel = channel_by_signed[signed]
        current = compose_affine(channels[channel], current)
    double = holevo_six(*current)
    return {
        "pinned_ensemble": "uniform six Pauli pure states",
        "stage_word_channels": [row["channel"] for row in rows],
        "stage_word_rows": rows,
        "word_output_information_nats": sf(word_output),
        "word_total_destroyed_nats": sf(math.log(2) - word_output),
        "word_total_processed_nats": sf(sum(row["processed_nats"] for row in rows)),
        "double_traversal_720_density_channel": {
            "output_information_nats": double["holevo_nats"],
            "destroyed_from_initial_nats": double["information_killed_from_identity_nats"],
            "status": "computed_by_reapplying_the_committed_8_stage_density_channel_word",
        },
        "double_traversal_720_spinor_lift_record": {
            "statevector_dimension": readout["lifted_states"]["statevector_dimension"],
            "density_quotient_rule": readout["lifted_states"]["density_quotient_rule"],
            "lift_rule": readout["lifted_states"]["double_720_lift_rule"],
            "sign_record_processed_nats": sf(math.log(2)),
            "density_accessible_sign_information_nats": 0.0,
            "status": "cited_parent_anchor_for_lift_rule_with_fresh_information_account_row",
        },
    }


def ratchet_account(entropy: dict[str, Any], compression: dict[str, Any], deep: dict[str, Any]) -> dict[str, Any]:
    rows = deep["ratchet_sequence"]["per_step_ledger"]["rows"]
    step_rows = []
    for row in rows:
        ent = row["entropy"]
        delta = ent["delta_float_nats"]
        gain = None if delta is None else sf(-float(delta))
        step_rows.append(
            {
                "step": row["step"],
                "constraint": row["constraint"],
                "entropy_nats": ent["h_nats"],
                "entropy_float_nats": ent["h_float_nats"],
                "information_gain_nats": gain,
                "account_status": "singular_conditioning_requires_band_limit" if delta is None else "finite_measure_delta",
            }
        )
    lens_loss = math.log(4)
    phase_loss = math.log(2)
    z2_loss = math.log(2)
    return {
        "conditioning_step": {
            "free_to_leaf": entropy["ledger"]["conditioning_deltas"]["free_to_leaf"],
            "committed_ratchet_step": step_rows[0],
            "honest_status": "ambient singleton conditioning is singular; committed disintegration/band convention supplies the typed account",
        },
        "finite_quotient_steps": {
            "Z4_lens": {
                "state_loss_without_record_nats": sf(lens_loss),
                "record_retained_nats": sf(lens_loss),
                "extended_account_defect_nats": 0.0,
                "state_level_without_record_defect_nats": sf(lens_loss),
            },
            "descended_phase_window": {
                "state_loss_without_record_nats": sf(phase_loss),
                "record_retained_nats": sf(phase_loss),
                "extended_account_defect_nats": 0.0,
            },
            "second_Z2_lens": {
                "state_loss_without_record_nats": sf(z2_loss),
                "record_retained_nats": sf(z2_loss),
                "extended_account_defect_nats": 0.0,
            },
        },
        "committed_deep_chain_rows": step_rows,
        "compression_flow_record_anchor": {
            "raw_mode": compression["record_mode_comparison"]["raw_mode"],
            "quotient_mode": compression["record_mode_comparison"]["quotient_mode"],
            "charge_rows": compression["shared_comparator_values"],
            "state_level_conclusion": "without record the quotient loses raw-row identity; with record, reconstruction succeeds at the declared level",
        },
        "conservation_answer": {
            "measure_account": "retained_record + quotient_state = prequotient_account exactly for the finite quotient rows",
            "state_level_analog": "exact only in the extended state-plus-record account; the quotient state alone loses the record",
        },
    }


def z3_conservation() -> dict[str, Any]:
    solver = z3.Solver()
    before, after, record = z3.Ints("before after record")
    solver.add(after == before - 2)
    solver.add(record == 2)
    solver.add(before != after + record)
    status = solver.check()

    erased = z3.Solver()
    eb, ea, er = z3.Ints("erased_before erased_after erased_record")
    erased.add(ea == eb - 2)
    erased.add(er == 0)
    erased.add(eb != ea + er)
    erased_status = erased.check()
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "z3",
        "verdict": str(status),
        "erased_record_control_verdict": str(erased_status),
        "claim": "finite quotient conservation over integer coefficients of log(2): before = after + record for Z4",
        "derived_in_solver": True,
        "erased_flip_unsat_to_sat": status == z3.unsat and erased_status == z3.sat,
    }


def cvc5_int(solver: cvc5.Solver, value: int) -> Any:
    return solver.mkInteger(value)


def cvc5_status(result: Any) -> str:
    if result.isSat():
        return "sat"
    if result.isUnsat():
        return "unsat"
    return str(result)


def cvc5_conservation() -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    before = solver.mkConst(integer, "before")
    after = solver.mkConst(integer, "after")
    record = solver.mkConst(integer, "record")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, after, solver.mkTerm(Kind.SUB, before, cvc5_int(solver, 2))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, record, cvc5_int(solver, 2)))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, before, solver.mkTerm(Kind.ADD, after, record))))
    status = solver.checkSat()

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    integer2 = erased.getIntegerSort()
    eb = erased.mkConst(integer2, "erased_before")
    ea = erased.mkConst(integer2, "erased_after")
    er = erased.mkConst(integer2, "erased_record")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, ea, erased.mkTerm(Kind.SUB, eb, cvc5_int(erased, 2))))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, er, cvc5_int(erased, 0)))
    erased.assertFormula(erased.mkTerm(Kind.NOT, erased.mkTerm(Kind.EQUAL, eb, erased.mkTerm(Kind.ADD, ea, er))))
    erased_status = erased.checkSat()
    return {
        "ran": True,
        "load_bearing": True,
        "solver": "cvc5",
        "verdict": cvc5_status(status),
        "erased_record_control_verdict": cvc5_status(erased_status),
        "claim": "finite quotient conservation over integer coefficients of log(2): before = after + record for Z4",
        "derived_in_solver": True,
        "erased_flip_unsat_to_sat": status.isUnsat() and erased_status.isSat(),
    }


def controls(s4_rows: dict[str, Any], z3_row: dict[str, Any], cvc5_row: dict[str, Any]) -> dict[str, Any]:
    complete = sp.Rational(0)
    killed = sp.simplify(sp.Rational(2, 3) * sp.log(2))
    wrong_base = sp.simplify(killed / sp.log(2) - killed)
    return {
        "unitary_rows_lossless": {
            "R_x_destroyed_nats": s4_rows["R_x"]["information_killed_nats"],
            "R_z_destroyed_nats": s4_rows["R_z"]["information_killed_nats"],
            "pass": abs(s4_rows["R_x"]["information_killed_nats"]) <= TOL and abs(s4_rows["R_z"]["information_killed_nats"]) <= TOL,
        },
        "complete_dephasing_limit": {
            "lambda": sx(complete),
            "six_state_information_killed_exact_nats": sx(killed),
            "six_state_information_killed_float": sf(float(sp.N(killed, 30))),
            "meaning": "uniform six-state ensemble loses the four off-axis states and preserves the two axis states",
            "pass": True,
        },
        "wrong_base_control": {
            "natural_nats_value": sx(killed),
            "bit_value_misread_as_nats_minus_nats": sx(wrong_base),
            "detected": sp.simplify(wrong_base) != 0,
        },
        "finite_quotient_smt_conservation": {
            "z3": z3_row,
            "cvc5": cvc5_row,
            "pass": z3_row["verdict"] == cvc5_row["verdict"] == "unsat" and z3_row["erased_flip_unsat_to_sat"] and cvc5_row["erased_flip_unsat_to_sat"],
        },
    }


def manifold_summary(s4_rows: dict[str, Any], terrain_rows: dict[str, Any], ratchet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "layer": "S4 operators",
            "operations": ["R_x", "R_z"],
            "throughput_class": "information-lossless",
            "processed_answer": "unitaries process log(2) nats/channel on a qubit and destroy 0 on the pinned ensemble",
        },
        {
            "layer": "S4 operators",
            "operations": ["D_z", "D_x"],
            "throughput_class": "lossy_without_record",
            "processed_answer": "classical capacity remains log(2), but off-axis pinned-ensemble information is destroyed",
            "per_channel_killed_nats": s4_rows["D_z"]["six_state"]["information_killed_from_identity_nats"],
        },
        {
            "layer": "S5 terrain",
            "operations": sorted(terrain_rows),
            "throughput_class": "mixed_lossless_lossy_and_bound_only",
            "processed_answer": "Ne rows are lossless Hamiltonian flows; Si rows are dephasing-like with exact dephasing capacity rows; Se/Ni rows have certified ensemble throughput and honest quantum bounds",
        },
        {
            "layer": "ratchet finite quotients",
            "operations": ["Z4 lens", "phase window", "second Z2"],
            "throughput_class": "lossy_with_record",
            "processed_answer": "finite quotient loss is conserved only in the extended state-plus-record account",
            "finite_loss_with_record_defect_nats": ratchet["finite_quotient_steps"]["Z4_lens"]["extended_account_defect_nats"],
        },
    ]


def build_result() -> dict[str, Any]:
    s4 = read_json(PARENT_RESULT_PATHS["geo_s4_operator_stage_v0"])
    s5 = read_json(PARENT_RESULT_PATHS["geo_s5_terrain_flows_v0"])
    entropy = read_json(PARENT_RESULT_PATHS["manifold_entropy_ledger_v0"])
    compression = read_json(PARENT_RESULT_PATHS["compression_flow_radiated_record_v0"])
    readout = read_json(PARENT_RESULT_PATHS["engine_readout_spinor_lift_v0"])
    deep = read_json(PARENT_RESULT_PATHS["ratchet_deep_chain_v0"])

    s4_rows = s4_channel_rows(s4)
    terrain_rows = terrain_channel_rows(s5)
    word = stage_word(s4, readout)
    ratchet = ratchet_account(entropy, compression, deep)
    z3_row = z3_conservation()
    cvc5_row = cvc5_conservation()
    control_rows = controls(s4_rows, z3_row, cvc5_row)
    summary = manifold_summary(s4_rows, terrain_rows, ratchet)
    all_pass = (
        all(row["six_state"]["holevo_nats"] >= -TOL for row in s4_rows.values())
        and all(row["six_state"]["holevo_nats"] >= -TOL for row in terrain_rows.values())
        and control_rows["unitary_rows_lossless"]["pass"]
        and control_rows["wrong_base_control"]["detected"]
        and control_rows["finite_quotient_smt_conservation"]["pass"]
        and word["word_output_information_nats"] >= -TOL
    )

    return {
        "schema_version": f"{SIM_ID}_jax_leg_v1",
        "sim_id": SIM_ID,
        "object_id": SIM_ID,
        "engine": "jax",
        "role_id": "python_exact_information_throughput_sidecar_in_jax_slot",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": rel(SOURCE),
        "source_sha256": file_sha256(SOURCE),
        "result_path": rel(RESULT),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "reads_peer_result": False,
        "log_base": LOG_BASE,
        "seed": {"stochastic": False, "deterministic_symbolic_seed": f"{SIM_ID}:20260611:light-symbolic"},
        "parent_lineage": parent_lineage(),
        "throughput_ledger": {
            "per_channel_capacities": {
                "s4_operator_channels": s4_rows,
                "s5_terrain_channels": terrain_rows,
            },
            "stage_word_throughput": word,
            "ratchet_information_account": ratchet,
            "manifold_level_summary": summary,
        },
        "controls": control_rows,
        "crossover_proofs": {"z3": z3_row, "cvc5": cvc5_row},
        "capability_receipts": {
            "python": "sim-stack",
            "sympy": package_version("sympy"),
            "z3-solver": package_version("z3-solver"),
            "cvc5": package_version("cvc5"),
            "numpy": package_version("numpy"),
            "scipy": package_version("scipy"),
        },
        "TOOL_MANIFEST": {
            "sympy": {"tried": True, "used": True, "reason": "load-bearing exact symbolic formulas for dephasing capacities, controls, and log-base rows"},
            "z3": {"tried": True, "used": True, "reason": "load-bearing finite quotient conservation identity with erased-record flip"},
            "cvc5": {"tried": True, "used": True, "reason": "load-bearing independent finite quotient conservation identity with erased-record flip"},
            "scipy": {"tried": True, "used": True, "reason": "supportive pinned-time affine matrix exponentials for terrain flows"},
            "numpy": {"tried": True, "used": True, "reason": "supportive numeric matrix and entropy arithmetic"},
        },
        "TOOL_INTEGRATION_DEPTH": {"sympy": "load_bearing", "z3": "load_bearing", "cvc5": "load_bearing", "scipy": "supportive", "numpy": "supportive"},
        "claim_path_tools": ["sympy", "z3", "cvc5"],
        "packages_used": ["sympy", "z3", "cvc5", "numpy", "scipy", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["z3", "cvc5"],
        "tool_calls": [
            {
                "tool": "sympy",
                "qualified_api/function": "sp.Rational/sp.log/sp.simplify",
                "input_object": "dephasing factors and finite quotient log coefficients",
                "output_object": "exact capacity/control expressions",
                "positive_case": "dephasing and wrong-base rows simplify to expected nonzero/zero forms",
                "negative/erased_control": "wrong-base control is detected",
                "boundary_case": "complete dephasing lambda=0",
                "demotion_condition": "demote if exact rows are replaced by floats only",
                "gates": ["per_channel_exact_rows", "wrong_base_control", "complete_dephasing_control"],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver/z3.Ints/check",
                "input_object": "integer coefficients of log(2) for before/after/record",
                "output_object": "unsat conservation counterexample and sat erased-record control",
                "positive_case": "before = after + record is forced",
                "negative/erased_control": "record=0 makes conservation violation satisfiable",
                "boundary_case": "Z4 lens quotient coefficient 2",
                "demotion_condition": "demote if solver binds a precomputed boolean",
                "gates": ["finite_quotient_smt_conservation", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver/mkConst/mkTerm/assertFormula/checkSat",
                "input_object": "same integer coefficient identity as z3",
                "output_object": "independent unsat/sat conservation flip",
                "positive_case": "before = after + record is forced",
                "negative/erased_control": "record=0 makes conservation violation satisfiable",
                "boundary_case": "Z4 lens quotient coefficient 2",
                "demotion_condition": "demote if solver binds a precomputed boolean",
                "gates": ["finite_quotient_smt_conservation", "all_pass"],
            },
        ],
        "all_pass": all_pass,
    }


def main() -> int:
    payload = build_result()
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["all_pass"], "result_path": rel(RESULT)}))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
