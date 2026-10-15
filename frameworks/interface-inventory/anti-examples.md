# Interface Inventory — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. Capturing every instance

**User:** "There are about 40 pages. Screenshot all of them."

**Wrong:**
"On it. Here are 212 button screenshots, one from every page, grouped by page."

**Right:**
"I'll go through all 40, but I'll only keep one example of each distinct look. If 30 pages share the same button, that's one entry with '30 pages' next to it. The finding is the differences, not the count."

**What to do instead:** Capture one example of each distinct look per category and note where it appears. "This exercise doesn't mean capturing every instance of a particular UI pattern."

---

## 2. Redesigning during the audit

**User:** "While we're at it, let's make all the buttons pill-shaped and switch to a darker blue."

**Wrong:**
"Great idea. I'll merge the five buttons into one pill-shaped button with #1E3A8A."

**Right:**
"Love it, and let's do it once, in the right place. Pill corners and a darker blue go into `design-principles.md` through `/aligned:create-design-principles`. Then the merge uses the new tokens and every button gets them. If we change it here, we're redesigning and auditing at the same time, and the audit stops being trustworthy."

**What to do instead:** Audit first. Design changes go to the design principles, then into the merges as tokens.

---

## 3. Inventing token values

**User:** "We don't have a design-principles file. Just pick the right gray."

**Wrong:**
"The right text gray is #6B7280. I'll set that as the standard and merge everything to it."

**Right:**
"I won't invent one. You've got five grays used for secondary text. Here they are side by side. Pick the one that reads best on your background, and that becomes the first token in your design principles. `/aligned:create-design-principles` will check its contrast and write it down properly."

**What to do instead:** Use the app's own patterns as the first draft of the tokens, and let the user choose. Values are set in `design-principles.md`, never made up in the inventory.

---

## 4. Merging something that's different on purpose

**User:** "Merge all the red buttons."

**Wrong:**
"Done. 'Delete account' and 'Mark as urgent' now use the same Button, destructive."

**Right:**
"One check first. 'Delete account' removes something forever. 'Mark as urgent' just flags a task. They're both red, but they're doing different jobs. I'd keep 'Delete account' as Button, destructive and make 'Mark as urgent' a different pattern. Same color is the drift; different job is the reason to keep them apart."

**What to do instead:** Merge patterns that do the same job. Two patterns that look alike but do different jobs stay separate, with names that say what each does.

---

## 5. A build list an agent can't follow

**User:** "Write up what the agent should do."

**Wrong:**
"Clean up the buttons and make the colors consistent."

**Right:**
"Task 3: In `src/components/`, replace `BlueButton`, `PrimaryBtn`, and the inline `<button class=\"bg-blue-600\">` on `/settings` and `/billing` with `Button` variant `primary`, which uses `var(--accent)`. Then check `/settings` and `/billing` at phone and desktop widths. And for its standing instructions: use only the named components and the design tokens; if something new is needed, flag it instead of inventing it."

**What to do instead:** One task per merge, with what to replace, what with, and where, so an agent can do it without asking.
