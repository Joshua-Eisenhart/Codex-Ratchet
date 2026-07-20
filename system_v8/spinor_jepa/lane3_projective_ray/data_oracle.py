"""lane3_projective_ray -- data loading + scorer-side oracle reconstruction.

Torch-free module. The oracle reconstructs each object's hidden state
(initial 8-bit word + additive-XOR CA rule) by exhaustive consistency over
the 1024-element hidden space, using VISIBLE bits only. Its output is used
EXCLUSIVELY as evaluation ground truth for occluded-bit accuracy. It never
enters any model feature (leak check asserts this structurally).

World-source parameters (from world_source/receipt.json, read-only):
  n_bits=8, n_objects=64, n_views=6, rule_family:
    0: [-1, 1]; 1: [-1, 0, 1]; 2: [0, 1]; 3: [-1, 0]
  additive (XOR) cellular automaton, periodic boundary.
"""
import json
import numpy as np

EVENTS = ("/Users/joshuaeisenhart/Codex-Ratchet/system_v8/loop2_world/"
          "results/world_source/events_dynamics_on.jsonl")
N_BITS, N_OBJ, N_VIEWS = 8, 64, 6
RULE_FAMILY = {0: (-1, 1), 1: (-1, 0, 1), 2: (0, 1), 3: (-1, 0)}


def load_rows(path=EVENTS):
    rows = []
    with open(path) as f:
        for line in f:
            ev = json.loads(line)
            for op in ev["payload"]["operations"]:
                d = {c["predicate"]: c["object"] for c in op["payload"]["claims"]}
                rows.append(d)
    return rows


def build_tables(rows):
    """Return outcome[obj, view, pos] in {0,1,-1(withheld)} and occ mask."""
    outcome = np.full((N_OBJ, N_VIEWS, N_BITS), -1, dtype=np.int64)
    occluded = np.zeros((N_OBJ, N_VIEWS, N_BITS), dtype=bool)
    for r in rows:
        o = int(r["has_object_id"].split("-")[1])
        v, p = int(r["view_index"]), int(r["probe_position"])
        occluded[o, v, p] = (r["occluded"] == "true")
        outcome[o, v, p] = -1 if r["probe_outcome"] == "withheld" else int(r["probe_outcome"])
    # structural invariant: withheld iff occluded
    assert np.all((outcome == -1) == occluded), "withheld/occluded mismatch"
    return outcome, occluded


def step(word, taps, sign):
    """One CA step. sign=+1: new[i] = XOR_t word[(i+t)%8]; sign=-1 mirrored."""
    out = np.zeros_like(word)
    for t in taps:
        out ^= np.roll(word, -sign * t)
    return out


def trajectory(word0, rule, sign):
    traj = np.zeros((N_VIEWS, N_BITS), dtype=np.int64)
    w = word0.copy()
    for v in range(N_VIEWS):
        traj[v] = w
        w = step(w, RULE_FAMILY[rule], sign)
    return traj


def reconstruct(outcome, occluded, sign):
    """For each object: unique (word0, rule) consistent with all visible bits.
    Returns full ground-truth table or None if any object is not uniquely
    identified under this tap-sign convention."""
    truth = np.zeros((N_OBJ, N_VIEWS, N_BITS), dtype=np.int64)
    hidden = []
    for o in range(N_OBJ):
        matches = []
        for rule in range(4):
            for w0i in range(256):
                w0 = np.array([(w0i >> b) & 1 for b in range(N_BITS)], dtype=np.int64)
                traj = trajectory(w0, rule, sign)
                vis = ~occluded[o]
                if np.all(traj[vis] == outcome[o][vis]):
                    matches.append((rule, w0i, traj))
        # count distinct full trajectories (equivalence class), not raw params
        distinct = {tr.tobytes() for _, _, tr in matches}
        if len(distinct) != 1:
            return None, None
        truth[o] = matches[0][2]
        hidden.append({"rule": matches[0][0], "word0": matches[0][1],
                       "n_param_matches": len(matches)})
    return truth, hidden


def main():
    rows = load_rows()
    outcome, occluded = build_tables(rows)
    for sign in (+1, -1):
        truth, hidden = reconstruct(outcome, occluded, sign)
        if truth is not None:
            # sanity: truth must agree with every visible bit
            vis = ~occluded
            assert np.all(truth[vis] == outcome[vis])
            n_occ = int(occluded.sum())
            print(f"tap sign convention {sign:+d}: ALL 64 objects uniquely "
                  f"identified; {n_occ} occluded bits reconstructed")
            rules = [h["rule"] for h in hidden]
            print("rule histogram:", {r: rules.count(r) for r in range(4)})
            np.savez("/Users/joshuaeisenhart/Codex-Ratchet/system_v8/spinor_jepa/"
                     "lane3_projective_ray/results/oracle_truth.npz",
                     truth=truth, occluded=occluded, outcome=outcome,
                     rules=np.array(rules),
                     words0=np.array([h["word0"] for h in hidden]),
                     tap_sign=np.array([sign]))
            return
        print(f"tap sign convention {sign:+d}: not uniquely consistent")
    raise SystemExit("oracle reconstruction FAILED under both conventions")


if __name__ == "__main__":
    main()
