"""Reproduce equivalent Unicode keys surviving the duplicate-key guard."""
from __future__ import annotations

import json
import shutil
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from constraintbox.intake import IntakeError, canonical_json, parse_json_value


def reproduce(equivalent_keys: bool = True) -> dict[str, Any]:
    temp = Path(tempfile.mkdtemp(prefix="claimgate-e6-unicode-"))
    try:
        nfc = unicodedata.normalize("NFC", "café")
        nfd = unicodedata.normalize("NFD", nfc)
        assert nfc != nfd and unicodedata.normalize("NFC", nfd) == nfc

        second = nfd if equivalent_keys else nfc
        payload = json.dumps(
            {nfc: 1}, ensure_ascii=False
        )[:-1] + "," + json.dumps(second, ensure_ascii=False) + ":2}"

        body = None
        parse_error = None
        try:
            body = parse_json_value(payload.encode("utf-8"))
        except IntakeError as exc:
            parse_error = str(exc)

        canonical = canonical_json(body) if body is not None else None
        true_duplicate_rejected = False
        duplicate_error = None
        try:
            parse_json_value(b'{"a":1,"a":2}')
        except IntakeError as exc:
            true_duplicate_rejected = True
            duplicate_error = str(exc)

        parsed_two = isinstance(body, dict) and len(body) == 2
        canonical_emitted_both = (
            canonical is not None
            and json.dumps(nfc, ensure_ascii=False).encode("utf-8") in canonical
            and json.dumps(nfd, ensure_ascii=False).encode("utf-8") in canonical
        )
        admitted = (
            parse_error is None
            and parsed_two
            and canonical_emitted_both
            and true_duplicate_rejected
        )
        return {
            "admitted": admitted,
            "nfc_nfd_equal": nfc == nfd,
            "nfc_equal_after_normalization": unicodedata.normalize("NFC", nfd) == nfc,
            "parse_error": parse_error,
            "body_keys": len(body) if isinstance(body, dict) else None,
            "canonical_json": canonical.decode("utf-8") if canonical is not None else None,
            "true_duplicate_rejected": true_duplicate_rejected,
            "true_duplicate_error": duplicate_error,
        }
    finally:
        shutil.rmtree(temp)
