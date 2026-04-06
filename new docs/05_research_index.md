# Research Index — Compression and Systems Math

This file links the research terms that now belong in the systems-math layer.

## Core terms
- Principal component analysis (PCA)
- Quantum principal component analysis (QPCA)
- Singular value decomposition (SVD)
- Schmidt decomposition
- covariance matrix / covariance operator
- density matrix / density operator
- low-rank approximation
- entanglement spectrum
- principal subspace

## Why these are grouped together
They all express the same basic move:
- find dominant modes of an operator
- keep the strongest modes
- compress the rest

## What this means for the engine
The engine already supports the operator vocabulary needed for this family:
- partial traces
- correlation tensors
- joint density matrices
- spectral checks
- entanglement measures
- graph/topology gates

So the research question is not whether compression mathematics belongs here.
The question is which spectral form best matches the runtime object.

## Current best alignment
- PCA for classical covariance structure
- QPCA for quantum-access spectral extraction
- Schmidt decomposition for bipartite pure states
- low-rank density operators for mixed-state compression

## Promotion rule
A new compression method belongs here if it can be stated as a principal-subspace / spectral-truncation / low-rank operator problem.
