#!/usr/bin/env python3
"""GATE 1 - TWO-TIER AUTHORITY: result-JSON verdict tokens vs the committed audit.

Mechanical, deterministic gate. NO LLM judgment. It does NOT mutate any sim.

Doctrine (from the deep re-audit ledger 2026-06-13): trust the frozen TIER-1
fields and the result *ceiling*, but DO NOT trust a positive TIER-2 verdict token
unless a committed `audit_verdict*.md` in the same sim dir affirmatively confirms
it. Overclaim in this estate lives in the dynamic verdict tokens / prose, not in
the frozen ceiling fields.

TWO TIERS
---------
TIER-1 (trusted, NOT checked here): classification, promotion_allowed,
  formal_admission_allowed, claim_ceiling. These are the frozen honesty fields and
  the gate leaves them alone.

TIER-2 (dynamic, verdict-bearing) tokens, scanned recursively over every result
  JSON in the sim's `results/` dir (excluding `*_validator_results.json`):

  HARD positive tokens (assert an earned/survived/accepted outcome):
    * any key named `verdict` whose value starts SURVIVES* / EARNED* / ACCEPTED
    * any key containing `earned` whose value is boolean True
      (e.g. *_earned, *_guard_earned, chirality_earned_on_grounded_carrier)
    * any key ending `_independent` or equal to `independent` whose value is True
      (covers engine_consensus.independent == true)
    * result_language / claim_strength prose values (non-empty)

  SOFT positive token:
    * TOOL_INTEGRATION_DEPTH.* == "load_bearing"

AUDIT DECISION
--------------
The single decisive sentence is read from the first `Bottom line:` / `Verdict:`
header (in file order) of the committed `audit_verdict*.md`, then truncated to its
first sentence (up to the first period) so trailing explanatory clauses do not
pollute the verdict read. It is classified deterministically by keyword:
  CONTRADICT  - reject* / by_construction / decorative / void / defer / dies* /
                fail* / "not accepted" / "does not survive" / "rejected as stated"
  AFFIRM      - genuine / sustain* / accept* / pass* / confirm*
  NEUTRAL     - none of the above (e.g. "COMMIT_READY at scratch_diagnostic ceiling")
  NO_AUDIT    - no committed audit_verdict*.md exists
CONTRADICT is checked before AFFIRM, so "NOT ACCEPTED" and "DIES_v2 accepted"
resolve to CONTRADICT.

VIOLATION RULES
---------------
A HARD positive token VIOLATES unless the audit decision is AFFIRM. That is:
NO_AUDIT, CONTRADICT, and NEUTRAL all fail a HARD token (a bare earned/survived
claim with no affirmative confirmation is an overclaim). A bare COMMIT_READY /
scratch-ceiling acceptance does not affirm a HARD "earned" token.

A SOFT (load_bearing) token VIOLATES only when there is NO committed audit file at
all. A present audit (even one that legitimately accepts a DEATH verdict, e.g.
"DIES_v2 accepted") does not by itself condemn genuine load-bearing tooling.

EXEMPTION (fence): a HARD token is exempted if a co-located fence string is present
in its immediate parent object - one of: does-not-self-upgrade, pending re-audit,
by_construction (and underscore/hyphen variants). The fence must sit beside the
token, not merely somewhere in the file.

GATE CEILING (honest scope of THIS gate)
----------------------------------------
This gate proves only `exists`/string-level consistency between result-JSON verdict
tokens and the audit headline sentence. It does NOT recompute any math, does NOT
verify that an AFFIRM audit is itself correct, and does NOT read builder prose
beyond the one decisive sentence. It is a keyword/structure consistency check, not
an evidence-grade adjudication. It is GAMEABLE by (a) wording the audit decisive
sentence with an affirm keyword, (b) renaming a verdict key, or (c) planting a
fence string next to a token. It catches the common failure mode in this estate -
a positive result-JSON verdict token sitting over an audit that rejects /
by-constructions / defers / has no audit - not adversarial evasion.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


SIMS_ROOT = Path("system_v6/sims")

# --- HARD positive verdict-value prefixes (for keys named exactly "verdict") ---
POS_VERDICT_PREFIXES = ("survives", "earned", "accepted")

# --- Audit decisive-sentence classification -----------------------------------
# Multi-word / underscore-bearing contradiction phrases (substring match).
CONTRADICT_PHRASES = (
    "by_construction",
    "by-construction",
    "by construction",
    "does not survive",
    "rejected as stated",
    "not accepted",
    "not-accepted",
    "not_accepted",
)
# Single-word contradiction stems (word-start anchored; tolerate _vN / suffixes).
CONTRADICT_STEMS = ("reject", "decorative", "void", "defer", "dies", "died", "fail", "deny", "denied", "dismiss", "invalid", "refut", "by_construction", "by-construction", "overclaim")
# Affirmation stems (word-start anchored; tolerate _WITH_CAVEATS / suffixes).
# NOTE: "commit_ready" is deliberately NOT here - a bare commit-ready / scratch
# ceiling acceptance does not affirmatively confirm a HARD "earned" token.
AFFIRM_STEMS = ("genuine", "sustain", "accept", "pass", "confirm")

# --- Fence strings that exempt a co-located HARD token ------------------------
FENCE_SUBSTRINGS = (
    "does_not_self_upgrade",
    "does-not-self-upgrade",
    "does not self-upgrade",
    "does not self upgrade",
    "pending_re_audit",
    "pending-re-audit",
    "pending re-audit",
    "pending re audit",
    "pending_reaudit",
    "by_construction",
    "by-construction",
)

# Header words that are section labels, not a verdict statement.
_HEADER_NOISE = {"table", "summary", "species", "detail", "details", "section"}
_VERDICT_HEADER_RE = re.compile(
    r"^#{0,4}\s*\*{0,2}\s*(bottom\s*line|verdict)\b\s*[:\-=]?\s*\**\s*(.*)$",
    re.IGNORECASE,
)


# ------------------------------------------------------------------------------
# Audit decisive-sentence extraction + classification
# ------------------------------------------------------------------------------
def audit_files(sim_dir: Path) -> list[Path]:
    return sorted(sim_dir.glob("audit_verdict*.md"))


def decisive_sentence(sim_dir: Path) -> str | None:
    """Return the single decisive audit sentence, or None if no audit file."""
    files = audit_files(sim_dir)
    if not files:
        return None
    lines = files[0].read_text(encoding="utf-8", errors="replace").splitlines()
    n = len(lines)
    for i, raw in enumerate(lines):
        match = _VERDICT_HEADER_RE.match(raw.strip())
        if not match:
            continue
        tail = match.group(2).strip(" *:`=")
        if len(tail) > 2 and tail.lower() not in _HEADER_NOISE:
            return tail
        for j in range(i + 1, n):
            if lines[j].strip():
                return lines[j].strip().strip(" *:`=")
    # No verdict/bottom-line header: fall back to first non-blank line.
    for raw in lines:
        if raw.strip():
            return raw.strip()
    return ""  # empty audit file


def _first_sentence(sentence: str) -> str:
    """Isolate the verdict clause: text up to the first sentence-ending period.

    Audit bottom-lines often state the verdict in the first sentence then discuss
    what failed/passed in later clauses (e.g. a PASS_WITH_CAVEATS headline whose
    second sentence mentions a sub-step that 'fails'). Only the first sentence is
    the verdict statement.
    """
    match = re.search(r"[.!](\*+)?(\s|$)", sentence)
    if match:
        return sentence[: match.start() + 1]
    return sentence


def classify_audit(sentence: str | None) -> str:
    if sentence is None:
        return "NO_AUDIT"
    text = _first_sentence(sentence).lower()
    for phrase in CONTRADICT_PHRASES:
        if phrase in text:
            return "CONTRADICT"
    for stem in CONTRADICT_STEMS:
        if re.search(r"\b" + re.escape(stem), text):
            return "CONTRADICT"
    for stem in AFFIRM_STEMS:
        if re.search(r"\b" + re.escape(stem), text):
            return "AFFIRM"
    return "NEUTRAL"


# ------------------------------------------------------------------------------
# Tier-2 token extraction
# ------------------------------------------------------------------------------
@dataclass(frozen=True)
class Token:
    kind: str          # "hard" | "soft"
    family: str        # verdict | earned | independent | prose | load_bearing
    path: str          # dotted JSON path
    value: object
    fenced: bool       # a fence string sits in the token's parent object


def _is_pos_verdict_value(value: object) -> bool:
    text = str(value).strip().lower()
    return any(text.startswith(p) for p in POS_VERDICT_PREFIXES)


def _parent_is_fenced(parent: dict) -> bool:
    for key, val in parent.items():
        blob = f"{key} {val}".lower()
        if any(f in blob for f in FENCE_SUBSTRINGS):
            return True
    return False


def collect_tokens(obj: object, path: str, parent: dict | None, out: list[Token]) -> None:
    if isinstance(obj, dict):
        fenced = _parent_is_fenced(obj)
        for key, val in obj.items():
            child_path = f"{path}.{key}" if path else key
            klow = key.lower()
            if isinstance(val, (dict, list)):
                collect_tokens(val, child_path, obj, out)
                continue
            vlow = str(val).strip().lower()
            # HARD: positive verdict value on a key named exactly "verdict"
            if klow == "verdict" and _is_pos_verdict_value(val):
                out.append(Token("hard", "verdict", child_path, val, fenced))
            # HARD: any *earned* boolean True, but NOT a negated *_not_earned
            # (a `*_not_earned == True` is an honest death claim, not an overclaim).
            elif "earned" in klow and "not_earned" not in klow and "not earned" not in klow and val is True:
                out.append(Token("hard", "earned", child_path, val, fenced))
            # HARD: *_independent / independent boolean True
            elif (klow.endswith("_independent") or klow == "independent") and val is True:
                out.append(Token("hard", "independent", child_path, val, fenced))
            # HARD: result_language / claim_strength prose
            elif klow in ("result_language", "claim_strength") and vlow not in ("", "none", "null"):
                out.append(Token("hard", "prose", child_path, val, fenced))
            # SOFT: load_bearing tool-integration depth
            elif vlow == "load_bearing":
                out.append(Token("soft", "load_bearing", child_path, val, fenced))
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            child_path = f"{path}[{idx}]"
            if isinstance(val, (dict, list)):
                collect_tokens(val, child_path, parent, out)


def result_files(sim_dir: Path) -> list[Path]:
    results_dir = sim_dir / "results"
    if not results_dir.is_dir():
        return []
    return sorted(
        p
        for p in results_dir.glob("*.json")
        if not p.name.endswith("_validator_results.json")
    )


# ------------------------------------------------------------------------------
# Per-sim evaluation
# ------------------------------------------------------------------------------
@dataclass
class SimViolation:
    sim: str
    decision: str
    decisive_sentence: str
    hard_paths: list[str] = field(default_factory=list)
    soft_paths: list[str] = field(default_factory=list)

    def reason(self) -> str:
        parts = []
        if self.hard_paths:
            parts.append(f"hard_token_not_affirmed[{self.decision}]")
        if self.soft_paths:
            parts.append("load_bearing_no_audit_file")
        return "+".join(parts)


def evaluate_sim(sim_dir: Path) -> tuple[SimViolation | None, int, int]:
    """Return (violation_or_None, hard_token_count, soft_token_count)."""
    tokens: list[Token] = []
    for path in result_files(sim_dir):
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except (json.JSONDecodeError, OSError):
            continue
        collect_tokens(data, "", None, tokens)

    hard = [t for t in tokens if t.kind == "hard"]
    soft = [t for t in tokens if t.kind == "soft"]
    if not hard and not soft:
        return None, 0, 0

    sentence = decisive_sentence(sim_dir)
    decision = classify_audit(sentence)

    # HARD tokens: violate unless decision is AFFIRM, unless co-located fence.
    hard_violating = [t for t in hard if not t.fenced and decision != "AFFIRM"]
    # SOFT tokens: violate only when there is no committed audit file at all.
    soft_violating = [t for t in soft if not t.fenced and decision == "NO_AUDIT"]

    if not hard_violating and not soft_violating:
        return None, len(hard), len(soft)

    violation = SimViolation(
        sim=sim_dir.name,
        decision=decision,
        decisive_sentence=(sentence or "<NO AUDIT FILE>")[:160],
        hard_paths=[t.path for t in hard_violating],
        soft_paths=[t.path for t in soft_violating],
    )
    return violation, len(hard), len(soft)


def sim_dirs(sims_root: Path) -> list[Path]:
    if not sims_root.is_dir():
        raise SystemExit(f"missing sims dir: {sims_root}")
    return sorted(p for p in sims_root.iterdir() if p.is_dir())


def run_gate(sims_root: Path) -> dict:
    dirs = sim_dirs(sims_root)
    violations: list[SimViolation] = []
    for sim_dir in dirs:
        violation, _hard, _soft = evaluate_sim(sim_dir)
        if violation is not None:
            violations.append(violation)
    return {
        "ok": len(violations) == 0,
        "sims_scanned": len(dirs),
        "violations": [
            {
                "sim": v.sim,
                "reason": v.reason(),
                "audit_decision": v.decision,
                "decisive_sentence": v.decisive_sentence,
                "hard_token_paths": v.hard_paths,
                "soft_token_paths": v.soft_paths,
            }
            for v in violations
        ],
    }


# ------------------------------------------------------------------------------
# Self-test (deterministic; no repo dependency)
# ------------------------------------------------------------------------------
def selftest() -> int:
    failures: list[str] = []

    def check(name: str, got: object, want: object) -> None:
        if got != want:
            failures.append(f"{name}: got {got!r} want {want!r}")

    # --- classify_audit on the calibrated named decisive sentences ---
    cases = [
        ("SURVIVES_v0` is rejected as stated. Verdict species", "CONTRADICT"),
        ("VERDICT: BY_CONSTRUCTION / SURVIVAL CLAIM REJECTED AS STATED.", "CONTRADICT"),
        ("VERDICT: BY_CONSTRUCTION / model-access-gap. does not survive", "CONTRADICT"),
        ("REJECT` for the earned independent guard claim.", "CONTRADICT"),
        ("NOT ACCEPTED under the current binding amendment pins.", "CONTRADICT"),
        ("DEFER.", "CONTRADICT"),
        ("VERDICT: `DIES_v2` accepted, with a generated-artifact freshness caveat.", "CONTRADICT"),
        ("FAIL for the claimed FULL first computed `M(C)` frontier packet.", "CONTRADICT"),
        ("DECORATIVE for the claimed 0/3/6 carrier-independence evidence.", "CONTRADICT"),
        ("genuine scratch diagnostic packet for the repaired object", "AFFIRM"),
        ("VERDICT: PASS / SUSTAINED, with the Betti consumer still blocked.", "AFFIRM"),
        ("GENUINE-WITH-CAVEATS", "AFFIRM"),
        ("ACCEPTED for the narrow Supplement-1-pinned light scope.", "AFFIRM"),
        ("PASS_WITH_CAVEATS at scratch_diagnostic ceiling.", "AFFIRM"),
        ("VERDICT `ACCEPTED_WITH_NAMED_CAVEATS` as a bounded S3", "AFFIRM"),
        ("COMMIT_READY at scratch_diagnostic ceiling.", "NEUTRAL"),
        # multi-clause headline: verdict in first sentence, "fail" in a later clause
        ("PASS_WITH_CAVEATS at scratch_diagnostic ceiling.** The heavy exclusion "
         "survives audit. CP.11 ... then fail the heavy teeth.", "AFFIRM"),
        (None, "NO_AUDIT"),
    ]
    for sentence, want in cases:
        check(f"classify({sentence!r})", classify_audit(sentence), want)

    # --- token extraction ---
    sample = {
        "discriminator": {"verdict": "SURVIVES_v0"},
        "chirality_earned_on_grounded_carrier": True,
        "engine_consensus": {"independent": True},
        "result_language": "this engine earns the chiral discriminator",
        "TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing", "json": "supportive"},
        "crossover_proofs": {"z3": {"verdict": "unsat"}},  # not a positive verdict
        "controls": {"scrambled": {"verdict": "DIES_v0"}},  # death verdict, not positive
        "boundary": {"full_A33_recovery_not_earned": True},  # negated earned = death, not positive
        "independent_guard_earned": False,  # earned but False = not a positive token
    }
    toks: list[Token] = []
    collect_tokens(sample, "", None, toks)
    hard = sorted(t.family for t in toks if t.kind == "hard")
    soft = sorted(t.family for t in toks if t.kind == "soft")
    check("hard families", hard, ["earned", "independent", "prose", "verdict"])
    check("soft families", soft, ["load_bearing"])

    # --- fence detection in parent object ---
    fenced_sample = {
        "block": {
            "verdict": "SURVIVES_v0",
            "note": "this row does-not-self-upgrade pending re-audit",
        }
    }
    ftoks: list[Token] = []
    collect_tokens(fenced_sample, "", None, ftoks)
    check("fenced hard token", [t.fenced for t in ftoks if t.kind == "hard"], [True])

    # --- end-to-end decision matrix (synthetic, no repo) ---
    import tempfile

    def build(tmp: Path, name: str, result: dict, audit: str | None) -> Path:
        d = tmp / name
        (d / "results").mkdir(parents=True)
        (d / "results" / f"{name}_results.json").write_text(json.dumps(result))
        if audit is not None:
            (d / "audit_verdict.md").write_text(audit)
        return d

    with tempfile.TemporaryDirectory() as tmpd:
        tmp = Path(tmpd)
        # HARD + CONTRADICT audit -> violation
        v, _, _ = evaluate_sim(
            build(tmp, "bite_contradict", {"discriminator": {"verdict": "SURVIVES_v0"}},
                  "Bottom line: VERDICT REJECTED as stated.")
        )
        check("hard+contradict bites", v is not None, True)
        # HARD + NEUTRAL (commit_ready) audit -> violation
        v, _, _ = evaluate_sim(
            build(tmp, "bite_neutral", {"x_earned": True},
                  "BOTTOM LINE: COMMIT_READY at scratch_diagnostic ceiling.")
        )
        check("hard+neutral bites", v is not None, True)
        # HARD + NO audit -> violation
        v, _, _ = evaluate_sim(build(tmp, "bite_noaudit", {"x_earned": True}, None))
        check("hard+no-audit bites", v is not None, True)
        # HARD + AFFIRM audit -> clean
        v, _, _ = evaluate_sim(
            build(tmp, "clean_affirm", {"x_earned": True}, "Verdict: GENUINE-WITH-CAVEATS")
        )
        check("hard+affirm clean", v is None, True)
        # HARD + fence + CONTRADICT audit -> exempt (clean)
        v, _, _ = evaluate_sim(
            build(tmp, "clean_fenced",
                  {"blk": {"y_earned": True, "n": "by_construction scratch"}},
                  "Bottom line: REJECTED.")
        )
        check("hard+fence exempt", v is None, True)
        # SOFT load_bearing + DIES-accepted audit (has file) -> clean (no false positive)
        v, _, _ = evaluate_sim(
            build(tmp, "clean_soft_dies",
                  {"TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing"}},
                  "VERDICT: `DIES_v2` accepted.")
        )
        check("soft+death-with-file clean", v is None, True)
        # SOFT load_bearing + NO audit -> violation
        v, _, _ = evaluate_sim(
            build(tmp, "bite_soft_noaudit",
                  {"TOOL_INTEGRATION_DEPTH": {"z3": "load_bearing"}}, None)
        )
        check("soft+no-audit bites", v is not None, True)
        # No tokens at all -> clean (skipped)
        v, _, _ = evaluate_sim(build(tmp, "clean_empty", {"all_pass": True}, None))
        check("no-tokens clean", v is None, True)

    if failures:
        print("SELFTEST FAIL:")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"SELFTEST PASS: {len(cases) + 11} checks")
    return 0


# ------------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="GATE 1 two-tier authority: positive result-JSON verdict tokens "
        "must be affirmatively confirmed by a committed audit verdict."
    )
    parser.add_argument(
        "--sims-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent / SIMS_ROOT,
        help="Sims root dir (default: <repo>/system_v6/sims).",
    )
    parser.add_argument("--selftest", action="store_true", help="Run built-in tests and exit.")
    parser.add_argument("--json", action="store_true", help="Emit the full {ok, violations} JSON.")
    args = parser.parse_args()

    if args.selftest:
        return selftest()

    report = run_gate(args.sims_root.expanduser().resolve())
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(
            f"validate_two_tier_authority: scanned {report['sims_scanned']} sims, "
            f"{len(report['violations'])} violation(s)"
        )
        for v in report["violations"]:
            print(f"  VIOLATION {v['sim']}: {v['reason']} | audit={v['audit_decision']}")
            print(f"    decisive: {v['decisive_sentence']}")
            for p in v["hard_token_paths"]:
                print(f"    hard: {p}")
            for p in v["soft_token_paths"]:
                print(f"    soft: {p}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
