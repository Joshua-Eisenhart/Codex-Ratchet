import hashlib
import json
import numpy as np

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def random_density_matrix():
    psi = np.random.randn(2) + 1j*np.random.randn(2)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, np.conj(psi))

def detect_trivial_dynamics(num_states, steps):
    for _ in range(num_states):
        rho = random_density_matrix()
        for _ in range(steps):
            U, _ = np.linalg.qr(np.random.randn(2,2) + 1j*np.random.randn(2,2))
            rho = U @ rho @ np.conj(U.T)
        if np.real(np.trace(rho @ rho)) < 0.999999:
            return False
    return True

def emit_sim_evidence(sim_id, flag, token):
    code = open(__file__).read()
    outputs = {
        "SIM_ID": sim_id,
        "FLAG": flag,
        "EVIDENCE_SIGNAL": [token] if flag else [],
    }

    print("BEGIN SIM_EVIDENCE v1")
    print(f"SIM_ID: {sim_id}")
    print(f"CODE_HASH_SHA256: {sha256_hex(code)}")
    print(f"OUTPUT_HASH_SHA256: {sha256_hex(json.dumps(outputs, sort_keys=True))}")
    if flag:
        print(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    print("END SIM_EVIDENCE v1")
    print()

flag = detect_trivial_dynamics(num_states=4096, steps=5000)
emit_sim_evidence("MS_TRIVIAL_DETECT", flag, "E_MS_TRIVIAL")