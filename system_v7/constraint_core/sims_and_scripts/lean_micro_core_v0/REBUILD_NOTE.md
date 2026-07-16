The .lake/ build directory (dependency checkouts + compiled artifacts) is deliberately NOT shipped — it is
rebuildable, not evidence. Evidence = the .lean sources, lakefile.toml, lean-toolchain, build_log.txt (verbatim
kernel output incl. #print axioms), and results_v1.json. To rebuild: `lake build` with the pinned toolchain.
