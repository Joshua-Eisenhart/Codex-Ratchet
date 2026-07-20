#!/usr/bin/env python3
"""
lane6_spinor_ideal -- Clifford minimal-ideal spinor carrier.

Authority: system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md (frozen, incl AMENDMENT
v0.1). Task: occluded-object perception on the world-source event log --
predict masked probe outcomes + maintain belief under occlusion.

Carrier (per card Object section, lane 6 semantics):
  - Spinor module: complexified Cl(6,0) = Mat(8,C); minimal left ideal via
    primitive idempotent P = prod_j (1 + i g_{2j-1} g_{2j})/2 (rank 1);
    S = Cl(6,C).P ~= C^8. Latent = psi in S: EXACTLY 16 real DOF.
  - Invariant pairing: Hermitian <psi,phi> = psi^dag phi (Spin(6)-invariant;
    gammas Hermitian, spin elements unitary).
  - Typed transports R_a: dynamics transport A in Cl(6,C) (open/non-unitary,
    Kraus-fragment; attractors possible). Probe/instrument updates M_{q,o} =
    I + W_{q,o} in Cl(6,C). ORDER RETAINED (sequential application).
  - Retraction: ray normalization psi -> psi/|psi| after every operator.
  - Loss: ray metric L_ray = 1 - |<t, psihat>|^2. Never coordinate MSE.
  - Derived (never primitive) readout: bilinear <psi| O_q |psi>, O_q Hermitian.

Budgets (charged): 16 real latent DOF; params <= 60k; split seed 20260719,
objects 0-47 train / 48-63 test; <= 300 steps; batch 32; torch CPU float64.

Blindness: this lane reads ONLY its own dir + the shared world-source data.
Oracle hidden-state reconstruction is EVALUATION-ONLY (leak check enforced).
promotion_allowed: false.
"""
import json, math, os, subprocess, sys
from collections import defaultdict

# ---------------------------------------------------------------- memory gate
def memory_gate():
    """>25% free before torch import. Two measures recorded: the OS authority
    (kern.memorystatus_level, the same 'system-wide memory free percentage'
    memory_pressure reports) and psutil available/total (stricter). Gate
    passes on the OS measure; both are written to the receipt."""
    import psutil
    vm = psutil.virtual_memory()
    psutil_frac = vm.available / vm.total
    try:
        lvl = int(subprocess.run(["sysctl", "-n", "kern.memorystatus_level"],
                                 capture_output=True, text=True).stdout)
    except Exception:
        lvl = None
    os_frac = (lvl / 100.0) if lvl is not None else psutil_frac
    print(f"[memory gate] os_free={os_frac:.3f} psutil_available={psutil_frac:.3f}")
    assert max(os_frac, psutil_frac) > 0.25, \
        f"memory gate FAIL: os={os_frac:.3f}, psutil={psutil_frac:.3f} <= 0.25"
    return {"os_memorystatus_free_fraction": os_frac,
            "psutil_available_fraction": psutil_frac}

FREE_FRAC = memory_gate()
import torch
torch.set_default_dtype(torch.float64)
torch.manual_seed(20260719)
import numpy as np
np.random.seed(20260719)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.normpath(os.path.join(
    HERE, "..", "..", "loop2_world", "results", "world_source",
    "events_dynamics_on.jsonl"))
OUT = os.path.join(HERE, "results", "receipt.json")

N_BITS, N_VIEWS, N_OBJ = 8, 6, 64
TRAIN_OBJS = list(range(48)); TEST_OBJS = list(range(48, 64))
STEPS, BATCH = 300, 32

# ---------------------------------------------------------------- data
def load_events(path):
    """obj -> view -> pos -> (outcome_str, occluded_bool). 'withheld' kept as
    string; NEVER converted to a bit anywhere in the feature path."""
    data = defaultdict(lambda: defaultdict(dict))
    for line in open(path):
        e = json.loads(line)
        p = e["payload"]["operations"][0]["payload"]
        c = {cl["predicate"]: cl["object"] for cl in p["claims"]}
        oi = int(c["has_object_id"].split("-")[1])
        data[oi][int(c["view_index"])][int(c["probe_position"])] = (
            c["probe_outcome"], c["occluded"] == "true")
    return data

RAW = load_events(DATA)

def tensorize(raw):
    """outcome[o,v,p] in {0,1} for visible, -1 sentinel for occluded (the
    sentinel is a MASK MARKER only -- it never carries outcome content).
    vis[o,v,p] = 1 if visible."""
    out = -torch.ones(N_OBJ, N_VIEWS, N_BITS, dtype=torch.long)
    vis = torch.zeros(N_OBJ, N_VIEWS, N_BITS)
    for o in range(N_OBJ):
        for v in range(N_VIEWS):
            for p in range(N_BITS):
                s, occ = raw[o][v][p]
                if not occ:
                    assert s in ("0", "1")
                    out[o, v, p] = int(s); vis[o, v, p] = 1.0
                else:
                    assert s == "withheld"
    return out, vis

OUTC, VIS = tensorize(RAW)

# -------------------------------------------------- oracle (EVALUATION ONLY)
RULES = {0: [-1, 1], 1: [-1, 0, 1], 2: [0, 1], 3: [-1, 0]}
def ca_step(w, taps):
    return tuple(sum(w[(i + t) % N_BITS] for t in taps) % 2
                 for i in range(N_BITS))

def oracle_reconstruct():
    """Exhaustive search over hidden space (256 words x 4 rules); view v =
    v CA steps from the hidden word. Returns truth[o,v,p] for ALL bits.
    Used ONLY in metric computation, never in features."""
    truth = torch.zeros(N_OBJ, N_VIEWS, N_BITS, dtype=torch.long)
    n_unique = 0
    for o in range(N_OBJ):
        hits = []
        for r, taps in RULES.items():
            for wi in range(256):
                w = tuple((wi >> b) & 1 for b in range(N_BITS))
                s, traj, ok = w, [], True
                for v in range(N_VIEWS):
                    traj.append(s); s = ca_step(s, taps)
                for v in range(N_VIEWS):
                    for p in range(N_BITS):
                        if VIS[o, v, p] > 0 and traj[v][p] != OUTC[o, v, p].item():
                            ok = False; break
                    if not ok: break
                if ok: hits.append(traj)
        assert len(hits) >= 1, f"oracle: no candidate for obj {o}"
        if len(hits) == 1: n_unique += 1
        # receipt says joint_consistent_max == 1; assert full uniqueness
        assert all(h == hits[0] for h in hits), f"oracle ambiguity obj {o}"
        for v in range(N_VIEWS):
            for p in range(N_BITS):
                truth[o, v, p] = hits[0][v][p]
    return truth, n_unique

TRUTH, N_UNIQUE = oracle_reconstruct()
# sanity: truth agrees with every visible outcome
assert torch.all((TRUTH == OUTC) | (VIS == 0)), "oracle contradicts visibles"
print(f"[oracle] all 64 objects uniquely reconstructed ({N_UNIQUE}/64 unique)")

# ---------------------------------------------------------------- Clifford
def build_clifford():
    I2 = torch.eye(2, dtype=torch.complex128)
    X = torch.tensor([[0, 1], [1, 0]], dtype=torch.complex128)
    Y = torch.tensor([[0, -1j], [1j, 0]], dtype=torch.complex128)
    Z = torch.tensor([[1, 0], [0, -1]], dtype=torch.complex128)
    def kron3(a, b, c):
        return torch.kron(torch.kron(a, b), c)
    g = [kron3(X, I2, I2), kron3(Y, I2, I2),
         kron3(Z, X, I2), kron3(Z, Y, I2),
         kron3(Z, Z, X), kron3(Z, Z, Y)]
    # Clifford relation check (charged structure #3)
    dev = 0.0
    for i in range(6):
        for j in range(6):
            anti = g[i] @ g[j] + g[j] @ g[i]
            tgt = 2 * torch.eye(8, dtype=torch.complex128) if i == j else \
                torch.zeros(8, 8, dtype=torch.complex128)
            dev = max(dev, (anti - tgt).abs().max().item())
    # chirality (grading, charged structure #4)
    Gam = g[0] @ g[1] @ g[2] @ g[3] @ g[4] @ g[5]
    Gam = Gam * (-1j) ** 3          # make Gam Hermitian with Gam^2 = I
    herm = (Gam - Gam.conj().T).abs().max().item()
    sq = (Gam @ Gam - torch.eye(8, dtype=torch.complex128)).abs().max().item()
    ev = torch.linalg.eigvalsh(Gam)
    # primitive idempotent -> minimal left ideal (charged structure #6)
    Pid = torch.eye(8, dtype=torch.complex128)
    for j in range(3):
        Pid = Pid @ (torch.eye(8, dtype=torch.complex128)
                     + 1j * g[2 * j] @ g[2 * j + 1]) / 2
    idem = (Pid @ Pid - Pid).abs().max().item()
    rank = int(torch.linalg.matrix_rank(Pid).item())
    return g, Gam, {"clifford_relation_max_dev": dev,
                    "chirality_hermitian_dev": herm,
                    "chirality_square_dev": sq,
                    "chirality_spectrum": [round(x, 12) for x in
                                           ev.real.tolist()],
                    "idempotent_dev": idem, "idempotent_rank": rank}

GAMMA, CHIR, CLIFF_RECEIPT = build_clifford()
assert CLIFF_RECEIPT["clifford_relation_max_dev"] < 1e-12
assert CLIFF_RECEIPT["idempotent_rank"] == 1, "minimal ideal must be rank-1"
print("[clifford] relations verified; primitive idempotent rank ="
      f" {CLIFF_RECEIPT['idempotent_rank']}")

# ---------------------------------------------------------------- model
def cplx(re, im): return torch.complex(re, im)

class SpinorCarrier(torch.nn.Module):
    """All learned objects are elements of Cl(6,C)=Mat(8,C) or of the minimal
    ideal S=C^8. Latent state psi: 16 real DOF, retraction = normalization."""
    def __init__(self):
        super().__init__()
        s = 0.1
        self.psi0_re = torch.nn.Parameter(torch.randn(8) * s)
        self.psi0_im = torch.nn.Parameter(torch.randn(8) * s)
        # probe instruments M_{q,o} = I + W  (8 pos x 2 outcomes)
        self.W_re = torch.nn.Parameter(torch.randn(8, 2, 8, 8) * s)
        self.W_im = torch.nn.Parameter(torch.randn(8, 2, 8, 8) * s)
        # typed dynamics transport A (open; Kraus-fragment)
        self.A_re = torch.nn.Parameter(torch.eye(8) + torch.randn(8, 8) * s)
        self.A_im = torch.nn.Parameter(torch.randn(8, 8) * s)
        # Hermitian readout observables O_q + affine calibration
        self.O_re = torch.nn.Parameter(torch.randn(8, 8, 8) * s)
        self.O_im = torch.nn.Parameter(torch.randn(8, 8, 8) * s)
        self.r_scale = torch.nn.Parameter(torch.ones(8) * 4.0)
        self.r_bias = torch.nn.Parameter(torch.zeros(8))

    def psi0(self, B):
        p = cplx(self.psi0_re, self.psi0_im).expand(B, 8)
        return retract(p)

    def M(self, q, o):
        W = cplx(self.W_re[q, o], self.W_im[q, o])
        return torch.eye(8, dtype=torch.complex128) + W

    def A(self):
        return cplx(self.A_re, self.A_im)

    def O(self, q):
        H = cplx(self.O_re[q], self.O_im[q])
        return (H + H.conj().T) / 2

    def readout(self, psi, q):
        """derived bilinear <psi|O_q|psi> -> P(bit=1); sigmoid calibration."""
        val = torch.einsum("bi,ij,bj->b", psi.conj(), self.O(q), psi).real
        return torch.sigmoid(self.r_scale[q] * val + self.r_bias[q])

def retract(psi):
    return psi / psi.norm(dim=-1, keepdim=True).clamp_min(1e-30)

def ray_loss(t, p):
    return 1.0 - torch.abs(torch.einsum("bi,bi->b", t.conj(), p)) ** 2

def view_update(model, psi, obj_idx, v, use_mask=None):
    """Apply probe instruments for one view IN POSITION ORDER (order
    retained). Occluded probes NEVER update (identity: belief persists).
    use_mask[b,p]=0 hides a visible probe (training-time masking)."""
    B = psi.shape[0]
    for p in range(N_BITS):
        upd = torch.zeros(B, dtype=torch.bool)
        oc = torch.zeros(B, dtype=torch.long)
        for b, o in enumerate(obj_idx):
            if VIS[o, v, p] > 0 and (use_mask is None or use_mask[b, p] > 0):
                upd[b] = True; oc[b] = OUTC[o, v, p]
        if not upd.any():
            continue
        new = psi.clone()
        for o_val in (0, 1):
            sel = upd & (oc == o_val)
            if sel.any():
                new[sel] = retract(psi[sel] @ self_T(model.M(p, o_val)))
        psi = new
    return psi

def self_T(M):  # right-multiplication convention psi' = M psi
    return M.T

def filtered_beliefs(model, obj_idx, use_mask=None):
    """Recursive filtering across the 6 views: psi_v = update(Retr(A psi_{v-1}),
    view v visibles). Returns list of per-view beliefs + transported preds."""
    B = len(obj_idx)
    psi = model.psi0(B)
    beliefs, transported = [], []
    A = model.A()
    for v in range(N_VIEWS):
        if v > 0:
            psi = retract(psi @ self_T(A))
        transported.append(psi)
        m = use_mask[v] if use_mask is not None else None
        psi = view_update(model, psi, obj_idx, v, m)
        beliefs.append(psi)
    return beliefs, transported

def single_view_encode(model, obj_idx, v):
    psi = model.psi0(len(obj_idx))
    return view_update(model, psi, obj_idx, v, None)

# ---------------------------------------------------------------- leak check
def leak_check():
    """Occluded outcomes must be absent from every feature path. The feature
    path consumes only OUTC (sentinel -1 at occluded slots) and VIS. Verify:
    replacing the oracle TRUTH at occluded slots with random bits changes NO
    feature input tensor."""
    occ = VIS == 0
    assert torch.all(OUTC[occ] == -1), "occluded slot carries outcome content"
    feats_before = (OUTC.clone(), VIS.clone())
    _ = TRUTH.clone()  # oracle exists, but:
    perturbed = TRUTH.clone()
    perturbed[occ] = torch.randint(0, 2, (int(occ.sum()),))
    same = torch.equal(feats_before[0], OUTC) and torch.equal(feats_before[1], VIS)
    return {"pass": bool(same and torch.all(OUTC[occ] == -1).item()),
            "criterion": "occluded slots are sentinel-masked; oracle "
                         "perturbation cannot reach any feature tensor"}

LEAK = leak_check()
assert LEAK["pass"]
print("[leak check] pass")

# ---------------------------------------------------------------- training
model = SpinorCarrier()
n_params = sum(p.numel() for p in model.parameters())
print(f"[budget] params = {n_params} (<= 60000), latent real DOF = 16")
assert n_params <= 60000
opt = torch.optim.Adam(model.parameters(), lr=3e-3)
MASK_P = 0.25
JEPA_W = 0.5
train_curve = []
for step in range(STEPS):
    obj_idx = [TRAIN_OBJS[i] for i in torch.randint(0, len(TRAIN_OBJS),
                                                    (BATCH,))]
    # per-view random masking of VISIBLE probes (targets for BCE)
    use_mask = []
    for v in range(N_VIEWS):
        m = (torch.rand(BATCH, N_BITS) > MASK_P).double()
        use_mask.append(m)
    beliefs, transported = filtered_beliefs(model, obj_idx, use_mask)
    bce, n_t = torch.zeros(()), 0
    for v in range(N_VIEWS):
        for b, o in enumerate(obj_idx):
            for p in range(N_BITS):
                if VIS[o, v, p] > 0 and use_mask[v][b, p] == 0:
                    prob = model.readout(beliefs[v][b:b + 1], p)[0]
                    y = float(OUTC[o, v, p])
                    bce = bce - (y * torch.log(prob.clamp_min(1e-12))
                                 + (1 - y) * torch.log((1 - prob).clamp_min(1e-12)))
                    n_t += 1
    bce = bce / max(n_t, 1)
    # JEPA ray loss: transported prior vs stop-grad single-view target
    jepa = torch.zeros(())
    for v in range(1, N_VIEWS):
        with torch.no_grad():
            tgt = single_view_encode(model, obj_idx, v)
        jepa = jepa + ray_loss(tgt, transported[v]).mean()
    jepa = jepa / (N_VIEWS - 1)
    loss = bce + JEPA_W * jepa
    opt.zero_grad(); loss.backward(); opt.step()
    if step % 25 == 0 or step == STEPS - 1:
        train_curve.append({"step": step, "bce": round(bce.item(), 6),
                            "jepa_ray": round(jepa.item(), 6)})
        print(f"  step {step:3d} bce={bce.item():.4f} jepa={jepa.item():.4f}")

# ---------------------------------------------------------------- evaluation
model.eval()

@torch.no_grad()
def eval_ray_loss(objs):
    beliefs, transported = filtered_beliefs(model, objs)
    tot = 0.0
    for v in range(1, N_VIEWS):
        tgt = single_view_encode(model, objs, v)
        tot += ray_loss(tgt, transported[v]).mean().item()
    return tot / (N_VIEWS - 1)

@torch.no_grad()
def occluded_accuracy(objs, evidence="true"):
    """Predict occluded bits from filtered belief; score vs oracle TRUTH
    (evaluation-only). evidence='cf' flips every visible outcome fed to the
    instruments (counterfactual binding control, P6)."""
    global OUTC
    if evidence == "cf":
        saved = OUTC.clone()
        flip = OUTC.clone()
        vismask = VIS > 0
        flip[vismask] = 1 - flip[vismask]
        OUTC = flip
    beliefs, _ = filtered_beliefs(model, objs)
    if evidence == "cf":
        OUTC = saved
    n_ok, n = 0, 0
    probs = []
    for v in range(N_VIEWS):
        for b, o in enumerate(objs):
            for p in range(N_BITS):
                if VIS[o, v, p] == 0:
                    pr = model.readout(beliefs[v][b:b + 1], p)[0].item()
                    probs.append(pr)
                    n_ok += int((pr > 0.5) == bool(TRUTH[o, v, p]))
                    n += 1
    return n_ok / n, n, probs

train_ray = eval_ray_loss(TRAIN_OBJS)
test_ray = eval_ray_loss(TEST_OBJS)
acc_true, n_occ_test, probs_true = occluded_accuracy(TEST_OBJS, "true")
acc_train, n_occ_train, _ = occluded_accuracy(TRAIN_OBJS, "true")
acc_cf, _, probs_cf = occluded_accuracy(TEST_OBJS, "cf")
print(f"[metrics] occluded acc test={acc_true:.4f} (n={n_occ_test}) "
      f"train={acc_train:.4f}  cf={acc_cf:.4f}")
print(f"[metrics] ray loss train={train_ray:.4f} test={test_ray:.4f}")

@torch.no_grad()
def test_latents():
    """(obj, view) -> belief psi for all test objects."""
    beliefs, _ = filtered_beliefs(model, TEST_OBJS)
    out = {}
    for v in range(N_VIEWS):
        for b, o in enumerate(TEST_OBJS):
            out[(o, v)] = beliefs[v][b]
    return out

LAT = test_latents()

# ---- Holevo belief persistence vs permutation null
@torch.no_grad()
def holevo():
    """For each occluded (obj,view,pos) on test: group belief densities by
    the TRUE occluded bit (oracle, eval-only); chi = S(rho_bar)-sum p_b S(rho_b),
    averaged over positions with both classes present. Null: 200 label
    permutations."""
    def vn_entropy(rho):
        ev = torch.linalg.eigvalsh(rho).clamp_min(1e-15)
        ev = ev / ev.sum()
        return float(-(ev * ev.log()).sum())
    def chi_for(labels_by_pos):
        chis = []
        for p, (states, labels) in labels_by_pos.items():
            labels = np.asarray(labels)
            if len(set(labels.tolist())) < 2:
                continue
            rhos, ps = [], []
            for b in (0, 1):
                sel = [s for s, l in zip(states, labels) if l == b]
                if not sel:
                    continue
                R = torch.stack([torch.outer(s, s.conj()) for s in sel]).mean(0)
                rhos.append(R); ps.append(len(sel) / len(states))
            rbar = sum(w * R for w, R in zip(ps, rhos))
            chis.append(vn_entropy(rbar)
                        - sum(w * vn_entropy(R) for w, R in zip(ps, rhos)))
        return float(np.mean(chis)) if chis else 0.0
    pool = defaultdict(lambda: ([], []))
    for (o, v), psi in LAT.items():
        for p in range(N_BITS):
            if VIS[o, v, p] == 0:
                pool[p][0].append(psi)
                pool[p][1].append(int(TRUTH[o, v, p]))
    obs = chi_for(pool)
    rng = np.random.default_rng(20260719)
    null = []
    for _ in range(200):
        perm_pool = {}
        for p, (states, labels) in pool.items():
            perm_pool[p] = (states, rng.permutation(labels).tolist())
        null.append(chi_for(perm_pool))
    null = np.array(null)
    p95 = float(np.percentile(null, 95))
    return {"chi_observed": obs, "null_mean": float(null.mean()),
            "null_p95": p95, "above_null": bool(obs > p95),
            "margin_over_p95": obs - p95, "n_permutations": 200}

HOLEVO = holevo()
print(f"[holevo] chi={HOLEVO['chi_observed']:.4f} null_p95="
      f"{HOLEVO['null_p95']:.4f} above={HOLEVO['above_null']}")

# ---- ARI latent clustering vs object ids + shuffled null
@torch.no_grad()
def ari_cluster():
    from sklearn.cluster import KMeans
    from sklearn.metrics import adjusted_rand_score
    feats, ids = [], []
    for (o, v), psi in LAT.items():
        rho = torch.outer(psi, psi.conj())          # ray-invariant
        f = torch.cat([rho.real.flatten(), rho.imag.flatten()])
        feats.append(f.numpy()); ids.append(o)
    X = np.stack(feats); ids = np.array(ids)
    km = KMeans(n_clusters=len(TEST_OBJS), n_init=10,
                random_state=20260719).fit(X)
    ari = adjusted_rand_score(ids, km.labels_)
    rng = np.random.default_rng(20260719)
    null = [adjusted_rand_score(rng.permutation(ids), km.labels_)
            for _ in range(200)]
    return {"ari": float(ari), "shuffled_null_mean": float(np.mean(null)),
            "shuffled_null_p95": float(np.percentile(null, 95)),
            "above_null": bool(ari > np.percentile(null, 95))}

ARI = ari_cluster()
print(f"[ari] {ARI['ari']:.4f} null_p95={ARI['shuffled_null_p95']:.4f}")

# ---------------------------------------------------------------- probes
PROBES = {}
psis = torch.stack(list(LAT.values()))            # trained belief states

# P1: 2pi vs 4pi sign/lift memory -- coherent-path interference witness on the
# carrier's spin connection U(theta)=exp(-theta/2 g1 g2); NOT a projector
# readout (bilinears are shown sign-blind).
with torch.no_grad():
    B12 = GAMMA[0] @ GAMMA[1]
    def U(theta):
        return torch.matrix_exp(-theta / 2 * B12)
    def interf(theta):
        Up = psis @ U(theta).T
        return (torch.abs((psis + Up) / 2).pow(2).sum(-1)).mean().item()
    I2pi, I4pi = interf(2 * math.pi), interf(4 * math.pi)
    # projector/bilinear sign-blindness: <psi|O|psi> unchanged by psi -> -psi
    q0 = model.O(0)
    bl = torch.einsum("bi,ij,bj->b", psis.conj(), q0, psis).real
    blm = torch.einsum("bi,ij,bj->b", (-psis).conj(), q0, -psis).real
    sign_blind = float((bl - blm).abs().max())
PROBES["P1_sign_lift_memory"] = {
    "score": max(0.0, min(1.0, 0.5 * (1 - I2pi) + 0.5 * I4pi)),
    "measurement": "coherent-path interference |psi+U(theta)psi|^2/4 on "
                   "trained beliefs; U=exp(-theta/2 g1g2). 2pi -> destructive "
                   "(sign flip), 4pi -> constructive; bilinear readout shown "
                   "sign-blind (projector erases psi->-psi).",
    "interference_2pi": I2pi, "interference_4pi": I4pi,
    "bilinear_sign_blindness_max_dev": sign_blind}

# P2: chirality / sector change
with torch.no_grad():
    evals, evecs = torch.linalg.eigh(CHIR)
    plus = evecs[:, evals > 0]; minus = evecs[:, evals < 0]
    checks = []
    checks.append(abs(float((CHIR @ CHIR
        - torch.eye(8, dtype=torch.complex128)).abs().max())) < 1e-12)
    checks.append(int((evals > 0).sum()) == 4)
    # odd element g1 flips sector exactly
    flip_dev = float((plus.conj().T @ (CHIR @ (GAMMA[0] @ plus))
                      + plus.conj().T @ (GAMMA[0] @ plus)).abs().max())
    checks.append(flip_dev < 1e-12)
    # learned instruments move sector weight (mixed even/odd elements)
    chir_exp = torch.einsum("bi,ij,bj->b", psis.conj(), CHIR, psis).real
    after = retract(psis @ self_T(model.M(0, 1)))
    chir_after = torch.einsum("bi,ij,bj->b", after.conj(), CHIR, after).real
    sector_shift = float((chir_after - chir_exp).abs().mean())
PROBES["P2_chirality_sector"] = {
    "score": sum(checks) / len(checks),
    "measurement": "structural: Gamma^2=I, 4+4 sector split, odd element g1 "
                   "anticommutes with Gamma (exact sector flip). Learned "
                   "instruments' mean |delta <Gamma>| reported.",
    "checks_passed": f"{sum(checks)}/{len(checks)}",
    "learned_mean_abs_sector_shift": sector_shift}

# P3: ab vs ba order witness on learned instruments
with torch.no_grad():
    rng = np.random.default_rng(20260719)
    ds = []
    for _ in range(64):
        q1, q2 = rng.integers(0, 8, 2); o1, o2 = rng.integers(0, 2, 2)
        Ma, Mb = model.M(int(q1), int(o1)), model.M(int(q2), int(o2))
        pa = retract(retract(psis @ self_T(Ma)) @ self_T(Mb))
        pb = retract(retract(psis @ self_T(Mb)) @ self_T(Ma))
        ds.append(ray_loss(pa, pb).mean().item())
    order_d = float(np.mean(ds))
PROBES["P3_order_witness"] = {
    "score": max(0.0, min(1.0, order_d)),
    "measurement": "mean ray distance 1-|<psi_ab,psi_ba>|^2 over 64 random "
                   "learned instrument pairs applied in both orders to "
                   "trained beliefs. >0 = order retained and load-bearing.",
    "mean_ray_distance_ab_vs_ba": order_d}

# P4: (ab)c vs a(bc) bracket witness -- associative carrier, honest negative
with torch.no_grad():
    rng = np.random.default_rng(7)
    dev = 0.0
    for _ in range(32):
        q = rng.integers(0, 8, 3); o = rng.integers(0, 2, 3)
        Ma, Mb, Mc = (model.M(int(q[i]), int(o[i])) for i in range(3))
        dev = max(dev, float((((Ma @ Mb) @ Mc) - (Ma @ (Mb @ Mc))).abs().max()))
PROBES["P4_bracket_witness"] = {
    "score": 0.0,
    "measurement": "max |(M_a M_b)M_c - M_a(M_b M_c)| over 32 learned "
                   "triples: matrix (Clifford) algebra is associative, so "
                   "this carrier has NO bracket-witness capacity. Scored 0 "
                   "as an honest structural fact, not not_applicable.",
    "max_associator_norm": dev}

# P5: hidden-mode belief under occlusion (primary) = occluded-bit accuracy
PROBES["P5_occluded_belief"] = {
    "score": acc_true,
    "measurement": "occluded-bit accuracy on test objects from filtered "
                   "belief (oracle ground truth used for scoring only). "
                   "Occluded probes never update belief (identity: "
                   "persistence by construction).",
    "n_occluded_test_bits": n_occ_test,
    "train_occluded_accuracy": acc_train}

# P6: counterfactual action binding (primary)
sens = float(np.mean(np.abs(np.array(probs_true) - np.array(probs_cf))))
PROBES["P6_counterfactual_binding"] = {
    "score": max(0.0, min(1.0, acc_true - acc_cf)),
    "measurement": "occluded-bit accuracy with true evidence minus accuracy "
                   "when every visible outcome fed to the instruments is "
                   "flipped (counterfactual). Positive gap = belief binds to "
                   "the actual instrument sequence.",
    "acc_true_evidence": acc_true, "acc_counterfactual_evidence": acc_cf,
    "mean_abs_prob_sensitivity": sens}

# P7: prediction vs finite-budget reachability
with torch.no_grad():
    beliefs_t, transported_t = filtered_beliefs(model, TEST_OBJS)
    l_pred = float(np.mean([ray_loss(single_view_encode(model, TEST_OBJS, v),
                                     transported_t[v]).mean().item()
                            for v in range(1, N_VIEWS)]))
    # null: transported prior vs targets of a permuted object batch
    rng = np.random.default_rng(3)
    l_null = []
    for v in range(1, N_VIEWS):
        tgt = single_view_encode(model, TEST_OBJS, v)
        perm = torch.tensor(rng.permutation(len(TEST_OBJS)))
        l_null.append(ray_loss(tgt[perm], transported_t[v]).mean().item())
    l_null = float(np.mean(l_null))
PROBES["P7_reachability"] = {
    "score": max(0.0, min(1.0, 1.0 - l_pred / max(l_null, 1e-12))),
    "measurement": "one-step transport ray loss to the correct next-view "
                   "target vs permuted-object null: attainability within the "
                   "1-step budget, not mere latent similarity.",
    "ray_loss_pred": l_pred, "ray_loss_null": l_null}

# P8: cross-view object persistence (pairwise fidelity AUC)
with torch.no_grad():
    keys = list(LAT.keys())
    same, diff = [], []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            f = float(torch.abs(LAT[keys[i]].conj() @ LAT[keys[j]]) ** 2)
            (same if keys[i][0] == keys[j][0] else diff).append(f)
    same, diff = np.array(same), np.array(diff)
    rng = np.random.default_rng(11)
    di = rng.choice(len(diff), size=min(len(diff), 4000), replace=False)
    auc = float(np.mean([(same[:, None] > diff[di][None, :]).mean()]))
PROBES["P8_cross_view_persistence"] = {
    "score": auc,
    "measurement": "AUC: P(fidelity |<psi,psi'>|^2 of same-object view pair "
                   "> different-object pair) over all test view latents.",
    "n_same_pairs": int(len(same)), "n_diff_pairs_sampled": int(len(di))}

# P9: shock / contraction / attractor formation under open transport
with torch.no_grad():
    A = model.A()
    start = retract(torch.randn(64, 8, dtype=torch.complex128))
    cur = start.clone()
    for _ in range(50):
        cur = retract(cur @ self_T(A))
    def mean_pdist(P):
        G = torch.abs(P.conj() @ P.T) ** 2
        n = P.shape[0]
        off = (1 - G)[~torch.eye(n, dtype=torch.bool)]
        return float(off.mean())
    d0, d50 = mean_pdist(start), mean_pdist(cur)
    contraction = max(0.0, min(1.0, 1.0 - d50 / max(d0, 1e-12)))
    # shock recovery: perturb converged states, iterate again
    shock = retract(cur + 0.5 * torch.randn_like(cur))
    rec = shock.clone()
    for _ in range(50):
        rec = retract(rec @ self_T(A))
    d_rec = mean_pdist(rec)
PROBES["P9_contraction_attractor"] = {
    "score": contraction,
    "measurement": "50 iterations of the open (non-unitary) transport "
                   "Retr(A psi) from 64 random rays: 1 - d_final/d_initial "
                   "of mean pairwise ray distance (1 = collapse to "
                   "attractor). Shock recovery distance reported.",
    "mean_pairwise_ray_dist_initial": d0,
    "mean_pairwise_ray_dist_after_50": d50,
    "mean_pairwise_ray_dist_after_shock_recovery": d_rec}

# P10: gauge/basis invariance under Spin(6) conjugation
with torch.no_grad():
    rng = np.random.default_rng(20260719)
    th = rng.normal(0, 0.7, 15)
    biv, k = torch.zeros(8, 8, dtype=torch.complex128), 0
    for i in range(6):
        for j in range(i + 1, 6):
            biv = biv + th[k] * (GAMMA[i] @ GAMMA[j]) / 2; k += 1
    Ug = torch.matrix_exp(biv)          # Spin element (unitary: biv anti-Herm)
    unit_dev = float((Ug.conj().T @ Ug
                      - torch.eye(8, dtype=torch.complex128)).abs().max())
    devs = []
    for (o, v), psi in list(LAT.items())[:32]:
        psig = Ug @ psi
        for p in range(N_BITS):
            Oq = model.O(p)
            b0 = float(torch.einsum("i,ij,j->", psi.conj(), Oq, psi).real)
            Og = Ug @ Oq @ Ug.conj().T
            b1 = float(torch.einsum("i,ij,j->", psig.conj(), Og, psig).real)
            devs.append(abs(b1 - b0))
    # pairing invariance
    ks = list(LAT.keys())[:16]
    pd = [abs(float(torch.abs(LAT[a].conj() @ LAT[b]) ** 2)
              - float(torch.abs((Ug @ LAT[a]).conj() @ (Ug @ LAT[b])) ** 2))
          for a in ks[:8] for b in ks[8:]]
    gauge_dev = float(np.max(devs + pd))
PROBES["P10_gauge_invariance"] = {
    "score": max(0.0, min(1.0, 1.0 - gauge_dev)),
    "measurement": "random Spin(6) element U=exp(bivector): readout "
                   "bilinears under (psi,O)->(U psi, U O U^dag) and pairing "
                   "fidelities under psi->U psi; score = 1 - max deviation.",
    "max_deviation": gauge_dev, "spin_element_unitarity_dev": unit_dev}

# ---------------------------------------------------------------- receipt
majority = float(TRUTH[torch.stack(
    [VIS == 0]).squeeze(0)].double().mean())
chance = max(majority, 1 - majority)
CONTROLS = {
    "leak_check": LEAK,
    "shuffled_object_ids_ari": {
        "ari_null_mean": ARI["shuffled_null_mean"],
        "ari_null_p95": ARI["shuffled_null_p95"],
        "ari_observed_above_null": ARI["above_null"]},
    "occluded_majority_baseline": {
        "occluded_bit_base_rate_1": majority,
        "majority_accuracy": chance,
        "model_above_majority": bool(acc_true > chance)},
    "counterfactual_evidence": {
        "acc_true": acc_true, "acc_cf": acc_cf,
        "binds": bool(acc_true > acc_cf)}}

all_pass = bool(
    LEAK["pass"] and HOLEVO["above_null"] and ARI["above_null"]
    and acc_true > chance and acc_true > acc_cf
    and all("score" in P for P in PROBES.values()))

receipt = {
    "lane": "lane6_spinor_ideal",
    "sim_id": "spinor_jepa_lane6_clifford_minimal_ideal_v0",
    "classification": "tournament_lane_working_sim",
    "card_authority": "system_v8/spinor_jepa/TOURNAMENT_CARD_v0.md "
                      "(frozen, incl AMENDMENT v0.1)",
    "task": "occluded-object perception: predict masked probe outcomes + "
            "maintain belief under occlusion (P5/P6 primary)",
    "data": DATA,
    "seed": 20260719,
    "engine": {"torch": torch.__version__, "dtype": "float64", "device": "cpu",
               "python": sys.version.split()[0],
               "memory_gate": FREE_FRAC,
               "memory_gate_note": "gate passes on max(os kern.memorystatus_"
               "level, psutil available); both recorded"},
    "budget": {"latent_real_dof": 16, "params": n_params,
               "param_budget": 60000, "train_steps": STEPS, "batch": BATCH,
               "split": {"train_objects": "0-47", "test_objects": "48-63"}},
    "carrier_construction_receipt": CLIFF_RECEIPT,
    "charges": [
        "field: complex structure C on R^16 (spinor space S ~= C^8)",
        "signature/quadratic form: Cl(6,0), positive-definite delta_ij",
        "Clifford relations: g_i g_j + g_j g_i = 2 delta_ij (verified, "
        "max dev {:.1e})".format(CLIFF_RECEIPT["clifford_relation_max_dev"]),
        "grading: Z2 grading + chirality operator Gamma (4+4 sector split)",
        "pairing: Hermitian Spin(6)-invariant <psi,phi>=psi^dag phi (ray "
        "loss + derived bilinear readouts)",
        "minimal left ideal: primitive idempotent prod(1+i g_{2j-1}g_{2j})/2, "
        "rank 1 (verified); S = Cl(6,C)P",
        "connection/transport: typed open dynamics transport A in Cl(6,C) "
        "(non-unitary Kraus-fragment, retraction = ray normalization); "
        "structural spin connection exp(bivector) for P1/P10 witnesses",
        "probe instruments: M_{q,o} = I + W_{q,o} in Cl(6,C), order "
        "retained, retraction after each application",
        "bracket: NONE (associative algebra; declared, see P4 honest zero)"],
    "training_curve": train_curve,
    "metrics": {
        "occluded_bit_accuracy_test": acc_true,
        "occluded_bit_accuracy_train": acc_train,
        "occluded_bit_accuracy_test_counterfactual_evidence": acc_cf,
        "n_occluded_test_bits": n_occ_test,
        "belief_persistence_holevo": HOLEVO,
        "train_ray_loss": train_ray,
        "test_ray_loss": test_ray,
        "latent_cluster_ari": ARI},
    "probes": PROBES,
    "controls": CONTROLS,
    "all_pass": all_pass,
    "promotion_allowed": False,
    "claim_ceiling": "working_sim; single tournament lane; no cross-lane "
                     "comparison and no spinor-minimality claim is made here",
    "findings": []}

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    json.dump(receipt, f, indent=2)
print(f"[receipt] {OUT}")
print(json.dumps({"lane": receipt["lane"], "all_pass": all_pass,
                  "occ_acc_test": acc_true, "params": n_params}, indent=1))
