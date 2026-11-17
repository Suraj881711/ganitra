"""Wave 110: the menu Settings row gets the ORIGINAL settings gear.

Suraj's order (17 Nov 2026): "setting ka icon original lagao" — the
hand-drawn gear (an SVG circle r=3.2 plus 8 spoke lines, stroke style)
looked homemade. Wave 110 replaces it, in every template that carries
its own copy of the menu settings row, with the standard Material
"settings" cog: the classic filled gear silhouette, viewBox 0 0 24 24,
fill="currentColor", no stroke. Nothing else changes — same row, same
href, same label, same CSS (no ?v pin bump).

These tests pin the template sources:
- the old spoke-gear signature is gone from ALL templates,
- the new cog path is present in each of the three row copies,
- each settings row still links to /account with its label span intact.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"

ROW_TEMPLATES = ("index.html", "chats.html", "account.html")

# Signature of the old hand-drawn gear: centre circle + spoke path.
OLD_CIRCLE = '<circle cx="12" cy="12" r="3.2"/>'
OLD_SPOKES = "M12 2.8v3M12 18.2v3M2.8 12h3M18.2 12h3"

# Signature of the standard Material settings cog (filled path).
NEW_COG_START = "M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94"
NEW_COG_HOLE = "M12,15.6c-1.98,0-3.6-1.62-3.6-3.6"


def _read(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def test_old_spoke_gear_gone_from_all_templates():
    for path in TEMPLATES.glob("*.html"):
        text = path.read_text(encoding="utf-8")
        assert OLD_CIRCLE not in text, path.name
        assert OLD_SPOKES not in text, path.name


def test_new_material_cog_present_in_each_settings_row_copy():
    for name in ROW_TEMPLATES:
        text = _read(name)
        assert text.count(NEW_COG_START) == 1, name
        assert NEW_COG_HOLE in text, name
        # Filled cog in currentColor, no stroke, same 22px box.
        assert 'fill="currentColor" aria-hidden="true"' in text, name


def test_settings_row_still_links_to_account_with_label():
    for name in ROW_TEMPLATES:
        text = _read(name)
        assert '<a class="menu-settings-row" href="/account">' in text, name
        assert "<span>{{ t.menu_settings }}</span>" in text, name
