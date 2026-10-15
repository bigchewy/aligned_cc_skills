# Design Principles — Examples

What finished sections of `design-principles.md` look like when every value has a rule behind it. The running example is a calm habit tracker for one person, with a teal brand colour and a sans serif throughout. The rules come from Adham Dannaway's *Practical UI* and his design system guide unless a line says otherwise. The contrast ratios below were computed for these exact hex values.

---

## Color, by role

Every colour is built from the brand hue and named for its job.

| Token | Light | Dark | Job | On background | On Fill / surface |
|---|---|---|---|---|---|
| `--brand` | `#0B7A6C` | `#4FC7B5` | Links and buttons only | 5.23:1 | 4.67:1 |
| `--text-strong` | `#1F2A28` | `#E8EEEC` | Headings, body, form labels | 14.79:1 | 13.19:1 |
| `--text-weak` | `#55625F` | `#A3B0AD` | Supporting text | 6.37:1 | 5.68:1 |
| `--stroke-strong` | `#7C8A87` | `#6F7D7A` | Input borders, icons | 3.59:1 | 3.21:1 |
| `--stroke-weak` | `#D5DDDB` | `#2A3331` | Decorative dividers only | decorative | decorative |
| `--fill` | `#EEF3F2` | `#1C2422` | Secondary background | — | — |
| `--bg` | `#FFFFFF` | `#141A19` | Page background | — | — |

- White text on `--brand` is 5.23:1, so a filled primary button passes.
- Text strong is a dark grey, not black. Pure black against white is harsher than reading needs.
- `--stroke-weak` fails 3:1 on purpose. It is only for decoration, never for the border of something you need to find, like an input.
- In dark mode, surfaces get lighter as they rise (`--bg`, then `--fill`), instead of using shadows.

**Why it works:** each colour has one job, every text colour reaches 4.5:1 on every surface it sits on, and an agent can pick the right token from the job alone.

---

## Typography

| Role | Size / line height | Weight | Notes |
|---|---|---|---|
| Headline 1 | 29 / 36 | 700 | Letter spacing -0.01em |
| Headline 2 | 24 / 32 | 700 | |
| Headline 3 | 20 / 28 | 700 | |
| Body | 16 / 24 | 400 | Line height 1.5 |
| Label | 16 / 24 | 700 | |
| Supporting | 13 / 20 | 400 | `--text-weak` only on `--bg` |

- Sizes come from a 16px base times 1.2, rounded: 16, 20, 24, 29. (13 is 16 ÷ 1.2, rounded.) The sizes after 20 are computed by his rule, not his list.
- Every line height is divisible by 4, so text sits on a 4px grid.
- Regular and bold only. Two weights cover every role here.
- Body lines are 40 to 80 characters. The file states the limit as 80 characters, and the CSS value that delivers it in Inter at 16px is set by rendering a paragraph of real copy and counting the longest line, as the Quality Floor requires.

**Why it works:** a new size can be checked against the ratio, and a new weight can't sneak in, because there are only two.

---

## Spacing

| Token | Value | Use |
|---|---|---|
| `--space-xs` | 8px | Inside a component: icon to label |
| `--space-s` | 16px | Between related items: label to field |
| `--space-m` | 24px | Between groups in a card |
| `--space-l` | 32px | Card padding on desktop |
| `--space-xl` | 48px | Between sections (Phase 1 answer: "calm, but not a magazine") |

- T-shirt sizes on steps of 8 that grow faster as they get bigger.
- The closer two things are related, the less space between them.

---

## Border Radius and Depth

- Radii: `--radius-s` 8px (inputs, buttons), `--radius-m` 16px (cards), `--radius-l` 32px (sheets and dialogs). Photos use `--radius-m` too.
- Shadows: `--shadow-raised` for cards that lift, `--shadow-overlay` for menus and dialogs. Two, no more.
- Hover and press: a transparent overlay on the element (`--text-strong` at 8% and 12%).

---

## Buttons

- **Primary:** `--brand` fill, white bold label. One per screen.
- **Secondary:** `--stroke-strong` border, `--brand` label, no fill.
- **Tertiary:** `--brand` label only, underlined on hover.
- At least 48px by 48px, at least 8px apart, left aligned.
- No disabled buttons. When something's missing, the button stays enabled and says what's needed on press.

**Why it works:** the most important action is the only filled thing on the screen, so the Squint Test finds it first.

---

## A choice made on purpose

> **Headline 1** uses Fraunces 600, a serif, at 29/36. *Practical UI*'s default is a single sans serif with regular and bold. The brand chose a serif headline for warmth (Phase 1, question 8). Fraunces 600 at 29px reaches 14.79:1 in `--text-strong`. Every other role stays Inter 400 or 700.

**Why it works:** the default is named once, the choice and its reason are written down, and the Quality Floor still holds. An agent reading this knows the serif is intentional and won't "fix" it.
