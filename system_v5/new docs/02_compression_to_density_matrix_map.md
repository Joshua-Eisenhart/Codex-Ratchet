# Compression Mathematics to Density-Matrix Map

## Canonical mapping

| Compression family | Native object | Density-matrix form | What to keep |
|---|---|---|---|
| PCA | covariance matrix | spectral decomposition of covariance | top eigenvectors |
| QPCA | density operator / covariance operator | dominant eigenmodes of the operator | principal subspace |
| SVD | matrix factorization | operator low-rank factorization | leading singular vectors |
| Schmidt decomposition | bipartite pure state | singular modes of the bipartite amplitude | top Schmidt modes |
| low-rank approximation | matrix / operator | PSD low-rank approximation | dominant spectrum |
| spectral truncation | Hermitian operator | eigenvalue thresholding | large eigenvalues |
| coarse-graining | state or observable family | projection to a reduced operator algebra | retained macro-modes |
| entanglement compression | bipartite state | truncation in Schmidt basis | leading entangled modes |

## Safe compression pattern
A compression method is system-compatible when it can be written as:
1. build operator
2. diagonalize or factorize operator
3. keep leading modes
4. reconstruct a valid density operator
5. renormalize and enforce positivity if needed

## Geometry-friendly operators
The following are the most natural ways to compress within the current geometry stack:
- covariance operator of Bloch/correlation data
- joint density matrix of two subsystems
- correlation tensor C_ij
- entanglement spectrum
- reduced density matrices from partial traces

## What to avoid
- compression with no spectral interpretation
- lossy transforms that break positivity or trace normalization
- ad hoc coordinates that cannot be mapped back to observables

## Rule of thumb
If the compression target can be represented as a principal subspace, a Schmidt basis, or a low-rank density operator, then it belongs in this system.
