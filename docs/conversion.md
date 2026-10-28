# Conversion guide: SRT, VTT, ASS

**Answers:** how do I move subtitles between the common formats and IAC without
shifting a cue by a centisecond?
**Does not answer:** the IAC rules. Those are [spec §6](../spec/iac-1.0.md); this page
is about the mapping.

## The five things that go wrong

1. **Closed versus half-open ends.** SRT and ASS stops are inclusive in practice, IAC's
   are exclusive. Adding one centisecond to every stop is wrong; the right move is not
   to touch the stop at all and to accept the one-centisecond difference at the seam
   (see below).
2. **Rounding twice.** Convert to an integer once, from the source's own unit.
3. **Frames.** ASS and SRT are time-based; if your source is a frame count, use
   `cs = round(frames * 100 / fps)` and never store the frame rate.
4. **Colour order.** ASS stores `&HAABBGGRR`: two hex digits of alpha, then blue, green,
   red. IAC stores `[#RRGGBB]` and has no alpha.
5. **Silent loss.** Every converter drops something. Report it per file; a pipeline that
   cannot say what it dropped cannot be trusted.

## Timestamps: round once, half up

SRT writes `HH:MM:SS,mmm`. IAC stores centiseconds:

```text
cs = (ms + 5) // 10
```

That is round-half-up on a value with three decimal digits. Do not convert to seconds
as a float and multiply — binary floating point reintroduces the rounding error you
were trying to avoid.

### Closed versus half-open: the 1 cs problem

A source cue `00:00:01,000 --> 00:00:02,000` ends, inclusive, at exactly 2.000 s. In IAC
that cue is `00:00:01:00-00:00:02:00` and is not visible at `02:00`. The next cue that
starts at `02:00` therefore begins exactly where this one ends: no gap, no overlap.

Do not add a centisecond to the stop to "include" the last frame. That turns every
touching pair into a one-centisecond overlap (W002) and shifts every seam.

## SRT → IAC

```bash
python tools/iac_lint.py from-srt in.srt out.iac [--name TRACK]
```

What it does:

- reads one cue per block, tolerating the optional cue number;
- joins a cue's several text lines with one space;
- strips simple HTML tags (`<i>`, `<b>`);
- sets the colour to `[#FFFFFF]` and the track name to `--name`, or to the file's stem;
- sorts cues by start time and writes `#!iac 1.0`;
- if a cue's stop is not after its start, pushes the stop one centisecond later;
- **fails with exit 2** if a cue is outside `00:00:00:00–99:59:59:99`, rather than
  writing a file that no longer parses.

Track names are sanitised: letters, digits, spaces, `_`, and `-` are kept, everything
else becomes `_` (so `#song` becomes `_song`), and the result is truncated to 256
characters.

What is lost: speaker names, styling, positioning, and the original file structure.
Add `Type` (`Music`, `SFX`, …) after the conversion if a track needs it.

## VTT → IAC

There is no built-in importer. Map as follows:

- ignore `NOTE`, `STYLE`, and `REGION` blocks;
- a cue is `[id] timestamp --> timestamp [settings]` followed by text; ignore the id
  and the settings;
- timestamps are `HH:MM:SS.mmm` or `MM:SS.mmm` — both are valid;
- `&amp;`, `&lt;`, `&gt;`, and `&nbsp;` must be decoded; strip `<c>`, `<i>`, `<v Name>`;
- VTT allows an empty cue; IAC does not. Drop it or give it text.

## ASS / SSA → IAC

Read the `[Events]` section and the `Format:` line to find the column order, then:

- take `Layer`, `Start`, `End`, `Style`, `Name`, `Text`;
- timestamps are `H:MM:SS.cc` — the fractional part is already centiseconds, do not
  divide;
- colour: take a style's `PrimaryColour` (`&HAABBGGRR`), drop the two alpha digits,
  reverse `BBGGRR` to `RRGGBB`, and write `[#RRGGBB]`. Ignore per-word overrides;
- text: strip `{…}` override blocks and `\N` / `\n` line breaks (they become one
  space), keep everything else literally;
- only `Dialogue` lines are cues; `Comment` lines can become `#!cut` records if you
  want to keep them.

What is lost: karaoke timing (`\k`), positioning, fonts, animation, per-entry colour,
and alpha.

## IAC → SRT / VTT / ASS

The reverse mapping is simpler, with three rules:

- the stop stays as written: `[start, stop)` goes out as `start --> stop`;
- the record's colour becomes the style colour; ASS needs `&H00BBGGRR` (alpha 00 =
  opaque, blue and red swapped);
- one record becomes one style or one file. Do not merge records: `AudioName` is the
  track boundary.

## Lossiness

| Source feature | Survives into IAC? | Where it goes |
|---|---|---|
| Text | Yes, code point for code point | — |
| Timing | Yes, rounded to centiseconds | §6 |
| Track split | Yes, as `AudioName` | §5.1 |
| Record colour | Yes | §5.3 |
| Speaker | No | fold into `AudioName` or `Type` |
| Per-entry colour, alpha | No | E013 if written |
| Positioning, font, style | No | renderer's job |
| Karaoke / word timing | No | use ASS |
| Line breaks inside a cue | No | separate cues, or one space |
| Markup / escaping beyond `\"` and `\\` | No | strip it during conversion |

## What round-trips

Text, centisecond timing, the track split, and the colour round-trip exactly for simple
dialogue. Everything else is a one-way door: IAC is a source format, not an interchange
format ([spec §1.1](../spec/iac-1.0.md)).

## Draft-era files

A record with a `: true` / `: false` field is from the draft. Do not convert it by hand:

```bash
python tools/iac_lint.py migrate path/to/file.iac
```

`: true` is dropped; `: false` becomes a `#!cut` retired record. The command is
idempotent and refuses to touch a record whose fourth field is a real `Type`.
