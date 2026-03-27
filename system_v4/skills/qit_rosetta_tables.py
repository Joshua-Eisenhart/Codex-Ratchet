from enum import Enum
from pydantic import BaseModel
from typing import Dict, List, Optional

class QITAxis(Enum):
    AXIS_0_GRADIENT = 0        # Entropic gradient / correlational structure
    AXIS_1_REGIME = 1          # Adiabatic vs Isothermal (Information preserved vs exchanged)
    AXIS_2_OPENNESS = 2        # Closed vs Open (Compression vs Expansion of state space)
    AXIS_3_CHIRALITY = 3       # Type 1 (Left) vs Type 2 (Right) topology
    AXIS_4_FLOW = 4            # Induction (release first) vs Deduction (constraint first)
    AXIS_5_ALGEBRA = 5         # Generator Algebra Class (FGA: Lindblad vs FSA: Hamiltonian)
    AXIS_6_ACTION = 6          # Action Orientation (Left pre-composition vs Right post-composition)

class QITOperatorPolarity(Enum):
    ABSORPTIVE_MINUS = "-"     # Topology -> Kernel
    EMISSIVE_PLUS = "+"        # Kernel -> Topology

class EngineTopologyType(Enum):
    TYPE_1_LEFT = "Left-Handed"
    TYPE_2_RIGHT = "Right-Handed"

class QITOperator(BaseModel):
    name: str                  # Core QIT name
    jungian_tag: str           # e.g., "Ti", "Te", "Fi", "Fe"
    polarity: QITOperatorPolarity
    kernel_identity: str
    intuition: str

OPERATORS: Dict[str, QITOperator] = {
    "Ti": QITOperator(
        name="Quantization Projector",
        jungian_tag="Ti",
        polarity=QITOperatorPolarity.ABSORPTIVE_MINUS,
        kernel_identity="State reduction / soft constraint",
        intuition="Carve / Constrain"
    ),
    "Te": QITOperator(
        name="Gradient Push",
        jungian_tag="Te",
        polarity=QITOperatorPolarity.EMISSIVE_PLUS,
        kernel_identity="Gradient descent/ascent",
        intuition="Optimize / Push"
    ),
    "Fe": QITOperator(
        name="Laplacian Diffuse",
        jungian_tag="Fe",
        polarity=QITOperatorPolarity.EMISSIVE_PLUS,
        kernel_identity="Entrainment / Synchronization drive",
        intuition="Couple / Broadcast"
    ),
    "Fi": QITOperator(
        name="Fourier Filter",
        jungian_tag="Fi",
        polarity=QITOperatorPolarity.ABSORPTIVE_MINUS,
        kernel_identity="Spectral absorption / matched filtering",
        intuition="Filter / Absorb"
    )
}

class EngineStage(BaseModel):
    stage_id: str              # e.g. "Se", "Si", "Ne", "Ni" (Terrains)
    topology_type: EngineTopologyType
    flow_type: str             # "Inductive" or "Deductive"
    primary_operator: str      # e.g. "Se" or "Ni" 
    secondary_operator: str
    description: str
    science_method_role: str   # How this maps to the science method

def get_science_method_sequence(is_inductive: bool) -> List[str]:
    '''
    Returns the sequence of terrain stages for the Science Method loops.
    Inductive: Se -> Si -> Ne -> Ni
    Deductive: Ni -> Ne -> Si -> Se
    '''
    if is_inductive:
        return ["Se", "Si", "Ne", "Ni"]
    else:
        return ["Ni", "Ne", "Si", "Se"]

class RosettaTranslator:
    @staticmethod
    def validate_operator(op_tag: str) -> bool:
        return op_tag in OPERATORS
        
    @staticmethod
    def get_qit_meaning(jungian_tag: str) -> str:
        # Extend this as needed for full terrain definitions
        if jungian_tag in OPERATORS:
            op = OPERATORS[jungian_tag]
            return f"{op.name} ({op.polarity.value}): {op.kernel_identity}"
        return "Unknown tag"
