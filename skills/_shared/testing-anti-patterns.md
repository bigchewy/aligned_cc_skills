# Testing Anti-Patterns

<!-- Forked from SuperPowers v4.0.3 (2025-01-22) -->
<!-- Custom modifications: Added Anti-Pattern 6 (Mocking Away Error Paths), Anti-Pattern 7 (Testing Language Features), Anti-Pattern 8 (Reimplementing Logic in Mocks), Anti-Pattern 9 (Mocking at the Wrong Boundary) -->

**Load this reference when:** writing or changing tests, adding mocks, or tempted to add test-only methods to production code.

## Overview

Tests must verify real behavior, not mock behavior. Mocks are a means to isolate, not the thing being tested.

**Core principle:** Test what the code does, not what the mocks do.

**Following strict TDD prevents these anti-patterns.**

## The Iron Laws

Core rules that cover the most damaging anti-patterns. Each anti-pattern below has its own gate function with full detail.

```
1. NEVER test mock behavior (AP1)
2. NEVER add test-only methods to production classes (AP2)
3. NEVER mock without understanding dependencies (AP3)
4. NEVER mock only success paths - test error paths too (AP6)
5. NEVER reimplement production logic in a mock (AP8)
6. NEVER skip glue code by mocking too high in the chain (AP9)
```

## Anti-Pattern 1: Testing Mock Behavior

**The violation:**
```typescript
// ❌ BAD: Testing that the mock exists
test('renders sidebar', () => {
  render(<Page />);
  expect(screen.getByTestId('sidebar-mock')).toBeInTheDocument();
});
```

**Why this is wrong:**
- You're verifying the mock works, not that the component works
- Test passes when mock is present, fails when it's not
- Tells you nothing about real behavior

**your human partner's correction:** "Are we testing the behavior of a mock?"

**The fix:**
```typescript
// ✅ GOOD: Test real component or don't mock it
test('renders sidebar', () => {
  render(<Page />);  // Don't mock sidebar
  expect(screen.getByRole('navigation')).toBeInTheDocument();
});

// OR if sidebar must be mocked for isolation:
// Don't assert on the mock - test Page's behavior with sidebar present
```

### Gate Function

```
BEFORE asserting on any mock element:
  Ask: "Am I testing real component behavior or just mock existence?"

  IF testing mock existence:
    STOP - Delete the assertion or unmock the component

  Test real behavior instead
```

## Anti-Pattern 2: Test-Only Methods in Production

**The violation:**
```typescript
// ❌ BAD: destroy() only used in tests
class Session {
  async destroy() {  // Looks like production API!
    await this._workspaceManager?.destroyWorkspace(this.id);
    // ... cleanup
  }
}

// In tests
afterEach(() => session.destroy());
```

**Why this is wrong:**
- Production class polluted with test-only code
- Dangerous if accidentally called in production
- Violates YAGNI and separation of concerns
- Confuses object lifecycle with entity lifecycle

**The fix:**
```typescript
// ✅ GOOD: Test utilities handle test cleanup
// Session has no destroy() - it's stateless in production

// In test-utils/
export async function cleanupSession(session: Session) {
  const workspace = session.getWorkspaceInfo();
  if (workspace) {
    await workspaceManager.destroyWorkspace(workspace.id);
  }
}

// In tests
afterEach(() => cleanupSession(session));
```

### Gate Function

```
BEFORE adding any method to production class:
  Ask: "Is this only used by tests?"

  IF yes:
    STOP - Don't add it
    Put it in test utilities instead

  Ask: "Does this class own this resource's lifecycle?"

  IF no:
    STOP - Wrong class for this method
```

## Anti-Pattern 3: Mocking Without Understanding

**The violation:**
```typescript
// ❌ BAD: Mock breaks test logic
test('detects duplicate server', () => {
  // Mock prevents config write that test depends on!
  vi.mock('ToolCatalog', () => ({
    discoverAndCacheTools: vi.fn().mockResolvedValue(undefined)
  }));

  await addServer(config);
  await addServer(config);  // Should throw - but won't!
});
```

**Why this is wrong:**
- Mocked method had side effect test depended on (writing config)
- Over-mocking to "be safe" breaks actual behavior
- Test passes for wrong reason or fails mysteriously

**The fix:**
```typescript
// ✅ GOOD: Mock at correct level
test('detects duplicate server', () => {
  // Mock the slow part, preserve behavior test needs
  vi.mock('MCPServerManager'); // Just mock slow server startup

  await addServer(config);  // Config written
  await addServer(config);  // Duplicate detected ✓
});
```

### Gate Function

```
BEFORE mocking any method:
  STOP - Don't mock yet

  1. Ask: "What side effects does the real method have?"
  2. Ask: "Does this test depend on any of those side effects?"
  3. Ask: "Do I fully understand what this test needs?"

  IF depends on side effects:
    Mock at lower level (the actual slow/external operation)
    OR use test doubles that preserve necessary behavior
    NOT the high-level method the test depends on

  IF unsure what test depends on:
    Run test with real implementation FIRST
    Observe what actually needs to happen
    THEN add minimal mocking at the right level

  Red flags:
    - "I'll mock this to be safe"
    - "This might be slow, better mock it"
    - Mocking without understanding the dependency chain

  See also: Anti-Pattern 9 (Mocking at the Wrong Boundary) for guidance
  on WHERE to place the mock once you've decided WHAT to mock.
```

## Anti-Pattern 4: Incomplete Mocks

**The violation:**
```typescript
// ❌ BAD: Partial mock - only fields you think you need
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' }
  // Missing: metadata that downstream code uses
};

// Later: breaks when code accesses response.metadata.requestId
```

**Why this is wrong:**
- **Partial mocks hide structural assumptions** - You only mocked fields you know about
- **Downstream code may depend on fields you didn't include** - Silent failures
- **Tests pass but integration fails** - Mock incomplete, real API complete
- **False confidence** - Test proves nothing about real behavior

**The Iron Rule:** Mock the COMPLETE data structure as it exists in reality, not just fields your immediate test uses.

**The fix:**
```typescript
// ✅ GOOD: Mirror real API completeness
const mockResponse = {
  status: 'success',
  data: { userId: '123', name: 'Alice' },
  metadata: { requestId: 'req-789', timestamp: 1234567890 }
  // All fields real API returns
};
```

### Gate Function

```
BEFORE creating mock responses:
  Check: "What fields does the real API response contain?"

  Actions:
    1. Examine actual API response from docs/examples
    2. Include ALL fields system might consume downstream
    3. Verify mock matches real response schema completely

  Critical:
    If you're creating a mock, you must understand the ENTIRE structure
    Partial mocks fail silently when code depends on omitted fields

  If uncertain: Include all documented fields
```

## Anti-Pattern 5: Integration Tests as Afterthought

**The violation:**
```
✅ Implementation complete
❌ No tests written
"Ready for testing"
```

**Why this is wrong:**
- Testing is part of implementation, not optional follow-up
- TDD would have caught this
- Can't claim complete without tests

**The fix:**
```
TDD cycle:
1. Write failing test
2. Implement to pass
3. Refactor
4. THEN claim complete
```

## Anti-Pattern 6: Mocking Away Error Paths

**CRITICAL: This is the most commonly missed anti-pattern.**

**The violation:**
```typescript
// ❌ BAD: Mock only tests success path
function createMockRequest(data: FormData) {
  return {
    headers: { get: () => 'multipart/form-data' },
    formData: jest.fn().mockResolvedValue(data),  // Always succeeds!
  } as unknown as Request
}

test('processes uploaded file', async () => {
  const req = createMockRequest(formData)
  const response = await POST(req)
  expect(response.status).toBe(200)
})
// MISSING: What if formData() throws?
```

**Why this is wrong:**
- **Production `req.formData()` can throw** - malformed body, wrong content-type, etc.
- **Your error handling code is never exercised** - bugs hide until production
- **Tests pass, production fails** - the exact scenario that prompted this anti-pattern
- **False confidence** - 100% test coverage means nothing if error paths aren't tested

**The Iron Rule:** Every mock that resolves must also have a test where it rejects — **where the function handles the error** (see Anti-Pattern 7).

**The fix:**
```typescript
// ✅ GOOD: Test BOTH success AND error paths

// Success path
test('processes uploaded file', async () => {
  const req = createMockRequest(formData)
  const response = await POST(req)
  expect(response.status).toBe(200)
})

// Error path - REQUIRED
test('returns 400 when formData() throws', async () => {
  const req = {
    headers: { get: () => 'multipart/form-data' },
    formData: jest.fn().mockRejectedValue(new Error('Malformed multipart body')),
  } as unknown as Request

  const response = await POST(req)

  expect(response.status).toBe(400)
  const body = await response.json()
  expect(body.error).toBeDefined()
})
```

### Gate Function

```
BEFORE completing tests that use mocks:
  For EACH mock that uses mockResolvedValue or mockReturnValue:
    Ask: "Can this operation throw/fail in production?"

    IF yes (almost always):
      REQUIRED: Write a test with mockRejectedValue
      REQUIRED: Verify error handling returns appropriate response

  Common operations that ALWAYS need error path tests:
    - req.formData()     -> malformed body
    - req.json()         -> invalid JSON
    - file.arrayBuffer() -> read failure
    - fetch()            -> network error
    - db.query()         -> connection failure
    - fs.readFile()      -> file not found
    - external APIs      -> timeout, 500, rate limit

  The Test Pattern:
    1. Mock resolves -> test success behavior
    2. Mock rejects  -> test error handling
    Both are REQUIRED. One without the other is incomplete.
```

## Anti-Pattern 7: Testing Language Features

**The violation:**
```typescript
// ❌ BAD: Testing that async/await propagates exceptions
it('saveIdea propagates Redis error', async () => {
  mockRedis.hset.mockRejectedValueOnce(new Error('Timeout'));
  await expect(saveIdea(testIdea)).rejects.toThrow('Timeout');
});
```

**Why this is wrong:**
- `saveIdea` has no try/catch. It's a thin wrapper around `redis.hset()`
- This test verifies that JavaScript's `async/await` propagates exceptions — a language guarantee
- The test cannot fail unless JavaScript itself is broken
- These accumulate to hundreds of tests that catch zero bugs

**Common forms:**
- **Error propagation without handling:** `mockRejectedValue` on a function with no try/catch
- **Type shape assertion:** `const x: Type = { a: 1 }; expect(x.a).toBe(1)` — testing that assignment works
- **Null pass-through:** Mock returns null, function returns null, no conditional logic

**The Iron Rule:** Only test error paths where your code HANDLES the error (try/catch, fallback, transformation, retry). If the function just passes through, the test is redundant.

**When error path tests ARE needed:**
```typescript
// ✅ GOOD: Function actually handles the error
async function getIdeaWithFallback(id: string) {
  try {
    return await getIdea(id);
  } catch {
    return DEFAULT_IDEA; // Fallback logic — worth testing
  }
}

it('returns default idea when db fails', async () => {
  mockRedis.hget.mockRejectedValueOnce(new Error('Timeout'));
  const result = await getIdeaWithFallback('id');
  expect(result).toEqual(DEFAULT_IDEA); // Tests real behavior
});
```

### Gate Function

```
BEFORE writing an error path test:
  Ask: "Does this function HANDLE the error?"

  Check for:
    - try/catch block
    - .catch() handler
    - Conditional logic on error type
    - Fallback/default return value
    - Error transformation (wrapping, enriching)
    - Retry logic

  IF none of these exist:
    STOP — Don't write the test. You'd be testing async/await.

  IF error handling exists:
    REQUIRED — Write the test. Verify the handling behavior.
```

**The distinction matters:** Anti-Pattern 6 says "every mock that resolves must have a test where it rejects." Anti-Pattern 7 clarifies: that rule applies only to code that handles errors. For pure pass-through functions, the caller's error test already covers the path.

## Anti-Pattern 8: Reimplementing Logic in Mocks

**The violation:**
```typescript
// Production code (has a bug: no try/catch around JSON.parse)
function parseValue(value: unknown): unknown {
  if (typeof value === 'string') return JSON.parse(value);
  return value;
}

export function getContentDraft(id: string): ContentDraft {
  const raw = await redis.get(`draft:${id}`);
  return parseValue(raw);
}

// ❌ BAD: Consumer test reimplements parseValue logic in the mock
vi.mock('@/lib/data/db', () => ({
  getContentDraft: vi.fn().mockImplementation(async (id: string) => {
    const raw = '{"title":"Hello","body":"Content"}';
    return typeof raw === 'string' ? JSON.parse(raw) : raw;  // <-- bug copied!
  }),
}));

test('pipeline processes draft', async () => {
  const result = await runPipeline('draft-123');
  expect(result.status).toBe('complete');
  // Passes! The mock reimplements parseValue's logic (including its bug).
  // Feed it only valid JSON and you'll never see the missing try/catch.
});
```

**Why this is wrong:**
- **The mock IS the bug.** If production code has a defect (missing try/catch, wrong edge case handling), the mock faithfully reproduces that defect
- **Tests can never fail for the right reason.** The mock and the production code break in identical ways — the test is structurally incapable of catching the bug
- **Feed it only happy-path data and it's invisible.** The mock above only receives `JSON.stringify`'d objects, never plain strings — so the missing try/catch never fires
- **Subtler than AP1.** This isn't testing a mock directly (AP1) — it's testing real consumer logic. But the mock's reimplemented logic smuggles the dependency's bug past the test boundary

**Real-world example:** `parseValue` called `JSON.parse()` on strings without try/catch. When @upstash/redis auto-deserialized a stored markdown draft (starting with `---` YAML frontmatter), `parseValue` received plain markdown and threw `"No number after minus sign in JSON."` Three layers of tests all passed — unit tests reimplemented the bug in the mock, consumer tests mocked above `parseValue` entirely, and no integration tests existed. The bug shipped to production.

**The Iron Rule:** Never reimplement production logic in a mock. Either import and use the real function, or use `vi.fn()` with explicit return values.

**The fix:**
```typescript
// ✅ GOOD Option A: Don't mock the dependency — test it directly
import { parseValue } from '@/lib/data/db';

test('parses JSON string', () => {
  expect(parseValue('{"title":"Hello"}')).toEqual({ title: 'Hello' });
});

test('handles non-JSON string gracefully', () => {
  // This test would have CAUGHT the missing try/catch
  expect(() => parseValue('---\ntitle: Hello\n---')).not.toThrow();
});

// ✅ GOOD Option B: Explicit return values in mock (no logic)
vi.mock('@/lib/data/db', () => ({
  getContentDraft: vi.fn().mockResolvedValue({ title: 'Hello', body: 'Content' }),
  // No logic — just a pre-computed return value.
  // Consumer tests verify pipeline behavior given this input.
  // Separate unit tests verify parseValue itself with real edge cases.
}));
```

### Gate Function

```
BEFORE creating any mock implementation:
  Ask: "Does this mock contain logic (if/else, try/catch, .parse(), etc.)?"

  IF yes:
    STOP — You are reimplementing production code.

    Options:
    1. Import and test the REAL function directly (preferred)
    2. Use vi.fn() with explicit return values (no logic)
    3. Don't mock at all — test the real dependency

  Red flags — mock contains:
    - JSON.parse, JSON.stringify
    - Conditional logic (if/else, ternary, switch)
    - String manipulation or parsing
    - Math or computation
    - Any transformation of input to output
    - Identity functions: (x) => x, (...args) => realFn(...args)
    - Delegation to real functions wrapped in vi.fn()

  These mean the mock IS the code. Test the real thing instead.
```

## Anti-Pattern 9: Mocking at the Wrong Boundary

**The violation:**
```typescript
// Production layers:
//   Redis client → getJson() → parseValue() → getContentDraft()
//                  ^^^^^^^^^^^^^^^^^^^^^^^^
//                  Glue code with real bugs

// ❌ BAD: Mock at intermediate layer, skipping glue code
vi.mock('@/lib/data/db', () => ({
  getContentDraft: vi.fn().mockResolvedValue({
    title: 'My Draft',
    body: 'Content here',
  }),
}));

test('pipeline processes draft', async () => {
  const result = await runPipeline('draft-123');
  expect(result.status).toBe('complete');
  // Passes! But getJson → parseValue chain is never exercised.
  // Bugs in that glue code (like missing try/catch) are invisible.
});
```

**Why this is wrong:**
- **Glue code is where bugs live.** The logic between I/O and business code — parsing, deserializing, transforming — is where most integration bugs occur
- **Mocking the intermediate function skips the glue entirely.** `getContentDraft` calls `getJson` which calls `parseValue` — none of these run when `getContentDraft` is mocked
- **Three layers of tests, zero caught the bug.** Unit tests mocked `parseValue` (Anti-Pattern 8). Consumer tests mocked `getContentDraft`. Integration tests didn't exist. The parsing bug sailed through to production
- **Library behavior surprises go undetected.** @upstash/redis auto-deserializes JSON on read — no test simulated this because every mock returned raw `JSON.stringify`'d values

**The Iron Rule:** For thin wrapper chains (client → helper → consumer), mock at the I/O boundary (the client/SDK), not at intermediate layers. For architectures with designed abstraction boundaries (repository interfaces, ports, service contracts), mock at the designed boundary — that's what it's for. The key question is: does glue code exist between your mock and your test subject? If yes, you're skipping the code most likely to have bugs.

**Relationship to Anti-Pattern 3:** AP3 addresses *understanding* what you mock. AP9 addresses *where* you place the mock boundary. AP3's fix — "mock the slow part, preserve behavior test needs" — is compatible: mock at the lowest layer that preserves the behavior your test depends on. For thin chains, that's the I/O client. For thick architectures with designed interfaces, that may be a repository or service boundary. See AP3's gate function for the complementary checklist.

**The fix:**
```typescript
// ✅ GOOD: Mock at the I/O boundary (Redis client)
vi.mock('@upstash/redis', () => ({
  Redis: vi.fn().mockImplementation(() => ({
    // Mock the client, not the wrapper functions
    get: vi.fn(),
    hget: vi.fn(),
    hset: vi.fn(),
  })),
}));

const mockRedis = new Redis();

test('handles auto-deserialized object from Redis', async () => {
  // Redis auto-deserializes JSON, returning an object not a string
  (mockRedis.get as Mock).mockResolvedValue({ title: 'My Draft', body: 'Content' });

  const result = await getContentDraft('draft-123');
  expect(result).toEqual({ title: 'My Draft', body: 'Content' });
});

test('handles plain string from Redis', async () => {
  // Redis returns non-JSON strings as-is
  (mockRedis.get as Mock).mockResolvedValue('---\ntitle: Draft\n---\nMarkdown body');

  // This test would have CAUGHT the parseValue bug
  const result = await getContentDraft('draft-123');
  expect(result).toBeDefined(); // Should handle gracefully, not throw
});
```

### Gate Function

```
BEFORE choosing what to mock:
  Draw the dependency chain from I/O to business logic:
    Client SDK → wrapper/helper → intermediate function → consumer

  Ask: "Where is the I/O boundary?"
    - Database client (Redis, Prisma, Knex)
    - HTTP client (fetch, axios)
    - File system (fs)
    - External SDK (@upstash/redis, @aws-sdk/*)

  Mock THERE. Not higher.

  Ask: "What glue code exists between I/O and my test subject?"
    - Parsing (JSON.parse, YAML parse)
    - Deserialization (client auto-deserialize)
    - Transformation (mapping, filtering)
    - Error wrapping (try/catch → custom errors)

  IF glue code exists between mock and test subject:
    STOP — You're skipping the code most likely to have bugs.
    Move the mock boundary down to the I/O layer.

  Ask: "Does the library do anything surprising?"
    - Auto-deserialization (@upstash/redis returns objects, not strings)
    - Connection pooling (Prisma)
    - Request transformation (axios interceptors)

  IF yes:
    Your per-test return values must reflect what the library actually returns.
    Don't build simulation logic into the mock (that's Anti-Pattern 8).
    Instead, use explicit mockResolvedValue calls that return what the real
    library would — e.g., an already-deserialized object, not a JSON string.
    Test with BOTH the library's auto-behavior AND edge-case values.

  IF the library's behavior is complex enough that per-test return values
  aren't sufficient, consider whether the right mock boundary is actually
  a thin wrapper with a stable interface, not the raw client.
```

## When Mocks Become Too Complex

**Warning signs:**
- Mock setup longer than test logic
- Mocking everything to make test pass
- Mocks missing methods real components have
- Test breaks when mock changes

**your human partner's question:** "Do we need to be using a mock here?"

**Consider:** Integration tests with real components often simpler than complex mocks

## TDD Prevents These Anti-Patterns

**Why TDD helps:**
1. **Write test first** → Forces you to think about what you're actually testing
2. **Watch it fail** → Confirms test tests real behavior, not mocks
3. **Minimal implementation** → No test-only methods creep in
4. **Real dependencies** → You see what the test actually needs before mocking

**If you're testing mock behavior, you violated TDD** - you added mocks without watching test fail against real code first.

## Quick Reference

| Anti-Pattern | Fix |
|--------------|-----|
| Assert on mock elements | Test real component or unmock it |
| Test-only methods in production | Move to test utilities |
| Mock without understanding | Understand dependencies first, mock minimally |
| Incomplete mocks | Mirror real API completely |
| Tests as afterthought | TDD - tests first |
| Over-complex mocks | Consider integration tests |
| **Mock only success paths** | **Test both resolve AND reject cases** |
| **Mock error path for pass-through** | **Only test error handling where handling exists** |
| **Reimplement logic in mocks** | **Import real function or use explicit return values** |
| **Mock intermediate layers (thin chains)** | **Mock at I/O boundary; for designed abstractions, mock at the interface** |

## Red Flags

- Assertion checks for `*-mock` test IDs
- Methods only called in test files
- Mock setup is >50% of test
- Test fails when you remove mock
- Can't explain why mock is needed
- Mocking "just to be safe"
- **Every mockResolvedValue without a corresponding mockRejectedValue test**
- **No tests for what happens when external operations fail**
- **mockRejectedValue tests on functions with no try/catch**
- **Mock implementation contains if/else, JSON.parse, or any production logic**
- **Mocking wrapper functions when glue code between wrapper and client has real logic**

## The Bottom Line

**Mocks are tools to isolate, not things to test.**

**Every mock that can fail in production must have an error path test.**

If TDD reveals you're testing mock behavior, you've gone wrong.
If your mocks only test success, you've gone wrong.
If your mock contains the same logic as production code, you've gone wrong.
If your mock skips the glue code between I/O and business logic, you've gone wrong.

Fix: Test real behavior AND test error handling AND mock at the right boundary.
