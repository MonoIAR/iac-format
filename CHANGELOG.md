# Changelog

Notable changes to the IAC subtitle format, its specification, and its reference tooling.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions
follow the policy in [GOVERNANCE.md](GOVERNANCE.md). A patch number identifies a
repository release of the same specification text, not a format change.

## [1.0.0] - 2026-10-29

The first stable release. It resolves the ambiguities of
[legacy/zh-specification-v1.0-draft.md](legacy/zh-specification-v1.0-draft.md) and makes
the format implementable by a second codebase.

### Added

- **Quote-aware field separator.** Records split on ` : ` only at brace depth 0, bracket
  depth 0, and outside quoted text, so dialogue may contain colons, commas, and braces.
- **Half-open intervals.** A cue is visible on `[StartTime, StopTime)`, which makes
  touching lyric cues correct and cue arithmetic composable.
- **`#!iac MAJOR.MINOR` version marker.** A newer major is E015; a newer minor is W007.
- **`#@` directive namespace** with `#@language` as the only 1.0 directive; unknown
  directives are ignored with W006.
- **Registered `Type` values** — `Voice`, `Music`, `SFX`, `Narration`, `UI` — with
  `Voice` as the default and unregistered values preserved.
- **Deterministic canonical form** and a formatter that enforces it.
- **Implementation limits** every conforming implementation must accept: 8 MiB per file,
  64 KiB per line, 10 000 records, 4 096 code points per text, 256 per `AudioName`.
- **Minimal rendering semantics** and conformance by role (Producer, Parser, Renderer).
- **A conformance corpus** in [testdata/](testdata/) whose outcomes are normative.
- **A contiguous error taxonomy**: E001–E018 and W001–W008.
- **Retired records** — `#!cut ` plus a record in canonical form, checked by a linter and
  reported as W008 when its payload no longer parses.
- **Reference tooling**: `validate`, `fmt`, `from-srt`, `migrate`, one stdlib-only file.
- **Governance, licensing, and a changelog.**

### Changed from the draft

- The record lost its boolean field. Three fields are required and `Type` is optional,
  moving from field 5 to field 4.
- `StopTime` is explicitly exclusive.
- `Type` is a registered, case-insensitive set instead of a free-form string.
- The separator is tokenized rather than split textually.
- The fourth time component is stated as centiseconds and explicitly not frames.
- Escapes are exactly `\"` and `\\`; anything else is E003.
- Encoding and line endings are specified: UTF-8, no BOM from producers, CRLF and CR
  accepted on read, LF on write.
- `Color` stays required, and eight-digit colour is rejected rather than truncated.
- `.iac` is the only extension new tooling may produce; `.txt` remains readable legacy.

### Fixed

- Two implementations could disagree by one centisecond on every cue, because the
  interval convention was unstated.
- `HH:MM:SS:CC` was shaped like SMPTE timecode; the unit is now normative and the frame
  reading is forbidden.
- There was no way to tell what version a file was written against.
- Tooling had no shared definition of "invalid".
- Studios could not legally depend on the format.
