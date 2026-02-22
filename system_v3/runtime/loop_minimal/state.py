import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import hashlib
import json
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class KernelState:
    probes: Dict[str, dict] = field(default_factory=dict)
    specs: Dict[str, dict] = field(default_factory=dict)
    evidence_pending: Dict[str, Set[str]] = field(default_factory=dict)
    survivor_order: List[str] = field(default_factory=list)
    graveyard: List[dict] = field(default_factory=list)
    parked: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "probes": {k: v for k, v in sorted(self.probes.items())},
            "specs": {k: v for k, v in sorted(self.specs.items())},
            "evidence_pending": {k: sorted(list(v)) for k, v in sorted(self.evidence_pending.items())},
            "survivor_order": list(self.survivor_order),
            "graveyard": list(self.graveyard),
            "parked": list(self.parked),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"

    @classmethod
    def from_json(cls, text: str) -> "KernelState":
        data = json.loads(text) if text else {}
        st = cls()
        st.probes = data.get("probes", {})
        st.specs = data.get("specs", {})
        st.evidence_pending = {k: set(v) for k, v in data.get("evidence_pending", {}).items()}
        st.survivor_order = data.get("survivor_order", [])
        st.graveyard = data.get("graveyard", [])
        st.parked = data.get("parked", [])
        return st

    def hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()
