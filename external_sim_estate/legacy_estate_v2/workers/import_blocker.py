from __future__ import annotations

import importlib.abc
import runpy
import sys


class BlockedImport(importlib.abc.MetaPathFinder):
    def __init__(self, blocked: str):
        self.blocked = blocked

    def find_spec(self, fullname, path=None, target=None):
        del path, target
        if fullname == self.blocked or fullname.startswith(self.blocked + "."):
            raise ImportError(f"dependency deliberately severed: {fullname}")
        return None


def main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: import_blocker.py MODULE SCRIPT [ARGS...]")
    blocked, script, *args = sys.argv[1:]
    sys.meta_path.insert(0, BlockedImport(blocked))
    sys.argv = [script, *args]
    runpy.run_path(script, run_name="__main__")


if __name__ == "__main__":
    main()
