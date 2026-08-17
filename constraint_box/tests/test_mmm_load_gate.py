from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from constraintbox.mmm_load_gate import (
    MmmLoadError,
    compose_packs,
    confirm_job_mmm,
    confirm_mmm_load,
    materialize_bound_prompt,
)


DEFAULT_PACKS = ("nominalist", "smt")


def mmm_bind(
    prompt_path: Path, extra: str = "test", packs: tuple[str, ...] = DEFAULT_PACKS
) -> dict[str, object]:
    text = compose_packs(list(packs))
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    prompt_path.write_text(text + "\n\n" + extra, encoding="utf-8")
    return {"mmm_packs": list(packs), "mmm_sha256": digest}


def test_confirm_matches_recomputed_bytes_in_prompt() -> None:
    text = compose_packs(["nominalist", "smt"])
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    prompt = (text + "\n\nwork").encode("utf-8")
    confirmed = confirm_mmm_load(
        {"mmm_packs": ["nominalist", "smt"], "mmm_sha256": digest},
        prompt,
    )
    assert confirmed["mmm_load_confirmed"] is True
    assert confirmed["mmm_sha256"] == digest
    assert confirmed["mmm_packs"] == ["nominalist", "smt"]
    assert confirmed["mmm_bytes"] == len(text.encode("utf-8"))


def test_missing_fields_refuse() -> None:
    with pytest.raises(MmmLoadError) as caught:
        confirm_mmm_load({"schema": "x"}, b"prompt")
    assert caught.value.reason_code == "REFUSE_MMM_LOAD_MISSING"


def test_unknown_pack_refuses() -> None:
    with pytest.raises(MmmLoadError) as caught:
        confirm_mmm_load(
            {
                "mmm_packs": ["not-a-pack"],
                "mmm_sha256": "0" * 64,
            },
            b"prompt",
        )
    assert caught.value.reason_code == "REFUSE_MMM_PACKS_INVALID"


def test_hash_mismatch_refuses() -> None:
    text = compose_packs(["nominalist"])
    with pytest.raises(MmmLoadError) as caught:
        confirm_mmm_load(
            {"mmm_packs": ["nominalist"], "mmm_sha256": "a" * 64},
            text.encode("utf-8"),
        )
    assert caught.value.reason_code == "REFUSE_MMM_SHA256_MISMATCH"


def test_declared_hash_without_pack_text_in_prompt_refuses() -> None:
    text = compose_packs(["nominalist"])
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    with pytest.raises(MmmLoadError) as caught:
        confirm_mmm_load(
            {"mmm_packs": ["nominalist"], "mmm_sha256": digest},
            b"named but not loaded",
        )
    assert caught.value.reason_code == "REFUSE_MMM_NOT_IN_PROMPT"


def test_materialize_bound_prompt_prepends_missing_packs(tmp_path: Path) -> None:
    source = tmp_path / "prompt.txt"
    dest = tmp_path / "bound.txt"
    source.write_text("task only", encoding="utf-8")
    fields = materialize_bound_prompt(source, dest)
    bound = dest.read_bytes()
    text = compose_packs(fields["mmm_packs"])
    assert text.encode("utf-8") in bound
    assert bound.endswith(b"task only")
    assert fields["mmm_load_confirmed"] is True
    assert fields["mmm_sha256"] == hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_confirm_job_mmm_refuses_unbound_task() -> None:
    class _Task:
        prompt = "no packs"
        mmm_packs = []
        mmm_sha256 = ""

    class _Job:
        task = _Task()

    with pytest.raises(MmmLoadError) as caught:
        confirm_job_mmm(_Job())
    assert caught.value.reason_code == "REFUSE_MMM_LOAD_MISSING"
