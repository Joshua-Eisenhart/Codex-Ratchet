#!/usr/bin/env python3

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
