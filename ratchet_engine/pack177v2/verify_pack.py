#!/usr/bin/env python3
"""Verify the fuel-bearing Pack 177 manifest and executed receipts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def main() -> int:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    expected = {row["path"]: row for row in manifest["files"]}
    for relative, row in expected.items():
        path = ROOT / relative
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing or nonregular: {relative}")
            continue
        raw = path.read_bytes()
        if len(raw) != row["bytes"]:
            errors.append(f"size mismatch: {relative}")
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            errors.append(f"hash mismatch: {relative}")
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.name not in {"MANIFEST.json", "SHA256SUMS"}
    }
    extras = sorted(actual - set(expected))
    if extras:
        errors.extend(f"unmanifested: {item}" for item in extras)
    campaign = json.loads((ROOT / "receipts" / "campaign_receipt.json").read_text(encoding="utf-8"))
    if campaign.get("mathematical_motion_executed") is not True:
        errors.append("campaign receipt lacks executed motion")
    if campaign.get("canonical_project_mutated") is not False:
        errors.append("campaign receipt claims canonical mutation")
    fuel_path = ROOT / "receipts" / "fuel_obligations.json"
    schedule_path = ROOT / "receipts" / "fuel_schedule_projection.json"
    proposal_path = ROOT / "receipts" / "proposal_fuel_projection.json"
    for path in (fuel_path, schedule_path, proposal_path):
        if not path.is_file():
            errors.append(f"missing fuel receipt: {path.name}")
    if fuel_path.is_file():
        fuel = json.loads(fuel_path.read_text(encoding="utf-8"))
        if fuel.get("every_source_has_obligation") is not True:
            errors.append("fuel compiler dropped a source")
        if fuel.get("pressure_is_vector_not_scalar") is not True:
            errors.append("fuel pressure was scalarized")
    if schedule_path.is_file():
        schedule = json.loads(schedule_path.read_text(encoding="utf-8"))
        if schedule.get("all_obligations_scheduled_once") is not True:
            errors.append("fair queue is incomplete")
        if schedule.get("epistemic_score_used") is not False:
            errors.append("fair queue used an epistemic score")
    if proposal_path.is_file():
        proposal = json.loads(proposal_path.read_text(encoding="utf-8"))
        if proposal.get("all_registry_entries_retained") is not True:
            errors.append("proposal fuel was semantically deleted")
        if proposal.get("selector_access") is not False:
            errors.append("proposal labels exposed to selector")
    donor_path = ROOT / "receipts" / "donor_integrity.json"
    if not donor_path.is_file():
        errors.append("missing donor integrity receipt")
    else:
        donor = json.loads(donor_path.read_text(encoding="utf-8"))
        if donor.get("all_zip_integrity_pass") is not True:
            errors.append("donor ZIP integrity is not green")
        if len(donor.get("donors", [])) != 6:
            errors.append("expected six preserved donor archives")
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, indent=2))
        return 1
    print(json.dumps({"ok": True, "file_count": len(expected)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
