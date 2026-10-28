# Error and warning codes

**Answers:** a tool printed a code — what happened, and what do I change?
**Does not answer:** the normative wording. That is
[spec §8](../spec/iac-1.0.md), and where the two disagree the spec wins.

`E` codes make the file invalid; `W` codes do not. Every tool that follows IAC
uses the same numbers, and the numbers never change meaning.

## The table

| Code | One line | What to do |
|---|---|---|
| E001 | Not UTF-8, a NUL byte, or a BOM from a producer | Re-save as UTF-8 without a BOM, and remove NUL padding. Fix the exporter, not the bytes by hand. |
| E002 | A quoted string is never closed | The line ended inside `"…"`. Close it, and write interior quotes as `\"`. Curly quotes are text, not delimiters. |
| E003 | Invalid escape | A backslash before anything but `"` or `\`: Windows paths, `\n`, `\t`, or a lone `\` before the closing quote. Write `\\` for one backslash. |
| E004 | Wrong number of fields, or an unclosed `{` / `[` | Expected 3 or 4 fields. Count the ` : ` separators, close the braces, and check that a ` : ` inside text is quoted. A draft-era record with `: true : Music` has five fields; run `migrate`. A lone `: true` or `: false` is a valid but unregistered `Type` (W005). |
| E005 | Empty `AudioName` | The line starts with the field separator. Put the track name first. |
| E006 | Illegal character in `AudioName` | The name contains `"`, `{`, `}`, `[`, `]`, or a ` : ` sequence. Replace it with a space or `_`. Two caveats: a ` : ` in a name splits the line before validation, so it usually surfaces as E004; and a leading `#` makes the line a comment, so the track disappears silently. |
| E007 | Duplicate `AudioName` | Two live records share a name. Comparison is exact and case-sensitive, so `VO_1` and `vo_1` do not collide. Retired `#!cut` lines are exempt. |
| E008 | Malformed time | The token is not four two-digit components separated by colons: decimal separators, a missing component, a hyphen, spaces, or one-digit fields. |
| E009 | Time component out of range | `MM` or `SS` above 59. Carry: `00:00:60:00` is `00:01:00:00`. |
| E010 | `StopTime <= StartTime` | The cue has no duration, usually a swapped pair. Extend the stop. A line you want to keep but not show becomes `#!cut`, not a zero-length cue. |
| E011 | Entries out of order | Cues were inserted out of sequence. Sort them; `fmt` does it for you. Equal starts are allowed. |
| E012 | Empty subtitle set | The field is empty or contains only `{}`. Add a cue, or retire the track. |
| E013 | Malformed colour | Not `[#RRGGBB]`: missing bracket or `#`, three digits, non-hex, or eight digits. Alpha is not part of 1.0. |
| E014 | Malformed `Type` | Field 4 is empty or cannot be a token (`!Music`, a leading digit, punctuation). A well-formed unknown value is W005, not this. |
| E015 | Unsupported major version | The file declares `#!iac 2.0` or higher. Upgrade the parser, or correct the version line. |
| E016 | A §9 limit exceeded | File over 8 MiB, line over 64 KiB, over 10 000 records, text over 4 096 code points, or `AudioName` over 256. Split the file or the cue. |
| E017 | Forbidden control character in text | U+0000–U+0008, U+000B, U+000C, U+000E–U+001F, or U+007F inside quotes. Usually pasted from a PDF or a spreadsheet. Tab is allowed. |
| E018 | Trailing content after the last field | A valid `Type` followed by more text: `Music extra`, `true junk`, or a comment glued to the record. A fifth ` : ` is E004 instead. |
| W001 | BOM present | Save as UTF-8 without BOM. Parsers tolerate it; producers must not emit it. |
| W002 | Overlapping entries | Cue *n* stops after cue *n+1* starts. Trim a boundary, or accept it: rendering allows stacking. |
| W003 | Missing trailing newline | Append a newline and enable "insert final newline". |
| W004 | Non-canonical casing or whitespace accepted | Extra spaces around a separator, whitespace inside `{}`, or a registered `Type` in the wrong casing. Run `fmt`. |
| W005 | Unregistered `Type` | The value is not in [registry](../spec/registry.md). Preserve it, style it as `Voice`, or register it. A draft-era `: true` lands here. |
| W006 | Unknown or duplicate directive | An unrecognised `#@` line, a malformed one, or the same directive twice. Ignored, never fatal. |
| W007 | File declares a newer minor version | A 1.0 parser met `#!iac 1.1`. Read what you can, warn, continue. |
| W008 | A `#!cut` payload is not a valid record | The retired line no longer parses. Fix the payload; the file is still valid. W008 names the underlying E-code. |

## Notes on the ones that bite

**E001 and W001 are different failures.** A BOM is tolerated on read (W001) and is a
producer defect (E001). A converter is a producer: emitting a BOM makes its output
fail other producers' checks.

**E008 versus E009.** E008 is "this is not a time"; E009 is "this is a time with an
impossible value". A UI can fix the second one by arithmetic and needs the author for
the first.

**E013 is deliberately loud.** Eight-digit colour is rejected rather than truncated,
because a silent truncation produces a visibly wrong colour that is hard to trace.

**E016 numbers are floors.** They are the minimum an implementation must accept. A
parser may accept more; a producer should never need to.

**Precedence.** Report the first failing stage of
[spec §8.2](../spec/iac-1.0.md). Continuing to report later codes is allowed, but a
cascade from one structural error is worse than one accurate code. The deliberate
distinctions: `{}` is E012, not E008; `Music extra` is E018, not E014; `!Music`
is E014; a draft-era `: true` is not an error at all.

**W008 wraps an error without failing the file.** The payload's diagnostics are not
promoted to file errors, which is what lets a retired line sit in a file for months
and still be checked.

**The numbering is contiguous.** E001–E018 and W001–W008. Numbers are assigned once
and never reused.

## Exit codes

| Exit | Meaning |
|---|---|
| `0` | No findings |
| `1` | Warnings only |
| `2` | At least one error |

These are the CLI-wide codes from [spec §8.3](../spec/iac-1.0.md). A subcommand that
cannot produce warnings never returns `1`.
