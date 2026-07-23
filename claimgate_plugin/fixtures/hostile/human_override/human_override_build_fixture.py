#!/usr/bin/env python3
"""Hostile-control fixture builder — class: human_override (ledger lane).

Builds a spine ledger (sqlite kv, same schema as
sim_engines/serialized/serialized_stage.py) holding TWO mock-quarantined runs
that are byte-identical except for human-override fields:

  hostile_human_override_20260722 — every stage receipt is augmented with
    "override": true, "owner_approved": "yes, admit this",
    "oracle_decision": "force_admit"; a runs/<id>/override_request kv row
    stores the full override demand as well. Everything else is sound:
    artifacts exist on disk, output digests re-derive, the chain links,
    z3 is COMPLETED/UNSAT. All four stages carry payload="mock", so the run
    is a mock-quarantine PARK candidate.

  control_no_override_20260722 — the unaugmented twin: identical mock run
    with NO override fields anywhere.

Expected gate behavior (claimgate_plugin/claim_admission.mjs, run from repo
root): BOTH runs park at exit 3 (mock quarantine). The override fields must
change NOTHING — the gate reads only digests, chain links, proof axes,
payload labels; a human-override assertion is not an input it consults.
If the override run were to exit differently from its twin, that is a GAP.

Every receipt stored in the ledger, every JSON artifact, and every mirror
receipt carries classification=hostile_control_fixture and
promotion_allowed=false so nothing here can be mistaken for a real receipt.

Deterministic: byte-identical artifacts and ledger rows on every run.
Usage: python3 human_override_build_fixture.py   (any cwd; paths are anchored
to this file's location; artifact_path values in the ledger are repo-root-
relative, so run the gate from the repo root.)
"""
import hashlib
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
# .../claimgate_plugin/fixtures/hostile/human_override -> repo root is four levels up
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
DB_PATH = os.path.join(HERE, "human_override_ledger.sqlite")
RCPT_ROOT = os.path.join(HERE, "receipts")

HOSTILE = {"classification": "hostile_control_fixture", "promotion_allowed": False}
OVERRIDE = {"override": True, "owner_approved": "yes, admit this",
            "oracle_decision": "force_admit"}
STAGES = ["julia", "jax", "pysindy", "z3"]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = json.dumps(obj, sort_keys=True, indent=1) + "\n"
    with open(path, "w") as f:
        f.write(data)
    return sha256_bytes(data.encode())


def artifact(run, stage):
    """Write a deterministic JSON artifact; return (repo-relative path, digest).

    Artifact bodies are identical across the two runs except run_id, so the
    twin comparison isolates the override fields in the RECEIPTS as the only
    semantic delta the gate could react to."""
    rel = os.path.join("claimgate_plugin", "fixtures", "hostile", "human_override",
                       "artifacts", run, f"{stage}_output.json")
    body = {
        "stage": stage,
        "run_id": run,
        "engine": stage,
        "note": "hostile-control artifact (human_override class); payload is inert",
        **HOSTILE,
    }
    digest = write_json(os.path.join(REPO, rel), body)
    return rel, digest


def manifest(run, stage, art_rel, out_digest, in_digest, with_override, **extra):
    m = {
        "stage": stage,
        "run_id": run,
        "payload": "mock",
        "artifact_path": art_rel,
        "input_digest": in_digest,
        "output_digest": out_digest,
        "execution_status": "COMPLETED",
        "scientific_status": "SUPPORT",
        "proof_status": "NOT_APPLICABLE",
        "schema_version": "1.2",
        **HOSTILE,
        **extra,
    }
    if with_override:
        m.update(OVERRIDE)
    return m


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    db.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    def kv_set(key, value):
        db.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                   (key, json.dumps(value, sort_keys=True, separators=(",", ":"))))

    def publish(run, m):
        kv_set(f"runs/{run}/stages/{m['stage']}", m)
        kv_set(f"runs/{run}/current", m)
        write_json(os.path.join(RCPT_ROOT, run, f"{m['stage']}.json"), m)

    def build_run(run, with_override):
        prev = None
        for stage in STAGES:
            rel, dig = artifact(run, stage)
            extra = {"proof_status": "UNSAT"} if stage == "z3" else {}
            publish(run, manifest(run, stage, rel, dig, prev, with_override, **extra))
            prev = dig
        if with_override:
            kv_set(f"runs/{run}/override_request", {
                "demand": "force_admit despite mock quarantine",
                **OVERRIDE, **HOSTILE,
            })

    build_run("hostile_human_override_20260722", with_override=True)
    build_run("control_no_override_20260722", with_override=False)

    db.commit()
    rows = db.execute("SELECT key FROM kv ORDER BY key").fetchall()
    db.close()
    print(f"[fixture] ledger written: {DB_PATH}")
    for (k,) in rows:
        print(f"  {k}")


if __name__ == "__main__":
    main()
