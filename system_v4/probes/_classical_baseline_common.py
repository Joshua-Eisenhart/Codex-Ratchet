"""Shared minimal manifest for classical_baseline compression/spectral sims.
numpy-only; sympy optional; no load-bearing non-numeric tools.
"""
import numpy as np  # noqa: F401

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "classical baseline: numpy only"},
    "pyg": {"tried": False, "used": False, "reason": "classical baseline: numpy only"},
    "z3": {"tried": False, "used": False, "reason": "not needed for numeric spectral baseline"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "optional symbolic; not load-bearing"},
    "clifford": {"tried": False, "used": False, "reason": "not needed"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}
TOOL_INTEGRATION_DEPTH = {k: None for k in TOOL_MANIFEST}
try:
    import sympy  # noqa: F401
    TOOL_MANIFEST["sympy"]["tried"] = True
except ImportError:
    pass
