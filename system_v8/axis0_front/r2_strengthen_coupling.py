#!/usr/bin/env python3
"""
AXIS0 R2 -- drive-through-the-entangling-generator strengthening attempt.

Authority: system_v8/axis0_front/AXIS0_FRONT_OBJECT_CARD_v0.md (S9, S14, GAP-1..GAP-3).
Owner doctrine (memory note user_entanglement_central_conditional_entropy_gradient.md,
2026-07-19/20, verbatim): "entanglement is central to this model!!!"; negative
conditional entropy S(A|B) is a resource witness, not a pathology. The task framing:
drive->quantum-cut coupling is the weakest genuinely-open item in the model.

MEASURED PRIOR STATE (read from the receipts on disk before this file was written;
every number below is cited, not recalled):

  1. scalar-rate (system_v8/nested_manifold/manifold_one.py, gamma_t =
     GAMMA_BASE*drive/log4 applied to LOCAL per-sheet jump operators only):
     drive_correlations dS_L=0.0155, dS_LR=0.0188, dPhi0=-0.0359
     (system_v8/nested_manifold/results/manifold_one/receipt.json). Re-measured in
     system_v8/unified/results/manifold_unified_v2/receipt.json layer_computations.L09:
     baseline_rms_correlation=0.0598, shuffled_rms_correlation=0.0373, signal_floor=0.2
     -- the baseline never reaches the floor regardless of the shuffle ratio
     (checks.k2_shuffled_drive_collapses_independent_observables=false).
  2. history-weights depth<=2 over LOCAL/PRODUCT Kraus words
     (system_v8/axis0_front/r1_history_weight_coupling.py): best candidate
     (W3_growth) rms_cut_correlation=0.04446 vs scalar baseline 0.04358 (no real
     improvement); ITS OWN shuffled-drive control gives rms=0.16167 -- the shuffle
     is LARGER than the real signal (system_v8/axis0_front/results/r1/receipt.json
     summary).
  3. gradient-tournament (10 independent gradient candidates x 3 event classes,
     system_v8/axis0_front/gradient_tournament_v0.py):
     best_per_event_class.stage_transition=null -- no candidate beats the shuffle
     null on the quantum-sensitive event proxy
     (system_v8/axis0_front/results/gradient_tournament_v0/receipt.json findings[1]).
  4. coherent-information ladder (system_v8/entanglement_gradient/
     coherent_information_ladder_v0.py -- found while reading the owner's
     entanglement-central doctrine note; not one of the three the task named, but
     directly relevant prior art): drive vs I(A>B)-growth correlation=-0.1288,
     shuffled=-0.0567, both_below_0.2=true -- its P6 control passes on the "both
     already small" branch, not a real collapse
     (system_v8/entanglement_gradient/results/coherent_information_ladder_v0/
     receipt.json data). That probe changed only the READOUT (added S(A|B) on a
     nested cut ladder); it kept the SAME scalar-rate coupling mechanism as (1),
     and had to recalibrate the coherent exchange term from J_XY=0.35 (manifold_
     one's value, which "does not cross the entanglement threshold") to a fixed,
     drive-BLIND J_COUPLE=2.0 just to make its own entangling apparatus fire at all.

WHAT NO PRIOR ATTEMPT HAS DONE: every Kraus branch the drive has ever been
weighted onto -- (1)'s bank_jumps generators, (2)'s depth<=2 words built from
them, (4)'s unchanged bank_jumps again -- is a LOCAL per-sheet operator
(kron(s,I2) or kron(I2,s)) or a PRODUCT of two such operators (kron(s,s')). A
mixture of local/product-form Kraus branches is a separable (LOCC-type) map: by
construction it cannot send a product state to an entangled one, branch by
branch (this is checkable directly: (A tensor B)|psi_L>|psi_R> = (A|psi_L>)
tensor (B|psi_R>), still a product ket, for every branch in (1),(2),(4)). The
only genuinely entangling term anywhere in this machinery is the COHERENT J_XY
exchange inside build_joint_h, and the drive has never touched it either.

DESIGN CHOICE, stated before any number was seen: modulating the coherent J_XY
term's strength by drive (J_XY_eff = J_XY_base * f(drive)) was considered and
REJECTED -- that is structurally identical to the already-falsified scalar-rate
stand-in from (1), just renamed to a different generator; it would not test the
doc's S9 w_h mechanism, it would just re-run negative (1) under a new label.
Instead this file adds a genuinely entangling COLLECTIVE dissipative generator
-- E_plus, E_minus = (SM_q0 +/- SM_q1)/sqrt(2), the textbook collective-decay /
dissipation-driven-entanglement construction (collective spontaneous emission;
Plenio & Huelga, PRL 88, 197901 (2002), "Entangled light from white noise", is
the standard citation for dissipation building entanglement through a shared,
non-product jump operator) -- to the SAME depth<=2 branch alphabet r1 already
built and audited, and lets the DRIVE control ONLY that new branch's WEIGHT via
the doc's own S9 slot (rho' = sum_h w_h K_h rho K_h^dagger), never as a scalar
rate multiplier on a single generator (the object card's G-drive-slot gate).

Proof the new branch is genuinely non-separable (checked here, not asserted):
(SM_q0+SM_q1) applied to the two-qubit ket |1,1> gives SM|1> x |1> + |1> x SM|1>
= |0,1> + |1,0>, an entangled (Bell-type) superposition from a product input --
no product-form operator (A tensor B) can do that from a product ket. This is
the one mechanism class no prior receipt in this lane exercised.

CANDIDATES (drive enters ONLY in W6; K_ENT fixed a priori, not fit to output):
  W5_scalar_baseline      -- reproduced fresh from manifold_one/r1 (unchanged);
                             same-run reference number + the qutip-referee substrate.
  W6_entangling_drive     -- raw[id]=raw[local depth1]=raw[local depth2]=1.0
                             (flat, drive-blind); raw[E_plus]=raw[E_minus]=
                             exp(drive*K_ENT), K_ENT=1.0 (matches the per-
                             distinction exponent scale W1_capacity already used
                             in r1 for its nd=1 branches; not searched here).
                             w = raw / sum(raw). THE new coupling under test.
  W7_entangling_uniform   -- same extended alphabet, weights uniform and
                             drive-BLIND. Ablation: isolates "does having the
                             branch at all matter" from "does drive->branch-
                             weight matter".
  product_no_entanglement_cut control (S38): NOT re-run here -- it is exactly
  r1's own W1/W2/W3 numbers (rms 0.033-0.045, all near/below the scalar
  baseline and below their own shuffle nulls); this file differs from r1 ONLY
  by adding E_plus/E_minus to the branch alphabet, so r1's existing receipt
  already IS that control. Cited in the summary, not recomputed.

PRE-REGISTERED VERDICT RULE (fixed before this file was run):
  "strengthened" requires ALL THREE:
    (a) w6_rms_cut_correlation > scalar_baseline_rms_cut_correlation
    (b) w6_rms_cut_correlation > w6_shuffled_rms_cut_correlation (matched shuffle)
    (c) w6_rms_cut_correlation > the 95th percentile of a 30-draw shuffled-drive
        null distribution (not just luckier than one single permutation --
        r1's single shuffle for W3_growth happened to land ABOVE the real
        signal by chance, which is why a one-sample shuffle is weak evidence).
  Otherwise: "still-open" -- an honest negative, reported with exactly which of
  (a)/(b)/(c) held and which did not. K_ENT, the branch set, and the drive
  series are NOT adjusted after seeing results.

30+ ticks (35, matching r1/manifold_one's exact drive series for direct
comparability). Independent panel + cut panel take rho only -- drive never
appears inside a readout definition. Shuffled-drive control: matched single
permutation (seed 20260720, same convention as r1/L09) PLUS the 30-draw null.
qutip referee: 2 spot ticks (owner-specified count), cross-checking the
W5_scalar_baseline reproduction only -- W6/W7 are weighted-branch mixtures with
post-hoc trace renormalization, not standard Lindblad channels, so there is no
mesolve equivalent to referee them against directly (same scope limit r1
recorded for its W1-W3).

Claim ceiling: scratch_diagnostic / tool_lego_fit_probe; promotion_allowed=
false; formal_admission_allowed=false; no layer, no bridge, no Axis-0 physics
claim, no uniqueness claim about K_ENT or the branch set.
Interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
"""

import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# ---------------- interpreter + memory gate (fail-closed, before heavy work) ----
SIM_INTERPRETER = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"


def check_memory_gate(min_available_frac: float = 0.25):
    import psutil
    vm = psutil.virtual_memory()
    avail = vm.available / vm.total
    return {
        "available_frac": float(avail),
        "used_pct": float(vm.percent),
        "threshold": min_available_frac,
        "ok": bool(avail >= min_available_frac),
    }


mem = check_memory_gate(0.25)
if not mem["ok"]:
    HERE = Path(__file__).resolve().parent
    OUT = HERE / "results" / "r2"
    OUT.mkdir(parents=True, exist_ok=True)
    blocked = {
        "schema": "ratchet.v8.axis0_front.r2.blocked",
        "reason": "memory_gate",
        "memory": mem,
        "message": "available system memory < 25% threshold. No sim executed.",
        "promotion_allowed": False,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    (OUT / "blocked_receipt.json").write_text(json.dumps(blocked, indent=2) + "\n")
    print(json.dumps(blocked, indent=2))
    sys.exit(2)

# ---------------- import manifold_one directly (safe: no top-level side effects;
# main() is guarded by __name__ == "__main__"). Do NOT import r1_history_weight_
# coupling.py -- its module-level code runs its OWN memory-gate check with
# sys.exit(2) on failure, which must not be a side effect of importing it from a
# sibling script. Everything reused from r1 below is PORTED (copied verbatim,
# attributed), matching the convention gradient_tournament_v0.py already used.
from system_v8.nested_manifold import manifold_one as m1

BUILD_JOINT_H = m1.build_joint_h
BANK_JUMPS = m1.bank_jumps
GKSL_RHS = m1.gksl_rhs
I2 = m1.I2
SM = m1.SM
TICK_DT = float(m1.TICK_DT)
NSUB = int(m1.NSUB)
GAMMA_BASE = float(m1.GAMMA_BASE)
J_XY_UNCHANGED = float(m1.J_XY)  # recorded, never modulated by drive (design note above)

N_TICKS = 35          # 30+ ticks; matches r1 exactly for direct comparability
DEPTH = 2              # same Kraus-word depth ceiling as r1 (unchanged)
K_ENT = 1.0            # fixed a priori; see header. Not tuned against output.
N_NULL_SHUFFLES = 30
SHUFFLE_SEED = 20260720
SPOT_TICKS = [8, 24]   # 2 qutip spot ticks (owner-specified count), stage 0 and stage 2

# ---------------- ported verbatim from r1_history_weight_coupling.py ------------
# (3-qubit embedding, partial trace, panels, drive series, correlation helpers,
# scalar-rate evolution, qutip spot-check runner). Copied rather than imported
# for the reason stated above; unchanged from r1 so numbers are directly
# comparable to r1's receipt.


def kron3(a, b, c):
    return np.kron(np.kron(a, b), c)


I8 = np.eye(8, dtype=complex)
Z0 = kron3(m1.SZ, I2, I2)
Z1 = kron3(I2, m1.SZ, I2)
Z2 = kron3(I2, I2, m1.SZ)
X0X1 = kron3(m1.SX, m1.SX, I2)
Y1Y2 = kron3(I2, m1.SY, m1.SY)


def embed_4d_to_8d(op4: np.ndarray) -> np.ndarray:
    return np.kron(op4, I2)


def embed_state_4d_to_8d(rho4: np.ndarray) -> np.ndarray:
    rho_third = 0.5 * (I2 + 0.2 * m1.SZ)
    return np.kron(rho4, rho_third)


def pauli_expect_3q(rho8: np.ndarray, pauli8: np.ndarray) -> float:
    return float(np.real(np.trace(rho8 @ pauli8)))


def vn_entropy_bits(rho: np.ndarray) -> float:
    w = np.linalg.eigvalsh(0.5 * (rho + rho.conj().T))
    w = w[w > 1e-14]
    if len(w) == 0:
        return 0.0
    return float(-(w * np.log2(w)).sum())


def purity(rho: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ rho)))


def partial_trace_3q(rho: np.ndarray, keep: list) -> np.ndarray:
    """Ported verbatim from r1 (KEEP_L/MR/LM/R nested-cut naming: the 3-qubit
    chain is (qubit0=L, qubit1=M [the original manifold_one R sheet], qubit2=R
    [the new spectator qubit]); cut1 = L|MR, cut2 = LM|R."""
    r = rho.reshape((2, 2, 2, 2, 2, 2))
    keep = sorted(set(keep))
    if keep == [0]:
        return np.sum(r, axis=(1, 2, 4, 5))
    if keep == [1, 2]:
        return np.sum(r, axis=(0, 3)).reshape(4, 4)
    if keep == [0, 1]:
        return np.sum(r, axis=(2, 5)).reshape(4, 4)
    if keep == [2]:
        return np.sum(r, axis=(0, 1, 3, 4))
    if keep == [0, 1, 2]:
        return rho.copy()
    raise NotImplementedError(f"partial_trace_3q keep={keep} not implemented for R2")


KEEP_L = [0]
KEEP_MR = [1, 2]
KEEP_LM = [0, 1]
KEEP_R = [2]


def cut_observables_3q(rho8: np.ndarray) -> dict:
    S_L = vn_entropy_bits(partial_trace_3q(rho8, KEEP_L))
    S_MR = vn_entropy_bits(partial_trace_3q(rho8, KEEP_MR))
    S_LM = vn_entropy_bits(partial_trace_3q(rho8, KEEP_LM))
    S_R = vn_entropy_bits(partial_trace_3q(rho8, KEEP_R))
    S_full = vn_entropy_bits(rho8)
    S_L_given_MR = S_full - S_MR      # S(A|B) for cut L|MR
    S_MR_given_L = S_full - S_L
    S_LM_given_R = S_full - S_R       # S(A|B) for cut LM|R
    w1, w2 = 0.5, 0.5
    Ic1 = -(S_full - S_MR)
    Ic2 = -(S_full - S_L)
    Phi0_proxy = w1 * Ic1 + w2 * Ic2
    return {
        "S_L": S_L, "S_MR": S_MR, "S_LR": S_full,
        "S_L_given_MR": S_L_given_MR, "S_MR_given_L": S_MR_given_L,
        "S_LM_given_R": S_LM_given_R, "Phi0_proxy": Phi0_proxy,
        "negativity": 0.0,
    }


def fixed_independent_panel(rho8: np.ndarray) -> dict:
    return {
        "purity": purity(rho8),
        "von_neumann_entropy_bits": vn_entropy_bits(rho8),
        "bloch_z_0": pauli_expect_3q(rho8, Z0),
        "bloch_z_1": pauli_expect_3q(rho8, Z1),
        "bloch_z_2": pauli_expect_3q(rho8, Z2),
        "pauli_xx_01": pauli_expect_3q(rho8, X0X1),
        "pauli_yy_12": pauli_expect_3q(rho8, Y1Y2),
    }


def compute_drive_series(n_ticks: int) -> list:
    """Ported verbatim from r1: replicates manifold_one's GROW step exactly,
    independent of manifold_one's own N_TICKS."""
    counts = [1, 1, 1, 0, 0]
    drives = []
    for t in range(n_ticks):
        a = 3 + ((t + 1) % 3)
        old_total = sum(counts)
        new_counts = [0] * 5
        for x in range(a):
            new_counts[x] = old_total - counts[x]
        drives.append(math.log(sum(new_counts)) - math.log(old_total))
        counts = new_counts
    return drives


def build_coherent_tick(dt: float) -> np.ndarray:
    H4 = BUILD_JOINT_H()
    H8 = embed_4d_to_8d(H4)
    U = np.eye(8, dtype=complex) - 1j * H8 * dt - 0.5 * (H8 @ H8) * dt * dt
    return 0.5 * (U + U.conj().T)


def evolve_tick_scalar(rho8: np.ndarray, stage: int, gamma: float) -> np.ndarray:
    H8 = embed_4d_to_8d(BUILD_JOINT_H())
    Ls8 = [embed_4d_to_8d(L) for L in BANK_JUMPS(stage, gamma)]
    dt = TICK_DT / NSUB
    r = rho8.copy()
    for _ in range(NSUB):
        k1 = GKSL_RHS(r, H8, Ls8)
        k2 = GKSL_RHS(r + 0.5 * dt * k1, H8, Ls8)
        k3 = GKSL_RHS(r + 0.5 * dt * k2, H8, Ls8)
        k4 = GKSL_RHS(r + dt * k3, H8, Ls8)
        r = r + (dt / 6.0) * (k1 + 2 * k2 + 2 * k3 + k4)
        r = 0.5 * (r + r.conj().T)
    tr = float(np.real(np.trace(r)))
    if abs(tr) > 1e-14:
        r = r / tr
    return r


def pearson(a: list, b: list) -> float:
    a = np.asarray(a, float)
    b = np.asarray(b, float)
    if a.std() < 1e-12 or b.std() < 1e-12:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def shuffle_series(xs: list, seed: int = SHUFFLE_SEED) -> list:
    rng = random.Random(seed)
    ys = xs[:]
    rng.shuffle(ys)
    return ys


def qutip_spot_checks(selected_states: list) -> list:
    import qutip as qt
    results = []
    for item in selected_states:
        Hq = qt.Qobj(item["H"])
        Lq = [qt.Qobj(L) for L in item["Ls"]]
        rhoq = qt.Qobj(item["rho_before"])
        res = qt.mesolve(Hq, rhoq, [0, item["dt"]], Lq, [])
        rho_after_qt = res.states[-1].full()
        rho_after_qt = 0.5 * (rho_after_qt + rho_after_qt.conj().T)
        tr = float(np.real(np.trace(rho_after_qt)))
        if abs(tr) > 1e-12:
            rho_after_qt = rho_after_qt / tr
        s_qt = vn_entropy_bits(rho_after_qt)
        s_np = vn_entropy_bits(item["np_after"])
        dev = abs(s_qt - s_np)
        results.append({
            "tick": item["tick"], "label": item.get("label", ""),
            "entropy_qt": float(s_qt), "entropy_np": float(s_np),
            "abs_dev": float(dev), "pass_1e5": bool(dev < 1e-5),
        })
    return results


# ---------------- NEW: the entangling / collective branch (r1 never built this) --
# Acts on qubits 0,1 -- the original manifold_one (L,R) sheet pair that every
# existing operator here already embeds via kron(op4, I2); qubit 2 (the nested-
# cut spectator) is left untouched, exactly like every other branch in this file.
SM_Q0 = kron3(SM, I2, I2)
SM_Q1 = kron3(I2, SM, I2)
E_PLUS_BASE = (SM_Q0 + SM_Q1) / math.sqrt(2.0)   # collective/"bright" combination
E_MINUS_BASE = (SM_Q0 - SM_Q1) / math.sqrt(2.0)  # collective/"dark" combination

# Sanity fact checked once at import time (not asserted, computed): (SM_q0+SM_q1)
# applied to |1,1> (both sheets excited) must NOT factor as a product state --
# this is what makes E_plus/E_minus qualitatively different from every branch in
# r1 (all of which are local or product-of-local and cannot do this).
_ket11 = np.zeros(8, dtype=complex)
_ket11[0b110] = 1.0  # |q0=1, q1=1, q2=0>
_out = E_PLUS_BASE @ _ket11
_ENTANGLING_CHECK = {
    "input_ket": "|q0=1,q1=1,q2=0>",
    "E_plus_output_amplitudes_nonzero_at": [int(i) for i in np.nonzero(np.abs(_out) > 1e-12)[0]],
    "is_product_form_impossible_check": (
        "output has amplitude on >1 basis ket from a single product input "
        "ket under a single branch operator; no operator of product form "
        "(A tensor B tensor I) can do this"
    ),
    "n_nonzero_output_terms": int(np.count_nonzero(np.abs(_out) > 1e-12)),
}


def build_branch_words(stage: int, dt: float) -> list:
    """Omega_r as (label, K, depth) triples. depth 0 = coherent/no-jump;
    depth 1 = single jump EVENT (local per-sheet OR the new collective
    entangling pair -- one jump event touching both sheets at once); depth 2 =
    composed products of two depth-1 LOCAL words, unchanged from r1. The
    E_plus/E_minus branches are the ONLY addition relative to r1's alphabet;
    depth-2 compositions involving them are deliberately out of scope (see
    header: one new ingredient at a time)."""
    Ls4 = BANK_JUMPS(stage, 1.0)
    Ls = [embed_4d_to_8d(L) for L in Ls4]
    U = build_coherent_tick(dt)
    sqdt = math.sqrt(max(dt, 1e-12))
    words = [("id", U, 0)]
    for i, L in enumerate(Ls):
        words.append((f"L{i}", L * sqdt, 1))
    words.append(("E_plus", E_PLUS_BASE * sqdt, 1))
    words.append(("E_minus", E_MINUS_BASE * sqdt, 1))
    for i, Li in enumerate(Ls):
        for j, Lj in enumerate(Ls):
            words.append((f"L{i}L{j}", (Li @ Lj) * max(dt, 1e-12), 2))
    return words


def compute_weights_v2(words: list, drive: float, law: str):
    n = len(words)
    meta = {"law": law, "drive": float(drive), "n": n, "k_ent": K_ENT}
    if law == "W7_entangling_uniform":
        return np.ones(n, dtype=float) / n, meta
    if law == "W6_entangling_drive":
        raw = np.ones(n, dtype=float)
        for idx, (lab, _K, _depth) in enumerate(words):
            if lab in ("E_plus", "E_minus"):
                raw[idx] = math.exp(float(drive) * K_ENT)
        return raw / raw.sum(), meta
    raise ValueError(f"unknown law {law}")


def apply_weighted_kraus(rho: np.ndarray, words: list, weights) -> tuple:
    M = np.zeros_like(rho)
    branch_info = []
    for (lab, K, depth), w in zip(words, weights):
        KrhoKd = K @ rho @ K.conj().T
        M += w * KrhoKd
        branch_info.append({
            "h": lab, "depth": depth, "w": float(w),
            "p_unweighted": float(np.real(np.trace(KrhoKd))),
        })
    tr = float(np.real(np.trace(M)))
    info = {"trace_before_renorm": tr, "n_branches": len(words), "branch_info": branch_info}
    if abs(tr) < 1e-14:
        return rho.copy(), {**info, "renorm": "zero_trace_fallback", "trace_dev": 1.0}
    rho_out = M / tr
    rho_out = 0.5 * (rho_out + rho_out.conj().T)
    info["renorm"] = "trace_renormalized" if abs(tr - 1.0) > 1e-9 else "trace_preserved"
    info["trace_dev"] = abs(tr - 1.0)
    return rho_out, info


# ---------------- trajectory machinery ----------------------------------------
def initial_rho() -> np.ndarray:
    rho4_0 = m1.ManifoldState().rho_LR.copy()
    rho = embed_state_4d_to_8d(rho4_0)
    rho = 0.5 * (rho + rho.conj().T)
    return rho / float(np.real(np.trace(rho)))


def simulate_trajectory(drive_series: list, law: str) -> list:
    rho = initial_rho()
    rows = []
    for t, drive_val in enumerate(drive_series):
        stage = t // 10
        drive = float(drive_val)
        ind = fixed_independent_panel(rho)
        cuts = cut_observables_3q(rho)
        row = {"tick": t, "stage": stage, "drive": drive, "independent": ind, "cuts": cuts}
        if law == "W5_scalar_baseline":
            gamma = GAMMA_BASE * drive / math.log(4)
            rho_next = evolve_tick_scalar(rho, stage, gamma)
            row["map_class"] = "scalar_gksl_gamma_t"
            row["gamma"] = gamma
        else:
            words = build_branch_words(stage, TICK_DT)
            w, _wmeta = compute_weights_v2(words, drive, law)
            rho_next, minfo = apply_weighted_kraus(rho, words, w)
            row["map_class"] = minfo["renorm"]
            row["trace_dev"] = minfo["trace_dev"]
            row["n_branches"] = minfo["n_branches"]
            row["entangling_branch_info"] = [
                bi for bi in minfo["branch_info"] if bi["h"] in ("E_plus", "E_minus")
            ]
        rho = rho_next
        rows.append(row)
    return rows


def series_from_rows(rows: list):
    drives = [r["drive"] for r in rows]
    keys_ind = list(rows[0]["independent"].keys())
    keys_cut = list(rows[0]["cuts"].keys())
    ind_series = {k: [r["independent"][k] for r in rows] for k in keys_ind}
    cut_series = {k: [r["cuts"][k] for r in rows] for k in keys_cut}
    return drives, ind_series, cut_series


def rms_cut_correlation(drives: list, cut_series: dict):
    cut_corrs = {k: pearson(drives, cut_series[k]) for k in cut_series}
    rms = math.sqrt(sum(v * v for v in cut_corrs.values()) / max(1, len(cut_corrs)))
    return cut_corrs, rms


def null_distribution(drive_series: list, law: str, n_shuffles: int = N_NULL_SHUFFLES,
                       base_seed: int = SHUFFLE_SEED):
    vals = []
    for i in range(n_shuffles):
        ds = shuffle_series(drive_series, seed=base_seed + 1000 + i)
        rows = simulate_trajectory(ds, law)
        drives, _ind, cuts = series_from_rows(rows)
        _corrs, rms = rms_cut_correlation(drives, cuts)
        vals.append(rms)
    arr = np.asarray(vals, dtype=float)
    return {
        "n_shuffles": n_shuffles,
        "mean": float(arr.mean()), "std": float(arr.std()),
        "min": float(arr.min()), "max": float(arr.max()),
        "p95": float(np.percentile(arr, 95)),
        "values": [float(v) for v in vals],
    }


def run_candidate(drive_series: list, law: str) -> dict:
    rows = simulate_trajectory(drive_series, law)
    drives, ind_series, cut_series = series_from_rows(rows)
    ind_corrs = {k: pearson(drives, ind_series[k]) for k in ind_series}
    cut_corrs, rms_cut = rms_cut_correlation(drives, cut_series)

    drives_shuf = shuffle_series(drives, SHUFFLE_SEED)
    rows_shuf = simulate_trajectory(drives_shuf, law)
    _dsh, _indsh, cut_series_shuf = series_from_rows(rows_shuf)
    shuf_cut_corrs, rms_cut_shuf = rms_cut_correlation(drives_shuf, cut_series_shuf)

    s_ent = ind_series["von_neumann_entropy_bits"]
    entropy_cut_corrs = {k: pearson(s_ent, cut_series[k]) for k in cut_series}
    scalar_entropy_only = {}
    for k in cut_corrs:
        dc, ec = abs(cut_corrs[k]), abs(entropy_cut_corrs[k])
        scalar_entropy_only[k] = {
            "drive_cut_corr": float(cut_corrs[k]),
            "entropy_cut_corr": float(entropy_cut_corrs[k]),
            "S_explains_as_well": bool(ec >= 0.95 * dc),
        }

    min_conditional = {
        k: float(min(cut_series[k])) for k in cut_series
        if k in ("S_L_given_MR", "S_MR_given_L", "S_LM_given_R")
    }
    any_negative_conditional = bool(any(v < -1e-9 for v in min_conditional.values()))

    entangling_activity = None
    if law != "W5_scalar_baseline":
        e_plus_p = [r["entangling_branch_info"][0]["p_unweighted"] for r in rows]
        e_minus_p = [r["entangling_branch_info"][1]["p_unweighted"] for r in rows]
        e_plus_w = [r["entangling_branch_info"][0]["w"] for r in rows]
        e_minus_w = [r["entangling_branch_info"][1]["w"] for r in rows]
        entangling_activity = {
            "E_plus_p_unweighted_mean": float(np.mean(e_plus_p)),
            "E_plus_p_unweighted_max": float(np.max(e_plus_p)),
            "E_minus_p_unweighted_mean": float(np.mean(e_minus_p)),
            "E_minus_p_unweighted_max": float(np.max(e_minus_p)),
            "E_plus_weight_mean": float(np.mean(e_plus_w)),
            "E_minus_weight_mean": float(np.mean(e_minus_w)),
            "branches_ever_active": bool(max(max(e_plus_p), max(e_minus_p)) > 1e-9),
        }

    trace_devs = [r.get("trace_dev", 0.0) for r in rows]

    return {
        "law": law,
        "n_ticks": len(drive_series),
        "drive_series": drives,
        "independent_corrs": ind_corrs,
        "cut_corrs": cut_corrs,
        "rms_cut_correlation": rms_cut,
        "shuffled_cut_corrs": shuf_cut_corrs,
        "shuffled_rms_cut_correlation": rms_cut_shuf,
        "shuffle_collapsed": bool(rms_cut_shuf < 0.5 * rms_cut) if rms_cut > 0 else False,
        "trace_dev_summary": {
            "max": float(max(trace_devs)) if trace_devs else 0.0,
            "mean": float(np.mean(trace_devs)) if trace_devs else 0.0,
        },
        "scalar_entropy_only": scalar_entropy_only,
        "min_conditional_entropy_per_cut": min_conditional,
        "any_negative_conditional_entropy": any_negative_conditional,
        "entangling_branch_activity": entangling_activity,
        "rows_tail": rows[-3:],
    }


# ---------------- main -----------------------------------------------------------
def main():
    HERE = Path(__file__).resolve().parent
    OUT = HERE / "results" / "r2"
    receipt_path = OUT / "receipt.json"
    if receipt_path.exists():
        print(json.dumps({"error": "refusing to reuse output dir",
                          "path": str(receipt_path)}, indent=2))
        sys.exit(1)
    OUT.mkdir(parents=True, exist_ok=True)

    drive_series = compute_drive_series(N_TICKS)

    candidates = ["W5_scalar_baseline", "W6_entangling_drive", "W7_entangling_uniform"]
    per_candidate = {law: run_candidate(drive_series, law) for law in candidates}

    # null distribution (30 draws) for the primary new candidate only (W6)
    w6_null = null_distribution(drive_series, "W6_entangling_drive")
    w6_rms = per_candidate["W6_entangling_drive"]["rms_cut_correlation"]
    w6_null_percentile = float(
        100.0 * np.mean(np.asarray(w6_null["values"]) < w6_rms)
    )

    # qutip referee: 2 spot ticks on the W5 reproduction only
    rho_spot = initial_rho()
    spot_checks = []
    for t in range(N_TICKS):
        stage = t // 10
        d = drive_series[t]
        gamma = GAMMA_BASE * d / math.log(4)
        if t in SPOT_TICKS:
            H8 = embed_4d_to_8d(BUILD_JOINT_H())
            Ls8 = [embed_4d_to_8d(L) for L in BANK_JUMPS(stage, gamma)]
            rho_after_np = evolve_tick_scalar(rho_spot, stage, gamma)
            spot_checks.append({
                "tick": t, "rho_before": rho_spot.copy(), "H": H8, "Ls": Ls8,
                "dt": TICK_DT, "label": f"W5_stage{stage}",
                "np_after": rho_after_np.copy(),
            })
        rho_spot = evolve_tick_scalar(rho_spot, stage, gamma)
    qutip_results = qutip_spot_checks(spot_checks)

    scalar_rms = per_candidate["W5_scalar_baseline"]["rms_cut_correlation"]
    w7_rms = per_candidate["W7_entangling_uniform"]["rms_cut_correlation"]
    w6_shuf_rms = per_candidate["W6_entangling_drive"]["shuffled_rms_cut_correlation"]

    beats_scalar_baseline = bool(w6_rms > scalar_rms)
    beats_matched_shuffle = bool(w6_rms > w6_shuf_rms)
    beats_null_p95 = bool(w6_rms > w6_null["p95"])
    strengthened = bool(beats_scalar_baseline and beats_matched_shuffle and beats_null_p95)

    summary = {
        "w6_rms_cut_correlation": w6_rms,
        "w6_shuffled_rms_cut_correlation_matched": w6_shuf_rms,
        "w6_null_distribution_30draw": {
            "mean": w6_null["mean"], "std": w6_null["std"], "p95": w6_null["p95"],
        },
        "w6_percentile_vs_null": w6_null_percentile,
        "scalar_baseline_rms_cut_correlation": scalar_rms,
        "w7_ablation_rms_cut_correlation": w7_rms,
        "w6_minus_scalar_baseline": w6_rms - scalar_rms,
        "w6_minus_w7_ablation": w6_rms - w7_rms,
        "prior_r1_best_rms_cut_correlation": 0.044456556847851436,
        "prior_r1_best_shuffle_rms_cut_correlation": 0.1616715574347303,
        "criteria": {
            "a_beats_scalar_baseline": beats_scalar_baseline,
            "b_beats_matched_shuffle": beats_matched_shuffle,
            "c_beats_null_p95": beats_null_p95,
        },
        "verdict": "strengthened" if strengthened else "still-open",
        "entangling_branches_ever_active_W6": (
            per_candidate["W6_entangling_drive"]["entangling_branch_activity"]["branches_ever_active"]
        ),
        "any_negative_conditional_entropy_any_candidate": {
            law: per_candidate[law]["any_negative_conditional_entropy"] for law in candidates
        },
    }

    receipt = {
        "schema": "ratchet.v8.axis0_front.r2_strengthen_coupling.v0",
        "authority": ("system_v8/axis0_front/AXIS0_FRONT_OBJECT_CARD_v0.md §9, §14, GAP-1..GAP-3; "
                      "owner doctrine memory: user_entanglement_central_conditional_entropy_gradient.md"),
        "hypothesis_status": "installed hypothesis only; nothing canon until ratcheted",
        "new_ingredient": "collective/entangling dissipative branch (E_plus, E_minus); "
                          "never present in any prior axis0_front or entanglement_gradient sim",
        "entangling_operator_check": _ENTANGLING_CHECK,
        "prior_state_cited": {
            "scalar_rate_manifold_one": {
                "path": "system_v8/nested_manifold/results/manifold_one/receipt.json",
                "drive_correlations": {"dS_L": 0.0155, "dS_LR": 0.0188, "dPhi0": -0.0359},
            },
            "scalar_rate_unified_v2_L09": {
                "path": "system_v8/unified/results/manifold_unified_v2/receipt.json:layer_computations.L09",
                "baseline_rms_correlation": 0.05983978912442773,
                "shuffled_rms_correlation": 0.03727037487323659,
                "signal_floor": 0.2,
            },
            "history_weights_r1": {
                "path": "system_v8/axis0_front/results/r1/receipt.json:summary",
                "best_rms_cut_correlation": 0.044456556847851436,
                "scalar_baseline_rms_cut_correlation": 0.04358289706304026,
                "best_shuffle_rms_cut_correlation": 0.1616715574347303,
            },
            "gradient_tournament": {
                "path": "system_v8/axis0_front/results/gradient_tournament_v0/receipt.json:findings",
                "best_per_event_class_stage_transition": None,
            },
            "coherent_information_ladder": {
                "path": "system_v8/entanglement_gradient/results/coherent_information_ladder_v0/receipt.json:data",
                "drive_I_correlation": -0.1288550593771927,
                "shuffled_drive_correlation": -0.05665507024423676,
                "note": "readout-side probe only; kept scalar-rate coupling; recalibrated "
                        "J_XY 0.35->2.0 (fixed, drive-blind) to make its own P3 control fire",
            },
        },
        "parameters": {
            "n_ticks": N_TICKS, "tick_dt": TICK_DT, "depth": DEPTH,
            "gamma_base": GAMMA_BASE, "k_ent": K_ENT,
            "j_xy_unchanged_drive_blind": J_XY_UNCHANGED,
            "n_null_shuffles": N_NULL_SHUFFLES,
            "interpreter": SIM_INTERPRETER, "sys_executable": sys.executable,
            "memory_gate": mem,
        },
        "drive_series_source": "A_SCHED packet growth (identical to manifold_one and r1)",
        "candidates": candidates,
        "per_candidate": per_candidate,
        "w6_null_distribution": w6_null,
        "qutip_referee": qutip_results,
        "product_no_entanglement_cut_control": (
            "not re-run; equals r1's existing W1_capacity/W2_surprise/W3_growth receipts "
            "(rms 0.0282-0.0445, all near/below the scalar baseline and below their own "
            "single-shuffle nulls) -- this file differs from r1 only by adding E_plus/E_minus"
        ),
        "summary": summary,
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("scratch_diagnostic / tool_lego_fit_probe; tests the doc's §9 w_h "
                          "slot with a genuinely entangling (collective) branch for the first "
                          "time in this lane; reports numbers honestly; no physics claim"),
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    receipt_path.write_text(json.dumps(receipt, indent=2, default=float) + "\n")

    print("R2 DONE: verdict=%s w6_rms=%.6f scalar_baseline=%.6f w7_ablation=%.6f "
          "w6_matched_shuffle=%.6f w6_null_p95=%.6f w6_pct_vs_null=%.1f "
          "criteria(a,b,c)=(%s,%s,%s)" % (
              summary["verdict"], w6_rms, scalar_rms, w7_rms, w6_shuf_rms,
              w6_null["p95"], w6_null_percentile,
              beats_scalar_baseline, beats_matched_shuffle, beats_null_p95))


if __name__ == "__main__":
    main()
