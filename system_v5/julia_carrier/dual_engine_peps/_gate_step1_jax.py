"""BOUNDED gate step 1 (hard-capped ~120s by the shell wrapper).

Reuse jax_ipeps_heisenberg.energy_torus (EXACT finite-torus energy) as the
OPTIMIZER target and the REFERENCE. Light-optimize a D=2 iPEPS tensor (tens of
steps only — do NOT chase the true GS), SAVE it to ipeps_heisenberg_D2.npy
([p,u,r,d,l], complex128), and write TENSOR_FORMAT.md with index order, the
exact torus energy at L=4,5,6, the Hamiltonian convention, and jax_energy for
the Julia handshake.

The prior optimizer's KEY finding: hand-rolled JAX CTMRG gives -0.30 for an
optimized tensor while the EXACT torus contraction gives -0.577 (L=4/5/6 agree)
=> CTMRG is unreliable for structured tensors. So we use the TORUS energy, not
the CTMRG energy, as the optimizer target and the reference.
"""

import jax

jax.config.update("jax_enable_x64", True)

import json
import time
from functools import partial

import jax.numpy as jnp
import numpy as np
import optax

import jax_ipeps_heisenberg as M  # reuse: energy_torus, init_tensor

HERE = "/Users/joshuaeisenhart/Desktop/Codex Ratchet/system_v5/julia_carrier/dual_engine_peps"
D = 2
L_OPT = 4          # optimize against the L=4 torus energy (cheap: ~0.02s/step jitted)
N_STEPS = 120      # light optimization, tens of steps (still ~1s total)
LR = 5e-2

t0 = time.time()

# ---- light optimization against the EXACT torus energy (L=L_OPT) ----
key = jax.random.PRNGKey(7)
T = M.init_tensor(D, key)

loss = partial(M.energy_torus, L=L_OPT)
vg = jax.value_and_grad(loss)
opt = optax.adam(LR)
state = opt.init(T)


@jax.jit
def step(T, state):
    e, g = vg(T)
    updates, state = opt.update(g, state, T)
    T = optax.apply_updates(T, updates)
    return T, state, e


best_e = float("inf")
best_T = T
hist = []
for it in range(N_STEPS):
    T, state, e = step(T, state)
    e = float(jnp.real(e))
    hist.append(round(e, 6))
    if np.isfinite(e) and e < best_e:
        best_e = e
        best_T = T
    if it % 10 == 0 or it == N_STEPS - 1:
        print(f"  [D={D}] step {it:3d}  E_torus(L={L_OPT})/site = {e:.6f}  ({time.time()-t0:.1f}s)")

# ---- exact torus energy of the OPTIMIZED tensor at L=4,5,6 (the REFERENCE) ----
torus = {}
for L in (4, 5, 6):
    e_site = float(jnp.real(M.energy_torus(best_T, L=L)))
    torus[L] = e_site
    print(f"  exact torus L={L}: E/site = {e_site:.6f}  ({time.time()-t0:.1f}s)")

# JAX-CTMRG energy of the SAME structured tensor (expected to diverge, per the
# prior finding). Best-effort; do not let it blow the cap.
jax_ctmrg = None
try:
    jax_ctmrg = float(jnp.real(M.energy_of_tensor(best_T, chi=16, n_iter=40)))
    print(f"  jax-CTMRG chi=16: E/site = {jax_ctmrg:.6f}  ({time.time()-t0:.1f}s)")
except Exception as exc:  # noqa: BLE001
    print(f"  jax-CTMRG failed: {exc}")

# ---- SAVE the structured tensor ----
path = f"{HERE}/ipeps_heisenberg_D2.npy"
np.save(path, np.asarray(best_T, dtype=np.complex128))
print(f"  saved {path}  shape={np.asarray(best_T).shape}")

# reference energy the Julia lane compares to = the exact torus at the largest L
ref_torus = torus[6]

# ---- TENSOR_FORMAT.md (Julia reads Jx/Jy/Jz and jax_energy from here) ----
fmt = f"""# TENSOR_FORMAT — dual-engine PEPS handshake (D=2 structured iPEPS tensor)

## Tensor
- File: `ipeps_heisenberg_D2.npy`
- Shape: `[p, u, r, d, l]` = (physical=2, up=D, right=D, down=D, left=D), D={D}
- dtype: `complex128`
- Ansatz: single-site (1x1 unit cell) iPEPS, sublattice pi-rotation folded in.
- This tensor is a LIGHT-OPTIMIZED structured/physical tensor (not the true GS);
  it was optimized against the EXACT L={L_OPT} torus energy for {N_STEPS} Adam steps.

## Hamiltonian convention
- S=1/2 antiferromagnetic Heisenberg, infinite square lattice.
- Jx: 1.0
- Jy: 1.0
- Jz: 1.0
- spin: 1//2
- Rotated bond used by the JAX optimizer: `H_rot = -SxSx - SySy + SzSz`
  (sublattice pi-rotation; equals true AFM per-site energy since the rotation is
  a local unitary). PEPSKit's `heisenberg_XYZ` with Jx=Jy=Jz=1.0 contracts the
  SAME tensor with the rotation folded into the saved tensor.
- Per-site energy = 2 * <H>_bond (2 bonds/site on the square lattice).

## EXACT finite-torus energy of THIS tensor (the REFERENCE — trust this, NOT CTMRG)
- This is a true Rayleigh quotient <psi|H|psi>/<psi|psi> on an L x L periodic
  lattice: no eigendecomposition, no truncation, always a valid variational bound.
- torus L=4: E/site = {torus[4]:.6f}
- torus L=5: E/site = {torus[5]:.6f}
- torus L=6: E/site = {torus[6]:.6f}

## Handshake target for the Julia/PEPSKit CTMRG cross-check
- jax_energy_per_site = {ref_torus:.6f}    (the L=6 exact torus energy)
- Compare PEPSKit CTMRG per-site energy to THIS value.
- Prior finding: the hand-rolled JAX CTMRG diverges from the exact torus energy
  for structured tensors (gave -0.30 vs torus -0.577). CTMRG is reliable only for
  random tensors. The exact torus energy is the ground truth here.

## JAX-CTMRG energy of this same tensor (for the record; expected to diverge)
- jax_ctmrg_chi16_per_site = {jax_ctmrg if jax_ctmrg is not None else 'NaN'}
"""
with open(f"{HERE}/TENSOR_FORMAT.md", "w") as f:
    f.write(fmt)
print(f"  wrote {HERE}/TENSOR_FORMAT.md")

# sidecar for the comparison step
side = {
    "D": D,
    "L_opt": L_OPT,
    "n_steps": N_STEPS,
    "exact_torus_per_site": torus,
    "reference_torus_L6": ref_torus,
    "jax_ctmrg_chi16_per_site": jax_ctmrg,
    "opt_history_torus": hist,
    "best_e_torus_Lopt": best_e,
    "tensor_path": path,
    "wall_sec": round(time.time() - t0, 2),
}
with open(f"{HERE}/_gate_jax_side.json", "w") as f:
    json.dump(side, f, indent=2)
print(f"  wrote {HERE}/_gate_jax_side.json   wall={side['wall_sec']}s")
print("STEP1_DONE")
