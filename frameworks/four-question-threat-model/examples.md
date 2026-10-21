# Four Question Threat Model — Examples

One running example, made up to show the moves. A solo founder is adding team invites to a Next.js app on Supabase. An owner types an email address. The app writes a row to an `invites` table and sends a link through Resend. The invitee clicks the link, signs in, and is added to `team_members`. A Resend webhook reports bounces back to an API route.

---

## Phase 1: What are we working on?

### Golden path

**User:** "Just the invite flow. Browser calls `/api/invite`, which inserts into `invites` and calls Resend. The email link goes to `/accept?token=...`, which inserts into `team_members`. Resend posts bounces to `/api/resend-webhook`. Boundaries: browser to my routes, my routes to Supabase, my app to Resend, Resend back to me. We're protecting who's on which team, and the team's data."

**Say something like:**
"Good. That's a diagram. Four boundaries, and the thing we're protecting is team membership. Let's go to the second question."

**Why it works:** Scoped to the part being worked on now, with flows and boundaries named in plain words.

### Struggle: the whole product

**User:** "Can we threat model the whole app? It's got billing, teams, uploads, the AI summaries..."

**Say something like:**
"Which part are we working on right now? Invites? Then that's this hour. Billing gets its own hour when you touch it."

**Why it works:** "What are we working on?" keeps the work small enough to finish.

### Edge case: no idea where the boundaries are

**User:** "I don't really know what counts as a boundary."

**Say something like:**
"Anywhere a request comes from outside, or your code talks to something it doesn't own. The browser hitting your route. Your route hitting Supabase. Resend calling you back. What enforces each one?"

**Why it works:** A boundary is defined by where it is and what enforces it, not by the word "trust."

---

## Phase 2: What can go wrong?

### Golden path

**User:** "Spoofing: the webhook. Anyone could post a fake bounce. Tampering: the accept route takes `team_id` from the query string, so someone could change it. Information disclosure: the `invites` table, I'm not sure RLS is on. Elevation of privilege: the accept route uses the service-role key to insert."

**Say something like:**
"Four real ones, each on a part of the picture. The `team_id` in the query string is the big one: change the number, join someone else's team. Using the service-role key there means RLS isn't checking it at all."

**Why it works:** STRIDE run on the flows that cross boundaries, and the threats are specific to this design.

### Struggle: "it's behind auth"

**User:** "The accept page requires login, so it's fine."

**Say something like:**
"Login tells us who they are. Does it tell us which team they're allowed to join? What stops a logged-in user from editing the token or the team ID?"

**Why it works:** It separates spoofing (who you are) from elevation of privilege (what you're allowed to do).

### Edge case: the design includes an LLM

**User:** "The invite email has an AI-written welcome line based on the team's description."

**Say something like:**
"Note that part. The team description is text a user wrote, going into a model, coming out in an email. That gets its own lens. We'll run `phantom-b-llm-threats` on it after this."

**Why it works:** STRIDE covers the system; the LLM part is flagged for the lens built for it.

---

## Phase 3: What are we going to do about it?

### Golden path

**User:** "Accept route: take the team from the invite row, not the query string, and use the user's session client so RLS applies. Mitigate. Webhook: verify Resend's signature. Mitigate. RLS on `invites`: turn it on, owner-only select. Repudiation: we don't log who sent invites. I'll accept that for now, small team."

**Say something like:**
"Three fixes and one written accept. That's what 'going to do about it' looks like. Put the accept in the doc with the reason."

**Why it works:** Each threat has a decision, including an accept on purpose.

### Struggle: wants to fix everything before shipping

**User:** "I should add rate limiting, audit logs, and CAPTCHA before I ship anything."

**Say something like:**
"Which of those has to change before this ships? The `team_id` one does. Rate limiting can be a ticket. 'Going to do' is a future action. A ticket is still a decision."

**Why it works:** It keeps the model from turning into a blocker.

### Edge case: don't build it

**User:** "I was going to store the invitee's phone number too, for SMS later."

**Say something like:**
"Do you use it now? If not, that's data you have to protect and never use. Sometimes the answer is 'it's not worth it.' Don't collect it."

**Why it works:** Eliminating the data is a valid answer to "What are we going to do about it?"

---

## Phase 4: Did we do a good job?

### Golden path

**User:** "Diagram, yes. Five threats. Four tickets and one accept. I didn't look at what happens if the invite token never expires."

**Say something like:**
"Good catch on the last one. That's a Phase 2 item we skipped. Add it: tokens should expire. Would you do this again on the next feature?"

**Why it works:** Q4 checks the work and finds the gap, and asks whether the method was worth it.

### Edge case: needs real assurance

**User:** "A customer's security team wants a written threat model before they sign."

**Say something like:**
"Then fast and cheap is a start, not the finish. They want a record. Write this up properly, and expect to go deeper on the parts they care about."

**Why it works:** "We might want records that can be shared with customers or regulators." That's the signal to go deeper.
