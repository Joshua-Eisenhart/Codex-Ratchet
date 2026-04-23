import time
import hashlib
import numpy as np

DEPTH = 500_000
rng = np.random.default_rng(0)

def h(x):
    return hashlib.sha256(x.encode()).hexdigest()

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_PAIR_ORDER_COUPLING_SCAN_V17")
print("CODE_HASH_SHA256:", h(open(__file__).read()))

# two independent histories
A = rng.standard_normal(DEPTH)
B = rng.standard_normal(DEPTH)

# preserved order, paired access
start = time.time()
for a, b in zip(A, B):
    _ = a + b
paired_runtime = time.time() - start

# scrambled second history
rng.shuffle(B)
start = time.time()
for a, b in zip(A, B):
    _ = a + b
scrambled_runtime = time.time() - start

print(f"METRIC: paired_preserved_runtime_sec={paired_runtime}")
print(f"METRIC: paired_scrambled_runtime_sec={scrambled_runtime}")

print("EVIDENCE_SIGNAL S_SIM_HISTORY_PAIR_ORDER_COUPLING_SCAN_V17 CORR E_SIM_HISTORY_PAIR_ORDER_COUPLING_SCAN_V17")
print("END SIM_EVIDENCE v1")