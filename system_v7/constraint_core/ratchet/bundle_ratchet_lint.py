#!/usr/bin/env python3
"""Fail-closed lint for the v0.7 complete-memory surface and Ratchet process."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ratchet_engine import DEFAULT_PACKET, run_packet, run_self_test, validate_run


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SCOPE_MARKER = "RATCHET_V0_5_ORDER_OPEN_PROCESS"
MANIFOLD_AUDIT_MARKER = "RATCHET_V0_6_EXECUTED_MANIFOLD_AUDIT"
PRESERVATION_MARKER = "RATCHET_V0_7_PRESERVATION_COMPLETE_SURFACE"

REQUIRED_TEXT = {
    "RATCHET_SPEC.md": [
        "ROOT = CONSTRAINED_DISTINGUISHABILITY",
        "ORDER-OPEN WORKING PROCESS SPECIFICATION v0.5",
        "Gates, subgates, and their order are hypotheses",
        "32,400",
        "75 ordered set-partitions",
        "Entropy and geometry are one finite coface",
        "No claim that “L1–L5 are all earned” is imported",
        "v0.7 preservation and surfacing law",
        "196 top-level simulation scripts",
        "byte preservation",
        "semantic surfacing",
    ],
    "00_START_HERE.md": [
        SCOPE_MARKER,
        MANIFOLD_AUDIT_MARKER,
        PRESERVATION_MARKER,
        "Gate order and gate decomposition are proposal populations",
        "scientific manifold layers admitted: 0",
        "16,384-proposal",
        "150 registered + 46 unregistered",
        "EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md",
        "ATTRACTOR_BASIN_STATE.md",
    ],
    "CLAUDE.md": [
        SCOPE_MARKER,
        MANIFOLD_AUDIT_MARKER,
        PRESERVATION_MARKER,
        "RATCHET_SPEC.md",
        "Do not infer a ladder from serialization order",
        "Search all 196 scripts",
        "Julia ownership must be executable and honest",
    ],
    "STATE_OF_THE_MODEL.md": [SCOPE_MARKER],
    "MODEL_LAYER_LEDGER.md": [SCOPE_MARKER],
    "ratchet/README.md": [
        "Order-open Ratchet v0.6 evidence audit",
        "32,400",
        "all 75 ordered set-partitions",
        "L5 demotion receipt remains killed",
    ],
    "ratchet/GRADIENT_DRIVE.md": [
        "Entropy–geometry coface gradient v0.5",
        "does not run entropy on a separately installed geometry",
        "UNRESOLVED_GATE__DIG_CONTINUES",
    ],
    "ratchet/CURRENT_FRONTIER.md": [
        "29,253 parameter aliases",
        "16,384 proposals",
        "L6→L7",
        "no canonical gate order",
        "no scientific manifold layer",
        "Open unordered dig pool",
    ],
    "ratchet/runs/L5_REAUDIT_AUDIT_KILLED_NOTE.md": [
        "KILLED AS EVIDENCE",
        "WITHDRAWN as evidence",
    ],
    "archive/RATCHET_V0_5_ORDER_OPEN_UPGRADE_REPORT.md": [
        "Scientific claim ceiling: formal generated-surface process evidence",
        "75 schedule hypotheses",
        "29,253 aliases",
    ],
    "archive/INPUT_127_COMPARISON_AND_DISPOSITION.md": [
        "What the “audited” archive still got wrong",
        "Gate order, gate boundaries, and subgate count remain hypotheses",
    ],
    "archive/RATCHET_V0_5_VALIDATION_REPORT.md": [
        "109 pass / 4 fail / 33 skip",
        "Ratchet v0.5 process-integrity lane: PASS",
        "restored byte-for-byte",
    ],
    "archive/RATCHET_V0_6_MANIFOLD_EVIDENCE_UPGRADE_REPORT.md": [
        "Scientific manifold layers admitted: 0",
        "L_orientation: 9 -> 0",
        "g^{marginal}_{\\phi\\phi}=0",
    ],
    "ratchet/manifold_evidence/MANIFOLD_RATCHET_STATE_REPORT.md": [
        "**Manifold scripts executed:** L1–L8",
        "**Scientific manifold layers admitted:** **0**",
        "g^{marginal}_{\\phi\\phi}=0",
        "L8 — numbering conflict",
    ],
    "ratchet/manifold_evidence/L5_EXTERNAL_CLAIM_DISPOSITION.md": [
        "CLAIM_ONLY__SOURCE_MISSING",
        "may_change_L5_state: false",
    ],
    "ESTATE_REGISTRY.yaml": [
        "process_version: \"0.5-order-open\"",
        "gate_order_canonical: false",
        "scientific_authority: false",
    ],
    "docs/GITHUB_REPO_CONTEXT_2026-07-10.md": [
        "this v0.5 zip is a local upgraded artifact",
        "pull request was created by this upgrade",
    ],
    "preservation/THREAD_WORK_PRESERVATION_INDEX.md": [
        "anti-amnesia front door",
        "196 = 150 registered + 46 unregistered",
        "KNOWN_EXTERNAL_NOT_MATERIALIZED",
        "Julia runtime replay in this build environment",
    ],
    "preservation/CLAUDE_CODE_FAILURES_AND_GUARDS.md": [
        "registration was mistaken for existence",
        "four artifacts were silently dropped",
        "Julia ownership was asserted but not materialized",
        "A missing source is not a clean audit",
    ],
    "preservation/bootstrap_project_memory.py": [
        "PROJECT_MEMORY_SNAPSHOT",
        "scientific_layers_admitted",
        "known_external_not_materialized",
    ],
    "reports/SIM_REGISTRATION_LEDGER.md": [
        "all 196",
        "Unregistered scripts (the former dark set)",
        "Registration means aggregate execution coverage",
    ],
    "reports/DIRECT_RERUN_RECEIPTS.md": [
        "formerly dark mathematics",
        "Fresh status",
        "BLOCKED CURRENT CONTAINER",
        "ten affected recent instruments",
    ],
    "reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.md": [
        "[e_1,e_2,e_4]=2e_7",
        "dim F_4=52",
        "not Ratchet-admitted",
        "Sedenion kill",
    ],
    "reports/ATTRACTOR_BASIN_STATE.md": [
        "Probe-relative basin object",
        "v1 allocation split is therefore refuted",
        "projective distance 0.99999997",
        "no directed Ratchet tooth",
    ],
    "julia_canon/README.md": [
        "Julia-owned exceptional algebra canon",
        "LOCAL_JULIA_REPLAY_BLOCKED_RUNTIME_ABSENT",
        "does not admit octonions",
    ],
    "archive/RATCHET_V0_7_PRESERVATION_COMPLETE_UPGRADE_REPORT.md": [
        "Four restored lineage artifacts",
        "196 / 150 / 46",
        "Julia-owned source",
    ],
}

CURRENT_FRONT_DOORS = {
    "RATCHET_SPEC.md",
    "00_START_HERE.md",
    "CLAUDE.md",
    "STATE_OF_THE_MODEL.md",
    "MODEL_LAYER_LEDGER.md",
    "ratchet/README.md",
    "ratchet/GRADIENT_DRIVE.md",
    "ratchet/CURRENT_FRONTIER.md",
    "ratchet/ratchet_engine.py",
    "ratchet/ratchet_kernel.py",
}

FORBIDDEN_PATTERNS = {
    r"Every bounded run performs this order": "fixed executable ladder",
    r"active next dig queue": "canonical next-queue wording",
    r"36 candidate structures executed": "inflated v0.4 independent-structure count",
    r"nested-shell geometry\s+(?:is\s+)?(?:demoted|survives but nonminimal)": "killed L5 demotion claim",
    r"Manifold spine L1.?L5[^\n]*all earned": "unratcheted all-earned manifold claim",
    r"canonical layer list": "layer inventory promoted to canon",
    r"scheduling priority is epistemic": "operational scheduling promoted",
    r"global (?:candidate )?space exhausted": "finite-to-global exhaustion claim",
}


def _load_json(relative: str, errors: list[str]) -> object | None:
    path = ROOT / relative
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {relative}: {exc}")
        return None


def main() -> int:
    errors: list[str] = []

    for relative, needles in REQUIRED_TEXT.items():
        path = ROOT / relative
        if not path.exists():
            errors.append(f"missing front-door file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in text:
                errors.append(f"{relative} missing required v0.5 marker: {needle!r}")

    for relative in CURRENT_FRONT_DOORS:
        path = ROOT / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern, label in FORBIDDEN_PATTERNS.items():
            if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                errors.append(f"{relative} contains forbidden {label}")

    for relative in (
        "ratchet/examples/root_order_open_packet_v0_5.json",
        "ratchet/runs/root_order_open_run_v0_5.json",
        "ratchet/schemas/ratchet_order_open_run.schema.json",
        "ratchet/weakening_grammar.json",
        "ratchet/manifold_evidence/layer_execution_receipts.json",
        "ratchet/manifold_evidence/entropic_geometry_audit_results.json",
        "ratchet/manifold_evidence/manifold_fixture_ratchet_results.json",
        "ratchet/manifold_evidence/manifold_layer_state.json",
        "preservation/preservation_manifest.json",
        "reports/SIM_REGISTRATION_LEDGER.json",
        "reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.json",
        "reports/ATTRACTOR_BASIN_STATE.json",
        "julia_canon/artifacts/python_cross_validation_receipt.json",
        "reports/DIRECT_RERUN_RECEIPTS.json",
        "reports/STANDALONE_PATH_AUDIT.json",
        "reports/V0_7_WORKING_TREE_VALIDATION.json",
    ):
        _load_json(relative, errors)

    layer_receipts = _load_json("ratchet/manifold_evidence/layer_execution_receipts.json", errors)
    if isinstance(layer_receipts, dict):
        if layer_receipts.get("local_pass_count") != 8:
            errors.append("manifold layer receipt does not record 8/8 local passes")
        if layer_receipts.get("ratchet_admitted_layer_count") != 0:
            errors.append("manifold layer receipt overpromotes a layer")

    geometry_audit = _load_json("ratchet/manifold_evidence/entropic_geometry_audit_results.json", errors)
    if isinstance(geometry_audit, dict):
        if geometry_audit.get("scientific_manifold_layers_admitted") != 0:
            errors.append("entropic geometry audit overpromotes a layer")
        bridge = geometry_audit.get("L6_to_L7_bridge", {})
        if not bridge.get("phase_bridge_obstruction_fires"):
            errors.append("L6-to-L7 phase obstruction is absent")

    fixture_run = _load_json("ratchet/manifold_evidence/manifold_fixture_ratchet_results.json", errors)
    if isinstance(fixture_run, dict):
        population = fixture_run.get("candidate_population", {})
        order_search = fixture_run.get("gate_order_search", {})
        gradient = fixture_run.get("entropy_geometry_coface", {}).get("orientation_tooth", {})
        checks = (
            (population.get("parameter_proposals_executed") == 16384, "manifold fixture proposal count"),
            (population.get("behavioural_partition_classes") == 224, "manifold fixture behavior count"),
            (order_search.get("ordered_set_partitions_executed") == 75, "manifold fixture schedule count"),
            (gradient.get("delta") == 9, "manifold fixture orientation gradient"),
            (fixture_run.get("scientific_manifold_layers_admitted") == 0, "manifold fixture claim ceiling"),
        )
        for passed, label in checks:
            if not passed:
                errors.append(f"invalid {label}")

    layer_state = _load_json("ratchet/manifold_evidence/manifold_layer_state.json", errors)
    if isinstance(layer_state, dict):
        if len(layer_state.get("layers", [])) != 16:
            errors.append("machine-readable manifold state does not contain 16 L0-L15+ rows")
        if layer_state.get("scientific_manifold_layers_admitted") != 0:
            errors.append("machine-readable manifold state overpromotes a layer")

    sim_ledger = _load_json("reports/SIM_REGISTRATION_LEDGER.json", errors)
    if isinstance(sim_ledger, dict):
        counts = sim_ledger.get("counts", {})
        actual = (
            counts.get("all_top_level_python_scripts"),
            counts.get("registered_in_run_all"),
            counts.get("unregistered"),
        )
        if actual != (196, 150, 46):
            errors.append(f"complete simulation ledger partition is not 196/150/46: {actual}")
        if len(sim_ledger.get("scripts", [])) != 196:
            errors.append("complete simulation ledger does not enumerate all 196 scripts")

    exceptional = _load_json("reports/EXCEPTIONAL_NONASSOCIATIVE_MATH_STATE.json", errors)
    if isinstance(exceptional, dict):
        if exceptional.get("promotion_allowed") is not False or exceptional.get("formal_admission_allowed") is not False:
            errors.append("exceptional/nonassociative report overpromotes the branch")
        if exceptional.get("open_forcing_link", {}).get("status") != "OPEN":
            errors.append("exceptional report hides the open 27/64/4 forcing link")
        if exceptional.get("observations", {}).get("engine_malcev_not_lie_hits") != 0:
            errors.append("exceptional report changed the engine-native Malcev negative")
        if exceptional.get("observations", {}).get("generalized_jordan_dissipator_relative_entropy_pawl") is not False:
            errors.append("exceptional report hides the generalized Jordan dissipator pawl failure")

    basins = _load_json("reports/ATTRACTOR_BASIN_STATE.json", errors)
    if isinstance(basins, dict):
        chain = basins.get("fep_known_unknown_audit_chain", {})
        if not str(chain.get("v1_allocation_split", "")).startswith("REFUTED_AS_EVIDENCE"):
            errors.append("basin report does not preserve the v1 FEP allocation retraction")
        if chain.get("v2_engine_allocation") != "NO_SPLIT":
            errors.append("basin report overstates the repaired v2 allocation")
        if basins.get("promotion_allowed") is not False:
            errors.append("basin report overpromotes finite basin observations")

    julia_receipt = _load_json("julia_canon/artifacts/python_cross_validation_receipt.json", errors)
    if isinstance(julia_receipt, dict):
        if not julia_receipt.get("all_pass"):
            errors.append("Julia-owned convention mirror cross-validation is not green")
        if julia_receipt.get("ratchet_admission") is not False:
            errors.append("Julia algebra export receipt self-promotes")
        _julia_status = julia_receipt.get("status", "")
        # honest states: runtime absent AND SAID SO, or replay actually executed and cross-validated
        # (2026-07-11: first environment with a live Julia runtime; executed replay is strictly stronger)
        if ("LOCAL_JULIA_REPLAY_BLOCKED_RUNTIME_ABSENT" not in _julia_status
                and "JULIA_EXPORT_EXECUTED" not in _julia_status
                and "JULIA_EXPORT_PREVIOUSLY_EXECUTED" not in _julia_status):
            errors.append("Julia replay status is neither honest-runtime-absent nor executed-and-cross-validated")

    direct_reruns = _load_json("reports/DIRECT_RERUN_RECEIPTS.json", errors)
    if isinstance(direct_reruns, dict):
        if direct_reruns.get("fresh_pass_count") != 11 or direct_reruns.get("blocked_count") != 1:
            errors.append("direct dark-math rerun receipt does not preserve 11 fresh passes / 1 Torch blocker")
        if direct_reruns.get("ratchet_admission_count") != 0:
            errors.append("direct reruns self-promote into Ratchet admission")

    path_audit = _load_json("reports/STANDALONE_PATH_AUDIT.json", errors)
    if isinstance(path_audit, dict):
        if not path_audit.get("all_portable_path_gates_pass") or path_audit.get("portable_script_count") != 10:
            errors.append("standalone path audit does not preserve all ten recent path repairs")

    validation = _load_json("reports/V0_7_WORKING_TREE_VALIDATION.json", errors)
    if isinstance(validation, dict):
        if validation.get("status") != "PASS_WITH_DECLARED_RUNTIME_BLOCKERS_AND_LEGACY_RED_LANE":
            errors.append("v0.7 validation receipt hides a blocker or legacy red lane")
        if validation.get("ratchet_admission_count_from_v0_7_preservation_work") != 0:
            errors.append("v0.7 preservation work self-promotes into Ratchet admission")

    preservation = _load_json("preservation/preservation_manifest.json", errors)
    if isinstance(preservation, dict):
        if not preservation.get("lineage_comparison", {}).get("all_dropped_paths_restored_in_131"):
            errors.append("preservation manifest does not restore all four dropped artifacts")
        if len(preservation.get("restored_artifacts", [])) != 4:
            errors.append("preservation manifest does not enumerate exactly four restored artifacts")

    for relative in (
        "ratchet/manifold_evidence/entropic_geometry_audit.py",
        "ratchet/manifold_evidence/manifold_fixture_ratchet.py",
        "ratchet/manifold_evidence/build_layer_state.py",
        "julia_canon/validate_exceptional_canon.py",
        "preservation/standalone_path_audit.py",
        "preservation/verify_preservation.py",
    ):
        completed = subprocess.run(
            [sys.executable, str(ROOT / relative)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if completed.returncode != 0:
            errors.append(f"fresh manifold evidence run failed for {relative}: {completed.stderr or completed.stdout}")

    saved = _load_json("ratchet/runs/root_order_open_run_v0_5.json", errors)
    if isinstance(saved, dict):
        for error in validate_run(saved):
            errors.append(f"saved order-open run: {error}")
        try:
            packet = json.loads(DEFAULT_PACKET.read_text(encoding="utf-8"))
            fresh = run_packet(packet)
            checks = (
                ("population digest", saved["candidate_population"]["population_digest"], fresh["candidate_population"]["population_digest"]),
                ("behaviour count", saved["candidate_population"]["behavioural_partition_classes"], fresh["candidate_population"]["behavioural_partition_classes"]),
                ("final frontier", saved["frontier_cache"]["full_packet_frontier_partition_digests"], fresh["frontier_cache"]["full_packet_frontier_partition_digests"]),
                ("schedule count", saved["gate_order_search"]["schedule_hypotheses_executed"], fresh["gate_order_search"]["schedule_hypotheses_executed"]),
                ("trajectory count", saved["gate_order_search"]["unique_trajectories"], fresh["gate_order_search"]["unique_trajectories"]),
            )
            for label, saved_value, fresh_value in checks:
                if saved_value != fresh_value:
                    errors.append(f"fresh run {label} differs from saved receipt")
        except (KeyError, OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"fresh v0.5 reproduction failed: {exc}")

    killed_note = ROOT / "ratchet/runs/L5_REAUDIT_AUDIT_KILLED_NOTE.md"
    killed_instrument = ROOT / "ratchet/archive/manifold_l5_reaudit_v0_4_killed.py"
    if not killed_note.exists() or not killed_instrument.exists():
        errors.append("killed v0.4 L5 evidence or frozen instrument is not preserved")

    allowed_toplevel_md = {
        "00_START_HERE.md",
        "RATCHET_SPEC.md",
        "CLAUDE.md",
        "LAPTOP_README.md",
        "MODEL_LAYER_LEDGER.md",
        "CHANGELOG_HARDENING.md",
        "STATE_OF_THE_MODEL.md",
    }
    for entry in sorted(ROOT.glob("*.md")):
        if entry.name not in allowed_toplevel_md:
            errors.append(f"top-level sprawl: {entry.name}")

    for failure in run_self_test():
        errors.append(f"Ratchet v0.5 self-test: {failure}")

    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1

    print("PASS bundle_ratchet_lint")
    print("order/decomposition search, mass-candidate alias accounting, coface gradient, and killed-evidence fence verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
