# Settings Security: Pre-Commit Hook & Secret Scanner Improvements

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Catch secrets at commit time (before the 10-minute auto-push) instead of days later via the cron audit, add tests for security-critical regex patterns, and fill pattern coverage gaps.

**Source Design Doc:** N/A — derived from QA Advisor and Architect critique of the secret scanning feature in `~/.claude/crons/settings-audit.js`

**Architecture:** Extract `SECRET_PATTERNS` to a shared Node.js module (`secret-patterns.js`). Create a pre-commit scanner (`pre-commit-secrets.js`) that reuses those patterns to scan staged diffs. Install it as a git pre-commit hook with self-healing via `autocommit.sh`. Tests use Node's built-in test runner (`node:test`, requires Node 18+; current environment is Node 22).

**Tech Stack:** Node.js (node:test, child_process, fs), Git hooks, Bash

**Target working directory:** `~/.claude/` (the Claude Code config repo, NOT the current plugin repo)

---

## Prerequisites

> Complete these steps manually before starting Task 1.

- [ ] Verify Node.js >= 18 is installed: `node --version` (needed for `node:test` built-in test runner)
- [ ] Verify you're working in the `~/.claude/` directory: `cd ~/.claude && git status`

---

### Task 1: Create shared secret patterns module with tests

**Files:**
- Create: `crons/secret-patterns.js`
- Create: `crons/secret-patterns.test.js`

**Step 1: Write the test file**

Create `crons/secret-patterns.test.js`:

```js
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const { SECRET_PATTERNS, SECRET_SCAN_SKIP } = require('./secret-patterns');

describe('SECRET_PATTERNS', () => {
  // Helper: returns true if any pattern matches the line
  function matchesAny(line) {
    return SECRET_PATTERNS.some(p => p.regex.test(line));
  }

  // Helper: returns the desc of the first matching pattern
  function firstMatch(line) {
    const m = SECRET_PATTERNS.find(p => p.regex.test(line));
    return m ? m.desc : null;
  }

  describe('Anthropic API key', () => {
    it('detects sk-ant- prefixed keys', () => {
      assert.ok(matchesAny('ANTHROPIC_KEY="sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"'));
    });

    it('rejects short sk-ant- fragments', () => {
      assert.ok(!matchesAny('sk-ant-short'));
    });
  });

  describe('AWS access key', () => {
    it('detects AKIA prefixed keys', () => {
      assert.ok(matchesAny('aws_key = "AKIAIOSFODNN7EXAMPLE"'));
      assert.equal(firstMatch('AKIAIOSFODNN7EXAMPLE'), 'AWS access key (AKIA...)');
    });

    it('rejects non-uppercase AKIA keys', () => {
      assert.ok(!matchesAny('AKIAiOSFODNN7EXAMPL'));
    });
  });

  describe('GitHub token', () => {
    it('detects ghp_ personal access tokens', () => {
      assert.ok(matchesAny('token: "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn"'));
    });

    it('detects ghs_ server tokens', () => {
      assert.ok(matchesAny('ghs_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmn'));
    });

    it('rejects short GitHub tokens', () => {
      assert.ok(!matchesAny('ghp_tooshort'));
    });
  });

  describe('GitLab token', () => {
    it('detects glpat- prefixed tokens', () => {
      assert.ok(matchesAny('GITLAB_TOKEN="glpat-abcdefghijklmnopqrstuvwxyz"'));
    });
  });

  describe('Slack token', () => {
    it('detects xoxb- bot tokens', () => {
      assert.ok(matchesAny('SLACK_TOKEN="xoxb-1234567890-abcdef"'));
    });

    it('detects xoxp- user tokens', () => {
      assert.ok(matchesAny('xoxp-1234567890-abcdef'));
    });
  });

  describe('Private key', () => {
    it('detects RSA private key headers', () => {
      assert.ok(matchesAny('-----BEGIN RSA PRIVATE KEY-----'));
    });

    it('detects generic private key headers', () => {
      assert.ok(matchesAny('-----BEGIN PRIVATE KEY-----'));
    });

    it('detects EC private key headers', () => {
      assert.ok(matchesAny('-----BEGIN EC PRIVATE KEY-----'));
    });

    it('detects OPENSSH private key headers', () => {
      assert.ok(matchesAny('-----BEGIN OPENSSH PRIVATE KEY-----'));
    });
  });

  describe('Bearer token', () => {
    it('detects Bearer tokens with 20+ char values', () => {
      assert.ok(matchesAny('Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI'));
    });

    it('rejects short Bearer values', () => {
      assert.ok(!matchesAny('Bearer short'));
    });
  });

  describe('key-value secret assignment', () => {
    it('detects api_key assignments with quoted values', () => {
      assert.ok(matchesAny('api_key = "abcdefghijklmnopqrstuvwxyz1234"'));
    });

    it('detects apiKey assignments', () => {
      assert.ok(matchesAny('apiKey: "abcdefghijklmnopqrstuvwxyz1234"'));
    });

    it('detects password assignments', () => {
      assert.ok(matchesAny('password = "abcdefghijklmnopqrstuvwxyz1234"'));
    });

    it('rejects values shorter than 20 chars', () => {
      assert.ok(!matchesAny('api_key = "short"'));
    });
  });

  describe('hex secret assignment', () => {
    it('detects SECRET hex assignments', () => {
      assert.ok(matchesAny('SECRET = "aabbccdd00112233445566778899aabb00112233"'));
    });

    it('detects ENCRYPTION_KEY hex assignments', () => {
      assert.ok(matchesAny('ENCRYPTION_KEY: "aabbccdd00112233445566778899aabb00112233"'));
    });
  });

  describe('no false positives on common content', () => {
    it('ignores normal markdown text', () => {
      assert.ok(!matchesAny('## How to configure authentication'));
    });

    it('ignores normal code comments', () => {
      assert.ok(!matchesAny('// This function handles the API response'));
    });

    it('ignores short variable assignments', () => {
      assert.ok(!matchesAny('const token = "abc"'));
    });

    it('ignores git URLs', () => {
      assert.ok(!matchesAny('git clone https://github.com/user/repo.git'));
    });
  });
});

describe('SECRET_SCAN_SKIP', () => {
  it('is a Set', () => {
    assert.ok(SECRET_SCAN_SKIP instanceof Set);
  });

  it('skips the settings-audit script', () => {
    assert.ok(SECRET_SCAN_SKIP.has('crons/settings-audit.js'));
  });

  it('skips the patterns module itself', () => {
    assert.ok(SECRET_SCAN_SKIP.has('crons/secret-patterns.js'));
  });

  it('skips the patterns test file', () => {
    assert.ok(SECRET_SCAN_SKIP.has('crons/secret-patterns.test.js'));
  });

  it('skips the pre-commit scanner', () => {
    assert.ok(SECRET_SCAN_SKIP.has('crons/pre-commit-secrets.js'));
  });

  it('skips the pre-commit scanner test file', () => {
    assert.ok(SECRET_SCAN_SKIP.has('crons/pre-commit-secrets.test.js'));
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `node --test crons/secret-patterns.test.js`
Expected: FAIL — `Cannot find module './secret-patterns'`

**Step 3: Create the shared patterns module**

Create `crons/secret-patterns.js`:

```js
// Secret detection patterns — shared between settings-audit.js and pre-commit hook.
// When adding patterns, also add test cases in secret-patterns.test.js.

const SECRET_PATTERNS = [
  { regex: /sk-ant-[a-zA-Z0-9_-]{20,}/, desc: 'Anthropic API key (sk-ant-)' },
  { regex: /AKIA[0-9A-Z]{16}/, desc: 'AWS access key (AKIA...)' },
  { regex: /gh[ps]_[a-zA-Z0-9]{36,}/, desc: 'GitHub token' },
  { regex: /glpat-[a-zA-Z0-9_-]{20,}/, desc: 'GitLab token' },
  { regex: /xox[bprs]-[a-zA-Z0-9-]{10,}/, desc: 'Slack token' },
  { regex: /-----BEGIN (?:RSA |DSA |EC |OPENSSH )?PRIVATE KEY-----/, desc: 'Private key' },
  { regex: /Bearer\s+[a-zA-Z0-9._-]{20,}/, desc: 'Bearer token' },
  {
    regex: /(?:api[_-]?key|apiKey|API_KEY|token|secret|password|credential|auth[_-]?token|access[_-]?token)["\s]*[:=]\s*["'][a-zA-Z0-9+\/=_-]{20,}["']/i,
    desc: 'Secret in key-value assignment'
  },
  {
    regex: /(?:SECRET|PRIVATE_KEY|ENCRYPTION_KEY)["\s]*[:=]\s*["'][a-fA-F0-9]{32,}["']/,
    desc: 'Hex secret in key-value assignment'
  },
];

// Files to skip during scanning (contain the regex patterns themselves, causing false positives)
const SECRET_SCAN_SKIP = new Set([
  'crons/settings-audit.js',
  'crons/secret-patterns.js',
  'crons/secret-patterns.test.js',
  'crons/pre-commit-secrets.js',
  'crons/pre-commit-secrets.test.js',
]);

module.exports = { SECRET_PATTERNS, SECRET_SCAN_SKIP };
```

**Step 4: Run tests to verify they pass**

Run: `node --test crons/secret-patterns.test.js`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add crons/secret-patterns.js crons/secret-patterns.test.js
git commit -m "feat: extract secret patterns to shared module with tests"
```

---

### Task 2: Refactor settings-audit.js to import shared module

**Files:**
- Modify: `crons/settings-audit.js`

> **Behavior change:** After this refactor, the cron audit's `SECRET_SCAN_SKIP` expands from 1 entry (`settings-audit.js`) to 5 entries (adding the four new pattern/scanner files). This is intentional — these files contain the detection regexes themselves and would false-positive. The pre-commit hook provides its own scanning coverage for staged changes, so the cron audit skipping these files does not create a security gap.

**Step 1: Replace inline patterns with require**

In `crons/settings-audit.js`, replace the entire `SECRET_PATTERNS` array (lines 91-108) and `SECRET_SCAN_SKIP` set (lines 110-113) with:

```js
// Secret patterns (shared with pre-commit hook)
const { SECRET_PATTERNS, SECRET_SCAN_SKIP } = require('./secret-patterns');
```

Remove these lines (91-113):
- The `// Secret patterns for scanning git-tracked files` comment
- The full `const SECRET_PATTERNS = [...]` array
- The `// Files to skip during secret scanning...` comment
- The full `const SECRET_SCAN_SKIP = new Set([...])` declaration

**Step 2: Run the audit to verify identical behavior**

Run: `node crons/settings-audit.js && cat last-settings-audit.details`
Expected: Same output as before — one MEDIUM finding about `auto-approve-safe-bash-paths.js`. No regressions.

**Step 3: Run the shared module tests too**

Run: `node --test crons/secret-patterns.test.js`
Expected: All PASS

**Step 4: Commit**

```bash
git add crons/settings-audit.js
git commit -m "refactor: settings-audit imports patterns from shared module"
```

---

### Task 3: Fix stale knownHookCommands and add missing secret patterns

> **Dependency:** Requires Tasks 1 and 2 complete (shared module must exist and be imported).

**Files:**
- Modify: `crons/settings-audit.js` (lines 61-67, `knownHookCommands`)
- Modify: `crons/secret-patterns.js` (add patterns)
- Modify: `crons/secret-patterns.test.js` (add tests for new patterns)

**Step 1: Add missing hook to `knownHookCommands`**

In `crons/settings-audit.js`, add to the `knownHookCommands` Set (after line 66, `usage-tracker.js`):

```js
  'node /Users/ericpage/.claude/hooks/auto-approve-safe-bash-paths.js',
```

**Step 2: Run audit to verify MEDIUM finding is gone**

Run: `node crons/settings-audit.js && cat last-settings-audit.details`
Expected: `no issues found` (the MEDIUM finding about unknown hook command should be gone)

**Step 3: Write tests for new secret patterns**

Add these test blocks to `crons/secret-patterns.test.js`, inside the `SECRET_PATTERNS` describe block:

```js
  describe('Stripe keys', () => {
    it('detects sk_live_ secret keys', () => {
      assert.ok(matchesAny('STRIPE_KEY="sk_live_abcdefghijklmnopqrstuvwx"'));
      assert.equal(firstMatch('sk_live_abcdefghijklmnopqrstuvwx'), 'Stripe live secret key');
    });

    it('detects sk_test_ secret keys', () => {
      assert.ok(matchesAny('sk_test_abcdefghijklmnopqrstuvwx'));
    });

    it('detects rk_live_ restricted keys', () => {
      assert.ok(matchesAny('rk_live_abcdefghijklmnopqrstuvwx'));
      assert.equal(firstMatch('rk_live_abcdefghijklmnopqrstuvwx'), 'Stripe restricted key');
    });
  });

  describe('Google Cloud API key', () => {
    it('detects AIza prefixed keys', () => {
      assert.ok(matchesAny('GOOGLE_API_KEY="AIzaSyA1234567890abcdefghijklmnopqrstuv"'));
    });

    it('rejects non-AIza prefixes', () => {
      assert.ok(!matchesAny('AIxx1234567890abcdefghijklmnopqrstuv'));
    });
  });

  describe('JWT token', () => {
    it('detects full JWT tokens (three segments)', () => {
      assert.ok(matchesAny('token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2V4YW1wbGUu.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV'));
    });

    it('rejects partial JWT (missing signature segment)', () => {
      assert.ok(!matchesAny('eyJhbGciOiJIUzI1'));
    });
  });
```

**Step 4: Run tests to verify new tests fail**

Run: `node --test crons/secret-patterns.test.js`
Expected: FAIL — new pattern tests fail (patterns don't exist yet)

**Step 5: Add new patterns to shared module**

In `crons/secret-patterns.js`, add these entries to the `SECRET_PATTERNS` array (before the closing `];`):

```js
  { regex: /sk_live_[a-zA-Z0-9]{24,}/, desc: 'Stripe live secret key' },
  { regex: /sk_test_[a-zA-Z0-9]{24,}/, desc: 'Stripe test secret key' },
  { regex: /rk_live_[a-zA-Z0-9]{24,}/, desc: 'Stripe restricted key' },
  { regex: /AIza[a-zA-Z0-9_-]{35}/, desc: 'Google Cloud API key' },
  { regex: /eyJhbGciOi[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}/, desc: 'JWT token' },
```

**Step 6: Run tests to verify they pass**

Run: `node --test crons/secret-patterns.test.js`
Expected: All PASS

**Step 7: Run audit to verify no new false positives**

Run: `node crons/settings-audit.js && cat last-settings-audit.details`
Expected: `no issues found`

**Step 8: Commit**

```bash
git add crons/settings-audit.js crons/secret-patterns.js crons/secret-patterns.test.js
git commit -m "feat: add Stripe/Google/JWT patterns, fix stale knownHookCommands"
```

---

### Task 4: Create pre-commit scanner script with tests

**Files:**
- Create: `crons/pre-commit-secrets.js`
- Create: `crons/pre-commit-secrets.test.js`

**Step 1: Write the test file**

Create `crons/pre-commit-secrets.test.js`:

```js
const { describe, it } = require('node:test');
const assert = require('node:assert/strict');
const mod = require('./pre-commit-secrets');

// Unit tests cover scanLines (pure function) and shouldSkipFile (pure function).
// getStagedFiles/getStagedContent/scan depend on git subprocess state and are
// verified via integration tests in Task 5 (plant secret → commit blocked).

describe('pre-commit-secrets', () => {
  describe('scanLines', () => {
    it('detects Anthropic API keys in content', () => {
      const content = 'some config\nkey = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"\nmore config';
      const findings = mod.scanLines(content, 'test-file.js');
      assert.equal(findings.length, 1);
      assert.ok(findings[0].includes('Anthropic API key'));
      assert.ok(findings[0].includes('test-file.js:2'));
    });

    it('returns empty array for clean content', () => {
      const content = 'const x = 42;\nconst y = "hello world";\n';
      const findings = mod.scanLines(content, 'clean.js');
      assert.equal(findings.length, 0);
    });

    it('detects multiple secrets in one file', () => {
      const content = 'key1 = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"\nkey2 = "AKIAIOSFODNN7EXAMPLE"\n';
      const findings = mod.scanLines(content, 'multi.js');
      assert.equal(findings.length, 2);
    });

    it('reports only one finding per line even with multiple pattern matches', () => {
      // A line that could match both Bearer and key-value patterns
      const content = 'auth_token = "Bearer-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.abc.def"\n';
      const findings = mod.scanLines(content, 'overlap.js');
      assert.ok(findings.length <= 1);
    });

    it('skips binary content (contains null bytes)', () => {
      const content = 'some\x00binary\x00content with sk-ant-api03-abcdefghijklmnopqrstuvwxyz';
      const findings = mod.scanLines(content, 'binary.bin');
      assert.equal(findings.length, 0);
    });

    it('provides redacted preview (max 12 chars + ...)', () => {
      const content = 'key = "sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890"';
      const findings = mod.scanLines(content, 'preview.js');
      assert.equal(findings.length, 1);
      // Preview should be truncated, not show the full key
      assert.ok(findings[0].includes('sk-ant-api03...'));
    });
  });

  describe('shouldSkipFile', () => {
    it('skips files in SECRET_SCAN_SKIP', () => {
      assert.ok(mod.shouldSkipFile('crons/secret-patterns.js'));
      assert.ok(mod.shouldSkipFile('crons/settings-audit.js'));
    });

    it('does not skip regular files', () => {
      assert.ok(!mod.shouldSkipFile('skills/some-skill/SKILL.md'));
      assert.ok(!mod.shouldSkipFile('settings.json'));
    });
  });
});
```

**Step 2: Run tests to verify they fail**

Run: `node --test crons/pre-commit-secrets.test.js`
Expected: FAIL — `Cannot find module './pre-commit-secrets'`

**Step 3: Create the pre-commit scanner script**

Create `crons/pre-commit-secrets.js`:

```js
#!/usr/bin/env node
// Pre-commit secret scanner for ~/.claude repo.
// Scans staged file contents for secret patterns before commit.
// Exit 0 = clean (commit proceeds), exit 1 = secrets found (commit blocked).
//
// Install: cp or symlink to ~/.claude/.git/hooks/pre-commit
// Bypass:  git commit --no-verify

const { execFileSync } = require('child_process');
const { SECRET_PATTERNS, SECRET_SCAN_SKIP } = require('./secret-patterns');

function getStagedFiles() {
  try {
    const output = execFileSync('git', ['diff', '--cached', '--name-only'], {
      encoding: 'utf8', timeout: 5000
    });
    return output.trim().split('\n').filter(Boolean);
  } catch {
    return [];
  }
}

function getStagedContent(filePath) {
  try {
    return execFileSync('git', ['show', `:${filePath}`], {
      encoding: 'utf8', timeout: 5000
    });
  } catch {
    return null;
  }
}

function shouldSkipFile(relPath) {
  return SECRET_SCAN_SKIP.has(relPath);
}

function scanLines(content, relPath) {
  const findings = [];
  if (content.includes('\0')) return findings; // skip binary

  const lines = content.split('\n');
  for (let i = 0; i < lines.length; i++) {
    for (const { regex, desc } of SECRET_PATTERNS) {
      if (regex.test(lines[i])) {
        const match = lines[i].match(regex);
        const preview = match ? match[0].substring(0, 12) + '...' : '';
        findings.push(`  ${desc} in ${relPath}:${i + 1} — "${preview}"`);
        break; // one finding per line
      }
    }
  }
  return findings;
}

function scan() {
  const findings = [];
  for (const relPath of getStagedFiles()) {
    if (shouldSkipFile(relPath)) continue;
    const content = getStagedContent(relPath);
    if (!content) continue;
    findings.push(...scanLines(content, relPath));
  }
  return findings;
}

if (require.main === module) {
  const findings = scan();
  if (findings.length > 0) {
    process.stderr.write('\nSECRET DETECTED — commit blocked\n\n');
    process.stderr.write(findings.join('\n') + '\n');
    process.stderr.write('\nIf this is a false positive, use: git commit --no-verify\n');
    process.stderr.write('Then add the pattern to SECRET_SCAN_SKIP in crons/secret-patterns.js\n\n');
    process.exit(1);
  }
}

module.exports = { scan, getStagedFiles, getStagedContent, scanLines, shouldSkipFile };
```

**Step 4: Run tests to verify they pass**

Run: `node --test crons/pre-commit-secrets.test.js`
Expected: All PASS

**Step 5: Commit**

```bash
git add crons/pre-commit-secrets.js crons/pre-commit-secrets.test.js
git commit -m "feat: add pre-commit secret scanner with tests"
```

---

### Task 5: Install git pre-commit hook and add self-healing

**Files:**
- Create: `.git/hooks/pre-commit` (untracked — lives in `.git/`, not pushed)
- Modify: `skills/.scripts/autocommit.sh`

**Step 1: Create the git hook shim**

Create `~/.claude/.git/hooks/pre-commit`:

```bash
#!/bin/bash
exec node "$HOME/.claude/crons/pre-commit-secrets.js"
```

Make it executable:

Run: `chmod +x ~/.claude/.git/hooks/pre-commit`

**Step 2: Test — plant a secret, verify commit is blocked**

Plant a fake secret in a tracked file:

Run: `echo '<!-- sk-ant-api03-FAKEKEYFAKEKEYFAKEKEY -->' >> README.md`

Stage it:

Run: `git add README.md`

Attempt to commit:

Run: `git commit -m "test: should be blocked"`
Expected: Non-zero exit. stderr contains `SECRET DETECTED — commit blocked` and mentions `README.md`

**Step 3: Test — remove secret, verify commit succeeds**

Remove the planted secret:

Run: `git checkout -- README.md`

Verify clean state:

Run: `git diff --cached --quiet && echo "staging area clean"`
Expected: `staging area clean`

**Step 4: Add self-healing hook installation and commit failure logging to autocommit.sh**

In `skills/.scripts/autocommit.sh`, add after line 6 (`cd "$CLAUDE_DIR" || exit 1`) and before line 8 (`# Sync settings between profiles before committing`):

```bash
# Ensure pre-commit hook is installed (self-healing — .git/hooks/ is untracked)
HOOK_PATH="$CLAUDE_DIR/.git/hooks/pre-commit"
if [ ! -x "$HOOK_PATH" ]; then
    mkdir -p "$CLAUDE_DIR/.git/hooks"
    printf '#!/bin/bash\nexec node "$HOME/.claude/crons/pre-commit-secrets.js"\n' > "$HOOK_PATH"
    chmod +x "$HOOK_PATH"
fi
```

Also, replace the `git commit` call (line 29) to log failures. Change:

```bash
git commit -m "Auto-snapshot: $TIMESTAMP

Changed:
$CHANGED"
```

To:

```bash
if ! git commit -m "Auto-snapshot: $TIMESTAMP

Changed:
$CHANGED"; then
    echo "[$TIMESTAMP] COMMIT BLOCKED (likely secret detected). Run: git diff --cached --name-only" >> "$CLAUDE_DIR/skills/.scripts/autocommit.log"
    exit 1
fi
```

> **Note:** `crons/` is intentionally NOT in autocommit.sh's staging list. The new `crons/` files require manual commits, which is appropriate for security infrastructure (you want deliberate commits, not auto-snapshots).

**Step 5: Test self-healing — remove hook, verify autocommit reinstalls it**

Remove the hook:

Run: `rm ~/.claude/.git/hooks/pre-commit`

Run just the self-healing portion (first 15 lines of autocommit.sh):

Run: `bash -c 'CLAUDE_DIR="$HOME/.claude"; HOOK_PATH="$CLAUDE_DIR/.git/hooks/pre-commit"; if [ ! -x "$HOOK_PATH" ]; then mkdir -p "$CLAUDE_DIR/.git/hooks"; printf "#!/bin/bash\nexec node \"\$HOME/.claude/crons/pre-commit-secrets.js\"\n" > "$HOOK_PATH"; chmod +x "$HOOK_PATH"; fi'`

Verify hook was reinstalled:

Run: `test -x ~/.claude/.git/hooks/pre-commit && echo "hook reinstalled" || echo "MISSING"`
Expected: `hook reinstalled`

Run: `cat ~/.claude/.git/hooks/pre-commit`
Expected: The two-line bash script calling `pre-commit-secrets.js`

**Step 6: Commit**

```bash
git add skills/.scripts/autocommit.sh
git commit -m "feat: install pre-commit hook with self-healing via autocommit"
```

---

### Task 6: End-to-end verification

**Step 1: Run all tests**

Run: `node --test crons/secret-patterns.test.js crons/pre-commit-secrets.test.js`
Expected: All PASS, zero failures

**Step 2: Run settings audit**

Run: `node crons/settings-audit.js && cat last-settings-audit.details`
Expected: `no issues found` (all patterns work, no false positives, knownHookCommands is complete)

**Step 3: Verify pre-commit hook end-to-end**

Plant a secret, attempt commit, verify blocked:

Run: `echo '<!-- sk-ant-api03-FAKEKEYFAKEKEYFAKEKEY -->' >> README.md && git add README.md && git commit -m "e2e test" 2>&1; echo "EXIT: $?"`
Expected: Output contains `SECRET DETECTED`, exit code is non-zero

Clean up:

Run: `git checkout -- README.md`

**Step 4: Push all commits**

Run: `git push origin main`

---

## Manual Steps (Post-Automation)

- [ ] Verify the next autocommit cycle (within 10 minutes) doesn't produce unexpected behavior — check `~/.claude/skills/.scripts/autocommit.log` after the next auto-snapshot
- [ ] Run `node ~/.claude/crons/settings-audit.js` one more time after the autocommit cycle to confirm the audit still reports clean

---

## Decision Log

### Summary
| # | Decision | Choice Made | Alternatives Considered |
|---|----------|------------|------------------------|
| 1 | Pre-commit hook vs. autocommit inline check | Git pre-commit hook | Inline check in autocommit.sh |
| 2 | Hook blocks commit vs. warns only | Block (exit 1) | Warn and continue |
| 3 | Shared module vs. duplicate patterns | Shared `secret-patterns.js` module | Inline patterns in both files |
| 4 | Test runner | Node built-in `node:test` | jest, mocha, tap |
| 5 | JWT pattern scope | Full 3-segment JWT match | Header-only match, no JWT detection |
| 6 | Self-healing hook installation | Via autocommit.sh check | Manual install only, setup script |

### Appendix: Decision Details

#### Decision 1: Git pre-commit hook vs. autocommit inline check
**Chose:** Git pre-commit hook (`.git/hooks/pre-commit`)
**Why:** A git pre-commit hook catches ALL commits — both automated (autocommit.sh) and manual. An inline check in autocommit.sh would only protect the automated path, leaving manual `git commit` unguarded. The hook is the standard git mechanism for pre-commit validation and works regardless of how the commit is triggered.
**Alternatives rejected:**
- Inline check in autocommit.sh: Only covers one commit path. Manual commits bypass it entirely.

#### Decision 2: Block vs. warn
**Chose:** Block the commit (exit 1)
**Why:** The entire purpose of this feature is to prevent secret exposure. The autocommit pushes every 10 minutes — a "warn and continue" approach means the secret goes public within 10 minutes, defeating the purpose. A blocked commit is recoverable (`git commit --no-verify`), but a leaked secret is an incident. The "permissive on failure" convention in CLAUDE.md applies to Claude Code hooks (LLM shouldn't be disrupted), not git hooks (protecting secrets).
**Observability note:** When the hook blocks an autocommit, the commit exits non-zero silently (no user notification). Task 5 mitigates this by adding failure logging to `autocommit.log` — check for `COMMIT BLOCKED` entries in `~/.claude/skills/.scripts/autocommit.log` if auto-snapshots stop appearing.
**Alternatives rejected:**
- Warn only: Defeats the purpose — secrets still get pushed. The 10-minute window is too short for a human to react to a warning.

#### Decision 3: Shared module
**Chose:** Extract patterns to `secret-patterns.js`, imported by both `settings-audit.js` and `pre-commit-secrets.js`
**Why:** DRY — a single source of truth for patterns means adding a new pattern updates both the cron audit and the pre-commit hook. The patterns array is the core security logic; duplicating it creates divergence risk.
**Alternatives rejected:**
- Duplicate inline: Two copies to maintain, inevitable drift, a new pattern added to one but not the other means a gap.

#### Decision 4: Test runner
**Chose:** Node built-in `node:test` (available since Node 18, current env is Node 22)
**Why:** Zero dependencies. The `~/.claude/` repo has no `package.json` and no test infrastructure. Adding jest or mocha would require npm init, dependency management, and ongoing maintenance — overkill for a personal config repo with two test files. `node:test` provides describe/it/assert with no setup.
**Alternatives rejected:**
- jest/mocha: Requires npm init, package.json, node_modules — too heavy for this repo.

#### Decision 5: JWT pattern scope
**Chose:** Full 3-segment JWT match (`header.payload.signature`, each 20+ chars)
**Why:** Requiring all three base64url segments dramatically reduces false positives from documentation examples that show partial JWTs or just a header. Supabase anon/service-role keys are full JWTs, so this catches the primary use case (Supabase is actively used per enabled plugins).
**Alternatives rejected:**
- Header-only match (`eyJhbGciOi` prefix): Too many false positives in markdown skill files that reference JWT format.
- No JWT detection: Misses Supabase keys entirely, which was the specific gap the QA advisor flagged.

#### Decision 6: Self-healing hook installation
**Chose:** Autocommit.sh checks for hook and installs if missing on every run
**Why:** The git hook lives in `.git/hooks/` which is untracked — it can be lost by git clone, git init, or accidental deletion. Since autocommit.sh runs every 10 minutes, adding a 3-line check ensures the hook is always present before any automated commit. The check is cheap (one `test -x` call) and the install is idempotent.
**Alternatives rejected:**
- Manual install only: Hook silently disappears, no protection until someone notices.
- Separate setup script: Extra file to remember to run; the autocommit path is the natural enforcement point since it's the primary committer.
