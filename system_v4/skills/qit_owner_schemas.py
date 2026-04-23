"""
qit_owner_schemas.py
====================
Pydantic owner schemas for the QIT Engine graph layer.

These are the canonical, typed contracts for the physical structures
that live in the NetworkX owner layer. Sidecar projections (TopoNetX,
clifford, PyG) consume these schemas but do not own them.

Schemas:
  - EngineType       (Deductive / Inductive)
  - MacroStage       (one of 8 terrains per engine type)
  - SubcycleOperator (Ti, Fe, Te, Fi)
  - SubcycleStep     (one operator application at one stage)
  - TorusState       (inner, Clifford, outer)
  - WeylBranch       (left or right spinor state)
  - AxisState        (one of 7 proven axes)
  - NegativeWitness  (graveyard kill proving necessity)
  - RuntimeStateOverlay   (graph-adjacent mutable snapshot keyed to public ids)
  - HistoryRunPacket      (append-only step history keyed to public ids)
"""

from __future__ import annotations

from enum import Enum
from typing import ClassVar, Literal, Optional
from pydantic import BaseModel, Field, model_validator


# ── Enums ──

class EngineTypeEnum(str, Enum):
    TYPE1 = "type1"   # Left Weyl, H_L = +n·σ
    TYPE2 = "type2"   # Right Weyl, H_R = −n·σ


class OperatorEnum(str, Enum):
    Ti = "Ti"   # constrain
    Fe = "Fe"   # release
    Te = "Te"   # explore
    Fi = "Fi"   # filter


class LoopEnum(str, Enum):
    FIBER = "fiber"
    BASE = "base"


class ModeEnum(str, Enum):
    EXPAND = "expand"
    COMPRESS = "compress"


class BoundaryEnum(str, Enum):
    OPEN = "open"
    CLOSED = "closed"


class TorusEnum(str, Enum):
    INNER = "inner"
    CLIFFORD = "clifford"
    OUTER = "outer"


class WeylEnum(str, Enum):
    LEFT = "left"
    RIGHT = "right"


class NegTargetEnum(str, Enum):
    TORUS = "TORUS"
    AXIS = "AXIS"
    OPERATOR = "OPERATOR"
    CHIRALITY = "CHIRALITY"


# ── Owner Schemas ──

class EngineType(BaseModel):
    """Canonical identity for a QIT engine type."""
    engine_type: EngineTypeEnum
    description: str = ""

    class Config:
        frozen = True


class SpinorEnum(str, Enum):
    LEFT = "L"    # Type-1, H_L = +n·σ
    RIGHT = "R"   # Type-2, H_R = −n·σ


class TerrainFamilyEnum(str, Enum):
    Se = "Se"   # radial expansion, open boundary (Lindblad div>0)
    Ne = "Ne"   # tangential circulation, closed boundary (Hamiltonian div=0)
    Ni = "Ni"   # radial contraction, open boundary (Lindblad div<0)
    Si = "Si"   # stratified retention, closed boundary ([H,Pk]=0)


class TerrainNameEnum(str, Enum):
    # Type-1 names (topology × engine_type=type1)
    FUNNEL = "Funnel"   # Se, type1
    VORTEX = "Vortex"   # Ne, type1
    PIT = "Pit"         # Ni, type1
    HILL = "Hill"       # Si, type1
    # Type-2 names (topology × engine_type=type2)
    CANNON = "Cannon"   # Se, type2
    SPIRAL = "Spiral"   # Ne, type2
    SOURCE = "Source"   # Ni, type2
    CITADEL = "Citadel" # Si, type2


class MacroStage(BaseModel):
    """One macro-stage: a single (topology × loop × spinor) placement.

    16 total placements = 4 topologies × 2 loops × 2 engine_types.
    8 terrain names = 4 topologies × 2 engine_types (NOT × loop).
    8 generators = 4 per engine_type; same generator used on both loops.
    Loop selects the carrier curve (γ_f vs γ_b) only.

    Terrain name by (engine_type × topology):
      type1: Se→Funnel, Ne→Vortex, Ni→Pit,  Si→Hill
      type2: Se→Cannon, Ne→Spiral, Ni→Source, Si→Citadel

    Generator by (engine_type × topology):
      type1: Se→X_F^L, Ne→X_V^L, Ni→X_P^L, Si→X_H^L
      type2: Se→X_C^R, Ne→X_S^R, Ni→X_{So}^R, Si→X_{Ci}^R
    """
    terrain: str = Field(..., pattern=r"^[SN][ei]_[fb]$",
                         description="Terrain code e.g. 'Se_f'")
    engine_type: EngineTypeEnum
    stage_index: int = Field(..., ge=0, le=7)
    loop: LoopEnum
    mode: ModeEnum
    boundary: BoundaryEnum
    spinor_type: SpinorEnum = Field(
        ..., description="L=Type-1 H_L=+n·σ, R=Type-2 H_R=−n·σ"
    )
    terrain_family: TerrainFamilyEnum = Field(
        ..., description="One of the 4 base topologies (Se/Ne/Ni/Si)"
    )
    terrain_name: TerrainNameEnum = Field(
        ..., description="Name from (engine_type × topology), NOT from loop"
    )
    hamiltonian_sign: int = Field(
        ..., description="+1 for Type-1 (H_L=+n·σ), -1 for Type-2 (H_R=−n·σ)"
    )
    generator: str = Field(
        ..., description="Generator symbol e.g. 'X_F^L' per TERRAIN_MATH_LEDGER_v1.md"
    )

    # Terrain code → (family, loop, mode, boundary)  [engine-type-agnostic]
    # Stage index is engine-type-dependent; validated separately via _STAGE_INDEX_SPEC.
    _TERRAIN_SPEC: ClassVar[dict[str, tuple[TerrainFamilyEnum, LoopEnum, ModeEnum, BoundaryEnum]]] = {
        "Se_f": (TerrainFamilyEnum.Se, LoopEnum.FIBER, ModeEnum.EXPAND,   BoundaryEnum.OPEN),
        "Ne_f": (TerrainFamilyEnum.Ne, LoopEnum.FIBER, ModeEnum.EXPAND,   BoundaryEnum.CLOSED),
        "Ni_f": (TerrainFamilyEnum.Ni, LoopEnum.FIBER, ModeEnum.COMPRESS, BoundaryEnum.OPEN),
        "Si_f": (TerrainFamilyEnum.Si, LoopEnum.FIBER, ModeEnum.COMPRESS, BoundaryEnum.CLOSED),
        "Se_b": (TerrainFamilyEnum.Se, LoopEnum.BASE,  ModeEnum.EXPAND,   BoundaryEnum.OPEN),
        "Ne_b": (TerrainFamilyEnum.Ne, LoopEnum.BASE,  ModeEnum.EXPAND,   BoundaryEnum.CLOSED),
        "Ni_b": (TerrainFamilyEnum.Ni, LoopEnum.BASE,  ModeEnum.COMPRESS, BoundaryEnum.OPEN),
        "Si_b": (TerrainFamilyEnum.Si, LoopEnum.BASE,  ModeEnum.COMPRESS, BoundaryEnum.CLOSED),
    }

    # Stage index: (engine_type_value, terrain_code) → stage_index (0–7).
    # Order is engine-type-dependent (O_ind vs O_ded, see TERRAIN_MATH_LEDGER_v1.md §6).
    # Type-1 inner=IND (Se0,Si1,Ni2,Ne3), outer=DED (Se4,Ne5,Ni6,Si7)
    # Type-2 inner=DED (Se0,Ne1,Ni2,Si3), outer=IND (Se4,Si5,Ni6,Ne7)
    _STAGE_INDEX_SPEC: ClassVar[dict[tuple, int]] = {
        ("type1", "Se_f"): 0, ("type1", "Si_f"): 1, ("type1", "Ni_f"): 2, ("type1", "Ne_f"): 3,
        ("type1", "Se_b"): 4, ("type1", "Ne_b"): 5, ("type1", "Ni_b"): 6, ("type1", "Si_b"): 7,
        ("type2", "Se_f"): 0, ("type2", "Ne_f"): 1, ("type2", "Ni_f"): 2, ("type2", "Si_f"): 3,
        ("type2", "Se_b"): 4, ("type2", "Si_b"): 5, ("type2", "Ni_b"): 6, ("type2", "Ne_b"): 7,
    }

    # Terrain name: (engine_type_value, terrain_family_value) → TerrainNameEnum
    _TERRAIN_NAME_BY_ENGINE: ClassVar[dict[tuple, TerrainNameEnum]] = {
        ("type1", "Se"): TerrainNameEnum.FUNNEL,
        ("type1", "Ne"): TerrainNameEnum.VORTEX,
        ("type1", "Ni"): TerrainNameEnum.PIT,
        ("type1", "Si"): TerrainNameEnum.HILL,
        ("type2", "Se"): TerrainNameEnum.CANNON,
        ("type2", "Ne"): TerrainNameEnum.SPIRAL,
        ("type2", "Ni"): TerrainNameEnum.SOURCE,
        ("type2", "Si"): TerrainNameEnum.CITADEL,
    }

    # Generator: (engine_type_value, terrain_family_value) → generator symbol
    _GENERATOR_BY_ENGINE: ClassVar[dict[tuple, str]] = {
        ("type1", "Se"): "X_F^L",
        ("type1", "Ne"): "X_V^L",
        ("type1", "Ni"): "X_P^L",
        ("type1", "Si"): "X_H^L",
        ("type2", "Se"): "X_C^R",
        ("type2", "Ne"): "X_S^R",
        ("type2", "Ni"): "X_{So}^R",
        ("type2", "Si"): "X_{Ci}^R",
    }

    @model_validator(mode="after")
    def validate_terrain_contract(self) -> "MacroStage":
        spec = self._TERRAIN_SPEC[self.terrain]
        fam, lp, md, bd = spec
        expected_idx = self._STAGE_INDEX_SPEC[(self.engine_type.value, self.terrain)]
        if (self.loop, self.mode, self.boundary) != (lp, md, bd):
            raise ValueError(
                f"MacroStage fields must match terrain contract for {self.terrain}: "
                f"loop={lp.value}, mode={md.value}, boundary={bd.value}"
            )
        if self.stage_index != expected_idx:
            raise ValueError(
                f"stage_index must be {expected_idx} for "
                f"engine_type={self.engine_type.value}, terrain={self.terrain}"
            )
        if self.terrain_family != fam:
            raise ValueError(f"terrain_family must be {fam.value} for terrain {self.terrain}")
        key = (self.engine_type.value, self.terrain_family.value)
        expected_name = self._TERRAIN_NAME_BY_ENGINE[key]
        if self.terrain_name != expected_name:
            raise ValueError(
                f"terrain_name must be {expected_name.value} for "
                f"engine_type={self.engine_type.value}, topology={self.terrain_family.value}"
            )
        expected_gen = self._GENERATOR_BY_ENGINE[key]
        if self.generator != expected_gen:
            raise ValueError(
                f"generator must be '{expected_gen}' for "
                f"engine_type={self.engine_type.value}, topology={self.terrain_family.value}"
            )
        expected_sign = +1 if self.spinor_type == SpinorEnum.LEFT else -1
        if self.hamiltonian_sign != expected_sign:
            raise ValueError(
                f"hamiltonian_sign must be {expected_sign} for spinor {self.spinor_type.value}"
            )
        expected_engine = EngineTypeEnum.TYPE1 if self.spinor_type == SpinorEnum.LEFT else EngineTypeEnum.TYPE2
        if self.engine_type != expected_engine:
            raise ValueError(
                f"engine_type must be {expected_engine.value} for spinor {self.spinor_type.value}"
            )
        return self

    class Config:
        frozen = True


class SubcycleOperator(BaseModel):
    """One of the 4 fixed operators in the Ti→Fe→Te→Fi cycle."""
    operator: OperatorEnum
    action: str = Field(..., description="What this operator does: constrain/release/explore/filter")

    class Config:
        frozen = True


class SubcycleStep(BaseModel):
    """A single operator application at a specific macro-stage."""
    operator: OperatorEnum
    stage_terrain: str = Field(..., pattern=r"^[SN][ei]_[fb]$")
    engine_type: EngineTypeEnum  # type1 or type2
    position_in_subcycle: int = Field(..., ge=0, le=3,
                                      description="0=Ti, 1=Fe, 2=Te, 3=Fi")

    _POSITION_BY_OPERATOR: ClassVar[dict[OperatorEnum, int]] = {
        OperatorEnum.Ti: 0,
        OperatorEnum.Fe: 1,
        OperatorEnum.Te: 2,
        OperatorEnum.Fi: 3,
    }

    @model_validator(mode="after")
    def validate_subcycle_position(self) -> "SubcycleStep":
        expected = self._POSITION_BY_OPERATOR[self.operator]
        if self.position_in_subcycle != expected:
            raise ValueError(
                "SubcycleStep position_in_subcycle must match the fixed "
                f"Ti->Fe->Te->Fi order; {self.operator.value} expects {expected}"
            )
        return self

    class Config:
        frozen = True


class TorusState(BaseModel):
    """One of the 3 nested Hopf tori."""
    torus: TorusEnum
    nesting_rank: int = Field(..., ge=0, le=2,
                               description="0=inner, 1=Clifford, 2=outer")
    description: str = ""

    class Config:
        frozen = True


class WeylBranch(BaseModel):
    """A Weyl spinor branch (left or right)."""
    branch: WeylEnum
    description: str = Field("", description="Which density matrix this branch carries")

    class Config:
        frozen = True


class AxisState(BaseModel):
    """One of the 7 proven load-bearing axes (0–6)."""
    axis_id: str = Field(..., pattern=r"^axis_[0-6]$")
    description: str = ""
    proven: bool = True
    negative_witness_sim: Optional[str] = Field(
        None, description="SIM file that kills the engine when this axis is removed"
    )

    class Config:
        frozen = True


class NegativeWitness(BaseModel):
    """A graveyard kill proving that a specific structure is necessary."""
    neg_id: str
    description: str
    target_structure: NegTargetEnum
    sim_file: Optional[str] = None
    specific_targets: list[str] = Field(
        default_factory=list,
        description="Specific owner members named by this witness when the proof is narrower than a whole class.",
    )
    owner_edge_emission: Literal[
        "specific_targets",
        "per_member_sweep",
        "suppressed_pending_owner_concept",
    ] = "suppressed_pending_owner_concept"
    proves_label: Optional[str] = None

    @model_validator(mode="after")
    def _validate_edge_emission(self) -> "NegativeWitness":
        if self.owner_edge_emission == "specific_targets" and not self.specific_targets:
            raise ValueError("specific_targets emission requires at least one specific target")
        if self.owner_edge_emission == "per_member_sweep" and not self.specific_targets:
            raise ValueError("per_member_sweep requires explicit member targets")
        return self

    class Config:
        frozen = True


# ── Bounded Sidecar Payloads ──
# These are read-only projection schemas. They do NOT own the data.
# The owner graph (NetworkX) is the source of truth.

class CliffordEdgePayload(BaseModel):
    """Bounded read-only Cl(3,0) multivector payload for a graph edge.
    
    8 coefficients: [scalar, e1, e2, e3, e12, e13, e23, e123]
    
    Notable mappings:
      - SUBCYCLE_ORDER → grade-1 along e1 (causal direction)
      - TORUS_NESTING → grade-2 in e13 plane (oriented nesting)
      - CHIRALITY_COUPLING → grade-3 pseudoscalar e123 (parity)
      - NEGATIVE_PROVES → grade-2 with negative e12 (negation semantics)
    """
    algebra: Literal["Cl(3,0)"] = "Cl(3,0)"
    grade: int = Field(..., ge=0, le=3)
    coefficients: list[float] = Field(..., min_length=8, max_length=8)
    relation: str = Field(..., description="The relation type this payload annotates")
    basis_labels: list[str] = Field(
        default=["scalar", "e1", "e2", "e3", "e12", "e13", "e23", "e123"]
    )

    class Config:
        frozen = True


class TopoNetXCellProjection(BaseModel):
    """Bounded read-only projection of a TopoNetX cell complex structure.
    
    Reports the shape (0-cells, 1-cells, 2-cells) and identified cycles
    from the owner graph data. Does NOT replace the owner graph.
    """
    shape: list[int] = Field(..., min_length=1, max_length=4,
                              description="[n_0cells, n_1cells, n_2cells]")
    stage_cycles: list[str] = Field(
        default_factory=list,
        description="Names of identified 1-cycles (closed stage loops)"
    )
    torus_2cells: list[str] = Field(
        default_factory=list,
        description="Names of identified 2-cells (torus surface patches)"
    )
    stage_diamonds: list[str] = Field(
        default_factory=list,
        description="Names of identified 2-cells (stage + 4 operators + next stage)"
    )

    class Config:
        frozen = True


class RuntimeStateOverlay(BaseModel):
    """Minimal mutable runtime snapshot projected onto stable QIT public ids.

    This is graph-adjacent scaffolding, not owner-graph mutation. It provides
    the smallest honest bridge from EngineState into later state-graph work.
    The current overlay is stage-granular, not live-subcycle-granular.
    """
    engine_public_id: str
    active_stage_public_id: str
    last_completed_step_public_id: Optional[str] = None
    stage_index_mod8: int = Field(..., ge=0, le=7)
    engine_type: EngineTypeEnum
    eta: float
    theta1: float
    theta2: float
    ga0_level: float = Field(..., ge=0.0, le=1.0)
    history_length: int = Field(..., ge=0)

    class Config:
        frozen = True


class HistoryStepRecord(BaseModel):
    """One append-only subcycle record keyed to stable QIT public ids."""
    sequence_index: int = Field(..., ge=0)
    step_public_id: str
    stage_public_id: str
    operator: OperatorEnum
    engine_type: EngineTypeEnum
    dphi_L: float
    dphi_R: float
    strength: float
    ga0_before: float
    ga0_after: float

    class Config:
        frozen = True


class HistoryRunPacket(BaseModel):
    """Append-only packet for one engine run or probe trace.

    This stays outside the owner graph until explicit history-graph promotion.
    """
    run_id: str
    engine_public_id: str
    engine_type: EngineTypeEnum
    total_steps: int = Field(..., ge=0)
    macro_stages_completed: int = Field(..., ge=0)
    step_records: list[HistoryStepRecord] = Field(default_factory=list)

    class Config:
        frozen = True


# ── Convenience builders ──

CANONICAL_OPERATORS = [
    SubcycleOperator(operator=OperatorEnum.Ti, action="constrain"),
    SubcycleOperator(operator=OperatorEnum.Fe, action="release"),
    SubcycleOperator(operator=OperatorEnum.Te, action="explore"),
    SubcycleOperator(operator=OperatorEnum.Fi, action="filter"),
]

CANONICAL_TORI = [
    TorusState(torus=TorusEnum.INNER, nesting_rank=0,
               description="Innermost torus — highest curvature"),
    TorusState(torus=TorusEnum.CLIFFORD, nesting_rank=1,
               description="Clifford torus — equal radii, flat"),
    TorusState(torus=TorusEnum.OUTER, nesting_rank=2,
               description="Outermost torus — lowest curvature"),
]

CANONICAL_ENGINE_TYPES = [
    EngineType(engine_type=EngineTypeEnum.TYPE1,
               description="Type-1 engine: Left Weyl spinor, H_L = +n·σ, Bloch law ṙ_L = +2n×r_L"),
    EngineType(engine_type=EngineTypeEnum.TYPE2,
               description="Type-2 engine: Right Weyl spinor, H_R = −n·σ, Bloch law ṙ_R = −2n×r_R"),
]


if __name__ == "__main__":
    # Validate all canonical instances
    print("=== QIT Owner Schema Validation ===")
    print(f"  Operators: {len(CANONICAL_OPERATORS)}")
    for op in CANONICAL_OPERATORS:
        print(f"    {op.operator.value}: {op.action}")
    print(f"  Tori:      {len(CANONICAL_TORI)}")
    for t in CANONICAL_TORI:
        print(f"    {t.torus.value} (rank {t.nesting_rank}): {t.description}")
    print(f"  Engines:   {len(CANONICAL_ENGINE_TYPES)}")
    for e in CANONICAL_ENGINE_TYPES:
        print(f"    {e.engine_type.value}: {e.description}")

    # Validate one macro-stage (Type-1, Se, fiber → Funnel, X_F^L)
    stage = MacroStage(
        terrain="Se_f", engine_type=EngineTypeEnum.TYPE1,
        stage_index=0, loop=LoopEnum.FIBER,
        mode=ModeEnum.EXPAND, boundary=BoundaryEnum.OPEN,
        spinor_type=SpinorEnum.LEFT, terrain_family=TerrainFamilyEnum.Se,
        terrain_name=TerrainNameEnum.FUNNEL, hamiltonian_sign=+1,
        generator="X_F^L",
    )
    print(f"\n  Sample stage: {stage.terrain} ({stage.terrain_name.value}, gen={stage.generator}) idx={stage.stage_index}")
    # Validate Type-2 base stage → Cannon, X_C^R (same generator as fiber — loop only sets carrier curve)
    stage2 = MacroStage(
        terrain="Se_b", engine_type=EngineTypeEnum.TYPE2,
        stage_index=4, loop=LoopEnum.BASE,
        mode=ModeEnum.EXPAND, boundary=BoundaryEnum.OPEN,
        spinor_type=SpinorEnum.RIGHT, terrain_family=TerrainFamilyEnum.Se,
        terrain_name=TerrainNameEnum.CANNON, hamiltonian_sign=-1,
        generator="X_C^R",
    )
    print(f"  Sample stage: {stage2.terrain} ({stage2.terrain_name.value}, gen={stage2.generator}) idx={stage2.stage_index}")

    # Validate one clifford payload
    payload = CliffordEdgePayload(
        grade=3, coefficients=[0, 0, 0, 0, 0, 0, 0, 1.0],
        relation="CHIRALITY_COUPLING"
    )
    print(f"  Sample clifford payload: grade={payload.grade}, relation={payload.relation}")

    # Validate one TopoNetX projection
    proj = TopoNetXCellProjection(
        shape=[105, 272, 0],
        stage_cycles=["type1_8stage_loop", "type2_8stage_loop"],
        torus_2cells=[],
        stage_diamonds=[]
    )
    print(f"  Sample TopoNetX projection: shape={proj.shape}")

    print("\n  All schemas valid. ✓")
