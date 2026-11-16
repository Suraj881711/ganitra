"""Wave 92: distance-speed-time phrasing pack.

Live failure (16 Nov 2026): "ek tren 360 km jati hai 40 km
per hour ki speed se, kitne ghante lagenge" -> "Answer nahi
mila" (expected 9). Diagnosis (see
~/workspace/ganitra-wave92-notes.md):

- The spelling fold was fine ("tren" -> "train"); the
  blockers were in solver/router.py's rewrite layer:
  (1) every speed rewrite keys on the literal "km/h", but
      students write "km per hour" / "km/hour" / "kmph" /
      "(kilo)metre prati ghanta" — never normalised;
  (2) the time rules covered speed-first order and the
      exact "km jana hai" frame, not the distance-first
      frame "360 km jati hai 40 km/h ki speed se";
  (3) the unit number was misread as a distance by the
      speed rule ("60 km per hour ... 3 ghante, kitni
      doori" answered speed 60/3 = 20);
  (4) "kitni der lagegi" never reached the gate: the
      skeleton fold rewrote "der" -> "doori" ("dr" target).
      "der" is now canon, so it can never fold.

Fixes, all in normalize_hinglish / the fold canon:
- speed-unit normalisation to "km/h" before any rewrite;
- a distance-first time rule (lag + ghante/time/samay/der,
  or "how long"; conditional-guarded like Wave 30);
- a time-first distance rule ("2 ghante me 80 km/h ...
  kitni doori");
- "der" added to _HINGLISH_CANON.

Probe before: 9 ok / 2 wrong / 13 miss of 24.
Probe after:  24 / 24.
"""
import re

from api import _solve_friendly
from solver.router import normalize_spelling


def _num(ans):
    m = re.findall(r"\d+(?:\.\d+)?", str(ans).replace(",", ""))
    return float(m[-1]) if m else None


def _check(q, want, tol=0.51):
    r = _solve_friendly(q)
    got = _num(r.get("answer"))
    assert got is not None and abs(got - want) < tol, \
        f"{q!r}: got {r.get('answer')!r} (op={r.get('op')}), want {want}"


# --- time asks: every unit form, distance-first --------------
TIME_ASKS = {
    "ek tren 360 km jati hai 40 km per hour ki speed se, kitne ghante lagenge": 9,
    "ek bus 240 km jati hai 60 km/hour ki speed se, kitna time lagega": 4,
    "ek car 300 km jati hai 50 kmph ki speed se, kitni der lagegi": 6,
    "ek train 180 km jati hai 45 kilometre prati ghanta ki raftaar se, kitne ghante lagenge": 4,
    "ek aadmi 20 km jata hai 5 km per hour ki speed se, how long will it take": 4,
    "ek cycl 90 km jati hai 15 km/h ki speed se, kitne ghante lagenge": 6,
    "ek bss 150 km jati hai 30 kmph se, kitna time lagega": 5,
    "ek tren 500 km jati hai 25 km/hour se, kitne ghante lagenge": 20,
    "bus 90 km jati hai 30 km prati ghanta ki speed se, kitna samay lagega": 3,
    "how long will it take a train to travel 420 km at 60 km per hour": 7,
    # speed-first order with a variant unit form
    "train 40 km per hour ki speed se 280 km jati hai, kitne ghante lagenge": 7,
}


def test_wave92_time_asks():
    for q, want in TIME_ASKS.items():
        _check(q, want)


# --- distance asks --------------------------------------------
DISTANCE_ASKS = {
    "ek train 60 km per hour ki speed se 3 ghante me kitni doori jayegi": 180,
    "ek bus 45 kmph ki speed se 4 ghante chalti hai, kitni doori tay karegi": 180,
    "ek car 2 ghante me 80 km/hour ki speed se kitni doori jayegi": 160,
    "ek cycle 12 km per hour ki raftaar se 5 ghante me kitna distance cover karegi": 60,
}


def test_wave92_distance_asks():
    for q, want in DISTANCE_ASKS.items():
        _check(q, want)


# --- speed asks (already worked; must not flip) ---------------
SPEED_ASKS = {
    "ek train 360 km 4 ghante me jati hai, speed kitni hai": 90,
    "ek bus 200 km 5 ghante me tay karti hai, raftaar batao": 40,
    "ek car 150 km 3 ghante me jati hai, speed batao": 50,
    "ek aadmi 24 km 6 ghante me chalta hai, uski raftaar kitni hai": 4,
    "ek tren 120 km 2 ghante me jati hai, uski speed kitni hai km per hour me": 60,
}


def test_wave92_speed_asks_unchanged():
    for q, want in SPEED_ASKS.items():
        _check(q, want)


# --- guards ----------------------------------------------------
def test_wave92_conditional_train_still_quadratic():
    # Wave 30/59: the conditional must stay with the
    # speed-time quadratic, never the plain time rule.
    _check("ek train 360 km jati hai, agar speed 5 km/h zyada "
           "hoti to 1 ghanta kam lagta, speed kitni hai", 40)


def test_wave92_canonical_frames_unchanged():
    _check("ek train 40 km/h ki speed se 360 km jati hai, "
           "kitne ghante lagenge", 9)
    _check("train ko 360 km jana hai, speed 40 km/h hai, "
           "kitne ghante lagenge", 9)


def test_wave92_unit_conversion_forms():
    _check("40 km/h ko m/s me badlo", 11.11, tol=0.1)
    # the variant unit form converts too, via normalisation
    _check("60 km per hour ko m/s me convert karo", 16.67, tol=0.1)


def test_wave92_der_never_folds_to_doori():
    out = normalize_spelling("kitni der lagegi")
    assert " der " in f" {out} "
    assert "doori" not in out


def test_wave92_word_soup_guard_intact():
    # Wave 73: no letter-soup answers, plain forms still solve.
    got = str(_solve_friendly("5 by 4").get("answer", ""))
    assert not re.search(r"\b[a-z](?:\*[a-z]\b|\*\*)", got)
    _check("5 into 4", 20)


def test_wave92_gibberish_still_not_found():
    r = _solve_friendly("ulta seedha bakwaas km per hour "
                        "ghante lagenge")
    assert r.get("op") == "not_found" \
        or r.get("fallback_kind") == "not_found"
