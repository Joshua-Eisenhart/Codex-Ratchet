#!/usr/bin/env python3
"""
sim_operator_geometry_compatibility.py
--------------------------------------
Operator-Geometry Compatibility Matrix (48-cell) + Attractor Discovery.

8 operator families x 6 geometry structures.
Tests which operators preserve which geometric manifolds,
and discovers each operator's natural attractor geometry.

Supporting compatibility-map lego, not a closure-grade proof surface.
NO engine imports. Pure legos: numpy, scipy, clifford.
"""

import sys, os, json, time
import numpy as np
from scipy.linalg import expm
classification = "classical_baseline"  # auto-backfill

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

TOOL_MANIFEST = {
    "pytorch": {"tried": False, "used": False, "reason": "not needed — numpy/scipy compatibility map"},
    "pyg": {"tried": False, "used": False, "reason": "not needed"},
    "z3": {"tried": False, "used": False, "reason": "not needed — no SMT proof obligations"},
    "cvc5": {"tried": False, "used": False, "reason": "not needed"},
    "sympy": {"tried": False, "used": False, "reason": "not needed"},
    "clifford": {"tried": True, "used": True, "reason": "load-bearing for native Cl(3) rotor action"},
    "geomstats": {"tried": False, "used": False, "reason": "not needed"},
    "e3nn": {"tried": False, "used": False, "reason": "not needed"},
    "rustworkx": {"tried": False, "used": False, "reason": "not needed"},
    "xgi": {"tried": False, "used": False, "reason": "not needed"},
    "toponetx": {"tried": False, "used": False, "reason": "not needed"},
    "gudhi": {"tried": False, "used": False, "reason": "not needed"},
}

TOOL_INTEGRATION_DEPTH = {
    "pytorch": None,
    "pyg": None,
    "z3": None,
    "cvc5": None,
    "sympy": None,
    "clifford": "load_bearing",
    "geomstats": None,
    "e3nn": None,
    "rustworkx": None,
    "xgi": None,
    "toponetx": None,
    "gudhi": None,
}

# ─── Pauli matrices ──────────────────────────────────────────────────────────

sx = np.array([[0, 1], [1, 0]], dtype=complex)
sy = np.array([[0, -1j], [1j, 0]], dtype=complex)
sz = np.array([[1, 0], [0, -1]], dtype=complex)
I2 = np.eye(2, dtype=complex)

# ─── 8 Operator Families ─────────────────────────────────────────────────────

def uz_rotation(rho, angle):
    """Z-rotation (unitary, U(1) subgroup)."""
    U = expm(-1j * angle / 2 * sz)
    return U @ rho @ U.conj().T

def ux_rotation(rho, angle):
    """X-rotation (unitary, different U(1))."""
    U = expm(-1j * angle / 2 * sx)
    return U @ rho @ U.conj().T

def su2_rotation(rho, axis, angle):
    """General SU(2) rotation (unitary, full group)."""
    ax = np.array(axis, dtype=float)
    ax /= np.linalg.norm(ax)
    H = ax[0] * sx + ax[1] * sy + ax[2] * sz
    U = expm(-1j * angle / 2 * H)
    return U @ rho @ U.conj().T

def z_dephasing(rho, strength):
    """Z-dephasing (CPTP, dissipative)."""
    P0 = np.array([[1, 0], [0, 0]], dtype=complex)
    P1 = np.array([[0, 0], [0, 1]], dtype=complex)
    return (1 - strength) * rho + strength * (P0 @ rho @ P0 + P1 @ rho @ P1)

def x_dephasing(rho, strength):
    """X-dephasing (CPTP, dissipative)."""
    Qp = np.array([[1, 1], [1, 1]], dtype=complex) / 2
    Qm = np.array([[1, -1], [-1, 1]], dtype=complex) / 2
    return (1 - strength) * rho + strength * (Qp @ rho @ Qp + Qm @ rho @ Qm)

def depolarizing(rho, p):
    """Depolarizing channel (CPTP, isotropic)."""
    return (1 - p) * rho + p * I2 / 2

def amplitude_damping(rho, gamma):
    """Amplitude damping (CPTP, non-unital)."""
    K0 = np.array([[1, 0], [0, np.sqrt(1 - gamma)]], dtype=complex)
    K1 = np.array([[0, np.sqrt(gamma)], [0, 0]], dtype=complex)
    return K0 @ rho @ K0.conj().T + K1 @ rho @ K1.conj().T

def cl3_rotor_action(bloch, angle, plane):
    """Cl(3) rotor action on Bloch vector (geometric algebra native)."""
    from clifford import Cl
    layout, blades = Cl(3)
    e1, e2, e3 = blades['e1'], blades['e2'], blades['e3']
    planes = {'xy': e1 * e2, 'xz': e1 * e3, 'yz': e2 * e3}
    B = planes[plane]
    R = np.cos(angle / 2) + (-np.sin(angle / 2)) * B
    v = bloch[0] * e1 + bloch[1] * e2 + bloch[2] * e3
    v_rot = R * v * ~R
    return np.array([float(v_rot[blades['e1']]),
                     float(v_rot[blades['e2']]),
                     float(v_rot[blades['e3']])])

# ─── Helpers: state <-> Bloch ─────────────────────────────────────────────────

def rho_to_bloch(rho):
    """Extract Bloch vector from 2x2 density matrix."""
    rx = 2 * np.real(rho[0, 1])
    ry = 2 * np.imag(rho[1, 0])
    rz = np.real(rho[0, 0] - rho[1, 1])
    return np.array([rx, ry, rz])

def bloch_to_rho(r):
    """Construct density matrix from Bloch vector."""
    return (I2 + r[0] * sx + r[1] * sy + r[2] * sz) / 2

def purity(rho):
    return np.real(np.trace(rho @ rho))

def von_neumann_entropy(rho):
    evals = np.real(np.linalg.eigvalsh(rho))
    evals = evals[evals > 1e-15]
    return -np.sum(evals * np.log2(evals))

# ─── Geometry generators ─────────────────────────────────────────────────────

def generate_flat_r3(n=10):
    """Flat R3 (Bloch ball interior): mixed states with |r| < 1."""
    states = []
    rng = np.random.RandomState(42)
    for _ in range(n):
        r = rng.randn(3)
        r *= rng.uniform(0.1, 0.9) / np.linalg.norm(r)
        states.append(bloch_to_rho(r))
    return states

def generate_sphere_s2(n=10):
    """Sphere S2 (Bloch surface): pure states |r| = 1."""
    states = []
    rng = np.random.RandomState(43)
    for _ in range(n):
        r = rng.randn(3)
        r /= np.linalg.norm(r)
        states.append(bloch_to_rho(r))
    return states

def generate_fiber_s1(n=10):
    """Fiber S1: states along one Hopf fiber (vary phase at fixed theta, phi)."""
    # Fix theta=pi/4, phi=0 on S2, vary global phase alpha
    theta = np.pi / 4
    states = []
    for i in range(n):
        alpha = 2 * np.pi * i / n
        # |psi> = cos(theta/2)|0> + e^{i(phi+alpha)} sin(theta/2)|1>
        psi = np.array([np.cos(theta / 2),
                        np.exp(1j * alpha) * np.sin(theta / 2)])
        rho = np.outer(psi, psi.conj())
        states.append(rho)
    return states

def generate_torus_t2(n=10):
    """Torus T2: states at fixed eta, varying (theta1, theta2)."""
    # eta = mixing parameter (fixed at 0.5 for balanced torus)
    eta = 0.5
    states = []
    side = int(np.ceil(np.sqrt(n)))
    count = 0
    for i in range(side):
        for j in range(side):
            if count >= n:
                break
            theta1 = 2 * np.pi * i / side
            theta2 = 2 * np.pi * j / side
            # Bloch vector on a torus embedded in R3
            R_major = eta  # distance from center = eta (0 < eta < 1)
            r = np.array([
                R_major * np.cos(theta1),
                R_major * np.sin(theta1),
                (1 - R_major) * np.cos(theta2)
            ])
            # Ensure inside Bloch ball
            norm = np.linalg.norm(r)
            if norm > 0.99:
                r *= 0.99 / norm
            states.append(bloch_to_rho(r))
            count += 1
    return states[:n]

def generate_nested_tori(n=10):
    """Nested tori: states at 3 different eta values."""
    etas = [0.3, 0.5, 0.7]
    states = []
    per_torus = max(1, n // 3)
    rng = np.random.RandomState(44)
    for eta in etas:
        for i in range(per_torus):
            theta1 = 2 * np.pi * rng.rand()
            theta2 = 2 * np.pi * rng.rand()
            r = np.array([
                eta * np.cos(theta1),
                eta * np.sin(theta1),
                (1 - eta) * np.cos(theta2)
            ])
            norm = np.linalg.norm(r)
            if norm > 0.99:
                r *= 0.99 / norm
            states.append(bloch_to_rho(r))
    while len(states) < n:
        states.append(states[-1])
    return states[:n]

def generate_cp1(n=10):
    """CP1 (projective): same as S2 but explicitly projective."""
    # CP1 ~ S2 for qubits; pure states identified up to global phase
    return generate_sphere_s2(n)


# ─── Geometry membership tests ───────────────────────────────────────────────

def is_on_sphere(rho, tol=1e-6):
    """Is the state on S2 (pure)?"""
    return abs(purity(rho) - 1.0) < tol

def is_in_ball(rho, tol=1e-6):
    """Is the state inside the Bloch ball (valid density matrix)?"""
    r = rho_to_bloch(rho)
    return np.linalg.norm(r) <= 1.0 + tol

def is_on_fiber(rho, ref_theta=np.pi / 4, tol=0.05):
    """Is the state on the S1 fiber at fixed theta?"""
    r = rho_to_bloch(rho)
    norm = np.linalg.norm(r)
    if norm < 1e-10:
        return False
    # For fiber: |r| should be ~1 (pure) and polar angle matches
    rz = r[2] / norm if norm > 0 else 0
    theta_state = np.arccos(np.clip(rz, -1, 1))
    return abs(purity(rho) - 1.0) < tol and abs(theta_state - ref_theta) < tol

def is_on_torus(rho, eta=0.5, tol=0.1):
    """Is the state on the T2 torus at given eta?"""
    r = rho_to_bloch(rho)
    rxy = np.sqrt(r[0]**2 + r[1]**2)
    # Torus constraint: rxy ~ eta (major radius)
    return abs(rxy - eta) < tol

def is_on_nested_tori(rho, etas=[0.3, 0.5, 0.7], tol=0.1):
    """Is the state on one of the nested tori?"""
    return any(is_on_torus(rho, eta, tol) for eta in etas)


# ─── Operator wrappers (uniform interface) ───────────────────────────────────

OPERATORS = {
    'uz_rotation': lambda rho: uz_rotation(rho, np.pi / 7),
    'ux_rotation': lambda rho: ux_rotation(rho, np.pi / 7),
    'su2_rotation': lambda rho: su2_rotation(rho, [1, 1, 1], np.pi / 7),
    'z_dephasing': lambda rho: z_dephasing(rho, 0.3),
    'x_dephasing': lambda rho: x_dephasing(rho, 0.3),
    'depolarizing': lambda rho: depolarizing(rho, 0.3),
    'amplitude_damping': lambda rho: amplitude_damping(rho, 0.3),
    'cl3_rotor': None  # handled separately (Bloch-space)
}

GEOMETRIES = {
    'flat_r3': {
        'gen': generate_flat_r3,
        'check': is_in_ball,
        'desc': 'Flat R3 (Bloch ball interior)'
    },
    'sphere_s2': {
        'gen': generate_sphere_s2,
        'check': is_on_sphere,
        'desc': 'Sphere S2 (Bloch surface)'
    },
    'fiber_s1': {
        'gen': generate_fiber_s1,
        'check': is_on_fiber,
        'desc': 'Fiber S1 (Hopf fiber)'
    },
    'torus_t2': {
        'gen': generate_torus_t2,
        'check': lambda rho: is_on_torus(rho, 0.5),
        'desc': 'Torus T2'
    },
    'nested_tori': {
        'gen': generate_nested_tori,
        'check': is_on_nested_tori,
        'desc': 'Nested tori (3 eta shells)'
    },
    'cp1': {
        'gen': generate_cp1,
        'check': is_on_sphere,  # CP1 ~ S2 for qubits
        'desc': 'CP1 (projective)'
    }
}

# ─── Core test: 48-cell matrix ───────────────────────────────────────────────

def test_cell(op_name, geom_name, n_states=10, n_iter=5):
    """Test one operator on one geometry. Returns detailed results."""
    geom = GEOMETRIES[geom_name]
    states = geom['gen'](n_states)
    check = geom['check']

    # Track per-state trajectories
    purities_init = [purity(s) for s in states]
    entropies_init = [von_neumann_entropy(s) for s in states]
    norms_init = [np.linalg.norm(rho_to_bloch(s)) for s in states]

    on_manifold_init = sum(1 for s in states if check(s))

    # Apply operator iteratively
    evolved = [s.copy() for s in states]
    manifold_frac_history = []

    for iteration in range(n_iter):
        new_evolved = []
        for rho in evolved:
            if op_name == 'cl3_rotor':
                # Cl(3) rotor works in Bloch space
                b = rho_to_bloch(rho)
                b_rot = cl3_rotor_action(b, np.pi / 7, 'xy')
                new_rho = bloch_to_rho(b_rot)
            else:
                new_rho = OPERATORS[op_name](rho)
            new_evolved.append(new_rho)
        evolved = new_evolved

        on_manifold = sum(1 for s in evolved if check(s))
        manifold_frac_history.append(on_manifold / n_states)

    # Final measurements
    purities_final = [purity(s) for s in evolved]
    entropies_final = [von_neumann_entropy(s) for s in evolved]
    norms_final = [np.linalg.norm(rho_to_bloch(s)) for s in evolved]

    # Classify compatibility
    final_on = manifold_frac_history[-1] if manifold_frac_history else 0
    init_on = on_manifold_init / n_states

    avg_purity_change = np.mean(np.array(purities_final) - np.array(purities_init))
    avg_entropy_change = np.mean(np.array(entropies_final) - np.array(entropies_init))
    avg_norm_change = np.mean(np.array(norms_final) - np.array(norms_init))

    # Determine verdict
    if init_on < 0.5:
        # States didn't start on manifold well, test is about ball containment
        verdict = 'COMPATIBLE' if all(is_in_ball(s) for s in evolved) else 'BREAKS'
    elif final_on >= 0.8:
        # Check if operator had any effect
        bloch_diffs = [np.linalg.norm(rho_to_bloch(e) - rho_to_bloch(s))
                       for e, s in zip(evolved, states)]
        if np.mean(bloch_diffs) < 1e-6:
            verdict = 'TRIVIAL'
        else:
            verdict = 'COMPATIBLE'
    else:
        verdict = 'BREAKS'

    return {
        'operator': op_name,
        'geometry': geom_name,
        'verdict': verdict,
        'manifold_fraction_initial': round(init_on, 4),
        'manifold_fraction_final': round(final_on, 4),
        'manifold_fraction_history': [round(x, 4) for x in manifold_frac_history],
        'avg_purity_change': round(float(avg_purity_change), 6),
        'avg_entropy_change': round(float(avg_entropy_change), 6),
        'avg_norm_change': round(float(avg_norm_change), 6),
        'purity_preserved': abs(avg_purity_change) < 1e-4,
        'entropy_preserved': abs(avg_entropy_change) < 1e-4,
        'norm_preserved': abs(avg_norm_change) < 1e-4,
    }


# ─── Attractor discovery ─────────────────────────────────────────────────────

def _cl3_rotor_as_matrix(angle, plane='xy'):
    """Pre-compute the Cl(3) rotor as a 3x3 rotation matrix (fast path)."""
    c, s = np.cos(angle), np.sin(angle)
    if plane == 'xy':
        return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    elif plane == 'xz':
        return np.array([[c, 0, -s], [0, 1, 0], [s, 0, c]])
    else:  # yz
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def discover_attractor(op_name, n_states=100, n_iter=50):
    """Apply operator to random states, find where outputs cluster."""
    rng = np.random.RandomState(99)
    states = []
    for _ in range(n_states):
        # Random state in Bloch ball
        r = rng.randn(3)
        r *= rng.uniform(0.0, 1.0) / max(np.linalg.norm(r), 1e-10)
        states.append(bloch_to_rho(r))

    # Pre-compute cl3 rotation matrix for speed (mathematically identical)
    cl3_rot_mat = _cl3_rotor_as_matrix(np.pi / 7, 'xy')

    # Iterate
    evolved = [s.copy() for s in states]
    for _ in range(n_iter):
        new_evolved = []
        for rho in evolved:
            if op_name == 'cl3_rotor':
                b = rho_to_bloch(rho)
                b_rot = cl3_rot_mat @ b  # fast matrix multiply
                new_rho = bloch_to_rho(b_rot)
            else:
                new_rho = OPERATORS[op_name](rho)
            new_evolved.append(new_rho)
        evolved = new_evolved

    # Analyze final distribution
    bloch_vecs = np.array([rho_to_bloch(s) for s in evolved])
    norms = np.linalg.norm(bloch_vecs, axis=1)
    purities_arr = np.array([purity(s) for s in evolved])

    centroid = np.mean(bloch_vecs, axis=0)
    spread = np.std(norms)
    mean_norm = np.mean(norms)

    # Check if operator preserves Bloch norms (unitary / isometry)
    init_bloch = np.array([rho_to_bloch(s) for s in states])
    init_norms = np.linalg.norm(init_bloch, axis=1)
    norm_deltas = np.abs(norms - init_norms)
    norm_preserving = np.max(norm_deltas) < 1e-6

    # Classify attractor geometry
    if mean_norm < 0.05:
        attractor = 'point (maximally mixed center)'
    elif norm_preserving:
        # Unitary: no attractor, each state orbits on its own shell
        attractor = 'NONE (unitary: norm-preserving, orbits on concentric shells)'
    elif spread < 0.05 and np.mean(purities_arr) > 0.99:
        # All converge to sphere, check if clustered at a pole
        centroid_norm = np.linalg.norm(centroid)
        if centroid_norm > 0.9:
            attractor = f'point on S2 (pole): centroid=({centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f})'
        else:
            attractor = 'S2 (full sphere, orbit closure)'
    elif spread < 0.05 and abs(mean_norm - norms[0]) < 0.05:
        # All at same radius but not pure
        attractor = f'sphere at r={mean_norm:.3f} (contracted S2)'
    else:
        # Check z-axis clustering
        xy_spread = np.std(np.sqrt(bloch_vecs[:, 0]**2 + bloch_vecs[:, 1]**2))
        z_spread = np.std(bloch_vecs[:, 2])
        if xy_spread < 0.05 and z_spread > 0.1:
            attractor = 'Z-axis (line segment)'
        elif xy_spread < 0.05 and z_spread < 0.05:
            attractor = f'point: ({centroid[0]:.3f}, {centroid[1]:.3f}, {centroid[2]:.3f})'
        else:
            # Check x-axis clustering (for x_dephasing)
            yz_spread = np.std(np.sqrt(bloch_vecs[:, 1]**2 + bloch_vecs[:, 2]**2))
            x_spread = np.std(bloch_vecs[:, 0])
            if yz_spread < 0.05 and x_spread > 0.1:
                attractor = 'X-axis (line segment)'
            else:
                attractor = f'diffuse region: mean_r={mean_norm:.3f}, spread={spread:.3f}'

    return {
        'operator': op_name,
        'attractor_geometry': attractor,
        'mean_bloch_norm': round(float(mean_norm), 4),
        'norm_spread': round(float(spread), 4),
        'mean_purity': round(float(np.mean(purities_arr)), 4),
        'centroid': [round(float(x), 4) for x in centroid],
        'n_states': n_states,
        'n_iterations': n_iter,
    }


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("OPERATOR-GEOMETRY COMPATIBILITY SIM")
    print("8 operators x 6 geometries = 48 cells")
    print("=" * 70)
    t0 = time.time()

    op_names = list(OPERATORS.keys()) + ['cl3_rotor'] if 'cl3_rotor' not in OPERATORS or OPERATORS.get('cl3_rotor') is None else list(OPERATORS.keys())
    # Deduplicate
    op_names = ['uz_rotation', 'ux_rotation', 'su2_rotation',
                'z_dephasing', 'x_dephasing', 'depolarizing',
                'amplitude_damping', 'cl3_rotor']
    geom_names = list(GEOMETRIES.keys())

    # ── 48-cell matrix ──
    print("\n--- Running 48-cell compatibility matrix ---")
    results_matrix = {}
    all_cells = []
    for op in op_names:
        results_matrix[op] = {}
        for geom in geom_names:
            print(f"  {op:20s} x {geom:15s} ... ", end='', flush=True)
            cell = test_cell(op, geom)
            results_matrix[op][geom] = cell
            all_cells.append(cell)
            print(cell['verdict'])

    # ── Attractor discovery ──
    print("\n--- Running attractor discovery ---")
    attractor_results = {}
    for op in op_names:
        print(f"  {op:20s} ... ", end='', flush=True)
        att = discover_attractor(op)
        attractor_results[op] = att
        print(att['attractor_geometry'])

    # ── Summary matrix display ──
    print("\n" + "=" * 70)
    print("COMPATIBILITY MATRIX")
    print("=" * 70)
    header = f"{'Operator':>22s} | " + " | ".join(f"{g:>12s}" for g in geom_names)
    print(header)
    print("-" * len(header))
    for op in op_names:
        row = f"{op:>22s} | "
        cells = []
        for geom in geom_names:
            v = results_matrix[op][geom]['verdict']
            cells.append(f"{v:>12s}")
        row += " | ".join(cells)
        print(row)

    # ── Summary statistics ──
    print("\n" + "=" * 70)
    print("ATTRACTOR DISCOVERY")
    print("=" * 70)
    for op in op_names:
        att = attractor_results[op]
        print(f"  {op:22s} -> {att['attractor_geometry']}")
        print(f"    mean |r|={att['mean_bloch_norm']:.4f}  "
              f"spread={att['norm_spread']:.4f}  "
              f"purity={att['mean_purity']:.4f}")

    # ── Verdict counts ──
    verdicts = [c['verdict'] for c in all_cells]
    print(f"\nVERDICT TOTALS: "
          f"COMPATIBLE={verdicts.count('COMPATIBLE')}  "
          f"BREAKS={verdicts.count('BREAKS')}  "
          f"TRIVIAL={verdicts.count('TRIVIAL')}")

    # ── Save results ──
    output = {
        'name': 'operator_geometry_compatibility',
        'sim': 'operator_geometry_compatibility',
        'description': 'Supporting compatibility matrix between operator families and geometry manifolds, plus attractor discovery.',
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'n_operators': len(op_names),
        'n_geometries': len(geom_names),
        'n_cells': len(all_cells),
        'compatibility_matrix': results_matrix,
        'attractor_discovery': attractor_results,
        'tool_manifest': TOOL_MANIFEST,
        'tool_integration_depth': TOOL_INTEGRATION_DEPTH,
        'summary': {
            'compatible_count': verdicts.count('COMPATIBLE'),
            'breaks_count': verdicts.count('BREAKS'),
            'trivial_count': verdicts.count('TRIVIAL'),
            'all_cells_accounted_for': verdicts.count('COMPATIBLE') + verdicts.count('BREAKS') + verdicts.count('TRIVIAL') == len(all_cells),
        },
        'classification': 'supporting',
        'classification_note': 'Supporting compatibility-map lego. Useful for operator/geometry routing, not a closure-grade proof or full promotion surface.',
        'elapsed_seconds': round(time.time() - t0, 2),
    }

    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'a2_state', 'sim_results')
    out_path = os.path.join(out_dir, 'operator_geometry_compatibility_results.json')
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"\nResults saved to: {out_path}")
    print(f"Elapsed: {output['elapsed_seconds']}s")

    return output


if __name__ == '__main__':
    main()
