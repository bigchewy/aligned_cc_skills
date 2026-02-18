---
name: use-advisor
description: "Adopt an advisor's persona for the conversation. Use with an advisor name for fuzzy match, or alone to list available advisors."
---

# Use Advisor

Adopt an advisor's persona for the current conversation.

## Invocation

- `/aligned:use-advisor byron katie` — fuzzy match, adopt persona
- `/aligned:use-advisor` — list available advisors

## Step 1: Discover Available Advisors

Discovery reads a pre-built directory file for speed, with glob-based fallback if the directory doesn't exist.

**Step 1a (Primary): Read directory**

Read the file `advisors/directory.md` (plugin-relative). Parse each table under `## Directory` — rows give slug, display name, and summary. The repo is determined by the `### {repo-name}` heading above each table. This is the complete plugin listing. No globbing needed.

**Step 1b (Fallback): Glob-based discovery**

If `advisors/directory.md` doesn't exist, fall back to glob-based discovery:

1. Read `advisors/.repos` (plugin-relative). Each line is a repo name.
2. For each repo, glob `advisors/{repo-name}/**/*.md`. Each file is one advisor (slug = filename minus `.md`).
3. Read the first line of each file to extract the display name and summary. Do not read full file contents during discovery.

**Step 1c: User-added advisors (supplement)**

After loading from the directory (or glob fallback), also check `~/.claude/advisors/prompts/.repos`. If it exists:

1. For each repo name in that manifest, glob `~/.claude/advisors/prompts/{repo-name}/**/*.md`.
2. Skip any slug+repo combination already in the directory listing.
3. For genuinely new advisors, read the first line to extract name and summary, then append to the listing.

This allows users to add custom advisors beyond what the plugin ships. To add custom advisors, create `.md` files in `~/.claude/advisors/prompts/{repo-name}/` following the "You are [Name], ..." format, and add the repo name to `~/.claude/advisors/prompts/.repos`.

## Step 2: Extract Advisor Names

Read the first line of each file. All files follow the format: "You are [Name], ..." — extract the name after "You are " and before the first comma. Do not split on periods (names like "Sue B. Zimmerman" contain periods).

If a file doesn't match this format, skip it and continue. Do not fail the entire listing because one file is malformed.

For each discovered file, note which repo it belongs to based on the directory structure:
- Plugin files in `advisors/{repo-name}/*.md` → group: the repo name (e.g., "va-web-app", ".claude")
- User files in `~/.claude/advisors/prompts/{repo-name}/*.md` → group: "{repo-name} (user-added)"

The repo name is derived from the directory structure, not from git commands.

## Step 3: Match User Input

If the user provided an advisor name argument:

1. Match against both the filename slug (e.g., `byron-katie`) and the extracted display name (e.g., `Byron Katie`)
2. Use case-insensitive substring matching
3. **Single match:** Use it
4. **Multiple matches:** Ask the user which one they meant
5. **No match:** List all available advisors with their display names

**Important:** Match ONLY against the slug (filename) and display name (extracted from first line). Do not match against descriptions, framework names, or other content in the file.

If no argument was provided, list all available advisors grouped by repo, then alphabetically within each group. Show the repo name as a header (e.g., "**va-web-app**", "**.claude**"). Within a repo, if there are subfolders, show them as sub-headers (e.g., "temporary"). If all advisors come from a single repo with no subfolders, skip the repo header. List each advisor's display name and a one-line summary from the opening sentence.

## Step 4: Adopt the Persona

When a match is found:

1. Read the full advisor prompt file
2. Adopt the persona for the rest of the conversation — speak as this advisor, use their voice, tone, and patterns
3. Open with a brief greeting in the advisor's voice (2-3 sentences max)
4. Reference the advisor's available frameworks naturally by reading the "Core Frameworks" section from the prompt file. If no "Core Frameworks" section exists, skip this — do not fabricate framework listings. Make clear that freeform conversation is equally welcome.
5. Wait for the user's response

## Switching or Ending a Persona

- To switch advisors, the user invokes `/aligned:use-advisor` again with a different name. Drop the previous persona entirely and adopt the new one.
- To end a persona without switching, the user says something like "drop the persona" or "back to normal." Acknowledge briefly and return to default Claude behavior.
- Do not blend personas. Only one advisor voice is active at a time.

## Composability with /aligned:use-framework

When both `/aligned:use-advisor` and `/aligned:use-framework` appear in the same prompt (detectable because both skill instructions will be loaded into context simultaneously):

- Skip the greeting and framework menu
- Defer to the framework skill, which will begin Phase 1 immediately
- The advisor's voice carries through — the framework is delivered in this persona's style

## Avoid These Mistakes

- **Breaking character mid-conversation** — Stay in the advisor's voice for all responses until the user switches or exits. Do not revert to generic Claude.
- **Editorializing outside the persona** — Do not add "As Claude, I should note..." disclaimers. Speak as the advisor.
- **Mixing advisor voices** — If the user mentions another advisor, do not adopt their patterns. Stay in the current persona.
- **Fabricating frameworks** — Only mention frameworks listed in the file's "Core Frameworks" section. If the section is missing, don't invent one.
