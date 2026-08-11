# CB Light Threat Model — Executive Summary

**Date**: 2026-08-10  
**Scope**: Read-only security analysis of CB Light constraint enforcement against unpinned Python package installations.

**Baseline assumption**: Owner account can write every local tree. Manifest detects kernel movement. SQLite receipts chain with sha256. GitHub required checks form outer boundary.

---

## 1. Fail-Closed Guarantee — What Is Protected

CB Light currently defends against:

| Category | Coverage | Mechanism | Evidence |
|---|---|---|---|
| **Wrong interpreter** | ✅ Complete | Path resolution + comparison | `_same_executable()` on mandated interpreter; REFUSE if mismatch |
| **Unbounded package sources** | ✅ Complete | CLI flag detection | `-r`, `-c`, `--index-url`, `--extra-index-url`, `--find-links` all REFUSE |
| **Unbounded installation targets** | ✅ Complete | CLI flag detection | `--target`, `--prefix`, `--root`, `--user` all REFUSE |
| **Direct URL installs** | ✅ Complete | URL pattern matching | `git+`, `http://`, VCS schemes all REFUSE |
| **Shell wrapping (basic)** | ✅ Mostly | Recursive mutation detection | `command`, `sudo`, `env`, `nice`, etc. up to depth 3 |
| **Compound commands** | ✅ Mostly | Control token detection | `;`, `&&`, `||`, `|`, `&` all REFUSE |
| **Packages outside domain** | ✅ Complete | Domain membership check | Requested package must be in `domain["rows"]` |
| **Unselected packages** | ✅ Complete | Core contract validation | Package must pass probes and be in direct + core sets |
| **Version constraints** | ✅ Complete | Spec normalization + comparison | Requested spec must be in declared or current-installed set |

---

## 2. Critical Gaps — What Is Not Protected

### Gap 1: PYTHONPATH Shadowing (CRITICAL)

**Threat**: Attacker sets `PYTHONPATH=/attacker` to load a fake `constraint_box` module.

**Why it works**:
- Hook runs as: `python3 -m constraint_box.hookkernel.cb_light_gate ...`
- Python searches `sys.path` in order: `PYTHONPATH` entries come first
- Attacker's fake module is imported instead of the real one
- Attacker's fake gate returns ADMIT for all mutations

**Impact**: Complete bypass of all constraints

**Detection status**: ❌ None. Manifest checks source files on disk, not what's actually imported.

**Viability**: **HIGH** — `PYTHONPATH` is always modifiable by the user running the hook.

---

### Gap 2: Pip Configuration Files (HIGH)

**Threat**: Attacker sets `~/.pip/pip.conf` to redirect package index to attacker-controlled server.

**Why it works**:
- Pre-install hook only sees CLI arguments
- pip reads config files (`pip.conf`, `setup.cfg`, `pyproject.toml [tool.pip]`) before execution
- Hook does not inspect pip's config loading
- Attacker's server provides compromised `cryptography`, etc.

**Impact**: Package compromise; attacker can replace any selected package with a backdoored version

**Detection status**: ❌ Pre-hook does not inspect pip config. Post-install gate observes installed package; if it's from attacker's source, gate likely ADMITS (package is importable).

**Viability**: **HIGH** — Pip config is user-writable and outside hook scope.

---

### Gap 3: Shell Function / Alias Wrapping (HIGH)

**Threat**: Attacker defines shell function in `~/.bashrc` that intercepts the mandated interpreter.

**Why it works**:
- If hook is invoked in a shell that sources user `.bashrc`, the function is available
- User defines: `python3() { /attacker/python3 "$@"; }`
- Hook sees `python3 -m pip install`, tries to resolve it, may find the function or the real binary depending on resolution order
- If function is found first, it redirects to attacker's version

**Impact**: Interpreter override; attacker's Python can return fake gate decisions

**Detection status**: ⚠️ Partial. Depends on hook invocation context:
- If hook runs in interactive shell: ❌ Function is available
- If hook runs in non-interactive subprocess: ✅ Function not available

**Viability**: **HIGH** if hook is invoked interactively (e.g., `session-start` hook in interactive shell).

---

### Gap 4: Setup.py / PEP 517 Build Backend Code Execution (MODERATE)

**Threat**: Attacker creates a CB Light candidate package with malicious `setup.py` or build backend.

**Why it works**:
- Pre-install hook validates command line and domain membership; ADMITS
- pip runs `setup.py` or PEP 517 build backend before installing
- Setup code runs with full permissions; can exfiltrate data, install backdoors, etc.
- Post-install gate observes the installed package (already compromised)

**Impact**: Arbitrary code execution during build

**Detection status**: ❌ None. Setup.py execution is post-hook; hooks do not sandbox or inspect it.

**Viability**: **MODERATE** — Requires attacker to control a package in the CB Light domain or modify `cb_light_library_candidates.json`.

---

### Gap 5: Registry and Manifest Tampering (MODERATE)

**Threat**: Attacker replaces `manifest.json` and CB Light source code together.

**Why it works**:
- Manifest check: `if expected == current_file_hash`
- If attacker replaces both manifest and source, the check passes
- Attacker's gate code returns ADMIT for all mutations

**Impact**: Permanent bypass until manifest is re-signed

**Detection status**: ⚠️ Partial.
- ✅ Manifest check detects one-sided tampering (manifest XOR source changed)
- ❌ Cannot detect both changed together (owner-level access)
- ⚠️ GitHub required check on CI/CD can detect tampering if manifest is versioned and CI validates before merge

**Viability**: **MODERATE** — Requires write access to manifest and source (true for owner account); but GitHub checks provide external validation.

---

### Gap 6: Subshell Parens Wrapping (MODERATE)

**Threat**: Attacker runs `(pip install malicious)` to evade control-token detection.

**Why it works**:
- `shlex.split("(pip install ...)")` → `['(', 'pip', 'install', ...]`
- `_CONTROL_TOKENS` = `{';', '&&', '||', '|', '&'}` (parens not included)
- Control token check passes
- Tokens `['(', 'pip', ...]` don't form a recognized mutation pattern
- Hook returns NOT_A_PACKAGE_MUTATION → ADMIT

**Impact**: Evades compound-command check; but pip still runs without mutation validation... wait, no. If hook sees `(pip install ...)` as non-mutation, pip runs in subshell post-hook. **Does the post-hook catch it?** 

Actually, the subprocess `pip install` inside the subshell would be a **new Bash command** if invoked in a child process. But if it's all in one shell statement `(pip install ...)`, the entire statement is one command to the hook.

**Verdict**: Hook sees outer `(...)` command; doesn't match pip signature directly; admits. The inner pip runs in subshell without re-hooking. ❌

**Impact**: Medium — Bypasses NOT_A_PACKAGE_MUTATION check for subshell-wrapped installs.

**Detection status**: ❌ Parens are not in control tokens.

**Viability**: **LOW to MODERATE** — Requires shell syntax knowledge; easily blocked by adding parens to control tokens.

---

### Gap 7: Environment Variable Inheritance (HIGH)

**Threat**: `PIP_INDEX_URL`, `PIP_TRUSTED_HOST`, `PYPI_*` environment variables redirect package source.

**Why it works**:
- pip reads these env vars before executing
- Hook does not inspect environment
- Attacker's package source is used

**Impact**: Package compromise

**Detection status**: ❌ Environment variables are not inspected.

**Viability**: **HIGH** — Environment is always modifiable by the user.

---

### Gap 8: Direct Python API Invocation (MODERATE)

**Threat**: Attacker runs pip via Python API instead of CLI, bypassing Bash hook.

**Why it works**:
- Bash hook only runs for Bash commands
- `python3 -c "import subprocess; subprocess.run(['pip', 'install', 'malicious'])"`
- Hook doesn't intercept subprocess.run()

**Impact**: Mutation bypasses pre-hook validation

**Detection status**: ⚠️ Partial.
- Pre-hook is bypassed ❌
- Post-install gate runs (if it does) and re-probes ✅

**Viability**: **MODERATE** — Depends on whether post-install gate always runs.

---

## 3. Risk Ranking

| Rank | Gap | Likelihood | Impact | Effort to exploit | Viability |
|---|---|---|---|---|---|
| **1** | PYTHONPATH shadowing | HIGH | CRITICAL | Low | **CRITICAL** |
| **2** | Pip config redirection | HIGH | HIGH | Very low | **HIGH** |
| **3** | Shell function wrapping | HIGH | HIGH | Low | **HIGH** (context-dependent) |
| **4** | Setup.py injection | MODERATE | HIGH | Moderate | **MODERATE** |
| **5** | Registry + manifest replacement | MODERATE | HIGH | Low | **MODERATE** |
| **6** | Environment variable redirection | HIGH | HIGH | Very low | **HIGH** |
| **7** | Subshell parens wrapping | LOW | MODERATE | Low | **LOW-MODERATE** |
| **8** | Direct Python API invocation | MODERATE | MODERATE | Low | **MODERATE** |

---

## 4. Fail-Closed Boundary

### What CB Light DOES provide

1. ✅ Refusal of unbounded CLI options and package sources
2. ✅ Mandatory interpreter path validation
3. ✅ Domain membership and version constraint checking
4. ✅ Detection of basic shell wrappers and compound commands
5. ✅ Post-install re-probing (catches stale domain changes)
6. ✅ SQLite audit trail (immutable receipt chain with WAL + FULL sync)
7. ✅ GitHub required checks as outer boundary (prevents unsigned merges of CB Light code changes)

### What CB Light DOES NOT provide

1. ❌ Protection against PYTHONPATH/PYPI_INDEX_URL environment variables
2. ❌ Inspection of pip config files
3. ❌ Isolation from user shell configuration (aliases, functions)
4. ❌ Sandbox for setup.py / build backend execution
5. ❌ Package integrity verification (no signature checking)
6. ❌ Signed manifest (manifest can be replaced with code)
7. ❌ Complete protection against subshell syntax variants

### Where the boundary is

**Protected side** (Fail-closed):
- CLI-based package mutations with bounded options and mandated interpreter
- Directly hooked Bash commands
- Pre-defined package domain with version pinning

**Unprotected side**:
- Pip configuration files and environment variables
- Shell configuration (if sourced before hook)
- Build-time execution (setup.py, PEP 517)
- Package integrity/authenticity
- Interpreter venv integrity

---

## 5. Realistic Threat Model

### Attacker with no filesystem write access
✅ CB Light holds. Attacker cannot modify `~/.pip/pip.conf`, venv, or shell config.

### Attacker with user-level write access (owner account)
❌ CB Light can be bypassed via:
1. PYTHONPATH shadowing (easiest)
2. Pip config modification
3. Shell config modification
4. Direct modification of CB Light source + manifest

### Attacker with root access
❌ CB Light is irrelevant (attacker can modify anything).

### Attacker without filesystem access (e.g., in CI/CD pipeline)
✅ CB Light holds. Environment is isolated.

---

## 6. Mandatory Mitigations (Priority Tier 0)

**Before CB Light is production-safe**:

1. **Isolate hook environment** (CRITICAL)
   - Run `pre-install` hook in subprocess with clean `PYTHONPATH`, `PATH`, no user shell config sourcing
   - Or: Inline constraint_box code instead of importing (eliminates import path vulnerability)

2. **Inspect pip configuration** (HIGH)
   - Read `~/.pip/pip.conf`, `setup.cfg`, `pyproject.toml [tool.pip]`
   - REFUSE if any non-mandated index is configured
   - Check `PIP_INDEX_URL`, `PIP_TRUSTED_HOST`, `PYPI_*` environment variables

3. **Add subshell paren detection** (MODERATE)
   - Include `(` and `)` in `_CONTROL_TOKENS` to refuse subshell wrapping

---

## 7. Recommended Enhancements (Tier 1)

1. **Package integrity verification**
   - Post-install: Verify installed package hashes or signatures
   - Requires: PyPI signature support or pre-computed whitelist

2. **Registry signing**
   - Sign `manifest.json` and `registry.json` with external key
   - Verify signatures on every hook invocation

3. **Setup.py sandboxing**
   - Run `pip install` in subprocess with restricted filesystem access
   - Audit what setup.py reads/writes

4. **Hook script integrity**
   - Add SHA256 hashes of `.claude/hooks/*.sh` to manifest
   - Detect script modification

5. **Invocation audit**
   - Log hook invocation context (tty vs. subprocess)
   - Log environment variables at invocation time
   - Flag anomalous contexts

---

## 8. Conclusion

**CB Light is a constraint system, not a cryptographic proof.**

It provides fail-closed detection against:
- CLI-based mutation attempts with unbounded options
- Packages outside the controlled domain
- Wrong interpreter or package source (if specified on CLI)

It does **not** protect against:
- User-level environment manipulation (PYTHONPATH, pip config, shell config)
- Build-time code execution
- Package authenticity attacks
- Owner-level filesystem modifications (both manifest and source)

**Threat boundary**: Owner-account security. CB Light assumes the user running the hook is trustworthy but may run commands from untrusted sources. It will catch obvious mistakes and direct attacks on the constraint system itself, but determined owner-level attacks can bypass it by manipulating environment or filesystem.

**Outer boundary**: GitHub required checks on CI/CD pipeline. Prevents unsigned merges of CB Light code changes to main branch. Provides protection against mass-scale supply chain attacks (requires attacker to compromise GitHub account or CI/CD pipeline in addition to local environment).

---

## Supplementary Documents

- **ATTACK_MATRIX.md**: Detailed analysis of each attack vector with detection paths
- **EXPLOITATION_PATHS.md**: Concrete attack sequences ranked by viability
- **DETECTION_CHECKLIST.md**: Specific detection mechanisms (implemented vs. missing)

---

