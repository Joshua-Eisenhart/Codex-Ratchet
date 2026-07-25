#!/usr/bin/env python3
"""
Engine reality check -- PYTORCH leg.

Single qubit, density-operator formalism only (no Bloch parametrisation).

    rho0  = [[0.75, 0.25], [0.25, 0.25]]
    H     = 0.5 * sigma_z,          sigma_z      = diag(1, -1)
    gamma = 0.3
    L     = sqrt(gamma) * sigma_minus,  sigma_minus = [[0, 0], [1, 0]]

GKSL generator:
    drho/dt = -i[H, rho] + L rho L^dag - 0.5 {L^dag L, rho}

Integrated to t = 1.0 by EXACT matrix exponential of the vectorised Liouvillian,
column-stacking convention:  vec(A X B) = (B^T kron A) vec(X).

Everything in torch.complex128. No hand-rolled ODE stepping anywhere.

Torch surface actually called (recorded in the JSON as torch_functions_called):
    torch.tensor, torch.eye, torch.kron, torch.linalg.matrix_exp,
    torch.linalg.eigvalsh, torch.matmul, torch.conj, torch.transpose,
    torch.reshape, torch.diagonal, torch.sum, torch.log2, torch.abs,
    torch.max, torch.min, torch.isfinite,
    Tensor.mH (conjugate transpose), Tensor.contiguous, Tensor.real, Tensor.item
"""

import json
import os
import sys

import torch

CDTYPE = torch.complex128
RDTYPE = torch.float64
N = 2
T_FINAL = 1.0
GAMMA = 0.3
TOL = 1e-12


# ---------------------------------------------------------------- vectorisation
def vec_col(mat: torch.Tensor) -> torch.Tensor:
    """Column-stacking vectorisation: vec(X)[i + N*j] = X[i, j].

    torch reshape is row-major, so the row-major flatten of X^T stacks columns.
    """
    return torch.reshape(torch.transpose(mat, 0, 1), (-1,))


def unvec_col(vec: torch.Tensor) -> torch.Tensor:
    """Inverse of vec_col."""
    return torch.transpose(torch.reshape(vec, (N, N)), 0, 1).contiguous()


def main() -> int:
    # ------------------------------------------------------------- operators
    rho0 = torch.tensor([[0.75, 0.25], [0.25, 0.25]], dtype=CDTYPE)
    sigma_z = torch.tensor([[1.0, 0.0], [0.0, -1.0]], dtype=CDTYPE)
    sigma_minus = torch.tensor([[0.0, 0.0], [1.0, 0.0]], dtype=CDTYPE)
    eye = torch.eye(N, dtype=CDTYPE)

    H = 0.5 * sigma_z
    L = (GAMMA ** 0.5) * sigma_minus
    Ldag = L.mH                      # conjugate transpose
    LdagL = torch.matmul(Ldag, L)

    # --------------------------------------------- vectorised Liouvillian
    # vec(A X B) = (B^T kron A) vec(X), column stacking.
    #
    #   -i[H, rho]                 ->  -i ( I kron H  -  H^T kron I )
    #   L rho L^dag                ->  ( (L^dag)^T kron L ) = ( conj(L) kron L )
    #   -0.5 {L^dag L, rho}        ->  -0.5 ( I kron LdagL + LdagL^T kron I )
    # NOTE (measured): torch.kron rejects the non-contiguous view that
    # torch.transpose returns -- "view size is not compatible with input
    # tensor's size and stride". The .contiguous() calls are load-bearing.
    Ht = torch.transpose(H, 0, 1).contiguous()
    LdagLt = torch.transpose(LdagL, 0, 1).contiguous()
    conjL = torch.conj(L).contiguous()
    minus_i = torch.tensor(-1.0j, dtype=CDTYPE)

    ham_part = minus_i * (torch.kron(eye, H) - torch.kron(Ht, eye))
    jump_part = torch.kron(conjL, L)
    anti_part = -0.5 * (torch.kron(eye, LdagL) + torch.kron(LdagLt, eye))

    liouvillian = ham_part + jump_part + anti_part

    # ----------------------------------------- exact propagation to t = 1.0
    propagator = torch.linalg.matrix_exp(liouvillian * T_FINAL)
    rho_t = unvec_col(torch.matmul(propagator, vec_col(rho0)))

    # ------------------------------------------------------------ readouts
    trace_t = torch.sum(torch.diagonal(rho_t))
    purity = torch.sum(torch.diagonal(torch.matmul(rho_t, rho_t)))

    def vn_entropy_log2(rho: torch.Tensor):
        """S = -Tr(rho log2 rho) via the Hermitian eigenvalues of rho."""
        evals = torch.linalg.eigvalsh(rho)          # real, ascending
        keep = evals[evals > 1e-15]
        s = -torch.sum(keep * torch.log2(keep))
        return s, evals

    S_t, evals_t = vn_entropy_log2(rho_t)
    S_0, evals_0 = vn_entropy_log2(rho0)

    t1_pop = rho_t[0, 0].real
    t2_coh_re = rho_t[0, 1].real
    t3_purity = purity.real
    t4_vn = S_t
    t5_trace = trace_t.real

    # -------------------------------------------------------- self-checks
    # C1 trace preserved to 1e-12
    trace_err = torch.abs(trace_t - torch.tensor(1.0 + 0.0j, dtype=CDTYPE))
    c1 = bool((trace_err <= TOL).item())

    # C2 Hermitian to 1e-12
    herm_err = torch.max(torch.abs(rho_t - rho_t.mH))
    c2 = bool((herm_err <= TOL).item())

    # C3 eigenvalues >= -1e-12
    min_eval = torch.min(evals_t)
    c3 = bool((min_eval >= -TOL).item())

    # C4 S(rho0) recomputed and reported beside S(rho_t)
    c4 = bool(torch.isfinite(S_0).item() and torch.isfinite(S_t).item())

    # ---------------------------- independent analytic cross-check (not a T value)
    # Closed form for this generator: rho00(t) = rho00(0) e^{-gamma t};
    # rho01(t) = rho01(0) e^{-(i + gamma/2) t}.  Used only to catch a wiring error
    # in the Liouvillian; the reported numbers all come from matrix_exp above.
    import cmath
    an_pop = 0.75 * cmath.exp(-GAMMA * T_FINAL).real
    an_coh = (0.25 * cmath.exp(-(1j + 0.5 * GAMMA) * T_FINAL)).real
    xcheck_pop_absdiff = abs(float(t1_pop.item()) - an_pop)
    xcheck_coh_absdiff = abs(float(t2_coh_re.item()) - an_coh)

    def f12(x) -> str:
        return f"{float(x):.12g}"

    print("=== PYTORCH GKSL leg (system_v8/engine_reality_check) ===")
    print(f"torch {torch.__version__}   dtype {CDTYPE}   t = {T_FINAL}   gamma = {GAMMA}")
    print(f"T1 rho_t[0,0] population      = {f12(t1_pop)}")
    print(f"T2 Re(rho_t[0,1]) coherence   = {f12(t2_coh_re)}")
    print(f"T3 purity Tr(rho_t^2)         = {f12(t3_purity)}")
    print(f"T4 von Neumann S (log2)       = {f12(t4_vn)}")
    print(f"T5 trace Tr(rho_t)            = {f12(t5_trace)}")
    print(f"C1 trace preserved <=1e-12    : {c1}   |Tr-1| = {float(trace_err.item()):.3e}")
    print(f"C2 Hermitian <=1e-12          : {c2}   max|rho-rho^dag| = {float(herm_err.item()):.3e}")
    print(f"C3 eigenvalues >= -1e-12      : {c3}   min eig = {f12(min_eval)}")
    print(f"C4 S(rho0) vs S(rho_t)        : {c4}   S(rho0) = {f12(S_0)}   S(rho_t) = {f12(S_t)}")
    print(f"eigenvalues rho_t             = [{f12(evals_t[0])}, {f12(evals_t[1])}]")
    print(f"eigenvalues rho0              = [{f12(evals_0[0])}, {f12(evals_0[1])}]")
    print(f"xcheck analytic |dpop|        = {xcheck_pop_absdiff:.3e}")
    print(f"xcheck analytic |dcoh|        = {xcheck_coh_absdiff:.3e}")

    payload = {
        "engine": "pytorch",
        "torch_version": torch.__version__,
        "dtype": "torch.complex128",
        "method": "exact matrix exponential of vectorised Liouvillian (column stacking)",
        "t": T_FINAL,
        "gamma": GAMMA,
        "t1_pop": float(t1_pop.item()),
        "t2_coh_re": float(t2_coh_re.item()),
        "t3_purity": float(t3_purity.item()),
        "t4_vn_entropy_log2": float(t4_vn.item()),
        "t5_trace": float(t5_trace.item()),
        "c1": c1,
        "c2": c2,
        "c3": c3,
        "c4": c4,
        "c1_trace_abs_err": float(trace_err.item()),
        "c2_hermitian_max_abs_err": float(herm_err.item()),
        "c3_min_eigenvalue": float(min_eval.item()),
        "c4_S_rho0_log2": float(S_0.item()),
        "c4_S_rhot_log2": float(S_t.item()),
        "eigenvalues_rho_t": [float(v) for v in evals_t],
        "eigenvalues_rho0": [float(v) for v in evals_0],
        "sig12": {
            "t1_pop": f12(t1_pop),
            "t2_coh_re": f12(t2_coh_re),
            "t3_purity": f12(t3_purity),
            "t4_vn_entropy_log2": f12(t4_vn),
            "t5_trace": f12(t5_trace),
        },
        "analytic_crosscheck": {
            "note": "independent closed form, used only to detect Liouvillian miswiring",
            "pop_abs_diff": xcheck_pop_absdiff,
            "coh_abs_diff": xcheck_coh_absdiff,
        },
        "torch_functions_called": [
            "torch.tensor", "torch.eye", "torch.kron", "torch.linalg.matrix_exp",
            "torch.linalg.eigvalsh", "torch.matmul", "torch.conj",
            "torch.transpose", "torch.reshape", "torch.diagonal", "torch.sum",
            "torch.log2", "torch.abs", "torch.max", "torch.min",
            "torch.isfinite", "Tensor.mH", "Tensor.contiguous",
            "Tensor.real", "Tensor.item",
        ],
    }

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "pytorch_gksl_leg.json")
    with open(out_path, "w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(f"wrote {out_path}")

    # ONE json object on the last line.
    print(json.dumps({
        "t1_pop": payload["t1_pop"],
        "t2_coh_re": payload["t2_coh_re"],
        "t3_purity": payload["t3_purity"],
        "t4_vn_entropy_log2": payload["t4_vn_entropy_log2"],
        "t5_trace": payload["t5_trace"],
        "c1": c1, "c2": c2, "c3": c3, "c4": c4,
    }))

    return 0 if (c1 and c2 and c3 and c4) else 1


if __name__ == "__main__":
    sys.exit(main())
