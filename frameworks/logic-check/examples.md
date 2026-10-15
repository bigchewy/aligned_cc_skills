# Logic Check — Examples

One running example: a solo builder's habit tracker. Its `design-principles.md` is at `docs/design/design-principles.md`. The settings screen uses pure black text, Inter at 400, 500, 600, and 700, the brand teal `#0F9D8A` on buttons, headings, and the streak star rating, and two filled teal buttons, Save and Export, side by side.

---

## Phase 1: What We're Checking

### Golden path

**User:** "Check the settings screen at localhost:3000/settings against our principles file."

**Say something like:**
"I'm checking `/settings` against `docs/design/design-principles.md`. Anything that file chose on purpose stays, even where my defaults differ."

**Why it works:** The principles file is named first, so a deliberate brand choice is never "fixed."

### Edge case: only a principles file

**User:** "No screens yet. Just check the file."

**Say something like:**
"Good, that's the cheapest time to do it. I'll check every token and rule in the file, and skip the Squint Test, since there's no screen to squint at."

**Why it works:** The check adapts to what exists and says which step it's skipping.

---

## Phase 2: Name the Rule Behind Every Value

### Golden path

**Say something like:**
"These follow a rule: the 16px body size is your base, 20px and 24px are 16 × 1.2 rounded, and the 8, 16, and 24 spacing is your t-shirt scale. These don't have one yet: the 13px caption, the 14px button label, the 500 and 600 weights, the 12px gap between rows, and `#000` for text. Nothing's wrong with any one of them. It's that your agent can't tell when to use which."

**Why it works:** Values with a rule are named first, so the list without one reads as gaps to fill, not mistakes.

---

## Phase 3: The Rule-by-Rule Check

### Golden path

**Say something like:**
"Rule by rule:
- **Pure black:** body text is `#000`. Fix: Text strong, a dark grey from your teal's hue. It's safest to avoid pure black against white.
- **Brand colour:** teal is on the headings and the star rating, which you can't click. Fix: headings go to Text strong; the stars get their own colour. This helps teach people what's interactive and what's not.
- **Weights:** 400, 500, 600, 700. Fix: regular and bold only.
- **Primary buttons:** Save and Export are both filled teal. Fix: Save stays primary, Export becomes secondary.
- **Contrast:** Text weak `#9AA3A0` on white is 2.6:1. Fix: darken it until it reaches 4.5:1.
- **Colour alone:** the selected tab is only a slightly darker teal. Fix: underline it.

Which of these did you choose on purpose?"

**Why it works:** Every finding has a place, a fix, and a reason, and the user gets the chance to defend a choice before anything changes.

### Struggle: defends a choice

**User:** "The 600 weight is on purpose. Our headlines need it."

**Say something like:**
"Then it's a decision, not drift. I'll write 'headlines at 600, chosen on purpose' so your agent stops adding 500 elsewhere."

**Why it works:** A deliberate choice gets written down instead of argued with, which is what stops the drift.

---

## Phase 4: The Squint Test

### Golden path

**Say something like:**
"Squint at the settings screen. The first thing you see is the teal star rating, then two identical teal buttons. It should be Save. With the stars and headings out of teal and Export as a secondary button, Save is the only filled teal thing on the screen."

**Why it works:** The test confirms the earlier fixes do what they're for.

---

## Phase 5: The Fix List

### Golden path

**Say something like:**
"Token changes, for `/aligned:create-design-principles`: Text strong replaces `#000`; Text weak darkened to 4.5:1; drop the 500 weight. Screen changes, one per task for your agent: headings on `/settings` to Text strong; stars to their own colour; Export to Button, secondary; selected tab gets an underline. Seven values had no rule; now they all do."

**Why it works:** Token changes and screen changes are separated, so the file changes once and the screens follow.
