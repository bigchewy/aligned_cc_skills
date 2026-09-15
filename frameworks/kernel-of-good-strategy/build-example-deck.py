#!/usr/bin/env python3
"""
Strategy kernel example deck: REM Medical.

Reference layout for the kernel-of-good-strategy framework's deliverable.
Page one is the kernel; the pages behind it carry the detail. Edit this
script and re-run it; never hand-edit the .pptx.

    python3 build-example-deck.py

Content: REM Medical was a sleep-medicine company that no longer exists.
Purpose, challenge, guiding policy, key actions, owners, and the year's
goals are from its original plan, used with its founder's permission. The
"why" behind the challenge and policy, the kill list, and the
assumptions and questions were not on the original page and are
illustrative: they show the format, not REM Medical's actual decisions.

Design: the Conscious OS design principles ("a well-set printed page with
one hot color"). Warm paper and warm ink, serif for what is said and sans
for what is controlled, hairline rules and cream bands instead of cards,
softened corners (rounder than the brand's rule, by choice), no shadows,
never a bold headline. Ember marks the
numerals; navy marks the guiding policy. Page one keeps the kernel's shape
(banner, arrow, block, arrow, three cards) in those surfaces. When rendering a real kernel,
replace the design tokens below with the project's design-principles.md
values; the layout does not change.

Typeface note: "New York" is the head of the serif stack and ships with
macOS; other machines fall back to Georgia.

Requires python-pptx (pip install python-pptx).
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

OUT = Path(__file__).with_name("example-strategy-kernel.pptx")

# ---------------------------------------------------------------- design tokens
# Values from the Conscious OS design-principles.md. Swap these for a
# project's own tokens; nothing below refers to a color by name.

PAPER = RGBColor(0xF7, 0xF2, 0xEA)      # cream-100, the page
CREAM_50 = RGBColor(0xFC, 0xFA, 0xF6)   # the lightest surface: page one's cards
CREAM_200 = RGBColor(0xEF, 0xE8, 0xDC)  # bands, the rare tinted panel
CREAM_300 = RGBColor(0xDF, 0xD6, 0xC8)  # hairlines that separate
BARK_900 = RGBColor(0x1A, 0x1A, 0x1A)   # headlines
BARK_700 = RGBColor(0x2D, 0x2D, 0x2D)   # reading text
BARK_500 = RGBColor(0x55, 0x55, 0x55)   # labels and metadata
BARK_400 = RGBColor(0x8F, 0x89, 0x81)   # non-text: rules that carry meaning
NAVY = RGBColor(0x1E, 0x28, 0x47)       # forest-500: competence, the guiding policy
NAVY_100 = RGBColor(0xE8, 0xEB, 0xF2)   # forest-100: the purpose banner's tint
EMBER = RGBColor(0xC2, 0x41, 0x0C)      # ember-500: heat, the numerals

# Corner rounding for bands and cards, in inches. The brand's own rule is
# near-square corners; this deck rounds them further by its author's choice.
RADIUS = 0.14

SERIF = "New York"        # what is said
SANS = "Helvetica Neue"   # what is controlled

MARGIN = 0.85
COLW = 11.63
FOOT_Y = 6.95
DECK_NAME = "REM Medical strategy kernel"

prs = Presentation()
prs.slide_width = Emu(12191695)
prs.slide_height = Emu(6858000)
BLANK = prs.slide_layouts[6]

# ---------------------------------------------------------------- primitives


def flatten(sh):
    """Drop the theme style reference so no renderer adds a drop shadow."""
    st = sh.element.find(qn("p:style"))
    if st is not None:
        sh.element.remove(st)
    return sh


def slide(bg_color=PAPER):
    s = prs.slides.add_slide(BLANK)
    r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    r.fill.solid()
    r.fill.fore_color.rgb = bg_color
    r.line.fill.background()
    r.shadow.inherit = False
    flatten(r)
    return s


def _shape(s, kind, x, y, w, h, fill):
    sh = s.shapes.add_shape(kind, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    flatten(sh)
    return sh


def panel(s, x, y, w, h, fill=CREAM_200):
    """A band with softened corners: flat fill, no border, no shadow."""
    return card(s, x, y, w, h, fill)


def card(s, x, y, w, h, fill=CREAM_200, radius=RADIUS):
    """A band with softened corners: flat fill, no border, no shadow.
    radius is in inches, so a short banner and a tall card round the same."""
    sh = _shape(s, MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h, fill)
    sh.adjustments[0] = min(0.5, radius / min(w, h))
    return sh


def arrow_down(s, y, color=BARK_400):
    """A small triangle on the page's center line. Non-text, so BARK_400."""
    _shape(s, MSO_SHAPE.ISOSCELES_TRIANGLE, 6.52, y, 0.30, 0.16, color).rotation = 180


def rule(s, x, y, w, color=CREAM_300):
    """Hairline. CREAM_300 separates; BARK_400 is a boundary that carries meaning."""
    return _shape(s, MSO_SHAPE.RECTANGLE, x, y, w, 0.011, color)


def vrule(s, x, y, h, color=CREAM_300):
    return _shape(s, MSO_SHAPE.RECTANGLE, x, y, 0.011, h, color)


def text(s, x, y, w, h, runs, size=14, bold=False, color=BARK_700, font=SERIF,
         align=PP_ALIGN.LEFT, spacing=None, line_spacing=1.35, anchor=None, gap=0):
    """runs: a string, a list of (text, bold, color, size, font) tuples for one
    paragraph, or a list of those lists for several paragraphs."""
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if anchor:
        tf.vertical_anchor = anchor
    if isinstance(runs, str):
        paras = [[(runs, bold, color)]]
    elif runs and isinstance(runs[0], tuple):
        paras = [runs]
    else:
        paras = runs
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(gap if i < len(paras) - 1 else 0)
        if isinstance(para, tuple):
            para = [para]
        for item in para:
            t = item[0]
            b = item[1] if len(item) > 1 and item[1] is not None else bold
            c = item[2] if len(item) > 2 and item[2] is not None else color
            sz = item[3] if len(item) > 3 and item[3] is not None else size
            f = item[4] if len(item) > 4 and item[4] is not None else font
            r = p.add_run()
            r.text = t
            r.font.name = f
            r.font.size = Pt(sz)
            r.font.bold = b
            r.font.color.rgb = c
            if spacing:
                r.font._rPr.set("spc", str(int(spacing)))
    return box


def label(s, txt, x, y, w=4.0, color=BARK_500, size=11):
    """Small-caps sans label: uppercase, 0.12em tracking, never bold."""
    return text(s, x, y, w, 0.18, txt.upper(), size=size, color=color, font=SANS,
                spacing=132, line_spacing=1.0)


def owner_run(name, size=10):
    """An owner's name as a small-caps sans run, for the end of a serif line."""
    return ("   " + name.upper(), False, BARK_500, size, SANS)


def eyebrow(s, txt, y=0.52):
    return label(s, txt, MARGIN, y, COLW)


def h1(s, runs, y=0.86, size=28, w=COLW, h=0.50, line_spacing=1.14, color=BARK_900):
    """Never bold a headline. Authority comes from size and space."""
    return text(s, MARGIN, y, w, h, runs, size=size, color=color, font=SERIF,
                line_spacing=line_spacing)


def numbered_h1(s, n, txt, y=0.86, size=28, h=0.50):
    """Section opener: a numeral in ember, then the serif heading."""
    return h1(s, [(n, False, EMBER), ("   " + txt, False, BARK_900)], y=y, size=size, h=h)


def footer(s, page):
    label(s, DECK_NAME, MARGIN, FOOT_Y, 10.9, size=9)
    text(s, 11.9, FOOT_Y, 0.60, 0.16, str(page), size=9, color=BARK_500, font=SANS,
         align=PP_ALIGN.RIGHT, line_spacing=1.0)


def labelled_text(s, x, y, w, lbl, body, size=13.5, color=BARK_700, label_color=BARK_500,
                  h=1.2):
    label(s, lbl, x, y, w, label_color)
    return text(s, x, y + 0.26, w, h, body, size=size, color=color)


def labelled_panel(s, x, y, w, h, lbl, body, size=13.5, pad=0.28):
    panel(s, x, y, w, h)
    label(s, lbl, x + pad, y + 0.24, w - 2 * pad)
    text(s, x + pad, y + 0.50, w - 2 * pad, h - 0.70, body, size=size, color=BARK_700)


def lines(s, x, y, w, h, items, size=13.5, color=BARK_700, gap=7):
    """Short serif lines, one paragraph per item, no bullet glyphs. They flow in
    one box, so a line that wraps pushes the next one down instead of into it."""
    paras = [[(item, False, color)] if isinstance(item, str) else item for item in items]
    return text(s, x, y, w, h, paras, size=size, color=color, line_spacing=1.3, gap=gap)


# ---------------------------------------------------------------- content

PURPOSE = "Enable people to lead a happier, healthier life starting with a better night's sleep"
CHALLENGE = "It is likely that Medicare reimbursement for sleep diagnostics will be significantly reduced."
POLICY = ("Leverage our strength in delivering outcomes by shifting from fee for service "
          "to getting paid for results.")

ACTIONS = [
    {
        "n": "1",
        "title": "Fuel the engine",
        "sub": "with existing fee-for-service business",
        "owner": "Jeff",
        "what": ("The in-lab and home-testing business we already run pays for the shift. "
                 "Keep it full and keep it collecting while reimbursement still holds."),
        "goals": [
            ("Engage 700 patients a month in Q4 in the Arizona region", "Jeff"),
            ("Perform, and collect payment on, 250 home tests in Q4", "Robert"),
        ],
        "depends": [
            "Referral volume from the existing physician network holds through the year",
            "Home-test billing and collection run without a new hire",
        ],
        "signal": "Monthly engaged patients and home-test collections, reviewed on the first of the month",
    },
    {
        "n": "2",
        "title": "New delivery models",
        "sub": "extend into new ways to deliver care",
        "owner": "Eric",
        "what": ("Find buyers who pay for a treated, sleeping patient rather than a test: employers "
                 "through occupational health, patients through ancillary products, sponsors through research."),
        "goals": [
            ("Treat 2,000 patients through occupational health", "Jen F"),
            ("$100,000 a month from ancillary DME products by end of Q3", "Michelle"),
            ("First dollar from the research division by end of Q3", "Colleen"),
        ],
        "depends": [
            "An occupational-health contract that pays per treated employee, not per test",
            "DME margin that survives payers following Medicare",
        ],
        "signal": "Revenue by delivery model, with fee-for-service share falling quarter over quarter",
    },
    {
        "n": "3",
        "title": "Geographic reach",
        "sub": "extend into new regions",
        "owner": "Russell",
        "what": ("Take the model to regions where sleep care is thin, built with provider groups who "
                 "bring the patients, so new sites open with referrals already attached."),
        "goals": [
            ("See the first patient in the Pacific Northwest by Aug 31", "Ken"),
            ("Break ground on 4 new sites in Q4", "Jen B"),
            ("Sign 6 provider groups to co-build new facilities", "Russell"),
        ],
        "depends": [
            "Provider groups willing to co-invest rather than refer at arm's length",
            "Site economics that work at reduced in-lab rates",
        ],
        "signal": "Signed co-build contracts and days from signature to first patient",
    },
]

KILL_LIST = [
    ("In-lab beds in existing markets", "In-lab utilization above 85% for two straight quarters"),
    ("Price cuts to win referrals", "A referral source names price as the reason they left"),
    ("Consumer sleep products", "Two occupational-health clients ask for them"),
    ("Acquiring other sleep labs", "A results-based payer contract is signed and needs capacity"),
]

ASSUMPTIONS = [
    ("Payers will pay for outcomes, not only for tests",
     "Two payer conversations end with “we only pay per study”"),
    ("Home testing can be profitable at reduced rates",
     "Home-test margin is negative after the Q4 volume push"),
    ("Occupational-health buyers want treated employees, not diagnoses",
     "Pilots renew as diagnostic-only contracts"),
]

QUESTIONS = [
    ("What does a results-based contract look like to a regional payer?", "Eric"),
    ("Which Pacific Northwest sites have the referral density to support a lab?", "Russell"),
    ("What DME margin holds once commercial payers follow Medicare?", "Michelle"),
]

# Two-column geometry shared by the detail pages.
COL_W = 5.55
X2 = MARGIN + COL_W + 0.53
VR_X = MARGIN + COL_W + 0.26

# ---------------------------------------------------------------- 1. the kernel
# Page one keeps the kernel's shape: a purpose banner, an arrow down to the
# challenge-and-policy block, an arrow down to three key-action cards. The
# brand supplies the surfaces (navy tint, cream band, cream-50 cards), the
# type (serif for what is said), and the ember numerals.

s = slide()
eyebrow(s, "The kernel", y=0.34)
h1(s, DECK_NAME, y=0.56, size=22, h=0.36)

# Purpose banner
card(s, MARGIN, 1.04, COLW, 0.60, NAVY_100)
label(s, "Purpose", MARGIN + 0.28, 1.25, 1.6, NAVY, size=10)
text(s, MARGIN + 2.10, 1.12, COLW - 2.38, 0.44, PURPOSE, size=15, color=NAVY,
     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
arrow_down(s, 1.72)

# Challenge and guiding policy, one band, a hairline between
card(s, MARGIN, 1.96, COLW, 1.12, CREAM_200)
label(s, "Challenge", MARGIN + 0.28, 2.18, 2.0, size=10)
text(s, MARGIN + 2.10, 2.04, COLW - 2.38, 0.42, CHALLENGE, size=14, color=BARK_900,
     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.2)
rule(s, MARGIN + 0.28, 2.52, COLW - 0.56, BARK_400)
label(s, "Guiding policy", MARGIN + 0.28, 2.74, 2.4, NAVY, size=10)
text(s, MARGIN + 2.10, 2.60, COLW - 2.38, 0.42, POLICY, size=14, color=NAVY,
     align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.2)
arrow_down(s, 3.16)

# Three key-action cards
CARD_Y, CARD_H, GAP = 3.40, 3.26, 0.30
CW = (COLW - 2 * GAP) / 3
PAD = 0.24
for i, a in enumerate(ACTIONS):
    x = MARGIN + i * (CW + GAP)
    card(s, x, CARD_Y, CW, CARD_H, CREAM_50)
    text(s, x + PAD, CARD_Y + 0.26, CW - 2 * PAD, 0.32,
         [(a["n"], False, EMBER, 16, SERIF), ("   " + a["title"], False, BARK_900, 16, SERIF)],
         align=PP_ALIGN.CENTER, line_spacing=1.1)
    text(s, x + PAD, CARD_Y + 0.62, CW - 2 * PAD, 0.2, a["sub"], size=10.5, color=BARK_500,
         font=SANS, align=PP_ALIGN.CENTER, line_spacing=1.2)
    text(s, x + PAD, CARD_Y + 0.84, CW - 2 * PAD, 0.2, "Owner: " + a["owner"], size=10.5,
         color=BARK_500, font=SANS, align=PP_ALIGN.CENTER, line_spacing=1.2)
    rule(s, x + PAD, CARD_Y + 1.14, CW - 2 * PAD)
    label(s, "This year", x + PAD, CARD_Y + 1.28, 1.5, size=9.5)
    lines(s, x + PAD, CARD_Y + 1.52, CW - 2 * PAD, 1.6,
          [[(goal, False, BARK_700, 10.5, SANS), owner_run(owner, 9)] for goal, owner in a["goals"]],
          gap=6)
footer(s, 1)

# ---------------------------------------------------------------- 2. challenge and policy in detail

s = slide()
eyebrow(s, "The challenge and the policy")
h1(s, "What the kernel stands on", y=0.82, size=26, h=0.44)
rule(s, MARGIN, 1.42, COLW, BARK_400)

label(s, "Challenge", MARGIN, 1.66, COL_W)
text(s, MARGIN, 1.92, COL_W, 0.9, CHALLENGE, size=17, color=BARK_900, line_spacing=1.3)
labelled_text(s, MARGIN, 3.00, COL_W, "Why it is that way",
              "Medicare has signaled cuts to in-lab polysomnography and is steering diagnosis toward "
              "home sleep testing at a fraction of the rate. Commercial payers follow Medicare within a "
              "year or two. Our revenue is built on the in-lab test.")
labelled_panel(s, MARGIN, 4.90, COL_W, 1.45, "How we'd know this is wrong",
               "The next Medicare fee schedule holds in-lab sleep study rates flat, and commercial "
               "payers don't move.")

vrule(s, VR_X, 1.66, 4.69)

label(s, "Guiding policy", X2, 1.66, COL_W, NAVY)
text(s, X2, 1.92, COL_W, 0.9, POLICY, size=17, color=NAVY, line_spacing=1.3)
label(s, "Why this policy fits", X2, 3.00, COL_W)
lines(s, X2, 3.26, COL_W, 1.4, [
    "Our outcomes data is the one asset a rate cut can't touch",
    "Payers cutting the test will still pay for a treated, adherent patient",
    "Fee-for-service funds the transition for as long as it lasts",
])
labelled_panel(s, X2, 4.90, COL_W, 1.45, "The gate",
               "When something new arrives, ask one question: does it get us paid for results, or fund "
               "the engine that will? If neither, it goes on the kill list.")
footer(s, 2)

# ---------------------------------------------------------------- 3-5. one page per key action

for i, a in enumerate(ACTIONS):
    s = slide()
    eyebrow(s, f"Key action {a['n']}")
    numbered_h1(s, a["n"], f"{a['title']}: {a['sub']}", y=0.82, size=26, h=0.44)
    text(s, MARGIN, 1.34, COLW, 0.2, "Owner: " + a["owner"], size=11, color=BARK_500, font=SANS,
         line_spacing=1.0)
    rule(s, MARGIN, 1.66, COLW, BARK_400)

    labelled_text(s, MARGIN, 1.90, COL_W, "What it is", a["what"], size=15, color=BARK_900, h=1.3)
    label(s, "What it depends on", MARGIN, 3.40, COL_W)
    lines(s, MARGIN, 3.66, COL_W, 1.1, a["depends"])
    labelled_panel(s, MARGIN, 4.90, COL_W, 1.30, "How we'll know it's working", a["signal"])

    vrule(s, VR_X, 1.90, 4.45)

    label(s, "This year's goals", X2, 1.90, COL_W)
    y = 2.20
    for goal, owner in a["goals"]:
        # One line per goal, the owner in small caps at its end, a hairline beneath.
        text(s, X2, y, COL_W, 0.6, [(goal, False, BARK_900, 15, SERIF), owner_run(owner)],
             line_spacing=1.3)
        rule(s, X2, y + 0.70, COL_W)
        y += 0.86
    footer(s, 3 + i)

# ---------------------------------------------------------------- 6. the kill list (its own page; not on page one)

s = slide()
eyebrow(s, "The kill list")
h1(s, "Not now, and what would bring each one back", y=0.82, size=26, h=0.44)
text(s, MARGIN, 1.40, 10.6, 0.5,
     "A refusal without a re-entry condition gets reopened in a hallway six months later. "
     "Each line here closes a door and puts a condition on the handle.",
     size=14, color=BARK_700)

label(s, "Not now", MARGIN, 2.30, 4.5)
label(s, "Comes back when", 6.40, 2.30, 5.5)
rule(s, MARGIN, 2.58, COLW, BARK_400)
y = 2.78
for name, cond in KILL_LIST:
    text(s, MARGIN, y, 5.0, 0.5, [("×  ", False, BARK_400), (name, False, BARK_900)],
         size=16, line_spacing=1.25)
    text(s, 6.40, y + 0.02, 6.08, 0.5, cond, size=14, color=BARK_700, line_spacing=1.3)
    y += 0.90
    rule(s, MARGIN, y - 0.24, COLW)
footer(s, 6)

# ---------------------------------------------------------------- 7. assumptions and questions

s = slide()
eyebrow(s, "WHAT WE'RE STANDING ON")
h1(s, "Key assumptions and key questions", y=0.82, size=26, h=0.44)
rule(s, MARGIN, 1.42, COLW, BARK_400)

label(s, "Key assumptions", MARGIN, 1.66, COL_W)
y = 2.00
for claim, breaks in ASSUMPTIONS:
    text(s, MARGIN, y, COL_W, 1.1,
         [[(claim, False, BARK_900, 15)],
          [("BROKE WHEN   ", False, BARK_500, 9.5, SANS), (breaks, False, BARK_700, 13)]],
         line_spacing=1.3, gap=6)
    y += 1.40
    rule(s, MARGIN, y - 0.26, COL_W)

vrule(s, VR_X, 1.66, 4.69)

label(s, "Key questions, each with an owner", X2, 1.66, COL_W)
y = 2.00
for q, owner in QUESTIONS:
    text(s, X2, y, COL_W, 1.1,
         [[(q, False, BARK_900, 15)], [(owner.upper(), False, BARK_500, 9.5, SANS)]],
         line_spacing=1.3, gap=6)
    y += 1.40
    rule(s, X2, y - 0.26, COL_W)
footer(s, 7)

prs.save(OUT)
print(f"wrote {OUT}")
