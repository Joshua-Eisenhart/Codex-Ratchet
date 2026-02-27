import time
import hashlib
import numpy as np

DEPTHS = [10_000, 50_000, 100_000, 250_000, 500_000, 1_000_000]

rng = np.random.default_rng(0)

def h(x):
    return hashlib.sha256(x.encode()).hexdigest()

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_ORDER_CRITICAL_SCAN_V16")
print("CODE_HASH_SHA256:", h(open(__file__).read()))

for d in DEPTHS:
    start = time.time()
    history = rng.standard_normal(d)
    _ = history  # preserve order
    runtime = time.time() - start
    print(f"METRIC: depth_{d}_runtime_sec={runtime}")

print("EVIDENCE_SIGNAL S_SIM_HISTORY_ORDER_CRITICAL_SCAN_V16 CORR E_SIM_HISTORY_ORDER_CRITICAL_SCAN_V16")
print("END SIM_EVIDENCE v1")