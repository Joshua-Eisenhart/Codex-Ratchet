# PCA / QPCA Source Digest

## PCA digest
- PCA is a linear method.
- It uses covariance.
- It extracts orthogonal principal directions.
- It keeps the largest-variance eigenmodes.
- It is a compression / denoising / visualization tool.

## QPCA digest
- QPCA is the quantum-algorithm analogue of PCA.
- The classic paper is Lloyd, Mohseni, Rebentrost (arXiv:1307.0401).
- The method targets dominant spectral structure of a density operator or covariance operator.
- Later work emphasizes assumptions and limitations, especially state-preparation cost.
- A resonant variant appears in later experimental / algorithmic work.

## Alignment labels
- PCA -> covariance eigen-decomposition
- QPCA -> quantum-access spectral extraction
- Schmidt decomposition -> bipartite principal-mode extraction
- low-rank density approximation -> valid compression primitive

## Promotion rule
If a note below can be rewritten as a dominant-subspace / operator-spectral statement, it can move to `new docs/`.
