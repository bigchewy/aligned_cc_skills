// condition-based-waiting-example.ts
//
// Domain-specific helpers for condition-based waiting in event-driven test
// suites. Use these instead of fixed-duration sleeps. Each helper polls a
// predicate until it is satisfied or a deadline passes.
//
// Why not `await new Promise(r => setTimeout(r, N))`? Fixed sleeps are always
// wrong. Too short, the test is flaky; too long, the suite is slow. Poll the
// actual condition instead.

type EventRecord = {
  type: string
  payload: Record<string, unknown>
  timestamp: number
}

type WaitOptions = {
  timeoutMs?: number
  intervalMs?: number
}

const DEFAULT_TIMEOUT_MS = 5000
const DEFAULT_INTERVAL_MS = 25

async function poll<T>(
  predicate: () => T | null | undefined,
  timeoutMs: number,
  intervalMs: number,
  description: string,
): Promise<T> {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    const result = predicate()
    if (result !== null && result !== undefined) {
      return result
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  throw new Error(`Timed out after ${timeoutMs}ms waiting for: ${description}`)
}

// Wait until at least one event of the given type has been recorded.
export async function waitForEvent(
  events: EventRecord[],
  type: string,
  options: WaitOptions = {},
): Promise<EventRecord> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  return poll(
    () => events.find((e) => e.type === type),
    timeoutMs,
    intervalMs,
    `event of type "${type}"`,
  )
}

// Wait until at least `count` events of the given type have been recorded.
export async function waitForEventCount(
  events: EventRecord[],
  type: string,
  count: number,
  options: WaitOptions = {},
): Promise<EventRecord[]> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  return poll(
    () => {
      const matches = events.filter((e) => e.type === type)
      return matches.length >= count ? matches : null
    },
    timeoutMs,
    intervalMs,
    `${count} events of type "${type}"`,
  )
}

// Wait until at least one event matches a custom predicate.
export async function waitForEventMatch(
  events: EventRecord[],
  match: (event: EventRecord) => boolean,
  description: string,
  options: WaitOptions = {},
): Promise<EventRecord> {
  const timeoutMs = options.timeoutMs ?? DEFAULT_TIMEOUT_MS
  const intervalMs = options.intervalMs ?? DEFAULT_INTERVAL_MS
  return poll(
    () => events.find(match),
    timeoutMs,
    intervalMs,
    `event matching "${description}"`,
  )
}
