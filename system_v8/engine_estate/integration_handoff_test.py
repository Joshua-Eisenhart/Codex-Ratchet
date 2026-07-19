#!/usr/bin/env python3
"""Integration handoff test — system_v8 engine estate, Integration phase.

ONE manifold quantity computed by handoff across the three engines via JSON
files, with each engine stack loaded in its OWN sequential subprocess:

  1. torch subprocess  — builds the continuation digraph + capacity complex of
     the gcm_completion_projection packet as torch_geometric graphs; exports
     the node-weight distribution p0 = (1 + out-degree)/sum.
  2. jax subprocess    — batched (vmap) amplitude-damping entropy sweep
     S(gamma) = sum_i h(e_i e^{-gamma T}) over a 64-point gamma grid, with
     excitation profile e = p0/max(p0); exports gamma* = argmax and q*.
  3. julia subprocess  — authoritative GKSL master-equation integration
     (QuantumOptics, reltol 1e-12) of each node's amplitude-damping channel at
     gamma*; chained value S_master = sum_i S_vN(rho_i(T)).

Control: this orchestrator process (numpy + stdlib ONLY — no engine stack)
recomputes the ENTIRE chain single-process and gates

    |S_master(julia chain) - S_control(numpy)| < 1e-8 .

Ceiling: working-sim estate probe. promotion_allowed: false. NOT proof-level.
Receipt: results/integration/receipt.json
"""
import json
import os
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUTDIR = os.path.join(HERE, "results", "integration")
os.makedirs(OUTDIR, exist_ok=True)

TORCH_PY = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
JAX_PY = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
JULIA = "/opt/homebrew/bin/julia"

receipt = {
    "engine": "integration",
    "phase": "system_v8 engine_estate Integration phase (torch -> jax -> julia handoff)",
    "date": "2026-07-19",
    "orchestrator_python": sys.version,
    "orchestrator_interpreter": sys.executable,
    "promotion_allowed": False,
    "claim_ceiling": "working-sim estate probe; not canonical, not proof-level",
    "chain": "torch(graph weights) -> jax(batched entropy sweep) -> julia(GKSL master integration)",
    "checks": {},
    "timings": {},
    "stage_interpreters": {},
    "versions": {},
    "blocked": [],
    "findings": [],
}


def check(name, ok, detail=""):
    receipt["checks"][name] = {"pass": bool(ok), "detail": str(detail)}
    print(f"[{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    return bool(ok)


def run_stage(name, cmd):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    dt = time.perf_counter() - t0
    receipt["timings"][f"{name}_stage_s"] = dt
    print(f"--- {name} stage (exit {r.returncode}, {dt:.2f}s) ---")
    print(r.stdout, end="")
    if r.returncode != 0:
        print(r.stderr[-3000:], file=sys.stderr)
        receipt["blocked"].append({"stage": name, "error": r.stderr[-1500:]})
    check(f"stage_{name}_exit0", r.returncode == 0, f"exit {r.returncode}")
    return r.returncode == 0


# guard: the orchestrator must not itself load an engine stack
assert "torch" not in sys.modules and "jax" not in sys.modules

# memory gate (>30% free required before loading any stack)
mp = subprocess.run(["memory_pressure"], capture_output=True, text=True)
free_line = [l for l in mp.stdout.splitlines() if "free percentage" in l]
free_pct = int(free_line[0].split(":")[1].strip().rstrip("%")) if free_line else -1
check("memory_free_gt_30pct", free_pct > 30, f"system free {free_pct}%")

# ------------------------------------------------ sequential engine stages
ok_t = run_stage("torch", [TORCH_PY, os.path.join(HERE, "integration_stage_torch.py")])
ok_j = ok_t and run_stage("jax", [JAX_PY, os.path.join(HERE, "integration_stage_jax.py")])
ok_u = ok_j and run_stage("julia", [JULIA, os.path.join(HERE, "integration_stage_julia.jl")])

h_torch = h_jax = h_julia = None
if ok_t:
    with open(os.path.join(OUTDIR, "handoff_torch.json")) as f:
        h_torch = json.load(f)
    receipt["versions"].update(h_torch["versions"])
    receipt["stage_interpreters"]["torch"] = h_torch["interpreter"]
if ok_j:
    with open(os.path.join(OUTDIR, "handoff_jax.json")) as f:
        h_jax = json.load(f)
    receipt["versions"].update(h_jax["versions"])
    receipt["stage_interpreters"]["jax"] = h_jax["interpreter"]
if ok_u:
    with open(os.path.join(OUTDIR, "handoff_julia.json")) as f:
        h_julia = json.load(f)
    receipt["versions"]["julia"] = h_julia["julia_version"]
    receipt["stage_interpreters"]["julia"] = JULIA

# ------------------------------------------------ single-process numpy control
t0 = time.perf_counter()
with open(os.path.join(HERE, "..", "manifold", "results",
                       "source_packets.json")) as f:
    src = json.load(f)
pkt = next(p for p in src["base_packets"]
           if p["packet_id"] == "gcm_completion_projection")
words = pkt["accepted_words"]
n = len(words)
HALF = pkt["width"] // 2
ins = {}
for k, w in enumerate(words):
    ins.setdefault(w[:HALF], set()).add(k)
cont = {k: frozenset(ins.get(w[HALF:], frozenset()))
        for k, w in enumerate(words)}
outdeg = np.array([len(cont[k]) for k in range(n)], dtype=np.float64)
wts = 1.0 + outdeg
p0_c = wts / wts.sum()

e_c = p0_c / p0_c.max()
T = 0.7
gammas_c = np.linspace(0.05, 3.0, 64)


def binent(q):
    q = np.clip(q, 1e-300, 1.0)
    r = np.clip(1.0 - q, 1e-300, 1.0)
    return -(q * np.log(q) + r * np.log(r))


S_c = np.array([binent(e_c * np.exp(-g * T)).sum() for g in gammas_c])
k_c = int(np.argmax(S_c))
gamma_c = float(gammas_c[k_c])
q_c = e_c * np.exp(-gamma_c * T)
S_control = float(binent(q_c).sum())
receipt["timings"]["numpy_control_s"] = time.perf_counter() - t0
receipt["numpy_control"] = {
    "p0": p0_c.tolist(), "k_star": k_c, "gamma_star": gamma_c,
    "S_control": S_control,
}
print(f"--- numpy control ---\nk*={k_c} gamma*={gamma_c:.6f} "
      f"S_control={S_control:.12f}")

# ------------------------------------------------ cross-engine gates (code)
all_stage = ok_t and ok_j and ok_u
if all_stage:
    dev_p0 = float(np.max(np.abs(np.array(h_torch["p0"]) - p0_c)))
    check("torch_p0_matches_numpy_control", dev_p0 < 1e-12,
          f"max|p0_torch - p0_numpy| = {dev_p0:.3e}")

    dev_S = float(np.max(np.abs(np.array(h_jax["S_sweep"]) - S_c)))
    check("jax_sweep_matches_numpy_control", dev_S < 1e-12,
          f"max|S_jax - S_numpy| over 64 gammas = {dev_S:.3e}")
    check("argmax_gamma_agrees", h_jax["k_star"] == k_c,
          f"jax k*={h_jax['k_star']} vs numpy k*={k_c} "
          f"(gamma*={h_jax['gamma_star']:.6f})")
    check("argmax_interior_not_boundary", h_jax["argmax_interior"],
          f"k*={h_jax['k_star']} in (0, 63) — sweep load-bearing")

    check("julia_gksl_law_1e-9", h_julia["gksl_law_check_pass"],
          f"max|pop_master - q*| = {h_julia['max_pop_dev_vs_analytic']:.3e} "
          f"(integrated master eq vs analytic damping law)")

    dev_chain = abs(h_julia["S_master"] - S_control)
    check("chained_value_matches_numpy_control_1e-8", dev_chain < 1e-8,
          f"|S_master(chain) - S_control(numpy)| = {dev_chain:.3e}; "
          f"S_master = {h_julia['S_master']:.12f}")
    receipt["chained_value"] = {
        "quantity": "sum_i S_vN(rho_i(T)) after GKSL amplitude damping at "
                    "gamma* selected by jax sweep on torch graph weights",
        "S_master_julia": h_julia["S_master"],
        "S_control_numpy": S_control,
        "abs_dev": dev_chain,
    }
else:
    receipt["findings"].append("one or more stages failed; chain gates not run")

npass = sum(1 for c in receipt["checks"].values() if c["pass"])
ntot = len(receipt["checks"])
receipt["checks_passed"] = npass
receipt["checks_total"] = ntot
receipt["all_pass"] = npass == ntot and all_stage
receipt["versions"]["numpy_control"] = np.__version__

out = os.path.join(OUTDIR, "receipt.json")
with open(out, "w") as f:
    json.dump(receipt, f, indent=1, sort_keys=True)
print(f"\n{npass}/{ntot} checks pass — all_pass={receipt['all_pass']}")
print(f"receipt: {out}")
sys.exit(0 if receipt["all_pass"] else 1)
