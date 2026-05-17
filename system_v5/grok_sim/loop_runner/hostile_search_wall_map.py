#!/usr/bin/env python3
"""hostile_search_wall_map.py — cluster failure modes across legos.

Walks every receipts/hostile_search/<lego>_<ts>/manifest.json and every
graveyard.md, extracts cause-of-death strings, and clusters them by
recognizable signatures. Output: WALL_MAP.md.

The wall map is what tells us where the cheap labor is going. If 60% of
deaths on every lego are qutip-API hallucinations, the next round's prompt
should counter that mode harder. If a particular MMM language is producing
disproportionately weak attacks, the lineup needs rebalancing.
"""
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE / "receipts" / "hostile_search"
PYTHON_BIN = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"


# Signature patterns. Order matters — first match wins.
SIGNATURES = [
    ("qutip_api_hallucination",  re.compile(r"qutip.*has no attribute|cannot import name '\w+' from 'qutip'", re.I)),
    ("numpy_norm_misuse",        re.compile(r"matrix norm must be in|norm.*invalid", re.I)),
    ("qutip_dim_mismatch",       re.compile(r"incompatible dimensions|dims.*mismatch", re.I)),
    ("kraus_completeness_fail",  re.compile(r"completeness|cptp tolerance|kraus.*violat", re.I)),
    ("import_error",             re.compile(r"ModuleNotFoundError|ImportError(?!.*qutip)", re.I)),
    ("syntax_error",             re.compile(r"syntax error", re.I)),
    ("banned_identifier",        re.compile(r"banned identifier", re.I)),
    ("missing_required_function",re.compile(r"missing required functions?", re.I)),
    ("naming_audit_format_miss", re.compile(r"naming-audit.*no claim-ceiling", re.I)),
    ("trivial_response",         re.compile(r"empty or trivially short|no python code block", re.I)),
    ("timeout",                  re.compile(r"timeout", re.I)),
    ("assertion_failure",        re.compile(r"AssertionError", re.I)),
    ("attribute_error_other",    re.compile(r"AttributeError", re.I)),
    ("value_error_other",        re.compile(r"ValueError", re.I)),
    ("type_error_other",         re.compile(r"TypeError", re.I)),
]


def classify(msg: str) -> str:
    for label, pat in SIGNATURES:
        if pat.search(msg):
            return label
    return "uncategorized"


RUN_SNIPPET = """
import sys, importlib.util, signal
def _to(s,f): raise TimeoutError()
signal.signal(signal.SIGALRM, _to); signal.alarm(30)
spec = importlib.util.spec_from_file_location('m', sys.argv[1])
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
    r = m.main() if hasattr(m,'main') else None
    print('OK')
except Exception as e:
    print(f'FAIL:{type(e).__name__}:{str(e)[:200]}')
"""


def runs_gate_msg(path: Path) -> tuple[bool, str]:
    if path.suffix == ".md":
        return True, "non-executable naming-audit"
    try:
        r = subprocess.run([PYTHON_BIN, "-c", RUN_SNIPPET, str(path)],
                           capture_output=True, text=True, timeout=45)
        out = (r.stdout + r.stderr).strip().splitlines()
        last = out[-1] if out else ""
        if last == "OK":
            return True, "main() executed"
        return False, last[:200]
    except subprocess.TimeoutExpired:
        return False, "timeout > 30s"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:160]}"


def main():
    if not ROOT.exists(): return
    runs = sorted([d for d in ROOT.iterdir() if d.is_dir() and (d / "manifest.json").exists()])
    if not runs:
        print("no runs"); return

    # cause counter by signature, by lego, by pool, by mmm, by attack_shape
    by_sig = Counter()
    by_lego = defaultdict(Counter)
    by_pool = defaultdict(Counter)
    by_mmm = defaultdict(Counter)
    by_shape = defaultdict(Counter)
    survivors_by_pool = Counter()
    survivors_by_mmm = Counter()
    survivors_by_shape = Counter()
    total_attacks = 0
    total_corpses = 0

    for run_dir in runs:
        manifest = json.loads((run_dir / "manifest.json").read_text())
        lego = manifest["primitive_key"]
        for r in manifest.get("receipts", []):
            total_attacks += 1
            light_passed = r.get("passed_gate", False)
            # collect light-gate corpses
            if not light_passed:
                sig = classify(r.get("gate_reason", ""))
                by_sig[sig] += 1
                by_lego[lego][sig] += 1
                by_pool[r["pool"]][sig] += 1
                by_mmm[r["mmm_language"]][sig] += 1
                by_shape[r["attack_shape"]][sig] += 1
                total_corpses += 1
                continue
            # apply runs gate
            if r.get("attack_shape") == "naming_audit":
                # gate-neutral; count as audit receipt
                continue
            attack_path = run_dir / r["attack_path"]
            if not attack_path.exists(): continue
            ok, msg = runs_gate_msg(attack_path)
            if ok:
                survivors_by_pool[r["pool"]] += 1
                survivors_by_mmm[r["mmm_language"]] += 1
                survivors_by_shape[r["attack_shape"]] += 1
            else:
                sig = classify(msg)
                by_sig[sig] += 1
                by_lego[lego][sig] += 1
                by_pool[r["pool"]][sig] += 1
                by_mmm[r["mmm_language"]][sig] += 1
                by_shape[r["attack_shape"]][sig] += 1
                total_corpses += 1

    # Audit-gate verdicts
    verdict_re = re.compile(r"VERDICT:\s*(PROMOTION_READY|PROMOTION_BLOCKED|NEEDS_REVISION)", re.I)
    audit_counter = Counter()
    audit_finding_re = re.compile(r"(tautological|shallow negative|vacuous|trivial(?: degenerate)?|"
                                  r"hardcoded|decorative|missing.*seed|hash|synthetic|identity.*disguised)", re.I)
    audit_findings = Counter()
    audit_by_lego = defaultdict(Counter)
    for run_dir in runs:
        manifest = json.loads((run_dir / "manifest.json").read_text())
        lego = manifest["primitive_key"]
        for af in run_dir.glob("AUDIT_*.md"):
            text = af.read_text()
            m = verdict_re.search(text)
            v = m.group(1).upper() if m else "UNPARSED"
            audit_counter[v] += 1
            audit_by_lego[lego][v] += 1
            for hit in audit_finding_re.findall(text):
                audit_findings[hit.lower()] += 1

    lines = ["# Wall map — hostile-search failure-mode clusters", ""]
    lines.append(f"Corpses across automated gates: {total_corpses} / {total_attacks} attacks.")
    lines.append("")
    lines.append("## Reviewer-gate verdicts")
    lines.append("")
    lines.append("| Verdict | Count |")
    lines.append("|---|---:|")
    for v in ("PROMOTION_READY", "NEEDS_REVISION", "PROMOTION_BLOCKED", "UNPARSED"):
        if audit_counter.get(v):
            lines.append(f"| `{v}` | {audit_counter[v]} |")
    if audit_findings:
        lines.append("")
        lines.append("### Recurring reviewer-finding keywords")
        lines.append("")
        lines.append("| Keyword | Count |")
        lines.append("|---|---:|")
        for kw, n in audit_findings.most_common():
            lines.append(f"| `{kw}` | {n} |")
    lines.append("")
    lines.append("## Failure-mode signatures (most common first)")
    lines.append("")
    lines.append("| Signature | Count |")
    lines.append("|---|---:|")
    for sig, n in by_sig.most_common():
        lines.append(f"| `{sig}` | {n} |")

    def section(title: str, table: dict, surv: Counter):
        lines.append("")
        lines.append(f"## {title}")
        lines.append("")
        keys = sorted(set(table) | set(surv))
        if not keys: return
        all_sigs = sorted({s for c in table.values() for s in c})
        header = "| key | survivors | " + " | ".join(f"`{s}`" for s in all_sigs) + " |"
        sep = "|---|---:|" + "---:|" * len(all_sigs)
        lines.append(header); lines.append(sep)
        for k in keys:
            row = [f"`{k}`", str(surv.get(k, 0))]
            for s in all_sigs:
                row.append(str(table[k].get(s, 0)))
            lines.append("| " + " | ".join(row) + " |")

    section("By model pool", by_pool, survivors_by_pool)
    section("By MMM attack language", by_mmm, survivors_by_mmm)
    section("By attack shape", by_shape, survivors_by_shape)

    lines.append("")
    lines.append("## By lego")
    lines.append("")
    for lego in sorted(by_lego):
        lines.append(f"### `{lego}`")
        for sig, n in by_lego[lego].most_common():
            lines.append(f"- `{sig}` × {n}")
        lines.append("")

    out = ROOT / "WALL_MAP.md"
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
