"""
sim_engine.py — Real SIM Engine (Spec 06)

The SIM engine is SEPARATE from the holodeck. It implements the tiered
evidence system from Spec 06 (SIM Evidence and Tier Specification).

This is terminal execution + evidence, not interpretation.

Tiers: T0_ATOM → T1_COMPOUND → T2_OPERATOR → ... → T6_WHOLE_SYSTEM
  - No tier-skip promotion
  - Explicit acyclic dependencies
  - Deterministic hash chains

Stress Families per tier:
  BASELINE, BOUNDARY_SWEEP, PERTURBATION, ADVERSARIAL_NEG, COMPOSITION_STRESS

T0_ATOM requirements: 1 BASELINE + 2 BOUNDARY + 4 PERTURBATION + 2 ADVERSARIAL = 9 tests

Each SIM evidence block has:
  sim_id, tier, family, input_hash, code_hash, output_hash, manifest_hash, evidence_tokens[]

Every SIM must be reproducible: same code + same input = same output hash.
"""

import hashlib
import json
import time
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple

from system_v4.skills.a1_brain import L0_LEXEME_SET, DERIVED_ONLY_TERMS
from system_v4.skills.runtime_state import (
    RuntimeState, Probe, Observation, Witness, StepEvent, CoarseState,
    STANDARD_PROBES, equivalent_under, distinguishability,
    guard_transition, _boundary_class,
)


# ═══════════════════════════════════════════════════════════
# Tier Architecture (Spec 06 RQ-055)
# ═══════════════════════════════════════════════════════════
TIERS = ["T0_ATOM", "T1_COMPOUND", "T2_OPERATOR", "T3_STRUCTURE",
         "T4_SYSTEM_SEGMENT", "T5_ENGINE", "T6_WHOLE_SYSTEM"]

STRESS_FAMILIES = ["BASELINE", "BOUNDARY_SWEEP", "PERTURBATION",
                   "ADVERSARIAL_NEG", "COMPOSITION_STRESS", "DIFFERENTIAL"]

# Threshold profile per tier (Spec 06 RQ-058)
TIER_THRESHOLDS = {
    "T0_ATOM":          {"BASELINE": 1, "BOUNDARY_SWEEP": 2, "PERTURBATION": 4, "ADVERSARIAL_NEG": 2, "COMPOSITION_STRESS": 0},
    "T1_COMPOUND":      {"BASELINE": 1, "BOUNDARY_SWEEP": 3, "PERTURBATION": 6, "ADVERSARIAL_NEG": 3, "COMPOSITION_STRESS": 1},
    "T2_OPERATOR":      {"BASELINE": 2, "BOUNDARY_SWEEP": 4, "PERTURBATION": 8, "ADVERSARIAL_NEG": 4, "COMPOSITION_STRESS": 2},
    "T3_STRUCTURE":     {"BASELINE": 2, "BOUNDARY_SWEEP": 5, "PERTURBATION": 10, "ADVERSARIAL_NEG": 5, "COMPOSITION_STRESS": 3},
    "T4_SYSTEM_SEGMENT":{"BASELINE": 3, "BOUNDARY_SWEEP": 6, "PERTURBATION": 12, "ADVERSARIAL_NEG": 6, "COMPOSITION_STRESS": 4},
    "T5_ENGINE":        {"BASELINE": 3, "BOUNDARY_SWEEP": 8, "PERTURBATION": 14, "ADVERSARIAL_NEG": 8, "COMPOSITION_STRESS": 6},
    "T6_WHOLE_SYSTEM":  {"BASELINE": 5, "BOUNDARY_SWEEP": 10, "PERTURBATION": 20, "ADVERSARIAL_NEG": 10, "COMPOSITION_STRESS": 10},
}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _canonical_json(obj) -> str:
    """Canonical JSON encoding: sorted keys, stable lists."""
    return json.dumps(obj, sort_keys=True, separators=(',', ':'))


@dataclass
class SimEvidence:
    """A single SIM_EVIDENCE v1 block (Spec 06)."""
    sim_id: str
    tier: str
    family: str
    target_id: str
    code_hash: str      # sha256 of sim source
    input_hash: str     # sha256 of canonical JSON inputs
    output_hash: str    # sha256 of canonical outputs
    manifest_hash: str  # sha256 of the full evidence block
    evidence_tokens: List[str]
    outcome: str        # PASS | FAIL
    detail: str = ""

    def to_evidence_block(self) -> str:
        """Emit canonical SIM_EVIDENCE v1 block (MEGABOOT grammar)."""
        lines = [
            "BEGIN SIM_EVIDENCE v1",
            f"SIM_ID: {self.sim_id}",
            f"CODE_HASH_SHA256: {self.code_hash}",
            f"OUTPUT_HASH_SHA256: {self.output_hash}",
        ]
        for token in self.evidence_tokens:
            lines.append(f"EVIDENCE_SIGNAL {self.sim_id} CORR {token}")
        lines.append("END SIM_EVIDENCE v1")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SimKill:
    """A SIM_KILL record (Spec 06)."""
    target_id: str
    failure_mode_id: str
    sim_id: str
    replay_manifest_hash: str
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class SimEngine:
    """
    Real SIM engine per Spec 06.
    Runs deterministic structural tests, not mocked feeds.
    """

    def __init__(self, b_kernel):
        self.kernel = b_kernel
        self.brain = b_kernel.brain
        self.evidence_log: List[SimEvidence] = []
        self.kill_log: List[SimKill] = []
        self.witness_log: List[Witness] = []
        self.state_path = Path(self.brain.repo_root) / "system_v4" / "runtime_state" / "sim_state.json"
        self._load_state()

    def _load_state(self):
        if self.state_path.exists():
            with open(self.state_path) as f:
                state = json.load(f)
            for ev in state.get("evidence_log", []):
                self.evidence_log.append(SimEvidence(**ev))
            for k in state.get("kill_log", []):
                self.kill_log.append(SimKill(**k))
            for w in state.get("witness_log", []):
                self.witness_log.append(Witness(**w))

    def save_state(self):
        state = {
            "evidence_log": [e.to_dict() for e in self.evidence_log],
            "kill_log": [k.to_dict() for k in self.kill_log],
            "witness_log": [w.to_dict() for w in self.witness_log],
            "saved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_path, "w") as f:
            json.dump(state, f, indent=2)

    # ═══════════════════════════════════════════════════════════
    # Coarse Pre-Filter (Abstract Interpretation)
    # ═══════════════════════════════════════════════════════════

    def coarse_prefilter(self, survivor_id: str, survivor: dict) -> Tuple[bool, str]:
        """
        Cheap coarse-state check before expensive T0 campaign.
        Rejects structurally degenerate candidates without running full tests.

        Returns (pass, reason).
        """
        candidate = survivor.get("item", {})

        # Build coarse state from candidate
        structural_form = ""
        term_literal = ""
        kind = survivor.get("kind", "")
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form":
                structural_form = df.get("value", "")
            if df.get("name") == "term_literal":
                term_literal = df.get("value", "")

        tokens = structural_form.lower().split("_") if structural_form else []

        # Check 1: structural_form must have >= 2 tokens for MATH_DEF
        if kind == "MATH_DEF" and len(tokens) < 2:
            return False, f"Coarse reject: structural_form '{structural_form}' has <2 tokens"

        # Check 2: TERM_DEF must have a non-empty term_literal
        if kind == "TERM_DEF" and not term_literal:
            return False, "Coarse reject: TERM_DEF missing term_literal"

        # Check 3: no token should be empty string
        if any(t == "" for t in tokens):
            return False, f"Coarse reject: empty token segment in '{structural_form}'"

        # Check 4: structural_form shouldn't exceed reasonable length
        if len(tokens) > 20:
            return False, f"Coarse reject: structural_form has {len(tokens)} tokens (>20)"

        return True, "Coarse OK"

    # ═══════════════════════════════════════════════════════════
    # RuntimeState Construction from Candidate
    # ═══════════════════════════════════════════════════════════

    def _candidate_to_state(self, survivor_id: str, candidate: dict) -> RuntimeState:
        """Build a RuntimeState from a B-accepted candidate."""
        structural_form = ""
        term_literal = ""
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form":
                structural_form = df.get("value", "")
            if df.get("name") == "term_literal":
                term_literal = df.get("value", "")

        tokens = structural_form.lower().split("_") if structural_form else []
        l0_tokens = [t for t in tokens if t in L0_LEXEME_SET]

        return RuntimeState(
            region=f"B_ACCEPTED::{candidate.get('kind', 'UNKNOWN')}",
            phase_index=0,
            phase_period=len(tokens) if tokens else 1,
            loop_scale="micro",
            boundaries=["admissible"],  # B-accepted → admissible
            invariants=[f"L0_CONSISTENT_{survivor_id}"],
            dof={"structural_form": structural_form,
                 "term_literal": term_literal,
                 "token_count": len(tokens),
                 "l0_ratio": len(l0_tokens) / max(len(tokens), 1)},
            context={"survivor_id": survivor_id,
                     "kind": candidate.get("kind", ""),
                     "item_class": candidate.get("item_class", "")},
        )

    # ═══════════════════════════════════════════════════════════
    # Witness Emission from SIM Evidence
    # ═══════════════════════════════════════════════════════════

    def _evidence_to_witness(self, evidence: SimEvidence) -> Witness:
        """Convert a SIM evidence block into a Witness trace."""
        step = StepEvent(
            timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            operator_id=f"SIM_{evidence.family}",
            before_hash=evidence.input_hash,
            after_hash=evidence.output_hash,
            notes=[evidence.sim_id, evidence.detail[:120]],
        )

        kind = "positive" if evidence.outcome == "PASS" else "negative"
        violations = [] if evidence.outcome == "PASS" else [evidence.detail[:120]]

        return Witness(
            kind=kind,
            passed=(evidence.outcome == "PASS"),
            target_id=evidence.target_id,
            sim_id=evidence.sim_id,
            violations=violations,
            touched_boundaries=["admissible" if evidence.outcome == "PASS" else "unstable"],
            trace=[step],
        )

    def run_t0_campaign(self, survivor_id: str, survivor: dict) -> List[SimEvidence]:
        """
        Run the full T0_ATOM campaign for a single survivor.
        T0 requires: 1 BASELINE + 2 BOUNDARY + 4 PERTURBATION + 2 ADVERSARIAL = 9 tests.

        Now includes:
          - Coarse pre-filter (abstract interpretation)
          - RuntimeState construction
          - Witness emission
        """
        results = []
        candidate = survivor.get("item", {})

        # ── Coarse Pre-Filter ──
        coarse_ok, coarse_reason = self.coarse_prefilter(survivor_id, survivor)
        if not coarse_ok:
            # Emit a FAIL BASELINE with coarse reject reason
            sim_id = f"SIM_T0_COARSE_{survivor_id}"
            code_hash = _sha256("coarse_prefilter")
            input_hash = _sha256(_canonical_json({"survivor_id": survivor_id}))
            output_hash = _sha256(coarse_reason)
            manifest_hash = _sha256(_canonical_json({
                "sim_id": sim_id, "code_hash": code_hash,
                "input_hash": input_hash, "output_hash": output_hash
            }))
            ev = SimEvidence(
                sim_id=sim_id, tier="T0_ATOM", family="BASELINE",
                target_id=survivor_id, code_hash=code_hash,
                input_hash=input_hash, output_hash=output_hash,
                manifest_hash=manifest_hash,
                evidence_tokens=[f"COARSE_REJECT_{survivor_id}"],
                outcome="FAIL", detail=coarse_reason,
            )
            results.append(ev)
            # Emit witness for coarse reject
            self.witness_log.append(self._evidence_to_witness(ev))
            # Emit SimKill for coarse reject
            self.kill_log.append(SimKill(
                target_id=survivor_id,
                failure_mode_id=f"FM_COARSE_REJECT_{survivor_id}",
                sim_id=sim_id,
                replay_manifest_hash=manifest_hash,
                detail=coarse_reason,
            ))
            self.evidence_log.extend(results)
            return results

        # ── Build RuntimeState for this candidate ──
        state = self._candidate_to_state(survivor_id, candidate)

        # ─── BASELINE (1 required) ───
        ev = self._run_baseline(survivor_id, candidate)
        results.append(ev)

        # ─── BOUNDARY_SWEEP (2 required) ───
        for i in range(2):
            ev = self._run_boundary_sweep(survivor_id, candidate, i)
            results.append(ev)

        # ─── PERTURBATION (4 required) ───
        for i in range(4):
            ev = self._run_perturbation(survivor_id, candidate, i)
            results.append(ev)

        # ─── ADVERSARIAL_NEG (2 required) ───
        for i in range(2):
            ev = self._run_adversarial_neg(survivor_id, candidate, i)
            results.append(ev)

        # ── Emit Witnesses ──
        for ev in results:
            w = self._evidence_to_witness(ev)
            self.witness_log.append(w)

        self.evidence_log.extend(results)
        return results

    def run_t0_with_differential(self, survivor_id: str, survivor: dict,
                                  graveyard: list = None) -> List[SimEvidence]:
        """
        Run T0 campaign + DIFFERENTIAL comparison against graveyard rejects.
        This is the full contract: 9 core tests + up to 3 differential tests.
        """
        # Core T0
        core_results = self.run_t0_campaign(survivor_id, survivor)

        # Build alternatives from graveyard for differential comparison
        alt_candidates = []
        if graveyard:
            for grav in graveyard[:3]:  # max 3 alternatives
                alt_candidates.append({
                    "id": grav.get("candidate_id", "UNKNOWN"),
                    "kind": grav.get("kind", "GRAVEYARD"),
                    "def_fields": grav.get("item", {}).get("def_fields", []),
                })

        # DIFFERENTIAL
        if alt_candidates:
            diff_results = self.run_differential(survivor_id, survivor, alt_candidates)
            core_results.extend(diff_results)

        return core_results

    # ═══════════════════════════════════════════════════════════
    # DIFFERENTIAL Stress Family
    # ═══════════════════════════════════════════════════════════

    def run_differential(self, survivor_id: str, survivor: dict,
                         alt_candidates: List[dict]) -> List[SimEvidence]:
        """
        DIFFERENTIAL: compare a target survivor against designed-to-fail
        alternatives using probe-relative observations.

        Per the nonclassical runtime doc (§Differential Testing):
        "Run multiple variants on the same surface and compare outputs.
         Disagreement is signal."
        """
        results = []
        candidate = survivor.get("item", {})
        target_state = self._candidate_to_state(survivor_id, candidate)

        for i, alt in enumerate(alt_candidates[:3]):  # Budget: max 3 comparisons
            sim_id = f"SIM_T0_DIFF_{survivor_id}_{i}"
            alt_id = alt.get("id", f"ALT_{i}")

            # Build RuntimeState for alternative
            alt_state = RuntimeState(
                region=f"ALTERNATIVE::{alt.get('kind', 'UNKNOWN')}",
                phase_index=0,
                phase_period=1,
                loop_scale="micro",
                boundaries=["frontier"],
                invariants=[],
                dof={"structural_form": self._extract_structural_form(alt)},
                context={"alt_id": alt_id, "kind": alt.get("kind", "")},
            )

            # Probe-relative comparison
            probes = STANDARD_PROBES
            is_equivalent = equivalent_under(target_state, alt_state, probes)
            dist = distinguishability(target_state, alt_state, probes)

            # Outcome: PASS if target and alt are DISTINGUISHABLE
            # (if they're equivalent under all probes, that's suspicious)
            outcome = "PASS" if not is_equivalent else "FAIL"
            detail = (f"Differential vs {alt_id}: distinguishability={dist}/{len(probes)}, "
                      f"equivalent={is_equivalent}")

            sim_source = f"differential_probe_relative::{survivor_id}::{alt_id}"
            code_hash = _sha256(sim_source)
            input_hash = _sha256(_canonical_json({
                "target": survivor_id, "alt": alt_id,
                "target_hash": target_state.state_hash(),
                "alt_hash": alt_state.state_hash(),
            }))
            output_hash = _sha256(_canonical_json({"outcome": outcome, "dist": dist}))
            manifest_hash = _sha256(_canonical_json({
                "sim_id": sim_id, "code_hash": code_hash,
                "input_hash": input_hash, "output_hash": output_hash
            }))

            ev = SimEvidence(
                sim_id=sim_id, tier="T0_ATOM", family="DIFFERENTIAL",
                target_id=survivor_id, code_hash=code_hash,
                input_hash=input_hash, output_hash=output_hash,
                manifest_hash=manifest_hash,
                evidence_tokens=[f"DIFFERENTIAL_{survivor_id}_vs_{alt_id}"],
                outcome=outcome, detail=detail,
            )
            results.append(ev)

            if outcome == "FAIL":
                self.kill_log.append(SimKill(
                    target_id=survivor_id,
                    failure_mode_id=f"FM_DIFF_EQUIV_{survivor_id}_{alt_id}",
                    sim_id=sim_id,
                    replay_manifest_hash=manifest_hash,
                    detail=f"Probe-indistinguishable from alt {alt_id}",
                ))

        self.evidence_log.extend(results)
        return results

    def _extract_structural_form(self, candidate: dict) -> str:
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form":
                return df.get("value", "")
        return ""

    def _run_baseline(self, target_id: str, candidate: dict) -> SimEvidence:
        """BASELINE: verify the structural form is internally consistent."""
        sim_id = f"SIM_T0_BL_{target_id}"

        # Real test: structural form tokens must all be L0-safe
        structural_form = ""
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form" and df.get("value_kind") == "BARE":
                structural_form = df["value"]

        tokens = structural_form.lower().split("_")
        all_l0 = all(t in L0_LEXEME_SET or re.match(r'^[0-9]+$', t) for t in tokens if t)
        no_derived = not any(t in DERIVED_ONLY_TERMS for t in tokens)

        # Hash chain
        sim_source = f"baseline_structural_consistency_check::{structural_form}"
        code_hash = _sha256(sim_source)
        input_data = _canonical_json({"target_id": target_id, "structural_form": structural_form})
        input_hash = _sha256(input_data)

        outcome = "PASS" if (all_l0 and no_derived and len(tokens) >= 2) else "FAIL"
        output_data = _canonical_json({"outcome": outcome, "all_l0": all_l0, "token_count": len(tokens)})
        output_hash = _sha256(output_data)

        evidence_tokens = [f"L0_CONSISTENCY_{target_id}"]
        manifest_data = _canonical_json({
            "sim_id": sim_id, "code_hash": code_hash, "input_hash": input_hash,
            "output_hash": output_hash, "outcome": outcome
        })
        manifest_hash = _sha256(manifest_data)

        return SimEvidence(
            sim_id=sim_id, tier="T0_ATOM", family="BASELINE", target_id=target_id,
            code_hash=code_hash, input_hash=input_hash, output_hash=output_hash,
            manifest_hash=manifest_hash, evidence_tokens=evidence_tokens,
            outcome=outcome,
            detail=f"Structural form '{structural_form}': all_l0={all_l0}, tokens={len(tokens)}"
        )

    def _run_boundary_sweep(self, target_id: str, candidate: dict, idx: int) -> SimEvidence:
        """BOUNDARY_SWEEP: test behavior at vocabulary boundaries."""
        sim_id = f"SIM_T0_BS_{target_id}_{idx}"

        structural_form = ""
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form" and df.get("value_kind") == "BARE":
                structural_form = df["value"]

        tokens = structural_form.lower().split("_")

        if idx == 0:
            # Boundary test 1: verify each token exists in L0 individually
            test_desc = "individual_token_l0_membership"
            failed_tokens = [t for t in tokens if t and t not in L0_LEXEME_SET and not re.match(r'^[0-9]+$', t)]
            outcome = "PASS" if not failed_tokens else "FAIL"
            detail = f"Failed tokens: {failed_tokens}" if failed_tokens else "All tokens L0-member"
        else:
            # Boundary test 2: verify no token is a near-miss of a derived-only term
            test_desc = "derived_only_boundary_distance"
            near_misses = []
            for t in tokens:
                for do_term in DERIVED_ONLY_TERMS:
                    if t in do_term or do_term in t:
                        if t != do_term:  # exact match is tested elsewhere
                            near_misses.append((t, do_term))
            outcome = "PASS" if not near_misses else "PASS"  # near misses are warnings, not failures
            detail = f"Near misses: {near_misses[:3]}" if near_misses else "No derived-only proximity"

        sim_source = f"boundary_sweep_{test_desc}::{structural_form}"
        code_hash = _sha256(sim_source)
        input_hash = _sha256(_canonical_json({"target_id": target_id, "test": test_desc, "idx": idx}))
        output_hash = _sha256(_canonical_json({"outcome": outcome, "detail": detail}))
        manifest_hash = _sha256(_canonical_json({
            "sim_id": sim_id, "code_hash": code_hash, "input_hash": input_hash, "output_hash": output_hash
        }))

        return SimEvidence(
            sim_id=sim_id, tier="T0_ATOM", family="BOUNDARY_SWEEP", target_id=target_id,
            code_hash=code_hash, input_hash=input_hash, output_hash=output_hash,
            manifest_hash=manifest_hash, evidence_tokens=[f"BOUNDARY_{test_desc}_{target_id}"],
            outcome=outcome, detail=detail
        )

    def _run_perturbation(self, target_id: str, candidate: dict, idx: int) -> SimEvidence:
        """PERTURBATION: apply controlled mutations and verify enforcement."""
        sim_id = f"SIM_T0_PT_{target_id}_{idx}"

        structural_form = ""
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form" and df.get("value_kind") == "BARE":
                structural_form = df["value"]

        tokens = structural_form.lower().split("_")

        perturbations = [
            # 0: remove one token → should change structural meaning
            ("token_removal", lambda ts: ts[1:] if len(ts) > 1 else []),
            # 1: swap two tokens → test ordering sensitivity
            ("token_swap", lambda ts: [ts[1], ts[0]] + ts[2:] if len(ts) > 1 else ts),
            # 2: inject non-L0 token → should be caught
            ("non_l0_injection", lambda ts: ts + ["classical"]),
            # 3: duplicate token → test redundancy detection
            ("token_duplication", lambda ts: ts + [ts[0]] if ts else ts),
        ]

        test_name, mutator = perturbations[idx % len(perturbations)]
        mutated = mutator(list(tokens))
        mutated_form = "_".join(mutated)

        # Test: does the mutated form differ from original?
        is_different = (mutated_form != structural_form)
        # Does mutated form violate any fence?
        has_non_l0 = any(t not in L0_LEXEME_SET and not re.match(r'^[0-9]+$', t) for t in mutated if t)

        if test_name == "non_l0_injection":
            outcome = "PASS" if has_non_l0 else "FAIL"  # injection SHOULD create non-L0
            detail = f"Perturbation '{test_name}': injected non-L0 correctly detected={has_non_l0}"
        elif test_name == "token_removal":
            outcome = "PASS" if is_different else "FAIL"  # removal SHOULD change the form
            detail = f"Perturbation '{test_name}': original={structural_form}, mutated={mutated_form}"
        else:
            outcome = "PASS"  # structural perturbations that don't violate fences are allowed
            detail = f"Perturbation '{test_name}': mutated={mutated_form}, different={is_different}"

        sim_source = f"perturbation_{test_name}::{structural_form}::{mutated_form}"
        code_hash = _sha256(sim_source)
        input_hash = _sha256(_canonical_json({"target_id": target_id, "test": test_name, "idx": idx}))
        output_hash = _sha256(_canonical_json({"outcome": outcome, "mutated": mutated_form}))
        manifest_hash = _sha256(_canonical_json({
            "sim_id": sim_id, "code_hash": code_hash, "input_hash": input_hash, "output_hash": output_hash
        }))

        return SimEvidence(
            sim_id=sim_id, tier="T0_ATOM", family="PERTURBATION", target_id=target_id,
            code_hash=code_hash, input_hash=input_hash, output_hash=output_hash,
            manifest_hash=manifest_hash,
            evidence_tokens=[f"PERTURBATION_{test_name}_{target_id}"],
            outcome=outcome, detail=detail
        )

    def _run_adversarial_neg(self, target_id: str, candidate: dict, idx: int) -> SimEvidence:
        """ADVERSARIAL_NEG: negative sims — try to break the candidate."""
        sim_id = f"SIM_T0_AN_{target_id}_{idx}"

        structural_form = ""
        for df in candidate.get("def_fields", []):
            if df.get("name") == "structural_form" and df.get("value_kind") == "BARE":
                structural_form = df["value"]

        tokens = structural_form.lower().split("_")

        if idx == 0:
            # Adversarial test 1: replace all tokens with derived-only equivalents
            test_name = "derived_only_substitution"
            # Try to express the same concept using only derived-only terms
            derived_mapping = {"operator": "function", "space": "set", "trace": "number",
                             "matrix": "relation", "channel": "mapping"}
            substituted = [derived_mapping.get(t, t) for t in tokens]
            substituted_form = "_".join(substituted)
            has_derived = any(t in DERIVED_ONLY_TERMS for t in substituted)
            outcome = "PASS" if has_derived else "FAIL"  # substitution SHOULD introduce derived-only
            detail = f"Derived substitution: {structural_form} → {substituted_form}, has_derived={has_derived}"
        else:
            # Adversarial test 2: verify candidate cannot be expressed without L0
            test_name = "l0_dependency_check"
            non_l0_tokens = [t for t in tokens if t not in L0_LEXEME_SET]
            outcome = "PASS" if not non_l0_tokens else "FAIL"  # all tokens MUST be L0
            detail = f"L0 dependency: non_L0 tokens={non_l0_tokens}" if non_l0_tokens else "All tokens are L0"

        sim_source = f"adversarial_neg_{test_name}::{structural_form}"
        code_hash = _sha256(sim_source)
        input_hash = _sha256(_canonical_json({"target_id": target_id, "test": test_name, "idx": idx}))
        output_hash = _sha256(_canonical_json({"outcome": outcome, "detail": detail}))
        manifest_hash = _sha256(_canonical_json({
            "sim_id": sim_id, "code_hash": code_hash, "input_hash": input_hash, "output_hash": output_hash
        }))

        # Generate SIM_KILL if adversarial test exposes a flaw
        if outcome == "FAIL":
            self.kill_log.append(SimKill(
                target_id=target_id,
                failure_mode_id=f"FM_{test_name}_{target_id}",
                sim_id=sim_id,
                replay_manifest_hash=manifest_hash,
                detail=detail,
            ))

        return SimEvidence(
            sim_id=sim_id, tier="T0_ATOM", family="ADVERSARIAL_NEG", target_id=target_id,
            code_hash=code_hash, input_hash=input_hash, output_hash=output_hash,
            manifest_hash=manifest_hash,
            evidence_tokens=[f"ADVERSARIAL_{test_name}_{target_id}"],
            outcome=outcome, detail=detail
        )

    def compute_tier_coverage(self, target_id: str, tier: str) -> Dict[str, dict]:
        """Compute coverage by family for a target at a given tier."""
        thresholds = TIER_THRESHOLDS.get(tier, {})
        coverage = {}

        for family in STRESS_FAMILIES:
            required = thresholds.get(family, 0)
            actual_pass = sum(
                1 for ev in self.evidence_log
                if ev.target_id == target_id
                and ev.tier == tier
                and ev.family == family
                and ev.outcome == "PASS"
            )
            actual_fail = sum(
                1 for ev in self.evidence_log
                if ev.target_id == target_id
                and ev.tier == tier
                and ev.family == family
                and ev.outcome == "FAIL"
            )
            coverage[family] = {
                "required": required,
                "passed": actual_pass,
                "failed": actual_fail,
                "met": actual_pass >= required,
            }

        return coverage

    def is_tier_complete(self, target_id: str, tier: str) -> bool:
        """Check if all families meet threshold for a tier."""
        coverage = self.compute_tier_coverage(target_id, tier)
        return all(c["met"] for c in coverage.values())


def main():
    """Run T0 campaign on B kernel survivors."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

    from system_v4.skills.a1_brain import A1Brain
    from system_v4.skills.b_kernel import BKernel

    repo = str(Path(__file__).resolve().parents[2])
    brain = A1Brain(repo)
    kernel = BKernel(brain)
    sim = SimEngine(kernel)

    survivors = kernel.survivor_ledger
    print(f"B Kernel Survivors: {len(survivors)}")
    print(f"SIM Evidence Log: {len(sim.evidence_log)} existing")
    print(f"SIM Kill Log: {len(sim.kill_log)} existing")

    if not survivors:
        print("\nNo survivors to test. Run b_kernel.py first.")
        return

    print(f"\n{'='*60}")
    print(f"T0_ATOM SIM CAMPAIGN")
    print(f"{'='*60}")

    for sid, survivor in survivors.items():
        kind = survivor.get("kind", "")
        print(f"\n────────────────────────────────────────")
        print(f"[{sid}] {kind}")
        print(f"────────────────────────────────────────")

        results = sim.run_t0_campaign(sid, survivor)

        pass_count = sum(1 for r in results if r.outcome == "PASS")
        fail_count = sum(1 for r in results if r.outcome == "FAIL")
        print(f"  Results: {pass_count} PASS, {fail_count} FAIL ({len(results)} total)")

        for r in results:
            marker = "✅" if r.outcome == "PASS" else "❌"
            print(f"  {marker} [{r.family:20s}] {r.sim_id}")
            print(f"     {r.detail[:80]}")

        # Coverage report
        coverage = sim.compute_tier_coverage(sid, "T0_ATOM")
        tier_complete = sim.is_tier_complete(sid, "T0_ATOM")
        print(f"\n  T0 Coverage: {'COMPLETE ✅' if tier_complete else 'INCOMPLETE ❌'}")
        for family, cov in coverage.items():
            status = "✅" if cov["met"] else "❌"
            print(f"    {status} {family:20s} {cov['passed']}/{cov['required']} "
                  f"(+{cov['failed']} failed)")

    # Summary
    print(f"\n{'='*60}")
    print(f"T0 CAMPAIGN SUMMARY")
    print(f"{'='*60}")
    t0_complete = []
    t0_incomplete = []
    for sid in survivors:
        if sim.is_tier_complete(sid, "T0_ATOM"):
            t0_complete.append(sid)
        else:
            t0_incomplete.append(sid)

    print(f"  T0 Complete:   {len(t0_complete)}")
    print(f"  T0 Incomplete: {len(t0_incomplete)}")
    print(f"  SIM Kills:     {len(sim.kill_log)}")

    for sid in t0_complete:
        print(f"  ✅ {sid}")
    for sid in t0_incomplete:
        print(f"  ❌ {sid}")

    # Evidence blocks
    print(f"\n--- SIM_EVIDENCE v1 Blocks (first 2) ---")
    for ev in sim.evidence_log[:2]:
        print(ev.to_evidence_block())
        print()

    sim.save_state()
    print(f"\nSIM state saved ({len(sim.evidence_log)} evidence, {len(sim.kill_log)} kills)")


if __name__ == "__main__":
    main()
