"""Derive assets/hero-static.svg from assets/hero.svg by removing the motion.

The README serves the static file to anyone browsing with
`prefers-reduced-motion: reduce`. Re-run this whenever hero.svg changes:

    python scripts/make_static_hero.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "hero.svg"
DST = ROOT / "assets" / "hero-static.svg"


def main():
    svg = SRC.read_text(encoding="utf-8")

    # Drop every SMIL element, self-closing or paired.
    svg = re.sub(r"<animate[^>]*?/>", "", svg)
    svg = re.sub(r"<animate\b.*?</animate>", "", svg, flags=re.S)
    svg = re.sub(r"<animateTransform[^>]*?/>", "", svg)
    svg = re.sub(r"<(set|animateMotion)\b[^>]*?/>", "", svg)

    # The sweep rule animates its width in from 0; without motion it should
    # simply be drawn at full width, which it already is in the markup.
    # The travelling bottom rule has no resting state, so take it out.
    svg = re.sub(r'\s*<rect id="sweep-travel".*?</rect>', "", svg, flags=re.S)
    svg = re.sub(r'\s*<rect id="sweep-travel"[^>]*?/>', "", svg)

    # Collapse any element left empty by the stripping.
    svg = re.sub(r"<(rect|circle|ellipse)([^>]*)>\s*</\1>", r"<\1\2/>", svg)
    svg = re.sub(r"\n\s*\n+", "\n", svg)

    DST.write_text(svg, encoding="utf-8")
    print("wrote {} ({} bytes)".format(DST, DST.stat().st_size))

    leftover = len(re.findall(r"<animate", svg))
    print("remaining animation elements:", leftover)
    return 0 if leftover == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
