# Source Notes

These are the source-derived anchors used for the research synthesis.

## PCA sources
- Wikipedia: Principal component analysis
  - PCA is a linear dimensionality-reduction method.
  - It finds orthogonal directions of maximal variance.
  - The principal directions are the eigenvectors of the covariance matrix.
  - The corresponding eigenvalues measure variance along those directions.

## Quantum PCA sources
- arXiv search results for "quantum principal component analysis Lloyd"
  - classic paper visible: `arXiv:1307.0401` — "Quantum principal component analysis" by Seth Lloyd, Masoud Mohseni, Patrick Rebentrost
  - later papers visible in the same search include:
    - `arXiv:1903.03999` — "An Improved Algorithm for Quantum Principal Component Analysis"
    - `arXiv:1811.00414` — "Quantum principal component analysis only achieves an exponential speedup because of its state preparation assumptions"
    - `arXiv:2104.02476` — "Resonant Quantum Principal Component Analysis"

## Alignment takeaway
The central shared structure is spectral extraction:
- covariance eigenvectors in PCA
- principal subspaces in QPCA
- Schmidt modes in bipartite states
- low-rank truncation in density-matrix compression

## Status
- source-note: yes
- canonical: no
- use for doc synthesis: yes
- use for runtime implementation directly: no
