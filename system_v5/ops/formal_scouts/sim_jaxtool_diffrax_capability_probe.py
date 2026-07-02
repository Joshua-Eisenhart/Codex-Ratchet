import jax
jax.config.update("jax_enable_x64", True)

import math
import jax.numpy as jnp
import diffrax

classification = "diagnostic_only"

# ---------------------------------------------------------------------------
# x64 honored check: a jnp float array must come back as float64.
# ---------------------------------------------------------------------------
_rtype_probe = jnp.asarray([1.0, 2.0])
_ctype_probe = jnp.asarray([1.0 + 1.0j])
RTYPE = str(_rtype_probe.dtype)
CTYPE = str(_ctype_probe.dtype)
assert RTYPE == "float64", f"x64 NOT honored: float dtype={RTYPE}"
assert CTYPE == "complex128", f"x64 NOT honored: complex dtype={CTYPE}"

# ---------------------------------------------------------------------------
# Operation 1: solve dy/dt = -y, y(0)=1 on t in [0,1]. KNOWN: y(1)=exp(-1).
# ---------------------------------------------------------------------------
def decay_rhs(t, y, args):
    return -y

term = diffrax.ODETerm(decay_rhs)
solver = diffrax.Tsit5()
y0 = jnp.asarray(1.0)
sol = diffrax.diffeqsolve(
    term,
    solver,
    t0=0.0,
    t1=1.0,
    dt0=0.01,
    y0=y0,
    saveat=diffrax.SaveAt(t1=True),
    stepsize_controller=diffrax.PIDController(rtol=1e-10, atol=1e-12),
)
y1_computed = float(sol.ys[-1])
y1_known = math.exp(-1.0)  # 0.36787944117144233
decay_state_dtype = str(sol.ys.dtype)
decay_err = abs(y1_computed - y1_known)
decay_match = bool(decay_err < 1e-9)

# ---------------------------------------------------------------------------
# Operation 2: unitary evolution dpsi/dt = -i H psi, H Hermitian (2-level).
# KNOWN: ||psi(t)|| == 1 preserved exactly (norm invariant under unitary flow).
# ---------------------------------------------------------------------------
# Hermitian H (Pauli-X plus detuning on Z): H = [[0.5, 1.0],[1.0, -0.5]]
H = jnp.asarray([[0.5 + 0.0j, 1.0 + 0.0j],
                 [1.0 + 0.0j, -0.5 + 0.0j]])
assert jnp.allclose(H, H.conj().T), "H is not Hermitian"

def schrodinger_rhs(t, psi, args):
    return -1j * (H @ psi)

cterm = diffrax.ODETerm(schrodinger_rhs)
csolver = diffrax.Tsit5()
psi0 = jnp.asarray([1.0 + 0.0j, 0.0 + 0.0j])
psi0 = psi0 / jnp.linalg.norm(psi0)
csol = diffrax.diffeqsolve(
    cterm,
    csolver,
    t0=0.0,
    t1=2.3,
    dt0=0.001,
    y0=psi0,
    saveat=diffrax.SaveAt(t1=True),
    stepsize_controller=diffrax.PIDController(rtol=1e-11, atol=1e-13),
)
psi_t = csol.ys[-1]
norm_computed = float(jnp.linalg.norm(psi_t).real)
norm_known = 1.0
psi_state_dtype = str(csol.ys.dtype)
norm_err = abs(norm_computed - norm_known)
norm_match = bool(norm_err < 1e-9)

# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------
all_match = bool(decay_match and norm_match)

print("=== diffrax capability probe ===")
print(f"classification      : {classification}")
print(f"x64 rtype (live)    : {RTYPE}")
print(f"x64 ctype (live)    : {CTYPE}")
print("--- op1: dy/dt=-y exponential decay ---")
print(f"decay state dtype   : {decay_state_dtype}")
print(f"y(1) computed       : {y1_computed!r}")
print(f"y(1) known exp(-1)  : {y1_known!r}")
print(f"decay abs err       : {decay_err:.3e}")
print(f"decay match         : {decay_match}")
print("--- op2: unitary norm preservation ---")
print(f"psi state dtype     : {psi_state_dtype}")
print(f"||psi(2.3)|| comp   : {norm_computed!r}")
print(f"||psi|| known       : {norm_known!r}")
print(f"norm abs err        : {norm_err:.3e}")
print(f"norm match          : {norm_match}")
print("--- aggregate ---")
print(f"ALL_MATCH           : {all_match}")
print(f"x64_honored         : {RTYPE == 'float64' and CTYPE == 'complex128'}")
