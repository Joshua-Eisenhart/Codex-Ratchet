#!/usr/bin/env python3
"""semantic_drift_gate — executable prototype of the SDG spec.

Implements the controller-owned parts of
CB_SEMANTIC_DRIFT_AND_ARGUMENT_CONTROL_SPEC_20260806.md section 7:
type registry, bridge requirement, scope/quantifier widening,
representation-is-not-identity, scalarization, agent insertion, causal
insertion, self-sealing necessity, countermodel obligation, and
verdict separation.

Design rule taken from the spec and enforced here: the gate is
LEXICAL AND STRUCTURAL, never semantic. It does not judge whether a
claim is true; it decides whether the packet declares the objects a
claim of that TYPE requires. Everything it needs is in the packet's
declared fields, so a replay produces the same verdict without a
model.
promotion_allowed=false. Verdicts: ADMIT_FOR_TESTING | PARKED |
BLOCKED.
"""
from __future__ import annotations
import json, re, sys
from dataclasses import dataclass, field

# registered claim types, ordered by escalation rank (spec section 1)
TYPE_RANK = {"finite_admission": 0, "distinguishability": 1,
             "mss_frontier": 2, "preference_utility": 3,
             "agent_policy": 4, "causal_scientific": 5}

AGENT_VERBS = ("chooses", "prefers", "aims", "selects", "uses",
               "relieves uneasiness", "wants", "decides", "seeks")
CAUSAL_VERBS = ("causes", "therefore produces", "drives", "leads to",
                "produces", "results in", "makes")
NECESSITY = ("necessary for any", "required for all", "presupposes",
             "any assertion", "must be the case for all",
             "by construction is", "always already")
SCALARIZE = ("single score", "utility", "ranks", "ordering over",
             "maximizes", "optimal", "best")
UNIVERSAL = ("all", "any", "every", "universal", "necessarily")
LOCAL = ("this probe", "this fixture", "in this run", "some", "local")

@dataclass
class Verdict:
    status: str
    reasons: list = field(default_factory=list)
    required_artifacts: list = field(default_factory=list)
    def add(self, status, reason, artifact=None):
        rank = {"ADMIT_FOR_TESTING": 0, "PARKED": 1, "BLOCKED": 2}
        if rank[status] > rank[self.status]:
            self.status = status
        self.reasons.append(reason)
        if artifact:
            self.required_artifacts.append(artifact)

def _text(packet) -> str:
    parts = [packet.get("requested_claim", {}).get("statement", "")]
    parts += [s.get("statement", "") for s in packet.get("intermediates", [])]
    return " ".join(parts).lower()

def semantic_drift_gate(packet: dict) -> Verdict:
    v = Verdict("ADMIT_FOR_TESTING")
    # --- 1 type check
    declared = packet.get("primitive", {}).get("type")
    target = packet.get("requested_claim", {}).get("type")
    for t, label in ((declared, "primitive"), (target, "requested_claim")):
        if t not in TYPE_RANK:
            v.add("BLOCKED", f"UNREGISTERED_TYPE:{label}={t}")
            return v
    # --- 2 bridge check (type escalation)
    if TYPE_RANK[target] > TYPE_RANK[declared]:
        bridges = {b.get("from"): b for b in packet.get("bridges", [])}
        step = declared
        while TYPE_RANK[step] < TYPE_RANK[target]:
            nxt = next((k for k, r in TYPE_RANK.items()
                        if r == TYPE_RANK[step] + 1), None)
            b = bridges.get(step)
            if not b or b.get("to") != nxt or not b.get("verifier"):
                v.add("PARKED", f"UNBRIDGED_TYPE_ESCALATION:{step}->{nxt}",
                      f"bridge_contract({step}->{nxt}) with declared "
                      f"inputs, finite representation, scope, verifier")
                break
            step = nxt
    # --- 3 scope / quantifier widening
    prim_scope = (packet.get("primitive", {}).get("scope") or "").lower()
    claim_txt = _text(packet)
    widened = any(u in claim_txt for u in UNIVERSAL)
    local_primitive = any(l in prim_scope for l in LOCAL) or prim_scope == ""
    if widened and local_primitive and not packet.get("scope_bridge"):
        v.add("PARKED", "UNBRIDGED_SCOPE_WIDENING", "scope_bridge record")
    # --- 4 representation is not identity
    for enc in packet.get("encodings", []):
        if enc.get("claims") in ("identity", "ontology", "causality"):
            v.add("BLOCKED", "REPRESENTATION_IS_NOT_IDENTITY:"
                             f"{enc.get('name')}")
        elif enc.get("marked") != "REPRESENTATIONAL_ENCODING":
            v.add("PARKED", f"UNMARKED_ENCODING:{enc.get('name')}",
                  "mark encoding REPRESENTATIONAL_ENCODING")
    # --- 5 scalarization
    if any(s in claim_txt for s in SCALARIZE):
        sc = packet.get("score_declaration")
        if not sc or not all(k in sc for k in
                             ("producer", "interpretation", "ties",
                              "failure_mode")):
            v.add("PARKED", "UNDECLARED_SCALARIZATION",
                  "score_declaration{producer,interpretation,ties,"
                  "failure_mode}")
        if packet.get("replaces_frontier_with_scalar"):
            v.add("BLOCKED", "FRONTIER_FLATTENED_TO_SCALAR")
    # --- 6 agent insertion
    if any(a in claim_txt for a in AGENT_VERBS):
        iface = packet.get("agent_interface")
        if not iface or not all(k in iface for k in
                                ("agent", "state", "action")):
            v.add("PARKED", "AGENT_LANGUAGE_WITHOUT_INTERFACE",
                  "agent_interface{agent,state,action}")
    # --- 7 causal insertion
    if any(c in claim_txt for c in CAUSAL_VERBS):
        cp = packet.get("causal_packet")
        if not cp or not all(k in cp for k in
                             ("intervention", "bounded_scope", "control")):
            v.add("PARKED", "CAUSAL_LANGUAGE_WITHOUT_PACKET",
                  "causal_packet{intervention,bounded_scope,control}")
    # --- 8 self-sealing necessity
    if any(n in claim_txt for n in NECESSITY):
        if not packet.get("proof_contract") and \
                not packet.get("countermodel_search"):
            v.add("PARKED", "UNTESTABLE_NECESSITY_CLAIM",
                  "proof_contract OR countermodel_search, else classify "
                  "as DECLARED_AXIOM_OR_INTERPRETATION")
    # --- 9 countermodel obligation for universal bridges
    for b in packet.get("bridges", []):
        if b.get("universal") and not (b.get("countermodel_search")
                                       or b.get("no_countermodel_reason")):
            v.add("PARKED", f"UNIVERSAL_BRIDGE_WITHOUT_COUNTERMODEL:"
                            f"{b.get('from')}->{b.get('to')}")
    # --- 10 verdict separation
    origin = packet.get("proposal_origin", {})
    if origin.get("producer_kind") in ("llm", "human") and \
            packet.get("self_issued_verdict"):
        v.add("BLOCKED", "PRODUCER_ISSUED_ITS_OWN_VERDICT")
    return v

# ---------------- v2: commitment ledger + input envelope (spec 7.3) --
def gate_controlled_evaluation(envelope: dict, proposal: dict) -> Verdict:
    """Section 7.3: an acknowledgement in prose is not a ledger mutation.

    Every conclusion must cite premise identifiers registered in the
    immutable INPUT_ENVELOPE. Structural checks only — the gate never
    reads meaning, it reads which identifiers were cited and which
    locked commitments the typed claim contradicts.
    """
    v = Verdict("ADMIT_FOR_TESTING")
    if proposal.get("envelope_sha256") != envelope.get("envelope_sha256"):
        v.add("BLOCKED", "ENVELOPE_HASH_MISMATCH")
        return v
    registered = set(envelope.get("premises", {}))
    registered |= set(envelope.get("commitments", {}))
    registered |= set(b.get("id") for b in envelope.get("bridges", []))
    for claim in proposal.get("claims", []):
        cited = set(claim.get("premises", []))
        unregistered = sorted(cited - registered)
        if unregistered:
            v.add("PARKED", f"UNREGISTERED_PREMISE:{unregistered}",
                  "new assumption record or bridge packet")
        if not cited and not claim.get("declared_new_assumption"):
            v.add("PARKED", "UNCITED_CONCLUSION",
                  "premise identifiers for every conclusion")
        # locked commitment contradiction: the typed escalation the
        # commitment forbids, attempted anyway
        for cid, c in envelope.get("commitments", {}).items():
            forbidden = c.get("forbids_escalation")
            if not forbidden:
                continue
            src, dst = forbidden
            if claim.get("from_type") == src and claim.get("to_type") == dst:
                bridge = claim.get("bridge")
                accepted = {b.get("id") for b in envelope.get("bridges", [])
                            if b.get("accepted")}
                if bridge not in accepted:
                    v.add("PARKED",
                          f"REVERSION_AFTER_ACKNOWLEDGEMENT:{cid}",
                          f"bridge packet {src}->{dst}")
                    v.add("PARKED", "UNBRIDGED_TYPE_ESCALATION")
        # alias of a blocked bridge: same typed escalation, new wording
        if claim.get("aliases_blocked_bridge"):
            v.add("PARKED", "SEMANTIC_ALIAS_WITHOUT_BRIDGE")
    ceiling = proposal.get("requested_ceiling")
    evidence = envelope.get("evidence_ceiling")
    order = ["none", "bounded_run", "recomputed", "released"]
    if ceiling and evidence and ceiling in order and evidence in order:
        if order.index(ceiling) > order.index(evidence):
            v.add("BLOCKED", f"EVIDENCE_CEILING_BREACH:{ceiling}>{evidence}")
    # artifact custody (plane 0): described but absent
    for a in proposal.get("artifact_claims", []):
        if a.get("status") == "described" and not a.get("manifest_path"):
            v.add("BLOCKED", f"HANDOFF_DESCRIBED_BUT_ABSENT:{a.get('name')}")
        if a.get("declared_version") and a.get("metadata_version") and \
                a["declared_version"] != a["metadata_version"]:
            v.add("BLOCKED", f"HANDOFF_VERSION_DIVERGENCE:{a.get('name')}")
    # producer-authored success language (plane 4)
    if proposal.get("producer_status") in ("proved", "canonical",
                                           "integrated", "promotion_allowed"):
        if not proposal.get("independent_recomputation"):
            v.add("BLOCKED", "PRODUCER_AUTHORED_STATUS_WITHOUT_RECOMPUTE")
    return v


# ---------------- mandatory adversarial fixtures (spec section 9) ----
FIXTURES = {
 "CB-SD-001 filter is not optimizer": ({
   "primitive": {"type": "finite_admission", "scope": "this probe"},
   "requested_claim": {"type": "preference_utility",
     "statement": "differential retention is selection, so the filter ranks options"},
   "bridges": [], "proposal_origin": {"producer_kind": "llm"}},
   "PARKED"),
 "CB-SD-002 boolean encoding is not utility identity": ({
   "primitive": {"type": "finite_admission", "scope": "this fixture"},
   "requested_claim": {"type": "preference_utility",
     "statement": "admit/exclude encoded as 1/0 is utility by construction"},
   "encodings": [{"name": "admit_as_1_0", "claims": "identity"}],
   "bridges": [], "proposal_origin": {"producer_kind": "llm"}},
   "BLOCKED"),
 "CB-SD-003 plural MSS is not scalar optimization": ({
   "primitive": {"type": "mss_frontier", "scope": "this run"},
   "requested_claim": {"type": "preference_utility",
     "statement": "the frontier maximizes a single score, the optimal one wins"},
   "replaces_frontier_with_scalar": True,
   "proposal_origin": {"producer_kind": "llm"}},
   "BLOCKED"),
 "CB-SD-005 self-sealing necessity": ({
   "primitive": {"type": "finite_admission", "scope": "this probe"},
   "requested_claim": {"type": "causal_scientific",
     "statement": "any assertion presupposes selection, so this is necessary for all reasoning"},
   "bridges": [], "proposal_origin": {"producer_kind": "llm"}},
   "PARKED"),
 "CB-SD-006 filter-to-agent drift": ({
   "primitive": {"type": "finite_admission", "scope": "this probe"},
   "requested_claim": {"type": "agent_policy",
     "statement": "the system chooses what it prefers and thereby relieves uneasiness"},
   "bridges": [], "proposal_origin": {"producer_kind": "llm"}},
   "PARKED"),
 "CB-SD-007 agent policy operationally bound (should ADMIT)": ({
   "primitive": {"type": "finite_admission", "scope": "this probe"},
   "requested_claim": {"type": "agent_policy",
     "statement": "the controller selects the next stage from the declared action set"},
   "agent_interface": {"agent": "cb_scheduler", "state": "packet",
                       "action": "stage_dispatch"},
   "bridges": [
     {"from": "finite_admission", "to": "distinguishability",
      "verifier": "probe_family_v1"},
     {"from": "distinguishability", "to": "mss_frontier",
      "verifier": "frontier_enum_v1"},
     {"from": "mss_frontier", "to": "preference_utility",
      "verifier": "declared_order_v1"},
     {"from": "preference_utility", "to": "agent_policy",
      "verifier": "actuation_binding_v1"}],
   "proposal_origin": {"producer_kind": "llm"}},
   "ADMIT_FOR_TESTING"),
 "PRODUCER SELF-VERDICT": ({
   "primitive": {"type": "finite_admission", "scope": "this probe"},
   "requested_claim": {"type": "finite_admission",
                       "statement": "the fixture admits three states"},
   "self_issued_verdict": True,
   "proposal_origin": {"producer_kind": "llm"}},
   "BLOCKED"),
}

V2_ENVELOPE = {
    "envelope_sha256": "e1",
    "premises": {"P-FINITE": "finite support", "P-PROBE": "probe demands",
                 "P-COMPAT": "compatibility rule"},
    "commitments": {"SC-D-ONLY": {
        "forbids_escalation": ["finite_admission", "preference_utility"]}},
    "bridges": [], "evidence_ceiling": "bounded_run"}

V2_FIXTURES = {
 "CB-SD-008 acknowledgement is not a state change":
   ({"envelope_sha256": "e1", "claims": [{"premises": ["SC-D-ONLY"],
     "from_type": "finite_admission",
     "to_type": "preference_utility"}]}, "PARKED"),
 "CB-SD-009 alias of a blocked bridge":
   ({"envelope_sha256": "e1", "claims": [{"premises": ["P-COMPAT"],
     "from_type": "finite_admission", "to_type": "preference_utility",
     "aliases_blocked_bridge": True}]}, "PARKED"),
 "CB-SD-010 unregistered premise":
   ({"envelope_sha256": "e1", "claims": [
     {"premises": ["P-SCARCITY-MUST-CHOOSE"],
      "from_type": "finite_admission", "to_type": "agent_policy"}]}, "PARKED"),
 "CB-SD-011 producer-authored status":
   ({"envelope_sha256": "e1", "producer_status": "proved",
     "claims": [{"premises": ["P-FINITE"], "from_type": "finite_admission",
                 "to_type": "finite_admission"}]}, "BLOCKED"),
 "CB-SD-012 handoff described but absent":
   ({"envelope_sha256": "e1", "claims": [{"premises": ["P-FINITE"],
     "from_type": "finite_admission", "to_type": "finite_admission"}],
     "artifact_claims": [{"name": "three_engine_seal",
                          "status": "described"}]}, "BLOCKED"),
 "CB-SD-012b version divergence":
   ({"envelope_sha256": "e1", "claims": [{"premises": ["P-FINITE"],
     "from_type": "finite_admission", "to_type": "finite_admission"}],
     "artifact_claims": [{"name": "constraintbox", "status": "present",
                          "manifest_path": "src/",
                          "declared_version": "0.3.5",
                          "metadata_version": "0.3.4"}]}, "BLOCKED"),
 "ceiling breach":
   ({"envelope_sha256": "e1", "requested_ceiling": "released",
     "claims": [{"premises": ["P-FINITE"], "from_type": "finite_admission",
                 "to_type": "finite_admission"}]}, "BLOCKED"),
 "wrong envelope":
   ({"envelope_sha256": "e2", "claims": []}, "BLOCKED"),
 "POSITIVE CONTROL (cited, within ceiling)":
   ({"envelope_sha256": "e1", "requested_ceiling": "bounded_run",
     "claims": [{"premises": ["P-FINITE", "P-PROBE"],
                 "from_type": "finite_admission",
                 "to_type": "finite_admission"}]}, "ADMIT_FOR_TESTING"),
}

if __name__ == "__main__":
    results, ok = [], 0
    for name, (packet, expected) in FIXTURES.items():
        v = semantic_drift_gate(packet)
        good = v.status == expected
        ok += good
        print(f"{'PASS' if good else 'FAIL'}  {name}")
        print(f"        verdict={v.status} expected={expected}")
        for r in v.reasons:
            print(f"        - {r}")
        results.append({"fixture": name, "verdict": v.status,
                        "expected": expected, "as_expected": good,
                        "reasons": v.reasons,
                        "required_artifacts": v.required_artifacts})
    ok2 = 0
    print()
    for name, (proposal, expected) in V2_FIXTURES.items():
        v = gate_controlled_evaluation(V2_ENVELOPE, proposal)
        good = v.status == expected
        ok2 += good
        print(f"{'PASS' if good else 'FAIL'}  {name}")
        print(f"        verdict={v.status} expected={expected}")
        for r in v.reasons:
            print(f"        - {r}")
        results.append({"fixture": name, "verdict": v.status,
                        "expected": expected, "as_expected": good,
                        "reasons": v.reasons})
    print(f"\nfixtures as expected: {ok}/{len(FIXTURES)} (v1) "
          f"and {ok2}/{len(V2_FIXTURES)} (v2 commitment ledger)")
    ok = ok + ok2
    json.dump({"schema": "cb.semantic-drift-gate-prototype.v1",
               "results": results, "promotion_allowed": False},
              open("SEMANTIC_DRIFT_GATE_RUN.json", "w"), indent=1)
    sys.exit(0 if ok == len(FIXTURES) + len(V2_FIXTURES) else 1)
