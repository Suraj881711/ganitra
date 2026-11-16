"""Ganitra solver package: routing + topic solvers (SymPy powered)."""

# ---------------------------------------------------------------------------
# Wave 97 (speed): stop the regex-recompile storm.
#
# The solver pipeline matches each question against well over 600
# DISTINCT regex patterns (router + applied + the topic solvers),
# but the stdlib `re` module caches only the last 512 compiled
# patterns and CLEARS the whole cache when it fills — so on any
# question that walks several solver modules (an unsolvable or
# MCQ question walks them all, repeatedly, through the fallback /
# salvage / wrapper layers), nearly every re.search recompiled
# its pattern from scratch. Profiling one such question (Wave 97):
# 18,138 re._compile calls for 614 distinct patterns, 24.5 s of a
# 27.3 s answer spent compiling regexes.
#
# Raising the cache ceiling keeps every compiled pattern resident
# (a few thousand small pattern objects, a few MB at most). The
# compiled patterns are exactly the objects `re` itself would
# cache — match semantics cannot change, only the recompilation
# disappears. Guarded: on a Python whose `re` has no such knob
# this is a silent no-op.
# ---------------------------------------------------------------------------
import re as _re

try:
    if getattr(_re, "_MAXCACHE", 512) < 32768:
        _re._MAXCACHE = 32768
except Exception:  # never let a speed knob break an import
    pass

del _re
