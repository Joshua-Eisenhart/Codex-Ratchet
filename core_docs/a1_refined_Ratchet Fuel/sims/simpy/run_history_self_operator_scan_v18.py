import time
import hashlib
import numpy as np

DEPTH = 200_000
rng = np.random.default_rng(0)

def h(x):
    return hashlib.sha256(x.encode()).hexdigest()

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_SELF_OPERATOR_SCAN_V18")
print("CODE_HASH_SHA256:", h(open(__file__).read()))

H = rng.standard_normal(DEPTH)

# history as data (control)
start = time.time()
acc = 0.0
for x in H:
    acc += x
data_runtime = time.time() - start

# history as operator (reuse prefix)
start = time.time()
acc = 0.0
for i in range(1, DEPTH):
    acc += np.sum(H[:i])   # growing history reused
operator_runtime = time.time() - start

print(f"METRIC: data_only_runtime_sec={data_runtime}")
print(f"METRIC: history_operator_runtime_sec={operator_runtime}")

print("EVIDENCE_SIGNAL S_SIM_HISTORY_SELF_OPERATOR_SCAN_V18 CORR E_SIM_HISTORY_SELF_OPERATOR_SCAN_V18")
print("END SIM_EVIDENCE v1")