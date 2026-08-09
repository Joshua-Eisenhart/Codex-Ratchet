#!/usr/bin/env python3
"""Fail-closed structural verifier for the v9 independent-product stack."""

from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "system_v9" / "STACK_MANIFEST.json"


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def verify() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(condition), "detail": detail})

    stack = _json("system_v9/STACK_MANIFEST.json")
    version = (ROOT / "system_v9" / "VERSION").read_text(encoding="utf-8").strip()
    check("stack_version_matches", stack["stack_version"] == version, f"manifest={stack['stack_version']} file={version}")

    products = stack["products"]
    product_ids = [row["id"] for row in products]
    check("five_independent_products", len(product_ids) == len(set(product_ids)) == 5, repr(product_ids))
    known = set(product_ids)
    for product in products:
        root = ROOT / product["root"]
        version_file = ROOT / product["version_file"]
        manifest = ROOT / product["manifest"]
        check(f"product_root:{product['id']}", root.is_dir(), str(root))
        check(f"product_version:{product['id']}", version_file.is_file() and version_file.read_text(encoding="utf-8").strip() == product["version"], str(version_file))
        check(f"product_manifest:{product['id']}", manifest.is_file(), str(manifest))

    levels_body = _json(stack["tool_status_vocabulary"])
    levels = set(levels_body["ordered_levels"])
    bridges = _json(stack["bridge_registry"])["bridges"]
    bridge_ids = [row["id"] for row in bridges]
    check("bridge_ids_unique", len(bridge_ids) == len(set(bridge_ids)), repr(bridge_ids))
    for bridge in bridges:
        check(f"bridge_products:{bridge['id']}", bridge["producer"] in known and bridge["consumer"] in known, f"{bridge['producer']}->{bridge['consumer']}")
        check(f"bridge_level:{bridge['id']}", bridge["integration_level"] in levels, bridge["integration_level"])
        check(f"bridge_request_schema:{bridge['id']}", (ROOT / bridge["request_schema"]).is_file(), bridge["request_schema"])
        check(f"bridge_result_schema:{bridge['id']}", (ROOT / bridge["result_schema"]).is_file(), bridge["result_schema"])
        if bridge["adapter"] is not None:
            check(f"bridge_adapter:{bridge['id']}", (ROOT / bridge["adapter"]).exists(), bridge["adapter"])

    cb_project = tomllib.loads((ROOT / "constraint_box" / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    cb_dependencies = {entry.split("<", 1)[0].split(">", 1)[0].split("=", 1)[0].strip().lower() for entry in cb_project["dependencies"]}
    expected_cb = {"z3-solver", "cvc5", "sympy", "rustworkx", "maude"}
    check("cb_exact_five_dependencies", cb_dependencies == expected_cb, repr(sorted(cb_dependencies)))
    check("cb_default_entrypoint_is_core", cb_project["scripts"]["constraintbox"] == "constraintbox.core_cli:main", cb_project["scripts"]["constraintbox"])
    check("cb_no_embedded_claimgate", not (ROOT / "constraint_box" / "claimgate_plugin").exists(), "constraint_box/claimgate_plugin")

    cb_registry = _json("constraint_box/config/core_tool_registry_v9.json")
    cb_ids = {row["id"] for row in cb_registry["tools"]}
    check("cb_registry_exact_five", cb_ids == {"python.z3", "python.cvc5", "python.sympy", "python.rustworkx", "python.maude"}, repr(sorted(cb_ids)))

    sim_registry = _json("sim_engines/registry/tool-registry.v9.json")
    sim_tools = sim_registry["tools"]
    sim_ids = [row["id"] for row in sim_tools]
    check("sim_registry_broad", len(sim_tools) >= 80, f"count={len(sim_tools)}")
    check("sim_tool_ids_unique", len(sim_ids) == len(set(sim_ids)), f"count={len(sim_ids)}")
    check("sim_levels_valid", all(row["declared_integration_level"] in levels for row in sim_tools), "all rows use v1 vocabulary")
    for row in sim_tools:
        for path in row.get("source_paths", []) + row.get("evidence_paths", []):
            check(f"sim_path:{row['id']}:{path}", (ROOT / path).exists(), path)

    sim_live = _json("sim_engines/status/LIVE_TOOL_INDEX.json")
    live_ids = {row["id"] for row in sim_live["registered_tools"]}
    check("sim_live_index_matches_registry", live_ids == set(sim_ids), f"live={len(live_ids)} registry={len(sim_ids)}")
    check("sim_live_index_keeps_declared_levels", all("declared_integration_level" in row for row in sim_live["registered_tools"]), "declared and live state are separate")
    julia_project = tomllib.loads((ROOT / "sim_engines" / "install" / "julia" / "Project.toml").read_text(encoding="utf-8"))
    check("sim_julia_is_environment_not_false_package", not ({"name", "uuid", "version"} & set(julia_project)), repr(sorted(set(julia_project) & {"name", "uuid", "version"})))
    check("sim_julia_manifest_present", (ROOT / "sim_engines" / "install" / "julia" / "Manifest.toml").is_file(), "sim_engines/install/julia/Manifest.toml")
    check("sim_julia_direct_deps_have_compat", set(julia_project["deps"]) <= set(julia_project["compat"]), f"deps={len(julia_project['deps'])}")

    cb_live = _json("constraint_box/status/LIVE_CORE_INDEX.json")
    check("cb_live_status_exact_five", {row["id"] for row in cb_live["doctor"]["rows"]} == cb_ids, repr(cb_live["doctor"]["core_tool_ids"]))
    check("cb_live_status_excludes_heavy_runtimes", set(cb_live["excluded_runtimes"]) >= {"jax", "pytorch", "julia", "java", "pysindy"}, repr(cb_live["excluded_runtimes"]))

    holodeck_project = tomllib.loads((ROOT / "holodeck" / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    check("holodeck_default_is_light", holodeck_project["dependencies"] == [], repr(holodeck_project["dependencies"]))
    holodeck_boundary = _json("holodeck/PRODUCT_BOUNDARY.v9.json")
    check("holodeck_qit_external", "qit_engine_implementation" in holodeck_boundary["does_not_own"], repr(holodeck_boundary["does_not_own"]))

    claimgate_boundary = _json("claimgate_plugin/PRODUCT_BOUNDARY.v9.json")
    check("claimgate_authority", claimgate_boundary["canonical_root"] == "claimgate_plugin", claimgate_boundary["canonical_root"])
    check("legacy_claimgate_marked", (ROOT / "claimgate" / "AUTHORITY_STATUS.v9.md").is_file(), "claimgate/AUTHORITY_STATUS.v9.md")
    claimgate_project = tomllib.loads((ROOT / "claimgate_plugin" / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    check("claimgate_version_matches", claimgate_project["version"] == (ROOT / "claimgate_plugin" / "VERSION").read_text(encoding="utf-8").strip(), claimgate_project["version"])
    smt_source = (ROOT / "claimgate_plugin" / "ratchet_floor_smt.py").read_text(encoding="utf-8")
    check("claimgate_smt_independent_of_cb_import", "from constraintbox" not in smt_source, "ClaimGate owns finite_constraint_contract.v1")

    holodeck_live = _json("holodeck/status/LIVE_DEVELOPMENT_INDEX.json")
    check("holodeck_live_status_is_nonpromoting", holodeck_live["claim_ceiling"] == "product_scaffold_and_live_tool_visibility_only", holodeck_live["claim_ceiling"])
    check("holodeck_qit_bridge_still_blocked", holodeck_live["qit_bridge_state"].startswith("blocked_"), holodeck_live["qit_bridge_state"])

    curation = _json("system_v9/intake/DESKTOP_CURATION_INDEX_20260806.json")
    archive_hashes = [row["sha256"] for row in curation["archives"]]
    check("desktop_intake_is_bounded", curation["copied_archive_count"] == 0 and len(curation["archives"]) == 12, f"indexed={len(curation['archives'])} copied={curation['copied_archive_count']}")
    check("desktop_intake_hashes_unique", len(archive_hashes) == len(set(archive_hashes)) and all(len(value) == 64 for value in archive_hashes), f"hashes={len(archive_hashes)}")

    failures = [row for row in checks if not row["ok"]]
    return {
        "schema": "codex-ratchet.stack-verification.v9",
        "stack_version": version,
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "failures": failures,
        "claim_ceiling": "structural_product_and_bridge_verification_only",
        "promotion_allowed": False
    }


def main() -> int:
    report = verify()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
