"""GF(2) oracle for withheld-bit ground truth. EVALUATION LABELS ONLY.

World source (per world_source/receipt.json): 8-bit words, additive XOR CA,
periodic boundary, rule_family {0:[-1,1], 1:[-1,0,1], 2:[0,1], 3:[-1,0]},
hidden state = (initial word, rule) -> 1024. View t = state after t steps.

For each object: enumerate rules, solve the GF(2) linear system given the
visible bits, collect ALL consistent hypotheses (rule, x0). A withheld bit
gets a label only when every consistent hypothesis agrees; otherwise it is
'ambiguous' and excluded from the accuracy denominator (count reported).

These labels never enter model features or training loss (leak check).
"""
import json
import collections

N_BITS = 8
RULES = {0: [-1, 1], 1: [-1, 0, 1], 2: [0, 1], 3: [-1, 0]}


def load_rows(path):
    rows = []
    with open(path) as f:
        for line in f:
            e = json.loads(line)
            for op in e["payload"]["operations"]:
                d = {c["predicate"]: c["object"] for c in op["payload"]["claims"]}
                rows.append(d)
    return rows


def build_views(rows):
    """-> obs[obj][view][pos] in {0,1,None}; occ[obj][view][pos] bool."""
    obs = collections.defaultdict(lambda: [[None] * N_BITS for _ in range(6)])
    occ = collections.defaultdict(lambda: [[False] * N_BITS for _ in range(6)])
    for r in rows:
        o = int(r["has_object_id"].split("-")[1])
        v = int(r["view_index"]); p = int(r["probe_position"])
        if r["occluded"] == "true":
            occ[o][v][p] = True
        else:
            obs[o][v][p] = int(r["probe_outcome"])
    return dict(obs), dict(occ)


def rule_matrix(offsets):
    """A[i][j] over GF(2): next[i] = XOR_j A[i][j] * state[j]."""
    A = [[0] * N_BITS for _ in range(N_BITS)]
    for i in range(N_BITS):
        for o in offsets:
            A[i][(i + o) % N_BITS] ^= 1
    return A


def mat_mul(A, B):
    n = len(A)
    return [[(sum(A[i][k] & B[k][j] for k in range(n)) & 1) for j in range(n)]
            for i in range(n)]


def mat_pows(A, tmax):
    out = [[[1 if i == j else 0 for j in range(N_BITS)] for i in range(N_BITS)]]
    for _ in range(tmax):
        out.append(mat_mul(A, out[-1]))
    return out


def solve_gf2_all(eqs):
    """eqs: list of (row8bits, rhs). Return list of ALL solutions x0 (as tuples),
    empty if inconsistent."""
    rows = [list(r) + [b] for r, b in eqs]
    n = N_BITS
    piv_cols = []
    r = 0
    for c in range(n):
        piv = next((i for i in range(r, len(rows)) if rows[i][c]), None)
        if piv is None:
            continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for i in range(len(rows)):
            if i != r and rows[i][c]:
                rows[i] = [a ^ b for a, b in zip(rows[i], rows[r])]
        piv_cols.append(c)
        r += 1
    for i in range(r, len(rows)):
        if rows[i][n]:
            return []  # inconsistent
    free_cols = [c for c in range(n) if c not in piv_cols]
    sols = []
    for m in range(1 << len(free_cols)):
        x = [0] * n
        for k, c in enumerate(free_cols):
            x[c] = (m >> k) & 1
        for i, c in enumerate(piv_cols):
            v = rows[i][n]
            for fc in free_cols:
                v ^= rows[i][fc] & x[fc]
            x[c] = v
        sols.append(tuple(x))
    return sols


def oracle_labels(obs, occ):
    """-> labels[obj][view][pos] in {0,1,None(ambiguous)}, stats dict."""
    pows = {r: mat_pows(rule_matrix(off), 5) for r, off in RULES.items()}
    labels = {}
    stats = {"objects": 0, "unique_hypothesis": 0, "multi_hypothesis": 0,
             "no_hypothesis": 0, "withheld_total": 0, "withheld_labeled": 0,
             "withheld_ambiguous": 0, "visible_check_fail": 0}
    for o in sorted(obs):
        stats["objects"] += 1
        eqs_base = []
        for t in range(6):
            for i in range(N_BITS):
                if obs[o][t][i] is not None:
                    eqs_base.append((t, i, obs[o][t][i]))
        hyps = []
        for r in RULES:
            eqs = [(pows[r][t][i], b) for t, i, b in eqs_base]
            for x0 in solve_gf2_all(eqs):
                hyps.append((r, x0))
        if len(hyps) == 0:
            stats["no_hypothesis"] += 1
        elif len(hyps) == 1:
            stats["unique_hypothesis"] += 1
        else:
            stats["multi_hypothesis"] += 1
        lab = [[None] * N_BITS for _ in range(6)]
        for t in range(6):
            for i in range(N_BITS):
                if not occ[o][t][i]:
                    # sanity: every hypothesis must reproduce visible bits
                    for r, x0 in hyps:
                        v = sum(pows[r][t][i][j] & x0[j] for j in range(N_BITS)) & 1
                        if v != obs[o][t][i]:
                            stats["visible_check_fail"] += 1
                    continue
                stats["withheld_total"] += 1
                vals = {sum(pows[r][t][i][j] & x0[j] for j in range(N_BITS)) & 1
                        for r, x0 in hyps}
                if len(vals) == 1 and hyps:
                    lab[t][i] = vals.pop()
                    stats["withheld_labeled"] += 1
                else:
                    stats["withheld_ambiguous"] += 1
        labels[o] = lab
    return labels, stats


if __name__ == "__main__":
    import sys
    rows = load_rows(sys.argv[1])
    obs, occ = build_views(rows)
    labels, stats = oracle_labels(obs, occ)
    print(json.dumps(stats, indent=1))
