"""Replace one named function with a raiser, then run a worker under it.

Why this exists, and why import_blocker.py is not enough.

`import_blocker.py` severs a MODULE. A worker that does `import scipy`, touches
the module so the import cannot be optimised away, and then computes the answer
with stdlib `math` is indistinguishable from a worker that genuinely calls
`scipy.linalg.expm`: both produce the right numbers, and both die when the
module is blocked. Import severance therefore tests module REACHABILITY, not
operation EXECUTION, and the import-only fake is the easier one to write.

Poisoning the claimed FUNCTION discriminates. A worker that actually calls it
dies; a worker that only imported the module to satisfy the severance control
survives untouched.

    usage: operation_poisoner.py MODULE FUNCTION SCRIPT [ARGS...]

Read the result with care.  Exit status alone is not evidence of a call.  A
confirmed severance has exactly both:

* exit status ``86``; and
* one stderr line:
  ``constraintbox.operation-severed.v1:MODULE.FUNCTION``

Any other nonzero result is merely a worker failure.  In particular, a worker
that notices the poison by introspection and exits early has not demonstrated
that it reached the claimed operation.

Poisoning happens before the script runs, so a worker's own
`from scipy.linalg import expm` binds the raiser rather than the real function.

This poison hides common callable metadata only. It does not withstand:

* type inspection (for example, NumPy's real ArrayFunctionDispatcher versus
  this plain function);
* ``__wrapped__`` presence: NumPy's real ``eigvalsh`` has it, while this
  poison deliberately removes it to prevent retrieving the real function;
* ``__code__`` presence: NumPy's real ``eigvalsh`` has no code object, while
  this poison does, so the ``co_name`` and ``co_qualname`` spoof buy nothing
  for that target;
* ``__globals__``, which exposes this module's ``OperationSevered``, ``runpy``,
  and ``importlib`` names;
* ``sys.modules`` inspection: ``runpy`` is loaded under this poisoner but was
  measured absent in a plain worker run;
* ``inspect.getsource`` or disassembly of ``__code__``;
* other implementation-specific introspection beyond the copied metadata.

Against ``scipy.linalg.expm``, by contrast, type, ``__code__`` presence,
``co_name``, ``__wrapped__`` absence, and signature all match the real
function; the weakness is specific to targets that are not plain Python
functions, and the ``co_name`` spoof is load-bearing there.

The exact signal removes the old false positive where *any* nonzero worker exit
was treated as operation use.  It is still only a bounded causality check for a
source-pinned worker and poisoner.  Arbitrary hostile code in this same process
can inspect or imitate the public protocol; this is not process containment.
"""

from __future__ import annotations

import functools
import importlib
import inspect
import runpy
import sys


OPERATION_SEVERED_EXIT_CODE = 86
OPERATION_SEVERED_SIGNAL_PREFIX = "constraintbox.operation-severed.v1:"


class OperationSevered(RuntimeError):
    def __init__(self, operation: str):
        self.operation = operation
        super().__init__(f"operation deliberately severed: {operation}")


def poison(module_name: str, function_name: str) -> None:
    module = importlib.import_module(module_name)
    if not hasattr(module, function_name):
        raise SystemExit(
            f"operation_poisoner: {module_name} has no attribute {function_name}"
        )
    original = getattr(module, function_name)
    operation = f"{module_name}.{function_name}"

    @functools.wraps(original)
    def _severed(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise OperationSevered(operation)

    try:
        _severed.__signature__ = inspect.signature(original)
    except (TypeError, ValueError):
        pass
    _severed.__dict__.pop("__wrapped__", None)
    try:
        _severed.__code__ = _severed.__code__.replace(
            co_name=original.__name__,
            co_qualname=original.__qualname__,
        )
    except (AttributeError, TypeError, ValueError):
        pass
    if hasattr(original, "__defaults__"):
        _severed.__defaults__ = original.__defaults__
    if hasattr(original, "__kwdefaults__"):
        _severed.__kwdefaults__ = original.__kwdefaults__
    setattr(module, function_name, _severed)


def main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit(
            "usage: operation_poisoner.py MODULE FUNCTION SCRIPT [ARGS...]"
        )
    module_name, function_name, script, *args = sys.argv[1:]
    poison(module_name, function_name)
    sys.argv = [script, *args]
    try:
        runpy.run_path(script, run_name="__main__")
    except OperationSevered as exc:
        # The broker requires this exact status-and-line pair.  Do not include a
        # traceback or arbitrary exception text: those would make generic
        # worker failures indistinguishable from the deliberate severance.
        sys.stderr.write(
            f"{OPERATION_SEVERED_SIGNAL_PREFIX}{exc.operation}\n"
        )
        raise SystemExit(OPERATION_SEVERED_EXIT_CODE) from None


if __name__ == "__main__":
    main()
