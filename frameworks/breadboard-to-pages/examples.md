# Breadboard to Pages — Examples

One running example: a solo builder's team habit tracker. Slice 1 of the story map has the owner set up a team and invite people. The breadboard for that slice has three places:

```
Team Settings
  team name (edit)        -> Team Settings
  Invite (email, role)    -> Invite Sent
  member row: role menu   -> Team Settings
  member row: Remove      -> Confirm Remove

Confirm Remove
  Remove {name}           -> Team Settings
  Cancel                  -> Team Settings

Invite Sent
  Invite another          -> Team Settings
  Done                    -> Team Settings
```

The project's `design-principles.md` is at `brand/guidelines/design-principles.md`, with tokens such as `--bg`, `--surface`, `--text`, `--text-muted`, `--accent`, `--danger`, `--space-1` to `--space-8` on a 4px grid, `--radius-md` (8px), and type roles headline, body, label, and data.

---

## Setup

### Golden path: everything is there

**What happens:** The framework finds one `design-principles.md` and the story map at `docs/story-maps/team-habits.md`, which ends with this breadboard.

**Say something like:**
"I'm building from `brand/guidelines/design-principles.md` and the breadboard at the end of `docs/story-maps/team-habits.md`. The screens go in `docs/story-maps/team-habits-screens.md` and `.html`, right next to the map."

**Why it works:** Saying which file supplied the tokens means a page in the wrong brand gets caught on the first draw, not after the build.

### Struggle: no design principles

**User:** "I don't have a design-principles file. Just use something clean."

**Say something like:**
"There's no design system to build from yet, and I'd be inventing every value. Run `/aligned:create-design-principles` first. It takes about twenty minutes, and then every page we draw uses the same blue, the same spacing, and the same type. Come back with the file and we'll start."

**Why it works:** The framework's promise is that every value comes from the system. Drawing from made-up values would produce screens the builder can't trust.

---

## Phase 1: Inventory the Parts

### Golden path

**Say something like:**
"Hooray, a breadboard! Three places: Team Settings, Confirm Remove, and Invite Sent. Here's the first pass at parts:

| Affordance | Part | Kind | In the system? |
|---|---|---|---|
| team name (edit) | text field with save | molecule | component, new |
| Invite (email, role) | invite form: email field, role menu, button | organism | recipe of existing parts |
| member row | avatar initial, name, email, role menu, Remove | molecule | component, new |
| Remove {name} | danger button | atom | component, uses `--danger` |
| Invite another, Done | secondary and primary button | atoms | components |

The member row is the one I'd watch. It shows up on every team page you'll ever build, so it's a component, not a snowflake. Does this match what you have?"

**Why it works:** Sorting each affordance into component, recipe, or snowflake before drawing means the second page reuses what the first one made.

### Edge case: a missing token

**Say something like:**
"Your design principles don't have a color for a destructive button. I won't make one up. Your file has `--danger` for error text. I can use that for the Remove button, or it goes into `design-principles.md` as its own token. Which?"

**Why it works:** The value gets decided once, in the system, instead of on one page.

---

## Phase 2: Template Each Place

### Golden path

**Say something like:**
"Team Settings first. On a phone, what does the owner come here to do? I think it's invite people. Here's the template:

1. Team name: headline role, `--text`. Longest: 'Thursday Morning Accountability Crew', 36 characters.
2. Invite form: email field, role menu, primary button. Longest email: 48 characters.
3. Member list heading: label role, `--text-muted`.
4. Member rows: name in body, `--text`; email in body, `--text-muted`; role menu; Remove as a quiet text button.

I stepped the emails and the list heading down to `--text-muted` so the names lead. That's Refactoring UI's 'De-emphasize to emphasize', from Wathan and Schoger. And I dropped the 'Name:' and 'Email:' labels. A name and an email explain themselves. That's their 'Labels are a last resort.' Does this order match?"

**Why it works:** Every hierarchy choice uses a role and a color the file already defines, and the borrowed rules are named as Refactoring UI's, not presented as Atomic Design.

### Struggle: wants desktop first

**User:** "Most people will use this on a laptop. Can we start there?"

**Say something like:**
"Small screen first anyway. It forces the question of what matters most, and the laptop version is the same template with more room. We'll draw both, side by side."

**Why it works:** "using the constraints of small screens to force the team to focus on the core content and hierarchy." The desktop page still gets drawn.

---

## Phase 3: Pages with Real Content

### Golden path

**What the markup looks like:** each element names where it came from.

```html
<template class="screen-src">
  <main class="ts">
    <h1 class="ts-name" data-from="Team Settings › team name">Thursday Morning Accountability Crew</h1>
    <form class="invite" data-from="Team Settings › Invite">
      <input type="email" value="jennifer.rodriguez-castellanos@example.co.uk" data-from="Team Settings › Invite › email">
      <select data-from="Team Settings › Invite › role"><option>Member</option></select>
      <button class="btn-primary" data-from="Team Settings › Invite">Invite</button>
    </form>
    <ul class="members">
      <li class="member" data-from="Team Settings › member row">…</li>
    </ul>
  </main>
</template>
```

```css
.ts { padding: var(--space-4); display: grid; gap: var(--space-6); background: var(--bg); color: var(--text); }
.btn-primary { background: var(--accent); border-radius: var(--radius-md); padding: var(--space-2) var(--space-4); }
@container (min-width: 900px) { .ts { grid-template-columns: 2fr 3fr; } }
```

**Say something like:**
"Three pages, phone and desktop, on the Pages tab. Flip 'Show sources' to see where each element comes from. The real content found one thing: on the phone, the long email pushes the role menu onto its own line. I let it wrap below the email instead of truncating it, because the owner needs to see the whole address to know they typed it right. On desktop, the invite form sits beside the member list. Which page looks wrong to you?"

**Why it works:** Real content found a problem a placeholder would have hidden, and the desktop page is the same markup with more room.

---

## Phase 4: Variations

### Golden path

**Say something like:**
"Same templates, different content. Team Settings has five variations that change it:
- **Empty:** just the owner. The member list says 'It's just you so far. Invite someone above.'
- **One:** one other member. Looks fine.
- **Many:** ten members. The list gets long on the phone, so the invite form stays at the top.
- **Long text:** the 48-character email, already handled.
- **Member, not owner:** the same page with no invite form, no role menus, and no Remove. Just the list.

The one I'd worry about is 'member, not owner'. Nobody had drawn it, and it's what eight out of nine people on a team will see."

**Why it works:** "Users with administrative privileges might see additional buttons and options." The other role was missing until the variations made someone draw it.

---

## Phase 5: System Check

### Golden path

**Say something like:**
"System check. Raw values outside the tokens: none. Parts doing the same job two ways: the Done button on Invite Sent was a link, and every other primary action is a button. I made it a button. New components: member row, invite form. Recipes: none. Snowflakes: the 'It's just you so far' empty message, which only this page needs. Values your design principles don't have yet: a destructive button color and a heading size between body and headline. Those go to `/aligned:create-design-principles`."

**Why it works:** The check is a count and a list, not an opinion, and every missing value has one place to go.

---

## Phase 6: Walk the Pages Against the Story Map

### Golden path

**Say something like:**
"Let's walk it. Dana wants to set up her team. She lands on Team Settings and types the team name into the headline field (`Team Settings › team name`). She invites Sam: email, role, Invite (`Team Settings › Invite`), and that takes her to Invite Sent. She taps Invite another and comes back. Then she changes Sam's role with the menu on his row. Walking it, I found one gap: the map has 'See who accepted', and no page shows whether an invite was accepted. Is that a real step for Slice 1?"

**Why it works:** The walk follows the story map's steps in order and names the element for each one by its source, so a step with no element shows up as a gap.

### Edge case: the gap is on the map, not the screen

**User:** "Yes, she needs to see who hasn't accepted yet."

**Say something like:**
"That's a hole in the story. It goes on the map under 'Invite the team' and on the breadboard as an affordance on Team Settings, a 'pending' state on the member row. Then I'll add it to the page and to the Variations."

**Why it works:** The page never gets ahead of the map and breadboard.
