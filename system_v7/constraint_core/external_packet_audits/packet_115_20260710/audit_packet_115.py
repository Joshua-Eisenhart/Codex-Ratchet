#!/usr/bin/env python3
"""Audit packet 115's withdrawn sixteen-stage invariant scaffold."""

from __future__ import annotations

import argparse
import hashlib
import json
import types
import zipfile
from pathlib import Path

import numpy as np


EXPECTED_ZIP_SHA256 = "05b6ad7da524f38f730cc9e5d4714d3dd3959afc8e1517b6bf8346098ba0316a"
EXPECTED_MEMBER_COUNT = 485
EXPECTED_SOURCE_SHA256 = "58f481a8555ae00b59f6927010d8b3f86910b8f075baf37e3809fb5312c9e6a5"
EXPECTED_ADDED = {"sims_and_scripts/sixteen_stages_protect_distinct_invariants_sim.py"}
EXPECTED_CHANGED = {
    "CHANGELOG_HARDENING.md",
    "MODEL_LAYER_LEDGER.md",
    "bundle_manifest.json",
    "docs/BUNDLE_GUIDE.md",
    "docs/MATH_INVENTORY.md",
    "docs/TOOLS_AND_REPOS.md",
    "docs/UP_REGISTRY.md",
    "docs/WITHDRAWN_AND_FAILED.md",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256(path)
        for path in root.rglob("*")
        if path.is_file()
    }


def load_module(path: Path):
    module = types.ModuleType("packet115_stage_scaffold")
    module.__file__ = str(path)
    code = compile(path.read_text(encoding="utf-8"), str(path), "exec")
    exec(code, module.__dict__)
    return module


def composed_channel_observable_counts(module) -> list[int]:
    basis = (module.I2, module.sx, module.sy, module.sz)
    counts = []
    for terrain, operator in module.STAGES:
        terrain_flow = module.gen(terrain)
        operation = module.op(operator)

        def channel(rho):
            return module.flow(terrain_flow, operation(rho))

        liouville = np.zeros((4, 4), dtype=complex)
        for column, element in enumerate(basis):
            image = channel(element)
            liouville[:, column] = [0.5 * np.trace(readout @ image) for readout in basis]
        # Fixed points of the dual map are conserved observables.
        values = np.linalg.eigvals(liouville.conj().T)
        counts.append(int(np.count_nonzero(np.abs(values - 1.0) < 2e-5)))
    return counts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-zip", type=Path, required=True)
    parser.add_argument("--packet-112-root", type=Path, required=True)
    parser.add_argument("--pristine-root", type=Path, required=True)
    parser.add_argument("--rerun-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with zipfile.ZipFile(args.packet_zip) as archive:
        names = archive.namelist()
        safe_names = all(not name.startswith("/") and ".." not in Path(name).parts for name in names)
        integrity_ok = archive.testzip() is None

    packet112 = hashes(args.packet_112_root)
    packet115 = hashes(args.pristine_root)
    added = set(packet115) - set(packet112)
    removed = set(packet112) - set(packet115)
    changed = {name for name in set(packet112) & set(packet115) if packet112[name] != packet115[name]}

    source = args.pristine_root / next(iter(EXPECTED_ADDED))
    rerun_result = args.rerun_root / "sims_and_scripts/sixteen_stages_protect_distinct_invariants_sim_results.json"
    source_text = source.read_text(encoding="utf-8")
    runner_text = (args.pristine_root / "run_all.py").read_text(encoding="utf-8")
    ledger_text = (args.pristine_root / "MODEL_LAYER_LEDGER.md").read_text(encoding="utf-8")
    rerun = json.loads(rerun_result.read_text(encoding="utf-8"))
    module = load_module(source)
    observable_counts = composed_channel_observable_counts(module)

    checks = {
        "packet_zip_hash": sha256(args.packet_zip) == EXPECTED_ZIP_SHA256,
        "zip_member_count": len(names) == EXPECTED_MEMBER_COUNT,
        "zip_member_names_safe": safe_names,
        "zip_integrity": integrity_ok,
        "delta_added_exact": added == EXPECTED_ADDED,
        "delta_removed_empty": not removed,
        "delta_changed_exact": changed == EXPECTED_CHANGED,
        "run_all_byte_identical_to_packet_112": packet115["run_all.py"] == packet112["run_all.py"],
        "source_hash": sha256(source) == EXPECTED_SOURCE_SHA256,
        "source_explicitly_withdrawn": "WITHDRAWN SCAFFOLD" in source_text,
        "source_not_registered": source.name not in runner_text,
        "standalone_green_reproduced": rerun["policy_eval"]["ENGINE_STAGES_PROTECT_DISTINCT_INVARIANTS_TWO_LEVEL"] is True,
        "standalone_result_nonpromotable": rerun.get("classification") == "scratch_diagnostic" and rerun.get("promotion_allowed") is False,
        "spinor_gate_reads_installed_epsilon": "H=eps*(sx+sy+sz)" in source_text and "carries eps sign" in source_text,
        "feature_vector_is_concatenated": "np.concatenate([ax, cspec, fp, [sv]])" in source_text,
        "composed_channels_only_trivial_dual_fixed_observable": observable_counts == [1] * 16,
        "ledger_records_withdrawal": "UP-141 -- WITHDRAWN" in ledger_text,
    }

    output = {
        "schema": "codex_ratchet.packet_115_audit.v1",
        "classification": "external_packet_delta_and_withdrawn_scaffold_audit",
        "packet_zip_sha256": sha256(args.packet_zip),
        "source_hashes": {
            "withdrawn_scaffold": sha256(source),
            "standalone_rerun_result": sha256(rerun_result),
        },
        "checks": checks,
        "check_count": len(checks),
        "all_pass": all(checks.values()),
        "standalone_reported_pass": True,
        "composed_channel_dual_fixed_observable_counts": observable_counts,
        "scientific_verdict": "WITHDRAWN_COMPOSITE_KEY_SCAFFOLD_WITH_NEGATIVE_INVARIANT_RESULT",
        "claim_ceiling": "packet_115_reproduces_a_green_withdrawn_scaffold_but_all_16_composed_channels_have_only_the_trivial_density_level_conserved_observable",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "blocked_consumers": [
            "sixteen distinct protected invariants",
            "four-substage or 64-stage derivation",
            "Axis0, perception, objects, MMMs, ontologies, mesh, business, or physics admission",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if output["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
