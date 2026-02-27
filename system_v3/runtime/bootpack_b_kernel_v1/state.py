import hashlib
import json
from dataclasses import dataclass, field


L0_LEXEME_SET = {
    "finite",
    "dimensional",
    "hilbert",
    "space",
    "density",
    "matrix",
    "operator",
    "probe",
    "channel",
    "cptp",
    "unitary",
    "lindblad",
    "hamiltonian",
    "commutator",
    "anticommutator",
    "trace",
    "partial",
    "tensor",
    "superoperator",
    "generator",
    # Extended QIT/geometry lexeme floor used by adaptive A1 planning.
    # This prevents repeated atomic bootstrap churn for obvious component words
    # and keeps ratchet pressure on compound-term + SIM semantics.
    "positive",
    "semidefinite",
    "one",
    "kraus",
    "measurement",
    "observable",
    "projector",
    "eigenvalue",
    "spectrum",
    "purity",
    "entropy",
    "coherence",
    "decoherence",
    "representation",
    "liouvillian",
    "left",
    "right",
    "action",
    "von",
    "neumann",
    "production",
    "rate",
    "noncommutative",
    "composition",
    "order",
    "pauli",
    "bloch",
    "sphere",
    "hopf",
    "fibration",
    "torus",
    "berry",
    "flux",
    "spinor",
    "double",
    "cover",
    "correlation",
    "polarity",
    "trajectory",
    "variance",
    "realization",
    "engine",
    "cycle",
    "qit",
    "master",
    "conjunction",
}


DERIVED_ONLY_TERMS = {
    "equal",
    "equality",
    "same",
    "identity",
    "coordinate",
    "cartesian",
    "origin",
    "center",
    "frame",
    "metric",
    "distance",
    "norm",
    "angle",
    "radius",
    "time",
    "before",
    "after",
    "past",
    "future",
    "cause",
    "because",
    "therefore",
    "implies",
    "results",
    "leads",
    "optimize",
    "maximize",
    "minimize",
    "utility",
    "map",
    "maps",
    "mapping",
    "mapped",
    "function",
    "functions",
    "domain",
    "codomain",
    "set",
    "relation",
    "real",
    "integer",
    "natural",
    "number",
    "probability",
    "random",
    "digit_sign",
    "equals_sign",
}


CANON_TERM_STATES = {"TERM_PERMITTED", "LABEL_PERMITTED", "CANONICAL_ALLOWED"}

# Root constraints are seeded into the initial survivor ledger. This is a genesis
# condition (constraints-before-axioms): the system is not meant to run without them.
_ROOT_CONSTRAINT_ITEMS: dict[str, dict] = {
    "F01_FINITUDE": {
        "class": "AXIOM_HYP",
        "status": "ACTIVE",
        "item_text": "\n".join(
            [
                "AXIOM_HYP F01_FINITUDE",
                "AXIOM_KIND F01_FINITUDE CORR AXIOM",
            ]
        ),
        "metadata": {"kill_if_tokens": [], "kill_bind": ""},
    },
    "N01_NONCOMMUTATION": {
        "class": "AXIOM_HYP",
        "status": "ACTIVE",
        "item_text": "\n".join(
            [
                "AXIOM_HYP N01_NONCOMMUTATION",
                "AXIOM_KIND N01_NONCOMMUTATION CORR AXIOM",
            ]
        ),
        "metadata": {"kill_if_tokens": [], "kill_bind": ""},
    },
}


@dataclass
class KernelState:
    survivor_ledger: dict[str, dict] = field(default_factory=dict)
    survivor_order: list[str] = field(default_factory=list)
    park_set: dict[str, dict] = field(default_factory=dict)
    graveyard: dict[str, dict] = field(default_factory=dict)
    reject_log: list[dict] = field(default_factory=list)
    kill_log: list[dict] = field(default_factory=list)
    term_registry: dict[str, dict] = field(default_factory=dict)
    evidence_pending: dict[str, set[str]] = field(default_factory=dict)
    evidence_tokens: set[str] = field(default_factory=set)
    spec_meta: dict[str, dict] = field(default_factory=dict)
    probe_meta: dict[str, dict] = field(default_factory=dict)
    formula_glyph_requirements: dict[str, str] = field(
        default_factory=lambda: {
            "+": "plus_sign",
            "-": "minus_sign",
            "*": "asterisk_sign",
            "/": "slash_sign",
            "^": "caret_sign",
            "~": "tilde_sign",
            "!": "exclamation_sign",
            "[": "left_square_bracket_sign",
            "]": "right_square_bracket_sign",
            "{": "left_curly_brace_sign",
            "}": "right_curly_brace_sign",
            "(": "left_parenthesis_sign",
            ")": "right_parenthesis_sign",
            "<": "less_than_sign",
            ">": "greater_than_sign",
            "|": "pipe_sign",
            "&": "ampersand_sign",
            ",": "comma_sign",
            ":": "colon_sign",
            ".": "dot_sign",
        }
    )
    l0_lexeme_set: set[str] = field(default_factory=lambda: set(L0_LEXEME_SET))
    derived_only_terms: set[str] = field(default_factory=lambda: set(DERIVED_ONLY_TERMS))
    active_megaboot_id: str = ""
    active_megaboot_sha256: str = ""
    active_ruleset_sha256: str = ""
    accepted_batch_count: int = 0
    unchanged_ledger_streak: int = 0
    sim_registry: dict[str, dict] = field(default_factory=dict)
    sim_results: dict[str, list[dict]] = field(default_factory=dict)
    sim_promotion_status: dict[str, str] = field(default_factory=dict)
    interaction_counts: dict[str, int] = field(default_factory=dict)
    canonical_ledger: list[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Seed only for fresh states. Resume loads must preserve exact on-disk state.
        if self.survivor_ledger:
            return
        for item_id in sorted(_ROOT_CONSTRAINT_ITEMS.keys()):
            self.survivor_ledger[item_id] = dict(_ROOT_CONSTRAINT_ITEMS[item_id])
            self.survivor_order.append(item_id)

    def _sorted_term_registry(self) -> dict:
        out = {}
        for key in sorted(self.term_registry.keys()):
            entry = dict(self.term_registry[key])
            out[key] = entry
        return out

    def _sorted_canonical_ledger(self) -> list[dict]:
        rows = [dict(row) for row in self.canonical_ledger if isinstance(row, dict)]
        rows.sort(
            key=lambda row: (
                int(row.get("sequence", 0)),
                int(row.get("step", 0)),
                str(row.get("state_transition_digest", "")),
            )
        )
        return rows

    def to_dict(self) -> dict:
        survivor_ledger = {key: self.survivor_ledger[key] for key in sorted(self.survivor_ledger.keys())}
        park_set = {key: self.park_set[key] for key in sorted(self.park_set.keys())}
        graveyard = {key: self.graveyard[key] for key in sorted(self.graveyard.keys())}
        evidence_pending = {key: sorted(self.evidence_pending[key]) for key in sorted(self.evidence_pending.keys())}
        spec_meta = {key: self.spec_meta[key] for key in sorted(self.spec_meta.keys())}
        probe_meta = {key: self.probe_meta[key] for key in sorted(self.probe_meta.keys())}
        sim_registry = {key: self.sim_registry[key] for key in sorted(self.sim_registry.keys())}
        sim_results = {key: self.sim_results[key] for key in sorted(self.sim_results.keys())}
        sim_promotion_status = {key: self.sim_promotion_status[key] for key in sorted(self.sim_promotion_status.keys())}
        interaction_counts = {key: int(self.interaction_counts[key]) for key in sorted(self.interaction_counts.keys())}
        canonical_ledger = self._sorted_canonical_ledger()
        return {
            "active_megaboot_id": self.active_megaboot_id,
            "active_megaboot_sha256": self.active_megaboot_sha256,
            "active_ruleset_sha256": self.active_ruleset_sha256,
            "accepted_batch_count": self.accepted_batch_count,
            "unchanged_ledger_streak": self.unchanged_ledger_streak,
            "survivor_ledger": survivor_ledger,
            "survivor_order": list(self.survivor_order),
            "park_set": park_set,
            "graveyard": graveyard,
            "reject_log": list(self.reject_log),
            "kill_log": list(self.kill_log),
            "term_registry": self._sorted_term_registry(),
            "evidence_pending": evidence_pending,
            "evidence_tokens": sorted(self.evidence_tokens),
            "spec_meta": spec_meta,
            "probe_meta": probe_meta,
            "sim_registry": sim_registry,
            "sim_results": sim_results,
            "sim_promotion_status": sim_promotion_status,
            "interaction_counts": interaction_counts,
            "canonical_ledger": canonical_ledger,
            "formula_glyph_requirements": {k: self.formula_glyph_requirements[k] for k in sorted(self.formula_glyph_requirements.keys())},
            "l0_lexeme_set": sorted(self.l0_lexeme_set),
            "derived_only_terms": sorted(self.derived_only_terms),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"

    @classmethod
    def from_dict(cls, payload: dict) -> "KernelState":
        state = cls()
        if not isinstance(payload, dict):
            return state

        state.active_megaboot_id = str(payload.get("active_megaboot_id", ""))
        state.active_megaboot_sha256 = str(payload.get("active_megaboot_sha256", ""))
        state.active_ruleset_sha256 = str(payload.get("active_ruleset_sha256", ""))
        state.accepted_batch_count = int(payload.get("accepted_batch_count", 0))
        state.unchanged_ledger_streak = int(payload.get("unchanged_ledger_streak", 0))

        state.survivor_ledger = {str(k): dict(v) for k, v in (payload.get("survivor_ledger", {}) or {}).items()}
        state.survivor_order = [str(x) for x in (payload.get("survivor_order", []) or [])]
        state.park_set = {str(k): dict(v) for k, v in (payload.get("park_set", {}) or {}).items()}
        state.graveyard = {str(k): dict(v) for k, v in (payload.get("graveyard", {}) or {}).items()}
        state.reject_log = [dict(x) for x in (payload.get("reject_log", []) or []) if isinstance(x, dict)]
        state.kill_log = [dict(x) for x in (payload.get("kill_log", []) or []) if isinstance(x, dict)]
        state.term_registry = {str(k): dict(v) for k, v in (payload.get("term_registry", {}) or {}).items()}
        state.evidence_pending = {
            str(k): {str(x) for x in (v or [])}
            for k, v in (payload.get("evidence_pending", {}) or {}).items()
        }
        state.evidence_tokens = {str(x) for x in (payload.get("evidence_tokens", []) or [])}
        state.spec_meta = {str(k): dict(v) for k, v in (payload.get("spec_meta", {}) or {}).items()}
        state.probe_meta = {str(k): dict(v) for k, v in (payload.get("probe_meta", {}) or {}).items()}
        state.sim_registry = {str(k): dict(v) for k, v in (payload.get("sim_registry", {}) or {}).items()}
        state.sim_results = {
            str(k): [dict(row) for row in (v or []) if isinstance(row, dict)]
            for k, v in (payload.get("sim_results", {}) or {}).items()
        }
        state.sim_promotion_status = {
            str(k): str(v) for k, v in (payload.get("sim_promotion_status", {}) or {}).items()
        }
        state.interaction_counts = {
            str(k): int(v) for k, v in (payload.get("interaction_counts", {}) or {}).items()
        }
        state.canonical_ledger = [
            dict(row) for row in (payload.get("canonical_ledger", []) or []) if isinstance(row, dict)
        ]
        state.formula_glyph_requirements = {
            str(k): str(v) for k, v in (payload.get("formula_glyph_requirements", {}) or {}).items()
        } or dict(state.formula_glyph_requirements)
        state.l0_lexeme_set = {str(x) for x in (payload.get("l0_lexeme_set", []) or [])} or set(L0_LEXEME_SET)
        state.derived_only_terms = {str(x) for x in (payload.get("derived_only_terms", []) or [])} or set(DERIVED_ONLY_TERMS)

        return state

    def hash(self) -> str:
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()
