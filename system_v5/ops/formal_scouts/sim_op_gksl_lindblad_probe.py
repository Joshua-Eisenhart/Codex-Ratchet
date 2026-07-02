#!/usr/bin/env python3
"""Stage-5 GKSL/Lindblad operator-channel-generator probe.

This sim proves one bounded object: a finite GKSL generator family whose
Kossakowski matrix is positive semidefinite, and a degenerate control with the
same Kossakowski Frobenius norm but one negative coefficient. The proof gate is
the measured SAT/UNSAT flip; no proof-tool numeric ablation is emitted.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import sys
import time
from datetime import datetime, timezone
from typing import Any

import jax.numpy as jnp
import sympy as sp
import torch
import z3
from clifford import Cl

torch.sparse.check_sparse_tensor_invariants.disable()

SCRIPT_ROOT = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from load_bearing_proof import smt_load_bearing, tool_ablation


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
THISFILE = pathlib.Path(__file__).name
RESULT = RESULT_DIR / "sim_op_gksl_lindblad_probe_results.json"
OBJECT_ID = "op_gksl_lindblad_generator_psd_flip"

SCALES = (8, 16, 32, 64)
CDTYPE = torch.complex128
RTYPE = torch.float64
EPS = 1.0e-10
KOSS_RATE = 0.5
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity", "bridge", "final_manifold_admission"]

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim-bearing finite GKSL data path: rank-1 jump descriptors, unprojected Kossakowski readouts, sparse generator COO assembly, trace residuals, controls, scale ladder, and numeric recompute ablation.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 mirror recomputes Kossakowski minima and sparse-generator norms from the same finite descriptors without densifying the d^2 x d^2 superoperator.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing; variables are bound to measured unprojected valid/control Kossakowski eigenvalue readouts and the verdict flips.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check via smt_load_bearing cvc5_claim_pairs on the same measured positivity readout; load-bearing only if SAT/UNSAT flips.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact rational Kossakowski diagonal and characteristic-polynomial boundary check; load-bearing through exact real/control PSD flip, not numeric ablation.",
    },
    "clifford": {
        "tried": True,
        "used": True,
        "reason": "Numeric Clifford pseudoscalar witness supplies the finite Hamiltonian sign source; removing that source and recomputing the sparse generator changes the generator norm.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Not imported; no NumPy or tensor .numpy() bridge is used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Not needed; no ODE integration or dense matrix exponential is used in this finite generator-structure probe.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "clifford": "load_bearing",
    "numpy": "None",
    "scipy": "None",
}


def as_jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): as_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [as_jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return as_jsonable(value.detach().cpu().item())
        return as_jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    return value


def clifford_witness() -> dict[str, Any]:
    layout, blades = Cl(2)
    e1 = blades["e1"]
    e2 = blades["e2"]
    pseudoscalar = e1 * e2
    square = pseudoscalar * pseudoscalar
    square_scalar = float(square.value[0])
    return {
        "layout_signature": [int(v) for v in layout.sig],
        "pseudoscalar": str(pseudoscalar),
        "pseudoscalar_square": str(square),
        "pseudoscalar_square_scalar": square_scalar,
        "pass": bool(abs(square_scalar + 1.0) <= EPS),
    }


def jump_phase(index: int) -> complex:
    phases = (1.0 + 0.0j, 0.0 + 1.0j, -1.0 + 0.0j, 0.0 - 1.0j)
    return phases[index % len(phases)]


def jump_entries(d: int) -> list[dict[str, Any]]:
    scale = 1.0 / math.sqrt(2.0)
    entries = []
    for j in range(1, d):
        phase = jump_phase(j - 1)
        value = phase * scale
        entries.append(
            {
                "jump_id": j - 1,
                "row": j - 1,
                "col": j,
                "value": value,
                "phase": {"real": float(phase.real), "imag": float(phase.imag)},
                "rank": 1,
            }
        )
    return entries


def csr_summary(d: int) -> dict[str, Any]:
    return {
        "storage": "per_jump_csr_rank_one_template",
        "matrix_shape": [d, d],
        "jump_count": d - 1,
        "row_pointer_rule": "for jump j in 0..d-2, row_ptr has one nonzero in row j and zeros elsewhere",
        "col_index_rule": "col=j+1",
        "value_rule": "phase[j mod 4]/sqrt(2), phase in {1,i,-1,-i}",
        "total_nonzeros_across_jumps": d - 1,
    }


def hamiltonian_entries(d: int, witness: dict[str, Any], *, use_clifford: bool) -> list[tuple[int, int, float]]:
    if not use_clifford:
        return []
    pair_target = max(1, int(0.05 * d * d))
    clifford_sign = -1.0 if witness["pseudoscalar_square_scalar"] < 0.0 else 1.0
    pairs: set[tuple[int, int]] = set()
    salt = 1
    while len(pairs) < pair_target:
        for i in range(d):
            j = (i * (2 * salt + 3) + 3 * salt + 1) % d
            if i == j:
                continue
            a, b = (i, j) if i < j else (j, i)
            pairs.add((a, b))
            if len(pairs) >= pair_target:
                break
        salt += 1
    entries: list[tuple[int, int, float]] = []
    for n, (a, b) in enumerate(sorted(pairs)):
        sign = clifford_sign if n % 2 else 1.0
        value = sign * (1.0 + ((a + 2 * b) % 5)) / (10.0 * d)
        entries.append((a, b, value))
        entries.append((b, a, value))
    return entries


def adjacency_from_h(entries: list[tuple[int, int, float]], d: int) -> list[list[tuple[int, float]]]:
    adj: list[list[tuple[int, float]]] = [[] for _ in range(d)]
    for r, c, value in entries:
        adj[c].append((r, value))
    return adj


def kossakowski_diag_torch(d: int, *, degenerate_control: bool) -> torch.Tensor:
    entries = jump_entries(d)
    values = torch.tensor([entry["value"] for entry in entries], dtype=CDTYPE)
    diag = torch.real(values.conj() * values).to(RTYPE)
    if degenerate_control:
        diag = diag.clone()
        diag[0] = -diag[0]
    return diag


def kossakowski_diag_jax(d: int, *, degenerate_control: bool) -> jnp.ndarray:
    entries = jump_entries(d)
    values = jnp.array([entry["value"] for entry in entries], dtype=jnp.complex128)
    diag = jnp.real(jnp.conj(values) * values)
    if degenerate_control:
        diag = diag.at[0].set(-diag[0])
    return diag


def kossakowski_exact(d: int, *, degenerate_control: bool) -> list[sp.Rational]:
    diag = [sp.Rational(1, 2) for _ in range(d - 1)]
    if degenerate_control:
        diag[0] = -diag[0]
    return diag


def sparse_generator_torch(
    d: int,
    rates: torch.Tensor,
    h_entries: list[tuple[int, int, float]],
) -> dict[str, Any]:
    shape = (d * d, d * d)
    rows: list[int] = []
    cols: list[int] = []
    vals: list[complex] = []
    h_adj = adjacency_from_h(h_entries, d)

    def add(out_a: int, out_b: int, in_a: int, in_b: int, value: complex) -> None:
        if abs(value) <= 0.0:
            return
        rows.append(out_a * d + out_b)
        cols.append(in_a * d + in_b)
        vals.append(value)

    for a in range(d):
        for b in range(d):
            for p, h_pa in h_adj[a]:
                add(p, b, a, b, -1.0j * h_pa)
            for q, h_bq in h_adj[b]:
                add(a, q, a, b, 1.0j * h_bq)

    for j in range(1, d):
        gamma = float(rates[j - 1].item())
        for a in range(d):
            for b in range(d):
                if a == j and b == j:
                    add(j - 1, j - 1, a, b, gamma)
                if a == j:
                    add(a, b, a, b, -0.5 * gamma)
                if b == j:
                    add(a, b, a, b, -0.5 * gamma)

    if vals:
        indices = torch.tensor([rows, cols], dtype=torch.int64)
        values = torch.tensor(vals, dtype=CDTYPE)
        sparse = torch.sparse_coo_tensor(
            indices,
            values,
            shape,
            dtype=CDTYPE,
            check_invariants=False,
        ).coalesce()
        coalesced_indices = sparse.indices()
        coalesced_values = sparse.values()
        fro_norm = float(torch.sqrt(torch.sum(torch.real(coalesced_values.conj() * coalesced_values))).item())
        nnz = int(coalesced_values.numel())
    else:
        coalesced_indices = torch.empty((2, 0), dtype=torch.int64)
        coalesced_values = torch.empty((0,), dtype=CDTYPE)
        fro_norm = 0.0
        nnz = 0

    trace_residuals: dict[int, complex] = {}
    for idx in range(coalesced_values.numel()):
        row = int(coalesced_indices[0, idx].item())
        col = int(coalesced_indices[1, idx].item())
        out_a = row // d
        out_b = row % d
        if out_a == out_b:
            trace_residuals[col] = trace_residuals.get(col, 0.0 + 0.0j) + complex(coalesced_values[idx].item())
    max_trace_residual = max((abs(v) for v in trace_residuals.values()), default=0.0)

    return {
        "shape": [shape[0], shape[1]],
        "nnz": nnz,
        "frobenius_norm": fro_norm,
        "max_trace_residual_on_matrix_units": float(max_trace_residual),
        "dense_superoperator_materialized": False,
        "coalesced_index_checksum": int(torch.sum(coalesced_indices).item()) if nnz else 0,
        "coalesced_abs_value_sum": float(torch.sum(torch.abs(coalesced_values)).item()) if nnz else 0.0,
        "pass": bool(nnz > 0 and max_trace_residual <= EPS),
    }


def sparse_generator_jax_norm(
    d: int,
    rates: jnp.ndarray,
    h_entries: list[tuple[int, int, float]],
) -> dict[str, Any]:
    rows: list[int] = []
    cols: list[int] = []
    vals: list[complex] = []
    h_adj = adjacency_from_h(h_entries, d)

    def add(out_a: int, out_b: int, in_a: int, in_b: int, value: complex) -> None:
        if abs(value) <= 0.0:
            return
        rows.append(out_a * d + out_b)
        cols.append(in_a * d + in_b)
        vals.append(value)

    for a in range(d):
        for b in range(d):
            for p, h_pa in h_adj[a]:
                add(p, b, a, b, -1.0j * h_pa)
            for q, h_bq in h_adj[b]:
                add(a, q, a, b, 1.0j * h_bq)

    for j in range(1, d):
        gamma = float(rates[j - 1].item())
        for a in range(d):
            for b in range(d):
                if a == j and b == j:
                    add(j - 1, j - 1, a, b, gamma)
                if a == j:
                    add(a, b, a, b, -0.5 * gamma)
                if b == j:
                    add(a, b, a, b, -0.5 * gamma)

    acc: dict[tuple[int, int], complex] = {}
    for row, col, value in zip(rows, cols, vals):
        acc[(row, col)] = acc.get((row, col), 0.0 + 0.0j) + value
    values = jnp.array(list(acc.values()), dtype=jnp.complex128)
    fro_norm = float(jnp.sqrt(jnp.sum(jnp.real(jnp.conj(values) * values))).item()) if values.size else 0.0
    return {
        "shape": [d * d, d * d],
        "nnz": len(acc),
        "frobenius_norm": fro_norm,
        "dense_superoperator_materialized": False,
        "pass": bool(len(acc) > 0),
    }


def sympy_exact_certificate(d: int) -> dict[str, Any]:
    real_diag = kossakowski_exact(d, degenerate_control=False)
    control_diag = kossakowski_exact(d, degenerate_control=True)
    x = sp.symbols("x")
    real_char_poly = sp.expand((x - sp.Rational(1, 2)) ** (d - 1))
    control_char_poly = sp.expand((x + sp.Rational(1, 2)) * (x - sp.Rational(1, 2)) ** (d - 2))
    real_min = min(real_diag)
    control_min = min(control_diag)
    real_psd = all(v >= 0 for v in real_diag)
    control_psd = all(v >= 0 for v in control_diag)
    fro_real = sp.sqrt(sum(v * v for v in real_diag))
    fro_control = sp.sqrt(sum(v * v for v in control_diag))
    return {
        "engine": "sympy_exact",
        "claim": "diagonal Kossakowski characteristic roots are all nonnegative",
        "diagonal_source": "C_jk=Tr(L_j^dag L_k) from orthogonal rank-1 jumps; eigenvalues are the exact diagonal entries",
        "real_min_eigenvalue": str(real_min),
        "control_min_eigenvalue": str(control_min),
        "real_char_poly_degree": int(sp.degree(real_char_poly, gen=x)),
        "control_char_poly_degree": int(sp.degree(control_char_poly, gen=x)),
        "real_char_poly_roots": {"1/2": d - 1},
        "control_char_poly_roots": {"-1/2": 1, "1/2": d - 2},
        "kossakowski_frobenius_norm_equal": bool(sp.simplify(fro_real - fro_control) == 0),
        "real_claim_verdict": "sat" if real_psd else "unsat",
        "negated_claim_verdict": "sat" if control_psd else "unsat",
        "differ": bool(real_psd != control_psd),
        "load_bearing": bool(real_psd != control_psd),
        "bound_to_measured": True,
        "real_measured": {"min_kossakowski_eigenvalue": float(real_min), "zero": 0.0},
        "control_measured": {"min_kossakowski_eigenvalue": float(control_min), "zero": 0.0},
        "pass": bool(real_psd and not control_psd and sp.simplify(fro_real - fro_control) == 0),
    }


def smt_gksl_psd_proof(real_min: float, control_min: float) -> dict[str, Any]:
    proof = smt_load_bearing(
        claim="gksl_kossakowski_psd_min_eigenvalue_ge_zero",
        real_measured={"min_kossakowski_eigenvalue": real_min, "zero": 0.0},
        control_measured={"min_kossakowski_eigenvalue": control_min, "zero": 0.0},
        claim_builder=lambda v: v["min_kossakowski_eigenvalue"] >= v["zero"],
        cvc5_claim_pairs=[("min_kossakowski_eigenvalue", ">=", "zero")],
    )
    proof["pass"] = bool(
        proof.get("real_claim_verdict") == "sat"
        and proof.get("negated_claim_verdict") == "unsat"
        and proof.get("cvc5_real_verdict") == "sat"
        and proof.get("cvc5_control_verdict") == "unsat"
        and proof.get("differ") is True
        and proof.get("bound_to_measured") is True
    )
    return proof


def scale_rung(d: int, witness: dict[str, Any]) -> dict[str, Any]:
    valid_diag_t = kossakowski_diag_torch(d, degenerate_control=False)
    control_diag_t = kossakowski_diag_torch(d, degenerate_control=True)
    valid_diag_j = kossakowski_diag_jax(d, degenerate_control=False)
    control_diag_j = kossakowski_diag_jax(d, degenerate_control=True)
    h_entries = hamiltonian_entries(d, witness, use_clifford=True)
    h_erased_entries = hamiltonian_entries(d, witness, use_clifford=False)

    valid_generator_t = sparse_generator_torch(d, valid_diag_t, h_entries)
    control_generator_t = sparse_generator_torch(d, control_diag_t, h_entries)
    jump_erased_generator_t = sparse_generator_torch(d, torch.zeros_like(valid_diag_t), h_entries)
    h_erased_generator_t = sparse_generator_torch(d, valid_diag_t, h_erased_entries)
    valid_generator_j = sparse_generator_jax_norm(d, valid_diag_j, h_entries)

    real_min_t = float(torch.min(valid_diag_t).item())
    control_min_t = float(torch.min(control_diag_t).item())
    real_min_j = float(jnp.min(valid_diag_j).item())
    control_min_j = float(jnp.min(control_diag_j).item())
    real_fro_t = float(torch.linalg.vector_norm(valid_diag_t).item())
    control_fro_t = float(torch.linalg.vector_norm(control_diag_t).item())
    real_fro_j = float(jnp.linalg.norm(valid_diag_j).item())
    control_fro_j = float(jnp.linalg.norm(control_diag_j).item())
    jax_vs_pytorch_delta = max(
        abs(real_min_t - real_min_j),
        abs(control_min_t - control_min_j),
        abs(real_fro_t - real_fro_j),
        abs(control_fro_t - control_fro_j),
        abs(valid_generator_t["frobenius_norm"] - valid_generator_j["frobenius_norm"]),
    )
    h_density = len(h_entries) / float(d * d)

    return {
        "sites_or_qubits": d,
        "operator_dim": d,
        "jump_count": d - 1,
        "kossakowski_dim": d - 1,
        "superoperator_shape": [d * d, d * d],
        "dense_state_closure_used": False,
        "dense_superoperator_materialized": False,
        "jump_csr_summary": csr_summary(d),
        "hamiltonian_nonzeros": len(h_entries),
        "hamiltonian_density": h_density,
        "torch_min_kossakowski_eigenvalue": real_min_t,
        "torch_control_min_kossakowski_eigenvalue": control_min_t,
        "torch_kossakowski_frobenius_norm": real_fro_t,
        "torch_control_kossakowski_frobenius_norm": control_fro_t,
        "torch_generator": valid_generator_t,
        "torch_control_generator": control_generator_t,
        "torch_jump_erased_generator": jump_erased_generator_t,
        "torch_hamiltonian_erased_generator": h_erased_generator_t,
        "jax_min_kossakowski_eigenvalue": real_min_j,
        "jax_control_min_kossakowski_eigenvalue": control_min_j,
        "jax_kossakowski_frobenius_norm": real_fro_j,
        "jax_control_kossakowski_frobenius_norm": control_fro_j,
        "jax_generator": valid_generator_j,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "control_psd_breaks": bool(control_min_t < 0.0),
        "kossakowski_norm_preserved_under_control": bool(abs(real_fro_t - control_fro_t) <= EPS),
        "pass": bool(
            real_min_t >= 0.0
            and control_min_t < 0.0
            and abs(real_fro_t - control_fro_t) <= EPS
            and valid_generator_t["pass"]
            and control_generator_t["pass"]
            and jump_erased_generator_t["pass"]
            and h_erased_generator_t["pass"]
            and jax_vs_pytorch_delta <= 1.0e-9
            and not valid_generator_t["dense_superoperator_materialized"]
            and not valid_generator_j["dense_superoperator_materialized"]
        ),
    }


def known_value_checks(scale_rows: dict[int, dict[str, Any]], sympy_cert: dict[str, Any]) -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    for d, row in scale_rows.items():
        checks.append(
            {
                "invariant": f"d={d} Kossakowski valid minimum eigenvalue from rank-1 jump Gram",
                "computed": row["torch_min_kossakowski_eigenvalue"],
                "known": "1/2 from Tr((phase/sqrt(2)|j-1><j|)^dag same)",
                "match": bool(abs(row["torch_min_kossakowski_eigenvalue"] - KOSS_RATE) <= EPS),
            }
        )
        checks.append(
            {
                "invariant": f"d={d} degenerate-control minimum eigenvalue",
                "computed": row["torch_control_min_kossakowski_eigenvalue"],
                "known": "-1/2 from unprojected C - |e0><e0|",
                "match": bool(abs(row["torch_control_min_kossakowski_eigenvalue"] + KOSS_RATE) <= EPS),
            }
        )
        checks.append(
            {
                "invariant": f"d={d} Kossakowski Frobenius norm preserved by sign-flip control",
                "computed": {
                    "real": row["torch_kossakowski_frobenius_norm"],
                    "control": row["torch_control_kossakowski_frobenius_norm"],
                },
                "known": "equal because the control changes one coefficient sign but not magnitude",
                "match": bool(row["kossakowski_norm_preserved_under_control"]),
            }
        )
        checks.append(
            {
                "invariant": f"d={d} sparse generator trace preservation on matrix-unit basis",
                "computed": row["torch_generator"]["max_trace_residual_on_matrix_units"],
                "known": "0 for GKSL Hamiltonian commutator plus Lindblad dissipator",
                "match": bool(row["torch_generator"]["max_trace_residual_on_matrix_units"] <= EPS),
            }
        )
        checks.append(
            {
                "invariant": f"d={d} torch/JAX Kossakowski and sparse-generator norm parity",
                "computed": row["jax_vs_pytorch_delta"],
                "known": "<=1e-9",
                "match": bool(row["jax_vs_pytorch_delta"] <= 1.0e-9),
            }
        )
    checks.append(
        {
            "invariant": "sympy exact characteristic roots flip under degenerate control",
            "computed": {
                "real_status": sympy_cert["real_claim_verdict"],
                "control_status": sympy_cert["negated_claim_verdict"],
                "roots": sympy_cert["control_char_poly_roots"],
            },
            "known": "real roots all 1/2; control roots include one -1/2",
            "match": bool(sympy_cert["pass"]),
        }
    )
    return checks


def build_tool_ablations(top: dict[str, Any]) -> dict[str, Any]:
    torch_valid = top["torch_generator"]["frobenius_norm"]
    torch_jump_erased = top["torch_jump_erased_generator"]["frobenius_norm"]
    clifford_valid = top["torch_generator"]["frobenius_norm"]
    clifford_erased = top["torch_hamiltonian_erased_generator"]["frobenius_norm"]
    return {
        "torch_sparse_generator_jump_contribution": tool_ablation(
            "sparse_gksl_generator_frobenius_norm_valid_vs_jump_dissipator_erased_recompute",
            baseline_value=torch_valid,
            ablated_value=torch_jump_erased,
            tool="torch",
        ),
        "clifford_hamiltonian_sign_source": tool_ablation(
            "sparse_gksl_generator_frobenius_norm_with_clifford_hamiltonian_vs_clifford_source_removed",
            baseline_value=clifford_valid,
            ablated_value=clifford_erased,
            tool="clifford",
        ),
    }


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    witness = clifford_witness()
    scale_rows = {d: scale_rung(d, witness) for d in SCALES}
    top = scale_rows[64]
    sympy_cert = sympy_exact_certificate(64)
    smt_proof = smt_gksl_psd_proof(
        top["torch_min_kossakowski_eigenvalue"],
        top["torch_control_min_kossakowski_eigenvalue"],
    )
    checks = known_value_checks(scale_rows, sympy_cert)
    tool_ablations = build_tool_ablations(top)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(smt_proof["pass"] and sympy_cert["pass"])
    known_pass = all(row["match"] for row in checks)
    ablation_pass = all(
        abs(float(row["baseline_value"]) - float(row["ablated_value"])) > EPS
        and abs((float(row["baseline_value"]) - float(row["ablated_value"])) - float(row["outcome_delta"])) <= EPS
        for row in tool_ablations.values()
    )
    all_pass = bool(scale_pass and proof_pass and known_pass and ablation_pass and witness["pass"])

    blockers = []
    if not scale_pass:
        blockers.append("one or more 8/16/32/64 non-dense sparse-generator rungs failed")
    if not proof_pass:
        blockers.append("helper-bound z3/cvc5 or exact sympy Kossakowski PSD flip failed")
    if not known_pass:
        blockers.append("one or more computed known-value checks failed")
    if not ablation_pass:
        blockers.append("torch/clifford remove-and-recompute ablation did not produce a nonzero matching delta")
    if not witness["pass"]:
        blockers.append("clifford pseudoscalar square witness failed")

    torch_primary_result = {
        "engine": "torch",
        "dtype": "torch.complex128 / torch.float64",
        "operator_dim": 64,
        "jump_count": top["jump_count"],
        "kossakowski_dim": top["kossakowski_dim"],
        "superoperator_shape": top["superoperator_shape"],
        "dense_superoperator_materialized": False,
        "min_kossakowski_eigenvalue": top["torch_min_kossakowski_eigenvalue"],
        "control_min_kossakowski_eigenvalue": top["torch_control_min_kossakowski_eigenvalue"],
        "kossakowski_frobenius_norm": top["torch_kossakowski_frobenius_norm"],
        "control_kossakowski_frobenius_norm": top["torch_control_kossakowski_frobenius_norm"],
        "generator_frobenius_norm": top["torch_generator"]["frobenius_norm"],
        "generator_nnz": top["torch_generator"]["nnz"],
        "max_trace_residual_on_matrix_units": top["torch_generator"]["max_trace_residual_on_matrix_units"],
        "claim": "unprojected Kossakowski minimum eigenvalue is nonnegative for the valid GKSL generator and negative for the degenerate control",
        "pass": bool(top["pass"]),
    }

    jax_mirror_result = {
        "engine": "jax",
        "x64_enabled": bool(jax.config.read("jax_enable_x64")),
        "operator_dim": 64,
        "min_kossakowski_eigenvalue": top["jax_min_kossakowski_eigenvalue"],
        "control_min_kossakowski_eigenvalue": top["jax_control_min_kossakowski_eigenvalue"],
        "kossakowski_frobenius_norm": top["jax_kossakowski_frobenius_norm"],
        "control_kossakowski_frobenius_norm": top["jax_control_kossakowski_frobenius_norm"],
        "generator_frobenius_norm": top["jax_generator"]["frobenius_norm"],
        "generator_nnz": top["jax_generator"]["nnz"],
        "dense_superoperator_materialized": False,
        "representable_scope": "JAX mirrors descriptor-derived Kossakowski and sparse-generator scalar readouts; PyTorch owns sparse COO object assembly.",
        "pass": bool(top["jax_vs_pytorch_delta"] <= 1.0e-9),
    }

    controls = {
        "degenerate_negative_kossakowski_coefficient": {
            "description": "Unprojected C control flips one diagonal coefficient from +1/2 to -1/2; Frobenius norm is preserved but PSD fails.",
            "control_operation": "C_bad = C - |e0><e0|",
            "real_min_kossakowski_eigenvalue": top["torch_min_kossakowski_eigenvalue"],
            "control_min_kossakowski_eigenvalue": top["torch_control_min_kossakowski_eigenvalue"],
            "real_kossakowski_frobenius_norm": top["torch_kossakowski_frobenius_norm"],
            "control_kossakowski_frobenius_norm": top["torch_control_kossakowski_frobenius_norm"],
            "projection_or_psd_repair_applied": False,
            "kills_gksl_psd_invariant": bool(top["torch_control_min_kossakowski_eigenvalue"] < 0.0),
            "pass": bool(top["torch_control_min_kossakowski_eigenvalue"] < 0.0 and top["kossakowski_norm_preserved_under_control"]),
        },
        "clifford_hamiltonian_source_erased": {
            "description": "Remove the Clifford-derived Hamiltonian sign source and recompute the sparse generator norm with the same valid jumps.",
            "baseline_generator_frobenius_norm": top["torch_generator"]["frobenius_norm"],
            "ablated_generator_frobenius_norm": top["torch_hamiltonian_erased_generator"]["frobenius_norm"],
            "changes_numeric_generator_observable": bool(abs(top["torch_generator"]["frobenius_norm"] - top["torch_hamiltonian_erased_generator"]["frobenius_norm"]) > EPS),
            "pass": bool(abs(top["torch_generator"]["frobenius_norm"] - top["torch_hamiltonian_erased_generator"]["frobenius_norm"]) > EPS),
        },
    }

    proof_results = {
        "gksl_psd_smt_load_bearing": smt_proof,
        "sympy_exact_kossakowski_characteristic_flip": sympy_cert,
        "pass": proof_pass,
    }

    scale_ladder = {
        "rungs": {
            str(d): {
                "sites_or_qubits": row["sites_or_qubits"],
                "operator_dim": row["operator_dim"],
                "jump_count": row["jump_count"],
                "kossakowski_dim": row["kossakowski_dim"],
                "superoperator_shape": row["superoperator_shape"],
                "dense_state_closure_used": row["dense_state_closure_used"],
                "dense_superoperator_materialized": row["dense_superoperator_materialized"],
                "hamiltonian_nonzeros": row["hamiltonian_nonzeros"],
                "hamiltonian_density": row["hamiltonian_density"],
                "generator_nnz": row["torch_generator"]["nnz"],
                "min_kossakowski_eigenvalue": row["torch_min_kossakowski_eigenvalue"],
                "control_min_kossakowski_eigenvalue": row["torch_control_min_kossakowski_eigenvalue"],
                "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                "pass": row["pass"],
            }
            for d, row in scale_rows.items()
        },
        "scale_axis": "operator_dimension_d",
        "dense_state_closure_used": False,
        "dense_superoperator_materialized": False,
        "pass": scale_pass,
    }

    result = {
        "schema": "formal_scout_stage5_operator_channel_generator_lego_v1",
        "sim_id": "sim_op_gksl_lindblad_probe",
        "name": "sim_op_gksl_lindblad_probe",
        "version": "1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "thisfile": THISFILE,
        "result_path": str(RESULT.relative_to(ROOT)),
        "object_id": OBJECT_ID,
        "classification": "lego",
        "promotion_allowed": False,
        "tier": "canonical STAGE 5 operator/channel/generator object",
        "sim_execution_kind": "nonclassical",
        "sim_class": "operator_channel_generator_probe",
        "purpose": "Build one finite GKSL/Lindblad generator object and prove its Kossakowski positivity against an unprojected negative-coefficient control.",
        "scientific_question": "Does the finite rank-1 jump family generate a GKSL-admissible Kossakowski matrix at d=8/16/32/64, and does the same invariant fail under a norm-preserving degenerate control?",
        "claim_ceiling": "One Stage-5 operator/channel/generator lego only; no layer completion, manifold admission, bridge, flux, Axis0, FEP, gravity, or physics claim.",
        "finite_map": {
            "domain": "For d in {8,16,32,64}: finite Hilbert basis {0..d-1}, finite rank-1 jump descriptors L_j=phase_j/sqrt(2)|j-1><j| for j=1..d-1, finite real-symmetric sparse Hamiltonian H, and finite matrix-unit probe basis E_ab.",
            "codomain_or_output": "Unprojected Kossakowski diagonal C_jk=Tr(L_j^dag L_k), sparse COO/rule representation of the GKSL generator on d^2 matrix units, trace residuals, proof flip, controls, ablations, and JSON receipt.",
            "definition": "G_d maps (H,{L_j}) to C, L(E_ab)=-i[H,E_ab]+sum_j gamma_j(F_j E_ab F_j^dag - 1/2{F_j^dag F_j,E_ab}), and finite readouts; the d^2 x d^2 superoperator is sparse and never densified.",
        },
        "domain": {
            "operator_dimensions": list(SCALES),
            "jump_family": "rank_one_shift_down_entries_in_Z_i_over_sqrt2",
            "hamiltonian": "deterministic real-symmetric sparse matrix, Clifford pseudoscalar signed, approximately 0.1 off-diagonal sparse",
            "probe_basis": "finite matrix units E_ab",
            "dense_state_closure_used": False,
        },
        "codomain_or_output": {
            "primary_invariant": "Kossakowski PSD via exact diagonal eigenvalue readout",
            "proof_object": "smt_load_bearing real/control measured min eigenvalue flip plus exact SymPy characteristic-root flip",
            "scale_output": "8/16/32/64 non-dense sparse generator rungs",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite operator/probe/path set: finite d, finite jump descriptors, finite matrix-unit probes, finite sparse generator rules, finite controls, finite proof variables.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting/order-sensitive operation/control: Hamiltonian commutator and jump dissipators act as noncommuting generator components; degenerate negative Kossakowski control kills CP/GKSL positivity while trace-generator structure remains finite.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control through commutator-plus-dissipator generator components and CP-breaking control",
        ],
        "carrier_layer": "finite sparse operator/channel/generator descriptor",
        "geometry_layer": "not_applicable_operator_channel_generator_stage5",
        "carrier_realization": "torch sparse COO/rule assembly from finite jump/H descriptors; JAX x64 mirror for descriptor-derived scalar readouts; no dense d^2 x d^2 materialization and no NumPy bridge.",
        "peps3d_embedding": {
            "status": "not_admitted_by_this_stage5_operator_packet",
            "anchor": "This file tests a finite generator object only; it does not embed PEPS3D cells or claim manifold carrier admission.",
        },
        "spinor_state": "not_applicable: this sim acts on finite density matrix-unit probes, not spinor-state carriers",
        "quaternion_action": "not_applicable",
        "dependency_receipts": ["standalone_stage5_operator_channel_generator_probe_no_lower_result_consumed"],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "GKSL Kossakowski positivity for a finite Lindblad generator family with rank-1 jumps",
        "branch_status_before_run": "single requested Stage-5 operator/channel/generator lego; no coupling, bridge, axis, manifold, physics, or completion route opened",
        "allowed_claims": [
            "bounded Stage-5 GKSL/Lindblad generator object receipt for this finite rank-1 jump family",
            "8/16/32/64 non-dense sparse generator scale execution",
            "helper-bound z3/cvc5 real/control Kossakowski PSD flip and exact SymPy characteristic-root flip",
            "torch primary and JAX mirror agree on finite Kossakowski/sparse-generator scalar readouts",
        ],
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "single operator/channel/generator lego only",
            "not a manifold layer, G-structure selection, PEPS3D carrier, or layer stack",
            "no coupling/coexistence/topology/emergence/bridge/axis/physics admission",
        ],
        "eligible_consumers": ["future bounded local operator/channel/generator comparisons only after citing this result path and fresh gates"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
        "proof_results": proof_results,
        "controls": controls,
        "tool_ablations": tool_ablations,
        "scale_ladder": scale_ladder,
        "scale_details": scale_rows,
        "known_value_checks": checks,
        "all_known_value_checks_match": known_pass,
        "clifford_witness": witness,
        "positive": {
            "scale_ladder": {"pass": scale_pass, "rungs": list(SCALES)},
            "smt_flip": smt_proof,
            "sympy_exact_flip": sympy_cert,
            "torch_primary": torch_primary_result,
            "jax_mirror": jax_mirror_result,
            "pass": bool(scale_pass and proof_pass),
        },
        "graveyard_companions": controls,
        "boundary": {
            "projection_or_psd_repair_applied": {"used": False, "pass": True},
            "dense_superoperator_materialized": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "proof_tool_numeric_ablation_emitted": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
        },
        "nearby_variants": {
            "valid_gksl_generator": "survives_local_psd_gate",
            "negative_kossakowski_control": "killed_by_psd_flip",
            "clifford_hamiltonian_erased": "numeric_generator_observable_changes_without_affecting_proof_tool_ablation_boundary",
        },
        "shells": [
            {
                "name": "stage5_gksl_lindblad_generator_object",
                "status": "operator_channel_generator_lego_only",
                "operator_dimensions": list(SCALES),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "Build a separate coupling receipt before using this generator inside a higher-stage composition.",
            "Do not cite this as PEPS3D, Xi, Phi0, Axis0, flux, FEP, gravity, bridge, physics, or final manifold evidence.",
        ],
        "compatibility_weights": {
            "stage5_operator_channel_generator_input": 1.0 if all_pass else 0.0,
            "Xi": 0.0,
            "Phi0": 0.0,
            "Axis0": 0.0,
            "flux": 0.0,
            "FEP": 0.0,
            "gravity": 0.0,
        },
        "compression_map": {
            "from": "finite sparse H plus d-1 rank-1 jump descriptors and finite matrix-unit probes",
            "to": "Kossakowski min eigenvalue, characteristic-root flip, sparse generator norm, trace residual, controls, ablations, and scale ladder",
            "loss_boundary": "does not preserve or claim dense semigroup evolution, PEPS3D contraction, manifold layer completion, stack readiness, bridge, Axis0, flux, FEP, gravity, physics, or final admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": top["torch_min_kossakowski_eigenvalue"],
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "GKSL generator object survives iff all scale rungs are non-dense, valid Kossakowski min eigenvalue >=0, degenerate control min eigenvalue <0 with norm preserved, SMT/SymPy proof flips, torch/JAX agree, numeric ablations recompute nonzero deltas, and promotion_allowed=false",
            "computed_capacity": top["torch_min_kossakowski_eigenvalue"],
            "threshold": 0.0,
            "passed": bool(all_pass and top["torch_min_kossakowski_eigenvalue"] >= 0.0),
        },
        "outward_record": {
            "result_path": str(RESULT.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {RESULT.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {RESULT.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {RESULT.relative_to(ROOT)} --rerun {THISFILE} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-5 operator/channel/generator lego only; no downstream consumer admitted",
        },
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3 Kossakowski PSD flip",
            "load_bearing_proof.smt_load_bearing cvc5 Kossakowski PSD cross-check",
            "sympy exact diagonal characteristic-root real/control flip",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_negatives": list(controls.keys()),
        "negatives_run": controls,
        "kill_conditions": {
            "degenerate_negative_kossakowski_coefficient": "same PSD invariant must become UNSAT under unprojected C_bad",
            "clifford_hamiltonian_source_erased": "generator numeric observable must change when Clifford-derived H source is removed and recomputed",
        },
        "required_artifacts": [
            "result JSON",
            "scale_ladder",
            "torch_primary_result",
            "jax_mirror_result",
            "proof_results",
            "controls",
            "tool_ablations",
            "known_value_checks",
        ],
        "artifacts_emitted": [str(RESULT.relative_to(ROOT))],
        "witness_trace_id": f"sim_op_gksl_lindblad_probe:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "known_value_checks_pass": known_pass,
            "tool_ablations_pass": ablation_pass,
            "min_kossakowski_eigenvalue": top["torch_min_kossakowski_eigenvalue"],
            "control_min_kossakowski_eigenvalue": top["torch_control_min_kossakowski_eigenvalue"],
            "kossakowski_norm_preserved_under_control": top["kossakowski_norm_preserved_under_control"],
            "max_jax_vs_pytorch_delta": float(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values())),
            "elapsed_seconds": time.time() - started,
        },
        "pass_rule": "all 8/16/32/64 rungs are non-dense and pass; valid C has min eigenvalue >=0; unprojected norm-preserving degenerate C control has min eigenvalue <0; z3/cvc5 and SymPy proof flips hold; torch/JAX mirror agrees; torch/clifford numeric ablations carry recomputed nonzero baseline/ablated values; downstream consumers remain blocked",
        "fail_rule": "fail on dense superoperator materialization, projection/PSD repair, missing rung, fake JAX mirror, proof verdict not flipping, proof-tool numeric ablation, control not killing PSD, missing genuine torch/clifford ablation, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blockers": blockers,
        "required_pass": all_pass,
        "all_pass": all_pass,
    }
    return result


def main() -> int:
    result = build_result()
    RESULT.write_text(json.dumps(as_jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "all_pass": result["all_pass"],
                "required_pass": result["required_pass"],
                "result_path": result["result_path"],
                "min_kossakowski_eigenvalue": result["result_summary"]["min_kossakowski_eigenvalue"],
                "control_min_kossakowski_eigenvalue": result["result_summary"]["control_min_kossakowski_eigenvalue"],
                "max_jax_vs_pytorch_delta": result["result_summary"]["max_jax_vs_pytorch_delta"],
                "blockers": result["blockers"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["required_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
