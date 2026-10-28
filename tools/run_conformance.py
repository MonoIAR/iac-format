#!/usr/bin/env python3
"""Run the IAC conformance suite.

    python tools/run_conformance.py [--suite-dir testdata] [--verbose]

A case passes when the reference parser reports exactly the expected set of
diagnostic codes for that file, and the overall severity matches `expect`.

This file is the definition of "conforms" for the suite in testdata/. Any
third-party parser can be checked against the same corpus by swapping the
`run_parser` function.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, List, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from iac_lint import parse_file  # noqa: E402


def run_parser(path: str) -> Set[str]:
    doc = parse_file(path)
    return {d.code for d in doc.diagnostics}


def classify(codes: Set[str]) -> str:
    errors = {c for c in codes if c.startswith("E")}
    if errors:
        return "error"
    if codes:
        return "warning"
    return "ok"


def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-dir", default="testdata")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args(argv)

    suite_path = os.path.join(args.suite_dir, "conformance.json")
    if not os.path.exists(suite_path):
        print(f"missing suite file: {suite_path}", file=sys.stderr)
        return 2

    with open(suite_path, "r", encoding="utf-8") as handle:
        suite = json.load(handle)

    cases = suite.get("cases", [])
    if not cases:
        print("suite contains no cases", file=sys.stderr)
        return 2

    failures: List[str] = []
    checked: Dict[str, int] = {"ok": 0, "warning": 0, "error": 0}

    for case in cases:
        relative = case["file"]
        expect = case["expect"]
        expected_codes = set(case.get("codes", []))
        path = os.path.join(args.suite_dir, relative)

        if not os.path.exists(path):
            failures.append(f"{relative}: file does not exist")
            continue

        actual_codes = run_parser(path)
        actual_kind = classify(actual_codes)
        checked[expect] = checked.get(expect, 0) + 1

        problems = []
        if actual_kind != expect:
            problems.append(f"expected {expect}, got {actual_kind}")
        if actual_codes != expected_codes:
            missing = sorted(expected_codes - actual_codes)
            extra = sorted(actual_codes - expected_codes)
            if missing:
                problems.append(f"missing {missing}")
            if extra:
                problems.append(f"unexpected {extra}")

        if problems:
            failures.append(f"{relative}: " + "; ".join(problems))
        elif args.verbose:
            print(f"PASS {relative} ({expect})")

    total = len(cases)
    print(f"\nIAC {suite.get('suite', '?')} conformance: {total - len(failures)}/{total} passed")
    print(f"  ok={checked.get('ok', 0)} warning={checked.get('warning', 0)} error={checked.get('error', 0)}")
    if failures:
        print("\nfailures:")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
