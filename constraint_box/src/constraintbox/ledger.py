from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .intake import canonical_json


GENESIS = "0" * 64


class HashChainLedger:
    """Local append-only consistency ledger.

    The chain detects accidental modification and deletion when its head is
    retained.  It is not a signature, external trust root, or authorship proof.
    """

    def __init__(self, path: Path, head_path: Path | None = None):
        self.path = path
        self.head_path = head_path or path.with_name(path.name + ".head")

    def _last_hash(self) -> str:
        if not self.path.exists() and not self.head_path.exists():
            return GENESIS
        return self.head_path.read_text(encoding="ascii").strip()

    def append(self, record: dict[str, Any]) -> str:
        valid, reason = self.verify()
        if not valid:
            raise ValueError(f"refusing append to invalid ledger: {reason}")
        previous = self._last_hash()
        body = {"previous_sha256": previous, "record": record}
        line_hash = hashlib.sha256(canonical_json(body)).hexdigest()
        row = {**body, "line_sha256": line_hash}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(row).decode("utf-8") + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        head_temp = self.head_path.with_name(self.head_path.name + ".tmp")
        with head_temp.open("w", encoding="ascii") as handle:
            handle.write(line_hash + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        head_temp.replace(self.head_path)
        try:
            directory_fd = os.open(self.head_path.parent, os.O_RDONLY)
        except OSError:
            directory_fd = None
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        return line_hash

    def verify(self) -> tuple[bool, str]:
        if not self.path.exists() and not self.head_path.exists():
            return True, "0 record(s)"
        if not self.path.exists():
            return False, "ledger missing while retained head exists"
        if not self.head_path.exists():
            return False, "retained head missing"
        previous = GENESIS
        count = 0
        for count, line in enumerate(
            self.path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            try:
                row = json.loads(line)
                body = {
                    "previous_sha256": row["previous_sha256"],
                    "record": row["record"],
                }
                actual = hashlib.sha256(canonical_json(body)).hexdigest()
            except (KeyError, TypeError, json.JSONDecodeError) as exc:
                return False, f"malformed record {count}: {exc}"
            if row["previous_sha256"] != previous:
                return False, f"previous hash mismatch at record {count}"
            if row.get("line_sha256") != actual:
                return False, f"line hash mismatch at record {count}"
            previous = actual
        try:
            retained_head = self.head_path.read_text(encoding="ascii").strip()
        except UnicodeDecodeError as exc:
            return False, f"retained head malformed: {exc}"
        if len(retained_head) != 64 or any(
            character not in "0123456789abcdef" for character in retained_head
        ):
            return False, "retained head malformed"
        if previous != retained_head:
            return False, "retained head mismatch"
        return True, f"{count} record(s)"
