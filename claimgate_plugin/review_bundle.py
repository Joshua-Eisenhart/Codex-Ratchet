#!/usr/bin/env python3
"""REVIEW BUNDLE — generated from disk and git, never transcribed from prose.

Why this file exists as CODE rather than as a hand-written JSON: the previous
bundle (schema claimgate_review_bundle_v1) was written by copying numbers out of
a narrative. Four of its counts, four of its digests and one commit SHA were
wrong by the time anyone read it, and nothing in the repo could tell. The SHA was
worse than stale: `ff8e389643aa0f5f0b0c2ad0e50a76e1c1e88a3f` names no object in
this repository. Its first 9 characters match the real commit, which is exactly
what a short hash echoed from a log looks like after the remaining 31 characters
are invented.

So the bundle is now a MEASUREMENT, and this script is the only thing allowed to
write it:

    python3 claimgate_plugin/review_bundle.py --write     regenerate from disk
    python3 claimgate_plugin/review_bundle.py --verify     FAIL on any drift

--verify re-measures every enforced field and compares it to what the bundle
claims. Any difference is exit 1 with the field named. That is the whole point: a
number in this bundle cannot go stale silently, because the check that would have
caught it is now runnable.

WHAT IS ENFORCED (the `measured` subtree): commit SHAs and their existence, the
count ahead of the base ref, file digests, every frozen-set count both as
DECLARED and as actually counted, the fixture manifest, the CI workflow's own
stated numbers, and the bypass-regression result set.

WHAT IS NOT ENFORCED (`observed_volatile`): the gate ledger's length and wall
clock. The ledger is append-only and grows whenever any receipt is gated, so
holding it fixed would fail on correct behaviour. It is recorded, and labelled.

The CORRECTIONS section is itself falsifiable: each entry names the commit where
the stale value was true, and --verify re-reads that blob from git and checks it.
An invented correction fails the same way an invented measurement does.

Exit: 0 clean | 1 drift (or a corrections entry that does not check out) | 2 usage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BUNDLE = REPO / "claimgate_plugin" / "results" / "review_bundle_v1.json"
BASE_REF = "origin/session/r0-three-engine-probes"
WORKFLOW = REPO / ".github" / "workflows" / "three-engine-seal.yml"

# The SHA the previous bundle's covering report asserted. It resolves to nothing.
# Kept here so the absence is a STANDING check, not a one-off observation.
FABRICATED_SHA = "ff8e389643aa0f5f0b0c2ad0e50a76e1c1e88a3f"
REAL_SHA = "ff8e38964caa423587a73ad4fb32347caecd3b1a"

FROZEN_SETS = {
    "intake_supervisor/live": "claimgate_plugin/baselines/frozen_failures_intake_supervisor_live.json",
    "intake_supervisor/all": "claimgate_plugin/baselines/frozen_failures_intake_supervisor_all.json",
    "recompute_veto/live": "claimgate_plugin/baselines/frozen_failures_recompute_veto_live.json",
    "recompute_veto/all": "claimgate_plugin/baselines/frozen_failures_recompute_veto_all.json",
}

# Load-bearing files whose bytes the bundle pins.
DIGEST_PATHS = [
    "claimgate_plugin/ci_orphan_baseline.json",
    "claimgate_plugin/ci_orphan_ratchet.py",
    "claimgate_plugin/ci_receipt_sweep.py",
    "claimgate_plugin/claim_policy.json",
    "claimgate_plugin/claim_policy_gate.py",
    "claimgate_plugin/engine_witness.py",
    "claimgate_plugin/fixtures/sweep_fixture_manifest.json",
    "claimgate_plugin/hooks/post_receipt_gate.sh",
    "claimgate_plugin/run_bypass_regression.py",
    ".github/workflows/three-engine-seal.yml",
] + sorted(FROZEN_SETS.values())


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(REPO), capture_output=True,
                          text=True, check=True).stdout.strip()


def object_exists(sha: str) -> bool:
    """git cat-file -e — the only honest test that a SHA names something here."""
    return subprocess.run(["git", "cat-file", "-e", sha], cwd=str(REPO),
                          capture_output=True).returncode == 0


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_bytes())


def blob_at(commit: str, rel: str):
    """The committed bytes of `rel` at `commit`, parsed as JSON."""
    out = subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=str(REPO),
                         capture_output=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)


# --------------------------------------------------------------------------
# CORRECTIONS. Every entry is checked by --verify against the commit it names.
# `container` is the key whose LENGTH the stale number claimed to be, so the
# check re-counts rather than trusting the blob's own declared count.
# --------------------------------------------------------------------------
CORRECTIONS = [
    {
        "field": "item_6_baselines.orphan_count_at_freeze",
        "status": "STALE_ONCE_TRUE",
        "stale_value": 2851,
        "was_true_at": "8104ce80243aee944839f51b166f65ae7c9104cd",
        "path": "claimgate_plugin/ci_orphan_baseline.json",
        "container": "orphans",
        "why_it_changed": "That freeze counted the WORKING TREE. CI only ever sees committed "
                          "files, so the set was re-measured from `git ls-files` — first to "
                          "1871 from a temp clone that was not a clean checkout, then to the "
                          "current 2198 in place. ci_orphan_ratchet.py:60-62 records the same "
                          "correction at the source.",
    },
    {
        "field": "item_6_baselines.orphan_baseline_sha256",
        "status": "STALE_ONCE_TRUE",
        "stale_value": "72deee17a0fe9bf054a1442d50742ad625e074b881672b1e6c1a989543f17ad5",
        "was_true_at": "8104ce80243aee944839f51b166f65ae7c9104cd",
        "path": "claimgate_plugin/ci_orphan_baseline.json",
        "container": None,
        "why_it_changed": "Digest of the superseded 2851-entry freeze.",
    },
    {
        "field": "item_7_E9_repair.frozen_sets['intake_supervisor/all'].count_at_freeze",
        "status": "STALE_ONCE_TRUE",
        "stale_value": 46,
        "was_true_at": "2ba9129b028d70aa0353ca290fcc7b7244dc9821",
        "path": "claimgate_plugin/baselines/frozen_failures_intake_supervisor_all.json",
        "container": "failures",
        "why_it_changed": "Re-frozen from the committed set at ec9d645d4; 10 of the 46 were "
                          "untracked working-tree files CI cannot see.",
    },
    {
        "field": "item_7_E9_repair.frozen_sets['recompute_veto/all'].count_at_freeze",
        "status": "STALE_ONCE_TRUE",
        "stale_value": 17,
        "was_true_at": "2ba9129b028d70aa0353ca290fcc7b7244dc9821",
        "path": "claimgate_plugin/baselines/frozen_failures_recompute_veto_all.json",
        "container": "failures",
        "why_it_changed": "Same re-freeze; one entry was untracked.",
    },
    {
        "field": "item_4_hostile_fixtures.total_pinned",
        "status": "STALE_ONCE_TRUE",
        "stale_value": 112,
        "was_true_at": "2ba9129b028d70aa0353ca290fcc7b7244dc9821",
        "path": "claimgate_plugin/fixtures/sweep_fixture_manifest.json",
        "container": "fixtures",
        "why_it_changed": "Re-pinned from `git ls-files`; the 4 dropped entries are the "
                          "untracked fixtures now listed under _skipped_untracked.",
    },
]

# Prose claims in the previous bundle that are now false. No numeric provenance to
# re-check; they are recorded so the correction is on the record, not inferred.
CORRECTIONS_PROSE = [
    {
        "field": "covering_report.commit_sha_for 'claimgate: freeze baselines from the "
                 "COMMITTED set, not the working tree.'",
        "status": "FABRICATED",
        "stale_text": FABRICATED_SHA,
        "current_state": f"That string names NO object in this repository: `git cat-file -e "
                         f"{FABRICATED_SHA}` exits 1. The real commit is {REAL_SHA}. The two "
                         f"share exactly the 9-character short hash `ff8e38964` that "
                         f"`git log --oneline` prints; the remaining 31 characters were "
                         f"invented, not mistyped or truncated. This is the one error here that "
                         f"is a FABRICATION rather than a stale-but-once-true measurement: the "
                         f"other six describe values that git can still show were real at the "
                         f"commit they name. Enforced by git.fabricated_sha_still_absent and by "
                         f"a standing --verify check that every recorded SHA is 40 characters "
                         f"and resolves.",
    },
    {
        "field": "item_7_E9_repair.residual",
        "status": "STALE_PROSE",
        "stale_text": "The CI workflow still passes counts; migrating it is the next step and "
                      "is NOT done here.",
        "current_state": "Superseded at ec9d645d4. All four sweep invocations in "
                         ".github/workflows/three-engine-seal.yml now pass --frozen-failures "
                         "with a path+digest set, and the orphan job runs the frozen-set "
                         "ratchet. --max-failures survives in ci_receipt_sweep.py as a "
                         "DEPRECATED flag but no workflow step uses it. Enforced below by "
                         "ci_workflow.frozen_failures_baselines_referenced and "
                         "ci_workflow.max_failures_in_run_steps == 0.",
    },
    {
        "field": "item_1_branch_and_shas",
        "status": "NEVER_FILLED",
        "stale_text": "Filled in by the push step; see git_push_result below.",
        "current_state": "The placeholder was never replaced and there is no git_push_result "
                         "key in the file. The bundle shipped with an empty commit list while "
                         "its covering report carried a SHA that names no object. Item 1 is "
                         "now git.commits_ahead, every entry verified with git cat-file -e.",
    },
]


def measure() -> dict:
    """Everything enforced. Read from disk or git; nothing copied from prose."""
    head = git("rev-parse", "HEAD")
    base = git("rev-parse", BASE_REF)
    shas = git("rev-list", f"{BASE_REF}..HEAD").split()

    commits = []
    for sha in shas:
        commits.append({
            "sha": sha,
            "sha_len": len(sha),
            "exists": object_exists(sha),
            "subject": git("log", "-1", "--format=%s", sha),
        })

    frozen = {}
    for name, rel in sorted(FROZEN_SETS.items()):
        d = read_json(REPO / rel)
        frozen[name] = {
            "path": rel,
            "sha256": sha256_file(REPO / rel),
            "declared_count_at_freeze": d.get("count_at_freeze"),
            "actual_entry_count": len(d.get("failures", {})),
            "declared_matches_actual": d.get("count_at_freeze") == len(d.get("failures", {})),
        }

    ob = read_json(REPO / "claimgate_plugin" / "ci_orphan_baseline.json")
    orphan = {
        "path": "claimgate_plugin/ci_orphan_baseline.json",
        "sha256": sha256_file(REPO / "claimgate_plugin" / "ci_orphan_baseline.json"),
        "declared_count_at_freeze": ob.get("count_at_freeze"),
        "actual_entry_count": len(ob.get("orphans", {})),
        "declared_matches_actual": ob.get("count_at_freeze") == len(ob.get("orphans", {})),
        "entry_shape": "{repo-relative path: sha256 of bytes}",
        "frozen_from": "git ls-files (the committed set — all CI can see)",
    }

    mf_path = REPO / "claimgate_plugin" / "fixtures" / "sweep_fixture_manifest.json"
    mf = read_json(mf_path)
    fx = mf["fixtures"]
    nonzero = [f for f in fx if any(v != 0 for v in f["expect_exit"].values())]
    manifest = {
        "path": "claimgate_plugin/fixtures/sweep_fixture_manifest.json",
        "sha256": sha256_file(mf_path),
        "total_pinned": len(fx),
        "asserting_nonzero_exit": len(nonzero),
        "asserting_all_zero_exit": len(fx) - len(nonzero),
        "checkers": mf.get("_checkers"),
        "skipped_untracked": mf.get("_skipped_untracked"),
        "nonzero_entries": [{"path": f["path"], "sha256": f["sha256"],
                             "expect_exit": f["expect_exit"]} for f in nonzero],
        "zero_means": "the checker has nothing to say about that fixture (a control receipt, "
                      "or poison outside that checker's remit). A recorded fact, not an "
                      "endorsement.",
    }

    wf = WORKFLOW.read_text()
    run_lines = [ln for ln in wf.splitlines() if not ln.lstrip().startswith("#")]
    stated = re.search(r"(\d+)\s+entries frozen", wf)
    ci = {
        "path": ".github/workflows/three-engine-seal.yml",
        "sha256": sha256_file(WORKFLOW),
        "frozen_failures_baselines_referenced": sorted(
            set(re.findall(r"--frozen-failures\s+(\S+)", wf))),
        "max_failures_in_run_steps": sum(ln.count("--max-failures") for ln in run_lines),
        "orphan_count_stated_in_comment": int(stated.group(1)) if stated else None,
        "_comment_number_rule": "The workflow states the orphan-baseline size in prose. It is "
                                "compared to the measured set here, because a stale number in "
                                "CI is the same defect this bundle exists to fix.",
    }

    br_path = REPO / "claimgate_plugin" / "results" / "bypass_regression_v1.json"
    br = read_json(br_path)
    src = (REPO / "claimgate_plugin" / "run_bypass_regression.py").read_text()
    bypass = {
        "result_path": "claimgate_plugin/results/bypass_regression_v1.json",
        "result_sha256": sha256_file(br_path),
        "blocked": br.get("blocked"),
        "total": br.get("total"),
        "still_admitted": br.get("still_admitted"),
        "cases_defined_in_source": len(re.findall(r'^\s{4}\("b\d+"', src, re.M)),
        "per_case": [{"id": r["id"], "disposition": r["disposition"],
                      "claim_verify": r["claim_verify"], "exit": r["exit"]}
                     for r in br.get("results", [])],
    }

    return {
        "git": {
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "base_ref": BASE_REF,
            "base_ref_sha": base,
            "head_sha": head,
            "count_ahead_of_base": len(shas),
            "count_ahead_cross_checked": int(git("rev-list", "--count", f"{BASE_REF}..HEAD")),
            "commits_ahead": commits,
            "fabricated_sha_still_absent": not object_exists(FABRICATED_SHA),
            "fabricated_sha": FABRICATED_SHA,
            "real_sha_it_corrupted": REAL_SHA,
            "real_sha_exists": object_exists(REAL_SHA),
            "shared_prefix_chars": 9,
            "_sha_note": "The fabricated string shares only the 9-character short hash that "
                         "`git log --oneline` prints. The other 31 characters name nothing.",
        },
        "file_digests": {p: {"sha256": sha256_file(REPO / p),
                             "bytes": (REPO / p).stat().st_size} for p in sorted(DIGEST_PATHS)},
        "frozen_failure_sets": frozen,
        "orphan_baseline": orphan,
        "fixture_manifest": manifest,
        "ci_workflow": ci,
        "bypass_regression": bypass,
    }


def observe_volatile() -> dict:
    """Recorded, NOT enforced — these move under correct operation."""
    ledger = REPO / "claimgate_plugin" / "results" / "gate_ledger.jsonl"
    head_file = REPO / "claimgate_plugin" / "results" / "gate_ledger.head.json"
    out = {"_why_not_enforced": "The ledger is append-only and grows on every gate run. "
                                "Pinning it would fail on correct behaviour."}
    if ledger.exists():
        lines = ledger.read_bytes().splitlines()
        modes: dict[str, int] = {}
        for ln in lines:
            try:
                modes[json.loads(ln).get("key_mode", "<absent>")] = \
                    modes.get(json.loads(ln).get("key_mode", "<absent>"), 0) + 1
            except json.JSONDecodeError:
                modes["<unparseable>"] = modes.get("<unparseable>", 0) + 1
        out["ledger_lines"] = len(lines)
        out["key_mode_histogram"] = modes
        out["key_mode_meaning"] = {
            "PRODUCTION_KEYED": "key at the default path, or CLAIMGATE_LEDGER_KEY_MODE=production "
                                "AND a non-temp path",
            "TEST_KEYED": "any other key location — the FAIL-SAFE default",
            "UNKEYED": "no usable key; consistency only, never authorship",
            "<absent>": "predates the key_mode field; treat as TEST_KEYED",
        }
        out["production_key_provisioned"] = False
        out["_authorship_note"] = (
            "No line in this ledger is production-authenticated. A durable record reading "
            "KEYED from a throwaway key is exactly what later reads as production "
            "authentication.")
    if head_file.exists():
        out["head_anchor"] = read_json(head_file)
    return out


def build() -> dict:
    return {
        "schema": "claimgate_review_bundle_v2",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "supersedes": "claimgate_review_bundle_v1 (same path). v1 was transcribed from prose "
                      "and four counts, four digests and one commit SHA were wrong.",
        "_generated_by": "python3 claimgate_plugin/review_bundle.py --write",
        "_self_check": "python3 claimgate_plugin/review_bundle.py --verify",
        "_provenance_rule": "Every value under `measured` is read from disk or from git by the "
                            "generator. Nothing is transcribed. --verify re-measures and exits 1 "
                            "on any difference, so this file cannot go stale silently.",
        "claim_ceiling": "LOCAL MEASUREMENT at the pinned head_sha. The CI jobs described here "
                         "are committed workflow steps; this bundle does not observe a server-"
                         "side run and does not claim one. The gate is NOT closed: three "
                         "bypasses are open and named under bypass_regression.still_admitted.",
        "measured": measure(),
        "observed_volatile": observe_volatile(),
        "corrections": CORRECTIONS + CORRECTIONS_PROSE,
        "_corrections_rule": "Entries with a `was_true_at` commit are re-checked by --verify: it "
                             "reads that blob from git and re-counts. A correction that cannot "
                             "be demonstrated fails the same way a bad measurement does.",
        "open_not_closed_by_this_bundle": [
            "bypass b7/b8/b9 are ADMITTED_PENDING_DEPTH — an ADMITTING disposition. The "
            "content-detection rules in claim_policy.json miss a claim hidden under an "
            "ignored-metadata key, a bare integer outside a claim-bearing container, and a "
            "number encoded as a JSON string.",
            "b10 PARKS rather than blocks, and parking is the correct floor, not a fix: "
            "dispatch counting proves an engine operation ran, not that the reported output "
            "came from it.",
            "claim_policy.json is not yet a trust root. CODEOWNERS plus branch protection on "
            "claimgate_plugin/claim_policy.json are NOT in force, so the producing agent can "
            "still edit the policy that judges it.",
            "No production ledger key. Every ledger line is TEST_KEYED, UNKEYED, or predates "
            "the field.",
            "The orphan baseline is DEBT, not enforcement: 2198 committed receipts carry no "
            "durable gate-ledger record and are grandfathered.",
        ],
    }


def compare(expected, actual, path=""):
    """Deep diff. Returns [(field_path, expected, actual)]."""
    diffs = []
    if isinstance(expected, dict) and isinstance(actual, dict):
        for k in sorted(set(expected) | set(actual)):
            sub = f"{path}.{k}" if path else k
            if k not in expected:
                diffs.append((sub, "<absent from bundle>", actual[k]))
            elif k not in actual:
                diffs.append((sub, expected[k], "<absent from disk>"))
            else:
                diffs += compare(expected[k], actual[k], sub)
    elif isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            diffs.append((f"{path}.<len>", len(expected), len(actual)))
        for i, (e, a) in enumerate(zip(expected, actual)):
            diffs += compare(e, a, f"{path}[{i}]")
    elif expected != actual:
        diffs.append((path, expected, actual))
    return diffs


def check_corrections(bundle: dict) -> list[str]:
    """Re-read each correction's named commit and confirm the stale value was real."""
    problems = []
    for c in bundle.get("corrections", []):
        commit = c.get("was_true_at")
        if not commit:
            continue
        if not object_exists(commit):
            problems.append(f"corrections[{c['field']}]: commit {commit} does not exist")
            continue
        blob = blob_at(commit, c["path"])
        if blob is None:
            problems.append(f"corrections[{c['field']}]: {c['path']} absent at {commit[:9]}")
            continue
        container = c.get("container")
        if container is None:
            # digest correction — hash the committed bytes
            raw = subprocess.run(["git", "show", f"{commit}:{c['path']}"], cwd=str(REPO),
                                 capture_output=True).stdout
            got = hashlib.sha256(raw).hexdigest()
        else:
            got = len(blob[container])
        if got != c["stale_value"]:
            problems.append(f"corrections[{c['field']}]: claims the stale value was "
                            f"{c['stale_value']!r} at {commit[:9]}, but that commit holds "
                            f"{got!r}")
    return problems


def verify() -> int:
    if not BUNDLE.exists():
        print(f"review_bundle: usage — {BUNDLE} does not exist. Run --write.", file=sys.stderr)
        return 2
    bundle = read_json(BUNDLE)
    fails = []

    diffs = compare(bundle.get("measured", {}), measure())
    for field, exp, act in diffs:
        fails.append(f"DRIFT  {field}\n         bundle: {exp!r}\n         disk:   {act!r}")

    fails += [f"BAD CORRECTION  {p}" for p in check_corrections(bundle)]

    # Standing invariants that must hold regardless of what the bundle recorded.
    m = bundle.get("measured", {})
    for c in m.get("git", {}).get("commits_ahead", []):
        if not object_exists(c["sha"]):
            fails.append(f"MISSING OBJECT  {c['sha']} no longer resolves (history rewritten?)")
        if len(c["sha"]) != 40:
            fails.append(f"SHORT SHA  {c['sha']} is {len(c['sha'])} chars, not 40")
    if object_exists(FABRICATED_SHA):
        fails.append(f"UNEXPECTED  the fabricated SHA {FABRICATED_SHA} now resolves")
    for name, f in m.get("frozen_failure_sets", {}).items():
        if not f.get("declared_matches_actual"):
            fails.append(f"SELF-INCONSISTENT BASELINE  {name} declares "
                         f"{f.get('declared_count_at_freeze')} and holds "
                         f"{f.get('actual_entry_count')}")
    ob = m.get("orphan_baseline", {})
    if ob and not ob.get("declared_matches_actual"):
        fails.append(f"SELF-INCONSISTENT BASELINE  orphan baseline declares "
                     f"{ob.get('declared_count_at_freeze')} and holds "
                     f"{ob.get('actual_entry_count')}")
    ci = m.get("ci_workflow", {})
    if ci.get("orphan_count_stated_in_comment") != ob.get("actual_entry_count"):
        fails.append(f"STALE NUMBER IN CI  the workflow comment says "
                     f"{ci.get('orphan_count_stated_in_comment')} orphan entries; the frozen "
                     f"set holds {ob.get('actual_entry_count')}")
    bp = m.get("bypass_regression", {})
    if bp.get("total") != bp.get("cases_defined_in_source"):
        fails.append(f"CASE COUNT MISMATCH  result file says total={bp.get('total')} but "
                     f"run_bypass_regression.py defines {bp.get('cases_defined_in_source')}")

    if fails:
        print(f"review_bundle: FAIL — {len(fails)} drift/consistency finding(s).\n",
              file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        print(f"\nreview_bundle: the bundle no longer describes the repo. Re-measure with\n"
              f"  python3 claimgate_plugin/review_bundle.py --write\n"
              f"and read the diff before trusting it. Do NOT hand-edit the numbers.",
              file=sys.stderr)
        return 1

    n = len(m.get("git", {}).get("commits_ahead", []))
    print(f"review_bundle: clean — {n} commit SHA(s) resolve, every count and digest matches "
          f"disk, {len(bundle.get('corrections', []))} correction(s) check out against the "
          f"commits they name.")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--write", action="store_true",
                   help="regenerate the bundle from disk and git")
    g.add_argument("--verify", action="store_true",
                   help="re-measure and FAIL on drift (default)")
    args = ap.parse_args(argv)

    if args.write:
        BUNDLE.parent.mkdir(parents=True, exist_ok=True)
        BUNDLE.write_text(json.dumps(build(), indent=1) + "\n")
        print(f"review_bundle: wrote {BUNDLE.relative_to(REPO)} from measurement")
        return 0
    return verify()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
