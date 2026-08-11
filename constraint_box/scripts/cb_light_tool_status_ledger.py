#!/usr/bin/env python3
"""Render a bounded, row-level CB Light status ledger from current receipts.

This is a read-only reporting consumer.  It does not select, adopt, promote,
or install a tool; those decisions remain in the manifest and selection
receipts it validates before rendering.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECEIPTS = ROOT / "receipts"


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def keyed(rows: Any, *, source: str) -> dict[str, dict[str, Any]]:
    if not isinstance(rows, list):
        raise ValueError(f"{source} rows missing")
    result: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"{source} row malformed")
        name = row.get("normalized_name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"{source} row identity missing")
        if name in result:
            raise ValueError(f"{source} duplicate identity: {name}")
        result[name] = row
    return result


def bool_field(row: dict[str, Any], field: str) -> bool:
    return row.get(field) is True


def receipt_binding(path: Path, body: dict[str, Any]) -> dict[str, str]:
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "manifest_identity_sha256": str(body["manifest_identity_sha256"]),
    }


def render() -> dict[str, Any]:
    manifest_path = ROOT / "config" / "cb_light_tools_v1.json"
    contract_path = ROOT / "config" / "cb_light_contract_v1.json"
    manifest = load_json(manifest_path)
    contract = load_json(contract_path)
    manifest_id = manifest.get("manifest_sha256")
    if not isinstance(manifest_id, str):
        raise ValueError("manifest identity missing")

    receipt_paths = {
        "runtime_install": RECEIPTS / "cb_light_install_runtime_v1.json",
        "clean_install": RECEIPTS / "cb_light_install_clean_v1.json",
        "metadata": RECEIPTS / "cb_light_metadata_v1.json",
        "operation": RECEIPTS / "cb_light_tool_probes_v1.json",
        "selection": RECEIPTS / "cb_light_selection_v1.json",
        "hook": RECEIPTS / "cb_light_hook_run_v1.json",
    }
    bodies = {label: load_json(path) for label, path in receipt_paths.items()}
    for label, body in bodies.items():
        if body.get("manifest_identity_sha256") != manifest_id:
            raise ValueError(f"stale manifest binding: {label}")

    manifest_rows = keyed(manifest.get("tools"), source="manifest")
    runtime_rows = keyed(bodies["runtime_install"].get("rows"), source="runtime")
    clean_rows = keyed(bodies["clean_install"].get("rows"), source="clean")
    metadata_rows = keyed(bodies["metadata"].get("rows"), source="metadata")
    operation_rows = keyed(
        bodies["operation"].get("tool_decisions"), source="operation"
    )
    selection_rows = keyed(bodies["selection"].get("rows"), source="selection")

    names = set(manifest_rows)
    for label, rows in {
        "runtime": runtime_rows,
        "clean": clean_rows,
        "metadata": metadata_rows,
        "operation": operation_rows,
        "selection": selection_rows,
    }.items():
        if set(rows) != names:
            raise ValueError(
                f"{label} domain mismatch: missing={sorted(names-set(rows))}, "
                f"extra={sorted(set(rows)-names)}"
            )

    row_ledger: list[dict[str, Any]] = []
    for name in sorted(names):
        tool = manifest_rows[name]
        runtime = runtime_rows[name]
        clean = clean_rows[name]
        metadata = metadata_rows[name]
        operation = operation_rows[name]
        selection = selection_rows[name]
        row_ledger.append(
            {
                "normalized_name": name,
                "distribution": tool["distribution"],
                "locked_version": tool["locked_version"],
                "import_name": tool["import_names"][0],
                "source_group": tool["source_group"],
                "role_class": tool["role_class"],
                "role": tool["role"],
                "lifecycle": {
                    "proposed_light": tool.get("membership") == "PROPOSED_LIGHT",
                    "runtime_install": {
                        "installed": bool_field(runtime, "installed"),
                        "version_matches": bool_field(runtime, "version_matches"),
                        "import_passed": bool_field(
                            runtime.get("import_probe", {}), "passed"
                        ),
                        "provider_bound": bool_field(
                            runtime, "expected_provider_present"
                        ),
                    },
                    "clean_install": {
                        "installed": bool_field(clean, "installed"),
                        "version_matches": bool_field(clean, "version_matches"),
                        "import_passed": bool_field(
                            clean.get("import_probe", {}), "passed"
                        ),
                        "provider_bound": bool_field(
                            clean, "expected_provider_present"
                        ),
                    },
                    "metadata": {
                        "disposition": metadata["disposition"],
                        "reason_code": metadata["reason_code"],
                        "failed_predicates": metadata.get("failed_predicates", []),
                    },
                    "operation": {
                        "disposition": operation["disposition"],
                        "reason_code": operation["reason_code"],
                        "failed_facts": operation.get("failed_facts", []),
                        "probe_structure_issues": operation.get(
                            "probe_structure_issues", []
                        ),
                    },
                    "current_work_selection": {
                        "disposition": selection["work_disposition"],
                        "reason_code": selection["reason_code"],
                        "failed_constraints": selection.get(
                            "failed_usable_now_constraints", []
                        ),
                    },
                    "owner_approved_adoption": False,
                    "portable_adoption": selection["portable_adoption_disposition"],
                    "cb_heavy_authorization": "NOT_IN_SCOPE",
                },
            }
        )

    exclusions = manifest.get("preinstall_excluded_candidates")
    if not isinstance(exclusions, list):
        raise ValueError("manifest exclusions missing")
    expected_exclusions = set(contract.get("preinstall_excluded_names") or [])
    exclusion_names = {
        row.get("normalized_name") for row in exclusions if isinstance(row, dict)
    }
    if exclusion_names != expected_exclusions:
        raise ValueError("preinstall exclusion set differs from contract")

    selected = [
        row
        for row in row_ledger
        if row["lifecycle"]["current_work_selection"]["disposition"]
        == "SELECTED_FOR_WORK"
    ]
    held = [row for row in row_ledger if row not in selected]
    body: dict[str, Any] = {
        "schema": "constraintbox.cb-light-tool-status-ledger.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "manifest_identity_sha256": manifest_id,
        "claim_ceiling": (
            "Read-only row-level status of the contained CB Light proposal domain. "
            "It is not an adoption, portability, CB Heavy, simulation, promotion, "
            "or release ledger."
        ),
        "controller_infrastructure": {
            "distributions": ["pip", "constraintbox"],
            "rule": (
                "Installer and local controller only; neither is a member of the "
                "finite 91-tool candidate domain."
            ),
        },
        "constraints_used_for_current_work_selection": contract[
            "usable_now_requires"
        ],
        "counts": {
            "proposed_light_tools": len(row_ledger),
            "preinstall_excluded_candidates": len(exclusions),
            "runtime_installed_exact": sum(
                row["lifecycle"]["runtime_install"]["installed"]
                and row["lifecycle"]["runtime_install"]["version_matches"]
                and row["lifecycle"]["runtime_install"]["import_passed"]
                and row["lifecycle"]["runtime_install"]["provider_bound"]
                for row in row_ledger
            ),
            "clean_installed_exact": sum(
                row["lifecycle"]["clean_install"]["installed"]
                and row["lifecycle"]["clean_install"]["version_matches"]
                and row["lifecycle"]["clean_install"]["import_passed"]
                and row["lifecycle"]["clean_install"]["provider_bound"]
                for row in row_ledger
            ),
            "operation_admit": sum(
                row["lifecycle"]["operation"]["disposition"] == "ADMIT"
                for row in row_ledger
            ),
            "operation_hold": sum(
                row["lifecycle"]["operation"]["disposition"] == "HOLD"
                for row in row_ledger
            ),
            "selected_for_work": len(selected),
            "held_for_missing_evidence": len(held),
            "owner_approved_adoptions": 0,
            "portable_adoptions": 0,
            "cb_heavy_authorizations": 0,
        },
        "receipt_bindings": {
            label: receipt_binding(receipt_paths[label], body)
            for label, body in bodies.items()
        },
        "preinstall_excluded_candidates": exclusions,
        "tools": row_ledger,
    }
    if body["counts"]["proposed_light_tools"] != 91:
        raise ValueError("unexpected proposed Light tool count")
    if body["counts"]["selected_for_work"] != 86:
        raise ValueError("unexpected selected-for-work count")
    return body


def main() -> int:
    parser = argparse.ArgumentParser(prog="cb-light-tool-status-ledger")
    parser.add_argument(
        "--output",
        type=Path,
        default=RECEIPTS / "cb_light_tool_status_ledger_v1.json",
    )
    args = parser.parse_args()
    body = render()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    print(
        "CB Light tool ledger: "
        f"proposed={body['counts']['proposed_light_tools']}, "
        f"selected={body['counts']['selected_for_work']}, "
        f"held={body['counts']['held_for_missing_evidence']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
