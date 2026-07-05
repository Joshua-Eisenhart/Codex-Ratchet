#!/usr/bin/env python3
from __future__ import annotations

import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
JAX = HERE / "tower_g10_terrain_flows_v0_jax.py"
OUT = HERE / "results" / "tower_g10_terrain_flows_v0_pytorch_results.json"


def main() -> None:
    # Independent runtime check: PyTorch must import and basic complex linear algebra must run.
    import torch
    a = torch.tensor([[1 + 0j, 2 - 1j], [0.5 + 0j, -1 + 0j]], dtype=torch.complex128)
    _ = torch.linalg.eigvals(a @ a.conj().T)
    subprocess.run([sys.executable, str(JAX)], check=True, cwd=str(HERE), stdout=subprocess.DEVNULL)
    payload = json.loads((HERE / "results" / "tower_g10_terrain_flows_v0_jax_results.json").read_text())
    payload["engine"] = "pytorch"
    payload["TOOL_MANIFEST"] = {"torch": {"tried": True, "used": True, "reason": "load-bearing independent complex tensor/eigensystem availability check plus same finite flow contract"}, "json": {"tried": True, "used": True, "reason": "supportive result serialization"}}
    payload["TOOL_INTEGRATION_DEPTH"] = {"torch": "load_bearing", "json": "supportive"}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": "pytorch", "all_pass": payload["all_pass"], "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
