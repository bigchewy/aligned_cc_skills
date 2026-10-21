# Framework Runner

Shared runner protocol for executing a matched framework. Invoked by `skills/use-framework/SKILL.md` (top-level invocation) and by `skills/brainstorming/modes/authoring.md` (engine selection via contextual-recommendation).

## Configuration

The calling skill passes:
- **Matched framework path:** absolute path to the framework folder containing `prompt.md` / `examples.md` / `anti-examples.md`
- **`intake_gate_mode`:** `strict` or `advisory` (default `advisory`)
- **`framework_entry`** (optional): the framework's merged entry from `skills/_shared/resolve-framework-source.md`. When absent, the runner reads the advisor from the first line of `prompt.md` (see Step 0).

## Configuration Validation (fail-closed)

Before Step 1, validate inputs. **STOP** if any check fails:

- **Matched framework path:** must be an absolute path AND must be a directory AND must contain at least `prompt.md`. If absent, stop and tell the caller "Framework runner cannot proceed: matched framework path `<path>` is missing or has no prompt.md."
- **`intake_gate_mode`:** must be exactly `strict` or `advisory`. If unset, default to `advisory`. If set to any other value, stop and tell the caller "Framework runner cannot proceed: invalid `intake_gate_mode=<value>`."

These checks fail closed — the runner refuses to start with invalid inputs rather than silently degrading.

## Step 0: Load the Framework's Advisor

Skip this step if an advisor persona is already active (for example, `skills/use-advisor/SKILL.md` or `skills/_shared/advisor-runner.md` dispatched this runner). That persona sets the voice.

Otherwise, find the framework's advisor:

1. Get the advisor from `framework_entry.advisor`. If no `framework_entry` was passed, read the first line of `prompt.md` ("You are {Advisor}, ...") and take the name after "You are " and before the first comma.
2. Read `skills/_shared/resolve-advisor-source.md` and follow its procedure to get the merged advisor set (plugin + project-local). Match the advisor by `id` first, then by display `name`, ignoring case. A local framework may name a plugin advisor or a local advisor.
3. On a match, read `skills/_shared/advisor-runner.md` and invoke it with that entry's `absolute_prompt_path` and `greeting_mode=silent`. The advisor's own prompt, including a project-local one, sets the voice.
4. On no match (or no advisor named), do not stop. The generic-facilitator fallback in Voice applies.

## Step 1: Load Framework Content

Read three files from the matched framework's directory:

1. `prompt.md` — the phase-by-phase guide (required)
2. `examples.md` — calibration examples per phase (read if exists, skip silently if missing)
3. `anti-examples.md` — failure modes to avoid (read if exists, skip silently if missing)

If `prompt.md` is missing or empty, report the error and stop. Do not attempt to run a framework without its prompt.

## Step 2: Apply the Intake Gate

If the framework's registry entry (or its `prompt.md` YAML frontmatter) lists `required_documents`:

- **`advisory` mode (default):** Note the missing documents to the user as a one-line observation; proceed with Phase 1 regardless. Preserves existing `use-framework` behavior.
- **`strict` mode:** Pause and prompt the user with the missing-document list. Options the user can pick from:
  - Provide a path to each missing document
  - Mark missing documents as N/A and proceed (the framework will run without that input)
  - Downgrade to advisory for this session

Strict mode is used when the framework is part of a larger brainstorming flow that expects each gate to be honored before continuing.

`helpful_documents` are noted but never gate execution regardless of mode.

## Step 3: Run the Framework

1. Inject all loaded content as operating instructions.
2. Begin Phase 1 immediately with the framework's scripted opening.
3. Complete each phase fully before advancing to the next.
4. **WAIT** for the user's response at each marked pause point — do not continue until they respond.
5. Use examples from `examples.md` to calibrate responses.
6. Actively avoid patterns described in `anti-examples.md`.

A phase is complete when: (a) the scripted content for that phase has been delivered, (b) the user has responded to all prompts within the phase, and (c) any reflection or summary the phase calls for has been provided.

## Voice

- If an advisor persona is active (via `skills/_shared/advisor-runner.md`, `/aligned:use-advisor`, or Step 0): deliver the framework in that advisor's voice.
- Prefer the resolved advisor prompt from Step 0 over the framework prompt's one-line opening. A project-local advisor prompt carries the project's own voice rules.
- If Step 0 found no advisor: follow the framework prompt as-is — it names an advisor in its opening line, so adopt that advisor's voice as written.
- If a framework's `prompt.md` references an advisor that cannot be resolved (missing advisor / broken reference): fallback to generic facilitator voice — narrate each phase neutrally without impersonating the missing advisor. Log a Decision Log entry noting the fallback.

<!-- DECISION-LOG conflict="stop vs fallback when a framework references a non-existent advisor" choice="fallback to generic facilitator voice" reason="stopping would break the user's framework session for a missing voice detail; graceful degradation preserves the framework's substance" confidence="0.85" -->

## Composability

When invoked alongside an active advisor persona (advisor-runner running):

1. The advisor sets the voice
2. The framework sets the structure
3. Begin Phase 1 immediately in the advisor's voice
4. No intermediate acknowledgment — straight into the framework

On framework completion, control returns to the caller (advisor mid-conversation, or the brainstorming authoring mode for post-engine dispatch).

## Avoid These Mistakes

- **Skipping phases** — Complete every phase in order.
- **Rushing past pause points** — When the framework says to wait for a response, stop. Do not continue with the next question or phase in the same message.
- **Combining multiple frameworks** — Run one framework per session.
- **Improvising structure** — Follow the framework's phases exactly as written.
- **Ignoring anti-examples** — Treat anti-example patterns as hard constraints.
