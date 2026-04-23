#!/usr/bin/env python3
# run_axis12_axis0_link_v1.py
# Produces:
#   results_axis12_axis0_link_v1.json
#   sim_evidence_pack_axis12_axis0_link_v1.txt  (3 SIM_EVIDENCE blocks)

from __future__ import annotations
import json, hashlib, os
import numpy as np

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

# ----------------------------
# basic matrices
# ----------------------------
I2 = np.eye(2, dtype=complex)
X = np.array([[0,1],[1,0]], dtype=complex)
Y = np.array([[0,-1j],[1j,0]], dtype=complex)
Z = np.array([[1,0],[0,-1]], dtype=complex)

def expm_2x2(a: np.ndarray) -> np.ndarray:
    w, v = np.linalg.eig(a)
    return (v @ np.diag(np.exp(w)) @ np.linalg.inv(v)).astype(complex)

def unitary_from_axis(n: np.ndarray, theta: float, sign: int) -> np.ndarray:
    n = n / np.linalg.norm(n)
    H = n[0]*X + n[1]*Y + n[2]*Z
    return expm_2x2(-1j * sign * theta * H)

def apply_unitary_A(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UA = np.kron(U, I2)
    out = UA @ rhoAB @ UA.conj().T
    return out / np.trace(out)

def apply_unitary_B(rhoAB: np.ndarray, U: np.ndarray) -> np.ndarray:
    UB = np.kron(I2, U)
    out = UB @ rhoAB @ UB.conj().T
    return out / np.trace(out)

CNOT = np.array([
    [1,0,0,0],
    [0,1,0,0],
    [0,0,0,1],
    [0,0,1,0],
], dtype=complex)

def apply_unitary_AB(rhoAB: np.ndarray, UAB: np.ndarray) -> np.ndarray:
    out = UAB @ rhoAB @ UAB.conj().T
    return out / np.trace(out)

def apply_kraus_A(rhoAB: np.ndarray, Ks: list[np.ndarray]) -> np.ndarray:
    out = np.zeros((4,4), dtype=complex)
    for K in Ks:
        KA = np.kron(K, I2)
        out += KA @ rhoAB @ KA.conj().T
    return out / np.trace(out)

# ----------------------------
# entropy / partial traces
# ----------------------------
def vn_entropy(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(rho).real
    w = np.clip(w, 1e-16, 1.0)
    return float(-(w * np.log(w)).sum())

def partial_trace_AB_to_A(rhoAB: np.ndarray) -> np.ndarray:
    rhoA = np.zeros((2,2), dtype=complex)
    for a in range(2):
        for ap in range(2):
            s = 0.0+0.0j
            for b in range(2):
                i = 2*a + b
                j = 2*ap + b
                s += rhoAB[i,j]
            rhoA[a,ap] = s
    return rhoA / np.trace(rhoA)

def partial_trace_AB_to_B(rhoAB: np.ndarray) -> np.ndarray:
    rhoB = np.zeros((2,2), dtype=complex)
    for b in range(2):
        for bp in range(2):
            s = 0.0+0.0j
            for a in range(2):
                i = 2*a + b
                j = 2*a + bp
                s += rhoAB[i,j]
            rhoB[b,bp] = s
    return rhoB / np.trace(rhoB)

def mi_and_sAgB(rhoAB: np.ndarray) -> tuple[float,float]:
    rhoA = partial_trace_AB_to_A(rhoAB)
    rhoB = partial_trace_AB_to_B(rhoAB)
    sab = vn_entropy(rhoAB)
    sa  = vn_entropy(rhoA)
    sb  = vn_entropy(rhoB)
    mi = sa + sb - sab
    sAgB = sab - sb
    return float(mi), float(sAgB)

# ----------------------------
# terrains on A
# ----------------------------
def terrain_Se(gamma: float) -> list[np.ndarray]:
    E0 = np.array([[1,0],[0,np.sqrt(1-gamma)]], dtype=complex)
    E1 = np.array([[0,np.sqrt(gamma)],[0,0]], dtype=complex)
    return [E0, E1]

def terrain_Ne(p: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-p) * I2
    K1 = np.sqrt(p) * X
    return [K0, K1]

def terrain_Ni(q: float) -> list[np.ndarray]:
    K0 = np.sqrt(1-q) * I2
    K1 = np.sqrt(q) * Z
    return [K0, K1]

def terrain_Si() -> list[np.ndarray]:
    return [I2]

TERRAIN = {
    "Se": lambda params: terrain_Se(params["gamma"]),
    "Ne": lambda params: terrain_Ne(params["p"]),
    "Ni": lambda params: terrain_Ni(params["q"]),
    "Si": lambda params: terrain_Si(),
}

# ----------------------------
# axis1/axis2 constraints (pure combinatorial)
# ----------------------------
SENI = frozenset(("Se","Ni"))
NESI = frozenset(("Ne","Si"))

SETA = {frozenset(("Se","Si")), frozenset(("Ne","Ni"))}
SETB = {frozenset(("Se","Ne")), frozenset(("Si","Ni"))}

def seq_edges_undirected(seq: list[str]) -> list[frozenset]:
    e = []
    for i in range(len(seq)):
        a = seq[i]
        b = seq[(i+1) % len(seq)]
        e.append(frozenset((a,b)))
    return e

def axis12_counts(seq: list[str], seta: set[frozenset], setb: set[frozenset]) -> dict:
    edges = seq_edges_undirected(seq)
    seni_within = 1 if SENI in edges else 0
    nesi_within = 1 if NESI in edges else 0
    seta_bad = sum(1 for ed in edges if ed not in seta)
    setb_bad = sum(1 for ed in edges if ed not in setb)
    return {
        "seni_within": int(seni_within),
        "nesi_within": int(nesi_within),
        "seta_bad": int(seta_bad),
        "setb_bad": int(setb_bad),
    }

# ----------------------------
# initial states
# ----------------------------
def random_ginibre_rhoAB(rng: np.random.Generator) -> np.ndarray:
    M = (rng.normal(size=(4,4)) + 1j*rng.normal(size=(4,4))).astype(complex)
    rho = M @ M.conj().T
    rho = rho / np.trace(rho)
    return rho

def bell_seed_state(rng: np.random.Generator) -> np.ndarray:
    phi = np.array([1,0,0,1], dtype=complex) / np.sqrt(2)  # |Phi+>
    rho = np.outer(phi, phi.conj())
    thA = rng.uniform(0, 2*np.pi)
    thB = rng.uniform(0, 2*np.pi)
    UA = expm_2x2(-1j * thA * Z)
    UB = expm_2x2(-1j * thB * X)
    rho = apply_unitary_A(rho, UA)
    rho = apply_unitary_B(rho, UB)
    return rho / np.trace(rho)

def run_seq_axis0_metrics(seq: list[str], *, rng: np.random.Generator,
                          trials: int, cycles: int, axis3_sign: int,
                          theta: float, n_vec: tuple[float,float,float],
                          params: dict, entangle_reps: int,
                          init_mode: str) -> dict:
    U = unitary_from_axis(np.array(n_vec,float), theta, axis3_sign)
    mi_list = []
    sagb_list = []
    for _ in range(trials):
        rho = bell_seed_state(rng) if init_mode == "bell" else random_ginibre_rhoAB(rng)
        for _c in range(cycles):
            for terr in seq:
                Ks = TERRAIN[terr](params)
                rho = apply_unitary_A(rho, U)
                rho = apply_kraus_A(rho, Ks)
                for _k in range(entangle_reps):
                    rho = apply_unitary_AB(rho, CNOT)
        mi, sagb = mi_and_sAgB(rho)
        mi_list.append(mi)
        sagb_list.append(sagb)
    mi_arr = np.array(mi_list, float)
    sg_arr = np.array(sagb_list, float)
    return {
        "MI_mean": float(mi_arr.mean()),
        "MI_min": float(mi_arr.min()),
        "MI_max": float(mi_arr.max()),
        "SAgB_mean": float(sg_arr.mean()),
        "SAgB_min": float(sg_arr.min()),
        "SAgB_max": float(sg_arr.max()),
        "neg_SAgB_frac": float(np.mean((sg_arr < 0.0).astype(float))),
    }

def run_variant(name: str, seta: set[frozenset], setb: set[frozenset], *,
                seed: int, trials: int, cycles: int,
                theta: float, n_vec: tuple[float,float,float],
                params: dict, entangle_reps: int) -> dict:
    rng = np.random.default_rng(seed)

    SEQ01 = ["Se","Ne","Ni","Si"]
    SEQ02 = ["Se","Si","Ni","Ne"]
    SEQ03 = ["Se","Ne","Si","Ni"]
    SEQ04 = ["Se","Si","Ne","Ni"]
    SEQS = {"SEQ01": SEQ01, "SEQ02": SEQ02, "SEQ03": SEQ03, "SEQ04": SEQ04}

    out = {"variant": name, "seed": seed, "trials": trials, "cycles": cycles,
           "theta": theta, "n_vec": list(n_vec),
           "terrain_params": dict(params), "entangle_reps": entangle_reps,
           "seqs": SEQS, "axis12": {}, "axis0": {}}

    for k, seq in SEQS.items():
        out["axis12"][k] = axis12_counts(seq, seta, setb)

    for k, seq in SEQS.items():
        out["axis0"][k] = {}
        for axis3_sign in (+1, -1):
            sign_key = "plus" if axis3_sign == +1 else "minus"
            out["axis0"][k][sign_key] = {}
            for init_mode in ("ginibre","bell"):
                m = run_seq_axis0_metrics(seq, rng=rng, trials=trials, cycles=cycles,
                                          axis3_sign=axis3_sign, theta=theta, n_vec=n_vec,
                                          params=params, entangle_reps=entangle_reps,
                                          init_mode=init_mode)
                out["axis0"][k][sign_key][init_mode] = m
    return out

def emit_block(sim_id: str, v: dict, code_hash: str) -> str:
    payload = json.dumps(v, sort_keys=True).encode("utf-8")
    oh = sha256_bytes(payload)

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append(f"SIM_ID: {sim_id}")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {oh}")

    a1 = v["axis12"]["SEQ01"]; a2 = v["axis12"]["SEQ02"]
    lines.append(f"METRIC: SEQ01_seni={a1['seni_within']}")
    lines.append(f"METRIC: SEQ01_nesi={a1['nesi_within']}")
    lines.append(f"METRIC: SEQ01_seta_bad={a1['seta_bad']}")
    lines.append(f"METRIC: SEQ01_setb_bad={a1['setb_bad']}")
    lines.append(f"METRIC: SEQ02_seni={a2['seni_within']}")
    lines.append(f"METRIC: SEQ02_nesi={a2['nesi_within']}")
    lines.append(f"METRIC: SEQ02_seta_bad={a2['seta_bad']}")
    lines.append(f"METRIC: SEQ02_setb_bad={a2['setb_bad']}")

    for sign_key in ("plus","minus"):
        for init_mode in ("ginibre","bell"):
            m1 = v["axis0"]["SEQ01"][sign_key][init_mode]
            m2 = v["axis0"]["SEQ02"][sign_key][init_mode]
            dmi = m2["MI_mean"] - m1["MI_mean"]
            ds  = m2["SAgB_mean"] - m1["SAgB_mean"]
            dn  = m2["neg_SAgB_frac"] - m1["neg_SAgB_frac"]
            lines.append(f"METRIC: {sign_key}_{init_mode}_dMI={dmi}")
            lines.append(f"METRIC: {sign_key}_{init_mode}_dSAgB={ds}")
            lines.append(f"METRIC: {sign_key}_{init_mode}_dNegFrac={dn}")

    # IMPORTANT: match the evidence tokens required by Thread B SIM_SPEC
    if sim_id == "S_SIM_AXIS12_AXIS0_LINK_CANON":
        evid = "E_SIM_AXIS12_AXIS0_LINK_CANON"
    elif sim_id == "S_SIM_AXIS12_AXIS0_LINK_SWAP":
        evid = "E_SIM_AXIS12_AXIS0_LINK_SWAP"
    elif sim_id == "S_SIM_AXIS12_AXIS0_LINK_RAND":
        evid = "E_SIM_AXIS12_AXIS0_LINK_RAND"
    else:
        evid = f"E_{sim_id}"

    lines.append(f"EVIDENCE_SIGNAL {sim_id} CORR {evid}")
    lines.append("END SIM_EVIDENCE v1")
    return "\n".join(lines)

def main():
    seed = 0
    trials = 128
    cycles = 16
    theta = 0.07
    n_vec = (0.3, 0.4, 0.866025403784)
    params = {"gamma": 0.02, "p": 0.02, "q": 0.02}
    entangle_reps = 1

    canon = run_variant("canon", SETA, SETB, seed=seed, trials=trials, cycles=cycles,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps)

    swap  = run_variant("swap", SETB, SETA, seed=seed, trials=trials, cycles=cycles,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps)

    rng = np.random.default_rng(seed)
    all_edges = [frozenset(("Se","Ne")), frozenset(("Ne","Ni")),
                 frozenset(("Ni","Si")), frozenset(("Si","Se")),
                 frozenset(("Se","Ni")), frozenset(("Ne","Si"))]
    pick = rng.choice(len(all_edges), size=2, replace=False)
    rand_seta = {all_edges[int(pick[0])], all_edges[int(pick[1])]}
    rand_setb = set(all_edges) - rand_seta
    randv = run_variant("rand", rand_seta, rand_setb, seed=seed, trials=trials, cycles=cycles,
                        theta=theta, n_vec=n_vec, params=params, entangle_reps=entangle_reps)

    out = {"canon": canon, "swap": swap, "rand": randv}

    raw = json.dumps(out, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)
    with open("results_axis12_axis0_link_v1.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    pack = []
    pack.append(emit_block("S_SIM_AXIS12_AXIS0_LINK_CANON", canon, code_hash))
    pack.append(emit_block("S_SIM_AXIS12_AXIS0_LINK_SWAP",  swap,  code_hash))
    pack.append(emit_block("S_SIM_AXIS12_AXIS0_LINK_RAND",  randv, code_hash))

    with open("sim_evidence_pack_axis12_axis0_link_v1.txt", "w", encoding="utf-8") as f:
        f.write("\n\n".join(pack) + "\n")

    print("DONE:")
    print("  results_axis12_axis0_link_v1.json")
    print("  sim_evidence_pack_axis12_axis0_link_v1.txt")

if __name__ == "__main__":
    main()