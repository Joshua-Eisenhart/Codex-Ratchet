#!/usr/bin/env python3
"""Explicit geometry+entropy readout of the Type-1 deductive loop.

Reuses the exact operator/terrain maps from the sealed jax leg and prints, at
every stage, the Bloch vector r=(x,y,z), its length |r| (1=pure, 0=mixed), the
von Neumann entropy S, and dS for that stage. Runs BOTH candidate loop orders
(doc Se->Ne->Ni->Si  and  owner-hypothesis Ne->Ni->Si->Se) so the numbers are
side by side. No canon: order is OD-11 (open); operator kernel is live-engine
(Ti=z-dephase, Fe=z-rotation) — the set that is fully specified and runnable.
"""
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import importlib.util, pathlib

spec = importlib.util.spec_from_file_location(
    "leg", str(pathlib.Path(__file__).parent / "type1_deductive_loop_jax.py"))
leg = importlib.util.module_from_spec(spec); spec.loader.exec_module(leg)

sx, sy, sz = leg.sx, leg.sy, leg.sz


def bloch(rho):
    return (float(jnp.trace(rho @ sx).real),
            float(jnp.trace(rho @ sy).real),
            float(jnp.trace(rho @ sz).real))


def S(rho):
    return leg.vN(rho)


# each atom = (name, terrain-stage function, plain-language geometry)
ATOMS = {
    "Ne": ("NeTi", leg.stage2, "precess about n + shrink y,z (x-dephase in Ne), then Ti halves x,y"),
    "Ni": ("NiFe", leg.stage3, "damp toward north pole |0> (sigma- sink), then Fe rotates x,y about z"),
    "Si": ("FeSi", leg.stage4, "Fe rotates x,y about z first, then z-dephase + precess about z (pin)"),
    "Se": ("TiSe", leg.stage1, "Ti halves x,y first, then z-dephase + precess about n (expand/contact)"),
}


def run_order(order, rho0):
    rho = rho0
    rows = [("start", bloch(rho), abs(complex(*(0,0)))*0 + _norm(bloch(rho)), S(rho), 0.0)]
    prev = S(rho)
    for terr in order:
        token, fn, _ = ATOMS[terr]
        rho = fn(rho)
        s = S(rho)
        rows.append((f"{terr}:{token}", bloch(rho), _norm(bloch(rho)), s, s - prev))
        prev = s
    dS_loop = rows[-1][3] - rows[0][3]
    return rows, dS_loop


def _norm(r):
    return float((r[0]**2 + r[1]**2 + r[2]**2) ** 0.5)


def show(title, order, rho0):
    rows, dS_loop = run_order(order, rho0)
    print(f"\n=== {title}:  {' -> '.join(order)} ===")
    print(f"{'stage':<10}{'x':>8}{'y':>8}{'z':>8}{'|r|':>8}{'S':>9}{'dS':>9}")
    for name, (x, y, z), r, s, ds in rows:
        print(f"{name:<10}{x:8.3f}{y:8.3f}{z:8.3f}{r:8.3f}{s:9.4f}{ds:+9.4f}")
    print(f"loop dS = {dS_loop:+.5f}   (return |r| = {rows[-1][2]:.3f})")


def main():
    I = leg.I
    rho0 = 0.5 * (I + 0.5 * sx + 0.3 * sz)     # start: r=(0.5,0,0.3), pure-ish
    print("start Bloch r =", bloch(rho0), " |r| =", round(_norm(bloch(rho0)), 3),
          " S =", round(S(rho0), 4))
    show("N->S  (owner hypothesis, deduction top-down)", ["Ne", "Ni", "Si", "Se"], rho0)
    show("S->N  (doc order, what the sealed sim ran)", ["Se", "Ne", "Ni", "Si"], rho0)


if __name__ == "__main__":
    main()
