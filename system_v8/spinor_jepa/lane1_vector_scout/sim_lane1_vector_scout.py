#!/usr/bin/env python3
"""SPINOR_JEPA tournament lane 1: six-dim vector scout control (historical control).

Authority: system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md incl AMENDMENT v0.1
(occluded-object perception). Carrier: real vector latent, tanh + linear layers,
coordinate MSE training loss (allowed for THIS control lane only per card lane 1).
Budget matching (charged): exactly 16 real latent DOF, encoder/predictor <= 60k
params, objects 0-47 train / 48-63 test, <= 300 steps, batch 32, torch CPU float64.

promotion_allowed: false. Ceiling: tournament control-lane receipt.
Blindness: reads ONLY the shared world-source events + this lane dir.
"""

from __future__ import annotations

import json
import math
import pathlib
import random
import sys
import time

# ---------------------------------------------------------------- memory gate
GATE_PCT = 25.0
GATE_RETRIES = 20
GATE_SLEEP_S = 30


def memory_gate() -> dict:
    import psutil

    history = []
    for attempt in range(GATE_RETRIES):
        vm = psutil.virtual_memory()
        pct_free = 100.0 * vm.available / vm.total
        history.append(round(pct_free, 2))
        if pct_free > GATE_PCT:
            return {"pass": True, "pct_free_at_import": round(pct_free, 2),
                    "attempts": attempt + 1, "history": history}
        if attempt < GATE_RETRIES - 1:
            time.sleep(GATE_SLEEP_S)
    return {"pass": False, "pct_free_at_import": history[-1],
            "attempts": GATE_RETRIES, "history": history}


MEM_GATE = memory_gate()
if not MEM_GATE["pass"]:
    out = {"lane": "lane1_vector_scout", "all_pass": False,
           "aborted": "memory_gate_below_25pct_after_retries",
           "memory_gate": MEM_GATE}
    print(json.dumps(out, indent=2))
    sys.exit(3)

import numpy as np  # noqa: E402
import torch  # noqa: E402

torch.set_default_dtype(torch.float64)

SEED = 20260719
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

ROOT = pathlib.Path(__file__).resolve().parent
EVENTS = (ROOT.parent.parent / "loop2_world" / "results" / "world_source" /
          "events_dynamics_on.jsonl")
OUT = ROOT / "results" / "receipt.json"

N_OBJ, N_VIEW, N_POS = 64, 6, 8
TRAIN_OBJS = list(range(0, 48))
TEST_OBJS = list(range(48, 64))
LATENT = 16
MAX_STEPS = 300
BATCH = 32
RULE_FAMILY = {0: [-1, 1], 1: [-1, 0, 1], 2: [0, 1], 3: [-1, 0]}
# mirror pairs under position reversal: rule2 taps [0,1] <-> rule3 taps [-1,0]
CHIRAL_RULES = (2, 3)

# ------------------------------------------------------------------ data load


def load_events(path: pathlib.Path):
    """outcome[obj,view,pos] in {0,1}; occl[obj,view,pos] bool; raw strings kept."""
    outcome = -np.ones((N_OBJ, N_VIEW, N_POS), dtype=np.int64)
    occl = np.zeros((N_OBJ, N_VIEW, N_POS), dtype=bool)
    n = 0
    for line in path.open():
        ev = json.loads(line)
        for op in ev["payload"]["operations"]:
            claims = {c["predicate"]: c["object"] for c in op["payload"]["claims"]}
            o = int(claims["has_object_id"].split("-")[1])
            v = int(claims["view_index"])
            p = int(claims["probe_position"])
            if claims["occluded"] == "true":
                occl[o, v, p] = True
                assert claims["probe_outcome"] == "withheld"
            else:
                outcome[o, v, p] = int(claims["probe_outcome"])
            n += 1
    assert n == N_OBJ * N_VIEW * N_POS
    assert ((outcome >= 0) ^ occl).all(), "every cell either visible-valued or occluded"
    return outcome, occl


# ------------------------------------------- CA solve (SCORING GROUND TRUTH ONLY)


def ca_step(word: np.ndarray, taps) -> np.ndarray:
    new = np.zeros_like(word)
    for t in taps:
        new ^= np.roll(word, -t)
    return new


def solve_objects(outcome: np.ndarray, occl: np.ndarray):
    """Enumerate 4 rules x 256 words per object against VISIBLE bits only.

    Used exclusively for evaluation labels (occluded-bit truth + rule id).
    Never enters model features. Receipt joint_identifiability says unique."""
    words = ((np.arange(256)[:, None] >> np.arange(N_POS)[None, :]) & 1).astype(np.int64)
    truth = np.zeros((N_OBJ, N_VIEW, N_POS), dtype=np.int64)
    rule_of = np.zeros(N_OBJ, dtype=np.int64)
    survivors_count = np.zeros(N_OBJ, dtype=np.int64)
    for o in range(N_OBJ):
        survivors = []
        for r, taps in RULE_FAMILY.items():
            state = words.copy()  # (256, 8) at view 0
            ok = np.ones(256, dtype=bool)
            traj = []
            for v in range(N_VIEW):
                traj.append(state.copy())
                vis = ~occl[o, v]
                if vis.any():
                    ok &= (state[:, vis] == outcome[o, v, vis][None, :]).all(axis=1)
                state = ca_step_batch(state, taps)
            for w in np.nonzero(ok)[0]:
                survivors.append((r, np.stack([t[w] for t in traj])))
        survivors_count[o] = len(survivors)
        assert len(survivors) == 1, f"object {o}: {len(survivors)} survivors"
        rule_of[o], truth[o] = survivors[0]
    vis = ~occl
    assert (truth[vis] == outcome[vis]).all(), "derived truth must match visible bits"
    return truth, rule_of, survivors_count


def ca_step_batch(states: np.ndarray, taps) -> np.ndarray:
    new = np.zeros_like(states)
    for t in taps:
        new ^= np.roll(states, -t, axis=1)
    return new


# --------------------------------------------------------------- features


def build_features(outcome: np.ndarray, occl: np.ndarray) -> torch.Tensor:
    """x[obj,view] = flatten(8 x [is1,is0,is_masked]) ++ onehot6(view). Dim 30.

    Occluded cells contribute ONLY the mask channel — leak check rebuilds with
    garbage in withheld cells and asserts byte-identical tensors."""
    x = np.zeros((N_OBJ, N_VIEW, N_POS * 3 + N_VIEW))
    for o in range(N_OBJ):
        for v in range(N_VIEW):
            for p in range(N_POS):
                base = 3 * p
                if occl[o, v, p]:
                    x[o, v, base + 2] = 1.0
                elif outcome[o, v, p] == 1:
                    x[o, v, base + 0] = 1.0
                else:
                    x[o, v, base + 1] = 1.0
            x[o, v, N_POS * 3 + v] = 1.0
    return torch.tensor(x)


def leak_check(outcome, occl, feats) -> dict:
    rng = np.random.default_rng(0)
    garbage = outcome.copy()
    garbage[occl] = rng.integers(0, 2, size=int(occl.sum()))
    feats2 = build_features(garbage, occl)
    identical = bool(torch.equal(feats, feats2))
    return {"pass": identical,
            "measurement": "features rebuilt with random garbage in all withheld "
                           "cells; torch.equal on the two feature tensors",
            "identical": identical}


# --------------------------------------------------------------- model

IN_DIM = N_POS * 3 + N_VIEW  # 30


class VectorScout(torch.nn.Module):
    """Tanh-latent linear carrier. Belief state = exactly 16 real DOF."""

    def __init__(self):
        super().__init__()
        self.enc = torch.nn.Linear(IN_DIM, LATENT)     # per-view embedding
        self.Ub = torch.nn.Linear(LATENT, LATENT, bias=False)   # belief <- belief
        self.Vb = torch.nn.Linear(LATENT, LATENT)      # belief <- embedding
        self.trans = torch.nn.Linear(LATENT, LATENT)   # action: advance one view
        self.dec = torch.nn.Linear(LATENT, N_POS)      # outcomes of current view

    def embed(self, x):
        return torch.tanh(self.enc(x))

    def belief_step(self, b, z):
        return torch.tanh(self.Ub(b) + self.Vb(z))

    def roll(self, x_seq):
        """x_seq (B, V, 30) -> beliefs (B, V, 16), embeddings (B, V, 16)."""
        z = self.embed(x_seq)
        b = torch.zeros(x_seq.shape[0], LATENT)
        beliefs = []
        for v in range(x_seq.shape[1]):
            b = self.belief_step(b, z[:, v])
            beliefs.append(b)
        return torch.stack(beliefs, dim=1), z

    def predict_next_embedding(self, b):
        return torch.tanh(self.trans(b))

    def decode(self, b):
        return torch.tanh(self.dec(b))


def param_count(m: torch.nn.Module) -> int:
    return sum(p.numel() for p in m.parameters())


# --------------------------------------------------------------- training


def train(model, feats, outcome, occl, truth_unused=None):
    """MSE control-lane training. Targets ONLY bits visible in the data
    (artificial extra masks hide them from the encoder, truth stays known).
    truth_unused is never touched here — occluded bits carry no gradient."""
    opt = torch.optim.Adam(model.parameters(), lr=1e-2)
    vis_np = ~occl
    target = torch.tensor(np.where(outcome == 1, 1.0, -1.0))  # occluded cells excluded via mask
    vis = torch.tensor(vis_np)
    gen = torch.Generator().manual_seed(SEED)
    losses = []
    for step in range(MAX_STEPS):
        idx = torch.tensor([TRAIN_OBJS[i] for i in
                            torch.randperm(len(TRAIN_OBJS), generator=gen)[:BATCH]])
        x = feats[idx].clone()
        vmask = vis[idx]
        # artificial masking: hide 25% of visible cells from the encoder
        drop = (torch.rand(len(idx), N_VIEW, N_POS, generator=gen) < 0.25) & vmask
        for p in range(N_POS):
            trip = x[:, :, 3 * p:3 * p + 3]
            d = drop[:, :, p]
            trip[d] = torch.tensor([0.0, 0.0, 1.0])
        beliefs, _ = model.roll(x)
        # clean-view embeddings as JEPA targets (stop-grad)
        with torch.no_grad():
            z_clean = model.embed(feats[idx])
        yhat = model.decode(beliefs.reshape(-1, LATENT)).reshape(len(idx), N_VIEW, N_POS)
        recon = ((yhat - target[idx]) ** 2 * vmask).sum() / vmask.sum()
        zhat = model.predict_next_embedding(beliefs[:, :-1].reshape(-1, LATENT))
        ztgt = z_clean[:, 1:].reshape(-1, LATENT)
        jepa = ((zhat - ztgt) ** 2).mean()
        loss = recon + jepa
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss))
    return losses


# --------------------------------------------------------------- metrics helpers


def cos2(a, b, dim=-1, eps=1e-12):
    num = (a * b).sum(dim) ** 2
    den = (a * a).sum(dim) * (b * b).sum(dim) + eps
    return num / den


def ray_loss(a, b):
    return float((1.0 - cos2(a, b)).mean())


def causal_eval(model, feats, outcome, occl, truth, objs):
    """Causal belief over real (unmasked-extra) inputs; decode occluded bits."""
    with torch.no_grad():
        beliefs, z = model.roll(feats[objs])
        yhat = model.decode(beliefs.reshape(-1, LATENT)).reshape(len(objs), N_VIEW, N_POS)
    pred = (yhat.numpy() > 0).astype(np.int64)
    occ = occl[objs]
    acc = float((pred[occ] == truth[objs][occ]).mean())
    return acc, beliefs, z, yhat


def von_neumann_entropy(rho):
    w = np.linalg.eigvalsh(rho)
    w = np.clip(w, 1e-15, None)
    w = w / w.sum()
    return float(-(w * np.log2(w)).sum())


def holevo_chi(beliefs_np, labels):
    u = beliefs_np / (np.linalg.norm(beliefs_np, axis=1, keepdims=True) + 1e-12)
    rhos = []
    for lab in sorted(set(labels)):
        uu = u[labels == lab]
        rhos.append((uu[:, :, None] * uu[:, None, :]).mean(axis=0))
    rhos = np.stack(rhos)
    return von_neumann_entropy(rhos.mean(axis=0)) - float(
        np.mean([von_neumann_entropy(r) for r in rhos]))


def adjusted_rand_index(a, b):
    from sklearn.metrics import adjusted_rand_score
    return float(adjusted_rand_score(a, b))


# --------------------------------------------------------------- main

def main():
    t0 = time.time()
    outcome, occl = load_events(EVENTS)
    truth, rule_of, survivors = solve_objects(outcome, occl)
    feats = build_features(outcome, occl)
    leak = leak_check(outcome, occl, feats)

    model = VectorScout()
    n_params = param_count(model)
    assert n_params <= 60000, n_params
    losses = train(model, feats, outcome, occl)

    train_acc, train_beliefs, train_z, _ = causal_eval(
        model, feats, outcome, occl, truth, TRAIN_OBJS)
    test_acc, test_beliefs, test_z, test_yhat = causal_eval(
        model, feats, outcome, occl, truth, TEST_OBJS)

    # ray loss (metric only; training loss stays MSE per control-lane exemption)
    with torch.no_grad():
        def rl(beliefs, z):
            zhat = model.predict_next_embedding(beliefs[:, :-1].reshape(-1, LATENT))
            return ray_loss(zhat, z[:, 1:].reshape(-1, LATENT))
        ray_train = rl(train_beliefs, train_z)
        ray_test = rl(test_beliefs, test_z)

    # ---- Holevo belief persistence vs permutation null
    B = test_beliefs.reshape(-1, LATENT).numpy()
    labels = np.repeat(np.arange(len(TEST_OBJS)), N_VIEW)
    chi = holevo_chi(B, labels)
    rng = np.random.default_rng(SEED)
    null = np.array([holevo_chi(B, rng.permutation(labels)) for _ in range(200)])
    q95 = float(np.quantile(null, 0.95))
    holevo = {"chi_bits": chi, "null_mean": float(null.mean()),
              "null_q95": q95, "above_null": bool(chi > q95),
              "margin_bits": chi - q95, "n_permutations": 200,
              "measurement": "unit-normalized belief vectors -> rho_o = mean_v u u^T "
                             "per test object; chi = S(mean rho) - mean S(rho_o), log2; "
                             "null = object labels permuted over the 96 test latents"}

    # ---- latent-cluster ARI vs object ids + shuffled null
    from sklearn.cluster import KMeans
    km = KMeans(n_clusters=len(TEST_OBJS), n_init=10, random_state=SEED).fit(B)
    ari = adjusted_rand_index(labels, km.labels_)
    ari_null = np.array([adjusted_rand_index(rng.permutation(labels), km.labels_)
                         for _ in range(200)])
    ari_block = {"ari": ari, "shuffled_null_mean": float(ari_null.mean()),
                 "shuffled_null_q95": float(np.quantile(ari_null, 0.95)),
                 "above_null": bool(ari > float(np.quantile(ari_null, 0.95))),
                 "measurement": "KMeans k=16 on 96 test beliefs; ARI vs object ids; "
                                "null = 200 object-id shuffles against same clustering"}

    probes = {}

    # P1 — 2pi vs 4pi sign/lift memory
    probes["P1_sign_lift"] = {
        "score": None, "status": "not_applicable_for_this_carrier",
        "reason": "real tanh vector latent charges no phase, no sign double cover, "
                  "no connection; card sign law requires coherent paths + connection "
                  "+ interference/holonomy witness, none of which exist on this "
                  "carrier — recorded as a scored fact of the control lane"}

    # P2 — chirality / sector-changing: probe rule chirality (rule2 vs rule3 mirror pair)
    def linear_probe(train_X, train_y, test_X, test_y):
        X = np.hstack([train_X, np.ones((len(train_X), 1))])
        w, *_ = np.linalg.lstsq(X, train_y * 2.0 - 1.0, rcond=None)
        pred = (np.hstack([test_X, np.ones((len(test_X), 1))]) @ w) > 0
        accs = [float((pred[test_y == c] == bool(c)).mean()) for c in (0, 1)
                if (test_y == c).any()]
        return float(np.mean(accs)), pred

    tr_mask = np.isin(rule_of[TRAIN_OBJS], CHIRAL_RULES)
    te_mask = np.isin(rule_of[TEST_OBJS], CHIRAL_RULES)
    b5_train = train_beliefs[:, -1].numpy()
    b5_test = test_beliefs[:, -1].numpy()
    tr_y = (rule_of[TRAIN_OBJS][tr_mask] == CHIRAL_RULES[1]).astype(float)
    te_y = (rule_of[TEST_OBJS][te_mask] == CHIRAL_RULES[1]).astype(float)
    if tr_mask.sum() >= 4 and len(set(te_y)) == 2:
        p2_score, _ = linear_probe(b5_train[tr_mask], tr_y, b5_test[te_mask], te_y)
        p2_note = (f"linear least-squares probe on final beliefs; train n={int(tr_mask.sum())}, "
                   f"test n={int(te_mask.sum())} objects with mirror-pair rules "
                   f"{CHIRAL_RULES}; balanced accuracy")
    else:
        p2_score, p2_note = 0.0, "insufficient mirror-pair objects in split; scored 0"
    probes["P2_chirality"] = {"score": round(p2_score, 4), "measurement": p2_note,
                              "rule_counts_train": np.bincount(rule_of[TRAIN_OBJS], minlength=4).tolist(),
                              "rule_counts_test": np.bincount(rule_of[TEST_OBJS], minlength=4).tolist()}

    # P3 — ab vs ba order witness: swap views 2 and 3 in the feeding order
    perm = [0, 1, 3, 2, 4, 5]
    with torch.no_grad():
        b_sw, _ = model.roll(feats[TEST_OBJS][:, perm])
    d_order = float((1.0 - cos2(test_beliefs[:, -1], b_sw[:, -1])).mean())
    with torch.no_grad():
        yh = model.decode(b_sw.reshape(-1, LATENT)).reshape(len(TEST_OBJS), N_VIEW, N_POS)
    # swapped-order predictions land at swapped slots; score decoded belief vs slot truth
    pred_sw = (yh.numpy() > 0).astype(np.int64)
    truth_sw = truth[TEST_OBJS][:, perm]
    occ_sw = occl[TEST_OBJS][:, perm]
    acc_sw = float((pred_sw[occ_sw] == truth_sw[occ_sw]).mean())
    probes["P3_order_witness"] = {
        "score": round(min(1.0, d_order), 4),
        "measurement": "mean (1 - cos^2) between final beliefs for view order "
                       "(...,2,3,...) vs (...,3,2,...); inputs keep their own view "
                       "one-hots so only feeding order differs",
        "occluded_acc_true_order": round(test_acc, 4),
        "occluded_acc_swapped_order": round(acc_sw, 4)}

    # P4 — (ab)c vs a(bc) bracket witness
    with torch.no_grad():
        b = test_beliefs.reshape(-1, LATENT)
        t1 = model.predict_next_embedding(
            model.predict_next_embedding(model.predict_next_embedding(b)))
        f2 = lambda x: model.predict_next_embedding(model.predict_next_embedding(x))
        t2 = f2(model.predict_next_embedding(b))
    dev = float((t1 - t2).abs().max())
    probes["P4_bracket_witness"] = {
        "score": round(min(1.0, dev), 6),
        "measurement": "max |((T.T).T)b - (T.(T.T))b| over 96 test beliefs; the "
                       "carrier charges no bracket — composition is function "
                       "composition, associative by construction",
        "max_deviation": dev}

    # P5 — hidden-mode belief under occlusion (PRIMARY) = occluded-bit accuracy
    probes["P5_occluded_belief"] = {
        "score": round(test_acc, 4),
        "measurement": "causal belief over views 0..v; sign(decode) at withheld "
                       "cells of test objects vs CA-solved ground truth; chance ~0.5",
        "n_occluded_test_bits": int(occl[TEST_OBJS].sum())}

    # P6 — counterfactual action binding (PRIMARY)
    wins = ties = tot = 0
    with torch.no_grad():
        for oi, o in enumerate(TEST_OBJS):
            for v in range(N_VIEW - 1):
                b_v = test_beliefs[oi, v]
                z_pred = model.predict_next_embedding(b_v)
                b_adv = model.belief_step(b_v.unsqueeze(0), z_pred.unsqueeze(0))[0]
                vis = ~occl[o, v + 1]
                tgt = truth[o, v + 1][vis]
                p_act = (model.decode(b_adv).numpy() > 0).astype(np.int64)[vis]
                p_stat = (model.decode(b_v).numpy() > 0).astype(np.int64)[vis]
                a_act = (p_act == tgt).mean()
                a_stat = (p_stat == tgt).mean()
                wins += a_act > a_stat
                ties += a_act == a_stat
                tot += 1
    probes["P6_counterfactual_binding"] = {
        "score": round((wins + 0.5 * ties) / tot, 4),
        "measurement": "for each test (obj, v<5): imagined action-advanced belief "
                       "(T then belief_step) vs static belief, both decoded against "
                       "view v+1 VISIBLE bits; score = win rate + 0.5*ties; 0.5 = "
                       "action adds nothing",
        "wins": int(wins), "ties": int(ties), "n": int(tot)}

    # P7 — prediction vs finite-budget reachability
    all_z = test_z  # (16, 6, 16)
    top1 = 0
    tot7 = 0
    vis_pat = np.where(occl[TEST_OBJS], -1, outcome[TEST_OBJS])  # (16,6,8)
    with torch.no_grad():
        for oi in range(len(TEST_OBJS)):
            for v in range(N_VIEW - 1):
                zhat = model.predict_next_embedding(test_beliefs[oi, v])
                tgt_pat = vis_pat[oi, v + 1]
                sims = []
                for oj in range(len(TEST_OBJS)):
                    if oj == oi:
                        continue
                    for vj in range(N_VIEW):
                        both = (tgt_pat >= 0) & (vis_pat[oj, vj] >= 0)
                        s = (tgt_pat[both] == vis_pat[oj, vj][both]).mean() if both.any() else 0.0
                        sims.append((s, oj, vj))
                sims.sort(reverse=True)
                decoys = [all_z[oj, vj] for _, oj, vj in sims[:5]]
                cands = torch.stack([all_z[oi, v + 1]] + decoys)
                d = 1.0 - cos2(zhat.unsqueeze(0), cands)
                top1 += int(torch.argmin(d)) == 0
                tot7 += 1
    probes["P7_reachability"] = {
        "score": round(top1 / tot7, 4),
        "measurement": "predicted next embedding vs {true successor + 5 maximally "
                       "visible-pattern-similar decoy views of OTHER objects}; "
                       "top-1 by ray distance; chance ~0.167 — similarity-only "
                       "carriers get fooled by lookalike unreachable views",
        "n": int(tot7)}

    # P8 — cross-view object persistence (retrieval)
    U = torch.tensor(B / (np.linalg.norm(B, axis=1, keepdims=True) + 1e-12))
    S = (U @ U.T).abs()
    S.fill_diagonal_(-1.0)
    nn_idx = S.argmax(dim=1).numpy()
    hits = float((labels[nn_idx] == labels).mean())
    probes["P8_cross_view_persistence"] = {
        "score": round(hits, 4),
        "measurement": "nearest-neighbour (|cos|) among the 96 test beliefs, self "
                       "excluded; hit = same object; chance = 5/95 ~ 0.053"}

    # P9 — shock / contraction / recovery
    shocked = feats[TEST_OBJS].clone()
    for oi, o in enumerate(TEST_OBJS):
        for p in range(N_POS):
            if not occl[o, 2, p]:
                trip = shocked[oi, 2, 3 * p:3 * p + 3].clone()
                shocked[oi, 2, 3 * p + 0], shocked[oi, 2, 3 * p + 1] = trip[1], trip[0]
    with torch.no_grad():
        b_shock, _ = model.roll(shocked)
    d = (1.0 - cos2(b_shock, test_beliefs)).numpy()  # (16, 6)
    rec = []
    for oi in range(len(TEST_OBJS)):
        if d[oi, 2] > 1e-9:
            rec.append(max(0.0, (d[oi, 2] - d[oi, 5]) / d[oi, 2]))
    probes["P9_shock_recovery"] = {
        "score": round(float(np.mean(rec)), 4) if rec else 0.0,
        "measurement": "flip all visible bits of view 2 (shock); divergence "
                       "d_v = 1-cos^2 vs clean belief; recovery = (d_2-d_5)/d_2 "
                       "clipped to [0,1], mean over test objects",
        "mean_d_shock": float(np.mean(d[:, 2])), "mean_d_final": float(np.mean(d[:, 5])),
        "n_objects_with_divergence": len(rec)}

    # P10 — gauge/basis invariance (cyclic position translation, a world symmetry)
    agree = []
    with torch.no_grad():
        base_sign = (model.decode(test_beliefs.reshape(-1, LATENT))
                     .reshape(len(TEST_OBJS), N_VIEW, N_POS).numpy() > 0)
        for k in range(1, N_POS):
            rot = feats[TEST_OBJS].clone()
            blocks = rot[:, :, :N_POS * 3].reshape(len(TEST_OBJS), N_VIEW, N_POS, 3)
            blocks = torch.roll(blocks, shifts=k, dims=2)
            rot[:, :, :N_POS * 3] = blocks.reshape(len(TEST_OBJS), N_VIEW, N_POS * 3)
            b_rot, _ = model.roll(rot)
            s_rot = (model.decode(b_rot.reshape(-1, LATENT))
                     .reshape(len(TEST_OBJS), N_VIEW, N_POS).numpy() > 0)
            agree.append((s_rot == np.roll(base_sign, k, axis=2)).mean())
    probes["P10_gauge_invariance"] = {
        "score": round(float(np.mean(agree)), 4),
        "measurement": "cyclic position rotation is an exact symmetry of the "
                       "periodic additive CA; score = mean sign-prediction "
                       "equivariance over k=1..7 rotations, test objects, all "
                       "views/positions; the carrier charges no equivariance",
        "per_k": [round(float(a), 4) for a in agree]}

    # ------------------------------------------------------------- controls
    # shuffled-object-id control: training is self-supervised (no id labels),
    # so the shuffle control binds at scoring: ARI/Holevo vs shuffled ids above.
    controls = {
        "leak_check_occluded_bits_never_in_features": leak,
        "shuffled_object_ids": {
            "note": "training uses no object-id labels; shuffle control applied "
                    "at scoring",
            "ari_vs_shuffled_ids_mean": ari_block["shuffled_null_mean"],
            "holevo_null_mean_bits": holevo["null_mean"]},
        "ca_solve_unique_survivors": {
            "pass": bool((survivors == 1).all()),
            "survivor_counts_min_max": [int(survivors.min()), int(survivors.max())],
            "note": "scoring-only ground truth; matches world_source "
                    "joint_identifiability (64/64 exact)"},
    }

    budgets = {
        "latent_real_dof": LATENT,
        "latent_dof_exact_16": LATENT == 16,
        "param_count": n_params, "param_budget": 60000,
        "train_steps": MAX_STEPS, "batch": BATCH,
        "split": {"seed": SEED, "train_objects": [0, 47], "test_objects": [48, 63]},
        "dtype": "float64", "device": "cpu",
    }

    charges = [
        "field: R (real vector latent, 16 DOF belief state)",
        "signature: none",
        "quadratic_form/pairing: Euclidean inner product (readout + ray-metric "
        "scoring only, not a charged geometric structure of the carrier)",
        "clifford_relation: none", "orientation: none", "grading: none",
        "connection: none", "factorization: none", "bracket: none",
        "nonlinearity: tanh (scout semantics)",
        "loss: coordinate MSE — historical-control exemption, card lane 1 only",
        f"parameters: {n_params} of 60000 budget",
    ]

    checks_pass = bool(leak["pass"] and controls["ca_solve_unique_survivors"]["pass"]
                       and n_params <= 60000 and LATENT == 16)

    findings = [
        f"occluded-bit test accuracy {test_acc:.4f} (train {train_acc:.4f}, chance ~0.5) "
        f"over {int(occl[np.array(TEST_OBJS)].sum())} withheld test bits",
        f"belief persistence: Holevo chi {chi:.4f} bits vs permutation-null q95 "
        f"{q95:.4f} -> above_null={holevo['above_null']}, margin {chi - q95:+.4f} bits",
        f"latent clusters: ARI {ari:.4f} vs shuffled-null mean "
        f"{ari_block['shuffled_null_mean']:.4f}",
        f"ray-loss (metric only, MSE-trained control): train {ray_train:.4f} / "
        f"test {ray_test:.4f}",
        "P1 not_applicable_for_this_carrier (no phase/connection charged); "
        "P4 deviation exactly 0 (no bracket charged, associative by construction)",
        "control lane: vector scout sets the floor the geometric carriers must beat "
        "under identical budgets; promotion_allowed false",
    ]

    receipt = {
        "lane": "lane1_vector_scout",
        "sim_id": "spinor_jepa_tournament_lane1_vector_scout_v0",
        "classification": "tournament_control_lane_receipt",
        "promotion_allowed": False,
        "card_authority": "system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md (AMENDMENT v0.1, "
                          "occluded-object perception)",
        "carrier": "six-dim vector scout semantics ported to matched 16-DOF budget: "
                   "tanh latent, linear layers, MSE (historical control, this lane only)",
        "data": str(EVENTS),
        "seed": SEED,
        "memory_gate": MEM_GATE,
        "budgets": budgets,
        "charges": charges,
        "metrics": {
            "occluded_bit_accuracy_test": round(test_acc, 4),
            "occluded_bit_accuracy_train": round(train_acc, 4),
            "belief_persistence_holevo": holevo,
            "ray_loss_train": round(ray_train, 4),
            "ray_loss_test": round(ray_test, 4),
            "latent_cluster_ari": ari_block,
            "final_train_loss_mse_plus_jepa": round(losses[-1], 6),
            "first_train_loss": round(losses[0], 6),
        },
        "probes": probes,
        "controls": controls,
        "all_pass": checks_pass,
        "findings": findings,
        "runtime_s": round(time.time() - t0, 2),
    }
    OUT.write_text(json.dumps(receipt, indent=2))
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
