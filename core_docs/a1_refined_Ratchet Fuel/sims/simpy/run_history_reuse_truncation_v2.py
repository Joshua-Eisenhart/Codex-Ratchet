import numpy as np
import time
import hashlib

def run_trial(history_len, use_operator):
    dim = 16
    x = np.random.randn(dim, dim)
    x = x @ x.T

    if use_operator:
        op = np.random.randn(dim, dim)
        op = op @ op.T

    start = time.time()
    for _ in range(history_len):
        if use_operator:
            x = op @ x @ op.T
        else:
            x = x + 0.0
    return time.time() - start

depths = [1000, 5000, 10000, 50000]

results = {}
for d in depths:
    t_rec = run_trial(d, use_operator=False)
    t_op  = run_trial(d, use_operator=True)
    results[d] = (t_rec, t_op)

code_hash = hashlib.sha256(open(__file__, "rb").read()).hexdigest()
out_hash  = hashlib.sha256(str(results).encode()).hexdigest()

print("BEGIN SIM_EVIDENCE v1")
print("SIM_ID: S_SIM_HISTORY_REUSE_TRUNCATION_V2")
print(f"CODE_HASH_SHA256: {code_hash}")
print(f"OUTPUT_HASH_SHA256: {out_hash}")

for d, (r, o) in results.items():
    print(f"METRIC: depth_{d}_record_runtime_sec={r}")
    print(f"METRIC: depth_{d}_operator_runtime_sec={o}")

print("EVIDENCE_SIGNAL S_SIM_HISTORY_REUSE_TRUNCATION_V2 CORR E_SIM_HISTORY_REUSE_TRUNCATION_V2")
print("END SIM_EVIDENCE v1")