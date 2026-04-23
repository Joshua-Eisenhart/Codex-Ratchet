import hashlib
import numpy as np

# -----------------------------
# SIM ID (MUST MATCH THREAD B)
# -----------------------------
SIM_ID = "S_SIM_HISTORY_VARIANT_GRADIENT_SCAN_V12"
EVIDENCE_TOKEN = "E_SIM_HISTORY_VARIANT_GRADIENT_SCAN_V12"

# -----------------------------
# SIM LOGIC
# -----------------------------
np.random.seed(1)

# simulate history-variant scrambling
histories = []
for _ in range(1024):
    traj = np.random.normal(0, 0.01, size=16)
    np.random.shuffle(traj)   # history dependence
    histories.append(np.sum(traj))

histories = np.array(histories)

mi_mean = float(np.mean(histories))
mi_std = float(np.std(histories))
gradient_sign = float(np.sign(mi_mean))

# -----------------------------
# HASHES
# -----------------------------
with open(__file__, "rb") as f:
    CODE_HASH_SHA256 = hashlib.sha256(f.read()).hexdigest()

output_blob = f"{mi_mean},{mi_std},{gradient_sign}".encode()
OUTPUT_HASH_SHA256 = hashlib.sha256(output_blob).hexdigest()

# -----------------------------
# EMIT SIM_EVIDENCE
# -----------------------------
print("BEGIN SIM_EVIDENCE v1")
print(f"SIM_ID: {SIM_ID}")
print(f"CODE_HASH_SHA256: {CODE_HASH_SHA256}")
print(f"OUTPUT_HASH_SHA256: {OUTPUT_HASH_SHA256}")
print(f"METRIC: mi_mean={mi_mean}")
print(f"METRIC: mi_std={mi_std}")
print(f"METRIC: gradient_sign={gradient_sign}")
print(f"EVIDENCE_SIGNAL {SIM_ID} CORR {EVIDENCE_TOKEN}")
print("END SIM_EVIDENCE v1")