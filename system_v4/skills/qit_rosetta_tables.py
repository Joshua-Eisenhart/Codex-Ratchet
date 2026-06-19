"""qit_rosetta_tables.py -- FENCED LEGACY.

WARNING (no-equals discipline): the `kernel_identity` field on each QITOperator and the AXIS enum
comments (e.g. "Type 1 (Left) vs Type 2 (Right)") are LEGACY de-facto EQUALS-SIGN strings -- they
assert "jungian_tag = kernel meaning" with NO probe family and NO erasure record. This system has
no equals sign and no universals. These strings are NOT admissible as correspondences and must NOT
be promoted. `seed_correspondences()` below re-expresses each row as a probe-relative ~_M
correspondence candidate with an EXPLICIT, still-unpinned probe family (claim_ceiling
"needs_probe_family") so the no-= lint can drive the migration. `get_qit_meaning` /
`get_kernel_translation` (the de-facto '=' accessors) are DEPRECATED in favour of the plural
perspective fan in rosetta_reattach.RosettaCarrier.perspectives().
"""

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
        # DEPRECATED: returns the legacy kernel_identity (a de-facto '='). Prefer
        # seed_correspondences() + rosetta_reattach.RosettaCarrier.perspectives() (plural ~_M).
        if jungian_tag in OPERATORS:
            op = OPERATORS[jungian_tag]
            return f"{op.name} ({op.polarity.value}): {op.kernel_identity}"
        return "Unknown tag"


# Per-tag probe families under which the jungian tag is *indistinguishable* from the kernel object.
# These are CANDIDATES still to be pinned by a sim; until then claim_ceiling = needs_probe_family.
_OPERATOR_PROBE_M: Dict[str, str] = {
    "Ti": "M={z-basis dephasing channel D_z; purity + z-expectation readout}",
    "Te": "M={x-basis dephasing channel D_x; purity + x-expectation readout}",
    "Fi": "M={x-axis unitary rotation R_x; orbit-on-Bloch readout}",
    "Fe": "M={z-axis unitary rotation R_z; orbit-on-Bloch readout}",
}


def seed_correspondences() -> List[dict]:
    """Re-express each legacy `kernel_identity` row as a probe-relative ~_M correspondence CANDIDATE
    (never an identity). Each carries a named probe family, what it preserves, what the jargon
    erases, and a needs_probe_family ceiling. Output is lint-clean under rosetta_reattach.validate_no_equals."""
    out = []
    for tag, op in OPERATORS.items():
        out.append({
            "object_id": f"L0::{op.name.replace(' ', '_')}",
            "perspective_label": op.jungian_tag,
            "jargon_type": "jungian_function",
            "model": "jung_mbti_igt",
            "relation_symbol": "~_M",
            "probe_family_M": _OPERATOR_PROBE_M.get(tag, "M={UNPINNED}"),
            "preserves": f"the {op.name} channel action ({op.polarity.value})",
            "erases": f"the felt/jungian semantics behind '{op.kernel_identity}' and the type narrative",
            "hypothesis_id": "H0",
            "claim_ceiling": "needs_probe_family" if _OPERATOR_PROBE_M.get(tag) else "unpinned_probe",
        })
    return out


if __name__ == "__main__":
    import json
    print(json.dumps(seed_correspondences(), indent=2))
