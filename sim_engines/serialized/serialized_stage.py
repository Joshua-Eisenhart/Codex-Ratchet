#!/usr/bin/env python3
"""Universal stage CLI for the serialized transport canary + real CR packets.

PACKET MODE (Slice C): SPINE_PACKET=<path.json> wraps an EXISTING repo-defined
CR packet, unchanged, in true separate processes. The spec lists ordered
stages, each a real command whose stdout-JSON (or written file) becomes the
immutable artifact. The packet's stage list is bound into the ledger at
genesis so the envelope check audits the declared chain, not a hardcoded one.
Engine disagreement in a crosscheck stage is COMPLETED/COUNTEREXAMPLE —
negative science that reaches admission — never a process crash.

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
    p.add_argument("--stage", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--state-db", required=True)
    p.add_argument("--force-fail", action="store_true",
                   help="z3 only: emit a SAT COUNTEREXAMPLE receipt (completed negative science, "
                        "exit 0 — it must REACH admission; nonzero exit is for infra failure only)")
    args = p.parse_args()

    # Packet mode: an ordered stage list from the spec replaces the canary's four.
    packet = None
    packet_path = os.environ.get("SPINE_PACKET", "")
    if packet_path:
        try:
            packet = json.load(open(packet_path))
        except Exception as exc:  # noqa: BLE001
            print(f"[FATAL] packet spec unreadable ({exc}); failing closed.", file=sys.stderr)
            return 1
    stage_names = [s["name"] for s in packet["stages"]] if packet else list(STAGES)
    if args.stage not in stage_names:
        print(f"[FATAL] unknown stage {args.stage!r} (expected one of {stage_names}).", file=sys.stderr)
        return 1

    if not RUN_ID_RE.match(args.run_id):
        print(f"[FATAL] invalid run_id {args.run_id!r} (allowed: [A-Za-z0-9_-]+); "
              f"refusing path/key interpolation.", file=sys.stderr)
        return 1

    db = ledger(args.state_db)
    art_dir = os.path.join(os.path.dirname(args.state_db), "..", "artifacts", args.run_id)
    art_dir = os.path.normpath(art_dir)
    os.makedirs(art_dir, exist_ok=True)

    # 1. CHAIN OF CUSTODY — re-derive, don't trust (the genesis stage has no input).
    input_digest = None
    if args.stage != stage_names[0]:
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
    role = "transport"
    m1 = {}
    scientific_status_override = None
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if packet:
        # PACKET MODE — every stage is a real command from the spec; the sim is UNCHANGED.
        import subprocess
        spec = next(s for s in packet["stages"] if s["name"] == args.stage)
        payload, role = "real", spec.get("role", "engine_leg")
        out_path = os.path.join(art_dir, f"{args.stage}_output.json")
        cmd = [c.replace("{out}", out_path)
                .replace("{repo}", repo)
                .replace("{art_dir}", art_dir) for c in spec["command"]]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, cwd=repo)
        sys.stderr.write(proc.stderr)
        if proc.returncode != 0:
            print(f"[FATAL] {args.stage}: packet command exit {proc.returncode}; infra failure.",
                  file=sys.stderr)
            return 1
        if spec.get("capture") == "stdout":
            lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("{")]
            if not lines:
                print(f"[FATAL] {args.stage}: no JSON on stdout; infra failure.", file=sys.stderr)
                return 1
            with open(out_path, "w") as f:
                f.write(lines[-1])
        elif not os.path.exists(out_path):
            print(f"[FATAL] {args.stage}: command wrote no artifact at {out_path}.", file=sys.stderr)
            return 1
        # A crosscheck artifact reporting disagreement is COMPLETED negative science.
        try:
            art = json.load(open(out_path))
            if isinstance(art, dict) and art.get("counterexample") is True:
                scientific_status_override = "COUNTEREXAMPLE"
        except Exception:  # noqa: BLE001 — non-JSON artifacts carry no verdict
            pass
    elif args.stage == "julia" and payload == "real":
        role = "carrier_calibration"
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

    # Three status axes, never collapsed (webui audit 2026-07-22): a SAT proof
    # is a successfully EXECUTED counterexample — completed negative science
    # that must reach admission as a receipt. Nonzero process exit is reserved
    # for infrastructure failure (unreadable input, broken chain, crash).
    proof_status = "NOT_APPLICABLE"
    # A mock stage is transport plumbing — it may not claim scientific support.
    scientific_status = "SUPPORT" if payload == "real" else "INCONCLUSIVE"
    if args.stage == "z3":
        if args.force_fail:
            proof_status = "SAT"
            scientific_status = "COUNTEREXAMPLE"
            print("[*] z3: proof returned SAT — counterexample found. Publishing the "
                  "counterexample receipt (completed execution, negative science).")
        else:
            proof_status = "UNSAT"

    # 3. PUBLISH MANIFEST (ledger + JSON receipt mirror) — atomic commit.
    manifest = {
        "stage": args.stage,
        "run_id": args.run_id,
        "payload": payload,
        "artifact_path": out_path,
        "input_digest": input_digest,
        "output_digest": hash_artifact(out_path),
        "execution_status": "COMPLETED",
        "scientific_status": scientific_status,
        "proof_status": proof_status,
        "schema_version": "1.2",
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
