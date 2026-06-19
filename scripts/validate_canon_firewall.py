#!/usr/bin/env python3
"""Canon-firewall audit for Codex-Ratchet sim artifacts.

CEILING: this is a mechanical promotion/authority firewall, not a proof of
mathematical correctness. It catches surfaces where LLM-authored prose or
Tier-2/dynamic fields promote scratch results into canon/admission/evidence.

It is intentionally stricter than prose taste: tiny status and authority leaks
are violations. Legitimate failures failing is the point.

Checks implemented:
- Prose/status gate: promotion words in JSON string values or Markdown lines
  are rejected unless fenced by scratch/not-admitted/ceiling language.
- Tier-2 dynamic-field gate: keys such as *_earned, *_independent,
  discriminator.verdict, engine_consensus.independent, and load_bearing=true are
  treated as claims and must carry local audit/control evidence.
- Count-tautology/load-bearing smell gate: load_bearing records based on counts
  or expected values without erased/negative/control/source evidence are flagged.
- Corpus authority gate: /tmp references are not authority unless explicitly
  marked non-authoritative/temporary.
- Engine-independence gate: independent=true without lane_evidence showing
  independent_recompute is flagged.

Usage:
    python3 scripts/validate_canon_firewall.py <repo | sims-root | sim-dir | file>
    python3 scripts/validate_canon_firewall.py --selftest

Output: JSON {"ok": bool, "summary": ..., "violations": [...]}.
Exit code: 0 if clean, 1 if violations, 2 on usage/input error.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PROMOTION_RE = re.compile(
    r"\b("
    r"canon(?:ical|ic|ize|ise|ized|ised|icity)?|"
    r"admit(?:ted|s|ting)?|admission|admissible|accepted|"
    r"promot(?:e|ed|ion|able|ion_allowed)|"
    r"formal[_ -]?admission|"
    r"prove(?:n|d)|proof|verified|validated|ratified|"
    r"earned|survives?|survivor|"
    r"installed?|unlocked"
    r")\b",
    re.IGNORECASE,
)

# A fence must be local and explicit. Generic words like "not" or "scratch"
# cannot launder "not a caveat: canonical admitted proof installed".
EXPLICIT_FENCE_RE = re.compile(
    r"("
    r"not[-_ ]?(?:admitted|admissible|accepted|canonical|canon|proven|proof|verified|validated|earned|installed|unlocked)|"
    r"not\s+(?:the|this|that|an?|any)\s+[A-Za-z0-9_ ./-]{0,55}\badmission\b|"
    r"no[-_ ]?(?:formal[-_ ]?admission|admission|promotion|proof|canon)|"
    r"non[-_ ]?admitted|unadmitted|"
    r"promotion_allowed\s*[:=]\s*false|formal_admission_allowed\s*[:=]\s*false|"
    r"claim_ceiling\s*[:=].*(?:scratch|diagnostic|not[-_ ]?admitted)|"
    r"scratch[-_ ]?diagnostic[-_ ]?only|"
    r"(?:disallowed|forbidden|blocked)[-_ ]?claims?"
    r")",
    re.IGNORECASE,
)

PATH_FENCE_RE = re.compile(r"/(?:disallowed|forbidden|blocked)_claims(?:\[|/|$)|/claim_ceiling$", re.IGNORECASE)
MATH_CANONICAL_RE = re.compile(r"\bcanonical[-_ ]?(?:form|forms|tuple|tuples|representative|representation|ordering|basis|target)\b", re.IGNORECASE)

DYNAMIC_KEY_RE = re.compile(
    r"(^|[_.-])(earned|independent|survives?|admitted|canonical|canon|load[_-]?bearing)([_.-]|$)|"
    r"discriminator[_.-]verdict|engine_consensus[_.-]independent|result_language",
    re.IGNORECASE,
)

COUNT_HINT_RE = re.compile(r"count|expected|agreement|max_divergence|divergence|survivor", re.IGNORECASE)
CONTROL_EVIDENCE_RE = re.compile(
    r"erased|negative|control|ablation|counterfactual|source_(?:path|sha|hash)|observable|witness|audit|independent_recompute",
    re.IGNORECASE,
)
TMP_RE = re.compile(r"/(?:private/)?tmp/|\b/tmp/|/var/folders/", re.IGNORECASE)
TMP_FENCE_RE = re.compile(r"non[-_ ]?authoritative|temporary[-_ ]?only|temp[-_ ]?only|cache[-_ ]?only|overlay[-_ ]?only", re.IGNORECASE)

TRUTHY = {True, "true", "True", "TRUE", "yes", "YES", "pass", "PASS", "ok", "OK", "survives", "SURVIVES"}
FALSY = {False, "false", "False", "FALSE", "no", "NO", "0", 0, None, ""}

# These key names are part of the explicit status schema. Their VALUES can still
# be audited; the key text itself must not trip the prose-promotion scanner.
KEY_PROSE_EXEMPT = frozenset(
    {
        "classification",
        "promotion_allowed",
        "formal_admission_allowed",
        "claim_ceiling",
        "evidence_allowed",
        "load_bearing",
        "is_load_bearing",
        "aligned_packages_load_bearing",
    }
)


@dataclass(frozen=True)
class Violation:
    path: str
    kind: str
    token: str
    message: str
    severity: str = "major"

    def as_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "kind": self.kind,
            "token": self.token,
            "message": self.message,
            "severity": self.severity,
        }


def rel(path: Path, root: Path | None = None) -> str:
    try:
        base = root or Path.cwd()
        return str(path.resolve().relative_to(base.resolve()))
    except Exception:
        return str(path)


def is_truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip() in TRUTHY
    if isinstance(value, bool):
        return value is True
    if isinstance(value, (int, float)):
        return value == 1
    return False


def is_positive_claim_value(value: Any) -> bool:
    """Truthiness for dynamic claim fields, stricter than boolean parsing."""
    if isinstance(value, bool):
        return value is True
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        text = value.strip()
        low = text.lower()
        if low in {"", "false", "no", "none", "null", "0", "not_run", "blocked", "rejected", "fail", "failed"}:
            return False
        return bool(PROMOTION_RE.search(text)) or low in {
            "true", "yes", "pass", "passed", "ok", "survives", "survived",
            "accepted", "verified", "validated", "supported", "earned", "admitted", "canonical",
        }
    if isinstance(value, (list, dict)):
        return bool(value)
    return False


def is_falsy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip() in FALSY
    if isinstance(value, (bool, int, float, type(None))):
        return value in FALSY
    return False


def path_join(base: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{base}[{key}]"
    return f"{base}/{key}"


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def local_blob(obj: Any, limit: int = 5000) -> str:
    try:
        text = json.dumps(obj, sort_keys=True, ensure_ascii=False)
    except Exception:
        text = str(obj)
    return text[:limit]


def top_level_promotion_violations(data: Any, path: str) -> list[Violation]:
    """Top-level admission/promotion fields cannot self-authorize."""
    out: list[Violation] = []
    if not isinstance(data, dict):
        return out
    if is_positive_claim_value(data.get("promotion_allowed")):
        out.append(Violation(path_join(path, "promotion_allowed"), "top_level_self_authorization", "promotion_allowed", "promotion_allowed=true requires external admission evidence; it cannot authorize itself", "blocking"))
    if is_positive_claim_value(data.get("formal_admission_allowed")):
        out.append(Violation(path_join(path, "formal_admission_allowed"), "top_level_self_authorization", "formal_admission_allowed", "formal_admission_allowed=true requires external proof/admission evidence; it cannot authorize itself", "blocking"))
    classification = str(data.get("classification", "")).lower()
    if classification in {"admitted", "formal_admission", "canonical", "canon"}:
        out.append(Violation(path_join(path, "classification"), "top_level_self_authorization", "classification", f"classification={classification!r} is a promotion claim requiring external admission evidence", "blocking"))
    return out


def contains_positive_independent_recompute(node: Any) -> bool:
    if isinstance(node, dict):
        for key, value in node.items():
            if str(key).lower() == "independent_recompute" and is_truthy(value):
                return True
            if contains_positive_independent_recompute(value):
                return True
    elif isinstance(node, list):
        return any(contains_positive_independent_recompute(item) for item in node)
    return False


def has_structured_evidence(node: Any) -> bool:
    """Minimal structural evidence, not mere lexical evidence words."""
    if isinstance(node, dict):
        keys = {str(k).lower() for k in node}
        has_source = "source_path" in keys and bool(node.get("source_path")) and any(
            k in keys and bool(node.get(k)) for k in ("source_sha", "source_sha256", "source_hash", "source_digest")
        )
        if has_source:
            return True
        if contains_positive_independent_recompute(node):
            return True
        for key, value in node.items():
            low = str(key).lower()
            if re.search(r"negative|erased|control|ablation|counterfactual|witness", low):
                if isinstance(value, dict):
                    if value.get("ran") is True or value.get("passed") is True or value.get("ok") is True or value.get("verdict") in {"sat", "unsat", "SAT", "UNSAT"}:
                        return True
                elif is_positive_claim_value(value):
                    return True
            if has_structured_evidence(value):
                return True
    elif isinstance(node, list):
        return any(has_structured_evidence(item) for item in node)
    return False


def claim_is_locally_fenced(path: str, text: str, match: re.Match[str]) -> bool:
    if PATH_FENCE_RE.search(path):
        return True
    start = max(0, match.start() - 55)
    end = min(len(text), match.end() + 55)
    window = text[start:end]
    token = match.group(0).lower()
    if token.startswith("canon") and MATH_CANONICAL_RE.search(window) and not re.search(r"admit|promotion|install|unlock|proof|proved|proven", window, re.IGNORECASE):
        return True
    if token.startswith("canon"):
        return bool(re.search(r"not[-_ ]?(?:canonical|canon)|no[-_ ]?canon", window, re.IGNORECASE))
    if token.startswith("admit") or token in {"admission", "admissible", "accepted"}:
        return bool(re.search(r"not[-_ ]?(?:admitted|admissible|accepted)|no[-_ ]?(?:formal[-_ ]?admission|admission)|non[-_ ]?admitted|unadmitted|not\s+(?:the|this|that|an?|any)\s+[A-Za-z0-9_ ./-]{0,55}\badmission\b", window, re.IGNORECASE))
    if token.startswith("promot"):
        return bool(re.search(r"not[-_ ]?promotion|no[-_ ]?promotion|promotion_allowed\s*[:=]\s*false", window, re.IGNORECASE))
    if token.startswith("formal"):
        return bool(re.search(r"no[-_ ]?formal[-_ ]?admission|formal_admission_allowed\s*[:=]\s*false", window, re.IGNORECASE))
    if token.startswith("proof") or token.startswith("prove"):
        return bool(re.search(r"not[-_ ]?(?:proof|proven)|no[-_ ]?proof", window, re.IGNORECASE))
    if token in {"verified", "validated", "ratified"}:
        return bool(re.search(r"not[-_ ]?(?:verified|validated|ratified)", window, re.IGNORECASE))
    if token.startswith("earn") or token.startswith("surviv"):
        return bool(re.search(r"not[-_ ]?(?:earned|survives?|survivor)", window, re.IGNORECASE))
    if token.startswith("install") or token.startswith("unlock"):
        return bool(re.search(r"not[-_ ]?(?:installed?|unlocked)", window, re.IGNORECASE))
    return bool(EXPLICIT_FENCE_RE.search(window))


def prose_violation(path: str, text: str, *, ceiling_allows: bool = False) -> Violation | None:
    for m in PROMOTION_RE.finditer(text):
        if claim_is_locally_fenced(path, text, m):
            continue
        snippet = text.strip().replace("\t", " ")[:180]
        return Violation(
            path=path,
            kind="prose_promotion_leak",
            token=m.group(0),
            message=f"promotion/admission word is not locally fenced by an explicit not-admitted/ceiling phrase: {snippet}",
            severity="blocking",
        )
    return None


def audit_dynamic_key(path: str, key: str, value: Any, parent: Any) -> list[Violation]:
    out: list[Violation] = []
    # Do not let a dynamic parent name taint every descendant. The claim is the
    # key itself (or a precise discriminator/engine_consensus verdict path), not
    # every child under it.
    full_path = f"{path.replace('/', '.')}.{key}" if path else key
    is_dynamic = bool(DYNAMIC_KEY_RE.search(key)) or bool(
        re.search(r"discriminator[_.-]verdict|engine_consensus[_.-]independent", full_path, re.IGNORECASE)
    )
    if not is_dynamic:
        return out

    positive = is_positive_claim_value(value)
    if isinstance(value, str):
        promo_match = PROMOTION_RE.search(value)
        if promo_match and not claim_is_locally_fenced(path_join(path, key), value, promo_match):
            positive = True
    if not positive:
        return out

    if has_structured_evidence(parent):
        return out

    out.append(
        Violation(
            path=path_join(path, key),
            kind="tier2_dynamic_claim",
            token=key,
            message="dynamic/LLM-authored claim field is positive without local independent audit/control evidence",
            severity="major",
        )
    )
    return out


def audit_tmp_authority(path: str, text: str) -> Violation | None:
    if not TMP_RE.search(text):
        return None
    if TMP_FENCE_RE.search(text):
        return None
    return Violation(
        path=path,
        kind="external_tmp_authority",
        token="/tmp",
        message="/tmp or ephemeral path appears in claim-bearing data without non-authoritative/temp fence",
        severity="major",
    )


def audit_load_bearing_record(path: str, obj: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    load_keys = [k for k in obj if re.search(r"load[_-]?bearing", str(k), re.IGNORECASE)]
    if not load_keys:
        return out
    if not any(is_truthy(obj.get(k)) for k in load_keys):
        return out
    blob = local_blob(obj)
    evidence = has_structured_evidence(obj)
    if COUNT_HINT_RE.search(blob) and not evidence:
        out.append(
            Violation(
                path=path,
                kind="count_tautology_load_bearing_smell",
                token="load_bearing",
                message="load_bearing=true sits with count/expected/divergence fields but no structured erased/negative/control/source/witness evidence in the same record",
                severity="major",
            )
        )
    if not evidence:
        out.append(
            Violation(
                path=path,
                kind="unbacked_load_bearing_claim",
                token="load_bearing",
                message="load_bearing=true lacks structured control/witness/audit/source evidence in the same record",
                severity="major",
            )
        )
    return out


def audit_independence_record(path: str, obj: dict[str, Any]) -> list[Violation]:
    out: list[Violation] = []
    has_recompute = contains_positive_independent_recompute(obj)
    for key, value in obj.items():
        key_s = str(key)
        if re.search(r"(^|[_.-])independent([_.-]|$)", key_s, re.IGNORECASE) and is_positive_claim_value(value):
            if not has_recompute:
                out.append(
                    Violation(
                        path=path_join(path, key_s),
                        kind="unbacked_engine_independence",
                        token=key_s,
                        message="independence claim lacks positive lane_evidence/independent_recompute proof in the local record",
                        severity="major",
                    )
                )
    return out


def walk_json(node: Any, path: str, violations: list[Violation], *, ceiling_allows: bool, parent: Any = None) -> None:
    if isinstance(node, dict):
        violations.extend(audit_load_bearing_record(path, node))
        violations.extend(audit_independence_record(path, node))
        for key, value in node.items():
            key_s = str(key)
            child = path_join(path, key_s)
            violations.extend(audit_dynamic_key(path, key_s, value, node))
            # Scan the KEY itself only when it is not one of the explicit
            # schema/status keys. Schema keys like promotion_allowed=false are
            # the fence, not a prose promotion claim.
            if key_s not in KEY_PROSE_EXEMPT:
                pv = prose_violation(child, key_s, ceiling_allows=ceiling_allows)
                if pv:
                    violations.append(pv)
            walk_json(value, child, violations, ceiling_allows=ceiling_allows, parent=node)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk_json(item, path_join(path, i), violations, ceiling_allows=ceiling_allows, parent=node)
    elif isinstance(node, str):
        tv = audit_tmp_authority(path, node)
        if tv:
            violations.append(tv)
        pv = prose_violation(path, node, ceiling_allows=ceiling_allows)
        if pv:
            violations.append(pv)


def audit_json_file(path: Path, root: Path | None = None) -> list[Violation]:
    data = load_json(path)
    if data is None:
        return [Violation(rel(path, root), "unreadable_json", "json", "file could not be parsed as JSON", "blocking")]
    violations: list[Violation] = []
    file_rel = rel(path, root)
    violations.extend(top_level_promotion_violations(data, file_rel))
    # Never let the artifact's own promotion fields disable the scanner. A
    # promotion claim is exactly what this firewall must test.
    walk_json(data, file_rel, violations, ceiling_allows=False)
    return violations


def audit_markdown_file(path: Path, root: Path | None = None) -> list[Violation]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return [Violation(rel(path, root), "unreadable_text", "text", f"file could not be read: {exc}", "blocking")]
    out: list[Violation] = []
    for lineno, line in enumerate(lines, 1):
        tv = audit_tmp_authority(f"{rel(path, root)}:{lineno}", line)
        if tv:
            out.append(tv)
        pv = prose_violation(f"{rel(path, root)}:{lineno}", line, ceiling_allows=False)
        if pv:
            out.append(pv)
    return out


def collect_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.exists():
        return []

    # One sim dir.
    if (target / "results").is_dir():
        files = sorted((target / "results").glob("*.json"))
        audit = target / "audit_verdict.md"
        if audit.exists():
            files.append(audit)
        return files

    # Sims root or repo root.
    root = target
    if (target / "system_v6" / "sims").is_dir():
        sims_root = target / "system_v6" / "sims"
        files = sorted(sims_root.glob("*/results/*.json"))
        files.extend(sorted(sims_root.glob("*/audit_verdict.md")))
        receipts = target / "system_v6" / "receipts"
        if receipts.is_dir():
            files.extend(sorted(receipts.glob("*.md")))
        return files
    if target.name == "sims" or any((target / child).is_dir() for child in ("results",)):
        return sorted(target.glob("*/results/*.json")) + sorted(target.glob("*/audit_verdict.md"))

    return sorted(root.rglob("*.json")) + sorted(root.rglob("*.md"))


def run(target: Path, *, max_examples: int = 200) -> dict[str, Any]:
    files = collect_files(target)
    if not files:
        return {
            "ok": False,
            "summary": {"files_scanned": 0, "violations": 1},
            "violations": [Violation(str(target), "no_input", "<none>", "no JSON/Markdown artifacts found", "blocking").as_dict()],
        }

    root = target if target.is_dir() else target.parent
    violations: list[Violation] = []
    for f in files:
        if f.suffix.lower() == ".json":
            violations.extend(audit_json_file(f, root))
        elif f.suffix.lower() in {".md", ".markdown"}:
            violations.extend(audit_markdown_file(f, root))

    by_kind = Counter(v.kind for v in violations)
    by_severity = Counter(v.severity for v in violations)
    return {
        "ok": not violations,
        "summary": {
            "files_scanned": len(files),
            "violations": len(violations),
            "by_kind": dict(sorted(by_kind.items())),
            "by_severity": dict(sorted(by_severity.items())),
        },
        "violations": [v.as_dict() for v in violations[:max_examples]],
        "truncated": len(violations) > max_examples,
    }


def _selftest() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        good_dir = tmp / "finite_map_packet_v0" / "results"
        good_dir.mkdir(parents=True)
        good = {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "claim_ceiling": "scratch diagnostic, not admitted",
            "finite_index_set": [0, 1, 2],
            "negative_control": {"ran": True, "witness": "erased relation flips"},
            "source_path": "system_v6/sims/finite_map_packet_v0/runner.py",
            "source_sha256": "0" * 64,
            "notes": "not admitted; scratch diagnostic only",
        }
        (good_dir / "finite_map_packet_v0_results.json").write_text(json.dumps(good))
        (good_dir.parent / "audit_verdict.md").write_text("Bottom line: not admitted; scratch diagnostic only.\n")
        good_res = run(good_dir.parent)
        if not good_res["ok"]:
            failures.append(f"good packet failed: {good_res}")

        bad_dir = tmp / "endpoint_claim_packet_v0" / "results"
        bad_dir.mkdir(parents=True)
        bad = {
            "classification": "scratch_diagnostic",
            "promotion_allowed": False,
            "formal_admission_allowed": False,
            "pin_canonical": "ADMIT/INSTALLS endpoint structure",
            "engine_consensus": {"independent": True, "max_divergence": 0.0},
            "crossover_proofs": {"z3": {"load_bearing": True, "expected_count": 7, "count": 7}},
            "build_card": "/tmp/queue_card_axis0.md says gate open",
        }
        (bad_dir / "endpoint_claim_packet_v0_results.json").write_text(json.dumps(bad))
        (bad_dir.parent / "audit_verdict.md").write_text("Bottom line: canonical admitted proof installed.\n")
        bad_res = run(bad_dir.parent, max_examples=1000)
        if bad_res["ok"]:
            failures.append("bad packet passed")
        kinds = {v["kind"] for v in bad_res["violations"]}
        for expected in {
            "prose_promotion_leak",
            "tier2_dynamic_claim",
            "unbacked_engine_independence",
            "count_tautology_load_bearing_smell",
            "unbacked_load_bearing_claim",
            "external_tmp_authority",
        }:
            if expected not in kinds:
                failures.append(f"bad packet missed {expected}: {bad_res}")

        # Regression probes from adversarial review: these must not pass.
        probes = {
            "self_authorized_canon": {"classification": "canonical", "promotion_allowed": True, "claim": "canonical admitted proof installed"},
            "self_authorized_string": {"classification": "scratch_diagnostic", "promotion_allowed": "true", "formal_admission_allowed": "true", "claim": "still promoted"},
            "self_authorized_numeric": {"classification": "scratch_diagnostic", "promotion_allowed": 1, "formal_admission_allowed": 1, "claim": "still promoted"},
            "broad_fence_smuggle": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "claim": "not a caveat: canonical admitted proof installed"},
            "later_token_smuggle": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "claim": "not admitted; canonical admitted proof installed"},
            "dummy_evidence_launder": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "load_bearing": True, "audit": "none"},
            "false_recompute_launder": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "engine_consensus": {"independent": True, "independent_recompute": False}},
            "numeric_dynamic_claim": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "proofs_earned": 3},
            "tmp_scratch_launder": {"classification": "scratch_diagnostic", "promotion_allowed": False, "formal_admission_allowed": False, "claim": "scratch /tmp/queue_card_axis0.md says canonical admitted proof installed"},
        }
        for name, payload in probes.items():
            probe_dir = tmp / name / "results"
            probe_dir.mkdir(parents=True)
            (probe_dir / f"{name}_results.json").write_text(json.dumps(payload))
            probe_res = run(probe_dir.parent, max_examples=1000)
            if probe_res["ok"]:
                failures.append(f"adversarial probe passed unexpectedly: {name}")

    if failures:
        print("SELFTEST FAILED")
        for item in failures:
            print("  -", item)
        return 1
    print("SELFTEST PASSED")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Canon-firewall audit for sim artifacts.")
    parser.add_argument("target", nargs="?", help="repo root, sims root, sim dir, result JSON, or Markdown file")
    parser.add_argument("--selftest", action="store_true", help="run built-in self-test and exit")
    parser.add_argument("--max-examples", type=int, default=200, help="maximum violation examples to print")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.selftest:
        return _selftest()
    if not args.target:
        print(json.dumps({
            "ok": False,
            "summary": {"files_scanned": 0, "violations": 1},
            "violations": [Violation("<none>", "no_input", "<none>", "provide a target path", "blocking").as_dict()],
        }, indent=2, sort_keys=True))
        return 2
    result = run(Path(args.target), max_examples=args.max_examples)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
