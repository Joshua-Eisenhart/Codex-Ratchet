# Probe lane 2 — root strata spec (n = 4)

Fixed by the owner dependency diagram. Every lane computes these independently.
No lane reads another lane's output. `compare_lanes.py` is the only reader.

## R0 finite binary address set
J = {0,1}^4 encoded as integers 0..15, bit i of j = (j >> i) & 1.
`cardinality` = |J| by enumeration. `H0_addr` = log2 |J|.

## R1 pair-indexed field over the same J
Omega = J x J, 256 ordered pairs.
- DIAG      F[j][k] = 1 iff j == k
- COHERENT  F[j][k] = 1 iff popcount(j XOR k) <= 1
Per field: `support_cardinality` = |supp F|, `H0_pair` = log2 |supp F|,
integer-matrix `rank`, integer `determinant`, and exact eigenvalue multiplicities
(nullity of M - lambda*I).

## R2 finite cubical complex K on the 4-cube
Cells = strings over {0,1,*} of length 4; dim = number of '*'.
Cubical boundary, free coords i_1 < ... < i_d:
  d(c) = sum_m (-1)^m ( c[i_m := 1] - c[i_m := 0] )
Face maps as integer matrices d_1..d_4. Measured: max |entry| of d_{k-1} d_k.

## R3 fibred finite pair relation
E = coprod_{c in K} {c} x R_c, pi : E -> K, kappa(c) = log2 |R_c|.
- FULL_FIELD  R_c = J x J for every cell
- RESTRICTED  R_c = {(j,k) : j,k both in subcube(c) and popcount(j XOR k) <= 1}
Reported: |R_c| and kappa(c) per cell-dimension class, and |E| = sum_c |R_c|.

## C1-C3 quotient, fibres, extension capacity
Probe family Pi = { p_popcount }, q(j) = popcount(j), Q = {0,1,2,3,4}.
`fibre_cardinality` per class, `kappa_ext(u)` = log2 |Fib(u)|.
TYPED RELEASE Release_q(u) = the fibre DESCRIPTOR. Empty-fibre case u = 5:
the descriptor must carry cardinality 0 and MUST NOT carry a kappa key
(ABSENT = key not present), and no log2/division may be evaluated on it.
Each lane counts its own log2 invocations across the empty release to measure that.
