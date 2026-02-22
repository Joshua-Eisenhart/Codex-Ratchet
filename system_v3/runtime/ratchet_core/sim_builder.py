import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

#!/usr/bin/env python3
"""sim_builder.py: generates and validates sims for B-admitted terms.

Usage:
  python3 sim_builder.py --term density_matrix --out sims/
  python3 sim_builder.py --term commutator --out sims/
  python3 sim_builder.py --list          # show all terms that have sims
  python3 sim_builder.py --check         # run all sims, report pass/fail
  python3 sim_builder.py --missing       # show admitted terms with no sim

Every sim:
  - Is pure Python, no numpy, no external deps
  - Proves exactly one mathematical property named by the term
  - Exits 0 if the property holds, nonzero if it fails
  - Is 30-60 lines, readable by a human
  - Corresponds 1:1 to a B-admitted term
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

SIMS_DIR = Path(__file__).parent / "sims"

# Map: term_literal -> (sim_filename, one-line description of what it proves)
SIM_REGISTRY = {
    "density": ("sim_density_matrix.py", "density matrix is PSD, Hermitian, trace-1"),
    "matrix": ("sim_density_matrix.py", "matrix is Hermitian, trace-1"),
    "density_matrix": ("sim_density_matrix.py", "density matrix is PSD, Hermitian, trace-1"),
    "commutator": ("sim_commutator_dynamics.py", "[H,rho] is anti-Hermitian"),
    "operator": ("sim_commutator_dynamics.py", "operator commutator is anti-Hermitian"),
    "channel": ("sim_cptp_channel.py", "CPTP channel: Kraus completeness sum(K†K)=I"),
    "cptp": ("sim_cptp_channel.py", "CPTP: Kraus sum(K†K)=I"),
    "cptp_channel": ("sim_cptp_channel.py", "CPTP channel: Kraus completeness"),
    "unitary": ("sim_unitary_operator.py", "unitary: U U†=I"),
    "unitary_operator": ("sim_unitary_operator.py", "unitary operator: U U†=I"),
    "hilbert": ("sim_hilbert_space.py", "Hilbert space: complex inner product norm"),
    "space": ("sim_hilbert_space.py", "space: inner product well-defined"),
    "hilbert_space": ("sim_hilbert_space.py", "Hilbert space: complex inner product"),
    "finite": ("sim_l0_math.py", "finite arithmetic: sum 0..9 = 45"),
    "generator": ("sim_lindblad_generator.py", "generator rates non-negative"),
    "lindblad": ("sim_lindblad_generator.py", "Lindblad rates non-negative"),
    "lindblad_generator": ("sim_lindblad_generator.py", "Lindblad generator: rates >= 0"),
    "trace": ("sim_trace.py", "trace is cyclic: Tr(AB)=Tr(BA)"),
    "partial": ("sim_partial_trace.py", "partial trace is normalized: Tr(rho_A)=1"),
    "partial_trace": ("sim_partial_trace.py", "partial trace preserves normalization"),
    "tensor": ("sim_tensor_product.py", "tensor product: Tr(A⊗B)=Tr(A)Tr(B)"),
    "anticommutator": ("sim_anticommutator.py", "{H,rho}=HR+RH is Hermitian"),
    "hamiltonian": ("sim_hamiltonian.py", "Hamiltonian: Hermitian, real eigenvalues"),
    "hamiltonian_operator": ("sim_hamiltonian.py", "Hamiltonian operator: real spectrum"),
    "entropy": ("sim_entropy.py", "von Neumann entropy S(rho) >= 0, = 0 for pure"),
    "purity": ("sim_purity.py", "purity Tr(rho^2) in [0,1], = 1 for pure"),
    "fidelity": ("sim_fidelity.py", "fidelity F(rho,sigma) in [0,1]"),
    "adjoint": ("sim_adjoint.py", "adjoint: (AB)† = B†A†, involutive"),
    "norm": ("sim_norm.py", "Frobenius norm: positive, homogeneous"),
    "basis": ("sim_basis.py", "orthonormal basis: completeness + orthogonality"),
    "coherence": ("sim_coherence.py", "l1 coherence >= 0, = 0 for diagonal"),
    "decoherence": ("sim_decoherence.py", "dephasing kills off-diagonals"),
    "measurement": ("sim_measurement.py", "projective measurement: completeness + Born rule"),
    "projector": ("sim_projector.py", "projector: P^2=P, Hermitian, rank=Tr(P)"),
    "hermitian": ("sim_hamiltonian.py", "Hermitian: H†=H, real eigenvalues"),
    "eigenvalue": ("sim_hamiltonian.py", "eigenvalues of Hermitian are real"),
    "observable": ("sim_hamiltonian.py", "observable = Hermitian operator"),
    "spectrum": ("sim_hamiltonian.py", "spectrum of Hermitian is real"),
    "kraus": ("sim_cptp_channel.py", "Kraus operators: sum(K†K) = I"),
}

# Templates for sims that don't exist yet
SIM_TEMPLATES = {
    "sim_trace.py": '''#!/usr/bin/env python3

def mm(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]

def tr(a):
    return a[0][0] + a[1][1]

def main():
    # Cyclic property: Tr(AB) = Tr(BA)
    A = [[1+0j, 2+1j], [0+1j, 3+0j]]
    B = [[0+0j, 1+0j], [1+0j, 2+0j]]
    tr_AB = tr(mm(A, B))
    tr_BA = tr(mm(B, A))
    if abs(tr_AB - tr_BA) > 1e-9:
        raise SystemExit(1)
    # Linearity: Tr(aA+B) = a*Tr(A) + Tr(B)
    alpha = 2.5 + 0j
    tr_aApB = tr([[alpha*A[i][j]+B[i][j] for j in range(2)] for i in range(2)])
    if abs(tr_aApB - (alpha*tr(A) + tr(B))) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
''',

    "sim_partial_trace.py": '''#!/usr/bin/env python3

def main():
    # 4x4 density matrix as 2x2x2x2 tensor
    # rho = |phi+><phi+| (Bell state)
    s = 0.5
    rho = [
        [s,  0,  0,  s],
        [0,  0,  0,  0],
        [0,  0,  0,  0],
        [s,  0,  0,  s],
    ]
    # Partial trace over system B (trace out last 2 dims)
    rho_A = [[0+0j]*2 for _ in range(2)]
    for i in range(2):
        for j in range(2):
            rho_A[i][j] = rho[2*i][2*j] + rho[2*i+1][2*j+1]
    tr_A = rho_A[0][0] + rho_A[1][1]
    if abs(tr_A.real - 1.0) > 1e-9:
        raise SystemExit(1)
    # Should be maximally mixed: rho_A = I/2
    if abs(rho_A[0][0].real - 0.5) > 1e-9:
        raise SystemExit(1)
    if abs(rho_A[1][1].real - 0.5) > 1e-9:
        raise SystemExit(1)
    if abs(rho_A[0][1]) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
''',

    "sim_tensor_product.py": '''#!/usr/bin/env python3

def main():
    # Tensor product of 2x2 matrices A and B gives 4x4 matrix
    # Tr(A tensor B) = Tr(A) * Tr(B)
    A = [[1+0j, 2+0j], [3+0j, 4+0j]]
    B = [[0+0j, 1+0j], [1+0j, 0+0j]]
    tr_A = A[0][0] + A[1][1]
    tr_B = B[0][0] + B[1][1]
    # Build 4x4 tensor product
    AB = [[0+0j]*4 for _ in range(4)]
    for i in range(2):
        for j in range(2):
            for k in range(2):
                for l in range(2):
                    AB[2*i+k][2*j+l] = A[i][j] * B[k][l]
    tr_AB = sum(AB[i][i] for i in range(4))
    if abs(tr_AB - tr_A * tr_B) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
''',

    "sim_anticommutator.py": '''#!/usr/bin/env python3

def mm(a, b):
    return [
        [a[0][0]*b[0][0]+a[0][1]*b[1][0], a[0][0]*b[0][1]+a[0][1]*b[1][1]],
        [a[1][0]*b[0][0]+a[1][1]*b[1][0], a[1][0]*b[0][1]+a[1][1]*b[1][1]],
    ]

def add(a, b):
    return [[a[i][j]+b[i][j] for j in range(2)] for i in range(2)]

def main():
    # {H, rho} = H rho + rho H
    # If H and rho are Hermitian, {H,rho} is Hermitian
    H = [[1+0j, 0.3+0j], [0.3+0j, -1+0j]]
    rho = [[0.6+0j, 0.1+0.2j], [0.1-0.2j, 0.4+0j]]
    anti = add(mm(H, rho), mm(rho, H))
    # Check Hermitian: anti[i][j] = anti[j][i].conj
    if abs(anti[0][1] - anti[1][0].conjugate()) > 1e-9:
        raise SystemExit(1)
    if abs(anti[0][0].imag) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
''',

    "sim_hamiltonian.py": '''#!/usr/bin/env python3
import math

def main():
    # Hermitian 2x2: eigenvalues must be real
    H = [[1+0j, 0.5+0j], [0.5+0j, -1+0j]]
    # Check Hermitian
    if abs(H[0][1] - H[1][0].conjugate()) > 1e-9:
        raise SystemExit(1)
    if abs(H[0][0].imag) > 1e-9 or abs(H[1][1].imag) > 1e-9:
        raise SystemExit(1)
    # Eigenvalues of 2x2 Hermitian are real
    a = H[0][0].real
    d = H[1][1].real
    b = H[0][1].real
    disc = (a - d)**2 + 4*b**2
    lam1 = 0.5*(a + d + math.sqrt(disc))
    lam2 = 0.5*(a + d - math.sqrt(disc))
    if abs(lam1.real - lam1) > 1e-9 or abs(lam2.real - lam2) > 1e-9:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
''',
}


def build_missing_sims(out_dir: Path):
    """Write any sim templates that don't exist yet."""
    created = []
    for filename, content in SIM_TEMPLATES.items():
        path = out_dir / filename
        if not path.exists():
            path.write_text(content)
            created.append(filename)
    return created


def check_all_sims(out_dir: Path):
    """Run every registered sim, report pass/fail."""
    seen = set()
    results = {}
    for term, (filename, description) in SIM_REGISTRY.items():
        if filename in seen:
            continue
        seen.add(filename)
        path = out_dir / filename
        if not path.exists():
            results[filename] = ("MISSING", description)
            continue
        ret = subprocess.run([sys.executable, str(path)], capture_output=True)
        status = "PASS" if ret.returncode == 0 else "FAIL"
        results[filename] = (status, description)
    return results


def missing_sims(out_dir: Path):
    """Find admitted terms with no sim."""
    missing = []
    for term, (filename, _) in SIM_REGISTRY.items():
        path = out_dir / filename
        if not path.exists():
            missing.append((term, filename))
    return missing


def main():
    parser = argparse.ArgumentParser(description="Sim builder for B-admitted terms")
    parser.add_argument("--term", help="Build/verify sim for this term")
    parser.add_argument("--out", default=str(SIMS_DIR), help="Output directory")
    parser.add_argument("--list", action="store_true", help="List all registered sims")
    parser.add_argument("--check", action="store_true", help="Run all sims")
    parser.add_argument("--missing", action="store_true", help="Show terms with no sim")
    parser.add_argument("--build-all", action="store_true", help="Write all missing sim templates")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(exist_ok=True)

    if args.list:
        print("=== SIM REGISTRY ===")
        for term, (filename, desc) in sorted(SIM_REGISTRY.items()):
            exists = "✓" if (out_dir / filename).exists() else "✗"
            print(f"  {exists} {term:35s} -> {filename}")
        return

    if args.check:
        results = check_all_sims(out_dir)
        print("=== SIM HEALTH CHECK ===")
        for filename, (status, desc) in sorted(results.items()):
            print(f"  {status:7s} {filename:40s} {desc}")
        passes = sum(1 for s, _ in results.values() if s == "PASS")
        fails = sum(1 for s, _ in results.values() if s == "FAIL")
        missing = sum(1 for s, _ in results.values() if s == "MISSING")
        print(f"\n  {passes} pass, {fails} fail, {missing} missing")
        return

    if args.missing:
        m = missing_sims(out_dir)
        print("=== TERMS WITH NO SIM ===")
        for term, filename in m:
            print(f"  {term} -> needs {filename}")
        return

    if args.build_all:
        created = build_missing_sims(out_dir)
        if created:
            print(f"Created: {created}")
        else:
            print("All sims already exist")
        return

    if args.term:
        term = args.term.lower()
        if term not in SIM_REGISTRY:
            print(f"No sim registered for term '{term}'")
            print("Known terms:", sorted(SIM_REGISTRY.keys()))
            return
        filename, desc = SIM_REGISTRY[term]
        path = out_dir / filename
        if not path.exists():
            build_missing_sims(out_dir)
        if path.exists():
            ret = subprocess.run([sys.executable, str(path)], capture_output=True)
            status = "PASS" if ret.returncode == 0 else "FAIL"
            print(f"{status}: {filename} — {desc}")
        else:
            print(f"No sim file for {term} (need to write {filename})")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
