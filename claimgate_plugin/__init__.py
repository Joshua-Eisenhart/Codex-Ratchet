"""ClaimGate plugin package.

Exists so checkers can be invoked as `python3 -I -m claimgate_plugin.<name>`.
Script-path invocation (`python3 claimgate_plugin/intake_supervisor.py`) puts
claimgate_plugin/ itself on sys.path[0], which lets an attacker-authored
claimgate_plugin/hashlib.py shadow the stdlib. Module invocation off the repo
root makes that file a SUBMODULE (claimgate_plugin.hashlib), not top-level
hashlib, so it cannot shadow.
"""
