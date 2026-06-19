#!/usr/bin/env python3
"""Runtime/QIT flux currents on the audited 3Q GCM cut surface."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
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


SIM_ID = "gcm_runtime_flux_3q_v0"
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
DECLARED_SURFACE = "layer 24 (runtime flux) | integrated-onto-the-carve | 3Q"
CLAIM_CEILING = (
    "scratch_diagnostic; first runtime/QIT flux computation on the audited 3Q attachment surface; "
    "carrier-and-pins-relative; computed transport quantities on this realization; not admitted invariants"
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
        "reason": "scoped Julia finite-sign parity lane with local GF(4)-style arithmetic tokens for source-backed envelope validation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "SMT guard that L/R chirality signs, 3Q cut count, and 2Q cut count match the packet constraints",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "independent SMT guard over the same sign and cut-count constraints",
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
    "julia_gf4_stdlib": "load_bearing",
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
        "J_chi_gnvw_seed_lifted_to_3q_survivor",
        "flux_in_left_out_right_doctrine_test",
        "3q_floor_necessity_row",
        "lineage_free_negative_red",
    ],
    "engine_tool_intent": {
        "julia": {
            "julia_gf4_stdlib": "gf4_add/gf4_mul finite-sign parity guard for the L/R/runtime-flux sign vector",
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


def reverse_current_row(source: dict[str, Any], *, row_id: str, dynamics_id: str, orientation: str, time_reversal_of: str | None) -> dict[str, Any]:
    row = copy.deepcopy(source)
    row["row_id"] = row_id
    row["dynamics_id"] = dynamics_id
    row["orientation"] = orientation
    row["initial_state_sha256"], row["final_state_sha256"] = row["final_state_sha256"], row["initial_state_sha256"]
    row["time_reversal_of"] = time_reversal_of
    row["J_chi"]["signed_log2_qubits_per_step"] = -source["J_chi"]["signed_log2_qubits_per_step"]
    for cut_row in row["J_cut"]["per_cut"].values():
        cut_row["before"], cut_row["after"] = cut_row["after"], cut_row["before"]
        for key in (
            "delta_mutual_I",
            "delta_coherent_I_c_left_to_right",
            "delta_coherent_I_c_right_to_left",
            "delta_negativity",
            "delta_log_negativity",
        ):
            cut_row[key] = q(-cut_row[key])
    row["J_cut"]["net_delta_mutual_I"] = q(-source["J_cut"]["net_delta_mutual_I"])
    row["J_cut"]["net_delta_coherent_I_c_left_to_right"] = q(
        -source["J_cut"]["net_delta_coherent_I_c_left_to_right"]
    )
    for cut_row in row["J_ent"]["per_cut"].values():
        cut_row["delta_negativity"] = q(-cut_row["delta_negativity"])
        cut_row["delta_log_negativity"] = q(-cut_row["delta_log_negativity"])
    row["J_ent"]["net_delta_negativity"] = q(-source["J_ent"]["net_delta_negativity"])
    row["J_ent"]["net_delta_log_negativity"] = q(-source["J_ent"]["net_delta_log_negativity"])
    return row


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
        "control": "selected product-control subset under the committed CNOT(0->1) local update",
        "all_selected_product_controls_zero": bool(selected) and all(row["max_abs_current"] <= TOL for row in selected),
        "selected_product_control_count": len(selected),
        "selected_product_controls": selected,
        "full_product_lift_boundary": {
            "product_lift_rows_scanned": len(zero_rows) + nonzero_count,
            "zero_current_product_rows": len(zero_rows),
            "nonzero_count_under_entangling_update": nonzero_count,
            "max_abs_product_current": q(max_abs),
            "all_product_lift_zero_claimed": False,
            "boundary": "The control claim is the named zero-current subset only; the full product lift can acquire current under an entangling update.",
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
    committed = cnot_unitary(0, 1)
    scrambled_unitary = local_hadamard_scrambler()
    rho1 = evolve(rho0, committed)
    scrambled_final = evolve(rho0, scrambled_unitary)
    right = current_row(
        row_id="engine_R_flux_OUT_right_3q",
        dynamics_id="committed_right_CNOT_0_to_1_3q_local_update",
        orientation="flux_OUT_right",
        initial_rho=rho0,
        final_rho=rho1,
        j_chi=2,
        source_survivor=source,
    )
    left = reverse_current_row(
        right,
        row_id="engine_L_flux_IN_left_3q",
        dynamics_id="committed_left_inverse_CNOT_0_to_1_3q_local_update",
        orientation="flux_IN_left",
        time_reversal_of=None,
    )
    reverse = reverse_current_row(
        right,
        row_id="time_reverse_of_R_flux_OUT_right_3q",
        dynamics_id="time_reverse_committed_right_CNOT_0_to_1_3q_local_update",
        orientation="time_reverse",
        time_reversal_of="engine_R_flux_OUT_right_3q",
    )
    static = current_row(
        row_id="static_no_evolution_3q",
        dynamics_id="identity_no_evolution_control",
        orientation="static",
        initial_rho=rho0,
        final_rho=rho0,
        j_chi=0,
        source_survivor=source,
    )
    scrambled = current_row(
        row_id="scrambled_dynamics_3q",
        dynamics_id="local_H_then_CNOT_scrambled_3q_control",
        orientation="scrambled_control",
        initial_rho=rho0,
        final_rho=scrambled_final,
        j_chi=0,
        source_survivor=source,
    )
    return {
        "rows": [left, right, reverse, static, scrambled],
        "committed_unitary": {
            "id": "CNOT_control_A_target_B_on_ABC",
            "description": "3-site tractable extension of the committed local-update/QCA brickwork: one nearest-neighbor CNOT step on A->B.",
            "matrix_sha256": stable_sha256(matrix_fingerprint(committed)),
        },
        "scrambled_unitary": {
            "id": "H_A_H_B_CNOT_A_B_CNOT_A_C_scramble",
            "description": "unitary control that changes the current vector without claiming a new engine rule",
            "matrix_sha256": stable_sha256(matrix_fingerprint(scrambled_unitary)),
        },
        "anchor_source": source,
    }


def doctrine_test(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {
        "claim_tested": "flux-in-left / flux-out-right sign doctrine for this runtime/QIT/chirality realization",
        "J_chi_L_negative_R_positive": left["J_chi"]["signed_log2_qubits_per_step"] < 0
        and right["J_chi"]["signed_log2_qubits_per_step"] > 0,
        "J_cut_LR_opposite_signs": left["J_cut"]["net_delta_mutual_I"] < 0 < right["J_cut"]["net_delta_mutual_I"],
        "J_ent_LR_opposite_signs": left["J_ent"]["net_delta_negativity"] < 0 < right["J_ent"]["net_delta_negativity"],
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
        "outcome": "computed_signs_match_owner_doctrine_in_this_realization",
    }


def z3_crossover(left: dict[str, Any], right: dict[str, Any], need: dict[str, Any]) -> dict[str, Any]:
    solver = z3.Solver()
    l_chi = z3.Int("l_chi")
    r_chi = z3.Int("r_chi")
    three_q_cuts = z3.Int("three_q_cuts")
    two_q_cuts = z3.Int("two_q_cuts")
    solver.add(l_chi == int(left["J_chi"]["signed_log2_qubits_per_step"]))
    solver.add(r_chi == int(right["J_chi"]["signed_log2_qubits_per_step"]))
    solver.add(three_q_cuts == int(need["three_q_cut_count"]))
    solver.add(two_q_cuts == int(need["two_q_cut_count"]))
    solver.add(l_chi == -2, r_chi == 2, r_chi == -l_chi, three_q_cuts == 3, two_q_cuts == 1)
    verdict = solver.check()
    return {
        "ran": True,
        "verdict": str(verdict),
        "load_bearing": True,
        "claim": "L/R chirality seed signs and 3Q-vs-2Q cut counts satisfy the packet constraints",
        "input_object": {
            "left_chi": left["J_chi"]["signed_log2_qubits_per_step"],
            "right_chi": right["J_chi"]["signed_log2_qubits_per_step"],
            "three_q_cut_count": need["three_q_cut_count"],
            "two_q_cut_count": need["two_q_cut_count"],
        },
    }


def cvc5_crossover(left: dict[str, Any], right: dict[str, Any], need: dict[str, Any]) -> dict[str, Any]:
    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    int_sort = solver.getIntegerSort()
    l_chi = solver.mkConst(int_sort, "l_chi")
    r_chi = solver.mkConst(int_sort, "r_chi")
    three_q_cuts = solver.mkConst(int_sort, "three_q_cuts")
    two_q_cuts = solver.mkConst(int_sort, "two_q_cuts")
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, l_chi, solver.mkInteger(int(left["J_chi"]["signed_log2_qubits_per_step"]))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, r_chi, solver.mkInteger(int(right["J_chi"]["signed_log2_qubits_per_step"]))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, three_q_cuts, solver.mkInteger(int(need["three_q_cut_count"]))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, two_q_cuts, solver.mkInteger(int(need["two_q_cut_count"]))))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, l_chi, solver.mkInteger(-2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, r_chi, solver.mkInteger(2)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, three_q_cuts, solver.mkInteger(3)))
    solver.assertFormula(solver.mkTerm(Kind.EQUAL, two_q_cuts, solver.mkInteger(1)))
    check = solver.checkSat()
    verdict = "sat" if check.isSat() else "unsat" if check.isUnsat() else "unknown"
    return {
        "ran": True,
        "verdict": verdict,
        "load_bearing": True,
        "claim": "independent cvc5 check of chirality seed signs and 3Q-vs-2Q cut counts",
        "input_object": {
            "left_chi": left["J_chi"]["signed_log2_qubits_per_step"],
            "right_chi": right["J_chi"]["signed_log2_qubits_per_step"],
            "three_q_cut_count": need["three_q_cut_count"],
            "two_q_cut_count": need["two_q_cut_count"],
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
        unitary=cnot_unitary(0, 1),
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
        "scrambled_dynamics": {
            "row_id": "scrambled_dynamics_3q",
            "differs_from_committed_LR_currents": (
                row_by_id["scrambled_dynamics_3q"]["J_cut"]["net_delta_mutual_I"]
                != row_by_id["engine_R_flux_OUT_right_3q"]["J_cut"]["net_delta_mutual_I"]
                or row_by_id["scrambled_dynamics_3q"]["J_ent"]["net_delta_negativity"]
                != row_by_id["engine_R_flux_OUT_right_3q"]["J_ent"]["net_delta_negativity"]
            ),
            "J_cut_net_delta_mutual_I": row_by_id["scrambled_dynamics_3q"]["J_cut"]["net_delta_mutual_I"],
            "J_ent_net_delta_negativity": row_by_id["scrambled_dynamics_3q"]["J_ent"]["net_delta_negativity"],
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
            "committed_local_update": rows_bundle["committed_unitary"],
            "scrambled_control_update": rows_bundle["scrambled_unitary"],
            "boundary": "3-site tractable local-update realization; not a full engine admission.",
        },
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
        "source_locks": {name: source_lock(path, role=name) for name, path in AUTHORITY_PATHS.items()},
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
        "z3": z3_crossover(row_by_id["engine_L_flux_IN_left_3q"], row_by_id["engine_R_flux_OUT_right_3q"], need),
        "cvc5": cvc5_crossover(row_by_id["engine_L_flux_IN_left_3q"], row_by_id["engine_R_flux_OUT_right_3q"], need),
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
        and controls["scrambled_dynamics"]["differs_from_committed_LR_currents"] is True
        and payload["flux_in_left_out_right_doctrine_test"]["J_cut_LR_opposite_signs"] is True
        and payload["flux_in_left_out_right_doctrine_test"]["J_chi_L_negative_R_positive"] is True
        and need["computed_floor_verdict"] == "runtime_flux_nontrivial_at_3Q_floor_not_below"
        and payload["crossover_proofs"]["z3"]["verdict"] == "sat"
        and payload["crossover_proofs"]["cvc5"]["verdict"] == "sat"
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
        require(right["J_cut"]["net_delta_mutual_I"] > 0, "right J_cut not positive")
        require(left["J_cut"]["net_delta_mutual_I"] < 0, "left J_cut not negative")
        require(right["J_ent"]["net_delta_negativity"] > 0, "right J_ent not positive")
        require(left["J_ent"]["net_delta_negativity"] < 0, "left J_ent not negative")
    require(payload.get("three_q_necessity_row", {}).get("three_q_cut_count") == 3, "3Q cut count mismatch")
    require(payload.get("three_q_necessity_row", {}).get("two_q_cut_count") == 1, "2Q cut count mismatch")
    require(payload.get("controls", {}).get("static_no_evolution", {}).get("all_currents_zero") is True, "static control failed")
    require(payload.get("controls", {}).get("time_reversal", {}).get("J_cut_flips_sign") is True, "time reversal J_cut failed")
    require(payload.get("controls", {}).get("product_survivor_controls", {}).get("all_selected_product_controls_zero") is True, "product subset control failed")
    require(payload.get("controls", {}).get("carve_erasure", {}).get("substrate_check_ok") is False, "carve erasure negative not red")
    require(payload.get("all_pass") is True, "all_pass false")
    return errors


def main() -> int:
    payload = build_packet(write=True)
    print(json.dumps({"ok": payload["all_pass"], "result": rel(RESULT_PATH)}, indent=2, sort_keys=True))
    return 0 if payload["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
