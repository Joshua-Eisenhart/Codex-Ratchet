# TENSOR_FORMAT — dual-engine PEPS handshake (D=2 structured iPEPS tensor)

## Tensor
- File: `ipeps_heisenberg_D2.npy`
- Shape: `[p, u, r, d, l]` = (physical=2, up=D, right=D, down=D, left=D), D=2
- dtype: `complex128`
- Ansatz: single-site (1x1 unit cell) iPEPS, sublattice pi-rotation folded in.
- This tensor is a LIGHT-OPTIMIZED structured/physical tensor (not the true GS);
  it was optimized against the EXACT L=4 torus energy for 120 Adam steps.

## Hamiltonian convention
- S=1/2 antiferromagnetic Heisenberg, infinite square lattice.
- Jx: 1.0
- Jy: 1.0
- Jz: 1.0
- spin: 1//2
- Rotated bond used by the JAX optimizer: `H_rot = -SxSx - SySy + SzSz`
  (sublattice pi-rotation; equals true AFM per-site energy since the rotation is
  a local unitary). PEPSKit's `heisenberg_XYZ` with Jx=Jy=Jz=1.0 contracts the
  SAME tensor with the rotation folded into the saved tensor.
- Per-site energy = 2 * <H>_bond (2 bonds/site on the square lattice).

## EXACT finite-torus energy of THIS tensor (the REFERENCE — trust this, NOT CTMRG)
- This is a true Rayleigh quotient <psi|H|psi>/<psi|psi> on an L x L periodic
  lattice: no eigendecomposition, no truncation, always a valid variational bound.
- torus L=4: E/site = -0.037979
- torus L=5: E/site = -0.054095
- torus L=6: E/site = -0.061694

## Handshake target for the Julia/PEPSKit CTMRG cross-check
- jax_energy_per_site = -0.061694    (the L=6 exact torus energy)
- Compare PEPSKit CTMRG per-site energy to THIS value.
- Prior finding: the hand-rolled JAX CTMRG diverges from the exact torus energy
  for structured tensors (gave -0.30 vs torus -0.577). CTMRG is reliable only for
  random tensors. The exact torus energy is the ground truth here.

## JAX-CTMRG energy of this same tensor (for the record; expected to diverge)
- jax_ctmrg_chi16_per_site = -0.6297439490028554
