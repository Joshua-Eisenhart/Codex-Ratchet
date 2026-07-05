# tower_g6g7_spinor_hopf_v0

Scratch diagnostic three-engine rung for G6/G7 from `ASSEMBLY_INVENTORY_20260704.md`.

- G6: spinor lift `S3 = {psi in C^2 : ||psi|| = 1}` runs on the G5 density floor. The rung computes `rho` first, then admits the lift only to witness distinctions erased by `rho`: identical density readouts but 2pi spinor sign/4pi return.
- G7: Hopf envelope `pi:S3->S2` on tori `T_eta` with `A = dphi + cos(2eta)dchi`. It checks three eta values against `-2pi*cos(2eta)`.
- Controls: rho-only cannot separate the 720 split, flat/plain-S2 kills the connection witness, and label shuffle preserves density.

Classification is `scratch_diagnostic`; `promotion_allowed=false`.
