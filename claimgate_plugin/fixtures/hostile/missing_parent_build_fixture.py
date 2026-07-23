#!/usr/bin/env python3
"""Hostile-control fixture builder — class: missing_parent.

Builds a spine ledger (sqlite kv, same schema as
sim_engines/serialized/serialized_stage.py) where a later stage references a
prior stage that has NO receipt row. Two runs in one DB:

  missing_parent_r1 — FIRST stage absent: no julia receipt row at all, but the
    jax receipt has input_digest SET (a phantom digest referencing a julia
    output that was never published). jax/pysindy/z3 rows are otherwise sound:
    artifacts exist on disk, output digests re-derive, links between the
    present stages are intact, z3 is COMPLETED/UNSAT. The ONLY defect is the
    missing parent.

  missing_parent_r2 — MIDDLE stage absent: julia present and fully sound
    (artifact re-derives, real payload with a bound M1 sat/unsat pair and a
    real sidecar receipt digest), jax row ABSENT, pysindy/z3 present with
    pysindy.input_digest set to a phantom jax output digest.

Expected gate behavior (claimgate_plugin/claim_admission.mjs, run from repo
root): PARKED exit 3 at the first absent stage — incomplete pipeline, never
REJECTED and never ENVELOPE SOUND.

Every receipt stored in the ledger, every JSON artifact, and every mirror
receipt carries classification=hostile_control_fixture and
promotion_allowed=false so nothing here can be mistaken for a real receipt.

Deterministic: byte-identical artifacts and ledger rows on every run.
Usage: python3 missing_parent_build_fixture.py   (any cwd; paths are anchored
to this file's location; artifact_path values in the ledger are repo-root-
relative, so run the gate from the repo root.)
"""
import hashlib
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
# .../claimgate_plugin/fixtures/hostile -> repo root is three levels up
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
DB_PATH = os.path.join(HERE, "missing_parent.state.db")
ART_ROOT = os.path.join(HERE, "missing_parent_artifacts")
RCPT_ROOT = os.path.join(HERE, "missing_parent_receipts")

HOSTILE = {"classification": "hostile_control_fixture", "promotion_allowed": False}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = json.dumps(obj, sort_keys=True, indent=1) + "\n"
    with open(path, "w") as f:
        f.write(data)
    return sha256_bytes(data.encode())


def artifact(run, stage, extra):
    """Write a deterministic JSON artifact; return (repo-relative path, digest)."""
    rel = os.path.join("claimgate_plugin", "fixtures", "hostile",
                       "missing_parent_artifacts", run, f"{stage}_output.json")
    body = {
        "stage": stage,
        "run_id": run,
        "note": "hostile-control artifact (missing_parent class); payload is inert",
        **HOSTILE,
        **extra,
    }
    digest = write_json(os.path.join(REPO, rel), body)
    return rel, digest


def manifest(run, stage, art_rel, out_digest, in_digest, **extra):
    m = {
        "stage": stage,
        "run_id": run,
        "payload": "real",
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

    # ---- run 1: FIRST stage (julia) has no receipt row -------------------
    r1 = "missing_parent_r1"
    # The phantom parent: a digest of julia output bytes that were never
    # published to the ledger. input_digest is SET; the parent row is absent.
    phantom_julia = sha256_bytes(b"PHANTOM_JULIA_OUTPUT_NEVER_PUBLISHED_r1")

    jax_rel, jax_dig = artifact(r1, "jax", {"engine": "jax"})
    publish(r1, manifest(r1, "jax", jax_rel, jax_dig, phantom_julia))

    ps_rel, ps_dig = artifact(r1, "pysindy", {"engine": "pysindy"})
    publish(r1, manifest(r1, "pysindy", ps_rel, ps_dig, jax_dig))

    z3_rel, z3_dig = artifact(r1, "z3", {"engine": "z3"})
    publish(r1, manifest(r1, "z3", z3_rel, z3_dig, ps_dig, proof_status="UNSAT"))
    # NOTE: no runs/missing_parent_r1/stages/julia key is ever written.

    # ---- run 2: MIDDLE stage (jax) has no receipt row --------------------
    r2 = "missing_parent_r2"
    # julia is fully sound: real artifact + bound M1 sat/unsat pair with a
    # real sidecar receipt on disk, so the only defect in r2 is the absent jax.
    sidecar_rel = os.path.join("claimgate_plugin", "fixtures", "hostile",
                               "missing_parent_artifacts", r2,
                               "julia_output.json.receipt.json")
    sidecar_digest = write_json(os.path.join(REPO, sidecar_rel),
                                {"m1_status": "sat", "m1_polarity": "unsat",
                                 "note": "hostile-control M1 sidecar", **HOSTILE})
    ju_rel, ju_dig = artifact(r2, "julia", {"engine": "julia"})
    publish(r2, manifest(r2, "julia", ju_rel, ju_dig, None,
                         m1_status="sat", m1_polarity="unsat",
                         m1_receipt_digest=sidecar_digest))

    phantom_jax = sha256_bytes(b"PHANTOM_JAX_OUTPUT_NEVER_PUBLISHED_r2")
    ps2_rel, ps2_dig = artifact(r2, "pysindy", {"engine": "pysindy"})
    publish(r2, manifest(r2, "pysindy", ps2_rel, ps2_dig, phantom_jax))

    z32_rel, z32_dig = artifact(r2, "z3", {"engine": "z3"})
    publish(r2, manifest(r2, "z3", z32_rel, z32_dig, ps2_dig, proof_status="UNSAT"))
    # NOTE: no runs/missing_parent_r2/stages/jax key is ever written.

    db.commit()
    rows = db.execute("SELECT key FROM kv ORDER BY key").fetchall()
    db.close()
    print(f"[fixture] ledger written: {DB_PATH}")
    for (k,) in rows:
        print(f"  {k}")
    absent = [f"runs/{r1}/stages/julia", f"runs/{r2}/stages/jax"]
    for k in absent:
        print(f"  ABSENT (by construction): {k}")


if __name__ == "__main__":
    main()
