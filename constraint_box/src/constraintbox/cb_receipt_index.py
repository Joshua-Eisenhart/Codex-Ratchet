#!/usr/bin/env python3
"""cb_receipt_index — the exact index CB lacks, stdlib only.

Two index layers already exist and neither answers CB's questions:
CocoIndex gives semantic retrieval over prose (wiki, Codex-Ratchet),
and codebase-memory-mcp gives a tree-sitter code knowledge graph.
Both are LEADS layers. CB needs EXACT relational lookup over receipts:
  - which runs touched artifact sha X
  - which receipts share a lease / tree_id
  - what changed between run A and run B
  - which claims are PARKED, and on which missing artifact
Those are index hits on structured fields, not similarity over text.

Design constraints taken from the owner: super lean, maintainable,
most aligned with Python. So: stdlib sqlite3, no ORM, no third-party
dependency, one file, WAL off (single-writer), schema versioned in the
database itself. Anything CocoIndex does better is left to CocoIndex.

Schema
  runs(run_id PK, root, ts, receipt_sha256)
  artifacts(sha256, path, size, run_id)         idx: sha256, path
  receipts(run_id, stage, artifact_path, sha256, verdict, reason, ts)
                                                idx: sha256, verdict,
                                                     run_id
  leases(tree_id, run_id, lease_sha256, ttl)    idx: tree_id
promotion_allowed=false: this is a lookup index, never an authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sqlite3, sys, time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT);
CREATE TABLE IF NOT EXISTS runs(
  run_id TEXT PRIMARY KEY, root TEXT, ts REAL, receipt_sha256 TEXT);
CREATE TABLE IF NOT EXISTS artifacts(
  sha256 TEXT, path TEXT, size INTEGER, run_id TEXT);
CREATE TABLE IF NOT EXISTS receipts(
  run_id TEXT, stage TEXT, artifact_path TEXT, sha256 TEXT,
  verdict TEXT, reason TEXT, ts REAL);
CREATE TABLE IF NOT EXISTS leases(
  tree_id TEXT, run_id TEXT, lease_sha256 TEXT, ttl REAL);
CREATE INDEX IF NOT EXISTS ix_art_sha  ON artifacts(sha256);
CREATE INDEX IF NOT EXISTS ix_art_path ON artifacts(path);
CREATE INDEX IF NOT EXISTS ix_rec_sha  ON receipts(sha256);
CREATE INDEX IF NOT EXISTS ix_rec_verd ON receipts(verdict);
CREATE INDEX IF NOT EXISTS ix_rec_run  ON receipts(run_id);
CREATE INDEX IF NOT EXISTS ix_lease_tree ON leases(tree_id);
"""
VERDICTS = ("PARKED", "BLOCKED", "ADMITTED", "RELEASED", "HOLD",
            "ELIGIBLE", "AGREE", "UNRESOLVED", "TREE_MISMATCH",
            "EVALUATION_ERROR")

def sha_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def walk_json(node, path="$"):
    if isinstance(node, dict):
        yield path, node
        for k, v in node.items():
            yield from walk_json(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_json(v, f"{path}[{i}]")

SCHEMA_VERSION = "cb.receipt-index.v1"


def index_run(con: sqlite3.Connection, root: Path) -> dict:
    """Idempotent: re-indexing a run replaces its rows, never duplicates."""
    run_id = root.name
    for tbl in ("artifacts", "receipts", "leases"):
        con.execute(f"DELETE FROM {tbl} WHERE run_id=?", (run_id,))
    files = [p for p in root.rglob("*") if p.is_file()]
    con.execute("INSERT OR REPLACE INTO runs VALUES(?,?,?,?)",
                (run_id, str(root), time.time(), ""))
    arts = []
    for p in files:
        arts.append((sha_file(p), str(p.relative_to(root)),
                     p.stat().st_size, run_id))
    con.executemany("INSERT INTO artifacts VALUES(?,?,?,?)", arts)
    recs, leases = [], []
    for p in files:
        if p.suffix != ".json":
            continue
        try:
            doc = json.loads(p.read_text())
        except Exception:
            continue
        for jpath, obj in walk_json(doc):
            v = (obj.get("status") or obj.get("verdict")
                 or obj.get("disposition") or obj.get("agreement"))
            if v is None:
                for boolean_field in ("passed", "all_pass", "release_allowed",
                                      "integrity_pass"):
                    if isinstance(obj.get(boolean_field), bool):
                        v = "ADMITTED" if obj[boolean_field] else "BLOCKED"
                        break
            if isinstance(v, str) and v.upper() in VERDICTS:
                recs.append((run_id, jpath[:120],
                             str(p.relative_to(root)),
                             obj.get("sha256") or obj.get("result_sha256")
                             or "", v.upper(),
                             str(obj.get("reason") or
                                 obj.get("error") or "")[:200],
                             time.time()))
            if obj.get("schema") == "constraintbox.tree-lease.v1":
                leases.append((obj.get("tree_id"), run_id,
                               obj.get("lease_sha256"),
                               obj.get("ttl_seconds")))
    con.executemany("INSERT INTO receipts VALUES(?,?,?,?,?,?,?)", recs)
    con.executemany("INSERT INTO leases VALUES(?,?,?,?)", leases)
    con.commit()
    return {"run_id": run_id, "files": len(files), "verdict_rows": len(recs),
            "leases": len(leases)}

QUERIES = {
 "runs_touching_sha": "SELECT DISTINCT run_id, path FROM artifacts WHERE sha256=?",
 "duplicate_artifacts": """SELECT sha256, COUNT(DISTINCT run_id) n,
      MIN(path) FROM artifacts GROUP BY sha256 HAVING n>1 ORDER BY n DESC LIMIT 10""",
 "verdict_census": "SELECT verdict, COUNT(*) FROM receipts GROUP BY verdict ORDER BY 2 DESC",
 "parked_with_reason": """SELECT run_id, artifact_path, reason FROM receipts
      WHERE verdict IN ('PARKED','BLOCKED','TREE_MISMATCH',
      'EVALUATION_ERROR','UNRESOLVED') LIMIT 8""",
 "runs_sharing_tree": """SELECT tree_id, GROUP_CONCAT(run_id) FROM leases
      GROUP BY tree_id HAVING COUNT(*)>1""",
}

def agent_context(con: sqlite3.Connection, question: str, arg: str | None,
                  budget_rows: int = 20) -> dict:
    """Return the few rows an agent needs, with the byte cost stated.
    This is the anti-context-rot surface: constrain the INPUT, not the
    answer."""
    sql = QUERIES[question]
    rows = con.execute(sql, (arg,) if arg else ()).fetchall()[:budget_rows]
    payload = {"question": question, "arg": arg, "rows": rows,
               "row_count": len(rows), "truncated_at": budget_rows,
               "schema": SCHEMA_VERSION,
               "claim_ceiling": "index lookup only; rows are pointers, "
                                "read the artifacts before any load-bearing "
                                "claim"}
    payload["bytes"] = len(json.dumps(payload))
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, type=Path)
    ap.add_argument("--index", nargs="*", type=Path, default=[])
    ap.add_argument("--query", default=None)
    ap.add_argument("--arg", default=None)
    a = ap.parse_args()
    con = sqlite3.connect(a.db)
    con.executescript(SCHEMA)
    for root in a.index:
        t0 = time.time()
        info = index_run(con, root)
        info["seconds"] = round(time.time() - t0, 2)
        print("indexed:", info)
    if a.query:
        t0 = time.time()
        cur = con.execute(QUERIES[a.query], (a.arg,) if a.arg else ())
        rows = cur.fetchall()
        dt = (time.time() - t0) * 1000
        for r in rows:
            print("  ", r)
        print(f"  ({len(rows)} rows in {dt:.2f} ms)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
