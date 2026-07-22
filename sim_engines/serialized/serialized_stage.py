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
import re
import shutil
import sqlite3
import sys

STAGES = ("julia", "jax", "pysindy", "z3")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")  # referee finding: run_id reaches paths+keys


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
    # No per-call commit: the caller commits once so multi-key publishes are
    # atomic (referee finding: a crash between writes left the ledger torn).
    db.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
               (key, json.dumps(value, sort_keys=True, separators=(",", ":"))))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, choices=STAGES)
    p.add_argument("--run-id", required=True)
    p.add_argument("--state-db", required=True)
    p.add_argument("--force-fail", action="store_true",
                   help="z3 only: simulate a failed proof — exit 1 WITHOUT publishing (fail-closed)")
    args = p.parse_args()

    if not RUN_ID_RE.match(args.run_id):
        print(f"[FATAL] invalid run_id {args.run_id!r} (allowed: [A-Za-z0-9_-]+); "
              f"refusing path/key interpolation.", file=sys.stderr)
        return 1

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

    # 2. PAYLOAD — real stages flip on one at a time via SPINE_REAL (comma list,
    # e.g. SPINE_REAL=julia). Anything not listed stays a mock, and the manifest
    # SAYS so (payload field) — referee finding: an unlabeled mock chain could
    # reach ADMITTED. Mocks may exercise the spine; they may never enter canon.
    real_stages = set(filter(None, os.environ.get("SPINE_REAL", "").split(",")))
    payload = "real" if args.stage in real_stages else "mock"
    m1 = {}
    if args.stage == "julia" and payload == "real":
        # Phase 2: the Catlab ratchet — Gate M1 proof + Arrow mask artifact.
        import subprocess
        out_path = os.path.join(art_dir, "julia_output.arrow")
        repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        julia_bin = shutil.which("julia")  # referee finding: no hardcoded binary path
        if not julia_bin:
            print("[FATAL] julia: no `julia` on PATH; failing closed.", file=sys.stderr)
            return 1
        proc = subprocess.run(
            [julia_bin, f"--project={repo}/system_v5/julia_carrier",
             os.path.join(repo, "sim_engines", "serialized", "catlab_ratchet.jl"), out_path],
            capture_output=True, text=True, timeout=900)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0 or not os.path.exists(out_path):
            print("[FATAL] julia: catlab_ratchet failed (Gate M1 or export); failing closed.",
                  file=sys.stderr)
            return 1
        # Bind the M1 proof into the ledger (referee finding: stdout pins nothing).
        sidecar = out_path + ".receipt.json"
        try:
            m1 = json.load(open(sidecar))
        except Exception as exc:  # noqa: BLE001
            print(f"[FATAL] julia: M1 sidecar receipt unreadable ({exc}); failing closed.",
                  file=sys.stderr)
            return 1
        if m1.get("m1_status") != "sat" or m1.get("m1_polarity") != "unsat":
            print(f"[FATAL] julia: M1 proof pair wrong ({m1.get('m1_status')}/"
                  f"{m1.get('m1_polarity')}, need sat/unsat); failing closed.", file=sys.stderr)
            return 1
        m1["m1_receipt_digest"] = hash_artifact(sidecar)
        # Independent structural verification — do not trust the producer
        # (referee finding: exit code 0 + file-exists is not evidence).
        chk = subprocess.run(
            [sys.executable, os.path.join(repo, "sim_engines", "serialized",
                                          "test_ratchet_mask.py"), out_path],
            capture_output=True, text=True, timeout=120)
        sys.stdout.write(chk.stdout)
        if chk.returncode != 0:
            print("[FATAL] julia: independent mask verification FAILED; failing closed.",
                  file=sys.stderr)
            return 1
    else:
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

    # 3. PUBLISH MANIFEST (ledger + JSON receipt mirror) — atomic commit.
    manifest = {
        "stage": args.stage,
        "run_id": args.run_id,
        "payload": payload,
        "artifact_path": out_path,
        "input_digest": input_digest,
        "output_digest": hash_artifact(out_path),
        "proof_status": proof_status,
        "schema_version": "1.1",
        **m1,
    }
    kv_set(db, f"runs/{args.run_id}/stages/{args.stage}", manifest)
    kv_set(db, f"runs/{args.run_id}/current", manifest)
    db.commit()  # both keys land together or not at all
    rc_dir = os.path.normpath(os.path.join(os.path.dirname(args.state_db), "..", "receipts", args.run_id))
    os.makedirs(rc_dir, exist_ok=True)
    with open(os.path.join(rc_dir, f"{args.stage}.json"), "w") as f:
        json.dump(manifest, f, sort_keys=True, indent=1)

    print(f"[+] {args.stage.upper()} bound. digest {manifest['output_digest'][:8]} -> tombstone.")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
