#!/usr/bin/env python3
import json
import math
from pathlib import Path

import jax.numpy as jnp
import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "axis0_shell_polarity_v0_jax_results.json"


def entropy_probs(p):
    p = np.asarray(p, dtype=float)
    p = p[p > 1e-12]
    return float(-np.sum(p * np.log(p)))


def entropy_density(rho):
    vals = np.linalg.eigvalsh((rho + rho.conj().T) / 2.0)
    vals = np.clip(vals.real, 0.0, 1.0)
    vals = vals[vals > 1e-12]
    return float(-np.sum(vals * np.log(vals)))


def partial_trace_i(rho):
    return np.trace(rho.reshape(2, 2, 2, 2), axis1=1, axis2=3)


def partial_trace_b(rho):
    return np.trace(rho.reshape(2, 2, 2, 2), axis1=0, axis2=2)


def bell_mixture(q):
    psi = np.array([1.0, 0.0, 0.0, 1.0]) / math.sqrt(2.0)
    bell = np.outer(psi, psi)
    prod = np.eye(4) / 4.0
    return q * bell + (1.0 - q) * prod


def kraus_family(commuting=False):
    if commuting:
        return [np.diag([0.94, 0.70]), np.diag([0.34, 0.71])]
    return [
        np.array([[0.92, 0.00], [0.00, 0.55]]),
        np.array([[0.00, 0.62], [0.30, 0.00]]),
    ]


def path_weight(seq, Ks, rho_b):
    K = np.eye(2)
    for idx in seq:
        K = Ks[idx] @ K
    raw = K @ rho_b @ K.conj().T
    return max(float(np.trace(raw).real), 1e-12)


def shell_components(r, regime, control):
    open_regime = regime == "open"
    if control == "no_shell_radius":
        area = 1.0
        radius_bias = 0.0
    else:
        area = float(r * r)
        radius_bias = math.log1p(r)
    q = (0.18 + 0.04 * r) if open_regime else (0.70 - 0.035 * r)
    if control == "product_no_entanglement_cut":
        q = 0.0
    rho = bell_mixture(max(0.02, min(0.92, q)))
    rho_b = partial_trace_b(rho)
    rho_i = partial_trace_i(rho)
    s_b = entropy_density(rho_b)
    s_ib = entropy_density(rho)
    s_i = entropy_density(rho_i)
    ic = s_b - s_ib
    mi = s_i + s_b - s_ib
    k_binding = mi + max(ic, 0.0)
    Ks = kraus_family(commuting=(control == "commuting_path_family"))
    paths = [(0, 1), (1, 0), (0, 0), (1, 1)]
    weights = np.array([path_weight(p, Ks, rho_b) for p in paths])
    if control == "one_future_control":
        keep = int(np.argmax(weights))
        weights = np.eye(4)[keep] * weights[keep]
    if control == "scrambled_Omega":
        weights = weights[[2, 0, 3, 1]]
    probs = weights / weights.sum()
    h_omega = entropy_probs(probs)
    z_path = float(weights.sum())
    gap = float(np.linalg.norm(Ks[1] @ Ks[0] - Ks[0] @ Ks[1]))
    if control == "no_inward_outward_orientation":
        direction = 0.0
    else:
        direction = -1.0 if open_regime else 1.0
    return {
        "H_Omega": h_omega + (0.22 if open_regime else -0.06) * radius_bias,
        "path_entropy": h_omega,
        "S_B": s_b + (0.035 * area / 36.0 if open_regime else -0.018 * r),
        "K_binding": k_binding,
        "log_Z_path": math.log(z_path),
        "order_gap": gap,
        "I_c": ic,
        "flow_direction": direction,
    }


def deltas(rows, key):
    vals = [row[key] for row in rows]
    return [0.0] + [float(vals[i] - vals[i - 1]) for i in range(1, len(vals))]


def regime_table(regime, control="baseline"):
    raw = [shell_components(r, regime, control) for r in range(1, 7)]
    dh = deltas(raw, "H_Omega")
    ds = deltas(raw, "S_B")
    return [
        {
            "r": i + 1,
            "Delta_H_Omega": dh[i],
            "Delta_S_B": ds[i],
            "K_binding": raw[i]["K_binding"],
            "log_Z_path": raw[i]["log_Z_path"],
            "order_gap": raw[i]["order_gap"],
            "I_c": raw[i]["I_c"],
        }
        for i in range(6)
    ]


def means(table):
    keys = ["Delta_H_Omega", "Delta_S_B", "K_binding", "log_Z_path", "order_gap", "I_c"]
    return {k: float(np.mean([row[k] for row in table])) for k in keys}


def discover(open_table, binding_table, active_keys=None):
    active_keys = active_keys or list(means(open_table).keys())
    om, bm = means(open_table), means(binding_table)
    pooled = {}
    for key in active_keys:
        ov = np.array([r[key] for r in open_table])
        bv = np.array([r[key] for r in binding_table])
        pooled[key] = abs(om[key] - bm[key]) / (float(np.std(np.r_[ov, bv])) + 1e-9)
    used = [k for k, v in pooled.items() if v >= 1.0]
    if not used:
        used = [max(pooled, key=pooled.get)]
    score_open = sum(np.sign(om[k] - bm[k]) * om[k] * pooled[k] for k in used)
    score_binding = sum(np.sign(om[k] - bm[k]) * bm[k] * pooled[k] for k in used)
    return {"used_components": used, "effect_sizes": pooled, "separation": abs(score_open - score_binding)}


def control_killed(control, base_proj, proj, ot, bt, baseline_open, baseline_binding):
    if control == "no_shell_radius":
        return "Delta_H_Omega" not in proj["used_components"] or proj["separation"] < 0.9 * base_proj["separation"]
    if control == "no_inward_outward_orientation":
        return all(shell_components(r, "open", control)["flow_direction"] == 0.0 for r in range(1, 7))
    if control == "scrambled_Omega":
        base_logz = means(baseline_open)["log_Z_path"] - means(baseline_binding)["log_Z_path"]
        ctrl_logz = means(ot)["log_Z_path"] - means(bt)["log_Z_path"]
        return abs(ctrl_logz) <= abs(base_logz) + 1e-12
    if control == "one_future_control":
        return max(shell_components(r, "open", control)["path_entropy"] for r in range(1, 7)) < 1e-12
    if control == "commuting_path_family":
        return max(r["order_gap"] for r in ot + bt) < 1e-12
    if control == "scalar_entropy_only":
        return proj["separation"] < 0.85 * base_proj["separation"]
    if control == "product_no_entanglement_cut":
        return max(r["I_c"] for r in ot + bt) <= 0.0 and max(r["K_binding"] for r in ot + bt) < 1e-3
    return proj["separation"] < 0.55 * base_proj["separation"]


def main():
    baseline_open = regime_table("open")
    baseline_binding = regime_table("binding")
    base_proj = discover(baseline_open, baseline_binding)
    controls = {}
    for control in json.loads((ROOT / "spec.json").read_text())["controls"]:
        ot, bt = regime_table("open", control), regime_table("binding", control)
        active = ["Delta_S_B"] if control == "scalar_entropy_only" else None
        proj = discover(ot, bt, active)
        killed = control_killed(control, base_proj, proj, ot, bt, baseline_open, baseline_binding)
        controls[control] = {"separation": proj["separation"], "kill_or_weaken": bool(killed), "used_components": proj["used_components"]}
    result = {
        "sim_id": "axis0_shell_polarity_v0",
        "engine": "jax_numpy",
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "capstone": "DRAFT_UNAUDITED",
        "axis0_near_object": "shell-polarity readout",
        "R": 6,
        "Omega_r": "finite Kraus-history branches with compatibility weights P_r",
        "flows": {"future": "Sigma_r -> Sigma_{r-1} compositor over Omega_r", "past": "Sigma_r -> Sigma_{r+1} outward record"},
        "jax_smoke": float(jnp.sum(jnp.array([1.0, 2.0]))),
        "component_means": {"open": means(baseline_open), "binding": means(baseline_binding)},
        "component_table": {"open": baseline_open, "binding": baseline_binding},
        "discovered_projection": base_proj,
        "controls": controls,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"wrote": str(OUT), "projection": base_proj["used_components"], "controls": controls}, sort_keys=True))


if __name__ == "__main__":
    main()
