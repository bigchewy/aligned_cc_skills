#!/usr/bin/env python3
"""Count what add-framework Steps 1, 3 and 4 ask for in one framework folder.

Usage: python3 check_framework.py <framework-folder>

Prints the number of examples for every phase, then a list of problems.
Exits 0 when there are none and 1 when there are any. It reads files and
changes nothing.
"""

import re
import sys
from pathlib import Path

FILES = ["prompt.md", "examples.md", "anti-examples.md", "sources.md"]
MIN_EXAMPLES = 2
MIN_ANTI_EXAMPLES = 3

PHASE = re.compile(r"^(#{1,4})[ \t]*(?:PHASE|Phase|STEP|Step)[ \t]*(\d+)\b", re.M)
HEADING = re.compile(r"^(#{1,6})[ \t]+\S.*$", re.M)


def sections(text, pattern):
    """Yield (match, body) for each heading the pattern finds, body running to the next one."""
    marks = list(pattern.finditer(text))
    for i, mark in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        yield mark, text[mark.end():end]


def count_examples(text):
    """Return {phase number: [body of each example]} for an examples.md."""
    found = {}
    for mark, body in sections(text, PHASE):
        deeper = len(mark.group(1)) + 1
        example = re.compile(rf"^#{{{deeper}}}[ \t]+\S.*$", re.M)
        bodies = [b for _, b in sections(body, example)]
        found.setdefault(int(mark.group(2)), []).extend(bodies)
    return found


def count_anti_examples(text):
    """A failure mode is a headed section that shows both a wrong and a right response."""
    total = 0
    for mark, body in sections(text, HEADING):
        if len(mark.group(1)) == 1:
            continue
        lower = body.lower()
        if "wrong" in lower and "right" in lower:
            total += 1
    return total


def check(folder):
    lines, problems = [], []

    missing = [name for name in FILES if not (folder / name).is_file()]
    for name in missing:
        problems.append(f"{name} is missing.")

    phases = []
    if "prompt.md" not in missing:
        prompt = (folder / "prompt.md").read_text(encoding="utf-8")
        phases = sorted({int(m.group(2)) for m in PHASE.finditer(prompt)})
        if not phases:
            problems.append(
                "prompt.md has no phase headings of the form '### PHASE 1: Name', "
                "so the examples can't be counted."
            )

    if phases and "examples.md" not in missing:
        found = count_examples((folder / "examples.md").read_text(encoding="utf-8"))
        lines.append("Examples per phase:")
        for number in phases:
            bodies = found.get(number, [])
            lines.append(f"  PHASE {number}: {len(bodies)}")
            if len(bodies) < MIN_EXAMPLES:
                noun = "example" if len(bodies) == 1 else "examples"
                problems.append(
                    f"examples.md: PHASE {number} has {len(bodies)} {noun}. "
                    f"Every phase needs at least {MIN_EXAMPLES}."
                )
            bare = sum(1 for b in bodies if not re.search(r"^>[ \t]*\S", b, re.M))
            if bare:
                problems.append(
                    f"examples.md: PHASE {number} has {bare} example(s) with no note "
                    "saying why the response works (a line starting with '>')."
                )

    if "anti-examples.md" not in missing:
        total = count_anti_examples((folder / "anti-examples.md").read_text(encoding="utf-8"))
        lines.append(f"Anti-examples: {total}")
        if total < MIN_ANTI_EXAMPLES:
            problems.append(
                f"anti-examples.md has {total} failure modes with a wrong and a right "
                f"response. It needs at least {MIN_ANTI_EXAMPLES}."
            )

    return lines, problems


def main(argv):
    if len(argv) != 2:
        print("Usage: python3 check_framework.py <framework-folder>")
        return 1
    folder = Path(argv[1])
    if not folder.is_dir():
        print(f"{folder} is not a folder.")
        return 1

    lines, problems = check(folder)
    print(f"Framework: {folder.name}")
    for line in lines:
        print(line)
    if not problems:
        print("Problems: none")
        return 0
    print(f"Problems: {len(problems)}")
    for problem in problems:
        print(f"  - {problem}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
