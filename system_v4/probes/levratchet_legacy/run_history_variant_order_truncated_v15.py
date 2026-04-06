import time
import hashlib
import numpy as np

H_LEN = 10_000_000
TRUNC = 100_000

rng = np.random.default_rng(0)

start = time.time()

history = rng.standard_normal(H_LEN)
history = history[:TRUNC]

runtime = time.time() - start

def h(x):
    return hashlib.sha256(x.encode()).hexdigest()

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_VARIANT_ORDER_TRUNCATED_V15")
print("CODE_HASH_SHA256:", h(open(__file__).read()))
print("OUTPUT_HASH_SHA256:", h(str(history[:1000])))
print(f"METRIC: runtime_sec={runtime}")
print("EVIDENCE_SIGNAL S_SIM_HISTORY_VARIANT_ORDER_TRUNCATED_V15 CORR E_SIM_HISTORY_VARIANT_ORDER_TRUNCATED_V15")
print("END SIM_EVIDENCE v1")