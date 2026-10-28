# Authoring guide

**Answers:** how do I write and edit `.iac` content that stays valid?
**Does not answer:** the exact rules. Those are
[spec §3–§7](../spec/iac-1.0.md); this page summarises and links.

## Start from a template

```iac
#!iac 1.0
#@language en-US

track_name : {"First line."|00:00:01:00-00:00:03:00|, "Second line."|00:00:03:50-00:00:05:00|} : [#FFFFFF]
```

Three fields are required: the track name, the cue set, and the colour. A fourth,
`Type`, is optional. One record per line, and the line is the unit of review.

## Name tracks for the pipeline, not for the moment

`AudioName` is the only identity a record has. It must not contain ` : `, `"`,
`{`, `}`, `[`, or `]`, and it must be unique among live records — exact and
case-sensitive, so `VO_1` and `vo_1` are two tracks.

Pick a scheme a build tool can predict: `<scene>_<speaker><n>` or `<asset>_<slot>`.
Names are cheap to change before assets are wired up and expensive afterwards. Do not
encode the line's text or language in the name.

## Timing

`HH:MM:SS:CC`, two digits per component, `CC` in centiseconds — not frames. A cue is
`[start, stop)`: visible at the start, gone at the stop. So a cue may end exactly where
the next begins, which is how lyric tracks are written:

```iac
music_theme : {"Line one"|00:00:08:58-00:00:17:20|, "Line two"|00:00:17:20-00:00:25:99|} : [#FFFFFF] : Music
```

A gap is fine. An overlap is fine and produces W002. A stop at or before its start is
E010. Frames become centiseconds with `cs = round(frames * 100 / fps)`; see
[conversion.md](conversion.md).

## The two escapes

Inside quoted text, exactly two sequences mean anything: `\"` for a quotation mark and
`\\` for a backslash. Everything else after a backslash is E003.

```iac
quote : {"He said \"go\" and \\ then left."|00:00:01:00-00:00:02:00|} : [#FFFFFF]
```

Common accidental E003 sources: Windows paths (`C:\new`), `\n`, `\t`, and a backslash
before the closing quote. Write `\\` for one literal backslash.

Everything else needs no escaping. ` : `, commas, pipes, braces, brackets, and Chinese
punctuation are ordinary text inside the quotes.

## Cut lines: `#!cut`

A line you want to keep but never render is a comment that still holds a record:

```iac
#!cut Level1VO2 : {"A deleted line"|00:00:00:29-00:00:00:92|} : [#FFFFFF]
```

- It is a comment for parsing and rendering: nothing displays it.
- The linter parses the payload and reports W008 if it is no longer valid, so a cut
  line cannot rot silently.
- `fmt` keeps it in place and canonicalises a valid payload.
- It is exempt from the duplicate-name check, so you can cut `Level1VO2` today and
  record a new one under that name tomorrow.

Write `#!cut` plus exactly one space. `#!cut` followed by anything else is an ordinary
comment.

## Type

`Type` is a styling hint: `Voice` (the default, omit it), `Music`, `SFX`, `Narration`,
`UI`. Matching is case-insensitive, and the canonical spelling is what `fmt` writes.

A well-formed value outside the registry is allowed: it is preserved, reported as
W005, and styled as `Voice`. Use it when the build consumes it and a generic value
would lose information.

## Canonical form

`fmt` produces, and `fmt --check` enforces:

- one record per line, fields joined by ` : `, entries by `, `;
- cues sorted by start time;
- `Type` omitted when it is `Voice`, registered values in canonical casing;
- colour preserved as written;
- UTF-8, no BOM, LF endings, final newline;
- comments and directives written as they were read.

Record order is never changed: sorting records is not part of canonical form.

## The eight mistakes

| # | Symptom | Cause | Fix |
|---|---|---|---|
| 1 | E004 | A ` : ` in the track name or outside quotes | Quote the text; keep ` : ` out of `AudioName` |
| 2 | E008 | `0:0:1:0` instead of `00:00:01:00` | Two digits per component |
| 3 | E010 | Swapped start and stop | `stop` after `start`, always |
| 4 | E002 | A raw `"` inside text | Write `\"` |
| 5 | E003 | Windows path or `\n` in text | Write `\\` |
| 6 | E004 / W005 | A draft-era `: true` or `: false` field | `python tools/iac_lint.py migrate <file>` |
| 7 | E013 | `[#FFF]` or `[#RRGGBBAA]` | Six hex digits, brackets, and `#` |
| 8 | W003 | A missing final newline (CRLF is accepted silently; only `fmt --check` reports it) | `fmt` fixes both |

## Before you commit

```bash
python tools/iac_lint.py validate path/to/file.iac
python tools/iac_lint.py fmt --check path/to/file.iac
```

Both exit `0` on a clean, canonical file. If `validate` is clean but `--check` is not,
run `fmt` without `--check` and review the diff.
