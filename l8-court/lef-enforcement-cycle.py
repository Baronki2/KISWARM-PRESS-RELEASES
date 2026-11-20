#!/usr/bin/env python3
"""LEF-1.0 enforcement cycle — cron entry point.

THE CRON INTERPRETER IS NOT THE RIGHT INTERPRETER.

The Hermes cron scheduler runs `no_agent` scripts on the *dependency
environment's* interpreter (…/installs/<hash>/environments/<hash>/venv/bin/python).
That environment has no PyNaCl, and — worse — appending the system
dist-packages path does NOT help either: the system `nacl` is a C extension
built for the system ABI, so on a mismatched interpreter the import fails one
level deeper with `No module named 'nacl._sodium'`.

Symptom: every enforcement cycle since 2026-11-20 14:00 died with
`ModuleNotFoundError: No module named 'nacl'` — and because the failure was in
the *signing* step, it only ever fired when a notice actually had to be
emitted. A green-looking script that never signs is worse than a red one.

FIX: re-exec into an interpreter that provably has a working PyNaCl. The
candidate list is probed, not assumed: each candidate is asked to import
nacl.signing AND produce a 64-byte signature. Only a candidate that actually
signs is used.

This is the same discipline the LEF layer itself applies: never trust that an
artifact exists because the code that consumes it never asked.
"""
import os
import subprocess
import sys

SELF = os.path.abspath(__file__)

# Interpreters that are known to carry a usable PyNaCl on this host, in
# preference order. /usr/bin/python3 is the system interpreter with the
# distro nacl; the Hermes tool-store python carries its own wheel.
CANDIDATES = [
    "/usr/bin/python3",
    "/usr/bin/python3.14",
    "/home/sah/.hermes/tools/python-3.14.9+20261021-linux-x64/bin/python3",
    "/home/sah/.hermes/hermes-agent/venv/bin/python",
]

PROBE = (
    "import nacl.signing, sys;"
    "from nacl.signing import SigningKey;"
    "k = SigningKey(b'\\x01' * 32);"
    "assert len(k.sign(b'\\x00' * 32).signature) == 64;"
    "print('OK')"
)


def _works(exe):
    """True only if this interpreter can actually SIGN — not merely import."""
    try:
        r = subprocess.run([exe, "-c", PROBE], capture_output=True,
                           text=True, timeout=60)
        return r.returncode == 0 and "OK" in (r.stdout or "")
    except Exception:
        return False


def _pick():
    """Return an interpreter that can sign, or None if the current one can."""
    try:
        from nacl.signing import SigningKey  # noqa: F401
        return None  # current interpreter is fine
    except Exception:
        pass
    for exe in CANDIDATES:
        if os.path.exists(exe) and _works(exe):
            return exe
    return None


def main():
    exe = _pick()
    if exe:
        # Replace this process so the scheduler sees one clean exit code.
        os.execv(exe, [exe, SELF] + sys.argv[1:])
    # No candidate signs — run anyway and let the real error surface.
    import runpy
    sys.argv = ["lef-enforcement-cycle-main.py", "--quiet"]
    runpy.run_path("/home/sah/.hermes/scripts/lef-enforcement-cycle-main.py",
                   run_name="__main__")


if __name__ == "__main__":
    main()
