#!/usr/bin/env python3
"""rosetta_reattach.py -- the MISSING reattach module (strip -> ratchet -> REATTACH).

The strip side (a1_rosetta_stripper / b_kernel routing / rosetta_v2) takes a jargon/narrative
concept down to a jargon-free L0 object that rides the ratchet; every gate IGNORES the jargon.
This module is the EXIT side that was absent: it hangs MANY probe-relative correspondences off
ONE admitted L0 survivor.

ROOT DISCIPLINE (structural, not advisory):
  - There is NO equals sign in this system. No universals. Every object is a perspectival story.
  - A reattach is `jargon ~_M kernel` (a probe-relative correspondence), NEVER `jargon = kernel`.
  - relation_symbol is a frozen "~_M". A record is INVALID without a non-empty probe_family_M AND
    non-empty `preserves` AND non-empty `erases` -- an equality has no erasure record, so by
    construction every admitted reattach NAMES WHAT IT LOSES.
  - Strip is one-to-one (jargon -> L0). Reattach is one-to-MANY (L0 -> a plural fan). There is no
    `primary_label` and no scalar "true name"; perspectives() returns the whole fan.
  - Many jargon types / models / hypotheses coexist as distinct rows; none merges, none promotes.
  - Reattach is READ-ONLY decoration on an already-admitted survivor; it NEVER feeds back into a
    gate (no jargon-laundering promotion path).

This module is standalone-runnable (no repo imports) so its behaviour is verifiable; the dataclasses
mirror rosetta_v2's typed-packet classes (OVERLAY_ALIAS / SENSE_CANDIDATE / KERNEL_BINDING) and are
intended to be wired into rosetta_v2's RosettaStore.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

import re as _re

RELATION = "~_M"  # frozen; the ONLY admissible reattach relation
_FORBIDDEN_RELATION_WORDS = {"=", "==", "is", "isa", "equals", "equal", "identical", "identicaltwin",
                             "kernelidentity", "same", "samewise", "equalsbaseline", "truename"}
_VACUOUS_TEXT = {"", ".", "-", "--", "n/a", "na", "none", "nothing", "tbd", "todo", "...", "unpinned",
                 "unknown", "x", "?", "etc"}


def _norm(s):
    return _re.sub(r"[^a-z0-9]+", "", str(s).strip().lower())


def _is_vacuous(s):
    """Empty / placeholder / pure-punctuation text -- not a substantive field."""
    if str(s).strip().lower() in _VACUOUS_TEXT:
        return True
    return _norm(s) == ""  # nothing but punctuation / whitespace


def _is_vacuous_probe(m):
    """A probe family that names no actual probe -- degrades back to '='."""
    if _is_vacuous(m) or str(m).strip().lower() in {"generic", "general", "any"}:
        return True
    inner = _re.findall(r"\{([^}]*)\}", str(m))  # M={...} brace content
    if inner and all(_is_vacuous(x) or _norm(x) in {"unpinned", "todo", "tbd", "anything", "x", "placeholder"} for x in inner):
        return True
    return False


def _asserts_identity(label):
    """True if the label is (or contains) an identity assertion, however punctuated."""
    if "=" in str(label):
        return True
    n = _norm(label)
    if n in _FORBIDDEN_RELATION_WORDS:
        return True
    return any(stem in n for stem in ("equal", "identic", "samewis", "isa", "truename", "kernelidentity"))


class EqualsSignError(ValueError):
    """Raised when a reattach tries to assert an identity instead of a ~_M correspondence."""


@dataclass(frozen=True)
class ErasureRecord:
    """What the strip dropped -- enough to reattach as a correspondence, not a flat word list.

    Replaces a1_rosetta_stripper's flat `dropped_jargon: list[str]` (structurally irreversible:
    you cannot reconstruct a correspondence from a bag of removed words). Here each dropped item
    keeps its jargon_type, the model/tradition it came from, and the probe family under which it
    was indistinguishable from the kernel object -- so reattach is a lossless-as-a-correspondence
    inverse, never an identity.
    """
    jargon_token: str
    jargon_type: str          # e.g. "jungian_function" | "igt_winlose" | "iching_line" | "mbti" | "physics_overlay"
    model: str                # the tradition/source/model the jargon belongs to
    probe_family_M: str       # the probes under which jargon_token ~_M the kernel object
    preserves: str            # the structure the correspondence keeps
    erases: str               # the structure it drops (MUST be non-empty)
    hypothesis_id: str = "H0"


@dataclass(frozen=True)
class StripResult:
    l0_object_id: str         # the jargon-free kernel object that rides the ratchet
    provenance_token: str     # opaque; rides through; NO gate reads it
    erasures: tuple            # tuple[ErasureRecord, ...]


@dataclass(frozen=True)
class CorrespondenceRecord:
    """One probe-relative perspective hung off an L0 survivor. NOT an identity."""
    object_id: str            # the L0 survivor
    perspective_label: str    # the jargon name (e.g. "Ti", "WinWin", "Hexagram 1 line 1")
    jargon_type: str
    model: str
    probe_family_M: str
    preserves: str
    erases: str
    hypothesis_id: str = "H0"
    claim_ceiling: str = "perspective_only"   # never promotes the L0 survivor
    relation_symbol: str = RELATION

    def __post_init__(self):
        if self.relation_symbol != RELATION:
            raise EqualsSignError(
                f"relation_symbol must be '{RELATION}', got {self.relation_symbol!r}: "
                "this system has no equals sign / no universals."
            )
        if _asserts_identity(self.perspective_label):
            raise EqualsSignError(f"perspective_label {self.perspective_label!r} asserts an identity")
        if _is_vacuous_probe(self.probe_family_M):
            raise EqualsSignError(
                f"probe_family_M {self.probe_family_M!r} names no actual probe -- a vacuous/placeholder "
                "probe family silently degrades back to '='. Name the probes."
            )
        if _is_vacuous(self.preserves):
            raise EqualsSignError(f"preserves {self.preserves!r} is vacuous -- name what the correspondence keeps")
        if _is_vacuous(self.erases):
            raise EqualsSignError(
                f"erases {self.erases!r} is vacuous -- an equality has no erasure record. Name what is lost."
            )
        # no '=' may hide in any semantic field (probe_family_M excluded: it is a formula slot)
        for fld in ("perspective_label", "model", "jargon_type", "preserves", "erases"):
            if "=" in str(getattr(self, fld)):
                raise EqualsSignError(f"field {fld} contains '=' (identity assertion): {getattr(self, fld)!r}")

    def render(self) -> str:
        return (f"{self.perspective_label} ~_M[{self.probe_family_M}] {self.object_id}  "
                f"(model={self.model}, type={self.jargon_type}, hyp={self.hypothesis_id}; "
                f"preserves={self.preserves}; erases={self.erases}; ceiling={self.claim_ceiling})")


class RosettaCarrier:
    """Holds the L0 survivor + its plural ~_M perspective fan. No primary label, no true name."""

    def __init__(self, l0_object_id: str, provenance_token: str):
        self.l0_object_id = l0_object_id
        self.provenance_token = provenance_token
        self._records: list[CorrespondenceRecord] = []
        self.verdict: Optional[dict] = None  # stamped back by the ratchet via the token

    def add_perspective(self, rec: CorrespondenceRecord) -> None:
        if rec.object_id != self.l0_object_id:
            raise ValueError("correspondence object_id does not match this carrier's L0 object")
        self._records.append(rec)  # plural: never replaces, never picks a winner

    def perspectives(self) -> list[CorrespondenceRecord]:
        return list(self._records)

    def perspectives_by(self, jargon_type: Optional[str] = None, model: Optional[str] = None,
                        hypothesis_id: Optional[str] = None) -> list[CorrespondenceRecord]:
        out = self._records
        if jargon_type is not None:
            out = [r for r in out if r.jargon_type == jargon_type]
        if model is not None:
            out = [r for r in out if r.model == model]
        if hypothesis_id is not None:
            out = [r for r in out if r.hypothesis_id == hypothesis_id]
        return list(out)


def mint_token(l0_object_id: str, erasures: tuple) -> str:
    """Content-addressed provenance token (deterministic; no Date/random)."""
    payload = l0_object_id + "|" + "|".join(sorted(e.jargon_token + ":" + e.model for e in erasures))
    return "tok_" + hashlib.sha256(payload.encode()).hexdigest()[:16]


def strip_with_erasure(l0_object_id: str, erasures: list) -> StripResult:
    """Strip side: produce the jargon-free L0 object + an erasure record (NOT a flat word list)."""
    er = tuple(erasures)
    return StripResult(l0_object_id=l0_object_id, provenance_token=mint_token(l0_object_id, er), erasures=er)


def reattach(strip: StripResult, verdict: dict,
             reattach_on_reject: bool = False) -> RosettaCarrier:
    """EXIT side: hang the plural ~_M fan off the survivor. One-to-many.

    reattach_on_reject (the held fork):
      False  (default, Design 2): a graveyarded L0 object reattaches NOTHING -- jargon never
             re-enters as a claim about a non-survivor.
      True   (Design 1): graveyarded objects ALSO reattach, but every correspondence inherits a
             'rejected' ceiling (graveyard-as-primary-output discipline on the jargon side).
    """
    accepted = bool(verdict.get("accepted", verdict.get("admitted", False)))
    carrier = RosettaCarrier(strip.l0_object_id, strip.provenance_token)
    carrier.verdict = verdict
    if not accepted and not reattach_on_reject:
        return carrier  # graveyarded: empty fan
    ceiling = "perspective_only" if accepted else "rejected_perspective_only"
    for e in strip.erasures:
        carrier.add_perspective(CorrespondenceRecord(
            object_id=strip.l0_object_id, perspective_label=e.jargon_token, jargon_type=e.jargon_type,
            model=e.model, probe_family_M=e.probe_family_M, preserves=e.preserves, erases=e.erases,
            hypothesis_id=e.hypothesis_id, claim_ceiling=ceiling,
        ))
    return carrier


def validate_no_equals(records) -> list:
    """Lint: returns a list of violations. Construction already forbids most; this catches
    hand-built/legacy records that bypassed the dataclass (e.g. plain dicts from qit_rosetta_tables)."""
    violations = []
    for i, r in enumerate(records):
        d = r if isinstance(r, dict) else asdict(r)
        rel = str(d.get("relation_symbol", "")).strip()
        if rel != RELATION:
            violations.append(f"[{i}] relation_symbol {rel!r} != '{RELATION}'")
        if _is_vacuous_probe(d.get("probe_family_M", "")):
            violations.append(f"[{i}] vacuous/placeholder probe_family_M -> degenerates to '='")
        if _is_vacuous(d.get("erases", "")):
            violations.append(f"[{i}] vacuous erases -> equality has no erasure record")
        if _is_vacuous(d.get("preserves", "")):
            violations.append(f"[{i}] vacuous preserves")
        if _asserts_identity(d.get("perspective_label", "")):
            violations.append(f"[{i}] perspective_label asserts an identity")
        # any semantic field literally containing '=' as an asserted identity
        for k in ("perspective_label", "kernel_identity", "model", "jargon_type", "preserves", "erases"):
            if "=" in str(d.get(k, "")):
                violations.append(f"[{i}] field {k} contains '=' (identity assertion)")
    return violations


# ── Typed-store wiring (rosetta_v2.RosettaStore) ──────────────────────────────
#
# The dataclasses above run standalone; this block is the ACTUAL wiring asked for:
# attach a RosettaCarrier perspective-fan onto an L0 object that is ALREADY STORED in
# a rosetta_v2.RosettaStore (reattach AFTER the ratchet). Each ~_M perspective is
# persisted as one typed RosettaPacket (SENSE_CANDIDATE) keyed to the stored L0 packet,
# never replacing it and never promoting it. A reattach packet carries:
#   object_class = SENSE_CANDIDATE   (one explicit reading; rosetta_v2's own class)
#   status       = PARKED            (a perspective NEVER promotes the L0 survivor)
#   source_term  = perspective_label (the jargon name)
#   the frozen CorrespondenceRecord is JSON-serialized into routing_reason behind a
#   marker prefix, so the round-trip is lossless and the stored row is a real ~_M record.

REATTACH_MARKER = "ROSETTA_REATTACH_v1::"   # tag + routing_reason prefix identifying a fan row


def _l0_object_id_for(store, l0_packet_id: str) -> str:
    """Resolve a STORED L0 packet's stable object id (its candidate_sense_id)."""
    pkt = store.get(l0_packet_id)
    if pkt is None:
        raise KeyError(f"L0 object {l0_packet_id!r} is not in the store -- reattach is AFTER the ratchet")
    return pkt.candidate_sense_id


def _record_to_packet(store, l0_packet_id: str, l0_object_id: str,
                      rec: "CorrespondenceRecord", index: int):
    """Build (but do not add) a typed RosettaPacket carrying one ~_M perspective row."""
    from rosetta_v2 import RosettaPacket  # local import: keeps this file standalone-runnable

    payload = asdict(rec)
    payload["_attached_to_packet"] = l0_packet_id
    pid = f"RST_REATTACH_{l0_packet_id}_{index}_{_norm(rec.perspective_label)}"
    return RosettaPacket(
        packet_id=pid,
        source_term=rec.perspective_label,
        source_context=rec.render(),
        object_class="SENSE_CANDIDATE",
        candidate_sense_id=f"{l0_object_id}::perspective::{rec.hypothesis_id}::{_norm(rec.perspective_label)}",
        source_tags=[REATTACH_MARKER + rec.jargon_type, "no_promote", rec.claim_ceiling],
        confidence_mode="structural",
        kernel_targets=[l0_object_id],
        probe_suggestions=[rec.probe_family_M],
        status="PARKED",   # a perspective never promotes the L0 survivor
        routing_reason=REATTACH_MARKER + json.dumps(payload, sort_keys=True),
    )


def _packet_payload(pkt) -> Optional[dict]:
    """RAW stored ~_M payload dict for a reattach packet (None if not one). Does NOT go through
    the dataclass, so a row that bypassed construction (hand-edited '=' / vacuous-M) is still
    returned -- that is exactly what the stored-row validator must lint."""
    rr = getattr(pkt, "routing_reason", "") or ""
    if not rr.startswith(REATTACH_MARKER):
        return None
    payload = json.loads(rr[len(REATTACH_MARKER):])
    payload.pop("_attached_to_packet", None)
    return payload


def _packet_to_record(pkt) -> Optional["CorrespondenceRecord"]:
    """Reconstruct a CorrespondenceRecord from a stored reattach packet (None if not one).
    Re-runs the dataclass guard, so a hand-edited bad row RAISES here -- use _packet_payload
    for lint-only reads that must survive a bad row."""
    payload = _packet_payload(pkt)
    if payload is None:
        return None
    return CorrespondenceRecord(**payload)


def attach_carrier_to_store(store, l0_packet_id: str, carrier: "RosettaCarrier",
                            save: bool = False) -> list:
    """Persist a RosettaCarrier's plural ~_M fan onto a STORED L0 object.

    One L0 -> many ~_M perspectives, no primary / no true-name: every perspective lands as
    its own SENSE_CANDIDATE row keyed to the stored L0 packet, none replacing any other.
    The L0 packet itself is NOT mutated (read-only decoration on an admitted survivor).
    Returns the list of stored RosettaPackets.
    """
    l0_object_id = _l0_object_id_for(store, l0_packet_id)
    stored = []
    for i, rec in enumerate(carrier.perspectives()):
        pkt = _record_to_packet(store, l0_packet_id, l0_object_id, rec, i)
        store.add_packet(pkt)
        stored.append(pkt)
    if save:
        store.save()
    return stored


def read_carrier_from_store(store, l0_packet_id: str) -> "RosettaCarrier":
    """Rebuild a RosettaCarrier (the plural fan) from the rows stored against an L0 object."""
    l0_object_id = _l0_object_id_for(store, l0_packet_id)
    l0_pkt = store.get(l0_packet_id)
    token = getattr(l0_pkt, "source_batch_id", "") or ""
    carrier = RosettaCarrier(l0_object_id, token)
    for pkt in store.packets.values():
        rec = _packet_to_record(pkt)
        if rec is not None and rec.object_id == l0_object_id:
            carrier.add_perspective(rec)
    return carrier


def reattach_into_store(store, l0_packet_id: str, strip: "StripResult", verdict: dict,
                        reattach_on_reject: bool = False, save: bool = False) -> "RosettaCarrier":
    """Full path: reattach the ~_M fan AFTER the ratchet, onto an L0 object already in the store.

    The graveyard fork is the reattach_on_reject flag (OFF default / ON_WITH_REJECTED_CEILING),
    delegated to reattach(): a rejected L0 stores NOTHING under OFF, or stores a fan with a
    'rejected_perspective_only' ceiling under ON. The stored L0 packet is never promoted.
    """
    if strip.l0_object_id != _l0_object_id_for(store, l0_packet_id):
        raise ValueError("strip.l0_object_id does not match the stored L0 object's candidate_sense_id")
    carrier = reattach(strip, verdict, reattach_on_reject=reattach_on_reject)
    attach_carrier_to_store(store, l0_packet_id, carrier, save=save)
    return carrier


def stored_correspondence_dicts(store, l0_packet_id: Optional[str] = None) -> list:
    """Pull every stored reattach row back to the ~_M dict shape validate_no_equals expects.

    If l0_packet_id is given, scope to that L0 object's fan; otherwise scan the whole store.
    """
    target_object_id = _l0_object_id_for(store, l0_packet_id) if l0_packet_id is not None else None
    out = []
    for pkt in store.packets.values():
        payload = _packet_payload(pkt)   # RAW: a bad row must reach the validator, not raise
        if payload is None:
            continue
        if target_object_id is not None and payload.get("object_id") != target_object_id:
            continue
        out.append(payload)
    return out


def validate_stored_correspondences(store, l0_packet_id: Optional[str] = None) -> list:
    """Run the no-equals validator over the STORED correspondence rows.

    A stored '=' / vacuous-probe / identity-label row is reported as a violation here even if
    it bypassed the dataclass guard (e.g. a hand-edited store JSON). Uses the hardened
    _is_vacuous_probe / _asserts_identity via validate_no_equals.
    """
    return validate_no_equals(stored_correspondence_dicts(store, l0_packet_id))


def _selftest() -> int:
    fails = []
    # 1. plural perspectives on one L0 object, many jargon types / models / hypotheses
    erasures = [
        ErasureRecord("Ti", "jungian_function", "jung_mbti", "M={z-basis dephasing channel D_z on a 2-state carrier}",
                      "the pinching/dephasing action on the z basis", "the felt introverted-thinking semantics, the type narrative", "H0"),
        ErasureRecord("WinWin", "igt_winlose", "igt_atlas", "M={unitary+conjugated frame readout pair}",
                      "the Si/closed-conjugated regime label", "the payoff-game semantics; the win/lose moral overlay", "H0"),
        ErasureRecord("Hexagram1.line1", "iching_line", "iching_rosetta", "M={Axis-6 up/down precedence probe}",
                      "the line-position ordering", "the divinatory meaning", "H1"),  # a DIFFERENT hypothesis
    ]
    strip = strip_with_erasure("L0::z_dephasing_then_conjugated_frame", erasures)
    carrier = reattach(strip, {"accepted": True})
    if len(carrier.perspectives()) != 3:
        fails.append("expected 3 plural perspectives")
    if len(carrier.perspectives_by(hypothesis_id="H1")) != 1:
        fails.append("hypothesis filter failed")
    if any(getattr(r, "relation_symbol") != RELATION for r in carrier.perspectives()):
        fails.append("a perspective is not ~_M")

    # 2. an attempted equals-sign record must RAISE
    try:
        CorrespondenceRecord("L0::x", "Ti", "jung", "jung", "M={D_z}", "p", "e", relation_symbol="=")
        fails.append("equals-sign relation did not raise")
    except EqualsSignError:
        pass
    # 3. a generic probe family must RAISE (lazy reattach degrading to '=')
    try:
        CorrespondenceRecord("L0::x", "Ti", "jung", "jung", "generic", "p", "e")
        fails.append("generic probe_family_M did not raise")
    except EqualsSignError:
        pass
    # 4. empty erasure record must RAISE (equality has no erasure record)
    try:
        CorrespondenceRecord("L0::x", "Ti", "jung", "jung", "M={D_z}", "p", "")
        fails.append("empty erases did not raise")
    except EqualsSignError:
        pass
    # 5. graveyard policy fork: default = no reattach on reject; ON = rejected-ceiling fan
    g_off = reattach(strip, {"accepted": False})
    g_on = reattach(strip, {"accepted": False}, reattach_on_reject=True)
    if g_off.perspectives():
        fails.append("graveyard default should reattach nothing")
    if len(g_on.perspectives()) != 3 or any(r.claim_ceiling != "rejected_perspective_only" for r in g_on.perspectives()):
        fails.append("graveyard ON should reattach with rejected ceiling")
    # 6. lint catches a legacy '=' dict (e.g. qit_rosetta_tables kernel_identity)
    legacy = [{"relation_symbol": "=", "perspective_label": "Ti", "kernel_identity": "State reduction", "probe_family_M": "generic", "erases": ""}]
    if len(validate_no_equals(legacy)) < 3:
        fails.append("lint failed to catch legacy '=' record")

    # 7. WIRING: reattach into a real rosetta_v2.RosettaStore against a STORED L0 object,
    #    round-trip the fan back out, and validate the STORED rows. Uses a temp store so the
    #    repo store is untouched.
    store_rows = 0
    try:
        import sys as _sys, tempfile as _tempfile, os as _os
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from rosetta_v2 import RosettaStore, RosettaPacket  # noqa: F401

        with _tempfile.TemporaryDirectory() as _tmp:
            store = RosettaStore(_tmp)
            # an already-admitted (ratcheted) L0 object lives in the store as a BOUND packet
            l0 = RosettaPacket(
                packet_id="L0PKT", source_term="z_dephasing_then_conjugated_frame",
                source_context="ratcheted survivor", object_class="KERNEL_BINDING",
                candidate_sense_id="L0::z_dephasing_then_conjugated_frame",
                kernel_targets=["S_TERM_DEPHASE_CHANNEL"], status="BOUND",
            )
            store.add_packet(l0)

            # reattach AFTER the ratchet: one L0 -> many stored ~_M perspectives
            stored_carrier = reattach_into_store(store, "L0PKT", strip, {"accepted": True})
            store_rows = len(stored_correspondence_dicts(store, "L0PKT"))
            if store_rows != 3:
                fails.append(f"expected 3 stored perspective rows, got {store_rows}")
            # round-trip: rebuild the fan from the store and confirm plurality survives
            rebuilt = read_carrier_from_store(store, "L0PKT")
            if len(rebuilt.perspectives()) != 3:
                fails.append("stored fan did not round-trip to 3 perspectives")
            if len({r.perspective_label for r in rebuilt.perspectives()}) != 3:
                fails.append("stored perspectives collapsed (not distinct rows)")
            # the STORED rows pass the no-equals validator
            if validate_stored_correspondences(store, "L0PKT"):
                fails.append("clean stored correspondences flagged by validator")
            # the L0 packet itself was NOT mutated/promoted by reattach
            if store.get("L0PKT").status != "BOUND":
                fails.append("reattach mutated/promoted the stored L0 packet")

            # a hand-edited store with a stored '=' / vacuous-M / identity-label row is REJECTED
            bad = RosettaPacket(
                packet_id="RST_REATTACH_BAD", source_term="equals",
                source_context="hand-edited bad row", object_class="SENSE_CANDIDATE",
                candidate_sense_id="L0::z_dephasing_then_conjugated_frame::perspective::H9::equals",
                kernel_targets=["L0::z_dephasing_then_conjugated_frame"], status="PARKED",
                routing_reason=REATTACH_MARKER + json.dumps({
                    "object_id": "L0::z_dephasing_then_conjugated_frame",
                    "perspective_label": "equals", "jargon_type": "x", "model": "x",
                    "probe_family_M": "generic", "preserves": "p", "erases": "",
                    "hypothesis_id": "H9", "claim_ceiling": "perspective_only",
                    "relation_symbol": "=",
                }),
            )
            store.add_packet(bad)
            bad_violations = validate_stored_correspondences(store, "L0PKT")
            if not bad_violations:
                fails.append("stored '=' / vacuous-M / identity-label row was NOT rejected by validator")

            # graveyard fork on the STORE: OFF stores nothing, ON stores rejected-ceiling rows
            store2 = RosettaStore(_tmp + "_2") if False else RosettaStore(_tempfile.mkdtemp())
            store2.add_packet(l0)
            reattach_into_store(store2, "L0PKT", strip, {"accepted": False})  # OFF default
            if stored_correspondence_dicts(store2, "L0PKT"):
                fails.append("graveyard OFF stored rows on a rejected L0")
            store3 = RosettaStore(_tempfile.mkdtemp())
            store3.add_packet(l0)
            reattach_into_store(store3, "L0PKT", strip, {"accepted": False}, reattach_on_reject=True)
            g3 = read_carrier_from_store(store3, "L0PKT").perspectives()
            if len(g3) != 3 or any(r.claim_ceiling != "rejected_perspective_only" for r in g3):
                fails.append("graveyard ON did not store rejected-ceiling rows")
    except Exception as exc:  # surface wiring import/runtime failures rather than hiding them
        fails.append(f"store-wiring selftest raised: {type(exc).__name__}: {exc}")

    result = {
        "module": "rosetta_reattach",
        "selftest_pass": not fails,
        "failures": fails,
        "stored_perspective_rows": store_rows,
        "example_perspectives": [r.render() for r in carrier.perspectives()],
        "token": strip.provenance_token,
    }
    print(json.dumps(result, indent=2))
    return 0 if not fails else 1


if __name__ == "__main__":
    # accept an optional 'selftest' argument (no-op selector; kept for the harness call)
    raise SystemExit(_selftest())
