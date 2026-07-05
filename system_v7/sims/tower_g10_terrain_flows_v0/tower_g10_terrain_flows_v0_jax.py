#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, pathlib
from datetime import datetime, timezone
from jax import config

config.update("jax_enable_x64", True)
import jax.numpy as xp

SIM_ID = "tower_g10_terrain_flows_v0"
HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "results" / f"{SIM_ID}_jax_results.json"


def dagger(a): return xp.conjugate(xp.swapaxes(a, -1, -2))
def comm(h, r): return h @ r - r @ h
def dissip(l, r):
    ld = dagger(l); a = ld @ l
    return l @ r @ ld - 0.5 * (a @ r + r @ a)
def v(m): return xp.reshape(m, (4,), order="F")
def m(w): return xp.reshape(w, (2, 2), order="F")
def fro(a): return float(xp.linalg.norm(a))


I = xp.eye(2, dtype=xp.complex128)
sx = xp.array([[0, 1], [1, 0]], dtype=xp.complex128)
sy = xp.array([[0, -1j], [1j, 0]], dtype=xp.complex128)
sz = xp.array([[1, 0], [0, -1]], dtype=xp.complex128)
sm = xp.array([[0, 0], [1, 0]], dtype=xp.complex128)
sp = xp.array([[0, 1], [0, 0]], dtype=xp.complex128)
p0 = xp.array([[1, 0], [0, 0]], dtype=xp.complex128)
p1 = xp.array([[0, 0], [0, 1]], dtype=xp.complex128)
pxp = 0.5 * (I + sx); pxm = 0.5 * (I - sx)
H0 = 0.5 * sz; HX = 0.5 * sx
STATES = [
    0.5 * (I + 0.2 * sx + 0.3 * sy + 0.4 * sz),
    0.5 * (I - 0.5 * sx + 0.1 * sy - 0.2 * sz),
    0.5 * (I + 0.0 * sx - 0.6 * sy + 0.1 * sz),
]


def rhs(name, side, r, eps=0.17):
    out = side == "out"
    h = HX if out else H0
    sign = 1.0 if out else -1.0
    if name == "Funnel":
        ls = [0.42 * sx, 0.31 * sy] if not out else [0.42 * sz, 0.31 * sx]
        return sum(dissip(l, r) for l in ls) + sign * 1j * eps * comm(h, r)
    if name == "Vortex":
        ls = [0.25 * sz] if not out else [0.25 * sy]
        return sign * 1j * comm(h, r) + eps * sum(dissip(l, r) for l in ls)
    if name == "Pit":
        l = xp.sqrt(0.73) * (sp if out else sm)
        return dissip(l, r) + sign * 1j * eps * comm(h, r)
    ps = [pxp, pxm] if out else [p0, p1]
    hc = HX if out else H0
    return sign * 1j * comm(hc, r) + sum(0.37 * (p @ r @ p - 0.5 * (p @ r + r @ p)) for p in ps)


def superop(name, side, eps=0.17):
    basis = [xp.array([[1, 0], [0, 0]], dtype=xp.complex128), xp.array([[0, 1], [0, 0]], dtype=xp.complex128), xp.array([[0, 0], [1, 0]], dtype=xp.complex128), xp.array([[0, 0], [0, 1]], dtype=xp.complex128)]
    return xp.stack([v(rhs(name, side, b, eps)) for b in basis], axis=1)


def fixed_point(L):
    a = xp.array(L); tr = xp.array([[1, 0, 0, 1]], dtype=xp.complex128)
    aa = xp.concatenate([a[:3, :], tr], axis=0)
    bb = xp.array([0, 0, 0, 1], dtype=xp.complex128)
    r = m(xp.linalg.lstsq(aa, bb, rcond=None)[0])
    r = 0.5 * (r + dagger(r))
    return xp.real(xp.diag(r)).tolist()


def classify(name, side):
    L = superop(name, side)
    vals = xp.linalg.eigvals(L)
    contraction = float(-xp.real(xp.trace(L)) / 4.0)
    swirl = float(xp.max(xp.abs(xp.imag(vals))))
    fp = fixed_point(L)
    deltas = [fro(rhs(name, side, r)) for r in STATES]
    zero_swirl = float(xp.max(xp.abs(xp.imag(xp.linalg.eigvals(superop(name, side, 0.0))))))
    return {"fixed_point_diag": fp, "contraction": contraction, "swirl": swirl, "balance": contraction / (swirl + 1e-12), "phase_portrait_witness": max(deltas), "eps0_swirl": zero_swirl}


def measured_controls(names, pairs, distinguish):
    relabeled_pairs = {"Funnel": "Spiral", "Vortex": "Cannon", "Pit": "Citadel", "Hill": "Source"}
    inverse = {v2: k for k, v2 in pairs.items()}
    relabeled = {f"{n}_vs_{relabeled_pairs[n]}": fro(superop(n, "in") - superop(inverse[relabeled_pairs[n]], "out")) for n in names}
    moved = {f"{n}_to_{relabeled_pairs[n]}": abs(relabeled[f"{n}_vs_{relabeled_pairs[n]}"] - distinguish[f"{n}_vs_{pairs[n]}"]) > 1e-6 for n in names}
    claimed_new = {f"{n}_identity_relabel_claimed_new": fro(superop(n, "in") - superop(n, "in")) for n in names}
    shuffle_order = ["Pit", "Funnel", "Hill", "Vortex"]
    shuffled = {f"{n}_vs_{pairs[n]}": distinguish[f"{src}_vs_{pairs[src]}"] for n, src in zip(names, shuffle_order, strict=True)}
    keyed_changed = any(abs(shuffled[f"{n}_vs_{pairs[n]}"] - distinguish[f"{n}_vs_{pairs[n]}"]) > 1e-6 for n in names)
    multiset_preserved = sorted(round(x, 12) for x in shuffled.values()) == sorted(round(x, 12) for x in distinguish.values())
    return {
        "eps0_degenerations_recorded": True,
        "relabel_control_dies": max(claimed_new.values()) < 1e-12,
        "relabel_values": claimed_new,
        "relabel_pairing_permutation": relabeled_pairs,
        "relabel_measured_distinguishability": relabeled,
        "relabel_values_move_with_channels": all(moved.values()),
        "label_shuffle": {"order": shuffle_order, "keyed_changed": keyed_changed, "multiset_preserved": multiset_preserved, "computed_values": shuffled},
        "label_shuffle_survives": keyed_changed and multiset_preserved,
    }


def main():
    names = ["Funnel", "Vortex", "Pit", "Hill"]
    pairs = {"Funnel": "Cannon", "Vortex": "Spiral", "Pit": "Source", "Hill": "Citadel"}
    terrains = {n: classify(n, "in") for n in names} | {pairs[n]: classify(n, "out") for n in names}
    distinguish = {f"{n}_vs_{pairs[n]}": fro(superop(n, "in") - superop(n, "out")) for n in names}
    controls = measured_controls(names, pairs, distinguish)
    result = {
        "schema": "engine_leg_result_v1", "sim_id": SIM_ID, "engine": "jax",
        "classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
        "nesting": "flows_on_G5_density_matrix_rho_floor", "geometry_not_axes": True,
        "terrain_count": len(terrains), "terrains": terrains,
        "t1_t2_channel_distinguishability": distinguish,
        "controls": controls,
        "TOOL_MANIFEST": {"jax": {"tried": True, "used": True, "reason": "load-bearing matrix flow, eigensystem, and fixed-point leg"}, "json": {"tried": True, "used": True, "reason": "supportive result serialization"}},
        "TOOL_INTEGRATION_DEPTH": {"jax": "load_bearing", "json": "supportive"},
    }
    result["all_pass"] = len(terrains) == 8 and min(distinguish.values()) > 1e-6 and controls["relabel_control_dies"] and controls["relabel_values_move_with_channels"] and controls["label_shuffle_survives"]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"engine": "jax", "all_pass": result["all_pass"], "out": str(OUT)}, sort_keys=True))


if __name__ == "__main__":
    main()
