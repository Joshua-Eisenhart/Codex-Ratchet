"""Narrow, reversible adapters for optional packages lagging canonical JAX.

These adapters do not alter installed package files or global environments.
They exist only for the bounded call in which they are explicitly activated,
and every stress receipt records both the unadapted failure and adapted path.
"""

from __future__ import annotations

import inspect
from contextlib import contextmanager
from typing import Any, Iterator


def install_dynamax_xla_alias() -> dict[str, Any]:
    """Restore the deprecated XLA mapping alias expected by Dynamax/TFP.

    Canonical JAX still exposes the same mapping at ``jax.core``.  The adapter
    only binds the removed legacy name when the source mapping is present and
    never replaces an existing value.
    """

    import jax
    import jax.interpreters.xla as xla

    already_present = hasattr(xla, "pytype_aval_mappings")
    source_present = hasattr(jax.core, "pytype_aval_mappings")
    if not already_present and source_present:
        xla.pytype_aval_mappings = jax.core.pytype_aval_mappings
    return {
        "adapter": "dynamax_xla_pytype_aval_mappings_alias",
        "already_present": already_present,
        "source_present": source_present,
        "installed_for_process": hasattr(xla, "pytype_aval_mappings"),
        "installed_package_files_modified": False,
    }


@contextmanager
def jaxga_static_argnames_compat() -> Iterator[dict[str, Any]]:
    """Drop JaxGA's invalid closure-only ``out_size`` static arg declaration.

    JaxGA 0.0.2 asks JAX to mark ``out_size`` static even though the generated
    closure captures it and has no such parameter.  Modern JAX rejects that
    declaration.  This context changes only that exact invalid call shape and
    restores ``jax.jit`` in ``finally``.
    """

    import jax

    original_jit = jax.jit
    witness: dict[str, Any] = {
        "adapter": "jaxga_closure_static_argnames_filter",
        "intercept_count": 0,
        "installed_package_files_modified": False,
    }

    def compatible_jit(fun=None, *args, **kwargs):
        static_argnames = kwargs.get("static_argnames")
        if fun is not None and static_argnames:
            parameters = inspect.signature(fun).parameters
            names = [static_argnames] if isinstance(static_argnames, str) else list(static_argnames)
            invalid = [name for name in names if name not in parameters]
            if invalid == ["out_size"] and getattr(fun, "__name__", "") == "_values_mv_mul":
                kwargs = dict(kwargs)
                kwargs.pop("static_argnames", None)
                witness["intercept_count"] += 1
        return original_jit(fun, *args, **kwargs)

    jax.jit = compatible_jit
    try:
        yield witness
    finally:
        jax.jit = original_jit
        witness["restored"] = jax.jit is original_jit
