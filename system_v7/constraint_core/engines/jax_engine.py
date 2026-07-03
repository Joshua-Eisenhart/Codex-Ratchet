"""
jax_engine.py -- the 16-stage engine as a pure-functional JAX kernel.

Substrate contract (spec 8b): pure functions, no hidden mutable state, explicit
composition, vmap over the 16 stages, float64 enforced. Emits
engines/jax_results.json in the same schema as targets.json; validate with
validate_engines.py.

Design: each terrain generator is a fixed 4x4 superoperator matrix acting on
vec(rho) (column-stacking). The terrain flow is one matrix exponential
expm(T * L) -- exact, no RK4 truncation -- so agreement with the numpy RK4
oracle within 1e-6 is a genuine two-method cross-check, not a re-run.
Operators are exact channel maps. The whole 16-stage sweep is a single
vmapped, jitted call.
scratch_diagnostic; promotion_allowed=false.
"""
import json, os
import numpy as _np

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "targets.json")))["model_constants"]
G, KAP, Q, TH, T_FLOW = C["G"], C["KAP"], C["Q"], C["TH"], C["T_FLOW"]
PROBE = C["PROBE"]

I2 = jnp.eye(2, dtype=jnp.complex128)
sx = jnp.array([[0, 1], [1, 0]], jnp.complex128)
sy = jnp.array([[0, -1j], [1j, 0]], jnp.complex128)
sz = jnp.array([[1, 0], [0, -1]], jnp.complex128)
sp = 0.5 * (sx + 1j * sy); sm = 0.5 * (sx - 1j * sy)

def sprod_left(A):   # superoperator of rho -> A rho
    return jnp.kron(jnp.eye(2, dtype=jnp.complex128), A)

def sprod_right(A):  # superoperator of rho -> rho A
    return jnp.kron(A.T, jnp.eye(2, dtype=jnp.complex128))

def super_D(L):
    Ld = L.conj().T
    return (sprod_left(L) @ sprod_right(Ld)
            - 0.5 * (sprod_left(Ld @ L) + sprod_right(Ld @ L)))

def super_comm(H):
    return -1j * (sprod_left(H) - sprod_right(H))

TERR = {0: (+1, 'damp', +1), 1: (+1, 'depol', 0), 2: (+1, 'damp', -1), 3: (+1, 'proj', 0),
        4: (-1, 'damp', -1), 5: (-1, 'depol', 0), 6: (-1, 'damp', +1), 7: (-1, 'proj', 0)}
NATIVE = {0: ('Ti', 'Fi'), 1: ('Ti', 'Fi'), 4: ('Ti', 'Fi'), 5: ('Ti', 'Fi'),
          2: ('Te', 'Fe'), 3: ('Te', 'Fe'), 6: ('Te', 'Fe'), 7: ('Te', 'Fe')}

def terrain_super(ti):
    eps, kind, pole = TERR[ti]
    H0 = (sx + sy + sz) / jnp.sqrt(3.0)
    Lsup = G * super_comm(eps * H0)
    if kind == 'damp':
        Lsup = Lsup + KAP * super_D(sp if pole > 0 else sm)
    elif kind == 'depol':
        Lsup = Lsup + 0.5 * KAP * (super_D(sx) + super_D(sy))
    else:
        Lsup = Lsup + KAP * super_D(sz)
    return Lsup

def op_super(name):
    P0 = 0.5 * (I2 + sz); P1 = 0.5 * (I2 - sz)
    Qp = 0.5 * (I2 + sx); Qm = 0.5 * (I2 - sx)
    if name == 'Ti':
        return ((1 - Q) * jnp.eye(4, dtype=jnp.complex128)
                + Q * (sprod_left(P0) @ sprod_right(P0) + sprod_left(P1) @ sprod_right(P1)))
    if name == 'Te':
        return ((1 - Q) * jnp.eye(4, dtype=jnp.complex128)
                + Q * (sprod_left(Qp) @ sprod_right(Qp) + sprod_left(Qm) @ sprod_right(Qm)))
    U = expm(-1j * TH / 2 * (sx if name == 'Fi' else sz))
    return sprod_left(U) @ sprod_right(U.conj().T)

def vec(rho):
    return rho.T.reshape(4)      # column stacking

def unvec(v):
    return v.reshape(2, 2).T

def bloch(rho):
    return jnp.stack([jnp.trace(rho @ s).real for s in (sx, sy, sz)])

STAGE_LIST = [(t, o) for t in range(8) for o in NATIVE[t]]
T_SUPERS = jnp.stack([terrain_super(t) for t, _ in STAGE_LIST])
O_SUPERS = jnp.stack([op_super(o) for _, o in STAGE_LIST])

@jax.jit
def run_all_stages(probe_vec):
    def one(Ts, Os):
        Uflow = expm(T_FLOW * Ts)                    # exact semigroup step
        down = Os @ (Uflow @ probe_vec)              # terrain-first
        up = Uflow @ (Os @ probe_vec)                # operator-first
        return bloch(unvec(down)), bloch(unvec(up))
    return jax.vmap(one)(T_SUPERS, O_SUPERS)

def main():
    probe = 0.5 * (I2 + PROBE[0] * sx + PROBE[1] * sy + PROBE[2] * sz)
    downs, ups = run_all_stages(vec(probe))
    downs, ups = _np.asarray(downs), _np.asarray(ups)
    stages = []
    for i, (t, o) in enumerate(STAGE_LIST):
        gap = float(_np.linalg.norm(downs[i] - ups[i]))
        stages.append({"t": t, "op": o,
                       "bloch_down": [float(x) for x in downs[i]],
                       "bloch_up": [float(x) for x in ups[i]],
                       "order_gap": gap})
    terrains = []
    for t in range(8):
        Ls = terrain_super(t)
        LI = unvec(Ls @ vec(I2))
        fp = unvec(_np.asarray(expm(8.0 * Ls)) @ _np.asarray(vec(probe)))
        fp = fp / _np.trace(fp).real
        terrains.append({"t": t,
                         "nonunital": int(float(jnp.linalg.norm(LI)) > 1e-9),
                         "fixed_z": float(_np.trace(fp @ _np.asarray(sz)).real)})
    json.dump({"substrate": "jax", "x64": True, "stages": stages, "terrains": terrains},
              open(os.path.join(HERE, "jax_results.json"), "w"), indent=1)
    print(f"jax_results.json written ({len(stages)} stages); "
          f"backend={jax.default_backend()}, x64 on")

if __name__ == "__main__":
    main()
