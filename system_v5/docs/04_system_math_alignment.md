# System Math Alignment

## The current system already speaks spectral language
The engine stack already uses objects that naturally support compression mathematics:
- density matrices
- Bloch vectors
- correlation tensors
- partial traces
- concurrence / entanglement measures
- covariance-like operators
- graph and topology gates

## Where compression math fits

### 1. State compression
Use dominant eigenmodes of a density matrix or reduced density matrix.

### 2. Correlation compression
Use the 3x3 correlation tensor C_ij and keep its principal directions.

### 3. Bipartite compression
Use Schmidt decomposition or SVD on the pure-state amplitude.

### 4. Operator compression
Use low-rank spectral approximation of the evolution / transport operator.

### 5. Geometry compression
Use basis changes that preserve the meaning of the geometric generators.

## Good candidate math families
- PCA
- quantum PCA
- SVD
- Schmidt decomposition
- spectral truncation
- low-rank PSD approximation
- covariance/operator eigendecomposition

## Better phrasing for this repo
Instead of saying "compression" generically, specify:
- covariance spectral compression
- Schmidt-mode truncation
- density-operator low-rank approximation
- principal-subspace retention
- entanglement-spectrum truncation

That keeps the math grounded in the operator language the system already uses.
