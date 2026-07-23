#!/usr/bin/env python3
"""Hostile-control fixture builder — class: solver_sat_counterexample.

Builds a spine ledger (sqlite kv, same schema as the serialized-stage spine)
where every stage is sound — artifacts on disk, digests re-derive, chain links
intact, julia carries a bound Gate M1 sat/unsat pair, every payload real —
and the ONLY event is the z3 stage reporting completed negative science:

    execution_status  COMPLETED       (the solver ran to completion — no crash)
    scientific_status COUNTEREXAMPLE  (the science outcome)
    proof_status      SAT             (a model satisfying the NEGATED claim)

The z3 artifact records a plausible counterexample model: an odd induced
cycle on the 4x4 torus carrier that breaks the claimed seam bipartition
(the Gate M1 claim family), with the satisfying color assignment.

Expected gate behavior (claimgate_plugin/claim_admission.mjs, run from repo
root): REJECTED exit 1 via the dedicated SAT branch, printing the
evidence-preserved line ("... counterexample EXISTS and its receipt is
preserved as completed negative science ...") AFTER all four stage digests
re-derive OK — proving the counterexample receipt reached admission as
evidence and was never converted into an infrastructure crash
(post-mortem miss #3, status-axis collapse).

Every ledger row, JSON artifact, and mirror receipt carries
classification=hostile_control_fixture and promotion_allowed=false so nothing
here can be mistaken for a real receipt.

Deterministic: byte-identical artifacts and ledger rows on every run.
Usage: python3 build_fixture.py   (any cwd; paths anchored to this file;
artifact_path values are repo-root-relative, so run the gate from repo root.)
"""
import hashlib
import json
import os
import sqlite3

HERE = os.path.dirname(os.path.abspath(__file__))
# .../claimgate_plugin/fixtures/hostile/solver_sat_counterexample -> repo root
REPO = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
RUN = "solver_sat_counterexample_hostile_v1"
DB_PATH = os.path.join(HERE, "state", "state.db")
REL_ROOT = os.path.join("claimgate_plugin", "fixtures", "hostile",
                        "solver_sat_counterexample")

HOSTILE = {"classification": "hostile_control_fixture", "promotion_allowed": False,
           "fixture_class": "solver_sat_counterexample"}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = json.dumps(obj, sort_keys=True, indent=1) + "\n"
    with open(path, "w") as f:
        f.write(data)
    return sha256_bytes(data.encode())


def manifest(stage, art_rel, out_digest, in_digest, **extra):
    return {
        "stage": stage,
        "run_id": RUN,
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


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.execute("CREATE TABLE IF NOT EXISTS kv (key TEXT PRIMARY KEY, value TEXT NOT NULL)")

    def kv_set(key, value):
        db.execute("INSERT OR REPLACE INTO kv (key, value) VALUES (?, ?)",
                   (key, json.dumps(value, sort_keys=True, separators=(",", ":"))))

    def publish(m):
        kv_set(f"runs/{RUN}/stages/{m['stage']}", m)
        kv_set(f"runs/{RUN}/current", m)
        write_json(os.path.join(HERE, "receipts", RUN, f"{m['stage']}.json"), m)

    art_dir_rel = os.path.join(REL_ROOT, "artifacts", RUN)
    art_dir = os.path.join(REPO, art_dir_rel)
    os.makedirs(art_dir, exist_ok=True)

    # ---- julia: sound carrier stage with bound Gate M1 pair ---------------
    julia_bytes = (b"ARROW-INERT\x00hostile_control_fixture "
                   b"fixture_class=solver_sat_counterexample promotion_allowed=false "
                   b"inert julia carrier payload; exists so the envelope digest re-derives\n")
    julia_rel = os.path.join(art_dir_rel, "julia_output.arrow")
    with open(os.path.join(REPO, julia_rel), "wb") as f:
        f.write(julia_bytes)
    julia_dig = sha256_bytes(julia_bytes)
    sidecar_rel = os.path.join(art_dir_rel, "julia_output.arrow.receipt.json")
    sidecar_dig = write_json(os.path.join(REPO, sidecar_rel), {
        "m1_status": "sat", "m1_polarity": "unsat",
        "note": "hostile-control M1 sidecar (inert); binds the julia stage proof pair",
        **HOSTILE,
    })
    publish(manifest("julia", julia_rel, julia_dig, None,
                     m1_status="sat", m1_polarity="unsat",
                     m1_receipt_digest=sidecar_dig))

    # ---- jax: sound -------------------------------------------------------
    jax_rel = os.path.join(art_dir_rel, "jax_output.json")
    jax_dig = write_json(os.path.join(REPO, jax_rel), {
        "stage": "jax", "engine": "jax",
        "note": "not a real engine artifact; exists so the envelope digest re-derives",
        **HOSTILE,
    })
    publish(manifest("jax", jax_rel, jax_dig, julia_dig))

    # ---- pysindy: sound ---------------------------------------------------
    ps_rel = os.path.join(art_dir_rel, "pysindy_output.json")
    ps_dig = write_json(os.path.join(REPO, ps_rel), {
        "stage": "pysindy", "engine": "pysindy",
        "note": "not a real engine artifact; exists so the envelope digest re-derives",
        **HOSTILE,
    })
    publish(manifest("pysindy", ps_rel, ps_dig, jax_dig))

    # ---- z3: COMPLETED / COUNTEREXAMPLE / SAT with a plausible model ------
    z3_rel = os.path.join(art_dir_rel, "z3_output.json")
    z3_dig = write_json(os.path.join(REPO, z3_rel), {
        "stage": "z3",
        "solver": "z3",
        "solver_version": "4.15.3",
        "check_sat": "sat",
        "wall_time_s": 0.41,
        "claim_under_test": ("seam bipartition (Gate M1 family): every admissible "
                             "mask on the 4x4 torus carrier preserves the seam "
                             "2-coloring; the NEGATION is encoded, so SAT = a "
                             "counterexample mask exists"),
        "encoding": "(assert (not (seam-bipartite carrier mask)))",
        "counterexample_model": {
            "mask_cells_open": [[0, 0], [0, 1], [1, 1], [2, 1], [2, 0]],
            "induced_cycle": ["v_0_0", "v_0_1", "v_1_1", "v_2_1", "v_2_0"],
            "cycle_length": 5,
            "cycle_parity": "odd",
            "color_assignment": {"v_0_0": 0, "v_0_1": 1, "v_1_1": 0,
                                 "v_2_1": 1, "v_2_0": 0},
            "conflict_edge": ["v_2_0", "v_0_0"],
            "conflict": "both endpoints of the seam-closing edge take color 0",
        },
        "note": ("completed negative science: the solver RAN (no infra error) and "
                 "found a model of the negated claim; this receipt must reach the "
                 "envelope check as preserved evidence, never as a crash"),
        **HOSTILE,
    })
    publish(manifest("z3", z3_rel, z3_dig, ps_dig,
                     scientific_status="COUNTEREXAMPLE",
                     proof_status="SAT"))

    db.commit()
    rows = db.execute("SELECT key FROM kv ORDER BY key").fetchall()
    db.close()
    print(f"[fixture] ledger written: {DB_PATH}")
    for (k,) in rows:
        print(f"  {k}")


if __name__ == "__main__":
    main()
