import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

"""A0: deterministic compiler. Packages proposals into EXPORT_BLOCKs.

A0 does NOT decide what to propose. It takes a term ladder and state,
finds the next items to admit, pairs each with a SIM_SPEC, and packages
them into a valid EXPORT_BLOCK for B.

The term ladder is the current static proposal source. When A1 exists
as a real agent, it will replace the ladder with live proposals.
"""

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from containers import build_export_block
from validator import load_bootpack_rules


@dataclass(frozen=True)
class PlannedItem:
    item_id: str
    lines: list


TERM_LADDER = [
    "density", "matrix", "operator", "trace", "hilbert", "space",
    "finite", "commutator", "channel", "unitary", "tensor", "generator",
    "cptp", "lindblad", "hamiltonian", "anticommutator", "superoperator",
    "dimensional", "partial",
]


class A0Compiler:
    def __init__(self):
        self.rules = load_bootpack_rules()

    def _probe(self, pid):
        return [
            f"PROBE_HYP {pid}",
            f"PROBE_KIND {pid} CORR PROBE_HYP",
            f"ASSERT {pid} CORR EXISTS PROBE_TOKEN PT_{pid}",
        ]

    def _axiom_sim(self, axiom_id, ev_token):
        sim_id = f"SIM_{axiom_id}"
        return sim_id, [
            f"SPEC_HYP {sim_id}",
            f"SPEC_KIND {sim_id} CORR SIM_SPEC",
            f"REQUIRES {sim_id} CORR {axiom_id}",
            f'DEF_FIELD {sim_id} CORR REQUIRES_EVIDENCE "{ev_token}"',
            f"ASSERT {sim_id} CORR EXISTS EVIDENCE_TOKEN {ev_token}",
        ]

    def _math_def(self):
        return [
            "SPEC_HYP S_L0_MATH",
            "SPEC_KIND S_L0_MATH CORR MATH_DEF",
            "REQUIRES S_L0_MATH CORR F01_FINITUDE",
            "REQUIRES S_L0_MATH CORR N01_NONCOMMUTATION",
            "DEF_FIELD S_L0_MATH CORR OBJECTS finite hilbert space",
            "DEF_FIELD S_L0_MATH CORR OPERATIONS operator commutator",
            "DEF_FIELD S_L0_MATH CORR INVARIANTS trace",
            "DEF_FIELD S_L0_MATH CORR DOMAIN hilbert space",
            "DEF_FIELD S_L0_MATH CORR CODOMAIN hilbert space",
            "DEF_FIELD S_L0_MATH CORR SIM_CODE_HASH_SHA256 " + "0" * 64,
            "ASSERT S_L0_MATH CORR EXISTS MATH_TOKEN MT_S_L0_MATH",
        ]

    def _term_def(self, term, spec_id, component_deps=None):
        lines = [
            f"SPEC_HYP {spec_id}",
            f"SPEC_KIND {spec_id} CORR TERM_DEF",
            f"REQUIRES {spec_id} CORR S_L0_MATH",
        ]
        for dep in (component_deps or []):
            lines.append(f"REQUIRES {spec_id} CORR {dep}")
        lines += [
            f'DEF_FIELD {spec_id} CORR TERM "{term}"',
            f"DEF_FIELD {spec_id} CORR BINDS S_L0_MATH",
            f"ASSERT {spec_id} CORR EXISTS TERM_TOKEN TT_{spec_id}",
        ]
        return lines

    def _sim_spec(self, sim_id, requires_id, ev_token):
        return [
            f"SPEC_HYP {sim_id}",
            f"SPEC_KIND {sim_id} CORR SIM_SPEC",
            f"REQUIRES {sim_id} CORR {requires_id}",
            f'DEF_FIELD {sim_id} CORR REQUIRES_EVIDENCE "{ev_token}"',
            f"ASSERT {sim_id} CORR EXISTS EVIDENCE_TOKEN {ev_token}",
        ]

    def _drain_stale_parks(self, state, threshold=3):
        counts = Counter(p["id"] for p in state.parked)
        stale = {pid for pid, n in counts.items() if n >= threshold}
        if not stale:
            return
        kept = []
        for p in state.parked:
            if p["id"] in stale:
                state.graveyard.append({
                    "id": p["id"],
                    "reason": f"STALE_PARK_{p.get('reason', 'UNKNOWN')}",
                })
            else:
                kept.append(p)
        state.parked = kept

    def plan(self, state, max_items=20):
        self._drain_stale_parks(state)
        items = []
        admitted = set(state.terms.keys()) if isinstance(state.terms, dict) else set()

        # 1. Axiom SIM_SPECs
        for ax_id, ev in [("F01_FINITUDE", "EV_FINITUDE"),
                           ("N01_NONCOMMUTATION", "EV_NONCOMMUTATION")]:
            sid = f"SIM_{ax_id}"
            if sid not in state.specs and ax_id in state.axioms:
                _, lines = self._axiom_sim(ax_id, ev)
                items.append(PlannedItem(sid, lines))

        # 2. Base math def
        if "S_L0_MATH" not in state.specs:
            items.append(PlannedItem("S_L0_MATH", self._math_def()))

        # 3. Terms from ladder + paired SIM_SPECs
        for term in TERM_LADDER:
            if len(items) >= max_items:
                break
            if term in admitted:
                continue
            spec_id = f"S_TERM_{term.upper()}"
            if spec_id in state.specs:
                continue

            comp_deps = []
            if "_" in term:
                parts = term.split("_")
                if not all(p in admitted or p in self.rules.lexeme_set for p in parts):
                    continue
                comp_deps = [f"S_TERM_{p.upper()}" for p in parts
                             if f"S_TERM_{p.upper()}" in state.specs]

            items.append(PlannedItem(spec_id, self._term_def(term, spec_id, comp_deps)))

            sim_id = f"SIM_TERM_{term.upper()}"
            if sim_id not in state.specs:
                items.append(PlannedItem(sim_id, self._sim_spec(sim_id, spec_id, f"EV_{term.upper()}")))

        return items

    def compile(self, state, max_items=20):
        items = self.plan(state, max_items)
        content = []

        spec_count = len(items)
        probes_needed = max(1, (spec_count + 9) // 10)
        for i in range(probes_needed):
            pid = f"P{1000 + state.probe_count + 1 + i}"
            content.extend(self._probe(pid))

        for item in items:
            content.extend(item.lines)

        if not content:
            pid = f"P{1000 + state.probe_count + 1}"
            content.extend(self._probe(pid))

        return build_export_block(
            f"A0_{state.hash()[:8]}", "A0_BATCH", content, version="v1"
        )


def generate_export_block(state, max_specs=6, run_dir=None):
    return A0Compiler().compile(state, max_items=max_specs)
