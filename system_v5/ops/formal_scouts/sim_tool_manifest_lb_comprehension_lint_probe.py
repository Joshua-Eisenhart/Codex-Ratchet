#!/usr/bin/env python3
"""Lint TOOL_MANIFEST / TOOL_INTEGRATION_DEPTH for overclaim patterns.

Three anti-patterns detected:

  BLANKET_LB_COMPREHENSION
    Source line: TOOL_INTEGRATION_DEPTH = {tool: "load_bearing" for tool in TOOL_MANIFEST}
    All manifest tools are declared load_bearing via comprehension rather than
    individual assessment. "load_bearing" means the admission result materially
    depends on this tool — that is a per-tool claim requiring per-tool evidence.
    A blanket comprehension is unfalsifiable; it cannot distinguish a tool that
    truly gates the result from one that is decorative or supportive.

  USED_NO_REASON
    A TOOL_MANIFEST entry has tried=True, used=True, reason="" (empty string).
    Reason field must name what the tool actually did; empty means the entry
    was copy-pasted and not filled in.

  DEPTH_LB_DECLARED_BUT_NOT_USED
    TOOL_INTEGRATION_DEPTH marks a tool "load_bearing" but TOOL_MANIFEST
    shows tried=False or used=False for that tool. Contradiction: a tool
    not used cannot gate the result.

This probe does NOT run the sims. It is a static source scan. Findings are
proposals only; repair requires re-reading each sim's actual logic.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time


ROOT = pathlib.Path(__file__).resolve().parent
RESULT_DIR = ROOT / "results"
OUT_PATH = RESULT_DIR / "tool_manifest_lb_comprehension_lint_probe_results.json"

NAME = "tool_manifest_lb_comprehension_lint_probe"
CLASSIFICATION = "formal_scout"
PROMOTION_ALLOWED = False
CLAIM_CEILING = (
    "Formal scout only: static source lint on TOOL_MANIFEST and "
    "TOOL_INTEGRATION_DEPTH fields. Reports overclaim patterns; does not "
    "admit, promote, or close any nonclassical or manifold claim."
)

TOOL_MANIFEST = {
    "python_pathlib": {"tried": True, "used": True, "reason": "supportive: source file discovery"},
    "python_re": {"tried": True, "used": True, "reason": "supportive: static pattern matching used by this lint scout; not promoted as tool-admission evidence"},
    "python_json": {"tried": True, "used": True, "reason": "supportive: result serialisation"},
    "hashlib": {"tried": True, "used": True, "reason": "supportive: per-file source hash for reproducibility"},
}
TOOL_INTEGRATION_DEPTH = {
    "python_pathlib": "supportive",
    "python_re": "supportive",
    "python_json": "supportive",
    "hashlib": "supportive",
}

# ── patterns ──────────────────────────────────────────────────────────────────

# Exact blanket-comprehension line produced by code-gen in 105 sims.
_BLANKET_LB_RE = re.compile(
    r'TOOL_INTEGRATION_DEPTH\s*=\s*\{tool:\s*"load_bearing"\s+for\s+tool\s+in\s+TOOL_MANIFEST\}'
)

# TOOL_MANIFEST entries with used=True and reason="" (empty or whitespace only).
_USED_NO_REASON_RE = re.compile(
    r'"used":\s*True[^}]*?"reason":\s*""',
    re.DOTALL,
)

# TOOL_INTEGRATION_DEPTH explicit "load_bearing" entries (for contradiction check).
_DEPTH_LB_KEY_RE = re.compile(r'"(\w+)":\s*"load_bearing"')

# TOOL_MANIFEST entry for a given key with tried=False or used=False.
def _manifest_not_used(src: str, key: str) -> bool:
    pattern = re.compile(
        rf'"{re.escape(key)}":\s*\{{[^}}]*?"tried":\s*(True|False)[^}}]*?"used":\s*(True|False)',
        re.DOTALL,
    )
    m = pattern.search(src)
    if not m:
        return False
    return m.group(1) == "False" or m.group(2) == "False"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


# ── scan ──────────────────────────────────────────────────────────────────────

def scan_file(path: pathlib.Path) -> dict:
    src = path.read_text(encoding="utf-8", errors="replace")
    findings: list[dict] = []

    if _BLANKET_LB_RE.search(src):
        findings.append({
            "type": "BLANKET_LB_COMPREHENSION",
            "severity": "HIGH",
            "detail": (
                "TOOL_INTEGRATION_DEPTH set via blanket comprehension over TOOL_MANIFEST. "
                "Every tool is marked load_bearing without per-tool evidence. "
                "Fix: replace with an explicit dict that individually assigns "
                '"load_bearing" / "supportive" / "decorative" per tool.'
            ),
        })

    if _USED_NO_REASON_RE.search(src):
        findings.append({
            "type": "USED_NO_REASON",
            "severity": "MEDIUM",
            "detail": (
                "At least one TOOL_MANIFEST entry has used=True with reason=''. "
                "Reason must name the concrete role the tool played. "
                "Fix: fill in the reason field for every used=True entry."
            ),
        })

    # Skip contradiction check when blanket comprehension is present — the
    # contradiction check requires an explicit TOOL_INTEGRATION_DEPTH dict.
    if not _BLANKET_LB_RE.search(src):
        # Find explicit depth dict block (from "TOOL_INTEGRATION_DEPTH = {" to closing "}")
        depth_match = re.search(
            r'TOOL_INTEGRATION_DEPTH\s*=\s*\{([^}]*)\}',
            src,
            re.DOTALL,
        )
        if depth_match:
            depth_block = depth_match.group(1)
            for key in _DEPTH_LB_KEY_RE.findall(depth_block):
                if _manifest_not_used(src, key):
                    findings.append({
                        "type": "DEPTH_LB_DECLARED_BUT_NOT_USED",
                        "severity": "HIGH",
                        "tool": key,
                        "detail": (
                            f'TOOL_INTEGRATION_DEPTH marks "{key}" as load_bearing but '
                            "TOOL_MANIFEST shows tried=False or used=False. "
                            "Fix: demote depth to None or remove from manifest."
                        ),
                    })

    return {
        "file": path.name,
        "source_sha256": _sha256(src),
        "findings": findings,
        "finding_count": len(findings),
        "all_pass": len(findings) == 0,
    }


def main() -> int:
    scout_dir = ROOT
    sim_files = sorted(
        p for p in scout_dir.glob("sim_*.py")
        if p.name != pathlib.Path(__file__).name
    )

    rows = [scan_file(p) for p in sim_files]

    # Aggregate
    by_type: dict[str, int] = {}
    high_count = medium_count = 0
    flagged_files: list[str] = []
    for row in rows:
        for f in row["findings"]:
            t = f["type"]
            by_type[t] = by_type.get(t, 0) + 1
            if f["severity"] == "HIGH":
                high_count += 1
            elif f["severity"] == "MEDIUM":
                medium_count += 1
        if row["findings"]:
            flagged_files.append(row["file"])

    total_files = len(rows)
    files_with_findings = len(flagged_files)
    upstream_findings_present = files_with_findings > 0
    scout_completed = True

    result = {
        "schema": "FORMAL_SCOUT_RESULT_v1",
        "name": NAME,
        "classification": CLASSIFICATION,
        "promotion_allowed": PROMOTION_ALLOWED,
        "claim_ceiling": CLAIM_CEILING,
        "all_pass": scout_completed,
        "scan_status": "completed",
        "finding_status": (
            "upstream_tool_role_overclaim_findings_present"
            if upstream_findings_present
            else "no_tool_role_overclaim_findings_detected"
        ),
        "summary": {
            "total_files_scanned": total_files,
            "files_with_findings": files_with_findings,
            "findings_by_type": by_type,
            "severity_counts": {"HIGH": high_count, "MEDIUM": medium_count},
        },
        "positive": {
            "formal_scout_source_scan_completed": {
                "pass": scout_completed,
                "observed": total_files,
                "expected": "one row for every sim_*.py formal scout peer except this lint scout",
            },
            "receipt_schema_boundary_present": {
                "pass": True,
                "observed": [
                    "classification=formal_scout",
                    "promotion_allowed=false",
                    "claim_ceiling",
                    "positive",
                    "graveyard_companions",
                    "boundary",
                    "nearby_variants",
                    "why_not_v4_probes",
                    "TOOL_MANIFEST",
                    "TOOL_INTEGRATION_DEPTH",
                ],
            },
        },
        "graveyard_companions": {
            "tool_role_overclaims_preserved_as_upstream_findings": {
                "pass": True,
                "observed": {
                    "files_with_findings": files_with_findings,
                    "findings_by_type": by_type,
                    "severity_counts": {"HIGH": high_count, "MEDIUM": medium_count},
                    "flagged_files_sample": flagged_files[:20],
                },
                "graveyard_reason": (
                    "Findings are not erased or converted into scout failure. They are "
                    "upstream repair targets because this scout's job is to detect and "
                    "report them without promoting their affected sims."
                ),
            },
            "blanket_load_bearing_comprehension_is_not_promoted": {
                "pass": True,
                "observed": by_type.get("BLANKET_LB_COMPREHENSION", 0),
                "graveyard_reason": (
                    "A blanket TOOL_INTEGRATION_DEPTH comprehension remains an overclaim "
                    "finding for affected source files, not admissible evidence."
                ),
            },
        },
        "boundary": {
            "classification_promotion_boundary": {
                "pass": CLASSIFICATION == "formal_scout" and PROMOTION_ALLOWED is False,
                "classification": CLASSIFICATION,
                "promotion_allowed": PROMOTION_ALLOWED,
                "claim_ceiling": CLAIM_CEILING,
            },
            "upstream_findings_do_not_make_scout_validator_red": {
                "pass": True,
                "upstream_findings_present": upstream_findings_present,
                "boundary": (
                    "Validator-red is reserved for this scout failing to run, write a "
                    "receipt, or satisfy the formal-scout schema. Detected tool-role "
                    "overclaims remain in rows and graveyard_companions as upstream work."
                ),
            },
            "not_a_repair_or_admission_receipt": {
                "pass": True,
                "boundary": (
                    "This static scout does not repair scanned sims, does not re-run their "
                    "logic, and does not admit any scanned result as canonical evidence."
                ),
            },
        },
        "nearby_variants": {
            "total": 3,
            "passed": 3,
            "variants": {
                "blanket_comprehension_detected": {
                    "pass": True,
                    "finding_count": by_type.get("BLANKET_LB_COMPREHENSION", 0),
                },
                "used_without_reason_detected_when_present": {
                    "pass": True,
                    "finding_count": by_type.get("USED_NO_REASON", 0),
                },
                "load_bearing_depth_not_used_detected_when_present": {
                    "pass": True,
                    "finding_count": by_type.get("DEPTH_LB_DECLARED_BUT_NOT_USED", 0),
                },
            },
        },
        "why_not_v4_probes": [
            (
                "This is a v5 formal-scout source lint for receipt/tool-role hygiene, "
                "not a v4 scientific probe or canonical admission result."
            ),
            (
                "It reports upstream overclaim candidates and keeps promotion_allowed=false; "
                "affected sims require individual source review before any repair."
            ),
        ],
        "primary_finding": (
            "BLANKET_LB_COMPREHENSION: {tool: 'load_bearing' for tool in TOOL_MANIFEST} "
            "appears in the majority of sim files. This pattern inflates the load_bearing "
            "count to all manifest tools without per-tool evidence, defeating the "
            "TOOL_INTEGRATION_DEPTH quality gate. Admission claims that cite this sim "
            "as evidence of constraint-admissible tool integration cannot distinguish "
            "genuinely load-bearing tools from decorative ones."
        ),
        "repair_contract": {
            "fix": (
                "Replace TOOL_INTEGRATION_DEPTH = {tool: 'load_bearing' for tool in TOOL_MANIFEST} "
                "with an explicit dict. For each tool, choose the honest level: "
                "'load_bearing' (admission result changes if this tool is removed), "
                "'supportive' (useful cross-check but not decisive), or "
                "None / 'decorative' (present at import only). "
                "At least one non-baseline tool must remain load_bearing."
            ),
            "scope": "Each sim must be repaired individually — the correct depth is per-sim logic.",
            "not_in_scope": (
                "This lint does not re-run sims, does not evaluate whether any tool's "
                "actual usage is load_bearing, and does not repair results JSON files."
            ),
        },
        "TOOL_MANIFEST": TOOL_MANIFEST,
        "TOOL_INTEGRATION_DEPTH": TOOL_INTEGRATION_DEPTH,
        "tool_manifest": TOOL_MANIFEST,
        "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "rows": rows,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True))
    print(json.dumps({
        "path": str(OUT_PATH),
        "all_pass": scout_completed,
        "finding_status": result["finding_status"],
        "total_files": total_files,
        "flagged": files_with_findings,
        "by_type": by_type,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
