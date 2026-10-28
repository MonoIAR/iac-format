# Contributing

If you are an automated agent rather than a person, read [`AGENTS.md`](AGENTS.md) first:
it is this document compressed to the rules that change what a patch looks like.

## What is useful

- **A bug report with a file.** The smallest `.iac` file that shows the problem, the
  command you ran, and the exit code. A failing conformance case is better than either.
- **A documentation fix.** If a guide contradicts the specification, that is a bug in
  the guide — say which sentence and which section.
- **A conformance case.** One case per pull request is fine; the corpus is the format's
  real contract.
- **An independent implementation.** The point of a specification is a second parser.
  Tell us when yours passes the corpus.
- **An RFC.** Anything that changes behaviour, syntax, or the registry.

Not useful: reformatting patches, new `Type` values that bypass the registry, and
vendor-specific hacks. If your product needs something the format does not have, that is
an RFC discussion, not a patch.

## Propose a change

Normative changes — grammar, field semantics, error taxonomy, registry, conformance
outcomes — go through the RFC process in [GOVERNANCE.md](GOVERNANCE.md). In short: copy
[rfcs/0000-template.md](rfcs/0000-template.md), claim the next free number, open a pull
request with status `Draft`, and expect a 10-day comment period (20 for a breaking
change).

Non-normative changes go straight to a pull request: docs, tooling fixes, test cases
that pin existing behaviour, broken links. If you are unsure which it is, ask in an
issue before writing an RFC.

Editorial corrections to an accepted specification — typographical errors, dead links,
clarifications that cannot change any conformance outcome — ship as a patch release
with a changelog entry. Nothing else is editorial.

## Add a conformance case

The corpus lives in [testdata/](testdata/), and
[testdata/conformance.json](testdata/conformance.json) is normative: it maps each case
file to its expected outcome (`ok`, `warning`, `error`) and to the exact set of codes a
conforming parser must produce.

A good case:

- **has one reason to exist.** One defect per invalid case: two errors in one file give
  an implementation two ways to pass for the wrong reason;
- **is small.** A few lines, hand-written, no production dialogue;
- **names the defect.** Follow the naming in `testdata/valid/` and `testdata/invalid/`;
- **pins the expected code set.** A tool that produces a different set fails;
- **does not depend on detection order** unless it is about detection order, in which
  case the name says so.

A case that seems to contradict the specification is a specification bug: open an RFC
rather than editing the case. Special-casing the corpus defeats its purpose.

## Code

`tools/` is the reference implementation, and its job is to be readable and boring.

- **Python 3, standard library only.** No dependencies: the tool must run from a
  checkout in a studio's CI without a package review.
- **The CLI surface is fixed:**
  ```text
  validate <path>... [--json]
  fmt <path>... [--check] [--stdout]
  from-srt <in.srt> <out.iac> [--name NAME]
  migrate <path>... [--check]
  ```
  Exit codes mean the same everywhere — `0` clean, `1` warnings, `2` errors — and a
  subcommand that cannot produce warnings never returns `1`.
- **Diagnostics carry the code.** Every message a user sees includes its `E`/`W` code
  and the line number.
- **No silent repair.** A validator does not fix; a formatter does not validate away an
  error; a converter reports what it dropped and refuses to write a file it cannot parse.

## Docs

- UTF-8, LF, no BOM. Wrap prose at about 100 columns; do not wrap code blocks or tables.
- **Link the spec, do not restate it.** "A stop must be after its start
  (spec §6.3)" is right; a second normative sentence in a guide is a future
  contradiction. If a rule cannot be summarised in a sentence, that is a gap in the
  specification, not a reason to duplicate it.
- Language: British spelling (`colour`, `behaviour`), present tense, second person.
  Error codes in backticks. Headings in sentence case. Code fences always carry a
  language (`iac`, `bash`, `json`, `text`).
- No marketing adjectives, no "Welcome", no "simply", no "just", no "of course".
- Every relative link must resolve, including anchors. `tools/check_links.py` checks
  that, and also that every diagnostic code you mention exists in the specification.
- Do not add a "TBD". If a decision is not made, link the RFC that will make it.

## Commits and sign-off

Commit with a sign-off:

```bash
git commit -s -m "spec: clarify half-open interval with a boundary example"
```

The sign-off certifies the [Developer Certificate of Origin 1.1](https://developercertificate.org/).
Use a real name and a reachable address. There is no CLA and no copyright assignment:
contributions are licensed under the terms of the files they touch.

Keep commits focused. A formatting pass bundled with a semantic change cannot be
reviewed, and will be sent back.

## Review

Maintainers review best-effort; there is no service-level agreement. Reviewers check, in
order: does it contradict the specification; does it have a conformance case; does it
change behaviour that existing files rely on; is it implemented in the reference tool;
are the docs updated. A change that alters the format without a case and a docs update
is incomplete, not "later".

Security issues in the tooling should go through a private advisory on the repository
rather than a public issue.
