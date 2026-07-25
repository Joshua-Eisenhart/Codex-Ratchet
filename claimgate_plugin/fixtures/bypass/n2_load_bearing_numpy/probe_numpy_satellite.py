#!/usr/bin/env python3
"""numpy in the CONTAINED role the owner rule allows — a downstream satellite.

It consumes numbers the engines already produced and does post-hoc bookkeeping.
It computes no observable of its own, so deleting this file changes no claimed
value; it only removes a convenience summary. That is what "contained" means
here, and it is why this fixture is expected to be ADMITTED.

Run it after the engine legs. It is deliberately NOT named probe_numpy.py: the
gate resolves an engine leg as <receipt-stem>_<engine>.py, and numpy is not an
engine in that sense.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SIM_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def leg(name):
    out = subprocess.run([SIM_PY, str(HERE / name)], capture_output=True, text=True, check=True)
    return json.loads([ln for ln in out.stdout.splitlines() if ln.strip().startswith("{")][-1])


jax_leg, torch_leg = leg("probe_jax.py"), leg("probe_torch.py")
keys = sorted(set(jax_leg) & set(torch_leg))
spread = np.array([abs(jax_leg[k] - torch_leg[k]) for k in keys], dtype=np.float64)
json.dump({"role": "downstream_satellite",
           "consumes": ["probe_jax.py", "probe_torch.py"],
           "produces_no_observable_of_its_own": True,
           "metrics_compared": keys,
           "max_abs_engine_spread": float(spread.max())},
          sys.stdout, indent=1)
print()
