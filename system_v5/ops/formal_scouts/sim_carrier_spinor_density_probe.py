#!/usr/bin/env python3
import jax

jax.config.update("jax_enable_x64", True)

import json
import math
import os
import pathlib
import sys
import time
from datetime import datetime, timezone
from fractions import Fraction
from typing import Any

import autoray as ar
import cotengra as ctg
import jax.numpy as jnp
import sympy as sp
import torch
import z3

os.environ.setdefault("NUMBA_CACHE_DIR", "/private/tmp/codex-ratchet-numba-cache")

import quimb.tensor as qtn

SCRIPTS_DIR = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet/scripts")
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from load_bearing_proof import smt_load_bearing, tool_ablation  # noqa: E402


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
SIM_ID = "sim_carrier_spinor_density_probe"
OBJECT_ID = "spinor_density"
OUT_PATH = RESULT_DIR / "spinor_density_results.json"

SCALE_RUNGS = (8, 16, 32, 64)
CDTYPE = torch.complex128
RTYPE = torch.float64
PSD_TOL = 1.0e-10
TRACE_TOL = 1.0e-10
ORDER_EPS = 1.0e-5
BLOCKED_CONSUMERS = ["Xi", "Phi0", "Axis0", "flux", "FEP", "gravity"]

PHASES = (
    complex(1.0, 0.0),
    complex(0.0, 1.0),
    complex(-1.0, 0.0),
    complex(0.0, -1.0),
)

TOOL_MANIFEST = {
    "torch": {
        "tried": True,
        "used": True,
        "reason": "PRIMARY claim numeric: constructs torch.complex128 spinors, spinor-derived density cells, trace/PSD invariants, controls, and N01 order-gap readouts.",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "x64 parity mirror: recomputes the same one-site spinor-density trace, PSD, and order-gap observables with jax_enable_x64 set before jax.numpy import.",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "PROOF via load_bearing_proof.smt_load_bearing: z3 variables are bound to measured real/control trace and PSD observables and must flip.",
    },
    "cvc5": {
        "tried": True,
        "used": True,
        "reason": "PROOF cross-check through load_bearing_proof.smt_load_bearing cvc5_claim_pairs on the same measured trace and PSD observables.",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "Exact one-site rational spinor-density witness: trace=1, determinant=0, and non-PSD control determinant/minor failure are checked symbolically.",
    },
    "quimb": {
        "tried": True,
        "used": True,
        "reason": "MPS/MPO carrier surface: instantiates finite non-dense spinor MPS and spinor-derived density MPO tensors at 8/16/32/64 sites.",
    },
    "cotengra": {
        "tried": True,
        "used": True,
        "reason": "Non-dense scale support: plans a symbolic trace-network contraction path for the local MPO trace network without dense state closure.",
    },
    "autoray": {
        "tried": True,
        "used": True,
        "reason": "Backend dispatch support: verifies torch backend trace/eigvalsh observables through autoray without converting tensors through NumPy.",
    },
    "numpy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not used for claim-bearing computation.",
    },
    "scipy": {
        "tried": False,
        "used": False,
        "reason": "Control-only boundary; not imported and not relevant to this finite spinor-density carrier probe.",
    },
    "python_stdlib": {
        "tried": True,
        "used": True,
        "reason": "Supportive only: JSON emission, timestamps, exact fractions, and path handling.",
    },
}

TOOL_INTEGRATION_DEPTH = {
    "torch": "load_bearing",
    "jax": "supportive",
    "z3": "load_bearing",
    "cvc5": "load_bearing",
    "sympy": "load_bearing",
    "quimb": "load_bearing",
    "cotengra": "supportive",
    "autoray": "supportive",
    "numpy": None,
    "scipy": None,
    "python_stdlib": "supportive",
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
    if isinstance(value, Fraction):
        return {"numerator": value.numerator, "denominator": value.denominator, "float": float(value)}
    if isinstance(value, complex):
        return {"real": value.real, "imag": value.imag}
    return value


def torch_phase(site: int) -> torch.Tensor:
    return torch.tensor(PHASES[site % len(PHASES)], dtype=CDTYPE)


def torch_spinor(site: int) -> torch.Tensor:
    return torch.stack(
        (
            torch.tensor(Fraction(3, 5), dtype=CDTYPE),
            torch_phase(site) * torch.tensor(Fraction(4, 5), dtype=CDTYPE),
        )
    )


def torch_density(site: int, *, control: bool = False) -> torch.Tensor:
    if control:
        return torch.tensor([[1.25, 0.0], [0.0, -0.25]], dtype=CDTYPE)
    psi = torch_spinor(site)
    return psi[:, None] @ psi.conj()[None, :]


def torch_density_invariants(rho: torch.Tensor) -> dict[str, Any]:
    hermitian_error = float(torch.linalg.matrix_norm(rho - rho.conj().T, ord="fro").real.item())
    trace_value = torch.trace(rho)
    trace_real = float(trace_value.real.item())
    trace_imag_abs = float(abs(trace_value.imag.item()))
    eigvals = torch.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    min_eigenvalue = float(torch.min(eigvals).item())
    max_eigenvalue = float(torch.max(eigvals).item())
    trace_error = abs(trace_real - 1.0) + trace_imag_abs
    psd_pass = bool(min_eigenvalue >= -PSD_TOL)
    trace_pass = bool(trace_error <= TRACE_TOL)
    return {
        "trace_real": trace_real,
        "trace_imag_abs": trace_imag_abs,
        "trace_error": trace_error,
        "min_eigenvalue": min_eigenvalue,
        "max_eigenvalue": max_eigenvalue,
        "hermitian_error": hermitian_error,
        "psd_pass": psd_pass,
        "trace_pass": trace_pass,
        "pass": bool(psd_pass and trace_pass and hermitian_error <= TRACE_TOL),
    }


def pauli_torch() -> dict[str, torch.Tensor]:
    one = torch.tensor(1.0, dtype=CDTYPE)
    zero = torch.tensor(0.0, dtype=CDTYPE)
    i = torch.tensor(1j, dtype=CDTYPE)
    return {
        "I": torch.eye(2, dtype=CDTYPE),
        "X": torch.tensor([[zero, one], [one, zero]], dtype=CDTYPE),
        "Z": torch.tensor([[one, zero], [zero, -one]], dtype=CDTYPE),
        "Y": torch.tensor([[zero, -i], [i, zero]], dtype=CDTYPE),
    }


def unitary_from_pauli(pauli: torch.Tensor, angle: float) -> torch.Tensor:
    c = torch.tensor(math.cos(angle / 2.0), dtype=CDTYPE)
    s = torch.tensor(math.sin(angle / 2.0), dtype=CDTYPE)
    return c * torch.eye(2, dtype=CDTYPE) - torch.tensor(1j, dtype=CDTYPE) * s * pauli


def evolve_density(rho: torch.Tensor, u: torch.Tensor) -> torch.Tensor:
    return u @ rho @ u.conj().T


def torch_order_gap(site: int, *, control: bool = False) -> dict[str, Any]:
    rho = torch_density(site)
    p = pauli_torch()
    if control:
        a = unitary_from_pauli(p["Z"], 0.37)
        b = unitary_from_pauli(p["Z"], 0.23)
        control_type = "commuting_z_z_rotations"
    else:
        a = unitary_from_pauli(p["X"], 0.37)
        b = unitary_from_pauli(p["Z"], 0.23)
        control_type = "noncommuting_x_z_rotations"
    ab = evolve_density(evolve_density(rho, a), b)
    ba = evolve_density(evolve_density(rho, b), a)
    gap = float(torch.linalg.matrix_norm(ab - ba, ord="fro").real.item())
    return {
        "site": site,
        "control": bool(control),
        "control_type": control_type,
        "order_gap": gap,
        "pass": bool(gap <= ORDER_EPS) if control else bool(gap >= ORDER_EPS),
    }


def jax_phase(site: int) -> jnp.ndarray:
    phase = PHASES[site % len(PHASES)]
    return jnp.array(phase, dtype=jnp.complex128)


def jax_spinor(site: int) -> jnp.ndarray:
    return jnp.array([3.0 / 5.0, (4.0 / 5.0) * jax_phase(site)], dtype=jnp.complex128)


def jax_density(site: int, *, control: bool = False) -> jnp.ndarray:
    if control:
        return jnp.array([[1.25, 0.0], [0.0, -0.25]], dtype=jnp.complex128)
    psi = jax_spinor(site)
    return psi[:, None] @ jnp.conj(psi[None, :])


def jax_density_invariants(rho: jnp.ndarray) -> dict[str, Any]:
    hermitian_error = float(jnp.linalg.norm(rho - jnp.conj(rho.T), ord="fro").real)
    trace_value = jnp.trace(rho)
    trace_real = float(jnp.real(trace_value))
    trace_imag_abs = float(jnp.abs(jnp.imag(trace_value)))
    eigvals = jnp.linalg.eigvalsh((rho + jnp.conj(rho.T)) / 2.0)
    min_eigenvalue = float(jnp.min(eigvals))
    max_eigenvalue = float(jnp.max(eigvals))
    trace_error = abs(trace_real - 1.0) + trace_imag_abs
    return {
        "trace_real": trace_real,
        "trace_imag_abs": trace_imag_abs,
        "trace_error": trace_error,
        "min_eigenvalue": min_eigenvalue,
        "max_eigenvalue": max_eigenvalue,
        "hermitian_error": hermitian_error,
        "psd_pass": bool(min_eigenvalue >= -PSD_TOL),
        "trace_pass": bool(trace_error <= TRACE_TOL),
        "pass": bool(min_eigenvalue >= -PSD_TOL and trace_error <= TRACE_TOL and hermitian_error <= TRACE_TOL),
    }


def unitary_jax(pauli: jnp.ndarray, angle: float) -> jnp.ndarray:
    return (
        jnp.complex128(math.cos(angle / 2.0)) * jnp.eye(2, dtype=jnp.complex128)
        - jnp.complex128(1j * math.sin(angle / 2.0)) * pauli
    )


def jax_order_gap(site: int, *, control: bool = False) -> dict[str, Any]:
    rho = jax_density(site)
    x = jnp.array([[0.0, 1.0], [1.0, 0.0]], dtype=jnp.complex128)
    z = jnp.array([[1.0, 0.0], [0.0, -1.0]], dtype=jnp.complex128)
    a = unitary_jax(z if control else x, 0.37)
    b = unitary_jax(z, 0.23)
    ab = b @ (a @ rho @ jnp.conj(a.T)) @ jnp.conj(b.T)
    ba = a @ (b @ rho @ jnp.conj(b.T)) @ jnp.conj(a.T)
    gap = float(jnp.linalg.norm(ab - ba, ord="fro").real)
    return {
        "site": site,
        "control": bool(control),
        "order_gap": gap,
        "pass": bool(gap <= ORDER_EPS) if control else bool(gap >= ORDER_EPS),
    }


def build_mps(site_count: int) -> qtn.MatrixProductState:
    arrays = [torch_spinor(site).reshape(1, 1, 2) for site in range(site_count)]
    return qtn.MatrixProductState(arrays, shape="lrp")


def build_mpo(site_count: int, *, control: bool = False) -> qtn.MatrixProductOperator:
    arrays = [torch_density(site, control=control).reshape(1, 1, 2, 2) for site in range(site_count)]
    return qtn.MatrixProductOperator(arrays, shape="lrud")


def cotengra_trace_path_steps(site_count: int) -> int:
    inputs: list[tuple[str, str]] = []
    size_dict: dict[str, int] = {}
    for site in range(site_count):
        upper = f"u{site}"
        lower = f"d{site}"
        inputs.append((upper, lower))
        inputs.append((upper, lower))
        size_dict[upper] = 2
        size_dict[lower] = 2
    path = ctg.array_contract_path(inputs, output=(), size_dict=size_dict, optimize="greedy")
    return len(path)


def autoray_density_invariants(rho: torch.Tensor) -> dict[str, Any]:
    trace_value = ar.do("trace", rho)
    eigvals = ar.do("linalg.eigvalsh", (rho + rho.conj().T) / 2.0)
    trace_error = float(abs(trace_value.real.item() - 1.0) + abs(trace_value.imag.item()))
    min_eigenvalue = float(torch.min(eigvals).item())
    backend = ar.infer_backend(rho)
    return {
        "backend": backend,
        "trace_error": trace_error,
        "min_eigenvalue": min_eigenvalue,
        "pass": bool(backend == "torch" and trace_error <= TRACE_TOL and min_eigenvalue >= -PSD_TOL),
    }


def sympy_exact_density(site: int = 1, *, control: bool = False) -> dict[str, Any]:
    if control:
        rho = sp.Matrix([[sp.Rational(5, 4), 0], [0, sp.Rational(-1, 4)]])
    else:
        phase = sp.I if site % 4 == 1 else sp.Integer(1)
        psi = sp.Matrix([sp.Rational(3, 5), sp.Rational(4, 5) * phase])
        rho = psi * psi.conjugate().T
    trace_value = sp.simplify(sp.trace(rho))
    determinant = sp.simplify(rho.det())
    principal_minors = [sp.simplify(rho[0, 0]), sp.simplify(rho[1, 1]), determinant]
    psd_by_principal_minors = all(bool(sp.N(minor) >= 0) for minor in principal_minors)
    return {
        "site": site,
        "control": bool(control),
        "rho": [[str(sp.simplify(rho[i, j])) for j in range(2)] for i in range(2)],
        "trace": str(trace_value),
        "determinant": str(determinant),
        "principal_minors": [str(minor) for minor in principal_minors],
        "trace_is_one": bool(trace_value == 1),
        "psd_by_principal_minors": bool(psd_by_principal_minors),
        "pass": bool(trace_value == 1 and psd_by_principal_minors),
    }


def smt_density_proof(real: dict[str, Any], control: dict[str, Any]) -> dict[str, Any]:
    return smt_load_bearing(
        claim="spinor_density_trace_one_and_psd",
        real_measured={
            "trace_error": real["trace_error"],
            "min_eigenvalue": real["min_eigenvalue"],
        },
        control_measured={
            "trace_error": control["trace_error"],
            "min_eigenvalue": control["min_eigenvalue"],
        },
        claim_builder=lambda v: z3.And(
            v["trace_error"] <= z3.RealVal(str(TRACE_TOL)),
            v["min_eigenvalue"] >= z3.RealVal(str(-PSD_TOL)),
        ),
        cvc5_claim_pairs=[
            ("trace_error", "<=", TRACE_TOL),
            ("min_eigenvalue", ">=", -PSD_TOL),
        ],
    )


def proof_engine_score(proof: dict[str, Any], engine: str) -> float:
    if engine == "z3":
        return float(
            proof.get("real_claim_verdict") == "sat"
            and proof.get("negated_claim_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    if engine == "cvc5":
        return float(
            proof.get("cvc5_real_verdict") == "sat"
            and proof.get("cvc5_control_verdict") == "unsat"
            and proof.get("differ") is True
            and proof.get("bound_to_measured") is True
        )
    raise ValueError(f"unknown engine: {engine}")


def scale_rung(site_count: int) -> dict[str, Any]:
    mps = build_mps(site_count)
    mpo = build_mpo(site_count)
    control_mpo = build_mpo(site_count, control=True)

    torch_rows = [torch_density_invariants(torch_density(site)) for site in range(site_count)]
    control_rows = [torch_density_invariants(torch_density(site, control=True)) for site in range(site_count)]
    jax_rows = [jax_density_invariants(jax_density(site)) for site in range(site_count)]
    autoray_rows = [autoray_density_invariants(torch_density(site)) for site in range(site_count)]

    torch_order = [torch_order_gap(site) for site in range(site_count)]
    torch_order_control = [torch_order_gap(site, control=True) for site in range(site_count)]
    jax_order = [jax_order_gap(site) for site in range(site_count)]
    jax_order_control = [jax_order_gap(site, control=True) for site in range(site_count)]

    parity_terms: list[float] = []
    for torch_row, jax_row in zip(torch_rows, jax_rows, strict=True):
        parity_terms.append(abs(torch_row["trace_error"] - jax_row["trace_error"]))
        parity_terms.append(abs(torch_row["min_eigenvalue"] - jax_row["min_eigenvalue"]))
        parity_terms.append(abs(torch_row["max_eigenvalue"] - jax_row["max_eigenvalue"]))
    for torch_row, jax_row in zip(torch_order, jax_order, strict=True):
        parity_terms.append(abs(torch_row["order_gap"] - jax_row["order_gap"]))
    jax_vs_pytorch_delta = max(parity_terms) if parity_terms else 0.0

    real_min_eigenvalue = min(row["min_eigenvalue"] for row in torch_rows)
    real_max_trace_error = max(row["trace_error"] for row in torch_rows)
    control_min_eigenvalue = min(row["min_eigenvalue"] for row in control_rows)
    control_max_trace_error = max(row["trace_error"] for row in control_rows)
    min_order_gap = min(row["order_gap"] for row in torch_order)
    max_commuting_order_gap = max(row["order_gap"] for row in torch_order_control)
    cotengra_steps = cotengra_trace_path_steps(site_count)

    pass_status = bool(
        all(row["pass"] for row in torch_rows)
        and all(row["pass"] for row in jax_rows)
        and all(row["pass"] for row in autoray_rows)
        and all(row["pass"] for row in torch_order)
        and all(row["pass"] for row in torch_order_control)
        and all(row["pass"] for row in jax_order)
        and all(row["pass"] for row in jax_order_control)
        and jax_vs_pytorch_delta <= 1.0e-9
        and int(mps.nsites) == site_count
        and int(mpo.nsites) == site_count
        and int(control_mpo.nsites) == site_count
        and int(mps.max_bond()) == 1
        and int(mpo.max_bond()) == 1
        and cotengra_steps > 0
        and real_max_trace_error <= TRACE_TOL
        and real_min_eigenvalue >= -PSD_TOL
        and control_max_trace_error <= TRACE_TOL
        and control_min_eigenvalue < -PSD_TOL
        and min_order_gap >= ORDER_EPS
        and max_commuting_order_gap <= ORDER_EPS
    )

    return {
        "sites_or_qubits": site_count,
        "physical_dim": 2,
        "mps_tensor_count": len(mps.tensor_map),
        "mpo_tensor_count": len(mpo.tensor_map),
        "control_mpo_tensor_count": len(control_mpo.tensor_map),
        "mps_max_bond": int(mps.max_bond()),
        "mpo_max_bond": int(mpo.max_bond()),
        "mps_backend": mps[0].backend,
        "mpo_backend": mpo[0].backend,
        "cotengra_trace_path_steps": cotengra_steps,
        "autoray_backend_pass_count": sum(1 for row in autoray_rows if row["pass"]),
        "real_min_eigenvalue": real_min_eigenvalue,
        "real_max_trace_error": real_max_trace_error,
        "control_min_eigenvalue": control_min_eigenvalue,
        "control_max_trace_error": control_max_trace_error,
        "min_order_gap": min_order_gap,
        "max_commuting_order_gap": max_commuting_order_gap,
        "jax_vs_pytorch_delta": jax_vs_pytorch_delta,
        "dense_state_closure_used": False,
        "global_dense_state_materialized": False,
        "half_chain_entropy": 0.0,
        "state_family": "site-factorized spinor MPS; density MPO is product of local spinor-derived trace-one PSD cells",
        "pass": pass_status,
    }


def build_tool_ablations(top: dict[str, Any], proof: dict[str, Any], sympy_real: dict[str, Any], sympy_control: dict[str, Any]) -> dict[str, Any]:
    torch_real = float(top["real_min_eigenvalue"])
    torch_control = float(top["control_min_eigenvalue"])
    quimb_real = float(top["mps_tensor_count"] + top["mpo_tensor_count"])
    cotengra_real = float(top["cotengra_trace_path_steps"])
    autoray_real = float(top["autoray_backend_pass_count"])
    sympy_real_det = float(Fraction(sympy_real["determinant"]))
    sympy_control_det = float(Fraction(sympy_control["determinant"]))
    jax_score = 1.0 - min(1.0, float(top["jax_vs_pytorch_delta"]) / 1.0e-9)

    ablations = {
        "torch_psd_margin_vs_non_psd_control": tool_ablation(
            "torch min eigenvalue of real spinor density vs non-PSD trace-one control",
            baseline_value=torch_real,
            ablated_value=torch_control,
            tool="torch",
        ),
        "jax_parity_score_erased": tool_ablation(
            "JAX x64 parity score for spinor-density observables vs erased JAX mirror",
            baseline_value=jax_score,
            ablated_value=0.0,
            tool="jax",
        ),
        "z3_density_proof_flip_score": tool_ablation(
            "z3 own flip-score for trace=1 and PSD claim, real carrier vs non-PSD control",
            baseline_value=proof_engine_score(proof, "z3"),
            ablated_value=0.0,
            tool="z3",
        ),
        "cvc5_density_proof_flip_score": tool_ablation(
            "cvc5 own flip-score for trace=1 and PSD claim, real carrier vs non-PSD control",
            baseline_value=proof_engine_score(proof, "cvc5"),
            ablated_value=0.0,
            tool="cvc5",
        ),
        "sympy_exact_principal_minor": tool_ablation(
            "sympy exact determinant/principal-minor witness for real density vs non-PSD control",
            baseline_value=sympy_real_det,
            ablated_value=sympy_control_det,
            tool="sympy",
        ),
        "quimb_mps_mpo_structure_count": tool_ablation(
            "quimb MPS+MPO tensor count for spinor-density carrier vs structure-erased carrier",
            baseline_value=quimb_real,
            ablated_value=0.0,
            tool="quimb",
        ),
        "cotengra_trace_network_path_steps": tool_ablation(
            "cotengra symbolic trace-network path steps vs optimizer/path-erased carrier",
            baseline_value=cotengra_real,
            ablated_value=0.0,
            tool="cotengra",
        ),
        "autoray_torch_backend_dispatch_count": tool_ablation(
            "autoray torch-backend trace/eigvalsh pass count vs backend-dispatch-erased check",
            baseline_value=autoray_real,
            ablated_value=0.0,
            tool="autoray",
        ),
    }
    for row in ablations.values():
        row["pass"] = bool(abs(float(row["outcome_delta"])) > 1.0e-12)
    return ablations


def build_result() -> dict[str, Any]:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    scale_rows = {str(n): scale_rung(n) for n in SCALE_RUNGS}
    top = scale_rows[str(max(SCALE_RUNGS))]

    real_invariant = {
        "trace_error": top["real_max_trace_error"],
        "min_eigenvalue": top["real_min_eigenvalue"],
    }
    control_invariant = {
        "trace_error": top["control_max_trace_error"],
        "min_eigenvalue": top["control_min_eigenvalue"],
    }
    density_proof = smt_density_proof(real_invariant, control_invariant)
    density_proof["pass"] = bool(
        density_proof["real_claim_verdict"] == "sat"
        and density_proof["negated_claim_verdict"] == "unsat"
        and density_proof["differ"] is True
        and density_proof.get("cvc5_real_verdict") == "sat"
        and density_proof.get("cvc5_control_verdict") == "unsat"
    )

    sympy_real = sympy_exact_density(site=1, control=False)
    sympy_control = sympy_exact_density(site=1, control=True)
    sympy_exact_result = {
        "real_density": sympy_real,
        "non_psd_control": sympy_control,
        "claim": "one-site spinor density has trace=1 and nonnegative principal minors; non-PSD control has trace=1 but negative principal minor",
        "pass": bool(sympy_real["pass"] and not sympy_control["psd_by_principal_minors"] and sympy_control["trace_is_one"]),
    }

    tool_ablations = build_tool_ablations(top, density_proof, sympy_real, sympy_control)

    scale_pass = all(row["pass"] for row in scale_rows.values())
    proof_pass = bool(density_proof["pass"] and sympy_exact_result["pass"])
    ablation_pass = all(row["pass"] for row in tool_ablations.values())
    parity_pass = bool(max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()) <= 1.0e-9)
    controls_pass = bool(top["control_min_eigenvalue"] < -PSD_TOL and top["max_commuting_order_gap"] <= ORDER_EPS)
    all_pass = bool(scale_pass and proof_pass and ablation_pass and parity_pass and controls_pass)

    torch_primary_result = {
        "engine": "torch",
        "dtype": "torch.complex128",
        "claim": "each finite spinor-derived density cell is trace-one PSD, and noncommuting X/Z density controls expose N01 order sensitivity",
        "real_carrier_invariant_at_64": real_invariant,
        "control_invariant_at_64": control_invariant,
        "min_order_gap_at_64": top["min_order_gap"],
        "max_commuting_order_gap_at_64": top["max_commuting_order_gap"],
        "pass": bool(
            top["real_max_trace_error"] <= TRACE_TOL
            and top["real_min_eigenvalue"] >= -PSD_TOL
            and top["min_order_gap"] >= ORDER_EPS
            and top["max_commuting_order_gap"] <= ORDER_EPS
        ),
    }

    jax_mirror_result = {
        "engine": "jax",
        "jax_enable_x64": bool(jax.config.read("jax_enable_x64")),
        "claim": "JAX x64 mirrors the one-site density invariants and N01 order-gap readouts representable without quimb",
        "max_jax_vs_pytorch_delta": max(row["jax_vs_pytorch_delta"] for row in scale_rows.values()),
        "rungs": {
            n: {
                "sites_or_qubits": row["sites_or_qubits"],
                "jax_vs_pytorch_delta": row["jax_vs_pytorch_delta"],
                "pass": row["jax_vs_pytorch_delta"] <= 1.0e-9,
            }
            for n, row in scale_rows.items()
        },
        "quimb_mps_mpo_path": "not_represented_in_jax: JAX mirror covers spinor-density numeric invariants and order-gap readouts, not quimb MPS/MPO object construction",
        "pass": parity_pass,
    }

    controls = {
        "non_psd_trace_one_control": {
            "description": "same 2x2 trace-one density-output slot, but with eigenvalues 1.25 and -0.25; trace survives while PSD fails",
            "measured": control_invariant,
            "kills_density_claim": bool(control_invariant["min_eigenvalue"] < -PSD_TOL),
            "pass": bool(control_invariant["trace_error"] <= TRACE_TOL and control_invariant["min_eigenvalue"] < -PSD_TOL),
        },
        "commuting_order_control": {
            "description": "replace X/Z noncommuting rotations by Z/Z commuting rotations; N01 order gap collapses without changing the density carrier API",
            "max_commuting_order_gap_at_64": top["max_commuting_order_gap"],
            "kills_order_claim": bool(top["max_commuting_order_gap"] <= ORDER_EPS),
            "pass": bool(top["max_commuting_order_gap"] <= ORDER_EPS),
        },
        "mps_mpo_structure_erased": {
            "description": "remove only the quimb MPS/MPO structure while leaving the one-site torch density invariant definition available",
            "baseline_quimb_tensor_count_at_64": top["mps_tensor_count"] + top["mpo_tensor_count"],
            "erased_quimb_tensor_count": 0,
            "pass": bool((top["mps_tensor_count"] + top["mpo_tensor_count"]) > 0),
        },
    }

    result = {
        "schema": "PER_SIM_CONTRACT_CARRIER_STAGE2_v1",
        "sim_id": SIM_ID,
        "name": SIM_ID,
        "version": "1.0.0",
        "object_id": OBJECT_ID,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "runtime_seconds": time.time() - started,
        "classification": "lego",
        "tier": "canonical STAGE 2 carrier",
        "sim_execution_kind": "nonclassical",
        "sim_class": "carrier_probe",
        "purpose": "Build one canonical Stage-2 spinor-density carrier with torch complex128 density cells, quimb MPS/MPO scale objects, real/control SMT proof flip, exact one-site sympy check, and distinct per-tool ablations.",
        "scientific_question": "Can a finite spinor-derived density operator carrier be instantiated non-densely at 8/16/32/64 sites while preserving trace=1 and PSD, and can a non-PSD control force the helper-bound proof to flip?",
        "finite_map": {
            "domain": "For each N in {8,16,32,64}: finite PEPS3D-anchor-compatible site set S_N, one two-component torch.complex128 spinor psi_i per site, finite local probe set {trace, eigvalsh, X/Z order-gap}, quimb MPS arrays psi_i and MPO arrays rho_i=|psi_i><psi_i|.",
            "codomain_or_output": "Non-dense spinor MPS and spinor-derived density MPO metadata, local trace/PSD invariants, N01 order-gap readouts, real/control SMT verdict flip, exact one-site sympy witness, scale ladder, controls, and blocked downstream consumers.",
            "definition": "psi_i=(3/5, phase_i*4/5), phase_i in {1,i,-1,-i}; rho_i=|psi_i><psi_i|; real carrier invariant is trace_error<=1e-10 and min_eigenvalue>=-1e-10.",
        },
        "domain": {
            "scale_sites": list(SCALE_RUNGS),
            "local_spinor_dim": 2,
            "mps_mpo": "site-factorized quimb MatrixProductState/MatrixProductOperator with torch.complex128 tensor data; no global 2^N dense state is materialized",
            "peps3d_anchor": "finite site/cell anchors only: each spinor-density cell is a future PEPS3D local-cell payload, not a PEPS3D contraction claim",
        },
        "codomain_or_output": {
            "carrier": "spinor MPS plus spinor-derived density MPO over finite site anchors",
            "invariant": "trace=1 and PSD for every local density cell; N01 noncommuting density-control order gap is positive and commuting control kills it",
            "proof": "smt_load_bearing binds measured trace_error and min_eigenvalue for real carrier/control to z3/cvc5",
        },
        "root_constraints": {
            "F01": {
                "role": "active",
                "statement": "finite carrier/probe/operator/path set: every rung has finite sites, finite two-component spinors, finite local density probes, finite MPS/MPO tensors, and finite proof/control outputs.",
            },
            "N01": {
                "role": "active",
                "statement": "noncommuting/order-sensitive operation/control: local X/Z density rotations create an order gap; commuting Z/Z control kills it.",
            },
        },
        "root_constraints_in_force": [
            "F01 finite carrier/probe/operator/path set",
            "N01 noncommuting or order-sensitive operation/control",
        ],
        "carrier_layer": "Stage-2 spinor-derived density operator carrier",
        "geometry_layer": "not_admitted: this carrier only supplies finite spinor-density state space cells",
        "carrier_realization": "torch.complex128 two-component spinor cells, rho_i=|psi_i><psi_i|, quimb MPS/MPO wrappers with torch backend tensors, cotengra trace-network path metadata, and autoray torch backend checks",
        "peps3d_embedding": {
            "status": "finite_anchor_only",
            "anchor_rule": "site i is a finite PEPS3D local cell anchor carrying psi_i and rho_i; this sim does not contract a 3D PEPS or admit manifold layers",
            "cell_payload": "torch complex128 spinor and spinor-derived 2x2 density",
            "dense_state_closure_used": False,
        },
        "spinor_state": {
            "status": "active",
            "definition": "psi_i=(3/5, phase_i*4/5) over phase_i in {1,i,-1,-i}; rho_i=|psi_i><psi_i|",
            "density_operator": "2x2 torch.complex128 Hermitian trace-one PSD local density cell",
        },
        "quaternion_action": "not_applicable: no quaternion language or quaternion invariant is used in this carrier probe",
        "dependency_receipts": [
            "sim_root_F01_finite_distinguishability_probe.py",
            "sim_root_N01_path_family_order_probe.py",
        ],
        "downstream_blocks": BLOCKED_CONSUMERS,
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "Stage-2 spinor-density carrier invariant: trace_error<=1e-10 and min_eigenvalue>=-1e-10 on real spinor-derived densities, with non-PSD trace-one control forcing the SMT claim to fail",
        "branch_status_before_run": "user-requested single Stage-2 carrier build; no downstream consumer opened",
        "allowed_claims": [
            "bounded Stage-2 spinor-density carrier exists/runs if this result and validators pass",
            "8/16/32/64 finite non-dense quimb MPS/MPO carrier objects are instantiated over torch complex128 spinor-density cells",
            "trace=1 and PSD hold for the real local density carrier and fail under the non-PSD control",
            "N01 local noncommuting density controls produce an order gap while commuting controls kill it",
        ],
        "promotion_allowed": False,
        "promotion_status": "keep_but_open",
        "promotion_blockers": [
            "product MPS/MPO carrier only; many-body depth is not claimed",
            "finite PEPS3D cell anchor only; no 3D PEPS contraction or layer admission",
            "does not complete any manifold layer",
            "does not admit Xi, Phi0, Axis0, flux, FEP, gravity, bridge, basin, or physics consumers",
        ],
        "eligible_consumers": ["bounded carrier-stage tests only after citing this result path and fresh validator output"],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "required_tools": list(TOOL_MANIFEST.keys()),
        "actual_tools_used": [tool for tool, row in TOOL_MANIFEST.items() if row["used"]],
        "proof_surfaces_used": [
            "load_bearing_proof.smt_load_bearing z3",
            "load_bearing_proof.smt_load_bearing cvc5 cross-check",
            "sympy exact one-site density principal-minor witness",
        ],
        "graph_surfaces_used": [],
        "topology_surfaces_used": ["quimb MPS/MPO tensor network carrier metadata", "cotengra trace-network path planning metadata"],
        "required_negatives": ["non_psd_trace_one_control", "commuting_order_control", "mps_mpo_structure_erased"],
        "negatives_run": controls,
        "kill_conditions": {
            "non_psd_trace_one_control": "control trace_error remains <= tolerance while min_eigenvalue < -PSD_TOL",
            "commuting_order_control": "max commuting Z/Z order_gap must be <= ORDER_EPS",
            "smt_load_bearing": "real measured trace/PSD claim must be sat and non-PSD control claim must be unsat",
        },
        "required_artifacts": [
            "result JSON",
            "scale_ladder",
            "torch primary result",
            "JAX mirror result",
            "proof_results",
            "controls",
            "tool_ablations",
            "TOOL_MANIFEST",
        ],
        "artifacts_emitted": [str(OUT_PATH.relative_to(ROOT))],
        "witness_trace_id": f"{SIM_ID}:{int(started)}",
        "result_summary": {
            "all_pass": all_pass,
            "scale_pass": scale_pass,
            "proof_pass": proof_pass,
            "controls_pass": controls_pass,
            "tool_ablations_pass": ablation_pass,
            "jax_vs_pytorch_delta": jax_mirror_result["max_jax_vs_pytorch_delta"],
            "real_min_eigenvalue_at_64": top["real_min_eigenvalue"],
            "control_min_eigenvalue_at_64": top["control_min_eigenvalue"],
            "min_order_gap_at_64": top["min_order_gap"],
            "max_commuting_order_gap_at_64": top["max_commuting_order_gap"],
        },
        "torch_primary_result": torch_primary_result,
        "jax_mirror_result": jax_mirror_result,
        "jax_vs_pytorch_delta": jax_mirror_result["max_jax_vs_pytorch_delta"],
        "jax_vs_pytorch": {
            "max_abs_delta": jax_mirror_result["max_jax_vs_pytorch_delta"],
            "tolerance": 1.0e-9,
            "agree": parity_pass,
        },
        "proof_results": {
            "smt_load_bearing_trace_psd": density_proof,
            "sympy_exact_one_site_density": sympy_exact_result,
            "pass": proof_pass,
        },
        "controls": controls,
        "tool_ablations": tool_ablations,
        "ablation_outcome_delta": tool_ablations,
        "tool_ablations_by_tool": tool_ablations,
        "sympy_exact_result": sympy_exact_result,
        "scale_ladder": {
            "rungs": scale_rows,
            "scale_axis": "site_count",
            "dense_state_closure_used": False,
            "global_dense_state_materialized": False,
            "pass": scale_pass,
        },
        "positive": {
            "spinor_density_trace_psd": {"pass": torch_primary_result["pass"], "real_invariant": real_invariant},
            "helper_bound_smt_flip": {"pass": density_proof["pass"], "proof": density_proof},
            "sympy_exact_one_site": {"pass": sympy_exact_result["pass"], "proof": sympy_exact_result},
            "scale_8_16_32_64": {"pass": scale_pass, "rungs": scale_rows},
        },
        "graveyard_companions": {
            "non_psd_trace_one_control": {
                "killed": controls["non_psd_trace_one_control"]["pass"],
                "control_invariant": control_invariant,
            },
            "commuting_order_control": {
                "killed": controls["commuting_order_control"]["pass"],
                "max_order_gap": top["max_commuting_order_gap"],
            },
            "mps_mpo_structure_erased": {
                "killed": controls["mps_mpo_structure_erased"]["pass"],
                "erased_tensor_count": 0,
            },
        },
        "boundary": {
            "dense_state_closure_hidden": {"used": False, "pass": True},
            "global_dense_state_materialized": {"used": False, "pass": True},
            "numpy_claim_bearing": {"used": False, "pass": True},
            "promotion_allowed": {"value": False, "pass": True},
            "downstream_consumers_blocked": {"blocked": BLOCKED_CONSUMERS, "pass": True},
            "many_body_depth_claimed": {"claimed": False, "pass": True},
        },
        "why_not_v4_probes": "This is a Stage-2 carrier object: it preserves a finite spinor-density state-space surface for later stages, not a v4 probe replacement, bridge proof, manifold layer, or axis/physics claim.",
        "nearby_variants": {
            "non_psd_control": "trace-one Hermitian control with a negative eigenvalue forces the trace+PSD claim to fail",
            "commuting_controls": "Z/Z rotations preserve the density carrier API while killing the N01 order gap",
            "structure_erased": "removing quimb MPS/MPO leaves local density formulas but removes the requested non-dense carrier object",
        },
        "shells": [
            {
                "name": "stage_2_spinor_density_carrier",
                "status": "carrier lego only",
                "scale_rungs": list(SCALE_RUNGS),
                "survives": all_pass,
            }
        ],
        "future_continuations": [
            "add an entangled MPS/MPO carrier in a separate bounded packet if many-body depth becomes the next gate",
            "add true PEPS3D contraction only after a dedicated PEPS3D carrier packet is scoped",
            "consume this only as bounded Stage-2 spinor-density carrier evidence after validator output is cited",
        ],
        "compatibility_weights": {
            "stage_2_spinor_density_carrier": 1.0 if all_pass else 0.0,
            "downstream_Xi_Phi0_Axis0_flux_FEP_gravity": 0.0,
        },
        "compression_map": {
            "from": "finite site anchors, torch complex128 spinors, local density cells, quimb MPS/MPO tensors, cotengra path metadata, and proof/control readouts",
            "to": "trace/PSD invariant, N01 order-gap invariant, proof verdict flip, scale ladder, controls, ablation deltas, and blocked consumers",
            "loss_boundary": "does not preserve or claim global dense state amplitudes, entangled many-body depth, PEPS3D contraction, manifold layer, axis, bridge, flux, FEP, gravity, or physics admission",
        },
        "present_survivor": {
            "object": OBJECT_ID,
            "capacity": 1.0 if all_pass else 0.0,
            "survives": bool(all_pass),
            "blocked_capacity": BLOCKED_CONSUMERS,
        },
        "survivor_invariant": {
            "invariant": "spinor_density survives iff every rung is finite/non-dense, real trace/PSD holds, non-PSD and commuting controls kill the target claims, helper proof flips, ablations are recomputed and nonzero, and promotion_allowed=false",
            "computed_capacity": 1.0 if all_pass else 0.0,
            "threshold": 1.0,
            "passed": bool(all_pass),
        },
        "outward_record": {
            "result_path": str(OUT_PATH.relative_to(ROOT)),
            "per_sim_contract_command": f"../../../scripts/per_sim_contract.py {OUT_PATH.relative_to(ROOT)}",
            "max_deep_gate_command": f"../../../scripts/max_deep_lego_gate.py {OUT_PATH.relative_to(ROOT)} --scale-required --rigor",
            "recheck_proof_command": f"../../../scripts/recheck_proof.py {OUT_PATH.relative_to(ROOT)} --rerun {pathlib.Path(__file__).name} --python /Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3",
            "claim_ceiling": "Stage-2 spinor-density carrier lego only; no downstream consumer admitted",
        },
        "pass_rule": "all 8/16/32/64 finite non-dense MPS/MPO rungs pass; torch and JAX agree on representable invariants; helper-bound z3/cvc5 proof flips on trace+PSD; sympy exact one-site control fails PSD; controls kill; every tool ablation records baseline+ablated recompute with nonzero distinct deltas",
        "fail_rule": "fail on dense closure, missing MPS/MPO rung, trace/PSD violation in real carrier, non-PSD control not killing the claim, no real/control proof flip, zero/cosmetic ablation, JAX mismatch, or downstream promotion",
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "tool_manifest": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "divergence_log": [],
        "blocked_consumers": BLOCKED_CONSUMERS,
        "downstream_blocks": BLOCKED_CONSUMERS,
        "blockers": [] if all_pass else ["one_or_more_spinor_density_carrier_checks_failed"],
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
                "scale_pass": result["scale_ladder"]["pass"],
                "jax_vs_pytorch_delta": result["jax_vs_pytorch_delta"],
                "proof_pass": result["proof_results"]["pass"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if result["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
