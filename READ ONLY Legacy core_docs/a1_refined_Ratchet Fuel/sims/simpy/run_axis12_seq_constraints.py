#!/usr/bin/env python3
# run_axis12_seq_constraints.py
# Produces:
#   results_axis12_seq_constraints.json
#   sim_evidence_pack.txt   (1 SIM_EVIDENCE block for S_SIM_AXIS12_SEQ_CONSTRAINTS)

from __future__ import annotations
import json, hashlib, os

def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def cycle_edges(seq):
    # edges including wrap
    out = []
    n = len(seq)
    for i in range(n):
        a = seq[i]
        b = seq[(i+1) % n]
        out.append((a,b))
    return out

def undirected_set(pairs):
    s = set()
    for a,b in pairs:
        s.add((a,b))
        s.add((b,a))
    return s

def count_not_in(edges, allowed):
    return sum(1 for e in edges if e not in allowed)

def count_within(edges, group):
    g = set(group)
    return sum(1 for (a,b) in edges if (a in g and b in g))

def main():
    # sequences exactly as your ratcheted seq tokens
    SEQS = {
        "SEQ01": ["Se","Ne","Ni","Si"],
        "SEQ02": ["Se","Si","Ni","Ne"],
        "SEQ03": ["Se","Ne","Si","Ni"],
        "SEQ04": ["Se","Si","Ne","Ni"],
    }

    # Axis1 pairing tokens (registered in B)
    SENI = {"Se","Ni"}
    NESI = {"Ne","Si"}

    # Axis2 adjacency sets (registered in B)
    SETA_allowed = undirected_set([("Ne","Ni"),("Se","Si")])
    SETB_allowed = undirected_set([("Ne","Se"),("Ni","Si")])

    metrics = {}

    for name, seq in SEQS.items():
        edges = cycle_edges(seq)

        # Axis2: adjacency nonmembership counts
        metrics[f"seta_bad_{name}"] = count_not_in(edges, SETA_allowed)
        metrics[f"setb_bad_{name}"] = count_not_in(edges, SETB_allowed)

        # Axis1: within-pair edge counts (pair cohesion signal)
        metrics[f"seni_within_{name}"] = count_within(edges, SENI)
        metrics[f"nesi_within_{name}"] = count_within(edges, NESI)

    out_obj = {
        "seqs": SEQS,
        "metrics": metrics,
    }

    raw = json.dumps(out_obj, indent=2, sort_keys=True).encode("utf-8")
    out_hash = sha256_bytes(raw)

    with open("results_axis12_seq_constraints.json", "wb") as f:
        f.write(raw)

    code_hash = sha256_file(os.path.abspath(__file__))

    lines = []
    lines.append("BEGIN SIM_EVIDENCE v1")
    lines.append("SIM_ID: S_SIM_AXIS12_SEQ_CONSTRAINTS")
    lines.append(f"CODE_HASH_SHA256: {code_hash}")
    lines.append(f"OUTPUT_HASH_SHA256: {out_hash}")
    for k,v in metrics.items():
        lines.append(f"METRIC: {k}={v}")
    lines.append("EVIDENCE_SIGNAL S_SIM_AXIS12_SEQ_CONSTRAINTS CORR E_SIM_AXIS12_SEQ_CONSTRAINTS")
    lines.append("END SIM_EVIDENCE v1")

    pack = "\n".join(lines) + "\n"
    with open("sim_evidence_pack.txt", "w", encoding="utf-8") as f:
        f.write(pack)

    print("DONE: wrote results_axis12_seq_constraints.json and sim_evidence_pack.txt")

if __name__ == "__main__":
    main()
