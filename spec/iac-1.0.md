# IAC 1.0 — Subtitle Format Specification

- **Status:** Stable
- **Version:** 1.0
- **Date:** 2026-10-29
- **Supersedes:** `legacy/zh-specification-v1.0-draft.md` (v1.0-draft)
- **License:** CC BY 4.0

IAC (Inline Annotation Container) is a plain-text subtitle format for timed text
authored next to an audio asset. A file associates an **AudioName** with a set of timed
subtitle **entries**, a display colour, and an optional track **Type**. A line kept for
reference but never rendered is a retired record (§5.4). The key words MUST, MUST NOT,
SHOULD, SHOULD NOT, and MAY are to be interpreted as described in RFC 2119.

## 0. How to read this specification

This document is normative. Three things sit beside it: [`spec/iac.abnf`](iac.abnf)
gives the shape of a record, [`spec/registry.md`](registry.md) lists the registered
values, and [`testdata/conformance.json`](../testdata/conformance.json) defines what a
conforming parser must produce.

| If you want to know | Read |
|---|---|
| what a line looks like | §3.5, then §4.1 |
| what each field means | §5 |
| how time works | §6 |
| what a writer must emit | §7 |
| what a tool must report | §8 |
| how much an implementation must accept | §9 |
| what a player must display | §10 |
| how versions work | §11 |
| how a transport labels a file | §12 |
| what an implementation must assume about input | §13 |
| why a rule exists | [`spec/rationale.md`](rationale.md) |

Sections 1–13 are normative; §14–§15 are references, and `spec/rationale.md` and
`spec/security.md` are informative. "Parser" means a reader, "Producer" a writer, "Renderer" a displayer
(§1.2). Where this text and `spec/iac.abnf` disagree about the shape of a line, the
grammar wins. Where they disagree about where a field ends, §3.5 wins: ABNF cannot
express a quote-aware separator.

## 1. Introduction and scope

IAC is a source format: written and reviewed by hand, stored in version control, and
compiled into an application build. The parser is small; the file is readable in a diff.

### 1.1 This is not a general subtitle format

IAC 1.0 deliberately excludes the following; none is expressible, and a tool that needs
any of them MUST use a general subtitle or container format instead:

- Broadcast and accessibility captioning: no positioning, regions, fonts, styling
  spans, karaoke timing, speaker identity, or reading-speed metadata.
- Per-entry colour and alpha transparency. Colour is a record property (§5.3);
  `#RRGGBBAA` is invalid in 1.0.
- Attachments, images, fonts, embedded metadata, or a binary container.
- External references: no file paths, no URLs, nothing to resolve (§13).
- Lossless interchange with SRT, WebVTT, or ASS; converting into IAC is a Producer
  concern, not part of this format.

### 1.2 Conformance roles

Conformance is claimed per role. A product that both reads and writes claims both.

| Role | Definition | Requirements |
|---|---|---|
| **Producer** | Writes IAC files. | §2, §4, §5, §7, §9, and every MUST on output. Output MUST NOT contain any E-code and MUST be canonical (§7). |
| **Parser** | Reads IAC files and reports diagnostics. | §2–§6, §8, §9, §11. It MUST accept every file §9 requires, MUST report the diagnostics of §8, and MUST NOT accept a file that has an E-code. |
| **Renderer** | Displays parsed entries. | §10. It MUST NOT display retired records, MUST honour half-open intervals, and MUST NOT alter text or timing. |

`testdata/conformance.json` is normative. Each case names a file and the exact set of
codes a Parser must produce; `expect` is `ok`, `warning` (warnings only), or `error` (an
E-code). A Parser claiming conformance MUST pass every case, comparing code sets without
regard to order. Producer conformance additionally requires canonical output (§7) for
every valid case. Renderer conformance requires an independent test of §10.

### 1.3 Terminology

| Term | Meaning |
|---|---|
| **code point** | A Unicode scalar value, U+0000–U+D7FF or U+E000–U+10FFFF. Lengths in §9 are counted in code points. |
| **record** | One AudioName, one subtitle set, one colour, optional Type. One record per line. |
| **retired record** | A `#!cut ` comment carrying a record for reference; not a record (§5.4). |
| **field** | One of the 3 or 4 values of a record, separated by ` : ` (§3.5). |
| **entry** | One quoted-text-plus-interval item inside a subtitle set. |
| **text** | The quoted content of an entry, after escape processing. |
| **centisecond (cs)** | 1/100 second; the fourth time component (§6). |
| **depth 0** | No `{` or `[` unmatched and no quoted string open (§3.5). |

`E0xx` and `W0xx` refer to §8. "Reject" means report an E-code and do not present the
file as conforming; a Parser MAY return a partial result marked invalid.

## 2. Encoding and line structure

### 2.1 Character encoding

- A file MUST be UTF-8 (RFC 3629); UTF-16, UTF-32, and legacy encodings are invalid.
- A Producer MUST NOT emit a byte order mark. A Parser MUST tolerate exactly one BOM
  (`EF BB BF`, U+FEFF) at the start of the file, MUST ignore it, and MUST report W001.
- A BOM elsewhere is data, not a BOM. A `NUL` (U+0000) anywhere is E001. A byte sequence
  that is not well-formed UTF-8 is E001. A BOM on read is W001, and a Producer that emits
  one violates canonical form (§7).

### 2.2 Line terminators

A line terminator is `LF` (U+000A), `CR LF` (U+000D U+000A, one terminator), or `CR`
(U+000D).

- A Parser MUST accept all three and MUST NOT report a diagnostic for them. One file MAY
  mix them; each occurrence is one terminator. A Producer MUST emit `LF` only. A final
  line without a terminator is accepted and MUST be reported as W003; a file SHOULD end
  with a newline, and a Parser MUST NOT reject one that does not.
- A terminator is never part of a field. `CR`/`LF` cannot occur inside quoted text: it
  starts a new line and leaves an unterminated string (E002).

### 2.3 Lines

Each line is classified in this order: version marker (§3.3, first line only), retired
record (§5.4), directive (§3.4), comment (§3.2), blank line (§3.1), otherwise a record
line (§3.5). A file MAY contain zero records; a Producer SHOULD NOT emit such a file. A
file containing only blank lines, comments, retired records, and directives is valid.

## 3. Lexical rules

### 3.1 Blank lines

A blank line is empty or contains only SPACE (U+0020) and TAB (U+0009). It has no
meaning, MUST be ignored, and MAY appear anywhere.

### 3.2 Comments

A comment is a line whose first character is `#` and which is not a version marker, a
retired record, or a directive. The rest is ignored and MUST NOT affect parsing; it MAY
contain any character except `CR`, `LF`, and `NUL`. A bare `#` is a valid comment.

### 3.3 Version marker

A file MAY begin, after an optional BOM, with the marker `#!iac <MAJOR>.<MINOR>` on
line 1. `MAJOR` and `MINOR` are decimal integers, one or more digits, no sign; exactly
one SPACE follows `#!iac`. The marker is a comment, so a parser that predates it ignores
it, but a conforming Parser MUST read it.

- Supported major version is 1. A greater `MAJOR` is E015 and no record is processed.
- A `MAJOR` of 1 with a newer `MINOR` is W007, then parsing continues; no marker means 1.0.
- Only a position-1 `#!iac` line is a marker; any other is a comment and MUST be ignored,
  and a linter SHOULD report W006. A Parser MUST NOT reject the file.
- A first line beginning `#!iac` that does not match the production is an ordinary comment.

### 3.4 Directives

A directive is a line beginning `#@` of the form `#@<name> <value>`, carrying
file-scoped metadata.

- `<name>` is one or more of `A`–`Z`, `a`–`z`, `0`–`9`, `-`, `_`.
- Exactly one SPACE separates name and value; `<value>` is the remainder with trailing
  SPACE and TAB ignored. An empty value is malformed. Directives are file-scoped and
  MUST NOT change the meaning of a record line.
- `#@` is reserved. An unrecognised directive MUST be ignored with W006. A malformed or
  duplicate directive MUST NOT cause rejection; a duplicate after the first occurrence
  is ignored and MUST be reported as W006.

IAC 1.0 defines exactly one directive, `#@language`, registered in `spec/registry.md`.
Its value is a BCP 47 tag (RFC 5646), informational: it MUST NOT affect timing, text,
colour, or Type, and an invalid tag MUST NOT cause rejection.

### 3.5 Record lines and the field separator

A record line is any non-blank line that is not a version marker, a retired record, a
directive, or a comment. It is divided into fields at ` : ` — SPACE, COLON, SPACE —
recognised only at brace depth 0, bracket depth 0, and outside a quoted string. A Parser
MUST tokenize left to right and MUST NOT use a plain string split; `spec/iac.abnf`
cannot express the three conditions, so this section is normative.

- Quote state: an unescaped `"` toggles it; `\"` does not close a string and `\\`
  consumes both characters (§5.2).
- Depth: outside quoted text, `{` and `[` increment and `}` and `]` decrement, never
  below 0. Braces and brackets inside quoted text have no effect.
- ` : ` at brace depth 0, bracket depth 0, outside a quoted string is a separator;
  occurrences inside text, `{...}`, or `[...]` are not.
- Text MAY contain ` : `, braces, brackets, commas, and pipes unescaped. `AudioName`
  MUST NOT contain ` : `, `"`, `{`, `}`, `[`, or `]` (§4.2).
- A separator is exactly one SPACE, COLON, SPACE; `:` alone, `::`, and tab around the
  colon are not separators.

Tokenization ends in exactly one state:

| State | Condition | Outcome |
|---|---|---|
| OK | quote closed, both depths 0 | fields split normally |
| UNTERMINATED_QUOTE | unescaped `"` open at end of line | E002 |
| UNBALANCED | quote closed, an opening `{` or `[` unmatched | E004 |

- UNTERMINATED_QUOTE MUST be E002 even though it also prevents separator recognition;
  it is lexical and pre-empts field counting. A terminated quote is never E002.
- UNBALANCED means intended separators were not recognised, so the field count is wrong:
  E004. A closing `}` or `]` without an opener never makes depth negative; it is handled
  by the field rules, not by UNBALANCED.
- A record MUST have exactly 3 or 4 fields; any other count is E004. With no separator
  the line has one field and is E004.

**Worked example.** Scanning

    Chapter One : {"Chapter : The Fall"|00:00:00:00-00:00:02:00|} : [#FFFFFF]

left to right: `Chapter One` is plain text at depth 0 with the quote closed, so the
first ` : ` ends field 1. The `{` raises brace depth to 1, so the ` : ` inside
`"Chapter : The Fall"` is both quoted and braced — not a separator. The `}` returns
depth to 0, so the next ` : ` ends field 2, and `[#FFFFFF]` is field 3.

### 3.6 Whitespace

- Only SPACE (U+0020) and TAB (U+0009) are whitespace; other Unicode spaces are content.
- A record line MUST be tokenized as written before trimming. Whitespace beyond canonical
  form (line edges, around a field separator, after an entry COMMA, and immediately inside
  the outer `{}` or `[]`) is non-canonical: a Parser MUST accept and trim it, report W004;
  empty field 1 is E005.
- Whitespace inside quoted text is content and MUST NOT be trimmed or normalised.
- Canonical form is exactly one SPACE each side of a field separator and exactly one
  SPACE after each entry COMMA (§7). A tab MAY appear in text and MUST be preserved.

## 4. Record grammar

The normative grammar is `spec/iac.abnf`; this section restates it per line, with the
line terminator removed.

### 4.1 Record line

```
record = audio-name " : " subtitle-set " : " color [ " : " type ]
```

Fields appear in this order and no other. Fields 1–3 are mandatory, field 4 is optional.
A present but empty field is invalid under that field's rule (E005, E012, E013,
E014), not treated as absent. An empty field 2 is an empty subtitle set (E012), not a
field-count error; an empty field 3 is a malformed colour (E013); an empty field 4 is a
malformed `Type` (E014).

### 4.2 AudioName

Field 1 names the audio track.

- It MUST NOT be empty (E005) and MUST NOT contain ` : ` (E006).
- It MUST NOT contain `"`, `{`, `}`, `[`, or `]`. When such a character leaves the
  line unbalanced it is caught earlier, as E002 or E004 (§8.2 stages 3–4); when the line
  still tokenizes, it is E006.
- It MUST NOT begin with `#`: such a line is a comment, directive, or retired record
  (§3, §5.4), so this is enforced by line classification.
- It MUST NOT exceed 256 code points (§9).
- Any other character is permitted, including SPACE, a single `:`, and non-ASCII; a
  Producer SHOULD restrict itself to printable characters.
- Comparison, including duplicate detection, is exact and case-sensitive: `VO_1` and
  `vo_1` are distinct AudioNames (for example `Level1VO1` and `music_KnewBefore`).

### 4.3 Subtitle set and entries

Field 2 is a brace-enclosed, non-empty list of entries separated by COMMA:

```
subtitle-set = "{" entry *( ", " entry ) "}"
entry        = text "|" time "-" time "|"
```

- The set MUST contain at least one entry; `{}` is E012.
- The canonical entry separator is COMMA followed by exactly one SPACE (§3.6, §7); a
  Parser MUST accept COMMA plus zero or more SP/TAB, reporting W004 unless exactly one
  SPACE follows. A COMMA inside quoted text is text, not a separator.
- Entries MUST appear in non-decreasing `StartTime` order; a descending pair is E011.
  Equal adjacent starts are non-decreasing and allowed; they overlap and produce W002.
- Overlapping intervals within one record are valid and produce W002.
- A malformed entry is reported with the code of the component that fails: unterminated
  quote E002, invalid escape E003, malformed time E008, forbidden control E017.

### 4.4 Colour and Type fields

```
color = "[" "#" 6HEXDIG "]"
type  = ALPHA *( ALPHA / DIGIT / "-" / "_" )
```

- `Color` is field 3, required, in square brackets (§5.3).
- `Type` is field 4, optional; absent means `Voice` (§5.5).
- A field 4 value that matches `type` is valid whether or not it is registered. A valid
  token followed by whitespace and further content is E018. A value that matches no
  `type` at all is E014.

## 5. Field semantics

### 5.1 AudioName (field 1, required)

AudioName is the identity of the record and the only link to an audio asset. IAC does
not define how an application maps it to a file, clip, or event; that mapping is outside
the format and MUST NOT cause the Parser to read a file or resolve a reference. Two live
records in one file MUST NOT share an AudioName; duplicates are E007. A retired record is
excluded from this check (§5.4). Parsers MUST preserve it exactly as written, including
case and interior spaces.

### 5.2 Subtitles (field 2, required)

The ordered entries of the record. Each entry pairs quoted text with a half-open
interval (§6).

- Text begins and ends with `"`. Inside text, `\"` encodes `"` and `\\` encodes `\`;
  any other backslash sequence is E003, as is a bare `\` before the closing quote. An
  unescaped `"` ends the text, and a string that is never closed is E002.
- Text MAY be empty (`""`). It MUST NOT contain U+0000–U+0008, U+000B, U+000C,
  U+000E–U+001F, or U+007F (E017); TAB is allowed, and `CR`/`LF` cannot occur (§2.2).
- Text MUST NOT exceed 4 096 code points after escape processing (E016).
- Text is otherwise arbitrary Unicode: ` : `, commas, pipes, braces, and brackets need
  no escaping. Parsers and Renderers MUST NOT normalise Unicode, collapse spaces, or
  change any code point.

```
"Chapter : The Fall"|00:00:03:00-00:00:05:50|
"He said \"go\" and \\ left"|00:00:05:50-00:00:07:00|
```

### 5.3 Color (field 3, required)

- Exactly `[#RRGGBB]`: one `[`, one `#`, six hexadecimal digits, one `]`.
- Hex digits are `0`–`9`, `a`–`f`, `A`–`F`; matching is case-insensitive. Eight digits
  (`#RRGGBBAA`), three digits, a missing `#`, missing brackets, or any other length is
  E013. Alpha is not supported in 1.0.
- The value is stored as written and compared case-insensitively. A Producer MUST
  preserve the case it received; a Renderer MUST interpret both cases identically.

### 5.4 Retired records

A line kept for reference but never rendered is a retired record:
`#!cut Level1VO2 : {"A deleted line"|00:00:00:29-00:00:00:92|} : [#FFFFFF]`.

- `#!cut`, exactly one SPACE, then a payload that MUST be a record in canonical form
  (§7): 3 or 4 fields, canonical separators, sorted entries, canonical `Type`.
- A Parser MUST NOT treat it as a record or render it; for parsing it is a comment.
- A line beginning with `#!cut ` is a retired record even when the payload is invalid;
  `#!cut` without the SPACE is an ordinary comment.
- A Linter SHOULD parse the payload under §4–§6 and report W008, naming the first
  E-code of §8.2, when the payload is not a valid record. That E-code is named in the
  W008 message and MUST NOT be emitted as a separate error. A valid payload keeps its
  ordinary warnings (for example W004), not W008.
- Retired records are excluded from the E007 duplicate check (§5.1); cutting a line and
  later recording a new one under the same name is a normal workflow.
- A formatter MUST preserve the line in place and canonicalise a valid payload; an
  invalid payload is preserved verbatim.
- For §9 a retired line is a comment: it does not count toward the record limit, but the
  file-size and line-length limits still apply.

Plain `#` cannot be auto-detected: a comment cannot be distinguished from prose, and the
superseded draft contains `# Format: Audio_name : {...} : [#Color]`. `#!cut` is not a
directive; `#@` is file-scoped metadata, while `#!cut` is line-scoped beside `#!iac`.

### 5.5 Type (field 4, optional)

- Absent means `Voice`. The value MUST match
  `type = ALPHA *( ALPHA / DIGIT / "-" / "_" )`: one token starting with an ASCII letter.
  Registered values are `Voice`, `Music`, `SFX`, `Narration`, and
  `UI` (`spec/registry.md`); matching is case-insensitive.
- A well-formed but unregistered value MUST be preserved, MUST NOT be an error, and
  SHOULD be reported as W005; a Renderer MUST fall back to default styling.
- A Producer MUST emit the canonical spelling for a registered value; for an
  unregistered value it MUST preserve the spelling received.
- Type affects styling only; it MUST NOT affect timing, text, or colour.

## 6. Time model

### 6.1 Representation

| Component | Meaning | Digits | Range |
|---|---|---|---|
| `HH` | hours | exactly 2 | `00`–`99` |
| `MM` | minutes | exactly 2 | `00`–`59` |
| `SS` | seconds | exactly 2 | `00`–`59` |
| `CC` | centiseconds | exactly 2 | `00`–`99` |

Each component is exactly two decimal digits, zero-padded (`00:00:00:07`, never
`0:0:0:7`). `CC` is a centisecond, 1/100 second, and is **not** a frame number.

### 6.2 Ranges and arithmetic

- A time's value is `cs = ((HH * 60 + MM) * 60 + SS) * 100 + CC`, an integer number of
  centiseconds. The range is `00:00:00:00` = 0 to `99:59:59:99` = 35 999 999.
- A component outside its range is E009 (`00:00:60:00`, `00:60:00:00`); wrong digit
  count, a non-digit, a missing colon, or a different component count is E008. Ordering
  is numeric order of `cs`, not lexicographic.

### 6.3 Half-open intervals

Every entry defines `[StartTime, StopTime)`:

- Visible at `StartTime`, inclusive; not visible at `StopTime`, exclusive.
- `StopTime` MUST be strictly greater than `StartTime`. Equality is E010, and a
  descending pair is E010.
- Touching cues are valid: an entry ending at `00:00:17:20` and the next starting at
  `00:00:17:20` do not overlap and produce no warning. Cue arithmetic composes:
  concatenating two files cannot create a one-centisecond overlap from touching bounds.
- Gaps are valid. Overlaps are valid and produce W002 (§4.3).

### 6.4 Frame-based sources

An importer converting from a frame-counting source MUST use
`cs = round(frames * 100 / fps)`, then clamp so that `StopTime > StartTime`. Rounding is
round-half-up. The frame rate is an input to conversion and MUST NOT be stored; an IAC
Parser MUST NOT infer a frame rate, resample, or reinterpret `CC` as frames.

## 7. Canonical form

A serializer MUST emit all of the following; this is what makes golden tests and formatters possible.

| Rule | Canonical output |
|---|---|
| Encoding | UTF-8, no BOM |
| Line endings | `LF` only |
| Final line | ends with `LF` |
| Record lines | one record per line |
| Fields | joined by exactly one SPACE, COLON, SPACE |
| Entry separators | exactly one COMMA followed by exactly one SPACE |
| Edge whitespace | none on a record line: not at its edges, not adjacent to a separator, and not immediately inside the outer `{}` or `[]` |
| Entry order | sorted by `StartTime`, non-decreasing |
| `Type` | omitted when `Voice`; registered values in canonical spelling |
| Retired records | `#!cut ` plus a canonical payload, preserved in place |
| Colour | preserved as written; comparison is case-insensitive |
| Records | original order preserved; sorting records is not part of canonical form |
| Comments, directives | written as they were read, apart from normalised line endings |
| Blank lines | a line of only SPACE or TAB is written as an empty line; positions are preserved |

- Formatting an already canonical file MUST reproduce it byte for byte. Record order is
  preserved: a Producer MUST NOT reorder records. Text, including interior whitespace
  and escapes, is preserved exactly; `\"` and `\\` MUST be re-emitted.

## 8. Error taxonomy

Codes are stable and shared by this specification, the linter, and every future tool. A
Parser MUST use these codes and MUST NOT invent new ones for the conditions listed.

### 8.1 Diagnostic codes

| Code | Severity | Meaning |
|---|---|---|
| E001 | error | Not valid UTF-8, or contains NUL |
| E002 | error | Unterminated quoted string |
| E003 | error | Invalid escape sequence |
| E004 | error | Wrong number of fields (expected 3 or 4) |
| E005 | error | Empty `AudioName` |
| E006 | error | Illegal character in `AudioName` |
| E007 | error | Duplicate `AudioName` |
| E008 | error | Malformed time (`HH:MM:SS:CC`) |
| E009 | error | Time component out of range |
| E010 | error | `StopTime <= StartTime` |
| E011 | error | Entries not in non-decreasing `StartTime` order |
| E012 | error | Empty subtitle set `{}` |
| E013 | error | Malformed or unsupported colour |
| E014 | error | Malformed `Type` token |
| E015 | error | Unsupported major version |
| E016 | error | A §9 limit exceeded |
| E017 | error | Forbidden control character in text |
| E018 | error | Trailing content after the last field |
| W001 | warning | BOM present |
| W002 | warning | Overlapping entries within a record |
| W003 | warning | Missing trailing newline |
| W004 | warning | Non-canonical casing/whitespace accepted |
| W005 | warning | Unregistered `Type` value |
| W006 | warning | Unknown or duplicate directive |
| W007 | warning | File declares a newer minor version |
| W008 | warning | A `#!cut` line whose payload is not a valid record |

Numbers are assigned once and are never reused. In 1.0 the E-numbers are contiguous, so a
diagnostic added later takes the next free number.

### 8.2 Detection order and precedence

A Parser MUST apply these stages in order and report the first stage that fails for a
given line. It MAY continue to report further errors; any E-code makes the file invalid.

| Stage | Check | Code |
|---|---|---|
| 1 | File-level encoding and NUL | E001 |
| 2 | Version marker major version | E015 |
| 3 | Tokenization: unterminated quote | E002 |
| 4 | Field count 3 or 4 (including UNBALANCED depths) | E004 |
| 5 | Field 1 not empty | E005 |
| 6 | Field 1 forbidden characters | E006 |
| 7 | Field 2 set non-empty | E012 |
| 8 | Each entry in file order: escapes, control characters, time shape, time range, interval, entry order | E003, E017, E008, E009, E010, E011 |
| 9 | Field 3 colour | E013 |
| 10 | Field 4 Type, then trailing content | E014, then E018 |
| 11 | File-level duplicate AudioName | E007 |
| 12 | Limits (§9), checked as soon as the quantity is known | E016 |

- An unescaped `"` open at end of line is E002; a closed quote with an unmatched opening
  `{` or `[` is E004 (§3.5). An empty field uses that field's code, not E004; `{}` is
  E012, not E008.
- `Music extra` in field 4 is E018; `!Music` is E014. A record with more than four
  fields is E004, never E018.
- E007 is file-level and applies to live records; retired records are excluded (§5.4).
  The conformance suite is constructed so each invalid case has exactly one code.
- A Linter parses each `#!cut` payload and reports W008, naming the first E-code that
  §8.2 would report for the payload. W008 is a warning; that E-code is not a separate error.

### 8.3 Exit codes

**Exit codes for CLI tools:** `0` clean, `1` warnings only, `2` at least one error.
A `--check` run that finds work to do (a file that is valid but not canonical) also
exits `2`, because a CI job must fail.

## 9. Limits

Every conforming implementation MUST accept at least the following.

| Quantity | Minimum a conforming implementation MUST accept |
|---|---|
| File size | 8 MiB |
| Line length | 64 KiB |
| Records per file | 10 000 |
| Code points per text | 4 096 |
| Code points per `AudioName` | 256 |

- File size is bytes including a BOM; line length is bytes excluding the terminator; text
  length counts code points after escape processing, excluding quotes. Text MUST NOT
  contain U+0000–U+0008, U+000B, U+000C, U+000E–U+001F, or U+007F (E017); tab is allowed.
- Exceeding a limit is E016. An implementation MAY accept more than the minimum, but it
  MUST NOT reject a file that stays within it. Limits are a security control as well as an
  interoperability floor (§13). The entry count is bounded by the line limit and needs no
  separate row.

## 10. Rendering minimums

A Renderer MUST implement all of the following.

1. MUST NOT render a retired record (`#!cut`): it is not a record; a nonexistent record is not rendered.
2. MUST display an entry exactly on `[StartTime, StopTime)` with no rounding and no inclusive stop.
3. MUST apply the record's colour to all of its entries.
4. MAY style entries by Type and MUST NOT change timing or text. An unregistered Type
   MUST fall back to default styling.
5. MUST NOT merge, trim, re-wrap, normalise, or change text code points; display as stored.
6. MUST display all active entries when intervals overlap; stacking order is implementation-defined, but dropping an entry is not allowed.
7. MUST NOT execute, evaluate, or resolve anything in the text. IAC text is opaque.

A Renderer MUST NOT render a file a Parser has rejected. It MAY render a partial result
only if the output is marked non-conforming.

## 11. Versioning and forward compatibility

- The specification version is `MAJOR.MINOR`; IAC 1.0 is major 1, minor 0. A 1.x Parser
  MUST read every 1.y file with `y <= x` and an unmarked file as 1.0. It MUST fail with
  E015 when the declared major is greater, and report W007 when only the minor is newer.
- A later minor version MUST add only constructs a 1.0 Parser can ignore or preserve:
  comments, directives, and registry values. Changing record syntax requires a major
  version; a breaking change needs a deprecation cycle of at least one minor release.
- Unknown directives MUST be ignored with W006; unknown Type values MUST be preserved
  with W005. These are the two extension points of 1.0.
- A Producer MAY emit the marker; `#!iac 1.0` is the recommended declaration.

## 12. Media type and file extension

- Interim media type: `text/x-iac` (unregistered); intended registered name: `text/vnd.iac`.
- Primary extension: `.iac`. `.txt` is legacy: existing valid IAC in `.txt` MUST be
  accepted, but new tooling MUST NOT produce it and MUST NOT use any other extension.
- The format is always UTF-8. A `charset=utf-8` parameter MAY appear in transport; any
  other charset contradicts §2.1.

## 13. Security considerations

IAC is untrusted input. Implementations MUST assume any file may be hostile.

- The format cannot execute anything: no script, markup, entity, include, external
  reference, path, or URL. Text is opaque (§10.7).
- Resource limits (§9) are mandatory; a Parser SHOULD enforce them incrementally rather
  than after buffering the whole file.
- A long line without a separator forces tokenization work; a Parser MUST reject it at
  the line-length limit. Empty or oversized fields MUST NOT cause unvalidated allocation.
- Renderers MUST treat text as data, never as markup.

The full analysis is in [`spec/security.md`](security.md).

## 14. Normative references

- RFC 2119 — Key words for use in RFCs to Indicate Requirement Levels.
- RFC 3629 — UTF-8, a transformation format of ISO 10646.
- RFC 5234 — Augmented BNF for Syntax Specifications: ABNF.
- RFC 5646 — Tags for Identifying Languages (BCP 47).
- RFC 7405 — Case-Sensitive String Support in ABNF.
- `spec/iac.abnf` — the normative grammar; `testdata/conformance.json` — the normative suite.

## 15. Informative references

- RFC 0001 — Standardizing IAC 1.0 (`rfcs/0001-standardize-iac-1.0.md`), the decision
  record this specification implements.
- `legacy/zh-specification-v1.0-draft.md` — the superseded 1.0-draft, retained for history.
- `spec/rationale.md` — design-decision record.
- `spec/security.md` — threat model and implementation checklist.
- RFC 6838 — Media Type Specifications and Registration Procedures.
- W3C WebVTT — a general caption format, for scope comparison only.
