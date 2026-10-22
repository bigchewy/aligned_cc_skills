# The Small-Size and Print Test — Examples

One running example, made up to show the moves. A neighborhood bookshop, Dog-Ear Books, has a new mark: the top corner of a page folded down, with a thin-line drawing of a dog's head inside the fold. The mark is mustard (`#C9A227`) on a cream background (`#FDFAF6`), next to near-black text (`#2B2B2B`). It has to work as the website favicon, a phone home-screen icon for the shop's app, a one-color stamp on paper bags, and the spine of the shop's printed reading guide.

---

## Phase 1: The Mark and Its Hard Places

### Golden path

**User:** "Folded page corner with a little dog drawn in the fold. Mustard #C9A227 on cream #FDFAF6, next to text in #2B2B2B. Favicon, app icon, a rubber stamp on bags, and the spine of our reading guide."

**Say something like:**
"Good, I can picture it. The stamp and the spine are the hard ones: one color, and the spine is narrow and sideways. And the favicon, where that little dog will have about six pixels to live in."

**Why it works:** The mark, every hard place, and the hex values are collected before any judgment.

### Edge case: only has the big version

**User:** "I've only seen it as a big file on my screen."

**Say something like:**
"That's the version that always looks best. We'll shrink it in our heads first, then you'll check each size for real."

**Why it works:** The test goes ahead without pretending the big version proves anything.

---

## Phase 2: Haviv's Three Tests

### Golden path

**Say something like:**
"Sagi Haviv's three tests.
- **Appropriate:** pass. A dog-eared page fits a bookshop, and it doesn't try to show every book.
- **Distinctive and memorable:** pass. The folded corner alone is common; the dog in the fold makes it yours.
- **Simple:** problem. Two ideas, the fold and the dog, and the dog is drawn with thin lines. The dog will go first when it shrinks."

**User:** "But the dog is the whole point. It's the pun."

**Say something like:**
"It is. So the dog has to survive, which means it can't be a thin line. Hold that thought for Phase 4."

**Why it works:** Each test gets a pass or a problem with a reason, and the user's objection is carried into the phase that can settle it.

### Struggle: defends on taste

**User:** "Everyone who's seen it loves it."

**Say something like:**
"Good. That's not the test, though. Haviv's point is that liking it doesn't tell you whether it works. Let's see where it breaks."

**Why it works:** Taste is acknowledged and set aside without arguing about it.

---

## Phase 3: Draw It From Memory

### Golden path

**User:** "My partner drew a triangle in a corner and a blob with two ears."

**Say something like:**
"Then the ears are the dog. Nobody remembers the eyes, the nose, or the collar. That tells us what to cut."

**Why it works:** What people left out becomes the list of what the mark doesn't need.

---

## Phase 4: Size and Print

### Golden path

**Say something like:**
"One at a time.
- **16 pixels:** fix. The thin-line dog turns into noise. Make a small version: the fold, with two solid ears poking up from it.
- **Home-screen icon:** pass, if the fold sits at the top right and nothing important is in the cropped corners.
- **One color:** pass. The fold and ears are just shapes.
- **Reversed out:** fix. The gap between the ears closes up in cream on dark. Widen it.
- **Spine:** pass, the mark alone above the title, turned to stay upright.
Check each one for real at size and tell me what you see."

**Why it works:** Each place has its own result. The small version comes from the same mark, cut down further.

### Struggle: wants to redraw the big mark

**User:** "Should we just make the whole logo two ears and a fold, then?"

**Say something like:**
"Maybe later. For now, keep the full mark where there's room, and use the small version where there isn't. Don't redraw the big one to suit the favicon unless the small one turns out to be better everywhere."

**Why it works:** The fix stays as small as the problem.

---

## Phase 5: Color Next to Its Neighbors

### Golden path

**Say something like:**
"Josef Albers: color deceives continually. Mustard on cream looks warm and fine on your screen. The numbers say otherwise. #C9A227 on #FDFAF6 is about 2.3 to 1. That's under the 3:1 a mark needs to be seen, and far under 4.5:1 for any text in that color. Darken it to about #8A6D0F and you get about 4.7 to 1, which passes both. Then look at it next to the near-black text. Does it still feel like mustard?"

**User:** "It looks more like brass now. I kind of like it."

**Why it works:** The color is judged on the real background, with real ratios, and the fix is a specific value the user can try.

### Edge case: the color is only on dark

**User:** "On the dark bags, the mustard looks great."

**Say something like:**
"It should. #C9A227 on #2B2B2B is about 5.9 to 1. So the light version and the dark version can use different mustards. Keep the frame the same and change only the color, the way Penguin did."

**Why it works:** The same rule gives a different answer on a different ground, and the Penguin example says why that's fine.

---

## Phase 6: The Verdict

### Golden path

**Say something like:**
"Here's where it stands. Haviv's three tests: appropriate and distinctive pass; simple needs the small version. From memory: the ears are the dog. 16 px: small version. Home screen: pass. One color: pass. Reversed: widen the gap between the ears. Spine: pass. Color: #C9A227 fails on cream at 2.3:1; use about #8A6D0F on cream, keep #C9A227 on dark.

My call: ship with these fixes. The one fix that matters most is the small version with solid ears. Then check it at real size again."

**Why it works:** One verdict, one most-important fix, and every result in one place.
