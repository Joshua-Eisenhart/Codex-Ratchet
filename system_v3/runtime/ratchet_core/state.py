import sys
from pathlib import Path

RUNTIME_ROOT = Path(__file__).resolve().parents[1]
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))
from runtime_surface_guard import enforce_canonical_runtime

enforce_canonical_runtime(__file__)

import hashlib
import json


class KernelState:
    def __init__(self):
        self.axioms = {}
        self.specs = {}
        self.terms = {}
        self.survivor_order = []
        self.graveyard = []
        self.parked = []
        self.evidence_pending = {}
        self.spec_count = 0
        self.probe_count = 0
        self.active_ruleset_sha256 = ""
        self.active_megaboot_sha256 = ""
        self.active_megaboot_id = ""
        self.sim_run_count = 0
        self.pool = {}

    def add_axiom(self, axiom_id, kind=None, raw_lines=None):
        if axiom_id in self.axioms or axiom_id in self.specs:
            return False
        self.axioms[axiom_id] = {
            "kind": kind or "AXIOM_HYP",
            "raw_lines": list(raw_lines or []),
        }
        self.survivor_order.append(axiom_id)
        return True

    def add_spec(self, spec_id, spec_kind, deps=None, raw_lines=None, status=None):
        if spec_id in self.specs or spec_id in self.axioms:
            return False
        self.specs[spec_id] = {
            "kind": spec_kind,
            "deps": list(deps or []),
            "raw_lines": list(raw_lines or []),
            "evidence_tokens": set(),
            "status": status or "ACTIVE",
        }
        self.spec_count += 1
        self.survivor_order.append(spec_id)
        return True

    def add_term(self, term_literal, spec_id, binds, state="TERM_PERMITTED"):
        if term_literal in self.terms:
            return False
        self.terms[term_literal] = {
            "spec_id": spec_id,
            "binds": binds,
            "state": state,
            "required_evidence": "",
        }
        return True

    def set_term_required_evidence(self, term_literal, evidence_token):
        info = self.terms.get(term_literal)
        if not info:
            return False
        info["required_evidence"] = evidence_token
        return True

    def set_term_state(self, term_literal, new_state):
        info = self.terms.get(term_literal)
        if not info:
            return False
        info["state"] = new_state
        return True

    def add_to_graveyard(self, item_id, reason, raw_lines):
        self.graveyard.append({
            "id": item_id,
            "reason": reason,
            "raw_lines": list(raw_lines)
        })
        for concept_id, concept in self.pool.items():
            if concept.get("current_spec_id") == item_id:
                concept["status"] = "DEAD"
                concept["attempts"].append({
                    "spec_id": item_id, "reason": reason,
                    "cycle": self.sim_run_count,
                })
                concept["current_spec_id"] = None
                break

    def seed_pool(self, concept_id, source, label, body, chain_needs=None):
        """Add a concept to the graveyard pool. Everything starts here."""
        if concept_id in self.pool:
            return False
        self.pool[concept_id] = {
            "status": "DEAD",
            "source": source,
            "label": label,
            "body": body,
            "chain_needs": list(chain_needs or []),
            "attempts": [],
            "current_spec_id": None,
        }
        return True

    def attempt_resurrect(self, concept_id, spec_id):
        """Mark a pool concept as being attempted via a spec."""
        if concept_id not in self.pool:
            return False
        self.pool[concept_id]["status"] = "ATTEMPTING"
        self.pool[concept_id]["current_spec_id"] = spec_id
        return True

    def resurrect(self, concept_id):
        """Mark a pool concept as successfully resurrected."""
        if concept_id not in self.pool:
            return False
        self.pool[concept_id]["status"] = "RESURRECTED"
        return True

    def seed_pool_from_fuel(self, fuel_path):
        """Seed the graveyard pool from a fuel_queue.json file. Everything starts dead."""
        import json as _json
        from pathlib import Path as _Path
        fuel = _json.loads(_Path(fuel_path).read_text())
        count = 0
        for entry in fuel.get("entries", []):
            if self.seed_pool(
                entry.get("id", ""), entry.get("source_doc", ""),
                entry.get("label", ""), entry.get("body", ""),
                chain_needs=entry.get("concepts_needed", []),
            ):
                count += 1
        return count

    def snapshot(self):
        axioms = []
        for ax_id in sorted(self.axioms.keys()):
            axioms.append({
                "id": ax_id,
                "kind": self.axioms[ax_id]["kind"],
                "raw_lines": list(self.axioms[ax_id]["raw_lines"]),
            })
        specs = []
        for sp_id in sorted(self.specs.keys()):
            specs.append({
                "id": sp_id,
                "kind": self.specs[sp_id]["kind"],
                "deps": list(self.specs[sp_id]["deps"]),
                "raw_lines": list(self.specs[sp_id]["raw_lines"]),
                "evidence_tokens": sorted(list(self.specs[sp_id].get("evidence_tokens", set()))),
                "status": self.specs[sp_id].get("status", "ACTIVE"),
            })
        terms = []
        for term in sorted(self.terms.keys()):
            terms.append({
                "term": term,
                "spec_id": self.terms[term]["spec_id"],
                "binds": self.terms[term]["binds"],
                "state": self.terms[term].get("state", "TERM_PERMITTED"),
                "required_evidence": self.terms[term].get("required_evidence", ""),
            })
        pool_snap = {}
        for cid in sorted(self.pool.keys()):
            c = self.pool[cid]
            pool_snap[cid] = {
                "status": c["status"],
                "source": c.get("source", ""),
                "label": c.get("label", ""),
                "body": c.get("body", ""),
                "chain_needs": list(c.get("chain_needs", [])),
                "attempts": list(c.get("attempts", [])),
                "current_spec_id": c.get("current_spec_id"),
            }

        return {
            "axioms": axioms,
            "specs": specs,
            "terms": terms,
            "survivor_order": list(self.survivor_order),
            "graveyard": list(self.graveyard),
            "parked": list(self.parked),
            "evidence_pending": {k: sorted(list(v)) for k, v in sorted(self.evidence_pending.items())},
            "counts": {
                "spec": self.spec_count,
                "probe": self.probe_count,
            },
            "active_ruleset_sha256": self.active_ruleset_sha256,
            "active_megaboot_sha256": self.active_megaboot_sha256,
            "active_megaboot_id": self.active_megaboot_id,
            "sim_run_count": self.sim_run_count,
            "pool": pool_snap,
        }

    def to_json(self):
        return json.dumps(self.snapshot(), sort_keys=True, separators=(",", ":"))

    def hash(self):
        data = self.to_json().encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @classmethod
    def from_json(cls, text):
        data = json.loads(text)
        st = cls()
        for ax in data.get("axioms", []):
            st.axioms[ax["id"]] = {
                "kind": ax.get("kind"),
                "raw_lines": list(ax.get("raw_lines", [])),
            }
        for sp in data.get("specs", []):
            st.specs[sp["id"]] = {
                "kind": sp.get("kind"),
                "deps": list(sp.get("deps", [])),
                "raw_lines": list(sp.get("raw_lines", [])),
                "evidence_tokens": set(sp.get("evidence_tokens", [])),
                "status": sp.get("status", "ACTIVE"),
            }
        st.evidence_pending = {k: set(v) for k, v in data.get("evidence_pending", {}).items()}
        # Backfill status if missing based on pending evidence
        if st.evidence_pending:
            for spec_id in st.evidence_pending.keys():
                if spec_id in st.specs:
                    st.specs[spec_id]["status"] = "PENDING_EVIDENCE"
        for spec_id, spec in st.specs.items():
            if spec_id not in st.evidence_pending and not spec.get("status"):
                spec["status"] = "ACTIVE"
        for term in data.get("terms", []):
            st.terms[term["term"]] = {
                "spec_id": term.get("spec_id"),
                "binds": term.get("binds"),
                "state": term.get("state", "TERM_PERMITTED"),
                "required_evidence": term.get("required_evidence", ""),
            }
        st.survivor_order = list(data.get("survivor_order", []))
        st.graveyard = list(data.get("graveyard", []))
        st.parked = list(data.get("parked", []))
        counts = data.get("counts", {})
        st.spec_count = int(counts.get("spec", 0))
        st.probe_count = int(counts.get("probe", 0))
        st.active_ruleset_sha256 = data.get("active_ruleset_sha256", "")
        st.active_megaboot_sha256 = data.get("active_megaboot_sha256", "")
        st.active_megaboot_id = data.get("active_megaboot_id", "")
        st.sim_run_count = int(data.get("sim_run_count", 0))
        for cid, cdata in data.get("pool", {}).items():
            st.pool[cid] = {
                "status": cdata.get("status", "DEAD"),
                "source": cdata.get("source", ""),
                "label": cdata.get("label", ""),
                "body": cdata.get("body", ""),
                "chain_needs": list(cdata.get("chain_needs", [])),
                "attempts": list(cdata.get("attempts", [])),
                "current_spec_id": cdata.get("current_spec_id"),
            }
        return st
