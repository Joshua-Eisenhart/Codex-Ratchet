"""Shared skeleton for doc-illumination sims (classical + bridges).

Each sim imports build_manifest() and write_results() to comply with
SIM_TEMPLATE without duplicating ~100 lines of boilerplate.
"""
import json
import os


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
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"Results written to {out_path}")
    print(f"PASS={results.get('pass')}  name={name}")
    return out_path
