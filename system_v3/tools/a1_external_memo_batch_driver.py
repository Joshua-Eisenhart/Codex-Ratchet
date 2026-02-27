#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
import re


REPO = Path(__file__).resolve().parents[2]
SYSTEM_V3 = REPO / "system_v3"
RUNS_DEFAULT = SYSTEM_V3 / "runs"
A2_STATE_DEFAULT = SYSTEM_V3 / "a2_state"
CORE_DOCS = REPO / "core_docs"
CAMPAIGN = SYSTEM_V3 / "tools" / "a1_entropy_engine_campaign_runner.py"
MEMO_GATE = SYSTEM_V3 / "tools" / "a1_memo_quality_gate.py"
OP_AUDIT = SYSTEM_V3 / "tools" / "run_a1_operational_integrity_audit.py"
SEM_AUDIT = SYSTEM_V3 / "tools" / "run_a1_semantic_and_math_substance_gate.py"

TERM_TOKEN_RE = re.compile(r"^[a-z][a-z0-9_]{2,120}$")
DEF_FIELD_PROBE_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+PROBE_TERM\s+(.+)$")
DEF_FIELD_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+(.+)$")
DEF_FIELD_GOAL_TERM_RE = re.compile(r"^DEF_FIELD\s+\S+\s+CORR\s+GOAL_TERM\s+(.+)$")
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


def _load_a1_brain_context(*, max_chars: int = 12000) -> dict:
    """
    Build a compact, deterministic A1 context payload for external memo providers.
    This keeps context explicit and persistent without inflating packet size.
    """
    sources = [
        SYSTEM_V3 / "a2_state" / "MODEL_CONTEXT.md",
        SYSTEM_V3 / "a2_state" / "INTENT_SUMMARY.md",
        CORE_DOCS / "a1_refined_Ratchet Fuel" / "PHYSICS_FUEL_DIGEST_v1.0.md",
        CORE_DOCS / "a1_refined_Ratchet Fuel" / "AXES_MASTER_SPEC_v0.2.md",
    ]
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
    return json.loads(path.read_text(encoding="utf-8"))


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


def _parse_csv_term_set(raw: str) -> set[str]:
    return {t for t in _parse_csv_terms(raw)}


def _csv_from_terms(terms: set[str]) -> str:
    return ",".join(sorted({str(t).strip() for t in terms if str(t).strip()}))


def _compact_timeline_row(row: dict) -> dict:
    out = dict(row)
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
            compact_exec.append(
                {
                    "sequence": int(r.get("sequence", 0) or 0),
                    "code": int(r.get("code", 0) or 0),
                }
            )
        out["provider_exec_rows"] = compact_exec
    if isinstance(out.get("exchange_ingest_rows"), list):
        compact_ingest = []
        for r in out["exchange_ingest_rows"]:
            if not isinstance(r, dict):
                continue
            compact_ingest.append(
                {
                    "sequence": int(r.get("sequence", 0) or 0),
                    "status": str(r.get("status", "")),
                    "written_count": int(r.get("written_count", 0)),
                    "rejected_count": int(r.get("rejected_count", 0)),
                }
            )
        out["exchange_ingest_rows"] = compact_ingest
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
    return goal_term or term_field or probe_term


def _collect_rescue_targets(state: dict, *, limit: int = 24) -> list[str]:
    out: list[str] = []
    for row in reversed(state.get("kill_log", []) if isinstance(state, dict) else []):
        if not isinstance(row, dict):
            continue
        if str(row.get("tag", "")).strip() != "KILL_SIGNAL":
            continue
        sid = str(row.get("id", "")).strip()
        if sid:
            out.append(sid)
            if len(out) >= int(limit):
                break
    out.reverse()
    return out


def _collect_focus_terms(state: dict, rescue_targets: list[str]) -> list[str]:
    out = set(BASE_TERMS)
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
    for t in _extract_doc_terms(limit=300):
        out.add(t)
    return sorted(out)


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
        CORE_DOCS / "a1_refined_Ratchet Fuel",
        SYSTEM_V3 / "a2_state" / "INTENT_SUMMARY.md",
        SYSTEM_V3 / "a2_state" / "MODEL_CONTEXT.md",
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


def _build_memo(*, run_id: str, sequence: int, role: str, proposed_terms: list[str], rescue_targets: list[str]) -> dict:
    role_u = str(role).strip().upper()
    return {
        "schema": "A1_LAWYER_MEMO_v1",
        "run_id": str(run_id),
        "sequence": int(sequence),
        "role": role_u,
        "claims": list(ROLE_CLAIMS.get(role_u, ["Provide explicit nonclassical claims."])),
        "risks": list(ROLE_RISKS.get(role_u, ["Do not smooth adversarial boundaries."])),
        "graveyard_rescue_targets": list(rescue_targets),
        "proposed_negative_classes": list(ROLE_NEG_CLASSES.get(role_u, ["COMMUTATIVE_ASSUMPTION", "CLASSICAL_TIME"])),
        "proposed_terms": list(proposed_terms),
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
) -> dict:
    state = _read_json(run_dir / "state.json")
    rescue_targets = _collect_rescue_targets(state)
    terms = _collect_focus_terms(state, rescue_targets)
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
                rescue_targets=rescue_targets,
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
    rescue_targets: list[str],
    a1_brain_context: dict | None = None,
) -> Path:
    root = run_dir / "a1_sandbox" / "external_memo_exchange"
    req_dir = root / "requests"
    req_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    obj = {
        "schema": "A1_EXTERNAL_MEMO_REQUEST_v1",
        "run_id": str(run_id),
        "sequence": int(sequence),
        "preset": str(preset),
        "required_roles": sorted({str(x).strip().upper() for x in required_roles if str(x).strip()}),
        "prompt_paths": list(prompt_paths),
        "term_candidates": list(terms),
        "graveyard_rescue_targets": list(rescue_targets),
        "a1_brain_context": dict(a1_brain_context or {}),
        "ts_utc": ts,
    }
    out = req_dir / f"{int(sequence):06d}__A1_EXTERNAL_MEMO_REQUEST__{ts}.json"
    out.write_text(json.dumps(obj, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return out


def _ingest_exchange_response(
    *,
    response_json: Path,
    run_id: str,
    sequence: int,
    memo_drop_dir: Path,
    strict_gate: bool,
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
    for idx, row in enumerate(memos, start=1):
        if not isinstance(row, dict):
            rejected.append({"index": idx, "reason": "memo_not_object"})
            continue
        memo = dict(row)
        memo["schema"] = "A1_LAWYER_MEMO_v1"
        memo["run_id"] = str(memo.get("run_id", run_id))
        memo["sequence"] = int(memo.get("sequence", sequence) or sequence)
        memo["role"] = str(memo.get("role", "")).strip().upper()
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


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="External memo-batch driver for A1 sandbox (non-autofill path).")
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--clean", action="store_true")
    ap.add_argument("--runs-root", default=str(RUNS_DEFAULT))
    ap.add_argument("--a2-state-dir", default=str(A2_STATE_DEFAULT))
    ap.add_argument("--preset", choices=["graveyard13", "entropy_lenses7", "lawyer4"], default="graveyard13")
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

    provider_script = str(args.provider_script).strip()
    provider_is_stub = bool(provider_script) and Path(provider_script).name == "a1_external_memo_provider_stub.py"
    if bool(args.forbid_provider_stub) and provider_is_stub:
        raise SystemExit("provider_script points to stub provider; use a real external provider script")

    executed = 0
    waits = 0
    clean_flag = bool(args.clean)
    timeline: list[dict] = []
    a1_brain_context = _load_a1_brain_context(max_chars=int(args.a1_brain_context_max_chars))
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
    process_mode = str(args.process_mode)
    path_build_cycles_executed = 0
    current_phase = "legacy"
    last_unique_structural = -1
    path_build_novelty_stall = 0

    goal_reached = False
    while executed < int(args.target_executed_cycles) and waits < int(args.max_wait_cycles):
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
        if current_phase == "path_build":
            if unique_structural_now > int(last_unique_structural):
                path_build_novelty_stall = 0
            else:
                path_build_novelty_stall += 1
        else:
            path_build_novelty_stall = 0
        last_unique_structural = unique_structural_now

        concept_in_graveyard = True
        if concept_target_terms:
            concept_in_graveyard = all(t in graveyard_terms_now for t in concept_target_terms)

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
            seed_ready = concept_in_graveyard and (not force_fill_by_fuel) and (not force_fill_by_library)
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
                cycle_debate_mode = "graveyard_first" if executed < int(args.fill_executed_cycles) else "graveyard_recovery"
                if force_fill_by_dominance or force_fill_by_fuel or force_fill_by_library:
                    cycle_debate_mode = "graveyard_first"
                cycle_debate_strategy = "fixed"
            else:
                cycle_debate_mode = str(args.debate_mode)
                cycle_debate_strategy = "fixed"
            campaign_fill_policy = str(args.campaign_graveyard_fill_policy)
            campaign_forbid_rescue = bool(args.campaign_forbid_rescue_during_graveyard_fill)
            pack_selector_max_terms = 0

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
        row = {
            "status": status,
            "sequence": int(cycle.get("sequence", 0) or 0),
            "run_stop_reason": result.get("stop_reason", ""),
            "cycle_debate_mode": cycle_debate_mode,
            "process_phase": current_phase,
            "fill_status": {
                "force_fill_by_dominance": bool(force_fill_by_dominance),
                "force_fill_by_fuel": bool(force_fill_by_fuel),
                "force_fill_by_library": bool(force_fill_by_library),
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
                "kill_token_diversity": int(kill_diversity_now),
                "pack_selector_max_terms": int(pack_selector_max_terms),
            },
        }
        if status == "STEP_EXECUTED":
            executed += 1
            if current_phase == "path_build":
                path_build_cycles_executed += 1
            counts = _state_counts(run_dir)
            row["state_counts"] = counts
            allow_goal_stop = True
            if process_mode == "concept_path_rescue":
                allow_goal_stop = current_phase == "rescue"
            if allow_goal_stop and executed >= int(args.min_executed_cycles_before_goal):
                if (
                    int(counts.get("canonical_term_count", 0)) >= int(args.goal_min_canonical_terms)
                    and int(counts.get("graveyard_count", 0)) >= int(args.goal_min_graveyard_count)
                    and int(counts.get("sim_registry_count", 0)) >= int(args.goal_min_sim_registry_count)
                ):
                    goal_reached = True
                    timeline.append(row)
                    break
        elif status == "WAITING_FOR_MEMOS":
            waits += 1
            memo_drop_dir = Path(str(cycle.get("memo_drop_dir", "")).strip())
            sequence = int(cycle.get("sequence", 0) or 0)
            missing_roles = [str(x).strip() for x in (cycle.get("missing_roles", []) or []) if str(x).strip()]
            state = _read_json(run_dir / "state.json")
            rescue_targets = _collect_rescue_targets(state)
            terms = _collect_focus_terms(state, rescue_targets)
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
                )
                row["memo_emit"] = emit
            else:
                request_paths: list[str] = []
                ingest_rows: list[dict] = []
                provider_exec_rows: list[dict] = []
                for offset in range(max(1, int(args.memo_prefill_depth))):
                    seq_i = int(sequence) + offset
                    req_roles = missing_roles if offset == 0 else _required_roles_for_preset(str(args.preset))
                    req = _emit_exchange_request(
                        run_id=run_id,
                        sequence=seq_i,
                        run_dir=run_dir,
                        preset=str(args.preset),
                        required_roles=req_roles,
                        prompt_paths=[str(p) for p in (cycle.get("prompt_paths", []) or []) if str(p).strip()],
                        terms=terms,
                        rescue_targets=rescue_targets,
                        a1_brain_context=a1_brain_context,
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
                    )
                    ingest["sequence"] = seq_i
                    ingest_rows.append(ingest)
                row["exchange_request_paths"] = request_paths
                row["provider_exec_rows"] = provider_exec_rows
                row["exchange_ingest_rows"] = ingest_rows
        else:
            timeline.append(row if bool(args.verbose_timeline) else _compact_timeline_row(row))
            break
        timeline.append(row if bool(args.verbose_timeline) else _compact_timeline_row(row))

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
        "wait_cycles": waits,
        "target_executed_cycles": int(args.target_executed_cycles),
        "goal_reached": bool(goal_reached),
        "post_run_audits": post_run_audits,
        "goal_thresholds": {
            "goal_min_canonical_terms": int(args.goal_min_canonical_terms),
            "goal_min_graveyard_count": int(args.goal_min_graveyard_count),
            "goal_min_sim_registry_count": int(args.goal_min_sim_registry_count),
            "min_executed_cycles_before_goal": int(args.min_executed_cycles_before_goal),
        },
        "timeline": timeline,
        "state_counts": counts,
    }
    out = run_dir / "reports" / "a1_external_memo_batch_driver_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(final, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    print(json.dumps({"schema": final["schema"], "out": str(out), "executed_cycles": executed, "wait_cycles": waits}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(list(__import__("os").sys.argv[1:])))
