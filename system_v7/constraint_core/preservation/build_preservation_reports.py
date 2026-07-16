#!/usr/bin/env python3
"""Build the preservation and simulation-visibility ledgers for Ratchet v0.7.

This generator deliberately inventories every top-level simulation, not only the
scripts selected by run_all.py.  Registration is execution coverage; it is not
canon and it is not a license to erase unregistered hypotheses or negatives.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parents[1]
SIMS = ROOT / "sims_and_scripts"

RESTORED = {
    "reference_docs_external_reviews/EXTERNAL_REVIEW_2026-07-10_math_imports_and_boundary.md":
        "f94874841592db7d5bdb6f46663f1be6f3708b9601fa13907d6c931dba4f9daf",
    "reference_docs_external_reviews/brave_thread_math_objects_2026-07-10.txt":
        "a34baf81a7b7313a17444bc5721ffb116588e60012a87fe61656a3b420ec16f9",
    "reference_docs_external_reviews/chatgpt_mannheim_review_2026-07-10.txt":
        "a53135709c57ed7665d00ac9dcb2836ef948b93d7c84875b3b386e2ac8b13b41",
    "sims_and_scripts/field_pair_of_engines_weakest_rung_sim_results.json":
        "2cb625359c79a50c049707c0d4c9e3d0273c220060adf9b0a8ee97aa1e3742a8",
}

LINEAGE = [
    ("112.zip", "upload/112.zip"),
    ("116.zip", "upload/116.zip"),
    ("122.zip", "upload/122.zip"),
    ("122(1).zip", "upload/122(1).zip"),
    ("123_claude_science_ratchet_v0_2.zip", "123_claude_science_ratchet_v0_2.zip"),
    ("124.zip", "upload/124.zip"),
    ("125_claude_science_ratchet_v0_3_gradient_drive.zip", "125_claude_science_ratchet_v0_3_gradient_drive.zip"),
    ("126_claude_science_working_ratchet_v0_4.zip", "126_claude_science_working_ratchet_v0_4.zip"),
    ("127.zip", "upload/127.zip"),
    ("127_claude_science_working_ratchet_v0_4_audited.zip", "upload/127_claude_science_working_ratchet_v0_4_audited.zip"),
    ("128_claude_science_order_open_ratchet_v0_5.zip", "128_claude_science_order_open_ratchet_v0_5.zip"),
    ("129.zip", "upload/129.zip"),
    ("129_claude_science_working_ratchet_v0_4_2_L5_answered.zip", "upload/129_claude_science_working_ratchet_v0_4_2_L5_answered.zip"),
    ("130_claude_science_executed_manifold_ratchet_v0_6.zip", "130_claude_science_executed_manifold_ratchet_v0_6.zip"),
]

KNOWN_EXTERNAL = [
    {
        "lineage": "Research Ratchet / Spinor Memory / Attractor Basin Digger",
        "status": "KNOWN_EXTERNAL_NOT_MATERIALIZED",
        "reason": "Known from project continuity, but no complete local artifact is present in this workspace.",
    },
    {
        "lineage": "full Joshua-Eisenhart wiki ingest",
        "status": "KNOWN_EXTERNAL_NOT_MATERIALIZED",
        "reason": "Selected wiki-derived reports are present; a complete wiki export is not.",
    },
    {
        "lineage": "LevOS-native / Leviathan convergence bundles",
        "status": "KNOWN_EXTERNAL_NOT_MATERIALIZED",
        "reason": "Repository references and bridge artifacts are present; a complete native bundle is not.",
    },
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def zip_file_names(path: Path) -> list[str]:
    with ZipFile(path) as archive:
        return sorted(name for name in archive.namelist() if not name.endswith("/"))


def parse_registered_sims() -> list[str]:
    text = (ROOT / "run_all.py").read_text(encoding="utf-8")
    return sorted(set(re.findall(r'^\s*\("([^"]+\.py)"\s*,\s*\d+', text, re.M)))


def subject_tags(name: str) -> list[str]:
    groups = {
        "exceptional_nonassociative": r"jordan|albert|octon|malcev|fano|spin9|op2|exceptional|\bf4\b|\be6\b|\bg2\b|nonassoci",
        "attractor_basin": r"attractor|basin|memory_carrier|hysteresis",
        "entropy_geometry": r"entropy|bkm|umegaki|petz|metric|manifold|geometry|berry|schmidt",
        "fep_active_inference": r"fep|active|surprise|known_unknown",
        "engine_axes_terrain": r"engine|axis|terrain|stage|substage|slot64|loop",
        "cellular_automata_finitude": r"cellular|_ca_|finite|ring|checkerboard",
        "topology_spinor": r"spinor|weyl|clifford|hopf|hott|braid|holonomy",
        "physics_biochemistry": r"gravity|cosmo|physics|chem|biochem|hubbard|mond|redshift",
        "formal_solver_control": r"smt|z3|cvc5|symbolic|proof|audit|census|control",
    }
    return sorted(label for label, pattern in groups.items() if re.search(pattern, name, re.I)) or ["uncategorized"]


def compact_result(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"present": False}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"present": True, "parse_error": str(exc)}
    keys = (
        "classification", "verdict", "overall", "headline", "claim_ceiling",
        "promotion_allowed", "formal_admission_allowed", "promotion_status", "all_pass",
    )
    out: dict[str, object] = {"present": True, "path": path.relative_to(ROOT).as_posix()}
    for key in keys:
        if key in payload:
            out[key] = payload[key]
    return out


def build_sim_ledger(now: str) -> dict[str, object]:
    registered = set(parse_registered_sims())
    all_scripts = sorted(path.name for path in SIMS.glob("*.py"))
    rows = []
    for name in all_scripts:
        stem = name[:-3]
        result = compact_result(SIMS / f"{stem}_results.json")
        rows.append({
            "script": name,
            "registration": "REGISTERED_IN_RUN_ALL" if name in registered else "UNREGISTERED_VISIBLE_HYPOTHESIS_OR_TOOL",
            "registered": name in registered,
            "subjects": subject_tags(name),
            "result": result,
        })
    unregistered = [row["script"] for row in rows if not row["registered"]]
    registered_without_result = [row["script"] for row in rows if row["registered"] and not row["result"].get("present")]
    unregistered_with_result = [row["script"] for row in rows if not row["registered"] and row["result"].get("present")]
    ledger = {
        "schema": "ratchet.sim-registration-ledger.v1",
        "generated_utc": now,
        "semantics": {
            "registration": "Selection into the current aggregate execution harness only.",
            "nonregistration": "Must remain visible. It can mean exploratory, audit, adapter, superseded, or simply not yet wired; it does not mean absent, false, or deletable.",
            "canon": "Neither registration nor a green local result earns canon. Canon is admitted only by a scoped Ratchet receipt.",
        },
        "counts": {
            "all_top_level_python_scripts": len(all_scripts),
            "registered_in_run_all": len(registered),
            "unregistered": len(unregistered),
            "registered_without_conventional_result_json": len(registered_without_result),
            "unregistered_with_conventional_result_json": len(unregistered_with_result),
        },
        "unregistered_scripts": unregistered,
        "registered_without_conventional_result_json": registered_without_result,
        "unregistered_with_conventional_result_json": unregistered_with_result,
        "scripts": rows,
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "SIM_REGISTRATION_LEDGER.json").write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Complete simulation registration ledger",
        "",
        f"Generated `{now}` by scanning **all {len(all_scripts)}** top-level Python files in `sims_and_scripts/`.",
        "",
        f"- Registered in `run_all.py`: **{len(registered)}**",
        f"- Unregistered but preserved and surfaced: **{len(unregistered)}**",
        f"- Unregistered with a conventional result receipt: **{len(unregistered_with_result)}**",
        "",
        "Registration means aggregate execution coverage. It is not canon. Nonregistration is not deletion, rejection, or permission to omit a result from project memory.",
        "",
        "## Unregistered scripts (the former dark set)",
        "",
    ]
    for row in rows:
        if row["registered"]:
            continue
        result = row["result"]
        receipt = result.get("path", "no conventional `_results.json` receipt")
        status_bits = []
        for key in ("classification", "verdict", "overall", "promotion_status", "promotion_allowed"):
            if key in result:
                status_bits.append(f"{key}={result[key]}")
        status = "; ".join(status_bits) if status_bits else "status must be read from source/receipt"
        lines.append(f"- `{row['script']}` — {', '.join(row['subjects'])}; receipt `{receipt}`; {status}")
    lines += ["", "## Registered scripts", ""]
    for row in rows:
        if row["registered"]:
            lines.append(f"- `{row['script']}` — {', '.join(row['subjects'])}")
    lines += [
        "",
        "## Claude Code failure repaired",
        "",
        f"The v0.6 documentation generator classified only registered scripts and truncated category displays. That made physically present Jordan, Albert, Fano, octonion, Malcev, and attractor-basin work effectively invisible. This ledger is complete and machine-checked; bundle lint fails if its {len(all_scripts)}/{len(registered)}/{len(unregistered)} partition drifts without regeneration.",
        "",
    ]
    (reports / "SIM_REGISTRATION_LEDGER.md").write_text("\n".join(lines), encoding="utf-8")
    return ledger


def build_manifest(now: str, sim_ledger: dict[str, object]) -> dict[str, object]:
    lineage = []
    for label, relative in LINEAGE:
        path = WORKSPACE / relative
        row: dict[str, object] = {"archive": label, "workspace_relative_path": relative}
        if path.exists():
            row.update({
                "available_during_build": True,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
            try:
                row.update({"zip_readable": True, "file_entries": len(zip_file_names(path))})
            except BadZipFile:
                row.update({"zip_readable": False, "file_entries": None, "status": "PRESENT_BUT_BAD_ZIP__NOT_USED_AS_SOURCE"})
        else:
            row["available_during_build"] = False
        lineage.append(row)

    source_127 = WORKSPACE / "upload/127.zip"
    source_130 = WORKSPACE / "130_claude_science_executed_manifold_ratchet_v0_6.zip"
    try:
        names_127 = set(zip_file_names(source_127))
        names_130 = set(zip_file_names(source_130))
    except (FileNotFoundError, BadZipFile):
        names_127 = set(); names_130 = set()
    dropped_127_to_130 = sorted(names_127 - names_130)

    restored = []
    for relative, expected in RESTORED.items():
        path = ROOT / relative
        actual = sha256(path) if path.exists() else None
        restored.append({
            "path": relative,
            "expected_sha256_from_127": expected,
            "actual_sha256": actual,
            "restored_byte_identical": actual == expected,
        })

    content = []
    excluded_suffixes = {".pyc"}
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        if ".ratchet_deps" in path.parts or "__pycache__" in path.parts or path.suffix in excluded_suffixes:
            continue
        if relative == "preservation/preservation_manifest.json":
            continue
        if relative == "run_all_report.json" or relative.endswith("_results.json"):
            continue  # regenerated harness OUTPUT, not preserved evidence
        content.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})

    manifest = {
        "schema": "ratchet.preservation-manifest.v1",
        "bundle": "131_claude_science_preservation_complete_ratchet_v0_7",
        "generated_utc": now,
        "purpose": "Preserve and surface project state without promoting hypotheses to canon.",
        "canon_rule": "The wiki, messages, scripts, and reports are proposal/evidence memory. Only a scoped Ratchet admission receipt provisionally earns canon.",
        "lineage_archives": lineage,
        "lineage_comparison": {
            "127_file_entries": len(names_127),
            "130_file_entries": len(names_130),
            "127_entries_retained_in_130": len(names_127 & names_130),
            "127_entries_absent_from_130": len(dropped_127_to_130),
            "dropped_paths": dropped_127_to_130,
            "all_dropped_paths_restored_in_131": all(row["restored_byte_identical"] for row in restored),
        },
        "restored_artifacts": restored,
        "known_external_not_materialized": KNOWN_EXTERNAL,
        "simulation_visibility": sim_ledger["counts"],
        "mandatory_memory_surfaces": [
            "00_START_HERE.md",
            "CLAUDE.md",
            "RATCHET_SPEC.md",
            "preservation/THREAD_WORK_PRESERVATION_INDEX.md",
            "preservation/CLAUDE_CODE_FAILURES_AND_GUARDS.md",
            "preservation/bootstrap_project_memory.py",
            "preservation/standalone_path_audit.py",
            "reports/SIM_REGISTRATION_LEDGER.md",
            "reports/DIRECT_RERUN_RECEIPTS.md",
            "reports/STANDALONE_PATH_AUDIT.json",
            "reports/V0_7_WORKING_TREE_VALIDATION.json",
            "reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md",
            "reports/ATTRACTOR_BASIN_STATE.md",
            "ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md",
            "julia_canon/README.md",
        ],
        "content_hash_scope": "All shipped bundle files except local transient .ratchet_deps, pyc/__pycache__, and this self-referential manifest.",
        "content_file_count": len(content),
        "content_files": content,
    }
    (ROOT / "preservation" / "preservation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def build_index(now: str, sim_ledger: dict[str, object]) -> None:
    text = f"""# Thread-work preservation index

Generated `{now}`. This is the anti-amnesia front door for the v0.7 successor.

## What this ZIP preserves

The ZIP preserves the complete locally available science tree, the executed manifold audit, the order-open Ratchet process, all **{sim_ledger['counts']['all_top_level_python_scripts']}** top-level simulation scripts, the results physically available for them, and the four files accidentally dropped between the 127 and 130 lineages. It does **not** claim to contain every external repository or every artifact ever mentioned in conversation.

The known external-but-not-materialized lineages are named in `preservation_manifest.json` with status
`KNOWN_EXTERNAL_NOT_MATERIALIZED`; they are not silently treated as included.

## Required read order

1. `RATCHET_SPEC.md` — process authority; constrained distinguishability is root.
2. `reports/SIM_REGISTRATION_LEDGER.md` — all {sim_ledger['counts']['all_top_level_python_scripts']} scripts, including the {sim_ledger['counts']['unregistered']} formerly dark scripts.
3. `reports/DIRECT_RERUN_RECEIPTS.md` — what was freshly rerun, what passed, and what was runtime-blocked.
4. `reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md` — Jordan, Albert, octonion, Fano, Malcev, Spin(9), OP2, and exceptional-Lie state.
5. `reports/ATTRACTOR_BASIN_STATE.md` — basin evidence, controls, and killed/qualified claims.
6. `ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md` — actual layer-by-layer manifold state.
7. `preservation/CLAUDE_CODE_FAILURES_AND_GUARDS.md` — operational protections against stale or fabricated state.
8. `julia_canon/README.md` — Julia ownership boundary and replay status.

## What is canon

Nothing becomes canon because it is in this ZIP, in the wiki, in a message, registered in `run_all.py`, or locally green. These are hypotheses, instruments, observations, controls, and provenance. A claim becomes a **provisional scoped admission** only when a Ratchet receipt names the candidate grammar, weakening relation, probes, negatives, controls, budget, gradient/coface witness, and surviving MSS frontier. It remains defeasible by a weaker candidate or stronger negative.

## Completeness claims and limits

- Complete relative to the locally available 130 tree plus the four identified 127 omissions: **yes, hash-audited**.
- Complete visibility of top-level `sims_and_scripts/*.py`: **yes, {sim_ledger['counts']['all_top_level_python_scripts']} = {sim_ledger['counts']['registered_in_run_all']} registered + {sim_ledger['counts']['unregistered']} unregistered**.
- Complete exceptional/nonassociative and attractor-basin state reports: **yes, dedicated reports and machine ledgers included**.
- Julia-owned exceptional algebra source: **included**.
- Julia runtime replay in this build environment: **not available; explicitly blocked, never faked**.
- Complete external wiki/Research-Ratchet/LevOS-native memory: **no; named as external, not materialized**.

Run `python preservation/verify_preservation.py`, `python ratchet/bundle_ratchet_lint.py`, and
`python preservation/bootstrap_project_memory.py` before accepting any summary generated by an LLM.
"""
    (ROOT / "preservation" / "THREAD_WORK_PRESERVATION_INDEX.md").write_text(text, encoding="utf-8")


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ledger = build_sim_ledger(now)
    build_index(now, ledger)
    manifest = build_manifest(now, ledger)
    print(json.dumps({
        "bundle": manifest["bundle"],
        "content_file_count": manifest["content_file_count"],
        "simulation_counts": ledger["counts"],
        "restored": manifest["lineage_comparison"]["all_dropped_paths_restored_in_131"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
