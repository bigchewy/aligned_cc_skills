#!/usr/bin/env bash
#
# find-polluter.sh — Bisect a test suite to identify the test that pollutes
# shared state. Usage:
#
#   ./find-polluter.sh '<sentinel>' '<test-glob>'
#
# sentinel:  A string/path the polluter creates or modifies (e.g., '.git',
#            '/tmp/flag', 'cache-file'). The script checks for this sentinel
#            after each test run.
# test-glob: A glob matching the test files to bisect (e.g.,
#            'src/**/*.test.ts').
#
# The script iterates tests one at a time. After each test, it checks whether
# the sentinel exists. The first test after which the sentinel appears is the
# polluter.
#
# Intended to be run from a project root that has a test command. Set the
# TEST_CMD env var to override the default (which assumes `npm test`). The
# test command receives the current test file path as its final argument.

set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 '<sentinel>' '<test-glob>'" >&2
  exit 2
fi

sentinel="$1"
glob="$2"
test_cmd="${TEST_CMD:-npm test --}"

# Collect files matching the glob (Bash 4+ globstar).
shopt -s globstar nullglob
# shellcheck disable=SC2206
files=( $glob )
shopt -u globstar nullglob

if [[ ${#files[@]} -eq 0 ]]; then
  echo "No files matched glob: $glob" >&2
  exit 1
fi

echo "Bisecting ${#files[@]} test files for polluter that creates: $sentinel"

# Ensure the sentinel is absent before we start.
if [[ -e "$sentinel" ]]; then
  echo "Sentinel '$sentinel' already exists before any test ran. Remove it first." >&2
  exit 1
fi

for f in "${files[@]}"; do
  echo "-- Running: $f"
  $test_cmd "$f" >/dev/null 2>&1 || true

  if [[ -e "$sentinel" ]]; then
    echo ""
    echo "POLLUTER FOUND: $f"
    echo "Sentinel '$sentinel' appeared after this test."
    exit 0
  fi
done

echo ""
echo "No polluter found. Sentinel '$sentinel' was not produced by any test."
exit 0
