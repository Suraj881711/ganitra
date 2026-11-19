"""Wave 180 (Suraj, 19 Nov 2026): composer tightening.

Viewing the Wave-176 screenshot, Suraj ordered two small
things and nothing else:

  "Ye jo icon hai chat ke niche unko thoda close karo woh
   bahut dur hai — or chat likhte hai uss box ko thoda
   sakara karna hai, height thodi Kam karo, length sahi hai."

Refined a minute later, naming the icons: the CAMERA, MIC
and SEND icons — "kuch jyada distance hai" — bring them
closer too.

Measured before (375px phone, local): the cluster gaps were
already 2px; the distance he saw was the 40px-wide visible
button boxes — mic/camera/send glyph centres sat 42px
apart, and the bar stood 66px tall (12px padding + 40px
row + 12px padding + border).

Wave 180 (append-only block at the end of style.css):
  - visible sign boxes 40px -> 34px, both cluster gaps
    2px -> 0: glyph centres now ~34px apart;
  - the invisible tap halo grows to inset -6px, so the
    tap target stays ~46px (Wave 118's rule was -4px);
  - bar padding 12px -> 9px vertical, textarea padding
    8px -> 5px vertical: the bar loses ~10px of height.
The bar's width, the horizontal paddings and every glyph
are untouched — length sahi hai.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
BASE = (ROOT / "templates" / "base.html").read_text(encoding="utf-8")
CSS = (ROOT / "static" / "style.css").read_text(encoding="utf-8")
SW = (ROOT / "static" / "sw.js").read_text(encoding="utf-8")

W180 = CSS[CSS.index("Wave 180: composer tightening"):]


def test_cluster_gaps_closed():
    assert "body.chat-page .chat-bar { gap: 0; padding: 9px 14px; }" in W180
    assert "body.chat-page .chat-bar-tools { gap: 0; }" in W180


def test_signs_shrink_to_34px():
    block = W180[W180.index("body.chat-page .chat-bar .composer-btn,"):]
    assert "width: 34px; height: 34px; min-height: 34px;" in block


def test_tap_halo_grows_past_wave118():
    # the -6px halo must come AFTER Wave 118's -4px in the
    # cascade, or the old rule would win and taps would shrink
    assert CSS.index("inset: -4px") < CSS.index("inset: -6px")
    block = W180[W180.index("body.chat-page .chat-bar .composer-btn::after,"):]
    assert "inset: -6px" in block


def test_box_slimmer_but_length_untouched():
    # vertical padding down a notch on bar + textarea;
    # horizontal padding (the length side) exactly as before
    assert "padding: 9px 14px" in W180
    assert ("body.chat-page .chat-bar textarea { padding: 5px 10px; }"
            in W180)


def test_all_four_signs_still_in_the_bar():
    for marker in ('id="file-btn"', 'id="mic-btn"',
                   'for="photo-input"', 'class="send-btn icon-btn"'):
        assert marker in INDEX


def test_pins_bumped_to_v58_v35():
    assert "v='60'" in BASE
    assert 'GANITRA_CACHE = "ganitra-static-v37"' in SW
    assert '"/static/style.css?v=60"' in SW


def test_answer_row_icons_closer():
    # Expansion (3): copy / speaker / bulb / ••• — side
    # padding 13px -> 8px, row gap 4px -> 2px; the vertical
    # padding stays 13px so the tap height stays 44px
    assert "body.chat-page .answer-actions { gap: 2px; }" in W180
    assert ("body.chat-page .answer-actions .act-btn "
            "{ padding: 13px 8px; }") in W180
    # Wave 118's wider rule must sit earlier in the cascade
    assert CSS.index("padding: 13px 13px") < CSS.index("Wave 180")


def test_greeting_block_moved_up():
    # Expansion (4 + refinement): the centred empty-state
    # block loses its auto centring and is pulled a notch
    # higher — close under the robot card.
    assert (".chat-empty { margin: 0; margin-top: -16px; "
            "padding-top: 8px; }") in W180
    assert CSS.index(".chat-empty { margin: auto 0") \
        < CSS.index("Wave 180")
