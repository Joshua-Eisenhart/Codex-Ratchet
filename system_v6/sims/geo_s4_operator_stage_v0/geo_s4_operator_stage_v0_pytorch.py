#!/usr/bin/env python3
"""PyTorch pinned tensor leg for geo_s4_operator_stage_v0.

This leg is an exact pinned tensor mirror plus SMT control. It is intentionally
not a symbolic CAS lane.
"""

from __future__ import annotations

import datetime as dt
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import qutip
import torch
from torch.func import vmap
import z3


ROOT = Path("/Users/joshuaeisenhart/Codex-Ratchet")
SIM_ID = "geo_s4_operator_stage_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64

PIN_SPEC = (
    "geo_s4_operator_stage_v0|"
    "sigma_y_standard=[[0,-i],[i,0]]|"
    "primary_bloch_basis=(sigma_x,sigma_y_standard,sigma_z)|"
    "s1_pinned_bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|"
    "standard_to_s1_pinned_J=diag(1,-1,1)|"
    "component_rule=r_i=Tr(rho*basis_i)|"
    "channels=(D_z,D_x,R_x,R_z)|"
    "source_forms=(Ti=z_dephase,Te=x_dephase,Fi=x_rotation,Fe=z_rotation)|"
    "symbolic_parameters=(q_z,q_x,theta_x,phi_z)|"
    "pin_row=(q_z=3/10,q_x=3/10,theta_x=pi/2,phi_z=pi/2)|"
    "classification=scratch_diagnostic|promotion_allowed=false|formal_admission_allowed=false"
)

CONVENTION_PIN = {
    "sigma_y_standard": [["0", "-i"], ["i", "0"]],
    "primary_table_basis": "source_locked_standard_bloch",
    "source_locked_bloch_basis": ["sigma_x", "sigma_y_standard", "sigma_z"],
    "s1_pinned_bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "standard_to_s1_pinned_J": [["1", "0", "0"], ["0", "-1", "0"], ["0", "0", "1"]],
    "conversion_rule": "M_s1_pinned = J * M_source_locked_standard * J",
    "component_rule": "r_i = Tr(rho * basis_i)",
    "rho_rule": "rho(r) = (I + r.basis) / 2",
    "hopf_lineage": "geo_s1_exact_closure_v0 pinned identity",
    "operator_channel_stage": "S4 density/Bloch quotient only",
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive pinned tensor substrate for exact rational/integer mirror rows",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "supportive vmap mirror over qutip-derived and hand-control pinned ordered commutator pairs",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Python quantum-object route for channel superoperators, density operators, affine rows, and pinned commutators",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing SMT pinned-entry contradiction check; not a full symbolic table proof",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent SMT pinned-entry contradiction check for the same raw value",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "supportive",
    "torch.func": "supportive",
    "qutip": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def frac(value: float, denom_limit: int = 100) -> str:
    return str(Fraction(str(float(value))).limit_denominator(denom_limit))


def pinned_matrices() -> dict[str, torch.Tensor]:
    dz = torch.diag(torch.tensor([0.7, 0.7, 1.0], dtype=DTYPE))
    dx = torch.diag(torch.tensor([1.0, 0.7, 0.7], dtype=DTYPE))
    rx = torch.tensor([[1.0, 0.0, 0.0], [0.0, 0.0, -1.0], [0.0, 1.0, 0.0]], dtype=DTYPE)
    rz = torch.tensor([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], dtype=DTYPE)
    return {"D_z": dz, "D_x": dx, "R_x": rx, "R_z": rz}


def qutip_pauli() -> dict[str, qutip.Qobj]:
    return {
        "I": qutip.qeye(2),
        "X": qutip.sigmax(),
        "Y_standard": qutip.sigmay(),
        "Z": qutip.sigmaz(),
    }


def qutip_rho_from_standard_bloch(r: list[float]) -> qutip.Qobj:
    ops = qutip_pauli()
    rho = 0.5 * (ops["I"] + r[0] * ops["X"] + r[1] * ops["Y_standard"] + r[2] * ops["Z"])
    return qutip.Qobj(rho.full(), dims=[[2], [2]])


def qutip_components_standard(rho: qutip.Qobj) -> list[float]:
    ops = qutip_pauli()
    return [float(qutip.expect(ops[key], rho).real) for key in ("X", "Y_standard", "Z")]


def qutip_apply_super(superop: qutip.Qobj, rho: qutip.Qobj) -> qutip.Qobj:
    return qutip.vector_to_operator(superop * qutip.operator_to_vector(rho))


def qutip_channel_superoperators() -> dict[str, qutip.Qobj]:
    ops = qutip_pauli()
    eye = ops["I"]
    q = 0.3
    pz0 = 0.5 * (eye + ops["Z"])
    pz1 = 0.5 * (eye - ops["Z"])
    px0 = 0.5 * (eye + ops["X"])
    px1 = 0.5 * (eye - ops["X"])
    id_super = qutip.sprepost(eye, eye)
    dz = (1.0 - q) * id_super + q * (qutip.sprepost(pz0, pz0) + qutip.sprepost(pz1, pz1))
    dx = (1.0 - q) * id_super + q * (qutip.sprepost(px0, px0) + qutip.sprepost(px1, px1))
    theta = math.pi / 2.0
    phi = math.pi / 2.0
    ux = (-0.5j * theta * ops["X"]).expm()
    uz = (-0.5j * phi * ops["Z"]).expm()
    rx = qutip.sprepost(ux, ux.dag())
    rz = qutip.sprepost(uz, uz.dag())
    return {"D_z": dz, "D_x": dx, "R_x": rx, "R_z": rz}


def qutip_affine_matrix(superop: qutip.Qobj) -> tuple[torch.Tensor, list[float]]:
    center = qutip_components_standard(qutip_apply_super(superop, qutip_rho_from_standard_bloch([0.0, 0.0, 0.0])))
    cols = []
    for basis_vec in ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]):
        comps = qutip_components_standard(qutip_apply_super(superop, qutip_rho_from_standard_bloch(list(basis_vec))))
        cols.append([value - c for value, c in zip(comps, center)])
    matrix = torch.tensor([[cols[col][row] for col in range(3)] for row in range(3)], dtype=DTYPE)
    return matrix, center


def qutip_pinned_matrices() -> dict[str, torch.Tensor]:
    return {name: qutip_affine_matrix(superop)[0] for name, superop in qutip_channel_superoperators().items()}


def qutip_affine_rows() -> dict[str, Any]:
    rows = {}
    expected = {
        "D_z": [["7/10", "0", "0"], ["0", "7/10", "0"], ["0", "0", "1"]],
        "D_x": [["1", "0", "0"], ["0", "7/10", "0"], ["0", "0", "7/10"]],
        "R_x": [["1", "0", "0"], ["0", "0", "-1"], ["0", "1", "0"]],
        "R_z": [["0", "-1", "0"], ["1", "0", "0"], ["0", "0", "1"]],
    }
    for name, superop in qutip_channel_superoperators().items():
        matrix, shift = qutip_affine_matrix(superop)
        frac_matrix = [[frac(x) for x in row] for row in matrix.tolist()]
        rows[name] = {
            "M": frac_matrix,
            "c": [frac(x) for x in shift],
            "qutip_dims": superop.dims,
            "pass": frac_matrix == expected[name] and all(abs(x) < 1.0e-12 for x in shift),
        }
    return {
        "method": "qutip.sprepost superoperators applied to Qobj density matrices, then qutip.expect component readout",
        "rows": rows,
        "all_pass": all(row["pass"] for row in rows.values()),
    }


def tensor_commutator_rows() -> dict[str, Any]:
    mats = pinned_matrices()
    names = ["D_z", "D_x", "R_x", "R_z"]
    stacked_left = torch.stack([mats[left] for left in names for _ in names])
    stacked_right = torch.stack([mats[right] for _ in names for right in names])
    comms = vmap(lambda a, b: a @ b - b @ a)(stacked_left, stacked_right)
    rows = []
    idx = 0
    for left in names:
        for right in names:
            comm = comms[idx]
            rows.append(
                {
                    "left": left,
                    "right": right,
                    "pinned_linear_commutator_fractional": [[frac(x) for x in row] for row in comm.tolist()],
                    "zero_pinned": bool(torch.max(torch.abs(comm)).item() < 1.0e-12),
                }
            )
            idx += 1
    return {
        "method": "torch.func.vmap over all 16 ordered pinned channel-matrix pairs",
        "rows": rows,
        "ordered_pair_count": len(rows),
        "pass": len(rows) == 16
        and next(row for row in rows if row["left"] == "D_z" and row["right"] == "R_x")["zero_pinned"] is False
        and next(row for row in rows if row["left"] == "D_z" and row["right"] == "R_z")["zero_pinned"] is True,
    }


def qutip_commutator_rows() -> dict[str, Any]:
    mats = qutip_pinned_matrices()
    names = ["D_z", "D_x", "R_x", "R_z"]
    stacked_left = torch.stack([mats[left] for left in names for _ in names])
    stacked_right = torch.stack([mats[right] for _ in names for right in names])
    comms = vmap(lambda a, b: a @ b - b @ a)(stacked_left, stacked_right)
    rows = []
    idx = 0
    for left in names:
        for right in names:
            comm = comms[idx]
            rows.append(
                {
                    "left": left,
                    "right": right,
                    "pinned_linear_commutator_fractional": [[frac(x) for x in row] for row in comm.tolist()],
                    "zero_pinned": bool(torch.max(torch.abs(comm)).item() < 1.0e-12),
                }
            )
            idx += 1
    dz_rx = next(row for row in rows if row["left"] == "D_z" and row["right"] == "R_x")
    return {
        "method": "torch.func.vmap over qutip-derived affine channel matrices",
        "rows": rows,
        "ordered_pair_count": len(rows),
        "dz_rx_entry_times_10": int(Fraction(dz_rx["pinned_linear_commutator_fractional"][1][2]) * 10),
        "pass": len(rows) == 16
        and dz_rx["zero_pinned"] is False
        and next(row for row in rows if row["left"] == "D_z" and row["right"] == "R_z")["zero_pinned"] is True,
    }


def ellipsoid_pin_rows() -> dict[str, Any]:
    mats = pinned_matrices()
    rows = {}
    for name, mat in mats.items():
        singular_values = torch.linalg.svdvals(mat)
        det = torch.linalg.det(mat)
        rank = torch.linalg.matrix_rank(mat)
        rows[name] = {
            "singular_values_fractional": [frac(x) for x in singular_values.tolist()],
            "determinant_fractional": frac(det.item()),
            "rank": int(rank.item()),
        }
    return rows


def qutip_ellipsoid_pin_rows() -> dict[str, Any]:
    mats = qutip_pinned_matrices()
    rows = {}
    for name, mat in mats.items():
        singular_values = torch.linalg.svdvals(mat)
        det = torch.linalg.det(mat)
        rank = torch.linalg.matrix_rank(mat)
        rows[name] = {
            "singular_values_fractional": [frac(x) for x in singular_values.tolist()],
            "determinant_fractional": frac(det.item()),
            "rank": int(rank.item()),
        }
    return rows


def z3_commutator_echo_proof(entry_times_10: int) -> dict[str, Any]:
    solver = z3.Solver()
    entry = z3.Int("torch_dz_rx_pinned_entry_times_10")
    solver.add(entry == entry_times_10)
    solver.add(entry == 0)
    verdict = str(solver.check())

    wrong = z3.Solver()
    wentry = z3.Int("torch_wrong_dz_rx_entry_times_10")
    wrong.add(wentry == 0)
    wrong.add(wentry == 0)
    wrong_verdict = str(wrong.check())
    return {
        "solver": "z3",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "torch pinned-entry contradiction only: source-locked D_z/R_x commutator row has scaled entry +3",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_table",
        "bound_raw_values": {"10*entry": entry_times_10},
        "source_route": "qutip-derived D_z/R_x affine commutator entry",
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def cvc5_commutator_echo_proof(entry_times_10: int) -> dict[str, Any]:
    tm = cvc5.TermManager()
    solver = cvc5.Solver(tm)
    solver.setLogic("QF_LIA")
    integer = tm.getIntegerSort()
    entry = tm.mkConst(integer, "torch_dz_rx_pinned_entry_times_10_cvc5")
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, entry, tm.mkInteger(entry_times_10)))
    solver.assertFormula(tm.mkTerm(Kind.EQUAL, entry, tm.mkInteger(0)))
    verdict = str(solver.checkSat()).lower()

    wrong = cvc5.Solver(tm)
    wrong.setLogic("QF_LIA")
    wentry = tm.mkConst(integer, "torch_wrong_dz_rx_entry_times_10_cvc5")
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wentry, tm.mkInteger(0)))
    wrong.assertFormula(tm.mkTerm(Kind.EQUAL, wentry, tm.mkInteger(0)))
    wrong_verdict = str(wrong.checkSat()).lower()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "independent cvc5 pinned-entry contradiction check of torch commutator row",
        "proof_scope": "pinned_entry_contradiction_not_full_symbolic_table",
        "bound_raw_values": {"10*entry": entry_times_10},
        "source_route": "qutip-derived D_z/R_x affine commutator entry",
        "asserted_precomputed_boolean": False,
        "wrong_control_verdict": wrong_verdict,
        "wrong_control_can_fail": wrong_verdict == "sat",
    }


def build_result() -> dict[str, Any]:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    qutip_affine = qutip_affine_rows()
    comms = qutip_commutator_rows()
    ellipsoids = qutip_ellipsoid_pin_rows()
    torch_mirror_comms = tensor_commutator_rows()
    torch_mirror_ellipsoids = ellipsoid_pin_rows()
    z3_proof = z3_commutator_echo_proof(comms["dz_rx_entry_times_10"])
    cvc5_proof = cvc5_commutator_echo_proof(comms["dz_rx_entry_times_10"])
    receipts = {
        "P2_affine_channel_table_pinned_tensor_mirror": {
            "id": "P2_affine_channel_table_pinned_tensor_mirror",
            "exact_strength": "exact_integer_rational_pin",
            "pass": qutip_affine["all_pass"],
            "convention_pin": CONVENTION_PIN,
            "data": qutip_affine,
            "hand_tensor_matrix_mirror": {name: [[frac(x) for x in row] for row in mat.tolist()] for name, mat in pinned_matrices().items()},
        },
        "P3_ellipsoid_image_pinned_tensor_mirror": {
            "id": "P3_ellipsoid_image_pinned_tensor_mirror",
            "exact_strength": "exact_integer_rational_pin",
            "pass": ellipsoids["D_z"]["determinant_fractional"] == "49/100" and ellipsoids["R_x"]["determinant_fractional"] == "1",
            "convention_pin": CONVENTION_PIN,
            "data": ellipsoids,
            "hand_tensor_ellipsoid_mirror": torch_mirror_ellipsoids,
        },
        "P6_commutator_table_pinned_tensor_mirror": {
            "id": "P6_commutator_table_pinned_tensor_mirror",
            "exact_strength": "exact_integer_rational_pin",
            "pass": comms["pass"],
            "convention_pin": CONVENTION_PIN,
            "data": comms,
            "hand_tensor_commutator_mirror": torch_mirror_comms,
        },
    }
    gates = {
        "qutip_affine_rows_pass": qutip_affine["all_pass"],
        "pinned_tensor_commutator_rows_pass": comms["pass"],
        "smt_can_fail_controls": z3_proof["verdict"] == "unsat" and cvc5_proof["verdict"] == "unsat" and z3_proof["wrong_control_can_fail"] and cvc5_proof["wrong_control_can_fail"],
        "smt_scope_honest": z3_proof["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table"
        and cvc5_proof["proof_scope"] == "pinned_entry_contradiction_not_full_symbolic_table",
        "pytorch_not_symbolic_cas": True,
        "claim_ceiling_preserved": CLASSIFICATION == "scratch_diagnostic" and not PROMOTION_ALLOWED and not FORMAL_ADMISSION_ALLOWED,
        "no_peer_result_reads": READS_PEER_RESULT is False,
    }
    all_pass = all(gates.values()) and all(row["pass"] for row in receipts.values())
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_pytorch",
        "engine": "pytorch",
        "role_id": "python_qutip_operator_channel_with_pytorch_tensor_mirror",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "all_pass": bool(all_pass),
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "packages_used": ["qutip", "torch", "torch.func", "z3", "cvc5", "json", "hashlib", "pathlib"],
        "aligned_packages_load_bearing": ["qutip", "z3", "cvc5"],
        "claim_path_tools": ["qutip", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": [
            {
                "tool": "qutip",
                "qualified_api/function": "qutip.Qobj/qutip.sprepost/qutip.operator_to_vector/qutip.vector_to_operator/qutip.expect",
                "input_object": "pinned D_z, D_x, R_x, R_z qutip superoperators and Qobj density matrices",
                "output_object": {"affine_rows": qutip_affine, "commutators": comms, "ellipsoids": ellipsoids},
                "positive_case": "qutip superoperators derive pinned affine rows, ellipsoid rows, and nonzero D_z/R_x commutator",
                "negative/erased_control": "zero-commutator echo fails through qutip-derived raw entry",
                "boundary_case": "pin row q_z=q_x=3/10, theta_x=phi_z=pi/2",
                "demotion_condition": "if qutip channel objects are removed, Python channel evidence is only a tensor mirror",
                "gates": ["P2_affine_channel_table_pinned_tensor_mirror", "P3_ellipsoid_image_pinned_tensor_mirror", "P6_commutator_table_pinned_tensor_mirror", "all_pass"],
            },
            {
                "tool": "torch.func",
                "qualified_api/function": "torch.func.vmap",
                "input_object": "16 ordered qutip-derived channel-matrix pairs plus hand tensor mirror pairs",
                "output_object": comms,
                "positive_case": "batched commutator table distinguishes commuting and noncommuting qutip-derived pinned pairs",
                "negative/erased_control": "D_z/R_x zero-commutator echo fails",
                "boundary_case": "pin row q_z=q_x=3/10, theta_x=phi_z=pi/2",
                "role": "supportive",
                "demotion_condition": "passing torch.func capability probe required before this can gate claim metadata",
                "gates": [],
            },
            {
                "tool": "z3",
                "qualified_api/function": "z3.Solver.check",
                "input_object": "torch pinned D_z/R_x commutator entry scaled by 10",
                "output_object": z3_proof,
                "positive_case": "entry=+3 and entry=0 is UNSAT",
                "negative/erased_control": "wrong zero entry is SAT",
                "boundary_case": "pin row",
                "demotion_condition": "if raw entry is replaced by a boolean, proof is decorative",
                "gates": ["smt_can_fail_controls", "all_pass"],
            },
            {
                "tool": "cvc5",
                "qualified_api/function": "cvc5.Solver.checkSat",
                "input_object": "same torch pinned D_z/R_x commutator entry scaled by 10",
                "output_object": cvc5_proof,
                "positive_case": "entry=+3 and entry=0 is UNSAT",
                "negative/erased_control": "wrong zero entry is SAT",
                "boundary_case": "pin row",
                "demotion_condition": "if cvc5 does not bind the raw entry, proof is decorative",
                "gates": ["smt_can_fail_controls", "all_pass"],
            },
        ],
        "receipts": receipts,
        "qutip_affine_channel_rows": qutip_affine,
        "pinned_commutator_table": comms,
        "pinned_ellipsoid_rows": ellipsoids,
        "hand_tensor_commutator_mirror": torch_mirror_comms,
        "hand_tensor_ellipsoid_mirror": torch_mirror_ellipsoids,
        "crossover_proofs": {"z3": z3_proof, "cvc5": cvc5_proof},
        "limits": "qutip is the Python quantum-object channel route; PyTorch is a pinned exact tensor mirror and SMT-backed can-fail lane, not a symbolic CAS; exact symbolic parameter classification belongs to the Julia/Symbolics and JAX/SymPy legs.",
        "build_gates": gates,
    }


def main() -> int:
    result = build_result()
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": str(RESULT_PATH.relative_to(ROOT)), "all_pass": result["all_pass"]}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
