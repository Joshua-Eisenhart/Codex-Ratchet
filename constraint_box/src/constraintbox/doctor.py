from __future__ import annotations

import importlib
import importlib.metadata
import json
import platform
import shutil
import sys

from .runtime_profiles import RuntimeProfileError, inspect_active_runtime


PYTHON_TOOLS = (
    "numpy",
    "scipy",
    "z3",
    "cvc5",
    "jax",
    "pysindy",
    "pydmd",
    "pykoopman",
    "torch",
    "e3nn",
    "jsonschema",
    "hypothesis",
)


def probe_python_tool(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001
        return {
            "tool": name,
            "state": "UNAVAILABLE",
            "error": f"{type(exc).__name__}: {exc}",
        }
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            version = "unknown"
    return {"tool": name, "state": "IMPORTABLE", "version": str(version)}


def build_report() -> dict[str, object]:
    try:
        runtime_profile: dict[str, object] = inspect_active_runtime()
    except RuntimeProfileError as exc:
        runtime_profile = {
            "schema": "constraintbox.runtime-profile-error.v1",
            "state": "BLOCKED",
            "reason": "runtime_profile_registry_error",
            "error": str(exc),
            "promotion_allowed": False,
        }
    return {
        "schema": "constraintbox.doctor.v2",
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "runtime_profile": runtime_profile,
        "python_tools": [probe_python_tool(name) for name in PYTHON_TOOLS],
        "executables": {
            name: shutil.which(name)
            for name in ("java", "node", "npm", "z3", "cvc5")
        },
        "status_rule": (
            "IMPORTABLE is weaker than a portable core profile. runtime_profile "
            "reports whether this active interpreter/library set is ELIGIBLE, "
            "PARKED, or BLOCKED; it never selects or installs a runtime. A "
            "fixed task still needs positive, negative, severance, and resource "
            "controls."
        ),
    }


def main() -> None:
    print(json.dumps(build_report(), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
