# Authoring guide

Rules for people writing `.iac` files by hand or generating them. Normative details live in [spec/iac-1.0.md](../../spec/iac-1.0.md); this guide covers what to do in practice.

## Start from a template

```iac
#!iac 1.0
#@language en-US

ch01_finale_vo_01 : {"那地方看起来或许很平静"|00:00:00:12-00:00:02:45|, "但……"|00:00:03:19-00:00:04:19|} : [#FFFFFF]
#!cut ch01_finale_vo_02 : {"Cut for pacing"|00:00:05:00-00:00:06:10|} : [#FFFFFF]
ch01_finale_music_01 : {"I meant to say goodbye"|00:00:40:62-00:00:49:35|} : [#FFFFFF] : Music
```

`#!iac 1.0` and `#@language` are both optional. Keep them: the version line is how a future 1.x parser knows what it is reading without guessing.

## Name tracks for the pipeline, not for the moment

`AudioName` is the track's identity. It is what a translation database matches on, what a diff shows when a line changes, and what a sound engineer sees next to the wave file. Rules:

- **Unique in the file.** A repeated name is E015 and makes the file unparseable, not ambiguous. Comparison is exact and case-sensitive: `VO_1` and `vo_1` are two different tracks — a useful fact, and a debugging trap if you rely on it. Retired `#!cut` lines do not take part in this check.
- **No ` : `, `"`, `{`, `}`, `[`, `]`.** These are structure, not content — E014.
- **Non-empty, and must not start with `#`.** A leading `#` makes the line a comment.
- **At most 256 code points.** Implementation limit, not a style preference.

A scheme that survives production: `<scene>_<speaker-or-role>_<index>`, e.g. `ch03_tower_vo_07`, `ch03_tower_music_01`. Include the scene so a line can be found from a bug report; include an index so two lines from the same speaker never collide. Avoid embedding final timings or revision numbers in the name — when the edit arrives, the name is the one thing that should not move.

## Timing

Times are `HH:MM:SS:CC`. The last field is **centiseconds** (1/100 s), two digits, `00`–`99`. It is not a frame count and carries no frame rate.

- An interval is `[start, stop)`: visible from `start`, gone at `stop`. Touching cues (`00:00:17:20` → `00:00:17:20` on the next cue) are correct and are how [music.iac](../../examples/music.iac) chains lyric lines.
- `stop` must be strictly greater than `start` — E018. A zero-length cue displays nothing; it is almost always a typo.
- Cues within a record must be in non-decreasing start order — E019. Records themselves may appear in any order.
- Gaps between cues are normal. Overlaps are legal and render as stacked cues, but they are usually a mistake and the linter flags them as W002.
- `99:59:59:99` is the ceiling (`HH` is `00`–`99`), just under 100 hours. If your source is longer, the file is not a subtitle file.

Do not hand-round frame numbers. If your source is frame-based, convert once with the formula in [conversion.md](conversion.md) — or by exporting a millisecond-based SRT from your animation tool and importing that — and keep the resulting file as the master.

## The two escapes

Inside text, exactly two sequences are escapes:

| Write | To get |
|---|---|
| `\"` | a literal `"` |
| `\\` | a literal `\` |

Anything else — `\n`, `\t`, `\u00e9`, `'`, a Windows path typed literally — is E011. There is no `\n`: a record is one line, and control characters other than a tab are forbidden in text. A literal tab is legal, but it is invisible in review; a space is usually what you meant.

Everything else is literal. Quotes protect ` : `, commas, `{}`, `[]`, `|`, and leading/trailing spaces, so none of them need escaping:

```iac
ch02_radio_vo_04 : {"Chapter : The Fall"|00:01:10:00-00:01:12:30|, "他说 : 你好"|00:01:13:00-00:01:14:40|, "a, b, {c}"|00:01:15:00-00:01:16:00|} : [#FFFFFF]
```

## Cut lines: `#!cut`

When a line is cut from the script, retire the record instead of deleting it:

```iac
#!cut ch04_hall_vo_11 : {"We never made it out."|00:02:00:00-00:02:03:00|} : [#FFFFFF]
```

- `#!cut`, exactly one space, then the record in canonical form. It is a comment: a parser must not treat it as a record, and no renderer can display it.
- The linter still parses the payload. If a retired record stops validating — a stale time range, a typo, an unbalanced brace — you get **W008**, which names the underlying E-code. That is the point of the marker: a cut line cannot rot quietly in a corner of the file.
- `fmt` preserves retired records and rewrites their payloads in canonical form: cues sorted, `Type` in its canonical spelling.
- Retired records are exempt from the duplicate-name check (**E015**). Cutting a line and later recording a new one under the same asset name is a normal workflow, so the name is free to reuse.
- They are greppable and countable: `grep -c '^#!cut'`.

**Delete instead of retiring when** the line never existed in a shipped build, when its text must not ship at all — embargoed content, a spoiler, a rights problem — or when the record is a placeholder with no translation and no timing worth keeping. Retiring preserves a translation and a decision; where there is neither, a `#!cut` line is just weight.

**Do not comment a line out with a plain `#`.** A plain comment is prose: nothing checks it, no tool sees it, and it is indistinguishable from a note such as `# Format: ...`. `#!cut` is the machine-checked form.

**Do not leave a draft-era `: true` / `: false` field.** After the field's removal, `NAME : {...} : [#FFFFFF] : true` is a record whose `Type` is literally `true` (W005), and the five-field form is E012. Run `python tools/iac_lint.py migrate <file>` instead.

## Type

`Type` is the optional fourth field. Absent means `Voice`.

| Value | Use for |
|---|---|
| `Voice` | Dialogue. The default; canonical form omits it. |
| `Music` | Lyrics and sung lines, usually with one cue per line. |
| `SFX` | Descriptive captions for non-speech audio. |
| `Narration` | Voice-over and narrator tracks. |
| `UI` | Menus, tutorials, diegetic interface text. |

Matching is case-insensitive and serializers emit the canonical spelling, so `music` becomes `Music`. Unknown values are preserved by parsers and warn as W005 — a studio may extend the set, but anything you invent will not get styling from third-party renderers. Register new values per [registry/types.md](../../registry/types.md).

## Canonical form

`python tools/iac_lint.py fmt <file>` produces canonical output:

- one record per physical line;
- fields joined by exactly ` : `, cues by exactly `, ` (one space after the comma);
- no leading or trailing whitespace;
- cues sorted by `StartTime`, non-decreasing;
- `Type` omitted when it is `Voice`;
- `#!cut` lines kept, with the payload rewritten in canonical form.

Run `fmt` before committing. Canonical form is what makes a review diff readable, a golden test stable, and a streaming renderer possible. If your generator emits ` : Voice` on every line, `fmt` removes it — that is the serializer's job, not a semantic change.

## The eight mistakes

**1. A raw quote in text.** The scanner ends the string at the first unescaped `"`.

```iac
Before: {"He said "go"."|00:00:04:00-00:00:06:00|}
After:  {"He said \"go\"."|00:00:04:00-00:00:06:00|}
```

**2. A lone backslash.** Only `\"` and `\\` exist.

```iac
Before: {"C:\Users\audio"|00:00:04:00-00:00:06:00|}
After:  {"C:\\Users\\audio"|00:00:04:00-00:00:06:00|}
```

**3. Zero-length or inverted interval.** E018.

```iac
Before: {"Wait."|00:00:05:00-00:00:05:00|}
After:  {"Wait."|00:00:05:00-00:00:06:00|}
```

**4. Cues out of order.** E019, even when the overlap looks harmless.

```iac
Before: {"One"|00:00:08:00-00:00:09:00|, "Two"|00:00:02:00-00:00:03:00|}
After:  {"Two"|00:00:02:00-00:00:03:00|, "One"|00:00:08:00-00:00:09:00|}
```

**5. The same track name twice.** E015. Two records with the same name cannot be addressed separately downstream.

```iac
Before: ch05_vo_01 : {...} : [#FFFFFF]
        ch05_vo_01 : {...} : [#FFFFFF]
After:  ch05_vo_01 : {...} : [#FFFFFF]
        ch05_vo_02 : {...} : [#FFFFFF]
```

**6. Structure characters in the track name.** E014.

```iac
Before: Chapter 5 [Final] : {...} : [#FFFFFF]
After:  Chapter 5 Final : {...} : [#FFFFFF]
```

A name that contains ` : ` is split before it is validated, so the line fails as E012 with a cascade of field errors rather than as E014. Same fix: take the sequence out of the name.

**7. Colours that are not `[#RRGGBB]`.** Missing brackets, three digits, or an alpha pair all fail with E021. Alpha is not part of 1.0.

```iac
Before: ... : #FFFFFF
        ... : [#FFF]
        ... : [#FFFFFF80]
After:  ... : [#FFFFFF]
```

**8. A cut line that is not marked.** A plain `#` comment is invisible to the linter; a leftover draft-era boolean is not a boolean any more.

```iac
Before: # ch04_vo_02 : {"We never made it out."|00:02:00:00-00:02:03:00|} : [#FFFFFF]
        ch04_vo_03 : {"We never made it out."|00:02:02:00-00:02:05:00|} : [#FFFFFF] : false
After:  #!cut ch04_vo_02 : {"We never made it out."|00:02:00:00-00:02:03:00|} : [#FFFFFF]
        #!cut ch04_vo_03 : {"We never made it out."|00:02:02:00-00:02:05:00|} : [#FFFFFF]
```

## Before you commit

```bash
python tools/iac_lint.py validate content/
python tools/iac_lint.py fmt content/myfile.iac
```

Exit `0` is clean. Fix every `E` code; decide about each `W` code deliberately. If a warning is wrong for a legitimate case, say why in the commit message or the review — that record is how the rule gets fixed later.
