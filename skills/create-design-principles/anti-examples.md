# Design Principles — Anti-Examples

Failures to avoid when writing `design-principles.md`, each with what it looks like, why it fails, and the fix. Most come from Adham Dannaway's published tips, where he shows the problem and then the fix.

---

## 1. Pure black text

**Looks like:** `--text: #000000` on `#FFFFFF`.

**Why it fails:** "It's safest to avoid pure black against white and opt for a dark grey instead." The contrast is harsher than reading needs.

**Fix:** Text strong is a dark grey built from the brand hue, such as `#1F2A28`, still well above 4.5:1.

---

## 2. Too many font weights

**Looks like:** Inter at 400, 500, 600, and 700, each used somewhere, with no rule for which goes where.

**Why it fails:** Four weights are three decisions nobody needs to make, and an agent will pick one at random. "Keep your design system simple and concise by using regular and bold font weights only."

**Fix:** Regular and bold. If the brand wants a third weight on purpose, write which role gets it and why.

---

## 3. More than one primary button on a screen

**Looks like:** Component Patterns says "Buttons: filled brand colour," and nothing else, so Save and Export both render filled.

**Why it fails:** "Avoid using multiple primary buttons on a screen. They can compete for attention and cause confusion around what to do next."

**Fix:** Define primary, secondary, and tertiary, and say there is one primary per screen.

---

## 4. Colour alone as the signal

**Looks like:** "Selected tab: `--brand` text." "Links: `--brand`." "Errors: red border."

**Why it fails:** "Don't rely on colour alone to convey meaning." People with low vision or colour blindness can't see the difference.

**Fix:** Selected tab gets an underline. Links are underlined. Errors get an icon and a message as well as the colour.

---

## 5. Brand colour on things you can't click

**Looks like:** Headings, the streak star rating, and section icons all in `--brand`.

**Why it fails:** The brand colour teaches people what's interactive. When headings are teal too, people can't tell what to tap.

**Fix:** Brand on links and buttons only. Headings in Text strong. Decorative accents get their own token.

---

## 6. Values with no rule

**Looks like:** Spacing values of 6, 10, 12, 14, 18, and 22px. Font sizes of 13, 14, 15, 17, and 22px. No scale named.

**Why it fails:** "Without a logical system, you're just using gut feeling to move stuff around until it looks pretty." An agent can't tell which value to use next.

**Fix:** Spacing in t-shirt sizes on steps of 8. Font sizes from a base and a ratio. Every value in the file is on a scale or has a written reason.

---

## 7. Faint borders and icons

**Looks like:** Input borders and icons in `#D5DDDB` on white (1.38:1).

**Why it fails:** Interface elements need at least 3:1, or people can't find the field or read the icon.

**Fix:** Inputs and icons use Stroke strong, at least 3:1. The faint grey is Stroke weak, for decorative dividers only.

---

## 8. Disabled buttons

**Looks like:** "Submit is disabled until every field is valid."

**Why it fails:** A greyed-out button doesn't say what's wrong, and its low contrast often fails 3:1.

**Fix:** Keep the button enabled. On press, show what's missing next to the field.

---

## 9. Overruling the brand with a default

**Looks like:** The brand's guidelines choose a serif headline at 400, and the file says "Headlines: Inter 700. A single sans serif is safest."

**Why it fails:** The principles file wins over the skill's defaults. A default that overwrites a deliberate brand choice makes the product look like every other app.

**Fix:** Name the default once, then write the brand's choice and its reason. Check it against the Quality Floor.

---

## 10. Minimal that removes what people need

**Looks like:** "No labels on icon buttons. No borders on inputs. Fewer elements is cleaner."

**Why it fails:** "Minimal doesn't mean simple." "Removing or hiding too much can harm usability."

**Fix:** Limit the options in the system (weights, sizes, colours, radii), not the cues people use. Icon buttons keep labels. Inputs keep a Stroke strong border.
