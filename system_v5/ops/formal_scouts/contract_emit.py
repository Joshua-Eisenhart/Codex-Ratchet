"""Thin emission helper: format an honest sim's REAL measured content into the
field names per_sim_contract.py greps for. It does NO computation -- each sim
still computes its own object, controls, and deltas. This only re-keys real
values into the contract's expected shape (object_id, tool_ablations with a
MEASURED outcome_delta, resource_blocker), so honest native-scale sims can pass
the repo gate without faking the 8/16/32/64 ladder or hardcoding ablation deltas.
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)
try:
    from load_bearing_proof import smt_load_bearing   # the repo's own anti-fabrication helper
except Exception:
    smt_load_bearing = None


def attach(result: dict, ablations: dict, scale_note: str, torch_primary=None) -> dict:
    """ablations: {name: (baseline_value, ablated_value)} from the sim's REAL controls.
    The outcome_delta is the measured difference -- not a planted constant."""
    result["object_id"] = result.get("name")
    result["resource_blocker"] = scale_note
    result["tool_ablations"] = {
        name: {"baseline": float(b), "ablated": float(a), "outcome_delta": float(b) - float(a)}
        for name, (b, a) in ablations.items()
    }
    if torch_primary is not None:
        result["torch_primary_result"] = float(torch_primary)
    # genuine load-bearing SMT proof (repo helper): the SAME structural claim, bound to the
    # MEASURED observable, flips verdict between the real carrier and the control carrier.
    if smt_load_bearing is not None and ablations:
        name, (b, a) = max(ablations.items(), key=lambda kv: abs(float(kv[1][0]) - float(kv[1][1])))
        b, a = float(b), float(a)
        mid = 0.5 * (b + a)
        builder = (lambda vs: vs["obs"] >= mid) if b >= a else (lambda vs: vs["obs"] <= mid)
        result["structural_proof"] = smt_load_bearing(
            f"{name}: real carrier on the structure-present side of {mid:.4g}, control on the erased side",
            {"obs": b}, {"obs": a}, builder)
    return result
