# AGENTS.md

Working notes for agents editing this repository.

## What this repository is

A published format standard, not an application. Four layers, each with one job:

| Layer | Path | Holds |
|---|---|---|
| Normative | `spec/` | The specification, the ABNF grammar, the registry, and the two informative pages (rationale, security) |
| Contract | `testdata/`, `tools/` | The conformance corpus and the reference implementation that proves it |
| Explanation | `docs/`, `README*.md` | Guides for writers, parser implementers, converters, and people debugging a code |
| Decision | `rfcs/` | Why the format looks like this; never a description of the current format |

`legacy/` is frozen history: read it, never edit it.

## Changing the format

A change to record syntax, field semantics, an error code, or a conformance outcome is
normative and follows the RFC process in `GOVERNANCE.md`:

1. Write `rfcs/NNNN-short-title.md` from `rfcs/0000-template.md`, taking the next free
   number. Record the alternatives you rejected and why.
2. Update `spec/iac-1.0.md` and `spec/iac.abnf` together so prose and grammar agree.
   Update `spec/registry.md` when a `Type` value or directive changes.
3. Add or adjust cases in `testdata/` and their entries in `testdata/conformance.json`.
4. Change `tools/iac_lint.py` until the corpus is green.
5. Update the affected guides in `docs/`, both `README.md` and `README.zh-CN.md`, and
   `CHANGELOG.md`.
6. Run the gates below.

## Gates

Done means all five exit 0:

```bash
python -m unittest discover -s tools/tests -v
python tools/run_conformance.py
python tools/check_links.py
python tools/iac_lint.py validate examples
python tools/iac_lint.py fmt --check examples
```

`run_conformance.py` is the authority on "conforms". When the corpus and the
implementation disagree, decide which one is wrong against the specification and fix
that one; a case is never weakened to make a parser pass. `check_links.py` also fails on
a diagnostic code that the specification does not define.

## Conventions

- `spec/` is normative: RFC 2119 keywords, one checkable rule per statement. A rule the
  corpus cannot express belongs in `spec/rationale.md` as prose, not as a MUST.
- `docs/` summarises and links to `spec/`. Restating a normative rule in a guide creates
  drift; link to it instead.
- English everywhere except `README.zh-CN.md`, which mirrors `README.md` and changes in
  the same edit. British spelling otherwise (`colour`, `behaviour`).
- UTF-8, LF, no BOM, final newline. `examples/*.iac` and `testdata/valid/*.iac` (except
  the cases that deliberately test BOM, CRLF, or a missing final newline) stay canonical.
- Error codes are append-only and contiguous: E001–E018 and W001–W008 in 1.0. A new
  diagnostic takes the next number; a number is never reused.
- A new CLI flag lands in `tools/iac_lint.py`, `README.md`, and `docs/quickstart.md` in
  one change.
- `tools/` stays stdlib-only and runnable from a checkout with no install step. It is
  vendored into build pipelines, so a dependency is a regression.
- Claim only what exists. There is no published package, no registered media type, and
  no third-party implementation to point at.

## Pointers

- Deciding whether a change is additive or breaking: `rfcs/0001-standardize-iac-1.0.md`
  and the versioning section of `GOVERNANCE.md`.
- Touching an error code: `spec/iac-1.0.md` section 8, `docs/errors.md`, and the matching case
  in `testdata/`.
- Writing or fixing a guide: the "Where things live" table in `README.md`.
- The grammar itself, when prose and ABNF disagree: `spec/iac.abnf` wins for shape,
  `spec/iac-1.0.md` section 3.5 wins for the quote-aware separator that ABNF cannot express.
