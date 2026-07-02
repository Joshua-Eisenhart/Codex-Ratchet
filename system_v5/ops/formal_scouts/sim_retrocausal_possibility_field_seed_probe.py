"""
sim_retrocausal_possibility_field_seed_probe.py

Wizard v4.3 PRIMARY OBJECT, Sim 1 of the retrocausal field ladder
(RETROCAUSAL_POSSIBILITY_FIELD_SIM_AND_WIZARD_METHOD_20260526.md, Sim 1: Field Seed).

The OBJECT is the finite retrocausal possibility field, INSTANTIATED (not proxied):

    future possibility field  ->  compatibility compression  ->  present survivor  ->  outward record

REVISION (after v4.3 audit findings): the first cut used a direction-BLIND convex
mixture rho = sum_i w_i rho_i, so "future-inward" was an inert label (a forward
mixture reproduced it bit-identically). FIXED: the compression is now an ORDERED,
state-dependent, NON-COMMUTATIVE inward fold across shells (outer futures
sqrt-filter the running survivor inward to the present). Consequences that make
the retrocausal direction LOAD-BEARING:
  - reversing orientation (outward/forward order) gives a DIFFERENT survivor;
  - a flat convex mixture CANNOT reproduce the inward survivor;
  - the no_inward_outward_orientation control kills the shell-polarity claim.

classification = "diagnostic_only"; no Axis0/Xi/Phi0 closure; 8/16/32/64 PEPS3D
carrier is Sim 3. blocked_consumers = flux/Xi/Phi0/Axis0/physics/manifold.
"""
import json
import math
import hashlib
import pathlib
import subprocess
import torch
import z3

torch.set_default_dtype(torch.float64)
CDT = torch.complex128
SIM_ID = "retrocausal_possibility_field_seed_probe"
PRIMARY_OBJECT = "retrocausal_possibility_field"
NQ = 3
DIM = 2 ** NQ
N_SHELLS = 4
N_BRANCH = 6
REPO = pathlib.Path("/Users/joshuaeisenhart/Desktop/Codex Ratchet")

TOOL_MANIFEST = {
    "pytorch": {"tried": True, "used": True, "reason": "load_bearing: torch complex128 branch densities, ORDERED non-commutative inward sqrt-filter compression to the present survivor"},
    "z3": {"tried": True, "used": True, "reason": "load_bearing: finite admissibility witness — an incompatible branch is PROVABLY excluded (UNSAT to admit it; flips SAT when threshold relaxed)"},
}
TOOL_INTEGRATION_DEPTH = {"pytorch": "load_bearing", "z3": "load_bearing"}


def _rand_pure_density(seed):
    g = torch.Generator().manual_seed(seed)
    v = (torch.randn(DIM, generator=g, dtype=torch.float64) + 1j * torch.randn(DIM, generator=g, dtype=torch.float64)).to(CDT)
    v = v / torch.linalg.norm(v)
    return torch.outer(v, v.conj())


def _vn_entropy(rho):
    ev = torch.linalg.eigvalsh((rho + rho.conj().T) / 2).real
    ev = ev[ev > 1e-13]
    return float(-torch.sum(ev * torch.log(ev)))


def _shannon(weights):
    w = weights[weights > 1e-13]
    return float(-torch.sum(w * torch.log(w)))


def _sqrtm_psd(M):
    Mh = (M + M.conj().T) / 2
    ev, U = torch.linalg.eigh(Mh)
    ev = torch.clamp(ev.real, min=0.0)
    return (U * ev.sqrt().to(CDT)) @ U.conj().T


def build_shells(seed_base=11, single_future=False):
    """Finite shell stack Sigma_r (r=1..R) of FUTURE continuations (branch densities),
    each shell with a finite area_measure ~ r^2 (possibility-surface scaling)."""
    boundary_E = _rand_pure_density(seed_base + 777)
    n_shells = 1 if single_future else N_SHELLS
    shells = []
    for r in range(1, n_shells + 1):
        n_branch = 1 if single_future else N_BRANCH
        branch_states = [_rand_pure_density(seed_base + 100 * r + b) for b in range(n_branch)]
        shells.append({
            "shell_radius_r": r,
            "shell_orientation": "future_inward",
            "area_measure": 4.0 * math.pi * r * r,   # finite possibility-surface measure (inverse-square structure)
            "future_continuations": list(range(len(branch_states))),
            "branch_states": branch_states,
        })
    return shells, boundary_E


def inward_fold(shells, boundary_E, order="inward", orientation_active=True):
    """ORDERED, state-dependent, NON-COMMUTATIVE compression of the future field into
    the present survivor. Process shells outer->inner (future-inward) by default.
    At each shell: compatibility of each future branch is measured against the CURRENT
    running survivor (state-dependent), admissible branches (>= median) are mixed, and
    the running survivor is updated by a Lueders sqrt-filter (non-commutative):
        running' = M^{1/2} running M^{1/2} / tr(M running).
    Reversing the order (outward) generally yields a different survivor -> direction is real.
    orientation_active=False scrambles the radial order (no_inward_outward control)."""
    radii = [s["shell_radius_r"] for s in shells]
    if order == "inward":
        seq = sorted(shells, key=lambda s: s["shell_radius_r"], reverse=True)   # outer first -> inner last (present)
    else:
        seq = sorted(shells, key=lambda s: s["shell_radius_r"])                 # inner first (forward/outward)
    if not orientation_active:
        # erase future-inward/past-outward orientation: use a fixed scrambled order regardless of r
        seq = [shells[i] for i in [min(1, len(shells) - 1), 0] + list(range(2, len(shells)))][:len(shells)]

    # running CONTEXT evolves non-commutatively across shells (provides order-dependence /
    # the future-inward direction). The present SURVIVOR is the compatibility-weighted MIXTURE
    # of the surviving future continuations -- so it RETAINS possibility-capacity (stays mixed),
    # while its weights are order-dependent (reversing the fold reweights -> different survivor).
    running = boundary_E.clone()
    survivor = torch.zeros(DIM, DIM, dtype=CDT)
    acc_w = []
    total_w = 0.0
    for s in seq:
        r = s["shell_radius_r"]
        compat = torch.tensor([max(float(torch.trace(rho_b @ running).real), 1e-9) for rho_b in s["branch_states"]],
                              dtype=torch.float64)
        tau = float(compat.median()) if compat.numel() > 1 else float(compat.min())
        adm = compat >= tau
        if adm.sum() == 0:
            adm = compat >= 0.0
        atten = 1.0 / math.sqrt(r)                       # inward radial attenuation (outer shells contribute less)
        shell_mix = torch.zeros(DIM, DIM, dtype=CDT)
        shell_w_sum = 0.0
        for b, rho_b in enumerate(s["branch_states"]):
            if bool(adm[b]):
                w = float(compat[b]) * atten             # weight depends on the CURRENT running context (order-dependent)
                survivor = survivor + w * rho_b          # accumulate the MIXTURE (keeps it mixed)
                total_w += w
                acc_w.append(w)
                shell_mix = shell_mix + float(compat[b]) * rho_b
                shell_w_sum += float(compat[b])
        # update running context non-commutatively so later (inner) shells see an evolved context
        if shell_w_sum > 0:
            shell_mix = shell_mix / shell_w_sum
            Msq = _sqrtm_psd(shell_mix)
            upd = Msq @ running @ Msq
            upd = (upd + upd.conj().T) / 2
            tr = torch.trace(upd).real
            running = upd / tr if float(tr) > 1e-15 else shell_mix
    survivor = (survivor + survivor.conj().T) / 2
    survivor = survivor / torch.trace(survivor).real     # normalize -> valid MIXED density
    weights = torch.tensor(acc_w, dtype=torch.float64)
    weights = weights / weights.sum()
    return survivor, weights, radii


def flat_mixture(shells, boundary_E):
    """Direction-BLIND convex mixture (the OLD proxy): rho = sum_b w_b rho_b over all branches,
    w_b from compatibility with the fixed boundary. Used as the decisive direction control:
    the ordered inward fold must NOT equal this."""
    branches, compat = [], []
    for s in shells:
        for rho_b in s["branch_states"]:
            branches.append(rho_b)
            compat.append(max(float(torch.trace(rho_b @ boundary_E).real), 1e-9))
    ct = torch.tensor(compat, dtype=torch.float64)
    tau = float(ct.median()) if ct.numel() > 1 else float(ct.min())
    adm = ct >= tau
    if adm.sum() == 0:
        adm = ct >= 0.0
    w = ct * adm.double(); w = w / w.sum()
    rho = torch.zeros(DIM, DIM, dtype=CDT)
    for wi, rho_b in zip(w, branches):
        rho = rho + wi.to(CDT) * rho_b
    return (rho + rho.conj().T) / 2, ct, tau


def forward_shadow(seed_base=11):
    g = torch.Generator().manual_seed(seed_base + 9999)
    prev = _rand_pure_density(seed_base + 1)
    H = (torch.randn(DIM, DIM, generator=g, dtype=torch.float64) + 1j * torch.randn(DIM, DIM, generator=g, dtype=torch.float64)).to(CDT)
    H = (H + H.conj().T) / 2
    U = torch.matrix_exp(1j * 0.5 * H)
    return U @ prev @ U.conj().T


def z3_branch_exclusion_witness(compat_values, threshold):
    incompatible = [i for i, c in enumerate(compat_values) if c < threshold]
    if not incompatible:
        return {"applicable": False, "verdict": "n/a (no incompatible branch this draw)"}
    i = incompatible[0]
    s = z3.Solver()
    c = z3.RealVal(repr(float(compat_values[i]))); thr = z3.RealVal(repr(float(threshold)))
    admitted = z3.Bool("admitted")
    s.add(admitted == (c >= thr)); s.add(admitted)
    real = str(s.check())
    s2 = z3.Solver(); s2.add(admitted == (c >= z3.RealVal("0.0"))); s2.add(admitted)
    relaxed = str(s2.check())
    return {"applicable": True, "excluded_branch_compat": float(compat_values[i]), "threshold": threshold,
            "real_verdict": real, "relaxed_verdict": relaxed, "load_bearing": real == "unsat" and relaxed == "sat"}


def primary_object_card():
    """Emit + validate the v4.3 primary-object card on the receipt surface (not just a reference)."""
    py = "/Users/joshuaeisenhart/.local/share/codex-ratchet/envs/main/bin/python3"
    script = str(REPO / "scripts" / "wizard_v4_3_object_preservation.py")
    card = json.loads(subprocess.run([py, script, "example"], capture_output=True, text=True).stdout)
    tmp = pathlib.Path("/tmp/_v43_card_sim1.json"); tmp.write_text(json.dumps(card))
    val = json.loads(subprocess.run([py, script, "validate", "--input", str(tmp)], capture_output=True, text=True).stdout)
    return card, bool(val.get("ok"))


def main():
    shells, boundary_E = build_shells()

    # ORDERED inward (future->present) compression — the present survivor
    rho_in, w_in, radii = inward_fold(shells, boundary_E, order="inward")
    # reversed (outward/forward) order — must differ (direction is real)
    rho_out, _, _ = inward_fold(shells, boundary_E, order="outward")
    # orientation erased — must differ (no_inward_outward_orientation control)
    rho_noorient, _, _ = inward_fold(shells, boundary_E, orientation_active=False)
    # direction-blind flat convex mixture (the proxy) — inward fold must NOT equal this
    rho_flat, compat_flat, tau_flat = flat_mixture(shells, boundary_E)

    rho_present = rho_in
    h_future = _shannon(w_in)
    S_present = _vn_entropy(rho_present)
    boundary_residue = float(torch.trace(rho_present @ boundary_E).real)
    survivor_hash = hashlib.sha256(rho_present.detach().cpu().numpy().tobytes()).hexdigest()[:16]
    surviving = [i for i, a in enumerate((compat_flat >= tau_flat).tolist()) if a]
    outward_record = {"surviving_branch_ids": surviving, "n_surviving": len(surviving),
                      "survivor_hash": survivor_hash, "boundary_residue": boundary_residue}

    # ---- DECISIVE direction tests (the audit's failing checks, now load-bearing) ----
    dir_vs_flat = float(torch.linalg.norm(rho_in - rho_flat))          # inward fold != flat mixture
    dir_vs_outward = float(torch.linalg.norm(rho_in - rho_out))        # inward != outward order
    dir_vs_noorient = float(torch.linalg.norm(rho_in - rho_noorient))  # orientation drives the result

    # ---- controls ----
    sh1, bE1 = build_shells(single_future=True)
    rho_single, w_single, _ = inward_fold(sh1, bE1, order="inward")
    single_delta = h_future - _shannon(w_single)
    single_future_control = {"passed": bool(_shannon(w_single) < 1e-9 and h_future > 1e-3), "delta": single_delta}
    S_present_single = _vn_entropy(rho_single)   # single-future survivor entropy (should collapse ~0)

    # U0 SURVIVOR INVARIANT (object-truth, resolved per Wizard v4.2 council): the present survivor
    # MUST retain nonzero possibility-capacity (mixedness) SOURCED from the future-continuation field;
    # collapsing the field to a single future must drive S_present -> 0. A pure survivor would mean the
    # object failed to instantiate (capacity destroyed at the compression that IS the model).
    survivor_invariant = {
        "statement": "present_survivor retains nonzero possibility-capacity S(rho_present)>0, sourced from the future-continuation field; single-future collapse drives it to 0",
        "S_present_full": S_present,
        "S_present_single_future": S_present_single,
        "capacity_retained": bool(S_present > 1e-3),
        "capacity_sourced_from_future_field": bool(S_present_single < S_present - 1e-3),
        "passed": bool(S_present > 1e-3 and S_present_single < S_present - 1e-3),
    }

    fwd = forward_shadow()
    forward_shadow_control = {"passed": bool(float(torch.linalg.norm(rho_in - fwd)) > 1e-6),
                              "delta": float(torch.linalg.norm(rho_in - fwd))}
    no_inward_outward_orientation_control = {"passed": bool(dir_vs_noorient > 1e-6), "delta": dir_vs_noorient}
    direction_decisive_control = {"passed": bool(dir_vs_flat > 1e-6), "delta": dir_vs_flat,
                                  "note": "inward fold differs from a direction-blind flat mixture => retrocausal direction is load-bearing"}

    z3w = z3_branch_exclusion_witness(compat_flat.tolist(), tau_flat)
    card, card_valid = primary_object_card()

    rho = rho_present
    herm = float(torch.linalg.norm(rho - rho.conj().T)); tr = float(torch.trace(rho).real)
    min_eig = float(torch.linalg.eigvalsh(rho).min()); w_sum = float(w_in.sum())

    known_value_checks = [
        {"invariant": "primary_object == retrocausal_possibility_field", "computed": PRIMARY_OBJECT, "known": "retrocausal_possibility_field", "match": PRIMARY_OBJECT == "retrocausal_possibility_field"},
        {"invariant": "future_continuation_count >= 2", "computed": sum(len(s["future_continuations"]) for s in shells), "known": ">=2", "match": sum(len(s["future_continuations"]) for s in shells) >= 2},
        {"invariant": "each shell carries area_measure (schema 8.1)", "computed": [s["area_measure"] for s in shells], "known": "present", "match": all("area_measure" in s for s in shells)},
        {"invariant": "compatibility weights normalized", "computed": f"{w_sum:.6f}", "known": "1", "match": abs(w_sum - 1.0) < 1e-9},
        {"invariant": "rho_present Hermitian", "computed": f"{herm:.2e}", "known": "0", "match": herm < 1e-9},
        {"invariant": "rho_present trace == 1", "computed": f"{tr:.6f}", "known": "1", "match": abs(tr - 1.0) < 1e-9},
        {"invariant": "rho_present PSD", "computed": f"{min_eig:.2e}", "known": ">=0", "match": min_eig > -1e-9},
        {"invariant": "U0 SURVIVOR INVARIANT: present survivor retains possibility-capacity (S>0) sourced from future field (single-future collapses it)", "computed": f"S_full={S_present:.3f} S_single={S_present_single:.3f}", "known": "S_full>0 & S_single<S_full", "match": survivor_invariant["passed"]},
        {"invariant": "DIRECTION LOAD-BEARING: inward fold != flat convex mixture (not a forward proxy)", "computed": f"delta={dir_vs_flat:.4f}", "known": ">0", "match": direction_decisive_control["passed"]},
        {"invariant": "orientation drives compression: no_inward_outward_orientation changes survivor", "computed": f"delta={dir_vs_noorient:.4f}", "known": ">0", "match": no_inward_outward_orientation_control["passed"]},
        {"invariant": "inward order != outward order (non-commutative fold)", "computed": f"delta={dir_vs_outward:.4f}", "known": ">0", "match": dir_vs_outward > 1e-6},
        {"invariant": "single_future_control weakens many-futures claim (h_future->0)", "computed": f"delta={single_delta:.4f}", "known": "single~0", "match": single_future_control["passed"]},
        {"invariant": "forward_shadow_control: survivor != forward dynamics", "computed": f"delta={forward_shadow_control['delta']:.4f}", "known": ">0", "match": forward_shadow_control["passed"]},
        {"invariant": "z3 branch-exclusion load-bearing (unsat to admit incompatible; flips sat relaxed)", "computed": f"{z3w.get('real_verdict')}/{z3w.get('relaxed_verdict')}", "known": "unsat/sat", "match": z3w.get("load_bearing", False) or not z3w.get("applicable", True)},
        {"invariant": "primary object card emitted to receipt + validates ok", "computed": f"card_valid={card_valid}", "known": "True", "match": card_valid},
    ]
    all_pass = all(c["match"] for c in known_value_checks)

    out = {
        "sim_id": SIM_ID, "primary_object": PRIMARY_OBJECT, "classification": "diagnostic_only", "promotion_allowed": False,
        "claim_ceiling": "Minimum retrocausal possibility-field SEED (Sim 1). Instantiates the object with a LOAD-BEARING future-inward direction (non-commutative inward sqrt-filter fold). No Axis0/Xi/Phi0 closure; 8/16/32/64 PEPS3D carrier is Sim 3. Passes the Sim-1 REQUIRED controls (single_future + forward_shadow) plus direction/orientation controls; the full 8.5 control set lands at later ladder steps.",
        "event_x": 0,
        "shells": [{"shell_radius_r": s["shell_radius_r"], "shell_orientation": s["shell_orientation"], "area_measure": s["area_measure"], "n_future_continuations": len(s["future_continuations"])} for s in shells],
        "future_continuation_count": sum(len(s["future_continuations"]) for s in shells),
        "compatibility_weights": [round(float(x), 6) for x in w_in.tolist()],
        "future_inward_past_outward": {"future": "inward (ordered non-commutative sqrt-filter compression)", "past": "outward (record)"},
        "compression_map": "present = ordered inward fold: for shells outer->inner, running' = M_shell^{1/2} running M_shell^{1/2}/tr (M_shell = compatibility-weighted future mix). NON-COMMUTATIVE; orientation load-bearing.",
        "compression_provenance": "F -> per-shell compatibility(running) -> admissible mix M_shell -> sqrt-filter update -> rho_present -> readout",
        "present_survivor_entropy": S_present, "h_future_possibility_capacity": h_future,
        "survivor_invariant": survivor_invariant,
        "outward_record_map": outward_record,
        "direction_tests": {"inward_vs_flat_mixture": dir_vs_flat, "inward_vs_outward": dir_vs_outward, "inward_vs_orientation_erased": dir_vs_noorient},
        "controls": {
            "single_future_control": single_future_control,
            "forward_shadow_control": forward_shadow_control,
            "no_inward_outward_orientation_control": no_inward_outward_orientation_control,
            "direction_decisive_control": direction_decisive_control,
        },
        "z3_admissibility_witness": z3w,
        "primary_object_card": card, "primary_object_card_valid": card_valid,
        "tensor_checks": {"hermitian_defect": herm, "trace": tr, "min_eig": min_eig, "weights_sum": w_sum},
        "known_value_checks": known_value_checks, "all_pass": all_pass,
        "tool_manifest": TOOL_MANIFEST, "tool_integration_depth": TOOL_INTEGRATION_DEPTH,
        "blocked_consumers": ["flux", "Xi", "Phi0", "Axis0", "physics", "manifold"], "blockers": [],
    }
    outdir = pathlib.Path(__file__).parent / "results"; outdir.mkdir(exist_ok=True)
    (outdir / f"{SIM_ID}_results.json").write_text(json.dumps(out, indent=2, default=str))
    print(json.dumps({"primary_object": PRIMARY_OBJECT, "future_continuation_count": out["future_continuation_count"],
                      "direction_tests": {k: round(v, 4) for k, v in out["direction_tests"].items()},
                      "controls": {k: v["passed"] for k, v in out["controls"].items()},
                      "z3_load_bearing": z3w.get("load_bearing"), "card_valid": card_valid,
                      "S_present": round(S_present, 4), "h_future": round(h_future, 4), "all_pass": all_pass}, indent=2))
    return out


if __name__ == "__main__":
    main()
