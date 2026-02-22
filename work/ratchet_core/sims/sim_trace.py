#!/usr/bin/env python3

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
