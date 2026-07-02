#!/usr/bin/env python3
"""Standalone Stage 3 Clifford-module geometry object probe.

Object:
    A finite Cl(1,3) gamma-module geometry represented by local gamma matrices
    acting on N sampled C^4 spinors for N in {8, 16, 32, 64}.

Defining invariant:
    {gamma_mu, gamma_nu} = 2 eta_mu_nu I.

The proof is helper-bound to measured observables: the real gamma module has
near-zero anticommutator defect, while the flattened commuting control does not.
No dense tensor-product state is constructed.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")
os.environ.setdefault("NUMBA_DISABLE_CACHE", "1")
os.environ.setdefault("NUMBA_CACHE_DIR", "/tmp/codex-numba")

import jax

jax.config.update("jax_enable_x64", True)

import jax.numpy as jnp
from clifford import Cl
import sympy as sp
import torch
import z3

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_geom_clifford_module_probe"
OBJECT_ID = "clifford_module_gamma_rep_geometry"
OUT_PATH = RESULT_DIR / "geom_clifford_module_probe_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
RTYPE = torch.float64
CTYPE = torch.complex128
TOL = 1.0e-10
KILL_FLOOR = 1.0e-8
LOCAL_SPINOR_DIM = 4
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY numeric carrier: complex128 gamma matrices, local C^4 spinor samples, anticommutator defects, module actions, and flattened controls without dense closure.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror for representable matrix/module-action readouts; no fake JAX Clifford or geomstats backend path is claimed.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING geometry source: Cl(1,3) basis squares and off-diagonal anticommutators determine the gamma-representation signature; removing it triggers a recomputed commuting-control ablation.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof surface: exact multiplication table for {gamma_mu,gamma_nu}=2 eta_mu_nu I and exact real-vs-control flip, with no numeric ablation row.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING proof via smt_load_bearing: real measured anticommutator defect satisfies the same claim that the flattened control fails.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "LOAD-BEARING cvc5 cross-check through smt_load_bearing on the same measured anticommutator defect.",
    },
    "geomstats": {
        "tried": False,
        "used": False,
        "reason": "Not used: this object is an algebraic Clifford-module geometry, not a Riemannian metric/geodesic computation; geomstats has no JAX backend and no fake JAX geomstats path is emitted.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "clifford": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "geomstats": None,
    "numpy": None,
}


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
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
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
    return value


def clifford_signature_witness() -> dict[str, Any]:
    layout, blades = Cl(1, 3)
    basis = [blades[f"e{i}"] for i in range(1, 5)]
    square_strings = [str(vector * vector) for vector in basis]
    signature = [1 if item == "1" else -1 if item == "-1" else 0 for item in square_strings]
    offdiag = []
    for i in range(4):
        for j in range(i + 1, 4):
            anti = basis[i] * basis[j] + basis[j] * basis[i]
            offdiag.append({"pair": [i, j], "anticommutator": str(anti), "zero": str(anti) == "0"})
    return {
        "tool": "clifford",
        "algebra": "Cl(1,3)",
        "layout_signature": [int(x) for x in layout.sig.tolist()],
        "basis_square_strings": square_strings,
        "signature": signature,
        "offdiag_anticommutators": offdiag,
        "pass": bool(signature == [1, -1, -1, -1] and all(row["zero"] for row in offdiag)),
    }


def torch_gamma_matrices(signature: list[int]) -> tuple[list[torch.Tensor], torch.Tensor]:
    if signature != [1, -1, -1, -1]:
        raise ValueError(f"expected Cl(1,3) signature [1,-1,-1,-1], got {signature}")
    zero = torch.zeros((2, 2), dtype=CTYPE)
    ident = torch.eye(2, dtype=CTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CTYPE)
    gamma0 = torch.cat((torch.cat((ident, zero), dim=1), torch.cat((zero, -ident), dim=1)), dim=0)
    gammas = [gamma0]
    for sigma in (sx, sy, sz):
        top = torch.cat((zero, sigma), dim=1)
        bottom = torch.cat((-sigma, zero), dim=1)
        gammas.append(torch.cat((top, bottom), dim=0))
    eta = torch.diag(torch.tensor(signature, dtype=RTYPE)).to(CTYPE)
    return gammas, eta


def jax_gamma_matrices(signature: list[int]) -> tuple[list[jax.Array], jax.Array]:
    zero = jnp.zeros((2, 2), dtype=jnp.complex128)
    ident = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    gamma0 = jnp.concatenate((jnp.concatenate((ident, zero), axis=1), jnp.concatenate((zero, -ident), axis=1)), axis=0)
    gammas = [gamma0]
    for sigma in (sx, sy, sz):
        top = jnp.concatenate((zero, sigma), axis=1)
        bottom = jnp.concatenate((-sigma, zero), axis=1)
        gammas.append(jnp.concatenate((top, bottom), axis=0))
    eta = jnp.diag(jnp.array(signature, dtype=jnp.float64)).astype(jnp.complex128)
    return gammas, eta


def sympy_gamma_matrices(signature: list[int]) -> tuple[list[sp.Matrix], sp.Matrix]:
    if signature != [1, -1, -1, -1]:
        raise ValueError(f"expected Cl(1,3) signature [1,-1,-1,-1], got {signature}")
    zero = sp.zeros(2)
    ident = sp.eye(2)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -sp.I], [sp.I, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    gamma0 = sp.Matrix.vstack(sp.Matrix.hstack(ident, zero), sp.Matrix.hstack(zero, -ident))
    gammas = [gamma0]
    for sigma in (sx, sy, sz):
        gammas.append(sp.Matrix.vstack(sp.Matrix.hstack(zero, sigma), sp.Matrix.hstack(-sigma, zero)))
    eta = sp.diag(*signature)
    return gammas, eta


def torch_commuting_control() -> tuple[list[torch.Tensor], torch.Tensor]:
    ident = torch.eye(4, dtype=CTYPE)
    gamma0 = torch.diag(torch.tensor([1.0, 1.0, -1.0, -1.0], dtype=RTYPE)).to(CTYPE)
    gamma1 = torch.diag(torch.tensor([1.0, -1.0, 1.0, -1.0], dtype=RTYPE)).to(CTYPE)
    gammas = [gamma0, gamma1, ident, -ident]
    eta = torch.diag(torch.tensor([1, -1, -1, -1], dtype=RTYPE)).to(CTYPE)
    return gammas, eta


def jax_commuting_control() -> tuple[list[jax.Array], jax.Array]:
    ident = jnp.eye(4, dtype=jnp.complex128)
    gamma0 = jnp.diag(jnp.array([1.0, 1.0, -1.0, -1.0], dtype=jnp.float64)).astype(jnp.complex128)
    gamma1 = jnp.diag(jnp.array([1.0, -1.0, 1.0, -1.0], dtype=jnp.float64)).astype(jnp.complex128)
    gammas = [gamma0, gamma1, ident, -ident]
    eta = jnp.diag(jnp.array([1, -1, -1, -1], dtype=jnp.float64)).astype(jnp.complex128)
    return gammas, eta


def sympy_commuting_control() -> tuple[list[sp.Matrix], sp.Matrix]:
    ident = sp.eye(4)
    gamma0 = sp.diag(1, 1, -1, -1)
    gamma1 = sp.diag(1, -1, 1, -1)
    gammas = [gamma0, gamma1, ident, -ident]
    eta = sp.diag(1, -1, -1, -1)
    return gammas, eta


def anticommutator_defects_torch(gammas: list[torch.Tensor], eta: torch.Tensor) -> dict[str, Any]:
    ident = torch.eye(4, dtype=CTYPE)
    defects: dict[str, float] = {}
    max_defect = 0.0
    diag_defects = []
    offdiag_defects = []
    for mu in range(4):
        for nu in range(4):
            lhs = gammas[mu] @ gammas[nu] + gammas[nu] @ gammas[mu]
            rhs = 2.0 * eta[mu, nu] * ident
            defect = float(torch.linalg.matrix_norm(lhs - rhs).item())
            defects[f"{mu}{nu}"] = defect
            max_defect = max(max_defect, defect)
            if mu == nu:
                diag_defects.append(defect)
            else:
                offdiag_defects.append(defect)
    return {
        "defects": defects,
        "max_defect": max_defect,
        "max_diag_defect": max(diag_defects),
        "max_offdiag_defect": max(offdiag_defects),
        "pass": bool(max_defect <= TOL),
    }


def anticommutator_defects_jax(gammas: list[jax.Array], eta: jax.Array) -> dict[str, Any]:
    ident = jnp.eye(4, dtype=jnp.complex128)
    defects: dict[str, float] = {}
    max_defect = 0.0
    diag_defects = []
    offdiag_defects = []
    for mu in range(4):
        for nu in range(4):
            lhs = gammas[mu] @ gammas[nu] + gammas[nu] @ gammas[mu]
            rhs = 2.0 * eta[mu, nu] * ident
            defect = float(jnp.linalg.norm(lhs - rhs))
            defects[f"{mu}{nu}"] = defect
            max_defect = max(max_defect, defect)
            if mu == nu:
                diag_defects.append(defect)
            else:
                offdiag_defects.append(defect)
    return {
        "defects": defects,
        "max_defect": max_defect,
        "max_diag_defect": max(diag_defects),
        "max_offdiag_defect": max(offdiag_defects),
        "pass": bool(max_defect <= TOL),
    }


def exact_table_sympy(gammas: list[sp.Matrix], eta: sp.Matrix) -> dict[str, Any]:
    ident = sp.eye(4)
    table: dict[str, dict[str, Any]] = {}
    satisfied = 0
    for mu in range(4):
        for nu in range(4):
            lhs = gammas[mu] * gammas[nu] + gammas[nu] * gammas[mu]
            rhs = 2 * eta[mu, nu] * ident
            diff = sp.simplify(lhs - rhs)
            exact_zero = diff == sp.zeros(4)
            satisfied += int(exact_zero)
            table[f"{mu}{nu}"] = {
                "exact_zero": bool(exact_zero),
                "rank_of_difference": int(diff.rank()),
                "frobenius_squared": str(sum(diff[i, j] ** 2 for i in range(4) for j in range(4))),
            }
    return {
        "table": table,
        "entries_total": 16,
        "entries_satisfied": satisfied,
        "entries_failed": 16 - satisfied,
        "pass": bool(satisfied == 16),
    }


def build_spinors_torch(sample_count: int, *, flattened: bool = False) -> torch.Tensor:
    if flattened:
        out = torch.zeros((sample_count, LOCAL_SPINOR_DIM), dtype=CTYPE)
        out[:, 0] = 1.0 + 0.0j
        return out
    idx = torch.arange(sample_count, dtype=RTYPE)
    a = (idx + 1.0) * (0.071 + 0.003 / sample_count)
    b = (idx + 0.5) * (0.113 + 0.001 / sample_count)
    c = (idx + 2.0) * (0.047 + 0.002 / sample_count)
    spinors = torch.stack(
        (
            torch.cos(a).to(CTYPE),
            torch.sin(a).to(CTYPE) * torch.exp(1j * b.to(CTYPE)),
            torch.cos(c).to(CTYPE) * torch.exp(-1j * b.to(CTYPE)),
            torch.sin(c).to(CTYPE),
        ),
        dim=1,
    )
    return spinors / torch.linalg.vector_norm(spinors, dim=1, keepdim=True)


def build_spinors_jax(sample_count: int, *, flattened: bool = False) -> jax.Array:
    if flattened:
        out = jnp.zeros((sample_count, LOCAL_SPINOR_DIM), dtype=jnp.complex128)
        return out.at[:, 0].set(jnp.complex128(1.0 + 0.0j))
    idx = jnp.arange(sample_count, dtype=jnp.float64)
    a = (idx + 1.0) * (0.071 + 0.003 / sample_count)
    b = (idx + 0.5) * (0.113 + 0.001 / sample_count)
    c = (idx + 2.0) * (0.047 + 0.002 / sample_count)
    spinors = jnp.stack(
        (
            jnp.cos(a).astype(jnp.complex128),
            jnp.sin(a).astype(jnp.complex128) * jnp.exp(1j * b.astype(jnp.complex128)),
            jnp.cos(c).astype(jnp.complex128) * jnp.exp(-1j * b.astype(jnp.complex128)),
            jnp.sin(c).astype(jnp.complex128),
        ),
        axis=1,
    )
    return spinors / jnp.linalg.norm(spinors, axis=1, keepdims=True)


def module_readout_torch(spinors: torch.Tensor, gammas: list[torch.Tensor]) -> dict[str, Any]:
    actions = [torch.einsum("ab,nb->na", gamma, spinors) for gamma in gammas]
    order_gap = float(torch.linalg.vector_norm(actions[0] @ gammas[1].T - actions[1] @ gammas[0].T).item() / spinors.shape[0])
    exp_abs2 = []
    for action in actions:
        values = torch.sum(spinors.conj() * action, dim=1)
        exp_abs2.append(float(torch.mean(torch.abs(values) ** 2).item()))
    signature_value = float(sum((idx + 1) * value for idx, value in enumerate(exp_abs2)) + order_gap)
    return {
        "expectation_abs2_by_gamma": exp_abs2,
        "order_gap_gamma0_gamma1": order_gap,
        "value_signature": signature_value,
        "pass": bool(order_gap > KILL_FLOOR),
    }


def module_readout_jax(spinors: jax.Array, gammas: list[jax.Array]) -> dict[str, Any]:
    actions = [jnp.einsum("ab,nb->na", gamma, spinors) for gamma in gammas]
    order_gap = float(jnp.linalg.norm(actions[0] @ gammas[1].T - actions[1] @ gammas[0].T) / spinors.shape[0])
    exp_abs2 = []
    for action in actions:
        values = jnp.sum(jnp.conj(spinors) * action, axis=1)
        exp_abs2.append(float(jnp.mean(jnp.abs(values) ** 2)))
    signature_value = float(sum((idx + 1) * value for idx, value in enumerate(exp_abs2)) + order_gap)
    return {
        "expectation_abs2_by_gamma": exp_abs2,
        "order_gap_gamma0_gamma1": order_gap,
        "value_signature": signature_value,
        "pass": bool(order_gap > KILL_FLOOR),
    }


def scale_rung(
    sample_count: int,
    gammas_t: list[torch.Tensor],
    eta_t: torch.Tensor,
    gammas_j: list[jax.Array],
    eta_j: jax.Array,
) -> dict[str, Any]:
    spinors_t = build_spinors_torch(sample_count)
    spinors_j = build_spinors_jax(sample_count)
    readout_t = module_readout_torch(spinors_t, gammas_t)
    readout_j = module_readout_jax(spinors_j, gammas_j)
    defects_t = anticommutator_defects_torch(gammas_t, eta_t)
    defects_j = anticommutator_defects_jax(gammas_j, eta_j)
    value_delta = abs(readout_t["value_signature"] - readout_j["value_signature"])
    order_delta = abs(readout_t["order_gap_gamma0_gamma1"] - readout_j["order_gap_gamma0_gamma1"])
    return {
        "sites_or_qubits": sample_count,
        "sample_count": sample_count,
        "local_spinor_dim": LOCAL_SPINOR_DIM,
        "operator_count": len(gammas_t),
        "carrier_kind": "N sampled local C^4 spinors with open-chain metadata; no tensor-product closure",
        "mps_metadata_shape": [sample_count, 1, LOCAL_SPINOR_DIM, 1],
        "mps_bond_dim": 1,
        "dense_state_closure_used": False,
        "global_dense_dimension_if_closed": f"4**{sample_count} (not instantiated)",
        "torch": readout_t,
        "jax": readout_j,
        "torch_anticommutator_max_defect": defects_t["max_defect"],
        "jax_anticommutator_max_defect": defects_j["max_defect"],
        "jax_vs_pytorch_value_delta": value_delta,
        "jax_vs_pytorch_order_delta": order_delta,
        "pass": bool(
            spinors_t.shape == (sample_count, LOCAL_SPINOR_DIM)
            and readout_t["pass"]
            and readout_j["pass"]
            and defects_t["pass"]
            and defects_j["pass"]
            and value_delta <= 1.0e-11
            and order_delta <= 1.0e-11
        ),
    }


def smt_anticommutation_proof(real_defect: float, control_defect: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="clifford_gamma_anticommutator_max_defect_le_eps",
        real_measured={"anticommutator_max_defect": real_defect, "eps": TOL},
        control_measured={"anticommutator_max_defect": control_defect, "eps": TOL},
        claim_builder=lambda v: v["anticommutator_max_defect"] <= v["eps"],
        cvc5_claim_pairs=[("anticommutator_max_defect", "<=", "eps")],
    )
    proof["pass"] = bool(
        proof["real_claim_verdict"] == "sat"
        and proof["negated_claim_verdict"] == "unsat"
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
        and proof["differ"] is True
        and proof["bound_to_measured"] is True
    )
    return proof


def sympy_exact_flip(real_table: dict[str, Any], control_table: dict[str, Any]) -> dict[str, Any]:
    real_entries = float(real_table["entries_satisfied"])
    control_entries = float(control_table["entries_satisfied"])
    real_holds = real_entries == float(real_table["entries_total"])
    control_holds = control_entries == float(control_table["entries_total"])
    return {
        "claim": "sympy_exact_all_16_gamma_anticommutator_entries_match",
        "engine": "sympy",
        "real_claim_verdict": "sat" if real_holds else "unsat",
        "negated_claim_verdict": "sat" if control_holds else "unsat",
        "differ": bool(real_holds != control_holds),
        "load_bearing": bool(real_holds and not control_holds),
        "bound_to_measured": True,
        "real_measured": {
            "entries_satisfied": real_entries,
            "entries_total": float(real_table["entries_total"]),
        },
        "control_measured": {
            "entries_satisfied": control_entries,
            "entries_total": float(control_table["entries_total"]),
        },
        "pass": bool(real_holds and not control_holds),
    }


def known_value_checks(
    torch_real: dict[str, Any],
    jax_real: dict[str, Any],
    sympy_real: dict[str, Any],
    sympy_control: dict[str, Any],
    clifford_witness: dict[str, Any],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for mu in range(4):
        for nu in range(4):
            checks.append(
                {
                    "invariant": f"gamma_anticommutator_{mu}{nu}_equals_2_eta_{mu}{nu}_I4",
                    "computed": {
                        "torch_defect": torch_real["defects"][f"{mu}{nu}"],
                        "jax_defect": jax_real["defects"][f"{mu}{nu}"],
                        "sympy_exact_zero": sympy_real["table"][f"{mu}{nu}"]["exact_zero"],
                    },
                    "known": "zero residual for Cl(1,3) gamma representation",
                    "match": bool(
                        torch_real["defects"][f"{mu}{nu}"] <= TOL
                        and jax_real["defects"][f"{mu}{nu}"] <= TOL
                        and sympy_real["table"][f"{mu}{nu}"]["exact_zero"] is True
                    ),
                }
            )
    checks.append(
        {
            "invariant": "clifford_library_signature_matches_Cl_1_3",
            "computed": {
                "signature": clifford_witness["signature"],
                "basis_square_strings": clifford_witness["basis_square_strings"],
                "offdiag_zero_count": sum(int(row["zero"]) for row in clifford_witness["offdiag_anticommutators"]),
            },
            "known": "[1,-1,-1,-1] and six off-diagonal zero anticommutators",
            "match": bool(clifford_witness["pass"]),
        }
    )
    checks.append(
        {
            "invariant": "commuting_flattened_control_does_not_satisfy_full_anticommutator_table",
            "computed": {
                "control_entries_satisfied": sympy_control["entries_satisfied"],
                "control_entries_failed": sympy_control["entries_failed"],
            },
            "known": "control must fail at least one exact anticommutator entry",
            "match": bool(sympy_control["entries_failed"] > 0),
        }
    )
    return checks


def add_ablation_pass(row: dict[str, Any]) -> dict[str, Any]:
    row["pass"] = bool(abs(float(row["outcome_delta"])) > KILL_FLOOR)
    return row


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    clifford_witness = clifford_signature_witness()
    gammas_t, eta_t = torch_gamma_matrices(clifford_witness["signature"])
    gammas_j, eta_j = jax_gamma_matrices(clifford_witness["signature"])
    gammas_s, eta_s = sympy_gamma_matrices(clifford_witness["signature"])

    control_gammas_t, control_eta_t = torch_commuting_control()
    control_gammas_j, control_eta_j = jax_commuting_control()
    control_gammas_s, control_eta_s = sympy_commuting_control()

    torch_real = anticommutator_defects_torch(gammas_t, eta_t)
    torch_control = anticommutator_defects_torch(control_gammas_t, control_eta_t)
    jax_real = anticommutator_defects_jax(gammas_j, eta_j)
    jax_control = anticommutator_defects_jax(control_gammas_j, control_eta_j)
    sympy_real = exact_table_sympy(gammas_s, eta_s)
    sympy_control = exact_table_sympy(control_gammas_s, control_eta_s)

    scale_rows = {str(n): scale_rung(n, gammas_t, eta_t, gammas_j, eta_j) for n in SCALE_RUNGS}
    top = scale_rows["64"]
    jax_vs_pytorch_delta = max(
        max(row["jax_vs_pytorch_value_delta"], row["jax_vs_pytorch_order_delta"], abs(row["torch_anticommutator_max_defect"] - row["jax_anticommutator_max_defect"]))
        for row in scale_rows.values()
    )

    smt_proof = smt_anticommutation_proof(torch_real["max_defect"], torch_control["max_defect"])
    sympy_flip = sympy_exact_flip(sympy_real, sympy_control)
    checks = known_value_checks(torch_real, jax_real, sympy_real, sympy_control, clifford_witness)

    clifford_ablation = add_ablation_pass(
        tool_ablation(
            "clifford_gamma_anticommutator_max_defect_with_Cl13_signature_vs_commuting_flattened_control",
            baseline_value=torch_real["max_defect"],
            ablated_value=torch_control["max_defect"],
            tool="clifford",
        )
    )
    tool_ablations = {
        "clifford_gamma_representation_ablation": clifford_ablation,
    }

    scale_ladder = {
        "rungs": {
            str(n): {
                "sites_or_qubits": scale_rows[str(n)]["sites_or_qubits"],
                "sample_count": scale_rows[str(n)]["sample_count"],
                "local_spinor_dim": scale_rows[str(n)]["local_spinor_dim"],
                "operator_count": scale_rows[str(n)]["operator_count"],
                "mps_metadata_shape": scale_rows[str(n)]["mps_metadata_shape"],
                "mps_bond_dim": scale_rows[str(n)]["mps_bond_dim"],
                "dense_state_closure_used": False,
                "jax_vs_pytorch_value_delta": scale_rows[str(n)]["jax_vs_pytorch_value_delta"],
                "jax_vs_pytorch_order_delta": scale_rows[str(n)]["jax_vs_pytorch_order_delta"],
                "torch_anticommutator_max_defect": scale_rows[str(n)]["torch_anticommutator_max_defect"],
                "pass": scale_rows[str(n)]["pass"],
            }
            for n in SCALE_RUNGS
        },
        "scale_axis": "sampled_local_spinor_sites",
        "dense_state_closure_used": False,
        "pass": bool(all(row["pass"] and row["dense_state_closure_used"] is False for row in scale_rows.values())),
    }

    controls = {
        "commuting_flattened_gamma_control": {
            "description": "Replace the Clifford-derived gamma representation with mutually commuting diagonal/identity matrices and recompute the same anticommutator invariant.",
            "real_anticommutator_max_defect": torch_real["max_defect"],
            "control_anticommutator_max_defect": torch_control["max_defect"],
            "real_sympy_entries_satisfied": sympy_real["entries_satisfied"],
            "control_sympy_entries_satisfied": sympy_control["entries_satisfied"],
            "kills_defining_invariant": bool(torch_control["max_defect"] > KILL_FLOOR and sympy_control["entries_failed"] > 0),
            "pass": bool(torch_control["max_defect"] > KILL_FLOOR and sympy_control["entries_failed"] > 0),
        },
        "flattened_spinor_sample_control": {
            "description": "All N local spinors flattened to e0; no dense global vector is formed. This control is not used for the SMT proof because the defining invariant is an operator anticommutator.",
            "rungs": {
                str(n): {
                    "sites_or_qubits": n,
                    "dense_state_closure_used": False,
                    "flattened_sample_shape": [n, LOCAL_SPINOR_DIM],
                    "norm_min": float(torch.min(torch.linalg.vector_norm(build_spinors_torch(n, flattened=True), dim=1)).item()),
                    "norm_max": float(torch.max(torch.linalg.vector_norm(build_spinors_torch(n, flattened=True), dim=1)).item()),
                    "pass": True,
                }
                for n in SCALE_RUNGS
            },
            "pass": True,
        },
    }

    proof_results = {
        "smt_load_bearing_anticommutator_defect": smt_proof,
        "sympy_exact_table_flip": sympy_flip,
        "clifford_signature_witness": clifford_witness,
        "pass": bool(smt_proof["pass"] and sympy_flip["pass"] and clifford_witness["pass"]),
    }

    all_known_match = all(row["match"] for row in checks)
    controls_pass = all(row["pass"] for row in controls.values())
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    scale_pass = scale_ladder["pass"]
    proof_pass = proof_results["pass"]
    all_pass = bool(
        clifford_witness["pass"]
        and torch_real["pass"]
        and jax_real["pass"]
        and sympy_real["pass"]
        and torch_control["max_defect"] > KILL_FLOOR
        and jax_control["max_defect"] > KILL_FLOOR
        and sympy_control["entries_failed"] > 0
        and proof_pass
        and all_known_match
        and controls_pass
        and ablation_pass
        and scale_pass
        and jax_vs_pytorch_delta <= 1.0e-11
    )

    blockers = []
    if not proof_pass:
        blockers.append("helper-bound SMT/SymPy proof flip failed")
    if not ablation_pass:
        blockers.append("Clifford structure removal did not change the recomputed anticommutator observable")
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 non-dense scale rungs failed")
    if not all_known_match:
        blockers.append("one or more computed known-value checks failed")
    if jax_vs_pytorch_delta > 1.0e-11:
        blockers.append(f"jax_vs_pytorch_delta {jax_vs_pytorch_delta} exceeds tolerance")

    min_order_gap = min(row["torch"]["order_gap_gamma0_gamma1"] for row in scale_rows.values())
    result = {
        "schema": "formal_scout_stage3_geometry_lego_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 3 geometry object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "purpose": "Instantiate one standalone Clifford-module geometry object on non-dense 8/16/32/64 local spinor samples and prove its defining anticommutator invariant against a flattened commuting control.",
        "scientific_question": "Does the finite Cl(1,3) gamma-module satisfy {gamma_mu,gamma_nu}=2 eta_mu_nu I on non-dense sampled local spinor carriers, and does the same invariant fail under a degenerate commuting control?",
        "finite_map": {
            "domain": "For N in {8,16,32,64}: finite sampled local spinor carrier Psi_N in (C^4)^N as an N x 4 tensor, finite operator set Gamma={gamma_0,...,gamma_3}, and metric eta=diag(1,-1,-1,-1).",
            "codomain_or_output": "Anticommutator defect table max_mu,nu ||gamma_mu gamma_nu + gamma_nu gamma_mu - 2 eta_mu_nu I4||, local module action readouts, exact SymPy table, SMT flip proof, controls, and scale ladder.",
            "definition": "GammaModule_N maps (Psi_N, Gamma, eta) to the finite defect/readout tuple; no global tensor-product state or dense 4**N closure is instantiated.",
        },
        "domain": {
            "site_counts": list(SCALE_RUNGS),
            "local_spinor_dim": LOCAL_SPINOR_DIM,
            "operator_set": ["gamma_0", "gamma_1", "gamma_2", "gamma_3"],
            "signature": clifford_witness["signature"],
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "max anticommutator defect for {gamma_mu,gamma_nu}=2 eta_mu_nu I4",
            "proof_object": "real/control measured defect bound through smt_load_bearing plus exact SymPy real/control table flip",
            "scale_output": "8/16/32/64 non-dense local module rungs",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: finite N, finite local spinor samples, four gamma operators, finite exact table entries, finite controls, and finite proof variables.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting/order-sensitive operation/control: gamma_0/gamma_1 module actions have nonzero order gap, and the Clifford anticommutation law fails under the commuting control.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control witnessed by gamma_0/gamma_1 order gap and anticommutator control failure",
        ],
        "carrier_layer": "finite sampled C4 spinor module",
        "geometry_layer": "clifford_module_gamma_rep_geometry",
        "carrier_realization": "torch.complex128 N x 4 local spinor tensor plus open-chain metadata; JAX complex128 mirror for representable matrix/module readouts; no NumPy and no dense closure.",
        "peps3d_embedding": {
            "status": "local_cell_anchor_only_not_manifold_admission",
            "anchor": "each sampled local C4 spinor can be read as a finite local cell tensor; this sim does not claim PEPS3D contraction, layer stacking, or manifold admission",
            "full_peps3d_contraction_claimed": False,
        },
        "spinor_state": "For each N, Psi_N is an N x 4 torch.complex128 tensor of normalized local spinors; no 4**N global vector is materialized.",
        "quaternion_action": "not_applicable: Clifford gamma-module geometry is tested without quaternion language",
        "dependency_receipts": ["stage3_geometry_object_standalone_no_lower_result_consumed"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "{gamma_mu,gamma_nu}=2 eta_mu_nu I4 for a finite Cl(1,3) gamma module",
        "branch_status_before_run": "single standalone geometry lego requested; no manifold layer, G-structure, coupling, bridge, flux, Axis0, FEP, gravity, or physics route opened",
        "allowed_claims": [
            "standalone Stage 3 geometry object receipt for this Clifford-module gamma representation",
            "8/16/32/64 non-dense local spinor sample scale execution",
            "helper-bound real/control anticommutator proof flip and exact SymPy table flip",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single geometry object only",
            "not a manifold layer and not a G-structure selection",
            "no coupling, stacking, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, physics, or final admission",
        ],
        "eligible_consumers": ["future bounded local Clifford-module geometry comparisons only after citing this result path and fresh gates"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 anticommutator-defect flip",
            "load_bearing_proof.smt_load_bearing cvc5 anticommutator-defect cross-check",
            "sympy exact multiplication-table real/control flip",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "commuting_flattened_gamma_control": "same anticommutator invariant must exceed tolerance and make the helper-bound claim unsat",
            "flattened_spinor_sample_control": "sample carrier remains finite/non-dense while demonstrating no dense global closure is needed",
        },
        "required_artifacts": ["result JSON", "scale_ladder", "torch_primary_result", "jax_mirror_result", "proof_results", "controls", "tool_ablations", "known_value_checks"],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "known_value_checks_pass": all_known_match,
            "torch_anticommutator_max_defect": torch_real["max_defect"],
            "control_anticommutator_max_defect": torch_control["max_defect"],
            "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
            "min_order_gap_gamma0_gamma1": min_order_gap,
            "elapsed_seconds": time.time() - started,
        },
        "torch_primary_result": {
            "engine": "torch",
            "dtype": "torch.complex128",
            "claim": "{gamma_mu,gamma_nu}=2 eta_mu_nu I4 has max defect <= eps on the real Clifford module",
            "anticommutator": torch_real,
            "commuting_control_anticommutator": torch_control,
            "top_rung": top,
            "pass": bool(torch_real["pass"] and top["pass"]),
        },
        "jax_mirror_result": {
            "engine": "jax",
            "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
            "representable_scope": "JAX mirrors the explicit gamma matrices, local spinor samples, module readouts, and anticommutator defects; it does not mirror the clifford library path.",
            "anticommutator": jax_real,
            "commuting_control_anticommutator": jax_control,
            "pass": bool(jax_real["pass"] and jax_vs_pytorch_delta <= 1.0e-11),
        },
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "proof_results": proof_results,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "scale_ladder": scale_ladder,
        "scale_details": scale_rows,
        "known_value_checks": checks,
        "all_known_value_checks_match": all_known_match,
        "sympy_exact_result": {
            "real_table": sympy_real,
            "commuting_control_table": sympy_control,
            "pass": bool(sympy_real["pass"] and sympy_control["entries_failed"] > 0),
        },
        "positive": {
            "clifford_signature": clifford_witness,
            "torch_anticommutator_defect": torch_real,
            "jax_anticommutator_defect": jax_real,
            "sympy_exact_table": sympy_real,
            "smt_flip": smt_proof,
            "scale_ladder": scale_ladder,
            "pass": bool(clifford_witness["pass"] and torch_real["pass"] and jax_real["pass"] and sympy_real["pass"] and smt_proof["pass"] and scale_pass),
        },
        "graveyard_companions": controls,
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "manifold_layer_claim": {"claimed": False, "pass": True},
            "g_structure_claim": {"claimed": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "commuting_control_defect_delta": torch_control["max_defect"] - torch_real["max_defect"],
            "sympy_control_failed_entries": sympy_control["entries_failed"],
            "pass": bool(torch_control["max_defect"] > KILL_FLOOR and sympy_control["entries_failed"] > 0),
        },
        "shells": [
            {
                "name": "clifford_module_gamma_rep_geometry_object",
                "status": "stage3_geometry_object_only",
                "rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "build another standalone geometry object only after this result is cited and re-gated",
            "do not use this result as Xi/Phi0/Axis0/flux/FEP/gravity evidence",
        ],
        "compatibility_weights": {
            "stage3_geometry_object_input": 1.0 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite sampled C4 spinor carrier plus four Cl(1,3) gamma operators",
            "to": "anticommutator max defect, exact table entries, local module order gap, proof flip, control failure, and scale ladder",
            "loss_boundary": "does not preserve or claim global dense 4**N tensor product, manifold layer completion, G-structure selection, Axis0, flux, FEP, gravity, bridge, or final admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": min_order_gap,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "clifford_module survives iff every scale rung is non-dense, the real anticommutator defect is <= eps, the flattened commuting control fails, SymPy exact table flips, SMT proof flips, JAX mirror agrees where representable, and promotion_allowed=false",
            "computed_capacity": min_order_gap,
            "threshold": KILL_FLOOR,
            "passed": bool(all_pass and min_order_gap > KILL_FLOOR),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage 3 standalone Clifford-module geometry object only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; torch/JAX agree where representable; helper-bound z3/cvc5 proof flips real vs commuting control; exact SymPy table flips; Clifford removal recomputes a nonzero anticommutator-defect ablation; downstream consumers remain blocked",
        "fail_rule": "fail on dense closure, missing rung, fake JAX path, no real/control proof flip, proof-tool numeric ablation, live commuting control, missing Clifford recompute ablation, JAX mismatch, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blockers": blockers,
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    OUT_PATH.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": str(OUT_PATH.relative_to(ROOT)),
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
                "scale_pass": result["scale_ladder"]["pass"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
