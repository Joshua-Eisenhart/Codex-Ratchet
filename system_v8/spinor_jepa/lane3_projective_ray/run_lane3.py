"""lane3_projective_ray -- complex projective ray carrier, occluded-object
perception per TOURNAMENT_CARD_v0.md AMENDMENT v0.1 (frozen; not edited).

Carrier (card Object section, instantiated for the CP class):
  state   psi in C^8, ||psi|| = 1, physical state = ray (U(1) gauge class)
  update  psi_v = Retr( M(obs_v) R psi_{v-1} )   -- ORDER RETAINED
          R      = learned complex 8x8 action transport (one world step)
          M(obs) = observation-conditioned complex 8x8 instrument update
          Retr   = normalization to the unit sphere of C^8
  loss    L_ray = 1 - |<psi*, psihat>|^2  (never coordinate MSE)
  readout derived bilinear rho = psi psi^dagger only (gauge-invariant);
          vectors/densities DERIVED, never primitive.

Budgets (charged): 16 real latent DOF (C^8), <=60k params, <=300 steps,
batch 32, torch CPU float64, split seed 20260719 objects 0-47/48-63.

Leak rule: occluded outcomes are withheld in the data; model features at
occluded positions are exactly (0,0). Oracle-reconstructed truth (from
visible bits only, data_oracle.py) is used EXCLUSIVELY as eval labels.
"""
import json
import math
import os
import sys
import time

import numpy as np

LANE = "/Users/joshuaeisenhart/Codex-Ratchet/system_v8/spinor_jepa/lane3_projective_ray"
SEED = 20260719
N_BITS, N_OBJ, N_VIEWS = 8, 64, 6
TRAIN_OBJS = list(range(0, 48))
TEST_OBJS = list(range(48, 64))
MAX_PARAMS = 60000
N_STEPS = 300
BATCH = 32


# ---------------------------------------------------------------- memory gate
def memory_gate(threshold=0.25,
                timeout_s=int(os.environ.get("LANE3_GATE_TIMEOUT_S", "900")),
                poll_s=20):
    import psutil
    t0 = time.time()
    while True:
        frac = psutil.virtual_memory().available / psutil.virtual_memory().total
        if frac > threshold:
            print(f"[memory_gate] PASS free_frac={frac:.3f} > {threshold}")
            return True, frac
        if time.time() - t0 > timeout_s:
            print(f"[memory_gate] FAIL free_frac={frac:.3f} <= {threshold} "
                  f"after {timeout_s}s")
            return False, frac
        print(f"[memory_gate] waiting: free_frac={frac:.3f} <= {threshold}")
        time.sleep(poll_s)


GATE_OK, GATE_FRAC = memory_gate()
if not GATE_OK:
    json.dump({"aborted": "memory_gate_failed", "free_frac": GATE_FRAC},
              open(os.path.join(LANE, "results", "receipt.json"), "w"), indent=2)
    sys.exit(2)

import torch  # noqa: E402  (imported only after the memory gate)

torch.set_default_dtype(torch.float64)
torch.manual_seed(SEED)
np.random.seed(SEED)
rng = np.random.default_rng(SEED)

# ---------------------------------------------------------------- data
d = np.load(os.path.join(LANE, "results", "oracle_truth.npz"))
outcome = d["outcome"]        # {0,1,-1 withheld}  (model-visible table)
occluded = d["occluded"]      # bool
oracle_truth = d["truth"]     # full bits -- EVAL LABELS ONLY
oracle_rules = d["rules"]     # per-object rule id -- P2 EVAL LABELS ONLY

# features: per position (value in {-1,+1,0}, vis in {0,1}) -> 16 dims/view
def make_feats(out_tab):
    val = np.where(out_tab == -1, 0.0, out_tab * 2.0 - 1.0)
    vis = (out_tab != -1).astype(np.float64)
    return np.concatenate([val, vis], axis=-1)  # (..., 16)

FEATS = make_feats(outcome)                     # (64, 6, 16)

# LEAK CHECK (structural): occluded slots carry exactly (0,0)
leak_val = np.abs(FEATS[..., :N_BITS][occluded]).max() if occluded.any() else 0.0
leak_vis = np.abs(FEATS[..., N_BITS:][occluded]).max() if occluded.any() else 0.0
LEAK_CHECK_PASS = bool(leak_val == 0.0 and leak_vis == 0.0)
print(f"[leak_check] occluded feature slots all zero: {LEAK_CHECK_PASS} "
      f"(max val {leak_val}, max vis {leak_vis}); oracle arrays touched only "
      f"in eval blocks below")

FEATS_T = torch.tensor(FEATS)
VIS_T = torch.tensor((outcome != -1).astype(np.float64))
BITS_T = torch.tensor(np.where(outcome == -1, 0, outcome).astype(np.float64))


# ---------------------------------------------------------------- model
class Encoder(torch.nn.Module):
    def __init__(self, h=96):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(16, h), torch.nn.SiLU(),
            torch.nn.Linear(h, h), torch.nn.SiLU(),
            torch.nn.Linear(h, 16))

    def forward(self, f):                      # (..., 16) -> C^8 ray
        r = self.net(f)
        z = torch.complex(r[..., :8], r[..., 8:])
        return z / torch.linalg.vector_norm(z, dim=-1, keepdim=True).clamp_min(1e-12)


class Carrier(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.enc = Encoder()
        self.A = torch.nn.Parameter(torch.randn(8, 8, dtype=torch.complex128) * 0.2
                                    + torch.eye(8, dtype=torch.complex128))
        self.Wm = torch.nn.Linear(16, 128)     # instrument update generator
        self.probe = torch.nn.Sequential(
            torch.nn.Linear(64, 48), torch.nn.SiLU(), torch.nn.Linear(48, 8))

    def instrument(self, f):                   # M(obs) = I + reshape(Wm f)
        m = self.Wm(f)
        M = torch.complex(m[..., :64], m[..., 64:]).reshape(*f.shape[:-1], 8, 8)
        return torch.eye(8, dtype=torch.complex128) + M

    @staticmethod
    def retr(z):
        return z / torch.linalg.vector_norm(z, dim=-1, keepdim=True).clamp_min(1e-12)

    def rho_feats(self, z):                    # gauge-invariant readout feats
        rho = z.unsqueeze(-1) * z.conj().unsqueeze(-2)          # psi psi^dag
        iu, ju = torch.triu_indices(8, 8, offset=1)
        di = torch.arange(8)
        return torch.cat([rho.real[..., di, di],
                          rho[..., iu, ju].real, rho[..., iu, ju].imag], dim=-1)

    def probe_logits(self, z):
        return self.probe(self.rho_feats(z))

    def filter(self, feats_seq, transport=None, order="MA"):
        """feats_seq: (B, V, 16). Returns beliefs (B, V, 8) and priors."""
        A = self.A if transport is None else transport
        psi = self.enc(feats_seq[:, 0])
        beliefs, priors = [psi], [psi]
        for v in range(1, feats_seq.shape[1]):
            prior = self.retr(psi @ A.T)
            M = self.instrument(feats_seq[:, v])
            if order == "MA":                  # psi -> Retr(M (A psi))
                psi = self.retr((M @ prior.unsqueeze(-1)).squeeze(-1))
            else:                              # swapped: Retr(A (M psi))
                mpsi = (M @ psi.unsqueeze(-1)).squeeze(-1)
                psi = self.retr(mpsi @ A.T)
            beliefs.append(psi)
            priors.append(prior)
        return torch.stack(beliefs, 1), torch.stack(priors, 1)


model = Carrier()
N_PARAMS = sum(p.numel() * (2 if p.is_complex() else 1) for p in model.parameters())
print(f"[budget] params (real count) = {N_PARAMS} (limit {MAX_PARAMS})")
assert N_PARAMS <= MAX_PARAMS

bce = torch.nn.BCEWithLogitsLoss(reduction="none")


def masked_bce(logits, targets, mask):
    per = bce(logits, targets) * mask
    return per.sum() / mask.sum().clamp_min(1.0)


def ray_loss(z, zt):
    return 1.0 - (z.conj() * zt).sum(-1).abs() ** 2


def run_losses(objs, drop_p=0.25, train_rng=None):
    f = FEATS_T[objs].clone()
    vis = VIS_T[objs].clone()
    bits = BITS_T[objs]
    if drop_p > 0:
        dropm = (torch.rand(vis.shape, generator=train_rng) < drop_p) & (vis > 0)
        f[..., :8] = f[..., :8] * (~dropm)
        f[..., 8:] = f[..., 8:] * (~dropm)
    beliefs, priors = model.filter(f)
    logit_b = model.probe_logits(beliefs)
    logit_p = model.probe_logits(priors[:, 1:])
    L_probe = masked_bce(logit_b, bits, vis)               # posterior readout
    L_pred = masked_bce(logit_p, bits[:, 1:], vis[:, 1:])  # prior prediction
    with torch.no_grad():
        z_tgt = model.enc(FEATS_T[objs])                   # stop-grad target
    L_jepa = ray_loss(priors[:, 1:], z_tgt[:, 1:]).mean()
    return L_probe, L_pred, L_jepa


def train(model_, objs_pool, tag):
    opt = torch.optim.Adam(model_.parameters(), lr=5e-3)
    g = torch.Generator().manual_seed(SEED)
    hist = []
    for step in range(N_STEPS):
        objs = torch.tensor(rng.choice(objs_pool, size=BATCH, replace=True))
        Lp, Lq, Lj = run_losses(objs, drop_p=0.25, train_rng=g)
        loss = Lp + Lq + Lj
        opt.zero_grad(); loss.backward(); opt.step()
        if step % 50 == 0 or step == N_STEPS - 1:
            hist.append((step, float(Lp), float(Lq), float(Lj)))
            print(f"[{tag}] step {step:3d} L_probe {Lp:.4f} L_pred {Lq:.4f} "
                  f"L_jepa {Lj:.4f}")
    return hist


t0 = time.time()
hist = train(model, np.array(TRAIN_OBJS), "train")
print(f"[train] done in {time.time()-t0:.1f}s, steps={N_STEPS}, batch={BATCH}")


# ---------------------------------------------------------------- evaluation
@torch.no_grad()
def eval_beliefs(objs):
    f = FEATS_T[objs]
    beliefs, priors = model.filter(f)
    return beliefs, priors


@torch.no_grad()
def occluded_accuracy(objs, beliefs, priors):
    """EVAL ONLY: labels come from oracle_truth (visible-bit reconstruction)."""
    objs_np = np.asarray(objs)
    occ = torch.tensor(occluded[objs_np])
    truth = torch.tensor(oracle_truth[objs_np].astype(np.float64))
    post = (model.probe_logits(beliefs) > 0).double()
    acc_post = ((post == truth) * occ).sum() / occ.sum()
    prior_pred = (model.probe_logits(priors[:, 1:]) > 0).double()
    occ_p, truth_p = occ[:, 1:], truth[:, 1:]
    acc_prior = ((prior_pred == truth_p) * occ_p).sum() / occ_p.sum()
    return float(acc_post), float(acc_prior)


@torch.no_grad()
def mean_ray_loss(objs):
    _, priors = eval_beliefs(objs)
    z_tgt = model.enc(FEATS_T[objs])
    return float(ray_loss(priors[:, 1:], z_tgt[:, 1:]).mean())


tr = torch.tensor(TRAIN_OBJS); te = torch.tensor(TEST_OBJS)
bel_tr, pri_tr = eval_beliefs(tr)
bel_te, pri_te = eval_beliefs(te)
acc_post_te, acc_prior_te = occluded_accuracy(te, bel_te, pri_te)
acc_post_tr, acc_prior_tr = occluded_accuracy(tr, bel_tr, pri_tr)
rayloss_tr, rayloss_te = mean_ray_loss(tr), mean_ray_loss(te)
n_occ_te = int(occluded[TEST_OBJS].sum())
print(f"[eval] occluded-bit acc TEST posterior {acc_post_te:.4f} "
      f"prior {acc_prior_te:.4f} (n={n_occ_te}); TRAIN posterior {acc_post_tr:.4f}")
print(f"[eval] ray-loss train {rayloss_tr:.4f} test {rayloss_te:.4f}")

# chance baseline from train visible bit rate
p1 = float((BITS_T[tr] * VIS_T[tr]).sum() / VIS_T[tr].sum())
chance = max(p1, 1 - p1)
print(f"[eval] majority-chance baseline {chance:.4f}")


# Holevo belief persistence (test objects), permutation null
def vn_entropy(rho):
    ev = np.clip(np.linalg.eigvalsh(rho), 0, None)
    ev = ev / max(ev.sum(), 1e-15)
    ev = ev[ev > 1e-15]
    return float(-(ev * np.log2(ev)).sum())


Z = bel_te.numpy()                              # (16, 6, 8) complex
rho_all = np.einsum("ovi,ovj->ovij", Z, Z.conj())


def holevo(groups):                             # groups: (16, 6, 8, 8)
    rho_i = groups.mean(axis=1)
    rho_bar = rho_i.mean(axis=0)
    return vn_entropy(rho_bar) - float(np.mean([vn_entropy(r) for r in rho_i]))


chi = holevo(rho_all)
flat = rho_all.reshape(-1, 8, 8)
null = []
for _ in range(200):
    perm = rng.permutation(flat.shape[0])
    null.append(holevo(flat[perm].reshape(16, 6, 8, 8)))
null = np.array(null)
chi_p95 = float(np.quantile(null, 0.95))
holevo_pass = bool(chi > chi_p95)
holevo_margin = float(chi - chi_p95)
print(f"[eval] Holevo chi {chi:.4f} vs null p95 {chi_p95:.4f} "
      f"pass={holevo_pass} margin={holevo_margin:.4f}")

# latent-cluster ARI vs object ids (test), + shuffled-label null
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score

feats_cluster = model.rho_feats(bel_te).numpy().reshape(-1, 64)
labels = np.repeat(np.arange(16), N_VIEWS)
km = KMeans(n_clusters=16, n_init=10, random_state=SEED).fit(feats_cluster)
ari = float(adjusted_rand_score(labels, km.labels_))
ari_null = np.array([adjusted_rand_score(rng.permutation(labels), km.labels_)
                     for _ in range(200)])
print(f"[eval] ARI {ari:.4f} vs shuffled-null mean {ari_null.mean():.4f} "
      f"p95 {np.quantile(ari_null, 0.95):.4f}")


# ---------------------------------------------------------------- probes
probes = {}

# P1: 2pi vs 4pi sign/lift memory
with torch.no_grad():
    z = bel_te.reshape(-1, 8)
    fid_sign = float((1.0 - ray_loss(z, -z)).mean())
probes["P1_sign_lift_memory"] = {
    "score": 0.0, "na": True,
    "reason": ("CP^7 ray carrier gauges out the global phase by construction "
               "(ray loss + rho readout): computed fidelity(psi, -psi) = "
               f"{fid_sign:.12f} = 1, so psi -> -psi is unobservable; no spin "
               "structure or holonomy witness is charged, and the view axis "
               "0..5 has no loops to carry holonomy. Honest N/A."),
    "measurement": "1 - L_ray(psi, -psi) averaged over all test beliefs"}

# P2: chirality (mirror rules 2 vs 3) -- EVAL-ONLY oracle rule labels
with torch.no_grad():
    obj_feats = model.rho_feats(bel_tr).mean(dim=1).numpy()
    obj_feats_te = model.rho_feats(bel_te).mean(dim=1).numpy()
r_tr = oracle_rules[TRAIN_OBJS]; r_te = oracle_rules[TEST_OBJS]
m_tr = np.isin(r_tr, [2, 3]); m_te = np.isin(r_te, [2, 3])
if m_te.sum() >= 4 and len(set(r_te[m_te])) == 2:
    c2 = obj_feats[m_tr & (r_tr == 2)].mean(0)
    c3 = obj_feats[m_tr & (r_tr == 3)].mean(0)
    X, y = obj_feats_te[m_te], (r_te[m_te] == 3).astype(int)
    pred = (np.linalg.norm(X - c3, axis=1) < np.linalg.norm(X - c2, axis=1)).astype(int)
    accs = [np.mean(pred[y == k] == k) for k in (0, 1)]
    p2 = float(np.mean(accs))
    p2_note = (f"nearest-centroid on mean rho feats, train centroids, test "
               f"objs rule2={int((y==0).sum())} rule3={int((y==1).sum())}, "
               f"balanced acc")
else:
    p2, p2_note = 0.5, "insufficient mirror-rule members in test; not scored"
probes["P2_chirality_sector"] = {"score": p2, "na": False, "measurement": p2_note}

# P3: ab vs ba order witness (M vs A do not commute in general)
with torch.no_grad():
    A = model.A.detach()
    f_te = FEATS_T[te][:, 1:].reshape(-1, 16)
    M = model.instrument(f_te)
    comm = M @ A - A @ M
    denom = (torch.linalg.matrix_norm(M) * torch.linalg.matrix_norm(A)).clamp_min(1e-12)
    p3_struct = float((torch.linalg.matrix_norm(comm) / denom).mean())
    # behavioural: swapped-order filter changes posterior probe probabilities
    bel_ma, _ = model.filter(FEATS_T[te], order="MA")
    bel_am, _ = model.filter(FEATS_T[te], order="AM")
    pr_ma = torch.sigmoid(model.probe_logits(bel_ma))
    pr_am = torch.sigmoid(model.probe_logits(bel_am))
    p3_behav = float((pr_ma - pr_am).abs().mean())
probes["P3_order_witness"] = {
    "score": float(min(1.0, p3_struct)), "na": False,
    "measurement": (f"normalized commutator ||MA-AM||_F/(||M|| ||A||) mean "
                    f"{p3_struct:.4f} over test instrument updates; behavioural "
                    f"mean |dp| of posterior probe probs under swapped update "
                    f"order = {p3_behav:.4f}. Order is retained and measurable.")}

# P4: (ab)c vs a(bc) bracket witness
with torch.no_grad():
    Ms = M[:8]
    lhs = (Ms @ A) @ Ms.transpose(-1, -2)
    rhs = Ms @ (A @ Ms.transpose(-1, -2))
    p4_def = float((torch.linalg.matrix_norm(lhs - rhs)
                    / torch.linalg.matrix_norm(lhs).clamp_min(1e-12)).max())
probes["P4_bracket_witness"] = {
    "score": float(min(1.0, p4_def)), "na": False,
    "measurement": (f"max normalized associator defect ||(MA)N - M(AN)||/||.|| "
                    f"= {p4_def:.3e}: composition is associative to float "
                    f"precision; no bracket/nonassociative structure charged "
                    f"in this carrier (genuine negative, not N/A).")}

# P5: hidden-mode belief under occlusion (PRIMARY) = posterior occluded acc
probes["P5_occlusion_belief"] = {
    "score": acc_post_te, "na": False,
    "measurement": (f"posterior occluded-bit accuracy on test objects "
                    f"(n={n_occ_te} withheld bits, labels = oracle visible-bit "
                    f"reconstruction); prior-only acc {acc_prior_te:.4f}; "
                    f"majority chance {chance:.4f}")}

# P6: counterfactual action binding (PRIMARY): wrong transport degrades
with torch.no_grad():
    eyeA = torch.eye(8, dtype=torch.complex128)
    belI, priI = model.filter(FEATS_T[te], transport=eyeA)
    belA2, priA2 = model.filter(FEATS_T[te], transport=A @ A)
    accI, _ = occluded_accuracy(te, belI, priI)
    accA2, _ = occluded_accuracy(te, belA2, priA2)
acc_wrong = max(accI, accA2)
p6 = float(np.clip(2.0 * (acc_post_te - acc_wrong), 0.0, 1.0))
probes["P6_counterfactual_action"] = {
    "score": p6, "na": False,
    "measurement": (f"occluded acc with learned transport {acc_post_te:.4f} vs "
                    f"identity transport {accI:.4f} vs A^2 {accA2:.4f}; score = "
                    f"clip(2*(correct - best_wrong), 0, 1)")}

# P7: prediction similarity vs finite-budget reachability
from scipy.stats import spearmanr
with torch.no_grad():
    z_enc = model.enc(FEATS_T[te])
    dists, budgets = [], []
    for v in range(N_VIEWS):
        for w in range(v + 1, N_VIEWS):
            dd = ray_loss(z_enc[:, v], z_enc[:, w])
            dists.append(dd.numpy()); budgets.append(np.full(len(te), w - v))
rs, _ = spearmanr(np.concatenate(dists), np.concatenate(budgets))
probes["P7_similarity_vs_reachability"] = {
    "score": float((rs + 1) / 2), "na": False,
    "measurement": (f"Spearman rank corr between encoder ray distance and "
                    f"transport step budget dv over test view pairs = {rs:.4f} "
                    f"(score=(r+1)/2). Low corr = similarity is NOT "
                    f"attainability for this carrier (RC-aux lesson).")}

# P8: cross-view object persistence (AUC, transported fidelity)
with torch.no_grad():
    fids, same = [], []
    for v in range(N_VIEWS - 1):
        for w in range(v + 1, N_VIEWS):
            zsrc = z_enc[:, v]
            for _ in range(w - v):
                zsrc = model.retr(zsrc @ A.T)
            ztgt = z_enc[:, w]
            F = (zsrc.conj() @ ztgt.T).abs() ** 2      # (16,16) pairwise
            fids.append(F.numpy()); same.append(np.eye(16, dtype=bool))
fids = np.concatenate([f.ravel() for f in fids])
same = np.concatenate([s.ravel() for s in same])
pos, neg = fids[same], fids[~same]
auc = float((pos[:, None] > neg[None, :]).mean()
            + 0.5 * (pos[:, None] == neg[None, :]).mean())
probes["P8_cross_view_persistence"] = {
    "score": auc, "na": False,
    "measurement": (f"AUC of transported ray fidelity |<A^dv z_v, z_w>|^2 "
                    f"separating same-object from different-object test pairs "
                    f"({same.sum()} pos / {(~same).sum()} neg)")}

# P9: contraction / attractor formation under pure transport
with torch.no_grad():
    zr = torch.randn(256, 8, dtype=torch.complex128)
    zr = model.retr(zr)
    for _ in range(64):
        zr = model.retr(zr @ A.T)
    evals, evecs = torch.linalg.eig(A)
    kmax = torch.argmax(evals.abs())
    vdom = model.retr(evecs[:, kmax])
    fid_dom = float(((zr.conj() @ vdom).abs() ** 2).mean())
    gap = float((torch.sort(evals.abs(), descending=True).values[1]
                 / evals.abs().max()).item())
probes["P9_contraction_attractor"] = {
    "score": fid_dom, "na": False,
    "measurement": (f"mean fidelity of 256 random rays to dominant eigenray of "
                    f"learned transport after 64 retracted steps = {fid_dom:.4f}; "
                    f"spectral ratio |l2/l1| = {gap:.4f}. Non-unitary linear "
                    f"transport + retraction admits a projective attractor "
                    f"(card: unitary-only rollout cannot).")}

# P10: gauge / basis invariance (U(1))
with torch.no_grad():
    devs = []
    base = torch.sigmoid(model.probe_logits(bel_te))
    for _ in range(20):
        th = torch.rand(bel_te.shape[:-1]) * 2 * math.pi
        zg = bel_te * torch.exp(1j * th).unsqueeze(-1)
        devs.append(float((torch.sigmoid(model.probe_logits(zg)) - base).abs().max()))
        devs.append(float(ray_loss(zg, bel_te).abs().max()))
p10_dev = max(abs(x) for x in devs)
probes["P10_gauge_invariance"] = {
    "score": float(1.0 - min(1.0, p10_dev)), "na": False,
    "measurement": (f"max deviation of probe probabilities and ray loss under "
                    f"20 random global U(1) phases on beliefs = {p10_dev:.3e}")}

for k, v in probes.items():
    print(f"[probe] {k}: score={v['score']:.4f} na={v['na']}")


# ------------------------------------------------- control: shuffled object ids
print("[control] retraining with shuffled object ids (views regrouped across "
      "objects; same budgets)")
perm_v = rng.permuted(np.tile(np.arange(48), (N_VIEWS, 1)).T, axis=0)
FEATS_SHUF = FEATS_T.clone(); VIS_SHUF = VIS_T.clone(); BITS_SHUF = BITS_T.clone()
for v in range(N_VIEWS):
    FEATS_SHUF[:48, v] = FEATS_T[perm_v[:, v], v]
    VIS_SHUF[:48, v] = VIS_T[perm_v[:, v], v]
    BITS_SHUF[:48, v] = BITS_T[perm_v[:, v], v]

_REAL = (FEATS_T, VIS_T, BITS_T)
FEATS_T, VIS_T, BITS_T = FEATS_SHUF, VIS_SHUF, BITS_SHUF
torch.manual_seed(SEED)
ctrl = Carrier()
model_main, model = model, ctrl
train(ctrl, np.array(TRAIN_OBJS), "ctrl-shuffled")
FEATS_T, VIS_T, BITS_T = _REAL          # evaluate control on REAL test data
with torch.no_grad():
    bel_c, pri_c = ctrl.filter(FEATS_T[te])
    acc_ctrl, acc_ctrl_prior = occluded_accuracy(te, bel_c, pri_c)
model = model_main
print(f"[control] shuffled-id model occluded acc TEST posterior {acc_ctrl:.4f} "
      f"prior {acc_ctrl_prior:.4f} (real model {acc_post_te:.4f})")


# ---------------------------------------------------------------- receipt
charges = [
    "field: complex numbers C; latent psi in C^8 = exactly 16 real DOF",
    "pairing: Hermitian inner product <z,w>=sum z_i* w_i; ray metric "
    "L_ray = 1-|<psi*,psihat>|^2 (never coordinate MSE)",
    "gauge: U(1) global-phase quotient (physical state = ray in CP^7); "
    "enforced by ray loss + rho-only readout, verified by P10",
    "connection/transport: ONE learned complex 8x8 action transport R=A "
    "(one world step), applied per view step; 128 real params",
    "instrument update: observation-conditioned complex 8x8 operator "
    "M(obs) = I + reshape(W_m f_obs); card's M_q; order retained (P3)",
    "retraction: normalization to unit sphere of C^8 after each update",
    "derived bilinear: rank-1 density rho = psi psi^dagger used for all "
    "readouts (derived, never primitive, per card Object section)",
    "target-update rule: stop-gradient target encoder, no EMA",
    "NOT charged: Clifford relation, grading, signature beyond "
    "positive-definite Hermitian form, bracket, factorization",
]

metrics = {
    "occluded_bit_accuracy_test_posterior": acc_post_te,
    "occluded_bit_accuracy_test_prior": acc_prior_te,
    "occluded_bit_accuracy_train_posterior": acc_post_tr,
    "n_occluded_bits_test": n_occ_te,
    "majority_chance_baseline": chance,
    "belief_persistence_holevo": {
        "above_permutation_null": holevo_pass, "chi_bits": chi,
        "null_p95": chi_p95, "margin": holevo_margin, "n_permutations": 200},
    "ray_loss_train": rayloss_tr, "ray_loss_test": rayloss_te,
    "latent_cluster_ari_test": {
        "ari": ari, "null_mean": float(ari_null.mean()),
        "null_p95": float(np.quantile(ari_null, 0.95)), "k": 16,
        "features": "vec(rho) gauge-invariant, per (object,view) belief"},
    "controls": {
        "shuffled_object_ids_occluded_acc_test": acc_ctrl,
        "shuffled_object_ids_occluded_acc_test_prior": acc_ctrl_prior,
        "leak_check_occluded_bits_never_in_features": LEAK_CHECK_PASS},
    "budget": {
        "latent_real_dof": 16, "params_real_count": N_PARAMS,
        "param_limit": MAX_PARAMS, "train_steps": N_STEPS, "batch": BATCH,
        "dtype": "float64/complex128", "device": "cpu",
        "split_seed": SEED, "train_objects": "0-47", "test_objects": "48-63",
        "memory_gate_free_frac": GATE_FRAC},
}

budget_ok = (N_PARAMS <= MAX_PARAMS and N_STEPS <= 300)
probes_ok = all(("score" in p) and (not p["na"] or p.get("reason"))
                for p in probes.values())
gauge_ok = probes["P10_gauge_invariance"]["score"] > 0.999
all_pass = bool(budget_ok and probes_ok and LEAK_CHECK_PASS and gauge_ok
                and GATE_OK)

findings = [
    f"Posterior occluded-bit accuracy on held-out objects {acc_post_te:.4f} "
    f"vs majority chance {chance:.4f} and shuffled-object-id control "
    f"{acc_ctrl:.4f} (labels: oracle reconstruction from visible bits only; "
    f"world is exactly identifiable, so 1.0 is the informational ceiling).",
    "Structural limit of this carrier (honest negative): ONE global linear "
    "transport A on C^8 cannot branch over the 4 hidden CA rules; rule "
    "identity is only inferable across views, so dynamics must be carried "
    "by the observation-conditioned instrument updates M(obs). Expect the "
    "gap to the 1.0 ceiling to be structural, not merely optimization.",
    f"Order witness P3 is real for this carrier ({probes['P3_order_witness']['score']:.3f} "
    "normalized commutator): M(obs) and A do not commute, matching the "
    "card's ORDER RETAINED requirement; bracket witness P4 is a genuine "
    "zero (associative composition).",
    "P1 (2pi/4pi lift) is not_applicable_for_this_carrier: the ray "
    "quotient erases the sign by construction; recorded as a scored fact.",
]

receipt = {
    "lane": "lane3_projective_ray",
    "sim_id": "spinor_jepa_tournament_v0_lane3",
    "card_authority": "system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md "
                      "(incl AMENDMENT v0.1, occluded-object perception)",
    "carrier": "complex projective ray (CP^7): psi in C^8, ||psi||=1, "
               "U(1) gauge class; update psi_v = Retr(M(obs_v) R psi_{v-1})",
    "classification": "tournament_lane_receipt",
    "promotion_allowed": False,
    "claim_ceiling": "working_sim; single-lane receipt; cross-lane verdicts "
                     "belong to the separate fresh-context scorer",
    "seed": SEED,
    "data": ("system_v8/loop2_world/results/world_source/"
             "events_dynamics_on.jsonl (64 objects x 6 views x 8 probes; "
             "occluded outcomes withheld at source)"),
    "eval_label_provenance": "occluded-bit labels reconstructed by exhaustive "
        "consistency over the 1024-element hidden space using VISIBLE bits "
        "only (data_oracle.py); unique for all 64 objects; eval-only, never "
        "a model feature",
    "all_pass": all_pass,
    "metrics": metrics,
    "charges": charges,
    "probes": probes,
    "training_history": hist,
    "findings": findings,
}
out = os.path.join(LANE, "results", "receipt.json")
json.dump(receipt, open(out, "w"), indent=2)
print(f"[receipt] written: {out}")
print(json.dumps({"lane": receipt["lane"], "all_pass": all_pass,
                  "occ_acc_test": acc_post_te, "holevo_pass": holevo_pass,
                  "ari": ari}, indent=2))
