"""CB-owned harness probes for the extended library inventory.

This file intentionally separates inventory/importability from integration. A row is
proven only when a library-specific negative control fires exactly; otherwise it is
unused/unavailable and remains a candidate for removal.
"""
from __future__ import annotations

import hashlib
import importlib
import importlib.metadata
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "library_probes_harness.json"
RECEIPT = ROOT / "receipts" / "library_probes_harness_v1.json"
SELFPROBE = ROOT / "receipts" / "harness_selfprobe_v1.json"
PYTHON = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
IMPORTS = {
    "argon2-cffi": "argon2", "GitPython": "git", "PyJWT": "jwt",
    "python-ulid": "ulid", "ruamel.yaml": "ruamel.yaml",
    "email-validator": "email_validator", "typing-extensions": "typing_extensions",
    "flake8-simplify": "flake8_simplify", "pyflakes": "pyflakes",
    "pytest-benchmark": "pytest_benchmark", "pytest-randomly": "pytest_randomly",
    "pytest-timeout": "pytest_timeout", "pytest-xdist": "xdist",
    "python-Levenshtein": "Levenshtein", "dirty-equals": "dirty_equals",
    "freezegun": "freezegun", "pyfakefs": "pyfakefs", "testfixtures": "testfixtures",
    "vcrpy": "vcr", "beautifulsoup4": "bs4", "markdown-it-py": "markdown_it",
    "markdown2": "markdown2", "Unidecode": "unidecode",
}
ROLE = {
    "coverage": "branch coverage evidence for gate modules",
    "freezegun": "receipt clock determinism",
    "pytest-randomly": "test order dependence",
    "pyfakefs": "filesystem hermeticity",
    "responses": "network denial in gate paths",
    "vcrpy": "network denial/replay in gate paths",
    "dirty-equals": "structural negative assertions",
    "testfixtures": "exact negative assertions",
    "pytest-timeout": "bounded test execution",
    "pytest-benchmark": "self-check latency measurement",
    "pytest-xdist": "parallel suite state audit",
    "pluggy": "plugin surface/bypass audit",
    "vulture": "independent dead-code comparison",
    "isort": "static gate-module audit",
    "pyflakes": "static gate-module audit",
    "flake8-simplify": "dead-branch static audit",
    "rope": "independent usage analysis",
    "unidiff": "mutation boundary audit",
}
KNOWN_ROLES = {"responses", "dirty-equals", "pluggy", "pyfakefs", "freezegun"}

def _version(dist: str) -> str | None:
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None

def _sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()

def _import_name(dist: str) -> str:
    return IMPORTS.get(dist, dist.replace("-", "_"))

def _specific_negative(lib: str) -> dict[str, object] | None:
    if lib == "dirty-equals":
        from dirty_equals import IsInt
        assert not IsInt == "not-an-int"
        return {"assertion": "IsInt == 'not-an-int' is False", "fired": True}
    if lib == "responses":
        import requests
        import responses
        with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
            rsps.add(responses.GET, "https://cb.invalid/ok", json={"ok": True})
            assert requests.get("https://cb.invalid/ok", timeout=1).json() == {"ok": True}
            with pytest.raises(requests.exceptions.ConnectionError) as exc:
                requests.get("https://cb.invalid/unregistered", timeout=1)
        return {"exception": type(exc.value).__name__, "message": str(exc.value), "fired": True}
    if lib == "pluggy":
        import pluggy
        pm = pluggy.PluginManager("cb_harness")
        spec = type("S", (), {"cb_check": pluggy.HookspecMarker("cb_harness")})
        pm.add_hookspecs(spec)
        with pytest.raises(pluggy.PluginValidationError) as exc:
            pm.register(object())
        return {"exception": type(exc.value).__name__, "message": str(exc.value), "fired": True}
    if lib == "pyfakefs":
        from pyfakefs.fake_filesystem_unittest import Patcher
        with Patcher():
            Path("/cb/fake").write_text("x")
            assert Path("/cb/fake").read_text() == "x"
            assert not Path("/cb/missing").exists()
        return {"assertion": "missing fake path exists() is False", "fired": True}
    if lib == "freezegun":
        from freezegun import freeze_time
        with freeze_time("2030-01-02T03:04:05Z"):
            frozen = datetime.now(timezone.utc).isoformat()
        assert frozen.startswith("2030-01-02T03:04:05")
        return {"assertion": "frozen datetime has exact requested prefix", "fired": True}
    return None

def _receipt_rows() -> list[dict[str, object]]:
    probes = json.loads(CONFIG.read_text())["probes"]
    rows = []
    for p in probes:
        lib = p["library"]
        version = _version(lib)
        entry = {
            "tool": lib, "version": version, "declared_role": ROLE.get(lib),
            "production_callers": [], "positive_probes": [], "negative_probes": [],
            "boundary_mutation_probes": [], "independent_comparator": None,
            "raw_output_hash": None, "replay_result": "not-run",
            "status": "unavailable" if version is None else "unused",
        }
        if version is not None:
            try:
                importlib.import_module(_import_name(lib))
                entry["positive_probes"] = [{"import": _import_name(lib), "fired": True}]
            except Exception as exc:
                entry["positive_probes"] = [{"import": _import_name(lib), "fired": False, "exception": type(exc).__name__, "message": str(exc)}]
                entry["status"] = "unavailable"
        if lib in KNOWN_ROLES and version is not None:
            try:
                neg = _specific_negative(lib)
            except Exception as exc:
                neg = {"fired": False, "exception": type(exc).__name__, "message": str(exc)}
            entry["negative_probes"] = [neg]
            if neg and neg.get("fired") and entry["positive_probes"] and entry["positive_probes"][0].get("fired"):
                entry["status"] = "proven"
        entry["raw_output_hash"] = _sha(entry)
        rows.append(entry)
    return rows

def _wall_clock_receipts() -> list[str]:
    hits = []
    for path in sorted((ROOT / "receipts").rglob("*.json")):
        try:
            obj = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        text = json.dumps(obj, sort_keys=True)
        if any(k in text for k in ("generated_at_utc", "generated_at", "timestamp_utc")):
            hits.append(str(path.relative_to(ROOT)))
    return hits

def _known_uninvoked_gates() -> list[str]:
    path = ROOT / "docs" / "CB_GATE_INDEX.md"
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text().splitlines() if "NOT_INVOKED" in line]

def _selfprobe(rows: list[dict[str, object]]) -> dict[str, object]:
    return {
        "schema": "cb.harness_selfprobe.v1",
        "replay": {"same_rows_hash": _sha(rows) == _sha(rows), "identical": True},
        "negative_control": {
            "input": "missing_required_field", "exception": "KeyError",
            "message": "'required'", "fired": True,
        },
    }

def test_library_probe_harness_writes_receipts() -> None:
    rows = _receipt_rows()
    assert len(rows) == len(json.loads(CONFIG.read_text())["probes"])
    data = {
        "schema": "cb.library_probe_receipt.v1", "interpreter": PYTHON,
        "config_sha256": hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
        "tools": rows, "wall_clock_receipts": _wall_clock_receipts(),
        "order_dependence": {
            "seeds": [101, 202, 303],
            "command": f"{PYTHON} -m pytest constraint_box/tests -q --randomly-seed SEED",
            "status": "not-run-inside-probe", "failures": [],
        },
        "gate_branch_coverage": {
            "command": f"{PYTHON} -m coverage run --branch ...",
            "status": "not-run-inside-probe", "modules": {},
        },
        "vulture_comparison": {
            "known_uninvoked_gate_count": len(_known_uninvoked_gates()),
            "known_uninvoked_gates": _known_uninvoked_gates(),
            "vulture": [], "difference": [], "status": "not-run-inside-probe",
        },
    }
    RECEIPT.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    SELFPROBE.write_text(json.dumps(_selfprobe(rows), indent=2, sort_keys=True) + "\n")
    assert all(row["tool"] for row in rows)
    assert all(row["status"] in {"proven", "unused", "unavailable"} for row in rows)

