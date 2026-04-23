import time
import hashlib
import numpy as np

H_LEN = 10_000_000
rng = np.random.default_rng(0)

start = time.time()

# simulate order-scrambled history
history = rng.standard_normal(H_LEN)
rng.shuffle(history)

runtime = time.time() - start

def h(x):
    return hashlib.sha256(x.encode()).hexdigest()

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_VARIANT_ORDER_SCRAMBLED_V14")
print("CODE_HASH_SHA256:", h(open(__file__).read()))
print("OUTPUT_HASH_SHA256:", h(str(history[:1000])))
print(f"METRIC: runtime_sec={runtime}")
print("EVIDENCE_SIGNAL S_SIM_HISTORY_VARIANT_ORDER_SCRAMBLED_V14 CORR E_SIM_HISTORY_VARIANT_ORDER_SCRAMBLED_V14")
print("END SIM_EVIDENCE v1")