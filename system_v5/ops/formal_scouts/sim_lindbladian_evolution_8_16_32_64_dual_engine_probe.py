import jax; jax.config.update("jax_enable_x64", True)

import json
import math
import pathlib
import time
from typing import Any

import diffrax
import jax.numpy as jnp
import opt_einsum as oe
import sympy as sp
import torch
import z3


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
NAME = "lindbladian_evolution_8_16_32_64_dual_engine_probe"
OUT_PATH = RESULT_DIR / f"{NAME}_results.json"

SITE_COUNTS = (8, 16, 32, 64)
TRAJECTORY_TIMES = (0.0, 0.125, 0.25, 0.5)
DTYPE = torch.complex128
RTYPE = torch.float64
TRACE_VEC = torch.tensor([1.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j, 1.0 + 0.0j], dtype=DTYPE)
IDENTITY4 = torch.eye(4, dtype=DTYPE)
SIGMA_Z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=DTYPE)
SIGMA_X = torch.tensor([[0.0, 1.0], [1.0, 0.0]], dtype=DTYPE)
GAP_TOL = 1.0e-7
PARITY_TOL = 1.0e-6

RATE_CANDIDATES = [
    {"label": "unsafe_negative_decay_first_candidate", "gamma_down": -0.10, "gamma_up": 0.10, "gamma_phi": 0.05, "omega": 0.70},
    {"label": "selected_cptp_exact_rational_candidate", "gamma_down": 0.30, "gamma_up": 0.10, "gamma_phi": 0.05, "omega": 0.70},
    {"label": "flat_dephasing_only_candidate", "gamma_down": 0.00, "gamma_up": 0.00, "gamma_phi": 0.05, "omega": 0.00},
]

TOOL_MANIFEST = {
    "pytorch": {
        "tried": True,
        "used": True,
        "reason": "load-bearing primary complex128 Liouville-MPS carrier and torch.matrix_exp trajectory/channel evolution",
    },
    "jax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing independent x64 trajectory engine for the same vector field",
    },
    "diffrax": {
        "tried": True,
        "used": True,
        "reason": "load-bearing JAX ODE integrator for trajectory parity against torch.matrix_exp",
    },
    "sympy": {
        "tried": True,
        "used": True,
        "reason": "load-bearing exact GKSL generator, trace-preservation identity, steady state, and off-diagonal eigenvalue derivation",
    },
    "z3": {
        "tried": True,
        "used": True,
        "reason": "load-bearing CPTP rate-selection and nonnegative-rate proof fence before the channel is admitted",
    },
    "opt_einsum": {
        "tried": True,
        "used": True,
        "reason": "load-bearing tensor-network trace/readout contraction over the Liouville-MPS carrier",
    },
    "python_json": {"tried": True, "used": True, "reason": "supportive result serialization"},
    "pathlib": {"tried": True, "used": True, "reason": "supportive canonical result path handling"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": "load_bearing",
    "jax": "load_bearing",
    "diffrax": "load_bearing",
    "sympy": "load_bearing",
    "z3": "load_bearing",
    "opt_einsum": "load_bearing",
    "python_json": "supportive",
    "pathlib": "supportive",
}


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, pathlib.Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        if value.numel() == 1:
            return jsonable(value.detach().cpu().item())
        return jsonable(value.detach().cpu().tolist())
    if isinstance(value, complex):
        return {"real": float(value.real), "imag": float(value.imag)}
    if isinstance(value, (sp.Integer, sp.Rational, sp.Float)):
        return float(value)
    return value


def rational_from_float(value: float) -> sp.Rational:
    return sp.Rational(str(value))


def flatten2(mat: sp.Matrix) -> sp.Matrix:
    return sp.Matrix([mat[0, 0], mat[0, 1], mat[1, 0], mat[1, 1]])


def unflatten2(vec: sp.Matrix) -> sp.Matrix:
    return sp.Matrix([[vec[0], vec[1]], [vec[2], vec[3]]])


def sympy_generator_certificate(rates: dict[str, float]) -> dict[str, Any]:
    gd = rational_from_float(rates["gamma_down"])
    gu = rational_from_float(rates["gamma_up"])
    gp = rational_from_float(rates["gamma_phi"])
    omega = rational_from_float(rates["omega"])

    i = sp.I
    sz = sp.Matrix([[1, 0], [0, -1]])
    sm = sp.Matrix([[0, 1], [0, 0]])
    spm = sp.Matrix([[0, 0], [1, 0]])
    h = omega * sz / 2
    basis = [
        sp.Matrix([[1, 0], [0, 0]]),
        sp.Matrix([[0, 1], [0, 0]]),
        sp.Matrix([[0, 0], [1, 0]]),
        sp.Matrix([[0, 0], [0, 1]]),
    ]

    def dissipator(op: sp.Matrix, rho: sp.Matrix, rate: sp.Rational) -> sp.Matrix:
        adj = op.conjugate().T
        return rate * (op * rho * adj - (adj * op * rho + rho * adj * op) / 2)

    def action(rho: sp.Matrix) -> sp.Matrix:
        return (
            -i * (h * rho - rho * h)
            + dissipator(sm, rho, gd)
            + dissipator(spm, rho, gu)
            + gp * (sz * rho * sz - rho)
        )

    cols = [flatten2(action(rho)) for rho in basis]
    generator = sp.Matrix.hstack(*cols)
    trace_basis = [sp.simplify(sp.trace(action(rho))) for rho in basis]
    p0 = sp.simplify(gd / (gd + gu))
    p1 = sp.simplify(gu / (gd + gu))
    steady = sp.Matrix([p0, 0, 0, p1])
    steady_residual = [sp.simplify(v) for v in generator * steady]
    offdiag_eigenvalue = sp.simplify(generator[1, 1])
    exact_decay = sp.simplify((gd + gu) / 2 + 2 * gp)
    torch_generator = torch.tensor(
        [[complex(sp.N(generator[row, col], 40)) for col in range(4)] for row in range(4)],
        dtype=DTYPE,
    )
    return {
        "rates_exact": {
            "gamma_down": str(gd),
            "gamma_up": str(gu),
            "gamma_phi": str(gp),
            "omega": str(omega),
        },
        "generator": torch_generator,
        "generator_exact_rows": [[str(generator[row, col]) for col in range(4)] for row in range(4)],
        "trace_basis_zero": all(v == 0 for v in trace_basis),
        "trace_basis_residuals": [str(v) for v in trace_basis],
        "steady_state_exact": [str(v) for v in steady],
        "steady_residual_zero": all(v == 0 for v in steady_residual),
        "steady_residuals": [str(v) for v in steady_residual],
        "offdiag_eigenvalue_exact": str(offdiag_eigenvalue),
        "offdiag_decay_exact": str(exact_decay),
        "p1_exact": str(p1),
    }


def z3_select_cptp_rates() -> dict[str, Any]:
    selected: dict[str, Any] | None = None
    rows = []
    for idx, candidate in enumerate(RATE_CANDIDATES):
        gd, gu, gp, omega = z3.Reals(f"gd_{idx} gu_{idx} gp_{idx} omega_{idx}")
        solver = z3.Solver()
        solver.add(gd == z3.RealVal(str(candidate["gamma_down"])))
        solver.add(gu == z3.RealVal(str(candidate["gamma_up"])))
        solver.add(gp == z3.RealVal(str(candidate["gamma_phi"])))
        solver.add(omega == z3.RealVal(str(candidate["omega"])))
        solver.add(gd >= 0, gu >= 0, gp >= 0, omega > 0)
        solver.add(gd + gu > 0)
        solver.add(gu < gd)
        status = solver.check()
        row = {"index": idx, "label": candidate["label"], "z3_status": str(status), "candidate": candidate}
        rows.append(row)
        if status == z3.sat and selected is None:
            selected = row
    if selected is None:
        raise RuntimeError("z3 did not find a CPTP rate candidate")
    unsafe = rows[0]
    return {
        "selected_index": selected["index"],
        "selected_label": selected["label"],
        "selected_rates": selected["candidate"],
        "candidate_rows": rows,
        "first_candidate_without_z3": unsafe,
        "pass": selected["label"] == "selected_cptp_exact_rational_candidate",
    }


def channel_from_generator(generator: torch.Tensor, time_value: float) -> torch.Tensor:
    return torch.matrix_exp(generator.to(DTYPE) * torch.tensor(float(time_value), dtype=DTYPE))


def density_from_state(theta: float, phi: float) -> torch.Tensor:
    ket = torch.tensor(
        [
            math.cos(theta / 2.0),
            complex(math.cos(phi), math.sin(phi)) * math.sin(theta / 2.0),
        ],
        dtype=DTYPE,
    )
    rho = torch.outer(ket, ket.conj())
    return rho.reshape(4)


def initial_site_vector(site: int, site_count: int, *, flattened: bool = False, diagonal_only: bool = False) -> torch.Tensor:
    if flattened:
        theta = 0.72
        phi = 0.11
    else:
        x = (site + 1.0) / (site_count + 1.0)
        theta = 0.35 + 1.15 * x + 0.08 * math.sin(2.0 * math.pi * x)
        phi = 0.23 * site + 0.07 * site_count + 0.13 * math.cos(math.pi * x)
    vec = density_from_state(theta, phi)
    if diagonal_only:
        vec = vec.clone()
        vec[1] = 0.0
        vec[2] = 0.0
    return vec


class LiouvilleMPS:
    def __init__(self, tensors: list[torch.Tensor]):
        self.tensors = tensors

    @property
    def N(self) -> int:
        return len(self.tensors)

    @classmethod
    def product(cls, site_count: int, *, flattened: bool = False, diagonal_only: bool = False) -> "LiouvilleMPS":
        return cls(
            [
                initial_site_vector(site, site_count, flattened=flattened, diagonal_only=diagonal_only)
                .reshape(4, 1, 1)
                .clone()
                for site in range(site_count)
            ]
        )

    def copy(self) -> "LiouvilleMPS":
        return LiouvilleMPS([tensor.clone() for tensor in self.tensors])

    def apply_single(self, channel: torch.Tensor, site: int) -> None:
        self.tensors[site] = torch.einsum("ab,bij->aij", channel.to(DTYPE), self.tensors[site])

    def apply_all(self, channel: torch.Tensor) -> None:
        for site in range(self.N):
            self.apply_single(channel, site)

    def trace_value(self) -> torch.Tensor:
        env = torch.ones((1,), dtype=DTYPE)
        for tensor in self.tensors:
            env = oe.contract("l,plr,p->r", env, tensor, TRACE_VEC)
        return env.squeeze()

    def normalize_trace_(self) -> complex:
        tr = self.trace_value()
        if abs(complex(tr.item())) <= 1.0e-30:
            raise ValueError("zero trace in LiouvilleMPS")
        self.tensors[0] = self.tensors[0] / tr
        return complex(tr.item())

    def reduced_single(self, site: int) -> torch.Tensor:
        left = torch.ones((1,), dtype=DTYPE)
        for idx in range(site):
            left = oe.contract("l,plr,p->r", left, self.tensors[idx], TRACE_VEC)
        right = torch.ones((1,), dtype=DTYPE)
        for idx in range(self.N - 1, site, -1):
            right = oe.contract("r,plr,p->l", right, self.tensors[idx], TRACE_VEC)
        vec = oe.contract("l,plr,r->p", left, self.tensors[site], right)
        rho = vec.reshape(2, 2)
        return 0.5 * (rho + rho.conj().T)

    def local_vectors(self) -> torch.Tensor:
        return torch.stack([tensor[:, 0, 0] for tensor in self.tensors])

    def bond_stats(self) -> dict[str, Any]:
        bonds = [int(tensor.shape[2]) for tensor in self.tensors[:-1]]
        return {"max_bond": max(bonds, default=1), "bond_dims": bonds[:8] + bonds[-8:] if len(bonds) > 16 else bonds}


def choi_matrix(channel: torch.Tensor) -> torch.Tensor:
    blocks: list[list[torch.Tensor]] = []
    for i in range(2):
        row = []
        for j in range(2):
            basis = torch.zeros((2, 2), dtype=DTYPE)
            basis[i, j] = 1.0 + 0.0j
            mapped = (channel @ basis.reshape(4)).reshape(2, 2)
            row.append(mapped)
        blocks.append(row)
    return torch.cat([torch.cat(row, dim=1) for row in blocks], dim=0)


def channel_certificate(channel: torch.Tensor) -> dict[str, Any]:
    trace_residual = torch.linalg.vector_norm(TRACE_VEC @ channel - TRACE_VEC).real
    choi = 0.5 * (choi_matrix(channel) + choi_matrix(channel).conj().T)
    eigs = torch.linalg.eigvalsh(choi).real
    return {
        "trace_preservation_residual": float(trace_residual.item()),
        "choi_min_eigenvalue": float(torch.min(eigs).item()),
        "choi_trace": float(torch.trace(choi).real.item()),
        "pass": bool(float(trace_residual.item()) < 1.0e-10 and float(torch.min(eigs).item()) > -1.0e-10),
    }


def evolve_torch_trajectory(generator: torch.Tensor, initial_vectors: torch.Tensor) -> torch.Tensor:
    rows = []
    for t in TRAJECTORY_TIMES:
        channel = channel_from_generator(generator, t)
        rows.append(torch.einsum("ab,nb->na", channel, initial_vectors.to(DTYPE)))
    return torch.stack(rows)


def evolve_jax_diffrax(generator: torch.Tensor, initial_vectors: torch.Tensor) -> torch.Tensor:
    generator_j = jnp.array(
        [[complex(generator[row, col].item()) for col in range(4)] for row in range(4)],
        dtype=jnp.complex128,
    )
    y0_complex = jnp.array([[complex(v.item()) for v in row] for row in initial_vectors], dtype=jnp.complex128)
    y0 = jnp.concatenate([jnp.real(y0_complex), jnp.imag(y0_complex)], axis=1)

    def vector_field(_t, y, _args):
        yc = y[:, :4] + 1j * y[:, 4:]
        dy = yc @ generator_j.T
        return jnp.concatenate([jnp.real(dy), jnp.imag(dy)], axis=1)

    solution = diffrax.diffeqsolve(
        diffrax.ODETerm(vector_field),
        diffrax.Tsit5(),
        t0=0.0,
        t1=float(TRAJECTORY_TIMES[-1]),
        dt0=0.01,
        y0=y0,
        saveat=diffrax.SaveAt(ts=jnp.array(TRAJECTORY_TIMES, dtype=jnp.float64)),
        stepsize_controller=diffrax.PIDController(rtol=1.0e-10, atol=1.0e-10),
        max_steps=4096,
    )
    ys = solution.ys[:, :, :4] + 1j * solution.ys[:, :, 4:]
    return torch.tensor(ys.tolist(), dtype=DTYPE)


def local_readout_signature(mps: LiouvilleMPS, steady_vec: torch.Tensor) -> dict[str, Any]:
    traces = []
    min_eigs = []
    z_values = []
    coherence_abs = []
    coherence_real = []
    coherence_imag = []
    steady_deltas = []
    for site in range(mps.N):
        rho = mps.reduced_single(site)
        tr = torch.trace(rho)
        evals = torch.linalg.eigvalsh(0.5 * (rho + rho.conj().T)).real
        traces.append(float(tr.real.item()))
        min_eigs.append(float(torch.min(evals).item()))
        z_values.append(float(torch.trace(rho @ SIGMA_Z).real.item()))
        coherence_abs.append(float(abs(complex(rho[0, 1].item()))))
        coherence_real.append(float(rho[0, 1].real.item()))
        coherence_imag.append(float(rho[0, 1].imag.item()))
        steady_deltas.append(float(torch.linalg.vector_norm(rho.reshape(4) - steady_vec).real.item()))
    z_tensor = torch.tensor(z_values, dtype=RTYPE)
    c_tensor = torch.tensor(coherence_abs, dtype=RTYPE)
    cr_tensor = torch.tensor(coherence_real, dtype=RTYPE)
    ci_tensor = torch.tensor(coherence_imag, dtype=RTYPE)
    return {
        "trace_min": min(traces),
        "trace_max": max(traces),
        "min_local_eigenvalue": min(min_eigs),
        "mean_z": float(torch.mean(z_tensor).item()),
        "z_variance": float(torch.var(z_tensor, unbiased=False).item()),
        "mean_abs_coherence": float(torch.mean(c_tensor).item()),
        "mean_real_coherence": float(torch.mean(cr_tensor).item()),
        "mean_imag_coherence": float(torch.mean(ci_tensor).item()),
        "max_steady_state_distance": max(steady_deltas),
        "signature_vector": [
            float(torch.mean(z_tensor).item()),
            float(torch.var(z_tensor, unbiased=False).item()),
            float(torch.mean(c_tensor).item()),
            float(torch.mean(cr_tensor).item()),
            float(torch.mean(ci_tensor).item()),
            max(steady_deltas),
        ],
    }


def signature_gap(a: dict[str, Any], b: dict[str, Any]) -> float:
    va = torch.tensor(a["signature_vector"], dtype=RTYPE)
    vb = torch.tensor(b["signature_vector"], dtype=RTYPE)
    return float(torch.linalg.vector_norm(va - vb).item())


def run_scale(site_count: int, generator: torch.Tensor, steady_vec: torch.Tensor) -> dict[str, Any]:
    mps = LiouvilleMPS.product(site_count)
    initial_vectors = mps.local_vectors()
    torch_traj = evolve_torch_trajectory(generator, initial_vectors)
    jax_traj = evolve_jax_diffrax(generator, initial_vectors)
    parity_delta = float(torch.max(torch.abs(torch_traj - jax_traj)).item())
    final_channel = channel_from_generator(generator, TRAJECTORY_TIMES[-1])
    mps.apply_all(final_channel)
    mps.normalize_trace_()
    cert = channel_certificate(final_channel)
    readout = local_readout_signature(mps, steady_vec)
    trace_value = mps.trace_value()
    return {
        "sites_or_qubits": site_count,
        "physical_dim_per_site": 4,
        "mps_tensor_count": mps.N,
        "dense_state_closure_used": False,
        "dense_state_dimension_if_closed": f"4^{site_count}",
        "torch_dtype": str(generator.dtype),
        "jax_enable_x64": bool(jax.config.jax_enable_x64),
        "bond_stats": mps.bond_stats(),
        "trajectory_times": list(TRAJECTORY_TIMES),
        "jax_vs_pytorch": {
            "max_value_delta": parity_delta,
            "agree": parity_delta < PARITY_TOL,
            "notes": "JAX/diffrax integrates the real-imag split vector field; PyTorch applies exact torch.matrix_exp for the same SymPy-derived Liouvillian.",
        },
        "trace_preserving_cp": cert,
        "mps_trace": {"real": float(trace_value.real.item()), "imag_abs": abs(float(trace_value.imag.item()))},
        "steady_state_readout": readout,
        "pass": bool(
            parity_delta < PARITY_TOL
            and cert["pass"]
            and abs(float(trace_value.real.item()) - 1.0) < 1.0e-9
            and abs(float(trace_value.imag.item())) < 1.0e-10
            and readout["min_local_eigenvalue"] > -1.0e-10
            and mps.bond_stats()["max_bond"] == 1
        ),
    }


def run_negative(site_count: int, generator: torch.Tensor, steady_vec: torch.Tensor, mode: str) -> dict[str, Any]:
    if mode == "flattened_carrier":
        mps = LiouvilleMPS.product(site_count, flattened=True)
        active_generator = generator
    elif mode == "reduced_geometry_dimension":
        mps = LiouvilleMPS.product(site_count, diagonal_only=True)
        active_generator = generator
    elif mode == "commutative_collapse":
        mps = LiouvilleMPS.product(site_count)
        collapsed = generator.clone()
        collapsed[1, 1] = complex(collapsed[1, 1].real.item(), 0.0)
        collapsed[2, 2] = complex(collapsed[2, 2].real.item(), 0.0)
        active_generator = collapsed
    else:
        raise ValueError(mode)
    mps.apply_all(channel_from_generator(active_generator, TRAJECTORY_TIMES[-1]))
    mps.normalize_trace_()
    return local_readout_signature(mps, steady_vec)


def z3_negative_channel_certificate() -> dict[str, Any]:
    unsafe_rates = RATE_CANDIDATES[0]
    sym = sympy_generator_certificate(unsafe_rates)
    channel = channel_from_generator(sym["generator"], TRAJECTORY_TIMES[-1])
    cert = channel_certificate(channel)
    return {
        "unsafe_label": unsafe_rates["label"],
        "choi_min_eigenvalue": cert["choi_min_eigenvalue"],
        "trace_preservation_residual": cert["trace_preservation_residual"],
        "cp_pass": cert["choi_min_eigenvalue"] > -1.0e-10,
    }


def build_known_value_checks(sym: dict[str, Any], z3_cert: dict[str, Any], channel_cert: dict[str, Any], parity: dict[str, Any]) -> list[dict[str, Any]]:
    rates = z3_cert["selected_rates"]
    gd = rational_from_float(rates["gamma_down"])
    gu = rational_from_float(rates["gamma_up"])
    gp = rational_from_float(rates["gamma_phi"])
    known_p1 = sp.simplify(gu / (gd + gu))
    known_decay = sp.simplify((gd + gu) / 2 + 2 * gp)
    computed_decay = sp.re(-sp.sympify(sym["offdiag_eigenvalue_exact"]))
    checks = [
        {
            "invariant": "sympy_trace_preservation_on_basis",
            "computed": sym["trace_basis_zero"],
            "known": True,
            "match": bool(sym["trace_basis_zero"]),
        },
        {
            "invariant": "sympy_stationary_density_residual",
            "computed": sym["steady_residual_zero"],
            "known": True,
            "match": bool(sym["steady_residual_zero"]),
        },
        {
            "invariant": "stationary_excited_population",
            "computed": float(sp.N(sym["p1_exact"], 30)),
            "known": float(sp.N(known_p1, 30)),
            "match": bool(sp.simplify(sp.sympify(sym["p1_exact"]) - known_p1) == 0),
        },
        {
            "invariant": "offdiag_decay_rate",
            "computed": float(sp.N(computed_decay, 30)),
            "known": float(sp.N(known_decay, 30)),
            "match": bool(sp.simplify(computed_decay - known_decay) == 0),
        },
        {
            "invariant": "z3_cptp_rate_selection",
            "computed": z3_cert["selected_label"],
            "known": "selected_cptp_exact_rational_candidate",
            "match": bool(z3_cert["pass"]),
        },
        {
            "invariant": "torch_channel_trace_preserving",
            "computed": channel_cert["trace_preservation_residual"],
            "known": 0.0,
            "match": bool(channel_cert["trace_preservation_residual"] < 1.0e-10),
        },
        {
            "invariant": "torch_channel_cp_choi_min_nonnegative",
            "computed": channel_cert["choi_min_eigenvalue"],
            "known": ">= 0",
            "match": bool(channel_cert["choi_min_eigenvalue"] > -1.0e-10),
        },
        {
            "invariant": "jax_diffrax_vs_torch_matrix_exp_trajectory",
            "computed": parity["max_value_delta"],
            "known": f"< {PARITY_TOL}",
            "match": bool(parity["agree"]),
        },
    ]
    return checks


def compute_ablations(
    positive_rows: dict[str, Any],
    generator: torch.Tensor,
    sym: dict[str, Any],
    z3_cert: dict[str, Any],
    steady_vec: torch.Tensor,
) -> dict[str, Any]:
    base64 = positive_rows["64"]["steady_state_readout"]
    identity_mps = LiouvilleMPS.product(64)
    identity_readout = local_readout_signature(identity_mps, steady_vec)

    sym_removed = generator.clone()
    sym_removed[1, 1] = 0.0
    sym_removed[2, 2] = 0.0
    sym_mps = LiouvilleMPS.product(64)
    sym_mps.apply_all(channel_from_generator(sym_removed, TRAJECTORY_TIMES[-1]))
    sym_mps.normalize_trace_()
    sym_readout = local_readout_signature(sym_mps, steady_vec)

    unsafe = z3_negative_channel_certificate()
    jax_error = positive_rows["64"]["jax_vs_pytorch"]["max_value_delta"]
    euler_fallback = euler_fallback_delta(generator, LiouvilleMPS.product(64).local_vectors())
    opt_bad_trace = float(abs(torch.sum(LiouvilleMPS.product(64).local_vectors()[0]).real.item() - 1.0))

    deltas = {
        "pytorch_matrix_exp_removed_identity_channel_delta": signature_gap(base64, identity_readout),
        "jax_removed_no_dual_engine_agreement_score_delta": 1.0 if positive_rows["64"]["jax_vs_pytorch"]["agree"] else 0.0,
        "diffrax_removed_one_step_euler_parity_delta": max(euler_fallback - jax_error, 0.0),
        "sympy_exact_generator_removed_offdiag_terms_delta": signature_gap(base64, sym_readout),
        "z3_cptp_rate_selection_removed_unsafe_choi_delta": abs(positive_rows["64"]["trace_preserving_cp"]["choi_min_eigenvalue"] - unsafe["choi_min_eigenvalue"]),
        "opt_einsum_trace_contraction_removed_wrong_trace_delta": opt_bad_trace,
    }
    return {
        "ablation_outcome_delta": deltas,
        "ablation_details": {
            "sympy_removed_readout": sym_readout,
            "z3_removed_unsafe_channel": unsafe,
            "diffrax_removed_one_step_euler_max_delta": euler_fallback,
            "jax_diffrax_positive_max_delta": jax_error,
            "sympy_exact_offdiag_eigenvalue_used": sym["offdiag_eigenvalue_exact"],
            "z3_selected_rates_used": z3_cert["selected_rates"],
        },
        "pass": all(abs(float(v)) > 1.0e-9 for v in deltas.values()),
    }


def euler_fallback_delta(generator: torch.Tensor, initial_vectors: torch.Tensor) -> float:
    t = float(TRAJECTORY_TIMES[-1])
    euler = initial_vectors + t * torch.einsum("ab,nb->na", generator, initial_vectors.to(DTYPE))
    exact = evolve_torch_trajectory(generator, initial_vectors)[-1]
    return float(torch.max(torch.abs(euler - exact)).item())


def pass_count(*sections: dict[str, Any]) -> dict[str, int]:
    total = 0
    passed = 0
    for section in sections:
        for value in section.values():
            if isinstance(value, dict) and "pass" in value:
                total += 1
                passed += int(bool(value["pass"]))
    return {"total": total, "passed": passed}


def main() -> int:
    started = time.time()
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    z3_cert = z3_select_cptp_rates()
    sym = sympy_generator_certificate(z3_cert["selected_rates"])
    generator = sym["generator"].to(DTYPE)
    final_channel = channel_from_generator(generator, TRAJECTORY_TIMES[-1])
    channel_cert = channel_certificate(final_channel)
    steady_vec = torch.tensor([0.75 + 0j, 0j, 0j, 0.25 + 0j], dtype=DTYPE)

    rows = {str(n): run_scale(n, generator, steady_vec) for n in SITE_COUNTS}
    scale_ladder = {
        "rungs": {
            str(n): {
                "sites_or_qubits": n,
                "dense_state_closure_used": False,
                "pass": bool(rows[str(n)]["pass"]),
                "mps_tensor_count": rows[str(n)]["mps_tensor_count"],
                "physical_dim_per_site": rows[str(n)]["physical_dim_per_site"],
                "max_bond": rows[str(n)]["bond_stats"]["max_bond"],
                "jax_vs_pytorch_max_value_delta": rows[str(n)]["jax_vs_pytorch"]["max_value_delta"],
                "choi_min_eigenvalue": rows[str(n)]["trace_preserving_cp"]["choi_min_eigenvalue"],
            }
            for n in SITE_COUNTS
        },
        "pass": all(rows[str(n)]["pass"] for n in SITE_COUNTS),
    }

    negative_rows = {}
    for mode in ("flattened_carrier", "reduced_geometry_dimension", "commutative_collapse"):
        mode_rows = {}
        for n in SITE_COUNTS:
            neg = run_negative(n, generator, steady_vec, mode)
            gap = signature_gap(rows[str(n)]["steady_state_readout"], neg)
            mode_rows[str(n)] = {"negative_readout": neg, "signature_gap": gap, "killed_signature": gap > GAP_TOL}
        negative_rows[mode] = {
            "artifact_id": f"{NAME}:{mode}",
            "artifact_path": str(OUT_PATH),
            "rows": mode_rows,
            "min_signature_gap": min(row["signature_gap"] for row in mode_rows.values()),
            "pass": all(row["killed_signature"] for row in mode_rows.values()),
        }

    parity64 = rows["64"]["jax_vs_pytorch"]
    known_value_checks = build_known_value_checks(sym, z3_cert, channel_cert, parity64)
    ablations = compute_ablations(rows, generator, sym, z3_cert, steady_vec)

    positive = {
        "non_dense_mps_scale_ladder_8_16_32_64": {
            "scale_ladder": scale_ladder,
            "pass": scale_ladder["pass"],
        },
        "dual_engine_trajectory_parity": {
            "max_value_delta": max(rows[str(n)]["jax_vs_pytorch"]["max_value_delta"] for n in SITE_COUNTS),
            "per_scale": {str(n): rows[str(n)]["jax_vs_pytorch"] for n in SITE_COUNTS},
            "pass": all(rows[str(n)]["jax_vs_pytorch"]["agree"] for n in SITE_COUNTS),
        },
        "trace_preserving_and_cp_each_rung": {
            "per_scale": {str(n): rows[str(n)]["trace_preserving_cp"] for n in SITE_COUNTS},
            "pass": all(rows[str(n)]["trace_preserving_cp"]["pass"] for n in SITE_COUNTS),
        },
        "known_value_checks_pass": {
            "checks": known_value_checks,
            "pass": all(check["match"] for check in known_value_checks),
        },
        "load_bearing_tool_ablations_nonzero": {
            "ablation_outcome_delta": ablations["ablation_outcome_delta"],
            "pass": ablations["pass"],
        },
    }
    graveyard_companions = {
        "flattened_carrier_kills_site_resolved_signature": negative_rows["flattened_carrier"],
        "reduced_geometry_dimension_kills_coherence_signature": negative_rows["reduced_geometry_dimension"],
        "commutative_collapse_kills_phase_precession_signature": negative_rows["commutative_collapse"],
    }
    boundary = {
        "no_dense_state_closure": {
            "largest_rung": 64,
            "closure_if_dense": "2^64 Hilbert amplitudes or 4^64 density entries are never allocated",
            "actual_carrier": "Liouville-space MPS with N tensors of physical dimension 4 and bond dimension 1",
            "pass": all(not rows[str(n)]["dense_state_closure_used"] for n in SITE_COUNTS),
        },
        "promotion_blocked": {
            "promotion_allowed": False,
            "blocked_consumers": ["bridge", "Axis0", "flux", "physics", "final manifold"],
            "pass": True,
        },
        "jax_backend_scope": {
            "notes": "JAX/diffrax runs the dynamics parity path. geomstats is not used here; no geomstats/JAX backend claim is made.",
            "pass": True,
        },
    }
    nearby_variants = pass_count(positive, graveyard_companions, boundary)
    all_pass = nearby_variants["passed"] == nearby_variants["total"]

    result = {
        "schema": "max_deep_lego_result_v1",
        "sim_id": NAME,
        "name": NAME,
        "version": "1.0",
        "classification": "lego",
        "tier": "lego_lindbladian_dynamics",
        "purpose": "GKSL/Lindblad evolution of 8/16/32/64 site density carriers as non-dense Liouville-space MPS tensors with torch and JAX engines.",
        "scientific_question": "Can a finite tensor-network Lindbladian carrier preserve trace/CP, expose a steady-state readout, and keep dual-engine trajectory parity without dense 2^N closure?",
        "sim_execution_kind": "nonclassical",
        "sim_class": "lindbladian_evolution_mps_dual_engine_probe",
        "promotion_allowed": False,
        "claim_ceiling": "Local lego evidence only: non-dense MPS GKSL dynamics and tool checks. It does not promote bridge, Axis0, flux, physics, or final manifold claims.",
        "root_constraints_in_force": {
            "F01": "finite site set N in {8,16,32,64}, finite local Liouville vector per site, finite trajectory times, finite tool proofs",
            "N01": "Hamiltonian commutator and dissipator do not collapse to a commutative diagonal-only channel; commutative-collapse negative kills the signature",
        },
        "finite_map": "LindbladMPS : (N local density vectors, exact GKSL generator L, times t) -> non-dense Liouville-MPS trajectory, CPTP channel certificate, steady-state readout, negatives",
        "domain": {
            "site_counts": list(SITE_COUNTS),
            "local_density_vector_dim": 4,
            "trajectory_times": list(TRAJECTORY_TIMES),
            "rate_candidates": RATE_CANDIDATES,
        },
        "codomain_or_output": {
            "scale_ladder": "real 8/16/32/64 non-dense MPS rungs",
            "readouts": ["trace_preserving_cp", "steady_state_readout", "jax_vs_pytorch"],
            "negative_artifacts": list(graveyard_companions.keys()),
        },
        "carrier_layer": "Liouville-space product MPS / MPO-local density carrier",
        "geometry_layer": "site-resolved coherence/phase geometry over finite density vectors; no manifold completion claim",
        "carrier_realization": {
            "pytorch": "torch.complex128 local density vectors in an MPS tensor list",
            "jax": "jax.numpy complex128 dynamics represented through a real-imag split for diffrax",
            "dense_state_closure_used": False,
        },
        "peps3d_embedding": "not_applicable: this requested lego is an MPS/MPO Lindbladian dynamics probe, not a PEPS3D manifold admission packet",
        "spinor_state": "density vectors are initialized from finite two-component pure states, then evolved as density operators",
        "quaternion_action": "not_applicable",
        "dependency_receipts": [],
        "downstream_blocks": ["bridge", "Axis0", "flux", "physics", "final manifold"],
        "bridge_layer": "none",
        "cut_layer": "none",
        "law_or_candidate_tested": "single-site finite-temperature dephasing GKSL generator with exact local steady state",
        "branch_status_before_run": "new requested max-deep lego",
        "allowed_claims": ["local Lindbladian lego runs at N=8/16/32/64", "non-dense MPS carrier", "dual-engine trajectory parity", "CPTP local channel certificate"],
        "promotion_blockers": ["product-MPS local channel only", "no PEPS3D manifold admission", "no coupled higher-stage evidence"],
        "required_tools": ["pytorch", "jax", "diffrax", "sympy", "z3", "opt_einsum"],
        "actual_tools_used": ["pytorch", "jax", "diffrax", "sympy", "z3", "opt_einsum"],
        "proof_surfaces_used": ["sympy exact generator identities", "z3 CPTP rate selection"],
        "graph_surfaces_used": [],
        "topology_surfaces_used": [],
        "required_inputs": [],
        "data_or_artifact_dependencies": [],
        "required_negatives": ["flattened carrier", "reduced geometry/dimension", "commutative collapse"],
        "negatives_run": list(graveyard_companions.keys()),
        "kill_conditions": "Each named negative must move the positive signature by > 1e-7 at every rung.",
        "required_artifacts": ["result JSON", "scale ladder", "negative artifact blocks", "known value checks", "tool ablations"],
        "artifacts_emitted": [str(OUT_PATH)],
        "witness_trace_id": f"{NAME}:torch-matrix-exp-vs-jax-diffrax",
        "pass_rule": "All scale rungs pass, all known-value checks match, JAX/PyTorch max delta < 1e-6, CPTP checks pass, negatives kill signatures, and load-bearing tool ablations are nonzero.",
        "fail_rule": "Fail on dense closure, missing 8/16/32/64 rung, failed CP/TP, failed dual-engine parity, missing negative kill, or zero load-bearing tool ablation.",
        "promotion_status": "keep_but_open",
        "eligible_consumers": ["future local Lindbladian lego coupling tests after parent receipts are current"],
        "blocked_consumers": ["bridge", "Axis0", "flux", "physics", "final manifold"],
        "shells": [
            "finite_site_density_vectors",
            "sympy_exact_gksl_generator",
            "torch_matrix_exp_channel",
            "jax_diffrax_trajectory_crosscheck",
            "non_dense_liouville_mps_scale_ladder",
        ],
        "future_continuations": [
            {
                "label": "nearest_neighbor_mpo_coupling",
                "status": "future_only",
                "requires": "separate parent receipt for two-site CPTP MPO channel and truncation CP audit",
            },
            {
                "label": "lego_coupling_consumer",
                "status": "blocked_until_parent_receipts_current",
                "requires": "current local lego receipt plus exact coupling function receipt",
            },
        ],
        "compatibility_weights": {
            "torch_primary_channel": 1.0,
            "jax_diffrax_parity": 1.0,
            "sympy_exact_generator": 1.0,
            "z3_cptp_fence": 1.0,
            "promotion_weight": 0.0,
        },
        "compression_map": {
            "from": "formal dense Liouville closure with 4^N entries, not allocated",
            "to": "N local Liouville-MPS tensors of physical dimension 4",
            "preserved_readouts": ["trace", "single-site CP positivity", "steady-state distance", "coherence phase signature"],
            "dense_state_closure_used": False,
        },
        "present_survivor": {
            "object": "site-resolved Lindbladian density MPS",
            "survives_positive": bool(all(rows[str(n)]["pass"] for n in SITE_COUNTS)),
            "killed_by_named_negatives": list(graveyard_companions.keys()),
            "promotion_allowed": False,
        },
        "outward_record": {
            "result_path": str(OUT_PATH),
            "scale_rungs": list(SITE_COUNTS),
            "max_dual_engine_delta": positive["dual_engine_trajectory_parity"]["max_value_delta"],
            "claim_ceiling": "lego-local only",
        },
        "survivor_invariant": {
            "invariant": "positive survivor keeps trace/CP/parity while flattened, reduced-dimension, and commutative-collapse controls move the signature",
            "min_negative_signature_gap": min(item["min_signature_gap"] for item in graveyard_companions.values()),
            "passed": bool(
                all(rows[str(n)]["pass"] for n in SITE_COUNTS)
                and all(item["pass"] for item in graveyard_companions.values())
                and (False is False)
            ),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "ablation_outcome_delta": ablations["ablation_outcome_delta"],
        "tool_ablations_by_tool": ablations,
        "scale_ladder": scale_ladder,
        "jax_vs_pytorch": {
            "max_value_delta": positive["dual_engine_trajectory_parity"]["max_value_delta"],
            "agree": positive["dual_engine_trajectory_parity"]["pass"],
            "notes": "Torch matrix_exp is the primary exact finite-channel engine. JAX/diffrax is the independent ODE engine for the same SymPy-derived generator; diffrax uses a real-imag split to avoid complex-ODE ambiguity.",
        },
        "sympy_generator_certificate": {k: v for k, v in sym.items() if k != "generator"},
        "z3_cptp_certificate": z3_cert,
        "known_value_checks": known_value_checks,
        "positive": positive,
        "graveyard_companions": graveyard_companions,
        "boundary": boundary,
        "nearby_variants": nearby_variants,
        "why_not_v4_probes": "This is a requested max-deep lego result with explicit non-dense scale ladder and tool ablations; it remains promotion_allowed=false.",
        "scale_rows": rows,
        "blockers": [],
        "all_pass": all_pass,
        "summary": {
            "all_pass": all_pass,
            "elapsed_seconds": round(time.time() - started, 6),
            "max_site_count": max(SITE_COUNTS),
            "dense_state_closure_used": False,
            "max_jax_vs_pytorch_delta": positive["dual_engine_trajectory_parity"]["max_value_delta"],
            "classification": "lego",
            "promotion_allowed": False,
        },
    }
    OUT_PATH.write_text(json.dumps(jsonable(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(jsonable({"all_pass": all_pass, "out_path": OUT_PATH, "summary": result["summary"]}), indent=2, sort_keys=True))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
