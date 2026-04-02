/**
 * Kickstart Expansion — Eval Scenarios
 *
 * These scenarios verify the kickstart skill correctly scaffolds
 * all 4 project types with appropriate structure and CLAUDE.md content.
 *
 * Run context: Each scenario should be executed in a fresh temp directory
 * with the aligned plugin enabled.
 */

// Scenario 1: Type selection routing
// Input: User selects each of the 4 types (A/B/C/D)
// Expected: Software type asks tech stack questions (3-5)
// Expected: Business/Personal/General skip tech stack questions
// Expected: All types ask project name and description (questions 1-2)

// Scenario 2: Base structure — all types
// Input: Any project type, project name "test-project"
// Expected: CLAUDE.md exists at root
// Expected: .claude/settings.json exists with enabledPlugins.aligned = true
// Expected: docs/ directory exists
// Expected: docs/lessons-learned/ directory exists

// Scenario 3: Software additions — software type only
// Input: Software type selected
// Expected: docs/design/design-principles.md exists with placeholder content
// Expected: docs/architecture.md exists with Mermaid template
// Expected: docs/plans/completed/ exists
// Expected: docs/kanban/todo/, in-progress/, done/, did_not_complete/ exist
// Expected: docs/kanban/.counter exists with content "1"
// Expected: docs/mockups/ exists
// Expected: docs/lessons-learned/completed/ exists
// Expected: e2e/scenarios/, e2e/fixtures/profiles/ exist
// Expected: e2e/eval-config.ts, e2e/eval-runner.ts exist
// Expected: e2e/.gitignore exists
// Expected: scripts/ exists
// Expected: eslint-rules/ exists
// NOT expected for Business/Personal/General types

// Scenario 4: CLAUDE.md content per type
// Input: Each project type with name "test-project", description "A test"
// Expected (all types): Has 6 sections (Identity, Folder Map, Reading Priority,
//   Communication, Guardrails, Workflows)
// Expected (software): Workflows lists 8 aligned skills (brainstorming through eval-audit)
// Expected (software): Guardrails contains Iron Rules (TDD, error paths, verify, root cause)
// Expected (software): Communication has Commands section
// Expected (business): Workflows lists business skills + content generation skills
// Expected (business): Guardrails mentions confidentiality
// Expected (personal): Communication says "Direct, informal"
// Expected (personal): Guardrails mentions privacy (health, financial, relationships)
// Expected (general): Workflows is empty placeholder

// Scenario 5: Global permission setup — first run
// Input: ~/.claude/settings.json has no aligned skill permissions
// Expected: permissions.allow array is created with all aligned skill entries
// Expected: Existing keys in settings.json are preserved
// Expected: User is told permissions were set up

// Scenario 6: Global permission setup — already configured
// Input: ~/.claude/settings.json already contains Skill(aligned:brainstorming)
// Expected: Phase is skipped silently
// Expected: No modifications to ~/.claude/settings.json

// Scenario 7: Idempotency
// Input: Run kickstart in directory with existing CLAUDE.md and .claude/settings.json
// Expected: Existing files are not overwritten
// Expected: Missing directories are created
// Expected: .claude/settings.json is merged (aligned: true added, existing keys preserved)

// Scenario 9: Brainstorming unification (v0.13.0)
// Context: /aligned:business-brainstorming was merged into /aligned:brainstorming
// Expected (business template): Workflows section references /aligned:brainstorming, not /aligned:business-brainstorming
// Expected (personal template): Next-step message references /aligned:brainstorming
// Expected (general template): Next-step message references /aligned:brainstorming
// Expected (software template): No change — already used /aligned:brainstorming
