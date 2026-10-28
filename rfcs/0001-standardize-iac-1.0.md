# RFC 0001 — Standardizing IAC 1.0

- **Status:** Accepted
- **Version:** 1.0
- **Date:** 2026-10-29
- **Superseded by:** RFC 0002 (D4, and the `enabled` references in D11, D13, D15 and §6)
- **Supersedes:** `legacy/zh-specification-v1.0-draft.md` (draft, v1.0-draft)

## Abstract

The existing draft describes IAC well enough for one codebase, but not well enough
to be adopted by a second one. This RFC records the decisions required to publish
IAC 1.0 as a stable, implementable, testable specification. Everything in
`spec/`, `docs/`, `tools/`, and `testdata/` follows from the decisions below.

Every decision is either **backward compatible** with existing `.iac` files or is
an **erratum** that resolves an ambiguity the draft left open. No existing file in
`examples/` changes meaning.

## 1. Why the draft cannot be promoted as-is

| # | Defect | Consequence |
|---|--------|-------------|
| 1 | Field split is "split on ` : `", and text may legally contain ` : ` | Any subtitle line with a colon breaks the parser; the draft "fixes" this by forbidding the sequence inside fields, which is an unenforceable constraint on *content* |
| 2 | No definition of whether `StopTime` is inclusive | Two implementations disagree by one centisecond on every cue |
| 3 | `Enabled` is marked "暂定" (TBD) | A required field with an undecided name cannot be versioned |
| 4 | No version marker in the file | No forward-compatible way to evolve the format |
| 5 | No conformance definition, no test vectors | Two parsers can both "implement the spec" and disagree |
| 6 | No license, no governance, no changelog | Studios and vendors cannot legally or procedurally depend on it |
| 7 | No reference implementation | Adoption cost is "write a parser first", which is where formats die |
| 8 | Precision is called "百分秒" in a field that looks like SMPTE `HH:MM:SS:FF` | Every new reader misreads it as frames |
| 9 | No error taxonomy | Tooling cannot agree on what "invalid" means |

## 2. Decisions

The key words MUST, MUST NOT, SHOULD, SHOULD NOT, MAY are to be interpreted as
described in RFC 2119.

### D1 — The separator is quote-aware, not textual

**Decision.** A record is split on the sequence ` : ` only where it occurs at
**brace depth 0, bracket depth 0, and outside a quoted string**. A conforming
parser MUST tokenize; it MUST NOT use a plain string split.

**Rationale.** This is the single defect that makes the format unsafe for real
dialogue. `"他说 : 你好"` and `"Chapter : The Fall"` are valid subtitle text.
Tokenizing keeps every existing file valid while making the grammar total.

**Normative consequences.**
- `AudioName` MUST NOT contain ` : `, `"`, `{`, `}`, `[`, or `]`.
- `AudioName` MUST NOT be empty and MUST NOT begin with `#`.
- Text inside `"` MAY contain any Unicode scalar value except an unescaped `"`
  and the control characters forbidden by D12.

### D2 — Intervals are half-open: `[StartTime, StopTime)`

**Decision.** An entry is visible from `StartTime` **inclusive** to `StopTime`
**exclusive**. `StopTime` MUST be strictly greater than `StartTime`.

**Rationale.** `examples/music.iac` chains cues with touching boundaries
(`00:00:17:20` → `00:00:17:20`). That only works if the stop is exclusive. It
also makes cue arithmetic composable (concatenating two files cannot create a
one-centisecond overlap).

### D3 — The time unit is a centisecond, never a frame

**Decision.** The fourth component is `CC` = centiseconds (1/100 s), range
`00`–`99`, exactly two digits. It is not a frame number and not tied to any
frame rate. The field is written `HH:MM:SS:CC` with `HH` in `00`–`99`.

**Rationale.** `HH:MM:SS:FF` is SMPTE timecode and means frames. Reusing the
shape without the meaning is the most likely source of silent sync bugs.
Implementations MUST NOT infer a frame rate.

**Conversion.** Converting from frame-based sources: `cs = round(frames * 100 / fps)`,
then clamp so `StopTime > StartTime`.

### D4 — `Enabled` becomes `enabled` and is normative

**Decision.** The fourth field is named `enabled`, is required, and accepts
exactly `true` or `false` (lowercase). The "暂定" marker is removed.

**Rationale.** The draft already relies on it (`false` = deleted-but-retained
line), which is a real production workflow. Leaving the name provisional makes
the field impossible to stabilise.

**Consequences.** `enabled = false` means "present in the file, never rendered".
Parsers MUST preserve such records; renderers MUST NOT display them. A lenient
parser MAY additionally accept `True`/`False` and MUST warn (W004).

### D5 — `Color` stays required in 1.0; alpha is deferred

**Decision.** Field 3 is `[#RRGGBB]`, six hex digits, case-insensitive. The
value is stored as written, compared case-insensitively. 8-digit
`#RRGGBBAA` is **not** valid in 1.0 and parsers MUST reject it (E021).

**Rationale.** Rejecting loudly is better than silently dropping alpha and
producing wrong colours. Alpha cannot ship in a minor release (see §4.2).

### D6 — `Type` is an optional registered value, default `Voice`

**Decision.** Field 5 is optional. Absent ⇒ `Voice`. Canonical spellings:
`Voice`, `Music`, `SFX`, `Narration`, `UI`. Values are registered in
`registry/types.md`. Matching is case-insensitive; serializers MUST emit the
canonical spelling. Unknown values MUST be preserved and MUST NOT be treated as
an error by a parser (linters SHOULD warn, W005); a renderer MUST fall back to
default styling.

**Rationale.** An open-but-registered set lets a studio extend the format
without forking it, and keeps `Voice` as the implicit common case.

### D7 — A version marker exists and is forward compatible

**Decision.** A file MAY begin with the magic comment `#!iac <MAJOR>.<MINOR>`
as its first line (after an optional BOM). Because it is a comment, 1.0-draft
parsers ignore it. Parsers MUST read it when present; if `MAJOR` exceeds the
supported major, the parser MUST fail with E024.

**Rationale.** Without this there is no way to add syntax without breaking old
readers. Placing it in the comment namespace costs nothing today.

### D8 — Directives live in a reserved namespace

**Decision.** Lines beginning with `#@` are directives: `#@` `name` SP `value`.
1.0 defines exactly one: `#@language <BCP-47>` (file-scoped, informational).
Unknown directives MUST be ignored with a warning (W006). `#@` is reserved;
`#` alone remains a plain comment.

**Rationale.** Localisation and sync offset are the next two things every studio
will ask for. Reserving the namespace now prevents a syntax change later.

### D9 — Escapes: exactly two

**Decision.** Inside text, `\"` encodes `"` and `\\` encodes `\`. Any other
backslash sequence is invalid (E011). A bare `\` followed by anything else MUST
be rejected rather than silently preserved.

**Rationale.** "Silently preserve unknown escapes" produces files that mean
different things in different tools. Two escapes are enough for subtitles.

### D10 — Encoding and line endings

**Decision.**
- Files MUST be UTF-8. Producers MUST NOT emit a BOM; parsers MUST tolerate one
  leading BOM.
- Parsers MUST accept LF, CRLF, and CR line endings. Serializers MUST emit LF.
- Files SHOULD end with a newline.
- A `NUL` byte anywhere is invalid (E001).

**Rationale.** Windows-authored subtitle files are CRLF. Refusing them is a
self-inflicted adoption barrier.

### D11 — Deterministic canonical form

**Decision.** Serializers MUST emit:
- one record per line, fields joined by exactly ` : `;
- exactly one space after each entry separator `, `;
- no leading or trailing whitespace on a line;
- entries within a record sorted by `StartTime`, non-decreasing;
- `Type` omitted when it is `Voice`.

Records MAY appear in any order. A file with two records having the same
`AudioName` is invalid (E015).

**Rationale.** Canonical form is what makes golden tests, reviewable diffs, and
`iac fmt` possible. Non-decreasing cue order also allows streaming renderers.

### D12 — Limits every implementation must support

| Quantity | Minimum a conforming implementation MUST accept |
|---|---|
| File size | 8 MiB |
| Line length | 64 KiB |
| Records per file | 10 000 |
| Entries per record | 4 096 |
| Code points per text | 4 096 |
| Code points per `AudioName` | 256 |

Control characters other than none at all: `U+0000`–`U+0008`, `U+000B`,
`U+000C`, `U+000E`–`U+001F`, `U+007F` MUST NOT appear in text (E026).
A tab MAY appear in text. Exceeding a limit is E025 in strict mode.

**Rationale.** "Unbounded" is not implementable. These numbers are far above any
real subtitle file and let a parser size its buffers.

### D13 — Minimal rendering semantics

**Decision.** A renderer:
1. MUST NOT display entries whose record has `enabled = false`.
2. MUST display an entry exactly on `[StartTime, StopTime)`.
3. MUST apply the record's colour to all of its entries.
4. MAY style by `Type`; MUST NOT change timing or text.
5. MUST NOT merge, trim, or re-wrap text in a way that changes its code points.

Overlapping entries within one record are allowed; the renderer MUST display all
of them (stacking is implementation-defined). Linters SHOULD warn (W002).

### D14 — Conformance is defined by role

**Decision.** Three roles: **Producer** (writes files), **Parser** (reads),
**Renderer** (displays). A tool claims conformance per role, and passes the
suite in `testdata/`. `testdata/conformance.json` is normative: it maps each
case file to expected outcome and error codes.

### D15 — Error taxonomy

Codes are stable and shared by the spec, the linter, and every future tool.

| Code | Severity | Meaning |
|---|---|---|
| E001 | error | Not valid UTF-8, contains NUL, or has a BOM in producer mode |
| E010 | error | Unterminated quoted string |
| E011 | error | Invalid escape sequence |
| E012 | error | Wrong number of fields (expected 4 or 5) |
| E013 | error | Empty `AudioName` |
| E014 | error | Illegal character in `AudioName` |
| E015 | error | Duplicate `AudioName` |
| E016 | error | Malformed time (`HH:MM:SS:CC`) |
| E017 | error | Time component out of range |
| E018 | error | `StopTime <= StartTime` |
| E019 | error | Entries not in non-decreasing `StartTime` order |
| E020 | error | Empty subtitle set `{}` |
| E021 | error | Malformed or unsupported colour |
| E022 | error | `enabled` is not `true` / `false` |
| E023 | error | Malformed `Type` token |
| E024 | error | Unsupported major version |
| E025 | error | A D12 limit exceeded |
| E026 | error | Forbidden control character in text |
| E027 | error | Trailing content after the last field |
| W001 | warning | BOM present |
| W002 | warning | Overlapping entries within a record |
| W003 | warning | Missing trailing newline |
| W004 | warning | Non-canonical casing/whitespace accepted |
| W005 | warning | Unregistered `Type` value |
| W006 | warning | Unknown or duplicate directive |
| W007 | warning | File declares a newer minor version |

**Exit codes for CLI tools:** `0` clean, `1` warnings only, `2` errors.

### D16 — Naming, licensing, stewardship

**Decision.**
- Spec text: **CC BY 4.0**. Reference code: **Apache-2.0**. Example `.iac`
  files: **CC0-1.0**, so studios can paste them into proprietary projects.
- The format is "the IAC subtitle format". The acronym alone collides with
  Infrastructure-as-Code in every search engine, so every user-facing title
  carries "subtitle".
- Steward: a named organisation in `GOVERNANCE.md`. Changes go through `rfcs/`.
- Versioning: `MAJOR.MINOR` for the spec; any 1.x parser MUST read any 1.y file
  with `y <= x`. Breaking changes require a major bump and a deprecation cycle
  of at least one minor release.
- Media type: `text/x-iac` (interim, unregistered). Registration template lives
  in `spec/appendix/media-type.md`. Primary extension `.iac`; `.txt` is legacy
  and MUST NOT be produced by new tooling.

## 3. Backward compatibility with the draft

| Draft behaviour | 1.0 behaviour | Existing files affected |
|---|---|---|
| Split on every ` : ` | Split only at top level | none (superset) |
| `StopTime` inclusive (implicit) | exclusive | none structurally; a renderer that had it inclusive now ends one centisecond earlier |
| `Enabled` name provisional | `enabled`, normative | none |
| Any `Type` string | registered set, unknown preserved | none |
| `HH:MM:SS:CC` | same, now explicit | none |
| No version line | optional `#!iac` | none |
| `.txt` accepted | `.iac` only for new tooling | legacy files still parse |

`examples/*.iac` are valid 1.0 without edits.

## 4. Deferred work

Two buckets, because the compatibility promise in D16 decides which is possible.

### 4.1 Additive — possible in 1.1

These can be added without breaking a 1.0 parser, because a 1.0 parser either
ignores them (directives) or preserves them (registry values):

- `#@offset ±HH:MM:SS:CC` for a file-scoped sync adjustment.
- Speaker identity separate from `AudioName`, carried as a directive.
- A multi-language sidecar convention (`<track>.<bcp47>.iac`).
- New registered `Type` values.

### 4.2 Breaking — requires 2.0

These change record or entry syntax, so a 1.0 parser rejects them with an E-code.
A minor version cannot introduce them without breaking the promise that any 1.x
parser reads any 1.y file with `y <= x`.

- `#RRGGBBAA` alpha in the colour field (a 1.0 parser answers E021).
- Per-entry colour override.
- Inline styling spans.

Each item gets its own RFC. An RFC that wants a breaking item in a minor release
must propose an encoding a 1.0 parser can ignore or preserve; otherwise it is a
major-version change. This is why "alpha is a 1.1 candidate" was wrong: the
label does not survive the compatibility promise.

## 5. Follow-up work created by this RFC

1. `spec/iac-1.0.md` + `spec/iac.abnf` — normative text and grammar.
2. `testdata/` — valid/invalid corpus and `conformance.json`.
3. `tools/iac_lint.py` — reference parser, validator, formatter, SRT importer.
4. `docs/` — quickstart, authoring guide, parser guide, conversion guide, FAQ.
5. `GOVERNANCE.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `LICENSE*`.
6. `registry/` — `types.md`, `directives.md`.
7. `rfcs/0000-template.md` — the change process this document itself followed.

## 6. Clarifications resolved during implementation

Writing the spec and the reference parser together exposed decisions this RFC left
implicit. They are normative in `spec/iac-1.0.md`; they are recorded here so the
decision record stays complete and a future editor knows why the text is so
specific.

| # | Question | Resolution | Spec |
|---|---|---|---|
| 1 | In what order are diagnostics reported? | Fixed stage order: E001 → E024 → E010 → E012 → field 1 → E020 → entry codes → E021 → E022/E023 → E027 → E015 → E025. One invalid input yields one deterministic primary code. | §8.2 |
| 2 | A quote is open at end of line *and* the record is unbalanced. Which code? | E010. An unescaped quote open at EOL is lexical and pre-empts field counting. A closed quote with an unmatched opening `{` or `[` is E012. A closer never makes depth negative. | §3.5, §8.2 |
| 3 | What exactly is a Type token? | `ALPHA *(ALPHA / DIGIT / "-" / "_")`. A non-token is E023; a well-formed but unregistered token is preserved with W005. | §4.4, §5.5 |
| 4 | Where is the E027 boundary? | A complete final value followed by whitespace and content is E027 (`true junk`, `Music extra`). A wholly wrong value is E022 or E023 (`yes`, `!Music`). Six or more fields is E012, not E027. | §4.4, §8.2 |
| 5 | Which code for a malformed time region? | E016 for a missing or malformed `HH:MM:SS:CC` region; text failures keep E010/E011/E026. Without this rule E016 was unreachable, because a strict entry pattern rejects the malformed time before `parse_time` can classify it. | §4.3 |
| 6 | BOM: E001 or W001? | A parser reading a BOM reports W001. E001 covers a producer-mode BOM, invalid UTF-8, and NUL. | §2.1 |
| 7 | D11 phrases entry sorting as an output rule, but the code table lists E019. | Descending `StartTime` is an error, not just a formatting defect. Equal adjacent starts are allowed and produce W002. | §4.3, §8.2 |
| 8 | Are the D12 limits hard errors? | Only in strict mode. A default parser MAY accept more or reject with E025, but MUST NOT reject a file within the minimum. | §9 |
| 9 | Version-marker edge cases. | A malformed `#!iac` on line 1 is an ordinary comment with no diagnostic. A marker after line 1 is ignored; linters SHOULD report W006. A declared major below the supported major is unspecified and not tested. | §3.3 |
| 10 | Are limits counted in bytes or code points? | File size and line length in bytes (line excluding terminator); text and `AudioName` lengths in code points, text counted after escape processing. | §9 |
| 11 | How tolerant is the entry separator? | Canonical is COMMA SP. Parsers MUST accept COMMA with zero or more SP/TAB and report W004 unless exactly one SPACE follows. | §3.6, §4.3 |
| 12 | Is duplicate detection case-sensitive? | Yes, exact: `VO_1` and `vo_1` are distinct. | §5.1 |
| 13 | Is a file with no records valid? | Syntactically valid; parsers MUST accept, producers SHOULD NOT emit. | §2.3 |
| 14 | What does W004 cover? | Non-canonical whitespace padding around any field or entry separator, and non-canonical `enabled`/`Type` casing accepted by a lenient parser. | §3.6, §5.4 |

One rule is deliberately left to implementers: an unescaped quote *inside* an
otherwise balanced entry. Any such input unbalances the record, so it lands on
E010 and never reaches the entry parser.
