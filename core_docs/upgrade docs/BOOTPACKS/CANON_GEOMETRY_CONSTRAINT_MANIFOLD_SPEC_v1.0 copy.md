# CANON_GEOMETRY_CONSTRAINT_MANIFOLD_SPEC v1.0

DATE_UTC: 2026-02-02T00:00:00Z
AUTHORITY: CANON

LOCKS (HARD)
- Geometry is a CONSTRAINT MANIFOLD emerging from constraints.
- Geometry exists before Axes 0–6.
- Axes 0–6 are FUNCTIONS / SLICES on the constraint manifold; they are not primitives.
- Axis-3 is ONLY the engine-family split (Type-1 vs Type-2).
- Engines are constrained by the manifold; engines are not primitives.

## 1) Core objects

- Constraint set **C**: admissibility statements used to define allowed configurations.
- Constraint manifold **M(C)**: the space of admissible configurations induced by **C**.
- Geometry: the coordinate-free structure on **M(C)** induced by **C** (no metric assumed as primitive).

## 2) Axes as slices

For each i in {0,1,2,3,4,5,6}:

- Axis-i is a function **Aᵢ : M(C) → Vᵢ** into a small codomain **Vᵢ**.
- Axis labels are bookkeeping over **M(C)**; they do not define **M(C)**.

## 3) Axis-3 definition

- **A₃ : M(C) → {Type-1, Type-2}**
- Meaning: selects which engine-family template is admissible at that point on **M(C)**.
- No additional semantics are attached to Type-1/Type-2 in CANON.

## 4) Engine families

- Engine family = an equivalence class of engine templates induced by constraints on **M(C)**.
- Engines are derived objects constrained by **M(C)**.

## 5) Compliance checklist (CANON)

- No doc may define an axis as a primitive substrate.
- No doc may place any axis before the constraint manifold.
- No doc may bind Axis-3 to chirality/handedness/spinor/Berry/flux language in CANON.
