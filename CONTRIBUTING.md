# Contributing

If you are an automated agent rather than a person, read [`AGENTS.md`](AGENTS.md) first: it is this document compressed to the rules that change what a patch looks like.

## What is useful

- **A bug report with a file.** The smallest `.iac` file that shows the problem, plus the command you ran and the exit code. A failing conformance case is better than either.
- **A documentation fix.** If a guide contradicts the spec, that is a bug in the guide — say which sentence and which spec section.
- **A conformance case.** One case per PR is fine; the corpus is the format's real contract.
- **An independent implementation.** The point of a spec is a second parser. Tell us when yours passes the corpus.
- **An RFC.** Anything that changes behaviour, syntax, or the registry.

Not useful: reformatting patches, new `Type` values that bypass the registry, and vendor-specific hacks. If your product needs something the format does not have, that is an RFC discussion, not a patch.

## Propose a change

Normative changes — grammar, field semantics, error taxonomy, registry, conformance outcomes — go through the RFC process in [GOVERNANCE.md](GOVERNANCE.md). In short: copy [rfcs/0000-template.md](rfcs/0000-template.md), claim the next free number, open a PR with status `Draft`, and expect a 10-day comment period (20 for a breaking change). An RFC that changes behaviour needs a **Compatibility impact** section; without it, it is not ready for review.

Non-normative changes go straight to a PR: docs, tooling fixes, test cases that pin existing behaviour, broken links. If you are unsure whether your change is normative, ask in an issue before writing the RFC — a question costs a day, a rejected RFC costs a week.

Editorial corrections to an accepted specification — typographical errors, dead links, clarifications that cannot change any conformance outcome — ship as a patch release with a CHANGELOG entry. Nothing else is editorial.

## Add a conformance case

The corpus lives in [testdata/](testdata/), and [testdata/conformance.json](testdata/conformance.json) is normative: it maps each case file to its expected outcome (`ok`, `warning`, or `error`) and to the exact set of codes a conforming parser must produce.

A good case:

- **has one reason to exist.** One defect per invalid case: a file with two errors gives an implementation two ways to pass for the wrong reason;
- **is small.** A few lines, hand-written, no real production dialogue;
- **names the defect.** Follow the existing naming pattern in `testdata/valid/` and `testdata/invalid/` so a reader can tell what it pins;
- **pins the expected code set.** If the case is rejected, `conformance.json` names every code it must produce, and a tool that produces a different set fails;
- **does not depend on detection order** unless it is specifically about detection order — in which case the case name says so and the expected code is the one spec §8.2 requires.

If a case seems to contradict the spec, that is a spec bug: open an RFC rather than editing the case. Special-casing the corpus defeats its purpose.

## Code

`tools/` is the reference implementation, and its job is to be readable and boring.

- **Python 3, standard library only.** No dependencies, because the tool must run from a checkout in a studio's CI without a package review. If you need a dependency, you need a different design.
- **The CLI surface is fixed:** `validate <file-or-dir> [--json]`, `fmt <file>`, `from-srt <in.srt> <out.iac>`. Exit codes mean the same everywhere — `0` clean, `1` warnings, `2` errors — and a subcommand that cannot produce warnings simply never returns `1`. New flags need a maintainer discussion, not an RFC, but they must never change what an existing exit code means.
- **Diagnostics carry the code.** Every message a user sees includes its `E`/`W` code and the line number.
- **No silent repair.** A validator does not fix; a formatter does not validate away an error; a converter reports what it dropped.

## Docs

- UTF-8, LF, no BOM. Wrap prose at about 100 columns; do not wrap code blocks or tables.
- **Link the spec, do not restate it.** "A stop must be after its start (spec §6.3)" is right; a second normative sentence in a guide is a future contradiction. If a rule cannot be summarised in a sentence, that is a gap in the spec, not a reason to duplicate it.
- Language: American English, present tense, second person. Error codes in backticks. Headings in sentence case. Code fences always carry a language (`iac`, `bash`, `json`, `text`).
- No marketing adjectives, no "Welcome", no "simply", no "just", no "of course". A reader who is stuck is not helped by being told it is easy.
- Every relative link must resolve, including anchors. Review checks this; so should you.
- Do not add a "TBD". If a decision is not made, link the RFC that will make it.

## Commits and sign-off

Commit with a sign-off:

```bash
git commit -s -m "spec: clarify half-open interval with a boundary example"
```

The sign-off certifies the [Developer Certificate of Origin 1.1](https://developercertificate.org/). Use your real name and an address you can be reached at. There is no CLA and no copyright assignment: contributions are licensed under the terms of the files they touch — spec text and docs CC BY 4.0, code Apache-2.0, examples CC0-1.0.

Keep commits focused. A formatting pass bundled with a semantic change cannot be reviewed, and will be sent back. Rebase rather than merge when updating a branch if you can do it without losing review context.

## Review

Maintainers review best-effort; there is no service-level agreement. Small PRs that cite an RFC or a failing case merge fastest.

Reviewers check, in order: does it contradict the spec; does it have a conformance case; does it change behaviour that existing files rely on; is it implemented in the reference tool; are the docs updated. A PR that changes the format without a case and a docs change is incomplete, not "later".

Security issues in the tooling should go through a private advisory on the repository rather than a public issue. The format itself has no attack surface beyond a parser's input handling; see [spec/appendix/security-considerations.md](spec/appendix/security-considerations.md).

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating you agree to it.
