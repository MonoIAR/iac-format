# AGENTS.md

Working notes for agents editing this repository.

## What this repository is

A published format standard, not an application. Three artefacts are normative and
move in lockstep: the specification (`spec/`), the conformance corpus (`testdata/`),
and the reference implementation (`tools/iac_lint.py`). `docs/` and `README*.md`
describe them and never define behaviour. `legacy/` is frozen history: read it,
never edit it.

## Changing the format

A change to record syntax, field semantics, an error code, or a conformance outcome
is a normative change and follows the RFC process in `GOVERNANCE.md`:

1. Write `rfcs/NNNN-short-title.md` from `rfcs/0000-template.md`, taking the next
   free number. Record the alternatives you rejected and why.
2. Update `spec/iac-1.0.md` and `spec/iac.abnf` together so prose and grammar agree.
   Update `registry/` when a Type value or directive changes.
3. Add or adjust cases in `testdata/` and their entries in `testdata/conformance.json`.
4. Change `tools/iac_lint.py` until the corpus is green.
5. Update the affected guides in `docs/`, both `README.md` and `README.zh-CN.md`, and
   `CHANGELOG.md`.
6. Run the gates below.

Done means all four gates exit 0.

## Gates

```
python -m unittest discover -s tools/tests -v
python tools/run_conformance.py
python tools/check_links.py
python tools/iac_lint.py validate examples
```

`run_conformance.py` is the authority on "conforms". When the corpus and the
implementation disagree, decide which one is wrong against the specification and fix
that one; a case is never weakened to make a parser pass.

## Conventions

- `spec/` is normative: RFC 2119 keywords, one checkable rule per statement. A rule
  the corpus cannot express belongs in `spec/appendix/rationale.md` as prose, not as
  a MUST.
- `docs/` summarises and links to `spec/`. Restating a normative rule in a guide
  creates drift; link to it instead.
- English everywhere except `README.zh-CN.md`, which mirrors `README.md` and changes
  in the same edit.
- UTF-8, LF, no BOM, final newline. `examples/*.iac` stay canonical:
  `iac_lint.py fmt --check` must pass on every one.
- Error codes are append-only. A retired code keeps its number and is documented as
  retired (E022 is retired); new behaviour takes a new number.
- A new CLI flag lands in `tools/iac_lint.py`, `README.md` and `docs/quickstart.md`
  in one change.
- `tools/` stays stdlib-only and runnable from a checkout with no install step. It is
  vendored into build pipelines, so a dependency is a regression.
- Claim only what exists. An unpublished package, media type or adopter stays
  "planned"; `ROADMAP.md` is where planned work lives.

## Pointers

- Deciding whether a change is additive or breaking: `rfcs/0001-standardize-iac-1.0.md`
  §4 and the versioning section of `GOVERNANCE.md`.
- Touching an error code: `spec/iac-1.0.md` §8, `docs/reference/errors.md`, and the
  matching case in `testdata/`.
- Writing or fixing a guide: `docs/index.md` is the map.
- Release or adoption work: `ROADMAP.md` and `docs/adoption.md`.
- The grammar itself, when prose and ABNF disagree: `spec/iac.abnf` wins for shape,
  `spec/iac-1.0.md` §3.5 wins for the quote-aware separator that ABNF cannot express.
