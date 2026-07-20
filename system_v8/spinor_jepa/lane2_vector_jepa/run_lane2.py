#!/usr/bin/env python3
"""Lane 2: ordinary vector JEPA (LeJEPA-style, unit-norm latent, ray loss).

Tournament: system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md (frozen, incl AMENDMENT
v0.1). Task: occluded-object perception on the world-source event log
(dynamics_on). Carrier: real vector latent z in R^16, unit-normalized, ray loss
L_ray = 1 - <z*, zhat>^2. No connection, no bracket, no grading, no Clifford
relation, no complex structure. Every added structure is CHARGED and listed in
the receipt.

Budgets (charged): 16 real latent DOF; params <= 60k; objects 0-47 train /
48-63 test; <=300 steps; batch 32; torch CPU float64; seed 20260719.

Blindness: reads ONLY the shared world_source data + this lane dir.
promotion_allowed: false.
"""
import json
import math
import os
import sys
import time
import random
import hashlib
from collections import defaultdict
from itertools import product

SEED = 20260719
LANE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(
    LANE_DIR, "..", "..", "loop2_world", "results", "world_source",
    "events_dynamics_on.jsonl"))
RESULTS = os.path.join(LANE_DIR, "results")
os.makedirs(RESULTS, exist_ok=True)

N_OBJ, N_VIEW, N_POS = 64, 6, 8
TRAIN_OBJ = list(range(48))
TEST_OBJ = list(range(48, 64))
STEPS = 300
BATCH = 32
GATE_PCT = 25.0
GATE_TIMEOUT_S = float(os.environ.get("GATE_TIMEOUT_S", "900"))

# ---------------------------------------------------------------- memory gate
def memory_gate():
    import psutil
    t0 = time.time()
    trace = []
    while True:
        vm = psutil.virtual_memory()
        free_pct = 100.0 * vm.available / vm.total
        trace.append(round(free_pct, 2))
        if free_pct > GATE_PCT:
            return True, free_pct, trace
        if time.time() - t0 > GATE_TIMEOUT_S:
            return False, free_pct, trace
        time.sleep(10)

gate_pass, gate_free_pct, gate_trace = memory_gate()
gate_record = {
    "criterion": "available memory > 25% before torch import",
    "pass": bool(gate_pass),
    "free_pct_at_decision": round(gate_free_pct, 2),
    "poll_trace_pct": gate_trace[-30:],
    "timeout_s": GATE_TIMEOUT_S,
}
if not gate_pass:
    out = {"lane": "lane2_vector_jepa", "all_pass": False,
           "memory_gate": gate_record,
           "findings": ["memory gate failed: torch never imported; no run"],
           "promotion_allowed": False}
    with open(os.path.join(RESULTS, "receipt.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
    sys.exit(2)

import torch  # noqa: E402  (gated import)
torch.set_default_dtype(torch.float64)
torch.manual_seed(SEED)
random.seed(SEED)

# ------------------------------------------------------------------ data load
def load_records(path):
    """(obj_idx, view, pos) -> (outcome_str, occluded_bool). Visible fields only."""
    recs = {}
    for line in open(path):
        ev = json.loads(line)
        for op in ev["payload"]["operations"]:
            d = {c["predicate"]: c["object"] for c in op["payload"]["claims"]}
            oi = int(d["has_object_id"].split("-")[1])
            recs[(oi, int(d["view_index"]), int(d["probe_position"]))] = (
                d["probe_outcome"], d["occluded"] == "true")
    return recs

records = load_records(DATA)
assert len(records) == N_OBJ * N_VIEW * N_POS

def build_features(recs):
    """x[obj,view] in R^30: per position one-hot (is0,is1,ismask) + view one-hot.
    LEAK RULE: when occluded flag is true the mask token is used and the
    outcome field is NEVER read."""
    X = torch.zeros(N_OBJ, N_VIEW, 3 * N_POS + N_VIEW)
    occ_mask = torch.zeros(N_OBJ, N_VIEW, N_POS, dtype=torch.bool)
    vis_bits = torch.full((N_OBJ, N_VIEW, N_POS), -1, dtype=torch.long)
    for (o, v, p), (out, occ) in recs.items():
        if occ:
            X[o, v, 3 * p + 2] = 1.0
            occ_mask[o, v, p] = True
        else:
            b = int(out)
            X[o, v, 3 * p + b] = 1.0
            vis_bits[o, v, p] = b
        X[o, v, 3 * N_POS + v] = 1.0
    return X, occ_mask, vis_bits

X, OCC, VIS = build_features(records)

# leak check: counterfactually rewrite every withheld outcome to random bits;
# features must be byte-identical because occluded outcomes are never read.
rng = random.Random(1234)
recs_perturbed = {k: ((str(rng.randint(0, 1)) if occ else out), occ)
                  for k, (out, occ) in records.items()}
X2, _, _ = build_features(recs_perturbed)
LEAK_CHECK_PASS = bool(torch.equal(X, X2))

# ------------------------------------------------- ground truth (EVAL ONLY)
# Scorer-side reconstruction: brute-force the 1024-state hidden space
# (256 words x 4 XOR-CA rules, periodic boundary; view v = v rule steps).
# Receipt of the world source certifies joint identifiability. NEVER used to
# build model inputs or training targets (training targets = visible bits only).
RULES = {0: [-1, 1], 1: [-1, 0, 1], 2: [0, 1], 3: [-1, 0]}

def ca_views(w0, rule):
    out, w = [w0], w0
    for _ in range(N_VIEW - 1):
        w = tuple(sum(w[(i + o) % N_POS] for o in RULES[rule]) % 2
                  for i in range(N_POS))
        out.append(w)
    return out

def reconstruct_gt():
    gt = {}
    for o in range(N_OBJ):
        cands = []
        for bits in product([0, 1], repeat=N_POS):
            for rule in range(4):
                vs = ca_views(bits, rule)
                ok = all(int(out) == vs[v][p]
                         for (oo, v, p), (out, occ) in records.items()
                         if oo == o and not occ)
                if ok:
                    cands.append(tuple(map(tuple, vs)))
        uniq = set(cands)
        assert len(uniq) == 1, (o, len(uniq))
        gt[o] = list(uniq)[0]
    return gt

GT = reconstruct_gt()

# --------------------------------------------------------------------- model
class Lane2Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        D = 3 * N_POS + N_VIEW  # 30
        self.enc = torch.nn.Sequential(
            torch.nn.Linear(D, 96), torch.nn.GELU(),
            torch.nn.Linear(96, 48), torch.nn.GELU(),
            torch.nn.Linear(48, 16))
        self.pred = torch.nn.Sequential(
            torch.nn.Linear(16 + 2 * N_VIEW, 64), torch.nn.GELU(),
            torch.nn.Linear(64, 16))
        self.readout = torch.nn.Sequential(
            torch.nn.Linear(16 + N_VIEW, 64), torch.nn.GELU(),
            torch.nn.Linear(64, N_POS))

    def encode(self, x):
        z = self.enc(x)
        return z / z.norm(dim=-1, keepdim=True).clamp_min(1e-12)

    def predict(self, z, src_v, tgt_v):
        sv = torch.nn.functional.one_hot(src_v, N_VIEW).to(z.dtype)
        tv = torch.nn.functional.one_hot(tgt_v, N_VIEW).to(z.dtype)
        zp = self.pred(torch.cat([z, sv, tv], dim=-1))
        return zp / zp.norm(dim=-1, keepdim=True).clamp_min(1e-12)

    def bits(self, z, view_v):
        tv = torch.nn.functional.one_hot(view_v, N_VIEW).to(z.dtype)
        return self.readout(torch.cat([z, tv], dim=-1))  # logits per position

def n_params(m):
    return sum(p.numel() for p in m.parameters())

def ray_loss(zhat, ztgt):
    return 1.0 - (zhat * ztgt).sum(-1) ** 2

def extra_mask(x, vis, k=2, gen=None):
    """Instrument update M_q: occlude up to k extra visible positions."""
    x = x.clone()
    for i in range(x.shape[0]):
        vis_pos = [p for p in range(N_POS) if vis[i, p] >= 0]
        gen.shuffle(vis_pos)
        for p in vis_pos[:k]:
            x[i, 3 * p:3 * p + 3] = torch.tensor([0.0, 0.0, 1.0])
    return x

def train_model(shuffle_pairing=False, seed=SEED):
    torch.manual_seed(seed)
    gen = random.Random(seed)
    model = Lane2Model()
    opt = torch.optim.Adam(model.parameters(), lr=3e-3)
    curve = []
    for step in range(STEPS):
        objs = [gen.choice(TRAIN_OBJ) for _ in range(BATCH)]
        va = torch.tensor([gen.randrange(N_VIEW) for _ in range(BATCH)])
        vb = torch.tensor([(a + 1 + gen.randrange(N_VIEW - 1)) % N_VIEW
                           for a in va.tolist()])
        tgt_objs = ([gen.choice(TRAIN_OBJ) for _ in range(BATCH)]
                    if shuffle_pairing else objs)
        xa = torch.stack([X[o, v] for o, v in zip(objs, va.tolist())])
        xb = torch.stack([X[o, v] for o, v in zip(tgt_objs, vb.tolist())])
        visa = torch.stack([VIS[o, v] for o, v in zip(objs, va.tolist())])
        visb = torch.stack([VIS[o, v] for o, v in zip(tgt_objs, vb.tolist())])
        xa_aug = extra_mask(xa, visa, k=2, gen=gen)

        za = model.encode(xa_aug)
        with torch.no_grad():
            zb = model.encode(xb)  # stop-gradient target
        zhat = model.predict(za, va, vb)
        L_jepa = ray_loss(zhat, zb).mean()

        # bit readout on VISIBLE bits only (cross-view + self-denoise)
        def bce_visible(logits, vis):
            m = vis >= 0
            if m.sum() == 0:
                return torch.tensor(0.0)
            return torch.nn.functional.binary_cross_entropy_with_logits(
                logits[m], vis[m].to(logits.dtype))
        L_bits = bce_visible(model.bits(zhat, vb), visb)
        L_self = bce_visible(model.bits(za, va), visa)

        C = (za - za.mean(0)).T @ (za - za.mean(0)) / BATCH
        L_iso = ((C - torch.eye(16) / 16.0) ** 2).sum()

        loss = L_jepa + 1.0 * L_bits + 0.5 * L_self + 0.05 * L_iso
        opt.zero_grad(); loss.backward(); opt.step()
        if step % 25 == 0 or step == STEPS - 1:
            curve.append({"step": step, "loss": round(float(loss), 5),
                          "ray": round(float(L_jepa), 5),
                          "bits": round(float(L_bits), 5)})
    return model, curve

# --------------------------------------------------------------- eval helpers
@torch.no_grad()
def all_latents(model, objs):
    Z = {}
    for o in objs:
        for v in range(N_VIEW):
            Z[(o, v)] = model.encode(X[o, v].unsqueeze(0))[0]
    return Z

@torch.no_grad()
def belief_latent(model, o, b):
    zs = []
    for a in range(N_VIEW):
        if a == b:
            continue
        za = model.encode(X[o, a].unsqueeze(0))
        zs.append(model.predict(za, torch.tensor([a]), torch.tensor([b]))[0])
    z = torch.stack(zs).mean(0)
    return z / z.norm().clamp_min(1e-12)

@torch.no_grad()
def occluded_accuracy(model, objs, mode="belief"):
    hit = tot = 0
    for o in objs:
        for b in range(N_VIEW):
            pos = [p for p in range(N_POS) if OCC[o, b, p]]
            if not pos:
                continue
            z = (belief_latent(model, o, b) if mode == "belief"
                 else model.encode(X[o, b].unsqueeze(0))[0])
            probs = torch.sigmoid(model.bits(z.unsqueeze(0),
                                             torch.tensor([b])))[0]
            for p in pos:
                hit += int((probs[p] > 0.5) == bool(GT[o][b][p]))
                tot += 1
    return hit / tot, tot

@torch.no_grad()
def mean_ray_loss(model, objs, gen):
    losses = []
    for o in objs:
        for a in range(N_VIEW):
            for b in range(N_VIEW):
                if a == b:
                    continue
                za = model.encode(X[o, a].unsqueeze(0))
                zb = model.encode(X[o, b].unsqueeze(0))
                zh = model.predict(za, torch.tensor([a]), torch.tensor([b]))
                losses.append(float(ray_loss(zh, zb)))
    return sum(losses) / len(losses)

def kmeans(Zm, k, seed, iters=100, restarts=20):
    best, best_inertia = None, None
    g = torch.Generator().manual_seed(seed)
    n = Zm.shape[0]
    for r in range(restarts):
        idx = torch.randperm(n, generator=g)[:k]
        cent = Zm[idx].clone()
        for _ in range(iters):
            d = torch.cdist(Zm, cent)
            lab = d.argmin(1)
            newc = torch.stack([
                Zm[lab == j].mean(0) if (lab == j).any() else cent[j]
                for j in range(k)])
            if torch.allclose(newc, cent):
                cent = newc; break
            cent = newc
        inertia = float(torch.cdist(Zm, cent).min(1).values.pow(2).sum())
        if best_inertia is None or inertia < best_inertia:
            best_inertia, best = inertia, lab.clone()
    return best

def ari(labels_a, labels_b):
    from math import comb
    n = len(labels_a)
    cont = defaultdict(int)
    for x, y in zip(labels_a, labels_b):
        cont[(x, y)] += 1
    a = defaultdict(int); b = defaultdict(int)
    for (x, y), c in cont.items():
        a[x] += c; b[y] += c
    sum_ij = sum(comb(c, 2) for c in cont.values())
    sum_a = sum(comb(c, 2) for c in a.values())
    sum_b = sum(comb(c, 2) for c in b.values())
    exp = sum_a * sum_b / comb(n, 2)
    mx = (sum_a + sum_b) / 2
    return (sum_ij - exp) / (mx - exp) if mx != exp else 0.0

def von_neumann_bits(rho):
    ev = torch.linalg.eigvalsh(rho).clamp_min(0)
    ev = ev / ev.sum()
    ev = ev[ev > 1e-15]
    return float(-(ev * torch.log2(ev)).sum())

@torch.no_grad()
def holevo(Z, objs, label_of=None):
    """chi = S(rho_bar) - mean_o S(rho_o); rho_o = mean_view zz^T (real)."""
    groups = defaultdict(list)
    for (o, v), z in Z.items():
        key = label_of((o, v)) if label_of else o
        groups[key].append(z)
    rhos = []
    for key in sorted(groups):
        zs = torch.stack(groups[key])
        rhos.append(zs.T @ zs / zs.shape[0])
    rho_bar = torch.stack(rhos).mean(0)
    return von_neumann_bits(rho_bar) - sum(von_neumann_bits(r) for r in rhos) / len(rhos)

# ------------------------------------------------------------------ training
t0 = time.time()
model, curve = train_model(shuffle_pairing=False)
ctrl_model, ctrl_curve = train_model(shuffle_pairing=True)
train_secs = time.time() - t0

P_ENC = n_params(model.enc); P_PRED = n_params(model.pred)
P_READ = n_params(model.readout); P_TOT = n_params(model)
assert P_TOT <= 60000

gen = random.Random(SEED + 1)
Z_test = all_latents(model, TEST_OBJ)

# ------------------------------------------------------------------- metrics
occ_acc_belief, n_occ_test = occluded_accuracy(model, TEST_OBJ, "belief")
occ_acc_self, _ = occluded_accuracy(model, TEST_OBJ, "self")
occ_acc_train, _ = occluded_accuracy(model, TRAIN_OBJ, "belief")
ctrl_occ_acc, _ = occluded_accuracy(ctrl_model, TEST_OBJ, "belief")
# majority-class chance on the scored occluded test bits
occ_bits = [GT[o][b][p] for o in TEST_OBJ for b in range(N_VIEW)
            for p in range(N_POS) if OCC[o, b, p]]
chance = max(occ_bits.count(0), occ_bits.count(1)) / len(occ_bits)

ray_train = mean_ray_loss(model, TRAIN_OBJ, gen)
ray_test = mean_ray_loss(model, TEST_OBJ, gen)

# ARI: kmeans k=16 on the 96 test-view latents vs object ids + shuffled null
Zm = torch.stack([Z_test[(o, v)] for o in TEST_OBJ for v in range(N_VIEW)])
true_lab = [o for o in TEST_OBJ for _ in range(N_VIEW)]
km_lab = kmeans(Zm, k=len(TEST_OBJ), seed=SEED)
ari_real = ari(true_lab, km_lab.tolist())
g = random.Random(SEED + 2)
ari_null = []
for _ in range(100):
    sh = true_lab[:]; g.shuffle(sh)
    ari_null.append(ari(sh, km_lab.tolist()))
ari_null_mean = sum(ari_null) / len(ari_null)
ari_null_p95 = sorted(ari_null)[94]
ctrl_km = kmeans(torch.stack([all_latents(ctrl_model, TEST_OBJ)[(o, v)]
                              for o in TEST_OBJ for v in range(N_VIEW)]),
                 k=len(TEST_OBJ), seed=SEED)
ari_ctrl = ari(true_lab, ctrl_km.tolist())

# Holevo belief persistence + permutation null
chi = holevo(Z_test, TEST_OBJ)
keys = [(o, v) for o in TEST_OBJ for v in range(N_VIEW)]
g2 = random.Random(SEED + 3)
chi_null = []
for _ in range(200):
    perm = keys[:]; g2.shuffle(perm)
    mapping = dict(zip(keys, perm))
    chi_null.append(holevo(Z_test, TEST_OBJ, label_of=lambda k: mapping[k][0]))
chi_null_p95 = sorted(chi_null)[189]
holevo_above_null = bool(chi > chi_null_p95)
holevo_margin = chi - chi_null_p95

# -------------------------------------------------------------------- probes
probes = {}

probes["P1_sign_lift_memory"] = {
    "score": 0.0, "not_applicable_for_this_carrier": True,
    "reason": ("real unit-vector carrier with ray loss quotients out the sign "
               "(z ~ -z); no connection, no coherent-path or holonomy "
               "structure exists to traverse a 2pi vs 4pi loop; per the card, "
               "a lift claim requires connection + interference witness, "
               "which this carrier does not define"),
    "measurement": "structural: carrier defines no loop transport to test"}

@torch.no_grad()
def probe_chirality():
    perm = [(-p) % N_POS for p in range(N_POS)]
    wins = tot = 0
    for o in TEST_OBJ:
        for b in range(N_VIEW):
            x = X[o, b]
            xm = x.clone()
            for p in range(N_POS):
                xm[3 * p:3 * p + 3] = x[3 * perm[p]:3 * perm[p] + 3]
            if torch.equal(x, xm):
                continue
            z = model.encode(x.unsqueeze(0))[0]
            zm = model.encode(xm.unsqueeze(0))[0]
            d_mir = float(1 - (z @ zm) ** 2)
            d_same = sum(float(1 - (z @ Z_test[(o, v)]) ** 2)
                         for v in range(N_VIEW) if v != b) / (N_VIEW - 1)
            wins += int(d_mir > d_same); tot += 1
    return wins / tot, tot

p2, p2_n = probe_chirality()
probes["P2_chirality"] = {
    "score": round(p2, 4),
    "measurement": ("fraction of test views (mirror-distinct only, n=%d) where "
                    "ray distance to the position-mirrored view exceeds mean "
                    "ray distance to same-object other views" % p2_n)}

@torch.no_grad()
def probe_order_bracket():
    g3 = random.Random(SEED + 4)
    d_ab, d_abc = [], []
    for _ in range(200):
        o = g3.choice(TEST_OBJ); v = g3.randrange(N_VIEW)
        ps = g3.sample(range(N_POS), 3)
        def mask_seq(x, seq):
            x = x.clone()
            for p in seq:
                x[3 * p:3 * p + 3] = torch.tensor([0.0, 0.0, 1.0])
            return x
        x = X[o, v]
        z1 = model.encode(mask_seq(x, [ps[0], ps[1]]).unsqueeze(0))[0]
        z2 = model.encode(mask_seq(x, [ps[1], ps[0]]).unsqueeze(0))[0]
        d_ab.append(float(1 - (z1 @ z2) ** 2))
        # ((a b) c) vs (a (b c)) -- flat application; grouping cannot register
        z3 = model.encode(mask_seq(mask_seq(x, [ps[0], ps[1]]), [ps[2]]).unsqueeze(0))[0]
        z4 = model.encode(mask_seq(mask_seq(x, [ps[0]]), [ps[1], ps[2]]).unsqueeze(0))[0]
        d_abc.append(float(1 - (z3 @ z4) ** 2))
    return sum(d_ab) / len(d_ab), sum(d_abc) / len(d_abc)

p3, p4 = probe_order_bracket()
probes["P3_order_witness"] = {
    "score": round(p3, 6),
    "measurement": ("mean ray distance between M_a.M_b and M_b.M_a occlusion "
                    "orders over 200 trials; instrument updates commute on the "
                    "observation and the carrier holds no internal "
                    "non-commuting update -- honest 0 expected")}
probes["P4_bracket_witness"] = {
    "score": round(p4, 6),
    "measurement": ("mean ray distance between (M_a M_b) M_c and M_a (M_b M_c) "
                    "groupings over 200 trials; flat associative application, "
                    "no bracket structure in the carrier -- honest 0 expected")}

probes["P5_hidden_mode_belief"] = {
    "score": round(occ_acc_belief, 4),
    "measurement": ("test occluded-bit accuracy via multi-view belief: "
                    "normalized mean of predictor outputs from all other views "
                    "-> readout at occluded positions vs reconstructed CA "
                    "ground truth (n=%d bits; majority chance %.3f)"
                    % (n_occ_test, chance))}

@torch.no_grad()
def probe_counterfactual():
    g3 = random.Random(SEED + 5)
    wins = tot = 0
    for o in TEST_OBJ:
        for a in range(N_VIEW):
            for b in range(N_VIEW):
                if a == b:
                    continue
                bp = g3.choice([v for v in range(N_VIEW) if v not in (a, b)])
                za = model.encode(X[o, a].unsqueeze(0))
                zb = Z_test[(o, b)]
                zh = model.predict(za, torch.tensor([a]), torch.tensor([b]))[0]
                zc = model.predict(za, torch.tensor([a]), torch.tensor([bp]))[0]
                wins += int(float((zh @ zb) ** 2) > float((zc @ zb) ** 2))
                tot += 1
    return wins / tot, tot

p6, p6_n = probe_counterfactual()
probes["P6_counterfactual_action"] = {
    "score": round(p6, 4),
    "measurement": ("fraction of ordered test pairs (n=%d) where the predictor "
                    "conditioned on the true target-view action lands closer "
                    "(ray sim) to the true target latent than the same "
                    "predictor with a counterfactual action label" % p6_n)}

@torch.no_grad()
def probe_reachability():
    g3 = random.Random(SEED + 6)
    pos, neg = [], []
    for o in TEST_OBJ:
        for a in range(N_VIEW):
            for b in range(N_VIEW):
                if a == b:
                    continue
                za = model.encode(X[o, a].unsqueeze(0))
                zh = model.predict(za, torch.tensor([a]), torch.tensor([b]))[0]
                pos.append(float((zh @ Z_test[(o, b)]) ** 2))
                o2 = g3.choice([q for q in TEST_OBJ if q != o])
                neg.append(float((zh @ Z_test[(o2, b)]) ** 2))
    wins = ties = 0
    for x in pos:
        for y in neg[:60]:
            wins += x > y; ties += x == y
    auc = (wins + 0.5 * ties) / (len(pos) * 60)
    return auc, len(pos)

p7, p7_n = probe_reachability()
probes["P7_prediction_vs_reachability"] = {
    "score": round(p7, 4),
    "measurement": ("AUC separating predictor similarity to the genuinely "
                    "reachable same-object target view (n=%d) from similarity "
                    "to the same view index of a different object; similarity "
                    "!= attainability unless AUC >> 0.5" % p7_n),
    "caveat": ("carrier has no explicit budget/viability structure; this is a "
               "similarity-based proxy, the honest weak form for lane 2")}

@torch.no_grad()
def probe_persistence():
    hits = tot = 0
    keys = [(o, v) for o in TEST_OBJ for v in range(N_VIEW)]
    for i, (o, v) in enumerate(keys):
        z = Z_test[(o, v)]
        best, best_s = None, -1
        for j, (o2, v2) in enumerate(keys):
            if i == j:
                continue
            s = float((z @ Z_test[(o2, v2)]) ** 2)
            if s > best_s:
                best_s, best = s, o2
        hits += int(best == o); tot += 1
    return hits / tot, tot

p8, p8_n = probe_persistence()
probes["P8_cross_view_persistence"] = {
    "score": round(p8, 4),
    "measurement": ("nearest-neighbour retrieval over the %d test-view "
                    "latents (ray sim): fraction whose NN is another view of "
                    "the same object; chance = 5/95 = 0.053" % p8_n)}

@torch.no_grad()
def probe_contraction():
    g3 = torch.Generator().manual_seed(SEED + 7)
    contracted = tot = 0
    ratios = []
    for o in TEST_OBJ:
        for v in range(N_VIEW):
            z0 = Z_test[(o, v)]
            eps = torch.randn(16, generator=g3)
            z0p = z0 + 0.05 * eps
            z0p = z0p / z0p.norm()
            z, zp = z0.clone(), z0p.clone()
            cur = v
            for _ in range(12):
                nxt = (cur + 1) % N_VIEW
                z = model.predict(z.unsqueeze(0), torch.tensor([cur]),
                                  torch.tensor([nxt]))[0]
                zp = model.predict(zp.unsqueeze(0), torch.tensor([cur]),
                                   torch.tensor([nxt]))[0]
                cur = nxt
            d0 = float(1 - (z0 @ z0p) ** 2)
            dk = float(1 - (z @ zp) ** 2)
            if d0 > 1e-12:
                contracted += int(dk < d0); tot += 1
                ratios.append(dk / d0)
    return contracted / tot, sum(ratios) / len(ratios), tot

p9, p9_ratio, p9_n = probe_contraction()
probes["P9_contraction_attractor"] = {
    "score": round(p9, 4),
    "mean_contraction_ratio": round(p9_ratio, 4),
    "measurement": ("fraction of %d perturbed test latents whose ray distance "
                    "to the unperturbed trajectory shrinks after 12 cyclic "
                    "predictor iterations; no energy/Hopfield structure is "
                    "charged, so any contraction is emergent from the "
                    "predictor map alone" % p9_n)}

@torch.no_grad()
def probe_gauge():
    g3 = torch.Generator().manual_seed(SEED + 8)
    M = (Zm @ Zm.T) ** 2
    passes = 0
    trials = 20
    for _ in range(trials):
        A = torch.randn(16, 16, generator=g3)
        Q, _ = torch.linalg.qr(A)
        MQ = ((Zm @ Q.T) @ (Zm @ Q.T).T) ** 2
        if float((M - MQ).abs().max()) < 1e-10:
            passes += 1
    return passes / trials

p10 = probe_gauge()
probes["P10_gauge_basis_invariance"] = {
    "score": round(p10, 4),
    "measurement": ("fraction of 20 random O(16) latent-basis changes under "
                    "which the pairwise ray-similarity matrix of test latents "
                    "is unchanged to 1e-10 (the ray metric is exactly "
                    "O(16)-invariant); caveat: the bit-readout and predictor "
                    "heads are basis-FIXED, so full-model gauge invariance "
                    "does not hold and is not claimed")}

# ------------------------------------------------------------------- receipt
data_hash = hashlib.sha256(open(DATA, "rb").read()).hexdigest()[:16]

charges = [
    "field: R (real numbers only)",
    "latent space: unit sphere S^15 in R^16 (norm-1 constraint; the charged 16 real DOF)",
    "pairing: Euclidean inner product; ray similarity <z,z'>^2",
    "signature: positive-definite Euclidean (16,0)",
    "loss: ray metric L_ray = 1 - <z*,zhat>^2 (quotients latent sign)",
    "action conditioning: source+target view one-hots (12 dims) into predictor",
    "asymmetry: stop-gradient target encoder (LeJEPA/SimSiam-style)",
    "regularizer: batch-covariance isotropy penalty (LeJEPA SIGReg-lite)",
    "instrument update M_q: position masking to a mask token (training augmentation)",
    "readout head: latent+view -> 8 bit logits (probe decoder, counted in params)",
    "NOT charged: connection, bracket, grading, Clifford relation, complex/quaternion structure, factorization",
]

findings = [
    "memory gate passed at %.2f%% free after polling (trace in receipt)" % gate_free_pct,
    "ground truth for scoring reconstructed scorer-side by brute-forcing the "
    "1024-state hidden space against visible bits (unique for all 64 objects); "
    "never used in features or training targets",
    "P1 honest not_applicable: no lift/connection structure in a real vector carrier",
    "P3/P4 honest ~0: commuting/associative instrument updates cannot witness order or bracket",
]

receipt = {
    "lane": "lane2_vector_jepa",
    "sim_id": "lane2_vector_jepa_v0",
    "classification": "tournament_lane_working_sim",
    "card_authority": "system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md (frozen, AMENDMENT v0.1)",
    "carrier": "ordinary vector JEPA (LeJEPA-style): unit-norm real 16-d latent, ray loss",
    "seed": SEED,
    "python": sys.version.split()[0],
    "torch": torch.__version__,
    "dtype": "float64",
    "device": "cpu",
    "data": {"path": DATA, "sha256_16": data_hash, "events": 3072,
             "objects": N_OBJ, "views": N_VIEW, "positions": N_POS},
    "split": {"train_objects": "0-47", "test_objects": "48-63"},
    "budgets": {
        "latent_real_dof": 16,
        "params_encoder": P_ENC, "params_predictor": P_PRED,
        "params_readout": P_READ, "params_total": P_TOT,
        "params_budget": 60000, "params_within_budget": P_TOT <= 60000,
        "train_steps": STEPS, "batch": BATCH,
        "train_wall_seconds": round(train_secs, 1)},
    "memory_gate": gate_record,
    "metrics": {
        "occluded_bit_accuracy_test_belief": round(occ_acc_belief, 4),
        "occluded_bit_accuracy_test_selfview": round(occ_acc_self, 4),
        "occluded_bit_accuracy_train_belief": round(occ_acc_train, 4),
        "occluded_bits_scored_test": n_occ_test,
        "occluded_majority_chance": round(chance, 4),
        "belief_persistence_holevo_bits": round(chi, 4),
        "holevo_permutation_null_p95": round(chi_null_p95, 4),
        "holevo_above_permutation_null": holevo_above_null,
        "holevo_margin_bits": round(holevo_margin, 4),
        "ray_loss_train": round(ray_train, 5),
        "ray_loss_test": round(ray_test, 5),
        "latent_cluster_ari_test": round(ari_real, 4),
        "ari_shuffled_null_mean": round(ari_null_mean, 4),
        "ari_shuffled_null_p95": round(ari_null_p95, 4)},
    "controls": {
        "shuffled_object_pairing_model": {
            "occluded_bit_accuracy_test_belief": round(ctrl_occ_acc, 4),
            "latent_cluster_ari_test": round(ari_ctrl, 4),
            "note": "identical arch/budget trained with target views drawn "
                    "from random other objects (object binding broken)"},
        "leak_check_occluded_bits_never_in_features": LEAK_CHECK_PASS,
        "leak_check_method": "counterfactual rebuild: every withheld outcome "
                             "rewritten to random bits; feature tensors "
                             "byte-identical"},
    "probes": probes,
    "train_curve": curve,
    "control_train_curve_tail": ctrl_curve[-2:],
    "charges": charges,
    "findings": findings,
    "promotion_allowed": False,
    "claim_ceiling": "working_sim tournament lane; no minimality or spinor "
                     "verdict is made here -- scorer is a separate agent",
}

gates = {
    "ran_to_completion": True,
    "memory_gate": bool(gate_pass),
    "params_within_budget": P_TOT <= 60000,
    "steps_within_budget": STEPS <= 300,
    "leak_check": LEAK_CHECK_PASS,
    "controls_behave": (ctrl_occ_acc <= occ_acc_belief and ari_ctrl <= ari_real),
    "all_probes_scored": len(probes) == 10,
}
receipt["gates"] = gates
receipt["all_pass"] = all(gates.values())

with open(os.path.join(RESULTS, "receipt.json"), "w") as f:
    json.dump(receipt, f, indent=1)
print(json.dumps({k: receipt[k] for k in
                  ["lane", "all_pass", "gates", "metrics", "budgets"]}, indent=1))
print("probe scores:", {k: v["score"] for k, v in probes.items()})
print("receipt ->", os.path.join(RESULTS, "receipt.json"))
