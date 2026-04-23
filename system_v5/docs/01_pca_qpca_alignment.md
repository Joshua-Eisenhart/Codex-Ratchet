# PCA, Quantum PCA, and the Density-Matrix View

## Why this matters
A large class of compression methods can be expressed as selecting dominant modes of a matrix or operator. In this system, those operators are naturally represented as density matrices, correlation matrices, or covariance operators.

## Classical PCA
Principal component analysis (PCA) is a linear method that:
- centers the data
- computes a covariance matrix
- diagonalizes that covariance matrix
- keeps the eigenvectors with the largest eigenvalues

Interpretation:
- eigenvectors = principal directions
- eigenvalues = variance carried by each direction
- truncation to the top-k components = compression

## Quantum PCA
Quantum principal component analysis (QPCA) is the quantum-algorithm version of the same spectral idea.
It is usually framed as:
- a quantum-access model for a density operator or covariance operator
- extraction of dominant eigenvalues/eigenvectors or principal subspaces
- phase-estimation-style readout of spectral structure

Important caveat:
- QPCA is not a generic magic replacement for PCA
- it depends on strong state-preparation and access assumptions
- speedups are tied to those assumptions and to spectral gaps

## Density-matrix translation
In this system, a compression procedure should usually be rewritten as one of:
- spectral truncation of a density matrix
- low-rank approximation of a correlation tensor
- Schmidt-mode truncation of a bipartite state
- projection onto the dominant eigenspace of a covariance operator

That gives a physically meaningful representation because:
- trace 1 is preserved for states
- positivity can be enforced
- principal modes remain interpretable as real structure rather than arbitrary coordinates

## Natural equivalences in this repo
- PCA ↔ covariance eigendecomposition
- SVD ↔ low-rank factorization
- Schmidt decomposition ↔ bipartite PCA of a pure state
- QPCA ↔ quantum-access spectral extraction
- entanglement spectrum ↔ spectral compression of joint states
- coarse-graining ↔ projection onto dominant modes

## System implication
If a proposed compression method can be rewritten as a dominant-subspace operator, it is likely admissible in the system math.
If it cannot be phrased in spectral / operator language, it is probably only a heuristic wrapper.
