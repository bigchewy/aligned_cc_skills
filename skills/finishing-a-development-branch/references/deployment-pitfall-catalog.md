# Vercel Deployment Pitfall Catalog

Reference document for the Vercel deployment audit step — **scoped to runtime bugs in bundled code** (e.g., `__dirname`/`__filename` resolution, `process.env[...]` bracket access, module-level mutable state). Contains detection patterns, explanations, false positive guidance, and recommended fixes for each audit category.

> For **manual-deploy artifacts** (DB migrations, env-var additions, cron/webhook setup, DNS — anything that requires a non-automatable production step), see the separate catalog at `skills/_shared/manual-deploy-artifact-catalog.md`. That catalog is a superset of this one in shape (severity-section organization, prose per entry) and adds a fenced machine-matchable block per entry for programmatic detection. Different concern; do not conflate.

## Contents

- [How to Use This Catalog](#how-to-use-this-catalog)
- [CRITICAL — Silent Production Failures](#critical--silent-production-failures)
- [HIGH — Data/Performance Issues](#high--dataperformance-issues)
- [MEDIUM — Potential Issues Under Load](#medium--potential-issues-under-load)
- [LOW — Best Practice Recommendations](#low--best-practice-recommendations)
- [Maintenance](#maintenance)

---

## How to Use This Catalog

For each category:
1. Run the **Detection** search patterns against `src/` (excluding `__tests__/` directories unless noted)
2. For each match, read the surrounding code and apply **False Positive Rules** to filter
3. Report true positives with the **Severity**, file location, matched pattern, risk explanation, and fix

---

## CRITICAL — Silent Production Failures

These pass all local tests but fail on Vercel. Block deployment if found.

### C1: `__dirname` / `__filename` in Server Code

**Why it breaks:** On Vercel, serverless functions are bundled by `@vercel/nft`. After bundling, `__dirname` resolves to the bundled chunk directory (e.g., `/var/task/.next/server/chunks/`), not the original source directory. Files expected to be adjacent to the source code are not there.

**Detection:**
- Grep for `__dirname` in `src/` (exclude `__tests__/`)
- Grep for `__filename` in `src/` (exclude `__tests__/`)

**False Positive Rules:**
- `__dirname` in `next.config.ts` or `next.config.js` → SAFE (runs at build time, not in serverless function)
- `__dirname` in files under `__tests__/` → SAFE (tests run locally)
- `__dirname` used only in `console.log` or error messages (not for file access) → SAFE

**Fix:** Replace with `process.cwd()` inside the handler function (not at module level — see C2 build-time caveat):
```typescript
// BAD — __dirname resolves to bundle chunk path on Vercel
const dataPath = path.join(__dirname, 'data/file.md')

// FRAGILE — works today but evaluated at module load time
const DATA_PATH = path.join(process.cwd(), 'src/lib/module/data/file.md')

// SAFEST — evaluated at request time
function getData() {
  const dataPath = path.join(process.cwd(), 'src/lib/module/data/file.md')
  return fs.readFileSync(dataPath, 'utf-8')
}
```

---

### C2: `readFileSync` / `readFile` with Unresolvable Paths

**Why it breaks:** Vercel's `@vercel/nft` uses static analysis to determine which files to include in the serverless bundle. If paths are constructed dynamically (template literals, string concatenation with variables), the tracer cannot determine which files are needed and excludes them. Result: `ENOENT: no such file or directory`.

**Detection:**
- Grep for `readFileSync` in `src/` (exclude `__tests__/`)
- Grep for `readFile[^S]` in `src/` (exclude `__tests__/`, catches async readFile but not readFileSync twice)
- For each match, check if the path argument contains variables, template literals, or function calls

**False Positive Rules:**
- `readFileSync` with a fully static string literal path → SAFE (bundler can trace it)
- `readFileSync` with `process.cwd()` + static path segments → GENERALLY SAFE (Vercel includes source files at `process.cwd()`)
- `readFileSync` in test files → SAFE
- `readFileSync` with `__dirname` → FLAG as C1 instead

**Contextual check:** For `process.cwd()` paths, verify the referenced file actually exists at the constructed path relative to project root. If the file exists, it should be included in the Vercel deployment.

**Build-time caveat:** `process.cwd()` called at module level (top-level `const`) is evaluated when the module first loads. During `next build`, this points to the build directory; at runtime on Vercel, it points to `/var/task`. This happens to work today because Vercel's build output mirrors the source structure, but it's fragile. Prefer calling `process.cwd()` inside the handler function. Flag module-level `process.cwd()` calls as a LOW concern, not CRITICAL.

**Fix:** Two options:
1. Use `process.cwd()` with static path segments (preferred for this project)
2. Add `outputFileTracingIncludes` to `next.config.ts` for the relevant routes:
```typescript
// next.config.ts
const nextConfig: NextConfig = {
  outputFileTracingIncludes: {
    '/api/chat': ['./src/lib/frameworks/prompts/**/*.md'],
  },
}
```

---

### C3: Dynamic `process.env` Access

**Why it breaks:** Next.js replaces `process.env.NEXT_PUBLIC_*` with literal values during build via static text replacement. This ONLY works with the exact pattern `process.env.NEXT_PUBLIC_FOO`. Bracket notation, destructuring, or intermediate variables defeat the replacement — the value will be `undefined` in the client bundle.

**Detection:**
- Grep for `process\.env\[` in `src/` (bracket access to env vars)
- Grep for `const.*=.*process\.env` followed by later use of the variable (intermediate variable)
- Grep for destructured env: `const { .* } = process.env` in client components

**False Positive Rules:**
- Bracket access in server-only code (API routes, `lib/` used only server-side) → LOWER RISK (server env vars are available at runtime, but bracket access is still fragile)
- Bracket access where the key is a static string constant defined in the same file → LOW RISK but still not recommended
- Literal dot access `process.env.SOME_VAR` → SAFE

**Fix:** Always use literal dot access:
```typescript
// BAD
const key = 'NEXT_PUBLIC_API_URL'
process.env[key]

// BAD
const { NEXT_PUBLIC_API_URL } = process.env

// GOOD
process.env.NEXT_PUBLIC_API_URL
```

---

### C4: Dynamic `require()` with Variable Paths

**Why it breaks:** The bundler cannot statically analyze which modules to include when the path is a runtime variable. The required files are excluded from the bundle, causing `MODULE_NOT_FOUND` at runtime.

**Detection:**
- Grep for `require(` with template literals or string concatenation in `src/` (exclude `__tests__/`)
- Pattern: `` require(` `` or `require(.*+` or `require(.*variable`

**False Positive Rules:**
- `require()` with a fully static string → SAFE (bundler traces it)
- Dynamic `import()` with static string → SAFE
- `require()` in test files (jest mocks, etc.) → SAFE
- `await import('static-string')` → SAFE (dynamic import but static path)

**Fix:** Use static imports with a mapping object:
```typescript
// BAD
const config = require(`./configs/${env}.json`)

// GOOD
import devConfig from './configs/dev.json'
import prodConfig from './configs/prod.json'
const configs = { dev: devConfig, prod: prodConfig }
const config = configs[env]
```

---

## HIGH — Data/Performance Issues

These don't crash the deployment but cause subtle bugs or performance problems. Warn but don't block.

### H1: Module-Level Mutable State

**Why it matters:** Each Vercel serverless function instance has isolated memory. Module-level state persists across requests within a single warm instance but is NOT shared across instances and is lost on cold start. This means:
- Caches work inconsistently (hit or miss depending on which instance handles the request)
- Mutable state can leak between users within the same instance
- State that grows unboundedly will eventually cause memory pressure

**Detection — scope to files changed on this branch only:**
- Run `git diff --name-only <base-branch>...HEAD` to get the changed file list
- In those files only, check for:
  - `let` at top level (mutable module state)
  - `new Map()` or `new Set()` at module level
  - `= []` or `= {}` at module level (empty collections that accumulate)
- Scanning the entire codebase produces too many false positives from intentional caches. Limit to changed files.

**False Positive Rules — Read the surrounding code to classify:**
- **Static read-only cache** (populated once from static data, never modified after init) → SAFE. Example: parsing a markdown file into a Map on first call, then returning cached result. Fine for serverless — each instance parses once.
- **TTL-bounded cache** (entries expire after a time period) → ACCEPTABLE. Memory bounded by TTL * request rate. Note: TTL only meaningful within a single instance's lifetime.
- **Unbounded mutable state** (entries added but never removed) → FLAG. Will grow indefinitely within a warm instance. Example: a Map that caches every user's profile without eviction.
- **User-scoped data without isolation** → FLAG. If Instance A handles User X then User Y, and the cache doesn't properly scope/isolate, data could leak.

**Fix:** For flagged cases:
- Add TTL or max-size bounds to caches
- Use external state stores (Redis, database) for cross-request state
- Accept the risk for low-volume apps (document the decision)

---

### H2: Native Binary Dependencies

**Why it matters:** Packages with native bindings (C/C++ addons compiled with node-gyp) must be compiled for Vercel's Linux x64 environment. If the package doesn't include prebuilt Linux binaries, or if the wrong platform's binary is bundled, the function fails at runtime with `Error: Module did not self-register` or similar.

Also: native packages are large. A single package like `sharp` adds ~15MB to the function bundle, consuming 6% of the 250MB limit.

**Detection:**
- Check `package.json` dependencies for known native packages: `sharp`, `canvas`, `bcrypt`, `better-sqlite3`, `@prisma/engines`, `puppeteer`, `playwright`
- Grep for `require('sharp')`, `require('canvas')`, etc. in `src/`
- Check if `package.json` has `optionalDependencies` with platform-specific packages

**False Positive Rules:**
- Package only used in development/testing (devDependency, only imported in test files) → SAFE
- Package uses WASM fallback on Vercel (some packages detect serverless and switch) → CHECK docs
- Package listed but not actually imported anywhere in `src/` → SAFE (tree-shaken out)

**Fix:**
- Use WASM alternatives where available (`@resvg/resvg-js-wasm`, etc.)
- Use Vercel's built-in image optimization instead of sharp
- Ensure the package includes `linux-x64` prebuilt binaries
- Consider moving heavy processing to a separate service

---

### H3: Barrel Import Bloat

**Why it breaks:** Importing from a package's barrel export (index file) can pull the entire package into the function bundle, even if only one export is used. Each API route becomes its own serverless function — shared barrel imports multiply across every function.

**Detection:**
- Grep for imports from known heavy barrel-export packages: `lodash`, `@mui/icons-material`, `@mui/material`, `date-fns`, `rxjs`
- Pattern: `from 'lodash'` (barrel) vs `from 'lodash/get'` (specific)

**False Positive Rules:**
- Specific/deep imports (`from 'lodash/get'`, `from '@mui/icons-material/Add'`) → SAFE
- Packages listed in `next.config.ts` `optimizePackageImports` → SAFE (Next.js handles tree-shaking)
- Client-only imports in components (not in API routes or server code) → LOWER RISK (affects client bundle size, not serverless function)

**Fix:**
- Use specific imports: `import get from 'lodash/get'`
- Add to `optimizePackageImports` in `next.config.ts`
- Replace with native alternatives (e.g., `Array.prototype.map` instead of `lodash/map`)

---

## MEDIUM — Potential Issues Under Load

Not checked automatically. Documented here for manual review.

### M1: Missing `maxDuration` on Long-Running Routes

**Why it matters:** Vercel serverless functions default to the plan's timeout limit (60s Hobby, up to 800s Pro). Routes that stream AI responses, process files, or call slow external APIs may exceed the default without explicit configuration. The response is silently truncated.

**Detection:**
- List all `route.ts` files in `src/app/api/`
- For each, check if it exports `maxDuration`
- Cross-reference with route content: does it use streaming (`ReadableStream`, `toTextStreamResponse`), call external AI APIs, or process files?

**False Positive Rules:**
- Simple CRUD routes that return quickly → no `maxDuration` needed
- Routes that only read from database → LOW RISK
- Routes that stream from AI models, process documents, or call slow external APIs → FLAG

**Fix:**
```typescript
// At the top of route.ts
export const maxDuration = 300 // 5 minutes
```

---

### M2: Edge Runtime with Node.js APIs

**Why it breaks:** Edge Runtime uses V8 isolates, not Node.js. It has NO access to: `fs`, `path`, `crypto` (partial), `Buffer` (partial), `child_process`, `net`, or any Node.js built-in modules.

**Detection:**
- Grep for `runtime.*=.*'edge'` or `runtime.*=.*"edge"` in `src/`
- For each match, check the file's imports for Node.js built-in modules

**False Positive Rules:**
- Middleware (`src/middleware.ts`) runs at the Edge by default — check its imports
- Routes without explicit `runtime = 'edge'` → SAFE (default is Node.js)

**Fix:** Either remove `runtime = 'edge'` (use Node.js) or replace Node.js APIs with Web Standard equivalents.

---

## LOW — Best Practice Recommendations

Not checked automatically. Documented here for manual review.

### L1: Filesystem Writes Outside `/tmp`

**Why it breaks:** Vercel's serverless filesystem is read-only except `/tmp`. Writes to any other path throw `EROFS: read-only file system`. `/tmp` itself is ephemeral (512MB limit, not shared between instances, not persistent).

**Detection:**
- Grep for `writeFileSync`, `writeFile`, `createWriteStream`, `mkdirSync`, `mkdir` in `src/` (exclude `__tests__/`)
- For matches writing to `/tmp` → check if the code assumes persistence across requests

**False Positive Rules:**
- Writes only to `/tmp` for truly temporary processing (e.g., buffer a file, process, delete) → ACCEPTABLE
- No write operations found → CLEAN

**Fix:** Use external storage (Vercel Blob, S3, database) for persistent data. Use `/tmp` only for ephemeral processing within a single request.

---

## Maintenance

Update this catalog when:
- A new Vercel deployment bug is encountered in this project
- Vercel changes their serverless runtime behavior (check Vercel changelog quarterly)
- New dependencies with native bindings are added to the project
- The project migrates to a different hosting platform

Last updated: 2026-02-02
