# Breadboard to Pages — Anti-Examples

Failure modes to avoid, each with the input that triggers it, the wrong response, the right response, and what to do instead.

---

## 1. Lorem ipsum in the pages

**User:** "Just use lorem ipsum for now, I'll write the copy later."

**Wrong:**
"Sure. Here's Team Settings with 'Lorem ipsum dolor' as the team name and three members named 'Member Name'."

**Right:**
"I'd rather not. Lorem ipsum always fits, and that's the problem. The page exists to find out whether 'Thursday Morning Accountability Crew' and an email like jennifer.rodriguez-castellanos@example.co.uk fit next to the role menu on a phone. I'll write realistic copy and mark every line for you to check."

**What to do instead:** Write realistic content when none is given, including the longest value the app allows, and mark it for the user to check. Pages are where the system gets tested, and placeholder text passes every test.

---

## 2. A one-off value on one page

**User:** "The primary blue is dull. On this page use #2F80FF, and round these cards to 16px."

**Wrong:**
```css
.member-card { background: #2F80FF; border-radius: 16px; }
```

**Right:**
"If the blue is dull, it's dull on every page. Change it in `design-principles.md` and everything gets it. Putting #2F80FF on Team Settings gives you two blues, and nobody will remember which page gets which. Same with the corners: your tokens say 8px. Want to run `/aligned:create-design-principles` and change them there? For now I'm drawing with `var(--accent)` and `var(--radius-md)`."

**What to do instead:** Every value comes from a token. When the user wants a different value, change the token for everyone or use what exists. Count raw values in Phase 5 and get the count to zero.

---

## 3. Only the happy path

**User:** "Looks good. We're done, right?"

**Wrong:**
"Yes! Here's the final Team Settings page with four members, all short names, everything loaded."

**Right:**
"Almost. That's the best case. What does the owner see the first day, with no one invited yet? What about a team of ten? What does a member who isn't the owner see on this same page? Fewer buttons, I'd guess. Let me draw those on the Variations switch, then we're done."

**What to do instead:** A page isn't finished until its variations are drawn: empty, one, many, long text, error, loading when it waits, and every other role who sees the place.

---

## 4. Inventing visual rules

**User:** "My design principles don't have a type scale for headings. Just pick something nice."

**Wrong:**
"I'll use a 1.25 major third scale: 16, 20, 25, 31, 39. That's the Atomic Design way."

**Right:**
"Atomic Design doesn't set type sizes, and I won't make some up and call them mine. Your file has a body size and one headline size. I'll draw with those, and I'll list 'heading sizes between body and headline' under values to add. `/aligned:create-design-principles` is where that decision gets made, once, for every page."

**What to do instead:** Use only what `design-principles.md` defines. Name each missing value and send it to the design principles skill. Brad Frost publishes no type scale, palette, contrast rule, or spacing scale, so never present one as his.

---

## 5. An element with no breadboard item behind it

**User:** "Add a little activity feed on the side of Team Settings. It'll look nice on desktop."

**Wrong:**
"Done. I added a Recent Activity panel on the right with five sample events."

**Right:**
"What's the owner doing when they'd use it? There's no activity feed on the breadboard, so on the page it would have nothing behind it. If it's a step the owner really takes, it goes on the story map and the breadboard first, then I'll draw it. If it's just to fill the desktop width, the desktop page can simply have more room."

**What to do instead:** Every element carries `data-from` naming its breadboard item. An element with nothing behind it goes back to the map and breadboard, or comes off the page.
