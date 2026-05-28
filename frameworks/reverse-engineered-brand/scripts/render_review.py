#!/usr/bin/env python3
"""Render a self-themed review.html from review-data.json + a token-slot template.

Deterministic, stdlib-only. Validates the data, emits theme CSS + server-side
panels, embeds a sanitized REVIEW_DATA snapshot for paste-back, runs the
verify-before-open checks, and aborts (writes nothing) on any failure.
Invoked by render-review-html.md (PHASE 3.7); render() is unit-tested directly.
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

CAP = 15
PALETTE_VARS = ["ink", "muted", "paper", "panel", "line", "line_strong",
                "primary", "primary_deep", "accent", "peach", "cream", "blush",
                "sky", "ice", "good", "warn", "risk"]
DEFAULT_PALETTE = {  # warm-neutral literal default (R3 h-6a) for public-web-only builds
    "ink": "#1a1a1a", "muted": "#6b7280", "paper": "#faf9f7", "panel": "#ffffff",
    "line": "#e5e7eb", "line_strong": "#d8c7bd", "primary": "#33312e",
    "primary_deep": "#1a1a1a", "accent": "#ff6900", "peach": "#ffe7d6",
    "cream": "#faf9f7", "blush": "#fff5f5", "sky": "#c9e5fc", "ice": "#edf7ff",
    "good": "#047857", "warn": "#a46716", "risk": "#b91c1c",
}


class RenderError(Exception):
    """Raised on validation or verify-before-open failure. Nothing is written."""


def _validate(data: dict, brand_folder: str) -> None:
    sections = data.get("sections", [])
    for s in sections:
        g = s.get("grade")
        if not isinstance(g, int) or not (1 <= g <= 5):
            raise RenderError(f"grade out of 1-5 range: section {s.get('id')} grade={g}")
    oqs = data.get("open_questions", [])
    if len(oqs) > CAP:
        raise RenderError(f"open_questions over cap: {len(oqs)} > {CAP}")
    # Offline-safety: every font src must be relative AND resolve inside the brand folder.
    theme = data.get("theme") or {}
    for key in ("heading", "body"):
        font = (theme.get("fonts") or {}).get(key) or {}
        for face in font.get("faces") or []:
            for src in (face.get("src_woff2"), face.get("src_woff")):
                if not src:
                    continue
                if re.match(r"^https?:", src):
                    raise RenderError(f"remote font src forbidden (offline-safety): {src}")
                if ".." in Path(src).parts:
                    raise RenderError(f"font src escapes brand folder: {src}")
    logo = (theme.get("logo") or {})
    if logo.get("src") and (re.match(r"^https?:", logo["src"]) or ".." in Path(logo["src"]).parts):
        raise RenderError(f"logo src must be local + non-escaping: {logo['src']}")


def _palette_css(theme: dict) -> str:
    palette = (theme.get("palette") or {})
    lines = []
    for var in PALETTE_VARS:
        value = palette.get(var) or DEFAULT_PALETTE[var]
        lines.append(f"      --{var}: {value};")
    return "\n".join(lines)


def _fontface_css(theme: dict) -> str:
    blocks = []
    for key in ("heading", "body"):
        font = (theme.get("fonts") or {}).get(key) or {}
        family = font.get("family")
        faces = [f for f in (font.get("faces") or [])
                 if (f.get("src_woff2") or f.get("src_woff"))]  # drop src-less faces (R3 h-6d)
        if not faces:
            if font.get("cdn"):
                blocks.append(f'@import url("{font["cdn"]}");')
            continue  # else rely on fallback stack
        for face in faces:
            srcs = []
            if face.get("src_woff2"):
                srcs.append(f'url("{face["src_woff2"]}") format("woff2")')
            if face.get("src_woff"):
                srcs.append(f'url("{face["src_woff"]}") format("woff")')
            blocks.append(
                f'@font-face {{ font-family: "{family}"; '
                f'src: {", ".join(srcs)}; '
                f'font-weight: {face.get("weight", 400)}; '
                f'font-style: {face.get("style", "normal")}; font-display: swap; }}')
    return "\n  ".join(blocks)


def _header_brand(theme: dict, org: str) -> str:
    logo = (theme.get("logo") or {})
    if logo.get("src"):
        return f'<img class="brand-mark" src="{html.escape(logo["src"], quote=True)}" alt="{html.escape(org)}">'
    text = logo.get("wordmark_text") or org
    return f'<span class="wordmark">{html.escape(text)}</span>'


def _nav_tabs(sections: list[dict]) -> str:
    out = []
    for s in sections:
        out.append(
            f'<button class="nav-btn" data-section="{html.escape(s["id"])}">'
            f'{html.escape(s["label"])}<span class="grade-chip g{s["grade"]}">{s["grade"]} / 5</span></button>')
    return "\n      ".join(out)


def _oq_blocks(section_id: str, oqs: list[dict]) -> str:
    # Overview lists no per-section OQs; area panels filter by slice path prefix.
    if section_id == "overview":
        return ""
    rows = [oq for oq in oqs if str(oq.get("slice", "")).startswith(section_id + "/")]
    if not rows:
        return ""
    blocks = ['<div class="oq-section-heading">Open questions</div>', '<ul class="oq-list">']
    for oq in rows:
        impact_cls = html.escape(oq["impact"].lower())
        blocks.append(
            f'<li class="oq-item">'
            f'<div class="oq-meta">'
            f'<span class="oq-id">{html.escape(oq["id"])}</span>'
            f'<span class="oq-impact {impact_cls}">{html.escape(oq["impact"])}</span>'
            f'</div>'
            f'<p class="oq-question">{html.escape(oq["question"])}</p>'
            f'<p class="oq-why">{html.escape(oq["why_it_matters"])}</p>'
            f'</li>')
    blocks.append('</ul>')
    return "\n".join(blocks)


def _panel(section: dict, oqs: list[dict]) -> str:
    provided = "".join(f"<li>{html.escape(x)}</li>" for x in section.get("provided", []))
    needed = "".join(f"<li>{html.escape(x)}</li>" for x in section.get("needed", []))
    readout = ""
    if section["id"] == "overview" and section.get("readout"):
        r = section["readout"]
        readout = (
            f'<div class="readout-grid">'
            f'<div class="readout-card"><p class="rc-label">Brand system</p>'
            f'<p>{html.escape(r.get("brand_system", ""))}</p></div>'
            f'<div class="readout-card"><p class="rc-label">Main risk</p>'
            f'<p>{html.escape(r.get("main_risk", ""))}</p></div>'
            f'<div class="readout-card"><p class="rc-label">Decisions needed</p>'
            f'<p>{html.escape(r.get("decisions_needed", ""))}</p></div>'
            f'</div>')
    return (
        f'<section class="panel" data-section="{html.escape(section["id"])}">'
        f'<p class="section-eyebrow">{html.escape(section.get("status", ""))}</p>'
        f'<div class="section-head">'
        f'<h2>{html.escape(section["label"])}</h2>'
        f'<span class="grade-badge g{section["grade"]}">{section["grade"]} / 5</span>'
        f'</div>'
        f'<p class="section-summary">{html.escape(section.get("summary", ""))}</p>'
        f'{readout}'
        f'<div class="signal-grid">'
        f'<div class="signal-card"><p class="sc-label">Working</p><ul>{provided}</ul></div>'
        f'<div class="signal-card"><p class="sc-label">Needs attention</p><ul>{needed}</ul></div>'
        f'</div>'
        f'{_oq_blocks(section["id"], oqs)}'
        f'</section>')


def _verify(out_html: str) -> None:
    if not out_html.startswith("<!DOCTYPE html>"):
        raise RenderError("verify: missing DOCTYPE")
    if "<script" not in out_html:
        raise RenderError("verify: missing <script>")
    if out_html.count("</script>") > out_html.count("<script"):
        raise RenderError("verify: unsanitized </script> in a string value")
    if not out_html.rstrip().endswith("</html>"):
        raise RenderError("verify: missing closing </html>")
    leftover = re.search(r"\{[A-Z][A-Z0-9_]*\}", out_html)
    if leftover:
        raise RenderError(f"verify: unsubstituted token {leftover.group(0)}")


def render(data: dict, template: str, brand_folder: str, org: str | None = None) -> str:
    org = org or data.get("org", "")
    _validate(data, brand_folder)
    theme = data.get("theme") or {}
    sections = data.get("sections", [])
    oqs = data.get("open_questions", [])
    # Serialize first, then sanitize the JSON text so </script> can't close the tag
    snapshot = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    out = (template
           .replace("{FONT_FACES_CSS}", _fontface_css(theme))
           .replace("{PALETTE_VARS_CSS}", _palette_css(theme))
           .replace("{HEADER_BRAND}", _header_brand(theme, org))
           .replace("{NAV_TABS}", _nav_tabs(sections))
           .replace("{SECTION_PANELS}", "\n".join(_panel(s, oqs) for s in sections))
           .replace("{ORG_NAME}", html.escape(org))
           .replace("{REVIEW_DATA_JSON}", snapshot))
    _verify(out)
    return out


def main(argv) -> int:
    if len(argv) != 6:
        sys.stderr.write("usage: render_review.py <review-data.json> <template> <out.html> <org> <brand-folder>\n")
        return 2
    data_path, template_path, out_path, org, brand_folder = argv[1:]
    data = json.loads(Path(data_path).read_text())
    try:
        out_html = render(data, Path(template_path).read_text(), brand_folder, org)
    except RenderError as e:
        sys.stderr.write(f"render aborted: {e}\n")
        return 1
    Path(out_path).write_text(out_html)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
