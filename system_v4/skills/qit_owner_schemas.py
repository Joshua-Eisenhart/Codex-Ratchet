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
    DEDUCTIVE = "type1_deductive"
    INDUCTIVE = "type2_inductive"


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


class MacroStage(BaseModel):
    """One of 8 terrains within an engine type.
    
    Terrains are named by loop + mode + boundary:
      Se_f = fiber, expand, open
      Si_f = fiber, compress, closed
      etc.
    """
    terrain: str = Field(..., pattern=r"^[SNe][ei]_[fb]$",
                         description="Terrain code e.g. 'Se_f'")
    engine_type: EngineTypeEnum
    stage_index: int = Field(..., ge=0, le=7)
    loop: LoopEnum
    mode: ModeEnum
    boundary: BoundaryEnum

    _TERRAIN_SPEC: ClassVar[dict[str, tuple[LoopEnum, ModeEnum, BoundaryEnum, int]]] = {
        "Se_f": (LoopEnum.FIBER, ModeEnum.EXPAND, BoundaryEnum.OPEN, 0),
        "Si_f": (LoopEnum.FIBER, ModeEnum.COMPRESS, BoundaryEnum.CLOSED, 1),
        "Ne_f": (LoopEnum.FIBER, ModeEnum.EXPAND, BoundaryEnum.CLOSED, 2),
        "Ni_f": (LoopEnum.FIBER, ModeEnum.COMPRESS, BoundaryEnum.OPEN, 3),
        "Se_b": (LoopEnum.BASE, ModeEnum.EXPAND, BoundaryEnum.OPEN, 4),
        "Si_b": (LoopEnum.BASE, ModeEnum.COMPRESS, BoundaryEnum.CLOSED, 5),
        "Ne_b": (LoopEnum.BASE, ModeEnum.EXPAND, BoundaryEnum.CLOSED, 6),
        "Ni_b": (LoopEnum.BASE, ModeEnum.COMPRESS, BoundaryEnum.OPEN, 7),
    }

    @model_validator(mode="after")
    def validate_terrain_contract(self) -> "MacroStage":
        expected = self._TERRAIN_SPEC[self.terrain]
        if (self.loop, self.mode, self.boundary, self.stage_index) != expected:
            raise ValueError(
                "MacroStage fields must match the canonical terrain contract "
                f"for {self.terrain}: loop={expected[0].value}, mode={expected[1].value}, "
                f"boundary={expected[2].value}, stage_index={expected[3]}"
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
    engine_type: EngineTypeEnum
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
    EngineType(engine_type=EngineTypeEnum.DEDUCTIVE,
               description="Fe/Ti dominant on base, Te/Fi on fiber"),
    EngineType(engine_type=EngineTypeEnum.INDUCTIVE,
               description="Te/Fi dominant on base, Fe/Ti on fiber"),
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

    # Validate one macro-stage
    stage = MacroStage(terrain="Se_f", engine_type=EngineTypeEnum.DEDUCTIVE,
                       stage_index=0, loop=LoopEnum.FIBER,
                       mode=ModeEnum.EXPAND, boundary=BoundaryEnum.OPEN)
    print(f"\n  Sample stage: {stage.terrain} (idx={stage.stage_index})")

    # Validate one clifford payload
    payload = CliffordEdgePayload(
        grade=3, coefficients=[0, 0, 0, 0, 0, 0, 0, 1.0],
        relation="CHIRALITY_COUPLING"
    )
    print(f"  Sample clifford payload: grade={payload.grade}, relation={payload.relation}")

    # Validate one TopoNetX projection
    proj = TopoNetXCellProjection(
        shape=[105, 297, 0],
        stage_cycles=["type1_deductive_8stage_loop", "type2_inductive_8stage_loop"],
        torus_2cells=[],
        stage_diamonds=[]
    )
    print(f"  Sample TopoNetX projection: shape={proj.shape}")

    print("\n  All schemas valid. ✓")
