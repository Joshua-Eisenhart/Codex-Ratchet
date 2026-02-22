import re
from dataclasses import dataclass

from containers import parse_export_block, parse_sim_evidence_pack, split_items
from state import CANON_TERM_STATES, KernelState


ALLOWED_TAGS = {
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


ALLOWED_SPEC_KINDS = {"MATH_DEF", "TERM_DEF", "LABEL_DEF", "CANON_PERMIT", "SIM_SPEC"}
TOKEN_CLASS_VALUES = {
    "STATE_TOKEN",
    "PROBE_TOKEN",
    "REGISTRY_TOKEN",
    "MATH_TOKEN",
    "TERM_TOKEN",
    "LABEL_TOKEN",
    "PERMIT_TOKEN",
    "EVIDENCE_TOKEN",
}
FIELD_REGEX = re.compile(r"^DEF_FIELD\s+(\S+)\s+CORR\s+(\S+)\s+(.+)$")
REQUIRES_REGEX = re.compile(r"^REQUIRES\s+(\S+)\s+CORR\s+(\S+)$")
SPEC_KIND_REGEX = re.compile(r"^SPEC_KIND\s+(\S+)\s+CORR\s+(\S+)$")
PROBE_KIND_REGEX = re.compile(r"^PROBE_KIND\s+(\S+)\s+CORR\s+(\S+)$")
AXIOM_KIND_REGEX = re.compile(r"^AXIOM_KIND\s+(\S+)\s+CORR\s+(\S+)$")
ASSERT_REGEX = re.compile(r"^ASSERT\s+(\S+)\s+CORR\s+EXISTS\s+(\S+)\s+(\S+)$")
KILL_IF_REGEX = re.compile(r"^KILL_IF\s+(\S+)\s+CORR\s+(\S+)$")
LOWER_TOKEN_REGEX = re.compile(r"[a-z][a-z0-9_]*")
MIXED_CASE_TOKEN_REGEX = re.compile(r"\b(?=\w*[A-Z])(?=\w*[a-z])\w+\b")
HEX64_REGEX = re.compile(r"^[0-9a-f]{64}$")
NON_ASCII_REGEX = re.compile(r"[^\x00-\x7F]")
FORMULA_LINE_REGEX = re.compile(r'^DEF_FIELD\s+(\S+)\s+CORR\s+FORMULA\s+"([^"]*)"$')
TERM_LINE_REGEX = re.compile(r'^DEF_FIELD\s+(\S+)\s+CORR\s+TERM\s+"([^"]*)"$')
LABEL_LINE_REGEX = re.compile(r'^DEF_FIELD\s+(\S+)\s+CORR\s+LABEL\s+"([^"]*)"$')
SIM_HASH_LINE_REGEX = re.compile(r"^DEF_FIELD\s+(\S+)\s+CORR\s+SIM_CODE_HASH_SHA256\s+(\S+)$")
ITEM_ID_REGEX = re.compile(r"^[A-Za-z0-9_]+$")


@dataclass
class _ItemParse:
    item_id: str
    header: str
    item_text: str
    axiom_kind: str
    probe_kind: str
    spec_kind: str
    requires: list[str]
    asserts: list[tuple[str, str]]
    fields: dict[str, list[str]]
    formulas: list[str]
    term_literals: list[str]
    label_literals: list[str]
    kill_if_tokens: list[str]
    kill_bind: str


@dataclass
class _LineViolation:
    tag: str
    rule_id: str
    offender_line: str
    offender_literal: str = ""


class BootpackBKernel:
    def __init__(self):
        self.allowed_spec_kinds = set(ALLOWED_SPEC_KINDS)

    def evaluate_export_block(self, text: str, state: KernelState, batch_id: str = "") -> dict:
        result = {"accepted": [], "parked": [], "rejected": []}
        old_hash = state.hash()
        try:
            block = parse_export_block(text)
        except Exception as exc:
            self._reject(state, result, "EXPORT_BLOCK", "SCHEMA_FAIL", f"PARSE_EXPORT:{exc}", batch_id)
            self._finalize_batch(state, old_hash, bool(result["accepted"]))
            return result

        if block.target != "THREAD_B_ENFORCEMENT_KERNEL":
            self._reject(state, result, block.export_id, "KERNEL_ERROR", "TARGET_MISMATCH", batch_id)
            self._finalize_batch(state, old_hash, bool(result["accepted"]))
            return result
        if state.active_megaboot_sha256:
            if not block.megaboot_sha256 or block.megaboot_sha256 != state.active_megaboot_sha256:
                self._reject(state, result, block.export_id, "KERNEL_ERROR", "MEGABOOT_HASH_MISMATCH", batch_id)
                self._finalize_batch(state, old_hash, bool(result["accepted"]))
                return result
        if state.active_ruleset_sha256:
            if not block.ruleset_sha256 or block.ruleset_sha256.lower() != state.active_ruleset_sha256.lower():
                self._reject(state, result, block.export_id, "SCHEMA_FAIL", "RULESET_HASH_MISMATCH", batch_id)
                self._finalize_batch(state, old_hash, bool(result["accepted"]))
                return result

        for line in block.content_lines:
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith("//"):
                self._reject(state, result, block.export_id, "COMMENT_BAN", stripped, batch_id)
                self._finalize_batch(state, old_hash, bool(result["accepted"]))
                return result

        items = split_items(block.content_lines)
        defined_ids = set(state.survivor_ledger.keys())
        prior_header_ids: set[str] = set()
        for item in items:
            item_id = item.get("id", "")
            header = item.get("header", "")
            if not ITEM_ID_REGEX.match(item_id or ""):
                self._reject(state, result, item_id or "UNKNOWN", "SCHEMA_FAIL", "BAD_ITEM_ID", batch_id)
                continue
            if not self._id_namespace_ok(header, item_id):
                self._reject(state, result, item_id, "SCHEMA_FAIL", "ID_NAMESPACE", batch_id)
                prior_header_ids.add(item_id)
                continue

            parse = self._parse_item(item, state)
            if parse is None:
                self._reject(state, result, item_id, "SCHEMA_FAIL", "ITEM_PARSE", batch_id)
                prior_header_ids.add(item_id)
                continue

            line_violation = self._line_fence_check(parse, state)
            if line_violation:
                self._reject(
                    state,
                    result,
                    item_id,
                    line_violation.tag,
                    "LINE_FENCE",
                    batch_id,
                    offender_rule=line_violation.rule_id,
                    offender_line=line_violation.offender_line,
                    offender_literal=line_violation.offender_literal,
                )
                prior_header_ids.add(item_id)
                continue

            for dep in parse.requires:
                if dep not in defined_ids and dep not in prior_header_ids:
                    self._park(
                        state,
                        result,
                        item_id,
                        "FORWARD_DEPEND",
                        f"MISSING:{dep}",
                        batch_id,
                        item_class=parse.header,
                        item_text=parse.item_text,
                    )
                    break
            else:
                if parse.header == "AXIOM_HYP":
                    self._admit_axiom(parse, state, result, batch_id)
                elif parse.header == "PROBE_HYP":
                    self._admit_probe(parse, state, result, batch_id)
                elif parse.header == "SPEC_HYP":
                    self._admit_spec(parse, state, result, batch_id)
                else:
                    self._reject(state, result, item_id, "SCHEMA_FAIL", "UNKNOWN_HEADER", batch_id)

            if any(x.get("id") == item_id for x in result["accepted"]):
                defined_ids.add(item_id)
            prior_header_ids.add(item_id)

        self._apply_probe_pressure(state, result, batch_id)
        self._finalize_batch(state, old_hash, bool(result["accepted"]))
        return result

    def ingest_sim_evidence_pack(self, text: str, state: KernelState, batch_id: str = "") -> dict:
        try:
            blocks = parse_sim_evidence_pack(text)
        except Exception as exc:
            state.reject_log.append({"batch_id": batch_id, "tag": "SCHEMA_FAIL", "detail": f"SIM_PARSE:{exc}"})
            return {"status": "REJECT", "reason": "SCHEMA_FAIL", "satisfied": []}

        satisfied: list[str] = []
        for block in blocks:
            # Unified SIM_EVIDENCE v1 contract: all hashes must be 64 lowercase hex.
            for field_name, value in [
                ("CODE_HASH_SHA256", block.code_hash_sha256),
                ("INPUT_HASH_SHA256", block.input_hash_sha256),
                ("OUTPUT_HASH_SHA256", block.output_hash_sha256),
                ("RUN_MANIFEST_SHA256", block.run_manifest_sha256),
            ]:
                if not HEX64_REGEX.match((value or "").strip()):
                    state.reject_log.append(
                        {"batch_id": batch_id, "tag": "SCHEMA_FAIL", "detail": f"SIM_EVIDENCE_INVALID_HASH:{field_name}"}
                    )
                    return {"status": "REJECT", "reason": "SCHEMA_FAIL", "satisfied": []}
            if block.sim_id == "S_RULESET_HASH":
                ruleset_hash = block.metrics.get("ruleset_sha256", "").lower()
                if HEX64_REGEX.match(ruleset_hash):
                    state.active_ruleset_sha256 = ruleset_hash
            for target, token in block.evidence_signals:
                state.evidence_tokens.add(token)
                if target in state.evidence_pending and token in state.evidence_pending[target]:
                    state.evidence_pending[target].remove(token)
                    if not state.evidence_pending[target]:
                        del state.evidence_pending[target]
                        if target in state.survivor_ledger:
                            state.survivor_ledger[target]["status"] = "ACTIVE"
                    satisfied.append(target)
                for term, entry in state.term_registry.items():
                    if entry.get("required_evidence") == token:
                        entry["state"] = "CANONICAL_ALLOWED"
                        state.term_registry[term] = entry
            if block.sim_id == "S_MEGA_BOOT_HASH":
                for target, token in block.evidence_signals:
                    if target == "S_MEGA_BOOT_HASH" and token == "E_MEGA_BOOT_HASH":
                        state.active_megaboot_sha256 = block.code_hash_sha256
                        state.active_megaboot_id = block.metrics.get("megaboot_id", "")
            for target, token in block.kill_signals:
                self._apply_kill_signal(state, block.sim_id, target, token, batch_id)
        return {"status": "OK", "satisfied": sorted(set(satisfied))}

    def _admit_axiom(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        if not parse.axiom_kind:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "AXIOM_KIND_REQUIRED", batch_id)
            return
        existing = state.survivor_ledger.get(parse.item_id)
        if existing and existing.get("item_text") != parse.item_text:
            state.kill_log.append({"batch_id": batch_id, "id": parse.item_id, "tag": "SHADOW_ATTEMPT"})
            self._reject(state, result, parse.item_id, "SHADOW_ATTEMPT", "AXIOM_IMMUTABLE", batch_id)
            return
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, "ACTIVE", metadata=metadata)

    def _admit_probe(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        if not parse.probe_kind:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "PROBE_KIND_REQUIRED", batch_id)
            return
        probe_tokens = [token for token_class, token in parse.asserts if token_class == "PROBE_TOKEN"]
        if len(probe_tokens) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "PROBE_TOKEN_REQUIRED", batch_id)
            return
        state.probe_meta[parse.item_id] = {
            "kind": parse.probe_kind,
            "probe_token": probe_tokens[0],
            "admitted_batch": state.accepted_batch_count + 1,
            "first_referenced_batch": 0,
            "utilization_checked": False,
            "status": "ACTIVE",
        }
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, "ACTIVE", metadata=metadata)

    def _admit_spec(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        if parse.spec_kind not in self.allowed_spec_kinds:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "SPEC_KIND_UNSUPPORTED", batch_id)
            return
        if self._is_near_duplicate(parse, state):
            self._park(
                state,
                result,
                parse.item_id,
                "NEAR_REDUNDANT",
                "JACCARD_GT_080",
                batch_id,
                item_class=parse.header,
                item_text=parse.item_text,
            )
            return
        if parse.spec_kind == "MATH_DEF":
            self._admit_math_def(parse, state, result, batch_id)
            return
        if parse.spec_kind == "TERM_DEF":
            self._admit_term_def(parse, state, result, batch_id)
            return
        if parse.spec_kind == "LABEL_DEF":
            self._admit_label_def(parse, state, result, batch_id)
            return
        if parse.spec_kind == "CANON_PERMIT":
            self._admit_canon_permit(parse, state, result, batch_id)
            return
        if parse.spec_kind == "SIM_SPEC":
            self._admit_sim_spec(parse, state, result, batch_id)
            return

    def _admit_math_def(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        required = {"OBJECTS", "OPERATIONS", "INVARIANTS", "DOMAIN", "CODOMAIN", "SIM_CODE_HASH_SHA256"}
        missing = [name for name in sorted(required) if name not in parse.fields]
        if missing:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", f"MATH_DEF_MISSING:{','.join(missing)}", batch_id)
            return
        for value in parse.fields.get("SIM_CODE_HASH_SHA256", []):
            if not HEX64_REGEX.match(value.lower()):
                self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "BAD_SIM_CODE_HASH", batch_id)
                return
        math_tokens = [token for token_class, token in parse.asserts if token_class == "MATH_TOKEN"]
        if len(math_tokens) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "MATH_TOKEN_REQUIRED", batch_id)
            return
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, "ACTIVE", metadata=metadata)
        state.spec_meta[parse.item_id] = {"kind": "MATH_DEF"}
        self._record_probe_references(state, parse.requires)

    def _admit_term_def(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        if len(parse.requires) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "TERM_DEF_REQUIRES_ONE_MATH", batch_id)
            return
        dep = parse.requires[0]
        dep_kind = state.spec_meta.get(dep, {}).get("kind")
        if dep_kind != "MATH_DEF":
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "TERM_DEF_REQUIRES_MATH_DEF", batch_id)
            return
        if "TERM" not in parse.fields or "BINDS" not in parse.fields:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "TERM_DEF_FIELDS_MISSING", batch_id)
            return
        term_literal = parse.fields["TERM"][0].lower()
        binds_value = parse.fields["BINDS"][0]
        if binds_value != dep:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "TERM_DEF_BINDS_MISMATCH", batch_id)
            return
        if "_" in term_literal:
            for component in term_literal.split("_"):
                if component in state.l0_lexeme_set:
                    continue
                if self._term_in_allowed_state(state, component):
                    continue
                self._park(
                    state,
                    result,
                    parse.item_id,
                    "UNDEFINED_TERM_USE",
                    f"UNDEFINED_LEXEME:{component}",
                    batch_id,
                    item_class=parse.header,
                    item_text=parse.item_text,
                )
                return
        existing = state.term_registry.get(term_literal)
        if existing and existing.get("bound_math_def") != dep:
            self._reject(state, result, parse.item_id, "SHADOW_ATTEMPT", "TERM_DRIFT", batch_id)
            return
        term_tokens = [token for token_class, token in parse.asserts if token_class == "TERM_TOKEN"]
        if len(term_tokens) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "TERM_TOKEN_REQUIRED", batch_id)
            return
        state.term_registry[term_literal] = {
            "state": "TERM_PERMITTED",
            "bound_math_def": dep,
            "required_evidence": "",
            "provenance": parse.item_id,
        }
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, "ACTIVE", metadata=metadata)
        state.spec_meta[parse.item_id] = {"kind": "TERM_DEF", "term": term_literal, "bound_math_def": dep}

    def _admit_label_def(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        if len(parse.requires) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "LABEL_DEF_REQUIRES_ONE_TERM", batch_id)
            return
        dep = parse.requires[0]
        dep_kind = state.spec_meta.get(dep, {}).get("kind")
        if dep_kind != "TERM_DEF":
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "LABEL_DEF_REQUIRES_TERM_DEF", batch_id)
            return
        if "TERM" not in parse.fields or "LABEL" not in parse.fields:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "LABEL_DEF_FIELDS_MISSING", batch_id)
            return
        term_literal = parse.fields["TERM"][0].lower()
        label_tokens = [token for token_class, token in parse.asserts if token_class == "LABEL_TOKEN"]
        if len(label_tokens) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "LABEL_TOKEN_REQUIRED", batch_id)
            return
        entry = state.term_registry.get(term_literal)
        if entry is None:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "LABEL_DEF_UNKNOWN_TERM", batch_id)
            return
        if entry["state"] != "CANONICAL_ALLOWED":
            entry["state"] = "LABEL_PERMITTED"
            state.term_registry[term_literal] = entry
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, "ACTIVE", metadata=metadata)
        state.spec_meta[parse.item_id] = {"kind": "LABEL_DEF", "term": term_literal}

    def _admit_canon_permit(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        if len(parse.requires) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "CANON_PERMIT_REQUIRES_ONE_TERM_DEF", batch_id)
            return
        dep = parse.requires[0]
        dep_kind = state.spec_meta.get(dep, {}).get("kind")
        if dep_kind != "TERM_DEF":
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "CANON_PERMIT_REQUIRES_TERM_DEF", batch_id)
            return
        if "TERM" not in parse.fields or "REQUIRES_EVIDENCE" not in parse.fields:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "CANON_PERMIT_FIELDS_MISSING", batch_id)
            return
        term_literal = parse.fields["TERM"][0].lower()
        evidence_token = parse.fields["REQUIRES_EVIDENCE"][0]
        permit_tokens = [token for token_class, token in parse.asserts if token_class == "PERMIT_TOKEN"]
        if len(permit_tokens) != 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "PERMIT_TOKEN_REQUIRED", batch_id)
            return
        entry = state.term_registry.get(term_literal)
        if entry is None:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "CANON_PERMIT_UNKNOWN_TERM", batch_id)
            return
        entry["required_evidence"] = evidence_token
        if evidence_token in state.evidence_tokens:
            entry["state"] = "CANONICAL_ALLOWED"
            status = "ACTIVE"
        else:
            status = "PENDING_EVIDENCE"
            state.evidence_pending[parse.item_id] = {evidence_token}
        state.term_registry[term_literal] = entry
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, status, metadata=metadata)
        state.spec_meta[parse.item_id] = {"kind": "CANON_PERMIT", "term": term_literal, "evidence_token": evidence_token}

    def _admit_sim_spec(self, parse: _ItemParse, state: KernelState, result: dict, batch_id: str) -> None:
        evidence_values = parse.fields.get("REQUIRES_EVIDENCE", [])
        if len(evidence_values) == 0:
            self._park(
                state,
                result,
                parse.item_id,
                "SCHEMA_FAIL",
                "SIM_SPEC_REQUIRES_EVIDENCE_MISSING",
                batch_id,
                item_class=parse.header,
                item_text=parse.item_text,
            )
            return
        if len(evidence_values) > 1:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "SIM_SPEC_REQUIRES_EVIDENCE_MULTI", batch_id)
            return
        evidence_token = evidence_values[0]
        asserted = [token for token_class, token in parse.asserts if token_class == "EVIDENCE_TOKEN"]
        if len(asserted) != 1 or asserted[0] != evidence_token:
            self._reject(state, result, parse.item_id, "SCHEMA_FAIL", "SIM_SPEC_ASSERT_EVIDENCE_MISMATCH", batch_id)
            return
        status = "ACTIVE" if evidence_token in state.evidence_tokens else "PENDING_EVIDENCE"
        if status == "PENDING_EVIDENCE":
            state.evidence_pending[parse.item_id] = {evidence_token}
        metadata = {"kill_if_tokens": list(parse.kill_if_tokens), "kill_bind": parse.kill_bind}
        self._accept(state, result, parse.item_id, parse.header, parse.item_text, status, metadata=metadata)
        sim_id = parse.fields.get("SIM_ID", [parse.item_id])[0]
        tier = parse.fields.get("TIER", ["T0_ATOM"])[0]
        family = parse.fields.get("FAMILY", ["BASELINE"])[0]
        target_class = parse.fields.get("TARGET_CLASS", [parse.item_id])[0]
        negative_class = parse.fields.get("NEGATIVE_CLASS", [""])[0]
        depends_on = parse.fields.get("DEPENDS_ON", [])
        state.spec_meta[parse.item_id] = {
            "kind": "SIM_SPEC",
            "sim_id": sim_id,
            "evidence_token": evidence_token,
            "tier": tier,
            "family": family,
            "target_class": target_class,
            "negative_class": negative_class,
            "depends_on": list(depends_on),
            "is_negative": bool(negative_class),
        }
        state.sim_registry[sim_id] = {
            "spec_id": parse.item_id,
            "tier": tier,
            "family": family,
            "target_class": target_class,
            "negative_class": negative_class,
            "depends_on": list(depends_on),
            "evidence_token": evidence_token,
        }
        if sim_id not in state.sim_promotion_status:
            state.sim_promotion_status[sim_id] = "NOT_READY"
        self._record_probe_references(state, parse.requires)

    def _parse_item(self, item: dict, state: KernelState) -> _ItemParse | None:
        header = item.get("header", "")
        item_id = item.get("id", "")
        lines = item.get("lines", [])
        if not lines:
            return None
        axiom_kind = ""
        probe_kind = ""
        spec_kind = ""
        requires: list[str] = []
        asserts: list[tuple[str, str]] = []
        fields: dict[str, list[str]] = {}
        formulas: list[str] = []
        term_literals: list[str] = []
        label_literals: list[str] = []
        kill_if_tokens: list[str] = []
        kill_bind = ""
        for line in lines[1:]:
            if not line:
                continue
            match = AXIOM_KIND_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                axiom_kind = match.group(2)
                continue
            match = PROBE_KIND_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                probe_kind = match.group(2)
                continue
            match = SPEC_KIND_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                spec_kind = match.group(2)
                continue
            match = REQUIRES_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                requires.append(match.group(2))
                continue
            match = ASSERT_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                token_class = match.group(2)
                token_value = match.group(3)
                if token_class not in TOKEN_CLASS_VALUES:
                    return None
                asserts.append((token_class, token_value))
                continue
            match = KILL_IF_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                kill_if_tokens.append(match.group(2))
                continue
            match = TERM_LINE_REGEX.match(line)
            if match and match.group(1) == item_id:
                fields.setdefault("TERM", []).append(match.group(2))
                term_literals.append(match.group(2))
                continue
            match = LABEL_LINE_REGEX.match(line)
            if match and match.group(1) == item_id:
                fields.setdefault("LABEL", []).append(match.group(2))
                label_literals.append(match.group(2))
                continue
            match = FORMULA_LINE_REGEX.match(line)
            if match and match.group(1) == item_id:
                fields.setdefault("FORMULA", []).append(match.group(2))
                formulas.append(match.group(2))
                continue
            match = SIM_HASH_LINE_REGEX.match(line)
            if match and match.group(1) == item_id:
                fields.setdefault("SIM_CODE_HASH_SHA256", []).append(match.group(2).lower())
                continue
            match = FIELD_REGEX.match(line)
            if match:
                if match.group(1) != item_id:
                    return None
                field_name = match.group(2)
                field_value = match.group(3).strip()
                fields.setdefault(field_name, []).append(field_value)
                if field_name == "KILL_BIND" and not kill_bind:
                    kill_bind = field_value
                continue
            if line.startswith("WITNESS ") or line.startswith("KILL_IF "):
                continue
            return None
        return _ItemParse(
            item_id=item_id,
            header=header,
            item_text="\n".join(lines),
            axiom_kind=axiom_kind,
            probe_kind=probe_kind,
            spec_kind=spec_kind,
            requires=requires,
            asserts=asserts,
            fields=fields,
            formulas=formulas,
            term_literals=term_literals,
            label_literals=label_literals,
            kill_if_tokens=kill_if_tokens,
            kill_bind=kill_bind,
        )

    def _line_fence_check(self, parse: _ItemParse, state: KernelState) -> _LineViolation | None:
        for line in parse.item_text.splitlines():
            is_term = TERM_LINE_REGEX.match(line) is not None
            is_label = LABEL_LINE_REGEX.match(line) is not None
            formula_match = FORMULA_LINE_REGEX.match(line)
            is_formula = formula_match is not None
            if is_formula:
                formula = formula_match.group(2)
                non_ascii = NON_ASCII_REGEX.search(formula)
                if non_ascii:
                    return _LineViolation("SCHEMA_FAIL", "BR-0F4", line, non_ascii.group(0))
                unknown_glyph = self._find_formula_unknown_glyph(formula)
                if unknown_glyph:
                    return _LineViolation("GLYPH_NOT_PERMITTED", "BR-0F6", line, unknown_glyph)
                missing_glyph = self._find_formula_missing_glyph_term(formula, state)
                if missing_glyph:
                    return _LineViolation("GLYPH_NOT_PERMITTED", "BR-0F5", line, missing_glyph)
                for token in LOWER_TOKEN_REGEX.findall(formula):
                    for segment in token.split("_"):
                        segment = segment.lower()
                        if segment.isdigit():
                            continue
                        if segment in state.l0_lexeme_set:
                            continue
                        if self._term_in_allowed_state(state, segment):
                            continue
                        return _LineViolation("UNDEFINED_TERM_USE", "BR-0F1", line, segment)
                    for segment in token.split("_"):
                        segment = segment.lower()
                        if segment in state.derived_only_terms and not self._term_canonical(state, segment):
                            return _LineViolation("DERIVED_ONLY_NOT_PERMITTED", "BR-0F2", line, segment)
                if "=" in formula and not self._term_canonical(state, "equals_sign"):
                    return _LineViolation("DERIVED_ONLY_NOT_PERMITTED", "BR-0F3", line, "=")
                if any(ch.isdigit() for ch in formula) and not self._term_canonical(state, "digit_sign"):
                    return _LineViolation("DERIVED_ONLY_NOT_PERMITTED", "BR-0F7", line, "digit_sign")
                continue

            payload = self._line_payload_for_scan(line)
            if not payload:
                continue
            non_ascii = NON_ASCII_REGEX.search(payload)
            if non_ascii:
                return _LineViolation("SCHEMA_FAIL", "BR-0U2", line, non_ascii.group(0))
            mixed_case = MIXED_CASE_TOKEN_REGEX.search(payload)
            if mixed_case:
                return _LineViolation("SCHEMA_FAIL", "BR-0U3", line, mixed_case.group(0))
            if "=" in payload:
                return _LineViolation("UNQUOTED_EQUAL", "BR-008", line, "=")
            if is_term or is_label:
                continue
            derived_literal = self._find_derived_only_violation(payload, state)
            if derived_literal:
                return _LineViolation("DERIVED_ONLY_PRIMITIVE_USE", "BR-0D1", line, derived_literal)
            undefined_literal = self._find_undefined_token(payload, state)
            if undefined_literal:
                return _LineViolation("UNDEFINED_TERM_USE", "BR-0U1", line, undefined_literal)
            digit_literal = self._find_digit_guard_violation(payload, state)
            if digit_literal:
                return _LineViolation("DERIVED_ONLY_NOT_PERMITTED", "BR-0D2", line, digit_literal)
            glyph_literal = self._find_glyph_violation(payload, state)
            if glyph_literal:
                return _LineViolation("GLYPH_NOT_PERMITTED", "BR-0U4", line, glyph_literal)
        return None

    def _line_payload_for_scan(self, line: str) -> str:
        if line.startswith(("AXIOM_HYP ", "PROBE_HYP ", "SPEC_HYP ")):
            return ""
        match = AXIOM_KIND_REGEX.match(line)
        if match:
            return ""
        match = PROBE_KIND_REGEX.match(line)
        if match:
            return ""
        match = SPEC_KIND_REGEX.match(line)
        if match:
            return ""
        match = REQUIRES_REGEX.match(line)
        if match:
            return ""
        match = ASSERT_REGEX.match(line)
        if match:
            return ""
        match = FIELD_REGEX.match(line)
        if match:
            field_name = match.group(2)
            if field_name in {"TERM", "LABEL", "FORMULA", "SIM_CODE_HASH_SHA256"}:
                return ""
            return match.group(3).strip()
        if line.startswith("WITNESS ") or line.startswith("KILL_IF "):
            parts = line.split()
            if len(parts) >= 4:
                return parts[-1]
        return ""

    def _find_undefined_token(self, payload: str, state: KernelState) -> str:
        for token in LOWER_TOKEN_REGEX.findall(payload):
            for segment in token.split("_"):
                segment = segment.lower()
                if segment.isdigit():
                    continue
                if segment in state.l0_lexeme_set:
                    continue
                if self._term_in_allowed_state(state, segment):
                    continue
                return segment
        return ""

    def _find_derived_only_violation(self, payload: str, state: KernelState) -> str:
        for token in LOWER_TOKEN_REGEX.findall(payload):
            for segment in token.split("_"):
                segment = segment.lower()
                if segment in state.derived_only_terms and not self._term_canonical(state, segment):
                    return segment
        return ""

    def _find_digit_guard_violation(self, payload: str, state: KernelState) -> str:
        for token in LOWER_TOKEN_REGEX.findall(payload):
            for segment in token.split("_"):
                segment = segment.lower()
                if re.search(r"[a-z]", segment) and re.search(r"[0-9]", segment):
                    if not self._term_canonical(state, "digit_sign"):
                        return segment
        return ""

    def _find_glyph_violation(self, payload: str, state: KernelState) -> str:
        for char in payload:
            if char.isalnum() or char.isspace() or char in {'"', "_"}:
                continue
            required_term = state.formula_glyph_requirements.get(char)
            if not required_term:
                return char
            if not self._term_canonical(state, required_term):
                return char
        return ""

    def _find_formula_unknown_glyph(self, formula: str) -> str:
        allowed = {
            "+",
            "-",
            "*",
            "/",
            "^",
            "~",
            "!",
            "[",
            "]",
            "{",
            "}",
            "(",
            ")",
            "<",
            ">",
            "|",
            "&",
            ",",
            ":",
            ".",
        }
        for char in formula:
            if char.isalnum() or char.isspace() or char in {"_", "="}:
                continue
            if char not in allowed:
                return char
        return ""

    def _find_formula_missing_glyph_term(self, formula: str, state: KernelState) -> str:
        for char in formula:
            if char not in state.formula_glyph_requirements:
                continue
            required_term = state.formula_glyph_requirements[char]
            if not self._term_canonical(state, required_term):
                return char
        return ""

    def _term_in_allowed_state(self, state: KernelState, term: str) -> bool:
        entry = state.term_registry.get(term.lower())
        return bool(entry and entry.get("state") in CANON_TERM_STATES)

    def _term_canonical(self, state: KernelState, term: str) -> bool:
        entry = state.term_registry.get(term.lower())
        return bool(entry and entry.get("state") == "CANONICAL_ALLOWED")

    def _id_namespace_ok(self, header: str, item_id: str) -> bool:
        if header == "AXIOM_HYP":
            return item_id.startswith(("F", "W", "K", "M"))
        if header == "PROBE_HYP":
            return item_id.startswith("P")
        if header == "SPEC_HYP":
            return item_id.startswith(("S", "R"))
        return False

    def _is_near_duplicate(self, parse: _ItemParse, state: KernelState) -> bool:
        token_set_new = self._tokens_for_jaccard(parse.item_text)
        for existing in state.survivor_ledger.values():
            if existing.get("class") != parse.header:
                continue
            token_set_old = self._tokens_for_jaccard(existing.get("item_text", ""))
            union = token_set_new | token_set_old
            if not union:
                continue
            score = len(token_set_new & token_set_old) / float(len(union))
            if score > 0.80:
                return True
        return False

    def _tokens_for_jaccard(self, text: str) -> set[str]:
        return set(re.findall(r"[A-Za-z0-9_]+", text.lower()))

    def _accept(
        self,
        state: KernelState,
        result: dict,
        item_id: str,
        item_class: str,
        item_text: str,
        status: str,
        metadata: dict | None = None,
    ) -> None:
        metadata = metadata or {}
        state.survivor_ledger[item_id] = {"class": item_class, "status": status, "item_text": item_text, "metadata": metadata}
        if item_id not in state.survivor_order:
            state.survivor_order.append(item_id)
        result["accepted"].append({"id": item_id, "class": item_class, "status": status})

    def _park(
        self,
        state: KernelState,
        result: dict,
        item_id: str,
        tag: str,
        detail: str,
        batch_id: str,
        item_class: str = "",
        item_text: str = "",
    ) -> None:
        norm_tag = self._tag(tag)
        state.park_set[item_id] = {
            "id": item_id,
            "class": item_class,
            "item_text": item_text,
            "tag": norm_tag,
            "detail": detail,
        }
        result["parked"].append({"id": item_id, "reason": norm_tag, "detail": detail})
        state.reject_log.append({"batch_id": batch_id, "tag": norm_tag, "detail": detail})

    def _reject(
        self,
        state: KernelState,
        result: dict,
        item_id: str,
        tag: str,
        detail: str,
        batch_id: str,
        offender_rule: str = "",
        offender_line: str = "",
        offender_literal: str = "",
    ) -> None:
        norm_tag = self._tag(tag)
        row = {"id": item_id, "reason": norm_tag, "detail": detail}
        if offender_rule:
            row["offender_rule"] = offender_rule
        if offender_line:
            row["offender_line"] = offender_line
        if offender_literal:
            row["offender_literal"] = offender_literal
        if norm_tag == "SCHEMA_FAIL" and "offender_rule" not in row:
            row["offender_rule"] = "STAGE_2_SCHEMA_CHECK"
        result["rejected"].append(row)
        log_entry = {"batch_id": batch_id, "tag": norm_tag, "detail": detail}
        if offender_rule:
            log_entry["offender_rule"] = offender_rule
        if offender_line:
            log_entry["offender_line"] = offender_line
        if offender_literal:
            log_entry["offender_literal"] = offender_literal
        if norm_tag == "SCHEMA_FAIL" and "offender_rule" not in log_entry:
            log_entry["offender_rule"] = "STAGE_2_SCHEMA_CHECK"
        state.reject_log.append(log_entry)

    def _tag(self, tag: str) -> str:
        if tag in ALLOWED_TAGS:
            return tag
        return "SCHEMA_FAIL"

    def _finalize_batch(self, state: KernelState, old_hash: str, accepted_any: bool) -> None:
        if accepted_any:
            state.accepted_batch_count += 1
            self._apply_probe_utilization(state)
        new_hash = state.hash()
        if new_hash == old_hash:
            state.unchanged_ledger_streak += 1
        else:
            state.unchanged_ledger_streak = 0

    def _record_probe_references(self, state: KernelState, requires: list[str]) -> None:
        batch_index = state.accepted_batch_count + 1
        for dep in requires:
            meta = state.probe_meta.get(dep)
            if not meta:
                continue
            existing = int(meta.get("first_referenced_batch", 0) or 0)
            if existing == 0 or batch_index < existing:
                meta["first_referenced_batch"] = batch_index
                state.probe_meta[dep] = meta

    def _apply_probe_utilization(self, state: KernelState) -> None:
        current_batch = state.accepted_batch_count
        for probe_id in sorted(state.probe_meta.keys()):
            meta = state.probe_meta[probe_id]
            if meta.get("status") == "PARKED_UNUSED":
                continue
            admitted_batch = int(meta.get("admitted_batch", 0) or 0)
            if admitted_batch <= 0:
                continue
            if current_batch < admitted_batch + 3:
                continue
            first_ref = int(meta.get("first_referenced_batch", 0) or 0)
            if first_ref and admitted_batch <= first_ref <= admitted_batch + 3:
                meta["utilization_checked"] = True
                state.probe_meta[probe_id] = meta
                continue
            if probe_id in state.survivor_ledger:
                probe_row = state.survivor_ledger.pop(probe_id)
                state.survivor_order = [entry for entry in state.survivor_order if entry != probe_id]
                state.park_set[probe_id] = {
                    "id": probe_id,
                    "class": probe_row.get("class", "PROBE_HYP"),
                    "item_text": probe_row.get("item_text", ""),
                    "tag": "UNUSED_PROBE",
                    "detail": "BR-010",
                }
                state.reject_log.append({"batch_id": "AUTO_PROBE_UTILIZATION", "tag": "UNUSED_PROBE", "detail": f"ID:{probe_id}"})
            meta["status"] = "PARKED_UNUSED"
            meta["utilization_checked"] = True
            state.probe_meta[probe_id] = meta

    def _apply_probe_pressure(self, state: KernelState, result: dict, batch_id: str) -> None:
        accepted_specs = [entry for entry in result["accepted"] if entry.get("class") == "SPEC_HYP"]
        accepted_probes = [entry for entry in result["accepted"] if entry.get("class") == "PROBE_HYP"]
        spec_count = len(accepted_specs)
        probe_count = len(accepted_probes)
        if spec_count == 0:
            return
        required_probes = (spec_count + 9) // 10
        if probe_count >= required_probes:
            return
        keep_specs = probe_count * 10
        park_needed = max(0, spec_count - keep_specs)
        if park_needed <= 0:
            return
        parked_ids = set()
        for accepted in reversed(result["accepted"]):
            if accepted.get("class") != "SPEC_HYP":
                continue
            item_id = accepted.get("id", "")
            if item_id in parked_ids:
                continue
            parked_ids.add(item_id)
            survivor = state.survivor_ledger.get(item_id, {})
            state.park_set[item_id] = {
                "id": item_id,
                "class": survivor.get("class", "SPEC_HYP"),
                "item_text": survivor.get("item_text", ""),
                "tag": "PROBE_PRESSURE",
                "detail": "BR-009",
            }
            state.reject_log.append({"batch_id": batch_id, "tag": "PROBE_PRESSURE", "detail": f"ID:{item_id}"})
            result["parked"].append({"id": item_id, "reason": "PROBE_PRESSURE", "detail": "BR-009"})
            if item_id in state.survivor_ledger:
                del state.survivor_ledger[item_id]
            state.survivor_order = [entry for entry in state.survivor_order if entry != item_id]
            park_needed -= 1
            if park_needed == 0:
                break
        if parked_ids:
            result["accepted"] = [entry for entry in result["accepted"] if entry.get("id") not in parked_ids]

    def _apply_kill_signal(self, state: KernelState, sim_id: str, target_id: str, cond_token: str, batch_id: str) -> None:
        entry = state.survivor_ledger.get(target_id)
        if entry is None:
            return
        metadata = entry.get("metadata", {})
        kill_tokens = set(metadata.get("kill_if_tokens", []))
        if cond_token not in kill_tokens:
            return
        kill_bind = metadata.get("kill_bind", "")
        if kill_bind:
            if sim_id != kill_bind:
                return
        else:
            if sim_id != target_id:
                return
        if entry.get("status") == "KILLED":
            return
        entry["status"] = "KILLED"
        state.survivor_ledger[target_id] = entry
        state.kill_log.append({"batch_id": batch_id, "id": target_id, "tag": "KILL_SIGNAL", "token": cond_token})
        state.evidence_pending.pop(target_id, None)
