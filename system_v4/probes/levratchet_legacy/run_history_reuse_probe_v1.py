import numpy as np
import time
import hashlib

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

np.random.seed(0)

N = 1000          # matrix size (safe, finite)
STEPS = 2000      # history depth

# ---------- HISTORY AS RECORD (DATA ONLY) ----------

x = np.random.randn(N, N)
x = x / np.linalg.norm(x)

t0 = time.time()
for _ in range(STEPS):
    x = x @ x.T
    x = x / np.linalg.norm(x)
t_record = time.time() - t0

record_hash = sha256_bytes(x.tobytes())

# ---------- HISTORY AS OPERATOR (SELF-ACTING) ----------

x = np.random.randn(N, N)
x = x / np.linalg.norm(x)

op = np.random.randn(N, N)
op = op / np.linalg.norm(op)

t0 = time.time()
for _ in range(STEPS):
    x = op @ x @ op.T
    x = x / np.linalg.norm(x)
t_operator = time.time() - t0

operator_hash = sha256_bytes(x.tobytes())

# ---------- OUTPUT ----------

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_REUSE_PROBE_V1")
print(f"CODE_HASH_SHA256: {sha256_bytes(open(__file__, 'rb').read())}")
print(f"OUTPUT_HASH_SHA256: {sha256_bytes((record_hash + operator_hash).encode())}")
print(f"METRIC: history_record_runtime_sec={t_record}")
print(f"METRIC: history_operator_runtime_sec={t_operator}")
print(f"METRIC: final_state_equal={record_hash == operator_hash}")
print("EVIDENCE_SIGNAL S_SIM_HISTORY_REUSE_PROBE_V1 CORR E_SIM_HISTORY_REUSE_PROBE_V1")
print("END SIM_EVIDENCE v1")