#!/usr/bin/env python3
"""UNOFFICIAL STRESS PROBE — entropy-gradient sweep over the Bell family.

classification: unofficial_stress_probe · promotion_allowed: false
claim_ceiling: engine exercise only — stresses the built JAX+Julia entropy
machinery at scale and demonstrates unused JAX tools (vmap, jit, grad) on a
real quantum object. No manifold, axis, or bridge claim. Parks by definition.

What it stresses:
  |psi(theta)> = cos(theta)|00> + sin(theta)|11>,  theta in [0, pi/2]
  S(A|B)(theta) = S(rho_AB) - S(rho_B) = -S_B  (pure global state)
  - jit(vmap(engine_path)) over 100_001 thetas: full 4x4 density matrix,
    einsum partial trace, eigvalsh, von Neumann entropy — the ENGINE path,
    not the closed form.
  - jax.grad of the engine path: d S(A|B)/d theta on 1_001 points — the
    entropy GRADIENT computed by autodiff through ptrace+eigh.
  - dynamiqs cross-check at 9 thetas (dq.ptrace/dq.entropy_vn).
  - Julia QuantumOptics cross-check at 9 thetas (separate process).
  - closed-form control: S_B = h2(cos^2 theta) in bits.

Exit 0 = probe completed (agreements recorded either way); 1 = infra failure.
"""
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path

os.environ.setdefault("JAX_PLATFORMS", "cpu")
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE", "false")
import jax

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
LN2 = math.log(2.0)


def s_cond_engine(theta):
    """S(A|B) in bits via the full engine path: state -> rho -> ptrace -> eigh -> S."""
    psi = jnp.zeros(4, dtype=jnp.complex128)
    psi = psi.at[0].set(jnp.cos(theta)).at[3].set(jnp.sin(theta))  # |00>, |11>
    rho = jnp.outer(psi, jnp.conj(psi))                            # 4x4, pure
    rho4 = rho.reshape(2, 2, 2, 2)
    rho_b = jnp.einsum("ijik->jk", rho4)                           # trace out A
    def vn_bits(m):
        w = jnp.linalg.eigvalsh(m)
        w = jnp.where(w > 1e-14, w, 1.0)                           # 0 log 0 = 0
        return -jnp.sum(w * jnp.log(w)) / LN2
    return vn_bits(rho) - vn_bits(rho_b)                           # S_AB - S_B


def main():
    # 1. STRESS: jit(vmap) over 100_001 thetas.
    thetas = jnp.linspace(0.0, jnp.pi / 2, 100_001)
    sweep = jax.jit(jax.vmap(s_cond_engine))
    t0 = time.perf_counter()
    s_cond = sweep(thetas).block_until_ready()
    t_sweep = time.perf_counter() - t0

    # closed-form control (not an engine — a check on the engine)
    c2 = jnp.cos(thetas) ** 2
    s2 = 1.0 - c2
    h2 = -(jnp.where(c2 > 1e-14, c2 * jnp.log(c2), 0.0)
           + jnp.where(s2 > 1e-14, s2 * jnp.log(s2), 0.0)) / LN2
    ctrl_div = float(jnp.max(jnp.abs(s_cond - (-h2))))

    # 2. GRADIENT: autodiff through ptrace+eigh on 1_001 points (endpoints
    # excluded — eigh degeneracy at theta=0, pi/2 makes the gradient singular).
    g_thetas = jnp.linspace(0.05, jnp.pi / 2 - 0.05, 1_001)
    t0 = time.perf_counter()
    grads = jax.jit(jax.vmap(jax.grad(s_cond_engine)))(g_thetas).block_until_ready()
    t_grad = time.perf_counter() - t0
    # witness: gradient crosses zero once, near pi/4 (max entanglement)
    sign_flips = int(jnp.sum(jnp.abs(jnp.diff(jnp.sign(grads))) > 0))
    zero_at = float(g_thetas[int(jnp.argmin(jnp.abs(grads)))])

    # 3. dynamiqs cross-check at 9 thetas.
    import dynamiqs as dq
    check_thetas = [i * math.pi / 16 for i in range(1, 8)] + [0.1, 1.2]
    dq_vals = []
    for th in check_thetas:
        psi = jnp.zeros((4, 1), dtype=jnp.complex128)
        psi = psi.at[0, 0].set(math.cos(th)).at[3, 0].set(math.sin(th))
        rho = dq.asqarray(psi @ psi.conj().T, dims=(2, 2))
        s_ab = float(dq.entropy_vn(rho)) / LN2
        s_b = float(dq.entropy_vn(dq.ptrace(rho, keep=1))) / LN2
        dq_vals.append(s_ab - s_b)
    jax_at_check = [float(s_cond_engine(jnp.asarray(th))) for th in check_thetas]
    dq_div = max(abs(a - b) for a, b in zip(dq_vals, jax_at_check))

    # 4. Julia QuantumOptics cross-check (separate process, same thetas).
    import shutil
    julia_bin = shutil.which("julia")
    if not julia_bin:
        print("[FATAL] no julia on PATH", file=sys.stderr)
        return 1
    proc = subprocess.run(
        [julia_bin, f"--project={REPO}/system_v5/julia_carrier",
         str(HERE / "entropy_gradient_sweep_julia.jl")] + [repr(t) for t in check_thetas],
        capture_output=True, text=True, timeout=600)
    if proc.returncode != 0:
        print(f"[FATAL] julia leg exit {proc.returncode}: {proc.stderr[-200:]}", file=sys.stderr)
        return 1
    jl = json.loads([ln for ln in proc.stdout.splitlines() if ln.startswith("{")][-1])
    jl_div = max(abs(a - b) for a, b in zip(jl["s_cond_bits"], jax_at_check))

    agree = ctrl_div < 1e-9 and dq_div < 1e-9 and jl_div < 1e-9
    receipt = {
        "classification": "unofficial_stress_probe",
        "promotion_allowed": False,
        "claim_ceiling": "engine exercise only — no manifold/axis/bridge claim; parks by definition",
        "engines_used": {
            "jax": ["vmap", "jit", "grad", "eigvalsh", "einsum_ptrace", "complex128_x64"],
            "dynamiqs": ["asqarray", "ptrace", "entropy_vn"],
            "julia": ["QuantumOptics tensor/ptrace/entropy_vn (separate process)"],
        },
        "stress": {
            "sweep_points": int(thetas.shape[0]),
            "sweep_seconds": round(t_sweep, 3),
            "points_per_second": round(thetas.shape[0] / t_sweep),
            "grad_points": int(g_thetas.shape[0]),
            "grad_seconds": round(t_grad, 3),
        },
        "witnesses": {
            "s_cond_min_bits": float(jnp.min(s_cond)),
            "s_cond_at_0": float(s_cond[0]),
            "s_cond_negative_fraction": float(jnp.mean(s_cond < -1e-12)),
            "grad_sign_flips": sign_flips,
            "grad_zero_near_pi_over_4": zero_at,
            "pi_over_4": math.pi / 4,
        },
        "agreement": {
            "engine_vs_closed_form_max_div": ctrl_div,
            "jax_vs_dynamiqs_max_div": dq_div,
            "jax_vs_julia_max_div": jl_div,
            "all_below_1e-9": agree,
        },
    }
    out = HERE / "results"
    out.mkdir(exist_ok=True)
    with open(out / "entropy_gradient_sweep_stress.json", "w") as f:
        json.dump(receipt, f, indent=1, sort_keys=True)
    print(json.dumps(receipt["agreement"] | receipt["stress"], indent=1))
    print(f"[*] stress probe COMPLETED — agreement {'HOLDS' if agree else 'FAILS (recorded)'}; "
          f"receipt: {out / 'entropy_gradient_sweep_stress.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
