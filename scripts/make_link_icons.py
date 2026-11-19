"""Generate the social link cards in assets/links/.

Each card is a self-contained SVG pill: dark surface, brand-tinted glyph, label.
Rendered at height="44" in the README, so everything is sized for that.

Run:  python scripts/make_link_icons.py
"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets" / "links"

SURFACE, BORDER, LABEL = "#0E1730", "#243457", "#C8D7F2"

# Brand glyphs are 24x24 paths from Simple Icons (CC0 1.0); the envelope and
# globe are drawn here.
GLYPHS = {
    "github": "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12",
    "linkedin": "M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z",
    "kaggle": "M18.825 23.859c-.022.092-.117.141-.281.141h-3.139c-.187 0-.351-.082-.492-.248l-5.178-6.589-1.448 1.374v5.111c0 .235-.117.352-.351.352H5.505c-.236 0-.354-.117-.354-.352V.353c0-.233.118-.353.354-.353h2.431c.234 0 .351.12.351.353v14.343l6.203-6.272c.165-.165.33-.246.495-.246h3.239c.144 0 .236.06.285.18.046.149.034.255-.036.315l-6.555 6.344 6.836 8.507c.095.104.117.208.07.336",
    "portfolio": "M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 2.4c1.47 0 3.06 2.52 3.66 6.3H8.34C8.94 4.92 10.53 2.4 12 2.4zM5.1 5.46A14.6 14.6 0 006.0 8.7H3.42A9.66 9.66 0 015.1 5.46zm13.8 0A9.66 9.66 0 0120.58 8.7H18a14.6 14.6 0 00.9-3.24zM2.58 11.1h3.18a25 25 0 000 1.8H2.58a9.7 9.7 0 010-1.8zm5.58 0h7.68a24 24 0 010 1.8H8.16a24 24 0 010-1.8zm10.08 0h3.18a9.7 9.7 0 010 1.8h-3.18a25 25 0 000-1.8zM3.42 15.3H6a14.6 14.6 0 00.9 3.24A9.66 9.66 0 013.42 15.3zm4.92 0h7.32c-.6 3.78-2.19 6.3-3.66 6.3s-3.06-2.52-3.66-6.3zm9.66 0h2.58a9.66 9.66 0 01-1.68 3.24 14.6 14.6 0 00.9-3.24z",
    "email": "M1.5 4.5h21A1.5 1.5 0 0124 6v12a1.5 1.5 0 01-1.5 1.5h-21A1.5 1.5 0 010 18V6a1.5 1.5 0 011.5-1.5zm.9 2.1v.63l9.6 6.27 9.6-6.27V6.6H2.4zm19.2 3.18l-8.97 5.85a1.2 1.2 0 01-1.26 0L2.4 9.78v7.62h19.2V9.78z",
}

CARDS = [
    ("github",    "GitHub",    "#E6EDF7", "GitHub: ShubhParmar112"),
    ("linkedin",  "LinkedIn",  "#4F9CF9", "LinkedIn: Shubh Parmar"),
    ("kaggle",    "Kaggle",    "#2DD4BF", "Kaggle: shubhparmar69"),
    ("portfolio", "Portfolio", "#F5A524", "Portfolio: shubhparmar112.github.io"),
    ("email",     "Email",     "#FF7B72", "Email Shubh Parmar"),
]

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 56" width="{w}" height="56" role="img" aria-label="{alt}">
  <title>{alt}</title>
  <rect x="0.75" y="0.75" width="{iw}" height="54.5" rx="12" fill="{surface}" stroke="{border}" stroke-width="1.5"/>
  <g transform="translate(17 16) scale(1)" fill="{tint}">
    <path d="{glyph}" transform="scale(1)"/>
  </g>
  <text x="{tx}" y="34.5" font-family="'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="16.5" font-weight="500" fill="{label}">{text}</text>
</svg>
"""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, text, tint, alt in CARDS:
        width = 56 + int(len(text) * 9.3)
        svg = TEMPLATE.format(
            w=width, iw=width - 1.5, alt=alt, surface=SURFACE, border=BORDER,
            tint=tint, glyph=GLYPHS[key], tx=51, label=LABEL, text=text,
        )
        (OUT / f"{key}.svg").write_text(svg, encoding="utf-8")
        print(f"wrote {key}.svg ({width}x56)")


if __name__ == "__main__":
    main()
