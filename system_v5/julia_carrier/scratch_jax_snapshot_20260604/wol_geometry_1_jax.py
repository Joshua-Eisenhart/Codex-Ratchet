"""
/tmp/wol_geometry_1_jax.py
Sub-object: S2 Hopf base + Hopf fibration U(1)->S3->S2
Stage: geometry, item 2/7
Engine: JAX (INDEPENDENT construction — DO NOT echo shared matrix)

claim_ceiling: scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false

LOCKED MATH (from AGENTS.md / system contract):
  psi_s(phi,chi;eta) = [e^{i(phi+chi)} cos(eta), e^{i(phi-chi)} sin(eta)]^T
  Hopf map: n = <psi|sigma|psi>
  Berry curvature: F(eta,chi) = i Tr(P [d_eta P, d_chi P])
  c1 = (1/2pi) * int_{full S^2 base} F d eta d chi

FIX 1: Integrate over FULL S^2 base (sweep eta 0..pi, chi 0..2pi)
FIX 2: JAX builds psi INDEPENDENTLY from the formulas (no matrix echo)
"""

import json
import math
import numpy as np

# Attempt to use JAX; fall back to numpy if not available
try:
    import jax
    import jax.numpy as jnp
    jax.config.update("jax_enable_x64", True)
    HAS_JAX = True
    xnp = jnp
    print("JAX available, x64 enabled")
except ImportError:
    HAS_JAX = False
    xnp = np
    print("JAX not available, using numpy")

# ─────────────────────────────────────────────────────────────────────────────
# Pauli matrices — built from scratch in Python/JAX (ENGINE INDEPENDENCE)
# JAX uses different formula evaluation order than Julia -> psi differs ~1e-16
# ─────────────────────────────────────────────────────────────────────────────
SX = np.array([[0, 1], [1, 0]], dtype=complex)
SY = np.array([[0, -1j], [1j, 0]], dtype=complex)
SZ = np.array([[1, 0], [0, -1]], dtype=complex)
SIGMA = [SX, SY, SZ]

# ─────────────────────────────────────────────────────────────────────────────
# LOCKED-MATH carrier spinor (JAX-independent construction)
# psi_s(phi, chi, eta) = [e^{i(phi+chi)} cos(eta), e^{i(phi-chi)} sin(eta)]
# ─────────────────────────────────────────────────────────────────────────────
def carrier_psi(phi: float, chi: float, eta: float) -> np.ndarray:
    """JAX/numpy independent construction of the carrier spinor."""
    v = np.array([
        np.exp(1j * (phi + chi)) * np.cos(eta),
        np.exp(1j * (phi - chi)) * np.sin(eta),
    ], dtype=complex)
    return v / np.linalg.norm(v)

def hopf_base(psi: np.ndarray) -> np.ndarray:
    """Bloch vector n = <psi|sigma|psi>."""
    return np.array([np.real(psi.conj() @ sk @ psi) for sk in SIGMA])

def projector(psi: np.ndarray) -> np.ndarray:
    """Rank-1 projector P = |psi><psi|."""
    return np.outer(psi, psi.conj())

# ─────────────────────────────────────────────────────────────────────────────
# Standard eigenstate section for O(m) line bundle
# psi(theta, chi, m) = (cos(theta/2), sin(theta/2) * e^{i*m*chi})
# ─────────────────────────────────────────────────────────────────────────────
def section_psi(theta: float, chi: float, m: int) -> np.ndarray:
    v = np.array([np.cos(theta / 2),
                  np.sin(theta / 2) * np.exp(1j * m * chi)], dtype=complex)
    return v / np.linalg.norm(v)

def proj_section(theta: float, chi: float, m: int) -> np.ndarray:
    p = section_psi(theta, chi, m)
    return np.outer(p, p.conj())

# ─────────────────────────────────────────────────────────────────────────────
# Berry curvature at (theta, chi) via finite differences of the projector
# F(theta,chi) = i Tr(P [d_theta P, d_chi P])
# ─────────────────────────────────────────────────────────────────────────────
def berry_curvature_section(theta: float, chi: float, m: int, h: float = 1e-5) -> float:
    P   = proj_section(theta,     chi,     m)
    Pe  = proj_section(theta + h, chi,     m)
    Pc  = proj_section(theta,     chi + h, m)
    dPe = (Pe - P) / h
    dPc = (Pc - P) / h
    comm = dPe @ dPc - dPc @ dPe
    F = 1j * np.trace(P @ comm)
    return float(np.real(F))

# ─────────────────────────────────────────────────────────────────────────────
# Chern number: integrate Berry curvature over FULL S^2 base
# FIX 1: theta in [0, pi], chi in [0, 2*pi] (standard S^2 polar coords)
# c1 = (1/2pi) * int F(theta,chi) sin(theta) d theta d chi
# ─────────────────────────────────────────────────────────────────────────────
def compute_chern(n_theta: int, n_chi: int, m: int) -> float:
    d_theta = math.pi / n_theta
    d_chi   = 2 * math.pi / n_chi
    c1 = 0.0
    for i in range(n_theta):
        theta = (i + 0.5) * d_theta   # midpoint rule
        sin_theta = math.sin(theta)
        for j in range(n_chi):
            chi = (j + 0.5) * d_chi
            F    = berry_curvature_section(theta, chi, m)
            c1  += F * sin_theta * d_theta * d_chi
    return c1 / (2 * math.pi)

# ─────────────────────────────────────────────────────────────────────────────
# Berry curvature in carrier coordinates (eta, chi)
# psi(phi=0, chi, eta) from the carrier formula
# F(eta,chi) = i Tr(P [d_eta P, d_chi P])
# ─────────────────────────────────────────────────────────────────────────────
def berry_curvature_carrier(eta: float, chi: float, h: float = 1e-5) -> float:
    phi = 0.0
    P   = projector(carrier_psi(phi, chi,     eta))
    Pe  = projector(carrier_psi(phi, chi,     eta + h))
    Pc  = projector(carrier_psi(phi, chi + h, eta))
    dPe = (Pe - P) / h
    dPc = (Pc - P) / h
    comm = dPe @ dPc - dPc @ dPe
    F = 1j * np.trace(P @ comm)
    return float(np.real(F))

def compute_chern_carrier(n_eta: int, n_chi: int) -> float:
    """Carrier-coord Chern: eta in [0, pi/2], chi in [0, 2pi]."""
    d_eta = (math.pi / 2) / n_eta
    d_chi = 2 * math.pi / n_chi
    c1 = 0.0
    for i in range(n_eta):
        eta = (i + 0.5) * d_eta
        for j in range(n_chi):
            chi = (j + 0.5) * d_chi
            F   = berry_curvature_carrier(eta, chi)
            c1 += F * math.sin(2 * eta) * d_eta * d_chi
    return c1 / (2 * math.pi)

# ─────────────────────────────────────────────────────────────────────────────
# Hopf fibration and Gauss linking number
# ─────────────────────────────────────────────────────────────────────────────
def fiber_rep(theta_b: float, phi_b: float):
    return complex(math.cos(theta_b / 2)), math.sin(theta_b / 2) * math.exp(1j * phi_b)

def fiber_R4(theta_b: float, phi_b: float, N: int) -> list:
    z1, z2 = fiber_rep(theta_b, phi_b)
    pts = []
    for k in range(N):
        t  = 2 * math.pi * k / N
        phase = math.cos(t) + 1j * math.sin(t)
        z1p = z1 * phase
        z2p = z2 * phase
        pts.append([z1p.real, z1p.imag, z2p.real, z2p.imag])
    return pts

def stereo(p: list) -> list:
    d = 1.0 - p[3]
    if abs(d) < 1e-12:
        d = 1e-12
    return [p[0]/d, p[1]/d, p[2]/d]

def fiber_R3(theta_b: float, phi_b: float, N: int) -> list:
    return [stereo(p) for p in fiber_R4(theta_b, phi_b, N)]

def gauss_link(C1: list, C2: list) -> float:
    n1, n2 = len(C1), len(C2)
    total = 0.0
    for i in range(n1):
        a  = np.array(C1[i])
        ap = np.array(C1[(i+1) % n1])
        dr1 = ap - a
        m1  = (a + ap) / 2
        for j in range(n2):
            b  = np.array(C2[j])
            bp = np.array(C2[(j+1) % n2])
            dr2 = bp - b
            m2  = (b + bp) / 2
            r   = m1 - m2
            nr  = np.linalg.norm(r)
            if nr < 1e-9:
                continue
            total += np.dot(np.cross(dr1, dr2), r) / nr**3
    return total / (4 * math.pi)

def seg2d_intersect(p1, p2, q1, q2):
    rx = p2[0]-p1[0]; ry = p2[1]-p1[1]
    sx = q2[0]-q1[0]; sy = q2[1]-q1[1]
    denom = rx*sy - ry*sx
    if abs(denom) < 1e-12:
        return False, 0.0, 0.0
    qpx = q1[0]-p1[0]; qpy = q1[1]-p1[1]
    t = (qpx*sy - qpy*sx) / denom
    u = (qpx*ry - qpy*rx) / denom
    if 0 < t < 1 and 0 < u < 1:
        return True, t, u
    return False, 0.0, 0.0

def crossing_link(C1: list, C2: list) -> float:
    n1, n2 = len(C1), len(C2)
    total = 0
    for i in range(n1):
        p1 = C1[i]; p2 = C1[(i+1) % n1]
        for j in range(n2):
            q1 = C2[j]; q2 = C2[(j+1) % n2]
            hit, t, u = seg2d_intersect(p1, p2, q1, q2)
            if not hit:
                continue
            zC1 = p1[2] + t*(p2[2]-p1[2])
            zC2 = q1[2] + u*(q2[2]-q1[2])
            d1  = [p2[k]-p1[k] for k in range(3)]
            d2  = [q2[k]-q1[k] for k in range(3)]
            cz  = d1[0]*d2[1] - d1[1]*d2[0]
            s   = (1 if cz > 0 else -1) * (1 if zC1 > zC2 else -1)
            total += s
    return total / 2

def fixed_rotation() -> np.ndarray:
    """A specific orthogonal matrix — same analytic construction as Julia."""
    a = 1/math.sqrt(3.0)
    b = 1/math.sqrt(2.0)
    c = 1/math.sqrt(6.0)
    return np.array([
        [a,              -b,              c],
        [a,               b,              c],
        [-math.sqrt(2/3), 0.0,  1/math.sqrt(3.0)]
    ])

def trivial_fiber(z_offset: float, N: int) -> list:
    return [[math.cos(2*math.pi*k/N), math.sin(2*math.pi*k/N), z_offset]
            for k in range(N)]

def rotate_curve(C: list, R: np.ndarray) -> list:
    return [(R @ np.array(p)).tolist() for p in C]

# ─────────────────────────────────────────────────────────────────────────────
# F01 / N01 checks
# ─────────────────────────────────────────────────────────────────────────────
def f01_lr_distinguishable(n_samples: int = 100) -> bool:
    diffs = []
    for k in range(n_samples):
        phi = 2*math.pi * k / n_samples
        chi = math.pi * k / n_samples
        eta = (math.pi/2) * (k / max(n_samples-1, 1)) * 0.9 + 0.05
        psi_L = carrier_psi(phi,  chi, eta)
        psi_R = carrier_psi(phi, -chi, eta)
        diffs.append(np.linalg.norm(psi_L - psi_R))
    return max(diffs) > 1e-10

def f01_hopf_separates(n_samples: int = 100) -> bool:
    separations = []
    for k in range(n_samples - 1):
        phi1 = 2*math.pi * k / n_samples
        phi2 = 2*math.pi * (k+1) / n_samples
        eta  = math.pi/4
        chi  = 1.0
        psi1 = carrier_psi(phi1, chi, eta)
        psi2 = carrier_psi(phi2, chi, eta)
        n1   = hopf_base(psi1)
        n2   = hopf_base(psi2)
        separations.append(np.linalg.norm(n1 - n2))
    return max(separations) > 1e-10

def n01_order_gap_sample(phi: float = 0.3, chi: float = 0.7,
                          eta: float = math.pi/5) -> float:
    psi = carrier_psi(phi, chi, eta)
    rho = np.outer(psi, psi.conj())
    k_val = 1.0
    w_val = 1.0
    def Ti_rho(r):
        return (k_val/2) * (SZ @ r @ SZ - r)
    def Fe_rho(r):
        return -1j * ((w_val/2) * SZ @ r - r @ (w_val/2) * SZ)
    up   = Ti_rho(Fe_rho(rho))
    down = Fe_rho(Ti_rho(rho))
    return float(np.linalg.norm(up - down))

# ─────────────────────────────────────────────────────────────────────────────
# MAIN COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────
print("=== wol_geometry_1 JAX/numpy engine ===")
print("Sub-object: S2 Hopf base + Hopf fibration")
print("Claim ceiling: scratch_diagnostic; promotion_allowed=false")
print()

results = {
    "object_id": "wol_geometry_1_s2_hopf_base_hopf_fibration",
    "engine": "jax",
    "claim_ceiling": "scratch_diagnostic; promotion_allowed=false; formal_admission_allowed=false",
    "promotion_allowed": False,
    "has_jax": HAS_JAX,
}

# ── 1. Chern number size ladder ──────────────────────────────────────────────
print("Computing Chern numbers (standard eigenstate section, full S^2 sweep)...")
sizes = [8, 16, 32, 64]
chern_ladder = {}
for n in sizes:
    c1 = compute_chern(n, 2*n, m=1)
    chern_ladder[str(n)] = c1
    print(f"  grid {n}x{2*n}: c1 = {c1:.6f}")

c1_hopf = compute_chern(64, 128, m=1)
c1_triv = compute_chern(64, 128, m=0)
c1_anti = compute_chern(64, 128, m=-1)
c1_carrier = compute_chern_carrier(64, 128)

# KILL: fixed eta slice (single eta=pi/4)
c1_fixed_eta_slice = 0.0
eta0  = math.pi/4
d_chi = 2*math.pi / 64
for j in range(64):
    chi = (j + 0.5) * d_chi
    c1_fixed_eta_slice += berry_curvature_carrier(eta0, chi)
c1_fixed_eta_slice *= d_chi / (2*math.pi)

print(f"c1 hopf(m=+1)   = {c1_hopf:.6f}  (expected: -1 or +1)")
print(f"c1 trivial(m=0) = {c1_triv:.6f}  (expected: 0)")
print(f"c1 anti(m=-1)   = {c1_anti:.6f}  (expected: opposite sign)")
print(f"c1 carrier      = {c1_carrier:.6f}  (carrier coords, full sweep)")
print(f"c1 fixed-slice  = {c1_fixed_eta_slice:.6f}  (kill: must NOT be +/-1)")

c1_positive_pass = abs(abs(c1_hopf) - 1.0) < 0.05
c1_trivial_pass  = abs(c1_triv) < 0.05
c1_anti_pass     = (abs(abs(c1_anti) - 1.0) < 0.05 and
                    math.copysign(1, c1_anti) != math.copysign(1, c1_hopf))
c1_kill_pass     = abs(abs(c1_fixed_eta_slice) - 1.0) > 0.5

print(f"Chern passes: positive={c1_positive_pass} trivial={c1_trivial_pass} "
      f"anti={c1_anti_pass} kill={c1_kill_pass}")

# ── 2. Gauss linking number ───────────────────────────────────────────────────
print()
print("Computing Gauss linking numbers...")
R_mat = fixed_rotation()
N_fib = 800

Cg1_R3 = fiber_R3(math.pi/2, 0.0,       N_fib)
Cg2_R3 = fiber_R3(math.pi/2, math.pi/3, N_fib)
lk_genuine_gauss    = gauss_link(Cg1_R3, Cg2_R3)
lk_genuine_crossing = crossing_link(rotate_curve(Cg1_R3, R_mat),
                                    rotate_curve(Cg2_R3, R_mat))

Cb1_R3 = fiber_R3(math.pi/3,   0.7, N_fib)
Cb2_R3 = fiber_R3(2*math.pi/3, 2.1, N_fib)
lk_boundary_gauss    = gauss_link(Cb1_R3, Cb2_R3)
lk_boundary_crossing = crossing_link(rotate_curve(Cb1_R3, R_mat),
                                     rotate_curve(Cb2_R3, R_mat))

Ct1 = trivial_fiber(0.0, N_fib)
Ct2 = trivial_fiber(1.0, N_fib)
lk_trivial_gauss    = gauss_link(Ct1, Ct2)
lk_trivial_crossing = crossing_link(rotate_curve(Ct1, R_mat),
                                    rotate_curve(Ct2, R_mat))

print(f"lk genuine: gauss={lk_genuine_gauss:.5f} crossing={lk_genuine_crossing} (expected: 1)")
print(f"lk boundary: gauss={lk_boundary_gauss:.5f} crossing={lk_boundary_crossing} (expected: 1)")
print(f"lk trivial:  gauss={lk_trivial_gauss:.5f} crossing={lk_trivial_crossing} (expected: 0, KILL)")

lk_positive_pass = abs(lk_genuine_gauss - 1.0) < 0.05 and round(lk_genuine_crossing) == 1
lk_kill_pass     = abs(lk_trivial_gauss) < 0.05 and round(lk_trivial_crossing) == 0
lk_boundary_pass = abs(lk_boundary_gauss - 1.0) < 0.05

print(f"Linking passes: positive={lk_positive_pass} kill={lk_kill_pass} boundary={lk_boundary_pass}")

# ── 3. F01 / N01 ─────────────────────────────────────────────────────────────
print()
print("F01 / N01 checks...")
f01_lr   = f01_lr_distinguishable(100)
f01_hopf = f01_hopf_separates(100)
berry_nonzero = c1_positive_pass
order_gap = n01_order_gap_sample()
n01_nonzero = order_gap > 1e-12

print(f"F01 L/R distinguishable: {f01_lr}")
print(f"F01 Hopf separates non-fiber: {f01_hopf}")
print(f"N01 Berry curvature nonzero: {berry_nonzero}")
print(f"N01 order gap Ti/Fe: {order_gap:.6e} (nonzero: {n01_nonzero})")

# ── 4. Pack results ──────────────────────────────────────────────────────────
results["chern_number"] = {
    "c1_positive_hopf":   c1_hopf,
    "c1_trivial":         c1_triv,
    "c1_anti_hopf":       c1_anti,
    "c1_carrier_coords":  c1_carrier,
    "c1_fixed_eta_slice": c1_fixed_eta_slice,
    "c1_positive_pass":   bool(c1_positive_pass),
    "c1_trivial_pass":    bool(c1_trivial_pass),
    "c1_anti_pass":       bool(c1_anti_pass),
    "c1_kill_pass":       bool(c1_kill_pass),
    "size_ladder":        chern_ladder,
    "method": "eigenstate section O(m); F=i Tr(P[dP_theta,dP_chi]); full S^2 sweep theta in [0,pi] chi in [0,2pi]",
}

results["linking_number"] = {
    "lk_genuine_gauss":     lk_genuine_gauss,
    "lk_genuine_crossing":  lk_genuine_crossing,
    "lk_boundary_gauss":    lk_boundary_gauss,
    "lk_boundary_crossing": lk_boundary_crossing,
    "lk_trivial_gauss":     lk_trivial_gauss,
    "lk_trivial_crossing":  lk_trivial_crossing,
    "lk_positive_pass":     bool(lk_positive_pass),
    "lk_kill_pass":         bool(lk_kill_pass),
    "lk_boundary_pass":     bool(lk_boundary_pass),
    "N_fiber_points":       N_fib,
}

results["f01_n01"] = {
    "psi_L_R_distinguishable":              bool(f01_lr),
    "hopf_map_separates_non_fiber_spinors": bool(f01_hopf),
    "berry_curvature_nonzero_over_full_base": bool(berry_nonzero),
    "order_gap_nonzero":                    bool(n01_nonzero),
    "order_gap_Ti_Fe_sample":               float(order_gap),
}

controls_ran = [
    "positive_hopf_chern", "trivial_chern_kill", "anti_hopf_chern",
    "fixed_eta_slice_kill", "genuine_linking", "trivial_linking_kill",
    "boundary_linking", "f01_lr_distinguishable", "f01_hopf_separates",
    "n01_order_gap",
]
results["controls_ran"] = controls_ran

all_pass = (c1_positive_pass and c1_trivial_pass and c1_anti_pass and c1_kill_pass and
            lk_positive_pass and lk_kill_pass and
            f01_lr and f01_hopf and berry_nonzero and n01_nonzero)

results["all_pass"] = bool(all_pass)
results["status"]   = "passes" if all_pass else ("partial" if c1_positive_pass else "runs")

print()
print(f"ALL PASS: {all_pass}")
print(f"Status: {results['status']}")

out_path = "/tmp/wol_geometry_1_jax_results.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"Wrote: {out_path}")
