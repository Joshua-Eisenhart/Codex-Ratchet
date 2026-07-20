#!/usr/bin/env python3
"""SCHEDULE TOURNAMENT v0: let the constraint manifold ADMIT the cycle order.

Replaces stage64 construction identities with MEASURED walls.
The D,H,D,H microstep adaptor is treated as a candidate, not installed truth.
All gates can fail. Controls are required to fail. Honest outcome.

Reference thresholds are taken from the canonical D,H,D,H run BEFORE any
alternative is scored. Admission is uniform and preregistered.

Micro orders: all 24 permutations of the four microstep roles ("D","H","D","H")
  per stage (declared count; many equivalent under repeated roles).

Macro orders: permutations of the 8 stages per engine (W+, W-) that respect
  the outer/inner engine split (W+ block and W- block never interleaved).
  Within each engine we enumerate all 4! family-block reorderings (families
  0-3), keeping the L/R sheet order inside each family as in the source
  (declared count: 24 macro family orders; applied symmetrically to both
  engines).

Measurements per candidate (composed engine, reuse v1 micro machinery):
  - monodromy defect: ||U_minus - inv(U_plus)||_F on the 16x16 superops after
    one full composed pass over the (ordered) stages using the candidate
    micro role sequence.
  - chirality flux split: signed proxy (difference of a chiral marker yy
    readout after separate W+ vs W- composed action on a probe); sign-consistency
    against reference.
  - terrain distinctness: min pairwise fingerprint distance (L07-style 7-axis
    fingerprint with the candidate micro order inside the four-step products).
  - stability margin: under 50 random coherent frame perturbations (smaller
    budget than jax_scale_lanes L14 1600-pt); fraction or min eps at which
    monodromy defect exceeds the preregistered mono threshold.

Admission (preregistered, thresholds from DHDH reference):
  survives iff
    monodromy_defect < MONO_THRESH and
    flux_split sign-consistent and
    terrain_min_dist > TERRAIN_FLOOR

Controls (must fail admission):
  - scrambled-composition: bad micro (D D H H) + reversed family macro.
  - known-degenerate raw stage-order: the scrambled_stage_order case from
    manifold_unified_v2 (endpoint distance flips; monodromy destroyed).
  - at least one additional expected-fail (all-H-then-D micro, reverse-family).

Interpreter: /Users/joshuaeisenhart/.local/share/sim-stack/bin/python3
One heavy stack per subprocess (fresh python -c per candidate via that interp).
No file deletion. No commit.

Receipt written under results/schedule_tournament_v0/receipt.json
classification=scratch_diagnostic, promotion_allowed=false.

Final line reports: SCHEDULE TOURNAMENT: N candidates, M survivors, DHDH status: <unique|plural|failed>.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import torch

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from system_v8.unified import manifold_unified_v1 as v1
from system_v8.nested_manifold import manifold_one as manifold

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "schedule_tournament_v0"
SIM_INTERPRETER = "/Users/joshuaeisenhart/.local/share/sim-stack/bin/python3"
DTYPE = v1.DTYPE
RD = v1.RD
I4 = v1.I4
I16 = torch.eye(16, dtype=DTYPE)

SOURCE_FILES = [
    REPO / "system_v8/unified/manifold_unified_v1.py",
    REPO / "system_v8/unified/manifold_unified_v2.py",
    REPO / "system_v8/nested_manifold/manifold_one.py",
    REPO / "system_v8/nested_manifold/stage64_constraint_tournament.py",
]

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def serial(value: Any) -> Any:
    return v1.serial(value)

def vn_entropy_bits(rho: torch.Tensor) -> float:
    herm = 0.5 * (rho + rho.mH)
    values = torch.clamp(torch.linalg.eigvalsh(herm).real, min=1e-15)
    return float(-torch.sum(values * torch.log2(values)))

def apply_superop(superop: torch.Tensor, rho: torch.Tensor) -> torch.Tensor:
    return v1.normalize_outer(v1.unvec_f(superop @ v1.vec_f(rho)))[0]

def macro_channel_for_order(stage: dict[str, Any], role_order: list[str]) -> torch.Tensor:
    """Compose exp(dt * gen(role)) in the given role_order (length 4)."""
    mats = []
    for role in role_order:
        g = v1.local_generator(stage, role)
        mats.append(torch.matrix_exp(v1.MICRO_DT * g))
    out = torch.eye(16, dtype=DTYPE)
    for m in mats:
        out = m @ out
    return out

def build_stage_lists():
    """Return the canonical plus/minus stage lists (source-selected order)."""
    plus, minus, _ = v1.source_stages(0.8, -2.0)
    return plus, minus

def compose_U_for_engine(stages: list[dict[str, Any]], role_order: list[str]) -> torch.Tensor:
    """Product superop for one engine (W+ or W-) under candidate order."""
    U = torch.eye(16, dtype=DTYPE)
    for st in stages:
        U = macro_channel_for_order(st, role_order) @ U
    return U

def monodromy_defect(U_plus: torch.Tensor, U_minus: torch.Tensor) -> float:
    """||U_minus - inv(U_plus)||_F . Small is good (preserves conjugate relation)."""
    try:
        inv_plus = torch.linalg.inv(U_plus)
    except Exception:
        inv_plus = torch.linalg.pinv(U_plus)
    diff = U_minus - inv_plus
    return float(torch.linalg.norm(diff))

def terrain_fingerprints_with_order(stages: list[dict[str, Any]], role_order: list[str]) -> list[torch.Tensor]:
    """L07-style 7-axis fingerprints, but using the candidate 4-step order inside."""
    rho_probe = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    vecs = []
    for st in stages:
        # Build the four matrices in role_order (D and H from this stage)
        d = torch.matrix_exp(v1.MICRO_DT * v1.local_generator(st, "D"))
        h = torch.matrix_exp(v1.MICRO_DT * v1.local_generator(st, "H"))
        # Map role_order to actual ops (roles are labels; D/H repeated)
        seq = []
        for r in role_order:
            seq.append(d if r == "D" else h)
        rho0 = rho_probe
        rhos = [rho0]
        for m in seq:
            rhos.append(apply_superop(m, rhos[-1]))
        # Use the same 7 coordinates as v2 stage_fingerprint (order-sensitive ones included)
        pauli = lambda r: torch.tensor(v1.pauli_readout(r)[:3], dtype=RD)
        init = pauli(rhos[0])
        d_vec = pauli(rhos[1])
        h_vec = pauli(rhos[2])
        dh_vec = pauli(rhos[3])  # after two
        dhdh_vec = pauli(rhos[4])
        # axis4 order gap uses the full product vs its swap (here we approximate by dhdh vs a swapped pattern)
        # For the candidate order we compute a proxy swap distance against a canonical DHDH on same stage
        dhdh_canon = apply_superop(h @ d @ h @ d, rho0)
        order_gap = v1.trace_distance(rhos[4], dhdh_canon)
        vals = [
            float(torch.dot(d_vec - init, torch.linalg.cross(h_vec - init, dh_vec - init))),
            vn_entropy_bits(rhos[1]) - vn_entropy_bits(rho0),
            v1.pauli_readout(rhos[4])[3],
            float(torch.linalg.norm(pauli(rhos[4]) - init)),
            order_gap,
            vn_entropy_bits(rhos[2]) - vn_entropy_bits(rhos[1]),
            v1.trace_distance(apply_superop(d @ h, rho0), apply_superop(h @ d, rho0)),
        ]
        vecs.append(torch.tensor(vals, dtype=RD))
    return vecs

def min_pairwise_terrain_dist(stages: list[dict[str, Any]], role_order: list[str]) -> float:
    vecs = terrain_fingerprints_with_order(stages, role_order)
    dists = [float(torch.linalg.norm(vecs[i] - vecs[j])) for i in range(len(vecs)) for j in range(i + 1, len(vecs))]
    return min(dists) if dists else 0.0

def chirality_flux_split_proxy(stages_plus: list[dict[str, Any]], stages_minus: list[dict[str, Any]], role_order: list[str]) -> tuple[float, int]:
    """Signed proxy for chirality split under the composed order.
    Applies the full engine product for + and for - to a probe and reads a chiral marker (yy component difference).
    Returns (split_value, sign).
    """
    rho0 = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    U_plus = compose_U_for_engine(stages_plus, role_order)
    U_minus = compose_U_for_engine(stages_minus, role_order)
    rho_p = apply_superop(U_plus, rho0)
    rho_m = apply_superop(U_minus, rho0)
    yy_p = v1.pauli_readout(rho_p)[3]
    yy_m = v1.pauli_readout(rho_m)[3]
    split = float(yy_p - yy_m)
    sgn = 1 if split > 0 else (-1 if split < 0 else 0)
    return split, sgn

def stability_margin_under_perturbations(stages_plus: list[dict[str, Any]], stages_minus: list[dict[str, Any]], role_order: list[str], n_pert: int = 50, base_defect: float = 0.0) -> dict[str, Any]:
    """50 random coherent frame perturbations (smaller budget).
    Perturb the hamiltonian axis sigma by a small random rotation on the Bloch sphere.
    Recompute monodromy defect; record fraction that stay below 2*base_defect + 1e-4 and the smallest eps that breaks.
    """
    random.seed(20260720)
    breaks = []
    survived = 0
    eps_vals = []
    for _ in range(n_pert):
        eps = random.uniform(0.01, 0.8)  # smaller budget than 1.5
        # random axis for rotation (small coherent frame tilt)
        ax = torch.tensor([random.gauss(0,1), random.gauss(0,1), random.gauss(0,1)], dtype=RD)
        ax = ax / (torch.norm(ax) + 1e-12)
        # Build rotation R = exp(-i (eps/2) n.sigma) on 2d
        nsigma = ax[0]*v1.stage64.SX + ax[1]*v1.stage64.SY + ax[2]*v1.stage64.SZ
        R = torch.matrix_exp(-1j * (eps / 2.0) * torch.tensor(nsigma, dtype=DTYPE))
        # Perturb: we tilt the "b" axis for H by conjugating the SIG[b] inside a patched local_generator path.
        # For isolation we patch only the H generator construction for this measurement.
        # Simpler: scale the H strength by (1+eps*0.5) with random sign flip on one family to simulate frame tilt.
        # To stay faithful to "coherent frame perturbation" we rotate the b-axis operator for all stages.
        orig_local = v1.local_generator
        def patched_local(stage, role):
            if role != "H":
                return orig_local(stage, role)
            # rotate the b sigma
            sig = torch.tensor(v1.stage64.SIG[stage["b"]], dtype=DTYPE)
            sig_p = R @ sig @ R.mH
            # rebuild only the H part
            h_local = stage["source_h_sign"] * stage["omega"] * sig_p
            if stage["sheet"] == "L":
                h = torch.kron(h_local, v1.I2)
            else:
                h = torch.kron(v1.I2, h_local)
            identity = v1.I4
            return -1j * (torch.kron(identity, h) - torch.kron(h.T.contiguous(), identity))
        # Temporarily swap
        v1.local_generator = patched_local  # type: ignore
        try:
            Up = compose_U_for_engine(stages_plus, role_order)
            Um = compose_U_for_engine(stages_minus, role_order)
            d = monodromy_defect(Up, Um)
        finally:
            v1.local_generator = orig_local  # type: ignore
        eps_vals.append(eps)
        if d > (2.0 * base_defect + 1e-4):
            breaks.append(eps)
        else:
            survived += 1
    min_break = min(breaks) if breaks else 1.0
    frac_survive = survived / float(n_pert)
    return {
        "n_pert": n_pert,
        "frac_survive_below_break": frac_survive,
        "min_break_eps": float(min_break),
        "mean_eps_sampled": float(sum(eps_vals) / len(eps_vals)),
    }

def run_reference_once() -> dict[str, Any]:
    """Run the canonical D,H,D,H once; return metrics and thresholds."""
    plus, minus = build_stage_lists()
    role_order = ["D", "H", "D", "H"]
    U_plus = compose_U_for_engine(plus, role_order)
    U_minus = compose_U_for_engine(minus, role_order)
    defect = monodromy_defect(U_plus, U_minus)
    split, sgn = chirality_flux_split_proxy(plus, minus, role_order)
    terrain = min_pairwise_terrain_dist(plus + minus, role_order)
    stab = stability_margin_under_perturbations(plus, minus, role_order, n_pert=50, base_defect=defect)
    return {
        "monodromy_defect": defect,
        "flux_split": split,
        "flux_split_sign": sgn,
        "terrain_min_dist": terrain,
        "stability": stab,
    }

def evaluate_candidate(plus: list[dict[str, Any]], minus: list[dict[str, Any]], micro_order: list[str], macro_family_perm: list[int]) -> dict[str, Any]:
    """Build reordered stage lists from family perm, compose, measure."""
    # Rebuild canonical lists then reorder by family perm (keep L/R relative order inside family)
    # Canonical plus order is family0 L, family0 R, family1 L, ...
    def reorder_engine(stages: list[dict[str, Any]], fam_perm: list[int]) -> list[dict[str, Any]]:
        by_fam: dict[str, list[dict[str, Any]]] = {}
        for s in stages:
            by_fam.setdefault(s["family"], []).append(s)
        # within each fam keep source order (L before R for W+)
        ordered = []
        for fi in fam_perm:
            fam = f"family_{fi}"
            ordered.extend(by_fam.get(fam, []))
        return ordered
    plus_ord = reorder_engine(plus, macro_family_perm)
    minus_ord = reorder_engine(minus, macro_family_perm)
    U_plus = compose_U_for_engine(plus_ord, micro_order)
    U_minus = compose_U_for_engine(minus_ord, micro_order)
    defect = monodromy_defect(U_plus, U_minus)
    split, sgn = chirality_flux_split_proxy(plus_ord, minus_ord, micro_order)
    terrain = min_pairwise_terrain_dist(plus_ord + minus_ord, micro_order)
    stab = stability_margin_under_perturbations(plus_ord, minus_ord, micro_order, n_pert=50, base_defect=defect)
    return {
        "micro_order": micro_order,
        "macro_family_perm": macro_family_perm,
        "monodromy_defect": defect,
        "flux_split": split,
        "flux_split_sign": sgn,
        "terrain_min_dist": terrain,
        "stability": stab,
    }

def is_scrambled_control(micro: list[str], macro: list[int]) -> bool:
    return micro == ["D", "D", "H", "H"] and macro == [3, 2, 1, 0]

def is_raw_degenerate(micro: list[str], macro: list[int]) -> bool:
    # The known degenerate: reverse within families or the equivalent of scrambled stage order.
    # We treat full family reversal as the "raw stage-order" proxy that destroyed monodromy in full sim.
    return micro == ["D", "H", "D", "H"] and macro == [3, 2, 1, 0]

def admission_ok(m: dict[str, Any], mono_th: float, terrain_floor: float, ref_sign: int) -> bool:
    return (
        m["monodromy_defect"] < mono_th and
        m["flux_split_sign"] == ref_sign and
        m["terrain_min_dist"] > terrain_floor
    )

def run_one_subprocess(spec: dict[str, Any]) -> dict[str, Any]:
    """Run one candidate (or control) in a fresh heavy-stack subprocess with the fixed interpreter.
    spec carries micro_order, macro_family_perm, plus_ref, minus_ref (ids only).
    """
    code = f"""
import sys, json, torch
sys.path.insert(0, '{REPO}')
from system_v8.unified import manifold_unified_v1 as v1
from system_v8.nested_manifold import manifold_one as manifold
DTYPE = v1.DTYPE
RD = v1.RD
def apply_superop(superop, rho):
    return v1.normalize_outer(v1.unvec_f(superop @ v1.vec_f(rho)))[0]
def macro_channel_for_order(stage, role_order):
    mats = []
    for role in role_order:
        g = v1.local_generator(stage, role)
        mats.append(torch.matrix_exp(v1.MICRO_DT * g))
    out = torch.eye(16, dtype=DTYPE)
    for m in mats: out = m @ out
    return out
def compose_U_for_engine(stages, role_order):
    U = torch.eye(16, dtype=DTYPE)
    for st in stages: U = macro_channel_for_order(st, role_order) @ U
    return U
def monodromy_defect(U_plus, U_minus):
    try: inv = torch.linalg.inv(U_plus)
    except: inv = torch.linalg.pinv(U_plus)
    return float(torch.linalg.norm(U_minus - inv))
def terrain_fingerprints_with_order(stages, role_order):
    rho_probe = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    vecs = []
    for st in stages:
        d = torch.matrix_exp(v1.MICRO_DT * v1.local_generator(st, 'D'))
        h = torch.matrix_exp(v1.MICRO_DT * v1.local_generator(st, 'H'))
        seq = [d if r=='D' else h for r in role_order]
        rhos = [rho_probe]
        for m in seq: rhos.append(apply_superop(m, rhos[-1]))
        pauli = lambda r: torch.tensor(v1.pauli_readout(r)[:3], dtype=RD)
        init = pauli(rhos[0])
        d_vec = pauli(rhos[1]); h_vec = pauli(rhos[2]); dh_vec = pauli(rhos[3])
        dhdh_canon = apply_superop(h @ d @ h @ d, rho_probe)
        order_gap = float(torch.linalg.norm(v1.unvec_f(v1.vec_f(rhos[4])) - v1.unvec_f(v1.vec_f(dhdh_canon))))
        vals = [
            float(torch.dot(d_vec - init, torch.linalg.cross(h_vec - init, dh_vec - init))),
            float(vn_entropy_bits(rhos[1]) - vn_entropy_bits(rho_probe)),
            v1.pauli_readout(rhos[4])[3],
            float(torch.linalg.norm(pauli(rhos[4]) - init)),
            order_gap,
            float(vn_entropy_bits(rhos[2]) - vn_entropy_bits(rhos[1])),
            float(torch.linalg.norm(v1.unvec_f(v1.vec_f(apply_superop(d @ h, rho_probe))) - v1.unvec_f(v1.vec_f(apply_superop(h @ d, rho_probe))))),
        ]
        vecs.append(torch.tensor(vals, dtype=RD))
    return vecs
def min_pairwise_terrain_dist(stages, role_order):
    vecs = terrain_fingerprints_with_order(stages, role_order)
    dists = [float(torch.linalg.norm(vecs[i]-vecs[j])) for i in range(len(vecs)) for j in range(i+1,len(vecs))]
    return min(dists) if dists else 0.0
def chirality_flux_split_proxy(stages_plus, stages_minus, role_order):
    rho0 = torch.tensor(manifold.ManifoldState().rho_LR, dtype=DTYPE)
    U_plus = compose_U_for_engine(stages_plus, role_order)
    U_minus = compose_U_for_engine(stages_minus, role_order)
    rp = apply_superop(U_plus, rho0); rm = apply_superop(U_minus, rho0)
    yy_p = v1.pauli_readout(rp)[3]; yy_m = v1.pauli_readout(rm)[3]
    split = float(yy_p - yy_m)
    sgn = 1 if split > 0 else (-1 if split < 0 else 0)
    return split, sgn
def stability_margin_under_perturbations(stages_plus, stages_minus, role_order, n_pert=50, base_defect=0.0):
    import random
    random.seed(20260720)
    breaks = []
    survived = 0
    for _ in range(n_pert):
        eps = random.uniform(0.01, 0.8)
        ax = torch.tensor([random.gauss(0,1), random.gauss(0,1), random.gauss(0,1)], dtype=RD)
        ax = ax / (torch.norm(ax) + 1e-12)
        nsigma = ax[0]*v1.stage64.SX + ax[1]*v1.stage64.SY + ax[2]*v1.stage64.SZ
        R = torch.matrix_exp(-1j * (eps/2.0) * torch.tensor(nsigma, dtype=DTYPE))
        orig_local = v1.local_generator
        def patched(stage, role):
            if role != 'H': return orig_local(stage, role)
            sig = torch.tensor(v1.stage64.SIG[stage['b']], dtype=DTYPE)
            sig_p = R @ sig @ R.mH
            h_local = stage['source_h_sign'] * stage['omega'] * sig_p
            if stage['sheet'] == 'L':
                h = torch.kron(h_local, v1.I2)
            else:
                h = torch.kron(v1.I2, h_local)
            identity = v1.I4
            return -1j * (torch.kron(identity, h) - torch.kron(h.T.contiguous(), identity))
        v1.local_generator = patched
        try:
            Up = compose_U_for_engine(stages_plus, role_order)
            Um = compose_U_for_engine(stages_minus, role_order)
            d = monodromy_defect(Up, Um)
        finally:
            v1.local_generator = orig_local
        if d > (2.0 * base_defect + 1e-4):
            breaks.append(eps)
        else:
            survived += 1
    min_break = min(breaks) if breaks else 1.0
    return {{'n_pert': n_pert, 'frac_survive_below_break': survived / float(n_pert), 'min_break_eps': float(min_break)}}
plus = {json.dumps(spec['plus'])}
minus = {json.dumps(spec['minus'])}
micro = {json.dumps(spec['micro_order'])}
fam = {json.dumps(spec['macro_family_perm'])}
def reorder(stages, fp):
    by = {{}}
    for s in stages: by.setdefault(s['family'], []).append(s)
    out = []
    for fi in fp:
        out.extend(by.get(f'family_{{fi}}', []))
    return out
p2 = reorder(plus, fam); m2 = reorder(minus, fam)
U_p = compose_U_for_engine(p2, micro)
U_m = compose_U_for_engine(m2, micro)
defect = monodromy_defect(U_p, U_m)
sp, sg = chirality_flux_split_proxy(p2, m2, micro)
ter = min_pairwise_terrain_dist(p2 + m2, micro)
stb = stability_margin_under_perturbations(p2, m2, micro, 50, defect)
print(json.dumps({{'monodromy_defect': defect, 'flux_split': sp, 'flux_split_sign': sg, 'terrain_min_dist': ter, 'stability': stb}}))
"""
    # Write temp file for the worker to avoid quoting hell in -c
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, dir=OUT) as tf:
        tf.write(code)
        tmp = tf.name
    try:
        proc = subprocess.run(
            [SIM_INTERPRETER, tmp],
            capture_output=True,
            text=True,
            timeout=300,
        )
        out = proc.stdout.strip()
        err = proc.stderr.strip()
        if proc.returncode != 0:
            return {"error": f"subprocess rc={proc.returncode}", "stderr": err[-800:]}
        return json.loads(out)
    finally:
        # do not delete the temp worker file (per instruction: do not delete files)
        pass

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ref = run_reference_once()
    mono_th = ref["monodromy_defect"] * 1.10 + 1e-6
    terrain_floor = ref["terrain_min_dist"] * 0.85
    ref_sign = ref["flux_split_sign"]
    print(f"REFERENCE DHDH: defect={ref['monodromy_defect']:.6e} terrain={ref['terrain_min_dist']:.6e} sign={ref_sign}")
    print(f"PREREG THRESH: mono<{mono_th:.6e} terrain>{terrain_floor:.6e} sign=={ref_sign}")

    plus, minus = build_stage_lists()
    # Serialize minimal stage records for subprocess handoff (ids + numeric fields needed by local_generator)
    def slim(stages):
        return [{k: s[k] for k in ("id","family","sheet","s","f","a","b","omega","gamma","source_h_sign")} for s in stages]
    plus_slim = slim(plus)
    minus_slim = slim(minus)

    # Enumerate micro: all 24 permutations of the four roles
    role_template = ["D", "H", "D", "H"]
    micro_orders = [list(p) for p in itertools.permutations(role_template)]
    n_micro_declared = 24

    # Macro: 4! family reorderings (outer/inner split respected by keeping W+ and W- blocks separate)
    family_perms = list(itertools.permutations([0, 1, 2, 3]))
    n_macro_declared = len(family_perms)

    candidates = []
    for mo in micro_orders:
        for fp in family_perms:
            candidates.append({"micro_order": mo, "macro_family_perm": list(fp)})

    # Add explicit controls as extra rows (they may overlap the enumeration)
    controls = [
        {"micro_order": ["D", "D", "H", "H"], "macro_family_perm": [3, 2, 1, 0], "label": "scrambled_composition"},
        {"micro_order": ["D", "H", "D", "H"], "macro_family_perm": [3, 2, 1, 0], "label": "raw_degenerate_family_reversed"},
        {"micro_order": ["H", "H", "D", "D"], "macro_family_perm": [0, 1, 2, 3], "label": "expected_fail_all_H_then_D"},
    ]

    # Run reference (canonical) is already measured; DHDH candidate is the first in enumeration with matching orders.
    results = []
    # Run reference metrics already in hand; now score the enumerated set via subprocesses (one heavy per candidate, limited fanout)
    max_conc = 3
    pending = []
    from concurrent.futures import ThreadPoolExecutor, as_completed
    with ThreadPoolExecutor(max_workers=max_conc) as ex:
        future_map = {}
        for idx, c in enumerate(candidates):
            spec = {"plus": plus_slim, "minus": minus_slim, "micro_order": c["micro_order"], "macro_family_perm": c["macro_family_perm"]}
            fut = ex.submit(run_one_subprocess, spec)
            future_map[fut] = (idx, c, False)
        for idx, c in enumerate(controls):
            spec = {"plus": plus_slim, "minus": minus_slim, "micro_order": c["micro_order"], "macro_family_perm": c["macro_family_perm"]}
            fut = ex.submit(run_one_subprocess, spec)
            future_map[fut] = (len(candidates) + idx, c, True)
        for fut in as_completed(future_map):
            idx, c, is_ctrl = future_map[fut]
            m = fut.result()
            if "error" in m:
                m = {"monodromy_defect": 999.0, "flux_split": 0.0, "flux_split_sign": 0, "terrain_min_dist": 0.0, "stability": {"frac_survive_below_break": 0.0, "min_break_eps": 0.0}, "error": m["error"]}
            entry = {**c, **m}
            if is_ctrl:
                entry["control"] = True
            results.append(entry)

    # Now evaluate admission on the non-control results (the enumerated space)
    enum_results = [r for r in results if not r.get("control")]
    for r in enum_results:
        r["admitted"] = admission_ok(r, mono_th, terrain_floor, ref_sign)
    for r in results:
        if r.get("control"):
            r["admitted"] = admission_ok(r, mono_th, terrain_floor, ref_sign)

    survivors = [r for r in enum_results if r.get("admitted")]
    M = len(survivors)
    N = len(enum_results)

    # DHDH status
    dhdh_micro = ["D", "H", "D", "H"]
    dhdh_macro = [0, 1, 2, 3]
    dhdh_survived = any(
        r.get("admitted") and r["micro_order"] == dhdh_micro and r["macro_family_perm"] == dhdh_macro
        for r in survivors
    )
    dhdh_is_unique = (len(survivors) == 1 and survivors[0]["micro_order"] == dhdh_micro and survivors[0]["macro_family_perm"] == dhdh_macro)
    if dhdh_is_unique:
        dhdh_status = "unique"
    elif dhdh_survived:
        dhdh_status = "plural"
    else:
        dhdh_status = "failed"

    # Verify controls failed
    scrambled_failed = any(c.get("label") == "scrambled_composition" and not c.get("admitted") for c in results)
    raw_failed = any(c.get("label") == "raw_degenerate_family_reversed" and not c.get("admitted") for c in results)
    extra_failed = any(c.get("label") == "expected_fail_all_H_then_D" and not c.get("admitted") for c in results)

    # Build receipt
    receipt = {
        "name": "schedule_tournament_v0",
        "schema": "ratchet.v8.schedule_tournament.v0",
        "generated_at": iso_now(),
        "classification": "scratch_diagnostic",
        "promotion_allowed": False,
        "formal_admission_allowed": False,
        "accepted_status_label": "runs_with_honest_negative_or_open_control",
        "claim_ceiling": "finite schedule-admission diagnostic on micro/macro orders; D,H,D,H treated as candidate; no canonical claim.",
        "runtime": {
            "interpreter": SIM_INTERPRETER,
            "resolved_interpreter": sys.executable,
            "torch": torch.__version__,
        },
        "composition_provenance": {str(p.relative_to(REPO)): sha(p) for p in SOURCE_FILES},
        "tool_manifest": {
            "pytorch": {"tried": True, "used": True, "reason": "All composition, monodromy, fingerprints, stability, and admission arithmetic."},
        },
        "tool_integration_depth": {"pytorch": "load_bearing"},
        "reference_dhdh": ref,
        "preregistered_thresholds": {
            "monodromy_defect_lt": mono_th,
            "terrain_min_dist_gt": terrain_floor,
            "flux_split_sign_must_equal": ref_sign,
        },
        "enumeration": {
            "micro_orderings_declared": n_micro_declared,
            "macro_family_orderings_declared": n_macro_declared,
            "total_candidates": N,
            "note": "micro: 24 permutations of (D,H,D,H); macro: 4! family permutations inside each engine block (W+/W- split respected by construction).",
        },
        "admission_rule": "monodromy_defect < mono_th AND flux_split_sign == ref_sign AND terrain_min_dist > terrain_floor",
        "survivors": M,
        "dhdh_status": dhdh_status,
        "controls": {
            "scrambled_composition_failed": scrambled_failed,
            "raw_degenerate_family_reversed_failed": raw_failed,
            "expected_fail_all_H_then_D_failed": extra_failed,
            "scrambled_negative_cited_from": "system_v8/unified/results/manifold_unified_v2/receipt.json: scrambled_stage_order_flips=true and endpoint_trace_distance large (monodromy destroyed under raw order).",
        },
        "all_results": serial(results),
        "findings": [
            "All gates are can-fail: monodromy defect, sign-consistency, and terrain floor are measured quantities with explicit thresholds taken from reference before alternatives run.",
            "Controls (scrambled and raw-degenerate) are required to fail admission; an additional expected-fail candidate is included and checked.",
            "D,H,D,H is evaluated under its own thresholds; outcome (unique/plural/failed) is reported without promotion.",
        ],
    }

    out_path = OUT / "receipt.json"
    out_path.write_text(json.dumps(serial(receipt), indent=2, allow_nan=False) + "\n")
    print(json.dumps(serial({"out": str(out_path), "N": N, "M": M, "dhdh_status": dhdh_status, "controls_ok": scrambled_failed and raw_failed and extra_failed}), indent=2, allow_nan=False))

    # Exact final line required by the query
    print(f"SCHEDULE TOURNAMENT: {N} candidates, {M} survivors, DHDH status: {dhdh_status}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
