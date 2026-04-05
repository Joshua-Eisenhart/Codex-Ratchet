import hashlib
import numpy as np
import sys
import time

# ---- CONFIG ----
MAX_STEPS = 10_000_000
PRINT_EVERY = 1

def sha256(data: bytes):
    return hashlib.sha256(data).hexdigest()

def simulate():
    history = []
    step = 0

    try:
        while step < MAX_STEPS:
            # artificial history growth to expose boundary
            history.append(np.random.rand())

            if step % PRINT_EVERY == 0:
                print(f"H_LEN = {len(history)}", flush=True)

            step += 1

    except MemoryError:
        print("MEMORY_ERROR")
        return b"MEMORY_ERROR"

    return b"COMPLETED"

if __name__ == "__main__":
    start = time.time()
    output = simulate()
    end = time.time()

    print("\nBEGIN SIM_EVIDENCE v1")
    print("SIM_ID: S_SIM_HISTORY_VARIANT_ORDER_PRESERVED_V13B")
    print("CODE_HASH_SHA256:", sha256(open(__file__, "rb").read()))
    print("OUTPUT_HASH_SHA256:", sha256(output))
    print("METRIC: runtime_sec=", end - start)
    print("END SIM_EVIDENCE v1")