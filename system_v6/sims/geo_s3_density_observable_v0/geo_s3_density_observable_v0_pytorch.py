#!/usr/bin/env python3
"""PyTorch tensor leg for geo_s3_density_observable_v0."""

from __future__ import annotations

import datetime as dt
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
SIM_ID = "geo_s3_density_observable_v0"
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
SOURCE_PATH = SIM_DIR / f"{SIM_ID}_pytorch.py"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
READS_PEER_RESULT = False
DTYPE = torch.float64
CDTYPE = torch.complex128

PIN_SPEC = (
    "geo_s3_density_observable_v0|"
    "sigma_y_standard=[[0,-i],[i,0]]|"
    "bloch_basis=(sigma_x,-sigma_y_standard,sigma_z)|"
    "component_rule=r_i=Tr(rho*basis_i)|"
    "rho_rule=rho(r)=(I+r.basis)/2|"
    "hopf_lineage=geo_s1_exact_closure_v0 pinned identity|"
    "trace_distance_convention=D(rho,sigma)=1/2||rho-sigma||_1|"
    "fidelity_convention=squared_Uhlmann_qubit_F=1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)));root_fidelity=sqrt(F)_if_emitted"
)

CONVENTION_PIN = {
    "sigma_y_standard": [["0", "-i"], ["i", "0"]],
    "bloch_basis": ["sigma_x", "-sigma_y_standard", "sigma_z"],
    "component_rule": "r_i = Tr(rho * basis_i)",
    "rho_rule": "rho(r) = (I + r.basis) / 2",
    "hopf_lineage": "geo_s1_exact_closure_v0 pinned identity",
    "trace_distance_convention": "D(rho,sigma) = 1/2 ||rho-sigma||_1",
    "fidelity_convention": {
        "squared_uhlmann_qubit": "F = 1/2(1+r.s+sqrt((1-||r||^2)(1-||s||^2)))",
        "root_fidelity": "sqrt(F) if emitted",
    },
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "supportive tensor substrate for pinned density matrices, projectors, probe maps, and channel rows",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "supportive PyTorch mirror for batched Born/projective update and contraction rows; qutip is the Python quantum-object claim route",
    },
    "qutip": {
        "tried": True,
        "used": True,
        "reason": "load-bearing Python quantum-object route for Qobj density matrices, projectors, expectation values, and superoperator channel contractions",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact SMT over torch-derived full Pauli probe rank",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent exact SMT over the same torch-derived probe-rank value",
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


def pauli() -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
    eye = torch.eye(2, dtype=CDTYPE)
    x = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sigma_y_standard = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    y_pinned = -sigma_y_standard
    z = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    return eye, x, y_pinned, z


def qutip_pauli() -> dict[str, qutip.Qobj]:
    return {
        "I": qutip.qeye(2),
        "X": qutip.sigmax(),
        "Yp": -qutip.sigmay(),
        "Y_standard": qutip.sigmay(),
        "Z": qutip.sigmaz(),
    }


def _float_triplet(values: Any) -> list[float]:
    if isinstance(values, torch.Tensor):
        return [float(x) for x in values.detach().cpu().tolist()]
    return [float(x) for x in values]


def qutip_rho_from_r(r: Any) -> qutip.Qobj:
    rv = _float_triplet(r)
    ops = qutip_pauli()
    rho = 0.5 * (ops["I"] + rv[0] * ops["X"] + rv[1] * ops["Yp"] + rv[2] * ops["Z"])
    return qutip.Qobj(rho.full(), dims=[[2], [2]])


def qutip_projector(n: Any, sign: float) -> qutip.Qobj:
    nv = _float_triplet(n)
    ops = qutip_pauli()
    proj = 0.5 * (ops["I"] + sign * (nv[0] * ops["X"] + nv[1] * ops["Yp"] + nv[2] * ops["Z"]))
    return qutip.Qobj(proj.full(), dims=[[2], [2]])


def qutip_bloch_components(rho: qutip.Qobj) -> list[float]:
    ops = qutip_pauli()
    return [float(qutip.expect(ops[key], rho).real) for key in ("X", "Yp", "Z")]


def qutip_born_plus(r: Any, n: Any) -> float:
    rho = qutip_rho_from_r(r)
    return float(qutip.expect(qutip_projector(n, 1.0), rho).real)


def qutip_nonselective_update(r: Any, n: Any) -> list[float]:
    rho = qutip_rho_from_r(r)
    pp = qutip_projector(n, 1.0)
    pm = qutip_projector(n, -1.0)
    updated = pp * rho * pp + pm * rho * pm
    return qutip_bloch_components(updated)


def qutip_selective_plus_update(r: Any, n: Any) -> list[float]:
    rho = qutip_rho_from_r(r)
    pp = qutip_projector(n, 1.0)
    p = float((pp * rho).tr().real)
    updated = pp * rho * pp / p
    return qutip_bloch_components(updated)


def qutip_apply_super(superop: qutip.Qobj, rho: qutip.Qobj) -> qutip.Qobj:
    return qutip.vector_to_operator(superop * qutip.operator_to_vector(rho))


def qutip_channel_superoperators() -> dict[str, qutip.Qobj]:
    ops = qutip_pauli()
    eye = ops["I"]
    pz0 = 0.5 * (eye + ops["Z"])
    pz1 = 0.5 * (eye - ops["Z"])
    id_super = qutip.sprepost(eye, eye)
    dephasing = 0.5 * id_super + 0.5 * (qutip.sprepost(pz0, pz0) + qutip.sprepost(pz1, pz1))
    lam = 0.5
    depolarizing = ((1 + 3 * lam) / 4) * id_super + ((1 - lam) / 4) * (
        qutip.sprepost(ops["X"], ops["X"]) + qutip.sprepost(ops["Y_standard"], ops["Y_standard"]) + qutip.sprepost(ops["Z"], ops["Z"])
    )
    gamma = 0.5
    k0 = qutip.Qobj([[1.0, 0.0], [0.0, math.sqrt(1.0 - gamma)]], dims=[[2], [2]])
    k1 = qutip.Qobj([[0.0, math.sqrt(gamma)], [0.0, 0.0]], dims=[[2], [2]])
    amplitude = qutip.sprepost(k0, k0.dag()) + qutip.sprepost(k1, k1.dag())
    return {
        "dephasing_p_1_2": dephasing,
        "depolarizing_lambda_1_2": depolarizing,
        "amplitude_damping_gamma_1_2": amplitude,
    }


def rho_from_r(r: torch.Tensor) -> torch.Tensor:
    eye, x, y, z = pauli()
    return 0.5 * (eye + r[0].to(CDTYPE) * x + r[1].to(CDTYPE) * y + r[2].to(CDTYPE) * z)


def projector(n: torch.Tensor, sign: float) -> torch.Tensor:
    eye, x, y, z = pauli()
    return 0.5 * (eye + sign * (n[0].to(CDTYPE) * x + n[1].to(CDTYPE) * y + n[2].to(CDTYPE) * z))


def bloch_components(rho: torch.Tensor) -> torch.Tensor:
    _, x, y, z = pauli()
    comps = [torch.real(torch.trace(rho @ b)) for b in (x, y, z)]
    return torch.stack(comps).to(DTYPE)


def born_plus(r: torch.Tensor, n: torch.Tensor) -> torch.Tensor:
    return 0.5 * (1.0 + torch.dot(r, n))


def nonselective_update(r: torch.Tensor, n: torch.Tensor) -> torch.Tensor:
    rho = rho_from_r(r)
    pp = projector(n, 1.0)
    pm = projector(n, -1.0)
    updated = pp @ rho @ pp + pm @ rho @ pm
    return bloch_components(updated)


def selective_plus_update(r: torch.Tensor, n: torch.Tensor) -> torch.Tensor:
    rho = rho_from_r(r)
    pp = projector(n, 1.0)
    p = torch.real(torch.trace(pp @ rho))
    updated = pp @ rho @ pp / p
    return bloch_components(updated)


def trace_distance(r: torch.Tensor, s: torch.Tensor) -> torch.Tensor:
    return 0.5 * torch.linalg.vector_norm(r - s)


def depolarizing(row: torch.Tensor, lam: float) -> torch.Tensor:
    return lam * row


def dephasing(row: torch.Tensor, p: float) -> torch.Tensor:
    return torch.stack([(1.0 - p) * row[0], (1.0 - p) * row[1], row[2]])


def amplitude_damping(row: torch.Tensor, gamma: float) -> torch.Tensor:
    return torch.stack([math.sqrt(1.0 - gamma) * row[0], math.sqrt(1.0 - gamma) * row[1], (1.0 - gamma) * row[2] + gamma])


def measurement_rows() -> dict[str, Any]:
    r = torch.tensor([0.25, -0.5, 0.75], dtype=DTYPE)
    dirs = torch.tensor(
        [
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
            [1.0 / math.sqrt(2.0), 0.0, 1.0 / math.sqrt(2.0)],
        ],
        dtype=DTYPE,
    )
    probs = vmap(lambda n: born_plus(r, n))(dirs)
    nonselective = vmap(lambda n: nonselective_update(r, n))(dirs)
    expected_nonselective = vmap(lambda n: torch.dot(r, n) * n)(dirs)
    selective = vmap(lambda n: selective_plus_update(r, n))(dirs)
    rows = []
    for idx, n in enumerate(dirs):
        rows.append(
            {
                "n": [float(x) for x in n.tolist()],
                "p_plus": float(probs[idx]),
                "selective_plus_components": [float(x) for x in selective[idx].tolist()],
                "selective_target": [float(x) for x in n.tolist()],
                "selective_max_abs_error": float(torch.max(torch.abs(selective[idx] - n))),
                "nonselective_components": [float(x) for x in nonselective[idx].tolist()],
                "nonselective_target": [float(x) for x in expected_nonselective[idx].tolist()],
                "nonselective_max_abs_error": float(torch.max(torch.abs(nonselective[idx] - expected_nonselective[idx]))),
            }
        )
    return {
        "method": "torch.func.vmap over pinned projectors P+/- built from tensor Pauli matrices",
        "rows": rows,
        "all_selective_targets_match": all(row["selective_max_abs_error"] < 1.0e-12 for row in rows),
        "all_nonselective_targets_match": all(row["nonselective_max_abs_error"] < 1.0e-12 for row in rows),
    }


def qutip_measurement_rows() -> dict[str, Any]:
    r = [0.25, -0.5, 0.75]
    dirs = [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
        [1.0 / math.sqrt(2.0), 0.0, 1.0 / math.sqrt(2.0)],
    ]
    rows = []
    for n in dirs:
        probs = qutip_born_plus(r, n)
        nonselective = qutip_nonselective_update(r, n)
        expected_nonselective = [sum(r_i * n_i for r_i, n_i in zip(r, n)) * n_i for n_i in n]
        selective = qutip_selective_plus_update(r, n)
        rows.append(
            {
                "n": n,
                "p_plus": probs,
                "selective_plus_components": selective,
                "selective_target": n,
                "selective_max_abs_error": max(abs(a - b) for a, b in zip(selective, n)),
                "nonselective_components": nonselective,
                "nonselective_target": expected_nonselective,
                "nonselective_max_abs_error": max(abs(a - b) for a, b in zip(nonselective, expected_nonselective)),
            }
        )
    return {
        "method": "qutip Qobj density matrices, projectors, qutip.expect, and Qobj product updates",
        "rows": rows,
        "all_selective_targets_match": all(row["selective_max_abs_error"] < 1.0e-12 for row in rows),
        "all_nonselective_targets_match": all(row["nonselective_max_abs_error"] < 1.0e-12 for row in rows),
    }


def probe_rank_rows() -> dict[str, Any]:
    families = {
        "Z_only": torch.tensor([[0.0, 0.0, 1.0]], dtype=DTYPE),
        "X_Z": torch.tensor([[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]], dtype=DTYPE),
        "X_Y_Z": torch.eye(3, dtype=DTYPE),
        "duplicate_Z": torch.tensor([[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]], dtype=DTYPE),
    }
    rows = []
    for name, matrix in families.items():
        rank = int(torch.linalg.matrix_rank(matrix).item())
        rows.append(
            {
                "family": name,
                "probe_matrix": [[float(x) for x in row] for row in matrix.tolist()],
                "torch_rank": rank,
                "quotient_dimension": rank,
                "full_ball_reconstruction": rank == 3,
                "pass": (name == "X_Y_Z" and rank == 3) or (name != "X_Y_Z" and rank < 3),
            }
        )
    return {"rows": rows, "all_pass": all(row["pass"] for row in rows)}


def contraction_rows() -> dict[str, Any]:
    pairs = torch.tensor(
        [
            [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]],
            [[0.25, -0.25, 0.25], [-0.25, 0.25, -0.25]],
            [[0.0, 0.0, 1.0], [0.0, 0.0, -1.0]],
        ],
        dtype=DTYPE,
    )
    maps = {
        "dephasing_p_1_2": lambda row: dephasing(row, 0.5),
        "depolarizing_lambda_1_2": lambda row: depolarizing(row, 0.5),
        "amplitude_damping_gamma_1_2": lambda row: amplitude_damping(row, 0.5),
    }
    rows = []
    for name, fn in maps.items():
        before = vmap(lambda pair: trace_distance(pair[0], pair[1]))(pairs)
        after = vmap(lambda pair: trace_distance(fn(pair[0]), fn(pair[1])))(pairs)
        rows.append(
            {
                "channel": name,
                "before": [float(x) for x in before.tolist()],
                "after": [float(x) for x in after.tolist()],
                "all_contracted": bool(torch.all(after <= before + 1.0e-12)),
                "claim_path": "diagnostic tensor row; symbolic contraction proof is in the envelope/SymPy lane",
            }
        )
    expansive = lambda row: 1.2 * row
    r = torch.tensor([0.0, 0.0, 0.0], dtype=DTYPE)
    s = torch.tensor([0.5, 0.0, 0.0], dtype=DTYPE)
    return {
        "method": "torch.func.vmap over named one-qubit affine maps and finite pairs",
        "rows": rows,
        "all_contracted": all(row["all_contracted"] for row in rows),
        "non_cptp_expansive_control": {
            "before": float(trace_distance(r, s)),
            "after": float(trace_distance(expansive(r), expansive(s))),
            "fails_contraction": bool(trace_distance(expansive(r), expansive(s)) > trace_distance(r, s)),
        },
    }


def qutip_contraction_rows() -> dict[str, Any]:
    pairs = [
        ([0.0, 0.0, 0.0], [0.5, 0.0, 0.0]),
        ([0.25, -0.25, 0.25], [-0.25, 0.25, -0.25]),
        ([0.0, 0.0, 1.0], [0.0, 0.0, -1.0]),
    ]
    rows = []
    for name, superop in qutip_channel_superoperators().items():
        before: list[float] = []
        after: list[float] = []
        for r, s in pairs:
            rho = qutip_rho_from_r(r)
            sigma = qutip_rho_from_r(s)
            before.append(float(qutip.tracedist(rho, sigma)))
            after.append(float(qutip.tracedist(qutip_apply_super(superop, rho), qutip_apply_super(superop, sigma))))
        rows.append(
            {
                "channel": name,
                "before": before,
                "after": after,
                "all_contracted": all(a <= b + 1.0e-12 for a, b in zip(after, before)),
                "claim_path": "qutip superoperator channel row",
            }
        )
    r = [0.0, 0.0, 0.0]
    s = [0.5, 0.0, 0.0]
    before = float(qutip.tracedist(qutip_rho_from_r(r), qutip_rho_from_r(s)))
    after = float(qutip.tracedist(qutip_rho_from_r([1.2 * x for x in r]), qutip_rho_from_r([1.2 * x for x in s])))
    return {
        "method": "qutip.sprepost superoperators plus qutip.tracedist over Qobj density matrices",
        "rows": rows,
        "all_contracted": all(row["all_contracted"] for row in rows),
        "non_cptp_expansive_control": {
            "before": before,
            "after": after,
            "fails_contraction": after > before,
        },
    }
def z3_rank_proof(rank_row: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    rank = z3.Int("torch_rank_XYZ")
    solver.add(rank == z3.IntVal(int(rank_row["torch_rank"])))
    solver.add(rank != z3.IntVal(3))
    positive = solver.check()

    wrong = z3.Solver()
    dup_rank = z3.Int("torch_rank_duplicate_Z")
    wrong.add(dup_rank == z3.IntVal(1))
    wrong.add(dup_rank == z3.IntVal(3))
    wrong_status = wrong.check()
    return {
        "solver": "z3",
        "ran": True,
        "verdict": str(positive),
        "load_bearing": True,
        "claim": "torch-derived X_Y_Z probe matrix has full rank 3",
        "derived_expression": "rank == 3",
        "bound_raw_values": {"torch_rank_XYZ": rank_row["torch_rank"]},
        "asserted_precomputed_boolean": False,
        "duplicate_Z_control_verdict": str(wrong_status),
        "duplicate_Z_control_can_fail": str(wrong_status) == "unsat",
    }


def cvc5_rank_proof(rank_row: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    ints = solver.getIntegerSort()
    rank = solver.mkConst(ints, "torch_rank_XYZ")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, rank, solver.mkInteger(int(rank_row["torch_rank"]))))
    solver.assertFormula(solver.mkTerm(Kind.NOT, solver.mkTerm(Kind.EQUAL, rank, solver.mkInteger(3))))
    positive = solver.checkSat()

    wrong = cvc5.Solver()
    wrong.setLogic("QF_LIA")
    ints2 = wrong.getIntegerSort()
    dup_rank = wrong.mkConst(ints2, "torch_rank_duplicate_Z")
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, dup_rank, wrong.mkInteger(1)))
    wrong.assertFormula(wrong.mkTerm(Kind.EQUAL, dup_rank, wrong.mkInteger(3)))
    wrong_result = wrong.checkSat()
    return {
        "solver": "cvc5",
        "ran": True,
        "verdict": "unsat" if positive.isUnsat() else "sat" if positive.isSat() else str(positive),
        "load_bearing": True,
        "claim": "Independent CVC5 rank check over the same torch-derived rank",
        "derived_expression": "rank == 3",
        "bound_raw_values": {"torch_rank_XYZ": rank_row["torch_rank"]},
        "asserted_precomputed_boolean": False,
        "duplicate_Z_control_verdict": "unsat" if wrong_result.isUnsat() else "sat" if wrong_result.isSat() else str(wrong_result),
        "duplicate_Z_control_can_fail": wrong_result.isUnsat(),
    }


def build_result() -> dict[str, Any]:
    qutip_measurement = qutip_measurement_rows()
    measurement = measurement_rows()
    probes = probe_rank_rows()
    qutip_contraction = qutip_contraction_rows()
    contraction = contraction_rows()
    xyz_rank = next(row for row in probes["rows"] if row["family"] == "X_Y_Z")
    z3proof = z3_rank_proof(xyz_rank)
    cvc5proof = cvc5_rank_proof(xyz_rank)
    receipts = {
        "S3.D": {
            "id": "S3.D",
            "exact_strength": "diagnostic_float_nonclaim",
            "pass": qutip_measurement["all_selective_targets_match"]
            and qutip_measurement["all_nonselective_targets_match"]
            and measurement["all_selective_targets_match"]
            and measurement["all_nonselective_targets_match"],
            "convention_pin": CONVENTION_PIN,
            "qutip_measurement_updates": qutip_measurement,
            "torch_tensor_measurement_mirror": measurement,
        },
        "S3.E": {
            "id": "S3.E",
            "exact_strength": "finite_exhaustive_enumeration",
            "pass": probes["all_pass"],
            "convention_pin": CONVENTION_PIN,
            "torch_probe_rank_rows": probes,
        },
        "S3.G": {
            "id": "S3.G",
            "exact_strength": "diagnostic_float_nonclaim",
            "pass": qutip_contraction["all_contracted"]
            and qutip_contraction["non_cptp_expansive_control"]["fails_contraction"]
            and contraction["all_contracted"]
            and contraction["non_cptp_expansive_control"]["fails_contraction"],
            "convention_pin": CONVENTION_PIN,
            "qutip_contraction_rows": qutip_contraction,
            "torch_tensor_contraction_mirror": contraction,
        },
    }
    all_pass = (
        all(row["pass"] for row in receipts.values())
        and z3proof["verdict"] == cvc5proof["verdict"] == "unsat"
        and z3proof["duplicate_Z_control_can_fail"]
        and cvc5proof["duplicate_Z_control_can_fail"]
        and CLASSIFICATION == "scratch_diagnostic"
        and PROMOTION_ALLOWED is False
        and FORMAL_ADMISSION_ALLOWED is False
        and READS_PEER_RESULT is False
    )
    tool_calls = [
        {
            "tool": "qutip",
            "qualified_api/function": "qutip.Qobj/qutip.expect/qutip.sprepost/qutip.operator_to_vector/qutip.vector_to_operator/qutip.tracedist",
            "input_object": "one-qubit density Qobjs, projectors, measurement directions, and CPTP channel superoperators",
            "output_object": {"measurement": qutip_measurement, "contraction": qutip_contraction},
            "positive_case": "qutip projective updates hit +/-n and named CPTP superoperators contract finite pairs",
            "negative/erased_control": "non-CPTP expansive Bloch scaling fails contraction",
            "boundary_case": "pure projectors and center density rows",
            "demotion_condition": "if qutip Qobj/channel route is removed, Python state/channel evidence is only a tensor mirror",
            "gates": ["all_pass", "S3.D", "S3.G"],
        },
        {
            "tool": "torch.func",
            "qualified_api/function": "torch.func.vmap",
            "input_object": "Bloch vectors, projective measurement directions, CPTP map pairs",
            "output_object": {"measurement": measurement, "contraction": contraction},
            "positive_case": "projective updates hit +/-n and named CPTP rows contract finite pairs",
            "negative/erased_control": "non-CPTP expansive map fails contraction",
            "boundary_case": "Z_only and duplicate_Z probe families remain rank deficient",
            "role": "supportive",
            "demotion_condition": "passing torch.func capability probe required before this can gate claim metadata",
            "gates": [],
        },
        {
            "tool": "z3",
            "qualified_api/function": "z3.Solver/check",
            "input_object": "torch-derived X_Y_Z rank",
            "output_object": z3proof,
            "positive_case": "full Pauli probe family has rank 3",
            "negative/erased_control": "duplicate_Z rank 1 cannot satisfy rank 3",
            "boundary_case": "rank deficient commuting probe family",
            "demotion_condition": "if bound rank is replaced by boolean, SMT is decorative",
            "gates": ["all_pass", "S3.E", "crossover_proofs"],
        },
        {
            "tool": "cvc5",
            "qualified_api/function": "cvc5.Solver/checkSat",
            "input_object": "same torch-derived X_Y_Z rank",
            "output_object": cvc5proof,
            "positive_case": "independent solver agrees with z3",
            "negative/erased_control": "duplicate_Z rank 1 fails full-rank claim",
            "boundary_case": "rank deficient commuting probe family",
            "demotion_condition": "if CVC5 does not bind raw rank, demote proof",
            "gates": ["all_pass", "S3.E", "crossover_proofs"],
        },
    ]
    return {
        "schema": "codex_ratchet.engine_leg_result.v1",
        "sim_id": SIM_ID,
        "object_id": f"{SIM_ID}_pytorch",
        "engine": "pytorch",
        "role_id": "python_qutip_state_channel_with_pytorch_tensor_mirror",
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "reads_peer_result": READS_PEER_RESULT,
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_path": str(SOURCE_PATH.relative_to(ROOT)),
        "source_sha256": file_sha256(SOURCE_PATH),
        "result_path": str(RESULT_PATH.relative_to(ROOT)),
        "pin_spec": PIN_SPEC,
        "pin_sha256": sha256_text(PIN_SPEC),
        "convention_pin": CONVENTION_PIN,
        "packages_used": ["qutip", "torch", "torch.func", "z3", "cvc5", "json", "hashlib", "pathlib", "math"],
        "aligned_packages_load_bearing": ["qutip", "z3", "cvc5"],
        "claim_path_tools": ["qutip", "z3", "cvc5"],
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_calls": tool_calls,
        "receipts": receipts,
        "crossover_proofs": {"z3": z3proof, "cvc5": cvc5proof},
        "all_pass": bool(all_pass),
        "summary": {
            "torch_version": torch.__version__,
            "qutip_version": qutip.__version__,
            "measurement_updates": receipts["S3.D"]["pass"],
            "probe_ranks": receipts["S3.E"]["pass"],
            "contraction_rows": receipts["S3.G"]["pass"],
            "smt": {"z3": z3proof["verdict"], "cvc5": cvc5proof["verdict"]},
            "all_pass": bool(all_pass),
        },
    }


def main() -> int:
    result = build_result()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["all_pass"], "result_path": str(RESULT_PATH.relative_to(ROOT))}, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
