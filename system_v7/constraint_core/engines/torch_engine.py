"""
torch_engine.py -- the 16-stage engine on PyTorch (complex128, CPU or CUDA).

Third independent numerical route: torch.linalg.matrix_exp on the batched
(16,4,4) superoperator stack, one batched call for all stages. Emits
engines/torch_results.json; validate with validate_engines.py.
scratch_diagnostic; promotion_allowed=false.
"""
import json, os
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(HERE, "targets.json")))["model_constants"]
G, KAP, Q, TH, T_FLOW = C["G"], C["KAP"], C["Q"], C["TH"], C["T_FLOW"]
PROBE = C["PROBE"]

dev = "cuda" if torch.cuda.is_available() else "cpu"
dt = torch.complex128
I2 = torch.eye(2, dtype=dt, device=dev)
sx = torch.tensor([[0, 1], [1, 0]], dtype=dt, device=dev)
sy = torch.tensor([[0, -1j], [1j, 0]], dtype=dt, device=dev)
sz = torch.tensor([[1, 0], [0, -1]], dtype=dt, device=dev)
sp = 0.5 * (sx + 1j * sy); sm = 0.5 * (sx - 1j * sy)
H0 = (sx + sy + sz) / np.sqrt(3.0)

def kron(A, B):
    return torch.kron(A.contiguous(), B.contiguous())

def sL(A):  # rho -> A rho
    return kron(torch.eye(2, dtype=dt, device=dev), A)

def sR(A):  # rho -> rho A
    return kron(A.T, torch.eye(2, dtype=dt, device=dev))

def sD(L):
    Ld = L.conj().T
    return sL(L) @ sR(Ld) - 0.5 * (sL(Ld @ L) + sR(Ld @ L))

def sC(H):
    return -1j * (sL(H) - sR(H))

TERR = {0: (+1, 'damp', +1), 1: (+1, 'depol', 0), 2: (+1, 'damp', -1), 3: (+1, 'proj', 0),
        4: (-1, 'damp', -1), 5: (-1, 'depol', 0), 6: (-1, 'damp', +1), 7: (-1, 'proj', 0)}
NATIVE = {0: ('Ti', 'Fi'), 1: ('Ti', 'Fi'), 4: ('Ti', 'Fi'), 5: ('Ti', 'Fi'),
          2: ('Te', 'Fe'), 3: ('Te', 'Fe'), 6: ('Te', 'Fe'), 7: ('Te', 'Fe')}

def terrain_super(ti):
    eps, kind, pole = TERR[ti]
    Ls = G * sC(eps * H0)
    if kind == 'damp':
        Ls = Ls + KAP * sD(sp if pole > 0 else sm)
    elif kind == 'depol':
        Ls = Ls + 0.5 * KAP * (sD(sx) + sD(sy))
    else:
        Ls = Ls + KAP * sD(sz)
    return Ls

def op_super(name):
    P0 = 0.5 * (I2 + sz); P1 = 0.5 * (I2 - sz)
    Qp = 0.5 * (I2 + sx); Qm = 0.5 * (I2 - sx)
    E4 = torch.eye(4, dtype=dt, device=dev)
    if name == 'Ti':
        return (1 - Q) * E4 + Q * (sL(P0) @ sR(P0) + sL(P1) @ sR(P1))
    if name == 'Te':
        return (1 - Q) * E4 + Q * (sL(Qp) @ sR(Qp) + sL(Qm) @ sR(Qm))
    U = torch.linalg.matrix_exp(-1j * TH / 2 * (sx if name == 'Fi' else sz))
    return sL(U) @ sR(U.conj().T)

def vec(rho):
    return rho.T.reshape(4)

def unvec(v):
    return v.reshape(2, 2).T

def bloch(rho):
    return [float(torch.trace(rho @ s).real) for s in (sx, sy, sz)]

def main():
    stage_list = [(t, o) for t in range(8) for o in NATIVE[t]]
    Ts = torch.stack([terrain_super(t) for t, _ in stage_list])       # (16,4,4)
    Os = torch.stack([op_super(o) for _, o in stage_list])
    flows = torch.linalg.matrix_exp(T_FLOW * Ts)                      # batched
    probe = 0.5 * (I2 + PROBE[0] * sx + PROBE[1] * sy + PROBE[2] * sz)
    pv = vec(probe)
    stages = []
    for i, (t, o) in enumerate(stage_list):
        down = unvec(Os[i] @ (flows[i] @ pv))
        up = unvec(flows[i] @ (Os[i] @ pv))
        bd, bu = bloch(down), bloch(up)
        stages.append({"t": t, "op": o, "bloch_down": bd, "bloch_up": bu,
                       "order_gap": float(np.linalg.norm(np.array(bd) - np.array(bu)))})
    terrains = []
    for t in range(8):
        Ls = terrain_super(t)
        LI = unvec(Ls @ vec(I2))
        fp = unvec(torch.linalg.matrix_exp(8.0 * Ls) @ pv)
        fp = fp / torch.trace(fp).real
        terrains.append({"t": t,
                         "nonunital": int(float(torch.linalg.norm(LI)) > 1e-9),
                         "fixed_z": float(torch.trace(fp @ sz).real)})
    json.dump({"substrate": "torch", "device": dev, "stages": stages, "terrains": terrains},
              open(os.path.join(HERE, "torch_results.json"), "w"), indent=1)
    print(f"torch_results.json written (16 stages) on {dev}, torch {torch.__version__}")

if __name__ == "__main__":
    main()
