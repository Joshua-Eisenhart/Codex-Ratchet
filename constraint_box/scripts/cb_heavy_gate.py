#!/usr/bin/env python3
"""cb_heavy_gate — CB LIGHT's deterministic gate over CB HEAVY.

The sim engines are NOT CB. Julia, JAX and PyTorch are a separate estate. CB
light is the lean core; CB heavy is the same core plus the sim engines. This
script is the piece CB light owns: it decides whether CB heavy is properly
installed AND integrated, and it refuses with named reasons when it is not.

Four separable questions per lane, never merged:

  DECLARED    the lane is a member in config/council_member_registry_v1.json
  INSTALLED   its module resolves in the project interpreter
  CAPABLE     a real computation runs and returns the right value
              (an import proves a package exists; it does not prove it works)
  INTEGRATED  some CB code actually calls it — a lane nothing calls is
              installed, not integrated, and the owner's distinction is exactly
              this one

Each lane is probed in a SUBPROCESS. CB light boots in about 0.6 s at 183 MB;
importing torch or qutip in this process would destroy that and make the light
tier untestable from inside itself. The subprocess also means one broken engine
cannot take the gate down.

No model decides anything here. Every refusal names its lane and its reason.

  cb_heavy_gate.py                 probe every lane, write a receipt
  cb_heavy_gate.py --lane jax      one lane
  cb_heavy_gate.py --declared-only skip capability probes (fast, no heavy import)
  cb_heavy_gate.py --install-plan  print what is missing, run nothing

promotion_allowed=false.
"""
from __future__ import annotations
import argparse, json, subprocess, sys, time
from pathlib import Path

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
CB = REPO / "constraint_box"
REG = CB / "config" / "council_member_registry_v1.json"
PY = str(Path.home() / ".local/share/codex-ratchet/envs/main/bin/python3")

# ---------------------------------------------------------------- capability probes
# Each probe must FAIL against a stub. "import x; print(x.__version__)" would
# pass against an empty shim, so every probe computes something with a known
# answer and asserts the value.
PROBES = {
 "lane.jax": ("jax", r'''
import jax, jax.numpy as jnp
f = jax.jit(lambda x: x * 2.0 + 1.0)
v = jax.vmap(f)(jnp.arange(4.0))
assert v.tolist() == [1.0, 3.0, 5.0, 7.0], v.tolist()
g = jax.grad(lambda x: x ** 3)(2.0)
assert abs(float(g) - 12.0) < 1e-5, g
print("jit+vmap+grad ok", jax.__version__)
'''),
 "lane.pytorch": ("torch", r'''
import torch
x = torch.tensor([2.0], requires_grad=True)
(x ** 3).sum().backward()
assert abs(float(x.grad) - 12.0) < 1e-5, x.grad
a = torch.linalg.eigvalsh(torch.tensor([[2.0, 0.0], [0.0, 3.0]]))
assert abs(float(a[0]) - 2.0) < 1e-6 and abs(float(a[1]) - 3.0) < 1e-6, a
print("autograd+linalg ok", torch.__version__)
'''),
 "lane.qutip_numpy": ("qutip", r'''
import qutip as qt
rho = (qt.basis(2, 0) * qt.basis(2, 0).dag() + qt.basis(2, 1) * qt.basis(2, 1).dag()) / 2
assert abs(rho.tr() - 1.0) < 1e-12, rho.tr()
assert abs(qt.entropy_vn(rho, base=2) - 1.0) < 1e-9, qt.entropy_vn(rho, base=2)
print("density matrix + von Neumann entropy ok", qt.__version__)
'''),
 "lane.diffrax": ("diffrax", r'''
import diffrax, jax.numpy as jnp
t = diffrax.diffeqsolve(diffrax.ODETerm(lambda t, y, a: -y), diffrax.Dopri5(),
                        t0=0.0, t1=1.0, dt0=0.01, y0=jnp.array(1.0))
import math
assert abs(float(t.ys[-1]) - math.exp(-1.0)) < 1e-4, float(t.ys[-1])
print("ODE solve matches exp(-1) ok", diffrax.__version__)
'''),
 "lane.quimb_cotengra": ("quimb", r'''
import quimb.tensor as qtn, cotengra
psi = qtn.MPS_rand_state(6, bond_dim=4, seed=0)
n = psi.H @ psi
assert abs(float(n) - 1.0) < 1e-8, n
print("MPS contraction norm ok", cotengra.__name__)
'''),
 "lane.julia": (None, None),   # handled separately: it is a binary, not a module
 "lane.pysindy": ("pysindy", r'''
import numpy as np, pysindy as ps
t = np.linspace(0, 2, 400); x = np.exp(-t).reshape(-1, 1)
m = ps.SINDy(feature_library=ps.PolynomialLibrary(degree=1))
m.fit(x, t=t)
c = m.coefficients()
assert abs(float(c[0][-1]) + 1.0) < 0.05, c   # dx/dt = -x
print("SINDy recovered dx/dt=-x ok")
'''),
 "lane.pydmd": ("pydmd", r'''
import numpy as np
from pydmd import DMD
t = np.linspace(0, 4, 128)
X = np.vstack([np.exp(-0.5 * t), 2 * np.exp(-0.5 * t)])
d = DMD(svd_rank=1); d.fit(X)
assert d.modes.shape[1] == 1, d.modes.shape
print("DMD rank-1 fit ok")
'''),
 "lane.pykoopman": ("pykoopman", r'''
import numpy as np, pykoopman as pk
X = np.random.default_rng(0).normal(size=(200, 2))
m = pk.Koopman(); m.fit(X)
assert m.A.shape[0] == m.A.shape[1], m.A.shape
print("Koopman operator square ok")
'''),
 # pymdp on this machine is the JAX build: the array constructors take a PRNG
 # key and return jax arrays. The probe asserts the generative model is a
 # genuine categorical distribution, which a stub cannot fake.
 "lane.pymdp": ("pymdp", r'''
import jax, jax.numpy as jnp
from pymdp import utils
k = jax.random.PRNGKey(0)
A = utils.random_A_array(k, num_obs=[3], num_states=[3])
B = utils.random_B_array(k, num_states=[3], num_controls=[1])
assert jnp.allclose(A[0].sum(axis=0), 1.0, atol=1e-5), A[0].sum(axis=0)
assert jnp.allclose(B[0].sum(axis=0), 1.0, atol=1e-5), B[0].sum(axis=0)
print("pymdp generative model columns normalised ok")
'''),
}

JULIA_PROBE = r'''
using LinearAlgebra
rho = [0.5 0.0; 0.0 0.5]
@assert abs(tr(rho) - 1.0) < 1e-12
e = eigvals(Hermitian(rho))
@assert all(abs.(e .- 0.5) .< 1e-12)
println("julia LinearAlgebra density matrix ok ", VERSION)
'''


def declared_lanes() -> list:
    members = json.loads(REG.read_text())["members"]
    return sorted(m["id"] for m in members if m.get("kind") == "sim_lane")


def probe_capability(lane: str, timeout: int = 180) -> dict:
    """Run the lane's real computation in a subprocess. Value-asserting."""
    t0 = time.time()
    if lane == "lane.julia":
        if not _which("julia"):
            return {"capable": False, "reason": "julia binary not on PATH",
                    "sec": 0.0, "stdout": ""}
        p = subprocess.run(["julia", "-e", JULIA_PROBE], capture_output=True,
                           text=True, timeout=timeout)
    else:
        mod, code = PROBES.get(lane, (None, None))
        if code is None:
            return {"capable": False, "reason": "no capability probe defined "
                    "for this lane — the lane cannot be verified, only assumed",
                    "sec": 0.0, "stdout": ""}
        p = subprocess.run([PY, "-c", code], capture_output=True, text=True,
                           timeout=timeout)
    sec = round(time.time() - t0, 2)
    if p.returncode == 0:
        return {"capable": True, "reason": "", "sec": sec,
                "stdout": (p.stdout or "").strip()[:120]}
    err = (p.stderr or "").strip().splitlines()
    return {"capable": False, "sec": sec, "stdout": (p.stdout or "").strip()[:120],
            "reason": (err[-1][:160] if err else f"exit {p.returncode}")}


def _which(binary: str) -> bool:
    return subprocess.run(["command", "-v", binary], capture_output=True,
                          shell=False, executable="/bin/zsh").returncode == 0 \
        if False else bool(subprocess.run(f"command -v {binary}", shell=True,
                                          capture_output=True).returncode == 0)


def installed(lane: str) -> tuple:
    """Does the module resolve at all? Cheap, no import of the package itself."""
    if lane == "lane.julia":
        return _which("julia"), "julia (binary)"
    mod, _ = PROBES.get(lane, (None, None))
    if not mod:
        return False, "?"
    p = subprocess.run([PY, "-c",
                        f"import importlib.util,sys;"
                        f"sys.exit(0 if importlib.util.find_spec('{mod}') else 1)"],
                       capture_output=True, text=True)
    return p.returncode == 0, mod


def integrated(lane: str) -> dict:
    """Does any CB code actually call this lane's engine?

    A lane that is installed and capable but referenced nowhere in CB is
    installed, not integrated. Grep is the measurement; it is deliberately
    literal so it cannot flatter.
    """
    mod, _ = PROBES.get(lane, (None, None))
    token = "julia" if lane == "lane.julia" else (mod or lane.split(".", 1)[1])
    hits = []
    for p in (CB / "scripts").glob("*.py"):
        # This file must never count as a call site. Its probes import every
        # engine, so counting itself made all 10 lanes report INTEGRATED — the
        # measure reading its own output, the same defect found four other
        # places in this estate today.
        if p.name == Path(__file__).name:
            continue
        try:
            t = p.read_text(errors="ignore")
        except OSError:
            continue
        for pat in (f"import {token}", f"from {token}", f'"{lane}"', f"'{lane}'"):
            if pat in t:
                hits.append(f"{p.name}:{pat}")
                break
    src = CB / "src" / "constraintbox"
    for p in src.rglob("*.py") if src.is_dir() else []:
        try:
            t = p.read_text(errors="ignore")
        except OSError:
            continue
        if f"import {token}" in t or f"from {token}" in t:
            hits.append(f"src/{p.name}")
    return {"integrated": bool(hits), "call_sites": sorted(set(hits))[:6]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lane", default="")
    ap.add_argument("--declared-only", action="store_true",
                    help="skip capability probes — no heavy imports at all")
    ap.add_argument("--install-plan", action="store_true",
                    help="print what is missing and how to get it; run nothing")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()
    t0 = time.time()

    lanes = [a.lane] if a.lane else declared_lanes()
    print("CB HEAVY GATE — CB light verifying the sim-engine estate")
    print(f"  interpreter {PY}")
    print(f"  declared sim lanes: {len(lanes)}")
    print("  DECLARED -> INSTALLED -> CAPABLE -> INTEGRATED  (each separable)\n")

    rows, refusals = {}, []
    print(f"  {'lane':<22}{'inst':<6}{'capable':<9}{'integ':<7}{'sec':>6}  note")
    for lane in lanes:
        inst, mod = installed(lane)
        cap = ({"capable": None, "reason": "not probed (--declared-only)",
                "sec": 0.0, "stdout": ""} if a.declared_only or not inst
               else probe_capability(lane, a.timeout))
        integ = integrated(lane)
        rows[lane] = {"declared": True, "module": mod, "installed": inst,
                      **{f"capability_{k}": v for k, v in cap.items()}, **integ}
        if not inst:
            refusals.append(f"{lane}: declared but NOT INSTALLED ({mod})")
        elif cap["capable"] is False:
            refusals.append(f"{lane}: installed but NOT CAPABLE — {cap['reason']}")
        if inst and not integ["integrated"]:
            refusals.append(f"{lane}: installed but NOT INTEGRATED — no CB code "
                            f"references it")
        cs = "yes" if cap["capable"] else ("--" if cap["capable"] is None else "NO")
        print(f"  {lane:<22}{'yes' if inst else 'NO':<6}{cs:<9}"
              f"{'yes' if integ['integrated'] else 'NO':<7}{cap['sec']:>6}  "
              f"{cap['stdout'] or cap['reason'][:60]}")

    n_inst = sum(1 for r in rows.values() if r["installed"])
    n_cap = sum(1 for r in rows.values() if r["capability_capable"])
    n_int = sum(1 for r in rows.values() if r["integrated"])
    print(f"\n  {len(lanes)} declared / {n_inst} installed / {n_cap} capable / "
          f"{n_int} integrated")

    print(f"\nGATE  {'ADMITTED' if not refusals else 'REFUSED'}")
    for r in refusals:
        print(f"   - {r}")

    if a.install_plan:
        missing = [l for l, r in rows.items() if not r["installed"]]
        print("\nINSTALL PLAN (nothing was run)")
        if not missing:
            print("   every declared lane is installed")
        for l in missing:
            mod, _ = PROBES.get(l, (None, None))
            print(f"   {l:<22}{PY} -m pip install {mod}" if mod else
                  f"   {l:<22}(no module mapping — needs a probe first)")

    out = CB / "receipts" / f"heavy_gate_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps({
        "schema": "cb.heavy-gate.v1",
        "what_this_is": "CB light's verification of the CB heavy sim-engine "
                        "estate. The sim engines are a separate estate; this "
                        "gate does not make them part of CB light.",
        "interpreter": PY, "lanes": rows,
        "totals": {"declared": len(lanes), "installed": n_inst,
                   "capable": n_cap, "integrated": n_int},
        "refusals": refusals, "admitted": not refusals,
        "wall_seconds": round(time.time() - t0, 1),
        "promotion_allowed": False,
        "claim_ceiling": "installation, capability and call-site integration of "
                         "the sim-engine lanes only; says nothing about whether "
                         "any sim result is correct"},
        indent=1, sort_keys=True))
    print(f"\nRECEIPT {out.name}  ({round(time.time()-t0,1)}s)")
    return 0 if not refusals else 1


if __name__ == "__main__":
    sys.exit(main())
