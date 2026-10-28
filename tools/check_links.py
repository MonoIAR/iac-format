#!/usr/bin/env python3
"""Check the documentation invariants that a spellchecker cannot.

    python tools/check_links.py [--root .]

Two checks, both offline:

1. every relative link and image path resolves, and every `#anchor` names a
   heading in its target file;
2. every diagnostic code mentioned in Markdown (E001, W004, ...) is defined in
   the §8.1 table of `spec/iac-1.0.md`.

External links are not fetched: a documentation repository should not need
network access to pass CI.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Iterable, List, Set, Tuple

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
# A diagnostic code is E001 / W004 and stands alone: not part of an identifier and
# not a Unicode scalar value such as U+E000 in the specification.
CODE_RE = re.compile(r"(?<![A-Za-z0-9+])([EW]\d{3})(?![A-Za-z0-9])")
CODE_ROW_RE = re.compile(r"^\|\s*([EW]\d{3})\s*\|", re.MULTILINE)

SPEC_PATH = os.path.join("spec", "iac-1.0.md")


def slugify(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: str) -> Set[str]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError:
        return set()
    text = FENCE_RE.sub("", text)
    return {slugify(m.group(1)) for m in HEADING_RE.finditer(text)}


def iter_markdown(root: str) -> Iterable[str]:
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "node_modules", "__pycache__"}]
        for name in filenames:
            if name.endswith(".md"):
                yield os.path.join(directory, name)


def defined_codes(root: str) -> Set[str]:
    with open(os.path.join(root, SPEC_PATH), "r", encoding="utf-8") as handle:
        text = handle.read()
    return {m.group(1) for m in CODE_ROW_RE.finditer(text)}


def check_links(root: str) -> Tuple[int, List[str]]:
    checked = 0
    problems: List[str] = []
    for path in iter_markdown(root):
        with open(path, "r", encoding="utf-8") as handle:
            text = FENCE_RE.sub("", handle.read())
        for match in LINK_RE.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "tel:")):
                continue
            anchor = ""
            if "#" in target:
                target, anchor = target.split("#", 1)
            checked += 1
            if target:
                resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
                if not os.path.exists(resolved):
                    problems.append(f"{path}: broken path -> {target}")
                    continue
            else:
                resolved = path
            if anchor and resolved.endswith(".md"):
                if anchor not in anchors(resolved):
                    problems.append(f"{path}: broken anchor -> #{anchor}")
    return checked, problems


def check_codes(root: str, codes: Set[str]) -> Tuple[int, List[str]]:
    seen = 0
    problems: List[str] = []
    for path in iter_markdown(root):
        with open(path, "r", encoding="utf-8") as handle:
            text = handle.read()
        for match in CODE_RE.finditer(text):
            seen += 1
            if match.group(1) not in codes:
                problems.append(f"{path}: unknown diagnostic code {match.group(1)}")
    return seen, problems


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    codes = defined_codes(args.root)
    if not codes:
        print(f"{SPEC_PATH}: no diagnostic codes found in the §8.1 table", file=sys.stderr)
        return 1

    links, link_problems = check_links(args.root)
    references, code_problems = check_codes(args.root, codes)
    problems = link_problems + code_problems
    print(
        f"checked {links} relative links and {references} diagnostic-code references "
        f"({len(codes)} defined) in {args.root}"
    )
    for problem in problems:
        print("  " + problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
