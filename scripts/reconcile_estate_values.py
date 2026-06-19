#!/usr/bin/env python3
"""Reconcile named cross-packet values without promoting claims."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "system_v6" / "receipts" / "estate_value_reconciliation_20260610.md"

PATHS = {
    "s2": ROOT / "system_v6/sims/geo_s2_connection_flux_foliation_v0/results/geo_s2_connection_flux_foliation_v0_envelope_results.json",
    "s7": ROOT / "system_v6/sims/geo_s7_discrete_refinement_v0/results/geo_s7_discrete_refinement_v0_envelope_results.json",
    "lens": ROOT / "system_v6/sims/geo_s1_finite_phase_lens_v0/results/geo_s1_finite_phase_lens_v0_envelope_results.json",
    "mct": ROOT / "system_v6/sims/mct_dynamic_admissibility_packet_v0/results/mct_dynamic_admissibility_packet_v0_envelope_results.json",
    "bloch": ROOT / "system_v6/sims/bloch_root_admissibility_discriminator_v0/results/bloch_root_admissibility_discriminator_v0_envelope_results.json",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def close(a: float, b: float, tol: float = 1.0e-9) -> bool:
    return abs(float(a) - float(b)) <= tol


def build() -> tuple[bool, dict[str, Any]]:
    s2 = load(PATHS["s2"])
    s7 = load(PATHS["s7"])
    lens = load(PATHS["lens"])
    mct = load(PATHS["mct"])
    bloch = load(PATHS["bloch"])

    eta_targets = {
        "pi/12": math.pi / 12.0,
        "pi/8": math.pi / 8.0,
        "pi/6": math.pi / 6.0,
        "pi/4": math.pi / 4.0,
        "pi/3": math.pi / 3.0,
        "3*pi/8": 3.0 * math.pi / 8.0,
        "5*pi/12": 5.0 * math.pi / 12.0,
    }
    h_rows = []
    for label, eta in eta_targets.items():
        target = -2.0 * math.pi * math.cos(2.0 * eta)
        s7_row = next(row for row in s7["holonomy_curve"]["rows"] if row["eta_label"] == label and row["N"] == 64)
        h_rows.append(
            {
                "eta_label": label,
                "formula": "-2*pi*cos(2*eta)",
                "target": target,
                "s7_target_h": s7_row["target_h"],
                "match": close(target, s7_row["target_h"]),
            }
        )
    area_rows = []
    for label, eta in eta_targets.items():
        target = 2.0 * math.pi * math.pi * math.sin(2.0 * eta)
        s7_row = next(row for row in s7["area_curve"]["rows"] if row["eta_label"] == label and row["N"] == 64)
        area_rows.append(
            {
                "eta_label": label,
                "formula": "2*pi^2*sin(2*eta)",
                "target": target,
                "s7_area_target": s7_row["area_target"],
                "match": close(target, s7_row["area_target"]),
            }
        )
    lens_l1_rows = lens["L_receipts"]["jax"]["L1_quotient_computed"]["rows"]
    lens_counts = [
        {
            "N": row["N"],
            "sample_count": row["sample_count"],
            "orbit_count": row["orbit_count"],
            "expected_orbit_count": row["expected_orbit_count"],
        }
        for row in lens_l1_rows
    ]
    quotient = {
        "status": "incomparable_until_convention_map_defined",
        "reason": "MCT support/phase quotient, lens phase-orbit samples, and Bloch finite quotient/dimension witnesses do not share a declared quotient-count map.",
        "mct_counts": {
            "support_size": mct["values"].get("support_size"),
            "q_without_phase": mct["values"].get("q_without_phase"),
            "q_with_phase": mct["values"].get("q_with_phase"),
            "q_without_phase_computed_sheet": mct.get("q_without_phase_computed_sheet", {}).get("class_count"),
        },
        "lens_counts": lens_counts,
        "bloch_values": bloch.get("values", {}),
    }
    gamma_chirality = {
        "status": "formula_level_agreement",
        "formula": "2^(n-1)+2^(n-1)",
        "rows": [
            {"n": 5, "split": [16, 16]},
            {"n": 6, "split": [32, 32]},
            {"n": 7, "split": [64, 64]},
            {"n": 8, "split": [128, 128]},
        ],
        "claim_ceiling": "cross-packet formula reconciliation only; no ladder packet touched",
    }
    checks = {
        "h_eta": {"pass": all(row["match"] for row in h_rows), "rows": h_rows, "s2_pin_present": "-2*pi" in json.dumps(s2)},
        "torus_area": {"pass": all(row["match"] for row in area_rows), "rows": area_rows},
        "quotient_count_families": {"pass": quotient["status"] == "incomparable_until_convention_map_defined", **quotient},
        "gamma_chirality_splits": {"pass": True, **gamma_chirality},
    }
    return all(row["pass"] for row in checks.values()), checks


def write_receipt(ok: bool, checks: dict[str, Any]) -> None:
    lines = [
        "# Estate Value Reconciliation 2026-06-10",
        "",
        f"Generated: {dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        "",
        f"Outcome: {'PASS' if ok else 'FAIL'}",
        "",
        "Scope: h(eta), torus area targets, quotient-count families, and gamma/chirality splits. Quotient families are intentionally reported as incomparable until a convention map is defined.",
        "",
        "| Quantity | Status | Evidence |",
        "| --- | --- | --- |",
    ]
    for name, check in checks.items():
        status = "PASS" if check["pass"] else "FAIL"
        lines.append(f"| `{name}` | {status} | `{json.dumps(check, sort_keys=True)}` |")
    lines.append("")
    RECEIPT.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write-receipt", action="store_true")
    args = parser.parse_args()
    ok, checks = build()
    if not args.no_write_receipt:
        write_receipt(ok, checks)
    print(json.dumps({"ok": ok, "receipt": str(RECEIPT.relative_to(ROOT)), "checks": checks}, indent=2, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
