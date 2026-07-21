import json, os
from pathlib import Path
KNOB = 1.0                      # a load-bearing coupling
def main():
    checks = {}
    checks["genuine_depends_on_knob"] = bool(KNOB > 0.5)   # flips when KNOB severed
    checks["byconstruction_identity"] = bool(2 + 2 == 4)   # cannot fail, ever
    out = Path(__file__).resolve().parent / "results" / "toy"
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipt.json").write_text(json.dumps({"checks": checks, "all_pass": all(checks.values())}))
if __name__ == "__main__":
    main()
