"""Wave 36, GAP B — bn/mr/ta/te UI translation consistency.

The four non-Hindi Indian-language tables were machine
generated and never proofread. This test pins the invariants
the app relies on (verify_wave5 already asserts key-set
identity for ADVICE; the same discipline is kept for
EXPLANATIONS, and get_strings() merges STRINGS over English):

- every English key exists in bn/mr/ta/te for STRINGS,
  EXPLANATIONS and ADVICE, with NO extra keys;
- the placeholder set ({name}-style and %s-style) of every
  translated string matches its English source exactly;
- no replacement characters (U+FFFD) anywhere;
- no Devanagari danda "।" in Tamil/Telugu strings (Hindi
  punctuation artifact — 14 sentence-final instances in the
  Wave-13 EXPLANATIONS/ADVICE additions were fixed to "."
  in this wave; the danda stays correct in bn/mr/hi);
- TEACH is exempt from key parity BY DESIGN: it ships en+hi
  tables only and teach_for() falls back to English lines
  for other languages — asserted here so the exemption is
  a checked behaviour, not an accident.
"""
import re

import i18n

LANGS = ("bn", "mr", "ta", "te")
TABLES = {
    "STRINGS": i18n.STRINGS,
    "EXPLANATIONS": i18n.EXPLANATIONS,
    "ADVICE": i18n.ADVICE,
}


def _placeholders(s):
    if not isinstance(s, str):
        return set()
    return (set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", s))
            | set(re.findall(r"%[sd]", s)))


def test_every_en_key_present_with_same_placeholders():
    for tname, table in TABLES.items():
        en = table["en"]
        for lang in LANGS:
            d = table[lang]
            missing = [k for k in en if k not in d]
            extra = [k for k in d if k not in en]
            assert not missing, (tname, lang, "missing", missing)
            assert not extra, (tname, lang, "extra", extra)
            for key, ev in en.items():
                pv = _placeholders(d[key])
                pe = _placeholders(ev)
                assert pv == pe, (tname, lang, key, pe, pv)


def test_get_strings_covers_english_for_all_langs():
    en_keys = set(i18n.STRINGS["en"])
    for lang in LANGS + ("hi",):
        assert en_keys <= set(i18n.get_strings(lang)), lang


def test_no_replacement_chars_anywhere():
    for tname, table in list(TABLES.items()) + [("TEACH", i18n.TEACH)]:
        for lang, d in table.items():
            for key, v in d.items():
                if isinstance(v, str):
                    assert "\ufffd" not in v, (tname, lang, key)
                elif isinstance(v, (list, tuple)):
                    for line in v:
                        assert "\ufffd" not in line, (tname, lang, key)


def test_no_danda_in_tamil_telugu():
    for tname, table in TABLES.items():
        for lang in ("ta", "te"):
            for key, v in table[lang].items():
                if isinstance(v, str):
                    assert "।" not in v, (tname, lang, key, v)


def test_teach_fallback_by_design():
    # TEACH ships en + hi only; other languages get the English
    # lines through teach_for() instead of a crash or empties.
    assert set(i18n.TEACH) == {"en", "hi"}
    result = {"type": "algebra", "op": "equation"}
    for lang in LANGS:
        lines = i18n.teach_for(result, lang)
        assert lines and all(isinstance(x, str) and x for x in lines), lang
