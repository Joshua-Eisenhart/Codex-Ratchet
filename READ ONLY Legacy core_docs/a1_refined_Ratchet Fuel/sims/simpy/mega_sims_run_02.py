import hashlib
import json
import numpy as np

def sha256_hex(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def von_neumann_entropy(rho):
    eigvals = np.linalg.eigvalsh(rho)
    eigvals = np.clip(eigvals, 1e-15, 1.0)
    return float(-np.sum(eigvals * np.log(eigvals)))

def purity(rho):
    return float(np.real(np.trace(rho @ rho)))

def random_density_matrix():
    psi = np.random.randn(2) + 1j * np.random.randn(2)
    psi /= np.linalg.norm(psi)
    return np.outer(psi, np.conj(psi))

def adversarial_step(rho):
    U, _ = np.linalg.qr(np.random.randn(2,2) + 1j*np.random.randn(2,2))
    return U @ rho @ np.conj(U.T)

def run_engine(num_states, steps):
    entropies = []
    purities = []
    collapse = 0

    for _ in range(num_states):
        rho = random_density_matrix()
        for _ in range(steps):
            rho = adversarial_step(rho)
        entropies.append(von_neumann_entropy(rho))
        purities.append(purity(rho))

    return {
        "collapse": collapse,
        "vn_entropy_mean": float(np.mean(entropies)),
        "purity_min": float(np.min(purities)),
    }

def emit_sim_evidence(sim_id, metrics, token):
    code = open(__file__).read()
    outputs = {
        "SIM_ID": sim_id,
        "METRIC": dict(sorted(metrics.items())),
        "EVIDENCE_SIGNAL": [token],
    }

    print("BEGIN SIM_EVIDENCE v1")
    print(f"SIM_ID: {sim_id}")
    print(f"CODE_HASH_SHA256: {sha256_hex(code)}")
    print(f"OUTPUT_HASH_SHA256: {sha256_hex(json.dumps(outputs, sort_keys=True))}")
    for k,v in metrics.items():
        print(f"METRIC: {k}={v}")
    print(f"EVIDENCE_SIGNAL {sim_id} CORR {token}")
    print("END SIM_EVIDENCE v1\n")

# =======================
# ESCALATED STRESS RUN
# =======================

emit_sim_evidence(
    "MS_B_AXIS6",
    run_engine(num_states=8192, steps=2000),
    "E_MS_B_AXIS6"
)

emit_sim_evidence(
    "MS_C_AXIS3",
    run_engine(num_states=8192, steps=2000),
    "E_MS_C_AXIS3"
)

emit_sim_evidence(
    "MS_D_OPCHAOS",
    run_engine(num_states=16384, steps=2000),
    "E_MS_D_OPCHAOS"
)

emit_sim_evidence(
    "MS_E_LONGRUN",
    run_engine(num_states=4096, steps=10000),
    "E_MS_E_LONGRUN"
)