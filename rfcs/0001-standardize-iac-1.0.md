# RFC 0001 — Standardizing IAC 1.0

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-10-29
- **Supersedes:** `legacy/zh-specification-v1.0-draft.md` (v1.0-draft)

This is the only decision record for IAC 1.0. It folds in a second proposal that was
merged before publication: the `enabled` field was removed and replaced by the
`#!cut` marker, so a record has three required fields. Nothing here describes the
superseded four-field draft unless it says so.

## 1. Why the draft could not be published as-is

| # | Defect | Consequence |
|---|---|---|
| 1 | Fields split on every ` : `, but text may legally contain ` : ` | Any dialogue with a colon breaks the parser |
| 2 | `StopTime` has no stated inclusivity | Two implementations disagree by one centisecond on every cue |
| 3 | A fourth boolean field exists and is marked provisional | A required field with an undecided name cannot be versioned |
| 4 | No version marker | No way to add syntax without breaking old readers |
| 5 | No conformance definition or test vectors | Two parsers can both "implement the spec" and disagree |
| 6 | No licence, governance, changelog, or reference implementation | Studios and vendors cannot legally or procedurally depend on it |

## 2. Decisions

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, and MAY are RFC 2119 terms. Each
decision is expanded, with the alternatives that were rejected, in
[`spec/rationale.md`](../spec/rationale.md).

**D1 — The separator is quote-aware, not textual.** A record splits on ` : ` only
at brace depth 0, bracket depth 0, and outside a quoted string. A parser tokenizes;
it never splits the raw line. This is the defect that made the draft unsafe for
dialogue: `"Chapter : The Fall"` is ordinary text.

**D2 — Intervals are half-open, `[StartTime, StopTime)`.** Visible at the start,
not visible at the stop, and `StopTime` strictly greater than `StartTime`.
Touching cues compose: concatenating files cannot create a one-centisecond overlap.

**D3 — The fourth time component is centiseconds, never frames.** `HH:MM:SS:CC`
with `CC` in `00`–`99`. An importer converts with `cs = round(frames * 100 / fps)`.
A parser MUST NOT infer a frame rate.

**D4 — A record has three required fields and one optional field.** `AudioName`,
the subtitle set, and the colour are required; `Type` is optional. A line that is
kept for reference but never rendered is a `#!cut` comment carrying a record in
canonical form. It is a comment for parsing and rendering, and a linter still checks
its payload (W008).

**D5 — Colour is required; alpha is deferred.** `[#RRGGBB]`, six hex digits,
case-insensitive, stored as written. `#RRGGBBAA` is E013, not a silent truncation.

**D6 — `Type` is an optional value from an open, registered set.** `Voice`,
`Music`, `SFX`, `Narration`, `UI`; absent means `Voice`. Matching is
case-insensitive, a producer emits the canonical spelling, an unregistered value is
preserved and reported as W005, and a renderer falls back to default styling.

**D7 — An optional version marker exists.** `#!iac <MAJOR>.<MINOR>` as the first
line, after an optional BOM. It lives in the comment namespace, so a parser that
predates it ignores it. A newer major is E015; a newer minor is W007 and parsing
continues.

**D8 — Directives live in a reserved namespace.** Lines beginning `#@` carry
file-scoped metadata: `#@<name> <value>`. 1.0 defines one, `#@language`. Unknown
directives are ignored with W006.

**D9 — Exactly two escapes.** Inside text, `\"` encodes a quotation mark and
`\\` encodes a backslash. Any other backslash sequence is E003. Silently
preserving unknown escapes would make one file mean different things in different
tools.

**D10 — UTF-8, LF on output, all three terminators on input.** A producer MUST NOT
emit a BOM; a parser tolerates one leading BOM with W001. A NUL byte anywhere is
E001. A missing final newline is W003, not an error.

**D11 — Canonical form is deterministic.** One record per line, fields joined by
` : `, entries by `, `, entries sorted by start time, `Type` omitted when
`Voice`, UTF-8 without BOM, LF, final newline. Comments and directives are written
as they were read. Formatting a canonical file reproduces it byte for byte.

**D12 — Five limits every implementation must accept.** 8 MiB per file, 64 KiB per
line, 10 000 records, 4 096 code points per text, 256 code points per `AudioName`.
Exceeding one is E016. The entry count is bounded by the line limit.

**D13 — Rendering minimums.** Display exactly on the half-open interval, apply the
record colour, never alter text or timing, never render a `#!cut` line, display
overlapping entries rather than dropping one, and treat text as opaque data.

**D14 — Conformance is claimed per role.** Producer, Parser, Renderer.
[`testdata/conformance.json`](../testdata/conformance.json) is normative: it maps
each case file to the exact set of codes a parser must produce.

**D15 — The error taxonomy is stable and contiguous.** E001–E018 and W001–W008. A
parser reports the first failing stage of §8.2 and MUST NOT invent codes.

**D16 — Naming, licensing, stewardship, versioning.** "The IAC subtitle format" in
every user-facing title, because the acronym alone collides with
Infrastructure-as-Code. Spec text CC BY 4.0, reference code Apache-2.0, example
files CC0-1.0. Versions are `MAJOR.MINOR`; a 1.x parser reads any 1.y file with
`y <= x`. The interim media type is `text/x-iac`; the primary extension is
`.iac`, and `.txt` remains readable legacy.

## 3. Compatibility with the draft

| Draft behaviour | 1.0 behaviour | Existing files affected |
|---|---|---|
| Split on every ` : ` | Split only at top level | none (superset) |
| `StopTime` inclusive (implicit) | exclusive | none structurally; a renderer ends one centisecond earlier |
| Required boolean field | removed; `#!cut` marks a retired line | draft files migrate mechanically |
| Any `Type` string | registered set, unknown preserved | none |
| No version line | optional `#!iac` | none |
| `.txt` accepted | `.iac` for new tooling, `.txt` still read | legacy files still parse |

`examples/*.iac` are valid 1.0 without edits. `tools/iac_lint.py migrate` rewrites
draft-era records.

## 4. Rejected alternatives

**Keep the required boolean (the draft's `enabled` field).** No consumer needs it.
A renderer that must not display a cue cannot distinguish it from a cue that is
absent; localisation needs a workflow decision, not a per-line flag; build inclusion
is decided by which file is built. A required field that almost always holds `true`
is a tax on every line.

- **Rename it.** No new consumer; still a constant.
- **Make it a `status` enum** (`live` / `cut` / `alt` / `draft`). The closest
  call, but it keeps a required field most files set to one value. Per-line state
  belongs in a marker, a directive, or a sidecar.
- **Make it optional.** Ambiguous with `Type`: a trailing optional field must be
  unique in kind.
- **Reuse the slot as `duration`.** Duplicates data in the audio asset.

**Mark retired lines with a plain `#`.** A comment cannot be distinguished from
prose. The superseded draft's own examples contain
`# Format: Audio_name : {...} : [#Color]`, which auto-detection would flag on every
run.

**Use `#@cut`.** `#@` is file-scoped metadata. `#!cut` is line-scoped and sits
beside `#!iac` as "structured, not prose".

## 5. Compatibility impact

Nothing was published between the draft and 1.0.0, so this is the first public
grammar: no parser in the wild accepts the four-field form, and no file outside this
repository needs migration. The four corpus cases added with this revision pin the
behaviour that changed while the format was unpublished: W004 (tolerated whitespace),
E006 (a stray closing bracket in `AudioName`), E012 (an empty subtitle-set field),
and E001 (a NUL byte).
