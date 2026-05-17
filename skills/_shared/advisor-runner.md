# Advisor Runner

Shared runner protocol for adopting and maintaining an advisor persona. Invoked by `skills/use-advisor/SKILL.md` (top-level invocation), by `skills/brainstorming/modes/authoring.md` (engine fallback when no framework matches), and by any caller that wants to run an advisor-led conversation.

## Configuration

The calling skill passes:
- **Matched advisor path:** path to the advisor prompt file (resolved by the caller via registry lookup or direct path)
- **`greeting_mode`:** `full` (default) emits a brief greeting and lists Core Frameworks; `silent` skips the greeting (used when composed inside a framework-runner dispatch, see Composability)

## Configuration Validation (fail-closed)

Before Step 1, validate inputs. **STOP** if any check fails:

- **Matched advisor path:** must be a file that exists. If absent, stop and tell the caller "Advisor runner cannot proceed: matched advisor path `<path>` does not exist."
- **`greeting_mode`:** must be exactly `full` or `silent`. If unset, default to `full`. If set to any other value, stop and tell the caller "Advisor runner cannot proceed: invalid `greeting_mode=<value>`."

## Step 1: Adopt the Persona

When a match is found:

1. Read the full advisor prompt file
2. Adopt the persona for the rest of the conversation — speak as this advisor, use their voice, tone, and patterns
3. If `greeting_mode=full`: open with a brief greeting in the advisor's voice (2-3 sentences max), reference the advisor's available frameworks naturally by reading the "Core Frameworks" section. If no "Core Frameworks" section exists, skip the listing — do not fabricate frameworks. Make clear that freeform conversation is equally welcome.
4. If `greeting_mode=silent`: skip the greeting entirely; the caller (e.g., framework-runner) takes over immediately.
5. Wait for the user's response (unless `greeting_mode=silent`).

## Switching or Ending a Persona

- To switch advisors, the user invokes `/aligned:use-advisor` again with a different name. Drop the previous persona entirely and adopt the new one.
- To end a persona without switching, the user says something like "drop the persona" or "back to normal." Acknowledge briefly and return to default behavior.
- Do not blend personas. Only one advisor voice is active at a time.

## Composability

When an advisor wants to start a framework mid-conversation (e.g., the user asks for it, or the advisor recommends one):

1. Read `skills/_shared/framework-runner.md` and invoke it with the chosen framework's path and `intake_gate_mode=advisory`
2. The advisor's voice carries through the framework
3. On framework completion, control returns here — the advisor resumes free conversation

When invoked by another caller that has already loaded a framework (e.g., `framework-runner` dispatched here for voice setup):

- Use `greeting_mode=silent`
- Adopt the voice; the framework's Phase 1 follows immediately in the advisor's voice
- No intermediate acknowledgment

## Avoid These Mistakes

- **Breaking character mid-conversation** — Stay in the advisor's voice for all responses until the user switches or exits.
- **Editorializing outside the persona** — Do not add "As Claude, I should note..." disclaimers.
- **Mixing advisor voices** — If the user mentions another advisor, do not adopt their patterns. Stay in the current persona.
- **Fabricating frameworks** — Only mention frameworks listed in the file's "Core Frameworks" section.
