#!/usr/bin/env python3
"""strict_receipt_consumer — CB foundation repair (CBIMP-1..3).

Three defects motivate this consumer, each reproduced with an
independent mutation canary in this container:

  CBIMP-1  DECLARED-HASH TRUST. Shipped consumers compare stored hash
           strings to each other, or read stored booleans, instead of
           recomputing digests from the artifact bytes they claim to
           verify. Canary: flipping one boolean inside a declared
           result file (sha 1558f20f... -> 2e8f3354...) left the
           shipped target verifier at 9/9 PASS.
  CBIMP-2  ARTIFACT-ROOT UNCLEANLINESS. A generated file left in a
           shipped run root silently changes the artifact set (the
           27/28 federated regression). No consumer treats
           present-but-undeclared files as a defect.
  CBIMP-3  STORED-VERDICT CONSUMPTION. Checks named
           "consumer_recomputed_checks" actually read
           row["consumer_checks"]["passed"]. A verdict a producer
           wrote about itself is not evidence.

This consumer does the opposite of each:
  1. harvests EVERY (path, sha256) pair declared anywhere in the
     receipt tree, recursively, whatever the schema;
  2. recomputes each digest from the bytes on disk;
  3. classifies the run root: MATCH / MISMATCH / DECLARED-ABSENT /
     PRESENT-UNDECLARED;
  4. recomputes derivable aggregates (all_pass = AND of checks) and
     REFUSES non-derivable stored verdicts, reporting them as
     unverifiable rather than passing them;
  5. emits verdict + defect list; exit 1 on any defect.
Schema-agnostic by design: it must work on receipts it has never
seen, because the point is to survive the next format.
promotion_allowed=false.
"""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys
from pathlib import Path

from .ledger import HashChainLedger

HEX64 = re.compile(r"^[0-9a-f]{64}$")
IGNORE_DIRS = {"__pycache__", ".git", "mplconfig", "numba_cache"}
# names that are self-referential digests, not artifact digests
SELF_KEYS = {"result_sha256_self", "self_sha256", "receipt_sha256",
             "audited_result_sha256", "retained_head_sha256"}

def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

BIND_CTX = ("source_bindings", "provenance", "candidate_patch",
            "inputs_sealed", "package_root", "source_files")


def verify_receipt_ledger(receipt: object, root: Path) -> tuple[bool, str, set[str]]:
    """Verify the controller-retained ledger using the canonical ledger primitive."""
    if not isinstance(receipt, dict) or not isinstance(receipt.get("ledger"), dict):
        return True, "no ledger declaration", set()
    ledger = receipt["ledger"]
    path_text = ledger.get("path")
    head_text = ledger.get("head_path")
    if not isinstance(path_text, str) or not isinstance(head_text, str):
        return False, "ledger binding is incomplete", set()
    path = Path(path_text).resolve()
    head = Path(head_text).resolve()
    try:
        path.relative_to(root)
        head.relative_to(root)
    except ValueError:
        return False, "ledger binding escapes run root", set()
    valid, reason = HashChainLedger(path, head).verify()
    retained = ledger.get("retained_head_sha256")
    if valid and isinstance(retained, str) and head.read_text(encoding="ascii").strip() != retained:
        return False, "retained ledger head differs from receipt", set()
    return valid, reason, {str(path.relative_to(root)), str(head.relative_to(root))}


def harvest(node, out, keyhint=None, ctx=""):
    """Collect (name, digest) pairs from any receipt shape."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, str) and HEX64.match(v):
                if k in SELF_KEYS:
                    continue
                name = k
                if k.endswith("_sha256") and k != "sha256":
                    name = k[:-7]
                elif k in ("sha256", "digest", "hash"):
                    name = (node.get("path") or node.get("file")
                            or node.get("relative") or node.get("name")
                            or keyhint)
                if name:
                    out.append((str(name), v, ctx))
            elif isinstance(v, dict) and all(
                    isinstance(x, str) and HEX64.match(x)
                    for x in v.values()) and v:
                for fname, dg in v.items():
                    out.append((fname, dg, ctx + "." + k))
            else:
                harvest(v, out, keyhint=k, ctx=ctx + "." + k)
    elif isinstance(node, list):
        for v in node:
            harvest(v, out, keyhint=keyhint, ctx=ctx)

def index_files(root: Path):
    idx = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = str(p.relative_to(root))
            idx.setdefault(fn, []).append(rel)
            idx.setdefault(rel, [rel])
    return idx

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-root", required=True, type=Path)
    ap.add_argument("--receipt", type=Path, default=None,
                    help="defaults to every *RECEIPT*.json in run root")
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--strict-cleanliness", action="store_true",
                    help="treat present-but-undeclared files as defects")
    a = ap.parse_args()
    root: Path = a.run_root.resolve()
    receipts = ([a.receipt] if a.receipt else
                sorted(p for p in root.glob("*.json")
                       if "RECEIPT" in p.name.upper()))
    if not receipts:
        receipts = sorted(root.glob("*.json"))
    declared = []
    for r in receipts:
        try:
            harvest(json.loads(r.read_text()), declared)
        except Exception as e:
            declared.append((f"<unreadable:{r.name}>", "0" * 64, ""))
    idx = index_files(root)
    ledger_valid, ledger_reason, ledger_files = (True, "no ledger declaration", set())
    for r in receipts:
        try:
            ledger_valid, ledger_reason, declared_ledger_files = verify_receipt_ledger(
                json.loads(r.read_text()), root
            )
        except Exception as exc:
            ledger_valid, ledger_reason, declared_ledger_files = False, f"ledger unreadable: {exc}", set()
        ledger_files.update(declared_ledger_files)
    seen_rel = set()
    match, mismatch, absent, nonartifact = [], [], [], []
    STREAM = ("stdout", "stderr", "argv", "command", "source", "input",
              "fixture", "zip", "package", "archive")
    external_binding, ambiguous = [], []
    binding_scope = []
    for name, digest, ctx in declared:
        if any(t in ctx.lower() for t in BIND_CTX):
            binding_scope.append({"declared": name, "context": ctx[:60]})
            continue
        base = os.path.basename(name)
        has_sep = ("/" in name) or ("\\" in name)
        if has_sep:
            # a path-qualified declaration must resolve EXACTLY inside
            # the run root; otherwise it binds a package-root file and
            # is not this run root's artifact (basename matching here
            # produced false mismatches — do not do it)
            cands = [name] if (root / name).is_file() else []
            if not cands:
                external_binding.append({"declared": name})
                continue
        else:
            hits = [r for r in idx.get(base, []) if (root / r).is_file()]
            hits = sorted(set(hits))
            if len(hits) == 0:
                looks_file = bool(os.path.splitext(base)[1]) and not any(
                    t in name.lower() for t in STREAM)
                (absent if looks_file else nonartifact).append(
                    {"declared": name, "sha256": digest})
                continue
            if len(hits) > 1:
                ambiguous.append({"declared": name, "candidates": hits[:4]})
                continue
            cands = hits
        rel = cands[0]
        actual = sha_file(root / rel)
        seen_rel.add(rel)
        if actual == digest:
            match.append({"path": rel, "sha256": digest})
        else:
            mismatch.append({"path": rel, "declared": digest,
                             "actual": actual})
    all_rel = {r for k, v in idx.items() for r in v if os.sep in k or k == v[0]}
    all_rel = set()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]
        for fn in filenames:
            all_rel.add(str((Path(dirpath) / fn).relative_to(root)))
    receipt_files = {
        str(r.resolve().relative_to(root))
        for r in receipts
        if r.resolve().is_relative_to(root)
    }
    undeclared = sorted(all_rel - seen_rel - ledger_files - receipt_files)
    # recomputable aggregates + refused stored verdicts
    refused, recomputed = [], []
    for r in receipts:
        try:
            d = json.loads(r.read_text())
        except Exception:
            continue
        def scan(node, path="$"):
            if isinstance(node, dict):
                checks = node.get("checks")
                if isinstance(checks, list) and checks and all(
                        isinstance(c, dict) and "passed" in c
                        for c in checks):
                    derived = all(bool(c["passed"]) for c in checks)
                    stored = node.get("passed")
                    recomputed.append({"at": path, "derived_all_pass":
                                       derived, "stored": stored,
                                       "agrees": stored is None
                                       or bool(stored) == derived})
                for k, v in node.items():
                    if k in ("passed", "all_pass",
                             "all_consumer_checks_pass") and \
                            isinstance(v, bool) and not isinstance(
                                node.get("checks"), list):
                        refused.append(f"{path}.{k}")
                    scan(v, f"{path}.{k}")
            elif isinstance(node, list):
                for i, v in enumerate(node):
                    scan(v, f"{path}[{i}]")
        scan(d, r.name)
    defects = []
    if mismatch:
        defects.append(f"CBIMP-1 hash mismatch on {len(mismatch)} "
                       f"declared artifact(s)")
    if absent:
        defects.append(f"declared-but-absent: {len(absent)}")
    if a.strict_cleanliness and undeclared:
        defects.append(f"CBIMP-2 present-but-undeclared: "
                       f"{len(undeclared)}")
    bad_agg = [r for r in recomputed if not r["agrees"]]
    if bad_agg:
        defects.append(f"CBIMP-3 stored aggregate disagrees with "
                       f"recomputation: {len(bad_agg)}")
    if not ledger_valid:
        defects.append(f"invalid-ledger-chain: {ledger_reason}")
    out = {"schema": "cb.strict-recomputing-consumer.v1",
           "run_root": str(root),
           "receipts_read": [r.name for r in receipts],
           "declared_digests": len(declared),
           "recomputed_match": len(match),
           "recomputed_mismatch": mismatch[:20],
           "declared_absent": absent[:20],
           "non_artifact_digests_skipped": len(nonartifact),
           "declared_outside_run_root": len(external_binding),
           "package_scope_bindings_not_run_artifacts": len(binding_scope),
           "ambiguous_basename_declarations": ambiguous[:10],
           "present_but_undeclared": undeclared[:20],
           "present_but_undeclared_count": len(undeclared),
           "aggregates_recomputed": recomputed[:20],
           "stored_verdicts_refused_as_evidence": sorted(set(refused))[:20],
           "stored_verdicts_refused_count": len(set(refused)),
           "ledger_verified": ledger_valid,
           "ledger_verification": ledger_reason,
           "defects": defects,
           "passed": not defects,
           "promotion_allowed": False,
           "claim_ceiling": "byte-level receipt integrity and artifact "
                            "set exactness only; no scientific claim"}
    a.output.write_text(json.dumps(out, indent=1, sort_keys=True))
    print(f"declared={len(declared)} match={len(match)} "
          f"mismatch={len(mismatch)} absent={len(absent)} "
          f"undeclared={len(undeclared)} "
          f"refused_stored_verdicts={len(set(refused))}")
    print("DEFECTS:", defects if defects else "none")
    return 1 if defects else 0

if __name__ == "__main__":
    sys.exit(main())
