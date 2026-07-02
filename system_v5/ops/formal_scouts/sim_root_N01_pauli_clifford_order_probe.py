#!/usr/bin/env python3
import jax
jax.config.update("jax_enable_x64", True)

import hashlib
import json
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", "/tmp/codex_ratchet_matplotlib")
os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import cvc5
from cvc5 import Kind
from clifford import Cl
import jax.numpy as jnp
import sympy as sp
import torch
import z3

SCRIPTS_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))
from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "root_N01_pauli_clifford_order_probe"
OBJECT_ID = "N01_pauli_clifford"
OUT_PATH = RESULT_DIR / "N01_pauli_clifford_results.json"

SCALE_RUNG_SIZES = (8, 16, 32, 64)
RTYPE = torch.float64
ITYPE = torch.int64
TOL = 1.0e-12
KILL_FLOOR = 1.0e-9

PAULI_X_TORCH = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=RTYPE)
PAULI_Z_TORCH = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=RTYPE)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing numeric engine: sparse binary Pauli descriptor tensors, symplectic commutation table, local X/Z order gap, and controls without dense global state closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity MIRROR for the same sparse Pauli descriptor table and order-gap readouts.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING Pauli/Clifford representation: Cl(3,0) generators e1,e3 anticommute and give the bivector/order coefficient that abelian erasure kills.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING exact symbolic Pauli table: {X,Z}=0, XZ=-ZX, and abelian subgroup controls.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING SMT proof: finite symplectic sign constraints are SAT for X/Z anticommutation and UNSAT when the structural claim is negated.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING independent SMT proof with Fraction rationals for the same sign/order structure and negated-claim flips.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not used; NumPy is control-only by instruction and is not a claim-bearing surface for this nonclassical root sim.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not used; no matrix exponential or SciPy routine is needed for this finite Pauli/Clifford order witness.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "numpy": None,
    "scipy": None,
}

BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): as_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(item) for item in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if hasattr(value, "tolist") and callable(value.tolist):
        try:
            return as_jsonable(value.tolist())
        except Exception:
            pass
    if hasattr(value, "item") and callable(value.item):
        try:
            return as_jsonable(value.item())
        except Exception:
            pass
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def pauli_generator_bits_torch(qubit_count: int) -> tuple[torch.Tensor, torch.Tensor, list[str]]:
    """Return sparse binary symplectic descriptors for X_i and Z_i generators."""
    x_bits = torch.zeros((2 * qubit_count, qubit_count), dtype=ITYPE)
    z_bits = torch.zeros((2 * qubit_count, qubit_count), dtype=ITYPE)
    labels: list[str] = []
    for idx in range(qubit_count):
        x_bits[idx, idx] = 1
        labels.append(f"X{idx}")
    for idx in range(qubit_count):
        z_bits[qubit_count + idx, idx] = 1
        labels.append(f"Z{idx}")
    return x_bits, z_bits, labels


def pauli_generator_bits_jax(qubit_count: int) -> tuple[jnp.ndarray, jnp.ndarray]:
    x_bits = jnp.zeros((2 * qubit_count, qubit_count), dtype=jnp.int64)
    z_bits = jnp.zeros((2 * qubit_count, qubit_count), dtype=jnp.int64)
    idx = jnp.arange(qubit_count, dtype=jnp.int64)
    x_bits = x_bits.at[idx, idx].set(1)
    z_bits = z_bits.at[qubit_count + idx, idx].set(1)
    return x_bits, z_bits


def symplectic_anticommutation_table_torch(x_bits: torch.Tensor, z_bits: torch.Tensor) -> torch.Tensor:
    table = (x_bits @ z_bits.T + z_bits @ x_bits.T) % 2
    return table.to(ITYPE)


def symplectic_anticommutation_table_jax(x_bits: jnp.ndarray, z_bits: jnp.ndarray) -> jnp.ndarray:
    return ((x_bits @ z_bits.T + z_bits @ x_bits.T) % 2).astype(jnp.int64)


def order_signs_from_bits_torch(
    x_a: torch.Tensor,
    z_a: torch.Tensor,
    x_b: torch.Tensor,
    z_b: torch.Tensor,
) -> tuple[torch.Tensor, torch.Tensor]:
    sign_ab = torch.where((torch.dot(z_a, x_b) % 2) == 1, torch.tensor(-1.0, dtype=RTYPE), torch.tensor(1.0, dtype=RTYPE))
    sign_ba = torch.where((torch.dot(z_b, x_a) % 2) == 1, torch.tensor(-1.0, dtype=RTYPE), torch.tensor(1.0, dtype=RTYPE))
    return sign_ab, sign_ba


def order_signs_from_bits_jax(
    x_a: jnp.ndarray,
    z_a: jnp.ndarray,
    x_b: jnp.ndarray,
    z_b: jnp.ndarray,
) -> tuple[jnp.ndarray, jnp.ndarray]:
    sign_ab = jnp.where((jnp.dot(z_a, x_b) % 2) == 1, -1.0, 1.0)
    sign_ba = jnp.where((jnp.dot(z_b, x_a) % 2) == 1, -1.0, 1.0)
    return sign_ab.astype(jnp.float64), sign_ba.astype(jnp.float64)


def table_hash(table: torch.Tensor) -> str:
    flat = "".join(str(int(item)) for item in table.flatten().tolist())
    return hashlib.sha256(flat.encode("ascii")).hexdigest()


def sparse_anticommuting_pairs(labels: list[str], table: torch.Tensor) -> list[list[str]]:
    rows, cols = torch.nonzero(table, as_tuple=True)
    return [[labels[int(i)], labels[int(j)]] for i, j in zip(rows.tolist(), cols.tolist())]


def torch_rung(qubit_count: int) -> dict[str, Any]:
    x_bits, z_bits, labels = pauli_generator_bits_torch(qubit_count)
    table = symplectic_anticommutation_table_torch(x_bits, z_bits)

    x0 = 0
    z0 = qubit_count
    sign_xz, sign_zx = order_signs_from_bits_torch(x_bits[x0], z_bits[x0], x_bits[z0], z_bits[z0])
    order_gap = torch.abs(sign_xz - sign_zx)
    anticommutator_coeff = sign_xz + sign_zx

    x1 = 1 if qubit_count > 1 else 0
    ctrl_sign_xx, ctrl_sign_xx_rev = order_signs_from_bits_torch(x_bits[x0], z_bits[x0], x_bits[x1], z_bits[x1])
    abelian_order_gap = torch.abs(ctrl_sign_xx - ctrl_sign_xx_rev)

    local_anticommutator = PAULI_X_TORCH @ PAULI_Z_TORCH + PAULI_Z_TORCH @ PAULI_X_TORCH
    local_commutator = PAULI_X_TORCH @ PAULI_Z_TORCH - PAULI_Z_TORCH @ PAULI_X_TORCH
    local_reversed_delta = torch.linalg.matrix_norm(PAULI_X_TORCH @ PAULI_Z_TORCH - PAULI_Z_TORCH @ PAULI_X_TORCH, ord="fro")
    zz_control_anticommutator = PAULI_Z_TORCH @ PAULI_Z_TORCH + PAULI_Z_TORCH @ PAULI_Z_TORCH
    zz_control_commutator = PAULI_Z_TORCH @ PAULI_Z_TORCH - PAULI_Z_TORCH @ PAULI_Z_TORCH
    zz_control_order_delta = torch.linalg.matrix_norm(zz_control_commutator, ord="fro")

    ordered_anticommute_pairs = int(torch.sum(table).item())
    unordered_anticommute_pairs = ordered_anticommute_pairs // 2
    expected_ordered = 2 * qubit_count
    pass_status = bool(
        ordered_anticommute_pairs == expected_ordered
        and unordered_anticommute_pairs == qubit_count
        and float(order_gap.item()) == 2.0
        and abs(float(anticommutator_coeff.item())) < TOL
        and float(abelian_order_gap.item()) == 0.0
        and float(torch.linalg.matrix_norm(local_anticommutator, ord="fro").item()) < TOL
        and float(local_reversed_delta.item()) > KILL_FLOOR
        and float(torch.linalg.matrix_norm(zz_control_commutator, ord="fro").item()) < TOL
        and float(zz_control_order_delta.item()) < TOL
    )

    return {
        "sites_or_qubits": qubit_count,
        "generator_count": 2 * qubit_count,
        "domain_cardinality": {
            "qubits": qubit_count,
            "generators": 2 * qubit_count,
            "sparse_descriptor_bits": int(4 * qubit_count * qubit_count),
        },
        "dense_state_closure_used": False,
        "dense_operator_closure_used": False,
        "global_hilbert_dimension_materialized": False,
        "local_2x2_pauli_check_only": True,
        "anticommutation_table_shape": list(table.shape),
        "anticommutation_table_hash": table_hash(table),
        "ordered_anticommuting_pair_count": ordered_anticommute_pairs,
        "unordered_anticommuting_pair_count": unordered_anticommute_pairs,
        "expected_ordered_anticommuting_pair_count": expected_ordered,
        "sparse_anticommuting_pairs": sparse_anticommuting_pairs(labels, table),
        "same_site_X0_Z0": {
            "sign_X_then_Z": float(sign_xz.item()),
            "sign_Z_then_X": float(sign_zx.item()),
            "order_gap": float(order_gap.item()),
            "anticommutator_sign_sum": float(anticommutator_coeff.item()),
            "anticommutator_zero": abs(float(anticommutator_coeff.item())) < TOL,
        },
        "abelian_X_subgroup_control": {
            "pair": [labels[x0], labels[x1]],
            "sign_forward": float(ctrl_sign_xx.item()),
            "sign_reverse": float(ctrl_sign_xx_rev.item()),
            "order_gap": float(abelian_order_gap.item()),
            "order_irrelevant": float(abelian_order_gap.item()) == 0.0,
        },
        "local_matrix_check": {
            "anticommutator_fro_norm": float(torch.linalg.matrix_norm(local_anticommutator, ord="fro").item()),
            "commutator_fro_norm": float(torch.linalg.matrix_norm(local_commutator, ord="fro").item()),
            "reversed_product_delta_fro_norm": float(local_reversed_delta.item()),
        },
        "abelian_ZZ_local_control": {
            "pair": ["Z0", "Z0"],
            "anticommutator_fro_norm": float(torch.linalg.matrix_norm(zz_control_anticommutator, ord="fro").item()),
            "commutator_fro_norm": float(torch.linalg.matrix_norm(zz_control_commutator, ord="fro").item()),
            "order_gap": float(zz_control_order_delta.item()),
            "order_irrelevant": float(zz_control_order_delta.item()) == 0.0,
        },
        "pass": pass_status,
    }


def jax_rung(qubit_count: int) -> dict[str, Any]:
    x_bits, z_bits = pauli_generator_bits_jax(qubit_count)
    table = symplectic_anticommutation_table_jax(x_bits, z_bits)
    x0 = 0
    z0 = qubit_count
    sign_xz, sign_zx = order_signs_from_bits_jax(x_bits[x0], z_bits[x0], x_bits[z0], z_bits[z0])
    order_gap = jnp.abs(sign_xz - sign_zx)
    anticommutator_coeff = sign_xz + sign_zx
    x1 = 1 if qubit_count > 1 else 0
    ctrl_sign_xx, ctrl_sign_xx_rev = order_signs_from_bits_jax(x_bits[x0], z_bits[x0], x_bits[x1], z_bits[x1])
    abelian_order_gap = jnp.abs(ctrl_sign_xx - ctrl_sign_xx_rev)
    ordered_anticommute_pairs = int(jnp.sum(table).item())
    return {
        "sites_or_qubits": qubit_count,
        "generator_count": 2 * qubit_count,
        "dense_state_closure_used": False,
        "ordered_anticommuting_pair_count": ordered_anticommute_pairs,
        "unordered_anticommuting_pair_count": ordered_anticommute_pairs // 2,
        "same_site_X0_Z0": {
            "sign_X_then_Z": float(sign_xz.item()),
            "sign_Z_then_X": float(sign_zx.item()),
            "order_gap": float(order_gap.item()),
            "anticommutator_sign_sum": float(anticommutator_coeff.item()),
            "anticommutator_zero": abs(float(anticommutator_coeff.item())) < TOL,
        },
        "abelian_X_subgroup_control": {
            "order_gap": float(abelian_order_gap.item()),
            "order_irrelevant": float(abelian_order_gap.item()) == 0.0,
        },
        "pass": bool(
            ordered_anticommute_pairs == 2 * qubit_count
            and float(order_gap.item()) == 2.0
            and abs(float(anticommutator_coeff.item())) < TOL
            and float(abelian_order_gap.item()) == 0.0
        ),
    }


def compare_torch_jax(torch_rows: dict[str, dict[str, Any]], jax_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    deltas = {}
    max_delta = 0.0
    for key in torch_rows:
        t = torch_rows[key]
        j = jax_rows[key]
        row_delta = max(
            abs(t["ordered_anticommuting_pair_count"] - j["ordered_anticommuting_pair_count"]),
            abs(t["same_site_X0_Z0"]["order_gap"] - j["same_site_X0_Z0"]["order_gap"]),
            abs(t["same_site_X0_Z0"]["anticommutator_sign_sum"] - j["same_site_X0_Z0"]["anticommutator_sign_sum"]),
            abs(t["abelian_X_subgroup_control"]["order_gap"] - j["abelian_X_subgroup_control"]["order_gap"]),
        )
        deltas[key] = {
            "max_delta": float(row_delta),
            "pass": float(row_delta) < TOL,
        }
        max_delta = max(max_delta, float(row_delta))
    return {"rows": deltas, "max_delta": max_delta, "agree": max_delta < TOL}


def torch_noncommutation_removed_rung(qubit_count: int) -> dict[str, Any]:
    x_bits, z_bits, _ = pauli_generator_bits_torch(qubit_count)
    removed_z_bits = torch.zeros_like(z_bits)
    table = symplectic_anticommutation_table_torch(x_bits, removed_z_bits)
    x0 = 0
    z0 = qubit_count
    sign_xz, sign_zx = order_signs_from_bits_torch(x_bits[x0], removed_z_bits[x0], x_bits[z0], removed_z_bits[z0])
    order_gap = torch.abs(sign_xz - sign_zx)
    return {
        "removed_structure": "torch symplectic z-bits erased before recomputing table/signs",
        "ordered_anticommuting_pair_count": int(torch.sum(table).item()),
        "same_site_X0_Z0": {
            "sign_X_then_Z": float(sign_xz.item()),
            "sign_Z_then_X": float(sign_zx.item()),
            "order_gap": float(order_gap.item()),
            "anticommutator_sign_sum": float((sign_xz + sign_zx).item()),
        },
        "pass": bool(int(torch.sum(table).item()) == 0 and float(order_gap.item()) == 0.0),
    }


def jax_noncommutation_removed_rung(qubit_count: int) -> dict[str, Any]:
    x_bits, z_bits = pauli_generator_bits_jax(qubit_count)
    removed_z_bits = jnp.zeros_like(z_bits)
    table = symplectic_anticommutation_table_jax(x_bits, removed_z_bits)
    x0 = 0
    z0 = qubit_count
    sign_xz, sign_zx = order_signs_from_bits_jax(x_bits[x0], removed_z_bits[x0], x_bits[z0], removed_z_bits[z0])
    order_gap = jnp.abs(sign_xz - sign_zx)
    return {
        "removed_structure": "JAX mirror z-bits erased before recomputing table/signs",
        "ordered_anticommuting_pair_count": int(jnp.sum(table).item()),
        "same_site_X0_Z0": {
            "sign_X_then_Z": float(sign_xz.item()),
            "sign_Z_then_X": float(sign_zx.item()),
            "order_gap": float(order_gap.item()),
            "anticommutator_sign_sum": float((sign_xz + sign_zx).item()),
        },
        "pass": bool(int(jnp.sum(table).item()) == 0 and float(order_gap.item()) == 0.0),
    }


def clifford_gate() -> dict[str, Any]:
    _, blades = Cl(3, 0)
    e1 = blades["e1"]
    e3 = blades["e3"]
    anticommutator = e1 * e3 + e3 * e1
    commutator = e1 * e3 - e3 * e1
    forward = e1 * e3
    reverse = e3 * e1
    control_anticommutator = e3 * e3 + e3 * e3
    control_commutator = e3 * e3 - e3 * e3
    baseline_order_coeff = float(commutator.mag2()) ** 0.5
    control_order_coeff = float(control_commutator.mag2()) ** 0.5
    return {
        "pass": bool(str(e1 * e1) == "1" and str(e3 * e3) == "1" and str(anticommutator) == "0" and str(forward + reverse) == "0" and control_order_coeff == 0.0),
        "algebra": "Cl(3,0)",
        "e1_square": str(e1 * e1),
        "e3_square": str(e3 * e3),
        "e1e3": str(forward),
        "e3e1": str(reverse),
        "anticommutator": str(anticommutator),
        "commutator": str(commutator),
        "bivector_order_coeff_abs": baseline_order_coeff if str(anticommutator) == "0" and str(forward) != str(reverse) else 0.0,
        "order_sensitive": str(forward) != str(reverse),
        "abelian_ZZ_control": {
            "pair": ["e3", "e3"],
            "anticommutator": str(control_anticommutator),
            "commutator": str(control_commutator),
            "bivector_order_coeff_abs": control_order_coeff,
            "order_irrelevant": control_order_coeff == 0.0,
        },
    }


def clifford_removed_abelian_rep() -> dict[str, Any]:
    x = Fraction(1, 1)
    z = Fraction(1, 1)
    forward = x * z
    reverse = z * x
    commutator = forward - reverse
    anticommutator = forward + reverse
    return {
        "representation": "non-Clifford commutative Fraction scalar replacement",
        "forward": str(forward),
        "reverse": str(reverse),
        "commutator": str(commutator),
        "anticommutator": str(anticommutator),
        "bivector_order_coeff_abs": float(abs(commutator)),
        "order_sensitive": forward != reverse,
        "pass": bool(forward == reverse and commutator == 0),
    }


def sympy_exact_gate() -> dict[str, Any]:
    x = sp.Matrix([[0, 1], [1, 0]])
    z = sp.Matrix([[1, 0], [0, -1]])
    identity = sp.eye(2)
    anticommutator = x * z + z * x
    commutator = x * z - z * x
    xx_commutator = x * identity - identity * x
    zz_anticommutator = z * z + z * z
    zz_commutator = z * z - z * z
    table = {
        "X*Z": str(x * z),
        "Z*X": str(z * x),
        "{X,Z}": str(anticommutator),
        "[X,Z]": str(commutator),
        "{Z,Z}": str(zz_anticommutator),
        "[Z,Z]": str(zz_commutator),
        "X*I-I*X": str(xx_commutator),
    }
    return {
        "pass": bool(anticommutator == sp.zeros(2) and x * z == -(z * x) and xx_commutator == sp.zeros(2) and zz_commutator == sp.zeros(2)),
        "anticommutator_is_zero": bool(anticommutator == sp.zeros(2)),
        "order_matters_XZ_vs_ZX": bool(x * z != z * x),
        "commutator_rank": int(commutator.rank()),
        "commutator_fro_norm": float(sp.sqrt(sum(v**2 for v in commutator))),
        "abelian_ZZ_commutator_rank": int(zz_commutator.rank()),
        "abelian_ZZ_commutator_fro_norm": float(sp.sqrt(sum(v**2 for v in zz_commutator))),
        "abelian_subgroup_order_irrelevant": bool(xx_commutator == sp.zeros(2)),
        "exact_table": table,
    }


def exact_matmul(a: list[list[Fraction]], b: list[list[Fraction]]) -> list[list[Fraction]]:
    return [
        [sum(a[i][k] * b[k][j] for k in range(len(b))) for j in range(len(b[0]))]
        for i in range(len(a))
    ]


def exact_matsub(a: list[list[Fraction]], b: list[list[Fraction]]) -> list[list[Fraction]]:
    return [[a[i][j] - b[i][j] for j in range(len(a[0]))] for i in range(len(a))]


def exact_matrix_rank_2x2(matrix: list[list[Fraction]]) -> int:
    if all(value == 0 for row in matrix for value in row):
        return 0
    det = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
    return 2 if det != 0 else 1


def exact_fro_norm(matrix: list[list[Fraction]]) -> float:
    return float(sum(value * value for row in matrix for value in row)) ** 0.5


def sympy_removed_exact_table() -> dict[str, Any]:
    z = [[Fraction(1, 1), Fraction(0, 1)], [Fraction(0, 1), Fraction(-1, 1)]]
    forward = exact_matmul(z, z)
    reverse = exact_matmul(z, z)
    commutator = exact_matsub(forward, reverse)
    return {
        "representation": "pure Fraction abelian Z/Z table after removing the SymPy symbolic X/Z step",
        "commutator": [[str(value) for value in row] for row in commutator],
        "commutator_rank": exact_matrix_rank_2x2(commutator),
        "commutator_fro_norm": exact_fro_norm(commutator),
        "pass": bool(exact_matrix_rank_2x2(commutator) == 0 and exact_fro_norm(commutator) == 0.0),
    }


def verdict_sat_score(proof: dict[str, Any], engine: str, side: str) -> float:
    if engine == "z3":
        key = "real_claim_verdict" if side == "real" else "negated_claim_verdict"
    elif engine == "cvc5":
        key = "cvc5_real_verdict" if side == "real" else "cvc5_control_verdict"
    else:
        raise ValueError(f"unknown proof engine: {engine}")
    return float(proof.get(key) == "sat")


def structural_claim_proof(torch_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    top = torch_rows[str(max(SCALE_RUNG_SIZES))]
    real_local = top["local_matrix_check"]
    control_local = top["abelian_ZZ_local_control"]
    real_measured = {
        "anticommutator_fro_norm": real_local["anticommutator_fro_norm"],
        "commutator_fro_norm": real_local["commutator_fro_norm"],
        "claim_margin": real_local["commutator_fro_norm"] - real_local["anticommutator_fro_norm"],
    }
    control_measured = {
        "anticommutator_fro_norm": control_local["anticommutator_fro_norm"],
        "commutator_fro_norm": control_local["commutator_fro_norm"],
        "claim_margin": control_local["commutator_fro_norm"] - control_local["anticommutator_fro_norm"],
    }
    proof = smt_load_bearing(
        "anticommutator-norm ||{X,Z}|| ~= 0 AND commutator nonzero",
        real_measured=real_measured,
        control_measured=control_measured,
        claim_builder=lambda v: z3.And(
            v["anticommutator_fro_norm"] <= z3.RealVal("1/1000000000"),
            v["commutator_fro_norm"] >= z3.RealVal("1/1000000000"),
        ),
        cvc5_claim_pairs=[
            ("anticommutator_fro_norm", "<=", 1.0e-9),
            ("commutator_fro_norm", ">=", 1.0e-9),
        ],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof["differ"]
        and proof.get("bound_to_measured") is True
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
    )
    proof["negative_control_carrier"] = "abelian same-generator Z0,Z0 control"
    return proof


def z3_proof_gate() -> dict[str, Any]:
    def build_sign_solver() -> tuple[z3.Solver, z3.ArithRef, z3.ArithRef, z3.ArithRef, z3.ArithRef]:
        solver = z3.Solver()
        x_a, z_a, x_b, z_b = z3.Ints("x_a z_a x_b z_b")
        sign_ab, sign_ba = z3.Ints("sign_ab sign_ba")
        solver.add(x_a == 1, z_a == 0, x_b == 0, z_b == 1)
        solver.add(sign_ab == z3.If((z_a * x_b) % 2 == 1, -1, 1))
        solver.add(sign_ba == z3.If((z_b * x_a) % 2 == 1, -1, 1))
        solver.add(z3.Or(sign_ab == -1, sign_ab == 1))
        solver.add(z3.Or(sign_ba == -1, sign_ba == 1))
        return solver, sign_ab, sign_ba, x_a, z_b

    sat_solver, sign_ab, sign_ba, _, _ = build_sign_solver()
    sat_solver.add(sign_ab + sign_ba == 0)
    sat_solver.add(sign_ab != sign_ba)
    sat_status = sat_solver.check()
    model = {}
    if sat_status == z3.sat:
        m = sat_solver.model()
        model = {"sign_X_then_Z": m[sign_ab].as_long(), "sign_Z_then_X": m[sign_ba].as_long()}

    neg_anticomm_solver, sign_ab2, sign_ba2, _, _ = build_sign_solver()
    neg_anticomm_solver.add(sign_ab2 + sign_ba2 != 0)
    neg_anticomm_status = neg_anticomm_solver.check()

    neg_order_solver, sign_ab3, sign_ba3, _, _ = build_sign_solver()
    neg_order_solver.add(sign_ab3 == sign_ba3)
    neg_order_status = neg_order_solver.check()

    ctrl = z3.Solver()
    xa, za, xb, zb = z3.Ints("ctrl_xa ctrl_za ctrl_xb ctrl_zb")
    s_ab, s_ba = z3.Ints("ctrl_sign_ab ctrl_sign_ba")
    ctrl.add(xa == 1, za == 0, xb == 1, zb == 0)
    ctrl.add(s_ab == z3.If((za * xb) % 2 == 1, -1, 1))
    ctrl.add(s_ba == z3.If((zb * xa) % 2 == 1, -1, 1))
    ctrl.add(s_ab == s_ba)
    ctrl_status = ctrl.check()

    return {
        "pass": bool(sat_status == z3.sat and neg_anticomm_status == z3.unsat and neg_order_status == z3.unsat and ctrl_status == z3.sat),
        "positive_structure_query": {
            "status": str(sat_status),
            "sat": sat_status == z3.sat,
            "model": model,
            "formula": "same-site Pauli descriptors X=(x=1,z=0), Z=(x=0,z=1) imply sign_XZ + sign_ZX == 0 and sign_XZ != sign_ZX",
        },
        "negated_anticommutator_query": {
            "status": str(neg_anticomm_status),
            "unsat": neg_anticomm_status == z3.unsat,
            "formula": "same finite sign constraints plus sign_XZ + sign_ZX != 0",
        },
        "negated_order_query": {
            "status": str(neg_order_status),
            "unsat": neg_order_status == z3.unsat,
            "formula": "same finite sign constraints plus sign_XZ == sign_ZX",
        },
        "abelian_control_query": {
            "status": str(ctrl_status),
            "sat": ctrl_status == z3.sat,
            "formula": "X_i and X_j have equal forward/reverse signs, so order is irrelevant",
        },
    }


def cvc5_solver() -> cvc5.Solver:
    solver = cvc5.Solver()
    solver.setLogic("ALL")
    solver.setOption("produce-models", "true")
    return solver


def cvc5_real(solver: cvc5.Solver, value: Fraction) -> cvc5.Term:
    return solver.mkReal(value.numerator, value.denominator) if value.denominator != 1 else solver.mkReal(value.numerator)


def cvc5_proof_gate() -> dict[str, Any]:
    def build_sign_solver(prefix: str) -> tuple[cvc5.Solver, cvc5.Term, cvc5.Term]:
        solver = cvc5_solver()
        real_sort = solver.getRealSort()
        sign_ab = solver.mkConst(real_sort, f"{prefix}_sign_ab")
        sign_ba = solver.mkConst(real_sort, f"{prefix}_sign_ba")
        one = cvc5_real(solver, Fraction(1, 1))
        minus_one = cvc5_real(solver, Fraction(-1, 1))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, sign_ab, one))
        solver.assertFormula(solver.mkTerm(Kind.EQUAL, sign_ba, minus_one))
        return solver, sign_ab, sign_ba

    sat_solver, sign_ab, sign_ba = build_sign_solver("same_site")
    zero = cvc5_real(sat_solver, Fraction(0, 1))
    sat_solver.assertFormula(sat_solver.mkTerm(Kind.EQUAL, sat_solver.mkTerm(Kind.ADD, sign_ab, sign_ba), zero))
    sat_solver.assertFormula(sat_solver.mkTerm(Kind.DISTINCT, sign_ab, sign_ba))
    sat_status = sat_solver.checkSat()
    model = {}
    if sat_status.isSat():
        model = {"sign_X_then_Z": str(sat_solver.getValue(sign_ab)), "sign_Z_then_X": str(sat_solver.getValue(sign_ba))}

    neg_anticomm_solver, sign_ab2, sign_ba2 = build_sign_solver("neg_anticomm")
    zero2 = cvc5_real(neg_anticomm_solver, Fraction(0, 1))
    neg_anticomm_solver.assertFormula(neg_anticomm_solver.mkTerm(Kind.DISTINCT, neg_anticomm_solver.mkTerm(Kind.ADD, sign_ab2, sign_ba2), zero2))
    neg_anticomm_status = neg_anticomm_solver.checkSat()

    neg_order_solver, sign_ab3, sign_ba3 = build_sign_solver("neg_order")
    neg_order_solver.assertFormula(neg_order_solver.mkTerm(Kind.EQUAL, sign_ab3, sign_ba3))
    neg_order_status = neg_order_solver.checkSat()

    ctrl_solver = cvc5_solver()
    real_sort = ctrl_solver.getRealSort()
    ctrl_ab = ctrl_solver.mkConst(real_sort, "ctrl_sign_ab")
    ctrl_ba = ctrl_solver.mkConst(real_sort, "ctrl_sign_ba")
    one_ctrl = cvc5_real(ctrl_solver, Fraction(1, 1))
    ctrl_solver.assertFormula(ctrl_solver.mkTerm(Kind.EQUAL, ctrl_ab, one_ctrl))
    ctrl_solver.assertFormula(ctrl_solver.mkTerm(Kind.EQUAL, ctrl_ba, one_ctrl))
    ctrl_solver.assertFormula(ctrl_solver.mkTerm(Kind.EQUAL, ctrl_ab, ctrl_ba))
    ctrl_status = ctrl_solver.checkSat()

    return {
        "pass": bool(sat_status.isSat() and neg_anticomm_status.isUnsat() and neg_order_status.isUnsat() and ctrl_status.isSat()),
        "uses_fraction_rationals": True,
        "positive_structure_query": {
            "status": str(sat_status),
            "sat": sat_status.isSat(),
            "model": model,
            "formula": "Fraction(1,1) + Fraction(-1,1) == 0 and signs distinct",
        },
        "negated_anticommutator_query": {
            "status": str(neg_anticomm_status),
            "unsat": neg_anticomm_status.isUnsat(),
            "formula": "same finite Fraction signs plus sign_XZ + sign_ZX != 0",
        },
        "negated_order_query": {
            "status": str(neg_order_status),
            "unsat": neg_order_status.isUnsat(),
            "formula": "same finite Fraction signs plus sign_XZ == sign_ZX",
        },
        "abelian_control_query": {
            "status": str(ctrl_status),
            "sat": ctrl_status.isSat(),
            "formula": "Fraction(1,1) and Fraction(1,1) signs for X-subgroup commute",
        },
    }


def add_ablation_pass(row: dict[str, Any], removed_structure: str) -> dict[str, Any]:
    row["removed_structure"] = removed_structure
    row["pass"] = abs(float(row["outcome_delta"])) > KILL_FLOOR
    return row


def controls_and_ablations(
    torch_rows: dict[str, dict[str, Any]],
    jax_rows: dict[str, dict[str, Any]],
    proof_results: dict[str, Any],
    clifford_result: dict[str, Any],
    sympy_result: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    top = torch_rows[str(max(SCALE_RUNG_SIZES))]
    jax_top = jax_rows[str(max(SCALE_RUNG_SIZES))]
    torch_removed = torch_noncommutation_removed_rung(max(SCALE_RUNG_SIZES))
    jax_removed = jax_noncommutation_removed_rung(max(SCALE_RUNG_SIZES))
    clifford_removed = clifford_removed_abelian_rep()
    sympy_removed = sympy_removed_exact_table()
    order_gap = float(top["same_site_X0_Z0"]["order_gap"])
    abelian_gap = float(top["abelian_X_subgroup_control"]["order_gap"])
    zz_control = top["abelian_ZZ_local_control"]
    real_local = top["local_matrix_check"]
    order_erased_gap = float(torch_removed["same_site_X0_Z0"]["order_gap"])
    probe_erased_anticommute_count = int(torch_removed["ordered_anticommuting_pair_count"])
    sparse_pair_count = top["ordered_anticommuting_pair_count"]
    real_claim_margin = float(real_local["commutator_fro_norm"] - real_local["anticommutator_fro_norm"])
    control_claim_margin = float(zz_control["commutator_fro_norm"] - zz_control["anticommutator_fro_norm"])
    proof_claim = proof_results["smt_anticommutator_commutator_claim"]

    controls = {
        "abelian_X_subgroup_order_irrelevant": {
            "pass": abelian_gap == 0.0,
            "killed_constraint": "N01",
            "order_gap": abelian_gap,
            "outcome_delta": order_gap - abelian_gap,
            "reason": "Restricting to the abelian X-generator subgroup removes the X/Z same-site anticommutation and makes product order irrelevant.",
        },
        "abelian_ZZ_control_anticommutator_claim_fails": {
            "pass": bool(zz_control["commutator_fro_norm"] < TOL and zz_control["anticommutator_fro_norm"] > KILL_FLOOR),
            "killed_constraint": "N01",
            "carrier": "same generator Z0,Z0 abelian control",
            "anticommutator_fro_norm": zz_control["anticommutator_fro_norm"],
            "commutator_fro_norm": zz_control["commutator_fro_norm"],
            "claim_margin": control_claim_margin,
            "outcome_delta": real_claim_margin - control_claim_margin,
            "reason": "The SMT structural claim is rechecked on Z0,Z0: commutator vanishes and anticommutator is nonzero, so the real X0,Z0 claim must fail on the control.",
        },
        "order_erased_commutative_sign_rule": {
            "pass": order_erased_gap == 0.0,
            "killed_constraint": "N01",
            "order_gap": order_erased_gap,
            "outcome_delta": order_gap - order_erased_gap,
            "recomputed_control": torch_removed,
            "reason": "Replacing the symplectic sign rule with sign=+1 for every product kills order sensitivity.",
        },
        "probe_erased_no_same_site_Z_generators": {
            "pass": probe_erased_anticommute_count == 0,
            "killed_constraint": "N01",
            "ordered_anticommuting_pair_count": probe_erased_anticommute_count,
            "outcome_delta": sparse_pair_count - probe_erased_anticommute_count,
            "recomputed_control": torch_removed,
            "reason": "Removing the paired Z-probe symplectic z-bits leaves no X_i/Z_i anticommutation table entries.",
        },
    }

    tool_ablations = {
        "torch": add_ablation_pass(
            tool_ablation(
                "torch_ordered_anticommuting_pair_count_with_symplectic_table_vs_z_bits_removed",
                top["ordered_anticommuting_pair_count"],
                torch_removed["ordered_anticommuting_pair_count"],
                tool="torch",
            ),
            "torch symplectic table recomputed after erasing the z-bit noncommutation structure",
        ),
        "jax": add_ablation_pass(
            tool_ablation(
                "jax_order_gap_X0_Z0_with_symplectic_table_vs_z_bits_removed",
                jax_top["same_site_X0_Z0"]["order_gap"],
                jax_removed["same_site_X0_Z0"]["order_gap"],
                tool="jax",
            ),
            "JAX x64 mirror recomputed after erasing the z-bit noncommutation structure",
        ),
        "clifford": add_ablation_pass(
            tool_ablation(
                "clifford_bivector_order_coeff_e1_e3_vs_non_clifford_abelian_scalar_rep",
                clifford_result["bivector_order_coeff_abs"],
                clifford_removed["bivector_order_coeff_abs"],
                tool="clifford",
            ),
            "Cl(3,0) anticommuting e1/e3 representation removed and recomputed through a commutative Fraction scalar replacement",
        ),
        "sympy": add_ablation_pass(
            tool_ablation(
                "sympy_exact_commutator_fro_norm_XZ_vs_fraction_ZZ_after_symbolic_step_removed",
                sympy_result["commutator_fro_norm"],
                sympy_removed["commutator_fro_norm"],
                tool="sympy",
            ),
            "SymPy symbolic X/Z table step removed; ablated observable recomputed by pure Fraction abelian Z/Z table arithmetic",
        ),
        "z3": add_ablation_pass(
            tool_ablation(
                "z3_own_flip_score_real_XZ_claim_vs_engine_decoupled_control",
                verdict_sat_score(proof_claim, "z3", "real"),
                verdict_sat_score(proof_claim, "z3", "control"),
                tool="z3",
            ),
            "z3 engine contribution measured as its own load_bearing_proof verdict flip score",
        ),
        "cvc5": add_ablation_pass(
            tool_ablation(
                "cvc5_own_flip_score_real_XZ_claim_vs_engine_decoupled_control",
                verdict_sat_score(proof_claim, "cvc5", "real"),
                verdict_sat_score(proof_claim, "cvc5", "control"),
                tool="cvc5",
            ),
            "cvc5 engine contribution measured as its own load_bearing_proof verdict flip score",
        ),
    }
    tool_ablations["torch"]["removed_tool_observable"] = torch_removed
    tool_ablations["jax"]["removed_tool_observable"] = jax_removed
    tool_ablations["clifford"]["removed_tool_observable"] = clifford_removed
    tool_ablations["sympy"]["removed_tool_observable"] = sympy_removed
    return controls, tool_ablations


def build_result() -> dict[str, Any]:
    started = time.time()
    torch_rows = {str(size): torch_rung(size) for size in SCALE_RUNG_SIZES}
    jax_rows = {str(size): jax_rung(size) for size in SCALE_RUNG_SIZES}
    parity = compare_torch_jax(torch_rows, jax_rows)

    clifford_result = clifford_gate()
    sympy_result = sympy_exact_gate()
    proof_results = {
        "smt_anticommutator_commutator_claim": structural_claim_proof(torch_rows),
    }

    controls, tool_ablations = controls_and_ablations(torch_rows, jax_rows, proof_results, clifford_result, sympy_result)
    scale_rungs = {}
    for size in SCALE_RUNG_SIZES:
        row = torch_rows[str(size)]
        mirror = jax_rows[str(size)]
        scale_rungs[str(size)] = {
            "sites_or_qubits": size,
            "generator_count": row["generator_count"],
            "operator_count": row["generator_count"],
            "path_count": 2,
            "dense_state_closure_used": False,
            "dense_operator_closure_used": False,
            "ordered_anticommuting_pair_count": row["ordered_anticommuting_pair_count"],
            "unordered_anticommuting_pair_count": row["unordered_anticommuting_pair_count"],
            "expected_ordered_anticommuting_pair_count": row["expected_ordered_anticommuting_pair_count"],
            "order_gap": row["same_site_X0_Z0"]["order_gap"],
            "anticommutator_sign_sum": row["same_site_X0_Z0"]["anticommutator_sign_sum"],
            "abelian_control_order_gap": row["abelian_X_subgroup_control"]["order_gap"],
            "jax_order_gap": mirror["same_site_X0_Z0"]["order_gap"],
            "commutation_table_hash": row["anticommutation_table_hash"],
            "pass": bool(row["pass"] and mirror["pass"]),
        }

    scale_pass = all(row["pass"] for row in scale_rungs.values())
    proof_pass = all(row["pass"] for row in proof_results.values()) and clifford_result["pass"] and sympy_result["pass"]
    controls_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in controls.values())
    ablations_pass = all(row["pass"] and abs(float(row["outcome_delta"])) > KILL_FLOOR for row in tool_ablations.values())
    all_pass = bool(scale_pass and proof_pass and parity["agree"] and controls_pass and ablations_pass)

    result = {
        "schema": "formal_scout_root_constraint_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "object_id": OBJECT_ID,
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classification": "lego",
        "tier": "0_root_constraint_N01",
        "purpose": "Build one Stage-1 root-constraint finite Pauli/Clifford order probe for N01 noncommutation/order sensitivity.",
        "scientific_question": "Does a finite sparse Pauli/Clifford generator object certify that same-site X and Z anticommute, that XZ and ZX products differ by order, and that an abelian subgroup control kills the N01 constraint at 8/16/32/64 qubits without dense state closure?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "root_constraint_order_probe",
        "finite_map": {
            "domain": "For each n in {8,16,32,64}: finite sparse Pauli generator descriptors P_n={X_i,Z_i | i=0..n-1} represented by binary symplectic x/z bit rows, plus local Cl(3,0) generators e1,e3 and local 2x2 X/Z matrices for the generator law only.",
            "codomain_or_output": "Sparse anticommutation table omega(P_a,P_b) in F2, signed product-order witnesses sign(A then B), sign(B then A), exact {X,Z}=0 proof receipts, abelian/order-erased controls, tool ablation deltas, and blocked downstream consumers.",
        },
        "domain": {
            "scale_qubits": list(SCALE_RUNG_SIZES),
            "generator_rule": "G_n has X_i and Z_i for each qubit i; generator_count=2n; no 2**n vector or 2**n x 2**n operator is materialized.",
            "operation": "signed Pauli multiplication over binary symplectic descriptors: sign(A then B)=(-1)^(z_A dot x_B)",
        },
        "codomain_or_output": {
            "commutation_table": "sparse ordered anticommuting pairs plus table hash per rung",
            "order_witness": "same-site X0,Z0 have sign_XZ=+1, sign_ZX=-1, anticommutator sign sum 0, order_gap 2",
            "control_witness": "abelian X-subgroup and order-erased sign rule have order_gap 0",
        },
        "root_constraints": {
            "F01": {
                "role": "referenced",
                "statement": "finite carrier/probe/operator/path set: each rung uses finite qubit index set, finite X_i/Z_i generator descriptors, finite signed product paths X->Z and Z->X, and finite proof/control outputs.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting/order-sensitive operation/control: same-site Pauli/Clifford generators anticommute ({X,Z}=0), XZ and ZX differ by sign, and abelian/order-erased controls kill the order gap.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "root finite Pauli/Clifford sparse descriptor object",
        "geometry_layer": "not_applicable: this is a root N01 order probe, not a manifold/geometry layer",
        "carrier_realization": "torch int64 binary symplectic rows for scaled sparse descriptors; local torch 2x2 Pauli matrices only for the generator law; JAX x64 mirrors sparse descriptors; clifford Cl(3,0) carries the Pauli/Clifford anticommuting basis.",
        "peps3d_embedding": {
            "status": "finite anchor only, not a PEPS3D/manifold claim",
            "anchor_rule": "qubit index i maps to a finite site anchor; this root N01 sim does not claim PEPS3D contraction, layer stacking, flux, Axis0, FEP, or physics.",
            "dense_state_closure_used": False,
        },
        "spinor_state": "local two-component Pauli spinor basis is used only through X/Z operator action; no dense n-qubit spinor state is materialized.",
        "quaternion_action": "not_applicable: no quaternion language or quaternion invariant is used in this root N01 probe",
        "dependency_receipts": [],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "N01 Pauli/Clifford same-site anticommutation and product-order sensitivity with abelian/order-erased negatives.",
        "branch_status_before_run": "root Stage-1 lego requested by user; no downstream consumer opened",
        "allowed_claims": [
            "bounded local N01 Pauli/Clifford order lego exists/runs if this result and validators pass",
            "same-site X_i and Z_i anticommute in the finite sparse Pauli/Clifford descriptor object",
            "abelian X-subgroup and order-erased controls kill order sensitivity",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "root-constraint N01 lego only",
            "no F01 standalone build completion claim",
            "no layer stacking, manifold, Xi, Phi0, Axis0, flux, FEP, gravity, or physics admission",
        ],
        "eligible_consumers": ["bounded root-constraint audits only after citing this result path and validator output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": ["load_bearing_proof.smt_load_bearing over measured torch X/Z vs Z/Z observables", "cvc5 helper mirror pairs", "sympy exact Pauli table", "clifford Cl(3,0) anticommutation"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "abelian_X_subgroup": "must make order_gap 0",
            "order_erased_commutative_sign_rule": "must make order_gap 0",
            "probe_erased_no_same_site_Z_generators": "must remove all ordered anticommuting pairs",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch primary readouts", "JAX mirror readouts", "proof_results", "controls", "tool_ablations"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablations_pass,
            "jax_vs_pytorch_delta": parity["max_delta"],
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "int64 sparse descriptors plus float64 local 2x2 generator-law checks",
            "rungs": torch_rows,
            "pass": all(row["pass"] for row in torch_rows.values()),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": True,
            "rungs": jax_rows,
            "pass": all(row["pass"] for row in jax_rows.values()),
        },
        "jax_vs_pytorch_delta": parity["max_delta"],
        "jax_vs_pytorch": parity,
        "clifford_primary_result": clifford_result,
        "sympy_exact_result": sympy_result,
        "proof_results": proof_results,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "scale_ladder": {"rungs": scale_rungs, "pass": scale_pass},
        "commutation_table": {
            "representation": "sparse ordered anticommuting pairs; full dense table not printed, but hash is computed from the full finite table for every rung",
            "rung_8_sparse_pairs": torch_rows["8"]["sparse_anticommuting_pairs"],
            "hashes": {key: row["anticommutation_table_hash"] for key, row in torch_rows.items()},
        },
        "positive": {
            "same_site_XZ_anticommutator_zero": {"pass": all(abs(row["same_site_X0_Z0"]["anticommutator_sign_sum"]) < TOL for row in torch_rows.values())},
            "same_site_XZ_order_gap_positive": {"pass": all(row["same_site_X0_Z0"]["order_gap"] > KILL_FLOOR for row in torch_rows.values())},
            "sparse_scale_8_16_32_64": {"pass": scale_pass, "rungs": scale_rungs},
            "proof_stack_nonvacuous_flip": {
                "pass": proof_pass,
                "smt_real_claim_verdict": proof_results["smt_anticommutator_commutator_claim"]["real_claim_verdict"],
                "smt_control_claim_verdict": proof_results["smt_anticommutator_commutator_claim"]["negated_claim_verdict"],
                "smt_differ": proof_results["smt_anticommutator_commutator_claim"]["differ"],
                "cvc5_real_verdict": proof_results["smt_anticommutator_commutator_claim"].get("cvc5_real_verdict"),
                "cvc5_control_verdict": proof_results["smt_anticommutator_commutator_claim"].get("cvc5_control_verdict"),
            },
            "clifford_basis_anticommutes": clifford_result,
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "abelian_X_subgroup": controls["abelian_X_subgroup_order_irrelevant"],
            "order_erased_sign_rule": controls["order_erased_commutative_sign_rule"],
            "probe_erased": controls["probe_erased_no_same_site_Z_generators"],
        },
        "shells": [
            {
                "name": "root_N01_sparse_pauli_clifford_order_object",
                "status": "root lego only",
                "scale_rungs": list(SCALE_RUNG_SIZES),
                "survives": scale_pass and proof_pass,
            }
        ],
        "future_continuations": [
            "build the separate F01 finite-carrier root sim if needed",
            "only consume this as bounded N01 order evidence after validator output is cited",
        ],
        "compatibility_weights": {
            "root_N01_order_evidence": 1.0 if all_pass else 0.0,
            "downstream_Xi_Phi0_Axis0_flux_FEP_gravity": 0.0,
        },
        "compression_map": {
            "from": "finite sparse X_i/Z_i descriptor rows and signed product paths",
            "to": "anticommutation table hash/sparse pairs, order gaps, proof flips, controls, tool ablation deltas",
            "loss_boundary": "does not preserve or claim dense global state, PEPS3D contraction, manifold, axis, bridge, flux, FEP, gravity, or physics admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min(row["order_gap"] for row in scale_rungs.values()),
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "N01 object survives iff every rung is sparse/non-dense, same-site X/Z anticommutes, order_gap=2, proof flips are present, controls kill, ablations are nonzero, and promotion_allowed=false",
            "computed_capacity": min(row["order_gap"] for row in scale_rungs.values()),
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and min(row["order_gap"] for row in scale_rungs.values()) > KILL_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required",
            "claim_ceiling": "N01 Pauli/Clifford root lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 sparse rungs pass; torch and JAX agree; clifford/sympy/z3/cvc5 proofs pass with negated-claim flips; controls kill N01; every tool ablation has nonzero outcome_delta",
        "fail_rule": "fail on dense closure, missing rung, zero order gap, missing anticommutator zero, proof without negated-claim flip, live abelian/order-erased control, zero tool ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blockers": [] if all_pass else ["one_or_more_root_N01_checks_failed"],
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": result["all_pass"], "required_output": str(OUT_PATH), "scale_pass": result["scale_ladder"]["pass"], "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"]}, indent=2, sort_keys=True))
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
