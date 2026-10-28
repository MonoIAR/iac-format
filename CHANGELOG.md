# Changelog

All notable changes to the IAC subtitle format, its specification, and its reference tooling are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Versions follow the `MAJOR.MINOR` policy in [GOVERNANCE.md](GOVERNANCE.md); a patch number identifies a repository release of the same spec text, not a format change.

## [Unreleased]

### Planned

Not commitments — each needs an RFC, and each is listed in [RFC 0001 §4](rfcs/0001-standardize-iac-1.0.md#4-deferred-work).

Additive, possible in 1.1:

- `#@offset` for a file-scoped sync adjustment.
- Speaker identity separate from `AudioName`.
- A multi-language sidecar convention.
- New registered `Type` values.

Breaking, requires 2.0 — a 1.0 parser rejects these, so a minor cannot carry them:

- Per-entry colour override.
- `#RRGGBBAA` alpha in the colour field.
- Inline styling spans.

## [1.0.0] - 2026-10-29

The first stable release. It resolves the ambiguities of `legacy/zh-specification-v1.0-draft.md` (v1.0-draft) and makes the format implementable by a second codebase. Nothing was published between the draft and this release, so the record grammar was still free to change: the `enabled` field was removed before the public announcement (RFC 0002), and draft-era files migrate mechanically with `tools/iac_lint.py migrate`.

### Added

- **Quote-aware field separator.** Records are split on ` : ` only at brace depth 0, bracket depth 0, and outside a quoted string; text may contain ` : `, `{}`, `[]`, and commas freely (RFC 0001 §D1).
- **Half-open intervals.** A cue is visible on `[StartTime, StopTime)`, and `StopTime` must be strictly greater than `StartTime` (D2). This is what makes touching lyric cues in `examples/music.iac` correct.
- **`#!iac MAJOR.MINOR` version marker**, optional, first line after an optional BOM; a newer major is E024, a newer minor is W007 (D7).
- **`#@` directive namespace**, reserved; `#@language <BCP-47>` is the only directive in 1.0, and unknown directives are ignored with W006 (D8).
- **Registered `Type` values** — `Voice`, `Music`, `SFX`, `Narration`, `UI` — with `Voice` as the default and unknown values preserved (D6).
- **Deterministic canonical form**: one record per line, ` : ` between fields, `, ` between cues, sorted cues, `Type` omitted when `Voice`, LF endings, final newline (D11).
- **Implementation limits** every conforming implementation must accept: 8 MiB file, 64 KiB line, 10 000 records, 4 096 entries per record, 4 096 code points per text, 256 code points per `AudioName` (D12).
- **Minimal rendering semantics**: display exactly on the interval, apply the record colour, styling may follow `Type` but never change timing or text (D13).
- **Conformance by role** — Producer, Parser, Renderer — with a normative corpus in `testdata/` and `conformance.json` mapping each case to its expected outcome (D14).
- **Stable error taxonomy** E001 and E010–E027 with E022 retired, warnings W001–W008, and CLI exit codes `0` clean, `1` warnings, `2` errors (D15, RFC 0002 §3).
- **Retired lines** — `#!cut ` plus a record in canonical form: a comment the linter still parses, reporting W008 when the payload is no longer valid, and exempt from the duplicate-name check (RFC 0002 §D4″).
- **Reference implementation** `tools/iac_lint.py`: `validate`, `fmt`, `from-srt`, and `migrate`.
- **Media type and extension**: `text/x-iac` is the interim media type with a registration package in `spec/appendix/media-type.md`, `text/vnd.iac` is the intended registered name, `.iac` is the primary extension, and `.txt` is legacy read-only (D16).
- **Licensing and stewardship**: spec text CC BY 4.0, reference code Apache-2.0, example files CC0-1.0; normative changes go through `rfcs/` (D16).
- **Project documents**: this changelog, `GOVERNANCE.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and the RFC template.

### Changed

- **The record lost its boolean field.** Three required fields — `AudioName`, cue set, colour — plus an optional `Type`, which moved from field 5 to field 4. A line that must not render is a `#!cut` comment now, not a `: false` flag in the record (RFC 0002).
- **`StopTime` is explicitly exclusive.** Structurally nothing changes, but a renderer that had treated the stop as inclusive now ends one centisecond earlier (D2).
- **`Type` is a registered, case-insensitive set** with canonical spellings, replacing the draft's "custom string" (D6).
- **The separator is tokenized, not textual.** Files the draft accepted still parse; the difference appears only on dialogue that contains ` : ` (D1).
- **The time unit is stated as centiseconds** and explicitly not frames, with a conversion formula for frame-based sources: `cs = round-half-up(frames * 100 / fps)`, clamped so the stop exceeds the start (D3).
- **Escapes are exactly two** — `\"` and `\\` — and every other backslash sequence is an error rather than silently preserved (D9).
- **Encoding and line endings are specified**: UTF-8, no BOM from producers, CRLF and CR accepted on read, LF on write, final newline expected (D10).
- **`Color` stays required**, and 8-digit `#RRGGBBAA` is invalid (E021); alpha was deferred rather than silently dropped (D5).
- **`.iac` is the only extension new tooling may produce**; `.txt` remains readable legacy (D16).
- **The specification text now lives in `spec/iac-1.0.md`** — English, RFC 2119 keywords, with a normative ABNF grammar in `spec/iac.abnf`; the Chinese draft is superseded.

### Removed

- **The requirement that ` : ` must not appear in field content.** It was unenforceable, and quote-aware splitting makes it unnecessary (D1).
- **The `enabled` field**, removed before the public announcement. A record carries what is said and when; whether a line renders is not a property of the line, and a required boolean that is almost always `true` was a tax on every record. The draft's provisional fourth field was stabilised by RFC 0001 D4 and then removed outright by RFC 0002; retired lines are `#!cut` comments and keep being checked.

### Fixed

- Two implementations could previously disagree by one centisecond on every cue, because the interval convention was unstated (D2).
- `HH:MM:SS:CC` was called "百分秒" in a field shaped like SMPTE `HH:MM:SS:FF`; the unit is now normative and the frame reading is explicitly forbidden (D3).
- There was no way to tell what a file was written against; the version marker provides one (D7).
- Tooling had no shared definition of "invalid"; the error taxonomy provides one (D15).
- Studios could not legally depend on the format; the licence grants and governance now exist (D16).
