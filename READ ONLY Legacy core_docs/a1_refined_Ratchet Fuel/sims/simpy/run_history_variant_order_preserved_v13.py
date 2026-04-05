import subprocess
import sys

SCRIPTS = [
    "run_history_invariant_gradient_scan_v11.py",
    "run_history_variant_gradient_scan_v12.py",
    "run_history_variant_order_preserved_v13.py",
]

for script in SCRIPTS:
    print(f"\n=== RUNNING {script} ===\n")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.stderr:
        print("ERROR:", result.stderr)