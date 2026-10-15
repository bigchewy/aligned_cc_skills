# Interface Inventory — Examples

One running example: a solo builder's invoicing app, about 18 months old and built mostly by an AI coding agent. It runs locally at `http://localhost:3000`. There's a `design-principles.md` at `docs/design/design-principles.md` with `--accent`, `--text`, `--text-muted`, `--border`, a 4px spacing grid, and an 8px radius.

---

## Phase 1: Round up the troops

### Golden path

**User:** "It's at localhost:3000. Yes, there's a design principles file. You can drive the browser."

**Say something like:**
"Perfect. I'm checking against `docs/design/design-principles.md`, and I'll capture at a phone width and a desktop width. Results go in `docs/design/interface-inventory-2026-10-15.md` and `.html`, with screenshots in the folder next to them."

**Why it works:** The design principles file is named up front, so every finding can be checked against it.

### Struggle: wants to skip ahead

**User:** "I already know the buttons are a mess. Can we just fix those?"

**Say something like:**
"We'll get to buttons first, promise. But if we fix buttons before we've seen everything, we'll miss that the same five grays are also in your headings and your borders. Give me the capture and you'll see it all on one page."

**Why it works:** The inventory's value is seeing every category at once; fixing one category first hides the pattern across categories.

---

## Phase 2: Prepare for screenshotting

### Golden path

**Say something like:**
"Here's the list: Dashboard, Invoices, New invoice, Invoice detail, Clients, Client detail, Settings, Billing, and the sign-in page. That's everywhere a person actually goes, plus Billing, which you said feels off. I'll go through all sixteen categories and skip Advertising and Media, since you don't have any. One example of each look, not every instance. Anything to add?"

**Why it works:** The page list covers real use, and skipped categories are named so nothing looks forgotten.

---

## Phase 3: Screenshot exercise

### Golden path

**Say something like:**
"Done. The tally: Buttons, 7 distinct looks. Colors, 11 grays and 4 blues. Forms, 3 different text field styles. Headings, 5 sizes where your principles define 3. Messaging, 2 kinds of success message, one green banner and one toast. Everything else is pretty tidy. It's all on the page now, side by side. Have a look."

**Why it works:** The tally gives a number per category, and the worst ones are called out before any naming or merging.

### Edge case: no running app

**User:** "The dev server's broken right now."

**Say something like:**
"Then I'll read it from the code. Every hard-coded color, every button class, every font size is a pattern. It's less pretty than screenshots but it finds the same duplicates."

**Why it works:** The inventory still runs, from a different source, without waiting for the app to work.

---

## Phase 4: Present Findings

### Golden path

**Say something like:**
"Buttons first, because wow. Seven buttons doing four jobs. Three of them are 'the main action,' and they're `#2563EB`, `#3B82F6`, and `var(--accent)`. Only the last one is in your tokens. Two are 'cancel': one's a gray button, one's a text link. Two are 'delete', and both are red, which is right. Does any of the blue difference look on purpose?"

**User:** "No, the agent just picked whatever."

**Say something like:**
"Ha, yep. That's the junior developer with no rails. Colors next: eleven grays…"

**Why it works:** Each finding says which job, how many looks, and which ones match the tokens, so the user can tell drift from intent.

---

## Phase 5: Name each pattern

### Golden path

**Say something like:**
"Names: Button, primary. Button, secondary. Button, destructive. Link, inline. Text field. Text field, with error. Message, success. Message, error. Heading 1 to 3. I named them for their job, so 'Button, destructive' stays right if the red changes."

**Why it works:** Names describe the job, not the look, so they survive a change of tokens.

---

## Phase 6: Regroup and Establish Next Steps

### Golden path

**Say something like:**
"Merge: the three main-action buttons into Button, primary on `var(--accent)`. The gray cancel button and the cancel link into Button, secondary. The green banner and the toast into Message, success, as a toast. Eleven grays down to the three your tokens have: `--text`, `--text-muted`, `--border`. Components: the buttons, text fields, messages, and headings. Recipe: the invoice line item row, made from a text field, a number field, and a delete button. Snowflake: the PDF preview, and that's fine. Values to add to your design principles: a fourth heading size that Billing uses, and a color for 'overdue'. Here's the build list, six tasks, each one your agent can do alone."

**Why it works:** Every pattern has a decision, missing values have one place to go, and the build list is ready to hand to an agent.

### Struggle: wants to redesign while merging

**User:** "Let's make the primary button bigger while we're at it."

**Say something like:**
"Good call to make once. Put the size in `design-principles.md` through `/aligned:create-design-principles`, and the merge picks it up. Then every primary button gets bigger, not just the ones we happen to touch."

**Why it works:** The change goes into the system, so the merge applies it everywhere.

---

## Phase 7: Write the Result

### Golden path

**Say something like:**
"Forty-one patterns down to nineteen. Hand the build list to your agent one task at a time, and put this in its instructions: use only these components and these tokens, and flag anything new. Run this again after the next big feature. Systems drift."

**Why it works:** The close gives the number, the next action, and the standing rule that keeps the drift from coming back.
