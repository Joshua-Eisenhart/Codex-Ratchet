#!/usr/bin/env python3

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
