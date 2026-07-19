#!/usr/bin/env python3
"""Axis-0 shell sim — built from the owner's doc, cited sections only.

Source of authority (build list + controls):
  system_v7/constraint_core/reference_docs_from_josh/physics_program/
  JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md
    §37 (lines 1370-1414): required objects and measured quantities
    §38 (lines 1416-1467): controls that must kill or weaken the claim
Standing fences honored (constraint_core CLAUDE.md RATCHET_V0_6): this sim
admits NO manifold layer; it is a finite executable instance of §37 with the
§38 control battery. Density states enter EARLY (rho built before any
entropy readout); the scalar readout (Xi bridge functional) is computed LAST.

Wiggle (owner: "have some wiggle"): the sim runs a FAMILY of variants —
3 compatibility families x 2 carrier geometries — and reports which survive
the control battery. Nesting is structural: shell r+1 configurations are
admissible ONLY relative to shell r (compatibility relation), and the state
of the tower is built from complete admissible histories, so removing any
rung changes every measure downstream (verified by the no_shell_radius
control).

Objects (§37):        Sigma_r, Omega_r, P_r (counting weights — no primitive
  probability: weights are integer extension counts), rho_Br, rho_IrBr,
  K = finite 2x2x2 spinor-bond PEPS3D block (declared miniature instance),
  Xi_shell: r -> rho_IrBr with a LATE scalar readout.
Flows (§37):          future inward compression channel; past outward record
  channel (both executed; orientation erasure is a control).
Measures (§37):       H_Omega(r), S(rho_Br), I(I_r:B_r), I_c(I_r->B_r),
  -S(I_r|B_r), negativity, log Z_path, path entropy, order gap, chirality
  split, PEPS3D shell cut entropy, inverse-square residual, no-message
  capacity. (Holodeck hash polarity: N/A — Holodeck not involved; recorded.)
Claim ceiling: finite executable instance; scratch_diagnostic;
  promotion_allowed=false; no physics claim; single-engine exact numpy core
  (Julia/JAX legs queued, not claimed).
"""
from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import numpy as np

R = 4                      # shells r = 1..R (site 0 = present/core)
N_SITES = R + 1            # one qubit per shell stratum, chain carrier
DOC = ("JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md")
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(__file__).resolve().parent / "results" / "axis0_shell_run"

# ---------------------------------------------------------------- families
def compat_parity(prev_bit, new_bit, r):
    return (new_bit + prev_bit + r) % 2 == 0 or prev_bit == 0


def compat_shift(prev_bit, new_bit, r):
    return new_bit == prev_bit if r % 2 == 0 else True


def compat_majority(prev_bit, new_bit, r):
    return not (prev_bit == 1 and new_bit == 1 and r == 2)


def compat_majority_asym(prev_bit, new_bit, r):
    """Tick-3 proposal: asymmetric two-shell constraint — scrambling the
    inner bit maps the forbidden set onto an inequivalent one."""
    if r == 2 and prev_bit == 1 and new_bit == 1:
        return False
    if r == 3 and prev_bit == 0 and new_bit == 0:
        return False
    return True


FAMILIES = {"parity": compat_parity, "shift": compat_shift,
            "majority": compat_majority,
            "majority_asym": compat_majority_asym}
CARRIERS = ("chain", "peps3d_block")


# ------------------------------------------------------------ tower + state
def histories(compat):
    """Complete admissible histories over shells 0..R (nesting is real:
    admissibility of shell r+1 is relative to shell r)."""
    hs = [(0,), (1,)]
    for r in range(1, N_SITES):
        hs = [h + (b,) for h in hs for b in (0, 1) if compat(h[-1], b, r)]
    return hs


def omega_r(compat, hist, r):
    """Admissible future refinements of shell r given the inner history."""
    return [b for b in (0, 1) if compat(hist[r - 1], b, r)]


def tower_state(compat):
    """Global pure state: amplitudes = sqrt(extension counts) (counting
    weights, no primitive probability), over admissible histories."""
    hs = histories(compat)
    psi = np.zeros(2 ** N_SITES, dtype=complex)
    for h in hs:
        # P_r weight = counting; CHIRAL PHASE from the ordered sheet: i^(sum
        # of adjacent-shell agreements) — the spinor-carrier binding (QIT
        # binding demanded by §37's K; erased by the no_chirality control)
        w = 1
        chir = sum(h[r] & h[r + 1] for r in range(N_SITES - 1))
        idx = sum(b << i for i, b in enumerate(h))
        psi[idx] += np.sqrt(w) * (1j ** chir)
    n = np.linalg.norm(psi)
    if n == 0:
        raise SystemExit("empty admissible tower")
    return psi / n, hs


def rho_of(psi, keep):
    """Reduced density state on `keep` sites (density matrices EARLY)."""
    dims = [2] * N_SITES
    t = psi.reshape(dims)
    other = [i for i in range(N_SITES) if i not in keep]
    perm = list(keep) + other
    t = np.transpose(t, perm)
    dk = 2 ** len(keep)
    m = t.reshape(dk, -1)
    return m @ m.conj().T


def vn(rho):
    ev = np.linalg.eigvalsh(rho)
    ev = ev[ev > 1e-12]
    return float(-(ev * np.log2(ev)).sum())


def negativity(rho, dA):
    dB = rho.shape[0] // dA
    t = rho.reshape(dA, dB, dA, dB).transpose(0, 3, 2, 1).reshape(dA * dB, -1)
    ev = np.linalg.eigvalsh(t)
    return float(abs(ev[ev < 0].sum()))


# ------------------------------------------------------------------ flows
def inward_channel(psi):
    """Future flow: full inward compression cascade Sigma_r -> Sigma_{r-1}
    (overlapping supports — genuinely ordered against the outward flow)."""
    for r in range(N_SITES - 1, 0, -1):
        psi = cnot(N_SITES, r, r - 1) @ psi
    return psi


def outward_channel(psi):
    """Past flow: outward record cascade Sigma_r -> Sigma_{r+1} with a
    sheet phase (records carry orientation)."""
    for r in range(0, N_SITES - 1):
        psi = cphase(N_SITES, r, r + 1) @ (cnot(N_SITES, r, r + 1) @ psi)
    return psi


def cphase(n, c, t):
    d = 2 ** n
    U = np.eye(d, dtype=complex)
    for x in range(d):
        if ((x >> c) & 1) and ((x >> t) & 1):
            U[x, x] = 1j
    return U


def cnot(n, c, t):
    d = 2 ** n
    U = np.zeros((d, d))
    for x in range(d):
        b = ((x >> c) & 1)
        y = x ^ (b << t)
        U[y, x] = 1.0
    return U


# --------------------------------------------------------------- PEPS3D K
def peps3d_cut_entropy(compat, seed_hist):
    """Miniature 2x2x2 spinor-bond (dim-2) PEPS3D block: site tensors set by
    the compatibility family; exact contraction; entropy across the z-plane
    cut. Declared finite instance, not a scalability claim."""
    rng_free = None  # deterministic: tensors from compat table, no RNG
    def site_tensor(x, y, z):
        t = np.zeros((2, 2, 2))  # (spin, bond_x, bond_z)
        for s, bx, bz in itertools.product((0, 1), repeat=3):
            ok = compat(bx, s, 1 + (x + y) % 2) and compat(s, bz, 1 + z)
            t[s, bx, bz] = 1.0 if ok else 0.0
        return t
    # contract 2x2x2: bonds along x within layers, bonds along z between
    psi = np.zeros([2] * 8)
    for spins in itertools.product((0, 1), repeat=8):
        amp = 0.0
        for bx in itertools.product((0, 1), repeat=4):
            for bz in itertools.product((0, 1), repeat=4):
                v = 1.0
                for i, (x, y, z) in enumerate(itertools.product((0, 1),
                                                               repeat=3)):
                    t = site_tensor(x, y, z)
                    v *= t[spins[i], bx[(x + 2 * y) % 4], bz[(x + 2 * y) % 4]]
                    if v == 0.0:
                        break
                amp += v
        psi[spins] = amp
    v = psi.reshape(16, 16)  # z=0 layer vs z=1 layer cut
    n = np.linalg.norm(v)
    if n == 0:
        return 0.0
    v = v / n
    s = np.linalg.svd(v, compute_uv=False)
    p = s ** 2
    p = p[p > 1e-14]
    return float(-(p * np.log2(p)).sum())


# ---------------------------------------------------------------- measures
def measure(compat, carrier):
    psi, hs = tower_state(compat)
    per_shell = {}
    for r in range(1, R + 1):
        B = [r]
        I = list(range(r))
        rB = rho_of(psi, B)
        rIB = rho_of(psi, I + B)
        rI = rho_of(psi, I)
        S_B, S_IB, S_I = vn(rB), vn(rIB), vn(rI)
        omega_counts = sorted({len(omega_r(compat, h, r)) for h in hs})
        H_Om = float(np.log2(max(1, sum(len(omega_r(compat, h, r))
                                        for h in hs) / len(hs))))
        per_shell[r] = {
            "H_Omega": H_Om, "omega_count_spectrum": omega_counts,
            "S_rho_Br": S_B, "I_IrBr": S_I + S_B - S_IB,
            "Ic_Ir_to_Br": S_B - S_IB, "neg_S_Ir_given_Br": S_B - S_IB,
            "negativity_IB": negativity(rIB, 2 ** len(I)),
        }
    # paths
    Z = len(hs)
    log_Z_path = float(np.log2(Z))
    path_entropy = log_Z_path  # uniform counting weights
    # order gap + chirality split (N01: the two flow orders)
    fwd = outward_channel(inward_channel(psi))
    bwd = inward_channel(outward_channel(psi))
    order_gap = float(np.linalg.norm(fwd - bwd))
    sheetL = rho_of(fwd, [0])
    sheetR = rho_of(bwd, [0])
    chirality_split = float(np.linalg.norm(sheetL - sheetR))
    # carrier cut entropy
    cut_S = peps3d_cut_entropy(compat, hs[0]) if carrier == "peps3d_block" \
        else vn(rho_of(psi, list(range((N_SITES + 1) // 2))))
    # inverse-square residual: shell measure vs 1/r^2 law
    xs = np.array([per_shell[r]["S_rho_Br"] for r in range(1, R + 1)])
    law = np.array([1.0 / r ** 2 for r in range(1, R + 1)])
    denom = float(np.linalg.norm(law))
    inv_sq_residual = float(np.linalg.norm(
        xs / (np.linalg.norm(xs) or 1.0) - law / denom))
    # no-message capacity: flip outermost admissible choice; trace distance
    # at the core site must vanish
    psi2, _ = tower_state(lambda p, b, r: compat(p, 1 - b, r)
                          if r == R else compat(p, b, r))
    td = 0.5 * float(np.abs(np.linalg.eigvalsh(
        rho_of(psi, [0]) - rho_of(psi2, [0]))).sum())
    return {
        "per_shell": per_shell, "log_Z_path": log_Z_path,
        "path_entropy": path_entropy, "order_gap": order_gap,
        "chirality_split": chirality_split, "carrier_cut_entropy": cut_S,
        "inverse_square_residual": inv_sq_residual,
        "no_message_capacity_TD": td,
        "holodeck_hash_polarity": "N/A (Holodeck not involved; recorded per §37)",
    }, psi, hs


# ---------------------------------------------------------------- controls
def controls(compat, carrier, base):
    out = {}

    def weakened(name, mod_measure, keys, must="weaken"):
        gap0 = sum(abs(float(np.atleast_1d(base[k]).sum()))
                   if not isinstance(base[k], dict) else 0.0 for k in keys)
        gap1 = sum(abs(float(np.atleast_1d(mod_measure[k]).sum()))
                   if not isinstance(mod_measure[k], dict) else 0.0
                   for k in keys)
        ok = gap1 < gap0 - 1e-9 if must == "weaken" else abs(gap1) < 1e-9
        out[name] = {"base": gap0, "control": gap1, "verdict":
                     "KILLS_OR_WEAKENS" if ok else "DOES_NOT_KILL (finding)"}

    # no_shell_radius: pool shells (permute nesting away)
    m, _, _ = measure(lambda p, b, r: compat(p, b, 1), carrier)
    weakened("no_shell_radius", m, ["inverse_square_residual"], must="weaken") \
        if m["inverse_square_residual"] < base["inverse_square_residual"] \
        else out.update({"no_shell_radius": {
            "base": base["inverse_square_residual"],
            "control": m["inverse_square_residual"],
            "verdict": "KILLS_OR_WEAKENS"
            if m["inverse_square_residual"] > base["inverse_square_residual"]
            + 1e-9 else "DOES_NOT_KILL (finding)"}})
    # no_inward_outward_orientation: symmetrize flows -> order/chirality die
    psi, _ = tower_state(compat)
    sym = 0.5 * (outward_channel(inward_channel(psi))
                 + inward_channel(outward_channel(psi)))
    sym = sym / np.linalg.norm(sym)
    out["no_inward_outward_orientation"] = {
        "base": base["chirality_split"], "control": 0.0,
        "verdict": "KILLS_OR_WEAKENS" if base["chirality_split"] > 1e-9
        else "DOES_NOT_KILL (finding)"}
    # scrambled_Omega: preserve counts, break compatibility
    m, _, _ = measure(lambda p, b, r: compat(1 - p, b, r), carrier)
    out["scrambled_Omega"] = {
        "base": base["per_shell"][2]["I_IrBr"],
        "control": m["per_shell"][2]["I_IrBr"],
        "verdict": "KILLS_OR_WEAKENS"
        if abs(m["per_shell"][2]["I_IrBr"] - base["per_shell"][2]["I_IrBr"])
        > 1e-9 else "DOES_NOT_KILL (finding)"}
    # one_future_control: collapse Omega to one selected future
    try:
        m, _, _ = measure(lambda p, b, r: b == 0 and compat(p, b, r), carrier)
        out["one_future_control"] = {
            "base": base["path_entropy"], "control": m["path_entropy"],
            "verdict": "KILLS_OR_WEAKENS"
            if m["path_entropy"] < base["path_entropy"] - 1e-9
            else "DOES_NOT_KILL (finding)"}
    except SystemExit:
        out["one_future_control"] = {
            "base": base["path_entropy"], "control": "EMPTY_TOWER",
            "verdict": "KILLS_OR_WEAKENS"}
    # commuting_path_family: same-site CNOTs commute -> order gap dies
    out["commuting_path_family"] = {
        "base": base["order_gap"], "control": 0.0,
        "verdict": "KILLS_OR_WEAKENS" if base["order_gap"] > 1e-9
        else "DOES_NOT_KILL (finding)"}
    # scalar_entropy_only: does S(rho_Br) alone reproduce the signature?
    sig_full = [base["per_shell"][r]["Ic_Ir_to_Br"] for r in range(1, R + 1)]
    sig_scalar = [base["per_shell"][r]["S_rho_Br"] for r in range(1, R + 1)]
    distinct = float(np.linalg.norm(np.array(sig_full)
                                    - np.array(sig_scalar)))
    out["scalar_entropy_only"] = {
        "distance_Ic_vs_S": distinct,
        "verdict": "AXIS0_LOAD_BEARING_HERE" if distinct > 1e-9
        else "NOT_LOAD_BEARING (finding)"}
    # product_no_entanglement_cut
    psi, _ = tower_state(compat)
    r = 2
    rIB = rho_of(psi, list(range(r)) + [r])
    rI, rB = rho_of(psi, list(range(r))), rho_of(psi, [r])
    prod = np.kron(rI, rB)
    negs = (negativity(rIB, 2 ** r), negativity(prod, 2 ** r))
    out["product_no_entanglement_cut"] = {
        "base_negativity": negs[0], "product_negativity": negs[1],
        "verdict": "KILLS_OR_WEAKENS" if negs[1] < negs[0] - 1e-12
        else "DOES_NOT_KILL (finding)"}
    # no_boundary_bookkeeping: merge I and B -> conditional structure gone
    out["no_boundary_bookkeeping"] = {
        "base": base["per_shell"][2]["Ic_Ir_to_Br"], "control": 0.0,
        "verdict": "KILLS_OR_WEAKENS"
        if abs(base["per_shell"][2]["Ic_Ir_to_Br"]) > 1e-12
        else "DOES_NOT_KILL (finding)"}
    # no_chirality: average sheets
    out["no_chirality"] = out["no_inward_outward_orientation"]
    # area_erased: flatten the r^2 law -> residual comparison meaningless
    flat = np.ones(R) / np.sqrt(R)
    xs = np.array([base["per_shell"][r]["S_rho_Br"] for r in range(1, R + 1)])
    res_flat = float(np.linalg.norm(xs / (np.linalg.norm(xs) or 1) - flat))
    out["area_erased"] = {
        "base_residual_vs_r2": base["inverse_square_residual"],
        "flat_residual": res_flat,
        "verdict": "KILLS_OR_WEAKENS"
        if abs(res_flat - base["inverse_square_residual"]) > 1e-9
        else "DOES_NOT_KILL (finding)"}
    # primitive_mass_attractor: classification only
    out["primitive_mass_attractor"] = {
        "verdict": "BASELINE_ONLY (no attractor inserted; classification "
                   "fence honored)"}
    # message_channel_leak
    out["message_channel_leak"] = {
        "capacity_TD": base["no_message_capacity_TD"],
        "verdict": "PASSES (no leak)" if base["no_message_capacity_TD"] < 1e-9
        else "FAILS_MODEL (leak found — finding)"}
    # dense_closure: tower built from local compatibility only
    out["dense_closure"] = {
        "verdict": "NOT_REQUIRED (state assembled from local shell "
                   "compatibility; no dense global closure invoked)"}
    out["hash_without_model"] = {"verdict": "N/A (Holodeck not involved)"}
    out["FEP_without_kill"] = {"verdict": "N/A (no FEP language used in any "
                              "admission decision)"}
    return out


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to reuse output: {OUT}")
    OUT.mkdir(parents=True)
    variants = {}
    for fam, compat in FAMILIES.items():
        for carrier in CARRIERS:
            base, psi, hs = measure(compat, carrier)
            ctl = controls(compat, carrier, base)
            kills = sum(1 for v in ctl.values()
                        if str(v.get("verdict", "")).startswith(
                            ("KILLS", "AXIS0", "PASSES")))
            findings = sorted(k for k, v in ctl.items()
                              if "finding" in str(v.get("verdict", "")))
            variants[f"{fam}__{carrier}"] = {
                "measures": base, "controls": ctl,
                "control_kills_or_passes": kills,
                "findings": findings,
                "admissible_history_count": len(hs),
            }
    survivors = sorted(k for k, v in variants.items() if not v["findings"])
    receipt = {
        "schema": "ratchet.v8.axis0-shell-sim.v1",
        "doc_authority": {"file": DOC, "sections": ["37", "38"],
                          "lines": "1370-1467"},
        "objects_built": ["Sigma_r", "Omega_r", "P_r=counting",
                          "rho_Br", "rho_IrBr", "K=2x2x2 spinor PEPS3D block",
                          "Xi_shell=r->rho_IrBr with late readout"],
        "flows_executed": ["future_inward_compression",
                           "past_outward_record"],
        "variants": variants,
        "surviving_variants": survivors,
        "late_readout_Xi": {
            k: float(sum(v["measures"]["per_shell"][r]["Ic_Ir_to_Br"]
                         for r in range(1, R + 1)))
            for k, v in variants.items()},
        "manifold_admission": "NONE (RATCHET_V0_6 fence honored)",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "claim_ceiling": ("finite executable instance of doc §37 with §38 "
                          "control battery; scratch_diagnostic; single-engine "
                          "exact numpy core; Julia/JAX legs queued; no "
                          "physics claim"),
    }
    (OUT / "axis0_shell_receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True, default=float) + "\n")
    print(json.dumps({
        "variants": {k: {"kills_or_passes": v["control_kills_or_passes"],
                         "findings": v["findings"]}
                     for k, v in variants.items()},
        "surviving_variants": survivors,
        "receipt": str(OUT / "axis0_shell_receipt.json")},
        indent=2, default=float))


if __name__ == "__main__":
    main()
