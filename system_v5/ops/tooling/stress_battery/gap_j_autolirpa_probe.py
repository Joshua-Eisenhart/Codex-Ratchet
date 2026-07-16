"""Gap J probe: auto_LiRPA first task (tool_lego_fit_probe, promotion_allowed=false).

Claim under probe: auto_LiRPA BoundedModule+BoundedTensor emits sound, non-vacuous,
eps-monotone output bounds for a tiny fixed-seed torch net over an L_inf input box.

Checks (each control can fail):
  1. soundness   -- 20 random samples INSIDE the box land inside [lb, ub].
  2. outside     -- some point OUTSIDE the box violates [lb, ub] (fails if bounds vacuous).
  3. tightening  -- shrinking the box (eps/2) gives lb2 >= lb and ub2 <= ub,
                    strictly on at least one side (fails if bounds ignore eps).
"""
import json
import os

import torch
import torch.nn as nn
from auto_LiRPA import BoundedModule, BoundedTensor
from auto_LiRPA.perturbations import PerturbationLpNorm

torch.manual_seed(0)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "gap_j_autolirpa_results.json")

# --- tiny net 2-4-1, fixed seed ---
net = nn.Sequential(nn.Linear(2, 4), nn.ReLU(), nn.Linear(4, 1))
net.eval()

center = torch.tensor([[0.3, -0.2]])
eps = 0.5
TOL = 1e-6          # float slack for soundness containment
STRICT = 1e-9       # margin for "strictly tighter on one side"

bounded = BoundedModule(net, torch.zeros_like(center))


def box_bounds(eps_val, method):
    ptb = PerturbationLpNorm(norm=float("inf"), eps=eps_val)
    x = BoundedTensor(center, ptb)
    lb, ub = bounded.compute_bounds(x=(x,), method=method)
    return lb.item(), ub.item()


lb, ub = box_bounds(eps, "CROWN")
lb_ibp, ub_ibp = box_bounds(eps, "IBP")

# --- check 1: soundness on 20 random inside samples ---
g = torch.Generator().manual_seed(1)
inside = center + eps * (2 * torch.rand(20, 2, generator=g) - 1)
with torch.no_grad():
    y_in = net(inside).squeeze(1)
n_inside_ok = int(((y_in >= lb - TOL) & (y_in <= ub + TOL)).sum())
soundness_pass = n_inside_ok == 20

# --- check 2: a point OUTSIDE the box may violate the bounds ---
# Walk outward along fixed directions; bounds are finite, the net is affine far
# from origin, so a violation should appear unless the bounds are vacuous.
violator = None
dirs = torch.tensor([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0],
                     [1.0, 1.0], [-1.0, -1.0], [1.0, -1.0], [-1.0, 1.0]])
for scale in [2.0, 4.0, 8.0, 16.0, 32.0]:
    for d in dirs:
        pt = center + scale * eps * d.unsqueeze(0)
        # confirm pt is genuinely outside the L_inf box
        if (pt - center).abs().max().item() <= eps:
            continue
        with torch.no_grad():
            y = net(pt).item()
        if y < lb - TOL or y > ub + TOL:
            violator = {"point": pt.squeeze(0).tolist(), "output": y,
                        "scale_over_eps": scale,
                        "side": "below_lb" if y < lb else "above_ub"}
            break
    if violator is not None:
        break
outside_pass = violator is not None

# --- check 3: shrinking the box tightens the bounds ---
lb2, ub2 = box_bounds(eps / 2, "CROWN")
nonstrict = (lb2 >= lb - TOL) and (ub2 <= ub + TOL)
strict_one_side = (lb2 > lb + STRICT) or (ub2 < ub - STRICT)
tighten_pass = nonstrict and strict_one_side

overall = soundness_pass and outside_pass and tighten_pass

result = {
    "gap_j_autolirpa": {
        "tool": "auto_LiRPA",
        "tool_path": "/Users/joshuaeisenhart/GitHub/auto_LiRPA",
        "net": "Linear(2,4)-ReLU-Linear(4,1), torch.manual_seed(0)",
        "box": {"center": center.squeeze(0).tolist(), "eps": eps},
        "method": "CROWN (IBP recorded for reference)",
        "bounds_crown": {"lb": lb, "ub": ub},
        "bounds_ibp": {"lb": lb_ibp, "ub": ub_ibp},
        "soundness": {
            "n_samples": 20, "n_inside_bounds": n_inside_ok,
            "sample_output_min": y_in.min().item(),
            "sample_output_max": y_in.max().item(),
            "pass": soundness_pass,
        },
        "control_outside_point": {
            "violator": violator,
            "pass": outside_pass,
            "can_fail": "fails if no searched outside point exits [lb,ub] (vacuous bounds)",
        },
        "control_shrink_tightens": {
            "eps2": eps / 2,
            "bounds_crown_eps2": {"lb": lb2, "ub": ub2},
            "nonstrict_containment": nonstrict,
            "strict_on_one_side": strict_one_side,
            "pass": tighten_pass,
            "can_fail": "fails if lb2<lb or ub2>ub, or neither side strictly improves",
        },
        "pass": overall,
    },
    "classification": "tool_lego_fit_probe",
    "promotion_allowed": False,
}

with open(OUT, "w") as f:
    json.dump(result, f, indent=1)

print(f"lb={lb:.6f} ub={ub:.6f}  (ibp: lb={lb_ibp:.6f} ub={ub_ibp:.6f})")
print(f"soundness 20-sample: {n_inside_ok}/20  -> {soundness_pass}")
print(f"outside-point control: violator={violator}  -> {outside_pass}")
print(f"shrink control: lb2={lb2:.6f} ub2={ub2:.6f} nonstrict={nonstrict} "
      f"strict_one_side={strict_one_side} -> {tighten_pass}")
print("PASS" if overall else "FAIL")
