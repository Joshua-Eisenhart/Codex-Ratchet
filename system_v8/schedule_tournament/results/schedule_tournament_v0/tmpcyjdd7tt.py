
import sys, json, torch
sys.path.insert(0, '/Users/joshuaeisenhart/Codex-Ratchet')
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
    return {'n_pert': n_pert, 'frac_survive_below_break': survived / float(n_pert), 'min_break_eps': float(min_break)}
plus = [{"id": "family_0|L|f+1", "family": "family_0", "sheet": "L", "s": 1, "f": 1, "a": "z", "b": "x", "omega": 2.5188667058086582, "gamma": 0.5889359102131049, "source_h_sign": 1}, {"id": "family_0|R|f-1", "family": "family_0", "sheet": "R", "s": -1, "f": -1, "a": "z", "b": "x", "omega": 2.5188667058086582, "gamma": 0.5889359102131049, "source_h_sign": 1}, {"id": "family_1|L|f+1", "family": "family_1", "sheet": "L", "s": 1, "f": 1, "a": "x", "b": "z", "omega": 1.7632066940660607, "gamma": 1.0306378428729335, "source_h_sign": 1}, {"id": "family_1|R|f-1", "family": "family_1", "sheet": "R", "s": -1, "f": -1, "a": "x", "b": "z", "omega": 1.7632066940660607, "gamma": 1.0306378428729335, "source_h_sign": 1}, {"id": "family_2|L|f+1", "family": "family_2", "sheet": "L", "s": 1, "f": 1, "a": "z", "b": "x", "omega": 3.274526717551256, "gamma": 0.4417019326598286, "source_h_sign": 1}, {"id": "family_2|R|f-1", "family": "family_2", "sheet": "R", "s": -1, "f": -1, "a": "z", "b": "x", "omega": 3.274526717551256, "gamma": 0.4417019326598286, "source_h_sign": 1}, {"id": "family_3|L|f+1", "family": "family_3", "sheet": "L", "s": 1, "f": 1, "a": "x", "b": "z", "omega": 2.2669800352277925, "gamma": 1.472339775532762, "source_h_sign": 1}, {"id": "family_3|R|f-1", "family": "family_3", "sheet": "R", "s": -1, "f": -1, "a": "x", "b": "z", "omega": 2.2669800352277925, "gamma": 1.472339775532762, "source_h_sign": 1}]
minus = [{"id": "family_0|L|f-1", "family": "family_0", "sheet": "L", "s": 1, "f": -1, "a": "z", "b": "x", "omega": 2.5188667058086582, "gamma": 0.5889359102131049, "source_h_sign": -1}, {"id": "family_0|R|f+1", "family": "family_0", "sheet": "R", "s": -1, "f": 1, "a": "z", "b": "x", "omega": 2.5188667058086582, "gamma": 0.5889359102131049, "source_h_sign": -1}, {"id": "family_1|L|f-1", "family": "family_1", "sheet": "L", "s": 1, "f": -1, "a": "x", "b": "z", "omega": 1.7632066940660607, "gamma": 1.0306378428729335, "source_h_sign": -1}, {"id": "family_1|R|f+1", "family": "family_1", "sheet": "R", "s": -1, "f": 1, "a": "x", "b": "z", "omega": 1.7632066940660607, "gamma": 1.0306378428729335, "source_h_sign": -1}, {"id": "family_2|L|f-1", "family": "family_2", "sheet": "L", "s": 1, "f": -1, "a": "z", "b": "x", "omega": 3.274526717551256, "gamma": 0.4417019326598286, "source_h_sign": -1}, {"id": "family_2|R|f+1", "family": "family_2", "sheet": "R", "s": -1, "f": 1, "a": "z", "b": "x", "omega": 3.274526717551256, "gamma": 0.4417019326598286, "source_h_sign": -1}, {"id": "family_3|L|f-1", "family": "family_3", "sheet": "L", "s": 1, "f": -1, "a": "x", "b": "z", "omega": 2.2669800352277925, "gamma": 1.472339775532762, "source_h_sign": -1}, {"id": "family_3|R|f+1", "family": "family_3", "sheet": "R", "s": -1, "f": 1, "a": "x", "b": "z", "omega": 2.2669800352277925, "gamma": 1.472339775532762, "source_h_sign": -1}]
micro = ["H", "D", "D", "H"]
fam = [2, 3, 1, 0]
def reorder(stages, fp):
    by = {}
    for s in stages: by.setdefault(s['family'], []).append(s)
    out = []
    for fi in fp:
        out.extend(by.get(f'family_{fi}', []))
    return out
p2 = reorder(plus, fam); m2 = reorder(minus, fam)
U_p = compose_U_for_engine(p2, micro)
U_m = compose_U_for_engine(m2, micro)
defect = monodromy_defect(U_p, U_m)
sp, sg = chirality_flux_split_proxy(p2, m2, micro)
ter = min_pairwise_terrain_dist(p2 + m2, micro)
stb = stability_margin_under_perturbations(p2, m2, micro, 50, defect)
print(json.dumps({'monodromy_defect': defect, 'flux_split': sp, 'flux_split_sign': sg, 'terrain_min_dist': ter, 'stability': stb}))
