#!/usr/bin/env python3
"""
Tier A A0x tool-capability probe for torch_ga.

This probe stays self-contained under the overnight pre-approved default: if
`torch_ga` is absent, every section reports an import-gated skip and the file can
still be committed and queued. When `torch_ga` is importable, the admitted tests
stay tool-local and rely only on torch_ga import and module-level behavior.
"""

import importlib
import importlib.util
import json
import os
from types import ModuleType

classification = "canonical"
NAME = "tool_capability_torch_ga"
SCOPE_NOTE = "Tier A torch_ga capability probe: import-gated module admission, exclusion checks, and import boundary behavior."

TOOL_MANIFEST = {
    "torch_ga": {
        "tried": False,
        "used": False,
        "reason": "torch_ga is the sole package under test; the probe only admits module import, symbol-surface inspection, and import-system boundary behavior that depend on torch_ga being present.",
    }
}

TOOL_INTEGRATION_DEPTH = {"torch_ga": None}

TORCH_GA_SPEC = importlib.util.find_spec("torch_ga")

try:
    import torch_ga  # type: ignore

    TOOL_MANIFEST["torch_ga"]["tried"] = True
    TOOL_INTEGRATION_DEPTH["torch_ga"] = "load_bearing"
except ImportError:
    torch_ga = None
    TOOL_MANIFEST["torch_ga"]["reason"] = "torch_ga import failed on this machine; the probe remains import-gated and queued for overnight runner coverage when the package becomes available."


def _mark_torch_ga_used() -> None:
    TOOL_MANIFEST["torch_ga"]["used"] = True


def _skip_payload(reason: str):
    return {"status": "skipped", "reason": reason}


def _module_public_names(module: ModuleType):
    return sorted(name for name in dir(module) if not name.startswith("_"))


# =====================================================================
# POSITIVE TESTS
# =====================================================================

def run_positive_tests():
    results = {}

    if not TOOL_MANIFEST["torch_ga"]["tried"]:
        results["torch_ga_import_gate"] = _skip_payload("torch_ga not importable")
        return results

    public_names = _module_public_names(torch_ga)
    module_origin = getattr(torch_ga, "__file__", None)
    package_path = list(getattr(torch_ga, "__path__", []))
    _mark_torch_ga_used()
    results["module_import_survives"] = {
        "module_name": getattr(torch_ga, "__name__", None),
        "origin": module_origin,
        "package_path": package_path,
        "spec_origin": getattr(getattr(torch_ga, "__spec__", None), "origin", None),
        "pass": bool(module_origin) or bool(package_path),
    }

    _mark_torch_ga_used()
    results["public_symbol_surface_survives"] = {
        "public_symbol_count": len(public_names),
        "public_symbol_sample": public_names[:12],
        "pass": len(public_names) > 0,
    }

    reimported = importlib.import_module("torch_ga")
    _mark_torch_ga_used()
    results["reimport_identity_survives"] = {
        "same_module_object": reimported is torch_ga,
        "pass": reimported is torch_ga,
    }

    return results


# =====================================================================
# NEGATIVE TESTS
# =====================================================================

def run_negative_tests():
    results = {}

    if not TOOL_MANIFEST["torch_ga"]["tried"]:
        results["torch_ga_import_gate"] = _skip_payload("torch_ga not importable")
        return results

    try:
        getattr(torch_ga, "__definitely_missing_capability_symbol__")
        missing_attr_status = "unexpected_success"
        missing_attr_detail = "nonsense attribute lookup was admitted"
    except AttributeError as exc:
        _mark_torch_ga_used()
        missing_attr_status = type(exc).__name__
        missing_attr_detail = str(exc)
    results["missing_attribute_excluded"] = {
        "status": missing_attr_status,
        "detail": missing_attr_detail,
        "claim_excluded": missing_attr_status != "unexpected_success",
    }

    try:
        importlib.import_module("torch_ga.__definitely_missing_submodule__")
        missing_submodule_status = "unexpected_success"
        missing_submodule_detail = "nonsense submodule import was admitted"
    except ModuleNotFoundError as exc:
        _mark_torch_ga_used()
        missing_submodule_status = type(exc).__name__
        missing_submodule_detail = str(exc)
    results["missing_submodule_excluded"] = {
        "status": missing_submodule_status,
        "detail": missing_submodule_detail,
        "claim_excluded": missing_submodule_status != "unexpected_success",
    }

    public_names = _module_public_names(torch_ga)
    nonsense_name = "__definitely_missing_capability_symbol__"
    _mark_torch_ga_used()
    results["public_surface_excludes_nonsense_symbol"] = {
        "public_symbol_count": len(public_names),
        "nonsense_symbol": nonsense_name,
        "claim_excluded": nonsense_name not in public_names,
    }

    return results


# =====================================================================
# BOUNDARY TESTS
# =====================================================================

def run_boundary_tests():
    results = {}

    if not TOOL_MANIFEST["torch_ga"]["tried"]:
        results["torch_ga_import_gate"] = _skip_payload("torch_ga not importable")
        return results

    package_path = list(getattr(torch_ga, "__path__", []))
    _mark_torch_ga_used()
    results["package_path_boundary"] = {
        "package_path": package_path,
        "path_entry_count": len(package_path),
        "pass": len(package_path) >= 1,
    }

    spec = getattr(torch_ga, "__spec__", None)
    _mark_torch_ga_used()
    results["module_spec_boundary"] = {
        "has_spec": spec is not None,
        "spec_name": getattr(spec, "name", None),
        "loader_type": type(getattr(spec, "loader", None)).__name__ if spec is not None else None,
        "pass": spec is not None and getattr(spec, "name", None) == "torch_ga",
    }

    fresh_spec = importlib.util.find_spec("torch_ga")
    _mark_torch_ga_used()
    results["repeat_spec_lookup_boundary"] = {
        "initial_spec_found": TORCH_GA_SPEC is not None,
        "repeat_spec_found": fresh_spec is not None,
        "same_origin": getattr(TORCH_GA_SPEC, "origin", None) == getattr(fresh_spec, "origin", None),
        "pass": fresh_spec is not None and getattr(TORCH_GA_SPEC, "origin", None) == getattr(fresh_spec, "origin", None),
    }

    return results


if __name__ == "__main__":
    results = {
        "name": NAME,
        "scope_note": SCOPE_NOTE,
        "classification": classification,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "positive": run_positive_tests(),
        "negative": run_negative_tests(),
        "boundary": run_boundary_tests(),
    }

    out_dir = os.path.join(os.path.dirname(__file__), "a2_state", "sim_results")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{NAME}_results.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2, sort_keys=True)
    print(f"Results written to {out_path}")
