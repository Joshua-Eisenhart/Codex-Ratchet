#!/usr/bin/env python3
"""Universal stage CLI for the serialized physics spine (Phase 1: dummy payloads).

Tombstone-and-boot: each stage runs as its OWN process, verifies the prior
stage's artifact by RE-HASHING it from disk (not trusting the ledger claim),
writes its own immutable artifact, publishes a manifest to the sqlite ledger,
and exits. No live memory pointers between stages ever exist.

Chain invariant: SHA256(input_artifact_on_disk) == output_digest recorded by
the prior stage. A mismatch is a fatal fail-closed abort (exit 1).

Phase 1 payloads are MOCK bytes — this spine proves the container boundaries
(digest chain, tombstoning, fail-closed halt, park/reject classification)
before any physics exists. Real stages replace the payload block only.

Ledger: stdlib sqlite3 (agentfs_sdk does not exist as an installed package —
verified 2026-07-22; the schema mirrors the AgentFS kv design so a later Lev
AgentFS backend is a drop-in).

Exit: 0 stage bound, 1 fail-closed abort, 2 usage.
"""
import argparse
import hashlib
import json
import os
import sqlite3
import sys

STAGES = ("julia", "jax", "pysindy", "z3")


def hash_artifact(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()


def ledger(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = sqlite3.connect(db_path)
    db.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return db


def kv_get(db, key):
    row = db.execute("SELECT value FROM kv WHERE key = ?", (key,)).fetchone()
    return json.loads(row[0]) if row else None


def kv_set(db, key, value):
    db.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
               (key, json.dumps(value, sort_keys=True, separators=(",", ":"))))
    db.commit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=STAGES)
    p.add_argument("--run-id", required=True)
    p.add_argument("--state-db", required=True)
    p.add_argument("--force-fail", action="store_true",
                   help="z3 only: simulate a failed proof — exit 1 WITHOUT publishing (fail-closed)")
    args = p.parse_args()

    db = ledger(args.state_db)
    art_dir = os.path.join(os.path.dirname(args.state_db), "..", "artifacts", args.run_id)
    art_dir = os.path.normpath(art_dir)
    os.makedirs(art_dir, exist_ok=True)

    # 1. CHAIN OF CUSTODY — re-derive, don't trust (genesis stage 'julia' has no input).
    input_digest = None
    if args.stage != "julia":
        prior = kv_get(db, f"runs/{args.run_id}/current")
        if not prior:
            print(f"[FATAL] {args.stage}: no prior state for run {args.run_id}; refusing to run.",
                  file=sys.stderr)
            return 1
        actual = hash_artifact(prior["artifact_path"])
        if actual != prior["output_digest"]:
            print(f"[FATAL] {args.stage}: digest mismatch on {prior['artifact_path']} — "
                  f"recorded {str(prior['output_digest'])[:8]} vs on-disk {str(actual)[:8]}. "
                  f"Handoff compromised; failing closed.", file=sys.stderr)
            return 1
        input_digest = actual
        print(f"[+] {args.stage}: verified input digest {actual[:8]} (re-hashed from disk)")

    # 2. PAYLOAD (Phase 1: mock bytes; real physics replaces ONLY this block).
    out_path = os.path.join(art_dir, f"{args.stage}_output.dat")
    with open(out_path, "wb") as f:
        f.write(f"MOCK_DATA_FOR_{args.stage.upper()}".encode())

    proof_status = None
    if args.stage == "z3":
        if args.force_fail:
            # Simulated proof failure: fail closed BEFORE publishing, so the
            # ledger holds no z3 receipt -> ClaimGate classifies the run PARKED.
            print("[-] z3: proof FAILED (forced) — bounds breached; halting without publishing.",
                  file=sys.stderr)
            return 1
        proof_status = "UNSAT"

    # 3. PUBLISH MANIFEST (ledger + JSON receipt mirror).
    manifest = {
        "stage": args.stage,
        "run_id": args.run_id,
        "artifact_path": out_path,
        "input_digest": input_digest,
        "output_digest": hash_artifact(out_path),
        "proof_status": proof_status,
        "schema_version": "1.0",
    }
    kv_set(db, f"runs/{args.run_id}/stages/{args.stage}", manifest)
    kv_set(db, f"runs/{args.run_id}/current", manifest)
    rc_dir = os.path.normpath(os.path.join(os.path.dirname(args.state_db), "..", "receipts", args.run_id))
    os.makedirs(rc_dir, exist_ok=True)
    with open(os.path.join(rc_dir, f"{args.stage}.json"), "w") as f:
        json.dump(manifest, f, sort_keys=True, indent=1)

    print(f"[+] {args.stage.upper()} bound. digest {manifest['output_digest'][:8]} -> tombstone.")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
