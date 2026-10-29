export const meta = {
  name: 'find-potential-advisors',
  description: 'Research a domain, profile and evaluate advisor candidates, pick finalists, write and check the brief',
  whenToUse: 'Run by the find-potential-advisors skill after its Phase 1 interview has written the brief',
  phases: [
    { title: 'Research', detail: 'one agent per research question' },
    { title: 'Candidates', detail: 'pick candidates from the research' },
    { title: 'Profile and evaluate', detail: 'profile 3 candidates per agent, then a different agent counts their sources' },
    { title: 'Finalists', detail: 'pick 2-3 finalists from the strong candidates' },
    { title: 'Write', detail: 'fill the report template in the brief' },
    { title: 'Check', detail: 'a fresh agent checks the brief against the template and the sources' },
  ],
}

// args: { brief_path, skill_dir, research_questions: string[], candidate_count?, exclude?: string[] }
const BRIEF = args.brief_path
const SKILL_DIR = args.skill_dir
const QUESTIONS = args.research_questions || []
const COUNT = args.candidate_count || 10
const EXCLUDE = args.exclude || []
const BATCH = 3

if (!BRIEF || !SKILL_DIR || QUESTIONS.length === 0) {
  throw new Error('find-potential-advisors needs args.brief_path, args.skill_dir and at least one research question')
}

// Every agent reads its instructions from agent-prompts.md, so the Agent-tool
// fallback in SKILL.md and this script use the same words.
const instructions = (section) =>
  `Read ${SKILL_DIR}/agent-prompts.md, the section "## ${section}", and follow it.`

const link = { type: 'string', description: 'http(s) URL of a page you opened' }
const listOf = (props, required) => ({
  type: 'array',
  items: { type: 'object', properties: props, required: required || Object.keys(props) },
})

const RESEARCH = {
  type: 'object',
  properties: {
    findings: listOf({ claim: { type: 'string' }, source_url: link, source_type: { type: 'string' } }),
    approaches: listOf({ name: { type: 'string' }, evidence: { type: 'string' }, source_urls: { type: 'array', items: link } }),
    names_mentioned: listOf({ name: { type: 'string' }, why: { type: 'string' }, source_url: link }),
    pages_opened: { type: 'integer' },
  },
  required: ['findings', 'approaches', 'names_mentioned', 'pages_opened'],
}
const CANDIDATES = {
  type: 'object',
  properties: {
    candidates: listOf({ name: { type: 'string' }, credentials: { type: 'string' }, why_considered: { type: 'string' }, source_url: link }),
  },
  required: ['candidates'],
}
const PROFILES = {
  type: 'object',
  properties: {
    profiles: listOf(
      {
        name: { type: 'string' },
        credentials: { type: 'string' },
        approach: { type: 'string' },
        key_works: listOf({ title: { type: 'string' }, year: { type: 'string' }, url: link }),
        fit: { type: 'string' },
        sources: { type: 'array', items: link },
        unverified: { type: 'array', items: { type: 'string' } },
      },
      ['name', 'credentials', 'approach', 'key_works', 'fit', 'sources', 'unverified'],
    ),
  },
  required: ['profiles'],
}
const EVALUATIONS = {
  type: 'object',
  properties: {
    evaluations: listOf(
      {
        name: { type: 'string' },
        books: listOf({ title: { type: 'string' }, year: { type: 'string' }, url: link }),
        talks: listOf({ title: { type: 'string' }, minutes: { type: 'number' }, url: link }),
        distinctive_terms: listOf({ term: { type: 'string' }, url: link }),
        quotes: listOf({ text: { type: 'string' }, url: link }),
        availability: { type: 'string' },
        not_found: { type: 'array', items: { type: 'string' } },
      },
      ['name', 'books', 'talks', 'distinctive_terms', 'quotes', 'availability', 'not_found'],
    ),
  },
  required: ['evaluations'],
}
const FINALISTS = {
  type: 'object',
  properties: {
    finalists: listOf({
      name: { type: 'string' },
      summary: { type: 'string' },
      differentiation: { type: 'string' },
      framework_potential: { type: 'string' },
      voice_sample: { type: 'string' },
      voice_sample_quote_urls: { type: 'array', items: link },
      tradeoffs: { type: 'string' },
    }),
    recommendation: { type: 'string' },
    recommendation_reason: { type: 'string' },
  },
  required: ['finalists', 'recommendation', 'recommendation_reason'],
}
const WRITTEN = { type: 'object', properties: { brief_path: { type: 'string' } }, required: ['brief_path'] }
const CHECKED = { type: 'object', properties: { problems: { type: 'array', items: { type: 'string' } } }, required: ['problems'] }
const FIXED = { type: 'object', properties: { fixed: { type: 'boolean' } }, required: ['fixed'] }

const skipped = []
const agentsRun = {}
const count = (role) => { agentsRun[role] = (agentsRun[role] || 0) + 1 }
const json = (value) => JSON.stringify(value, null, 1)

// --- Research: one agent per question ---------------------------------------
phase('Research')
const research = await parallel(QUESTIONS.map((q, i) => () => {
  count('research')
  return agent(
    `${instructions('Research')}\n\nBrief: ${BRIEF}\nResearch question: ${q}`,
    { label: `research:${i + 1}`, phase: 'Research', schema: RESEARCH },
  )
}))
const answered = []
research.forEach((r, i) => {
  if (r) answered.push({ question: QUESTIONS[i], ...r })
  else skipped.push(`Research question "${QUESTIONS[i]}": the agent failed, so this question has no findings.`)
})
const pagesOpened = answered.reduce((sum, r) => sum + (r.pages_opened || 0), 0)
if (answered.length === 0) return { status: 'failed', brief_path: BRIEF, skipped, agents_run: agentsRun }

// --- Candidates --------------------------------------------------------------
phase('Candidates')
count('candidates')
const picked = await agent(
  `${instructions('Candidates')}\n\nBrief: ${BRIEF}\nHow many candidates: ${COUNT}\n` +
  `Already on the board, leave out: ${EXCLUDE.join(', ') || 'none'}\n\nResearch findings:\n${json(answered)}`,
  { label: 'candidates', phase: 'Candidates', schema: CANDIDATES },
)
if (!picked || picked.candidates.length === 0) {
  skipped.push('Candidates: the agent failed or found no one, so no one was profiled.')
  return { status: 'failed', brief_path: BRIEF, skipped, agents_run: agentsRun }
}
const candidates = picked.candidates.slice(0, COUNT)
if (picked.candidates.length > COUNT) log(`Kept ${COUNT} of ${picked.candidates.length} candidates`)

// --- Profile, then a different agent evaluates --------------------------------
const batches = []
for (let i = 0; i < candidates.length; i += BATCH) batches.push(candidates.slice(i, i + BATCH))

const hasUrl = (x) => typeof x.url === 'string' && /^https?:\/\//.test(x.url)

function rate(e) {
  const books = (e.books || []).filter(hasUrl)
  const talks = (e.talks || []).filter((t) => hasUrl(t) && t.minutes > 0)
  const terms = (e.distinctive_terms || []).filter(hasUrl)
  const minutes = talks.reduce((sum, t) => sum + t.minutes, 0)
  const hours = Math.round((minutes / 60) * 10) / 10
  let rating = 'Low'
  if (books.length >= 2 && hours >= 5 && terms.length >= 3) rating = 'High'
  else if ((books.length >= 1 || hours >= 2) && terms.length >= 1) rating = 'Medium'
  return {
    ...e,
    books_counted: books.length,
    talk_minutes: talks.map((t) => t.minutes),
    hours,
    terms_counted: terms.length,
    rating,
  }
}

phase('Profile and evaluate')
const batchResults = await pipeline(
  batches,
  (batch, _item, i) => {
    count('profile')
    return agent(
      `${instructions('Profile')}\n\nBrief: ${BRIEF}\nCandidates:\n${json(batch)}`,
      { label: `profile:${i + 1}`, phase: 'Profile and evaluate', schema: PROFILES },
    )
  },
  (profiled, batch, i) => {
    if (!profiled) {
      skipped.push(`Profiles of ${batch.map((c) => c.name).join(', ')}: the agent failed, so they were not profiled or evaluated.`)
      return null
    }
    count('evaluate')
    return agent(
      `${instructions('Evaluate')}\n\nCandidates (names only; find every source yourself):\n` +
      `${batch.map((c) => `- ${c.name}`).join('\n')}`,
      { label: `evaluate:${i + 1}`, phase: 'Profile and evaluate', schema: EVALUATIONS },
    ).then((evaluated) => ({ batch, profiled, evaluated }))
  },
)

const evaluations = []
const profiles = []
batchResults.forEach((r) => {
  if (!r) return
  const { batch, profiled, evaluated } = r
  for (const c of batch) {
    const p = profiled.profiles.find((x) => x.name === c.name)
    const e = evaluated && evaluated.evaluations.find((x) => x.name === c.name)
    if (!p) skipped.push(`Profile of ${c.name}: the agent returned none.`)
    if (!e) skipped.push(`Evaluation of ${c.name}: the agent failed or returned none, so ${c.name} has no rating.`)
    if (p && e) {
      profiles.push(p)
      evaluations.push(rate(e))
    }
  }
})

const order = { High: 0, Medium: 1, Low: 2 }
evaluations.sort((a, b) => order[a.rating] - order[b.rating] || b.hours - a.hours)
const strong = evaluations.filter((e) => e.rating !== 'Low')
log(`${strong.length} of ${evaluations.length} evaluated candidates rated High or Medium`)

const data = () => ({ brief_path: BRIEF, research: answered, candidates, profiles, evaluations, skipped, agents_run: agentsRun, pages_opened: pagesOpened })

// Fewer than 2 strong candidates: write what we have and hand the choice back.
if (strong.length < 2) {
  phase('Write')
  count('write')
  await agent(
    `${instructions('Write')}\n\nThis run stopped before finalists: fewer than 2 candidates rated High or Medium. ` +
    `Fill every section up to Evaluation, plus "What was skipped or not verified" and "Run record".\n\nRun data:\n${json(data())}`,
    { label: 'write', phase: 'Write', schema: WRITTEN },
  )
  return { status: 'too_few', ...data() }
}

// --- Finalists -----------------------------------------------------------------
phase('Finalists')
count('finalists')
const strongProfiles = profiles.filter((p) => strong.some((e) => e.name === p.name))
const chosen = await agent(
  `${instructions('Finalists')}\n\nBrief: ${BRIEF}\nAlready on the board: ${EXCLUDE.join(', ') || 'none'}\n\n` +
  `Strong candidates, ranked (ratings were computed from the cited sources and are final):\n${json(strong)}\n\nTheir profiles:\n${json(strongProfiles)}`,
  { label: 'finalists', phase: 'Finalists', schema: FINALISTS },
)
if (!chosen) {
  skipped.push('Finalists: the agent failed, so no finalists were chosen.')
  return { status: 'failed', ...data() }
}

// --- Write the brief -----------------------------------------------------------
phase('Write')
count('write')
const written = await agent(
  `${instructions('Write')}\n\nRun data:\n${json({ ...data(), finalists: chosen.finalists, recommendation: chosen.recommendation, recommendation_reason: chosen.recommendation_reason })}`,
  { label: 'write', phase: 'Write', schema: WRITTEN },
)
if (!written) {
  skipped.push('Write: the agent failed, so the brief was not written.')
  return { status: 'failed', ...data(), finalists: chosen.finalists }
}

// --- A fresh agent checks the brief; one fix round -----------------------------
phase('Check')
count('check')
let checked = await agent(`${instructions('Check')}\n\nBrief: ${BRIEF}`, { label: 'check:1', phase: 'Check', schema: CHECKED })
let problems = checked ? checked.problems : ['The check agent failed, so the brief was not checked.']
if (checked && problems.length > 0) {
  count('fix')
  await agent(
    `${instructions('Fix')}\n\nBrief: ${BRIEF}\nProblems found:\n${problems.map((p) => `- ${p}`).join('\n')}`,
    { label: 'fix', phase: 'Check', schema: FIXED },
  )
  count('check')
  checked = await agent(`${instructions('Check')}\n\nBrief: ${BRIEF}`, { label: 'check:2', phase: 'Check', schema: CHECKED })
  problems = checked ? checked.problems : ['The second check agent failed, so the fixes were not checked.']
}

return {
  status: 'done',
  ...data(),
  finalists: chosen.finalists,
  recommendation: chosen.recommendation,
  problems,
}
