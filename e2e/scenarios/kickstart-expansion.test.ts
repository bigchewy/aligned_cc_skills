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
// Expected (all types): Reading Priority references ~/.claude/about-me.md
// Expected (software): Workflows lists 8 aligned skills (brainstorming through eval-audit)
// Expected (software): Guardrails contains Iron Rules (TDD, error paths, verify, root cause)
// Expected (software): Communication has Commands section
// Expected (business): Workflows lists business skills + content generation skills
// Expected (business): Guardrails mentions confidentiality
// Expected (personal): Communication says "Direct, informal"
// Expected (personal): Guardrails mentions privacy (health, financial, relationships)
// Expected (general): Workflows is empty placeholder

// Scenario 5: About-me check — missing
// Input: ~/.claude/about-me.md does not exist
// Expected: User is prompted to create about-me.md
// Expected: If user says yes, file is created with 4-section template
//   (Role & Identity, Expertise, Methodology, Communication Style)
// Expected: User is asked about adding reference to ~/.claude/CLAUDE.md

// Scenario 6: About-me check — exists
// Input: ~/.claude/about-me.md already exists
// Expected: No prompt about about-me.md
// Expected: Scaffolding continues without interruption

// Scenario 7: About-me check — permission failure
// Input: ~/.claude/ cannot be created (simulated permission error)
// Expected: Graceful skip with informational note
// Expected: Scaffolding continues without error

// Scenario 8: Idempotency
// Input: Run kickstart in directory with existing CLAUDE.md and .claude/settings.json
// Expected: Existing files are not overwritten
// Expected: Missing directories are created
// Expected: .claude/settings.json is merged (aligned: true added, existing keys preserved)
