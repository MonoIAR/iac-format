#!/usr/bin/env python3
"""Check that every relative link and image path in the repository resolves.

    python tools/check_links.py [--root .]

External links are not fetched: a documentation repo should not need network
access to pass CI. Anchors are checked against headings in the target file.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Iterable, List, Tuple

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#{1,6}\s+(.*)$", re.MULTILINE)
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)


def slugify(heading: str) -> str:
    text = heading.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def anchors(path: str) -> set:
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


def check(root: str) -> Tuple[int, List[str]]:
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


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    checked, problems = check(args.root)
    print(f"checked {checked} relative links in {args.root}")
    if problems:
        for problem in problems:
            print("  " + problem)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
