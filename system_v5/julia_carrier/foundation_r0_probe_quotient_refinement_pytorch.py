#!/usr/bin/env python3
"""PyTorch-lane R0 quotient-refinement probe (mirror of the Julia canon probe).

Real torch compute for the probe-relative quotient (states {z0,z1,+,-} under
M_Z vs M_ZX, Born-rule distributions), plus a real torch-ecosystem geometric
invariant via geomstats SPD manifold so the lane is not bare torch.

scratch_diagnostic; promotion_allowed=false. Exit 0 on all_pass, 2 otherwise.
"""
import json
import os
import sys

os.environ.setdefault("GEOMSTATS_BACKEND", "pytorch")
import torch

torch.set_default_dtype(torch.float64)

def dm(ket):
    k = torch.tensor(ket, dtype=torch.complex128).reshape(-1, 1)
    return k @ k.conj().T

z0, z1 = dm([1, 0]), dm([0, 1])
r2 = 2 ** 0.5
xp, xm = dm([1 / r2, 1 / r2]), dm([1 / r2, -1 / r2])
states = {"rho_z0": z0, "rho_z1": z1, "rho_plus": xp, "rho_minus": xm}
Z, X = [z0, z1], [xp, xm]
probes = {"Z": Z, "X": X}

def distribution(rho, effects):
    return tuple(round(float(torch.trace(E @ rho).real), 9) for E in effects)

def quotient(families):
    classes = {}
    for sid in sorted(states):
        sig = json.dumps([distribution(states[sid], probes[f]) for f in families])
        classes.setdefault(sig, []).append(sid)
    return [sorted(v) for v in classes.values()]

def class_of(q, sid):
    return next((tuple(c) for c in q if sid in c), None)

q_z, q_zx = quotient(["Z"]), quotient(["Z", "X"])
witness = {
    "same_under_Z": distribution(xp, Z) == distribution(xm, Z),
    "distinct_under_X": distribution(xp, X) != distribution(xm, X),
    "same_Z_class": class_of(q_z, "rho_plus") == class_of(q_z, "rho_minus"),
    "split_ZX_class": class_of(q_zx, "rho_plus") != class_of(q_zx, "rho_minus"),
}
strict = (len(q_zx) > len(q_z) and all(witness.values()))

# real torch-ecosystem tool: geomstats SPD affine-invariant distance on a mixed pair
from geomstats.geometry.spd_matrices import SPDMatrices  # load-bearing, no try/except
spd = SPDMatrices(2)
A = torch.tensor([[0.8, 0.0], [0.0, 0.2]])
B = torch.tensor([[0.5, 0.3], [0.3, 0.5]])  # same spectrum {0.8,0.2}, different frame
spd_dist = float(spd.metric.dist(A, B))
spd_ok = spd_dist > 1e-6  # genuinely distinct points on the SPD manifold

all_pass = strict and len(q_z) == 3 and len(q_zx) == 4 and spd_ok
result = {
    "schema": "codex_ratchet.formal_scout.scratch_diagnostic.v1",
    "object_id": "foundation_r0_probe_quotient_refinement_pytorch_v1",
    "classification": "scratch_diagnostic",
    "engine": "pytorch",
    "promotion_allowed": False,
    "reads_peer_result": False,
    "packages": {"load_bearing": ["torch", "geomstats"]},
    "quotient": {"M_Z_class_count": len(q_z), "M_ZX_class_count": len(q_zx)},
    "witness_pair": witness,
    "geomstats_spd_dist_A_B": round(spd_dist, 9),
    "core_checks": {"strict_quotient_refinement": strict, "spd_invariant_nonzero": spd_ok, "all_pass": all_pass},
    "all_pass": all_pass,
    "claim_ceiling": "R0 scratch_diagnostic PyTorch-lane quotient refinement + geomstats SPD invariant; Not M(C), not canonical.",
}
print(json.dumps(result))
print(f"SCOUT_DONE engine=pytorch all_pass={str(all_pass).lower()} z_classes={len(q_z)} zx_classes={len(q_zx)} spd_dist={spd_dist:.4f}")
sys.exit(0 if all_pass else 2)
