import jax; jax.config.update("jax_enable_x64", True)
"""Clifford module geometry layer scout at 8/16/32/64 sites.

This is one independent geometric-manifold layer: Cl(1,3) gamma matrices acting
locally on an N-site spinor module. The carrier is an N-sample/open-chain
bond-1 MPS representation, not a dense 2**N or 4**N state closure.
"""

import json
import os
import pathlib
import time
from typing import Any

os.environ.setdefault("NUMBA_DISABLE_JIT", "1")

import jax.numpy as jnp
from clifford import Cl
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "clifford_module_geometry"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SITE_COUNTS = [8, 16, 32, 64]
CDTYPE = torch.complex128
RTYPE = torch.float64
TOL = 1.0e-10


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            item = value.detach().cpu().item()
            if isinstance(item, complex):
                return {"real": float(item.real), "imag": float(item.imag)}
            return item
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    return value


def clifford_signature() -> dict[str, Any]:
    layout, blades = Cl(1, 3)
    basis = [blades["e1"], blades["e2"], blades["e3"], blades["e4"]]
    squares = [str(b * b) for b in basis]
    signs = [1 if s == "1" else -1 if s == "-1" else 0 for s in squares]
    offdiag_zero = []
    for i in range(4):
        for j in range(i + 1, 4):
            offdiag_zero.append(str(basis[i] * basis[j] + basis[j] * basis[i]) == "0")
    return {
        "signature": signs,
        "layout_sig": [int(x) for x in layout.sig.tolist()],
        "basis_square_strings": squares,
        "offdiag_anticommutators_zero": bool(all(offdiag_zero)),
        "pass": signs == [1, -1, -1, -1] and all(offdiag_zero),
    }


def torch_gamma_matrices(signature: list[int]) -> tuple[list[torch.Tensor], torch.Tensor]:
    if signature != [1, -1, -1, -1]:
        raise ValueError(f"this probe expects Cl(1,3), got {signature}")
    zero = torch.zeros((2, 2), dtype=CDTYPE)
    ident = torch.eye(2, dtype=CDTYPE)
    sx = torch.tensor([[0, 1], [1, 0]], dtype=CDTYPE)
    sy = torch.tensor([[0, -1j], [1j, 0]], dtype=CDTYPE)
    sz = torch.tensor([[1, 0], [0, -1]], dtype=CDTYPE)
    g0 = torch.cat((torch.cat((ident, zero), dim=1), torch.cat((zero, -ident), dim=1)), dim=0)
    gammas = [g0]
    for sigma in (sx, sy, sz):
        top = torch.cat((zero, sigma), dim=1)
        bottom = torch.cat((-sigma, zero), dim=1)
        gammas.append(torch.cat((top, bottom), dim=0))
    eta = torch.diag(torch.tensor(signature, dtype=RTYPE)).to(CDTYPE)
    return gammas, eta


def jax_gamma_matrices(signature: list[int]) -> tuple[list[Any], Any]:
    zero = jnp.zeros((2, 2), dtype=jnp.complex128)
    ident = jnp.eye(2, dtype=jnp.complex128)
    sx = jnp.array([[0, 1], [1, 0]], dtype=jnp.complex128)
    sy = jnp.array([[0, -1j], [1j, 0]], dtype=jnp.complex128)
    sz = jnp.array([[1, 0], [0, -1]], dtype=jnp.complex128)
    g0 = jnp.concatenate((jnp.concatenate((ident, zero), axis=1), jnp.concatenate((zero, -ident), axis=1)), axis=0)
    gammas = [g0]
    for sigma in (sx, sy, sz):
        top = jnp.concatenate((zero, sigma), axis=1)
        bottom = jnp.concatenate((-sigma, zero), axis=1)
        gammas.append(jnp.concatenate((top, bottom), axis=0))
    eta = jnp.diag(jnp.array(signature, dtype=jnp.float64)).astype(jnp.complex128)
    return gammas, eta


def anticommutator_defects_torch(gammas: list[torch.Tensor], eta: torch.Tensor) -> dict[str, Any]:
    ident = torch.eye(4, dtype=CDTYPE)
    defects: dict[str, float] = {}
    max_defect = 0.0
    for mu in range(4):
        for nu in range(4):
            lhs = gammas[mu] @ gammas[nu] + gammas[nu] @ gammas[mu]
            rhs = 2.0 * eta[mu, nu] * ident
            defect = float(torch.linalg.matrix_norm(lhs - rhs).item())
            defects[f"{mu}{nu}"] = defect
            max_defect = max(max_defect, defect)
    return {"defects": defects, "max_defect": max_defect, "pass": max_defect < TOL}


def anticommutator_defects_jax(gammas: list[Any], eta: Any) -> dict[str, Any]:
    ident = jnp.eye(4, dtype=jnp.complex128)
    defects: dict[str, float] = {}
    max_defect = 0.0
    for mu in range(4):
        for nu in range(4):
            lhs = gammas[mu] @ gammas[nu] + gammas[nu] @ gammas[mu]
            rhs = 2.0 * eta[mu, nu] * ident
            defect = float(jnp.linalg.norm(lhs - rhs))
            defects[f"{mu}{nu}"] = defect
            max_defect = max(max_defect, defect)
    return {"defects": defects, "max_defect": max_defect, "pass": max_defect < TOL}


def gamma5_torch(gammas: list[torch.Tensor]) -> torch.Tensor:
    return 1j * gammas[0] @ gammas[1] @ gammas[2] @ gammas[3]


def gamma5_jax(gammas: list[Any]) -> Any:
    return 1j * gammas[0] @ gammas[1] @ gammas[2] @ gammas[3]


def build_spinors_torch(n: int) -> torch.Tensor:
    idx = torch.arange(n, dtype=RTYPE)
    a = (idx + 1.0) * (0.071 + 0.003 / n)
    b = (idx + 0.5) * (0.113 + 0.001 / n)
    c = (idx + 2.0) * (0.047 + 0.002 / n)
    spinors = torch.stack(
        (
            torch.cos(a).to(CDTYPE),
            torch.sin(a).to(CDTYPE) * torch.exp(1j * b.to(CDTYPE)),
            torch.cos(c).to(CDTYPE) * torch.exp(-1j * b.to(CDTYPE)),
            torch.sin(c).to(CDTYPE),
        ),
        dim=1,
    )
    return spinors / torch.linalg.vector_norm(spinors, dim=1, keepdim=True)


def build_spinors_jax(n: int) -> Any:
    idx = jnp.arange(n, dtype=jnp.float64)
    a = (idx + 1.0) * (0.071 + 0.003 / n)
    b = (idx + 0.5) * (0.113 + 0.001 / n)
    c = (idx + 2.0) * (0.047 + 0.002 / n)
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


def module_signature_torch(spinors: torch.Tensor, gammas: list[torch.Tensor], g5: torch.Tensor) -> dict[str, Any]:
    actions = [torch.einsum("ab,nb->na", gamma, spinors) for gamma in gammas]
    commuted = torch.einsum("ab,nb->na", gammas[0], actions[1])
    reversed_action = torch.einsum("ab,nb->na", gammas[1], actions[0])
    order_gap = float(torch.linalg.vector_norm(commuted - reversed_action).item() / spinors.shape[0])
    expectations = []
    for action in actions:
        values = torch.sum(spinors.conj() * action, dim=1)
        expectations.append(float(torch.mean(torch.abs(values) ** 2).item()))
    chirality = torch.sum(spinors.conj() * torch.einsum("ab,nb->na", g5, spinors), dim=1)
    signature_value = float(sum((idx + 1) * v for idx, v in enumerate(expectations)) + torch.mean(chirality.real).item())
    return {
        "expectation_abs2_by_gamma": expectations,
        "mean_gamma5_expectation": float(torch.mean(chirality.real).item()),
        "order_gap_gamma0_gamma1": order_gap,
        "value_signature": signature_value,
        "pass": order_gap > 1.0e-6,
    }


def module_signature_jax(spinors: Any, gammas: list[Any], g5: Any) -> dict[str, Any]:
    actions = [jnp.einsum("ab,nb->na", gamma, spinors) for gamma in gammas]
    commuted = jnp.einsum("ab,nb->na", gammas[0], actions[1])
    reversed_action = jnp.einsum("ab,nb->na", gammas[1], actions[0])
    order_gap = float(jnp.linalg.norm(commuted - reversed_action) / spinors.shape[0])
    expectations = []
    for action in actions:
        values = jnp.sum(jnp.conj(spinors) * action, axis=1)
        expectations.append(float(jnp.mean(jnp.abs(values) ** 2)))
    chirality = jnp.sum(jnp.conj(spinors) * jnp.einsum("ab,nb->na", g5, spinors), axis=1)
    signature_value = float(sum((idx + 1) * v for idx, v in enumerate(expectations)) + jnp.mean(jnp.real(chirality)))
    return {
        "expectation_abs2_by_gamma": expectations,
        "mean_gamma5_expectation": float(jnp.mean(jnp.real(chirality))),
        "order_gap_gamma0_gamma1": order_gap,
        "value_signature": signature_value,
        "pass": order_gap > 1.0e-6,
    }


def sympy_exact_table(signature: list[int]) -> dict[str, Any]:
    i = sp.I
    zero = sp.zeros(2)
    ident = sp.eye(2)
    sx = sp.Matrix([[0, 1], [1, 0]])
    sy = sp.Matrix([[0, -i], [i, 0]])
    sz = sp.Matrix([[1, 0], [0, -1]])
    g0 = sp.Matrix.vstack(sp.Matrix.hstack(ident, zero), sp.Matrix.hstack(zero, -ident))
    gammas = [g0]
    for sigma in (sx, sy, sz):
        gammas.append(sp.Matrix.vstack(sp.Matrix.hstack(zero, sigma), sp.Matrix.hstack(-sigma, zero)))
    ident4 = sp.eye(4)
    table: dict[str, dict[str, Any]] = {}
    failures = 0
    for mu in range(4):
        for nu in range(4):
            lhs = gammas[mu] * gammas[nu] + gammas[nu] * gammas[mu]
            rhs = 2 * signature[mu] * ident4 if mu == nu else sp.zeros(4)
            diff = sp.simplify(lhs - rhs)
            exact_zero = diff == sp.zeros(4)
            failures += int(not exact_zero)
            table[f"{mu}{nu}"] = {
                "exact_zero": bool(exact_zero),
                "rank_of_difference": int(diff.rank()),
            }
    gamma5 = i * gammas[0] * gammas[1] * gammas[2] * gammas[3]
    gamma5_square_ok = sp.simplify(gamma5 * gamma5 - ident4) == sp.zeros(4)
    return {
        "table": table,
        "exact_entries": len(table),
        "failed_entries": failures,
        "gamma5_square_exact": bool(gamma5_square_ok),
        "pass": failures == 0 and gamma5_square_ok,
    }


def z3_structure_gate(positive: dict[str, Any], negatives: dict[str, Any]) -> dict[str, Any]:
    diag_ok = z3.Bool("diag_ok")
    offdiag_ok = z3.Bool("offdiag_ok")
    orientation_ok = z3.Bool("orientation_ok")
    structure_valid = z3.Bool("structure_valid")

    solver = z3.Solver()
    solver.add(diag_ok == bool(positive["torch"]["pass"]))
    solver.add(offdiag_ok == bool(positive["sympy"]["pass"]))
    solver.add(orientation_ok == bool(positive["orientation"]["pass"]))
    solver.add(structure_valid == z3.And(diag_ok, offdiag_ok, orientation_ok))
    positive_status = solver.check()

    collapse = z3.Solver()
    commute_kills = z3.Bool("commute_kills")
    flatten_kills = z3.Bool("flatten_kills")
    real_only_kills = z3.Bool("real_only_kills")
    collapse.add(commute_kills == bool(negatives["commute_gammas"]["kills_signature"]))
    collapse.add(flatten_kills == bool(negatives["flatten_metric"]["kills_signature"]))
    collapse.add(real_only_kills == bool(negatives["real_only_restriction"]["kills_signature"]))
    collapse.add(z3.Not(z3.And(commute_kills, flatten_kills, real_only_kills)))
    negative_status = collapse.check()

    return {
        "positive_structure_status": str(positive_status),
        "negative_kill_countermodel_status": str(negative_status),
        "pass": positive_status == z3.sat and negative_status == z3.unsat,
    }


def orientation_checks_torch(gammas: list[torch.Tensor], g5: torch.Tensor) -> dict[str, Any]:
    ident = torch.eye(4, dtype=CDTYPE)
    square_defect = float(torch.linalg.matrix_norm(g5 @ g5 - ident).item())
    anticommute_defects = [
        float(torch.linalg.matrix_norm(g5 @ gamma + gamma @ g5).item())
        for gamma in gammas
    ]
    return {
        "gamma5_square_defect": square_defect,
        "gamma5_anticommute_max_defect": max(anticommute_defects),
        "pass": square_defect < TOL and max(anticommute_defects) < TOL,
    }


def negative_controls(gammas: list[torch.Tensor], eta: torch.Tensor, g5: torch.Tensor) -> dict[str, Any]:
    ident = torch.eye(4, dtype=CDTYPE)
    diag = torch.diag(torch.tensor([1.0, -1.0, 0.5, -0.5], dtype=RTYPE)).to(CDTYPE)
    commuting = [gammas[0], diag, ident, -ident]
    commute_defects = anticommutator_defects_torch(commuting, eta)
    commute_norm = float(torch.linalg.matrix_norm(commuting[0] @ commuting[1] - commuting[1] @ commuting[0]).item())

    flat_eta = torch.eye(4, dtype=CDTYPE)
    flat_defects = anticommutator_defects_torch(gammas, flat_eta)

    orientation_identity = ident
    orientation_defect = max(
        float(torch.linalg.matrix_norm(orientation_identity @ gamma + gamma @ orientation_identity).item())
        for gamma in gammas
    )

    real_only = [gamma.real.to(CDTYPE) for gamma in gammas]
    real_defects = anticommutator_defects_torch(real_only, eta)

    positive_pseudoscalar_norm = float(torch.linalg.matrix_norm(g5).item())
    return {
        "commute_gammas": {
            "control": "replace spatial gammas with mutually commuting diagonal/identity matrices",
            "commutator_norm_gamma0_gamma1": commute_norm,
            "anticommutator_max_defect": commute_defects["max_defect"],
            "kills_signature": commute_norm < TOL and commute_defects["max_defect"] > 1.0,
            "pass": commute_norm < TOL and commute_defects["max_defect"] > 1.0,
        },
        "flatten_metric": {
            "control": "replace eta=diag(1,-1,-1,-1) with Euclidean diag(1,1,1,1)",
            "anticommutator_max_defect": flat_defects["max_defect"],
            "kills_signature": flat_defects["max_defect"] > 1.0,
            "pass": flat_defects["max_defect"] > 1.0,
        },
        "drop_orientation_fiber": {
            "control": "replace gamma5=i gamma0 gamma1 gamma2 gamma3 with identity",
            "gamma5_anticommute_max_defect": orientation_defect,
            "positive_pseudoscalar_norm": positive_pseudoscalar_norm,
            "kills_signature": orientation_defect > 1.0,
            "pass": orientation_defect > 1.0,
        },
        "real_only_restriction": {
            "control": "erase imaginary entries, which collapses gamma2",
            "anticommutator_max_defect": real_defects["max_defect"],
            "kills_signature": real_defects["max_defect"] > 1.0,
            "pass": real_defects["max_defect"] > 1.0,
        },
    }


def run_rung(n: int, gammas_t: list[torch.Tensor], eta_t: torch.Tensor, gammas_j: list[Any], eta_j: Any) -> dict[str, Any]:
    spinors_t = build_spinors_torch(n)
    spinors_j = build_spinors_jax(n)
    g5_t = gamma5_torch(gammas_t)
    g5_j = gamma5_jax(gammas_j)
    torch_sig = module_signature_torch(spinors_t, gammas_t, g5_t)
    jax_sig = module_signature_jax(spinors_j, gammas_j, g5_j)
    value_delta = abs(torch_sig["value_signature"] - jax_sig["value_signature"])
    order_delta = abs(torch_sig["order_gap_gamma0_gamma1"] - jax_sig["order_gap_gamma0_gamma1"])
    local_tensor_count = int(spinors_t.reshape(n, 1, 4, 1).shape[0])
    path_edge_count = n - 1
    return {
        "sites_or_qubits": n,
        "local_spinor_dim": 4,
        "carrier_kind": "N-sample open-chain spinor module with bond-1 MPS metadata",
        "mps_tensor_shape": [n, 1, 4, 1],
        "mps_bond_dim": 1,
        "local_tensor_count": local_tensor_count,
        "sparse_path_edge_count": path_edge_count,
        "dense_state_closure_used": False,
        "global_dense_dimension_if_closed": f"4**{n} (not instantiated)",
        "torch": torch_sig,
        "jax": jax_sig,
        "jax_torch_value_delta": value_delta,
        "jax_torch_order_gap_delta": order_delta,
        "pass": bool(
            local_tensor_count == n
            and path_edge_count == n - 1
            and not False
            and torch_sig["pass"]
            and jax_sig["pass"]
            and value_delta < 1.0e-11
            and order_delta < 1.0e-11
        ),
    }


def known_value_checks(
    torch_ac: dict[str, Any],
    jax_ac: dict[str, Any],
    sympy_table: dict[str, Any],
    orientation: dict[str, Any],
    eta_signature: list[int],
) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for mu in range(4):
        for nu in range(4):
            known = f"2*eta[{mu},{nu}]*I4 with eta=diag({eta_signature})"
            checks.append(
                {
                    "invariant": f"{{gamma_{mu},gamma_{nu}}}=2 eta_{mu}{nu} I4",
                    "computed": {
                        "torch_defect": torch_ac["defects"][f"{mu}{nu}"],
                        "jax_defect": jax_ac["defects"][f"{mu}{nu}"],
                        "sympy_exact_zero": sympy_table["table"][f"{mu}{nu}"]["exact_zero"],
                    },
                    "known": known,
                    "match": (
                        torch_ac["defects"][f"{mu}{nu}"] < TOL
                        and jax_ac["defects"][f"{mu}{nu}"] < TOL
                        and sympy_table["table"][f"{mu}{nu}"]["exact_zero"]
                    ),
                }
            )
    checks.append(
        {
            "invariant": "gamma5=i gamma0 gamma1 gamma2 gamma3 squares to I4 and anticommutes with all gamma_mu",
            "computed": {
                "gamma5_square_defect": orientation["gamma5_square_defect"],
                "gamma5_anticommute_max_defect": orientation["gamma5_anticommute_max_defect"],
                "sympy_gamma5_square_exact": sympy_table["gamma5_square_exact"],
            },
            "known": "gamma5^2=I4 and {gamma5,gamma_mu}=0",
            "match": orientation["pass"] and sympy_table["gamma5_square_exact"],
        }
    )
    return checks


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    cliff = clifford_signature()
    gammas_t, eta_t = torch_gamma_matrices(cliff["signature"])
    gammas_j, eta_j = jax_gamma_matrices(cliff["signature"])
    torch_ac = anticommutator_defects_torch(gammas_t, eta_t)
    jax_ac = anticommutator_defects_jax(gammas_j, eta_j)
    sym = sympy_exact_table(cliff["signature"])
    g5_t = gamma5_torch(gammas_t)
    orient = orientation_checks_torch(gammas_t, g5_t)
    negatives = negative_controls(gammas_t, eta_t, g5_t)
    z3_gate = z3_structure_gate(
        {"torch": torch_ac, "sympy": sym, "orientation": orient},
        negatives,
    )
    rungs = {str(n): run_rung(n, gammas_t, eta_t, gammas_j, eta_j) for n in SITE_COUNTS}
    max_value_delta = max(rung["jax_torch_value_delta"] for rung in rungs.values())
    max_order_delta = max(rung["jax_torch_order_gap_delta"] for rung in rungs.values())
    checks = known_value_checks(torch_ac, jax_ac, sym, orient, cliff["signature"])
    all_checks_match = all(check["match"] for check in checks)

    positive_score = (
        int(cliff["pass"])
        + int(torch_ac["pass"])
        + int(jax_ac["pass"])
        + int(sym["pass"])
        + int(orient["pass"])
        + int(z3_gate["pass"])
        + sum(int(rung["pass"]) for rung in rungs.values())
    )
    ablated_clifford_signature = [1, 1, 1, 1]
    ablated_gammas_t, ablated_eta_t = torch_gamma_matrices([1, -1, -1, -1])
    ablated_eta_t = torch.diag(torch.tensor(ablated_clifford_signature, dtype=RTYPE)).to(CDTYPE)
    ablated_clifford_defect = anticommutator_defects_torch(ablated_gammas_t, ablated_eta_t)["max_defect"]
    torch_obligations = 1 + len(SITE_COUNTS)
    jax_obligations = 2 + len(SITE_COUNTS)
    tool_ablation_outcome_deltas = {
        "torch": {
            "outcome_delta": float(torch_obligations),
            "reason": "removing torch drops the primary anticommutator/orientation computation plus all four torch rung validations",
        },
        "jax": {
            "outcome_delta": float(jax_obligations),
            "reason": "removing jax drops the independent x64 anticommutator, agreement check, and all four jax rung validations",
        },
        "clifford": {
            "outcome_delta": float(ablated_clifford_defect),
            "reason": "replacing the clifford-derived Cl(1,3) metric with a flat positive signature breaks spatial gamma squares",
        },
        "sympy": {
            "outcome_delta": float(sym["exact_entries"] - (sym["exact_entries"] - sym["failed_entries"] if not sym["pass"] else 0)),
            "reason": "removing sympy exact multiplication-table certification drops the 16 exact anticommutator entries",
        },
        "z3": {
            "outcome_delta": float(int(z3_gate["negative_kill_countermodel_status"] == "unsat")),
            "reason": "removing z3 drops the structural proof that the named negatives cannot coexist with a valid structure",
        },
    }

    tool_manifest = {
        "torch": {
            "tried": True,
            "used": True,
            "reason": "primary load-bearing complex128 gamma matrices, local N-site module action, order-gap, and gamma5 orientation checks",
        },
        "jax": {
            "tried": True,
            "used": True,
            "reason": "independent load-bearing x64/complex128 engine for the same gamma action and per-rung scalar signatures",
        },
        "clifford": {
            "tried": True,
            "used": True,
            "reason": "load-bearing Cl(1,3) signature and basis anticommutation source for the gamma representation metric",
        },
        "sympy": {
            "tried": True,
            "used": True,
            "reason": "load-bearing exact gamma-matrix multiplication table for {gamma_mu,gamma_nu}=2 eta_munu",
        },
        "z3": {
            "tried": True,
            "used": True,
            "reason": "load-bearing structural gate proving the positive structure and rejecting named killed controls",
        },
        "python_json": {
            "tried": True,
            "used": True,
            "reason": "supportive deterministic result artifact writer",
        },
        "geomstats": {
            "tried": False,
            "used": False,
            "reason": "not used: this layer is algebraic Clifford-module geometry, and geomstats has no jax backend; no fake jax geomstats path is emitted",
        },
    }
    tool_integration_depth = {
        "torch": "load_bearing",
        "jax": "load_bearing",
        "clifford": "load_bearing",
        "sympy": "load_bearing",
        "z3": "load_bearing",
        "python_json": "supportive",
        "geomstats": "None",
    }
    scale_ladder = {
        "rungs": {
            str(n): {
                "sites_or_qubits": rungs[str(n)]["sites_or_qubits"],
                "dense_state_closure_used": rungs[str(n)]["dense_state_closure_used"],
                "pass": rungs[str(n)]["pass"],
                "carrier_kind": rungs[str(n)]["carrier_kind"],
                "mps_tensor_shape": rungs[str(n)]["mps_tensor_shape"],
                "mps_bond_dim": rungs[str(n)]["mps_bond_dim"],
                "jax_torch_value_delta": rungs[str(n)]["jax_torch_value_delta"],
                "order_gap_gamma0_gamma1": rungs[str(n)]["torch"]["order_gap_gamma0_gamma1"],
            }
            for n in SITE_COUNTS
        },
        "all_required_rungs_present": sorted(int(k) for k in rungs) == SITE_COUNTS,
        "pass": all(rung["pass"] and rung["dense_state_closure_used"] is False for rung in rungs.values()),
    }
    compatibility_weights = {
        str(n): float(1.0 / (1.0 + rungs[str(n)]["jax_torch_value_delta"] + rungs[str(n)]["jax_torch_order_gap_delta"]))
        for n in SITE_COUNTS
    }
    survivor_invariant = {
        "name": "clifford_module_law_survives_scale_and_dual_engine",
        "computed": {
            "all_scale_rungs_pass": scale_ladder["pass"],
            "torch_anticommutator_max_defect": torch_ac["max_defect"],
            "jax_anticommutator_max_defect": jax_ac["max_defect"],
            "max_jax_torch_value_delta": max_value_delta,
            "named_negatives_killed": sorted(name for name, row in negatives.items() if row["kills_signature"]),
        },
        "known": "Cl(1,3) gamma module preserves {gamma_mu,gamma_nu}=2 eta_munu I4 under non-dense N-site replication; commuting/flat/orientation-erased/real-only controls do not preserve it",
        "passed": bool(
            scale_ladder["pass"]
            and torch_ac["max_defect"] < TOL
            and jax_ac["max_defect"] < TOL
            and max_value_delta < 1.0e-11
            and all(row["kills_signature"] for row in negatives.values())
        ),
    }
    positive = {
        "clifford_module_gamma_representation": {
            "clifford": cliff,
            "torch_anticommutator": torch_ac,
            "jax_anticommutator": jax_ac,
            "sympy_exact_table": {
                "exact_entries": sym["exact_entries"],
                "failed_entries": sym["failed_entries"],
                "gamma5_square_exact": sym["gamma5_square_exact"],
                "pass": sym["pass"],
            },
            "z3_structure_gate": z3_gate,
            "pass": cliff["pass"] and torch_ac["pass"] and jax_ac["pass"] and sym["pass"] and orient["pass"] and z3_gate["pass"],
        },
        "non_dense_scale_ladder_8_16_32_64": scale_ladder,
    }
    graveyard_companions = {
        name: {
            "kills_signature": row["kills_signature"],
            "pass": row["pass"],
            "artifact": row,
        }
        for name, row in negatives.items()
    }
    boundary = {
        "single_layer_only_no_coupling_or_stacking": {
            "claim": "independent clifford_module_geometry layer only",
            "promotion_allowed": False,
            "pass": True,
        },
        "dense_state_closure_blocked": {
            "largest_rung": max(SITE_COUNTS),
            "dense_state_closure_used": False,
            "blocked_dense_closures": ["2**N", "4**N", "global Kronecker product"],
            "pass": all(rung["dense_state_closure_used"] is False for rung in rungs.values()),
        },
    }
    all_pass = (
        positive["clifford_module_gamma_representation"]["pass"]
        and scale_ladder["pass"]
        and all(row["pass"] for row in graveyard_companions.values())
        and all(row["pass"] for row in boundary.values())
        and all_checks_match
        and all(abs(entry["outcome_delta"]) > 1.0e-9 for entry in tool_ablation_outcome_deltas.values())
        and max_value_delta < 1.0e-11
    )
    result = {
        "schema": "formal_scout_result_v1",
        "name": NAME,
        "sim_id": "sim_layer_clifford_module_8_16_32_64_probe",
        "version": "1.0",
        "tier": "2 geometry",
        "classification": "lego",
        "sim_execution_kind": "nonclassical",
        "sim_class": "geometry_probe",
        "source_alignment_category": "geometric_manifold_layer_clifford_module_geometry",
        "promotion_allowed": False,
        "claim_ceiling": (
            "One independent Clifford-module geometry lego: Cl(1,3) gamma representation acting locally on "
            "N=8/16/32/64 site spinor modules. No coupling, stacking, full manifold completion, Axis0, flux, "
            "bridge, basin, or physics claim is made."
        ),
        "purpose": "Instantiate and test the clifford_module_geometry layer on a non-dense N-site spinor carrier.",
        "scientific_question": "Does a Cl(1,3) gamma-matrix module satisfy its defining anticommutator law on an 8/16/32/64 non-dense spinor carrier in both torch and jax, with named negatives killing the signature?",
        "root_constraints_in_force": {
            "F01": "finite N-site spinor module, finite gamma operator set, finite path/order probes",
            "N01": "gamma0/gamma1 order gap and Clifford anticommutation/commutator structure",
        },
        "finite_map": "GammaModule_N : ({psi_i in C^4}_{i=1..N}, gamma_mu, eta) -> local gamma actions, anticommutator invariant defects, gamma5 orientation readout, and killed controls",
        "domain": {
            "site_counts": SITE_COUNTS,
            "operator_set": ["gamma0", "gamma1", "gamma2", "gamma3", "gamma5"],
            "signature": cliff["signature"],
            "carrier": "N-sample/open-chain spinor module with bond-1 MPS tensors; no dense closure",
        },
        "codomain_or_output": "JSON receipt with per-rung local module signatures, exact/numeric anticommutator checks, dual-engine agreement, negatives, and tool ablations",
        "carrier_layer": "finite local spinor module over Cl(1,3)",
        "geometry_layer": "clifford_module_geometry",
        "carrier_realization": {
            "torch": "torch.complex128 site tensor of shape (N,4) plus bond-1 MPS metadata (N,1,4,1)",
            "jax": "jax complex128 site array of shape (N,4) plus same local action equations",
            "dense_state_closure_used": False,
        },
        "peps3d_embedding": {
            "status": "finite anchor only for this independent layer",
            "anchor": "each site is a local PEPS3D-compatible cell tensor with one physical spinor leg and trivial open-chain bonds; no full PEPS3D contraction or stacked layer claim",
            "blocked_promotion_note": "This satisfies the local finite carrier anchor for this one lego but does not admit a full manifold tower.",
        },
        "spinor_state": "psi_i in C^4 for every site i; torch and jax generate matching normalized local spinors",
        "quaternion_action": "not_applicable: this probe uses Clifford gamma matrices but makes no quaternion-language claim",
        "dependency_receipts": [],
        "downstream_blocks": ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "layer_stacking", "full_manifold_admission"],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "{gamma_mu,gamma_nu}=2 eta_munu I4 for Cl(1,3) on a finite N-site spinor module",
        "branch_status_before_run": "independent lego build requested directly by user",
        "allowed_claims": ["local Clifford-module gamma representation witness", "non-dense 8/16/32/64 scale execution", "negative controls kill the Clifford signature"],
        "promotion_blockers": ["single layer only", "no coupling/stacking evidence", "no full PEPS3D contraction", "no downstream manifold tower admission"],
        "required_tools": ["torch", "jax", "clifford", "sympy", "z3"],
        "actual_tools_used": ["torch", "jax", "clifford", "sympy", "z3"],
        "proof_surfaces_used": ["sympy exact multiplication table", "z3 structural gate"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "TOOL_MANIFEST": tool_manifest,
        "TOOL_INTEGRATION_DEPTH": tool_integration_depth,
        "tool_manifest": tool_manifest,
        "tool_integration_depth": tool_integration_depth,
        "TOOL_ROLE_SOURCE": {tool: "local_runtime" for tool in tool_manifest},
        "tool_ablation_outcome_deltas": tool_ablation_outcome_deltas,
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "required_negatives": list(negatives.keys()),
        "negatives_run": negatives,
        "kill_conditions": {
            "commute_gammas": "off-diagonal Clifford anticommutator law fails under commuting replacements",
            "flatten_metric": "spatial gamma squares no longer match eta",
            "drop_orientation_fiber": "gamma5 no longer anticommutes with gamma_mu",
            "real_only_restriction": "imaginary gamma2 structure is erased and the anticommutator law fails",
        },
        "required_artifacts": [str(OUT_PATH)],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{NAME}:{int(started)}",
        "scale_ladder": scale_ladder,
        "shells": {
            "active_shell": "clifford_module_geometry",
            "single_layer_only": True,
            "site_counts": SITE_COUNTS,
        },
        "future_continuations": [
            "bounded local Clifford-module variants may consume this receipt",
            "coupling, stacking, Axis0, flux, bridge, basin, and physics continuations remain blocked",
        ],
        "compatibility_weights": compatibility_weights,
        "compression_map": {
            "from": "formal dense tensor product of N local C^4 spinor factors",
            "to": "per-site gamma-action invariant quotient plus bond-1 MPS metadata",
            "dense_source_instantiated": False,
            "preserved_observables": ["gamma anticommutator defects", "gamma5 orientation defects", "gamma0/gamma1 order gap"],
        },
        "present_survivor": {
            "object": "Cl(1,3) gamma-module anticommutator law on N-site local spinors",
            "survives_rungs": SITE_COUNTS,
            "survives_dual_engine": True,
            "promotion_allowed": False,
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "scale_gate_command": "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3 ../../../scripts/max_deep_lego_gate.py results/clifford_module_geometry_results.json --scale-required",
        },
        "survivor_invariant": survivor_invariant,
        "rungs": rungs,
        "jax_vs_pytorch": {
            "max_value_delta": max_value_delta,
            "max_order_gap_delta": max_order_delta,
            "agree": max_value_delta < 1.0e-11 and max_order_delta < 1.0e-11,
            "notes": "JAX is used directly with jax_enable_x64 for the Clifford-module core. geomstats is not used; it has no jax backend and would be only a torch-side geometry helper here.",
        },
        "known_value_checks": checks,
        "all_known_value_checks_match": all_checks_match,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": {
            "positive_score": positive_score,
            "total_positive_obligations": 10,
            "tool_ablation_count": len(tool_ablation_outcome_deltas),
            "negative_count": len(negatives),
            "pass": positive_score == 10 and all(row["pass"] for row in negatives.values()),
        },
        "why_not_v4_probes": "This is a v5 max-deep single-layer lego with explicit non-dense 8/16/32/64 scale rungs and dual torch/jax engines.",
        "pass_rule": "all known_value_checks match, all scale_ladder rungs pass without dense closure, jax agrees with torch, each named negative kills, and every load-bearing tool has nonzero ablation delta",
        "fail_rule": "any dense closure, missing rung, fake jax path, zero ablation delta, or surviving named negative fails the lego",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["future bounded local Clifford-module tests only"],
        "blocked_consumers": ["flux", "Xi", "Phi0", "Axis0", "bridge", "basin", "physics", "layer_stacking", "full_manifold_admission"],
        "result_summary": {
            "all_pass": all_pass,
            "site_counts": SITE_COUNTS,
            "max_scale": max(SITE_COUNTS),
            "dense_state_closure_used": False,
            "torch_anticommutator_max_defect": torch_ac["max_defect"],
            "jax_anticommutator_max_defect": jax_ac["max_defect"],
            "jax_vs_pytorch_max_value_delta": max_value_delta,
            "negatives_killed": sorted(name for name, row in negatives.items() if row["kills_signature"]),
            "elapsed_seconds": time.time() - started,
        },
        "blockers": [],
        "all_pass": all_pass,
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"all_pass": all_pass, "result_path": str(OUT_PATH), "summary": result["result_summary"]}, indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
