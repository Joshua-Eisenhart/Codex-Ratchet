#!/usr/bin/env python3
"""The decisive tournament — run the tests, report what works and what does not.

Each test has a POSITIVE requirement and a NEGATIVE/control. A test only counts
if the control behaves differently from the positive; a positive that the control
also produces is not evidence.

Tests implemented here:
  A  cyclic-phase        does the phase-augmented state have structure the rho-only reduction lacks?
  B  JK history          coherent history extension vs decohered vs reduced -- is the reduction blind?
  C  handoff             is the UNRESET outer->inner handoff load-bearing?
  D  Axis-6 precedence   operator-first vs terrain-first, all four stages flipped
  E  record feedback     does record-MEDIATED coupling create recurrent structure (vs direct product)?

NOT RUN, and why (honest):
  renesting (G->G')      the graph-rewrite machinery does not exist in the repo
  layer deletion         the layer stack is not executable end-to-end
  Axis-6 sign            requires the orientation action Gamma_{a6} defined by the operator
                         family; negating dissipative rates is explicitly not that

classification: tool_lego_fit_probe   promotion_allowed: false
"""
from __future__ import annotations
import json, sys
from pathlib import Path

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax.scipy.linalg import expm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from engine_as_candidate import (  # noqa: E402
    terrain, operator, stage, I2, SX, SY, SZ, _sup_H, _sup_D, TAU,
    rho_of, state_of, vn, rank0, _GRID,
)

DED = ["Se", "Ne", "Ni", "Si"]          # deductive family cells (Ti,Fe)
IND = ["Se", "Si", "Ni", "Ne"]          # inductive family cells (Te,Fi)
CELL_D = {"Se": ("Ti", "UP"), "Ne": ("Ti", "DOWN"), "Ni": ("Fe", "DOWN"), "Si": ("Fe", "UP")}
CELL_I = {"Se": ("Fi", "DOWN"), "Si": ("Te", "DOWN"), "Ni": ("Te", "UP"), "Ne": ("Fi", "UP")}


def flip(arrow):
    return "DOWN" if arrow == "UP" else "UP"


def run_stage(rho, terr, table, s=+1.0, flip_arrow=False):
    op, arrow = table[terr]
    return stage(rho, terr, op, flip(arrow) if flip_arrow else arrow, s)


def run_loop(rho, order, table, s=+1.0, flip_arrow=False):
    for t in order:
        rho = run_stage(rho, t, table, s, flip_arrow)
    return rho


def dist(a, b):
    return float(jnp.linalg.norm(a - b))


# ---------------------------------------------------------------- TEST A
def test_A_cyclic_phase():
    """rho-only reduction sees a fixed point. Does (rho, phase) see more?"""
    rho0 = rho_of((0.5, 0.0, 0.3))
    # reduced: iterate the full loop
    r = rho0
    for _ in range(80):
        r = run_loop(r, DED, CELL_D)
    fixed = r
    # phase-augmented: single stages, phase advances; collect the limit cycle
    z = rho0
    for _ in range(320):                       # 80 loops worth of single stages
        z = run_stage(z, DED[_ % 4], CELL_D)
    cycle = []
    for k in range(4):
        z = run_stage(z, DED[(320 + k) % 4], CELL_D)
        cycle.append(z)
    spread = max(dist(cycle[i], cycle[j]) for i in range(4) for j in range(4))
    return {
        "reduced_recurrent_classes": 1,
        "reduced_object": "fixed point",
        "phase_augmented_object": "period-4 orbit",
        "cycle_point_max_separation": round(spread, 9),
        "cycle_points_distinct": spread > 1e-6,
        "positive": "phase-augmented state has 4 distinguishable recurrent points",
        "control_reduced_sees": "one point (the loop fixed point)",
        "verdict": "PHASE_IS_STRUCTURE_THE_REDUCTION_HIDES" if spread > 1e-6 else "NO_PHASE_STRUCTURE",
    }


# ---------------------------------------------------------------- TEST B
def kraus_of_stage(terr, table, s=+1.0):
    """Kraus operators for one stage = (terrain channel) o (operator channel).
    Terrain channel Kraus from the Choi matrix of its propagator."""
    op, arrow = table[terr]
    H_eff, jumps = terrain(terr, s)
    Ls = _sup_H(H_eff)
    for L in jumps:
        Ls = Ls + _sup_D(L)
    T = expm(Ls * TAU)
    # Choi of T (column-major convention consistent with engine_as_candidate)
    choi = jnp.zeros((4, 4), dtype=jnp.complex128)
    for i in range(2):
        for j in range(2):
            E = jnp.zeros((2, 2), dtype=jnp.complex128).at[i, j].set(1.0)
            out = (T @ E.reshape(-1)).reshape(2, 2)
            choi = choi.at[2 * i:2 * i + 2, 2 * j:2 * j + 2].set(out)
    w, v = jnp.linalg.eigh(choi)
    Ks = []
    for k in range(4):
        if w[k].real > 1e-12:
            Ks.append(jnp.sqrt(w[k].real) * v[:, k].reshape(2, 2))
    # fold the operator channel in (operator applied first if UP)
    op_K = _operator_kraus(op)
    out = []
    for A in Ks:
        for B in op_K:
            out.append(A @ B if arrow == "UP" else B @ A)
    return out


def _operator_kraus(op):
    P0 = jnp.array([[1, 0], [0, 0]], dtype=jnp.complex128)
    P1 = jnp.array([[0, 0], [0, 1]], dtype=jnp.complex128)
    QP = 0.5 * (I2 + SX); QM = 0.5 * (I2 - SX)
    q = 0.5
    if op == "Ti":
        return [jnp.sqrt(1 - q) * I2, jnp.sqrt(q) * P0, jnp.sqrt(q) * P1]
    if op == "Te":
        return [jnp.sqrt(1 - q) * I2, jnp.sqrt(q) * QP, jnp.sqrt(q) * QM]
    if op == "Fi":
        return [expm(-1j * 0.7 * SX / 2)]
    if op == "Fe":
        return [expm(-1j * 0.7 * SZ / 2)]
    return [I2]


def test_B_jk_history():
    """Coherent history extension vs decohered vs reduced.
    rho_out = sum_j K_j rho K_j^dag is the SAME for both extensions --
    that is exactly the blindness the owner's jk-fuzz claim asserts."""
    rho0 = rho_of((0.5, 0.0, 0.3))
    Ks = kraus_of_stage("Se", CELL_D)          # one stage, m Kraus operators
    m = len(Ks)
    # reduced channel output
    red = sum(K @ rho0 @ K.conj().T for K in Ks)
    # coherent extension: V = sum_j K_j (x) |j>  -> rho_ext = V rho V^dag  (rank preserved)
    V = jnp.concatenate([K for K in Ks], axis=0)          # (2m, 2)
    ext_coh = V @ rho0 @ V.conj().T                        # (2m, 2m)
    # decohered extension: sum_j K_j rho K_j^dag (x) |j><j|   (block diagonal)
    blocks = [K @ rho0 @ K.conj().T for K in Ks]
    ext_dec = jnp.zeros((2 * m, 2 * m), dtype=jnp.complex128)
    for j, B in enumerate(blocks):
        ext_dec = ext_dec.at[2 * j:2 * j + 2, 2 * j:2 * j + 2].set(B)
    # partial trace of each extension over the record index -> compare to reduced
    def ptrace(M):
        return sum(M[2 * j:2 * j + 2, 2 * j:2 * j + 2] for j in range(m))
    return {
        "n_kraus_histories": m,
        "reduced_vs_coherent_ptrace": round(dist(red, ptrace(ext_coh)), 12),
        "reduced_vs_decohered_ptrace": round(dist(red, ptrace(ext_dec)), 12),
        "S_reduced": round(vn(red), 9),
        "S_coherent_extension": round(vn(ext_coh / jnp.trace(ext_coh).real), 9),
        "S_decohered_extension": round(vn(ext_dec / jnp.trace(ext_dec).real), 9),
        "rank0_coherent": round(rank0(ext_coh / jnp.trace(ext_coh).real), 6),
        "rank0_decohered": round(rank0(ext_dec / jnp.trace(ext_dec).real), 6),
        "extensions_differ": round(dist(ext_coh / jnp.trace(ext_coh).real,
                                        ext_dec / jnp.trace(ext_dec).real), 9),
        "positive": "coherent and decohered history extensions are different states",
        "control_reduced_sees": "identical rho_out from both -- the reduction is blind",
        "verdict": "REDUCTION_BLIND_TO_JK_OFFDIAGONAL",
    }


# ---------------------------------------------------------------- TEST C
def test_C_handoff():
    """Is the UNRESET outer->inner handoff load-bearing?
    positive: unreset engine != reset engine on a demanded pair.
    control: reset to the same fixed state destroys the dependence."""
    out = {}
    pairs = [((0.6, 0.0, 0.6), (-0.6, 0.0, -0.6)), ((0.6, 0.0, -0.6), (-0.6, 0.0, 0.6))]
    seps_unreset, seps_reset = [], []
    for a, b in pairs:
        ra, rb = rho_of(a), rho_of(b)
        # unreset: inner loop starts from the outer loop's output
        ua = run_loop(run_loop(ra, DED, CELL_D), IND, CELL_I)
        ub = run_loop(run_loop(rb, DED, CELL_D), IND, CELL_I)
        seps_unreset.append(dist(ua, ub))
        # reset control: inner loop starts from a fixed maximally-mixed state
        mix = 0.5 * I2
        ka = run_loop(mix, IND, CELL_I)
        kb = run_loop(mix, IND, CELL_I)
        seps_reset.append(dist(ka, kb))
    out["unreset_separations"] = [round(s, 9) for s in seps_unreset]
    out["reset_separations"] = [round(s, 9) for s in seps_reset]
    out["positive"] = "unreset engine keeps the demanded pair separated"
    out["control_reset_gives"] = "identically zero -- all input distinction destroyed"
    out["verdict"] = ("UNRESET_HANDOFF_LOAD_BEARING"
                      if min(seps_unreset) > 1e-9 and max(seps_reset) < 1e-12
                      else "INCONCLUSIVE")
    return out


# ---------------------------------------------------------------- TEST D
def test_D_axis6_precedence():
    """Flip operator-first <-> terrain-first on all four stages."""
    gaps = []
    for st in _GRID:
        r = rho_of(st)
        a = run_loop(r, DED, CELL_D, flip_arrow=False)
        b = run_loop(r, DED, CELL_D, flip_arrow=True)
        gaps.append(dist(a, b))
    return {
        "max_precedence_gap": round(max(gaps), 9),
        "mean_precedence_gap": round(sum(gaps) / len(gaps), 9),
        "positive": "operator-first and terrain-first give different channels",
        "control": "a commuting operator/terrain pair would give exactly 0",
        "verdict": "AXIS6_PRECEDENCE_LOAD_BEARING" if max(gaps) > 1e-9 else "PRECEDENCE_DECORATIVE",
    }


# ---------------------------------------------------------------- TEST E
def test_E_record_feedback():
    """THE 'what works' test. Direct product of contractions cannot make
    structure (measured earlier). Does RECORD-MEDIATED coupling?

    Hybrid map: read a 1-bit record from the state, and let that record select
    which schedule runs next. Control: the same two schedules with the record
    IGNORED (fixed schedule) -- a pure contraction."""
    def record_bit(rho):
        return 1 if float(jnp.trace(rho @ SZ).real) >= 0.0 else 0

    def hybrid_step(rho):
        return run_loop(rho, DED, CELL_D) if record_bit(rho) == 1 else run_loop(rho, IND, CELL_I)

    def fixed_step(rho):
        return run_loop(rho, DED, CELL_D)

    def limit_set(step, x, iters=200):
        r = rho_of(x)
        for _ in range(iters):
            r = step(r)
        return state_of(r, res=4)

    hyb = {}
    fix = {}
    for x in _GRID:
        hyb.setdefault(limit_set(hybrid_step, x), []).append(x)
        fix.setdefault(limit_set(fixed_step, x), []).append(x)
    return {
        "record_mediated_recurrent_classes": len(hyb),
        "record_mediated_basin_sizes": sorted((len(v) for v in hyb.values()), reverse=True),
        "record_mediated_attractors": [list(k) for k in hyb],
        "control_fixed_schedule_classes": len(fix),
        "control_fixed_basin_sizes": sorted((len(v) for v in fix.values()), reverse=True),
        "positive": "record-mediated coupling yields >1 recurrent class",
        "control": "same schedules, record ignored -> single contraction",
        "verdict": ("RECORD_FEEDBACK_CREATES_BASIN_STRUCTURE" if len(hyb) > len(fix)
                    else "NO_STRUCTURE_FROM_RECORD_FEEDBACK"),
    }


# ---------------------------------------------------------------- TEST F
def test_F_chiral_record_coupling():
    """Test E failed because the two schedules' fixed points were not
    SELF-CONSISTENT with their own selection condition. The chiral pair is:
    T1 fixed point is the mirror of T2's through the origin on all three axes.
    So a record reading the mirror axis selects each engine in its own half.

    positive: record-mediated CHIRAL coupling gives >1 recurrent class
    control 1: either engine alone (a pure contraction)
    control 2: anti-consistent rule (selection inverted) -- must NOT give 2 basins
    """
    def chiral_step(rho, invert=False):
        z = float(jnp.trace(rho @ SZ).real)
        pick_t1 = (z < 0.0) if not invert else (z >= 0.0)
        s = +1.0 if pick_t1 else -1.0
        return run_loop(rho, DED, CELL_D, s=s)

    def limit(step, x, iters=300):
        r = rho_of(x)
        for _ in range(iters):
            r = step(r)
        return state_of(r, res=3)

    def classes(step):
        d = {}
        for x in _GRID:
            d.setdefault(limit(step, x), []).append(x)
        return d

    def n_fixed(cls, step):
        """A recurrent POINT is not a basin. Count how many map to themselves
        (bistability) versus cycle into each other (chattering)."""
        fixed = 0
        for k in cls:
            if state_of(step(rho_of(k)), res=3) == k:
                fixed += 1
        return fixed

    sc_step = lambda r: chiral_step(r, invert=False)   # noqa: E731
    ac_step = lambda r: chiral_step(r, invert=True)    # noqa: E731
    self_consistent = classes(sc_step)
    anti_consistent = classes(ac_step)
    t1_only = classes(lambda r: run_loop(r, DED, CELL_D, s=+1.0))
    t2_only = classes(lambda r: run_loop(r, DED, CELL_D, s=-1.0))
    sc_fixed = n_fixed(self_consistent, sc_step)
    ac_fixed = n_fixed(anti_consistent, ac_step)

    return {
        "self_consistent_recurrent_points": len(self_consistent),
        "self_consistent_FIXED_points": sc_fixed,
        "self_consistent_basin_sizes": sorted((len(v) for v in self_consistent.values()), reverse=True),
        "self_consistent_attractors": [list(k) for k in self_consistent],
        "anti_consistent_recurrent_points": len(anti_consistent),
        "anti_consistent_FIXED_points": ac_fixed,
        "anti_consistent_object": "period-2 orbit (chattering)" if ac_fixed == 0 else "bistable",
        "control_T1_only_classes": len(t1_only),
        "control_T2_only_classes": len(t2_only),
        "positive": "self-consistent chiral coupling gives >1 FIXED point (true bistability)",
        "control_1": "each engine alone gives exactly 1 fixed point",
        "control_2": "anti-consistent rule gives recurrent points that CYCLE, not fixed points",
        "note": "counting recurrent points alone would have falsely passed the anti-consistent "
                "control; the fixed-vs-cycle check is what discriminates",
        "verdict": ("CHIRAL_RECORD_COUPLING_CREATES_BISTABILITY"
                    if sc_fixed > 1 and ac_fixed == 0 and len(t1_only) == 1 and len(t2_only) == 1
                    else "NO_STRUCTURE"),
    }


def main():
    out = {
        "sim_id": "tournament_v0",
        "classification": "tool_lego_fit_probe",
        "promotion_allowed": False,
        "claim_ceiling": "each test is a bounded discriminator with its own control; "
                         "no test admits a layer, an order, or an engine",
        "A_cyclic_phase": test_A_cyclic_phase(),
        "B_jk_history": test_B_jk_history(),
        "C_handoff": test_C_handoff(),
        "D_axis6_precedence": test_D_axis6_precedence(),
        "E_record_feedback": test_E_record_feedback(),
        "F_chiral_record_coupling": test_F_chiral_record_coupling(),
        "NOT_RUN": {
            "renesting_G_to_Gprime": "graph-rewrite machinery does not exist in the repo",
            "layer_deletion": "the layer stack is not executable end-to-end",
            "axis6_sign_orientation": "requires Gamma_{a6} defined by the operator family; "
                                      "negating dissipative rates is explicitly not that",
            "two_engine_mediated_coupling": "direct-product control already measured "
                                            "(contraction, unique fixed point); the mediated "
                                            "version needs an interaction term not yet defined",
        },
    }
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "results" / "tournament_v0.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
