"""Stable short entrypoint for :mod:`host_hook_installer`.

The implementation lives in ``host_hook_installer.py`` so the historical
``install_plan.py`` compatibility API can remain intact.
"""

from __future__ import annotations

try:
    from host_hook_installer import *  # noqa: F401,F403
    from host_hook_installer import main
except ModuleNotFoundError:  # loaded by a fixture through spec_from_file_location
    import importlib.util
    import sys
    from pathlib import Path

    _path = Path(__file__).with_name("host_hook_installer.py")
    _spec = importlib.util.spec_from_file_location("integrated_host_hook_installer", _path)
    if _spec is None or _spec.loader is None:
        raise
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[_spec.name] = _module
    _spec.loader.exec_module(_module)
    globals().update({name: value for name, value in vars(_module).items() if not name.startswith("__")})
    main = _module.main


if __name__ == "__main__":
    raise SystemExit(main())
