# Autopilot Process Instrumentation

Observability for diagnosing CPU/memory pressure and process accumulation during long autopilot runs. **No behavior change** — pure logging. Safe to leave on.

## Where the logs land

| File | Written by | Cadence |
|------|------------|---------|
| `$LOG.processes` | `snapshot_post_wait` in `lib/process.sh` | One block per claude exit (success OR timeout) |
| `$LOG.system` | background sampler started by `start_system_sampler` | Every `SAMPLER_INTERVAL` seconds (default 15) until cleanup |

`$LOG` is set by the caller — autopilot.sh uses `$PROJECT/.autopilot-log`; run-ralph.sh uses `$WORKTREE/.ralph-log`. So during a full run you'll see four files:

```
$PROJECT/.autopilot-log.processes
$PROJECT/.autopilot-log.system
$WORKTREE/.ralph-log.processes
$WORKTREE/.ralph-log.system
```

## `.processes` block format

```
==== POST-WAIT [2026-05-16 09:42:13] label=ralph-iter-3 pgid=12345 exit=0 ====
survivors_in_group=4 system_claude=6 system_node=12
--- group members (pid pgid ppid rss %cpu etime comm) ---
 12346 12345 12345 184320  2.1 00:00:42 node
 12347 12345 12346  98304  0.8 00:00:41 node
--- all claude processes (pid pgid ppid sid rss %cpu etime time comm) ---
 12345 12345 12340 12345 512000 15.2 00:00:42 00:00:08 claude
 12389 12389     1 12389 380000  3.4 00:00:05 00:00:01 claude
 12401 12401     1 12401 280000  1.2 00:00:02 00:00:00 claude
```

### What each field means

| Field | Meaning |
|-------|---------|
| `label` | Which phase or ralph iteration emitted this block |
| `pgid` | Process group id of the claude that just exited (== claude's pid) |
| `exit` | Exit code returned by `wait` (0 = success, 143/137 = killed) |
| `survivors_in_group` | Count of processes still alive in that pgid after wait. **> 0 means cleanup is incomplete on the success path.** |
| `system_claude` | Total `claude` processes on the system at snapshot time |
| `system_node` | Total `node` processes on the system at snapshot time |
| `group members` block | `ps` listing of survivors in the pgid |
| `all claude processes` block | Every `claude` on the system. **Crucial:** sub-agents spawned via Task tool may call `setsid` and escape the parent pgid — they show up here with `ppid=1` (orphaned to launchd) or with `sid != parent pgid` (own session). |

### What to look for

| Signal | What it means |
|--------|---------------|
| `survivors_in_group=0` AND `system_claude` count steady across iterations | Clean — no leak |
| `survivors_in_group > 0` for many blocks in a row | Slow cleanup tail; success path needs explicit `kill_claude` |
| `system_claude` climbs across iterations even with `survivors_in_group=0` | **Sub-agent leak via setsid** — claudes escaping the parent pgid |
| `ppid=1` in `all claude processes` block | An orphan re-parented to launchd. Confirms tree-kill failure. |
| `etime` longer than the iteration's elapsed time | Cross-iteration survivor (stale claude from a prior iteration) |
| `%cpu` > 50 on multiple claude rows | Active CPU contention, not idle accumulation |

## `.system` block format

```
==== MARKER 2026-05-16 09:42:00 ralph-iter-3 starting ====
==== SAMPLE 2026-05-16 09:42:15 ====
load:  3.45 2.91 2.03
swap: total = 4096.00M  used = 1234.50M  free = 2861.50M  (encrypted)
--- vm_stat (first 8 lines) ---
Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                               34521.
Pages active:                            980321.
Pages inactive:                          540210.
...
--- claude and node processes (pid pgid ppid rss %cpu etime time comm) ---
 12345 12345 12340 512000 15.2 00:01:32 00:00:18 claude
 12389 12389     1 380000  3.4 00:00:35 00:00:04 claude
 12346 12345 12345 184320  2.1 00:01:32 00:00:12 node
```

### What to look for

| Signal | What it means |
|--------|---------------|
| `load:` rising above CPU count for sustained periods | System CPU saturation |
| `swap: used` growing over the run | Memory pressure — predictor of slowdown / crash |
| `vm_stat` "Pages free" trending down | Memory pressure (cross-check with swap) |
| Total claude+node lines exceeding ~10 | Accumulation in progress |
| Same `pid` showing up across many samples | Long-lived survivor (potentially stuck) |
| `etime` increasing faster than wall time elapsed | A claude that never exits |

## Quick analysis one-liners

Assuming you're in the worktree (or replace `.ralph-log` with `.autopilot-log`):

```bash
# Max survivors_in_group seen across the run
grep survivors_in_group .ralph-log.processes | sort -t= -k2 -rn | head -5

# All iterations where any survivors lingered after success exit (exit=0)
awk '/exit=0/{label=$0} /survivors_in_group=/{n=$1; sub("survivors_in_group=","",n); if (n+0 > 0) print label, $0}' .ralph-log.processes

# Peak system_claude count across the run
grep system_claude .ralph-log.processes | awk '{for(i=1;i<=NF;i++) if($i ~ /system_claude=/) print $i}' | sort -t= -k2 -rn | head -5

# Find orphans (ppid=1) in any post-wait block
grep -A 20 'POST-WAIT' .ralph-log.processes | awk '$3 == 1 && $9 == "claude"'

# Load average over the run
grep '^load:' .ralph-log.system

# Swap pressure curve
grep '^swap:' .ralph-log.system | awk -F'used = ' '{print $2}' | awk '{print $1}'

# Iterations correlated with peak claude count (uses MARKER lines)
awk '/^==== MARKER/{m=$0} /comm/{} END{}' .ralph-log.system  # see MARKER + nearby SAMPLE blocks
```

## Cleanup if autopilot was killed with SIGKILL

The sampler runs in a background subshell. Normal exit paths (clean exit, SIGINT, SIGTERM, watchdog timeout) all reach the EXIT trap → `cleanup` → `stop_system_sampler`. But `kill -9` of the parent script bypasses the trap and orphans the sampler.

To clean up an orphan sampler:

```bash
pgrep -fl 'sleep 15' | grep -v grep   # locate
pkill -f 'while true; do sleep'       # kill
```

## Tuning

| Env var | Default | When to change |
|---------|---------|----------------|
| `SAMPLER_INTERVAL` | 15 | Lower (5-10) for capturing fast CPU bursts; higher (30-60) for long quiet runs |

## Disabling

The instrumentation activates automatically when `lib/process.sh` is sourced and `LOG` is set. To run with no observability, unset `LOG` before invoking — the sampler returns immediately and snapshots are silent no-ops.
