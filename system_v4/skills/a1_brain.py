"""
a1_brain.py — A1 Persistent Brain

The A1 brain is the Rosetta layer between high-entropy A2 concepts and
canon-safe B grammar targets. It performs cold-core extraction: stripping
jargon/metaphor/narrative to produce explicit math objects, relations, and
ratchet-safe candidates.

Per Spec 05 (A1 Strategy and Repair) and Spec 18 (A1 Wiggle Execution Contract):
- Output is A1_STRATEGY_v1 packets only
- Each candidate must be compile-ready: item_class, id, kind, requires, def_fields, asserts
- Alternatives must be designed to fail (try_to_fail intent)
- Negative sim plans must have explicit expected_failure_modes
- No confidence/probability fields (nominalized-reality ban)
- No free prose in compile lanes (BARE values must be token-safe)

The L0 lexeme set is the bootstrap vocabulary from the MEGABOOT (Thread B boot).
Everything else must earn admission through the term pipeline.
"""

import hashlib
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

# Need rosetta mapper
from system_v4.skills.intent_runtime_policy import (
    merge_execution_bias,
    normalize_intent_runtime_policy,
)
from system_v4.skills.a1_rosetta_mapper import A1RosettaMapper


# ═══════════════════════════════════════════════════════════════════════
# L0 LEXEME SET — From MEGABOOT Thread B v3.9.9 (Spec 03 / RQ-024)
# This is the ONLY vocabulary that is free at boot. Everything else
# must earn admission through TERM_DEF, LABEL_DEF, CANON_PERMIT.
# ═══════════════════════════════════════════════════════════════════════
L0_LEXEME_SET: Set[str] = {
    "finite", "dimensional", "hilbert", "space",
    "density", "matrix", "operator",
    "channel", "cptp", "unitary",
    "lindblad", "hamiltonian", "commutator",
    "anticommutator", "trace", "partial",
    "tensor", "superoperator", "generator",
}

# Derived-only primitives — these CANNOT be used as bare primitives
# unless explicitly admitted to CANONICAL_ALLOWED via term pipeline
DERIVED_ONLY_TERMS: Set[str] = {
    "equal", "equality", "identity", "equals_sign",
    "time", "before", "after", "cause", "implies", "results",
    "coordinate", "frame", "metric", "distance",
    "number", "counting", "integer", "natural", "real", "probability", "random", "ratio",
    "set", "function", "relation", "mapping", "domain", "codomain",
}

# ═══════════════════════════════════════════════════════════════════════
# DISCOURSE STOPLIST — Terms that should NEVER become extraction targets
# These are meta/narrative labels that leak into extraction from
# description text. A1 must not mine these as TERM_DEF or MATH_DEF.
# ═══════════════════════════════════════════════════════════════════════
DISCOURSE_STOPLIST: Set[str] = {
    "promoted", "concept", "canonical", "legacy", "compile", "compiled",
    "pipeline", "module", "component", "framework", "abstraction", "layer",
    "process", "workflow", "architecture", "design", "pattern", "system",
    "bundle", "playbook", "dispatch", "controller", "worker", "skill",
    "intake", "ingest", "extract", "extraction", "boot", "reboot",
    "step", "stage", "phase", "sequence", "loop", "cycle",
    "document", "file", "json", "markdown", "script", "config",
    "status", "state", "active", "pending", "done", "locked",
    "audit", "check", "verify", "validate", "test", "fixture",
    "reason", "summary", "description", "overview", "note", "context",
    "upgrade", "migration", "version", "legacy", "archive",
    "mission", "reduction", "objective",
    "ontology", "teleology", "universe", "multiverse", "genesis",
    "holographic", "emerge", "emergence", "principle"
}

# ═══════════════════════════════════════════════════════════════════════
# OVERLAY TERMS — High-level labels that should NOT enter the kernel
# directly.  They route to Rosetta v2 as AMBIGUOUS_LABEL or
# OVERLAY_ALIAS packets instead of becoming MATH_DEF or TERM_DEF.
# ═══════════════════════════════════════════════════════════════════════
OVERLAY_TERMS: Set[str] = {
    "entropy", "information", "measurement", "collapse", "observer",
    "geometry", "reality", "spacetime", "consciousness", "perception",
    "energy", "force", "field", "wave", "particle", "causality",
    "symmetry", "conservation", "thermodynamics", "mechanics",
}

# JARGON TERMS — Theory-internal or compressed labels that must go
# through isolated decomposition before they can reach kernel space.
# This set grows as novel vocabulary is identified in source material.
JARGON_TERMS: Set[str] = {
    "engine", "attractor", "basin", "axis", "ratchet", "wiggle",
    "conflation", "orthogonal", "degrees", "freedom", "manifold",
    "topological", "constraint", "geometric", "retrocausal",
    "nonclassical", "holodeck", "rosetta", "overlay",
}
# Item class → ID prefix mapping (from MEGABOOT BR-002)
ID_NAMESPACE = {
    "AXIOM_HYP": ["F", "W", "K", "M"],
    "PROBE_HYP": ["P"],
    "SPEC_HYP": ["S", "R"],
}

# Allowed kinds (from MEGABOOT / Spec 03)
ALLOWED_KINDS = {"MATH_DEF", "TERM_DEF", "LABEL_DEF", "CANON_PERMIT", "SIM_SPEC"}

# Forbidden fields (A1 output policy)
FORBIDDEN_FIELDS = {"confidence", "probability", "embedding", "hidden_prompt"}


@dataclass
class DefField:
    """A single DEF_FIELD in a compile-ready candidate."""
    field_id: str
    name: str
    value_kind: str  # BARE | TERM_QUOTED | LABEL_QUOTED | FORMULA_QUOTED
    value: str


@dataclass
class Assertion:
    """A single ASSERT in a compile-ready candidate."""
    assert_id: str
    token_class: str
    token: str


@dataclass
class KernelCandidate:
    """A compile-ready candidate object per Spec 05/18."""
    item_class: str       # AXIOM_HYP | PROBE_HYP | SPEC_HYP
    id: str               # Namespace-prefixed ID
    kind: str             # MATH_DEF | TERM_DEF | LABEL_DEF | CANON_PERMIT | SIM_SPEC
    requires: List[str]   # Dependency IDs (may be empty)
    def_fields: List[DefField]
    asserts: List[Assertion]
    operator_id: str = "OP_COLD_CORE_EXTRACT"

    # Metadata (not in compile lane)
    source_concept_id: Optional[str] = None
    primary_candidate_id: Optional[str] = None
    extraction_notes: Optional[str] = None
    alt_intent: Optional[str] = None  # None for primary, "TRY_TO_FAIL" for alternatives

    def to_dict(self) -> dict:
        d = {
            "item_class": self.item_class,
            "id": self.id,
            "kind": self.kind,
            "requires": self.requires,
            "def_fields": [asdict(f) for f in self.def_fields],
            "asserts": [asdict(a) for a in self.asserts],
            "operator_id": self.operator_id,
        }
        if self.source_concept_id:
            d["source_concept_id"] = self.source_concept_id
        if self.primary_candidate_id:
            d["primary_candidate_id"] = self.primary_candidate_id
        return d


@dataclass
class NegativeSimPlan:
    """A falsification test plan for SIM."""
    target_id: str
    failure_mode_id: str
    expected_outcome_class: str  # NEG_EXPECT_FAIL_TARGET | NEG_EXPECT_REJECT_ALTERNATIVE
    sim_spec_id: Optional[str] = None
    description: str = ""


@dataclass
class A1StrategyPacket:
    """Complete A1_STRATEGY_v1 output packet."""
    schema: str = "A1_STRATEGY_v1"
    strategy_id: str = ""
    inputs: Dict[str, Any] = field(default_factory=dict)
    budget: Dict[str, int] = field(default_factory=lambda: {"max_items": 200, "max_sims": 200})
    policy: Dict[str, Any] = field(default_factory=lambda: {
        "forbid_fields": list(FORBIDDEN_FIELDS),
        "overlay_ban_terms": [],
        "require_try_to_fail": True,
    })
    targets: List[dict] = field(default_factory=list)
    alternatives: List[dict] = field(default_factory=list)
    sims: Dict[str, list] = field(default_factory=lambda: {"positive": [], "negative": []})
    self_audit: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class A1WigglePacket:
    """Sequential multi-lane A1 output envelope."""
    schema: str = "A1_WIGGLE_v1"
    wiggle_id: str = ""
    lane_packets: List[dict] = field(default_factory=list)
    merge_report: Dict[str, Any] = field(default_factory=dict)
    merged_strategy_packet: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class A1Brain:
    """
    The A1 Persistent Brain.

    Maintains term registry state, Rosetta mappings, and performs
    cold-core extraction from A2 concepts into compile-ready candidates.
    """

    def __init__(self, repo_root: str, eval_mode: bool = False):
        self.repo_root = Path(repo_root)
        self.brain_state_path = self.repo_root / "system_v4" / "a1_state" / "a1_brain_state.json"
        self.eval_mode = eval_mode

        # Term registry: tracks what has been admitted by B
        # term_literal -> {state, bound_math_def, provenance}
        self.term_registry: Dict[str, dict] = {}

        # Rosetta mappings handled by mapper
        self.rosetta = A1RosettaMapper(repo_root)

        # Rosetta v2 typed proposal store
        from system_v4.skills.rosetta_v2 import RosettaStore
        self.rosetta_v2 = RosettaStore(repo_root)

        # A1 routing state — treatment trace for every concept
        from system_v4.skills.a1_routing_state import A1RoutingState
        if eval_mode:
            # Ephemeral routing: don't load from or write to disk
            self.routing = A1RoutingState.__new__(A1RoutingState)
            self.routing.records = {}
            self.routing.workspace_root = Path(repo_root).resolve()
            self.routing.state_dir = self.routing.workspace_root / "system_v4" / "a1_state"
            self.routing.state_path = self.routing.state_dir / "_eval_ephemeral_routing.json"
        else:
            self.routing = A1RoutingState(repo_root)

        # Graveyard terms: terms that failed B admission
        self.graveyard_terms: Dict[str, dict] = {}

        # ID counter for generating unique IDs
        self._id_counters = {"F": 1, "W": 1, "K": 1, "M": 1, "P": 1, "S": 1, "R": 1}

        # Load existing state if present
        self._load_state()

    def _load_state(self):
        if self.brain_state_path.exists():
            with open(self.brain_state_path) as f:
                state = json.load(f)
            self.term_registry = state.get("term_registry", {})
            self.graveyard_terms = state.get("graveyard_terms", {})
            self.graveyard_terms = state.get("graveyard_terms", {})
            self._id_counters = state.get("id_counters", self._id_counters)

    def save_state(self):
        state = {
            "term_registry": self.term_registry,
            "graveyard_terms": self.graveyard_terms,
            "id_counters": self._id_counters,
            "saved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.brain_state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.brain_state_path, "w") as f:
            json.dump(state, f, indent=2)

    def _next_id(self, prefix: str) -> str:
        """Generate next sequential ID for a given prefix."""
        n = self._id_counters.get(prefix, 1)
        self._id_counters[prefix] = n + 1
        return f"{prefix}{n:03d}"

    def is_token_safe(self, token: str) -> bool:
        """Check if a token is safe for compile-lane BARE values."""
        # Must be alphanumeric + underscore, no spaces, no free English
        if not re.match(r'^[A-Za-z0-9_]+$', token):
            return False
        # Check each segment against L0 + term registry
        segments = token.lower().split("_")
        for seg in segments:
            if re.match(r'^[0-9]+$', seg):
                continue  # numeric suffixes OK
            if seg in L0_LEXEME_SET:
                continue
            if seg in self.term_registry and self.term_registry[seg]["state"] in (
                "TERM_PERMITTED", "LABEL_PERMITTED", "CANONICAL_ALLOWED"
            ):
                continue
            return False
        return True

    def is_derived_only(self, token: str) -> bool:
        """Check if a token contains derived-only primitives."""
        segments = token.lower().split("_")
        for seg in segments:
            if seg in DERIVED_ONLY_TERMS:
                if seg not in self.term_registry or \
                   self.term_registry[seg]["state"] != "CANONICAL_ALLOWED":
                    return True
        return False

    def extract_kernel_candidate(self, concept_id: str, name: str,
                                  description: str, tags: List[str],
                                  properties: Dict[str, Any]) -> List[KernelCandidate]:
        """
        Cold-core extraction: take an A2 concept and produce compile-ready candidates.

        Every call writes an A1RouteRecord so the selector never re-eats residue.
        Routes concepts into: KERNEL_EXTRACTED, ROSETTA_DIVERTED,
        NO_STRUCTURAL_SIGNAL, or REJECTED_AS_DISCOURSE.
        """
        from system_v4.skills.a1_routing_state import A1RouteRecord
        candidates = []
        node_type = properties.get("node_type", "") if properties else ""

        # ── 1. Check existing routing record ──
        # In eval mode, skip the routing check — always classify fresh.
        if not self.eval_mode:
            existing_route = self.routing.get(concept_id)
            if existing_route and not existing_route.reopen_requested:
                if existing_route.route_status in (
                    "KERNEL_EXTRACTED", "ROSETTA_DIVERTED",
                    "NO_STRUCTURAL_SIGNAL", "REJECTED_AS_DISCOURSE"
                ):
                    return []  # Already treated

        # Normalize concept name to token form
        raw_name = name.lower().replace("-", "_").replace(" ", "_")
        clean_name = re.sub(r'[^a-z0-9_]', '', raw_name)

        # ── 2. Classify ──
        kind, item_class = self._classify_concept(clean_name, description, tags, properties)

        # ── 3. Determine routing category ──
        name_words = set(clean_name.split("_")) - {"", "the", "of", "and", "in", "a", "is"}
        overlay_hits = name_words & OVERLAY_TERMS
        jargon_hits = name_words & JARGON_TERMS

        has_structural_form = bool(
            properties and (properties.get("structural_form")
                            or any(isinstance(v, str) and "structural_form" in v
                                   for v in properties.values()))
        )

        # Divert if name contains ANY overlay/jargon token and kind is
        # non-structural.  The old "majority" gate missed mixed labels
        # like dual_szilard_engine (1 jargon word out of 3).
        has_overlay = len(overlay_hits) > 0
        has_jargon = len(jargon_hits) > 0
        is_rosetta_worthy = has_overlay or has_jargon

        # ── Route A: Rosetta-worthy overlay/jargon (non-structural) ──
        if is_rosetta_worthy and kind in ("TERM_DEF", "LABEL_DEF") and not has_structural_form:
            obj_class = "AMBIGUOUS_LABEL" if has_overlay else "SENSE_CANDIDATE"
            status = "AMBIGUOUS" if has_overlay else "PARKED"
            pkt = self.rosetta_v2.upsert_diversion(
                source_concept_id=concept_id,
                source_term=clean_name,
                source_context=f"A1 diversion: {description[:200]}",
                source_node_type=node_type,
                source_tags=tags,
                object_class=obj_class,
                candidate_sense_id=f"{clean_name}::{'UNRESOLVED' if has_overlay else 'theory_internal'}",
                confidence_mode="theory_internal" if has_jargon else "unknown",
                status=status,
                routing_reason="overlay_or_jargon_term",
            )
            if not self.eval_mode:
                self.rosetta_v2.save()
            self.routing.upsert(A1RouteRecord(
                source_concept_id=concept_id,
                source_name=name,
                source_node_type=node_type,
                route_status="ROSETTA_DIVERTED",
                route_reason="overlay_or_jargon_term",
                classification_kind=kind,
                rosetta_packet_ids=[pkt.packet_id],
            ))
            if not self.eval_mode:
                self.routing.save()
            return []

        # ── Route B: Pure discourse / no structural signal ──
        # Extract structural tokens from name and description
        structural_tokens = self._extract_structural_tokens(clean_name, description, properties)

        # Check which tokens are L0-safe
        safe_tokens = [t for t in structural_tokens if self.is_token_safe(t)]
        unsafe_tokens = [t for t in structural_tokens if not self.is_token_safe(t)
                         and t not in DISCOURSE_STOPLIST]

        # Skip concepts that are pure discourse with no structural signal
        if kind == "LABEL_DEF" and not safe_tokens and not unsafe_tokens:
            # Determine if this is discourse or merely non-structural
            desc_words = set(re.findall(r'[a-z]+', (description or "").lower()))
            discourse_hits = len(desc_words & DISCOURSE_STOPLIST)
            if discourse_hits > 2:
                route_status = "REJECTED_AS_DISCOURSE"
                route_reason = f"discourse_stoplist_hits={discourse_hits}"
            else:
                route_status = "NO_STRUCTURAL_SIGNAL"
                route_reason = "no_kernel_extractable_structure"

            self.routing.upsert(A1RouteRecord(
                source_concept_id=concept_id,
                source_name=name,
                source_node_type=node_type,
                route_status=route_status,
                route_reason=route_reason,
                classification_kind=kind,
            ))
            if not self.eval_mode:
                self.routing.save()
            return candidates  # empty

        # ── Route C: Kernel extraction ──
        if safe_tokens or kind in ("MATH_DEF", "TERM_DEF", "SIM_SPEC"):
            cand = self._build_primary_candidate(
                concept_id, clean_name, kind, item_class,
                safe_tokens, unsafe_tokens, description, tags
            )
            candidates.append(cand)

            if kind in ("MATH_DEF", "TERM_DEF"):
                probe = self._build_probe(concept_id, clean_name, cand)
                candidates.append(probe)

        if kind != "LABEL_DEF":
            for tk in unsafe_tokens:
                if not self.is_derived_only(tk):
                    admission = self._build_term_admission(concept_id, tk)
                    if admission:
                        candidates.append(admission)

        # Write routing record for kernel-extracted concepts
        if candidates:
            self.routing.upsert(A1RouteRecord(
                source_concept_id=concept_id,
                source_name=name,
                source_node_type=node_type,
                route_status="KERNEL_EXTRACTED",
                route_reason="compile_ready_candidates_emitted",
                classification_kind=kind,
                kernel_candidate_ids=[c.id for c in candidates],
            ))
            if not self.eval_mode:
                self.routing.save()
        else:
            # Classified as structural kind but no candidates built (edge case)
            self.routing.upsert(A1RouteRecord(
                source_concept_id=concept_id,
                source_name=name,
                source_node_type=node_type,
                route_status="NO_STRUCTURAL_SIGNAL",
                route_reason=f"classified_{kind}_but_no_candidates_built",
                classification_kind=kind,
            ))
            if not self.eval_mode:
                self.routing.save()

        return candidates

    # ─── Discourse stoplist: terms that should NEVER become candidates ───
    # These are meta/discourse labels that leak into extraction from description text.

    def _classify_concept(self, name: str, description: str,
                          tags: List[str], properties: Dict[str, Any] = None) -> Tuple[str, str]:
        """Classify concept into kind + item_class using L0-weighted scoring."""
        desc_lower = (description or "").lower()
        desc_words = set(re.findall(r'[a-z]+', desc_lower))
        name_words = set(name.lower().split("_"))
        
        # Combine name and description words for full context, but weight name heavily later
        all_words = desc_words | name_words
        props = properties or {}

        # ── L0 structural density ──
        l0_hits = len(all_words & L0_LEXEME_SET)
        name_l0_hits = len(name_words & L0_LEXEME_SET)

        # ── Extended math vocabulary (beyond L0 but still structural) ──
        MATH_EXT = {"eigenvalue", "spectral", "adjoint", "hermitian", "projection",
                    "kraus", "isometry", "entropy", "algebra", "quantum", "von",
                    "neumann", "bloch", "pauli", "stinespring", "choi"}
        math_ext_hits = len(all_words & MATH_EXT)
        name_math_ext_hits = len(name_words & MATH_EXT)

        # ── Spec/constraint signals ──
        SPEC_SIGNALS = {"constraint", "requirement", "invariant", "gate", "fence",
                        "validator", "conformance", "deterministic", "stress",
                        "tier", "threshold", "pipeline", "execution", "audit", "commit",
                        "compiler", "compilation", "grammar", "ordering", "export"}
        spec_hits = len(all_words & SPEC_SIGNALS)
        name_spec_hits = len(name_words & SPEC_SIGNALS)

        # ── Discourse/meta penalty ──
        discourse_hits = len(desc_words & DISCOURSE_STOPLIST)

        # ── Score each kind ──
        # Name signals are highly weighted. Discourse penalty is capped or reduced if name is strong.
        structural_name_bonus = (name_l0_hits * 6) + (name_math_ext_hits * 4)
        
        math_score = (l0_hits * 2) + (math_ext_hits * 1) + structural_name_bonus
        if structural_name_bonus > 0:
             math_score -= min(discourse_hits * 2, structural_name_bonus - 1)
        else:
             math_score -= (discourse_hits * 4)

        structural_spec_bonus = (name_spec_hits * 8)
        spec_score = (spec_hits * 2) + structural_spec_bonus + (l0_hits * 1)
        if structural_spec_bonus > 0:
             spec_score -= min(discourse_hits * 2, structural_spec_bonus - 1)
        else:
             spec_score -= (discourse_hits * 3)

        rosetta_hits = 0
        name_rosetta_hits = 0
        for w in all_words:
            mapped = self.rosetta.get_kernel_translation(w)
            if mapped and mapped.startswith("S_TERM_"):
                rosetta_hits += 1
                if w in name_words:
                    name_rosetta_hits += 1

        structural_term_bonus = (name_l0_hits * 5) + (name_rosetta_hits * 8)
        term_score = structural_term_bonus + (l0_hits * 1) + (rosetta_hits * 3)
        if structural_term_bonus > 0:
             term_score -= min(discourse_hits * 2, structural_term_bonus - 1)
        else:
             term_score -= (discourse_hits * 4)

        # ── Structural form override & JSON trap inspection ──
        # If concept has a structural_form property, strongly prefer MATH_DEF
        
        has_structural_form = False
        if props:
            # Check direct key
            if props.get("structural_form"):
                 has_structural_form = True
            else:
                 # Check if it was packed as a string dump 
                 for v in props.values():
                     if isinstance(v, str) and "structural_form" in v:
                          has_structural_form = True
                          break
                          
        if has_structural_form:
            math_score += 15

        # Overrides for dense string dumps (e.g. JSON strings where tokenization fails)
        if "partial_trace" in desc_lower or "density_matrix" in desc_lower:
            math_score += 10

        # ── Decision ──
        
        # Immediate esoteric filter to stop highly theoretical physics/philosophy concepts
        # from abusing math/term signals.
        tag_words = set(t.lower() for t in tags)
        ESOTERIC_BAN = {"universe", "multiverse", "holographic", "ontology", "teleology", "genesis", "emergence", "emerge"}
        if len((all_words | tag_words) & ESOTERIC_BAN) > 0:
             return "LABEL_DEF", "AXIOM_HYP"
        if math_score >= 8:
            return "MATH_DEF", "AXIOM_HYP"
        elif spec_score >= 7:
            return "SIM_SPEC", "SPEC_HYP"
        elif term_score >= 5:
            return "TERM_DEF", "AXIOM_HYP"
        elif math_score >= 4:
            return "MATH_DEF", "AXIOM_HYP"
        elif spec_score >= 4:
            return "SIM_SPEC", "SPEC_HYP"
        else:
            return "LABEL_DEF", "AXIOM_HYP"

    def _extract_structural_tokens(self, name: str, description: str,
                                    properties: Dict[str, Any] = None) -> List[str]:
        """Extract structural tokens using compound form detection.

        Sources tokens from concept name AND description.
        Prefers compound L0 bigrams (density_matrix, hilbert_space) over
        individual word deduplication. Filters discourse terms.
        """
        props = properties or {}

        # ── Prefer structural_form property if available ──
        if props.get("structural_form"):
            form = props["structural_form"]
            return [t.strip() for t in form.split(",") if t.strip()]

        desc_lower = (description or "").lower()
        desc_words = re.findall(r'[a-z][a-z0-9]*', desc_lower)
        name_words = name.lower().split("_")
        
        # Name is the primary structural signal. Description provides supporting context.
        words = name_words + desc_words

        # ── Build compound tokens from L0 bigrams ──
        compounds = []
        L0_LIST = list(L0_LEXEME_SET)
        
        # First check name explicitly for compounds (highly reliable)
        for i in range(len(name_words) - 1):
            w1, w2 = name_words[i], name_words[i + 1]
            if w1 in L0_LEXEME_SET and w2 in L0_LEXEME_SET:
                compound = f"{w1}_{w2}"
                if compound not in compounds:
                    compounds.append(compound)
                    
        # Then check remaining words
        for i in range(len(words) - 1):
            w1, w2 = words[i], words[i + 1]
            if w1 in L0_LEXEME_SET and w2 in L0_LEXEME_SET:
                compound = f"{w1}_{w2}"
                if compound not in compounds:
                    compounds.append(compound)

        # ── Collect individual L0 tokens not already in compounds ──
        seen = set()
        for c in compounds:
            for part in c.split("_"):
                seen.add(part)

        singles = []
        
        # Prioritize name singles
        for w in name_words:
            if w in L0_LEXEME_SET and w not in seen and w not in singles:
                singles.append(w)
                
        # Then description singles
        for w in desc_words:
            if w in L0_LEXEME_SET and w not in seen and w not in singles:
                singles.append(w)

        # ── Result: compounds first, then singles ──
        tokens = compounds + singles

        # ── Rosetta Translation ──
        # Check all raw words (not just L0) against active Rosetta mappings
        # to pull in jargon that translates to kernel IDs
        for w in words:
            mapped_kernel_target = self.rosetta.get_kernel_translation(w)
            # Remove the S_TERM_ prefix so a1_brain treats it as a structural token, not a full ID yet
            if mapped_kernel_target and mapped_kernel_target.startswith("S_TERM_"):
                translated_token = mapped_kernel_target[7:].lower() # e.g. S_TERM_OBSERVABLE -> observable
                if translated_token not in tokens:
                    tokens.append(translated_token)

        # ── Fallback: if no L0 tokens + no rosetta hits, try extended math vocabulary or spec signals ──
        if not tokens:
            MATH_EXT = {"eigenvalue", "spectral", "adjoint", "hermitian", "projection",
                        "kraus", "isometry", "entropy", "algebra", "quantum"}
            SPEC_SIGNALS = {"constraint", "requirement", "invariant", "gate", "fence",
                            "validator", "conformance", "deterministic", "stress",
                            "tier", "threshold", "pipeline", "execution", "audit", "commit"}
            FALLBACK_SET = MATH_EXT | SPEC_SIGNALS
            
            # Name first
            for w in name_words:
                if w in FALLBACK_SET and w not in tokens and w not in DISCOURSE_STOPLIST:
                    tokens.append(w)
            # Then description
            for w in desc_words:
                if w in FALLBACK_SET and w not in tokens and w not in DISCOURSE_STOPLIST:
                    tokens.append(w)
                    if len(tokens) >= 3:
                        break

        return tokens

    def _build_primary_candidate(self, concept_id: str, name: str,
                                  kind: str, item_class: str,
                                  safe_tokens: List[str],
                                  unsafe_tokens: List[str],
                                  description: str,
                                  tags: List[str]) -> KernelCandidate:
        """Build a primary compile-ready candidate."""
        prefix = ID_NAMESPACE[item_class][0]
        cand_id = self._next_id(prefix)

        def_fields = []
        structural_tokens = [tk for tk in safe_tokens if tk]
        if kind == "MATH_DEF" and not structural_tokens:
            structural_tokens = re.findall(r"[a-z0-9]+", (name or "").lower())[:5]

        # Emit kind-specific required fields so graph-derived primaries do not
        # arrive at B already schema-invalid.
        if kind == "TERM_DEF":
            term_literal = None
            for token in structural_tokens:
                if not self.is_derived_only(token):
                    term_literal = token
                    break
            if not term_literal:
                for token in re.findall(r"[a-z0-9]+", (name or "").lower()):
                    if not self.is_derived_only(token):
                        term_literal = token
                        break
            if term_literal:
                def_fields.append(DefField(
                    field_id=f"DF_{cand_id}_01",
                    name="term_literal",
                    value_kind="BARE",
                    value=term_literal,
                ))
        elif kind == "SIM_SPEC":
            # Graph-derived SIM specs do not have an upstream primary candidate
            # yet, so bind the probe target back to the source concept.
            def_fields.append(DefField(
                field_id=f"DF_{cand_id}_01",
                name="probe_target",
                value_kind="BARE",
                value=concept_id,
            ))
        elif structural_tokens:
            structural_value = "_".join(structural_tokens[:5])
            def_fields.append(DefField(
                field_id=f"DF_{cand_id}_01",
                name="structural_form",
                value_kind="BARE",
                value=structural_value,
            ))

        # Add description as LABEL_QUOTED (safe — doesn't enter compile scan)
        if description:
            def_fields.append(DefField(
                field_id=f"DF_{cand_id}_02",
                name="description",
                value_kind="LABEL_QUOTED",
                value=description[:200],  # truncate for sanity
            ))

        # Build assertions from safe tokens
        asserts = []
        for i, token in enumerate(structural_tokens[:3]):
            asserts.append(Assertion(
                assert_id=f"A_{cand_id}_{i+1:02d}",
                token_class="STRUCTURAL",
                token=token,
            ))

        return KernelCandidate(
            item_class=item_class,
            id=cand_id,
            kind=kind,
            requires=[],  # Will be populated by dependency analysis
            def_fields=def_fields,
            asserts=asserts,
            source_concept_id=concept_id,
            extraction_notes=f"Cold-core extraction from {name}. "
                            f"L0 tokens: {len(safe_tokens)}, "
                            f"non-L0 tokens: {len(unsafe_tokens)}",
        )

    def _build_probe(self, concept_id: str, name: str,
                     primary: KernelCandidate) -> KernelCandidate:
        """Build a PROBE_HYP to test the primary candidate."""
        probe_id = self._next_id("P")

        # Probe checks that the primary's structural form is consistent
        def_fields = [DefField(
            field_id=f"DF_{probe_id}_01",
            name="probe_target",
            value_kind="BARE",
            value=primary.id,
        )]

        asserts = [Assertion(
            assert_id=f"A_{probe_id}_01",
            token_class="PROBE_CHECK",
            token=f"structural_consistency_{primary.id}",
        )]

        return KernelCandidate(
            item_class="PROBE_HYP",
            id=probe_id,
            kind="SIM_SPEC",
            requires=[primary.id],
            def_fields=def_fields,
            asserts=asserts,
            source_concept_id=concept_id,
            extraction_notes=f"Probe for {primary.id}",
        )

    def _build_term_admission(self, concept_id: str, token: str) -> Optional[KernelCandidate]:
        """Build a TERM_DEF candidate to admit a new term."""
        if token in DERIVED_ONLY_TERMS:
            return None  # Can't admit derived-only this way

        cand_id = self._next_id("F")

        def_fields = [
            DefField(
                field_id=f"DF_{cand_id}_01",
                name="term_literal",
                value_kind="BARE",
                value=token,
            ),
            DefField(
                field_id=f"DF_{cand_id}_02",
                name="admission_basis",
                value_kind="LABEL_QUOTED",
                value=f"Structural term extracted from concept analysis",
            ),
        ]

        asserts = [Assertion(
            assert_id=f"A_{cand_id}_01",
            token_class="TERM_ADMISSION",
            token=token,
        )]

        return KernelCandidate(
            item_class="AXIOM_HYP",
            id=cand_id,
            kind="TERM_DEF",
            requires=[],
            def_fields=def_fields,
            asserts=asserts,
            source_concept_id=concept_id,
            extraction_notes=f"Term admission request for '{token}'",
        )

    def generate_alternatives(self, primary: KernelCandidate) -> List[KernelCandidate]:
        """
        Generate alternatives designed to fail (requirement RQ-103).

        Each target cluster must emit at least one explicit graveyard-seeking
        alternative with alt_intent=TRY_TO_FAIL.
        """
        alternatives = []

        # Alt 1: Same structural claim but with a derived-only term injected
        # (should be caught by DERIVED_ONLY_GUARD)
        alt1_id = self._next_id(ID_NAMESPACE[primary.item_class][0])
        alt1_fields = list(primary.def_fields)
        if alt1_fields:
            # Inject a derived-only term into the first field
            poisoned_field = DefField(
                field_id=f"DF_{alt1_id}_POISON",
                name="structural_form",
                value_kind="BARE",
                value="equality_identity",  # derived-only terms
            )
            alt1_fields = [poisoned_field] + alt1_fields[1:]

        alternatives.append(KernelCandidate(
            item_class=primary.item_class,
            id=alt1_id,
            kind=primary.kind,
            requires=primary.requires,
            def_fields=alt1_fields,
            asserts=primary.asserts,
            alt_intent="TRY_TO_FAIL",
            source_concept_id=primary.source_concept_id,
            primary_candidate_id=primary.id,
            extraction_notes=f"Alt of {primary.id}: derived-only poison test",
        ))

        # Alt 2: Forward dependency (references undefined ID)
        # (should be caught by DEPENDENCY_GRAPH / FORWARD_DEPEND)
        alt2_id = self._next_id(ID_NAMESPACE[primary.item_class][0])
        alternatives.append(KernelCandidate(
            item_class=primary.item_class,
            id=alt2_id,
            kind=primary.kind,
            requires=["UNDEFINED_999"],  # Nonexistent dependency
            def_fields=primary.def_fields,
            asserts=primary.asserts,
            alt_intent="TRY_TO_FAIL",
            source_concept_id=primary.source_concept_id,
            primary_candidate_id=primary.id,
            extraction_notes=f"Alt of {primary.id}: forward-dependency test",
        ))

        # Alt 3: Near-duplicate (same content, different ID)
        # (should be caught by NEAR_DUPLICATE if primary is already admitted)
        alt3_id = self._next_id(ID_NAMESPACE[primary.item_class][0])
        alternatives.append(KernelCandidate(
            item_class=primary.item_class,
            id=alt3_id,
            kind=primary.kind,
            requires=primary.requires,
            def_fields=primary.def_fields,
            asserts=primary.asserts,
            alt_intent="TRY_TO_FAIL",
            source_concept_id=primary.source_concept_id,
            primary_candidate_id=primary.id,
            extraction_notes=f"Alt of {primary.id}: near-duplicate test",
        ))

        return alternatives

    def _apply_lane_bias(
        self,
        candidates: List[KernelCandidate],
        lane_id: Optional[str] = None,
        bias_config: Optional[Dict[str, Any]] = None,
    ) -> List[KernelCandidate]:
        """Apply bounded lane-scoped filtering/reordering outside compile payloads."""
        if not candidates:
            return candidates
        config = bias_config or {}
        filtered = list(candidates)

        allowed_kinds = set(config.get("allowed_kinds", []))
        if allowed_kinds:
            allowed = [c for c in filtered if c.kind in allowed_kinds]
            if allowed:
                filtered = allowed

        preferred_kind_order = config.get("preferred_kind_order", [])
        if preferred_kind_order:
            rank = {kind: idx for idx, kind in enumerate(preferred_kind_order)}
            filtered.sort(key=lambda c: (rank.get(c.kind, len(rank)), c.id))

        max_candidates = config.get("max_candidates_per_concept")
        if isinstance(max_candidates, int) and max_candidates > 0:
            filtered = filtered[:max_candidates]

        return filtered

    def _score_intent_focus(self, node: Dict[str, Any], focus_terms: List[str]) -> int:
        if not focus_terms:
            return 0
        haystacks = [
            str(node.get("name", "")),
            str(node.get("description", "")),
            " ".join(str(tag) for tag in (node.get("tags", []) or [])),
        ]
        corpus = " ".join(h.lower() for h in haystacks)
        return sum(1 for term in focus_terms if term and term.lower() in corpus)

    def _apply_intent_candidate_policy(
        self,
        candidates: List[KernelCandidate],
        node: Dict[str, Any],
        intent_control: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[KernelCandidate], Dict[str, Any]]:
        report: Dict[str, Any] = {
            "applied": False,
            "effective_mode": "disabled",
            "concept_focus_score": 0,
            "suppressed_count": 0,
            "suppressed_kinds": [],
        }
        if not candidates or not intent_control:
            return candidates, report

        runtime_policy = normalize_intent_runtime_policy(intent_control)
        policy = (runtime_policy.get("candidate_policy", {}) or {})
        runtime = (
            runtime_policy.get("concept_selection_runtime")
            or ((runtime_policy.get("concept_selection", {}) or {}).get("runtime", {}))
            or {}
        )
        focus_terms = list(
            runtime_policy.get("executable_focus_terms")
            or runtime_policy.get("steering_focus_terms")
            or runtime_policy.get("focus_terms", [])
            or []
        )
        if not policy or not focus_terms:
            return candidates, report

        if policy.get("mode") == "disabled":
            report["effective_mode"] = "disabled_by_quality"
            return candidates, report

        if runtime.get("explicit_targets_used") and policy.get("respect_explicit_targets", True):
            report["effective_mode"] = "explicit-target-passthrough"
            return candidates, report

        apply_on_modes = set(policy.get("apply_on_modes", []) or [])
        runtime_mode = str(runtime.get("effective_mode", ""))
        if apply_on_modes and runtime_mode not in apply_on_modes:
            report["effective_mode"] = "runtime-mode-bypass"
            return candidates, report

        focus_score = self._score_intent_focus(node, focus_terms)
        report["concept_focus_score"] = focus_score
        min_focus_score = int(policy.get("min_focus_score", 1) or 1)
        if focus_score >= min_focus_score:
            report["effective_mode"] = "focus-aligned"
            return candidates, report

        if (
            policy.get("mode") == "suppress-off-focus-term-defs"
            and policy.get("suppress_term_defs_without_focus", False)
        ):
            retained = [c for c in candidates if c.kind != "TERM_DEF"]
            suppressed = len(candidates) - len(retained)
            if retained and suppressed > 0:
                report["applied"] = True
                report["effective_mode"] = "term-def-suppressed"
                report["suppressed_count"] = suppressed
                report["suppressed_kinds"] = ["TERM_DEF"]
                return retained, report
            report["effective_mode"] = "fail-open-no-non-term-candidates"
            return candidates, report

        report["effective_mode"] = "no-op"
        return candidates, report

    def generate_negative_sim_plans(self, primary: KernelCandidate,
                                     alternatives: List[KernelCandidate]) -> List[NegativeSimPlan]:
        """
        Generate negative sim plans (Spec 06 RQ-053).

        Negative sims are falsification tests, not generic failures.
        Each must specify target_id, failure_mode_id, expected_outcome_class.
        """
        plans = []

        # Plan 1: Expect the primary to fail if a core dependency is removed
        plans.append(NegativeSimPlan(
            target_id=primary.id,
            failure_mode_id=f"FM_{primary.id}_DEP_REMOVAL",
            expected_outcome_class="NEG_EXPECT_FAIL_TARGET",
            description=f"Remove core dependency and verify {primary.id} fails",
        ))

        # Plan 2: Expect each alternative to be rejected
        for alt in alternatives:
            plans.append(NegativeSimPlan(
                target_id=alt.id,
                failure_mode_id=f"FM_{alt.id}_DESIGNED_FAIL",
                expected_outcome_class="NEG_EXPECT_REJECT_ALTERNATIVE",
                description=f"Verify alternative {alt.id} is correctly rejected",
            ))

        return plans

    def build_strategy_packet(self, concept_ids: List[str],
                               graph_nodes: Dict[str, Any],
                               strategy_id: Optional[str] = None,
                               lane_id: Optional[str] = None,
                               bias_config: Optional[Dict[str, Any]] = None,
                               intent_control: Optional[Dict[str, Any]] = None) -> A1StrategyPacket:
        """
        Build a complete A1_STRATEGY_v1 packet from a batch of concept IDs.

        This is the main entry point: takes graph concept nodes, extracts
        candidates, generates alternatives, generates sim plans, and produces
        the full strategy packet.
        """
        if not strategy_id:
            strategy_id = f"A1_STRAT_{time.strftime('%Y%m%d_%H%M%S')}"

        runtime_policy = normalize_intent_runtime_policy(intent_control)
        effective_bias_config = merge_execution_bias(
            runtime_policy.get("bias_config", {}),
            bias_config or {},
        )
        effective_runtime_policy = json.loads(json.dumps(runtime_policy))
        effective_runtime_policy["bias_config"] = effective_bias_config

        all_targets = []
        all_alternatives = []
        all_positive_sims = []
        all_negative_sims = []
        intent_candidate_policy_reports: List[Dict[str, Any]] = []
        intent_alternative_policy_reports: List[Dict[str, Any]] = []
        
        # Track term literals in this batch to prevent duplicate TERM_DEFs
        batch_terms = set()

        for concept_id in concept_ids:
            node = graph_nodes.get(concept_id)
            if not node:
                continue

            name = node.get("name", concept_id)
            description = node.get("description", "")
            tags = node.get("tags", []) or []
            properties = node.get("properties", {})

            # Cold-core extraction
            candidates = self.extract_kernel_candidate(
                concept_id, name, description, tags, properties
            )

            if not candidates:
                continue

            candidates, intent_candidate_report = self._apply_intent_candidate_policy(
                candidates,
                node,
                intent_control=intent_control,
            )
            intent_candidate_report["concept_id"] = concept_id
            intent_candidate_report["concept_name"] = name
            intent_candidate_policy_reports.append(intent_candidate_report)

            if not candidates:
                continue

            # Filter duplicates if they are TERM_DEFs
            filtered_candidates = []
            for c in candidates:
                if c.kind == "TERM_DEF":
                    term = None
                    for df in c.def_fields:
                        if df.name == "term_literal":
                            term = df.value
                            break
                    if term:
                        if term in batch_terms or term in self.term_registry:
                            continue # Skip duplicate
                        batch_terms.add(term)
                
                filtered_candidates.append(c)
                
            filtered_candidates = self._apply_lane_bias(
                filtered_candidates, lane_id=lane_id, bias_config=effective_bias_config
            )

            if not filtered_candidates:
                continue
                
            candidates = filtered_candidates

            # Primary target is first candidate
            primary = candidates[0]
            all_targets.extend([c.to_dict() for c in candidates])

            # Generate alternatives designed to fail
            alternatives = self.generate_alternatives(primary)
            raw_alternative_count = len(alternatives)
            if effective_bias_config:
                max_alts = effective_bias_config.get("max_alternatives_per_primary")
                if effective_bias_config.get("suppress_alternatives"):
                    alternatives = []
                elif isinstance(max_alts, int) and max_alts >= 0:
                    alternatives = alternatives[:max_alts]
            alt_policy = (runtime_policy.get("alternative_policy", {}) or {})
            alt_runtime = {
                "concept_id": concept_id,
                "primary_candidate_id": primary.id,
                "configured_mode": alt_policy.get("mode", ""),
                "raw_count": raw_alternative_count,
                "kept_count": len(alternatives),
                "trimmed_count": max(0, raw_alternative_count - len(alternatives)),
                "applied": False,
                "effective_mode": "disabled",
            }
            if alt_policy:
                alt_runtime["effective_mode"] = "bounded-pass-through"
                if alt_runtime["trimmed_count"] > 0:
                    alt_runtime["applied"] = True
                    alt_runtime["effective_mode"] = "alt-cap-trimmed"
            intent_alternative_policy_reports.append(alt_runtime)
            all_alternatives.extend([a.to_dict() for a in alternatives])

            # Generate sim plans
            neg_plans = self.generate_negative_sim_plans(primary, alternatives)
            for plan in neg_plans:
                all_negative_sims.append({
                    "target_id": plan.target_id,
                    "failure_mode_id": plan.failure_mode_id,
                    "expected_outcome_class": plan.expected_outcome_class,
                    "description": plan.description,
                })

            # Positive sim plan: verify primary holds under baseline conditions
            all_positive_sims.append({
                "sim_id": f"SIM_{primary.id}_BASELINE",
                "target_id": primary.id,
                "tier": "T0_ATOM",
                "family": "BASELINE",
            })

        # Build self-audit
        state_hash = hashlib.sha256(
            json.dumps(self.term_registry, sort_keys=True).encode()
        ).hexdigest()

        packet = A1StrategyPacket(
            strategy_id=strategy_id,
            inputs={
                "state_hash": state_hash,
                "fuel_slice_hashes": [],
                "bootpack_rules_hash": "",  # Would be MEGABOOT hash
                "concept_ids": concept_ids,
                "lane_id": lane_id,
                "bias_config": effective_bias_config,
                "intent_control": {
                    "surface_id": (intent_control or {}).get("surface_id", ""),
                    "surface_hash": ((intent_control or {}).get("provenance", {}) or {}).get("surface_hash", ""),
                    "focus_terms": runtime_policy.get("focus_terms", []),
                    "runtime_policy": runtime_policy,
                    "effective_runtime_policy": effective_runtime_policy,
                    "concept_selection": runtime_policy.get("concept_selection", {}),
                    "concept_selection_runtime": (
                        runtime_policy.get("concept_selection_runtime")
                        or ((runtime_policy.get("concept_selection", {}) or {}).get("runtime", {}))
                        or {}
                    ),
                    "candidate_policy": runtime_policy.get("candidate_policy", {}),
                    "alternative_policy": runtime_policy.get("alternative_policy", {}),
                    "non_negotiables": [
                        item.get("label", "")
                        for item in (((intent_control or {}).get("maker_intent", {}) or {}).get("constraints", []) or [])
                    ],
                },
            },
            policy={
                "forbid_fields": list(FORBIDDEN_FIELDS),
                "overlay_ban_terms": [],
                "require_try_to_fail": True,
                "intent_control": {
                    "surface_id": (intent_control or {}).get("surface_id", ""),
                    "packet_policy_notes": ((intent_control or {}).get("control", {}) or {}).get("packet_policy_notes", []),
                    "runtime_policy_schema": runtime_policy.get("schema", ""),
                    "concept_selection_mode": (runtime_policy.get("concept_selection", {}) or {}).get("mode", ""),
                    "candidate_policy_mode": (runtime_policy.get("candidate_policy", {}) or {}).get("mode", ""),
                    "alternative_policy_mode": (runtime_policy.get("alternative_policy", {}) or {}).get("mode", ""),
                },
            },
            targets=all_targets,
            alternatives=all_alternatives,
            sims={
                "positive": all_positive_sims,
                "negative": all_negative_sims,
            },
            self_audit={
                "strategy_hash": hashlib.sha256(
                    json.dumps(all_targets, sort_keys=True).encode()
                ).hexdigest(),
                "candidate_count": len(all_targets),
                "alternative_count": len(all_alternatives),
                "operator_ids_used": ["OP_COLD_CORE_EXTRACT"],
                "lane_id": lane_id,
                "lane_stats": {
                    "lane_id": lane_id,
                    "bias_config": effective_bias_config,
                },
                "intent_control": {
                    "surface_id": (intent_control or {}).get("surface_id", ""),
                    "surface_hash": ((intent_control or {}).get("provenance", {}) or {}).get("surface_hash", ""),
                    "source_ids": ((intent_control or {}).get("self_audit", {}) or {}).get("source_ids", []),
                    "focus_terms": runtime_policy.get("focus_terms", []),
                    "runtime_policy": runtime_policy,
                    "effective_runtime_policy": effective_runtime_policy,
                    "concept_selection": runtime_policy.get("concept_selection", {}),
                    "concept_selection_runtime": (
                        runtime_policy.get("concept_selection_runtime")
                        or ((runtime_policy.get("concept_selection", {}) or {}).get("runtime", {}))
                        or {}
                    ),
                    "candidate_policy": runtime_policy.get("candidate_policy", {}),
                    "candidate_policy_runtime": {
                        "concepts_evaluated": len(intent_candidate_policy_reports),
                        "concepts_with_focus": sum(1 for rec in intent_candidate_policy_reports if int(rec.get("concept_focus_score", 0)) > 0),
                        "concepts_suppressed": sum(1 for rec in intent_candidate_policy_reports if rec.get("applied")),
                        "suppressed_term_defs": sum(int(rec.get("suppressed_count", 0)) for rec in intent_candidate_policy_reports),
                        "suppressed_concepts": [
                            rec.get("concept_id", "")
                            for rec in intent_candidate_policy_reports
                            if rec.get("applied")
                        ],
                    },
                    "alternative_policy": runtime_policy.get("alternative_policy", {}),
                    "alternative_policy_runtime": {
                        "primaries_evaluated": len(intent_alternative_policy_reports),
                        "primaries_trimmed": sum(1 for rec in intent_alternative_policy_reports if rec.get("applied")),
                        "alternatives_trimmed": sum(int(rec.get("trimmed_count", 0)) for rec in intent_alternative_policy_reports),
                        "trimmed_primary_ids": [
                            rec.get("primary_candidate_id", "")
                            for rec in intent_alternative_policy_reports
                            if rec.get("applied")
                        ],
                    },
                    "maker_intent_summary": ((intent_control or {}).get("maker_intent", {}) or {}).get("summary", ""),
                    "queue_notes": [
                        item.get("text", "")
                        for item in (((intent_control or {}).get("maker_intent", {}) or {}).get("queue_notes", []) or [])
                    ],
                },
            },
        )

        return packet


def main():
    """Quick test: extract candidates from top kernel concepts."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    from system_v4.skills.a2_graph_refinery import A2GraphRefinery

    repo = str(Path(__file__).resolve().parents[2])
    brain = A1Brain(repo)
    refinery = A2GraphRefinery(repo)
    nodes = refinery.builder.pydantic_model.nodes

    # Find kernel concepts
    kernels = [
        (nid, n) for nid, n in nodes.items()
        if n.trust_zone == "A2_1_KERNEL"
        and n.node_type == "KERNEL_CONCEPT"
    ]

    # Sort by edge count (most connected first)
    edge_counts = {}
    for e in refinery.builder.pydantic_model.edges:
        edge_counts[e.source_id] = edge_counts.get(e.source_id, 0) + 1
        edge_counts[e.target_id] = edge_counts.get(e.target_id, 0) + 1

    kernels.sort(key=lambda x: edge_counts.get(x[0], 0), reverse=True)

    # Pick top 5
    selected = kernels[:5]
    concept_ids = [nid for nid, _ in selected]

    print(f"A1 Brain: {len(brain.term_registry)} terms in registry")
    print(f"L0 lexeme set: {len(L0_LEXEME_SET)} terms")
    print(f"Selected {len(selected)} kernel concepts for extraction:\n")

    for nid, n in selected:
        print(f"  {n.name[:60]:60s} edges={edge_counts.get(nid, 0)}")

    # Build node dict for strategy packet
    graph_dict = {}
    for nid, n in selected:
        graph_dict[nid] = {
            "name": n.name,
            "description": n.description,
            "tags": n.tags,
            "properties": n.properties,
        }

    # Build strategy packet
    packet = brain.build_strategy_packet(concept_ids, graph_dict)

    print(f"\n{'='*60}")
    print(f"A1_STRATEGY_v1 Packet: {packet.strategy_id}")
    print(f"{'='*60}")
    print(f"  Targets:      {len(packet.targets)}")
    print(f"  Alternatives: {len(packet.alternatives)}")
    print(f"  Positive SIMs: {len(packet.sims['positive'])}")
    print(f"  Negative SIMs: {len(packet.sims['negative'])}")

    # Show extraction detail for each target
    for t in packet.targets:
        kind = t["kind"]
        cid = t["id"]
        n_fields = len(t["def_fields"])
        n_asserts = len(t["asserts"])
        n_requires = len(t["requires"])
        print(f"\n  [{cid}] {kind}")
        print(f"    def_fields: {n_fields}, asserts: {n_asserts}, requires: {n_requires}")
        for df in t["def_fields"]:
            vk = df["value_kind"]
            val = df["value"][:60] if len(df["value"]) > 60 else df["value"]
            print(f"    → {df['name']} ({vk}): {val}")

    # Show alternatives
    print(f"\n--- Alternatives (designed to fail) ---")
    for a in packet.alternatives[:6]:
        intent = "TRY_TO_FAIL"
        print(f"  [{a['id']}] {a['kind']} → {intent}")

    # Save state
    brain.save_state()
    print(f"\nBrain state saved to {brain.brain_state_path}")

    # Save packet
    packet_path = Path(repo) / "system_v4" / "a1_state" / "a1_strategy_packets" / f"{packet.strategy_id}.json"
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    with open(packet_path, "w") as f:
        json.dump(packet.to_dict(), f, indent=2)
    print(f"Strategy packet saved to {packet_path}")


if __name__ == "__main__":
    main()
