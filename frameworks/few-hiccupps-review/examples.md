# FEW HICCUPPS Review — Examples

One running example, made up to show the moves. A solo founder builds a project-tracking web app with Claude Code and TDD. The design doc is for a weekly digest email: "Every Monday at 8am in the user's own time zone, each user gets an email listing last week's activity on their projects. It uses the existing getUserTimezone() helper in lib/time.ts. The digest shows the same items, in the same order, as the dashboard's activity feed. The unsubscribe link complies with CAN-SPAM. Users with no activity get no email." There are 22 unit tests for the digest, all passing.

---

## Phase 1: What Are We Testing, and for Whom?

### Golden path

**User:** "The digest email, not the dashboard. It matters to my users, who are team leads, and to me, because I don't want spam complaints. The tests cover building the item list and the 'no activity, no email' rule. Yes, the repo is open."

**Say something like:**
"Good. Two people who matter: the team lead reading it, and you, who'd hear about it if it went wrong. And your checks cover the list and the skip rule. Worth keeping. What they don't cover yet is the time zone, the order, and the unsubscribe link. Let's start with what the doc claims."

**Why it works:** The scope, the people who matter, and what the checks do and don't assert are all on the table before any oracle runs.

### Struggle: the tests are offered as proof

**User:** "All 22 tests pass, so the claims about the code are already verified."

**Say something like:**
"Keep the 22. They're checks, and they're doing their job. But a check confirms only what someone thought to ask. Do any of them call getUserTimezone()? Do any compare the digest's order with the activity feed's? If not, those claims are still open. When a check passes, we don't know whether the program works."

**Why it works:** The tests are welcomed and the founder isn't told to stop writing them. The gap between what the checks assert and what the doc claims becomes the next thing to look at.

---

## Phase 2: Claims, Against the Code

### Golden path

**User:** "I opened lib/time.ts. There's no getUserTimezone(). There's getTimezone(userId), and it returns null if the user never set one."

**Say something like:**
"That's a claim contradicted by the code. Two findings, really. The name is wrong, which is easy. And the doc assumes every user has a time zone, but the code says some don't. What does 8am mean for a user with no time zone? The design doesn't say. That might be a problem, and it's inconsistent with the Claims oracle. Cheap to fix now."

**Why it works:** The claim was checked by reading the file, not by trusting the doc or a test. One contradicted claim turned up a missing decision.

### Edge case: the code can't be read

**User:** "The activity feed is in a separate service I don't have access to."

**Say something like:**
"Then that claim stays 'not confirmed.' The doc says the digest matches the feed's items and order. Until someone reads the feed's code or asks whoever owns it, we can't tell. Put it on the list for before you build."

**Why it works:** An unreadable claim is marked, not assumed true.

---

## Phase 3: History and Product

### Golden path

**User:** "History: nothing sends email on a schedule today, so nothing changes. Product: the password reset email uses a different template and no unsubscribe link."

**Say something like:**
"Let's check the first part. Does the digest add a cron job or a queue that other jobs share? If it shares one, it could change their timing. On the second: the reset email is transactional, so it doesn't need an unsubscribe link. The digest does. That difference is on purpose. But the template difference is worth a sentence in the doc, or the two will drift."

**Why it works:** "Nothing changes" gets checked instead of accepted, and a Product inconsistency is judged as intended or not.

---

## Phase 4: Purpose and User Desires

### Struggle: only the planned use

**User:** "Purpose is: read last week's activity."

**Say something like:**
"That's the explicit use. What are the implicit ones? A team lead might forward it to their boss. Someone might open it on Monday afternoon after a long weekend. Someone might want it on Friday instead. What would a reasonable user want here that the design doesn't give them?"

**Why it works:** The prompt for implicit uses comes from the user's own people, not from a generic list.

---

## Phase 5: World, Familiarity, and Explainability

### Golden path

**User:** "World: daylight saving time. 8am on the Monday the clocks change. Familiarity: we had a bug last year where a job ran twice after a deploy. Explainability: I can't explain what happens if someone changes time zones on Sunday night."

**Say something like:**
"Three good ones. Daylight saving is a World problem: the doc assumes every Monday has an 8am that happens once. The job running twice is your own bug history, which is the best Familiarity oracle you have. Two digests on one Monday is a possible problem. And the part you can't explain is the part nobody has decided yet. Each of these could become a check before you build."

**Why it works:** Each finding names its oracle and comes from the founder's own knowledge, and the founder is pointed toward new checks.

---

## Phase 6: Image, Comparable Products, and Statutes and Standards

### Edge case: a group finds nothing

**User:** "Image and Comparable Products, I've got nothing. CAN-SPAM I'm not sure about. I think it needs a physical address."

**Say something like:**
"Nothing for Image and Comparable Products is fine. An oracle that finds nothing still did its job. On CAN-SPAM, the doc claims compliance and you're not sure what compliance requires. That's a finding: the claim isn't backed yet. Check the rule itself before you build, not after."

**Why it works:** Empty oracles aren't padded, and an unsupported claim of compliance is treated as a possible problem.

---

## Phase 7: The Problem List and What the Checks Miss

### Golden path

**User:** "Which of these become tests?"

**Say something like:**
"The null time zone, the daylight saving Monday, and 'no activity, no email' across a time zone change can all be checks. Write them first, the way you already do. The double send after a deploy might be a check too, if you can make it repeat. The order matching the feed needs someone to look at both, side by side, with real data. And we didn't look at load or deliverability. Say that in the doc."

**Why it works:** Findings split into checks for the TDD workflow and things a person has to try, and the review says what it didn't cover.
