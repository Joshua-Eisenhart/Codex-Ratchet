#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple


REQ_RE = re.compile(r"RQ-\d{3}")
RANGE_RE = re.compile(r"`(RQ-\d{3})\.\.(RQ-\d{3})`")
INLINE_RANGE_RE = re.compile(r"(RQ-\d{3})\.\.(RQ-\d{3})")
OWNER_LINE_RE = re.compile(r"-\s+`([^`]+)`\s+owns:\s+(.+)")


@dataclass(frozen=True)
class NormativeClause:
    req_id: str
    owner_doc: str
    clause: str


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def expand_range(a: str, b: str) -> List[str]:
    ia = int(a.split("-")[1])
    ib = int(b.split("-")[1])
    return [f"RQ-{n:03d}" for n in range(ia, ib + 1)]


def parse_requirements(ledger_text: str) -> List[str]:
    return sorted(set(REQ_RE.findall(ledger_text)))


def parse_owner_map(owner_text: str) -> Tuple[Dict[str, Set[str]], Dict[str, str]]:
    req_to_docs: Dict[str, Set[str]] = {}
    doc_to_line: Dict[str, str] = {}
    for line in owner_text.splitlines():
        m = OWNER_LINE_RE.search(line)
        if not m:
            continue
        doc = m.group(1).strip()
        doc_to_line[doc] = line.strip()
        for a, b in RANGE_RE.findall(line):
            for rid in expand_range(a, b):
                req_to_docs.setdefault(rid, set()).add(doc)
    return req_to_docs, doc_to_line


def parse_normative_clauses(owner_doc_path: Path) -> List[NormativeClause]:
    out: List[NormativeClause] = []
    for raw in load_text(owner_doc_path).splitlines():
        line = raw.strip()
        if not line:
            continue
        reqs: Set[str] = set()
        for a, b in INLINE_RANGE_RE.findall(line):
            reqs.update(expand_range(a, b))
        reqs.update(REQ_RE.findall(line))
        reqs = set(sorted(reqs))
        if not reqs:
            continue
        for req_id in sorted(reqs):
            out.append(
                NormativeClause(
                    req_id=req_id,
                    owner_doc=owner_doc_path.name,
                    clause=line,
                )
            )
    return out


def normalize_clause(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--spec-dir",
        default="system_v3/specs",
        help="Path to spec directory",
    )
    parser.add_argument(
        "--init-baseline",
        action="store_true",
        help="Initialize normative hash baseline file",
    )
    args = parser.parse_args()

    spec_dir = Path(args.spec_dir).resolve()
    ledger_path = spec_dir / "01_REQUIREMENTS_LEDGER.md"
    owner_path = spec_dir / "02_OWNERSHIP_MAP.md"
    reports_dir = spec_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    baseline_path = spec_dir / "_normative_hash_baseline.json"

    ledger_text = load_text(ledger_path)
    owner_text = load_text(owner_path)

    all_reqs = parse_requirements(ledger_text)
    global_ids = {
        "RQ-001",
        "RQ-002",
        "RQ-003",
        "RQ-004",
        "RQ-010",
        "RQ-011",
        "RQ-012",
        "RQ-013",
        "RQ-014",
    }

    req_to_docs, _ = parse_owner_map(owner_text)

    owner_collision = []
    orphan_requirements = []
    for rid in all_reqs:
        if rid in global_ids:
            continue
        docs = sorted(req_to_docs.get(rid, set()))
        if len(docs) == 0:
            orphan_requirements.append({"req_id": rid, "reason": "no_owner"})
        elif len(docs) > 1:
            owner_collision.append({"req_id": rid, "owners": docs})

    owner_docs = sorted({doc for docs in req_to_docs.values() for doc in docs})
    clauses: List[NormativeClause] = []
    missing_owner_doc_files = []
    for doc in owner_docs:
        p = spec_dir / doc
        if not p.exists():
            missing_owner_doc_files.append(doc)
            continue
        clauses.extend(parse_normative_clauses(p))

    # Requirement presence in owner docs
    owner_req_presence = {}
    for rid, docs in sorted(req_to_docs.items()):
        if rid in global_ids:
            continue
        for doc in sorted(docs):
            owner_req_presence.setdefault(doc, set()).add(rid)

    clauses_by_doc_req = {}
    for c in clauses:
        clauses_by_doc_req.setdefault((c.owner_doc, c.req_id), []).append(c.clause)

    missing_owner_clauses = []
    for doc, reqs in sorted(owner_req_presence.items()):
        for rid in sorted(reqs):
            if (doc, rid) not in clauses_by_doc_req:
                missing_owner_clauses.append(
                    {
                        "owner_doc": doc,
                        "req_id": rid,
                        "reason": "owner_doc_missing_normative_clause",
                    }
                )

    # Redundancy report across owner docs
    norm_clause_map: Dict[str, List[Dict[str, str]]] = {}
    for c in clauses:
        key = normalize_clause(c.clause)
        norm_clause_map.setdefault(key, []).append(
            {"req_id": c.req_id, "owner_doc": c.owner_doc, "clause": c.clause}
        )
    duplicate_normative_clauses = []
    for key, items in sorted(norm_clause_map.items()):
        if len(items) > 1:
            docs = sorted({i["owner_doc"] for i in items})
            if len(docs) > 1:
                duplicate_normative_clauses.append(
                    {
                        "normalized_clause": key,
                        "instances": sorted(
                            items, key=lambda x: (x["owner_doc"], x["req_id"], x["clause"])
                        ),
                    }
                )

    # Normative hash (first clause line per owner/req key)
    by_key: Dict[Tuple[str, str], str] = {}
    for c in sorted(clauses, key=lambda x: (x.owner_doc, x.req_id, x.clause)):
        key = (c.owner_doc, c.req_id)
        if key not in by_key:
            by_key[key] = normalize_clause(c.clause)
    norm_records = sorted(
        [(req_id, owner_doc, clause) for (owner_doc, req_id), clause in by_key.items()],
        key=lambda x: (x[0], x[1], x[2]),
    )
    payload = json.dumps(norm_records, separators=(",", ":"), ensure_ascii=True)
    normative_hash = hashlib.sha256(payload.encode("ascii")).hexdigest()
    normative_hash_report = {
        "normative_hash_sha256": normative_hash,
        "clause_count": len(norm_records),
        "spec_dir": str(spec_dir),
    }

    baseline = None
    drift = None
    if baseline_path.exists():
        baseline = json.loads(load_text(baseline_path))
        drift = baseline.get("normative_hash_sha256") != normative_hash

    if args.init_baseline or not baseline_path.exists():
        baseline_obj = {
            "normative_hash_sha256": normative_hash,
            "clause_count": len(norm_records),
        }
        baseline_path.write_text(
            json.dumps(baseline_obj, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        baseline = baseline_obj
        drift = False

    normative_hash_report["baseline_hash_sha256"] = baseline.get("normative_hash_sha256")
    normative_hash_report["drift_detected"] = bool(drift)

    owner_collision_report = {
        "count": len(owner_collision),
        "items": owner_collision,
    }
    orphan_requirements_report = {
        "count": len(orphan_requirements),
        "items": orphan_requirements,
    }
    redundancy_report = {
        "missing_owner_doc_files": sorted(missing_owner_doc_files),
        "missing_owner_clauses_count": len(missing_owner_clauses),
        "missing_owner_clauses": sorted(
            missing_owner_clauses, key=lambda x: (x["owner_doc"], x["req_id"])
        ),
        "duplicate_normative_clauses_count": len(duplicate_normative_clauses),
        "duplicate_normative_clauses": duplicate_normative_clauses,
    }

    (reports_dir / "owner_collision_report.json").write_text(
        json.dumps(owner_collision_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "orphan_requirements_report.json").write_text(
        json.dumps(orphan_requirements_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "normative_hash_report.json").write_text(
        json.dumps(normative_hash_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (reports_dir / "redundancy_report.json").write_text(
        json.dumps(redundancy_report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    summary = {
        "owner_collision_count": owner_collision_report["count"],
        "orphan_requirements_count": orphan_requirements_report["count"],
        "missing_owner_clause_count": redundancy_report["missing_owner_clauses_count"],
        "duplicate_normative_clause_count": redundancy_report[
            "duplicate_normative_clauses_count"
        ],
        "normative_hash": normative_hash_report["normative_hash_sha256"],
        "drift_detected": normative_hash_report["drift_detected"],
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
