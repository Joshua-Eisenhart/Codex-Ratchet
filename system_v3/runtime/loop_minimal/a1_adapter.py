import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import hashlib
import json
import re
import subprocess
from copy import deepcopy
from pathlib import Path


_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_FENCED_JSON_RE = re.compile(r"```json\s*(\{[\s\S]*?\})\s*```", re.IGNORECASE)


_REQUIRED_ROOT = {
    "strategy_id",
    "version",
    "input_doc_refs",
    "intent",
    "candidate_families",
    "repair_rules",
    "stop_conditions",
    "budget",
}

_REQUIRED_FAMILY = {
    "family_id",
    "purpose",
    "required_terms",
    "forbidden_terms",
    "candidate_templates",
    "expected_b_fences",
    "sim_hooks",
}

_REQUIRED_TEMPLATE = {
    "spec_id",
    "expected_kind",
    "probe_id",
    "probe_kind",
    "probe_token",
    "requires_probe",
    "evidence_token",
}

_REQUIRED_SIM_HOOK = {"sim_spec_id", "sim_id"}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_hex64(value: str) -> bool:
    return bool(_HEX64_RE.match(value or ""))


def _merge_dict(base: dict, override: dict) -> dict:
    out = deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge_dict(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def _coerce_strategy(candidate: dict, base_strategy: dict, step: int) -> dict:
    out = deepcopy(base_strategy)
    if not isinstance(candidate, dict):
        candidate = {}

    if isinstance(candidate.get("strategy_id"), str) and candidate["strategy_id"].strip():
        out["strategy_id"] = candidate["strategy_id"].strip()
    if isinstance(candidate.get("intent"), str) and candidate["intent"].strip():
        out["intent"] = candidate["intent"].strip()
    if isinstance(candidate.get("rosetta_map"), dict):
        out["rosetta_map"] = _merge_dict(out.get("rosetta_map", {}), candidate["rosetta_map"])
    if isinstance(candidate.get("repair_rules"), dict):
        out["repair_rules"] = _merge_dict(out.get("repair_rules", {}), candidate["repair_rules"])
    if isinstance(candidate.get("stop_conditions"), dict):
        out["stop_conditions"] = _merge_dict(out.get("stop_conditions", {}), candidate["stop_conditions"])
    if isinstance(candidate.get("budget"), dict):
        out["budget"] = _merge_dict(out.get("budget", {}), candidate["budget"])

    refs = []
    for ref in candidate.get("input_doc_refs", []) if isinstance(candidate.get("input_doc_refs"), list) else []:
        if not isinstance(ref, dict):
            continue
        path = ref.get("path")
        sha = ref.get("sha256")
        if isinstance(path, str) and isinstance(sha, str) and _is_hex64(sha):
            refs.append({"path": path, "sha256": sha.lower()})
    if refs:
        out["input_doc_refs"] = refs

    base_families = base_strategy.get("candidate_families", [])
    base_family = deepcopy(base_families[0]) if base_families else {}
    base_templates = base_family.get("candidate_templates", [])
    base_template = deepcopy(base_templates[0]) if base_templates else {}
    base_hooks = base_family.get("sim_hooks", [])
    base_hook = deepcopy(base_hooks[0]) if base_hooks else {"sim_spec_id": "S_BIND_MS_A_FULL16X4", "sim_id": "S_BIND_MS_A_FULL16X4"}

    families_out = []
    raw_families = candidate.get("candidate_families", [])
    if isinstance(raw_families, list):
        for fam in raw_families:
            if not isinstance(fam, dict):
                continue
            fam_out = deepcopy(base_family)
            for key in ["family_id", "purpose"]:
                if isinstance(fam.get(key), str) and fam[key].strip():
                    fam_out[key] = fam[key].strip()
            for key in ["required_terms", "forbidden_terms", "expected_b_fences"]:
                if isinstance(fam.get(key), list):
                    fam_out[key] = [str(x) for x in fam[key]]

            hooks_out = []
            if isinstance(fam.get("sim_hooks"), list):
                for hook in fam["sim_hooks"]:
                    if not isinstance(hook, dict):
                        continue
                    h = deepcopy(base_hook)
                    if isinstance(hook.get("sim_spec_id"), str) and hook["sim_spec_id"].strip():
                        h["sim_spec_id"] = hook["sim_spec_id"].strip()
                    if isinstance(hook.get("sim_id"), str) and hook["sim_id"].strip():
                        h["sim_id"] = hook["sim_id"].strip()
                    hooks_out.append(h)
            fam_out["sim_hooks"] = hooks_out or fam_out.get("sim_hooks") or [deepcopy(base_hook)]

            templates_out = []
            if isinstance(fam.get("candidate_templates"), list):
                for tpl in fam["candidate_templates"]:
                    if not isinstance(tpl, dict):
                        continue
                    t = deepcopy(base_template)
                    for key in ["spec_id", "expected_kind", "probe_id", "probe_kind", "probe_token", "requires_probe", "evidence_token", "assert_evidence_token"]:
                        if isinstance(tpl.get(key), str) and tpl[key].strip():
                            t[key] = tpl[key].strip()
                    if not t.get("requires_probe"):
                        t["requires_probe"] = t.get("probe_id", "")
                    if t.get("probe_id") and not t.get("probe_token"):
                        t["probe_token"] = f"PT_{t['probe_id']}"
                    if t.get("evidence_token") and not t.get("assert_evidence_token"):
                        t["assert_evidence_token"] = t["evidence_token"]
                    if isinstance(t.get("spec_id"), str) and t["spec_id"] and f"_S{step:04d}" not in t["spec_id"]:
                        t["spec_id"] = f"{t['spec_id']}_S{step:04d}"
                    if isinstance(t.get("probe_id"), str) and t["probe_id"] and f"_S{step:04d}" not in t["probe_id"]:
                        t["probe_id"] = f"{t['probe_id']}_S{step:04d}"
                        t["requires_probe"] = t["probe_id"]
                        t["probe_token"] = f"PT_{t['probe_id']}"
                    templates_out.append(t)
            fam_out["candidate_templates"] = templates_out or fam_out.get("candidate_templates") or [deepcopy(base_template)]
            families_out.append(fam_out)

    out["candidate_families"] = families_out or out.get("candidate_families") or [deepcopy(base_family)]
    out["version"] = "A1_STRATEGY_v1"
    return out


def validate_strategy_schema(strategy: dict) -> list[str]:
    errors: list[str] = []

    missing = sorted(_REQUIRED_ROOT - set(strategy.keys()))
    for key in missing:
        errors.append(f"missing root field: {key}")

    if strategy.get("version") != "A1_STRATEGY_v1":
        errors.append("version must be A1_STRATEGY_v1")

    refs = strategy.get("input_doc_refs", [])
    if not isinstance(refs, list):
        errors.append("input_doc_refs must be array")
    else:
        for i, ref in enumerate(refs):
            if not isinstance(ref, dict):
                errors.append(f"input_doc_refs[{i}] must be object")
                continue
            if "path" not in ref or "sha256" not in ref:
                errors.append(f"input_doc_refs[{i}] missing path/sha256")
                continue
            if not isinstance(ref["path"], str) or not isinstance(ref["sha256"], str):
                errors.append(f"input_doc_refs[{i}] path/sha256 must be string")
            elif not _HEX64_RE.match(ref["sha256"]):
                errors.append(f"input_doc_refs[{i}] sha256 invalid")

    families = strategy.get("candidate_families", [])
    if not isinstance(families, list) or not families:
        errors.append("candidate_families must be non-empty array")
    else:
        for i, family in enumerate(families):
            if not isinstance(family, dict):
                errors.append(f"candidate_families[{i}] must be object")
                continue
            missing_family = sorted(_REQUIRED_FAMILY - set(family.keys()))
            for key in missing_family:
                errors.append(f"candidate_families[{i}] missing field: {key}")

            templates = family.get("candidate_templates", [])
            if not isinstance(templates, list) or not templates:
                errors.append(f"candidate_families[{i}] candidate_templates must be non-empty array")
            else:
                for j, template in enumerate(templates):
                    if not isinstance(template, dict):
                        errors.append(f"candidate_templates[{i}][{j}] must be object")
                        continue
                    missing_t = sorted(_REQUIRED_TEMPLATE - set(template.keys()))
                    for key in missing_t:
                        errors.append(f"candidate_templates[{i}][{j}] missing field: {key}")
                    if template.get("expected_kind") != "SIM_SPEC":
                        errors.append(f"candidate_templates[{i}][{j}] expected_kind must be SIM_SPEC")

            hooks = family.get("sim_hooks", [])
            if not isinstance(hooks, list):
                errors.append(f"candidate_families[{i}] sim_hooks must be array")
            else:
                for j, hook in enumerate(hooks):
                    if not isinstance(hook, dict):
                        errors.append(f"sim_hooks[{i}][{j}] must be object")
                        continue
                    missing_h = sorted(_REQUIRED_SIM_HOOK - set(hook.keys()))
                    for key in missing_h:
                        errors.append(f"sim_hooks[{i}][{j}] missing field: {key}")

    repair_rules = strategy.get("repair_rules", {})
    if not isinstance(repair_rules, dict):
        errors.append("repair_rules must be object")

    stop_conditions = strategy.get("stop_conditions", {})
    for key in ["max_repair_attempts_per_step", "repeated_noop_limit", "repeated_schema_fail_limit"]:
        if key not in stop_conditions:
            errors.append(f"stop_conditions missing field: {key}")

    budget = strategy.get("budget", {})
    for key in [
        "max_new_terms_per_batch",
        "max_new_specs_per_batch",
        "max_graveyard_growth_per_n_cycles",
        "n_cycles",
        "probe_pressure_ratio",
    ]:
        if key not in budget:
            errors.append(f"budget missing field: {key}")

    return errors


def load_strategy_artifact(path: Path) -> dict:
    raw = path.read_bytes()
    strategy = json.loads(raw.decode("utf-8"))
    errors = validate_strategy_schema(strategy)
    if errors:
        raise ValueError("A1_STRATEGY schema invalid: " + "; ".join(errors))
    return {
        "path": str(path),
        "sha256": _sha256_bytes(raw),
        "strategy": strategy,
    }


def parse_strategy_output_text(raw_text: str) -> dict:
    text = raw_text.strip()
    if not text:
        raise ValueError("empty A1 output")

    # Try direct JSON object first.
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Try fenced json blocks.
    m = _FENCED_JSON_RE.search(text)
    if m:
        parsed = json.loads(m.group(1))
        if isinstance(parsed, dict):
            return parsed

    # Try first balanced object boundary fallback.
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != "{":
            continue
        try:
            parsed, _end = decoder.raw_decode(text[i:])
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            continue

    # Final fallback: widest braces.
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        parsed = json.loads(text[start : end + 1])
        if isinstance(parsed, dict):
            return parsed

    raise ValueError("no parseable JSON object in A1 output")


def _build_ollama_prompt(base_strategy: dict, step: int, canonical_state_snapshot_hash: str, last_tags: list[str]) -> str:
    return "\n".join(
        [
            "You are generating one A1_STRATEGY_v1 JSON object.",
            "Output exactly one JSON object only. No prose. No markdown. No comments.",
            "Keep schema valid for required fields and nested fields.",
            "Required root keys:",
            "strategy_id, version, input_doc_refs, intent, candidate_families, repair_rules, stop_conditions, budget",
            "Hard rules:",
            "- version must be A1_STRATEGY_v1",
            "- expected_kind must stay SIM_SPEC",
            "- Do not invent unsupported SPEC_KIND",
            "- Keep repair_rules, stop_conditions, and budget present",
            "- Keep input_doc_refs path+sha256 format valid",
            f"- At least one candidate template id must include suffix _S{step:04d}",
            f"Runtime context: step={step}",
            f"Runtime context: canonical_state_snapshot_hash={canonical_state_snapshot_hash}",
            f"Runtime context: last_reject_tags={','.join(sorted(set(last_tags)))}",
            "You may vary candidate_templates/spec_id/probe_id/probe_kind/purpose to explore alternatives,",
            "but remain bootpack-safe and schema-valid.",
            "BASE_STRATEGY_JSON:",
            json.dumps(base_strategy, sort_keys=True, separators=(",", ":")),
        ]
    )


def generate_strategy_with_ollama(
    model: str,
    base_strategy: dict,
    step: int,
    canonical_state_snapshot_hash: str,
    last_tags: list[str],
    timeout_sec: int = 90,
    max_attempts: int = 3,
) -> dict:
    prompt = _build_ollama_prompt(base_strategy, step, canonical_state_snapshot_hash, last_tags)
    attempts: list[dict] = []
    for attempt in range(1, max_attempts + 1):
        proc = subprocess.run(
            ["ollama", "run", model, "--format", "json", "--hidethinking"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        raw = (proc.stdout or "").strip()
        if proc.returncode != 0:
            attempts.append({"attempt": attempt, "status": "OLLAMA_ERROR", "stderr": (proc.stderr or "").strip()[:500]})
            continue
        try:
            strategy = _coerce_strategy(parse_strategy_output_text(raw), base_strategy, step)
            errors = validate_strategy_schema(strategy)
            if errors:
                attempts.append({"attempt": attempt, "status": "SCHEMA_FAIL", "errors": errors[:10]})
                continue
            return {
                "strategy": strategy,
                "raw_output": raw,
                "model": model,
                "attempts": attempts + [{"attempt": attempt, "status": "OK"}],
            }
        except Exception as exc:
            attempts.append({"attempt": attempt, "status": "PARSE_FAIL", "error": str(exc)[:500]})
            continue

    raise ValueError("A1 ollama generation failed: " + json.dumps(attempts, sort_keys=True))
