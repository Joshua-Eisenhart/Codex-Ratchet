#!/usr/bin/env python3
"""
perception_intelligence_v0 -- lane: intelligence (system_v8/loop2_world)

REAL INTELLIGENCE test on the occluded-object perception task
(card authority: system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md AMENDMENT v0.1).

WORLD INPUT (sole view source): the world-source event log
  system_v8/loop2_world/results/world_source/events_dynamics_on.jsonl
  (64 objects x 6 views x 8 probe positions; occluded probes = "withheld").
Ground truth for occluded bits is NOT read from any hidden field: it is
recovered from the visible probes alone by exhaustive consistency over the
published 1024-state hidden space (the world receipt's C2 says all 64 objects
are jointly exactly identified; check c1 re-verifies that here). The rule
FAMILY is public (world_source receipt "parameters.rule_family"); per-object
hidden state (word, rule id) is never read.

TASK (sequential, causal): after consuming the visible probes of views 0..v
of an object, predict every OCCLUDED bit of view v. Train on 44 objects,
evaluate on 20 held-out objects. Chance baseline is COMPUTED (train-selected
majority rule, pooled vs per-position, applied to test).

LANES
 1. QIT engine: faithful port of the loop-1 engine mechanics
    (system_v8/engines_perception/engine_processor_v0.py: stage64 L-side
    operating generators, 2-qubit register, GKSL stage channels, sequential
    probe encoding; params DT/LAM/GAM0/TD from disclosed run-3, NO new tuning).
    Probe position p -> stage p; stage conditioned on the probe OUTCOME bit;
    occluded probes are skipped (identity). The register is NEVER reset across
    views of one object: belief must persist. Readout = 15 exact 2-qubit Pauli
    expectations -> per-position ridge decoders (trained on train objects).
 2. torch predictive model (JEPA-proto per card): per-view encoder -> latent,
    GRU context, predictor for the NEXT view's latent, ray-style loss on
    normalized latents (1 - cos^2, never raw MSE) + variance anti-collapse
    term; free energy = prediction error; OBJECTS = latent clusters
    (KMeans on context latents, ARI vs object ids, computed). Occluded-bit
    readout: per-position ridge probes on the context latent.
 3. Turing twin: ID3 decision tree (categorical, multiway) on automaton
    features of the SAME views: last-seen value/age at the target position,
    the 4 public-rule-family predictions from view v-1, per-rule running
    agreement scores (clipped), best-rule consensus prediction, position, view.
CEILING (not a lane): exact Bayes filter over the 1024-state hidden space
    (majority vote of the causal survivor set) -- upper bound for any method.

VERDICT METRICS: occluded-bit accuracy engine vs twin vs JEPA (each vs the
computed baseline); complementarity matrix engine-vs-twin (loop-1's
"largely_redundant" verdict RETESTED where hidden state matters); belief
persistence = Holevo chi between register states grouped by a bit NOT probed
in the current view, gated against a permutation null (computed, not assumed).

CONTROLS: shuffled object ids (ARI collapses); occlusion-free rerun of twin
and engine (only the queried bit masked -- does the twin catch up?); frozen
engine (conditioning off).

Honest negatives are KEPT: if the twin matches or beats the engine under
occlusion, that verdict is the finding. promotion_allowed: false.
Ceiling: unofficial working sim. Refuses to reuse the outdir.
Run with /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3.
"""

import json
import os
import sys
import math
import numpy as np
from scipy.linalg import expm

REPO = "/Users/joshuaeisenhart/Codex-Ratchet"
HERE = os.path.join(REPO, "system_v8", "loop2_world")
OUTDIR = os.path.join(HERE, "results", "intelligence")
EVENTS = os.path.join(HERE, "results", "world_source", "events_dynamics_on.jsonl")
WORLD_RECEIPT = os.path.join(HERE, "results", "world_source", "receipt.json")
STAGE64 = os.path.join(REPO, "system_v8", "nested_manifold", "results",
                       "stage64", "receipt.json")
ENGINE_SOURCE = os.path.join(REPO, "system_v8", "engines_perception",
                             "engine_processor_v0.py")

# ---------------------------------------------------------------- refuse reuse
if os.path.exists(OUTDIR):
    print(f"REFUSE-TO-REUSE: outdir already exists: {OUTDIR}", file=sys.stderr)
    sys.exit(2)
os.makedirs(OUTDIR)

SEED = 20260719
rng = np.random.default_rng(SEED)

N_BITS, N_VIEWS = 8, 6
N_OBJECTS = 64
N_TRAIN = 44

# public model class (world_source receipt parameters.rule_family)
with open(WORLD_RECEIPT) as f:
    WR = json.load(f)
RULE_FAMILY = {int(k): tuple(v) for k, v in WR["parameters"]["rule_family"].items()}
N_RULES = len(RULE_FAMILY)
HIDDEN_SPACE = [(w, r) for w in range(2 ** N_BITS) for r in range(N_RULES)]

# ---------------------------------------------------------------- parse events
def parse_log(path):
    out = {}
    with open(path) as fh:
        for line in fh:
            ev = json.loads(line)
            ent = ev["payload"]["operations"][0]["payload"]
            preds = {c["predicate"]: c["object"] for c in ent["claims"]}
            oid = preds["has_object_id"]
            v = int(preds["view_index"])
            pos = int(preds["probe_position"])
            out.setdefault(oid, {}).setdefault(v, {})[pos] = preds["probe_outcome"]
    return out

LOG = parse_log(EVENTS)
OBJ_IDS = sorted(LOG.keys())
assert len(OBJ_IDS) == N_OBJECTS
for o in OBJ_IDS:
    assert len(LOG[o]) == N_VIEWS and all(len(LOG[o][v]) == N_BITS
                                          for v in range(N_VIEWS))

# ---------------------------------------------------------------- world model
def step(bits, rule_idx):
    taps = RULE_FAMILY[rule_idx]
    n = len(bits)
    return tuple(sum(bits[(i + o) % n] for o in taps) % 2 for i in range(n))

def trajectory(w0, rule_idx):
    bits = tuple((w0 >> i) & 1 for i in range(N_BITS))
    traj = [bits]
    for _ in range(N_VIEWS - 1):
        traj.append(step(traj[-1], rule_idx))
    return traj

TRAJ = {hs: trajectory(*hs) for hs in HIDDEN_SPACE}

# causal survivor sets: survivors[obj][v] = hidden states consistent with the
# VISIBLE probes of views 0..v (this is also the Bayes-filter state)
survivors = {}
for o in OBJ_IDS:
    cur = list(HIDDEN_SPACE)
    survivors[o] = []
    for v in range(N_VIEWS):
        vis = {p: int(x) for p, x in LOG[o][v].items() if x != "withheld"}
        cur = [hs for hs in cur
               if all(TRAJ[hs][v][p] == b for p, b in vis.items())]
        survivors[o].append(list(cur))

# ground truth via exhaustive consistency on VISIBLE data only (check c1)
gt_unique = all(len(survivors[o][N_VIEWS - 1]) == 1 for o in OBJ_IDS)
ORACLE = {o: TRAJ[survivors[o][N_VIEWS - 1][0]] for o in OBJ_IDS if
          len(survivors[o][N_VIEWS - 1]) == 1}
assert gt_unique, "ground truth not recoverable; abort before any lane runs"

# occluded slots (obj, view, pos) + train/test object split
SLOTS = [(o, v, p) for o in OBJ_IDS for v in range(N_VIEWS)
         for p in range(N_BITS) if LOG[o][v][p] == "withheld"]
perm = rng.permutation(N_OBJECTS)
TRAIN_OBJS = set(OBJ_IDS[i] for i in perm[:N_TRAIN])
TEST_OBJS = set(OBJ_IDS[i] for i in perm[N_TRAIN:])
TRAIN_SLOTS = [s for s in SLOTS if s[0] in TRAIN_OBJS]
TEST_SLOTS = [s for s in SLOTS if s[0] in TEST_OBJS]
def truth(slot):
    o, v, p = slot
    return ORACLE[o][v][p]

# computed chance baseline: majority rule SELECTED ON TRAIN, applied to test
train_bits = np.array([truth(s) for s in TRAIN_SLOTS])
pooled_maj = int(train_bits.mean() >= 0.5)
pos_maj = {}
for p in range(N_BITS):
    tb = [truth(s) for s in TRAIN_SLOTS if s[2] == p]
    pos_maj[p] = int(np.mean(tb) >= 0.5) if tb else pooled_maj
acc_pool_train = float(np.mean([truth(s) == pooled_maj for s in TRAIN_SLOTS]))
acc_pos_train = float(np.mean([truth(s) == pos_maj[s[2]] for s in TRAIN_SLOTS]))
use_pos = acc_pos_train > acc_pool_train
BASELINE = float(np.mean(
    [truth(s) == (pos_maj[s[2]] if use_pos else pooled_maj) for s in TEST_SLOTS]))
print(f"slots: total={len(SLOTS)} train={len(TRAIN_SLOTS)} test={len(TEST_SLOTS)}")
print(f"computed baseline (train-selected {'per-position' if use_pos else 'pooled'} "
      f"majority) on test = {BASELINE:.4f}")

# ==================================================================== ENGINE
# faithful port of engine_processor_v0.py (lines 104-174): stage64 L stages,
# GKSL superoperators, run-3 params DT=0.5 LAM=0.7 GAM0=0.05 TD=0.5 (disclosed
# grid-scan lineage there; NO new tuning here).
with open(STAGE64) as f:
    S64 = json.load(f)
OP = S64["data"]["operating_pairs"]
K1 = S64["data"]["k1_commutator_norms"]
def stage_list(side):
    out = []
    for fam in (0, 1, 2, 3):
        for fpol in (+1, -1):
            sid = f"family_{fam}|{side}|f{'+' if fpol > 0 else '-'}1"
            pair = OP[sid]
            out.append(dict(sid=sid, f=fpol, d_ax=pair.split("|")[0][-1],
                            h_ax=pair.split("|")[1][-1], kappa=K1[sid][pair]))
    return out
L_STAGES = stage_list("L")

I2 = np.eye(2, dtype=complex)
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
PAULI1 = {"x": SX, "y": SY, "z": SZ}
def kron(a, b): return np.kron(a, b)
def vec(rho): return rho.reshape(-1, order="F")
def unvec(v): return v.reshape(4, 4, order="F")

def dissipator_superop(L):
    LdL = L.conj().T @ L
    I4 = np.eye(4, dtype=complex)
    return (kron(L.conj(), L) - 0.5 * kron(I4, LdL) - 0.5 * kron(LdL.T, I4))

def unitary_superop(U):
    return kron(U.conj(), U)

DT, LAM, GAM0, TD = 0.5, 0.7, 0.05, 0.5

def stage_superops(st, bit):
    sh, sd = PAULI1[st["h_ax"]], PAULI1[st["d_ax"]]
    theta = st["kappa"] * DT * (2 * bit - 1)
    H_loc = kron(sh, I2) if bit == 0 else kron(I2, sh)
    U = expm(-1j * theta * H_loc) @ expm(-1j * LAM * kron(sh, sh))
    Lop = np.sqrt(GAM0 * (1 + 2 * bit)) * kron(sd, I2)
    SU = unitary_superop(U)
    SD = expm(TD * dissipator_superop(Lop))
    return SU, SD

# precompute the full stage channel per (position, bit)
STAGE_CH = {}
for p, st in enumerate(L_STAGES):
    for bit in (0, 1):
        SU, SD = stage_superops(st, bit)
        STAGE_CH[(p, bit)] = (SD @ SU) if st["f"] > 0 else (SU @ SD)

RHO0 = np.zeros((4, 4), dtype=complex); RHO0[0, 0] = 1.0

def choi_cptp(S):
    d = 4
    J = np.zeros((16, 16), dtype=complex)
    for i in range(d):
        for j in range(d):
            E = np.zeros((d, d), dtype=complex); E[i, j] = 1.0
            J += kron(E, unvec(S @ vec(E)))
    J = 0.5 * (J + J.conj().T)
    mineig = float(np.min(np.linalg.eigvalsh(J)))
    TP = np.einsum("ikjk->ij", J.reshape(d, d, d, d))
    return mineig, float(np.max(np.abs(TP - np.eye(d))))

PHYS_VIOL = []
def check_physical(rho, tag):
    tr = abs(np.trace(rho) - 1.0)
    herm = np.max(np.abs(rho - rho.conj().T))
    mineig = float(np.min(np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))))
    if not (tr < 1e-9 and herm < 1e-9 and mineig > -1e-10):
        PHYS_VIOL.append(dict(tag=tag, trace_dev=float(tr),
                              herm_dev=float(herm), min_eig=mineig))

def run_engine_on_log(getter, frozen=False):
    """getter(v,p) -> '0'/'1'/None. Sequential probe encoding: within each
    view, positions 0..7 in order; visible probe at p applies stage p
    conditioned on the outcome bit (frozen: bit forced 0); occluded = skip.
    Register NOT reset across views. Returns state after each view."""
    rho = RHO0.copy()
    states = []
    for v in range(N_VIEWS):
        for p in range(N_BITS):
            out = getter(v, p)
            if out is None:
                continue
            b = 0 if frozen else int(out)
            rho = unvec(STAGE_CH[(p, b)] @ vec(rho))
        states.append(rho.copy())
    return states

def log_getter(o):
    return lambda v, p: (None if LOG[o][v][p] == "withheld" else LOG[o][v][p])

print("\n== engine (faithful loop-1 port) ==")
cptp = {}
for bit in (0, 1):
    me, tp = choi_cptp(STAGE_CH[(0, bit)])
    cptp[f"stage0_bit{bit}"] = dict(choi_min_eig=me, tp_dev=tp)
    print(f"CPTP stage0 bit{bit}: choi_min_eig={me:.3e} tp_dev={tp:.3e}")

ENG_STATES = {}
for o in OBJ_IDS:
    ENG_STATES[o] = run_engine_on_log(log_getter(o))
    for v, r in enumerate(ENG_STATES[o]):
        check_physical(r, f"{o}|view{v}")
FROZEN_STATES = {o: run_engine_on_log(log_getter(o), frozen=True)
                 for o in OBJ_IDS}

# readout features: 15 exact 2-qubit Pauli expectations
PAULIS2 = []
for a, A in [("i", I2), ("x", SX), ("y", SY), ("z", SZ)]:
    for b, B in [("i", I2), ("x", SX), ("y", SY), ("z", SZ)]:
        if a == "i" and b == "i":
            continue
        PAULIS2.append(kron(A, B))
def pauli_feats(rho):
    return np.array([float(np.real(np.trace(P @ rho))) for P in PAULIS2])

def ridge_fit(X, y, lam=1e-3):
    Xa = np.hstack([X, np.ones((X.shape[0], 1))])
    return np.linalg.solve(Xa.T @ Xa + lam * np.eye(Xa.shape[1]), Xa.T @ y)
def ridge_predict(w, X):
    return np.hstack([X, np.ones((X.shape[0], 1))]) @ w

def decode_per_position(feat_of_slot, train_slots, test_slots):
    """Per-position ridge decoders trained on train slots; returns
    (test_acc, per-slot correctness dict on test)."""
    correct = {}
    for p in range(N_BITS):
        tr = [s for s in train_slots if s[2] == p]
        te = [s for s in test_slots if s[2] == p]
        if not te:
            continue
        if len(tr) < 10:
            for s in te:
                correct[s] = (truth(s) == pooled_maj)
            continue
        Xtr = np.array([feat_of_slot(s) for s in tr])
        ytr = np.array([2.0 * truth(s) - 1.0 for s in tr])
        w = ridge_fit(Xtr, ytr)
        Xte = np.array([feat_of_slot(s) for s in te])
        pred = ridge_predict(w, Xte) >= 0
        for s, pr in zip(te, pred):
            correct[s] = (bool(pr) == bool(truth(s)))
    acc = float(np.mean([correct[s] for s in test_slots]))
    return acc, correct

eng_acc, eng_correct = decode_per_position(
    lambda s: pauli_feats(ENG_STATES[s[0]][s[1]]), TRAIN_SLOTS, TEST_SLOTS)
froz_acc, _ = decode_per_position(
    lambda s: pauli_feats(FROZEN_STATES[s[0]][s[1]]), TRAIN_SLOTS, TEST_SLOTS)
print(f"engine occluded-bit acc (test) = {eng_acc:.4f}  (baseline {BASELINE:.4f})")
print(f"frozen-engine occluded-bit acc (test) = {froz_acc:.4f}")

# ---- belief persistence: Holevo chi about bits NOT probed in current view --
def vn_entropy(rho):
    ev = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    ev = ev[ev > 1e-14]
    return float(-np.sum(ev * np.log2(ev)))

def holevo_binary(states, bits):
    n = len(bits)
    n1 = sum(bits)
    if n1 == 0 or n1 == n:
        return 0.0
    r1 = sum(s for s, b in zip(states, bits) if b == 1) / n1
    r0 = sum(s for s, b in zip(states, bits) if b == 0) / (n - n1)
    q1 = n1 / n
    avg = q1 * r1 + (1 - q1) * r0
    return vn_entropy(avg) - q1 * vn_entropy(r1) - (1 - q1) * vn_entropy(r0)

def persistence_chi(state_map, perm_rng=None):
    """mean over positions of Holevo chi(bit_p ; register after view v),
    over instances where p is occluded at v (all 64 objects; a physical
    property of the states, no training involved)."""
    chis = []
    for p in range(N_BITS):
        inst = [(o, v) for (o, v, q) in SLOTS if q == p]
        if len(inst) < 20:
            continue
        states = [state_map[o][v] for o, v in inst]
        bits = [ORACLE[o][v][p] for o, v in inst]
        if perm_rng is not None:
            bits = list(perm_rng.permutation(bits))
        chis.append(holevo_binary(states, bits))
    return float(np.mean(chis)), chis

N_PERM = 200
chi_real, chi_by_pos = persistence_chi(ENG_STATES)
null_rng = np.random.default_rng(SEED + 1)
chi_null = np.array([persistence_chi(ENG_STATES, null_rng)[0]
                     for _ in range(N_PERM)])
chi_froz, _ = persistence_chi(FROZEN_STATES)
froz_null_rng = np.random.default_rng(SEED + 2)
chi_froz_null = np.array([persistence_chi(FROZEN_STATES, froz_null_rng)[0]
                          for _ in range(N_PERM)])
print(f"belief persistence: mean Holevo chi (real) = {chi_real:.5f} bits; "
      f"perm-null mean={chi_null.mean():.5f} p95={np.quantile(chi_null,0.95):.5f}")
print(f"  per-position chi: {[round(c,5) for c in chi_by_pos]}")
print(f"  frozen engine: chi={chi_froz:.5f}; frozen null p95="
      f"{np.quantile(chi_froz_null,0.95):.5f}")

# ==================================================================== TWIN
def make_getter_occfree(o, v_q, p_q):
    return lambda v, p: (None if (v == v_q and p == p_q)
                         else str(ORACLE[o][v][p]))

def twin_features(get, v, p):
    f = {"pos": str(p), "view": str(v)}
    last, age = "none", "inf"
    for u in range(v, -1, -1):
        out = get(u, p)
        if out is not None:
            last, age = out, str(min(v - u, 3))
            break
    f["last"], f["age"] = last, age
    scores = {}
    for r, taps in RULE_FAMILY.items():
        if v == 0:
            pred = "unk"
        else:
            vals = [get(v - 1, (p + o) % N_BITS) for o in taps]
            pred = (str(sum(int(x) for x in vals) % 2)
                    if all(x is not None for x in vals) else "unk")
        f[f"rule{r}_pred"] = pred
        s = 0
        for u in range(1, v + 1):
            for q in range(N_BITS):
                out = get(u, q)
                if out is None:
                    continue
                vals = [get(u - 1, (q + o) % N_BITS) for o in taps]
                if any(x is None for x in vals):
                    continue
                s += 1 if str(sum(int(x) for x in vals) % 2) == out else -1
        scores[r] = s
        f[f"agree{r}"] = str(max(-2, min(2, s)))
    mx = max(scores.values())
    best = [r for r in scores if scores[r] == mx]
    bp = {f[f"rule{r}_pred"] for r in best}
    f["best_pred"] = bp.pop() if (mx > 0 and len(bp) == 1
                                  and "unk" not in bp) else "unk"
    return f

FEATS = None
def entropy_b(labels):
    n = len(labels)
    p1 = sum(labels) / n
    if p1 in (0.0, 1.0):
        return 0.0
    return -p1 * math.log2(p1) - (1 - p1) * math.log2(1 - p1)

def id3(rows, labels, depth=0, max_depth=6, min_n=8):
    n = len(labels)
    p1 = sum(labels) / n
    node = {"maj": p1 >= 0.5}
    if p1 in (0.0, 1.0) or depth >= max_depth or n < min_n:
        return node
    base = entropy_b(labels)
    best_feat, best_gain, best_split = None, 1e-9, None
    for feat in FEATS:
        groups = {}
        for i in range(n):
            groups.setdefault(rows[i][feat], []).append(i)
        if len(groups) < 2:
            continue
        rem = sum(len(ix) * entropy_b([labels[i] for i in ix])
                  for ix in groups.values()) / n
        if base - rem > best_gain:
            best_feat, best_gain, best_split = feat, base - rem, groups
    if best_feat is None:
        return node
    node["feat"] = best_feat
    node["children"] = {
        val: id3([rows[i] for i in ix], [labels[i] for i in ix],
                 depth + 1, max_depth, min_n)
        for val, ix in best_split.items()}
    return node

def id3_predict(node, row):
    while "feat" in node:
        child = node["children"].get(row[node["feat"]])
        if child is None:
            break
        node = child
    return node["maj"]

def tree_size(node):
    if "feat" not in node:
        return 1, 1
    tot, dep = 1, 0
    for c in node["children"].values():
        t, d = tree_size(c)
        tot += t
        dep = max(dep, d)
    return tot, dep + 1

def twin_run(getter_of_slot, train_slots, test_slots):
    global FEATS
    rows_tr = [getter_of_slot(s) for s in train_slots]
    FEATS = sorted(rows_tr[0].keys())
    y_tr = [bool(truth(s)) for s in train_slots]
    tree = id3(rows_tr, y_tr)
    correct = {}
    for s in test_slots:
        correct[s] = (id3_predict(tree, getter_of_slot(s)) == bool(truth(s)))
    acc = float(np.mean([correct[s] for s in test_slots]))
    return acc, correct, tree

print("\n== Turing twin (ID3 automaton-feature tree) ==")
def occl_slot_feats(s):
    o, v, p = s
    return twin_features(log_getter(o), v, p)
twin_acc, twin_correct, twin_tree = twin_run(occl_slot_feats,
                                             TRAIN_SLOTS, TEST_SLOTS)
tsz, tdep = tree_size(twin_tree)
print(f"twin occluded-bit acc (test) = {twin_acc:.4f}  "
      f"(tree nodes={tsz} depth={tdep})")

# Bayes-filter ceiling (exact causal posterior majority; ties -> pooled_maj)
bayes_correct = []
bayes_ties = 0
for s in TEST_SLOTS:
    o, v, p = s
    surv = survivors[o][v]
    votes = [TRAJ[hs][v][p] for hs in surv]
    m = np.mean(votes)
    if abs(m - 0.5) < 1e-12:
        bayes_ties += 1
        pred = pooled_maj
    else:
        pred = int(m > 0.5)
    bayes_correct.append(pred == truth(s))
bayes_acc = float(np.mean(bayes_correct))
print(f"Bayes-filter ceiling acc (test) = {bayes_acc:.4f} (ties {bayes_ties})")

# ---- complementarity engine vs twin on test slots (loop-1 retest) ----------
comp = np.zeros((2, 2), dtype=int)
for s in TEST_SLOTS:
    comp[int(eng_correct[s]), int(twin_correct[s])] += 1
neither, twin_only = int(comp[0, 0]), int(comp[0, 1])
eng_only, both = int(comp[1, 0]), int(comp[1, 1])
n_c = len(TEST_SLOTS)
pe, pt = (both + eng_only) / n_c, (both + twin_only) / n_c
den = math.sqrt(pe * (1 - pe) * pt * (1 - pt))
phi = float((both / n_c - pe * pt) / den) if den > 1e-12 else float("nan")
agree_rate = float((both + neither) / n_c)
if eng_only == 0 and twin_only == 0:
    coupling = "redundant"
elif phi > 0.5:
    coupling = "largely_redundant"
elif phi < -0.2:
    coupling = "complementary"
else:
    coupling = "partially_independent"
print(f"complementarity [[neither,twin_only],[eng_only,both]] = "
      f"[[{neither},{twin_only}],[{eng_only},{both}]]  phi={phi:.4f}  "
      f"agree={agree_rate:.4f}  coupling={coupling}")

# ---- occlusion-free control (twin + engine; only the queried bit masked) ---
print("\n== occlusion-free control ==")
def occfree_slot_feats(s):
    o, v, p = s
    return twin_features(make_getter_occfree(o, v, p), v, p)
twin_free_acc, _, _ = twin_run(occfree_slot_feats, TRAIN_SLOTS, TEST_SLOTS)

# engine occlusion-free: cache state after full views 0..v-1, then apply view v
# minus the queried position
free_prefix = {}
for o in OBJ_IDS:
    rho = RHO0.copy()
    free_prefix[(o, 0)] = rho.copy()
    for v in range(N_VIEWS):
        for p in range(N_BITS):
            rho = unvec(STAGE_CH[(p, ORACLE[o][v][p])] @ vec(rho))
        free_prefix[(o, v + 1)] = rho.copy()
def eng_free_feats(s):
    o, v, p = s
    rho = free_prefix[(o, v)].copy()
    for q in range(N_BITS):
        if q == p:
            continue
        rho = unvec(STAGE_CH[(q, ORACLE[o][v][q])] @ vec(rho))
    return pauli_feats(rho)
eng_free_acc, _ = decode_per_position(eng_free_feats, TRAIN_SLOTS, TEST_SLOTS)
print(f"occlusion-free: twin acc={twin_free_acc:.4f} (occluded {twin_acc:.4f}); "
      f"engine acc={eng_free_acc:.4f} (occluded {eng_acc:.4f})")

# ==================================================================== JEPA
print("\n== torch JEPA-proto ==")
import torch
import torch.nn as nn
import torch.nn.functional as F
torch.manual_seed(SEED)

def view_tensor(o):
    x = np.zeros((N_VIEWS, 2 * N_BITS), dtype=np.float32)
    for v in range(N_VIEWS):
        for p in range(N_BITS):
            out = LOG[o][v][p]
            if out != "withheld":
                x[v, p] = 2.0 * int(out) - 1.0   # signed value
                x[v, N_BITS + p] = 1.0           # visibility flag
    return x

X_ALL = torch.tensor(np.stack([view_tensor(o) for o in OBJ_IDS]))  # (64,6,16)
tr_idx = [i for i, o in enumerate(OBJ_IDS) if o in TRAIN_OBJS]
LATENT = 32

class Jepa(nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(nn.Linear(2 * N_BITS, 64), nn.ReLU(),
                                 nn.Linear(64, LATENT))
        self.gru = nn.GRU(LATENT, LATENT, batch_first=True)
        self.pred = nn.Sequential(nn.Linear(LATENT, 64), nn.ReLU(),
                                  nn.Linear(64, LATENT))
    def forward(self, x):
        B, V, D = x.shape
        z = self.enc(x.reshape(B * V, D)).reshape(B, V, LATENT)
        h, _ = self.gru(z)
        return z, h

model = Jepa()
opt = torch.optim.Adam(model.parameters(), lr=1e-3)
Xtr = X_ALL[tr_idx]

def jepa_loss(x):
    z, h = model(x)
    zp = model.pred(h[:, :-1])                    # predict next-view latent
    zt = z[:, 1:].detach()                        # stop-grad target
    cos = F.cosine_similarity(zp, zt, dim=-1)
    ray = (1.0 - cos ** 2).mean()                 # ray-style loss, not MSE
    std = z.reshape(-1, LATENT).std(dim=0)
    var_reg = F.relu(1.0 - std).mean()            # anti-collapse
    return ray, var_reg, z

loss_first = loss_last = None
for ep in range(400):
    opt.zero_grad()
    ray, var_reg, _ = jepa_loss(Xtr)
    loss = ray + var_reg
    loss.backward()
    opt.step()
    if ep == 0:
        loss_first = float(ray)
    loss_last = float(ray)
print(f"JEPA train free energy (ray loss): epoch0={loss_first:.4f} "
      f"final={loss_last:.4f}")

with torch.no_grad():
    ray_all, _, _ = jepa_loss(X_ALL)
    te_idx = [i for i, o in enumerate(OBJ_IDS) if o in TEST_OBJS]
    z_all, h_all = model(X_ALL)
    ray_te, _, _ = jepa_loss(X_ALL[te_idx])
    H = h_all.numpy()                             # (64,6,32) context latents
    z_std = float(z_all.reshape(-1, LATENT).std(dim=0).mean())
print(f"JEPA free energy: all={float(ray_all):.4f} test={float(ray_te):.4f}; "
      f"latent std (collapse monitor)={z_std:.4f}")

jepa_acc, jepa_correct = decode_per_position(
    lambda s: H[OBJ_IDS.index(s[0]), s[1]], TRAIN_SLOTS, TEST_SLOTS)
print(f"JEPA occluded-bit acc (test) = {jepa_acc:.4f}")

# objects = latent clusters: ARI of KMeans(64) on all (obj,view) contexts
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
ctx = H.reshape(N_OBJECTS * N_VIEWS, LATENT)
ctx = ctx / (np.linalg.norm(ctx, axis=1, keepdims=True) + 1e-12)
obj_labels = np.repeat(np.arange(N_OBJECTS), N_VIEWS)
km = KMeans(n_clusters=N_OBJECTS, n_init=10, random_state=0).fit(ctx)
ari_real = float(adjusted_rand_score(obj_labels, km.labels_))
ari_rng = np.random.default_rng(SEED + 3)
ari_null = np.array([
    float(adjusted_rand_score(ari_rng.permutation(obj_labels), km.labels_))
    for _ in range(100)])
# within/between-object context cosine (attractor convergence, descriptive)
sim = ctx @ ctx.T
within_m = np.zeros_like(sim, dtype=bool)
for i in range(N_OBJECTS):
    within_m[i * N_VIEWS:(i + 1) * N_VIEWS, i * N_VIEWS:(i + 1) * N_VIEWS] = True
np.fill_diagonal(sim, np.nan)
within_cos = float(np.nanmean(np.where(within_m, sim, np.nan)))
between_cos = float(np.nanmean(np.where(~within_m, sim, np.nan)))
print(f"attractor check: ARI(real)={ari_real:.4f}; shuffled-id null "
      f"mean={ari_null.mean():.5f} p95={np.quantile(ari_null,0.95):.5f}")
print(f"  context cosine within-object={within_cos:.4f} "
      f"between-object={between_cos:.4f}")

# ==================================================================== CHECKS
checks = {
    "ground_truth_recovered_from_visible_probes_only": bool(gt_unique),
    "all_states_physical": bool(len(PHYS_VIOL) == 0),
    "cptp_stage_channels": bool(all(
        v["choi_min_eig"] > -1e-9 and v["tp_dev"] < 1e-9
        for v in cptp.values())),
    "engine_occluded_acc_above_computed_baseline": bool(eng_acc > BASELINE),
    "twin_occluded_acc_above_computed_baseline": bool(twin_acc > BASELINE),
    "jepa_occluded_acc_above_computed_baseline": bool(jepa_acc > BASELINE),
    "belief_persistence_holevo_above_permutation_null": bool(
        chi_real > float(np.quantile(chi_null, 0.95))),
    "frozen_engine_no_belief_persistence": bool(
        chi_froz <= float(np.quantile(chi_froz_null, 0.95))
        and froz_acc <= BASELINE + 0.03),
    "jepa_ari_above_shuffled_null": bool(
        ari_real > float(np.quantile(ari_null, 0.95))),
    "shuffled_object_ids_ari_collapses": bool(abs(float(ari_null.mean())) < 0.02),
    "occlusion_free_twin_catches_up": bool(twin_free_acc >= twin_acc + 0.05),
    "complementarity_sample_size_adequate": bool(n_c >= 100),
}
all_pass = all(checks.values())
print("\n== checks ==")
for k, v in checks.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
print(f"ALL_PASS: {all_pass}")

findings = []
findings.append(
    f"VERDICT (occluded-bit acc, {n_c} test slots, computed baseline "
    f"{BASELINE:.4f}): engine {eng_acc:.4f}, twin {twin_acc:.4f}, JEPA "
    f"{jepa_acc:.4f}, Bayes-filter ceiling {bayes_acc:.4f}.")
if twin_acc >= eng_acc:
    findings.append(
        f"HONEST NEGATIVE KEPT: the classical twin ({twin_acc:.4f}) matches or "
        f"beats the QIT engine ({eng_acc:.4f}) under occlusion — on this task "
        f"the 2-qubit register does not out-predict a rule-feature automaton.")
else:
    findings.append(
        f"engine beats twin under occlusion by {eng_acc - twin_acc:+.4f}.")
findings.append(
    f"loop-1 redundancy RETEST (hidden state now matters): complementarity "
    f"[[neither,twin_only],[eng_only,both]] = [[{neither},{twin_only}],"
    f"[{eng_only},{both}]], phi={phi:.4f}, agreement {agree_rate:.4f}, "
    f"computed coupling class: {coupling} (loop-1 verdict was "
    f"largely_redundant, phi 0.756).")
findings.append(
    f"belief persistence: mean Holevo chi(unprobed bit; register) = "
    f"{chi_real:.5f} bits vs permutation-null p95 "
    f"{float(np.quantile(chi_null,0.95)):.5f} (frozen engine {chi_froz:.5f} vs "
    f"its null p95 {float(np.quantile(chi_froz_null,0.95)):.5f}); per-position "
    f"chi {[round(c,5) for c in chi_by_pos]}.")
findings.append(
    f"occlusion-free control: twin {twin_acc:.4f} -> {twin_free_acc:.4f}, "
    f"engine {eng_acc:.4f} -> {eng_free_acc:.4f}; occlusion "
    f"{'is' if (twin_free_acc - twin_acc) > (eng_free_acc - eng_acc) else 'is NOT'} "
    f"the regime where the twin was being held back.")
findings.append(
    f"JEPA attractor check: KMeans-64 ARI {ari_real:.4f} vs shuffled-id null "
    f"p95 {float(np.quantile(ari_null,0.95)):.5f} (null mean "
    f"{float(ari_null.mean()):.5f}); within-object context cosine "
    f"{within_cos:.4f} vs between {between_cos:.4f}; free energy (ray) train "
    f"{loss_last:.4f}, test {float(ray_te):.4f}; latent std {z_std:.4f}.")
findings.append(
    f"frozen-engine control: occluded acc {froz_acc:.4f} (baseline "
    f"{BASELINE:.4f}); conditioning off removes the outcome channel.")
findings.append(
    f"ground truth for all 64 objects recovered from visible probes alone "
    f"(unique joint survivor per object); Bayes ties on test slots: "
    f"{bayes_ties}.")

receipt = dict(
    schema="loop2_world/intelligence/receipt_v1",
    lane="intelligence",
    sim_id="perception_intelligence_v0",
    date="2026-07-19",
    card_authority="system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md AMENDMENT v0.1 "
                   "(occluded-object perception; probes P5/P6 primary)",
    inputs=dict(
        world_events=EVENTS,
        world_receipt=WORLD_RECEIPT,
        stage64_receipt=STAGE64,
        engine_port_source=ENGINE_SOURCE,
        engine_port_note="faithful port of stage_superops/dissipator/unitary "
                         "superops and run-3 params (DT=0.5 LAM=0.7 GAM0=0.05 "
                         "TD=0.5); no new parameter tuning in this sim",
        rule_family_publicity="rule FAMILY read from the world receipt "
                              "parameters (public model class); per-object "
                              "hidden state never read -- ground truth "
                              "recovered from visible probes by exhaustive "
                              "consistency",
    ),
    protocol=dict(
        task="after visible probes of views 0..v, predict occluded bits of "
             "view v (causal)",
        split=dict(train_objects=sorted(TRAIN_OBJS),
                   test_objects=sorted(TEST_OBJS),
                   train_slots=len(TRAIN_SLOTS), test_slots=len(TEST_SLOTS)),
        baseline="train-selected majority rule (pooled vs per-position by "
                 "train acc) applied to test",
        engine="stage64 L stages; probe position p -> stage p conditioned on "
               "outcome bit; occluded probes skipped; register never reset "
               "across views; readout = 15 Pauli expectations -> per-position "
               "ridge (L engine only; R conjugate lane out of scope here)",
        twin="ID3 categorical tree on automaton features: last-seen/age, 4 "
             "rule-family predictions from view v-1, clipped per-rule "
             "agreement scores, best-rule consensus prediction, pos, view",
        jepa="view encoder MLP(16->64->32) + GRU(32) context + predictor "
             "MLP; ray loss 1-cos^2 on stop-grad normalized targets + "
             "variance anti-collapse; 400 epochs Adam 1e-3 on train objects; "
             "occluded-bit readout = per-position ridge on context latent",
        bayes_ceiling="exact causal survivor-set majority over the 1024-state "
                      "hidden space (ceiling, not a lane)",
    ),
    results=dict(
        computed_baseline=BASELINE,
        engine=dict(occluded_acc=eng_acc, occlusion_free_acc=eng_free_acc,
                    frozen_acc=froz_acc),
        twin=dict(occluded_acc=twin_acc, occlusion_free_acc=twin_free_acc,
                  tree_nodes=tsz, tree_depth=tdep),
        jepa=dict(occluded_acc=jepa_acc, ari_real=ari_real,
                  ari_null_mean=float(ari_null.mean()),
                  ari_null_p95=float(np.quantile(ari_null, 0.95)),
                  within_object_context_cos=within_cos,
                  between_object_context_cos=between_cos,
                  free_energy_train_final=loss_last,
                  free_energy_test=float(ray_te),
                  latent_std=z_std),
        bayes_ceiling=dict(acc=bayes_acc, ties=bayes_ties),
        complementarity=dict(neither=neither, twin_only=twin_only,
                             engine_only=eng_only, both=both,
                             phi=None if math.isnan(phi) else phi,
                             agreement_rate=agree_rate,
                             coupling_class=coupling,
                             loop1_verdict="largely_redundant (phi 0.756), "
                                           "engines_perception/results/"
                                           "processor_v0/receipt.json"),
        belief_persistence=dict(
            chi_mean_real=chi_real,
            chi_by_position=[float(c) for c in chi_by_pos],
            null_mean=float(chi_null.mean()),
            null_p95=float(np.quantile(chi_null, 0.95)),
            frozen_chi=chi_froz,
            frozen_null_p95=float(np.quantile(chi_froz_null, 0.95)),
            n_permutations=N_PERM),
        cptp_certificates=cptp,
        physicality_violations=PHYS_VIOL,
    ),
    checks=checks,
    all_pass=bool(all_pass),
    findings=findings,
    tool_manifest=dict(
        numpy="load_bearing: density-matrix algebra, Holevo chi, ridge decoders",
        scipy="load_bearing: expm of GKSL superoperators (exact CPTP stages)",
        torch="load_bearing: JEPA encoder/GRU/predictor training (ray loss)",
        sklearn="load_bearing: KMeans-64 clustering + adjusted_rand_score",
    ),
    claim_ceiling="unofficial working sim; occluded-object perception "
                  "evidence only; no bridge/axis/carrier claims",
    promotion_allowed=False,
    formal_admission_allowed=False,
)
receipt_path = os.path.join(OUTDIR, "receipt.json")
with open(receipt_path, "w") as f:
    json.dump(receipt, f, indent=2)
print(f"\nreceipt written: {receipt_path}")
print(json.dumps(dict(lane="intelligence",
                      file=os.path.join(HERE, "perception_intelligence_v0.py"),
                      all_pass=bool(all_pass), checks=checks,
                      findings=findings), indent=1))
