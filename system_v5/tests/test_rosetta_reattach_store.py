"""Could-fail tests for the Rosetta REATTACH wired into the typed RosettaStore.

Covers the EXIT side (strip -> ratchet -> REATTACH) operating on a STORED L0 object:
  - a stored fan returns PLURAL perspectives (no primary / no true-name);
  - an attempted '=' / vacuous-M / identity-label STORED correspondence is REJECTED;
  - a legit ~_M STORED correspondence is ACCEPTED;
  - multiple hypotheses coexist as DISTINCT stored rows;
  - the graveyard-reattach FORK (reattach_on_reject OFF default / ON_WITH_REJECTED_CEILING).

Each test is written to FAIL if the wiring silently degrades a perspective fan back to an
equality, drops a hypothesis, mutates/promotes the stored L0 survivor, or stores a bad row.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "system_v4" / "skills"


def _load(name: str):
    """Import a skills module by path, with the skills dir on sys.path so its sibling
    import (rosetta_reattach -> rosetta_v2) resolves."""
    import sys
    if str(SKILLS_DIR) not in sys.path:
        sys.path.insert(0, str(SKILLS_DIR))
    path = SKILLS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, f"{name}.py is missing"
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


reattach = _load("rosetta_reattach")
rosetta_v2 = _load("rosetta_v2")


def _stored_l0(store, *, packet_id="L0PKT",
               sense_id="L0::z_dephasing_then_conjugated_frame"):
    """Put an already-ratcheted (BOUND) L0 survivor into the store and return it."""
    pkt = rosetta_v2.RosettaPacket(
        packet_id=packet_id,
        source_term="z_dephasing_then_conjugated_frame",
        source_context="ratcheted survivor",
        object_class="KERNEL_BINDING",
        candidate_sense_id=sense_id,
        kernel_targets=["S_TERM_DEPHASE_CHANNEL"],
        status="BOUND",
    )
    store.add_packet(pkt)
    return pkt


def _three_erasures():
    E = reattach.ErasureRecord
    return [
        E("Ti", "jungian_function", "jung_mbti",
          "M={z-basis dephasing channel D_z on a 2-state carrier}",
          "the pinching/dephasing action on the z basis",
          "the felt introverted-thinking semantics", "H0"),
        E("WinWin", "igt_winlose", "igt_atlas",
          "M={unitary+conjugated frame readout pair}",
          "the Si/closed-conjugated regime label",
          "the win/lose moral overlay", "H0"),
        E("Hexagram1.line1", "iching_line", "iching_rosetta",
          "M={Axis-6 up/down precedence probe}",
          "the line-position ordering",
          "the divinatory meaning", "H1"),  # a DIFFERENT hypothesis
    ]


@pytest.fixture
def store(tmp_path):
    return rosetta_v2.RosettaStore(str(tmp_path))


# ── 1. a stored fan returns PLURAL perspectives, no primary / no true-name ─────

def test_stored_fan_returns_plural_perspectives(store):
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures())

    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": True})

    rows = reattach.stored_correspondence_dicts(store, l0.packet_id)
    assert len(rows) == 3, "stored fan collapsed below 3 perspectives (degraded to a single name)"

    rebuilt = reattach.read_carrier_from_store(store, l0.packet_id)
    labels = [r.perspective_label for r in rebuilt.perspectives()]
    assert sorted(labels) == ["Hexagram1.line1", "Ti", "WinWin"]
    # no primary / no true-name: every stored row is a ~_M correspondence, none is an '='
    assert all(r.relation_symbol == reattach.RELATION for r in rebuilt.perspectives())
    assert not reattach.validate_stored_correspondences(store, l0.packet_id)


def test_reattach_does_not_mutate_or_promote_the_stored_l0(store):
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures())
    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": True})
    # reattach is read-only decoration on the survivor: the L0 packet keeps its identity/status
    after = store.get(l0.packet_id)
    assert after.status == "BOUND", "reattach promoted the stored L0 survivor"
    assert after.object_class == "KERNEL_BINDING"
    assert after.candidate_sense_id == l0.candidate_sense_id


# ── 2. a legit ~_M stored correspondence is ACCEPTED ──────────────────────────

def test_legit_mtilde_stored_correspondence_is_accepted(store):
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures()[:1])
    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": True})

    violations = reattach.validate_stored_correspondences(store, l0.packet_id)
    assert violations == [], f"a clean ~_M stored correspondence was wrongly rejected: {violations}"
    rows = reattach.stored_correspondence_dicts(store, l0.packet_id)
    assert rows and rows[0]["relation_symbol"] == reattach.RELATION


# ── 3. an attempted '=' / vacuous-M / identity-label stored correspondence is REJECTED ─

def _store_raw_reattach_row(store, l0, payload, pid="RST_REATTACH_BAD"):
    """Bypass the dataclass and stuff a raw payload into the store the way a hand-edit would."""
    import json
    bad = rosetta_v2.RosettaPacket(
        packet_id=pid,
        source_term=str(payload.get("perspective_label", "bad")),
        source_context="hand-edited row",
        object_class="SENSE_CANDIDATE",
        candidate_sense_id=f"{l0.candidate_sense_id}::perspective::H9::bad",
        kernel_targets=[l0.candidate_sense_id],
        status="PARKED",
        routing_reason=reattach.REATTACH_MARKER + json.dumps(payload, sort_keys=True),
    )
    store.add_packet(bad)
    return bad


def _base_payload(l0, **over):
    p = {
        "object_id": l0.candidate_sense_id,
        "perspective_label": "Ti",
        "jargon_type": "jungian_function",
        "model": "jung_mbti",
        "probe_family_M": "M={z-basis dephasing channel}",
        "preserves": "the dephasing action",
        "erases": "the type narrative",
        "hypothesis_id": "H9",
        "claim_ceiling": "perspective_only",
        "relation_symbol": reattach.RELATION,
    }
    p.update(over)
    return p


def test_stored_equals_sign_row_is_rejected(store):
    l0 = _stored_l0(store)
    _store_raw_reattach_row(store, l0, _base_payload(l0, relation_symbol="="))
    violations = reattach.validate_stored_correspondences(store, l0.packet_id)
    assert violations, "a stored '=' correspondence was NOT rejected (silently degraded to equality)"


def test_stored_vacuous_probe_row_is_rejected(store):
    l0 = _stored_l0(store)
    _store_raw_reattach_row(store, l0, _base_payload(l0, probe_family_M="generic"))
    violations = reattach.validate_stored_correspondences(store, l0.packet_id)
    assert any("probe_family_M" in v for v in violations), \
        f"a vacuous probe family (de-facto '=') was NOT rejected: {violations}"


def test_stored_identity_label_row_is_rejected(store):
    l0 = _stored_l0(store)
    _store_raw_reattach_row(store, l0, _base_payload(l0, perspective_label="equals"))
    violations = reattach.validate_stored_correspondences(store, l0.packet_id)
    assert any("identity" in v for v in violations), \
        f"an identity-label perspective was NOT rejected: {violations}"


def test_dataclass_guard_rejects_equals_at_construction(store):
    """The strict side: a CorrespondenceRecord with '=' can never even be built, so it never
    reaches the store -- the validator is the second line of defence for hand-edits."""
    with pytest.raises(reattach.EqualsSignError):
        reattach.CorrespondenceRecord(
            "L0::x", "Ti", "jung", "jung", "M={D_z}", "p", "e", relation_symbol="=")
    with pytest.raises(reattach.EqualsSignError):
        reattach.CorrespondenceRecord("L0::x", "Ti", "jung", "jung", "generic", "p", "e")
    with pytest.raises(reattach.EqualsSignError):
        reattach.CorrespondenceRecord("L0::x", "Ti", "jung", "jung", "M={D_z}", "p", "")


# ── 4. multiple hypotheses coexist as DISTINCT stored rows ────────────────────

def test_multiple_hypotheses_coexist_as_distinct_rows(store):
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures())
    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": True})

    carrier = reattach.read_carrier_from_store(store, l0.packet_id)
    h0 = carrier.perspectives_by(hypothesis_id="H0")
    h1 = carrier.perspectives_by(hypothesis_id="H1")
    assert len(h0) == 2 and len(h1) == 1, "hypotheses did not coexist as distinct stored rows"
    # distinct rows: distinct candidate_sense_id per perspective in the store (no merge/overwrite)
    reattach_pkts = [p for p in store.packets.values()
                     if (p.routing_reason or "").startswith(reattach.REATTACH_MARKER)]
    sense_ids = {p.candidate_sense_id for p in reattach_pkts}
    assert len(sense_ids) == 3, "stored perspectives merged onto one row (lost plurality)"


# ── 5. the graveyard-reattach FORK ────────────────────────────────────────────

def test_graveyard_fork_off_default_stores_nothing(store):
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures())
    # rejected L0, default OFF: jargon never re-enters as a claim about a non-survivor
    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": False})
    assert reattach.stored_correspondence_dicts(store, l0.packet_id) == [], \
        "graveyard OFF stored perspective rows on a rejected L0"


def test_graveyard_fork_on_stores_rejected_ceiling_rows(store):
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures())
    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": False},
                                 reattach_on_reject=True)  # ON_WITH_REJECTED_CEILING
    carrier = reattach.read_carrier_from_store(store, l0.packet_id)
    persp = carrier.perspectives()
    assert len(persp) == 3, "graveyard ON did not store the full fan"
    assert all(r.claim_ceiling == "rejected_perspective_only" for r in persp), \
        "graveyard ON stored rows without the rejected ceiling (jargon would re-enter as a live claim)"
    # even rejected-ceiling rows are still ~_M correspondences, not equalities
    assert not reattach.validate_stored_correspondences(store, l0.packet_id)


# ── persistence round-trip (the store is the point: survive a save/reload) ─────

def test_stored_fan_survives_save_and_reload(tmp_path):
    store = rosetta_v2.RosettaStore(str(tmp_path))
    l0 = _stored_l0(store)
    strip = reattach.strip_with_erasure(l0.candidate_sense_id, _three_erasures())
    reattach.reattach_into_store(store, l0.packet_id, strip, {"accepted": True}, save=True)

    reloaded = rosetta_v2.RosettaStore(str(tmp_path))
    carrier = reattach.read_carrier_from_store(reloaded, l0.packet_id)
    assert len(carrier.perspectives()) == 3, "fan did not survive store save/reload"
    assert not reattach.validate_stored_correspondences(reloaded, l0.packet_id)
