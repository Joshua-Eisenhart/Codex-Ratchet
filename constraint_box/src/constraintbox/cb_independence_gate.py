#!/usr/bin/env python3
"""cb_independence_gate — "what CB is" vs "what makes and tests CB".

The owner's rule: the sim engines, CR and the holodeck may be used to
BUILD and TEST ConstraintBox, but CB must not become bound to them.
That is only meaningful if it is checkable, so this gate measures two
closures and enforces the separation between them.

  RUNTIME CLOSURE  — every third-party module actually imported when
    CB does its own work (import the package, then exercise the
    controller paths). Must be a subset of the DECLARED runtime
    dependencies in pyproject.
  DEVELOPMENT CLOSURE — everything else the project may use to make,
    test, fuzz, or generate evidence about CB: jax, torch, julia,
    qutip, pysindy, the sim estate, CR structures, the holodeck.
    Allowed to be arbitrarily heavy. Forbidden to appear in the
    runtime closure.

The gate fails if any development-only tool leaks into the runtime
closure, or if the runtime closure imports something pyproject does
not declare. It does not care how big the development closure is —
that is the point: heavy tools may make CB, they may not be CB.

Freezing rule (the mechanism that keeps the separation honest):
anything a development tool produces for CB — fixtures, expected
verdicts, adversarial cases, basin envelopes — enters the repository
as FROZEN STATIC DATA with a hash, so CB's tests run without the tool
present. The tool is needed to CREATE the test, never to RUN it.
promotion_allowed=false.
"""
from __future__ import annotations
import argparse, importlib, json, sys, sysconfig
from pathlib import Path

DEV_ONLY = {"jax", "jaxlib", "torch", "torch_geometric", "qutip",
            "pysindy", "pykoopman", "pydmd", "netket", "quimb",
            "diffrax", "equinox", "optax", "numba", "matplotlib",
            "pandas", "networkx", "hypothesis", "pytest"}

# distribution name -> import name(s)
DIST_TO_IMPORT = {"z3_solver": {"z3"}, "cvc5": {"cvc5"},
                  "rustworkx": {"rustworkx"}, "sympy": {"sympy"},
                  "maude": {"maude"}, "numpy": {"numpy"}}
INTERPRETER_ARTIFACTS = {"cython_runtime", "_cython", "sitecustomize"}


def declared_runtime(pyproject: Path) -> set[str]:
    text = pyproject.read_text()
    block = text.split("dependencies = [", 1)[1].split("]", 1)[0]
    names = set()
    for line in block.splitlines():
        line = line.strip().strip('",')
        if not line:
            continue
        name = line.split(">=")[0].split("==")[0].split("<")[0].strip()
        if name:
            names.add(name.replace("-", "_").lower())
    imports = set()
    for n in names:
        imports |= DIST_TO_IMPORT.get(n, {n})
    return imports

def third_party(mods) -> set[str]:
    std = set(sys.stdlib_module_names)
    stdlib_path = sysconfig.get_paths()["stdlib"]
    out = set()
    for m in mods:
        top = m.split(".")[0]
        if top.startswith("_") or top in std or top == "constraintbox":
            continue
        mod = sys.modules.get(top)
        f = getattr(mod, "__file__", None) or ""
        if f.startswith(stdlib_path):
            continue
        if top.lower() in INTERPRETER_ARTIFACTS:
            continue
        out.add(top.lower())
    return out

def exercise_runtime() -> set[str]:
    """import CB and drive its own work paths, then read sys.modules"""
    before = set(sys.modules)
    importlib.import_module("constraintbox")
    for name in ("crosscheck", "constraints", "lease", "cli",
                 "capability_box", "execution_lease", "boundary_contract"):
        try:
            importlib.import_module(f"constraintbox.{name}")
        except Exception:
            pass
    try:  # actually run the SMT spine, not just import it
        from constraintbox.crosscheck import cross_check
        r = cross_check("finite_constraint_satisfiability",
                        {"variables": {"x": [0, 1, 2], "y": [0, 1, 2]},
                         "constraints": [{"op": "neq",
                                          "left": {"var": "x"},
                                          "right": {"var": "y"}}]})
        if r.agreement != "AGREE":
            raise RuntimeError(f"probe claim did not decide: {r.agreement}")
    except Exception as exc:
        print(f"WARNING: runtime probe failed ({exc}); closure measurement "
              f"is not trustworthy", file=sys.stderr)
        raise
    return third_party(set(sys.modules) - before | {"constraintbox"})

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pyproject", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    a = ap.parse_args()
    declared = declared_runtime(a.pyproject)
    runtime = exercise_runtime()
    # a gate that measures nothing must fail, not pass
    if not runtime:
        print("EMPTY RUNTIME CLOSURE — the probe exercised no third-party "
              "code; refusing to certify independence", file=sys.stderr)
        return 2
    leaked = sorted(runtime & DEV_ONLY)
    undeclared = sorted(m for m in runtime
                        if m not in declared and m not in DEV_ONLY)
    dev_present = sorted(m for m in DEV_ONLY
                         if importlib.util.find_spec(m) is not None)
    defects = []
    if leaked:
        defects.append(f"development-only tools in CB's runtime "
                       f"closure: {leaked}")
    if undeclared:
        defects.append(f"runtime imports not declared in pyproject: "
                       f"{undeclared}")
    out = {"schema": "cb.independence-gate.v1",
           "declared_runtime_dependencies": sorted(declared),
           "measured_runtime_closure": sorted(runtime),
           "development_tools_installed_here": dev_present,
           "leaked_into_runtime": leaked,
           "undeclared_runtime_imports": undeclared,
           "independence_holds": not defects,
           "defects": defects,
           "freezing_rule": "artifacts produced by development tools "
                            "enter the repo as frozen hashed data; CB "
                            "tests must run with those tools absent",
           "promotion_allowed": False}
    a.output.write_text(json.dumps(out, indent=1, sort_keys=True))
    print("declared runtime deps :", sorted(declared))
    print("measured runtime closure:", sorted(runtime))
    print("dev tools installed here:", dev_present)
    print("INDEPENDENCE HOLDS:", out["independence_holds"],
          "" if not defects else defects)
    return 0 if not defects else 1

if __name__ == "__main__":
    sys.exit(main())
