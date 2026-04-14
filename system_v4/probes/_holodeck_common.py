"""Shared tool manifest/import helpers for sim_holodeck_* lego family.

Kept minimal so each sim stays 60-150 lines. Not a framework -- just
a de-duplication of the SIM_TEMPLATE boilerplate. Each sim still owns
its classification, integration depth, and test bodies.
"""
import json
import os

def build_manifest():
    manifest = {
        "sympy":     {"tried": False, "used": False, "reason": ""},
        "clifford":  {"tried": False, "used": False, "reason": ""},
        "geomstats": {"tried": False, "used": False, "reason": ""},
        "toponetx":  {"tried": False, "used": False, "reason": ""},
        "gudhi":     {"tried": False, "used": False, "reason": ""},
        "numpy":     {"tried": True,  "used": False, "reason": "baseline numeric"},
    }
    try:
        import sympy  # noqa
        manifest["sympy"]["tried"] = True
    except ImportError:
        manifest["sympy"]["reason"] = "not installed"
    try:
        import clifford  # noqa
        manifest["clifford"]["tried"] = True
    except ImportError:
        manifest["clifford"]["reason"] = "not installed"
    try:
        import geomstats  # noqa
        manifest["geomstats"]["tried"] = True
    except ImportError:
        manifest["geomstats"]["reason"] = "not installed"
    try:
        from toponetx.classes import CellComplex  # noqa
        manifest["toponetx"]["tried"] = True
    except ImportError:
        manifest["toponetx"]["reason"] = "not installed"
    try:
        import gudhi  # noqa
        manifest["gudhi"]["tried"] = True
    except ImportError:
        manifest["gudhi"]["reason"] = "not installed"
    return manifest


def write_results(name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    return out_path


def summary_ok(results):
    """All positive pass, negative all False (fail as expected), boundary pass."""
    pos_ok = all(bool(v) for v in results.get("positive", {}).values())
    neg_ok = all(not bool(v) for v in results.get("negative", {}).values())
    bnd_ok = all(bool(v) for v in results.get("boundary", {}).values())
    return pos_ok and neg_ok and bnd_ok
