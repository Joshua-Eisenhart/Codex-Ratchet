from __future__ import annotations

import importlib.metadata
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path


def emit(capability: str, version: str, observed, dispatch, runtime=None):
    print(
        json.dumps(
            {
                "schema": "constraintbox.capability-witness.v1",
                "capability_id": capability,
                "version": version,
                "observed": observed,
                "dispatch": dispatch,
                "runtime": runtime or {},
            },
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )


def density_observed(values, eigvalsh, trace, array_builder=lambda value: value):
    eigs = [float(value) for value in eigvalsh(values)]
    eigs.sort()
    dephased = array_builder([[values[0][0], 0.0], [0.0, values[1][1]]])
    dephased_eigs = [float(value) for value in eigvalsh(dephased)]

    def entropy(items):
        return -sum(value * math.log2(value) for value in items if value > 1e-15)

    rank = sum(value > 1e-12 for value in eigs)
    return {
        "trace": float(trace(values)),
        "eigenvalues": eigs,
        "rank": rank,
        "hartley_bits": math.log2(rank),
        "von_neumann_bits": entropy(eigs),
        "dephased_entropy_bits": entropy(dephased_eigs),
    }


def stdlib_finite(fixture):
    histories = fixture["finite_histories"]
    present = sorted({row["present"] for row in histories})
    fibres = sorted(
        sum(1 for row in histories if row["present"] == value)
        for value in present
    )
    emit(
        "stdlib_finite",
        "builtin",
        {
            "history_count": len(histories),
            "projection_count": len(present),
            "fibre_sizes": fibres,
            "hartley_bits": math.log2(len(histories)),
        },
        ["set", "math.log2"],
    )


def numpy_density(fixture):
    import numpy as np

    rho = np.asarray(fixture["rho"], dtype=np.float64)
    emit(
        "numpy_density",
        importlib.metadata.version("numpy"),
        density_observed(rho, np.linalg.eigvalsh, np.trace, np.asarray),
        ["numpy.asarray", "numpy.linalg.eigvalsh", "numpy.trace"],
        {"dtype": str(rho.dtype)},
    )


def scipy_channel(_fixture):
    import numpy as np
    import scipy
    import scipy.linalg

    gamma = _fixture["channel"]["gamma"]
    duration = _fixture["channel"]["duration"]
    generator = np.asarray([[-gamma, gamma], [gamma, -gamma]], dtype=np.float64)
    channel = scipy.linalg.expm(generator * duration)
    state = channel @ np.asarray([1.0, 0.0])
    emit(
        "scipy_channel",
        scipy.__version__,
        {
            "state": [float(value) for value in state],
            "column_sum": float(channel[:, 0].sum()),
        },
        ["scipy.linalg.expm", "numpy.matmul"],
    )


def z3_finite(_fixture):
    import z3

    x, y = z3.Ints("x y")
    sat_solver = z3.Solver()
    sat_solver.add(x >= 0, x <= 1, y >= 0, y <= 1, x != y)
    sat_status = sat_solver.check()
    model = sat_solver.model()
    unsat_solver = z3.Solver()
    unsat_solver.add(x == y, x != y)
    unsat_status = unsat_solver.check()
    emit(
        "z3_finite",
        importlib.metadata.version("z3-solver"),
        {
            "sat": str(sat_status),
            "unsat": str(unsat_status),
            "witness": {"x": model[x].as_long(), "y": model[y].as_long()},
        },
        ["z3.Solver.add", "z3.Solver.check", "z3.Solver.model"],
    )


def cvc5_finite(_fixture):
    import cvc5
    from cvc5 import Kind

    solver = cvc5.Solver()
    solver.setLogic("QF_LIA")
    integer = solver.getIntegerSort()
    x = solver.mkConst(integer, "x")
    y = solver.mkConst(integer, "y")
    zero, one = solver.mkInteger(0), solver.mkInteger(1)
    for term in (
        solver.mkTerm(Kind.GEQ, x, zero),
        solver.mkTerm(Kind.LEQ, x, one),
        solver.mkTerm(Kind.GEQ, y, zero),
        solver.mkTerm(Kind.LEQ, y, one),
        solver.mkTerm(Kind.DISTINCT, x, y),
    ):
        solver.assertFormula(term)
    sat_status = solver.checkSat()

    unsat = cvc5.Solver()
    unsat.setLogic("QF_LIA")
    integer2 = unsat.getIntegerSort()
    a = unsat.mkConst(integer2, "a")
    b = unsat.mkConst(integer2, "b")
    unsat.assertFormula(unsat.mkTerm(Kind.EQUAL, a, b))
    unsat.assertFormula(unsat.mkTerm(Kind.DISTINCT, a, b))
    unsat_status = unsat.checkSat()
    emit(
        "cvc5_finite",
        importlib.metadata.version("cvc5"),
        {"sat": str(sat_status), "unsat": str(unsat_status)},
        ["cvc5.Solver.assertFormula", "cvc5.Solver.checkSat"],
    )


def jax_density(fixture, capability="jax_density"):
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp

    rho = jnp.asarray(fixture["rho"], dtype=jnp.float64)
    observed = density_observed(rho, jnp.linalg.eigvalsh, jnp.trace, jnp.asarray)
    lowered = jax.jit(jnp.linalg.eigvalsh).lower(rho)
    stablehlo = str(lowered.compiler_ir(dialect="stablehlo"))
    device = rho.device
    is_gpu = getattr(device, "platform", "") == "gpu"
    if capability == "jax_cuda_parity" and not is_gpu:
        raise RuntimeError("JAX CUDA witness requested but execution device is not GPU")
    emit(
        capability,
        importlib.metadata.version("jax"),
        observed,
        ["jax.numpy.asarray", "jax.numpy.linalg.eigvalsh", "jax.jit.lower"],
        {
            "x64": bool(jax.config.jax_enable_x64),
            "device": str(device),
            "platform": getattr(device, "platform", None),
            "stablehlo_sha256": __import__("hashlib").sha256(stablehlo.encode()).hexdigest(),
        },
    )


def diffrax_flow(fixture):
    import diffrax
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp

    flow = fixture["flow"]
    term = diffrax.ODETerm(lambda t, y, args: flow["rate"] * y)
    solution = diffrax.diffeqsolve(
        term,
        diffrax.Tsit5(),
        t0=0.0,
        t1=float(flow["duration"]),
        dt0=0.01,
        y0=jnp.asarray(flow["initial"], dtype=jnp.float64),
        saveat=diffrax.SaveAt(t1=True),
    )
    emit(
        "diffrax_flow",
        importlib.metadata.version("diffrax"),
        {"terminal": float(solution.ys[0])},
        ["diffrax.ODETerm", "diffrax.Tsit5", "diffrax.diffeqsolve"],
        {"result": str(solution.result)},
    )


def quimb_tensor(fixture):
    import quimb as qu

    rho = qu.qarray(fixture["rho"])
    emit(
        "quimb_tensor",
        importlib.metadata.version("quimb"),
        density_observed(rho, qu.eigvalsh, qu.trace, qu.qarray),
        ["quimb.qarray", "quimb.eigvalsh", "quimb.trace"],
    )


def cotengra_path(_fixture):
    import cotengra as ctg

    inputs = [(0, 1), (1, 2), (2, 0)]
    output = ()
    sizes = {0: 2, 1: 2, 2: 2}
    optimizer = ctg.HyperOptimizer(
        max_repeats=4, progbar=False, parallel=False, minimize="flops"
    )
    tree = optimizer.search(inputs, output, sizes)
    emit(
        "cotengra_path",
        importlib.metadata.version("cotengra"),
        {
            "contraction_cost": int(tree.contraction_cost()),
            "max_size": int(tree.max_size()),
        },
        ["cotengra.HyperOptimizer", "cotengra.HyperOptimizer.search"],
    )


def torch_density(fixture, capability="torch_density"):
    import torch

    torch.set_default_dtype(torch.float64)
    device = torch.device("cuda" if capability == "torch_cuda_parity" else "cpu")
    if capability == "torch_cuda_parity" and not torch.cuda.is_available():
        raise RuntimeError("Torch CUDA witness requested but CUDA is unavailable")
    rho = torch.tensor(fixture["rho"], dtype=torch.float64, device=device)
    eigs = torch.linalg.eigvalsh(rho).detach().cpu().tolist()
    dephased = torch.diag(torch.diagonal(rho))
    dephased_eigs = torch.linalg.eigvalsh(dephased).detach().cpu().tolist()
    entropy = lambda items: -sum(
        value * math.log2(value) for value in items if value > 1e-15
    )
    rank = sum(value > 1e-12 for value in eigs)
    observed = {
        "trace": float(torch.trace(rho).detach().cpu().item()),
        "eigenvalues": sorted(float(value) for value in eigs),
        "rank": rank,
        "hartley_bits": math.log2(rank),
        "von_neumann_bits": entropy(eigs),
        "dephased_entropy_bits": entropy(dephased_eigs),
    }
    emit(
        capability,
        importlib.metadata.version("torch"),
        observed,
        ["torch.tensor", "torch.linalg.eigvalsh", "torch.trace"],
        {
            "device": str(device),
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda,
        },
    )


def pysindy_law(fixture):
    import numpy as np
    import pysindy as ps

    flow = fixture["flow"]
    t = np.linspace(0.0, float(flow["duration"]), 301)
    x = flow["initial"] * np.exp(flow["rate"] * t)
    library = ps.PolynomialLibrary(degree=1, include_bias=False)
    optimizer = ps.STLSQ(threshold=0.0, alpha=1e-12)
    model = ps.SINDy(feature_library=library, optimizer=optimizer)
    model.fit(x.reshape(-1, 1), t=t)
    coefficient = float(model.coefficients()[0, 0])
    derivative = flow["rate"] * x
    true_residual = float(np.mean((derivative - coefficient * x) ** 2))
    wrong_residual = float(np.mean((derivative - (-1.0) * x) ** 2))
    emit(
        "pysindy_law",
        importlib.metadata.version("pysindy"),
        {
            "coefficient": coefficient,
            "true_residual": true_residual,
            "wrong_residual": wrong_residual,
        },
        ["pysindy.PolynomialLibrary", "pysindy.STLSQ", "pysindy.SINDy.fit"],
        {"feature_library": "polynomial_degree_1_no_bias"},
    )


def pydmd_rate(fixture):
    import numpy as np
    from pydmd import DMD

    item = fixture["discrete_rate"]
    values = np.asarray(
        [item["initial"] * item["multiplier"] ** i for i in range(item["steps"])],
        dtype=float,
    ).reshape(1, -1)
    model = DMD(svd_rank=1, exact=True)
    model.fit(values)
    eigenvalue = complex(model.eigs[0])
    emit(
        "pydmd_rate",
        importlib.metadata.version("PyDMD"),
        {"eigenvalue": float(eigenvalue.real)},
        ["pydmd.DMD", "pydmd.DMD.fit", "pydmd.DMD.eigs"],
    )


def pymdp_fep(_fixture):
    import jax

    jax.config.update("jax_enable_x64", True)
    import jax.numpy as jnp
    import jax.random as jr
    from pymdp import utils
    from pymdp.agent import Agent

    keys = jr.split(jr.PRNGKey(7), 4)
    num_obs, num_states, num_controls = [2], [2], [2]
    a = utils.random_A_array(keys[0], num_obs, num_states)
    b = utils.random_B_array(keys[1], num_states, num_controls)
    c = utils.list_array_uniform([[2]])
    agent = Agent(A=a, B=b, C=c, batch_size=1)
    qs, info = agent.infer_states([jnp.array([0])], empirical_prior=agent.D, return_info=True)
    q_pi, neg_efe = agent.infer_policies(qs)
    posterior_sum = float(jnp.sum(qs[0][0]))
    policy_sum = float(jnp.sum(q_pi[0]))
    vfe = float(jnp.ravel(info["vfe"])[0])
    emit(
        "pymdp_fep",
        importlib.metadata.version("inferactively-pymdp"),
        {
            "posterior_sum": posterior_sum,
            "policy_sum": policy_sum,
            "vfe_finite": math.isfinite(vfe),
            "neg_efe_finite": bool(jnp.all(jnp.isfinite(neg_efe))),
        },
        ["pymdp.Agent.infer_states", "pymdp.Agent.infer_policies"],
    )


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: capability_worker.py CAPABILITY FIXTURE")
    capability, fixture_path = sys.argv[1:]
    fixture = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    dispatch = {
        "stdlib_finite": stdlib_finite,
        "numpy_density": numpy_density,
        "scipy_channel": scipy_channel,
        "z3_finite": z3_finite,
        "cvc5_finite": cvc5_finite,
        "jax_density": jax_density,
        "jax_cuda_parity": lambda value: jax_density(value, "jax_cuda_parity"),
        "diffrax_flow": diffrax_flow,
        "quimb_tensor": quimb_tensor,
        "cotengra_path": cotengra_path,
        "torch_density": torch_density,
        "torch_cuda_parity": lambda value: torch_density(value, "torch_cuda_parity"),
        "pysindy_law": pysindy_law,
        "pydmd_rate": pydmd_rate,
        "pymdp_fep": pymdp_fep,
    }
    if capability not in dispatch:
        raise SystemExit(f"capability worker not implemented: {capability}")
    dispatch[capability](fixture)


if __name__ == "__main__":
    main()
