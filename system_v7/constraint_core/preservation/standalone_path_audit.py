#!/usr/bin/env python3
"""Verify that the recent/dark science instruments resolve inside the ZIP."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMS = ROOT / "sims_and_scripts"
REPORT = ROOT / "reports" / "STANDALONE_PATH_AUDIT.json"

PORTABLE_SET = [
    "admissibility_census_general_d_sim.py",
    "alfsen_shultz_correspondence_probe_sim.py",
    "choi_field_multiaxis_null_albert_stress_sim.py",
    "engine_field_choi_jordan_albert_probe_sim.py",
    "j3o_bloch_body_entropy_pawl_sim.py",
    "jordan_dissipator_pawl_v2_sim.py",
    "jordan_dpi_probe_v3_sim.py",
    "jordan_dpi_probe_v4_sim.py",
    "jordan_octonion_entropy_pawl_sim.py",
    "spin9_stabilizer_op2_coset_sim.py",
]

EXPLICIT_EXTERNAL = [
    {
        "script": "v7_codex_ratchet_crosscheck_sim.py",
        "dependency": "owner desktop Codex-Ratchet result",
        "status": "KNOWN_EXTERNAL_NOT_MATERIALIZED__SCRIPT_SKIP_CLEAN",
    },
    {
        "script": "four_substages_up130_fabrication_audit_sim.py",
        "dependency": "owner desktop 97.zip with fixed SHA-256",
        "status": "KNOWN_EXTERNAL_NOT_MATERIALIZED__AUDIT_CANNOT_REPLAY_HERE",
    },
]


def main() -> int:
    rows = []
    for name in PORTABLE_SET:
        path = SIMS / name
        text = path.read_text(encoding="utf-8")
        forbidden = {
            "parents_3_repo_assumption": "parents[3]" in text,
            "hardcoded_system_v7_self_path": 'ROOT / "system_v7/constraint_core/sims_and_scripts' in text,
            "hardcoded_system_v7_sim_dir": 'SIM_DIR = ROOT / "system_v7/constraint_core/sims_and_scripts"' in text,
        }
        rows.append({
            "script": name,
            "exists": path.is_file(),
            "forbidden_matches": forbidden,
            "portable_path_gate": path.is_file() and not any(forbidden.values()),
        })

    report = {
        "schema": "ratchet.standalone-path-audit.v1",
        "portable_recent_science_scripts": rows,
        "portable_script_count": len(rows),
        "explicit_external_dependencies": EXPLICIT_EXTERNAL,
        "all_portable_path_gates_pass": all(row["portable_path_gate"] for row in rows),
        "claim_ceiling": "Checks source/result path resolution only. It does not supply optional runtimes or validate scientific claims.",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    if not report["all_portable_path_gates_pass"]:
        for row in rows:
            if not row["portable_path_gate"]:
                print(f"FAIL {row['script']}: {row['forbidden_matches']}")
        return 1
    print("PASS standalone path audit")
    print("10 recent science scripts are bundle-relative; 2 historical external probes are explicitly fenced")
    return 0


if __name__ == "__main__":
    sys.exit(main())

