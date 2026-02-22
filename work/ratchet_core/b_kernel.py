import hashlib
import json
import re
from pathlib import Path

from containers import parse_export_block, split_items


_QUOTED_RE = re.compile(r'"([^"]+)"')
_ALLOWED_CONTEXT_RE = re.compile(r'^\s*DEF_FIELD\s+\S+\s+CORR\s+(TERM|LABEL|FORMULA|STATEMENT|FORBIDS|PERMITS|OPEN)\s+"')
_SPEC_KIND_RE = re.compile(r'^SPEC_KIND\s+\S+\s+CORR\s+(\S+)')
_REQUIRES_RE = re.compile(r'^REQUIRES\s+\S+\s+CORR\s+(.+)$')
_DEF_TERM_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+TERM\s+"([^"]+)"')
_DEF_BINDS_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+BINDS\s+(\S+)')
_DEF_LABEL_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+LABEL\s+"([^"]+)"')
_DEF_TARGET_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+TARGET\s+(\S+)')
_DEF_REQUIRES_EVIDENCE_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+REQUIRES_EVIDENCE\s+(\S+)$')
_PROBE_KIND_RE = re.compile(r'^PROBE_KIND\s+\S+\s+CORR\s+(\S+)$')
_ASSERT_PROBE_RE = re.compile(r'^ASSERT\s+\S+\s+CORR\s+EXISTS\s+PROBE_TOKEN\s+(\S+)$')
_ASSERT_EVIDENCE_RE = re.compile(r'^ASSERT\s+\S+\s+CORR\s+EXISTS\s+EVIDENCE_TOKEN\s+(\S+)$')
_LOWER_TOKEN_RE = re.compile(r'[a-z][a-z0-9_]*')
_MIXED_ALNUM_RE = re.compile(r'[a-z].*[0-9]|[0-9].*[a-z]')
_FORMULA_RE = re.compile(r'^DEF_FIELD\s+\S+\s+CORR\s+FORMULA\s+"([^"]*)"')
_COMMENT_RE = re.compile(r'^\s*(#|//)')
_SIM_BEGIN_RE = re.compile(r'^BEGIN SIM_EVIDENCE v1$')
_SIM_END_RE = re.compile(r'^END SIM_EVIDENCE v1$')
_SIM_ID_RE = re.compile(r'^SIM_ID:?\s+(\S+)$')
_SIM_TARGET_RE = re.compile(r'^TARGET_SPEC:?\s+(\S+)$')
_SIM_TOKEN_RE = re.compile(r'^EVIDENCE_TOKEN:?\s+(\S+)$')
_SIM_CODE_HASH_RE = re.compile(r'^CODE_HASH_SHA256:\s*(\S+)$')
_SIM_OUTPUT_HASH_RE = re.compile(r'^OUTPUT_HASH_SHA256:\s*(\S+)$')
_SIM_INPUT_HASH_RE = re.compile(r'^INPUT_HASH_SHA256:\s*(\S+)$')
_SIM_MANIFEST_HASH_RE = re.compile(r'^RUN_MANIFEST_SHA256:\s*(\S+)$')
_SIM_METRIC_RE = re.compile(r'^METRIC:\s*([^=]+)=(\S+)$')
_SIM_EVIDENCE_SIGNAL_RE = re.compile(r'^EVIDENCE_SIGNAL\s+(\S+)\s+CORR\s+(\S+)$')
_SIM_KILL_SIGNAL_RE = re.compile(r'^KILL_SIGNAL\s+(\S+)\s+CORR\s+(\S+)$')


class BKernel:
    def __init__(self, bootpack_path):
        self.bootpack_path = bootpack_path
        self.lexeme_set = set()
        self.derived_only_terms = set()
        self.allowed_axioms = {"F01_FINITUDE", "N01_NONCOMMUTATION"}
        self.repo_root = None
        self.manifest_dir = None
        self.manifest_ledger_dir = None
        self._manifest_cache = None
        self._manifest_cache_root = None
        self._load_bootpack_lists()
        try:
            self.repo_root = Path(self.bootpack_path).resolve().parent
        except Exception:
            self.repo_root = None

    def _load_bootpack_lists(self):
        with open(self.bootpack_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        self.lexeme_set = set(self._collect_literals(lines, "INIT L0_LEXEME_SET"))
        derived = set(self._collect_literals(lines, "INIT DERIVED_ONLY_TERMS"))
        variants = set(self._collect_literals(lines, "Extend DERIVED_ONLY_TERMS"))
        self.derived_only_terms = set([t.lower() for t in derived.union(variants)])

    def _collect_literals(self, lines, marker):
        tokens = []
        i = 0
        while i < len(lines):
            if lines[i].strip().startswith(marker):
                j = i + 1
                while j < len(lines):
                    s = lines[j].strip()
                    if s.startswith("RULE") or s.startswith("STATE") or s.startswith("====") or s.startswith("CONTAINER"):
                        break
                    tokens.extend(_QUOTED_RE.findall(s))
                    j += 1
                i = j
            else:
                i += 1
        return tokens

    def evaluate_export_block(self, text, state, log_fn=None):
        block = parse_export_block(text)
        if state.active_ruleset_sha256:
            if not block.ruleset_sha256 or block.ruleset_sha256 != state.active_ruleset_sha256:
                self._reject_block("SCHEMA_FAIL", log_fn)
                return state
        if state.active_megaboot_sha256:
            if not block.megaboot_sha256 or block.megaboot_sha256 != state.active_megaboot_sha256:
                self._reject_block("KERNEL_ERROR", log_fn)
                return state
        items = split_items(block.content_lines)
        probe_ok_ids = set()
        for item in items:
            if item["header"] == "PROBE_HYP":
                if self._probe_schema_ok(item["lines"]):
                    probe_ok_ids.add(item["id"])
        accepted_spec_ids = set()
        accepted_spec_kind_by_id = {}
        accepted_term_literals = set(state.terms.keys())
        staged_accepts = []
        staged_parks = []

        for item in items:
            header = item["header"]
            item_id = item["id"]
            lines = item["lines"]

            if header == "AXIOM_HYP":
                if item_id not in self.allowed_axioms:
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue
                shadow_tag = self._shadow_attempt_violation(item_id, "AXIOM_HYP", lines, state)
                if shadow_tag:
                    self._reject(state, item_id, shadow_tag, log_fn, raw_lines=lines)
                    continue
                if item_id in state.axioms or item_id in state.specs:
                    self._reject(state, item_id, "OVERWRITE", log_fn, raw_lines=lines)
                    continue
                staged_accepts.append({"class": "AXIOM_HYP", "id": item_id, "lines": lines})
                continue

            if header == "PROBE_HYP":
                if item_id in state.specs or item_id in state.axioms:
                    self._reject(state, item_id, "OVERWRITE", log_fn, raw_lines=lines)
                    continue
                if not self._probe_schema_ok(lines):
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue
                staged_accepts.append({"class": "PROBE_HYP", "id": item_id, "lines": lines})
                continue

            if header != "SPEC_HYP":
                self._reject(state, item_id, "UNKNOWN_HEADER", log_fn, raw_lines=lines)
                continue

            if item_id in state.specs or item_id in state.axioms:
                self._reject(state, item_id, "OVERWRITE", log_fn, raw_lines=lines)
                continue

            spec_kind = self._parse_spec_kind(lines)
            if spec_kind not in {"MATH_DEF", "TERM_DEF", "LABEL_DEF", "CANON_PERMIT", "SIM_SPEC"}:
                self._reject(state, item_id, "SPEC_KIND_UNSUPPORTED", log_fn, raw_lines=lines)
                continue

            eq_tag = self._unquoted_equal_violation(lines)
            if eq_tag:
                self._reject(state, item_id, eq_tag, log_fn, raw_lines=lines)
                continue

            formula_tag = self._formula_equals_violation(lines, state)
            if formula_tag:
                self._reject(state, item_id, formula_tag, log_fn, raw_lines=lines)
                continue

            derived_tag = self._derived_only_violation(lines, state)
            if derived_tag:
                self._reject(state, item_id, derived_tag, log_fn, raw_lines=lines)
                continue

            digit_tag = self._digit_guard_violation(lines, state)
            if digit_tag:
                self._reject(state, item_id, digit_tag, log_fn, raw_lines=lines)
                continue

            undef_tag = self._undefined_term_violation(lines, state)
            if undef_tag:
                self._reject(state, item_id, undef_tag, log_fn, raw_lines=lines)
                continue

            deps = self._parse_dependencies(lines)
            if item_id in deps:
                self._reject(state, item_id, "CIRCULAR_DEPENDENCY", log_fn, raw_lines=lines)
                continue

            evidence_tokens = []
            if spec_kind == "SIM_SPEC":
                evidence_tokens = self._parse_requires_evidence(lines)
                if len(evidence_tokens) == 0:
                    staged_parks.append({"id": item_id, "reason": "SCHEMA_FAIL"})
                    continue
                if len(evidence_tokens) > 1:
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue
                if not any(_ASSERT_EVIDENCE_RE.match(l.strip()) for l in lines):
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue

            if not self._deps_satisfied(deps, state, accepted_spec_ids, probe_ok_ids):
                staged_parks.append({"id": item_id, "reason": "MISSING_DEPENDENCY"})
                continue

            term_literal = None
            binds = None
            label_literal = None
            if spec_kind == "TERM_DEF":
                term_literal = self._parse_term_literal(lines)
                binds = self._parse_binds(lines)
                if term_literal is None or binds is None:
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue
                if term_literal in state.terms:
                    existing = state.terms[term_literal]
                    if existing.get("binds") != binds or existing.get("spec_id") != item_id:
                        self._reject(state, item_id, "TERM_DRIFT", log_fn, raw_lines=lines)
                        continue
                    self._reject(state, item_id, "OVERWRITE", log_fn, raw_lines=lines)
                    continue
                if self._lexeme_fence_violation(term_literal, state, accepted_term_literals):
                    staged_parks.append({"id": item_id, "reason": "UNDEFINED_LEXEME"})
                    continue
            if spec_kind == "LABEL_DEF":
                term_literal = self._parse_term_literal(lines)
                label_literal = self._parse_label_literal(lines)
                if term_literal is None or label_literal is None:
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue
            if spec_kind == "CANON_PERMIT":
                term_literal = self._parse_term_literal(lines)
                evidence_tokens = self._parse_requires_evidence(lines)
                if term_literal is None or len(evidence_tokens) != 1:
                    self._reject(state, item_id, "SCHEMA_FAIL", log_fn, raw_lines=lines)
                    continue

            # No STRUCT_DEF or CONSTRAINT_DEF in bootpack v3.9.13

            # BR-007 NEAR_DUPLICATE check
            near_tag = self._near_redundant_violation(item_id, spec_kind, lines, state)
            if near_tag:
                staged_parks.append({"id": item_id, "reason": near_tag})
                continue

            pending = False
            if spec_kind == "SIM_SPEC":
                pending = True
            staged_accepts.append({
                "class": "SPEC_HYP",
                "id": item_id,
                "spec_kind": spec_kind,
                "deps": deps,
                "lines": lines,
                "term_literal": term_literal,
                "binds": binds,
                "permit_evidence": evidence_tokens[0] if spec_kind == "CANON_PERMIT" and len(evidence_tokens) == 1 else None,
                "evidence_tokens": evidence_tokens,
                "pending": pending,
            })
            if not pending:
                accepted_spec_ids.add(item_id)
                accepted_spec_kind_by_id[item_id] = spec_kind

        # Probe pressure enforcement (per batch) after staging accepts
        spec_accepts = [a for a in staged_accepts if a["class"] == "SPEC_HYP"]
        probe_accepts = [a for a in staged_accepts if a["class"] == "PROBE_HYP"]
        allowed_specs = len(probe_accepts) * 10 + 9
        if len(spec_accepts) > allowed_specs:
            # park newest specs first until ratio satisfied
            to_park = len(spec_accepts) - allowed_specs
            for a in reversed(staged_accepts):
                if to_park <= 0:
                    break
                if a["class"] == "SPEC_HYP":
                    staged_parks.append({"id": a["id"], "reason": "PROBE_PRESSURE"})
                    a["parked"] = True
                    to_park -= 1

        # Commit accepts
        for a in staged_accepts:
            if a.get("parked"):
                continue
            if a["class"] == "AXIOM_HYP":
                state.add_axiom(a["id"], "AXIOM_HYP", a["lines"])
                self._log(log_fn, "accept", {"id": a["id"], "class": "AXIOM_HYP"})
            elif a["class"] == "PROBE_HYP":
                added = state.add_spec(a["id"], "PROBE_HYP", [], a["lines"])
                if added:
                    state.probe_count += 1
                self._log(log_fn, "accept", {"id": a["id"], "class": "PROBE_HYP"})
            else:
                status = "ACTIVE"
                if a.get("pending"):
                    status = "PENDING_EVIDENCE"
                added = state.add_spec(a["id"], a["spec_kind"], a["deps"], a["lines"], status=status)
                if not added:
                    self._reject(state, a["id"], "OVERWRITE", log_fn, raw_lines=a["lines"])
                    continue
                if a.get("pending"):
                    token = a.get("evidence_tokens")[0]
                    state.evidence_pending[a["id"]] = set([token])
                if a["spec_kind"] == "CANON_PERMIT":
                    term = a.get("term_literal")
                    tok = a.get("permit_evidence")
                    if term and tok and term in state.terms:
                        state.set_term_required_evidence(term, tok)
                        if self._evidence_token_seen(state, tok):
                            state.set_term_state(term, "CANONICAL_ALLOWED")
                if a["spec_kind"] == "TERM_DEF":
                    if not state.add_term(a["term_literal"], a["id"], a["binds"]):
                        self._reject(state, a["id"], "TERM_DRIFT", log_fn, raw_lines=a["lines"])
                        continue
                    accepted_term_literals.add(a["term_literal"])
                self._log(log_fn, "accept", {"id": a["id"], "class": "SPEC_HYP", "kind": a["spec_kind"]})

        for p in staged_parks:
            state.parked.append({"id": p["id"], "reason": p["reason"]})
            self._log(log_fn, "park", {"id": p["id"], "reason": p["reason"]})

        return state

    def evaluate_message(self, text, state, log_fn=None):
        lines = text.splitlines()
        non_empty = [l for l in lines if l.strip() != ""]
        if not non_empty:
            self._reject_message("MULTI_ARTIFACT_OR_PROSE", log_fn)
            return state

        if all(l.startswith("REQUEST ") for l in non_empty):
            self._log(log_fn, "accept", {"class": "COMMAND_MESSAGE"})
            return state

        # Artifact message: comment ban
        for line in non_empty:
            if _COMMENT_RE.match(line):
                self._reject_message("COMMENT_BAN", log_fn)
                return state

        first = non_empty[0].strip()
        last = non_empty[-1].strip()

        if first.startswith("BEGIN EXPORT_BLOCK"):
            if not last.startswith("END EXPORT_BLOCK"):
                self._reject_message("MULTI_ARTIFACT_OR_PROSE", log_fn)
                return state
            try:
                self.evaluate_export_block(text, state, log_fn=log_fn)
                return state
            except ValueError:
                self._reject_message("SCHEMA_FAIL", log_fn)
                return state

        if first.startswith("BEGIN THREAD_S_SAVE_SNAPSHOT v2"):
            if last != "END THREAD_S_SAVE_SNAPSHOT v2":
                self._reject_message("MULTI_ARTIFACT_OR_PROSE", log_fn)
                return state
            ok = self.ingest_snapshot(text, state, log_fn=log_fn)
            if ok:
                self._log(log_fn, "accept", {"class": "THREAD_S_SAVE_SNAPSHOT"})
            return state

        if first.startswith("BEGIN SIM_EVIDENCE v1"):
            ok = self.ingest_sim_evidence_pack(text, state, log_fn=log_fn)
            if ok:
                self._log(log_fn, "accept", {"class": "SIM_EVIDENCE_PACK"})
            return state

        self._reject_message("MULTI_ARTIFACT_OR_PROSE", log_fn)
        return state

    def ingest_sim_evidence(self, text, state, log_fn=None):
        lines = [l.strip() for l in text.splitlines() if l.strip() != ""]
        if not lines or not _SIM_BEGIN_RE.match(lines[0]) or not _SIM_END_RE.match(lines[-1]):
            self._log(log_fn, "sim_reject", {"reason": "SIM_EVIDENCE_FORMAT"})
            return False
        sim_id = None
        target_spec = None
        token = None
        code_hash = None
        output_hash = None
        input_hash = None
        manifest_hash = None
        metrics = {}
        evidence_signals = []
        for line in lines[1:-1]:
            m = _SIM_ID_RE.match(line)
            if m:
                sim_id = m.group(1)
                continue
            m = _SIM_CODE_HASH_RE.match(line)
            if m:
                code_hash = m.group(1)
                continue
            m = _SIM_OUTPUT_HASH_RE.match(line)
            if m:
                output_hash = m.group(1)
                continue
            m = _SIM_INPUT_HASH_RE.match(line)
            if m:
                input_hash = m.group(1)
                continue
            m = _SIM_MANIFEST_HASH_RE.match(line)
            if m:
                manifest_hash = m.group(1)
                continue
            m = _SIM_METRIC_RE.match(line)
            if m:
                metrics[m.group(1)] = m.group(2)
                continue
            m = _SIM_EVIDENCE_SIGNAL_RE.match(line)
            if m:
                evidence_signals.append((m.group(1), m.group(2)))
                continue
            if _SIM_KILL_SIGNAL_RE.match(line):
                continue
            m = _SIM_TARGET_RE.match(line)
            if m:
                target_spec = m.group(1)
                continue
            m = _SIM_TOKEN_RE.match(line)
            if m:
                token = m.group(1)
                continue
        if sim_id is None or code_hash is None or output_hash is None or input_hash is None or manifest_hash is None:
            self._log(log_fn, "sim_reject", {"reason": "SIM_EVIDENCE_MISSING_FIELD"})
            return False

        if not self._verify_manifest(sim_id, code_hash, output_hash, input_hash, manifest_hash):
            self._log(log_fn, "sim_reject", {"reason": "SCHEMA_FAIL"})
            return False

        # Policy sign gates
        if sim_id == "S_RULESET_HASH":
            ruleset_hash = metrics.get("ruleset_sha256")
            if ruleset_hash:
                state.active_ruleset_sha256 = ruleset_hash
        if sim_id == "S_MEGA_BOOT_HASH":
            has_signal = any(sig == "S_MEGA_BOOT_HASH" and tok == "E_MEGA_BOOT_HASH" for sig, tok in evidence_signals)
            if has_signal:
                if not code_hash:
                    self._log(log_fn, "sim_reject", {"reason": "SIM_EVIDENCE_MISSING_FIELD"})
                    return False
                state.active_megaboot_sha256 = code_hash
                state.active_megaboot_id = metrics.get("megaboot_id", "")

        # Evidence satisfaction
        for sig_id, sig_token in evidence_signals:
            pending = state.evidence_pending.get(sig_id)
            if pending and sig_token in pending:
                pending.remove(sig_token)
                if not pending:
                    state.evidence_pending.pop(sig_id, None)
                    if sig_id in state.specs:
                        state.specs[sig_id]["status"] = "ACTIVE"
                        ev = state.specs[sig_id].get("evidence_tokens")
                        if ev is None:
                            ev = set()
                            state.specs[sig_id]["evidence_tokens"] = ev
                        ev.add(sig_token)
            self._apply_term_evidence(state, sig_token)

        # Legacy evidence path (TARGET_SPEC/EVIDENCE_TOKEN)
        if target_spec is not None and token is not None:
            if target_spec not in state.specs:
                self._log(log_fn, "sim_reject", {"reason": "TARGET_MISSING", "target": target_spec})
                return False
            spec = state.specs[target_spec]
            ev = spec.get("evidence_tokens")
            if ev is None:
                ev = set()
                spec["evidence_tokens"] = ev
            ev.add(token)
            self._apply_term_evidence(state, token)
            self._log(log_fn, "sim_accept", {"sim_id": sim_id, "target": target_spec, "token": token})
            return True

        self._log(log_fn, "sim_accept", {"sim_id": sim_id, "code_hash": code_hash, "output_hash": output_hash})
        return True

    def ingest_sim_evidence_pack(self, text, state, log_fn=None):
        lines = text.splitlines()
        blocks = []
        current = []
        in_block = False
        for line in lines:
            if line.strip() == "BEGIN SIM_EVIDENCE v1":
                if in_block:
                    self._reject_message("MULTI_ARTIFACT_OR_PROSE", log_fn)
                    return False
                in_block = True
                current = [line]
                continue
            if in_block:
                current.append(line)
                if line.strip() == "END SIM_EVIDENCE v1":
                    blocks.append("\n".join(current))
                    in_block = False
                continue
            if line.strip() != "":
                self._reject_message("MULTI_ARTIFACT_OR_PROSE", log_fn)
                return False
        if in_block or not blocks:
            self._reject_message("SCHEMA_FAIL", log_fn)
            return False
        for block in blocks:
            if not self.ingest_sim_evidence(block, state, log_fn=log_fn):
                self._reject_message("SCHEMA_FAIL", log_fn)
                return False
        return True

    def ingest_snapshot(self, text, state, log_fn=None):
        lines = text.splitlines()
        if not lines or lines[0].strip() != "BEGIN THREAD_S_SAVE_SNAPSHOT v2" or lines[-1].strip() != "END THREAD_S_SAVE_SNAPSHOT v2":
            self._reject_message("SCHEMA_FAIL", log_fn)
            return False
        # This method only validates the container structure for acceptance as a message.
        # It does NOT load the state (that is a boot operation, not a kernel message operation).
        section = None
        ledger_ids = []
        park_ids = []
        term_literals = []
        for line in lines[1:-1]:
            stripped = line.strip()
            if stripped in {"SURVIVOR_LEDGER:", "PARK_SET:", "TERM_REGISTRY:", "EVIDENCE_PENDING:", "PROVENANCE:"}:
                section = stripped
                continue
            if section == "SURVIVOR_LEDGER:":
                if stripped.startswith(("AXIOM_HYP ", "SPEC_HYP ", "PROBE_HYP ")):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        ledger_ids.append(parts[1])
            elif section == "PARK_SET:":
                if stripped.startswith(("AXIOM_HYP ", "SPEC_HYP ", "PROBE_HYP ")):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        park_ids.append(parts[1])
            elif section == "TERM_REGISTRY:":
                if stripped.startswith("TERM "):
                    parts = stripped.split()
                    if len(parts) >= 2:
                        term_literals.append(parts[1])

        if not ledger_ids:
            self._reject_message("SNAPSHOT_NONVERBATIM", log_fn)
            return False
        if ledger_ids != sorted(ledger_ids):
            self._reject_message("SCHEMA_FAIL", log_fn)
            return False
        if park_ids and park_ids != sorted(park_ids):
            self._reject_message("SCHEMA_FAIL", log_fn)
            return False
        if term_literals and term_literals != sorted(term_literals):
            self._reject_message("SCHEMA_FAIL", log_fn)
            return False
        return True

    def strict_ingest_snapshot(self, text, state, log_fn=None):
        """
        Boot-time utility to strictly ingest a snapshot file.
        Replays the SURVIVOR_LEDGER items through the kernel validators.
        Discards invalid items (hallucinations).
        """
        lines = text.splitlines()
        if not lines or not lines[0].strip().startswith("BEGIN THREAD_S_SAVE_SNAPSHOT"):
            if log_fn: log_fn({"event": "boot_error", "reason": "BAD_HEADER"})
            return False

        # Extract SURVIVOR_LEDGER lines
        ledger_lines = []
        in_ledger = False
        for line in lines:
            stripped = line.strip()
            if stripped == "SURVIVOR_LEDGER:":
                in_ledger = True
                continue
            if in_ledger:
                if stripped in {"PARK_SET:", "TERM_REGISTRY:", "EVIDENCE_PENDING:", "PROVENANCE:", "---"}:
                    break
                ledger_lines.append(line)
        
        items = split_items(ledger_lines)
        accepted_count = 0
        rejected_count = 0
        
        # Pre-scan for accepted IDs to handle dependencies
        # In a snapshot, items should be ordered, but we build the sets as we go.
        accepted_spec_ids = set()
        probe_ok_ids = set()
        accepted_term_literals = set()

        for item in items:
            header = item["header"]
            item_id = item["id"]
            lines = item["lines"]
            
            # 1. Axioms
            if header == "AXIOM_HYP":
                if item_id in self.allowed_axioms:
                    state.add_axiom(item_id, "AXIOM_HYP", lines)
                    accepted_count += 1
                else:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, "UNKNOWN_AXIOM", lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": "UNKNOWN_AXIOM"})
                continue

            # 2. Probes
            if header == "PROBE_HYP":
                if self._probe_schema_ok(lines):
                    state.add_spec(item_id, "PROBE_HYP", [], lines)
                    state.probe_count += 1
                    probe_ok_ids.add(item_id)
                    accepted_count += 1
                else:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, "BAD_PROBE_SCHEMA", lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": "BAD_PROBE_SCHEMA"})
                continue

            # 3. Specs
            if header == "SPEC_HYP":
                # Run all validators
                spec_kind = self._parse_spec_kind(lines)
                if not spec_kind:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, "NO_SPEC_KIND", lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": "NO_SPEC_KIND"})
                    continue

                # Check violations
                v = self._unquoted_equal_violation(lines)
                if v:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, v, lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": v})
                    continue
                v = self._formula_equals_violation(lines, state)
                if v:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, v, lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": v})
                    continue
                v = self._derived_only_violation(lines, state)
                if v:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, v, lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": v})
                    continue
                v = self._digit_guard_violation(lines, state)
                if v:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, v, lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": v})
                    continue
                v = self._undefined_term_violation(lines, state)
                if v:
                    rejected_count += 1
                    state.add_to_graveyard(item_id, v, lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": v})
                    continue
                
                # Check deps
                deps = self._parse_dependencies(lines)
                if not self._deps_satisfied(deps, state, accepted_spec_ids, probe_ok_ids):
                    rejected_count += 1
                    state.add_to_graveyard(item_id, "MISSING_DEP", lines)
                    if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": "MISSING_DEP"})
                    continue

                # Term checks
                if spec_kind == "TERM_DEF":
                    term_literal = self._parse_term_literal(lines)
                    binds = self._parse_binds(lines)
                    if not term_literal or not binds:
                        rejected_count += 1
                        state.add_to_graveyard(item_id, "BAD_TERM_DEF", lines)
                        if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": "BAD_TERM_DEF"})
                        continue
                    if self._lexeme_fence_violation(term_literal, state, accepted_term_literals):
                        rejected_count += 1
                        state.add_to_graveyard(item_id, "UNDEFINED_LEXEME", lines)
                        if log_fn: log_fn({"event": "boot_reject", "id": item_id, "reason": "UNDEFINED_LEXEME"})
                        continue
                    state.add_term(term_literal, item_id, binds)
                    accepted_term_literals.add(term_literal)

                # Add to state
                state.add_spec(item_id, spec_kind, deps, lines)
                accepted_spec_ids.add(item_id)
                accepted_count += 1
        
        if log_fn:
            log_fn({"event": "boot_complete", "accepted": accepted_count, "rejected": rejected_count})
        return True

    def _parse_spec_kind(self, lines):
        for line in lines:
            m = _SPEC_KIND_RE.match(line.strip())
            if m:
                return m.group(1)
        return None

    def _parse_dependencies(self, lines):
        deps = []
        for line in lines:
            m = _REQUIRES_RE.match(line.strip())
            if m:
                tail = m.group(1).strip()
                parts = re.split(r"[\s,]+", tail)
                deps.extend([p for p in parts if p])
            m2 = _DEF_BINDS_RE.match(line.strip())
            if m2:
                deps.append(m2.group(1))
        return deps

    def _parse_term_literal(self, lines):
        for line in lines:
            m = _DEF_TERM_RE.match(line.strip())
            if m:
                return m.group(1)
        return None

    def _parse_label_literal(self, lines):
        for line in lines:
            m = _DEF_LABEL_RE.match(line.strip())
            if m:
                return m.group(1)
        return None

    def _parse_binds(self, lines):
        for line in lines:
            m = _DEF_BINDS_RE.match(line.strip())
            if m:
                return m.group(1)
        return None

    def _parse_target(self, lines):
        for line in lines:
            m = _DEF_TARGET_RE.match(line.strip())
            if m:
                return m.group(1)
        return None

    def _parse_requires_evidence(self, lines):
        tokens = []
        for line in lines:
            m = _DEF_REQUIRES_EVIDENCE_RE.match(line.strip())
            if m:
                tokens.append(m.group(1))
        return tokens

    def _load_manifest_cache(self, force_reload=False):
        if not self.manifest_ledger_dir:
            return {}
        root = str(self.manifest_ledger_dir)
        if not force_reload and self._manifest_cache is not None and self._manifest_cache_root == root:
            return self._manifest_cache
        cache = {}
        try:
            ledger_dir = Path(self.manifest_ledger_dir)
            for shard in sorted(ledger_dir.glob("manifests.*.jsonl")):
                with shard.open("r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        row = json.loads(line)
                        digest = row.get("manifest_sha256")
                        if not digest:
                            continue
                        payload = dict(row)
                        payload.pop("manifest_sha256", None)
                        payload.pop("record_index", None)
                        cache[digest] = payload
        except Exception:
            cache = {}
        self._manifest_cache = cache
        self._manifest_cache_root = root
        return cache

    def _verify_manifest(self, sim_id, code_hash, output_hash, input_hash, manifest_hash):
        if not self.repo_root and not self.manifest_dir and not self.manifest_ledger_dir:
            return False
        try:
            payload = None
            manifest_path = None
            if self.manifest_dir:
                candidate = Path(self.manifest_dir) / f"{manifest_hash}.json"
                if candidate.exists():
                    manifest_path = candidate
            if manifest_path is None and self.repo_root:
                fallback = Path(self.repo_root) / "sim_evidence_store" / "manifests" / f"{manifest_hash}.json"
                if fallback.exists():
                    manifest_path = fallback

            if manifest_path is not None and manifest_path.exists():
                data = manifest_path.read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                if digest != manifest_hash:
                    return False
                payload = json.loads(data.decode("utf-8"))
            elif self.manifest_ledger_dir:
                payload = self._load_manifest_cache().get(manifest_hash)
                if not payload:
                    payload = self._load_manifest_cache(force_reload=True).get(manifest_hash)
                if not payload:
                    return False
                payload_data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
                digest = hashlib.sha256(payload_data).hexdigest()
                if digest != manifest_hash:
                    return False
            else:
                return False

            if payload.get("sim_id") != sim_id:
                return False
            if payload.get("code_hash_sha256") != code_hash:
                return False
            if payload.get("output_hash_sha256") != output_hash:
                return False
            if payload.get("input_hash_sha256") != input_hash:
                return False
            return True
        except Exception:
            return False

    def _token_set(self, lines):
        """Extract non-schema lowercase tokens from item lines for Jaccard comparison."""
        _SCHEMA_WORDS = {"spec_hyp", "probe_hyp", "axiom_hyp", "spec_kind", "requires",
                         "def_field", "assert", "corr", "exists", "probe_kind", "binds"}
        tokens = set()
        for line in lines:
            for tok in _LOWER_TOKEN_RE.findall(line.strip()):
                for seg in tok.split("_"):
                    if seg and seg not in _SCHEMA_WORDS and len(seg) > 1:
                        tokens.add(seg)
        return tokens

    def _near_redundant_violation(self, item_id, item_class, lines, state):
        """BR-007: Jaccard > 0.80 with existing item of same class => NEAR_REDUNDANT."""
        new_tokens = self._token_set(lines)
        if not new_tokens:
            return None
        for existing_id, existing in state.specs.items():
            if existing_id == item_id:
                continue
            existing_class = existing.get("kind", "")
            if existing_class != item_class:
                continue
            existing_lines = existing.get("raw_lines", existing.get("lines", []))
            if not existing_lines:
                continue
            existing_tokens = self._token_set(existing_lines)
            if not existing_tokens:
                continue
            intersection = len(new_tokens & existing_tokens)
            union = len(new_tokens | existing_tokens)
            if union > 0 and (intersection / union) > 0.80:
                return "NEAR_REDUNDANT"
        return None

    def _shadow_attempt_violation(self, item_id, item_class, lines, state):
        """BR-004: Duplicate axiom ID with different content => SHADOW_ATTEMPT (kill)."""
        if item_class != "AXIOM_HYP":
            return None
        if item_id not in state.axioms:
            return None
        existing_lines = state.axioms[item_id].get("raw_lines", state.axioms[item_id].get("lines", []))
        new_content = "\n".join(l.strip() for l in lines)
        existing_content = "\n".join(l.strip() for l in existing_lines)
        if new_content != existing_content:
            return "SHADOW_ATTEMPT"
        return None

    def _deps_satisfied(self, deps, state, accepted_spec_ids, accepted_probe_ids=None):
        accepted_probe_ids = accepted_probe_ids or set()
        for dep in deps:
            if dep in accepted_spec_ids:
                continue
            if dep in accepted_probe_ids:
                continue
            # Axioms are always considered satisfied (they are immutable admitted facts)
            if dep in state.axioms:
                continue
            if dep in state.specs:
                if state.specs[dep].get("status") == "ACTIVE":
                    continue
                return False
            return False
        return True

    def _derived_only_violation(self, lines, state):
        nonword_terms = [t for t in self.derived_only_terms if re.search(r"[^a-z0-9_]", t)]
        for line in lines:
            if _ALLOWED_CONTEXT_RE.match(line.strip()):
                continue
            for t in nonword_terms:
                if t and t in line and not self._term_state_ok(state, t, {"CANONICAL_ALLOWED"}):
                    return "DERIVED_ONLY_PRIMITIVE_USE"
            tokens = _LOWER_TOKEN_RE.findall(line)
            for tok in tokens:
                for seg in tok.split("_"):
                    if not seg:
                        continue
                    if seg in self.derived_only_terms and not self._term_state_ok(state, seg, {"CANONICAL_ALLOWED"}):
                        return "DERIVED_ONLY_PRIMITIVE_USE"
        return None

    def _unquoted_equal_violation(self, lines):
        for line in lines:
            stripped = line.strip()
            if _ALLOWED_CONTEXT_RE.match(stripped):
                continue
            if _FORMULA_RE.match(stripped):
                continue
            if self._has_unquoted_equal(stripped):
                return "UNQUOTED_EQUAL"
        return None

    def _formula_equals_violation(self, lines, state):
        for line in lines:
            stripped = line.strip()
            m = _FORMULA_RE.match(stripped)
            if not m:
                continue
            formula_text = m.group(1)
            if "=" in formula_text and not self._term_state_ok(state, "equals_sign", {"CANONICAL_ALLOWED"}):
                return "DERIVED_ONLY_NOT_PERMITTED"
        return None

    def _has_unquoted_equal(self, line):
        in_quotes = False
        for ch in line:
            if ch == '"':
                in_quotes = not in_quotes
                continue
            if ch == "=" and not in_quotes:
                return True
        return False

    def _lexeme_fence_violation(self, term_literal, state, accepted_term_literals):
        if "_" not in term_literal:
            return False
        components = term_literal.split("_")
        for comp in components:
            if not comp:
                continue
            if comp.isdigit():
                continue
            if comp in self.lexeme_set:
                continue
            if comp in accepted_term_literals:
                continue
            if self._term_state_ok(state, comp, {"TERM_PERMITTED", "LABEL_PERMITTED", "CANONICAL_ALLOWED"}):
                continue
            return True
        return False

    def _undefined_term_violation(self, lines, state):
        for line in lines:
            if _ALLOWED_CONTEXT_RE.match(line.strip()):
                continue
            if "SIM_CODE_HASH_SHA256" in line:
                continue
            tokens = _LOWER_TOKEN_RE.findall(line)
            for tok in tokens:
                for seg in tok.split("_"):
                    if not seg:
                        continue
                    if seg.isdigit():
                        continue
                    if seg in self.lexeme_set:
                        continue
                    if self._term_state_ok(state, seg, {"TERM_PERMITTED", "LABEL_PERMITTED", "CANONICAL_ALLOWED"}):
                        continue
                    return "UNDEFINED_TERM_USE"
        return None

    def _digit_guard_violation(self, lines, state):
        if self._term_state_ok(state, "digit_sign", {"CANONICAL_ALLOWED"}):
            return None
        for line in lines:
            if _ALLOWED_CONTEXT_RE.match(line.strip()):
                continue
            if "SIM_CODE_HASH_SHA256" in line:
                continue
            tokens = _LOWER_TOKEN_RE.findall(line)
            for tok in tokens:
                for seg in tok.split("_"):
                    if not seg:
                        continue
                    if _MIXED_ALNUM_RE.search(seg):
                        return "DERIVED_ONLY_NOT_PERMITTED"
        return None

    def _term_state_ok(self, state, term_literal, allowed_states):
        info = state.terms.get(term_literal)
        if not info:
            return False
        return info.get("state", "TERM_PERMITTED") in allowed_states

    def _apply_term_evidence(self, state, evidence_token):
        if not evidence_token:
            return
        for term_literal in sorted(state.terms.keys()):
            info = state.terms.get(term_literal, {})
            if info.get("required_evidence") == evidence_token:
                state.set_term_state(term_literal, "CANONICAL_ALLOWED")

    def _evidence_token_seen(self, state, evidence_token):
        if not evidence_token:
            return False
        for _, spec in state.specs.items():
            if evidence_token in spec.get("evidence_tokens", set()):
                return True
        return False

    def _probe_schema_ok(self, lines):
        has_kind = False
        has_token = False
        for line in lines:
            if _PROBE_KIND_RE.match(line.strip()):
                has_kind = True
            if _ASSERT_PROBE_RE.match(line.strip()):
                has_token = True
        return has_kind and has_token

    def _probe_pressure_violation(self, spec_in_batch, probe_in_batch):
        allowed = probe_in_batch * 10 + 9
        return (spec_in_batch + 1) > allowed

    def _reject(self, state, item_id, reason, log_fn, raw_lines=None):
        # raw_lines is crucial for resurrection
        state.add_to_graveyard(item_id, reason, raw_lines or [])
        self._log(log_fn, "reject", {"id": item_id, "reason": reason})

    def _park(self, state, item_id, reason, log_fn):
        state.parked.append({"id": item_id, "reason": reason})
        self._log(log_fn, "park", {"id": item_id, "reason": reason})

    def _reject_message(self, reason, log_fn):
        self._log(log_fn, "reject", {"id": "MESSAGE", "reason": reason})

    def _reject_block(self, reason, log_fn):
        self._log(log_fn, "reject", {"id": "EXPORT_BLOCK", "reason": reason})

    def _log(self, log_fn, event, payload):
        if log_fn:
            log_fn({"event": event, **payload})
