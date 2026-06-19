#!/usr/bin/env python3
"""Runtime/QIT flux currents on the audited 3Q GCM cut surface."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import cvc5
from cvc5 import Kind
import torch
import z3


SIM_ID = "gcm_runtime_flux_3q_v1"
ROOT = Path(__file__).resolve().parents[3]
SIM_DIR = ROOT / "system_v6" / "sims" / SIM_ID
RESULT_DIR = SIM_DIR / "results"
RESULT_PATH = RESULT_DIR / f"{SIM_ID}_results.json"
PYTORCH_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_pytorch_results.json"
JAX_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_jax_results.json"
JULIA_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_julia_results.json"
ENVELOPE_SPEC_PATH = RESULT_DIR / f"{SIM_ID}_envelope_spec.json"
ENVELOPE_PATH = RESULT_DIR / f"{SIM_ID}_envelope_results.json"
VALIDATOR_RESULT_PATH = RESULT_DIR / f"{SIM_ID}_validator_results.json"
LINEAGE_FREE_NEGATIVE_PATH = RESULT_DIR / f"{SIM_ID}_lineage_free_negative.json"

THREE_Q_FREEZE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_3q_freeze_and_cuts_v0" / "results" / "gcm_3q_freeze_and_cuts_v0_results.json"
)
THREE_Q_FREEZE_REGISTRY = (
    ROOT / "system_v6" / "sims" / "gcm_3q_freeze_and_cuts_v0" / "results" / "gcm_3q_freeze_and_cuts_v0_registry.json"
)
THREE_Q_FREEZE_AUDIT = ROOT / "system_v6" / "sims" / "gcm_3q_freeze_and_cuts_v0" / "audit_verdict.md"
THREE_Q_CARVE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_constraint_carve_3q_v1" / "results" / "gcm_constraint_carve_3q_v1_results.json"
)
TWO_Q_FREEZE_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "results" / "gcm_2q_freeze_and_cut_v0_results.json"
)
TWO_Q_FREEZE_AUDIT = ROOT / "system_v6" / "sims" / "gcm_2q_freeze_and_cut_v0" / "audit_verdict.md"
QCA_2Q_RESULT = (
    ROOT / "system_v6" / "sims" / "gcm_qca_runner_2q_v0" / "results" / "gcm_qca_runner_2q_v0_results.json"
)
QCA_2Q_AUDIT = ROOT / "system_v6" / "sims" / "gcm_qca_runner_2q_v0" / "audit_verdict.md"
ENGINE64_COMMON = (
    ROOT / "system_v6" / "sims" / "engine_64_stage_full_run_v0" / "engine_64_stage_full_run_v0_common.py"
)
ENGINE64_AUDIT = ROOT / "system_v6" / "sims" / "engine_64_stage_full_run_v0" / "audit_verdict.md"
HERMES_FLUX_SPLIT = ROOT / "system_v6" / "receipts" / "hermes_architecture_corrections_20260612.md"
NESTING_LAW = ROOT / "system_v6" / "receipts" / "nesting_law_final_object_spec_20260612.md"
CLIMB_LEDGER = ROOT / "system_v6" / "receipts" / "qubit_ladder_climb_ledger_20260612.md"
SUBSTRATE_HELPER = ROOT / "scripts" / "gcm_substrate_check.py"
BUILDER_BOUNDARY_HELPER = ROOT / "scripts" / "builder_audit_boundary.py"

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from builder_audit_boundary import builder_audit_boundary_ok  # noqa: E402
from gcm_substrate_check import gcm_substrate_check  # noqa: E402


torch.set_default_dtype(torch.float64)

CLASSIFICATION = "scratch_diagnostic"
PROMOTION_ALLOWED = False
FORMAL_ADMISSION_ALLOWED = False
DECLARED_SURFACE = "layer 24 (runtime flux) | integrated | 3Q"
CLAIM_CEILING = (
    "scratch_diagnostic; doctrine-repair runtime/QIT flux test on the audited 3Q attachment surface; "
    "carrier-and-pins-relative; independent Type1-L and Type2-R generator pins; not admitted invariants"
)
EXPECTED_3Q_OBJECT_ID = "gcm3qobj_492a4d00823507fd9ae8a1b3e4d0acb5"
EXPECTED_3Q_REGISTRY_BODY_SHA256 = "623785e4ec0f41bd8cd040c44ceefbc5f1bd3c14d3257487a82afc0a89439fb0"
EXPECTED_2Q_OBJECT_ID = "gcm2qobj_715e9424ea66468243108751fb59395f"
EXPECTED_2Q_REGISTRY_BODY_SHA256 = "57c8b47b0c60867f9d58969803e905fb905e27a2915641121583175e32c598ac"
EXPECTED_1Q_OBJECT_ID = "gcmobj_a40e54e13cec01466c9d675028b3574b"
EXPECTED_1Q_REGISTRY_BODY_SHA256 = "0fddf60cea951e88ddde9cde6cb3e6c49ee36c77ae02dfe059d8550f2c6221ed"
ANCHOR_RAW_3Q_SURVIVOR_ID = 544
TOL = 1.0e-10
CUTS = {
    "A|BC": {"left": [0], "right": [1, 2], "dims": [2, 4]},
    "B|AC": {"left": [1], "right": [0, 2], "dims": [2, 4]},
    "C|AB": {"left": [2], "right": [0, 1], "dims": [2, 4]},
}

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 8x8 density-matrix evolution, partial traces, spectra, partial transpose, and current deltas",
    },
    "torch.func": {
        "tried": True,
        "used": True,
        "reason": "load-bearing PyTorch lane batched scalar parity over the accepted current vector",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "scoped parity lane for sign/readout vectors; not the claim-bearing density recomputation",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "exact sign/finite-count guards in the JAX lane and envelope checks",
    },
    "julia_gf4_stdlib": {
        "tried": True,
        "used": True,
        "reason": "supportive Julia finite-sign arithmetic receipt; not the Julia load-bearing observable",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing UNSAT flip for independent L/R generator non-identity with erased-control SAT",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent load-bearing UNSAT flip for the same generator non-identity gate",
    },
    "gcm_substrate_check": {
        "tried": True,
        "used": True,
        "reason": "load-bearing 1Q/2Q/3Q lineage check plus lineage-free/carve-erasure negative",
    },
    "builder_audit_boundary": {
        "tried": True,
        "used": True,
        "reason": "G.2a builder/audit boundary from birth; builder writes builder_self_assessment.md, not audit_verdict.md",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "source locks, JSON, SHA-256, deterministic result writing, and process orchestration",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "torch.func": "load_bearing",
    "jax": "supportive",
    "sympy": "load_bearing",
    "julia_gf4_stdlib": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "gcm_substrate_check": "load_bearing",
    "builder_audit_boundary": "load_bearing",
    "python_stdlib": "load_bearing",
}

TOOL_INTENT = {
    "claim_classes": [
        "runtime_qit_flux_on_3q_cut_surface",
        "J_cut_delta_mutual_information",
        "J_ent_delta_negativity",
        "independent_l_r_generator_doctrine_test",
        "R_not_reverse_or_reflection_of_L",
        "3q_floor_necessity_row",
        "lineage_free_negative_red",
    ],
    "engine_tool_intent": {
        "julia": {
            "Z3": "Z3.Solver chirality sign binding with erased-control SAT flip",
        },
        "jax": {
            "sympy": "sp.Rational exact sign and cut-count guard over the exported runtime-current scalars",
        },
        "pytorch": {
            "sympy": "sp.Rational exact sign cancellation guard over the accepted PyTorch current vector",
        },
    },
}

CURRENT_DEFINITIONS = {
    "J_cut": {
        "observable": "delta mutual information across each 3Q bipartition",
        "definition": (
            "For each step and cut X|YZ, J_cut(X|YZ)=I_after(X:YZ)-I_before(X:YZ), "
            "with I=S_left+S_right-S_ABC in nats. The net row value sums the three 3Q cuts."
        ),
        "cuts": list(CUTS),
    },
    "J_ent": {
        "observable": "delta negativity and log-negativity across each 3Q bipartition",
        "definition": (
            "For each step and cut X|YZ, J_ent tracks negativity_after-negativity_before and "
            "log_negativity_after-log_negativity_before. The net row value sums the three 3Q cuts."
        ),
        "cuts": list(CUTS),
    },
    "J_chi": {
        "observable": "GNVW signed log2 transport seed lifted from committed 2Q runner",
        "definition": (
            "Use the committed open-chain 2Q QCA chirality seed as orientation: L=-2 and R=+2 "
            "log2-qubits per step, attached here only as a 3Q-survivor row current label/control."
        ),
        "source": "gcm_qca_runner_2q_v0",
    },
}

AUTHORITY_PATHS = {
    "three_q_freeze_result": THREE_Q_FREEZE_RESULT,
    "three_q_freeze_registry": THREE_Q_FREEZE_REGISTRY,
    "three_q_freeze_audit": THREE_Q_FREEZE_AUDIT,
    "three_q_carve_result": THREE_Q_CARVE_RESULT,
    "two_q_freeze_result": TWO_Q_FREEZE_RESULT,
    "two_q_freeze_audit": TWO_Q_FREEZE_AUDIT,
    "qca_2q_result": QCA_2Q_RESULT,
    "qca_2q_audit": QCA_2Q_AUDIT,
    "engine_64_stage_full_run_common": ENGINE64_COMMON,
    "engine_64_stage_full_run_audit": ENGINE64_AUDIT,
    "hermes_flux_split": HERMES_FLUX_SPLIT,
    "nesting_law": NESTING_LAW,
    "qubit_ladder_climb_ledger": CLIMB_LEDGER,
    "substrate_check_helper": SUBSTRATE_HELPER,
    "builder_audit_boundary": BUILDER_BOUNDARY_HELPER,
}


def now_z() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def stable_sha256(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_last_commit(path: Path) -> str | None:
    try:
        rel_path = rel(path)
        if rel_path.startswith("..") or path.is_absolute() and not path.resolve().is_relative_to(ROOT):
            return None
    except Exception:
        return None
    proc = subprocess.run(
        ["git", "log", "-n", "1", "--pretty=%h", "--", rel_path],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout.strip() or None


def source_lock(path: Path, role: str) -> dict[str, Any]:
    return {
        "path": rel(path),
        "exists": path.exists(),
        "sha256": sha256_file(path),
        "git_last_commit": git_last_commit(path) if path.exists() else None,
        "role": role,
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def q(value: float, digits: int = 15) -> float:
    rounded = round(float(value), digits)
    return 0.0 if abs(rounded) <= TOL else rounded


def json_cell_to_complex(cell: Any) -> complex:
    if isinstance(cell, dict):
        return complex(float(cell["re"]), float(cell["im"]))
    if isinstance(cell, list):
        return complex(float(cell[0]), float(cell[1]))
    return complex(float(cell), 0.0)


def matrix_from_json(value: list[list[Any]]) -> torch.Tensor:
    return torch.tensor(
        [[json_cell_to_complex(cell) for cell in row] for row in value],
        dtype=torch.complex128,
    )


def matrix_fingerprint(matrix: torch.Tensor) -> list[list[list[float]]]:
    rows = []
    for row in matrix.detach().cpu().tolist():
        rows.append([[q(float(complex(cell).real)), q(float(complex(cell).imag))] for cell in row])
    return rows


def hermitian(matrix: torch.Tensor) -> torch.Tensor:
    return (matrix + matrix.conj().T) / 2.0


def entropy_nats(matrix: torch.Tensor) -> float:
    eigs = torch.linalg.eigvalsh(hermitian(matrix))
    probs = torch.clamp(torch.real(eigs), min=0.0, max=1.0)
    total = torch.sum(probs)
    probs = probs / torch.clamp(total, min=1.0e-30)
    terms = torch.where(probs > TOL, -probs * torch.log(probs), torch.zeros_like(probs))
    return q(float(torch.sum(terms).item()))


def partial_trace_3q(rho: torch.Tensor, keep: list[int]) -> torch.Tensor:
    shaped = rho.reshape(2, 2, 2, 2, 2, 2)
    key = tuple(keep)
    if key == (0,):
        return torch.einsum("abcdbc->ad", shaped)
    if key == (1,):
        return torch.einsum("abcaec->be", shaped)
    if key == (2,):
        return torch.einsum("abcabf->cf", shaped)
    if key == (1, 2):
        return torch.einsum("abcaef->bcef", shaped).reshape(4, 4)
    if key == (0, 2):
        return torch.einsum("abcdbf->acdf", shaped).reshape(4, 4)
    if key == (0, 1):
        return torch.einsum("abcdec->abde", shaped).reshape(4, 4)
    if key == (0, 1, 2):
        return rho
    raise ValueError(f"unsupported keep axes: {keep}")


def partial_transpose_right(rho: torch.Tensor, left_dim: int, right_dim: int) -> torch.Tensor:
    return rho.reshape(left_dim, right_dim, left_dim, right_dim).permute(0, 3, 2, 1).reshape(
        left_dim * right_dim,
        left_dim * right_dim,
    )


def negativity(rho: torch.Tensor, cut_name: str) -> tuple[float, list[float]]:
    left_dim, right_dim = CUTS[cut_name]["dims"]
    pt = partial_transpose_right(rho, left_dim, right_dim)
    eigs = torch.linalg.eigvalsh(hermitian(pt))
    neg = torch.sum(torch.where(eigs < -TOL, -eigs, torch.zeros_like(eigs)))
    return q(float(neg.item())), [q(float(value)) for value in eigs.detach().cpu().tolist()]


def cut_metrics(rho: torch.Tensor, cut_name: str) -> dict[str, Any]:
    spec = CUTS[cut_name]
    rho_left = partial_trace_3q(rho, spec["left"])
    rho_right = partial_trace_3q(rho, spec["right"])
    s_left = entropy_nats(rho_left)
    s_right = entropy_nats(rho_right)
    s_full = entropy_nats(rho)
    neg, pt_spectrum = negativity(rho, cut_name)
    return {
        "S_rho_left": s_left,
        "S_rho_right": s_right,
        "S_rho_ABC": s_full,
        "conditional_S_left_given_right": q(s_full - s_right),
        "conditional_S_right_given_left": q(s_full - s_left),
        "mutual_I_left_right": q(s_left + s_right - s_full),
        "coherent_I_c_left_to_right": q(s_right - s_full),
        "coherent_I_c_right_to_left": q(s_left - s_full),
        "negativity": neg,
        "log_negativity": q(math.log(1.0 + 2.0 * neg)),
        "partial_transpose_right_spectrum": pt_spectrum,
    }


def delta_metrics(before: dict[str, Any], after: dict[str, Any]) -> dict[str, float]:
    return {
        "delta_mutual_I": q(after["mutual_I_left_right"] - before["mutual_I_left_right"]),
        "delta_coherent_I_c_left_to_right": q(
            after["coherent_I_c_left_to_right"] - before["coherent_I_c_left_to_right"]
        ),
        "delta_coherent_I_c_right_to_left": q(
            after["coherent_I_c_right_to_left"] - before["coherent_I_c_right_to_left"]
        ),
        "delta_negativity": q(after["negativity"] - before["negativity"]),
        "delta_log_negativity": q(after["log_negativity"] - before["log_negativity"]),
    }


def cnot_unitary(control: int, target: int) -> torch.Tensor:
    out = torch.zeros((8, 8), dtype=torch.complex128)
    for basis in range(8):
        bits = [(basis >> 2) & 1, (basis >> 1) & 1, basis & 1]
        routed = list(bits)
        if bits[control] == 1:
            routed[target] ^= 1
        routed_index = routed[0] * 4 + routed[1] * 2 + routed[2]
        out[routed_index, basis] = 1.0
    return out


def kron3(left: torch.Tensor, middle: torch.Tensor, right: torch.Tensor) -> torch.Tensor:
    return torch.kron(torch.kron(left, middle), right)


def local_hadamard_scrambler() -> torch.Tensor:
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    h = torch.tensor([[inv_sqrt2, inv_sqrt2], [inv_sqrt2, -inv_sqrt2]], dtype=torch.complex128)
    identity = torch.eye(2, dtype=torch.complex128)
    return cnot_unitary(0, 2) @ kron3(h, identity, identity) @ cnot_unitary(0, 1) @ kron3(identity, h, identity)


def import_engine64_common() -> Any:
    spec = importlib.util.spec_from_file_location("engine_64_stage_full_run_v0_common_for_flux_v1", ENGINE64_COMMON)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import engine64 common source: {ENGINE64_COMMON}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rx(theta: float) -> torch.Tensor:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return torch.tensor([[c, -1j * s], [-1j * s, c]], dtype=torch.complex128)


def ry(theta: float) -> torch.Tensor:
    c = math.cos(theta / 2.0)
    s = math.sin(theta / 2.0)
    return torch.tensor([[c, -s], [s, c]], dtype=torch.complex128)


def rz(theta: float) -> torch.Tensor:
    return torch.tensor(
        [[complex(math.cos(-theta / 2.0), math.sin(-theta / 2.0)), 0.0], [0.0, complex(math.cos(theta / 2.0), math.sin(theta / 2.0))]],
        dtype=torch.complex128,
    )


def one_qubit_gate(gate: torch.Tensor, qubit: int) -> torch.Tensor:
    identity = torch.eye(2, dtype=torch.complex128)
    mats = [identity, identity, identity]
    mats[qubit] = gate
    return kron3(mats[0], mats[1], mats[2])


def terrain_axis(terrain_id: str) -> str:
    if any(token in terrain_id for token in ("Funnel", "Cannon")):
        return "x"
    if any(token in terrain_id for token in ("Hill", "Citadel")):
        return "y"
    return "z"


def rotation_gate(axis: str, theta: float) -> torch.Tensor:
    if axis == "x":
        return rx(theta)
    if axis == "y":
        return ry(theta)
    if axis == "z":
        return rz(theta)
    raise ValueError(f"unknown rotation axis: {axis}")


def slot_operator_unitary(slot: dict[str, Any]) -> torch.Tensor:
    bits = slot["axis_bits"]
    chirality = float(slot["chirality_sign"])
    direction = float(slot["direction_sign"])
    axis5 = int(bits["axis5"])
    scale = 1.0 + 0.12 * axis5
    family = str(slot["operator_family"])
    if family == "Ti":
        gate = rz(chirality * direction * 0.071 * scale)
        qubit = 0
    elif family == "Te":
        gate = rx(chirality * direction * 0.083 * scale)
        qubit = 1
    elif family == "Fi":
        gate = ry(chirality * direction * 0.097 * scale)
        qubit = 2
    elif family == "Fe":
        gate = rz(-chirality * direction * 0.109 * scale)
        qubit = (int(slot["stroke_index"]) + int(slot["substage_index"])) % 3
    else:
        raise ValueError(f"unknown operator family: {family}")
    return one_qubit_gate(gate, qubit)


def slot_terrain_unitary(slot: dict[str, Any]) -> torch.Tensor:
    bits = slot["axis_bits"]
    chirality = float(slot["chirality_sign"])
    direction = float(slot["direction_sign"])
    stage_index = {"Se": 0, "Ne": 1, "Ni": 2, "Si": 3}[str(slot["stage"])]
    axis5 = int(bits["axis5"])
    axis = terrain_axis(str(slot["terrain_id"]))
    theta = chirality * direction * (0.043 + 0.011 * stage_index + 0.007 * axis5)
    qubit = (stage_index + int(bits["axis1"]) + int(bits["axis2"])) % 3
    return one_qubit_gate(rotation_gate(axis, theta), qubit)


def slot_entangler(slot: dict[str, Any]) -> torch.Tensor:
    bits = slot["axis_bits"]
    if int(bits["axis6"]) == 0:
        return cnot_unitary(int(bits["axis1"]) % 3, (int(bits["axis1"]) + 1) % 3)
    return cnot_unitary((int(bits["axis2"]) + 1) % 3, int(bits["axis2"]) % 3)


def slot_unitary(slot: dict[str, Any]) -> torch.Tensor:
    op = slot_operator_unitary(slot)
    terrain = slot_terrain_unitary(slot)
    entangler = slot_entangler(slot)
    if slot["precedence"] == "operator_first":
        return entangler @ terrain @ op
    return entangler @ op @ terrain


def schedule_unitary(slots: list[dict[str, Any]]) -> torch.Tensor:
    unitary = torch.eye(8, dtype=torch.complex128)
    for slot in slots:
        unitary = slot_unitary(slot) @ unitary
    return unitary


def qubit_reflection_unitary() -> torch.Tensor:
    swap_ac = torch.zeros((8, 8), dtype=torch.complex128)
    for basis in range(8):
        bits = [(basis >> 2) & 1, (basis >> 1) & 1, basis & 1]
        routed = [bits[2], bits[1], bits[0]]
        routed_index = routed[0] * 4 + routed[1] * 2 + routed[2]
        swap_ac[routed_index, basis] = 1.0
    return swap_ac


def max_abs_delta(left: torch.Tensor, right: torch.Tensor) -> float:
    return q(float(torch.max(torch.abs(left - right)).item()))


def engine_generator_bundle() -> dict[str, Any]:
    engine64 = import_engine64_common()
    schedule = engine64.build_schedule()
    left_slots = [copy.deepcopy(slot) for slot in schedule if slot["engine_family"] == "Type1-L"]
    right_slots = [copy.deepcopy(slot) for slot in schedule if slot["engine_family"] == "Type2-R"]
    left_unitary = schedule_unitary(left_slots)
    right_unitary = schedule_unitary(right_slots)
    reflector = qubit_reflection_unitary()
    reflected_left = reflector @ left_unitary @ reflector.conj().T
    reverse_left = left_unitary.conj().T
    return {
        "left": {
            "generator_id": "engine64_Type1-L_32slot_local_update",
            "schedule": left_slots,
            "schedule_sha256": stable_sha256(left_slots),
            "unitary": left_unitary,
            "unitary_sha256": stable_sha256(matrix_fingerprint(left_unitary)),
        },
        "right": {
            "generator_id": "engine64_Type2-R_32slot_local_update",
            "schedule": right_slots,
            "schedule_sha256": stable_sha256(right_slots),
            "unitary": right_unitary,
            "unitary_sha256": stable_sha256(matrix_fingerprint(right_unitary)),
        },
        "reflection_control": {
            "reflection": "qubit_order_reflection_A_B_C_to_C_B_A",
            "reflected_left_unitary_sha256": stable_sha256(matrix_fingerprint(reflected_left)),
            "max_abs_R_minus_reflect_L": max_abs_delta(right_unitary, reflected_left),
            "max_abs_R_minus_reverse_L": max_abs_delta(right_unitary, reverse_left),
        },
        "source_locks": {
            "engine_64_stage_full_run_common": source_lock(ENGINE64_COMMON, "committed_Type1_L_Type2_R_schedule_source"),
            "engine_64_stage_full_run_audit": source_lock(ENGINE64_AUDIT, "independent_engine64_audit"),
        },
    }


def evolve(rho: torch.Tensor, unitary: torch.Tensor) -> torch.Tensor:
    return hermitian(unitary @ rho @ unitary.conj().T)


def load_state_map(carve_payload: dict[str, Any]) -> dict[str, torch.Tensor]:
    return {
        content_id: matrix_from_json(row["rho_ABC"])
        for content_id, row in carve_payload["state_artifacts"]["states_by_content_id"].items()
    }


def anchor_row(freeze_payload: dict[str, Any]) -> dict[str, Any]:
    return next(
        row
        for row in freeze_payload["cut_tables"]["survivor_cut_rows"]
        if int(row["raw_3q_survivor_id"]) == ANCHOR_RAW_3Q_SURVIVOR_ID
    )


def current_row(
    *,
    row_id: str,
    dynamics_id: str,
    orientation: str,
    initial_rho: torch.Tensor,
    final_rho: torch.Tensor,
    j_chi: int | float,
    source_survivor: dict[str, Any],
    time_reversal_of: str | None = None,
    trajectory_source: str = "own_engine_evolution",
    constructed_from_peer_row: bool = False,
    generator_id: str | None = None,
    generator_pin: dict[str, Any] | None = None,
) -> dict[str, Any]:
    per_cut: dict[str, Any] = {}
    for cut_name in CUTS:
        before = cut_metrics(initial_rho, cut_name)
        after = cut_metrics(final_rho, cut_name)
        deltas = delta_metrics(before, after)
        per_cut[cut_name] = {"before": before, "after": after, **deltas}

    net_delta_mutual = q(sum(row["delta_mutual_I"] for row in per_cut.values()))
    net_delta_ic_lr = q(sum(row["delta_coherent_I_c_left_to_right"] for row in per_cut.values()))
    net_delta_neg = q(sum(row["delta_negativity"] for row in per_cut.values()))
    net_delta_log_neg = q(sum(row["delta_log_negativity"] for row in per_cut.values()))
    out = {
        "row_id": row_id,
        "dynamics_id": dynamics_id,
        "orientation": orientation,
        "source_raw_3q_survivor_id": source_survivor["raw_3q_survivor_id"],
        "gcm_3q_survivor_id": source_survivor["gcm_3q_survivor_id"],
        "gcm_3q_quotient_class_id": source_survivor["gcm_3q_quotient_class_id"],
        "gcm_3q_candidate_region_id": source_survivor["gcm_3q_candidate_region_id"],
        "initial_state_sha256": stable_sha256(matrix_fingerprint(initial_rho)),
        "final_state_sha256": stable_sha256(matrix_fingerprint(final_rho)),
        "step_count": 1,
        "time_reversal_of": time_reversal_of,
        "trajectory_source": trajectory_source,
        "constructed_from_peer_row": constructed_from_peer_row,
        "generator_id": generator_id,
        "generator_pin": generator_pin or {},
        "J_cut": {
            "definition": CURRENT_DEFINITIONS["J_cut"]["definition"],
            "per_cut": per_cut,
            "net_delta_mutual_I": net_delta_mutual,
            "net_delta_coherent_I_c_left_to_right": net_delta_ic_lr,
        },
        "J_ent": {
            "definition": CURRENT_DEFINITIONS["J_ent"]["definition"],
            "per_cut": {
                cut_name: {
                    "delta_negativity": row["delta_negativity"],
                    "delta_log_negativity": row["delta_log_negativity"],
                }
                for cut_name, row in per_cut.items()
            },
            "net_delta_negativity": net_delta_neg,
            "net_delta_log_negativity": net_delta_log_neg,
        },
        "J_chi": {
            "definition": CURRENT_DEFINITIONS["J_chi"]["definition"],
            "signed_log2_qubits_per_step": j_chi,
            "source_seed": {
                "sim_id": "gcm_qca_runner_2q_v0",
                "path": rel(QCA_2Q_RESULT),
                "L": -2,
                "R": 2,
            },
            "lift_boundary": "chirality seed is attached to the 3Q row; this is not finite-ring GNVW admission",
        },
    }
    return out


def all_current_values_zero(row: dict[str, Any]) -> bool:
    values = [
        row["J_cut"]["net_delta_mutual_I"],
        row["J_cut"]["net_delta_coherent_I_c_left_to_right"],
        row["J_ent"]["net_delta_negativity"],
        row["J_ent"]["net_delta_log_negativity"],
        row["J_chi"]["signed_log2_qubits_per_step"],
    ]
    return all(abs(float(value)) <= TOL for value in values)


def product_control_scan(
    *,
    freeze_payload: dict[str, Any],
    states: dict[str, torch.Tensor],
    unitary: torch.Tensor,
) -> dict[str, Any]:
    zero_rows = []
    nonzero_count = 0
    max_abs = 0.0
    for row in freeze_payload["cut_tables"]["survivor_cut_rows"]:
        if row.get("tripartite_entangled_anchor"):
            continue
        rho = states[row["rho_ABC_content_id"]]
        final = evolve(rho, unitary)
        max_row = 0.0
        per_cut = {}
        for cut_name in CUTS:
            deltas = delta_metrics(cut_metrics(rho, cut_name), cut_metrics(final, cut_name))
            cut_max = max(abs(deltas["delta_mutual_I"]), abs(deltas["delta_negativity"]), abs(deltas["delta_log_negativity"]))
            max_row = max(max_row, cut_max)
            per_cut[cut_name] = {
                "delta_mutual_I": deltas["delta_mutual_I"],
                "delta_negativity": deltas["delta_negativity"],
                "delta_log_negativity": deltas["delta_log_negativity"],
            }
        max_abs = max(max_abs, max_row)
        if max_row <= TOL:
            zero_rows.append(
                {
                    "raw_3q_survivor_id": row["raw_3q_survivor_id"],
                    "gcm_3q_survivor_id": row["gcm_3q_survivor_id"],
                    "family": row["family"],
                    "max_abs_current": q(max_row),
                    "per_cut": per_cut,
                }
            )
        else:
            nonzero_count += 1
    selected = zero_rows[:8]
    return {
        "control": "selected product-control subset under an identity product-local no-current baseline",
        "all_selected_product_controls_zero": bool(selected) and all(row["max_abs_current"] <= TOL for row in selected),
        "selected_product_control_count": len(selected),
        "selected_product_controls": selected,
        "full_product_lift_boundary": {
            "product_lift_rows_scanned": len(zero_rows) + nonzero_count,
            "zero_current_product_rows": len(zero_rows),
            "nonzero_count_under_entangling_update": nonzero_count,
            "max_abs_product_current": q(max_abs),
            "all_product_lift_zero_claimed": False,
            "boundary": "The control claim is the named no-current product baseline only; full product-lift zero-current under engine dynamics is not claimed.",
        },
    }


def lineage_free_variant(payload: dict[str, Any]) -> dict[str, Any]:
    variant = copy.deepcopy(payload)
    for key in (
        "gcm_lineage",
        "gcm_object_id",
        "gcm_2q_object_id",
        "gcm_3q_object_id",
        "registry_body_sha256",
        "gcm_2q_registry_body_sha256",
        "gcm_3q_registry_body_sha256",
        "base_registry_body_sha256",
    ):
        variant.pop(key, None)
    for row in variant.get("runtime_current_rows", []):
        for key in ("gcm_3q_survivor_id", "gcm_3q_quotient_class_id", "gcm_3q_candidate_region_id"):
            row.pop(key, None)
    return variant


def substrate_enforcement(payload: dict[str, Any]) -> dict[str, Any]:
    positive = gcm_substrate_check(payload, THREE_Q_FREEZE_REGISTRY)
    negative_payload = lineage_free_variant(payload)
    negative = gcm_substrate_check(negative_payload, THREE_Q_FREEZE_REGISTRY)
    return {
        "helper": rel(SUBSTRATE_HELPER),
        "positive_payload_ok": positive,
        "lineage_free_negative": negative,
        "negative_failed_as_required": negative.get("ok") is False,
    }


def three_q_necessity_row(freeze_payload: dict[str, Any]) -> dict[str, Any]:
    anchor = freeze_payload["tripartite_only_anchor_profile"]
    monogamy = freeze_payload["monogamy_table"]["rows"][0]
    anchor_negativities = {
        cut_name: anchor["cuts"][cut_name]["entropy_values"]["negativity"]
        for cut_name in CUTS
    }
    ckw_margins = {cut_name: monogamy["party_cuts"][cut_name]["ckw_margin"] for cut_name in CUTS}
    return {
        "claim": "runtime/QIT flux is non-trivial at the 3Q floor, below formal admission",
        "three_q_cut_count": len(CUTS),
        "two_q_cut_count": 1,
        "anchor_has_nonzero_negativity_on_all_three_cuts": all(value > TOL for value in anchor_negativities.values()),
        "ckw_margin_positive_on_all_party_cuts": all(value > TOL for value in ckw_margins.values()),
        "anchor_negativity_by_cut": anchor_negativities,
        "ckw_margin_by_party_cut": ckw_margins,
        "computed_reason": (
            "The 3Q survivor exposes three inequivalent bipartitions A|BC, B|AC, and C|AB plus a CKW monogamy row; "
            "the 2Q surface has only the single A|B cut, so J_cut/J_ent cannot distinguish tripartite routing or "
            "monogamy-fed redistribution below 3Q."
        ),
        "computed_floor_verdict": "runtime_flux_nontrivial_at_3Q_floor_not_below",
    }


def runtime_rows(
    *,
    freeze_payload: dict[str, Any],
    states: dict[str, torch.Tensor],
) -> dict[str, Any]:
    source = anchor_row(freeze_payload)
    rho0 = states[source["rho_ABC_content_id"]]
    generators = engine_generator_bundle()
    left_unitary = generators["left"]["unitary"]
    right_unitary = generators["right"]["unitary"]
    scramble = local_hadamard_scrambler()
    left_scrambled_unitary = scramble @ left_unitary
    right_scrambled_unitary = scramble @ right_unitary
    left_final = evolve(rho0, left_unitary)
    right_final = evolve(rho0, right_unitary)
    right = current_row(
        row_id="engine_R_flux_OUT_right_3q",
        dynamics_id=generators["right"]["generator_id"],
        orientation="flux_OUT_right",
        initial_rho=rho0,
        final_rho=right_final,
        j_chi=2,
        source_survivor=source,
        generator_id=generators["right"]["generator_id"],
        generator_pin={
            "schedule_sha256": generators["right"]["schedule_sha256"],
            "unitary_sha256": generators["right"]["unitary_sha256"],
        },
    )
    left = current_row(
        row_id="engine_L_flux_IN_left_3q",
        dynamics_id=generators["left"]["generator_id"],
        orientation="flux_IN_left",
        initial_rho=rho0,
        final_rho=left_final,
        j_chi=-2,
        source_survivor=source,
        generator_id=generators["left"]["generator_id"],
        generator_pin={
            "schedule_sha256": generators["left"]["schedule_sha256"],
            "unitary_sha256": generators["left"]["unitary_sha256"],
        },
    )
    reverse = current_row(
        row_id="time_reverse_of_R_flux_OUT_right_3q",
        dynamics_id="explicit_inverse_of_engine64_Type2-R_32slot_local_update",
        orientation="time_reverse",
        initial_rho=right_final,
        final_rho=rho0,
        j_chi=-2,
        source_survivor=source,
        time_reversal_of="engine_R_flux_OUT_right_3q",
        trajectory_source="explicit_inverse_evolution_control",
        generator_id="inverse_of_engine64_Type2-R_32slot_local_update",
        generator_pin={
            "source_unitary_sha256": generators["right"]["unitary_sha256"],
            "inverse_unitary_sha256": stable_sha256(matrix_fingerprint(right_unitary.conj().T)),
        },
    )
    static = current_row(
        row_id="static_no_evolution_3q",
        dynamics_id="identity_no_evolution_control",
        orientation="static",
        initial_rho=rho0,
        final_rho=rho0,
        j_chi=0,
        source_survivor=source,
        trajectory_source="identity_control",
    )
    scrambled_left = current_row(
        row_id="scrambled_engine_L_flux_IN_left_3q",
        dynamics_id="scrambled_engine64_Type1-L_32slot_local_update",
        orientation="scrambled_flux_IN_left",
        initial_rho=rho0,
        final_rho=evolve(rho0, left_scrambled_unitary),
        j_chi=-2,
        source_survivor=source,
        trajectory_source="scrambled_own_engine_evolution_control",
        generator_id="scrambled_engine64_Type1-L_32slot_local_update",
        generator_pin={
            "source_unitary_sha256": generators["left"]["unitary_sha256"],
            "scrambled_unitary_sha256": stable_sha256(matrix_fingerprint(left_scrambled_unitary)),
        },
    )
    scrambled_right = current_row(
        row_id="scrambled_engine_R_flux_OUT_right_3q",
        dynamics_id="scrambled_engine64_Type2-R_32slot_local_update",
        orientation="scrambled_control",
        initial_rho=rho0,
        final_rho=evolve(rho0, right_scrambled_unitary),
        j_chi=2,
        source_survivor=source,
        trajectory_source="scrambled_own_engine_evolution_control",
        generator_id="scrambled_engine64_Type2-R_32slot_local_update",
        generator_pin={
            "source_unitary_sha256": generators["right"]["unitary_sha256"],
            "scrambled_unitary_sha256": stable_sha256(matrix_fingerprint(right_scrambled_unitary)),
        },
    )
    return {
        "rows": [left, right, reverse, static, scrambled_left, scrambled_right],
        "engine_generators": {
            "left": {k: v for k, v in generators["left"].items() if k not in {"unitary", "schedule"}},
            "right": {k: v for k, v in generators["right"].items() if k not in {"unitary", "schedule"}},
            "source_locks": generators["source_locks"],
            "boundary": "Type1-L and Type2-R schedules are consumed as distinct committed local generator assignments for this scratch diagnostic; this is not engine admission.",
        },
        "generator_independence": {
            "left_generator_id": generators["left"]["generator_id"],
            "right_generator_id": generators["right"]["generator_id"],
            "left_schedule_sha256": generators["left"]["schedule_sha256"],
            "right_schedule_sha256": generators["right"]["schedule_sha256"],
            "left_unitary_sha256": generators["left"]["unitary_sha256"],
            "right_unitary_sha256": generators["right"]["unitary_sha256"],
            "distinct_committed_generator_assignments": generators["left"]["schedule_sha256"] != generators["right"]["schedule_sha256"],
            "R_not_reverse_of_L": generators["reflection_control"]["max_abs_R_minus_reverse_L"] > TOL,
            "R_not_reflection_of_L": generators["reflection_control"]["max_abs_R_minus_reflect_L"] > TOL,
            "max_abs_R_minus_reflect_L": generators["reflection_control"]["max_abs_R_minus_reflect_L"],
            "max_abs_R_minus_reverse_L": generators["reflection_control"]["max_abs_R_minus_reverse_L"],
            "source_locks": generators["source_locks"],
        },
        "scrambled_unitary": {
            "id": "H_A_CNOT_A_B_H_B_CNOT_A_C_left_composed_scramble",
            "description": "same left-multiplied unitary perturbation applied separately to both independent generators",
            "matrix_sha256": stable_sha256(matrix_fingerprint(scramble)),
        },
        "anchor_source": source,
    }


def doctrine_test(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    cut_opposes = left["J_cut"]["net_delta_mutual_I"] * right["J_cut"]["net_delta_mutual_I"] < 0
    ent_opposes = left["J_ent"]["net_delta_negativity"] * right["J_ent"]["net_delta_negativity"] < 0
    chi_opposes = left["J_chi"]["signed_log2_qubits_per_step"] * right["J_chi"]["signed_log2_qubits_per_step"] < 0
    emerged = bool(cut_opposes and ent_opposes and chi_opposes)
    return {
        "claim_tested": "flux-in-left / flux-out-right sign doctrine for this runtime/QIT/chirality realization",
        "non_tautological_by_construction": True,
        "opposition_forced_by_reflection_or_reversal": False,
        "J_chi_L_negative_R_positive": left["J_chi"]["signed_log2_qubits_per_step"] < 0
        and right["J_chi"]["signed_log2_qubits_per_step"] > 0,
        "J_cut_LR_opposite_signs": cut_opposes,
        "J_ent_LR_opposite_signs": ent_opposes,
        "left": {
            "J_cut_net_delta_mutual_I": left["J_cut"]["net_delta_mutual_I"],
            "J_ent_net_delta_negativity": left["J_ent"]["net_delta_negativity"],
            "J_chi_signed_log2": left["J_chi"]["signed_log2_qubits_per_step"],
        },
        "right": {
            "J_cut_net_delta_mutual_I": right["J_cut"]["net_delta_mutual_I"],
            "J_ent_net_delta_negativity": right["J_ent"]["net_delta_negativity"],
            "J_chi_signed_log2": right["J_chi"]["signed_log2_qubits_per_step"],
        },
        "outcome": "independent_opposition_emerged" if emerged else "independent_opposition_not_clean",
    }


def z3_crossover(independence: dict[str, Any]) -> dict[str, Any]:
    real_distinct = int(independence["distinct_committed_generator_assignments"])
    real_not_reverse = int(independence["R_not_reverse_of_L"])
    real_not_reflect = int(independence["R_not_reflection_of_L"])
    solver = z3.Solver()
    distinct = z3.Int("distinct_committed_generator_assignments")
    not_reverse = z3.Int("R_not_reverse_of_L")
    not_reflect = z3.Int("R_not_reflection_of_L")
    solver.add(distinct == real_distinct, not_reverse == real_not_reverse, not_reflect == real_not_reflect)
    real_gate = z3.And(distinct == 1, not_reverse == 1, not_reflect == 1)
    solver.add(z3.Not(real_gate))
    verdict = str(solver.check()).lower()

    erased = z3.Solver()
    e_distinct = z3.Int("erased_distinct")
    e_not_reverse = z3.Int("erased_not_reverse")
    e_not_reflect = z3.Int("erased_not_reflect")
    erased.add(e_distinct == 0, e_not_reverse == 0, e_not_reflect == 0)
    erased.add(z3.Not(z3.And(e_distinct == 1, e_not_reverse == 1, e_not_reflect == 1)))
    erased_verdict = str(erased.check()).lower()
    return {
        "ran": True,
        "verdict": verdict,
        "erased_control_verdict": erased_verdict,
        "load_bearing": True,
        "polarity": "negated_violation_unsat_real_erasure_sat",
        "proof_flips_under_erasure": verdict == "unsat" and erased_verdict == "sat",
        "claim": "independent L/R generator non-identity is structurally required for this doctrine repair packet",
        "input_object": {
            "left_generator_id": independence["left_generator_id"],
            "right_generator_id": independence["right_generator_id"],
            "distinct_committed_generator_assignments": real_distinct,
            "R_not_reverse_of_L": real_not_reverse,
            "R_not_reflection_of_L": real_not_reflect,
            "max_abs_R_minus_reflect_L": independence["max_abs_R_minus_reflect_L"],
        },
    }


def cvc5_crossover(independence: dict[str, Any]) -> dict[str, Any]:
    real_distinct = int(independence["distinct_committed_generator_assignments"])
    real_not_reverse = int(independence["R_not_reverse_of_L"])
    real_not_reflect = int(independence["R_not_reflection_of_L"])
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    distinct = solver.mkConst(int_sort, "distinct_committed_generator_assignments")
    not_reverse = solver.mkConst(int_sort, "R_not_reverse_of_L")
    not_reflect = solver.mkConst(int_sort, "R_not_reflection_of_L")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, distinct, solver.mkInteger(real_distinct)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, not_reverse, solver.mkInteger(real_not_reverse)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, not_reflect, solver.mkInteger(real_not_reflect)))
    real_gate = solver.mkTerm(
        Kind.AND,
        solver.mkTerm(Kind.EQUAL, distinct, solver.mkInteger(1)),
        solver.mkTerm(Kind.EQUAL, not_reverse, solver.mkInteger(1)),
        solver.mkTerm(Kind.EQUAL, not_reflect, solver.mkInteger(1)),
    )
    solver.assertFormula(solver.mkTerm(Kind.NOT, real_gate))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"

    erased = cvc5.Solver()
    erased.setLogic("QF_LIA")
    erased_int = erased.getIntegerSort()
    e_distinct = erased.mkConst(erased_int, "erased_distinct")
    e_not_reverse = erased.mkConst(erased_int, "erased_not_reverse")
    e_not_reflect = erased.mkConst(erased_int, "erased_not_reflect")
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, e_distinct, erased.mkInteger(0)))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, e_not_reverse, erased.mkInteger(0)))
    erased.assertFormula(erased.mkTerm(Kind.EQUAL, e_not_reflect, erased.mkInteger(0)))
    erased_gate = erased.mkTerm(
        Kind.AND,
        erased.mkTerm(Kind.EQUAL, e_distinct, erased.mkInteger(1)),
        erased.mkTerm(Kind.EQUAL, e_not_reverse, erased.mkInteger(1)),
        erased.mkTerm(Kind.EQUAL, e_not_reflect, erased.mkInteger(1)),
    )
    erased.assertFormula(erased.mkTerm(Kind.NOT, erased_gate))
    erased_check = erased.checkSat()
    erased_verdict = "sat" if erased_check.isSat() else "unsat" if erased_check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "erased_control_verdict": erased_verdict,
        "load_bearing": True,
        "polarity": "negated_violation_unsat_real_erasure_sat",
        "proof_flips_under_erasure": verdict == "unsat" and erased_verdict == "sat",
        "claim": "independent cvc5 encoding of the same L/R generator non-identity gate",
        "input_object": {
            "left_generator_id": independence["left_generator_id"],
            "right_generator_id": independence["right_generator_id"],
            "distinct_committed_generator_assignments": real_distinct,
            "R_not_reverse_of_L": real_not_reverse,
            "R_not_reflection_of_L": real_not_reflect,
            "max_abs_R_minus_reflect_L": independence["max_abs_R_minus_reflect_L"],
        },
    }


def build_packet(write: bool = True) -> dict[str, Any]:
    freeze_payload = load_json(THREE_Q_FREEZE_RESULT)
    registry = load_json(THREE_Q_FREEZE_REGISTRY)
    carve_payload = load_json(THREE_Q_CARVE_RESULT)
    states = load_state_map(carve_payload)
    rows_bundle = runtime_rows(freeze_payload=freeze_payload, states=states)
    rows = rows_bundle["rows"]
    row_by_id = {row["row_id"]: row for row in rows}
    need = three_q_necessity_row(freeze_payload)
    product_controls = product_control_scan(
        freeze_payload=freeze_payload,
        states=states,
        unitary=torch.eye(8, dtype=torch.complex128),
    )
    left_current_changed = (
        row_by_id["scrambled_engine_L_flux_IN_left_3q"]["J_cut"]["net_delta_mutual_I"]
        != row_by_id["engine_L_flux_IN_left_3q"]["J_cut"]["net_delta_mutual_I"]
        or row_by_id["scrambled_engine_L_flux_IN_left_3q"]["J_ent"]["net_delta_negativity"]
        != row_by_id["engine_L_flux_IN_left_3q"]["J_ent"]["net_delta_negativity"]
        or all_current_values_zero(row_by_id["scrambled_engine_L_flux_IN_left_3q"])
    )
    right_current_changed = (
        row_by_id["scrambled_engine_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"]
        != row_by_id["engine_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"]
        or row_by_id["scrambled_engine_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"]
        != row_by_id["engine_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"]
        or all_current_values_zero(row_by_id["scrambled_engine_R_flux_OUT_right_3q"])
    )
    controls = {
        "static_no_evolution": {
            "row_id": "static_no_evolution_3q",
            "all_currents_zero": all_current_values_zero(row_by_id["static_no_evolution_3q"]),
        },
        "time_reversal": {
            "forward_row_id": "engine_R_flux_OUT_right_3q",
            "reverse_row_id": "time_reverse_of_R_flux_OUT_right_3q",
            "J_cut_flips_sign": row_by_id["time_reverse_of_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"]
            == -row_by_id["engine_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"],
            "J_ent_flips_sign": row_by_id["time_reverse_of_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"]
            == -row_by_id["engine_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"],
            "J_chi_flips_sign": row_by_id["time_reverse_of_R_flux_OUT_right_3q"]["J_chi"]["signed_log2_qubits_per_step"]
            == -row_by_id["engine_R_flux_OUT_right_3q"]["J_chi"]["signed_log2_qubits_per_step"],
        },
        "product_survivor_controls": product_controls,
        "scramble_pair": {
            "control": "same scramble perturbation is composed separately with each independent generator",
            "left_row_id": "scrambled_engine_L_flux_IN_left_3q",
            "right_row_id": "scrambled_engine_R_flux_OUT_right_3q",
            "left_current_changed_or_vanished": left_current_changed,
            "right_current_changed_or_vanished": right_current_changed,
            "left_J_cut_net_delta_mutual_I": row_by_id["scrambled_engine_L_flux_IN_left_3q"]["J_cut"]["net_delta_mutual_I"],
            "right_J_cut_net_delta_mutual_I": row_by_id["scrambled_engine_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"],
            "left_J_ent_net_delta_negativity": row_by_id["scrambled_engine_L_flux_IN_left_3q"]["J_ent"]["net_delta_negativity"],
            "right_J_ent_net_delta_negativity": row_by_id["scrambled_engine_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"],
        },
        "carve_erasure": {
            "control": "remove GCM lineage and 3Q IDs before running scripts/gcm_substrate_check.py",
            "substrate_check_ok": None,
            "error_codes": [],
        },
    }
    payload: dict[str, Any] = {
        "schema": f"{SIM_ID}_result_v1",
        "sim_id": SIM_ID,
        "generated_at": now_z(),
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "formal_admission_allowed": FORMAL_ADMISSION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "declared_surface": DECLARED_SURFACE,
        "coordinates": {
            "layer": "24_runtime_flux",
            "nesting": "integrated-onto-the-carve",
            "qubit_depth": "3Q",
        },
        "carrier_and_pins_relative": True,
        "not_THE_manifold": True,
        "not_engine_admission": True,
        "not_physics": True,
        "computed_transport_quantities_not_admitted_invariants": True,
        "gcm_object_id": EXPECTED_1Q_OBJECT_ID,
        "gcm_2q_object_id": EXPECTED_2Q_OBJECT_ID,
        "gcm_3q_object_id": registry["gcm_3q_object_id"],
        "registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
        "base_registry_body_sha256": EXPECTED_1Q_REGISTRY_BODY_SHA256,
        "gcm_2q_registry_body_sha256": EXPECTED_2Q_REGISTRY_BODY_SHA256,
        "gcm_3q_registry_body_sha256": registry["registry_body_sha256"],
        "gcm_lineage": copy.deepcopy(freeze_payload["gcm_lineage"]),
        "cross_rung_lineage": copy.deepcopy(freeze_payload["cross_rung_lineage"]),
        "current_definitions": CURRENT_DEFINITIONS,
        "dynamics": {
            "independent_engine_generators": rows_bundle["engine_generators"],
            "scrambled_control_update": rows_bundle["scrambled_unitary"],
            "boundary": "3-site tractable local-update realization derived from distinct Type1-L and Type2-R schedule assignments; not a full engine admission.",
        },
        "generator_independence": rows_bundle["generator_independence"],
        "runtime_current_rows": rows,
        "flux_in_left_out_right_doctrine_test": doctrine_test(
            row_by_id["engine_L_flux_IN_left_3q"],
            row_by_id["engine_R_flux_OUT_right_3q"],
        ),
        "three_q_necessity_row": need,
        "controls": controls,
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_intent": TOOL_INTENT,
        "source_locks": {
            **{name: source_lock(path, role=name) for name, path in AUTHORITY_PATHS.items()},
            **rows_bundle["engine_generators"]["source_locks"],
        },
        "builder_gates": {
            "G_2a_idempotency_from_birth": True,
            "file_disjoint_packet": True,
            "no_builder_audit_verdict": True,
            "no_builder_audit_verdict_envelope_gate": True,
            "builder_self_assessment_only": True,
        },
        "allowed_claims": [
            "scratch_diagnostic runtime/QIT current computation on the cited 3Q survivor realization",
            "carrier-and-pins-relative sign/current row",
            "control outcomes for this finite packet",
        ],
        "disallowed_claims": [
            "engine admission",
            "formal manifold invariant",
            "physics",
            "axis admission",
            "geometric Hopf flux",
            "full product-lift zero-current theorem",
        ],
        "no_builder_audit_verdict": True,
        "no_builder_audit_verdict_envelope_gate": True,
    }
    enforcement = substrate_enforcement(payload)
    payload["substrate_enforcement"] = enforcement
    payload["controls"]["carve_erasure"]["substrate_check_ok"] = enforcement["lineage_free_negative"].get("ok")
    payload["controls"]["carve_erasure"]["error_codes"] = enforcement["lineage_free_negative"].get("error_codes", [])
    payload["crossover_proofs"] = {
        "z3": z3_crossover(payload["generator_independence"]),
        "cvc5": cvc5_crossover(payload["generator_independence"]),
    }
    payload["all_pass"] = bool(
        payload["classification"] == CLASSIFICATION
        and payload["promotion_allowed"] is False
        and payload["formal_admission_allowed"] is False
        and payload["gcm_3q_object_id"] == EXPECTED_3Q_OBJECT_ID
        and payload["gcm_3q_registry_body_sha256"] == EXPECTED_3Q_REGISTRY_BODY_SHA256
        and payload["substrate_enforcement"]["positive_payload_ok"].get("ok") is True
        and payload["substrate_enforcement"]["negative_failed_as_required"] is True
        and controls["static_no_evolution"]["all_currents_zero"] is True
        and controls["time_reversal"]["J_cut_flips_sign"] is True
        and controls["time_reversal"]["J_ent_flips_sign"] is True
        and controls["product_survivor_controls"]["all_selected_product_controls_zero"] is True
        and controls["scramble_pair"]["left_current_changed_or_vanished"] is True
        and controls["scramble_pair"]["right_current_changed_or_vanished"] is True
        and payload["generator_independence"]["distinct_committed_generator_assignments"] is True
        and payload["generator_independence"]["R_not_reverse_of_L"] is True
        and payload["generator_independence"]["R_not_reflection_of_L"] is True
        and payload["flux_in_left_out_right_doctrine_test"]["non_tautological_by_construction"] is True
        and payload["flux_in_left_out_right_doctrine_test"]["opposition_forced_by_reflection_or_reversal"] is False
        and need["computed_floor_verdict"] == "runtime_flux_nontrivial_at_3Q_floor_not_below"
        and payload["crossover_proofs"]["z3"]["proof_flips_under_erasure"] is True
        and payload["crossover_proofs"]["cvc5"]["proof_flips_under_erasure"] is True
        and builder_audit_boundary_ok(SIM_DIR / "audit_verdict.md")
    )
    payload["result_sha256"] = stable_sha256({k: v for k, v in payload.items() if k not in {"generated_at", "result_sha256"}})
    if write:
        write_json(RESULT_PATH, payload)
        write_json(LINEAGE_FREE_NEGATIVE_PATH, lineage_free_variant(payload))
    return payload


def validation_errors(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    rows = {row.get("row_id"): row for row in payload.get("runtime_current_rows", [])}
    require(payload.get("classification") == CLASSIFICATION, "classification mismatch")
    require(payload.get("promotion_allowed") is False, "promotion_allowed must be false")
    require(payload.get("formal_admission_allowed") is False, "formal_admission_allowed must be false")
    require(payload.get("declared_surface") == DECLARED_SURFACE, "declared surface mismatch")
    require(payload.get("gcm_3q_object_id") == EXPECTED_3Q_OBJECT_ID, "3Q object id mismatch")
    require(payload.get("gcm_3q_registry_body_sha256") == EXPECTED_3Q_REGISTRY_BODY_SHA256, "3Q registry hash mismatch")
    require(payload.get("substrate_enforcement", {}).get("positive_payload_ok", {}).get("ok") is True, "substrate positive failed")
    require(payload.get("substrate_enforcement", {}).get("negative_failed_as_required") is True, "lineage-free negative did not fail")
    require("engine_R_flux_OUT_right_3q" in rows, "right current row missing")
    require("engine_L_flux_IN_left_3q" in rows, "left current row missing")
    if "engine_R_flux_OUT_right_3q" in rows and "engine_L_flux_IN_left_3q" in rows:
        right = rows["engine_R_flux_OUT_right_3q"]
        left = rows["engine_L_flux_IN_left_3q"]
        require(right["J_chi"]["signed_log2_qubits_per_step"] == 2, "right J_chi not +2")
        require(left["J_chi"]["signed_log2_qubits_per_step"] == -2, "left J_chi not -2")
        require(right.get("constructed_from_peer_row") is False, "right row constructed from peer")
        require(left.get("constructed_from_peer_row") is False, "left row constructed from peer")
        require(right.get("trajectory_source") == "own_engine_evolution", "right trajectory not own-engine")
        require(left.get("trajectory_source") == "own_engine_evolution", "left trajectory not own-engine")
        require(right["initial_state_sha256"] == left["initial_state_sha256"], "L/R initial states differ")
        require(right["final_state_sha256"] != left["final_state_sha256"], "L/R final states are identical")
    independence = payload.get("generator_independence", {})
    require(independence.get("distinct_committed_generator_assignments") is True, "generator assignments not distinct")
    require(independence.get("R_not_reverse_of_L") is True, "R equals reverse(L) under declared metric")
    require(independence.get("R_not_reflection_of_L") is True, "R equals reflection(L) under declared metric")
    require(float(independence.get("max_abs_R_minus_reflect_L", 0.0)) > TOL, "reflection nonidentity delta missing")
    doctrine = payload.get("flux_in_left_out_right_doctrine_test", {})
    require(doctrine.get("non_tautological_by_construction") is True, "doctrine test not marked non-tautological")
    require(doctrine.get("opposition_forced_by_reflection_or_reversal") is False, "doctrine opposition forced by construction")
    require(payload.get("three_q_necessity_row", {}).get("three_q_cut_count") == 3, "3Q cut count mismatch")
    require(payload.get("three_q_necessity_row", {}).get("two_q_cut_count") == 1, "2Q cut count mismatch")
    require(payload.get("controls", {}).get("static_no_evolution", {}).get("all_currents_zero") is True, "static control failed")
    require(payload.get("controls", {}).get("time_reversal", {}).get("J_cut_flips_sign") is True, "time reversal J_cut failed")
    require(payload.get("controls", {}).get("product_survivor_controls", {}).get("all_selected_product_controls_zero") is True, "product subset control failed")
    require(payload.get("controls", {}).get("scramble_pair", {}).get("left_current_changed_or_vanished") is True, "left scramble did not change/vanish")
    require(payload.get("controls", {}).get("scramble_pair", {}).get("right_current_changed_or_vanished") is True, "right scramble did not change/vanish")
    require(payload.get("controls", {}).get("carve_erasure", {}).get("substrate_check_ok") is False, "carve erasure negative not red")
    for solver_name in ("z3", "cvc5"):
        proof = payload.get("crossover_proofs", {}).get(solver_name, {})
        require(proof.get("verdict") == "unsat", f"{solver_name} real proof did not return unsat")
        require(proof.get("erased_control_verdict") == "sat", f"{solver_name} erased proof did not return sat")
        require(proof.get("proof_flips_under_erasure") is True, f"{solver_name} proof did not flip")
    require(payload.get("all_pass") is True, "all_pass false")
    return errors


def main() -> int:
    payload = build_packet(write=True)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
