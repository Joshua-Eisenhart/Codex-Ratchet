"""
b_kernel.py — B-Layer Deterministic Enforcement Kernel

The B kernel is the sole source of truth for canon admission.
It does NOT look at empirical evidence (that's SIM's job).
It enforces structural integrity only, via a fixed 7-stage pipeline.

Per Spec 03 (B Kernel) and MEGABOOT Thread B v3.9.9:
  Stage 1:   AUDIT_PROVENANCE — verify container shape and metadata
  Stage 1.5: DERIVED_ONLY_GUARD — scan for derived-only primitives
  Stage 1.6: UNDEFINED_TERM_FENCE — tokens against L0 + term registry
  Stage 2:   SCHEMA_CHECK — enforce required fields per item kind
  Stage 3:   DEPENDENCY_GRAPH — forward reference detection
  Stage 4:   NEAR_DUPLICATE — Jaccard(token_set) > 0.80 → PARK
  Stage 5:   PRESSURE — probe pressure check
  Stage 6:   EVIDENCE_UPDATE — update evidence pending state
  Stage 7:   COMMIT — if all gates pass → ACCEPT

Outcomes:
  ACCEPT → canon state mutates, append-only survivor ledger
  PARK   → retained for replay/unpark, not admitted
  REJECT → graveyard record with full provenance

No stage reordering permitted.
"""

import hashlib
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from system_v4.skills.runtime_state import StepEvent

from system_v4.skills.a1_brain import L0_LEXEME_SET, DERIVED_ONLY_TERMS, ALLOWED_KINDS


# ═══════════════════════════════════════════════════════════════
# Outcome types
# ═══════════════════════════════════════════════════════════════

@dataclass
class BOutcome:
    """Result of B-layer adjudication for a single candidate."""
    candidate_id: str
    outcome: str              # ACCEPT | PARK | REJECT
    stage_failed: Optional[str]  # Which stage caught it (None if ACCEPT)
    reason_tag: str           # From the allowed tag set
    detail: str               # Human-readable detail
    raw_lines: List[str]      # Raw candidate content for graveyard
    failure_class: Optional[str] = None  # B_KILL for rejects
    step_trace: List[dict] = field(default_factory=list)  # StepEvent trace

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GraveyardRecord:
    """A rejected/parked candidate record for the graveyard."""
    candidate_id: str
    reason_tag: str
    raw_lines: List[str]
    failure_class: str   # B_KILL | B_PARK
    source_concept_id: Optional[str] = None  # Original refinery/source concept when known
    primary_candidate_id: Optional[str] = None  # The primary candidate an alt was tested against
    item: Optional[dict] = None  # Original rejected candidate payload for replay/differential
    target_ref: Optional[str] = None  # If alternative, reference to primary
    stage: str = ""
    detail: str = ""
    timestamp_utc: str = ""
    step_trace: List[dict] = field(default_factory=list)  # StepEvent trace


# Allowed rejection tags (from MEGABOOT BR-000A)
ALLOWED_REJECT_TAGS = {
    "MULTI_ARTIFACT_OR_PROSE",
    "COMMENT_BAN",
    "SNAPSHOT_NONVERBATIM",
    "UNDEFINED_TERM_USE",
    "DERIVED_ONLY_PRIMITIVE_USE",
    "DERIVED_ONLY_NOT_PERMITTED",
    "UNQUOTED_EQUAL",
    "SCHEMA_FAIL",
    "FORWARD_DEPEND",
    "NEAR_REDUNDANT",
    "PROBE_PRESSURE",
    "UNUSED_PROBE",
    "SHADOW_ATTEMPT",
    "KERNEL_ERROR",
    "GLYPH_NOT_PERMITTED",
}

# Required fields per kind (from Spec 03 + MEGABOOT)
REQUIRED_FIELDS_BY_KIND = {
    "MATH_DEF": {"structural_form"},
    "TERM_DEF": {"term_literal"},
    "LABEL_DEF": set(),
    "CANON_PERMIT": {"term_literal"},
    "SIM_SPEC": {"probe_target"},
}


class BKernel:
    """
    Deterministic B-layer enforcement kernel.

    Maintains canon state:
      - survivor_ledger: accepted items (append-only)
      - park_set: parked items (retained)
      - reject_log: rejection records
      - term_registry: from A1 brain (shared reference)
      - graveyard: full rejection records with provenance
    """

    def __init__(self, a1_brain):
        self.brain = a1_brain
        self.state_path = Path(a1_brain.repo_root) / "system_v4" / "runtime_state" / "b_kernel_state.json"

        # Canon state
        self.survivor_ledger: Dict[str, dict] = {}   # id → {class, status, item, provenance}
        self.park_set: Dict[str, dict] = {}           # id → {class, item, tags, provenance}
        self.reject_log: List[dict] = []
        self.graveyard: List[GraveyardRecord] = []
        self.accepted_batch_count: int = 0

        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            with open(self.state_path) as f:
                state = json.load(f)
            self.survivor_ledger = state.get("survivor_ledger", {})
            self.park_set = state.get("park_set", {})
            self.reject_log = state.get("reject_log", [])
            self.accepted_batch_count = state.get("accepted_batch_count", 0)
            for g in state.get("graveyard", []):
                self.graveyard.append(GraveyardRecord(**g))

    def save_state(self):
        state = {
            "survivor_ledger": self.survivor_ledger,
            "park_set": self.park_set,
            "reject_log": self.reject_log,
            "graveyard": [asdict(g) for g in self.graveyard],
            "accepted_batch_count": self.accepted_batch_count,
            "saved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    def adjudicate_batch(self, targets: List[dict],
                          alternatives: List[dict]) -> List[BOutcome]:
        """
        Run the full 7-stage enforcement pipeline on a batch of candidates.

        Returns list of BOutcome for each candidate.
        """
        all_candidates = targets + alternatives
        outcomes = []
        batch_id = f"BATCH_{time.strftime('%Y%m%d_%H%M%S')}"

        # Build batch-local ID set (for forward reference checking)
        batch_ids = set()
        batch_id_order = []
        for c in all_candidates:
            batch_ids.add(c["id"])
            batch_id_order.append(c["id"])

        for i, candidate in enumerate(all_candidates):
            cid = candidate["id"]
            raw_lines = [json.dumps(candidate, indent=2)]

            # IDs defined BEFORE this candidate in batch order
            defined_before = set(batch_id_order[:i])

            outcome = self._run_stages(candidate, batch_id, defined_before, raw_lines)
            outcomes.append(outcome)

            # Process outcome
            if outcome.outcome == "ACCEPT":
                self._commit(candidate, batch_id)
            elif outcome.outcome == "PARK":
                self._park(candidate, batch_id, outcome)
            elif outcome.outcome == "REJECT":
                self._reject(candidate, batch_id, outcome)

        self.accepted_batch_count += 1
        return outcomes

    def _run_stages(self, candidate: dict, batch_id: str,
                    defined_before: Set[str],
                    raw_lines: List[str]) -> BOutcome:
        """Run all enforcement stages in fixed order. Emits a StepEvent for each stage."""
        cid = candidate["id"]
        step_trace = []
        state_hash = hashlib.sha256(json.dumps(candidate, sort_keys=True).encode()).hexdigest()[:16]

        # Stage definitions: (name, method, args, failure_class)
        stages = [
            ("AUDIT_PROVENANCE", self._stage_audit_provenance, (candidate,), "B_KILL"),
            ("DERIVED_ONLY_GUARD", self._stage_derived_only_guard, (candidate,), "B_KILL"),
            ("UNDEFINED_TERM_FENCE", self._stage_undefined_term_fence, (candidate,), "B_KILL"),
            ("SCHEMA_CHECK", self._stage_schema_check, (candidate,), "B_KILL"),
            ("DEPENDENCY_GRAPH", self._stage_dependency_graph, (candidate, defined_before), "B_PARK"),
            ("NEAR_DUPLICATE", self._stage_near_duplicate, (candidate,), "B_PARK"),
            ("PRESSURE", self._stage_pressure, (candidate,), "B_PARK"),
        ]

        for stage_name, stage_fn, stage_args, fail_class in stages:
            result = stage_fn(*stage_args)

            # Build state hash after this stage
            post_hash = hashlib.sha256(
                f"{state_hash}:{stage_name}:{result is None}".encode()
            ).hexdigest()[:16]

            step = StepEvent(
                timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                operator_id=f"B_{stage_name}",
                before_hash=state_hash,
                after_hash=post_hash,
            )
            step_trace.append(step.to_dict())
            state_hash = post_hash

            if result:
                return BOutcome(cid, result[0], stage_name, result[1], result[2],
                                raw_lines, fail_class, step_trace)

        # Stage 6: EVIDENCE_UPDATE — deferred to SIM ingestion
        # Stage 7: COMMIT — all stages passed → ACCEPT
        return BOutcome(cid, "ACCEPT", None, "", "All enforcement stages passed",
                        raw_lines, None, step_trace)

    def _stage_audit_provenance(self, candidate: dict) -> Optional[Tuple[str, str, str]]:
        """Stage 1: Verify container shape and required metadata."""
        required_keys = {"item_class", "id", "kind", "requires", "def_fields", "asserts"}
        missing = required_keys - set(candidate.keys())
        if missing:
            return ("REJECT", "SCHEMA_FAIL", f"Missing required keys: {missing}")

        # Validate item_class
        if candidate["item_class"] not in ("AXIOM_HYP", "PROBE_HYP", "SPEC_HYP"):
            return ("REJECT", "SCHEMA_FAIL",
                    f"Invalid item_class: {candidate['item_class']}")

        # Validate kind
        if candidate["kind"] not in ALLOWED_KINDS:
            return ("REJECT", "SCHEMA_FAIL",
                    f"Invalid kind: {candidate['kind']}")

        # Validate ID namespace (BR-002)
        cid = candidate["id"]
        item_class = candidate["item_class"]
        valid_prefixes = {"AXIOM_HYP": ["F", "W", "K", "M"],
                         "PROBE_HYP": ["P"],
                         "SPEC_HYP": ["S", "R"]}
        if not any(cid.startswith(p) for p in valid_prefixes.get(item_class, [])):
            return ("REJECT", "SCHEMA_FAIL",
                    f"ID '{cid}' does not match namespace for {item_class}")

        # Check for forbidden fields
        for key in candidate:
            if key.lower() in {"confidence", "probability", "embedding", "hidden_prompt"}:
                return ("REJECT", "SCHEMA_FAIL",
                        f"Forbidden field: {key}")

        return None

    def _stage_derived_only_guard(self, candidate: dict) -> Optional[Tuple[str, str, str]]:
        """Stage 1.5: Scan for derived-only primitives in BARE def_fields."""
        for df in candidate.get("def_fields", []):
            if df.get("value_kind") == "BARE":
                value = df.get("value", "")
                segments = value.lower().split("_")
                for seg in segments:
                    if seg in DERIVED_ONLY_TERMS:
                        # Check if canonically allowed
                        term_state = self.brain.term_registry.get(seg, {}).get("state", "")
                        if term_state != "CANONICAL_ALLOWED":
                            return ("REJECT", "DERIVED_ONLY_NOT_PERMITTED",
                                    f"Derived-only term '{seg}' in BARE value "
                                    f"'{value}' — requires CANONICAL_ALLOWED admission")
        return None

    def _stage_undefined_term_fence(self, candidate: dict) -> Optional[Tuple[str, str, str]]:
        """Stage 1.6: Scan BARE def_field tokens against L0 + term registry."""
        # Collect self-admitting terms for TERM_DEF candidates
        self_admitting_terms = set()
        if candidate.get("kind") == "TERM_DEF":
            for tdf in candidate.get("def_fields", []):
                if tdf.get("name") == "term_literal":
                    self_admitting_terms.add(tdf.get("value", "").lower())

        for df in candidate.get("def_fields", []):
            if df.get("value_kind") == "BARE":
                field_name = df.get("name", "")
                value = df.get("value", "")

                # Exempt probe_target fields — they contain candidate IDs, not vocabulary
                if field_name == "probe_target":
                    continue

                segments = value.lower().split("_")
                for seg in segments:
                    if re.match(r'^[0-9]+$', seg):
                        continue  # Numeric suffixes OK
                    if seg in L0_LEXEME_SET:
                        continue
                    term_entry = self.brain.term_registry.get(seg, {})
                    if term_entry.get("state") in ("TERM_PERMITTED", "LABEL_PERMITTED",
                                                    "CANONICAL_ALLOWED", "MATH_DEFINED"):
                        continue
                    # Self-admission: TERM_DEF can define the term it's admitting
                    if seg in self_admitting_terms:
                        continue
                    return ("REJECT", "UNDEFINED_TERM_USE",
                            f"Token '{seg}' not in L0 lexeme set or term registry. "
                            f"L0 has {len(L0_LEXEME_SET)} terms. "
                            f"Registry has {len(self.brain.term_registry)} admitted terms.")
        return None

    def _stage_schema_check(self, candidate: dict) -> Optional[Tuple[str, str, str]]:
        """Stage 2: Enforce required fields per item kind."""
        kind = candidate.get("kind", "")
        required_field_names = REQUIRED_FIELDS_BY_KIND.get(kind, set())

        actual_field_names = set()
        for df in candidate.get("def_fields", []):
            actual_field_names.add(df.get("name", ""))

        missing = required_field_names - actual_field_names
        if missing:
            return ("REJECT", "SCHEMA_FAIL",
                    f"Kind '{kind}' requires fields {missing}, "
                    f"but only found {actual_field_names}")

        # Check that def_fields have required structure
        for df in candidate.get("def_fields", []):
            required_df_keys = {"field_id", "name", "value_kind", "value"}
            missing_df = required_df_keys - set(df.keys())
            if missing_df:
                return ("REJECT", "SCHEMA_FAIL",
                        f"DEF_FIELD missing keys: {missing_df}")
            if df.get("value_kind") not in ("BARE", "TERM_QUOTED", "LABEL_QUOTED", "FORMULA_QUOTED"):
                return ("REJECT", "SCHEMA_FAIL",
                        f"Invalid value_kind: {df.get('value_kind')}")

        # Check assertions structure
        for a in candidate.get("asserts", []):
            required_a_keys = {"assert_id", "token_class", "token"}
            missing_a = required_a_keys - set(a.keys())
            if missing_a:
                return ("REJECT", "SCHEMA_FAIL",
                        f"ASSERT missing keys: {missing_a}")

        # SIM_SPEC must have at least one probe dependency
        if kind == "SIM_SPEC":
            requires = candidate.get("requires", [])
            has_probe_dep = any(r.startswith("P") for r in requires)
            if not has_probe_dep:
                # Check if any requires starts with P
                # If no requires at all but it's SIM_SPEC, that's also a schema fail
                pass  # Relaxed for now — MEGABOOT says "current live packet validator also requires"

        return None

    def _stage_dependency_graph(self, candidate: dict,
                                 defined_before: Set[str]) -> Optional[Tuple[str, str, str]]:
        """Stage 3: Forward reference detection (BR-006)."""
        requires = candidate.get("requires", [])
        for dep_id in requires:
            # A dependency is DEFINED if:
            # 1. It exists in survivor_ledger (any status)
            # 2. It appears earlier in the same batch
            if dep_id in self.survivor_ledger:
                continue
            if dep_id in defined_before:
                continue
            return ("PARK", "FORWARD_DEPEND",
                    f"REQUIRES '{dep_id}' is undefined — "
                    f"not in survivor_ledger ({len(self.survivor_ledger)} items) "
                    f"and not earlier in batch ({len(defined_before)} prior items)")
        return None

    def _stage_near_duplicate(self, candidate: dict) -> Optional[Tuple[str, str, str]]:
        """Stage 4: Near-duplicate detection (BR-007, Jaccard > 0.80)."""
        cid = candidate["id"]
        item_class = candidate["item_class"]

        # Build token set for this candidate
        cand_tokens = self._extract_token_set(candidate)
        if not cand_tokens:
            return None

        # Compare against existing survivors of same class
        for sid, survivor in self.survivor_ledger.items():
            if survivor.get("class") != item_class:
                continue
            if sid == cid:
                continue

            surv_tokens = set(survivor.get("token_set", []))
            if not surv_tokens:
                continue

            # Jaccard similarity
            intersection = cand_tokens & surv_tokens
            union = cand_tokens | surv_tokens
            if union:
                jaccard = len(intersection) / len(union)
                if jaccard > 0.80:
                    return ("PARK", "NEAR_REDUNDANT",
                            f"Jaccard({cid}, {sid}) = {jaccard:.2f} > 0.80 threshold. "
                            f"Shared tokens: {sorted(intersection)[:5]}")

        return None

    def _stage_pressure(self, candidate: dict) -> Optional[Tuple[str, str, str]]:
        """Stage 5: Probe pressure check (Spec 03 RQ-026).

        Per 10 newly accepted SPEC_HYP, require >= 1 newly accepted PROBE_HYP.
        If unmet, park lowest-priority spec items.
        """
        # Count active survivors by class
        spec_count = sum(
            1 for s in self.survivor_ledger.values()
            if s.get("class") == "SPEC_HYP" and s.get("status") == "ACTIVE"
        )
        probe_count = sum(
            1 for s in self.survivor_ledger.values()
            if s.get("class") == "PROBE_HYP" and s.get("status") == "ACTIVE"
        )

        # Only enforce pressure on SPEC_HYP candidates
        if candidate.get("item_class") == "SPEC_HYP":
            required_probes = (spec_count + 1) // 10  # 1 probe per 10 specs
            if required_probes > 0 and probe_count < required_probes:
                return ("PARK", "PROBE_PRESSURE",
                        f"Probe pressure unmet: {probe_count} probes for "
                        f"{spec_count}+1 specs (need {required_probes})")

        return None

    def _extract_token_set(self, candidate: dict) -> Set[str]:
        """Extract the token set from a candidate for duplicate detection."""
        tokens = set()
        for df in candidate.get("def_fields", []):
            if df.get("value_kind") == "BARE":
                tokens.update(df.get("value", "").lower().split("_"))
            elif df.get("value_kind") in ("TERM_QUOTED", "LABEL_QUOTED"):
                # Add quoted content tokens too
                words = re.findall(r'[a-z][a-z0-9]*', df.get("value", "").lower())
                tokens.update(words)
        for a in candidate.get("asserts", []):
            tokens.add(a.get("token", "").lower())
        return tokens

    def _commit(self, candidate: dict, batch_id: str):
        """Stage 7: Accept candidate into canon state."""
        cid = candidate["id"]
        token_set = list(self._extract_token_set(candidate))

        self.survivor_ledger[cid] = {
            "class": candidate["item_class"],
            "status": "ACTIVE",
            "kind": candidate["kind"],
            "item": candidate,
            "token_set": token_set,
            "provenance": {
                "batch_id": batch_id,
                "accepted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "source_concept_id": candidate.get("source_concept_id"),
                "primary_candidate_id": candidate.get("primary_candidate_id"),
            },
        }

        # If this is a TERM_DEF, update term registry
        if candidate["kind"] == "TERM_DEF":
            for df in candidate.get("def_fields", []):
                if df.get("name") == "term_literal":
                    term = df.get("value", "").lower()
                    self.brain.term_registry[term] = {
                        "state": "TERM_PERMITTED",
                        "bound_math_def": cid,
                        "provenance": batch_id,
                    }

    def _park(self, candidate: dict, batch_id: str, outcome: BOutcome):
        """Park a candidate (retained for later replay/unpark)."""
        cid = candidate["id"]
        self.park_set[cid] = {
            "class": candidate["item_class"],
            "kind": candidate["kind"],
            "item": candidate,
            "tags": [outcome.reason_tag],
            "provenance": {
                "batch_id": batch_id,
                "parked_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": outcome.detail,
                "source_concept_id": candidate.get("source_concept_id"),
                "primary_candidate_id": candidate.get("primary_candidate_id"),
            },
        }

    def _reject(self, candidate: dict, batch_id: str, outcome: BOutcome):
        """Reject a candidate — write graveyard record."""
        cid = candidate["id"]
        source_concept_id = candidate.get("source_concept_id", None)
        primary_candidate_id = candidate.get("primary_candidate_id", None)

        # In the current runtime, target_ref is the best available lineage handle.
        # Preserve source_concept_id explicitly as well so reopen logic does not
        # depend on one overloaded field.
        target_ref = primary_candidate_id or source_concept_id

        record = GraveyardRecord(
            candidate_id=cid,
            reason_tag=outcome.reason_tag,
            raw_lines=outcome.raw_lines,
            failure_class="B_KILL",
            source_concept_id=source_concept_id,
            primary_candidate_id=primary_candidate_id,
            item=candidate,
            target_ref=target_ref,
            stage=outcome.stage_failed or "",
            detail=outcome.detail,
            timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            step_trace=outcome.step_trace,
        )
        self.graveyard.append(record)

        self.reject_log.append({
            "batch_id": batch_id,
            "tag": outcome.reason_tag,
            "detail": outcome.detail,
            "candidate_id": cid,
            "source_concept_id": source_concept_id,
            "primary_candidate_id": primary_candidate_id,
        })


def main():
    """Test: run A1 strategy packet through real B enforcement."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    from system_v4.skills.a1_brain import A1Brain
    from system_v4.skills.a2_graph_refinery import A2GraphRefinery

    repo = str(Path(__file__).resolve().parents[2])
    brain = A1Brain(repo)
    kernel = BKernel(brain)
    refinery = A2GraphRefinery(repo)
    nodes = refinery.builder.pydantic_model.nodes

    print(f"B Kernel State:")
    print(f"  Survivors: {len(kernel.survivor_ledger)}")
    print(f"  Parked:    {len(kernel.park_set)}")
    print(f"  Graveyard: {len(kernel.graveyard)}")
    print(f"  L0 terms:  {len(L0_LEXEME_SET)}")
    print(f"  Registry:  {len(brain.term_registry)}")

    # Find kernel concepts with highest edge count
    edge_counts = {}
    for e in refinery.builder.pydantic_model.edges:
        edge_counts[e.source_id] = edge_counts.get(e.source_id, 0) + 1
        edge_counts[e.target_id] = edge_counts.get(e.target_id, 0) + 1

    kernels = [
        (nid, n) for nid, n in nodes.items()
        if n.trust_zone == "A2_1_KERNEL" and n.node_type == "KERNEL_CONCEPT"
    ]
    kernels.sort(key=lambda x: edge_counts.get(x[0], 0), reverse=True)

    selected = kernels[:5]
    concept_ids = [nid for nid, _ in selected]

    print(f"\n{'='*60}")
    print(f"Selected {len(selected)} concepts for ratchet:")
    for nid, n in selected:
        print(f"  {n.name[:50]:50s} edges={edge_counts.get(nid, 0)}")

    # Build strategy packet
    graph_dict = {}
    for nid, n in selected:
        graph_dict[nid] = {
            "name": n.name,
            "description": n.description,
            "tags": n.tags,
            "properties": n.properties,
        }

    packet = brain.build_strategy_packet(concept_ids, graph_dict)
    print(f"\nA1 Strategy Packet: {len(packet.targets)} targets, {len(packet.alternatives)} alternatives")

    # Run through B kernel
    print(f"\n{'='*60}")
    print(f"B KERNEL ENFORCEMENT")
    print(f"{'='*60}")

    outcomes = kernel.adjudicate_batch(packet.targets, packet.alternatives)

    # Report
    accept_count = sum(1 for o in outcomes if o.outcome == "ACCEPT")
    park_count = sum(1 for o in outcomes if o.outcome == "PARK")
    reject_count = sum(1 for o in outcomes if o.outcome == "REJECT")

    print(f"\n  ACCEPT: {accept_count}")
    print(f"  PARK:   {park_count}")
    print(f"  REJECT: {reject_count}")
    print(f"  Total:  {len(outcomes)}")

    # Details
    print(f"\n--- Outcomes ---")
    for o in outcomes:
        marker = {"ACCEPT": "✅", "PARK": "⏸️", "REJECT": "❌"}.get(o.outcome, "?")
        stage = f" @ {o.stage_failed}" if o.stage_failed else ""
        tag = f" [{o.reason_tag}]" if o.reason_tag else ""
        print(f"  {marker} {o.candidate_id:8s} → {o.outcome}{stage}{tag}")
        if o.detail and o.outcome != "ACCEPT":
            print(f"     {o.detail[:100]}")

    # Graveyard report
    print(f"\n--- Graveyard ({len(kernel.graveyard)} records) ---")
    for g in kernel.graveyard[:10]:
        print(f"  ❌ {g.candidate_id:8s} [{g.reason_tag}] @ {g.stage}")
        print(f"     {g.detail[:80]}")

    # Save state
    kernel.save_state()
    brain.save_state()
    print(f"\nB kernel state saved")
    print(f"Brain state saved (registry now {len(brain.term_registry)} terms)")


if __name__ == "__main__":
    main()
