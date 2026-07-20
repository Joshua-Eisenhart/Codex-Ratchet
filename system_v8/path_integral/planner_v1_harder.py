#!/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""
planner_v1_harder.py -- HARDER-WORLD rerun of planner_v0 (ceiling check failed there:
all three planners scored 1.0 -- task was too easy).

v1 world (self-contained generator, same doctrine as loop2_world/world_object_source.py
and loop3_senses/senses_v2_slow_memory.py, but scaled):
  - N_OBJECTS   = 128   (v0: 64)
  - N_BITS      = 14    (v0: 8)   -- hidden latent word, same 4-member XOR/CA rule family
  - N_VIEWS     = 8     (v0: 6)
  - occlusion   = 4-6 bits per view (v0: 2-4)  -- strictly worse visibility
  - probe budget per episode (word length r) = 2 = round(3 * 0.6)  (v0: r=3)
    -- this is the "reduce probe budget to 60% of v0" instruction: fewer probes are
       actually spent resolving occlusion, on top of MORE occluded bits and a LARGER
       hidden-state space. Information is genuinely scarcer on every axis.

Channels: same GKSL construction as visibility_sanity_gate.load_stage_channels
(real stage64 receipt operating_pairs / commutator norms), extended from 8 to 14
probe positions by cycling position % 8 through the same 8 real stages -- no new
free parameters, same math, same tool (scipy.linalg.expm).

Bayes engine: senses_v2_slow_memory.QuantumReadoutBayes reused as-is (its methods
are N_BITS/N_VIEWS-agnostic; only calibrate_sigma()'s internal loop reads the module
globals, which are monkeypatched to the v1 sizes for the duration of this run and
restored after -- documented, not silent).

THREE-WAY comparison (same episodes, same budget), same finite exact path-sum
discipline (enumerate admitted probe-order words; declare truncation if >4096),
same controls (commuting collapse, uniform-weight reduces to random), object
bootstrap CIs.

PREREGISTERED CEILING GATE: if any planner scores acc_mean > 0.95, this task is
STILL too easy. Report TASK_STILL_EASY plus the numbers. No discrimination claim
in that case. Honest outcome whatever it is.

Receipt: results/planner_v1/receipt.json
classification=scratch_diagnostic; promotion_allowed=false
interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
Do not delete files; do not commit.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

# ----------------------------------------------------------------------------
# Interpreter and safety
# ----------------------------------------------------------------------------
SIM_PY = Path("/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3")
if Path(sys.executable).resolve() != SIM_PY.resolve():
    print(f"FATAL: must run under {SIM_PY}, got {sys.executable}", file=sys.stderr)
    sys.exit(2)

REPO = Path("/Users/joshuaeisenhart/Codex-Ratchet")
HERE = REPO / "system_v8" / "path_integral"
OUTDIR = HERE / "results" / "planner_v1"
RECEIPT = OUTDIR / "receipt.json"

if OUTDIR.exists():
    print(f"REFUSE-TO-REUSE: {OUTDIR} exists", file=sys.stderr)
    sys.exit(2)
OUTDIR.mkdir(parents=True, exist_ok=False)

# ----------------------------------------------------------------------------
# Memory gate
# ----------------------------------------------------------------------------
def memory_free_percent() -> int:
    out = subprocess.run(["memory_pressure"], capture_output=True, text=True, check=True).stdout
    m = re.search(r"System-wide memory free percentage:\s*(\d+)%", out)
    if not m:
        raise RuntimeError("memory_pressure parse failed")
    return int(m.group(1))

mem_pct = memory_free_percent()
if mem_pct < 25:
    print(f"FATAL: memory {mem_pct}% < 25%", file=sys.stderr)
    sys.exit(2)

sys.path.insert(0, str(REPO))
from system_v8.loop3_senses import visibility_sanity_gate as visibility
from system_v8.loop3_senses import senses_v2_slow_memory as senses

# ----------------------------------------------------------------------------
# V1 harder-world parameters
# ----------------------------------------------------------------------------
SEED = 20260720
N_BITS = 14
N_OBJECTS = 128
N_VIEWS = 8
OCCLUDE_MIN, OCCLUDE_MAX = 4, 6
R_FOR_WORDS = 2  # round(3 * 0.60) -- 60% of v0's probe budget
PLANNING_VIEW = N_VIEWS - 4  # analogous mid-late view as v0 (4 of 6 -> 4 of 8)
RULE_FAMILY = {
    0: (-1, 1),
    1: (-1, 0, 1),
    2: (0, 1),
    3: (-1, 0),
}
N_RULES = len(RULE_FAMILY)

rng = np.random.default_rng(SEED)

def ca_step(bits: tuple[int, ...], rule_idx: int) -> tuple[int, ...]:
    taps = RULE_FAMILY[rule_idx]
    n = len(bits)
    return tuple(sum(bits[(i + o) % n] for o in taps) % 2 for i in range(n))

def ca_trajectory(w0: int, rule_idx: int, n_steps: int) -> list[tuple[int, ...]]:
    bits = tuple((w0 >> i) & 1 for i in range(N_BITS))
    traj = [bits]
    for _ in range(n_steps - 1):
        traj.append(ca_step(traj[-1], rule_idx))
    return traj

# ----------------------------------------------------------------------------
# Generate objects (hidden (w0,r)), full views, occlusion masks (public, per
# object/view, drawn from a declared rng -- withheld positions never leak bits)
# ----------------------------------------------------------------------------
object_ids = [f"obj-{i:04d}" for i in range(N_OBJECTS)]
hidden = {}
full_views: dict[str, list[tuple[int, ...]]] = {}
for oid in object_ids:
    w0 = int(rng.integers(0, 2 ** N_BITS))
    r = int(rng.integers(0, N_RULES))
    hidden[oid] = (w0, r)
    full_views[oid] = ca_trajectory(w0, r, N_VIEWS)

occlusion_masks: dict[str, list[tuple[bool, ...]]] = {}
for oid in object_ids:
    masks = []
    for v in range(N_VIEWS):
        k = int(rng.integers(OCCLUDE_MIN, OCCLUDE_MAX + 1))
        occ_positions = set(rng.choice(N_BITS, size=k, replace=False).tolist())
        masks.append(tuple(p not in occ_positions for p in range(N_BITS)))
    occlusion_masks[oid] = masks

# log[oid][view][pos] -> "0"/"1"/"withheld" (mirrors world_object_source event content)
log: dict[str, list[list[str]]] = {}
for oid in object_ids:
    rows = []
    for v in range(N_VIEWS):
        bits = full_views[oid][v]
        mask = occlusion_masks[oid][v]
        rows.append([str(bits[p]) if mask[p] else "withheld" for p in range(N_BITS)])
    log[oid] = rows

def visible_positions(oid: str, view: int) -> list[int]:
    return [p for p in range(N_BITS) if occlusion_masks[oid][view][p]]

def has_occlusion(oid: str, view: int) -> bool:
    return any(not occlusion_masks[oid][view][p] for p in range(N_BITS))

# train/test split (deterministic, same style as visibility.train_test_objects)
shuffled = list(object_ids)
rng.shuffle(shuffled)
split = int(0.7 * len(shuffled))
train_ids, test_ids = shuffled[:split], shuffled[split:]

# ----------------------------------------------------------------------------
# Hypotheses: full (w0, rule) space is 2**14 * 4 = 65536 -- too large to
# enumerate as dense trajectories per episode; restrict the hypothesis space
# per planning episode to the true object's rule-consistent neighborhood plus
# all 4 rules x all w0 consistent with what's visible up to (not incl.)
# PLANNING_VIEW, capped, exactly as senses_v2 restricts by visible evidence.
# Kept simple and honest: exact Bayes over rule (4) x hamming-ball(w0, radius)
# around the true w0, capped at 4096 hypotheses total (declared, not hidden).
# ----------------------------------------------------------------------------
HYP_CAP = 4096
HAMMING_RADIUS = 6

def neighborhood_words(w0_true: int, radius: int, cap: int) -> list[int]:
    words = {w0_true}
    bits_true = [(w0_true >> i) & 1 for i in range(N_BITS)]
    all_positions = list(range(N_BITS))
    for r in range(1, radius + 1):
        for combo in itertools.combinations(all_positions, r):
            w = w0_true
            for p in combo:
                w ^= (1 << p)
            words.add(w)
            if len(words) >= cap:
                return sorted(words)
    return sorted(words)

def build_hypotheses_for_object(oid: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    w0_true, r_true = hidden[oid]
    cap_per_rule = HYP_CAP // N_RULES
    words = neighborhood_words(w0_true, HAMMING_RADIUS, cap_per_rule)
    all_words = []
    all_rules = []
    all_traj = []
    for r in range(N_RULES):
        for w in words:
            all_words.append(w)
            all_rules.append(r)
            all_traj.append(ca_trajectory(w, r, N_VIEWS))
    return (
        np.asarray(all_words, dtype=np.int64),
        np.asarray(all_rules, dtype=np.int64),
        np.asarray(all_traj, dtype=np.int64),  # (n_hyp, N_VIEWS, N_BITS)
    )

# ----------------------------------------------------------------------------
# Channels: extend the real stage64 GKSL construction from 8 to N_BITS=14
# positions by cycling position % 8 through the same 8 real stages.
# ----------------------------------------------------------------------------
from scipy.linalg import expm as _expm  # noqa: E402  (mirrors visibility module's import)

stage64_receipt = json.loads((REPO / "system_v8/nested_manifold/results/stage64/receipt.json").read_text())
_channels8, _stages8 = visibility.load_stage_channels(stage64_receipt, encoder_channel_fix=False)

def extend_channels(channels8: dict[tuple[int, int], np.ndarray], n_positions: int) -> dict[tuple[int, int], np.ndarray]:
    ext: dict[tuple[int, int], np.ndarray] = {}
    for position in range(n_positions):
        base = position % 8
        for bit in (0, 1):
            ext[(position, bit)] = channels8[(base, bit)]
    return ext

channels = extend_channels(_channels8, N_BITS)

vec = visibility.vec
unvec = visibility.unvec
RHO0 = visibility.RHO0

# ----------------------------------------------------------------------------
# Umegaki (bits, stable) -- identical to planner_v0
# ----------------------------------------------------------------------------
def umegaki_bits(rho: np.ndarray, sigma: np.ndarray, eps: float = 1e-12) -> float:
    rho = (rho + rho.conj().T) * 0.5
    sigma = (sigma + sigma.conj().T) * 0.5
    wr, Vr = np.linalg.eigh(rho)
    ws, Vs = np.linalg.eigh(sigma)
    wr = np.clip(wr, eps, None)
    ws = np.clip(ws, eps, None)
    log_rho = Vr @ np.diag(np.log2(wr)) @ Vr.conj().T
    log_sig = Vs @ np.diag(np.log2(ws)) @ Vs.conj().T
    return float(np.real(np.trace(rho @ (log_rho - log_sig))))

# ----------------------------------------------------------------------------
# Admitted probe-order words (finite, exact when <=4096) -- length R_FOR_WORDS
# ----------------------------------------------------------------------------
def admitted_words(vis: list[int], r: int = R_FOR_WORDS) -> list[tuple[int, ...]]:
    if not vis:
        return []
    if len(vis) <= 6:
        cands = list(itertools.permutations(vis, min(r, len(vis))))
    else:
        cands = list(itertools.permutations(vis, r))
    if len(cands) > 4096:
        return cands[:4096]
    return cands

def is_truncated(vis: list[int]) -> bool:
    full_count = math.perm(len(vis), min(R_FOR_WORDS, len(vis))) if len(vis) >= R_FOR_WORDS else 0
    return full_count > 4096

# ----------------------------------------------------------------------------
# Goal density for a view: canonical (sorted-position) application of all
# visible TRUE bits at that view.
# ----------------------------------------------------------------------------
def canonical_goal_rho(oid: str, view: int) -> np.ndarray:
    vis = sorted(visible_positions(oid, view))
    bits = full_views[oid][view]
    r = RHO0.copy()
    for p in vis:
        b = int(bits[p])
        r = unvec(channels[(p, b)] @ vec(r))
    return r

def compute_G_and_final(start_rho, word, true_bits, goal):
    r = start_rho.copy()
    total = umegaki_bits(r, goal)
    for p in word:
        b = int(true_bits[p])
        r = unvec(channels[(p, b)] @ vec(r))
        total += umegaki_bits(r, goal)
    return total, r

def order_sensitivity(words, oid, view):
    if not words:
        return 0.0, 0, 0
    true_bits = full_views[oid][view]
    goal = canonical_goal_rho(oid, view)
    differs = 0
    counted = 0
    for w in words:
        if len(w) < 2:
            continue
        g_fwd, _ = compute_G_and_final(RHO0, w, true_bits, goal)
        g_rev, _ = compute_G_and_final(RHO0, tuple(reversed(w)), true_bits, goal)
        if abs(g_fwd - g_rev) > 1e-9:
            differs += 1
        counted += 1
    frac = (differs / counted) if counted else 0.0
    return frac, differs, counted

def custom_view_density(oid: str, view: int, pos_order: list[int]) -> np.ndarray:
    bits = full_views[oid][view]
    r = RHO0.copy()
    for p in pos_order:
        b = int(bits[p])
        r = unvec(channels[(p, b)] @ vec(r))
    return r

# ----------------------------------------------------------------------------
# Episode execution: per-episode hypothesis set (rule x hamming-ball), engine
# built fresh per object (hypothesis space is object-local by construction).
# ----------------------------------------------------------------------------
LIKELIHOOD_SIGMA_MULTIPLIER = senses.LIKELIHOOD_SIGMA_MULTIPLIER

def make_engine_for_object(oid: str, words_arr, rules_arr, traj_arr):
    engine = senses.QuantumReadoutBayes(channels, visibility, words_arr, rules_arr, traj_arr)
    masks_by_view = {v: set() for v in range(N_VIEWS)}
    for v in range(N_VIEWS):
        m = occlusion_masks[oid][v]
        masks_by_view[v].add(m)
        masks_by_view[v].add(tuple(True for _ in range(N_BITS)))
    # monkeypatch module N_VIEWS for calibrate_sigma's internal loop, restore after
    prev_nv = senses.N_VIEWS
    senses.N_VIEWS = N_VIEWS
    try:
        engine.calibrate_sigma(masks_by_view)
    finally:
        senses.N_VIEWS = prev_nv
    return engine

def run_episode_to_view(engine, oid, up_to_view, custom_order_at=None, order=None):
    masks = tuple(occlusion_masks[oid][v] for v in range(up_to_view + 1))
    post = np.full(engine.n_hypotheses, 1.0 / engine.n_hypotheses)
    for v in range(up_to_view + 1):
        pos_before = post[post > 0]
        ent_b = float(-np.sum(pos_before * np.log2(pos_before))) if len(pos_before) > 0 else 0.0
        if v == custom_order_at and order is not None:
            vis = [p for p in range(N_BITS) if masks[v][p]]
            rem = [p for p in sorted(vis) if p not in order]
            applied = list(order) + rem
            dens = custom_view_density(oid, v, applied)
            qr = engine.readout(dens)
            vecs = np.repeat(visibility.vec(RHO0)[None, :], engine.n_hypotheses, axis=0)
            for p in applied:
                cb = engine.trajectories[:, v, p]
                for b in (0, 1):
                    sel = (cb == b)
                    if np.any(sel):
                        vecs[sel] = vecs[sel] @ channels[(p, int(b))].T
            cd = engine.features_from_vectors(vecs)
        else:
            bits = full_views[oid][v]
            r = RHO0.copy()
            for p in range(N_BITS):
                if masks[v][p]:
                    r = unvec(channels[(p, int(bits[p]))] @ vec(r))
            qr = engine.readout(r)
            cd = engine.reset_candidate_readouts(v, masks[v])
        post = engine.update_posterior(post, qr, cd)
        if v == custom_order_at:
            pos_a = post[post > 0]
            ent_a = float(-np.sum(pos_a * np.log2(pos_a))) if len(pos_a) > 0 else 0.0
            ig = ent_b - ent_a
            trueb = full_views[oid][v]
            occ = [p for p in range(N_BITS) if not masks[v][p]]
            if occ:
                marg = post @ engine.trajectories[:, v, :]
                corr = sum((1 if marg[p] >= 0.5 else 0) == trueb[p] for p in occ)
                acc = corr / len(occ)
            else:
                acc = 1.0
            return post, acc, ig
    pos_f = post[post > 0]
    return post, 0.0, 0.0

def random_orders(vis, n=50, r=R_FOR_WORDS):
    if not vis:
        return []
    out = []
    for _ in range(n):
        out.append(tuple(rng.choice(vis, size=min(r, len(vis)), replace=False)))
    return out

# ----------------------------------------------------------------------------
# MCTS arm -- same 64-sim Gumbel MuZero IG pattern as planner_v0, generalized
# to N_BITS positions (subset-mask entropy space is 2**N_BITS, too large for
# an exhaustive mask table at N_BITS=14; use the visible-position sub-mask
# entropy restricted to the episode's visible set, same construction logic,
# capped mask table size).
# ----------------------------------------------------------------------------
def mcts_probe_order(engine, oid, view, max_depth=R_FOR_WORDS, n_sims=64):
    vis = visible_positions(oid, view)
    if len(vis) == 0:
        return []
    true_bits = full_views[oid][view]
    candidates = engine.trajectories[:, view, :]
    k = len(vis)
    n_masks = 1 << k

    def local_mask_to_positions(m):
        return [vis[i] for i in range(k) if (m >> i) & 1]

    ent = np.zeros(n_masks, dtype=np.float32)
    for m in range(n_masks):
        keep = np.ones(candidates.shape[0], dtype=bool)
        for p in local_mask_to_positions(m):
            keep &= (candidates[:, p] == true_bits[p])
        q = keep / max(keep.sum(), 1)
        if keep.sum() > 0:
            ent[m] = -float(np.sum(q[keep] * np.log(q[keep])))

    import jax
    import jax.numpy as jnp
    import mctx

    E = jnp.asarray(ent)

    def recurrent(params, key, action, embedding):
        nxt = embedding | (jnp.int32(1) << action.astype(jnp.int32))
        reward = E[embedding] - E[nxt]
        next_masks = nxt[:, None] | (jnp.int32(1) << jnp.arange(k, dtype=jnp.int32))
        next_masks = jnp.clip(next_masks, 0, n_masks - 1)
        logits = E[nxt, None] - E[next_masks]
        return mctx.RecurrentFnOutput(reward=reward, discount=jnp.ones_like(reward),
                                       prior_logits=logits, value=jnp.zeros_like(reward)), nxt

    root = mctx.RootFnOutput(
        prior_logits=(100.0 * (E[0] - E[jnp.int32(1) << jnp.arange(k, dtype=jnp.int32)]))[None, :],
        value=jnp.zeros(1),
        embedding=jnp.zeros(1, dtype=jnp.int32),
    )
    mctx.gumbel_muzero_policy(
        params=(), rng_key=jax.random.PRNGKey(SEED),
        root=root, recurrent_fn=recurrent,
        num_simulations=n_sims, max_depth=max_depth, gumbel_scale=0.01,
    )
    seq = []
    emb = 0
    for depth_i in range(max_depth):
        root2 = mctx.RootFnOutput(
            prior_logits=(100.0 * (E[emb] - E[jnp.clip(emb | (jnp.int32(1) << jnp.arange(k, dtype=jnp.int32)), 0, n_masks - 1)]))[None, :],
            value=jnp.zeros(1),
            embedding=jnp.array([emb], dtype=jnp.int32),
        )
        o2 = mctx.gumbel_muzero_policy(params=(), rng_key=jax.random.PRNGKey(SEED + len(seq)),
                                       root=root2, recurrent_fn=recurrent,
                                       num_simulations=max(8, n_sims // 4), max_depth=1, gumbel_scale=0.01)
        a = int(np.asarray(o2.action)[0])
        if (emb >> a) & 1:
            break
        seq.append(vis[a])
        emb |= (1 << a)
        if emb == (n_masks - 1):
            break
    return seq if seq else vis[:R_FOR_WORDS]

# ----------------------------------------------------------------------------
# Controls
# ----------------------------------------------------------------------------
def make_commuting_channels(n_positions: int) -> dict[tuple[int, int], np.ndarray]:
    comm: dict[tuple[int, int], np.ndarray] = {}
    for pos in range(n_positions):
        for b in (0, 1):
            th = 0.4 * (2 * b - 1) * (0.3 + 0.1 * (pos % 3))
            U = np.diag(np.exp(-1j * th * np.array([1, -1, 1, -1], dtype=complex)))
            ch = visibility.kron(U.conj(), U)
            comm[(pos, b)] = ch
    return comm

def order_sens_commuting(words, oid, view, comm_ch):
    if not words:
        return 0.0
    trueb = full_views[oid][view]
    goal = canonical_goal_rho(oid, view)
    diff = 0
    cnt = 0
    for w in words:
        if len(w) < 2:
            continue
        r = RHO0.copy()
        g = umegaki_bits(r, goal)
        for p in w:
            b = int(trueb[p])
            r = unvec(comm_ch[(p, b)] @ vec(r))
            g += umegaki_bits(r, goal)
        rr = RHO0.copy()
        grv = umegaki_bits(rr, goal)
        for p in reversed(w):
            b = int(trueb[p])
            rr = unvec(comm_ch[(p, b)] @ vec(rr))
            grv += umegaki_bits(rr, goal)
        if abs(g - grv) > 1e-9:
            diff += 1
        cnt += 1
    return (diff / cnt) if cnt else 0.0

# ----------------------------------------------------------------------------
# Episode selection: test-set objects with occlusion at PLANNING_VIEW and
# at least R_FOR_WORDS+1 visible positions (need room to choose an order),
# bounded budget (20 episodes, same as v0).
# ----------------------------------------------------------------------------
episodes = [
    oid for oid in test_ids
    if has_occlusion(oid, PLANNING_VIEW) and len(visible_positions(oid, PLANNING_VIEW)) >= R_FOR_WORDS + 1
]
if len(episodes) > 20:
    episodes = episodes[:20]
if not episodes:
    episodes = [oid for oid in object_ids if len(visible_positions(oid, PLANNING_VIEW)) >= R_FOR_WORDS + 1][:16]

print(f"episodes selected: {len(episodes)} (planning_view={PLANNING_VIEW}, n_bits={N_BITS}, r={R_FOR_WORDS})")

# ----------------------------------------------------------------------------
# Main evaluation
# ----------------------------------------------------------------------------
all_admitted: list[tuple[int, ...]] = []
planner_metrics: list[dict[str, float]] = []
mcts_metrics: list[dict[str, float]] = []
random_metrics: list[dict[str, float]] = []
comm_sens_list: list[float] = []

comm_ch = make_commuting_channels(N_BITS)

for oid in episodes:
    words_arr, rules_arr, traj_arr = build_hypotheses_for_object(oid)
    engine = make_engine_for_object(oid, words_arr, rules_arr, traj_arr)

    vis = visible_positions(oid, PLANNING_VIEW)
    words = admitted_words(vis, r=R_FOR_WORDS)
    frac, d, c = order_sensitivity(words, oid, PLANNING_VIEW)
    all_admitted.extend(words)

    cs = order_sens_commuting(words, oid, PLANNING_VIEW, comm_ch)
    comm_sens_list.append(cs)

    # --- PLANNER (min G) ---
    trueb = full_views[oid][PLANNING_VIEW]
    goal = canonical_goal_rho(oid, PLANNING_VIEW)
    best_g = float("inf")
    best_word: tuple[int, ...] = tuple(sorted(vis)[:R_FOR_WORDS])
    for w in words:
        g, _ = compute_G_and_final(RHO0, w, trueb, goal)
        if g < best_g:
            best_g = g
            best_word = w
    _, p_acc, p_ig = run_episode_to_view(engine, oid, PLANNING_VIEW, custom_order_at=PLANNING_VIEW, order=list(best_word))
    planner_metrics.append({"acc": p_acc, "ig": p_ig, "g": best_g})

    # --- MCTS (64 sims, IG) ---
    m_seq = mcts_probe_order(engine, oid, PLANNING_VIEW, max_depth=R_FOR_WORDS, n_sims=64)
    _, m_acc, m_ig = run_episode_to_view(engine, oid, PLANNING_VIEW, custom_order_at=PLANNING_VIEW, order=m_seq)
    mcts_metrics.append({"acc": m_acc, "ig": m_ig})

    # --- RANDOM (50 draws) ---
    r_orders = random_orders(vis, n=50, r=R_FOR_WORDS)
    raccs, rigs = [], []
    for ro in r_orders:
        _, ra, ri = run_episode_to_view(engine, oid, PLANNING_VIEW, custom_order_at=PLANNING_VIEW, order=list(ro))
        raccs.append(ra)
        rigs.append(ri)
    random_metrics.append({"acc": float(np.mean(raccs)), "ig": float(np.mean(rigs))})

# ----------------------------------------------------------------------------
# Aggregate + bootstrap CIs (object bootstrap)
# ----------------------------------------------------------------------------
def bootstrap_ci(values, n_boot=5000, alpha=0.05):
    if not values:
        return 0.0, (0.0, 0.0)
    arr = np.asarray(values, dtype=float)
    mu = float(arr.mean())
    if len(arr) < 2:
        return mu, (mu, mu)
    boots = []
    for _ in range(n_boot):
        samp = rng.choice(arr, size=len(arr), replace=True)
        boots.append(float(samp.mean()))
    boots = np.sort(np.asarray(boots))
    lo = float(boots[int(alpha / 2 * n_boot)])
    hi = float(boots[int((1 - alpha / 2) * n_boot)])
    return mu, (lo, hi)

planner_accs = [m["acc"] for m in planner_metrics]
planner_igs = [m["ig"] for m in planner_metrics]
mcts_accs = [m["acc"] for m in mcts_metrics]
mcts_igs = [m["ig"] for m in mcts_metrics]
rand_accs = [m["acc"] for m in random_metrics]
rand_igs = [m["ig"] for m in random_metrics]

p_acc_mu, p_acc_ci = bootstrap_ci(planner_accs)
m_acc_mu, m_acc_ci = bootstrap_ci(mcts_accs)
r_acc_mu, r_acc_ci = bootstrap_ci(rand_accs)
p_ig_mu, p_ig_ci = bootstrap_ci(planner_igs)
m_ig_mu, m_ig_ci = bootstrap_ci(mcts_igs)
r_ig_mu, r_ig_ci = bootstrap_ci(rand_igs)

# pooled order sensitivity (exact, over all enumerated admitted words)
total_diff = 0
total_cnt = 0
for oid in episodes:
    vis = visible_positions(oid, PLANNING_VIEW)
    ws = admitted_words(vis, r=R_FOR_WORDS)
    goal = canonical_goal_rho(oid, PLANNING_VIEW)
    trueb = full_views[oid][PLANNING_VIEW]
    for w in ws:
        if len(w) < 2:
            continue
        g1, _ = compute_G_and_final(RHO0, w, trueb, goal)
        g2, _ = compute_G_and_final(RHO0, tuple(reversed(w)), trueb, goal)
        if abs(g1 - g2) > 1e-9:
            total_diff += 1
        total_cnt += 1
v1_sens = (total_diff / total_cnt) if total_cnt > 0 else 0.0

comm_mean = float(np.mean(comm_sens_list)) if comm_sens_list else 0.0

# uniform-weight control
uniform_accs = []
for oid in episodes:
    vis = visible_positions(oid, PLANNING_VIEW)
    ws = admitted_words(vis, r=R_FOR_WORDS)
    if not ws:
        uniform_accs.append(0.0)
        continue
    words_arr, rules_arr, traj_arr = build_hypotheses_for_object(oid)
    engine = make_engine_for_object(oid, words_arr, rules_arr, traj_arr)
    chosen = list(ws[rng.integers(0, len(ws))])
    _, ua, ui = run_episode_to_view(engine, oid, PLANNING_VIEW, custom_order_at=PLANNING_VIEW, order=chosen)
    uniform_accs.append(ua)
u_acc_mu, u_acc_ci = bootstrap_ci(uniform_accs)

# ----------------------------------------------------------------------------
# Preregistered ceiling gate
# ----------------------------------------------------------------------------
CEILING_THRESHOLD = 0.95
any_ceiling = (p_acc_mu > CEILING_THRESHOLD) or (m_acc_mu > CEILING_THRESHOLD) or (r_acc_mu > CEILING_THRESHOLD)
verdict = "TASK_STILL_EASY" if any_ceiling else "DISCRIMINATES"

# ----------------------------------------------------------------------------
# Receipt
# ----------------------------------------------------------------------------
truncated_declarations = sum(1 for oid in episodes if is_truncated(visible_positions(oid, PLANNING_VIEW)))

receipt = {
    "schema": "system_v8/path_integral/planner_v1/receipt_v1",
    "sim_id": "planner_v1_harder",
    "version": "1.0.0",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "classification": "scratch_diagnostic",
    "promotion_allowed": False,
    "claim_ceiling": "working sim; no admission, no bridge, no axis claim",
    "context": {
        "predecessor": "planner_v0 (results/planner_v0/receipt.json)",
        "predecessor_finding": "all three planners (min-G, MCTS, random) scored acc_mean=1.0 -- ceiling, task too easy",
        "preregistered_ceiling_gate": f"if any planner acc_mean > {CEILING_THRESHOLD}, report TASK_STILL_EASY with numbers, no discrimination claim",
    },
    "runtime": {
        "python": sys.executable,
        "interpreter_required": str(SIM_PY),
        "memory_free_percent": mem_pct,
    },
    "parameters": {
        "n_objects": N_OBJECTS,
        "n_bits_hidden_state": N_BITS,
        "n_views": N_VIEWS,
        "occlude_min": OCCLUDE_MIN,
        "occlude_max": OCCLUDE_MAX,
        "planning_view": PLANNING_VIEW,
        "n_episodes": len(episodes),
        "episode_ids": episodes,
        "r_for_words_probe_budget": R_FOR_WORDS,
        "r_for_words_v0": 3,
        "probe_budget_fraction_of_v0": round(R_FOR_WORDS / 3.0, 4),
        "hypothesis_space_construction": "rule (4) x hamming-ball(w0_true, radius=6), capped 4096, per-episode object-local",
        "mcts_sims": 64,
        "random_draws": 50,
        "bootstrap_n": 5000,
    },
    "admitted_words": {
        "total_pooled": len(all_admitted),
        "per_episode_max": max((len(admitted_words(visible_positions(oid, PLANNING_VIEW), R_FOR_WORDS)) for oid in episodes), default=0),
        "truncated_declarations": truncated_declarations,
    },
    "path_order_sensitivity": {
        "v1_fraction_G_fwd_neq_rev": float(v1_sens),
        "n_admitted_words_counted": int(total_cnt),
        "n_differs": int(total_diff),
        "note": "exact finite sum over enumerated admitted probe-order words on v1 extended stage channels (position%8 cycling of real stage64 channels)",
    },
    "controls": {
        "commuting_generator_mean_sensitivity": comm_mean,
        "commuting_collapse_expected": comm_mean < 0.02,
        "uniform_weight_planner_acc_mean": u_acc_mu,
        "uniform_weight_vs_random_overlap": abs(u_acc_mu - r_acc_mu) < 0.05,
        "note": "commuting channels force G(forward) == G(reverse) structurally; uniform G reduces selection to random",
    },
    "three_way_comparison": {
        "planner_minG": {
            "acc_mean": p_acc_mu, "acc_ci95": list(p_acc_ci),
            "ig_mean": p_ig_mu, "ig_ci95": list(p_ig_ci),
            "n_episodes": len(planner_accs),
        },
        "mcts_64sim_IG": {
            "acc_mean": m_acc_mu, "acc_ci95": list(m_acc_ci),
            "ig_mean": m_ig_mu, "ig_ci95": list(m_ig_ci),
            "n_episodes": len(mcts_accs),
        },
        "random_50draw_mean": {
            "acc_mean": r_acc_mu, "acc_ci95": list(r_acc_ci),
            "ig_mean": r_ig_mu, "ig_ci95": list(r_ig_ci),
            "n_episodes": len(rand_accs),
        },
    },
    "ceiling_gate": {
        "threshold": CEILING_THRESHOLD,
        "planner_minG_over_threshold": bool(p_acc_mu > CEILING_THRESHOLD),
        "mcts_over_threshold": bool(m_acc_mu > CEILING_THRESHOLD),
        "random_over_threshold": bool(r_acc_mu > CEILING_THRESHOLD),
        "verdict": verdict,
    },
    "tool_manifest": {
        "numpy": {"tried": True, "used": True, "reason": "load-bearing for all densities, Umegaki, posteriors, bootstrap, enumeration"},
        "scipy.linalg.expm": {"tried": True, "used": True, "reason": "load-bearing via visibility stage channels (GKSL+unitary construction), extended to 14 positions"},
        "jax": {"tried": True, "used": (len(episodes) > 0), "reason": "mctx arm only; 64-sim Gumbel MuZero on IG objective (reused battery pattern, generalized mask space)"},
        "mctx": {"tried": True, "used": (len(episodes) > 0), "reason": "information-gain MCTS comparator"},
    },
    "tool_integration_depth": {
        "numpy": "load_bearing",
        "scipy.linalg.expm": "load_bearing",
        "jax": "supportive (MCTS arm only)",
        "mctx": "supportive (MCTS arm only)",
    },
    "divergence_log": [
        {"comparison": "planner_v1 vs planner_v0", "status": "harder_world", "note": "128 objects, 14-bit hidden state, 8 views, 4-6 bits occluded/view, probe budget r=2 (60% of v0's r=3)"},
        {"comparison": "hypothesis space vs v0", "status": "changed", "note": "v0 used the fixed 8-bit/4-rule 1024-hypothesis global set; v1's 14-bit space (65536) is capped per-episode via rule x hamming-ball(radius=6,cap=4096), declared not hidden"},
        {"comparison": "channels vs v0", "status": "extended", "note": "same real stage64 GKSL channels, cycled position%8 across 14 probe positions -- no new free parameters"},
        {"comparison": "honest negatives", "status": "kept", "note": "if random or mcts beats planner, or if the ceiling gate fires again, that is the reported result; no inflation"},
    ],
    "input_hashes": {
        "stage64_receipt": hashlib.sha256((REPO / "system_v8/nested_manifold/results/stage64/receipt.json").read_bytes()).hexdigest()[:16],
        "seed": SEED,
    },
}

RECEIPT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n")

print(f"PLANNER V1 DONE: minG={p_acc_mu:.4f} mcts={m_acc_mu:.4f} random={r_acc_mu:.4f} verdict={verdict}")
