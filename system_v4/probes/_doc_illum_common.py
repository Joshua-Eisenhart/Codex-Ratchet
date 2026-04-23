"""Shared skeleton for doc-illumination sims (classical + bridges).

Each sim imports build_manifest() and write_results() to comply with
SIM_TEMPLATE without duplicating ~100 lines of boilerplate.
"""
import json
import os

classification = "canonical"

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "pyg": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "z3": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "sympy": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "clifford": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "xgi": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed in shared helper; sims decide actual usage"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": None,
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}


def build_manifest():
    tm = {k: {"tried": False, "used": False, "reason": ""} for k in [
        "pytorch", "pyg", "z3", "cvc5", "sympy",
        "clifford", "geomstats", "e3nn",
        "rustworkx", "xgi", "toponetx", "gudhi",
    ]}
    depth = {k: None for k in tm}
    try:
        import numpy  # noqa
    except ImportError:
        pass
    for k, modname in [
        ("pytorch", "torch"), ("pyg", "torch_geometric"), ("z3", "z3"),
        ("cvc5", "cvc5"), ("sympy", "sympy"), ("clifford", "clifford"),
        ("geomstats", "geomstats"), ("e3nn", "e3nn"),
        ("rustworkx", "rustworkx"), ("xgi", "xgi"),
        ("toponetx", "toponetx"), ("gudhi", "gudhi"),
    ]:
        try:
            __import__(modname)
            tm[k]["tried"] = True
        except ImportError:
            tm[k]["reason"] = "not installed"
    return tm, depth


def write_results(name, results):
    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}_results.json")
    results.setdefault(
        "tool_integration_depth",
        results.get("TOOL_INTEGRATION_DEPTH", TOOL_INTEGRATION_DEPTH),
    )
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"PASS={results.get('pass')}  name={name}")
    return out_path
