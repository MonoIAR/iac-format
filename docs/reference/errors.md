# Error and warning codes

Codes are stable identifiers, shared by [spec §8](../../spec/iac-1.0.md), the reference linter, and every tool that follows it. They do not change meaning without a major version bump. `E` codes are fatal for the file, `W` codes are not.

The table below reproduces the normative list (spec §8.1, RFC 0001 §D15), with the changes from [RFC 0002 §3](../../rfcs/0002-remove-enabled-field.md#3-error-taxonomy-changes): E022 is retired and W008 is added. The last column is the cause and the fix as implementers and authors actually meet them.

## Table

| Code | Severity | Meaning | Cause, and the fix |
|---|---|---|---|
| E001 | error | Not valid UTF-8, contains NUL, or has a BOM in producer mode | The bytes are not UTF-8 (often UTF-16 saved with a `.iac` extension), or the file was NUL-padded. Re-save as UTF-8 without BOM; fix the exporter, not the bytes by hand. |
| E010 | error | Unterminated quoted string | A cue opened `"` and the line ended before the closing `"`. Close it, and write interior quotes as `\"`. Curly quotes (`“ ”`) are content, not delimiters, so they never close the string. |
| E011 | error | Invalid escape sequence | A backslash followed by something other than `"` or `\`: Windows paths, `\n`, `\t`, a stray `\` before the closing quote. Write `\\` for one literal backslash. |
| E012 | error | Wrong number of fields (expected 3 or 4) | Missing colour, an accidental fifth field, a ` : ` sitting outside quotes where text was meant, or a record too misshapen to split — a cue set without `{}`, an entry without its `|` delimiters. Count the fields; quote the text; check the braces. A draft-era record that still carries `: true` or `: false` before a `Type` produces five fields and lands here. |
| E013 | error | Empty `AudioName` | The line begins with the field separator. Put the track name first. |
| E014 | error | Illegal character in `AudioName` | The name contains ` : `, `"`, `{`, `}`, `[`, `]`, or starts with `#`. Replace the character with a space or `_`. Two caveats: a ` : ` in a name splits the line before validation, so it usually surfaces as E012; and a leading `#` makes the line a comment, so the track silently disappears instead of failing. |
| E015 | error | Duplicate `AudioName` | Two records share a name — copy-paste, a merge, or a generator bug. Comparison is exact and case-sensitive, so `VO_1` and `vo_1` do not collide. Rename one; names are the only track identity the format has. Retired `#!cut` lines are exempt, so a name can be reused after a cut. |
| E016 | error | Malformed time (`HH:MM:SS:CC`) | The token is not four two-digit components separated by colons: decimal separators, missing component, a hyphen inside, stray spaces, one-digit fields. Rewrite as `HH:MM:SS:CC`. |
| E017 | error | Time component out of range | `MM` or `SS` above 59, `CC` above 99, `HH` above 99. Carry instead: `00:00:60:00` is `00:01:00:00`; `00:00:00:100` is `00:00:01:00`. |
| E018 | error | `StopTime <= StartTime` | The cue has no positive duration, usually a swapped pair or a stop edited without the start. Extend the stop. A line you want to keep but not show is retired as a `#!cut` comment, not given a zero-length cue. |
| E019 | error | Entries not in non-decreasing `StartTime` order | Cues were inserted out of sequence. Sort them; `fmt` does this for you. Equal start times are allowed — "non-decreasing" is not "strictly increasing". |
| E020 | error | Empty subtitle set `{}` | The record has no cues, or the braces contain only whitespace. Add a cue, or retire/remove the track — an empty track cannot be rendered or translated. |
| E021 | error | Malformed or unsupported colour | Not `[#RRGGBB]`: missing brackets or `#`, three-digit shorthand, non-hex digits, or eight-digit `#RRGGBBAA`. Use exactly six hex digits; alpha is not part of 1.0. |
| E023 | error | Malformed `Type` token | The fourth field is present but empty, or its value cannot be a type token at all (`!Music`, a leading digit, punctuation). Remove the trailing separator, or supply a value matching `ALPHA *( ALPHA / DIGIT / "-" / "_" )`. A well-formed unknown value is W005, and a valid token followed by more content is E027 — not E023. |
| E024 | error | Unsupported major version | The file declares `#!iac` with a major version above what the parser supports — for example `2.0`. Upgrade the parser. If the file is simply mislabelled, correct the version line; do not guess and continue. |
| E025 | error | A D12 limit exceeded | Spec §9 limits: file over 8 MiB, line over 64 KiB, more than 10 000 records, more than 4 096 entries in a record, text over 4 096 code points, or `AudioName` over 256. Split the file or the cue; check for a runaway generator. |
| E026 | error | Forbidden control character in text | `U+0000`–`U+0008`, `U+000B`, `U+000C`, `U+000E`–`U+001F`, or `U+007F` inside quoted text. Usually pasted in from a PDF, a spreadsheet, or a rich-text editor. Strip it; a tab is allowed. |
| E027 | error | Trailing content after the last field | A valid `Type` token is followed by whitespace and more content: `Music extra`, `true junk`, or a comment glued to the record. Delete the extra, and put the comment on its own line. A fifth ` : ` produces five fields and E012 instead, not E027. |
| W001 | warning | BOM present | The file starts with a UTF-8 BOM. Parsers tolerate it; producers must not emit it. Save as UTF-8 without BOM. |
| W002 | warning | Overlapping entries within a record | Cue *n* stops after cue *n+1* starts, so both are visible at once. Trim one boundary. If stacked display is intended, the warning is informational — rendering allows it. |
| W003 | warning | Missing trailing newline | The last line has no terminator. Append a newline and enable "insert final newline" in the editor. |
| W004 | warning | Non-canonical casing/whitespace accepted | A lenient parser accepted a variant: extra spaces around a field or cue separator, a registered `Type` written in non-canonical casing, or similar. Run `fmt`. |
| W005 | warning | Unregistered `Type` value | The value is not in [registry/types.md](../../registry/types.md). Parsers must preserve it and renderers fall back to default styling. Register it or map it to an existing type. A draft-era `: true` in field 4 lands here as `Type` = `true`. |
| W006 | warning | Unknown or duplicate directive | An unrecognised `#@` directive (for example a 1.1 feature read by a 1.0 tool), or the same directive twice. Remove it, or keep one. Unknown directives are ignored, never fatal. |
| W007 | warning | File declares a newer minor version | A 1.0 parser met `#!iac 1.1`. Read what you can, warn, and continue. Upgrade the tool if the file uses the newer features. |
| W008 | warning | A `#!cut` line is not a valid record | The retired payload fails the rules a live record must pass — a stale interval (E018), an unbalanced brace (E012), a bad colour (E021), an empty payload. Fix the payload; the file itself is still valid. W008 names the underlying E-code. A valid but non-canonical payload is W004, not W008; `#!cut` without a following space is an ordinary comment. |

## Notes on the ones that bite

**E001 and W001 are different failures.** A BOM is tolerated on read (W001) but is a producer defect: in producer mode it is E001. The distinction matters for a converter, which is a producer — emitting a BOM makes its output fail other producers' checks.

**E016 versus E017.** E016 is "this is not a time", E017 is "this is a time with an impossible value". Both are worth distinguishing in a UI: a malformed token needs the author's attention, an out-of-range one is arithmetic that can be suggested.

**E021 is deliberately loud.** Eight-digit colour is rejected rather than truncated, because a silent truncation produces visibly wrong colours that are hard to trace back to the converter. Any tool that supports alpha today is emitting files that 1.0 must reject.

**E025 numbers are floors, not targets.** They are the minimum a conforming implementation must accept (spec §9). A parser may accept more; a producer should not need to. If you hit one, the file is far outside subtitle territory.

**Precedence.** Report the first stage that fails for a line, in the order spec §8.2 gives. Continuing to report later codes is allowed, but any E-code makes the file invalid, and a cascade of secondary codes from one structural error is worse than one accurate code. Note the deliberate distinctions: `{}` is E020, not E016; `Music extra` is E027, not E023; `!Music` is E023; a draft-era `: true` is not an error at all, it is `Type` = `true` with W005.

**W008 wraps an error without failing the file.** A malformed `#!cut` payload is reported as one W008 naming the underlying E-code, and the payload's own diagnostics are not promoted to file errors. That is what lets a retired line sit in a file for months and still be checked: it cannot rot into invalid syntax, and it cannot break a build either.

**E022 is retired.** RFC 0002 removed the `enabled` field and with it the code that validated it. The number must not be reused for something new, so a tool that meets an `enabled`-era file should either migrate it or report the field-count/type consequences (E012 or W005), never E022.

**Codes that do not exist.** `E002`–`E009` are unused, and `E022` is retired. Numbers are assigned once and never reused, so a gap is cheaper than a rename.

## Exit codes

| Exit | Meaning |
|---|---|
| `0` | No findings |
| `1` | Warnings only |
| `2` | At least one error |

These are the CLI-wide codes from spec §8.3: `0` clean, `1` warnings only, `2` errors.
