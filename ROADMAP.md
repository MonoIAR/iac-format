# Roadmap

Status legend: **done** · **next** · **planned** · **exploring**

## v1.0.0 — 2026-10-29 (done)

- Normative specification `spec/iac-1.0.md` and grammar `spec/iac.abnf`.
- Error taxonomy E001–E027 / W001–W007 shared by all tooling.
- Reference parser, validator, formatter and SRT importer: `tools/iac_lint.py`.
- Conformance suite: `testdata/` + `tools/run_conformance.py`.
- Registry for track types and directives.
- Governance, contribution process, changelog, licensing.

## v1.0.1 — hygiene, no format change (next)

These are the things that block a credible public announcement. None of them
change the format.

- Vendor the full legal texts of CC BY 4.0, Apache-2.0 and CC0-1.0.
- Publish the reference implementation as `pip install iac-subtitle` and
  `npm i iac-subtitle` (single code path, two thin wrappers).
- TextMate grammar + VS Code extension: syntax highlighting, snippet for a
  record, lint-on-save using the reference parser.
- CI: unit tests + conformance suite on Linux, macOS and Windows.
- Chinese translation of the normative specification, pinned to 1.0.x.
- `iac.schema.json` — JSON Schema for the parsed object model, for tools that
  want to consume IAC through a JSON boundary.

## v1.1 — additive (planned)

Every item must keep 1.0 files valid.

- `#@offset ±HH:MM:SS:CC` for global sync adjustment.
- Speaker identity separate from `AudioName`.
- Multi-language sidecar convention (`<track>.<bcp47>.iac`).
- Registered type: `Whisper`, `Radio`, `System`.

Anything that changes record or entry syntax cannot go here: a 1.0 parser would
reject it, which breaks the promise that any 1.x parser reads any 1.y file. Those
items are in v2.0.

## Adoption milestones (planned)

- First third-party parser (not maintained by the IAC steward).
- Localisation vendor support: a documented custom-format regex for Crowdin
  and Transifex, plus a converter CLI that round-trips through XLIFF 1.2.
- Media type registration: `text/vnd.iac` with IANA, plus a
  `shared-mime-info` entry so `.iac` files open correctly on the desktop.
- One published case study from a shipping game, including the migration diff
  from its previous format.

## v2.0 — exploring, no commitments

Only if 1.x adoption produces real pressure:

- `#RRGGBBAA` alpha in the colour field.
- Per-entry colour override.
- Inline styling spans.
- Escaping or quoting model beyond the two escapes.
- Binary packaging for very large cue sheets.

## Explicitly out of scope

- Karaoke timing (word-level). Use ASS or a dedicated format.
- Fonts, positioning, animation. IAC describes *what is said and when*, not
  *how it looks*.
- Anything executable: no paths, no URLs, no code, no includes.
