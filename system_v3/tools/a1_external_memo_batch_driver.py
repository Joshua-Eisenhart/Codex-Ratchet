#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
import re

from a1_selector_warning_snapshot import (
    build_selector_warning_snapshot,
    extract_selector_provenance_fields,
    extract_selector_warning_fields,
)


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
CORE_DOCS = REPO / "core_docs"
CAMPAIGN = SYSTEM_V3 / "tools" / "a1_entropy_engine_campaign_runner.py"
MEMO_GATE = SYSTEM_V3 / "tools" / "a1_memo_quality_gate.py"
OP_AUDIT = SYSTEM_V3 / "tools" / "run_a1_operational_integrity_audit.py"
SEM_AUDIT = SYSTEM_V3 / "tools" / "run_a1_semantic_and_math_substance_gate.py"
PREPACK_TOOL = SYSTEM_V3 / "tools" / "run_a1_consolidation_prepack_job.py"
TRANSIENT_A1_EXCHANGE_ROOT = REPO / "work" / "a1_transient_exchange"

TERM_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{2,120}$")
DEF_FIELD_PROBE_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+PROBE_TERM\s+(.+)$")
DEF_FIELD_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+(.+)$")
DEF_FIELD_GOAL_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+GOAL_TERM\s+(.+)$")
MATH_REF_TERM_RE = re.compile(r"Z_MATH_([A-Z0-9_]+)")
TARGET_ID_TERM_SUFFIX_RE = re.compile(r"(?:EXTRA\d+_)?([A-Z][A-Z0-9_]+)$")
TOKEN_CANDIDATE_RE = re.compile(r"\b[a-z][a-z0-9_]{3,120}\b")


ROLE_NEG_CLASSES: dict[str, list[str]] = {
    "STEELMAN_CORE": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "STEELMAN_ALT_FORMALISM": ["COMMUTATIVE_ASSUMPTION", "INFINITE_SET"],
    "DEVIL_CLASSICAL_TIME": ["CLASSICAL_TIME"],
    "DEVIL_COMMUTATIVE": ["COMMUTATIVE_ASSUMPTION"],
    "DEVIL_CONTINUUM": ["CONTINUOUS_BATH", "INFINITE_SET", "INFINITE_RESOLUTION", "EUCLIDEAN_METRIC"],
    "DEVIL_EQUALS_SMUGGLE": ["COMMUTATIVE_ASSUMPTION", "INFINITE_SET", "PRIMITIVE_EQUALS"],
    "BOUNDARY_REPAIR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "RESCUER_MINIMAL_EDIT": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "RESCUER_OPERATOR_REFACTOR": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "ENTROPY_LENS_VN": ["CLASSICAL_TIME", "CONTINUOUS_BATH"],
    "ENTROPY_LENS_MUTUAL": ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"],
    "ENGINE_LENS_SZILARD_CARNOT": ["CONTINUOUS_BATH", "CLASSICAL_TIME", "INFINITE_SET", "CLASSICAL_TEMPERATURE"],
}


ROLE_CLAIMS: dict[str, list[str]] = {
    "STEELMAN_CORE": [
        "Build strongest finite noncommutative substrate first: density_matrix + probe_operator + cptp_channel + partial_trace.",
        "Keep terms explicit and compositional; avoid narrative labels in math surfaces.",
    ],
    "STEELMAN_ALT_FORMALISM": [
        "Construct an admissible alternate formal path using superoperators and operator-sidedness without changing constraints.",
    ],
    "DEVIL_CLASSICAL_TIME": [
        "Generate mathematically plausible classical-time variants expected to fail under nonclassical constraints.",
        "Adversarial smuggling lane: make classical assumptions explicit so they can be killed.",
    ],
    "DEVIL_COMMUTATIVE": [
        "Generate commutative-assumption variants that look plausible but violate noncommutative structure.",
    ],
    "DEVIL_CONTINUUM": [
        "Generate infinite and continuous-bath assumptions explicitly and adversarially for kill pressure.",
    ],
    "DEVIL_EQUALS_SMUGGLE": [
        "Generate identity/equality smuggling variants that encode classical assumptions and should fail.",
    ],
    "BOUNDARY_REPAIR": [
        "Generate boundary perturbations around known failures with explicit rescue ancestry.",
    ],
    "RESCUER_MINIMAL_EDIT": [
        "Select recent graveyard targets and propose minimal-edit rescues while preserving finite noncommutative structure.",
    ],
    "RESCUER_OPERATOR_REFACTOR": [
        "Select recent graveyard targets and propose operator-level refactors preserving probe semantics.",
    ],
    "ENTROPY_LENS_VN": [
        "Drive entropy claims through density_matrix spectrum and operator witnesses without classical bath assumptions.",
    ],
    "ENTROPY_LENS_MUTUAL": [
        "Drive entropy/correlation claims through partial_trace cuts and trajectory correlation witnesses.",
    ],
    "ENGINE_LENS_SZILARD_CARNOT": [
        "Treat Carnot and Szilard as overlays only; ratchet QIT witnesses and explicit nonclassical boundaries.",
    ],
}


ROLE_RISKS: dict[str, list[str]] = {
    "STEELMAN_CORE": ["No classical time or commutative collapse."],
    "STEELMAN_ALT_FORMALISM": ["No implicit Euclidean geometry assumptions."],
    "DEVIL_CLASSICAL_TIME": ["Adversarial lane; expected to fail and be killed."],
    "DEVIL_COMMUTATIVE": ["Adversarial lane; expected to fail and be killed."],
    "DEVIL_CONTINUUM": ["Adversarial lane; expected to fail and be killed."],
    "DEVIL_EQUALS_SMUGGLE": ["Adversarial lane; expected to fail and be killed."],
    "BOUNDARY_REPAIR": ["Do not narrative-smooth competing alternatives."],
    "RESCUER_MINIMAL_EDIT": ["Rescue may fail; failure is informative."],
    "RESCUER_OPERATOR_REFACTOR": ["Rescue may fail; failure is informative."],
    "ENTROPY_LENS_VN": ["No primitive thermal bath/time assumptions."],
    "ENTROPY_LENS_MUTUAL": ["No classical probability collapse."],
    "ENGINE_LENS_SZILARD_CARNOT": ["No primitive temperature or global-time lanes in positive claims."],
}


BASE_TERMS = sorted(
    {
        "finite_dimensional_hilbert_space",
        "density_matrix",
        "probe_operator",
        "cptp_channel",
        "partial_trace",
        "unitary_operator",
        "noncommutative_composition_order",
        "commutator_operator",
        "measurement_operator",
        "observable_operator",
        "projector_operator",
        "pauli_operator",
        "bloch_sphere",
        "hopf_fibration",
        "hopf_torus",
        "berry_flux",
        "spinor_double_cover",
        "left_weyl_spinor",
        "right_weyl_spinor",
        "left_action_superoperator",
        "right_action_superoperator",
        "von_neumann_entropy",
        "trajectory_correlation",
        "correlation_polarity",
        "entropy_production_rate",
        "engine_cycle",
        "qit_master_conjunction",
        "nested_hopf_torus_left_weyl_spinor_right_weyl_spinor_engine_cycle_constraint_manifold_conjunction",
        "information_work_extraction_bound",
        "erasure_channel_entropy_cost_lower_bound",
    }
)

# Curated fuel surface: terms that map to real planner/sim lanes.
# This prevents noisy doc tokens from polluting graveyard-library coverage gates.
CURATED_FUEL_TERMS = set(BASE_TERMS) | {
    "positive_semidefinite",
    "trace_one",
    "kraus_representation",
    "kraus_operator",
    "kraus_channel",
    "liouvillian_superoperator",
    "hamiltonian_operator",
    "channel_realization",
    "variance_order",
    "left_right_action_entropy_production_rate_orthogonality",
    "variance_order_trajectory_correlation_orthogonality",
    "channel_realization_correlation_polarity_orthogonality",
}

TERM_KEYWORDS = (
    "density",
    "matrix",
    "probe",
    "operator",
    "channel",
    "entropy",
    "correlation",
    "trajectory",
    "partial_trace",
    "commutator",
    "noncommutative",
    "superoperator",
    "lindblad",
    "hamiltonian",
    "kraus",
    "weyl",
    "spinor",
    "hopf",
    "torus",
    "fibration",
    "bloch",
    "manifold",
    "orthogonality",
    "engine",
)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _transient_exchange_root(*, run_id: str) -> Path:
    return TRANSIENT_A1_EXCHANGE_ROOT / str(run_id).strip() / "external_memo_exchange"


def _brain_context_sources_for_track(track: str) -> list[Path]:
    a2_control = [
        SYSTEM_V3 / "a2_state" / "A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
        SYSTEM_V3 / "a2_state" / "A2_TERM_CONFLICT_MAP__v1.md",
        SYSTEM_V3 / "a2_state" / "A2_TO_A1_DISTILLATION_INPUTS__v1.md",
        SYSTEM_V3 / "a2_state" / "A2_BRAIN_SLICE__v1.md",
        SYSTEM_V3 / "a2_state" / "INTENT_SUMMARY.md",
        SYSTEM_V3 / "a2_state" / "MODEL_CONTEXT.md",
        SYSTEM_V3 / "a2_state" / "OPEN_UNRESOLVED__v1.md",
        SYSTEM_V3 / "a2_state" / "SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
    ]
    track_upper = str(track or "").strip().upper()
    if "ENTROPY" in track_upper:
        return [
            *a2_control,
            SYSTEM_V3 / "a1_state" / "A1_FIRST_ENTROPY_BROAD_RESCUE_PACK__v1.md",
            SYSTEM_V3 / "a1_state" / "A1_FIRST_ENTROPY_ENGINE_CAMPAIGN__v1.md",
            SYSTEM_V3 / "a1_state" / "A1_FIRST_ENTROPY_BRIDGE_CAMPAIGN__v1.md",
            SYSTEM_V3 / "a2_state" / "ENTROPY_ENGINE_CLASSICAL_RESIDUE_QUARRY__v1.md",
        ]
    return [
        *a2_control,
        CORE_DOCS / "a1_refined_Ratchet Fuel" / "PHYSICS_FUEL_DIGEST_v1.0.md",
        CORE_DOCS / "a1_refined_Ratchet Fuel" / "AXES_MASTER_SPEC_v0.2.md",
    ]


def _load_a1_brain_context(*, max_chars: int = 12000, track: str = "") -> dict:
    """
    Build a compact, deterministic A1 context payload for external memo providers.
    This keeps context explicit and persistent without inflating packet size.
    """
    sources = _brain_context_sources_for_track(track)
    blocks: list[str] = []
    used: list[str] = []
    remaining = max(1000, int(max_chars))
    for path in sources:
        if not path.exists() or not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        text = " ".join(raw.split())
        if not text:
            continue
        # Reserve room for delimiters and header.
        take = min(len(text), max(200, remaining // max(1, (len(sources) - len(used)))))
        chunk = text[:take]
        blocks.append(f"[SOURCE={path.name}] {chunk}")
        used.append(str(path))
        remaining -= len(chunk)
        if remaining <= 0:
            break
    excerpt = "\n".join(blocks).strip()
    return {
        "sources": used,
        "excerpt": excerpt,
        "excerpt_sha256": _sha256_text(excerpt) if excerpt else "",
    }


def _required_roles_for_preset(preset: str) -> list[str]:
    p = str(preset).strip()
    if p == "substrate5":
        return [
            "STEELMAN_CORE",
            "DEVIL_CLASSICAL_TIME",
            "DEVIL_COMMUTATIVE",
            "BOUNDARY_REPAIR",
            "RESCUER_MINIMAL_EDIT",
        ]
    if p == "graveyard13":
        return [
            "STEELMAN_CORE",
            "STEELMAN_ALT_FORMALISM",
            "DEVIL_CLASSICAL_TIME",
            "DEVIL_COMMUTATIVE",
            "DEVIL_CONTINUUM",
            "DEVIL_EQUALS_SMUGGLE",
            "BOUNDARY_REPAIR",
            "RESCUER_MINIMAL_EDIT",
            "RESCUER_OPERATOR_REFACTOR",
            "ENTROPY_LENS_VN",
            "ENTROPY_LENS_MUTUAL",
            "ENGINE_LENS_SZILARD_CARNOT",
        ]
    if p == "entropy_lenses7":
        return [
            "LENS_VN",
            "LENS_MUTUAL_INFO",
            "LENS_CONDITIONAL",
            "LENS_THERMO_ANALOGY",
            "DEVIL_CLASSICAL_SMUGGLER",
            "RESCUER",
        ]
    return ["STEELMAN", "DEVIL", "BOUNDARY"]


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {}
    if path.name == "state.json":
        heavy_path = path.with_name("state.heavy.json")
        if heavy_path.exists():
            heavy = json.loads(heavy_path.read_text(encoding="utf-8"))
            if isinstance(heavy, dict):
                data.update(heavy)
    return data


def _run_cmd(cmd: list[str], *, cwd: Path) -> str:
    return subprocess.check_output(cmd, cwd=str(cwd), text=True).strip()


def _run_cmd_proc(cmd: list[str], *, cwd: Path) -> tuple[int, str, str]:
    proc = subprocess.run(cmd, cwd=str(cwd), check=False, capture_output=True, text=True)
    return int(proc.returncode), (proc.stdout or "").strip(), (proc.stderr or "").strip()


def _run_audit_cmd(cmd: list[str], *, cwd: Path) -> dict:
    code, out, err = _run_cmd_proc(cmd, cwd=cwd)
    payload: dict = {
        "exit_code": int(code),
        "status": "FAIL",
        "stdout_tail": out[-400:],
        "stderr_tail": err[-400:],
    }
    if out:
        last_line = out.splitlines()[-1]
        try:
            parsed = json.loads(last_line)
            if isinstance(parsed, dict):
                payload.update(parsed)
        except json.JSONDecodeError:
            pass
    report_path_raw = str(payload.get("report_path", "")).strip()
    if report_path_raw:
        report_path = Path(report_path_raw)
        if report_path.exists():
            try:
                report_obj = json.loads(report_path.read_text(encoding="utf-8"))
                if isinstance(report_obj, dict):
                    payload["report"] = report_obj
                    if str(report_obj.get("status", "")).strip():
                        payload["status"] = str(report_obj.get("status", "")).strip()
            except json.JSONDecodeError:
                pass
    return payload


def _state_counts(run_dir: Path) -> dict:
    state = _read_json(run_dir / "state.json")
    term_registry = state.get("term_registry", {}) if isinstance(state.get("term_registry", {}), dict) else {}
    canonical_term_count = sum(
        1
        for row in term_registry.values()
        if isinstance(row, dict) and str(row.get("state", "")).strip() == "CANONICAL_ALLOWED"
    )
    return {
        "canonical_term_count": int(canonical_term_count),
        "graveyard_count": int(len(state.get("graveyard", {}) or {})),
        "kill_log_count": int(len(state.get("kill_log", []) or [])),
        "sim_registry_count": int(len(state.get("sim_registry", {}) or {})),
    }


def _kill_token_diversity(state: dict) -> int:
    tokens: set[str] = set()
    for row in state.get("kill_log", []) if isinstance(state, dict) else []:
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        tok = str(row.get("token", "")).strip()
        if tok:
            tokens.add(tok)
    return len(tokens)


def _parse_csv_terms(raw: str) -> list[str]:
    out: list[str] = []
    for part in str(raw or "").split(","):
        t = part.strip()
        if t and t not in out:
            out.append(t)
    return out


def _dedup_keep_order(rows: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in rows:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _parse_pipe_claims(raw: str) -> list[str]:
    out: list[str] = []
    for part in str(raw or "").split("||"):
        text = str(part).strip()
        if text and text not in out:
            out.append(text)
    return out


def _parse_csv_term_set(raw: str) -> set[str]:
    return {t for t in _parse_csv_terms(raw)}


def _csv_from_terms(terms: set[str]) -> str:
    return ",".join(sorted({str(t).strip() for t in terms if str(t).strip()}))


def _selector_provenance_fields(row: dict) -> dict:
    out = dict(extract_selector_provenance_fields(row))
    selector_warning_fields = extract_selector_warning_fields(row)
    selector_process_warnings = list(selector_warning_fields.get("selector_process_warnings", []) or [])
    if selector_process_warnings:
        out["selector_process_warnings"] = selector_process_warnings
    selector_warning_codes = list(selector_warning_fields.get("selector_warning_codes", []) or [])
    if selector_warning_codes:
        out["selector_warning_codes"] = selector_warning_codes
    selector_warning_categories = list(selector_warning_fields.get("selector_warning_categories", []) or [])
    if selector_warning_categories:
        out["selector_warning_categories"] = selector_warning_categories
    return out


def _selector_warning_snapshot(
    warnings: list[str],
    *,
    warning_codes: list[str] | None = None,
    warning_categories: list[str] | None = None,
    summary_limit: int = 160,
    example_limit: int = 3,
) -> dict:
    snapshot = build_selector_warning_snapshot(
        warnings,
        warning_codes=warning_codes,
        warning_categories=warning_categories,
        summary_limit=summary_limit,
        example_limit=example_limit,
    )
    if not snapshot:
        return {
            "selector_warning_count": 0,
            "selector_warning_codes": [],
            "selector_warning_categories": [],
            "selector_support_warning_present": False,
        }
    return snapshot


def _compact_selector_provenance_fields(row: dict, *, allow_prepack_local_default: bool = False) -> dict:
    selector_fields = _selector_provenance_fields(row)
    selector_cold_core_source = str(selector_fields.get("selector_cold_core_source", "")).strip()
    selector_cold_core_path_class = str(selector_fields.get("selector_cold_core_path_class", "")).strip()
    selector_cold_core_sequence = int(selector_fields.get("selector_cold_core_sequence", 0) or 0)
    selector_process_warnings = list(selector_fields.get("selector_process_warnings", []) or [])
    selector_warning_codes = list(selector_fields.get("selector_warning_codes", []) or [])
    selector_warning_categories = list(selector_fields.get("selector_warning_categories", []) or [])
    ordinary_pairs = {("run_local_sandbox", "run_local_sandbox")}
    if bool(allow_prepack_local_default):
        ordinary_pairs.add(("explicit_arg", "transient_store"))
    has_any_selector_provenance = bool(selector_cold_core_source or selector_cold_core_path_class)
    is_ordinary_selector_provenance = (selector_cold_core_source, selector_cold_core_path_class) in ordinary_pairs
    row_sequence = int(row.get("sequence", 0) or 0)
    has_sequence_mismatch = (
        selector_cold_core_sequence > 0
        and row_sequence > 0
        and selector_cold_core_sequence != row_sequence
    )
    has_nondefault_selector_provenance = bool(selector_process_warnings) or has_sequence_mismatch or (
        has_any_selector_provenance and not is_ordinary_selector_provenance
    )
    out: dict = {}
    if has_nondefault_selector_provenance:
        if selector_cold_core_source:
            out["selector_cold_core_source"] = selector_cold_core_source
        if selector_cold_core_path_class:
            out["selector_cold_core_path_class"] = selector_cold_core_path_class
        if selector_cold_core_sequence > 0:
            out["selector_cold_core_sequence"] = int(selector_cold_core_sequence)
        if selector_process_warnings:
            out.update(
                _selector_warning_snapshot(
                    selector_process_warnings,
                    warning_codes=selector_warning_codes,
                    warning_categories=selector_warning_categories,
                )
            )
    return out


def _compact_failure_summary(*texts: str, limit: int = 160) -> str:
    for text in texts:
        lines = [str(line).strip() for line in str(text or "").splitlines() if str(line).strip()]
        if not lines:
            continue
        summary = lines[-1]
        if len(summary) > int(limit):
            summary = summary[-int(limit):]
        return summary
    return ""


def _compact_selector_warning_summary(warnings: list[str], limit: int = 160) -> str:
    snapshot = _selector_warning_snapshot(warnings, summary_limit=limit)
    return str(snapshot.get("selector_warning_summary", "")).strip()


def _row_failure_summary(row: dict, *fallback_texts: str, limit: int = 160) -> str:
    summary = str(row.get("failure_summary", "")).strip()
    if summary:
        if len(summary) > int(limit):
            summary = summary[-int(limit):]
        return summary
    return _compact_failure_summary(*fallback_texts, limit=limit)


def _compact_ingest_failure_summary(row: dict) -> str:
    rejected = row.get("rejected", [])
    for item in rejected if isinstance(rejected, list) else []:
        if not isinstance(item, dict):
            continue
        reason = str(item.get("reason", "")).strip()
        if reason:
            return reason
        gate = item.get("gate", {})
        if isinstance(gate, dict):
            failures = gate.get("failures", [])
            for raw in failures if isinstance(failures, list) else []:
                msg = str(raw).strip()
                if msg:
                    return msg
    return ""


def _first_nested_failure_info(row: dict) -> tuple[int, str, str]:
    failures: list[tuple[int, int, str, str]] = []
    provider_rows = row.get("provider_exec_rows", [])
    for item in provider_rows if isinstance(provider_rows, list) else []:
        if not isinstance(item, dict):
            continue
        code = int(item.get("code", 0) or 0)
        if code != 0:
            failures.append(
                (
                    int(item.get("sequence", 0) or 0),
                    0,
                    "provider_exec",
                    _compact_failure_summary(item.get("stderr", ""), item.get("stdout", "")),
                )
            )
    ingest_rows = row.get("exchange_ingest_rows", [])
    for item in ingest_rows if isinstance(ingest_rows, list) else []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip()
        if status and status != "INGESTED":
            failures.append(
                (
                    int(item.get("sequence", 0) or 0),
                    1,
                    "exchange_ingest",
                    _compact_ingest_failure_summary(item),
                )
            )
    prepack_rows = row.get("exchange_prepack_rows", [])
    for item in prepack_rows if isinstance(prepack_rows, list) else []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status", "")).strip()
        if status and status != "PASS":
            failures.append(
                (
                    int(item.get("sequence", 0) or 0),
                    2,
                    "exchange_prepack",
                    _row_failure_summary(item, item.get("stderr", ""), item.get("stdout", "")),
                )
            )
    if not failures:
        return 0, "", ""
    failures.sort()
    return int(failures[0][0]), str(failures[0][2]), str(failures[0][3]).strip()


def _annotate_first_failure_info(row: dict) -> dict:
    out = dict(row)
    first_failure_sequence, first_failure_surface, first_failure_summary = _first_nested_failure_info(out)
    if int(first_failure_sequence) > 0:
        out["first_failure_sequence"] = int(first_failure_sequence)
    else:
        out.pop("first_failure_sequence", None)
    if first_failure_surface:
        out["first_failure_surface"] = first_failure_surface
    else:
        out.pop("first_failure_surface", None)
    if first_failure_summary:
        out["first_failure_summary"] = first_failure_summary
    else:
        out.pop("first_failure_summary", None)
    return out


def _compact_timeline_row(row: dict) -> dict:
    out = _annotate_first_failure_info(row)
    out.pop("selector_cold_core_path", None)
    out.pop("selector_cold_core_source", None)
    out.pop("selector_cold_core_path_class", None)
    out.pop("selector_cold_core_sha256", None)
    out.pop("selector_process_warnings", None)
    out.update(_compact_selector_provenance_fields(row, allow_prepack_local_default=True))
    if isinstance(out.get("memo_emit"), dict):
        m = dict(out["memo_emit"])
        out["memo_emit"] = {
            "written_count": int(m.get("written_count", 0)),
            "rejected_count": int(m.get("rejected_count", 0)),
        }
    if isinstance(out.get("exchange_request_paths"), list):
        out["exchange_request_count"] = len(out["exchange_request_paths"])
        out.pop("exchange_request_paths", None)
    if isinstance(out.get("provider_exec_rows"), list):
        compact_exec = []
        for r in out["provider_exec_rows"]:
            if not isinstance(r, dict):
                continue
            compact_row = {
                "sequence": int(r.get("sequence", 0) or 0),
                "code": int(r.get("code", 0) or 0),
            }
            if int(compact_row["code"]) != 0:
                failure_summary = _compact_failure_summary(r.get("stderr", ""), r.get("stdout", ""))
                if failure_summary:
                    compact_row["failure_summary"] = failure_summary
            compact_exec.append(compact_row)
        out["provider_exec_rows"] = compact_exec
    if isinstance(out.get("exchange_ingest_rows"), list):
        compact_ingest = []
        for r in out["exchange_ingest_rows"]:
            if not isinstance(r, dict):
                continue
            compact_row = {
                "sequence": int(r.get("sequence", 0) or 0),
                "status": str(r.get("status", "")),
                "written_count": int(r.get("written_count", 0)),
                "rejected_count": int(r.get("rejected_count", 0)),
            }
            if str(compact_row["status"]) != "INGESTED":
                failure_summary = _compact_ingest_failure_summary(r)
                if failure_summary:
                    compact_row["failure_summary"] = failure_summary
            compact_ingest.append(compact_row)
        out["exchange_ingest_rows"] = compact_ingest
    if isinstance(out.get("exchange_prepack_rows"), list):
        compact_prepack = []
        for r in out["exchange_prepack_rows"]:
            if not isinstance(r, dict):
                continue
            prepack_status = str(r.get("status", ""))
            compact_row = {
                "sequence": int(r.get("sequence", 0) or 0),
                "status": prepack_status,
                "input_count": int(r.get("input_count", 0) or 0),
                "memo_count": int(r.get("memo_count", 0) or 0),
                "effective_memo_count": int(r.get("effective_memo_count", 0) or 0),
                "external_response_count": int(r.get("external_response_count", 0) or 0),
            }
            if prepack_status == "PREPACK_FAILED":
                compact_row["code"] = int(r.get("code", 0) or 0)
                failure_summary = _row_failure_summary(r, r.get("stderr", ""), r.get("stdout", ""))
                if failure_summary:
                    compact_row["failure_summary"] = failure_summary
            compact_row.update(_compact_selector_provenance_fields(r, allow_prepack_local_default=True))
            compact_prepack.append(compact_row)
        out["exchange_prepack_rows"] = compact_prepack
    return out


def _extract_term_from_item_text(item_text: str) -> str:
    goal_term = ""
    term_field = ""
    probe_term = ""
    for raw_line in str(item_text or "").splitlines():
        line = raw_line.strip()
        m = DEF_FIELD_GOAL_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if TERM_TOKEN_RE.fullmatch(value):
                goal_term = value
                continue
        m = DEF_FIELD_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if TERM_TOKEN_RE.fullmatch(value):
                term_field = value
                continue
        m = DEF_FIELD_PROBE_TERM_RE.match(line)
        if m:
            value = str(m.group(1)).strip().strip('"')
            if TERM_TOKEN_RE.fullmatch(value):
                probe_term = value
                continue
        m = MATH_REF_TERM_RE.search(line)
        if m:
            value = str(m.group(1)).strip().lower()
            if TERM_TOKEN_RE.fullmatch(value):
                return value
    return goal_term or term_field or probe_term


def _collect_rescue_targets(state: dict, *, limit: int = 24) -> list[str]:
    prioritized: list[str] = []
    overflow: list[str] = []
    seen_ids: set[str] = set()
    seen_keys: set[str] = set()
    for row in reversed(state.get("kill_log", []) if isinstance(state, dict) else []):
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        sid = str(row.get("id", "")).strip()
        if not sid or sid in seen_ids:
            continue
        seen_ids.add(sid)
        token = str(row.get("token", "")).strip().upper()
        term = _rescue_target_term(state, sid)
        key = f"{token}::{term or sid}"
        if key not in seen_keys:
            seen_keys.add(key)
            prioritized.append(sid)
        else:
            overflow.append(sid)
        if len(prioritized) >= int(limit):
            break
    out = prioritized + overflow
    out = out[: int(limit)]
    out.reverse()
    return out


def _rescue_target_term(state: dict, target: str) -> str:
    candidate = str(target).strip()
    if not candidate:
        return ""
    if TERM_TOKEN_RE.fullmatch(candidate):
        return candidate
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    survivor = state.get("survivor_ledger", {}) if isinstance(state.get("survivor_ledger", {}), dict) else {}
    parked = state.get("park_set", {}) if isinstance(state.get("park_set", {}), dict) else {}
    row = graveyard.get(candidate) or survivor.get(candidate) or parked.get(candidate)
    if isinstance(row, dict):
        term = _extract_term_from_item_text(str(row.get("item_text", "")))
        if term:
            return term
    m = TARGET_ID_TERM_SUFFIX_RE.search(candidate)
    if m:
        return str(m.group(1)).strip().lower()
    return ""


def _rescue_target_signature(state: dict, target: str) -> str:
    candidate = str(target).strip()
    if not candidate:
        return ""
    token = ""
    for row in reversed(state.get("kill_log", []) if isinstance(state, dict) else []):
        if not isinstance(row, dict):
            continue
        if str(row.get("id", "")).strip() != candidate:
            continue
        token = str(row.get("token", "")).strip().upper()
        break
    term = _rescue_target_term(state, candidate)
    if token or term:
        return f"{token}::{term or candidate}"
    return candidate


def _filter_rescue_targets_for_allowed_terms(
    state: dict,
    rescue_targets: list[str],
    *,
    allowed_terms: list[str] | None = None,
) -> list[str]:
    allowed = {str(x).strip() for x in (allowed_terms or []) if TERM_TOKEN_RE.fullmatch(str(x).strip())}
    if not allowed:
        return [str(x).strip() for x in rescue_targets if str(x).strip()]

    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    survivor = state.get("survivor_ledger", {}) if isinstance(state.get("survivor_ledger", {}), dict) else {}
    parked = state.get("park_set", {}) if isinstance(state.get("park_set", {}), dict) else {}
    filtered: list[str] = []
    for raw in rescue_targets:
        target = str(raw).strip()
        if not target:
            continue
        target_term = _rescue_target_term(state, target)
        if target_term and target_term in allowed and target not in filtered:
            filtered.append(target)
    return filtered


def _clamp_rescue_targets_by_allowed_terms(
    rescue_targets: list[str],
    *,
    allowed_terms: list[str] | None = None,
) -> list[str]:
    allowed = {str(x).strip() for x in (allowed_terms or []) if TERM_TOKEN_RE.fullmatch(str(x).strip())}
    if not allowed:
        return [str(x).strip() for x in rescue_targets if str(x).strip()]
    filtered: list[str] = []
    for raw in rescue_targets:
        target = str(raw).strip()
        if not target:
            continue
        m = TARGET_ID_TERM_SUFFIX_RE.search(target)
        if not m:
            continue
        term = str(m.group(1)).strip().lower()
        if term in allowed and target not in filtered:
            filtered.append(target)
    return filtered


def _rescue_allowed_term_frontier(
    state: dict,
    *,
    allowed_terms: list[str] | None = None,
    recent_signatures: list[str] | None = None,
) -> list[str]:
    allowed = [str(x).strip() for x in (allowed_terms or []) if TERM_TOKEN_RE.fullmatch(str(x).strip())]
    if not allowed:
        return []
    seen: set[str] = set()
    recent = set(str(x).strip() for x in (recent_signatures or []) if str(x).strip())
    out: list[str] = []
    for term in allowed:
        if term in seen:
            continue
        seen.add(term)
        signature = _rescue_target_signature(state, term)
        if signature and signature in recent:
            continue
        out.append(term)
    return out


def _deterministic_rotating_term_subset(
    ordered_terms: list[str] | None,
    *,
    sequence: int,
    keep_head: int = 2,
    rotate_width: int = 2,
) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for raw in ordered_terms or []:
        term = str(raw).strip()
        if not TERM_TOKEN_RE.fullmatch(term):
            continue
        if term in seen:
            continue
        seen.add(term)
        terms.append(term)
    if not terms:
        return []
    if len(terms) <= int(keep_head):
        return terms
    head_count = max(0, min(int(keep_head), len(terms)))
    head = list(terms[:head_count])
    tail = list(terms[head_count:])
    if not tail:
        return head
    width = max(1, min(int(rotate_width), len(tail)))
    start = max(0, int(sequence) - 1) % len(tail)
    chosen: list[str] = []
    for offset in range(width):
        term = tail[(start + offset) % len(tail)]
        if term not in chosen:
            chosen.append(term)
    out: list[str] = []
    seen_out: set[str] = set()
    for term in head + chosen:
        if term in seen_out:
            continue
        seen_out.add(term)
        out.append(term)
    return out


def _deterministic_rotating_rescue_target_subset(
    state: dict,
    rescue_targets: list[str] | None,
    *,
    sequence: int,
    keep_head: int = 2,
    rotate_width: int = 2,
) -> list[str]:
    targets: list[str] = []
    seen_targets: set[str] = set()
    for raw in rescue_targets or []:
        target = str(raw).strip()
        if not target or target in seen_targets:
            continue
        seen_targets.add(target)
        targets.append(target)
    if not targets:
        return []
    if len(targets) <= int(keep_head):
        return targets
    head_count = max(0, min(int(keep_head), len(targets)))
    head = list(targets[:head_count])
    tail = list(targets[head_count:])
    if not tail:
        return head
    buckets: dict[str, list[str]] = {}
    ordered_keys: list[str] = []
    for target in tail:
        signature = _rescue_target_signature(state, target)
        token = ""
        term = ""
        if "::" in signature:
            token, term = signature.split("::", 1)
        bucket_key = f"{token}::{term or _rescue_target_term(state, target) or target}"
        if bucket_key not in buckets:
            buckets[bucket_key] = []
            ordered_keys.append(bucket_key)
        buckets[bucket_key].append(target)
    if not ordered_keys:
        ordered_keys = list(tail)
        buckets = {target: [target] for target in tail}
    width = max(1, min(int(rotate_width), len(ordered_keys)))
    start = max(0, int(sequence) - 1) % len(ordered_keys)
    chosen: list[str] = []
    bucket_offsets: dict[str, int] = {}
    for offset in range(width):
        bucket_key = ordered_keys[(start + offset) % len(ordered_keys)]
        bucket = buckets.get(bucket_key, [])
        if not bucket:
            continue
        idx = bucket_offsets.get(bucket_key, 0) % len(bucket)
        bucket_offsets[bucket_key] = idx + 1
        target = bucket[idx]
        if target not in chosen:
            chosen.append(target)
    out: list[str] = []
    seen_out: set[str] = set()
    for target in head + chosen:
        if target in seen_out:
            continue
        seen_out.add(target)
        out.append(target)
    return out


def _strategy_item_field_map(item: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in item.get("def_fields", []) if isinstance(item, dict) else []:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name", "")).strip().upper()
        value = str(row.get("value", "")).strip()
        if name:
            out[name] = value
    return out


def _strategy_item_signature(item: dict, *, allowed_terms: set[str] | None = None) -> tuple | None:
    if not isinstance(item, dict):
        return None
    allowed = {str(x).strip() for x in (allowed_terms or set()) if str(x).strip()}
    field_map = _strategy_item_field_map(item)
    probe_term = str(field_map.get("PROBE_TERM", "")).strip()
    goal_term = str(field_map.get("GOAL_TERM", "")).strip()
    term = str(field_map.get("TERM", "")).strip()
    related_terms = [x for x in [probe_term, goal_term, term] if TERM_TOKEN_RE.fullmatch(x)]
    if allowed and not any(t in allowed for t in related_terms):
        return None
    return (
        str(item.get("operator_id", "")).strip(),
        str(item.get("kind", "")).strip(),
        str(field_map.get("TARGET_CLASS", "")).strip(),
        str(field_map.get("FAMILY", "")).strip(),
        str(field_map.get("BRANCH_TRACK", "")).strip(),
        probe_term,
        goal_term,
        term,
    )


def _strategy_shape_signature(
    run_dir: Path,
    *,
    sequence: int,
    allowed_terms: list[str] | None = None,
) -> str:
    path = run_dir / "a1_sandbox" / "outgoing" / f"{int(sequence):06d}_A1_STRATEGY_v1__PACK_SELECTOR.json"
    if not path.exists():
        return ""
    obj = _read_json(path)
    if not isinstance(obj, dict):
        return ""
    allowed = {str(x).strip() for x in (allowed_terms or []) if TERM_TOKEN_RE.fullmatch(str(x).strip())}
    targets = []
    for item in obj.get("targets", []) or []:
        sig = _strategy_item_signature(item, allowed_terms=allowed)
        if sig is not None:
            targets.append(sig)
    alternatives = []
    for item in obj.get("alternatives", []) or []:
        sig = _strategy_item_signature(item, allowed_terms=allowed)
        if sig is not None:
            alternatives.append(sig)
    negative_binds: list[str] = []
    sims = obj.get("sims", {}) if isinstance(obj.get("sims", {}), dict) else {}
    for row in sims.get("negative", []) or []:
        if not isinstance(row, dict):
            continue
        bind = str(row.get("binds_to", "")).strip()
        if bind:
            negative_binds.append(bind)
    payload = {
        "targets": targets[:8],
        "alternatives": alternatives[:16],
        "negative_binds": sorted(negative_binds)[:16],
    }
    if not payload["targets"] and not payload["alternatives"] and not payload["negative_binds"]:
        return ""
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _rescue_plan_signature(
    *,
    terms: list[str] | None = None,
    rescue_targets: list[str] | None = None,
) -> str:
    ordered_terms: list[str] = []
    seen_terms: set[str] = set()
    for raw in terms or []:
        term = str(raw).strip()
        if not TERM_TOKEN_RE.fullmatch(term):
            continue
        if term in seen_terms:
            continue
        seen_terms.add(term)
        ordered_terms.append(term)
    ordered_targets: list[str] = []
    seen_targets: set[str] = set()
    for raw in rescue_targets or []:
        target = str(raw).strip()
        if not target:
            continue
        if target in seen_targets:
            continue
        seen_targets.add(target)
        ordered_targets.append(target)
    if not ordered_terms and not ordered_targets:
        return ""
    payload = {
        "terms": ordered_terms,
        "rescue_targets": ordered_targets,
    }
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def _recent_cold_core_bootstrap_term_counts(
    run_dir: Path,
    *,
    max_sequence: int,
    window: int = 12,
) -> dict[str, dict[str, int]]:
    cold_core_dir = run_dir / "a1_sandbox" / "cold_core"
    if not cold_core_dir.exists():
        return {}
    rows: list[tuple[int, Path]] = []
    for path in cold_core_dir.glob("*_A1_COLD_CORE_PROPOSALS_v1.json"):
        try:
            seq = int(str(path.name).split("_", 1)[0])
        except Exception:
            continue
        if seq <= int(max_sequence):
            rows.append((seq, path))
    if not rows:
        return {}
    rows.sort(key=lambda item: item[0])
    counts: dict[str, dict[str, int]] = {}
    for _, path in rows[-max(1, int(window)):]:
        obj = _read_json(path)
        if not isinstance(obj, dict):
            continue
        bootstrap = [str(x).strip() for x in (obj.get("need_atomic_bootstrap", []) or []) if str(x).strip()]
        if not bootstrap:
            continue
        signature = "|".join(sorted(bootstrap))
        if not signature:
            continue
        for raw in (obj.get("admissible_term_candidates", []) or []):
            term = str(raw).strip()
            if not TERM_TOKEN_RE.fullmatch(term):
                continue
            bucket = counts.setdefault(term, {})
            bucket[signature] = int(bucket.get(signature, 0)) + 1
    return counts


def _bootstrap_stalled_terms(
    run_dir: Path,
    *,
    max_sequence: int,
    allowed_terms: list[str] | None = None,
    min_repeats: int = 3,
    window: int = 12,
) -> tuple[set[str], dict[str, int]]:
    allowed = {str(x).strip() for x in (allowed_terms or []) if TERM_TOKEN_RE.fullmatch(str(x).strip())}
    counts = _recent_cold_core_bootstrap_term_counts(
        run_dir,
        max_sequence=max_sequence,
        window=window,
    )
    stalled: set[str] = set()
    histogram: dict[str, int] = {}
    for term, signatures in counts.items():
        if allowed and term not in allowed:
            continue
        peak = max((int(v) for v in signatures.values()), default=0)
        if peak >= int(min_repeats):
            stalled.add(term)
            histogram[term] = peak
    return stalled, histogram


def _recent_bootstrap_companion_terms(
    run_dir: Path,
    *,
    max_sequence: int,
    allowed_terms: list[str] | None = None,
    min_repeats: int = 2,
    window: int = 12,
) -> tuple[list[str], dict[str, int]]:
    allowed = {str(x).strip() for x in (allowed_terms or []) if TERM_TOKEN_RE.fullmatch(str(x).strip())}
    if not allowed:
        return [], {}
    cold_core_dir = run_dir / "a1_sandbox" / "cold_core"
    if not cold_core_dir.exists():
        return [], {}
    rows: list[tuple[int, Path]] = []
    for path in cold_core_dir.glob("*_A1_COLD_CORE_PROPOSALS_v1.json"):
        try:
            seq = int(str(path.name).split("_", 1)[0])
        except Exception:
            continue
        if seq <= int(max_sequence):
            rows.append((seq, path))
    if not rows:
        return [], {}
    rows.sort(key=lambda item: item[0])
    counts: dict[str, int] = {}
    for _, path in rows[-max(1, int(window)):]:
        obj = _read_json(path)
        if not isinstance(obj, dict):
            continue
        admissible_terms = {
            str(x).strip()
            for x in (obj.get("admissible_term_candidates", []) or [])
            if TERM_TOKEN_RE.fullmatch(str(x).strip())
        }
        if not admissible_terms.intersection(allowed):
            continue
        for raw in (obj.get("need_atomic_bootstrap", []) or []):
            comp = str(raw).strip()
            if not TERM_TOKEN_RE.fullmatch(comp) or "_" in comp:
                continue
            counts[comp] = int(counts.get(comp, 0)) + 1
    selected = [
        comp
        for comp, count in sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))
        if int(count) >= int(min_repeats)
    ]
    return selected, counts


DECOMPOSITION_SUPPORT_MAP: dict[str, tuple[str, ...]] = {
    "correlation_diversity_functional": ("functional",),
    "correlation": ("unitary_operator", "qit_master_conjunction"),
    "correlation_polarity": ("unitary_operator", "qit_master_conjunction"),
}

DECOMPOSITION_RESCUE_FRAGMENT_MAP: dict[str, tuple[str, ...]] = {
    "correlation_diversity_functional": ("functional",),
}

WITNESS_ACTIVATION_SUPPORT_MAP: dict[str, tuple[str, ...]] = {
    "correlation_diversity_functional": ("unitary_operator", "qit_master_conjunction"),
}


def _fallback_decomposition_support_terms(
    *,
    allowed_terms: list[str] | None = None,
    stalled_terms: set[str] | None = None,
) -> list[str]:
    active_terms: list[str] = []
    seen_terms: set[str] = set()
    for raw in list(allowed_terms or []) + list(stalled_terms or set()):
        term = str(raw).strip()
        if not TERM_TOKEN_RE.fullmatch(term):
            continue
        if term in seen_terms:
            continue
        seen_terms.add(term)
        active_terms.append(term)
    if not active_terms:
        return []
    support: list[str] = []
    seen_support: set[str] = set()
    blocked = set(active_terms)
    for term in active_terms:
        for raw_support in DECOMPOSITION_SUPPORT_MAP.get(term, ()):
            item = str(raw_support).strip()
            if not TERM_TOKEN_RE.fullmatch(item):
                continue
            if item in blocked or item in seen_support:
                continue
            seen_support.add(item)
            support.append(item)
    return support


def _fallback_decomposition_rescue_fragments(
    *,
    stalled_terms: set[str] | None = None,
) -> list[str]:
    active_terms: list[str] = []
    seen_terms: set[str] = set()
    for raw in stalled_terms or set():
        term = str(raw).strip()
        if not TERM_TOKEN_RE.fullmatch(term):
            continue
        if term in seen_terms:
            continue
        seen_terms.add(term)
        active_terms.append(term)
    if not active_terms:
        return []
    rescue_fragments: list[str] = []
    seen_fragments: set[str] = set()
    blocked = set(active_terms)
    for term in active_terms:
        for raw_fragment in DECOMPOSITION_RESCUE_FRAGMENT_MAP.get(term, ()):
            item = str(raw_fragment).strip()
            if not TERM_TOKEN_RE.fullmatch(item):
                continue
            if item in blocked or item in seen_fragments:
                continue
            seen_fragments.add(item)
            rescue_fragments.append(item)
    return rescue_fragments


def _fallback_witness_activation_support_terms(
    *,
    stalled_terms: set[str] | None = None,
) -> list[str]:
    active_terms: list[str] = []
    seen_terms: set[str] = set()
    for raw in stalled_terms or set():
        term = str(raw).strip()
        if not TERM_TOKEN_RE.fullmatch(term):
            continue
        if term in seen_terms:
            continue
        seen_terms.add(term)
        active_terms.append(term)
    if not active_terms:
        return []
    support: list[str] = []
    seen_support: set[str] = set()
    blocked = set(active_terms)
    for term in active_terms:
        for raw_support in WITNESS_ACTIVATION_SUPPORT_MAP.get(term, ()):
            item = str(raw_support).strip()
            if not TERM_TOKEN_RE.fullmatch(item):
                continue
            if item in blocked or item in seen_support:
                continue
            seen_support.add(item)
            support.append(item)
    return support


def _collect_focus_terms(
    state: dict,
    rescue_targets: list[str],
    *,
    concept_target_terms: list[str] | None = None,
    priority_terms: list[str] | None = None,
    focus_term_mode: str = "broad",
) -> list[str]:
    mode = str(focus_term_mode).strip().lower()
    concept_terms = [str(t).strip() for t in (concept_target_terms or []) if TERM_TOKEN_RE.fullmatch(str(t).strip())]
    priority = [str(t).strip() for t in (priority_terms or []) if TERM_TOKEN_RE.fullmatch(str(t).strip())]
    if mode == "concept_only":
        ordered = []
        seen = set()
        for term in priority + concept_terms:
            if term and term not in seen:
                seen.add(term)
                ordered.append(term)
        return ordered
    if mode == "concept_priority_rescue":
        out = set(concept_terms)
        for term in priority:
            out.add(term)
        if rescue_targets:
            graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
            for rid in rescue_targets:
                row = graveyard.get(rid)
                if isinstance(row, dict):
                    t = _extract_term_from_item_text(str(row.get("item_text", "")))
                    if t:
                        out.add(t)
        ordered = []
        seen = set()
        for term in priority + concept_terms + sorted(out):
            if term and term not in seen:
                seen.add(term)
                ordered.append(term)
        return ordered
    if mode == "concept_local_rescue":
        out = set(concept_terms)
        if rescue_targets:
            graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
            for rid in rescue_targets:
                row = graveyard.get(rid)
                if isinstance(row, dict):
                    t = _extract_term_from_item_text(str(row.get("item_text", "")))
                    if t:
                        out.add(t)
        ordered = []
        seen = set()
        for term in priority + sorted(out):
            if term and term not in seen:
                seen.add(term)
                ordered.append(term)
        return ordered

    out = set(BASE_TERMS)
    for t in concept_terms:
        out.add(t)
    term_registry = state.get("term_registry", {}) if isinstance(state.get("term_registry", {}), dict) else {}
    for term in term_registry.keys():
        t = str(term).strip()
        if TERM_TOKEN_RE.fullmatch(t):
            out.add(t)
    for row in (state.get("graveyard", {}) or {}).values() if isinstance(state.get("graveyard", {}), dict) else []:
        if isinstance(row, dict):
            t = _extract_term_from_item_text(str(row.get("item_text", "")))
            if t:
                out.add(t)
    for row in (state.get("park_set", {}) or {}).values() if isinstance(state.get("park_set", {}), dict) else []:
        if isinstance(row, dict):
            t = _extract_term_from_item_text(str(row.get("item_text", "")))
            if t:
                out.add(t)
    if rescue_targets:
        graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
        for rid in rescue_targets:
            row = graveyard.get(rid)
            if isinstance(row, dict):
                t = _extract_term_from_item_text(str(row.get("item_text", "")))
                if t:
                    out.add(t)
    # Pull additional model-specific token candidates from refined A1 fuel docs
    # and A2 intent/context, then filter to math/QIT-relevant tokens.
    if mode != "concept_plus_rescue":
        for t in _extract_doc_terms(limit=300):
            out.add(t)
    ordered = []
    seen = set()
    for term in priority + sorted(out):
        if term and term not in seen:
            seen.add(term)
            ordered.append(term)
    return ordered


def _graveyard_term_set(state: dict) -> set[str]:
    out: set[str] = set()
    graveyard = state.get("graveyard", {}) if isinstance(state.get("graveyard", {}), dict) else {}
    for row in graveyard.values():
        if not isinstance(row, dict):
            continue
        t = _extract_term_from_item_text(str(row.get("item_text", "")))
        if t:
            out.add(t)
    return out


def _fuel_term_set(*, fuel_term_limit: int = 300) -> set[str]:
    out = set(BASE_TERMS)
    for t in _extract_doc_terms(limit=max(1, int(fuel_term_limit))):
        out.add(t)
    return {str(t).strip() for t in out if str(t).strip()}


def _extract_doc_terms(*, limit: int = 300) -> list[str]:
    candidates: list[Path] = []
    roots = [
        SYSTEM_V3 / "a2_state" / "A2_SYSTEM_UNDERSTANDING_UPDATE__SOURCE_BOUND_v2.md",
        SYSTEM_V3 / "a2_state" / "A2_TERM_CONFLICT_MAP__v1.md",
        SYSTEM_V3 / "a2_state" / "A2_TO_A1_DISTILLATION_INPUTS__v1.md",
        SYSTEM_V3 / "a2_state" / "A2_BRAIN_SLICE__v1.md",
        CORE_DOCS / "a1_refined_Ratchet Fuel",
        SYSTEM_V3 / "a2_state" / "INTENT_SUMMARY.md",
        SYSTEM_V3 / "a2_state" / "MODEL_CONTEXT.md",
        SYSTEM_V3 / "a2_state" / "OPEN_UNRESOLVED__v1.md",
        SYSTEM_V3 / "a2_state" / "SURFACE_CLASS_AND_MEMORY_ADMISSION_RULES__v1.md",
    ]
    for root in roots:
        if root.is_file():
            candidates.append(root)
        elif root.is_dir():
            for p in sorted(root.rglob("*.md"), key=lambda x: x.as_posix()):
                candidates.append(p)

    found: list[str] = []
    seen: set[str] = set()
    for path in candidates:
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            continue
        for tok in TOKEN_CANDIDATE_RE.findall(text):
            if not TERM_TOKEN_RE.fullmatch(tok):
                continue
            if tok not in CURATED_FUEL_TERMS:
                continue
            if tok in seen:
                continue
            if not any(k in tok for k in TERM_KEYWORDS):
                continue
            seen.add(tok)
            found.append(tok)
            if len(found) >= int(limit):
                return found
    return found


def _build_memo(
    *,
    run_id: str,
    sequence: int,
    role: str,
    proposed_terms: list[str],
    support_terms: list[str] | None = None,
    rescue_targets: list[str],
    extra_negative_classes: list[str] | None = None,
    extra_claims: list[str] | None = None,
    term_specificity_mode: str = "broad",
) -> dict:
    role_u = str(role).strip().upper()
    neg_classes: list[str] = []
    for value in list(extra_negative_classes or []) + list(
        ROLE_NEG_CLASSES.get(role_u, ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"])
    ):
        token = str(value).strip().upper()
        if token and token not in neg_classes:
            neg_classes.append(token)
    claims: list[str] = []
    for value in list(extra_claims or []) + list(ROLE_CLAIMS.get(role_u, ["Provide explicit nonclassical claims."])):
        text = str(value).strip()
        if text and text not in claims:
            claims.append(text)
    return {
        "schema": "A1_LAWYER_MEMO_v1",
        "run_id": str(run_id),
        "sequence": int(sequence),
        "role": role_u,
        "term_specificity_mode": str(term_specificity_mode).strip().lower(),
        "claims": claims,
        "risks": list(ROLE_RISKS.get(role_u, ["Do not smooth adversarial boundaries."])),
        "graveyard_rescue_targets": list(rescue_targets),
        "proposed_negative_classes": neg_classes,
        "proposed_terms": list(proposed_terms),
        "support_terms": [str(x).strip() for x in (support_terms or []) if str(x).strip()],
    }


def _gate_memo(path: Path, *, strict: bool) -> tuple[bool, dict]:
    cmd = ["python3", str(MEMO_GATE), "--input-json", str(path)]
    code, out, err = _run_cmd_proc(cmd, cwd=REPO)
    payload_raw = out or err
    payload: dict = {}
    if payload_raw:
        try:
            payload = json.loads(payload_raw)
        except Exception:
            payload = {"status": "FAIL", "failures": ["gate_payload_parse_failed"], "raw": payload_raw}
    status_ok = str(payload.get("status", "")).upper() == "PASS" and code == 0
    if strict and not status_ok:
        return False, payload
    return True, payload


def _write_memos_for_cycle(
    *,
    run_id: str,
    run_dir: Path,
    sequence: int,
    memo_drop_dir: Path,
    missing_roles: list[str],
    preset: str,
    prefill_depth: int,
    strict_gate: bool,
    concept_target_terms: list[str],
    priority_terms: list[str],
    priority_negative_classes: list[str],
    priority_claims: list[str],
    focus_term_mode: str,
    forced_terms: list[str] | None = None,
    support_terms: list[str] | None = None,
) -> dict:
    state = _read_json(run_dir / "state.json")
    rescue_targets = _collect_rescue_targets(state)
    terms = _collect_focus_terms(
        state,
        rescue_targets,
        concept_target_terms=concept_target_terms,
        priority_terms=priority_terms,
        focus_term_mode=focus_term_mode,
    )
    if forced_terms:
        terms = [str(t).strip() for t in forced_terms if str(t).strip()]
    memo_drop_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    written: list[str] = []
    rejected: list[dict] = []
    seq_to_roles: dict[int, set[str]] = {}
    seq_to_roles[int(sequence)] = {str(r).strip().upper() for r in missing_roles if str(r).strip()}
    future_roles = set(_required_roles_for_preset(preset))
    for offset in range(1, max(0, int(prefill_depth))):
        seq_to_roles[int(sequence) + offset] = set(future_roles)

    for seq, roles in sorted(seq_to_roles.items(), key=lambda x: x[0]):
        for role in sorted(roles):
            memo = _build_memo(
                run_id=run_id,
                sequence=int(seq),
                role=role,
                proposed_terms=terms,
                support_terms=support_terms,
                rescue_targets=rescue_targets,
                extra_negative_classes=priority_negative_classes,
                extra_claims=priority_claims,
                term_specificity_mode=focus_term_mode,
            )
            path = memo_drop_dir / f"{int(seq):06d}_MEMO_{role}__{ts}__DRIVER.json"
            if path.exists():
                continue
            path.write_text(json.dumps(memo, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            ok, gate = _gate_memo(path, strict=strict_gate)
            if ok:
                written.append(str(path))
            else:
                rejected.append({"path": str(path), "gate": gate})
                path.unlink(missing_ok=True)
    return {
        "written_count": len(written),
        "rejected_count": len(rejected),
        "written_paths": written,
        "rejected": rejected,
    }


def _emit_exchange_request(
    *,
    run_id: str,
    sequence: int,
    run_dir: Path,
    preset: str,
    required_roles: list[str],
    prompt_paths: list[str],
    terms: list[str],
    support_terms: list[str],
    rescue_targets: list[str],
    priority_negative_classes: list[str],
    priority_claims: list[str],
    focus_term_mode: str,
    a1_brain_context: dict | None = None,
    allowed_terms: list[str] | None = None,
) -> Path:
    root = _transient_exchange_root(run_id=run_id)
    req_dir = root / "requests"
    req_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    allowed = [str(x).strip() for x in (allowed_terms or []) if str(x).strip()]
    allowed_set = set(allowed)
    clean_terms = _dedup_keep_order([str(x).strip() for x in terms if str(x).strip()])
    clean_support_terms = _dedup_keep_order([str(x).strip() for x in support_terms if str(x).strip()])
    clean_rescue_targets = _dedup_keep_order([str(x).strip() for x in rescue_targets if str(x).strip()])
    if allowed:
        clean_terms = [term for term in allowed if term in allowed_set and term in set(clean_terms)]
        clean_rescue_targets = _clamp_rescue_targets_by_allowed_terms(
            clean_rescue_targets,
            allowed_terms=allowed,
        )
        if not clean_rescue_targets:
            clean_rescue_targets = list(clean_terms)
    obj = {
        "schema": "A1_EXTERNAL_MEMO_REQUEST_v1",
        "run_id": str(run_id),
        "sequence": int(sequence),
        "preset": str(preset),
        "required_roles": sorted({str(x).strip().upper() for x in required_roles if str(x).strip()}),
        "prompt_paths": list(prompt_paths),
        "term_candidates": list(clean_terms),
        "support_term_candidates": list(clean_support_terms),
        "graveyard_rescue_targets": list(clean_rescue_targets),
        "priority_negative_classes": [str(x).strip().upper() for x in priority_negative_classes if str(x).strip()],
        "priority_claims": [str(x).strip() for x in priority_claims if str(x).strip()],
        "focus_term_mode": str(focus_term_mode).strip().lower(),
        "a1_brain_context": dict(a1_brain_context or {}),
        "ts_utc": ts,
    }
    out = req_dir / f"{int(sequence):06d}__A1_EXTERNAL_MEMO_REQUEST__{ts}.json"
    out.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return out


def _latest_exchange_response(*, run_dir: Path, sequence: int) -> Path | None:
    run_id = str(run_dir.name).strip()
    req_dir = _transient_exchange_root(run_id=run_id) / "requests"
    if not req_dir.exists():
        return None
    pattern = f"{int(sequence):06d}__A1_EXTERNAL_MEMO_RESPONSE__*.json"
    candidates = sorted(req_dir.glob(pattern))
    return candidates[-1] if candidates else None


def _sanitize_memo_terms_for_allowed_set(memo: dict, *, allowed_terms: set[str]) -> dict:
    if not allowed_terms:
        return memo
    clean = dict(memo)
    proposed_terms = clean.get("proposed_terms")
    if isinstance(proposed_terms, list):
        filtered: list[str] = []
        for item in proposed_terms:
            term = str(item).strip()
            if term and term in allowed_terms and term not in filtered:
                filtered.append(term)
        clean["proposed_terms"] = filtered
    rescue_targets = clean.get("graveyard_rescue_targets")
    if isinstance(rescue_targets, list):
        clean["graveyard_rescue_targets"] = _clamp_rescue_targets_by_allowed_terms(
            [str(item).strip() for item in rescue_targets if str(item).strip()],
            allowed_terms=sorted(allowed_terms),
        )
    return clean


def _ingest_exchange_response(
    *,
    response_json: Path,
    run_id: str,
    sequence: int,
    memo_drop_dir: Path,
    strict_gate: bool,
    allowed_terms: list[str] | None = None,
) -> dict:
    if not response_json.exists():
        return {"status": "NO_RESPONSE_FILE", "written_count": 0, "rejected_count": 0, "written_paths": [], "rejected": []}
    obj = _read_json(response_json)
    if not isinstance(obj, dict):
        return {"status": "INVALID_RESPONSE", "written_count": 0, "rejected_count": 0, "written_paths": [], "rejected": []}
    memos = obj.get("memos", [])
    if not isinstance(memos, list):
        return {"status": "INVALID_MEMOS", "written_count": 0, "rejected_count": 0, "written_paths": [], "rejected": []}

    memo_drop_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    written: list[str] = []
    rejected: list[dict] = []
    allowed_set = {str(x).strip() for x in (allowed_terms or []) if str(x).strip()}
    for idx, row in enumerate(memos, start=1):
        if not isinstance(row, dict):
            rejected.append({"index": idx, "reason": "memo_not_object"})
            continue
        memo = dict(row)
        memo["schema"] = "A1_LAWYER_MEMO_v1"
        memo["run_id"] = str(memo.get("run_id", run_id))
        memo["sequence"] = int(memo.get("sequence", sequence) or sequence)
        memo["role"] = str(memo.get("role", "")).strip().upper()
        memo = _sanitize_memo_terms_for_allowed_set(memo, allowed_terms=allowed_set)
        path = memo_drop_dir / f"{int(sequence):06d}_MEMO_{memo['role'] or f'UNK_{idx:02d}'}__{ts}__EXTERNAL.json"
        path.write_text(json.dumps(memo, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        ok, gate = _gate_memo(path, strict=strict_gate)
        if ok:
            written.append(str(path))
        else:
            rejected.append({"path": str(path), "gate": gate})
            path.unlink(missing_ok=True)

    return {
        "status": "INGESTED" if written else "NO_VALID_MEMOS",
        "written_count": len(written),
        "rejected_count": len(rejected),
        "written_paths": written,
        "rejected": rejected,
    }


def _run_external_response_prepack(
    *,
    response_json: Path,
    run_id: str,
    sequence: int,
    runs_root: Path,
    debate_mode: str,
    goal_selection: str,
    graveyard_fill_policy: str,
    graveyard_library_terms: str,
    allowed_terms: str,
    forbid_rescue_in_graveyard_first: bool,
    max_terms: int,
) -> dict:
    stale_strategy = runs_root / str(run_id) / "a1_sandbox" / "outgoing" / f"{int(sequence):06d}_A1_STRATEGY_v1__PACK_SELECTOR.json"
    stale_strategy.unlink(missing_ok=True)
    cmd = [
        "python3",
        str(PREPACK_TOOL),
        "--run-id",
        str(run_id),
        "--runs-root",
        str(runs_root),
        "--sequence",
        str(int(sequence)),
        "--debate-mode",
        str(debate_mode),
        "--goal-selection",
        str(goal_selection),
        "--graveyard-fill-policy",
        str(graveyard_fill_policy),
        "--graveyard-library-terms",
        str(graveyard_library_terms),
        "--input",
        str(response_json),
    ]
    if str(allowed_terms).strip():
        cmd.extend(["--allowed-terms", str(allowed_terms).strip()])
    if bool(forbid_rescue_in_graveyard_first) and str(debate_mode) == "graveyard_first":
        cmd.append("--forbid-rescue-in-graveyard-first")
    if int(max_terms) > 0:
        cmd.extend(["--max-terms", str(int(max_terms))])
    proc = subprocess.run(cmd, cwd=str(REPO), check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        payload: dict = {}
        try:
            maybe_payload = json.loads((proc.stdout or "").strip() or "{}")
            if isinstance(maybe_payload, dict):
                payload = maybe_payload
        except Exception:
            payload = {}
        out = {
            "status": "PREPACK_FAILED",
            "code": int(proc.returncode),
            "stdout": (proc.stdout or "").strip()[-400:],
            "stderr": (proc.stderr or "").strip()[-400:],
            "response_json": str(response_json),
        }
        for key in (
            "report_path",
            "cold_core_path",
            "selector_cold_core_source",
            "selector_cold_core_path_class",
            "selector_cold_core_sha256",
            "selector_process_warnings",
            "failure_summary",
            "strategy_out",
            "mode",
        ):
            if key in payload:
                out[key] = payload.get(key)
        return out
    try:
        payload = json.loads((proc.stdout or "").strip() or "{}")
    except Exception:
        payload = {}
    payload["status"] = str(payload.get("status", "PASS")).strip() or "PASS"
    payload["response_json"] = str(response_json)
    return payload


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="External memo-batch driver for A1 sandbox (non-autofill path).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT))
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT))
    ap.add_argument("--preset", choices=["graveyard13", "entropy_lenses7", "lawyer4", "substrate5"], default="graveyard13")
    ap.add_argument(
        "--process-mode",
        choices=["legacy", "concept_path_rescue"],
        default="legacy",
        help="legacy uses debate-strategy directly; concept_path_rescue enforces graveyard_seed -> path_build -> rescue phases.",
    )
    ap.add_argument(
        "--concept-target-terms",
        default="",
        help="Comma-separated concept terms that must first appear in graveyard before rescue phase begins.",
    )
    ap.add_argument(
        "--seed-target-terms",
        default="",
        help="Optional comma-separated seed terms that control exit from graveyard_seed; defaults to concept-target-terms.",
    )
    ap.add_argument(
        "--focus-term-mode",
        choices=[
            "broad",
            "concept_plus_rescue",
            "concept_priority_rescue",
            "phase_seed_broad_then_priority",
            "concept_only",
            "concept_local_rescue",
        ],
        default="broad",
        help="How strongly to constrain worker/request term candidates around concept-target-terms.",
    )
    ap.add_argument("--debate-strategy", choices=["fixed", "graveyard_then_recovery"], default="graveyard_then_recovery")
    ap.add_argument("--debate-mode", choices=["balanced", "graveyard_first", "graveyard_recovery"], default="graveyard_first")
    ap.add_argument(
        "--fill-executed-cycles",
        type=int,
        default=6,
        help="When debate-strategy=graveyard_then_recovery, use graveyard_first for this many executed cycles, then graveyard_recovery.",
    )
    ap.add_argument(
        "--fill-until-graveyard-dominates",
        action="store_true",
        help="If set, remain in graveyard_first until graveyard count exceeds canonical count by --fill-graveyard-minus-canonical-min.",
    )
    ap.add_argument(
        "--fill-graveyard-minus-canonical-min",
        type=int,
        default=0,
        help="Minimum (graveyard_count - canonical_term_count) required before switching to graveyard_recovery when --fill-until-graveyard-dominates is set.",
    )
    ap.add_argument(
        "--fill-until-fuel-coverage",
        action="store_true",
        help="If set, keep graveyard_first until graveyard contains enough of extracted fuel terms.",
    )
    ap.add_argument(
        "--fill-fuel-coverage-target",
        type=float,
        default=1.0,
        help="Required graveyard coverage ratio over extracted fuel term set before recovery (0-1).",
    )
    ap.add_argument(
        "--fill-fuel-term-limit",
        type=int,
        default=300,
        help="Max extracted fuel terms considered for graveyard coverage gating.",
    )
    ap.add_argument(
        "--fill-min-graveyard-term-count",
        type=int,
        default=0,
        help="Minimum distinct graveyard terms required before switching to recovery in fill-until-fuel-coverage mode.",
    )
    ap.add_argument(
        "--graveyard-library-terms",
        default="",
        help="Comma-separated terms to treat as graveyard-library (processed in graveyard, excluded from rescue).",
    )
    ap.add_argument(
        "--graveyard-library-mode",
        choices=["explicit", "from_fuel"],
        default="explicit",
        help="explicit uses --graveyard-library-terms only; from_fuel uses extracted fuel terms (plus explicit terms).",
    )
    ap.add_argument(
        "--fill-until-library-coverage",
        action="store_true",
        help="If set, keep graveyard-first until graveyard coverage over graveyard-library-terms meets target.",
    )
    ap.add_argument(
        "--fill-library-coverage-target",
        type=float,
        default=1.0,
        help="Required graveyard coverage ratio over graveyard-library-terms before recovery (0-1).",
    )
    ap.add_argument("--graveyard-fill-cycles", type=int, default=8)
    ap.add_argument("--graveyard-fill-max-stall-cycles", type=int, default=1)
    ap.add_argument("--goal-selection", choices=["closure_first", "interleaved"], default="closure_first")
    ap.add_argument("--track", default="ENGINE_ENTROPY_EXPLORATION")
    ap.add_argument(
        "--priority-terms",
        default="",
        help="Comma-separated terms to force to the front of the A1 memo/request candidate set.",
    )
    ap.add_argument(
        "--path-build-allowed-terms",
        default="",
        help="Optional comma-separated hard allowlist for worker requests and prepack selection during path_build.",
    )
    ap.add_argument(
        "--rescue-allowed-terms",
        default="",
        help="Optional comma-separated hard allowlist for worker requests and prepack selection during rescue.",
    )
    ap.add_argument(
        "--seed-allowed-terms",
        default="",
        help="Optional comma-separated hard allowlist for worker requests and prepack selection during graveyard_seed.",
    )
    ap.add_argument(
        "--priority-negative-classes",
        default="",
        help="Comma-separated negative classes to force into every memo before role-default negatives.",
    )
    ap.add_argument(
        "--priority-claims",
        default="",
        help="Pipe-delimited claims to force into every memo before role-default claims.",
    )
    ap.add_argument(
        "--probe-companion-terms",
        default="",
        help="Comma-separated witness-only support terms pinned into live support generation.",
    )
    ap.add_argument("--max-run-mb", type=float, default=60.0)
    ap.add_argument("--target-executed-cycles", type=int, default=20)
    ap.add_argument(
        "--path-build-min-cycles",
        type=int,
        default=8,
        help="Minimum executed cycles spent in path_build phase before rescue.",
    )
    ap.add_argument(
        "--path-build-max-cycles",
        type=int,
        default=40,
        help="Maximum executed cycles in path_build before forcing rescue (if minimums are met).",
    )
    ap.add_argument(
        "--path-build-novelty-stall-max",
        type=int,
        default=8,
        help="If unique structural digest count stalls this many cycles during path_build, allow rescue transition.",
    )
    ap.add_argument(
        "--rescue-novelty-stall-max",
        type=int,
        default=6,
        help="If unique structural digest count stalls this many cycles during rescue, stop the loop instead of replaying the same rescue family.",
    )
    ap.add_argument(
        "--rescue-start-min-canonical",
        type=int,
        default=25,
        help="Minimum canonical terms before rescue phase in concept_path_rescue mode.",
    )
    ap.add_argument(
        "--rescue-start-min-graveyard",
        type=int,
        default=80,
        help="Minimum graveyard count before rescue phase in concept_path_rescue mode.",
    )
    ap.add_argument(
        "--rescue-start-min-kill-diversity",
        type=int,
        default=5,
        help="Minimum kill token diversity before rescue phase in concept_path_rescue mode.",
    )
    ap.add_argument(
        "--seed-max-terms-per-cycle",
        type=int,
        default=24,
        help="Pack selector max terms during graveyard_seed phase.",
    )
    ap.add_argument(
        "--path-max-terms-per-cycle",
        type=int,
        default=18,
        help="Pack selector max terms during path_build phase.",
    )
    ap.add_argument(
        "--rescue-max-terms-per-cycle",
        type=int,
        default=16,
        help="Pack selector max terms during rescue phase.",
    )
    ap.add_argument(
        "--goal-min-canonical-terms",
        type=int,
        default=35,
        help="Stop early once canonical term floor is reached (after min-executed-cycles-before-goal).",
    )
    ap.add_argument(
        "--goal-min-graveyard-count",
        type=int,
        default=45,
        help="Stop early once graveyard floor is reached (after min-executed-cycles-before-goal).",
    )
    ap.add_argument(
        "--goal-min-sim-registry-count",
        type=int,
        default=450,
        help="Stop early once SIM registry floor is reached (after min-executed-cycles-before-goal).",
    )
    ap.add_argument(
        "--min-executed-cycles-before-goal",
        type=int,
        default=16,
        help="Do not apply early-goal stopping before this many executed cycles.",
    )
    ap.add_argument("--max-wait-cycles", type=int, default=80)
    ap.add_argument(
        "--seed-force-transition-min-executed",
        type=int,
        default=-1,
        help="If >=0, allow graveyard_seed -> path_build after this many executed cycles when the other force-transition floors are met.",
    )
    ap.add_argument(
        "--seed-force-transition-min-graveyard",
        type=int,
        default=0,
        help="Minimum graveyard_count required for the seed-force-transition override.",
    )
    ap.add_argument(
        "--seed-force-transition-min-kill-diversity",
        type=int,
        default=0,
        help="Minimum kill-token diversity required for the seed-force-transition override.",
    )
    ap.add_argument("--campaign-graveyard-fill-min-delta", type=int, default=0)
    ap.add_argument("--campaign-graveyard-fill-max-canonical-delta", type=int, default=99)
    ap.add_argument("--campaign-recovery-min-rescue-from-fields", type=int, default=1)
    ap.add_argument(
        "--campaign-graveyard-fill-policy",
        choices=["anchor_replay", "fuel_full_load"],
        default="fuel_full_load",
        help="Pass-through to campaign runner pack selector fill policy.",
    )
    ap.add_argument(
        "--campaign-forbid-rescue-during-graveyard-fill",
        action="store_true",
        help="Pass-through to strip RESCUE_FROM in graveyard_first cycles.",
    )
    ap.add_argument("--memo-provider-mode", choices=["template", "exchange"], default="template")
    ap.add_argument(
        "--external-response-prepack",
        dest="external_response_prepack",
        action="store_true",
        default=True,
        help="Run the A1 consolidation/prepack adapter on each exchange response (default: on).",
    )
    ap.add_argument(
        "--no-external-response-prepack",
        dest="external_response_prepack",
        action="store_false",
        help="Disable the A1 consolidation/prepack adapter for exchange responses.",
    )
    ap.add_argument(
        "--provider-script",
        default="",
        help=(
            "Optional external provider script path. When --memo-provider-mode=exchange, "
            "it is invoked as: python3 <script> --request-json <path> --response-json <path>"
        ),
    )
    ap.add_argument("--provider-timeout-sec", type=int, default=120)
    ap.add_argument(
        "--memo-prefill-depth",
        type=int,
        default=3,
        help="When WAITING_FOR_MEMOS, pre-generate this many sequences (current + future) to reduce wait overhead.",
    )
    ap.add_argument(
        "--a1-brain-context-max-chars",
        type=int,
        default=12000,
        help="Max characters to include in external memo request context payload.",
    )
    ap.add_argument(
        "--verbose-timeline",
        action="store_true",
        help="If set, keep full path-level details in timeline; default stores compact counts only.",
    )
    ap.add_argument("--strict-local-gate-check", action="store_true")
    ap.add_argument(
        "--forbid-provider-stub",
        action="store_true",
        help="Fail fast if provider_script path appears to be the local stub implementation.",
    )
    ap.add_argument("--post-run-audits", dest="post_run_audits", action="store_true", default=True)
    ap.add_argument("--no-post-run-audits", dest="post_run_audits", action="store_false")
    ap.add_argument(
        "--post-run-audit-phase",
        choices=["auto", "mixed", "graveyard_fill", "recovery"],
        default="auto",
        help="Phase for post-run audit tools. auto resolves from final process phase.",
    )
    ap.add_argument(
        "--post-run-semantic-recent-rows",
        type=int,
        default=300,
        help="Recent semantic sim row window for post-run semantic audit in mixed/recovery phases.",
    )
    args = ap.parse_args(argv)

    run_id = str(args.run_id).strip()
    runs_root = Path(args.runs_root).expanduser().resolve()
    a2_state_dir = Path(args.a2_state_dir).expanduser().resolve()
    run_dir = runs_root / run_id
    report_path = run_dir / "reports" / "a1_external_memo_batch_driver_report.json"

    provider_script = str(args.provider_script).strip()
    provider_is_stub = bool(provider_script) and Path(provider_script).name == "a1_external_memo_provider_stub.py"
    if bool(args.forbid_provider_stub) and provider_is_stub:
        raise SystemExit("provider_script points to stub provider; use a real external provider script")

    executed = 0
    waits = 0
    executed_baseline = 0
    wait_baseline = 0
    clean_flag = bool(args.clean)
    timeline: list[dict] = []
    a1_brain_context = _load_a1_brain_context(
        max_chars=int(args.a1_brain_context_max_chars),
        track=str(args.track),
    )
    fuel_term_set = _fuel_term_set(fuel_term_limit=int(args.fill_fuel_term_limit))
    fill_target = max(0.0, min(1.0, float(args.fill_fuel_coverage_target)))
    explicit_library_terms = _parse_csv_term_set(str(args.graveyard_library_terms))
    if str(args.graveyard_library_mode) == "from_fuel":
        library_term_set = set(fuel_term_set) | set(explicit_library_terms)
    else:
        library_term_set = set(explicit_library_terms)
    library_target = max(0.0, min(1.0, float(args.fill_library_coverage_target)))
    library_terms_csv = _csv_from_terms(library_term_set)
    concept_target_terms = _parse_csv_terms(str(args.concept_target_terms))
    seed_target_terms = _parse_csv_terms(str(args.seed_target_terms)) or list(concept_target_terms)
    priority_terms = _parse_csv_terms(str(args.priority_terms))
    path_build_allowed_terms = _parse_csv_terms(str(args.path_build_allowed_terms))
    rescue_allowed_terms = _parse_csv_terms(str(args.rescue_allowed_terms))
    seed_allowed_terms = _parse_csv_terms(str(args.seed_allowed_terms))
    priority_negative_classes = [str(x).strip().upper() for x in _parse_csv_terms(str(args.priority_negative_classes))]
    priority_claims = _parse_pipe_claims(str(args.priority_claims))
    focus_term_mode = str(args.focus_term_mode)
    process_mode = str(args.process_mode)
    path_build_cycles_executed = 0
    current_phase = "legacy"
    last_unique_structural = -1
    path_build_novelty_stall = 0
    rescue_novelty_stall = 0
    rescue_recent_signatures: list[str] = []
    rescue_recent_strategy_signatures: list[str] = []
    rescue_recent_plan_signatures: list[str] = []
    pending_rescue_plan_signature = ""
    pending_rescue_plan_is_new = False

    resumed_process_phase = ""
    rescue_resume_carryover_pending = False
    if report_path.exists() and not clean_flag:
        previous_report = _read_json(report_path)
        if isinstance(previous_report, dict) and str(previous_report.get("schema", "")).strip() == "A1_EXTERNAL_MEMO_BATCH_DRIVER_REPORT_v1":
            executed_baseline = int(previous_report.get("executed_cycles_total", previous_report.get("executed_cycles", 0)) or 0)
            wait_baseline = int(previous_report.get("wait_cycles_total", previous_report.get("wait_cycles", 0)) or 0)
            last_unique_structural = int(previous_report.get("last_unique_structural", -1) or -1)
            last_timeline = previous_report.get("timeline", []) or []
            if isinstance(last_timeline, list) and last_timeline:
                last_row = last_timeline[-1] if isinstance(last_timeline[-1], dict) else {}
                resumed_process_phase = str(last_row.get("process_phase", "")).strip()
                fill_status = last_row.get("fill_status", {}) if isinstance(last_row, dict) else {}
                if isinstance(fill_status, dict):
                    path_build_cycles_executed = int(fill_status.get("path_build_cycles_executed", 0) or 0)
                    path_build_novelty_stall = int(fill_status.get("path_build_novelty_stall", 0) or 0)
                    rescue_novelty_stall = int(fill_status.get("rescue_novelty_stall", 0) or 0)
            rescue_resume_carryover_pending = (
                resumed_process_phase == "rescue"
                and int(rescue_novelty_stall) > 0
            )

    goal_reached = False
    while executed < int(args.target_executed_cycles) and waits < int(args.max_wait_cycles):
        executed_total = executed_baseline + executed
        counts_now = _state_counts(run_dir) if run_dir.exists() else {}
        canonical_now = int(counts_now.get("canonical_term_count", 0))
        graveyard_now = int(counts_now.get("graveyard_count", 0))
        if run_dir.exists():
            state_now = _read_json(run_dir / "state.json")
            graveyard_terms_now = _graveyard_term_set(state_now)
        else:
            state_now = {}
            graveyard_terms_now = set()
        fuel_overlap = len(graveyard_terms_now & fuel_term_set)
        fuel_total = len(fuel_term_set) if fuel_term_set else 0
        fuel_coverage = (float(fuel_overlap) / float(fuel_total)) if fuel_total > 0 else 1.0
        library_overlap = len(graveyard_terms_now & library_term_set)
        library_total = len(library_term_set) if library_term_set else 0
        library_coverage = (float(library_overlap) / float(library_total)) if library_total > 0 else 1.0
        kill_diversity_now = _kill_token_diversity(state_now)

        summary_now = _read_json(run_dir / "summary.json") if run_dir.exists() else {}
        unique_structural_now = int(summary_now.get("unique_export_structural_digest_count", 0) or 0)
        concept_in_graveyard = True
        if seed_target_terms:
            concept_in_graveyard = all(t in graveyard_terms_now for t in seed_target_terms)

        force_fill_by_dominance = False
        if bool(args.fill_until_graveyard_dominates):
            force_fill_by_dominance = (graveyard_now - canonical_now) < int(args.fill_graveyard_minus_canonical_min)

        force_fill_by_fuel = False
        if bool(args.fill_until_fuel_coverage):
            force_fill_by_fuel = (
                fuel_coverage < fill_target
                or len(graveyard_terms_now) < int(args.fill_min_graveyard_term_count)
            )
        force_fill_by_library = False
        if bool(args.fill_until_library_coverage):
            force_fill_by_library = library_coverage < library_target

        if process_mode == "concept_path_rescue":
            seed_force_transition = False
            if int(args.seed_force_transition_min_executed) >= 0:
                seed_force_transition = (
                    executed_total >= int(args.seed_force_transition_min_executed)
                    and graveyard_now >= int(args.seed_force_transition_min_graveyard)
                    and kill_diversity_now >= int(args.seed_force_transition_min_kill_diversity)
                )
            seed_ready = (
                concept_in_graveyard and (not force_fill_by_fuel) and (not force_fill_by_library)
            ) or seed_force_transition
            rescue_prereq = (
                canonical_now >= int(args.rescue_start_min_canonical)
                and graveyard_now >= int(args.rescue_start_min_graveyard)
                and kill_diversity_now >= int(args.rescue_start_min_kill_diversity)
            )
            if not seed_ready:
                current_phase = "graveyard_seed"
            elif path_build_cycles_executed < int(args.path_build_min_cycles):
                current_phase = "path_build"
            elif rescue_prereq and (
                path_build_cycles_executed >= int(args.path_build_max_cycles)
                or path_build_novelty_stall >= int(args.path_build_novelty_stall_max)
            ):
                current_phase = "rescue"
            elif rescue_prereq:
                current_phase = "rescue"
            else:
                current_phase = "path_build"

            if (
                executed == 0
                and waits == 0
                and resumed_process_phase in {"path_build", "rescue"}
                and not bool(clean_flag)
            ):
                current_phase = resumed_process_phase

            if current_phase in {"graveyard_seed", "path_build"}:
                cycle_debate_mode = "graveyard_first"
                cycle_debate_strategy = "fixed"
                campaign_fill_policy = "fuel_full_load"
                campaign_forbid_rescue = True
                pack_selector_max_terms = (
                    int(args.seed_max_terms_per_cycle)
                    if current_phase == "graveyard_seed"
                    else int(args.path_max_terms_per_cycle)
                )
            else:
                cycle_debate_mode = "graveyard_recovery"
                cycle_debate_strategy = "fixed"
                campaign_fill_policy = "anchor_replay"
                campaign_forbid_rescue = False
                pack_selector_max_terms = int(args.rescue_max_terms_per_cycle)
        else:
            current_phase = "legacy"
            if str(args.debate_strategy) == "graveyard_then_recovery":
                cycle_debate_mode = "graveyard_first" if executed_total < int(args.fill_executed_cycles) else "graveyard_recovery"
                if force_fill_by_dominance or force_fill_by_fuel or force_fill_by_library:
                    cycle_debate_mode = "graveyard_first"
                cycle_debate_strategy = "fixed"
            else:
                cycle_debate_mode = str(args.debate_mode)
                cycle_debate_strategy = "fixed"
            campaign_fill_policy = str(args.campaign_graveyard_fill_policy)
            campaign_forbid_rescue = bool(args.campaign_forbid_rescue_during_graveyard_fill)
            pack_selector_max_terms = 0

        if current_phase not in {"path_build", "rescue"}:
            path_build_novelty_stall = 0
            rescue_novelty_stall = 0

        current_focus_term_mode = focus_term_mode
        if focus_term_mode == "phase_seed_broad_then_priority":
            current_focus_term_mode = "concept_plus_rescue" if current_phase == "graveyard_seed" else "concept_priority_rescue"
        current_allowed_terms: list[str] = []
        if current_phase == "graveyard_seed" and seed_allowed_terms:
            current_allowed_terms = [t for t in seed_allowed_terms if t]
        elif current_phase == "path_build" and path_build_allowed_terms:
            current_allowed_terms = [t for t in path_build_allowed_terms if t]
        elif current_phase == "rescue" and rescue_allowed_terms:
            current_allowed_terms = [t for t in rescue_allowed_terms if t]
        elif current_phase == "legacy" and current_focus_term_mode == "concept_local_rescue" and concept_target_terms:
            # Legacy concept-local runs must still clamp proposal ingress to the
            # actual concept targets, otherwise canonical helper terms can
            # re-enter as local heads and shadow the intended structure route.
            current_allowed_terms = [t for t in concept_target_terms if t]
        elif current_focus_term_mode == "concept_local_rescue" and concept_target_terms:
            # Concept-local rescue should stay clamped to the target structure
            # family unless an explicit phase allowlist is provided.
            current_allowed_terms = [t for t in concept_target_terms if t]
        rescue_recent_window = max(8, (len(current_allowed_terms) * 2) if current_allowed_terms else 8)

        cmd = [
            "python3",
            str(CAMPAIGN),
            "--run-id",
            run_id,
            "--runs-root",
            str(runs_root),
            "--a2-state-dir",
            str(a2_state_dir),
            "--preset",
            str(args.preset),
            "--debate-strategy",
            str(cycle_debate_strategy),
            "--debate-mode",
            str(cycle_debate_mode),
            "--graveyard-fill-cycles",
            str(int(args.graveyard_fill_cycles)),
            "--graveyard-fill-max-stall-cycles",
            str(int(args.graveyard_fill_max_stall_cycles)),
            "--graveyard-fill-min-delta",
            str(int(args.campaign_graveyard_fill_min_delta)),
            "--graveyard-fill-max-canonical-delta",
            str(int(args.campaign_graveyard_fill_max_canonical_delta)),
            "--recovery-min-rescue-from-fields",
            str(int(args.campaign_recovery_min_rescue_from_fields)),
            "--graveyard-fill-policy",
            str(campaign_fill_policy),
            "--graveyard-library-terms",
            str(library_terms_csv),
            "--pack-selector-max-terms",
            str(max(0, int(pack_selector_max_terms))),
            "--goal-selection",
            str(args.goal_selection),
            "--track",
            str(args.track),
            "--max-cycles",
            "1",
            "--max-run-mb",
            str(float(args.max_run_mb)),
            "--memo-quality-gate",
        ]
        if bool(campaign_forbid_rescue):
            cmd.append("--forbid-rescue-during-graveyard-fill")
        if clean_flag:
            cmd.append("--clean")
            clean_flag = False
        out = _run_cmd(cmd, cwd=REPO)
        result = json.loads(out)
        report_path = Path(str(result.get("out", "")).strip())
        report = _read_json(report_path)
        cycle = (report.get("cycles", []) or [{}])[-1]
        status = str(cycle.get("status", "")).strip()
        selector_fields = _selector_provenance_fields(cycle if isinstance(cycle, dict) else {})
        row = {
            "status": status,
            "sequence": int(cycle.get("sequence", 0) or 0),
            "run_stop_reason": result.get("stop_reason", ""),
            "cycle_debate_mode": cycle_debate_mode,
            "process_phase": current_phase,
            **selector_fields,
            "current_allowed_terms": list(current_allowed_terms),
            "fill_status": {
                "force_fill_by_dominance": bool(force_fill_by_dominance),
                "force_fill_by_fuel": bool(force_fill_by_fuel),
                "force_fill_by_library": bool(force_fill_by_library),
                "seed_force_transition": bool(seed_force_transition if process_mode == "concept_path_rescue" else False),
                "fuel_coverage": fuel_coverage,
                "fuel_overlap": int(fuel_overlap),
                "fuel_total": int(fuel_total),
                "library_coverage": library_coverage,
                "library_overlap": int(library_overlap),
                "library_total": int(library_total),
                "graveyard_terms_count": len(graveyard_terms_now),
                "concept_in_graveyard": bool(concept_in_graveyard),
                "path_build_cycles_executed": int(path_build_cycles_executed),
                "path_build_novelty_stall": int(path_build_novelty_stall),
                "rescue_novelty_stall": int(rescue_novelty_stall),
                "kill_token_diversity": int(kill_diversity_now),
                "pack_selector_max_terms": int(pack_selector_max_terms),
                "path_build_allowed_terms_active": list(path_build_allowed_terms) if current_phase == "path_build" else [],
                "rescue_allowed_terms_active": list(rescue_allowed_terms) if current_phase == "rescue" else [],
            },
        }
        cold_core_sequence_mismatch_stage = str(cycle.get("cold_core_sequence_mismatch_stage", "")).strip()
        if cold_core_sequence_mismatch_stage:
            row["cold_core_sequence_mismatch_stage"] = cold_core_sequence_mismatch_stage
        if status == "STEP_EXECUTED":
            executed += 1
            if current_phase == "path_build":
                path_build_cycles_executed += 1
            counts = _state_counts(run_dir)
            row["state_counts"] = counts
            summary_after = _read_json(run_dir / "summary.json") if run_dir.exists() else {}
            unique_structural_after = int(summary_after.get("unique_export_structural_digest_count", unique_structural_now) or 0)
            if current_phase == "path_build":
                if unique_structural_after > int(last_unique_structural):
                    path_build_novelty_stall = 0
                else:
                    path_build_novelty_stall += 1
                rescue_novelty_stall = 0
            elif current_phase == "rescue":
                strategy_signature = _strategy_shape_signature(
                    run_dir,
                    sequence=int(cycle.get("sequence", 0) or 0),
                    allowed_terms=current_allowed_terms,
                )
                strategy_signature_is_new = bool(strategy_signature) and strategy_signature not in rescue_recent_strategy_signatures
                if rescue_resume_carryover_pending:
                    strategy_signature_is_new = False
                row["strategy_signature"] = strategy_signature
                row["strategy_signature_is_new"] = bool(strategy_signature_is_new)
                row["rescue_plan_signature"] = pending_rescue_plan_signature
                row["rescue_plan_is_new"] = bool(pending_rescue_plan_is_new)
                if (
                    unique_structural_after > int(last_unique_structural)
                    or strategy_signature_is_new
                    or pending_rescue_plan_is_new
                ):
                    rescue_novelty_stall = 0
                else:
                    rescue_novelty_stall += 1
                if strategy_signature_is_new:
                    rescue_recent_strategy_signatures.append(strategy_signature)
                rescue_recent_strategy_signatures = rescue_recent_strategy_signatures[-rescue_recent_window:]
                pending_rescue_plan_signature = ""
                pending_rescue_plan_is_new = False
                rescue_resume_carryover_pending = False
            last_unique_structural = unique_structural_after
            row["fill_status"]["path_build_novelty_stall"] = int(path_build_novelty_stall)
            row["fill_status"]["rescue_novelty_stall"] = int(rescue_novelty_stall)
            if current_phase == "rescue" and rescue_novelty_stall >= int(args.rescue_novelty_stall_max):
                row["run_stop_reason"] = "STOPPED__RESCUE_NOVELTY_STALL"
                row["driver_override_stop_reason"] = "rescue_novelty_stall"
                emitted_row = _annotate_first_failure_info(row)
                timeline.append(emitted_row if bool(args.verbose_timeline) else _compact_timeline_row(emitted_row))
                break
            allow_goal_stop = True
            if process_mode == "concept_path_rescue":
                allow_goal_stop = current_phase == "rescue"
            if allow_goal_stop and (executed_baseline + executed) >= int(args.min_executed_cycles_before_goal):
                if (
                    int(counts.get("canonical_term_count", 0)) >= int(args.goal_min_canonical_terms)
                    and int(counts.get("graveyard_count", 0)) >= int(args.goal_min_graveyard_count)
                    and int(counts.get("sim_registry_count", 0)) >= int(args.goal_min_sim_registry_count)
                ):
                    goal_reached = True
                    emitted_row = _annotate_first_failure_info(row)
                    timeline.append(emitted_row if bool(args.verbose_timeline) else _compact_timeline_row(emitted_row))
                    break
        elif status == "WAITING_FOR_MEMOS":
            waits += 1
            memo_drop_dir = Path(str(cycle.get("memo_drop_dir", "")).strip())
            sequence = int(cycle.get("sequence", 0) or 0)
            missing_roles = [str(x).strip() for x in (cycle.get("missing_roles", []) or []) if str(x).strip()]
            state = _read_json(run_dir / "state.json")
            rescue_targets = _collect_rescue_targets(state)
            terms = _collect_focus_terms(
                state,
                rescue_targets,
                concept_target_terms=concept_target_terms,
                priority_terms=priority_terms,
                focus_term_mode=current_focus_term_mode,
            )
            if current_phase == "graveyard_seed" and seed_allowed_terms:
                terms = [t for t in seed_allowed_terms if t]
            if current_phase == "path_build" and path_build_allowed_terms:
                terms = [t for t in path_build_allowed_terms if t]
            if current_phase == "rescue" and rescue_allowed_terms:
                terms = [t for t in rescue_allowed_terms if t]
            if current_phase == "legacy" and current_focus_term_mode == "concept_local_rescue" and concept_target_terms:
                terms = [t for t in concept_target_terms if t]
            current_allowed_terms: list[str] = []
            if current_phase == "graveyard_seed" and seed_allowed_terms:
                current_allowed_terms = [t for t in seed_allowed_terms if t]
            elif current_phase == "path_build" and path_build_allowed_terms:
                current_allowed_terms = [t for t in path_build_allowed_terms if t]
            elif current_phase == "rescue" and rescue_allowed_terms:
                current_allowed_terms = [t for t in rescue_allowed_terms if t]
            elif current_phase == "legacy" and current_focus_term_mode == "concept_local_rescue" and concept_target_terms:
                current_allowed_terms = [t for t in concept_target_terms if t]
            elif current_focus_term_mode == "concept_local_rescue" and concept_target_terms:
                current_allowed_terms = [t for t in concept_target_terms if t]
            if current_allowed_terms:
                terms = [t for t in current_allowed_terms if t]
            if current_allowed_terms:
                rescue_targets = _filter_rescue_targets_for_allowed_terms(
                    state,
                    rescue_targets,
                    allowed_terms=current_allowed_terms,
                )
                rescue_targets = _clamp_rescue_targets_by_allowed_terms(
                    rescue_targets,
                    allowed_terms=current_allowed_terms,
                )
            rescue_recent_window = max(8, (len(current_allowed_terms) * 2) if current_allowed_terms else 8)
            proposal_support_terms: list[str] = []
            probe_companion_terms = _parse_csv_terms(str(getattr(args, "probe_companion_terms", "")))
            if current_phase == "rescue":
                stalled_bootstrap_terms: set[str] = set()
                stalled_bootstrap_histogram: dict[str, int] = {}
                bootstrap_companion_terms: list[str] = []
                bootstrap_companion_histogram: dict[str, int] = {}
                pinned_support_terms: list[str] = []
                witness_activation_support_terms: list[str] = []
                pinned_rescue_fragment_terms: list[str] = []
                rescue_rotation_keep_head_terms = 2
                rescue_rotation_width_terms = 2
                rescue_rotation_keep_head_targets = 2
                rescue_rotation_width_targets = 2
                if rescue_novelty_stall >= 2:
                    rescue_rotation_keep_head_terms = 1
                if rescue_novelty_stall >= 4:
                    rescue_rotation_width_terms = 3
                    rescue_rotation_width_targets = 3
                if rescue_novelty_stall >= 8:
                    rescue_rotation_keep_head_terms = 0
                    rescue_rotation_keep_head_targets = 0
                    rescue_rotation_width_terms = 4
                    rescue_rotation_width_targets = 4
                if current_allowed_terms:
                    stalled_bootstrap_terms, stalled_bootstrap_histogram = _bootstrap_stalled_terms(
                        run_dir,
                        max_sequence=max(0, int(sequence) - 1),
                        allowed_terms=current_allowed_terms,
                        min_repeats=3,
                        window=12,
                    )
                    if stalled_bootstrap_terms:
                        filtered_terms = [
                            term for term in terms
                            if term not in stalled_bootstrap_terms
                        ]
                        if filtered_terms:
                            terms = filtered_terms
                        filtered_rescue_targets = [
                            target for target in rescue_targets
                            if _rescue_target_term(state, target) not in stalled_bootstrap_terms
                        ]
                        if filtered_rescue_targets:
                            rescue_targets = filtered_rescue_targets
                        bootstrap_companion_terms, bootstrap_companion_histogram = _recent_bootstrap_companion_terms(
                            run_dir,
                            max_sequence=max(0, int(sequence) - 1),
                            allowed_terms=sorted(stalled_bootstrap_terms),
                            min_repeats=2,
                            window=12,
                        )
                    fallback_support_terms = _fallback_decomposition_support_terms(
                        allowed_terms=current_allowed_terms,
                        stalled_terms=stalled_bootstrap_terms,
                    )
                    fallback_rescue_fragments = _fallback_decomposition_rescue_fragments(
                        stalled_terms=stalled_bootstrap_terms,
                    )
                    fallback_witness_activation_support_terms = _fallback_witness_activation_support_terms(
                        stalled_terms=stalled_bootstrap_terms,
                    )
                    if fallback_support_terms:
                        pinned_support_terms = list(fallback_support_terms)
                        existing = list(bootstrap_companion_terms)
                        existing.extend(fallback_support_terms)
                        bootstrap_companion_terms = _dedup_keep_order(existing)
                        for term in fallback_support_terms:
                            if term not in bootstrap_companion_histogram:
                                bootstrap_companion_histogram[term] = 0
                    if fallback_rescue_fragments:
                        pinned_rescue_fragment_terms = list(fallback_rescue_fragments)
                    if fallback_witness_activation_support_terms:
                        witness_activation_support_terms = list(fallback_witness_activation_support_terms)
                        existing = list(bootstrap_companion_terms)
                        existing.extend(fallback_witness_activation_support_terms)
                        bootstrap_companion_terms = _dedup_keep_order(existing)
                        for term in fallback_witness_activation_support_terms:
                            if term not in bootstrap_companion_histogram:
                                bootstrap_companion_histogram[term] = 0
                effective_allowed_terms = list(terms) if terms else list(current_allowed_terms or [])
                row["rescue_bootstrap_stalled_terms"] = sorted(stalled_bootstrap_terms)
                row["rescue_bootstrap_stalled_histogram"] = stalled_bootstrap_histogram
                row["rescue_bootstrap_companion_terms"] = list(bootstrap_companion_terms)
                row["rescue_bootstrap_companion_histogram"] = bootstrap_companion_histogram
                row["rescue_pinned_support_terms"] = list(pinned_support_terms)
                row["rescue_witness_activation_support_terms"] = list(witness_activation_support_terms)
                row["rescue_pinned_fragment_terms"] = list(pinned_rescue_fragment_terms)
                row["rescue_rotation_keep_head_terms"] = int(rescue_rotation_keep_head_terms)
                row["rescue_rotation_width_terms"] = int(rescue_rotation_width_terms)
                row["rescue_rotation_keep_head_targets"] = int(rescue_rotation_keep_head_targets)
                row["rescue_rotation_width_targets"] = int(rescue_rotation_width_targets)
                if current_allowed_terms and bootstrap_companion_terms:
                    ordered_support_terms = list(probe_companion_terms)
                    ordered_support_terms.extend(witness_activation_support_terms)
                    ordered_support_terms.extend(pinned_support_terms)
                    ordered_support_terms.extend(bootstrap_companion_terms)
                    unique_support_terms = [
                        term
                        for term in _dedup_keep_order(ordered_support_terms)
                        if term not in current_allowed_terms
                    ]
                    support_keep_head_terms = max(1, len(witness_activation_support_terms))
                    support_rotate_width_terms = 2
                    if rescue_novelty_stall >= 4:
                        support_keep_head_terms = 0
                        support_rotate_width_terms = 3
                    if rescue_novelty_stall >= 8:
                        support_keep_head_terms = 0
                        support_rotate_width_terms = 4
                    proposal_support_terms = _deterministic_rotating_term_subset(
                        unique_support_terms,
                        sequence=sequence,
                        keep_head=support_keep_head_terms,
                        rotate_width=support_rotate_width_terms,
                    ) or list(unique_support_terms)
                    proposal_support_terms = proposal_support_terms[:4]
                    row["rescue_support_keep_head_terms"] = int(support_keep_head_terms)
                    row["rescue_support_rotate_width_terms"] = int(support_rotate_width_terms)
            if probe_companion_terms:
                proposal_support_terms = _dedup_keep_order(
                    list(probe_companion_terms) + list(proposal_support_terms)
                )[:4]
            if current_allowed_terms:
                narrowed_allowed_terms = [
                    t for t in effective_allowed_terms
                    if t in current_allowed_terms
                ] if effective_allowed_terms else [t for t in current_allowed_terms if t]
                if narrowed_allowed_terms:
                    terms = list(narrowed_allowed_terms)
                    effective_allowed_terms = list(narrowed_allowed_terms)
                else:
                    terms = [t for t in current_allowed_terms if t]
                    effective_allowed_terms = list(current_allowed_terms)
                rescue_targets = _clamp_rescue_targets_by_allowed_terms(
                    rescue_targets,
                    allowed_terms=effective_allowed_terms,
                )
                if rescue_targets:
                    if pinned_rescue_fragment_terms:
                        rescue_targets = _dedup_keep_order(
                            list(pinned_rescue_fragment_terms) + list(rescue_targets)
                        )
                    novel_rescue_targets: list[str] = []
                    for target in rescue_targets:
                        signature = _rescue_target_signature(state, target)
                        if signature and signature not in rescue_recent_signatures:
                            novel_rescue_targets.append(target)
                    if novel_rescue_targets:
                        rescue_targets = novel_rescue_targets
                    elif effective_allowed_terms:
                        rescue_targets = _rescue_allowed_term_frontier(
                            state,
                            allowed_terms=effective_allowed_terms,
                            recent_signatures=rescue_recent_signatures,
                        )
                elif effective_allowed_terms:
                    rescue_targets = _rescue_allowed_term_frontier(
                        state,
                        allowed_terms=effective_allowed_terms,
                        recent_signatures=rescue_recent_signatures,
                    )
                if effective_allowed_terms:
                    terms = _deterministic_rotating_term_subset(
                        effective_allowed_terms,
                        sequence=sequence,
                        keep_head=rescue_rotation_keep_head_terms,
                        rotate_width=rescue_rotation_width_terms,
                    ) or list(effective_allowed_terms)
                if rescue_targets:
                    rescue_targets = _deterministic_rotating_rescue_target_subset(
                        state,
                        rescue_targets,
                        sequence=sequence,
                        keep_head=rescue_rotation_keep_head_targets,
                        rotate_width=rescue_rotation_width_targets,
                    ) or list(rescue_targets)
                elif effective_allowed_terms:
                    rescue_targets = _deterministic_rotating_term_subset(
                        effective_allowed_terms,
                        sequence=sequence,
                        keep_head=rescue_rotation_keep_head_targets,
                        rotate_width=rescue_rotation_width_targets,
                    ) or list(effective_allowed_terms)
                rescue_plan_signature = _rescue_plan_signature(
                    terms=terms,
                    rescue_targets=rescue_targets,
                )
                rescue_plan_is_new = bool(rescue_plan_signature) and rescue_plan_signature not in rescue_recent_plan_signatures
                if rescue_resume_carryover_pending:
                    rescue_plan_is_new = False
                pending_rescue_plan_signature = rescue_plan_signature
                pending_rescue_plan_is_new = bool(rescue_plan_is_new)
                row["rescue_plan_signature"] = rescue_plan_signature
                row["rescue_plan_is_new"] = bool(rescue_plan_is_new)
                if rescue_plan_is_new:
                    rescue_recent_plan_signatures.append(rescue_plan_signature)
                rescue_recent_plan_signatures = rescue_recent_plan_signatures[-rescue_recent_window:]
            proposal_allowed_terms = _dedup_keep_order(list(current_allowed_terms))
            proposal_request_terms = _dedup_keep_order(list(terms))
            row["current_allowed_terms"] = list(current_allowed_terms)
            row["proposal_support_terms"] = list(proposal_support_terms)
            row["proposal_allowed_terms"] = list(proposal_allowed_terms)
            if str(args.memo_provider_mode) == "template":
                emit = _write_memos_for_cycle(
                    run_id=run_id,
                    run_dir=run_dir,
                    sequence=sequence,
                    memo_drop_dir=memo_drop_dir,
                    missing_roles=missing_roles,
                    preset=str(args.preset),
                    prefill_depth=int(args.memo_prefill_depth),
                    strict_gate=bool(args.strict_local_gate_check),
                    concept_target_terms=concept_target_terms,
                    priority_terms=priority_terms,
                    priority_negative_classes=priority_negative_classes,
                    priority_claims=priority_claims,
                    focus_term_mode=current_focus_term_mode,
                    forced_terms=proposal_request_terms or None,
                    support_terms=proposal_support_terms or None,
                )
                row["memo_emit"] = emit
                if current_phase == "rescue" and rescue_targets:
                    for target in rescue_targets:
                        signature = _rescue_target_signature(state, target)
                        if signature and signature not in rescue_recent_signatures:
                            rescue_recent_signatures.append(signature)
                    rescue_recent_signatures = rescue_recent_signatures[-rescue_recent_window:]
            else:
                request_paths: list[str] = []
                ingest_rows: list[dict] = []
                provider_exec_rows: list[dict] = []
                prepack_rows: list[dict] = []
                for offset in range(max(1, int(args.memo_prefill_depth))):
                    seq_i = int(sequence) + offset
                    req_roles = missing_roles if offset == 0 else _required_roles_for_preset(str(args.preset))
                    existing_response = _latest_exchange_response(run_dir=run_dir, sequence=seq_i)
                    if existing_response is not None:
                        ingest = _ingest_exchange_response(
                            response_json=existing_response,
                            run_id=run_id,
                            sequence=seq_i,
                            memo_drop_dir=memo_drop_dir,
                            strict_gate=bool(args.strict_local_gate_check),
                            allowed_terms=proposal_allowed_terms,
                        )
                        ingest["sequence"] = seq_i
                        ingest["response_json"] = str(existing_response)
                        ingest_rows.append(ingest)
                        if bool(args.external_response_prepack):
                            prepack = _run_external_response_prepack(
                                response_json=existing_response,
                                run_id=run_id,
                                sequence=seq_i,
                                runs_root=runs_root,
                                debate_mode=cycle_debate_mode,
                                goal_selection=str(args.goal_selection),
                                graveyard_fill_policy=str(campaign_fill_policy),
                                graveyard_library_terms=str(library_terms_csv),
                                allowed_terms=",".join(proposal_allowed_terms) if proposal_allowed_terms else "",
                                forbid_rescue_in_graveyard_first=bool(campaign_forbid_rescue),
                                max_terms=int(pack_selector_max_terms),
                            )
                            prepack["sequence"] = seq_i
                            prepack["reused_existing_response"] = True
                            prepack_rows.append(prepack)
                        continue
                    req = _emit_exchange_request(
                        run_id=run_id,
                        sequence=seq_i,
                        run_dir=run_dir,
                        preset=str(args.preset),
                        required_roles=req_roles,
                        prompt_paths=[str(p) for p in (cycle.get("prompt_paths", []) or []) if str(p).strip()],
                        terms=proposal_request_terms,
                        support_terms=proposal_support_terms,
                        rescue_targets=rescue_targets,
                        priority_negative_classes=priority_negative_classes,
                        priority_claims=priority_claims,
                        focus_term_mode=current_focus_term_mode,
                        a1_brain_context=a1_brain_context,
                        allowed_terms=proposal_allowed_terms,
                    )
                    request_paths.append(str(req))
                    response_path = req.with_name(req.name.replace("REQUEST", "RESPONSE"))
                    if provider_script:
                        cmd = [
                            "python3",
                            str(Path(provider_script).expanduser().resolve()),
                            "--request-json",
                            str(req),
                            "--response-json",
                            str(response_path),
                        ]
                        try:
                            proc = subprocess.run(
                                cmd,
                                cwd=str(REPO),
                                check=False,
                                capture_output=True,
                                text=True,
                                timeout=max(1, int(args.provider_timeout_sec)),
                            )
                            provider_exec_rows.append(
                                {
                                    "sequence": seq_i,
                                    "code": int(proc.returncode),
                                    "stdout": (proc.stdout or "").strip()[-400:],
                                    "stderr": (proc.stderr or "").strip()[-400:],
                                }
                            )
                        except subprocess.TimeoutExpired:
                            provider_exec_rows.append(
                                {
                                    "sequence": seq_i,
                                    "code": -1,
                                    "stdout": "",
                                    "stderr": f"provider_timeout_after_{int(args.provider_timeout_sec)}s",
                                }
                            )
                    ingest = _ingest_exchange_response(
                        response_json=response_path,
                        run_id=run_id,
                        sequence=seq_i,
                        memo_drop_dir=memo_drop_dir,
                        strict_gate=bool(args.strict_local_gate_check),
                        allowed_terms=proposal_allowed_terms,
                    )
                    ingest["sequence"] = seq_i
                    ingest_rows.append(ingest)
                    if bool(args.external_response_prepack):
                        prepack = _run_external_response_prepack(
                            response_json=response_path,
                            run_id=run_id,
                            sequence=seq_i,
                            runs_root=runs_root,
                            debate_mode=cycle_debate_mode,
                            goal_selection=str(args.goal_selection),
                            graveyard_fill_policy=str(campaign_fill_policy),
                            graveyard_library_terms=str(library_terms_csv),
                            allowed_terms=",".join(proposal_allowed_terms) if proposal_allowed_terms else "",
                            forbid_rescue_in_graveyard_first=bool(campaign_forbid_rescue),
                            max_terms=int(pack_selector_max_terms),
                        )
                        prepack["sequence"] = seq_i
                        prepack_rows.append(prepack)
                if current_phase == "rescue" and rescue_targets:
                    for target in rescue_targets:
                        signature = _rescue_target_signature(state, target)
                        if signature and signature not in rescue_recent_signatures:
                            rescue_recent_signatures.append(signature)
                    rescue_recent_signatures = rescue_recent_signatures[-rescue_recent_window:]
                row["exchange_request_paths"] = request_paths
                row["provider_exec_rows"] = provider_exec_rows
                row["exchange_ingest_rows"] = ingest_rows
                row["exchange_prepack_rows"] = prepack_rows
        else:
            emitted_row = _annotate_first_failure_info(row)
            timeline.append(emitted_row if bool(args.verbose_timeline) else _compact_timeline_row(emitted_row))
            break
        emitted_row = _annotate_first_failure_info(row)
        timeline.append(emitted_row if bool(args.verbose_timeline) else _compact_timeline_row(emitted_row))

    state = _read_json(run_dir / "state.json")
    counts = _state_counts(run_dir)
    audit_phase = str(args.post_run_audit_phase)
    if audit_phase == "auto":
        audit_phase = "graveyard_fill" if current_phase in {"graveyard_seed", "path_build"} else "mixed"
    post_run_audits: dict = {"enabled": bool(args.post_run_audits), "phase": str(audit_phase)}
    if bool(args.post_run_audits) and run_dir.exists():
        post_run_audits["operational_integrity"] = _run_audit_cmd(
            [
                "python3",
                str(OP_AUDIT),
                "--run-dir",
                str(run_dir),
                "--phase",
                str(audit_phase),
            ],
            cwd=REPO,
        )
        post_run_audits["semantic_and_math_substance"] = _run_audit_cmd(
            [
                "python3",
                str(SEM_AUDIT),
                "--run-dir",
                str(run_dir),
                "--phase",
                str(audit_phase),
                "--recent-semantic-rows",
                str(0 if str(audit_phase) == "graveyard_fill" else max(0, int(args.post_run_semantic_recent_rows))),
            ],
            cwd=REPO,
        )
    final = {
        "schema": "A1_EXTERNAL_MEMO_BATCH_DRIVER_REPORT_v1",
        "run_id": run_id,
        "memo_provider_mode": str(args.memo_provider_mode),
        "provider_script": str(args.provider_script),
        "provider_is_stub": bool(provider_is_stub),
        "process_mode": process_mode,
        "concept_target_terms": list(concept_target_terms),
        "focus_term_mode": str(focus_term_mode),
        "graveyard_library_mode": str(args.graveyard_library_mode),
        "graveyard_library_terms": sorted(library_term_set),
        "graveyard_library_coverage": {
            "overlap": int(len(_graveyard_term_set(state) & library_term_set)) if library_term_set else 0,
            "total": int(len(library_term_set)),
            "coverage": (
                float(len(_graveyard_term_set(state) & library_term_set)) / float(len(library_term_set))
                if library_term_set
                else 1.0
            ),
        },
        "a1_brain_context": {
            "sources": list(a1_brain_context.get("sources", [])),
            "excerpt_sha256": str(a1_brain_context.get("excerpt_sha256", "")),
            "excerpt_chars": len(str(a1_brain_context.get("excerpt", ""))),
        },
        "executed_cycles": executed,
        "executed_cycles_total": executed_baseline + executed,
        "wait_cycles": waits,
        "wait_cycles_total": wait_baseline + waits,
        "target_executed_cycles": int(args.target_executed_cycles),
        "goal_reached": bool(goal_reached),
        "post_run_audits": post_run_audits,
        "goal_thresholds": {
            "goal_min_canonical_terms": int(args.goal_min_canonical_terms),
            "goal_min_graveyard_count": int(args.goal_min_graveyard_count),
            "goal_min_sim_registry_count": int(args.goal_min_sim_registry_count),
            "min_executed_cycles_before_goal": int(args.min_executed_cycles_before_goal),
        },
        "last_unique_structural": int(last_unique_structural),
        "timeline": timeline,
        "state_counts": counts,
    }
    stable_report_path = run_dir / "reports" / "a1_external_memo_batch_driver_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(final, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if stable_report_path != report_path:
        stable_report_path.parent.mkdir(parents=True, exist_ok=True)
        stable_report_path.write_text(json.dumps(final, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "schema": final["schema"],
                "out": str(stable_report_path),
                "campaign_report_out": str(report_path),
                "executed_cycles": executed,
                "wait_cycles": waits,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
