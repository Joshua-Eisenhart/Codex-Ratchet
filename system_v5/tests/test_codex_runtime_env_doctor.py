from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import codex_runtime_env_doctor as doctor


def report_with_manifest(**manifest_overrides: object) -> dict:
    repo_project = {
        "forbidden_deps_present": [],
        "manifest_present": True,
        "manifest_tracked": True,
        "manifest_ignored": False,
        "manifest_parse_error": None,
        "manifest_metadata": {
            "julia_version": "1.12.6",
            "manifest_format": "2.0",
            "project_hash": "abc123",
        },
        "manifest_absolute_path_entries": [],
        **manifest_overrides,
    }
    return {
        "sim_stack_alias": {"exists": True, "ok": True},
        "python": {
            "exists": True,
            "modules": {name: {"ok": True} for name in doctor.PYTHON_EXPECT_OK},
        },
        "julia": {"skipped": True},
        "repo_project": repo_project,
        "repo_pollution": [],
        "active_installers": {"ok": True, "matches": []},
    }


def test_portable_manifest_state_is_accepted() -> None:
    assert doctor.summarize(report_with_manifest())["ok"] is True


def test_manifest_portability_mutations_fail_closed() -> None:
    mutations = [
        {"manifest_present": False},
        {"manifest_tracked": False},
        {"manifest_ignored": True},
        {"manifest_parse_error": "bad TOML"},
        {"manifest_metadata": {"julia_version": "1.12.6", "manifest_format": "2.0"}},
        {"manifest_absolute_path_entries": ["/Users/example/local-package"]},
    ]
    for mutation in mutations:
        summary = doctor.summarize(report_with_manifest(**mutation))
        assert summary["ok"] is False, mutation
        assert summary["failures"], mutation


def test_live_carrier_manifest_has_static_portability_fields() -> None:
    state = doctor.project_dep_scan(ROOT)
    assert state["manifest_present"] is True
    assert state["manifest_ignored"] is False
    assert state["manifest_parse_error"] is None
    assert state["manifest_absolute_path_entries"] == []
    assert state["manifest_metadata"]["project_hash"]
