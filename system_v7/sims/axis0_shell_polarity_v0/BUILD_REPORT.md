# Axis0 Shell Polarity v0

Status: `scratch_diagnostic`; `promotion_allowed=false`; capstone
`DRAFT_UNAUDITED`.

Source card:
`system_v7/constraint_core/reference_docs_from_josh/physics_program/JOSHUA_EISENHART_AXIS0_PHYSICS_MODEL_CORE_20260526.md`.

Object tested: section 22 Axis0-near object, specifically the
shell-polarity readout of the possibility field.

Build:
- finite shells `r=1..6`;
- finite `Omega_r` as four two-step Kraus-history branches;
- compatibility weights `P_r`;
- boundary states `rho_Br`;
- compatible interior-boundary cut states `rho_IrBr`;
- future inward flow recorded as `Sigma_r -> Sigma_{r-1}` via weighted
  compositor over all branches, not argmax;
- past outward flow recorded as `Sigma_r -> Sigma_{r+1}` preserved record.

Measured vector:
`Delta_H_Omega`, `Delta_S_B`, `K_binding`, `log_Z_path`, `order_gap`, and
`I_c`.

The projection is discovered by comparing component effect sizes between the
open and binding regimes. It is not a fixed Axis0 scalar formula.
