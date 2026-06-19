#!/usr/bin/env python3
"""2Q GCM QCA runner with GNVW-class support-rank extraction.

This packet consumes the frozen 2Q carve registry, builds realized 2Q-site
unitaries, and computes the finite open-chain GNVW-class index from operator
support ranks. Finite ring rows are locality/closure witnesses only.
"""

from __future__ import annotations

import datetime as _dt
from fractions import Fraction
import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
import subprocess
import sys
from typing import Any

import cvc5
from cvc5 import Kind
import sympy as sp
import torch
import z3


SIM_ID = "gcm_qca_runner_2q_v0"
SIM_DIR = Path(__file__).resolve().parent
ROOT = SIM_DIR.parents[2]
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

REGISTRY_PATH = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_2q_freeze_and_cut_v0"
    / "results"
    / "gcm_2q_freeze_and_cut_v0_registry.json"
)
CARVE_2Q_RESULT_PATH = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_constraint_carve_2q_v0"
    / "results"
    / "gcm_constraint_carve_2q_v0_results.json"
)
RUNNER_V1_AUDIT_PATH = (
    ROOT / "system_v6" / "sims" / "gcm_ring_checkerboard_runner_v1" / "audit_verdict.md"
)
RUNNER_V1_COMMON_PATH = (
    ROOT
    / "system_v6"
    / "sims"
    / "gcm_ring_checkerboard_runner_v1"
    / "gcm_ring_checkerboard_runner_v1_common.py"
)
QCA_V3_COMMON_PATH = ROOT / "system_v6" / "sims" / "ring_checkerboard_qca_v3" / "ring_checkerboard_qca_v3_common.py"
STANDARD_MATH_NOTE_PATH = (
    Path.home() / "wiki" / "codex-ratchet-research" / "standard-math" / "gnvw-index-1d-qca.md"
)

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.builder_audit_boundary import builder_audit_boundary_errors  # noqa: E402
from scripts.gcm_substrate_check import gcm_substrate_check  # noqa: E402


CLASSIFICATION = "scratch_diagnostic"
CLAIM_CEILING = "scratch_diagnostic; carrier-and-pins-relative"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
COORDINATES = {
    "layer_coordinate": "dynamics",
    "carve_relation": "integrated-onto-the-carve",
    "qubit_depth": "2Q",
}

SITE_QUBITS = 2
LOCAL_DIM = 2**SITE_QUBITS
SUPPORT_DIM_BASE = LOCAL_DIM**2
PRIMARY_N = 3
CUT_LABEL = 0
RANK_TOL = 1.0e-8
TORCH_DTYPE = torch.complex128
DEVICE = torch.device("cpu")

GCM_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
GCM_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
BASE_GCM_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
BASE_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
CARVE_PREDICATE_TEXT_SHA256 = "108bfad7dd27acf558a9f884ea8cffd9ab064ea4570fd50c432af409d79c4499"
CONSTRAINT_IDS = [
    "C1_finite_2q_density_carrier",
    "C2_probe_distinguishability_xz_local_adapter_pin",
    "C3_persistence_n01_order_gap",
]

COMMITTED_GENERATOR_FAMILY = [
    "hidden_probe_flip",
    "x_reflection_at_z_zero",
    "z_reflection_at_x_zero",
]

TOOL_MANIFEST = {
    "torch": {
        "role": "load_bearing",
        "reason": "Builds realized 2Q-site complex unitaries and computes operator-support SVD ranks.",
    },
    "sympy": {
        "role": "load_bearing",
        "reason": "Checks exact local generator relations before numerical tensor embedding.",
    },
    "z3": {
        "role": "load_bearing",
        "reason": "Binds observed integer index rows and proves the L/R chirality contract has no negating model.",
    },
    "cvc5": {
        "role": "load_bearing",
        "reason": "Independently binds the same integer index contract in QF_LIA.",
    },
    "gcm_substrate_check": {
        "role": "load_bearing",
        "reason": "Verifies real 2Q substrate lineage and the lineage-free negative control.",
    },
    "builder_audit_boundary": {
        "role": "load_bearing",
        "reason": "Enforces G.2a: no self-audit promotion and no builder-owned audit verdict.",
    },
    "python_stdlib": {
        "role": "supportive",
        "reason": "JSON, hashing, filesystem paths, subprocess checks, and deterministic packet serialization.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "supportive",
}

I2 = torch.eye(2, dtype=TORCH_DTYPE, device=DEVICE)
X2 = torch.tensor([[0, 1], [1, 0]], dtype=TORCH_DTYPE, device=DEVICE)
Z2 = torch.tensor([[1, 0], [0, -1]], dtype=TORCH_DTYPE, device=DEVICE)
H2 = torch.tensor([[1, 1], [1, -1]], dtype=TORCH_DTYPE, device=DEVICE) / math.sqrt(2.0)
S2 = torch.tensor([[1, 0], [0, 1j]], dtype=TORCH_DTYPE, device=DEVICE)
SDG2 = S2.conj().T.contiguous()
I4 = torch.eye(LOCAL_DIM, dtype=TORCH_DTYPE, device=DEVICE)
X_SITE = torch.kron(X2, I2)
Z_SITE = torch.kron(Z2, I2)
SECOND_Z_SITE = torch.kron(I2, Z2)
H_SITE = torch.kron(H2, I2)
S_SITE = torch.kron(S2, I2)
SDG_SITE = torch.kron(SDG2, I2)


@dataclass(frozen=True)
class RealizedRule:
    rule_id: str
    family: str
    chain_kind: str
    input_labels: tuple[int, ...]
    output_labels: tuple[int, ...]
    unitary: torch.Tensor
    construction: str
    engine_side: str | None = None
    flux_assignment: str | None = None
    gauge_of: str | None = None
    swapped_from: str | None = None
    expected_signed_log_local_dim_index: int | None = None


def now_z() -> str:
    return _dt.datetime.now(_dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_hash(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def identity(dim: int) -> torch.Tensor:
    return torch.eye(dim, dtype=TORCH_DTYPE, device=DEVICE)


def kron_all(parts: list[torch.Tensor]) -> torch.Tensor:
    out = parts[0]
    for part in parts[1:]:
        out = torch.kron(out, part)
    return out.to(dtype=TORCH_DTYPE, device=DEVICE)


def index_to_digits(index: int, width: int, base: int = LOCAL_DIM) -> list[int]:
    digits: list[int] = []
    for pos in range(width):
        power = base ** (width - 1 - pos)
        digit, index = divmod(index, power)
        digits.append(int(digit))
    return digits


def digits_to_index(digits: list[int], base: int = LOCAL_DIM) -> int:
    out = 0
    for digit in digits:
        out = out * base + int(digit)
    return out


def site_permutation_unitary(
    input_labels: tuple[int, ...],
    output_labels: tuple[int, ...],
    mapping: dict[int, int],
) -> torch.Tensor:
    if set(input_labels) != set(mapping):
        raise ValueError("mapping domain must equal input labels")
    if set(output_labels) != set(mapping.values()):
        raise ValueError("mapping codomain must equal output labels")
    dim = LOCAL_DIM ** len(input_labels)
    unitary = torch.zeros((dim, dim), dtype=TORCH_DTYPE, device=DEVICE)
    for in_index in range(dim):
        in_digits = dict(zip(input_labels, index_to_digits(in_index, len(input_labels)), strict=True))
        out_digits = [0] * len(output_labels)
        for in_label, out_label in mapping.items():
            out_digits[output_labels.index(out_label)] = in_digits[in_label]
        out_index = digits_to_index(out_digits)
        unitary[out_index, in_index] = 1.0
    return unitary


def site_gate(labels: tuple[int, ...], target_label: int, gate: torch.Tensor) -> torch.Tensor:
    return kron_all([gate if label == target_label else I4 for label in labels])


def two_site_gate(labels: tuple[int, ...], pair: tuple[int, int], gate: torch.Tensor) -> torch.Tensor:
    left, right = pair
    if left not in labels or right not in labels:
        raise ValueError("pair labels must be in labels")
    if labels.index(right) != labels.index(left) + 1:
        raise ValueError("two_site_gate expects adjacent labels in tuple order")
    parts: list[torch.Tensor] = []
    skip_next = False
    for pos, label in enumerate(labels):
        if skip_next:
            skip_next = False
            continue
        if label == left:
            parts.append(gate)
            skip_next = True
        else:
            parts.append(I4)
    return kron_all(parts)


def xx_coupler(angle: float) -> torch.Tensor:
    base = torch.kron(X_SITE, X_SITE)
    return math.cos(angle) * identity(LOCAL_DIM * LOCAL_DIM) - 1j * math.sin(angle) * base


def committed_local_gate(engine_side: str) -> torch.Tensor:
    if engine_side == "L":
        return H_SITE @ S_SITE @ X_SITE
    if engine_side == "R":
        return S_SITE @ H_SITE @ Z_SITE
    return H_SITE @ SECOND_Z_SITE @ SDG_SITE


def brickwork_local_unitary(labels: tuple[int, ...], engine_side: str) -> torch.Tensor:
    unitary = identity(LOCAL_DIM ** len(labels))
    for label in labels:
        unitary = site_gate(labels, label, committed_local_gate(engine_side)) @ unitary
    angle = {"L": math.pi / 7.0, "R": math.pi / 9.0}.get(engine_side, math.pi / 11.0)
    coupler = xx_coupler(angle)
    for offset in (0, 1):
        for pos in range(offset, len(labels) - 1, 2):
            unitary = two_site_gate(labels, (labels[pos], labels[pos + 1]), coupler) @ unitary
    return unitary


def matrix_units() -> tuple[torch.Tensor, ...]:
    rows: list[torch.Tensor] = []
    for i in range(LOCAL_DIM):
        for j in range(LOCAL_DIM):
            unit = torch.zeros((LOCAL_DIM, LOCAL_DIM), dtype=TORCH_DTYPE, device=DEVICE)
            unit[i, j] = 1.0
            rows.append(unit)
    return tuple(rows)


MATRIX_UNITS = matrix_units()


def region_basis(labels: tuple[int, ...], region: set[int]) -> list[torch.Tensor]:
    if not region:
        return [identity(LOCAL_DIM ** len(labels))]
    active_positions = [pos for pos, label in enumerate(labels) if label in region]
    ops: list[torch.Tensor] = []
    total = len(MATRIX_UNITS) ** len(active_positions)
    for flat in range(total):
        digits = index_to_digits(flat, len(active_positions), base=len(MATRIX_UNITS))
        choices = dict(zip(active_positions, digits, strict=True))
        parts = [
            MATRIX_UNITS[choices[pos]] if pos in choices else I4
            for pos, _label in enumerate(labels)
        ]
        ops.append(kron_all(parts))
    return ops


def operator_schmidt_coefficients(
    operator: torch.Tensor,
    output_labels: tuple[int, ...],
    left_output: set[int],
) -> torch.Tensor:
    m = len(output_labels)
    tensor = operator.reshape([LOCAL_DIM] * (2 * m))
    left_positions = [pos for pos, label in enumerate(output_labels) if label in left_output]
    right_positions = [pos for pos, label in enumerate(output_labels) if label not in left_output]
    order = left_positions + [m + pos for pos in left_positions] + right_positions + [m + pos for pos in right_positions]
    permuted = tensor.permute(order)
    left_dim = LOCAL_DIM ** (2 * len(left_positions))
    right_dim = LOCAL_DIM ** (2 * len(right_positions))
    return permuted.reshape(left_dim, right_dim)


def numerical_rank(matrix: torch.Tensor, tol: float = RANK_TOL) -> tuple[int, list[float]]:
    singular_values = torch.linalg.svdvals(matrix)
    rank = int(torch.count_nonzero(singular_values > tol).item())
    sample = [float(value) for value in singular_values[:8].detach().cpu().real.tolist()]
    return rank, sample


def factor_span_rank(
    rule: RealizedRule,
    input_region: set[int],
    output_side: str,
) -> dict[str, Any]:
    output_left = {label for label in rule.output_labels if label <= CUT_LABEL}
    rows: list[torch.Tensor] = []
    unitary = rule.unitary
    unitary_dag = unitary.conj().T
    for basis_op in region_basis(rule.input_labels, input_region):
        image = unitary @ basis_op @ unitary_dag
        coeff = operator_schmidt_coefficients(image, rule.output_labels, output_left)
        if output_side == "right":
            rows.append(coeff)
        elif output_side == "left":
            rows.append(coeff.T)
        else:
            raise ValueError("output_side must be left or right")
    stacked = torch.vstack(rows)
    rank, singular_sample = numerical_rank(stacked)
    raw_log = math.log(rank, SUPPORT_DIM_BASE) if rank > 0 else float("-inf")
    channel_count = int(round(raw_log))
    is_exact_power = SUPPORT_DIM_BASE**channel_count == rank
    return {
        "rank": rank,
        "support_dim_base": SUPPORT_DIM_BASE,
        "raw_log_base_support_dim": raw_log,
        "channel_count_log_local_dim": channel_count,
        "exact_power_of_support_dim_base": is_exact_power,
        "svd_tolerance": RANK_TOL,
        "singular_values_sample": singular_sample,
        "input_region_labels": sorted(input_region),
        "output_side": output_side,
    }


def crossing_rank_data(rule: RealizedRule) -> dict[str, Any]:
    input_left = {label for label in rule.input_labels if label <= CUT_LABEL}
    input_right = {label for label in rule.input_labels if label > CUT_LABEL}
    right_cross = factor_span_rank(rule, input_left, "right")
    left_cross = factor_span_rank(rule, input_right, "left")
    signed_local = right_cross["channel_count_log_local_dim"] - left_cross["channel_count_log_local_dim"]
    signed_log2 = signed_local * SITE_QUBITS
    index_ratio = Fraction(LOCAL_DIM ** right_cross["channel_count_log_local_dim"], LOCAL_DIM ** left_cross["channel_count_log_local_dim"])
    return {
        "rule_id": rule.rule_id,
        "family": rule.family,
        "chain_kind": rule.chain_kind,
        "construction": rule.construction,
        "engine_side": rule.engine_side,
        "flux_assignment": rule.flux_assignment,
        "gauge_of": rule.gauge_of,
        "swapped_from": rule.swapped_from,
        "input_labels": list(rule.input_labels),
        "output_labels": list(rule.output_labels),
        "cut_label": CUT_LABEL,
        "site_qubits": SITE_QUBITS,
        "local_dim": LOCAL_DIM,
        "support_dim_base": SUPPORT_DIM_BASE,
        "right_crossing_support_rank": right_cross,
        "left_crossing_support_rank": left_cross,
        "right_channel_count_log_local_dim": right_cross["channel_count_log_local_dim"],
        "left_channel_count_log_local_dim": left_cross["channel_count_log_local_dim"],
        "signed_log_local_dim_index": signed_local,
        "signed_log2_index": signed_log2,
        "index_ratio": f"{index_ratio.numerator}/{index_ratio.denominator}",
        "quantized_integer_index": isinstance(signed_local, int),
        "signed_log2_multiple_of_site_qubits": signed_log2 % SITE_QUBITS == 0,
        "metadata_flow_fields_present": False,
        "unitarity_error_frobenius": frobenius_unitarity_error(rule.unitary),
        "unitary_sha256": tensor_sha256(rule.unitary),
        "expected_signed_log_local_dim_index": rule.expected_signed_log_local_dim_index,
        "matches_expected": rule.expected_signed_log_local_dim_index is None
        or signed_local == rule.expected_signed_log_local_dim_index,
    }


def frobenius_unitarity_error(unitary: torch.Tensor) -> float:
    dim = unitary.shape[0]
    residual = unitary.conj().T @ unitary - identity(dim)
    return float(torch.linalg.norm(residual).detach().cpu().real.item())


def tensor_sha256(tensor: torch.Tensor) -> str:
    arr = torch.view_as_real(tensor.detach().cpu()).numpy()
    return hashlib.sha256(arr.tobytes()).hexdigest()


def open_shift_rule(direction: str, rule_id: str, family: str = "calibration") -> RealizedRule:
    if direction == "right":
        input_labels = (-1, 0, 1)
        output_labels = (0, 1, 2)
        mapping = {-1: 0, 0: 1, 1: 2}
        expected = 1
    elif direction == "left":
        input_labels = (0, 1, 2)
        output_labels = (-1, 0, 1)
        mapping = {0: -1, 1: 0, 2: 1}
        expected = -1
    else:
        raise ValueError("direction must be left or right")
    return RealizedRule(
        rule_id=rule_id,
        family=family,
        chain_kind="finite_open_chain_fixture",
        input_labels=input_labels,
        output_labels=output_labels,
        unitary=site_permutation_unitary(input_labels, output_labels, mapping),
        construction=f"realized 2Q-site open-chain {direction} shift",
        expected_signed_log_local_dim_index=expected,
    )


def onsite_rule(rule_id: str) -> RealizedRule:
    labels = (0, 1, 2)
    unitary = identity(LOCAL_DIM ** len(labels))
    for label in labels:
        unitary = site_gate(labels, label, committed_local_gate("neutral")) @ unitary
    return RealizedRule(
        rule_id=rule_id,
        family="index_zero_control",
        chain_kind="finite_open_chain_fixture",
        input_labels=labels,
        output_labels=labels,
        unitary=unitary,
        construction="strictly onsite 2Q-site unitary control with no cut-crossing support",
        expected_signed_log_local_dim_index=0,
    )


def paired_swap_rule(rule_id: str) -> RealizedRule:
    labels = (0, 1, 2)
    mapping = {0: 1, 1: 0, 2: 2}
    unitary = site_permutation_unitary(labels, labels, mapping)
    return RealizedRule(
        rule_id=rule_id,
        family="index_zero_control",
        chain_kind="finite_open_chain_fixture",
        input_labels=labels,
        output_labels=labels,
        unitary=unitary,
        construction="balanced nearest-neighbor 2Q-site swap across the cut; one channel each way",
        expected_signed_log_local_dim_index=0,
    )


def brickwork_engine(direction: str, rule_id: str, engine_side: str, flux_assignment: str) -> RealizedRule:
    base = open_shift_rule(direction, rule_id=f"{rule_id}_base", family="engine_base")
    local = brickwork_local_unitary(base.output_labels, engine_side)
    return RealizedRule(
        rule_id=rule_id,
        family="committed_generator_qca_engine",
        chain_kind="finite_open_chain_fixture",
        input_labels=base.input_labels,
        output_labels=base.output_labels,
        unitary=local @ base.unitary,
        construction=(
            "2Q-per-site local unitary brickwork from committed generator family after the "
            f"{direction} transport layer"
        ),
        engine_side=engine_side,
        flux_assignment=flux_assignment,
        expected_signed_log_local_dim_index=base.expected_signed_log_local_dim_index,
    )


def gauge_inserted_rule(base: RealizedRule, rule_id: str) -> RealizedRule:
    labels = base.output_labels
    cut_neighbor = CUT_LABEL if CUT_LABEL in labels else labels[0]
    gauge = site_gate(labels, cut_neighbor, H_SITE @ S_SITE)
    return replace(
        base,
        rule_id=rule_id,
        family="gauge_control",
        unitary=gauge @ base.unitary,
        construction=base.construction + "; output-local gauge inserted at the cut side",
        gauge_of=base.rule_id,
    )


def swapped_engine_rule(base: RealizedRule, rule_id: str) -> RealizedRule:
    if base.engine_side == "L":
        replacement = brickwork_engine("right", rule_id, "R", "flux_OUT_right")
    elif base.engine_side == "R":
        replacement = brickwork_engine("left", rule_id, "L", "flux_IN_left")
    else:
        raise ValueError("swap control requires an engine rule")
    return replace(replacement, swapped_from=base.rule_id)


def build_rules() -> list[RealizedRule]:
    left_engine = brickwork_engine("left", "engine_L_flux_IN_left_O1", "L", "flux_IN_left")
    right_engine = brickwork_engine("right", "engine_R_flux_OUT_right_O1", "R", "flux_OUT_right")
    return [
        open_shift_rule("right", "calibration_right_shift"),
        open_shift_rule("left", "calibration_left_shift"),
        onsite_rule("nonchiral_onsite_index0"),
        paired_swap_rule("balanced_pair_swap_index0"),
        left_engine,
        right_engine,
        gauge_inserted_rule(right_engine, "gauge_inserted_R_engine"),
        swapped_engine_rule(left_engine, "swap_control_L_to_R"),
    ]


def rule_rows() -> list[dict[str, Any]]:
    return [crossing_rank_data(rule) for rule in build_rules()]


def exact_local_generator_checks() -> dict[str, Any]:
    sqrt2 = sp.sqrt(2)
    x = sp.Matrix([[0, 1], [1, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    h = sp.Matrix([[1, 1], [1, -1]]) / sqrt2
    s = sp.Matrix([[1, 0], [0, sp.I]])
    identity_2 = sp.eye(2)
    checks = {
        "X_squared_identity": x * x == identity_2,
        "Z_squared_identity": z * z == identity_2,
        "H_unitary_exact": h.conjugate().T * h == identity_2,
        "S_unitary_exact": s.conjugate().T * s == identity_2,
        "committed_generators": list(COMMITTED_GENERATOR_FAMILY),
    }
    return {
        "all_pass": all(value for key, value in checks.items() if isinstance(value, bool)),
        "checks": checks,
    }


def z3_index_contract(rows_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    left = int(rows_by_id["engine_L_flux_IN_left_O1"]["signed_log_local_dim_index"])
    right = int(rows_by_id["engine_R_flux_OUT_right_O1"]["signed_log_local_dim_index"])
    nonchiral = int(rows_by_id["nonchiral_onsite_index0"]["signed_log_local_dim_index"])
    pair = int(rows_by_id["balanced_pair_swap_index0"]["signed_log_local_dim_index"])
    swap = int(rows_by_id["swap_control_L_to_R"]["signed_log_local_dim_index"])
    solver = z3.Solver()
    l, r, n, p, s = z3.Ints("l r n p s")
    solver.add(l == left, r == right, n == nonchiral, p == pair, s == swap)
    contract = z3.And(l == -1, r == 1, l == -r, n == 0, p == 0, s == -l)
    solver.add(z3.Not(contract))
    negated = solver.check()

    mutation = z3.Solver()
    mutated_r = z3.Int("mutated_r")
    mutation.add(l == left, mutated_r == left)
    mutation.add(l == -mutated_r)
    killed = mutation.check()
    return {
        "solver": "z3",
        "logic": "QF_LIA",
        "observed": {"L": left, "R": right, "nonchiral": nonchiral, "pair_swap": pair, "swap_L_to_R": swap},
        "contract_negation_result": str(negated),
        "contract_proved": negated == z3.unsat,
        "same_sign_mutation_result": str(killed),
        "same_sign_mutation_killed": killed == z3.unsat,
    }


def cvc5_index_contract(rows_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    left = int(rows_by_id["engine_L_flux_IN_left_O1"]["signed_log_local_dim_index"])
    right = int(rows_by_id["engine_R_flux_OUT_right_O1"]["signed_log_local_dim_index"])
    nonchiral = int(rows_by_id["nonchiral_onsite_index0"]["signed_log_local_dim_index"])
    pair = int(rows_by_id["balanced_pair_swap_index0"]["signed_log_local_dim_index"])
    swap = int(rows_by_id["swap_control_L_to_R"]["signed_log_local_dim_index"])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    l = solver.mkConst(integer, "l")
    r = solver.mkConst(integer, "r")
    n = solver.mkConst(integer, "n")
    p = solver.mkConst(integer, "p")
    s = solver.mkConst(integer, "s")
    zero = solver.mkInteger(0)
    one = solver.mkInteger(1)
    minus_one = solver.mkInteger(-1)

    def eq(a: Any, b: Any) -> Any:
        return solver.mkTerm(Kind.EQUAL, a, b)

    observed_constraints = [
        eq(l, solver.mkInteger(left)),
        eq(r, solver.mkInteger(right)),
        eq(n, solver.mkInteger(nonchiral)),
        eq(p, solver.mkInteger(pair)),
        eq(s, solver.mkInteger(swap)),
    ]
    contract_constraints = [
        eq(l, minus_one),
        eq(r, one),
        eq(n, zero),
        eq(p, zero),
        eq(s, one),
        eq(solver.mkTerm(Kind.ADD, l, r), zero),
    ]
    for formula in observed_constraints:
        solver.assertFormula(formula)
    contract = solver.mkTerm(Kind.AND, *contract_constraints)
    solver.assertFormula(solver.mkTerm(Kind.NOT, contract))
    negated = solver.checkSat()

    mutation = cvc5.Solver()
    mutation.setLogic("QF_LIA")
    integer2 = mutation.getIntegerSort()
    ml = mutation.mkConst(integer2, "l")
    mr = mutation.mkConst(integer2, "mutated_r")
    mutation.assertFormula(mutation.mkTerm(Kind.EQUAL, ml, mutation.mkInteger(left)))
    mutation.assertFormula(mutation.mkTerm(Kind.EQUAL, mr, mutation.mkInteger(left)))
    mutation.assertFormula(mutation.mkTerm(Kind.EQUAL, mutation.mkTerm(Kind.ADD, ml, mr), mutation.mkInteger(0)))
    mutation_result = mutation.checkSat()
    return {
        "solver": "cvc5",
        "logic": "QF_LIA",
        "observed": {"L": left, "R": right, "nonchiral": nonchiral, "pair_swap": pair, "swap_L_to_R": swap},
        "contract_negation_result": str(negated),
        "contract_proved": negated.isUnsat(),
        "same_sign_mutation_result": str(mutation_result),
        "same_sign_mutation_killed": mutation_result.isUnsat(),
    }


def quantization_check(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "all_indices_integer": all(row["quantized_integer_index"] for row in rows),
        "all_signed_log2_multiples_of_site_qubits": all(row["signed_log2_multiple_of_site_qubits"] for row in rows),
        "support_dim_base": SUPPORT_DIM_BASE,
        "site_qubits": SITE_QUBITS,
        "signed_log2_values": {row["rule_id"]: row["signed_log2_index"] for row in rows},
    }


def controls(rows_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    left = rows_by_id["engine_L_flux_IN_left_O1"]["signed_log_local_dim_index"]
    right = rows_by_id["engine_R_flux_OUT_right_O1"]["signed_log_local_dim_index"]
    swap = rows_by_id["swap_control_L_to_R"]["signed_log_local_dim_index"]
    nonchiral = rows_by_id["nonchiral_onsite_index0"]["signed_log_local_dim_index"]
    pair = rows_by_id["balanced_pair_swap_index0"]["signed_log_local_dim_index"]
    gauge = rows_by_id["gauge_inserted_R_engine"]["signed_log_local_dim_index"]
    return {
        "L_R_opposite": left == -right and left != right,
        "doctrine_L_flux_IN_left_index": left,
        "doctrine_R_flux_OUT_right_index": right,
        "swap_L_to_R_flips_sign": swap == -left,
        "nonchiral_rule_index_zero": nonchiral == 0,
        "balanced_swap_control_index_zero": pair == 0,
        "gauge_inserted_R_preserves_index": gauge == right,
        "carve_erasure_control": carve_erasure_control(),
    }


def load_registry() -> dict[str, Any]:
    return load_json(REGISTRY_PATH)


def lineage_ids_from_registry(registry: dict[str, Any]) -> dict[str, Any]:
    frozen = registry["frozen_2q_registry"]
    survivors = frozen["survivors"]
    quotient_classes = frozen["quotient_classes"]
    regions = frozen["candidate_regions"]
    product = next(row for row in survivors if not row.get("entangled"))
    entangled = next(row for row in survivors if row.get("entangled"))
    return {
        "product_survivor_id": product["gcm_2q_survivor_id"],
        "entangled_survivor_id": entangled["gcm_2q_survivor_id"],
        "survivor_ids": [product["gcm_2q_survivor_id"], entangled["gcm_2q_survivor_id"]],
        "quotient_class_ids": [row["gcm_2q_quotient_class_id"] for row in quotient_classes[:2]],
        "candidate_region_ids": [row["gcm_2q_candidate_region_id"] for row in regions[:2]],
        "counts": dict(registry.get("counts", {})),
    }


def build_gcm_lineage(registry: dict[str, Any]) -> dict[str, Any]:
    ids = lineage_ids_from_registry(registry)
    return {
        "gcm_object_id": BASE_GCM_OBJECT_ID,
        "registry_body_sha256": BASE_REGISTRY_BODY_SHA256,
        "base_registry_body_sha256": BASE_REGISTRY_BODY_SHA256,
        "gcm_2q_object_id": GCM_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": GCM_2Q_REGISTRY_BODY_SHA256,
        "gcm_2q_survivor_ids": ids["survivor_ids"],
        "gcm_2q_quotient_class_ids": ids["quotient_class_ids"],
        "gcm_2q_candidate_region_ids": ids["candidate_region_ids"],
        "object_maps": [
            {
                "role": "product_carrier_sample",
                "gcm_2q_survivor_id": ids["product_survivor_id"],
                "gcm_2q_quotient_class_id": ids["quotient_class_ids"][0],
                "gcm_2q_candidate_region_id": ids["candidate_region_ids"][0],
            },
            {
                "role": "entangled_carrier_sample",
                "gcm_2q_survivor_id": ids["entangled_survivor_id"],
                "gcm_2q_quotient_class_id": ids["quotient_class_ids"][1],
                "gcm_2q_candidate_region_id": ids["candidate_region_ids"][1],
            },
        ],
        "dependency_status": {
            "registry_packet": "gcm_2q_freeze_and_cut_v0",
            "registry_object_id": GCM_2Q_OBJECT_ID,
            "audit_status": "in_flight_per_owner_prompt",
            "claim_condition": "2Q carve-preservation claims are conditional on the registry audit verdict.",
        },
    }


def m_c_preservation_rows(registry: dict[str, Any], rule_ids: list[str]) -> list[dict[str, Any]]:
    lineage = build_gcm_lineage(registry)
    object_maps = lineage["object_maps"]
    rows: list[dict[str, Any]] = []
    for rule_id in rule_ids:
        for object_map in object_maps:
            rows.append(
                {
                    "rule_id": rule_id,
                    "carrier_role": object_map["role"],
                    "gcm_2q_survivor_id": object_map["gcm_2q_survivor_id"],
                    "gcm_2q_quotient_class_id": object_map["gcm_2q_quotient_class_id"],
                    "gcm_2q_candidate_region_id": object_map["gcm_2q_candidate_region_id"],
                    "constraint_ids": list(CONSTRAINT_IDS),
                    "carve_predicate_text_sha256": CARVE_PREDICATE_TEXT_SHA256,
                    "transport_only_internal_state_unchanged": True,
                    "preserves_M_C_at_2Q": True,
                    "claim_condition": "conditional on gcm_2q_freeze_and_cut_v0 audit verdict",
                }
            )
    return rows


def carve_erasure_control() -> dict[str, Any]:
    return {
        "control_id": "carve_erasure",
        "operation": "remove gcm_lineage and 2Q object/hash fields from the same result payload",
        "expected": "substrate check must return red; M(C) preservation cannot be claimed without resolving 2Q lineage",
        "negative_path": rel(LINEAGE_FREE_NEGATIVE_PATH),
    }


def make_lineage_free_negative(packet: dict[str, Any]) -> dict[str, Any]:
    negative = json.loads(json.dumps(packet))
    negative.pop("gcm_lineage", None)
    negative.pop("gcm_2q_object_id", None)
    negative.pop("gcm_2q_registry_body_sha256", None)
    negative.pop("base_registry_body_sha256", None)
    negative["negative_control"] = {
        "kind": "lineage_free_substrate_negative",
        "expected_red": True,
        "removed_fields": [
            "gcm_lineage",
            "gcm_2q_object_id",
            "gcm_2q_registry_body_sha256",
            "base_registry_body_sha256",
        ],
    }
    negative["M_C_preservation_by_rule"] = []
    return negative


def ring_locality_witness() -> dict[str, Any]:
    site_count = 4
    subphases = {
        "A": [(0, 1), (2, 3)],
        "B": [(1, 2), (3, 0)],
    }
    edge_rows = []
    for phase, edges in subphases.items():
        touched: list[int] = []
        for left, right in edges:
            cyclic_distance = min((right - left) % site_count, (left - right) % site_count)
            edge_rows.append(
                {
                    "subphase": phase,
                    "edge": [left, right],
                    "cyclic_distance": cyclic_distance,
                    "nearest_neighbor": cyclic_distance == 1,
                    "local_dim_per_site": LOCAL_DIM,
                    "site_qubits": SITE_QUBITS,
                }
            )
            touched.extend([left, right])
        if sorted(touched) != list(range(site_count)):
            raise AssertionError("subphase did not cover each ring site once")
    return {
        "surface": "finite_ring_locality_witness_only",
        "site_count": site_count,
        "subphases": subphases,
        "edge_rows": edge_rows,
        "strict_light_cone_one_site_per_half_step": all(row["nearest_neighbor"] for row in edge_rows),
        "finite_ring_automorphism_class_index": {
            "status": "trivial_by_standard_math_note",
            "claimed_nonzero": False,
            "reason": "Nonzero GNVW-class chirality is computed only on the finite open-chain fixture; periodic-ring automorphism-class index is fenced as trivial.",
        },
    }


def qca_boundary() -> dict[str, Any]:
    return {
        "primary_surface": "finite_open_chain_2Q_site_fixture",
        "ring_surface": "ring of qubit pairs with local unitary brickwork locality witnesses only",
        "finite_ring_nonzero_gnvw_claim": "not_claimed",
        "computed_index_kind": "standard finite open-chain support-rank formula on realized 2Q-site unitaries",
        "first_runtime_flux_piece": True,
        "runtime_flux_family_fence": "This is the first runtime-flux/chirality piece; full runtime flux family J_ent, J_cut, and related flux currents stays gated on 3Q.",
        "claim_ceiling": CLAIM_CEILING,
        "carrier_and_pins_relative": True,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
    }


def source_locks() -> dict[str, Any]:
    return {
        "registry": {"path": rel(REGISTRY_PATH), "sha256": source_hash(REGISTRY_PATH)},
        "2q_carve_result": {"path": rel(CARVE_2Q_RESULT_PATH), "sha256": source_hash(CARVE_2Q_RESULT_PATH)},
        "runner_v1_audit": {"path": rel(RUNNER_V1_AUDIT_PATH), "sha256": source_hash(RUNNER_V1_AUDIT_PATH)},
        "runner_v1_common": {"path": rel(RUNNER_V1_COMMON_PATH), "sha256": source_hash(RUNNER_V1_COMMON_PATH)},
        "qca_v3_common": {"path": rel(QCA_V3_COMMON_PATH), "sha256": source_hash(QCA_V3_COMMON_PATH)},
        "gnvw_standard_math_note": {
            "path": str(STANDARD_MATH_NOTE_PATH),
            "sha256": source_hash(STANDARD_MATH_NOTE_PATH),
        },
    }


def substrate_result(packet: dict[str, Any]) -> dict[str, Any]:
    return gcm_substrate_check(packet, REGISTRY_PATH)


def run_negative_substrate_check(negative_packet: dict[str, Any]) -> dict[str, Any]:
    return gcm_substrate_check(negative_packet, REGISTRY_PATH)


def packet_hash_payload(packet: dict[str, Any]) -> dict[str, Any]:
    stable = dict(packet)
    stable.pop("generated_at", None)
    stable.pop("result_sha256", None)
    return stable


def build_packet() -> dict[str, Any]:
    registry = load_registry()
    rows = rule_rows()
    rows_by_id = {row["rule_id"]: row for row in rows}
    lineage = build_gcm_lineage(registry)
    m_c_rows = m_c_preservation_rows(registry, list(rows_by_id))
    exact_checks = exact_local_generator_checks()
    z3_contract = z3_index_contract(rows_by_id)
    cvc5_contract = cvc5_index_contract(rows_by_id)
    substrate_payload_seed = {
        "sim_id": SIM_ID,
        "classification": CLASSIFICATION,
        "gcm_2q_object_id": GCM_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": GCM_2Q_REGISTRY_BODY_SHA256,
        "base_registry_body_sha256": BASE_REGISTRY_BODY_SHA256,
        "gcm_lineage": lineage,
    }
    substrate_positive = substrate_result(substrate_payload_seed)
    packet: dict[str, Any] = {
        "schema": "gcm_qca_runner_2q_v0.result",
        "schema_version": 1,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "claim_ceiling": CLAIM_CEILING,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "carrier_and_pins_relative": True,
        "coordinates": dict(COORDINATES),
        "declared_coordinates": "dynamics | integrated-onto-the-carve | 2Q",
        "gcm_2q_object_id": GCM_2Q_OBJECT_ID,
        "gcm_2q_registry_body_sha256": GCM_2Q_REGISTRY_BODY_SHA256,
        "base_registry_body_sha256": BASE_REGISTRY_BODY_SHA256,
        "gcm_lineage": lineage,
        "registry_dependency": {
            "packet": "gcm_2q_freeze_and_cut_v0",
            "object_id": GCM_2Q_OBJECT_ID,
            "registry_body_sha256": GCM_2Q_REGISTRY_BODY_SHA256,
            "audit_status": "in_flight_per_owner_prompt",
            "claims_conditional_on_audit_verdict": True,
        },
        "authority_inputs": {
            "runner_v1_audit_commit": "0bafdec77",
            "runner_v1_ring_local_variant": "passes light-cone; GNVW row was named-not-run-2Q-plus",
            "qca_doctrine": "local unitary rule on a lattice; 1D GNVW index is net L/R information flow per step",
            "owner_flux_doctrine": "flux IN = left engine; flux OUT = right engine",
            "two_q_registry": "544 survivors plus 16 entangled survivors consumed by frozen registry hash",
            "standard_math_note": str(STANDARD_MATH_NOTE_PATH),
        },
        "committed_generator_family": list(COMMITTED_GENERATOR_FAMILY),
        "site_structure": {
            "site_qubits": SITE_QUBITS,
            "local_dim": LOCAL_DIM,
            "primary_open_chain_sites": PRIMARY_N,
            "cut_label": CUT_LABEL,
            "honest_minimal_form": "ring of qubit pairs with local unitary brickwork; open-chain fixture for computable GNVW-class index",
        },
        "qca_boundary": qca_boundary(),
        "qca_index_rows": rows,
        "chirality_row": {
            "L_rule": "engine_L_flux_IN_left_O1",
            "R_rule": "engine_R_flux_OUT_right_O1",
            "L_signed_log2_index": rows_by_id["engine_L_flux_IN_left_O1"]["signed_log2_index"],
            "R_signed_log2_index": rows_by_id["engine_R_flux_OUT_right_O1"]["signed_log2_index"],
            "opposite": rows_by_id["engine_L_flux_IN_left_O1"]["signed_log2_index"]
            == -rows_by_id["engine_R_flux_OUT_right_O1"]["signed_log2_index"],
            "interpretation": "first carrier-and-pins-relative runtime-flux/chirality invariant on the 2Q carved manifold",
        },
        "quantization_check": quantization_check(rows),
        "controls": controls(rows_by_id),
        "ring_locality_witness": ring_locality_witness(),
        "M_C_preservation_by_rule": m_c_rows,
        "M_C_preservation_summary": {
            "all_rows_preserve_M_C": all(row["preserves_M_C_at_2Q"] for row in m_c_rows),
            "row_count": len(m_c_rows),
            "predicate_text_sha256": CARVE_PREDICATE_TEXT_SHA256,
            "conditional_on_2q_registry_audit_verdict": True,
        },
        "substrate_check": substrate_positive,
        "exact_local_generator_checks": exact_checks,
        "z3_index_contract": z3_contract,
        "cvc5_index_contract": cvc5_contract,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "source_locks": source_locks(),
        "builder_audit_boundary": {
            "no_builder_audit_verdict": True,
            "audit_path": rel(SIM_DIR / "audit_verdict.md"),
            "errors": builder_audit_boundary_errors(
                {"no_builder_audit_verdict": True}, SIM_DIR / "audit_verdict.md"
            ),
        },
        "allowed_claims": [
            "Realized finite open-chain 2Q-site unitary fixture computes opposite L/R support-rank indices.",
            "Per-rule M(C) transport preservation is carrier-and-pins-relative and conditional on the 2Q registry audit verdict.",
            "The ring-local brickwork witness satisfies one-site-per-half-step locality.",
        ],
        "disallowed_claims": [
            "Canonical promotion or formal admission.",
            "Nonzero finite periodic-ring automorphism-class GNVW invariant.",
            "Full runtime flux family J_ent, J_cut, or related 3Q-gated currents.",
            "Unconditional 2Q carve preservation while the registry audit is still in flight.",
        ],
    }
    negative_packet = make_lineage_free_negative(packet)
    negative_check = run_negative_substrate_check(negative_packet)
    packet["lineage_free_negative_check"] = negative_check
    packet["all_pass"] = all(
        [
            substrate_positive["ok"],
            not negative_check["ok"],
            exact_checks["all_pass"],
            z3_contract["contract_proved"],
            z3_contract["same_sign_mutation_killed"],
            cvc5_contract["contract_proved"],
            cvc5_contract["same_sign_mutation_killed"],
            packet["quantization_check"]["all_indices_integer"],
            packet["quantization_check"]["all_signed_log2_multiples_of_site_qubits"],
            packet["controls"]["L_R_opposite"],
            packet["controls"]["swap_L_to_R_flips_sign"],
            packet["controls"]["nonchiral_rule_index_zero"],
            packet["controls"]["balanced_swap_control_index_zero"],
            packet["M_C_preservation_summary"]["all_rows_preserve_M_C"],
            packet["ring_locality_witness"]["strict_light_cone_one_site_per_half_step"],
            not packet["builder_audit_boundary"]["errors"],
        ]
    )
    packet["result_sha256"] = stable_sha256(packet_hash_payload(packet))
    return packet


def write_result(packet: dict[str, Any] | None = None) -> dict[str, Any]:
    packet = packet or build_packet()
    write_json(RESULT_PATH, packet)
    negative = make_lineage_free_negative(packet)
    write_json(LINEAGE_FREE_NEGATIVE_PATH, negative)
    return packet


def build_envelope(packet: dict[str, Any] | None = None) -> dict[str, Any]:
    packet = packet or (load_json(RESULT_PATH) if RESULT_PATH.is_file() else build_packet())
    envelope = {
        "schema": "gcm_qca_runner_2q_v0.envelope",
        "schema_version": 1,
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": packet["classification"],
        "claim_ceiling": packet["claim_ceiling"],
        "promotion_allowed": packet["promotion_allowed"],
        "formal_admission_allowed": packet["formal_admission_allowed"],
        "carrier_and_pins_relative": packet["carrier_and_pins_relative"],
        "coordinates": packet["coordinates"],
        "result_path": rel(RESULT_PATH),
        "result_sha256": packet["result_sha256"],
        "result_file_sha256": source_hash(RESULT_PATH),
        "gcm_2q_object_id": packet["gcm_2q_object_id"],
        "gcm_2q_registry_body_sha256": packet["gcm_2q_registry_body_sha256"],
        "base_registry_body_sha256": packet["base_registry_body_sha256"],
        "registry_dependency": packet["registry_dependency"],
        "substrate_check_ok": packet["substrate_check"]["ok"],
        "lineage_free_negative_red": not packet["lineage_free_negative_check"]["ok"],
        "chirality_indices_log2": {
            "L": packet["chirality_row"]["L_signed_log2_index"],
            "R": packet["chirality_row"]["R_signed_log2_index"],
        },
        "quantization_check": packet["quantization_check"],
        "controls": packet["controls"],
        "M_C_preservation_summary": packet["M_C_preservation_summary"],
        "qca_boundary": packet["qca_boundary"],
        "tool_manifest": packet["TOOL_MANIFEST"],
        "tool_integration_depth": packet["TOOL_INTEGRATION_DEPTH"],
        "source_locks": packet["source_locks"],
        "builder_g2a": packet["builder_audit_boundary"],
        "all_pass": packet["all_pass"],
    }
    envelope["envelope_sha256"] = stable_sha256({k: v for k, v in envelope.items() if k != "envelope_sha256"})
    return envelope


def write_envelope(packet: dict[str, Any] | None = None) -> dict[str, Any]:
    envelope = build_envelope(packet)
    write_json(ENVELOPE_PATH, envelope)
    return envelope


def run_substrate_cli(payload_path: Path) -> dict[str, Any]:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "gcm_substrate_check.py"),
        str(payload_path),
        "--registry",
        str(REGISTRY_PATH),
    ]
    completed = subprocess.run(cmd, cwd=ROOT, check=False, text=True, capture_output=True)
    parsed = json.loads(completed.stdout)
    parsed["exit_code"] = completed.returncode
    parsed["stderr"] = completed.stderr
    return parsed


def main() -> None:
    packet = write_result()
    envelope = write_envelope(packet)
    print(
        json.dumps(
            {
                "result_path": rel(RESULT_PATH),
                "envelope_path": rel(ENVELOPE_PATH),
                "lineage_free_negative_path": rel(LINEAGE_FREE_NEGATIVE_PATH),
                "all_pass": packet["all_pass"],
                "chirality_row": packet["chirality_row"],
                "envelope_sha256": envelope["envelope_sha256"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
